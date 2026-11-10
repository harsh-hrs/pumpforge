// App lifecycle, frame loop, touch gestures (3-D stage + kinetic scrolling for the UI) and text entry.
#include "ui.h"
#include "glapi.h"
#include <stdio.h>

App* g_app = nullptr;
bool ImGuiGLES_Init();
void ImGuiGLES_Render(ImDrawData*);
void ImGuiGLES_Lost();
void ImGuiGLES_Shutdown();

void viewer_cam_touched(bool v);
void pf_imgui_assert(const char* e, const char* f, int l) { pf_log("ImGui assert %s (%s:%d)", e, f, l); }

static ImFont* add_font(const char* path, const char* const* merge, int nmerge) {
    ImGuiIO& io = ImGui::GetIO();
    ImFont* font = nullptr;
    for (int i = -1; i < nmerge; i++) {
        const char* p = i < 0 ? path : merge[i];
        Vec<uint8_t> b;
        if (!plat::read_asset(p, b)) { pf_log("font missing: %s", p); continue; }
        void* mem = ImGui::MemAlloc((size_t)b.n); memcpy(mem, b.d, (size_t)b.n);
        ImFontConfig cfg; cfg.MergeMode = i >= 0 && font; cfg.FontDataOwnedByAtlas = true;
        cfg.OversampleH = 2; cfg.OversampleV = 1; cfg.PixelSnapH = false;
        snprintf(cfg.Name, sizeof cfg.Name, "%s", p);
        ImFont* f = io.Fonts->AddFontFromMemoryTTF(mem, b.n, 14.f, &cfg);
        if (!font) font = f;
    }
    return font;
}

bool App::init(float density, bool dark_mode, char* err, int errlen) {
    g_app = this;
    dp = density; ui::dp = density; sys_dark = dark_mode;
    store.load();
    live = store.live_default; markers = store.markers_default;
    dark = is_dark(); theme_set(dark);
    if (!load_index(err, errlen)) return false;
    IMGUI_CHECKVERSION();
    ImGui::CreateContext();
    ImGuiIO& io = ImGui::GetIO();
    io.IniFilename = nullptr; io.LogFilename = nullptr;
    io.ConfigFlags |= ImGuiConfigFlags_IsTouchScreen | ImGuiConfigFlags_NoMouseCursorChange;
    io.ConfigWindowsMoveFromTitleBarOnly = true;
    io.ConfigInputTrickleEventQueue = true;
    io.ConfigScrollbarScrollByPage = false;
    const char* sym[] = {"fonts/PFSymbols-Regular.ttf"};
    const char* mono_m[] = {"fonts/IBMPlexSans-Regular.ttf", "fonts/PFSymbols-Regular.ttf"};
    f_body = add_font("fonts/IBMPlexSans-Regular.ttf", sym, 1);
    f_med = add_font("fonts/IBMPlexSans-Medium.ttf", sym, 1);
    f_semi = add_font("fonts/IBMPlexSans-SemiBold.ttf", sym, 1);
    f_bold = add_font("fonts/IBMPlexSans-Bold.ttf", sym, 1);
    f_disp = add_font("fonts/IBMPlexSansCondensed-SemiBold.ttf", mono_m, 2);
    f_mono = add_font("fonts/IBMPlexMono-Regular.ttf", mono_m, 2);
    f_monom = add_font("fonts/IBMPlexMono-Medium.ttf", mono_m, 2);
    if (!f_body || !f_med || !f_semi || !f_bold || !f_disp || !f_mono || !f_monom) { snprintf(err, (size_t)errlen, "fonts missing"); return false; }
    setup_style();
    screen = SCR_HOME;          // the 3-D viewer loads its module when it is first opened
    return true;
}

void App::apply_theme() { dark = is_dark(); theme_set(dark); setup_style(); plat::theme_changed(dark); }

void App::setup_style() {
    ImGuiStyle& s = ImGui::GetStyle();
    s = ImGuiStyle();
    s.FontSizeBase = 14 * dp; s.FontScaleDpi = 1; s.FontScaleMain = 1;
    s.WindowPadding = ImVec2(0, 0); s.WindowRounding = 0; s.WindowBorderSize = 0; s.ChildBorderSize = 0; s.PopupBorderSize = 0;
    s.FramePadding = ImVec2(8 * dp, 6 * dp); s.FrameRounding = 6 * dp; s.ItemSpacing = ImVec2(8 * dp, 6 * dp); s.ItemInnerSpacing = ImVec2(6 * dp, 4 * dp);
    s.ScrollbarSize = 3 * dp; s.ScrollbarRounding = 2 * dp; s.GrabMinSize = 18 * dp; s.GrabRounding = 9 * dp;
    s.TouchExtraPadding = ImVec2(2 * dp, 2 * dp);
    s.CellPadding = ImVec2(0, 6 * dp);
    s.AntiAliasedFill = s.AntiAliasedLines = true;
    ImVec4* c = s.Colors;
    auto V = [](ImU32 u) { return ImGui::ColorConvertU32ToFloat4(u); };
    c[ImGuiCol_Text] = V(T.ink); c[ImGuiCol_TextDisabled] = V(T.muted);
    c[ImGuiCol_WindowBg] = V(T.bg); c[ImGuiCol_ChildBg] = ImVec4(0, 0, 0, 0); c[ImGuiCol_PopupBg] = V(T.surface);
    c[ImGuiCol_Border] = V(T.border); c[ImGuiCol_Separator] = V(T.line);
    c[ImGuiCol_FrameBg] = V(T.line); c[ImGuiCol_FrameBgHovered] = V(T.line); c[ImGuiCol_FrameBgActive] = V(T.line);
    c[ImGuiCol_SliderGrab] = V(T.accent); c[ImGuiCol_SliderGrabActive] = V(T.amber);
    c[ImGuiCol_ScrollbarBg] = ImVec4(0, 0, 0, 0); c[ImGuiCol_ScrollbarGrab] = V(T.line); c[ImGuiCol_ScrollbarGrabHovered] = V(T.muted); c[ImGuiCol_ScrollbarGrabActive] = V(T.muted);
    c[ImGuiCol_TableBorderLight] = V(T.line); c[ImGuiCol_TableBorderStrong] = V(T.line); c[ImGuiCol_TableRowBg] = ImVec4(0, 0, 0, 0); c[ImGuiCol_TableRowBgAlt] = ImVec4(0, 0, 0, 0);
    c[ImGuiCol_Header] = V(T.chip); c[ImGuiCol_HeaderHovered] = V(T.chip); c[ImGuiCol_HeaderActive] = V(T.chip);
    c[ImGuiCol_ModalWindowDimBg] = ImVec4(8 / 255.f, 16 / 255.f, 28 / 255.f, 0.55f);
    c[ImGuiCol_NavCursor] = ImVec4(0, 0, 0, 0);
}

bool App::gl_init(char* err, int errlen) {
    if (!R.init(err, errlen)) return false;
    if (!ImGuiGLES_Init()) { snprintf(err, (size_t)errlen, "imgui renderer"); return false; }
    // GL objects of loaded models must exist again (after a context loss)
    if (model) model->upload();
    for (Overlay& o : overlays) if (o.m) o.m->upload();
    if (hero) hero->upload();
    gl_ready = true;
    return true;
}
void App::gl_lost() {
    gl_ready = false;
    R.lost();
    ImGuiGLES_Lost();
    if (model) { for (Mesh& M : model->meshes) for (Prim& p : M.prims) p.vao = p.vbo = p.ibo = p.mbo = 0; model->gpu = false; }
    for (Overlay& o : overlays) if (o.m) { for (Mesh& M : o.m->meshes) for (Prim& p : M.prims) p.vao = p.vbo = p.ibo = p.mbo = 0; o.m->gpu = false; }
    if (hero) { for (Mesh& M : hero->meshes) for (Prim& p : M.prims) p.vao = p.vbo = p.ibo = p.mbo = 0; hero->gpu = false; }
    stage_rt = Target(); hero_rt = Target(); thumb_rt = Target();
    thumbs.clear();
}
void App::shutdown() {
    if (store.dirty) store.save();
    plat::stop_speaking();
    unload();                                  // frees GL objects only when a context is current (gl_ready)
    if (hero) { hero->release(); delete hero; hero = nullptr; }
    if (gl_ready) {
        for (Thumb& t : thumbs) { if (t.tex) glDeleteTextures(1, &t.tex); if (t.fbo) glDeleteFramebuffers(1, &t.fbo); }
        R.target_free(stage_rt); R.target_free(hero_rt); R.target_free(thumb_rt);
        ImGuiGLES_Shutdown(); R.shutdown(); gl_ready = false;
    }
    thumbs.clear();
    if (ImGui::GetCurrentContext()) ImGui::DestroyContext();
}

// Android Back: close the innermost thing first, then walk the screen history, then leave the app.
bool App::back() {
    if (text_target) return true;
    if (picker_open) { picker_open = false; return true; }
    if (screen == SCR_VIEWER) {
        if (fullscreen) { fullscreen = false; return true; }
        if (step_idx >= 0) { close_steps(); return true; }
        if (tour_n >= 0) { stop_tour(); return true; }
        if (!selected.empty()) { select(nullptr); return true; }
        if (measuring) { measuring = false; clear_measure(); return true; }
    }
    if (screen == SCR_MORE && more_page) { more_page = MP_NONE; page_scroll_reset = 0; return true; }
    if (screen == SCR_CATALOG && nav_stack.n == 0 && (cat_dept >= 0 || !cat_query.empty() || cat_saved)) { cat_dept = -1; cat_query.clear(); cat_saved = false; return true; }
    if (nav_stack.n) { screen = nav_stack.back(); nav_stack.pop(); page_scroll_reset = -1; if (screen == SCR_VIEWER) fullscreen = false; return true; }
    if (screen != SCR_HOME) { screen = SCR_HOME; page_scroll_reset = 0; return true; }
    return false;
}

void App::show_toast(const char* m) { toast = m; toast_on = true; toast_until = plat::now() + 2.5; }

// ------------------------------------------------------------------ text entry (system keyboard dialog, polled live)
void App::begin_text(int target, const char* key, const char* title, const char* initial, plat::InputKind kind) {
    text_target = target; text_key = key; text_value = initial;
    plat::text_begin(title, initial, kind);
}

// ------------------------------------------------------------------ touch: queue to ImGui + gesture table
void App::process_touch(float dt) {
    ImGuiIO& io = ImGui::GetIO();
    for (const TouchEvent& e : pending_touch) {
        int k = -1; for (int i = 0; i < ptrs.n; i++) if (ptrs[i].id == e.id) k = i;
        if (e.kind == TouchEvent::Down) {
            if (k < 0) { Ptr p{e.id, e.x, e.y, e.x, e.y, true}; ptrs.push(p); k = ptrs.n - 1; }
            if (ptrs.n == 1) {
                prim_x = last_x = e.x; prim_y = last_y = e.y;
                gesture_pending = true; stage_gesture = ui_gesture = false; gesture_moved = false; scroll_drag = false; scroll_vx = scroll_vy = 0; pinch_d = 0;
                io.AddMouseSourceEvent(ImGuiMouseSource_TouchScreen); io.AddMousePosEvent(e.x, e.y); io.AddMouseButtonEvent(0, true);
            } else { gesture_moved = true; pinch_d = 0; }
        } else if (k >= 0) {
            ptrs[k].x = e.x; ptrs[k].y = e.y;
            if (fabsf(e.x - ptrs[k].sx) > 6 * dp || fabsf(e.y - ptrs[k].sy) > 6 * dp) gesture_moved = true;
            bool primary = k == 0;
            if (primary) { io.AddMouseSourceEvent(ImGuiMouseSource_TouchScreen); io.AddMousePosEvent(e.x, e.y); }
            if (e.kind == TouchEvent::Up || e.kind == TouchEvent::Cancel) {
                if (primary) {
                    io.AddMouseSourceEvent(ImGuiMouseSource_TouchScreen);
                    if (e.kind == TouchEvent::Cancel || scroll_drag) io.AddMousePosEvent(-FLT_MAX, -FLT_MAX);   // never click after a scroll
                    io.AddMouseButtonEvent(0, false);
                }
                bool was_last = ptrs.n == 1;
                if (stage_gesture && was_last && !gesture_moved && e.kind == TouchEvent::Up) tap_stage(e.x, e.y);
                ptrs.erase(k);
                if (ptrs.n) { last_x = ptrs[0].x; last_y = ptrs[0].y; }   // the remaining finger continues without a jump
                if (!ptrs.n) {
                    if (e.kind == TouchEvent::Up && gesture_pending) { /* resolved next frame: keep the tap */ }
                    if (scroll_drag) { scroll_drag = false; kin_t = plat::now(); }
                    else { scroll_vx = scroll_vy = 0; }
                    if (!gesture_pending) { stage_gesture = ui_gesture = false; }
                    io.AddMousePosEvent(-FLT_MAX, -FLT_MAX);
                }
                pinch_d = 0;
            }
        }
    }
    pending_touch.clear();
    (void)dt;
}

// resolve ownership (after ImGui::NewFrame) and drive the camera / scrolling
void App::stage_input(float dt) {
    ImGuiContext& g = *GImGui;
    if (gesture_pending) {
        gesture_pending = false;
        // the stage is an image inside the page: a touch on it orbits unless it hits one of the stage controls
        bool in_stage = stage_visible && screen == SCR_VIEWER && prim_x >= stage_x && prim_x < stage_x + stage_w && prim_y >= stage_clip_y0 && prim_y < stage_clip_y1;
        for (const ImRect_& r : blockers) if (prim_x >= r.x0 && prim_x <= r.x1 && prim_y >= r.y0 && prim_y <= r.y1) in_stage = false;
        if (in_stage && loaded() && pending_load < 0 && !picker_open) { stage_gesture = true; cam.auto_rotate = false; }
        else ui_gesture = true;
        (void)g;
        // a tap that already ended in the same batch
        if (!ptrs.n) { if (stage_gesture && !gesture_moved) tap_stage(prim_x, prim_y); stage_gesture = ui_gesture = false; }
    }
    float slop = 6 * dp;
    if (stage_gesture && ptrs.n) {
        if (ptrs.n == 1) {
            Ptr& p = ptrs[0];
            if (fabsf(p.x - p.sx) > slop || fabsf(p.y - p.sy) > slop) gesture_moved = true;
            float dx = p.x - last_x, dy = p.y - last_y;
            if (gesture_moved && stage_h > 0) { cam.rotate(2 * (float)M_PI * dx / stage_h, 2 * (float)M_PI * dy / stage_h); viewer_cam_touched(true); }
            last_x = p.x; last_y = p.y;
        } else {
            Ptr &a = ptrs[0], &b = ptrs[1];
            float d = sqrtf((a.x - b.x) * (a.x - b.x) + (a.y - b.y) * (a.y - b.y)), mx = (a.x + b.x) / 2, my = (a.y + b.y) / 2;
            if (pinch_d > 0 && d > 1) { cam.dolly(pinch_d / d); cam.pan(mx - pinch_mx, my - pinch_my, stage_h); viewer_cam_touched(true); }
            pinch_d = d; pinch_mx = mx; pinch_my = my;
            last_x = a.x; last_y = a.y;
        }
    }
    // touch scrolling of ImGui windows: a drag beyond the slop converts the press into a scroll (buttons do not fire)
    if (ui_gesture && ptrs.n == 1) {
        Ptr& p = ptrs[0];
        float dx = p.x - last_x, dy = p.y - last_y;
        if (!scroll_drag && !slider_active && (fabsf(p.x - p.sx) > slop * 1.4f || fabsf(p.y - p.sy) > slop * 1.4f)) {
            bool horiz = fabsf(p.x - p.sx) > fabsf(p.y - p.sy);
            ImGuiWindow* w = g.HoveredWindow;
            while (w && !(horiz ? w->ScrollMax.x > 0 : w->ScrollMax.y > 0)) w = w->ParentWindow;
            if (!w && horiz) { w = g.HoveredWindow; while (w && !(w->ScrollMax.y > 0)) w = w->ParentWindow; horiz = false; }
            if (w) { scroll_drag = true; scroll_win = w; scroll_h = horiz; ImGui::ClearActiveID(); scroll_vx = scroll_vy = 0; }
        }
        if (scroll_drag && scroll_win) {
            ImGuiWindow* w = (ImGuiWindow*)scroll_win;
            if (scroll_h) ImGui::SetScrollX(w, w->Scroll.x - dx); else ImGui::SetScrollY(w, w->Scroll.y - dy);
            float v = (scroll_h ? dx : dy) / fmaxf(dt, 1e-3f);
            float& sv = scroll_h ? scroll_vx : scroll_vy;
            sv = sv * 0.6f + v * 0.4f;
        }
        last_x = p.x; last_y = p.y;
    } else if (!ptrs.n && scroll_win && (fabsf(scroll_vx) > 20 || fabsf(scroll_vy) > 20)) {
        // kinetic fling
        ImGuiWindow* w = (ImGuiWindow*)scroll_win;
        if (scroll_h) { ImGui::SetScrollX(w, w->Scroll.x - scroll_vx * dt); scroll_vx *= expf(-4.f * dt); }
        else { ImGui::SetScrollY(w, w->Scroll.y - scroll_vy * dt); scroll_vy *= expf(-4.f * dt); }
    }
    if (!ptrs.n && !gesture_pending) { stage_gesture = ui_gesture = false; }
}

// ------------------------------------------------------------------ frame
void App::frame(double now) {
    float dt = t_last > 0 ? (float)pf_min(0.05, now - t_last) : 1.f / 60;   // three.js clock delta clamped to 0.05 s
    if (dt <= 0) dt = 1e-3f;
    t_last = now;
    if (!gl_ready || fbw <= 0 || fbh <= 0) return;
    ImGuiIO& io = ImGui::GetIO();
    io.DisplaySize = ImVec2((float)fbw, (float)fbh); io.DisplayFramebufferScale = ImVec2(1, 1);
    io.DeltaTime = dt;
    process_touch(dt);
    if (pending_load >= 0 && --pending_frames <= 0) { int k = pending_load; pending_load = -1; do_load(k); }
    if (loaded()) {
        if (operate && op_anim >= 0) { anim_started = true; anim_t += dt; float d = model->anims[op_anim].dur; if (d > 0) anim_t = fmodf(anim_t, d); }
        update_particles(dt);
        cam.update(dt);
        if (!flash_part.empty() && now >= flash_until) { hl_set(flash_part, false); flash_part.clear(); if (!selected.empty()) hl_set(selected, true); }
        if (step_idx >= 0 && step_auto && now >= step_next) show_step(step_idx + 1);
        tour_tick(now);
        if (explode_target >= 0) {   // Exploded View segment: animate the explode amount
            explode += (explode_target - explode) * fminf(1.f, dt * 5.f);
            if (fabsf(explode - explode_target) < 0.004f) { explode = explode_target; explode_target = -1; }
        }
    }
    if (toast_on && now > toast_until) toast_on = false;
    ui_text_poll();
    ImGui::NewFrame();
    stage_input(dt);
    slider_active = false;
    build_ui(dt);
    ImGui::Render();
    // ---- GL: offscreen 3-D first (stage, hero, one thumbnail), then the UI that shows them
    if (screen == SCR_VIEWER && stage_visible && stage_rt.fbo && loaded() && pending_load < 0) {
        R.target_begin(stage_rt);
        R.background(T.stage0, T.stage1);
        render_scene();
        R.target_end(stage_rt);
    }
    hero_update(dt);
    if (!hero_wanted && hero && screen != SCR_HOME) { hero->release(); delete hero; hero = nullptr; }
    thumbs_update();
    glBindFramebuffer(GL_FRAMEBUFFER, 0);
    glViewport(0, 0, fbw, fbh); glDisable(GL_SCISSOR_TEST);
    ImVec4 bg = ImGui::ColorConvertU32ToFloat4(T.bg);
    glClearColor(bg.x, bg.y, bg.z, 1); glColorMask(GL_TRUE_, GL_TRUE_, GL_TRUE_, GL_TRUE_); glDepthMask(GL_TRUE_); glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);
    ImGuiGLES_Render(ImGui::GetDrawData());
    static double last_save = 0;
    if (store.dirty && now - last_save > 1.5) { store.save(); last_save = now; }
}
