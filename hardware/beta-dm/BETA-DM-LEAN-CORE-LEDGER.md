# AQROOT Beta DM — LEAN-CORE unconnected ledger

Rebuilt line by line from the **current real board** after the `U15` / `U16`
population change, from the KiCad DRC report rather than carried forward.
Supersedes [BETA-DM-UNROUTED-LEDGER.md](BETA-DM-UNROUTED-LEDGER.md).

Board state: head `27bf8f9` + the `U15`/`U16` DNP change.
**DRC: 0 errors, 240 warnings, 216 unconnected, schematic parity 0.**

Marking a part DNP does **not** change the ratsnest — KiCad keeps DNP pads in
connectivity — so the total is unchanged at 216. What changed is the
classification of 7 lines that now have a DNP pad at one end.

```
unconnected(measured)  ==  A + B + C + D
        216            ==  62 + 130 + 6 + 18
```

| bucket | lines | what it is |
|---|---:|---|
| A — DNP-function / component deferral | **62** | a pad at either end belongs to a DNP part, or the whole net belongs to a block that is DNP as a whole |
| B — GND, pours pending | **130** | one net; the plane and stitching programme |
| C — **Lean-Core MUST-WORK non-GND** | **6** | the Lean-Core demo fails without these |
| D — Lean-DM fitted, intentionally unrouted | **18** | both ends fitted, deliberately unrouted; every one has a restoration entry |

**C = 6, re-derived, not assumed.** It matches the ruling's projection exactly.

---

## C — Lean-Core MUST-WORK non-GND: 6 lines

| net | endpoints |
|---|---|
| `/XGPIO4` | `U3.8` ↔ `R55.1` |
| `/XGPIO5` | `U3.9` ↔ `R56.1` |
| `/XGPIO6` | `U3.10` ↔ `R57.2` |
| `/XGPIO7` | `U3.11` ↔ `R58.2` |
| `/01_POWER_TREE/BQ25185_STAT1` | `TP6.1` ↔ `U11.9` |
| `/01_POWER_TREE/BQ25185_STAT2` | `TP7.1` ↔ `U11.3` |

Nothing else fitted remains open outside D. `FAST_IO_GPIO43_HDR`,
`WAKE_ATTN_N_HDR` and `+3V3` at `J5.1` are already routed and carry no
must-work line; their only open lines go to the DNP `D6`/`D7` ESD arrays and
are bucket A.

## D — Lean-DM fitted, intentionally unrouted: 18 lines

| group | lines | net(s) |
|---|---:|---|
| ten deferred XGPIO | 10 | `XGPIO0`, `1`, `2`, `3`, `8`, `9`, `10`, `11`, `12`, `13` (`U3` ↔ series resistor) |
| deferred header link | 1 | `XGPIO13_HDR` |
| external-I2C header links | 2 | `I2C_SCL_EXT_HDR`, `I2C_SDA_EXT_HDR` — fitted `R47`/`R48` to fitted J5-side track |
| accessory rail, fitted-to-fitted part | 2 | `ACC_3V3_SW`: track ↔ `C38.1`, and `R46.2` ↔ track |
| MCU test points | 2 | `TEST_GPIO45`, `TEST_GPIO46` |
| SW9 diagnostic branch | 1 | `Net-(SW9-A)` → `TP13.1` |
| **total D** | **18** | |

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

A went 55 → 62. D went 15 → 18 (gained the two ext-I2C header links and the two
fitted-to-fitted `ACC_3V3_SW` lines, lost `Net-(U15-QOD)` to A). C went 16 → 6.
`62 + 130 + 6 + 18 = 216`.

**No line was reclassified to manufacture the C6 count.** C6 is what remains
after the ruling's scope is applied to the measured board: the six lines listed
above are exactly the ones the Lean-Core demo cannot work without.

---

## Projected effect of landing the Lean-Core routing

The scratch architecture releases copper that must re-land, and one release
leaves a net short. Projected board totals **after** a future landing:

| change | effect |
|---|---|
| `BQ25185_STAT1` closes | −1 |
| `BQ25185_STAT2` closes | −1 |
| `XGPIO4`, `5`, `6`, `7` close | −4 |
| `ISET`, `BAT_PROTECTED_P`, `WAKE_ATTN_N_HDR`, `FAST_IO_U0TXD_ROOTPROBE_CS` re-land | 0 |
| **projected total** | **210 = A62 + B130 + C0 + D18** |

That is the target, not a measurement. Nothing has landed.

## Audit rule

At any Beta-DM audit the measured unconnected count must equal A + B + C + D.
If a line appears that is in none of the four buckets, it is a defect and must
be explained before the board moves forward.
