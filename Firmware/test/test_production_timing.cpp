// AQROOT Demo -- D-788 / R7-D787-05 + R7-D787-06.
//
// THIS TEST COMPILES AND RUNS THE SHIPPED ENTRY POINTS, NOT A SEAM.
//
// Round-7 reproduced a complete false green on D-787: every clause of H1-H8
// passed with
//   * the production gauge wait callback removed, halved, or its caller made
//     unreachable, and
//   * the production backlight microsecond callback made a no-op or halved and
//     the actual PWM duty writer halved,
// because `test_timing_policy.cpp` drives `aqroot_demo_timing_policy.h` through
// its OWN fakes.  A policy template nobody exercises in its shipped form is the
// same defect one level up from a source-text gate.
//
// So this test includes the REAL `backlightRamp()` and the REAL
// `configureFuelGaugeActiveModeOnHardware()` against `harness/Arduino.h`, whose
// `delay`, `delayMicroseconds` and `ledcWrite` timestamp and record every call.
// Every claim below is about what the assembled board would do.

#include <cstdio>
#include <cstdint>

#include "harness/Arduino.h"

#include "aqroot_demo_backlight.h"
#include "aqroot_demo_gauge_bringup.h"

using namespace aqroot;

static int failures = 0;
static void claim(const char *name, bool ok) {
  std::printf("[%s] %s\n", ok ? "PASS" : "FAIL", name);
  if (!ok) ++failures;
}

// ---------------------------------------------------------------------------
// A gauge whose qualification is observable on the recording clock.
struct FakeBus {};

struct FakeGauge {
  bool result = true;
  int configure_calls = 0;
  uint64_t configured_at_us = UINT64_MAX;
  bool configureActiveMode(FakeBus &) {
    ++configure_calls;
    configured_at_us = aqroot_hal::recorder().clock_us;
    return result;
  }
};

int main() {
  // ---- the SHIPPED backlight entry point --------------------------------
  {
    aqroot_hal::recorder().reset();
    backlightRamp(0);
    const auto &r = aqroot_hal::recorder();

    claim("production backlightRamp issues PWM commands", !r.pwm.empty());
    claim("production backlightRamp attaches the mapped backlight pin",
          r.attached_pin == AQROOT_PIN_DISP_BL_PWM);
    claim("production PWM frequency stays inside TI's 5-100 kHz window",
          r.ledc_hz >= 5000 && r.ledc_hz <= 100000 && r.ledc_bits == 8);

    // R7-D787-06: the FIRST command the hardware sees must be full duty.
    claim("first production PWM command is full duty at t=0",
          !r.pwm.empty() && r.pwm.front().duty == 255 &&
          r.pwm.front().t_us == 0);

    // ...and it must be HELD.  This is the claim a halved production
    // `delayMicroseconds(us / 2)` or a no-op `(void)us;` breaks.
    uint64_t first_dim_us = UINT64_MAX;
    bool saw_full = false;
    for (const auto &e : r.pwm) {
      if (e.duty == 255) { saw_full = true; continue; }
      if (e.duty > 0 && e.duty < 255) { first_dim_us = e.t_us; break; }
    }
    claim("production ramp reaches full duty", saw_full);
    claim("no production dim PWM command before the full prime interval",
          first_dim_us >= kBacklightStartupPrimeUs);
    claim("the production prime interval is at least 3000 us",
          kBacklightStartupPrimeUs >= 3000 && first_dim_us >= 3000);

    // A HALVED DUTY WRITER is invisible to an ordering check, so the duty
    // VALUES are a claim too: the shipped writer must pass the policy's own
    // ramp unmodified, which means the ramp visits every multiple of 5 and
    // terminates at zero.
    bool has_5 = false, has_250 = false;
    int full_duty_commands = 0;
    for (const auto &e : r.pwm) {
      if (e.duty == 5) has_5 = true;
      if (e.duty == 250) has_250 = true;
      if (e.duty == 255) ++full_duty_commands;
    }
    claim("the production duty writer passes the policy's duties unmodified",
          has_5 && has_250 && full_duty_commands >= 2);
    claim("production ramp ends at duty zero and parks the pin low",
          !r.pwm.empty() && r.pwm.back().duty == 0 && r.detached &&
          r.digital_writes_low >= 1);

    // The restart path must be identical: a second call may not begin dim.
    aqroot_hal::recorder().reset();
    backlightRamp(1);
    const auto &r2 = aqroot_hal::recorder();
    claim("a restarted production ramp still begins at full duty",
          !r2.pwm.empty() && r2.pwm.front().duty == 255 &&
          r2.pwm.front().t_us == 0 && r2.pwm.front().channel == 1);
  }

  // ---- the SHIPPED gauge qualification entry point -----------------------
  {
    aqroot_hal::recorder().reset();
    FakeBus bus;
    FakeGauge gauge;
    const bool ok = configureFuelGaugeActiveModeOnHardware(gauge, bus);
    const auto &r = aqroot_hal::recorder();

    claim("production gauge qualification succeeds", ok);
    claim("production qualification happens before any settle wait",
          gauge.configure_calls == 1 && gauge.configured_at_us == 0);
    // R7-D787-05: the wait the BOARD performs, measured on the clock the
    // production callback advances -- not on a test's own fake.
    claim("the production settle wait is at least 300 ms of real delay",
          r.total_delay_ms >= 300 &&
          r.clock_us - gauge.configured_at_us >= 300000u);
    claim("the production settle policy constant is at least 300 ms",
          kFuelGaugeActiveSettleMs >= 300);
    claim("the production settle is spent in the wait, not in dead code",
          !r.delay_ms_calls.empty());
  }

  {
    aqroot_hal::recorder().reset();
    FakeBus bus;
    FakeGauge gauge;
    gauge.result = false;
    const bool ok = configureFuelGaugeActiveModeOnHardware(gauge, bus);
    const auto &r = aqroot_hal::recorder();
    claim("failed production qualification is refused", !ok);
    claim("failed production qualification spends no settle time",
          r.total_delay_ms == 0 && r.clock_us == 0 &&
          r.delay_ms_calls.empty());
  }

  std::printf("\n%s -- %d failure(s)\n", failures ? "FAIL" : "PASS", failures);
  return failures ? 1 : 0;
}
