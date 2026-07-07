// AQROOT — touch driver.
//
// FINAL PART: CST816-series capacitive touch controller over I2C. This chip is confirmed
// (see "01 - Hardware Core.md") — this is a real implementation, not a placeholder.
//
// In SIMULATION_MODE the CST816 is absent (Wokwi has no model for it), so touch reports
// "not pressed" and navigation is handled by the physical-button keypad wired in
// diagram.json (see main.cpp). On real hardware the touchscreen is the primary input.

#include "touch.h"
#include "../config.h"

#include <Arduino.h>
#include <Wire.h>

// CST816 register map (read starting at 0x02):
//   0x02 : number of touch points
//   0x03 : X high nibble (bits[3:0]) + event flag (bits[7:6])
//   0x04 : X low byte
//   0x05 : Y high nibble (bits[3:0])
//   0x06 : Y low byte
static const uint8_t CST816_REG_TOUCH = 0x02;

void touch_init(void) {
#ifndef SIMULATION_MODE
    Wire.begin(I2C_SDA, I2C_SCL, I2C_FREQ_HZ);
#endif
}

touch_point_t touch_get_point(void) {
    touch_point_t p = {0, 0, 0};

#ifndef SIMULATION_MODE
    Wire.beginTransmission(TOUCH_I2C_ADDR);
    Wire.write(CST816_REG_TOUCH);
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
