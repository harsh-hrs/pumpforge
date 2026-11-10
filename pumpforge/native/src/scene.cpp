// 3-D scene behaviour: a line-by-line port of library.html (applyState, framing, overlays, live flow,
// step player, tours, highlight, inspector selection, picking, measuring).
#include "app.h"
#include "glapi.h"
#include <stdio.h>

static V3 jv3(const JV& a) { return V3((float)a[0].n(), (float)a[1].n(), (float)a[2].n()); }

// ------------------------------------------------------------------ orbit camera
void Orbit::pan(float dx, float dy, float vh) {
    // OrbitControls.pan (perspective): move target by screen delta at the target distance
    V3 off = pos - target;
    float td = len(off) * tanf(fov / 2 * (float)M_PI / 180.f);
    M4 v = view();
    V3 right(v.m[0], v.m[4], v.m[8]), up(v.m[1], v.m[5], v.m[9]);
    d_pan += right * (-2 * dx * td / vh) + up * (2 * dy * td / vh);
}
void Orbit::dolly(float scale) {
    V3 off = pos - target;
    float r = pf_clamp(len(off) * scale, 1e-3f, 1e4f);
    pos = target + norm(off) * r;
}
void Orbit::update(float dt) {
    // spherical coordinates around +Y (three.js Spherical)
    V3 off = pos - target;
    float r = len(off);
    if (r < 1e-6f) r = 1e-6f;
    float theta = atan2f(off.x, off.z), phi = acosf(pf_clamp(off.y / r, -1.f, 1.f));
    float k = 1.f - powf(1.f - 0.05f, pf_clamp(dt, 0.f, 0.1f) * 60.f);   // dampingFactor 0.05 per 60 Hz frame
    if (auto_rotate) theta -= 2 * (float)M_PI / 60.f * auto_speed * dt;
    theta += d_theta * k; phi += d_phi * k;
    phi = pf_clamp(phi, 1e-6f, (float)M_PI - 1e-6f);
    target += d_pan * k;
    d_theta *= (1 - k); d_phi *= (1 - k); d_pan = d_pan * (1 - k);
    pos = target + V3(r * sinf(phi) * sinf(theta), r * cosf(phi), r * sinf(phi) * cosf(theta));
}

// ------------------------------------------------------------------ helpers
int App::part_index(const char* id) const {
    int i = 0; for (const JV& p : M()["parts"]) { if (streq(p["id"].str(), id)) return i; i++; }
    return -1;
}
bool App::has_part_node(const char* id) const {
    if (!model || !id || !*id) return false;
    for (const Node& n : model->nodes) if (n.mesh < 0 && n.has_explode && n.part_id.eq(id)) return true;
    return false;
}
void App::hl_set(const char* id, bool on) {
    for (int i = 0; i < hl.n; i++) if (hl[i].eq(id)) { if (!on) hl.erase(i); return; }
    if (on && id && *id) hl.push(Str(id));
}
bool App::hl_has(const char* id) const { for (const Str& s : hl) if (s.eq(id)) return true; return false; }
static bool contains(const Vec<Str>& v, const char* s) { for (const Str& x : v) if (x.eq(s)) return true; return false; }

// ------------------------------------------------------------------ applyState
void App::apply_state() {
    if (!model) return;
    Model& md = *model;
    int n = md.nodes.n;
    prim_base.resize(n);
    int tot = 0;
    for (int i = 0; i < n; i++) { prim_base[i] = tot; if (md.nodes[i].mesh >= 0) tot += md.meshes[md.nodes[i].mesh].prims.n; }
    prim_vis.resize(tot);
    for (int i = 0; i < n; i++) {
        const Node& nd = md.nodes[i];
        bool own = !(nd.section_role.eq("front") || nd.section_role.eq("hide")) || !cut;
        bool par = nd.parent >= 0 ? node_vis[nd.parent] : true;
        node_vis[i] = own && par;
        if (nd.mesh < 0) continue;
        const char* pid = nd.part >= 0 ? md.nodes[nd.part].part_id.c() : "";
        bool hid = contains(hidden, pid);
        const Mesh& me = md.meshes[nd.mesh];
        for (int k = 0; k < me.prims.n; k++) {
            int mi = me.prims[k].mat;
            bool sec = mi >= 0 && mi < md.mats.n && md.mats[mi].section;
            bool v;
            // a single-primitive mesh node is itself the three.js Mesh: its section material overrides the role rule
            if (sec) v = cut && (me.prims.n == 1 ? par : node_vis[i]);
            else v = node_vis[i];
            prim_vis[prim_base[i] + k] = (uint8_t)(v && !hid);
        }
    }
    if (operate && op_anim >= 0) anim_started = true;   // actions.Operate.play()
}

// per frame: pose = rest -> Operate clip (if started) -> explode offsets
static void pose(App& a) {
    Model& md = *a.model;
    for (Node& n : md.nodes) { n.t = n.t0; n.r = n.r0; n.s = n.s0; if (n.mesh >= 0) for (int k = 0; k < 2; k++) n.w[k] = md.meshes[n.mesh].w0[k]; }
    if (a.anim_started && a.op_anim >= 0) a.model->sample(a.op_anim, a.anim_t);
    for (Node& n : md.nodes) if (n.mesh < 0 && n.has_explode && !n.part_id.empty()) n.t = n.t + n.explode * a.explode;
    md.update_world();
}

// ------------------------------------------------------------------ camera framing
void App::frame_box(const Box& b, V3 dir, float tight) {
    if (!b.valid() || !model) return;
    V3 c = b.center(), sz = b.size();
    float aspect = stage_h > 0 ? stage_w / stage_h : 1;
    float vf = cam.fov * (float)M_PI / 180.f / 2, hf = atanf(tanf(vf) * aspect);
    float d = fmaxf(sz.y / 2 / tanf(vf), fmaxf(sz.x, sz.z) / 2 / tanf(hf)) * tight + fmaxf(sz.x, sz.z) / 2;
    cam.pos = c + norm(dir) * d; cam.target = c;
    cam.near_ = fmaxf(d / 200, 0.005f); cam.far_ = d * 20;
    cam.d_theta = cam.d_phi = 0; cam.d_pan = V3();
    Box full = model->bounds(nullptr);
    sun_c = full.center(); sun_s = len(full.size());
}
void App::frame_full() { if (model) { pose(*this); frame_box(model->bounds(nullptr), V3(0.85f, 0.45f, 1.1f), 1.15f); } }
void App::frame_part(const char* id) {
    int pi = part_index(id); if (pi < 0 || !model) return;
    const JV& p = M()["parts"][pi];
    Box b; b.add(jv3(p["bbox_min"])); b.add(jv3(p["bbox_max"]));
    float fsz = len(model->bounds(nullptr).size()), e = fmaxf(0.12f * fsz, 0.05f);
    b.lo -= V3(e, e, e); b.hi += V3(e, e, e);
    frame_box(b, V3(0.7f, 0.35f, 1.1f), 1.25f);
}

// ------------------------------------------------------------------ overlays
bool App::overlay_on(const char* k) const { for (const Overlay& o : overlays) if (o.kind.eq(k)) return o.on; return false; }
void App::clear_overlays() {
    for (Overlay& o : overlays) { if (o.m) { o.m->release(); delete o.m; } }
    overlays.clear(); labels.clear();
}
void App::toggle_overlay(const char* k, bool on) {
    const JV& info = M()["overlays"][k];
    if (!info.isObj()) return;
    for (int i = labels.n - 1; i >= 0; i--) if (labels[i].kind.eq(k)) labels.erase(i);
    Overlay* o = nullptr;
    for (Overlay& x : overlays) if (x.kind.eq(k)) o = &x;
    if (o) o->on = false;
    if (!on) return;
    if (!o) {
        Model* m = new Model(); char err[200];
        Str path = Str::f("models/%s_%s.pfm", mods[cur].id.c(), k);
        if (!m->load(path, err, sizeof err)) { pf_log("overlay %s: %s", path.c(), err); delete m; return; }
        m->upload();
        o = &overlays.push(); o->kind = k; o->m = m; o->xray = streq(info["render"].str(), "xray");
    }
    o->on = true;
    for (const JV& a : info["annotations"]) { Label& l = labels.push(); l.kind = k; l.text = a["text"].str(); l.p = jv3(a["anchor"]); }
}
void App::set_overlay_exclusive(const char* k) {
    for (const JV& o : M()["overlays"]) { bool want = k && streq(o.key, k); if (overlay_on(o.key) != want) toggle_overlay(o.key, want); }
}

// ------------------------------------------------------------------ live flow particles (meta.flow_paths)
static uint32_t kind_col(const char* k) {
    struct { const char* k; uint32_t c; } T[] = {{"flow_suction", 0x2b95ff}, {"flow_discharge", 0xff6a1f}, {"air", 0x7cc832}, {"water", 0x3d8fd6}, {"steam", 0xe8eef3},
        {"hydraulic_oil", 0xe0a526}, {"flame", 0xff5a00}, {"electric", 0xffcc00}, {"flue_gas", 0x9c8878}, {"exhaust", 0xd2742a}, {"heat", 0xff3b30}, {"power", 0xd63384}, {"sand", 0xc8b38a}};
    for (auto& t : T) if (streq(t.k, k)) return t.c;
    return 0x2b95ff;
}
void App::build_particles() {
    flows.clear();
    if (!model) return;
    pose(*this);
    model_size = len(model->bounds(nullptr).size());
    for (const JV& fp : M()["flow_paths"]) {
        Flow f;
        for (const JV& q : fp["points"]) f.pts.push(jv3(q));
        if (f.pts.n < 2) continue;
        f.cum.push(0); for (int i = 1; i < f.pts.n; i++) f.cum.push(f.cum[i - 1] + len(f.pts[i] - f.pts[i - 1]));
        f.L = f.cum.back(); if (f.L <= 0) continue;
        double rad = fp["radius"].truthy() ? fp["radius"].n() : 0.01;
        f.r = (float)fmax(0.0025, fmin(0.03, rad * 0.95));
        f.n = (int)fmax(6.0, fmin(80.0, round(f.L / (f.r * 7))));
        f.color = hex_linear(kind_col(fp["kind"].str()));
        for (int i = 0; i < f.n; i++) f.u.push((float)i / f.n);
        for (const JV& s : fp["speed"]) f.speed.push((float)s.n());
        for (const JV& a : fp["active"]) { f.active.push((float)a[0].n()); f.active.push((float)a[1].n()); }
        f.base = fmaxf(0.08f, model_size * 0.12f);
        flows.push(f);
    }
}
float App::phase_now() const {
    if (!model || op_anim < 0) return 0;
    float d = model->anims[op_anim].dur; if (d <= 0) return 0;
    return fmodf(anim_t, d) / d;
}
void App::update_particles(float dt) {
    if (!flows.n || !live) return;
    float ph = phase_now();
    for (Flow& p : flows) {
        bool on = p.active.n == 0;
        for (int i = 0; i + 1 < p.active.n; i += 2) if (ph >= p.active[i] && ph <= p.active[i + 1]) on = true;
        p.on = on;
        if (!on) continue;
        for (int i = 0; i < p.n; i++) {
            float s = fmodf(p.u[i], 1.f) * p.L; int k = 1;
            while (k < p.cum.n - 1 && p.cum[k] < s) k++;
            float t = (s - p.cum[k - 1]) / fmaxf(1e-9f, p.cum[k] - p.cum[k - 1]);
            float f = p.speed.n > k ? (p.speed[k - 1] + (p.speed[k] - p.speed[k - 1]) * t) : 1;
            p.u[i] = fmodf(p.u[i] + dt * p.base * f / p.L, 1.f);
        }
    }
}

// ------------------------------------------------------------------ actions, steps, tours
void App::run_action(const JV& a, bool force_operate) {
    if (!model) return;
    if (a.has("cut")) cut = a["cut"].truthy();
    if (force_operate) operate = true; else if (a.has("operate")) operate = a["operate"].truthy();
    if (a.has("explode")) explode = pf_clamp((float)a["explode"].n(0), 0.f, 1.f);
    if (a.has("overlay")) set_overlay_exclusive(a["overlay"].isStr() && a["overlay"].slen ? a["overlay"].str() : nullptr);
    hl.clear();
    const char* h = a["highlight"].str();
    if (*h && has_part_node(h)) hl_set(h, true);
    const char* v = a["view"].str();
    cam.auto_rotate = streq(v, "orbit"); cam.auto_speed = 1.2f;
    apply_state(); pose(*this);
    Box full = model->bounds(nullptr);
    if (streq(v, "part") && *h) frame_part(h);
    else if (streq(v, "front")) frame_box(full, V3(0, 0.0001f, 1), 1.15f);
    else if (streq(v, "iso") || streq(v, "orbit")) frame_box(full, V3(0.85f, 0.45f, 1.1f), 1.15f);
}

void App::show_step(int i) {
    const JV& st = S()["working_principle"]["steps"];
    if (!st.size()) return;
    step_idx = ((i % st.size()) + st.size()) % st.size();
    const JV& s = st[step_idx];
    // web: runAction({cut: s.cut, operate: true, overlay: s.overlay || null, highlight: s.part, explode: s.explode || 0, view: s.part ? 'part' : 'front'})
    JDoc tmp; JW w; w.beginObj();
    if (s.has("cut")) { w.key("cut"); json_write_value(w, s["cut"]); }
    w.key("overlay"); if (s["overlay"].truthy()) json_write_value(w, s["overlay"]); else w.null();
    w.key("highlight"); json_write_value(w, s["part"]);
    w.key("explode").num(s["explode"].n(0));
    w.key("view").str(s["part"].truthy() ? "part" : "front");
    w.endObj();
    tmp.parse(w.o.c(), (size_t)w.o.n);
    run_action(*tmp.root, true);
    if (store.narrate) plat::speak(s["text"].str());
    if (step_auto) step_next = plat::now() + 6.0;
}
void App::close_steps() { step_idx = -1; step_auto = false; }

void App::stop_tour() {
    if (tour_n < 0) return;
    tour_n = -1; tour_i = -1; caption.clear(); cam.auto_rotate = false;
    plat::stop_speaking();
}
void App::play_tour(int n) {
    stop_tour();
    const JV& v = S()["video_tutorials"][n];
    if (!v.isObj() || !v["script"].size()) return;
    tour_n = n; tour_i = -1; tour_scene_end = 0;
    tour_tick(plat::now());
}
void App::tour_tick(double now) {
    if (tour_n < 0 || !loaded()) return;
    const JV& v = S()["video_tutorials"][tour_n];
    if (tour_i >= 0) {
        if (now < tour_scene_end) return;
        // with narration, wait for the speech to finish too (as the browser version does)
        if (tour_spoken && plat::speaking() && now < tour_scene_end + 30) return;
    }
    tour_i++;
    if (tour_i >= v["script"].size()) { stop_tour(); return; }
    const JV& l = v["script"][tour_i];
    run_action(l["action"], false);
    caption_head = Str::f("%s · %d/%d", v["title"].str(), tour_i + 1, v["script"].size());
    caption = l["narration"].str();
    tour_spoken = false;
    if (store.narrate) { plat::speak(l["narration"].str()); tour_spoken = plat::tts_available(); }
    tour_scene_start = now; tour_scene_end = now + l["duration_s"].n(4);
}

// ------------------------------------------------------------------ highlight / select
void App::flash(const char* id, double now) {
    if (!selected.empty()) hl_set(selected, false);
    hl_set(id, true); flash_part = id; flash_until = now + 2.6;
}
void App::select(const char* id) {
    if (!selected.empty()) hl_set(selected, false);
    if (!id || !*id || part_index(id) < 0) { selected.clear(); return; }
    selected = id; hl_set(id, true);
}

// ------------------------------------------------------------------ picking + measure
void App::clear_measure() { m_n = 0; m_line = false; m_text = measuring ? "Measure: tap two points" : ""; }
void App::tap_stage(float x, float y) {
    if (!loaded()) return;
    float nx = (x - stage_x) / stage_w * 2 - 1, ny = -((y - stage_y) / stage_h * 2 - 1);
    M4 ivp = m4_inverse(cam.proj(stage_w / stage_h) * cam.view());
    float a[4], b[4];
    auto unp = [&](float z, float* o) { const float* m = ivp.m; float v[4] = {nx, ny, z, 1};
        for (int r = 0; r < 4; r++) o[r] = m[r] * v[0] + m[4 + r] * v[1] + m[8 + r] * v[2] + m[12 + r] * v[3]; };
    unp(-1, a); unp(1, b);
    V3 p0(a[0] / a[3], a[1] / a[3], a[2] / a[3]), p1(b[0] / b[3], b[1] / b[3], b[2] / b[3]);
    Ray r{p0, norm(p1 - p0)};
    Hit h = model->pick(r, prim_vis.d, prim_base.d);
    if (measuring) {
        if (!h.ok) return;
        m_pts[m_n++] = h.p;
        if (m_n == 1) { m_text = "Measure: tap the second point"; return; }
        m_a = m_pts[0]; m_b = m_pts[1]; m_line = true; m_n = 0;
        m_text = Str::f("Distance ≈ %s mm (model scale)", js_fixed(len(m_b - m_a) * 1000.0, 0).c());
        return;
    }
    const char* pid = "";
    if (h.ok) { int k = model->nodes[h.node].part; if (k >= 0) pid = model->nodes[k].part_id.c(); }
    select(pid);
}

// ------------------------------------------------------------------ draw
void App::render_scene() {
    if (!model) return;
    pose(*this);
    Vec<DrawItem> items;
    auto add_model = [&](Model& md, bool main, bool xr) {
        for (int i = 0; i < md.nodes.n; i++) {
            const Node& nd = md.nodes[i];
            if (nd.mesh < 0) continue;
            const Mesh& me = md.meshes[nd.mesh];
            bool nv = true;
            if (!main) { // overlay: role 'front' hidden in cutaway; inherit parent visibility
                for (int k = i; k >= 0; k = md.nodes[k].parent) if (md.nodes[k].section_role.eq("front") && cut) nv = false;
                if (!nv) continue;
            }
            const char* pid = main && nd.part >= 0 ? md.nodes[nd.part].part_id.c() : "";
            for (int k = 0; k < me.prims.n; k++) {
                if (main && !prim_vis[prim_base[i] + k]) continue;
                const Prim& p = me.prims[k];
                DrawItem it; it.p = &p; it.m = p.mat >= 0 && p.mat < md.mats.n ? &md.mats[p.mat] : nullptr; it.world = nd.world; it.w[0] = nd.w[0]; it.w[1] = nd.w[1];
                bool sec = it.m && it.m->section;
                if (main) {
                    bool ghost = xray && node_static[i];
                    if (!sec) { bool fl = node_fluid[i] && !ghost; it.transparent = ghost || fl; it.opacity = ghost ? 0.14f : (fl ? 0.55f : 1.f); it.depth_write = !(ghost || fl); }
                    it.highlight = !sec && *pid && hl_has(pid);
                } else {
                    it.cast_shadow = false; it.receive_shadow = false;
                    if (xr) { it.transparent = true; it.depth_test = false; it.depth_write = false; it.opacity = 0.9f; it.order = 10; }
                }
                items.push(it);
            }
        }
    };
    add_model(*model, true, false);
    for (Overlay& o : overlays) if (o.on && o.m) { o.m->update_world(); add_model(*o.m, false, o.xray); }
    Vec<Particles> parts;
    if (live) for (Flow& f : flows) {
        if (!f.on) continue;
        Particles& P = parts.push(); P.color = f.color; P.radius = f.r;
        for (int i = 0; i < f.n; i++) {
            float s = fmodf(f.u[i], 1.f) * f.L; int k = 1;
            while (k < f.cum.n - 1 && f.cum[k] < s) k++;
            float t = (s - f.cum[k - 1]) / fmaxf(1e-9f, f.cum[k] - f.cum[k - 1]);
            P.pos.push(lerp(f.pts[k - 1], f.pts[k], t));
        }
    }
    float aspect = stage_h > 0 ? stage_w / stage_h : 1;
    R.set_sun(sun_c, sun_s);
    R.set_camera(cam.view(), cam.proj(aspect), cam.pos);
    R.draw(items, ground_y, true, parts);
}
