// Engineering calculators (exact port of CALCS / FAMILY_CALCS / firstBy in library.html).
#pragma once
#include "base.h"

struct CalcField { const char* label; double def; };
struct Calc {
    const char* key; const char* title;
    CalcField f[8]; int nf;
    Str (*run)(const double* v);
};
extern const Calc CALCS[];
extern const int NCALCS;
const Calc* calc_find(const char* key);
// ordered calculator keys for a module: family set (by hi_family) with the module-specific ones first
void calc_keys_for(const char* module_id, const char* hi_family, Vec<const char*>& out);
