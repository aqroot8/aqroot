# AQROOT Beta DM — Lean-DM scratch routing study

> ## SUPERSEDED AS AN ARCHITECTURE — RETAINED AS EVIDENCE
>
> This study solved the **C16** demand set: four XGPIO **plus** external I2C,
> `Net-(U16-SCLB/SDAB)`, `ACC_PWR_EN` and `ACC_3V3_SW`. The Lean-Core ruling
> defers all six of those, so the release architecture and the negotiated solves
> below are **not** carried forward as assumptions. The Lean-Core pass starts
> again from the current real board.
>
> What stays authoritative here:
>
> * the `U11` pad geometry and the `BQ25185_STAT2` / `BAT_PROTECTED_P` escape
>   contention (§5) — still the live problem
> * the verified `BQ25185_STAT1` candidate and its DRC/DFM result (§6, §7)
> * the two **router-model corrections** in §6 — hardcoded via radius, and
>   courtyard-scoped power necking. Both are fixed in the tooling and both apply
>   to every pass from here on
> * the finding that `ACC_3V3_SW` was the last unjoined commodity — now moot,
>   since the net is deferred
>
> See [BETA-DM-LEAN-CORE-ROUTING.md](BETA-DM-LEAN-CORE-ROUTING.md) for the
> authoritative Lean-Core routing study.

**SCRATCH ONLY. No real-board copper was written.** The Beta-DM PCB and the DRU
are byte-identical to `6adf065`; `hardware/beta/` has an empty diff against
`beta-full-reference-v1`. No pours, no component moves, no DNP decisions, no
rule exception, no pin renumbered, no area reclaimed.

**Result, stated plainly:**

* The Lean four-XGPIO problem is **materially easier** than the full-fourteen
  problem, and it breaks the phase-2 deadlock: **all four selected XGPIO join,
  `ACC_PWR_EN` joins, and both re-land commodities (`SX1262_RXEN`,
  `WAKE_ATTN_N_HDR`) get home.** Phase 2 could not do any of that.
* But the header solve **still does not converge**, and the starved commodity
  has *moved*: from `SX1262_RXEN` in phase 2 to the **`ACC_3V3_SW` accessory
  rail** now. In the better of the two release variants, **11 of the 12
  commodities join and `ACC_3V3_SW` is the only one that does not.**
* Outside the header there **is** a landable candidate: `BQ25185_STAT1` closes
  and the `ISET` and `BAT_PROTECTED_P` re-lands both come home, verified at
  **0 KiCad DRC errors, no warning regression, DFM pass**. `BQ25185_STAT2` does
  not close — it and the battery-rail re-land want the same escape lane out of
  `U11`'s left column.

So the Lean-DM must-work non-GND residual does **not** reach zero in this pass.
Against the 16:

| | lines | status |
|---|---:|---|
| `BQ25185_STAT1` | **1** | **closed and fully verified** — DRC-clean candidate, DFM pass |
| `XGPIO4/5/6/7`, both ext-I2C header links, `Net-(U16-SCLB/SDAB)`, `ACC_PWR_EN` | **11** | **join** in the variant-B solve, but not separably — topology proven, candidate not landable |
| `ACC_3V3_SW` | **3** | **does not join** — the one remaining header blocker |
| `BQ25185_STAT2` | **1** | **does not close** — contends with the battery-rail escape at `U11` |

---

## 1. Starting state

| item | measured |
|---|---|
| HEAD | `6adf065` |
| DRC | 0 errors, 240 warnings, 216 unconnected |
| ledger | `216 = A55 + B130 + C16 + D15` |
| `hardware/beta/` | empty diff |

## 2. The demand set

Twelve simultaneous commodities in the header window `(8, 2)–(62, 30)`, grid
0.05 mm, 1081 × 561 cells:

| commodity | why it is in the problem |
|---|---|
| `/XGPIO4`, `/XGPIO5`, `/XGPIO6`, `/XGPIO7` | the Lean four |
| `I2C_SCL_EXT_HDR`, `I2C_SDA_EXT_HDR` | external I2C at the header |
| `Net-(U16-SCLB)`, `Net-(U16-SDAB)` | the `U16` buffer B side |
| `/ACC_PWR_EN` | `U16.5` EN and `U15.3` ON — external I2C never enables without it |
| `ACC_3V3_SW` | `U16.8` VCCB — the external bus B side is unpowered without it |
| `/SX1262_RXEN` | **re-land**, carried simultaneously so no J5 route can eat the corridor it needs to get home |
| `WAKE_ATTN_N_HDR` | **re-land**, same reason |

Per-net obstacle maps are built once and never contain another net's new
copper: other nets are **present cost, not obstacles**, which is what makes the
negotiated solve order-independent.

`BQ25185_STAT1` / `STAT2` are a separate, disjoint problem in the power-tree
region and are solved on their own in §5.

## 3. Release

The joint minimum over all ten header demands at once — **15 objects
(2 vias), 25.302 mm**. Derivation and the two ruling deviations it forces are
in [BETA-DM-LEAN-SCOPE.md](BETA-DM-LEAN-SCOPE.md) §5.

| net | objects | length | must re-land? |
|---|---:|---:|---|
| `XGPIO9_HDR` | 6 | 7.057 mm | no — Lean-DM deferred function |
| `WAKE_ATTN_N_HDR` | 6 | 9.520 mm | **yes** |
| `/SX1262_RXEN` | 3 | 8.725 mm | **yes** |

No hard lock is in the set, asserted object by object.

## 4. Negotiated-congestion solve — the header

13 iterations, present-cost factor rising 0.60 → 385.61 (**640×**), 1197 s.

| iter | pfac | conflicts | unjoined | total mm |
|---:|---:|---:|---:|---:|
| 0 | 0.60 | 7 220 | 4 | 315.50 |
| 1 | 1.08 | 8 911 | 4 | 363.39 |
| 2 | 1.94 | 8 020 | 3 | 361.86 |
| 3 | 3.50 | 7 780 | 3 | 363.40 |
| 4 | 6.30 | 7 889 | 5 | 370.94 |
| 5 | 11.34 | 7 854 | 5 | 373.28 |
| 6 | 20.41 | 7 729 | 4 | 379.99 |
| 7 | 36.73 | 7 507 | 5 | 369.25 |
| 8 | 66.12 | 7 560 | 3 | 378.49 |
| 9 | 119.02 | 7 385 | 5 | 373.54 |
| 10 | 214.23 | 7 427 | 4 | 385.18 |
| 11 | 385.61 | 7 739 | 5 | 379.07 |

**NOT CONVERGED.** Conflicts plateau at 7 400–8 900 from iteration 2 onward
while the present-cost factor rises 640×, and total length inflates rather than
falling. That is the signature of a saturated corridor, not of a bad search —
the same signature phase 2 reported, at roughly half the conflict count.

### Per-commodity result

| commodity | segments | vias | length | open |
|---|---:|---:|---:|---:|
| `XGPIO4` | 108 | 6 | **33.874 mm** | **0** |
| `XGPIO5` | 134 | 7 | **41.764 mm** | **0** |
| `XGPIO6` | 109 | 7 | **33.056 mm** | **0** |
| `XGPIO7` | 93 | 3 | **33.000 mm** | **0** |
| `Net-(U16-SCLB)` | 79 | 2 | **20.913 mm** | **0** |
| `Net-(U16-SDAB)` | 92 | 2 | **27.289 mm** | **0** |
| `/ACC_PWR_EN` | 142 | 6 | **53.550 mm** | **0** |
| `/SX1262_RXEN` re-land | 24 | 0 | **8.244 mm** | **0** |
| `WAKE_ATTN_N_HDR` re-land | 86 | 2 | **28.418 mm** | **0** |
| `I2C_SCL_EXT_HDR` | 130 | 4 | 33.140 mm | **1** |
| `I2C_SDA_EXT_HDR` | 173 | 4 | 54.029 mm | **1** |
| `ACC_3V3_SW` | 50 | 3 | 11.795 mm | **3** |

### What changed against phase 2, and what did not

**Broken:**

* Phase 2 ended with `/SX1262_RXEN` itself starved — it paid for the corridor
  and could not get back in. **Here it re-lands in 8.244 mm with zero vias.**
  The Lean release is a *pad escape* (`f4200000` + `f4200001` + `f4200002`,
  8.725 mm) rather than a corridor-wide one, so RXEN's route home is short.
* Phase 2 could not join `ACC_PWR_EN`. **Here it joins**, 53.550 mm — which is
  what makes the external-I2C enable reachable at all.
* All four selected XGPIO join. Phase 2 joined all fourteen but only while
  starving RXEN, `ACC_3V3_SW` and `ACC_PWR_EN`.

**Not broken:** the corridor is still saturated. The demand that now cannot be
separated is the **external-I2C rail and its header links**, which live in the
densest part of the cluster around `U15`, `U16`, `R46`–`R48` and `C38`/`C42`.
`ACC_3V3_SW` is the worst of them: a **0.40 mm** P3V3-geometry net with five
fitted islands inside that corner, and it accounts for 3 of the 5 open joins.

### Variant B — release the Lean-active nets' own copper too

Variant A stitches each rail to whatever fragments of it are already on the
board. Variant B additionally releases the **Lean-ACTIVE** nets' own partial
copper — `ACC_3V3_SW`, `I2C_SCL_EXT_HDR`, `I2C_SDA_EXT_HDR`: 40 further
objects, 56.339 mm — so the router can plan each rail whole. Nothing here is
deferred; every one of those nets stays a commodity and must come back.

**Release total: 55 objects.** 11 iterations, 986 s.

| iter | pfac | conflicts | unjoined | total mm |
|---:|---:|---:|---:|---:|
| 0 | 0.60 | 6 093 | 4 | 354.15 |
| 3 | 3.50 | 6 861 | 4 | 408.70 |
| 6 | 20.41 | 6 309 | 4 | 420.25 |
| 9 | 119.02 | 6 248 | 4 | 405.42 |

| commodity | segments | vias | length | open |
|---|---:|---:|---:|---:|
| `XGPIO4` | 80 | 4 | **30.939 mm** | **0** |
| `XGPIO5` | 124 | 7 | **42.243 mm** | **0** |
| `XGPIO6` | 119 | 7 | **33.776 mm** | **0** |
| `XGPIO7` | 111 | 3 | **32.361 mm** | **0** |
| `I2C_SCL_EXT_HDR` | 153 | 7 | **51.558 mm** | **0** |
| `I2C_SDA_EXT_HDR` | 100 | 2 | **28.962 mm** | **0** |
| `Net-(U16-SCLB)` | 169 | 4 | **49.580 mm** | **0** |
| `Net-(U16-SDAB)` | 79 | 2 | **22.208 mm** | **0** |
| `/ACC_PWR_EN` | 192 | 9 | **64.643 mm** | **0** |
| `/SX1262_RXEN` re-land | 21 | 0 | **8.493 mm** | **0** |
| `WAKE_ATTN_N_HDR` re-land | 86 | 2 | **29.285 mm** | **0** |
| `ACC_3V3_SW` | 33 | 2 | 11.370 mm | **4** |

**Releasing the ext-I2C links' own copper closed both of them.** Variant B
leaves exactly one commodity unjoined, and it is `ACC_3V3_SW`.

Still NOT CONVERGED — conflicts plateau at 6 250–6 900 while the present-cost
factor rises 200× — so these routes are joined but not separated, and the
candidate is not DRC-clean. It is a proof that the topology exists, not a
candidate that can land.

**The Lean-DM header problem has therefore reduced to one net.** `ACC_3V3_SW`
is 0.40 mm P3V3 geometry with its 0.65 mm class via, it has five fitted islands
(`U15.6`, `C38.1`, `R46.2`, `TP12.1`, and the `U16.8` + `C42.2` + `J5.19`
group), and they are spread across the densest corner of the cluster. Everything
else in the Lean must-work header set now has a route.

### Sequential cross-check

Sequential routing with mutual obstacles — separated by construction rather
than negotiated towards separation — was run over six orders as a control. Best
was 12 of 12 joins open ⇒ **open 12** with `acc-first`. It confirms the routes
exist individually (`ACC_PWR_EN` 46.187 mm, `XGPIO7` 25.264 mm) but that
whichever net is placed first walls the rest. That is why negotiation is the
right tool here and why its plateau is meaningful.

## 5. `BQ25185_STAT1` / `STAT2` — separate region, and it nearly closes

`U11` is a `Texas_DLH0010A_WSON-10-1EP_2.2x2mm_P0.4mm`, **0.400 mm pitch**.
Read from the board:

```
left column  x = 63.900     right column x = 66.100     EP GND 0.900 x 1.500
  U11.1 y 66.200 BQ25185_SYS   U11.10 y 66.200 USB_VBUS_CHG   at (65.000, 67.000)
  U11.2 y 66.600 BAT_PROTECTED_P  U11.9 y 66.600 STAT1
  U11.3 y 67.000 STAT2         U11.8 y 67.000 ISET
  U11.4 y 67.400 GND           U11.7 y 67.400 ILIM_VSET
  U11.5 y 67.800 GND           U11.6 y 67.800 Net-(U11-TS_MR)
```

Pads are 0.750 × 0.200. Between-pin escape needs 0.20 + 0.20 + 0.20 = 0.600 mm
against a 0.400 mm pitch, so **every escape must be outboard**, and the exposed
GND pad blocks the inboard direction. The left column therefore has three
signals — `BQ25185_SYS`, `BAT_PROTECTED_P`, `STAT2` — that all have to leave
westward inside a band only 0.800 mm tall.

**Release: 3 objects, 1.000 mm** — plus the in-window `ISET` run.

| net | objects | length | note |
|---|---:|---:|---|
| `/01_POWER_TREE/ISET` | 5 | 7.500 mm | Default class, ordinary signal |
| `/BAT_PROTECTED_P` | 2 | 1.000 mm | the 0.20 mm F.Cu neck off `U11.2` **and its 0.80/0.40 via**. The 0.60 mm BAT_MAIN trunk beyond the via is **not** released |

Keeping the trunk means **no power geometry is re-landed at signal width**: the
re-land reproduces the same necked pad escape the board already carries and the
DRU already permits for `U11`. That is the defect in the phase-2 plan, which
released `BAT_PROTECTED_P` (0.60 mm BAT_MAIN) and `BQ25185_SYS` (up to 0.80 mm
SYS_MAIN) and re-landed both at 0.20 mm.

### Result

All 24 route orders were tried. `STAT2` and the `BAT_PROTECTED_P` re-land are
**mutually exclusive**: whichever is routed first closes and the other fails.
Two orders reach open = 1, and **they are not equivalent**:

| order | closes | leaves open | landable? |
|---|---|---|---|
| `STAT2` first | `STAT1` 28.846 mm, `STAT2` 21.672 mm, `ISET` 7.242 mm | `BAT_PROTECTED_P` | **no — it severs the battery rail** |
| `STAT1` first | `ISET` 7.242 mm, `STAT1` 28.846 mm, `BAT_PROTECTED_P` 0.650 mm | `STAT2` | **yes** |

DRC scores both identically, because "unconnected item" does not know that one
of them is the battery. The order is therefore chosen by what the net **is**,
not by the count. The landable candidate is the second.

### The landable candidate, verified

| net | segments | vias | length | open |
|---|---:|---:|---:|---:|
| `ISET` re-land | 15 | 0 | **7.242 mm** | **0** |
| `BQ25185_STAT1` | 68 | 2 | **28.846 mm** | **0** |
| `BAT_PROTECTED_P` re-land | 2 | 1 | **0.650 mm** | **0** |
| `BQ25185_STAT2` | 0 | 0 | — | **1** |

**The named cause, read from the DRU:**

```
(rule "Pad-escape necking - width, fine-pitch power packages"
    (constraint track_width (min 0.20mm))
    (condition "A.intersectsCourtyard('U11') || ... "))

(rule "BAT_MAIN minimum width"     min 0.6000 mm
(rule "BAT_MAIN routed clearance"  min 0.3000 mm
```

The 0.20 mm allowance is scoped by `intersectsCourtyard('U11')`: a
`BAT_PROTECTED_P` track may be 0.20 mm **only while it is inside U11's
courtyard**, and must be 0.60 mm the moment it leaves. Its layer transition
therefore needs the class 0.80 mm via, and that via is the problem — centred on
the `U11.2` lane at y = 66.600, with BAT_MAIN's 0.30 mm clearance it occupies
y ≈ 65.90 … 67.30, which is the whole of the y = 67.000 lane `U11.3` needs.
Releasing the neck lets `STAT2` out; re-landing the via puts it straight back.

This is not a modelling guess — it was **confirmed by KiCad itself**. Releasing
one more lane west (the 1.500 mm B.Cu run, 8 objects / 10.000 mm) let the
router re-land BAT, and the resulting board DRC'd with **exactly one error**:

```
track_width | Track width (rule 'BAT_MAIN minimum width' min width 0.6000 mm;
              actual 0.2000 mm)
    Track [/BAT_PROTECTED_P] on B.Cu, length 1.5000 mm at (62.900, 66.600)
```

— the re-land had left U11's courtyard still necked. Releasing the diagonal and
the second via as well (10 objects / 17.098 mm) made it **worse still**, open 2,
because there is then more 0.60 mm trunk to re-land through a congested area.

So the narrow release is the right one, and the open join is real.

**What this needs:** a dedicated `U11` left-column pad-escape pass that plans
`BQ25185_SYS`, `BAT_PROTECTED_P` and `STAT2` **together** as three parallel
0.20 mm lanes at y = 66.200 / 66.600 / 67.000 — which is exactly at the legal
limit, 0.20 mm track with 0.20 mm gap on a 0.400 mm pitch — and places the
0.80 mm BAT transition via far enough west to clear all three. That is a
tractable, well-posed problem, but it is its own pass and it is not taken here.

## 6. DRC on the scratch candidate

The landable `STAT` candidate was written to a scratch project, **zones refilled
with KiCad's own `pcbnew`** (43 zones) — `kicad-cli` cannot refill, and a new
via judged against a stale fill reports bogus zone clearances — and then DRC'd.

| item | measured |
|---|---|
| DRC errors | **0** |
| warnings | **240** — unchanged; **warning-type delta vs baseline: NONE** |
| unconnected | **215** = 216 − `BQ25185_STAT1` |

Getting there took two corrections that KiCad found and the raster had missed.
Both are worth recording because they would have bitten any future pass.

**1. The raster hardcoded a 0.30 mm via radius.** Every net was modelled as if
it used a 0.60 mm via. `BAT_PROTECTED_P` is BAT_MAIN and its class via is
**0.80 mm**, so its re-land was under-stamped by 0.10 mm and KiCad reported:

```
clearance | rule 'Pad-escape necking - clearance' clearance 0.2000 mm; actual 0.1400 mm
    Pad 1 [BQ25185_SYS] of U11        Via [/BAT_PROTECTED_P] at (63.100, 66.600)
```

`route.Grid.build` now takes the real `via_pad` / `via_drill` and stamps
`via_pad / 2` — and the hole-to-hole margin uses the real drill radius instead
of a fixed 0.15 mm. **Impact on the rest of this study: the header candidate
routes 0.60 mm vias everywhere except `ACC_3V3_SW`, whose class via is 0.65 mm,
so three of its vias were under-stamped by 0.025 mm. That does not change the
header conclusion — that solve does not converge for reasons two orders of
magnitude larger — but any future header candidate must be re-checked with the
fixed model.**

**2. A power net cannot be routed at one width.** The router routes a net at a
single width, so the `BAT_PROTECTED_P` escape came out 0.20 mm along its whole
length, and the 0.100 mm B.Cu tail that reaches the surviving trunk landed
outside `U11`'s courtyard where the class minimum applies. The DRU's scope is
`A.intersectsCourtyard('U11')`, so 0.20 mm is legal for the F.Cu neck (which
does intersect) and illegal for that tail (which does not). Widening exactly
that one 0.100 mm segment to 0.60 mm — what a person would draw by hand —
clears it.

With both corrections the candidate is clean, and that is a real, independent
confirmation that the model now matches KiCad's own rule engine on this board.

The header candidate was **not** written to a scratch board and **not** DRC'd,
because it does not converge — 7 400 residual conflicts mean it would report
thousands of clearance errors. Writing it would produce a number, not a result.

## 7. DFM — vias under fitted SMDs

Every via the `STAT` candidate adds was audited against fitted-footprint bodies
and courtyards, with same-net pads excluded from the mask-dam check (a via
landing on its own test point shares one mask opening by design).

| via | net | position | size/drill | verdict |
|---|---|---|---|---|
| 1 | `BQ25185_STAT1` | (70.850, 82.500) | 0.60/0.30 | clear of every fitted body and courtyard |
| 2 | `BQ25185_STAT1` | (67.750, 66.400) | 0.60/0.30 | clear of every fitted body and courtyard |
| 3 | `BAT_PROTECTED_P` | (63.000, 66.600) | 0.80/0.40 | clear; nearest foreign pad `U11.1` at **0.6231 mm** copper gap, **mask dam 0.5718 mm** — comfortable |

**Vias under a fitted SMD body or courtyard: 0 of 3. DFM PASS.**

Worth recording: the *rejected* `STAT2`-first candidate placed a via at
(60.950, 84.400), **under the body and courtyard of `J4`** — a fitted
through-hole JST-PH battery connector. That is not something to wave through on
a tenting argument, and it is a second reason the landable order is the right
one. A future pass should forbid new via sites inside fitted-footprint
courtyards outright, so candidates are DFM-clean by construction rather than by
audit.

No new rule exception was taken anywhere in this study.

## 8. Preservation

PCB and DRU byte-identical to `6adf065`. `hardware/beta/` empty diff.
`BOOT_N`, `WAKE_INT_N`, the R2 candidate-B `+3V3` escape, the microphone I2S,
internal I2C, SPI-A, SPI-B, USB, the backlight, the buttons, `CC1101`, every
`SX1262` control other than the three scratch-released pad-escape objects,
the RXEN In2/E5 crossing, Edge.Cuts and the mounting holes are all untouched.
No pours. No component moved. No pin renumbered. No area reclaimed.

## 9. What a next pass needs

In priority order:

1. **`ACC_3V3_SW` is the whole remaining header problem.** Variant B joins
   every other Lean must-work header commodity. Plan that rail *first and
   whole*, as a single-commodity problem with the other eleven as fixed
   obstacles, rather than negotiating it against them. Worth testing in that
   pass: whether the rail needs all five islands stitched in one topology, or
   whether `TP12` and `C38` can hang off spurs taken late.
   Note also that the fixed via model (§6) changes `ACC_3V3_SW`'s three
   0.65 mm vias slightly, so the rail must be re-solved with the corrected
   raster in any case.
2. **A `U11` left-column pad-escape pass** for `BQ25185_SYS` /
   `BAT_PROTECTED_P` / `STAT2` as three parallel lanes, §5.
3. **Forbid new vias inside fitted-footprint courtyards** in the router, so
   candidates are DFM-clean by construction instead of by audit.
4. Only then, more negotiation budget. The plateau across 12 iterations at a
   640× present-cost rise, and again across 11 iterations at 200×, says search
   budget is not what is missing.
