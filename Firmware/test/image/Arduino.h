#pragma once
// AQROOT Demo -- D-790 / D789-A04.  THE IMAGE-LEVEL ARDUINO CORE.
//
// `test/harness/Arduino.h` is the RECORDING core that lets a host test drive
// the safety headers.  It is not enough for Round-9: Astra's five
// counterexamples all live in `src/demo/main.cpp` itself -- `setup()`,
// `loop()` and the console dispatch -- which no host test had ever COMPILED.
// A helper can be perfect and its call site still be dead.
//
// This directory is the minimum core surface that lets `src/demo/main.cpp` be
// compiled and RUN on the host, unmodified, so the mutations Round-9 named
// are executed rather than grepped for.  It re-uses the recording clock and
// PWM log of `test/harness/Arduino.h` and adds `Serial`, `SPI`, `Wire`, the
// pin state the image parks, and the I2S surface `aqroot_demo_peripherals.h`
// needs.  Nothing here models hardware beyond what the image OBSERVES.

#include <stdint.h>
#include <stddef.h>
#include <stdarg.h>
#include <stdio.h>

#include <string>
#include <vector>

namespace aqroot_hal {

struct PwmWrite {
  uint8_t channel;
  uint8_t duty;
  uint64_t t_us;
};

struct PinWrite {
  uint8_t pin;
  uint8_t value;
  uint64_t t_us;
};

struct Recorder {
  uint64_t clock_us = 0;
  std::vector<PwmWrite> pwm;
  std::vector<uint64_t> delay_ms_calls;
  std::vector<uint64_t> delay_us_calls;
  uint64_t total_delay_ms = 0;
  uint64_t attached_pin = 0xFFFF;
  bool detached = false;
  int pin_mode_calls = 0;
  int digital_writes_low = 0;
  uint32_t ledc_hz = 0;
  uint8_t ledc_bits = 0;

  // --- image level -------------------------------------------------------
  std::vector<std::string> console;           // every Serial line
  std::vector<PinWrite> digital_writes;
  std::vector<uint8_t> pin_modes_set;         // pins that got a pinMode()
  std::string serial_in;                      // characters loop() will read
  size_t serial_in_pos = 0;
  int spi_begin_calls = 0;
  int i2s_installs = 0;
  bool pin_low[64] = {false};
  // What `digitalRead` returns.  Every pin idles HIGH, which is this board's
  // resting state for BOOT_N, WAKE_INT_N and the two I2C lines; the test sets
  // SPI-B MISO and SX1262 BUSY low, which is what a healthy radio presents.
  uint8_t pin_level[64];
  Recorder() { for (int i = 0; i < 64; ++i) pin_level[i] = 1; }

  void reset() { *this = Recorder(); }
  bool consoleHas(const char *needle) const {
    for (const auto &l : console) {
      if (l.find(needle) != std::string::npos) return true;
    }
    return false;
  }
  int consoleCount(const char *needle) const {
    int n = 0;
    for (const auto &l : console) {
      if (l.find(needle) != std::string::npos) ++n;
    }
    return n;
  }
};

inline Recorder &recorder() {
  static Recorder r;
  return r;
}

}  // namespace aqroot_hal

// ---------------------------------------------------------------------------
inline void delay(uint32_t ms) {
  auto &r = aqroot_hal::recorder();
  r.delay_ms_calls.push_back(ms);
  r.total_delay_ms += ms;
  r.clock_us += uint64_t(ms) * 1000u;
}

inline void delayMicroseconds(uint32_t us) {
  auto &r = aqroot_hal::recorder();
  r.delay_us_calls.push_back(us);
  r.clock_us += us;
}

inline uint32_t millis() {
  return uint32_t(aqroot_hal::recorder().clock_us / 1000u);
}
inline uint32_t micros() { return uint32_t(aqroot_hal::recorder().clock_us); }

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
#define INPUT_PULLUP 0x05
#define OUTPUT_OPEN_DRAIN 0x13
#define PULLUP 0x04
#define LOW 0x0
#define HIGH 0x1
#define MSBFIRST 1
#define SPI_MODE0 0x00
#define SPI_MODE1 0x01

inline void pinMode(uint8_t pin, uint8_t mode) {
  (void)mode;
  auto &r = aqroot_hal::recorder();
  ++r.pin_mode_calls;
  r.pin_modes_set.push_back(pin);
}

inline void digitalWrite(uint8_t pin, uint8_t value) {
  auto &r = aqroot_hal::recorder();
  if (value == LOW) {
    ++r.digital_writes_low;
    if (pin < 64) r.pin_low[pin] = true;
  } else if (pin < 64) {
    r.pin_low[pin] = false;
  }
  r.digital_writes.push_back({pin, value, r.clock_us});
}

// D-790 / D789-A04.  A HOST CORE MUST NOT LET A POLLING LOOP HANG.
//
// The image contains real hardware polls -- the CC1101's SO line, the
// SX1262's BUSY line, the IR receiver -- written as `while (digitalRead(...)
// == HIGH && millis() < deadline)`.  On silicon the pin moves; on the host it
// does not, so the deadline is the only thing that can end the loop and
// `millis()` only advances when the firmware ASKS to wait.  Every read
// therefore advances the recording clock by one microsecond: polling costs
// time here exactly as it does on the board, and no shipped poll can wedge
// this test whatever a future edit does to it.
inline int digitalRead(uint8_t pin) {
  auto &r = aqroot_hal::recorder();
  ++r.clock_us;
  return pin < 64 ? int(r.pin_level[pin]) : HIGH;
}

// ---------------------------------------------------------------------------
// Serial.  Every line the image prints is captured; `serial_in` is what the
// console dispatch will read.
class HostSerial {
 public:
  void begin(uint32_t) {}
  operator bool() const { return true; }
  void println() { aqroot_hal::recorder().console.emplace_back(""); }
  void println(const char *s) {
    aqroot_hal::recorder().console.emplace_back(s ? s : "");
  }
  void print(const char *s) { println(s); }
  void printf(const char *fmt, ...) {
    char buf[512];
    va_list ap;
    va_start(ap, fmt);
    vsnprintf(buf, sizeof(buf), fmt, ap);
    va_end(ap);
    aqroot_hal::recorder().console.emplace_back(buf);
  }
  int available() {
    auto &r = aqroot_hal::recorder();
    return int(r.serial_in.size() - r.serial_in_pos);
  }
  int read() {
    auto &r = aqroot_hal::recorder();
    if (r.serial_in_pos >= r.serial_in.size()) return -1;
    return int(r.serial_in[r.serial_in_pos++]);
  }
};
extern HostSerial Serial;
