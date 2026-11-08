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
| 1. Needle Valve | 3 k | 0.1 MB | 4 | flow |
| 2. Pinch Valve | 11 k | 0.4 MB | 6 | flow |
| 3. Float Valve | 4 k | 0.1 MB | 6 | flow |
| 4. Foot Valve | 10 k | 0.3 MB | 7 | flow |
| 5. Solenoid Valve | 6 k | 0.2 MB | 6 | flow, magnetic_field |
| 6. Three-Way Valve | 10 k | 0.3 MB | 5 | flow |
| 7. Four-Way Valve | 11 k | 0.3 MB | 6 | flow |
| 8. Vacuum Relief Valve | 9 k | 0.3 MB | 7 | flow |
| 9. Pressure Sustaining Valve | 16 k | 0.5 MB | 5 | flow |
| 10. Steam Trap | 4 k | 0.1 MB | 5 | flow |
| 11. Flame Arrestor | 20 k | 0.6 MB | 4 | flow, quench |
| 12. Rupture Disc | 8 k | 0.3 MB | 4 | flow, pressure |
| 13. Sight Glass | 14 k | 0.4 MB | 5 | flow |
| 14. Flow Indicator | 10 k | 0.3 MB | 4 | flow |
| 15. Pipe Spool | 9 k | 0.3 MB | 5 | flow |
| 16. Pipe Manifold | 12 k | 0.4 MB | 7 | flow |
| 17. Orifice Plate | 6 k | 0.2 MB | 4 | flow, pressure |
| 18. Flow Nozzle | 6 k | 0.2 MB | 4 | flow, pressure |
| 19. Venturi Tube | 6 k | 0.2 MB | 3 | flow, pressure |
| 20. Pig Launcher | 11 k | 0.4 MB | 6 | flow |
| 21. Pig Receiver | 9 k | 0.3 MB | 6 | flow |
| 22. Pipe Insulation System | 4 k | 0.2 MB | 5 | flow, heat_loss |
| 23. Pipe Tracing System | 6 k | 0.2 MB | 5 | flow, heat_input |
| 24. End Suction Centrifugal Pump | 62 k | 1.7 MB | 19 | flow |
| 25. Horizontal Split Case Pump | 66 k | 1.8 MB | 22 | flow |
| 26. Horizontal Multistage Pump | 149 k | 3.4 MB | 34 | flow, pressure, thrust |
| 27. Vertical Turbine Pump | 106 k | 2.8 MB | 41 | flow, pressure, thrust, installation |
| 28. Vertical Can Pump | 112 k | 2.9 MB | 40 | flow |
| 29. Vertical Inline Pump | 54 k | 1.5 MB | 14 | flow |
| 30. Submersible Borewell Pump | 99 k | 2.3 MB | 43 | flow |
| 31. Submersible Sewage Pump | 39 k | 1.0 MB | 13 | flow |
| 32. Vertical Sump / Cantilever Pump | 53 k | 1.4 MB | 16 | flow |
| 33. Self-Priming Centrifugal Pump | 52 k | 1.5 MB | 19 | flow |
| 34. Axial Flow Pump | 61 k | 1.7 MB | 21 | flow |
| 35. Mixed Flow Pump | 64 k | 1.8 MB | 24 | flow |
| 36. Slurry Pump | 74 k | 2.0 MB | 21 | flow, wear |
| 37. Magnetic Drive Pump | 58 k | 1.6 MB | 19 | flow |
| 38. Canned Motor Pump | 42 k | 1.2 MB | 12 | flow |
| 39. Regenerative Turbine Pump | 33 k | 1.0 MB | 11 | flow |
| 40. External Gear Pump | 25 k | 0.7 MB | 16 | flow |
| 41. Internal Gear Pump | 38 k | 1.2 MB | 17 | flow |
| 42. Twin Screw Pump | 112 k | 2.5 MB | 16 | flow |
| 43. Three Screw Pump | 82 k | 1.8 MB | 18 | flow |
| 44. Progressive Cavity Pump | 82 k | 2.0 MB | 18 | flow |
| 45. Rotary Lobe Pump | 34 k | 1.1 MB | 18 | flow |
| 46. Sliding Vane Pump | 35 k | 1.1 MB | 21 | flow |
| 47. Peristaltic Pump | 36 k | 1.1 MB | 16 | flow |
| 48. Piston Pump | 46 k | 1.3 MB | 31 | flow |
| 49. Plunger Pump | 50 k | 1.4 MB | 38 | flow |
| 50. Diaphragm Metering Pump | 43 k | 1.2 MB | 18 | flow |
| 51. Air-Operated Double Diaphragm Pump | 46 k | 1.4 MB | 25 | flow |
| 52. Jet Pump / Eductor | 17 k | 0.5 MB | 6 | flow |
| 53. Airlift Pump | 33 k | 1.0 MB | 15 | flow |
| 54. Archimedes Screw Pump | 47 k | 1.2 MB | 14 | flow |
| 55. Boiler Feedwater Pump | 131 k | 3.1 MB | 32 | flow, pressure, thrust |
| 56. Firewater Pump Package | 88 k | 2.5 MB | 33 | flow |
| 57. Chemical Dosing System | 69 k | 1.9 MB | 30 | flow |
| 58. Condensate Extraction Pump | 131 k | 3.4 MB | 47 | flow |
| 59. Cooling Water Pump | 69 k | 1.9 MB | 22 | flow |
| 60. Hydraulic Power Pack Pump | 27 k | 0.9 MB | 21 | flow |
| 61. Lubricating Oil Pump | 140 k | 2.8 MB | 31 | flow |
| 62. Sewage Pumping System | 67 k | 1.7 MB | 21 | flow |
| 63. Reciprocating Compressor | 40 k | 1.3 MB | 21 | flow |
| 64. Rotary Screw Compressor | 44 k | 1.2 MB | 16 | flow, pressure |
| 65. Rotary Vane Compressor | 28 k | 0.9 MB | 24 | flow |
| 66. Roots Blower | 10 k | 0.3 MB | 11 | flow |
| 67. Side Channel Blower | 24 k | 0.8 MB | 11 | flow |
| 68. Axial Flow Fan | 9 k | 0.3 MB | 6 | flow |
| 69. Centrifugal Fan | 29 k | 0.9 MB | 13 | flow |
| 70. Induced Draft Fan | 29 k | 0.9 MB | 15 | flow |
| 71. Forced Draft Fan | 30 k | 1.0 MB | 16 | flow |
| 72. Primary Air Fan | 30 k | 1.0 MB | 17 | flow |
| 73. Steam Turbine | 59 k | 1.8 MB | 11 | flow, pressure |
| 74. Gas Turbine | 65 k | 1.9 MB | 10 | flow, pressure |
| 75. Hydraulic Turbine | 20 k | 0.6 MB | 7 | flow |
| 76. Expander Turbine | 10 k | 0.3 MB | 6 | flow, pressure |
| 77. Rotary Vacuum Pump | 28 k | 0.9 MB | 20 | flow |
| 78. Liquid Ring Vacuum Pump | 31 k | 0.9 MB | 16 | flow |
| 79. Dry Screw Vacuum Pump | 69 k | 1.7 MB | 16 | flow, pressure |
| 80. Vacuum Ejector | 12 k | 0.3 MB | 8 | flow, pressure |
| 81. Engine-Driven Generator | 20 k | 0.7 MB | 17 | flow |
| 82. Alternator | 10 k | 0.4 MB | 7 | flow, magnetic_field |
| 83. Diesel Generator Set | 23 k | 0.8 MB | 17 | flow |
| 84. Variable Frequency Drive (VFD) | 6 k | 0.2 MB | 14 | flow, waveforms |
| 85. Soft Starter | 4 k | 0.2 MB | 12 | flow, waveforms |
| 86. Magnetic Coupling | 23 k | 0.7 MB | 10 | flow, magnetic_field |
| 87. Torque Limiter | 9 k | 0.3 MB | 6 | flow, torque |
| 88. Speed Reducer | 30 k | 0.8 MB | 7 | flow |
| 89. Belt Drive Assembly | 37 k | 1.1 MB | 14 | flow |
| 90. Chain Drive Assembly | 38 k | 1.4 MB | 14 | flow |
| 91. Flywheel Assembly | 25 k | 0.8 MB | 15 | flow |
| 92. Rotor Assembly | 9 k | 0.3 MB | 12 | flow, balance |
| 93. Double Pipe Heat Exchanger | 6 k | 0.2 MB | 4 | flow, temperature |
| 94. Air Cooled Heat Exchanger | 8 k | 0.3 MB | 9 | flow |
| 95. Spiral Heat Exchanger | 8 k | 0.2 MB | 5 | flow |
| 96. Jacketed Vessel | 15 k | 0.4 MB | 6 | flow |
| 97. Agitated Reactor | 16 k | 0.4 MB | 9 | flow |
| 98. Pressure Reactor | 14 k | 0.4 MB | 8 | flow |
| 99. Autoclave | 6 k | 0.2 MB | 10 | flow |
| 100. Packed Bed Reactor | 20 k | 0.6 MB | 5 | flow, temperature |
| 101. Fluidized Bed Reactor | 13 k | 0.3 MB | 7 | flow |
| 102. Deaerator | 35 k | 1.0 MB | 8 | flow |
| 103. Boiler Feedwater Tank | 11 k | 0.3 MB | 5 | flow |
| 104. Hotwell | 6 k | 0.2 MB | 6 | flow |
| 105. Surge Vessel | 12 k | 0.3 MB | 6 | flow |
| 106. Knockout Drum | 10 k | 0.2 MB | 6 | flow |
| 107. Gas-Liquid Separator | 12 k | 0.3 MB | 7 | flow |
| 108. Three-Phase Separator | 11 k | 0.3 MB | 8 | flow |
| 109. Scrubber Vessel | 9 k | 0.3 MB | 9 | flow |
| 110. Demister Vessel | 11 k | 0.3 MB | 7 | flow |
| 111. Chimney / Stack | 10 k | 0.3 MB | 8 | flow |
| 112. Silencer | 4 k | 0.1 MB | 5 | flow, noise |
| 113. Gas Holder | 5 k | 0.2 MB | 5 | flow |
| 114. LPG Storage Bullet | 12 k | 0.3 MB | 6 | flow |
| 115. Cryogenic Storage Tank | 5 k | 0.2 MB | 8 | flow |
| 116. Floating Roof Tank | 7 k | 0.2 MB | 7 | flow |
| 117. Pressure Storage Tank | 7 k | 0.2 MB | 6 | flow |
| 118. Apron Feeder | 7 k | 0.4 MB | 7 | flow |
| 119. Vibrating Feeder | 7 k | 0.2 MB | 6 | flow |
| 120. Rotary Airlock Feeder | 2 k | 0.1 MB | 6 | flow |
| 121. Screw Feeder | 25 k | 0.8 MB | 13 | flow |
| 122. Weigh Feeder | 5 k | 0.2 MB | 11 | flow |
| 123. Vibrating Screen | 8 k | 0.3 MB | 8 | flow |
| 124. Trommel Screen | 17 k | 0.6 MB | 7 | flow |
| 125. Grizzly Feeder | 8 k | 0.3 MB | 8 | flow |
| 126. Jaw Crusher | 3 k | 0.1 MB | 7 | flow, wear |
| 127. Cone Crusher | 5 k | 0.2 MB | 7 | flow, wear |
| 128. Gyratory Crusher | 5 k | 0.2 MB | 8 | flow, wear |
| 129. Impact Crusher | 2 k | 0.1 MB | 5 | flow, wear |
| 130. Hammer Crusher | 3 k | 0.1 MB | 5 | flow, wear |
| 131. Roller Crusher | 6 k | 0.2 MB | 8 | flow, wear |
| 132. Stacker | 3 k | 0.1 MB | 6 | flow |
| 133. Reclaimer | 5 k | 0.2 MB | 7 | flow |
| 134. Stacker Reclaimer | 5 k | 0.2 MB | 7 | flow |
| 135. Tripper Conveyor | 7 k | 0.2 MB | 8 | flow |
| 136. Shuttle Conveyor | 4 k | 0.2 MB | 8 | flow |
| 137. Drag Chain Conveyor | 5 k | 0.3 MB | 8 | flow |
| 138. Pneumatic Conveying System | 12 k | 0.3 MB | 7 | flow |
| 139. Screw Jack | 47 k | 1.2 MB | 12 | flow |
| 140. Gantry Crane | 1 k | 0.1 MB | 6 | flow |
| 141. Jib Crane | 1 k | 0.0 MB | 5 | flow |
| 142. Monorail Hoist | 1 k | 0.1 MB | 5 | flow |
| 143. Electric Winch | 7 k | 0.2 MB | 6 | flow |
| 144. Hydraulic Power Unit | 3 k | 0.1 MB | 9 | flow, pressure |
| 145. Hydraulic Cylinder | 3 k | 0.1 MB | 6 | flow, pressure |
| 146. Hydraulic Accumulator | 9 k | 0.2 MB | 6 | flow, pressure |
| 147. Hydraulic Control Valve Assembly | 3 k | 0.1 MB | 9 | flow, pressure |
| 148. Vibrating Conveyor | 2 k | 0.1 MB | 7 | flow |
| 149. Bucket Wheel Excavator | 4 k | 0.3 MB | 9 | flow |
| 150. Reboiler | 10 k | 0.3 MB | 9 | flow |
| 151. Preheater | 14 k | 0.4 MB | 8 | flow, temperature |
| 152. Economizer | 12 k | 0.4 MB | 7 | flow, temperature |
| 153. Superheater | 9 k | 0.2 MB | 8 | flow, temperature |
| 154. Air Preheater | 8 k | 0.3 MB | 8 | flow, temperature |
| 155. Steam Generator | 9 k | 0.3 MB | 11 | flow |
| 156. Waste Heat Recovery Boiler | 22 k | 0.5 MB | 10 | flow, temperature |
| 157. Flash Evaporator | 21 k | 0.5 MB | 9 | flow, pressure |
| 158. Falling Film Evaporator | 23 k | 0.6 MB | 11 | flow, temperature |
| 159. Forced Circulation Evaporator | 16 k | 0.5 MB | 11 | flow, temperature |
| 160. Multiple Effect Evaporator | 44 k | 1.1 MB | 19 | flow, pressure |
| 161. Spray Dryer | 8 k | 0.3 MB | 8 | flow, temperature |
| 162. Fluidized Bed Dryer | 10 k | 0.3 MB | 9 | flow, temperature |
| 163. Flash Dryer | 11 k | 0.3 MB | 9 | flow, temperature |
| 164. Paddle Dryer | 4 k | 0.2 MB | 10 | flow, temperature |
| 165. Vacuum Dryer | 20 k | 0.4 MB | 5 | flow, pressure |
| 166. Fluidized Bed Combustor | 14 k | 0.4 MB | 11 | flow, temperature |
| 167. Thermal Oxidizer | 10 k | 0.3 MB | 9 | flow, temperature |
| 168. Incinerator | 7 k | 0.3 MB | 9 | flow, temperature |
| 169. Gas Fired Furnace | 3 k | 0.1 MB | 10 | flow, temperature |
| 170. Electric Furnace | 6 k | 0.2 MB | 12 | flow, temperature |
| 171. Heat Recovery System | 13 k | 0.3 MB | 8 | flow, temperature |
| 172. Quench Tower | 8 k | 0.2 MB | 9 | flow, temperature |
| 173. Cooling Coil | 3 k | 0.1 MB | 7 | flow, temperature |
| 174. Cooling Water Distribution System | 24 k | 0.5 MB | 12 | flow, temperature |
| 175. Cartridge Filter | 16 k | 0.5 MB | 8 | flow, pressure |
| 176. Membrane Filter | 5 k | 0.2 MB | 8 | flow, pressure |
| 177. Microfiltration System | 6 k | 0.2 MB | 10 | flow, pressure |
| 178. Ultrafiltration System | 8 k | 0.3 MB | 11 | flow, pressure |
| 179. Nanofiltration System | 21 k | 0.5 MB | 8 | flow, pressure |
| 180. Disc Stack Centrifuge | 11 k | 0.3 MB | 8 | flow, pressure |
| 181. Decanter Centrifuge | 5 k | 0.2 MB | 8 | flow, pressure |
| 182. Basket Centrifuge | 8 k | 0.3 MB | 8 | flow, pressure |
| 183. Magnetic Separator | 6 k | 0.2 MB | 9 | flow, magnetic_field |
| 184. Flotation Cell | 6 k | 0.2 MB | 8 | flow, pressure |
| 185. Dissolved Air Flotation Unit | 12 k | 0.3 MB | 11 | flow, pressure |
| 186. Oil-Water Separator | 2 k | 0.1 MB | 8 | flow, pressure |
| 187. Coalescer | 17 k | 0.4 MB | 7 | flow, pressure |
| 188. Molecular Sieve Adsorber | 30 k | 0.6 MB | 10 | flow, temperature |
| 189. Activated Alumina Adsorber | 13 k | 0.3 MB | 8 | flow, pressure |
| 190. Desiccant Dryer | 27 k | 0.5 MB | 9 | flow, pressure |
| 191. Gas Dehydration Unit | 56 k | 1.5 MB | 12 | flow, temperature |
| 192. Sand Trap | 8 k | 0.2 MB | 6 | flow, pressure |
| 193. Bauxite Stockpile Reclaimer | 3 k | 0.2 MB | 12 | flow, pressure |
| 194. Bauxite Washing Drum | 8 k | 0.3 MB | 9 | flow, pressure |
| 195. Bauxite Grinding Mill | 8 k | 0.3 MB | 7 | flow, pressure |
| 196. Bauxite Slurry Mixing Tank | 6 k | 0.2 MB | 9 | flow, pressure |
| 197. Digestion Autoclave | 25 k | 0.6 MB | 15 | flow, pressure |
| 198. Digestion Heater | 16 k | 0.4 MB | 7 | flow, temperature |
| 199. Multi-Stage Flash Vessel | 23 k | 0.6 MB | 11 | flow, pressure |
| 200. Desilication Tank | 9 k | 0.3 MB | 8 | flow, temperature |
| 201. Precipitation Tank Agitator | 13 k | 0.3 MB | 7 | flow, temperature |
| 202. Seed Classification Unit | 7 k | 0.2 MB | 9 | flow, pressure |
| 203. Classification Hydrocyclone | 9 k | 0.3 MB | 6 | flow, pressure |
| 204. Red Mud Washer | 17 k | 0.5 MB | 19 | flow, pressure |
| 205. Mud Settling Tank | 8 k | 0.3 MB | 10 | flow, pressure |
| 206. Sand Separator | 3 k | 0.1 MB | 6 | flow, pressure |
| 207. Alumina Hydrate Filter | 13 k | 0.3 MB | 11 | flow, pressure |
| 208. Hydrate Washing System | 33 k | 0.7 MB | 13 | flow, pressure |
| 209. Calcination Fluidized Bed Cooler | 7 k | 0.2 MB | 5 | flow, temperature |
| 210. Alumina Cooler | 7 k | 0.3 MB | 7 | flow, temperature |
| 211. Alumina Storage Silo | 9 k | 0.2 MB | 6 | flow, pressure |
| 212. Alumina Pneumatic Conveying System | 14 k | 0.4 MB | 8 | flow, pressure |
| 213. Causticization Tank | 11 k | 0.3 MB | 10 | flow, pressure |
| 214. Oxalate Removal System | 9 k | 0.3 MB | 11 | flow, temperature |
| 215. Sodium Oxalate Filter | 10 k | 0.3 MB | 7 | flow, pressure |
| 216. Process Liquor Clarifier | 12 k | 0.4 MB | 9 | flow, pressure |
| 217. Alumina Dust Collection System | 3 k | 0.1 MB | 9 | flow, pressure |
| 218. Clariflocculator | 7 k | 0.3 MB | 10 | flow, pressure |
| 219. Flash Mixer | 4 k | 0.2 MB | 7 | flow, pressure |
| 220. Flocculation Tank | 3 k | 0.1 MB | 7 | flow, pressure |
| 221. Lamella Clarifier | 2 k | 0.1 MB | 8 | flow, pressure |
| 222. Chlorination System | 4 k | 0.1 MB | 9 | flow, pressure |
| 223. UV Disinfection System | 6 k | 0.2 MB | 7 | flow, pressure |
| 224. Ozonation System | 20 k | 0.4 MB | 10 | flow, pressure |
| 225. Demineralization Plant | 35 k | 0.8 MB | 16 | flow, pressure |
| 226. Mixed Bed Polisher | 12 k | 0.3 MB | 6 | flow, pressure |
| 227. Water Softener | 21 k | 0.5 MB | 12 | flow, pressure |
| 228. Degasser Tower | 6 k | 0.3 MB | 10 | flow, pressure |
| 229. Chemical Preparation Tank | 8 k | 0.2 MB | 8 | flow, pressure |
| 230. Chemical Injection Skid | 17 k | 0.4 MB | 10 | flow, pressure |
| 231. Instrument Air Dryer | 23 k | 0.5 MB | 13 | flow, temperature |
| 232. Air Receiver Dryer Package | 15 k | 0.4 MB | 10 | flow, temperature |
| 233. Nitrogen Generation System | 34 k | 0.7 MB | 13 | flow, pressure |
| 234. Nitrogen Storage Vessel | 26 k | 0.6 MB | 10 | flow, temperature |
| 235. Steam Distribution Header | 12 k | 0.4 MB | 10 | flow, pressure |
| 236. Condensate Recovery System | 25 k | 0.6 MB | 14 | flow, pressure |
| 237. Cooling Tower Basin | 6 k | 0.2 MB | 11 | flow, temperature |
| 238. Cooling Tower Fan | 3 k | 0.1 MB | 8 | flow, pressure |
| 239. Cooling Tower Gearbox | 18 k | 0.5 MB | 7 | flow, pressure |
| 240. Emergency Diesel Firewater System | 15 k | 0.4 MB | 15 | flow, pressure |
| 241. Sewage Lift Station | 11 k | 0.3 MB | 13 | flow, pressure |
| 242. Effluent Treatment Plant | 20 k | 0.7 MB | 30 | flow, pressure |
| 243. Labyrinth Seal | 11 k | 0.3 MB | 4 | flow, pressure |
| 244. Oil Seal | 9 k | 0.2 MB | 7 | flow, pressure |
| 245. Gland Packing Assembly | 9 k | 0.3 MB | 7 | flow, pressure |
| 246. Thrust Bearing Assembly | 11 k | 0.3 MB | 7 | flow, pressure, thrust |
| 247. Journal Bearing | 5 k | 0.2 MB | 6 | flow, pressure |
| 248. Bearing Housing | 14 k | 0.4 MB | 10 | flow, temperature |
| 249. Mechanical Cartridge Seal | 27 k | 0.8 MB | 9 | flow, pressure |
| 250. Expansion Coupling | 11 k | 0.4 MB | 7 | flow, pressure, thrust |
| 251. Universal Joint | 2 k | 0.1 MB | 4 | flow, pressure |
| 252. Torsional Coupling | 5 k | 0.2 MB | 4 | flow, pressure |
| 253. Shaft Sleeve | 10 k | 0.3 MB | 4 | flow, wear |
| 254. Wear Ring | 15 k | 0.4 MB | 5 | flow, pressure, wear |
| 255. Impeller | 11 k | 0.3 MB | 3 | flow, pressure |
| 256. Rotor | 4 k | 0.2 MB | 4 | flow, magnetic_field |
| 257. Stator | 12 k | 0.4 MB | 5 | flow, magnetic_field |
| 258. Gear Assembly | 8 k | 0.3 MB | 5 | flow, pressure |
| 259. Lubricating Oil Skid | 25 k | 0.6 MB | 11 | flow, pressure |
| 260. Grease Lubrication System | 7 k | 0.2 MB | 10 | flow, temperature |
| 261. Centralized Lubrication System | 7 k | 0.2 MB | 20 | flow, pressure |
| 262. Oil Mist Lubrication System | 9 k | 0.3 MB | 11 | flow, pressure |
| 263. Shaft Alignment System | 3 k | 0.1 MB | 7 | flow, pressure |
| 264. Dynamic Balancing Machine | 3 k | 0.1 MB | 8 | flow, pressure |
| 265. Vibration Monitoring System | 4 k | 0.2 MB | 8 | flow, pressure |
| 266. Online Condition Monitoring System | 6 k | 0.2 MB | 15 | flow, pressure |
| 267. Laser Alignment Equipment | 5 k | 0.2 MB | 9 | flow, pressure |
| 268. Emergency Pressure Relief System | 15 k | 0.4 MB | 9 | flow, pressure |
| 269. Blowdown Tank | 15 k | 0.4 MB | 6 | flow, temperature |
| 270. Closed Drain System | 21 k | 0.5 MB | 9 | flow, pressure |
| 271. Open Drain System | 4 k | 0.1 MB | 10 | flow, pressure |
| 272. Flare Stack | 14 k | 0.4 MB | 12 | flow, temperature |
| 273. Flare Knockout Drum | 19 k | 0.4 MB | 10 | flow, pressure |
| 274. Gas Scrubbing System | 14 k | 0.5 MB | 10 | flow, pressure |
| 275. Wet Scrubber | 11 k | 0.3 MB | 10 | flow, pressure |
| 276. Dry Scrubber | 9 k | 0.2 MB | 7 | flow, pressure |
| 277. Baghouse Dust Collector | 8 k | 0.3 MB | 12 | flow, pressure |
| 278. Ventilation System | 7 k | 0.2 MB | 10 | flow, pressure |
| 279. Emergency Ventilation Fan | 5 k | 0.2 MB | 13 | flow, pressure |
| 280. Fire and Gas Detection System | 12 k | 0.3 MB | 8 | flow, pressure |
| 281. Firewater Monitor | 9 k | 0.2 MB | 4 | flow, pressure |
| 282. Foam Firefighting System | 15 k | 0.3 MB | 8 | flow, pressure |

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
