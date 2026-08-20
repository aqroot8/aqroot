# AQROOT Beta DM — intentional-unrouted ledger

Every ratsnest line on the Beta-DM board is accounted for here. The point of
this file is that **nothing is unexplained**: at any DM audit the remaining
unconnected count must equal the sum of the three buckets below, and any line
that falls into none of them is a defect, not a deferral.

Measured on the board after Option W landed `BOOT_N` and the active-J5 residual
sweep closed four more lines. **Total unconnected: 216.**

| bucket | ratsnest lines | what it is |
|---|---|---|
| A — intentional DM deferral (DNP function) | **55** | at least one endpoint is a pad of a DNP part, or the whole net belongs to a deferred block |
| B — GND, pours pending | **130** | one net; the plane and stitching program |
| C — fitted must-work, still open | **31** | see [BETA-DM-BOOT-N-OPTION-W.md](BETA-DM-BOOT-N-OPTION-W.md) §7 |
| **total** | **216** | |

A is 55 rather than 53 because two lines that used to be counted in C —
`AMP_SD_MODE` to the DNP amplifier and the `NFC_5V_PA_PENDING` track-to-track
line — are filed by the rule they actually meet: a DNP pad at one end, or a
block that is DNP as a whole.

Buckets are assigned **per ratsnest line**, not per net: several header nets
have one line to a DNP ESD diode (bucket A) and another to a fitted resistor
(bucket C), and counting them per net would blur exactly the distinction this
ledger exists to make.

History: 281 after the I2S landed → 264 after `FAST_IO`, the USB-C CC pair, the
shield and the critical power controls → 239 after GND stitching at both radios
and the microphone → 230 after stitching the USB-C connector, the MCU and the
pull-to-ground parts → **225** after the display backlight closed its five
lines → **223** after `XGPIO2_HDR` and `XGPIO3_HDR` → **220** after Option W
landed `BOOT_N` → **216** after the active-J5 sweep closed `XGPIO6_HDR`, two
`Net-(SW9-A)` lines and one `ACC_3V3_SW` line.

The `D2`–`D7` DNP reclassification did not change the total; it moved 15 signal
lines from bucket C to bucket A.

---

## A — intentional DM deferral: 55 lines

These are unrouted **because the function is DNP on the Demo Model**. They are
not defects and must not be "fixed" by routing them. Every one restores for the
Final product.

Assignment rule, applied line by line: a line is bucket A if **a pad at either
end belongs to a DNP part**, or if **the net belongs to a block that is DNP as a
whole** (NFC front end, IR, speaker). The counts below are measured from the
board, not carried forward.

| block | lines | detail |
|---|---|---|
| NFC front end and its 5 V PA rail — `U9`, `U13` DNP | **22** | `NFC_5V_PA_PENDING` 5, `NFC_5V_EN` 3, `NFC_VDD_RF` 3, `NFC_AGDC` 2, `NFC_CS_N` 2, `NFC_VDD_A` 2, `NFC_VDD_AM` 2, `NFC_VDD_D` 2, `NFC_IRQ` 1 |
| Header ESD arrays and other DNP-pad links — `D2`–`D7`, `R49`, `R50`, `R68`, `U5` | **20** | `XGPIO0/1/4/5/7/8/9/10/11/12_HDR` 1 each, `I2C_SCL_EXT_HDR` 1, `I2C_SDA_EXT_HDR` 1, `FAST_IO_GPIO43_HDR` 1, `WAKE_ATTN_N_HDR` 1, `ACC_3V3_SW` 3 (to `R49`/`R50`), `Net-(SW9-A)` 1 (to `R68`), `I2S_BCLK` 1 and `I2S_LRCLK` 1 (the isolated `U5` pad) |
| IR transmitter and receiver — deferred | **8** | `IR_GATE` 2, `IR_RX_VS_LOCAL` 2, `IR_LED_A` 1, `IR_LED_K` 1, `IR_RX_GPIO44` 1, `IR_TX_GPIO16` 1 |
| Speaker — `U5`, `J6` DNP | **5** | `AMP_SD_MODE` 2, `I2S_SPK_DOUT` 1, `SPK_N` 1, `SPK_P` 1 |
| **total A** | **55** | |

`AMP_SD_MODE` carries two lines: `U5.4`–`U2.7`, which has a DNP pad, and
`U2.7`–`R15.1`, where both parts are fitted. The second is filed here anyway
because the function it serves — holding the DNP `U5` amplifier muted — is
deferred as a whole. It is listed so it is not silently forgotten, not because
the demo needs it. `NFC_5V_PA_PENDING` likewise includes one track-to-track
line with no pad at either end, inside a block that is DNP throughout.

Also permanently unrouted by DRU rule and carrying **no** ratsnest because they
are single-node nets: `NFC_RFO1_TBD`, `NFC_RFO2_TBD`, `NFC_RFI1_TBD`,
`NFC_RFI2_TBD`, `NFC_AAT_A_TBD`, `NFC_AAT_B_TBD`, `NFC_EXT_LM_TBD`,
`NFC_CSI_TBD`, `NFC_CSO_TBD`, `NFC_XIN_TBD`, `NFC_XOUT_TBD`,
`NFC_MCU_CLK_TBD`. The NFC loop, matching network and crystal were never
designed; the `RF_DEFERRED_NFC` netclass makes routing them a DRC error.

`Net-(U13-FB)` and `Net-(U13-SW)` have no ratsnest because every node on them is
DNP — they are entirely dead on DM.

### The two permanent I2S residuals

`I2S_BCLK` and `I2S_LRCLK` each report two islands: the fitted circuit, and one
isolated `U5` amplifier pad. **That is the correct DM state and it does not
change.** `I2S_MIC_DIN` is one island with zero ratsnest.

### The microphone is unaffected

`MK1` (ICS-43434) and `C8` are fitted and all three microphone I2S nets are
routed. Nothing in bucket A touches the demo audio-in path.

---

## B — GND finalisation: 130 lines

One net. The `In1 GND REFERENCE` plane is drawn and filled, and both radios, the
microphone, the USB-C connector, the MCU and the pull-to-ground parts are
stitched, but most remaining SMD ground pads still need a stitch via and a short
stub. This is board-wide work inherited from the Beta, not a DM cut, and it is
the single largest remaining job. 61 GND vias are placed.

Concentrations, measured: `J1` 31, `J2` 7, `U5` 7 (DNP — skippable), `U2` 6,
`U4` 4, `U9` 4 (DNP), `C56` 4, `U3` 3, `U15` 3, `J3` 1, `U10` 1.
`U7`, `U8` and `MK1` are **fully stitched — 0 GND lines each**.

**Pours are HELD** by CTO direction until every fitted must-work non-GND line is
closed, so this bucket does not move in this pass.

---

## C — fitted must-work, still open: 31 lines

| group | lines | status |
|---|---|---|
| J5 header interconnect — `XGPIO0`…`XGPIO13` (`U3` ↔ series resistor) | 14 | **congestion-sealed**; `U3` pads reach 186–1 330-cell pockets, the `R5x` pads reach separate ones, no pair shares a free region |
| `ACC_3V3_SW` | 3 | congestion-sealed; one join closed at the P3V3 0.40 mm floor |
| `ACC_PWR_EN` | 3 | congestion-sealed, 4 disjoint pockets |
| `I2C_SCL_EXT_HDR`, `I2C_SDA_EXT_HDR`, `XGPIO13_HDR` | 3 | header-side links, congestion-sealed |
| `Net-(U15-QOD)`, `Net-(U16-SCLB)`, `Net-(U16-SDAB)` | 3 | congestion-sealed inside the header cluster |
| `BQ25185_STAT1` / `STAT2`, `TEST_GPIO45` / `46` | 4 | status and test points; `U11.9` reaches **zero** free cells |
| `Net-(SW9-A)` `TP13.1` | 1 | 1 016-cell pocket; the switch function itself is now routed |
| ~~`BOOT_N`~~ | ~~3~~ | **CLOSED** — Option W landed, 52.445 mm, one island |
| ~~`XGPIO6_HDR`~~ | ~~1~~ | **CLOSED** — 1.613 mm |

**Nothing in bucket C is unexplained**, and nothing in it is blocked by a rule
or by a lock. Every one of the 31 is blocked by local congestion: each endpoint
was flooded over the whole board on all three routing layers with via
transitions honoured, and no pair shares a free region. Closing them needs a
dedicated header-and-power release programme, not opportunistic routing.

**23 of the 31 are J5-active** — `XGPIO0`…`XGPIO13` (14), `ACC_3V3_SW` (3),
`ACC_PWR_EN` (3), `I2C_SCL_EXT_HDR`, `I2C_SDA_EXT_HDR` and `XGPIO13_HDR` (3).
The other 8 are `BQ25185_STAT1`/`STAT2`, `TEST_GPIO45`/`46`,
`Net-(U15-QOD)`, `Net-(U16-SCLB)`, `Net-(U16-SDAB)` and `Net-(SW9-A)` `TP13`.

`AMP_SD_MODE` is **no longer counted here**. Both of its lines are in bucket A:
one has a DNP `U5` pad, and the other is filed with the speaker block because
the function is deferred as a whole. See the note under bucket A.

---

## Audit rule

At any Beta-DM audit:

```
unconnected(measured)  ==  A(intentional deferral) + B(GND) + C(must-work open)
        216            ==       55                 + 130    +      31
```

If the measured count exceeds the sum, something broke. If a line appears that
is in none of the three buckets, it is a defect and must be explained before the
board moves forward.
