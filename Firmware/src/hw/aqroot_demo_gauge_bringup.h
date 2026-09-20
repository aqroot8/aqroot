#pragma once
// AQROOT Demo -- the MAX17048 active-mode qualification PRODUCTION entry point.
//
// ADDED AT D-788 / R7-D787-05.  Round-7 reproduced a false green: the complete
// H1-H8 suite still passed with the production settle callback removed, halved,
// or its caller rendered unreachable, because the only executable test drove
// `qualifyFuelGaugeActiveMode` through its OWN fake wait.  The wait the ASSEMBLED
// BOARD performs lived in a lambda inside `demo/main.cpp`, which no host test
// ever compiled.
//
// The lambda now lives here, in a header that needs nothing but the Arduino
// `delay()` declaration, so `Firmware/test/test_production_timing.cpp` compiles
// and RUNS the shipped callback against a recording clock.  `demo/main.cpp`
// calls this and owns no second copy of the ordering.

#include <stdint.h>

#include <Arduino.h>

#include "aqroot_demo_timing_policy.h"

namespace aqroot {

// The SHIPPED qualification: HIBRT=0 + MODE.HibStat=0 must succeed FIRST, and
// only then does the board spend the settle interval.  A failed qualification
// returns false without waiting, so a hibernating or unreadable gauge cannot
// buy itself a settle it never earned.
template <typename Gauge, typename Bus>
inline bool configureFuelGaugeActiveModeOnHardware(Gauge &gauge, Bus &bus) {
  return qualifyFuelGaugeActiveMode(
      gauge, bus, [](uint32_t ms) { delay(ms); });
}

}  // namespace aqroot
