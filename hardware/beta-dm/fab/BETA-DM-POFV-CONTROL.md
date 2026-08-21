# AQROOT Beta-DM — POFV Via Fill Control

**Manufacturer control document. This is a binding process requirement for the
Beta-DM fabrication build, not a preference.**

Companion data file: [`BETA-DM-POFV-VIAS.csv`](BETA-DM-POFV-VIAS.csv)

---

## 1. Required process

For every via listed in `BETA-DM-POFV-VIAS.csv`:

1. **FILL** the barrel with **non-conductive epoxy** (resin plug).
2. **PLANARISE** the fill flush with the copper surface.
3. **COPPER CAP / PLATE OVER** the filled barrel on both faces.

The finished component pad surface must be **flat and solderable**.

**No open barrel may remain inside the paste aperture of any fitted
component.**

### Explicitly not acceptable

| | |
|---|---|
| solder-mask ink plugging | **NOT acceptable** as the resolution |
| tenting only | **NOT acceptable** — these barrels sit inside pad apertures, where the pad opening dominates and the barrel stays exposed |
| accept-and-inspect | **NOT acceptable** as the primary production process |
| moving or resizing copper to avoid POFV | **NOT permitted** — the board is released and must not be modified |

**Conductive (copper-paste) fill is NOT required.** Use it only where a
specific thermal via genuinely needs the conductivity; nothing in the selected
set has been identified as needing it.

---

## 2. The selected set

Re-derived directly from the released board. The criterion is the one already
used for the `R2.1` critical feature: distance from the **drill edge** — not
the via pad edge — to the solder-paste aperture.

| | |
|---|---|
| via / paste-aperture intersections | **62** |
| **distinct vias to fill and cap** | **59** |
| on fitted components | 58 of the 62 intersections |
| on DNP components | 4 of the 62 intersections |
| paste side | 41 back, 21 front |
| classification | 45 thermal/ground, 12 signal, 5 power |
| true via-in-pad (barrel inside pad copper) | 46 |
| barrel near but not inside pad copper | 16 |

### Reconciliation against the earlier figure of 63

The earlier count was 63 raw (via, pad-object) pairs. `J3.A12` and `J3.B1` are
**two pad objects at the same physical location** — the USB-C receptacle's
shared ground land carried under two pin numbers. That is one aperture and one
via, so it is one instruction, giving **62** intersections. The delta is
exactly that one duplicate and nothing else.

**Also checked and clear:** no plated through-hole *pad* on this board carries
a paste aperture (0 of 47), so there is no second population of open barrels
hiding outside the via list. The 59 vias are the complete set.

---

## 3. Capability gate — PASS

Every selected via was measured against the process limits below.
**Drill diameter and via outer diameter are reported separately and are never
interchangeable.**

| parameter | measured across the 59 | gate | result |
|---|---|---|---|
| **drill diameter** | 0.25 – 0.40 mm | 0.20 – 0.60 mm | PASS |
| **via outer diameter** | 0.55 – 0.80 mm | (not a fill limit; recorded for plating) | — |
| annular ring | 0.150 – 0.200 mm | ≥ 0.125 mm | PASS |
| aspect ratio (1.6 mm board ÷ drill) | 4.00 : 1 – 6.40 : 1 | ≤ 10 : 1 | PASS |
| hole edge to nearest hole edge | 0.400 – 5.581 mm | ≥ 0.25 mm | PASS |
| capped pad to nearest other-net copper | 0.200 – 7.905 mm | ≥ 0.10 mm | PASS |
| via type | all through vias, F.Cu → B.Cu | — | fill and cap from both faces |

Drill population: 0.40 mm ×5, 0.30 mm ×41, 0.25 mm ×13 (by intersection:
0.40 ×5, 0.30 ×41, 0.25 ×16).

**Vendor-grounded confirmation.** The gate figures above are checked against
JLCPCB's published material (accessed 2026-08-21):

| vendor statement | AQROOT worst case | result |
|---|---|---|
| filled-and-capped vias "compatible with via diameters from **0.15 to 0.55 mm**" | drills 0.25–0.40 mm | **PASS** |
| "recommends **≤ 0.5 mm finished diameter** for reliable filling" | largest drill 0.40 mm | **PASS** |
| "non-conductive fill uses standard epoxy resin … followed by leveling and copper over-plating" | the specified process | **matches** |
| POFV free on 6-layer and above | this is a **4-layer** board | chargeable — confirm at quote |

The 0.15–0.55 mm range must be read as **hole** diameter, not pad: the same
source lists minimum via *hole* 0.15 mm and minimum via *diameter* 0.25 mm, and
a 0.15 mm pad is impossible. This matters, because our via **outer** diameters
reach 0.80 mm and would fail on a pad reading. **Confirm this in writing** —
it is question 2 in the ordering note.

If the fabricator's actual capability excludes any listed via — particularly
the thirteen 0.25 mm drills — **stop and return the query**; do not substitute
a different process.

Sources: <https://jlcpcb.com/capabilities/pcb-capabilities> ·
<https://jlcpcb.com/blog/via-filling-explained>

---

## 4. Communicating this to the fabricator

Gerbers alone do **not** unambiguously convey selective via filling. Supply all
of the following, and require written confirmation before fabrication starts:

1. **`BETA-DM-POFV-VIAS.csv`** — the coordinate list, with net, side,
   footprint, pad, via outer diameter, drill diameter, annular ring and overlap
   depth for every entry.
2. **This document**, as the process statement.
3. **The native KiCad `.kicad_pcb`**, if the manufacturer accepts it — it
   carries the via geometry directly.
4. **Exact counts and drill sizes**, repeated on the order sheet:
   **59 vias, drills 0.25 / 0.30 / 0.40 mm, epoxy filled and copper capped.**

**Require a production-file confirmation from the manufacturer that states the
via count they will fill.** Do not assume the fab house inferred the list from
the Gerbers — it cannot.

If the manufacturer's confirmation names a different count than 59, stop and
reconcile before release.

---

## 5. Stencil policy after POFV

Once a via is epoxy filled, planarised and copper capped, **it is no longer an
open solder-wicking barrel.** The pad is a normal flat solderable surface.

Therefore:

* **Do not** shrink paste apertures merely because a pad contains a filled via.
* **Do not** use stencil reduction as a substitute for POFV.
* Audit the exported stencil normally, on ordinary paste-volume grounds.
  If a pad still needs aperture tuning for a normal reason — fine-pitch bridging
  risk, large-to-small pad imbalance — identify it **separately**, on its own
  merits, and record it as a stencil item rather than a via item.

No paste aperture has been modified in this pass.

---

## 6. Interaction with the `R2.1` critical feature

`R2.1`'s documented 0.125 mm solder-mask dam is measured and intact — the
barrel edge sits **0.125 mm outside** the `R2.1` paste aperture, which is why
that via is *not* in the POFV set.

`BETA-DM-FABRICATION-NOTES.md` §2 already records that plugging or capping that
via is "acceptable and welcome". With POFV now specified for 59 other vias, the
sensible instruction is: **include the `R2.1` via at (21.900, 37.400) in the
same fill-and-cap operation if the process is running anyway.** It strictly
reduces risk and removes the board's tightest mask dependency. It is optional;
the dam is valid without it.
