#include <cstdio>
#include <cstdint>
#include <vector>
#include "aqroot_demo_timing_policy.h"

using namespace aqroot;

static int failures = 0;
static void claim(const char *name, bool ok) {
  std::printf("[%s] %s\n", ok ? "PASS" : "FAIL", name);
  if (!ok) ++failures;
}

struct FakeBus {};

struct FakeGauge {
  bool result = true;
  uint64_t *clock_ms = nullptr;
  uint64_t configured_at_ms = UINT64_MAX;
  bool configureActiveMode(FakeBus &) {
    configured_at_ms = *clock_ms;
    return result;
  }
};

struct PwmEvent {
  uint8_t duty;
  uint64_t t_us;
};

int main() {
  {
    FakeBus bus;
    uint64_t clock_ms = 0;
    FakeGauge gauge;
    gauge.clock_ms = &clock_ms;
    uint64_t wait_started_ms = UINT64_MAX;
    uint32_t waited_ms = 0;
    const bool ok = qualifyFuelGaugeActiveMode(
        gauge, bus, [&](uint32_t ms) {
          wait_started_ms = clock_ms;
          waited_ms += ms;
          clock_ms += ms;
        });
    claim("gauge qualification succeeds", ok);
    claim("gauge is qualified before the settle wait starts",
          gauge.configured_at_ms == 0 && wait_started_ms >= gauge.configured_at_ms);
    claim("executed post-qualification settle is at least 300 ms",
          waited_ms >= 300 && clock_ms - gauge.configured_at_ms >= 300);
  }

  {
    FakeBus bus;
    uint64_t clock_ms = 0;
    FakeGauge gauge;
    gauge.clock_ms = &clock_ms;
    gauge.result = false;
    uint32_t waited_ms = 0;
    const bool ok = qualifyFuelGaugeActiveMode(
        gauge, bus, [&](uint32_t ms) {
          waited_ms += ms;
          clock_ms += ms;
        });
    claim("failed gauge qualification is refused", !ok);
    claim("failed qualification does not invent a settle wait", waited_ms == 0);
  }

  {
    uint64_t clock_us = 0;
    std::vector<PwmEvent> writes;
    runBacklightRampPolicy(
        [&](uint8_t duty) { writes.push_back({duty, clock_us}); },
        [&](uint32_t us) { clock_us += us; },
        [&](uint32_t ms) { clock_us += uint64_t(ms) * 1000; });

    claim("backlight policy emits PWM commands", !writes.empty());
    claim("first backlight command is full duty",
          !writes.empty() && writes.front().duty == 255 &&
          writes.front().t_us == 0);

    bool dim_before_prime = false;
    uint64_t first_dim_us = UINT64_MAX;
    for (const auto &e : writes) {
      if (e.duty < 255 && e.duty > 0) {
        first_dim_us = e.t_us;
        if (e.t_us < 3000) dim_before_prime = true;
        break;
      }
    }
    claim("no dim PWM command occurs before 3000 us",
          !dim_before_prime && first_dim_us >= 3000);
    claim("first dim command occurs only after the full-duty prime",
          first_dim_us >= kBacklightStartupPrimeUs);
    claim("ramp ends at duty zero",
          !writes.empty() && writes.back().duty == 0);
  }

  std::printf("\n%s -- %d failure(s)\n",
              failures ? "FAIL" : "PASS", failures);
  return failures ? 1 : 0;
}
