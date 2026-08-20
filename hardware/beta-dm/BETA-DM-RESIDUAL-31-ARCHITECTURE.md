# Beta-DM — residual-31 architecture study, phase 1

**ANALYSIS ONLY. No real-board copper was written; the PCB and the DRU are
byte-identical to `6ea9e2b`.** No pours, no component moves, no DNP decisions.

**Result: FAIL — blocked on a hard lock.** No architecture exists that closes
the residual set using only ordinary, non-locked copper. The minimum conflict is
**two `/SX1262_RXEN` B.Cu segments, 12.825 mm**, and per §2 of the ruling this
study stops rather than taking that lock.

---

## 1. Starting state, verified

| item | measured |
|---|---|
| HEAD | `6ea9e2b` |
| `origin/master...HEAD` | `0 0` |
| `git status` | clean (one pre-existing untracked dir) |
| KiCad DRC | **0 errors**, 240 warnings, **216 unconnected** |
| ledger | **216 = A 55 + B 130 + C 31** |
| `hardware/beta/` vs `beta-full-reference-v1` | **empty diff** |

## 2. Residual set, re-derived from the board

**31 lines = 23 J5-active + 8 non-J5**, matching the expected grouping exactly.

| group | lines | content |
|---|---|---|
| **J1** | 14 | `XGPIO0`…`XGPIO13`, `U3` pad ↔ series resistor |
| **J2** | 3 | `ACC_3V3_SW` |
| **J3** | 3 | `ACC_PWR_EN` |
| **J4** | 3 | `I2C_SCL_EXT_HDR`, `I2C_SDA_EXT_HDR`, `XGPIO13_HDR` |
| **P** | 8 | `BQ25185_STAT1`/`STAT2`, `TEST_GPIO45`/`46`, `Net-(U15-QOD)`, `Net-(U16-SCLB)`, `Net-(U16-SDAB)`, `Net-(SW9-A)` `TP13` |

## 3. Measured congestion regions

Single-link clustering at 8 mm on endpoint midpoints. **The measured regions
differ from the assumed ones and the measured grouping is used.**

| region | lines | bbox | content |
|---|---|---|---|
| **1 — header cluster** | **26** (23 J5-active) | x 25.4…44.4, y 9.8…14.5 | all of J1–J4 **plus** `Net-(U15-QOD)`, `Net-(U16-SCLB)`, `Net-(U16-SDAB)` |
| **2 — battery status** | 2 | x 62.2…65.3, y 75.5…75.8 | `BQ25185_STAT1`/`STAT2` |
| **3 — MCU test points** | 2 | x 20.0…21.7, y 39.1…45.5 | `TEST_GPIO45`/`46` |
| **4 — hard-off switch** | 1 | (6.9, 55.0) | `Net-(SW9-A)` `TP13` |

The three `U15`/`U16` lines assumed to sit in a separate power region are
physically inside the header cluster. Region 1 owns **26 of the 31**.

## 4. Cut analysis — who owns the walls

Each endpoint's free region was flooded on all three routing layers with via
transitions honoured, the one-cell boundary ring taken, and every nearby object
stamped against the ring so the wall is attributed to its **owner**.

### Region 1, `U3` side

| endpoint set | pocket | wall owners (ring cells) |
|---|---|---|
| `U3.4`…`U3.11` (north row) | **1 337** cells each | `PAD U3` 270–276, **`SX1262_RXEN` 169**, `CC1101_GDO0` 62, `PAD U1` 29–35, `WAKE_INT_N` 6 |
| `U3.14`…`U3.18` (south row) | **192** cells each | `PAD U3` 64, **`SX1262_RXEN` 6** |
| `U3.20` (`ACC_PWR_EN`) | 311 cells | `PAD U3` 86, `I2C_SCL_INT` 26, `+3V3` 20, `SX1262_RXEN` 8 |

`U3` is a TSSOP-24 on 0.65 mm pitch: its own pads are the dominant wall, and
`/SX1262_RXEN` — which **originates at `U3.19`**, it is not a trace passing
through — boxes the package in on B.Cu with two jumpers, one on each side.

### Region 1, resistor-bank side

`R51`…`R64` pads reach 488–6 224-cell pockets whose walls are dominated by the
**resistor pads themselves** (`PAD R58` 185, `PAD R60` 184, `PAD R64` 170,
`PAD R62` 155 …) plus the existing `*_HDR` escapes. Pads cannot be released
without a component move, which is forbidden.

### Regions 2–4 — a different failure mode

All eight non-J5 lines have **one endpoint that reaches the open board** and one
trapped in a local pad-escape pocket. They are pad-escape problems, not corridor
problems:

| line | trapped endpoint | pocket | wall owners |
|---|---|---|---|
| `BQ25185_STAT1` | `U11.9` | **zero free cells at the pad** | pad-level escape failure |
| `BQ25185_STAT2` | `U11.3` | **1** cell | `PAD U11` 3, `BAT_PROTECTED_P` 2 |
| `TEST_GPIO45` | `U1.26` | 2 468 | `PAD U1` 80, `DISP_BL_CTL` 68, `I2S_MIC_DIN` via 53, `BTN_HOME_N` 51, `SD_CS_N` 34 |
| `TEST_GPIO46` | `U1.16` | 460 204 | **`WAKE_INT_N` 1 092**, `PAD U1` 1 000, `CC1101_GDO0` 775, `+3V3` 736, internal I²C 588/559 |
| `Net-(SW9-A)` | `TP13.1` | 1 016 | `BTN_A_N` 50, `BTN_DOWN_N` 44, `+3V3` via 22, `BTN_B_N` via 16 |

Their walls are also made of preserve-list nets — `WAKE_INT_N` (a hard lock),
the button nets, SPI-A `SD_CS_N`, `I2S_MIC_DIN`, display `DISP_BL_CTL`.

## 5. Escalation ladder — the decisive evidence

Release candidates were taken in strict §8 priority order, cheapest first. The
question asked at each rung is how many of the 22 residual nets have their
endpoints in one free region.

| rung | released | objects | length | reachable |
|---|---|---|---|---|
| 0 | nothing | 0 | 0 mm | **0 / 22** |
| 1 | **all** header-cluster ordinary copper (18 `*_HDR` / `ACC_3V3_SW` nets) | 266 seg, 28 via | 305.671 mm | **9 / 22** |
| 2 | + all ordinary local signals (`Net-(U15-CT)`, `BMI270_INT1_STRAP`, `DISP_CS_N`, `Net-(U1-EN)`, `FAST_IO_U0TXD_ROOTPROBE_CS`) | 344 seg, 34 via | 472.879 mm | **9 / 22** |
| 2d | + the local `+3V3` **and** the local `GND` | 440 seg, 46 via | **626.070 mm** | **9 / 22** |
| **R** | + **two** `/SX1262_RXEN` B.Cu segments | 346 seg, 34 via | 485.704 mm | **22 / 22** |

**Releasing every ordinary, non-locked, non-RF object in the header region — 440
objects and 626 mm of copper — opens 9 of 22 and not one more.** Adding
12.825 mm of `/SX1262_RXEN` opens all 22.

Isolation runs confirm both halves are necessary: `SX1262_RXEN` + `CC1101_GDO0`
released with the header copper **kept** gives only 6 / 22, and released alone
gives 2 / 22.

## 6. The minimum hard-lock conflict — exactly two objects

1-minimised against the 22 targets:

| uuid | net | layer | from | to | length | why required |
|---|---|---|---|---|---|---|
| `f4200001-5e60-4b8c-9d03-c10000000001` | `/SX1262_RXEN` | B.Cu | (22.325, 10.600) | (17.500, 10.600) | **4.825 mm** | crosses `U3`'s **south-row** escape corridor; restoring it drops 22 → 14 |
| `f4200003-5e60-4b8c-9d03-c10000000003` | `/SX1262_RXEN` | B.Cu | (17.500, 13.500) | (25.500, 13.500) | **8.000 mm** | crosses `U3`'s **north-row** escape corridor; restoring it drops 22 → 11 |
| | | | | **total** | **12.825 mm** | |

Everything else on `/SX1262_RXEN` is untouched: the other 16 segments, all
4 vias, and the **entire In2 E5-corridor crossing to `U8`** are not involved.
The conflict is only with two local B.Cu jumpers around `U3`, and the net's
source is `U3.19` itself.

## 7. Is the ask even sufficient? — necessary conditions met, sufficiency NOT proven

| test | result |
|---|---|
| reachability at rung R | **22 / 22** |
| corridor capacity at the tightest cut (x = 28, y 8.6…17.5) | **18 track slots** (F.Cu 4, In2 6, B.Cu 8) against a demand of ~14–17 — **capacity is not the wall** |
| one sequential solve at rung R | **jammed** — 4 of 14 `XGPIO` closed, routes ballooning to 30–50 mm |

Sequential routing is not evidence, exactly as §9 says. Proving the architecture
would need a negotiated-congestion program over ~40 nets. **That program was not
run, because the architecture it would prove depends on a lock this study is
instructed not to take.** Reachability and capacity are necessary conditions and
both are met; simultaneous routability remains **unproven**.

## 8. A model defect found and fixed during this study

`route.Grid.build` stamped `min_hole_clearance` around **every** drilled pad,
including the pad of the net being routed. KiCad exempts same-net items from
clearance, so this made every through-hole J5 pin read as unreachable to its own
net. Fixed: own-net through-hole pads no longer block their own net.

Effect on this study: rung 1 moved from 6/22 to 9/22, and the three "stragglers"
(`I2C_SCL_EXT_HDR`, `I2C_SDA_EXT_HDR`, `XGPIO13_HDR`) were shown to be sealed on
the **J5 side only as a modelling artifact** — their resistor-side pads reach the
open board.

**Effect on anything already landed: none.** Re-tested with the fix, the current
board with nothing released still gives **0 / 22**, so the previous pass's
finding that all 31 are congestion-sealed stands, and no landed copper or ledger
entry changes.

## 9. Preservation

PCB and DRU **byte-identical** to `6ea9e2b`. `hardware/beta/` empty diff against
`beta-full-reference-v1`. `BOOT_N`, `WAKE_INT_N`, the R2 candidate-B escape,
I2S, internal I²C, SPI-A, SPI-B, USB, RF, backlight, buttons, Edge.Cuts and the
mounting holes all untouched. No pours.

## 10. What a ruling would have to authorise

If the CTO wishes to proceed, the ask is:

* release `/SX1262_RXEN` segments `f4200001…` and `f4200003…` (**12.825 mm**,
  B.Cu, local to `U3`) and re-land that connection — `SX1262_RXEN` runs from
  `U3.19` to `R74.1`/`U8.6`, so the re-land is local and the E5 crossing is
  untouched;
* release the header-cluster ordinary copper: **266 segments, 28 vias,
  305.671 mm** across 18 `*_HDR`/`ACC_3V3_SW` nets, plus optionally the five
  ordinary local signal nets (a further 78 segments, 6 vias, 167.208 mm);
* re-derive all of it, plus the 23 J5-active joins, as one negotiated-congestion
  problem — an estimated 380–450 new segments and 30–40 vias;
* `ACC_3V3_SW` is netclass **P3V3** and must be re-derived at 0.40 mm outer
  width with a 0.65 / 0.40 POWER via, and any via landing under a fitted body
  needs the R2-style DFM audit (mask dam ≥ 0.125 mm).

The eight non-J5 residuals are a **separate** programme: they are pad-escape
pockets, several of them walled by `WAKE_INT_N`, the button nets, SPI-A and
I2S — and `BQ25185_STAT1`'s `U11.9` has **zero** free cells at the pad, which
may be a closed-form impossibility rather than a congestion problem.
