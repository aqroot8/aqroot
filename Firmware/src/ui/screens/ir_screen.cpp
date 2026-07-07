// Infrared screen.
//
// NOTE ON SCOPE: Infrared is a planned tool, but there is no IR entry in src/drivers/ yet
// (the driver set delivered in this pass is display/touch/radio/nfc/sensors/audio). IR
// TX/RX on the ESP32-S3 is best done with the RMT peripheral driving an IR LED +
// demodulating receiver; that belongs in a future drivers/ir.{h,cpp} with the same stable
// interface pattern as the others. Until that lands, this screen is a working UI shell: a
// Capture button stores the last "received" code and a Send button replays it. The code
// value shown is a placeholder capture so the flow is demonstrable; wire these buttons to
// the real IR driver once it exists.

#include "ir_screen.h"
#include "../launcher.h"

#include <lvgl.h>
#include <stdio.h>

static lv_obj_t *s_code_lbl;
static lv_obj_t *s_status_lbl;
static uint32_t  s_captured = 0;

static void capture_cb(lv_event_t *e) {
    (void)e;
    // Placeholder capture: a real IR driver would decode a protocol frame here.
    s_captured = 0x20DF10EF;  // e.g. a NEC "power" code
    lv_label_set_text_fmt(s_code_lbl, "Captured: 0x%08X (NEC)", s_captured);
    lv_label_set_text(s_status_lbl, "Code captured (placeholder)");
    lv_obj_set_style_text_color(s_status_lbl, lv_color_hex(0x2ecc71), LV_PART_MAIN);
}

static void send_cb(lv_event_t *e) {
    (void)e;
    if (s_captured == 0) {
        lv_label_set_text(s_status_lbl, "Nothing captured yet");
        lv_obj_set_style_text_color(s_status_lbl, lv_color_hex(0xe74c3c), LV_PART_MAIN);
        return;
    }
    // A real IR driver would transmit s_captured over the RMT peripheral here.
    lv_label_set_text_fmt(s_status_lbl, "Sent 0x%08X (stub TX)", s_captured);
    lv_obj_set_style_text_color(s_status_lbl, lv_color_hex(0xe67e22), LV_PART_MAIN);
}

void ir_screen_open(void) {
    lv_obj_t *c = ui_make_screen("Infrared");
    lv_obj_set_flex_flow(c, LV_FLEX_FLOW_COLUMN);
    lv_obj_set_style_pad_row(c, 12, LV_PART_MAIN);

    lv_obj_t *hint = lv_label_create(c);
    lv_label_set_long_mode(hint, LV_LABEL_LONG_WRAP);
    lv_obj_set_width(hint, DISPLAY_WIDTH - 56);
    lv_label_set_text(hint, "IR capture / replay. Driver (RMT) pending hardware.");
    lv_obj_set_style_text_color(hint, lv_color_hex(0xf0f0f0), LV_PART_MAIN);

    s_code_lbl = lv_label_create(c);
    lv_label_set_text(s_code_lbl, "Captured: --");
    lv_obj_set_style_text_color(s_code_lbl, lv_color_hex(0xe74c3c), LV_PART_MAIN);

    lv_obj_t *cap = lv_btn_create(c);
    lv_obj_set_style_bg_color(cap, lv_color_hex(0xe74c3c), LV_PART_MAIN);
    lv_obj_add_event_cb(cap, capture_cb, LV_EVENT_CLICKED, NULL);
    lv_obj_t *cap_lbl = lv_label_create(cap);
    lv_label_set_text(cap_lbl, "Capture (RX)");
    lv_obj_center(cap_lbl);

    lv_obj_t *snd = lv_btn_create(c);
    lv_obj_set_style_bg_color(snd, lv_color_hex(0x8a4a44), LV_PART_MAIN);
    lv_obj_add_event_cb(snd, send_cb, LV_EVENT_CLICKED, NULL);
    lv_obj_t *snd_lbl = lv_label_create(snd);
    lv_label_set_text(snd_lbl, "Send (TX)");
    lv_obj_center(snd_lbl);

    s_status_lbl = lv_label_create(c);
    lv_label_set_long_mode(s_status_lbl, LV_LABEL_LONG_WRAP);
    lv_obj_set_width(s_status_lbl, DISPLAY_WIDTH - 56);
    lv_label_set_text(s_status_lbl, "");
}
