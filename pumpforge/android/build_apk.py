"""Build the PumpForge Android APK without the Android SDK/Gradle.

Toolchain (fetched from the npm registry, cached in android/build/tools):
  apktool 2.9.3  - assembles smali -> classes.dex and links the manifest/resources with its bundled aapt2 + framework
  apksigner      - Google's APK signer (v1 + v2 + v3 signatures)
Steps: offline web bundle -> staging dir -> apktool b -> zip align (resources.arsc stored) -> sign -> verify.
Usage: python3 android/build_apk.py [--version-name 1.0.0 --version-code 1]
"""
import argparse, os, shutil, subprocess, sys, tarfile, zipfile, re

A = os.path.dirname(os.path.abspath(__file__))
B = os.path.join(A, 'build')
TOOLS = os.path.join(B, 'tools')
KS = os.path.join(A, 'keystore', 'pumpforge-debug.jks')
KS_PASS = 'pumpforge-debug'
ALIAS = 'pumpforge'


def sh(*cmd, **kw):
    print('$', ' '.join(cmd)[:160])
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if r.returncode:
        print(r.stdout[-3000:], r.stderr[-3000:])
        sys.exit(f'command failed: {cmd[0]}')
    return r.stdout + r.stderr


def tools():
    apktool, signer = os.path.join(TOOLS, 'apktool.jar'), os.path.join(TOOLS, 'apksigner.jar')
    if not (os.path.exists(apktool) and os.path.exists(signer)):
        os.makedirs(TOOLS, exist_ok=True)
        sh('npm', 'pack', '@postar/apktool-node@0.3.4', '--ignore-scripts', cwd=TOOLS)
        out = [f for f in os.listdir(TOOLS) if f.endswith('.tgz')][0]
        with tarfile.open(os.path.join(TOOLS, out)) as t:
            for name, dst in (('package/lib/apktool.jar', apktool), ('package/lib/apksigner.jar', signer)):
                with t.extractfile(name) as src, open(dst, 'wb') as fh:
                    shutil.copyfileobj(src, fh)
    return apktool, signer


def align(src, dst):
    """Rewrite the zip: resources.arsc and PNGs stored (uncompressed), every stored entry 4-byte aligned."""
    zin = zipfile.ZipFile(src)
    with open(dst, 'wb') as fh:
        zout = zipfile.ZipFile(fh, 'w')
        for info in zin.infolist():
            data = zin.read(info.filename)
            store = info.filename == 'resources.arsc' or info.filename.endswith('.png') or info.compress_type == zipfile.ZIP_STORED
            zi = zipfile.ZipInfo(info.filename, date_time=(2026, 11, 7, 0, 0, 0))
            zi.compress_type = zipfile.ZIP_STORED if store else zipfile.ZIP_DEFLATED
            zi.external_attr = 0o644 << 16
            if store:
                # local header = 30 bytes + name + extra; pad extra so the data starts on a 4-byte boundary
                off = fh.tell() + 30 + len(zi.filename.encode())
                pad = (4 - off % 4) % 4
                zi.extra = b'\x00' * pad
            zout.writestr(zi, data, compresslevel=9 if not store else None)
        zout.close()


def check_aligned(path):
    with open(path, 'rb') as fh:
        z = zipfile.ZipFile(fh)
        for i in z.infolist():
            if i.compress_type == zipfile.ZIP_STORED:
                fh.seek(i.header_offset + 26)
                n, e = int.from_bytes(fh.read(2), 'little'), int.from_bytes(fh.read(2), 'little')
                if (i.header_offset + 30 + n + e) % 4:
                    sys.exit(f'not aligned: {i.filename}')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--version-name', default='1.0.0')
    ap.add_argument('--version-code', default='1')
    a = ap.parse_args()
    sh(sys.executable, os.path.join(A, 'make_www.py'))
    apktool, signer = tools()
    stage = os.path.join(B, 'stage')
    if os.path.exists(stage):
        shutil.rmtree(stage)
    shutil.copytree(os.path.join(A, 'app'), stage)
    yml = open(os.path.join(stage, 'apktool.yml')).read()
    yml = re.sub(r'versionCode: .*', f'versionCode: {a.version_code}', yml)
    yml = re.sub(r'versionName: .*', f'versionName: {a.version_name}', yml)
    open(os.path.join(stage, 'apktool.yml'), 'w').write(yml)
    shutil.copytree(os.path.join(B, 'www'), os.path.join(stage, 'assets', 'www'))
    raw = os.path.join(B, 'unsigned.apk')
    sh('java', '-jar', apktool, 'b', stage, '-o', raw, '-f')
    aligned = os.path.join(B, 'aligned.apk')
    align(raw, aligned)
    check_aligned(aligned)
    if not os.path.exists(KS):
        os.makedirs(os.path.dirname(KS), exist_ok=True)
        sh('keytool', '-genkeypair', '-keystore', KS, '-storepass', KS_PASS, '-keypass', KS_PASS, '-alias', ALIAS, '-keyalg', 'RSA',
           '-keysize', '2048', '-validity', '10000', '-dname', 'CN=PumpForge Debug, O=Red Eye Labs, C=IN')
    out = os.path.join(B, f'PumpForge-{a.version_name}.apk')
    sh('java', '-jar', signer, 'sign', '--ks', KS, '--ks-pass', f'pass:{KS_PASS}', '--ks-key-alias', ALIAS,
       '--v1-signing-enabled', 'true', '--v2-signing-enabled', 'true', '--v3-signing-enabled', 'true', '--out', out, aligned)
    print(sh('java', '-jar', signer, 'verify', '--verbose', '--print-certs', out).strip()[-1500:])
    print(f'APK: {out} ({os.path.getsize(out) / 1e6:.1f} MB)')


if __name__ == '__main__':
    main()
