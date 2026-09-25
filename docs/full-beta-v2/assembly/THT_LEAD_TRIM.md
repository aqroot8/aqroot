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

## 2. `J4` — D-781 MANUAL BATTERY PIGTAIL.  ITS FRONT-SIDE JOINTS MUST STAY LOW.

D-781 removed the fitted JST-PH board header. `J4` now reuses the existing two
0.75 mm plated holes as a **manual 26-AWG wire land**.  The exact detachable
harness, wire identities, polarity and acceptance criteria are frozen in
[`BATTERY_HARNESS.json`](BATTERY_HARNESS.json).  The red/black board-side wires
enter from the **rear (`B.Cu`)**, are soldered on the **front (`F.Cu`)**, and the
two solder joints lie inside `DISPLAY_SHADOW` beneath the panel.

| | |
|---|---|
| Board-side conductors | **26 AWG** red/black pre-crimps: Molex `2175012101` / `2175011101` |
| Detachable housing | Molex Micro-Lock Plus 2.0 `5055700201`, 2 circuits |
| Board land | existing `J4.1/J4.2` 0.75 mm nominal PTH pair; **no board connector is fitted**. Supplier/assembler acceptance requires **≥0.70 mm finished plated-hole diameter** and one exact pre-crimp lead must pass freely before all five units. |
| Polarity | cavity 1 = BAT+ / red / `J4.1`; cavity 2 = GND / black / `J4.2` |
| Where solder emerges | `J4.1` and `J4.2`, both inside `DISPLAY_SHADOW` |
| Display-shadow allowance | **0.80 mm** above `F.Cu` |

### REQUIREMENT J4-T1

> Insert the stripped 26-AWG conductors from the **rear**, solder on `F.Cu`, then
> trim each finished conductive profile to **≤ 0.50 mm above the `F.Cu` surface**.
> No sharp conductor, loose strand or clipped fragment may remain.  The 0.50 mm
> limit is an assembly requirement, not a vendor lead-length calculation.

### REQUIREMENT J4-T2

> Solder, trim, clean, then inspect — **in that order**.  Do not pre-cut to a
> guessed insertion depth.  After cutting, inspect both barrels and fillets; if
> cutting disturbed a joint, rework/reflow it and re-measure the ≤0.50 mm profile.
> After the joint/profile inspection and cleaning, form the relaxed rear service loop and apply **DOWSIL 3145 RTV MIL-A-46146 gray** to the **insulated** red/black pigtails over clean B.Cu solder mask, beginning beyond the inspected solder fillets. Bond both insulated leads to the PCB for at least **8 mm** and preserve **≥35 mm free wire from the Micro-Lock housing before bundling**. Cure under the ONE qualified hold of the packaged harness record (`BATTERY_HARNESS.json` `strain_relief.cure`, D-800): apply and cure at 25 ± 5 °C and 40–70 % RH with the bead ≤ 1.0 mm; the board may be MOVED — never the joint loaded — only after a passed tack-free check and no earlier than 4 h; the qualified process release is the full **≥ 72 h** hold, and no pull test, thermal test, enclosure retention or closure check, or shipment happens before it. Do not allow cured adhesive, wire, or the hard solder-wick transition to bear on the LiPo pouch or coax. Disconnect by releasing/gripping the two connector housings — **never pull the wires**.

### REQUIREMENT J4-T3

> **Before the display is fitted, cover both inspected J4 joints together with
> a high-temperature polyimide electrical-insulation patch ≤ 0.10 mm thick.**
> It must fully isolate raw BAT+ (`J4.1`) and GND (`J4.2`) from the display rear
> structure, contain no metal debris, and remain bonded after cleaning.  Trimmed
> conductor + insulation must stay **< 0.80 mm total**.

### REQUIREMENT J4-T4

> Build and inspect the pigtail exactly to `BATTERY_HARNESS.json`: verify cavity
> polarity by DMM before battery connection; verify an exact `217501` 26-AWG tinned lead passes a **≥0.70 mm finished J4 hole** freely with no strand shaving before soldering all five boards; perform the specified terminal pull/retention check and the frozen DOWSIL-3145 strain-relief/service-loop inspection; verify the Micro-Lock can be disconnected by the housings without loading the PCB joints; and record the first-article worst-case thermal-rise result.

### Why a manual pigtail is used

The prior `B2B-PH-K-S(LF)(SN)` board header is rated below the board's modeled
full-feature worst-case battery current.  D-781 therefore keeps the proven J4
copper and hole locations but moves the detachable interface off-board to a
**2.6 A-rated 26-AWG Molex Micro-Lock Plus harness**.  This avoids disabling
sub-GHz, NFC or IR merely to protect an underspecified connector and makes the
current rating explicit in the assembly artifact.  No protected copper moved.

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
