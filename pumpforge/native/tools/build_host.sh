#!/bin/sh
set -e
cd "$(dirname "$0")/.."   # native/
O=build/host; mkdir -p $O
FL="-O1 -g -std=c++17 -fno-exceptions -fno-rtti -Isrc -Ithird_party/imgui -DIMGUI_USER_CONFIG=\"imconfig_pf.h\" -Wall -Wno-c99-extensions -Wno-unused-function -Wno-missing-field-initializers"
for f in third_party/imgui/imgui.cpp third_party/imgui/imgui_draw.cpp third_party/imgui/imgui_tables.cpp third_party/imgui/imgui_widgets.cpp third_party/imgui/imgui_stacklayout.cpp; do
  b=$O/$(basename $f .cpp).o; [ $b -nt $f ] || clang++ $FL -w -c $f -o $b &
done; wait
OBJS=""
for f in src/base.cpp src/json.cpp src/glapi.cpp src/model.cpp src/render.cpp src/imgui_gles.cpp src/app.cpp src/app_data.cpp src/scene.cpp src/ui.cpp src/ui_widgets.cpp src/calcs.cpp src/thumbs.cpp src/ui_viewer.cpp src/linux_main.cpp; do
  b=$O/$(basename $f .cpp).o; OBJS="$OBJS $b"; clang++ $FL -c $f -o $b &
done; wait
clang++ -o $O/pf_test $OBJS $O/imgui.o $O/imgui_draw.o $O/imgui_tables.o $O/imgui_widgets.o $O/imgui_stacklayout.o -ldl -lm
echo built $O/pf_test
