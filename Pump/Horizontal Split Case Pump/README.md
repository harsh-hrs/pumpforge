# Horizontal Split Case Pump — model output

Generated model files for the Horizontal Split Case (axially split, between-bearings, single-stage,
double-suction) centrifugal pump. Educational geometry model with illustrative proportions — not OEM CAD.

**Source of truth:** `C:\dev\equipment-learning\src\equipment\pumps\horizontal-split-case\` (builders,
registry, content). Re-export with `npx tsx tools/export-horizontal-split-case.ts --copy "<this folder>\model"`
from `C:\dev\equipment-learning`. These files are copies; edit the source, not these.

| File | Contents |
|---|---|
| `model/model.glb` | High detail — 149.4 k triangles, 140 meshes, 1.18 MB (meshopt) |
| `model/model-low.glb` | Low detail — 59.8 k triangles, 140 meshes, 0.62 MB |
| `model/report.json` | Export + budget report |
| `model/hsc-descriptor.json` | Component registry / viewer descriptor (ids = GLB node names), variants, explode offsets, maintenance-sequence data |
| `model/hsc-content.json` | Component learning records in the app's content schema + references + illustrative curves |
| `model/hsc-extended-content.json` | Lessons, quiz bank, failures & symptoms, materials, standards, procedures, checklists, working-principle and thrust lessons |

GLBs use `EXT_meshopt_compression` + `KHR_mesh_quantization` (three.js: `GLTFLoader.setMeshoptDecoder(MeshoptDecoder)`).
World frame: metres, +Y up, floor y = 0, shaft axis along X at y = 0.95 m, +X = drive end, suction +Z, discharge −Z.
