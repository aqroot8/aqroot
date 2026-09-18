# AQROOT Demo — THROUGH-HOLE LEAD TRIM (NORMATIVE for assembly)

**Status: NORMATIVE.** Created 2026-09-18 at **D-763**.  Machine-checked by
`hardware/demo/manufacturing/checks/mechanical_keepout_contract.py` **MK10**.

This document exists for one part.  Read §2 before soldering `J4`.

---

## 1. Why a lead length is a mechanical requirement on this board

A through-hole part protrudes on the face its **body is not on**.  The register
`pcb/FBV2_P1_KEEPOUTS.md` writes that rule down for exactly one region —
`BATTERY_SHADOW`, *"no through-hole lead may protrude into it"*, because a
clipped lead against a LiPo pouch is a puncture risk — and `MK5` has enforced
it since D-759.

It does **not** write it down for `DISPLAY_SHADOW`, whose rule is worded
*"F.Cu component height ≤ 0.8 mm"*.  And `MK8`, which measures component
heights, filters by face: **a component on `B.Cu` is not an `F.Cu` component.**

Between those two clauses, one part fell through.

---

## 2. `J4` — THE BATTERY CONNECTOR.  ITS LEADS MUST BE TRIMMED.

`J4` is the **only through-hole part on this board whose body is on `B.Cu`**.

| | |
|---|---|
| Part | **JST `B2B-PH-K-S(LF)(SN)`**, PH series, 2.00 mm pitch, 2 circuits, top entry, through-hole |
| Body | **6.0 mm** above the rear face (JST `ePH.pdf`, *Header (Through-hole type)*, top entry, 2 circuits) |
| Lead below the seating plane | **(3.4) mm** — same drawing |
| Board thickness | **1.5744 mm** — this board's own stackup, not a nominal |
| **Untrimmed protrusion above `F.Cu`** | **1.826 mm**, plus the solder fillet |
| Where the leads land | `J4.1` at KiCad `(7.000, 35.000)`, `J4.2` at `(7.000, 33.000)` — **both inside `DISPLAY_SHADOW`** (KiCad `x 4.390 … 60.930`, `y 8.000 … 92.960`) |
| Allowance there | **0.80 mm** (`FBV2_P1_KEEPOUTS.md` §2 row A) |
| **Overshoot** | **1.026 mm** |

`J4.2` also lies **0.82 mm inside the west edge of `DISPLAY_ACTIVE`**
(doc `X 7.18 … 56.14`, `Y 60.80 … 134.24`).  The panel is over it.

### REQUIREMENT J4-T1

> **After soldering `J4`, trim both leads to a verified conductive-profile
> height ≤ 0.50 mm above the `F.Cu` surface.**  This leaves 0.30 mm geometric
> margin to the 0.80 mm `DISPLAY_SHADOW` limit before the insulation below.
> No sharp clipped lead or loose fragment may remain.

### REQUIREMENT J4-T2

> `J4` is soldered from the **FRONT** face (the leads enter from the rear and
> emerge on the front).  Solder, trim, clean, then inspect — **in that order**.
> Do not pre-cut the leads before soldering.  Inspect both joints after cutting;
> if the cutter cracked, lifted or removed the required fillet, rework/reflow
> the joint to a sound low-profile fillet and re-measure the ≤ 0.50 mm profile.

### REQUIREMENT J4-T3

> **Before the display is fitted, cover both inspected J4 joints together with
> a high-temperature polyimide electrical-insulation patch ≤ 0.10 mm thick.**
> The patch must fully isolate J4.1 (raw battery positive) and J4.2 (GND) from
> the display rear structure, contain no metal debris, and remain bonded after
> cleaning.  Trimmed conductor + insulation must remain < 0.80 mm total.

### Why the part was not changed instead

JST's PH series also has an **SMT** top-entry header (`B2B-PH-SM4-TB`) that
would remove the protrusion entirely.  It was **considered and declined**:

* `J4` is the **battery** connector, the one connector on this product a user
  or a repairer will plug and unplug.  A through-hole header's retention comes
  from its two soldered leads in plated barrels; an SMT header's comes from its
  pads.  **Mechanical retention on a repeatedly-mated power connector is worth
  more than avoiding one assembly operation.**
* Substituting it changes a land pattern on a **battery-path** connector and
  would require the full release suite on a board that is otherwise frozen.
* A lead trim is a routine, inspectable, zero-cost operation, and this board
  already carries a normative assembly-forming document
  (`IR_LEAD_FORMING.md`) for `D1` and `U6`.

`J4`'s position is **not** available to change either: D-241 placed it at doc
`(7.000, 113.000)` as the one part of the battery-protection chain that could
not join the column, *"north of the coax's western excursion, 8.59 mm from
`F1` and 0.7 mm clear of the cable"*.

---

## 3. Every other through-hole part, and why it needs nothing

| ref | body face | lead | why no trim requirement |
|---|---|---|---|
| `J6` JST PH (speaker) | **F.Cu** | 3.4 mm | protrudes on the REAR at doc `(38.000, 20.000)` — `y = 128.000` KiCad, **3.5 mm clear of `BATTERY_SHADOW`** (`y ≤ 124.5`) and outside every other limited region |
| `J5` Samtec `SSQ-124-02-G-S-RA` | F.Cu | 2.54 mm (RA tail, lead style −02) | `x = 65.900`, east of `BATTERY_SHADOW` (`x ≤ 64.0`) and outside every limited region |
| `D1` TSAL6100 | F.Cu | **formed and trimmed** | `IR_LEAD_FORMING.md`, NORMATIVE |
| `U6` TSOP38238 | F.Cu | **formed and trimmed** | `IR_LEAD_FORMING.md`, NORMATIVE |
| `J3` GCT USB4105 | F.Cu | **none** | its PTH entries are shell ground tabs and its NPTH are locating pins — a top-mount receptacle passes no lead through |
| `U1` ESP32-S3-WROOM-1 | F.Cu | **none** | the PTH entries on pad 41 are thermal vias inside the module's own thermal land |
| `SW9` C&K JS102011 | F.Cu | **none** | the two NPTH are moulded locating pegs; the terminals are surface-mount |
| `MK1` PUI mic | B.Cu | **none** | the NPTH is the acoustic port |
| `BOSS1`, `BOSS2` | — | **none** | M2 NPTH retention holes |

**MK10 refuses a through-hole footprint inside a height-limited region that has
neither a vendor lead figure nor one of these positive declarations**, so a
part moved into a limited region later cannot be silently skipped.
