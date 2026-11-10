# PumpForge native (v2.1) — fully native Android app

The Android app is now **fully native**: C++17 + OpenGL ES 3.0 on `android.app.NativeActivity`.
There is **no WebView, no JavaScript, no three.js and no Java/Kotlin code** in the APK. All 282 modules,
every lesson section, quiz, tour and tool of the web library (`viewer/library.html`) are implemented natively,
and the 3-D models are stored in a compact native format.

| | v1.8 (WebView) | v2.0 (native) |
|---|---|---|
| APK size | 58.6 MB | ≈ 22 MB |
| 3-D models in the APK | 172.5 MB `.glb` (55.6 MB zipped) | 95.3 MB `.pfm` (18.2 MB zipped) |
| Rendering | three.js in a WebView | C++ / OpenGL ES 3.0, 4× MSAA |
| Start-up | browser engine + JS parse | native library, no JS |
| ABIs | — | arm64-v8a, armeabi-v7a, x86_64 |

## What is where

```
native/
  src/                 C++ sources (shared by the command-line and the Android Studio build)
    android_main.cpp   NativeActivity glue: EGL, Choreographer frame loop, input queue, back key,
                       TextToSpeech / keyboard dialog / clipboard / system-bar colours through JNI
    linux_main.cpp     desktop test harness (Mesa, headless): scripted taps/drags, screenshots, full sweeps
    app.cpp            lifecycle, frame loop, touch gestures (orbit, pinch-zoom/pan, tap, kinetic scrolling)
    app_data.cpp       catalogue, per-device store (bookmarks, progress, notes, datasheets), module loading
    scene.cpp          port of library.html: applyState, cutaway, X-ray, explode, Operate clip, live-flow
                       particles, overlays + labels, How-it-works steps, tours, highlight, picking, measuring
    render.cpp         renderer: three.js r170 MeshStandardMaterial in GLSL ES 3.00 (RoomEnvironment IBL baked
                       from three itself, sun 1.6 + PCF shadows, shadow-catcher ground, ACES Filmic, sRGB)
    ui.cpp             screens: Home, Catalog, Bookmarks, More (+ Learning Paths, Compare, Calculators, Training,
                       Settings, Help, About), bottom navigation, model picker with search
    ui_viewer.cpp      3-D Viewer screen: header card, 3D View/Exploded/Cutaway/X-ray segments, stage controls,
                       on-model How-it-works player, chips, sticky lesson tabs, every tab's content, part inspector
    ui_widgets.cpp     design system: theme tokens (dark navy / light), cards, pills, toggles, fields, icons, logo
    thumbs.cpp         live 3-D thumbnails (one model rendered per frame, LRU cache) and the rotating Home hero
    calcs.cpp          the 50 engineering calculators (byte-identical output to the web, see Tests)
    model.cpp          .pfm loader, scene graph, LINEAR animation (slerp), morph targets, ray picking
    json.cpp, base.cpp JSON DOM/writer, strings, maths, JS-exact toFixed()
    imgui_gles.cpp     Dear ImGui renderer for GLES 3 with dynamic font atlas textures
  third_party/imgui    Dear ImGui 1.93 (MIT)
  assets/fonts         IBM Plex Sans / Sans Condensed / Mono subsets (OFL) + DejaVu symbol subset
  assets/env.bin       three.js RoomEnvironment radiance at roughness 0…1 (RGB9E5), baked by tools/envgen
  tools/glb2pfm.py     .glb -> .pfm converter with full round-trip verification
  tools/build_so.py    cross-compiles libpumpforge.so (clang/lld, NDK symbol allow-lists, ABI checks)
  tools/build_apk.py   stages assets, builds the libraries, packs, aligns, signs and verifies the APK
  tools/build_assets.py stages the assets (used by build_apk.py and by the Android Studio project)
  android-studio/      Gradle + CMake project building the same sources with the NDK
```

## Compact model format (.pfm)
`'PFM1' | u32 json_len | json header | binary`. Per primitive the positions are quantised to 16-bit in the
primitive's bounding box and normals to 8-bit (max error 0.07 mm on the largest parts, 0.38° on normals —
no visible change). Vertices are stored in first-use order, as zig-zag deltas split into byte planes, and the
indices with high-watermark coding; the APK's deflate then packs the models 3× smaller than the `.glb` files.
Morph targets, all node extras (`part_id`, `section_role`, `group`, `explode_offset`, `flow_kind`, `overlay`)
and the `Operate`/`Explode` clips are kept. `glb2pfm.py` decodes every file again and compares it with the source.

## Build (command line, no Android SDK needed)
```
pip install numpy fonttools brotli          # once
python3 native/tools/build_apk.py --version-name 2.1.0 --version-code 13
```
Output: `native/build/PumpForge-2.1.0-native.apk`, signed with `android/keystore/pumpforge-debug.jks`
(same key as the WebView builds, so it installs as an update). The toolchain is clang + lld with the C library
headers from musl (only ABI-identical parts are used: no errno, no pthread, no time_t) and link-time stub
libraries carrying the exact bionic/NDK symbol names; every imported symbol must be on an allow-list.
Android Studio users: see `native/android-studio/README.md`.

## Tests (desktop harness)
`native/tools/build_host.sh` builds `pf_test` (`native/tools/run_tests.py` runs the smoke test and the full sweep), which runs the same app on Mesa (llvmpipe) without a window.
Scripts drive it: `tap X Y`, `drag …`, `pinch …`, `text …`, `back`, `load ID`, `screen N`, `more N`, `theme N`, `full`,
`settab N`, `select PART`, `shot FILE`, `sweep`, `calcdump`. `tests/smoke.txt` walks every screen of the v2.1 layout.
* `sweep 0 282` loads **every module**, opens every tab scrolled to the end, toggles every overlay, runs the
  step player, the inspector, a tour, cutaway + X-ray + Operate + explode: 282/282 pass, no GL errors, no asserts.
* `calcdump` prints all 50 calculators for two input sets; the text is **byte-identical** to the web's JavaScript.
* `calckeys` prints the calculator order for every module; identical to the web's `FAMILY_CALCS` + `firstBy`.

## User interface (v2.1)
Navy/electric-blue design with amber accents and a bottom navigation bar (Home · Catalog · 3D Viewer · Bookmarks · More).
* **Home** — live rotating 3-D hero, Start Exploring, stats, Continue learning, Browse by Category (live thumbnails),
  Featured Equipment carousel (snaps, auto-advances), Quick Access.
* **Catalog** — search (name, EQ number, component), chips (All / Saved / departments), department grid with live
  3-D thumbnails, then module cards.
* **3D Viewer** — header card (prev/next), segments 3D View / Exploded (animated, slider) / Cutaway / X-ray, side
  buttons (operate, auto-rotate, zoom, reset), full screen, 360° hint, chips (How it works, Live flow, overlays, Labels,
  Measure, Show all parts), the How-it-works player on the model, numbered part markers matching the Parts tab, and the
  lesson tabs Overview · Parts · Working · Specs · Care · Failures · Tours · Quiz · Tools.
* **Bookmarks** — All / Recently Viewed / Progress (opened and passed counts).
* **More** — Learning Paths, Compare Models, Engineering Calculators, Training & Tutorials, Settings, Help, About.
* Thumbnails are rendered by the app's own renderer (no images in the APK): one model per frame, only for cards on
  screen, at most 72 kept in GPU memory.

## Behaviour notes
* Touch: one finger orbits, two fingers pinch-zoom and pan, a tap selects a part (or measures), long lists
  scroll with momentum, the Back key closes the picker, full screen, the step player, a tour, the inspector, measuring, a More page,
  catalog filters, then goes back through visited screens to Home and exits.
* Text entry (search, notes, datasheet, calculator inputs) opens the system keyboard in a small dialog; the
  app updates live while you type.
* Bookmarks, progress, quiz best scores, notes and datasheets are stored in the app's private storage
  (`pumpforge.v1.json`, same structure as the web's localStorage). Data from the WebView app is not migrated.
* Theme: Dark (default), Light or System (More → Settings). Phones use one scrolling viewer page with sticky lesson
  tabs; tablets/landscape (≥ 860 dp) put the 3-D stage on the left and the lessons on the right.
* Model emissive colours (flame, hot glow, UV lamp …) are shown as designed; the web viewer cleared them on load.
* "Show all" really restores hidden parts (the web viewer kept them hidden until a reload).
