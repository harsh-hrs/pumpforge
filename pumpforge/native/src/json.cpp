#include "json.h"
#include <stdio.h>

const JV JNULL;

const JV& JV::operator[](const char* k) const {
    if (t != Object) return JNULL;
    for (const JV* c = first; c; c = c->next) if (streq(c->key, k)) return *c;
    return JNULL;
}
const JV& JV::operator[](int i) const {
    if (t != Array && t != Object) return JNULL;
    const JV* c = first;
    while (c && i-- > 0) c = c->next;
    return c ? *c : JNULL;
}
bool JV::has(const char* k) const {
    if (t != Object) return false;
    for (const JV* c = first; c; c = c->next) if (streq(c->key, k)) return true;
    return false;
}
bool JV::truthy() const {
    switch (t) { case Null: return false; case Bool: return b; case Num: return num != 0 && num == num; case String: return slen > 0; default: return true; }
}
Str JV::text() const {
    if (t == String) return Str(s, slen);
    if (t == Num) return fmt_num(num);
    if (t == Bool) return Str(b ? "true" : "false");
    return Str();
}

namespace {
struct P {
    const char* p; const char* e; Arena* a; char* err;
    void ws() { while (p < e && (*p == ' ' || *p == '\n' || *p == '\r' || *p == '\t')) p++; }
    bool fail(const char* m) { snprintf(err, 160, "%s at offset %d", m, (int)(e - p)); return false; }
    static int hex(char c) { return c >= '0' && c <= '9' ? c - '0' : (c >= 'a' && c <= 'f' ? c - 'a' + 10 : (c >= 'A' && c <= 'F' ? c - 'A' + 10 : -1)); }
    bool string(const char*& out, int& olen) {
        p++;  // opening quote
        const char* st = p; bool esc = false;
        while (p < e && *p != '"') { if (*p == '\\') { esc = true; p++; } p++; }
        if (p >= e) return fail("unterminated string");
        size_t raw = (size_t)(p - st);
        char* d = (char*)a->alloc(raw + 1);
        if (!esc) { memcpy(d, st, raw); d[raw] = 0; out = d; olen = (int)raw; p++; return true; }
        char* w = d;
        for (const char* q = st; q < p; q++) {
            if (*q != '\\') { *w++ = *q; continue; }
            q++;
            switch (*q) {
                case 'n': *w++ = '\n'; break; case 't': *w++ = '\t'; break; case 'r': *w++ = '\r'; break;
                case 'b': *w++ = '\b'; break; case 'f': *w++ = '\f'; break;
                case 'u': {
                    if (q + 4 >= p + 1) return fail("bad \\u");
                    unsigned cp = 0; for (int i = 1; i <= 4; i++) { int h = hex(q[i]); if (h < 0) return fail("bad hex"); cp = cp * 16 + (unsigned)h; }
                    q += 4;
                    if (cp >= 0xD800 && cp < 0xDC00 && q + 6 < p + 1 && q[1] == '\\' && q[2] == 'u') {
                        unsigned lo = 0; bool ok = true; for (int i = 3; i <= 6; i++) { int h = hex(q[i]); if (h < 0) { ok = false; break; } lo = lo * 16 + (unsigned)h; }
                        if (ok && lo >= 0xDC00 && lo < 0xE000) { cp = 0x10000 + ((cp - 0xD800) << 10) + (lo - 0xDC00); q += 6; }
                    }
                    if (cp < 0x80) *w++ = (char)cp;
                    else if (cp < 0x800) { *w++ = (char)(0xC0 | (cp >> 6)); *w++ = (char)(0x80 | (cp & 63)); }
                    else if (cp < 0x10000) { *w++ = (char)(0xE0 | (cp >> 12)); *w++ = (char)(0x80 | ((cp >> 6) & 63)); *w++ = (char)(0x80 | (cp & 63)); }
                    else { *w++ = (char)(0xF0 | (cp >> 18)); *w++ = (char)(0x80 | ((cp >> 12) & 63)); *w++ = (char)(0x80 | ((cp >> 6) & 63)); *w++ = (char)(0x80 | (cp & 63)); }
                    break;
                }
                default: *w++ = *q;
            }
        }
        *w = 0; out = d; olen = (int)(w - d); p++;
        return true;
    }
    bool value(JV* v, int depth) {
        if (depth > 200) return fail("too deep");
        ws(); if (p >= e) return fail("unexpected end");
        char c = *p;
        if (c == '{' || c == '[') {
            bool obj = c == '{'; v->t = obj ? JV::Object : JV::Array; p++;
            JV** tail = &v->first;
            ws(); if (p < e && *p == (obj ? '}' : ']')) { p++; return true; }
            for (;;) {
                JV* ch = (JV*)a->alloc(sizeof(JV)); PF_PLACE(ch) JV();
                if (obj) {
                    ws(); if (p >= e || *p != '"') return fail("expected key");
                    int kl; if (!string(ch->key, kl)) return false;
                    ws(); if (p >= e || *p != ':') return fail("expected :"); p++;
                }
                if (!value(ch, depth + 1)) return false;
                *tail = ch; tail = &ch->next; v->count++;
                ws(); if (p >= e) return fail("unexpected end");
                if (*p == ',') { p++; continue; }
                if (*p == (obj ? '}' : ']')) { p++; return true; }
                return fail("expected , or close");
            }
        }
        if (c == '"') { v->t = JV::String; return string(v->s, v->slen); }
        if (c == 't' && e - p >= 4 && !memcmp(p, "true", 4)) { v->t = JV::Bool; v->b = true; p += 4; return true; }
        if (c == 'f' && e - p >= 5 && !memcmp(p, "false", 5)) { v->t = JV::Bool; v->b = false; p += 5; return true; }
        if (c == 'n' && e - p >= 4 && !memcmp(p, "null", 4)) { v->t = JV::Null; p += 4; return true; }
        if (c == '-' || (c >= '0' && c <= '9')) {
            char buf[64]; int k = 0;
            while (p < e && k < 63 && (strchr("+-.eE", *p) || (*p >= '0' && *p <= '9'))) buf[k++] = *p++;
            buf[k] = 0; v->t = JV::Num; v->num = strtod(buf, nullptr);
            return true;
        }
        return fail("bad token");
    }
};
}

bool JDoc::parse(const char* text, size_t len) {
    arena.reset(); root = nullptr; err[0] = 0;
    P ps{text, text + len, &arena, err};
    // skip UTF-8 BOM
    if (len >= 3 && (unsigned char)text[0] == 0xEF && (unsigned char)text[1] == 0xBB && (unsigned char)text[2] == 0xBF) ps.p += 3;
    JV* r = (JV*)arena.alloc(sizeof(JV)); PF_PLACE(r) JV();
    if (!ps.value(r, 0)) return false;
    root = r;
    return true;
}

void JW::str_(const char* v) {
    o.add('"');
    for (const unsigned char* q = (const unsigned char*)(v ? v : ""); *q; q++) {
        unsigned char c = *q;
        if (c == '"') o.add("\\\""); else if (c == '\\') o.add("\\\\");
        else if (c == '\n') o.add("\\n"); else if (c == '\r') o.add("\\r"); else if (c == '\t') o.add("\\t");
        else if (c < 0x20) o.addf("\\u%04x", c);
        else o.add((char)c);
    }
    o.add('"');
}
void json_write_value(JW& w, const JV& v) {
    switch (v.t) {
        case JV::Null: w.null(); break;
        case JV::Bool: w.boolean(v.b); break;
        case JV::Num: w.num(v.num); break;
        case JV::String: w.str(v.s); break;
        case JV::Array: w.beginArr(); for (const JV& c : v) json_write_value(w, c); w.endArr(); break;
        case JV::Object: w.beginObj(); for (const JV& c : v) { w.key(c.key); json_write_value(w, c); } w.endObj(); break;
    }
}
