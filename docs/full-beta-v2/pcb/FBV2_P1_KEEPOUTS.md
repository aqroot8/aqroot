# AQROOT Full Beta v2 — FBV2-P1 mechanical regions and keepouts

**Status: NORMATIVE for FBV2-P2 and for the enclosure CAD.**

> **RE-BASED 2026-08-24 at FBV2-EXP-002.** The board is now **72.000 × 148.000 mm** and grew
> **symmetrically**, so **every X coordinate below gains +1.0 mm** and `X_cavity = X_doc + 1.5`
> (was +2.5). Three regions changed by more than the shift and are restated here; the machine
> -generated current figures are [`FBV2_P1_METRICS.txt`](FBV2_P1_METRICS.txt).
>
> | region | now |
> |---|---|
> | `BATTERY_SHADOW` | **X 7.00 … 64.00, Y 23.50 … 98.50 — 57 × 75 × 8.0 mm MAX** (D-239). Rear height ≤ 1.2 mm, no through-hole lead |
> | `NFC_CLEAR_D48` / `NFC_METAL_D58` / `NFC_PLACEMENT_BOX` | centre **doc (31.800, 124.500)**, diameters unchanged |
> | `ANT433_REGION` | **X −1.40 … −0.60, Y 1.50 … 48.50 — RE-DERIVED, not shifted.** The old 2.2 mm reservation does not fit a 1.5 mm wall gap and never described anything real: the flex is **0.28 mm thick** and bonded flat to the wall, so it projects inward by its thickness plus adhesive. 0.6 mm of air remains to the board edge |
> | `COMM_RECESS` | **X 65.40 … 72.00, Y 77.50 … 140.00** — the 1 × 24 socket recess. **Internal length 62.5 mm against a 60.96 mm male body: 1.54 mm of play on a 2.54 mm pitch, so a one-position shift is physically impossible. Both ends CLOSED. The D-097 asymmetric key is no longer required** |
> | `COAX_915_CHANNEL` | **X −0.50 … 7.00, Y 24.00 … 110.00.** Clarified, not changed: it is a **CABLE lane, not a component keepout** — the Ø1.8 mm RG-178 lies over rear parts, so components **≤ 2.0 mm** may share it. What it forbids is anything the cable cannot lie over: a connector, a boss, a rib or an edge-capture rail |
> | `USB_APERTURE` / `USD_APERTURE` / IR windows / `SMA_APPROACH` | shifted +1.0 mm in X, otherwise unchanged. The IR barrier is **X 57.50 … 62.50** |
> | **`BOOT` service aperture — NEW** | **Ø2 mm recessed tool hole in the FRONT wall** at doc ≈ (28.3, 6.0). `SW1` is an SMD switch whose actuator faces out of the front shell, so the hole is **not** in the bottom wall and is therefore clear of both the microSD card-insertion path and the USB-C plug envelope |
> | **Qwiic aperture — NEW** | right wall at doc Y 67.7 … 75.6, for the `JST SM04B-SRSS-TB` side-entry cable |
 Created 2026-08-24 at
**FBV2-P1-001**, **superseded in part 2026-08-24 at FBV2-P1-002**. All coordinates use the
**P1 doc datum**: origin at the **lower-left board corner**, X → right, Y → **up**, millimetres.
`Y_kicad = 148.000 − Y_doc`.

> ### ⚠ READ THE RE-BASE HEADER BEFORE USING ANY COORDINATE IN SECTION 1 (D-759)
> Every X coordinate in section 1 is **PRE-REBASE** and gains **+1.000 mm**. The board is on
> the re-based datum and proves it: `U6` fits only the re-based `IR_RX_OPTICAL`, `J3` only the
> re-based `USB_APERTURE`, `MK1` only the re-based `MIC_ACOUSTIC`. Reading section 1 as current
> is not hypothetical — **D-758 did exactly that and corrected a real defect into a different
> one.** `mechanical_keepout_contract` MK1 now re-proves the datum against the board before any
> other clause is allowed to ask its question.

Regions marked **rule area** are real KiCad copper keepouts and are enforced by DRC. Regions
marked **mechanical** are enclosure-only and are drawn on user layers for review — **no copper was
created merely to visualise a zone, and none was created for plastic support.**

---

## 1. Named regions

| id | name | extent | layer | kind | rule |
|---|---|---|---|---|---|
| **A** | `DISPLAY_SHADOW` | X 3.39 … 59.93, Y 55.04 … 140.00 | `User.1` | mechanical | **F.Cu component height ≤ 0.8 mm.** No `J1`, no switches, no module |
| — | `DISPLAY_ACTIVE` | X 7.18 … 56.14, Y 60.80 … 134.24 | `User.1` | mechanical | 48.96 × 73.44 active area, for the front aperture |
| **B** | `BATTERY_SHADOW` | X 6.00 … 66.00, Y 23.50 … 98.50 | `User.2` | mechanical | **B.Cu height ≤ 1.2 mm. No through-hole lead may protrude into it.** 60 × 75 × 8.0 mm. **UNCHANGED at P1-002** |
| **C** | `NFC_CLEAR_D48` | **Ø48 circle, centre 30.800, 124.500** → X 6.80 … 54.80, Y 100.50 … 148.50 | `User.2` | mechanical | **Ø48 metal-free CLEAR region.** No boss, screw, shielding can, battery, speaker or cable. **B.Cu height ≤ 1.0 mm.** F.Cu copper is permitted — the reverse ferrite faces the PCB |
| **C2** | `NFC_PLACEMENT_BOX` | 48 × 48 square, same centre | `User.2` | mechanical | **placement / positioning tolerance envelope only**, per CTO §2A. It is NOT a metal exclusion |
| **D** | `NFC_METAL_D58` | **Ø58 circle, same centre** → X 1.80 … 59.80, Y 95.50 … 153.50 | `User.2` | mechanical | loop perimeter + 5 mm. **No metal: screws, bosses, shielding cans.** Supersedes the 58 × 51 rectangle; the circle is inscribed in it, so only the four corners are reclaimed |
| **E** | `SPEAKER_ZONE` | X 48.00 … 68.00, Y 1.00 … 21.00 | `User.2` | mechanical | Ø20 × 3 driver + **1.5–2.0 cm³ sealed rear cavity. NO B.Cu components at all.** **UNCHANGED** |
| **F** | `ANT433_REGION` | X −2.40 … −0.20, Y 1.50 … 48.50 | `User.3` | mechanical | 433 MHz flex **on the LEFT cavity wall**, 47 × 17 × 0.28 mm, adhesive to plastic. **Not on the PCB** |
| **G** | `COMM_RECESS` | X 59.90 … 70.00, Y 104.00 … 138.00 | `User.3` | mechanical | recess ≥ 1.5 mm below the outer wall, asymmetric **upper-edge** key, **both ends closed to ≤ 0.3 mm**, backing boss carries ≈ 33 N |
| **H** | `USB_APERTURE` | X 36.00 … 48.00, Y −3.50 … 1.20 | `User.3` | mechanical | shell aperture must clear the receptacle **mouth** and the cable overmould |
| **I** | `USD_APERTURE` | X 6.00 … 22.00, Y −21.00 … 1.20 | `User.3` | mechanical | aperture **plus ≈ 22 mm of card insertion travel outside the shell**, clear of the USB plug |
| **J** | `IR_TX_OPTICAL` | X 48.00 … 56.50, Y 140.00 … 148.00 | `User.4` | mechanical | TSAL6100, ±10°, axis **normal to the top face** |
| **J** | `IR_RX_OPTICAL` | X 61.50 … 70.00, Y 140.00 … 148.00 | `User.4` | mechanical | TSOP38238, ±45° FOV |
| **J** | `IR_BARRIER` | **X 56.50 … 61.50**, Y 140.00 … 148.00 | `User.4` | mechanical | **MANDATORY opaque barrier, full height, bonded to BOTH shells.** **WIDENED 3.0 → 5.0 mm at P1-002** so it fills the whole inter-window gap, touching neither window, and **it carries `BOSS2`** |
| **K** | `SMA_APPROACH` | X −1.00 … 11.00, Y 134.00 … 148.00 | `User.4` | mechanical | **Ø6.5 mm bulkhead hole at doc (5.000, 148.000)**, top panel, left half. Ø10.2 washer envelope drawn. **Bend radius ≥ 5 mm, service loop ≥ 15 mm, must not cross the IR path.** **MOVED from x 12.000 at P1-002** |
| **N** | `COAX_915_CHANNEL` | X −1.50 … 6.00, Y 24.00 … 110.00 | `User.4` | mechanical | **NEW at P1-002.** The reserved lane for the 915 MHz assembly between the board's left edge and the battery. **No boss, no rib and no edge-capture rail may occupy it.** The route polyline itself is drawn on the same layer |
| **M** | `MIC_ACOUSTIC` | X 0.50 … 5.50, Y 46.50 … 53.50 | `User.1` | **rule area** | gasket footprint on the **FRONT** face; **no tracks, vias or pours on any copper layer**; Ø1.05 mm NPTH carried by the `MK1` footprint |
| **L** | `BOSS1_KEEPOUT` | X 37.75 … 42.25, Y 9.75 … 14.25 — **RE-BASED: X 38.75 … 43.25** | `User.3` | **rule area** | M2, Ø2.2 NPTH at doc (40.000, 12.000) — **RE-BASED: (41.000, 12.000)**. **D-759: the board's rule area was already at the re-based 38.75 … 43.25; its HOLE was the one object on this board that never took the re-base** and sat at 40.000, so four pours stood 0.2505 mm from the edge of a 2.200 mm NPTH. The hole moved +1.000 mm; the pour now stands 1.1505 mm off it. Machine-checked by `mechanical_keepout_contract` MK2 |
| **L** | `BOSS2_KEEPOUT` | X 56.75 … 61.25, Y 142.75 … 147.25 — **RE-BASED: X 57.75 … 62.25** | `User.3` | **rule area** | M2, Ø2.2 NPTH at doc (59.000, 145.000) — **RE-BASED: (60.000, 145.000)**, inside the re-based IR barrier (X 57.50 … 62.50). **D-759: the board was already correct here and D-758 was wrong to move it** — 59.000 is the PRE-REBASE figure and at 59.000 the keep-out runs 0.750 mm into `IR_TX_OPTICAL`. Machine-checked by `mechanical_keepout_contract` MK2 and MK6 |
| **P** | `RIB_R1` | X 66.20 … 69.70, Y 24.00 … 44.00 | `User.3` | mechanical | rear non-metallic support pad. **Component-free, verified** |
| **P** | ~~`RIB_R2`~~ **RETIRED at D-759** | ~~X 66.20 … 69.70, Y 45.00 … 64.00~~ | `User.3` | mechanical | ~~rear support pad, behind the A/B control area~~ **NO LONGER COMPONENT-FREE.** D-719 re-floorplanned the `TPS63020` block into it: on the re-based footprint (X 67.20 … 70.70) `C28`, `C31`, `R39`, `R40` and `U12` are inside. A moulded rib there lands on a 3 × 3 mm QFN. **Replaced by `RIB_R2A`** |
| **P** | `RIB_R2A` — **NEW at D-759** | **X 65.50 … 69.00, Y 36.00 … 48.00** (re-based datum, stated directly) | `User.3` | mechanical | rear non-metallic support pad, **12.00 mm long, its top edge 1.00 mm from the A/B control row at Y 49.000** — closer to the load than the retired rib's centre was. Measured component-free on the back with 0.25 mm of margin, east of the re-based `BATTERY_SHADOW` (X 7.00 … 64.00), outside the Ø58 metal exclusion. A second bearing is available at **X 70.00 … 73.50, Y 58.00 … 71.50** (13.50 mm) if CAD wants the row bracketed. Machine-checked by `mechanical_keepout_contract` MK3 |
| **P** | `RIB_R3` | X 66.20 … 69.70, Y 76.00 … 97.00 | `User.3` | mechanical | rear support pad, mid-upper right margin |
| **P** | `RIB_B1` | X 44.00 … 47.60, Y 21.20 … 23.30 | `User.3` | mechanical | rear support pad, bottom strip below the battery |

**Withdrawn at FBV2-P1-002:** `NFC_ZONE` (the 48 × 48 square metal-free region — superseded by
`NFC_CLEAR_D48` + `NFC_PLACEMENT_BOX`), the 58 × 51 rectangular `NFC_METAL_KEEPOUT` (superseded by
`NFC_METAL_D58`), and `BOSS3_KEEPOUT` together with P1-001's `BOSS1` position at (3.5, 44.0).

## 2. ESP32 antenna keepout

Carried by the **`RF_Module:ESP32-S3-WROOM-1` footprint itself** as an all-copper-layer rule area —
it is not a drawn approximation. **Unchanged at P1-002.**

| item | value |
|---|---|
| Zone | **X 63.06 … 84.06, Y −4.00 … 44.00** (48 × 21 mm, the manufacturer's own keep-out polygon) |
| On-board portion | **6.94 mm** deep along the right edge |
| Off-board portion | **14.06 mm**, i.e. two-thirds of the keep-out is air beyond the board edge |
| Forbids | tracks, vias, pads, copper pours **and footprints**, on **every** copper layer |
| Antenna direction | **+X**, module rotated 270°, radiating through the right plastic wall |
| Clearance to the 433 flex | the flex is on the **left** wall — opposite side of the device |
| Clearance to the NFC clear region | **> 70 mm** |

> **Note for the collision reviewer.** The footprint's `F.CrtYd` bounding box **is** this keep-out
> polygon, not the module body. Collision review must use the module **body**,
> X 42.90 … 63.06, Y 9.90 … 30.10, and test the keep-out separately. `p1_geometry.py` does this
> automatically (`U1_BODY`); reviewing against the raw courtyard reports 58 false collisions.

## 3. Height rules enforced during placement

> **D-760: THESE THREE RULES HAD NEVER BEEN CHECKED AGAINST A PART, AND TWO OF
> THEM ARE NOT MET.** `mechanical_keepout_contract` **MK8** now measures every
> fitted part in each region against its package's published maximum height
> (`vendor` rows from the manufacturer's own document, `eia` rows the worst-case
> chip maximum for the case code). The measured rear profile is below. The
> difference between the *retained* limit and the *measured* profile is an
> **OPEN CAD ITEM**: closing it is a stack calculation that needs the enclosure,
> which does not exist yet. MK8 enforces the measured profile as a
> **no-regression ceiling** so the board cannot get taller without a decision.

| region | face | retained limit | **measured profile** | gap | what sets it |
|---|---|---|---|---|---|
| `DISPLAY_SHADOW` | F.Cu | ≤ 0.8 mm | **0.60 mm** | **MET, 0.20 mm spare** | `D2`/`D4`/`D5` SOT-563 |
| `BATTERY_SHADOW` | B.Cu | ≤ 1.2 mm | **1.80 mm** | **+0.60 mm** | `C26`, `C29`, `C30` 1206 bulk MLCC (1.6 ± 0.2 mm); also `C33`, `C64`, `D9` |
| `NFC_CLEAR_D48` | B.Cu | ≤ 1.0 mm | **1.40 mm** | **+0.40 mm** | `J7` JST ACH (1.4 mm, JST `eACH`); also `C45`/`C47`/`C49`/`C51`/`C83`/`C84` 0805 and `D10`–`D12` SOD-323 |

**MITIGATION IN PLACE FOR THE PACK.** The `BATTERY_SHADOW` parts are hard points
against a soft pouch, so `OFF_BOARD_BOM.md` now REQUIRES a **0.5 mm compliant
insulating sheet** over the rear face under the cell. That spreads the load and
insulates the pack from rear copper; **it does not close the 0.60 mm gap** and is
not offered as if it did.

| region | face | limit | source |
|---|---|---|---|
| `DISPLAY_SHADOW` | F.Cu | **≤ 0.8 mm** | measured Beta-DM limit, retained |
| `BATTERY_SHADOW` | B.Cu | **≤ 1.2 mm** | measured Beta-DM limit, retained |
| `NFC_CLEAR_D48` | B.Cu | **≤ 1.0 mm** | mechanical spec §3.3 Column A rear air gap |
| `SPEAKER_ZONE` | B.Cu | **no components** | sealed acoustic cavity |
| any through-hole part | both | its **leads and holes** occupy both faces | prevents pins entering the battery, NFC or speaker volume |

## 4. Objects recorded INSIDE the Ø58 metal exclusion

Neither is a screw, a boss or a shielding can, so neither breaches the rule as written; both are
recorded so no later reader has to rediscover them.

| object | inside by | note |
|---|---|---|
| battery pouch foil | **3.000 mm** | 1.500 mm inside the superseded rectangle. Zero overlap with the **clear** region (2.000 mm gap) — the locked policy N-5 holds |
| `D1` `TSAL6100` leadframe | **1.381 mm** | 3.619 mm outside the Ø48 loop perimeter. Was inside the superseded rectangle too. Cannot move without breaking the ≥ 15 mm IR TX↔RX rule |
| `J7` JST `BM02B-ACHSS-GAN-ETF` — **RECORDED at D-760** | **5.870 mm** inside the Ø58; **0.870 mm inside the Ø48 CLEAR region** | The NFC antenna's own connector, at doc (54.000, 118.000), **23.130 mm from the Ø48 centre — 0.130 mm OUTSIDE the Ø46 coil itself**, so the coil does not sit on it; only the Ø48 margin ring does. It is not a screw, a boss or a shielding can, so it does not breach the Ø58 rule as written. It IS where the antenna's twisted pair lands, and at **1.4 mm** it stands 0.4 mm above the Ø48 rear-air-gap figure — see §3. Recorded so no later reader has to rediscover it |

## 5. What is deliberately NOT here

- **No copper pours, no tracks, no vias.** FBV2-P2 owns those.
- **No enclosure CAD.** Every region above is a reservation the CAD must honour, not a model.
- **No stack-up change.** The layer stack and netclasses are the pre-P1 ones. The only
  `.kicad_dru` change is §15, the scoped `U1` thermal-pad hole-size guard.
- **No copper pad for plastic support.** The four `RIB_*` regions are mechanical reservations on
  `User.3` and carry no copper.
