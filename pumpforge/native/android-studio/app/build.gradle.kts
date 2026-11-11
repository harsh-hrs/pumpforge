// PumpForge native - Android Studio build of the same C++ sources as native/tools/build_apk.py
// (NativeActivity + libpumpforge.so, no Java/Kotlin code, ANDROID_STL=none because the code uses no STL).
plugins { id("com.android.application") }

val nativeRoot = rootProject.projectDir.parentFile           // <repo>/native
val stagedAssets = File(nativeRoot, "build/apk_assets")       // made by native/tools/build_assets.py

android {
    namespace = "com.redeyelabs.pumpforge"
    compileSdk = 34
    ndkVersion = "27.1.12297006"
    defaultConfig {
        applicationId = "com.redeyelabs.pumpforge"
        minSdk = 24
        targetSdk = 34
        versionCode = 14
        versionName = "2.2.0"
        ndk { abiFilters += listOf("arm64-v8a", "armeabi-v7a", "x86_64") }
        externalNativeBuild { cmake { arguments += listOf("-DANDROID_STL=none") } }
    }
    externalNativeBuild { cmake { path = file("src/main/cpp/CMakeLists.txt"); version = "3.22.1" } }
    sourceSets["main"].assets.srcDir(stagedAssets)
    // same key as the command-line builds (android/keystore), so Android Studio builds install as updates of the APKs
    signingConfigs {
        create("pumpforge") {
            storeFile = File(nativeRoot.parentFile, "android/keystore/pumpforge-debug.jks")
            storePassword = "pumpforge-debug"; keyAlias = "pumpforge"; keyPassword = "pumpforge-debug"
        }
    }
    buildTypes {
        debug { signingConfig = signingConfigs.getByName("pumpforge") }
        release { isMinifyEnabled = false; signingConfig = signingConfigs.getByName("pumpforge") }
    }
    packaging { jniLibs { useLegacyPackaging = true } }
}

// Assets (compact models, fonts, lighting, lesson JSON) are generated from <repo>/output by Python 3 + numpy.
val stageAssets by tasks.registering(Exec::class) {
    group = "pumpforge"
    description = "Convert output/glb to .pfm and stage all app assets (python native/tools/build_assets.py)"
    workingDir = nativeRoot.parentFile
    val py = if (System.getProperty("os.name").lowercase().contains("windows")) "python" else "python3"
    commandLine(py, File(nativeRoot, "tools/build_assets.py").absolutePath)
    onlyIf { !File(stagedAssets, "models").isDirectory }
}
tasks.named("preBuild") { dependsOn(stageAssets) }
