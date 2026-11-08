# PumpForge Android app

An offline Android app containing the whole 282-module Industrial Engineering Equipment Library (v1.8: arranged & numbered by department; v1.7: mechanical components, safety & environmental; v1.6: water & utilities; v1.5: departments, alumina refinery; X-ray, live flow particles, How-it-works step player, search / bookmarks / progress, engineering tools).
- A full-screen WebView loads the learning-library player and every model from the APK's own assets, served at `https://appassets.androidplatform.net/www/…`. No internet connection is needed.
- Tour narration uses Android TextToSpeech through `window.AndroidTTS`.
- Package: `com.redeyelabs.pumpforge`. minSdk 24 (Android 7.0), targetSdk 34. Signed with APK Signature Scheme v2 and v3.

## Build
```bash
python3 android/build_apk.py --version-name 1.8.0 --version-code 9
# -> android/build/PumpForge-1.8.0.apk
```
- Requires Java 17+, Python 3 and npm. The Android SDK and Gradle are not needed.
- `apktool` 2.9.3 assembles `app/smali` into `classes.dex` and links the manifest and resources with its bundled aapt2 and framework. Google's `apksigner` signs the APK.
- Both tools are fetched once from the npm registry (`@postar/apktool-node`) into `android/build/tools/`.

| Path | Purpose |
|---|---|
| `app/AndroidManifest.xml`, `app/apktool.yml` | Manifest, SDK levels, version |
| `app/smali/com/redeyelabs/pumpforge/*.smali` | `MainActivity` (WebView + TTS), `AssetClient` (serves assets), `TtsBridge` (JS → TextToSpeech) |
| `app/res/` | App name and launcher icons (`make_icon.py`) |
| `make_www.py` | Builds the offline web bundle (player, three.js, GLB, meta and learning JSON) |
| `keystore/pumpforge-debug.jks` | **Debug** signing key (password `pumpforge-debug`, alias `pumpforge`) |

## Signing / Play Store
- The bundled keystore is a debug key, suitable only for sideloading and testing.
- Before publishing, create your own private release key and keep it out of version control. Sign with it, either by changing `KS` in `build_apk.py` or with `apksigner` directly.
- Bump `--version-code` for every release.
- For Google Play, upload an Android App Bundle (AAB) built with Android Studio/Gradle. The same `www/` bundle can be dropped into a standard Android Studio project's `src/main/assets/`, using `androidx.webkit.WebViewAssetLoader`.

## Install (sideload)
Copy the APK to the phone. Open it and allow "Install unknown apps" for your file manager or browser when Android asks.
