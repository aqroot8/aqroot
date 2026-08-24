# AQROOT Full Beta v2 — IR lead-forming requirement, first five units

**Status: NORMATIVE ASSEMBLY INSTRUCTION.** Created 2026-08-24 at **FBV2-P1-002** to discharge
**P1-O8**. Authority: [`../CTO_DECISIONS.md`](../CTO_DECISIONS.md) §13 ruling,
[`../pcb/FBV2_P1_FLOORPLAN.md`](../pcb/FBV2_P1_FLOORPLAN.md) §8.

> **These are MECHANICAL ASSEMBLY OPERATIONS. Nothing electrical changes: no MPN, no footprint,
> no net, no land pattern.** Both parts stay exactly as locked — `D1` = Vishay **`TSAL6100`**,
> `U6` = Vishay **`TSOP38238`** (`TSOP38438` same-package fallback).

---

## 1. Why forming is required at all

`D1` is a T-1¾ through-hole emitter and `U6` is a three-pin minicast receiver. **Both have their
optical axis normal to the PCB.** The AQROOT IR windows are in the **TOP PANEL**, whose normal is
+Y in the board plane. There is no surface-mount or right-angle variant of either locked part, and
the CTO has ruled that the MPNs do not change for the first five boards. **Therefore both parts are
lead-formed 90° at assembly so their axes point out of the top panel.**

Both are already **hand-soldered after reflow** (D-206/D-207: `J5` and `D1` are the two manual
parts per board; `U6` joins them as a formed THT part). Forming adds a step to work that is
already manual.

---

## 2. Manufacturer guidance actually used

| source | what it says |
|---|---|
| Vishay **doc 84892**, *Processing Instructions for Mounting of Through-Hole LEDs*, rev 28-Nov-2017 | **"During cutting and lead forming, mechanical force must not be applied to the epoxy case."** · **"Use a bending tool, which securely holds the leads at their upper position without touching the epoxy case, so that no force will be transmitted to the epoxy case."** · **"Minimum 2 mm clearance between the epoxy case and bending point."** · **"Lead forming has to be done prior to soldering."** · **"Do not bend the leads more than twice at the same point."** · **"The distance between the lower epoxy rim and the closest solder point should be > 2 mm."** · **"A direct touch down of the epoxy case to the PCB should be avoided."** · allow the part to cool below 50 °C before applying any external force · holders must not create a stiff connection between case and PCB, nor apply spring force |
| Vishay **`TSAL6100`** datasheet, doc 81009 rev 1.8 | package **Ø5.8 ± 0.15**, body height **8.7 ± 0.3 mm**, lead pitch **2.54 mm**, total lead length 35.2 ± 0.55 mm, soldering temperature **260 °C** |
| Vishay **`TSOP382..`/`TSOP384..`** datasheet, doc 82491 rev 2.1, 27-May-2025 | minicast **5.0 W × 6.95 H × 4.8 D mm**; the datasheet's own resource list links a **"Bends and Cuts"** page — **Vishay publishes standard formed-lead geometries for this package**, and one of them, or an equivalent tool-formed bend, must be used |

Where a figure below is *not* from those sources it is marked **TARGET** or **CAD-TO-VERIFY** and
says so.

---

## 3. `D1` — TSAL6100 IR transmitter

| # | requirement | value | status |
|---|---|---|---|
| D1-1 | **Orientation after forming** | optical axis **horizontal, pointing +Y** (out of the TOP panel), normal to the top face **± 0°** (T-8) | **LOCKED** |
| D1-2 | **Bend direction** | leads bend from vertical (as inserted) to horizontal **toward +Y**. The case ends up **north of** its own pads | **LOCKED** |
| D1-3 | **Bend line** | one 90° bend per lead, at the **same** height on both leads, perpendicular to the lead pitch axis | **LOCKED** |
| D1-4 | **Minimum straight lead length before the bend, measured from the epoxy case** | **≥ 2.0 mm** | **LOCKED** — Vishay 84892 |
| D1-5 | **Bend radius** | **≥ 0.6 mm** inner radius (≥ 1× lead width). Formed with a tool that grips the leads above the bend | **TARGET** |
| D1-6 | **Bends per point** | **one.** Never more than two at the same point | **LOCKED** — Vishay 84892 |
| D1-7 | **No stress at the package body** | the bending tool must hold the leads at their upper position **without touching the epoxy case**; no force may reach the case; no direct touch-down of the case on the PCB | **LOCKED** — Vishay 84892 |
| D1-8 | **Sequence** | **form → insert → solder.** Forming after soldering is forbidden; it transfers the bending moment into the joint and the case | **LOCKED** — Vishay 84892 |
| D1-9 | **Solder point clearance** | lower epoxy rim to nearest solder point **> 2 mm** — satisfied by construction, the case is ≥ 2 mm along +Y from the pads | **LOCKED** — Vishay 84892 |
| D1-10 | **Final optical-axis height above the F.Cu surface** | **2.90 mm** nominal (half of Ø5.8), **± 0.50 mm** | **TARGET**, must equal the window centreline — **CAD-TO-VERIFY** |
| D1-11 | **Positional tolerance of the axis, in X** | **± 0.50 mm** about doc X 50.750 | **TARGET** |
| D1-12 | **Positional tolerance of the axis, in Y (reach)** | the dome tip must land between doc **Y 151.5 and 153.0** | **TARGET** |
| D1-13 | **Angular tolerance of the axis** | **± 3°** in both planes. The TSAL6100's half-angle is ±10°, so 3° of forming error costs little on-axis intensity but is visible at range | **TARGET** |
| D1-14 | **Barrier relationship** | the whole formed part must stay **west of X 56.500**, the IR barrier's face. Its courtyard does (X 47.495 … 54.005) | **LOCKED** |
| D1-15 | **Enclosure support** | a moulded cradle or half-clip in the top-front cavity **may** carry the formed body. It must leave clearance to the epoxy case and must not apply spring force (Vishay 84892 item 8) | **TARGET**, **CAD-TO-VERIFY** |

### 3.1 The reach arithmetic, and why `D1` moved

Measured from the pad centre in +Y, a formed `TSAL6100` occupies:

```
bend radius            0.6 mm     (D1-5)
straight before case   2.0 mm     (D1-4, Vishay minimum)
body                   8.7 mm  +0.3   (datasheet 81009)
                      --------
total                 11.3 mm ... 11.6 mm worst case
```

The top wall runs from cavity **Y 151.5** to external **Y 154.0**. **The enclosure must present a
clear bore to Y = 153.0**, i.e. 1.5 mm into the 2.5 mm wall, with the IR-transmissive insert
occupying the outer 1.0 mm and recessed 0.5 mm from the outer face (T-12). That gives
**pad Y ≤ 153.0 − 11.6 = 141.4**.

**At FBV2-P1-001's Y = 143.600 the dome would have finished at Y ≈ 155.2 — 1.2 mm outside the
enclosure.** `D1` is therefore placed at **doc (50.750, 141.400)**, the northernmost position that
works. It cannot go further north (the shell) and it cannot go east (`U6` is already hard against
the right board edge and the ≥ 15 mm TX↔RX rule pins `D1`'s X exactly).

**Recorded consequence:** at Y = 141.400 the `D1` leadframe sits **2.854 mm inside the Ø58 NFC
metal exclusion**, i.e. **2.146 mm outside the Ø48 loop perimeter** against a 5 mm target. See
[`../pcb/FBV2_P1_FLOORPLAN.md`](../pcb/FBV2_P1_FLOORPLAN.md) §8.

---

## 4. `U6` — TSOP38238 IR receiver

| # | requirement | value | status |
|---|---|---|---|
| U6-1 | **Orientation after forming** | lens face **vertical, looking +Y** out of the TOP panel, ±45° FOV about that axis | **LOCKED** |
| U6-2 | **Bend direction** | leads bend from vertical to horizontal **toward +Y**; the package ends up **north of** its own pads with the lens at the far face | **LOCKED** |
| U6-3 | **Preferred method** | **use one of Vishay's published "Bends and Cuts" standard forms** for the minicast package (linked from datasheet 82491). Only if none fits, form with a tool to the geometry below | **LOCKED** |
| U6-4 | **Minimum straight lead length before the bend, from the package body** | **≥ 1.5 mm** | **TARGET** — Vishay publishes no explicit minimum for the minicast; this is the LED figure less the epoxy-case allowance the minicast does not have |
| U6-5 | **Bend radius** | **≥ 0.6 mm** inner radius | **TARGET** |
| U6-6 | **No stress at the package body** | the tool grips the leads only; no force into the moulding; **form before soldering** | **LOCKED** by analogy with 84892 and standard THT practice |
| U6-7 | **Final optical-axis height above the F.Cu surface** | **2.40 mm** nominal (half of the 4.8 mm depth), **± 0.50 mm** | **TARGET**, must equal the window centreline — **CAD-TO-VERIFY** |
| U6-8 | **Reach** | formed extent from the pad in +Y ≈ 0.5 + 1.5 + 6.95 = **≈ 9.0 mm**; from doc Y 143.400 the lens lands at **Y ≈ 152.4**, inside the 153.0 bore. **`U6` fits where it is and was NOT moved** | measured |
| U6-9 | **Positional tolerance of the axis** | **± 0.50 mm** in X about doc X 65.750; **± 3°** angular | **TARGET** |
| U6-10 | **Barrier relationship** | the whole formed part must stay **east of X 61.500**, the IR barrier's face. Its courtyard does (X 61.955 … 69.545) | **LOCKED** |
| U6-11 | **Enclosure support** | as D1-15 | **TARGET**, **CAD-TO-VERIFY** |

> **The two axes are 0.50 mm apart in height** (2.90 mm for `D1`, 2.40 mm for `U6`). The two
> windows are separate apertures, so this is not a conflict — but the enclosure CAD must place each
> window on **its own** part's axis rather than on a shared centreline.

---

## 5. The barrier is not optional

`IR_BARRIER`, doc **X 56.500 … 61.500**, full height, **bonded to BOTH shells**, opaque. It was
widened from 3.0 to 5.0 mm at FBV2-P1-002 so that it fills the entire gap between the two optical
windows while touching neither, and it **also carries `BOSS2`**, the M2 retention screw at doc
(59.000, 145.000).

**It blocks the internal reflection path, which is the path that actually causes self-blinding**
(T-11). Forming the two parts to look out of the same panel makes that path shorter, not longer,
so the barrier matters more after forming than before.

---

## 6. First-article acceptance

| # | check | how |
|---|---|---|
| A-1 | Both epoxy/moulding bodies free of cracks, whitening or lifted leads | 10× inspection after forming, before insertion |
| A-2 | Bend point ≥ 2.0 mm from the `D1` epoxy case | measured on the first three formed parts of each batch |
| A-3 | Axis height within tolerance | gauge block or the enclosure's own window as the go/no-go |
| A-4 | `D1` dome reaches the window bore and does **not** protrude past the outer face | dry-fit in the shell before soldering |
| A-5 | Barrier fitted and bonded to both shells before any IR range test | visual |
| A-6 | **Self-blinding test:** transmit at full current into an absorbing target; the receiver must not decode its own carrier | bench, all five units |
| A-7 | No mechanical load on either part from the shell once closed | the parts must still be nudgeable by hand after closing (Vishay 84892 items 8 and 9) |
