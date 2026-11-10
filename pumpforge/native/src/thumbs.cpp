// Live 3-D thumbnails and the Home hero: models rendered into textures with the same renderer as the viewer.
#include "ui.h"
#include "glapi.h"

static const int TW = 448, TH = 336, MAX_THUMBS = 72;

// default appearance (library.html on load): no cutaway, section faces hidden, liquids at 55 % opacity
void App::render_model_to(Model& m, Target& t, float yaw, float tight, bool transparent) {
    m.update_world();
    Box b = m.bounds(nullptr);
    if (!b.valid()) return;
    Vec<DrawItem> items;
    for (int i = 0; i < m.nodes.n; i++) {
        const Node& nd = m.nodes[i];
        if (nd.mesh < 0) continue;
        bool fluid = nd.part >= 0 && m.nodes[nd.part].group.eq("fluid");
        for (const Prim& p : m.meshes[nd.mesh].prims) {
            const Material* mt = p.mat >= 0 && p.mat < m.mats.n ? &m.mats[p.mat] : nullptr;
            if (mt && mt->section) continue;
            DrawItem it; it.p = &p; it.m = mt; it.world = nd.world; it.w[0] = nd.w[0]; it.w[1] = nd.w[1];
            if (fluid) { it.transparent = true; it.opacity = 0.55f; it.depth_write = false; }
            items.push(it);
        }
    }
    V3 c = b.center(), sz = b.size();
    float aspect = (float)t.w / t.h, fov = 32;
    float vf = fov * (float)M_PI / 180.f / 2, hf = atanf(tanf(vf) * aspect);
    float d = fmaxf(sz.y / 2 / tanf(vf), fmaxf(sz.x, sz.z) / 2 / tanf(hf)) * tight + fmaxf(sz.x, sz.z) / 2;
    V3 dir = norm(V3(0.85f, 0.45f, 1.1f));
    float cy = cosf(yaw), sy = sinf(yaw);
    dir = V3(dir.x * cy + dir.z * sy, dir.y, -dir.x * sy + dir.z * cy);
    V3 eye = c + dir * d;
    R.target_begin(t);
    if (transparent) R.clear_transparent(); else R.background(T.stage0, T.stage1);
    R.set_sun(c, len(sz));
    R.set_camera(m4_lookat(eye, c, V3(0, 1, 0)), m4_persp(fov * (float)M_PI / 180.f, aspect, fmaxf(d / 200, 0.005f), d * 20), eye);
    Vec<Particles> none;
    R.draw(items, b.lo.y - 0.002f, true, none);
}

unsigned App::thumb(int mod) {
    if (mod < 0 || mod >= mods.n) return 0;
    for (Thumb& t : thumbs) if (t.mod == mod) { t.requested = thumb_clock; if (t.ready) { t.used = thumb_clock; return t.tex; } return 0; }
    Thumb& n = thumbs.push(); n.mod = mod; n.requested = thumb_clock;
    return 0;
}

void App::thumbs_update() {
    thumb_clock++;
    if (!gl_ready) return;
    // one new thumbnail per frame (most recently requested first) so scrolling stays smooth
    int pick = -1;
    for (int i = 0; i < thumbs.n; i++) if (!thumbs[i].ready && !thumbs[i].failed && thumbs[i].requested >= thumb_clock - 2) { pick = i; }
    if (pick >= 0) {
        Thumb& th = thumbs[pick];
        Model m; char err[200];
        if (!m.load(Str::f("models/%s.pfm", mods[th.mod].id.c()), err, sizeof err)) { th.failed = true; pf_log("thumb %s: %s", mods[th.mod].id.c(), err); }
        else if (R.target_ensure(thumb_rt, TW, TH)) {
            m.upload();
            render_model_to(m, thumb_rt, 0, 1.08f, true);
            if (!th.tex) {
                glGenTextures(1, &th.tex); glBindTexture(GL_TEXTURE_2D, th.tex);
                glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA8, TW, TH, 0, GL_RGBA, GL_UNSIGNED_BYTE, nullptr);
                glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR); glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);
                glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE); glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE);
                glGenFramebuffers(1, &th.fbo); glBindFramebuffer(GL_FRAMEBUFFER, th.fbo);
                glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, th.tex, 0);
            }
            // resolve the multisampled scratch target straight into this thumbnail's texture
            glBindFramebuffer(GL_READ_FRAMEBUFFER, thumb_rt.fbo); glBindFramebuffer(GL_DRAW_FRAMEBUFFER, th.fbo);
            glDisable(GL_SCISSOR_TEST);
            glBlitFramebuffer(0, 0, TW, TH, 0, 0, TW, TH, GL_COLOR_BUFFER_BIT, GL_NEAREST);
            glBindFramebuffer(GL_FRAMEBUFFER, 0); R.cur_fbo = 0;
            m.release();
            th.ready = true; th.used = thumb_clock;
        }
    }
    // keep GPU memory bounded: drop the least recently shown thumbnails
    int ready = 0; for (Thumb& t : thumbs) ready += t.ready;
    while (ready > MAX_THUMBS) {
        int lru = -1; for (int i = 0; i < thumbs.n; i++) if (thumbs[i].ready && thumbs[i].used < thumb_clock - 2 && (lru < 0 || thumbs[i].used < thumbs[lru].used)) lru = i;
        if (lru < 0) break;
        glDeleteTextures(1, &thumbs[lru].tex); glDeleteFramebuffers(1, &thumbs[lru].fbo);
        thumbs.erase(lru); ready--;
    }
    // forget stale requests
    for (int i = thumbs.n - 1; i >= 0; i--) if (!thumbs[i].ready && thumbs[i].requested < thumb_clock - 120) thumbs.erase(i);
}

void App::hero_update(float dt) {
    if (!hero_wanted || !gl_ready || hero_mod < 0 || !hero_rt.fbo) return;
    if (!hero || hero->pump_id != mods[hero_mod].id) {
        if (hero) { hero->release(); delete hero; hero = nullptr; }
        hero = new Model(); char err[200];
        if (!hero->load(Str::f("models/%s.pfm", mods[hero_mod].id.c()), err, sizeof err)) { delete hero; hero = nullptr; hero_mod = -1; return; }
        hero->upload();
        hero->pump_id = mods[hero_mod].id;
    }
    hero_yaw += dt * 0.32f;
    render_model_to(*hero, hero_rt, hero_yaw, 1.02f, true);
    R.target_end(hero_rt);
}
