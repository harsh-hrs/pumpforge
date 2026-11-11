"""Learning-module content model (13 sections per pump) and builder.

Content lives in content/*.py as MODULES[pump_id] = mod(...).  build_content.py turns it
into output/learning/<pump_id>.json, cross-checks part ids against output/meta/<id>.json,
and generates three in-app video tours (narration + timed camera/animation actions)
that the app plays on the 3-D model itself.
"""
import json
import os
import re

SECTIONS = ['introduction', 'model_3d', 'exploded_view', 'cross_section', 'working_principle', 'flow_animation',
            'components', 'engineering_parameters', 'installation', 'maintenance', 'failure_analysis',
            'video_tutorials', 'assessment']

PARAM_BASIS = ('Typical published range for this design class (not a rating of the 3-D model or of any specific '
               'product). Verify against the selected manufacturer datasheet and performance curve; fill reference_model '
               'when a specific product is chosen.')
PARAM_SOURCES = ['Hydraulic Institute — ANSI/HI pump standards and Pump Types guidance',
                 'KSB Pump Lexicon / KSB Centrifugal Pump Design',
                 'US DOE — Improving Pumping System Performance: A Sourcebook for Industry',
                 'Karassik et al., Pump Handbook (4th ed.)',
                 'Manufacturer catalogue envelopes (generic; to be verified)']


# ------------------------------------------------------------------ authoring helpers
def P(value, unit='', note=None):
    d = {'typical_range': value, 'unit': unit}
    if note:
        d['note'] = note
    return d


def step(text, part=None, cut=True, operate=True, overlay=None, explode=0.0, view=None):
    return {'text': text, 'part': part, 'cut': cut, 'operate': operate, 'overlay': overlay, 'explode': explode, 'view': view}


def F(problem, symptoms, causes, remedies, part=None, category=None):
    return {'problem': problem, 'category': category or _cat(problem), 'symptoms': symptoms, 'causes': causes,
            'remedies': remedies, 'part': part}


def Q(question, options, answer, explanation, level='basic'):
    """Quiz item. Options are written with the correct one anywhere (usually first); they are rotated by a stable hash of the
    question so the correct answer lands in a different position from question to question (the app does not shuffle)."""
    import hashlib
    assert 0 <= answer < len(options)
    n = len(options)
    k = int(hashlib.md5(question.encode('utf-8')).hexdigest(), 16) % n
    opts = options[k:] + options[:k]
    return {'question': question, 'options': opts, 'answer': (answer - k) % n, 'explanation': explanation, 'level': level}


def M(text, part=None, interval=None):
    d = {'task': text}
    if part:
        d['part'] = part
    if interval:
        d['interval'] = interval
    return d


def _cat(p):
    p = p.lower()
    for k, c in (('cavitat', 'cavitation'), ('wear', 'wear'), ('erosi', 'wear'), ('abras', 'wear'), ('leak', 'leakage'),
                 ('seal', 'leakage'), ('vibrat', 'vibration'), ('misalign', 'vibration'), ('bearing', 'bearing'),
                 ('overheat', 'thermal'), ('dry', 'thermal'), ('prime', 'priming'), ('air', 'priming'), ('clog', 'blockage'),
                 ('block', 'blockage'), ('pulsat', 'pulsation'), ('valve', 'valves'), ('corros', 'corrosion')):
        if k in p:
            return c
    return 'performance'


def mod(definition, applications, principle, params, install, maint, failures, quiz, curve=None, key_points=None,
        refs=None, selection=None, safety=None, operation=None, param_title=None, param_basis=None, param_sources=None, plant=None,
        narration=None):
    """operation (Mine-to-Port catalog): dict(controls=[...], pre_start=[...], start_up=[...], normal=[...], shut_down=[...],
    alarms_interlocks=[...], tips=[...]) shown in the app's Operation tab. plant: dict(area, tag, qty, interfaces) — where the
    equipment sits in the reference plant."""
    return dict(definition=definition, applications=applications, principle=principle, params=params, install=install,
                maint=maint, failures=failures, quiz=quiz, curve=curve, key_points=key_points or [], refs=refs or [],
                selection=selection or [], safety=safety or [], operation=operation, param_title=param_title,
                param_basis=param_basis, param_sources=param_sources, plant=plant, narration=narration or {})


# ------------------------------------------------------------------ builder
def _words(s):
    return len(re.findall(r'\w+', s))


def _line(text, **action):
    return {'narration': text, 'duration_s': max(4.0, round(_words(text) / 2.4, 1)),
            'action': {k: v for k, v in action.items() if v is not None}}


def _sentences(s, n):
    out = [x.strip() for x in re.split(r'(?<=[.!?])\s+', s) if x.strip()]
    return out[:n]


def _lc(s):
    """Lower-case for mid-sentence use without breaking acronyms or chemical formulas (Al₂O₃, SiO₂, TKPH, ROM)."""
    out = []
    for w in s.split(' '):
        core = w.strip('(),.;:')
        keep = (any(ch.isdigit() or ch in '₀₁₂₃₄₅₆₇₈₉' for ch in core) or sum(ch.isupper() for ch in core) >= 2)
        out.append(w if keep else w.lower())
    return ' '.join(out)


def _tours(pid, title, c, meta):
    parts = {p['id']: p['name'] for p in meta['parts']}
    nar = c.get('narration') or {}
    m2p = pid.startswith('m2p_')
    ovl = list(meta.get('overlays', {}))
    key = [p for p in meta['parts'] if p['group'] in ('rotating_element', 'casing', 'stages', 'bowl_assembly', 'pumps', 'body')][:4]
    intro = [_line(f'This module introduces the {title}.', view='iso', cut=False, explode=0, operate=False)]
    for s_ in _sentences(c['definition'], 3):
        intro.append(_line(s_, view='orbit', operate=True))
    lf = lambda a: a.rstrip('.') if (a[:2].isupper() or any(ch.isdigit() or ch in '₂₃' for ch in a.split(' ')[0])) else a[:1].lower() + a[1:].rstrip('.')
    intro.append(_line('Typical applications include ' + '; '.join(lf(a) for a in c['applications'][:4]) + '.', view='iso'))
    has_cut = any(p.get('section_role') in ('front', 'split') for p in meta['parts'])
    has_explode = any(any(abs(v) > 1e-6 for v in (p.get('explode_offset') or [0, 0, 0])) for p in meta['parts'])
    if 'cutaway' in nar:
        intro.append(_line(nar['cutaway'], view='front', cut=True))
    elif has_cut or not m2p:
        intro.append(_line('The cutaway reveals the internal construction' + (': ' + ', '.join(p['name'] for p in key) if key else '') + '.',
                           view='front', cut=True))
    if 'explode' in nar:
        intro.append(_line(nar['explode'], view='iso', cut=False, explode=1.0))
    elif has_explode or not m2p:
        intro.append(_line('The exploded view separates every component so each one can be tapped for its function, material and failure modes.',
                           view='iso', cut=False, explode=1.0))
    intro.append(_line('Next, watch the operation tutorial to see how it works.', view='iso', explode=0.0))
    op = [_line(f'How the {title} works.', view='iso', cut=True, operate=True)]
    for s in c['principle']:
        op.append(_line(s['text'], highlight=s['part'] if s['part'] in parts else None, cut=s['cut'], operate=s['operate'],
                        overlay=s['overlay'] if (s['overlay'] in ovl) else None, explode=s['explode'] or None,
                        view=s['view'] or ('part' if s['part'] in parts else 'front')))
    if 'flow' in ovl:
        fdesc = meta['overlays']['flow'].get('description') or ''
        if 'flow' in nar:
            ftxt = nar['flow']
        elif m2p and fdesc and not fdesc.startswith('Suction and discharge'):
            ftxt = 'The overlay shows the ' + _lc(meta['overlays']['flow'].get('title', 'flow path')[:1]) + meta['overlays']['flow'].get('title', 'flow path')[1:] + '. ' + fdesc
        else:
            ftxt = 'The flow overlay traces the liquid from suction to discharge.'
        op.append(_line(ftxt, overlay='flow', cut=not m2p, view='front' if not m2p else 'iso'))
    for k in ovl:
        if k != 'flow':
            op.append(_line(meta['overlays'][k]['description'].split('. ')[0].rstrip('.') + '.', overlay=k, view='front',
                            cut=meta['overlays'][k].get('render') != 'xray' or True))
    mt = [_line(f'Maintenance essentials for the {title}.', view='iso', cut=False, operate=False)]
    tasks = (c['maint'].get('routine', [])[:3] + c['maint'].get('periodic', [])[:2] + c['maint'].get('overhaul', [])[:2])
    for t in tasks:
        pp = t.get('part')
        mt.append(_line(t['task'], highlight=pp if pp in parts else None, view='part' if pp in parts else 'iso', cut=bool(pp)))
    for f in c['failures'][:3]:
        pp = f.get('part')
        txt = f"Watch for {_lc(f['problem'])}: {_lc(f['symptoms'][0].rstrip('.'))}. Common cause: {_lc(f['causes'][0].rstrip('.'))}."
        mt.append(_line(txt, highlight=pp if pp in parts else None, view='part' if pp in parts else 'front', cut=True,
                        overlay='wear' if ('wear' in ovl and f['category'] == 'wear') else None))
    mt.append(_line(nar.get('records') or ('Record every inspection so trends — wear, temperatures, pressures, leaks and performance — can be compared over time.' if m2p else
                    'Record every inspection so trends — vibration, temperature, leakage and performance — can be compared over time.'), view='iso', cut=False))
    out = []
    for vid, name, lines in (('introduction', 'Introduction', intro), ('operation', 'Operation', op), ('maintenance', 'Maintenance', mt)):
        out.append({'id': vid, 'title': f'{title} — {name}', 'type': 'in_app_tour', 'model': f'{pid}.glb',
                    'duration_s': round(sum(l['duration_s'] for l in lines), 1), 'script': lines,
                    'production_note': 'Rendered live in the app: each line plays its narration (TTS or recorded) while '
                                       'applying the action (camera, cutaway, explode, operate, overlay, highlight).'})
    return out


_GENERIC = ('motor_frame_h', 'stator', 'rotor', 'motor_fan', 'fan_cover', 'motor_bearings', 'coupling_guard', 'baseplate', 'pressure_gauge',
            'pipework', 'flow_tracers', 'gasket')


def _component_questions(pid, meta, n=3):
    """'Identify the component' questions built from this model's own component notes (tap-to-answer in 3-D)."""
    import hashlib
    seen, cands = set(), []
    for p in meta['parts']:
        ref = p['info_ref']
        fn = (meta['components'].get(ref) or {}).get('function')
        if not fn or ref in seen or ref in _GENERIC or p['id'].startswith(('m_', 'mx_', 'mduty_', 'mstandby_', 'mmain_', 'jm_')):
            continue
        seen.add(ref)
        cands.append((p, fn))
    out = []
    for i, (p, fn) in enumerate(cands[:n]):
        others = [q['name'] for q, _ in cands if q['info_ref'] != p['info_ref']]
        others += [q['name'] for q in meta['parts'] if q['info_ref'] != p['info_ref'] and q['name'] not in others]
        h = int(hashlib.md5(f'{pid}{i}'.encode()).hexdigest(), 16)
        dis = []
        for k in range(len(others)):
            o = others[(h + k * 7) % len(others)]
            if o not in dis and o != p['name']:
                dis.append(o)
            if len(dis) == 3:
                break
        for o in others:
            if len(dis) >= 3:
                break
            if o not in dis and o != p['name']:
                dis.append(o)
        if len(dis) < 3:
            continue
        pos = h % 4
        opts = dis[:pos] + [p['name']] + dis[pos:]
        q = Q(f'Which component has this function? "{fn}"', opts, pos, f'{p["name"]}: {fn}', 'basic')
        q['part'] = p['id']
        q['type'] = 'identify_component'
        out.append(q)
    return out


def build_module(pid, c, meta, catalog_entry, family):
    parts = {p['id'] for p in meta['parts']}
    problems = []
    for s in c['principle']:
        if s['part'] and s['part'] not in parts:
            problems.append(f'principle part {s["part"]}')
    for f in c['failures']:
        if f.get('part') and f['part'] not in parts:
            problems.append(f'failure part {f["part"]}')
    for grp in c['maint'].values():
        for t in grp:
            if isinstance(t, dict) and t.get('part') and t['part'] not in parts:
                problems.append(f'maintenance part {t["part"]}')
    title = catalog_entry['name']
    ov = meta.get('overlays', {})
    params = dict(c['params'])
    extra = params.pop('extra', {})
    ref = params.pop('reference_model', None)
    sec = {
        'introduction': {'definition': c['definition'], 'applications': c['applications'], 'key_points': c['key_points'],
                         'classification': meta.get('classification', {}), 'hi_family': family,
                         'summary': meta.get('summary', '')},
        'model_3d': {'asset': f'glb/{pid}.glb', 'metadata': f'meta/{pid}.json', 'controls': 'orbit, zoom, tap a part for details',
                     'triangles': meta['stats']['triangles'], 'parts': meta['stats']['parts']},
        'exploded_view': {'animation': 'Explode', 'duration_s': meta['animations']['Explode']['duration_s'],
                          'method': 'play clip or lerp part nodes by explode_offset (0–1 slider)'},
        'cross_section': {'mode': 'cutaway', 'hide_section_roles': ['front', 'hide'], 'section_material': 'section',
                          'what_to_look_for': [s['text'] for s in c['principle'] if s['cut']][:3]},
        'working_principle': {'animation': 'Operate', 'loop_s': meta['animations']['Operate']['duration_s'], 'steps': c['principle'],
                              'characteristic_curve': c['curve']},
        'flow_animation': {'overlay': 'flow' if 'flow' in ov else None, 'asset': ov.get('flow', {}).get('file'),
                           'tracers_in_model': any(p['group'] == 'flow_tracers' for p in meta['parts']),
                           'other_overlays': {k: {kk: v[kk] for kk in ('file', 'title', 'description', 'render', 'annotations') if kk in v}
                                              for k, v in ov.items() if k != 'flow'}},
        'components': {'source': f'meta/{pid}.json#components', 'key_components': catalog_entry.get('key_components') or catalog_entry.get('underlying_design'),
                       'parts': [{'id': p['id'], 'name': p['name'], 'info_ref': p['info_ref'],
                                  'function': meta['components'].get(p['info_ref'], {}).get('function'),
                                  'material': meta['components'].get(p['info_ref'], {}).get('material')} for p in meta['parts']]},
        'engineering_parameters': {'basis': c.get('param_basis') or PARAM_BASIS, 'status': 'to be verified', 'parameters': params, 'additional': extra,
                                   **({'title': c['param_title']} if c.get('param_title') else {}),
                                   'selection_notes': c['selection'],
                                   'reference_model': ref or {'manufacturer': None, 'model': None, 'datasheet': None,
                                                              'rated_point': {'flow': None, 'head': None, 'speed_rpm': None, 'efficiency_pct': None, 'npshr': None, 'power_kW': None},
                                                              'status': 'empty — fill from the selected manufacturer datasheet / test certificate'},
                                   'sources': (c.get('param_sources') or PARAM_SOURCES) + c['refs']},
        'installation': c['install'],
        'maintenance': c['maint'],
        'failure_analysis': {'items': c['failures'], 'safety': c['safety']},
        'video_tutorials': _tours(pid, title, c, meta),
        'assessment': {'questions': c['quiz'] + _component_questions(pid, meta), 'pass_mark_pct': 70,
                       'note': 'Questions with a "part" field can highlight that part in the 3-D model after answering.'},
    }
    if c.get('operation'):
        sec['operation'] = c['operation']
    if c.get('plant'):
        sec['introduction']['plant'] = c['plant']
    out = {'schema': 'pumpforge.learning/1.0', 'pump_id': pid, 'no': catalog_entry['no'], 'title': title,
           'model_title': meta['title'], 'category': meta['category'], 'phase': catalog_entry['phase'],
           'flagship': catalog_entry.get('flagship', False), 'sections_order': SECTIONS, 'sections': sec,
           'disclaimer': meta['disclaimer']}
    return out, problems
