# AQROOT Beta DM — intentional-unrouted ledger

Every ratsnest line on the Beta-DM board is accounted for here. The point of
this file is that **nothing is unexplained**: at any DM audit, the remaining
unconnected count must equal the sum of these four buckets, and any line that
does not fall into one of them is a defect, not a deferral.

Measured on the Beta-DM board after the residual-copper and GND-stitching
commits. Total unconnected: **230**.

| bucket | ratsnest lines | nets |
|---|---|---|
| A — intentional DM deferral (DNP function) | **37** | 21 |
| B — GND, pours pending | **130** | 1 |
| C — must-work still open (see the blockers document) | **63** | 48 |
| **total** | **230** | **70** |

History: 281 after the I2S landed → 278 → **264** after FAST_IO, the USB-C CC
pair, the shield and the critical power controls → **239** after GND stitching
at both radios and the microphone → **230** after stitching the USB-C connector,
the MCU and the pull-to-ground parts.

Bucket C is enumerated and evidenced in
[BETA-DM-RESIDUAL-BLOCKERS.md](BETA-DM-RESIDUAL-BLOCKERS.md): `BOOT_N` (3) is
blocked by hard-locked copper and returned for ruling; the J5/F4 header
interconnect (41) needs a dedicated program; the display backlight (5) is
partly blocked at its elevated 0.30 mm clearance; and 14 power/status/test lines
are blocked by local congestion. **Nothing in bucket C is unexplained.**

---

## A — intentional DM deferral: 37 lines, 21 nets

These are unrouted **because the function is DNP on the Demo Model**. They are
not defects and must not be "fixed" by routing them. Every one restores for the
Final product.

### A.1 NFC front end and its 5 V PA rail — `U9`, `U13` block DNP

| net | lines | why unrouted |
|---|---|---|
| `/NFC_CS_N` | 2 | U9 DNP. Also the net whose absence makes a fitted U9 unsafe. |
| `/NFC_IRQ` | 1 | U9 DNP |
| `/04_SPI_B_RADIOS_NFC/NFC_VDD_D` | 2 | U9 regulator output, U9 DNP |
| `/04_SPI_B_RADIOS_NFC/NFC_VDD_A` | 2 | U9 regulator output, U9 DNP |
| `/04_SPI_B_RADIOS_NFC/NFC_VDD_RF` | 3 | U9 regulator output, U9 DNP |
| `/04_SPI_B_RADIOS_NFC/NFC_VDD_AM` | 2 | U9 regulator output, U9 DNP |
| `/04_SPI_B_RADIOS_NFC/NFC_AGDC` | 2 | U9 reference, U9 DNP |
| `/NFC_5V_PA_PENDING` | 5 | boost output, U13 DNP and no load |
| `/NFC_5V_EN` | 3 | boost enable, U13 DNP |

Also permanently unrouted by DRU rule, and carrying **no** ratsnest because they
are single-node nets: `NFC_RFO1_TBD`, `NFC_RFO2_TBD`, `NFC_RFI1_TBD`,
`NFC_RFI2_TBD`, `NFC_AAT_A_TBD`, `NFC_AAT_B_TBD`, `NFC_EXT_LM_TBD`,
`NFC_CSI_TBD`, `NFC_CSO_TBD`, `NFC_XIN_TBD`, `NFC_XOUT_TBD`,
`NFC_MCU_CLK_TBD`. The NFC loop, matching network and crystal were never
designed; the `RF_DEFERRED_NFC` netclass makes routing them a DRC error.

`Net-(U13-FB)` and `Net-(U13-SW)` have no ratsnest because every node on them is
DNP — they are entirely dead on DM.

### A.2 Speaker — `U5`, `J6` DNP

| net | lines | why unrouted |
|---|---|---|
| `/I2S_SPK_DOUT` | 1 | sink U5.1 is DNP |
| `/AMP_SD_MODE` | 2 | no amplifier to mute; R15 stays fitted but has nothing to hold off |
| `/06_AUDIO/SPK_P` | 1 | both nodes DNP |
| `/06_AUDIO/SPK_N` | 1 | both nodes DNP |

### A.2b The two permanent I2S residuals — `U5` DNP

| net | lines | why unrouted |
|---|---|---|
| `/I2S_BCLK` | 1 | the routed net connects U1.32 to MK1.4; the remaining line is the **U5.16 amplifier pad**, which the DNP ledger says not to route |
| `/I2S_LRCLK` | 1 | same — the remaining line is **U5.14** |

KiCad's connectivity engine reports each of these nets as two islands: the
fitted circuit, and a single isolated `U5` pad. That is the correct DM state and
it does not change. `/I2S_MIC_DIN` is **one island** with zero ratsnest.

### A.3 IR — transmitter and receiver deferred

| net | lines | why unrouted |
|---|---|---|
| `/IR_TX_GPIO16` | 1 | IR TX deferred. `U1.9` also has **zero** escape cells and needs a two-object release. |
| `/IR_RX_GPIO44` | 1 | IR RX deferred. `U1.36` has **zero** escape cells and **no** single-object release exists. |
| `/07_IR/IR_GATE` | 2 | Q1/R22/R23 DNP |
| `/07_IR/IR_LED_A` | 1 | D1/R24 DNP |
| `/07_IR/IR_LED_K` | 1 | D1/Q1 DNP |
| `/07_IR/IR_RX_VS_LOCAL` | 2 | U6/R21/C11 DNP |

---

## B — GND finalisation: 164 lines

One net. The `In1 GND REFERENCE` plane is drawn and filled and 27 GND stitching
vias exist, but most SMD ground pads still need a stitch via and a short stub.
This is board-wide work inherited from the Beta, not a DM cut, and it is the
single largest remaining job on the board.

Concentrations: `J1` 55, `U8` 17, `U7` 15, `J2` 9, `U2` 9, `U4` 6, `U3` 5,
`U5` 8 (DNP — those eight can be skipped), `U9` 4 (DNP), `MK1` 4, `U1` 4.

`MK1`'s four are now on the critical path: the microphone's data, clock and
word-select are routed, so ground is the last thing between it and working.

Both radios are gated on this: **`U8` needs 17 and `U7` needs 15** stitches
before either can be brought up.

---

## C — DM routing still to do: 5 lines, 3 nets

The microphone bus is landed. What remains of the DM demand set is `BOOT_N` and
`FAST_IO`, whose releases (R4 and R5) are already landed and whose escape sites
are **held clear and verified open**.

| net | lines | status |
|---|---|---|
| `/02_MCU_CORE/BOOT_N` | 3 | release R4 landed; escape site (23.750, 34.150) held and legal, **6 escape cells** |
| `/FAST_IO_U0TXD_ROOTPROBE_CS` | 1 | release R5 landed; escape site (11.300, 34.100) held and legal, **54 escape cells** |
| `/09_COMMUNITY_HEADER/FAST_IO_GPIO43_HDR` | 1 | header side of the same link |

The three `I2S` nets have left this bucket. `I2S_MIC_DIN` is fully connected;
`I2S_BCLK` and `I2S_LRCLK` are fully connected in the fitted circuit and keep
one line each for their DNP `U5` pad, which is bucket A.

---

## D — other remaining board work: 72 lines, 53 nets

Inherited from the full Beta. **Not DM cuts** — every one of these is Final
scope too and will be routed.

| group | lines |
|---|---|
| J5 community header: `XGPIO0..13` ↔ `XGPIO*_HDR` links | 28 |
| `/09_COMMUNITY_HEADER/ACC_3V3_SW` | 7 |
| `/ACC_PWR_EN` | 3 |
| external I2C `I2C_SDA_EXT_HDR` / `I2C_SCL_EXT_HDR` | 4 |
| `WAKE_ATTN_N_HDR` | 1 |
| display backlight string `LED_A1..A4`, `LED_K` | 5 |
| USB-C `J3` CC1 / CC2 / SHIELD | 6 |
| power tree: `SW9-A`, `U12-PG`, `U12-PS_SYNC`, `U15-CT`, `U15-QOD`, `U1-EN`, `BQ25185_STAT1/2` | 14 |
| I2C buffer `U16-SCLB` / `U16-SDAB` | 2 |
| MCU test pins `TEST_GPIO45` / `TEST_GPIO46` | 2 |

---

## Audit rule

At any Beta-DM audit:

```
unconnected(measured)  ==  A(intentional deferral) + B(GND) + C(DM work) + D(inherited)
        278            ==       37                 +   164   +      5     +      72
```

If the measured count exceeds the sum, something broke. If a net appears that is
in none of the four buckets, it is a defect and must be explained before the
board moves forward.
