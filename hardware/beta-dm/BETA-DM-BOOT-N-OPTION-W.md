# Beta-DM — `BOOT_N` closed: Option W landed, and the exception it did not need

**Implementation record.** Beta-DM only. Full Beta (`hardware/beta/`) untouched.
Commits `f919953` (Option W) and `c83a7b6` (active-J5 residual sweep).

The headline: the ruling authorised a **new scoped 0.175 mm power-via clearance
exception** for the replacement `R2.1` `+3V3` escape. **It is not needed and was
not created.** With the P3V3 rules actually applied — the 0.40 mm outer-layer
width floor and a compliant 0.65 / 0.40 POWER via — and with `BOOT_N` routed
first, the re-join lands at the **ordinary 0.200 mm**. No new rule area, no DRU
change, no global change, nothing to hard-lock.

---

## 1. Starting state

| item | measured |
|---|---|
| HEAD | `7b4b7a2`, `origin/master...HEAD = 0 0` after the analysis push |
| DRC | 0 errors, 240 warnings, 223 unconnected |
| `hardware/beta/` vs `beta-full-reference-v1` | **empty diff** |
| backlight | complete, all six LED nets one island |
| global `LED_BOOST` clearance | 0.30 mm, unchanged |
| `BOOT_N` | 0 tracks, 3 islands |
| `/WAKE_INT_N` | **one island**, 15 seg, 4 via, 68.633 mm, five fitted pads |
| `E6_R2_1_CLR` / `_WIDTH` | present, unchanged |
| `D2`–`D7` | all DNP |
| `U10` (USBLC6-2SC6) | fitted |
| `J5` | fitted, 26 through-hole pads, all signal nets live |

## 2. The release, re-identified on the current board

Not taken on trust — re-derived and asserted against the expected counts:

| object set | segments | vias | length |
|---|---|---|---|
| `/WAKE_INT_N` | 15 | 4 | **68.633 mm** |
| R2-local `+3V3` escape | 18 | 1 | **5.528 mm** |
| **total removal UUIDs** | | | **38** |

Both count and length assertions passed. The released `+3V3` escape is the old
`E6_R2_1` copper: a 0.15 mm B.Cu neck plus a 0.40 mm F.Cu run and an 0.80 / 0.40
via, legal only because of the two `E6_R2_1` areas.

## 3. What was routed

| net | length | objects | layers | islands |
|---|---|---|---|---|
| `BOOT_N` | **52.445 mm** | 67 seg, 5 via | F 32 / B 24 / In2 11 | **1** — `U1.27`, `R2.2`, both `SW1.1` |
| `/WAKE_INT_N` re-land | **97.588 mm** | 178 seg, 4 via | F 68 / B 57 / In2 53 | **1** — `R3.1`, `R66.1`, `U1.23`, `U2.1`, `U3.1` all kept |
| `+3V3` `R2.1` re-join | **3.631 mm** | 13 seg, 1 via | B.Cu 2, F.Cu 11 | rail **1** island |

The `+3V3` escape leaves `R2.1` on B.Cu at 0.40 mm, takes a **0.65 / 0.40 POWER
via at (21.900, 37.400)** — annular ring 0.1250 mm, exactly the global floor —
and runs 0.40 mm F.Cu to the `x = 21.150` spine.

> **The via was originally landed at (21.850, 37.400) and that geometry was
> REJECTED on DFM.** It gave only a 0.075 mm solder-mask dam and overlapped the
> `R2.1` pad copper by 0.050 mm. It was replaced by a minimum four-object edit —
> three segments and the via — moving the via 0.050 mm east to
> **(21.900, 37.400)**, which gives a **0.125 mm mask dam** and **zero copper
> overlap** at the **ordinary 0.200 mm** clearance, with **no 0.175 mm exception
> used**. Escape length 3.531 → 3.631 mm. `BOOT_N` and `WAKE_INT_N` were not
> touched. Full audit:
> [BETA-DM-R2-POWER-VIA-DFM.md](BETA-DM-R2-POWER-VIA-DFM.md); fabrication
> consequences: [fab/BETA-DM-FABRICATION-NOTES.md](fab/BETA-DM-FABRICATION-NOTES.md).
>
> **Beta-DM solder mask is locked to GREEN for this fabrication build.** The
> 0.125 mm dam is accepted under that constraint. Full Beta and the Final-product
> colour decision are unaffected.

## 4. Why no exception was needed

The previous attempt failed because it routed the replacement escape with
**Default-class geometry**: 0.20 mm track and a 0.60 / 0.30 via. KiCad then
reported 10 `track_width` errors and 1 `hole_size` error, and the follow-up
analysis concluded that a compliant 0.65 / 0.40 via could only escape `R2.1`
if clearance dropped to 0.175 mm.

Re-measured with the compliant geometry actually in the router — 0.40 mm track,
0.325 mm via radius, 0.40 mm drill, hole rules never relaxed — and with `BOOT_N`
routed **first** so it takes its corridor before `+3V3` asks for one:

| clearance offered | result |
|---|---|
| **0.200 mm, the ordinary rule** | **routes: 3.531 mm, 13 seg, 1 via** |
| 0.175 mm local relaxation | never reached; the ordinary attempt succeeded |

Measured over all 268 new objects, the tightest separation on the whole board
is **0.2000 mm against a 0.200 mm limit**. Nothing is inside a measured-margin
exception.

### Leak probes

| probe | result |
|---|---|
| new `+3V3` copper enclosed by `E6_R2_1_CLR` (the 0.100 mm clearance area) | **0 items** — the exception is not used |
| `E6_R2_1_CLR` enclosed P3V3 items on the landed board | **0** — the area is now inert |
| `E6_R2_1_WIDTH` enclosed P3V3 items | 12, all of them **0.40 mm** copper that satisfies the *unrelaxed* 0.40 mm floor; the area lowers a floor the copper already clears |
| foreign-net inheritance | `BOOT_N` segments pass through both `E6_R2_1` areas but are netclass `Default`; every `E6_R2_1` rule is scoped `A.hasNetclass('P3V3')`, so nothing is inherited |
| `WAKE_INT_N` inheritance | netclass `Default`, no E6 area applies |
| global `+3V3` clearance | untouched |
| P3V3 outer-layer width | 0.40 mm on every new segment, PASS |
| POWER via | 0.65 / 0.40, annular 0.1250 mm ≥ 0.125 mm floor, PASS |

`E6_R2_1_CLR` and `E6_R2_1_WIDTH` were **left in place** rather than deleted:
removing a rule area is a DRU change the ruling did not authorise, and both are
now provably inert. They are candidates for retirement at DM closeout.

## 5. Gate results

| gate | result |
|---|---|
| KiCad DRC, zones refilled | **0 errors**; 240 warnings, identical to baseline |
| exact analytic measurement, per-object geometry | **PASS, 0 violations**, tightest 0.2000 mm |
| RF band rules (915 / 433) | PASS — no B.Cu in band, no in-band via, no In2 outside an E5 corridor |
| `BOOT_N` one island | **YES** |
| `WAKE_INT_N` one island, all five fitted pads | **YES** |
| `+3V3` one island | **YES** |
| I2S / internal I²C / SPI-A / SPI-B / USB / backlight / `BTN_RIGHT_N` | unchanged |
| preservation diff | 188 footprints, 776 pad keys, 44 zone definitions, Edge.Cuts **identical**; 0 objects modified in place; removals exactly the 38 released |

## 6. J5 kept active — residual sweep

With the expansion pins active, every fitted J5 signal path is must-work. The
whole fitted must-work non-GND set was re-audited on the post-Option-W board and
everything routable under the current locks was routed:

| net | what closed | geometry |
|---|---|---|
| `XGPIO6_HDR` | `R57.1` → the `J5.10` island | 1.613 mm, 5 seg, F.Cu, **one island** |
| `Net-(SW9-A)` | `SW9.1` ↔ `U12.12` ↔ `R43.1` | 89.399 mm, 76 seg, 6 via |
| `ACC_3V3_SW` | one join | 2.504 mm, 2 seg, B.Cu at the P3V3 0.40 mm floor |

`ACC_3V3_SW` resolves to **P3V3**, so it carries the 0.40 mm outer-layer floor.
A first pass routed it at 0.20 mm, KiCad returned four `track_width` errors, and
that copper was **discarded and re-routed**, not kept.

Unconnected **220 → 216**.

## 7. What remains, and why it is not routable

31 fitted must-work lines remain. Every one was tested by flooding the whole
board free region from each endpoint on all three routing layers with via
transitions honoured. **None is blocked by a rule or by a lock — all are blocked
by congestion**, and per the ruling that means STOP rather than expand.

| group | lines | evidence |
|---|---|---|
| `XGPIO0`…`XGPIO13`, `U3` ↔ series resistor | 14 | `U3` pads reach 181-cell pockets sized 186–1330; the `R5x` pads reach separate 267–305-cell pockets sized 488–5.2 M. **No pair shares a free region.** |
| `ACC_PWR_EN` `U3.20`↔`U16.5`↔`U15.3`↔`R17.1` | 3 | four pockets: 282, 1546, 8221, 2855 cells — disjoint |
| `ACC_3V3_SW` remainder | 3 | `R46.2` 1060, `C38.1` 3205, `U15.6` 4323 — disjoint from the joined pair |
| `I2C_SCL_EXT_HDR`, `I2C_SDA_EXT_HDR`, `XGPIO13_HDR` | 3 | resistor pad 3157 / 3337 / 5782 cells vs the J5-side island 21164 / 14926 / 4328 — disjoint |
| `BQ25185_STAT1` / `STAT2`, `TEST_GPIO45` / `46` | 4 | `U11.9` reaches **0** free cells, `U11.3` reaches 1; `U1.26` 2468 vs `TP1.1` 5.2 M |
| `Net-(U15-QOD)`, `Net-(U16-SCLB)`, `Net-(U16-SDAB)` | 3 | 2125–6056-cell pockets, disjoint |
| `Net-(SW9-A)` `TP13.1` | 1 | 1016-cell pocket |

Of the 31, **23 are J5-active** and 8 are not.

## 8. Ledger

| bucket | lines |
|---|---|
| A — intentional DM deferral (DNP function) | **55** — NFC 22, ESD/DNP part at one end 20, IR 8, speaker 5 |
| B — GND, pours pending | **130** |
| C — fitted must-work, still open | **31** |
| **total** | **216** |

`216 == 55 + 130 + 31`. Nothing is unexplained.

## 9. Pours

**HELD.** §14 of the ruling permits pours only when the fitted must-work non-GND
residual is zero. It is 31. Pours are not started, and no further hard-lock
ruling is taken in this pass.

## 10. Hard locks created by this pass

Per §10 of the ruling, the following are now **HARD-LOCKED** and must not be
reopened during DM closeout:

| locked object | what it is | UUID prefix |
|---|---|---|
| `BOOT_N` | 67 segments, 5 vias, 52.445 mm, one island | `a5e10000` |
| `/WAKE_INT_N` replacement | 178 segments, 4 vias, 97.588 mm, one island | `a5e10000` |
| R2-local `+3V3` re-join | 13 segments, 1 POWER via at **(21.900, 37.400)**, 3.631 mm | `a5e10000` + `f2b40000` |

There is **no rule exception to lock**: the escape stands on the ordinary
0.200 mm clearance, the 0.40 mm P3V3 outer-layer floor and the 0.65 / 0.40
POWER via. The `0.175 mm` figure the ruling authorised was never used.

`E6_R2_1_CLR` and `E6_R2_1_WIDTH` remain in the DRU but are inert — see §4.
Retiring them is a documentation task for closeout, not a lock.

The released copper — the old `/WAKE_INT_N` route and the old `E6_R2_1` `+3V3`
escape — is recorded object by object in `reports/w_release.json` of the
implementation pass and in commit `f919953`, so it is restorable for Final.

## 11. Preservation

| | |
|---|---|
| `hardware/beta/` vs `beta-full-reference-v1` | **empty diff** |
| footprints / pads / zones / Edge.Cuts / mounting holes | identical, object-level diff |
| backlight, I2S, internal I²C, SPI-A, SPI-B, USB data, RF keepouts | unchanged |
| objects modified in place | **0** |
| DRU | unchanged — no rule added, removed or edited |
| schematics | unchanged |
