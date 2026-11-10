"""Stage the app assets for the native APK / Android Studio project: native/build/apk_assets/
  fonts/ (IBM Plex subset + symbols), env.bin (three.js RoomEnvironment light, baked), learning/ + meta/ (minified JSON,
  same content as output/), models/ (compact .pfm converted and verified from output/glb).
Needs Python 3 with numpy (pip install numpy) for the model conversion and fonttools only if fonts must be rebuilt."""
import glob, json, os, shutil, subprocess, sys

N = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = os.path.dirname(N)
OUT = os.path.join(N, 'build', 'apk_assets')


def newer(src_glob, dst_dir):
    srcs = glob.glob(src_glob)
    if not os.path.isdir(dst_dir):
        return True
    outs = glob.glob(os.path.join(dst_dir, '*'))
    return len(outs) < len(srcs) or max(os.path.getmtime(s) for s in srcs) > min(os.path.getmtime(o) for o in outs)


def main(out=OUT):
    pfm = os.path.join(N, 'build', 'pfm')
    if newer(os.path.join(R, 'output', 'glb', '*.glb'), pfm):
        subprocess.run([sys.executable, os.path.join(N, 'tools', 'glb2pfm.py'), os.path.join(R, 'output', 'glb'), pfm], check=True)
    if not glob.glob(os.path.join(N, 'assets', 'fonts', '*.ttf')):
        subprocess.run([sys.executable, os.path.join(N, 'tools', 'fonts.py')], check=True)
    if os.path.exists(out):
        shutil.rmtree(out)
    os.makedirs(out)
    shutil.copytree(os.path.join(N, 'assets', 'fonts'), os.path.join(out, 'fonts'))
    shutil.copy(os.path.join(N, 'assets', 'env.bin'), os.path.join(out, 'env.bin'))
    for sub in ('learning', 'meta'):
        os.makedirs(os.path.join(out, sub))
        for f in glob.glob(os.path.join(R, 'output', sub, '*.json')):
            d = json.load(open(f, encoding='utf-8'))
            with open(os.path.join(out, sub, os.path.basename(f)), 'w', encoding='utf-8') as fh:
                json.dump(d, fh, ensure_ascii=False, separators=(',', ':'))
    shutil.copytree(pfm, os.path.join(out, 'models'))
    nm, ng = len(glob.glob(os.path.join(out, 'models', '*.pfm'))), len(glob.glob(os.path.join(R, 'output', 'glb', '*.glb')))
    assert nm == ng, f'models {nm} != glb {ng}'
    size = sum(os.path.getsize(os.path.join(a, f)) for a, _, fs in os.walk(out) for f in fs)
    print(f'assets: {out} ({nm} models, {size / 1e6:.1f} MB uncompressed)')
    return out


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else OUT)
