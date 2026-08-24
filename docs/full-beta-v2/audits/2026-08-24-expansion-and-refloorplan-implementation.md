# FBV2-EXP-002 — Standard expansion interface and combined re-floorplan

**Date:** 2026-08-24 · **Task:** FBV2-EXP-002 — implementation
**Repository HEAD at start:** `7515d57` (FBV2-EXP-001 audit)
**Result: FBV2-P1 RE-ISSUED = PASS. FBV2-P2 ENTRY = PASS. PM-1, PM-2, PM-3 and PT-1 CLOSED.**
**Overall Full Beta v2 stays 74 %** — P1 was re-earned, not newly earned, and P2 entry earns none.

> **ZERO SIGNAL ROUTING.** 0 tracks, 0 signal vias, 0 electrical copper pours.

---

## 1. Battery procurement gate — PASS, and it gated everything else

The 57 × 75 × 8 mm envelope was checked against real, purchasable 1S pouch cells **before** any
authoritative file was touched, because a fail here would have stopped the task.

| # | cell | dimensions (T × W × L) | capacity | protection / leads | evidence |
|---|---|---|---|---|---|
| **1** | **PKCELL `LP785060`** (Adafruit 328) | **7.3 × 50 × 60 mm** | **2500 mAh typ / 2375 mAh min**, 3.7 V | **PCM fitted**, cuts out ≈ 2.8 V, short-circuit protected; ships with a genuine **2-pin JST-PH** | manufacturer datasheet `LP785060 2500mAh 3.7V 20190510` — nominal 2500 mAh typ, charge cut-off 4.2 V, discharge cut-off 3.0 V, standard charge 1500 mA, 500 cycles |
| **2** | **`LP755070`** (li-polymer-battery.com, EEMB-class) | **7.5 × 50 × 70 mm** | **3000 mAh min / 3050 mAh typ**, 3.7 V | **PCM fitted**, overcharge 4.275 V ± 50 mV, overdischarge with 2.50 V resume; AWG26 UL1007 flying leads | manufacturer datasheet `LP755070-Datasheet.pdf` — 60 g, 2.75–4.20 V, 1500 mA charge, 3000 mA discharge, 500 cycles to 80 %, 0–45 °C charge |

Both fit **inside** the new envelope with room on every axis, both are **1S with protection
already fitted**, and both use the JST-PH lead arrangement `J4` already expects. Neither is a
marketplace mystery cell: both are manufacturer datasheets for catalogued part numbers.

> **The capacity penalty is smaller than the geometric estimate, and it is honest to say so.**
> The EXP-001 prediction was ≈ −5 % from volume scaling. The real answer is that the **57 mm limit
> does not bind either candidate** — `LP755070` is 50 mm wide and delivers **3000 mAh**, which is
> **more** than the 2500–3000 mAh the 60 mm envelope was targeting (D-071). The envelope was
> always larger than the cells that fill it. **Recorded capacity target: 2500–3000 mAh, unchanged.**

**GATE: PASS.** The task continued.

---

## 2. What was built

| change | detail |
|---|---|
| **Expansion connector** | `J5` **Samtec `BCS-112-S-D-HE` 2 × 12 → `SSQ-124-02-G-S-RA` 1 × 24**, 2.54 mm, female, right-angle, single row. New project footprint, drawn from the Samtec SSW/SSQ datasheet and the Sullins 1-row RA recommended layout |
| **Pin order** | **ORDER-B**, superseding EXP-001's ORDER-A |
| **Qwiic / STEMMA QT** | `J8` **`JST SM04B-SRSS-TB`**, new, on the protected external I²C node |
| **PCB outline** | **70.0 → 72.0 mm**, symmetric. Height unchanged at 148.0 |
| **Battery** | **60 → 57 mm wide** (75 × 8.0 unchanged) |
| **`BOOT`** | right wall → **bottom band, doc (28.300, 6.000)**, front face |
| **`POWER`** | **stays on the right wall**, doc (66.700, 61.500) |
| **PM-1** | all four converter cells rebuilt |
| **PM-2** | the whole 1.5 A protection chain rebuilt as one column |
| **PM-3** | NFC front end rebuilt as an exact mirror pair |
| **PT-1** | `U11` moved out of the battery shadow |

**No protection was removed.** Every GPIO series resistor, the 22 Ω I²C pair, the 330 Ω WAKE
resistor, all four TVS arrays, `U16` TCA4307, both `TPS22950C` load switches, the `TPS61023` boost,
the FLT wire-OR, the `Q10` WAKE isolation gate and the `ACC_DETECT_N` protection are all present and
electrically identical. **The schematic change is a footprint swap plus a pin re-map on sheet 09,
plus one 4-pin symbol whose pins land on four nets that already existed.**

---

## 3. The datum, and why the board grew symmetrically

The board grew **1.0 mm on each side**, not 2.0 mm on the right. Every part therefore shifted
**+1.0 mm in X**, which means **every part-to-part relationship on the board is unchanged** and
only the two edge margins moved — each gaining 1.0 mm.

| item | before | after |
|---|---|---|
| Board | 70.000 × 148.000 | **72.000 × 148.000** |
| Cavity | 75.0 × 155.0 | unchanged |
| Board edge → cavity wall | 2.5 mm | **1.5 mm both sides** — the ≥ 1.5 mm rule met **exactly**, with nothing to spare |
| `X_cavity` | `X_doc + 2.5` | **`X_doc + 1.5`** |
| Enclosure | 80 × 160 × 23 | **unchanged** |

**`ANT433_REGION` had to be re-derived, not shifted.** The old reservation was
X −2.40 … −0.20 — 2.2 mm wide — which does not fit inside a 1.5 mm wall gap. That 2.2 mm never
described anything real: the flex is **0.28 mm thick** and is bonded flat to the wall, so it
projects inward only by its thickness plus adhesive. The region is now **X −1.40 … −0.60**, taken
from the part, and there is still **0.6 mm of air** between the flex face and the board edge.

---

## 4. Right-wall stack — measured

| element | doc position | courtyard | gap to the next |
|---|---|---|---|
| **`J5` 1 × 24** | (65.900, 108.790) rot 270 | X 64.95 … 72.97, **Y 77.51 … 140.07** | — |
| **`J8` Qwiic** | (68.400, 71.600) rot 90 | X 65.08 … 71.72, Y 67.66 … 75.55 | **1.97 mm** below `J5` |
| **`SW9` POWER** | (66.700, 61.500) rot 90 | X 62.16 … 71.00, Y 56.45 … 66.55 | **1.11 mm** below `J8` |
| `SW2` UP button | unchanged | Y 45.56 … 52.44 | 4.01 mm below `SW9` |

**The fit, and the margin that governs it:**

| constraint | value |
|---|---|
| `J5` tail row | **X 65.900** |
| Tail pad edge (Ø1.6 pad) | X 65.100 |
| Battery right edge | X 64.000 |
| **Clearance, tails to cell** | **1.100 mm** (rule ≥ 0.5) |
| Mating face (tail row + 6.53) | X **72.430** |
| Board edge | X 72.000 → face **0.430 mm outboard**, inside the 1.5 mm gap |
| **Face to cavity wall** | **1.070 mm** for the recess lip |
| Pin 1 (top) | doc Y **138.000** |
| Pin 24 (bottom) | doc Y **79.580** |
| Pin span | **58.420 mm** = 23 × 2.54 |
| `J5` ↔ IR RX `U6` | 1.53 mm |
| **NFC Ø48 loop ↔ `J5` metal** | **9.155 mm** (was 5.490; rule ≥ 5) |

> **`J5`'s courtyard legitimately overhangs the right edge by 0.975 mm.** That is what a
> right-angle socket is *for* — the mating face has to reach the wall. `p1_regression.py` now
> tests it explicitly (`J5 mating face vs the wall ≤ 1.0 mm`) instead of counting it as a part
> that has fallen off the board.

---

## 5. ORDER-B, and the 180° reversal proof

```
 1 5V    2 G     3 3V3   4 SDA   5 SCL   6 G     7 N38   8 N47
 9 X0   10 X1   11 X2   12 X3   13 X4   14 X5   15 X6   16 X7
17 X8   18 X9   19 G    20 WAKE 21 DET  22 3V3  23 G    24 5V
```

**All 24 electrical functions retained** — 2 × `ACC_5V_SW`, 2 × `ACC_3V3_SW`, 4 × `GND`,
`EXT_SDA`, `EXT_SCL`, `NATIVE_A`/GPIO38, `NATIVE_B`/GPIO47, `WAKE_ATTN_N`, `ACC_DETECT_N`,
`XGPIO0`–`XGPIO9`. Nothing added, removed or merged. Verified from the exported netlist, pin by pin.

**Reversal safety, proved programmatically.** A full 24-pin accessory inserted 180° maps its pin
*n* to AQROOT contact *25 − n*:

| accessory | AQROOT | class |
|---|---|---|
| 1 `5V` | 24 `5V` | **5V ↔ 5V** |
| 2 `G` | 23 `G` | GND ↔ GND |
| 3 `3V3` | 22 `3V3` | **3V3 ↔ 3V3** |
| 6 `G` | 19 `G` | GND ↔ GND |
| 19 `G` | 6 `G` | GND ↔ GND |
| 22 `3V3` | 3 `3V3` | 3V3 ↔ 3V3 |
| 23 `G` | 2 `G` | GND ↔ GND |
| 24 `5V` | 1 `5V` | 5V ↔ 5V |
| every other pair | | **3.3 V logic ↔ 3.3 V logic** |

> **Power-to-signal maps under 180° reversal: ZERO.** No 5 V reaches a signal, no 3.3 V reaches
> 5 V, no GND reaches a signal. The order is symmetric by construction, and that symmetry is the
> reason ORDER-B supersedes ORDER-A.

**One-position shift: still physically impossible.** A mating male body is exactly
24 × 2.54 = **60.96 mm**; the closed-end recess is **62.5 mm** internally, leaving **1.54 mm** of
play against a 2.54 mm pitch — **61 % of one position**. Both ends closed, pin-1 triangle, red
bands over pins 1 and 24. **No proprietary shroud, and D-097's asymmetric key is no longer needed.**

---

## 6. Qwiic

`J8` `JST SM04B-SRSS-TB(LF)(SN)`, SH 1.0 mm, 4 circuit, side entry, SMT — **machine-placed**, so
the manual-assembly list (`J5`, `D1`) does not grow.

**Pin order 1 GND · 2 `ACC_3V3_SW` · 3 `EXT_SDA` · 4 `EXT_SCL`** — the ecosystem standard, identical
for SparkFun Qwiic and Adafruit STEMMA QT.

**It attaches at `EXT_SDA` / `EXT_SCL`** — downstream of `U16` TCA4307 and of the `R47`/`R48` 22 Ω
pair, at `D2`'s TPD4E1B06 clamp, the same node as the header. **No buffer, no mux, no repeater, no
extra pull-ups and no second TVS were added**, and the authoritative analysis for that is in the
symbol's own description: the existing clamp sits on the shared node, so it protects both exits by
construction.

**Power is `ACC_3V3_SW`, and that is architectural.** `U16`'s own VCC is already `ACC_3V3_SW` and
`R49`/`R50` pull to it, so an unswitched `+3V3` feed would create a powered-device / unpowered-bus
state. **`ACC_5V_SW` is not present on `J8` and cannot be.**

**Capacitance recheck on the built placement:** on-board copper from `U16` to the two exits is now
≈ 25 mm ≈ 25 pF; connector ≈ 1 pF; a 100 mm Qwiic cable ≈ 5–10 pF; a typical breakout ≈ 10 pF.
**One board ≈ 40 pF; three short daisy-chained boards ≈ 60–80 pF**, against **≤ 200 pF at 400 kHz**
on the 1.5 kΩ pull-ups. 100 kHz remains the fallback. **No mux or repeater is required.**

---

## 7. PM-1 — four converter cells, all closed

| converter | IC → inductor, before | **after** | requirement |
|---|---|---|---|
| `U12` TPS63020 +3V3 | 12.96 mm | **4.80 mm** | ≤ 5 mm |
| `U13` TPS61023 NFC 5 V | 28.56 mm | **4.34 mm** | ≤ 5 mm |
| `U21` TPS61023 accessory 5 V | 30.50 mm | **3.86 mm** | ≤ 5 mm |
| `U17` TPS61169 backlight | **45.90 mm** | **3.79 mm** | ≤ 5 mm |

Each cell was packed in **electrical order**, so the IC gets its inductor, then its input
capacitor, then its output capacitor, then its feedback divider — the whole power cell, not just
the inductor. `D8`, the backlight catch diode that sat **45.7 mm from its own inductor**, is now
**3.56 mm from `U17`** and adjacent to `L3` and `C44`, so the `L3 → D8 → C44` boost energy loop —
the one that switches to **39 V** on an open-LED fault — is a local loop instead of a 76 mm
perimeter running past the microphone.

Switch nodes are also away from their victims by construction: `U12`/`U11` are in the bottom band,
`U21`/`U13` are east of the NFC circle, and `U17` is in the lower left margin — none of them
adjacent to `MK1`, the NFC receive path, the USB pair or the I²C trunk.

---

## 8. PM-2 — the protection chain, and PT-1

**The whole 1.5 A path is now one monotonic column in the left margin**, in electrical order:

| link | length |
|---|---|
| `J4` → `F1` | 8.59 mm |
| `F1` → `Q2` | 6.21 mm |
| `Q2` → `Q3` | 7.80 mm |
| `Q3` → `R75` | 8.26 mm |
| **total 1.5 A path** | **30.86 mm** (was **116.7 mm**) |
| `R75` ↔ `U18` (Kelvin) | **6.60 mm** |

**Protection topology is unchanged and D-049 is untouched.** No FET, no threshold, no divider value
and no recovery branch was altered — only positions moved.

**`J4` is the one part in the chain that could not join it, and that is recorded rather than
hidden.** The left margin is also the mandatory 915 MHz coax lane. The lane is a *cable* lane, not
a component keepout — the RG-178 lies over the rear parts, all of which are ≤ 2.0 mm — but `J4` is
a **5.75 mm JST-PH with a mating cable** and nothing can lie over it. It sits at the **top of the
column at doc (7.000, 113.000)**, north of the coax's western excursion, **8.59 mm from `F1`** and
clear of the cable by 0.7 mm.

**PT-1 CLOSED.** `U11` BQ25185 moved from inside `BATTERY_SHADOW` to doc **(67.500, 70.200)** — the
rear right column, **3.5 mm clear of the cell's right edge** at X 64.0 and outside the shadow
entirely. Its ≈ 0.65 W of charging dissipation now spreads into board copper in a region with no
cell behind it.

### 8.1 B-34 re-estimated on the built geometry

**Do not claim routing losses are zero.** Estimated on the *intended* copper, at 1 oz / 35 µm:

| path | length | width | resistance | at 1.5 A | at 1.75 A |
|---|---|---|---|---|---|
| **Before** — `Q3` → `R75` alone | 79.0 mm | 1.0 mm | 38.8 mΩ | 58 mV / 87 mW | 68 mV / 119 mW |
| **After** — the whole `J4` → `R75` chain | **30.9 mm** | 1.0 mm | **15.2 mΩ** | **23 mV / 34 mW** | **27 mV / 47 mW** |

**Board copper in the protection path improves by ≈ 53 mW at 1.5 A and ≈ 72 mW at 1.75 A.**
B-34's ≈ 0.70 W is dominated by the BQ25185 BATFET's 115 mΩ and the FET R_DS(on), which this task
did not and should not change — **so B-34 improves materially but does not close.** It stays open,
now quantified: the copper contribution falls from ≈ 17 % of the figure to ≈ 7 %.

---

## 9. PM-3 — NFC symmetry, closed exactly

The front end is rebuilt as a mirror pair about **y = 118.000**, running `U9` → `J7` in +X:

| stage | arm A | arm B | Δx | arm-length Δ |
|---|---|---|---|---|
| EMC inductor | `L5` (39.30, 120.20) | `L6` (39.30, 115.80) | **0.000** | **0.000** |
| EMC capacitor | `C69` (39.30, 122.30) | `C70` (39.30, 113.70) | **0.000** | **0.000** |
| matching capacitor | `C71` (42.70, 120.20) | `C72` (42.70, 115.80) | **0.000** | **0.000** |
| Q resistor | `R114` (46.10, 120.20) | `R115` (46.10, 115.80) | **0.000** | **0.000** |
| RX divider | `R116` (46.10, 122.30) | `R117` (46.10, 113.70) | **0.000** | **0.000** |
| antenna capacitor | `C75` (49.50, 120.20) | `C77` (49.50, 115.80) | **0.000** | **0.000** |

> **Geometric arm-length difference: 0.000 mm, against a ≤ 1 mm requirement.** Both arms have the
> same topology, the same orientation and the same stage order, and every pair is equidistant from
> the axis. The `NFC_RF` class already forbids vias on both arms, so the symmetry survives routing.

`Y1` is now **5.40 mm from `U9`** with `C79`/`C80` on the same side of the crystal instead of
13–15 mm away on the far side of the IC, so the oscillator loop is local. `J7` is on the axis at
doc (54.000, 118.000), **20.00 mm** from `U9`, with the tuning parts (`C71`, `C72`, `C75`, `C77`,
`R114`, `R115`, `L5`, `L6`) in an open row and `TP37`/`TP38` symmetric about the axis.

**No locked NFC component value was changed.** Ø48 clear and Ø58 exclusion are unchanged at centre
doc (31.800, 124.500); the battery keeps **zero overlap** with the clear region with a 2.0 mm gap.

---

## 10. `BOOT`, retention, and the regressions

**`BOOT` `SW1` → doc (28.300, 6.000), front face**, in the measured 11.04 mm window between the
microSD shell and the USB-C receptacle. It is an **SMD** PTS645 whose actuator faces **out of the
front shell**, so the service aperture is a **Ø2 mm recessed hole in the FRONT wall low down** —
not in the bottom wall, and therefore **not in the microSD card-insertion path and not in the
USB-C plug envelope**. Recessed, tool-only, independent of firmware, usable on a bricked device.
**Lower-left was not used**: that wall *is* `ANT433_REGION` and the mandatory `COAX_915_CHANNEL`.

**Retention: still two M2**, `BOSS1` doc (40.000, 12.000) and `BOSS2` doc (60.000, 145.000),
Ø4.5 keep-out / Ø2.2 NPTH. The Ø6.0 search still returns **zero** sites; Ø4.5 returns **two**. The
four rear ribs shifted with the board and are still component-free. **Widening the board did not
buy a third screw** — the display and the cell still leave slivers narrower than a Ø4.5 keep-out —
and no functional geometry was sacrificed chasing one.

**Every P1 relationship re-derived by script and re-verified:**

| check | result |
|---|---|
| Board outline | **72.000 × 148.000** |
| Footprints | 324 = 322 schematic + 2 bosses |
| **Side-aware courtyard collisions** | **0** |
| Parts outside the board in X | **0** (`J5` mating face and the `U1` keep-out excepted, both tested separately) |
| 915 coax routed length | **138.48 mm** of 200, 46.52 mm spare, min bend radius 7.42 mm |
| 433 flex lead | 44.12 mm of 100 |
| NFC pair | **31.23 mm** of 75 (was 41.73 — PM-3 shortened it) |
| Speaker lead | 29.31 mm of 152 |
| FPC consumed | 14.94 mm of 29.5 |
| microSD ↔ USB-C | 14.990 mm (rule ≥ 8.0) |
| NFC clear ↔ battery | 2.0 mm, **zero overlap** |
| NFC loop ↔ speaker | 80.919 mm (rule ≥ 20) |
| `MK1` ↔ speaker | 67.424 mm (rule ≥ 60) |
| SMA hex / washer ↔ Ø58 | +1.279 / +0.798 mm |
| SMA ↔ IR TX / RX | 47.25 / 60.75 mm centre; 38.381 / 51.881 mm edge |
| IR TX ↔ IR RX | 15.000 mm |
| Display offset | **2.34 mm** left of centre (was 3.34 — the symmetric growth halved it) |

---

## 11. Validation

| check | before (P2-000) | **after** |
|---|---|---|
| **DRC** | 26 violations | **1** |
| DRC residue | 24 `silk_over_copper` + 1 `silk_edge_clearance` + 1 `solder_mask_bridge` | **1 `solder_mask_bridge`** — the `MK1` netless-NPTH-inside-its-own-GND-ring artefact, reviewed and accepted at D-227, **still not excluded and not suppressed** |
| **ERC** | 0 errors / 27 warnings | **0 errors / 27 warnings**, histogram identical |
| Unrouted (DRC) | 499 | **499** — `J8`'s four pads *are* in the list; the minimum spanning tree simply rewired around them, because `J8` sits close to existing `GND` and `EXT_*` nodes |
| Tracks / signal vias / electrical pours | 0 / 0 / 0 | **0 / 0 / 0** |
| `p1_regression` | PASS | **PASS**, 0 checks failed |
| `dru_probe` | PASS | **PASS** — 64 rules, 0 missing references, 0 dead patterns |
| `netclass_probe` | PASS | **PASS** |
| `fork_equivalence` | PASS | **PASS** — the new footprint is declared; **`Samtec_BCS-112-S-D-HE.kicad_mod` is RETAINED in the library, not deleted**, because Beta-DM still uses it and it is the fallback if the owner reverses D-237 |
| Netclasses / patterns | 18 / 57 | **18 / 57**, unchanged |

---

## 12. Opportunity and simplification scan

| question | finding |
|---|---|
| Connector or Qwiic part that simplifies assembly | **Yes.** `J8` is **SMT and machine-placed**, so the manual-assembly list stays at two parts (`J5`, `D1`). The through-hole count is unchanged at 24 — one part replaced one part |
| Duplicate protection created by Qwiic | **None.** `J8` shares `U16`, the pull-ups, the 22 Ω pair and `D2`. Zero components added |
| Converter cells sharing harmless space | **Yes, and used.** `U21` and `U13` are both TPS61023 with identical passives (D-088) and now sit as adjacent cells east of the NFC circle |
| Test points blocking routing channels | **None.** The 24 displaced test points were packed into a rear service strip clear of the `J5` escape lane and the four converter cells |
| `BOOT` consuming useful edge | **No longer.** It vacated 10.2 mm of the right wall — the space the Qwiic connector now occupies |
| Hot part under the battery | **Fixed** — PT-1 |
| High-impedance protection node unnecessarily long | **Fixed** — PM-2 |
| Connector pin-order hazard | **Fixed** — ORDER-B removes both 5 V-adjacent-to-signal cases and is 180°-symmetric |
| No-respin option made inaccessible | **Checked and none.** The DNP rework sites `R112`, `C81`, `C82`, `R123`, `R107` are all still on open faces with no part over them |
| New features | **None added.** No Grove, no mikroBUS, no Arduino shield, no Pi header, no hub, no mux |

---

## 13. Gate results

### FBV2-P1 re-issued: **PASS**

The outline, the battery and `J5` all changed, so the FBV2-P1-002 pass was superseded and the gate
was re-run in full against the new design. Every criterion above is re-derived from the board file
by `p1_regression.py`, not asserted. **0 collisions, 0 parts off the board, every keepout valid,
every cable within budget, the expansion port / Qwiic / POWER / BOOT / retention all mechanically
valid, and every no-respin site accessible.**

**No percentage is awarded**: P1 was **re-earned, not newly earned**. The programme already held
its +6 for FBV2-P1 at FBV2-P1-002, and the gate-backed method does not pay twice for one gate.

### FBV2-P2 entry re-issued: **PASS**

| criterion | verdict |
|---|---|
| Design rules valid | **PASS** — `dru_probe`, 64 rules, 0 missing references |
| Netclass probe | **PASS** |
| Stackup strategy | **unchanged and still valid** — 4-layer JLC04161H-7628, layer roles enforced by rule |
| Ground strategy | **valid** — one solid In1, one authorised void (the ESP32 keepout) |
| Power routing placement-ready | **PASS** — PM-2 closed |
| Converters placement-ready | **PASS** — PM-1 closed |
| NFC placement-ready | **PASS** — PM-3 closed |
| Community / Qwiic escape feasible | **PASS** — see below |
| **No electrically required placement move remains** | **PASS — PM-1, PM-2, PM-3 and PT-1 are all CLOSED** |

**Escape feasibility on the new connector.** The 1 × 24 presents 24 Ø1.02 mm holes on 2.54 mm at
X 65.900, Y 79.58 … 138.00. Adjacent-pad gap is 2.54 − 1.6 = **0.94 mm**, which passes one 0.2 mm
track at 0.2 mm clearance per gap per layer: **23 gaps × 3 usable layers = 69 crossings**, against
the 66 the old 2 × 12 field offered — and the 7.87 mm dead band between the old rows is gone.
Both ends of the row are open. **No reservation area and no fanout exception is needed**, which is
why the retired `HEADER RESERVED` / `J5_SELF_FANOUT` rules were not re-created.

**P2 entry earns no percentage of its own**, by its own terms.

---

## 14. Overall

**Full Beta v2 stays at ~74 %.** PCB placement remains 100 % (re-earned on a new outline), PCB
routing remains 0 %, and no gate in the twelve-gate table newly passed.

---

## 15. New item requiring owner / CTO approval

> **E-7 — the 57 mm battery envelope is now the LOWER bound of what fits, not a target.** The
> procurement gate found that both credible candidates are **50 mm wide**, so the cell no longer
> fills the envelope in X and there is **7 mm of unused width** inside the reservation. That is not
> a defect and nothing depends on it, but it means a future task could either (a) reclaim some of
> that width for rear components, or (b) keep it as tolerance for a wider, higher-capacity cell.
> **Recorded, not decided** — the reservation stays at 57 mm until the owner rules.

Everything else in this task was executed under the authority the owner granted at FBV2-EXP-001.
