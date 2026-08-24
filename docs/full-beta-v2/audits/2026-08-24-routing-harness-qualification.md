# FBV2-P2-002B — Routing harness qualification

**Date:** 2026-08-24 · **Task:** FBV2-P2-002B — qualify the obstacle-aware router before
safety-critical routing
**Repository HEAD at start:** `8b9efba`
**Result: ROUTER HARNESS QUALIFICATION = PASS.**
**No copper was committed. The authoritative PCB is track-for-track identical to `8b9efba`.**

> **All three named router defects are fixed and proved fixed on real Full Beta v2 geometry.**
> Six of the eight qualification cases route cleanly — zero new DRC violations of any class, one
> connected copper component after a real save and reload, no foreign pad in the cluster, and the
> ratsnest falling by exactly one edge per connection. The two remaining cases are **not router
> defects**: they are a **proved land-pattern / rule conflict** on five fine-pitch pads, which is
> precisely the outcome §6 and §17 asked to be surfaced rather than papered over.
>
> **PR-5 is therefore closed as a router-implementation matter.** What replaces it is a narrower,
> harder question that only the CTO can answer: **the `BAT_MAIN` 0.60 mm floor and the D-245
> 1.20 mm floor are applied to whole nets that contain both a 1.5 A trunk and zero-current sense
> and probe taps, and five pads cannot legally accept those widths at all.**

---

## 1. Preflight

| check | result |
|---|---|
| HEAD / `origin/master` | both `8b9efba` |
| Working tree | clean but for the two long-standing untracked paths |
| Authoritative tracks / signal vias / outer pours | **0 / 0 / 0** |
| In1 plane | **1 zone, 1 island, net GND** |
| DRC baseline | **1** — the `MK1` artefact (D-227), never suppressed — plus 499 unconnected |
| ERC baseline | **0 errors / 27 warnings** (`--severity-error --severity-warning`) |
| `p1_regression` | **PASS**, 0 checks failed |
| `dru_probe` / `netclass_probe` / `fork_equivalence` | **PASS / PASS / PASS** |
| Tag `beta-v2-p2-entry-pass` | `e9c6307` → `faa0c91`, untouched |
| Beta-DM, frozen Beta, `hardware/beta/mechanical/` | untouched |

---

## 2. The project-faithful scratch environment (§3)

FBV2-P2-002A wasted a routing attempt reading a **phantom** `clearance: 73,
lib_footprint_issues: 17` offset on every net. The cause was that a `.kicad_pcb` copied on its own
into a scratch directory silently loses `.kicad_dru`, the `.kicad_pro` netclasses and
`fp-lib-table` — and DRC then measures against **KiCad defaults**, not against this project.

Every board in this task is a **complete copy of the whole KiCad project directory**, and the
harness refuses to run DRC at all unless `.kicad_dru`, `.kicad_pro`, `fp-lib-table`,
`sym-lib-table` and `libraries/` are all present next to the board.

**Required proof, and it holds exactly:**

| board | DRC histogram |
|---|---|
| authoritative `aqroot-Beta-v2.kicad_pcb` | `{solder_mask_bridge: 1, unconnected_items: 499}` |
| scratch copy, before any test copper | `{solder_mask_bridge: 1, unconnected_items: 499}` |

**Identical. Phantom DRC offset: NONE.**

### 2.1 An incidental finding about the "499 unrouted" figure

`kicad-cli pcb drc` reports **499** unconnected items. The board's own connectivity engine reports
**781** ratsnest edges on the same file:

```
pcbnew.LoadBoard(...).GetConnectivity().GetUnconnectedCount(True)  ->  781
```

The two numbers measure different things and **both are KiCad-native**; 499 is what DRC reports and
what this project's documents have quoted since FBV2-P2-000, and it is not withdrawn here. But the
**ratsnest count is the metric the harness gates on**, because it moves by exactly one edge per
routed connection and is therefore a usable per-connection connectivity assertion. Every routed
test below shows that exact delta.

---

## 3. The three defects, and what was actually wrong

### PR-5A — dangling neck / trunk join → **FIXED**

**Two distinct causes, and only one of them was a coordinate problem.**

1. **Float coordinates.** The old emitter computed launch points as `round(x/G)*G` in millimetre
   floats and then re-derived the trunk start from a grid index. The router is now **integer
   nanometres end to end**: the neck's end point and the trunk's start point are the *same integer*,
   not two floats that agree to within a rounding step. Every emitted vertex is `origin + k·G` with
   `G` an exact integer.
2. **The bigger one: the old router never checked which layer a pad was on.** It routed on `B.Cu`
   and happily started a track at the centre of an `F.Cu`-only pad. That is not a joinable track —
   it is a dangling end by construction. `escape()` now refuses a pad that is not on the routing
   layer and says so.

That second cause is not hypothetical. **`TP34.1` is an `F.Cu`-only pad on `BAT_CONNECTOR_P`, whose
other terminals (`F1.1`, and `J4.1` as a through-hole) are on `B.Cu`.** It is the only net in the
whole battery / protection block whose pads are split across faces without a through-hole pad to
bridge them. See §7.

**Proof:** `T6 LTC_OV`, previously a `track_dangling` failure, routes 15.179 mm over 9 segments with
**zero** new DRC violations, **one** connected component after save and reload, and a ratsnest delta
of exactly **−2** for its two connections.

### PR-5B — neck below rule width → **FIXED, and it exposed a real conflict**

**Policy implemented exactly as §6 required: ROUTING RULE MINIMUM WINS.** The escape width ladder
starts at the trunk width and steps down in 0.05 mm increments, and **stops at the applicable rule
minimum**. It never derives a width from the pad's short dimension. If no direction and no width at
or above the floor can leave the pad legally, the pad is classified **NO LEGAL ESCAPE** and
**nothing is emitted** — no illegal track, no silent exception.

**Proof:** `T3 BAT_MID`, previously a `track_width` failure, routes 24.860 mm over 12 segments at a
**minimum emitted width of 1.000 mm** against a 0.600 mm floor, zero new DRC, ratsnest **−3**.

**And `BAT_SENSE` did not become legal — it produced the conflict instead.** That is the correct
behaviour, and §5 records it.

### PR-5C — neck obstacle awareness → **FIXED**

The neck is now checked against the **same obstacle set as the trunk**, before it is emitted:
foreign pads (as true rotated rounded rectangles, not bounding boxes), same-layer tracks as
capsules, every drilled hole on every layer, rule areas, the board edge, the applicable clearance
and the track half-width. The check is analytic — exact segment-to-shape distance, sampled at 20 µm
with half a step subtracted so the result is a sound lower bound — rather than a grid lookup, so a
short neck gets a *stricter* test than the trunk, not a weaker one. **No exemption for being short.**

**Proof:** `T5 LTC_GATE`, previously a `shorting_items` failure, routes 66.982 mm over 29 segments
through six connections with **zero** new DRC violations, one connected component, no foreign pad in
the cluster, ratsnest **−6**.

### PR-5D — a fourth defect found during qualification: the grid guard band

Not on the original list, and it would have quietly produced illegal copper on any future net.

The A\* search proves that **grid cells** are clear. The emitted track is a **continuous segment**
between those cells and can pass up to about three-quarters of a cell closer to an obstacle than
either sampled endpoint. The first `BAT_SENSE` feasibility run duly produced:

```
Clearance violation (netclass 'BAT_MAIN' clearance 0.2000 mm; actual 0.1718 mm)
```

— a 0.028 mm shortfall on a 0.05 mm grid, exactly the predicted magnitude. Every obstacle is now
inflated by an additional **0.75 × grid** guard band, so a path the search proves is a track DRC
accepts. This is §9's "grid conversion may never create post-search geometry that violates the path
the search actually proved", enforced rather than assumed.

**Cost of the fix:** `R86.2 → R89.1` no longer fits at 0.05 mm and now requires the local **0.025 mm**
dense grid. That is the honest price of correctness, and it is why §9's fine grid exists.

---

## 4. Qualification test set (§11, §15, §16)

Every test: fresh project-faithful scratch copy → emit **only** that net → save → reload → DRC in
project context → diff against the scratch baseline → KiCad-native connectivity assertion.

| # | test | result | length | seg | grid | min width | new DRC | components | foreign | ratsnest |
|---|---|---|---|---|---|---|---|---|---|---|
| T1 | `Q2_CS` (was PASS) | **PASS** | 5.500 mm | 3 | 0.05 | 0.250 | none | 1 | none | −1 |
| T2 | `Q3_CS` (was PASS) | **PASS** | 5.500 mm | 3 | 0.05 | 0.250 | none | 1 | none | −1 |
| T3 | `BAT_MID` (was `track_width`) | **PASS** | 24.860 mm | 12 | 0.05 | 1.000 | none | 1 | none | −3 |
| T4 | `BAT_SENSE` (was `track_width`) | **CONFLICT** | — | — | — | — | — | — | — | — |
| T5 | `LTC_GATE` (was `shorting_items`) | **PASS** | 66.982 mm | 29 | 0.05 | 0.200 | none | 1 | none | −6 |
| T6 | `LTC_OV` (was `track_dangling`) | **PASS** | 15.179 mm | 9 | 0.05 | 0.200 | none | 1 | none | −2 |
| T7 | `BAT_RAW` `R86.2→R89.1` (was NO PATH) | **PASS** | 45.274 mm | 11 | **0.025** | 1.000 | none | 1 | none | −1 |
| T8 | `BAT_PROTECTED_P` `TP15.1→U14.2` (was NO PATH) | **CONFLICT** | — | — | — | — | — | — | — | — |

**Six of eight route clean. Zero new electrical shorts across every test in this task. Zero foreign
pads joined any routed cluster. Connectivity after save and reload: correct in every routed case.**

T4 and T8 are the two conflicts, and §5 proves they are not the router's fault.

---

## 5. The real conflict: five pads cannot legally accept the rule width (§6, §17, §23)

Each pad below was bisected to 5 µm resolution against the project's own clearances, over eight
launch directions and nine escape lengths, using the same code path that emits real copper.

| pad | package | pad size | applicable floor | widest legal escape | shortfall | limited by |
|---|---|---|---|---|---|---|
| `U18.9` | MSOP-10, 0.50 mm pitch | 1.500 × 0.350 mm | **0.600 mm** `BAT_MAIN` | **0.245 mm** | 0.355 mm | `U18.8` / `U18.10` at 0.325 mm |
| `U18.8` | MSOP-10, 0.50 mm pitch | 1.500 × 0.350 mm | **1.200 mm** D-245 | **0.245 mm** | 0.955 mm | `U18.7` / `U18.9` at 0.325 mm |
| `U14.2` | T822, 0.50 mm pitch | 0.700 × 0.300 mm | **1.200 mm** D-245 | **0.295 mm** | 0.905 mm | `U14.1` at 0.350 mm, board edge |
| `U14.3` | T822, 0.50 mm pitch | 0.700 × 0.300 mm | **1.200 mm** D-245 | **0.295 mm** | 0.905 mm | `U14.4` at 0.350 mm, board edge |
| `U11.2` | WSON-10, 0.40 mm pitch | 0.750 × 0.200 mm | **1.200 mm** D-245 | **0.195 mm** | 1.005 mm | `U11.1` / `U11.3` at 0.300 mm |

**The arithmetic is closed-form and matches the measurement to the bisection step.** For `U18` on
0.50 mm pitch with 0.35 mm pads, the neighbouring pad edge is 0.5 − 0.175 = **0.325 mm** from the
centre line; with the 0.20 mm netclass pad clearance the track half-width can be at most 0.125 mm,
so **0.25 mm** is the widest track that can leave the pad. Measured: 0.245 mm. `U14` gives 0.30 mm;
measured 0.295 mm. `U11` gives 0.20 mm; measured 0.195 mm.

Every other terminal on both nets clears its floor comfortably — `R75.1`/`R75.2` at 1.995 mm,
`Q3.5` at 1.995 mm, `Q3.6` at 1.535 mm, `TP15.1` at 1.995 mm, `D9.1` at 1.995 mm, `TP20.1` at
1.995 mm.

### 5.1 What this actually is

**It is not a router bug, and it is not a placement bug.** It is a **rule-scoping** problem:

> `BAT_MAIN`'s 0.60 mm floor and D-245's 1.20 mm floor are written as **whole-net** constraints.
> But `BAT_SENSE` and `BAT_PROTECTED_P` each contain **two electrically different things**: a
> current-carrying trunk that genuinely needs the width, and **zero-current sense and probe taps**
> that cannot physically have it.

`BAT_SENSE` is the LTC4368's **Kelvin sense line** — it carries microamps into a high-impedance
input, and the 0.60 mm floor exists for the 1.5 A trunk, not for it. `BAT_PROTECTED_P` carries the
full pack current from `R75` to `U11`, but it *also* feeds the MAX17048 fuel gauge's sense input
(`U14.2`/`U14.3`) and a test point (`TP15.1`), neither of which carries current at all.

D-245's own text already anticipates this — it carries a four-condition neckdown policy in the rule
comment — but **the rule body has no neck exception in it**, so DRC enforces 1.20 mm on every
segment of the net including the fuel-gauge tap. As written, **D-245 makes `BAT_PROTECTED_P`
unroutable.**

**This is surfaced, not fixed.** §6 is explicit: *do not invent a rule exception in this task*, and
§17: *do not hide it by weakening rules*. Nothing in `.kicad_dru` was changed.

---

## 6. `BAT_PROTECTED_P` 1.50 mm feasibility (§14)

Measured on scratch, each hop on its own fresh board so an earlier hop's copper cannot mask a later
one, then emitted end-to-end and DRC'd as a chain.

### 6.1 Per-hop corridor widths

| hop | widest legal width | length at that width |
|---|---|---|
| `R75.2 → U18.8` | **1.50 mm** | 15.137 mm |
| `U18.8 → D9.1` | **1.50 mm** | 14.118 mm |
| `D9.1 → C25.1` | **1.50 mm** | 56.020 mm |
| `C25.1 → C36.1` | 1.20 mm | 80.61 mm |
| `C36.1 → C58.1` | **1.50 mm** | 10.78 mm |
| `C58.1 → U11.2` | 0.60 mm | 16.95 mm |
| `D9.1 → U11.2` direct | 0.60 mm | 69.75 mm |
| `C25.1 → U11.2` direct | 0.60 mm | 20.75 mm |
| `D9.1 → TP15.1` | **1.50 mm** | 16.11 mm |
| `TP15.1 → U14.2` | 0.20 mm | 8.82 mm |
| `U14.2 → U14.3` | 0.30 mm | 2.31 mm |

### 6.2 The demonstrated 1.50 mm traverse

Emitted as one chain, saved, reloaded and DRC'd:

| item | value |
|---|---|
| Chain | `R75.2 → U18.8 → D9.1 → C25.1` |
| **Legal route at 1.50 mm** | **YES** |
| Length | **85.274 mm** |
| Segments | 22 |
| Layer | **B.Cu**, single outer layer |
| **Vias** | **0** |
| Widest segment | 1.500 mm |
| Narrowest segment | **0.245 mm** — the two `U18.8` escapes only |
| New DRC | **2 × `track_width`**, both naming rule *"BAT_PROTECTED_P trunk width - local override, D-245"*, both at that 0.245 mm escape. **Nothing else. Nothing hidden.** |
| Connectivity after save/reload | **1 component, 0 foreign pads, ratsnest −3** |
| Shorts / crossings | **0 / 0** |

**So the answer to §14 is: the trunk is feasible at 1.50 mm; the terminations are not.** Past
`C25.1` the charger cluster caps the trunk at **0.60 mm**, and `U11.2`'s own WSON-10 land pattern
caps it at **0.195 mm**.

### 6.3 An honest correction to D-245's arithmetic

D-245 computed its benefit from the **71 mm placement span** and assumed a uniform 1.50 mm run. The
**measured** route is **85.3 mm** — 20 % longer, because copper has to go around things — plus two
mandatory `U18.8` escape necks of 1.95 mm each at 0.245 mm.

At 0.491 mΩ/square for 1 oz outer copper:

| term | value |
|---|---|
| 85.274 mm at 1.50 mm | 56.85 squares → **27.9 mΩ** |
| 2 × 1.95 mm at 0.245 mm (in series through `U18.8`) | 15.9 squares → **7.8 mΩ** |
| **`BAT_PROTECTED_P` as actually routable** | **≈ 35.7 mΩ** |
| same route at 1.00 mm | 85.3 squares → ≈ 41.9 mΩ, + necks |

**D-245 still helps, but by about half what it promised: roughly 6 mΩ on the path rather than the
predicted 11.7 mΩ**, because the routed length is longer than the placement span and because the
`U18` neck is unavoidable. **This does not argue against D-245** — it argues that the ruling on the
neck exception should put a **bounded length and a stated resistance budget** on the neck rather
than leaving it open, since 7.8 mΩ of the 35.7 mΩ total sits in 3.9 mm of copper.

---

## 7. `R86 / R89` (§12) and `TP15 / U14` (§13)

### `R86.2 → R89.1` — **LEGAL ROUTE EXISTS. NO PLACEMENT MOVE PROPOSED.**

| width | result |
|---|---|
| 1.00 mm (`BAT_MAIN` target) | **routes**, 45.274 mm, requires the local **0.025 mm** grid |
| 0.60 mm (`BAT_MAIN` floor) | routes, **16.848 mm** |

§12 is explicit: *if a legal route exists, no placement move.* One exists. **`R86` and `R89` are not
moved and no move is proposed**, and the ≤ 2.0 mm allowance was not spent.

It is worth recording that the 1.00 mm route is a **45 mm detour for a 5.8 mm gap** — the direct
corridor down the left-margin resistor column is genuinely too narrow for 1.00 mm — whereas the same
connection at the class floor of 0.60 mm is 16.8 mm. On a 1.5 A net that is a real trade
(45.3 mm at 1.00 mm ≈ 22.2 mΩ against 16.8 mm at 0.60 mm ≈ 13.8 mΩ), and **the shorter, narrower
route is the better one on both counts.** That is a routing decision for FBV2-P2-002C, recorded here
rather than taken.

### `TP15.1 → U14.2` — **LEGAL CORRIDOR EXISTS AT 0.20 mm. TP15 IS NOT MOVED.**

The connection is **not** blocked by geometry and **not** blocked by where `TP15` sits. It routes in
**8.82 mm at 0.20 mm**, and `U14.2 → U14.3` routes in 2.31 mm at 0.30 mm. What blocks it is D-245's
whole-net 1.20 mm floor landing on a fuel-gauge sense tap.

Moving `TP15` would not change that by one micron, so **no `TP15` relocation is proposed** and
**`U14` was not moved** (§13-C). The fix is a ruling on rule scope, not a placement change.

---

## 8. Grid policy actually required (§9, §17)

| case | grid required |
|---|---|
| Everything except one connection | **0.05 mm** |
| `R86.2 → R89.1` at 1.00 mm | **0.025 mm**, local dense box only |
| `D9.1 → C25.1` at 1.50 mm | **0.025 mm**, local dense box only |

The board is **never** searched globally at 0.025 mm. The router tries 0.05 mm first and falls back
per connection, which is exactly §9's policy.

For windows above ~400 000 cells an exhaustive A\* over eight directional states per cell is
hundreds of millions of Python-level states, so the search switches to a **vectorised numpy
wavefront** plus **line-of-sight smoothing**, where every straightened segment is re-tested against
the same blocked grid. Below that threshold the exact A\* with a bend penalty is used unchanged.
The 56 mm `D9.1 → C25.1` hop at 0.025 mm takes 36 s that way; the same search as plain A\* did not
terminate.

---

## 9. Opportunity and simplification scan (§19)

**No native installed routing mechanism exists in this environment.**

| candidate | finding |
|---|---|
| `kicad-cli pcb` | subcommands are `drc, export, import, render, upgrade`. **No routing subcommand.** |
| `pcbnew` Python (KiCad 10.0.3, bundled) | the only router-adjacent symbol exposed is the constant `ROUTER_TRANSIENT`. **The PNS push-and-shove engine is not scriptable.** |
| KiCad IPC API (`kipy`) | **not installed**, and it does not expose the router in any case |
| Freerouting | **not installed.** A Java 17 runtime is present, but §19 forbids installing software. It would also be the wrong tool: it round-trips through Specctra DSN, which carries netclass width and clearance but **not** custom `.kicad_dru` rules — so D-245, the `BAT_MAIN` outer-layer policy and the rule areas would all be invisible to it |
| any other installed autorouter | none found |

**Recommendation: keep the qualified A\* / wavefront harness.** It is roughly 600 lines, it reads
the project's own rules, and it is now covered by a regression test. Nothing simpler is available
that could honour this board's rule set.

---

## 10. Regression test (§18)

**`hardware/beta-v2/checks/router_regression.py`** — run with KiCad's bundled Python. It builds its
own throwaway project-faithful workspace and removes it afterwards. Six guards:

| guard | catches |
|---|---|
| **G1** | a scratch project missing its rule context, and any drift between the scratch and authoritative baseline DRC histograms |
| **G2** | neck / trunk disconnection, judged by KiCad connectivity after a real save and reload |
| **G3** | any emitted segment below the applicable rule floor |
| **G4** | neck or trunk collision — any new DRC violation of any class |
| **G5** | a foreign-net pad joining the routed cluster |
| **G6** | an endpoint not actually connected — the ratsnest must fall by exactly one edge per connection |

It also **pins the five proved land-pattern conflicts by their exact widest-legal-escape widths**.
If a rule is relaxed, or a part is moved so one of them becomes routable, or a new pad joins the
list, the test fails and asks for a fresh ruling instead of letting the change through unnoticed.

**Current result: ALL CHECKS PASS** — 22 assertions.

The router itself is committed alongside it as **`hardware/beta-v2/checks/qrouter.py`**, so the test
and the tool cannot drift apart.

---

## 11. Authoritative validation at exit (§4, §20)

| check | result |
|---|---|
| `aqroot-Beta-v2.kicad_pcb` vs `8b9efba` | **byte-identical**, `git diff` empty |
| Tracks / signal vias | **0 / 0** |
| Outer pours | **0** |
| In1 plane | **1 zone, 1 island, net GND** |
| DRC | **1** — the `MK1` artefact, **not suppressed** — plus 499 unconnected. Unchanged |
| ERC | **0 errors / 27 warnings.** Unchanged |
| `p1_regression` | **PASS**, 0 checks failed |
| `dru_probe` | **PASS** — 65 rules, 0 missing references, 57 patterns all matching |
| `netclass_probe` / `fork_equivalence` | **PASS / PASS** |
| Authoritative placement | **unchanged.** PM-2 placement untouched |
| Frozen trees | Beta-DM, `hardware/beta/`, `hardware/beta/mechanical/` untouched |

---

## 12. Open items

| # | item |
|---|---|
| **PR-5** | **CLOSED as a router-implementation matter.** All three named defects fixed and proved fixed; a fourth (grid guard band) found and fixed during qualification |
| **PR-6** | **CLOSED.** `R86.2 → R89.1` routes legally at 1.00 mm; `TP15.1 → U14.2` routes legally at 0.20 mm. **Neither needs a placement move**, and none was taken |
| **PR-7** | **NEW, AND IT NEEDS A CTO RULING.** `BAT_MAIN`'s 0.60 mm floor and D-245's 1.20 mm floor are whole-net constraints on nets that contain zero-current sense and probe taps, and **five pads — `U18.8`, `U18.9`, `U14.2`, `U14.3`, `U11.2` — cannot legally accept those widths at all** (widest legal escape 0.195–0.295 mm). As written, **D-245 makes `BAT_PROTECTED_P` unroutable.** The shape of the answer is a bounded, documented escape exception and/or a trunk-versus-tap split, but that is the CTO's call and no rule was touched here |
| **PR-8** | **NEW.** **`TP34.1` is an `F.Cu`-only pad on the otherwise-`B.Cu` net `BAT_CONNECTOR_P`.** It needs a via and an `F.Cu` stub, or the test point flipped to `B.Cu`. It is the only face-split net in the battery / protection block. Minor, but it is a real board issue and it caused part of the old dangling failure |
| **PR-9** | **NEW, informational.** `R86.2 → R89.1` is a 45.3 mm detour at 1.00 mm against 16.8 mm at the 0.60 mm class floor — **shorter *and* lower-resistance at the narrower width.** A routing decision for the next task |
| **PR-10** | **NEW.** D-245's benefit is about **half** what its arithmetic predicted: the measured 1.50 mm traverse is 85.3 mm not 71 mm, and the mandatory `U18.8` neck adds ≈ 7.8 mΩ in 3.9 mm of copper. The net still gains ≈ 6 mΩ, not ≈ 11.7 mΩ. Feeds directly into the PR-7 ruling |
| **PR-2** | `BAT_PROTECTED_P` at 1.50 mm — **feasibility now demonstrated** for the traverse; blocked at the terminations pending PR-7 |
| **PM-2** | **Placement corrected and approved; closure still pending DRC-clean routing.** Unchanged by this task |
| **B-34** | **OPEN — physical validation required.** Unchanged |
| **PR-4** | F.Cu / B.Cu ground pours and perimeter stitching remain the **last** step of FBV2-P2 |

---

## 13. What was NOT done

**No copper was committed to the authoritative PCB** — it is byte-identical to `8b9efba`, zero
tracks, zero signal vias. **No `.kicad_dru` rule was added, removed, relaxed or scoped.** **No
netclass changed.** **No placement moved** — not `R86`, not `R89`, not `TP15`, and certainly not
`U14` or any other IC. **PM-2 placement untouched.** **The `MK1` artefact was not suppressed.** **No
converters, USB, NFC, SPI or I²C were routed.** **No percentage moved: PCB routing stays 0 %,
overall stays 74 %.** Beta-DM, the frozen Beta tree and `hardware/beta/mechanical/` untouched.
