# FBV2-P2-003J — D-282: the shared western-corridor BAT_PROTECTED_P bridge is a TOPOLOGY/CAPACITY wall, and 003J LOCALISES it — the 003I-proposed route-only fix (relocate the `LTC_GATE`/`BAT_RAW` corridor TAP via drops out of the box, candidate b) is MEASURED INSUFFICIENT, because the wall is the WHOLE western through-via + control-copper field, not the taps; the only ≥1.20 mm F.Cu path that exists is a ~48 mm SOUTHERN cross-board detour that caps at ≤1.30 mm, not the D-275 ≥1.50 mm corridor bridge; no authoritative promotion; D-275 and D-277..D-280 preserved; the remaining viable candidate (a disjoint sub-box reserved in the sparse window / co-scheduled joint reservation) needs a parent-supervised full run

**Date:** 2026-08-28 · **Task:** FBV2-P2-003J · **Starting HEAD:** `b97718b`
**Verdict:** **MEASURED CAPACITY RESULT — no route-only via relocation of the
western corridor tap vias yields a viable ≥1.20 mm F.Cu western-corridor bridge.
On the committed dense 003H board (bridge OFF, the clean 71-connection routed
end-state), after the exact D-275 cardinality-1 `BAT_PROT_SHDN_CTL` vacate + 4× R75.2
entry array, the via-AWARE ≥1.20 mm traverse (D-269 0.30 mm trunk-to-via clearance)
is NO_PATH to every BAT_PROTECTED_P landing — and REMOVING the 9 corridor
`LTC_GATE`/`BAT_RAW` TAP vias from the obstacle model (simulating a route-target /
staging relocation OUT of the box — candidate b) does NOT reopen it, to the near
D9.1 landing OR to the far node. The taps are not the lever; the ~50-via western
through-via field is. Even COPPER-ONLY (no via clearance at all) there is NO_PATH
at the D-275 target width 1.50 mm to any landing, and the single ≥1.20 mm
copper-only path that exists is a ~48 mm cross-board SOUTHERN detour to the far
node (path max-y ≈ 78.8 mm, well south of the corridor y<75) that caps at ≤1.30 mm
— NOT the western-corridor bridge. Candidate (b) is refuted and candidate (d)
[early / reserved bridge] is the 003I FAIL. The remaining viable directions —
(c) a disjoint bridge sub-box reserved in the sparse window with the whole western
block forced into the complement, or a placement spread of the LTC4368 block
(owner/mechanical-adjacent, the fallback) — change CAPACITY, cannot be proven by a
bounded probe, and need a parent-supervised full run. This is engineering, CTO
scope, NOT an OWNER decision. No authoritative copper, no placement ECO, no rule
relaxed; the 0.200 mm clearance and 0.25 mm hole-to-hole floors are ENFORCED. The
authoritative PCB stays 0-track/0-via; D-275 + D-277..D-280 are preserved. NO
routing progress earned — a measured refinement of a FAIL earns knowledge, not
readiness.**

003I (D-281) measured that re-timing the proven D-275 bridge EARLY lays it but then
breaks the current-carrying corridor users downstream (`GND` 0.0726 mm, `BAT_MAIN`
0.125 mm clearance, `BAT_RAW` NO_VIA_SITE), and deferred the topology/capacity fix
to 003J with four candidate directions. 003J measures those candidates cheaply and
in bounded order, and records which is the lever.

---

## 1. Premise — one corridor, two mutually-exclusive high-current users

The D-281 framing: the tight western corridor `R75.2 (2.8,68) → D9.1 (11.35,72.5)`
must carry BOTH the ≥1.20 mm F.Cu BAT_PROTECTED_P bridge traverse AND the western
routing (the LTC4368 protection block — `BAT_RAW` divider + `LTC_GATE`/`SHDN`/`OV`/
`UV`/`FAULT` control + `N_POL`/`REF_POL` sense). Route order decides only WHICH
high-current user fails. 003I's leading hypothesis (candidate b) was that the "+4
`LTC_GATE`/`BAT_RAW`-tap vias" that make the dense corridor 15-deep (vs the
proven-sparse 11) are the choke, and relocating those tap via drops out of the box
would let the bridge own the corridor.

003J measures that hypothesis directly, plus the region's total capacity.

---

## 2. Method — cheap, in-memory, read-only (`bridge_probe_003j.py`)

On the committed dense 003H board (`w/FIX003H3`, the D-279/D-280 full run reproduced
at `phaseA_003h_fix.json`: 71 connections, `bridge_eco null`, DRC == baseline). The
board is COPIED to scratch before any mutation; the exact D-275 mechanism is
reconstructed on it — `BR.vacate` (cardinality-1 `BAT_PROT_SHDN_CTL` → In3, 9 F.Cu
tracks moved) + `BR.scan_entry_sites` (4× 0.80/0.40 POFV entry array on R75.2's pad)
— and a single QBoard is built. Then the bridge's own high-current traverse rule
(`route_traverse` grid+search, ≥W F.Cu, `CP`/`CTW` = 0.20/0.30 mm) is run **read-only**
(no track emission) against candidate landings, with an arbitrary SUBSET of the
board's 56 through-vias modelled as obstacles (all-layer SEG copper + hole, exactly
`BR.inject_vias`' D-269 0.30 mm-clearance model). All primitives/constants are
single-sourced VERBATIM from `bridge_route_003c` (D-275). Landings: the NEAR
west-cluster pad `D9.1` (11.35,72.5) and the FAR `NODE_AIM` (42.4,76.4) → the node's
existing 1.00 mm B.Cu trunk at (40.67,70.71).

Cheap: a handful of bounded traverse searches, no full route, no board copies per
query.

---

## 3. The measurements

`w/FIX003H3`: 56 board vias, 15 in the corridor box, of which **9** are the
`LTC_GATE`/`BAT_RAW` taps `(5.75,70.05) (5.85,71.65) (7.05,66.0) (7.20,71.90)
(7.25,74.45) (7.40,67.80) (7.75,72.45) (8.00,74.70) (8.05,67.80)`.

| clause | model | landing | width | result |
|---|---|---|---|---|
| **A** baseline (confirms D-281) | via-AWARE, all 56 vias | D9.1 near | 1.20 mm | **NO_PATH** |
| **B** candidate (b) | taps-OUT (9 removed) | D9.1 near | 1.20 mm | **NO_PATH** |
| **B** candidate (b) | taps-OUT (9 removed) | node far | 1.20 mm | **NO_PATH** |
| **C** saturation | copper-only (0 vias) | node far | **1.50 mm** | **NO_PATH** |
| **C** saturation | copper-only (0 vias) | D9.1 near | 1.20 mm | **NO_PATH** |
| **C** the only path | copper-only (0 vias) | node far | 1.20 mm | PATH — **mm=47.5, ymax=78.8** |

**A** reproduces D-281: the via-aware ≥1.20 mm bridge does not fit end-of-run.

**B is the decisive new result — candidate (b) is REFUTED.** Removing the 9 corridor
tap vias from the obstacle model does NOT reopen the via-aware ≥1.20 mm traverse to
either landing. The remaining ~47 through-vias (the control field: `LTC_SHDN`,
`LTC_OV`, `LTC_UV`, `N_POL`, `REF_POL`, `LTC4368_FAULT_N`, `BAT_SENSE`, … each a
THROUGH-via whose barrel physically occupies all layers and gets the D-269 0.30 mm
trunk clearance) still wall the F.Cu traverse. The wall is the WHOLE western
through-via field, not the taps. A leave-one-class-out sweep (recorded in the probe
transcript) confirms the copper-only node path is pinned by MULTIPLE classes — the
only single class whose removal reopens even the 1.20 mm detour is the 2-via
`LTC_GATE_RC` RC-filter, and only because those 2 vias sit on the single southern
detour thread (see C), not because they are the corridor choke.

**C: the region is SATURATED at the bridge's target width, and the one path that
exists is a DETOUR, not a corridor bridge.** Even copper-only (no via clearance),
there is NO_PATH at 1.50 mm (the D-275 target) to any landing, and NO_PATH at
1.20 mm to the near D9.1 landing. The single copper-only ≥1.20 mm path runs to the
FAR node and is a ~48 mm cross-board SOUTHERN detour — it leaves the corridor south
(path max-y ≈ 78.8 mm ≫ the corridor y<75), threads under the LTC block, and runs
east to (40.67,70.71) — and it caps at ≤1.30 mm (NO_PATH at 1.40/1.50 mm; also
NO_PATH with the 9 taps ALSO removed). This is the same 48.9 mm / 1.30 mm path
`bridge_probe_003i` clause B already reached; 003J characterises it precisely: it is
NOT the D-275 ≥1.50 mm western-corridor bridge but a long, low-margin cross-board
lane that would multiply the trunk length/resistance (B-34) and does not honour the
D-275 mechanism.

---

## 4. Conclusion — the lever is CAPACITY, and it is not a via-relocation

The corridor cannot host both a viable ≥1.20 mm F.Cu bridge and the western routing
by any END-OF-RUN or via-RELOCATION means:

- **candidate (b)** — relocate the `LTC_GATE`/`BAT_RAW` tap via drops out of the box
  — **MEASURED INSUFFICIENT** (§3B): removing them opens nothing, because the wall
  is the ~50-via control+power field, not the corridor taps.
- **candidate (d)** — a bridge laid first / reserved in the corridor — is the 003I
  EARLY FAIL: the bridge then takes the space the taps + `GND`/`BAT_MAIN` need.
- **candidate (a)** — widen or add a western lane — needs board space (R75.2 sits
  at x=2.8, ~2.8 mm from the west edge) and is an envelope change (OWNER) if it grows
  the outline; it is NOT a route-only change.
- **candidate (c)** — re-plan the landing/trunk into a DISJOINT sub-box, reserved in
  the sparse window, with the whole western block forced to route in the complement
  — is the one remaining ROUTE-scope direction that could work. It changes CAPACITY
  (a co-scheduled joint reservation), cannot be proven by a bounded probe (it needs
  the full driver to re-route the western block around the reserved bridge lane and
  then to pass the Phase-A DRC gate), and its risk is precisely the 003I symmetry —
  the bridge must take a sub-box the `GND`/`BAT_MAIN`/`BAT_RAW` users do NOT need.

So the smallest sufficient change is NOT a tap-via relocation. It is either a
co-scheduled disjoint-sub-box reservation (candidate c/d, engineering/CTO scope,
decided by a supervised full run) or — if that is exhausted — a placement spread of
the LTC4368 block (owner/mechanical-adjacent, the fallback). **No OWNER decision is
forced yet**: candidate (c) is unexhausted route-scope work.

---

## 5. Suites, cleanliness, no false promotion

**No incomplete result masquerades as evidence.** 003J ran no full route and
promoted nothing. The probe copies the board to scratch (`w/PROBE003J`) before the
in-memory vacate; no committed artifact is mutated; `phaseA_journal.json` is
untouched (the driver was never invoked). No `phaseA_003j_fix.json` exists claiming a
clean/absorbed end-state (`bridge_probe_003j` clause E guards this).

**The authoritative PCB is untouched:** `pcbnew` load of
`hardware/beta-v2/kicad/aqroot-beta-v2/aqroot-Beta-v2.kicad_pcb` reads **0 signal
tracks, 0 signal vias** (probe clause E). No KiCad source mutated, no placement ECO,
no rule relaxed — the 0.200 mm clearance and 0.25 mm hole-to-hole floors are
ENFORCED.

**Suites (all PASS, no long route re-run):**

- `bridge_probe_003j` — NEW, the standing measured-capacity record. Clause A
  (baseline NO_PATH, confirms D-281), clause B (candidate b refuted — taps-out
  NO_PATH near+node), clause C (region saturated at 1.50 mm; the only 1.20 mm path
  is a 47.5 mm / ymax 78.8 southern detour), clause D (D-275 invariant reused,
  cardinality-1 control vacate), clause E (no false promotion, authoritative 0/0).
  PASS.
- `bridge_probe_003i` — the D-281 measured-FAIL record, intact. PASS.
- `router_regression` — ALL CHECKS G1–G11 (D-280 off). PASS.
- `bridge_probe_003c` — 003C/D-275 held fixed. PASS.
- `bridge_probe_003d` — 003D end-of-run abort preserved. PASS.
- `u19_escape_probe_003e` (D-277), `003f` (D-278), `003g` (D-279), `003h` (D-280) —
  all intact. PASS.

**Committed artifacts:** `bridge_probe_003j.py` (the standing record), this audit,
the CTO_DECISIONS D-282 row, the CHANGELOG entry, the PROGRESS entry. No driver
change (candidate b is refuted, not implemented; candidate c machinery is the next
task, to be built once the CTO approves the direction — committing a large inert
unproven reservation now would add risk with no measured backing).

**Nothing moved and nothing relaxed:** D9, U18, R75–R83, Q3, shunt, FETs, C58, U19,
D10 and the whole R84–R96/Q5–Q9 field frozen; `c3_00` NOT promoted; D-249..D-281
(incl. **D-275/D-277/D-278/D-279/D-280/D-281**) untouched; the proven 003C bridge
geometry held fixed; no safety weakening; no topology/net/footprint/polarity change;
no six-layer/GND change; no netclass/width/clearance/hole-to-hole relaxation; no
authoritative promotion. Phase A NOT completed (the D-275 BPP bridge is still not
integrated); Phase B NOT run. `/home/aqroot8/.aqroot-progress.env` untouched — a
measured FAIL earns no readiness, and the CTO owns the readiness review. No OWNER
decision exists or was made — 003J and its successor are engineering scope within
CTO authority.

---

## 6. The next task — FBV2-P2-003K (defined for immediate continuation)

**FBV2-P2-003K — a co-scheduled DISJOINT-SUB-BOX bridge reservation (candidate c/d),
proven on a parent-supervised full run.** 003J measured that the corridor lacks the
capacity for both users by any via-relocation and that the only spare ≥1.20 mm F.Cu
lane is a southern band DISJOINT from the tap cluster (the corridor taps sit at
y<74.7; the copper-only detour uses y>75). 003K implements the minimal env-gated
candidate that RESERVES a bridge sub-box in that disjoint band in the sparse window
(reusing the D-266/D-267 reservation machinery and the existing `AQROOT_BRIDGE_EARLY`
003I stage as the base) and forces the western LTC block to route in the complement,
then MEASURES on a supervised full run whether BPP closes WITHOUT reintroducing the
003I `GND`/`BAT_MAIN`/`BAT_RAW` clearance/site failures.

- **precise candidate hypothesis:** a ≥1.50 mm F.Cu bridge reserved in the southern
  disjoint sub-box (R75.2 entry → south band y>74.7 → far node), laid before the
  LTC_GATE/BAT_RAW taps, leaves the tap cluster's y<74.7 space free so the taps AND
  `GND`/`BAT_MAIN` still find legal sites. UNKNOWN until measured: whether the
  southern band holds ≥1.50 mm once reserved (003J shows it caps at ≤1.30 mm on the
  already-dense board — the sparse-window reservation is the whole point), and
  whether the western block fits in the complement.
- **the supervised full run (hand to the parent CTO):** the exact command is the
  003I recipe with the 003K reservation gate on, e.g.
  `AQROOT_D279=1 AQROOT_D280=1 AQROOT_BRIDGE_EARLY=1 AQROOT_BRIDGE_SOUTH=1
  python3 route_battery_block.py c3_00 …` (the `c3_00` + SIXLAYER + D277..D280 Phase-A
  recipe), **≈ 35–40 min wall-clock** (the 003E/003F/003G full runs were 2300–2330 s).
  **STOP CRITERIA:** the run is a candidate ONLY if BPP (`D9.1/C58` at ≥1.20 mm) closes
  AND `GND`/`BAT_MAIN` hold ≥0.200 mm AND `BAT_RAW` keeps its via site AND the DRC
  histogram equals the scratch baseline (no new clearance/hole class) AND the
  D-277..D-280 closures are retained; ANY new clearance violation is GENUINE and MUST
  NOT be absorbed (the 003I ruling). If the southern reservation cannot hold ≥1.20 mm
  or the western block cannot fit the complement, candidate (c) is exhausted and the
  fallback is a placement spread of the LTC4368 block — an OWNER/mechanical decision.
- **hard constraints (binding, unchanged from 003I/003J):** preserve the proven
  D-275 bridge geometry (cardinality-1 `BAT_PROT_SHDN_CTL` vacate, entry/traverse/exit
  arrays, ≥3 fault-tolerant floor, ≥1.20 mm F.Cu trunk) and the D-277..D-280 closures;
  no netclass/width/clearance/hole-to-hole relaxation (0.200 mm and 0.25 mm ENFORCED);
  no topology/net/footprint/polarity/safety change; no six-layer/GND change; treat the
  optional `BAT_SENSE TP20.1` (TEST) point SEPARATELY; no authoritative promotion
  unless the full Phase-A gate passes on a supervised run; do NOT launch the long full
  run without CTO supervision.
- **scope:** CTO/engineering; an OWNER decision only if the routing candidate is
  exhausted and a placement/envelope change becomes the only remaining lever.
