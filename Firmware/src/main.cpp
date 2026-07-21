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
//
// The S3 simulation runs slower than wall-clock time, so a quick mouse click on a Wokwi
// pushbutton can last less than one LVGL indev poll period (30 ms of *simulated* time)
// and be sampled away entirely. Each button therefore latches its falling edge in a GPIO
// interrupt; the read callback consumes the latch, so even the shortest click registers.
static lv_indev_drv_t s_keys_drv;

typedef struct {
    uint8_t       pin;
    uint32_t      key;
    volatile bool edge;   // set by ISR on press, consumed by keys_read_cb
} sim_key_t;

static sim_key_t s_keys[] = {
    { BTN_PREV,  LV_KEY_PREV,  false },
    { BTN_NEXT,  LV_KEY_NEXT,  false },
    { BTN_ENTER, LV_KEY_ENTER, false },
};
static const size_t SIM_KEY_COUNT = sizeof(s_keys) / sizeof(s_keys[0]);

static volatile bool s_back_edge = false;

// Diagnostic log, mirrored to USB-CDC (Serial) and UART0 (Serial0) so it shows up in the
// Wokwi serial monitor regardless of which console the simulator is attached to.
#define SIM_LOG(...) do { Serial.printf(__VA_ARGS__); Serial0.printf(__VA_ARGS__); } while (0)

static void IRAM_ATTR key_edge_isr(void *arg) {
    ((sim_key_t *)arg)->edge = true;
}

static void IRAM_ATTR back_edge_isr(void) {
    s_back_edge = true;
}

static void keys_read_cb(lv_indev_drv_t *drv, lv_indev_data_t *data) {
    (void)drv;
    static sim_key_t *cur = NULL;   // key currently reported to LVGL as pressed

    // Only navigate tiles while the home screen is active; tool screens use BACK (polled
    // in loop()) to return, so keypad presses there are dropped.
    if (lv_scr_act() != launcher_get_screen()) {
        for (size_t i = 0; i < SIM_KEY_COUNT; i++) s_keys[i].edge = false;
        data->key   = cur ? cur->key : 0;
        data->state = LV_INDEV_STATE_RELEASED;
        cur = NULL;
        return;
    }

    // A press was reported last poll: keep it pressed while the button is held (LVGL
    // long-press repeat), then report exactly one release.
    if (cur != NULL) {
        data->key = cur->key;
        if (digitalRead(cur->pin) == LOW) {
            data->state = LV_INDEV_STATE_PRESSED;
        } else {
            cur->edge   = false;   // swallow contact-bounce edges from the release
            data->state = LV_INDEV_STATE_RELEASED;
            cur = NULL;
        }
        return;
    }

    // Idle: start a new press from a latched edge or a currently-held button.
    for (size_t i = 0; i < SIM_KEY_COUNT; i++) {
        sim_key_t *k = &s_keys[i];
        if (k->edge || digitalRead(k->pin) == LOW) {
            k->edge = false;
            cur = k;
            data->key   = k->key;
            data->state = LV_INDEV_STATE_PRESSED;
            SIM_LOG("[sim-btn] GPIO%u -> key %u\n", k->pin, (unsigned)k->key);
            return;
        }
    }
    data->key   = 0;
    data->state = LV_INDEV_STATE_RELEASED;
}

// BACK button: return to the launcher from any tool screen. Latched by ISR so short
// clicks survive until the next loop() poll; ui_return_home() is a no-op when the home
// screen is already active, so stray edges are harmless.
static void poll_back_button(void) {
    static bool was_down = false;
    bool down = (digitalRead(BTN_BACK) == LOW);
    if (s_back_edge || (down && !was_down)) {
        s_back_edge = false;
        SIM_LOG("[sim-btn] GPIO%u -> BACK\n", (unsigned)BTN_BACK);
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
    nfc_init();       // PN532 — WRONG PART, pending ST25R3916/SPI rewrite
    sensors_init();   // 6-axis IMU
    audio_init();     // I2S mic + speaker

    // 3) App launcher shell (builds and loads the home screen).
    launcher_init();

#ifdef SIMULATION_MODE
    Serial0.begin(115200);   // UART0 mirror for SIM_LOG (Serial is USB-CDC in this build)

    for (size_t i = 0; i < SIM_KEY_COUNT; i++) {
        pinMode(s_keys[i].pin, INPUT_PULLUP);
        attachInterruptArg(s_keys[i].pin, key_edge_isr, &s_keys[i], FALLING);
    }
    pinMode(BTN_BACK, INPUT_PULLUP);
    attachInterrupt(BTN_BACK, back_edge_isr, FALLING);

    SIM_LOG("[sim] button levels at boot (1=idle): PREV=%d NEXT=%d ENTER=%d BACK=%d\n",
            digitalRead(BTN_PREV), digitalRead(BTN_NEXT),
            digitalRead(BTN_ENTER), digitalRead(BTN_BACK));

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
    // Heartbeat: proves the main loop (and therefore LVGL timer servicing) is alive.
    static uint32_t s_last_beat = 0;
    if (millis() - s_last_beat >= 5000) {
        s_last_beat = millis();
        SIM_LOG("[sim] alive, uptime %lus\n", (unsigned long)(millis() / 1000));
    }
#endif
    delay(5);
}
