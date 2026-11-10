// PumpForge design system: dark industrial theme (navy / electric blue / amber), vector icons, cards and widgets.
#pragma once
#include "imgui.h"
#include "imgui_internal.h"
#include "app.h"

struct Theme {
    bool dark;
    ImU32 bg, bg2, surface, surface2, border, ink, muted, faint, accent, accent2, accent_ink, amber, amber_ink;
    ImU32 chip, chip_ink, good, bad, nav_bg, field, overlay_bg, label_bg, star, line, glow;
    V3 stage0, stage1;                 // 3-D stage gradient (sRGB)
};
extern Theme T;
void theme_set(bool dark);
ImU32 dept_color(int dept, int which);  // gradient top (0) / bottom (1) / accent (2) for a department

namespace ui {
extern float dp;
inline float px(float v) { return v * dp; }
void font(ImFont* f, float size_css);
void pop();
ImVec2 text_size(ImFont* f, float css, const char* s, float wrap = -1);
// text
void text(ImFont* f, float size, ImU32 col, const char* s, bool wrap = true);
void text_at(ImDrawList* dl, ImFont* f, float size, ImVec2 p, ImU32 col, const char* s, float wrap = 0);
void text_clipped(ImDrawList* dl, ImFont* f, float size, ImVec2 p, float maxw, ImU32 col, const char* s, int max_lines = 1);
void h2(const char* s);
void h3(const char* s);
void para(const char* s);
void muted(const char* s, float size = 12.5f);
void bullets(const JV& arr);
void chip(const char* s, bool same_line_first = false);
void chips_begin(); void chips_end();
void spacer(float h);
// shapes
void grad_rect(ImDrawList* dl, ImVec2 a, ImVec2 b, float r, ImU32 top, ImU32 bottom, ImDrawFlags fl = 0);
void card_bg(ImDrawList* dl, ImVec2 a, ImVec2 b, float r, ImU32 fill, bool border = true);
void glow(ImDrawList* dl, ImVec2 a, ImVec2 b, float r, ImU32 col, float spread);
void image(ImDrawList* dl, unsigned tex, ImVec2 a, ImVec2 b, float rounding, bool premultiplied);
void progress(ImDrawList* dl, ImVec2 a, float w, float h, float f, ImU32 fill, ImU32 track);
// buttons
bool tool(const char* label, bool pressed = false, float min_w = 0, const char* id = nullptr);
bool pill(const char* label, bool active, int icon = 0, const char* id = nullptr, float h = 34);
bool primary(const char* label, int icon, bool amber, float w = 0, const char* id = nullptr, float h = 44);
bool link(const char* label, const char* id = nullptr);
bool round_icon(const char* id, int icon, float size, ImU32 bg, ImU32 fg, bool border = false);
bool checkbox(const char* label, bool* v);
bool toggle(const char* id, bool* v);
bool field(const char* id, const char* value, const char* placeholder, float w, int icon = 0, float h = 40);
bool section_header(const char* title, const char* action = nullptr);
// cards (child windows that grow with their content)
void card_begin(const char* id, float pad = 12);
void card_end();
// icons (vector)
enum {
    IC_NONE = 0, IC_PREV, IC_NEXT, IC_STAR, IC_STAR_O, IC_CLOSE, IC_SEARCH, IC_CHEV_DOWN, IC_PLAY, IC_STOP, IC_BACK,
    IC_HOME, IC_GRID, IC_CUBE, IC_BOOKMARK, IC_BOOKMARK_FILL, IC_DOTS, IC_PAUSE, IC_ROTATE, IC_PLUS, IC_MINUS, IC_EXPAND,
    IC_COLLAPSE, IC_TARGET, IC_CAP, IC_SCALES, IC_PLAYCIRCLE, IC_GEAR, IC_HEADSET, IC_INFO, IC_CALC, IC_LAYERS, IC_CUT,
    IC_EYE, IC_FLOW, IC_STEPS, IC_RULER, IC_WRENCH, IC_ALERT, IC_CHECK, IC_CLOCK, IC_BOLT, IC_DROP, IC_GAUGE, IC_ARROW_UP,
    IC_THERMO, IC_TROPHY, IC_BOOK, IC_HAND, IC_SPEAKER, IC_TAG, IC_TRASH, IC_ARROW_RIGHT, IC_MOON, IC_SUN, IC_LIST, IC_SPARK,
};
void draw_icon(ImDrawList* dl, int icon, ImVec2 c, float s, ImU32 col);
void star(ImDrawList* dl, ImVec2 c, float r, ImU32 col, bool filled);
void logo(ImDrawList* dl, ImVec2 c, float r);
void spinner(ImDrawList* dl, ImVec2 c, float r, ImU32 col, double t);
}
