// Platform services the app needs (implemented by android_main.cpp and linux_main.cpp).
#pragma once
#include "base.h"

namespace plat {
bool read_asset(const char* path, Vec<uint8_t>& out);      // bundled read-only data (APK assets / ./assets)
bool read_user(const char* name, Vec<uint8_t>& out);       // private app storage
bool write_user(const char* name, const void* data, size_t len);   // atomic replace
double now();                                              // seconds, monotonic
double now_epoch_ms();                                     // wall clock (Date.now())
void speak(const char* text);                              // text-to-speech (flushes the queue)
void stop_speaking();
bool speaking();
bool tts_available();
// Text entry: opens the system keyboard in a small native dialog. The text is polled every frame
// (text_poll) so typing updates the app live; returns false once the dialog has closed.
enum InputKind { TEXT = 0, MULTILINE = 1, NUMBER = 2 };
void text_begin(const char* title, const char* initial, InputKind kind);
bool text_poll(Str& current, bool& closed, bool& accepted);
void copy_to_clipboard(const char* text);
void quit();
void theme_changed(bool dark);                             // system bar colours follow the app theme
}

// Input events delivered by the platform layer to the app (pixels, origin top-left).
struct TouchEvent { enum Kind { Down, Move, Up, Cancel } kind; int id; float x, y; };
