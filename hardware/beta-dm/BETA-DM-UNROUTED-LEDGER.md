# AQROOT Beta DM — intentional-unrouted ledger

> ## SUPERSEDED — REBUILT UNDER LEAN-CORE SCOPE
>
> The `216 = A55 + B130 + C16 + D15` equation below was measured before the
> Lean-Core ruling deferred external I2C and the switched accessory rail and
> made `U15` and `U16` DNP. The authoritative ledger is now
> [BETA-DM-LEAN-CORE-LEDGER.md](BETA-DM-LEAN-CORE-LEDGER.md), rebuilt from the
> real board after those population changes. This file is retained as the
> pre-Lean-Core measurement.

Every ratsnest line on the Beta-DM board is accounted for here. The point of
this file is that **nothing is unexplained**: at any DM audit the remaining
unconnected count must equal the sum of the buckets below, and any line that
falls into none of them is a defect, not a deferral.

Measured on the board at head `6adf065`, re-derived line by line from the
KiCad DRC report rather than carried forward. **Total unconnected: 216.**

The Lean-DM scope ruling splits what used to be bucket C. The lines did not
move on the board — the classification changed. See
[BETA-DM-LEAN-SCOPE.md](BETA-DM-LEAN-SCOPE.md).

| bucket | ratsnest lines | what it is |
|---|---|---|
| A — intentional DM deferral (**DNP function**) | **55** | at least one endpoint is a pad of a DNP part, or the whole net belongs to a deferred block |
| B — GND, pours pending | **130** | one net; the plane and stitching program |
| C — **Lean-DM must-work, still open** | **16** | the Lean demo fails without these |
| D — **Lean-DM scope deferral (fitted-to-fitted)** | **15** | both ends fitted, deliberately not routed for the Demo Model; Full Beta restores every one |
| **total** | **216** | |

```
unconnected(measured)  ==  A + B + C + D
        216            ==  55 + 130 + 16 + 15
```

If the top-level three-bucket form is preferred, D folds into A and the
equation is `216 = A70 + B130 + C16`. The four-bucket form is kept as
authoritative because A and D fail for different reasons — A because a part is
not populated, D because a fitted circuit was descoped — and merging them
hides the distinction the restoration ledger depends on.

History: 281 after the I2S landed → 264 after `FAST_IO`, the USB-C CC pair, the
shield and the critical power controls → 239 after GND stitching at both radios
and the microphone → 230 after stitching the USB-C connector, the MCU and the
pull-to-ground parts → 225 after the display backlight closed its five lines →
223 after `XGPIO2_HDR` and `XGPIO3_HDR` → 220 after Option W landed `BOOT_N` →
**216** after the active-J5 sweep. The Lean-DM reclassification does **not**
change 216; it moves 15 lines from C to the new bucket D.

---

## A — intentional DM deferral, DNP function: 55 lines

Unrouted **because the function is DNP on the Demo Model**. Not defects, and
they must not be "fixed" by routing them. Every one restores for Final.

Assignment rule, applied line by line: bucket A if **a pad at either end
belongs to a DNP part**, or if **the net belongs to a block that is DNP as a
whole** (NFC front end, IR, speaker).

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
deferred as a whole. `NFC_5V_PA_PENDING` likewise includes one track-to-track
line with no pad at either end, inside a block that is DNP throughout.

Also permanently unrouted by DRU rule and carrying **no** ratsnest because they
are single-node nets: `NFC_RFO1_TBD`, `NFC_RFO2_TBD`, `NFC_RFI1_TBD`,
`NFC_RFI2_TBD`, `NFC_AAT_A_TBD`, `NFC_AAT_B_TBD`, `NFC_EXT_LM_TBD`,
`NFC_CSI_TBD`, `NFC_CSO_TBD`, `NFC_XIN_TBD`, `NFC_XOUT_TBD`,
`NFC_MCU_CLK_TBD`. `Net-(U13-FB)` and `Net-(U13-SW)` have no ratsnest because
every node on them is DNP.

### The two permanent I2S residuals

`I2S_BCLK` and `I2S_LRCLK` each report two islands: the fitted circuit, and one
isolated `U5` amplifier pad. **That is the correct DM state and it does not
change.** `I2S_MIC_DIN` is one island with zero ratsnest. The microphone path
is complete.

---

## B — GND finalisation: 130 lines

One net. The `In1 GND REFERENCE` plane is drawn and filled and both radios, the
microphone, the USB-C connector, the MCU and the pull-to-ground parts are
stitched, but most remaining SMD ground pads still need a stitch via and a short
stub. Board-wide work inherited from the Beta, not a DM cut. 61 GND vias placed.

Concentrations, measured: `J1` 31, `J2` 7, `U5` 7 (DNP — skippable), `U2` 6,
`U4` 4, `U9` 4 (DNP), `C56` 4, `U3` 3, `U15` 3, `J3` 1, `U10` 1.
`U7`, `U8` and `MK1` are **fully stitched — 0 GND lines each**.

**Pours are HELD** by CTO direction until every Lean-DM must-work non-GND line
is closed, so this bucket does not move in this pass.

---

## C — Lean-DM must-work, still open: 16 lines

| group | lines | endpoints | status |
|---|---|---:|---|
| the four selected XGPIO | 4 | `U3.8`↔`R55.1`, `U3.9`↔`R56.1`, `U3.10`↔`R57.2`, `U3.11`↔`R58.2` | scratch-proven route architecture, see [BETA-DM-LEAN-ROUTING.md](BETA-DM-LEAN-ROUTING.md) |
| external I2C header links | 2 | `R47.2`↔track, `R48.2`↔track | `I2C_SCL_EXT_HDR`, `I2C_SDA_EXT_HDR` |
| `U16` buffer B side | 2 | `R47.1`↔`U16.7`, `R48.1`↔`U16.6` | `Net-(U16-SCLB)`, `Net-(U16-SDAB)` |
| `/ACC_PWR_EN` | 3 | `U3.20`↔`U16.5`, `U16.5`↔`U15.3`, `U15.3`↔`R17.1` | **must-work by dependency**: `U16.5` is the buffer EN |
| `ACC_3V3_SW` | 3 | track↔`C38.1`, `R46.2`↔`U15.6`, `R46.2`↔track | **must-work by dependency**: `U16.8` is VCCB |
| `BQ25185_STAT1` / `STAT2` | 2 | `TP6.1`↔`U11.9`, `TP7.1`↔`U11.3` | ruling §11; both closable, see routing study |
| **total C** | **16** | | |

The ruling projected **C10**. The re-derivation returns **C16**. The
difference is exactly the six `ACC_PWR_EN` + `ACC_3V3_SW` lines that §7 asked
to defer, and the reason is the dependency finding in
[BETA-DM-LEAN-SCOPE.md](BETA-DM-LEAN-SCOPE.md) §1: those two nets carry the
`U16` enable and the `U16` VCCB supply, so external I2C — which §5 and §12 rank
MUST-WORK — cannot function without them. Every other reclassification in §13
of the ruling is confirmed exactly as projected.

---

## D — Lean-DM scope deferral, fitted-to-fitted: 15 lines

Both ends fitted. Deliberately unrouted for the Demo Model under the Lean
ruling. **Not defects, not DNP, and not abandoned** — every line has a
restoration entry in [BETA-DM-LEAN-RESTORATION.md](BETA-DM-LEAN-RESTORATION.md).

| group | lines | net(s) | authority |
|---|---:|---|---|
| ten deferred XGPIO | 10 | `XGPIO0`, `1`, `2`, `3`, `8`, `9`, `10`, `11`, `12`, `13` (`U3` ↔ series resistor) | ruling §6 |
| deferred header link | 1 | `XGPIO13_HDR` (`R64.2` ↔ J5-side track) | ruling §6 |
| accessory QOD | 1 | `Net-(U15-QOD)` (`R46.1` ↔ `U15.5`) | ruling §7/§8, audited safe |
| MCU test points | 2 | `TEST_GPIO45` (`TP1.1`↔`U1.26`), `TEST_GPIO46` (`TP2.1`↔`U1.16`) | ruling §9 |
| SW9 diagnostic branch | 1 | `Net-(SW9-A)` → `TP13.1` | ruling §10 |
| **total D** | **15** | | |

Nothing in D was made DNP to achieve the count. Every series resistor,
test point and header pin involved stays **fitted and in place**.

`XGPIO9_HDR` deserves a note: it is currently **routed**, so it contributes no
line here, but the Lean routing plan releases 6 of its objects to open the
corridor and does not re-land them. When that plan lands, `XGPIO9_HDR` gains
one ratsnest line and bucket D becomes 16 with a board total of 217. That is a
deliberate, documented cost of the release, not a regression.

---

## Audit rule

At any Beta-DM audit:

```
unconnected(measured)  ==  A(DNP deferral) + B(GND) + C(Lean must-work) + D(Lean deferral)
        216            ==       55         + 130    +        16         +      15
```

If the measured count exceeds the sum, something broke. If a line appears that
is in none of the four buckets, it is a defect and must be explained before the
board moves forward.

---

## Current state after the final copper closeout (2026-08-20)

The audit rule above is stated against the 216-line board it was written for.
The equation still holds; only the numbers have moved. Measured on the landed
board after the GND closeout, the E6_R2_1 retirement and the outer GND pours:

```
unconnected(measured)  ==  A(DNP deferral) + B(GND) + C(Lean must-work) + D(Lean deferral)
        103            ==       64         +  18    +         0         +      21
```

with **B split** as the GND closeout requires:

| bucket | meaning | count |
|---|---|---:|
| A | DNP-function deferral | 64 |
| **B1** | **GND on a fitted part — must ground** | **0** |
| B2 | GND on DNP parts only — no copper owed | 18 |
| **C** | **Lean must-work, non-GND** | **0** |
| D | Lean fitted-but-deferred | 21 |

The trajectory across the recent passes:

| stage | total | GND | C |
|---|---:|---:|---:|
| before the Lean GPIO landing | 216 | 130 | 16 |
| after XGPIO5 + XGPIO6 landed | 215 | 130 | 0 |
| after the GND stitching pass | 137 | 52 | 0 |
| **after the outer GND pours** | **103** | **18** | **0** |

**Both must-be-zero buckets are now zero.** Every one of the 103 remaining
lines is an intentional deferral: 64 terminate on a DNP part, 18 are GND lines
whose only ungrounded endpoint is a DNP pad, and 21 are Lean-deferred functions
on fitted parts. Nothing is unexplained.

Full detail, including the solid-vs-thermal decision and the RF containment
measurements, is in
[`BETA-DM-GND-CLOSEOUT.md`](BETA-DM-GND-CLOSEOUT.md) Part 2.
