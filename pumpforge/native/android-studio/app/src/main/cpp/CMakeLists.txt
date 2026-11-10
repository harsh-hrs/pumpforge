cmake_minimum_required(VERSION 3.22.1)
project(pumpforge CXX)
# Shared with the command-line build (native/tools/build_so.py): <repo>/native/src and Dear ImGui 1.93
get_filename_component(PF_NATIVE "${CMAKE_CURRENT_SOURCE_DIR}/../../../../.." ABSOLUTE)
set(PF_SRC ${PF_NATIVE}/src)
set(IMGUI ${PF_NATIVE}/third_party/imgui)
add_library(pumpforge SHARED
    ${PF_SRC}/base.cpp ${PF_SRC}/json.cpp ${PF_SRC}/glapi.cpp ${PF_SRC}/model.cpp ${PF_SRC}/render.cpp ${PF_SRC}/imgui_gles.cpp
    ${PF_SRC}/app.cpp ${PF_SRC}/app_data.cpp ${PF_SRC}/scene.cpp ${PF_SRC}/ui.cpp ${PF_SRC}/ui_widgets.cpp ${PF_SRC}/calcs.cpp ${PF_SRC}/thumbs.cpp ${PF_SRC}/ui_viewer.cpp
    ${PF_SRC}/android_main.cpp ${PF_SRC}/rt.cpp
    ${IMGUI}/imgui.cpp ${IMGUI}/imgui_draw.cpp ${IMGUI}/imgui_tables.cpp ${IMGUI}/imgui_widgets.cpp ${IMGUI}/imgui_stacklayout.cpp)
target_include_directories(pumpforge PRIVATE ${PF_SRC} ${IMGUI})
target_compile_definitions(pumpforge PRIVATE PF_NDK_BUILD=1 PF_ANDROID=1 IMGUI_USER_CONFIG="imconfig_pf.h")
set_target_properties(pumpforge PROPERTIES CXX_STANDARD 17 CXX_STANDARD_REQUIRED ON)
target_compile_options(pumpforge PRIVATE -O2 -fno-exceptions -fno-rtti -fno-threadsafe-statics -fvisibility=hidden -ffunction-sections -fdata-sections
    -Wno-c99-extensions -Wno-unused-function -Wno-missing-field-initializers)
# EGL / GLES are opened at run time with dlopen (glapi.cpp), so only these system libraries are linked
target_link_libraries(pumpforge PRIVATE android log dl m)
target_link_options(pumpforge PRIVATE -Wl,--gc-sections -Wl,-z,max-page-size=16384 -Wl,--no-undefined)
