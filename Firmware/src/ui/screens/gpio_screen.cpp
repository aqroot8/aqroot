// GPIO screen.
// Real digital I/O on the expansion-header test pins (config.h GPIO_TEST_OUT / _IN). The
// Toggle button flips the output pin; a timer polls and displays the input pin state.
// These pins are PLACEHOLDER assignments pending the final header pinout.

#include "gpio_screen.h"
#include "../launcher.h"
#include "../../config.h"

#include <Arduino.h>
#include <lvgl.h>

static lv_obj_t *s_out_lbl;
static lv_obj_t *s_in_lbl;
static int       s_out_state = 0;

static void del_timer_cb(lv_event_t *e) {
    lv_timer_t *t = (lv_timer_t *)lv_event_get_user_data(e);
    if (t) lv_timer_del(t);
}

static void in_tick(lv_timer_t *t) {
    (void)t;
    int v = digitalRead(GPIO_TEST_IN);
    lv_label_set_text_fmt(s_in_lbl, "Input  (GPIO%d): %s", GPIO_TEST_IN, v ? "HIGH" : "LOW");
    lv_obj_set_style_text_color(s_in_lbl,
        v ? lv_color_hex(0x2ecc71) : lv_color_hex(0x8a8f98), LV_PART_MAIN);
}

static void toggle_cb(lv_event_t *e) {
    (void)e;
    s_out_state = !s_out_state;
    digitalWrite(GPIO_TEST_OUT, s_out_state ? HIGH : LOW);
    lv_label_set_text_fmt(s_out_lbl, "Output (GPIO%d): %s",
                          GPIO_TEST_OUT, s_out_state ? "HIGH" : "LOW");
    lv_obj_set_style_text_color(s_out_lbl,
        s_out_state ? lv_color_hex(0xe67e22) : lv_color_hex(0x8a8f98), LV_PART_MAIN);
}

void gpio_screen_open(void) {
    pinMode(GPIO_TEST_OUT, OUTPUT);
    digitalWrite(GPIO_TEST_OUT, s_out_state ? HIGH : LOW);
    pinMode(GPIO_TEST_IN, INPUT_PULLUP);

    lv_obj_t *c = ui_make_screen("GPIO Control");
    lv_obj_set_flex_flow(c, LV_FLEX_FLOW_COLUMN);
    lv_obj_set_style_pad_row(c, 12, LV_PART_MAIN);

    s_out_lbl = lv_label_create(c);
    lv_label_set_text_fmt(s_out_lbl, "Output (GPIO%d): %s",
                          GPIO_TEST_OUT, s_out_state ? "HIGH" : "LOW");
    lv_obj_set_style_text_color(s_out_lbl, lv_color_hex(0x8a8f98), LV_PART_MAIN);

    lv_obj_t *btn = lv_btn_create(c);
    lv_obj_set_style_bg_color(btn, lv_color_hex(0xe67e22), LV_PART_MAIN);
    lv_obj_add_event_cb(btn, toggle_cb, LV_EVENT_CLICKED, NULL);
    lv_obj_t *btn_lbl = lv_label_create(btn);
    lv_label_set_text(btn_lbl, "Toggle output");
    lv_obj_center(btn_lbl);

    s_in_lbl = lv_label_create(c);
    lv_label_set_text_fmt(s_in_lbl, "Input  (GPIO%d): --", GPIO_TEST_IN);
    lv_obj_set_style_text_color(s_in_lbl, lv_color_hex(0x8a8f98), LV_PART_MAIN);

    lv_timer_t *timer = lv_timer_create(in_tick, 200, NULL);
    lv_obj_add_event_cb(c, del_timer_cb, LV_EVENT_DELETE, timer);
}
