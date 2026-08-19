# AQROOT Beta DM — residual routing blockers, returned for ruling

This pass stopped short of completing the residual program **on purpose**. Per
the standing process rule, work that would cross a hard lock is returned with
evidence instead of landed. Everything in this file is measured on the board at
the GND-stitching commit, at the enforced 0.20 mm clearance (0.30 mm where an
elevated netclass applies), with no rule relaxed.

## Summary

| item | lines | status |
|---|---|---|
| `BOOT_N` | 3 | **SOLVABLE — ruling required.** Two complete solutions proven end to end, neither touching a hard lock. See [BETA-DM-R2-MICROMOVE-STUDY.md](BETA-DM-R2-MICROMOVE-STUDY.md) |
| J5/F4 header interconnect | 26 | **BLOCKED by congestion inside the hard-locked header region.** Was 41; the 15 ESD-array links moved to the intentional-deferral bucket when `D2`–`D7` became DNP |
| display backlight string | 5 | **completes at a 0.25 mm scoped exception**, 4 of 6 at the enforced 0.30 mm. See [BETA-DM-BACKLIGHT-ANALYSIS.md](BETA-DM-BACKLIGHT-ANALYSIS.md) |
| charger status, MCU test points, `SW9-A`, `U15-QOD` | 14 | blocked; local congestion |
| **total must-work non-GND still open** | **48** | |

Nothing here is a defect in the copper already landed. Every one of these is a
route that does not exist at the current geometry.

---

## 1. `BOOT_N` — SUPERSEDED, and solvable

`BOOT_N` is mandatory programming and recovery access: `U1.27` (IO0) ↔ `R2.2`
(10 k pull-up) ↔ `SW1.1` (BOOT button). It still has **zero copper**.

**The analysis below this heading in earlier revisions was wrong and has been
replaced.** It measured escape sites inside one reserved via window, which made
the problem look like a two-lock conflict between `I2S_LRCLK` and either
`SD_CS_N` or the `+3V3` `R2.1` escape. Measuring the whole reachable region
instead shows that `U1.27` sits in a sealed 9 728-cell pocket, that **nine
different single-object releases each open it**, and that **`I2S_LRCLK` is not
required at all**.

The ratified `R2` micro-move was studied in full and **does not solve it**:
278 legal `R2` positions exist within a 1.285 mm displacement, 72 of them
connect `U1.27` to `R2.2`, and none escapes the pocket. Per the standing
instruction, nothing was landed and the two-lock fallback was not activated.

Two complete solutions are proven end to end, neither touching a hard lock —
`WAKE_INT_N` (recommended) and `CC1101_GDO0` — plus a third, `BTN_RIGHT_N`
alone, whose `BOOT_N` route is proven but whose re-land is not.

**Full evidence, candidate tables and the ruling request:
[BETA-DM-R2-MICROMOVE-STUDY.md](BETA-DM-R2-MICROMOVE-STUDY.md).**

---

## 2. J5 / F4 header interconnect — 26 lines, blocked by congestion

The header cluster (x 30–52, y 9–14) holds two rows of series resistors between
`U3`/`U15`/`U16` and the `D3`–`D7` ESD diodes, all inside the hard-locked
J5/F4 region and the `HEADER RESERVED` rule area.

Attempted all 37 header-cluster nets on a focused grid. **3 routed**
(`WAKE_ATTN_N_HDR`, `XGPIO2_HDR`, `XGPIO3_HDR`); **34 failed**.

The systematic pattern, from geometric island analysis: on every header net the
**series resistor and the J5 pin are already connected**, and the **ESD diode
pin is a separate island**. The entire J5 ESD protection network is unrouted —
14 `XGPIO*`, `WAKE_ATTN_N`, `FAST_IO_GPIO43` and both external-I2C lines.
`ACC_3V3_SW` is in **8 islands** and is effectively unrouted as a rail.

Reachability measured for `FAST_IO_GPIO43_HDR`: the J5-side island reaches only
21 977 cells bounded to x 14.85–31.85, y 3.75–14.85 — it cannot get out to
where the diode roams. The region is saturated.

The three routable nets were **deliberately not landed**: landing 3 of 37 would
consume space the remaining 34 need and make a proper header program harder.

**This needs a dedicated header-completion program, not opportunistic routing.**
**That ruling has since been given and implemented**: `D2`–`D7` are now DNP on
the Demo Model (commit `4ea1588`). Their 15 signal links moved out of this
bucket into the intentional-deferral ledger, which is why this section is 26
lines rather than 41. What remains here is the header interconnect proper —
`XGPIO*` series-resistor links, `ACC_3V3_SW`, `ACC_PWR_EN`, the buffered
external I2C and `U15-QOD` — and it still needs a dedicated program.

---

## 3. Display backlight — SUPERSEDED, and solvable

`LED_A1`…`LED_A4` and `LED_K` carry the `LED_BOOST` netclass, which the DRU
gives an elevated 0.30 mm routed clearance on the stated premise that the
backlight string runs above 20 V.

**That premise does not match the circuit**, and the earlier claim that three of
five nets were geometrically blocked was an artifact of routing order. Measured
individually, every backlight net has a fully connected free region at
0.30 mm; the failures are mutual congestion in a ~2 mm corridor. Order alone
takes the result from 2 of 6 to 4 of 6, and the whole string completes at a
**0.25 mm** clearance in 53 segments and 5 vias.

**Full analysis — operating voltage, fault voltage, `J1` geometry, the two
proposed scoped areas, leak probes, IPC-2221 and JLCPCB comparisons:
[BETA-DM-BACKLIGHT-ANALYSIS.md](BETA-DM-BACKLIGHT-ANALYSIS.md).** Nothing was
landed and no rule was changed.

---

## 4. Remaining power / control — 14 lines

| net | lines | why open |
|---|---|---|
| `Net-(SW9-A)` | 4 | hard-off switch → `U12.EN`, `R43`, `TP13`. Islands 1/2 unroutable |
| `/ACC_PWR_EN` | 3 | `R17`/`U15.3`/`U16.5`/`U3.20` — inside the saturated header cluster |
| `Net-(U15-QOD)` | 1 | `R46.1` ↔ `U15.5`, header cluster |
| `Net-(U16-SCLB)` / `SDAB` | 2 | buffered external I2C, header cluster |
| `/01_POWER_TREE/BQ25185_STAT1` / `STAT2` | 2 | `U11` WSON-10 0.4 mm pitch → `TP6`/`TP7` |
| `/02_MCU_CORE/TEST_GPIO45` / `46` | 2 | `U1` → `TP1`/`TP2` |

`SW9-A` is the physical power switch and is the most functionally important of
these. The rest are status and test-point nets.

Note on the fine-pitch packages: the DRU's "pad-escape necking" rules set
`track_width min 0.20` and `clearance min 0.20` inside the `U11`/`U12`/`U13`/
`U14`/`U17`/`U9` courtyards. They **confirm** 0.20/0.20 rather than relaxing
below it, so there is no unused headroom there — the model already routes at the
allowed minimum.

---

## 5. What this means for pours

Pours are explicitly last, and only after `BOOT_N` is complete. `BOOT_N` is
still unrouted pending the ruling, and pours are separately **HELD** by the
pass-4 directive, so **pours were not created**. That is also the right
engineering call: pouring now would have to be undone by whichever remedy the
`BOOT_N` ruling selects, and by the header program.

The GND stitching that does not depend on any of this — both radios and the
microphone — **was** completed and landed.
