#pragma once
// AQROOT Demo -- a RECORDING Arduino core, for host tests only.
//
// D-788 / R7-D787-05 + R7-D787-06.  Round-7's counterexamples all lived in the
// PRODUCTION callbacks -- `[](uint32_t ms) { delay(ms); }`,
// `[](uint32_t us) { delayMicroseconds(us); }`, `ledcWrite(channel, duty)` --
// and every one of them survived the whole gate suite because no host test ever
// compiled them.  This header is the minimum Arduino surface the two shipped
// bring-up entry points need, and every call is timestamped and recorded so a
// halved, no-op, reordered or bypassed production callback is VISIBLE.
//
// It is NOT a simulation.  Nothing here models hardware; it models only the
// passage of the time the production code asks for and the order of the PWM
// commands the production code issues.

#include <stdint.h>
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>

#include <vector>

namespace aqroot_hal {

struct PwmWrite {
  uint8_t channel;
  uint8_t duty;
  uint64_t t_us;          // recording clock when the command was issued
};

struct Recorder {
  uint64_t clock_us = 0;
  std::vector<PwmWrite> pwm;
  std::vector<uint64_t> delay_ms_calls;      // argument of every delay()
  std::vector<uint64_t> delay_us_calls;      // argument of every delayMicroseconds()
  uint64_t total_delay_ms = 0;               // as REQUESTED, in ms
  uint64_t attached_pin = 0xFFFF;
  bool detached = false;
  int pin_mode_calls = 0;
  int digital_writes_low = 0;
  uint32_t ledc_hz = 0;
  uint8_t ledc_bits = 0;
  // D-797 / D797-10: consecutive waits in which no time passed.
  uint64_t stalled_waits = 0;

  void reset() { *this = Recorder(); }
};

inline Recorder &recorder() {
  static Recorder r;
  return r;
}

// D-797 / D797-10.  AN UNBOUNDED WAIT IS A NAMED FAILURE, NOT AN EXHAUSTED
// HARNESS.  Every wait is RECORDED, so a wait loop that loses its own bound
// used to end only when the recording vector grew until `std::bad_alloc`
// terminated the process -- with no claim printed.  The same two limits as
// `test/image/Arduino.h`: a million consecutive waits with no elapsed time
// (a zero-length delay spinning), or twenty million waits since the last
// reset (a loop whose exit condition never comes).  Either prints a named
// `[FAIL]` claim and exits non-zero.
constexpr uint64_t kHostStalledWaitLimit = 1000000u;
constexpr size_t kHostRecordedWaitLimit = 20000000u;

[[noreturn]] inline void hostGuardFail(const char *why) {
  printf("[FAIL] host guard (D797-10): %s\n", why);
  fflush(stdout);
  exit(1);
}

inline void noteHostWait(uint64_t us) {
  auto &r = recorder();
  if (us == 0) {
    if (++r.stalled_waits > kHostStalledWaitLimit) {
      hostGuardFail("a shipped wait loop kept waiting without time passing "
                    "-- its own attempt bound is missing");
    }
  } else {
    r.stalled_waits = 0;
  }
  if (r.delay_ms_calls.size() + r.delay_us_calls.size()
      > kHostRecordedWaitLimit) {
    hostGuardFail("a shipped wait loop never reached its exit condition "
                  "(more than 20 million waits since the last reset)");
  }
}

}  // namespace aqroot_hal

// ---------------------------------------------------------------------------
// The Arduino surface.  Signatures match the ESP32 Arduino core's.
inline void delay(uint32_t ms) {
  auto &r = aqroot_hal::recorder();
  r.delay_ms_calls.push_back(ms);
  r.total_delay_ms += ms;
  aqroot_hal::noteHostWait(uint64_t(ms) * 1000u);
  r.clock_us += uint64_t(ms) * 1000u;
}

inline void delayMicroseconds(uint32_t us) {
  auto &r = aqroot_hal::recorder();
  r.delay_us_calls.push_back(us);
  aqroot_hal::noteHostWait(us);
  r.clock_us += us;
}

inline uint32_t millis() {
  return uint32_t(aqroot_hal::recorder().clock_us / 1000u);
}

inline uint32_t micros() {
  return uint32_t(aqroot_hal::recorder().clock_us);
}

inline double ledcSetup(uint8_t channel, uint32_t freq, uint8_t resolution) {
  (void)channel;
  auto &r = aqroot_hal::recorder();
  r.ledc_hz = freq;
  r.ledc_bits = resolution;
  return double(freq);
}

inline void ledcAttachPin(uint8_t pin, uint8_t channel) {
  (void)channel;
  aqroot_hal::recorder().attached_pin = pin;
}

inline void ledcDetachPin(uint8_t pin) {
  (void)pin;
  aqroot_hal::recorder().detached = true;
}

inline void ledcWrite(uint8_t channel, uint32_t duty) {
  auto &r = aqroot_hal::recorder();
  r.pwm.push_back({channel, uint8_t(duty), r.clock_us});
}

#define OUTPUT 0x03
#define INPUT 0x01
#define LOW 0x0
#define HIGH 0x1

inline void pinMode(uint8_t pin, uint8_t mode) {
  (void)pin;
  (void)mode;
  ++aqroot_hal::recorder().pin_mode_calls;
}

inline void digitalWrite(uint8_t pin, uint8_t value) {
  (void)pin;
  if (value == LOW) ++aqroot_hal::recorder().digital_writes_low;
}
