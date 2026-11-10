// App shell and main screens: Home, Catalog, Bookmarks, More (+ learning paths, compare, calculators, training,
// settings, help, about), bottom navigation, module picker, text entry and toasts.
#include "ui.h"
#include "calcs.h"
#include <stdio.h>

using namespace ui;

extern const ImGuiWindowFlags WF;
const ImGuiWindowFlags WF = ImGuiWindowFlags_NoDecoration | ImGuiWindowFlags_NoMove | ImGuiWindowFlags_NoSavedSettings |
                            ImGuiWindowFlags_NoFocusOnAppearing | ImGuiWindowFlags_NoNav | ImGuiWindowFlags_NoBringToFrontOnFocus;
bool g_wide = false;
static const char* VERSION = "2.1.0";

// representative model per department (live thumbnails on the category cards)
static const char* DEPT_REP[] = {"three_way_valve", "end_suction_centrifugal_pump", "steam_turbine", "air_cooled_heat_exchanger", "jaw_crusher",
                                 "spray_dryer", "decanter_centrifuge", "digestion_autoclave", "clariflocculator", "gear_assembly", "flare_stack"};
static const char* FEATURED[] = {"horizontal_multistage_pump", "vertical_turbine_pump", "slurry_pump", "steam_turbine", "rotary_screw_compressor", "jaw_crusher"};

Str dept_label(const App& a, int d) { return d >= 0 && d < a.depts.n ? Str::f("%d. %s", d + 1, a.depts[d].name.c()) : Str(); }
static int dept_rep(const App& a, int d) {
    if (d >= 0 && d < (int)(sizeof DEPT_REP / sizeof DEPT_REP[0])) { int i = a.mod_index(DEPT_REP[d]); if (i >= 0) return i; }
    for (int i = 0; i < a.mods.n; i++) if (a.mods[i].dept == d) return i;
    return -1;
}
static Str sub_line(const ModInfo& m) {
    Str s; if (!m.eq_id.empty()) s.add(m.eq_id);
    Str sc = !m.subcategory.empty() ? m.subcategory : (!m.category.empty() ? m.category : Str::f("Phase %d", m.phase));
    if (!s.empty()) s.add(" · "); s.add(sc);
    return s;
}

// full-screen page window (transparent: the screen background shows through)
static void page_begin(const char* id, float x, float y, float w, float h, bool scroll = true) {
    ImGui::SetNextWindowPos(ImVec2(x, y)); ImGui::SetNextWindowSize(ImVec2(w, h));
    ImGui::PushStyleColor(ImGuiCol_WindowBg, IM_COL32(0, 0, 0, 0));
    ImGui::PushStyleVar(ImGuiStyleVar_WindowPadding, ImVec2(0, 0));
    ImGui::Begin(id, nullptr, WF | ImGuiWindowFlags_NoScrollWithMouse | (scroll ? 0 : ImGuiWindowFlags_NoScrollbar));
    ImGui::PopStyleVar(); ImGui::PopStyleColor();
}
// centred content column with side padding
static float column(float w, float maxw = 1100) {
    float cw = fminf(w - px(32), px(maxw));
    ImGui::SetCursorPosX((w - cw) / 2);
    return cw;
}
static void indent_to(float w, float cw) { ImGui::SetCursorPosX((w - cw) / 2); }

// thumbnail tile: department gradient + live model render (spinner until ready)
void thumb_tile(App& a, ImDrawList* dl, int mod, ImVec2 p0, ImVec2 p1, float r, bool gradient) {
    int d = a.mods[mod].dept;
    if (!ImGui::IsRectVisible(p0, p1)) return;   // off-screen rows never queue a thumbnail render
    if (gradient) grad_rect(dl, p0, p1, r, dept_color(d, 0), dept_color(d, 1));
    unsigned tex = a.thumb(mod);
    float w = p1.x - p0.x, h = p1.y - p0.y;
    if (tex) {
        // keep the 4:3 thumbnail aspect, centred
        float tw = w, th = w * 0.75f; if (th > h) { th = h; tw = h / 0.75f; }
        ImVec2 c((p0.x + p1.x) / 2, (p0.y + p1.y) / 2);
        image(dl, tex, ImVec2(c.x - tw / 2, c.y - th / 2), ImVec2(c.x + tw / 2, c.y + th / 2), 0, true);
    } else spinner(dl, ImVec2((p0.x + p1.x) / 2, (p0.y + p1.y) / 2), fminf(w, h) * 0.08f, IM_COL32(255, 255, 255, 120), plat::now());
}

// ================================================================== root
void App::build_ui(float dt) {
    (void)dt;
    float W = (float)fbw, H = (float)fbh;
    g_wide = W / dp >= 860;
    ImDrawList* bg = ImGui::GetBackgroundDrawList();
    // screen background: navy gradient with a soft blue glow (light theme: pale blue-grey)
    bg->AddRectFilledMultiColor(ImVec2(0, 0), ImVec2(W, H), T.bg, T.bg, T.bg2, T.bg2);
    if (T.dark) for (int i = 6; i >= 1; i--) bg->AddCircleFilled(ImVec2(W * 0.85f, H * 0.12f), W * 0.12f * i, IM_COL32(0x2f, 0x7c, 0xff, 5), 48);
    stage_visible = false; blockers.clear(); hero_wanted = false;
    bool nav = !(screen == SCR_VIEWER && fullscreen);
    float navh = nav ? px(66) + inset_bottom : inset_bottom;
    float y0 = inset_top, ch = H - inset_top - navh;
    switch (screen) {
        case SCR_HOME: ui_home(0, y0, W, ch); break;
        case SCR_CATALOG: ui_catalog(0, y0, W, ch); break;
        case SCR_BOOKMARKS: ui_bookmarks(0, y0, W, ch); break;
        case SCR_MORE: if (more_page) ui_more_page(0, y0, W, ch); else ui_more(0, y0, W, ch); break;
        case SCR_VIEWER: ui_viewer(0, y0, W, ch); break;
    }
    if (nav) ui_nav(0, H - navh, W, navh);
    if (inset_top > 0) ImGui::GetForegroundDrawList()->AddRectFilled(ImVec2(0, 0), ImVec2(W, inset_top), T.bg);
    if (picker_open) ui_picker();
    if (toast_on) {
        ImDrawList* fg = ImGui::GetForegroundDrawList();
        ImVec2 ts = text_size(f_med, 14, toast);
        ImVec2 c(W / 2, H - navh - px(40));
        ImVec2 a(c.x - ts.x / 2 - px(18), c.y - ts.y / 2 - px(11)), b(c.x + ts.x / 2 + px(18), c.y + ts.y / 2 + px(11));
        fg->AddRectFilled(a, b, T.overlay_bg, px(22)); fg->AddRect(a, b, T.border, px(22), px(1));
        text_at(fg, f_med, 14, ImVec2(c.x - ts.x / 2, c.y - ts.y / 2), IM_COL32_WHITE, toast);
    }
}

void App::go(int scr) {
    if (scr == screen) return;
    nav_stack.push(screen);
    if (nav_stack.n > 24) nav_stack.erase(0);
    screen = scr;
    page_scroll_reset = 0;
}
void App::open_module(int idx, int t) {
    if (idx < 0 || idx >= mods.n) return;
    if (idx != cur) request_load(idx);
    if (t >= 0) { tab = t; scroll_to_tabs = true; }
    fullscreen = false;
    go(SCR_VIEWER);
}

// ================================================================== bottom navigation (Home, Catalog, 3-D viewer, Bookmarks, More)
void App::ui_nav(float x, float y, float w, float h) {
    ImGui::SetNextWindowPos(ImVec2(x, y - px(22))); ImGui::SetNextWindowSize(ImVec2(w, h + px(22)));
    ImGui::PushStyleColor(ImGuiCol_WindowBg, IM_COL32(0, 0, 0, 0));
    ImGui::PushStyleVar(ImGuiStyleVar_WindowPadding, ImVec2(0, 0));
    ImGui::Begin("##nav", nullptr, WF | ImGuiWindowFlags_NoScrollbar | ImGuiWindowFlags_NoScrollWithMouse);
    ImGui::PopStyleVar(); ImGui::PopStyleColor();
    ImDrawList* dl = ImGui::GetWindowDrawList();
    float top = y;
    dl->AddRectFilled(ImVec2(x, top), ImVec2(x + w, y + h), T.nav_bg);
    dl->AddLine(ImVec2(x, top), ImVec2(x + w, top), T.border, px(1));
    struct It { int scr; int icon; const char* label; } items[] = {{SCR_HOME, IC_HOME, "Home"}, {SCR_CATALOG, IC_GRID, "Catalog"}, {SCR_VIEWER, IC_CUBE, "3D Viewer"},
                                                                {SCR_BOOKMARKS, IC_BOOKMARK, "Bookmarks"}, {SCR_MORE, IC_DOTS, "More"}};
    float iw = fminf(w, px(560)) / 5, x0 = x + (w - iw * 5) / 2;
    for (int i = 0; i < 5; i++) {
        bool active = screen == items[i].scr;
        float cx = x0 + iw * (i + 0.5f);
        ImGui::PushID(i);
        if (i == 2) {
            // raised centre button
            float r = px(28);
            ImVec2 c(cx, top + px(6));
            ImGui::SetCursorScreenPos(ImVec2(cx - r, c.y - r));
            bool click = ImGui::InvisibleButton("##fab", ImVec2(2 * r, 2 * r + px(30)));
            for (int k = 4; k >= 1; k--) dl->AddCircleFilled(c, r + px(2.5f) * k, IM_COL32(0x2f, 0x7c, 0xff, (int)(T.dark ? 22 : 14)), 40);
            dl->AddCircleFilled(c, r + px(3), T.nav_bg, 40);
            int v0 = dl->VtxBuffer.Size; dl->AddCircleFilled(c, r, IM_COL32_WHITE, 40);
            ImGui::ShadeVertsLinearColorGradientKeepAlpha(dl, v0, dl->VtxBuffer.Size, ImVec2(c.x, c.y - r), ImVec2(c.x, c.y + r), IM_COL32(0x4d, 0x95, 0xff, 255), IM_COL32(0x16, 0x4f, 0xd8, 255));
            if (active) dl->AddCircle(c, r + px(1.5f), IM_COL32(255, 255, 255, 160), 40, px(2));
            draw_icon(dl, IC_CUBE, c, r * 0.95f, IM_COL32_WHITE);
            ImVec2 ts = text_size(f_med, 11.5f, items[i].label);
            text_at(dl, f_med, 11.5f, ImVec2(cx - ts.x / 2, top + px(40)), active ? T.accent : T.muted, items[i].label);
            if (click) {
                if (screen == SCR_VIEWER) { /* already here */ }
                else { int m = cur >= 0 ? cur : mod_index(store.last); if (m < 0) m = mod_index(FEATURED[0]); open_module(m < 0 ? 0 : m); }
            }
        } else {
            ImGui::SetCursorScreenPos(ImVec2(cx - iw / 2, top));
            bool click = ImGui::InvisibleButton("##n", ImVec2(iw, h - inset_bottom));
            ImU32 col = active ? T.accent : T.muted;
            int ic = items[i].icon; if (i == 3 && active) ic = IC_BOOKMARK_FILL;
            draw_icon(dl, ic, ImVec2(cx, top + px(22)), px(22), col);
            ImVec2 ts = text_size(f_med, 11.5f, items[i].label);
            text_at(dl, active ? f_semi : f_med, 11.5f, ImVec2(cx - ts.x / 2, top + px(40)), col, items[i].label);
            if (active) dl->AddRectFilled(ImVec2(cx - px(14), top + px(1)), ImVec2(cx + px(14), top + px(4)), T.accent, px(2));
            if (click) {
                if (items[i].scr == SCR_MORE) more_page = MP_NONE;
                if (screen != items[i].scr) { nav_stack.clear(); screen = items[i].scr; page_scroll_reset = 0; }
                else page_scroll_reset = 0;   // tapping the current tab scrolls to the top
            }
        }
        ImGui::PopID();
    }
    ImGui::End();
}

// ================================================================== Home
void App::ui_home(float x, float y, float w, float h) {
    page_begin("##home", x, y, w, h);
    if (page_scroll_reset >= 0) { ImGui::SetScrollY(page_scroll_reset); page_scroll_reset = -1; }
    ImDrawList* dl = ImGui::GetWindowDrawList();
    spacer(14);
    float cw = column(w);
    float xL = ImGui::GetCursorScreenPos().x;
    // ---- brand row
    {
        ImVec2 p = ImGui::GetCursorScreenPos();
        logo(dl, ImVec2(p.x + px(22), p.y + px(24)), px(21));
        ImVec2 ps = text_size(f_bold, 25, "Pump");
        text_at(dl, f_bold, 25, ImVec2(p.x + px(54), p.y + px(4)), T.ink, "Pump");
        text_at(dl, f_bold, 25, ImVec2(p.x + px(54) + ps.x, p.y + px(4)), T.amber, "Forge");
        text_at(dl, f_med, 12.5f, ImVec2(p.x + px(55), p.y + px(34)), T.muted, "Explore · Learn · Apply");
        ImGui::SetCursorScreenPos(ImVec2(p.x + cw - px(92), p.y + px(4)));
        if (round_icon("hsearch", IC_SEARCH, 42, T.surface2, T.ink, true)) { go(SCR_CATALOG); cat_query.clear(); begin_text(2, "", "Search equipment", "", plat::TEXT); }
        ImGui::SameLine(0, px(8));
        if (round_icon("hset", IC_GEAR, 42, T.surface2, T.ink, true)) { more_page = MP_SETTINGS; go(SCR_MORE); }
        ImGui::SetCursorScreenPos(ImVec2(p.x, p.y + px(58)));
    }
    spacer(10);
    // ---- hero: live rotating model
    {
        indent_to(w, cw);
        ImVec2 a = ImGui::GetCursorScreenPos();
        float hh = g_wide ? px(340) : fminf(px(330), cw * 0.95f);
        ImGui::Dummy(ImVec2(cw, hh));
        ImVec2 b(a.x + cw, a.y + hh);
        glow(dl, a, b, px(22), T.glow, px(6));
        grad_rect(dl, a, b, px(22), T.dark ? IM_COL32(0x13, 0x2f, 0x66, 255) : IM_COL32(0xdc, 0xe8, 0xff, 255), T.dark ? IM_COL32(0x08, 0x14, 0x30, 255) : IM_COL32(0xf6, 0xf9, 0xff, 255));
        dl->AddRect(a, b, T.border, px(22), px(1));
        // blueprint grid
        dl->PushClipRect(a, b, true);
        ImU32 gl = T.dark ? IM_COL32(0x4d, 0x8f, 0xff, 18) : IM_COL32(0x1f, 0x63, 0xe0, 16);
        for (float gx = a.x + px(20); gx < b.x; gx += px(26)) dl->AddLine(ImVec2(gx, a.y), ImVec2(gx, b.y), gl, px(1));
        for (float gy = a.y + px(20); gy < b.y; gy += px(26)) dl->AddLine(ImVec2(a.x, gy), ImVec2(b.x, gy), gl, px(1));
        // model area: right side on wide, lower right on phones
        float mw = g_wide ? cw * 0.55f : cw * 0.92f, mh = g_wide ? hh * 0.92f : hh * 0.62f;
        ImVec2 m0(b.x - mw - px(4), b.y - mh - (g_wide ? hh * 0.04f : px(4))), m1(m0.x + mw, m0.y + mh);
        hero_wanted = true;
        if (hero_mod < 0) { hero_mod = mod_index("end_suction_centrifugal_pump"); if (hero_mod < 0) hero_mod = 0; }
        int tw = pf_max(64, (int)mw), th = pf_max(48, (int)mh);
        if (gl_ready) R.target_ensure(hero_rt, tw, th);
        if (hero && hero_rt.tex) image(dl, hero_rt.tex, m0, m1, 0, true);
        else spinner(dl, ImVec2((m0.x + m1.x) / 2, (m0.y + m1.y) / 2), px(14), T.muted, plat::now());
        // 360 arc under the model
        ImVec2 ac((m0.x + m1.x) / 2, m1.y - px(58));
        dl->PathArcTo(ac, px(52), 0.35f, 2.8f, 24); dl->PathStroke(T.dark ? IM_COL32(255, 255, 255, 150) : T.muted, px(1.5f));
        ImVec2 ts = text_size(f_bold, 14, "360°"); ImVec2 lc(ac.x, ac.y + px(52));
        dl->AddRectFilled(ImVec2(lc.x - ts.x / 2 - px(8), lc.y - px(10)), ImVec2(lc.x + ts.x / 2 + px(8), lc.y + px(12)), T.dark ? IM_COL32(0x08, 0x14, 0x30, 230) : IM_COL32(255, 255, 255, 230), px(8));
        text_at(dl, f_bold, 14, ImVec2(lc.x - ts.x / 2, lc.y - px(9)), T.ink, "360°");
        dl->PopClipRect();
        // copy
        float tx = a.x + px(20), ty = a.y + px(20);
        float tsz = g_wide ? 34 : 27;
        text_at(dl, f_bold, tsz, ImVec2(tx, ty), T.ink, "Explore");
        float ew = text_size(f_bold, tsz, "Explore ").x;
        text_at(dl, f_bold, tsz, ImVec2(tx + ew, ty), T.amber, "3D");
        float dw = text_size(f_bold, tsz, "3D ").x;
        text_at(dl, f_bold, tsz, ImVec2(tx + ew + dw, ty), T.ink, "Models of");
        text_at(dl, f_bold, tsz, ImVec2(tx, ty + px(tsz * 1.2f)), T.ink, "Industrial Equipment");
        text_at(dl, f_semi, 16, ImVec2(tx, ty + px(tsz * 2.5f)), T.dark ? IM_COL32(0x8f, 0xb8, 0xff, 255) : T.accent, "Learn. Interact. Master.");
        ImGui::SetCursorScreenPos(ImVec2(tx, g_wide ? b.y - px(72) : ty + px(tsz * 2.5f) + px(30)));
        if (primary("Start Exploring", IC_ARROW_RIGHT, true, 0, "hero_go", 44)) go(SCR_CATALOG);
        ImGui::SetCursorScreenPos(ImVec2(a.x, b.y));
        ImGui::Dummy(ImVec2(1, 1));
    }
    spacer(14);
    // ---- feature stats
    {
        int opened = 0; for (const Store::Entry& e : store.e) if (e.prog.seen > 0) opened++;
        struct S { int icon; Str a; const char* b; ImU32 col; } st[4] = {
            {IC_CUBE, Str::f("%d", mods.n), "3D models", T.accent}, {IC_ROTATE, Str("Interactive"), "Orbit · cut · explode", IM_COL32(0x41, 0xd1, 0xf0, 255)},
            {IC_INFO, Str("Detailed"), "13 lesson sections", IM_COL32(0x4f, 0xe0, 0xa0, 255)}, {IC_BOOK, Str::f("%d opened", opened), "Your learning", T.amber}};
        int cols = g_wide ? 4 : 2;
        float gap = px(10), bw = (cw - gap * (cols - 1)) / cols, bh = px(64);
        for (int i = 0; i < 4; i++) {
            if (i % cols == 0) indent_to(w, cw); else ImGui::SameLine(0, gap);
            ImVec2 a = ImGui::GetCursorScreenPos();
            ImGui::PushID(i);
            bool click = ImGui::InvisibleButton("##st", ImVec2(bw, bh));
            ImGui::PopID();
            card_bg(dl, a, ImVec2(a.x + bw, a.y + bh), px(14), T.surface);
            dl->AddCircleFilled(ImVec2(a.x + px(28), a.y + bh / 2), px(18), (st[i].col & 0x00ffffff) | 0x26000000, 28);
            draw_icon(dl, st[i].icon, ImVec2(a.x + px(28), a.y + bh / 2), px(20), st[i].col);
            text_clipped(dl, f_bold, 15, ImVec2(a.x + px(54), a.y + px(13)), bw - px(60), T.ink, st[i].a);
            text_clipped(dl, f_body, 12, ImVec2(a.x + px(54), a.y + px(34)), bw - px(60), T.muted, st[i].b);
            if (click) { if (i == 3) { bm_tab = 2; go(SCR_BOOKMARKS); } else go(SCR_CATALOG); }
        }
        spacer(8);
    }
    // ---- continue learning
    int last = mod_index(store.last);
    if (last >= 0) {
        spacer(8); indent_to(w, cw);
        ImVec2 a = ImGui::GetCursorScreenPos(); float hh = px(92);
        bool click = ImGui::InvisibleButton("##cont", ImVec2(cw, hh));
        ImVec2 b(a.x + cw, a.y + hh);
        card_bg(dl, a, b, px(16), T.surface);
        thumb_tile(*this, dl, last, ImVec2(a.x + px(10), a.y + px(10)), ImVec2(a.x + px(106), b.y - px(10)), px(12), true);
        float tx = a.x + px(118), tw = cw - px(118) - px(60);
        text_at(dl, f_semi, 11.5f, ImVec2(tx, a.y + px(12)), T.amber, "CONTINUE LEARNING");
        text_clipped(dl, f_bold, 16, ImVec2(tx, a.y + px(30)), tw, T.ink, mods[last].title);
        const Store::Entry* e = store.find(mods[last].id);
        Str sub = Str::f("Module %d · %s", mods[last].no, mods[last].department.c());
        text_clipped(dl, f_body, 12.5f, ImVec2(tx, a.y + px(52)), tw, T.muted, sub);
        if (e && e->prog.best >= 0) text_at(dl, f_med, 12, ImVec2(tx, a.y + px(70)), e->prog.best >= 70 ? T.good : T.amber, Str::f("Quiz best %d %%", e->prog.best));
        dl->AddCircleFilled(ImVec2(b.x - px(32), a.y + hh / 2), px(20), T.accent, 32);
        draw_icon(dl, IC_PLAY, ImVec2(b.x - px(30), a.y + hh / 2), px(18), IM_COL32_WHITE);
        if (click) open_module(last);
        spacer(6);
    }
    // ---- browse by category
    spacer(10); indent_to(w, cw);
    if (section_header("Browse by Category", "View All")) { cat_dept = -1; cat_query.clear(); cat_saved = false; go(SCR_CATALOG); }
    {
        indent_to(w, cw);
        float cardw = g_wide ? px(150) : px(124), cardh = cardw * 1.22f;
        ImGui::PushStyleVar(ImGuiStyleVar_ItemSpacing, ImVec2(px(10), 0));
        ImGui::BeginChild("##cats", ImVec2(cw, cardh + px(4)), 0, ImGuiWindowFlags_HorizontalScrollbar | ImGuiWindowFlags_NoScrollbar | ImGuiWindowFlags_NoScrollWithMouse);
        ImDrawList* cdl = ImGui::GetWindowDrawList();
        for (int d = 0; d < depts.n; d++) {
            if (!depts[d].modules) continue;
            if (d) ImGui::SameLine();
            ImGui::PushID(d);
            ImVec2 a = ImGui::GetCursorScreenPos();
            bool click = ImGui::InvisibleButton("##c", ImVec2(cardw, cardh));
            ImVec2 b(a.x + cardw, a.y + cardh);
            grad_rect(cdl, a, b, px(16), dept_color(d, 0), dept_color(d, 1));
            cdl->AddRect(a, b, (dept_color(d, 2) & 0x00ffffff) | 0x55000000, px(16), px(1));
            int rep = dept_rep(*this, d);
            if (rep >= 0) thumb_tile(*this, cdl, rep, ImVec2(a.x + px(6), a.y + px(8)), ImVec2(b.x - px(6), a.y + cardh * 0.62f), 0, false);
            ImU32 tc = T.dark ? IM_COL32_WHITE : T.ink;
            text_at(cdl, f_semi, 13.5f, ImVec2(a.x + px(10), a.y + cardh * 0.66f), tc, depts[d].name, cardw - px(18));
            text_at(cdl, f_med, 11.5f, ImVec2(a.x + px(10), b.y - px(22)), (dept_color(d, 2) & 0x00ffffff) | 0xff000000, Str::f("%d models", depts[d].modules));
            if (click) { cat_dept = d; cat_query.clear(); cat_saved = false; go(SCR_CATALOG); }
            ImGui::PopID();
        }
        ImGui::EndChild();
        ImGui::PopStyleVar();
    }
    // ---- featured equipment carousel
    spacer(16); indent_to(w, cw);
    {
        ImVec2 p = ImGui::GetCursorScreenPos();
        star(dl, ImVec2(p.x + px(10), p.y + px(14)), px(10), T.amber, true);
        text_at(dl, f_bold, 19, ImVec2(p.x + px(28), p.y + px(1)), T.ink, "Featured Equipment");
        ImGui::Dummy(ImVec2(cw, px(36)));
    }
    if (!featured.n) {
        for (const char* id : FEATURED) {
            int i = mod_index(id); if (i < 0) continue;
            featured.push(i);
            Vec<uint8_t> b; JDoc d; Str desc;
            if (plat::read_asset(Str::f("learning/%s.json", id), b) && d.parse((const char*)b.d, (size_t)b.n)) desc = (*d.root)["sections"]["introduction"]["definition"].str();
            featured_desc.push(desc);
        }
    }
    if (featured.n) {
        indent_to(w, cw);
        float fh = g_wide ? px(230) : px(250);
        ImGui::PushStyleVar(ImGuiStyleVar_ItemSpacing, ImVec2(0, 0));
        ImGui::BeginChild("##feat", ImVec2(cw, fh), 0, ImGuiWindowFlags_HorizontalScrollbar | ImGuiWindowFlags_NoScrollbar | ImGuiWindowFlags_NoScrollWithMouse);
        ImGuiWindow* fw = ImGui::GetCurrentWindow();
        ImDrawList* fdl = ImGui::GetWindowDrawList();
        ImVec2 origin = ImGui::GetCursorScreenPos();
        for (int k = 0; k < featured.n; k++) {
            int i = featured[k];
            ImGui::PushID(k);
            ImGui::SetCursorScreenPos(ImVec2(origin.x + k * cw, origin.y));
            ImVec2 a = ImGui::GetCursorScreenPos();
            ImGui::Dummy(ImVec2(cw, fh));
            ImVec2 b(a.x + cw - px(2), a.y + fh - px(2));
            grad_rect(fdl, a, b, px(18), T.dark ? IM_COL32(0x15, 0x33, 0x70, 255) : IM_COL32(0xe3, 0xed, 0xff, 255), T.dark ? IM_COL32(0x0a, 0x18, 0x36, 255) : IM_COL32(0xfa, 0xfc, 0xff, 255));
            fdl->AddRect(a, b, T.border, px(18), px(1));
            float iw = (b.x - a.x) * 0.44f;
            thumb_tile(*this, fdl, i, ImVec2(a.x + px(6), a.y + px(16)), ImVec2(a.x + iw, b.y - px(16)), 0, false);
            float tx = a.x + iw + px(8), tw = b.x - tx - px(14);
            text_at(fdl, f_bold, 19, ImVec2(tx, a.y + px(18)), T.ink, mods[i].title, tw);
            float th = text_size(f_bold, 19, mods[i].title, tw).y;
            text_clipped(fdl, f_body, 13, ImVec2(tx, a.y + px(24) + th), tw, T.muted, featured_desc[k], g_wide ? 4 : 4);
            // tags
            float cy = b.y - px(98);
            Str tags[2] = {mods[i].department, mods[i].subcategory.empty() ? mods[i].category : mods[i].subcategory};
            float cx = tx;
            for (int t = 0; t < 2; t++) {
                ImVec2 ts = text_size(f_med, 11.5f, tags[t]);
                if (cx + ts.x + px(18) > b.x - px(10)) break;
                fdl->AddRectFilled(ImVec2(cx, cy), ImVec2(cx + ts.x + px(18), cy + px(24)), T.chip, px(12));
                text_at(fdl, f_med, 11.5f, ImVec2(cx + px(9), cy + px(5)), T.chip_ink, tags[t]);
                cx += ts.x + px(24);
            }
            ImGui::SetCursorScreenPos(ImVec2(tx, b.y - px(58)));
            if (primary("Explore Model", IC_ARROW_RIGHT, false, 0, "fx", 40)) open_module(i);
            ImGui::PopID();
        }
        // paging: snap to the nearest card after a swipe, auto-advance every 7 s
        static bool dragging = false; static double last_move = 0; static float target = 0;
        float pw = cw;
        if (scroll_drag && scroll_win == fw) { dragging = true; last_move = plat::now(); }
        else if (dragging && !ptrs.n) {
            dragging = false;
            float v = scroll_win == fw ? scroll_vx : 0;
            int pg = (int)floorf((fw->Scroll.x - v * 0.25f) / pw + 0.5f);
            feat_idx = pf_clamp(pg, 0, featured.n - 1); target = feat_idx * pw;
            if (scroll_win == fw) { scroll_vx = 0; scroll_win = nullptr; }
            last_move = plat::now();
        } else if (!dragging) {
            if (plat::now() - last_move > 7.0) { feat_idx = (feat_idx + 1) % featured.n; last_move = plat::now(); }
            target = feat_idx * pw;
            float cur_x = fw->Scroll.x;
            if (fabsf(cur_x - target) > 0.5f) ImGui::SetScrollX(fw, cur_x + (target - cur_x) * fminf(1.f, ImGui::GetIO().DeltaTime * 10));
        }
        ImGui::EndChild();
        ImGui::PopStyleVar();
        // dots
        indent_to(w, cw);
        ImVec2 p = ImGui::GetCursorScreenPos();
        float dw = featured.n * px(16);
        for (int k = 0; k < featured.n; k++) dl->AddCircleFilled(ImVec2(p.x + (cw - dw) / 2 + px(8) + k * px(16), p.y + px(12)), px(k == feat_idx ? 4.5f : 3.5f), k == feat_idx ? T.accent : T.faint, 16);
        ImGui::Dummy(ImVec2(cw, px(24)));
    }
    // ---- quick access
    spacer(8); indent_to(w, cw);
    section_header("Quick Access");
    {
        struct Q { int icon; const char* t; const char* s; ImU32 col; } q[4] = {
            {IC_CUBE, "View All Models", "282 in 11 departments", T.accent}, {IC_CAP, "Learning Paths", "Department by department", IM_COL32(0xa9, 0x96, 0xff, 255)},
            {IC_CLOCK, "Recently Viewed", "Pick up where you left", IM_COL32(0x41, 0xd1, 0xf0, 255)}, {IC_STAR, "My Favorites", "Your bookmarks", T.amber}};
        int cols = g_wide ? 4 : 2;
        float gap = px(10), bw = (cw - gap * (cols - 1)) / cols, bh = px(76);
        for (int i = 0; i < 4; i++) {
            if (i % cols == 0) indent_to(w, cw); else ImGui::SameLine(0, gap);
            ImVec2 a = ImGui::GetCursorScreenPos();
            ImGui::PushID(100 + i);
            bool click = ImGui::InvisibleButton("##q", ImVec2(bw, bh));
            ImGui::PopID();
            card_bg(dl, a, ImVec2(a.x + bw, a.y + bh), px(14), ImGui::IsItemActive() ? T.surface2 : T.surface);
            draw_icon(dl, q[i].icon, ImVec2(a.x + px(26), a.y + px(26)), px(24), q[i].col);
            text_clipped(dl, f_semi, 14, ImVec2(a.x + px(14), a.y + px(44)), bw - px(20), T.ink, q[i].t);
            text_clipped(dl, f_body, 11.5f, ImVec2(a.x + px(48), a.y + px(18)), bw - px(54), T.muted, q[i].s);
            if (click) {
                if (i == 0) { cat_dept = -1; cat_query.clear(); cat_saved = false; go(SCR_CATALOG); }
                else if (i == 1) { more_page = MP_PATHS; go(SCR_MORE); }
                else { bm_tab = i == 2 ? 1 : 0; go(SCR_BOOKMARKS); }
            }
            if (i % cols == cols - 1) spacer(4);
        }
    }
    spacer(16); indent_to(w, cw);
    ImGui::PushTextWrapPos(ImGui::GetCursorPosX() + cw);
    muted("Educational models with typical design-class data. Verify against manufacturer datasheets and the relevant standards before engineering decisions.", 11.5f);
    ImGui::PopTextWrapPos();
    spacer(24);
    (void)xL;
    ImGui::End();
}

// ================================================================== Catalog
static bool mod_match(const ModInfo& x, const Vec<Str>& words) { for (const Str& w : words) if (!strstr(x.hay, w)) return false; return true; }

static void module_card(App& a, ImDrawList* dl, int i, float cw, float ch) {
    const ModInfo& m = a.mods[i];
    ImGui::PushID(i);
    ImVec2 p = ImGui::GetCursorScreenPos();
    bool click = ImGui::InvisibleButton("##m", ImVec2(cw, ch));
    bool held = ImGui::IsItemActive();
    ImVec2 q(p.x + cw, p.y + ch);
    card_bg(dl, p, q, px(16), held ? T.surface2 : T.surface);
    float ih = ch * 0.56f;
    thumb_tile(a, dl, i, ImVec2(p.x + px(6), p.y + px(6)), ImVec2(q.x - px(6), p.y + ih), px(12), true);
    text_at(dl, a.f_monom, 11, ImVec2(p.x + px(14), p.y + px(12)), IM_COL32(255, 255, 255, 210), Str::f("#%d", m.no));
    const Store::Entry* e = a.store.find(m.id);
    bool starred = e && e->star;
    // bookmark toggle
    ImVec2 bc(q.x - px(26), p.y + px(26));
    ImGui::SetCursorScreenPos(ImVec2(bc.x - px(18), bc.y - px(18)));
    if (ImGui::InvisibleButton("##bm", ImVec2(px(36), px(36)))) { Store::Entry& se = a.store.get(m.id); se.star = !se.star; a.store.dirty = true; a.show_toast(se.star ? "Bookmarked" : "Bookmark removed"); click = false; }
    dl->AddCircleFilled(bc, px(15), IM_COL32(0, 0, 0, 90), 24);
    draw_icon(dl, starred ? IC_BOOKMARK_FILL : IC_BOOKMARK, bc, px(16), starred ? T.amber : IM_COL32_WHITE);
    float tx = p.x + px(12), tw = cw - px(24);
    text_at(dl, a.f_semi, 14, ImVec2(tx, p.y + ih + px(8)), T.ink, m.title, tw);
    float th = text_size(a.f_semi, 14, m.title, tw).y;
    text_clipped(dl, a.f_body, 11.5f, ImVec2(tx, p.y + ih + px(12) + th), tw, T.muted, sub_line(m));
    // badges
    float bx = tx, by = q.y - px(26);
    if (e && e->prog.seen > 0) { dl->AddRectFilled(ImVec2(bx, by), ImVec2(bx + px(56), by + px(18)), (T.good & 0x00ffffff) | 0x30000000, px(9)); text_at(dl, a.f_med, 10.5f, ImVec2(bx + px(8), by + px(2)), T.good, "opened"); bx += px(62); }
    if (e && e->prog.best >= 0) { Str s = Str::f("quiz %d%%", e->prog.best); ImVec2 ts = text_size(a.f_med, 10.5f, s); ImU32 c = e->prog.best >= 70 ? T.good : T.amber;
        dl->AddRectFilled(ImVec2(bx, by), ImVec2(bx + ts.x + px(16), by + px(18)), (c & 0x00ffffff) | 0x30000000, px(9)); text_at(dl, a.f_med, 10.5f, ImVec2(bx + px(8), by + px(2)), c, s); }
    if (m.flagship) star(dl, ImVec2(q.x - px(16), by + px(9)), px(7), T.amber, true);
    ImGui::SetCursorScreenPos(p); ImGui::Dummy(ImVec2(cw, ch));
    if (click) a.open_module(i);
    ImGui::PopID();
}

void App::ui_catalog(float x, float y, float w, float h) {
    page_begin("##catalog", x, y, w, h);
    if (page_scroll_reset >= 0) { ImGui::SetScrollY(page_scroll_reset); page_scroll_reset = -1; }
    ImDrawList* dl = ImGui::GetWindowDrawList();
    spacer(14);
    float cw = column(w);
    {
        ImVec2 p = ImGui::GetCursorScreenPos();
        if (nav_stack.n) { ImGui::SetCursorScreenPos(p); if (round_icon("cback", IC_BACK, 40, T.surface2, T.ink, true)) back(); ImGui::SetCursorScreenPos(ImVec2(p.x + px(52), p.y)); }
        ImVec2 q = ImGui::GetCursorScreenPos();
        text_at(dl, f_bold, 30, q, T.ink, cat_dept >= 0 ? depts[cat_dept].name.c() : "Catalog");
        text_at(dl, f_body, 14, ImVec2(q.x, q.y + px(40)), T.muted, cat_dept >= 0 ? Str::f("Department %d · %d models", cat_dept + 1, depts[cat_dept].modules).c() : Str::f("Explore %d 3D models", mods.n).c());
        ImGui::SetCursorScreenPos(ImVec2(p.x, p.y + px(70)));
    }
    indent_to(w, cw);
    if (field("csearch", cat_query, "Search by name, EQ number, component…", cw, IC_SEARCH, 46)) begin_text(2, "", "Search equipment", cat_query, plat::TEXT);
    if (!cat_query.empty()) {
        ImVec2 r = ImGui::GetItemRectMax();
        ImGui::SetCursorScreenPos(ImVec2(r.x - px(42), r.y - px(43)));
        if (round_icon("cclr", IC_CLOSE, 40, 0, T.muted)) cat_query.clear();
        ImGui::SetCursorScreenPos(ImVec2(r.x - cw, r.y)); ImGui::Dummy(ImVec2(1, 1));
    }
    spacer(10);
    // filter chips
    indent_to(w, cw);
    ImGui::PushStyleVar(ImGuiStyleVar_ItemSpacing, ImVec2(px(8), 0));
    ImGui::BeginChild("##cchips", ImVec2(cw, px(38)), 0, ImGuiWindowFlags_HorizontalScrollbar | ImGuiWindowFlags_NoScrollbar | ImGuiWindowFlags_NoScrollWithMouse);
    if (pill("All", cat_dept < 0 && !cat_saved, 0, "all")) { cat_dept = -1; cat_saved = false; }
    ImGui::SameLine(); if (pill("Saved", cat_saved, IC_BOOKMARK, "saved")) { cat_saved = !cat_saved; }
    for (int d = 0; d < depts.n; d++) if (depts[d].modules) {
        ImGui::SameLine();
        ImGui::PushID(d);
        if (pill(depts[d].name, cat_dept == d, 0, "d")) cat_dept = cat_dept == d ? -1 : d;
        if (cat_dept == d && ImGui::IsWindowAppearing()) ImGui::SetScrollHereX(0.5f);
        ImGui::PopID();
    }
    ImGui::EndChild();
    ImGui::PopStyleVar();
    spacer(12);
    Str q(cat_query); str_lower(q);
    Vec<Str> words; { const char* s = q.c(); while (*s) { while (*s == ' ') s++; const char* e = s; while (*e && *e != ' ') e++; if (e > s) words.push(Str(s, (int)(e - s))); s = e; } }
    int cols = g_wide ? (w / dp > 1200 ? 5 : 4) : 2;
    float gap = px(12);
    if (words.empty() && cat_dept < 0 && !cat_saved) {
        // department grid
        float bw = (cw - gap * (cols - 1)) / cols, bh = bw * 1.08f;
        int k = 0;
        for (int d = 0; d < depts.n; d++) {
            if (k % cols == 0) indent_to(w, cw); else ImGui::SameLine(0, gap);
            ImGui::PushID(d);
            ImVec2 a = ImGui::GetCursorScreenPos();
            bool future = depts[d].modules == 0;
            bool click = ImGui::InvisibleButton("##dc", ImVec2(bw, bh));
            ImVec2 b(a.x + bw, a.y + bh);
            grad_rect(dl, a, b, px(18), dept_color(future ? 11 : d, 0), dept_color(future ? 11 : d, 1));
            dl->AddRect(a, b, (dept_color(d, 2) & 0x00ffffff) | 0x50000000, px(18), px(1));
            if (ImGui::IsItemActive()) dl->AddRectFilled(a, b, IM_COL32(255, 255, 255, 20), px(18));
            int rep = future ? -1 : dept_rep(*this, d);
            if (rep >= 0) thumb_tile(*this, dl, rep, ImVec2(a.x + px(6), a.y + px(6)), ImVec2(b.x - px(6), a.y + bh * 0.62f), 0, false);
            else draw_icon(dl, IC_GAUGE, ImVec2((a.x + b.x) / 2, a.y + bh * 0.33f), bw * 0.3f, IM_COL32(255, 255, 255, 110));
            ImU32 tc = T.dark ? IM_COL32_WHITE : T.ink;
            text_at(dl, f_bold, 15, ImVec2(a.x + px(14), a.y + bh * 0.64f), tc, depts[d].name, bw - px(24));
            Str sub = future ? Str("Coming soon") : Str::f("%d Models  ›", depts[d].modules);
            text_at(dl, f_med, 12, ImVec2(a.x + px(14), b.y - px(26)), future ? T.muted : ((dept_color(d, 2) & 0x00ffffff) | 0xff000000), sub);
            text_at(dl, f_monom, 11, ImVec2(a.x + px(14), a.y + px(12)), T.dark ? IM_COL32(255, 255, 255, 170) : ((dept_color(d, 2) & 0x00ffffff) | 0xb0000000), Str::f("%02d", d + 1));
            if (click && !future) { cat_dept = d; page_scroll_reset = 0; }
            ImGui::PopID();
            k++;
            if (k % cols == 0) spacer(gap / dp);
        }
        if (k % cols) spacer(gap / dp);
    } else {
        // module cards (grouped by department when browsing everything)
        float bw = (cw - gap * (cols - 1)) / cols, bh = bw * 1.2f;
        int k = 0, shown = 0, last_dept = -2;
        for (int i = 0; i < mods.n; i++) {
            const ModInfo& m = mods[i];
            if (cat_dept >= 0 && m.dept != cat_dept) continue;
            if (cat_saved) { const Store::Entry* e = store.find(m.id); if (!(e && e->star)) continue; }
            if (!mod_match(m, words)) continue;
            if (m.dept != last_dept && cat_dept < 0) {
                if (k % cols) spacer(gap / dp);
                k = 0; last_dept = m.dept;
                spacer(6); indent_to(w, cw);
                ImVec2 p = ImGui::GetCursorScreenPos();
                text_at(dl, f_bold, 16, p, T.ink, dept_label(*this, m.dept));
                ImGui::Dummy(ImVec2(cw, px(30)));
            }
            if (k % cols == 0) indent_to(w, cw); else ImGui::SameLine(0, gap);
            module_card(*this, dl, i, bw, bh);
            k++; shown++;
            if (k % cols == 0) spacer(gap / dp);
        }
        if (k % cols) spacer(gap / dp);
        if (!shown) {
            spacer(30); indent_to(w, cw);
            ImVec2 p = ImGui::GetCursorScreenPos();
            draw_icon(dl, cat_saved ? IC_BOOKMARK : IC_SEARCH, ImVec2(p.x + cw / 2, p.y + px(24)), px(40), T.faint);
            const char* msg = cat_saved ? "No bookmarks yet" : "No matches";
            ImVec2 ts = text_size(f_semi, 16, msg); text_at(dl, f_semi, 16, ImVec2(p.x + (cw - ts.x) / 2, p.y + px(58)), T.ink, msg);
            const char* m2 = cat_saved ? "Tap the bookmark on any model to save it here." : "Try another name, EQ number or component.";
            ImVec2 t2 = text_size(f_body, 13, m2); text_at(dl, f_body, 13, ImVec2(p.x + (cw - t2.x) / 2, p.y + px(84)), T.muted, m2);
            ImGui::Dummy(ImVec2(cw, px(110)));
        }
    }
    spacer(24);
    ImGui::End();
}

// ================================================================== Bookmarks
void App::ui_bookmarks(float x, float y, float w, float h) {
    page_begin("##bookmarks", x, y, w, h);
    if (page_scroll_reset >= 0) { ImGui::SetScrollY(page_scroll_reset); page_scroll_reset = -1; }
    ImDrawList* dl = ImGui::GetWindowDrawList();
    spacer(14);
    float cw = column(w, 900);
    { ImVec2 p = ImGui::GetCursorScreenPos(); text_at(dl, f_bold, 30, p, T.ink, "Bookmarks"); text_at(dl, f_semi, 16, ImVec2(p.x, p.y + px(42)), T.muted, "Your saved models"); ImGui::Dummy(ImVec2(cw, px(72))); }
    Vec<int> list;
    int nstar = 0; for (const ModInfo& m : mods) { const Store::Entry* e = store.find(m.id); if (e && e->star) nstar++; }
    indent_to(w, cw);
    ImGui::PushStyleVar(ImGuiStyleVar_ItemSpacing, ImVec2(px(8), 0));
    if (pill(Str::f("All (%d)", nstar), bm_tab == 0, 0, "b0")) bm_tab = 0;
    ImGui::SameLine(); if (pill("Recently Viewed", bm_tab == 1, IC_CLOCK, "b1")) bm_tab = 1;
    ImGui::SameLine(); if (pill("Progress", bm_tab == 2, IC_TROPHY, "b2")) bm_tab = 2;
    ImGui::PopStyleVar();
    spacer(14);
    if (bm_tab == 0) { for (int i = 0; i < mods.n; i++) { const Store::Entry* e = store.find(mods[i].id); if (e && e->star) list.push(i); } }
    else {
        for (int i = 0; i < mods.n; i++) { const Store::Entry* e = store.find(mods[i].id); if (e && (bm_tab == 1 ? e->prog.seen > 0 : (e->prog.seen > 0 || e->prog.best >= 0))) list.push(i); }
        // most recent first
        for (int i = 1; i < list.n; i++) { int k = list[i], j = i - 1; double sk = store.find(mods[k].id)->prog.seen;
            while (j >= 0 && store.find(mods[list[j]].id)->prog.seen < sk) { list[j + 1] = list[j]; j--; } list[j + 1] = k; }
        if (bm_tab == 1 && list.n > 60) list.resize(60);
    }
    if (bm_tab == 2) {
        int opened = 0, passed = 0, attempted = 0;
        for (const ModInfo& m : mods) { const Store::Entry* e = store.find(m.id); if (!e) continue; if (e->prog.seen > 0) opened++; if (e->prog.best >= 0) attempted++; if (e->prog.best >= 70) passed++; }
        indent_to(w, cw);
        ImVec2 a = ImGui::GetCursorScreenPos(); float hh = px(96);
        ImGui::Dummy(ImVec2(cw, hh));
        grad_rect(dl, a, ImVec2(a.x + cw, a.y + hh), px(18), T.dark ? IM_COL32(0x16, 0x36, 0x75, 255) : IM_COL32(0xe0, 0xeb, 0xff, 255), T.dark ? IM_COL32(0x0b, 0x19, 0x38, 255) : IM_COL32(0xf7, 0xfa, 0xff, 255));
        dl->AddRect(a, ImVec2(a.x + cw, a.y + hh), T.border, px(18), px(1));
        ImVec2 c(a.x + px(48), a.y + hh / 2); float f = mods.n ? (float)opened / mods.n : 0;
        dl->AddCircle(c, px(30), T.line, 48, px(7));
        if (f > 0) { dl->PathArcTo(c, px(30), -(float)M_PI / 2, -(float)M_PI / 2 + 2 * (float)M_PI * f, 48); dl->PathStroke(T.amber, px(7)); }
        Str pc = Str::f("%d%%", (int)roundf(f * 100)); ImVec2 ts = text_size(f_bold, 14, pc); text_at(dl, f_bold, 14, ImVec2(c.x - ts.x / 2, c.y - ts.y / 2), T.ink, pc);
        text_at(dl, f_bold, 17, ImVec2(a.x + px(94), a.y + px(18)), T.ink, Str::f("%d of %d modules opened", opened, mods.n));
        text_at(dl, f_body, 13, ImVec2(a.x + px(94), a.y + px(44)), T.muted, Str::f("%d quizzes taken · %d passed (≥ 70 %%)", attempted, passed), cw - px(110));
        spacer(12);
    }
    float rh = px(96);
    for (int k = 0; k < list.n; k++) {
        int i = list[k]; const ModInfo& m = mods[i]; const Store::Entry* e = store.find(m.id);
        indent_to(w, cw);
        ImGui::PushID(i);
        ImVec2 a = ImGui::GetCursorScreenPos();
        bool click = ImGui::InvisibleButton("##r", ImVec2(cw, rh));
        ImVec2 b(a.x + cw, a.y + rh);
        card_bg(dl, a, b, px(16), ImGui::IsItemActive() ? T.surface2 : T.surface);
        thumb_tile(*this, dl, i, ImVec2(a.x + px(8), a.y + px(8)), ImVec2(a.x + px(118), b.y - px(8)), px(12), true);
        float tx = a.x + px(130), tw = cw - px(130) - px(76);
        text_clipped(dl, f_bold, 15.5f, ImVec2(tx, a.y + px(14)), tw, T.ink, m.title);
        text_clipped(dl, f_body, 12.5f, ImVec2(tx, a.y + px(38)), tw, T.muted, sub_line(m));
        Str meta = Str::f("#%d · %s", m.no, m.department.c());
        if (e && e->prog.best >= 0) meta = Str::f("Quiz best %d %% · %s", e->prog.best, e->prog.best >= 70 ? "passed" : "keep practising");
        text_clipped(dl, f_med, 12, ImVec2(tx, a.y + px(62)), tw, e && e->prog.best >= 0 ? (e->prog.best >= 70 ? T.good : T.amber) : T.faint, meta);
        bool st = e && e->star;
        ImGui::SetCursorScreenPos(ImVec2(b.x - px(70), a.y + px(26)));
        if (round_icon("bm", st ? IC_BOOKMARK_FILL : IC_BOOKMARK, 40, 0, st ? T.amber : T.muted)) { Store::Entry& se = store.get(m.id); se.star = !se.star; store.dirty = true; click = false; }
        draw_icon(dl, IC_NEXT, ImVec2(b.x - px(16), a.y + rh / 2), px(18), T.muted);
        ImGui::SetCursorScreenPos(ImVec2(a.x, b.y)); ImGui::Dummy(ImVec2(1, px(8)));
        if (click) open_module(i);
        ImGui::PopID();
    }
    if (!list.n) {
        spacer(30); indent_to(w, cw);
        ImVec2 p = ImGui::GetCursorScreenPos();
        draw_icon(dl, bm_tab == 0 ? IC_BOOKMARK : (bm_tab == 1 ? IC_CLOCK : IC_TROPHY), ImVec2(p.x + cw / 2, p.y + px(26)), px(44), T.faint);
        const char* t1 = bm_tab == 0 ? "No saved models yet" : (bm_tab == 1 ? "Nothing viewed yet" : "No progress yet");
        const char* t2 = bm_tab == 0 ? "Tap the bookmark on a model card or in the 3-D viewer." : "Open a model in the 3-D viewer to start.";
        ImVec2 s1 = text_size(f_semi, 17, t1), s2 = text_size(f_body, 13, t2);
        text_at(dl, f_semi, 17, ImVec2(p.x + (cw - s1.x) / 2, p.y + px(62)), T.ink, t1);
        text_at(dl, f_body, 13, ImVec2(p.x + (cw - s2.x) / 2, p.y + px(88)), T.muted, t2);
        ImGui::Dummy(ImVec2(cw, px(116)));
        float bw = px(200); ImGui::SetCursorPosX((w - bw) / 2);
        if (primary("Browse catalog", IC_ARROW_RIGHT, false, bw, "bcat")) { cat_dept = -1; cat_saved = false; go(SCR_CATALOG); }
    }
    spacer(24);
    ImGui::End();
}

// ================================================================== More
static bool menu_row(const char* id, int icon, ImU32 tint, const char* title, const char* sub, float cw) {
    ImDrawList* dl = ImGui::GetWindowDrawList();
    ImVec2 a = ImGui::GetCursorScreenPos(); float hh = px(68);
    ImGui::PushID(id);
    bool click = ImGui::InvisibleButton("##mr", ImVec2(cw, hh));
    ImGui::PopID();
    ImVec2 b(a.x + cw, a.y + hh);
    card_bg(dl, a, b, px(16), ImGui::IsItemActive() ? T.surface2 : T.surface);
    ImVec2 ia(a.x + px(12), a.y + px(12)), ib(a.x + px(56), a.y + px(56));
    grad_rect(dl, ia, ib, px(12), tint, (tint & 0x00ffffff) | 0xb0000000);
    draw_icon(dl, icon, ImVec2((ia.x + ib.x) / 2, (ia.y + ib.y) / 2), px(24), IM_COL32_WHITE);
    text_at(dl, g_app->f_semi, 16, ImVec2(a.x + px(70), a.y + px(13)), T.ink, title);
    text_clipped(dl, g_app->f_body, 12.5f, ImVec2(a.x + px(70), a.y + px(37)), cw - px(110), T.muted, sub);
    draw_icon(dl, IC_NEXT, ImVec2(b.x - px(22), a.y + hh / 2), px(20), T.muted);
    ImGui::Dummy(ImVec2(1, px(8)));
    return click;
}

void App::ui_more(float x, float y, float w, float h) {
    page_begin("##more", x, y, w, h);
    if (page_scroll_reset >= 0) { ImGui::SetScrollY(page_scroll_reset); page_scroll_reset = -1; }
    ImDrawList* dl = ImGui::GetWindowDrawList();
    spacer(14);
    float cw = column(w, 900);
    { ImVec2 p = ImGui::GetCursorScreenPos(); text_at(dl, f_bold, 30, p, T.ink, "More"); ImGui::Dummy(ImVec2(cw, px(50))); }
    // progress card
    {
        int opened = 0, passed = 0, starred = 0;
        for (const ModInfo& m : mods) { const Store::Entry* e = store.find(m.id); if (!e) continue; opened += e->prog.seen > 0; passed += e->prog.best >= 70; starred += e->star; }
        indent_to(w, cw);
        ImVec2 a = ImGui::GetCursorScreenPos(); float hh = px(90);
        bool click = ImGui::InvisibleButton("##prog", ImVec2(cw, hh));
        ImVec2 b(a.x + cw, a.y + hh);
        card_bg(dl, a, b, px(18), T.surface);
        ImVec2 c(a.x + px(46), a.y + hh / 2); float f = mods.n ? (float)opened / mods.n : 0;
        dl->AddCircleFilled(c, px(30), T.surface2, 40);
        dl->AddCircle(c, px(26), T.line, 40, px(5));
        if (f > 0) { dl->PathArcTo(c, px(26), -(float)M_PI / 2, -(float)M_PI / 2 + 2 * (float)M_PI * f, 40); dl->PathStroke(T.accent, px(5)); }
        draw_icon(dl, IC_TROPHY, c, px(22), T.amber);
        text_at(dl, f_bold, 18, ImVec2(a.x + px(90), a.y + px(18)), T.ink, "Your progress");
        text_clipped(dl, f_body, 13, ImVec2(a.x + px(90), a.y + px(46)), cw - px(130), T.muted, Str::f("%d of %d opened · %d quizzes passed · %d saved", opened, mods.n, passed, starred), 2);
        draw_icon(dl, IC_NEXT, ImVec2(b.x - px(22), a.y + hh / 2), px(20), T.muted);
        if (click) { bm_tab = 2; go(SCR_BOOKMARKS); }
        spacer(12);
    }
    indent_to(w, cw); text(f_bold, 19, T.ink, "Sections", false); spacer(8);
    struct R { int page; int icon; uint32_t tint; const char* t; const char* s; } rows[] = {
        {MP_PATHS, IC_CAP, 0x2f7cff, "Learning Paths", "Structured journey through the 11 departments"},
        {MP_COMPARE, IC_SCALES, 0x8b5cf6, "Compare Models", "Side-by-side engineering comparison"},
        {MP_CALCS, IC_CALC, 0x0ea5b7, "Engineering Calculators", "50 calculators: pumps, piping, heat, solids, safety"},
        {MP_TRAINING, IC_PLAYCIRCLE, 0x22a06b, "Training & Tutorials", "Guided 3-D tours with narration"},
        {MP_SETTINGS, IC_GEAR, 0x5b6b8c, "Settings", "Appearance, narration and viewer defaults"},
        {MP_HELP, IC_HEADSET, 0x2f7cff, "Help & Support", "Gestures, controls and FAQs"},
        {MP_ABOUT, IC_INFO, 0x3d63c9, "About App", "Version and licences"}};
    for (auto& r : rows) {
        indent_to(w, cw);
        ImU32 tint = IM_COL32((r.tint >> 16) & 255, (r.tint >> 8) & 255, r.tint & 255, 255);
        Str sub = r.page == MP_ABOUT ? Str::f("Version %s · native", VERSION) : Str(r.s);
        if (menu_row(r.t, r.icon, tint, r.t, sub, cw)) { more_page = r.page; page_scroll_reset = 0; reset_confirm = false; }
    }
    // brand footer
    spacer(6); indent_to(w, cw);
    {
        ImVec2 a = ImGui::GetCursorScreenPos(); float hh = px(76);
        ImGui::Dummy(ImVec2(cw, hh));
        ImVec2 b(a.x + cw, a.y + hh);
        grad_rect(dl, a, b, px(18), T.dark ? IM_COL32(0x13, 0x2c, 0x5e, 255) : IM_COL32(0xe3, 0xed, 0xff, 255), T.dark ? IM_COL32(0x08, 0x13, 0x2c, 255) : IM_COL32(0xf8, 0xfa, 0xff, 255));
        logo(dl, ImVec2(a.x + px(40), a.y + hh / 2), px(22));
        ImVec2 ps = text_size(f_bold, 20, "Pump");
        text_at(dl, f_bold, 20, ImVec2(a.x + px(72), a.y + px(16)), T.ink, "Pump"); text_at(dl, f_bold, 20, ImVec2(a.x + px(72) + ps.x, a.y + px(16)), T.amber, "Forge");
        text_at(dl, f_body, 12.5f, ImVec2(a.x + px(72), a.y + px(44)), T.muted, "Explore. Learn. Apply.");
    }
    spacer(24);
    ImGui::End();
}

static void top_bar(App& a, const char* title, float w) {
    ImDrawList* dl = ImGui::GetWindowDrawList();
    spacer(10);
    float cw = column(w, 900);
    ImVec2 p = ImGui::GetCursorScreenPos();
    if (round_icon("tb_back", IC_BACK, 42, T.surface2, T.ink, true)) a.back();
    text_at(dl, a.f_bold, 22, ImVec2(p.x + px(56), p.y + px(8)), T.ink, title);
    ImGui::SetCursorScreenPos(ImVec2(p.x, p.y + px(56)));
    (void)cw;
}

void App::ui_more_page(float x, float y, float w, float h) {
    page_begin("##morepage", x, y, w, h);
    if (page_scroll_reset >= 0) { ImGui::SetScrollY(page_scroll_reset); page_scroll_reset = -1; }
    ImDrawList* dl = ImGui::GetWindowDrawList();
    static const char* TITLES[] = {"", "Learning Paths", "Compare Models", "Engineering Calculators", "Training & Tutorials", "Settings", "Help & Support", "About App"};
    top_bar(*this, TITLES[more_page], w);
    float cw = fminf(w - px(32), px(900));
    ImGui::SetCursorPosX((w - cw) / 2);
    ImGui::BeginChild("##mpcol", ImVec2(cw, 0), ImGuiChildFlags_AutoResizeY, ImGuiWindowFlags_NoScrollbar | ImGuiWindowFlags_NoScrollWithMouse | ImGuiWindowFlags_NoBackground);
    if (more_page == MP_PATHS) {
        muted("Work through each department in order. Opening a model marks it as studied; passing its quiz (≥ 70 %) completes it.", 13);
        spacer(10);
        int next = -1; for (int i = 0; i < mods.n && next < 0; i++) { const Store::Entry* e = store.find(mods[i].id); if (!(e && e->prog.seen > 0)) next = i; }
        if (next >= 0) {
            ImVec2 a = ImGui::GetCursorScreenPos(); float hh = px(84);
            ImGui::Dummy(ImVec2(cw, hh));
            grad_rect(dl, a, ImVec2(a.x + cw, a.y + hh), px(16), T.dark ? IM_COL32(0x16, 0x36, 0x75, 255) : IM_COL32(0xe0, 0xeb, 0xff, 255), T.dark ? IM_COL32(0x0b, 0x19, 0x38, 255) : IM_COL32(0xf7, 0xfa, 0xff, 255));
            thumb_tile(*this, dl, next, ImVec2(a.x + px(8), a.y + px(8)), ImVec2(a.x + px(96), a.y + hh - px(8)), px(10), true);
            text_at(dl, f_semi, 11.5f, ImVec2(a.x + px(108), a.y + px(14)), T.amber, "NEXT UP");
            text_clipped(dl, f_bold, 15.5f, ImVec2(a.x + px(108), a.y + px(32)), cw - px(170), T.ink, mods[next].title);
            text_clipped(dl, f_body, 12, ImVec2(a.x + px(108), a.y + px(54)), cw - px(170), T.muted, Str::f("Module %d · %s", mods[next].no, mods[next].department.c()));
            ImGui::SetCursorScreenPos(ImVec2(a.x + cw - px(56), a.y + px(20)));
            if (round_icon("next", IC_PLAY, 44, T.accent, IM_COL32_WHITE)) open_module(next);
            ImGui::SetCursorScreenPos(ImVec2(a.x, a.y + hh)); spacer(10);
        }
        for (int d = 0; d < depts.n; d++) {
            ImGui::PushID(d);
            int n = 0, op = 0, pass = 0, a0 = -1, a1 = -1;
            for (const ModInfo& m : mods) if (m.dept == d) { n++; if (a0 < 0) a0 = m.no; a1 = m.no; const Store::Entry* e = store.find(m.id); if (e) { op += e->prog.seen > 0; pass += e->prog.best >= 70; } }
            ImVec2 a = ImGui::GetCursorScreenPos(); float hh = px(86);
            bool click = ImGui::InvisibleButton("##p", ImVec2(cw, hh));
            ImVec2 b(a.x + cw, a.y + hh);
            card_bg(dl, a, b, px(16), path_open == d ? T.surface2 : T.surface);
            ImVec2 ia(a.x + px(12), a.y + px(14)), ib(a.x + px(56), a.y + px(58));
            grad_rect(dl, ia, ib, px(12), dept_color(n ? d : 11, 2), T.dark ? dept_color(n ? d : 11, 1) : ((dept_color(n ? d : 11, 2) & 0x00ffffff) | 0xc8000000));
            Str num = Str::f("%d", d + 1); ImVec2 ns = text_size(f_bold, 17, num); text_at(dl, f_bold, 17, ImVec2((ia.x + ib.x - ns.x) / 2, (ia.y + ib.y - ns.y) / 2), IM_COL32_WHITE, num);
            text_clipped(dl, f_semi, 15.5f, ImVec2(a.x + px(70), a.y + px(12)), cw - px(110), T.ink, depts[d].name);
            if (n) {
                text_at(dl, f_body, 12, ImVec2(a.x + px(70), a.y + px(36)), T.muted, Str::f("#%d–%d · %d modules · %d/%d opened · %d passed", a0, a1, n, op, n, pass));
                progress(dl, ImVec2(a.x + px(70), a.y + px(62)), cw - px(110), px(6), (float)op / n, T.accent, T.line);
                draw_icon(dl, path_open == d ? IC_CHEV_DOWN : IC_NEXT, ImVec2(b.x - px(22), a.y + hh / 2), px(18), T.muted);
            } else text_at(dl, f_body, 12, ImVec2(a.x + px(70), a.y + px(36)), T.muted, "Future expansion");
            if (click && n) path_open = path_open == d ? -1 : d;
            spacer(6);
            if (path_open == d) {
                for (int i = 0; i < mods.n; i++) if (mods[i].dept == d) {
                    ImGui::PushID(i);
                    const Store::Entry* e = store.find(mods[i].id);
                    ImVec2 r0 = ImGui::GetCursorScreenPos(); float rh = px(46);
                    bool c2 = ImGui::InvisibleButton("##m", ImVec2(cw, rh));
                    if (ImGui::IsItemActive()) dl->AddRectFilled(r0, ImVec2(r0.x + cw, r0.y + rh), T.surface2, px(10));
                    bool done = e && e->prog.seen > 0, passed = e && e->prog.best >= 70;
                    ImVec2 cc(r0.x + px(26), r0.y + rh / 2);
                    if (passed) { dl->AddCircleFilled(cc, px(11), T.good, 24); draw_icon(dl, IC_CHECK, cc, px(14), IM_COL32_WHITE); }
                    else if (done) { dl->AddCircle(cc, px(10), T.accent, 24, px(2)); dl->AddCircleFilled(cc, px(4), T.accent, 12); }
                    else dl->AddCircle(cc, px(10), T.faint, 24, px(1.5f));
                    text_at(dl, f_monom, 12, ImVec2(r0.x + px(46), r0.y + px(14)), T.faint, Str::f("%3d", mods[i].no));
                    text_clipped(dl, f_med, 14, ImVec2(r0.x + px(84), r0.y + px(13)), cw - px(150), T.ink, mods[i].title);
                    if (e && e->prog.best >= 0) { Str s = Str::f("%d%%", e->prog.best); ImVec2 ts = text_size(f_med, 12, s); text_at(dl, f_med, 12, ImVec2(r0.x + cw - ts.x - px(12), r0.y + px(15)), passed ? T.good : T.amber, s); }
                    if (c2) open_module(i);
                    ImGui::PopID();
                }
                spacer(8);
            }
            ImGui::PopID();
        }
    } else if (more_page == MP_COMPARE) {
        muted("Choose two models to compare their design-class parameters and key points.", 13);
        spacer(10);
        if (cmp_a < 0) cmp_a = cur >= 0 ? cur : 0;
        auto sel = [&](const char* id, const char* lab, int m, int mode) {
            text(f_semi, 12, T.muted, lab, false);
            Str l = m >= 0 ? Str::f("%s  %s", mods[m].eq_id.empty() ? Str::f("#%d", mods[m].no).c() : mods[m].eq_id.c(), mods[m].title.c()) : Str();
            if (field(id, l, "Choose a model…", cw, IC_CUBE, 46)) { picker_mode = mode; picker_open = true; }
            spacer(6);
        };
        sel("ca", "MODEL A", cmp_a, 2);
        sel("cb", "MODEL B", cmp_mod, 3);
        auto load_learn = [&](int m, JDoc& d) { Vec<uint8_t> b; return m >= 0 && plat::read_asset(Str::f("learning/%s.json", mods[m].id.c()), b) && d.parse((const char*)b.d, (size_t)b.n); };
        static int la = -1, lb = -1;
        if (la != cmp_a) { la = load_learn(cmp_a, cmp_learn_a) ? cmp_a : -1; }
        if (lb != cmp_mod) { lb = load_learn(cmp_mod, cmp_learn) ? cmp_mod : -1; }
        if (la >= 0 && lb >= 0 && cmp_learn_a.root && cmp_learn.root) {
            spacer(6);
            card_begin("##cmpcard");
            ui_compare(cmp_a, cmp_mod, *cmp_learn_a.root, *cmp_learn.root);
            card_end();
            if (primary("Open A in 3-D", IC_CUBE, false, 0, "oa", 40)) open_module(cmp_a);
            ImGui::SameLine(0, px(8));
            if (primary("Open B in 3-D", IC_CUBE, false, 0, "ob", 40)) open_module(cmp_mod);
        } else {
            spacer(10);
            card_begin("##cmphint");
            ImVec2 p = ImGui::GetCursorScreenPos(); ImDrawList* cdl = ImGui::GetWindowDrawList();
            cdl->AddCircleFilled(ImVec2(p.x + px(18), p.y + px(18)), px(18), T.chip, 24);
            draw_icon(cdl, IC_SCALES, ImVec2(p.x + px(18), p.y + px(18)), px(18), T.accent);
            ImGui::SetCursorScreenPos(ImVec2(p.x + px(48), p.y + px(8)));
            text(f_semi, 14.5f, T.ink, "Pick Model B to compare", false);
            ImGui::SetCursorScreenPos(ImVec2(p.x, p.y + px(44)));
            muted("The table lists both models side by side: department, design-class parameter ranges (pressure, flow, speed, temperature…), standards and key points. Tip: the Tools tab of an open model can compare against it directly.", 13);
            card_end();
        }
    } else if (more_page == MP_CALCS) {
        muted("Simplified textbook relations for engineers and subject-matter experts — verify against the relevant standards before design decisions. Tap a calculator to open it.", 13);
        spacer(10);
        for (int i = 0; i < NCALCS; i++) calc_card(CALCS[i], true);
    } else if (more_page == MP_TRAINING) {
        muted("Every module has guided tours that drive the 3-D model (camera, cutaway, explode, animation and overlays) with captions and optional narration.", 13);
        spacer(8);
        bool nar = store.narrate;
        if (checkbox("Read narration aloud (text-to-speech)", &nar)) { store.narrate = nar; store.dirty = true; }
        spacer(6);
        ImGui::PushStyleVar(ImGuiStyleVar_ItemSpacing, ImVec2(px(8), 0));
        ImGui::BeginChild("##tchips", ImVec2(cw, px(38)), 0, ImGuiWindowFlags_HorizontalScrollbar | ImGuiWindowFlags_NoScrollbar | ImGuiWindowFlags_NoScrollWithMouse);
        if (pill("All", cat_dept < 0, 0, "all")) cat_dept = -1;
        for (int d = 0; d < depts.n; d++) if (depts[d].modules) { ImGui::SameLine(); ImGui::PushID(d); if (pill(depts[d].name, cat_dept == d, 0, "d")) cat_dept = d; ImGui::PopID(); }
        ImGui::EndChild(); ImGui::PopStyleVar();
        spacer(10);
        for (int i = 0; i < mods.n; i++) {
            if (cat_dept >= 0 && mods[i].dept != cat_dept) continue;
            ImGui::PushID(i);
            ImVec2 a = ImGui::GetCursorScreenPos(); float rh = px(70);
            bool click = ImGui::InvisibleButton("##t", ImVec2(cw, rh));
            card_bg(dl, a, ImVec2(a.x + cw, a.y + rh), px(14), ImGui::IsItemActive() ? T.surface2 : T.surface);
            thumb_tile(*this, dl, i, ImVec2(a.x + px(6), a.y + px(6)), ImVec2(a.x + px(78), a.y + rh - px(6)), px(10), true);
            text_clipped(dl, f_semi, 14.5f, ImVec2(a.x + px(90), a.y + px(12)), cw - px(150), T.ink, mods[i].title);
            text_at(dl, f_body, 12, ImVec2(a.x + px(90), a.y + px(36)), T.muted, Str::f("%d guided tours · %d quiz questions", mods[i].tours, mods[i].quizq));
            dl->AddCircleFilled(ImVec2(a.x + cw - px(30), a.y + rh / 2), px(17), T.accent, 28);
            draw_icon(dl, IC_PLAY, ImVec2(a.x + cw - px(28), a.y + rh / 2), px(15), IM_COL32_WHITE);
            if (click) open_module(i, TAB_TOURS);
            ImGui::SetCursorScreenPos(ImVec2(a.x, a.y + rh)); spacer(8);
            ImGui::PopID();
        }
    } else if (more_page == MP_SETTINGS) {
        // one preference row inside the card: title + explanation on the left, switch on the right
        // (drawn into the card's own draw list and sized to the card's inner width)
        auto row = [&](const char* title, const char* sub) {
            ImDrawList* cdl = ImGui::GetWindowDrawList();
            float iw = ImGui::GetContentRegionAvail().x;
            ImVec2 p = ImGui::GetCursorScreenPos();
            text_at(cdl, f_semi, 15, p, T.ink, title);
            text_at(cdl, f_body, 12.5f, ImVec2(p.x, p.y + px(22)), T.muted, sub, iw - px(64));
            float sh = text_size(f_body, 12.5f, sub, iw - px(64)).y;
            ImGui::SetCursorScreenPos(ImVec2(p.x + iw - px(48), p.y + px(4)));
            return sh + px(26);
        };
        card_begin("##appear");
        text(f_semi, 15, T.ink, "Appearance", false); spacer(2); muted("Dark is the default industrial look; Light suits bright workshops.", 12.5f); spacer(8);
        {
            float sw = ImGui::GetContentRegionAvail().x / 3 - px(6);
            const char* L[3] = {"System", "Dark", "Light"}; int I[3] = {IC_GEAR, IC_MOON, IC_SUN};
            for (int k = 0; k < 3; k++) { if (k) ImGui::SameLine(0, px(8)); ImGui::PushID(k);
                if (pill(L[k], store.theme == k, I[k], "th", 40)) { store.theme = k; store.dirty = true; apply_theme(); }
                (void)sw; ImGui::PopID(); }
        }
        card_end();
        card_begin("##prefs");
        float cwi = ImGui::GetContentRegionAvail().x; (void)cwi;
        { float y0 = ImGui::GetCursorPosY(); float hh = row("Read narration aloud", "Tours and the How-it-works player speak the captions (Android text-to-speech).");
          bool v = store.narrate; if (toggle("t1", &v)) { store.narrate = v; store.dirty = true; if (!v) plat::stop_speaking(); } ImGui::SetCursorPosY(y0 + hh + px(10)); }
        ImGui::Separator(); spacer(8);
        { float y0 = ImGui::GetCursorPosY(); float hh = row("Live flow on start", "Animated flow particles are shown when a model opens.");
          bool v = store.live_default; if (toggle("t2", &v)) { store.live_default = v; live = v; store.dirty = true; } ImGui::SetCursorPosY(y0 + hh + px(10)); }
        ImGui::Separator(); spacer(8);
        { float y0 = ImGui::GetCursorPosY(); float hh = row("Part number markers", "Numbered markers on the model match the Parts list.");
          bool v = store.markers_default; if (toggle("t3", &v)) { store.markers_default = v; markers = v; store.dirty = true; } ImGui::SetCursorPosY(y0 + hh + px(10)); }
        ImGui::Dummy(ImVec2(0, 0));
        card_end();
        card_begin("##data");
        text(f_semi, 15, T.ink, "Your data", false); spacer(2);
        muted("Bookmarks, progress, quiz scores, notes and datasheets are stored only on this device.", 12.5f); spacer(8);
        if (!reset_confirm) { if (tool("Reset progress and bookmarks…")) reset_confirm = true; }
        else {
            text(f_med, 13, T.bad, "This clears bookmarks, progress, quiz scores, notes and datasheets.", true); spacer(4);
            if (tool("Yes, reset everything", true)) { store.e.clear(); store.dirty = true; reset_confirm = false; show_toast("Progress reset"); }
            ImGui::SameLine(0, px(8)); if (tool("Cancel")) reset_confirm = false;
        }
        card_end();
    } else if (more_page == MP_HELP) {
        struct H { int icon; const char* t; const char* b; } items[] = {
            {IC_HAND, "Gestures", "One finger: orbit the model.  Two fingers: pinch to zoom, drag to pan.  Tap a part: open its details.  Lists scroll with a swipe."},
            {IC_CUBE, "3-D viewer controls", "3D View resets the model; Exploded pulls the parts apart (fine-tune with the slider); Cutaway shows the section; X-ray ghosts static parts. Side buttons: operate (play/pause), auto-rotate, zoom, reset view, full screen."},
            {IC_STEPS, "How it works & tours", "How it works steps through the working principle on the model. Tours (Tours tab) play scripted scenes with captions and optional narration."},
            {IC_TAG, "Parts & markers", "The Parts tab lists every component; the numbers match the markers on the model. Inspect a part to isolate, hide or zoom to it."},
            {IC_CALC, "Engineering tools", "Each model's Tools tab has the most relevant calculators first, a datasheet you can fill in and copy as JSON, notes, compare and distance measurement."},
            {IC_BOOKMARK, "Bookmarks & progress", "Save models with the bookmark icon. Opening a model and passing its quiz (≥ 70 %) is tracked in Bookmarks → Progress and in Learning Paths."},
            {IC_SPEAKER, "Narration is silent?", "Install or enable a text-to-speech voice in Android Settings → Accessibility → Text-to-speech output."},
            {IC_INFO, "Offline", "Everything (282 models, lessons, quizzes) is inside the app. No internet connection or account is needed."},
            {IC_HEADSET, "Contact", "Red Eye Labs — send feedback and requests for new equipment modules through your project channel."}};
        for (auto& it : items) {
            ImGui::PushID(it.t);
            card_begin("##h");
            ImVec2 p = ImGui::GetCursorScreenPos();
            ImGui::GetWindowDrawList()->AddCircleFilled(ImVec2(p.x + px(16), p.y + px(14)), px(16), T.chip, 24);
            draw_icon(ImGui::GetWindowDrawList(), it.icon, ImVec2(p.x + px(16), p.y + px(14)), px(18), T.accent);
            ImGui::SetCursorScreenPos(ImVec2(p.x + px(44), p.y + px(4)));
            text(f_semi, 15, T.ink, it.t, false);
            ImGui::SetCursorScreenPos(ImVec2(p.x, p.y + px(34)));
            text(f_body, 13.5f, T.muted, it.b);
            card_end();
            ImGui::PopID();
        }
    } else if (more_page == MP_ABOUT) {
        ImVec2 p = ImGui::GetCursorScreenPos();
        logo(dl, ImVec2(p.x + cw / 2, p.y + px(46)), px(40));
        ImVec2 ps = text_size(f_bold, 26, "PumpForge");
        float tx = p.x + (cw - ps.x) / 2;
        text_at(dl, f_bold, 26, ImVec2(tx, p.y + px(98)), T.ink, "Pump"); text_at(dl, f_bold, 26, ImVec2(tx + text_size(f_bold, 26, "Pump").x, p.y + px(98)), T.amber, "Forge");
        Str v = Str::f("Version %s · fully native (C++ / OpenGL ES 3)", VERSION); ImVec2 vs = text_size(f_body, 13, v);
        text_at(dl, f_body, 13, ImVec2(p.x + (cw - vs.x) / 2, p.y + px(134)), T.muted, v);
        ImGui::Dummy(ImVec2(cw, px(162)));
        card_begin("##ab1");
        text(f_semi, 15, T.ink, "Industrial Engineering Equipment Library", true); spacer(4);
        para(Str::f("%d interactive 3-D modules in %d departments, each with 13 lesson sections: introduction, 3-D model, exploded view, cross-section, working principle, flow animation, components, engineering parameters, installation, maintenance, failure analysis, guided tours and assessment.", mods.n, depts.n - 1));
        card_end();
        card_begin("##ab2");
        text(f_semi, 15, T.ink, "Credits & licences", false); spacer(4);
        para("Dear ImGui (MIT) · IBM Plex Sans, Sans Condensed and Mono (SIL Open Font License 1.1) · DejaVu Sans symbols (Bitstream Vera licence) · image-based light baked from three.js RoomEnvironment (MIT).");
        card_end();
        card_begin("##ab3");
        text(f_semi, 15, T.ink, "Disclaimer", false); spacer(4);
        muted("Educational models with typical design-class ranges, not ratings of any specific product. Verify against the selected manufacturer datasheet, the applicable standards (current editions) and site procedures before engineering, installation or maintenance decisions.", 13);
        card_end();
        muted("© Red Eye Labs", 12);
    }
    spacer(28);
    ImGui::EndChild();
    ImGui::End();
}

// ================================================================== module picker (open / compare)
void App::ui_picker() {
    float W = (float)fbw, H = (float)fbh;
    ImGui::SetNextWindowPos(ImVec2(0, 0)); ImGui::SetNextWindowSize(ImVec2(W, H));
    ImGui::PushStyleColor(ImGuiCol_WindowBg, IM_COL32(2, 6, 16, 170));
    ImGui::Begin("##pickdim", nullptr, WF & ~ImGuiWindowFlags_NoBringToFrontOnFocus);
    ImGui::PopStyleColor();
    float sw = pf_min(px(560), W - px(16)), sh = (H - inset_top - inset_bottom) * (g_wide ? 0.82f : 0.88f);
    float sx = (W - sw) / 2, sy = inset_top + ((H - inset_top - inset_bottom) - sh) / 2;
    ImVec2 mp = ImGui::GetIO().MousePos;
    if (ImGui::IsMouseReleased(0) && ImGui::IsWindowHovered() && !scroll_drag && (mp.x < sx || mp.x > sx + sw || mp.y < sy || mp.y > sy + sh)) picker_open = false;
    ImGui::SetCursorScreenPos(ImVec2(sx, sy));
    ImGui::PushStyleColor(ImGuiCol_ChildBg, T.surface); ImGui::PushStyleColor(ImGuiCol_Border, T.border);
    ImGui::PushStyleVar(ImGuiStyleVar_ChildRounding, px(20)); ImGui::PushStyleVar(ImGuiStyleVar_WindowPadding, ImVec2(px(16), px(14))); ImGui::PushStyleVar(ImGuiStyleVar_ChildBorderSize, px(1));
    ImGui::BeginChild("##psheet", ImVec2(sw, sh), ImGuiChildFlags_AlwaysUseWindowPadding | ImGuiChildFlags_Borders, ImGuiWindowFlags_NoScrollbar);
    float cw = ImGui::GetContentRegionAvail().x;
    const char* title = picker_mode == 0 ? "Choose a module" : (picker_mode == 1 ? "Compare with…" : (picker_mode == 2 ? "Model A" : "Model B"));
    ImVec2 tp = ImGui::GetCursorScreenPos();
    text_at(ImGui::GetWindowDrawList(), f_bold, 19, ImVec2(tp.x, tp.y + px(8)), T.ink, title);
    ImGui::SetCursorScreenPos(ImVec2(tp.x + cw - px(40), tp.y));
    if (round_icon("pclose", IC_CLOSE, 40, T.surface2, T.ink)) picker_open = false;
    // search: same matching as the Catalog (all words must appear in title / EQ number / components)
    ImGui::SetCursorScreenPos(ImVec2(tp.x, tp.y + px(50)));
    float fw = pick_query.empty() ? cw : cw - px(48);
    if (field("psearch", pick_query, "Search by name, EQ number, component…", fw, IC_SEARCH, 42)) begin_text(6, "", "Search models", pick_query, plat::TEXT);
    if (!pick_query.empty()) { ImGui::SameLine(0, px(8)); if (round_icon("pclr", IC_CLOSE, 40, T.surface2, T.muted)) pick_query.clear(); }
    Str q(pick_query); str_lower(q);
    Vec<Str> words; { const char* s = q.c(); while (*s) { while (*s == ' ') s++; const char* e = s; while (*e && *e != ' ') e++; if (e > s) words.push(Str(s, (int)(e - s))); s = e; } }
    ImGui::SetCursorScreenPos(ImVec2(tp.x, tp.y + px(100)));
    ImGui::BeginChild("##plist", ImVec2(cw, 0), 0, ImGuiWindowFlags_NoScrollWithMouse);
    float rw = ImGui::GetContentRegionAvail().x;
    int cur_sel = picker_mode == 0 ? cur : (picker_mode == 1 || picker_mode == 3 ? cmp_mod : cmp_a);
    static int scroll_to = -1; static bool opened_once = false;
    if (!opened_once) { scroll_to = cur_sel; opened_once = true; }
    if (!words.empty()) scroll_to = -1;
    int dep = -2, shown = 0;
    ImDrawList* dl = ImGui::GetWindowDrawList();
    for (int i = 0; i < mods.n; i++) {
        const ModInfo& x = mods[i];
        if (picker_mode == 1 && i == cur) continue;
        if (!words.empty() && !mod_match(x, words)) continue;
        shown++;
        if (x.dept != dep) { dep = x.dept; spacer(10); text(f_semi, 12.5f, T.muted, dept_label(*this, dep), false); spacer(2); }
        ImGui::PushID(i);
        Str lbl = Str::f("%s", x.title.c());
        ImVec2 p = ImGui::GetCursorScreenPos(); float rh = px(56);
        bool click = ImGui::InvisibleButton("##p", ImVec2(rw, rh));
        bool sel = i == cur_sel;
        if (sel || ImGui::IsItemActive()) dl->AddRectFilled(p, ImVec2(p.x + rw, p.y + rh), sel ? T.chip : T.surface2, px(12));
        thumb_tile(*this, dl, i, ImVec2(p.x + px(4), p.y + px(4)), ImVec2(p.x + px(68), p.y + rh - px(4)), px(8), true);
        text_clipped(dl, sel ? f_semi : f_med, 14, ImVec2(p.x + px(78), p.y + px(9)), rw - px(110), sel ? T.chip_ink : T.ink, lbl);
        text_clipped(dl, f_body, 11.5f, ImVec2(p.x + px(78), p.y + px(31)), rw - px(110), T.muted, Str::f("#%d · %s", x.no, sub_line(x).c()));
        if (x.flagship) star(dl, ImVec2(p.x + rw - px(16), p.y + rh / 2), px(6), T.amber, true);
        if (scroll_to == i) { ImGui::SetScrollHereY(0.3f); scroll_to = -1; }
        if (click) {
            picker_open = false; opened_once = false;
            if (picker_mode == 0) open_module(i);
            else if (picker_mode == 2) cmp_a = i;
            else {
                cmp_mod = i;
                if (picker_mode == 1) { Vec<uint8_t> b; if (!plat::read_asset(Str::f("learning/%s.json", x.id.c()), b) || !cmp_learn.parse((const char*)b.d, (size_t)b.n)) { cmp_mod = -1; show_toast("Could not load."); } }
            }
        }
        ImGui::PopID();
    }
    if (!shown) { spacer(24); text(f_semi, 14, T.ink, "No models match your search", false); spacer(4); muted("Try fewer words, an EQ number (e.g. EQ-121) or a component name.", 12.5f); }
    spacer(12);
    ImGui::EndChild();
    ImGui::EndChild();
    ImGui::PopStyleVar(3); ImGui::PopStyleColor(2);
    ImGui::End();
    if (!picker_open) { opened_once = false; pick_query.clear(); }
}

// ================================================================== text entry results (polled every frame, applied live)
void App::ui_text_poll() {
    if (!text_target) return;
    Str v; bool closed = false, accepted = false;
    bool any = plat::text_poll(v, closed, accepted);
    if (any || closed) {
        if (text_target == 2) { cat_query = v; page_scroll_reset = 0; }
        else if (text_target == 6) pick_query = v;
        else if (text_target == 3 && cur >= 0) { Store::Entry& e = store.get(mods[cur].id); if (!e.notes.eq(v)) { e.notes = v; store.dirty = true; } }
        else if (text_target == 4 && cur >= 0) {
            Store::Entry& e = store.get(mods[cur].id); e.ds.set = true;
            if (text_key.eq("manufacturer")) e.ds.manufacturer = v;
            else if (text_key.eq("model")) e.ds.model = v;
            else if (!strncmp(text_key, "rp:", 3)) for (int i = 0; i < e.ds.keys.n; i++) if (e.ds.keys[i].eq(text_key.c() + 3)) e.ds.vals[i] = v;
            store.dirty = true; ds_msg.clear();
        } else if (text_target == 5) {
            const char* colon = strrchr(text_key, ':');
            if (colon) {
                Str ck(text_key.c(), (int)(colon - text_key.c())); int fi = atoi(colon + 1);
                int off = 0; for (int i = 0; i < calc_keys.n; i++) { if (calc_keys[i].eq(ck)) break; const Calc* c = calc_find(calc_keys[i]); off += c ? c->nf : 0; }
                // JS: +input.value -> '' is 0, otherwise Number() (NaN shows as NaN)
                const char* s = v.c(); while (*s == ' ') s++;
                double d = 0;
                if (*s) { char* end = nullptr; d = strtod(s, &end); while (end && *end == ' ') end++; if (!end || *end) d = NAN; }
                if (off + fi < calc_vals.n) calc_vals[off + fi] = d;
            }
        }
    }
    if (closed) text_target = 0;
}
