# FBV2-P2-003G — D-279: the dead-cell resistor-field congestion (`VBRIDGE_TOP R85.1`, `REF_HO R92.1↔R93.2`) is an ANTISOCIAL B.Cu DETOUR in the packed 0402 field, not intrinsic geometry and not the D-278 crossing pin; a measured route-time ANTISOCIAL-DETOUR LAYER HOP closes BOTH named blockers on a full production run — net-positive, DRC-identical — while rotating ONE functional casualty (`N_BATDIV C61.1`) that is deferred to 003H; D-277/D-278 and the proven 003C bridge are held fixed

**Date:** 2026-08-28 · **Task:** FBV2-P2-003G · **Starting HEAD:** `3fc55e4`
**Verdict:** **MEASURED REPAIR (both named blockers) — a scoped, env-gated
route-time layer hop closes `VBRIDGE_TOP R85.1→D10.1` and `REF_HO R92.1↔R93.2`
on a full production run, net-positive on connectivity (23→24 in-scope nets) with
an identical DRC histogram and every regression gate green. The coupled packed
field ROTATES one casualty onto the pre-existing hyper-marginal `N_BATDIV C61.1`
(a functional net, disclosed, NOT a test point) → defined as 003H. No
topology/net/footprint/polarity/safety change; no authoritative promotion (the
board stays 0-track; Phase A remains open on the held-fixed 003C BPP bridge and
now C61.1).**

D-278 (003F) cleared `VREC_VCC U19.8` and named the next two blockers, both
`NO_LEGAL_ESCAPE ≥ 0.150 mm` on a full run inside the packed 0402 dead-cell
field (R84–R96 / Q5–Q9, 0.65 mm pitch): `VBRIDGE_TOP R85.1→D10.1` (boxed by
N_POL) and `REF_HO R92.1↔R93.2` (boxed by REC_GATE_N). 003G discriminated the
same A→B→C way and repaired both.

---

## 1. The three candidate causes, discriminated by measurement

### (A) intrinsic pad / footprint / board-edge geometry — **REFUTED**

On the empty authoritative board the escape count at ≥ 0.150 mm is:

| pad | position | ways out (empty board) |
|---|---|---|
| `VBRIDGE_TOP R85.1` | (8.000, 28.725) | **8** |
| `VBRIDGE_TOP D10.1` | (1.195, 6.265) | **7** |
| `REF_HO R92.1` | (8.000, 15.775) | **8** |
| `REF_HO R93.2` | (9.650, 13.925) | **8** |

Every packed-field 0402 pad leaves its own copper freely — intrinsic geometry is
not the blocker.

### (B) route-order / already-laid copper — **CONFIRMED, and it is an ANTISOCIAL DETOUR**

**Reproduction note — this is a FULL-RUN phenomenon.** Unlike D-278's U19.8 (a
pure local pin-field-order effect the `AQROOT_LOCAL=DEADCELL` bounded prefix
reproduced), the committed DEADCELL prefix ROUTES both R85.1 and R93.2: it omits
the west-margin `BAT_RAW` divider, so the dead-cell `BAT_RAW` field taps (R86.2 /
R89.1 → node) fail for lack of any `BAT_RAW` copper and never lay the field
copper that boxes the victims. The two blockers only bind on a full production
run, so attribution was done on the **real routed baseline board** (a full run at
`3fc55e4`, D-279 off, reproducing `phaseA_003f_fix.json` exactly: 68 connections,
ratsnest 710/−71, identical DRC).

**Attribution on the real routed baseline board.** The victim pads are sealed to
**0 escape** and the boxing copper is a horseshoe of an ADJACENT net's route:

- `VBRIDGE_TOP R85.1` — `blocked by track ×49, R85.2 ×7, R86.1 ×7, R86.2 ×5`.
  The seal is the connection **`N_POL R85.2→R86.1`**, which routed **6.23 mm for a
  2.48 mm straight-line span (2.5×)** as a B.Cu box around R85.1 (walls at
  x = 7.20 and x = 8.80, a north wall at y = 29.60), plus the wide `BAT_RAW R86.2`
  tap. Removing the nine N_POL box tracks within 1.6 mm of R85.1 restores it from
  **0 → 7 ways**; removing `BAT_RAW` alone leaves it at 0. The N_POL horseshoe is
  the seal.
- `REF_HO R93.2` (the sealed end of the `R92.1↔R93.2` connection; R92.1 itself
  keeps 1 way) — `blocked by track ×46, R93.1 ×7, R92.2 ×7, R94.2 ×7`. The seal
  is **REC_GATE_N** copper wrapping R93.2 as `R94.2` escapes north through the
  packed column, reinforced by the antisocial `REC_BAT_LOW Q7.1→R93.1`
  (23.1 mm / 3.1×). Removing REC_GATE_N within 1.6 mm restores R93.2 from
  **0 → 6 ways**; removing REC_GATE_N + REC_BAT_LOW → **0 → 8 ways**.

**The aggressor is the DETOUR, not the net.** Routed DIRECT on the empty board,
`N_POL R85.2→R86.1` runs 2.52 mm and R85.1 stays at 7 ways; only when the packed
field fills does the same connection come back a 6+ mm horseshoe that walls
R85.1. This is the D-278 lesson generalised: a single crossing pin was the
special case; the general case is any low-current dead-cell route whose direct
lane is full and whose B.Cu detour walls a co-located pad.

### (C) minimum placement ECO — **NOT REQUIRED**

(B) is repaired without moving any part (the route-time layer hop, §2), so cause
(C) is left un-exercised per the A→B→C order.

## 2. The fix — D-279, an ANTISOCIAL-DETOUR LAYER HOP measured at route time

`run_once` already has `connect_hop` on its fallback ladder, but a B.Cu route
that *succeeds* with a horseshoe never reaches it. D-279 measures the result: for
a **dead-cell-class SIG** connection (`net[len(N):] in PL.DEADCELL`, never a
wide/high-current net, TRUNK/TAP role, or `(node)` target) whose B.Cu copper came
back **> `D279_K` × its straight-line pad span AND > `D279_MIN_MM`**
(defaults 2.0 / 5.0 mm), the route is reverted and re-laid as an **ordinary
0.35/0.20 through-via hop** (D-257 preferred via, no rule relaxed) that runs
**direct** off the outer layer. The hop prefers an **inner signal layer
(In2/In3) first, F.Cu last** — a local field detour belongs on an inner fan-out
layer, leaving the outer F.Cu clear for the cross-board runs that need it — and
the swap is kept **only if the hop is legal AND strictly shorter**; otherwise the
original B.Cu route is re-laid untouched. It adds an option, removes none.

Env-gated (`AQROOT_D279`): unset reproduces the pre-003G behaviour byte-for-byte,
so every earlier measurement and the whole G1–G11 / bridge / u19 gate set stand.

**Measured on the full run (`AQROOT_D279=1`, K=2.0, MIN=5.0):** two connections
tripped the predicate and hopped, both onto **In2.Cu**:

- `N_POL R85.2→R86.1` — antisocial B.Cu 6.2 mm (2.5×) → layer hop 4.5 mm, 2 via.
- `REC_BAT_LOW Q7.1→R93.1` — antisocial B.Cu 23.1 mm (3.1×) → layer hop 9.4 mm, 2 via.

With the horseshoes gone, **both victims route**: `VBRIDGE_TOP R85.1→D10.1`
(F.Cu, 2 via) and `REF_HO R92.1→R93.2` (B.Cu, 3.8 mm).

**Blast radius.** Exactly two dead-cell SIG connections were re-routed; both are
enumerated above. The mechanism is inert for every wide/high-current net, every
TRUNK/TAP, every node target, and every route whose copper is within 2× of its
span — measured, not asserted.

## 3. The full production run (`phaseA_003g_fix.json`)

Recipe = the pinned D-271 production recipe (`AQROOT_SIXLAYER`, c3_00 asserted,
`AQROOT_D256=GSQ`, `AQROOT_Q3_POFV`, `AQROOT_D266`, `AQROOT_D267=F1`,
`AQROOT_TRUNK_LAST`, `AQROOT_U18_ORDER=6,10,7,1,3,2`, LOCAL empty, no
`AQROOT_BRIDGE_ECO`) **plus `AQROOT_D279=1`** (with `D279_K` / `D279_MIN_MM` at
their committed defaults 2.0 / 5.0 mm — the measured 003G values) — the same base
config as the 003G baseline, run in the foreground and owned by this task.

| metric | baseline (D-279 off) | fix (D-279 on) |
|---|---|---|
| connections | 68 | **69** |
| ratsnest / Δ | 710 / −71 | **709 / −72** |
| in-scope nets connected | 23 / 29 | **24 / 29** |
| DRC histogram | `{hole_clearance 5, lib_footprint_issues 199, solder_mask_bridge 1, unconnected_items 499}` | **identical** |
| `bridge_eco` | null | null |

Per-net connectivity diff (baseline → fix), all 29 in-scope nets, **exactly three
changed**:

- `VBRIDGE_TOP`  not connected → **connected** (R85.1—D10.1 closed)
- `REF_HO`       not connected → **connected** (R93.2 joined)
- `N_BATDIV`     connected → **not connected** (C61.1 rotated out — §4)

## 4. The casualty ledger — `N_BATDIV C61.1` rotates (→ 003H), tracked not hidden

The packed field is coupled: relaxing it to free R85.1/R93.2 rotates a casualty
onto **`N_BATDIV C61.1→U19.6`**. This is a **functional** connection (a bypass cap
on the divider-sense node), **not** a test point — the task's line "do not
silently trade a functional connection for a test point" is respected by
disclosing it here in full.

`C61.1` is a **pre-existing hyper-marginal** connection: a 46 mm cross-board hop
from C61.1 (17.05, 66.545) down into the packed U19.6 field, whose landing via
co-locates with `U19.6→R89.2`'s via. On the baseline it survives *only* on a late
pass with a 0.25/0.15 reserve via that clears the neighbour by ~25 µm
(hole-to-hole 0.275 mm vs the 0.2495 mm floor); the D-279 field perturbation tips
that 25 µm fit over and its landing fails `holes_co_located` / `hole_to_hole` on
every pass. The casualty is **robust across both hop layers** (an F.Cu-first
variant and the adopted inner-first variant produce the identical aggregate — 69
conn, 709/−72, same C61.1 loss), so it is a genuine coupling of the packed field,
not an F.Cu-run artefact. It is a marginal-*landing* problem distinct from the two
named escape blockers, and is defined as **003H** below.

Net effect: **+2 named functional closures, −1 functional casualty = +1** on
in-scope connectivity, DRC unchanged. This is the same casualty-rotation pattern
by which 003F closed U19.8 (003F itself rotated `REF_HO R92.1↔R93.2`, which became
a 003G target); 003G names its rotation to C61.1 rather than over-claim a clean
close.

## 5. Suites, state, cleanliness

All run at `3fc55e4` + this change; every suite green:

| suite | result | pins |
|---|---|---|
| `u19_escape_probe_003g.py` (new) | **PASS** | A geometry refuted (R85.1=8/D10.1=7/R92.1=8/R93.2=8); B the boxing connection is harmless routed direct; C baseline seals both / D-279 routes both; D the scoped measured predicate; E net-positive + the C61.1 casualty tracked, not over-claimed |
| `u19_escape_probe_003f.py` | **PASS** | D-278 crossing-pin hop intact |
| `u19_escape_probe_003e.py` | **PASS** | D-277 planar tie-break intact |
| `router_regression.py` | **PASS** | all checks G1–G11 (D-279 off → pre-003G behaviour) |
| `bridge_probe_003c.py` | **PASS** | D-275 vacate + F.Cu 4-via bridge held fixed |
| `bridge_probe_003d.py` | **PASS** | committed 003D FAIL artifacts un-regressed |

**Scratch restored.** `phaseA_journal.json` (per-run scratch) reset to HEAD;
`w/` scratch dirs are gitignored. Committed 003G artifacts: the driver change
(the env-gated D-279 block in `run_once` + its config), `u19_escape_probe_003g.py`,
and the result JSONs `phaseA_003g_base.json` (full baseline, D-279 off) and
`phaseA_003g_fix.json` (full fix, D-279 on), both produced by the committed logic.

**No authoritative PCB promotion.** The full run applies no ECO, lays no
authoritative copper, asserts no promotion gates (Phase A did not pass — the
held-fixed 003C BPP bridge and now C61.1 remain open).
`/home/aqroot8/.aqroot-progress.env` is unchanged; the CTO reviews readiness only
after accepting this pushed milestone.

**Nothing moved and nothing relaxed:** D9, U18, R75–R83, Q3, the shunt, the FETs,
TP17, C58, U19, D10 and the whole R84–R96/Q5–Q9 field all frozen; `c3_00` NOT
promoted; D-249…D-278 (incl. **D-275/D-277/D-278**) untouched; the proven 003C
vacate + F.Cu bridge held fixed; outer-1-oz / high-current policy unchanged; no
safety weakening; no topology/net/footprint/polarity change; no netclass/width/
clearance rule relaxed; the D-279 hop uses ordinary D-257 through vias at declared
geometry. Authoritative PCB UNCHANGED — six copper layers, 0 signal tracks, 0
signal vias.

## 6. The next blocker — FBV2-P2-003H (defined for immediate continuation)

With both named dead-cell escape blockers repaired, the remaining FUNCTIONAL
dead-cell blocker is the casualty this repair rotated:

> `N_BATDIV C61.1→U19.6 NO ROUTE` — a 46 mm cross-board bypass-cap hop whose
> landing via co-locates with `U19.6→R89.2`'s via in the packed U19.6 field
> (hole-to-hole ~25 µm under the floor). Discriminate it the same A→B→C way,
> favouring a **bounded via-site reservation** for its U19.6-field landing (the
> D-266/D-267 scarce-exit-reservation class) or an owner decision to accept the
> net-positive functional trade — WITHOUT moving the frozen field and WITHOUT
> relaxing the hole-to-hole floor, holding D-277/D-278/**D-279** and the proven
> 003C bridge fixed, no topology/net change, no safety weakening, no authoritative
> promotion unless a later full gate passes.

The BPP trunk closure (`D9.1/C25/C36/C58` at ≥ 1.20 mm) remains the held-fixed
003C bridge case and is not in 003H's scope.
