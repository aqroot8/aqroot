# AQROOT Beta DM — minimum MCU release, recomputed for DM demand only

The full-Beta MCU release plan was **not** carried over. It was recomputed from
the Beta-DM copy of `0f53205` against the DM demand set, with a corrected
geometry model.

---

## 1. The model, and the three defects it had to fix

Everything below is produced by a DRC-accurate raster model of the Beta-DM
board (0.05 mm grid over F.Cu / In2.Cu / B.Cu; In1.Cu is GND-only and is never
a routing layer), plus an exact analytic re-check of every final polyline.

Clearance model, deliberately conservative:

- 0.20 mm global (all five DM demand nets resolve to `Default`)
- elevated **routing** clearances honoured: `LED_BOOST`/`BAT_MAIN`/`SWITCH_NODE`
  0.30 mm, `SYS_MAIN`/`VBUS_CHG`/`NFC_5V_PA` 0.25 mm
- the `E6_*` local relaxations are **never** used — they are `P3V3`-scoped
- 0.60/0.30 mm through vias only; 0.25 mm hole-to-hole; 0.5 mm copper-to-edge
- rule areas honoured, **including footprint-embedded ones**

Three model defects were found and fixed **before** any conclusion below was
accepted. Each was caught by disagreement with KiCad's own DRC, and each is the
kind of error that silently produces a route that cannot be built:

| # | defect | consequence if left in |
|---|---|---|
| 1 | **Through vias were treated as occupying only the two layers named in the file** (`"F.Cu" "B.Cu"`). All 270 vias on this board are through vias and occupy **every** copper layer. | tracks routed straight across existing vias on In2 — KiCad reported four such clearance errors at 0.058–0.169 mm |
| 2 | **Rule areas were tested against the track centreline.** KiCad's `intersectsArea()` tests the item's real copper outline, so a centreline lying exactly on an area boundary still intersects it. | 8 `items_not_allowed` errors: LRCLK and MIC_DIN ran along the `NFC RESERVED` boundary at y = 35.000 and x = 54.000 |
| 3 | **Custom pads were sized from their `size` field only.** `MK1.3` is a 0.3 mm anchor **plus a 1.625 mm-diameter GND ring** (an unfilled `gr_circle`, stroke 0.30, so copper from r = 0.5125 to r = 0.8125) around the ICS-43434 acoustic port. | 16 `shorting_items` and 5 `solder_mask_bridge` errors — a route driven straight through the microphone's own ground ring |

The corrected model reproduces the published full-Beta baseline exactly (§2),
which is the evidence that it is now right.

---

## 2. Baseline reproduction — the model agrees with the full-Beta result

**Escape cell** (definition, so it can be audited): a 0.05 mm grid cell inside a
pad's own escape window `x ∈ [cx−0.635, cx+0.635], y ∈ [34.00, 37.00]` at which
a 0.60/0.30 through via may legally sit **and** to which a 0.20 mm B.Cu track
may legally run from the pad centre, with at least one of F.Cu / In2.Cu free at
that cell to continue on.

All six MCU demands sit on U1's south pad row at y = 34.750, pitch 1.27 mm:

| pad | net | x | escape cells, untouched baseline | minimum blocker |
|---|---|---|---|---|
| U1.37 | `FAST_IO_U0TXD_ROOTPROBE_CS` | 11.300 | **0** | `/SPI_B_SCK` In2.Cu trunk at x = 11.300 (y 19.100→82.000) |
| U1.36 | `IR_RX_GPIO44` | 12.570 | **0** | **no single-object release exists** |
| U1.35 | `I2S_MIC_DIN` | 13.840 | **12** (lowest 13.650, 35.000) | — none needed |
| U1.34 | `I2S_SPK_DOUT` | 15.110 | **0** | `/BTN_HOME_N` In2.Cu (15.100,33.481)-(14.863,36.099) |
| U1.33 | `I2S_LRCLK` | 16.380 | **0** | `/BTN_RIGHT_N` F.Cu (16.898,33.481)-(15.900,35.898) **or** `/I2C_SCL_INT` B.Cu (10.030,36.000)-(18.200,36.000) |
| U1.32 | `I2S_BCLK` | 17.650 | **0** | `/I2C_SDA_INT` In2.Cu trunk at x = 17.500 (y 10.875→37.000) |
| U1.27 | `BOOT_N` | 24.000 | **0** | `/BTN_RIGHT_N` In2.Cu (24.701,35.985)-(23.300,33.481) |

That is the published full-Beta 5-object release set, rediscovered from geometry
alone — `#1 SDA→BCLK`, `#2 BTN_RIGHT_N F.Cu→LRCLK`, `#3 BTN_HOME_N In2→SPK_DOUT`,
`#4 BTN_RIGHT_N In2→BOOT_N`, `#5 SPI_B_SCK In2→FAST_IO` — together with the
known fact that MIC_DIN escaped without a release.

**Why the corridor is this tight.** The pads are 0.90 mm wide on 1.27 mm pitch,
so the 0.37 mm inter-pad gap cannot carry a 0.20 mm track (which needs 0.60 mm).
The only escape is a fan-out via at the pad, and the `/I2C_SCL_INT` B.Cu wall at
y = 36.000 sits 0.40 mm below the pad row — too close for a via to fit between
them. So every pad's fan-out via must sit in its own 1.27 mm-wide window, where
the In2 and F.Cu trunks running under U1 decide whether there is room.

---

## 3. DM demand set, and what falls away

DM demand: `I2S_BCLK`, `I2S_LRCLK`, `I2S_MIC_DIN`, `BOOT_N`, `FAST_IO`.
`I2S_SPK_DOUT` is gone (U5 DNP); `AMP_SD_MODE`/R15.1 is not routed.

### 3.1 Release object eliminated

**Release #3 — `/08_BUTTONS_EXPANDERS/BTN_HOME_N` In2.Cu (15.100,33.481)-(14.863,36.099), 2.628 mm — is eliminated.**

Verified rather than assumed: with the DM 4-object set applied, U1.34
(`I2S_SPK_DOUT`) returns **0** escape cells, i.e. #3 is genuinely no longer
being paid for and is not incidentally freed by the other releases.

Consequently `BTN_HOME_N` is a net Beta DM **does not touch at all**, and the
hard-locked HOME Option-D escape landed in `0f53205` is **not reopened**.

### 3.2 Release #5 — the part that existed only for R15.1

`R15.1` (`AMP_SD_MODE`, at 10.675, 54.900) has **0** escape cells at baseline
and is freed by exactly one object: **the same `/SPI_B_SCK` In2 trunk** that
blocks FAST_IO. Release #5 was therefore serving two customers 20 mm apart.

With `AMP_SD_MODE` on the DM do-not-route list, **the R15 half of release #5 is
eliminated**. The DM replacement geometry only has to clear the U1.37 window at
y ≈ 34.0–37.0; it no longer has to clear R15's window at y ≈ 53.7–56.1. The
full-Beta candidate family (~65.424 mm, 0 vias, In2) was shaped for both and is
therefore **not** the DM answer — the DM re-land is a shorter problem and needs
its own solve.

Note the constraint that makes it non-trivial anyway: a purely local In2 detour
around x = 11.300 is impossible, because `/BTN_B_N` In2 sits at x ≈ 10.675
(y 33.0→38.1) to the west and `/SX1262_CS_N` In2 at x = 12.000 to the east,
leaving no 0.40 mm-pitch lane on either side.

---

## 4. DM minimum release — result

```
FULL-BETA RELEASE OBJECTS:      5
DM REQUIRED RELEASE OBJECTS:    4   (at the MCU end)
OBJECTS ELIMINATED BY DM SCOPE: #3  BTN_HOME_N In2.Cu  (SPK_DOUT blocker)
NETS NO LONGER TOUCHED:         /08_BUTTONS_EXPANDERS/BTN_HOME_N
HARD-LOCKS NO LONGER OPENED:    the BTN_HOME_N Option-D escape (hard-locked in 0f53205)
```

The four DM release objects:

| id | object | net | layer | length | serves |
|---|---|---|---|---|---|
| R1 | (17.500,37.000)-(17.500,10.875) | `/I2C_SDA_INT` | In2.Cu | 26.125 mm | BCLK |
| R2 | (16.898,33.481)-(15.900,35.898) | `/08_BUTTONS_EXPANDERS/BTN_RIGHT_N` | F.Cu | 2.615 mm | LRCLK |
| R2-alt | (10.030,36.000)-(18.200,36.000) | `/I2C_SCL_INT` | B.Cu | 8.170 mm | LRCLK (alternative) |
| R4 | (24.701,35.985)-(23.300,33.481) | `/08_BUTTONS_EXPANDERS/BTN_RIGHT_N` | In2.Cu | 2.869 mm | BOOT_N |
| R5 | (11.300,19.100)-(11.300,82.000) | `/SPI_B_SCK` | In2.Cu | 62.900 mm | FAST_IO |

Joint feasibility, all five DM demands simultaneously (4-object set applied):

| demand | escape cells | chosen fan-out via |
|---|---|---|
| FAST_IO | 54 | (11.300, 34.100) → F.Cu / In2.Cu |
| MIC_DIN | 12 | (13.650, 35.000) → F.Cu / In2.Cu |
| LRCLK | 310 | (16.200, 34.050) → F.Cu / In2.Cu |
| BCLK | 133 | (17.450, 34.100) → F.Cu / In2.Cu |
| BOOT_N | 144 | (23.750, 34.150) → F.Cu / In2.Cu |
| SPK_DOUT | **0** | (correctly still blocked) |
| IR_RX | **0** | (no release exists) |

Minimum via-to-via centre distance across the chosen set: **1.251 mm**
(0.80 mm required). Joint selection: **OK**.

### 4.1 Why 4 is minimal

Exhaustive single-object sweep over the union of all four blocked demands'
candidate neighbourhoods (**139 objects**): exactly **five** objects free any
demand at all, and **every one of them frees exactly one**:

```
08cf0bd1  /I2C_SCL_INT       B.Cu    -> LRCLK   (195 cells)
101eaf2a  /I2C_SDA_INT       In2.Cu  -> BCLK    (133 cells)
3a41d05e  /BTN_RIGHT_N       F.Cu    -> LRCLK   (310 cells)
2d29d28f  /BTN_RIGHT_N       In2.Cu  -> BOOT_N  (144 cells)
bbc00001  /SPI_B_SCK         In2.Cu  -> FAST_IO ( 54 cells)
MAX demands freed by any single object: 1
```

Pair sweep over the **52** objects that lie within reach of two or more demand
pads (1 326 pairs): the maximum number of demands freed by any pair is **2**,
and the only pairs achieving it are the disjoint singles combined
(`{SCL, SDA}` and `{SDA, BTN_RIGHT_N F.Cu}`). No combination effect frees a
demand that neither member frees alone.

The four demands therefore draw from four pairwise-disjoint option sets, so
**four releases are required and four suffice**. As with the J5 west-trio
result, this is a strong computational bound, not a closed-form proof: it rests
on an exhaustive single- and multi-reach-pair search, not on an exhaustive
search over all triples.

### 4.2 LRCLK has a choice — and the recommendation

`R2` (`BTN_RIGHT_N` F.Cu escape stub, 2.615 mm) reopens the E2 hard-lock.
`R2-alt` (`I2C_SCL_INT` B.Cu wall, 8.170 mm) does not, but it re-routes a live
I2C trunk through a congested part of the board. Both give all three I2S nets
full reachability to MK1, so neither costs the microphone anything.

**Recommendation: take `R2-alt` (`I2C_SCL_INT` B.Cu).** It is the variant the
validated 3-net solution in §7 was solved and DRC-checked against, and the
landed LRCLK escape via at (16.700, 35.550) is the cell that release vacates.
`R2` remains available and is attractive on a different axis — `BOOT_N` needs
`R4`, the *same net* on In2, so taking `R2` would let the whole DM release set
touch three nets instead of four — but it has no validated route behind it yet
and would need its own solve.

Either way `I2C_SCL_INT` or `BTN_RIGHT_N` must be re-landed; the release tails
are visible in the scratch DRC as `track_dangling` warnings (§7.3).

---

## 5. The microphone bus needs a fifth release — at the MK1 end

This was **not** in the full-Beta plan and is a new finding, exposed only after
model defect #3 (the custom-pad ring) was fixed.

`MK1.6` (`I2S_MIC_DIN`) is trapped in a **411-cell B.Cu pocket**,
x ∈ [71.05, 71.90], y ∈ [8.90, 10.40], with **no** reachable F.Cu or In2.Cu cell
— no via fits, because the `+3V3` 0.60 mm F.Cu run (71.400,9.600)-(72.700,10.900)
crosses the pocket on F.Cu.

The pocket walls:

| side | obstacle |
|---|---|
| north | `MK1.3` acoustic-port GND ring, outer edge y = 8.6025 at x = 71.5 |
| west | `MK1.1` (LRCLK pad), copper x 70.30–70.90 |
| east | `MK1.5` (+3V3 pad), copper x 72.10–72.70, and `/SX1262_RXEN` B.Cu turning south at x = 72.000 |
| south | `/SX1262_RXEN` B.Cu at y = 10.800 |

The only exit is a B.Cu lane running west underneath `MK1.1`:

```
MK1.1 copper bottom edge          y = 10.124
+ 0.20 clearance + 0.10 half-width  -> lane centreline must be at y >= 10.424
SX1262_RXEN copper top edge       y = 10.700
- 0.20 clearance - 0.10 half-width  -> lane centreline must be at y <= 10.400
```

**The lane is short by 0.024 mm.** Reachability search confirms it: exactly one
object, when released, opens the pocket from 411 cells to 161 137 —
`/SX1262_RXEN` B.Cu `(66.000,10.800)-(72.000,10.800)`.

`MK1.4` (BCLK) and `MK1.1` (LRCLK) are unaffected: both reach the whole board.

### 5.1 R6 — the fix, and it is cheap

Move the RXEN run 0.200 mm south. Three B.Cu segments are released and re-landed:

| released | re-landed |
|---|---|
| (66.000,12.600)-(66.000,10.800) | (66.000,12.600)-(66.000,**11.000**) |
| (66.000,10.800)-(72.000,10.800) | (66.000,**11.000**)-(72.000,**11.000**) |
| (72.000,10.800)-(72.000,83.500) | (72.000,**11.000**)-(72.000,83.500) |

Net length change ≈ 0. Clearances after the move: 0.225 mm to `C8.1`/`C8.2`
(pads at y = 11.800, copper edge 11.325) on both the horizontal run and the
x = 72.000 vertical — inside the 0.20 mm requirement with margin.

Verified: at y = 10.900 and at y = 11.000 the MIC_DIN reachable set opens to
≈160 000 cells; at y = 10.825 it does **not** (the surviving lane is degenerate).
**y = 11.000 is the chosen re-land.**

`SX1262_RXEN` is a static enable held low by `R74`; a 0.2 mm move has no signal-
integrity consequence. It does, however, touch a **must-work radio net**, so it
is called out explicitly rather than folded into the I2S work.

---

## 6. Beta-DM release summary

```
MCU end (U1 south row)        4 objects   R1, R2 (or R2-alt), R4, R5
Microphone end (MK1)          1 object    R6  /SX1262_RXEN B.Cu, re-land at y = 11.000
------------------------------------------------------------------------
TOTAL for the full DM demand set   5 objects
of which the 3-net microphone bus needs   R1, R2 (or R2-alt), R6
```

Compared with full Beta: one MCU-end object eliminated (`#3 BTN_HOME_N`), one
whole hard-locked net no longer touched, the R15.1 half of `#5` eliminated —
and one genuinely new object (`R6`) that the full-Beta plan had missed because
the microphone's own custom pad was mis-modelled.

---

## 7. The 3-net microphone bus — corridor capacity

With `U5` DNP the microphone bus is `I2S_BCLK`, `I2S_LRCLK` and `I2S_MIC_DIN`
only, each a two-pad net from U1's south row to MK1. The **4-net Full-Beta
conclusion does not apply and was not reused** — this was solved from scratch.

### 7.1 Each net reaches on its own

Flood-fill reachability on the Beta-DM copy with `R1 + R2 (or R2-alt) + R6`
applied, 0.05 mm grid, three routing layers:

| net | from | reachable cells | goal reachable |
|---|---|---|---|
| `I2S_BCLK` | U1.32 | 1 638 256 | **yes** (MK1.4) |
| `I2S_LRCLK` | U1.33 | 1 637 963 | **yes** (MK1.1) |
| `I2S_MIC_DIN` | U1.35 | 1 637 955 | **yes** (MK1.6) |

Identical outcome for both LRCLK release variants, so the §4.2 recommendation
does not cost the microphone anything.

### 7.2 The three nets cannot share one corridor

They are not short of board — they are short of **passages**, and the reason is
a structure that had not been characterised before:

> **`U1.41` is a 13-pad through-hole GND stitching array**, 0.60 mm pads on a
> 0.70 mm staggered grid, spanning x 13.810–16.610, y 23.100–25.900, on
> **every copper layer**. With 0.20 mm clearance and a 0.10 mm half width it
> walls off In2 (and F.Cu) from x 13.51 to 16.91 across the middle of U1's
> footprint.

Northbound In2 lanes under U1, after that wall and the surviving trunks
(`/SPI_B_SCK` 11.300, `/SX1262_CS_N` 12.000, `/SPI_B_MOSI` 13.000,
`/I2C_SCL_INT` 18.200):

| candidate band | usable centreline | verdict |
|---|---|---|
| between `SPI_B_MOSI` (13.000) and the array (13.51) | 13.40 … 13.41 | **no** — degenerate |
| between the array (16.91) and `I2C_SCL_INT` (18.200) | 17.21 … 17.80 | **yes — one lane** |
| between `SX1262_CS_N` (12.000) and `SPI_B_MOSI` (13.000) | 12.40 … 12.60 | closed at y = 18.500 by the `SX1262_CS_N` In2 crossing |

**The northbound In2 passage under U1 has capacity one, and release R1 is
exactly what creates it.** The other two nets must take the eastern passage
beside `NFC RESERVED` or the southern route around it.

That is also why every naive solve fails: routed first, any one net takes the
shared fan-out strip south of the pad row and strands the others. Measured —
with `MIC_DIN` landed first, `LRCLK` is left with a **647-cell** pocket
(x 15.85–16.90, y 33.75–35.55) and cannot escape at all. All six sequential
orders fail after the first net.

### 7.3 Result — PASS

Solved with negotiated congestion (present cost = the number of other nets whose
0.40 mm exclusion envelope covers a cell, plus an accumulating history cost),
then cleaned up by ripping up and re-routing each net once with the other two
frozen as hard obstacles. Converged at iteration 23 with **zero conflict cells**.

Releases in force: `R1` (`/I2C_SDA_INT` In2), `R2-alt` (`/I2C_SCL_INT` B.Cu),
`R6` (`/SX1262_RXEN` B.Cu re-landed at y = 11.000).

| net | length | vias | B.Cu | F.Cu | In2.Cu |
|---|---|---|---|---|---|
| `I2S_BCLK` U1.32 → MK1.4 | **84.251 mm** | 5 | 0.69 | 42.01 | 41.55 |
| `I2S_LRCLK` U1.33 → MK1.1 | **87.909 mm** | 8 | 41.33 | 19.30 | 27.28 |
| `I2S_MIC_DIN` U1.35 → MK1.6 | **91.635 mm** | 8 | 15.21 | 56.67 | 19.75 |
| **total** | **263.795 mm** | **21** | | | |

Escape vias: BCLK (17.550, 34.100), LRCLK (16.700, 35.550),
MIC_DIN (13.650, 35.000).

**Success gate**

| requirement | result |
|---|---|
| 3/3 I2S routed | **PASS** |
| `BCLK` connected | **PASS** — U1.32 ↔ MK1.4 |
| `LRCLK` connected | **PASS** — U1.33 ↔ MK1.1 |
| `MIC_DIN` connected | **PASS** — U1.35 ↔ MK1.6, net ratsnest **0** |
| 0 pairwise conflicts | **PASS** — 0 conflict cells at convergence, and the cleanup pass treats the other two nets as hard obstacles |
| exact analytic validation | **PASS** — 0 violations over 239 new segments and 21 new vias, checked against every foreign pad (custom-pad primitives included), track, via (all four layers), rule area, board edge and Edge.Cuts cutout |
| scratch KiCad DRC | **0 errors** |
| minimum clearance | **0.200 mm** — several categories sit exactly on the requirement; nothing is below it |
| reference plane | `In1.Cu` solid GND. F.Cu and In2.Cu are each adjacent to it; the B.Cu portions reference it across the full core |
| artificial matching | none, and none needed — two clocks and one data line at a 16 kHz frame rate |

**Two honest qualifications on the DRC number.**

1. `kicad-cli` cannot refill zones, so a via added through the `In1 GND
   REFERENCE` pour is judged against a **stale** fill and reports a bogus
   0.000 mm zone clearance. With the pour left in place the run reports exactly
   42 errors — 21 `clearance` + 21 `hole_clearance`, one pair per new via, every
   single one against that zone and **nothing else**. With the pour removed for
   the check the run reports **0 errors**. The pour must be refilled and
   re-DRC'd inside KiCad before this lands.
2. Removing the pour for the check orphans the 27 existing GND stitching vias
   (`via_dangling` warnings) and lifts the GND ratsnest from 164 to 186. Both
   are artifacts of the same removal, not of the new copper.

Remaining ratsnest after the solve: `I2S_MIC_DIN` **0**; `I2S_BCLK` **1** and
`I2S_LRCLK` **1** — and those two are the **U5.16 / U5.14 amplifier pads we
deliberately do not route**, exactly as the DNP ledger specifies.
`/SX1262_RXEN` is **0**, so the R6 re-land is complete.

`track_dangling` rises from 2 to 7: the five new tails are the released
`I2C_SCL_INT` (×3) and `I2C_SDA_INT` (×2) stubs waiting for their re-land. That
re-land is the next piece of work and is not part of this result.

> **Status: the 3-net microphone bus is SOLVED and validated in scratch. It has
> not been landed on `hardware/beta-dm/`** — per the standing instruction to
> report before major DM routing. Landing it requires, in the same pass, the
> re-land of `I2C_SDA_INT` and `I2C_SCL_INT`, and a KiCad zone refill.
