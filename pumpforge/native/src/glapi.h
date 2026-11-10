// OpenGL ES 3.0 + EGL 1.4 entry points, loaded at run time with dlopen/dlsym (no SDK headers needed).
#pragma once
#include <stdint.h>
#include <stddef.h>

typedef unsigned int GLenum; typedef unsigned char GLboolean; typedef unsigned int GLbitfield; typedef int GLint; typedef int GLsizei;
typedef unsigned int GLuint; typedef float GLfloat; typedef char GLchar; typedef intptr_t GLintptr; typedef intptr_t GLsizeiptr; typedef uint8_t GLubyte;
typedef void* EGLDisplay; typedef void* EGLConfig; typedef void* EGLSurface; typedef void* EGLContext; typedef int32_t EGLint; typedef unsigned int EGLBoolean;
typedef unsigned int EGLenum; typedef void* EGLNativeWindowType; typedef void* EGLNativeDisplayType;

enum : GLenum {
    GL_FALSE_ = 0, GL_TRUE_ = 1,
    GL_DEPTH_BUFFER_BIT = 0x100, GL_STENCIL_BUFFER_BIT = 0x400, GL_COLOR_BUFFER_BIT = 0x4000,
    GL_POINTS = 0, GL_LINES = 1, GL_LINE_STRIP = 3, GL_TRIANGLES = 4, GL_TRIANGLE_STRIP = 5,
    GL_ZERO = 0, GL_ONE = 1, GL_SRC_ALPHA = 0x302, GL_ONE_MINUS_SRC_ALPHA = 0x303,
    GL_FRONT = 0x404, GL_BACK = 0x405, GL_CULL_FACE = 0xB44, GL_DEPTH_TEST = 0xB71, GL_BLEND = 0xBE2, GL_SCISSOR_TEST = 0xC11,
    GL_POLYGON_OFFSET_FILL = 0x8037, GL_SAMPLE_ALPHA_TO_COVERAGE = 0x809E,
    GL_CW = 0x900, GL_CCW = 0x901, GL_LESS = 0x201, GL_LEQUAL = 0x203, GL_ALWAYS = 0x207,
    GL_BYTE = 0x1400, GL_UNSIGNED_BYTE = 0x1401, GL_SHORT = 0x1402, GL_UNSIGNED_SHORT = 0x1403, GL_INT = 0x1404, GL_UNSIGNED_INT = 0x1405, GL_FLOAT = 0x1406,
    GL_VENDOR = 0x1F00, GL_RENDERER = 0x1F01, GL_VERSION = 0x1F02,
    GL_TEXTURE_2D = 0xDE1, GL_TEXTURE_MAG_FILTER = 0x2800, GL_TEXTURE_MIN_FILTER = 0x2801, GL_TEXTURE_WRAP_S = 0x2802, GL_TEXTURE_WRAP_T = 0x2803,
    GL_NEAREST = 0x2600, GL_LINEAR = 0x2601, GL_CLAMP_TO_EDGE = 0x812F, GL_TEXTURE0 = 0x84C0,
    GL_RGBA = 0x1908, GL_RGBA8 = 0x8058, GL_RED = 0x1903, GL_R8 = 0x8229, GL_DEPTH_COMPONENT = 0x1902, GL_DEPTH_COMPONENT16 = 0x81A5, GL_DEPTH_COMPONENT24 = 0x81A6,
    GL_DEPTH24_STENCIL8 = 0x88F0,
    GL_TEXTURE_COMPARE_MODE = 0x884C, GL_TEXTURE_COMPARE_FUNC = 0x884D, GL_COMPARE_REF_TO_TEXTURE = 0x884E,
    GL_UNPACK_ALIGNMENT = 0xCF5, GL_PACK_ALIGNMENT = 0xD05, GL_UNPACK_ROW_LENGTH = 0xCF2,
    GL_ARRAY_BUFFER = 0x8892, GL_ELEMENT_ARRAY_BUFFER = 0x8893, GL_STATIC_DRAW = 0x88E4, GL_DYNAMIC_DRAW = 0x88E8, GL_STREAM_DRAW = 0x88E0,
    GL_FRAGMENT_SHADER = 0x8B30, GL_VERTEX_SHADER = 0x8B31, GL_COMPILE_STATUS = 0x8B81, GL_LINK_STATUS = 0x8B82, GL_INFO_LOG_LENGTH = 0x8B84,
    GL_FRAMEBUFFER = 0x8D40, GL_READ_FRAMEBUFFER = 0x8CA8, GL_DRAW_FRAMEBUFFER = 0x8CA9, GL_RENDERBUFFER = 0x8D41,
    GL_COLOR_ATTACHMENT0 = 0x8CE0, GL_DEPTH_ATTACHMENT = 0x8D00, GL_FRAMEBUFFER_COMPLETE = 0x8CD5, GL_NONE = 0,
    GL_MAX_TEXTURE_SIZE = 0xD33, GL_SAMPLES = 0x80A9, GL_MAX_SAMPLES = 0x8D57,
    GL_FUNC_ADD = 0x8006,
};

#define PF_GL_FUNCS(X) \
    X(const GLubyte*, glGetString, (GLenum name)) \
    X(void, glGetIntegerv, (GLenum p, GLint* v)) \
    X(GLenum, glGetError, (void)) \
    X(void, glViewport, (GLint x, GLint y, GLsizei w, GLsizei h)) \
    X(void, glScissor, (GLint x, GLint y, GLsizei w, GLsizei h)) \
    X(void, glClearColor, (GLfloat r, GLfloat g, GLfloat b, GLfloat a)) \
    X(void, glClearDepthf, (GLfloat d)) \
    X(void, glClear, (GLbitfield m)) \
    X(void, glEnable, (GLenum c)) \
    X(void, glDisable, (GLenum c)) \
    X(void, glBlendFunc, (GLenum s, GLenum d)) \
    X(void, glBlendFuncSeparate, (GLenum sr, GLenum dr, GLenum sa, GLenum da)) \
    X(void, glBlendEquation, (GLenum m)) \
    X(void, glDepthFunc, (GLenum f)) \
    X(void, glDepthMask, (GLboolean f)) \
    X(void, glColorMask, (GLboolean r, GLboolean g, GLboolean b, GLboolean a)) \
    X(void, glCullFace, (GLenum m)) \
    X(void, glFrontFace, (GLenum m)) \
    X(void, glPolygonOffset, (GLfloat f, GLfloat u)) \
    X(void, glLineWidth, (GLfloat w)) \
    X(void, glGenBuffers, (GLsizei n, GLuint* b)) \
    X(void, glDeleteBuffers, (GLsizei n, const GLuint* b)) \
    X(void, glBindBuffer, (GLenum t, GLuint b)) \
    X(void, glBufferData, (GLenum t, GLsizeiptr s, const void* d, GLenum u)) \
    X(void, glBufferSubData, (GLenum t, GLintptr o, GLsizeiptr s, const void* d)) \
    X(void, glGenVertexArrays, (GLsizei n, GLuint* a)) \
    X(void, glDeleteVertexArrays, (GLsizei n, const GLuint* a)) \
    X(void, glBindVertexArray, (GLuint a)) \
    X(void, glVertexAttribPointer, (GLuint i, GLint s, GLenum t, GLboolean n, GLsizei st, const void* p)) \
    X(void, glEnableVertexAttribArray, (GLuint i)) \
    X(void, glDisableVertexAttribArray, (GLuint i)) \
    X(void, glVertexAttrib4f, (GLuint i, GLfloat x, GLfloat y, GLfloat z, GLfloat w)) \
    X(void, glVertexAttribDivisor, (GLuint i, GLuint d)) \
    X(GLuint, glCreateShader, (GLenum t)) \
    X(void, glShaderSource, (GLuint s, GLsizei c, const GLchar* const* src, const GLint* l)) \
    X(void, glCompileShader, (GLuint s)) \
    X(void, glGetShaderiv, (GLuint s, GLenum p, GLint* v)) \
    X(void, glGetShaderInfoLog, (GLuint s, GLsizei m, GLsizei* l, GLchar* log)) \
    X(void, glDeleteShader, (GLuint s)) \
    X(GLuint, glCreateProgram, (void)) \
    X(void, glAttachShader, (GLuint p, GLuint s)) \
    X(void, glBindAttribLocation, (GLuint p, GLuint i, const GLchar* n)) \
    X(void, glLinkProgram, (GLuint p)) \
    X(void, glGetProgramiv, (GLuint p, GLenum q, GLint* v)) \
    X(void, glGetProgramInfoLog, (GLuint p, GLsizei m, GLsizei* l, GLchar* log)) \
    X(void, glUseProgram, (GLuint p)) \
    X(void, glDeleteProgram, (GLuint p)) \
    X(GLint, glGetUniformLocation, (GLuint p, const GLchar* n)) \
    X(void, glUniform1i, (GLint l, GLint v)) \
    X(void, glUniform1f, (GLint l, GLfloat v)) \
    X(void, glUniform2f, (GLint l, GLfloat a, GLfloat b)) \
    X(void, glUniform3f, (GLint l, GLfloat a, GLfloat b, GLfloat c)) \
    X(void, glUniform4f, (GLint l, GLfloat a, GLfloat b, GLfloat c, GLfloat d)) \
    X(void, glUniform3fv, (GLint l, GLsizei n, const GLfloat* v)) \
    X(void, glUniform4fv, (GLint l, GLsizei n, const GLfloat* v)) \
    X(void, glUniformMatrix3fv, (GLint l, GLsizei n, GLboolean t, const GLfloat* v)) \
    X(void, glUniformMatrix4fv, (GLint l, GLsizei n, GLboolean t, const GLfloat* v)) \
    X(void, glGenTextures, (GLsizei n, GLuint* t)) \
    X(void, glDeleteTextures, (GLsizei n, const GLuint* t)) \
    X(void, glBindTexture, (GLenum t, GLuint x)) \
    X(void, glActiveTexture, (GLenum t)) \
    X(void, glTexImage2D, (GLenum t, GLint l, GLint i, GLsizei w, GLsizei h, GLint b, GLenum f, GLenum ty, const void* p)) \
    X(void, glTexImage3D, (GLenum t, GLint l, GLint i, GLsizei w, GLsizei h, GLsizei d, GLint b, GLenum f, GLenum ty, const void* p)) \
    X(void, glTexSubImage2D, (GLenum t, GLint l, GLint x, GLint y, GLsizei w, GLsizei h, GLenum f, GLenum ty, const void* p)) \
    X(void, glTexParameteri, (GLenum t, GLenum p, GLint v)) \
    X(void, glPixelStorei, (GLenum p, GLint v)) \
    X(void, glGenFramebuffers, (GLsizei n, GLuint* f)) \
    X(void, glDeleteFramebuffers, (GLsizei n, const GLuint* f)) \
    X(void, glBindFramebuffer, (GLenum t, GLuint f)) \
    X(void, glFramebufferTexture2D, (GLenum t, GLenum a, GLenum tt, GLuint tx, GLint l)) \
    X(GLenum, glCheckFramebufferStatus, (GLenum t)) \
    X(void, glGenRenderbuffers, (GLsizei n, GLuint* r)) \
    X(void, glDeleteRenderbuffers, (GLsizei n, const GLuint* r)) \
    X(void, glBindRenderbuffer, (GLenum t, GLuint r)) \
    X(void, glRenderbufferStorageMultisample, (GLenum t, GLsizei s, GLenum f, GLsizei w, GLsizei h)) \
    X(void, glFramebufferRenderbuffer, (GLenum t, GLenum a, GLenum rt, GLuint r)) \
    X(void, glBlitFramebuffer, (GLint a, GLint b, GLint c, GLint d, GLint e, GLint f, GLint g, GLint h, GLbitfield m, GLenum fl)) \
    X(void, glInvalidateFramebuffer, (GLenum t, GLsizei n, const GLenum* a)) \
    X(void, glDrawBuffers, (GLsizei n, const GLenum* b)) \
    X(void, glReadBuffer, (GLenum b)) \
    X(void, glReadPixels, (GLint x, GLint y, GLsizei w, GLsizei h, GLenum f, GLenum t, void* p)) \
    X(void, glDrawArrays, (GLenum m, GLint f, GLsizei c)) \
    X(void, glDrawElements, (GLenum m, GLsizei c, GLenum t, const void* i)) \
    X(void, glDrawElementsInstanced, (GLenum m, GLsizei c, GLenum t, const void* i, GLsizei n)) \
    X(void, glFinish, (void)) \
    X(void, glFlush, (void))

#define PF_EGL_FUNCS(X) \
    X(EGLDisplay, eglGetDisplay, (EGLNativeDisplayType d)) \
    X(EGLBoolean, eglInitialize, (EGLDisplay d, EGLint* ma, EGLint* mi)) \
    X(EGLBoolean, eglTerminate, (EGLDisplay d)) \
    X(EGLBoolean, eglBindAPI, (EGLenum a)) \
    X(EGLBoolean, eglChooseConfig, (EGLDisplay d, const EGLint* a, EGLConfig* c, EGLint s, EGLint* n)) \
    X(EGLBoolean, eglGetConfigAttrib, (EGLDisplay d, EGLConfig c, EGLint a, EGLint* v)) \
    X(EGLSurface, eglCreateWindowSurface, (EGLDisplay d, EGLConfig c, EGLNativeWindowType w, const EGLint* a)) \
    X(EGLSurface, eglCreatePbufferSurface, (EGLDisplay d, EGLConfig c, const EGLint* a)) \
    X(EGLContext, eglCreateContext, (EGLDisplay d, EGLConfig c, EGLContext s, const EGLint* a)) \
    X(EGLBoolean, eglDestroySurface, (EGLDisplay d, EGLSurface s)) \
    X(EGLBoolean, eglDestroyContext, (EGLDisplay d, EGLContext c)) \
    X(EGLBoolean, eglMakeCurrent, (EGLDisplay d, EGLSurface w, EGLSurface r, EGLContext c)) \
    X(EGLBoolean, eglSwapBuffers, (EGLDisplay d, EGLSurface s)) \
    X(EGLBoolean, eglSwapInterval, (EGLDisplay d, EGLint i)) \
    X(EGLBoolean, eglQuerySurface, (EGLDisplay d, EGLSurface s, EGLint a, EGLint* v)) \
    X(EGLint, eglGetError, (void)) \
    X(void*, eglGetProcAddress, (const char* n))

#define PF_DECL(ret, name, args) typedef ret (*PFN_##name) args; extern PFN_##name name;
PF_GL_FUNCS(PF_DECL)
PF_EGL_FUNCS(PF_DECL)
#undef PF_DECL

enum : EGLint {
    EGL_NONE = 0x3038, EGL_RED_SIZE = 0x3024, EGL_GREEN_SIZE = 0x3023, EGL_BLUE_SIZE = 0x3022, EGL_ALPHA_SIZE = 0x3021,
    EGL_DEPTH_SIZE = 0x3025, EGL_STENCIL_SIZE = 0x3026, EGL_SAMPLES = 0x3031, EGL_SAMPLE_BUFFERS = 0x3032,
    EGL_SURFACE_TYPE = 0x3033, EGL_WINDOW_BIT = 0x4, EGL_PBUFFER_BIT = 0x1, EGL_RENDERABLE_TYPE = 0x3040,
    EGL_OPENGL_ES2_BIT = 0x4, EGL_OPENGL_ES3_BIT = 0x40, EGL_CONTEXT_CLIENT_VERSION = 0x3098,
    EGL_WIDTH = 0x3057, EGL_HEIGHT = 0x3056, EGL_NATIVE_VISUAL_ID = 0x302E, EGL_OPENGL_ES_API = 0x30A0,
    EGL_PLATFORM_SURFACELESS_MESA = 0x31DD,
};
#define EGL_NO_CONTEXT ((EGLContext)0)
#define EGL_NO_SURFACE ((EGLSurface)0)
#define EGL_NO_DISPLAY ((EGLDisplay)0)
#define EGL_DEFAULT_DISPLAY ((EGLNativeDisplayType)0)

bool gl_load(const char* egl_lib, const char* gles_lib, char* err, int errlen);
