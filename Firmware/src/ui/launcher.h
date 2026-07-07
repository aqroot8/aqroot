#pragma once
// AQROOT — app launcher / UI shell (LVGL 8.3).
//
// Builds the tile-based dashboard from "Assets/first-design-concept.png": a 2x3 grid of
// tool tiles (Scan, NFC, Infrared, GPIO, Bluetooth, Tools) plus a live Signal Monitor
// panel and an NFC Tag panel. Tapping a tile opens that tool's screen; each tool screen
// has a Back control that returns here.

#include <lvgl.h>
#include "../config.h"   // DISPLAY_WIDTH/HEIGHT, available to every screen via this header

// Build the home screen and load it. Call after LVGL + drivers are initialized.
void launcher_init(void);

// Return to the launcher home screen, deleting the current tool screen if one is open.
// Used by every tool screen's Back button and by the simulator's Back button.
void ui_return_home(void);

// The home screen object (used to gate simulator keypad input to the home screen only).
lv_obj_t *launcher_get_screen(void);

// The keypad group holding the home tiles (used by the simulator's button navigation).
lv_group_t *launcher_get_group(void);

// Shared helper: create a fresh tool screen with a titled header + Back button and load
// it. Returns a content container the caller fills with the tool's widgets. Timers that
// a screen creates should be deleted on the content's LV_EVENT_DELETE so they stop when
// the user navigates away.
lv_obj_t *ui_make_screen(const char *title);
