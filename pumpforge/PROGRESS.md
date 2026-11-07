# PROGRESS — PumpForge Pump Learning Library

_Last updated: 2026-11-07_

## Status: 62 of 62 modules complete ✔ (3-D model + 13 learning sections each) — app v1.1.0

`python3 tools/check_library.py` reports no problems.
- **Assets:** every module has its GLB, metadata and learning JSON.
- **Sections:** all 13 are populated.
- **Parameters:** flow, head, pressure, speed and efficiency are present, plus an empty `reference_model` slot.
- **Care and failures:** installation and maintenance have all four subsections; failure analysis has at least 2 items.
- **Tours and quizzes:** 3 in-app video tours per module; at least 6 quiz questions per module (at least 8 for flagships).
- **Validation:** the Khronos glTF validator reports 0 errors and 0 warnings on all 140 GLBs (62 models, 62 flow overlays, 16 teaching overlays).
- **Valves & piping parameters:** size, pressure rating, temperature and flow capacity (design-class ranges) plus the `reference_model` slot.

| Family | Modules |
|---|---|
| 1 · Centrifugal & rotodynamic (16) | end suction (OH1), horizontal split case (BB1), horizontal multistage ★ (BB4), vertical turbine ★ (VS1), vertical can (VS6), vertical inline, submersible borewell, submersible sewage, vertical sump/cantilever, self-priming, axial flow, mixed flow, slurry ★, magnetic drive, canned motor, regenerative turbine |
| 2 · Rotary PD (8) | external gear, internal gear, twin screw, three screw, progressive cavity, rotary lobe, sliding vane, peristaltic |
| 3 · Reciprocating PD (4) | piston, plunger, diaphragm metering, AODD |
| 4 · Special-purpose (3) | jet pump/eductor, airlift, Archimedes screw |
| 5 · Applications (8) | boiler feedwater, firewater package, chemical dosing, condensate extraction, cooling water, hydraulic power pack, lube oil, sewage station — each `built_from` a core design |
| 6 · Valves & piping (23, EQ-118…140) | needle, pinch, float, foot, solenoid, three-way, four-way, vacuum relief, pressure sustaining, steam trap, flame arrestor, rupture disc, sight glass, flow indicator, pipe spool, pipe manifold, orifice plate, flow nozzle, venturi tube, pig launcher, pig receiver, pipe insulation, pipe tracing |

### v1.1 changes
- **Working operation made visible:** motors now show a squirrel-cage rotor (skewed bars, end rings) and stator windings; the firewater diesel engine has running pistons and connecting rods; every model has flow polylines for live particles; the player's X-ray mode ghosts static parts so moving internals stay in view.
- **New player features:** X-ray, live flow particles (with port gating), How-it-works step player, library search / bookmarks / progress, Tools tab (calculators, datasheet editor, notes, compare, measure, isolate/hide parts).
- **23 valves & piping models** with cutaway, explode, Operate animation (morphs for pinch sleeve, trap condensate, rupture-disc burst), flow and teaching overlays.

Phases follow the requested roadmap. Phase 1 has 12 core modules, phase 2 has 12 intermediate modules, phase 3 holds the specialist and application modules, and phase 4 the valves & piping items (see `catalog.json`).

## Open items needing data from you
- **WPIL WVT-30-18:** fill `engineering_parameters.reference_model` in `content/rotodynamic_a.py` from the WPIL datasheet or GA drawing. If you want the geometry matched (stages, bowl diameter, column), the model can be re-proportioned in `pumps/vertical_turbine_pump.py`.
- **Specific products for other modules:** add a `reference_model={...}` entry to the module's `params` dict and rebuild with `python3 build_content.py`.
- **Standards editions:** these are marked "to be verified" and should be confirmed against the current publications.

## How to resume / extend
1. Restore the repo: `git clone <github repo>`, or `git clone pump3d.bundle pump3d`.
2. `pip install bpy --break-system-packages`, then run:
   - `python3 build.py` (about 1 min)
   - `python3 build_content.py`
   - `python3 tools/check_library.py`
   - `python3 tools/update_docs.py` (README catalogue + performance table)
3. Viewers:
   - `viewer/index.html?model=<id>&cut=1&ovl=pressure` (dev/screenshot viewer)
   - `viewer/library.html?m=<id>` (full learning-library reference player)
   - Serve the repo root on port 8765, after `cd viewer && npm install three@0.170.0`.
4. To add a module:
   - Add it to `catalog.json`.
   - Create `pumps/<id>.py` (geometry + `META`) and a `MODULES['<id>'] = mod(...)` entry in `content/`.
   - Build, run the checker, and commit.

## Conventions (don't break these)
- Blender Z-up metres in the scripts; glTF Y-up output.
- Cutaway keeps +Y (Blender); Y-axis PD pumps keep −X.
- Section faces use material `section`. Animation clips are exactly `Operate` (2 s loop) and `Explode` (1 s).
- Every part needs a `components` entry.
- Content part ids are cross-checked at build time.
- Overlays come from `m.overlay(kind, obj, title, description, split=, xray=)` and `m.annotate(kind, text, pos)`.
