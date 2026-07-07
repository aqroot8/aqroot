#pragma once
// Sensor driver interface — 6-axis IMU (accel + gyro, e.g. BMI270)

typedef struct {
    float accel_x, accel_y, accel_z;
    float gyro_x, gyro_y, gyro_z;
} imu_reading_t;

void sensors_init(void);
imu_reading_t sensors_read_imu(void);
