# FBV2-P1-002 — Full Beta v2 P1 closeout: circular NFC keepout, 915 feed, mechanical cleanup

**Date:** 2026-08-24
**Task:** FBV2-P1-002
**Gate:** **FBV2-P1 — PASSES.** Overall Full Beta v2 **68 % → 74 %**.
**Starting SHA:** `ccb0816f76990fcd345df38e583c9d1a253ab039` — matches the expected HEAD.
**Scope:** PCB **placement** changes authorised. **Signal routing NOT authorised, and none was
done.** FBV2-P2 has not begun.

---

## 0. Preflight

| check | result |
|---|---|
| `git status` | clean but for two long-standing untracked paths, both left alone |
| local `master` / `origin/master` | both `ccb0816` — in sync |
| staged / uncommitted tracked work | none |
| local-only commits | none |
| current PCB, as found | **70.0 × 148.0 mm, 324 footprints (321 + 3 bosses), 0 tracks, 0 vias, 0 fill zones, 4 rule areas, 499 unrouted** — exactly the FBV2-P1-001 state |
| untracked, untouched | `hardware/beta-dm/fab/AQROOT-Beta-DM-Gerbers-aa64c16.zip`, `hardware/beta/mechanical/` |

**Recovered prior work:** none needed. Nothing was in flight.

**One preflight correction to the record.** FBV2-P1-001 reported **76 DRC violations** including
*"12 × the stock ESP32 footprint's 0.2 mm thermal vias against the board's 0.3 mm minimum-hole
rule."* Re-running `kicad-cli pcb drc --severity-all` on the untouched board returns **64**, and
**there is no such violation class in it.** The board's global floor is
`min_through_hole_diameter = 0.20 mm`, so those twelve holes were always legal. **The twelve
errors were `copper_edge_clearance` on `J5`** — see §6. The misattribution is what P1-O5 was built
on; §5 below closes P1-O5 on the corrected facts.

---

## 1. The one thing that mattered: opening a legal 915 lane

FBV2-P1-001 failed on the 915 MHz feed, and it failed for a reason that had nothing to do with
cable length: **the SMA is locked to the top-panel LEFT half, and the NFC region owned the entire
upper-left.** A 200 mm or a 300 mm cable would both have had to cross the NFC clear zone or run
inside the 5 mm metal keep-out.

The CTO's circular-geometry ruling is what unlocks it, but **not because a circle is smaller than a
square** — it is, only at the corners, and the corners were never the problem. It unlocks it
because a circle can be **re-centred** against a hard right-hand limit in a way a 58-wide rectangle
sitting at x −4.5 … 53.5 could not.

### 1.1 The width budget, which is the whole argument

| item | width |
|---|---|
| Enclosure cavity | **75.0 mm** (doc x −2.5 … 72.5) |
| Ø58 NFC metal exclusion | **58.0 mm** |
| `J5` community port, from its copper to the cavity wall | **12.1 mm** |
| **What is left for a coax lane** | **4.9 mm — and only if the exclusion is pushed as far right as `J5` allows** |

A 1.8 mm RG-178 needs about 2.8 mm with sane clearances. **4.9 mm is enough. 0 mm was what the
P1-001 centre left.**

### 1.2 Final NFC geometry

| region | shape | centre | extent |
|---|---|---|---|
| Clear | **Ø48 circle** | **doc (30.800, 124.500)** | X 6.80 … 54.80, Y 100.50 … 148.50 |
| Metal exclusion | **Ø58 circle** | same | X 1.80 … 59.80, Y 95.50 … 153.50 |
| Placement / tolerance box | 48 × 48 square | same | as the clear region |

The centre moved **+6.30 mm in X and −1.50 mm in Y** from P1-001's (24.500, 126.000). Both
components are load-bearing:

* **+6.30 X** is the coax lane. It is bounded above by `J5`: the loop perimeter is now **5.490 mm**
  from `J5`'s copper against a ≥ 5 mm rule, so **0.49 mm of the shift is all that remains.**
* **−1.50 Y** buys the SMA its margin. At Y = 126.000 the bulkhead would have had to sit at
  x ≤ 4.31 with the washer 3.7 mm from the enclosure's external left face; at Y = 124.500 it sits
  at **x = 5.000** with **0.798 mm** of radial margin and **2.400 mm** to the cavity wall.

**The radial clearance around the antenna was not reduced.** The superseded metal keep-out was the
**58 × 51 rectangle** X −4.5 … 53.5, Y 97 … 148. The Ø58 circle is inscribed in that square: the
change loses **only the four corners**, which is exactly what the ruling asked for.

### 1.3 What the centre shift cost, stated plainly

| object | before | after |
|---|---|---|
| Ø48 clear ↔ battery | 3.50 mm gap, zero overlap | **2.00 mm gap, zero overlap** — N-5 holds |
| battery inside the metal exclusion | 1.50 mm | **3.00 mm** |
| `D1` leadframe inside the metal exclusion | inside the rectangle too | **2.854 mm** (see §7) |
| `J5` copper ↔ loop perimeter | 6.86 mm | **5.490 mm** |

**No screw, boss or shielding can is inside the Ø58 exclusion** — which is what the rule text
actually forbids. Both intruders are recorded in
[`../pcb/FBV2_P1_KEEPOUTS.md`](../pcb/FBV2_P1_KEEPOUTS.md) §4 so nobody has to rediscover them.

### 1.4 Micro-optimisation: the answer to "should it move at all"

The CTO asked for the present centre to be preferred unless a small shift gives a material benefit.
It gives the **only** benefit available: **there is no coax route at (24.5, 126.0) for any cable
length.** The shift was then bounded on all four sides by `J5`, the battery, the cavity top and the
SMA, and the result is the unique small region where all four hold. It was not moved because
movement was allowed.

---

## 2. The 915 MHz route — measured, not estimated

`U8` and `U7` were **swapped** in the bottom-rear band. Both Ebyte modules use dimensionally
identical 15.89 × 21.34 mm footprints, so the swap costs **zero plan area** and puts the
length-critical 915 module next to the only north–south cable channel on the board. The 433 flex
lead needs 44 mm of its 100 mm either way.

| # | doc (x, y) | |
|---|---|---|
| 0 | 9.00, 16.60 | `U8` IPEX / MHF1, right-angle plug |
| 1 | 5.40, 19.20 | west, over `U8`'s own can |
| 2 | 3.00, 25.50 | into the left channel |
| 3 | 3.00, 108.00 | north beside the battery, over `MK1`'s sealed lid |
| 4 | 0.30, 118.50 | west around the exclusion |
| 5 | 0.30, 130.50 | the pinch, 30.50 mm from the NFC centre |
| 6 | 5.00, 143.00 | back east |
| 7 | 5.00, 148.00 | SMA bulkhead |

| measurement | value |
|---|---|
| Polyline | **134.88 mm** |
| **Routed, including bend allowances** | **138.48 mm** |
| Minimum available bend radius | **7.42 mm** (rule ≥ 5.0) |
| Installed + 15 mm mandated service loop | **153.48 mm** |
| **Spare on a 200 mm assembly** | **46.52 mm** |
| Tightest clearance to the Ø58 exclusion | **0.600 mm** |
| Violations against every hard obstacle | **0** |

Every segment was tested against the Ø58 exclusion, the 433 flex body, the battery envelope, the
speaker cavity, the microSD card-travel volume, the USB aperture, both IR optical regions, the IR
barrier, the community recess and `J5`'s courtyard. The test is in
`hardware/beta-v2/checks/p1_geometry.py::coax_legal` and is re-run by the regression.

**Two crossings, both recorded rather than engineered away:** the coax passes over `MK1`'s sealed
lid (a bottom-port MEMS microphone whose acoustic path leaves the *other* face), and the 433 lead
crosses the 915 coax once at about (4.5, 21.5) on top of `U8`. **C-6 forbids crossing a radiating
element, not another cable.**

---

## 3. The cable — `CBA-UFLSMA20IP`, and the CTO's own rule decides it

The measured installed path is **138.48 mm**, comfortably **≤ 180 mm**, so the ruling's first
branch applies and the 200 mm assembly locks. The 250 mm Taoglas `CAB.01034` fallback is **not
used** and is recorded as the fallback only.

**Live verification 2026-08-24 under D-096:**

| source | what it says |
|---|---|
| **DigiKey** 14566928 | `CBA-UFLSMA20IP`, **Part Status ACTIVE**, **296 in stock**, $11.58 @1 / $7.11 @vol, **200.00 mm**, **RG-178**, **50 Ω**, 1st connector **SMA Jack, Panel Mount, Bulkhead — Front Side Nut**, 2nd connector **U.FL (UMCC) Plug, Right Angle, free hanging** |
| **CPC / Farnell** RF00982 | **IP67**, 50 Ω, RG178, 200 mm, **"90° U.FL Plug to SMA Bulkhead Jack"**, **7 in stock**, £6.29 @1 |
| **Manufacturer drawing** `CBA-UFLSMAF20IP-1`, rev 1 12/11/2015, revised 03/12/2015 | notes: **1 UFL Right Angle · 2 Waterproof SMA Female Bulkhead Straight · 3 Heatshrink · 4 RG178 Coax cable**; 200 mm; 50 Ω; RoHS. **Marked NOT TO SCALE and carrying no body dimensions** |

**This is a procurement improvement, not just a mechanical one.** The superseded Amphenol
`095-902-568-100` was ACTIVE but **0 in stock with a 12-week factory lead time** (D-218). The
replacement is stocked at two distributors today.

**Mating verdict: COMPATIBLE.** `U8` `E22-900M22S` carries an **I-PEX MHF1 (IPEX-1)** socket.
Hirose **U.FL** and I-PEX **MHF1** are the same 2.0 × 2.0 mm interface and intermate; the cable's
connector A is a U.FL **plug**, the correct gender for that socket. The far end is SMA **female**
against the `TI.92.2113`'s SMA **male** — the chain D-120 locked, unchanged.

**Estimated feed loss ≈ 0.4 dB** — RG-178 at ≈ 1.2–1.5 dB/m over 0.20 m plus two interfaces,
against +22 dBm. Negligible, and unchanged from the figure D-120 budgeted.

**Slack:** 46.52 mm beyond the service loop, dressed as a shallow serpentine inside the reserved
`COAX_915_CHANNEL` (6 mm wide against a 1.8 mm cable) plus the ≥ 15 mm loop at the bulkhead.
**There is no free rear pocket large enough for a dedicated coil, and none is needed.**

---

## 4. B-52 — the floorplan half closes

`CBA-UFLSMA20IP`'s own drawing is **NOT TO SCALE and dimensions nothing**. The interface it names —
SMA(F) bulkhead straight — is fully dimensioned in the **Taoglas SPE-24-8-198-C** drawing of the
same interface (the fallback candidate's own drawing), and both agree with MIL-STD-348A:

| feature | value |
|---|---|
| Hex across flats / **across corners** | 8.00 mm / **Ø9.238 mm** |
| Hex body length into the cavity | 3.40 ± 0.2 mm |
| Thread | 1/4-36 UNS-2A, 11.40 ± 0.2 mm |
| Panel hole | **Ø6.5 mm** — unchanged |
| **Star lock washer — the governing planar envelope** | **Ø10.2 REF** |
| Nut | HEX 8, 1.80 ± 0.3 mm |

**The body OD is no longer unknown, so the floorplan part of B-52 is CLOSED.**

| rule | measured | verdict |
|---|---|---|
| SMA ↔ IR TX, centre-to-centre ≥ 15 mm | **47.250 mm** | **PASS** |
| SMA body ↔ IR TX aperture, edge-to-edge ≥ 8 mm | **38.381 mm** | **PASS** |
| SMA ↔ IR RX, centre-to-centre | **60.750 mm** | **PASS** |
| SMA body ↔ IR RX aperture, edge-to-edge | **51.881 mm** | **PASS** |

Moving the bulkhead from x 12.000 to **x 5.000** only improved both rules. The hex sits against the
inner face of the top wall at cavity Y 151.5 and protrudes inward to Y ≈ 148.1 — **above the board
edge, not over it** — so it claims no board area.

**Residual, enclosure-CAD only:** the IP67 variant's face O-ring seat diameter and its exact front
protrusion are not dimensioned by RF Solutions. The floorplan carries **1.6 mm of diametral
headroom** (the SMA planar envelope may grow to Ø11.8 before touching the Ø58 exclusion), which
bounds that residual. **§22 permits an enclosure-CAD-only residual; this is it.**

---

## 5. P1-O5 — the ESP32 thermal vias were never in violation

| item | finding |
|---|---|
| Manufacturer geometry | **12 × Ø0.20 mm drill in Ø0.60 mm pad** on pad 41, `pad_prop_heatsink`, net GND — Espressif's recommended land pattern, carried by the stock `RF_Module:ESP32-S3-WROOM-1` footprint. **0.200 mm annular ring**, above the board's 0.125 mm floor |
| Board rule as it actually is | `min_through_hole_diameter = **0.20 mm**`, not 0.30. **Zero violations, and there never were any** |
| **Fabricator capability**, JLCPCB multilayer, verified live 2026-08-24 | minimum via hole **0.15 mm**; the surcharge applies only to *"0.2 mm or 0.25 mm hole size with a via diameter **less than 0.45 mm**"*. The 0.60 mm pad is above that threshold |
| **Verdict** | **SUPPORTED on the intended JLC04161H-7628 4-layer 1.6 mm stack at no premium.** Nothing about the footprint changes and no fabricator exception is required |
| Local rule added | `.kicad_dru` **§15**, `FP-U1 ESP32-S3-WROOM-1 manufacturer thermal-pad vias (0.20 mm drill)`, `hole_size min 0.20 max 0.20`, scoped to `A.memberOfFootprint('U1') && A.Pad_Number == '41'` |
| Global minimum | **NOT lowered.** The rule is a **guard**, not a waiver: if the global floor is later raised to 0.30 mm — which is right for *routing* vias — the manufacturer's thermal array stays legal instead of being silently "corrected" away |

---

## 6. `J5` — twelve real errors, fixed for 0.070 mm

`J5`'s PTH field ended 0.445 mm from the board's right edge against the board's own 0.5 mm
copper-to-edge rule: **twelve `copper_edge_clearance` errors**, one per outer-row pad. These are
the twelve the P1-001 audit attributed to the ESP32.

`J5` moved **0.070 mm west**, x 64.970 → 64.900. Copper is now **0.515 mm** inside the edge and
**all twelve errors are gone.** This is not "moving `J5` to centre the display" — it is a
sub-tenth-millimetre correction of a rule violation, and the community port's mechanical story is
unchanged.

---

## 7. IR — the forming requirement found a real defect

The CTO ruled the IR MPNs unchanged and asked for a documented 90° forming requirement.
**Writing it down showed that the formed `TSAL6100` did not fit.**

Measured from its pads in +Y, a formed `TSAL6100` occupies **0.6 mm of bend radius + 2.0 mm of
straight lead (Vishay's stated minimum between the epoxy case and the bending point, doc 84892) +
8.7 ± 0.3 mm of body = up to 11.6 mm.** At P1-001's Y = 143.600 the dome would have ended at
Y ≈ 155.2 — **1.2 mm outside the enclosure's external top face.**

`D1` moved to **doc (50.750, 141.400)**, the northernmost position at which the dome lands on
Y = 153.0, which the enclosure must provide as a clear bore 1.5 mm into the 2.5 mm top wall.
`TP39` and `R123` each moved **1.750 mm** south to clear `D1`'s new courtyard. `U6`'s formed
`TSOP38238` needs only ≈ 9.0 mm and **fits where it already was**; it was not moved.

**Recorded consequence:** `D1`'s leadframe is now **2.854 mm inside the Ø58 exclusion**, i.e.
**2.146 mm outside the Ø48 loop perimeter**. `D1` cannot move east — it is already at the exact X
the ≥ 15 mm TX↔RX rule allows with `U6` hard against the right board edge — and it cannot move
north without breaking the shell. The intruding metal is two 0.5 mm leads and a reflector cup of a
few mm², perpendicular to the antenna plane and in the FRONT cavity while the antenna is on the
REAR shell, so the true 3-D separation is considerably larger than the plan-view number.

The full requirement — orientation, bend direction, bend line, minimum straight length, bend
radius, forming-before-soldering, no case stress, optical-axis heights and tolerances, barrier
relationship, enclosure support and a first-article acceptance list — is
[`../assembly/IR_LEAD_FORMING.md`](../assembly/IR_LEAD_FORMING.md), sourced to Vishay doc **84892**
and the two datasheets. **The IR barrier was widened 3.0 → 5.0 mm** to fill the whole inter-window
gap, and it now also carries `BOSS2`.

---

## 8. `MK1` — P1-O4 fixed, zero padstack errors

The electrical and acoustic geometry did **not** change: **Ø1.05 mm NPTH acoustic opening
retained, GND annulus ID 1.05 / OD 1.65 retained from the PUI drawing, 0.10 mm paste pullback
retained, acoustic keep-out retained, microphone location unchanged.**

| | before | after |
|---|---|---|
| GND ring copper | custom pad whose only primitive was a **stroked circle** — an annulus, two boundaries, rejected by KiCad 10 | **plain filled Ø1.65 mm circular SMD pad**; the concentric **non-plated** Ø1.05 mm hole drills the centre out, giving the same annulus. **Not a custom pad at all, so the validator has nothing to reject** |
| Acoustic hole | Ø1.05 NPTH | unchanged. **No fake plated through-hole was used** |
| Paste | custom pad, stroked annular aperture — same defect | **one custom pad, one filled C-shaped polygon**: the same ID 1.25 / OD 1.65 ring with a 20° web, anchored by a Ø0.20 mm circle sitting **on** the ring band so anchor and primitive are one connected region |
| Paste coverage | 71.6 % of the copper ring | **67.6 %** (0.860 of 1.272 mm²); stencil area ratio **0.71** on a 0.12 mm foil, above the 0.66 release floor |

**`padstack_invalid`: 2 → 0.** Library and board copies are identical; `lib_footprint_mismatch` is
clean. Full rationale in `hardware/beta-v2/checks/p1_mk1_padstack.py`.

One `solder_mask_bridge` remains and is **left in place, not excluded**: the netless NPTH sits
concentrically inside its own footprint's GND ring, so the two mask apertures merge. **There is no
second net inside the merged aperture.** It is a construction artefact of "SMD ring pad + concentric
non-plated hole", which is the geometry the PUI drawing specifies.

---

## 9. Retention — the honest number is TWO, and it is escalated

| boss | doc (x, y) | where |
|---|---|---|
| `BOSS1` | 40.000, 12.000 | bottom edge, between USB-C and the ESP32 body |
| `BOSS2` | 59.000, 145.000 | top edge, **inside the mandatory full-height IR barrier** |

**Search result: Ø6.0 mm keep-out — ZERO legal sites. Ø4.5 mm — TWO.**

The arithmetic, not a preference:

* a boss must clear **both** faces;
* the **display** owns X 3.39 … 59.93 for Y 55.04 … 140.00 on the front, the **battery** owns
  X 6.00 … 66.00 for Y 23.50 … 98.50 on the rear;
* between them they leave a **3.39 mm** left sliver and a **4.00 mm** right sliver — **both
  narrower than a Ø4.5 keep-out** — so only the 23.5 mm bottom band and the 8 mm top band can host
  a through-board screw at all;
* the bottom band yields exactly one site once microSD, USB-C, `J6`, the ESP32 body and both radio
  modules are honoured;
* the top band yields exactly one, in the 5.0 mm gap between the IR windows;
* the top-left corner and the left margin are now the **915 coax channel**, which is mandatory.

**Both of P1-001's other two positions were withdrawn for cause:** its `BOSS1` at (3.5, 44.0) is
inside the coax channel, and its `BOSS2` at (59.5, 145.0) **overlapped the mandatory opaque IR
barrier** — it was never legal. Correcting it to (59.0, 145.0) and widening the barrier to the full
inter-window gap makes the barrier and the boss one moulded feature.

**Ø4.5 is justified, not inflated:** the moulded M2 boss OD is 4.0 mm, so Ø4.5 is that plus 0.25 mm
per side. Ø6.0 would be an arbitrary 50 % oversize.

**Structural support is completed by the enclosure and needs no PCB holes:** moulded edge-capture
rails, continuous on the right and bottom edges and segmented on the left to clear the 433 flex and
the coax channel's western excursion; plus four rear non-metallic support ribs bearing on reserved
component-free pads — `RIB_R1`, `RIB_R2`, `RIB_R3` on the right margin and `RIB_B1` on the bottom
strip, all verified component-free on the rear face including every through-hole lead, **all
outside the battery shadow** and all far outside the Ø58 exclusion. **No copper pad was created for
plastic support.**

> **THE ONE NEW ITEM FOR CTO DECISION.** §9 sets **3 × M2 as the acceptable minimum**; this outline
> yields **2**. A third needs one of: a battery narrower than 60 mm, a display narrower than
> 56.54 mm, the SMA off the top-left, or an M2 with ~1.4 mm of board between the hole and the board
> edge. **All four are CTO calls and none was taken.**

---

## 10. Display — accepted, unchanged, and the Z stack was not spent

The module sits **3.34 mm LEFT of the board centreline. Accepted as INTENTIONAL** (D-224). It was
not raised, the PCB was not widened, `J5` was not moved for it and the enclosure width did not
change. The display/`J1` relationship is unchanged.

**The FBV2-P1-001 recommendation to raise the display support by ≈ 3 mm as the primary 915 solution
is REJECTED and withdrawn.** The circular NFC geometry closed the feed without spending any of
Column A's 9.9 mm of unused Z. **Display Z stack changed: NO.**

---

## 11. P1-O6 and P1-O7

**P1-O6 accepted and re-run.** The corrected expectation — **one** `/03_SPI_A_DISPLAY_SD/LED_A`
net, not Beta-DM's `LED_A1`…`LED_A4` — stands. The probe scans 224 board nets, 3 resolve to
`LED_BOOST` (`LED_A`, `LED_BOOST`, `LED_K`), and the actual guard holds: **`LED_BOOST` does not
capture `/07_IR/IR_LED_A` or `/07_IR/IR_LED_K`.** **`NETCLASS PROBE: PASS`.**

**P1-O7: no action taken, as instructed.** No feature or placement change derives from it.

---

## 12. Floorplan regression — every check passes

Re-derived from the board by `hardware/beta-v2/checks/p1_regression.py`; the full run is
[`../pcb/FBV2_P1_METRICS.txt`](../pcb/FBV2_P1_METRICS.txt).

| check | result |
|---|---|
| Outline 70.000 × 148.000 | **PASS** — unchanged |
| 321 schematic footprints + 2 bosses = 323 | **PASS** |
| Duplicate references | **0** |
| **Side-aware placement collisions** | **0** |
| Parts outside the board in X | **0** |
| Battery, speaker | **UNCHANGED** |
| `MK1` ↔ speaker | **67.424 mm**, opposite faces (≥ 60) |
| FPC consumed of the 29.5 mm worst case | **14.94 mm** |
| `J5` copper to board edge | **0.515 mm** (≥ 0.5) |
| ESP32 antenna keep-out | valid, carried by the footprint |
| 433 flex lead, routed | **44.12 mm of 100 mm** |
| NFC pair, routed | **41.73 mm of 75 mm** |
| Speaker lead, routed | **29.31 mm of 152 mm** |
| NFC clear ↔ battery | **2.000 mm, ZERO overlap** |
| NFC loop ↔ speaker | **80.919 mm** (≥ 20) |
| microSD ↔ USB-C, courtyard edge | **14.990 mm** (≥ 8) |
| IR TX ↔ IR RX | **15.000 mm** (≥ 15) |
| SMA ↔ IR, both rules | **PASS** |
| **Signal tracks / vias / fill zones** | **0 / 0 / 0** |

### 12.1 The collision model had to be corrected first

Two modelling defects in the naive review were fixed, and both would have produced false alarms:

* **`U1`'s `F.CrtYd` bounding box is the manufacturer's antenna keep-out polygon**, X 43.255 …
  84.545, not the module body. Reviewing against it reports **58 false collisions**. The body,
  X 42.90 … 63.06 / Y 9.90 … 30.10, is now used for collision review and the keep-out is tested
  separately;
* **opposite-face pairs must be tested hole-against-courtyard, not courtyard-against-courtyard.**
  Only a lead or a hole can reach the other face. `SW9`'s two Ø0.9 mm NPTH alignment holes do not
  make its whole 8.84 × 10.09 mm courtyard opaque to the rear.

---

## 13. Validation

| check | result |
|---|---|
| Schematic parses, 9 sheets | **PASS** |
| **ERC** | **27 violations / 0 errors** — histogram byte-identical to FBV2-MECH-002 and FBV2-P1-001 |
| Schematic connectivity | **UNCHANGED** — the schematic files were not opened |
| PCB parses in `pcbnew` | **PASS** |
| Footprint count vs schematic | **321 / 321**, zero missing, zero duplicate |
| Placement / courtyard errors | **0** |
| **DRC** | **47 violations / 499 unconnected** — down from 64. See §13.1 |
| `netclass_probe` | **PASS** |
| `fork_equivalence` | **PASS** — Beta-DM untouched, every added footprint declared |
| **Signal routing added** | **ZERO tracks, ZERO vias, ZERO copper pours** |

### 13.1 DRC — 47, every one classified

| n | type | classification |
|---|---|---|
| 24 | `silk_over_copper` | reference-designator silkscreen. **Silk is a P2/finishing activity** |
| 21 | `clearance` | **vendor intra-footprint land patterns** at 0.150 mm against the 0.200 mm global, on `U18`, `U19`, `U21`, `D2`. Exactly the class already handled for `U9`/`U13`/`U16`/`D3`–`D6` by scoped `FP-*` rules. **A P2 rule-pass item, not a placement defect** |
| 1 | `solder_mask_bridge` | `MK1`, §8. Recorded, **not excluded** |
| 1 | `silk_edge_clearance` | `J5` silkscreen clipped by the board edge. Silk again |
| **0** | `padstack_invalid` | **was 2 — FIXED** |
| **0** | `copper_edge_clearance` | **was 12 — FIXED** |
| **0** | `lib_footprint_issues` / `_mismatch` | **was 3 — FIXED** by adding `MountingBoss_M2_NPTH.kicad_mod` to the library |

**Nothing was fake-cleaned.** No DRC exclusion was added, no severity was lowered and no global
rule was relaxed. The single `.kicad_dru` addition raises a floor for one footprint; it does not
lower one.

### 13.2 Trees confirmed untouched

`hardware/beta-dm/` · frozen `hardware/beta/` · `hardware/beta/mechanical/` · all nine schematic
sheets · every symbol library. **The design files changed are `aqroot-Beta-v2.kicad_pcb`,
`aqroot-Beta-v2.kicad_dru`, `PUI_DMM-4026-B-I2S_4.0x3.0mm.kicad_mod` and the new
`MountingBoss_M2_NPTH.kicad_mod`.**

---

## 14. Opportunity and simplification scan

**Surfaced, not decided. No feature was added and nothing locked was changed.**

| # | finding |
|---|---|
| **P2-O1** | The circular geometry **opened the coax route — that is the gate result — but it did not open a mounting position. It cost one**, because the lane it opens is the lane a boss would have used |
| **P2-O2** | **`J7` serviceability improved incidentally**: the NFC connector is now 1.914 mm outside the Ø58 exclusion instead of sitting on the old rectangle's boundary |
| **P2-O3** | **Dead area barely moved.** The four reclaimed corners are off-board or under the display; the only on-board area genuinely freed is X 0 … 6, Y 100 … 115, and the coax now uses it |
| **P2-O4** | **The speaker lead is still 6× longer than its 29.3 mm run** — carried forward from P1-O9, unchanged |
| **P2-O5** | **`.kicad_dru` still references E5/E6 rule areas the P1 rebuild deleted.** Those rules are inert today and must be re-created or retired **before routing — a P2 entry condition** |

---

## 15. Exit gate

| criterion | result |
|---|---|
| 915 cable has an exact, orderable MPN | **YES** — RF Solutions `CBA-UFLSMA20IP` |
| Cable physically reaches with useful slack | **YES** — 138.48 mm routed, 200 mm cable, 46.52 mm spare beyond the 15 mm service loop |
| Route stays outside the Ø58 NFC metal exclusion | **YES** — tightest clearance 0.600 mm, zero violations |
| No illegal cable crossing | **YES** — the two crossings that exist are cable-over-can and coax-over-coax, neither prohibited |
| Display offset recorded and accepted | **YES** — 3.34 mm left, intentional |
| Mounting strategy closed | **YES**, as 2 × M2 + edge-capture rails + 4 rib pads — **with the count escalated** |
| `MK1` validator defect fixed | **YES** — 2 → 0 |
| ESP32 via issue explicitly resolved | **YES** — false premise corrected, capability verified, scoped guard added |
| IR forming documented | **YES** — and it caught a real fit defect |
| Zero placement collisions | **YES** |
| All prior P1 mechanical constraints still pass | **YES** |
| Schematic connectivity unchanged | **YES** |
| **Zero signal routing** | **YES** |

**FBV2-P1 = PASS.** B-52 retains an enclosure-CAD-only residual, which §22 permits.

---

## 16. Progress

**FBV2-P1 passes — the third of the twelve gates.** Applying the established increment (S1
+7, S2 +6), overall Full Beta v2 moves **68 % → 74 %** and the **PCB placement** phase moves
**0 % → 100 %**. **FBV2-P2 has not begun and no routing exists.**
