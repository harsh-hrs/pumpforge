// Catalogue, per-device store and module loading.
#include "app.h"
#include <stdio.h>

void viewer_cam_touched(bool v);

static const char* STORE_FILE = "pumpforge.v1.json";

Store::Entry& Store::get(const char* id) {
    for (Entry& x : e) if (x.id.eq(id)) return x;
    Entry& n = e.push(); n.id = id; return n;
}
const Store::Entry* Store::find(const char* id) const {
    for (const Entry& x : e) if (x.id.eq(id)) return &x;
    return nullptr;
}

// Same shape as the web library's localStorage 'pumpforge.v1': {prog:{id:{seen,best}}, stars:{id:true}, notes:{id:txt}, ds:{id:{...}}}
void Store::load() {
    Vec<uint8_t> b;
    if (!plat::read_user(STORE_FILE, b) || !b.n) return;
    JDoc d;
    if (!d.parse((const char*)b.d, (size_t)b.n)) { pf_log("store parse failed: %s", d.err); return; }
    const JV& r = *d.root;
    for (const JV& p : r["prog"]) { Entry& x = get(p.key); if (p["seen"].isNum()) x.prog.seen = p["seen"].n(); if (p["best"].isNum()) x.prog.best = (int)p["best"].n(); }
    for (const JV& s : r["stars"]) get(s.key).star = s.truthy();
    for (const JV& s : r["notes"]) get(s.key).notes = s.str();
    for (const JV& s : r["ds"]) {
        Entry& x = get(s.key); x.ds.set = true;
        x.ds.manufacturer = s["manufacturer"].str(); x.ds.model = s["model"].str();
        for (const JV& k : s["rated_point"]) { x.ds.keys.push(Str(k.key)); x.ds.vals.push(k.text()); }
    }
    const JV& st = r["settings"];
    narrate = st["narrate"].truthy();
    if (st["theme"].isNum()) theme = pf_clamp((int)st["theme"].n(), 0, 2);
    if (st.has("live")) live_default = st["live"].truthy();
    if (st.has("markers")) markers_default = st["markers"].truthy();
    last = st["last"].str();
}

void Store::save() {
    JW w; w.beginObj();
    w.key("prog").beginObj();
    for (const Entry& x : e) if (x.prog.seen > 0 || x.prog.best >= 0) {
        w.key(x.id).beginObj();
        if (x.prog.seen > 0) w.key("seen").num(x.prog.seen);
        if (x.prog.best >= 0) w.key("best").num(x.prog.best);
        w.endObj();
    }
    w.endObj();
    w.key("stars").beginObj(); for (const Entry& x : e) if (x.star) w.key(x.id).boolean(true); w.endObj();
    w.key("notes").beginObj(); for (const Entry& x : e) if (!x.notes.empty()) w.key(x.id).str(x.notes); w.endObj();
    w.key("ds").beginObj();
    for (const Entry& x : e) if (x.ds.set) {
        w.key(x.id).beginObj().key("manufacturer").str(x.ds.manufacturer).key("model").str(x.ds.model).key("rated_point").beginObj();
        for (int i = 0; i < x.ds.keys.n; i++) w.key(x.ds.keys[i]).str(x.ds.vals[i]);
        w.endObj().endObj();
    }
    w.endObj();
    w.key("settings").beginObj().key("narrate").boolean(narrate).key("theme").num(theme).key("live").boolean(live_default)
        .key("markers").boolean(markers_default).key("last").str(last).endObj();
    w.endObj();
    if (!plat::write_user(STORE_FILE, w.o.c(), (size_t)w.o.n)) pf_log("store save failed");
    dirty = false;
}

bool App::load_index(char* err, int errlen) {
    Vec<uint8_t> b;
    if (!plat::read_asset("learning/index.json", b)) { snprintf(err, (size_t)errlen, "learning/index.json missing"); return false; }
    if (!index.parse((const char*)b.d, (size_t)b.n)) { snprintf(err, (size_t)errlen, "index.json: %s", index.err); return false; }
    const JV& r = *index.root;
    for (const JV& d : r["departments"]) { DeptInfo& x = depts.push(); x.id = d["id"].str(); x.name = d["name"].str(); x.status = d["status"].str(); x.modules = (int)d["modules"].n(); }
    for (const JV& m : r["modules"]) {
        ModInfo& x = mods.push();
        x.id = m["id"].str(); x.title = m["title"].str(); x.category = m["category"].str(); x.department = m["department"].str();
        x.eq_id = m["eq_id"].str(); x.subcategory = m["subcategory"].str(); x.no = (int)m["no"].n(); x.phase = (int)m["phase"].n();
        x.flagship = m["flagship"].truthy();
        x.tours = (int)m["video_tours"].n(); x.quizq = (int)m["quiz_questions"].n();
        for (int k = 0; k < depts.n; k++) if (depts[k].name.eq(x.department)) x.dept = k;
        // web search haystack: title id eq_id department category subcategory keywords (lower-case)
        x.hay = Str::f("%s %s %s %s %s %s", x.title.c(), x.id.c(), x.eq_id.c(), x.department.c(), x.category.c(), x.subcategory.c());
        for (const JV& k : m["keywords"]) { x.hay.add(' '); x.hay.add(k.str()); }
        str_lower(x.hay);
    }
    if (!mods.n) { snprintf(err, (size_t)errlen, "index has no modules"); return false; }
    return true;
}

int App::mod_index(const char* id) const { for (int i = 0; i < mods.n; i++) if (mods[i].id.eq(id)) return i; return -1; }

// Loading is deferred by one frame so the "Loading model..." state is drawn first.
void App::request_load(int idx) {
    if (idx < 0 || idx >= mods.n || idx == cur) return;
    stop_tour();
    pending_load = idx; pending_frames = 2;
}

void App::unload() {
    clear_overlays();
    if (model) { model->release(); delete model; model = nullptr; }
    flows.clear(); labels.clear();
    meta.root = nullptr; learn.root = nullptr;
}

void App::do_load(int idx) {
    unload();
    cur = idx; load_error.clear();
    const ModInfo& m = mods[idx];
    char err[200] = {0};
    Vec<uint8_t> b;
    Str mp = Str::f("meta/%s.json", m.id.c()), lp = Str::f("learning/%s.json", m.id.c()), gp = Str::f("models/%s.pfm", m.id.c());
    if (!plat::read_asset(mp, b) || !meta.parse((const char*)b.d, (size_t)b.n)) { load_error = "Could not load this model."; pf_log("meta %s", mp.c()); return; }
    if (!plat::read_asset(lp, b) || !learn.parse((const char*)b.d, (size_t)b.n)) { load_error = "Could not load this model."; meta.root = nullptr; pf_log("learning %s", lp.c()); return; }
    Model* md = new Model();
    if (!md->load(gp, err, sizeof err)) { pf_log("model: %s", err); delete md; load_error = "Could not load this model."; meta.root = learn.root = nullptr; return; }
    md->upload();
    model = md;
    // per-node classification (library.html load())
    int n = md->nodes.n;
    node_vis.resize(n); node_static.resize(n); node_fluid.resize(n);
    op_anim = md->anim("Operate");
    Vec<uint8_t> animated; animated.resize(n); for (int i = 0; i < n; i++) animated[i] = 0;
    if (op_anim >= 0) for (const Channel& c : md->anims[op_anim].ch) animated[c.node] = 1;
    Vec<Str> moving;
    for (int i = 0; i < n; i++) {
        const Node& nd = md->nodes[i];
        if (nd.mesh < 0) continue;
        bool anim = animated[i] || (nd.parent >= 0 && animated[nd.parent]);
        const char* pid = nd.part >= 0 ? md->nodes[nd.part].part_id.c() : "";
        if (anim) { bool have = false; for (Str& s : moving) if (s.eq(pid)) have = true; if (!have) moving.push(Str(pid)); }
    }
    const JV& parts = M()["parts"];
    for (int i = 0; i < n; i++) {
        const Node& nd = md->nodes[i];
        node_static[i] = node_fluid[i] = 0;
        if (nd.mesh < 0) continue;
        const char* pid = nd.part >= 0 ? md->nodes[nd.part].part_id.c() : "";
        bool mv = false; for (Str& s : moving) if (s.eq(pid)) mv = true;
        const char* grp = "";
        for (const JV& p : parts) if (streq(p["id"].str(), pid)) { grp = p["group"].str(); break; }
        node_static[i] = !mv && !streq(grp, "flow_tracers");
        node_fluid[i] = streq(grp, "fluid");
    }
    operate = cut = xray = false; explode = 0; anim_t = 0; anim_started = false;   // a fresh scene: nothing animated yet
    hidden.clear(); selected.clear(); hl.clear(); flash_part.clear(); flash_until = 0;
    quiz.clear(); for (int i = 0; i < S()["assessment"]["questions"].size(); i++) quiz.push(-1);
    clear_measure();
    step_idx = -1; step_auto = false; cmp_mod = -1; ds_msg.clear(); more_calcs = false;
    calc_keys.clear(); calc_vals.clear();
    build_particles();
    apply_state();
    Store::Entry& se = store.get(m.id); se.prog.seen = plat::now_epoch_ms(); store.dirty = true;
    full_box = md->bounds(nullptr);
    ground_y = full_box.lo.y - 0.002f;
    frame_full();
    cam.d_theta = cam.d_phi = 0; cam.d_pan = V3(); cam.auto_rotate = false;
    page_scroll_reset = 0; explode_target = -1;
    viewer_cam_touched(false);
    store.last = m.id; store.dirty = true;
}
