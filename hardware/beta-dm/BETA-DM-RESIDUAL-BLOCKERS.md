# AQROOT Beta DM — residual routing blockers, returned for ruling

This pass stopped short of completing the residual program **on purpose**. Per
the standing process rule, work that would cross a hard lock is returned with
evidence instead of landed. Everything in this file is measured on the board at
the GND-stitching commit, at the enforced 0.20 mm clearance (0.30 mm where an
elevated netclass applies), with no rule relaxed.

## Summary

| item | lines | status |
|---|---|---|
| `BOOT_N` | 3 | **BLOCKED by hard-locked copper — ruling required** |
| J5/F4 header interconnect | 41 | **BLOCKED by congestion inside the hard-locked header region** |
| display backlight string | 5 | **3 of 5 blocked** at the LED_BOOST 0.30 mm clearance |
| charger status, MCU test points, `SW9-A`, `U15-QOD` | 14 | blocked; local congestion |
| **total must-work non-GND still open** | **63** | |

Nothing here is a defect in the copper already landed. Every one of these is a
route that does not exist at the current geometry.

---

## 1. `BOOT_N` — blocked by the hard-locked I2S, and then by SPI-A and +3V3

`BOOT_N` is mandatory programming and recovery access: `U1.27` (IO0) ↔ `R2.2`
(10 k pull-up) ↔ `SW1.1` (BOOT button).

### 1.1 What blocks it

`U1.27` sits at (24.000, 34.750) on B.Cu. It has **zero escape cells**.

The immediate blocker is `/I2S_LRCLK` on **F.Cu**, which runs
(23.100, 34.100)–(24.300, 34.100) — straight across `U1.27`'s escape window —
as part of a diagonal that spans x 21.5→25.1, y 32.6→34.1. That is copper this
programme landed and the CTO has since **hard-locked**.

Measured: with 17 of those `I2S_LRCLK` F.Cu segments (**6.008 mm**) released,
`BOOT_N` regains **6 escape cells**, including the originally reserved site
(23.750, 34.150) on F.Cu / In2.Cu. And `I2S_LRCLK` re-lands in **6.001 mm with
0 vias** — a net change of −0.007 mm. As hard-lock touches go this is about as
cheap as one can be.

### 1.2 But that alone is not enough

With the `LRCLK` stretch released, `U1.27` reaches an F.Cu pocket of
x 17.50–25.15, y 29.90–35.60, and `R2.2` reaches a *different* F.Cu pocket of
x 23.05–25.60, y 34.75–38.55. The two overlap spatially but are separate
components. `SW1.1` reaches the whole board.

The barrier between them, measured:

| copper | net | status |
|---|---|---|
| F.Cu (25.200,34.300)–(24.100,36.200) | `/SD_CS_N` | **SPI-A — hard-locked** |
| F.Cu (21.945,35.850)–(23.300,36.000), 0.40 mm | `+3V3` | **R2.1 E6 escape — hard-locked, and it carries the Tier-B `E6_R2_1` 0.100 mm measured-clearance exception** |
| F.Cu (24.400,31.950)–(27.250,34.800) | `/I2S_BCLK` | **I2S — hard-locked** |

So completing `BOOT_N` needs the `I2S_LRCLK` stretch **plus** one of `SD_CS_N`
(SPI-A) or the `+3V3` R2.1 escape. That is a two-lock conflict, which is why it
is being returned rather than forced.

### 1.3 Options, for ruling

| # | option | cost | risk |
|---|---|---|---|
| A | release 6.008 mm of `I2S_LRCLK` F.Cu **and** re-route the `/SD_CS_N` F.Cu diagonal | LRCLK re-land proven at 6.001 mm / 0 vias; SD_CS_N re-land not yet costed | opens I2S and SPI-A |
| B | release the `I2S_LRCLK` stretch **and** the `+3V3` R2.1 escape bar | LRCLK proven; +3V3 re-land would have to re-derive the `E6_R2_1` measured clearance | opens I2S and a Tier-B E6 pocket — the most delicate copper on the board |
| C | move `R2` a short distance | forbidden this pass (no component moves) | needs a placement ruling; probably the cheapest real fix |
| D | accept `BOOT_N` unrouted and program via USB only | zero copper | **loses hardware BOOT/recovery access** — recommend against |

**Recommendation: C, then A.** `R2` is a 0603 pull-up whose only constraint is
proximity to `U1.27`; a 1–2 mm move opens the corridor without touching any
routed net. If component moves stay forbidden, A is the next cheapest because
the `+3V3` E6 pocket in B is the highest-risk copper on the board.

---

## 2. J5 / F4 header interconnect — 41 lines, blocked by congestion

The header cluster (x 30–52, y 9–14) holds two rows of series resistors between
`U3`/`U15`/`U16` and the `D3`–`D7` ESD diodes, all inside the hard-locked
J5/F4 region and the `HEADER RESERVED` rule area.

Attempted all 37 header-cluster nets on a focused grid. **3 routed**
(`WAKE_ATTN_N_HDR`, `XGPIO2_HDR`, `XGPIO3_HDR`); **34 failed**.

The systematic pattern, from geometric island analysis: on every header net the
**series resistor and the J5 pin are already connected**, and the **ESD diode
pin is a separate island**. The entire J5 ESD protection network is unrouted —
14 `XGPIO*`, `WAKE_ATTN_N`, `FAST_IO_GPIO43` and both external-I2C lines.
`ACC_3V3_SW` is in **8 islands** and is effectively unrouted as a rail.

Reachability measured for `FAST_IO_GPIO43_HDR`: the J5-side island reaches only
21 977 cells bounded to x 14.85–31.85, y 3.75–14.85 — it cannot get out to
where the diode roams. The region is saturated.

The three routable nets were **deliberately not landed**: landing 3 of 37 would
consume space the remaining 34 need and make a proper header program harder.

**This needs a dedicated header-completion program, not opportunistic routing.**
It is also worth a ruling on whether the DM demo needs the ESD network populated
and connected at all, given `D3`–`D7` are fitted but their protection is
currently not attached to anything.

---

## 3. Display backlight — 3 of 5 blocked

`LED_A1`…`LED_A4` and `LED_K` carry the `LED_BOOST` netclass, which the DRU
gives an **elevated 0.30 mm routed clearance** because the backlight string runs
above 20 V.

At 0.20 mm all five routed. At the correct 0.30 mm only **`LED_A1` (4.874 mm)**
and **`LED_A3` (2.528 mm)** route; `LED_A2`, `LED_A4` and `LED_K` fail.

This was caught by the analytic validator before anything landed — the router
had been applying only the *obstacle's* netclass clearance, not the routed net's.
Fixed, and the two routable nets were not landed because two of four anodes plus
no cathode is not a usable backlight.

---

## 4. Remaining power / control — 14 lines

| net | lines | why open |
|---|---|---|
| `Net-(SW9-A)` | 4 | hard-off switch → `U12.EN`, `R43`, `TP13`. Islands 1/2 unroutable |
| `/ACC_PWR_EN` | 3 | `R17`/`U15.3`/`U16.5`/`U3.20` — inside the saturated header cluster |
| `Net-(U15-QOD)` | 1 | `R46.1` ↔ `U15.5`, header cluster |
| `Net-(U16-SCLB)` / `SDAB` | 2 | buffered external I2C, header cluster |
| `/01_POWER_TREE/BQ25185_STAT1` / `STAT2` | 2 | `U11` WSON-10 0.4 mm pitch → `TP6`/`TP7` |
| `/02_MCU_CORE/TEST_GPIO45` / `46` | 2 | `U1` → `TP1`/`TP2` |

`SW9-A` is the physical power switch and is the most functionally important of
these. The rest are status and test-point nets.

Note on the fine-pitch packages: the DRU's "pad-escape necking" rules set
`track_width min 0.20` and `clearance min 0.20` inside the `U11`/`U12`/`U13`/
`U14`/`U17`/`U9` courtyards. They **confirm** 0.20/0.20 rather than relaxing
below it, so there is no unused headroom there — the model already routes at the
allowed minimum.

---

## 5. What this means for pours

Pours are explicitly last, and only after `BOOT_N` is complete. `BOOT_N` is
blocked, so **pours were not created in this pass**. That is also the right
engineering call: pouring now would have to be undone by whichever remedy the
`BOOT_N` ruling selects, and by the header program.

The GND stitching that does not depend on any of this — both radios and the
microphone — **was** completed and landed.
