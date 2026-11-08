"""Recheck the whole library: python3 tools/check_library.py
Verifies, for every catalogue entry, that the 3-D assets exist and that all 13 learning
sections are present and populated. Exit code 1 on any problem."""
import json, os, sys
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
cat = json.load(open(os.path.join(R, 'catalog.json'), encoding='utf-8'))
FAMILY_KEYS = {'safety_environmental': ['size', 'capacity', 'operating_conditions', 'performance'], 'mechanical_components': ['size', 'speed', 'load_capacity', 'operating_conditions'], 'water_utilities': ['size', 'capacity', 'operating_conditions', 'power_rating'], 'alumina_refinery': ['size', 'capacity', 'operating_conditions', 'power_rating'], 'filtration_separation': ['size', 'capacity', 'operating_pressure', 'separation_performance'], 'thermal_process': ['size', 'heat_duty', 'operating_temperature', 'capacity'], 'material_handling': ['size', 'power_rating', 'speed', 'capacity'], 'static_equipment': ['size', 'design_pressure', 'design_temperature', 'capacity'], 'valves_piping': ['size', 'pressure_rating', 'temperature', 'flow_capacity'], 'rotating_machinery': ['size', 'power_rating', 'speed', 'capacity']}
PKEYS = ['flow', 'head', 'pressure', 'speed', 'efficiency']
problems, rows = [], []
for c in cat['categories']:
    for e in c['pumps']:
        pid = e['id']; P = lambda m: problems.append(f'{pid}: {m}')
        glb = os.path.join(R, 'output', 'glb', f'{pid}.glb'); meta_p = os.path.join(R, 'output', 'meta', f'{pid}.json')
        lp = os.path.join(R, 'output', 'learning', f'{pid}.json')
        for f in (glb, meta_p, lp):
            if not os.path.exists(f): P(f'missing {os.path.relpath(f, R)}')
        if not (os.path.exists(meta_p) and os.path.exists(lp)):
            continue
        meta = json.load(open(meta_p, encoding='utf-8')); L = json.load(open(lp, encoding='utf-8')); s = L['sections']
        for k, v in meta.get('overlays', {}).items():
            if not os.path.exists(os.path.join(R, 'output', 'glb', v['file'])): P(f'overlay file missing {v["file"]}')
        if e['status'] != 'done': P('catalogue status not done')
        if set(L['sections_order']) != set(s): P('section set mismatch')
        if not s['introduction']['definition'] or len(s['introduction']['applications']) < 2: P('introduction thin')
        if meta['stats']['parts'] < 3: P('too few parts')
        if 'Explode' not in meta['animations'] or 'Operate' not in meta['animations']: P('animations missing')
        if len(s['working_principle']['steps']) < 3: P('working principle < 3 steps')
        if not (s['flow_animation']['overlay'] or s['flow_animation']['tracers_in_model']): P('no flow animation')
        miss = [u for u in {p['info_ref'] for p in meta['parts']} if u not in meta['components']]
        if miss: P(f'components without info {miss}')
        ep = s['engineering_parameters']['parameters']
        keys = FAMILY_KEYS.get(c['hi_family'], PKEYS)
        if any(k not in ep for k in keys): P(f'parameters missing {[k for k in keys if k not in ep]}')
        if 'reference_model' not in s['engineering_parameters']: P('no reference_model slot')
        for k in ('foundation', 'alignment', 'piping', 'commissioning'):
            if not s['installation'].get(k): P(f'installation.{k} empty')
        for k in ('routine', 'periodic', 'overhaul', 'lubrication'):
            if not s['maintenance'].get(k): P(f'maintenance.{k} empty')
        if len(s['failure_analysis']['items']) < 2: P('failure analysis < 2 items')
        if len(s['video_tutorials']) != 3: P('video tours != 3')
        nq = len(s['assessment']['questions'])
        if nq < 3 or (e.get('flagship') and nq < 8): P(f'only {nq} quiz questions')
        for st in s['working_principle']['steps']:
            if st['overlay'] and st['overlay'] not in meta.get('overlays', {}): P(f'step overlay {st["overlay"]} not in model')
        rows.append((e['no'], pid, meta['stats']['parts'], meta['stats']['triangles'], ','.join(meta.get('overlays', {})), nq, len(s['failure_analysis']['items']),
                     round(sum(v['duration_s'] for v in s['video_tutorials']))))
print(f"{'#':>2} {'module':34} parts   tris  overlays                         quiz fail tours_s")
for r in rows:
    print(f'{r[0]:>2} {r[1]:34} {r[2]:>5} {r[3]:>7}  {r[4]:32} {r[5]:>4} {r[6]:>4} {r[7]:>6}')
print(f'\n{len(rows)} / {sum(len(c["pumps"]) for c in cat["categories"])} modules complete;', 'problems:' if problems else 'no problems found')
for p in problems:
    print('  -', p)
sys.exit(1 if problems else 0)
