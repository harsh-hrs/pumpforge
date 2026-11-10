# PumpForge native — Android Studio project

This project builds **the same native app** as `native/tools/build_apk.py` (C++17 + OpenGL ES 3.0,
`android.app.NativeActivity`, no WebView, no Java/Kotlin code) with Android Studio, Gradle and the NDK.
The C++ sources are shared: `native/src/*.cpp` and Dear ImGui in `native/third_party/imgui`.

## Requirements
* Android Studio (Koala or newer) with **SDK 34**, **NDK 27.1.12297006** and **CMake 3.22.1** (SDK Manager → SDK Tools).
* **Python 3 with numpy** (`pip install numpy`) — the first build converts `output/glb/*.glb` into the compact
  `.pfm` models and stages the app assets in `native/build/apk_assets` (`native/tools/build_assets.py`).

## Build
1. *File → Open…* and choose the folder `native/android-studio`. Let Android Studio download Gradle 8.7 and the
   Android Gradle Plugin 8.5.2 (the Gradle wrapper jar is created by Android Studio on first sync).
2. *Build → Build App Bundle(s) / APK(s) → Build APK(s)*, or press Run with a phone connected.

Both builds are signed with `android/keystore/pumpforge-debug.jks` (the same key as the command-line APKs),
so they install as updates of `com.redeyelabs.pumpforge`.

## Command-line build (no Android SDK needed)
`python3 native/tools/build_apk.py --version-name 2.0.0 --version-code 12` — see `native/README.md`.
