# AQROOT Beta DM — Full-Beta restoration ledger for Lean-DM cuts

One entry per feature the **Lean** Demo Model ruling descoped. This file exists
so the Full-Beta routing programme stays explicit rather than getting forgotten
once the demo works.

Every row below is marked:

> **LEAN DM CUT ONLY — FULL BETA RESTORE**

Preservation invariants held across every row, verified this pass:

* **no footprint moved** — placement is byte-identical to `6adf065`
* **no board area reclaimed** — same outline, same mounting holes
* **no pin renumbered** — `J5` pins 1–26 and `U3` pins 4–20 keep their
  full-Beta assignments
* **no part DNP'd to reduce a ratsnest count** — every series resistor, test
  point and header pin below stays **fitted**
* **`hardware/beta/`** (full Beta, `beta-full-reference-v1`) — empty diff

This ledger covers the **Lean** cuts only. The earlier DNP-function cuts
(speaker, IR, NFC front end, NFC 5 V PA) keep their own restoration table in
[BETA-DM-SCOPE-LEDGER.md](BETA-DM-SCOPE-LEDGER.md) §5 and are unchanged.

---

## 1. The ten deferred XGPIO

| item | Lean-DM | Full Beta | what restoration costs |
|---|---|---|---|
| `XGPIO0` (`U3.4` ↔ `R51.1`) | LEAN DM NO ROUTE | **RESTORE / REQUIRED** | route 1 join. Minimum ordinary release measured at **21 objects / 87.476 mm** — endpoint pockets are 7 274 and 1 187 cells |
| `XGPIO1` (`U3.5` ↔ `R52.1`) | LEAN DM NO ROUTE | **RESTORE / REQUIRED** | 1 join, **22 objects / 87.476 mm** |
| `XGPIO2` (`U3.6` ↔ `R53.2`) | LEAN DM NO ROUTE | **RESTORE / REQUIRED** | 1 join, **19 objects / 84.258 mm** |
| `XGPIO3` (`U3.7` ↔ `R54.2`) | LEAN DM NO ROUTE | **RESTORE / REQUIRED** | 1 join, **24 objects / 85.587 mm** |
| `XGPIO8` (`U3.13` ↔ `R59.1`) | LEAN DM NO ROUTE | **RESTORE / REQUIRED** | 1 join, **11 objects / 10.918 mm** — the cheapest of the ten, and the named alternate to `XGPIO4` |
| `XGPIO9` (`U3.14` ↔ `R60.1`) | LEAN DM NO ROUTE | **RESTORE / REQUIRED** | 1 join. **Needs the `SX1262_RXEN` release** — no ordinary release of any size opens `U3.14` |
| `XGPIO10` (`U3.15` ↔ `R61.2`) | LEAN DM NO ROUTE | **RESTORE / REQUIRED** | as `XGPIO9` |
| `XGPIO11` (`U3.16` ↔ `R62.2`) | LEAN DM NO ROUTE | **RESTORE / REQUIRED** | as `XGPIO9` |
| `XGPIO12` (`U3.17` ↔ `R63.1`) | LEAN DM NO ROUTE | **RESTORE / REQUIRED** | as `XGPIO9` |
| `XGPIO13` (`U3.18` ↔ `R64.1`) | LEAN DM NO ROUTE | **RESTORE / REQUIRED** | as `XGPIO9`, **plus** the `XGPIO13_HDR` join below |

Nothing is removed: `R51`–`R64` all stay **fitted**, all fourteen `J5` header
pins keep their nets, and all fourteen `U3` port assignments are unchanged.

**Full-Beta XGPIO preserved: 14 / 14.**

### The shared prerequisite the Full-Beta programme inherits

Five of the ten (`XGPIO9`–`XGPIO13`) plus `ACC_PWR_EN` are sealed by the same
object: the 4.825 mm `SX1262_RXEN` B.Cu run at y = 10.600 that passes beneath
the `U3` bottom pad row. Measured at the maximal-ordinary-release ceiling,
`U3.14`–`U3.18` sit in **198-cell** pockets walled only by `PAD U3` (66 cells)
and `SX1262_RXEN` (6 cells).

**The Lean-Core plan does NOT pay this cost.** `ACC_PWR_EN` is deferred, and
the GPIO study measured that releasing `SX1262_RXEN` buys nothing for
`XGPIO4`–`XGPIO7`, so it was never spent. `SX1262_RXEN` is **unchanged on the
board**, and `XGPIO9`–`XGPIO13` still face a hard-lock ruling for Full Beta.

That is a real cost the Lean Demo Model leaves on the table, and it is worth
keeping visible: the earlier expectation that Lean would pre-pay it no longer
holds.

---

## 2. Header-side and accessory items

| item | Lean-DM | Full Beta | what restoration costs |
|---|---|---|---|
| `XGPIO13_HDR` (`R64.2` ↔ J5-side track) | LEAN DM NO ROUTE | **RESTORE / REQUIRED** | 1 join, header-side, congestion-sealed. Restore together with `XGPIO13` |
| `Net-(U15-QOD)` (`R46.1` ↔ `U15.5`) | LEAN DM NO ROUTE; `U15` now **DNP** | **RESTORE WITH U15** | clear `dnp` on `U15`, then 1 join inside the header cluster. `R46` 100 k stays **fitted** |
| `ACC_PWR_EN` | LEAN DM NO ROUTE; `U15`/`U16` **DNP** | **RESTORE WITH U15 + U16** | clear `dnp`, then 3 joins: `U3.20` ↔ `U16.5` ↔ `U15.3` ↔ `R17.1`. `R17` 100 k stays **fitted** |
| `ACC_3V3_SW` | LEAN DM NO ROUTE; partial copper on the board, and **the rest may be spent** by the GPIO routing | **RESTORE WITH U15** | clear `dnp`, re-route whatever the GPIO pass spent, then close the rail to `U16.8`, `C38`, `C42`, `TP12`, `J5.19` |
| external I2C — `I2C_SCL_EXT_HDR`, `I2C_SDA_EXT_HDR`, `Net-(U16-SCLB)`, `Net-(U16-SDAB)` | LEAN DM NO ROUTE; `U16` **DNP**; copper **may be spent** | **RESTORE WITH U16** | clear `dnp`, re-route whatever was spent, then close the four joins. `R47`/`R48` 22 R stay **fitted** |
| `U15` TPS22918 | **DNP** | **RESTORE / REQUIRED** | population only — the footprint, pads and placement are untouched |
| `U16` TCA9517A | **DNP** | **RESTORE / REQUIRED** | population only — the footprint, pads and placement are untouched |
| `R49`, `R50` external-bus pull-ups | DNP — **pre-existing full Beta DNP**, not a DM decision | unchanged full-Beta matter | population only, if ever wanted |

`U15` and `U16` are **DNP** on the Lean Demo Model. The earlier "keep `U15`
fitted" verdict is **withdrawn** — see
[BETA-DM-LEAN-CORE-SCOPE.md](BETA-DM-LEAN-CORE-SCOPE.md) §4 for the audit that
authorised both, run against KiCad's own connectivity engine.

Support passives deliberately left **fitted** so restoration is population-only:
`R17`, `C38`, `C39`, `C42`, `R46`, `R47`, `R48`.

---

## 2a. BQ25185 status outputs — LEAN-CORE CLOSEOUT

| item | Lean-DM | Full Beta | what restoration costs |
|---|---|---|---|
| `BQ25185_STAT1` (`TP6.1` ↔ `U11.9`) | **LEAN DM INTENTIONAL NO ROUTE** | **RESTORE IF STILL WANTED** | routes at **28.846 mm / 68 seg / 2 via** on a 7-object / 8.500 mm release (in-window `ISET` + the `U11.2` pad escape). This was **fully verified** — released nets re-landed, KiCad DRC 0 errors, DFM pass — before the ruling deferred it. The candidate is on record and can be replayed |
| `BQ25185_STAT2` (`TP7.1` ↔ `U11.3`) | **LEAN DM INTENTIONAL NO ROUTE** | **RESTORE IF STILL WANTED** | needs a dedicated `U11` left-column pad-escape pass: `BQ25185_SYS`, `BAT_PROTECTED_P` and `STAT2` planned together as three parallel 0.20 mm lanes at y = 66.200 / 66.600 / 67.000, with the 0.80 mm BAT transition via placed clear of all three |

Both are BQ25185 **open-drain status outputs exposed only as diagnostic test
points**. They are not charger-control inputs, not safety dependencies, not MCU
inputs, and not required for USB, boot/programming or any Demo-Model UI
function. **The BQ25185 charger operates without these traces.**

`TP6` and `TP7` remain fitted and in place. Neither was moved, and neither was
DNP'd for bookkeeping. The `U11` power rail — `ISET`, `BAT_PROTECTED_P`,
`BQ25185_SYS`, `BAT_MAIN` — was **not touched** to reach them.

**LEAN DM CUT ONLY — FULL BETA RESTORE.**

## 3. Test and diagnostic points

| item | Lean-DM | Full Beta | what restoration costs |
|---|---|---|---|
| `TEST_GPIO45` (`TP1.1` ↔ `U1.26`) | **LEAN DM INTENTIONAL NO ROUTE** | **RESTORE IF STILL WANTED** | `DISP_BL_CTL` alone is not enough; the wall also includes `I2S_MIC_DIN`, `SD_CS_N` and `BTN_HOME_N`, all preserve-list. Needs its own architecture pass or a preserve-list ruling. `TP1` stays fitted and in place |
| `TEST_GPIO46` (`TP2.1` ↔ `U1.16`) | **LEAN DM INTENTIONAL NO ROUTE** | **RESTORE IF STILL WANTED** | closes with **no release at all** at 130.826 mm / 296 segments. The reason it is cut is length and corridor consumption, not feasibility. `TP2` stays fitted and in place |
| `Net-(SW9-A)` → `TP13` | **LEAN DM INTENTIONAL NO ROUTE** | **RESTORE IF STILL WANTED** | reachable only by releasing 63 objects of `BTN_A_N` / `BTN_B_N` / `BTN_DOWN_N` / `+3V3`; the button nets are preserve-list. The **functional** SW9 path is already routed — only the diagnostic branch is open. `TP13` stays fitted and in place |

These three are routing-scope decisions, not DNP decisions. No test point was
removed or moved. Alternative bring-up access already exists: `TP6`, `TP7`,
`TP12`, `TP15`, the RootProbe header, USB, `BOOT_N`, and the module
castellations at `U1.16` / `U1.26`.

---

## 4. What the Lean pass does NOT defer

Stated so the Full-Beta programme does not inherit phantom work:

* **Both radios.** `SX1262` and `CC1101` signal sides are complete, 0 rats.
* **The microphone.** All three I2S nets routed; `I2S_MIC_DIN` one island.
* **`BOOT_N`.** Landed by Option W, 52.445 mm, one island.
* **The backlight.** Whole string one island, 0 rats.
* **The buttons, display, touch, microSD, USB.** Complete on the signal side.
* **`FAST_IO_GPIO43_HDR`.** Routed and **untouched** by the Lean release.
* **`WAKE_ATTN_N_HDR`.** Routed; the Lean plan releases 6 objects and
  **re-lands** it as a simultaneous commodity. It stays ACTIVE — this is not a
  cut and needs no restoration entry.
* **`J5` population and all 19 header escapes.** Unchanged.
* **`U10` USBLC6-2SC6.** Fitted, unchanged.
* **`D2`–`D7`.** DNP as previously ruled — bucket A, not a Lean cut.

---

## 5. Restoration summary

| Lean-DM cut | ratsnest lines | Full-Beta disposition |
|---|---:|---|
| ten deferred `XGPIO` | 10 | RESTORE / REQUIRED |
| `XGPIO13_HDR` | 1 | RESTORE / REQUIRED |
| `Net-(U15-QOD)` | 1 | RESTORE / REQUIRED |
| `TEST_GPIO45` | 1 | RESTORE IF STILL WANTED |
| `TEST_GPIO46` | 1 | RESTORE IF STILL WANTED |
| `Net-(SW9-A)` → `TP13` | 1 | RESTORE IF STILL WANTED |
| `BQ25185_STAT1` | 1 | RESTORE IF STILL WANTED — verified candidate on record |
| `BQ25185_STAT2` | 1 | RESTORE IF STILL WANTED — needs a `U11` left-column pass |
| **bucket D total** | **20** | |
| `XGPIO9_HDR` | 0 today, **1 after the Lean routing lands** | RESTORE / REQUIRED |
| `ACC_PWR_EN` feature | 0 — copper routed | firmware only |
| `ACC_3V3_SW` feature | 0 — copper routed | firmware only |

**LEAN DM CUT ONLY — FULL BETA RESTORE** applies to every row above.
