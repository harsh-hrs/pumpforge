// Desktop test harness: the same app code on Mesa (headless EGL), driven by a script, writing screenshots.
// usage: pf_test <assets_dir> <script> [--size WxH] [--density D] [--dark]
// script lines: frames N | tap X Y | drag X1 Y1 X2 Y2 [steps] | pinch CX CY D1 D2 | shot FILE.ppm | text VALUE | cancel | back | log MSG | set KEY VAL
#include "app.h"
#include "glapi.h"
#include "calcs.h"
#include "imgui.h"
#include "imgui_internal.h"
#include <stdio.h>
#include <time.h>
#include <unistd.h>

static Str g_assets, g_userdir = "/tmp/pumpforge-user";
static Str g_text_pending; static bool g_text_open = false, g_text_ready = false, g_text_cancel = false;
static double g_fake_time = 0; static bool g_nomsaa = true;   // Mesa surfaceless: multisampled pbuffers cannot be read back

void pf_log(const char* fmt, ...) { va_list ap; va_start(ap, fmt); fprintf(stderr, "[pf] "); vfprintf(stderr, fmt, ap); fprintf(stderr, "\n"); va_end(ap); }
void pf_fatal(const char* fmt, ...) { va_list ap; va_start(ap, fmt); fprintf(stderr, "[pf FATAL] "); vfprintf(stderr, fmt, ap); fprintf(stderr, "\n"); va_end(ap); abort(); }

namespace plat {
static bool read_file(const char* p, Vec<uint8_t>& out) {
    FILE* f = fopen(p, "rb"); if (!f) return false;
    fseek(f, 0, SEEK_END); long n = ftell(f); fseek(f, 0, SEEK_SET);
    out.resize((int)n); size_t r = n ? fread(out.d, 1, (size_t)n, f) : 0; fclose(f);
    return r == (size_t)n;
}
bool read_asset(const char* path, Vec<uint8_t>& out) { return read_file(Str::f("%s/%s", g_assets.c(), path), out); }
bool read_user(const char* name, Vec<uint8_t>& out) { return read_file(Str::f("%s/%s", g_userdir.c(), name), out); }
bool write_user(const char* name, const void* d, size_t n) {
    Str p = Str::f("%s/%s", g_userdir.c(), name), t = Str::f("%s.tmp", p.c());
    FILE* f = fopen(t, "wb"); if (!f) return false;
    bool ok = fwrite(d, 1, n, f) == n; fclose(f);
    return ok && rename(t, p) == 0;
}
double now() { return g_fake_time; }
double now_epoch_ms() { struct timespec ts; clock_gettime(CLOCK_REALTIME, &ts); return floor(ts.tv_sec * 1000.0 + ts.tv_nsec / 1e6); }
void speak(const char* t) { pf_log("TTS: %s", t); }
void stop_speaking() {}
bool speaking() { return false; }
bool tts_available() { return true; }
void text_begin(const char* title, const char* initial, InputKind kind) { pf_log("text dialog '%s' (kind %d) initial='%s'", title, kind, initial); g_text_open = true; g_text_ready = false; }
bool text_poll(Str& cur, bool& closed, bool& accepted) {
    closed = accepted = false;
    if (!g_text_open) { closed = true; return false; }
    if (g_text_cancel) { g_text_open = false; g_text_cancel = false; closed = true; return false; }
    if (!g_text_ready) return false;
    cur = g_text_pending; g_text_ready = false; g_text_open = false; closed = true; accepted = true;
    return true;
}
void copy_to_clipboard(const char* t) { pf_log("CLIPBOARD: %s", t); }
void quit() { pf_log("quit"); }
void theme_changed(bool d) { pf_log("theme %s", d ? "dark" : "light"); }
}

static void write_ppm(const char* path, int w, int h, const uint8_t* rgba) {
    FILE* f = fopen(path, "wb"); if (!f) return;
    fprintf(f, "P6\n%d %d\n255\n", w, h);
    for (int y = h - 1; y >= 0; y--) for (int x = 0; x < w; x++) fwrite(rgba + ((size_t)y * w + x) * 4, 1, 3, f);
    fclose(f);
}

int main(int argc, char** argv) {
    if (argc < 3) { fprintf(stderr, "usage: %s assets script [--size WxH] [--density D] [--dark]\n", argv[0]); return 2; }
    g_assets = argv[1];
    int W = 1080, H = 2280; float density = 2.75f; bool dark = false;
    for (int i = 3; i < argc; i++) {
        if (!strcmp(argv[i], "--size") && i + 1 < argc) sscanf(argv[++i], "%dx%d", &W, &H);
        else if (!strcmp(argv[i], "--density") && i + 1 < argc) density = (float)atof(argv[++i]);
        else if (!strcmp(argv[i], "--dark")) dark = true;
        else if (!strcmp(argv[i], "--nomsaa")) g_nomsaa = true;
        else if (!strcmp(argv[i], "--user") && i + 1 < argc) g_userdir = argv[++i];
    }
    char err[256];
    if (!gl_load("libEGL.so.1", "libGLESv2.so.2", err, sizeof err)) { fprintf(stderr, "gl: %s\n", err); return 1; }
    typedef EGLDisplay (*PFNGETPLAT)(EGLenum, void*, const EGLint*);
    PFNGETPLAT getplat = (PFNGETPLAT)eglGetProcAddress("eglGetPlatformDisplayEXT");
    EGLDisplay dpy = getplat ? getplat(EGL_PLATFORM_SURFACELESS_MESA, EGL_DEFAULT_DISPLAY, nullptr) : eglGetDisplay(EGL_DEFAULT_DISPLAY);
    EGLint ma, mi; if (!eglInitialize(dpy, &ma, &mi)) { fprintf(stderr, "eglInitialize failed 0x%x\n", eglGetError()); return 1; }
    eglBindAPI(EGL_OPENGL_ES_API);
    EGLint attrs[] = {EGL_SURFACE_TYPE, EGL_PBUFFER_BIT, EGL_RENDERABLE_TYPE, EGL_OPENGL_ES3_BIT, EGL_RED_SIZE, 8, EGL_GREEN_SIZE, 8, EGL_BLUE_SIZE, 8, EGL_ALPHA_SIZE, 8, EGL_DEPTH_SIZE, 24, EGL_SAMPLE_BUFFERS, 1, EGL_SAMPLES, 4, EGL_NONE};
    EGLConfig cfg; EGLint n = 0;
    if (g_nomsaa) attrs[14] = EGL_NONE;
    if (!eglChooseConfig(dpy, attrs, &cfg, 1, &n) || n < 1) { attrs[14] = EGL_NONE; eglChooseConfig(dpy, attrs, &cfg, 1, &n); }
    { EGLint sb = 0, sm = 0; eglGetConfigAttrib(dpy, cfg, EGL_SAMPLE_BUFFERS, &sb); eglGetConfigAttrib(dpy, cfg, EGL_SAMPLES, &sm); fprintf(stderr, "EGL config: sample buffers %d samples %d\n", sb, sm); }
    if (n < 1) { fprintf(stderr, "no EGL config\n"); return 1; }
    EGLint pb[] = {EGL_WIDTH, W, EGL_HEIGHT, H, EGL_NONE};
    EGLSurface surf = eglCreatePbufferSurface(dpy, cfg, pb);
    EGLint ca[] = {EGL_CONTEXT_CLIENT_VERSION, 3, EGL_NONE};
    EGLContext ctx = eglCreateContext(dpy, cfg, EGL_NO_CONTEXT, ca);
    if (!surf || !ctx || !eglMakeCurrent(dpy, surf, surf, ctx)) { fprintf(stderr, "EGL context failed 0x%x\n", eglGetError()); return 1; }
    fprintf(stderr, "GL: %s | %s\n", glGetString(GL_RENDERER), glGetString(GL_VERSION));

    { Str c = Str::f("mkdir -p %s", g_userdir.c()); if (system(c)) {} }
    App app;
    app.inset_top = 24 * density; app.inset_bottom = 16 * density;
    if (!app.init(density, dark, err, sizeof err)) { fprintf(stderr, "init: %s\n", err); return 1; }
    if (!app.gl_init(err, sizeof err)) { fprintf(stderr, "gl_init: %s\n", err); return 1; }
    app.resize(W, H);
    FILE* sf = fopen(argv[2], "r"); if (!sf) { fprintf(stderr, "no script\n"); return 1; }
    char line[1024];
    auto step = [&](int frames) { for (int i = 0; i < frames; i++) { g_fake_time += 1.0 / 60; app.frame(g_fake_time); eglSwapBuffers(dpy, surf); } };
    step(4);
    float d = density;
    while (fgets(line, sizeof line, sf)) {
        char cmd[32] = {0}; if (sscanf(line, "%31s", cmd) != 1 || cmd[0] == '#') continue;
        float a, b, c, e; int k;
        if (!strcmp(cmd, "frames") && sscanf(line + 6, "%d", &k) == 1) step(k);
        else if (!strcmp(cmd, "tap") && sscanf(line + 3, "%f %f", &a, &b) == 2) {
            app.touch({TouchEvent::Down, 1, a * d, b * d}); step(2); app.touch({TouchEvent::Up, 1, a * d, b * d}); step(3);
        } else if (!strcmp(cmd, "drag") && sscanf(line + 4, "%f %f %f %f %d", &a, &b, &c, &e, &k) >= 4) {
            if (k <= 0) k = 12;
            app.touch({TouchEvent::Down, 1, a * d, b * d}); step(1);
            for (int i = 1; i <= k; i++) { float t = (float)i / k; app.touch({TouchEvent::Move, 1, (a + (c - a) * t) * d, (b + (e - b) * t) * d}); step(1); }
            app.touch({TouchEvent::Up, 1, c * d, e * d}); step(2);
        } else if (!strcmp(cmd, "pinch") && sscanf(line + 5, "%f %f %f %f", &a, &b, &c, &e) == 4) {
            app.touch({TouchEvent::Down, 1, (a - c / 2) * d, b * d}); app.touch({TouchEvent::Down, 2, (a + c / 2) * d, b * d}); step(1);
            for (int i = 1; i <= 10; i++) { float r = c + (e - c) * i / 10.f; app.touch({TouchEvent::Move, 1, (a - r / 2) * d, b * d}); app.touch({TouchEvent::Move, 2, (a + r / 2) * d, b * d}); step(1); }
            app.touch({TouchEvent::Up, 2, (a + e / 2) * d, b * d}); app.touch({TouchEvent::Up, 1, (a - e / 2) * d, b * d}); step(2);
        } else if (!strcmp(cmd, "shot")) {
            char f[512]; sscanf(line + 4, "%511s", f);
            step(1);
            Vec<uint8_t> px; px.resize(W * H * 4);
            // the pbuffer is multisampled: resolve into a single-sample FBO before reading (ES 3.0 rule)
            static unsigned fbo = 0, rb = 0;
            if (!fbo) { glGenFramebuffers(1, &fbo); glGenRenderbuffers(1, &rb); glBindRenderbuffer(GL_RENDERBUFFER, rb); glRenderbufferStorageMultisample(GL_RENDERBUFFER, 0, GL_RGBA8, W, H);
                        glBindFramebuffer(GL_FRAMEBUFFER, fbo); glFramebufferRenderbuffer(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_RENDERBUFFER, rb); }
            glBindFramebuffer(GL_READ_FRAMEBUFFER, 0); glBindFramebuffer(GL_DRAW_FRAMEBUFFER, fbo);
            glBlitFramebuffer(0, 0, W, H, 0, 0, W, H, GL_COLOR_BUFFER_BIT, GL_NEAREST);
            glBindFramebuffer(GL_READ_FRAMEBUFFER, fbo);
            glPixelStorei(GL_PACK_ALIGNMENT, 1); glReadPixels(0, 0, W, H, GL_RGBA, GL_UNSIGNED_BYTE, px.d);
            glBindFramebuffer(GL_FRAMEBUFFER, 0);
            fprintf(stderr, "center px %d %d %d\n", px[(H / 2 * W + W / 2) * 4], px[(H / 2 * W + W / 2) * 4 + 1], px[(H / 2 * W + W / 2) * 4 + 2]);
            write_ppm(f, W, H, px.d); fprintf(stderr, "wrote %s\n", f);
        } else if (!strcmp(cmd, "text")) {
            char* v = line + 5; size_t L = strlen(v); while (L && (v[L - 1] == '\n' || v[L - 1] == '\r')) v[--L] = 0;
            g_text_pending = v; g_text_ready = true; step(3);
        } else if (!strcmp(cmd, "cancel")) { g_text_cancel = true; step(2); }
        else if (!strcmp(cmd, "back")) { if (!app.back()) fprintf(stderr, "back -> exit app\n"); step(2); }
        else if (!strcmp(cmd, "log")) fprintf(stderr, "%s", line);
        else if (!strcmp(cmd, "load")) { char id[128]; sscanf(line + 4, "%127s", id); int i = app.mod_index(id); if (i < 0) fprintf(stderr, "unknown %s\n", id); app.open_module(i); step(4); }
        else if (!strcmp(cmd, "screen")) { sscanf(line + 6, "%d", &k); app.nav_stack.clear(); app.screen = k; app.more_page = 0; step(3); }
        else if (!strcmp(cmd, "more")) { sscanf(line + 4, "%d", &k); app.screen = SCR_MORE; app.more_page = k; step(3); }
        else if (!strcmp(cmd, "theme")) { sscanf(line + 5, "%d", &k); app.store.theme = k; app.apply_theme(); step(2); }
        else if (!strcmp(cmd, "full")) { app.fullscreen = !app.fullscreen; step(3); }
        else if (!strcmp(cmd, "settab")) { sscanf(line + 6, "%d", &k); app.tab = k; app.scroll_to_tabs = true; step(3); }
        else if (!strcmp(cmd, "tour")) { sscanf(line + 4, "%d", &k); app.play_tour(k); step(3); }
        else if (!strcmp(cmd, "select")) { char id[128]; sscanf(line + 6, "%127s", id); app.select(id); step(3); }
        else if (!strcmp(cmd, "overlay")) { char id[128]; sscanf(line + 7, "%127s", id); app.toggle_overlay(id, !app.overlay_on(id)); step(3); }
        else if (!strcmp(cmd, "measure")) { app.measuring = !app.measuring; app.clear_measure(); step(2); }
        else if (!strcmp(cmd, "narrate")) { app.store.narrate = !app.store.narrate; step(1); }
        else if (!strcmp(cmd, "scroll")) { sscanf(line + 6, "%f", &a); const char* names[] = {"##home", "##catalog", "##vpage", "##bookmarks", "##more", "##morepage", "##vright"}; for (const char* nm : names) if (ImGuiWindow* w = ImGui::FindWindowByName(nm)) ImGui::SetScrollY(w, a * d); step(3); }
        else if (!strcmp(cmd, "sweep")) {
            // every module: load, every tab scrolled to the end, overlays on/off, step player, inspector, tour start/stop
            int from = 0, to = app.mods.n; sscanf(line + 5, "%d %d", &from, &to);
            for (int i = from; i < to && i < app.mods.n; i++) {
                double t0 = g_fake_time; (void)t0;
                struct timespec a0, a1; clock_gettime(CLOCK_MONOTONIC, &a0);
                app.open_module(i); step(3);
                clock_gettime(CLOCK_MONOTONIC, &a1);
                if (!app.loaded()) { fprintf(stderr, "SWEEP FAIL load %s: %s\n", app.mods[i].id.c(), app.load_error.c()); continue; }
                double ms = (a1.tv_sec - a0.tv_sec) * 1e3 + (a1.tv_nsec - a0.tv_nsec) / 1e6;
                for (int t = 0; t < TAB_COUNT; t++) { app.tab = t; step(2); if (ImGuiWindow* w = ImGui::FindWindowByName("##vpage")) ImGui::SetScrollY(w, 1e7f); step(2); }
                for (const JV& o : app.M()["overlays"]) { app.toggle_overlay(o.key, true); step(1); }
                app.set_overlay_exclusive(nullptr); step(1);
                app.show_step(0); step(2); app.show_step(1); step(1); app.close_steps();
                const JV& parts = app.M()["parts"]; if (parts.size()) { app.select(parts[0]["id"].str()); step(2); app.select(nullptr); }
                if (app.S()["video_tutorials"].size()) { app.play_tour(0); step(2); app.stop_tour(); }
                app.cut = true; app.xray = true; app.operate = true; app.explode = 0.5f; app.apply_state(); step(3);
                app.cut = app.xray = app.operate = false; app.explode = 0; app.apply_state();
                fprintf(stderr, "SWEEP ok %3d %-40s load %.0f ms, %d tris, %d nodes, tabs %d, overlays %d\n", i + 1, app.mods[i].id.c(), ms, app.model->tris, app.model->nodes.n, TAB_COUNT, app.M()["overlays"].size());
            }
            app.tab = 0;
        }
        else if (!strcmp(cmd, "calcdump")) {
            // default inputs plus a second perturbed input set (each value x1.37 + 0.11) for every calculator
            FILE* o = fopen(line[8] == ' ' ? "/tmp/claude-0/calc_cpp.txt" : "/tmp/claude-0/calc_cpp.txt", "w");
            for (int c = 0; c < NCALCS; c++) for (int pass = 0; pass < 2; pass++) {
                double v[8]; for (int i = 0; i < CALCS[c].nf; i++) v[i] = pass ? CALCS[c].f[i].def * 1.37 + 0.11 : CALCS[c].f[i].def;
                if (!strcmp(CALCS[c].key, "units") && pass) v[1] = 4;
                if (!strcmp(CALCS[c].key, "bearing_life") && pass) v[3] = 2;
                fprintf(o, "== %s %d\n%s\n", CALCS[c].key, pass, CALCS[c].run(v).c());
            }
            fclose(o); fprintf(stderr, "calcdump %d\n", NCALCS);
        }
        else if (!strcmp(cmd, "calckeys")) {
            FILE* o = fopen("/tmp/claude-0/keys_cpp.txt", "w");
            for (int i = 0; i < app.mods.n; i++) {
                Vec<uint8_t> b; JDoc d; Str p = Str::f("learning/%s.json", app.mods[i].id.c());
                if (!plat::read_asset(p, b) || !d.parse((const char*)b.d, (size_t)b.n)) continue;
                Vec<const char*> keys; calc_keys_for(app.mods[i].id, (*d.root)["sections"]["introduction"]["hi_family"].str(), keys);
                fprintf(o, "%s:", app.mods[i].id.c()); for (const char* k : keys) fprintf(o, " %s", k); fprintf(o, "\n");
            }
            fclose(o);
        }
        else if (!strcmp(cmd, "state")) {
            fprintf(stderr, "state: cur=%s tab=%d operate=%d cut=%d xray=%d live=%d explode=%.2f sel='%s' screen=%d picker=%d step=%d tour=%d hidden=%d measuring=%d cam=(%.3f %.3f %.3f) tgt=(%.3f %.3f %.3f)\n",
                app.cur >= 0 ? app.mods[app.cur].id.c() : "-", app.tab, app.operate, app.cut, app.xray, app.live, app.explode, app.selected.c(), app.screen, app.picker_open, app.step_idx, app.tour_n, app.hidden.n, app.measuring,
                app.cam.pos.x, app.cam.pos.y, app.cam.pos.z, app.cam.target.x, app.cam.target.y, app.cam.target.z);
        }
        GLenum ge = glGetError(); if (ge) fprintf(stderr, "GL error 0x%x after: %s", ge, line);
    }
    fclose(sf);
    app.shutdown();
    eglMakeCurrent(dpy, EGL_NO_SURFACE, EGL_NO_SURFACE, EGL_NO_CONTEXT);
    eglTerminate(dpy);
    return 0;
}
