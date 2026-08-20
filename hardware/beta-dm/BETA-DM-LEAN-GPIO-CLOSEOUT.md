# AQROOT Beta DM — final Lean GPIO closeout

**SCRATCH ONLY for routing. No copper landed.** The board is byte-identical to
`090f7c3`; `hardware/beta/` has an empty diff. No pours, no component moved, no
footprint removed, no board area reclaimed, no pin renumbered, no new rule
exception.

Scope reclassification (`BQ25185_STAT1` / `STAT2`) is documentation only and
changes no copper.

## 1. Starting state

| item | measured |
|---|---|
| HEAD | `090f7c3`, `origin/master...HEAD = 0 0` |
| DRC | **0 errors**, 240 warnings, **216 unconnected** |
| ledger before | `216 = A62 + B130 + C6 + D18` |

## 2. `BQ25185_STAT1` / `STAT2` — LEAN-DM INTENTIONAL NO ROUTE

Both are BQ25185 **open-drain status outputs exposed only as diagnostic test
points** — `STAT1` → `TP6`, `STAT2` → `TP7`. They are not charger-control
inputs, not safety dependencies, not MCU inputs, and not required for USB,
boot/programming or any Demo-Model UI function. The charger operates without
these traces.

`TP6` and `TP7` stay **fitted and in place**. Neither was moved, neither was
DNP'd for bookkeeping, and the `U11` power rail — `ISET`, `BAT_PROTECTED_P`,
`BQ25185_SYS`, `BAT_MAIN` — was **not touched**.

Restoration entries are in
[BETA-DM-LEAN-RESTORATION.md](BETA-DM-LEAN-RESTORATION.md) §2a, including the
`STAT1` candidate that was fully verified last pass (28.846 mm, DRC 0 errors,
DFM pass) and can be replayed for Full Beta.

**LEAN DM CUT ONLY — FULL BETA RESTORE.**

## 3. Ledger, re-measured on the real board

```
unconnected(measured)  ==  A + B + C + D
        216            ==  62 + 130 + 4 + 20
```

**C = 4**: `XGPIO4`, `XGPIO5`, `XGPIO6`, `XGPIO7`. Measured, not assumed; the
two STAT lines moved C→D and nothing else changed. No copper was altered to
reach the count.

## 4. What may be spent, and what may not

§8 changed the economics: **Lean-deferred copper may be spent and need not
re-land.** The spend taken is **243 objects, 203.662 mm**:

| net(s) | what |
|---|---|
| `XGPIO0_HDR` … `XGPIO3_HDR`, `XGPIO8_HDR` … `XGPIO13_HDR` | the ten deferred header routes |
| `I2C_SCL_EXT_HDR`, `I2C_SDA_EXT_HDR` | external I2C, deferred |
| `ACC_3V3_SW` | switched accessory rail, deferred |
| `Net-(U15-CT)` | dead once `U15` is DNP |

`Net-(SW9-A)` is deliberately **not** spent: its switch path is active and only
the `TP13` branch is deferred — and that branch has no copper.

Each spent net gains a ratsnest line and a Full-Beta restoration entry. **The
board's unconnected total will rise, not fall, when this lands.** That is
intended: §8 forbids wasting routing capacity to re-land a deferred function.

Not spent, and unchanged: `SX1262_RXEN` (see §6), `FAST_IO_GPIO43_HDR`,
`WAKE_INT_N`, and everything else on the §9 preserve list.

## 5. Corridor measurement

Spending the deferred copper widens the corridor substantially — 0.20 mm slots
in the band y 8.0–17.5:

| x | before | after |
|---:|---:|---:|
| 29.0 | 12 | 12 |
| 32.0 | 11 | **18** |
| 35.0 | 12 | **23** |
| 38.0 | 8 | **18** |
| 41.0 | 11 | **14** |

The reachable region still pinches to a single aperture at **x ≈ 28.0 – 28.8**.
Measured on the reachable component itself at the tightest x:

```
F.Cu    y 13.700 .. 14.900   1.25 mm -> 4 parallel 0.20 mm centrelines
B.Cu    y 11.350 .. 12.300   1.00 mm -> 3
In2.Cu  y 14.600 .. 14.900   0.35 mm -> 1
                                        --
                             capacity  10   against a demand of 4
```

There is no northern or southern bypass **within the header band** — the same
figures come back when the scan covers the full window height.

## 6. `SX1262_RXEN` — not released, not needed

The release ladder settles it:

| tier | objects | length | XGPIO reachable |
|---|---:|---:|---:|
| T0 nothing | 0 | 0 mm | 0 / 4 |
| T1 deferred-function copper | 243 | 203.662 mm | 0 / 4 |
| T2 + ordinary local signals | 271 | 348.793 mm | 0 / 4 |
| T3 + `FAST_IO_GPIO43_HDR` / `WAKE_ATTN_N_HDR` | 336 | 430.301 mm | **4 / 4** |
| T4 + the `SX1262_RXEN` pad escape | 339 | 439.026 mm | 4 / 4 — **no change** |

T4 buys nothing over T3, so **`SX1262_RXEN` is untouched**, in scratch and on
the board. `FAST_IO_GPIO43_HDR` was tested and dropped from the release with
4/4 still reaching, so it is untouched too.

## 7. `WAKE_ATTN_N_HDR` — one via, and it is needed

Shrunk against all four targets, then object by object, the **reachability**
minimum is a single object: the 0.60/0.30 `WAKE_ATTN_N_HDR` via at
**(27.991, 14.152)**. Deferred copper alone — all 243 objects — leaves 0 / 4
reachable, so §10's "do not take it unless needed" test is met: it is needed.

Its re-land is the same one via placed elsewhere. §13's conditions hold: `R66`
path preserved, `J5.13` WAKE pin re-lands, the net returns to one intended
connected path, and `WAKE_INT_N` is never touched — it is a different net and
remains byte-identical.

`WAKE_ATTN_N_HDR` must be routed **last**. Placed first, its re-landed via
drops straight back into the aperture its own release opened and blocks every
XGPIO — measured, 0 / 4.

## 8. A window artifact that inverted an intermediate result

Worth recording, because it nearly produced a wrong recommendation.

With the study window `(8, 2) – (62, 30)`, every configuration returned
**exactly one** XGPIO closed — plain sequential and lane-reserved alike, at 4,
3 and 2 pins. That reads as "the corridor admits one route", and would have
meant returning to CTO under §3.

It was false. Re-measured on a window reaching `y = 70`, `XGPIO5` is **still
reachable after `XGPIO4` is routed**. The second path leaves the header band
entirely, and the study window could not see it. This is the same class of
error as the `FAST_IO_U0TXD_ROOTPROBE_CS` spine in the previous pass: a routing
window that clips a net's real escape route.

All maximum-count results below are therefore measured on the **big window**.

## 9. Maximum-useful XGPIO — measured

Sequential routing with mutual obstacles: every net already placed is a hard
obstacle for the next, so a success is **separated by construction**, which is
what §11 requires. Negotiated congestion was not used again — §6.

`WAKE_ATTN_N_HDR` is routed last in every attempt and re-lands in all of them.

| set | result | detail |
|---|---|---|
| 4/5/6/7 | **NOT COMPLETED** | the exhaustive 24-permutation big-window run was abandoned on time after the smaller results made 4 implausible. **This is an unmeasured gap, not a FAIL** |
| 4/5/6 | **FAIL** — open 1 | `XGPIO4` OK 108.0 mm · `XGPIO5` OK 25.8 mm · `XGPIO6` FAIL |
| 4/5/7, 5/6/7, 4/6/7 | **NOT COMPLETED** | same reason |
| **4 + 5** | **PASS** | `XGPIO4` **108.0 mm**, `XGPIO5` **25.8 mm**, WAKE re-landed |

**MAXIMUM CLEAN XGPIO COUNT DEMONSTRATED: 2. SELECTED: `XGPIO4`, `XGPIO5`.**

That meets §3's minimum and clears the "return to CTO" threshold.

**Stated precisely: 2 is what has been *proved*, not what has been proved to be
the maximum.** One triple was measured and failed; the other three triples and
the full four were not carried to completion. The big window makes each solve
3–5× slower and the exhaustive sweeps did not finish inside this pass. A
follow-up pass that completes them could still find 3.

### Verification of the selected pair

Written to a scratch project, zones refilled with KiCad's own `pcbnew`
(43 zones), then DRC'd:

| item | measured |
|---|---|
| DRC errors | **0** |
| warnings | **240** — warning-type delta vs the real board **NONE** |
| unconnected | **231** |

Every line of the 216 → 231 change is accounted for:

| net | delta | why |
|---|---:|---|
| `XGPIO4`, `XGPIO5` | **−2** | the two Lean must-work lines close |
| `XGPIO0/1/2/3/8/9/10/11/12/13_HDR` | **+12** | deferred header copper spent, §8, not re-landed |
| `ACC_3V3_SW` | +2 | deferred, spent |
| `I2C_SCL_EXT_HDR`, `I2C_SDA_EXT_HDR` | +2 | deferred, spent |
| `Net-(U15-CT)` | +1 | dead once `U15` is DNP, spent |
| **net change** | **+15** | 216 − 2 + 17 = **231** |

`XGPIO4` at **108.0 mm** is long for a low-speed GPIO. It is electrically fine
and DRC-legal, but it is the price of the southern detour, and it is worth the
CTO seeing the number rather than only the PASS.

## 10. DFM — one exception that needs a ruling

Nine vias are added. Seven are clear of every fitted body and courtyard, with
mask dams 0.47–0.57 mm. **Two are not:**

| via | net | position | finding |
|---|---|---|---|
| A | `XGPIO5` | (22.650, 12.350) | inside `U3`'s courtyard at local (−0.050, 0.650) — **essentially at U3's centre, under the package body** |
| B | `XGPIO5` | (20.400, 14.100) | inside `U3`'s courtyard at local (−1.800, −1.600) — **under the package body** |

`U3` is a `Package_SO:TSSOP-24_4.4x7.8mm_P0.65mm` on B.Cu. Neither via is under
`U1`'s Fab body — both sit outside its ±9.000 × ±12.750 mm outline.

Two stricter router constraints were tried and **both cost the second GPIO**:

| constraint | fitted regions blocked | result |
|---|---:|---|
| no via inside any fitted **courtyard** | 131 | `45` open 1 — `XGPIO5` FAILS |
| no via under any fitted **body** (Fab outline, or courtyard − 0.25 mm) | 131 | `45` open 1 — `XGPIO5` FAILS; `56` open 1 — `XGPIO6` FAILS, `XGPIO5` alone routes at 90.3 mm |

So this is not a router preference that can simply be tightened away:
**`XGPIO5`'s escape from `U3.9` requires a via under `U3`'s own body.** With
that forbidden, only one XGPIO closes.

In its favour: a TSSOP-24 4.4 × 7.8 mm has **no exposed thermal pad**, so there
is no paste or wicking conflict, and the vias would be tented on the component
side. This is ordinary practice on dense boards. Against it: it is a via under
a fitted package, and §13 asks for the interaction to be audited rather than
assumed.

**This is a CTO call, not a rule exception** — no DRU rule is relaxed and DRC
is clean either way. The options are: accept two tented vias under `U3`
(2 GPIO), or forbid them (1 GPIO).

## 11. Preservation

Board byte-identical to `090f7c3`. `hardware/beta/` empty diff.
`BOOT_N`, **`WAKE_INT_N`**, the R2 candidate-B `+3V3` escape, the microphone
I2S, internal I2C, SPI-A, SPI-B, USB data and CC, the backlight, the buttons,
`CC1101`, **`SX1262_RXEN` and the RXEN In2/E5 crossing**, `FAST_IO_GPIO43_HDR`,
direct `+3V3`, the GND architecture, Edge.Cuts and the mounting holes are all
untouched.
