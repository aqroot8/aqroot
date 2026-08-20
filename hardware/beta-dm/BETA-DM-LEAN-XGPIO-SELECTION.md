# AQROOT Beta DM — Lean-DM XGPIO selection

> ## RANKING RETAINED — INTERACTION SECTION SUPERSEDED
>
> The candidate ranking in §1–§3 was measured against the board alone and is
> **still authoritative**; it is re-validated under Lean-Core scope rather than
> re-derived. §4's interaction analysis assumed external I2C, `U16` and the
> switched accessory rail were simultaneous demands. All six of those nets are
> now Lean-DM deferred, so §4 **overstates** the contention the selected four
> face. It is retained as evidence of the harder case.

Which four of the fourteen expansion GPIOs Beta-DM keeps functional, chosen by
**measured routability on the current board**, not by pin order or convenience.

Method, per candidate: both fitted endpoints (`U3` pad and series-resistor pad)
are flooded over the whole header window on all three routing layers with via
transitions honoured; if they do not share a free region the one-cell boundary
ring of each pocket is attributed to the copper that owns it, so the wall is
named rather than reported as "no path". Then the minimum ordinary release is
found by greedy shrink from the maximal-release ceiling.

Window `(8.0, 2.0) – (62.0, 30.0)`, grid 0.05 mm, 1081 × 561 cells.

---

## 1. Full candidate ranking, XGPIO0 … XGPIO12

`XGPIO13` is excluded up front by ruling §3 — `XGPIO13_HDR` carries an
additional unresolved header-side join — and it is also disqualified by the
same wall as `XGPIO9`–`XGPIO12`, below.

| rank | net | U3 pad | U3 pocket | resistor pad | R pocket | minimum ordinary release | verdict |
|---:|---|---|---:|---|---:|---|---|
| **1** | `XGPIO4` | `U3.8` | 278 059 | `R55.1` | 6 026 | **11 obj / 10.918 mm** | **SELECTED** |
| **1** | `XGPIO5` | `U3.9` | 278 059 | `R56.1` | 235 620 | **11 obj / 10.918 mm** | **SELECTED** |
| **1** | `XGPIO6` | `U3.10` | 278 059 | `R57.2` | 5 956 | **11 obj / 10.918 mm** | **SELECTED** |
| **1** | `XGPIO7` | `U3.11` | 278 059 | `R58.2` | 235 772 | **11 obj / 10.918 mm** | **SELECTED** |
| **5** | `XGPIO8` | `U3.13` | 265 040 | `R59.1` | 6 535 | 11 obj / 10.918 mm | viable alternate |
| 6 | `XGPIO2` | `U3.6` | 7 274 | `R53.2` | 1 616 | 19 obj / 84.258 mm | rejected — 7.7× the release |
| 7 | `XGPIO3` | `U3.7` | 7 274 | `R54.2` | 547 | 24 obj / 85.587 mm | rejected |
| 8 | `XGPIO0` | `U3.4` | 7 274 | `R51.1` | 1 187 | 21 obj / 87.476 mm | rejected |
| 9 | `XGPIO1` | `U3.5` | 7 274 | `R52.1` | 1 113 | 22 obj / 87.476 mm | rejected |
| — | `XGPIO9` | `U3.14` | **198** | `R60.1` | 6 235 | **none exists** | **DISQUALIFIED** |
| — | `XGPIO10` | `U3.15` | **198** | `R61.2` | 6 297 | **none exists** | **DISQUALIFIED** |
| — | `XGPIO11` | `U3.16` | **198** | `R62.2` | 6 227 | **none exists** | **DISQUALIFIED** |
| — | `XGPIO12` | `U3.17` | **198** | `R63.1` | 6 281 | **none exists** | **DISQUALIFIED** |
| — | `XGPIO13` | `U3.18` | **198** | `R64.1` | — | **none exists** | excluded by §3 **and** disqualified |

Pocket figures are free cells at 0.05 mm, i.e. 0.0025 mm² each. A 198-cell
pocket is 0.5 mm² — a pad and nothing else.

## 2. Why XGPIO9 … XGPIO13 are disqualified, not merely expensive

Every ordinary track and via inside the header window was released at once —
492 objects over 29 nets, with the hard locks held out — and the U3 bottom-row
pins were re-flooded. `U3.14`–`U3.18` stayed at **198 cells**. The wall that
remains at that ceiling is:

```
PAD U3           66 cells   (the package's own pads)
SX1262_RXEN       6 cells   HARD LOCK
```

`SX1262_RXEN` leaves `U3.19` southward and then runs **west along y = 10.600
directly beneath the bottom pad row** before turning north and back east
through the U3 inter-row channel. That single 4.825 mm B.Cu run is what seals
`XGPIO9` through `XGPIO13`.

So these five are not "expensive" — **no ordinary release of any size opens
them.** They are reachable only across a hard lock, which is exactly what
ruling §16 declines to spend by default. They are the correct ten to defer.

Confirmed by the converse test: releasing `f4200001` alone lifts `U3.14`–`U3.18`
from 198 cells to 177 164.

## 3. Why the top four are a genuine tie, and how it was broken

`XGPIO4`, `5`, `6`, `7` and `8` all take the **same** 11-object, 10.918 mm
minimum release — the wall in front of all five is one shared structure, so
paying for it once pays for all of them. That leaves five candidates for four
slots, decided on ruling §17's lower-priority criteria:

| criterion | XGPIO4-7 | XGPIO5-8 |
|---|---|---|
| U3-side coherence | `U3.8`–`U3.11`, four **contiguous** top-row pins | splits across both pad rows (`U3.9`–`U3.11` + `U3.13`) |
| header-side coherence | `J5.8`, `9`, `10`, `11` — four contiguous pins | `J5.9`, `10`, `11`, `12` — also contiguous |
| congestion interaction | one fan-out from one pad row | two fan-outs from opposite rows, both crossing the inter-row channel |

`XGPIO4`–`XGPIO7` wins on U3-side coherence and on congestion interaction: all
four escape from one contiguous run of pads on one row, so their fan-out is a
single ordered bundle rather than two bundles converging in the channel that
`ACC_PWR_EN` and the `SX1262_RXEN` re-land also need.

**`XGPIO8` is the named alternate.** If a later pass finds `XGPIO4` awkward,
`XGPIO8` substitutes at identical release cost.

## 4. Interaction with the rest of the Lean must-work set

Checked as part of the joint minimum-release derivation, with all ten Lean
header demands present simultaneously:

| interaction | result |
|---|---|
| with external I2C (`I2C_SCL/SDA_EXT_HDR`) | no additional release; both reach on the same 15-object set |
| with `U16` (`Net-(U16-SCLB)`, `Net-(U16-SDAB)`) | no additional release |
| with `BQ25185_STAT1` / `STAT2` | none — different region of the board, disjoint release |
| with `SX1262_RXEN` | the selected four do **not** need the RXEN release; `ACC_PWR_EN` does. RXEN is carried as a simultaneous commodity so the J5 routes cannot eat the corridor it needs to get home |

The decisive difference from the phase-2 full-header study is the size of the
demand on the U3 inter-row channel. That study put 14 `XGPIO` plus
`ACC_PWR_EN`, `ACC_3V3_SW` and `RXEN` — 17 demands — through a corridor
measured at 18 lanes, and the negotiation could not find a separation. The Lean
problem puts **`ACC_PWR_EN` and the `RXEN` re-land** through it. The selected
four escape from the *other* pad row and never enter it.
