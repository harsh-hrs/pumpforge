#include "base.h"
#include <stdio.h>

Str& Str::vaddf(const char* fmt, va_list ap) {
    va_list a2; va_copy(a2, ap);
    char tmp[512];
    int k = vsnprintf(tmp, sizeof tmp, fmt, ap);
    if (k < 0) { va_end(a2); return *this; }
    if (k < (int)sizeof tmp) add(tmp, k);
    else { reserve(n + k); vsnprintf(s + n, (size_t)k + 1, fmt, a2); n += k; }
    va_end(a2);
    return *this;
}
Str& Str::addf(const char* fmt, ...) { va_list ap; va_start(ap, fmt); vaddf(fmt, ap); va_end(ap); return *this; }
Str Str::f(const char* fmt, ...) { Str r; va_list ap; va_start(ap, fmt); r.vaddf(fmt, ap); va_end(ap); return r; }

static inline char lc(char c) { return (c >= 'A' && c <= 'Z') ? (char)(c + 32) : c; }
bool ci_contains(const char* hay, const char* nd) {
    if (!nd || !*nd) return true;
    if (!hay) return false;
    size_t m = strlen(nd);
    for (const char* h = hay; *h; h++) {
        size_t i = 0;
        while (i < m && h[i] && lc(h[i]) == lc(nd[i])) i++;
        if (i == m) return true;
    }
    return false;
}
void str_lower(Str& s) { for (int i = 0; i < s.n; i++) s.s[i] = lc(s.s[i]); }

Str nice_key(const char* k) {
    Str r(k);
    for (int i = 0; i < r.n; i++) if (r.s[i] == '_') r.s[i] = ' ';
    if (r.n && r.s[0] >= 'a' && r.s[0] <= 'z') r.s[0] = (char)(r.s[0] - 32);
    return r;
}

Str fmt_num(double v) {
    if (v != v) return Str("NaN");
    if (isinf(v)) return Str(v > 0 ? "Infinity" : "-Infinity");
    if (v == 0) return Str("0");
    char b[64];
    for (int p = 1; p <= 17; p++) {
        snprintf(b, sizeof b, "%.*g", p, v);
        if (strtod(b, nullptr) == v) break;
    }
    // JS prints plain decimals for 1e-7 <= |v| < 1e21
    double a = fabs(v);
    if (strchr(b, 'e') && a >= 1e-7 && a < 1e21) {
        char c[400]; snprintf(c, sizeof c, "%.20f", v);
        // trim to the same significant digits: use repr from %.17g digits via strtod check
        for (int d = 0; d <= 20; d++) { snprintf(c, sizeof c, "%.*f", d, v); if (strtod(c, nullptr) == v) break; }
        return Str(c);
    }
    return Str(b);
}

// JS Number.prototype.toFixed: exact decimal expansion, ties rounded away from zero, "-" kept for negative inputs.
Str js_fixed(double x, int f) {
    if (x != x) return Str("NaN");
    if (isinf(x)) return Str(x > 0 ? "Infinity" : "-Infinity");
    if (fabs(x) >= 1e21) return fmt_num(x);
    bool neg = x < 0; if (neg) x = -x;
    char b[512];
    snprintf(b, sizeof b, "%.*f", f + 30, x);          // exact enough: digits beyond 17 sig are the binary expansion
    char* dot = strchr(b, '.');
    int ip = dot ? (int)(dot - b) : (int)strlen(b);
    // digits array: integer part + f fraction digits, then decide using the remaining digits
    char dg[400]; int nd = 0;
    for (int i = 0; i < ip; i++) dg[nd++] = b[i];
    for (int i = 0; i < f; i++) dg[nd++] = dot[1 + i];
    const char* rest = dot + 1 + f;
    bool up = rest[0] >= '5';                           // >= half: JS picks the larger n on exact ties
    if (up) {
        int i = nd - 1;
        while (i >= 0) { if (dg[i] == '9') { dg[i] = '0'; i--; } else { dg[i]++; break; } }
        if (i < 0) { memmove(dg + 1, dg, (size_t)nd); dg[0] = '1'; nd++; ip++; }
    }
    Str r; if (neg) r.add('-');
    r.add(dg, ip);
    if (f > 0) { r.add('.'); r.add(dg + ip, f); }
    return r;
}

// ------------------------------------------------------------------ math
M4 M4::operator*(const M4& b) const {
    M4 r;
    for (int c = 0; c < 4; c++)
        for (int rr = 0; rr < 4; rr++)
            r.m[c * 4 + rr] = m[0 * 4 + rr] * b.m[c * 4 + 0] + m[1 * 4 + rr] * b.m[c * 4 + 1] + m[2 * 4 + rr] * b.m[c * 4 + 2] + m[3 * 4 + rr] * b.m[c * 4 + 3];
    return r;
}
M4 m4_trs(V3 t, Quat q, V3 s) {
    float x = q.x, y = q.y, z = q.z, w = q.w;
    float x2 = x + x, y2 = y + y, z2 = z + z, xx = x * x2, xy = x * y2, xz = x * z2, yy = y * y2, yz = y * z2, zz = z * z2, wx = w * x2, wy = w * y2, wz = w * z2;
    M4 r;
    r.m[0] = (1 - (yy + zz)) * s.x; r.m[1] = (xy + wz) * s.x; r.m[2] = (xz - wy) * s.x; r.m[3] = 0;
    r.m[4] = (xy - wz) * s.y; r.m[5] = (1 - (xx + zz)) * s.y; r.m[6] = (yz + wx) * s.y; r.m[7] = 0;
    r.m[8] = (xz + wy) * s.z; r.m[9] = (yz - wx) * s.z; r.m[10] = (1 - (xx + yy)) * s.z; r.m[11] = 0;
    r.m[12] = t.x; r.m[13] = t.y; r.m[14] = t.z; r.m[15] = 1;
    return r;
}
M4 m4_persp(float fovy, float aspect, float n, float f) {
    M4 r; memset(r.m, 0, sizeof r.m);
    float t = 1.f / tanf(fovy / 2);
    r.m[0] = t / aspect; r.m[5] = t; r.m[10] = (f + n) / (n - f); r.m[11] = -1; r.m[14] = 2 * f * n / (n - f);
    return r;
}
M4 m4_ortho(float l, float r_, float b, float t, float n, float f) {
    M4 r = M4::id();
    r.m[0] = 2 / (r_ - l); r.m[5] = 2 / (t - b); r.m[10] = -2 / (f - n);
    r.m[12] = -(r_ + l) / (r_ - l); r.m[13] = -(t + b) / (t - b); r.m[14] = -(f + n) / (f - n);
    return r;
}
M4 m4_lookat(V3 eye, V3 at, V3 up) {
    V3 z = norm(eye - at);
    V3 x = cross(up, z);
    if (len(x) < 1e-6f) x = cross(fabsf(up.z) < 0.9f ? V3(0, 0, 1) : V3(1, 0, 0), z);
    x = norm(x);
    V3 y = cross(z, x);
    M4 r = M4::id();
    r.m[0] = x.x; r.m[4] = x.y; r.m[8] = x.z;
    r.m[1] = y.x; r.m[5] = y.y; r.m[9] = y.z;
    r.m[2] = z.x; r.m[6] = z.y; r.m[10] = z.z;
    r.m[12] = -dot(x, eye); r.m[13] = -dot(y, eye); r.m[14] = -dot(z, eye);
    return r;
}
M4 m4_inverse(const M4& a) {
    const float* m = a.m; float inv[16];
    inv[0] = m[5] * m[10] * m[15] - m[5] * m[11] * m[14] - m[9] * m[6] * m[15] + m[9] * m[7] * m[14] + m[13] * m[6] * m[11] - m[13] * m[7] * m[10];
    inv[4] = -m[4] * m[10] * m[15] + m[4] * m[11] * m[14] + m[8] * m[6] * m[15] - m[8] * m[7] * m[14] - m[12] * m[6] * m[11] + m[12] * m[7] * m[10];
    inv[8] = m[4] * m[9] * m[15] - m[4] * m[11] * m[13] - m[8] * m[5] * m[15] + m[8] * m[7] * m[13] + m[12] * m[5] * m[11] - m[12] * m[7] * m[9];
    inv[12] = -m[4] * m[9] * m[14] + m[4] * m[10] * m[13] + m[8] * m[5] * m[14] - m[8] * m[6] * m[13] - m[12] * m[5] * m[10] + m[12] * m[6] * m[9];
    inv[1] = -m[1] * m[10] * m[15] + m[1] * m[11] * m[14] + m[9] * m[2] * m[15] - m[9] * m[3] * m[14] - m[13] * m[2] * m[11] + m[13] * m[3] * m[10];
    inv[5] = m[0] * m[10] * m[15] - m[0] * m[11] * m[14] - m[8] * m[2] * m[15] + m[8] * m[3] * m[14] + m[12] * m[2] * m[11] - m[12] * m[3] * m[10];
    inv[9] = -m[0] * m[9] * m[15] + m[0] * m[11] * m[13] + m[8] * m[1] * m[15] - m[8] * m[3] * m[13] - m[12] * m[1] * m[11] + m[12] * m[3] * m[9];
    inv[13] = m[0] * m[9] * m[14] - m[0] * m[10] * m[13] - m[8] * m[1] * m[14] + m[8] * m[2] * m[13] + m[12] * m[1] * m[10] - m[12] * m[2] * m[9];
    inv[2] = m[1] * m[6] * m[15] - m[1] * m[7] * m[14] - m[5] * m[2] * m[15] + m[5] * m[3] * m[14] + m[13] * m[2] * m[7] - m[13] * m[3] * m[6];
    inv[6] = -m[0] * m[6] * m[15] + m[0] * m[7] * m[14] + m[4] * m[2] * m[15] - m[4] * m[3] * m[14] - m[12] * m[2] * m[7] + m[12] * m[3] * m[6];
    inv[10] = m[0] * m[5] * m[15] - m[0] * m[7] * m[13] - m[4] * m[1] * m[15] + m[4] * m[3] * m[13] + m[12] * m[1] * m[7] - m[12] * m[3] * m[5];
    inv[14] = -m[0] * m[5] * m[14] + m[0] * m[6] * m[13] + m[4] * m[1] * m[14] - m[4] * m[2] * m[13] - m[12] * m[1] * m[6] + m[12] * m[2] * m[5];
    inv[3] = -m[1] * m[6] * m[11] + m[1] * m[7] * m[10] + m[5] * m[2] * m[11] - m[5] * m[3] * m[10] - m[9] * m[2] * m[7] + m[9] * m[3] * m[6];
    inv[7] = m[0] * m[6] * m[11] - m[0] * m[7] * m[10] - m[4] * m[2] * m[11] + m[4] * m[3] * m[10] + m[8] * m[2] * m[7] - m[8] * m[3] * m[6];
    inv[11] = -m[0] * m[5] * m[11] + m[0] * m[7] * m[9] + m[4] * m[1] * m[11] - m[4] * m[3] * m[9] - m[8] * m[1] * m[7] + m[8] * m[3] * m[5];
    inv[15] = m[0] * m[5] * m[10] - m[0] * m[6] * m[9] - m[4] * m[1] * m[10] + m[4] * m[2] * m[9] + m[8] * m[1] * m[6] - m[8] * m[2] * m[5];
    float det = m[0] * inv[0] + m[1] * inv[4] + m[2] * inv[8] + m[3] * inv[12];
    M4 r; if (fabsf(det) < 1e-30f) return M4::id();
    det = 1.f / det; for (int i = 0; i < 16; i++) r.m[i] = inv[i] * det;
    return r;
}
bool m4_project(const M4& vp, V3 p, float& x, float& y, float& z) {
    const float* m = vp.m;
    float cx = m[0] * p.x + m[4] * p.y + m[8] * p.z + m[12], cy = m[1] * p.x + m[5] * p.y + m[9] * p.z + m[13];
    float cz = m[2] * p.x + m[6] * p.y + m[10] * p.z + m[14], cw = m[3] * p.x + m[7] * p.y + m[11] * p.z + m[15];
    if (cw <= 1e-9f) { x = y = 0; z = 2; return false; }
    x = cx / cw; y = cy / cw; z = cz / cw;
    return true;
}
Quat qnorm(Quat q) { float l = sqrtf(q.x * q.x + q.y * q.y + q.z * q.z + q.w * q.w); if (l < 1e-12f) return Quat(); return {q.x / l, q.y / l, q.z / l, q.w / l}; }
Quat qslerp(Quat a, Quat b, float t) {   // matches three.js Quaternion.slerpFlat
    float c = a.x * b.x + a.y * b.y + a.z * b.z + a.w * b.w;
    if (c < 0) { b.x = -b.x; b.y = -b.y; b.z = -b.z; b.w = -b.w; c = -c; }
    float s0 = 1 - t, s1 = t;
    if (1 - c > 1e-6f) { float th = acosf(pf_min(c, 1.f)), sn = sinf(th); s0 = sinf(s0 * th) / sn; s1 = sinf(s1 * th) / sn; }
    Quat r{a.x * s0 + b.x * s1, a.y * s0 + b.y * s1, a.z * s0 + b.z * s1, a.w * s0 + b.w * s1};
    return qnorm(r);
}
float srgb_to_linear(float c) { return c < 0.04045f ? c * 0.0773993808f : powf(c * 0.9478672986f + 0.0521327014f, 2.4f); }
V3 hex_linear(uint32_t h) { return {srgb_to_linear(((h >> 16) & 255) / 255.f), srgb_to_linear(((h >> 8) & 255) / 255.f), srgb_to_linear((h & 255) / 255.f)}; }

// ------------------------------------------------------------------ arena
void* Arena::alloc(size_t sz) {
    sz = (sz + 7) & ~(size_t)7;
    if (!head || head->used + sz > head->cap) {
        size_t cap = sz > 60000 ? sz : 60000;
        Blk* b = (Blk*)malloc(sizeof(Blk) + cap);
        if (!b) pf_fatal("arena oom");
        b->next = head; b->used = 0; b->cap = cap; head = b;
    }
    void* p = (char*)(head + 1) + head->used;
    head->used += sz;
    return p;
}
void Arena::reset() { while (head) { Blk* n = head->next; free(head); head = n; } }
