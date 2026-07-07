// Bluetooth screen.
//
// Shows the device's own controller MAC (read from the ESP32-S3 eFuse, no extra library)
// and a list of nearby devices. A live BLE/Classic scan needs the NimBLE or BLEDevice
// stack; that is intentionally not pulled in yet (heavy dependency, and Wokwi has no radio
// model), so the Scan button here fills the list with representative entries. Swap the
// scan handler for a real NimBLE scan once the BLE app layer is added.

#include "bluetooth_screen.h"
#include "../launcher.h"

#include <Arduino.h>
#include <lvgl.h>

static lv_obj_t *s_list;

static void add_row(const char *name, const char *rssi) {
    lv_obj_t *btn = lv_list_add_btn(s_list, LV_SYMBOL_BLUETOOTH, name);
    lv_obj_t *lbl = lv_label_create(btn);
    lv_label_set_text(lbl, rssi);
}

static void scan_cb(lv_event_t *e) {
    (void)e;
    lv_obj_clean(s_list);
    // Representative results (placeholder for a real NimBLE scan).
    add_row("Pixel-Buds  A4:C1", "-58 dBm");
    add_row("MI Band 7  E8:9F", "-71 dBm");
    add_row("BLE-Sensor 12:3A", "-83 dBm");
}

void bluetooth_screen_open(void) {
    lv_obj_t *c = ui_make_screen("Bluetooth");
    lv_obj_set_flex_flow(c, LV_FLEX_FLOW_COLUMN);
    lv_obj_set_style_pad_row(c, 10, LV_PART_MAIN);

    uint64_t mac = ESP.getEfuseMac();
    uint8_t *m = (uint8_t *)&mac;
    lv_obj_t *self = lv_label_create(c);
    lv_label_set_text_fmt(self, "This device: %02X:%02X:%02X:%02X:%02X:%02X",
                          m[0], m[1], m[2], m[3], m[4], m[5]);
    lv_obj_set_style_text_color(self, lv_color_hex(0x2980e0), LV_PART_MAIN);

    lv_obj_t *btn = lv_btn_create(c);
    lv_obj_set_style_bg_color(btn, lv_color_hex(0x2980e0), LV_PART_MAIN);
    lv_obj_add_event_cb(btn, scan_cb, LV_EVENT_CLICKED, NULL);
    lv_obj_t *btn_lbl = lv_label_create(btn);
    lv_label_set_text(btn_lbl, "Scan");
    lv_obj_center(btn_lbl);

    s_list = lv_list_create(c);
    lv_obj_set_size(s_list, DISPLAY_WIDTH - 56, 140);
    lv_obj_set_style_bg_color(s_list, lv_color_hex(0x0f1114), LV_PART_MAIN);
}
