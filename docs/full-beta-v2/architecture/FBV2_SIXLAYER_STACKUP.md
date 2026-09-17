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

## 4. POFV — the via-in-pad fabrication note

**THIS IS A PROCESS ORDER, NOT A GEOMETRY.** Gerbers alone do not force a
fabricator to select it, and a via inside a pad that is merely tented,
mask-plugged or left open **wicks solder out of the joint**.

> **D-738 — THE SCOPE OF THIS ORDER IS NO LONGER ONE PAD.**  This section was
> written when `Q3.3` was the only ruled site and it still says the process is
> "applied to **one pad**".  The board has been routed since.  Measured on the
> finished copper — `pad_to_mask_clearance` is 0, so a pad's mask aperture IS
> its copper — **128 via barrels open into 134 solderable lands across 75
> components**, on 0.20 / 0.25 / 0.30 / 0.40 mm holes, and almost every one of
> them carries the SAME net as the land it sits in (they are the router's own
> pad escapes and the decoupling fan-outs), which is why no clearance rule and
> no KiCad DRC class reports them.  **The process order below now applies to
> every via in a solderable land, not to `Q3.3` alone.**  Applying it to every
> via on the board is acceptable and is the simpler instruction to give.
> `aqroot-Demo-FAB-NOTES.md` states it, `MANIFEST.json` lists every barrel
> centre under `via_in_pad`, and `fab_package_contract` **FAB9** re-derives the
> set from the board and refuses a package that under-reports it.  The worst
> single site is not `Q3.3`: it is **`C18.1`, where a 0.40 mm hole occupies
> 38.2 % of a 0.56 x 0.62 mm land**, followed by `D8.1` at 24.2 % and the
> **0.300 mm-wide FPC lands of `J1`**, the 50-pin display connector, where a
> 0.30-0.40 mm hole is as wide as the land itself.

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
which to reach an external via. The POFV is what closes it.  ***`Q3.1` keeps an ordinary
external via*** was true of the process SCOPE when this was written; D-738's
note above supersedes the scope, not the `Q3.3` reasoning, which stands exactly
as measured.

Measured on scratch: `Q3_CS Q3.3 → Q3.1` routes **4.626 mm at 0.25 mm on
In2.Cu**, two 0.35/0.20 vias, and `LTC_GATE Q3.2 → Q3.4` gets the B.Cu slot back
at **5.500 mm with zero vias** — the right answer for a MOSFET gate drive and
the reason one premium via is worth buying.

---

## 5. Impedance impact register — **CLOSED BY D-738: THIS BOARD HAS NO CONTROLLED-IMPEDANCE NET**

> **D-738 — READ THIS BEFORE THE TABLE.**  Every row below was left `PENDING`
> when the six-layer migration was ruled, and the board has since been routed.
> Re-asked against the finished copper, the register closes without a single
> width recalculation, because **not one net on this board is impedance-
> controlled**, and three of the rows describe nets that do not exist.
>
> **`USB D+/D-` — CLOSED, NOT CONTROLLED, AND CORRECT ANYWAY.**  The pair is
> `0.250 mm` on `F.Cu` over the `In1.Cu` GND plane at `0.2104 mm` of 7628, 1 oz.
> Edge-coupled microstrip on those inputs gives `Z0 = 60.6 ohm` single-ended.
> **But the pair is not coupled**: the closest the two nets come, measured
> segment to segment on the same layer, is **1.173 mm centre to centre**, a
> **0.923 mm edge gap against a 0.2104 mm reference height** (`s/h = 4.39`), so
> the coupling term is 1.5 % and `Zdiff` is about **120 ohm** — two independent
> 60 ohm lines, not a 90 ohm pair.  ***THAT IS ACCEPTABLE HERE AND ONLY
> BECAUSE OF THE SPEED GRADE:*** the `ESP32-S3-WROOM-1-N16R8` has **no
> High-Speed USB**.  Both its USB blocks — the USB-Serial-JTAG controller and
> the USB-OTG peripheral — are **USB 1.1 / 2.0 FULL SPEED, 12 Mbit/s**.  The
> 90 ohm +/- 15 % differential requirement is a HIGH-SPEED (480 Mbit/s) rule;
> at Full Speed the 28 mm run is electrically short (~190 ps against an 83 ns
> unit interval) and the measured **2.97 mm P/N length mismatch is ~20 ps**, four
> thousand times shorter than the UI.  **Impedance control need not be ordered**,
> and `JLC06161H-7628` is bought for its construction, not for a controlled-
> impedance order.
>
> **RETURN PATH, MEASURED AND RECORDED HONESTLY.**  `USB_D_MCU_N` and
> `USB_D_MCU_P` each change layer twice (`F.Cu <-> B.Cu`, `0.55/0.25` barrels),
> so their return hands off between the two solid GND planes.  The nearest GND
> via to each transition is **2.476 / 6.836 mm** (`N`) and **3.821 / 5.825 mm**
> (`P`); the connector-side `USB_D_CONN_P` transitions are better at 2.347 and
> 2.535 mm.  A High-Speed design would want a stitch inside ~1 mm.  At Full
> Speed the few nH of detour is a low-single-digit percentage of a 60 ohm line
> and is not a functional risk — but it is the **first Rev-B improvement in this
> block** and is recorded as one rather than left to be rediscovered.
>
> **`915 MHz feed` and `433 MHz controlled traces` — THE NETS DO NOT EXIST.**
> `U8` (`E22-900M22S`) and `U7` (`E07-400M10S`) are MODULES that carry their own
> antenna connectors; neither has a single board net whose name contains `ANT`
> or `RF`.  The only `ANT` nets on the whole board are
> `NFC_ANT_A` and `NFC_ANT_B`.  **There is no board-level 50 ohm structure to
> control.**
>
> **`NFC transmit arms` — CLOSED BY CONSTRUCTION, NOT BY CALCULATION.**  This
> row called itself "the largest change in this table" because the reference
> moved from the far side of a 1.065 mm core to `0.2104 mm`.  At 13.56 MHz the
> arms are electrically nothing (`lambda/2` is 11 m); what the closer plane
> changes is STRAY CAPACITANCE, of order 0.15 pF/mm including fringing — a few
> pF across an arm, against `C71`/`C72` at 300 pF and `C73`/`C74` at 1.5 nF.
> That is inside the C0G tolerance stack, and **every part in the ladder is
> already marked `TUNE`** — twelve C0G capacitors, `L5`/`L6`, `R114`-`R117`, with
> `TP37`/`TP38` on the two arms.  The network is designed to be tuned on
> hardware and that bench tune is this row's closure.
>
> **`Display / high-speed SPI` and `internal signals on In2 / In3` — both rows
> already said "none is today", and that is still true.**

### 5.1 The original register, retained

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

> **SUPERSEDED IN ITS NUMBER BY D-709, CORRECTED HERE AT D-738.**  The datum is
> now **77.000 × 148.000 mm MAXIMUM** — a STEPPED profile, 72.000 mm wide except
> an east bump to `x = 77.000` between `y = 70.500` and `y = 104.005`, made under
> owner authority D-703 option 2 and owner approval D-707.  DEVICE_SPEC section
> 12 is the dimension authority.  **The API artefact described below is
> unaffected and is still the point of this section.**

**The design datum was 72.000 × 148.000 mm when this was written.**

`GetBoardEdgesBoundingBox()` measures to the **outside** of the Edge.Cuts
stroke, so with a 0.100 mm outline stroke it reports **72.100 × 148.100 mm**.
That is an API artefact of where the stroke is measured from, not a board
dimension. FBV2-P2-002M's regression quoted the artefact as though it were the
requirement; the six-layer regression now reports **both** figures and subtracts
the stroke to recover the datum. **Edge.Cuts itself is untouched.**
