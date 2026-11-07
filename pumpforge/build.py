"""Build all pump models: python3 build.py [pump_id ...]"""
import sys, time, importlib, pkgutil, os, traceback
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: F401  (registers mathutils)
import pumps

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output')

def main(ids):
    all_ids = [m.name for m in pkgutil.iter_modules(pumps.__path__) if not m.name.startswith('_')]
    ids = ids or all_ids
    failed = []
    for pid in ids:
        t = time.time()
        try:
            mod = importlib.import_module(f'pumps.{pid}')
            path = mod.build(OUT)
            print(f'[ok] {pid}: {os.path.getsize(path)/1e6:.2f} MB in {time.time()-t:.1f}s')
        except Exception:
            traceback.print_exc()
            failed.append(pid)
    if failed:
        print('FAILED:', failed); sys.exit(1)

if __name__ == '__main__':
    main(sys.argv[1:])
