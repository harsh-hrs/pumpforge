# End Suction Centrifugal Pump — model output

Generated model files for the End Suction Centrifugal pump: horizontal, single-stage, single-suction, overhung impeller,
radially split volute casing, top discharge, back-pull-out, motor on a common baseplate with a flexible spacer coupling.
This is an educational model with illustrative proportions, not OEM CAD.

**Source of truth:** `C:\dev\equipment-learning\src\equipment\pumps\end-suction-centrifugal\` (builders, registry,
content). The files here are copies; edit the source, not these. To regenerate the GLBs, run
`npm run models:build -- --only end-suction-centrifugal` in `C:\dev\equipment-learning`, then copy
`public\models\pumps\end-suction-centrifugal\*` here.

| File | Contents |
|---|---|
| `model/model.glb` | High detail: 137.7k triangles, 107 meshes, 1.19 MB (meshopt) |
| `model/model-low.glb` | Low detail: 54.0k triangles, 105 meshes, 0.58 MB (phones load this first) |
| `model/stats.json` | Build and budget report, and the list of component ids |
| `model/thumb.png` | Catalog thumbnail |
| `model/es-descriptor.json` | Component registry / viewer descriptor (ids = GLB node names), variants (seal, impeller, bearings), explode offsets, camera presets, section planes |
| `model/es-content.json` | 91 component learning records + 117 references, plus the ILLUSTRATIVE performance-curve dataset (not manufacturer data) |
| `PROGRESS.md` | Build status, known limitations, measured usage, how to resume |

The GLBs use `EXT_meshopt_compression` + `KHR_mesh_quantization` (three.js: `GLTFLoader.setMeshoptDecoder(MeshoptDecoder)`).
World frame: metres, +Y up, floor at y = 0, shaft axis along X at y = 0.55 m. The suction end is at −X, the motor at +X,
and the discharge points up (+Y).

Copied 2026-11-06 from git commit 6b523f8.
