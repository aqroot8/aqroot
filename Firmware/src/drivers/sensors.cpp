// AQROOT — sensor driver (6-axis IMU: accel + gyro).
//
// ============================== PLACEHOLDER PART ==============================
// The exact IMU is NOT finalized (BMI270 vs ICM-42670 — see "01 - Hardware Core.md").
// Rather than hard-depend on a BMI270 library that may not resolve on the PlatformIO
// registry (and that would need a multi-KB config blob uploaded at init), this reads a
// GENERIC 6-axis IMU over I2C using the common MPU-style register layout (accel @ 0x3B,
// gyro @ 0x43, wake via PWR_MGMT_1 @ 0x6B). Many breakout IMUs answer this map, which is
// enough to bring the UI up.
//
// When the final part is chosen: add its dedicated library to platformio.ini, replace the
// register offsets / scale factors below, and add the part-specific init (e.g. BMI270's
// config upload). The imu_reading_t interface does not change.
// =============================================================================

#include "sensors.h"
#include "../config.h"
#include <Arduino.h>

#ifndef SIMULATION_MODE
#include <Wire.h>

static const uint8_t REG_PWR_MGMT_1 = 0x6B;
static const uint8_t REG_ACCEL_XOUT = 0x3B;   // accel(6) then temp(2) then gyro(6)
static bool s_ready = false;

static bool read_bytes(uint8_t reg, uint8_t *out, uint8_t n) {
    Wire.beginTransmission(IMU_I2C_ADDR);
    Wire.write(reg);
    if (Wire.endTransmission(false) != 0) return false;
    if (Wire.requestFrom((int)IMU_I2C_ADDR, (int)n) != n) return false;
    for (uint8_t i = 0; i < n; i++) out[i] = Wire.read();
    return true;
}

void sensors_init(void) {
    Wire.begin(I2C_SDA, I2C_SCL, I2C_FREQ_HZ);
    Wire.beginTransmission(IMU_I2C_ADDR);
    Wire.write(REG_PWR_MGMT_1);
    Wire.write(0x00);   // wake device
    s_ready = (Wire.endTransmission() == 0);
}

imu_reading_t sensors_read_imu(void) {
    imu_reading_t r = {0, 0, 0, 0, 0, 0};
    if (!s_ready) return r;

    uint8_t d[14];
    if (!read_bytes(REG_ACCEL_XOUT, d, 14)) return r;

    int16_t ax = (d[0]  << 8) | d[1];
    int16_t ay = (d[2]  << 8) | d[3];
    int16_t az = (d[4]  << 8) | d[5];
    // d[6..7] = temperature (unused)
    int16_t gx = (d[8]  << 8) | d[9];
    int16_t gy = (d[10] << 8) | d[11];
    int16_t gz = (d[12] << 8) | d[13];

    // Generic ±2g / ±250 dps scaling; adjust for the final part's configured full-scale.
    const float accel_scale = 9.80665f / 16384.0f;  // -> m/s^2
    const float gyro_scale  = 1.0f / 131.0f;         // -> deg/s
    r.accel_x = ax * accel_scale;
    r.accel_y = ay * accel_scale;
    r.accel_z = az * accel_scale;
    r.gyro_x  = gx * gyro_scale;
    r.gyro_y  = gy * gyro_scale;
    r.gyro_z  = gz * gyro_scale;
    return r;
}

#else
// ============================ SIMULATION (mock data) ============================
void sensors_init(void) {}

imu_reading_t sensors_read_imu(void) {
    // Device resting flat, face up, with a little sensor noise.
    imu_reading_t r;
    r.accel_x = (random(-40, 41)) / 100.0f;
    r.accel_y = (random(-40, 41)) / 100.0f;
    r.accel_z = 9.81f + (random(-20, 21)) / 100.0f;
    r.gyro_x  = (random(-30, 31)) / 100.0f;
    r.gyro_y  = (random(-30, 31)) / 100.0f;
    r.gyro_z  = (random(-30, 31)) / 100.0f;
    return r;
}
#endif  // SIMULATION_MODE
