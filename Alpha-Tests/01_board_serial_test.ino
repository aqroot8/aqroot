// AQROOT Alpha - Test 1: bare board serial test (PASSED)
// Confirms toolchain + board are alive.
void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println("AQROOT board alive!");
}
void loop() {
  Serial.println("still running...");
  delay(1000);
}
