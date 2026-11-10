// Minimal C++ runtime for the Android build (no libc++): allocation operators and ABI hooks.
#include <stdlib.h>
#include <stddef.h>
extern "C" {
#ifndef PF_NDK_BUILD   // the NDK's crtbegin_so.o defines __dso_handle
__attribute__((visibility("hidden"))) void* __dso_handle = &__dso_handle;
#endif
void __cxa_pure_virtual() { abort(); }
}
void* operator new(size_t n) { void* p = malloc(n ? n : 1); if (!p) abort(); return p; }
void* operator new[](size_t n) { void* p = malloc(n ? n : 1); if (!p) abort(); return p; }
void operator delete(void* p) noexcept { free(p); }
void operator delete[](void* p) noexcept { free(p); }
void operator delete(void* p, size_t) noexcept { free(p); }
void operator delete[](void* p, size_t) noexcept { free(p); }
