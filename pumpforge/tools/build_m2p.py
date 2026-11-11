"""Build output/learning/m2p.json (Mine-to-Port catalog overview: plant basis, areas in process order, streams)
from the reconciled design basis m2p/basis/final_*.json (falls back to the drafts). python3 tools/build_m2p.py"""
import glob, json, os, re
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

AREAS = [  # process order, short names and the icon hint used by the app
    ('A01', 'Mine', 'mine'), ('A02', 'Ore Transport', 'conveyor'), ('A03', 'Bauxite Handling & Blending', 'stockpile'),
    ('A04', 'Grinding', 'mill'), ('A05', 'Pre-desilication', 'tank'), ('A06', 'Digestion', 'vessel'), ('A07', 'Flash Cooling & Heat Recovery', 'vessel'),
    ('A08', 'Sand Removal, Settling & Washing', 'thickener'), ('A09', 'Residue Filtration & Storage', 'residue'), ('A10', 'Security Filtration', 'filter'),
    ('A11', 'Heat Interchange', 'exchanger'), ('A12', 'Precipitation', 'tank'), ('A13', 'Classification & Seed', 'cyclone'), ('A14', 'Hydrate Filtration', 'filter'),
    ('A15', 'Calcination', 'calciner'), ('A16', 'Product Storage & Conveying', 'silo'), ('A17', 'Port & Export', 'ship'),
    ('A18', 'Evaporation', 'exchanger'), ('A19', 'Liquor Purification', 'tank'), ('A20', 'Utilities', 'utility')]


def main():
    files = sorted(glob.glob(os.path.join(R, 'm2p', 'basis', 'final_*.json'))) or sorted(glob.glob(os.path.join(R, 'm2p', 'basis', 'draft_*.json')))
    src = {}
    pw = []
    for f in files:
        d = json.load(open(f, encoding='utf-8'))
        for a in d['areas']:
            src[a['area_id']] = a
        pw += d.get('plantwide_numbers', [])
    idx = json.load(open(os.path.join(R, 'output', 'learning', 'index.json'), encoding='utf-8'))
    mods = [m for m in idx['modules'] if m.get('collection') == 'm2p']
    areas = []
    for aid, short, icon in AREAS:
        a = src.get(aid, {})
        areas.append({'id': aid, 'name': short, 'full_name': a.get('area_name', short), 'icon': icon, 'purpose': a.get('purpose', ''),
                      'process_description': a.get('process_description', ''),
                      'process_steps': [x.strip() for x in re.split(r'(?:^|\s)\d{1,2}\)\s', a.get('process_description', '')) if x.strip()], 'layout_notes': a.get('layout_notes', ''),
                      'streams': [{k: s.get(k, '') for k in ('name', 'from_to', 'flow', 'temperature', 'pressure', 'composition')} for s in a.get('streams', [])][:12],
                      'interfaces': a.get('interfaces', []),
                      'equipment_planned': [e['name'] for e in a.get('equipment', [])],
                      'modules': [m['id'] for m in mods if m.get('area') == aid]})
    out = {'schema': 'pumpforge.m2p/1.0', 'title': 'Alumina Refinery — Mine to Port',
           'subtitle': 'Generic 2 Mt/yr low-temperature Bayer refinery, from bauxite mine to export ship',
           'basis_note': ('Generic reference plant built from published practice and engineering estimates by a multi-agent SME panel '
                          '(knowledge-based; not verified against live sources). Not a copy of any company\'s plant. Verify before engineering use.'),
           'basis_status': 'final' if 'final_' in (files[0] if files else '') else 'draft',
           'plant': [{'parameter': p['parameter'], 'value': p['value']} for p in pw][:40],
           'site_model': 'm2p_site' if os.path.exists(os.path.join(R, 'output', 'meta', 'm2p_site.json')) else None,
           'areas': areas}
    json.dump(out, open(os.path.join(R, 'output', 'learning', 'm2p.json'), 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('m2p.json:', len(areas), 'areas,', len(mods), 'modules, basis', out['basis_status'])


if __name__ == '__main__':
    main()
