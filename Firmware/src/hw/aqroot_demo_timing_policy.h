#pragma once
#include <stdint.h>

namespace aqroot {

// D-787 / Round-6: these are executable timing policies, not source-text
// conventions. The host test records callback order and elapsed time.
constexpr uint32_t kFuelGaugeActiveSettleMs = 300;
constexpr uint32_t kBacklightStartupPrimeUs = 3000;

template <typename Gauge, typename Bus, typename WaitMs>
bool qualifyFuelGaugeActiveMode(Gauge &gauge, Bus &bus, WaitMs wait_ms) {
  if (!gauge.configureActiveMode(bus)) return false;
  wait_ms(kFuelGaugeActiveSettleMs);
  return true;
}

template <typename WriteDuty, typename WaitUs, typename WaitMs>
void runBacklightRampPolicy(WriteDuty write_duty, WaitUs wait_us,
                            WaitMs wait_ms) {
  // The first PWM command MUST be full duty and it MUST remain there for the
  // complete prime interval before any dim duty is issued.
  write_duty(255);
  wait_us(kBacklightStartupPrimeUs);
  for (int duty = 5; duty <= 255; duty += 5) {
    write_duty(uint8_t(duty));
    wait_ms(8);
  }
  for (int duty = 255; duty >= 0; duty -= 5) {
    write_duty(uint8_t(duty));
    wait_ms(8);
  }
  write_duty(0);
}

}  // namespace aqroot
