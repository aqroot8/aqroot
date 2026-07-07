// Tools screen.
// Exercises the sensor and audio drivers: a live 6-axis IMU readout, basic device info,
// and a Test Tone button. In SIMULATION_MODE the IMU driver returns mock motion data and
// the tone is silent (no I2S model in Wokwi), but the call paths are identical.

#include "tools_screen.h"
#include "../launcher.h"
#include "../../drivers/sensors.h"
#include "../../drivers/audio.h"

#include <Arduino.h>
#include <lvgl.h>

static lv_obj_t *s_accel_lbl;
static lv_obj_t *s_gyro_lbl;
static lv_obj_t *s_heap_lbl;

static void del_timer_cb(lv_event_t *e) {
    lv_timer_t *t = (lv_timer_t *)lv_event_get_user_data(e);
    if (t) lv_timer_del(t);
}

static void imu_tick(lv_timer_t *t) {
    (void)t;
    imu_reading_t r = sensors_read_imu();
    lv_label_set_text_fmt(s_accel_lbl, "Accel  x%+.2f  y%+.2f  z%+.2f m/s2",
                          r.accel_x, r.accel_y, r.accel_z);
    lv_label_set_text_fmt(s_gyro_lbl, "Gyro   x%+.1f  y%+.1f  z%+.1f dps",
                          r.gyro_x, r.gyro_y, r.gyro_z);
    lv_label_set_text_fmt(s_heap_lbl, "Free heap: %u KB", (unsigned)(ESP.getFreeHeap() / 1024));
}

static void tone_cb(lv_event_t *e) {
    (void)e;
    audio_play_tone(1000, 200);   // 1 kHz for 200 ms
}

void tools_screen_open(void) {
    lv_obj_t *c = ui_make_screen("Tools");
    lv_obj_set_flex_flow(c, LV_FLEX_FLOW_COLUMN);
    lv_obj_set_style_pad_row(c, 10, LV_PART_MAIN);

    lv_obj_t *imu_title = lv_label_create(c);
    lv_label_set_text(imu_title, "IMU (6-axis)");
    lv_obj_set_style_text_color(imu_title, lv_color_hex(0x9b59b6), LV_PART_MAIN);

    s_accel_lbl = lv_label_create(c);
    lv_label_set_long_mode(s_accel_lbl, LV_LABEL_LONG_WRAP);
    lv_obj_set_width(s_accel_lbl, DISPLAY_WIDTH - 56);
    lv_label_set_text(s_accel_lbl, "Accel  --");
    lv_obj_set_style_text_color(s_accel_lbl, lv_color_hex(0xf0f0f0), LV_PART_MAIN);

    s_gyro_lbl = lv_label_create(c);
    lv_label_set_long_mode(s_gyro_lbl, LV_LABEL_LONG_WRAP);
    lv_obj_set_width(s_gyro_lbl, DISPLAY_WIDTH - 56);
    lv_label_set_text(s_gyro_lbl, "Gyro   --");
    lv_obj_set_style_text_color(s_gyro_lbl, lv_color_hex(0xf0f0f0), LV_PART_MAIN);

    s_heap_lbl = lv_label_create(c);
    lv_label_set_text(s_heap_lbl, "Free heap: -- KB");
    lv_obj_set_style_text_color(s_heap_lbl, lv_color_hex(0x8a8f98), LV_PART_MAIN);

    lv_obj_t *btn = lv_btn_create(c);
    lv_obj_set_style_bg_color(btn, lv_color_hex(0x9b59b6), LV_PART_MAIN);
    lv_obj_add_event_cb(btn, tone_cb, LV_EVENT_CLICKED, NULL);
    lv_obj_t *btn_lbl = lv_label_create(btn);
    lv_label_set_text(btn_lbl, "Test tone (1 kHz)");
    lv_obj_center(btn_lbl);

    lv_timer_t *timer = lv_timer_create(imu_tick, 200, NULL);
    lv_obj_add_event_cb(c, del_timer_cb, LV_EVENT_DELETE, timer);
}
