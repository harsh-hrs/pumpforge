"""Assemble the offline web bundle that the Android app serves from its assets:
android/build/www/{index.html, lib/three/..., output/{glb,meta,learning}/...}"""
import os, shutil, sys
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W = os.path.join(R, 'android', 'build', 'www')
THREE = os.path.join(R, 'viewer', 'node_modules', 'three')


def main():
    if os.path.exists(W):
        shutil.rmtree(W)
    os.makedirs(W)
    s = open(os.path.join(R, 'viewer', 'library.html'), encoding='utf-8').read()
    s = s.replace('../output/', 'output/').replace('./node_modules/three/', './lib/three/')
    s = s.replace('// Local reference player for the learning library (serve the repo root, open /viewer/library.html).',
                  '// Offline bundle inside the Android app (served from assets via https://appassets.androidplatform.net/).')
    import re
    s = re.sub(r'<link rel="preconnect" href="https://fonts.googleapis.com">\n?', '', s)
    s = re.sub(r'<link rel="stylesheet" href="https://fonts.googleapis.com[^>]*>\n?', '', s)   # offline-first: system fonts
    assert 'fonts.googleapis' not in s and 'cdn.jsdelivr' not in s
    assert 'node_modules' not in s and '../output' not in s
    open(os.path.join(W, 'index.html'), 'w', encoding='utf-8').write(s)
    for rel in ['build/three.module.js', 'examples/jsm/loaders/GLTFLoader.js', 'examples/jsm/controls/OrbitControls.js',
                'examples/jsm/environments/RoomEnvironment.js', 'examples/jsm/utils/BufferGeometryUtils.js', 'LICENSE']:
        d = os.path.join(W, 'lib', 'three', rel)
        os.makedirs(os.path.dirname(d), exist_ok=True)
        shutil.copy(os.path.join(THREE, rel), d)
    for sub in ('glb', 'meta', 'learning'):
        shutil.copytree(os.path.join(R, 'output', sub), os.path.join(W, 'output', sub))
    n = sum(len(f) for _, _, f in os.walk(W))
    size = sum(os.path.getsize(os.path.join(a, x)) for a, _, f in os.walk(W) for x in f)
    print(f'www bundle: {n} files, {size / 1e6:.1f} MB')


if __name__ == '__main__':
    main()
