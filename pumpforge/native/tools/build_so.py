"""Cross-compile libpumpforge.so for Android (arm64-v8a, x86_64) without the NDK.

How: clang/lld --target=<arch>-linux-android24, C library *headers* from musl (shipped with zig) - only
ABI-identical parts are used (no errno, no pthread, no TLS) - and link-time stub libraries carrying the
exact bionic / NDK symbol names. Every undefined symbol must be on the allow-lists below (checked
against the NDK API-24 symbol sets), so a typo or a non-NDK symbol fails the build instead of the phone.
"""
import os, subprocess, sys, glob, concurrent.futures as cf

N = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
B = os.path.join(N, 'build', 'android')
ZIG = None
for p in sys.path:
    if os.path.isdir(os.path.join(p, 'ziglang', 'lib', 'libc', 'include')):
        ZIG = os.path.join(p, 'ziglang')
if not ZIG:
    ZIG = '/usr/local/lib/python3.13/site-packages/ziglang'
JNI = '/usr/lib/jvm/java-21-openjdk-amd64/include'
RES = subprocess.run(['clang', '-print-resource-dir'], capture_output=True, text=True).stdout.strip()

ARCHES = {'arm64-v8a': ('aarch64', 'aarch64-linux-musl', 'aarch64-linux-any'), 'armeabi-v7a': ('armv7a', 'arm-linux-musl', 'arm-linux-any'),
          'x86_64': ('x86_64', 'x86_64-linux-musl', 'x86-linux-any')}
TRIPLE = {'aarch64': 'aarch64-linux-android24', 'armv7a': 'armv7a-linux-androideabi24', 'x86_64': 'x86_64-linux-android24'}

LIBC = set('''memcpy memmove memset memcmp memchr strlen strcmp strncmp strchr strrchr strstr strncpy strcpy strcat strtod strtol strtoul strtof atoi atof
malloc free realloc calloc abort qsort bsearch vsnprintf snprintf sscanf vsscanf fopen fclose fread fwrite fseek ftell fflush rename remove clock_gettime time
localtime_r __cxa_atexit __cxa_finalize toupper tolower isspace isdigit isalpha isalnum isprint isupper islower isxdigit getenv write'''.split())
LIBM = set('''sinf cosf tanf asinf acosf atanf atan2f powf expf exp2f logf log2f log10f sqrtf fmodf floorf ceilf roundf truncf fabsf fminf fmaxf ldexpf frexpf
sin cos tan asin acos atan atan2 pow exp exp2 log log2 log10 sqrt fmod floor ceil round trunc fabs fmin fmax ldexp frexp hypot hypotf cbrt modf sincosf sincos'''.split())
LIBDL = {'dlopen', 'dlsym', 'dlclose', 'dlerror'}
LIBLOG = {'__android_log_print', '__android_log_vprint', '__android_log_write'}
LIBANDROID = set('''ANativeWindow_getWidth ANativeWindow_getHeight ALooper_forThread AInputQueue_attachLooper AInputQueue_detachLooper AInputQueue_getEvent
AInputQueue_preDispatchEvent AInputQueue_finishEvent AInputEvent_getType AMotionEvent_getAction AMotionEvent_getPointerCount AMotionEvent_getPointerId
AMotionEvent_getX AMotionEvent_getY AKeyEvent_getAction AKeyEvent_getKeyCode AChoreographer_getInstance AChoreographer_postFrameCallback
AAssetManager_open AAsset_getLength64 AAsset_read AAsset_close AConfiguration_new AConfiguration_delete AConfiguration_fromAssetManager
AConfiguration_getDensity AConfiguration_getUiModeNight ANativeActivity_finish'''.split())
LIBS = {'c': LIBC, 'm': LIBM, 'dl': LIBDL, 'log': LIBLOG, 'android': LIBANDROID}
DATA = set()  # no data symbols are imported

SRC = ['base.cpp', 'json.cpp', 'glapi.cpp', 'model.cpp', 'render.cpp', 'imgui_gles.cpp', 'app.cpp', 'app_data.cpp', 'scene.cpp', 'ui.cpp',
       'ui_widgets.cpp', 'calcs.cpp', 'thumbs.cpp', 'ui_viewer.cpp', 'android_main.cpp', 'rt.cpp']
IMGUI = ['imgui.cpp', 'imgui_draw.cpp', 'imgui_tables.cpp', 'imgui_widgets.cpp', 'imgui_stacklayout.cpp']


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        print(' '.join(cmd)[:400]); print(r.stdout[-4000:], r.stderr[-6000:])
        sys.exit('build failed')
    if r.stderr.strip():
        print(r.stderr.strip()[-3000:])
    return r.stdout


def cflags(arch):
    a, musl, anyd = ARCHES[arch]
    inc = os.path.join(ZIG, 'lib', 'libc', 'include')
    return ['--target=' + TRIPLE[a], '-nostdinc', '-nostdinc++',
            '-isystem', os.path.join(inc, musl), '-isystem', os.path.join(inc, 'generic-musl'),
            '-isystem', os.path.join(inc, anyd), '-isystem', os.path.join(inc, 'any-linux-any'),
            '-isystem', os.path.join(RES, 'include'), '-isystem', JNI, '-isystem', os.path.join(JNI, 'linux'),
            '-I', os.path.join(N, 'src'), '-I', os.path.join(N, 'third_party', 'imgui'), '-DIMGUI_USER_CONFIG="imconfig_pf.h"', '-DPF_ANDROID=1',
            '-std=c++17', '-O2', '-fPIC', '-fno-exceptions', '-fno-rtti', '-fno-threadsafe-statics', '-fno-stack-protector', '-fno-math-errno',
            '-fvisibility=hidden', '-ffunction-sections', '-fdata-sections', '-fno-unwind-tables', '-fno-asynchronous-unwind-tables',
            '-Wall', '-Wno-c99-extensions', '-Wno-unused-function', '-Wno-missing-field-initializers'] + (['-mno-outline-atomics'] if a == 'aarch64' else []) + \
        (['-mthumb', '-mfpu=neon', '-mfloat-abi=softfp'] if a == 'armv7a' else [])


def stubs(arch, undef):
    a = ARCHES[arch][0]
    d = os.path.join(B, arch, 'stubs')
    os.makedirs(d, exist_ok=True)
    for lib, syms in LIBS.items():
        c = os.path.join(d, f'lib{lib}.c')
        with open(c, 'w') as fh:
            for s in sorted(syms & undef):
                fh.write(f'void {s}(void) {{}}\n')
        run(['clang', '--target=' + TRIPLE[a], '-w', '-fno-builtin', '-shared', '-nostdlib', '-fuse-ld=lld', f'-Wl,-soname,lib{lib}.so', '-o', os.path.join(d, f'lib{lib}.so'), c])
    return d


def compiler_rt(arch):
    """32-bit ARM needs the compiler-rt helpers (__aeabi_idiv, __aeabi_uldivmod, ...): built from zig's compiler_rt.zig."""
    if arch != 'armeabi-v7a':
        return None
    lib = os.path.join(B, arch, 'libcompiler_rt.a')
    if not os.path.exists(lib):
        obj = os.path.join(B, arch, 'compiler_rt.o')
        run([sys.executable, '-m', 'ziglang', 'build-obj', os.path.join(ZIG, 'lib', 'compiler_rt.zig'), '-target', 'arm-linux-androideabi',
             '-mcpu=generic+v7a+vfp3+d32+neon', '-OReleaseSmall', '-fPIC', f'-femit-bin={obj}'])
        run(['llvm-ar', 'rcs', lib, obj])
    return lib


def build(arch):
    od = os.path.join(B, arch, 'obj')
    os.makedirs(od, exist_ok=True)
    fl = cflags(arch)
    jobs = []
    for f in SRC:
        jobs.append((os.path.join(N, 'src', f), os.path.join(od, f.replace('.cpp', '.o')), False))
    for f in IMGUI:
        jobs.append((os.path.join(N, 'third_party', 'imgui', f), os.path.join(od, f.replace('.cpp', '.o')), True))
    deps = glob.glob(os.path.join(N, 'src', '*.h')) + [os.path.abspath(__file__)]
    newest_dep = max(os.path.getmtime(x) for x in deps)

    def comp(j):
        src, obj, quiet = j
        if os.path.exists(obj) and os.path.getmtime(obj) > max(os.path.getmtime(src), newest_dep if not quiet else os.path.getmtime(os.path.join(N, 'src', 'imconfig_pf.h'))):
            return obj
        run(['clang++'] + fl + (['-w'] if quiet else []) + ['-c', src, '-o', obj])
        return obj
    with cf.ThreadPoolExecutor(8) as ex:
        objs = list(ex.map(comp, jobs))
    # undefined symbols of all objects -> allow-list check -> stub libraries
    und = set()
    for o in objs:
        for line in run(['llvm-nm', '-u', o]).split('\n'):
            s = line.strip().split()[-1] if line.strip() else ''
            if s:
                und.add(s)
    defined = set()
    for o in objs:
        for line in run(['llvm-nm', '--defined-only', o]).split('\n'):
            parts = line.split()
            if len(parts) >= 3:
                defined.add(parts[2])
    rt = compiler_rt(arch)
    if rt:
        for line in run(['llvm-nm', '--defined-only', rt]).split('\n'):
            parts = line.split()
            if len(parts) >= 3:
                defined.add(parts[2])
    und -= defined
    known = set().union(*LIBS.values())
    bad = sorted(s for s in und if s not in known)
    if bad:
        sys.exit(f'[{arch}] symbols not on the NDK allow-list: {bad}')
    sd = stubs(arch, und)
    out = os.path.join(B, arch, 'libpumpforge.so')
    run(['clang++', '--target=' + TRIPLE[ARCHES[arch][0]], '-shared', '-nostdlib', '-fuse-ld=lld', '-o', out] + objs + ([rt] if rt else []) +
        ['-L', sd, '-Wl,--no-undefined', '-Wl,-soname,libpumpforge.so', '-Wl,-z,max-page-size=16384', '-Wl,-z,common-page-size=16384',
         '-Wl,--gc-sections', '-Wl,--build-id=sha1', '-Wl,-z,relro', '-Wl,-z,now', '-Wl,--hash-style=both', '-Wl,-z,noexecstack',
         '-Wl,--exclude-libs,ALL', '-Wl,--as-needed', '-lc', '-lm', '-ldl', '-llog', '-landroid'])
    run(['llvm-strip', '--strip-unneeded', out])
    # sanity: needed libs, exported entry, no text relocations, 16 KB alignment
    dyn = run(['llvm-readelf', '-d', '--dyn-syms', '-l', out])
    assert 'ANativeActivity_onCreate' in dyn, 'entry point not exported'
    assert 'TEXTREL' not in dyn, 'text relocations'
    needed = [l.split('[')[1].rstrip(']') for l in dyn.split('\n') if '(NEEDED)' in l]
    for l in dyn.split('\n'):
        if l.strip().startswith('LOAD') and l.split()[-1] not in ('0x4000', '0x10000'):
            sys.exit(f'LOAD segment not 16 KB aligned: {l}')
    print(f'[{arch}] {os.path.getsize(out) / 1024:.0f} KB  NEEDED={needed}  imports={len(und)}')
    return out


if __name__ == '__main__':
    arches = sys.argv[1:] or list(ARCHES)
    for a in arches:
        build(a)
