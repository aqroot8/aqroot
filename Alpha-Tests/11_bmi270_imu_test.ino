// AQROOT Alpha - Test 11: BMI270 IMU (PASSED)
// SparkFun BMI270 Qwiic breakout, wired via jumpers to the shared I2C bus.
// I2C address 0x68 (confirmed via scanner). Shares SDA=GPIO1 / SCL=GPIO2 with the
// FT6236 touch controller (0x38) - multiple I2C devices coexisting, validated.
// Requires the "SparkFun BMI270 Arduino Library" (handles the config-blob upload the
// BMI270 needs before accel/gyro data works).
// Result: accel read -1.00g on the down axis (perfect gravity), gyro ~0 at rest and
// spikes on rotation. IMU detected AND functional.
// Wiring: SCL->GPIO2, SDA->GPIO1, 3V3->3V3, GND->GND. CS/ADR left unconnected.
#include <Wire.h>
#include "SparkFun_BMI270_Arduino_Library.h"
#define I2C_SDA 1
#define I2C_SCL 2
BMI270 imu;
void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println("\nAQROOT BMI270 Motion Test");
  Wire.begin(I2C_SDA, I2C_SCL);
  if (imu.beginI2C(0x68) != BMI2_OK) {
    Serial.println("BMI270 not detected. Check wiring.");
    while (1) delay(1000);
  }
  Serial.println("BMI270 connected! Tilt and move the board...\n");
}
void loop() {
  imu.getSensorData();
  Serial.print("Accel (g):  X="); Serial.print(imu.data.accelX, 2);
  Serial.print("  Y="); Serial.print(imu.data.accelY, 2);
  Serial.print("  Z="); Serial.print(imu.data.accelZ, 2);
  Serial.print("   |  Gyro (deg/s):  X="); Serial.print(imu.data.gyroX, 1);
  Serial.print("  Y="); Serial.print(imu.data.gyroY, 1);
  Serial.print("  Z="); Serial.println(imu.data.gyroZ, 1);
  delay(200);
}
