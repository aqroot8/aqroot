# AQROOT Beta DM — LEAN-CORE unconnected ledger

Rebuilt line by line from the **current real board** after the `U15` / `U16`
population change, from the KiCad DRC report rather than carried forward.
Supersedes [BETA-DM-UNROUTED-LEDGER.md](BETA-DM-UNROUTED-LEDGER.md).

Board state: head `27bf8f9` + the `U15`/`U16` DNP change.
**DRC: 0 errors, 240 warnings, 216 unconnected, schematic parity 0.**

Marking a part DNP does **not** change the ratsnest — KiCad keeps DNP pads in
connectivity — so the total is unchanged at 216. What changed is the
classification of 7 lines that now have a DNP pad at one end.

> **UPDATED by the final GPIO closeout ruling.** `BQ25185_STAT1` and
> `BQ25185_STAT2` are now **LEAN-DM INTENTIONAL NO ROUTE** and move from C to
> D. Re-measured on the real board:

```
unconnected(measured)  ==  A + B + C + D
        216            ==  62 + 130 + 4 + 20
```

C is now **4**: `XGPIO4`, `XGPIO5`, `XGPIO6`, `XGPIO7`. Nothing else fitted
remains must-work outside D. The previous equation, `216 = A62 + B130 + C6 +
D18`, is kept below for the record; only the two STAT lines moved, and no
copper changed.

| bucket | lines | what it is |
|---|---:|---|
| A — DNP-function / component deferral | **62** | a pad at either end belongs to a DNP part, or the whole net belongs to a block that is DNP as a whole |
| B — GND, pours pending | **130** | one net; the plane and stitching programme |
| C — **Lean MUST-WORK non-GND** | **4** | the Lean demo fails without these |
| D — Lean-DM fitted, intentionally unrouted | **20** | both ends fitted, deliberately unrouted; every one has a restoration entry |

**C = 4, re-derived, not assumed.** It matches the ruling's projection exactly.

---

## C — Lean MUST-WORK non-GND: 4 lines

| net | endpoints |
|---|---|
| `/XGPIO4` | `U3.8` ↔ `R55.1` |
| `/XGPIO5` | `U3.9` ↔ `R56.1` |
| `/XGPIO6` | `U3.10` ↔ `R57.2` |
| `/XGPIO7` | `U3.11` ↔ `R58.2` |

Nothing else fitted remains open outside D. `FAST_IO_GPIO43_HDR`,
`WAKE_ATTN_N_HDR` and `+3V3` at `J5.1` are already routed and carry no
must-work line; their only open lines go to the DNP `D6`/`D7` ESD arrays and
are bucket A.

## D — Lean-DM fitted, intentionally unrouted: 20 lines

| group | lines | net(s) |
|---|---:|---|
| **BQ25185 status test points** | **2** | `BQ25185_STAT1` (`TP6.1`↔`U11.9`), `BQ25185_STAT2` (`TP7.1`↔`U11.3`) — open-drain diagnostic outputs, not charger control, not safety, not MCU inputs, not boot/USB/UI. The charger operates without these traces |
| ten deferred XGPIO | 10 | `XGPIO0`, `1`, `2`, `3`, `8`, `9`, `10`, `11`, `12`, `13` (`U3` ↔ series resistor) |
| deferred header link | 1 | `XGPIO13_HDR` |
| external-I2C header links | 2 | `I2C_SCL_EXT_HDR`, `I2C_SDA_EXT_HDR` — fitted `R47`/`R48` to fitted J5-side track |
| accessory rail, fitted-to-fitted part | 2 | `ACC_3V3_SW`: track ↔ `C38.1`, and `R46.2` ↔ track |
| MCU test points | 2 | `TEST_GPIO45`, `TEST_GPIO46` |
| SW9 diagnostic branch | 1 | `Net-(SW9-A)` → `TP13.1` |
| **total D** | **20** | |

## A — 62 lines, composition

| owner | lines |
|---|---:|
| `U5` speaker amplifier | 6 |
| `U9` NFC front end | 5 |
| deferred blocks with no DNP pad at either end (NFC 5 V rail, IR, speaker) | 4 |
| `D5` | 4 |
| `D4` | 3 |
| **`U15`** | **3** |
| **`U16`** | **3** |
| `D7` | 2 |
| remaining `D2`, `D3`, `D6`, `U6`, `U13`, `R49`, `R50`, `R68`, NFC and IR parts | 32 |

### What moved into A this pass — 7 lines

`Net-(U16-SCLB)` (`U16.7`) · `Net-(U16-SDAB)` (`U16.6`) · `ACC_PWR_EN` ×3
(`U16.5`, `U15.3`) · `ACC_3V3_SW` `R46.2`↔`U15.6` (`U15.6`) ·
`Net-(U15-QOD)` `R46.1`↔`U15.5` (`U15.5`).

A went 55 → 62 with the `U15`/`U16` DNP. D went 15 → 18 there (gained the two
ext-I2C header links and the two fitted-to-fitted `ACC_3V3_SW` lines, lost
`Net-(U15-QOD)` to A), then **18 → 20** when the closeout ruling deferred
`BQ25185_STAT1` and `BQ25185_STAT2`. C went 16 → 6 → **4**.
`62 + 130 + 4 + 20 = 216`.

**No line was reclassified to manufacture the C4 count, and no copper was
touched to reach it.** C4 is what remains once the ruling's scope is applied to
the measured board: the four lines listed above are exactly the ones the Lean
demo cannot work without.

---

## Projected effect of landing the Lean GPIO routing

| change | effect |
|---|---|
| selected XGPIO close | −1 per pin |
| `WAKE_ATTN_N_HDR` re-lands | 0 |
| **Lean-deferred copper spent and NOT re-landed** | **+1 per net left short** — a deliberate, documented cost, see [BETA-DM-LEAN-GPIO-CLOSEOUT.md](BETA-DM-LEAN-GPIO-CLOSEOUT.md) |

The board total will therefore **rise**, not fall, when the GPIO routing lands:
bucket D grows by every deferred header route whose copper is spent. That is
intended — §8 of the closeout ruling forbids wasting routing capacity to
re-land a function the Demo Model has explicitly deferred. Every spent net gets
a Full-Beta restoration entry.

Those are targets, not measurements. **Nothing has landed.**

## Audit rule

At any Beta-DM audit the measured unconnected count must equal A + B + C + D.
If a line appears that is in none of the four buckets, it is a defect and must
be explained before the board moves forward.
