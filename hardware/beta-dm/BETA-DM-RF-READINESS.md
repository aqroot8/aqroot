# AQROOT Beta DM — RF and antenna readiness

Re-audited from the **current** Beta-DM board, not from an earlier report.
Both radios are Demo Model must-work and neither is deferred.

---

## 1. SX1262 / 915 MHz — U8 Ebyte E22-900M22S at (65.000, 128.000), B.Cu

### 1.1 Electrical state, measured

| signal | MCU / driver | module pin | pads | segments | vias | **ratsnest** |
|---|---|---|---|---|---|---|
| `SPI_B_SCK` | U1.4 (IO4) | U8.18 | 4 | 27 | 5 | **0** |
| `SPI_B_MOSI` | U1.5 (IO5) | U8.17 | 4 | 25 | 6 | **0** |
| `SPI_B_MISO` | U1.6 (IO6) | U8.16 | 4 | 23 | 8 | **0** |
| `SX1262_CS_N` | U1.10 (IO17) + R27 pull-up | U8.19 | 3 | 17 | 2 | **0** |
| `SX1262_BUSY` | U1.12 (IO8) | U8.14 | 2 | 19 | 4 | **0** |
| `SX1262_DIO1` | U1.31 (IO38) | U8.13 | 2 | 14 | 5 | **0** |
| `SX1262_RST_N` | **U2.P01** expander + R13 | U8.15 | 3 | 18 | 7 | **0** |
| `SX1262_RXEN` | **U3.P16** expander + R74 pull-down | U8.6 | 3 | 18 | 4 | **0** |
| `TXEN` | strapped to `DIO2` on the module | U8.7 ↔ U8.8 | 2 | 1 | 0 | **0** |
| `+3V3` | main rail | U8.9 | 76 | 323 | 36 | **0** |
| `RF_ANT_TBD` | — | U8.21 | 1 | **0** | 0 | **0** |

**Every control, data and power net on the SX1262 is fully routed with zero
ratsnest.** Counts are as measured on the board at the DNP-variant commit; the
R5 release re-lands `SPI_B_SCK` on a different path, which changes its segment
count but not its connectivity — it stays one island with zero ratsnest.

Two control lines come from **I2C port expanders, not the MCU** — `RST_N` from
U2.P01 and `RXEN` from U3.P16. The internal I2C bus must be alive before the
radio can be reset or its receive path enabled. This is a firmware sequencing
dependency, not a routing gap, and the acceptance procedure tests it explicitly.

### 1.2 RF output path

`U8.21` (`RF_ANT_TBD`) is a **single-node net with zero copper, deliberately**.
The DRU rule *"RF_DO_NOT_ROUTE: U7/U8 pin-21 stamp RF pads carry no PCB feed"*
makes routing it a DRC error. The E22-900M22S carries its own certified front
end and presents a matched 50 Ω **IPEX/u.FL port on the module**, so no 915 MHz
energy ever travels on this PCB.

There is therefore **no RF trace to design, no matching network to tune, and no
board-mounted RF connector to fit.**

### 1.3 Remaining work

| item | state |
|---|---|
| RF traces | **none — by design** |
| matching / support parts | **none** |
| board RF connector | **none — the connector is on the module** |
| signal routing | **complete, 0 ratsnest** |
| power routing | **complete, 0 ratsnest** |
| **GND stitching** | **17 ratsnest lines on U8** — the only electrical work left |
| antenna | Taoglas FXP890.07.0100C flex, plugs onto the module IPEX port — **mechanical install** |
| firmware | radio manager enforcing one-TX-at-a-time and driving the idle radio's CS high |

---

## 2. CC1101 / 433 MHz — U7 Ebyte E07-400M10S at (55.500, 146.500), B.Cu

### 2.1 Electrical state, measured

| signal | MCU / driver | module pin | pads | segments | vias | **ratsnest** |
|---|---|---|---|---|---|---|
| `SPI_B_SCK` | U1.4 (IO4) | U7.18 | shared | — | — | **0** |
| `SPI_B_MOSI` | U1.5 (IO5) | U7.17 | shared | — | — | **0** |
| `SPI_B_MISO` | U1.6 (IO6) | U7.16 | shared | — | — | **0** |
| `CC1101_CS_N` | U1.7 (IO7) + R28 pull-up | U7.19 | 3 | 17 | 5 | **0** |
| `CC1101_GDO0` | U1.8 (IO15) | U7.15 | 2 | 25 | 7 | **0** |
| `+3V3` | main rail | U7.9 | — | — | — | **0** |
| `CC1101_ANT_TBD` | — | U7.21 | 1 | **0** | 0 | **0** |

**Every CC1101 net is fully routed with zero ratsnest.**

### 2.2 RF output path

Same architecture as the SX1262: `U7.21` is a single-node net with no copper,
stamped `RF_DO_NOT_ROUTE`. The E07-400M10S has its own front end and a matched
IPEX port.

### 2.3 Remaining work

| item | state |
|---|---|
| RF traces / matching / board connector | **none — by design** |
| signal + power routing | **complete, 0 ratsnest** |
| **GND stitching** | **15 ratsnest lines on U7** |
| antenna | Taoglas FXP450.07.0100C flex on the module IPEX port — **mechanical install** |
| firmware | no CC1101 driver exists yet; tracked in the Build TODO |

---

## 3. Antenna and mechanical readiness

Do **not** redesign the antenna architecture. It is settled: certified modules,
IPEX ports, hidden flex antennas, no board RF.

| question | 915 MHz | 433 MHz |
|---|---|---|
| electrical path complete? | **Yes** — nothing on the PCB by design; module front end is the path | **Yes** — same |
| connector fitted? | **Yes, and it is on the module.** The IPEX/u.FL port is part of U8; there is no board-mounted RF connector to fit or forget | **Yes, on U7** |
| flex antenna install required? | **Yes** — Taoglas FXP890.07.0100C, u.FL cable onto the module port, adhered inside the enclosure | **Yes** — Taoglas FXP450.07.0100C, same method |
| enclosure placement dependency? | **Yes** — plastic only in front of the radiator, away from the normal grip, and away from the 2.4 GHz WROOM antenna for coexistence | **Yes, and harder.** 433 MHz is electrically small in this volume; the RF crown gives it the most room and placement dominates performance |
| keepout preserved? | **Yes** — see §4 | **Yes** — see §4 |
| test access | the module IPEX port **is** the test port: unplug the flex, connect the NanoVNA there. Do not add a separate U.FL test connector | same |

## 4. Keepout preservation, verified on the current board

| rule area | layers | policy | bbox |
|---|---|---|---|
| `915 KEEPOUT` | F.Cu, B.Cu, In2.Cu | no copper pour | (0, 88) – (74, 114) |
| `433 KEEPOUT` | F.Cu, B.Cu, In2.Cu | no copper pour | (0, 115) – (52.5, 138) |
| `WROOM ANTENNA KEEPOUT` | all four | nothing at all | (0, 17) – (6, 35) |
| plus the ESP32-S3 footprint's own embedded keepout | all four | nothing at all | (−15, 2) – (6, 50) |

Measured copper inside the two RF bands:

| band | segments | vias | layers used | nets |
|---|---|---|---|---|
| 915 | 14 | **0** | F.Cu only | `BTN_LEFT_N`, `BTN_RIGHT_N`, `BTN_UP_N`, GND button-side escapes |
| 433 | 15 | **0** | F.Cu only | `BTN_A_N`, `BTN_DOWN_N`, `BTN_HOME_N`, GND button-side escapes |

That is exactly the sanctioned E2 exception set and nothing else: **no B.Cu, no
In2, and zero vias in either band**, which is what the DRU requires. The DM work
in this pass added no copper to either band.

---

## 5. Verdict

| | |
|---|---|
| SX1262 hardware | **READY** — pending GND stitching (17) and the flex install |
| CC1101 hardware | **READY** — pending GND stitching (15) and the flex install |
| 915 antenna path | **READY** — no board work exists or is needed; mechanical install only |
| 433 antenna path | **READY** — no board work; mechanical install, with placement and in-enclosure tuning as the real risk |

The single shared blocker for both radios is **GND finalisation**, which is
board-wide work, not RF work. See `BETA-DM-UNROUTED-LEDGER.md` bucket B.
