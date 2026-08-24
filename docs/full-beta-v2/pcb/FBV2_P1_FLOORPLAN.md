# AQROOT Full Beta v2 — FBV2-P1 enclosure-driven floorplan

**Status: NORMATIVE for FBV2-P2.** Created 2026-08-24 at **FBV2-P1-001**.
Authority: [`../CTO_DECISIONS.md`](../CTO_DECISIONS.md),
[`../mechanical/MECHANICAL_INTERFACE_SPEC.md`](../mechanical/MECHANICAL_INTERFACE_SPEC.md),
[`../mechanical/P1_FLOORPLAN_INPUTS.md`](../mechanical/P1_FLOORPLAN_INPUTS.md).

> **GATE RESULT: FBV2-P1 DOES NOT PASS.** Every placement criterion in the task closes except
> one: **the 915 MHz pigtail cannot reach the top-panel SMA.** The floorplan itself is complete,
> collision-free and mechanically credible — the blocker is a cable length and an antenna-feed
> route, not a placement. See §9. **No progress percentage was awarded.**

> **NO SIGNAL ROUTING EXISTS.** Zero tracks, zero vias, zero copper pours. 499 unrouted
> connections is the correct state at P1 exit.

---

## 1. Coordinate datum

| item | convention |
|---|---|
| **Origin** | **lower-left corner of the board outline** |
| **X** | left → right, 0 … 70.000 mm |
| **Y** | **bottom → top**, 0 … 148.000 mm |
| **F.Cu** | **FRONT** — display, buttons, RGB, IR, USB-C, microSD, community connector |
| **B.Cu** | **REAR** — battery side; microphone, both radio modules, most support ICs |
| **KiCad file datum** | upper-left, **Y grows downward**. Translation: `X_kicad = X_doc`, **`Y_kicad = 148.000 − Y_doc`** |

Every table in this document, in `FBV2_P1_COORDINATES.csv` and in `FBV2_P1_KEEPOUTS.md` uses the
**doc** datum. The board sits centred in the 75.0 × 155.0 mm cavity, so
**`X_cavity = X_doc + 2.5`, `Y_cavity = Y_doc + 3.5`**.

---

## 2. Outline

| item | value | status |
|---|---|---|
| Outline | **70.000 × 148.000 mm**, plain rectangle, closed `Edge.Cuts` | **as TARGET — not expanded** |
| Thickness | **1.6 mm** | LOCKED |
| Board edge → cavity wall | **2.5 mm** in X, **3.5 mm** in Y | ≥ 1.5 mm required |
| Corner radii / chamfers | **none** | not required by the fit |

**The 70 × 148 target closed, so the 72 × 152 maximum was not used.** No decorative geometry was
added. The outline is four straight segments and nothing else.

---

## 3. What was rebuilt, and from what

The pre-P1 PCB was still the inherited **Beta-DM** board — 188 footprints, 2 801 track segments,
424 vias, 43 zones, bit-identical to `hardware/beta-dm/`. It is not a placement baseline for a
design whose content has changed, so it was **rebuilt from the current nine-sheet schematic**:

| step | result |
|---|---|
| Template | the pre-P1 board **stripped to its header, layer stack, `general` and `setup`** — design rules, layer names and constraints preserved verbatim |
| Removed | **all** Beta-DM footprints, tracks, vias, zones and graphics |
| Re-created | **321 footprints, one per schematic component**, references and exact verified footprints preserved |
| Nets | **224 nets / 991 pads** applied from the schematic netlist |
| Added | Edge.Cuts outline, 13 named mechanical regions, 4 copper rule areas, 3 M2 NPTH bosses |
| **Schematic** | **UNTOUCHED — ERC 27 / 0 errors, histogram byte-identical to FBV2-MECH-002** |

**Beta-DM itself was not opened.** `hardware/beta-dm/` and the frozen `hardware/beta/` tree are
unchanged; `fork_equivalence` now correctly reports the v2 PCB as *changed*, which is the expected
and intended outcome of P1.

---

## 4. Board-side convention and the microphone (ruling P1-A)

**F.Cu = FRONT / display / buttons. B.Cu = REAR / battery.** LOCKED.

`MK1` **PUI `DMM-4026-B-I2S-R`** is on **B.Cu at X 3.000, Y 50.000**, rotation 0.

| requirement | achieved |
|---|---|
| On B.Cu | **yes** |
| Listens **forward** through the board | **yes** — bottom-port part on the rear face, port aperture through the Ø1.05 mm NPTH to the FRONT shell |
| Ø1.05 mm NPTH concentric with pad 4 | **yes — carried by the footprint itself**, drawn at FBV2-S2-002 (D-203) |
| Front gasket / aperture on the opposite face | **yes** — `MIC_ACOUSTIC` region, X 0.50 … 5.50, Y 46.50 … 53.50 on the FRONT face |
| **NOT under the LiPo envelope** | **yes — 1.21 mm clear** of the battery's left edge (battery starts at X 6.000) |
| Front bottom third | **yes** — Y 50.0 of 148, i.e. ≈ 34 % of the enclosure height, and **below the display**, whose bottom edge is Y 55.04 |
| ≥ 60 mm from the speaker | **67.42 mm** centre-to-centre, on opposite faces |
| Ø2.5 mm component keepout / gasket path ≤ 2.5 mm | reserved as a copper rule area plus the mechanical region |

**O-1 is resolved by construction:** the aperture is on the FRONT shell and `MK1` is on the copper
face pointing away from it, which is the only arrangement that satisfies both §7.1 and M-14.

---

## 5. Rear packing (ruling P1-B)

The 20 mm speaker-to-loop separation is **not** double-counted: the battery physically lies
between the NFC zone and the speaker and creates the separation itself.

| band | region (doc mm) | occupied length |
|---|---|---|
| **NFC clear zone** | X 0.50 … 48.50, Y 102.00 … 150.00 | **48.0** |
| gap | | 3.5 |
| **Battery** | X 6.00 … 66.00, Y 23.50 … 98.50 | **75.0** |
| gap | | 2.5 |
| **Speaker** | X 48.00 … 68.00, Y 1.00 … 21.00 | **20.0** |

**48 + 75 + 20 = 143 mm of the 155 mm cavity; 12 mm remains as real gaps and tolerance** — exactly
the arithmetic the ruling specifies.

| check | result |
|---|---|
| NFC clear zone | **48.0 × 48.0 mm** (the top 2.0 mm sits above the board edge, inside the cavity, where the antenna is bonded to the rear shell) |
| NFC ↔ battery overlap | **ZERO**, 3.50 mm gap |
| Battery envelope | **60 × 75 × 8.0 mm**, not reduced |
| Speaker | **Ø20 × 3 mm** driver plus sealed cavity, **bottom band, biased lower-right** (centre X 58.0 of a 70 mm board) |
| Speaker ↔ NFC loop perimeter | **81.00 mm** (rule ≥ 20) |
| Speaker beside the battery | **not attempted** — the ruling forbids it and the 75 mm cavity does not allow it |
| B.Cu parts in the speaker zone | **none** — the sealed acoustic cavity is a hard exclusion |
| B.Cu height under the battery | **≤ 1.2 mm enforced on every part** |
| B.Cu height under the NFC zone | **≤ 1.0 mm enforced** (the Column A rear air gap) |
| Bosses / screws through the NFC region | **none** |

---

## 6. Placement by face

### 6.1 Front (F.Cu) — 120 footprints

| ref | part | X | Y | rot | note |
|---|---|---|---|---|---|
| `J1` | Hirose FH69-50S-0.5SH | 31.660 | 52.000 | 0 | FPC mouth faces the panel; **1.24 mm below the display edge** |
| `J2` | Molex 5025700893 microSD | 14.000 | 11.200 | 0 | card enters the bottom edge |
| `J3` | GCT USB4105-GF-A-120 | 42.000 | 5.300 | 180 | mouth at the bottom edge |
| `J5` | Samtec BCS-112-S-D-HE | 64.970 | 121.000 | 270 | mates **+X** through the right wall |
| `J4` | JST B2B-PH-K (battery) | 63.500 | 102.000 | 0 | clear of the battery and the NFC zone |
| `J6` | JST B2B-PH-K (speaker) | 37.000 | 20.000 | 0 | 22.8 mm to the driver on a 152 mm lead |
| `SW9` | JS102011SAQN power | 64.920 | 70.000 | 90 | right wall, lower-middle |
| `SW1` | PTS645 **BOOT** | 64.920 | 84.000 | 90 | recessed service-tool access |
| `SW3`–`SW6` | PTS645 D-pad | 12.5 / 5.0 / 20.0 | 40.5 / 25.5 / 33.0 | 90 | 7.5 mm arms, front lower-left |
| `SW7`, `SW2` | PTS645 A / B | 52.500, 63.200 | 49.000 | 0 | front lower-right |
| `D13` | MEIHUA MHPA3528RGBCT | 31.660 | 41.000 | 0 | front-facing RGB, needs a diffuser / short pipe |
| `D1` | Vishay TSAL6100 IR TX | 50.750 | 143.600 | 0 | THT, formed 90° to look out of the top panel |
| `U6` | Vishay TSOP38238 IR RX | 65.750 | 143.400 | 0 | THT, formed 90°, tallest top-side part |
| `U1` | **ESP32-S3-WROOM-1** | 56.750 | 20.000 | 270 | **antenna faces +X, at the right board edge** |
| `U5` | MAX98357A | 30.000 | 32.000 | 0 | near `J6` and the speaker band |

### 6.2 Rear (B.Cu) — 201 footprints

| ref | part | X | Y | note |
|---|---|---|---|---|
| `MK1` | PUI DMM-4026-B-I2S-R | 3.000 | 50.000 | ruling P1-A |
| `U7` | Ebyte E07-400M10S (433) | 9.000 | 12.000 | **IPEX faces the rear shell → serviceable with the shell open** |
| `U8` | Ebyte E22-900M22S (915) | 26.000 | 12.000 | see §9 — the coax route is the P1 blocker |
| `U9`, `Y1` | ST25R3916-AQET + 27.12 MHz | 30.000, 36.500 | 112.000 | **inside the NFC zone, ≤ 1.0 mm**, matching network short |
| `J7` | JST BM02B-ACHSS (NFC) | 52.000 | 102.000 | outside the loop, top-entry clearance in the rear cavity |
| `U12`, `U14` | TPS63020, MAX17048 | 12.000, 26.000 | 96.000 | main rail cluster above the battery |
| `U11` | BQ25185 charger | 56.000 | 32.000 | near the USB input |
| `U2`, `U3`, `U23` | PCAL9535A ×3 | 56.000 | 60 / 70 / 50 | 0x20 / 0x21 / 0x22 unchanged, right-side column |
| `U16` | TCA4307 | 58.600 | 94.000 | at the community-port boundary |
| `U4` | BMI270 | 56.000 | 78.000 | |
| `U17` | TPS61169 backlight boost | 48.000 | 34.000 | |

Everything not anchored above was placed by **net-affinity clustering**: each remaining part is
seated next to whichever anchored device it shares the most (non-power) nets with, so switching
converters keep their inductors and capacitors, the NFC front end stays together and the expanders
sit beside their destinations. **No part was placed by area-filling alone.**

---

## 7. Gate metrics, measured

```
BOARD                 70.0 x 148.0 x 1.6 mm            target 70.0 x 148.0
COMPONENTS            321 placed   F.Cu 120   B.Cu 201
DISPLAY               56.54 x 84.96 at X 3.39..59.93, Y 55.04..140.00
J1 FH69               X 16.38..46.95  Y 43.66..53.80   1.24 mm below the panel edge
FPC REACH             4.7 drop + 6.0 fold + 3.0 run = 13.7 mm of a 29.5 mm worst-case tail
FPC MARGIN            15.8 mm spare
USB <-> microSD       BODY edge-to-edge 16.40 mm       rule >= 8.00
USB-C CENTRING        7.00 mm right of board centre
J5 COMMUNITY          X 60.36..69.58  Y 105.22..136.78, 24 x D0.71 PTH
J5 vs BATTERY         6.72 mm   |  J5 vs NFC+5  6.86 mm
IR TX <-> IR RX       15.00 mm                          rule >= 15.00
SMA <-> IR TX         39.55 mm centre-to-centre         rule >= 15.00
SMA <-> IR TX         31.05 mm edge-to-edge             rule >= 8.00
ESP32 KEEP-OUT        X 63.06..84.06  Y -4.00..44.00 -> 6.94 mm on-board, 14.06 mm off-board
NFC ZONE              48.0 x 48.0    NFC <-> BATTERY 3.50 mm, ZERO overlap
SPEAKER <-> NFC       81.00 mm                          rule >= 20.00
MIC <-> SPEAKER       67.42 mm, opposite faces          rule >= 60.00
MIC vs BATTERY        1.21 mm clear
433 CABLE             straight 16.6 mm, routed est. 35.7 mm of 100 mm -> REACHES
915 CABLE             straight 140.2 mm, routed est. 190.3 mm of 100 mm -> SHORT BY 90 mm
MOUNTING BOSSES       3 x M2 placed at D4.5 keepout     target 6 x M2 at D6.0
```

---

## 8. Geometry review — zero placement conflicts

A full pairwise review was run over all 321 courtyards, **side-aware** (front and rear parts may
share plan area; through-hole parts block both faces):

| check | result |
|---|---|
| Courtyard / body overlaps | **0** |
| Parts outside the board or inside the 0.4 mm edge margin | **0** |
| Pads closer than 0.55 mm to the board edge | **0** |
| Parts inside a boss keepout | **0** |
| Display-shadow height violations (F.Cu > 0.8 mm) | **0** |
| Battery-shadow height violations (B.Cu > 1.2 mm) | **0** |
| NFC-zone height violations (B.Cu > 1.0 mm) | **0** |
| B.Cu parts inside the speaker cavity | **0** |
| THT leads protruding into the battery, NFC or speaker volume | **0** |
| Parts inside the ESP32 antenna keepout | **0** |
| Parts inside the microphone acoustic keepout | **0** |

**KiCad DRC: 76 violations, and none of them is a placement collision.** They break down as
24 `silk_over_copper` + 1 `silk_edge_clearance` (reference-designator silkscreen — P1 does not do
silk), 21 `clearance` (pad-to-pad adjacency, a routing-stage nudge), 12 `drill_out_of_range`
(the **stock ESP32 footprint's 0.2 mm thermal vias** against the board's 0.3 mm minimum-hole rule
— a fab-rule reconciliation for FBV2-P2), 12 `copper_edge_clearance` at the board corner,
3 `extra_footprint` + 3 `lib_footprint_issues` (the three mechanical M2 bosses, which correctly
have no schematic symbol), 2 `padstack_invalid` and 1 `solder_mask_bridge`. **499 unconnected
pads is the intended P1 state.**

---

## 9. Why the gate does not pass — the 915 MHz feed

**Every 3.5 mm-tall part is excluded from the upper half of the board.** Above Y ≈ 55 the front is
the display (F.Cu ≤ 0.8 mm) and the rear is first the battery (B.Cu ≤ 1.2 mm) and then the NFC
zone (B.Cu ≤ 1.0 mm, no shielding cans). The only free strip is X 53.5 … 70.0 above the battery,
which is 16.5 mm wide and already carries `J5`'s 31.6 mm through-hole field. **A 15.89 × 21.34 mm
radio module does not fit anywhere above Y ≈ 55.**

`U8` therefore sits at the bottom rear. From there to a top-panel SMA is **140.2 mm straight**;
with a ≥ 5 mm bend radius and a ≥ 15 mm service loop the routed run is **≈ 190 mm**.

| assembly | verdict |
|---|---|
| `095-902-568-100` (**100 mm**, the part ruled in this task) | **SHORT BY ≈ 90 mm** |
| `095-902-568-150` (150 mm, the superseded part) | **SHORT BY ≈ 40 mm** |
| `095-902-568-200` (200 mm) | reaches |

**And length is not the whole problem.** The SMA is locked to the **top-edge left half**, and the
NFC 48 × 48 clear zone occupies the entire upper-left. A coax run from the bottom to the top-left
either crosses the NFC zone or runs in the 2.5 mm side gap **inside the 5 mm metal keepout**.
Neither is permitted.

**This is surfaced, not decided.** Three CTO options are set out in the audit; the cleanest is to
**raise the display support by ≈ 3 mm** — Column A of the mechanical spec carries **9.9 mm of
unused Z** — which frees the whole upper half for a radio module and lets a short pigtail reach.
**No antenna MPN, no locked dimension and no electrical architecture was changed here.**

---

## 10. Review artefacts

| file | content |
|---|---|
| [`FBV2_P1_COORDINATES.csv`](FBV2_P1_COORDINATES.csv) | every reference: side, X, Y, rotation, footprint, value, sheet, courtyard box |
| [`FBV2_P1_KEEPOUTS.md`](FBV2_P1_KEEPOUTS.md) | all 13 mechanical regions and 4 copper rule areas, with layers |
| [`review/FBV2-P1-front.svg`](review/FBV2-P1-front.svg) | front plot: outline, F.Cu, references, display / IR / SMA / USB / microSD regions |
| [`review/FBV2-P1-back.svg`](review/FBV2-P1-back.svg) | rear plot, mirrored: battery, NFC, speaker, 433 regions |
| [`review/FBV2-P1-mechanical.svg`](review/FBV2-P1-mechanical.svg) | mechanical only: outline, all named regions, bosses, part bodies |
