# AQROOT Beta DM — LEAN Demo Model scope

> ## SUPERSEDED IN PART BY THE LEAN-CORE FINAL SCOPE RULING
>
> This document is **retained as study evidence**. Its measurements stand; three
> of its *rulings* do not. See
> [BETA-DM-LEAN-CORE-SCOPE.md](BETA-DM-LEAN-CORE-SCOPE.md) for the authoritative
> Lean-DM scope.
>
> | claim in this document | status |
> |---|---|
> | external I2C is Lean-DM **ACTIVE** (§2) | **SUPERSEDED** — buffered external J5 I2C is Lean-DM **DEFERRED**. Internal I2C is unaffected and remains MUST-WORK and hard-locked |
> | `ACC_PWR_EN` is **MUST-WORK** because it is `U16.5` EN (§1) | **SUPERSEDED FOR LEAN DM** — with external I2C deferred, `U16` is DNP and the dependency disappears |
> | `ACC_3V3_SW` is **MUST-WORK** because it is `U16.8` VCCB (§1) | **SUPERSEDED FOR LEAN DM** — same reason |
> | `U15` **KEEP SAFE / keep fitted** (§3) | **WITHDRAWN** — see the note below |
>
> ### Why the U15 verdict is withdrawn, precisely
>
> The `KEEP SAFE` verdict was **conditional on `ACC_PWR_EN` being routed**, and
> §3's "safe-state pull" row said so. But §3's "default enable state" row
> asserted the `R17` pull-down unconditionally, and this same study measured
> `U3.20`, `R17.1`, `U15.3` and `U16.5` as **four separate islands**. Both
> cannot hold on the current board: while `ACC_PWR_EN` is unrouted, `R17`
> **cannot** hold `U15.3` low, because it is not connected to it.
>
> The Lean-Core ruling defers `ACC_PWR_EN`, so the condition the verdict rested
> on is gone. A fitted `TPS22918` with a floating `ON` pin is not acceptable,
> and `U15` is therefore **DNP** for Lean-DM. The dependency evidence in §1 and
> the measurements in §3 remain valid and are what justify that.
>
> The two release deviations recorded in §5 (`SX1262_RXEN`, `WAKE_ATTN_N_HDR`)
> were derived for the C16 demand set and are **not** carried forward as
> assumptions; the Lean-Core pass re-derives the release from scratch.

Authoritative record of the Lean-DM scope ruling as **implemented against the
measured board**, not as assumed. Created against Beta-DM head `6adf065`.

**This pass changed no copper.** The PCB and the DRU are byte-identical to
`6adf065`. `hardware/beta/` (full Beta, frozen at `beta-full-reference-v1`) has
an empty diff. No pours, no component moves, no pin renumbering, no area
reclaim.

## Starting state, measured

| item | measured |
|---|---|
| HEAD | `6adf065` |
| DRC | **0 errors**, 240 warnings, **216 unconnected** |
| ledger | `216 = A55 + B130 + C31` — reproduced exactly from the DRC report |
| `hardware/beta/` | empty diff vs `beta-full-reference-v1` |

---

## 1. The one place the ruling does not survive its own dependency audit

The ruling asks for two things that this schematic cannot both deliver:

* §5 / §12 — **external I2C stays MUST-WORK**, U16 required, path audited end
  to end.
* §7 — **`ACC_PWR_EN` and `ACC_3V3_SW` are LEAN-DM DEFER / NO ROUTE.**

Read from the board, not from the block diagram:

| net | nodes |
|---|---|
| `/ACC_PWR_EN` | `U3.20`, `R17.1`, `U15.3`, **`U16.5`** |
| `ACC_3V3_SW` | `U15.6`, **`U16.8`**, `R46.2`, `C38.1`, `C42.2`, `R49.2`, `R50.2`, `TP12.1`, `J5.19` |

`U16` is a **TCA9517ADGK** level-translating I²C buffer in VSSOP-8:

```
U16.1 VCCA = +3V3          U16.8 VCCB = ACC_3V3_SW      <- the switched rail
U16.2 SCLA = I2C_SCL_INT   U16.7 SCLB = Net-(U16-SCLB) -> R47 22R -> J5.16
U16.3 SDAA = I2C_SDA_INT   U16.6 SDAB = Net-(U16-SDAB) -> R48 22R -> J5.15
U16.4 GND                  U16.5 EN   = ACC_PWR_EN      <- the accessory enable
```

`U15` is a **TPS22918DBVR** load switch in SOT-23-6: `1 VIN=+3V3`, `2 GND`,
`3 ON=ACC_PWR_EN`, `4 CT=Net-(U15-CT)` (`C39` 100 nF, already routed and
closed), `5 QOD=Net-(U15-QOD)` (`R46` 100 k to VOUT), `6 VOUT=ACC_3V3_SW`.

So on this board:

* **`ACC_PWR_EN` is not only the accessory-power enable. It is also the U16
  buffer enable.** Its only passive is `R17` 100 k to GND and its only driver
  is `U3.20`. Left unrouted, `U3.20`, `R17.1`, `U15.3` and `U16.5` are four
  separate islands: neither `U15` nor `U16` can see the pull-down or the
  expander, and both enable pins float independently.
* **`ACC_3V3_SW` is not only the accessory rail. It is `U16` VCCB.** Left
  unrouted, `U16.8` sits on an island with `C42.2` and `J5.19` and has no
  source at all. A bus buffer cannot drive an unpowered side.

**Deferring the switched accessory rail therefore deletes external I2C.** The
switched-accessory system and the external-I2C enable system are one circuit on
this design, not two.

`R49` / `R50` (4.7 k pull-ups from the external bus up to `ACC_3V3_SW`) are
pre-existing **full-Beta DNP** — the accessory supplies its own pull-ups — so
they are not what makes the rail load-bearing. `U16.8` VCCB is.

### Ruling applied

§5 and §12 rank external I2C as MUST-WORK, and §12 explicitly orders the path
to be audited for electrical completeness. The audit result is taken as
controlling, and §7 is reversed **only as far as external I2C requires**:

| net | ruling §7 | after audit | why |
|---|---|---|---|
| `/ACC_PWR_EN` | DEFER | **MUST-WORK** | `U16.5` EN and `U15.3` ON; without it external I2C never enables |
| `ACC_3V3_SW` | DEFER | **MUST-WORK** | `U16.8` VCCB; without it the external bus B side is unpowered |
| `Net-(U15-QOD)` | DEFER | **LEAN-DM DEFERRED — confirmed safe** | §3 below |

This is a dependency finding, not a scope expansion. The *switched accessory
power feature* is still deferred in the sense the ruling intended — no
sequencing behaviour and no `ACC_PWR_EN` firmware feature is required for the
demo — but the copper cannot be.

---

## 2. Lean-DM active J5 interface

| function | net(s) | status |
|---|---|---|
| four XGPIO | `/XGPIO4`, `/XGPIO5`, `/XGPIO6`, `/XGPIO7` | **MUST-WORK** |
| external I2C | `I2C_SCL_EXT_HDR`, `I2C_SDA_EXT_HDR`, `Net-(U16-SCLB)`, `Net-(U16-SDAB)` | ~~MUST-WORK~~ **SUPERSEDED — LEAN-DM DEFERRED** |
| external I2C enable + rail | `/ACC_PWR_EN`, `ACC_3V3_SW` | ~~MUST-WORK~~ **SUPERSEDED — LEAN-DM DEFERRED** |
| FAST_IO | `FAST_IO_GPIO43_HDR` | ACTIVE — already routed, untouched |
| WAKE | `WAKE_ATTN_N_HDR` | ACTIVE — routed; 6 objects released and **re-landed** by the Lean plan, §5 |
| +3V3 header access | `J5.1` | ACTIVE — already routed |
| GND header access | `J5.2` / `7` / `20` / `24` / `25` | bucket B, board-wide GND closeout |

Names are unchanged. There is no `DM_XGPIO` renumbering.

The four selected XGPIO land on `J5.8`, `J5.9`, `J5.10`, `J5.11` — a contiguous
run of four header pins, and **`J5.7` is GND, directly adjacent** to `J5.8`:

```
   x =   44.620   42.080   39.540   37.000
 row A    J5.7     J5.9    J5.11    J5.13     GND, XGPIO5, XGPIO7, WAKE_ATTN_N
 row B    J5.8    J5.10    J5.12    J5.14     XGPIO4, XGPIO6, XGPIO8_HDR, XGPIO9_HDR
```

That is a usable accessory footprint for both the sensor-pod and the GPIO-card
concepts: two pins driven as outputs, two read as inputs, with a ground return
on the pin next door and `WAKE_ATTN_N` two columns away for device wake.
External I2C sits at `J5.15` / `J5.16` and `+3V3` at `J5.1`.

---

## 3. U15 accessory load-switch audit

> **VERDICT WITHDRAWN.** It was conditional on `ACC_PWR_EN` being routed. The
> Lean-Core ruling defers `ACC_PWR_EN`, so `U15.3` `ON` floats and `U15` is
> **DNP** for Lean-DM. The measurements in this table remain valid evidence.

~~**Result: KEEP U15 FITTED. No DNP recommendation. The DNP list is unchanged.**~~

| check | finding |
|---|---|
| default enable state | `ON` = `ACC_PWR_EN`, pulled down by `R17` 100 k. `U3` is a TCA9535; after reset its ports are high-impedance inputs, so `R17` holds `ON` low and **U15 powers up OFF** |
| safe-state pull | present and adequate **once `ACC_PWR_EN` is routed**. Unrouted, it is absent — one of the two reasons §7 is reversed |
| input supply | `U15.1 VIN` = `+3V3`, already routed |
| output behaviour | `U15.6 VOUT` = `ACC_3V3_SW` → `U16.8` VCCB, `C38` 1 µF, `C42` 100 nF, `TP12`, `J5.19` |
| soft start | `U15.4 CT` = `C39` 100 nF, **already routed and closed**, 0 rats |
| QOD behaviour | `U15.5 QOD` open. QOD is the drain of the internal discharge FET, **not a logic input**, so floating it is benign. The only loss is that `ACC_3V3_SW` no longer discharges through `R46` at turn-off; it decays through the accessory load and leakage instead |
| back-power | none. `U15` is a load switch fed from `+3V3`; with `ON` low, `VOUT` is not a source, and nothing on Beta-DM drives `VOUT` from the header side |
| floating input risk | **only `QOD`, which is not an input.** `ON` is defined by `R17` once routed |
| effect on `+3V3` | none beyond `U15` shutdown current |
| effect on `J5` | `J5.19` becomes a live switched 3.3 V pin once `ACC_3V3_SW` is routed — a gain, not a hazard |
| quiescent current | drawn from `VIN`; with `ON` low the device is in shutdown. Negligible against the demo budget |

`Net-(U15-QOD)` therefore **follows the switched-accessory ruling and stays
LEAN-DM DEFERRED**: no other circuit requires it, and floating `QOD` carries no
risk. If a later solve closes it at zero marginal cost it should be taken
opportunistically, but it is not a Lean requirement.

---

## 4. J5 functions deferred for Lean-DM

Nothing below is removed. No J5 pin, series resistor, `U3` assignment or
footprint changed. Every row restores for Full Beta.

| item | Lean-DM | note |
|---|---|---|
| `XGPIO0`, `1`, `2`, `3`, `8`, `9`, `10`, `11`, `12`, `13` | **LEAN-DM NO ROUTE / DEFER** | 10 of 14; series resistors stay **fitted** |
| `XGPIO13_HDR` | **LEAN-DM NO ROUTE / DEFER** | `XGPIO13` is not one of the selected four |
| `Net-(U15-QOD)` | **LEAN-DM NO ROUTE / DEFER** | audited safe, §3 |
| `TEST_GPIO45` | **LEAN-DM INTENTIONAL NO ROUTE** | ruling §9; `TP1` stays fitted and in place |
| `TEST_GPIO46` | **LEAN-DM INTENTIONAL NO ROUTE** | ruling §9; `TP2` stays fitted and in place |
| `Net-(SW9-A)` → `TP13` | **LEAN-DM INTENTIONAL NO ROUTE** | ruling §10; the functional SW9 path is already routed, `TP13` stays fitted |

No part is DNP'd to make a ratsnest count look better. The `XGPIO` series
resistors `R51`–`R64` all stay populated.

---

## 5. Exact ordinary release the Lean plan needs

Measured as the **joint minimum** over all ten Lean header demands at once: a
net stays in the release only if removing it seals at least one demand, then
object by object inside the survivors.

**15 objects (2 vias), 25.302 mm.**

| net | objects | length | class | disposition |
|---|---|---|---|---|
| `XGPIO9_HDR` | 6 | 7.057 mm | ordinary signal | **deferred function** — Lean-DM does not re-land it; Full Beta restores it |
| `WAKE_ATTN_N_HDR` | 6 | 9.520 mm | ordinary signal | **Lean-ACTIVE — must re-land**, carried as a simultaneous commodity |
| `/SX1262_RXEN` | 3 | 8.725 mm | `E5_CROSSING` | **must re-land**, carried as a simultaneous commodity |

No hard lock is released. `BOOT_N`, `WAKE_INT_N`, the R2 candidate-B `+3V3`
escape, the microphone I2S, internal I2C, SPI-A, SPI-B, USB, the backlight, the
buttons, Edge.Cuts and the mounting holes are all absent from the set, asserted
object by object.

### Two deviations from the ruling text, both forced by measurement

**1. §16 — "Do not release `SX1262_RXEN` by default."**

The four-XGPIO problem still needs it, but for a different reason and at a
fraction of the size. `U3.20` (`ACC_PWR_EN`) sits in a **311-cell** pocket
whose wall — after *every* ordinary object in the header window is already
released — is `PAD U3` (86 cells), `I2C_SCL_INT` (26) and `SX1262_RXEN` (8).
Internal I2C was tested explicitly and is **not** load-bearing. Releasing
exactly `f4200000` (1.000 mm) and `f4200001` (4.825 mm) frees `U3.20` into a
317 524-cell region. `f4200002` (2.900 mm) is added so the release leaves no
orphan copper with no pad: **3 objects, 8.725 mm**.

That is smaller and cleaner than the 12.825 mm phase-2 set, and it is the
*whole* RXEN cost rather than a corridor-wide one. The same wall is what
disqualifies `XGPIO9`…`XGPIO13` from selection.

**2. §5 — "FAST_IO and WAKE are already functionally routed… do not disturb them."**

`FAST_IO_GPIO43_HDR` is **not** disturbed: it was tested and dropped from the
release with all ten demands still reaching. `WAKE_ATTN_N_HDR` is load-bearing
— with it kept, no Lean demand reaches at all. Only **6 of its objects,
9.520 mm** are released, and it is carried as a simultaneous routing commodity
so it must come back to one island. This is a release-and-re-land, not a
deferral: WAKE stays ACTIVE.

Both are returned for ruling rather than assumed. Neither is a **rule**
exception: no DRU relaxation, no new netclass, no clearance waiver.
