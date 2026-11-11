// 3-D Viewer screen: header card, view-mode segments, stage (render-to-texture) with side controls, markers and
// overlays, action chips, How-it-works player, part inspector, lesson tabs and the engineering tools.
#include "ui.h"
#include "calcs.h"
#include <stdio.h>

using namespace ui;
extern const ImGuiWindowFlags WF;
extern bool g_wide;
Str dept_label(const App& a, int d);
void thumb_tile(App& a, ImDrawList* dl, int mod, ImVec2 p0, ImVec2 p1, float r, bool gradient);

static const char* TAB_NAMES[TAB_COUNT] = {"Overview", "Parts", "Working", "Operation", "Specs", "Care", "Failures", "Tours", "Quiz", "Tools"};
static const int TAB_ICONS[TAB_COUNT] = {IC_INFO, IC_TAG, IC_GEAR, IC_HAND, IC_GAUGE, IC_WRENCH, IC_ALERT, IC_PLAYCIRCLE, IC_CHECK, IC_CALC};
static ImU32 marker_col(int i) {
    static const uint32_t P[8] = {0x4d9bff, 0xffb21e, 0x3ddc97, 0xff6b6b, 0xb38cff, 0x41d1f0, 0xff9a52, 0xe86ad6};
    uint32_t c = P[i % 8]; return IM_COL32((c >> 16) & 255, (c >> 8) & 255, c & 255, 255);
}
static bool g_tab_clicked = false;
static bool g_cam_touched = false;

static void page_begin_v(const char* id, float x, float y, float w, float h, bool scroll) {
    ImGui::SetNextWindowPos(ImVec2(x, y)); ImGui::SetNextWindowSize(ImVec2(w, h));
    ImGui::PushStyleColor(ImGuiCol_WindowBg, IM_COL32(0, 0, 0, 0));
    ImGui::PushStyleVar(ImGuiStyleVar_WindowPadding, ImVec2(0, 0));
    ImGui::Begin(id, nullptr, WF | ImGuiWindowFlags_NoScrollWithMouse | (scroll ? 0 : (ImGuiWindowFlags_NoScrollbar | ImGuiWindowFlags_NoScrollWithMouse)));
    ImGui::PopStyleVar(); ImGui::PopStyleColor();
}

static bool part_btn(App& a, const char* id, const char* label, const char* uid) {
    if (!id || !*id || !a.has_part_node(id)) return false;
    if (link(label, uid)) {
        if (!a.cut) { a.cut = true; a.apply_state(); }
        a.flash(id, plat::now()); a.frame_part(id);
        a.page_scroll_reset = 0;      // bring the model into view
        return true;
    }
    return false;
}

// ------------------------------------------------------------------ header card + view-mode segments + chips
static void header_card(App& a, float cw) {
    ImDrawList* dl = ImGui::GetWindowDrawList();
    const ModInfo& m = a.mods[a.pending_load >= 0 ? a.pending_load : a.cur];
    int mi = a.pending_load >= 0 ? a.pending_load : a.cur;
    ImVec2 p = ImGui::GetCursorScreenPos(); float hh = px(96);
    ImGui::Dummy(ImVec2(cw, hh));
    ImVec2 q(p.x + cw, p.y + hh);
    card_bg(dl, p, q, px(18), T.surface);
    // thumbnail with accent ring
    ImVec2 t0(p.x + px(10), p.y + px(10)), t1(p.x + px(86), q.y - px(10));
    dl->AddRect(ImVec2(t0.x - px(1), t0.y - px(1)), ImVec2(t1.x + px(1), t1.y + px(1)), T.accent, px(13), px(1.5f));
    thumb_tile(a, dl, mi, t0, t1, px(12), true);
    float tx = p.x + px(98), tw = cw - px(98) - px(96);
    text_clipped(dl, a.f_bold, 18, ImVec2(tx, p.y + px(12)), tw, T.ink, m.title, 2);
    float th = fminf(text_size(a.f_bold, 18, m.title, tw).y, px(18 * 1.25f * 2));
    text_clipped(dl, a.f_body, 12.5f, ImVec2(tx, p.y + px(16) + th), tw, T.muted, Str::f("%s · %s", m.eq_id.empty() ? Str::f("Module %d", m.no).c() : m.eq_id.c(), m.subcategory.empty() ? m.category.c() : m.subcategory.c()));
    text_at(dl, a.f_med, 11.5f, ImVec2(tx, q.y - px(24)), (dept_color(m.dept, 2) & 0x00ffffff) | 0xff000000, m.m2p && m.area_idx >= 0 ? Str::f("Mine to Port · %s %s", a.areas[m.area_idx].id.c(), a.areas[m.area_idx].name.c()) : Str::f("%d / %d · %s", m.no, a.mods.n, m.department.c()));
    // previous / next module
    ImGui::SetCursorScreenPos(ImVec2(q.x - px(88), p.y + (hh - px(38)) / 2));
    if (round_icon("vprev", IC_PREV, 38, T.surface2, T.ink, true)) a.request_load((mi - 1 + a.mods.n) % a.mods.n);
    ImGui::SameLine(0, px(6));
    if (round_icon("vnext", IC_NEXT, 38, T.surface2, T.ink, true)) a.request_load((mi + 1) % a.mods.n);
    ImGui::SetCursorScreenPos(ImVec2(p.x, q.y)); ImGui::Dummy(ImVec2(1, px(10)));
}

static void segments(App& a, float cw) {
    ImDrawList* dl = ImGui::GetWindowDrawList();
    const char* L[4] = {"3D View", "Exploded", "Cutaway", "X-ray"}; int I[4] = {IC_CUBE, IC_LAYERS, IC_CUT, IC_EYE};
    bool on[4] = {!a.cut && !a.xray && a.explode < 0.01f && a.explode_target <= 0, a.explode >= 0.01f || a.explode_target > 0, a.cut, a.xray};
    ImVec2 p = ImGui::GetCursorScreenPos(); float hh = px(46), sw = cw / 4;
    dl->AddRectFilled(p, ImVec2(p.x + cw, p.y + hh), T.surface, px(14));
    dl->AddRect(p, ImVec2(p.x + cw, p.y + hh), T.border, px(14), px(1));
    for (int k = 0; k < 4; k++) {
        ImGui::PushID(k);
        ImGui::SetCursorScreenPos(ImVec2(p.x + sw * k, p.y));
        bool click = ImGui::InvisibleButton("##seg", ImVec2(sw, hh));
        ImVec2 a0(p.x + sw * k + px(4), p.y + px(4)), a1(p.x + sw * (k + 1) - px(4), p.y + hh - px(4));
        if (on[k]) { glow(dl, a0, a1, px(10), T.glow, px(3)); grad_rect(dl, a0, a1, px(10), T.accent, T.accent2); }
        else if (ImGui::IsItemActive()) dl->AddRectFilled(a0, a1, T.surface2, px(10));
        ImU32 fg = on[k] ? T.accent_ink : T.ink;
        float lw = text_size(a.f_med, 13, L[k]).x, tot = lw + (g_wide || cw > px(380) ? px(22) : 0);
        float sx = (a0.x + a1.x - tot) / 2;
        if (tot > lw) { draw_icon(dl, I[k], ImVec2(sx + px(8), (a0.y + a1.y) / 2), px(15), fg); sx += px(22); }
        text_at(dl, on[k] ? a.f_semi : a.f_med, 13, ImVec2(sx, (a0.y + a1.y) / 2 - px(9)), fg, L[k]);
        if (click && a.loaded()) {
            if (k == 0) { a.cut = a.xray = false; a.explode_target = 0; a.apply_state(); }
            else if (k == 1) a.explode_target = (a.explode >= 0.01f || a.explode_target > 0) ? 0.f : 1.f;
            else if (k == 2) { a.cut = !a.cut; a.apply_state(); }
            else { a.xray = !a.xray; a.apply_state(); }
        }
        ImGui::PopID();
    }
    ImGui::SetCursorScreenPos(ImVec2(p.x, p.y + hh)); ImGui::Dummy(ImVec2(1, px(10)));
}

static void chips_row(App& a, float cw) {
    ImGui::PushStyleVar(ImGuiStyleVar_ItemSpacing, ImVec2(px(8), 0));
    ImGui::BeginChild("##vchips", ImVec2(cw, px(40)), 0, ImGuiWindowFlags_HorizontalScrollbar | ImGuiWindowFlags_NoScrollbar | ImGuiWindowFlags_NoScrollWithMouse);
    if (a.loaded()) {
        if (pill("How it works", a.step_idx >= 0, IC_STEPS, "hiw")) { if (a.step_idx >= 0) a.close_steps(); else a.show_step(0); }
        ImGui::SameLine(); if (pill("Live flow", a.live, IC_FLOW, "live")) { a.live = !a.live; a.apply_state(); }
        for (const JV& o : a.M()["overlays"]) { ImGui::SameLine(); if (pill(o["title"].str(), a.overlay_on(o.key), IC_SPARK, o.key)) a.toggle_overlay(o.key, !a.overlay_on(o.key)); }
        ImGui::SameLine(); if (pill("Labels", a.markers, IC_TAG, "lbl")) a.markers = !a.markers;
        ImGui::SameLine(); if (pill("Measure", a.measuring, IC_RULER, "meas")) { a.measuring = !a.measuring; a.clear_measure(); }
        if (!a.hidden.empty()) { ImGui::SameLine(); if (pill("Show all parts", false, IC_EYE, "showall")) { a.hidden.clear(); a.apply_state(); } }
    }
    ImGui::EndChild();
    ImGui::PopStyleVar();
    ImGui::Dummy(ImVec2(1, px(8)));
}

// ------------------------------------------------------------------ stage (3-D view as an image + overlays)
static bool glass_btn(App& a, const char* id, int icon, ImVec2 c, float r, bool active) {
    ImDrawList* dl = ImGui::GetWindowDrawList();
    ImGui::SetCursorScreenPos(ImVec2(c.x - r, c.y - r));
    ImGui::PushID(id);
    bool click = ImGui::InvisibleButton("##g", ImVec2(2 * r, 2 * r));
    ImGui::PopID();
    a.blockers.push({c.x - r, c.y - r, c.x + r, c.y + r});
    if (active) { int v0 = dl->VtxBuffer.Size; dl->AddCircleFilled(c, r, IM_COL32_WHITE, 32); ImGui::ShadeVertsLinearColorGradientKeepAlpha(dl, v0, dl->VtxBuffer.Size, ImVec2(c.x, c.y - r), ImVec2(c.x, c.y + r), T.accent, T.accent2); }
    else dl->AddCircleFilled(c, r, T.dark ? IM_COL32(0x0b, 0x18, 0x36, 200) : IM_COL32(255, 255, 255, 220), 32);
    dl->AddCircle(c, r, active ? T.accent : T.border, 32, px(1));
    if (ImGui::IsItemActive()) dl->AddCircleFilled(c, r, IM_COL32(255, 255, 255, 40), 32);
    draw_icon(dl, icon, c, r * 0.95f, active ? IM_COL32_WHITE : T.ink);
    return click;
}

void App::ui_stage(float sx, float sy, float sw, float sh) {
    ImDrawList* dl = ImGui::GetWindowDrawList();
    ImGui::SetCursorScreenPos(ImVec2(sx, sy));
    ImGui::Dummy(ImVec2(sw, sh));
    ImGuiWindow* win = ImGui::GetCurrentWindow();
    stage_x = sx; stage_y = sy; stage_w = sw; stage_h = sh;
    stage_clip_y0 = fmaxf(sy, win->InnerClipRect.Min.y); stage_clip_y1 = fminf(sy + sh, win->InnerClipRect.Max.y);
    stage_visible = stage_clip_y1 - stage_clip_y0 > 2 && sw > 8;
    float r = fullscreen ? 0 : px(20);
    ImVec2 a(sx, sy), b(sx + sw, sy + sh);
    if (!fullscreen) glow(dl, a, b, r, T.glow, px(4));
    if (gl_ready && stage_visible) R.target_ensure(stage_rt, (int)sw, (int)sh);
    bool ready = loaded() && pending_load < 0;
    if (ready && stage_rt.tex) image(dl, stage_rt.tex, a, b, r, false);
    else { grad_rect(dl, a, b, r, T.dark ? IM_COL32(0x16, 0x30, 0x5f, 255) : IM_COL32(0xf3, 0xf6, 0xfb, 255), T.dark ? IM_COL32(0x07, 0x11, 0x28, 255) : IM_COL32(0xdc, 0xe3, 0xee, 255)); }
    if (!fullscreen) dl->AddRect(a, b, T.border, r, px(1));
    dl->PushClipRect(a, b, true);
    if (!ready) {
        spinner(dl, ImVec2((a.x + b.x) / 2, (a.y + b.y) / 2 - px(10)), px(18), T.accent, plat::now());
        const char* msg = load_error.empty() || pending_load >= 0 ? "Loading model…" : load_error.c();
        ImVec2 ts = text_size(f_med, 13, msg); text_at(dl, f_med, 13, ImVec2((a.x + b.x - ts.x) / 2, (a.y + b.y) / 2 + px(20)), T.muted, msg);
        dl->PopClipRect();
        return;
    }
    M4 vp = cam.proj(sw / sh) * cam.view();
    auto proj = [&](V3 p, ImVec2& o) { float nx, ny, nz; if (!m4_project(vp, p, nx, ny, nz) || nz >= 1) return false; o = ImVec2(sx + (nx + 1) / 2 * sw, sy + (1 - ny) / 2 * sh); return true; };
    // numbered part markers (match the Parts tab)
    if (markers || tab == TAB_PARTS) {
        int i = 0;
        for (const JV& p : M()["parts"]) {
            i++;
            bool hid = false; for (const Str& hd : hidden) if (hd.eq(p["id"].str())) hid = true;
            const JV& an = p["label_anchor"].size() == 3 ? p["label_anchor"] : p["center"];
            if (hid || an.size() != 3) continue;
            ImVec2 c; if (!proj(V3((float)an[0].n(), (float)an[1].n(), (float)an[2].n()), c)) continue;
            bool sel = selected.eq(p["id"].str());
            float rr = px(sel ? 12 : 10);
            dl->AddCircleFilled(c, rr + px(2), IM_COL32(0, 0, 0, 90), 20);
            dl->AddCircleFilled(c, rr, marker_col(i - 1), 20);
            if (sel) dl->AddCircle(c, rr + px(3), IM_COL32_WHITE, 20, px(2));
            Str n = Str::f("%d", i); ImVec2 ts = text_size(f_bold, 11, n);
            text_at(dl, f_bold, 11, ImVec2(c.x - ts.x / 2, c.y - ts.y / 2), IM_COL32(8, 16, 32, 255), n);
        }
    }
    // overlay annotations
    for (const Label& l : labels) {
        ImVec2 c; if (!proj(l.p, c)) continue;
        ImVec2 ts = text_size(f_med, 11.5f, l.text);
        ImVec2 p0(c.x - ts.x / 2 - px(8), c.y - ts.y / 2 - px(4)), p1(c.x + ts.x / 2 + px(8), c.y + ts.y / 2 + px(4));
        dl->AddRectFilled(p0, p1, T.label_bg, px(6)); dl->AddRect(p0, p1, IM_COL32(0x4d, 0x8f, 0xff, 120), px(6), px(1));
        text_at(dl, f_med, 11.5f, ImVec2(p0.x + px(8), p0.y + px(4)), IM_COL32_WHITE, l.text);
    }
    if (m_line) {
        ImVec2 p0, p1;
        if (proj(m_a, p0) && proj(m_b, p1)) { dl->AddLine(p0, p1, IM_COL32(0xff, 0x2d, 0x55, 255), px(2.5f)); dl->AddCircleFilled(p0, px(4), IM_COL32(0xff, 0x2d, 0x55, 255)); dl->AddCircleFilled(p1, px(4), IM_COL32(0xff, 0x2d, 0x55, 255)); }
    }
    // top-left badges: operating, measuring
    float by = sy + px(12);
    auto badge = [&](const char* t, ImU32 dot) {
        ImVec2 ts = text_size(f_med, 12, t);
        ImVec2 p0(sx + px(12), by), p1(sx + px(12) + ts.x + px(dot ? 30 : 20), by + px(26));
        dl->AddRectFilled(p0, p1, T.overlay_bg, px(13));
        float tx = p0.x + px(10);
        if (dot) { dl->AddCircleFilled(ImVec2(tx + px(4), by + px(13)), px(4), dot, 12); tx += px(14); }
        text_at(dl, f_med, 12, ImVec2(tx, by + px(5)), IM_COL32_WHITE, t);
        by += px(32);
    };
    if (operate) badge("Operating", T.good);
    if (measuring) badge(m_text, IM_COL32(0xff, 0x2d, 0x55, 255));
    if (!g_cam_touched && !operate && !measuring && step_idx < 0 && tour_n < 0) {
        const char* hint = "Drag to orbit · pinch to zoom · tap a part";
        ImVec2 ts = text_size(f_body, 11.5f, hint);
        if (ts.x < sw - px(80)) text_at(dl, f_body, 11.5f, ImVec2(sx + px(14), by + px(2)), T.dark ? IM_COL32(255, 255, 255, 150) : T.muted, hint);
    }
    // right column: operate, auto-rotate, zoom in/out, reset view
    float br = px(21), bx = sx + sw - px(12) - br, cy = sy + px(12) + br;
    if (glass_btn(*this, "op", operate ? IC_PAUSE : IC_PLAY, ImVec2(bx, cy), br, operate)) { operate = !operate; apply_state(); }
    cy += 2 * br + px(10);
    if (sh > px(260)) { if (glass_btn(*this, "rot", IC_ROTATE, ImVec2(bx, cy), br, cam.auto_rotate)) { cam.auto_rotate = !cam.auto_rotate; cam.auto_speed = 1.2f; } cy += 2 * br + px(10); }
    if (glass_btn(*this, "zin", IC_PLUS, ImVec2(bx, cy), br, false)) cam.dolly(0.8f);
    cy += 2 * br + px(10);
    if (glass_btn(*this, "zout", IC_MINUS, ImVec2(bx, cy), br, false)) cam.dolly(1.25f);
    cy += 2 * br + px(10);
    if (glass_btn(*this, "reset", IC_TARGET, ImVec2(bx, cy), br, false)) { cam.auto_rotate = false; frame_full(); }
    // bottom area: tour caption / selected part / explode slider / 360 badge
    float bottom = sy + sh - px(12);
    bool show_ex = explode >= 0.01f || explode_target > 0;
    if (show_ex) {
        float ew = fminf(sw - px(24) - (2 * br + px(10)), px(360)), eh = px(40);
        ImVec2 p0(sx + px(12), bottom - eh), p1(p0.x + ew, bottom);
        dl->AddRectFilled(p0, p1, T.dark ? IM_COL32(0x0b, 0x18, 0x36, 215) : IM_COL32(255, 255, 255, 230), eh / 2);
        dl->AddRect(p0, p1, T.border, eh / 2, px(1));
        draw_icon(dl, IC_LAYERS, ImVec2(p0.x + px(20), p0.y + eh / 2), px(16), T.accent);
        Str pc = Str::f("%d%%", (int)roundf(explode * 100)); ImVec2 ts = text_size(f_monom, 12, pc);
        text_at(dl, f_monom, 12, ImVec2(p1.x - ts.x - px(14), p0.y + (eh - ts.y) / 2), T.ink, pc);
        ImGui::SetCursorScreenPos(ImVec2(p0.x + px(38), p0.y + px(7)));
        ImGui::PushStyleVar(ImGuiStyleVar_FramePadding, ImVec2(0, px(6))); ImGui::PushStyleVar(ImGuiStyleVar_GrabMinSize, px(20)); ImGui::PushStyleVar(ImGuiStyleVar_FrameRounding, px(13)); ImGui::PushStyleVar(ImGuiStyleVar_GrabRounding, px(10));
        ImGui::PushStyleColor(ImGuiCol_FrameBg, T.line); ImGui::PushStyleColor(ImGuiCol_FrameBgActive, T.line); ImGui::PushStyleColor(ImGuiCol_FrameBgHovered, T.line);
        ImGui::SetNextItemWidth(ew - px(38) - ts.x - px(26));
        font(f_body, 12);
        float ex = explode;
        if (ImGui::SliderFloat("##ex", &ex, 0, 1, "", ImGuiSliderFlags_AlwaysClamp | ImGuiSliderFlags_NoRoundToFormat)) { explode = ex; explode_target = -1; }
        pop();
        if (ImGui::IsItemActive()) slider_active = true;
        ImGui::PopStyleColor(3); ImGui::PopStyleVar(4);
        blockers.push({p0.x, p0.y, p1.x, p1.y});
        bottom -= eh + px(8);
    }
    if (!selected.empty() && part_index(selected) >= 0) {
        const char* nm = M()["parts"][part_index(selected)]["name"].str();
        float pw = fminf(sw - px(24) - (2 * br + px(10)), px(380)), ph = px(44);
        ImVec2 p0(sx + px(12), bottom - ph), p1(p0.x + pw, bottom);
        dl->AddRectFilled(p0, p1, T.overlay_bg, px(14)); dl->AddRect(p0, p1, T.accent, px(14), px(1));
        dl->AddCircleFilled(ImVec2(p0.x + px(20), p0.y + ph / 2), px(9), T.accent, 16);
        draw_icon(dl, IC_TAG, ImVec2(p0.x + px(20), p0.y + ph / 2), px(12), IM_COL32_WHITE);
        text_clipped(dl, f_semi, 13.5f, ImVec2(p0.x + px(38), p0.y + px(13)), pw - px(130), IM_COL32_WHITE, nm);
        ImGui::SetCursorScreenPos(ImVec2(p1.x - px(88), p0.y + px(6)));
        ImGui::PushID("seldet");
        if (ImGui::InvisibleButton("##d", ImVec2(px(80), px(32)))) { tab = TAB_PARTS; scroll_to_tabs = true; }
        ImGui::PopID();
        dl->AddRectFilled(ImVec2(p1.x - px(88), p0.y + px(7)), ImVec2(p1.x - px(8), p1.y - px(7)), T.accent, px(10));
        text_at(dl, f_semi, 12.5f, ImVec2(p1.x - px(74), p0.y + px(13)), IM_COL32_WHITE, "Details");
        blockers.push({p0.x, p0.y, p1.x, p1.y});
        bottom -= ph + px(8);
    }
    if (step_idx >= 0 && (!g_wide || fullscreen)) {
        // How-it-works player on the model (phones / full screen): the stage stays in view while stepping
        const JV& st = S()["working_principle"]["steps"];
        float col_bottom = sy + px(12) + 5 * (2 * br + px(10));
        float cw2 = sw - px(24), tw = cw2 - px(24);
        const char* txt = step_idx < st.size() ? st[step_idx]["text"].str() : "";
        float th = text_size(f_body, 13.5f, txt, tw).y;
        float ch = px(34) + th + px(58);
        if (bottom - ch < col_bottom) { cw2 = sw - px(24) - (2 * br + px(10)); tw = cw2 - px(24); th = text_size(f_body, 13.5f, txt, tw).y; ch = px(34) + th + px(58); }
        ImVec2 p0(sx + px(12), bottom - ch), p1(p0.x + cw2, bottom);
        dl->AddRectFilled(p0, p1, T.overlay_bg, px(16)); dl->AddRect(p0, p1, T.accent, px(16), px(1));
        text_at(dl, f_semi, 11.5f, ImVec2(p0.x + px(12), p0.y + px(10)), T.amber, Str::f("HOW IT WORKS · STEP %d OF %d", step_idx + 1, st.size()));
        for (int k = 0; k < st.size(); k++) { float sg = (cw2 - px(70) - px(3) * (st.size() - 1)) / st.size(); ImVec2 s0(p0.x + px(12) + k * (sg + px(3)), p0.y + px(28)); dl->AddRectFilled(s0, ImVec2(s0.x + sg, s0.y + px(3)), k <= step_idx ? T.accent : IM_COL32(255, 255, 255, 40), px(2)); }
        text_at(dl, f_body, 13.5f, ImVec2(p0.x + px(12), p0.y + px(38)), IM_COL32_WHITE, txt, tw);
        float rb = px(17), ry = p1.y - px(26);
        ImGui::SetCursorScreenPos(ImVec2(p1.x - px(40), p0.y + px(4)));
        if (round_icon("stx", IC_CLOSE, 34, IM_COL32(255, 255, 255, 24), IM_COL32_WHITE)) close_steps();
        ImGui::SetCursorScreenPos(ImVec2(p0.x + px(12), ry - rb));
        if (round_icon("stp", IC_PREV, 34, IM_COL32(255, 255, 255, 30), IM_COL32_WHITE)) show_step(step_idx - 1);
        ImGui::SameLine(0, px(10));
        if (round_icon("sta", step_auto ? IC_PAUSE : IC_PLAY, 34, step_auto ? T.accent : IM_COL32(255, 255, 255, 30), IM_COL32_WHITE)) { step_auto = !step_auto; if (step_auto) step_next = plat::now() + 6.0; }
        ImGui::SameLine(0, px(10));
        if (round_icon("stn", IC_NEXT, 34, T.accent, IM_COL32_WHITE)) show_step(step_idx + 1);
        text_at(dl, f_med, 12, ImVec2(p0.x + px(150), ry - px(8)), IM_COL32(255, 255, 255, 170), step_auto ? "Auto: next step every 6 s" : "Back · Auto · Next");
        blockers.push({p0.x, p0.y, p1.x, p1.y});
        bottom -= ch + px(8);
    }
    if (tour_n >= 0 && !caption.empty()) {
        float cw2 = fminf(sw - px(24) - (2 * br + px(10)), px(560)), tw = cw2 - px(80);
        ImVec2 hs = text_size(f_monom, 11, caption_head, tw), ts = text_size(f_body, 13.5f, caption, tw);
        float ch = px(20) + hs.y + ts.y;
        ImVec2 p0(sx + px(12), bottom - ch), p1(p0.x + cw2, bottom);
        dl->AddRectFilled(p0, p1, T.overlay_bg, px(14)); dl->AddRect(p0, p1, T.border, px(14), px(1));
        text_at(dl, f_monom, 11, ImVec2(p0.x + px(12), p0.y + px(8)), IM_COL32(0x9f, 0xc0, 0xff, 255), caption_head, tw);
        text_at(dl, f_body, 13.5f, ImVec2(p0.x + px(12), p0.y + px(12) + hs.y), IM_COL32_WHITE, caption, tw);
        ImGui::SetCursorScreenPos(ImVec2(p1.x - px(56), p0.y + (ch - px(40)) / 2));
        if (round_icon("tstop", IC_STOP, 40, T.bad, IM_COL32_WHITE)) stop_tour();
        blockers.push({p0.x, p0.y, p1.x, p1.y});
        bottom -= ch + px(8);
    }
    if (!g_cam_touched && bottom >= sy + sh - px(12) - 0.5f && sh > px(220)) {   // only when the bottom area is free
        ImVec2 c(sx + sw / 2, sy + sh - px(30));
        ImU32 col = T.dark ? IM_COL32(255, 255, 255, 170) : IM_COL32(0x33, 0x44, 0x66, 170);
        dl->PathArcTo(ImVec2(c.x, c.y - px(26)), px(60), 0.45f, 2.7f, 24); dl->PathStroke(col, px(1.5f));
        ImVec2 ts = text_size(f_bold, 14, "360°");
        dl->AddRectFilled(ImVec2(c.x - ts.x / 2 - px(8), c.y - px(2)), ImVec2(c.x + ts.x / 2 + px(8), c.y + ts.y + px(2)), T.overlay_bg, px(8));
        text_at(dl, f_bold, 14, ImVec2(c.x - ts.x / 2, c.y), IM_COL32_WHITE, "360°");
    }
    dl->PopClipRect();
    ImGui::SetCursorScreenPos(ImVec2(sx, sy + sh)); ImGui::Dummy(ImVec2(1, 1));
}

// ------------------------------------------------------------------ step player + tabs bar
static void step_card(App& a, float cw) {
    if (a.step_idx < 0 || !a.loaded()) return;
    const JV& st = a.S()["working_principle"]["steps"];
    ImGui::PushID("stepcard");
    card_begin("##st");
    float iw = ImGui::GetContentRegionAvail().x;
    ImDrawList* dl = ImGui::GetWindowDrawList();
    ImVec2 p = ImGui::GetCursorScreenPos();
    text_at(dl, a.f_semi, 11.5f, p, T.amber, Str::f("HOW IT WORKS · STEP %d OF %d", a.step_idx + 1, st.size()));
    ImGui::SetCursorScreenPos(ImVec2(p.x + iw - px(34), p.y - px(6)));
    if (round_icon("stx", IC_CLOSE, 34, T.surface2, T.ink)) a.close_steps();
    ImGui::SetCursorScreenPos(ImVec2(p.x, p.y + px(26)));
    // progress segments
    for (int k = 0; k < st.size(); k++) { float sw = (iw - px(4) * (st.size() - 1)) / st.size(); ImVec2 s0(p.x + k * (sw + px(4)), p.y + px(20)); dl->AddRectFilled(s0, ImVec2(s0.x + sw, s0.y + px(3)), k <= a.step_idx ? T.accent : T.line, px(2)); }
    if (a.step_idx < st.size()) text(a.f_body, 14.5f, T.ink, st[a.step_idx]["text"].str());
    spacer(8);
    float bw = (iw - px(16)) / 3;
    if (tool("‹ Back", false, bw, "stprev")) a.show_step(a.step_idx - 1);
    ImGui::SameLine(0, px(8));
    if (tool(a.step_auto ? "Auto ■" : "Auto ▶", a.step_auto, bw, "stauto")) { a.step_auto = !a.step_auto; if (a.step_auto) a.step_next = plat::now() + 6.0; }
    ImGui::SameLine(0, px(8));
    if (tool("Next ›", false, bw, "stnext")) a.show_step(a.step_idx + 1);
    card_end();
    ImGui::PopID();
    (void)cw;
}

// tabs shown for the loaded module (Operation only where the lesson has operating guidance — Mine-to-Port equipment)
bool App::has_tab(int t) {
    if (t == TAB_OPERATION) return loaded() && S()["operation"].isObj();
    return true;
}

void App::ui_tabs_bar(float w, bool sticky) {
    ImGui::PushStyleVar(ImGuiStyleVar_ItemSpacing, ImVec2(px(8), 0));
    ImGui::BeginChild(sticky ? "##tabs2" : "##tabs", ImVec2(w, px(42)), 0, ImGuiWindowFlags_HorizontalScrollbar | ImGuiWindowFlags_NoScrollbar | ImGuiWindowFlags_NoScrollWithMouse | ImGuiWindowFlags_NoBackground);
    if (!has_tab(tab)) tab = TAB_OVERVIEW;
    bool first = true;
    for (int t = 0; t < TAB_COUNT; t++) {
        if (!has_tab(t)) continue;
        if (!first) ImGui::SameLine();
        first = false;
        ImGui::PushID(t);
        if (pill(TAB_NAMES[t], tab == t, TAB_ICONS[t], "tab", 38)) { if (tab != t) { tab = t; g_tab_clicked = true; } }
        if (tab == t && (g_tab_clicked || ImGui::IsWindowAppearing())) ImGui::SetScrollHereX(0.5f);
        ImGui::PopID();
    }
    ImGui::EndChild();
    ImGui::PopStyleVar();
}

// ------------------------------------------------------------------ screen
void App::ui_viewer(float x, float y, float w, float h) {
    if (cur < 0 && pending_load < 0) { int m = mod_index(store.last); request_load(m < 0 ? 0 : m); }
    // ---- top bar
    float tb = px(58);
    ImGui::SetNextWindowPos(ImVec2(x, y)); ImGui::SetNextWindowSize(ImVec2(w, tb));
    ImGui::PushStyleColor(ImGuiCol_WindowBg, IM_COL32(0, 0, 0, 0)); ImGui::PushStyleVar(ImGuiStyleVar_WindowPadding, ImVec2(0, 0));
    ImGui::Begin("##vtop", nullptr, WF | ImGuiWindowFlags_NoScrollbar | ImGuiWindowFlags_NoScrollWithMouse);
    ImGui::PopStyleVar(); ImGui::PopStyleColor();
    {
        ImDrawList* dl = ImGui::GetWindowDrawList();
        float cw = fminf(w - px(32), g_wide ? w - px(32) : px(1100));
        float x0 = x + (w - cw) / 2;
        ImGui::SetCursorScreenPos(ImVec2(x0, y + px(8)));
        if (round_icon("vback", IC_BACK, 42, T.surface2, T.ink, true)) back();
        text_at(dl, f_bold, 21, ImVec2(x0 + px(56), y + px(16)), T.ink, "3D Viewer");
        int mi = pending_load >= 0 ? pending_load : cur;
        bool st = mi >= 0 && store.find(mods[mi].id) && store.find(mods[mi].id)->star;
        ImGui::SetCursorScreenPos(ImVec2(x0 + cw - px(92), y + px(8)));
        if (round_icon("vstar", st ? IC_BOOKMARK_FILL : IC_BOOKMARK, 42, T.surface2, st ? T.amber : T.ink, true) && mi >= 0) {
            Store::Entry& e = store.get(mods[mi].id); e.star = !e.star; store.dirty = true; show_toast(e.star ? "Saved to Bookmarks" : "Removed from Bookmarks");
        }
        ImGui::SameLine(0, px(8));
        if (round_icon("vfull", fullscreen ? IC_COLLAPSE : IC_EXPAND, 42, fullscreen ? T.accent : T.surface2, fullscreen ? IM_COL32_WHITE : T.ink, true)) fullscreen = !fullscreen;
    }
    ImGui::End();
    float y1 = y + tb, ph = h - tb;
    if (cur < 0 && pending_load < 0) return;

    if (fullscreen) {
        page_begin_v("##vfull", x, y1, w, ph, false);
        float cw = w - px(24), x0 = x + px(12);
        ImGui::SetCursorScreenPos(ImVec2(x0, y1 + px(4)));
        segments(*this, cw);
        float sy = ImGui::GetCursorScreenPos().y;
        float sh = y1 + ph - sy - px(56) - inset_bottom;
        ui_stage(x0, sy, cw, sh);
        ImGui::SetCursorScreenPos(ImVec2(x0, sy + sh + px(8)));
        chips_row(*this, cw);
        ImGui::End();
        return;
    }

    if (g_wide) {
        float pw = fminf(px(420), w * 0.4f), lw = w - pw;
        page_begin_v("##vleft", x, y1, lw, ph, false);
        float cw = lw - px(32), x0 = x + px(16);
        ImGui::SetCursorScreenPos(ImVec2(x0, y1 + px(4)));
        header_card(*this, cw);
        ImGui::SetCursorScreenPos(ImVec2(x0, ImGui::GetCursorScreenPos().y));   // keep the column's left edge
        segments(*this, cw);
        float sy = ImGui::GetCursorScreenPos().y;
        float sh = y1 + ph - sy - px(58);
        ui_stage(x0, sy, cw, sh);
        ImGui::SetCursorScreenPos(ImVec2(x0, sy + sh + px(10)));
        chips_row(*this, cw);
        ImGui::End();
        page_begin_v("##vright", x + lw, y1, pw, ph, true);
        ImGuiWindow* page = ImGui::GetCurrentWindow();
        if (page_scroll_reset >= 0) { ImGui::SetScrollY(0); page_scroll_reset = -1; }
        float scroll = ImGui::GetScrollY();
        ImGui::GetWindowDrawList()->AddLine(ImVec2(x + lw, y1), ImVec2(x + lw, y1 + ph), T.border, px(1));
        float rcw = pw - px(32);
        ImGui::SetCursorPos(ImVec2(px(16), px(4)));
        ImGui::BeginChild("##vrcol", ImVec2(rcw, 0), ImGuiChildFlags_AutoResizeY, ImGuiWindowFlags_NoScrollbar | ImGuiWindowFlags_NoScrollWithMouse | ImGuiWindowFlags_NoBackground);
        step_card(*this, rcw);
        if (loaded() && pending_load < 0) {
            tabs_y = ImGui::GetCursorScreenPos().y - page->Pos.y + scroll;
            ui_tabs_bar(rcw, false);
            spacer(10);
            if (!selected.empty()) ui_inspector();
            ui_tab(tab);
        }
        spacer(28);
        ImGui::EndChild();
        static int pin = 0;
        if (scroll_to_tabs) { pin = 4; scroll_to_tabs = false; }
        else if (g_tab_clicked) { if (scroll > tabs_y) pin = 4; g_tab_clicked = false; }
        if (pin > 0) { ImGui::SetScrollY(page, tabs_y); pin--; }
        ImGui::End();
        return;
    }

    // ---- phone: one scrolling page; content in a fixed-width column child so every widget gets the right width
    page_begin_v("##vpage", x, y1, w, ph, true);
    ImGuiWindow* page = ImGui::GetCurrentWindow();
    if (page_scroll_reset >= 0) { ImGui::SetScrollY(page_scroll_reset); page_scroll_reset = -1; }
    float scroll = ImGui::GetScrollY();
    float cw = fminf(w - px(32), px(900)), x0 = (w - cw) / 2;
    ImGui::SetCursorPos(ImVec2(x0, px(2)));
    ImGui::BeginChild("##vcol", ImVec2(cw, 0), ImGuiChildFlags_AutoResizeY, ImGuiWindowFlags_NoScrollbar | ImGuiWindowFlags_NoScrollWithMouse | ImGuiWindowFlags_NoBackground);
    header_card(*this, cw);
    segments(*this, cw);
    float sh = fminf(fmaxf(px(300), ph * 0.56f), cw * 1.25f);
    ImVec2 sp = ImGui::GetCursorScreenPos();
    ui_stage(sp.x, sp.y, cw, sh);
    spacer(10);
    chips_row(*this, cw);
    if (loaded() && pending_load < 0) {
        tabs_y = ImGui::GetCursorScreenPos().y - page->Pos.y + scroll;
        ui_tabs_bar(cw, false);
        spacer(10);
        if (!selected.empty()) ui_inspector();
        ui_tab(tab);
    }
    spacer(28);
    ImGui::EndChild();
    // (repeated for a few frames: the content column resizes one frame after a tab change)
    static int pin = 0;
    if (scroll_to_tabs) { pin = 4; scroll_to_tabs = false; }
    else if (g_tab_clicked) { if (scroll > tabs_y) pin = 4; g_tab_clicked = false; }
    if (pin > 0) { ImGui::SetScrollY(page, tabs_y - px(4)); pin--; }
    ImGui::End();
    // sticky tabs once the tab bar scrolls under the top bar
    if (loaded() && pending_load < 0 && scroll > tabs_y) {
        ImGui::SetNextWindowPos(ImVec2(x, y1)); ImGui::SetNextWindowSize(ImVec2(w, px(52)));
        ImGui::PushStyleColor(ImGuiCol_WindowBg, T.bg); ImGui::PushStyleVar(ImGuiStyleVar_WindowPadding, ImVec2(x0, px(5)));
        ImGui::Begin("##vsticky", nullptr, (WF & ~ImGuiWindowFlags_NoBringToFrontOnFocus) | ImGuiWindowFlags_NoScrollbar | ImGuiWindowFlags_NoScrollWithMouse);
        ImGui::PopStyleVar(); ImGui::PopStyleColor();
        ui_tabs_bar(cw, true);
        ImGui::GetWindowDrawList()->AddLine(ImVec2(x, y1 + px(51)), ImVec2(x + w, y1 + px(51)), T.border, px(1));
        blockers.push({x, y1, x + w, y1 + px(52)});
        ImGui::End();
    }
}

// ------------------------------------------------------------------ tab contents
static void spec_list(const Vec<Str>& k, const Vec<Str>& v, const Vec<int>* missing = nullptr) {
    ImDrawList* dl = ImGui::GetWindowDrawList();
    float cw = ImGui::GetContentRegionAvail().x;
    for (int i = 0; i < k.n; i++) {
        ImVec2 p = ImGui::GetCursorScreenPos();
        float kw = cw * 0.38f, vw = cw - kw - px(10);
        ImVec2 ks = text_size(g_app->f_med, 13, k[i], kw), vs = text_size(g_app->f_body, 13.5f, v[i], vw);
        float rh = fmaxf(ks.y, vs.y) + px(16);
        if (i % 2 == 0) dl->AddRectFilled(p, ImVec2(p.x + cw, p.y + rh), T.surface2, px(8));
        text_at(dl, g_app->f_med, 13, ImVec2(p.x + px(10), p.y + px(8)), T.muted, k[i], kw - px(10));
        bool miss = missing && (*missing)[i];
        text_at(dl, g_app->f_body, 13.5f, ImVec2(p.x + kw + px(10), p.y + px(8)), miss ? T.faint : T.ink, v[i], vw - px(10));
        ImGui::Dummy(ImVec2(cw, rh));
    }
}

static int spec_icon(const char* k) {
    if (strstr(k, "flow") || strstr(k, "capacity")) return IC_DROP;
    if (strstr(k, "head") || strstr(k, "lift") || strstr(k, "height")) return IC_ARROW_UP;
    if (strstr(k, "eff")) return IC_GAUGE;
    if (strstr(k, "press")) return IC_GAUGE;
    if (strstr(k, "power") || strstr(k, "kw") || strstr(k, "voltage")) return IC_BOLT;
    if (strstr(k, "speed") || strstr(k, "rpm")) return IC_ROTATE;
    if (strstr(k, "temp")) return IC_THERMO;
    return IC_RULER;
}

static void key_specs(App& a) {
    const JV& e = a.S()["engineering_parameters"]["parameters"];
    int n = pf_min(e.size(), 3);
    if (!n) return;
    ImDrawList* dl = ImGui::GetWindowDrawList();
    float cw = ImGui::GetContentRegionAvail().x, gap = px(8), bw = (cw - gap * (n - 1)) / n;
    ImVec2 p0 = ImGui::GetCursorScreenPos();
    text_at(dl, a.f_bold, 17, p0, T.ink, "Key Specifications");
    ImGui::Dummy(ImVec2(cw, px(30)));
    p0 = ImGui::GetCursorScreenPos();
    float maxh = 0;
    for (int i = 0; i < n; i++) {
        const JV& v = e[i];
        Str val = Str::f("%s %s", v["typical_range"].text().c(), v["unit"].text().c());
        float hh = px(46) + text_size(a.f_semi, 13, val, bw - px(20)).y + text_size(a.f_med, 11.5f, nice_key(v.key), bw - px(20)).y;
        maxh = fmaxf(maxh, hh);
    }
    for (int i = 0; i < n; i++) {
        const JV& v = e[i];
        ImVec2 a0(p0.x + i * (bw + gap), p0.y), a1(a0.x + bw, a0.y + maxh);
        card_bg(dl, a0, a1, px(14), T.surface);
        dl->AddCircleFilled(ImVec2(a0.x + px(22), a0.y + px(22)), px(14), T.chip, 20);
        draw_icon(dl, spec_icon(v.key), ImVec2(a0.x + px(22), a0.y + px(22)), px(16), T.accent);
        Str key = nice_key(v.key);
        text_at(dl, a.f_med, 11.5f, ImVec2(a0.x + px(10), a0.y + px(42)), T.muted, key, bw - px(20));
        float kh = text_size(a.f_med, 11.5f, key, bw - px(20)).y;
        text_at(dl, a.f_semi, 13, ImVec2(a0.x + px(10), a0.y + px(44) + kh), T.ink, Str::f("%s %s", v["typical_range"].text().c(), v["unit"].text().c()), bw - px(20));
    }
    ImGui::Dummy(ImVec2(cw, maxh + px(4)));
}

static void sub_label(App& a, const char* s, int icon, ImU32 col) {
    ImDrawList* dl = ImGui::GetWindowDrawList();
    ImVec2 p = ImGui::GetCursorScreenPos();
    draw_icon(dl, icon, ImVec2(p.x + px(8), p.y + px(9)), px(14), col);
    text_at(dl, a.f_semi, 12.5f, ImVec2(p.x + px(22), p.y + px(1)), col, s);
    ImGui::Dummy(ImVec2(10, px(22)));
}

void App::ui_tab(int t) {
    const JV& s = S();
    ImDrawList* dl = ImGui::GetWindowDrawList();
    ImGui::PushID(t);
    if (t == TAB_OVERVIEW) {
        const JV& i = s["introduction"];
        key_specs(*this);
        if (i["plant"].isObj()) {                     // Mine-to-Port: where this equipment sits in the reference plant
            const JV& pl = i["plant"];
            card_begin("##plant");
            sub_label(*this, "In the reference plant", IC_FLOW, T.amber);
            int ai = -1; for (int k = 0; k < areas.n; k++) if (areas[k].id.eq(pl["area"].str())) ai = k;
            Vec<Str> k, v;
            if (ai >= 0) { k.push(Str("Area")); v.push(Str::f("%s · %s", areas[ai].id.c(), areas[ai].name.c())); }
            if (pl["tag"].truthy()) { k.push(Str("Tag")); v.push(Str(pl["tag"].str())); }
            if (pl["qty"].truthy()) { k.push(Str("Quantity")); v.push(Str(pl["qty"].str())); }
            spec_list(k, v);
            if (pl["interfaces"].size()) { spacer(4); bullets(pl["interfaces"]); }
            if (ai >= 0) { spacer(4); if (link(Str::f("Open area %s in the Mine-to-Port catalog  ›", areas[ai].id.c()), "goarea")) { cat_coll = 1; m2p_area = ai; page_scroll_reset = 0; go(SCR_CATALOG); } }
            card_end();
        }
        h3("Introduction"); para(i["definition"].str());
        h3("Applications"); bullets(i["applications"]);
        if (i["key_points"].size()) { h3("Key points"); bullets(i["key_points"]); }
        h3("Model configuration");
        { Vec<Str> k, v; for (const JV& c : M()["model_configuration"]) if (!c.isObj() && !c.isArr()) { k.push(nice_key(c.key)); v.push(c.text()); } spec_list(k, v); }
        h3("Standards");
        for (const JV& x : M()["standards"]) {
            ImVec2 p = ImGui::GetCursorScreenPos(); float cw = ImGui::GetContentRegionAvail().x;
            Str rel = Str::f("%s (edition %s)", x["relevance"].str(), x["edition"].text().c());
            ImVec2 idsz = text_size(f_semi, 12.5f, x["id"].str());
            float rh = px(10) + idsz.y + px(4) + text_size(f_body, 13, rel, cw - px(20)).y + px(10);
            card_bg(dl, p, ImVec2(p.x + cw, p.y + rh), px(12), T.surface);
            dl->AddRectFilled(ImVec2(p.x + px(10), p.y + px(9)), ImVec2(p.x + px(18) + idsz.x + px(8), p.y + px(13) + idsz.y), T.chip, px(6));
            text_at(dl, f_semi, 12.5f, ImVec2(p.x + px(14), p.y + px(11)), T.chip_ink, x["id"].str());
            text_at(dl, f_body, 13, ImVec2(p.x + px(10), p.y + px(18) + idsz.y), T.ink, rel, cw - px(20));
            ImGui::Dummy(ImVec2(cw, rh)); spacer(4);
        }
        spacer(8);
        muted(M()["disclaimer"].str(), 12);
    } else if (t == TAB_PARTS) {
        muted("Tap a part to inspect it. The numbers match the markers on the model.", 13);
        spacer(6);
        bool mk = markers; if (checkbox("Keep number markers on in every tab", &mk)) markers = mk;
        spacer(6);
        int pi = 0;
        for (const JV& p : M()["parts"]) {
            ImGui::PushID(pi);
            float rw = ImGui::GetContentRegionAvail().x;
            Str g(p["group"].str()); for (int c = 0; c < g.n; c++) if (g.s[c] == '_') g.s[c] = ' ';
            ImVec2 ns = text_size(f_semi, 14, p["name"].str(), rw - px(80));
            float rh = ns.y + px(36);
            ImVec2 a = ImGui::GetCursorScreenPos();
            if (ImGui::InvisibleButton("##part", ImVec2(rw, rh))) { select(p["id"].str()); scroll_to_tabs = true; }
            bool sel = selected.eq(p["id"].str());
            bool hid = false; for (const Str& hd : hidden) if (hd.eq(p["id"].str())) hid = true;
            card_bg(dl, a, ImVec2(a.x + rw, a.y + rh), px(12), sel ? T.chip : (ImGui::IsItemActive() ? T.surface2 : T.surface), !sel);
            ImVec2 c(a.x + px(22), a.y + rh / 2);
            dl->AddCircleFilled(c, px(12), marker_col(pi), 20);
            Str n = Str::f("%d", pi + 1); ImVec2 ts = text_size(f_bold, 11.5f, n);
            text_at(dl, f_bold, 11.5f, ImVec2(c.x - ts.x / 2, c.y - ts.y / 2), IM_COL32(8, 16, 32, 255), n);
            text_at(dl, f_semi, 14, ImVec2(a.x + px(44), a.y + px(9)), hid ? T.faint : T.ink, p["name"].str(), rw - px(80));
            text_at(dl, f_body, 12, ImVec2(a.x + px(44), a.y + px(13) + ns.y), T.muted, hid ? Str::f("%s · hidden", g.c()).c() : g.c());
            draw_icon(dl, IC_NEXT, ImVec2(a.x + rw - px(18), a.y + rh / 2), px(16), T.muted);
            ImGui::Dummy(ImVec2(1, px(6)));
            ImGui::PopID(); pi++;
        }
        if (!hidden.empty()) { spacer(4); if (tool("Show all parts")) { hidden.clear(); apply_state(); } }
    } else if (t == TAB_WORKING) {
        if (primary(step_idx >= 0 ? "Restart How it works" : "Start How it works", IC_PLAY, false, ImGui::GetContentRegionAvail().x, "hiwgo", 46)) { show_step(0); page_scroll_reset = 0; }
        spacer(6);
        muted("Each step moves the camera, highlights the parts and shows the right overlay. Tap Show or Play on a step.", 12.5f);
        h3("Working principle");
        int n = 0;
        for (const JV& st : s["working_principle"]["steps"]) {
            ImGui::PushID(n);
            ImVec2 p = ImGui::GetCursorScreenPos();
            bool cur_step = n == step_idx;
            dl->AddCircleFilled(ImVec2(p.x + px(13), p.y + px(12)), px(13), cur_step ? T.accent : T.chip, 20);
            Str num = Str::f("%d", n + 1); ImVec2 ts = text_size(f_bold, 12, num);
            text_at(dl, f_bold, 12, ImVec2(p.x + px(13) - ts.x / 2, p.y + px(12) - ts.y / 2), cur_step ? IM_COL32_WHITE : T.chip_ink, num);
            ImGui::Indent(px(36));
            para(st["text"].str());
            bool any = false;
            if (has_part_node(st["part"].str())) { part_btn(*this, st["part"].str(), "Show", "show"); any = true; }
            if (st["overlay"].truthy()) {
                if (any) ImGui::SameLine(0, px(14));
                if (link("Play", "play")) {
                    // web data-step: runAction({cut, operate, overlay, highlight, view})
                    JW w; w.beginObj();
                    if (st.has("cut")) { w.key("cut"); json_write_value(w, st["cut"]); }
                    if (st.has("operate")) { w.key("operate"); json_write_value(w, st["operate"]); }
                    w.key("overlay"); json_write_value(w, st["overlay"]);
                    w.key("highlight"); json_write_value(w, st["part"]);
                    w.key("view").str(st["part"].truthy() ? "part" : "front");
                    w.endObj();
                    JDoc d; if (d.parse(w.o.c(), (size_t)w.o.n)) run_action(*d.root, false);
                    page_scroll_reset = 0;
                }
            }
            ImGui::Unindent(px(36));
            spacer(8);
            ImGui::PopID(); n++;
        }
        if (s["working_principle"]["characteristic_curve"].truthy()) { h3("Characteristic curve"); para(s["working_principle"]["characteristic_curve"].str()); }
        if (M()["overlays"].size()) {
            h3("Teaching overlays");
            const JV& other = s["flow_animation"]["other_overlays"];
            for (const JV& o : M()["overlays"]) {
                ImGui::PushID(o.key);
                card_begin("##ov");
                float iw = ImGui::GetContentRegionAvail().x;
                bool on = overlay_on(o.key);
                ImVec2 p = ImGui::GetCursorScreenPos();
                ImGui::PushTextWrapPos(ImGui::GetCursorPosX() + iw - px(80));
                text(f_semi, 14.5f, T.ink, o["title"].str());
                const char* desc = other[o.key]["description"].truthy() ? other[o.key]["description"].str() : o["description"].str();
                text(f_body, 13, T.muted, desc);
                ImGui::PopTextWrapPos();
                float yb = ImGui::GetCursorScreenPos().y;
                ImGui::SetCursorScreenPos(ImVec2(p.x + iw - px(68), p.y));
                if (tool(on ? "Hide" : "Show", on, px(68), "ovb")) { toggle_overlay(o.key, !on); if (!on) page_scroll_reset = 0; }
                ImGui::SetCursorScreenPos(ImVec2(p.x, fmaxf(yb, ImGui::GetCursorScreenPos().y)));
                ImGui::Dummy(ImVec2(0, 0));
                card_end();
                ImGui::PopID();
            }
        }
    } else if (t == TAB_PARAMS) {
        const JV& e = s["engineering_parameters"];
        key_specs(*this);
        spacer(4);
        {
            ImVec2 p = ImGui::GetCursorScreenPos(); float cw = ImGui::GetContentRegionAvail().x;
            float th = text_size(f_body, 12.5f, e["basis"].str(), cw - px(44)).y + px(20);
            dl->AddRectFilled(p, ImVec2(p.x + cw, p.y + th), T.chip, px(12));
            draw_icon(dl, IC_INFO, ImVec2(p.x + px(18), p.y + px(18)), px(16), T.chip_ink);
            text_at(dl, f_body, 12.5f, ImVec2(p.x + px(34), p.y + px(10)), T.chip_ink, e["basis"].str(), cw - px(44));
            ImGui::Dummy(ImVec2(cw, th));
        }
        h3(e["title"].truthy() ? e["title"].str() : "Design-class ranges");
        {
            float cw = ImGui::GetContentRegionAvail().x; int k = 0;
            auto row = [&](const JV& v) {
                ImVec2 p = ImGui::GetCursorScreenPos();
                Str val = Str::f("%s %s", v["typical_range"].text().c(), v["unit"].text().c());
                float kw = cw * 0.36f, vw = cw - kw - px(14);
                float vh = text_size(f_semi, 13.5f, val, vw).y + (v["note"].truthy() ? text_size(f_body, 12, v["note"].str(), vw).y + px(4) : 0);
                float rh = fmaxf(text_size(f_med, 13, nice_key(v.key), kw - px(12)).y, vh) + px(18);
                if (k++ % 2 == 0) dl->AddRectFilled(p, ImVec2(p.x + cw, p.y + rh), T.surface2, px(8));
                text_at(dl, f_med, 13, ImVec2(p.x + px(10), p.y + px(9)), T.muted, nice_key(v.key), kw - px(12));
                text_at(dl, f_semi, 13.5f, ImVec2(p.x + kw + px(4), p.y + px(9)), T.ink, val, vw);
                if (v["note"].truthy()) text_at(dl, f_body, 12, ImVec2(p.x + kw + px(4), p.y + px(13) + text_size(f_semi, 13.5f, val, vw).y), T.muted, v["note"].str(), vw);
                ImGui::Dummy(ImVec2(cw, rh));
            };
            for (const JV& v : e["parameters"]) row(v);
            for (const JV& v : e["additional"]) row(v);
        }
        if (e["selection_notes"].size()) { h3("Selection notes"); bullets(e["selection_notes"]); }
        h3("Reference model (manufacturer datasheet)");
        const JV& rm = e["reference_model"];
        Vec<Str> k, v; Vec<int> miss;
        k.push(Str("Manufacturer")); v.push(Str(rm["manufacturer"].truthy() ? rm["manufacturer"].str() : "— not set")); miss.push(!rm["manufacturer"].truthy());
        k.push(Str("Model")); v.push(Str(rm["model"].truthy() ? rm["model"].str() : "— not set")); miss.push(!rm["model"].truthy());
        for (const JV& r : rm["rated_point"]) { k.push(nice_key(r.key)); bool nul = r.isNull(); v.push(nul ? Str("to be filled") : r.text()); miss.push(nul); }
        spec_list(k, v, &miss);
        if (rm["status"].truthy()) { spacer(6); muted(rm["status"].str(), 12); }
        muted("Fill in your own datasheet values in the Tools tab.", 12);
        h3("Sources"); bullets(e["sources"]);
    } else if (t == TAB_CARE) {
        const JV& I = s["installation"]; const JV& Mt = s["maintenance"];
        card_begin("##inst");
        text(f_bold, 16, T.ink, strstr(M()["classification"]["family"].str(), "Mining") ? "Assembly & commissioning" : "Installation", false); spacer(4);
        for (const JV& sec : I) {
            if (!sec.isArr()) continue;
            const char* k = sec.key;
            int ic = !strcmp(k, "foundation") ? IC_LAYERS : !strcmp(k, "alignment") ? IC_TARGET : !strcmp(k, "piping") ? IC_FLOW : !strcmp(k, "commissioning") ? IC_CHECK : IC_LIST;
            sub_label(*this, nice_key(k), ic, T.accent); bullets(sec);
        }
        card_end();
        card_begin("##maint");
        text(f_bold, 16, T.ink, "Maintenance", false); spacer(4);
        sub_label(*this, "Routine checks", IC_CLOCK, T.amber); bullets(Mt["routine"]);
        sub_label(*this, "Periodic maintenance", IC_WRENCH, T.amber); bullets(Mt["periodic"]);
        sub_label(*this, "Overhaul", IC_GEAR, T.amber); bullets(Mt["overhaul"]);
        sub_label(*this, "Lubrication", IC_DROP, T.amber); bullets(Mt["lubrication"]);
        card_end();
    } else if (t == TAB_OPERATION) {
        const JV& o = s["operation"];
        muted("How the equipment is operated in the reference plant: controls, checks, start-up, normal running, shut-down, alarms and interlocks. Always follow your site procedures and the OEM manual.", 12.5f);
        spacer(6);
        struct OS { const char* key; const char* title; int icon; } secs[] = {
            {"controls", "Controls & indications", IC_GAUGE}, {"pre_start", "Pre-start checks", IC_LIST}, {"start_up", "Start-up", IC_PLAY},
            {"normal", "Normal operation", IC_ROTATE}, {"shut_down", "Shut-down", IC_STOP}, {"alarms_interlocks", "Alarms & interlocks", IC_ALERT}, {"tips", "Operator tips", IC_SPARK}};
        for (auto& sc : secs) {
            if (!o[sc.key].size()) continue;
            ImGui::PushID(sc.key);
            card_begin("##op");
            sub_label(*this, sc.title, sc.icon, !strcmp(sc.key, "alarms_interlocks") ? T.bad : T.accent);
            bullets(o[sc.key]);
            card_end();
            ImGui::PopID();
        }
    } else if (t == TAB_FAILURES) {
        int n = 0;
        for (const JV& f : s["failure_analysis"]["items"]) {
            ImGui::PushID(n++);
            card_begin("##fa");
            float cw = ImGui::GetContentRegionAvail().x;
            ImDrawList* cdl = ImGui::GetWindowDrawList();
            ImVec2 cs = text_size(f_med, 11, f["category"].str());
            ImVec2 p = ImGui::GetCursorScreenPos();
            cdl->AddCircleFilled(ImVec2(p.x + px(14), p.y + px(12)), px(14), (T.bad & 0x00ffffff) | 0x30000000, 20);
            draw_icon(cdl, IC_ALERT, ImVec2(p.x + px(14), p.y + px(12)), px(16), T.bad);
            ImGui::SetCursorScreenPos(ImVec2(p.x + px(36), p.y + px(2)));
            ImGui::PushTextWrapPos(ImGui::GetCursorPosX() + cw - cs.x - px(60));
            text(f_semi, 15, T.ink, f["problem"].str());
            ImGui::PopTextWrapPos();
            ImVec2 ca(p.x + cw - cs.x - px(16), p.y + px(2));
            cdl->AddRectFilled(ca, ImVec2(ca.x + cs.x + px(16), ca.y + cs.y + px(8)), T.chip, px(10));
            text_at(cdl, f_med, 11, ImVec2(ca.x + px(8), ca.y + px(4)), T.chip_ink, f["category"].str());
            ImGui::SetCursorScreenPos(ImVec2(p.x, ImGui::GetCursorScreenPos().y + px(4)));
            sub_label(*this, "Symptoms", IC_EYE, T.amber); bullets(f["symptoms"]);
            sub_label(*this, "Causes", IC_ALERT, T.bad); bullets(f["causes"]);
            sub_label(*this, "Remedies", IC_WRENCH, T.good); bullets(f["remedies"]);
            part_btn(*this, f["part"].str(), "Show affected part  ›", "aff");
            card_end();
            ImGui::PopID();
        }
    } else if (t == TAB_TOURS) {
        para("Each tour plays on the 3-D model: the camera, cutaway, explode, animation and overlays follow the script, with captions on the model.");
        spacer(6);
        card_begin("##narr");
        {
            float iw = ImGui::GetContentRegionAvail().x;
            ImVec2 p = ImGui::GetCursorScreenPos();
            draw_icon(ImGui::GetWindowDrawList(), IC_SPEAKER, ImVec2(p.x + px(12), p.y + px(14)), px(18), T.accent);
            text_at(ImGui::GetWindowDrawList(), f_semi, 14.5f, ImVec2(p.x + px(32), p.y + px(4)), T.ink, "Read narration aloud");
            ImGui::SetCursorScreenPos(ImVec2(p.x + iw - px(48), p.y));
            bool nar = store.narrate;
            if (toggle("narr", &nar)) { store.narrate = nar; store.dirty = true; if (!nar) plat::stop_speaking(); }
            ImGui::SetCursorScreenPos(ImVec2(p.x, p.y + px(32)));
            if (!plat::tts_available()) muted("Text-to-speech is not available on this device; captions still show.", 12);
            else muted("Uses Android text-to-speech.", 12);
        }
        card_end();
        int n = 0;
        for (const JV& v : s["video_tutorials"]) {
            ImGui::PushID(n);
            card_begin("##tour");
            float cw = ImGui::GetContentRegionAvail().x;
            const char* title = v["title"].str(); const char* sep = strstr(title, " — ");
            Str tt(sep ? sep + strlen(" — ") : title);
            bool running = tour_n == n;
            ImVec2 p = ImGui::GetCursorScreenPos();
            ImDrawList* cdl = ImGui::GetWindowDrawList();
            ImGui::SetCursorScreenPos(ImVec2(p.x + cw - px(46), p.y));
            if (round_icon("tp", running ? IC_STOP : IC_PLAY, 46, running ? T.bad : T.accent, IM_COL32_WHITE)) { if (running) stop_tour(); else { play_tour(n); page_scroll_reset = 0; } }
            ImGui::SetCursorScreenPos(p);
            ImGui::PushTextWrapPos(ImGui::GetCursorPosX() + cw - px(60));
            text(f_semi, 15, T.ink, tt);
            double mins = round(v["duration_s"].n() / 60 * 10) / 10;
            text(f_body, 12.5f, T.muted, Str::f("%d scenes · %s min%s", v["script"].size(), fmt_num(mins).c(), running ? Str::f(" · playing %d/%d", tour_i + 1, v["script"].size()).c() : ""));
            ImGui::PopTextWrapPos();
            if (running) progress(cdl, ImGui::GetCursorScreenPos(), cw - px(60), px(4), (float)(tour_i + 1) / pf_max(1, v["script"].size()), T.accent, T.line), spacer(8);
            ImGui::SetCursorScreenPos(ImVec2(p.x, fmaxf(ImGui::GetCursorScreenPos().y, p.y + px(48))));
            ImGui::Dummy(ImVec2(0, 0));
            card_end();
            ImGui::PopID(); n++;
        }
    } else if (t == TAB_QUIZ) {
        const JV& Qs = s["assessment"]["questions"];
        int done = 0, right = 0;
        for (int i = 0; i < Qs.size() && i < quiz.n; i++) if (quiz[i] >= 0) { done++; if ((int)Qs[i]["answer"].n(-1) == quiz[i]) right++; }
        {
            ImVec2 p = ImGui::GetCursorScreenPos(); float cw = ImGui::GetContentRegionAvail().x, hh = px(78);
            grad_rect(dl, p, ImVec2(p.x + cw, p.y + hh), px(16), T.dark ? IM_COL32(0x16, 0x36, 0x75, 255) : IM_COL32(0xe0, 0xeb, 0xff, 255), T.dark ? IM_COL32(0x0b, 0x19, 0x38, 255) : IM_COL32(0xf7, 0xfa, 0xff, 255));
            ImVec2 c(p.x + px(40), p.y + hh / 2); float f = Qs.size() ? (float)done / Qs.size() : 0;
            dl->AddCircle(c, px(24), T.line, 40, px(5));
            if (f > 0) { dl->PathArcTo(c, px(24), -(float)M_PI / 2, -(float)M_PI / 2 + 2 * (float)M_PI * f, 40); dl->PathStroke(T.amber, px(5)); }
            Str sc = done ? Str::f("%d/%d", right, done) : Str::f("%d", Qs.size()); ImVec2 ts = text_size(f_bold, 13, sc);
            text_at(dl, f_bold, 13, ImVec2(c.x - ts.x / 2, c.y - ts.y / 2), T.ink, sc);
            Str l1 = done == Qs.size() && done ? Str::f("Score %d %%", (int)round(100.0 * right / Qs.size())) : (done ? Str::f("%d of %d answered", done, Qs.size()) : Str::f("%d questions", Qs.size()));
            text_at(dl, f_bold, 17, ImVec2(p.x + px(78), p.y + px(16)), T.ink, l1);
            const Store::Entry* se = store.find(mods[cur].id);
            Str l2 = Str::f("Pass mark %s %%%s", s["assessment"]["pass_mark_pct"].text().c(), se && se->prog.best >= 0 ? Str::f(" · best %d %%", se->prog.best).c() : "");
            text_at(dl, f_body, 13, ImVec2(p.x + px(78), p.y + px(44)), T.muted, l2);
            ImGui::Dummy(ImVec2(cw, hh)); spacer(8);
        }
        for (int i = 0; i < Qs.size(); i++) {
            const JV& q = Qs[i]; int a = i < quiz.n ? quiz[i] : -1; int ans = (int)q["answer"].n(-1);
            ImGui::PushID(i);
            card_begin("##q");
            text(f_semi, 14.5f, T.ink, Str::f("%d. %s", i + 1, q["question"].str()));
            spacer(4);
            int j = 0;
            ImDrawList* cdl = ImGui::GetWindowDrawList();
            for (const JV& o : q["options"]) {
                ImGui::PushID(j);
                float rw = ImGui::GetContentRegionAvail().x;
                ImVec2 ts = text_size(f_body, 14, o.str(), rw - px(46));
                ImVec2 p = ImGui::GetCursorScreenPos(); float rh = ts.y + px(20);
                bool click = ImGui::InvisibleButton("##o", ImVec2(rw, rh));
                if (click && a < 0) {
                    quiz[i] = j; a = j;
                    if (q["part"].truthy() && has_part_node(q["part"].str())) flash(q["part"].str(), plat::now());
                    // all answered -> best score into progress (web: setProg best if higher)
                    int d2 = 0, r2 = 0; for (int k = 0; k < Qs.size(); k++) if (quiz[k] >= 0) { d2++; if ((int)Qs[k]["answer"].n(-1) == quiz[k]) r2++; }
                    if (d2 == Qs.size() && d2) { int sc = (int)round(100.0 * r2 / d2); Store::Entry& se = store.get(mods[cur].id); if (sc > se.prog.best) { se.prog.best = sc; store.dirty = true; } show_toast(Str::f("Quiz complete: %d %%", sc)); }
                }
                bool chosen = a == j, correct = j == ans;
                ImU32 bgc = T.surface2, brc = T.border, fg = T.ink;
                if (a >= 0 && correct) { bgc = (T.good & 0x00ffffff) | 0x26000000; brc = T.good; }
                else if (a >= 0 && chosen) { bgc = (T.bad & 0x00ffffff) | 0x26000000; brc = T.bad; }
                else if (ImGui::IsItemActive()) bgc = T.chip;
                cdl->AddRectFilled(p, ImVec2(p.x + rw, p.y + rh), bgc, px(12)); cdl->AddRect(p, ImVec2(p.x + rw, p.y + rh), brc, px(12), px(1));
                ImVec2 c(p.x + px(18), p.y + rh / 2);
                if (a >= 0 && correct) { cdl->AddCircleFilled(c, px(9), T.good, 20); draw_icon(cdl, IC_CHECK, c, px(12), IM_COL32_WHITE); }
                else if (a >= 0 && chosen) { cdl->AddCircleFilled(c, px(9), T.bad, 20); draw_icon(cdl, IC_CLOSE, c, px(11), IM_COL32_WHITE); }
                else cdl->AddCircle(c, px(8), T.faint, 20, px(1.5f));
                text_at(cdl, f_body, 14, ImVec2(p.x + px(36), p.y + px(10)), fg, o.str(), rw - px(46));
                ImGui::Dummy(ImVec2(1, px(4)));
                ImGui::PopID(); j++;
            }
            if (a >= 0) {
                spacer(2);
                text(f_semi, 13, a == ans ? T.good : T.bad, a == ans ? "Correct." : "Not quite.", false);
                text(f_body, 13, T.muted, q["explanation"].str());
                part_btn(*this, q["part"].str(), "Show in 3-D  ›", "q3d");
            }
            card_end();
            ImGui::PopID();
        }
        if (done && tool("Reset quiz")) { for (int& x : quiz) x = -1; }
    } else if (t == TAB_TOOLS) {
        ui_tools();
    }
    ImGui::PopID();
}

// ------------------------------------------------------------------ part inspector
void App::ui_inspector() {
    int pi = part_index(selected);
    if (pi < 0) { selected.clear(); return; }
    const JV& p = M()["parts"][pi];
    const JV& c = M()["components"][p["info_ref"].str()];
    ImGui::PushID("insp");
    ImGui::PushStyleColor(ImGuiCol_Border, T.accent);
    card_begin("##insp", 14);
    ImGui::PopStyleColor();
    float iw = ImGui::GetContentRegionAvail().x;
    ImDrawList* dl = ImGui::GetWindowDrawList();
    ImVec2 p0 = ImGui::GetCursorScreenPos();
    dl->AddCircleFilled(ImVec2(p0.x + px(14), p0.y + px(14)), px(14), marker_col(pi), 20);
    Str n = Str::f("%d", pi + 1); ImVec2 ns = text_size(f_bold, 12, n);
    text_at(dl, f_bold, 12, ImVec2(p0.x + px(14) - ns.x / 2, p0.y + px(14) - ns.y / 2), IM_COL32(8, 16, 32, 255), n);
    text_at(dl, f_semi, 11.5f, ImVec2(p0.x + px(36), p0.y + px(6)), T.amber, "PART DETAILS");
    ImGui::SetCursorScreenPos(ImVec2(p0.x + iw - px(36), p0.y - px(4)));
    if (round_icon("ix", IC_CLOSE, 36, T.surface2, T.ink)) { select(nullptr); card_end(); ImGui::PopID(); return; }
    ImGui::SetCursorScreenPos(ImVec2(p0.x, p0.y + px(36)));
    h2(p["name"].str());
    chips_begin();
    { Str g(p["group"].str()); for (int i = 0; i < g.n; i++) if (g.s[i] == '_') g.s[i] = ' '; chip(g); }
    chip(p["id"].str());
    chips_end();
    if (p["link"].truthy()) {                         // area/site models: jump to the detailed equipment model
        int li = mod_index(p["link"].str());
        if (li >= 0) {
            spacer(4);
            if (primary("Open detailed 3D model", IC_CUBE, false, iw, "olink", 44)) { Str l(p["link"].str()); select(nullptr); card_end(); ImGui::PopID(); open_module(mod_index(l)); return; }
            spacer(4);
        }
    }
    auto txt = [&](const char* title, const JV& v) { const char* t = v.str(); if (*t && strcmp(t, "—") && strcmp(t, "-")) { h3(title); para(t); } };
    txt("Function", c["function"]);
    txt("Construction", c["construction"]);
    txt("Typical materials", c["material"]);
    txt("Operating conditions", c["operating_conditions"]);
    if (c["failure_modes"].size()) { h3("Common failure modes"); bullets(c["failure_modes"]); }
    if (c["inspection"].size()) { h3("Inspection"); bullets(c["inspection"]); }
    if (p["note"].truthy()) { spacer(6); muted(p["note"].str(), 12); }
    spacer(10);
    float x0 = ImGui::GetCursorPosX();
    auto flow = [&](const char* l) { float w = text_size(f_med, 13, l).x + px(50); if (ImGui::GetCursorPosX() > x0 + 1) { ImGui::SameLine(0, px(8)); if (ImGui::GetCursorPosX() + w > x0 + iw) ImGui::NewLine(); } };
    flow("Isolate"); if (pill("Isolate", false, IC_TARGET, "iso")) { hidden.clear(); for (const JV& q : M()["parts"]) if (!streq(q["id"].str(), selected)) hidden.push(Str(q["id"].str())); apply_state(); frame_part(selected); page_scroll_reset = 0; }
    flow("Hide part"); if (pill("Hide part", false, IC_EYE, "hide")) { hidden.push(Str(selected)); apply_state(); }
    flow("Show all"); if (pill("Show all", false, IC_LAYERS, "all")) { hidden.clear(); apply_state(); }
    flow("Zoom to part"); if (pill("Zoom to part", false, IC_SEARCH, "zoom")) { frame_part(selected); page_scroll_reset = 0; }
    card_end();
    ImGui::PopID();
    spacer(6);
}

// ------------------------------------------------------------------ calculators, compare, tools tab
void App::calc_card(const Calc& c, bool collapsible) {
    ImGui::PushID(c.key);
    int off = 0; bool found = false;
    for (int i = 0; i < calc_keys.n; i++) { const Calc* ci = calc_find(calc_keys[i]); if (calc_keys[i].eq(c.key)) { found = true; break; } off += ci ? ci->nf : 0; }
    if (!found) { off = calc_vals.n; calc_keys.push(Str(c.key)); for (int i = 0; i < c.nf; i++) calc_vals.push(c.f[i].def); }
    bool open = !collapsible || calc_open.eq(c.key);
    card_begin("##calc");
    float cw = ImGui::GetContentRegionAvail().x;
    ImDrawList* dl = ImGui::GetWindowDrawList();
    {
        ImVec2 p = ImGui::GetCursorScreenPos();
        float th = text_size(f_semi, 14.5f, c.title, cw - px(70)).y;
        if (collapsible) { if (ImGui::InvisibleButton("##hdr", ImVec2(cw, fmaxf(th, px(28))))) calc_open = open ? Str() : Str(c.key); }
        else ImGui::Dummy(ImVec2(cw, fmaxf(th, px(28))));
        dl->AddCircleFilled(ImVec2(p.x + px(14), p.y + px(13)), px(14), T.chip, 20);
        draw_icon(dl, IC_CALC, ImVec2(p.x + px(14), p.y + px(13)), px(15), T.accent);
        text_at(dl, f_semi, 14.5f, ImVec2(p.x + px(36), p.y + px(3)), T.ink, c.title, cw - px(70));
        if (collapsible) draw_icon(dl, open ? IC_CHEV_DOWN : IC_NEXT, ImVec2(p.x + cw - px(12), p.y + px(13)), px(16), T.muted);
    }
    if (open) {
        spacer(6);
        double v[8];
        for (int i = 0; i < c.nf; i++) {
            ImGui::PushID(i);
            v[i] = calc_vals[off + i];
            float fw = px(116);
            ImVec2 ls = text_size(f_body, 13, c.f[i].label, cw - fw - px(8));
            float y0 = ImGui::GetCursorPosY();
            ImGui::PushTextWrapPos(ImGui::GetCursorPosX() + cw - fw - px(8));
            ImGui::SetCursorPosY(y0 + fmaxf(0, (px(40) - ls.y) / 2));
            text(f_body, 13, T.ink, c.f[i].label);
            ImGui::PopTextWrapPos();
            float y1 = ImGui::GetCursorPosY();
            ImGui::SetCursorPos(ImVec2(ImGui::GetCursorPosX() + cw - fw, y0));
            Str val = fmt_num(v[i]);
            if (field("in", val, "", fw)) { Str k = Str::f("%s:%d", c.key, i); begin_text(5, k, c.f[i].label, val, plat::NUMBER); }
            ImGui::SetCursorPosY(fmaxf(y1, y0 + px(46)));
            ImGui::PopID();
        }
        Str out = c.run(v);
        ImVec2 os = text_size(f_monom, 13, out, cw - px(24));
        ImVec2 a = ImGui::GetCursorScreenPos();
        ImGui::Dummy(ImVec2(cw, os.y + px(20)));
        dl->AddRectFilled(a, ImVec2(a.x + cw, a.y + os.y + px(20)), T.chip, px(10));
        dl->AddRectFilled(a, ImVec2(a.x + px(4), a.y + os.y + px(20)), T.accent, px(2));
        text_at(dl, f_monom, 13, ImVec2(a.x + px(14), a.y + px(10)), T.chip_ink, out, cw - px(24));
    }
    card_end();
    ImGui::PopID();
}

void App::ui_compare(int ia, int ib, const JV& la, const JV& lb) {
    const JV& ea = la["sections"]["engineering_parameters"]; const JV& eb = lb["sections"]["engineering_parameters"];
    Vec<Str> keys2;
    auto addk = [&](const JV& o) { for (const JV& k : o) { bool hv = false; for (Str& x : keys2) if (x.eq(k.key)) hv = true; if (!hv) keys2.push(Str(k.key)); } };
    addk(ea["parameters"]); addk(ea["additional"]); addk(eb["parameters"]); addk(eb["additional"]);
    // web: Object.assign({}, parameters, additional) -> 'additional' wins on duplicate keys
    auto cell = [](const JV& e, const char* k) -> Str { const JV& v = e["additional"].has(k) ? e["additional"][k] : e["parameters"][k]; if (!v.isObj()) return Str("—"); return Str::f("%s %s", v["typical_range"].text().c(), v["unit"].text().c()); };
    ImDrawList* dl = ImGui::GetWindowDrawList();
    float cw = ImGui::GetContentRegionAvail().x, kw = cw * 0.28f, vw = (cw - kw) / 2;
    auto row = [&](const char* k, const char* va, const char* vb, bool head, int idx) {
        ImFont* fv = head ? f_semi : f_body;
        float rh = fmaxf(fmaxf(text_size(f_med, 12.5f, k, kw - px(10)).y, text_size(fv, 12.5f, va, vw - px(10)).y), text_size(fv, 12.5f, vb, vw - px(10)).y) + px(14);
        ImVec2 p = ImGui::GetCursorScreenPos();
        if (head) dl->AddRectFilled(p, ImVec2(p.x + cw, p.y + rh), T.chip, px(8));
        else if (idx % 2 == 0) dl->AddRectFilled(p, ImVec2(p.x + cw, p.y + rh), T.surface2, px(8));
        text_at(dl, f_med, 12.5f, ImVec2(p.x + px(8), p.y + px(7)), T.muted, k, kw - px(10));
        text_at(dl, fv, 12.5f, ImVec2(p.x + kw, p.y + px(7)), head ? T.chip_ink : T.ink, va, vw - px(10));
        text_at(dl, fv, 12.5f, ImVec2(p.x + kw + vw, p.y + px(7)), head ? T.chip_ink : T.ink, vb, vw - px(10));
        ImGui::Dummy(ImVec2(cw, rh));
    };
    row("", la["title"].str(), lb["title"].str(), true, 0);
    int k = 0;
    for (Str& key : keys2) row(nice_key(key), cell(ea, key), cell(eb, key), false, k++);
    auto kp = [](const JV& a) { Str r; int i = 0; for (const JV& x : a) { if (i++) r.add("; "); r.add(x.str()); } return r; };
    row("Key points", kp(la["sections"]["introduction"]["key_points"]), kp(lb["sections"]["introduction"]["key_points"]), false, k++);
    (void)ia; (void)ib;
}

void App::ui_tools() {
    const JV& s = S();
    muted("Tools for engineers and subject-matter experts. Calculations are simplified textbook relations — verify against the relevant standards before design decisions.", 12.5f);
    h3("Engineering calculators");
    Vec<const char*> keys; calc_keys_for(mods[cur].id, s["introduction"]["hi_family"].str(), keys);
    for (const char* k : keys) if (const Calc* c = calc_find(k)) calc_card(*c, false);
    if (link(more_calcs ? "Hide other calculators" : Str::f("More calculators (%d)", NCALCS - keys.n).c(), "more")) more_calcs = !more_calcs;
    if (more_calcs) for (int i = 0; i < NCALCS; i++) { bool in = false; for (const char* k : keys) if (streq(k, CALCS[i].key)) in = true; if (!in) calc_card(CALCS[i], true); }

    // ---- reference datasheet (your data): reference_model merged with the device copy
    h3("Reference datasheet (your data)");
    Store::Entry& se = store.get(mods[cur].id);
    const JV& rm = s["engineering_parameters"]["reference_model"];
    if (!se.ds.set) {
        // initial values exactly as the web: Object.assign({}, reference_model, ds) / rated_point
        se.ds.manufacturer = rm["manufacturer"].text(); se.ds.model = rm["model"].text();
        se.ds.keys.clear(); se.ds.vals.clear();
        for (const JV& r : rm["rated_point"]) { se.ds.keys.push(Str(r.key)); se.ds.vals.push(r.text()); }
    } else {
        for (const JV& r : rm["rated_point"]) { bool have = false; for (Str& k : se.ds.keys) if (k.eq(r.key)) have = true; if (!have) { se.ds.keys.push(Str(r.key)); se.ds.vals.push(r.text()); } }
    }
    card_begin("##ds");
    {
        float cw = ImGui::GetContentRegionAvail().x, fw = cw * 0.56f;
        auto row = [&](const char* label, const char* val, const char* key) {
            ImGui::PushID(key);
            float y0 = ImGui::GetCursorPosY();
            ImGui::SetCursorPosY(y0 + px(11)); text(f_body, 13, T.ink, label, false);
            ImGui::SetCursorPos(ImVec2(ImGui::GetCursorPosX() + cw - fw, y0));
            if (field("f", val, "—", fw)) begin_text(4, key, label, val, plat::TEXT);
            ImGui::SetCursorPosY(y0 + px(46));
            ImGui::PopID();
        };
        row("Manufacturer", se.ds.manufacturer, "manufacturer");
        row("Model", se.ds.model, "model");
        for (int i = 0; i < se.ds.keys.n; i++) row(nice_key(se.ds.keys[i]), se.ds.vals[i], Str::f("rp:%s", se.ds.keys[i].c()));
        spacer(4);
        if (pill("Copy as JSON", false, IC_LIST, "copy")) {
            // same text as the web: JSON.stringify({ pump_id, reference_model: { rated_point, manufacturer, model } }, null, 1)
            auto q = [](const char* v) { JW j; j.str_(v); return j.o; };
            se.ds.set = true; store.dirty = true;
            Str o = Str::f("{\n \"pump_id\": %s,\n \"reference_model\": {\n  \"rated_point\": ", q(mods[cur].id).c());
            if (!se.ds.keys.n) o.add("{}");
            else { o.add("{\n"); for (int i = 0; i < se.ds.keys.n; i++) o.addf("   %s: %s%s\n", q(se.ds.keys[i]).c(), q(se.ds.vals[i]).c(), i + 1 < se.ds.keys.n ? "," : ""); o.add("  }"); }
            o.addf(",\n  \"manufacturer\": %s,\n  \"model\": %s\n }\n}", q(se.ds.manufacturer).c(), q(se.ds.model).c());
            plat::copy_to_clipboard(o); ds_msg = "Copied to clipboard."; show_toast("Datasheet copied as JSON");
        }
        ImGui::SameLine(0, px(10)); ImGui::SetCursorPosY(ImGui::GetCursorPosY() + px(9));
        muted(ds_msg.empty() ? "Saved on this device." : ds_msg.c(), 12);
    }
    card_end();

    // ---- notes
    h3("Notes");
    {
        float cw = ImGui::GetContentRegionAvail().x;
        const char* nt = se.notes.c();
        const char* ph = "Site observations, settings, lessons learned…";
        ImVec2 ts = text_size(f_body, 13.5f, *nt ? nt : ph, cw - px(24));
        float hgt = fmaxf(px(110), ts.y + px(24));
        ImVec2 a = ImGui::GetCursorScreenPos();
        if (ImGui::InvisibleButton("##notes", ImVec2(cw, hgt))) begin_text(3, "", "Notes", se.notes, plat::MULTILINE);
        ImDrawList* dl = ImGui::GetWindowDrawList();
        dl->AddRectFilled(a, ImVec2(a.x + cw, a.y + hgt), T.field, px(12)); dl->AddRect(a, ImVec2(a.x + cw, a.y + hgt), T.border, px(12), px(1));
        text_at(dl, f_body, 13.5f, ImVec2(a.x + px(12), a.y + px(12)), *nt ? T.ink : T.faint, *nt ? nt : ph, cw - px(24));
    }

    // ---- compare
    h3("Compare with another item");
    {
        float cw = ImGui::GetContentRegionAvail().x;
        Str lbl = cmp_mod >= 0 ? Str::f("%s  %s", mods[cmp_mod].eq_id.empty() ? Str::f("#%d", mods[cmp_mod].no).c() : mods[cmp_mod].eq_id.c(), mods[cmp_mod].title.c()) : Str();
        if (field("cmp", lbl, "Choose a model…", cw, IC_SCALES, 46)) { picker_mode = 1; picker_open = true; }
        if (cmp_mod >= 0 && cmp_learn.root) { spacer(6); ui_compare(cur, cmp_mod, *learn.root, *cmp_learn.root); }
    }

    // ---- model tools
    h3("Model tools");
    if (pill("Measure distance", measuring, IC_RULER, "meas2")) { measuring = !measuring; clear_measure(); if (measuring) page_scroll_reset = 0; }
    ImGui::SameLine(0, px(8));
    if (pill("Show all parts", false, IC_LAYERS, "sall")) { hidden.clear(); apply_state(); }
}

void viewer_cam_touched(bool v) { g_cam_touched = v; }
