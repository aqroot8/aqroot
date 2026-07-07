// AQROOT — firmware entry point
// Boot order per OS Architecture note: display/touch -> launcher -> radio -> NFC -> sensors

#include "drivers/display.h"
#include "drivers/touch.h"
#include "drivers/radio.h"
#include "drivers/nfc.h"
#include "drivers/sensors.h"
#include "drivers/audio.h"

extern "C" void app_main(void) {
    display_init();
    touch_init();
    // TODO: lv_init() and launcher startup goes here once LVGL is wired in

    radio_init();   // SX1262 via RadioLib: LoRa + sub-GHz
    nfc_init();     // PN532
    sensors_init(); // 6-axis IMU
    audio_init();   // I2S mic + speaker

    // TODO: app launcher main loop (v1: simple flashable .bin menu)
}
