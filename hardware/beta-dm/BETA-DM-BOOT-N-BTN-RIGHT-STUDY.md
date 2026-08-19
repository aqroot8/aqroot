# Beta-DM — `BOOT_N` final architecture study: the `BTN_RIGHT_N` single-object release

**ANALYSIS ONLY. No real-board copper was written. Nothing here is an
implementation.** Full Beta (`hardware/beta/`) is untouched; the Beta-DM board,
its DRU and its schematics are byte-identical to `7495507`.

Scope: prove or disprove Option **B** from
[`BETA-DM-R2-MICROMOVE-STUDY.md`](BETA-DM-R2-MICROMOVE-STUDY.md) §4.2 — release
`/08_BUTTONS_EXPANDERS/BTN_RIGHT_N` alone, complete `BOOT_N`, and re-land
`BTN_RIGHT_N`. That option was the cleanest available: no `+3V3` change, no
`E6_R2_1` change, no component move, no hard lock touched. Its re-land had
never been proven.

**Result: `BOOT_N` completes. The `BTN_RIGHT_N` re-land is geometrically
impossible, not solver-inconclusive.** The two demands need the same
single-file 0.651 mm aperture on `In2.Cu`, and that aperture holds exactly one
0.20 mm track.

---

## 1. Starting state, verified

| item | measured |
|---|---|
| `AQROOT` HEAD | `7495507` = `origin/master`; worktree clean (one pre-existing untracked dir, `hardware/beta/mechanical/`) |
| `git diff beta-full-reference-v1..HEAD -- hardware/beta/` | **empty** |
| Beta-DM KiCad DRC | **0 errors**, 240 warnings (138 `silk_over_copper`, 96 `silk_overlap`, 3 `silk_edge_clearance`, 2 `track_dangling`, 1 `text_height`), 223 unconnected items |
| backlight | landed — `LED_BOOST`, `LED_K`, `LED_A1..A4` all **one island** |
| global `LED_BOOST` routed clearance | **0.30 mm** (`.kicad_dru` "LED_BOOST routed clearance"), reduced only inside `E6_BL_FANOUT_CLR` / `E6_BL_KVIA_CLR` |
| `BOOT_N` | **0 tracks, 0 vias**, 3 islands (`U1.27`, `R2.2`, `SW1.1`) |
| `E6_R2_1_CLR` / `E6_R2_1_WIDTH` | **present**, unchanged — (22.800, 35.500)–(23.800, 36.500) all layers, and the B.Cu width area |
| `BTN_RIGHT_N` | **60 segments, 5 vias, 114.014 mm**, one island; F.Cu 18 / B.Cu 19 / In2 23; pads `SW5.1` ×2, `U2.16`, `R7.2` |

---

## 2. The release candidate, recovered exactly

The remembered candidate is reproduced on the current board, not taken on
trust: releasing **all 65 `BTN_RIGHT_N` objects** (60 segments + 5 vias,
114.014 mm) completes `BOOT_N` at

> **57.905 mm, 102 segments, 3 vias, one island** — identical to the figure
> recorded in the micro-move study.

`BTN_RIGHT_N`'s topology explains why it is the wall: it is a single chain
`U2.16 → F.Cu column x = 15.900 → B.Cu run y = 33.481 → In2 diagonal
x ≈ 23.2…24.7 → In2 lane south to y = 50.3 → R7.2 → B.Cu/F.Cu south → SW5.1`.
The In2 diagonal passes through `U1.27`'s escape.

### 2.1 The full-net release cannot be re-landed, and not because of `BOOT_N`

With all 65 objects released and **no `BOOT_N` copper on the board at all**,
`U2.16` sits in an **803-cell (≈ 2.0 mm²) sealed pocket**; `SW5.1` and `R7.2`
are in the 6 892 586-cell main free region. `U2.16`'s escape depends on
`BTN_RIGHT_N`'s *own* existing stub and via. Releasing the whole net therefore
destroys the connection it is supposed to re-make, before `BOOT_N` is even
considered.

The release must be minimal.

### 2.2 The 1-minimal release set

Every one of the 65 objects was tested for necessity by re-flooding the whole
board (all three routing layers, via transitions honoured) and asking whether
`U1.27`, `R2.2` and `SW1.1` remain in one free region. Greedy 1-minimisation,
far-from-`U1` first, 65 tests, 728 s:

> **14 objects, 14.814 mm** — 13 segments and 1 via, all of them the `In2.Cu`
> lane plus its `B.Cu` stub at the `R7.2` end.

Two further `In2` segments are left as a floating stub by that set, so the
release actually studied is the **16-object, 17.563 mm** clean variant:

| # | kind | layer | from | to | mm | uuid | 1-minimal |
|---|---|---|---|---|---|---|---|
| 1 | seg | `In2.Cu` | (23.150, 34.450) | (24.300, 35.600) | 1.626 | `4e17ab00-fe21-f9b5-11f5-145a95513f91` | yes |
| 2 | seg | `In2.Cu` | (24.300, 35.600) | (24.350, 35.600) | 0.050 | `4e17ab00-fc22-4dbb-ccf2-a7a84a59c909` | yes |
| 3 | seg | `In2.Cu` | (24.350, 35.600) | (24.400, 35.650) | 0.071 | `4e17ab00-cdd1-ea30-4cda-dcc69b6940c6` | yes |
| 4 | seg | `In2.Cu` | (24.400, 35.650) | (24.450, 35.650) | 0.050 | `4e17ab00-fd9f-ff4b-0614-84f0346607a5` | yes |
| 5 | seg | `In2.Cu` | (24.450, 35.650) | (24.650, 35.850) | 0.283 | `4e17ab00-aa99-4117-8627-8f16ff44fd82` | yes |
| 6 | seg | `In2.Cu` | (24.650, 35.850) | (24.650, 35.900) | 0.050 | `4e17ab00-ee7f-1155-d549-ac493495bc31` | yes |
| 7 | seg | `In2.Cu` | (24.650, 35.900) | (24.700, 35.950) | 0.071 | `4e17ab00-e31f-08fa-f588-3546bd0188b9` | yes |
| 8 | seg | `In2.Cu` | (24.700, 35.950) | (24.700, 36.000) | 0.050 | `4e17ab00-f3a3-1d57-7964-0099f8b4d412` | yes |
| 9 | seg | `In2.Cu` | (24.701, 37.398) | (24.701, 35.985) | 1.413 | `8fceb353-d16f-4f00-8f78-6c96d8c7d67e` | yes |
| 10 | seg | `In2.Cu` | (23.700, 41.276) | (24.701, 37.398) | 4.005 | `05a12258-2c6e-4f32-a2ab-d22ce67b9772` | yes |
| 11 | seg | `In2.Cu` | (23.424, 44.481) | (23.700, 41.276) | 3.217 | `7cee230c-dc90-4f38-8e58-5eed19f4a736` | yes |
| 12 | seg | `In2.Cu` | (23.253, 46.303) | (23.424, 44.481) | 1.830 | `11a6b0d3-a3e2-4c37-843e-cc358e633e68` | orphan cleanup |
| 13 | seg | `In2.Cu` | (23.253, 47.224) | (23.253, 46.303) | 0.920 | `de00b7f6-957e-4b27-adb5-4d542805cedd` | orphan cleanup |
| 14 | seg | `In2.Cu` | (22.602, 50.349) | (23.253, 47.224) | 3.192 | `a4315bca-fb2d-4df2-89bf-a3c56fe649af` | yes |
| 15 | seg | `B.Cu` | (21.866, 50.349) | (22.602, 50.349) | 0.735 | `76646ac1-5a78-4b4f-9f9b-1684cdfb16e4` | yes |
| 16 | via | — | (22.602, 50.349) 0.60/0.30 | — | — | `67dae851-4323-4483-8eb1-8d29e75af3e9` | yes |

Nothing outside `BTN_RIGHT_N` is released. No `+3V3`, no `E6_R2_1`, no I2S, no
internal I²C, no SPI-A, no SPI-B, no `WAKE_INT_N`, no `CC1101_GDO0`, no
component move.

---

## 3. `BOOT_N` routes, and it is clean

With the 16-object release:

| | |
|---|---|
| length | **54.513 mm** |
| objects | 79 segments, 6 vias |
| layers | `In2.Cu` 49, `B.Cu` 17, `F.Cu` 13 |
| islands | **1** — `U1.27`, `R2.2`, both `SW1.1` halves |
| exact analytic validation | **PASS, 0 violations** |
| tightest measured separation | **0.2000 mm** against the 0.200 mm limit — `BOOT_N` vs the `/SD_CS_N` via on `In2.Cu`, and vs `/SPI_B_MOSI` |
| RF band rules (915 / 433) | **PASS** — no B.Cu in band, no in-band via, no In2 outside an E5 corridor |
| KiCad DRC on the scratch, zones refilled | **0 errors** |
| KiCad connectivity on the scratch | `BOOT_N` **one island** |

`BOOT_N` is 3.4 mm shorter than the full-release figure because the retained
`BTN_RIGHT_N` copper steers it onto a slightly different southern lane.

The route: `U1.27` (24.000, 34.750) → `In2` north-east through the aperture →
`In2` (24.300, 36.800) → via (23.400, 36.900) → `B.Cu` → `R2.2` (22.800,
37.500); and from (24.300, 36.800) south down the `In2` lane to (23.150,
50.150) → `F.Cu` → `B.Cu` → (10.000, 72.250) `SW1.1`.

---

## 4. The re-land — every family tried

| family | order | result |
|---|---|---|
| **B** full 65-object release | `BOOT_N` then `BTN_RIGHT_N` | `BOOT_N` 57.905 mm OK; re-land **FAIL** — `U2.16` sealed in its own 803-cell pocket regardless of `BOOT_N` |
| **A1** 14-object minimal | `BOOT_N` then `BTN_RIGHT_N` | `BOOT_N` 54.762 mm / 81 seg / 6 via OK; re-land **FAIL** |
| **A2** 16-object clean | `BOOT_N` then `BTN_RIGHT_N` | `BOOT_N` 54.513 mm OK; re-land **FAIL** |
| **A2r** | `BTN_RIGHT_N` then `BOOT_N` | re-land **OK — 17.570 mm, 19 seg, 1 via, one island**; then `BOOT_N` **FAIL** (`U1.27` cannot leave its pocket) |
| **E-W1/W2/W3** held `BOOT_N` window, 3 sizes | `BTN_RIGHT_N` first, window held | re-land **FAIL in all three** — even the smallest window, (22.60, 33.00)–(25.40, 39.00), leaves `BTN_RIGHT_N` no route at all |
| **F1** `BOOT_N` barred from the shared lane south of y = 38 | `BOOT_N` first | `BOOT_N` joins `U1.27`↔`R2.2` (12.325 mm) then **FAIL** to reach `SW1.1` |
| **F2** `BTN_RIGHT_N` barred from the throat only, (23.80, 34.30)–(25.00, 36.60) | `BTN_RIGHT_N` first | re-land **FAIL** |
| **F3** `BTN_RIGHT_N` barred from the lane north of y = 42 | `BTN_RIGHT_N` first | re-land **FAIL** |
| **PathFinder** negotiated congestion, both nets ripped up and re-routed every iteration, present + history costs, via costs 1.0 and 3.0, 14 iterations each (3641 s and 3817 s) | order-free | **NOT CONVERGED, both runs** — the conflict count oscillates between 267 and 330 samples across all 14 iterations with no downward trend, while the present-cost factor rises from 1.00 to 990.46 and the `BOOT_N` route inflates from 54.513 mm to 93.873 mm. The router pays any price asked and still cannot separate the two nets. |

Both nets route *alone*. Neither order works. No held window helps. Negotiated
congestion — the tool that closed the I2S trio — does not converge. That is the
signature of a capacity conflict, not of a search failure, and the geometry
confirms it.

---

## 5. Why: one aperture, capacity one

### 5.1 A two-cell cut that severs both demands

On the full-board free graph (all three routing layers, via transitions
honoured), blocking **two `In2.Cu` cells** — (24.650, 35.900) and (24.700,
35.900) — produces:

| net | effect |
|---|---|
| `BOOT_N` | `U1.27` **CUT** from `R2.2`, **CUT** from both `SW1.1` halves |
| `BTN_RIGHT_N` | its two islands **CUT** from each other |

Two cells. No bypass on `F.Cu` or `B.Cu`, no bypass around the window —
the flood is global, so any detour would have shown up as "JOINED".

**Every legal `BOOT_N` route and every legal `BTN_RIGHT_N` re-land must pass
through the same aperture.**

### 5.2 The aperture is one track wide

Measured against real geometry, not the raster. A 0.20 mm track needs 0.300 mm
(0.10 half width + 0.20 clearance) to any foreign copper edge. Free centreline
intervals on `In2.Cu`, x ∈ [21.5, 26.5]:

| y | usable centreline band |
|---|---|
| 35.65 | 0.285 mm |
| 35.75 | 0.165 mm |
| 35.85 | 0.110 mm |
| 35.95 | 0.090 mm |
| 36.05 | 0.065 mm |
| **36.20** | **0.045 mm** ← narrowest |
| 36.35 | 0.065 mm |
| 36.50 | 0.130 mm |
| 36.65 | 0.250 mm |

The band y = 35.65 … 36.65 has **no interval anywhere wide enough for two
tracks** (0.400 mm centre-to-centre). **No 0.60/0.30 via is legal anywhere in
that band**, on any layer, so the second track cannot change layer through it
either.

### 5.3 Closed form at the narrowest cross-section, y = 36.200

| bound | object | copper edge |
|---|---|---|
| west | `/SD_CS_N` via (24.100, 36.200) ⌀0.60 — **SPI-A, hard-locked** | x = 24.400 |
| east | `/08_BUTTONS_EXPANDERS/BTN_HOME_N` `In2.Cu` run x = 25.151, w 0.20 | x = 25.051 |
| | **free gap** | **0.651 mm** |

| demand | needs | verdict |
|---|---|---|
| one 0.20 mm track at 0.20 mm clearance | w + 2c = 0.600 mm | **fits, +0.051 mm** |
| two 0.20 mm tracks at 0.20 mm clearance | 2w + 3c = 1.000 mm | **short by 0.349 mm** |

That is the whole result. `BOOT_N` fits. `BOOT_N` *and* `BTN_RIGHT_N` do not.

### 5.4 What an exception would have to grant

| track width | maximum clearance that still fits two tracks |
|---|---|
| 0.20 mm | **0.0837 mm** — below the 0.09 mm fab minimum, not manufacturable |
| 0.15 mm | 0.1170 mm — needs a width exception as well |
| 0.13 mm | 0.1303 mm — likewise |
| 0.10 mm | 0.1503 mm — likewise |

Option W's blocker is a single **0.175 mm** via-clearance exception. Every
two-track variant here is **worse than that**, and the 0.20 mm-width version is
not manufacturable at all. Pursuing an exception at this aperture is strictly
dominated by pursuing one at Option W's.

---

## 6. Button-function audit

`BTN_RIGHT_N` endpoints before and after the release, on the scratch:

| | before | after |
|---|---|---|
| segments | 60 | 45 |
| vias | 5 | 4 |
| length | 114.014 mm | 96.451 mm |
| layers | F.Cu 18 / B.Cu 19 / In2 23 | F.Cu 18 / B.Cu 18 / In2 9 |
| in-band (915/433) copper | F.Cu 4 segments, **0 vias** | F.Cu 4 segments, **0 vias** — unchanged |
| **islands (KiCad)** | **1** | **2** |
| fitted endpoints connected | `SW5.1` ×2, `U2.16`, `R7.2` | `U2.16` **separated** from `R7.2` / `SW5.1` |

`BTN_HOME_N`, `BTN_LEFT_N`, `BTN_UP_N`, `BTN_DOWN_N`, `BTN_A_N`, `BTN_B_N`:
**byte-identical, all unchanged** in segment count, via count, length, layer
mix and in-band footprint. The E2 exception set is untouched: the release is
entirely in x 21.9 … 24.7, y 33.5 … 50.3 — nowhere near either RF band.

So the release preserves the E2/RF posture perfectly and breaks the button
anyway, because it severs the net.

---

## 7. Combined scratch validation

No combined candidate exists: there is no `BTN_RIGHT_N` replacement to
validate. What was gated instead is the release plus `BOOT_N` alone, which is
the strongest state Option B can reach.

| gate | result |
|---|---|
| KiCad DRC (`--severity-error`), zones refilled in `pcbnew` | **0 errors** |
| unconnected items | 221 (base 223: `BOOT_N` −3, `BTN_RIGHT_N` +1) |
| `BOOT_N` one island | **YES** |
| `BTN_RIGHT_N` one island | **NO — 2 islands** ← **the gate fails here** |
| `+3V3` | one island, 435 items — unchanged |
| `E6_R2_1` | unchanged |
| I2S (`LRCLK`/`BCLK` 2 islands, `MIC_DIN` 1) | unchanged from base |
| SPI-A (`MOSI`/`MISO`/`SCK`/`SD_CS_N`) | one island each — unchanged |
| SPI-B (`MOSI`/`MISO`/`SCK`) | one island each — unchanged |
| internal I²C (`SDA_INT`/`SCL_INT`) | one island each — unchanged |
| `WAKE_INT_N`, `CC1101_GDO0` | one island each — unchanged |
| RF band rules | PASS |

---

## 8. Option BTN_RIGHT vs Option W

| | **Option BTN_RIGHT (B)** | **Option W** |
|---|---|---|
| released net | `/08_…/BTN_RIGHT_N` only | `/WAKE_INT_N` **+** the R2-local `+3V3` escape |
| old copper disturbed | 16 objects, **17.563 mm** (minimal); 65 objects / 114.014 mm if the whole net | 38 objects, 74.161 mm |
| replacement copper | **none exists** | 178 seg / 4 via / 97.588 mm (`WAKE_INT_N`) + 10 seg / 1 via / 3.373 mm (`+3V3`) |
| `BOOT_N` length | **54.513 mm** (57.905 mm on the full release) | 52.445 mm |
| `BOOT_N` vias | **6** (3 on the full release) | 5 |
| special rule required? | **none for `BOOT_N`**; a two-track exception at the aperture would need ≤ 0.0837 mm — **not manufacturable** | **yes** — a new scoped `P3V3` via clearance at **0.175 mm** |
| `+3V3` touched? | **NO** | YES — the R2.1 escape is replaced |
| `E6_R2_1` touched? | **NO** | YES — deleted and replaced by a weaker exception |
| hard locks touched | **0** | 0 outright, but it re-derives copper pass 3 listed as locked |
| DRC (scratch) | **0 errors** — but `BTN_RIGHT_N` left in 2 islands | 11 errors as first run; blocked on the exception |
| architecture risk | **fatal** — the button net cannot be reconnected under any ordinary rule | moderate — one new scoped exception, weaker than the one it replaces |

---

## 9. Classification of the failure, and what remains

Per the ruling's taxonomy, this is **not** "solver inconclusive". It is:

* **endpoint pocket** — for the full-net release: `U2.16` is sealed in 803 cells
  by its own released copper; and
* **no legal re-land / structural** — for every minimal release: a two-cell cut
  severs both demands, and the aperture it names is 0.651 mm wide where two
  0.20 mm tracks need 1.000 mm.

Search families that remain, none of them inside the single-object premise:

1. **Two-object release, `BTN_RIGHT_N` + `BTN_HOME_N`.** `BTN_HOME_N`'s three
   `In2` segments at x = 25.151 are the aperture's east wall; releasing them
   widens the `In2` free band at y = 35.90 from 0.10 mm to **0.70 mm**, enough
   for two tracks. Measured in this pass: `BOOT_N` still completes (54.513 mm),
   but neither order closed all three nets — `BTN_HOME_N` is a 97-segment /
   258.114 mm net and its own re-land did not converge inside the pass. This
   family is **open**, and it breaks the single-object premise.
2. **Move the `/SD_CS_N` via at (24.100, 36.200)**, the aperture's west wall.
   SPI-A is hard-locked; out of scope without a ruling.
3. **A scoped clearance/width exception at the aperture** — quantified in §5.4
   and strictly worse than Option W's.

---

## 10. Held window

The doctrine was applied literally rather than as a textual claim: the
`BOOT_N` escape window was represented in scratch as an explicit named
temporary keepout (`TMP_BOOT_N_WINDOW`) in three sizes and the `BTN_RIGHT_N`
re-land was re-run against each. All three failed, which is *why* the aperture
was then measured directly. No held-window claim survives into any
recommendation, because there is no candidate to hold a window for.

---

## 11. Preservation

| | |
|---|---|
| real Beta-DM `.kicad_pcb` | **unchanged** |
| `.kicad_dru` | **unchanged** |
| schematics | **unchanged** |
| `hardware/beta/` | **unchanged** — `git diff beta-full-reference-v1..HEAD -- hardware/beta/` empty |
| copper committed | **none** |
| copper pushed | **none** |
| scratch location | session scratchpad only, never under `hardware/` |

---

## 12. Verdict

**Option B is closed.** `BOOT_N` can be completed by releasing `BTN_RIGHT_N`
and the result is DRC-clean, but `BTN_RIGHT_N` can never be re-landed
afterwards: both nets need the same 0.651 mm `In2.Cu` aperture between the
`/SD_CS_N` via and the `BTN_HOME_N` run, and it holds one 0.20 mm track.
Buttons are a MUST-WORK function, so the release cannot be taken.

`BOOT_N` therefore still needs either Option W's 0.175 mm exception, a ruling
on a two-object release, or a ruling on moving the `/SD_CS_N` via.
