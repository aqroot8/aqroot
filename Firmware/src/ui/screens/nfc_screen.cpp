// NFC screen.
// Polls the PN532 driver for a tag UID and shows it live; a Write button performs a raw
// block write. In SIMULATION_MODE the NFC driver returns a fixed mock UID so the readout
// and write flow can be exercised without hardware.

#include "nfc_screen.h"
#include "../launcher.h"
#include "../../drivers/nfc.h"

#include <lvgl.h>
#include <stdio.h>

static lv_obj_t *s_uid_lbl;
static lv_obj_t *s_status_lbl;

static void del_timer_cb(lv_event_t *e) {
    lv_timer_t *t = (lv_timer_t *)lv_event_get_user_data(e);
    if (t) lv_timer_del(t);
}

static void nfc_tick(lv_timer_t *t) {
    (void)t;
    unsigned char uid[10];
    int n = nfc_read_tag(uid, sizeof(uid));
    if (n > 0) {
        char buf[48];
        int off = snprintf(buf, sizeof(buf), "UID:");
        for (int i = 0; i < n && off < (int)sizeof(buf) - 3; i++) {
            off += snprintf(buf + off, sizeof(buf) - off, " %02X", uid[i]);
        }
        lv_label_set_text(s_uid_lbl, buf);
        lv_obj_set_style_text_color(s_uid_lbl, lv_color_hex(0x2ecc71), LV_PART_MAIN);
    } else {
        lv_label_set_text(s_uid_lbl, "No tag in field");
        lv_obj_set_style_text_color(s_uid_lbl, lv_color_hex(0x8a8f98), LV_PART_MAIN);
    }
}

static void write_cb(lv_event_t *e) {
    (void)e;
    const unsigned char payload[] = "AQROOT";
    int w = nfc_write_tag(payload, sizeof(payload) - 1);
    if (w > 0) {
        lv_label_set_text_fmt(s_status_lbl, "Wrote %d bytes to block 4", w);
        lv_obj_set_style_text_color(s_status_lbl, lv_color_hex(0x2ecc71), LV_PART_MAIN);
    } else {
        lv_label_set_text(s_status_lbl, "Write failed (no writable tag)");
        lv_obj_set_style_text_color(s_status_lbl, lv_color_hex(0xe74c3c), LV_PART_MAIN);
    }
}

void nfc_screen_open(void) {
    lv_obj_t *c = ui_make_screen("NFC / 13.56 MHz");
    lv_obj_set_flex_flow(c, LV_FLEX_FLOW_COLUMN);
    lv_obj_set_style_pad_row(c, 12, LV_PART_MAIN);

    lv_obj_t *hint = lv_label_create(c);
    lv_label_set_text(hint, "Present a tag to read its UID:");
    lv_obj_set_style_text_color(hint, lv_color_hex(0xf0f0f0), LV_PART_MAIN);

    s_uid_lbl = lv_label_create(c);
    lv_label_set_long_mode(s_uid_lbl, LV_LABEL_LONG_WRAP);
    lv_obj_set_width(s_uid_lbl, DISPLAY_WIDTH - 56);
    lv_label_set_text(s_uid_lbl, "No tag in field");
    lv_obj_set_style_text_color(s_uid_lbl, lv_color_hex(0x8a8f98), LV_PART_MAIN);

    lv_obj_t *btn = lv_btn_create(c);
    lv_obj_set_style_bg_color(btn, lv_color_hex(0x3498db), LV_PART_MAIN);
    lv_obj_add_event_cb(btn, write_cb, LV_EVENT_CLICKED, NULL);
    lv_obj_t *btn_lbl = lv_label_create(btn);
    lv_label_set_text(btn_lbl, "Write \"AQROOT\"");
    lv_obj_center(btn_lbl);

    s_status_lbl = lv_label_create(c);
    lv_label_set_long_mode(s_status_lbl, LV_LABEL_LONG_WRAP);
    lv_obj_set_width(s_status_lbl, DISPLAY_WIDTH - 56);
    lv_label_set_text(s_status_lbl, "");

    lv_timer_t *timer = lv_timer_create(nfc_tick, 500, NULL);
    lv_obj_add_event_cb(c, del_timer_cb, LV_EVENT_DELETE, timer);
}
