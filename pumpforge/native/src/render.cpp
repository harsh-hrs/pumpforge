#include "render.h"
#include "glapi.h"
#include "plat.h"
#include <stdio.h>

// ------------------------------------------------------------------ shaders
static const char* VS_MESH = R"(#version 300 es
layout(location=0) in vec3 a_p; layout(location=1) in vec3 a_n;
layout(location=2) in vec3 a_m0p; layout(location=3) in vec3 a_m0n; layout(location=4) in vec3 a_m1p; layout(location=5) in vec3 a_m1n;
uniform mat4 u_model, u_vp, u_light; uniform mat3 u_nmat;
uniform vec3 u_qc, u_qh, u_ms0, u_ms1; uniform vec2 u_mn;
out vec3 v_wp; out vec3 v_n; out vec4 v_ls;
void main() {
  vec3 p = u_qc + a_p * u_qh + a_m0p * u_ms0 + a_m1p * u_ms1;
  vec3 n = a_n + a_m0n * u_mn.x + a_m1n * u_mn.y;
  vec4 w = u_model * vec4(p, 1.0);
  v_wp = w.xyz; v_n = u_nmat * n; v_ls = u_light * w;
  gl_Position = u_vp * w;
})";

// three.js r170 MeshStandardMaterial (lights_physical_pars_fragment) + PCF shadow + ACES Filmic + sRGB
static const char* FS_COMMON = R"(
const float PI = 3.141592653589793;
vec3 RRTAndODTFit(vec3 v) { vec3 a = v * (v + 0.0245786) - 0.000090537; vec3 b = v * (0.983729 * v + 0.4329510) + 0.238081; return a / b; }
vec3 aces(vec3 c) {
  const mat3 IN = mat3(vec3(0.59719, 0.07600, 0.02840), vec3(0.35458, 0.90834, 0.13383), vec3(0.04823, 0.01566, 0.83777));
  const mat3 OUT = mat3(vec3(1.60475, -0.10208, -0.00327), vec3(-0.53108, 1.10813, -0.07276), vec3(-0.07367, -0.00605, 1.07602));
  c *= 1.0 / 0.6; c = IN * c; c = RRTAndODTFit(c); c = OUT * c; return clamp(c, 0.0, 1.0); }
vec3 srgb(vec3 c) { return mix(pow(c, vec3(0.41666)) * 1.055 - vec3(0.055), c * 12.92, vec3(lessThanEqual(c, vec3(0.0031308)))); }
)";

static const char* FS_MESH = R"(
precision highp sampler2DShadow; precision highp sampler2DArray;
in vec3 v_wp; in vec3 v_n; in vec4 v_ls;
uniform vec4 u_base; uniform float u_metal, u_rough, u_opacity; uniform vec3 u_emis, u_eye, u_sundir;
uniform sampler2DShadow u_shadow; uniform vec2 u_smap; uniform float u_recv;
uniform sampler2DArray u_env; uniform float u_envn;
out vec4 o;
vec3 envAt(vec3 d, float r) {
  d = normalize(d);
  vec2 uv = vec2(atan(d.x, d.z) * (0.5 / PI) + 0.5, 1.0 - acos(clamp(d.y, -1.0, 1.0)) / PI);
  float f = clamp(r, 0.0, 1.0) * (u_envn - 1.0); float l0 = floor(f); float l1 = min(l0 + 1.0, u_envn - 1.0);
  return mix(textureLod(u_env, vec3(uv, l0), 0.0).rgb, textureLod(u_env, vec3(uv, l1), 0.0).rgb, f - l0);
}
float shadowAt() {
  if (u_smap.y < 0.5 || u_recv < 0.5) return 1.0;
  vec3 c = v_ls.xyz / v_ls.w * 0.5 + 0.5;
  if (c.x < 0.0 || c.x > 1.0 || c.y < 0.0 || c.y > 1.0 || c.z > 1.0) return 1.0;
  float ts = 1.0 / u_smap.x, s = 0.0;
  for (int i = -1; i <= 1; i++) for (int j = -1; j <= 1; j++) s += texture(u_shadow, vec3(c.xy + vec2(float(i), float(j)) * ts, c.z));
  return s / 9.0;
}
void main() {
  vec3 gn = normalize(v_n);
  vec3 N = gl_FrontFacing ? gn : -gn;
  vec3 V = normalize(u_eye - v_wp);
  vec3 dxy = max(abs(dFdx(gn)), abs(dFdy(gn)));
  float rough = min(max(u_rough, 0.0525) + max(max(dxy.x, dxy.y), dxy.z), 1.0);
  vec3 base = u_base.rgb, diff = base * (1.0 - u_metal), F0 = mix(vec3(0.04), base, u_metal);
  float dotNV = clamp(dot(N, V), 0.0, 1.0);
  // direct: DirectionalLight(0xffffff, 1.6)
  vec3 L = u_sundir; float dotNL = clamp(dot(N, L), 0.0, 1.0);
  vec3 irr = vec3(dotNL * 1.6 * shadowAt());
  vec3 H = normalize(L + V); float dotNH = clamp(dot(N, H), 0.0, 1.0), dotVH = clamp(dot(V, H), 0.0, 1.0);
  float a = rough * rough, a2 = a * a;
  float fr = exp2((-5.55473 * dotVH - 6.98316) * dotVH);
  vec3 F = F0 * (1.0 - fr) + fr;
  float gv = dotNL * sqrt(a2 + (1.0 - a2) * dotNV * dotNV), gl = dotNV * sqrt(a2 + (1.0 - a2) * dotNL * dotNL);
  float Vis = 0.5 / max(gv + gl, 1e-6);
  float den = dotNH * dotNH * (a2 - 1.0) + 1.0; float D = a2 / (PI * den * den);
  vec3 col = irr * F * (Vis * D) + irr * diff / PI;
  // image-based light: RoomEnvironment PMREM
  vec3 R = normalize(mix(reflect(-V, N), N, rough * rough));
  vec3 rad = envAt(R, rough), envI = envAt(gn, 1.0);
  const vec4 c0 = vec4(-1.0, -0.0275, -0.572, 0.022), c1 = vec4(1.0, 0.0425, 1.04, -0.04);
  vec4 rr = rough * c0 + c1; float a004 = min(rr.x * rr.x, exp2(-9.28 * dotNV)) * rr.x + rr.y;
  vec2 fab = vec2(-1.04, 1.04) * a004 + rr.zw;
  vec3 FssEss = F0 * fab.x + fab.y; float Ems = 1.0 - (fab.x + fab.y);
  vec3 Favg = F0 + (1.0 - F0) * 0.047619; vec3 Fms = FssEss * Favg / (1.0 - Ems * Favg);
  vec3 ms = Fms * Ems, tot = FssEss + ms;
  col += rad * FssEss + ms * envI + diff * (1.0 - max(max(tot.r, tot.g), tot.b)) * envI;
  col += u_emis;
  o = vec4(srgb(aces(col)), u_base.a * u_opacity);
})";

static const char* FS_DEPTH = R"(
out vec4 o; void main() { o = vec4(1.0); })";

static const char* VS_GROUND = R"(#version 300 es
layout(location=0) in vec2 a_p;
uniform mat4 u_vp, u_light; uniform vec3 u_c; uniform float u_r, u_y;
out vec4 v_ls; out vec2 v_q;
void main() { vec4 w = vec4(u_c.x + a_p.x * u_r, u_y, u_c.z + a_p.y * u_r, 1.0); v_q = a_p; v_ls = u_light * w; gl_Position = u_vp * w; })";
static const char* FS_GROUND = R"(
precision highp sampler2DShadow;
in vec4 v_ls; in vec2 v_q; uniform sampler2DShadow u_shadow; uniform vec2 u_smap; out vec4 o;
void main() {
  if (dot(v_q, v_q) > 1.0) discard;                 // CircleGeometry(30)
  vec3 c = v_ls.xyz / v_ls.w * 0.5 + 0.5; float s = 1.0;
  if (u_smap.y > 0.5 && c.x >= 0.0 && c.x <= 1.0 && c.y >= 0.0 && c.y <= 1.0 && c.z <= 1.0) {
    float ts = 1.0 / u_smap.x; s = 0.0;
    for (int i = -1; i <= 1; i++) for (int j = -1; j <= 1; j++) s += texture(u_shadow, vec3(c.xy + vec2(float(i), float(j)) * ts, c.z));
    s /= 9.0; }
  o = vec4(0.0, 0.0, 0.0, 0.16 * (1.0 - s));      // ShadowMaterial({ opacity: 0.16 })
})";

static const char* VS_BG = R"(#version 300 es
layout(location=0) in vec2 a_p; out vec2 v_uv;
void main() { v_uv = a_p * 0.5 + 0.5; gl_Position = vec4(a_p, 0.0, 1.0); })";
// CSS: radial-gradient(120% 90% at 50% 35%, stage 0%, stage2 100%) (interpolated in sRGB, like the browser)
static const char* FS_BG = R"(
in vec2 v_uv; uniform vec3 u_c0, u_c1; uniform vec2 u_size; out vec4 o;
void main() { vec2 p = vec2(v_uv.x, 1.0 - v_uv.y) * u_size; vec2 c = vec2(0.5, 0.35) * u_size; vec2 r = vec2(1.2, 0.9) * u_size;
  float d = clamp(length((p - c) / r), 0.0, 1.0); o = vec4(mix(u_c0, u_c1, d), 1.0); })";

static const char* VS_PART = R"(#version 300 es
layout(location=0) in vec3 a_p; layout(location=6) in vec3 a_off;
uniform mat4 u_vp; uniform float u_r;
void main() { gl_Position = u_vp * vec4(a_off + a_p * u_r, 1.0); })";
static const char* FS_PART = R"(
uniform vec3 u_col; out vec4 o; void main() { o = vec4(srgb(aces(u_col)), 1.0); })";

static unsigned compile(unsigned type, const char* const* src, int n, char* err, int el) {
    unsigned s = glCreateShader(type);
    glShaderSource(s, n, src, nullptr); glCompileShader(s);
    GLint ok = 0; glGetShaderiv(s, GL_COMPILE_STATUS, &ok);
    if (!ok) { char log[2048]; glGetShaderInfoLog(s, sizeof log, nullptr, log); snprintf(err, (size_t)el, "shader: %s", log); pf_log("%s", log); glDeleteShader(s); return 0; }
    return s;
}
static unsigned program(const char* vs, const char* fs, char* err, int el) {
    const char* vsrc[1] = {vs};
    const char* fsrc[3] = {"#version 300 es\nprecision highp float;\n", FS_COMMON, fs};
    unsigned v = compile(GL_VERTEX_SHADER, vsrc, 1, err, el); if (!v) return 0;
    unsigned f = compile(GL_FRAGMENT_SHADER, fsrc, 3, err, el); if (!f) return 0;
    unsigned p = glCreateProgram(); glAttachShader(p, v); glAttachShader(p, f); glLinkProgram(p);
    glDeleteShader(v); glDeleteShader(f);
    GLint ok = 0; glGetProgramiv(p, GL_LINK_STATUS, &ok);
    if (!ok) { char log[2048]; glGetProgramInfoLog(p, sizeof log, nullptr, log); snprintf(err, (size_t)el, "link: %s", log); pf_log("%s", log); return 0; }
    return p;
}

namespace {
struct MeshU { int model, vp, light, nmat, qc, qh, ms0, ms1, mn, base, metal, rough, opacity, emis, eye, sundir, shadow, smap, env, envn, recv; } MU, DU;
void locs(unsigned p, MeshU& u) {
#define L(x) u.x = glGetUniformLocation(p, "u_" #x);
    L(model) L(vp) L(light) L(nmat) L(qc) L(qh) L(ms0) L(ms1) L(mn) L(base) L(metal) L(rough) L(opacity) L(emis) L(eye) L(sundir) L(shadow) L(smap) L(env) L(envn) L(recv)
#undef L
}
const unsigned GL_TEXTURE_2D_ARRAY = 0x8C1A, GL_RGB9_E5 = 0x8C3D, GL_RGB = 0x1907, GL_UNSIGNED_INT_5_9_9_9_REV = 0x8C3E, GL_REPEAT = 0x2901, GL_TEXTURE_WRAP_R = 0x8072;
}

bool Renderer::init(char* err, int el) {
    prog_mesh = program(VS_MESH, FS_MESH, err, el); if (!prog_mesh) return false;
    prog_depth = program(VS_MESH, FS_DEPTH, err, el); if (!prog_depth) return false;
    prog_ground = program(VS_GROUND, FS_GROUND, err, el); if (!prog_ground) return false;
    prog_bg = program(VS_BG, FS_BG, err, el); if (!prog_bg) return false;
    prog_part = program(VS_PART, FS_PART, err, el); if (!prog_part) return false;
    locs(prog_mesh, MU); locs(prog_depth, DU);
    // fullscreen / unit quad
    float q[] = {-1, -1, 1, -1, -1, 1, 1, 1};
    glGenVertexArrays(1, &quad_vao); glBindVertexArray(quad_vao);
    glGenBuffers(1, &quad_vbo); glBindBuffer(GL_ARRAY_BUFFER, quad_vbo); glBufferData(GL_ARRAY_BUFFER, sizeof q, q, GL_STATIC_DRAW);
    glEnableVertexAttribArray(0); glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE_, 8, nullptr);
    // particle sphere: SphereGeometry(1, 10, 8)
    {
        Vec<float> v; Vec<uint16_t> ix; const int ws = 10, hs = 8;
        for (int y = 0; y <= hs; y++) for (int x = 0; x <= ws; x++) {
            float u = (float)x / ws, t = (float)y / hs;
            v.push(-cosf(u * 2 * (float)M_PI) * sinf(t * (float)M_PI)); v.push(cosf(t * (float)M_PI)); v.push(sinf(u * 2 * (float)M_PI) * sinf(t * (float)M_PI));
        }
        for (int y = 0; y < hs; y++) for (int x = 0; x < ws; x++) {
            uint16_t a = (uint16_t)(y * (ws + 1) + x + 1), b = (uint16_t)(y * (ws + 1) + x), c = (uint16_t)((y + 1) * (ws + 1) + x), d = (uint16_t)((y + 1) * (ws + 1) + x + 1);
            if (y != 0) { ix.push(a); ix.push(b); ix.push(d); }
            if (y != hs - 1) { ix.push(b); ix.push(c); ix.push(d); }
        }
        glGenVertexArrays(1, &sph_vao); glBindVertexArray(sph_vao);
        glGenBuffers(1, &sph_vbo); glBindBuffer(GL_ARRAY_BUFFER, sph_vbo); glBufferData(GL_ARRAY_BUFFER, v.n * 4, v.d, GL_STATIC_DRAW);
        glEnableVertexAttribArray(0); glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE_, 12, nullptr);
        glGenBuffers(1, &inst_vbo); glBindBuffer(GL_ARRAY_BUFFER, inst_vbo); inst_cap = 256; glBufferData(GL_ARRAY_BUFFER, inst_cap * 12, nullptr, GL_DYNAMIC_DRAW);
        glEnableVertexAttribArray(6); glVertexAttribPointer(6, 3, GL_FLOAT, GL_FALSE_, 12, nullptr); glVertexAttribDivisor(6, 1);
        glGenBuffers(1, &sph_ibo); glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, sph_ibo); glBufferData(GL_ELEMENT_ARRAY_BUFFER, ix.n * 2, ix.d, GL_STATIC_DRAW);
        sph_ic = ix.n;
    }
    glBindVertexArray(0);
    // morph attributes default to zero when a primitive has no targets
    for (int i = 2; i < 6; i++) glVertexAttrib4f((GLuint)i, 0, 0, 0, 0);
    // shadow map (depth texture with hardware comparison = PCF taps)
    glGenTextures(1, &shadow_tex); glBindTexture(GL_TEXTURE_2D, shadow_tex);
    glTexImage2D(GL_TEXTURE_2D, 0, GL_DEPTH_COMPONENT24, shadow_size, shadow_size, 0, GL_DEPTH_COMPONENT, GL_UNSIGNED_INT, nullptr);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR); glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE); glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_COMPARE_MODE, GL_COMPARE_REF_TO_TEXTURE); glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_COMPARE_FUNC, GL_LEQUAL);
    glGenFramebuffers(1, &shadow_fbo); glBindFramebuffer(GL_FRAMEBUFFER, shadow_fbo);
    glFramebufferTexture2D(GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_TEXTURE_2D, shadow_tex, 0);
    GLenum none = GL_NONE; glDrawBuffers(1, &none); glReadBuffer(GL_NONE);
    if (glCheckFramebufferStatus(GL_FRAMEBUFFER) != GL_FRAMEBUFFER_COMPLETE) { pf_log("shadow fbo incomplete; shadows off"); shadow_size = 0; }
    glBindFramebuffer(GL_FRAMEBUFFER, 0);
    // environment (RoomEnvironment radiance at roughness 0, 0.2 ... 1)
    {
        Vec<uint8_t> e;
        if (!plat::read_asset("env.bin", e) || e.n < 20 || memcmp(e.d, "PFEV", 4)) { snprintf(err, (size_t)el, "env.bin missing"); return false; }
        uint32_t W, H, Ln; memcpy(&W, e.d + 4, 4); memcpy(&H, e.d + 8, 4); memcpy(&Ln, e.d + 12, 4);
        env_layers = (int)Ln; for (int i = 0; i < env_layers && i < 8; i++) memcpy(&env_lv[i], e.d + 20 + 4 * i, 4);
        size_t off = 20 + 4 * Ln;
        if (e.n < (int)(off + (size_t)W * H * Ln * 4)) { snprintf(err, (size_t)el, "env.bin short"); return false; }
        glGenTextures(1, &env_tex); glBindTexture(GL_TEXTURE_2D_ARRAY, env_tex);
        glPixelStorei(GL_UNPACK_ALIGNMENT, 4);
        glTexImage3D(GL_TEXTURE_2D_ARRAY, 0, (GLint)GL_RGB9_E5, (GLsizei)W, (GLsizei)H, (GLsizei)Ln, 0, GL_RGB, GL_UNSIGNED_INT_5_9_9_9_REV, e.d + off);
        glTexParameteri(GL_TEXTURE_2D_ARRAY, GL_TEXTURE_MIN_FILTER, GL_LINEAR); glTexParameteri(GL_TEXTURE_2D_ARRAY, GL_TEXTURE_MAG_FILTER, GL_LINEAR);
        glTexParameteri(GL_TEXTURE_2D_ARRAY, GL_TEXTURE_WRAP_S, GL_REPEAT); glTexParameteri(GL_TEXTURE_2D_ARRAY, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE);
        glTexParameteri(GL_TEXTURE_2D_ARRAY, GL_TEXTURE_WRAP_R, GL_CLAMP_TO_EDGE);
    }
    GLenum ge = glGetError(); if (ge) pf_log("GL error after renderer init: 0x%x", ge);
    ok = true;
    return true;
}

void Renderer::lost() { prog_mesh = prog_depth = prog_ground = prog_bg = prog_part = 0; shadow_fbo = shadow_tex = env_tex = quad_vao = quad_vbo = sph_vao = sph_vbo = sph_ibo = inst_vbo = 0; ok = false; shadow_size = 2048; }
void Renderer::shutdown() {
    if (!ok) return;
    unsigned progs[] = {prog_mesh, prog_depth, prog_ground, prog_bg, prog_part}; for (unsigned p : progs) glDeleteProgram(p);
    glDeleteFramebuffers(1, &shadow_fbo); unsigned tx[] = {shadow_tex, env_tex}; glDeleteTextures(2, tx);
    unsigned b[] = {quad_vbo, sph_vbo, sph_ibo, inst_vbo}; glDeleteBuffers(4, b);
    unsigned va[] = {quad_vao, sph_vao}; glDeleteVertexArrays(2, va);
    lost();
}

void Renderer::begin(int w, int h, int x, int y, int sw, int sh) { fbw = w; fbh = h; vx = x; vy = y; vw = sw; vh = sh; }

void Renderer::background(V3 c0, V3 c1) {
    glBindFramebuffer(GL_FRAMEBUFFER, cur_fbo);
    glViewport(vx, vy, vw, vh); glEnable(GL_SCISSOR_TEST); glScissor(vx, vy, vw, vh);
    glDepthMask(GL_TRUE_); glClearDepthf(1); glClear(GL_DEPTH_BUFFER_BIT);
    glDisable(GL_DEPTH_TEST); glDisable(GL_BLEND); glDisable(GL_CULL_FACE);
    glUseProgram(prog_bg);
    glUniform3f(glGetUniformLocation(prog_bg, "u_c0"), c0.x, c0.y, c0.z);
    glUniform3f(glGetUniformLocation(prog_bg, "u_c1"), c1.x, c1.y, c1.z);
    glUniform2f(glGetUniformLocation(prog_bg, "u_size"), (float)vw, (float)vh);
    glBindVertexArray(quad_vao); glDrawArrays(GL_TRIANGLE_STRIP, 0, 4);
}
void Renderer::clear_transparent() {
    glBindFramebuffer(GL_FRAMEBUFFER, cur_fbo);
    glViewport(vx, vy, vw, vh); glEnable(GL_SCISSOR_TEST); glScissor(vx, vy, vw, vh);
    glColorMask(GL_TRUE_, GL_TRUE_, GL_TRUE_, GL_TRUE_); glDepthMask(GL_TRUE_);
    glClearColor(0, 0, 0, 0); glClearDepthf(1); glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);
}
bool Renderer::target_ensure(Target& t, int w, int h) {
    w = pf_max(w, 8); h = pf_max(h, 8);
    if (t.fbo && t.w == w && t.h == h) return true;
    target_free(t);
    if (!max_samples) { GLint ms = 0; glGetIntegerv(GL_MAX_SAMPLES, &ms); max_samples = ms > 0 ? ms : 1; }
    t.w = w; t.h = h; t.samples = pf_min(4, max_samples);
    glGenTextures(1, &t.tex); glBindTexture(GL_TEXTURE_2D, t.tex);
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA8, w, h, 0, GL_RGBA, GL_UNSIGNED_BYTE, nullptr);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR); glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE); glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE);
    glGenFramebuffers(1, &t.rfbo); glBindFramebuffer(GL_FRAMEBUFFER, t.rfbo);
    glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, t.tex, 0);
    if (t.samples > 1) {
        glGenRenderbuffers(1, &t.color_rb); glBindRenderbuffer(GL_RENDERBUFFER, t.color_rb);
        glRenderbufferStorageMultisample(GL_RENDERBUFFER, t.samples, GL_RGBA8, w, h);
        glGenRenderbuffers(1, &t.depth_rb); glBindRenderbuffer(GL_RENDERBUFFER, t.depth_rb);
        glRenderbufferStorageMultisample(GL_RENDERBUFFER, t.samples, GL_DEPTH_COMPONENT24, w, h);
        glGenFramebuffers(1, &t.fbo); glBindFramebuffer(GL_FRAMEBUFFER, t.fbo);
        glFramebufferRenderbuffer(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_RENDERBUFFER, t.color_rb);
        glFramebufferRenderbuffer(GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_RENDERBUFFER, t.depth_rb);
        if (glCheckFramebufferStatus(GL_FRAMEBUFFER) != GL_FRAMEBUFFER_COMPLETE) { pf_log("MSAA target incomplete: single-sampled"); glDeleteFramebuffers(1, &t.fbo); unsigned rb[2] = {t.color_rb, t.depth_rb}; glDeleteRenderbuffers(2, rb); t.fbo = t.color_rb = t.depth_rb = 0; t.samples = 1; }
    }
    if (t.samples <= 1) {
        glBindFramebuffer(GL_FRAMEBUFFER, t.rfbo);
        glGenRenderbuffers(1, &t.rdepth); glBindRenderbuffer(GL_RENDERBUFFER, t.rdepth);
        glRenderbufferStorageMultisample(GL_RENDERBUFFER, 0, GL_DEPTH_COMPONENT24, w, h);
        glFramebufferRenderbuffer(GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_RENDERBUFFER, t.rdepth);
        t.fbo = t.rfbo;
    }
    bool ok2 = glCheckFramebufferStatus(GL_FRAMEBUFFER) == GL_FRAMEBUFFER_COMPLETE;
    glBindFramebuffer(GL_FRAMEBUFFER, 0);
    if (!ok2) { pf_log("render target %dx%d incomplete", w, h); target_free(t); return false; }
    return true;
}
void Renderer::target_free(Target& t) {
    if (t.fbo && t.fbo != t.rfbo) glDeleteFramebuffers(1, &t.fbo);
    if (t.rfbo) glDeleteFramebuffers(1, &t.rfbo);
    unsigned rb[3] = {t.color_rb, t.depth_rb, t.rdepth}; for (unsigned x : rb) if (x) glDeleteRenderbuffers(1, &x);
    if (t.tex) glDeleteTextures(1, &t.tex);
    t = Target();
}
void Renderer::target_begin(Target& t) { cur_fbo = t.fbo; fbw = t.w; fbh = t.h; vx = vy = 0; vw = t.w; vh = t.h; }
void Renderer::target_end(Target& t) {
    if (t.fbo != t.rfbo) {
        glBindFramebuffer(GL_READ_FRAMEBUFFER, t.fbo); glBindFramebuffer(GL_DRAW_FRAMEBUFFER, t.rfbo);
        glDisable(GL_SCISSOR_TEST);
        glBlitFramebuffer(0, 0, t.w, t.h, 0, 0, t.w, t.h, GL_COLOR_BUFFER_BIT, GL_NEAREST);
        GLenum att[2] = {GL_COLOR_ATTACHMENT0, GL_DEPTH_ATTACHMENT};
        glBindFramebuffer(GL_FRAMEBUFFER, t.fbo); glInvalidateFramebuffer(GL_FRAMEBUFFER, 2, att);
    }
    glBindFramebuffer(GL_FRAMEBUFFER, 0); cur_fbo = 0;
    glDisable(GL_SCISSOR_TEST);
}

void Renderer::set_camera(const M4& v, const M4& p, V3 e) { view = v; proj = p; vp = p * v; eye = e; }

void Renderer::set_sun(V3 c, float s) {
    if (s < 1e-4f) s = 1;
    sun_center = c; sun_size = s;
    V3 off = V3(0.6f, 1.2f, 0.8f) * s, pos = c + off;
    sun_dir = norm(off);
    float d = len(off);
    M4 lv = m4_lookat(pos, c, V3(0, 1, 0));
    // three: ortho left/right/top/bottom = +-size; depth range tightened around the scene for precision
    M4 lp = m4_ortho(-s, s, -s, s, pf_max(0.01f, d - 1.5f * s), d + 2.5f * s);
    light_vp = lp * lv;
}

static void normal_matrix(const M4& w, float out[9]) {
    // inverse-transpose of the upper 3x3
    const float* m = w.m;
    float a = m[0], b = m[4], c = m[8], d = m[1], e = m[5], f = m[9], g = m[2], h = m[6], i = m[10];
    float A = e * i - f * h, B = -(d * i - f * g), C = d * h - e * g, det = a * A + b * B + c * C;
    if (fabsf(det) < 1e-20f) det = 1;
    float id = 1.f / det;
    // cofactor matrix / det (this is inverse-transpose), stored column-major
    out[0] = A * id; out[1] = B * id; out[2] = C * id;
    out[3] = -(b * i - c * h) * id; out[4] = (a * i - c * g) * id; out[5] = -(a * h - b * g) * id;
    out[6] = (b * f - c * e) * id; out[7] = -(a * f - c * d) * id; out[8] = (a * e - b * d) * id;
}
static float det3(const M4& w) { const float* m = w.m; return m[0] * (m[5] * m[10] - m[9] * m[6]) - m[4] * (m[1] * m[10] - m[9] * m[2]) + m[8] * (m[1] * m[6] - m[5] * m[2]); }

static void set_prim_uniforms(const MeshU& u, const DrawItem& it) {
    const Prim* p = it.p;
    glUniformMatrix4fv(u.model, 1, GL_FALSE_, it.world.m);
    glUniform3f(u.qc, p->c.x, p->c.y, p->c.z); glUniform3f(u.qh, p->h.x / 1.0f, p->h.y, p->h.z);
    V3 m0 = p->ntg > 0 ? p->ps[0] * it.w[0] : V3(), m1 = p->ntg > 1 ? p->ps[1] * it.w[1] : V3();
    glUniform3f(u.ms0, m0.x, m0.y, m0.z); glUniform3f(u.ms1, m1.x, m1.y, m1.z);
    glUniform2f(u.mn, p->ntg > 0 ? p->ns[0] * it.w[0] : 0.f, p->ntg > 1 ? p->ns[1] * it.w[1] : 0.f);
}

void Renderer::shadow_pass(Vec<DrawItem>& items) {
    if (!shadow_size) return;
    glBindFramebuffer(GL_FRAMEBUFFER, shadow_fbo);
    glViewport(0, 0, shadow_size, shadow_size); glDisable(GL_SCISSOR_TEST);
    glEnable(GL_DEPTH_TEST); glDepthFunc(GL_LEQUAL); glDepthMask(GL_TRUE_); glDisable(GL_BLEND);
    glClearDepthf(1); glClear(GL_DEPTH_BUFFER_BIT);
    glUseProgram(prog_depth);
    glUniformMatrix4fv(DU.vp, 1, GL_FALSE_, light_vp.m);
    glEnable(GL_POLYGON_OFFSET_FILL); glPolygonOffset(1.0f, 2.0f);
    for (DrawItem& it : items) {
        if (!it.cast_shadow || it.order >= 10) continue;
        // three.js shadowSide: FrontSide materials render their back faces into the map, DoubleSide both
        bool neg = det3(it.world) < 0;
        if (it.m && it.m->ds) glDisable(GL_CULL_FACE); else { glEnable(GL_CULL_FACE); glCullFace(GL_FRONT); }
        glFrontFace(neg ? GL_CW : GL_CCW);
        set_prim_uniforms(DU, it);
        glBindVertexArray(it.p->vao);
        glDrawElements(GL_TRIANGLES, it.p->ic, GL_UNSIGNED_SHORT, nullptr);
    }
    glDisable(GL_POLYGON_OFFSET_FILL); glFrontFace(GL_CCW);
    glBindFramebuffer(GL_FRAMEBUFFER, cur_fbo);
}

void Renderer::draw_mesh_pass(DrawItem& it, int side) {
    const Material* m = it.m;
    static Material def;
    if (!m) m = &def;
    bool neg = det3(it.world) < 0;
    glFrontFace(neg ? GL_CW : GL_CCW);
    if (side == 0) { if (m->ds) glDisable(GL_CULL_FACE); else { glEnable(GL_CULL_FACE); glCullFace(GL_BACK); } }
    else { glEnable(GL_CULL_FACE); glCullFace(side == 1 ? GL_FRONT : GL_BACK); }
    set_prim_uniforms(MU, it);
    float nm[9]; normal_matrix(it.world, nm); glUniformMatrix3fv(MU.nmat, 1, GL_FALSE_, nm);
    glUniform4f(MU.base, m->c[0], m->c[1], m->c[2], m->c[3]);
    glUniform1f(MU.metal, m->metal); glUniform1f(MU.rough, m->rough); glUniform1f(MU.opacity, it.opacity);
    glUniform1f(MU.recv, it.receive_shadow ? 1.f : 0.f);
    V3 e = it.highlight ? hex_linear(0x2a6fd6) : m->emissive;
    glUniform3f(MU.emis, e.x, e.y, e.z);
    glBindVertexArray(it.p->vao);
    glDrawElements(GL_TRIANGLES, it.p->ic, GL_UNSIGNED_SHORT, nullptr);
}

void Renderer::draw(Vec<DrawItem>& items, float ground_y, bool ground, const Vec<Particles>& parts) {
    shadow_pass(items);
    glBindFramebuffer(GL_FRAMEBUFFER, cur_fbo);
    glViewport(vx, vy, vw, vh); glEnable(GL_SCISSOR_TEST); glScissor(vx, vy, vw, vh);
    for (DrawItem& it : items) { V3 c = it.world.point(it.p->lbox.center()); const float* v = view.m; it.z = v[2] * c.x + v[6] * c.y + v[10] * c.z + v[14]; }
    // three.js order: opaque (renderOrder, then front-to-back), then transparent (renderOrder, then back-to-front)
    Vec<int> opq, trn;
    for (int i = 0; i < items.n; i++) (items[i].transparent ? trn : opq).push(i);
    auto sort = [&](Vec<int>& v, bool back_to_front) {
        for (int i = 1; i < v.n; i++) { int k = v[i], j = i - 1;
            auto less = [&](int a, int b) { if (items[a].order != items[b].order) return items[a].order < items[b].order; return back_to_front ? items[a].z < items[b].z : items[a].z > items[b].z; };
            while (j >= 0 && less(k, v[j])) { v[j + 1] = v[j]; j--; } v[j + 1] = k; }
    };
    sort(opq, false); sort(trn, true);
    glUseProgram(prog_mesh);
    glUniformMatrix4fv(MU.vp, 1, GL_FALSE_, vp.m); glUniformMatrix4fv(MU.light, 1, GL_FALSE_, light_vp.m);
    glUniform3f(MU.eye, eye.x, eye.y, eye.z); glUniform3f(MU.sundir, sun_dir.x, sun_dir.y, sun_dir.z);
    glActiveTexture(GL_TEXTURE0 + 1); glBindTexture(GL_TEXTURE_2D, shadow_tex); glUniform1i(MU.shadow, 1);
    glUniform2f(MU.smap, (float)(shadow_size ? shadow_size : 1), shadow_size ? 1.f : 0.f);
    glActiveTexture(GL_TEXTURE0 + 2); glBindTexture(0x8C1A, env_tex); glUniform1i(MU.env, 2);
    glUniform1f(MU.envn, (float)env_layers);
    glActiveTexture(GL_TEXTURE0);
    glEnable(GL_DEPTH_TEST); glDepthFunc(GL_LEQUAL); glDepthMask(GL_TRUE_); glDisable(GL_BLEND);
    // opaque with renderOrder < 6
    int oi = 0;
    for (; oi < opq.n && items[opq[oi]].order < 6; oi++) draw_mesh_pass(items[opq[oi]], 0);
    // particles: InstancedMesh, MeshBasicMaterial (opaque, renderOrder 6)
    if (parts.n) {
        glUseProgram(prog_part); glDisable(GL_CULL_FACE);
        glUniformMatrix4fv(glGetUniformLocation(prog_part, "u_vp"), 1, GL_FALSE_, vp.m);
        int lr = glGetUniformLocation(prog_part, "u_r"), lc = glGetUniformLocation(prog_part, "u_col");
        glBindVertexArray(sph_vao); glBindBuffer(GL_ARRAY_BUFFER, inst_vbo);
        for (const Particles& P : parts) {
            if (!P.pos.n) continue;
            if (P.pos.n > inst_cap) { while (inst_cap < P.pos.n) inst_cap *= 2; glBufferData(GL_ARRAY_BUFFER, inst_cap * 12, nullptr, GL_DYNAMIC_DRAW); }
            glBufferSubData(GL_ARRAY_BUFFER, 0, P.pos.n * 12, P.pos.d);
            glUniform1f(lr, P.radius); glUniform3f(lc, P.color.x, P.color.y, P.color.z);
            glDrawElementsInstanced(GL_TRIANGLES, sph_ic, GL_UNSIGNED_SHORT, nullptr, P.pos.n);
        }
        glUseProgram(prog_mesh);
    }
    for (; oi < opq.n; oi++) draw_mesh_pass(items[opq[oi]], 0);
    // shadow catcher ground (transparent, renderOrder 0 -> drawn first among transparent objects at similar depth)
    glEnable(GL_BLEND); glBlendFuncSeparate(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA, GL_ONE, GL_ONE_MINUS_SRC_ALPHA);
    if (ground) {
        glUseProgram(prog_ground); glDisable(GL_CULL_FACE); glDepthMask(GL_FALSE_);
        glUniformMatrix4fv(glGetUniformLocation(prog_ground, "u_vp"), 1, GL_FALSE_, vp.m);
        glUniformMatrix4fv(glGetUniformLocation(prog_ground, "u_light"), 1, GL_FALSE_, light_vp.m);
        glUniform3f(glGetUniformLocation(prog_ground, "u_c"), 0, 0, 0);
        glUniform1f(glGetUniformLocation(prog_ground, "u_r"), 30.f); glUniform1f(glGetUniformLocation(prog_ground, "u_y"), ground_y);
        glActiveTexture(GL_TEXTURE0 + 1); glBindTexture(GL_TEXTURE_2D, shadow_tex); glUniform1i(glGetUniformLocation(prog_ground, "u_shadow"), 1);
        glUniform2f(glGetUniformLocation(prog_ground, "u_smap"), (float)(shadow_size ? shadow_size : 1), shadow_size ? 1.f : 0.f);
        glActiveTexture(GL_TEXTURE0);
        glBindVertexArray(quad_vao); glDrawArrays(GL_TRIANGLE_STRIP, 0, 4);
        glUseProgram(prog_mesh);
    }
    for (int k = 0; k < trn.n; k++) {
        DrawItem& it = items[trn[k]];
        if (it.depth_test) glEnable(GL_DEPTH_TEST); else glDisable(GL_DEPTH_TEST);
        glDepthMask(it.depth_write ? GL_TRUE_ : GL_FALSE_);
        // three.js renders transparent double-sided materials as two passes: back faces, then front faces
        if (it.m && it.m->ds) { draw_mesh_pass(it, 1); draw_mesh_pass(it, 2); }
        else draw_mesh_pass(it, 0);
    }
    glDepthMask(GL_TRUE_); glEnable(GL_DEPTH_TEST); glDisable(GL_BLEND); glFrontFace(GL_CCW);
    glBindVertexArray(0);
}

void Renderer::end() { glDisable(GL_SCISSOR_TEST); glViewport(0, 0, fbw, fbh); }

bool Renderer::read_pixels(int x, int y, int w, int h, uint8_t* rgba) {
    glPixelStorei(GL_PACK_ALIGNMENT, 1);
    glReadPixels(x, y, w, h, GL_RGBA, GL_UNSIGNED_BYTE, rgba);
    return glGetError() == 0;
}
