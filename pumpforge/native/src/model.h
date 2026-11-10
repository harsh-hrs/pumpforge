// Compact model (.pfm) loading, scene graph, LINEAR keyframe animation, morph targets and ray picking.
#pragma once
#include "base.h"
#include "json.h"

struct Material { Str name; float c[4] = {1, 1, 1, 1}; float metal = 1, rough = 1; V3 emissive; bool ds = false; bool section = false; };

struct Prim {
    int mat = -1, vc = 0, ic = 0;
    V3 c, h;                       // dequantisation: pos = c + q/32767 * h
    int ntg = 0; V3 ps[2]; float ns[2] = {0, 0};
    unsigned vao = 0, vbo = 0, ibo = 0, mbo = 0;
    Vec<int16_t> qpos;             // CPU copy (x,y,z,pad) for picking
    Vec<uint16_t> idx;
    Vec<int16_t> mpos[2];          // morph position deltas (x,y,z,pad)
    Vec<uint8_t> gpuv, gpum;       // GPU-layout vertex / morph data (kept so GL objects can be recreated after context loss)
    Box lbox;                      // local bounds (base pose)
};
struct Mesh { Vec<Prim> prims; float w0[2] = {0, 0}; int nw = 0; };

struct Node {
    Str name, part_id, section_role, group, flow_kind, overlay, part_name;
    int parent = -1, mesh = -1;
    V3 t0, s0{1, 1, 1}; Quat r0;   // rest pose (from file)
    V3 t, s{1, 1, 1}; Quat r;      // current pose
    bool has_explode = false; V3 explode;
    float w[2] = {0, 0};           // morph weights
    M4 world = M4::id();
    // derived (per model)
    int part = -1;                 // nearest ancestor-or-self node index carrying part_id (for meshes)
    bool animated = false;         // targeted by the Operate clip (node or its parent, as in the web viewer)
};

struct Channel { int node; char path; int n, k; const float* times; const float* vals; };
struct Anim { Str name; float dur = 0; Vec<Channel> ch; };

struct Ray { V3 o, d; };
struct Hit { bool ok = false; float t = 1e30f; int node = -1; V3 p; };

struct Model {
    Vec<uint8_t> file;            // raw .pfm (animation arrays point into it)
    JDoc hdr;
    Vec<Material> mats;
    Vec<Node> nodes;
    Vec<Mesh> meshes;
    Vec<Anim> anims;
    Str pump_id, title, overlay_kind;
    int tris = 0;
    bool gpu = false;

    bool load(const char* asset_path, char* err, int errlen);
    void upload();                 // create GL buffers (needs a current context)
    void release();                // free GL objects
    ~Model() { release(); }
    int anim(const char* name) const;
    void sample(int anim, float t);               // apply clip at time t (sets t/r/s/w of targeted nodes)
    void update_world();
    Box bounds(const bool* node_visible) const;   // world AABB of visible mesh nodes (null = all)
    Hit pick(const Ray& r, const uint8_t* prim_vis, const int* prim_base) const;   // visibility per (node, primitive); null = all
};

bool decode_pfm_vertices(const uint8_t* src, int vc, uint8_t* dst12, int16_t* qpos4);
bool decode_pfm_indices(const uint8_t* src, int ic, int vc, uint16_t* dst);
