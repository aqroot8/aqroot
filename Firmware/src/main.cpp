// AQROOT — firmware entry point (Arduino core for ESP32-S3).
//
// Boot order (per "03 - OS Architecture.md"): display/touch -> launcher -> radio -> NFC
// -> sensors/audio. LVGL is initialized inside display_init(); its tick comes from the
// Arduino millis() clock (LV_TICK_CUSTOM in include/lv_conf.h), and lv_timer_handler() is
// pumped from loop().
//
// INPUT:
//   * Real hardware: the CST816 touchscreen drives an LVGL pointer device.
//   * SIMULATION_MODE: Wokwi has no CST816, so four physical buttons (wired in
//     diagram.json) drive an LVGL keypad — PREV/NEXT move focus between home tiles, ENTER
//     opens the focused tile, and BACK returns to the launcher.

#include <Arduino.h>
#include <lvgl.h>

#include "config.h"
#include "drivers/display.h"
#include "drivers/touch.h"
#include "drivers/radio.h"
#include "drivers/nfc.h"
#include "drivers/sensors.h"
#include "drivers/audio.h"
#include "ui/launcher.h"

// ---- Touch pointer input (real hardware) ----
static lv_indev_drv_t s_touch_drv;

static void touch_read_cb(lv_indev_drv_t *drv, lv_indev_data_t *data) {
    (void)drv;
    touch_point_t p = touch_get_point();
    if (p.pressed) {
        data->state   = LV_INDEV_STATE_PRESSED;
        data->point.x = p.x;
        data->point.y = p.y;
    } else {
        data->state = LV_INDEV_STATE_RELEASED;
    }
}

#ifdef SIMULATION_MODE
// ---- Physical-button keypad input (simulation stand-in for touch) ----
static lv_indev_drv_t s_keys_drv;

static void keys_read_cb(lv_indev_drv_t *drv, lv_indev_data_t *data) {
    (void)drv;
    // Only navigate tiles while the home screen is active; tool screens use BACK (polled
    // in loop()) to return, so keypad presses there are ignored.
    static uint32_t last_key = 0;
    if (lv_scr_act() != launcher_get_screen()) {
        data->key = last_key;
        data->state = LV_INDEV_STATE_RELEASED;
        return;
    }

    uint32_t key = 0;
    if (digitalRead(BTN_PREV) == LOW)       key = LV_KEY_PREV;
    else if (digitalRead(BTN_NEXT) == LOW)  key = LV_KEY_NEXT;
    else if (digitalRead(BTN_ENTER) == LOW) key = LV_KEY_ENTER;

    if (key != 0) {
        last_key = key;
        data->key = key;
        data->state = LV_INDEV_STATE_PRESSED;
    } else {
        data->key = last_key;
        data->state = LV_INDEV_STATE_RELEASED;
    }
}

// Edge-detected BACK button: return to the launcher from any tool screen.
static void poll_back_button(void) {
    static bool was_down = false;
    bool down = (digitalRead(BTN_BACK) == LOW);
    if (down && !was_down) {
        ui_return_home();
    }
    was_down = down;
}
#endif  // SIMULATION_MODE

void setup(void) {
    Serial.begin(115200);

    // 1) Display + LVGL, then touch.
    display_init();
    touch_init();

    lv_indev_drv_init(&s_touch_drv);
    s_touch_drv.type    = LV_INDEV_TYPE_POINTER;
    s_touch_drv.read_cb = touch_read_cb;
    lv_indev_drv_register(&s_touch_drv);

    // 2) Radios and sensors.
    radio_init();     // SX1262 via RadioLib: LoRa + sub-GHz
    nfc_init();       // PN532
    sensors_init();   // 6-axis IMU
    audio_init();     // I2S mic + speaker

    // 3) App launcher shell (builds and loads the home screen).
    launcher_init();

#ifdef SIMULATION_MODE
    pinMode(BTN_PREV,  INPUT_PULLUP);
    pinMode(BTN_NEXT,  INPUT_PULLUP);
    pinMode(BTN_ENTER, INPUT_PULLUP);
    pinMode(BTN_BACK,  INPUT_PULLUP);

    lv_indev_drv_init(&s_keys_drv);
    s_keys_drv.type    = LV_INDEV_TYPE_KEYPAD;
    s_keys_drv.read_cb = keys_read_cb;
    lv_indev_t *kp = lv_indev_drv_register(&s_keys_drv);
    lv_indev_set_group(kp, launcher_get_group());
#endif

    Serial.println("AQROOT ready");
}

void loop(void) {
    lv_timer_handler();
#ifdef SIMULATION_MODE
    poll_back_button();
#endif
    delay(5);
}
