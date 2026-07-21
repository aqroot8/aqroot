// AQROOT — touch driver.
//
// LOCKED PART: FT6236-family capacitive touch controller over I2C @ 0x38, validated on
// Alpha hardware alongside the ILI9341 panel (see "05 - Design Decisions Log.md").
//
// This was originally written against a CST816 @ 0x15. The FT6236 and CST816 share the same
// read layout starting at register 0x02 (count, then 12-bit X/Y with the high nibble
// masked), so the transfer logic below is unchanged — only TOUCH_I2C_ADDR moved.
//
// TODO (see "07 - Build TODO Tracker.md"): touch_init() must pulse CTP_RST low->high before
// the first read. The FT6236 is held asleep out of reset and will NOT even appear on an I2C
// scan without it — this cost real bench time during Alpha. Beta shares touch RST with the
// display RST on GPIO21, so the reset has to be sequenced with display init.
//
// In SIMULATION_MODE the controller is absent (Wokwi has no model for it), so touch reports
// "not pressed" and navigation is handled by the physical-button keypad wired in
// diagram.json (see main.cpp). On real hardware the touchscreen is the primary input.

#include "touch.h"
#include "../config.h"

#include <Arduino.h>
#include <Wire.h>

// FT6236 register map (read starting at 0x02) — CST816-compatible for these registers:
//   0x02 : number of touch points
//   0x03 : X high nibble (bits[3:0]) + event flag (bits[7:6])
//   0x04 : X low byte
//   0x05 : Y high nibble (bits[3:0])
//   0x06 : Y low byte
static const uint8_t TOUCH_REG_POINT = 0x02;

void touch_init(void) {
#ifndef SIMULATION_MODE
    Wire.begin(I2C_SDA, I2C_SCL, I2C_FREQ_HZ);
#endif
}

touch_point_t touch_get_point(void) {
    touch_point_t p = {0, 0, 0};

#ifndef SIMULATION_MODE
    Wire.beginTransmission(TOUCH_I2C_ADDR);
    Wire.write(TOUCH_REG_POINT);
    if (Wire.endTransmission(false) != 0) {
        return p;  // controller not responding this cycle
    }

    const uint8_t want = 5;
    if (Wire.requestFrom((int)TOUCH_I2C_ADDR, (int)want) != want) {
        return p;
    }

    uint8_t d[5];
    for (uint8_t i = 0; i < want; i++) {
        d[i] = Wire.read();
    }

    const uint8_t fingers = d[0] & 0x0F;
    if (fingers > 0) {
        p.x = ((d[1] & 0x0F) << 8) | d[2];
        p.y = ((d[3] & 0x0F) << 8) | d[4];
        p.pressed = 1;
    }
#endif  // !SIMULATION_MODE

    return p;
}
