# AQROOT Beta DM — display backlight: analysis only, nothing landed

**Status: ANALYSIS ONLY.** No copper was landed, no DRU rule was changed, no
rule area was created. Every number below is measured on the board at commit
`4ea1588`, at the rules as they stand. The scratch routes exist only as JSON
artifacts outside the repository.

The directive was explicit that **voltage governs the clearance argument, not
current draw**. So this starts with the voltage.

---

## 1. What `LED_BOOST` actually is

### 1.1 Topology, read off the board pin by pin

| node | connection |
|---|---|
| `U17` | TPS61169DCKR, SOT-353. pin 5 `VIN` = **`+3V3`**, pin 2 `GND`, pin 1 `SW` = `BL_SW`, pin 3 `FB` = `LED_K`, pin 4 `CTRL` = `DISP_BL_CTL` from `U1.24` |
| `L3` | 4.7 µH (XFL4020-472MEC), `+3V3` → `BL_SW` |
| `D8` | NSR0240 Schottky, `BL_SW` → **`LED_BOOST`** |
| `C44` | 1 µF, `LED_BOOST` → `GND` |
| `R70`–`R73` | 39 R each, `LED_BOOST` → `LED_A1`…`LED_A4` |
| `J1.2`–`J1.5` | `LED_A1`…`LED_A4` — four **separate anode pins** |
| `J1.1` | `LED_K` — one **common cathode** pin |
| `R69` | 2.55 R, `LED_K` → `GND`; `LED_K` is also the `FB` tap |

Four separate anodes, one common cathode, one sense resistor carrying the whole
return: this is **four LEDs in parallel**, each with its own 39 R ballast. A
series string would need one anode pin and would make four equal per-anode
ballasts meaningless.

### 1.2 The operating voltage

The TPS61169 regulates `FB` to **200 mV**.

```
I_total   = 0.200 V / 2.55 R          = 78.4 mA
I_string  = 78.4 mA / 4               = 19.6 mA        (typical for a 2.8" panel)
V_ballast = 19.6 mA x 39 R            = 0.764 V
V(LED_BOOST) = Vf + V_ballast + V_FB  = Vf + 0.964 V
```

With a white-LED `Vf` of 2.9–3.4 V at 20 mA:

> **`LED_BOOST` in normal operation is about 3.9 – 4.4 V, nominally ~4.2 V.**

It is a **boost from 3.3 V to about 4.2 V** — the point of `U17` is to clear the
LED forward drop from a 3.3 V rail, not to generate a high-voltage string.
**The DRU's stated premise, "backlight string runs above 20 V", is not what this
circuit does in operation.**

### 1.3 The case that does justify an elevated figure

If **all four** LEDs open, or the display FPC is unmated, `FB` collapses to 0 V,
the regulator cannot satisfy the loop, and the output rises until the driver's
internal over-voltage protection clamps it. That is the only condition in which
`LED_BOOST` leaves the single-digit volts, and it is bounded by the silicon, not
by the load.

**This needs datasheet confirmation before any ruling** — the TPS61169 is a
38 V-class part and its OVP threshold sets the worst case. The surrounding
components are consistent with that class: `D8` NSR0240 is a 40 V Schottky.

> **Finding, raised for ruling: `C44` (1 µF, 0805, `LED_BOOST`→`GND`) has no MPN
> and no voltage rating in the BOM.** It sits directly on the node the OVP clamp
> defines. Whatever clearance is ratified, `C44` must be specified at or above
> the OVP limit; a 6.3 V or 10 V part there is a field failure waiting to
> happen.

### 1.4 Netclass over-reach found while measuring this

The `LED_BOOST` netclass is assigned by pattern. One pattern is `*LED_K`, which
also matches **`/07_IR/IR_LED_K`** — the IR transmitter's LED cathode, an
unrelated net that is DNP on the Demo Model. It carries the 0.30 mm elevated
routed clearance for no reason. Harmless today (IR is unrouted and unfitted),
but it should be tightened to an explicit net list before Final. `IR_LED_A` does
not collide, because the patterns are `*LED_A1`…`*LED_A4`.

---

## 2. The geometry that limits the fan-out

### 2.1 `J1` pad geometry, measured

| property | value |
|---|---|
| footprint | `AQROOT_Beta:Hirose_FH69-50S-0.5SH` (CH280QV10-CT, 50-pin FPC) |
| pads | 50, all on `F.Cu` |
| pad size | **0.300 × 1.230 mm** |
| pitch | **0.500 mm** |
| edge-to-edge gap | **0.200 mm** |
| row | y = 80.150; pad 1 at x = 49.750, pad 50 at x = 25.250 |
| backlight pins | `J1.1` `LED_K` 49.750 · `J1.2` `LED_A1` 49.250 · `J1.3` `LED_A2` 48.750 · `J1.4` `LED_A3` 48.250 · `J1.5` `LED_A4` 47.750 · `J1.6` `GND` 47.250 |

The pads occupy y 79.535 … 80.765.

### 2.2 The other side of the fan-out

`R70`–`R73` pad 2 sit on **`B.Cu`** in a vertical column at x = 49.575,
y = 84.900 / 83.000 / 81.100 / 79.200. So **every anode route needs a layer
change** — a `B.Cu` resistor pad to an `F.Cu` connector pad — with the via
squeezed into the same small region.

The mapping is monotonic (`R70`→`J1.2`, `R71`→`J1.3`, `R72`→`J1.4`,
`R73`→`J1.5`), so the four routes **nest** rather than cross. They nest inside a
corridor about 2 mm wide.

### 2.3 What bounds the corridor

| copper | net | why it matters |
|---|---|---|
| `F.Cu` y = 78.725, w 0.25, x 39.400–53.400 | `/USB_D_MCU_N` | runs the full width just north of `J1`'s pad row |
| `F.Cu` y = 78.275, w 0.25, x 39.850–53.850 | `/USB_D_MCU_P` | the other half of the pair |
| `In2.Cu` y = 80.700, x 44.500–61.400 | `/SX1262_CS_N` | crosses the fan-out region on the inner layer |
| `In2.Cu` y = 83.500 / 84.200 / 86.500 | `SPI_B_MOSI` / `SPI_B_SCK` / `SPI_B_MISO` | close the inner layer above |
| `B.Cu` y = 77.800, x 33.400–57.100 | `/CC1101_GDO0` | closes `B.Cu` to the north |
| `B.Cu` x = 51.225, w 0.30 | `LED_BOOST` | the rail feeding `R70`–`R73` pad 1 |
| `B.Cu` via (46.150, 81.400) 0.80/0.40 | `+3V3` | the obstacle on the `LED_K` return |

The tightest single geometric fact:

```
J1 pad row, south edge of the copper    y = 79.535
USB_D_MCU_N, north edge of the copper   y = 78.850
free strip on F.Cu                          0.685 mm

a 0.20 mm track in that strip needs
   0.10 (half width) + 0.20 (to J1 pad, global)   ->  centre <= 79.235
   0.10 (half width) + 0.30 (to USB, LED_BOOST)   ->  centre >= 79.250
                                                      SHORT BY 0.015 mm
at 0.25 mm to the USB track                       ->  centre >= 79.200
                                                      FITS, 0.035 mm spare
```

---

## 3. What the routing actually does

Every net was routed against the DRC-accurate obstacle model: 0.20 mm tracks,
elevated clearances applied when **either** side carries the netclass, pads
excluded per the rule text, rule areas tested against the real copper outline,
through vias occupying all four layers.

### 3.1 No net is individually blocked

Measured one at a time, with no other backlight copper present, **all five nets
have a fully connected free region between their two pads at the enforced
0.30 mm.** There is no per-net wall.

The pass-3 statement that three of five were "blocked at 0.30 mm" was an
artifact of routing them in sequence: the first nets take the corridor the later
ones need. That correction matters, because it changes the problem from "the
rule forbids it" to "the fan-out needs to be routed as one nested structure".

### 3.2 Order matters, and is not sufficient

| routing order | result at 0.30 mm |
|---|---|
| `A1 A2 A3 A4 K BOOST` | 3 of 6 |
| `K BOOST A1 A2 A3 A4` | 2 of 6 |
| `A4 A3 A2 A1 K BOOST` | **4 of 6** — best of 60 orders × 3 via costs |

### 3.3 The clearance at which it completes

| `LED_BOOST` routed clearance | result |
|---|---|
| 0.30 mm (enforced today) | 4 of 6 — `LED_A1`, `LED_A3` blocked |
| 0.28 mm | 5 of 6 — `LED_A2` blocked |
| 0.26 mm | 5 of 6 — `LED_A2` blocked |
| **0.25 mm** | **6 of 6 — 53 segments, 5 vias** |

### 3.4 The minimal exception

Relaxing all six nets is unnecessary. Searching every subset:

> **The smallest set that completes the string is `LED_A2`, `LED_A3`, `LED_A4`
> and `LED_K` at 0.25 mm. `LED_A1` and `LED_BOOST` keep the full 0.30 mm.**

No subset of three or fewer completes it — all 42 subsets of size ≤ 3 were
tested and the best reached 5 of 6.

### 3.5 Where the solution is actually tight

Measured on the final geometry, not on the router's map:

| gap | A | B | layer | note |
|---|---|---|---|---|
| **0.236 mm** | `LED_A3` via (48.050, 81.400) | `LED_K` | B.Cu | inside the string |
| 0.250 mm | `LED_K` | `+3V3` via (46.150, 81.400) | B.Cu | **foreign** |
| 0.250 mm | `LED_A4` | `USB_D_MCU_N` track | F.Cu | **foreign** |
| 0.252 mm | `LED_K` via (50.200, 82.050) | `LED_A1` | F.Cu | inside the string |
| 0.253 mm | `LED_A3` | `LED_A4` | F.Cu | inside the string |
| 0.272–0.295 mm | eight further pairs | | | all inside the string |

**Only two of the fourteen sub-0.30 mm pairs involve a foreign net.** The other
twelve are backlight-to-backlight, where the whole string spans about 4.0 V in
operation (`LED_BOOST` ≈ 4.2 V to `LED_K` ≈ 0.2 V) and anode-to-anode is within
millivolts.

---

## 4. Proposed scoped areas — for ruling, not for landing

Same construction as the existing `E6_*` pockets: a named rule area, the
exception granted only to copper of the netclass **wholly enclosed** by it, pads
excluded, placed last in the file so it takes precedence.

### 4.1 `E6_BL_FANOUT_CLR` — F.Cu

```
layer   F.Cu
polygon (47.600, 79.050) (50.550, 79.050) (50.550, 85.050) (47.600, 85.050)
size    2.950 x 6.000 mm
```

```
(rule "E6_BL_FANOUT: measured local backlight clearance 0.250 mm"
	(constraint clearance (min 0.250mm))
	(condition "A.hasNetclass('LED_BOOST') && A.Type != 'Pad' && A.enclosedByArea('E6_BL_FANOUT_CLR')"))
```

### 4.2 `E6_BL_K_RETURN_CLR` — B.Cu

```
layer   B.Cu
polygon (46.000, 80.450) (48.200, 80.450) (48.200, 82.000) (46.000, 82.000)
size    2.200 x 1.550 mm
```

```
(rule "E6_BL_K_RETURN: measured local backlight clearance 0.250 mm"
	(constraint clearance (min 0.250mm))
	(condition "A.hasNetclass('LED_BOOST') && A.Type != 'Pad' && A.enclosedByArea('E6_BL_K_RETURN_CLR')"))
```

Track **width** stays 0.20 mm, so unlike the `+3V3` pockets no paired `_WIDTH`
area is needed. **No `In2.Cu` area is needed** — the solution has no sub-0.30 mm
site on the inner layer.

### 4.3 Leak probes

What foreign copper sits inside the proposed areas, i.e. what would gain the
0.25 mm allowance:

| area | foreign tracks / vias inside | foreign pads inside |
|---|---|---|
| `E6_BL_FANOUT_CLR` (F.Cu) | **none** | none — the only pads inside are `J1.1`–`J1.5`, the backlight pins themselves, and pads are excluded by the rule text |
| `E6_BL_K_RETURN_CLR` (B.Cu) | `+3V3` — two 0.50 mm tracks and the via at (46.150, 81.400) | none |

The counterparties reached from *outside* the F.Cu area are `USB_D_MCU_N` and
`USB_D_MCU_P` at y = 78.725 / 78.275, immediately south of it. Those two, plus
`+3V3` on B.Cu, are the **complete** list of foreign nets that would ever see
0.25 mm instead of 0.30 mm. Nothing else on the board is affected.

Rules **not** relaxed, and verified still met by the scratch solution:

| rule | limit | measured |
|---|---|---|
| track to foreign **pad** | 0.200 mm | **0.200 mm** (`LED_A4` vs `J1.4`) — at the limit, not below |
| copper to **hole** | 0.250 mm | 6.325 mm |
| global clearance elsewhere | 0.200 mm | unaffected |

---

## 5. Standards comparison

### 5.1 IPC-2221 electrical conductor spacing

The question is the peak voltage **between** the two conductors.

| condition | voltage between conductors | B1 internal | B4 external, permanent polymer coating |
|---|---|---|---|
| normal operation, anywhere in the string | ≤ ~4.2 V (0–15 V band) | 0.05 mm | 0.05 mm |
| backlight to `USB_D_MCU_N` / `+3V3`, normal | ≤ ~4.2 V (0–15 V band) | 0.05 mm | 0.05 mm |
| all-LEDs-open fault, `LED_BOOST` / `LED_A*` at the OVP clamp | 31–50 V band | 0.10 mm | 0.13 mm |

These traces run under solder mask, which is the B4 case. The B2 row — external
conductors **uncoated** — asks 0.60 mm at 31–50 V and would not be met by the
present 0.30 mm rule either; it does not apply to masked copper.

**Margin at the proposed 0.25 mm against the worst applicable row (B4,
31–50 V, 0.13 mm): 1.9×. Against the operating condition: 5.0×.** The tightest
measured pair, 0.236 mm, still gives 1.8× and 4.7×.

### 5.2 JLCPCB manufacturability

| parameter | JLCPCB 4-layer capability | proposed | margin |
|---|---|---|---|
| minimum trace width | 0.09 mm (3.5 mil) | 0.200 mm | **2.2×** |
| minimum trace spacing | 0.09 mm (3.5 mil) | 0.250 mm rule, 0.236 mm worst measured | **2.8× / 2.6×** |

For scale, the `E6` pockets already ratified on this board run at **0.100 mm**
(`E6_R2_1`), **0.120 mm** (`E6_J1_42`), **0.140 mm** (`E6_R11_1`) and
**0.160 mm** (`E6_R29_1`). A 0.250 mm backlight pocket would be by a wide margin
the **loosest** exception on the board — 2.5× the tightest one already approved.

---

## 6. Recommendation, for ruling

1. **Confirm the TPS61169 OVP threshold from the datasheet and specify `C44`
   accordingly.** That is a real electrical gap and it is independent of
   routing.
2. **Correct the DRU's premise.** The comment says the string "runs above 20 V";
   it runs at about 4.2 V and only approaches the driver's clamp in an open-LED
   fault. Whatever figure is ratified should be justified by the fault case and
   stated as such.
3. If an exception is granted, grant **0.25 mm inside the two named areas in
   §4**, to `LED_A2` / `LED_A3` / `LED_A4` / `LED_K` only. That is the measured
   minimum that completes the string, its leak set is three nets, and it is the
   loosest E6 pocket on the board.
4. **A global `LED_BOOST` relaxation remains the wrong instrument** and is not
   proposed here: it would hand 0.25 mm to every backlight-class conductor
   everywhere, including the `LED_BOOST` rail itself, for the sake of two
   0.250 mm sites.
5. Worth weighing as an alternative: moving `USB_D_MCU_N` south by 0.05 mm, or
   moving the `+3V3` via at (46.150, 81.400), would each remove one of the two
   foreign-net sites with **no rule change at all**. Both are outside this
   pass's authority and are noted, not attempted.

**Nothing in this document has been landed.** The scratch route — 53 segments,
5 vias — exists only as an out-of-tree JSON artifact and is reproducible from
the tooling.
