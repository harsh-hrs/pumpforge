// Dear ImGui renderer for OpenGL ES 3.0 with dynamic texture support (ImGuiBackendFlags_RendererHasTextures).
#include "imgui.h"
#include "glapi.h"
#include "base.h"
#include <stdio.h>

static unsigned g_prog, g_vao, g_vbo, g_ibo; static int g_ltex, g_lproj;

static const char* VS = R"(#version 300 es
layout(location=0) in vec2 a_p; layout(location=1) in vec2 a_uv; layout(location=2) in vec4 a_c;
uniform mat4 u_proj; out vec2 v_uv; out vec4 v_c;
void main() { v_uv = a_uv; v_c = a_c; gl_Position = u_proj * vec4(a_p, 0.0, 1.0); })";
static const char* FS = R"(#version 300 es
precision mediump float; uniform sampler2D u_tex; in vec2 v_uv; in vec4 v_c; out vec4 o;
void main() { o = v_c * texture(u_tex, v_uv); })";

static unsigned sh(unsigned t, const char* s) {
    unsigned x = glCreateShader(t); glShaderSource(x, 1, &s, nullptr); glCompileShader(x);
    GLint ok; glGetShaderiv(x, GL_COMPILE_STATUS, &ok);
    if (!ok) { char l[1024]; glGetShaderInfoLog(x, sizeof l, nullptr, l); pf_log("imgui shader: %s", l); }
    return x;
}

bool ImGuiGLES_Init() {
    ImGuiIO& io = ImGui::GetIO();
    io.BackendRendererName = "pumpforge_gles3";
    io.BackendFlags |= ImGuiBackendFlags_RendererHasVtxOffset | ImGuiBackendFlags_RendererHasTextures;
    g_prog = glCreateProgram();
    unsigned v = sh(GL_VERTEX_SHADER, VS), f = sh(GL_FRAGMENT_SHADER, FS);
    glAttachShader(g_prog, v); glAttachShader(g_prog, f); glLinkProgram(g_prog); glDeleteShader(v); glDeleteShader(f);
    GLint ok; glGetProgramiv(g_prog, GL_LINK_STATUS, &ok); if (!ok) return false;
    g_ltex = glGetUniformLocation(g_prog, "u_tex"); g_lproj = glGetUniformLocation(g_prog, "u_proj");
    glGenVertexArrays(1, &g_vao); glBindVertexArray(g_vao);
    glGenBuffers(1, &g_vbo); glGenBuffers(1, &g_ibo);
    glBindBuffer(GL_ARRAY_BUFFER, g_vbo); glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, g_ibo);
    glEnableVertexAttribArray(0); glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE_, sizeof(ImDrawVert), (void*)offsetof(ImDrawVert, pos));
    glEnableVertexAttribArray(1); glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE_, sizeof(ImDrawVert), (void*)offsetof(ImDrawVert, uv));
    glEnableVertexAttribArray(2); glVertexAttribPointer(2, 4, GL_UNSIGNED_BYTE, GL_TRUE_, sizeof(ImDrawVert), (void*)offsetof(ImDrawVert, col));
    glBindVertexArray(0);
    return true;
}

static void update_texture(ImTextureData* tex) {
    if (tex->Status == ImTextureStatus_WantCreate) {
        GLuint id; glGenTextures(1, &id); glBindTexture(GL_TEXTURE_2D, id);
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR); glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE); glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE);
        glPixelStorei(GL_UNPACK_ALIGNMENT, 1);
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA8, tex->Width, tex->Height, 0, GL_RGBA, GL_UNSIGNED_BYTE, tex->GetPixels());
        tex->SetTexID((ImTextureID)(intptr_t)id);
        tex->SetStatus(ImTextureStatus_OK);
    } else if (tex->Status == ImTextureStatus_WantUpdates) {
        GLuint id = (GLuint)(intptr_t)tex->TexID; glBindTexture(GL_TEXTURE_2D, id);
        glPixelStorei(GL_UNPACK_ALIGNMENT, 1); glPixelStorei(GL_UNPACK_ROW_LENGTH, tex->Width);
        for (ImTextureRect& r : tex->Updates)
            glTexSubImage2D(GL_TEXTURE_2D, 0, r.x, r.y, r.w, r.h, GL_RGBA, GL_UNSIGNED_BYTE, tex->GetPixelsAt(r.x, r.y));
        glPixelStorei(GL_UNPACK_ROW_LENGTH, 0);
        tex->SetStatus(ImTextureStatus_OK);
    } else if (tex->Status == ImTextureStatus_WantDestroy && tex->UnusedFrames > 0) {
        GLuint id = (GLuint)(intptr_t)tex->TexID; glDeleteTextures(1, &id);
        tex->SetTexID(ImTextureID_Invalid); tex->SetStatus(ImTextureStatus_Destroyed);
    }
}

// After a GL context loss every texture must be uploaded again.
void ImGuiGLES_Lost() {
    g_prog = g_vao = g_vbo = g_ibo = 0;
    for (ImTextureData* t : ImGui::GetPlatformIO().Textures)
        if (t->Status != ImTextureStatus_Destroyed) { t->SetTexID(ImTextureID_Invalid); t->SetStatus(ImTextureStatus_WantCreate); }
}

void ImGuiGLES_Shutdown() {
    for (ImTextureData* t : ImGui::GetPlatformIO().Textures)
        if (t->RefCount == 1 && t->TexID) { GLuint id = (GLuint)(intptr_t)t->TexID; glDeleteTextures(1, &id); t->SetTexID(ImTextureID_Invalid); t->SetStatus(ImTextureStatus_Destroyed); }
    if (g_prog) glDeleteProgram(g_prog);
    unsigned b[2] = {g_vbo, g_ibo}; glDeleteBuffers(2, b); glDeleteVertexArrays(1, &g_vao);
    g_prog = 0;
}

void ImGuiGLES_Render(ImDrawData* dd) {
    if (dd->Textures) for (ImTextureData* t : *dd->Textures) if (t->Status != ImTextureStatus_OK) update_texture(t);
    int fbw = (int)(dd->DisplaySize.x * dd->FramebufferScale.x), fbh = (int)(dd->DisplaySize.y * dd->FramebufferScale.y);
    if (fbw <= 0 || fbh <= 0) return;
    glEnable(GL_BLEND); glBlendEquation(GL_FUNC_ADD); glBlendFuncSeparate(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA, GL_ONE, GL_ONE_MINUS_SRC_ALPHA);
    glDisable(GL_CULL_FACE); glDisable(GL_DEPTH_TEST); glEnable(GL_SCISSOR_TEST);
    glViewport(0, 0, fbw, fbh);
    float L = dd->DisplayPos.x, R = L + dd->DisplaySize.x, T = dd->DisplayPos.y, B = T + dd->DisplaySize.y;
    const float P[16] = {2 / (R - L), 0, 0, 0, 0, 2 / (T - B), 0, 0, 0, 0, -1, 0, (R + L) / (L - R), (T + B) / (B - T), 0, 1};
    glUseProgram(g_prog); glUniform1i(g_ltex, 0); glUniformMatrix4fv(g_lproj, 1, GL_FALSE_, P);
    glActiveTexture(GL_TEXTURE0);
    glBindVertexArray(g_vao); glBindBuffer(GL_ARRAY_BUFFER, g_vbo); glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, g_ibo);
    ImVec2 off = dd->DisplayPos, sc = dd->FramebufferScale;
    for (const ImDrawList* cl : dd->CmdLists) {
        glBufferData(GL_ARRAY_BUFFER, (GLsizeiptr)cl->VtxBuffer.Size * (int)sizeof(ImDrawVert), cl->VtxBuffer.Data, GL_STREAM_DRAW);
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, (GLsizeiptr)cl->IdxBuffer.Size * (int)sizeof(ImDrawIdx), cl->IdxBuffer.Data, GL_STREAM_DRAW);
        for (const ImDrawCmd& c : cl->CmdBuffer) {
            if (c.UserCallback) { if (c.UserCallback != ImGui::GetPlatformIO().DrawCallback_ResetRenderState) c.UserCallback(cl, &c); continue; }
            ImVec2 a((c.ClipRect.x - off.x) * sc.x, (c.ClipRect.y - off.y) * sc.y), b((c.ClipRect.z - off.x) * sc.x, (c.ClipRect.w - off.y) * sc.y);
            if (b.x <= a.x || b.y <= a.y) continue;
            glScissor((int)a.x, (int)((float)fbh - b.y), (int)(b.x - a.x), (int)(b.y - a.y));
            glBindTexture(GL_TEXTURE_2D, (GLuint)(intptr_t)c.GetTexID());
            // base-vertex is not core in ES 3.0: rebind the attribute pointers at VtxOffset instead
            size_t vo = (size_t)c.VtxOffset * sizeof(ImDrawVert);
            glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE_, sizeof(ImDrawVert), (void*)(vo + offsetof(ImDrawVert, pos)));
            glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE_, sizeof(ImDrawVert), (void*)(vo + offsetof(ImDrawVert, uv)));
            glVertexAttribPointer(2, 4, GL_UNSIGNED_BYTE, GL_TRUE_, sizeof(ImDrawVert), (void*)(vo + offsetof(ImDrawVert, col)));
            glDrawElements(GL_TRIANGLES, (GLsizei)c.ElemCount, sizeof(ImDrawIdx) == 2 ? GL_UNSIGNED_SHORT : GL_UNSIGNED_INT, (void*)(intptr_t)(c.IdxOffset * sizeof(ImDrawIdx)));
        }
    }
    glDisable(GL_SCISSOR_TEST); glBindVertexArray(0);
}

// draw-list callbacks: premultiplied-alpha images (3-D thumbnails rendered on a transparent background)
namespace ui {
void pf_cb_premul(const ImDrawList*, const ImDrawCmd*) { glBlendFuncSeparate(GL_ONE, GL_ONE_MINUS_SRC_ALPHA, GL_ONE, GL_ONE_MINUS_SRC_ALPHA); }
void pf_cb_normal(const ImDrawList*, const ImDrawCmd*) { glBlendFuncSeparate(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA, GL_ONE, GL_ONE_MINUS_SRC_ALPHA); }
}
