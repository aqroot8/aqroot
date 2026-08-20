# AQROOT Beta DM — LEAN-CORE final scope

Authoritative Beta-DM scope. Supersedes the expansion rulings in
[BETA-DM-LEAN-SCOPE.md](BETA-DM-LEAN-SCOPE.md), which is retained as study
evidence.

Created against Beta-DM head `27bf8f9`.

## 1. Lean-Core expansion requirement — the whole of it

| function | net(s) | status |
|---|---|---|
| four XGPIO | `/XGPIO4`, `/XGPIO5`, `/XGPIO6`, `/XGPIO7` | **MUST-WORK** |
| fast native signal | `FAST_IO_GPIO43_HDR` | **ACTIVE** — routed, and **untouched** by the Lean-Core release |
| wake / attention | `WAKE_ATTN_N_HDR` | **ACTIVE** — routed; one via released and re-landed, §5 |
| direct 3V3 header access | `+3V3` at `J5.1` | **ACTIVE** — routed, one island |
| GND header access | `J5.2` / `7` / `20` / `24` / `25` | bucket B, board-wide GND closeout |

Plus, outside the header: `BQ25185_STAT1` and `BQ25185_STAT2` remain MUST-WORK
charger bring-up signals.

XGPIO names are unchanged. There is no `DM_XGPIO` renumbering.

The four selected land on `J5.8`–`J5.11`, a contiguous run of four header pins
with GND on `J5.7` immediately adjacent:

```
   x =   44.620   42.080   39.540   37.000
 row A    J5.7     J5.9    J5.11    J5.13      GND, XGPIO5, XGPIO7, WAKE_ATTN_N
 row B    J5.8    J5.10    J5.12    J5.14      XGPIO4, XGPIO6, (deferred), (deferred)
```

That supports both intended accessory shapes — two outputs and two inputs with
a ground return next door, or low-speed sensor lines with WAKE/ATTN two columns
away and `FAST_IO` on `J5.23` where one faster signal is wanted. Accessory
boards are **not** designed in this pass.

## 2. External I2C — LEAN-DM DEFERRED

| net | Lean-DM | Full Beta |
|---|---|---|
| `I2C_SCL_EXT_HDR` | **NO ROUTE / DEFER** | RESTORE |
| `I2C_SDA_EXT_HDR` | **NO ROUTE / DEFER** | RESTORE |
| `Net-(U16-SCLB)` | **NO ROUTE / DEFER** | RESTORE |
| `Net-(U16-SDAB)` | **NO ROUTE / DEFER** | RESTORE |

**Internal I2C is a different thing and is unaffected.** `/I2C_SCL_INT` and
`/I2C_SDA_INT` remain MUST-WORK and hard-locked, each one island, with nine
other fitted nodes between them (`J1.44/45`, `U14.7/8`, `U3.22/23`, `U4.13/14`,
`U2.22/23`, `U1.38/39`, `TP4`, `TP5`, `R19`, `R20`). Verified below.

## 3. Switched accessory power — LEAN-DM DEFERRED

| net | Lean-DM | Full Beta |
|---|---|---|
| `/ACC_PWR_EN` | **NO ROUTE / DEFER** | RESTORE |
| `ACC_3V3_SW` | **NO ROUTE / DEFER** | RESTORE |
| `Net-(U15-QOD)` | **NO ROUTE / DEFER** | RESTORE |

Accessories take power from the **direct** `+3V3` at `J5.1`, which is routed
and live. **`J5.19` (`ACC_3V3_SW`) is an unpowered pin on Beta-DM** — that must
reach whoever designs a demo accessory.

## 4. U15 and U16 — DNP, and the audit that authorised it

Both are now **DNP** in the schematic, on the PCB, and in the assembly control
data. The PCB change was **exactly two footprint attributes** — an object-level
diff shows `pads 0, segments 0, vias 0, zones 0, edge.cuts unchanged`.

### The question that mattered

KiCad's `dnp` is an assembly attribute: the pad copper stays on the board. So
the audit is not "does anything touch these pins" — plenty does — but:

1. does any **fitted Lean-DM** function need signal or current to pass
   **through the device**?
2. does any live net's **copper continuity** depend on one of its pads as a
   junction?

### Answers, from KiCad's own connectivity engine

Each footprint was **deleted entirely** on a scratch copy — not merely marked
DNP, which would keep the bridge — and the island counts re-measured:

| net | real board | U16 footprint removed | verdict |
|---|---:|---:|---|
| `+3V3` | 1 island (430 items) | **1 island** | not load-bearing |
| `/I2C_SCL_INT` | 1 island (67 items) | **1 island** | not load-bearing |
| `/I2C_SDA_INT` | 1 island (65 items) | **1 island** | not load-bearing |

| net | real board | U15 footprint removed | verdict |
|---|---:|---:|---|
| `+3V3` | 1 island (430 items) | **1 island** | not load-bearing |

> An earlier intermediate result from the project's own approximate island
> code reported `U15.1` as load-bearing for `+3V3` (42 → 43 islands). That
> approximation is unreliable on a 430-item net; KiCad's engine is
> authoritative and says otherwise. **No caveat attaches to either DNP.**

### Through-device paths

| device | through-path | Lean-DM status |
|---|---|---|
| `U16` TCA9517A | A side (`SCLA`/`SDAA`, internal I2C) ↔ B side (`SCLB`/`SDAB` → `R47`/`R48` → `J5.15/16`) | the B side is **entirely deferred**; the only function is buffered external I2C |
| `U15` TPS22918 | `VIN` (+3V3) → `VOUT` (`ACC_3V3_SW`) | the switched rail is **deferred**; no fitted Lean-DM load remains on `ACC_3V3_SW` — its other nodes are `R46`, `C38`, `C42`, `TP12`, `J5.19`, and the DNP `R49`/`R50` |

**U16: DNP SAFE. U15: DNP SAFE.** No dependency found for either.

`U15` DNP also removes the condition the withdrawn "KEEP SAFE" verdict rested
on: with `ACC_PWR_EN` deferred, a **fitted** TPS22918 would sit with `ON`
floating, because `R17` is on a different island. Not populating it is the
correct resolution.

### Support passives — classified individually, not swept

| part | value | net(s) | Lean-DM disposition |
|---|---|---|---|
| `R17` | 100 k | `ACC_PWR_EN` → GND | **KEEP FITTED** — the only passive defining `U3.20`'s node; harmless, and it is what makes `ACC_PWR_EN` safe if Full Beta routes it |
| `C39` | 100 nF | `Net-(U15-CT)` → GND | DNP-ELIGIBLE / **KEEP** — bare cap to GND on a dead net |
| `R46` | 100 k | `Net-(U15-QOD)` ↔ `ACC_3V3_SW` | DNP-ELIGIBLE / **KEEP** — both ends dead |
| `C38` | 1 µF | `ACC_3V3_SW` → GND | DNP-ELIGIBLE / **KEEP** — also AC-grounds the unpowered `J5.19` pin |
| `C42` | 100 nF | `ACC_3V3_SW` → GND | DNP-ELIGIBLE / **KEEP** — as `C38` |
| `R47` | 22 R | `Net-(U16-SCLB)` ↔ `I2C_SCL_EXT_HDR` | DNP-ELIGIBLE / **KEEP** — both ends dead |
| `R48` | 22 R | `Net-(U16-SDAB)` ↔ `I2C_SDA_EXT_HDR` | DNP-ELIGIBLE / **KEEP** — both ends dead |
| `TP12` | test point | `ACC_3V3_SW` | KEEP — no part |
| `R49`, `R50` | 4.7 k | ext-bus pull-ups | already DNP, **pre-existing full Beta**, not a DM decision |

This follows the precedent already set for `C9`, `C10`, `R15`, `C18` and `C12`:
a part sitting between two dead or bare nets costs nothing to fit and removes a
way to get the build wrong. No unrelated `+3V3` component is touched.

### One manufacturing consequence that needs stating

`U15` and `U16` are the first DNP parts on this board whose pads sit adjacent
to **live, must-work** nets:

| adjacency | gap | what a stray solder ball would bridge |
|---|---:|---|
| `U16.1` (+3V3) ↔ `U16.2` (`I2C_SCL_INT`) | **0.400 mm** | the 3.3 V rail onto the **internal I2C bus** |
| `U16.2` ↔ `U16.3` | 0.400 mm | `SCL` to `SDA` |
| `U15.1` (+3V3) ↔ `U15.2` (GND) | 0.650 mm | a short across the 3.3 V rail |

The assembly DNP control document carries **no paste or stencil policy**. It
needs one: **DNP footprints must have no paste apertures**, or the stencil must
be modified for them. This is an ordinary fab instruction, not a design change,
and it is recorded in
[fab/ASSEMBLY-DNP-CONTROL.md](fab/ASSEMBLY-DNP-CONTROL.md).

## 5. Other Lean deferrals — unchanged

`XGPIO0`–`3`, `8`–`13` NO ROUTE · `XGPIO13_HDR` NO ROUTE · `TEST_GPIO45` NO
ROUTE · `TEST_GPIO46` NO ROUTE · SW9 `TP13` branch NO ROUTE · `D2`–`D7` DNP ·
speaker deferred · IR deferred · physical NFC deferred.

No area reclaimed. No component moved. No pin renumbered.

## 6. Firmware note

`U3.20` (TCA9535 P17, `ACC_PWR_EN`) joins the ten deferred XGPIO ports as an
expander pin with no external connection. The TCA9535 has no internal pull-ups,
so firmware should configure every unconnected port as an **output** rather
than leave it a floating input. This is a pre-existing Lean-DM condition, not
new — it now covers one more pin.
