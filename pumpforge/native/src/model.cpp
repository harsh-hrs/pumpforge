#include "model.h"
#include "plat.h"
#include "glapi.h"
#include <stdio.h>

// ----------------------------------------------------------------- decoders (mirror tools/glb2pfm.py)
bool decode_pfm_vertices(const uint8_t* src, int vc, uint8_t* dst, int16_t* qpos) {
    for (int k = 0; k < 3; k++) {
        const uint8_t* lo = src + 2 * k * vc; const uint8_t* hi = lo + vc;
        uint16_t acc = 0;
        for (int i = 0; i < vc; i++) {
            uint16_t z = (uint16_t)(lo[i] | (hi[i] << 8));
            int16_t d = (int16_t)((z >> 1) ^ (uint16_t)(-(int)(z & 1)));
            acc = (uint16_t)(acc + (uint16_t)d);
            int16_t v = (int16_t)acc;
            memcpy(dst + (size_t)i * 12 + (size_t)k * 2, &v, 2);
            qpos[i * 4 + k] = v;
        }
    }
    for (int i = 0; i < vc; i++) { int16_t z0 = 0; memcpy(dst + (size_t)i * 12 + 6, &z0, 2); qpos[i * 4 + 3] = 0; dst[(size_t)i * 12 + 11] = 0; }
    for (int k = 0; k < 3; k++) {
        const uint8_t* p = src + 6 * vc + k * vc;
        uint8_t acc = 0;
        for (int i = 0; i < vc; i++) {
            uint8_t z = p[i];
            int8_t d = (int8_t)((z >> 1) ^ (uint8_t)(-(int)(z & 1)));
            acc = (uint8_t)(acc + (uint8_t)d);
            dst[(size_t)i * 12 + 8 + k] = acc;
        }
    }
    return true;
}
bool decode_pfm_indices(const uint8_t* src, int ic, int vc, uint16_t* dst) {
    const uint8_t* lo = src; const uint8_t* hi = src + ic;
    int hw = 0;
    for (int i = 0; i < ic; i++) {
        int code = lo[i] | (hi[i] << 8);
        int v = hw - code;
        if (v < 0 || v >= vc) return false;
        dst[i] = (uint16_t)v;
        if (v + 1 > hw) hw = v + 1;
    }
    return true;
}

static V3 jv3(const JV& a, V3 def = V3()) { if (a.size() < 3) return def; return V3((float)a[0].n(), (float)a[1].n(), (float)a[2].n()); }

bool Model::load(const char* path, char* err, int errlen) {
    if (!plat::read_asset(path, file)) { snprintf(err, (size_t)errlen, "missing %s", path); return false; }
    if (file.n < 8 || memcmp(file.d, "PFM1", 4)) { snprintf(err, (size_t)errlen, "bad header %s", path); return false; }
    uint32_t jl; memcpy(&jl, file.d + 4, 4);
    if (8 + (size_t)jl > (size_t)file.n) { snprintf(err, (size_t)errlen, "truncated %s", path); return false; }
    if (!hdr.parse((const char*)file.d + 8, jl)) { snprintf(err, (size_t)errlen, "json %s: %s", path, hdr.err); return false; }
    const uint8_t* blob = file.d + 8 + jl; size_t blen = (size_t)file.n - 8 - jl;
    const JV& H = *hdr.root;
    for (const JV& m : H["materials"]) {
        Material& mt = mats.push();
        mt.name = m["name"].str();
        for (int i = 0; i < 4; i++) mt.c[i] = (float)m["c"][i].n(1);
        mt.metal = (float)m["m"].n(1); mt.rough = (float)m["r"].n(1);
        mt.emissive = jv3(m["e"]); mt.ds = m["ds"].truthy();
        mt.section = mt.name.eq("section");
    }
    for (const JV& me : H["meshes"]) {
        Mesh& M = meshes.push();
        M.nw = pf_min(me["w"].size(), 2); for (int i = 0; i < M.nw; i++) M.w0[i] = (float)me["w"][i].n();
        for (const JV& pj : me["prims"]) {
            Prim& p = M.prims.push();
            p.mat = (int)pj["mat"].n(-1); p.vc = (int)pj["vc"].n(); p.ic = (int)pj["ic"].n();
            p.c = jv3(pj["c"]); p.h = jv3(pj["h"]);
            size_t vo = (size_t)pj["vo"].n(), io = (size_t)pj["io"].n();
            if (vo + (size_t)p.vc * 9 > blen || io + (size_t)p.ic * 2 > blen || p.vc <= 0 || p.ic <= 0) { snprintf(err, (size_t)errlen, "bad prim %s", path); return false; }
            p.qpos.resize(p.vc * 4); p.idx.resize(p.ic);
            p.gpuv.resize(p.vc * 12);
            decode_pfm_vertices(blob + vo, p.vc, p.gpuv.d, p.qpos.d);
            if (!decode_pfm_indices(blob + io, p.ic, p.vc, p.idx.d)) { snprintf(err, (size_t)errlen, "bad indices %s", path); return false; }
            p.ntg = pf_min(pj["tg"].size(), 2);
            for (int t = 0; t < p.ntg; t++) {
                const JV& tg = pj["tg"][t];
                p.ps[t] = jv3(tg["ps"]); p.ns[t] = (float)tg["ns"].n();
                size_t po = (size_t)tg["po"].n();
                if (po + (size_t)p.vc * 8 > blen) { snprintf(err, (size_t)errlen, "bad morph %s", path); return false; }
                size_t no = (size_t)tg["no"].n();
                if (no + (size_t)p.vc * 4 > blen) { snprintf(err, (size_t)errlen, "bad morph %s", path); return false; }
                p.mpos[t].resize(p.vc * 4); memcpy(p.mpos[t].d, blob + po, (size_t)p.vc * 8);
                if (t == 0) p.gpum.resize(p.ntg * p.vc * 12);
                memcpy(p.gpum.d + (size_t)t * p.vc * 12, blob + po, (size_t)p.vc * 8);
                memcpy(p.gpum.d + (size_t)t * p.vc * 12 + (size_t)p.vc * 8, blob + no, (size_t)p.vc * 4);
            }
            for (int i = 0; i < p.vc; i++) {
                const int16_t* q = &p.qpos[i * 4];
                p.lbox.add(V3(p.c.x + q[0] / 32767.f * p.h.x, p.c.y + q[1] / 32767.f * p.h.y, p.c.z + q[2] / 32767.f * p.h.z));
            }
            tris += p.ic / 3;
        }
    }
    for (const JV& nj : H["nodes"]) {
        Node& n = nodes.push();
        n.name = nj["n"].str(); n.parent = (int)nj["p"].n(-1); n.mesh = (int)nj["mesh"].n(-1);
        n.t0 = jv3(nj["t"]); n.s0 = jv3(nj["s"], V3(1, 1, 1));
        const JV& r = nj["r"]; n.r0 = r.size() == 4 ? Quat{(float)r[0].n(), (float)r[1].n(), (float)r[2].n(), (float)r[3].n(1)} : Quat();
        n.t = n.t0; n.s = n.s0; n.r = n.r0;
        const JV& x = nj["x"];
        n.part_id = x["part_id"].str(); n.section_role = x["section_role"].str(); n.group = x["group"].str();
        n.flow_kind = x["flow_kind"].str(); n.overlay = x["overlay"].str(); n.part_name = x["part_name"].str();
        if (x["explode_offset"].size() == 3) { n.has_explode = true; n.explode = jv3(x["explode_offset"]); }
        if (n.mesh >= 0 && n.mesh < meshes.n) { for (int i = 0; i < meshes[n.mesh].nw; i++) n.w[i] = meshes[n.mesh].w0[i]; }
        else n.mesh = -1;
        if (n.parent >= nodes.n - 1) n.parent = -1;   // parents precede children by construction
    }
    for (int i = 0; i < nodes.n; i++) {
        int k = i; while (k >= 0 && nodes[k].part_id.empty()) k = nodes[k].parent;
        nodes[i].part = k;
    }
    for (const JV& aj : H["anims"]) {
        Anim& A = anims.push();
        A.name = aj["name"].str(); A.dur = (float)aj["dur"].n();
        for (const JV& c : aj["ch"]) {
            Channel ch; ch.node = (int)c["node"].n(-1); const char* ps = c["path"].str("t"); ch.path = ps[0];
            ch.n = (int)c["n"].n(); ch.k = (int)c["k"].n();
            size_t to = (size_t)c["to"].n(), vo = (size_t)c["vo"].n();
            if (ch.node < 0 || ch.node >= nodes.n || ch.n <= 0 || to + (size_t)ch.n * 4 > blen || vo + (size_t)ch.n * ch.k * 4 > blen) continue;
            ch.times = (const float*)(blob + to); ch.vals = (const float*)(blob + vo);
            A.ch.push(ch);
        }
    }
    const JV& ex = H["extras"];
    pump_id = ex["pump_id"].str(); title = ex["title"].str();
    for (const Node& n : nodes) if (!n.overlay.empty()) { overlay_kind = n.overlay; break; }
    update_world();
    return true;
}

void Model::upload() {
    if (gpu) return;
    for (Mesh& M : meshes) for (Prim& p : M.prims) {
        glGenVertexArrays(1, &p.vao); glBindVertexArray(p.vao);
        glGenBuffers(1, &p.vbo); glBindBuffer(GL_ARRAY_BUFFER, p.vbo);
        glBufferData(GL_ARRAY_BUFFER, (GLsizeiptr)p.gpuv.n, p.gpuv.d, GL_STATIC_DRAW);
        glEnableVertexAttribArray(0); glVertexAttribPointer(0, 3, GL_SHORT, GL_TRUE_, 12, (const void*)0);
        glEnableVertexAttribArray(1); glVertexAttribPointer(1, 3, GL_BYTE, GL_TRUE_, 12, (const void*)8);
        if (p.ntg) {
            glGenBuffers(1, &p.mbo); glBindBuffer(GL_ARRAY_BUFFER, p.mbo);
            glBufferData(GL_ARRAY_BUFFER, (GLsizeiptr)p.gpum.n, p.gpum.d, GL_STATIC_DRAW);
            for (int t = 0; t < p.ntg; t++) {
                size_t base = (size_t)t * p.vc * 12;
                glEnableVertexAttribArray(2 + 2 * t); glVertexAttribPointer(2 + 2 * t, 3, GL_SHORT, GL_TRUE_, 8, (const void*)base);
                glEnableVertexAttribArray(3 + 2 * t); glVertexAttribPointer(3 + 2 * t, 3, GL_BYTE, GL_TRUE_, 4, (const void*)(base + (size_t)p.vc * 8));
            }
        }
        glGenBuffers(1, &p.ibo); glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, p.ibo);
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, (GLsizeiptr)p.ic * 2, p.idx.d, GL_STATIC_DRAW);
        glBindVertexArray(0);
    }
    glBindBuffer(GL_ARRAY_BUFFER, 0);
    gpu = true;
}

void Model::release() {
    if (!gpu) return;
    for (Mesh& M : meshes) for (Prim& p : M.prims) {
        if (p.vao) glDeleteVertexArrays(1, &p.vao);
        unsigned b[3] = {p.vbo, p.ibo, p.mbo}; for (unsigned x : b) if (x) glDeleteBuffers(1, &x);
        p.vao = p.vbo = p.ibo = p.mbo = 0;
    }
    gpu = false;
}

int Model::anim(const char* name) const { for (int i = 0; i < anims.n; i++) if (anims[i].name.eq(name)) return i; return -1; }

void Model::sample(int ai, float t) {
    if (ai < 0 || ai >= anims.n) return;
    for (const Channel& c : anims[ai].ch) {
        const float* T = c.times; int n = c.n;
        int i0 = 0, i1 = 0; float f = 0;
        if (t <= T[0]) { i0 = i1 = 0; }
        else if (t >= T[n - 1]) { i0 = i1 = n - 1; }
        else { int lo = 0, hi = n - 1; while (hi - lo > 1) { int m = (lo + hi) / 2; if (T[m] <= t) lo = m; else hi = m; } i0 = lo; i1 = hi; float dt = T[i1] - T[i0]; f = dt > 0 ? (t - T[i0]) / dt : 0; }
        Node& N = nodes[c.node];
        const float* a = c.vals + (size_t)i0 * c.k; const float* b = c.vals + (size_t)i1 * c.k;
        if (c.path == 't' && c.k == 3) N.t = lerp(V3(a[0], a[1], a[2]), V3(b[0], b[1], b[2]), f);
        else if (c.path == 's' && c.k == 3) N.s = lerp(V3(a[0], a[1], a[2]), V3(b[0], b[1], b[2]), f);
        else if (c.path == 'r' && c.k == 4) N.r = qslerp(Quat{a[0], a[1], a[2], a[3]}, Quat{b[0], b[1], b[2], b[3]}, f);
        else if (c.path == 'w') for (int k = 0; k < pf_min(c.k, 2); k++) N.w[k] = a[k] + (b[k] - a[k]) * f;
    }
}

void Model::update_world() {
    for (int i = 0; i < nodes.n; i++) {
        Node& n = nodes[i];
        M4 l = m4_trs(n.t, n.r, n.s);
        n.world = n.parent >= 0 ? nodes[n.parent].world * l : l;
    }
}

Box Model::bounds(const bool* vis) const {
    Box b;
    for (int i = 0; i < nodes.n; i++) {
        const Node& n = nodes[i];
        if (n.mesh < 0 || (vis && !vis[i])) continue;
        for (const Prim& p : meshes[n.mesh].prims) {
            for (int c = 0; c < 8; c++) {
                V3 q((c & 1) ? p.lbox.hi.x : p.lbox.lo.x, (c & 2) ? p.lbox.hi.y : p.lbox.lo.y, (c & 4) ? p.lbox.hi.z : p.lbox.lo.z);
                b.add(n.world.point(q));
            }
        }
    }
    return b;
}

static bool ray_box(const Ray& r, const Box& b, float tmax) {
    float t0 = 0, t1 = tmax;
    for (int k = 0; k < 3; k++) {
        float inv = 1.f / (fabsf(r.d[k]) > 1e-12f ? r.d[k] : 1e-12f);
        float a = (b.lo[k] - r.o[k]) * inv, c = (b.hi[k] - r.o[k]) * inv;
        if (a > c) pf_swap(a, c);
        t0 = fmaxf(t0, a); t1 = fminf(t1, c);
        if (t0 > t1) return false;
    }
    return true;
}

Hit Model::pick(const Ray& wr, const uint8_t* pvis, const int* pbase) const {
    Hit best;
    for (int i = 0; i < nodes.n; i++) {
        const Node& n = nodes[i];
        if (n.mesh < 0) continue;
        M4 inv = m4_inverse(n.world);
        const float* w = n.world.m;
        float wdet = w[0] * (w[5] * w[10] - w[9] * w[6]) - w[4] * (w[1] * w[10] - w[9] * w[2]) + w[8] * (w[1] * w[6] - w[5] * w[2]);
        Ray r{inv.point(wr.o), inv.dir(wr.d)};
        float dl = len(r.d); if (dl < 1e-12f) continue;
        r.d = r.d * (1.f / dl);
        for (int pi = 0; pi < meshes[n.mesh].prims.n; pi++) {
            const Prim& p = meshes[n.mesh].prims[pi];
            if (pvis && !pvis[pbase[i] + pi]) continue;
            Box lb = p.lbox;
            bool morphed = false;
            for (int t = 0; t < p.ntg; t++) if (fabsf(n.w[t]) > 1e-6f) morphed = true;
            if (morphed) { V3 pad = (p.ps[0] + p.ps[1]); lb.lo -= pad; lb.hi += pad; }
            if (!ray_box(r, lb, 1e30f)) continue;
            auto P = [&](int v) {
                const int16_t* q = &p.qpos[v * 4];
                V3 x(p.c.x + q[0] / 32767.f * p.h.x, p.c.y + q[1] / 32767.f * p.h.y, p.c.z + q[2] / 32767.f * p.h.z);
                for (int t = 0; t < p.ntg; t++) if (n.w[t] != 0) { const int16_t* d = &p.mpos[t][v * 4]; x += V3(d[0] / 32767.f * p.ps[t].x, d[1] / 32767.f * p.ps[t].y, d[2] / 32767.f * p.ps[t].z) * n.w[t]; }
                return x;
            };
            bool two = p.mat >= 0 && p.mat < mats.n ? mats[p.mat].ds : false;
            for (int k = 0; k + 2 < p.ic; k += 3) {
                V3 a = P(p.idx[k]), b = P(p.idx[k + 1]), c = P(p.idx[k + 2]);
                V3 e1 = b - a, e2 = c - a, pv = cross(r.d, e2);
                float det = dot(e1, pv);
                if (fabsf(det) < 1e-14f) continue;
                if (!two && (wdet < 0 ? det > 0 : det < 0)) continue;   // single-sided: back faces are not hit (three.js FrontSide)
                float id = 1.f / det; V3 tv = r.o - a;
                float u = dot(tv, pv) * id; if (u < 0 || u > 1) continue;
                V3 qv = cross(tv, e1);
                float v = dot(r.d, qv) * id; if (v < 0 || u + v > 1) continue;
                float t = dot(e2, qv) * id; if (t <= 1e-7f) continue;
                V3 lp = r.o + r.d * t, wp = n.world.point(lp);
                float wt = len(wp - wr.o);
                if (wt < best.t) { best.ok = true; best.t = wt; best.node = i; best.p = wp; }
            }
        }
    }
    return best;
}
