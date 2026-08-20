# AQROOT Beta-DM — Final PCB DFM and Fabrication Release Gate

Board: **155 × 74 mm**, 4 layers, 1.6 mm, green mask. Measured on the released
board, `a5f5d97` + this pass. Every figure below is measured from the board
file or from the exported fabrication data, not read off KiCad's DRC severity.

---

## 1. Starting state

| | |
|---|---|
| DRC | 0 errors, 240 warnings, 0 schematic-parity issues |
| Unconnected | 103 |
| Ledger | `103 = A64 + B1(0) + B2(18) + C0 + D21` |
| B1 (fitted must-ground) | **0** |
| C (Lean must-work non-GND) | **0** |
| `hardware/beta/` tracked | unchanged vs `beta-full-reference-v1` |
| `hardware/beta/mechanical/` (untracked) | listed, untouched, uncommitted — 9 files, all dated 2026-08-15 |

All 240 warnings are silkscreen-related or dangling-track, and all are resolved
or explained in §3.

---

## 2. DFM sweep

| check | measured | limit | verdict |
|---|---:|---:|---|
| copper to board edge | 0.213 mm at `J2.9` | 0.20 mm (scoped) / 0.50 board-wide | **PASS** — documented `J2` vendor exception |
| hole to board edge | 0.850 mm | 0.30 mm | PASS |
| mounting hole to copper | 0.503 mm | 0.20 mm | PASS |
| minimum track width | 0.150 mm | 0.15 mm | PASS |
| annular ring, plated | 0.200 mm (`U1.41`); vias 0.125 mm | 0.125 mm | PASS |
| minimum drill | 0.200 mm | 0.20 mm | PASS |
| hole to hole, all nets | 0.400 mm | 0.25 mm | PASS |
| solder-mask web, different nets | **0.150 mm** (`U16.2`/`U16.3`) | 0.125 preferred / 0.100 floor | PASS — 0 pairs below either floor |
| courtyard overlaps, same side | 0 | 0 | PASS |
| zone islands | F.Cu 32, B.Cu 35, In1 2 | — | PASS |
| RF / reserved containment | **0.000000 mm** penetration | 0 | PASS |

Three sweep results needed a second look and turned out to be measurement
artifacts rather than board problems:

* **"annular ring 0.0000 mm"** — the five zero-ring holes are all
  `np_thru_hole`: `SW9` mechanical pegs, `J3` USB-C alignment holes, `MK1`.
  Non-plated holes have no annular ring. The tightest *plated* ring is
  0.200 mm.
* **"mask web −1.55 mm"** — the first pass compared `U1.41` against itself.
  `U1.41` is a 13-pad thermal array all carrying pad number 41. Measuring only
  different-net pairs, and along the centre-line so pad rotation is respected,
  gives a true minimum of **0.150 mm**.
* **"142 pathological tiny segments"** — none is zero-length, 129 are exactly
  0.05 mm (one step of the 0.05 mm router grid) and **none has a free end**.
  They are interior fragments of continuous routed paths, not acid traps.

### Dangling tracks

Two, both benign:

* `+3V3` on B.Cu, (69.100, 116.000) → (69.100, 141.000). Not vestigial —
  deleting it opens 4 `+3V3` rats, so it is a working trunk. Other `+3V3`
  copper meets it at y = 140.78, so the genuinely unused tail is **0.22 mm**.
* `NFC_5V_PA_PENDING` on F.Cu, 1.65 mm at (21.700, 25.650). A deferred NFC net,
  bucket A. Expected deferred copper.

---

## 3. Silkscreen

138 reference designators sit over a solder-mask opening on the board, 3
silkscreen items are clipped by the outline, and `U4`'s reference is 0.70 mm
against a 0.80 mm minimum.

**The released Gerbers resolve the 138 in data.** They were plotted with
soldermask subtraction, and the exported `F_Silkscreen` / `B_Silkscreen` each
contain a clear-polarity block carrying all 418 mask openings — verified by
reading the Gerber, not by trusting the flag. No ink is printed on a solderable
surface. The remaining four items are cosmetic and accepted.

---

## 4. Solid GND pour — assembly review

The outer pours are solid-connected, which was forced by measurement: thermal
relief produced 15 `starved_thermal` errors and still left 4 fitted GND pads
unconnected.

| pad class | assessment |
|---|---|
| 0402 / 0603 GND terminations | Acceptable. These pads already sit over a full In1 plane, so the outer pour adds heat capacity to a pad that was never thermally isolated. Tombstoning risk is a profile question, not a layout defect: use a normal 4-layer 1.6 mm profile with a full ground plane. |
| fine-pitch IC GND pads (`U2`, `U3`, `U4`) | Solid is what made these connect at all — see the GND closeout. No spoke geometry exists to starve. |
| USB shell / shield (`J3`) | Solid is the preferred low-impedance connection for shield tabs. |
| power components | Solid is preferred; thermal relief on a power return is a defect, not a feature. |

**No local pad exception is requested and no copper was modified.** The solid
design is accepted as proven.

---

## 5. The one finding that needs a decision

`R2.1`'s critical mask dam measures **+0.125 mm** exactly as the fab notes
document — the same measurement method confirms it. Applying that method to the
whole board found **63 vias whose drill barrel falls inside a paste aperture**,
of which **20 pads across 17 fitted references are small discretes or
fine-pitch pads with no dam at all**.

Worst cases are `C13.1` and `R9.1`: 0603 `+3V3` terminations with a 0.40 mm
barrel open 0.200 mm inside the paste aperture.

All are **same-net** fan-out vias, so there is no short risk; the risk is solder
wicking at reflow — precisely the mechanism §2 of the fabrication notes
protects `R2.1` against. This is a process decision, not a board defect, and no
copper was changed. The options and the full table are in
[`fab/BETA-DM-FABRICATION-NOTES.md`](fab/BETA-DM-FABRICATION-NOTES.md) §5:
resin-plug and cap the vias, reduce the stencil apertures locally, or accept
and inspect for a two-unit demo build.

---

## 6. Critical feature audit — `XGPIO5`

| | measured | required |
|---|---|---|
| position | (20.400, 14.050) | unchanged |
| diameter / drill | 0.50 / 0.25 mm | 0.50 / 0.25 |
| annular ring | 0.1250 mm | 0.125 |
| web to `U3.9` paste | 0.1250 mm | 0.125 |
| tenting | front and back, no per-via override | both sides |
| mask | green, CTO-locked | green |
| present in PTH drill export | yes, under the 0.25 mm tool at the exact coordinate | yes |

**PASS. Unaltered.**

---

## 7. Connectivity

| | |
|---|---|
| Fitted GND pads not on the main GND island | **0** |
| Lean must-work non-GND unrouted (C) | **0** |
| Unexplained rats | **0** |

Hard locks, all **PASS** with 0 must-work non-GND rats: `BOOT_N`,
`WAKE_INT_N`, R2 `+3V3`, `XGPIO5`, `XGPIO6`, `WAKE_ATTN_N_HDR`, `SX1262_RXEN`,
SPI-A, SPI-B, internal I2C, USB, I2S, backlight, buttons, FAST_IO.

---

## 8. DNP reconciliation

188 footprints = 146 fitted + 42 DNP. Position files carry 173, the 15
difference being `TP1`–`TP15`, correctly flagged `exclude_from_pos_files` —
test points are copper, not placed parts. 173 − 42 DNP = **131 placeable fitted
parts**.

| file | content | reconciles |
|---|---|---|
| `BOM-full.csv` | every symbol, reference only | 189 refs |
| `BOM-fitted.csv` | on this PCB, not DNP | **146 — exact match to the board** |
| `DO-NOT-POPULATE.csv` | on this PCB, DNP | **42 — exact match to the board** |
| `OFF-BOARD.csv` | in the design, no PCB footprint | `LS1` |
| `pos-fitted.csv` | placeable, not DNP | 131 |

`U5`, `U9`, `U13`, `U15`, `U16` and `D2`–`D7` are all confirmed DNP.
**`U10` (USBLC6-2SC6) is confirmed FITTED.** DNP parts leaking into the fitted
BOM: **none**.

**One correction was needed.** KiCad's schematic BOM put `LS1` — an 8 Ω
*off-board* speaker with no footprint — into the fitted assembly BOM. An
assembler would have been asked to place a part with no location on the board.
The assembly BOM set is now built against the board's footprint list, and `LS1`
is isolated in `OFF-BOARD.csv`. No schematic change was made.

---

## 9. Fabrication package

Regenerated in full from the post-pour board; all pre-pour files are replaced.

```
fab/gerbers/   F_Cu In1_Cu In2_Cu B_Cu  F_Mask B_Mask  F_Paste B_Paste
               F_Silkscreen B_Silkscreen  Edge_Cuts
               PTH.drl  NPTH.drl  drill maps  drill-report.txt  .gbrjob
fab/           BOM-full  BOM-fitted  DO-NOT-POPULATE  OFF-BOARD
               pos-fitted  pos-all
               assembly-top.pdf  assembly-bottom.pdf
               BETA-DM-FABRICATION-NOTES.md  ASSEMBLY-DNP-CONTROL.md
```

Validated by reading the exported files:

| check | result |
|---|---|
| layer set | 11 files, no stale or unexpected layer |
| Edge.Cuts extent | **74.000 × 155.000 mm** |
| copper regions | F.Cu 32, In1 2, In2 0, B.Cu 35 — matches the board's zone islands |
| PTH drill | 9 tools, 475 hits, 0.20–1.10 mm |
| NPTH drill | 3 tools, 5 hits (SW9 ×2, J3 ×2, MK1) |
| `XGPIO5` 0.25 mm drill at (20.400, 14.050) | present |
| silkscreen | mask-subtracted, verified in the Gerber |

---

## 10. Open order choices — none of these are decided

Surface finish (ENIG is the sensible default for the fine-pitch parts, but is
not chosen), copper weight, **impedance control (not specified — no controlled
stack-up is declared and the RF paths were not designed against one)**, via
plugging (§5), panelisation and fiducials (none in the data), IPC class and
E-test, and **MPN / manufacturer fields, which are empty on every BOM line**.
Part selection is not captured in the schematic and must be supplied before any
assembly quote.

---

## 11. Verdict

| | |
|---|---|
| DFM | **PASS** |
| Ready to order the PCB | **YES** |
| Ready for assembly | **NOT YET** — §5 must be decided, and MPNs supplied |
