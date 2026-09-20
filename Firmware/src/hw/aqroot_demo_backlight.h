#pragma once
// AQROOT Demo -- the display backlight production entry point.
//
// SEPARATED FROM `aqroot_demo_peripherals.h` AT D-788 / R7-D787-06.  Round-7
// reproduced a false green: the whole H1-H8 suite still passed with this
// block's PWM duty writer halved and its microsecond callback made a no-op,
// because the only executable test drove `runBacklightRampPolicy` through its
// OWN fakes and never compiled the production lambdas.  The block now lives in
// a header that needs nothing but the Arduino LEDC API, so
// `Firmware/test/test_production_timing.cpp` compiles and RUNS the shipped
// `backlightRamp()` against a recording HAL and the mutations are caught.
//
// Anything added here must stay compilable against
// `Firmware/test/harness/Arduino.h`.

#include <stdint.h>

#include <Arduino.h>

#include "aqroot_demo_board.h"
#include "aqroot_demo_timing_policy.h"

namespace aqroot {

// Backlight: U17 TPS61169 WLED boost, enabled and dimmed from GPIO46 through
// R109.  GPIO46 is a strapping pin held low by R108 at reset, so this is also
// the moment the strap stops being a strap.
//
// CTRL IS AN ANALOG DIMMING INPUT, NOT A CHOPPER.  TI SNVSA40B section 6.3.5:
// the part chops its internal 204 mV reference at the CTRL duty cycle, filters
// it, and regulates the LED current to the average -- "only the WLED DC current
// is modulated, which is often referred as analog dimming".  The converter
// therefore KEEPS SWITCHING through every PWM low phase, and only enters
// shutdown after CTRL has been low for longer than tSD (2.5 ms max).
//
// THAT IS WHY Q11's GATE IS NOT ON THIS PIN.  Q11 is the panel-cathode
// true-off disconnect (the TPS61169 leaks ~25 mA through L3/D8 in shutdown on
// a 3.3 V rail; D-750).  If it opened on the PWM low phase the converter would
// be regulating into an open string, ramp SW to its 36-39 V overvoltage clamp
// and stress a 30 V AO3400A.  D-752 gives it its own hold network -- D14
// charges C85 from this net, R132 discharges it with nominal tau = 220 ms --
// so the gate follows the ENVELOPE of CTRL and Q11 cannot open until well after
// U17 has shut down.  The larger D-779 capacitor also means startup must not
// begin at a tiny PWM duty from a discharged gate: prime CTRL at 100 % long
// enough to charge Q11, then apply PWM.  Switching OFF still means holding this
// pin LOW; exact fade/hold timing is a first-article waveform measurement.
//
// kBacklightPwmHz stays inside TI's recommended 5-100 kHz window; below 5 kHz
// the internal low-pass no longer smooths the chopped reference and the output
// ripples audibly (SNVSA40B 6.3.5).
static const uint32_t kBacklightPwmHz = 5000;
static_assert(kBacklightPwmHz >= 5000 && kBacklightPwmHz <= 100000,
              "TPS61169 PWM dimming frequency must stay within TI's 5-100 kHz");

inline void backlightRamp(uint8_t channel = 0) {
  ledcSetup(channel, kBacklightPwmHz, 8);
  ledcAttachPin(AQROOT_PIN_DISP_BL_PWM, channel);
  // D-787 / Round-6: C85 is 1 uF. The executable ordering is shared
  // with a host behavioral test: first PWM command 255, >=3000 us prime, then
  // (and only then) dim PWM. Comments/dead code cannot satisfy that test.
  runBacklightRampPolicy(
      [channel](uint8_t duty) { ledcWrite(channel, duty); },
      [](uint32_t us) { delayMicroseconds(us); },
      [](uint32_t ms) { delay(ms); });
  ledcDetachPin(AQROOT_PIN_DISP_BL_PWM);
  pinMode(AQROOT_PIN_DISP_BL_PWM, OUTPUT);
  digitalWrite(AQROOT_PIN_DISP_BL_PWM, LOW);
}

}  // namespace aqroot
