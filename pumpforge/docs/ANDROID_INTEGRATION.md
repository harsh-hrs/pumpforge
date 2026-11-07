# Using the models in an Android app

The GLB files are standard glTF 2.0. They pass the Khronos glTF Validator with 0 errors and 0 warnings. Any Android 3-D stack that reads glTF can load them:

| Stack | Notes |
|---|---|
| **SceneView** (Kotlin, wraps Google Filament) | Recommended for a native app. Supports animations, morph targets, PBR and picking |
| Filament `gltfio` directly | Lowest level, full control |
| Unity / Godot | Import the GLB (Unity via glTFast). Node names and extras are kept |
| Flutter `model_viewer_plus` / WebView + three.js | Fastest to prototype. `viewer/index.html` is a complete reference implementation of every interaction |

## Recommended app structure
```
assets/models/<pump_id>.glb
assets/models/<pump_id>_flow.glb
assets/models/<pump_id>_<overlay>.glb     # pressure, thrust, wear, installation (flagships)
assets/learning/<pump_id>.json            # 13-section learning module
assets/learning/index.json
assets/meta/<pump_id>.json
assets/catalog.json
```

## SceneView sketch (Kotlin)
API names differ slightly between SceneView versions. Treat this as a guide and check the version you use.
```kotlin
val instance = modelLoader.createModelInstance("models/vertical_turbine_pump.glb")
val model = ModelNode(modelInstance = instance, scaleToUnits = 1.0f, centerOrigin = null)
sceneView.addChildNode(model)

// Operate (looping)
model.playAnimation(animationName = "Operate", loop = true)

// Explode: either play the clip...
model.playAnimation(animationName = "Explode", loop = false)
// ...or drive positions from a slider using meta.parts[i].explode_offset

// Cutaway: hide '<id>__front' meshes and parts with section_role == "hide"
val asset = instance.asset
meta.parts.forEach { p ->
    p.nodes.filter { it.endsWith("__front") || p.section_role == "hide" }.forEach { name ->
        val e = asset.getFirstEntityByName(name)
        if (e != 0) setVisible(e, !cutaway)   // e.g. remove from / add back to scene, or set layer mask
    }
}
```
**Picking:** use `sceneView.onTapListener`, or Filament `View.pick()`, to get the tapped entity. Then walk up `TransformManager.getParent()` until `asset.getName(entity)` matches a part id in the metadata. Highlight it by changing the emissive factor or swapping the material instance.

**Section faces:** the cut faces are a separate primitive whose material is named `section`. In Filament, find it with `RenderableManager.getMaterialInstanceAt(...)`. In full view, swap in a transparent or disabled instance; in cutaway, restore it.

**Flow overlay:** load `<pump_id>_flow.glb` as a second node with the same transform as the pump, and toggle its visibility.

## Performance
| Module | Triangles | GLB size | Parts | Overlays |
|---|---|---|---|---|
| 1. End Suction Centrifugal Pump | 62 k | 1.7 MB | 19 | flow |
| 2. Horizontal Split Case Pump | 66 k | 1.8 MB | 22 | flow |
| 3. Horizontal Multistage Pump | 149 k | 3.4 MB | 34 | flow, pressure, thrust |
| 4. Vertical Turbine Pump | 106 k | 2.8 MB | 41 | flow, pressure, thrust, installation |
| 5. Vertical Can Pump | 112 k | 2.9 MB | 40 | flow |
| 6. Vertical Inline Pump | 54 k | 1.5 MB | 14 | flow |
| 7. Submersible Borewell Pump | 99 k | 2.3 MB | 43 | flow |
| 8. Submersible Sewage Pump | 39 k | 1.0 MB | 13 | flow |
| 9. Vertical Sump / Cantilever Pump | 53 k | 1.4 MB | 16 | flow |
| 10. Self-Priming Centrifugal Pump | 52 k | 1.5 MB | 19 | flow |
| 11. Axial Flow Pump | 61 k | 1.7 MB | 21 | flow |
| 12. Mixed Flow Pump | 64 k | 1.8 MB | 24 | flow |
| 13. Slurry Pump | 74 k | 2.0 MB | 21 | flow, wear |
| 14. Magnetic Drive Pump | 58 k | 1.6 MB | 19 | flow |
| 15. Canned Motor Pump | 42 k | 1.2 MB | 12 | flow |
| 16. Regenerative Turbine Pump | 33 k | 1.0 MB | 11 | flow |
| 17. External Gear Pump | 25 k | 0.7 MB | 16 | flow |
| 18. Internal Gear Pump | 38 k | 1.2 MB | 17 | flow |
| 19. Twin Screw Pump | 112 k | 2.5 MB | 16 | flow |
| 20. Three Screw Pump | 82 k | 1.8 MB | 18 | flow |
| 21. Progressive Cavity Pump | 82 k | 2.0 MB | 18 | flow |
| 22. Rotary Lobe Pump | 34 k | 1.1 MB | 18 | flow |
| 23. Sliding Vane Pump | 35 k | 1.1 MB | 21 | flow |
| 24. Peristaltic Pump | 36 k | 1.1 MB | 16 | flow |
| 25. Piston Pump | 46 k | 1.3 MB | 31 | flow |
| 26. Plunger Pump | 50 k | 1.4 MB | 38 | flow |
| 27. Diaphragm Metering Pump | 43 k | 1.2 MB | 18 | flow |
| 28. Air-Operated Double Diaphragm Pump | 46 k | 1.4 MB | 25 | flow |
| 29. Jet Pump / Eductor | 17 k | 0.5 MB | 6 | flow |
| 30. Airlift Pump | 33 k | 1.0 MB | 15 | flow |
| 31. Archimedes Screw Pump | 47 k | 1.2 MB | 14 | flow |
| 32. Boiler Feedwater Pump | 131 k | 3.1 MB | 32 | flow, pressure, thrust |
| 33. Firewater Pump Package | 88 k | 2.5 MB | 33 | flow |
| 34. Chemical Dosing System | 69 k | 1.9 MB | 30 | flow |
| 35. Condensate Extraction Pump | 131 k | 3.4 MB | 47 | flow |
| 36. Cooling Water Pump | 69 k | 1.9 MB | 22 | flow |
| 37. Hydraulic Power Pack Pump | 27 k | 0.9 MB | 21 | flow |
| 38. Lubricating Oil Pump | 140 k | 2.8 MB | 31 | flow |
| 39. Sewage Pumping System | 67 k | 1.7 MB | 21 | flow |
| 40. Needle Valve | 3 k | 0.1 MB | 4 | flow |
| 41. Pinch Valve | 11 k | 0.4 MB | 6 | flow |
| 42. Float Valve | 4 k | 0.1 MB | 6 | flow |
| 43. Foot Valve | 10 k | 0.3 MB | 7 | flow |
| 44. Solenoid Valve | 6 k | 0.2 MB | 6 | flow, magnetic_field |
| 45. Three-Way Valve | 10 k | 0.3 MB | 5 | flow |
| 46. Four-Way Valve | 11 k | 0.3 MB | 6 | flow |
| 47. Vacuum Relief Valve | 9 k | 0.3 MB | 7 | flow |
| 48. Pressure Sustaining Valve | 16 k | 0.5 MB | 5 | flow |
| 49. Steam Trap | 4 k | 0.1 MB | 5 | flow |
| 50. Flame Arrestor | 20 k | 0.6 MB | 4 | flow, quench |
| 51. Rupture Disc | 8 k | 0.3 MB | 4 | flow, pressure |
| 52. Sight Glass | 14 k | 0.4 MB | 5 | flow |
| 53. Flow Indicator | 10 k | 0.3 MB | 4 | flow |
| 54. Pipe Spool | 9 k | 0.3 MB | 5 | flow |
| 55. Pipe Manifold | 12 k | 0.4 MB | 7 | flow |
| 56. Orifice Plate | 6 k | 0.2 MB | 4 | flow, pressure |
| 57. Flow Nozzle | 6 k | 0.2 MB | 4 | flow, pressure |
| 58. Venturi Tube | 6 k | 0.2 MB | 3 | flow, pressure |
| 59. Pig Launcher | 11 k | 0.4 MB | 6 | flow |
| 60. Pig Receiver | 9 k | 0.3 MB | 6 | flow |
| 61. Pipe Insulation System | 4 k | 0.2 MB | 5 | flow, heat_loss |
| 62. Pipe Tracing System | 6 k | 0.2 MB | 5 | flow, heat_input |

The largest model is about 149 k triangles, and the whole set of 140 GLBs is about 77 MB uncompressed, including flow and teaching overlays. Every model runs comfortably on mid-range phones. Bundle the models as on-demand downloads (Play Asset Delivery) or fetch them from a CDN, rather than shipping them all in the APK. If needed, the build can add meshopt or Draco compression later. Filament supports both, but the decoder must be enabled.

## Learning modules (`output/learning/<id>.json`)
- `sections_order` lists the 13 sections; `sections.<name>` holds each one. Render them as tabs or as a scrolling lesson.
- `working_principle.steps[]` contain `text`, `part`, `cut`, `operate`, `overlay` and `explode`. Apply them as one action when the learner taps a step.
- `video_tutorials[]` are **in-app tours**. Each `script[]` line has `narration`, `duration_s` and an `action`. The action can set `view` (iso | front | orbit | part), `cut`, `explode`, `operate`, `overlay` and `highlight`. Play the narration with Android `TextToSpeech` or a recorded voice-over, apply the action, and wait `duration_s`. No video files need to be hosted. The page published with this project ("PumpForge Model Review") is a working reference player.
- `meta.flow_paths[]` (see MODEL_SPEC) can drive live flow particles; honour each path's `active` phase ranges.
- `assessment.questions[]` use `answer` as the index into `options`. A question with a `part` field can highlight that part after the learner answers.
- `engineering_parameters.reference_model` is an empty datasheet slot. Fill it when a specific manufacturer model is chosen; the ranges above it are design-class guidance only.

## Teaching overlays
`meta.overlays` lists each overlay's `file`, `title`, `description`, `render` (`normal` | `xray`) and `annotations[]` (`text` + `anchor` in model coordinates). Load the overlay GLB at the same transform as the model.

- For `render: "xray"` (the slurry wear map), disable depth test and depth write on its materials and draw it last, so the wear zones show through the liners.
- Overlay meshes tagged `section_role: front` must be hidden in cutaway mode, like part meshes.
- Draw annotations as screen-space labels projected from `anchor`.
