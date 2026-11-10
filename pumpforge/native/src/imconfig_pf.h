// Dear ImGui build configuration for PumpForge native
#pragma once
void pf_imgui_assert(const char* expr, const char* file, int line);
#define IM_ASSERT(_EXPR) do { if (!(_EXPR)) pf_imgui_assert(#_EXPR, __FILE__, __LINE__); } while (0)
#define IMGUI_DISABLE_OBSOLETE_FUNCTIONS
#define IMGUI_DISABLE_FILE_FUNCTIONS            // ini/log files are not used
#define IMGUI_DISABLE_DEFAULT_SHELL_FUNCTIONS
#define IMGUI_DISABLE_DEMO_WINDOWS
#define IMGUI_DISABLE_DEBUG_TOOLS
#define IMGUI_DISABLE_DEFAULT_FONT              // IBM Plex is loaded from assets
#define IMGUI_DISABLE_TIME_FUNCTIONS            // no libc time API in the library (keeps the 32-bit build free of time_t ABI issues)
