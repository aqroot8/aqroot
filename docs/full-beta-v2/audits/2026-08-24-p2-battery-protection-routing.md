# FBV2-P2-002A — Battery / protection routing attempt

**Date:** 2026-08-24 · **Task:** FBV2-P2-002A — route the battery / protection block only
**Repository HEAD at start:** `8b6e64e`
**Result: FBV2-P2-002A = FAIL.** The battery / protection block is **not** routed.
**PM-2: PLACEMENT CORRECTED, CLOSURE STILL PENDING. Overall Full Beta v2 stays 74 %.**

> **The board carries ZERO tracks and ZERO signal vias.** Twenty-seven of twenty-nine nets could
> not be routed to a DRC-clean state, so **nothing was committed as copper.** Two nets (`Q2_CS`,
> `Q3_CS`) did route cleanly and were reverted with the rest rather than committed as an
> unrepresentative fragment.
>
> **What this task did establish is the method**, and that is the thing the next task actually
> needed: an obstacle-aware router with pad-escape necking and per-net DRC gating that **refuses
> to keep anything that is not clean.** It reverted every failing net automatically. That is the
> behaviour FBV2-P2-001 lacked.

---

## 1. Preflight

| check | result |
|---|---|
| HEAD / `origin/master` | both `8b6e64e` |
| Working tree | clean but for the two long-standing untracked paths |
| In1 plane | **1 zone, 1 island, net GND** |
| Tracks / signal vias / outer pours | 0 / 0 / 0 |
| DRC baseline | **1** — the `MK1` artefact (D-227), never suppressed |
| ERC baseline | **0 errors / 27 warnings** |
| P1 regression | **PASS** |
| PM-2 corrected placement | present and verified |

---

## 2. CTO rulings recorded

**PM-2 (§2).** The FBV2-P2-001 corrective support-network placement is **APPROVED and retained**.
Status is **PLACEMENT CORRECTED, FINAL CLOSURE PENDING DRC-CLEAN ROUTING** — and since this task
did not achieve that routing, **PM-2 does not close here.**

**BAT_PROTECTED_P width (§3) — D-245, implemented.** A **per-net local override**, target
**1.50 mm**, minimum **1.20 mm**, added to `.kicad_dru` as a scoped rule and to the netclass ledger
as row **A2**. **The `BAT_MAIN` class is unchanged** — `BAT_CONNECTOR_P`, `BAT_RAW`, `BAT_MID` and
`BAT_SENSE` keep 1.00 mm / 0.60 mm, because none of them carries current over anything like the
same distance. The rule and the ledger row both carry the neckdown policy in full: shortest length
that clears the package, never a traverse, length and width documented per pad, no thermal-relief
or single-via bottleneck.

Arithmetic behind it: at ≈ 71 mm, `BAT_PROTECTED_P` is **34.9 mΩ at 1.00 mm** against **23.3 mΩ at
1.50 mm** — the whole protection-path copper falls from ≈ 50.6 to ≈ 38.9 mΩ, and the 1.5 A copper
loss from 114 to 88 mW.

---

## 3. The method — and it is the deliverable

§4 forbids MST routing, batch straight pad-to-pad routing and route-all-then-DRC. What was built
instead:

**Obstacle-aware A* on a 0.10 mm grid.** For every connection the grid is rebuilt from the real
board: every foreign pad, every track already laid, every track-forbidding rule area (including
the ESP32 antenna keep-out embedded in `U1`'s own footprint) and the board edge, **each inflated by
(clearance + track width / 2)** so that a legal path on the grid is a legal track on the board.
8-way movement with corner-cutting suppressed.

**Pad-escape necking.** A 1.00 mm `BAT_MAIN` trunk cannot land on `U18` — an MSOP-10 on 0.50 mm
pitch whose pad-to-pad gap is **0.20 mm**. Every terminal therefore gets a short neck along its
pad's own long axis out to a grid-snapped launch point clear of the package, with three fallback
directions if the preferred one is blocked by the board edge or a neighbour, and the trunk is
routed between launch points at full width. **This is why the first attempt reported "NO PATH" on
a 2.44 mm hop** — the destination pad was simply unreachable at trunk width, which is a real
property of the land pattern and not a router bug.

**Per-net DRC gating.** After each net the board is saved to its own path — so DRC sees the
project's own `.kicad_dru`, `fp-lib-table` and netclasses, which an earlier scratch-file approach
did not — the report is diffed against the baseline, and **any new violation of any class reverts
that net's tracks before the next net starts.** Violations never accumulate.

---

## 4. Routing journal

Baseline DRC excluding unconnected: **1**.

| net | result |
|---|---|
| `Q2_CS` | **ROUTED CLEAN** — 5.35 mm, 3 segments, 0.25 mm, B.Cu, 0 new DRC |
| `Q3_CS` | **ROUTED CLEAN** — 5.35 mm, 3 segments, 0.25 mm, B.Cu, 0 new DRC |
| `BAT_CONNECTOR_P`, `LTC_GATE_RC`, `LTC_OV`, `LTC_SHDN`, `LTC4368_FAULT_N`, `BAT_PROT_SHDN_CTL`, `VREC_VCC`, `VBRIDGE_TOP`, `VREF_TOP`, `N_BATDIV`, `REF_HO`, `REC_POL_OK`, `REC_AND1`, `REC_AND2`, `REC_GATE_N`, `REC_LIM_IN`, `REC_DIODE_IN` | **REVERTED — `track_dangling`** (1–2 per net) |
| `BAT_MID`, `BAT_SENSE` | **REVERTED — `track_width`** (5–6), the trunk narrowed below the class floor where the grid forced it |
| `LTC_GATE`, `N_POL`, `REF_POL`, `REC_BAT_LOW`, `REC_FAULT_B`, `LTC_UV` | **REVERTED — `shorting_items` / `tracks_crossing` / `clearance`**, from a neck laid outside the grid check |
| `BAT_RAW` | **NO PATH** `R86.2 → R89.1` |
| `BAT_PROTECTED_P` | **NO PATH** `TP15.1 → U14.2` |

**Nets routed: 2 of 29. Nets committed as copper: 0.**

### 4.1 The three defects that remain, named precisely

1. **`track_dangling`, the dominant failure.** The escape neck is laid pad → launch and the trunk
   starts at the launch cell, but the two do not register as connected. This is a **fixable
   geometry bug in the emitter**, not an electrical problem — but a dangling end is exactly the
   kind of thing that must never be committed, so every affected net was reverted.
2. **`track_width` on `BAT_MID` / `BAT_SENSE`.** The neck width is derived from the pad's short
   dimension, and on an SO-8 that falls below the `BAT_MAIN` 0.60 mm floor. **The rule is right and
   the router is wrong**: these necks need the D-245-style documented exception or a wider landing,
   not a silent narrow track on a 1.5 A net.
3. **`shorting_items` on six nets.** The neck itself is laid without consulting the obstacle grid,
   so a neck can cross a neighbouring pad even when the trunk cannot. The neck must be grid-checked
   like any other copper.

None of these is a reason to change the placement, the widths or the topology. All three are
router defects with known fixes.

---

## 5. What this means for the numbers the task asked for

Every geometric figure below is a **placement** measurement, because there is no routed copper.
They are reported as such rather than as routed lengths.

| item | value |
|---|---|
| `BAT_PROTECTED_P` routed length | **not routed** (placement span ≈ 71 mm `R75` → `U11`) |
| Width breakdown | **not routed.** Approved strategy: 1.50 mm trunk, 1.20 mm floor, documented necks |
| Layer / via count | **not routed.** Intended: one outer layer, zero vias if the traverse closes on B.Cu |
| Total high-current chain | **not routed** (placement `J4`→`R75` 30.86 mm) |
| R75 Kelvin | **not routed.** Placement: `R75.1`→`U18.9` **2.44 mm**, `R75.2`→`U18.8` **8.26 mm**, mismatch **5.82 mm** |
| `LTC_GATE` | **not routed** (placement span 29.77 mm) |
| `BAT_SENSE` | **not routed** (placement span 24.29 mm) |
| Max high-impedance span | **29.77 mm** (`LTC_GATE`), placement |
| Dead-cell network | **not routed.** Topology, values and the D10/D11 matched pair are untouched |

**B-34 is unchanged from FBV2-P2-001** and is repeated here only to correct the unit confusion §16
flagged: the copper estimate is **≈ 50.6 mΩ**, not 525 mΩ. With `F1` ≈ 25 mΩ, `Q2`+`Q3` ≈ 46 mΩ and
the BQ25185 BATFET's **115 mΩ**, the path is **≈ 355 mV / 532 mW at 1.5 A** and **≈ 414 mV / 724 mW
at 1.75 A**. **B-34: OPEN — physical validation required.** Nothing here is clearly unsafe. D-245
would take the copper term to ≈ 38.9 mΩ once the net is actually routed.

---

## 6. Validation at exit

| check | result |
|---|---|
| **DRC** | **1** — the `MK1` artefact, **not suppressed** |
| **ERC** | **0 errors / 27 warnings** |
| Unrouted | **499**, unchanged |
| Tracks / signal vias / outer pours | **0 / 0 / 0** |
| In1 plane | **1 zone, 1 island, net GND** |
| **P1 regression** | **PASS**, 0 checks failed — the FBV2-P2-001 placement is re-verified here |
| `dru_probe` | **PASS** — 65 rules, the new D-245 rule included, 0 missing references |
| `netclass_probe` / `fork_equivalence` | **PASS / PASS** |
| **Accidental out-of-scope copper** | **0** — nothing is routed |
| Frozen trees | Beta-DM, `hardware/beta/`, `hardware/beta/mechanical/` untouched |

---

## 7. Carried forward

| # | item |
|---|---|
| **PR-5** | **Fix the three router defects** — join the neck to the trunk (dangling), grid-check the neck itself (shorting), and honour the class width floor or take a documented exception on the neck (width). All three are known and local |
| **PR-6** | **`R86.2 → R89.1` and `TP15.1 → U14.2` have no path at trunk width.** Both are in the dense left-margin resistor column. Either the router needs a finer grid in that column, or those two connections need a ≤ 2 mm placement nudge — **surfaced, not taken**, per §9's rule about nudges |
| **PR-2** | `BAT_PROTECTED_P` at 1.50 mm — **now ruled and implemented as D-245**, awaiting the route |
| **PM-2** | **Placement corrected and approved; closure still pending DRC-clean routing** |
| **B-34** | OPEN — physical validation required |
