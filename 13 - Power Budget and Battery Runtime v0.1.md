---
tags: [hardware, beta, power, battery]
status: analysis
---

# AQROOT Power Budget & Battery Runtime v0.1

Per-usage-mode power analysis (runtime depends on how the device is used, not just
component maxes). Figures at the 3.3V rail, typical/conservative datasheet-class numbers.

## Usage-mode current draw
| Mode | Description | Avg draw |
|---|---|---|
| Idle / standby | screen off, radios off, light sleep, wake-on-button | ~5 mA |
| UI browsing | screen ON, navigating menus, no radio | ~100 mA |
| Sub-GHz scanning | screen + CC1101 RX | ~115 mA |
| WiFi active | screen + WiFi (spikes to ~400+ on TX) | ~160 mA |
| LoRa TX session | screen + SX1262 (bursty TX, low duty) | ~110-130 mA |
| Heavy burst | WiFi TX + SD write + audio (momentary) | ~640 mA peak |

Biggest continuous draw in normal use = the display BACKLIGHT (~60 mA of the ~100 mA
browsing draw).

## Battery runtime (2000 mAh LiPo, ~85% usable = ~1700 mAh effective)
| Mode | Runtime |
|---|---|
| Standby (~5 mA) | ~340 hrs (~2 weeks) — **ESTIMATED, pending Beta measurement** |
| UI browsing (~100 mA) | ~17 hrs |
| Sub-GHz scanning (~115 mA) | ~15 hrs |
| WiFi active (~160 mA) | ~11 hrs |
| Mixed real-world active use | ~12-15 hrs |
| Heavy continuous (~640 mA) | ~2.6 hrs (rarely sustained) |

## Conclusions
1. 2000 mAh gives ~10-17 hrs typical active use, ~2 weeks standby *(standby ESTIMATED — see
   the caveat section below)*. Good for a handheld
   (competitive with / better than Flipper in active use). Confirms 2000 mAh is sound.
2. TPS63020 (2A) has huge headroom - even the ~640 mA worst burst is well within spec.
   Regulator choice validated by the numbers.
3. HIGHEST-VALUE power optimization = display backlight dimming + auto-timeout (backlight
   is the biggest continuous drain). Build into firmware from the start.
4. Power-gating idle radios saves ~30 mA baseline - confirms the power-gating strategy.
5. Deep sleep (~10-20 uA) enables very long standby with wake-on-motion (BMI270) or
   wake-on-button. **ESTIMATED — PENDING BETA MEASUREMENT (see the caveat below).**
6. OPTION (settle at enclosure CAD): a 2500-3000 mAh cell would push active use to ~20+ hrs
   if the enclosure volume allows - a size-vs-runtime tradeoff.

---

## ⚠ Deep-sleep / standby figures are ESTIMATED — PENDING BETA MEASUREMENT

**The ~10-20 uA deep-sleep figure and the ~2-week / ~340 hr standby number derived from it are
NOT measured. They are estimates, and the ~10-20 uA part is an ESP32-S3 *chip* deep-sleep
figure, not a system figure.** The real number will be higher — plausibly by an order of
magnitude — because the whole board draws current in standby, not just the MCU.

**The true system standby current must be summed from every contributor, not assumed:**

| Contributor | Why it matters in standby |
|---|---|
| **Reverse-polarity protection controller (~80 µA, if LTC4368-1 is locked)** | **Always-on, in the battery path, and not power-gateable** — it must keep working precisely when everything else is asleep. At ~80 µA it is comparable to the whole ESP32-S3 chip deep-sleep figure (~10–20 µA) and could dominate it several times over. **Topology is PARKED and the part is NOT locked** (see [[05 - Design Decisions Log]]), so treat this as a budget line to close, not a number to publish. Standby-current impact is open question **(f)** assigned to the power/DFM review. |
| ESP32-S3 deep sleep | the ~10-20 uA that is currently standing in for the whole system |
| **TPS63020 quiescent** | ~25 uA in power-save — already comparable to the entire ESP32 figure. **The block is architecture-locked (2026-07-30) with PS/SYNC tied to GND via `R_PS_DEFAULT` 0R, so power-save is the DEFAULT and this ~25 uA figure is the one that applies in standby.** Forced-PWM is a bring-up/EMI test option only and would raise this substantially — do not leave it strapped. EN is driven by the **physical hard-off switch**: with the switch OFF the `+3V3` rail is disabled, but **total battery standby is NOT zero** — bq25185, MAX17048 and the reverse-protection controller candidate stay powered upstream. See [[05 - Design Decisions Log]] |
| **Both TCA9535PWR expanders** (U60 @ 0x20 + U61 @ 0x21) | two expanders, powered and retaining state, low-uA each per datasheet but **unmeasured — this part has never been on the bench** |
| **MAX17048 fuel gauge** | runs continuously by design — that is its job |
| **All pull-ups** | 7 button pull-ups + the `WAKE_INT_N` pull-up + I2C pair + every safe-state pull on the expander enables. Each one is a static path whenever its net is pulled to the opposite rail. **The TCA9535 has no internal pull-ups, so all of these are external resistors and none can be disabled in firmware to save standby current** |
| **Load-switch leakage** | NFC 5V boost enable, accessory rail (ACC_PWR_EN), any other gating |
| **Charger / power-path (bq25185)** | battery-side quiescent + power-path leakage |
| **Display leakage** | panel + backlight driver in the off state |
| **IMU wake-mode current** | BMI270 in low-power motion-detect is NOT free — it is the cost of wake-on-motion |

Note two of these are structural consequences of decisions already locked: the second expander
(U61, community header) and the expander safe-state pull resistors both exist for good reasons,
and both add standby current. That is a fair trade, but it has to be counted. **The 2026-07-27
move to the TCA9535PWR makes the pull-resistor contribution slightly worse and wholly
non-negotiable** — that part has no internal pull-ups, so every pull is an external static path
that firmware cannot switch off before sleeping.

**DO NOT PUBLISH THE STANDBY NUMBER IN MARKETING UNTIL IT IS MEASURED ON BETA HARDWARE.** A
"2-week standby" claim on a Kickstarter page is a promise; if the measured figure comes in at
100-200 uA the real answer could be days rather than weeks. Measure first, claim second — this
is the same rule already applied to demoing only features that actually work
([[06 - BOM and Cost Tracker]], prototype-to-production strategy).

**Beta bring-up action:** measure true system standby current at the battery, in the final
enclosure, with firmware in deep sleep and wake sources armed. Then revise this document and
only then decide what standby figure is safe to advertise.
