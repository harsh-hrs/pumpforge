// PumpForge native app: state shared by the data, scene and UI modules.
#pragma once
#include "base.h"
#include "json.h"
#include "model.h"
#include "render.h"
#include "plat.h"

struct ImRect_ { float x0, y0, x1, y1; };

struct ImFont;

// ------------------------------------------------------------------ persistent per-device store (bookmarks, progress, notes, datasheets)
struct Store {
    struct Prog { double seen = 0; int best = -1; };
    struct DS { Str manufacturer, model; Vec<Str> keys, vals; bool set = false; };
    struct Entry { Str id; Prog prog; bool star = false; Str notes; DS ds; };
    Vec<Entry> e;
    bool narrate = false;
    int theme = 1;            // 0 = follow system, 1 = dark, 2 = light
    bool live_default = true, markers_default = false;
    Str last;                 // last module opened in the 3-D viewer
    bool dirty = false;
    Entry& get(const char* id);
    const Entry* find(const char* id) const;
    void load();
    void save();
};

// ------------------------------------------------------------------ catalogue
struct ModInfo { Str id, title, category, department, eq_id, subcategory, hay, area; int no = 0, phase = 0, dept = -1, tours = 0, quizq = 0, area_idx = -1; bool flagship = false, m2p = false; };
struct DeptInfo { Str id, name, status; int modules = 0; bool m2p = false; };
// Mine-to-Port catalog: plant areas in process order (from learning/m2p.json)
struct AreaInfo { Str id, name, icon; int modules = 0; };

// ------------------------------------------------------------------ orbit camera (three.js OrbitControls behaviour)
struct Orbit {
    V3 target, pos{3, 2, 4};
    float fov = 32, near_ = 0.01f, far_ = 200;
    float d_theta = 0, d_phi = 0; V3 d_pan;            // damped deltas
    bool auto_rotate = false; float auto_speed = 1.2f;
    void rotate(float left, float up) { d_theta -= left; d_phi -= up; }
    void pan(float dx, float dy, float vh);             // pixels
    void dolly(float scale);                            // >1 = zoom out
    void update(float dt);
    M4 view() const { return m4_lookat(pos, target, V3(0, 1, 0)); }
    M4 proj(float aspect) const { return m4_persp(fov * (float)M_PI / 180.f, aspect, near_, far_); }
};

struct Overlay { Str kind; Model* m = nullptr; bool xray = false; bool on = false; };
struct Label { Str kind, text; V3 p; };
struct Flow { Vec<V3> pts; Vec<float> cum, speed, u; Vec<float> active; float L = 0, r = 0, base = 0; int n = 0; V3 color; bool on = true; };

enum Tab { TAB_OVERVIEW, TAB_PARTS, TAB_WORKING, TAB_OPERATION, TAB_PARAMS, TAB_CARE, TAB_FAILURES, TAB_TOURS, TAB_QUIZ, TAB_TOOLS, TAB_COUNT };
enum Screen { SCR_HOME, SCR_CATALOG, SCR_VIEWER, SCR_BOOKMARKS, SCR_MORE };
enum MorePage { MP_NONE, MP_PATHS, MP_COMPARE, MP_CALCS, MP_TRAINING, MP_SETTINGS, MP_HELP, MP_ABOUT };

// Live 3-D thumbnails: each module model rendered once into a small texture (no images shipped in the APK).
struct Thumb { int mod = -1; unsigned tex = 0, fbo = 0; int used = 0; int requested = -10; bool ready = false; bool failed = false; };

struct App {
    // ---- platform / display
    int fbw = 0, fbh = 0; float dp = 1;                 // dp = pixels per CSS px
    float inset_top = 0, inset_bottom = 0, inset_left = 0, inset_right = 0;
    bool dark = false;
    Renderer R;
    bool gl_ready = false;
    double t_last = 0;
    ImFont *f_body = nullptr, *f_med = nullptr, *f_semi = nullptr, *f_bold = nullptr, *f_disp = nullptr, *f_mono = nullptr, *f_monom = nullptr;
    bool sys_dark = false;                               // system night mode (theme 0 follows it)

    // ---- data
    JDoc index;
    Vec<ModInfo> mods; Vec<DeptInfo> depts;
    Store store;
    int cur = -1;                                        // index into mods
    JDoc meta, learn;
    Model* model = nullptr;
    Str load_error;
    int pending_load = -1; int pending_frames = 0;

    // ---- scene state (mirrors library.html)
    bool operate = false, cut = false, xray = false, live = true, measuring = false;
    float explode = 0, anim_t = 0; bool anim_started = false; int op_anim = -1;
    Vec<bool> node_vis;                                  // effective visibility per node
    Vec<uint8_t> node_static, node_fluid;               // per mesh node
    Vec<Str> hidden;                                     // hidden part ids
    Str selected;                                        // inspected part
    Vec<Str> hl; double flash_until = 0; Str flash_part;   // highlighted parts (selection, flash, step/tour)
    Vec<int> prim_base; Vec<uint8_t> prim_vis;          // per (node, primitive) visibility for drawing and picking
    Vec<Overlay> overlays; Vec<Label> labels;
    Vec<Flow> flows; float model_size = 1;
    Orbit cam; float ground_y = 0; Box full_box; V3 sun_c; float sun_s = 1;
    V3 m_pts[2]; int m_n = 0; bool m_line = false; V3 m_a, m_b; Str m_text;
    // steps / tours
    int step_idx = -1; bool step_auto = false; double step_next = 0;
    int tour_n = -1, tour_i = -1; double tour_scene_end = 0, tour_scene_start = 0; bool tour_spoken = false; Str caption_head, caption;

    // ---- UI state
    int screen = SCR_HOME; Vec<int> nav_stack;           // back stack of screens
    int more_page = MP_NONE;
    int tab = TAB_OVERVIEW;
    bool picker_open = false, fullscreen = false, markers = true; int picker_mode = 0;   // 0 open, 1 compare (tools), 2/3 compare page A/B
    Str pick_query;   // picker search (name, EQ number, component…)
    Str cat_query; int cat_dept = -1; bool cat_saved = false; // catalog filters (-1 = all departments)
    int cat_coll = 0;                                    // 0 Equipment Library, 1 Mine to Port
    int m2p_area = -1;                                   // open plant area page (-1 = Mine-to-Port overview)
    JDoc m2p; Vec<AreaInfo> areas;                       // Mine-to-Port overview data
    int bm_tab = 0; int path_open = -1; int cmp_a = -1;
    Vec<int> quiz;                                       // answer per question (-1 = none)
    int cmp_mod = -1; JDoc cmp_learn; JDoc cmp_learn_a;
    Vec<double> calc_vals; Vec<Str> calc_keys;           // calculator inputs (session)
    Str calc_open;                                       // expanded calculator on the calculators page
    Str ds_msg; bool reset_confirm = false;
    bool more_calcs = false;
    float page_scroll_reset = -1; bool scroll_to_tabs = false; float tabs_y = 0;
    int feat_idx = 0; Vec<int> featured; Vec<Str> featured_desc;
    float explode_target = -1;                           // animated explode (Exploded View segment)
    double last_interact = 0;
    // render targets
    Target stage_rt, hero_rt; Model* hero = nullptr; float hero_yaw = 0; int hero_mod = -1; bool hero_wanted = false;
    Vec<Thumb> thumbs; int thumb_clock = 0; Target thumb_rt;
    Vec<ImRect_> blockers;                               // stage controls (touches there are not orbit gestures)
    bool stage_visible = false; float stage_clip_y0 = 0, stage_clip_y1 = 0;
    // text entry
    int text_target = 0; Str text_key; Str text_value;
    // touch / gestures
    struct Ptr { int id; float x, y, sx, sy; bool down; };
    Vec<Ptr> ptrs; bool stage_gesture = false, ui_gesture = false, gesture_moved = false;
    float pinch_d = 0; float pinch_mx = 0, pinch_my = 0;
    bool scroll_drag = false; void* scroll_win = nullptr; float scroll_vy = 0, scroll_vx = 0; bool scroll_h = false; bool gesture_pending = false; bool slider_active = false;
    float prim_x = 0, prim_y = 0, last_x = 0, last_y = 0; double kin_t = 0;
    Vec<TouchEvent> pending_touch;
    float stage_x = 0, stage_y = 0, stage_w = 0, stage_h = 0;   // in pixels, top-left origin
    bool toast_on = false; Str toast; double toast_until = 0;

    // ---- lifecycle
    bool init(float density, bool dark_mode, char* err, int errlen);
    bool gl_init(char* err, int errlen);
    void gl_lost();
    void resize(int w, int h) { fbw = w; fbh = h; }
    void touch(const TouchEvent& e) { pending_touch.push(e); }
    bool back();
    void frame(double now);
    void shutdown();

    // ---- data (app_data.cpp)
    bool load_index(char* err, int errlen);
    void request_load(int idx);
    void do_load(int idx);
    void unload();
    int mod_index(const char* id) const;
    const JV& S() const { return (*learn.root)["sections"]; }
    const JV& M() const { return *meta.root; }
    bool loaded() const { return model && meta.root && learn.root; }

    // ---- scene (scene.cpp)
    void apply_state();
    void frame_box(const Box& b, V3 dir, float tight);
    void frame_full();
    void frame_part(const char* id);
    void build_particles();
    void update_particles(float dt);
    float phase_now() const;
    void toggle_overlay(const char* kind, bool on);
    void set_overlay_exclusive(const char* kind);
    bool overlay_on(const char* kind) const;
    void clear_overlays();
    void run_action(const JV& a, bool force_operate);
    void show_step(int i);
    void close_steps();
    void play_tour(int n);
    void stop_tour();
    void tour_tick(double now);
    void hl_set(const char* id, bool on);
    bool hl_has(const char* id) const;
    void flash(const char* id, double now);
    void select(const char* id);
    void tap_stage(float x, float y);
    void clear_measure();
    int part_index(const char* id) const;                 // index into meta.parts
    bool has_part_node(const char* id) const;            // web: parts[id] (node with explode_offset)
    void render_scene();
    void stage_input(float dt);

    // ---- UI (ui.cpp, ui_screens.cpp, ui_viewer.cpp)
    void setup_style();
    void apply_theme();
    bool is_dark() const { return store.theme == 0 ? sys_dark : store.theme == 1; }
    void build_ui(float dt);
    void go(int scr);                                    // switch screen (pushes the back stack)
    void open_module(int idx, int tab_ = -1);            // open the 3-D viewer on a module
    void ui_nav(float x, float y, float w, float h);
    void ui_home(float x, float y, float w, float h);
    void ui_catalog(float x, float y, float w, float h);
    void ui_m2p(float x, float y, float w, float h);
    bool has_tab(int t);
    void ui_bookmarks(float x, float y, float w, float h);
    void ui_more(float x, float y, float w, float h);
    void ui_more_page(float x, float y, float w, float h);
    void ui_viewer(float x, float y, float w, float h);
    void ui_stage(float x, float y, float w, float h);
    void ui_tabs_bar(float w, bool sticky);
    void ui_tab(int t);
    void ui_inspector();
    void ui_picker();
    void ui_tools();
    void ui_compare(int a, int b, const JV& la, const JV& lb);
    void calc_card(const struct Calc& c, bool collapsible);
    void ui_text_poll();
    void begin_text(int target, const char* key, const char* title, const char* initial, plat::InputKind kind);
    void process_touch(float dt);
    void show_toast(const char* msg);
    // thumbnails / hero
    unsigned thumb(int mod);                             // texture or 0 (queued)
    void thumbs_update();
    void hero_update(float dt);
    void render_model_to(Model& m, Target& t, float yaw, float tight, bool transparent);
};

extern App* g_app;
