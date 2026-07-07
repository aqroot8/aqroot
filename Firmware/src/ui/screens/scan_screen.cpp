// Scan (Sub-GHz) screen.
// Puts the radio in raw sub-GHz mode and shows live RSSI, tuned frequency, and the bytes
// of any frame the SX1262 driver captures. In SIMULATION_MODE the radio driver feeds
// realistic mock data so this screen is fully testable without hardware.

#include "scan_screen.h"
#include "../launcher.h"
#include "../../drivers/radio.h"

#include <lvgl.h>
#include <stdio.h>

static lv_obj_t *s_freq_lbl;
static lv_obj_t *s_rssi_lbl;
static lv_obj_t *s_bar;
static lv_obj_t *s_pkt_lbl;

static void del_timer_cb(lv_event_t *e) {
    lv_timer_t *t = (lv_timer_t *)lv_event_get_user_data(e);
    if (t) lv_timer_del(t);
}

static void scan_tick(lv_timer_t *t) {
    (void)t;
    unsigned char buf[32];
    int n = radio_receive(buf, sizeof(buf));

    float rssi = radio_get_rssi();
    long  freq = radio_get_frequency();
    lv_label_set_text_fmt(s_freq_lbl, "Freq: %.2f MHz", freq / 1000000.0f);
    lv_label_set_text_fmt(s_rssi_lbl, "RSSI: %d dBm", (int)rssi);

    int level = (int)(rssi + 110.0f) * 100 / 70;
    if (level < 0) level = 0;
    if (level > 100) level = 100;
    lv_bar_set_value(s_bar, level, LV_ANIM_OFF);

    if (n > 0) {
        char line[80];
        int off = snprintf(line, sizeof(line), "RX %d B:", n);
        for (int i = 0; i < n && off < (int)sizeof(line) - 3; i++) {
            off += snprintf(line + off, sizeof(line) - off, " %02X", buf[i]);
        }
        lv_label_set_text(s_pkt_lbl, line);
    }
}

void scan_screen_open(void) {
    radio_set_mode(RADIO_MODE_SUBGHZ_RAW);

    lv_obj_t *c = ui_make_screen("Scan / Sub-GHz");
    lv_obj_set_flex_flow(c, LV_FLEX_FLOW_COLUMN);
    lv_obj_set_style_pad_row(c, 10, LV_PART_MAIN);

    s_freq_lbl = lv_label_create(c);
    lv_label_set_text(s_freq_lbl, "Freq: -- MHz");
    lv_obj_set_style_text_color(s_freq_lbl, lv_color_hex(0xf0f0f0), LV_PART_MAIN);

    s_rssi_lbl = lv_label_create(c);
    lv_label_set_text(s_rssi_lbl, "RSSI: -- dBm");
    lv_obj_set_style_text_color(s_rssi_lbl, lv_color_hex(0x2ecc71), LV_PART_MAIN);

    s_bar = lv_bar_create(c);
    lv_obj_set_size(s_bar, DISPLAY_WIDTH - 56, 12);
    lv_bar_set_range(s_bar, 0, 100);
    lv_obj_set_style_bg_color(s_bar, lv_color_hex(0x2ecc71), LV_PART_INDICATOR);

    s_pkt_lbl = lv_label_create(c);
    lv_label_set_long_mode(s_pkt_lbl, LV_LABEL_LONG_WRAP);
    lv_obj_set_width(s_pkt_lbl, DISPLAY_WIDTH - 56);
    lv_label_set_text(s_pkt_lbl, "Listening for frames...");
    lv_obj_set_style_text_color(s_pkt_lbl, lv_color_hex(0x8a8f98), LV_PART_MAIN);

    lv_timer_t *timer = lv_timer_create(scan_tick, 300, NULL);
    lv_obj_add_event_cb(c, del_timer_cb, LV_EVENT_DELETE, timer);
}
