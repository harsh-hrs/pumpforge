"""Desktop test run: builds the harness, stages assets, runs the smoke script and the full 282-module sweep.
Needs clang++ and Mesa EGL/GLES (Linux). Usage: python3 native/tools/run_tests.py [--quick]"""
import os, subprocess, sys
N = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(N, 'tools'))
import build_assets  # noqa: E402

def main():
    subprocess.run([os.path.join(N, 'tools', 'build_host.sh')], check=True)
    assets = build_assets.main(os.path.join(N, 'build', 'test_assets'))
    os.makedirs(os.path.join(N, 'build', 'test_shots'), exist_ok=True)
    exe = os.path.join(N, 'build', 'host', 'pf_test')
    r = subprocess.run([exe, assets, os.path.join(N, 'tests', 'smoke.txt'), '--size', '1078x2280', '--density', '2.75'], cwd=N, capture_output=True, text=True)
    print(r.stderr[-2000:])
    if '--quick' in sys.argv:
        return
    r = subprocess.run([exe, assets, os.path.join(N, 'tests', 'sweep_all.txt'), '--size', '392x829', '--density', '1'], cwd=N, capture_output=True, text=True)
    ok = r.stderr.count('SWEEP ok'); bad = [l for l in r.stderr.split('\n') if 'FAIL' in l or 'assert' in l or 'GL error' in l]
    print(f'sweep: {ok} modules ok, {len(bad)} problems'); print('\n'.join(bad[:20]))
    sys.exit(1 if bad or ok < 282 else 0)

if __name__ == '__main__':
    main()
