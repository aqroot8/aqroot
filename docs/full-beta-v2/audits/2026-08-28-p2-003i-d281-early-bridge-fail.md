# FBV2-P2-003I — D-281: the route-order EARLY landing of the proven D-275 western-corridor bridge is a MEASURED, REPRODUCIBLE FAIL — the bridge and the current-carrying corridor users (`LTC_GATE`/`BAT_RAW` tap, the `GND` pour and `BAT_MAIN`) CONTEND for one ~9 mm western corridor, so moving the bridge earlier in the route order changes only WHICH high-current user fails, not WHETHER one fails; no authoritative promotion; D-275 and D-277..D-280 preserved; the topology/capacity fix is deferred to FBV2-P2-003J

**Date:** 2026-08-28 · **Task:** FBV2-P2-003I · **Starting HEAD:** `f4dfe3f`
**Verdict:** **MEASURED FAIL — the obvious re-timing of the proven D-275 bridge
(lay it EARLY, while the western corridor is still sparse, and let later routing
route around it) was measured on a parent-supervised full run and DOES NOT WORK.
The early bridge LAYS (`EARLY BRIDGE OK land=C58.1 traverse=8.920mm w=1.50 entry=4
exit=4`), but the current-carrying corridor users that route AFTER it then FAIL
their normal gates with two new clearance VIOLATIONS and a lost via site — `GND`
clearance actual 0.0726 mm vs 0.200 mm, `BAT_MAIN` actual 0.125 mm vs 0.200 mm,
`BAT_RAW` NO_VIA_SITE. Per the CTO ruling these are GENUINE safety-clearance
violations and MUST NOT be absorbed/refreshed into the baseline; the run is INVALID
as a Phase-A candidate, not proof of success. The root cause is structural: the
western corridor lacks the CAPACITY for both the bridge and the taps, and a
re-ordering cannot create room the geometry does not have. No authoritative copper,
no placement ECO, no rule relaxed; the authoritative PCB stays 0-track/0-via and
D-275 + D-277..D-280 are preserved. The fix is a TOPOLOGY/CAPACITY change, deferred
to FBV2-P2-003J.**

003H (D-280) closed the last named dead-cell blocker and left the D-275
`BAT_PROTECTED_P` (BPP) bridge integration as the sole remaining Phase-A promotion
blocker. 003D (D-276) had already integrated the exact D-275 mechanism as an
END-OF-RUN driver stage (`AQROOT_BRIDGE_ECO` → `bridge_eco_003d.apply_eco`) and
measured it to ABORT; 003I's preflight isolated the cause to western via-density.
003I then measured the obvious next move — re-time the same bridge to fire EARLY,
before the corridor fills — and this audit records that measured FAIL.

---

## 1. Arc and premise — where the bridge stands after D-280

- **D-275 (003C)** proved the vacate + F.Cu via-array bridge on a SPARSE `c3` board
  as a POST-PROCESS: PR-40 9/9, U18 8/8, no new DRC, ratsnest −1. Proven in
  ISOLATION on a placed-but-unrouted board.
- **D-276 (003D)** integrated the exact mechanism as an END-OF-RUN driver stage and
  measured it to ABORT with `no >= 1.20 mm F.Cu traverse corridor`. At the time the
  abort was conflated with upstream Phase-A failures (`N_POL U19.3`, the dead-cell
  field), since repaired by D-277..D-280.
- **003I preflight** re-measured the end-of-run bridge on the fully-repaired board
  and isolated the root cause (§2): the tight western corridor is VIA-DENSE.
- The D-275 vacate premise is intact — the cardinality-1 `BAT_PROT_SHDN_CTL`
  control vacate is unchanged and the trunk is never moved to an inner layer.

The precondition 003D lacked is now MET: the D-279/D-280 repaired full run
(`phaseA_003h_fix.json`) reaches a clean routed end-state with the bridge OFF
(connections 71, `bridge_eco null`, DRC == baseline). So the bridge is the sole
Phase-A promotion blocker, and it was correct to test whether re-timing closes it.

---

## 2. Root cause — the western corridor is via-DENSE, and it is ONE shared corridor

`bridge_probe_003i` clause B, on the committed dense production board (scratch
`FIX003H3`, the 003H full run):

- the tight western corridor `R75.2 (2.8,68) → D9.1 (11.35,72.5)` carries **15**
  through-vias (the proven-sparse `c3` board carries 11 — the +4 are the
  `LTC_GATE` / `BAT_RAW`-tap stage vias);
- with the D-269 0.30 mm trunk clearance respected on the ~56 board vias, the
  ≥ 1.20 mm via-AWARE `route_traverse` has **NO_PATH** to every candidate BPP
  landing;
- the SAME traverse with the via clearance dropped (copper-only) **PATHs**.

So the wall is **via density, not copper**, and it sits in a single ~9 mm corridor
that both the high-current BPP traverse AND the `LTC_GATE` / `BAT_RAW` taps must
cross. This is why the end-of-run bridge aborts: by the time it runs, the taps have
already dropped their vias into the box.

---

## 3. The re-timing candidate — the EARLY stage (`AQROOT_BRIDGE_EARLY`)

`bridge_early_003i.apply_early`, wired into `route_battery_block.main` at the first
stage-8 queue item (env-gated `AQROOT_BRIDGE_EARLY`, off by default):

- fires ONCE, after the D-266 Kelvin reservation and the U18 pin field have claimed
  their sites but BEFORE the `LTC_GATE` / `BAT_RAW` taps inject the corridor-choking
  vias — i.e. in the proven-sparse window;
- lays the EXACT D-275 mechanism, single-sourced VERBATIM from `bridge_route_003c`:
  the cardinality-1 `BAT_PROT_SHDN_CTL` vacate, the 4× 0.80/0.40 entry array on
  `R75.2` (POFV), the ≥ 1.20 mm F.Cu traverse, the 4× exit array (array landing, no
  single via carries pack current), the ≥ 3 fault-tolerant floor;
- lands the exit array on a west-cluster BPP pad present from board load (`D9.1`,
  then `C58.1`), joined onward to the node / `U11.2` by the ordinary trunk / cap-tap
  / `u11_escape` stages;
- restores the driver's via-blind obstacle model on return (removes only the
  injected phantom via-obstacles), leaving the real bridge copper
  (net `BAT_PROTECTED_P`) as an obstacle every later net routes around.

**It LAYS — the NECESSARY precondition holds.** `bridge_probe_003i` clause E lays it
on a reconstructed sparse placed board: entry 4, traverse 1.50 mm, exit 4, and NO
new DRC (clearance/hole/short/mask) on the sparse board. The supervised full run
laid it too: `EARLY BRIDGE OK land=C58.1 traverse=8.920mm w=1.50 entry=4 exit=4`.

---

## 4. The measured FAIL — necessary is not sufficient

Parent-supervised full run, recipe `c3_00` + SIXLAYER + D277..D280 +
`AQROOT_BRIDGE_EARLY=1`. The early bridge laid, but the current-carrying corridor
users that route AFTER it failed their normal gates:

| net | gate | actual | required | verdict |
|---|---|---|---|---|
| `GND` | clearance | **0.0726 mm** | 0.200 mm | VIOLATION |
| `BAT_MAIN` | clearance | **0.125 mm** | 0.200 mm | VIOLATION |
| `BAT_RAW` | via site | — | — | **NO_VIA_SITE** |

These are genuine safety-clearance violations and a lost via site, not baseline
noise. **Per the CTO ruling they MUST NOT be absorbed/refreshed into the baseline —
doing so would waive real clearance violations.** The parent stopped the run once
the conflict became decisive; it is INVALID as a candidate, not proof of Phase-A
success. No log of the run was retained; the measured figures are recorded verbatim
in `bridge_probe_003i` (constant `MEASURED`, clause F) so the closeout does not
depend on re-running a long full route.

### Why — a resource-contention SYMMETRY, not a timing bug

The early FAIL is the exact symmetric corollary of §2:

- **End-of-run:** the 4 `LTC_GATE` / `BAT_RAW`-tap vias occupy the corridor first,
  and the ≥ 1.20 mm bridge traverse **NO_PATHs** around them (003D's abort, §2).
- **Early:** the 1.50 mm bridge traverse occupies the corridor first, and the SAME
  taps then have **no legal via site** / lose clearance around it (`GND` 0.0726,
  `BAT_MAIN` 0.125).

**One corridor, two mutually-exclusive high-current users. Route ORDER decides WHICH
one fails, not WHETHER one fails.** Timing is not the lever: the corridor does not
have the CAPACITY for both, and re-ordering cannot manufacture room the geometry
lacks. Closing BPP on the full board requires a TOPOLOGY / CAPACITY change, not a
schedule change — deferred to 003J (§6).

---

## 5. Suites, cleanliness, no false promotion

**No incomplete result masquerades as evidence.** The interrupted run left a partial
board (scratch `w/FIX003I`, early bridge + partial downstream routing) and clobbered
the per-run `phaseA_journal.json`. Both were cleaned: `FIX003I` removed (it does not
honestly pin any result — the probe was even mis-reading it as a "completed board"),
`phaseA_journal.json` restored to HEAD. No `phaseA_003i_fix.json` exists claiming a
clean/absorbed end-state (`bridge_probe_003i` clause F guards this).

**The authoritative PCB is untouched:** `pcbnew` load of
`hardware/beta-v2/kicad/aqroot-beta-v2/aqroot-Beta-v2.kicad_pcb` reads **0 signal
tracks, 0 signal vias** (probe clause F). No KiCad source mutated, no placement ECO,
no rule relaxed — the 0.200 mm clearance floor is ENFORCED, not waived.

**Suites (all PASS, no long route re-run):**

- `bridge_probe_003i` — rewritten as the standing measured-FAIL record. Clause A
  (precondition met), clause B (via-density root cause on `FIX003H3`), clause C
  (D-275 invariant preserved), clause E (early bridge lays on the sparse board —
  necessary only), clause F (the measured downstream FAIL, candidate rejected, no
  false promotion). PASS.
- `router_regression` — ALL CHECKS G1–G11 (D-280 off → pre-003H behaviour). PASS.
- `bridge_probe_003c` — 003C/D-275 held fixed. PASS.
- `bridge_probe_003d` — 003D end-of-run abort preserved. PASS.
- `u19_escape_probe_003e` (D-277), `003f` (D-278), `003g` (D-279), `003h` (D-280) —
  all intact. PASS.

**Committed artifacts:**

- `route_battery_block.py` — the env-gated (`AQROOT_BRIDGE_EARLY`) EARLY stage hook
  (off by default; when set it also disables the `AQROOT_BRIDGE_ECO` end-of-run
  duplicate so the bridge is laid exactly once). Default behaviour byte-unchanged.
- `bridge_early_003i.py` — the EARLY route-order driver stage (the FAIL reproducer).
- `bridge_probe_003i.py` — the standing measured-FAIL record.
- This audit, the CTO_DECISIONS D-281 row, the CHANGELOG entry, the PROGRESS entry,
  the transcript.

**Nothing moved and nothing relaxed:** D9, U18, R75–R83, Q3, shunt, FETs, C58, U19,
D10 frozen; `c3_00` NOT promoted; D-249..D-280 (incl. **D-275/D-277/D-278/D-279/
D-280**) untouched; the proven 003C bridge geometry held fixed; no safety weakening;
no topology/net/footprint/polarity change; no six-layer/GND change; no netclass/
width/clearance/hole-to-hole relaxation; no authoritative promotion. Phase A NOT
completed (the D-275 BPP bridge is still not integrated); Phase B NOT run.
`/home/aqroot8/.aqroot-progress.env` untouched — a failed candidate earns no
readiness, and the CTO owns the readiness review. No OWNER decision exists or was
made — 003I and 003J are engineering scope within CTO authority.

---

## 6. The next task — FBV2-P2-003J (defined for immediate continuation)

**FBV2-P2-003J — a TOPOLOGY / CAPACITY solution for the shared western corridor.**
The measured conclusion of 003I is that BPP closure and the `LTC_GATE` / `BAT_RAW`
taps CONTEND for one ~9 mm corridor and route order cannot resolve it; the corridor
needs more capacity, or one user must leave it. 003J investigates a
scheduling/topology-of-routing solution WITHOUT weakening clearance or any product /
electrical requirement:

- **candidate directions** (to be measured, not assumed): (a) widen or add a second
  western corridor lane so the bridge traverse and the taps do not share the box;
  (b) relocate the `LTC_GATE` / `BAT_RAW`-tap via drops OUT of the corridor (a
  route-target / staging change, not a part move) so the bridge owns the corridor;
  (c) re-plan the bridge landing / trunk so the ≥ 1.20 mm traverse and the taps
  occupy disjoint corridor sub-boxes; (d) a co-scheduled joint placement that
  reserves the corridor capacity for both before either routes.
- **hard constraints (binding):** preserve the proven D-275 bridge geometry (the
  cardinality-1 `BAT_PROT_SHDN_CTL` vacate, the entry/traverse/exit arrays, the
  ≥ 3 fault-tolerant floor, the ≥ 1.20 mm F.Cu trunk) and the D-277..D-280 closures;
  no netclass / width / clearance / hole-to-hole relaxation (the 0.200 mm and 0.25 mm
  floors ENFORCED); no topology/net/footprint/polarity/safety change; no six-layer/
  GND change; treat the optional `BAT_SENSE TP20.1` (TEST) point SEPARATELY; no
  authoritative promotion unless the full Phase-A gate passes on a supervised run.
- **scope:** CTO / engineering, no OWNER decision unless a genuinely product-level
  question surfaces (e.g. a placement change that touches the mechanical envelope or
  the high-current policy). Do NOT launch a long full production run without CTO
  supervision.
