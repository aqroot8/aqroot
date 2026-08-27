# Full Beta v2 — six-layer stackup, POFV fabrication note, impedance register

**D-258 · D-259(c) · LOCKED ON THE AUTHORITATIVE BOARD (FBV2-P2-002R, commit
`f8c931b`).** Status: **THIS IS NOW THE AUTHORITATIVE FULL BETA v2 STACKUP.**
FBV2-P2-002R §2 decoupled the architecture from the battery local-route gate —
the migration had passed its own regression on every screen from 002M to 002Q,
PR-47's solution requires the six-layer/POFV strategy, and there was no
authoritative signal copper to disturb. Rollback point:
**`beta-v2-p2-pre-sixlayer-authoritative`** at `5f10073`.

The authoritative PCB is **six layers with zero signal tracks and zero signal
vias** — architecture only. No placement ECO, no Q3.3 POFV via, no battery
copper has been written.

---

## 1. The ruling

| item | value |
|---|---|
| manufacturer | JLCPCB |
| copper layers | **6** |
| nominal thickness | **1.6 mm** |
| stackup | **JLC06161H-7628** impedance-control |
| outer copper | 1 oz |
| inner copper | 0.5 oz |
| process | **NO HDI. No blind vias, no buried vias, no laser microvias.** |
| via-in-pad | filled + capped ordinary **THROUGH** via (POFV), **only where explicitly ruled** |

## 2. Layer roles

```
L1  F.Cu     components, critical / high-speed / RF signals, local power
L2  In1.Cu   SOLID GND PLANE
L3  In2.Cu   internal signals + slow power distribution
L4  In3.Cu   internal signals + slow power distribution
L5  In4.Cu   SOLID GND PLANE
L6  B.Cu     components, local signals, battery / high-current copper
```

**Neither GND plane is ever split into power islands.** The only authorised
void remains the ESP32 antenna keepout, which is a manufacturer requirement and
overrides plane continuity locally on every layer.

**High-current battery copper stays on 1 oz OUTER copper.** At 0.5 oz an inner
layer needs 2.73 mm for 1.5 A at a 10 K rise — the board's own `.kicad_dru`
arithmetic — which defeats the purpose of moving it there. The board already
carries `BAT_MAIN is outer-layer only`, and 002M's router now honours it by
construction: `connect_hop` offers the new internal layers to control nets and
never to a wide net.

## 3. Stackup geometry — the PUBLISHED JLC06161H-7628 construction

**D-259(c) is CLOSED.** FBV2-P2-002M authored a *derived* inner distribution
(0.2 core / 0.6312 prepreg / 0.2 core) chosen so the listed materials summed
close to 1.6 mm, and flagged it for confirmation. It is replaced here by the
manufacturer's own table, and the derived split is **not** kept merely because
it added up more neatly.

```
F.Cu          0.0350      1 oz
prepreg 7628  0.2104      <- outer dielectric, as JLC04161H-7628
In1.Cu        0.0152      0.5 oz   GND
core          0.4000
In2.Cu        0.0152      0.5 oz   signal
prepreg 7628  0.2028      <- central prepreg
In3.Cu        0.0152      0.5 oz   signal
core          0.4000
In4.Cu        0.0152      0.5 oz   GND
prepreg 7628  0.2104      <- outer dielectric
B.Cu          0.0350      1 oz
```

**Listed materials total 1.5544 mm; 1.5744 mm including both solder masks.**

**That is not a discrepancy and it is not a thickness measurement.** The board
is a **nominal 1.6 mm construction**: the vendor's table lists nominal laminate
and copper, and the finished board also carries plating, resin flow and press
tolerance. Summing the table does not produce the finished thickness, and
nothing in this repository claims that it does. The board is ordered as
**JLC06161H-7628, 6 layers, nominal 1.6 mm, 1 oz outer / 0.5 oz inner.**

The one figure that carries over from four layers is the **outer dielectric**:
0.2104 mm of 7628 from each outer copper to its adjacent reference, identical to
JLC04161H-7628. That is the geometry the outer-layer routing plans depend on,
and it is unchanged.

## 4. POFV — the Q3.3 via-in-pad fabrication note

**THIS IS A PROCESS ORDER, NOT A GEOMETRY.** Gerbers alone do not force a
fabricator to select it, and a via inside a pad that is merely tented,
mask-plugged or left open **wicks solder out of the joint**.

| field | value |
|---|---|
| component / pad | **Q3 pin 3** (`Q3_CS`), `Package_SO:SOIC-8_3.9x4.9mm_P1.27mm` |
| pad size | 1.950 × 0.600 mm |
| via type | **ordinary THROUGH via** (L1–L6) |
| via diameter | **0.35 mm** |
| drill | **0.20 mm** |
| pad copper remaining | **0.125 mm each side** across the pad width |
| required process | **PLATED OVER FILLED VIA — resin-filled, capped and plated, planarised** |
| NOT acceptable | tented via · soldermask-plugged via · open via · blind or buried via · laser microvia |

**Why this pad and no other.** FBV2-P2-002L measured `Q3.3` as having **no legal
escape at 0.25, 0.20 or 0.15 mm**, blocked by `Q3.2` and `Q3.4` — its own
neighbours on a row where `Q3_CS` owns pins 1/3 and `LTC_GATE` owns pins 2/4
across a single B.Cu slot. Both D-257 via geometries failed identically, and
they had to: a via needs a landing site, a landing site must be **reached** from
the pad, and no via size helps a pad that cannot emit copper at all.

Six layers alone do **not** fix this — `Q3.3` still has no B.Cu escape from
which to reach an external via. The POFV is what closes it, and it is applied to
**one pad**. `Q3.1` keeps an ordinary external via: it has four escape
directions and does not need a premium process.

Measured on scratch: `Q3_CS Q3.3 → Q3.1` routes **4.626 mm at 0.25 mm on
In2.Cu**, two 0.35/0.20 vias, and `LTC_GATE Q3.2 → Q3.4` gets the B.Cu slot back
at **5.500 mm with zero vias** — the right answer for a MOSFET gate drive and
the reason one premium via is worth buying.

---

## 5. Impedance impact register — PUBLISHED-STACKUP INPUTS

**No impedance-sensitive net was routed in 002M or 002N.** The inputs below are
now the published JLC06161H-7628 values; every width remains **pending
recalculation**. The four-layer widths must not be carried over on the
assumption that a similar outer prepreg means an unchanged impedance — the
reference distance is one input, and the return-path layer changes for anything
that used In2 as a reference.

**Dielectric inputs, published:**

| item | value |
|---|---|
| outer dielectric (F.Cu↔In1.Cu, In4.Cu↔B.Cu) | **0.2104 mm**, 7628 |
| central prepreg (In2.Cu↔In3.Cu) | **0.2028 mm**, 7628 |
| cores (In1↔In2, In3↔In4) | **0.4000 mm** each |
| outer copper | 1 oz (0.0350 mm) |
| inner copper | 0.5 oz (0.0152 mm) |

| net / class | old reference | new intended reference | recalculation |
|---|---|---|---|
| **USB D+/D−** (`USB_D`, 0.25 mm, 0.55/0.25 vias) | F.Cu over In1.Cu, 0.2104 mm; In2 excursion already forbidden | F.Cu over In1.Cu, **0.2104 mm** — same pairing | **PENDING** — differential pair; re-solve against the published stack |
| **915 MHz feed** (RF controls, 0.4 mm) | F.Cu over In1.Cu | F.Cu over In1.Cu, **0.2104 mm** | **PENDING** — 50 Ω single-ended |
| **433 MHz controlled traces** | outer over In1.Cu | outer over nearest plane, **0.2104 mm** | **PENDING** — confirm which arms are controlled |
| **NFC transmit arms** (`NFC_RF`, via-prohibited by rule) | B.Cu over In1.Cu across the full 4-layer core | **B.Cu over In4.Cu, 0.2104 mm** | **PENDING — the largest change in this table.** The reference moves from the far side of a 1.065 mm core to 0.2104 mm; the tuning network must be re-derived |
| **NFC_RX / NFC_OSC** | outer over In1.Cu | outer over nearest plane | **PENDING** where tuning-sensitive |
| **Display / high-speed SPI** | outer over In1.Cu | outer over nearest plane | **PENDING** for any pair declared controlled; none is today |
| **internal signals on In2 / In3** | did not exist | In2 over In1 (0.4000 mm core) · In3 over In4 (0.4000 mm core), the pair separated by 0.2028 mm | **PENDING** if any controlled net is ever placed there — none is today |
| `SWITCH_NODE` | outer only, never In2 | outer only, never In2 **or In3** | **NOT APPLICABLE** — not impedance-controlled; the rule is extended, not recalculated |

**Structural check: the migration does not invalidate the USB, RF or display
PLANNING assumptions.** Every one of those blocks keeps an outer layer against a
solid plane at the same 0.2104 mm, which is the property the plans depend on.
What changes is the numeric width, and that is what this register schedules.

---

## 6. Board-outline datum

**The design datum is 72.000 × 148.000 mm.**

`GetBoardEdgesBoundingBox()` measures to the **outside** of the Edge.Cuts
stroke, so with a 0.100 mm outline stroke it reports **72.100 × 148.100 mm**.
That is an API artefact of where the stroke is measured from, not a board
dimension. FBV2-P2-002M's regression quoted the artefact as though it were the
requirement; the six-layer regression now reports **both** figures and subtracts
the stroke to recover the datum. **Edge.Cuts itself is untouched.**
