"""Arrange the catalogue in the department order of the Industrial Engineering Equipment Library and renumber
modules 1…N continuously in that order (EQ numbers are unchanged).  python3 tools/arrange.py"""
import json, os
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORDER = ['valves_piping', 'pumps', 'rotating', 'static', 'material_handling', 'thermal_process', 'filtration_separation',
         'alumina_refinery', 'water_utilities', 'mechanical_components', 'safety_environmental', 'instrumentation_controls']


def main():
    p = os.path.join(R, 'catalog.json')
    c = json.load(open(p, encoding='utf-8'))
    deps = {d['id']: d for d in c['departments']}
    assert set(deps) == set(ORDER), set(deps) ^ set(ORDER)
    c['departments'] = [deps[k] for k in ORDER]
    cats = {x['id']: x for x in c['categories']}
    ordered = [cats[cid] for d in c['departments'] for cid in d['categories']]
    assert len(ordered) == len(cats)
    c['categories'] = ordered
    n = 0
    for cat in ordered:
        for e in cat['pumps']:
            n += 1
            e['no'] = n
    c['note'] = f'Industrial Engineering Equipment Library: {n} modules arranged by department ({", ".join(d["name"] for d in c["departments"])}).'
    json.dump(c, open(p, 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
    open(p, 'a').write('\n')
    print(n, 'modules renumbered;', ' | '.join(f"{d['name']}: {sum(len(cats[i]['pumps']) for i in d['categories'])}" for d in c['departments']))


if __name__ == '__main__':
    main()
