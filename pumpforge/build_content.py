"""Build learning modules: python3 build_content.py  ->  output/learning/<id>.json + index.json"""
import importlib, json, os, pkgutil, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import content
from pumpforge.learning import build_module, SECTIONS

R = os.path.dirname(os.path.abspath(__file__))


def main():
    mods = {}
    for m in pkgutil.iter_modules(content.__path__):
        mods.update(importlib.import_module(f'content.{m.name}').MODULES)
    cat = json.load(open(os.path.join(R, 'catalog.json'), encoding='utf-8'))
    os.makedirs(os.path.join(R, 'output', 'learning'), exist_ok=True)
    index, missing, bad = [], [], {}
    for c in cat['categories']:
        for e in c['pumps']:
            pid = e['id']
            mp = os.path.join(R, 'output', 'meta', f'{pid}.json')
            if pid not in mods or not os.path.exists(mp):
                missing.append(pid)
                continue
            meta = json.load(open(mp, encoding='utf-8'))
            out, problems = build_module(pid, mods[pid], meta, e, c['hi_family'])
            if problems:
                bad[pid] = problems
            json.dump(out, open(os.path.join(R, 'output', 'learning', f'{pid}.json'), 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
            s = out['sections']
            index.append({'no': e['no'], 'id': pid, 'title': e['name'], 'category': c['name'], 'phase': e['phase'], 'flagship': e.get('flagship', False),
                          'eq_id': e.get('eq_id'), 'subcategory': e.get('subcategory'),
                          'keywords': list(dict.fromkeys([w.strip() for w in str(e.get('key_components') or '').split(',') if w.strip()] + [pp.get('name') for pp in meta.get('parts', []) if isinstance(pp, dict) and pp.get('name')])),
                          'overlays': list(meta.get('overlays', {})), 'quiz_questions': len(s['assessment']['questions']),
                          'failure_items': len(s['failure_analysis']['items']), 'video_tours': len(s['video_tutorials'])})
    json.dump({'schema': 'pumpforge.learning-index/1.0', 'sections': SECTIONS, 'modules': index},
              open(os.path.join(R, 'output', 'learning', 'index.json'), 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print(f'{len(index)} modules written; missing: {missing}')
    for k, v in bad.items():
        print('PART-ID PROBLEMS', k, v)
    return 0 if not missing and not bad else 1


if __name__ == '__main__':
    sys.exit(main())
