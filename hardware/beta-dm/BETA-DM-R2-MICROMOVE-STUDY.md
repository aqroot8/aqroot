# AQROOT Beta DM — R2 micro-move study and the `BOOT_N` result

> **UPDATE — Option W was ratified and attempted. It does not land.** The
> replay reproduced exactly, and the exact analytic validation passed, but the
> **KiCad scratch gate rejected it with 11 errors**: the replacement `+3V3`
> escape violates the `P3V3` netclass rules. §7 has the full evidence and the
> corrected option set. `E6_R2_1` therefore **cannot** be removed, and the
> condition attached to its removal is not met. Nothing was landed.

**Status of the original study: STOPPED AND RETURNED FOR RULING.** The ratified R2 micro-move was
studied in full. It does **not** solve `BOOT_N`. Per the standing instruction —
*"If the micro-move does NOT solve `BOOT_N` cleanly: STOP. Do NOT activate the
two-lock fallback. Return to CTO."* — nothing was landed: `R2` has not moved,
`E6_R2_1` is untouched, no `BOOT_N` copper exists, and the two-lock fallback was
not activated.

The study did, however, find that the pass-3 option set was wrong, and that a
**strictly cheaper option exists that touches no hard lock at all**. That is
§4, and it is the reason this is a ruling request rather than a dead end.

---

## 1. The board before anything

| item | value |
|---|---|
| `R2` | `R_0603_1608Metric`, 10 k, `B.Cu`, centre (22.000, 37.500), rotation 0 |
| `R2.1` | `+3V3`, (21.175, 37.500), 0.80 × 0.95 mm |
| `R2.2` | `BOOT_N`, (22.825, 37.500), 0.80 × 0.95 mm |
| courtyard | ±1.480 × ±0.730 mm → (20.520, 36.770)–(23.480, 38.230) |
| `E6_R2_1_CLR` | F.Cu + In1 + In2 + B.Cu, (22.800, 35.500)–(23.800, 36.500) |
| `E6_R2_1_WIDTH` | B.Cu, (20.625, 35.800)–(23.450, 38.125) |
| `BOOT_N` | 4 pads — `U1.27` (24.000, 34.750), `R2.2`, `SW1.1` ×2 (2.020 / 9.980, 72.250). **Zero copper: 0 tracks, 0 vias.** |

The R2-local `+3V3` escape that any move would void: **18 segments (5.528 mm)
and 1 via** at (23.300, 36.000) — the F.Cu east run at y ≈ 35.85–36.00, the via,
and the 0.15 mm B.Cu neck into `R2.1`. It is this copper, not `R2` itself, that
carries the Tier-B `E6_R2_1` measured-clearance exception.

---

## 2. Where `R2` can legally go

Every candidate was tested against real copper: pad-to-pad, pad-to-track,
pad-to-via and pad-to-hole, at the enforced minima, with the R2-local `+3V3`
detour released (a move voids it by definition).

Swept at **0.05 mm resolution within a 2.000 mm radius**:

> **278 legal positions, confined to x 20.750 … 22.550, y 37.150 … 37.800 — an
> island 1.800 × 0.650 mm. The largest legal displacement from home is
> 1.285 mm**, at (20.750, 37.800), limited by `SX1262_DIO1` at 0.225 mm.

`R2`'s clearance at home is 0.355 mm, limited by a `CC1101_GDO0` via.

Representative candidates, with the metrics the directive asked for:

| R2 centre | ΔX / ΔY | min clr | limiting object | crtyd → R12 | crtyd → TP5 | `U1.27`↔`R2.2` | escapes pocket | legal |
|---|---|---|---|---|---|---|---|---|
| (22.000, 37.500) | 0.00 / 0.00 | 0.355 | via `CC1101_GDO0` | 1.754 | 1.620 | YES | **NO** | LEGAL |
| (22.000, 36.500) | 0.00 / −1.00 | 0.025 | via `CC1101_GDO0` | 2.675 | 1.620 | YES | NO | illegal |
| (22.000, 38.500) | 0.00 / +1.00 | −0.097 | trk `SX1262_DIO1` | 0.999 | 1.622 | YES | NO | illegal |
| (23.000, 37.500) | +1.00 / 0.00 | −0.086 | trk `SD_CS_N` | 2.399 | 2.620 | YES | NO | illegal |
| (21.000, 37.500) | −1.00 / 0.00 | 0.175 | via `CC1101_GDO0` | 1.540 | 0.620 | YES | NO | illegal |
| (22.700, 38.200) | +0.70 / +0.70 | −0.097 | trk `SX1262_DIO1` | 1.754 | 2.320 | YES | NO | illegal |
| (21.300, 36.800) | −0.70 / −0.70 | −0.300 | via `CC1101_GDO0` | 2.244 | 0.920 | YES | NO | illegal |
| (22.000, 35.500) | 0.00 / −2.00 | 0.000 | `U1.29` pad | 3.638 | 1.622 | YES | NO | illegal |
| (22.000, 39.500) | 0.00 / +2.00 | −0.079 | trk `TOUCH_RST_N` | 0.840 | 1.941 | no | NO | illegal |
| (20.500, 37.500) | −1.50 / 0.00 | −0.025 | trk `SX1262_DIO1` | 1.540 | 0.120 | YES | NO | illegal |
| (24.000, 37.500) | +2.00 / 0.00 | −0.088 | trk `SPI_A_MISO` | 3.231 | 3.620 | no | NO | illegal |

`R2` is nested inside a ring of routed signal copper — `SX1262_DIO1`,
`CC1101_GDO0`, `SD_CS_N`, `SPI_A_MISO`, `TOUCH_RST_N` — plus `U1.29`'s pad. Any
move of a millimetre or more in almost any direction is a clearance violation.

**Function is unchanged in every candidate**: 10 kΩ, `R2.1` = `+3V3`,
`R2.2` = `BOOT_N`, rotation 0, no re-pinning.

---

## 3. Why the move cannot work — the real blocker

The escape metric used in pass 3 counted **via sites inside one reserved
window**. That was too narrow, and it hid the actual shape of the problem.

Flooding `BOOT_N`'s reachable free space from `U1.27` at the enforced rules:

| state | `U1.27` reachable set |
|---|---|
| board as landed | 779 cells, `B.Cu` only, x 23.50–24.95, y 33.35–35.60 |
| R2-local `+3V3` detour released | **9 728 cells** — F.Cu x 17.50–25.60 y 30.55–38.55, In2 x 23.10–24.30 y 35.00–38.70, B.Cu x 19.60–24.95 y 33.35–38.25 |

So releasing the `+3V3` detour opens a great deal — and **`U1.27` then reaches
`R2.2` directly.** With `R2` at home and only that detour released, the
`U1.27` ↔ `R2.2` link routes in **6 segments on B.Cu, no vias, at ordinary
0.20/0.20 rules**, and `+3V3` re-joins `R2.1` in 3.373 mm with one via.

> **Corrected in §7.2:** that `+3V3` re-join is *not* at ordinary rules. `+3V3`
> carries the `P3V3` netclass, which requires 0.40 mm width on the outer layers
> and a 0.40 mm via drill; the router had used the 0.20 mm default. `E6_R2_1`
> cannot be deleted.

But that 9 728-cell region is a **sealed pocket**. `SW1.1` reaches 2 826 267
cells — effectively the whole board. The pocket and the board are separate
components, and `R2.2` is inside the pocket.

Sweeping every legal `R2` position:

> **75 legal candidates in a 3 mm radius at 0.1 mm resolution.
> 72 of them connect `U1.27` ↔ `R2.2`. Zero of them escape the pocket.**

That is the whole result. `R2` is a two-pad passive; wherever it goes inside its
1.8 × 0.65 mm legal island, it is still inside `U1.27`'s pocket, and `SW1` is
still outside it. **No R2 position solves `BOOT_N`.**

---

## 4. What actually seals the pocket — and the cheaper option set

The pocket wall was attributed by stamping each nearby object's exclusion
envelope against the pocket boundary ring (1 196 cells):

| owner | boundary cells |
|---|---|
| `/I2S_LRCLK` | 267 |
| `/SD_CS_N` | 218 |
| `/SX1262_DIO1` | 177 |
| `/CC1101_GDO0` | 134 |
| `U1` pads | 131 |
| `+3V3` | 120 |
| `/08_BUTTONS_EXPANDERS/BTN_RIGHT_N` | 73 |
| `/WAKE_INT_N` | 70 |
| `R2` pads | 63 |
| `/SPI_A_MISO` | 32 |
| `/08_BUTTONS_EXPANDERS/BTN_HOME_N` | 6 |

Then each wall net was released in turn and `U1.27` → `SW1.1` reachability
re-measured on a full-board grid:

| single release | objects | length | `U1.27` → `SW1.1` | lock status |
|---|---|---|---|---|
| `/I2S_LRCLK` | 78 seg, 8 via | 87.909 mm | **YES** | I2S — hard-locked |
| `/SD_CS_N` | 13 seg, 5 via | 142.443 mm | **YES** | SPI-A |
| `/SPI_A_MISO` | 16 seg, 5 via | 156.244 mm | **YES** | SPI-A |
| `+3V3` | 323 seg, 36 via | 623.797 mm | **YES** | power rail |
| `/WAKE_INT_N` | 15 seg, 4 via | 68.633 mm | **YES** | **not locked** |
| `/SX1262_DIO1` | 14 seg, 5 via | 148.407 mm | **YES** | **not locked** |
| `/CC1101_GDO0` | 25 seg, 7 via | 198.487 mm | **YES** | **not locked** |
| `/08_…/BTN_RIGHT_N` | 60 seg, 5 via | 114.014 mm | **YES** | **not locked** |
| `/08_…/BTN_HOME_N` | 97 seg, 8 via | 258.114 mm | **YES** | **not locked** |

**Every one of them opens it.** The pass-3 conclusion — that `BOOT_N` needs
`I2S_LRCLK` *plus* one of `SD_CS_N` or the `+3V3` R2.1 escape, a two-lock
conflict — was an artifact of looking only at the one reserved escape window.
`I2S_LRCLK` is **not required at all**.

### 4.1 Two complete, proven solutions that touch no hard lock

Each was taken end to end: release the object, complete `BOOT_N` to one island,
re-land the released net to one island, and re-join `R2.1` to the `+3V3` rail.

| option | release | `BOOT_N` | released net re-lands | `+3V3` `R2.1` re-join | result |
|---|---|---|---|---|---|
| **W** | `/WAKE_INT_N` (15 seg, 4 via, 68.633 mm) **+** the R2-local `+3V3` detour (18 seg, 1 via, 5.528 mm) | **52.445 mm, 67 seg, 5 via, one island** | 97.588 mm, 178 seg, 4 via, one island | 3.373 mm, 1 via, **ordinary rules** | **COMPLETE** |
| **G** | `/CC1101_GDO0` (25 seg, 7 via, 198.487 mm) **+** the same `+3V3` detour | 57.701 mm, 88 seg, 3 via, one island | 174.807 mm, 510 seg, 4 via, one island | 3.109 mm, 1 via, ordinary rules | **COMPLETE** |

Option **W** is much the better of the two: fewest objects released, shortest
re-land, and `WAKE_INT_N` is a low-speed interrupt line where a 28.955 mm length
increase is of no consequence.

Both options **delete** the `E6_R2_1` Tier-B measured-clearance exception rather
than re-deriving it, because the replacement `+3V3` escape routes at the
ordinary 0.20 mm / 0.20 mm. That removes the most delicate copper on the board
instead of moving it.

### 4.2 One option that needs no `+3V3` change at all — but is not yet proven

`/08_…/BTN_RIGHT_N` released **alone**, with the R2-local `+3V3` detour left
exactly as it is, opens `U1.27` → `SW1.1`, and `BOOT_N` then routes complete in
**57.905 mm, 102 segments, 3 vias, one island**. Nothing else on the board is
touched — no `+3V3`, no `E6_R2_1`, no component move, no hard lock.

`BTN_HOME_N` behaves the same way.

The catch: with `BOOT_N` landed first, `BTN_RIGHT_N` **failed to re-land** — it
needs the corridor `BOOT_N` just took. Reversed orders and via-cost variants ran
past a ten-minute bound without converging. This option is therefore **not yet
proven** and would need a proper negotiated-congestion program for the pair, of
the same kind used for the I2S trio. It is listed because if it can be closed,
it is the cleanest result available: `BOOT_N` complete with **zero** collateral
change.

Note also that `BTN_RIGHT_N`'s F.Cu run was *retired* as an `I2S_LRCLK` release
object in the pass-4 ruling. Retiring it as a release object is not the same as
locking it, so it is treated here as ordinary copper — but that reading is worth
confirming in the ruling.

---

## 5. What is being asked

`BOOT_N` is mandatory programming and recovery access and the directive says it
must complete. It can complete. The choice is which object to release:

| # | option | cost | touches a hard lock? |
|---|---|---|---|
| **W** | release `/WAKE_INT_N` + the R2-local `+3V3` escape | proven end to end; deletes `E6_R2_1` | **no** — but it does replace the `+3V3` R2.1 escape, which pass 3 listed as hard-locked. The pass-4 ruling already authorised re-deriving that copper as part of the micro-move; this asks to do the same thing **without** moving `R2`. |
| **B** | release `/08_…/BTN_RIGHT_N` alone | `BOOT_N` proven complete; the re-land is **not** proven | **no**, and no `+3V3` or `E6` change either |
| **G** | release `/CC1101_GDO0` + the `+3V3` escape | proven end to end, but 4× the released length of W | no |
| — | the ratified R2 micro-move | **does not work** — 278 legal positions, none escapes | n/a |
| — | the two-lock `I2S_LRCLK` + `SD_CS_N` / `+3V3` fallback | **not needed** — no `I2S` release is required | would have |

**Recommendation: W, with B pursued first if a short negotiated-congestion run
can close its re-land.** Either way this needs a ruling before any copper moves,
because both replace the `R2.1` `+3V3` escape or a previously-listed lock, and
the standing instruction on `BOOT_N` is to stop and return.

---

## 6. What was and was not done

Done: the full micro-move study; the pocket and wall analysis; nine
single-release reachability tests; three end-to-end release-and-re-land proofs.

Not done, deliberately: `R2` has not moved; `E6_R2_1` is unchanged; no `BOOT_N`
copper exists on the board; the two-lock fallback was not activated; no DRU rule
was changed; no component was moved.

---

## 7. Option W, ratified and attempted — and why it does not land

### 7.1 The replay reproduced exactly

Fresh scratch from the current board, releasing `/WAKE_INT_N` (15 segments,
4 vias, 68.633 mm) and the R2-local `+3V3` escape (18 segments, 1 via,
5.528 mm) — 38 removal UUIDs in total:

| net | result | length | objects | islands |
|---|---|---|---|---|
| `BOOT_N` | routed | **52.445 mm** | 67 seg, 5 via | **1** — `U1.27`, `R2.2`, both `SW1.1` halves |
| `/WAKE_INT_N` re-land | routed | 97.588 mm | 178 seg, 4 via | **1** — all five fitted pads: `R3.1`, `R66.1`, `U1.23`, `U2.1`, `U3.1` |
| `+3V3` `R2.1` re-join | routed | 3.373 mm | 10 seg, 1 via | `+3V3` island count 42 → 42, `R2.1` on the same island as before |

**WAKE function is preserved**: all five `WAKE_INT_N` pads are fitted, none
disappears, and `R66.1` — the J5 `WAKE_ATTN_N_HDR` path — stays on the single
island. The J5 ESD side is a *different* net (`WAKE_ATTN_N_HDR`, `D7`), so no
ESD-DNP branch was ever treated as required connectivity.

Exact analytic validation of all 255 new segments and 10 vias: **PASS**, 0
violations, tightest figure 0.2000 mm against a 0.200 mm limit. (Getting there
required fixing a validator defect — released *vias* were not being excluded
from the obstacle set, only released segments. The defect was over-strict, so
it produced false failures and could never have hidden a real one.)

### 7.2 The scratch gate rejected it

KiCad DRC on the scratch, zones refilled: **11 errors.** All of them on the
replacement `+3V3` escape:

| rule | violations |
|---|---|
| `P3V3 minimum width on the outer layers` — min 0.40 mm | 10 tracks at 0.20 mm |
| `POWER-class vias use the 0.40 mm drill` — min hole 0.40 mm | 1 via at 0.30 mm |

**This corrects a claim in the previous report.** That report said the `R2.1`
`+3V3` re-join routed "at ordinary rules". It did not. The router had used the
0.20 mm default width; `+3V3` carries the `P3V3` netclass, which requires
**0.40 mm on the outer layers** and a **0.40 mm via drill**. The rules were
never relaxed — the model simply was not asked the right question.

### 7.3 What the real `P3V3` rules allow at `R2.1`

Re-measured with the correct figures, releasing the same objects:

| track width | via | `R2.1` reachable set | escapes its pocket |
|---|---|---|---|
| 0.40 mm | 0.60 / 0.30 standard | 118 884 cells, reaches F.Cu | **yes** |
| 0.40 mm | 0.65 / 0.40 (the smallest legal `P3V3` via: 0.40 drill + 0.125 mm annular floor) | 1 621 cells, B.Cu only | **no** |
| 0.40 / 0.30 / 0.25 / 0.20 / 0.15 mm | 0.65 / 0.40 | 1 621 – 2 372 cells | **no, at every width** |
| any width, **no via at all** | — | B.Cu pocket contains **zero** other `+3V3` copper | **no** |

So the track width is not the problem — **the via is**. A compliant `P3V3` via
needs 0.325 mm of copper radius plus 0.200 mm of clearance; nowhere in `R2.1`'s
reachable pocket is there room. The threshold is sharp: a 0.60 mm via (radius
0.300) fits, a 0.65 mm via (radius 0.325) does not.

Measured: **the largest clearance at which a fully compliant 0.65/0.40 via
escapes `R2.1` is 0.175 mm.** That is what a replacement exception would have
to grant — against the 0.100 mm clearance plus 0.15 mm neck that `E6_R2_1`
grants today. It would be a *much weaker* exception, but it is still a new
scoped rule, and creating one is a STOP condition.

### 7.4 The two demands want the same 1 mm²

`E6_R2_1_CLR` is the square (22.800, 35.500)–(23.800, 36.500). Reserving just
that square while everything else stays released:

| state | `U1.27` reachable set | `U1.27` → `SW1.1` |
|---|---|---|
| WAKE + the `+3V3` escape released (Option W) | 2 972 215 cells | **yes** |
| the same, but `E6_R2_1_CLR` reserved | **751 cells** | no |
| WAKE released, `+3V3` escape kept | 779 cells | no |

`BOOT_N`'s only escape from `U1.27` runs **through** the exact pocket the
`+3V3` power via needs. They are mutually exclusive.

Option **G** (`/CC1101_GDO0`) fails for the same reason — it also requires the
`+3V3` escape released.

### 7.5 `BTN_HOME_N` checked, and it does not work either

`BTN_HOME_N` was not named in the ruling, and it is the only other release that
opens `U1.27` with the `+3V3` escape left intact. Measured:

| release, `+3V3` escape KEPT | `U1.27` → `SW1.1` | `U1.27` → `R2.2` | `R2.2` reachable set |
|---|---|---|---|
| `/08_…/BTN_HOME_N` | yes | **no** | 4 304 cells, sealed |
| `/08_…/BTN_RIGHT_N` | yes | yes | 2 952 612 cells |

With `BTN_HOME_N` released, `U1.27` reaches the switch but `R2.2` is sealed in
its own pocket, so `BOOT_N` still cannot be one island. **`BTN_RIGHT_N` remains
the only release that completes `BOOT_N` with the `+3V3` escape and `E6_R2_1`
untouched** — and it is ruled DO NOT PURSUE.

### 7.6 Where that leaves `BOOT_N`

| option | completes `BOOT_N`? | cost |
|---|---|---|
| **W** — `/WAKE_INT_N` + the `+3V3` escape | yes, but only with a **new scoped via-clearance exception at 0.175 mm** | replaces `E6_R2_1` with a weaker exception |
| **G** — `/CC1101_GDO0` + the `+3V3` escape | same blocker | 4× the released length of W |
| **B** — `/08_…/BTN_RIGHT_N` alone | yes, **no `+3V3` or `E6` change at all**; `BOOT_N` proven at 57.905 mm / 102 seg / 3 via, one island | its own re-land is unproven and needs a negotiated-congestion program |
| `BTN_HOME_N` alone | **no** — `R2.2` stays sealed | — |
| R2 micro-move | **no** — 278 legal positions, none escapes | — |

`E6_R2_1` is **KEPT**: the ruling's condition — *"only if ordinary-rule R2.1
+3V3 connectivity is fully proven"* — is measurably not met.

Nothing from Option W was landed. `R2` has not moved, `E6_R2_1` is unchanged,
`BOOT_N` still has zero copper, `/WAKE_INT_N` is untouched and remains one
island with all five fitted pads.
