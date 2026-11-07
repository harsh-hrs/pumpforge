# PumpForge model specification (v1.1)

Every pump ships as three files, plus optional teaching overlays. The set covers all 62 catalogue entries (39 pumps, 23 valves & piping items):

| File | Purpose |
|---|---|
| `output/glb/<pump_id>.glb` | The model: geometry, PBR materials, part hierarchy, `Operate` and `Explode` animations |
| `output/glb/<pump_id>_flow.glb` | Optional flow-path overlay (suction = blue, discharge = orange, air = green). Same coordinate frame, so load it as a sibling node at the same transform |
| `output/meta/<pump_id>.json` | Engineering metadata: per-part function, construction, materials, operating conditions, failure modes, inspection, plus label anchors, bounding boxes, explode offsets, standards and references |

## Coordinates and units
- glTF 2.0 binary, **metres**, **+Y up**, **+Z toward the default viewer (front)**.
- Ground or mounting face is at y = 0, except the vertical turbine pump: y = 0 is the discharge-head sole plate, and the bowl assembly hangs below it.
- No textures. All materials are metallic-roughness PBR factors, so files stay small and colours can be swapped at runtime.

## Node hierarchy
```
<pump_id>                     root (extras: pump_id, title, model_type, disclaimer)
 ├─ <part_id>                 part node (extras: part_id, part_name, group, section_role, explode_offset)
 │    ├─ <part_id>            mesh (whole part)          section_role = keep | hide
 │    ├─ <part_id>__back      mesh (kept half)           section_role = back
 │    └─ <part_id>__front     mesh (removed in cutaway)  section_role = front
```
- **Picking:** raycast hits a mesh. Walk up the parents until you reach a node with `extras.part_id`, then look up that id in `meta.parts[]` and `meta.components[info_ref]`.
- **Groups**, such as `rotating_element`, `bowl_assembly`, `motor`, `bearings`, `mechanical_seal`, `relief_valve`, `check_valves` and `air_side`, let you filter parts or colour them by group.

## Cutaway (section view)
- Hide every node whose `section_role` is `front` or `hide`.
- Faces created by the cut use a material named **`section`** (red-orange). Show `section` primitives only in cutaway mode. In full view they sit inside the solid and can produce a faint seam line.
- Impellers use split hub and shroud halves, while the blades stay whole (`<id>_blades`, role `keep`). The cutaway therefore shows the blade passages, and the halves still rotate together.
- Gear, lobe, screw, vane and reciprocating rotors are generally kept whole. Housings, magnets and cans around them are split.
- In system models (sewage station, borewell, Archimedes screw), the civil structure such as the wet well, well casing or trough is a permanent half shell (role `keep`). The cover slab uses role `hide`.

## Explode
Either play the **`Explode`** clip (1 s, from assembled to exploded; play it in reverse to reassemble), or drive a slider yourself:
`node.position = rest_position + explode_offset * t`, with `t` from 0 to 1. `explode_offset` is in each part node's extras and in the metadata JSON.

## Operate
`Operate` is a seamless 2 s loop of the working motion:
- **Vertical turbine pump:** the shafts, impellers, collets, couplings, rotor and fan rotate counter-clockwise viewed from the motor end.
- **External gear pump:** the drive gear and idler counter-rotate in correct mesh (1 rev per loop).
- **AODD pump:** the shaft and plates reciprocate (triangle wave). Diaphragms flex through the morph targets `shaft_plus` and `shaft_minus`. The check balls lift and seat in the correct phase, and the air spool shifts at each stroke end.

- **All other models** follow the same rules. Shafts, impellers, rotors, gears, lobes, screws and vanes rotate about their axis (sliding vanes also extend and retract). Crankshafts, connecting rods, crossheads and plungers move with true slider-crank kinematics. Valves lift in phase. The diaphragm metering pump uses morph targets as the AODD pump does. Peristaltic shoes rotate.
- **No moving parts** (jet pump/eductor, airlift pump): the separate `*_tracers` parts carry animated spheres along the flow path (group `flow_tracers`). Hide them along with the flow overlay if you want a static view.

`Operate` and `Explode` touch different nodes (meshes versus part nodes), so both can play at the same time.

## Metadata JSON (abridged)
```json
{
  "schema": "pumpforge.model/1.0", "pump_id": "...", "title": "...", "category": "...",
  "summary": "...", "classification": {...}, "model_configuration": {...},
  "standards": [{"id": "API 610", "relevance": "...", "edition": "to be verified"}],
  "parts": [{"id": "...", "name": "...", "group": "...", "section_role": "split|keep|hide",
             "nodes": ["..."], "pivot": [x,y,z], "explode_offset": [x,y,z],
             "bbox_min": [...], "bbox_max": [...], "label_anchor": [...], "center": [...],
             "info_ref": "component key"}],
  "components": {"<info_ref>": {"function": "...", "construction": "...", "material": "...",
                  "operating_conditions": "...", "failure_modes": ["..."], "inspection": ["..."]}}
}
```

## Accuracy policy
- These are **explanatory engineering models**, generated procedurally from typical published arrangements. Proportions are representative. They are not certified manufacturer drawings and must not be used for fabrication or compliance.
- Standard editions marked "to be verified" must be confirmed against the current published edition before you quote them.
- Typical values, such as air pressure ranges, are labelled as typical. Always defer to the manufacturer's data.

## Teaching overlays (schema 1.1)
Besides `<id>_flow.glb`, a model can export `<id>_<kind>.glb` overlays. The current kinds are `pressure`, `thrust`, `wear`, `installation`, `magnetic_field` (solenoid valve), `quench` (flame arrestor), `heat_loss` (pipe insulation) and `heat_input` (heat tracing).

- `meta.overlays[kind]` gives the file, title, description, render mode and annotations.
- Overlay materials: `pressure_0` … `pressure_9` (blue → red, low → high pressure), `thrust` (magenta, impeller thrust), `counter_force` (green, balancing force), and `wear_light`, `wear_moderate`, `wear_severe` (yellow, pink, purple).
- Overlay halves carry `section_role` `back` or `front`, so they respond to the cutaway the same way part meshes do.
- `meta.library` gives `no`, `phase`, `hi_family`, `flagship`, `api_610_type`, `built_from` (for application modules) and, for valves & piping, `eq_id` and `subcategory`.

## Flow paths and morph targets (v1.1)
- `meta.flow_paths[]` gives each flow route as a polyline in glTF coordinates: `name`, `kind` (liquid, steam, gas, condensate, oil, air …), `radius`, `points[]`, an optional `speed[]` (relative speed per point, e.g. faster through a vena contracta) and an optional `active[]` list of `[start, end]` phase ranges (0–1 of the Operate loop). A path with `active` should only show flow during those ranges — this is how three-way / four-way valves and manifolds show which port is open. The player draws animated particles along these polylines.
- Some valves animate by **morph targets** inside the `Operate` clip: pinch-valve sleeve (`pinch`), steam-trap condensate level (`fill`), rupture-disc dome (`bulge`) and petals (`burst`). glTF viewers play them as normal weight animation.

## Learning module (`pumpforge.learning/1.0`)
See `pumpforge/learning.py` and `docs/ANDROID_INTEGRATION.md#learning-modules`. Every part id referenced by a step, maintenance task, failure or quiz is cross-checked against the model at build time.
