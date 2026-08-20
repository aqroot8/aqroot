# AQROOT Beta-DM — GND Closeout

**Scope:** Beta-DM only. `hardware/beta/` is frozen at `beta-full-reference-v1`
and is proven unchanged in this pass.

**Pass boundary:** fitted-hardware ground finalisation only. No new signal
routing, no outer-layer pours, no E6 retirement. `E6_R2_1_CLR` and
`E6_R2_1_WIDTH` are untouched.

---

## 1. Reclassification of the 130 GND ratsnest lines

Every GND line on the board before this pass was classified against KiCad's own
connectivity graph and the footprint `dnp` attribute.

| class | meaning | count |
|---|---|---:|
| **G1** | at least one endpoint on a **fitted** part → must ground | **100** |
| **G2** | every ungrounded endpoint on a **DNP** part → no copper owed | **30** |
| **G3** | already satisfied (line is an artefact) | **0** |
| **G4** | special / needs a ruling | **0** |
| | **total** | **130** |

There are no G3 and no G4 lines: every GND rat is explained, and the split is
purely fitted vs DNP.

A ratsnest line is a minimum-spanning-tree edge, not a unit of work. The real
unit is the **island**. KiCad's connectivity engine reports, on the pre-pass
board:

* **91 isolated FITTED islands** — these owe copper
* **35 isolated DNP-only islands** — these owe nothing

---

## 2. Method

As directed: **pad → short stub → local GND via → In1.Cu plane.** No long GND
traces, no In1 modification, no pours, no signal copper touched.

A candidate via site must clear **all** of:

* the full GND obstacle model at via geometry — pads, tracks, holes, rule areas
* the RF keepout bands
* **every paste aperture on every net**, with a **0.125 mm solder-mask web**
  retained — no via under or tangent to a solder termination
* the **In1.Cu GND zone outline** — a via outside it never reaches the plane
* **hole-to-hole ≥ 0.250 mm against every existing hole on the board,
  same net included** (see §6)

and the stub from pad to via must be legal at 0.20 mm.

Where a pad could not take its own via, it was joined by local same-net copper
to GND copper that already reaches the plane — the topology the ruling
contemplates: several pads sharing one well-positioned via.

**DNP-only islands were deliberately not stitched.** No via was added anywhere
merely to reduce the ratsnest count.

---

## 3. What landed

Three authorised writes to the real board, each with a fresh UUID prefix, exact
release accounting, pre/post SHA-256, and the Full-Beta freeze guard:

| tag | added | released |
|---|---|---:|
| `aqroot-gnd-closeout-v2` | 120 segments + 52 vias | 0 |
| `aqroot-gnd-closeout-v3` | 7 segments + 3 vias | 0 |
| `aqroot-gnd-closeout-v4` | 7 segments + 0 vias | 0 |
| | **134 segments + 55 vias** | **0** |

Preservation diff against the pre-pass board:

```
footprints  added 0    removed 0    changed 0
pads        added 0    removed 0    changed 0
segments    added 134  removed 0    changed 0
vias        added 55   removed 0    changed 0
zones       added 0    removed 0    changed 0
edge.cuts   12 -> 12
```

**Signal copper modifications: 0.** Nothing was removed and nothing was
changed — the preferred result.

Result: **76 of the 91 isolated fitted islands are now on the main GND island.**
GND ratsnest **130 → 52**. Total unconnected **215 → 137**.

---

## 4. Ground-via DFM

All 55 new vias:

| check | measured | limit |
|---|---:|---|
| annular ring, 50 × 0.60/0.30 | 0.1500 mm | ≥ 0.125 mm |
| annular ring, 5 × 0.50/0.25 | 0.1250 mm | ≥ 0.125 mm (at the floor) |
| solder-mask web to any paste aperture | **0.1250 mm** (`C36.2`) | ≥ 0.125 preferred, 0.100 absolute |
| hole-to-hole, all nets | **0.4818 mm** | ≥ 0.250 mm |
| vias inside a component courtyard | 0 | — |
| vias overlapping a paste aperture | 0 | — |

Every via is tented front and back by the board-level
`(tenting (front yes) (back yes))`; no per-via override exists and none was
added. No design rule was changed in this pass.

**DRC on the landed board: 240 violations, 0 errors, 137 unconnected,
0 schematic-parity issues, and zero new warnings of any type** against the
pre-pass baseline.

---

## 5. The 15 fitted islands that remain open — and why

Fifteen fitted islands could not be closed. This is a **geometric** result, not
a search-effort result: three independent passes converged on the same set, and
the last one — deliberately the most permissive ever run (10 mm radius, both via
sizes, layer changes, and *either* a via site *or* any already-grounded GND pad
as the goal) — closed **0 of 15**.

The diagnosis, measured per pad on the landed board:

| island | part | pitch | escape | reachable pocket | nearest legal via site |
|---|---|---:|---|---:|---|
| `U2/2`, `U2/3`, `U2/21` | TCA9535PWR TSSOP-24 | 0.65 mm | B.Cu only | 418–1983 cells | **none in reach** |
| `U3/2`, `U3/3`, `U3/12` | TCA9535PWR TSSOP-24 | 0.65 mm | B.Cu only | 1039–3026 cells | **none in reach** |
| `U4/6`, `U4/7` | BMI270 LGA-14 | 0.50 mm | B.Cu, 40–50 cells | 383 cells | **none in reach** |
| `J3/A1` | USB-C receptacle 16P | stacked | F.Cu only | 326 cells | **none in reach** |
| `C4/2`, `C6/2`, `C18/2`, `C38/2`, `C40/2`, `R13/2` | 0402/0603 passives in those same pockets | — | — | 320–5887 cells | **none in reach** |

Each of these pads *can* escape — a 0.20 mm trace has somewhere to go — but the
free region it can reach is a narrow channel, and **a via needs a wider clear
disc than a trace does**: 0.125 mm drill radius + 0.20 mm clearance + 0.125 mm
mask web is a 0.575 mm halo that does not fit anywhere inside those pockets.
The board carries 966,950 legal 0.50/0.25 via cells; not one of them is
reachable from these fifteen pads.

`C38/2` is the one island with a legal site somewhere in its reachable region,
at **13.558 mm**. A 210 mm, 10-via route to it was generated and **rejected**:
that is not a local ground stitch, and adding 210 mm of GND trace across the
board to retire one ratsnest line would be worse than leaving the line open.

**These islands are pour-resolvable, not via-resolvable.** Every one of them is
a fine-pitch pad or a passive sitting in the congested pocket beside one, and an
F.Cu / B.Cu GND pour is the normal and correct way to ground them. This ruling
explicitly defers outer-layer pours to a later pass, so they are recorded here
rather than forced.

**Recommendation for the pour pass:** re-measure these 15 islands *after* the
outer-layer GND pours are placed, before considering any further via work.

---

## 6. Corrections made in this pass

**A router defect — hole-to-hole was not enforced against same-net holes.**
A candidate stitch via for `C5/2` was generated at (27.400, 12.950), 0.050 mm
from an existing GND via at (27.400, 13.000): the two drills overlap by
0.225 mm and would break out into each other. KiCad reports same-net
hole-to-hole only as a **warning**, so the standard error gate would not have
caught it. The candidate was rejected, the obstacle model was corrected to stamp
hole-to-hole against **every** existing hole regardless of net, and `C5/2` was
re-routed — it then closed as a 3.016 mm same-net pad-to-pad join needing no via
at all. **This check must stay in the model for the pour pass.**

**A 210 mm "stitch" was generated and rejected** — see §5. A length cap of
6.0 mm now applies to anything called a ground stitch.

**A false claim in the fab notes was corrected.** `fab/ASSEMBLY-DNP-CONTROL.md`
§3b described the `XGPIO5` via as *"the smallest via on the board — every other
via is 0.60 / 0.30 or larger."* That was wrong when written: the board already
carried four 0.50/0.25 vias (`Net-(U13-FB)` ×2, `ISET` ×2) and thirty 0.55/0.25
vias. The section now states the size class correctly and identifies the
**0.125 mm mask web under a fitted TSSOP body** — which is genuinely unique — as
the critical attribute. The via itself is unchanged and still at
(20.400, 14.050).

**An earlier stitch set was reverted before landing.** A first attempt placed
roughly 40 vias between 0.000 and 0.050 mm from a paste aperture, four of them
exactly tangent. That landing was reverted and every pass rebuilt with the
0.125 mm mask-web margin now described in §2. The cost of the margin was two
additional islands left open.

---

## 7. Ledger

Measured on the landed board, with the B1/B2 split taken from KiCad's island
membership rather than from endpoint reference alone:

```
137 = A63 + B1(15) + B2(37) + C0 + D22
```

| bucket | meaning | count |
|---|---|---:|
| **A** | DNP-function deferral | 63 |
| **B1** | **GND, fitted part, must ground** | **15** |
| **B2** | GND, DNP-only — no copper owed | 37 |
| **C** | Lean must-work, non-GND | **0** |
| **D** | Lean fitted-but-deferred | 22 |

B1 = 15 corresponds one-to-one with the 15 open fitted islands in §5.

A note on the split: a line such as `D4.2 (DNP) ↔ C42.1` has a fitted endpoint,
but `C42.1` is now grounded and the line exists solely because the DNP pad
floats. Classifying by "is either endpoint fitted" counts that as fitted work
owed and inflates B1 to 21. The correct test — used here — is **"is either
endpoint a fitted pad that is not yet on the main GND island"**, which gives 15.
B2 rises from 30 to 37 for the same reason: closing fitted islands separates
DNP pads that previously shared an island with a fitted pad.

Against the ruling's objectives:

* **zero unexplained rats** — met; all 137 are bucketed, and 85 of them are the
  unchanged non-GND A/D deferrals
* **zero fitted must-work non-GND rats** — met, C = 0
* **zero fitted must-ground rats** — **not met: 15 remain**, all of them
  pour-resolvable and itemised in §5

---

## 8. Freeze proof

```
git diff --stat beta-full-reference-v1 -- hardware/beta/     (empty)
```

An untracked directory `hardware/beta/mechanical/` exists on disk, dated
2026-08-15, containing FreeCAD and STEP reference work from an earlier session.
It is **not** part of this pass, it modifies no tracked frozen file, and it has
deliberately been left uncommitted. It is flagged here for a CTO decision on
whether it belongs in the repository.
