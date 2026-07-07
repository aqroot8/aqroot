// AQROOT — app launcher / UI shell implementation.

#include "launcher.h"
#include "../config.h"

#include "../drivers/radio.h"
#include "../drivers/nfc.h"

#include "screens/scan_screen.h"
#include "screens/nfc_screen.h"
#include "screens/ir_screen.h"
#include "screens/gpio_screen.h"
#include "screens/bluetooth_screen.h"
#include "screens/tools_screen.h"

#include <Arduino.h>
#include <stdio.h>

static lv_obj_t   *s_home    = NULL;
static lv_group_t *s_group   = NULL;

// Live home-screen widgets updated by the refresh timer.
static lv_obj_t *s_clock_lbl = NULL;
static lv_obj_t *s_sig_freq  = NULL;
static lv_obj_t *s_sig_dbm   = NULL;
static lv_obj_t *s_sig_bar   = NULL;
static lv_obj_t *s_nfc_lbl   = NULL;

typedef void (*open_fn_t)(void);

// ---------------------------------------------------------------------------------------
// Tile grid
// ---------------------------------------------------------------------------------------
static void tile_event_cb(lv_event_t *e) {
    open_fn_t fn = (open_fn_t)lv_event_get_user_data(e);
    if (fn) fn();
}

static lv_obj_t *make_tile(lv_obj_t *parent, const char *icon, const char *title,
                           const char *subtitle, uint32_t color, open_fn_t fn) {
    lv_obj_t *tile = lv_btn_create(parent);
    lv_obj_set_size(tile, 104, 60);
    lv_obj_set_style_bg_color(tile, lv_color_hex(0x22262e), LV_PART_MAIN);
    lv_obj_set_style_bg_grad_color(tile, lv_color_hex(0x171a1f), LV_PART_MAIN);
    lv_obj_set_style_bg_grad_dir(tile, LV_GRAD_DIR_VER, LV_PART_MAIN);
    lv_obj_set_style_border_width(tile, 1, LV_PART_MAIN);
    lv_obj_set_style_border_color(tile, lv_color_hex(color), LV_PART_MAIN);
    lv_obj_set_style_radius(tile, 8, LV_PART_MAIN);
    lv_obj_set_style_pad_all(tile, 4, LV_PART_MAIN);
    lv_obj_add_event_cb(tile, tile_event_cb, LV_EVENT_CLICKED, (void *)fn);
    lv_group_add_obj(s_group, tile);   // explicit: only tiles are keypad-navigable

    lv_obj_set_flex_flow(tile, LV_FLEX_FLOW_COLUMN);
    lv_obj_set_flex_align(tile, LV_FLEX_ALIGN_CENTER, LV_FLEX_ALIGN_CENTER,
                          LV_FLEX_ALIGN_CENTER);

    lv_obj_t *ic = lv_label_create(tile);
    lv_label_set_text(ic, icon);
    lv_obj_set_style_text_color(ic, lv_color_hex(color), LV_PART_MAIN);
    lv_obj_set_style_text_font(ic, &lv_font_montserrat_20, LV_PART_MAIN);

    lv_obj_t *tl = lv_label_create(tile);
    lv_label_set_text(tl, title);
    lv_obj_set_style_text_color(tl, lv_color_hex(0xf0f0f0), LV_PART_MAIN);
    lv_obj_set_style_text_font(tl, &lv_font_montserrat_14, LV_PART_MAIN);

    lv_obj_t *sub = lv_label_create(tile);
    lv_label_set_text(sub, subtitle);
    lv_obj_set_style_text_color(sub, lv_color_hex(0x8a8f98), LV_PART_MAIN);
    lv_obj_set_style_text_font(sub, &lv_font_montserrat_12, LV_PART_MAIN);

    return tile;
}

// ---------------------------------------------------------------------------------------
// Info panels (Signal Monitor + NFC Tag)
// ---------------------------------------------------------------------------------------
static lv_obj_t *make_panel(lv_obj_t *parent, int height) {
    lv_obj_t *p = lv_obj_create(parent);
    lv_obj_set_size(p, DISPLAY_WIDTH - 16, height);
    lv_obj_set_style_bg_color(p, lv_color_hex(0x14161a), LV_PART_MAIN);
    lv_obj_set_style_border_width(p, 1, LV_PART_MAIN);
    lv_obj_set_style_border_color(p, lv_color_hex(0x2a2e36), LV_PART_MAIN);
    lv_obj_set_style_radius(p, 8, LV_PART_MAIN);
    lv_obj_set_style_pad_all(p, 6, LV_PART_MAIN);
    lv_obj_clear_flag(p, LV_OBJ_FLAG_SCROLLABLE);
    return p;
}

// ---------------------------------------------------------------------------------------
// Live refresh: clock, signal monitor, NFC tag panel
// ---------------------------------------------------------------------------------------
static void refresh_cb(lv_timer_t *t) {
    (void)t;

    // Clock — advances from 12:37 (matching the concept art) using device uptime.
    uint32_t total = 12u * 3600u + 37u * 60u + (millis() / 1000u);
    lv_label_set_text_fmt(s_clock_lbl, "%02u:%02u", (total / 3600u) % 24u, (total / 60u) % 60u);

    // Signal monitor — poll the radio (mock in simulation) for RSSI + frequency.
    unsigned char scratch[16];
    radio_receive(scratch, sizeof(scratch));
    float rssi = radio_get_rssi();
    long  freq = radio_get_frequency();
    lv_label_set_text_fmt(s_sig_freq, "%.2f MHz", freq / 1000000.0f);
    lv_label_set_text_fmt(s_sig_dbm, "%d dBm", (int)rssi);
    int level = (int)(rssi + 110.0f) * 100 / 70;   // map -110..-40 dBm -> 0..100
    if (level < 0) level = 0;
    if (level > 100) level = 100;
    lv_bar_set_value(s_sig_bar, level, LV_ANIM_OFF);

    // NFC tag panel — show the UID of any tag in the field.
    unsigned char uid[10];
    int n = nfc_read_tag(uid, sizeof(uid));
    if (n > 0) {
        char buf[48];
        int off = snprintf(buf, sizeof(buf), "UID:");
        for (int i = 0; i < n && off < (int)sizeof(buf) - 3; i++) {
            off += snprintf(buf + off, sizeof(buf) - off, " %02X", uid[i]);
        }
        lv_label_set_text(s_nfc_lbl, buf);
    } else {
        lv_label_set_text(s_nfc_lbl, "UID: --  (no tag)");
    }
}

// ---------------------------------------------------------------------------------------
// Public API
// ---------------------------------------------------------------------------------------
lv_obj_t   *launcher_get_screen(void) { return s_home; }
lv_group_t *launcher_get_group(void)  { return s_group; }

void ui_return_home(void) {
    lv_obj_t *cur = lv_scr_act();
    if (cur != s_home && s_home != NULL) {
        lv_scr_load(s_home);
        lv_obj_del_async(cur);   // async: safe even when called from cur's own event cb
    }
}

void launcher_init(void) {
    s_home = lv_obj_create(NULL);
    lv_obj_set_style_bg_color(s_home, lv_color_hex(0x0b0c0f), LV_PART_MAIN);
    lv_obj_set_flex_flow(s_home, LV_FLEX_FLOW_COLUMN);
    lv_obj_set_flex_align(s_home, LV_FLEX_ALIGN_START, LV_FLEX_ALIGN_CENTER,
                          LV_FLEX_ALIGN_CENTER);
    lv_obj_set_style_pad_all(s_home, 8, LV_PART_MAIN);
    lv_obj_set_style_pad_row(s_home, 6, LV_PART_MAIN);

    // Keypad group for simulator navigation; tiles are added explicitly in make_tile().
    s_group = lv_group_create();

    // --- Status bar: clock left, battery right ---
    lv_obj_t *bar = lv_obj_create(s_home);
    lv_obj_set_size(bar, DISPLAY_WIDTH - 16, 22);
    lv_obj_set_style_bg_opa(bar, LV_OPA_TRANSP, LV_PART_MAIN);
    lv_obj_set_style_border_width(bar, 0, LV_PART_MAIN);
    lv_obj_set_style_pad_all(bar, 0, LV_PART_MAIN);
    lv_obj_clear_flag(bar, LV_OBJ_FLAG_SCROLLABLE);

    s_clock_lbl = lv_label_create(bar);
    lv_label_set_text(s_clock_lbl, "12:37");
    lv_obj_align(s_clock_lbl, LV_ALIGN_LEFT_MID, 0, 0);
    lv_obj_set_style_text_color(s_clock_lbl, lv_color_hex(0xf0f0f0), LV_PART_MAIN);

    lv_obj_t *batt = lv_label_create(bar);
    lv_label_set_text(batt, "100% " LV_SYMBOL_BATTERY_FULL);
    lv_obj_align(batt, LV_ALIGN_RIGHT_MID, 0, 0);
    lv_obj_set_style_text_color(batt, lv_color_hex(0xf0f0f0), LV_PART_MAIN);

    // --- Title ---
    lv_obj_t *title = lv_label_create(s_home);
    lv_label_set_text(title, "Dashboard");
    lv_obj_set_style_text_font(title, &lv_font_montserrat_24, LV_PART_MAIN);
    lv_obj_set_style_text_color(title, lv_color_hex(0xffffff), LV_PART_MAIN);

    // --- Tile grid (2 columns x 3 rows) ---
    lv_obj_t *grid = lv_obj_create(s_home);
    lv_obj_set_size(grid, DISPLAY_WIDTH - 16, 196);
    lv_obj_set_style_bg_opa(grid, LV_OPA_TRANSP, LV_PART_MAIN);
    lv_obj_set_style_border_width(grid, 0, LV_PART_MAIN);
    lv_obj_set_style_pad_all(grid, 0, LV_PART_MAIN);
    lv_obj_set_style_pad_gap(grid, 6, LV_PART_MAIN);
    lv_obj_set_flex_flow(grid, LV_FLEX_FLOW_ROW_WRAP);
    lv_obj_set_flex_align(grid, LV_FLEX_ALIGN_CENTER, LV_FLEX_ALIGN_CENTER,
                          LV_FLEX_ALIGN_CENTER);
    lv_obj_clear_flag(grid, LV_OBJ_FLAG_SCROLLABLE);

    make_tile(grid, LV_SYMBOL_WIFI,      "Scan",      "Sub-GHz",   0x2ecc71, scan_screen_open);
    make_tile(grid, LV_SYMBOL_SD_CARD,   "NFC",       "13.56 MHz", 0x3498db, nfc_screen_open);
    make_tile(grid, LV_SYMBOL_EYE_OPEN,  "Infrared",  "IR TX/RX",  0xe74c3c, ir_screen_open);
    make_tile(grid, LV_SYMBOL_LIST,      "GPIO",      "Control",   0xe67e22, gpio_screen_open);
    make_tile(grid, LV_SYMBOL_BLUETOOTH, "Bluetooth", "Connect",   0x2980e0, bluetooth_screen_open);
    make_tile(grid, LV_SYMBOL_SETTINGS,  "Tools",     "Utilities", 0x9b59b6, tools_screen_open);

    // --- Signal Monitor panel ---
    lv_obj_t *sig = make_panel(s_home, 48);
    lv_obj_t *sig_title = lv_label_create(sig);
    lv_label_set_text(sig_title, "Signal Monitor");
    lv_obj_set_style_text_color(sig_title, lv_color_hex(0xe67e22), LV_PART_MAIN);
    lv_obj_align(sig_title, LV_ALIGN_TOP_LEFT, 0, 0);

    s_sig_freq = lv_label_create(sig);
    lv_label_set_text(s_sig_freq, "915.20 MHz");
    lv_obj_set_style_text_color(s_sig_freq, lv_color_hex(0xf0f0f0), LV_PART_MAIN);
    lv_obj_align(s_sig_freq, LV_ALIGN_TOP_RIGHT, 0, 0);

    s_sig_bar = lv_bar_create(sig);
    lv_obj_set_size(s_sig_bar, 130, 8);
    lv_obj_align(s_sig_bar, LV_ALIGN_BOTTOM_LEFT, 0, 0);
    lv_bar_set_range(s_sig_bar, 0, 100);
    lv_obj_set_style_bg_color(s_sig_bar, lv_color_hex(0x2a2e36), LV_PART_MAIN);
    lv_obj_set_style_bg_color(s_sig_bar, lv_color_hex(0xe67e22), LV_PART_INDICATOR);

    s_sig_dbm = lv_label_create(sig);
    lv_label_set_text(s_sig_dbm, "-67 dBm");
    lv_obj_set_style_text_color(s_sig_dbm, lv_color_hex(0xf0f0f0), LV_PART_MAIN);
    lv_obj_align(s_sig_dbm, LV_ALIGN_BOTTOM_RIGHT, 0, 0);

    // --- NFC Tag panel ---
    lv_obj_t *nfc = make_panel(s_home, 34);
    lv_obj_t *nfc_title = lv_label_create(nfc);
    lv_label_set_text(nfc_title, "NFC Tag");
    lv_obj_set_style_text_color(nfc_title, lv_color_hex(0x3498db), LV_PART_MAIN);
    lv_obj_align(nfc_title, LV_ALIGN_TOP_LEFT, 0, 0);

    s_nfc_lbl = lv_label_create(nfc);
    lv_label_set_text(s_nfc_lbl, "UID: --");
    lv_obj_set_style_text_color(s_nfc_lbl, lv_color_hex(0xf0f0f0), LV_PART_MAIN);
    lv_obj_align(s_nfc_lbl, LV_ALIGN_BOTTOM_LEFT, 0, 0);

    lv_timer_create(refresh_cb, 500, NULL);
    lv_scr_load(s_home);
}

// ---------------------------------------------------------------------------------------
// Shared tool-screen scaffold
// ---------------------------------------------------------------------------------------
static void back_event_cb(lv_event_t *e) {
    (void)e;
    ui_return_home();
}

lv_obj_t *ui_make_screen(const char *title) {
    lv_obj_t *scr = lv_obj_create(NULL);
    lv_obj_set_style_bg_color(scr, lv_color_hex(0x0b0c0f), LV_PART_MAIN);
    lv_obj_clear_flag(scr, LV_OBJ_FLAG_SCROLLABLE);

    // Header: Back button + title.
    lv_obj_t *back = lv_btn_create(scr);
    lv_obj_set_size(back, 40, 30);
    lv_obj_align(back, LV_ALIGN_TOP_LEFT, 6, 6);
    lv_obj_set_style_bg_color(back, lv_color_hex(0x22262e), LV_PART_MAIN);
    lv_obj_add_event_cb(back, back_event_cb, LV_EVENT_CLICKED, NULL);
    lv_obj_t *back_lbl = lv_label_create(back);
    lv_label_set_text(back_lbl, LV_SYMBOL_LEFT);
    lv_obj_center(back_lbl);

    lv_obj_t *ttl = lv_label_create(scr);
    lv_label_set_text(ttl, title);
    lv_obj_set_style_text_font(ttl, &lv_font_montserrat_20, LV_PART_MAIN);
    lv_obj_set_style_text_color(ttl, lv_color_hex(0xffffff), LV_PART_MAIN);
    lv_obj_align(ttl, LV_ALIGN_TOP_LEFT, 54, 12);

    // Content container below the header.
    lv_obj_t *content = lv_obj_create(scr);
    lv_obj_set_size(content, DISPLAY_WIDTH - 16, DISPLAY_HEIGHT - 56);
    lv_obj_align(content, LV_ALIGN_TOP_MID, 0, 46);
    lv_obj_set_style_bg_color(content, lv_color_hex(0x14161a), LV_PART_MAIN);
    lv_obj_set_style_border_width(content, 1, LV_PART_MAIN);
    lv_obj_set_style_border_color(content, lv_color_hex(0x2a2e36), LV_PART_MAIN);
    lv_obj_set_style_radius(content, 8, LV_PART_MAIN);
    lv_obj_set_style_pad_all(content, 10, LV_PART_MAIN);

    lv_scr_load(scr);
    return content;
}
