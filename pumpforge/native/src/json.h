// Minimal JSON DOM (arena allocated, read-only) + a small writer used for the progress store.
#pragma once
#include "base.h"

struct JV {
    enum T : uint8_t { Null, Bool, Num, String, Array, Object } t = Null;
    bool b = false;
    double num = 0;
    const char* s = "";      // string value (UTF-8, unescaped, NUL-terminated)
    int slen = 0;
    const char* key = nullptr;   // when inside an object
    JV* first = nullptr;     // children
    JV* next = nullptr;
    int count = 0;

    bool isNull() const { return t == Null; }
    bool isObj() const { return t == Object; }
    bool isArr() const { return t == Array; }
    bool isStr() const { return t == String; }
    bool isNum() const { return t == Num; }
    const JV& operator[](const char* k) const;   // object member (or a shared Null)
    const JV& operator[](int i) const;           // array element (or Null)
    bool has(const char* k) const;
    int size() const { return (t == Array || t == Object) ? count : 0; }
    const char* str(const char* def = "") const { return t == String ? s : def; }
    double n(double def = 0) const { return t == Num ? num : (t == Bool ? (b ? 1 : 0) : def); }
    bool truthy() const;
    Str text() const;           // display text: strings as-is, numbers JS-formatted, null -> ""
    struct It { const JV* p; const JV& operator*() const { return *p; } It& operator++() { p = p->next; return *this; } bool operator!=(const It& o) const { return p != o.p; } };
    It begin() const { return {(t == Array || t == Object) ? first : nullptr}; }
    It end() const { return {nullptr}; }
};
extern const JV JNULL;

struct JDoc {
    Arena arena;
    JV* root = nullptr;
    char err[160] = {0};
    bool parse(const char* text, size_t len);
};

// writer
struct JW {
    Str o;
    Vec<int> first;   // stack: whether next item is the first in the container
    void sep() { if (first.n) { if (!first.back()) o.add(','); first.back() = 0; } }
    JW& beginObj() { sep(); o.add('{'); first.push(1); return *this; }
    JW& endObj() { o.add('}'); first.pop(); return *this; }
    JW& beginArr() { sep(); o.add('['); first.push(1); return *this; }
    JW& endArr() { o.add(']'); first.pop(); return *this; }
    JW& key(const char* k) { sep(); str_(k); o.add(':'); if (first.n) first.back() = 1; return *this; }
    JW& str(const char* v) { sep(); str_(v); return *this; }
    JW& num(double v) { sep(); o.add(fmt_num(v).c()); return *this; }
    JW& boolean(bool v) { sep(); o.add(v ? "true" : "false"); return *this; }
    JW& null() { sep(); o.add("null"); return *this; }
    void str_(const char* v);
};
void json_write_value(JW& w, const JV& v);   // re-serialise a DOM value
