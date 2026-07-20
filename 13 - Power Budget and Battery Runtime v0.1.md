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
| Standby (~5 mA) | ~340 hrs (~2 weeks) |
| UI browsing (~100 mA) | ~17 hrs |
| Sub-GHz scanning (~115 mA) | ~15 hrs |
| WiFi active (~160 mA) | ~11 hrs |
| Mixed real-world active use | ~12-15 hrs |
| Heavy continuous (~640 mA) | ~2.6 hrs (rarely sustained) |

## Conclusions
1. 2000 mAh gives ~10-17 hrs typical active use, ~2 weeks standby. Good for a handheld
   (competitive with / better than Flipper in active use). Confirms 2000 mAh is sound.
2. TPS63020 (2A) has huge headroom - even the ~640 mA worst burst is well within spec.
   Regulator choice validated by the numbers.
3. HIGHEST-VALUE power optimization = display backlight dimming + auto-timeout (backlight
   is the biggest continuous drain). Build into firmware from the start.
4. Power-gating idle radios saves ~30 mA baseline - confirms the power-gating strategy.
5. Deep sleep (~10-20 uA) enables very long standby with wake-on-motion (BMI270) or
   wake-on-button.
6. OPTION (settle at enclosure CAD): a 2500-3000 mAh cell would push active use to ~20+ hrs
   if the enclosure volume allows - a size-vs-runtime tradeoff.
