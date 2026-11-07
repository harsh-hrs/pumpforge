# PumpForge — Pump, Valve & Piping Learning Library (62 modules, interactive 3-D)

Procedurally built, engineering-proportioned 3-D models plus structured learning content for an Android app. The library has 62 modules:

- **39 pumps** (modules 1–39), classified by working mechanism following the Hydraulic Institute's rotodynamic / positive-displacement families, on the three-phase roadmap: core, intermediate, and specialist & applications.
- **23 valves & piping items** (modules 40–62, equipment numbers EQ-118 to EQ-140, phase 4): special, automated, control and safety valves; steam trap; flame arrestor; rupture disc; sight glass and flow indicator; pipe spool and manifold; orifice plate, flow nozzle and venturi tube; pig launcher and receiver; insulation and heat-tracing systems.

Every module has the same **13 sections**:

| # | Section | Where it lives |
|---|---|---|
| 1 | Introduction (definition, applications, key points) | `output/learning/<id>.json` |
| 2 | 3-D model, rotatable and zoomable | `output/glb/<id>.glb` |
| 3 | Exploded view | `Explode` clip / `explode_offset` per part |
| 4 | Cross-section | split meshes + `section` material (cutaway) |
| 5 | Working principle, animated | `Operate` clip + step list with part highlights |
| 6 | Flow animation | `<id>_flow.glb` overlay (tracers for jet/airlift) |
| 7 | Components, with the function and material of every part | `output/meta/<id>.json#components` |
| 8 | Engineering parameters: design-class ranges plus an empty `reference_model` datasheet slot | learning JSON |
| 9 | Installation (foundation, alignment, piping, commissioning) | learning JSON |
| 10 | Maintenance (routine, periodic, overhaul, lubrication) | learning JSON |
| 11 | Failure analysis (symptoms, causes, remedies, affected part) | learning JSON |
| 12 | Video tutorials: three in-app tours (intro, operation, maintenance), each a narrated script that drives the camera, cutaway, explode, animation and overlays | learning JSON |
| 13 | Assessment: quizzes, including "identify the component" questions tied to 3-D parts | learning JSON |

**Flagship modules** have extra teaching overlays, which are separate GLBs that the app can toggle:

- **Vertical Turbine Pump.** A WPIL WVT-series (WVT-30-18) learning case. Overlays show stage-by-stage pressure, the down-thrust path to the motor thrust bearing, and sump levels with submergence (ANSI/HI 9.8).
- **Slurry Pump.** An x-ray map of wear zones by severity: throatbush, impeller eye, cutwater, liner and back shroud.
- **Horizontal Multistage Pump.** Overlays show stage-by-stage pressure build-up, and impeller thrust against the balance-drum force, with the leak-off line.

Engineering parameters are **typical published ranges for the design class**, marked "to be verified". They are not ratings of a specific product. Each module has an empty `reference_model` block to fill in from the chosen manufacturer's datasheet.

## Model catalogue — 62 of 62 built

![All models in cutaway](docs/catalogue_cutaways.jpg)

| Module | Iso | Cutaway | Exploded |
|---|---|---|---|
| **1 · Centrifugal & Rotodynamic Pumps** | | | |
| 1. End Suction Centrifugal Pump<br><sub>`end_suction_centrifugal_pump` · phase 1 · 19 parts</sub> | ![](output/previews/end_suction_centrifugal_pump_iso.jpg) | ![](output/previews/end_suction_centrifugal_pump_cutaway.jpg) | ![](output/previews/end_suction_centrifugal_pump_exploded.jpg) |
| 2. Horizontal Split Case Pump<br><sub>`horizontal_split_case_pump` · phase 1 · 22 parts</sub> | ![](output/previews/horizontal_split_case_pump_iso.jpg) | ![](output/previews/horizontal_split_case_pump_cutaway.jpg) | ![](output/previews/horizontal_split_case_pump_exploded.jpg) |
| 3. Horizontal Multistage Pump ★<br><sub>`horizontal_multistage_pump` · phase 1 · 34 parts · overlays: pressure, thrust</sub> | ![](output/previews/horizontal_multistage_pump_iso.jpg) | ![](output/previews/horizontal_multistage_pump_cutaway.jpg) | ![](output/previews/horizontal_multistage_pump_exploded.jpg) |
| 4. Vertical Turbine Pump ★<br><sub>`vertical_turbine_pump` · phase 1 · 41 parts · overlays: pressure, thrust, installation</sub> | ![](output/previews/vertical_turbine_pump_iso.jpg) | ![](output/previews/vertical_turbine_pump_cutaway.jpg) | ![](output/previews/vertical_turbine_pump_exploded.jpg) |
| 5. Vertical Can Pump<br><sub>`vertical_can_pump` · phase 2 · 40 parts</sub> | ![](output/previews/vertical_can_pump_iso.jpg) | ![](output/previews/vertical_can_pump_cutaway.jpg) | ![](output/previews/vertical_can_pump_exploded.jpg) |
| 6. Vertical Inline Pump<br><sub>`vertical_inline_pump` · phase 2 · 14 parts</sub> | ![](output/previews/vertical_inline_pump_iso.jpg) | ![](output/previews/vertical_inline_pump_cutaway.jpg) | ![](output/previews/vertical_inline_pump_exploded.jpg) |
| 7. Submersible Borewell Pump<br><sub>`submersible_borewell_pump` · phase 1 · 43 parts</sub> | ![](output/previews/submersible_borewell_pump_iso.jpg) | ![](output/previews/submersible_borewell_pump_cutaway.jpg) | ![](output/previews/submersible_borewell_pump_exploded.jpg) |
| 8. Submersible Sewage Pump<br><sub>`submersible_sewage_pump` · phase 1 · 13 parts</sub> | ![](output/previews/submersible_sewage_pump_iso.jpg) | ![](output/previews/submersible_sewage_pump_cutaway.jpg) | ![](output/previews/submersible_sewage_pump_exploded.jpg) |
| 9. Vertical Sump / Cantilever Pump<br><sub>`vertical_sump_cantilever_pump` · phase 1 · 16 parts</sub> | ![](output/previews/vertical_sump_cantilever_pump_iso.jpg) | ![](output/previews/vertical_sump_cantilever_pump_cutaway.jpg) | ![](output/previews/vertical_sump_cantilever_pump_exploded.jpg) |
| 10. Self-Priming Centrifugal Pump<br><sub>`self_priming_centrifugal_pump` · phase 2 · 19 parts</sub> | ![](output/previews/self_priming_centrifugal_pump_iso.jpg) | ![](output/previews/self_priming_centrifugal_pump_cutaway.jpg) | ![](output/previews/self_priming_centrifugal_pump_exploded.jpg) |
| 11. Axial Flow Pump<br><sub>`axial_flow_pump` · phase 1 · 21 parts</sub> | ![](output/previews/axial_flow_pump_iso.jpg) | ![](output/previews/axial_flow_pump_cutaway.jpg) | ![](output/previews/axial_flow_pump_exploded.jpg) |
| 12. Mixed Flow Pump<br><sub>`mixed_flow_pump` · phase 2 · 24 parts</sub> | ![](output/previews/mixed_flow_pump_iso.jpg) | ![](output/previews/mixed_flow_pump_cutaway.jpg) | ![](output/previews/mixed_flow_pump_exploded.jpg) |
| 13. Slurry Pump ★<br><sub>`slurry_pump` · phase 1 · 21 parts · overlays: wear</sub> | ![](output/previews/slurry_pump_iso.jpg) | ![](output/previews/slurry_pump_cutaway.jpg) | ![](output/previews/slurry_pump_exploded.jpg) |
| 14. Magnetic Drive Pump<br><sub>`magnetic_drive_pump` · phase 2 · 19 parts</sub> | ![](output/previews/magnetic_drive_pump_iso.jpg) | ![](output/previews/magnetic_drive_pump_cutaway.jpg) | ![](output/previews/magnetic_drive_pump_exploded.jpg) |
| 15. Canned Motor Pump<br><sub>`canned_motor_pump` · phase 2 · 12 parts</sub> | ![](output/previews/canned_motor_pump_iso.jpg) | ![](output/previews/canned_motor_pump_cutaway.jpg) | ![](output/previews/canned_motor_pump_exploded.jpg) |
| 16. Regenerative Turbine Pump<br><sub>`regenerative_turbine_pump` · phase 3 · 11 parts</sub> | ![](output/previews/regenerative_turbine_pump_iso.jpg) | ![](output/previews/regenerative_turbine_pump_cutaway.jpg) | ![](output/previews/regenerative_turbine_pump_exploded.jpg) |
| **2 · Rotary Positive-Displacement Pumps** | | | |
| 17. External Gear Pump<br><sub>`external_gear_pump` · phase 1 · 16 parts</sub> | ![](output/previews/external_gear_pump_iso.jpg) | ![](output/previews/external_gear_pump_cutaway.jpg) | ![](output/previews/external_gear_pump_exploded.jpg) |
| 18. Internal Gear Pump<br><sub>`internal_gear_pump` · phase 3 · 17 parts</sub> | ![](output/previews/internal_gear_pump_iso.jpg) | ![](output/previews/internal_gear_pump_cutaway.jpg) | ![](output/previews/internal_gear_pump_exploded.jpg) |
| 19. Twin Screw Pump<br><sub>`twin_screw_pump` · phase 2 · 16 parts</sub> | ![](output/previews/twin_screw_pump_iso.jpg) | ![](output/previews/twin_screw_pump_cutaway.jpg) | ![](output/previews/twin_screw_pump_exploded.jpg) |
| 20. Three Screw Pump<br><sub>`three_screw_pump` · phase 2 · 18 parts</sub> | ![](output/previews/three_screw_pump_iso.jpg) | ![](output/previews/three_screw_pump_cutaway.jpg) | ![](output/previews/three_screw_pump_exploded.jpg) |
| 21. Progressive Cavity Pump<br><sub>`progressive_cavity_pump` · phase 1 · 18 parts</sub> | ![](output/previews/progressive_cavity_pump_iso.jpg) | ![](output/previews/progressive_cavity_pump_cutaway.jpg) | ![](output/previews/progressive_cavity_pump_exploded.jpg) |
| 22. Rotary Lobe Pump<br><sub>`rotary_lobe_pump` · phase 2 · 18 parts</sub> | ![](output/previews/rotary_lobe_pump_iso.jpg) | ![](output/previews/rotary_lobe_pump_cutaway.jpg) | ![](output/previews/rotary_lobe_pump_exploded.jpg) |
| 23. Sliding Vane Pump<br><sub>`sliding_vane_pump` · phase 2 · 21 parts</sub> | ![](output/previews/sliding_vane_pump_iso.jpg) | ![](output/previews/sliding_vane_pump_cutaway.jpg) | ![](output/previews/sliding_vane_pump_exploded.jpg) |
| 24. Peristaltic Pump<br><sub>`peristaltic_pump` · phase 2 · 16 parts</sub> | ![](output/previews/peristaltic_pump_iso.jpg) | ![](output/previews/peristaltic_pump_cutaway.jpg) | ![](output/previews/peristaltic_pump_exploded.jpg) |
| **3 · Reciprocating Positive-Displacement Pumps** | | | |
| 25. Piston Pump<br><sub>`piston_pump` · phase 3 · 31 parts</sub> | ![](output/previews/piston_pump_iso.jpg) | ![](output/previews/piston_pump_cutaway.jpg) | ![](output/previews/piston_pump_exploded.jpg) |
| 26. Plunger Pump<br><sub>`plunger_pump` · phase 3 · 38 parts</sub> | ![](output/previews/plunger_pump_iso.jpg) | ![](output/previews/plunger_pump_cutaway.jpg) | ![](output/previews/plunger_pump_exploded.jpg) |
| 27. Diaphragm Metering Pump<br><sub>`diaphragm_metering_pump` · phase 1 · 18 parts</sub> | ![](output/previews/diaphragm_metering_pump_iso.jpg) | ![](output/previews/diaphragm_metering_pump_cutaway.jpg) | ![](output/previews/diaphragm_metering_pump_exploded.jpg) |
| 28. Air-Operated Double Diaphragm Pump<br><sub>`aodd_pump` · phase 2 · 25 parts</sub> | ![](output/previews/aodd_pump_iso.jpg) | ![](output/previews/aodd_pump_cutaway.jpg) | ![](output/previews/aodd_pump_exploded.jpg) |
| **4 · Special-Purpose Pumping Systems** | | | |
| 29. Jet Pump / Eductor<br><sub>`jet_pump_eductor` · phase 3 · 6 parts</sub> | ![](output/previews/jet_pump_eductor_iso.jpg) | ![](output/previews/jet_pump_eductor_cutaway.jpg) | ![](output/previews/jet_pump_eductor_exploded.jpg) |
| 30. Airlift Pump<br><sub>`airlift_pump` · phase 3 · 15 parts</sub> | ![](output/previews/airlift_pump_iso.jpg) | ![](output/previews/airlift_pump_cutaway.jpg) | ![](output/previews/airlift_pump_exploded.jpg) |
| 31. Archimedes Screw Pump<br><sub>`archimedes_screw_pump` · phase 3 · 14 parts</sub> | ![](output/previews/archimedes_screw_pump_iso.jpg) | ![](output/previews/archimedes_screw_pump_cutaway.jpg) | ![](output/previews/archimedes_screw_pump_exploded.jpg) |
| **5 · Industrial Pump Applications** | | | |
| 32. Boiler Feedwater Pump<br><sub>`boiler_feedwater_pump` · phase 3 · 32 parts · overlays: pressure, thrust</sub> | ![](output/previews/boiler_feedwater_pump_iso.jpg) | ![](output/previews/boiler_feedwater_pump_cutaway.jpg) | ![](output/previews/boiler_feedwater_pump_exploded.jpg) |
| 33. Firewater Pump Package<br><sub>`firewater_pump_package` · phase 3 · 33 parts</sub> | ![](output/previews/firewater_pump_package_iso.jpg) | ![](output/previews/firewater_pump_package_cutaway.jpg) | ![](output/previews/firewater_pump_package_exploded.jpg) |
| 34. Chemical Dosing System<br><sub>`chemical_dosing_system` · phase 3 · 30 parts</sub> | ![](output/previews/chemical_dosing_system_iso.jpg) | ![](output/previews/chemical_dosing_system_cutaway.jpg) | ![](output/previews/chemical_dosing_system_exploded.jpg) |
| 35. Condensate Extraction Pump<br><sub>`condensate_extraction_pump` · phase 3 · 47 parts</sub> | ![](output/previews/condensate_extraction_pump_iso.jpg) | ![](output/previews/condensate_extraction_pump_cutaway.jpg) | ![](output/previews/condensate_extraction_pump_exploded.jpg) |
| 36. Cooling Water Pump<br><sub>`cooling_water_pump` · phase 3 · 22 parts</sub> | ![](output/previews/cooling_water_pump_iso.jpg) | ![](output/previews/cooling_water_pump_cutaway.jpg) | ![](output/previews/cooling_water_pump_exploded.jpg) |
| 37. Hydraulic Power Pack Pump<br><sub>`hydraulic_power_pack_pump` · phase 3 · 21 parts</sub> | ![](output/previews/hydraulic_power_pack_pump_iso.jpg) | ![](output/previews/hydraulic_power_pack_pump_cutaway.jpg) | ![](output/previews/hydraulic_power_pack_pump_exploded.jpg) |
| 38. Lubricating Oil Pump<br><sub>`lubricating_oil_pump` · phase 3 · 31 parts</sub> | ![](output/previews/lubricating_oil_pump_iso.jpg) | ![](output/previews/lubricating_oil_pump_cutaway.jpg) | ![](output/previews/lubricating_oil_pump_exploded.jpg) |
| 39. Sewage Pumping System<br><sub>`sewage_pumping_system` · phase 3 · 21 parts</sub> | ![](output/previews/sewage_pumping_system_iso.jpg) | ![](output/previews/sewage_pumping_system_cutaway.jpg) | ![](output/previews/sewage_pumping_system_exploded.jpg) |
| **6 · Valves & Piping – Additional Equipment** | | | |
| 40. Needle Valve<br><sub>`needle_valve` · EQ-118 · phase 4 · 4 parts</sub> | ![](output/previews/needle_valve_iso.jpg) | ![](output/previews/needle_valve_cutaway.jpg) | ![](output/previews/needle_valve_exploded.jpg) |
| 41. Pinch Valve<br><sub>`pinch_valve` · EQ-119 · phase 4 · 6 parts</sub> | ![](output/previews/pinch_valve_iso.jpg) | ![](output/previews/pinch_valve_cutaway.jpg) | ![](output/previews/pinch_valve_exploded.jpg) |
| 42. Float Valve<br><sub>`float_valve` · EQ-120 · phase 4 · 6 parts</sub> | ![](output/previews/float_valve_iso.jpg) | ![](output/previews/float_valve_cutaway.jpg) | ![](output/previews/float_valve_exploded.jpg) |
| 43. Foot Valve<br><sub>`foot_valve` · EQ-121 · phase 4 · 7 parts</sub> | ![](output/previews/foot_valve_iso.jpg) | ![](output/previews/foot_valve_cutaway.jpg) | ![](output/previews/foot_valve_exploded.jpg) |
| 44. Solenoid Valve<br><sub>`solenoid_valve` · EQ-122 · phase 4 · 6 parts · overlays: magnetic_field</sub> | ![](output/previews/solenoid_valve_iso.jpg) | ![](output/previews/solenoid_valve_cutaway.jpg) | ![](output/previews/solenoid_valve_exploded.jpg) |
| 45. Three-Way Valve<br><sub>`three_way_valve` · EQ-123 · phase 4 · 5 parts</sub> | ![](output/previews/three_way_valve_iso.jpg) | ![](output/previews/three_way_valve_cutaway.jpg) | ![](output/previews/three_way_valve_exploded.jpg) |
| 46. Four-Way Valve<br><sub>`four_way_valve` · EQ-124 · phase 4 · 6 parts</sub> | ![](output/previews/four_way_valve_iso.jpg) | ![](output/previews/four_way_valve_cutaway.jpg) | ![](output/previews/four_way_valve_exploded.jpg) |
| 47. Vacuum Relief Valve<br><sub>`vacuum_relief_valve` · EQ-125 · phase 4 · 7 parts</sub> | ![](output/previews/vacuum_relief_valve_iso.jpg) | ![](output/previews/vacuum_relief_valve_cutaway.jpg) | ![](output/previews/vacuum_relief_valve_exploded.jpg) |
| 48. Pressure Sustaining Valve<br><sub>`pressure_sustaining_valve` · EQ-126 · phase 4 · 5 parts</sub> | ![](output/previews/pressure_sustaining_valve_iso.jpg) | ![](output/previews/pressure_sustaining_valve_cutaway.jpg) | ![](output/previews/pressure_sustaining_valve_exploded.jpg) |
| 49. Steam Trap<br><sub>`steam_trap` · EQ-127 · phase 4 · 5 parts</sub> | ![](output/previews/steam_trap_iso.jpg) | ![](output/previews/steam_trap_cutaway.jpg) | ![](output/previews/steam_trap_exploded.jpg) |
| 50. Flame Arrestor<br><sub>`flame_arrestor` · EQ-128 · phase 4 · 4 parts · overlays: quench</sub> | ![](output/previews/flame_arrestor_iso.jpg) | ![](output/previews/flame_arrestor_cutaway.jpg) | ![](output/previews/flame_arrestor_exploded.jpg) |
| 51. Rupture Disc<br><sub>`rupture_disc` · EQ-129 · phase 4 · 4 parts · overlays: pressure</sub> | ![](output/previews/rupture_disc_iso.jpg) | ![](output/previews/rupture_disc_cutaway.jpg) | ![](output/previews/rupture_disc_exploded.jpg) |
| 52. Sight Glass<br><sub>`sight_glass` · EQ-130 · phase 4 · 5 parts</sub> | ![](output/previews/sight_glass_iso.jpg) | ![](output/previews/sight_glass_cutaway.jpg) | ![](output/previews/sight_glass_exploded.jpg) |
| 53. Flow Indicator<br><sub>`flow_indicator` · EQ-131 · phase 4 · 4 parts</sub> | ![](output/previews/flow_indicator_iso.jpg) | ![](output/previews/flow_indicator_cutaway.jpg) | ![](output/previews/flow_indicator_exploded.jpg) |
| 54. Pipe Spool<br><sub>`pipe_spool` · EQ-132 · phase 4 · 5 parts</sub> | ![](output/previews/pipe_spool_iso.jpg) | ![](output/previews/pipe_spool_cutaway.jpg) | ![](output/previews/pipe_spool_exploded.jpg) |
| 55. Pipe Manifold<br><sub>`pipe_manifold` · EQ-133 · phase 4 · 7 parts</sub> | ![](output/previews/pipe_manifold_iso.jpg) | ![](output/previews/pipe_manifold_cutaway.jpg) | ![](output/previews/pipe_manifold_exploded.jpg) |
| 56. Orifice Plate<br><sub>`orifice_plate` · EQ-134 · phase 4 · 4 parts · overlays: pressure</sub> | ![](output/previews/orifice_plate_iso.jpg) | ![](output/previews/orifice_plate_cutaway.jpg) | ![](output/previews/orifice_plate_exploded.jpg) |
| 57. Flow Nozzle<br><sub>`flow_nozzle` · EQ-135 · phase 4 · 4 parts · overlays: pressure</sub> | ![](output/previews/flow_nozzle_iso.jpg) | ![](output/previews/flow_nozzle_cutaway.jpg) | ![](output/previews/flow_nozzle_exploded.jpg) |
| 58. Venturi Tube<br><sub>`venturi_tube` · EQ-136 · phase 4 · 3 parts · overlays: pressure</sub> | ![](output/previews/venturi_tube_iso.jpg) | ![](output/previews/venturi_tube_cutaway.jpg) | ![](output/previews/venturi_tube_exploded.jpg) |
| 59. Pig Launcher<br><sub>`pig_launcher` · EQ-137 · phase 4 · 6 parts</sub> | ![](output/previews/pig_launcher_iso.jpg) | ![](output/previews/pig_launcher_cutaway.jpg) | ![](output/previews/pig_launcher_exploded.jpg) |
| 60. Pig Receiver<br><sub>`pig_receiver` · EQ-138 · phase 4 · 6 parts</sub> | ![](output/previews/pig_receiver_iso.jpg) | ![](output/previews/pig_receiver_cutaway.jpg) | ![](output/previews/pig_receiver_exploded.jpg) |
| 61. Pipe Insulation System<br><sub>`pipe_insulation_system` · EQ-139 · phase 4 · 5 parts · overlays: heat_loss</sub> | ![](output/previews/pipe_insulation_system_iso.jpg) | ![](output/previews/pipe_insulation_system_cutaway.jpg) | ![](output/previews/pipe_insulation_system_exploded.jpg) |
| 62. Pipe Tracing System<br><sub>`pipe_tracing_system` · EQ-140 · phase 4 · 5 parts · overlays: heat_input</sub> | ![](output/previews/pipe_tracing_system_iso.jpg) | ![](output/previews/pipe_tracing_system_cutaway.jpg) | ![](output/previews/pipe_tracing_system_exploded.jpg) |

Per-model triangle counts and file sizes are listed in [docs/ANDROID_INTEGRATION.md](docs/ANDROID_INTEGRATION.md#performance).

## Learning player (v1.1)
`viewer/library.html` is the full player and the source of the Android app. On top of orbit / tap-to-inspect / explode / cutaway / operate it adds:

| Feature | What it does |
|---|---|
| **X-ray** | Ghosts every static part so the moving internals (impellers, pistons, spools, discs, pigs) stay visible while the animation runs |
| **Live flow** | Animated particles run along each flow path, coloured by fluid (liquid, steam, gas, condensate, oil). Gated paths (three/four-way valves, manifold branches) only flow while that port is open in the animation |
| **How it works** | Step-by-step player: each working-principle step moves the camera, highlights the parts and shows the right overlay; manual or auto (6 s per step) |
| **Library** | Search by name, EQ number, category, subcategory or component; bookmarks (★); progress per module (opened, best quiz score) |
| **Tools tab** (for engineers / SMEs) | Calculators: pump power, affinity laws, NPSHa, specific speed, valve Kv/Cv, differential-pressure flowmeter (ISO 5167, simplified), pipe friction (Darcy / Swamee-Jain), insulated-pipe heat loss, unit converter. Editable reference datasheet (saved on the device, copy as JSON), notes per module, side-by-side compare with any other module, distance measurement on the model, isolate / hide parts |

Progress, bookmarks, notes and datasheets are stored on the device only.

## Android app (APK)
`python3 android/build_apk.py --version-name 1.1.0 --version-code 2` builds `android/build/PumpForge-<version>.apk`. It is an offline app that contains all 62 modules, overlays, tours (with text-to-speech), quizzes and the v1.1 player features. See [android/README.md](android/README.md).

## Repository layout
```
build.py                 build all (or selected) models
pumpforge/core.py        modelling kernel: lathe/CSG/split, parts, animation baking, glTF export, metadata
pumpforge/shapes.py      vane (impeller/diffuser) lofts, involute gears, lobes, twisted screws, tubes, arrows
pumpforge/parts.py       reusable assemblies: impellers, volutes, motors, couplings, baseplates, bearings, seals, valves, piping, tracers
pumpforge/vertical.py    vertical-pump parts: bowls, columns, suction bells, discharge heads
pumpforge/recip.py       reciprocating power end: crankshaft, connecting rods, crossheads
pumpforge/splitcase.py   axially split-case (BB1) double-suction pump
pumpforge/common_meta.py shared component engineering notes
pumps/<pump_id>.py       one script per pump: geometry + engineering metadata
pumpforge/learning.py    learning-module schema, tour generator, part-id cross-checks
content/*.py             learning content for the 62 modules (parameters, install, maintenance, failures, quizzes)
build_content.py         builds output/learning/*.json from content + model metadata
tools/check_library.py   rechecks all 62 modules (assets, 13 sections, overlays, quiz counts)
tools/update_docs.py     regenerates the README catalogue table from output/learning/index.json
pumpforge/valvekit.py    valve & piping building blocks: flanges, bolts, handwheels, springs, morph helpers, taps, transmitters
pumps/_eq_*.py           builders for the 23 valves & piping models (one stub file per item in pumps/)
output/glb/              GLB models (+ _flow and teaching overlays: _pressure, _thrust, _wear, _installation, _magnetic_field, _quench, _heat_loss, _heat_input)
output/meta/             per-model engineering metadata JSON
output/learning/         13-section learning module per pump + index.json
output/previews/         rendered previews
viewer/library.html      full learning player (source of the Android app)
viewer/index.html        dev/screenshot viewer (three.js): orbit, tap-to-inspect, explode, cutaway, operate, flow
viewer/shot.js           headless preview renderer (Playwright)
catalog.json             62 modules: family, phase, EQ number, subcategory, key components, API type, built_from, flagship
docs/MODEL_SPEC.md       file format, node naming, cutaway/explode/animation contract
docs/ANDROID_INTEGRATION.md  how to use the models in Android (SceneView/Filament)
PROGRESS.md              status and continuation checklist
android/                 offline Android app (WebView shell, smali sources, build_apk.py)
```

## Build
Requirements: Python 3.11+ with `bpy` (Blender as a Python module, tested with 5.2 LTS).
```bash
pip install bpy            # ~400 MB
python3 build.py           # all models
python3 build.py aodd_pump # one model
python3 build_content.py   # learning modules (no Blender needed)
python3 tools/check_library.py   # recheck all 62 modules
python3 tools/update_docs.py     # refresh README catalogue
```
Building is deterministic: the GLB and JSON files are regenerated from source in seconds.

## Preview locally
```bash
cd viewer && npm install three@0.170.0 && cd ..
python3 -m http.server 8765
# open http://localhost:8765/viewer/index.html
```
Teaching overlays in the dev viewer: `viewer/index.html?model=slurry_pump&cut=1&ovl=wear`. Headless previews: `node viewer/shot.js <pump_id> out.png "cut=1&view=iso"`. Requires Playwright and Chromium.

## Validation
`npx gltf-validator output/glb/*.glb` reports 0 errors and 0 warnings for every file.

## Accuracy statement
These are explanatory engineering models based on typical published arrangements, such as HI and API nomenclature and the standard involute gear form. They are not manufacturer drawings. Standards editions are marked "to be verified" where they have not been confirmed against the current publication.
