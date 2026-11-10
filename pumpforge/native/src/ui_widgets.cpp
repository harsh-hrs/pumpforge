#include "ui.h"
#include <stdio.h>

Theme T;
static ImU32 C(uint32_t rgb, float a = 1) { return IM_COL32((rgb >> 16) & 255, (rgb >> 8) & 255, rgb & 255, (int)(a * 255)); }
static V3 S3(uint32_t rgb) { return V3(((rgb >> 16) & 255) / 255.f, ((rgb >> 8) & 255) / 255.f, (rgb & 255) / 255.f); }

void theme_set(bool dark) {
    T.dark = dark;
    if (dark) {
        T.bg = C(0x060d1d); T.bg2 = C(0x0b1733); T.surface = C(0x0e1c39); T.surface2 = C(0x13284f); T.border = C(0x1f3a6d);
        T.ink = C(0xf2f6ff); T.muted = C(0x9aabcb); T.faint = C(0x62769c); T.accent = C(0x2f7cff); T.accent2 = C(0x1b5be0); T.accent_ink = C(0xffffff);
        T.amber = C(0xffb21e); T.amber_ink = C(0x1a1200); T.chip = C(0x15305f); T.chip_ink = C(0xcfe0ff); T.good = C(0x3ddc97); T.bad = C(0xff6b6b);
        T.nav_bg = C(0x0a1530); T.field = C(0x0c1a35); T.line = C(0x1a3060); T.glow = C(0x2f7cff, 0.35f);
        T.stage0 = S3(0x1b3d78); T.stage1 = S3(0x07122b);
    } else {
        T.bg = C(0xeef2f9); T.bg2 = C(0xe2e9f5); T.surface = C(0xffffff); T.surface2 = C(0xf3f6fc); T.border = C(0xd5deee);
        T.ink = C(0x0f1d33); T.muted = C(0x56688a); T.faint = C(0x8a99b3); T.accent = C(0x1f63e0); T.accent2 = C(0x1550c4); T.accent_ink = C(0xffffff);
        T.amber = C(0xf2a20c); T.amber_ink = C(0x1a1200); T.chip = C(0xe5eefd); T.chip_ink = C(0x1748a8); T.good = C(0x138a52); T.bad = C(0xc0392b);
        T.nav_bg = C(0xffffff); T.field = C(0xf2f5fa); T.line = C(0xe1e7f1); T.glow = C(0x1f63e0, 0.18f);
        T.stage0 = S3(0xf7f9fc); T.stage1 = S3(0xd9e1ec);
    }
    T.overlay_bg = C(0x0a1530, 0.92f); T.label_bg = C(0x0a1530, 0.9f); T.star = C(0xffb21e);
}

// department card colours (gradient top / bottom / accent) - distinct hue per department
ImU32 dept_color(int d, int which) {
    static const uint32_t P[12][3] = {
        {0x8a4a22, 0x2a1810, 0xff9a52}, {0x1f56b3, 0x0d1f45, 0x5aa0ff}, {0x16697f, 0x0a2731, 0x41d1f0}, {0x7a5a14, 0x2a1f0a, 0xffc14d},
        {0x5240a0, 0x1a1540, 0xa996ff}, {0x93332f, 0x2e1111, 0xff7a6e}, {0x217552, 0x0c2a1d, 0x4fe0a0}, {0x82602c, 0x2b2011, 0xe8b46a},
        {0x1d6697, 0x0b2539, 0x5cc2ff}, {0x3d4e72, 0x151c2c, 0x9fb4e0}, {0x96610f, 0x2f1f07, 0xffb340}, {0x3a4252, 0x161a22, 0x9aa3b5}};
    uint32_t c = P[((d % 12) + 12) % 12][which];
    if (!T.dark && which < 2) {   // light theme: soft tints of the same hues
        float f = which == 0 ? 0.80f : 0.90f;
        int r = (int)(((c >> 16) & 255) * (1 - f) + 255 * f), g = (int)(((c >> 8) & 255) * (1 - f) + 255 * f), b = (int)((c & 255) * (1 - f) + 255 * f);
        return IM_COL32(r, g, b, 255);
    }
    if (!T.dark) return C(P[((d % 12) + 12) % 12][0]);   // light theme accent: the deep hue reads on pale tints
    return C(c);
}

namespace ui {
float dp = 1;
void font(ImFont* f, float s) { ImGui::PushFont(f, s * dp); }
void pop() { ImGui::PopFont(); }
ImVec2 text_size(ImFont* f, float css, const char* s, float wrap) { return f->CalcTextSizeA(css * dp, FLT_MAX, wrap, s); }

void text(ImFont* f, float size, ImU32 col, const char* s, bool wrap) {
    font(f, size);
    ImGui::PushStyleColor(ImGuiCol_Text, col);
    bool push = wrap && ImGui::GetCurrentWindow()->DC.TextWrapPos < 0;
    if (push) ImGui::PushTextWrapPos(0);
    ImGui::TextUnformatted(s);
    if (push) ImGui::PopTextWrapPos();
    ImGui::PopStyleColor();
    pop();
}
void text_at(ImDrawList* dl, ImFont* f, float size, ImVec2 p, ImU32 col, const char* s, float wrap) {
    dl->AddText(f, size * dp, p, col, s, nullptr, wrap);
}
void text_clipped(ImDrawList* dl, ImFont* f, float size, ImVec2 p, float maxw, ImU32 col, const char* s, int lines) {
    float lh = size * dp * 1.25f;
    dl->PushClipRect(p, ImVec2(p.x + maxw, p.y + lh * lines + 1), true);
    dl->AddText(f, size * dp, p, col, s, nullptr, lines > 1 ? maxw : 0);
    dl->PopClipRect();
}
void spacer(float h) { ImGui::Dummy(ImVec2(1, px(h))); }
void h2(const char* s) { text(g_app->f_bold, 21, T.ink, s); }
void h3(const char* s) {
    spacer(14);
    text(g_app->f_semi, 15, T.ink, s);
    spacer(2);
}
void para(const char* s) { text(g_app->f_body, 14, T.ink, s); }
void muted(const char* s, float size) { text(g_app->f_body, size, T.muted, s); }

void bullets(const JV& arr) {
    if (!arr.size()) { para("—"); return; }
    for (const JV& x : arr) {
        Str s = x.isStr() ? Str(x.str()) : Str(x["task"].str());
        if (!x.isStr() && x["interval"].truthy()) s.addf(" (%s)", x["interval"].str());
        font(g_app->f_body, 14);
        ImVec2 p = ImGui::GetCursorScreenPos();
        float lh = ImGui::GetTextLineHeight();
        ImGui::GetWindowDrawList()->AddCircleFilled(ImVec2(p.x + px(5), p.y + lh * 0.55f), px(2.6f), T.accent);
        ImGui::Indent(px(16));
        ImGui::PushStyleColor(ImGuiCol_Text, T.ink); bool push = ImGui::GetCurrentWindow()->DC.TextWrapPos < 0; if (push) ImGui::PushTextWrapPos(0);
        ImGui::TextUnformatted(s); if (push) ImGui::PopTextWrapPos(); ImGui::PopStyleColor();
        ImGui::Unindent(px(16));
        pop();
        spacer(3);
    }
}

static float chip_right;
static bool chip_first = true;
void chips_begin() { spacer(6); chip_right = ImGui::GetCursorPosX() + ImGui::GetContentRegionAvail().x; chip_first = true; }
void chip(const char* s, bool) {
    font(g_app->f_med, 12);
    ImVec2 ts = ImGui::CalcTextSize(s);
    ImVec2 sz(ts.x + px(18), ts.y + px(8));
    if (!chip_first) { ImGui::SameLine(0, px(6)); if (ImGui::GetCursorPosX() + sz.x > chip_right) ImGui::NewLine(); }
    chip_first = false;
    ImVec2 p = ImGui::GetCursorScreenPos();
    ImGui::Dummy(sz);
    ImDrawList* dl = ImGui::GetWindowDrawList();
    dl->AddRectFilled(p, ImVec2(p.x + sz.x, p.y + sz.y), T.chip, sz.y / 2);
    dl->AddText(ImVec2(p.x + px(9), p.y + px(4)), T.chip_ink, s);
    pop();
}
void chips_end() { chip_first = true; spacer(4); }

// ------------------------------------------------------------------ shapes
void grad_rect(ImDrawList* dl, ImVec2 a, ImVec2 b, float r, ImU32 top, ImU32 bottom, ImDrawFlags fl) {
    int v0 = dl->VtxBuffer.Size;
    dl->AddRectFilled(a, b, IM_COL32_WHITE, r, fl);
    ImGui::ShadeVertsLinearColorGradientKeepAlpha(dl, v0, dl->VtxBuffer.Size, a, ImVec2(a.x + (b.x - a.x) * 0.35f, b.y), top, bottom);
}
void card_bg(ImDrawList* dl, ImVec2 a, ImVec2 b, float r, ImU32 fill, bool border) {
    dl->AddRectFilled(a, b, fill, r);
    if (border) dl->AddRect(a, b, T.border, r, px(1));
}
void glow(ImDrawList* dl, ImVec2 a, ImVec2 b, float r, ImU32 col, float spread) {
    ImVec4 c = ImGui::ColorConvertU32ToFloat4(col);
    for (int i = 4; i >= 1; i--) {
        float e = spread * i / 4.f;
        ImVec4 k = c; k.w = c.w * (0.22f / i);
        dl->AddRectFilled(ImVec2(a.x - e, a.y - e), ImVec2(b.x + e, b.y + e), ImGui::ColorConvertFloat4ToU32(k), r + e);
    }
}
void pf_cb_premul(const ImDrawList*, const ImDrawCmd*);
void pf_cb_normal(const ImDrawList*, const ImDrawCmd*);
void image(ImDrawList* dl, unsigned tex, ImVec2 a, ImVec2 b, float rounding, bool premul) {
    if (!tex) return;
    if (premul) dl->AddCallback(pf_cb_premul, nullptr);
    dl->AddImageRounded(ImTextureRef((ImTextureID)(intptr_t)tex), a, b, ImVec2(0, 1), ImVec2(1, 0), IM_COL32_WHITE, rounding);
    if (premul) dl->AddCallback(pf_cb_normal, nullptr);
}
void progress(ImDrawList* dl, ImVec2 a, float w, float h, float f, ImU32 fill, ImU32 track) {
    dl->AddRectFilled(a, ImVec2(a.x + w, a.y + h), track, h / 2);
    f = pf_clamp(f, 0.f, 1.f);
    if (f > 0) dl->AddRectFilled(a, ImVec2(a.x + fmaxf(h, w * f), a.y + h), fill, h / 2);
}

// ------------------------------------------------------------------ buttons
bool tool(const char* label, bool pressed, float min_w, const char* id) {
    font(g_app->f_med, 13);
    ImVec2 ts = ImGui::CalcTextSize(label, nullptr, true);
    ImVec2 sz(fmaxf(ts.x + px(26), min_w), px(36));
    ImGui::PushID(id ? id : label);
    bool click = ImGui::InvisibleButton("##t", sz);
    bool held = ImGui::IsItemActive();
    ImVec2 a = ImGui::GetItemRectMin(), b = ImGui::GetItemRectMax();
    ImDrawList* dl = ImGui::GetWindowDrawList();
    if (pressed) grad_rect(dl, a, b, px(10), T.accent, T.accent2); else dl->AddRectFilled(a, b, T.surface2, px(10));
    if (!pressed) dl->AddRect(a, b, T.border, px(10), px(1));
    if (held) dl->AddRectFilled(a, b, IM_COL32(255, 255, 255, 30), px(10));
    dl->AddText(ImVec2(a.x + (sz.x - ts.x) / 2, a.y + (sz.y - ts.y) / 2), pressed ? T.accent_ink : T.ink, label, ImGui::FindRenderedTextEnd(label));
    ImGui::PopID();
    pop();
    return click;
}
bool pill(const char* label, bool active, int icon, const char* id, float h) {
    font(g_app->f_med, 13);
    ImVec2 ts = ImGui::CalcTextSize(label, nullptr, true);
    float iw = icon ? px(20) : 0;
    ImVec2 sz(ts.x + iw + px(30), px(h));
    ImGui::PushID(id ? id : label);
    bool click = ImGui::InvisibleButton("##p", sz);
    ImVec2 a = ImGui::GetItemRectMin(), b = ImGui::GetItemRectMax();
    ImDrawList* dl = ImGui::GetWindowDrawList();
    if (active) { grad_rect(dl, a, b, sz.y / 2, T.accent, T.accent2); }
    else { dl->AddRectFilled(a, b, T.surface2, sz.y / 2); dl->AddRect(a, b, T.border, sz.y / 2, px(1)); }
    if (ImGui::IsItemActive()) dl->AddRectFilled(a, b, IM_COL32(255, 255, 255, 28), sz.y / 2);
    ImU32 fg = active ? T.accent_ink : T.ink;
    float x = a.x + px(15);
    if (icon) { draw_icon(dl, icon, ImVec2(x + px(8), (a.y + b.y) / 2), px(16), fg); x += iw; }
    dl->AddText(ImVec2(x, a.y + (sz.y - ts.y) / 2), fg, label, ImGui::FindRenderedTextEnd(label));
    ImGui::PopID();
    pop();
    return click;
}
bool primary(const char* label, int icon, bool amber, float w, const char* id, float h) {
    font(g_app->f_semi, 15);
    ImVec2 ts = ImGui::CalcTextSize(label, nullptr, true);
    float iw = icon ? px(26) : 0;
    ImVec2 sz(fmaxf(w, ts.x + iw + px(40)), px(h));
    ImGui::PushID(id ? id : label);
    bool click = ImGui::InvisibleButton("##b", sz);
    ImVec2 a = ImGui::GetItemRectMin(), b = ImGui::GetItemRectMax();
    ImDrawList* dl = ImGui::GetWindowDrawList();
    ImU32 c0 = amber ? IM_COL32(0xff, 0xc4, 0x3d, 255) : T.accent, c1 = amber ? IM_COL32(0xf5, 0x9e, 0x0b, 255) : T.accent2;
    glow(dl, a, b, sz.y / 2, amber ? IM_COL32(0xff, 0xb2, 0x1e, 90) : T.glow, px(5));
    grad_rect(dl, a, b, sz.y / 2, c0, c1);
    if (ImGui::IsItemActive()) dl->AddRectFilled(a, b, IM_COL32(0, 0, 0, 40), sz.y / 2);
    ImU32 fg = amber ? T.amber_ink : T.accent_ink;
    float x = a.x + (sz.x - ts.x - iw) / 2;
    dl->AddText(ImVec2(x, a.y + (sz.y - ts.y) / 2), fg, label, ImGui::FindRenderedTextEnd(label));
    if (icon) draw_icon(dl, icon, ImVec2(x + ts.x + px(16), (a.y + b.y) / 2), px(18), fg);
    ImGui::PopID();
    pop();
    return click;
}
bool link(const char* label, const char* id) {
    font(g_app->f_semi, 13);
    ImVec2 ts = ImGui::CalcTextSize(label, nullptr, true);
    ImGui::PushID(id ? id : label);
    ImVec2 p = ImGui::GetCursorScreenPos();
    bool click = ImGui::InvisibleButton("##l", ImVec2(ts.x + px(6), ts.y + px(10)));
    ImGui::GetWindowDrawList()->AddText(ImVec2(p.x, p.y + px(5)), ImGui::IsItemActive() ? T.ink : T.accent, label, ImGui::FindRenderedTextEnd(label));
    ImGui::PopID();
    pop();
    return click;
}
bool round_icon(const char* id, int ic, float size, ImU32 bg, ImU32 fg, bool border) {
    ImGui::PushID(id);
    float s = px(size);
    bool click = ImGui::InvisibleButton("##r", ImVec2(s, s));
    ImVec2 a = ImGui::GetItemRectMin();
    ImVec2 c(a.x + s / 2, a.y + s / 2);
    ImDrawList* dl = ImGui::GetWindowDrawList();
    if (bg) dl->AddCircleFilled(c, s / 2, bg, 32);
    if (border) dl->AddCircle(c, s / 2 - px(0.5f), T.border, 32, px(1));
    if (ImGui::IsItemActive()) dl->AddCircleFilled(c, s / 2, IM_COL32(255, 255, 255, 36), 32);
    draw_icon(dl, ic, c, s * 0.5f, fg);
    ImGui::PopID();
    return click;
}
bool checkbox(const char* label, bool* v) {
    font(g_app->f_body, 14);
    ImVec2 ts = ImGui::CalcTextSize(label);
    float box = px(20);
    ImGui::PushID(label);
    ImVec2 p = ImGui::GetCursorScreenPos();
    float h = fmaxf(box, ts.y) + px(10);
    bool click = ImGui::InvisibleButton("##c", ImVec2(box + px(10) + ts.x, h));
    if (click) *v = !*v;
    ImDrawList* dl = ImGui::GetWindowDrawList();
    float cy = p.y + h / 2;
    ImVec2 a(p.x, cy - box / 2), b(p.x + box, cy + box / 2);
    if (*v) { grad_rect(dl, a, b, px(5), T.accent, T.accent2); draw_icon(dl, IC_CHECK, ImVec2((a.x + b.x) / 2, cy), box * 0.8f, T.accent_ink); }
    else dl->AddRect(a, b, T.faint, px(5), px(1.5f));
    dl->AddText(ImVec2(b.x + px(10), cy - ts.y / 2), T.ink, label);
    ImGui::PopID();
    pop();
    return click;
}
bool toggle(const char* id, bool* v) {
    ImGui::PushID(id);
    ImVec2 sz(px(48), px(28));
    bool click = ImGui::InvisibleButton("##tg", sz);
    if (click) *v = !*v;
    ImVec2 a = ImGui::GetItemRectMin(), b = ImGui::GetItemRectMax();
    ImDrawList* dl = ImGui::GetWindowDrawList();
    // off state: a clearly visible grey track in both themes; the knob carries a soft shadow
    if (*v) grad_rect(dl, a, b, sz.y / 2, T.accent, T.accent2); else dl->AddRectFilled(a, b, T.dark ? T.surface2 : IM_COL32(0xc9, 0xd2, 0xe3, 255), sz.y / 2);
    dl->AddRect(a, b, T.border, sz.y / 2, px(1));
    float cx = *v ? b.x - sz.y / 2 : a.x + sz.y / 2;
    dl->AddCircleFilled(ImVec2(cx, (a.y + b.y) / 2 + px(1)), sz.y / 2 - px(3.5f), IM_COL32(0, 0, 0, 40), 24);
    dl->AddCircleFilled(ImVec2(cx, (a.y + b.y) / 2), sz.y / 2 - px(4), IM_COL32_WHITE, 24);
    ImGui::PopID();
    return click;
}
bool field(const char* id, const char* value, const char* ph, float w, int icon, float h) {
    font(g_app->f_body, 14);
    ImGui::PushID(id);
    float hh = px(h);
    ImVec2 p = ImGui::GetCursorScreenPos();
    bool click = ImGui::InvisibleButton("##f", ImVec2(w, hh));
    ImDrawList* dl = ImGui::GetWindowDrawList();
    ImVec2 b(p.x + w, p.y + hh);
    float r = icon ? hh / 2 : px(10);
    dl->AddRectFilled(p, b, T.field, r);
    dl->AddRect(p, b, ImGui::IsItemActive() ? T.accent : T.border, r, px(1));
    float x = p.x + px(14);
    if (icon) { draw_icon(dl, icon, ImVec2(x + px(9), p.y + hh / 2), px(18), T.muted); x += px(28); }
    bool empty = !value || !*value;
    dl->PushClipRect(p, ImVec2(b.x - px(8), b.y), true);
    dl->AddText(ImVec2(x, p.y + (hh - ImGui::GetTextLineHeight()) / 2), empty ? T.faint : T.ink, empty ? ph : value);
    dl->PopClipRect();
    ImGui::PopID();
    pop();
    return click;
}
bool section_header(const char* title, const char* action) {
    float w = ImGui::GetContentRegionAvail().x;
    ImVec2 p = ImGui::GetCursorScreenPos();
    ImDrawList* dl = ImGui::GetWindowDrawList();
    dl->AddRectFilled(ImVec2(p.x, p.y + px(4)), ImVec2(p.x + px(4), p.y + px(24)), T.amber, px(2));
    text_at(dl, g_app->f_bold, 19, ImVec2(p.x + px(14), p.y + px(1)), T.ink, title);
    bool click = false;
    if (action) {
        ImVec2 ts = text_size(g_app->f_med, 14, action);
        ImGui::SetCursorScreenPos(ImVec2(p.x + w - ts.x - px(24), p.y));
        ImGui::PushID(title);
        click = ImGui::InvisibleButton("##sh", ImVec2(ts.x + px(24), px(28)));
        ImGui::PopID();
        text_at(dl, g_app->f_med, 14, ImVec2(p.x + w - ts.x - px(22), p.y + px(4)), T.accent, action);
        draw_icon(dl, IC_ARROW_RIGHT, ImVec2(p.x + w - px(8), p.y + px(14)), px(14), T.accent);
        ImGui::SetCursorScreenPos(p);
    }
    ImGui::Dummy(ImVec2(w, px(36)));
    return click;
}

void card_begin(const char* id, float pad) {
    ImGui::PushStyleVar(ImGuiStyleVar_WindowPadding, ImVec2(px(pad + 2), px(pad)));
    ImGui::PushStyleVar(ImGuiStyleVar_ChildRounding, px(14));
    ImGui::PushStyleVar(ImGuiStyleVar_ChildBorderSize, px(1));
    ImGui::PushStyleColor(ImGuiCol_ChildBg, T.surface);
    ImGui::PushStyleColor(ImGuiCol_Border, T.border);
    ImGui::BeginChild(id, ImVec2(0, 0), ImGuiChildFlags_Borders | ImGuiChildFlags_AutoResizeY | ImGuiChildFlags_AlwaysUseWindowPadding, ImGuiWindowFlags_NoScrollbar | ImGuiWindowFlags_NoScrollWithMouse);
}
void card_end() {
    ImGui::EndChild();
    ImGui::PopStyleColor(2); ImGui::PopStyleVar(3);
    spacer(6);
}

// ------------------------------------------------------------------ icons
void star(ImDrawList* dl, ImVec2 c, float r, ImU32 col, bool filled) {
    ImVec2 pts[10];
    for (int i = 0; i < 10; i++) { float a = -(float)M_PI / 2 + i * (float)M_PI / 5, rr = (i & 1) ? r * 0.45f : r; pts[i] = ImVec2(c.x + cosf(a) * rr, c.y + sinf(a) * rr); }
    if (filled) dl->AddConcavePolyFilled(pts, 10, col);
    else dl->AddPolyline(pts, 10, col, fmaxf(1.f, r * 0.14f), ImDrawFlags_Closed);
}
static void arc(ImDrawList* dl, ImVec2 c, float r, float a0, float a1, ImU32 col, float t) { dl->PathArcTo(c, r, a0, a1, 24); dl->PathStroke(col, t); }
template <int N> static void poly(ImDrawList* dl, const ImVec2 (&p)[N], ImU32 col, float t, bool closed = false) { dl->AddPolyline(p, N, col, t, closed ? ImDrawFlags_Closed : 0); }
static void gear(ImDrawList* dl, ImVec2 c, float r, int teeth, ImU32 col, bool fill, float t) {
    Vec<ImVec2> p;
    for (int i = 0; i < teeth * 4; i++) {
        float a = (float)i / (teeth * 4) * 2 * (float)M_PI;
        float rr = (i % 4 == 1 || i % 4 == 2) ? r : r * 0.78f;
        p.push(ImVec2(c.x + cosf(a) * rr, c.y + sinf(a) * rr));
    }
    if (fill) dl->AddConcavePolyFilled(p.d, p.n, col); else dl->AddPolyline(p.d, p.n, col, t, ImDrawFlags_Closed);
}

void draw_icon(ImDrawList* dl, int ic, ImVec2 c, float s, ImU32 col) {
    float t = fmaxf(1.4f, s * 0.11f), h = s / 2;
    float x = c.x, y = c.y;
    switch (ic) {
        case IC_PREV: poly(dl, {{x + s * .15f, y - s * .3f}, {x - s * .15f, y}, {x + s * .15f, y + s * .3f}}, col, t); break;
        case IC_NEXT: poly(dl, {{x - s * .15f, y - s * .3f}, {x + s * .15f, y}, {x - s * .15f, y + s * .3f}}, col, t); break;
        case IC_CHEV_DOWN: poly(dl, {{x - s * .25f, y - s * .1f}, {x, y + s * .15f}, {x + s * .25f, y - s * .1f}}, col, t); break;
        case IC_STAR: star(dl, c, s * .45f, col, true); break;
        case IC_STAR_O: star(dl, c, s * .45f, col, false); break;
        case IC_CLOSE: dl->AddLine({x - s * .25f, y - s * .25f}, {x + s * .25f, y + s * .25f}, col, t); dl->AddLine({x + s * .25f, y - s * .25f}, {x - s * .25f, y + s * .25f}, col, t); break;
        case IC_SEARCH: dl->AddCircle({x - s * .07f, y - s * .07f}, s * .27f, col, 24, t); dl->AddLine({x + s * .13f, y + s * .13f}, {x + s * .36f, y + s * .36f}, col, t * 1.2f); break;
        case IC_PLAY: dl->AddTriangleFilled({x - s * .2f, y - s * .3f}, {x + s * .32f, y}, {x - s * .2f, y + s * .3f}, col); break;
        case IC_STOP: dl->AddRectFilled({x - s * .22f, y - s * .22f}, {x + s * .22f, y + s * .22f}, col, s * .05f); break;
        case IC_PAUSE: dl->AddRectFilled({x - s * .25f, y - s * .3f}, {x - s * .07f, y + s * .3f}, col, s * .04f); dl->AddRectFilled({x + s * .07f, y - s * .3f}, {x + s * .25f, y + s * .3f}, col, s * .04f); break;
        case IC_BACK: dl->AddLine({x - s * .32f, y}, {x + s * .32f, y}, col, t); poly(dl, {{x - s * .05f, y - s * .27f}, {x - s * .32f, y}, {x - s * .05f, y + s * .27f}}, col, t); break;
        case IC_ARROW_RIGHT: dl->AddLine({x - s * .32f, y}, {x + s * .32f, y}, col, t); poly(dl, {{x + s * .05f, y - s * .27f}, {x + s * .32f, y}, {x + s * .05f, y + s * .27f}}, col, t); break;
        case IC_HOME:
            poly(dl, {{x - s * .42f, y - s * .02f}, {x, y - s * .4f}, {x + s * .42f, y - s * .02f}}, col, t);
            poly(dl, {{x - s * .3f, y - s * .12f}, {x - s * .3f, y + s * .38f}, {x + s * .3f, y + s * .38f}, {x + s * .3f, y - s * .12f}}, col, t);
            dl->AddRectFilled({x - s * .08f, y + s * .12f}, {x + s * .08f, y + s * .38f}, col); break;
        case IC_GRID: for (int i = 0; i < 4; i++) { float ox = (i & 1) ? s * .06f : -s * .38f, oy = (i & 2) ? s * .06f : -s * .38f; dl->AddRect({x + ox, y + oy}, {x + ox + s * .32f, y + oy + s * .32f}, col, s * .07f, t); } break;
        case IC_CUBE: {
            ImVec2 tp(x, y - s * .42f), l(x - s * .38f, y - s * .2f), r(x + s * .38f, y - s * .2f), m(x, y + s * .02f), bl(x - s * .38f, y + s * .24f), br(x + s * .38f, y + s * .24f), bm(x, y + s * .46f);
            poly(dl, {tp, r, m, l}, col, t, true); poly(dl, {l, bl, bm, br, r}, col, t); dl->AddLine(m, bm, col, t); break; }
        case IC_BOOKMARK: poly(dl, {{x - s * .26f, y - s * .4f}, {x + s * .26f, y - s * .4f}, {x + s * .26f, y + s * .4f}, {x, y + s * .18f}, {x - s * .26f, y + s * .4f}}, col, t, true); break;
        case IC_BOOKMARK_FILL: { ImVec2 p[5] = {{x - s * .26f, y - s * .4f}, {x + s * .26f, y - s * .4f}, {x + s * .26f, y + s * .4f}, {x, y + s * .18f}, {x - s * .26f, y + s * .4f}}; dl->AddConcavePolyFilled(p, 5, col); break; }
        case IC_DOTS: for (int i = -1; i <= 1; i++) dl->AddCircleFilled({x + i * s * .32f, y}, s * .09f, col); break;
        case IC_ROTATE: arc(dl, c, s * .34f, -2.6f, 2.1f, col, t); { float a = 2.1f; ImVec2 e(x + cosf(a) * s * .34f, y + sinf(a) * s * .34f); dl->AddTriangleFilled({e.x - s * .14f, e.y - s * .02f}, {e.x + s * .08f, e.y - s * .14f}, {e.x + s * .06f, e.y + s * .1f}, col); } break;
        case IC_PLUS: dl->AddLine({x - s * .32f, y}, {x + s * .32f, y}, col, t); dl->AddLine({x, y - s * .32f}, {x, y + s * .32f}, col, t); break;
        case IC_MINUS: dl->AddLine({x - s * .32f, y}, {x + s * .32f, y}, col, t); break;
        case IC_EXPAND: case IC_COLLAPSE: {
            float o = s * .38f, k = s * .16f;
            for (int i = 0; i < 4; i++) { float sx = (i & 1) ? 1.f : -1.f, sy = (i & 2) ? 1.f : -1.f;
                ImVec2 cc(x + sx * o, y + sy * o);
                if (ic == IC_EXPAND) poly(dl, {{cc.x - sx * k, cc.y}, cc, {cc.x, cc.y - sy * k}}, col, t);
                else { ImVec2 ci(x + sx * o * .45f, y + sy * o * .45f); poly(dl, {{ci.x + sx * k, ci.y}, ci, {ci.x, ci.y + sy * k}}, col, t); } }
            break; }
        case IC_TARGET: dl->AddCircle(c, s * .28f, col, 24, t); for (int i = 0; i < 4; i++) { float a = i * (float)M_PI / 2; dl->AddLine({x + cosf(a) * s * .18f, y + sinf(a) * s * .18f}, {x + cosf(a) * s * .44f, y + sinf(a) * s * .44f}, col, t); } break;
        case IC_CAP: { ImVec2 p[4] = {{x, y - s * .32f}, {x + s * .46f, y - s * .1f}, {x, y + s * .12f}, {x - s * .46f, y - s * .1f}}; dl->AddConvexPolyFilled(p, 4, col);
            poly(dl, {{x - s * .26f, y + s * .02f}, {x - s * .26f, y + s * .26f}, {x, y + s * .38f}, {x + s * .26f, y + s * .26f}, {x + s * .26f, y + s * .02f}}, col, t);
            dl->AddLine({x + s * .4f, y - s * .08f}, {x + s * .4f, y + s * .28f}, col, t); break; }
        case IC_SCALES: dl->AddLine({x, y - s * .38f}, {x, y + s * .36f}, col, t); dl->AddLine({x - s * .2f, y + s * .36f}, {x + s * .2f, y + s * .36f}, col, t);
            dl->AddLine({x - s * .4f, y - s * .24f}, {x + s * .4f, y - s * .24f}, col, t);
            poly(dl, {{x - s * .4f, y - s * .24f}, {x - s * .52f, y + s * .06f}, {x - s * .28f, y + s * .06f}, {x - s * .4f, y - s * .24f}}, col, t);
            poly(dl, {{x + s * .4f, y - s * .24f}, {x + s * .28f, y + s * .06f}, {x + s * .52f, y + s * .06f}, {x + s * .4f, y - s * .24f}}, col, t); break;
        case IC_PLAYCIRCLE: dl->AddCircle(c, s * .42f, col, 32, t); dl->AddTriangleFilled({x - s * .12f, y - s * .2f}, {x + s * .22f, y}, {x - s * .12f, y + s * .2f}, col); break;
        case IC_GEAR: gear(dl, c, s * .45f, 8, col, false, t); dl->AddCircle(c, s * .15f, col, 20, t); break;
        case IC_HEADSET: arc(dl, ImVec2(x, y + s * .05f), s * .36f, (float)M_PI, 2 * (float)M_PI, col, t);
            dl->AddRectFilled({x - s * .44f, y + s * .02f}, {x - s * .26f, y + s * .34f}, col, s * .06f); dl->AddRectFilled({x + s * .26f, y + s * .02f}, {x + s * .44f, y + s * .34f}, col, s * .06f); break;
        case IC_INFO: dl->AddCircle(c, s * .42f, col, 32, t); dl->AddCircleFilled({x, y - s * .2f}, s * .06f, col); dl->AddLine({x, y - s * .05f}, {x, y + s * .24f}, col, t * 1.2f); break;
        case IC_CALC: dl->AddRect({x - s * .3f, y - s * .42f}, {x + s * .3f, y + s * .42f}, col, s * .08f, t); dl->AddRectFilled({x - s * .18f, y - s * .3f}, {x + s * .18f, y - s * .12f}, col, s * .03f);
            for (int i = 0; i < 6; i++) dl->AddCircleFilled({x - s * .14f + (i % 3) * s * .14f, y + s * .04f + (i / 3) * s * .17f}, s * .045f, col); break;
        case IC_LAYERS: for (int i = 0; i < 3; i++) { float oy = (i - 1) * s * .2f; poly(dl, {{x, y - s * .18f + oy}, {x + s * .42f, y + oy}, {x, y + s * .18f + oy}, {x - s * .42f, y + oy}}, col, t, true); } break;
        case IC_CUT: dl->AddCircle(c, s * .4f, col, 32, t); dl->PathArcTo(c, s * .4f, -(float)M_PI / 2, (float)M_PI / 2, 16); dl->PathFillConvex(col); break;
        case IC_EYE: { dl->PathArcTo({x, y + s * .5f}, s * .62f, -2.25f, -0.89f, 16); dl->PathArcTo({x, y - s * .5f}, s * .62f, 0.89f, 2.25f, 16); dl->PathStroke(col, t, ImDrawFlags_Closed);
            dl->AddCircleFilled(c, s * .13f, col); break; }
        case IC_FLOW: for (int k = 0; k < 2; k++) { float oy = (k ? s * .16f : -s * .16f); dl->PathClear();
            for (int i = 0; i <= 12; i++) { float u = i / 12.f; dl->PathLineTo({x - s * .42f + u * s * .84f, y + oy + sinf(u * 6.283f) * s * .1f}); } dl->PathStroke(col, t); } break;
        case IC_STEPS: case IC_LIST: for (int i = -1; i <= 1; i++) { dl->AddCircleFilled({x - s * .32f, y + i * s * .26f}, s * .06f, col); dl->AddLine({x - s * .16f, y + i * s * .26f}, {x + s * .38f, y + i * s * .26f}, col, t); } break;
        case IC_RULER: { ImVec2 p[4] = {{x - s * .46f, y + s * .14f}, {x + s * .14f, y - s * .46f}, {x + s * .46f, y - s * .14f}, {x - s * .14f, y + s * .46f}}; dl->AddPolyline(p, 4, col, t, ImDrawFlags_Closed);
            for (int i = 1; i < 5; i++) { float u = i / 5.f; ImVec2 a(p[0].x + (p[1].x - p[0].x) * u, p[0].y + (p[1].y - p[0].y) * u); dl->AddLine(a, {a.x + s * .1f, a.y + s * .1f}, col, t * .8f); } break; }
        case IC_WRENCH: dl->AddLine({x - s * .34f, y + s * .34f}, {x + s * .1f, y - s * .1f}, col, t * 1.6f); arc(dl, {x + s * .2f, y - s * .2f}, s * .2f, -2.6f, 1.0f, col, t * 1.2f); break;
        case IC_ALERT: poly(dl, {{x, y - s * .4f}, {x + s * .44f, y + s * .36f}, {x - s * .44f, y + s * .36f}}, col, t, true); dl->AddLine({x, y - s * .12f}, {x, y + s * .12f}, col, t); dl->AddCircleFilled({x, y + s * .24f}, s * .05f, col); break;
        case IC_CHECK: poly(dl, {{x - s * .3f, y}, {x - s * .08f, y + s * .22f}, {x + s * .32f, y - s * .2f}}, col, t * 1.2f); break;
        case IC_CLOCK: dl->AddCircle(c, s * .4f, col, 32, t); poly(dl, {{x, y - s * .24f}, c, {x + s * .18f, y + s * .1f}}, col, t); break;
        case IC_BOLT: { ImVec2 p[6] = {{x + s * .08f, y - s * .44f}, {x - s * .26f, y + s * .06f}, {x - s * .02f, y + s * .06f}, {x - s * .1f, y + s * .44f}, {x + s * .26f, y - s * .08f}, {x + s * .02f, y - s * .08f}}; dl->AddConcavePolyFilled(p, 6, col); break; }
        case IC_DROP: dl->AddCircle({x, y + s * .1f}, s * .26f, col, 24, t); poly(dl, {{x - s * .22f, y - s * .02f}, {x, y - s * .42f}, {x + s * .22f, y - s * .02f}}, col, t); break;
        case IC_GAUGE: arc(dl, {x, y + s * .1f}, s * .4f, -3.5f, 0.36f, col, t); dl->AddLine({x, y + s * .1f}, {x + s * .22f, y - s * .14f}, col, t * 1.2f); dl->AddCircleFilled({x, y + s * .1f}, s * .07f, col); break;
        case IC_ARROW_UP: dl->AddLine({x, y + s * .38f}, {x, y - s * .38f}, col, t); poly(dl, {{x - s * .24f, y - s * .12f}, {x, y - s * .38f}, {x + s * .24f, y - s * .12f}}, col, t); break;
        case IC_THERMO: dl->AddRect({x - s * .09f, y - s * .42f}, {x + s * .09f, y + s * .14f}, col, s * .09f, t); dl->AddCircleFilled({x, y + s * .26f}, s * .17f, col); break;
        case IC_TROPHY: arc(dl, {x, y - s * .14f}, s * .28f, 0.f, (float)M_PI, col, t); dl->AddLine({x - s * .28f, y - s * .14f}, {x + s * .28f, y - s * .14f}, col, t);
            dl->AddLine({x, y + s * .14f}, {x, y + s * .32f}, col, t); dl->AddLine({x - s * .2f, y + s * .36f}, {x + s * .2f, y + s * .36f}, col, t);
            arc(dl, {x - s * .3f, y - s * .04f}, s * .11f, 1.6f, 4.7f, col, t); arc(dl, {x + s * .3f, y - s * .04f}, s * .11f, -1.6f, 1.5f, col, t); break;
        case IC_BOOK: poly(dl, {{x, y - s * .26f}, {x - s * .44f, y - s * .36f}, {x - s * .44f, y + s * .3f}, {x, y + s * .38f}, {x + s * .44f, y + s * .3f}, {x + s * .44f, y - s * .36f}, {x, y - s * .26f}, {x, y + s * .38f}}, col, t); break;
        case IC_HAND: {   // pointing hand: index finger, folded fingers/palm, tap mark above the tip
            dl->AddRect({x - s * .07f, y - s * .40f}, {x + s * .09f, y + s * .06f}, col, s * .08f, t);
            dl->AddRect({x - s * .07f, y - s * .04f}, {x + s * .34f, y + s * .42f}, col, s * .12f, t);
            dl->AddLine({x - s * .07f, y + s * .10f}, {x - s * .26f, y - s * .02f}, col, t);
            dl->AddLine({x - s * .26f, y - s * .02f}, {x - s * .07f, y + s * .30f}, col, t);
            dl->AddLine({x + s * .16f, y - s * .04f}, {x + s * .16f, y + s * .10f}, col, t * .8f);
            dl->AddLine({x - s * .2f, y - s * .44f}, {x - s * .3f, y - s * .5f}, col, t * .8f);
            dl->AddLine({x + s * .22f, y - s * .44f}, {x + s * .32f, y - s * .5f}, col, t * .8f); break; }
        case IC_SPEAKER: { ImVec2 p[6] = {{x - s * .4f, y - s * .12f}, {x - s * .2f, y - s * .12f}, {x + s * .02f, y - s * .34f}, {x + s * .02f, y + s * .34f}, {x - s * .2f, y + s * .12f}, {x - s * .4f, y + s * .12f}}; dl->AddConcavePolyFilled(p, 6, col);
            arc(dl, {x + s * .02f, y}, s * .2f, -0.8f, 0.8f, col, t); arc(dl, {x + s * .02f, y}, s * .36f, -0.8f, 0.8f, col, t); break; }
        case IC_TAG: dl->AddCircle({x, y - s * .06f}, s * .3f, col, 24, t); dl->AddLine({x, y + s * .24f}, {x, y + s * .44f}, col, t); dl->AddCircleFilled({x, y - s * .06f}, s * .09f, col); break;
        case IC_TRASH: dl->AddLine({x - s * .36f, y - s * .26f}, {x + s * .36f, y - s * .26f}, col, t); poly(dl, {{x - s * .26f, y - s * .26f}, {x - s * .2f, y + s * .4f}, {x + s * .2f, y + s * .4f}, {x + s * .26f, y - s * .26f}}, col, t);
            dl->AddLine({x - s * .1f, y - s * .26f}, {x - s * .08f, y - s * .38f}, col, t); dl->AddLine({x + s * .1f, y - s * .26f}, {x + s * .08f, y - s * .38f}, col, t); break;
        case IC_MOON: dl->PathArcTo(c, s * .38f, 0.9f, 5.4f, 24); dl->PathArcTo({x + s * .16f, y - s * .1f}, s * .3f, 4.0f, 2.3f, 20); dl->PathStroke(col, t, ImDrawFlags_Closed); break;
        case IC_SUN: dl->AddCircle(c, s * .18f, col, 20, t); for (int i = 0; i < 8; i++) { float a = i * (float)M_PI / 4; dl->AddLine({x + cosf(a) * s * .3f, y + sinf(a) * s * .3f}, {x + cosf(a) * s * .44f, y + sinf(a) * s * .44f}, col, t); } break;
        case IC_SPARK: { ImVec2 p[8]; for (int i = 0; i < 8; i++) { float a = i * (float)M_PI / 4 - (float)M_PI / 2, r = (i & 1) ? s * .12f : s * .44f; p[i] = ImVec2(x + cosf(a) * r, y + sinf(a) * r); } dl->AddConcavePolyFilled(p, 8, col); break; }
    }
    (void)h;
}

// PumpForge mark: amber gear ring around a blue impeller
void logo(ImDrawList* dl, ImVec2 c, float r) {
    gear(dl, c, r, 10, IM_COL32(0xff, 0xb2, 0x1e, 255), true, 0);
    dl->AddCircleFilled(c, r * 0.62f, IM_COL32(0x0b, 0x17, 0x33, 255), 32);
    for (int i = 0; i < 5; i++) {
        float a0 = i * 2 * (float)M_PI / 5;
        dl->PathClear();
        for (int k = 0; k <= 8; k++) { float u = k / 8.f, rr = r * (0.12f + 0.42f * u), a = a0 + u * 1.1f; dl->PathLineTo(ImVec2(c.x + cosf(a) * rr, c.y + sinf(a) * rr)); }
        dl->PathStroke(IM_COL32(0x4d, 0x9b, 0xff, 255), fmaxf(1.5f, r * 0.12f));
    }
    dl->AddCircleFilled(c, r * 0.13f, IM_COL32(0xe8, 0xf0, 0xff, 255), 16);
}
void spinner(ImDrawList* dl, ImVec2 c, float r, ImU32 col, double t) {
    float a = (float)fmod(t * 5.0, 6.2832);
    dl->PathArcTo(c, r, a, a + 4.2f, 20); dl->PathStroke(col, fmaxf(1.5f, r * 0.16f));
}
}
