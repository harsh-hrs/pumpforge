// Android entry point: android.app.NativeActivity glue (no Java code), EGL, choreographer frame loop,
// input queue on the main looper, TextToSpeech / keyboard dialog / clipboard through JNI.
#include "app.h"
#include "glapi.h"
#include <jni.h>
#include <stdio.h>

#ifdef PF_NDK_BUILD
// Android Studio / NDK build: the real NDK headers
#include <android/native_activity.h>
#include <android/looper.h>
#include <android/input.h>
#include <android/choreographer.h>
#include <android/asset_manager.h>
#include <android/configuration.h>
#include <android/native_window.h>
#include <android/log.h>
#include <time.h>
typedef struct timespec pf_timespec;
#else
// ------------------------------------------------------------------ NDK declarations (stable C API, API level 24)
extern "C" {
typedef struct ANativeWindow ANativeWindow; typedef struct AInputQueue AInputQueue; typedef struct AInputEvent AInputEvent;
typedef struct ALooper ALooper; typedef struct AAssetManager AAssetManager; typedef struct AAsset AAsset; typedef struct AConfiguration AConfiguration;
typedef struct AChoreographer AChoreographer;
typedef struct ARect { int32_t left, top, right, bottom; } ARect;
struct ANativeActivity;
typedef struct ANativeActivityCallbacks {
    void (*onStart)(ANativeActivity*); void (*onResume)(ANativeActivity*); void* (*onSaveInstanceState)(ANativeActivity*, size_t*);
    void (*onPause)(ANativeActivity*); void (*onStop)(ANativeActivity*); void (*onDestroy)(ANativeActivity*);
    void (*onWindowFocusChanged)(ANativeActivity*, int); void (*onNativeWindowCreated)(ANativeActivity*, ANativeWindow*);
    void (*onNativeWindowResized)(ANativeActivity*, ANativeWindow*); void (*onNativeWindowRedrawNeeded)(ANativeActivity*, ANativeWindow*);
    void (*onNativeWindowDestroyed)(ANativeActivity*, ANativeWindow*); void (*onInputQueueCreated)(ANativeActivity*, AInputQueue*);
    void (*onInputQueueDestroyed)(ANativeActivity*, AInputQueue*); void (*onContentRectChanged)(ANativeActivity*, const ARect*);
    void (*onConfigurationChanged)(ANativeActivity*); void (*onLowMemory)(ANativeActivity*);
} ANativeActivityCallbacks;
typedef struct ANativeActivity {
    ANativeActivityCallbacks* callbacks; JavaVM* vm; JNIEnv* env; jobject clazz; const char* internalDataPath; const char* externalDataPath;
    int32_t sdkVersion; void* instance; AAssetManager* assetManager; const char* obbPath;
} ANativeActivity;
typedef int (*ALooper_callbackFunc)(int fd, int events, void* data);
typedef void (*AChoreographer_frameCallback)(long frameTimeNanos, void* data);
int32_t ANativeWindow_getWidth(ANativeWindow*); int32_t ANativeWindow_getHeight(ANativeWindow*);
ALooper* ALooper_forThread(void);
void AInputQueue_attachLooper(AInputQueue*, ALooper*, int, ALooper_callbackFunc, void*); void AInputQueue_detachLooper(AInputQueue*);
int32_t AInputQueue_getEvent(AInputQueue*, AInputEvent**); int32_t AInputQueue_preDispatchEvent(AInputQueue*, AInputEvent*);
void AInputQueue_finishEvent(AInputQueue*, AInputEvent*, int);
int32_t AInputEvent_getType(const AInputEvent*);
int32_t AMotionEvent_getAction(const AInputEvent*); size_t AMotionEvent_getPointerCount(const AInputEvent*);
int32_t AMotionEvent_getPointerId(const AInputEvent*, size_t); float AMotionEvent_getX(const AInputEvent*, size_t); float AMotionEvent_getY(const AInputEvent*, size_t);
int32_t AKeyEvent_getAction(const AInputEvent*); int32_t AKeyEvent_getKeyCode(const AInputEvent*);
AChoreographer* AChoreographer_getInstance(void); void AChoreographer_postFrameCallback(AChoreographer*, AChoreographer_frameCallback, void*);
AAsset* AAssetManager_open(AAssetManager*, const char*, int); long long AAsset_getLength64(AAsset*); int AAsset_read(AAsset*, void*, size_t); void AAsset_close(AAsset*);
AConfiguration* AConfiguration_new(void); void AConfiguration_delete(AConfiguration*); void AConfiguration_fromAssetManager(AConfiguration*, AAssetManager*);
int32_t AConfiguration_getDensity(AConfiguration*); int32_t AConfiguration_getUiModeNight(AConfiguration*);
void ANativeActivity_finish(ANativeActivity*);
int __android_log_vprint(int prio, const char* tag, const char* fmt, va_list ap);
// bionic: time_t and tv_nsec are 'long' on every ABI (musl's 32-bit headers would use a 64-bit time_t, so <time.h> is not used)
struct pf_timespec { long tv_sec; long tv_nsec; };
int clock_gettime(int clk, struct pf_timespec* ts);
int __android_log_write(int prio, const char* tag, const char* text);
__attribute__((visibility("default"))) void ANativeActivity_onCreate(ANativeActivity* activity, void* savedState, size_t savedStateSize);
}

#endif
void theme_set(bool dark);
void pf_log(const char* fmt, ...) { va_list ap; va_start(ap, fmt); __android_log_vprint(4, "PumpForge", fmt, ap); va_end(ap); }
void pf_fatal(const char* fmt, ...) { va_list ap; va_start(ap, fmt); __android_log_vprint(7, "PumpForge", fmt, ap); va_end(ap); abort(); }

// ------------------------------------------------------------------ state
static ANativeActivity* g_act = nullptr;
static App* g_appp = nullptr;
static ANativeWindow* g_win = nullptr;
static AInputQueue* g_queue = nullptr;
static EGLDisplay g_dpy = EGL_NO_DISPLAY; static EGLConfig g_cfg = nullptr; static EGLContext g_ctx = EGL_NO_CONTEXT; static EGLSurface g_surf = EGL_NO_SURFACE;
static bool g_resumed = false, g_frame_posted = false, g_gl_loaded = false, g_init_ok = false;
static Str g_fatal;
static jobject g_tts = nullptr, g_dialog = nullptr, g_edit = nullptr;
static Str g_last_text;

static JNIEnv* env() { return g_act->env; }
static bool jcheck() { JNIEnv* e = env(); if (e->ExceptionCheck()) { e->ExceptionDescribe(); e->ExceptionClear(); return false; } return true; }

// ------------------------------------------------------------------ platform services
namespace plat {
bool read_asset(const char* path, Vec<uint8_t>& out) {
    AAsset* a = AAssetManager_open(g_act->assetManager, path, 3 /*AASSET_MODE_BUFFER*/);
    if (!a) return false;
    long long n = AAsset_getLength64(a);
    out.resize((int)n);
    long long got = 0;
    while (got < n) { int r = AAsset_read(a, out.d + got, (size_t)(n - got)); if (r <= 0) break; got += r; }
    AAsset_close(a);
    return got == n;
}
bool read_user(const char* name, Vec<uint8_t>& out) {
    Str p = Str::f("%s/%s", g_act->internalDataPath, name);
    FILE* f = fopen(p, "rb"); if (!f) return false;
    fseek(f, 0, SEEK_END); long n = ftell(f); fseek(f, 0, SEEK_SET);
    out.resize((int)n); size_t r = n > 0 ? fread(out.d, 1, (size_t)n, f) : 0; fclose(f);
    return (long)r == n;
}
bool write_user(const char* name, const void* d, size_t n) {
    Str p = Str::f("%s/%s", g_act->internalDataPath, name), t = Str::f("%s.tmp", p.c());
    FILE* f = fopen(t, "wb"); if (!f) return false;
    bool ok = fwrite(d, 1, n, f) == n; ok = (fclose(f) == 0) && ok;
    return ok && rename(t, p) == 0;
}
double now() { pf_timespec ts; clock_gettime(1 /*CLOCK_MONOTONIC*/, &ts); return ts.tv_sec + ts.tv_nsec * 1e-9; }
double now_epoch_ms() { pf_timespec ts; clock_gettime(0 /*CLOCK_REALTIME*/, &ts); return floor(ts.tv_sec * 1000.0 + ts.tv_nsec / 1e6); }

static void tts_create() {
    JNIEnv* e = env();
    jclass c = e->FindClass("android/speech/tts/TextToSpeech"); if (!jcheck() || !c) return;
    jmethodID ctor = e->GetMethodID(c, "<init>", "(Landroid/content/Context;Landroid/speech/tts/TextToSpeech$OnInitListener;)V");
    if (!jcheck() || !ctor) return;
    jobject t = e->NewObject(c, ctor, g_act->clazz, (jobject) nullptr);
    if (!jcheck() || !t) return;
    g_tts = e->NewGlobalRef(t); e->DeleteLocalRef(t); e->DeleteLocalRef(c);
}
bool tts_available() { return g_tts != nullptr; }
void speak(const char* text) {
    if (!g_tts) return;
    JNIEnv* e = env();
    jclass c = e->GetObjectClass(g_tts);
    jmethodID m = e->GetMethodID(c, "speak", "(Ljava/lang/CharSequence;ILandroid/os/Bundle;Ljava/lang/String;)I");
    jstring s = e->NewStringUTF(text), id = e->NewStringUTF("pf");
    if (m) e->CallIntMethod(g_tts, m, s, 0 /*QUEUE_FLUSH*/, (jobject) nullptr, id);
    jcheck(); e->DeleteLocalRef(s); e->DeleteLocalRef(id); e->DeleteLocalRef(c);
}
void stop_speaking() {
    if (!g_tts) return;
    JNIEnv* e = env(); jclass c = e->GetObjectClass(g_tts);
    jmethodID m = e->GetMethodID(c, "stop", "()I"); if (m) e->CallIntMethod(g_tts, m);
    jcheck(); e->DeleteLocalRef(c);
}
bool speaking() {
    if (!g_tts) return false;
    JNIEnv* e = env(); jclass c = e->GetObjectClass(g_tts);
    jmethodID m = e->GetMethodID(c, "isSpeaking", "()Z"); jboolean r = m ? e->CallBooleanMethod(g_tts, m) : JNI_FALSE;
    jcheck(); e->DeleteLocalRef(c);
    return r == JNI_TRUE;
}

// keyboard entry: AlertDialog + EditText built through JNI; the app polls the text every frame
void text_begin(const char* title, const char* initial, InputKind kind) {
    JNIEnv* e = env();
    if (g_dialog) { e->DeleteGlobalRef(g_dialog); g_dialog = nullptr; }
    if (g_edit) { e->DeleteGlobalRef(g_edit); g_edit = nullptr; }
    jclass cE = e->FindClass("android/widget/EditText");
    jobject et = e->NewObject(cE, e->GetMethodID(cE, "<init>", "(Landroid/content/Context;)V"), g_act->clazz); if (!jcheck()) return;
    jstring ini = e->NewStringUTF(initial ? initial : "");
    e->CallVoidMethod(et, e->GetMethodID(cE, "setText", "(Ljava/lang/CharSequence;)V"), ini);
    int type = kind == NUMBER ? (2 | 0x1000 | 0x2000) : (kind == MULTILINE ? (1 | 0x20000 | 0x4000) : (1 | 0x4000 * 0));
    e->CallVoidMethod(et, e->GetMethodID(cE, "setInputType", "(I)V"), type);
    if (kind == MULTILINE) {
        e->CallVoidMethod(et, e->GetMethodID(cE, "setMinLines", "(I)V"), 4);
        e->CallVoidMethod(et, e->GetMethodID(cE, "setMaxLines", "(I)V"), 10);
        e->CallVoidMethod(et, e->GetMethodID(cE, "setGravity", "(I)V"), 0x800033);
    } else e->CallVoidMethod(et, e->GetMethodID(cE, "setSingleLine", "(Z)V"), JNI_TRUE);
    jint len = e->CallIntMethod(et, e->GetMethodID(cE, "length", "()I"));
    e->CallVoidMethod(et, e->GetMethodID(cE, "setSelection", "(I)V"), len);
    jcheck();
    jclass cF = e->FindClass("android/widget/FrameLayout");
    jobject fl = e->NewObject(cF, e->GetMethodID(cF, "<init>", "(Landroid/content/Context;)V"), g_act->clazz);
    int pad = (int)(20 * (g_appp ? g_appp->dp : 2));
    e->CallVoidMethod(fl, e->GetMethodID(cF, "setPadding", "(IIII)V"), pad, pad / 2, pad, 0);
    e->CallVoidMethod(fl, e->GetMethodID(cF, "addView", "(Landroid/view/View;)V"), et);
    jcheck();
    jclass cB = e->FindClass("android/app/AlertDialog$Builder");
    jobject b = e->NewObject(cB, e->GetMethodID(cB, "<init>", "(Landroid/content/Context;)V"), g_act->clazz);
    jstring tt = e->NewStringUTF(title ? title : "");
    e->CallObjectMethod(b, e->GetMethodID(cB, "setTitle", "(Ljava/lang/CharSequence;)Landroid/app/AlertDialog$Builder;"), tt);
    e->CallObjectMethod(b, e->GetMethodID(cB, "setView", "(Landroid/view/View;)Landroid/app/AlertDialog$Builder;"), fl);
    jstring done = e->NewStringUTF("Done");
    e->CallObjectMethod(b, e->GetMethodID(cB, "setPositiveButton", "(Ljava/lang/CharSequence;Landroid/content/DialogInterface$OnClickListener;)Landroid/app/AlertDialog$Builder;"), done, (jobject) nullptr);
    jobject dlg = e->CallObjectMethod(b, e->GetMethodID(cB, "create", "()Landroid/app/AlertDialog;"));
    if (!jcheck() || !dlg) return;
    jclass cD = e->FindClass("android/app/Dialog");
    jobject win = e->CallObjectMethod(dlg, e->GetMethodID(cD, "getWindow", "()Landroid/view/Window;"));
    if (win) { jclass cW = e->FindClass("android/view/Window"); e->CallVoidMethod(win, e->GetMethodID(cW, "setSoftInputMode", "(I)V"), 5 /*STATE_ALWAYS_VISIBLE*/); }
    e->CallVoidMethod(dlg, e->GetMethodID(cD, "show", "()V"));
    jclass cV = e->FindClass("android/view/View");
    e->CallBooleanMethod(et, e->GetMethodID(cV, "requestFocus", "()Z"));
    if (!jcheck()) return;
    g_dialog = e->NewGlobalRef(dlg); g_edit = e->NewGlobalRef(et);
    g_last_text = initial ? initial : "";
}
bool text_poll(Str& cur, bool& closed, bool& accepted) {
    closed = accepted = false;
    if (!g_dialog) { closed = true; return false; }
    JNIEnv* e = env();
    jclass cD = e->FindClass("android/app/Dialog");
    jboolean showing = e->CallBooleanMethod(g_dialog, e->GetMethodID(cD, "isShowing", "()Z"));
    jclass cT = e->FindClass("android/widget/TextView");
    jobject ed = e->CallObjectMethod(g_edit, e->GetMethodID(cT, "getText", "()Landroid/text/Editable;"));
    jclass cO = e->FindClass("java/lang/Object");
    jstring js = ed ? (jstring)e->CallObjectMethod(ed, e->GetMethodID(cO, "toString", "()Ljava/lang/String;")) : nullptr;
    bool changed = false;
    if (js) { const char* u = e->GetStringUTFChars(js, nullptr); if (u) { if (!g_last_text.eq(u)) { g_last_text = u; changed = true; } e->ReleaseStringUTFChars(js, u); } }
    jcheck();
    e->DeleteLocalRef(cD); e->DeleteLocalRef(cT); e->DeleteLocalRef(cO); if (ed) e->DeleteLocalRef(ed); if (js) e->DeleteLocalRef(js);
    cur = g_last_text;
    if (!showing) { closed = true; accepted = true; e->DeleteGlobalRef(g_dialog); e->DeleteGlobalRef(g_edit); g_dialog = g_edit = nullptr; return true; }
    return changed;
}
void copy_to_clipboard(const char* text) {
    JNIEnv* e = env();
    jclass cC = e->FindClass("android/content/Context");
    jstring svc = e->NewStringUTF("clipboard");
    jobject cm = e->CallObjectMethod(g_act->clazz, e->GetMethodID(cC, "getSystemService", "(Ljava/lang/String;)Ljava/lang/Object;"), svc);
    jclass cD = e->FindClass("android/content/ClipData");
    jstring lbl = e->NewStringUTF("PumpForge"), txt = e->NewStringUTF(text);
    jobject cd = e->CallStaticObjectMethod(cD, e->GetStaticMethodID(cD, "newPlainText", "(Ljava/lang/CharSequence;Ljava/lang/CharSequence;)Landroid/content/ClipData;"), lbl, txt);
    jclass cM = e->FindClass("android/content/ClipboardManager");
    if (cm && cd) e->CallVoidMethod(cm, e->GetMethodID(cM, "setPrimaryClip", "(Landroid/content/ClipData;)V"), cd);
    jcheck();
}
void quit() { ANativeActivity_finish(g_act); }
}

static void apply_bars();
// status / navigation bar colours to match the app background and the bottom navigation
static void system_bars(uint32_t top, uint32_t bottom, bool light) {
    JNIEnv* e = env();
    jclass cA = e->FindClass("android/app/Activity");
    jobject win = e->CallObjectMethod(g_act->clazz, e->GetMethodID(cA, "getWindow", "()Landroid/view/Window;"));
    if (!jcheck() || !win) return;
    jclass cW = e->FindClass("android/view/Window");
    e->CallVoidMethod(win, e->GetMethodID(cW, "addFlags", "(I)V"), (jint)0x80000000);
    e->CallVoidMethod(win, e->GetMethodID(cW, "setStatusBarColor", "(I)V"), (jint)(0xff000000u | top));
    e->CallVoidMethod(win, e->GetMethodID(cW, "setNavigationBarColor", "(I)V"), (jint)(0xff000000u | bottom));
    // dark status/navigation icons on the light theme (API 23 / 26 flags)
    jobject dv = e->CallObjectMethod(win, e->GetMethodID(cW, "getDecorView", "()Landroid/view/View;"));
    if (dv) {
        jclass cV = e->FindClass("android/view/View");
        int flags = light ? (0x2000 | (g_act->sdkVersion >= 26 ? 0x10 : 0)) : 0;
        e->CallVoidMethod(dv, e->GetMethodID(cV, "setSystemUiVisibility", "(I)V"), flags);
    }
    jcheck();
}
void plat::theme_changed(bool) { apply_bars(); }
static void apply_bars() { if (!g_appp) return; bool d = g_appp->is_dark(); system_bars(d ? 0x060d1d : 0xeef2f9, d ? 0x0a1530 : 0xffffff, !d); }

// ------------------------------------------------------------------ EGL
static bool egl_init() {
    if (!g_gl_loaded) {
        char err[200];
        if (!gl_load("libEGL.so", "libGLESv3.so", err, sizeof err)) { g_fatal = err; pf_log("GL load: %s", err); return false; }
        g_gl_loaded = true;
    }
    if (g_dpy == EGL_NO_DISPLAY) {
        g_dpy = eglGetDisplay(EGL_DEFAULT_DISPLAY);
        if (!eglInitialize(g_dpy, nullptr, nullptr)) { pf_log("eglInitialize failed"); return false; }
        EGLint want[][20] = {
            {EGL_RENDERABLE_TYPE, EGL_OPENGL_ES3_BIT, EGL_SURFACE_TYPE, EGL_WINDOW_BIT, EGL_RED_SIZE, 8, EGL_GREEN_SIZE, 8, EGL_BLUE_SIZE, 8, EGL_DEPTH_SIZE, 24, EGL_SAMPLE_BUFFERS, 1, EGL_SAMPLES, 4, EGL_NONE},
            {EGL_RENDERABLE_TYPE, EGL_OPENGL_ES3_BIT, EGL_SURFACE_TYPE, EGL_WINDOW_BIT, EGL_RED_SIZE, 8, EGL_GREEN_SIZE, 8, EGL_BLUE_SIZE, 8, EGL_DEPTH_SIZE, 24, EGL_NONE},
            {EGL_RENDERABLE_TYPE, EGL_OPENGL_ES3_BIT, EGL_SURFACE_TYPE, EGL_WINDOW_BIT, EGL_RED_SIZE, 8, EGL_GREEN_SIZE, 8, EGL_BLUE_SIZE, 8, EGL_DEPTH_SIZE, 16, EGL_NONE}};
        EGLint n = 0;
        for (auto& w : want) if (eglChooseConfig(g_dpy, w, &g_cfg, 1, &n) && n > 0) break;
        if (n < 1) { g_fatal = "This device does not support OpenGL ES 3."; return false; }
    }
    if (g_ctx == EGL_NO_CONTEXT) {
        EGLint ca[] = {EGL_CONTEXT_CLIENT_VERSION, 3, EGL_NONE};
        g_ctx = eglCreateContext(g_dpy, g_cfg, EGL_NO_CONTEXT, ca);
        if (g_ctx == EGL_NO_CONTEXT) { g_fatal = "OpenGL ES 3 context could not be created."; return false; }
    }
    return true;
}
static void surface_create() {
    if (!g_win || !egl_init()) return;
    if (g_surf == EGL_NO_SURFACE) g_surf = eglCreateWindowSurface(g_dpy, g_cfg, (EGLNativeWindowType)g_win, nullptr);
    if (g_surf == EGL_NO_SURFACE || !eglMakeCurrent(g_dpy, g_surf, g_surf, g_ctx)) { pf_log("eglMakeCurrent failed 0x%x", eglGetError()); return; }
    if (g_appp && g_init_ok && !g_appp->gl_ready) {
        char err[200];
        if (!g_appp->gl_init(err, sizeof err)) { pf_log("gl_init: %s", err); g_fatal = err; }
    }
}
static void surface_destroy() {
    if (g_surf != EGL_NO_SURFACE) { eglMakeCurrent(g_dpy, EGL_NO_SURFACE, EGL_NO_SURFACE, EGL_NO_CONTEXT); eglDestroySurface(g_dpy, g_surf); g_surf = EGL_NO_SURFACE; }
}

// ------------------------------------------------------------------ frame loop (Choreographer, main thread)
static void post_frame();
static void on_frame(long, void*) {
    g_frame_posted = false;
    if (!g_win || !g_resumed || !g_appp || g_surf == EGL_NO_SURFACE) return;
    eglMakeCurrent(g_dpy, g_surf, g_surf, g_ctx);
    int w = ANativeWindow_getWidth(g_win), h = ANativeWindow_getHeight(g_win);
    g_appp->resize(w, h);
    if (g_appp->gl_ready) {
        g_appp->frame(plat::now());
        if (!eglSwapBuffers(g_dpy, g_surf)) {
            EGLint er = eglGetError();
            if (er == 0x300E /*EGL_CONTEXT_LOST*/) {
                pf_log("EGL context lost: recreating");
                g_appp->gl_lost(); surface_destroy(); eglDestroyContext(g_dpy, g_ctx); g_ctx = EGL_NO_CONTEXT; surface_create();
            }
        }
    }
    post_frame();
}
static void post_frame() { if (!g_frame_posted) { g_frame_posted = true; AChoreographer_postFrameCallback(AChoreographer_getInstance(), on_frame, nullptr); } }

// ------------------------------------------------------------------ input
static int on_input(int, int, void*) {
    AInputEvent* ev = nullptr;
    while (g_queue && AInputQueue_getEvent(g_queue, &ev) >= 0) {
        if (AInputQueue_preDispatchEvent(g_queue, ev)) continue;
        int handled = 0;
        int32_t type = AInputEvent_getType(ev);
        if (type == 2 /*MOTION*/ && g_appp) {
            int32_t act = AMotionEvent_getAction(ev), a = act & 0xff, idx = (act & 0xff00) >> 8;
            size_t n = AMotionEvent_getPointerCount(ev);
            if (a == 0 || a == 5) { g_appp->touch({TouchEvent::Down, AMotionEvent_getPointerId(ev, (size_t)idx), AMotionEvent_getX(ev, (size_t)idx), AMotionEvent_getY(ev, (size_t)idx)}); }
            else if (a == 1 || a == 6) { g_appp->touch({TouchEvent::Up, AMotionEvent_getPointerId(ev, (size_t)idx), AMotionEvent_getX(ev, (size_t)idx), AMotionEvent_getY(ev, (size_t)idx)}); }
            else if (a == 2) { for (size_t i = 0; i < n; i++) g_appp->touch({TouchEvent::Move, AMotionEvent_getPointerId(ev, i), AMotionEvent_getX(ev, i), AMotionEvent_getY(ev, i)}); }
            else if (a == 3) { for (size_t i = 0; i < n; i++) g_appp->touch({TouchEvent::Cancel, AMotionEvent_getPointerId(ev, i), AMotionEvent_getX(ev, i), AMotionEvent_getY(ev, i)}); }
            handled = 1;
        } else if (type == 1 /*KEY*/ && AKeyEvent_getKeyCode(ev) == 4 /*BACK*/) {
            if (AKeyEvent_getAction(ev) == 1 /*UP*/ && g_appp && !g_appp->back()) ANativeActivity_finish(g_act);
            handled = 1;
        }
        AInputQueue_finishEvent(g_queue, ev, handled);
    }
    return 1;
}

// ------------------------------------------------------------------ activity callbacks
static void onResume(ANativeActivity*) { g_resumed = true; post_frame(); }
static void onPause(ANativeActivity*) { g_resumed = false; if (g_appp && g_appp->store.dirty) g_appp->store.save(); if (g_appp) plat::stop_speaking(); }
static void onStop(ANativeActivity*) { if (g_appp && g_appp->store.dirty) g_appp->store.save(); }
static void onDestroy(ANativeActivity*) {
    if (g_appp) {
        if (g_surf == EGL_NO_SURFACE && g_win) surface_create();
        if (g_surf == EGL_NO_SURFACE && g_appp->gl_ready) g_appp->gl_lost();   // no current context: let eglDestroyContext free GL objects
        g_appp->shutdown(); delete g_appp; g_appp = nullptr;
    }
    JNIEnv* e = env();
    if (g_tts) { jclass c = e->GetObjectClass(g_tts); jmethodID m = e->GetMethodID(c, "shutdown", "()V"); if (m) e->CallVoidMethod(g_tts, m); jcheck(); e->DeleteGlobalRef(g_tts); g_tts = nullptr; }
    if (g_dialog) { e->DeleteGlobalRef(g_dialog); g_dialog = nullptr; } if (g_edit) { e->DeleteGlobalRef(g_edit); g_edit = nullptr; }
    surface_destroy();
    if (g_ctx != EGL_NO_CONTEXT) { eglDestroyContext(g_dpy, g_ctx); g_ctx = EGL_NO_CONTEXT; }
    if (g_dpy != EGL_NO_DISPLAY) { eglTerminate(g_dpy); g_dpy = EGL_NO_DISPLAY; }
    g_act = nullptr;
}
static void onWindowCreated(ANativeActivity*, ANativeWindow* w) { g_win = w; surface_create(); post_frame(); }
static void onWindowResized(ANativeActivity*, ANativeWindow*) { post_frame(); }
static void onWindowRedraw(ANativeActivity*, ANativeWindow*) { if (g_resumed) on_frame(0, nullptr); }
static void onWindowDestroyed(ANativeActivity*, ANativeWindow*) { surface_destroy(); g_win = nullptr; }
static void onInputCreated(ANativeActivity*, AInputQueue* q) { g_queue = q; AInputQueue_attachLooper(q, ALooper_forThread(), 1, on_input, nullptr); }
static void onInputDestroyed(ANativeActivity*, AInputQueue* q) { AInputQueue_detachLooper(q); if (g_queue == q) g_queue = nullptr; }
static void onContentRect(ANativeActivity*, const ARect* r) {
    if (!g_appp || !g_win) return;
    int h = ANativeWindow_getHeight(g_win), w = ANativeWindow_getWidth(g_win);
    g_appp->inset_top = (float)r->top; g_appp->inset_bottom = (float)pf_max(0, h - r->bottom);
    g_appp->inset_left = (float)r->left; g_appp->inset_right = (float)pf_max(0, w - r->right);
    post_frame();
}
static void onConfigChanged(ANativeActivity* a) {
    if (!g_appp) return;
    AConfiguration* c = AConfiguration_new(); AConfiguration_fromAssetManager(c, a->assetManager);
    bool dark = AConfiguration_getUiModeNight(c) == 2; AConfiguration_delete(c);
    if (dark != g_appp->sys_dark) { g_appp->sys_dark = dark; g_appp->apply_theme(); apply_bars(); }
    post_frame();
}
static void onLowMemory(ANativeActivity*) { pf_log("low memory"); }

extern "C" __attribute__((visibility("default"))) void ANativeActivity_onCreate(ANativeActivity* a, void*, size_t) {
    g_act = a;
    ANativeActivityCallbacks* cb = a->callbacks;
    cb->onResume = onResume; cb->onPause = onPause; cb->onStop = onStop; cb->onDestroy = onDestroy;
    cb->onNativeWindowCreated = onWindowCreated; cb->onNativeWindowResized = onWindowResized; cb->onNativeWindowRedrawNeeded = onWindowRedraw;
    cb->onNativeWindowDestroyed = onWindowDestroyed; cb->onInputQueueCreated = onInputCreated; cb->onInputQueueDestroyed = onInputDestroyed;
    cb->onContentRectChanged = onContentRect; cb->onConfigurationChanged = onConfigChanged; cb->onLowMemory = onLowMemory;
    AConfiguration* c = AConfiguration_new(); AConfiguration_fromAssetManager(c, a->assetManager);
    int dpi = AConfiguration_getDensity(c); bool dark = AConfiguration_getUiModeNight(c) == 2;
    AConfiguration_delete(c);
    if (dpi <= 0 || dpi > 2000) dpi = 160;
    g_appp = new App();
    char err[256] = {0};
    g_init_ok = g_appp->init(dpi / 160.f, dark, err, sizeof err);
    if (!g_init_ok) pf_log("init failed: %s", err);
    apply_bars();
    plat::tts_create();
}
