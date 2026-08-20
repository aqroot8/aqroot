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
| 4/5/7 | **FAIL** — open 1 | `XGPIO4` OK 108.0 mm · `XGPIO5` OK 25.8 mm · `XGPIO7` FAIL |
| 5/6/7 | **FAIL** — open 1 | `XGPIO5` OK 25.8 mm · `XGPIO6` OK **94.5 mm** · `XGPIO7` FAIL |
| 4/6/7 | **NOT COMPLETED** | the big window makes each solve 3–5× slower and this one did not finish |

Three of the four triples are measured and all fail. The constant across every
one of them is **`XGPIO5`**, which closes at 25.8 mm in all three. The second
pin can be either `XGPIO4` (108.0 mm) or `XGPIO6` (94.5 mm). **`XGPIO7` has
never closed in any configuration.**

That third triple is what changed the selection — see below.
| 4 + 5 | **PASS** | `XGPIO4` 108.0 mm, `XGPIO5` 25.8 mm, WAKE re-landed |
| **5 + 6** | **PASS — SELECTED** | `XGPIO5` **25.8 mm**, `XGPIO6` **94.5 mm**, WAKE re-landed |

**MAXIMUM CLEAN XGPIO COUNT DEMONSTRATED: 2. SELECTED: `XGPIO5`, `XGPIO6`.**

### Why `5 + 6` and not `4 + 5`

Both pairs verify at DRC 0 errors with no warning delta and the same 231
unconnected. §5's tie-breakers decide, in order:

| tie-breaker | `4 + 5` | `5 + 6` | winner |
|---|---|---|---|
| 1. least release length | 243 obj / 203.662 mm + 1 WAKE via | identical | tie |
| 2. fewest released active objects | 1 (the WAKE via) | identical | tie |
| 3. fewest vias | 9 | 9 | tie |
| 4. shortest replacement routes | 133.7 mm, 115 segments | **120.3 mm, 74 segments** | **`5 + 6`** |
| 5. best physical grouping on J5 | `J5.8` + `J5.9`, spanning two columns | **`J5.9` + `J5.10`, one full column at x = 42.080** | **`5 + 6`** |

`5 + 6` wins the first tie-breaker that separates them and the one after it:
**13.4 mm shorter, 41 fewer segments, and a tidier header footprint** — two
pins in a single column, one on each row, which is a cleaner 1-output /
1-input accessory landing than a pair straddling two columns.

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

`XGPIO6` at **94.5 mm** is long for a low-speed GPIO — as is `XGPIO4` at
108.0 mm in the rejected pair. Both are electrically fine and DRC-legal, but
the length is the price of the southern detour and is worth seeing rather than
only the PASS. `XGPIO5` is the cheap one at 25.8 mm in every configuration.

## 10. DFM — one exception that needs a ruling

Nine vias are added. Seven are clear of every fitted body and courtyard, with
mask dams 0.47–0.57 mm. **Two are not:**

| via | net | position | finding |
|---|---|---|---|
| A | `XGPIO5` | (22.650, 12.350) | inside `U3`'s courtyard at local (−0.050, 0.650) — **essentially at U3's centre, under the package body** |
| B | `XGPIO5` | (20.400, 14.100) | inside `U3`'s courtyard at local (−1.800, −1.600) — **under the package body** |
| C | `XGPIO6` | (41.700, 11.800) | inside `R57`'s courtyard — a 0402 resistor, not a body concern; nearest foreign pad `U15.2` at 0.5000 mm, mask dam 0.4487 mm |

Vias A and B belong to **`XGPIO5`'s escape from `U3.9`** and are therefore
present in *both* candidate pairs — the choice between `4+5` and `5+6` does not
affect this question.

`U3` is a `Package_SO:TSSOP-24_4.4x7.8mm_P0.65mm` on B.Cu. Neither via is under
`U1`'s Fab body — both sit outside its ±9.000 × ±12.750 mm outline.

Two stricter router constraints were tried and **both cost the second GPIO**:

| constraint | fitted regions blocked | result |
|---|---:|---|
| no via inside any fitted **courtyard** | 131 | `45` open 1 — `XGPIO5` FAILS |
| no via under any fitted **body** (Fab outline, or courtyard − 0.25 mm) | 131 | **no pair closes at all** — `45` open 1, `56` open 1 (`XGPIO5` alone 90.3 mm), `67` open 1 (`XGPIO6` alone 94.5 mm) |

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


---

# PART 2 — FINAL IMPLEMENTATION PASS

## 12. Final scope

`XGPIO5` + `XGPIO6` are the final Lean-DM GPIO set. `XGPIO4` and `XGPIO7` join
the other unused XGPIO as **LEAN DM CUT ONLY — FULL BETA RESTORE**. No
footprint moved, no series resistor DNP'd, no `J5` pin renumbered.

Ledger re-derived on the real board:

```
216 = A62 + B130 + C2 + D22
```

**C = 2**: `XGPIO5` (`U3.9`↔`R56.1`), `XGPIO6` (`U3.10`↔`R57.2`).

## 13. A via-in-pad defect the earlier DFM tool missed

The verified `{5,6}` candidate placed the `XGPIO6` via at (41.700, 11.800) —
**inside `R57.2`'s SMD pad, 0.3000 mm inside that pad's paste aperture.**

KiCad does not flag via-in-pad, and the router placed it because a net's **own**
pads are exempt from clearance, so nothing upstream caught it. The earlier DFM
tool missed it too: it skipped same-net pads deliberately, to avoid reporting a
via landing on its own test point as a mask-dam violation.

The §5/§6 gate caught it: `via-in-pad: YES`, `paste over via: −0.3000 mm`.

**Fixed in the router**, not argued about: new vias may not overlap any paste
aperture. Re-solved, `{5,6}` still closes — `XGPIO5` 25.8 mm, `XGPIO6`
**107.8 mm** (up from 94.5 mm, the cost of leaving the pad), 9 vias, DRC
**0 errors**, no warning delta, 231 unconnected.

## 14. §5 U3 under-body via gate

Board facts read from the `.kicad_pcb` setup block, not assumed:

```
(tenting (front yes) (back yes))    -> every via tented BOTH sides
0 vias in the file carry a per-via (tenting ...) override
(pad_to_mask_clearance 0)           -> a pad's mask opening IS its copper outline
```

Two vias sit under `U3` (`Package_SO:TSSOP-24_4.4x7.8mm_P0.65mm`, B.Cu, no
exposed thermal pad):

| | via A | via B |
|---|---|---|
| net | `XGPIO5` | `XGPIO5` |
| centre | (22.650, 12.350) | (20.400, 14.100) |
| diameter / drill | 0.60 / **0.30 mm** | 0.60 / **0.30 mm** |
| annular ring | 0.150 mm | 0.150 mm |
| side | through — F.Cu…B.Cu | through — F.Cu…B.Cu |
| tented F.Cu / B.Cu | **YES / YES** | **YES / YES** |
| mask opening on the via | **NONE** (tented) | **NONE** (tented) |
| annulus exposed | **NO** | **NO** |
| paste over the via | **NONE** | **NONE** |
| via-in-pad | **NO** | **NO** |
| nearest foreign pad copper | `R66.1` (`WAKE_INT_N`) **0.2250 mm** to via edge | `U3.8` (`XGPIO4`) **0.2755 mm** to via edge |
| nearest paste aperture | `R66.1` 0.2250 mm | **`U3.9` 0.0250 mm** |
| nearest pad mask opening | `R66.1` 0.2250 mm | `U3.8` 0.2755 mm |
| nearest drilled hole | 0.7300 mm | 1.7304 mm |
| beneath the plastic body | yes | yes |
| min electrical clearance | 0.2250 mm — **PASS** | 0.2755 mm — **PASS** |

Every listed §5 criterion passes: drill 0.30 ≤ 0.40, tented both sides, no
paste over the via, no via-in-pad, no merged opening, clearance PASS.

### The number that stops it

**Via B sits 0.0250 mm from `U3.9`'s paste aperture.**

`U3.9` is 1.475 × 0.400 mm, long axis vertical, at (20.375, 15.163) — it
extends down to y = 14.4255, and the via edge is 25 µm below that. `U3.9` is
`XGPIO5`'s **own** pad, so there is **no short risk**. The failure mode is
different: at 25 µm the solder-mask tent cannot be relied on. Mask registration
tolerance alone is typically ±50–75 µm, so after registration error the via
annulus can sit partly inside `U3.9`'s opening, and solder from that joint
wicks into the barrel — a **starved or open joint on a 0.65 mm pitch TSSOP
pin**.

§5's floor for a mask web is **0.125 mm preferred, 0.100 mm absolute**. 0.025 mm
is a quarter of the absolute floor.

### What happens if a real web is enforced

The constraint was put into the router and the pair re-solved:

| mask web enforced | result |
|---|---|
| none (as verified) | `XGPIO5` 25.8 mm + `XGPIO6` 107.8 mm — **both close** |
| **0.100 mm** (absolute floor) | **only ONE closes** — `XGPIO5` alone 91.5 mm, or `XGPIO6` alone 107.8 mm |
| **0.125 mm** (preferred) | **only ONE closes** — same |

**§5's STOP therefore applies: the pair is not landed.**

## 15. R57 via — resolved

The `XGPIO6` via inside `R57`'s courtyard is **gone** from the corrected
candidate. With via-in-pad forbidden the router routes `XGPIO6` clear of it, at
the cost of 13.3 mm of extra length. No via now sits in or under any solder
termination.

## 16. Status at the previous pass: NOT LANDED

The real board is **unchanged**. No copper was written. `hardware/beta/` has an
empty diff.

The decision needed is not a rule exception — DRC is 0 either way — but a
manufacturing judgement:

| option | GPIO | cost |
|---|---|---|
| **A** — accept via B at 0.0250 mm from `U3.9`'s paste | **2** | risk of a starved/open joint on `U3.9`, a 0.65 mm pitch TSSOP pin. Same-net, so no short |
| **B** — enforce the 0.100 mm mask-web floor | **1** | `XGPIO5` alone at 91.5 mm, or `XGPIO6` alone at 107.8 mm. Below the previously ruled minimum of 2 |

Option B is a scope change below the stated minimum and is not taken
unilaterally. Option A is not taken because §5 instructs a STOP on exactly this
finding.


## 17. §8 release minimisation — net phase COMPLETE

Run against the corrected candidate: every released net restored in turn, then
re-tested that `XGPIO5` and `XGPIO6` both still close, separated, with
`WAKE_ATTN_N_HDR` re-landing.

| released net | objects | restoring it |
|---|---:|---|
| `Net-(U15-CT)` | 56 | **RESTORED** |
| `XGPIO2_HDR` | 41 | **RESTORED** |
| `XGPIO3_HDR` | 29 | **RESTORED** |
| `XGPIO12_HDR` | 18 | **RESTORED** |
| `ACC_3V3_SW` | 15 | **RESTORED** |
| `I2C_SDA_EXT_HDR` | 13 | **RESTORED** |
| **`I2C_SCL_EXT_HDR`** | **12** | **load-bearing — stays released** |
| `XGPIO10_HDR` | 11 | **RESTORED** |
| `XGPIO11_HDR` | 10 | **RESTORED** |
| `XGPIO0_HDR` | 10 | **RESTORED** |
| `XGPIO13_HDR` | 9 | **RESTORED** |
| `XGPIO9_HDR` | 7 | **RESTORED** |
| `XGPIO8_HDR` | 6 | **RESTORED** |
| `XGPIO1_HDR` | 6 | **RESTORED** |
| **`WAKE_ATTN_N_HDR`** | **1** | **load-bearing — stays released** |

### B — CLEAN PRACTICAL RELEASE

> **13 objects, 19.834 mm, two nets:**
> `I2C_SCL_EXT_HDR` (12 objects, 19.834 mm) and the single
> `WAKE_ATTN_N_HDR` via.

**231 of the 244 diagnostic objects are restored — a 95 % reduction.** The
203.662 mm diagnostic release was an artefact of proving *four* XGPIO; the
two-net requirement needs almost none of it. Twelve of the ten deferred
`XGPIO*_HDR` routes, the whole `Net-(U15-CT)` run, `ACC_3V3_SW` and
`I2C_SDA_EXT_HDR` all stay on the board untouched.

This is the preferred landing set: it is contiguous per net, leaves no orphan
copper, and spends exactly one deferred function (`I2C_SCL_EXT_HDR`) plus one
active via that re-lands.

### A — 1-MINIMAL RELEASE

> **7 objects (2 vias), 15.246 mm:**
> `I2C_SCL_EXT_HDR` 6 objects / 15.246 mm, plus the `WAKE_ATTN_N_HDR` via.

Every remaining object is individually necessary — restoring any one of them
breaks the pair.

### Why B is still the release to land

A is 6 objects smaller, but it leaves **6 of `I2C_SCL_EXT_HDR`'s 12 in-window
objects on the board**, in three disconnected pieces:

```
B.Cu    (34.460, 6.580) -> (35.280, 8.348)   1.949 mm  |  a stub at the J5 end
B.Cu    (35.280, 8.348) -> (35.560, 9.250)   0.944 mm  |
In2.Cu  (48.648,11.601) -> (49.474,11.177)   0.928 mm  |  a stub around the via
In2.Cu  (49.474,11.177) -> (49.474,11.123)   0.053 mm  |  at (49.474, 11.123),
B.Cu    (49.474,11.123) -> (49.600,11.825)   0.713 mm  |  with the via itself
VIA     (49.474, 11.123)                               |  left floating
```

That is exactly the "orphan traces / floating vias / tiny isolated stubs"
§8 warns against — including a 0.053 mm fragment and a via left with copper on
both sides of it but no path anywhere. **B removes all 12 in-window objects,
i.e. the complete run, leaving no fragment at all.**

§8 says to prefer the clean practical release, and the geometry agrees: 6 extra
objects buys a release with no pathological restoration geometry.

**LANDING SET, if authorised: B — 13 objects, 19.834 mm.**

### Effect on the ledger

Only `I2C_SCL_EXT_HDR` is now spent, so the post-landing prediction changes
sharply. Instead of +17 deferred openings the board gains roughly **+1**, and
`XGPIO5` / `XGPIO6` close for −2. **Nothing may be assumed here** — the ledger
must be rebuilt from the landed board, per §16.


---

# PART 3 — LANDED

## 18. The 0.45 mm via was rejected by the board's own minimum

§2 authorised **0.45 / 0.20** for this signal via, reasoning that the 0.40 mm
drill floor is POWER-class only and the annular floor is 0.125 mm. Both of
those are correct — `/XGPIO5` resolves to `Default`, and the DRU's
`hole_size (min 0.40mm)` rule is conditioned on
`BAT_MAIN || SYS_MAIN || P3V3 || NFC_5V_PA || VBUS_CHG`.

But the constraint that bites is not in the DRU. It is in **board setup**:

```
rules.min_via_diameter            0.5      <-- 0.45 violates this
rules.min_through_hole_diameter   0.2      <-- the 0.40/0.15 fallback violates this too
rules.min_via_annular_width       0.125
```

Tested rather than argued: a 0.45 mm via was written to a scratch board and
KiCad returned

```
ERR via_diameter | Via diameter (board setup constraints min diameter 0.5000 mm;
                   actual 0.4500 mm)   Via [/XGPIO5] at (20.4, 14.1)
```

The §6 fallback of **0.40 / 0.15** fails twice over — 0.40 < 0.50 diameter and
0.15 < 0.20 drill. Neither authorised geometry can land without changing a
global minimum, and §2 forbids that.

## 19. What was landed instead — same result, no rule change

The web depends only on via **diameter**, not drill, so at the minimum legal
0.50 mm diameter the best achievable web at the original position is 0.0750 mm
— still under the floor. §4 authorises "a tiny local adjustment around this
via", and 0.050 mm of movement is enough:

| | before | landed |
|---|---|---|
| position | (20.400, 14.100) | **(20.400, 14.050)** — moved 0.050 mm |
| diameter / drill | 0.60 / 0.30 | **0.50 / 0.25** |
| annular ring | 0.150 mm | **0.125 mm** — exactly the documented floor |
| web to `U3.9` paste | 0.0250 mm | **0.1250 mm** — the *preferred* figure |

Two track endpoints were re-attached to the new via position; nothing else
moved. **No DRU rule changed, no board-setup minimum changed, no exception
taken.**

## 20. Landed geometry — measured on the real board after refill

| via | net | position | dia/drill | annular | tented | web / nearest |
|---|---|---|---|---|---|---|
| A | `XGPIO5` | (22.650, 12.350) | 0.60 / 0.30 | 0.150 | both sides | paste 0.2250 mm, foreign copper `R66.1` 0.2250 mm — **unchanged per §7** |
| B | `XGPIO5` | (20.400, 14.050) | **0.50 / 0.25** | **0.125** | both sides | **paste `U3.9` 0.1250 mm**, foreign copper `U3.8` 0.3580 mm, hole-to-hole 1.7250 mm |

Both: no via-in-pad, no paste overlap, no mask-opening merge, annulus not
exposed (tented, and the board carries `tenting front yes / back yes` with zero
per-via overrides). **GATE: PASS on both.**

`XGPIO6` carries no via-in-pad; the rejected `R57.2` geometry is absent.

## 21. Landing record

| | |
|---|---|
| release | **13 objects, 19.834 mm** — `I2C_SCL_EXT_HDR` 12 + the `WAKE_ATTN_N_HDR` via |
| added | 114 segments + 9 vias |
| `XGPIO5` | 25.775 mm, 30 seg, 3 via — **one island** |
| `XGPIO6` | 113.115 mm, 82 seg, 5 via — **one island** |
| `WAKE_ATTN_N_HDR` | 0.566 mm + 1 via — `{R66.2, J5.13}` one path, `{D7.1 DNP}` isolated as before |
| board sha256 before | `bdfd2cec77e40f5be560ccdc2ba0256547b36c9f21d0da4b6821c15070686a21` |
| board sha256 after | `aba9c46775b503411d182e76e338f829edf06b6373ae73a29cb140d7edc9d998` |
| uuid prefix | `d8c58cf6`, proven absent before the write |

Object-level preservation diff: **footprints 0, pads 0, zones 0, Edge.Cuts
12 → 12**. Segments +114 / −10, vias +9 / −3 — exactly 13 removed. Removals
touched **only** `I2C_SCL_EXT_HDR` (12) and `WAKE_ATTN_N_HDR` (1); additions
touched **only** `XGPIO6`, `XGPIO5` and `WAKE_ATTN_N_HDR`.

**DRC after refill: 0 errors, 240 warnings, warning-type delta NONE, schematic
parity 0, 215 unconnected.**

Hard locks verified one island each and unchanged: `WAKE_INT_N`,
`SX1262_RXEN`, `BOOT_N`, `+3V3`. `FAST_IO_GPIO43_HDR` unchanged at 2 islands
(fitted path + DNP `D7.3`).

## 22. Fabrication note — new critical feature

The `XGPIO5` via at **(20.400, 14.050)** is a **0.50 mm / 0.25 mm** via with a
**0.125 mm annular ring**, sitting under the `U3` TSSOP-24 body with a
**0.125 mm solder-mask web** to `U3.9`'s paste aperture.

* it must be **tented on both sides** — it inherits the board-level
  `(tenting (front yes) (back yes))`; do not add a per-via override
* the 0.125 mm web depends on **green** solder mask holding a dam at that
  width; it is at the preferred figure, not the 0.100 mm floor
* it is the **smallest via on the board** — 0.25 mm drill against 0.30 mm
  elsewhere. Confirm the fab quotes that drill without an exception
