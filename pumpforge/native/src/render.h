// 3-D renderer: a GLSL ES 3.00 port of three.js r170 MeshStandardMaterial shading as used by the web library
// (RoomEnvironment PMREM image-based light baked from three itself, directional sun 1.6 with PCF shadows,
//  shadow-catcher ground at 0.16 opacity, ACES Filmic tone mapping, sRGB output).
#pragma once
#include "base.h"
#include "model.h"

struct DrawItem {
    const Prim* p; const Material* m; M4 world; float w[2];
    bool highlight = false;      // emissive 0x2a6fd6 instead of the material emissive
    float opacity = 1;
    bool transparent = false, depth_write = true, depth_test = true, cast_shadow = true, receive_shadow = true;
    int order = 0;               // three.js renderOrder
    float z = 0;                 // view depth for sorting (filled by renderer)
};

struct Particles { V3 color; float radius; Vec<V3> pos; };

// Offscreen colour target: multisampled renderbuffers resolved into a texture the UI draws.
struct Target { unsigned fbo = 0, color_rb = 0, depth_rb = 0, rfbo = 0, tex = 0, rdepth = 0; int w = 0, h = 0, samples = 0; };

struct Renderer {
    bool init(char* err, int errlen);
    void shutdown();
    void lost();                 // GL context was lost: forget object names

    // stage rectangle in framebuffer pixels (origin bottom-left)
    void begin(int fbw, int fbh, int x, int y, int w, int h);
    void background(V3 c0_srgb, V3 c1_srgb);                  // radial gradient (CSS radial-gradient(120% 90% at 50% 35%))
    void clear_transparent();
    bool target_ensure(Target& t, int w, int h);                // (re)allocate at this size; 4x MSAA when available
    void target_free(Target& t);
    void target_begin(Target& t);                               // render into t (viewport = whole target)
    void target_end(Target& t);                                 // resolve multisampling into t.tex
    void set_camera(const M4& view, const M4& proj, V3 eye);
    void set_sun(V3 center, float size);                      // three: sun at center + (0.6,1.2,0.8)*size, ortho +-size
    void draw(Vec<DrawItem>& items, float ground_y, bool ground, const Vec<Particles>& parts);
    void end();
    bool read_pixels(int x, int y, int w, int h, uint8_t* rgba);   // harness screenshots

    // state
    int fbw = 0, fbh = 0, vx = 0, vy = 0, vw = 0, vh = 0; unsigned cur_fbo = 0; int max_samples = 0;
    M4 view, proj, vp; V3 eye;
    M4 light_vp; V3 sun_dir{0.4685f, 0.7809f, 0.5206f}; float sun_size = 1; V3 sun_center;
    int shadow_size = 2048;
    unsigned prog_mesh = 0, prog_depth = 0, prog_ground = 0, prog_bg = 0, prog_part = 0;
    unsigned shadow_fbo = 0, shadow_tex = 0, env_tex = 0, quad_vao = 0, quad_vbo = 0;
    unsigned sph_vao = 0, sph_vbo = 0, sph_ibo = 0, inst_vbo = 0; int sph_ic = 0; int inst_cap = 0;
    int env_layers = 0; float env_lv[8];
    bool ok = false;
private:
    void draw_mesh_pass(DrawItem& it, int side);   // side: 0 = as material, 1 = back only, 2 = front only
    void shadow_pass(Vec<DrawItem>& items);
};
