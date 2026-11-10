// PumpForge native - core utilities (no STL: the Android build links only against bionic's C library).
#pragma once
#include <stddef.h>
#include <stdint.h>
#include <string.h>
#include <stdlib.h>
#include <stdarg.h>
#include <math.h>

void pf_log(const char* fmt, ...);
[[noreturn]] void pf_fatal(const char* fmt, ...);
#define PF_ASSERT(x) do { if (!(x)) pf_fatal("assert %s:%d %s", __FILE__, __LINE__, #x); } while (0)

inline void* operator new(size_t, void* p, int) noexcept { return p; }   // placement helper (no <new>)
#define PF_PLACE(p) new ((void*)(p), 0)

template <class T> inline T pf_min(T a, T b) { return a < b ? a : b; }
template <class T> inline T pf_max(T a, T b) { return a > b ? a : b; }
template <class T> inline T pf_clamp(T v, T a, T b) { return v < a ? a : (v > b ? b : v); }
template <class T> inline void pf_swap(T& a, T& b) { T t = a; a = b; b = t; }

// ------------------------------------------------------------------ growable array
template <class T> struct Vec {
    T* d = nullptr; int n = 0, cap = 0;
    Vec() {}
    Vec(const Vec& o) { *this = o; }
    Vec& operator=(const Vec& o) { if (this == &o) return *this; clear(); reserve(o.n); for (int i = 0; i < o.n; i++) PF_PLACE(d + i) T(o.d[i]); n = o.n; return *this; }
    ~Vec() { clear(); free(d); }
    void reserve(int c) {
        if (c <= cap) return;
        int nc = cap ? cap : 8; while (nc < c) nc *= 2;
        T* nd = (T*)malloc(sizeof(T) * (size_t)nc);
        if (!nd) pf_fatal("out of memory (%d x %d)", nc, (int)sizeof(T));
        for (int i = 0; i < n; i++) { PF_PLACE(nd + i) T(static_cast<T&&>(d[i])); d[i].~T(); }
        free(d); d = nd; cap = nc;
    }
    T& push(const T& v) { if (n == cap) { T tmp(v); reserve(n + 1); PF_PLACE(d + n) T(static_cast<T&&>(tmp)); } else PF_PLACE(d + n) T(v); return d[n++]; }
    T& push() { reserve(n + 1); PF_PLACE(d + n) T(); return d[n++]; }
    void pop() { d[--n].~T(); }
    void resize(int m) { reserve(m); while (n < m) PF_PLACE(d + n++) T(); while (n > m) d[--n].~T(); }
    void clear() { while (n > 0) d[--n].~T(); }
    void erase(int i) { for (int k = i; k < n - 1; k++) d[k] = static_cast<T&&>(d[k + 1]); pop(); }
    T& operator[](int i) { return d[i]; }
    const T& operator[](int i) const { return d[i]; }
    T& back() { return d[n - 1]; }
    T* begin() { return d; } T* end() { return d + n; }
    const T* begin() const { return d; } const T* end() const { return d + n; }
    int size() const { return n; }
    bool empty() const { return n == 0; }
    template <class F> int find(F f) const { for (int i = 0; i < n; i++) if (f(d[i])) return i; return -1; }
};

// ------------------------------------------------------------------ string
struct Str {
    char* s = nullptr; int n = 0, cap = 0;
    Str() {}
    Str(const char* c) { set(c); }
    Str(const char* c, int len) { set(c, len); }
    Str(const Str& o) { set(o.c(), o.n); }
    Str(Str&& o) noexcept { s = o.s; n = o.n; cap = o.cap; o.s = nullptr; o.n = o.cap = 0; }
    Str& operator=(const Str& o) { if (this != &o) set(o.c(), o.n); return *this; }
    Str& operator=(Str&& o) noexcept { if (this != &o) { free(s); s = o.s; n = o.n; cap = o.cap; o.s = nullptr; o.n = o.cap = 0; } return *this; }
    Str& operator=(const char* c) { set(c); return *this; }
    ~Str() { free(s); }
    void reserve(int c) { if (c + 1 <= cap) return; int nc = cap ? cap : 16; while (nc < c + 1) nc *= 2; char* ns = (char*)realloc(s, (size_t)nc); if (!ns) pf_fatal("oom"); s = ns; cap = nc; }
    void set(const char* c, int len = -1) { if (!c) c = ""; if (len < 0) len = (int)strlen(c); if (c >= s && s && c < s + cap) { Str t(c, len); *this = static_cast<Str&&>(t); return; } reserve(len); memcpy(s, c, (size_t)len); s[len] = 0; n = len; }
    const char* c() const { return s ? s : ""; }
    operator const char*() const { return c(); }
    Str& add(const char* c, int len = -1) { if (!c) return *this; if (len < 0) len = (int)strlen(c); reserve(n + len); memmove(s + n, c, (size_t)len); n += len; s[n] = 0; return *this; }
    Str& add(char ch) { reserve(n + 1); s[n++] = ch; s[n] = 0; return *this; }
    Str& addf(const char* fmt, ...) __attribute__((format(printf, 2, 3)));
    Str& vaddf(const char* fmt, va_list ap);
    static Str f(const char* fmt, ...) __attribute__((format(printf, 1, 2)));
    bool eq(const char* o) const { return strcmp(c(), o ? o : "") == 0; }
    bool empty() const { return n == 0; }
    void clear() { n = 0; if (s) s[0] = 0; }
};
inline bool streq(const char* a, const char* b) { return strcmp(a ? a : "", b ? b : "") == 0; }
bool ci_contains(const char* hay, const char* needle);   // ASCII case-insensitive substring
void str_lower(Str& s);
Str nice_key(const char* k);                            // "rated_flow" -> "Rated flow"
Str fmt_num(double v);                                   // JS-like Number -> string (shortest round-trip-ish)
Str js_fixed(double v, int digits);                      // JS toFixed()

// ------------------------------------------------------------------ math
struct V3 { float x = 0, y = 0, z = 0; V3() {} V3(float a, float b, float c) : x(a), y(b), z(c) {}
    V3 operator+(V3 o) const { return {x + o.x, y + o.y, z + o.z}; } V3 operator-(V3 o) const { return {x - o.x, y - o.y, z - o.z}; }
    V3 operator*(float s) const { return {x * s, y * s, z * s}; } V3 operator-() const { return {-x, -y, -z}; }
    V3& operator+=(V3 o) { x += o.x; y += o.y; z += o.z; return *this; } V3& operator-=(V3 o) { x -= o.x; y -= o.y; z -= o.z; return *this; }
    float& operator[](int i) { return (&x)[i]; } float operator[](int i) const { return (&x)[i]; } };
inline float dot(V3 a, V3 b) { return a.x * b.x + a.y * b.y + a.z * b.z; }
inline V3 cross(V3 a, V3 b) { return {a.y * b.z - a.z * b.y, a.z * b.x - a.x * b.z, a.x * b.y - a.y * b.x}; }
inline float len(V3 a) { return sqrtf(dot(a, a)); }
inline V3 norm(V3 a) { float l = len(a); return l > 1e-12f ? a * (1.f / l) : V3(0, 0, 1); }
inline V3 vmin(V3 a, V3 b) { return {fminf(a.x, b.x), fminf(a.y, b.y), fminf(a.z, b.z)}; }
inline V3 vmax(V3 a, V3 b) { return {fmaxf(a.x, b.x), fmaxf(a.y, b.y), fmaxf(a.z, b.z)}; }
inline V3 lerp(V3 a, V3 b, float t) { return a + (b - a) * t; }

struct Quat { float x = 0, y = 0, z = 0, w = 1; };
Quat qslerp(Quat a, Quat b, float t);
Quat qnorm(Quat q);

struct M4 { float m[16]; // column-major (OpenGL)
    static M4 id() { M4 r; memset(r.m, 0, sizeof r.m); r.m[0] = r.m[5] = r.m[10] = r.m[15] = 1; return r; }
    M4 operator*(const M4& b) const;
    V3 point(V3 p) const { return {m[0] * p.x + m[4] * p.y + m[8] * p.z + m[12], m[1] * p.x + m[5] * p.y + m[9] * p.z + m[13], m[2] * p.x + m[6] * p.y + m[10] * p.z + m[14]}; }
    V3 dir(V3 p) const { return {m[0] * p.x + m[4] * p.y + m[8] * p.z, m[1] * p.x + m[5] * p.y + m[9] * p.z, m[2] * p.x + m[6] * p.y + m[10] * p.z}; }
};
M4 m4_trs(V3 t, Quat r, V3 s);
M4 m4_persp(float fovy_rad, float aspect, float n, float f);
M4 m4_ortho(float l, float r, float b, float t, float n, float f);
M4 m4_lookat(V3 eye, V3 at, V3 up);
M4 m4_inverse(const M4& a);
bool m4_project(const M4& vp, V3 p, float& ndc_x, float& ndc_y, float& ndc_z);   // false if behind camera

struct Box { V3 lo{1e30f, 1e30f, 1e30f}, hi{-1e30f, -1e30f, -1e30f};
    bool valid() const { return lo.x <= hi.x; }
    void add(V3 p) { lo = vmin(lo, p); hi = vmax(hi, p); }
    void add(const Box& b) { if (b.valid()) { add(b.lo); add(b.hi); } }
    V3 center() const { return (lo + hi) * 0.5f; } V3 size() const { return hi - lo; }
};

// colour helpers: sRGB hex -> linear (three.js Color.setHex converts sRGB to linear working space)
float srgb_to_linear(float c);
V3 hex_linear(uint32_t hex);

// ------------------------------------------------------------------ simple arena for JSON etc.
struct Arena {
    struct Blk { Blk* next; size_t used, cap; };
    Blk* head = nullptr;
    ~Arena() { reset(); }
    void* alloc(size_t sz);
    void reset();
};
