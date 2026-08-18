# AQROOT Beta DM — RF feed readiness, and the IR TX ruling

Measured on the Beta-DM copy of `0f53205`.

---

## 1. RF feed readiness — both radios

Neither radio is deferred. Both are DM must-work, and both are in better shape
than expected: **every signal net on both radios is already fully routed.**

### 1.1 SX1262 / 915 MHz (U8, Ebyte E22-900M22S at 65.000, 128.000)

| net | pads | segments | vias | ratsnest |
|---|---|---|---|---|
| `/SPI_B_SCK` | 4 | 36 | — | **0** |
| `/SPI_B_MOSI` | 4 | 35 | — | **0** |
| `/SPI_B_MISO` | 4 | 35 | — | **0** |
| `/SX1262_CS_N` | 3 | 17 | 2 | **0** |
| `/SX1262_BUSY` | 2 | 19 | 4 | **0** |
| `/SX1262_DIO1` | 2 | 14 | 5 | **0** |
| `/SX1262_RST_N` | 3 | 18 | 7 | **0** |
| `/SX1262_RXEN` | 3 | 18 | 4 | **0** |
| `DIO2_TXEN` (U8.7↔U8.8 module strap) | 2 | — | — | **0** |
| `+3V3` at U8.9 | — | — | — | **0** |

Control ownership: `RXEN` from `U3.P16` with the `R74` 100 k pull-down that
holds the RF switch in CLOSE while the expander is high-Z; `RST_N` from
`U2.P01` with `R13`; `TXEN` strapped to `DIO2` on the module so the radio drives
its own switch.

### 1.2 CC1101 / 433 MHz (U7, Ebyte E07-400M10S at 55.500, 146.500)

| net | pads | segments | vias | ratsnest |
|---|---|---|---|---|
| `/CC1101_CS_N` | 3 | 17 | 5 | **0** |
| `/CC1101_GDO0` | 2 | 25 | 7 | **0** |
| `/SPI_B_*` shared | — | — | — | **0** |
| `+3V3` at U7.9 | — | — | — | **0** |

### 1.3 RF traces — there are none, by design

`U8.21` → `/04_SPI_B_RADIOS_NFC/RF_ANT_TBD` and `U7.21` →
`/04_SPI_B_RADIOS_NFC/CC1101_ANT_TBD` are **single-node nets with zero copper,
deliberately**. The DRU rule *"RF_DO_NOT_ROUTE: U7/U8 pin-21 stamp RF pads carry
no PCB feed"* enforces it. Both modules carry their own certified front end and
present a matched 50 Ω IPEX port; the antenna plugs onto that port, so the board
never carries 433 or 915 MHz energy.

**Therefore: no RF trace work, no matching network, no board-level RF connector
is outstanding for either radio.** Do not add one; the RF plan explicitly says
the module IPEX port *is* the NanoVNA test port.

### 1.4 Exact remaining work per radio

| item | SX1262 / 915 | CC1101 / 433 |
|---|---|---|
| RF traces | **none — by design** | **none — by design** |
| matching / support parts | **none** | **none** |
| board connector | **none** | **none** |
| signal routing | **complete, 0 ratsnest** | **complete, 0 ratsnest** |
| power routing | `+3V3` complete | `+3V3` complete |
| **GND** | **17 ratsnest lines to stitch** | **15 ratsnest lines to stitch** |
| flex antenna | Taoglas FXP890.07.0100C on the module IPEX — mechanical install and in-enclosure placement | Taoglas FXP450.07.0100C on the module IPEX — mechanical install; 433 is electrically small, so placement and tuning dominate |
| bring-up dependencies | ESP32-S3 core, SPI-B, `U2`/`U3` expanders (for `RST_N`/`RXEN`), `+3V3`, GND stitching | ESP32-S3 core, SPI-B, `+3V3`, GND stitching |
| firmware | radio manager enforcing one-TX-at-a-time and driving the idle radio's CS high (a floating CS on the idle radio corrupts shared MISO — learned in Alpha) | CC1101 driver does not exist yet; tracked in the Build TODO |

The single shared blocker for both radios is **GND finalisation** — part of the
board-wide 164-line GND job, not an RF-specific task.

> Note for the routing program: the microphone bus needs release **R6**, a
> 0.200 mm southward move of the `/SX1262_RXEN` B.Cu run at y = 10.800. That
> touches a must-work radio net and is called out in
> [BETA-DM-MCU-RELEASE.md](BETA-DM-MCU-RELEASE.md) §5 rather than being folded
> silently into the audio work. `RXEN` is a static enable held low by `R74`; a
> 0.2 mm move has no signal-integrity consequence.

---

## 2. IR TX — audit result

**Question asked:** can `GPIO16` / `IR_TX` be routed under ordinary current
rules with no hard-lock release, no USB change, no DRU change and no component
move?

**Answer: no.**

`IR_TX_GPIO16` runs `U1.9` (IO16, at 17.650, 17.250 on U1's **north** pad row)
to `R22.1` (at 60.125, 11.400, B.Cu).

| end | escape cells at baseline |
|---|---|
| `R22.1` | **274** — the IR end is wide open |
| `U1.9` | **0** — and **no single-object release** restores it |

`U1.9` is boxed in on the north row by two In2 trunks that straddle it at
0.15 mm and 0.55 mm: `/I2C_SDA_INT` at x = 17.500 and `/I2C_SCL_INT` at
x = 18.200. A 0.60/0.30 via at x = 17.650 needs 0.60 mm of clearance from a
0.20 mm trunk centreline, so both must go.

An exhaustive pair sweep over the 20 objects within 2.2 mm of `U1.9` finds
exactly **two** 2-object releases that open it:

| pair | escape cells |
|---|---|
| `+3V3` F.Cu (19.975,17.100)-(12.180,17.550) **+** `/I2C_SDA_INT` In2 | 78 |
| `/I2C_SDA_INT` In2 **+** `/SPI_B_SCK` F.Cu (25.775,16.200)-(11.300,16.200) | 22 |

`/I2C_SDA_INT` In2 is release **R1**, which DM is taking anyway for `I2S_BCLK`.
So IR_TX's marginal cost over the DM baseline is **one additional release** —
but the only two candidates are a **+3V3 power bar** or the **SPI_B_SCK F.Cu
escape bar** feeding a must-work radio bus. Neither is a trivial fix, and the
second lands on the same net as release R5.

**Ruling taken: DEFER IR_TX for the Demo Model**, per the standing instruction
not to spend a major architecture cycle for an IR demo. All IR TX parts
(`D1`, `Q1`, `R22`, `R23`, `R24`, `C12`) become DNP alongside the already-
deferred receiver, and `IR_TX_GPIO16` is not routed.

Returned for ruling, not decided here: if IR TX is later judged demo-critical,
the cheapest route is `R1` (already taken) plus a release of the `+3V3` F.Cu
bar at y ≈ 17.10–17.55, which yields 78 escape cells. That is a power-net
rework in the densest part of the board and should be costed properly first.

`IR_RX` stays deferred independently: `U1.36` has **zero** escape cells and
**no** single-object release exists for it — the only demand in the U1 south
row for which that is true.
