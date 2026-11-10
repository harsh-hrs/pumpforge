#include "glapi.h"
// dlopen/dlsym declared directly: musl's <dlfcn.h> renames dlsym on 32-bit targets, and bionic's flag values differ by ABI
#ifdef PF_NDK_BUILD
#include <dlfcn.h>
#else
extern "C" { void* dlopen(const char* file, int mode); void* dlsym(void* handle, const char* name); }
#endif
static const int PF_RTLD_NOW = sizeof(void*) == 8 ? 2 : 0;   // bionic: RTLD_NOW is 2 on LP64, 0 on 32-bit; RTLD_LOCAL is 0
#include <stdio.h>

#define PF_DEF(ret, name, args) PFN_##name name = nullptr;
PF_GL_FUNCS(PF_DEF)
PF_EGL_FUNCS(PF_DEF)
#undef PF_DEF

bool gl_load(const char* egl_lib, const char* gles_lib, char* err, int errlen) {
    void* egl = dlopen(egl_lib, PF_RTLD_NOW);
    if (!egl) { snprintf(err, (size_t)errlen, "cannot open %s", egl_lib); return false; }
    void* gles = dlopen(gles_lib, PF_RTLD_NOW);
    if (!gles) { snprintf(err, (size_t)errlen, "cannot open %s", gles_lib); return false; }
#define PF_LOAD_EGL(ret, name, args) name = (PFN_##name)dlsym(egl, #name); if (!name) { snprintf(err, (size_t)errlen, "missing %s", #name); return false; }
    PF_EGL_FUNCS(PF_LOAD_EGL)
#undef PF_LOAD_EGL
#define PF_LOAD_GL(ret, name, args) name = (PFN_##name)dlsym(gles, #name); if (!name) name = (PFN_##name)eglGetProcAddress(#name); if (!name) { snprintf(err, (size_t)errlen, "missing %s", #name); return false; }
    PF_GL_FUNCS(PF_LOAD_GL)
#undef PF_LOAD_GL
    return true;
}
