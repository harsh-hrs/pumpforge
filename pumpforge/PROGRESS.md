# PROGRESS — PumpForge Pump Learning Library

_Last updated: 2026-11-07_

## Status: 282 of 282 modules complete ✔ (3-D model + 13 learning sections each) — app v1.8.0

All requested sections (EQ-118 … EQ-360) are complete. Instrumentation & Controls is reserved as a future department.

`python3 tools/check_library.py` reports no problems.
- **Assets:** every module has its GLB, metadata and learning JSON.
- **Sections:** all 13 are populated.
- **Parameters:** flow, head, pressure, speed and efficiency are present, plus an empty `reference_model` slot.
- **Care and failures:** installation and maintenance have all four subsections; failure analysis has at least 2 items.
- **Tours and quizzes:** 3 in-app video tours per module; at least 6 quiz questions per module (at least 8 for flagships).
- **Validation:** the Khronos glTF validator reports 0 errors and 0 warnings on all GLBs (282 models, 282 flow overlays and the teaching overlays).
- **Valves & piping parameters:** size, pressure rating, temperature and flow capacity (design-class ranges) plus the `reference_model` slot.

| Family | Modules |
|---|---|
| 1 · Centrifugal & rotodynamic (16) | end suction (OH1), horizontal split case (BB1), horizontal multistage ★ (BB4), vertical turbine ★ (VS1), vertical can (VS6), vertical inline, submersible borewell, submersible sewage, vertical sump/cantilever, self-priming, axial flow, mixed flow, slurry ★, magnetic drive, canned motor, regenerative turbine |
| 2 · Rotary PD (8) | external gear, internal gear, twin screw, three screw, progressive cavity, rotary lobe, sliding vane, peristaltic |
| 3 · Reciprocating PD (4) | piston, plunger, diaphragm metering, AODD |
| 4 · Special-purpose (3) | jet pump/eductor, airlift, Archimedes screw |
| 5 · Applications (8) | boiler feedwater, firewater package, chemical dosing, condensate extraction, cooling water, hydraulic power pack, lube oil, sewage station — each `built_from` a core design |
| 6 · Valves & piping (23, EQ-118…140) | needle, pinch, float, foot, solenoid, three-way, four-way, vacuum relief, pressure sustaining, steam trap, flame arrestor, rupture disc, sight glass, flow indicator, pipe spool, pipe manifold, orifice plate, flow nozzle, venturi tube, pig launcher, pig receiver, pipe insulation, pipe tracing |
| 7 · Rotating equipment (30, EQ-141…170) | compressors, blowers, fans, turbines, vacuum pumps & ejector, generators, drives & power transmission |
| 8 · Static equipment (25, EQ-171…195) | heat exchangers, reactors, vessels & separators, stack/silencer/gas holder, storage tanks & sphere |
| 9 · Material handling & heavy machinery (32, EQ-196…227) | feeders, screens, crushers, stockyard machines & BWE, conveyors, pneumatic conveying, lifting equipment, hydraulics |
| 10 · Thermal & process (25, EQ-228…252) | exchangers & boilers, heat recovery, evaporators, dryers, combustion & fired equipment, gas cooling, cooling water |
| 11 · Filtration & separation (18, EQ-253…270) | filters & membranes, centrifuges, magnetic & flotation, oil–water, adsorbers & dryers, gas dehydration, sand trap |
| 12 · Alumina refinery — Bayer process (25, EQ-271…295) | bauxite handling & grinding, digestion & flash, desilication, residue settling & washing, precipitation & classification, hydrate filtration, calcination products & silo, liquor purification, dust collection |
| 13 · Water treatment & utilities (25, EQ-296…320) | clarification, disinfection, ion exchange, chemical systems, compressed air, nitrogen, steam & condensate, cooling towers, diesel firewater, sewage lift station, ETP |
| 14 · Mechanical components & maintenance (25, EQ-321…345) | seals, bearings, couplings, pump components, rotor & stator, gears, lubrication systems, alignment & balancing, condition monitoring |
| 15 · Safety & environmental (15, EQ-346…360) | relief & blowdown, drains, flare & KO drum, scrubbers, baghouse, ventilation, F&G detection, firewater monitor, foam |

### v1.8 changes
- **One library, arranged by department** in this order: 1 Valves & Piping, 2 Pumps, 3 Rotating Equipment, 4 Static Equipment, 5 Material Handling, 6 Thermal & Process, 7 Filtration & Separation, 8 Alumina Refinery, 9 Water & Utilities, 10 Mechanical Components, 11 Safety & Environmental, 12 Instrumentation & Controls (future).
- Modules renumbered 1–282 continuously in that order (EQ numbers unchanged); department numbers shown in the model picker, library headings (with module ranges) and filter chips; `tools/arrange.py` keeps the order.

### v1.7 changes
- **25 mechanical components & maintenance models** (EQ-321…345; parameters: size, speed, load capacity, operating conditions) and **15 safety & environmental models** (EQ-346…360; parameters: size, capacity, operating conditions, performance), each with 13-section learning content.
- Moving internals: true Cardan-joint kinematics (non-uniform output), torsional-coupling damping, gear trains in mesh, tilting-pad oil wedges, oil rings, progressive-divider sequencing, alignment brackets and laser units turning, balancing pedestals vibrating, PSV disc lifting, flare and pilot flames, bag-row pulse cleaning, damper blades opening, oscillating firewater monitor, foam blanket spreading as the fire dies.
- New overlays: magnetic field (rotor, stator), wear (shaft sleeve, wear ring), thrust (thrust bearing, coupling), temperature (bearing housing, flare radiation, blowdown).
- New calculators: bearing L10 life, permissible residual unbalance (ISO 21940), relubrication quantity, rim-and-face alignment, PSV area (API 520 gas), flare radiation, baghouse cloth area, ventilation dilution.

### v1.6 changes
- **25 water treatment & utilities models** (EQ-296…320) with 13-section learning content (required parameters: size, capacity, operating conditions, power rating + `reference_model` slot).
- Moving internals: paddles, rakes and agitators turn; flocs grow and settle; moisture / oxygen fronts climb adsorbent beds; UV lamps and corona glow; float valves and level floats move; fans, gearboxes (spiral-bevel + helical), diesel engine and pumps turn; wet-well and tank levels rise and fall.
- New overlays: temperature (dryers, LN₂ storage, cooling-tower basin), pressure (clarifiers, disinfection, IX, PSA, steam, pumps).
- New calculators: chlorine dose & C·t, mixing power from G, ion-exchange resin volume & regenerant, air-receiver size.

### v1.5 changes
- **25 alumina refinery (Bayer process) models** (EQ-271…295) with 13-section learning content (required parameters: size, capacity, operating conditions, power rating + `reference_model` slot).
- **Departments:** the library and model picker are grouped into 12 departments with filter chips; empty departments show as "coming soon" / "future expansion" (Instrumentation & Controls).
- Moving internals: drums and mills turn with tyres/girth gears, thickener rakes sweep, agitators turn, slurry levels rise and fall, flash vessels boil, hydrate particles grow and settle; process liquids are drawn semi-transparent so internals stay visible.
- New calculators: Bayer liquor yield (A/C ratio), thickener unit area, slurry density / % solids.

### v1.4 changes
- **25 thermal & process models** (EQ-228…252) and **18 filtration & separation models** (EQ-253…270), each with 13-section learning content.
- Required parameters: thermal — size, heat duty, operating temperature, capacity; filtration — size, capacity, operating pressure, separation performance (+ `reference_model` slot).
- Moving internals: flames flicker, rotors/fans/pumps/kilns turn, bubbles rise, films fall, beds fluidise, mass-transfer zones travel down adsorbers, centrifuges eject solids, skimmers run.
- New overlays: temperature (exchangers, boilers, dryers, furnaces), pressure (membranes, filters, flash/vacuum, DAF), magnetic field (drum separator).
- New calculators: flash fraction, dryer load, excess air, boiler efficiency, cooling-tower range/approach/make-up, Stokes velocity, centrifuge g-force, membrane flux/recovery/rejection, adsorber bed life.

### v1.3 changes
- **32 material handling & heavy machinery models** (EQ-196…227) with 13-section learning content (required parameters: size, power rating, speed, capacity + `reference_model` slot).
- Moving material everywhere: ore/coal lumps ride apron pans, belts and booms, fall through grizzlies and screens, are nipped in crushers; the shuttle belt reverses; cranes travel and hoist with scaling ropes.
- New teaching overlays: wear (jaw, cone, gyratory, impact, hammer and roll crushers), pressure (HPU, hydraulic cylinder, accumulator, control valve manifold).
- New calculators (shown most-relevant-first per module): bed-flow capacity, belt conveyor power (simplified ISO 5048), screw capacity, Bond crushing energy & reduction ratio, hoist power & rope force, hydraulic cylinder force/speed, accumulator usable volume, drum critical speed.

### v1.2 changes
- **30 rotating-equipment models** (EQ-141…170) and **25 static-equipment models** (EQ-171…195) with 13-section learning content.
- New teaching overlays: waveforms (VFD, soft starter), torque (torque limiter), balance (rotor assembly), magnetic field (alternator, magnetic coupling), temperature (heat exchangers, packed bed), noise (silencer), pressure (screw compressor, turbines, ejector, vacuum pump).
- Liquids animate their level (morph targets) in vessels and tanks; agitators, fans, rotors, gates, doors, dampers, roofs and bells move.
- New calculators: shaft power/torque, synchronous speed & slip, compressor power, drive ratio, flywheel energy, shell thickness (UG-27), LMTD & area, horizontal tank volume, Souders–Brown separator sizing.

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
