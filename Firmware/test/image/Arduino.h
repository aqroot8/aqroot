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

// D-797 / D797-08: tells `src/demo/main.cpp` it is being compiled against
// this host core, which is the only build that gets its one test seam
// (`aqrootHostImageSpiB()`).  The ESP32 Arduino core never defines it.
#define AQROOT_HOST_IMAGE_HARNESS 1

#include <stdint.h>
#include <stddef.h>
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>

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
  // D-800: the SCK the SPI peripheral is bound to (-1 = released), and how
  // many `begin`s asked for OTHER pins while it was bound -- which the real
  // core silently ignores.
  int spi_bound_sck = -1;
  uint64_t hang_guard_us = ~uint64_t(0);      // D-800, see advanceClockUs
  int spi_begin_ignored_other_pins = 0;
  int i2s_installs = 0;
  bool pin_low[64] = {false};
  // D-795 / R14-02: how often each pin has been driven from HIGH to LOW, so a
  // SPI peripheral model can see a chip-select FRAME begin -- which is when a
  // real part resets its own SPI state machine.
  uint32_t low_edges[64] = {0};
  // D-795 / R14-01: an RTOS delay is `vTaskDelay(ms / portTICK_PERIOD_MS)`
  // and can return up to a tick early.  With this set, every delay longer
  // than it returns that many milliseconds EARLY, so a caller that delays
  // once and assumes the time has passed is caught.
  uint32_t delay_shortfall_ms = 0;
  // D-796 / C-GAUGE-EPOCH-01 (Fable G10).  A STALLED FRESHNESS CLOCK.  With
  // `clock_frozen` set -- or once the clock reaches `freeze_at_us` -- nothing
  // advances the recording clock any more: not `delay()`, not
  // `delayMicroseconds()`, not a `digitalRead()` poll.  `millis()` then
  // returns the same value for ever, which is the condition the gauge window
  // must FAIL CLOSED on rather than read as elapsed time.  `frozen_polls`
  // bounds a shipped polling loop that spins on the frozen clock, so a mutant
  // that hangs is reported as a FAILED claim rather than wedging the gate.
  bool clock_frozen = false;
  uint64_t freeze_at_us = ~uint64_t(0);
  uint64_t frozen_polls = 0;
  // D-797 / D797-10.  THE SAME BOUND FOR A WAIT LOOP.  `frozen_polls` only
  // covered `digitalRead()`.  A wait loop that loses its own attempt bound
  // spins on `delay()` instead, and every call is RECORDED -- so before this
  // counter the only thing that ended such a mutant was the recording vector
  // growing until `std::bad_alloc` terminated the process with no claim
  // printed.  `stalled_waits` counts CONSECUTIVE waits that did not move the
  // clock (a frozen clock, or a zero-length wait); the limit below turns an
  // unbounded wait into a NAMED failed claim.
  uint64_t stalled_waits = 0;
  // D-796 / C-NFC-QUIESCE-01: when each console line was printed, so a
  // revocation LATENCY can be measured from the image's own output.
  std::vector<uint64_t> console_t_us;
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

// D-797 / D797-10.  AN UNBOUNDED WAIT IS A NAMED FAILURE, NOT AN EXHAUSTED
// HARNESS.  Every `delay()` / `delayMicroseconds()` passes through
// `noteHostWait` before it moves the clock.  Two limits, each far above any
// scenario the image test runs between two `rig()` resets:
//
//   * a million CONSECUTIVE waits in which no time passed -- a wait loop
//     spinning on a frozen clock, or on a zero-length delay;
//   * twenty million waits recorded since the last reset -- a wait loop whose
//     clock does advance but whose exit condition never comes.
//
// Either prints a `[FAIL]` claim that says which, and exits non-zero, so a
// mutant that removes a loop's own bound is caught for that stated reason.
constexpr uint64_t kHostStalledWaitLimit = 1000000u;
constexpr size_t kHostRecordedWaitLimit = 20000000u;
constexpr size_t kHostConsoleLineLimit = 2000000u;

[[noreturn]] inline void hostGuardFail(const char *why) {
  printf("[FAIL] host guard (D797-10): %s\n", why);
  fflush(stdout);
  exit(1);
}

inline void noteHostWait(uint64_t us) {
  auto &r = recorder();
  if (r.clock_frozen || us == 0) {
    if (++r.stalled_waits > kHostStalledWaitLimit) {
      hostGuardFail("a shipped wait loop kept waiting on a clock that does "
                    "not advance -- its own attempt bound is missing");
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

// Every advance of the recording clock goes through here, so a frozen clock
// is frozen for every caller alike.
inline void advanceClockUs(uint64_t us) {
  auto &r = recorder();
  if (r.clock_frozen) return;
  r.clock_us += us;
  // D-800: a HANG GUARD for the millis()-wrap scenarios.  A wait that ignores
  // its own bound near the wrap spins for ever; past `hang_guard_us` any
  // clock advance ends the run as a NAMED failed claim instead.
  if (r.clock_us > r.hang_guard_us) {
    printf("[FAIL] host: a shipped wait ran past its own bound across the "
           "millis() wrap\n");
    fflush(stdout);
    exit(1);
  }
  if (r.clock_us >= r.freeze_at_us) {
    r.clock_us = r.freeze_at_us;
    r.clock_frozen = true;
  }
}

inline void consoleLine(const char *s) {
  auto &r = recorder();
  if (r.console.size() > kHostConsoleLineLimit) {
    hostGuardFail("the image printed more than two million console lines "
                  "since the last reset -- a loop that never ends");
  }
  r.console.emplace_back(s ? s : "");
  r.console_t_us.push_back(r.clock_us);
}

}  // namespace aqroot_hal

// ---------------------------------------------------------------------------
inline void delay(uint32_t ms) {
  auto &r = aqroot_hal::recorder();
  r.delay_ms_calls.push_back(ms);
  r.total_delay_ms += ms;
  const uint32_t real = (ms > r.delay_shortfall_ms) ? ms - r.delay_shortfall_ms
                                                     : ms;
  aqroot_hal::noteHostWait(uint64_t(real) * 1000u);
  aqroot_hal::advanceClockUs(uint64_t(real) * 1000u);
}

inline void delayMicroseconds(uint32_t us) {
  auto &r = aqroot_hal::recorder();
  r.delay_us_calls.push_back(us);
  aqroot_hal::noteHostWait(us);
  aqroot_hal::advanceClockUs(us);
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
    if (pin < 64 && !r.pin_low[pin]) ++r.low_edges[pin];
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
  if (r.clock_frozen && ++r.frozen_polls > 1000000u) {
    printf("[FAIL] host: a shipped polling loop spun on a frozen clock\n");
    fflush(stdout);
    exit(1);
  }
  aqroot_hal::advanceClockUs(1);
  return pin < 64 ? int(r.pin_level[pin]) : HIGH;
}

// ---------------------------------------------------------------------------
// Serial.  Every line the image prints is captured; `serial_in` is what the
// console dispatch will read.
class HostSerial {
 public:
  void begin(uint32_t) {}
  operator bool() const { return true; }
  void println() { aqroot_hal::consoleLine(""); }
  void println(const char *s) { aqroot_hal::consoleLine(s); }
  void print(const char *s) { println(s); }
  void printf(const char *fmt, ...) {
    char buf[512];
    va_list ap;
    va_start(ap, fmt);
    vsnprintf(buf, sizeof(buf), fmt, ap);
    va_end(ap);
    aqroot_hal::consoleLine(buf);
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
