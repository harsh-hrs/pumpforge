"""Build the fully native PumpForge APK (android.app.NativeActivity + libpumpforge.so, no WebView, no Java code).

Steps: models (.glb -> compact .pfm, verified) -> UI fonts -> libpumpforge.so for arm64-v8a + x86_64 ->
stage (manifest, icons, assets) -> apktool b (manifest + resources) -> add lib/ -> zip align -> apksigner (v1+v2+v3) -> verify.
Usage: python3 native/tools/build_apk.py --version-name 2.1.0 --version-code 13
Signed with the same key as the WebView builds, so it installs as an update of com.redeyelabs.pumpforge.
"""
import argparse, glob, json, os, shutil, subprocess, sys, zipfile

N = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = os.path.dirname(N)
B = os.path.join(N, 'build')
import importlib.util  # noqa: E402
_spec = importlib.util.spec_from_file_location('web_build_apk', os.path.join(R, 'android', 'build_apk.py'))
web = importlib.util.module_from_spec(_spec)   # reuse the npm-provided apktool/apksigner, zip alignment and the signing key
_spec.loader.exec_module(web)
sys.path.insert(0, os.path.join(N, 'tools'))

MANIFEST = '''<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android" package="com.redeyelabs.pumpforge">
    <uses-feature android:glEsVersion="0x00030000" android:required="true"/>
    <queries>
        <intent>
            <action android:name="android.intent.action.TTS_SERVICE"/>
        </intent>
    </queries>
    <application android:label="@string/app_name" android:icon="@mipmap/ic_launcher" android:allowBackup="false"
        android:hasCode="false" android:extractNativeLibs="true" android:hardwareAccelerated="true" android:largeHeap="true">
        <activity android:name="android.app.NativeActivity" android:exported="true" android:launchMode="singleTask"
            android:theme="@android:style/Theme.Material.Light.NoActionBar"
            android:windowSoftInputMode="adjustResize"
            android:configChanges="orientation|screenSize|screenLayout|smallestScreenSize|keyboardHidden|keyboard|navigation|uiMode">
            <meta-data android:name="android.app.lib_name" android:value="pumpforge"/>
            <intent-filter>
                <action android:name="android.intent.action.MAIN"/>
                <category android:name="android.intent.category.LAUNCHER"/>
            </intent-filter>
        </activity>
    </application>
</manifest>
'''


def sh(*cmd, **kw):
    return web.sh(*cmd, **kw)


def newer(src_glob, dst_dir):
    srcs = glob.glob(src_glob)
    if not os.path.isdir(dst_dir):
        return True
    newest = max(os.path.getmtime(s) for s in srcs)
    outs = glob.glob(os.path.join(dst_dir, '*'))
    return len(outs) < len(srcs) or newest > min(os.path.getmtime(o) for o in outs)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--version-name', default='2.1.0')
    ap.add_argument('--version-code', default='13')
    a = ap.parse_args()
    import build_assets
    sh(sys.executable, os.path.join(N, 'tools', 'build_so.py'))
    apktool, signer = web.tools()
    stage = os.path.join(B, 'apk_stage')
    if os.path.exists(stage):
        shutil.rmtree(stage)
    os.makedirs(stage)
    shutil.copytree(os.path.join(R, 'android', 'app', 'res'), os.path.join(stage, 'res'))
    open(os.path.join(stage, 'AndroidManifest.xml'), 'w').write(MANIFEST)
    yml = open(os.path.join(R, 'android', 'app', 'apktool.yml')).read()
    import re
    yml = re.sub(r'versionCode: .*', f'versionCode: {a.version_code}', yml)
    yml = re.sub(r'versionName: .*', f'versionName: {a.version_name}', yml)
    open(os.path.join(stage, 'apktool.yml'), 'w').write(yml)
    # assets: fonts, image-based light, learning/meta JSON (minified, same content), compact models
    build_assets.main(os.path.join(stage, 'assets'))
    ng = len(glob.glob(os.path.join(R, 'output', 'glb', '*.glb')))
    nm = len(glob.glob(os.path.join(stage, 'assets', 'models', '*.pfm')))
    raw = os.path.join(B, 'native-unsigned.apk')
    sh('java', '-jar', apktool, 'b', stage, '-o', raw, '-f')
    # add the native libraries (compressed; extracted at install - extractNativeLibs=true)
    with zipfile.ZipFile(raw, 'a', zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        names = set(z.namelist())
        assert 'classes.dex' not in names, 'unexpected dex in a hasCode=false app'
        for abi in ('arm64-v8a', 'armeabi-v7a', 'x86_64'):
            z.write(os.path.join(B, 'android', abi, 'libpumpforge.so'), f'lib/{abi}/libpumpforge.so')
    aligned = os.path.join(B, 'native-aligned.apk')
    web.align(raw, aligned)
    web.check_aligned(aligned)
    out = os.path.join(B, f'PumpForge-{a.version_name}-native.apk')
    sh('java', '-jar', signer, 'sign', '--ks', web.KS, '--ks-pass', f'pass:{web.KS_PASS}', '--ks-key-alias', web.ALIAS,
       '--v1-signing-enabled', 'true', '--v2-signing-enabled', 'true', '--v3-signing-enabled', 'true', '--out', out, aligned)
    v = sh('java', '-jar', signer, 'verify', '--verbose', out)
    assert 'Verified using v2 scheme (APK Signature Scheme v2): true' in v, v
    with zipfile.ZipFile(out) as z:
        n = z.namelist()
        assert all(f'lib/{abi}/libpumpforge.so' in n for abi in ('arm64-v8a', 'armeabi-v7a', 'x86_64')) and 'assets/env.bin' in n
        assert sum(1 for x in n if x.startswith('assets/models/')) == ng
    print(f'APK: {out} ({os.path.getsize(out) / 1e6:.1f} MB, {nm} models)')


if __name__ == '__main__':
    main()
