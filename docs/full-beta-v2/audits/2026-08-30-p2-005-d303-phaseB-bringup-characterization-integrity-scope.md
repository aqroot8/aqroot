# FBV2-P2-005 / D-303 — Phase-B bring-up on the first promoted authoritative board

**Date:** 2026-08-30
**Starting HEAD:** `01a38a5422f4504bf481d37ceae6382a0197cee7` (D-302; pushed; `origin/master` identical)
**Result:** A governed CTO **CHARACTERIZATION + INTEGRITY + SCOPING** milestone — **no copper change, authoritative board byte-identical, autonomy CONTINUES, no owner decision.**
**Verdict:** the D-302 promotion is confirmed sound and re-verified; the in-repo "Phase B" replay drivers are STALE and assume a copper-empty base (must not be naively re-run); the real remaining Phase-B (rest-of-board routing) is inventoried and scoped as the next bounded lever.

---

## 1. Objective

Perform a bounded, evidence-first Phase-B bring-up on the first promoted
authoritative Phase-A board: determine the exact Phase-B definition and
replay/order semantics; establish whether the existing drivers assume a
copper-empty authoritative base; re-verify the promoted-board integrity with
affordable checks before any long route; and either land the first safe accepted
Phase-B increment or sharply characterize the blocker and the next lever — all
without duplicating, erasing or silently rerouting accepted Phase-A copper.

## 2. Exact Phase-B definition (from the code, not assumption)

"Phase B" in this repository is the **battery-block replay / idempotence
verification** of the D-271 discipline — NOT rest-of-board routing:

| artifact | role |
|---|---|
| `replay_battery_block.py` | **promotion** — copies the validated Phase-A scratch geometry (tracks/vias/rule-areas) **verbatim** onto the authoritative board; "NOTHING IS RECOMPUTED HERE". |
| `route_battery_block.py` **SECTION 17** (`AQROOT_REPLAY`) | **independent reproduction** — re-runs the router from the journal with **frozen order + pinned widths**, `passes=2`, on a **clean scratch** copy, to prove the result is a property of the placement not a lucky pass ordering. |
| `phaseB_compare.py` | the **A-vs-B gate** — connections, nets, tracks, vias, per-net widths, connectivity clusters, DRC, ratsnest and per-net length must all match. |

The driver `route_battery_block.py` is scoped to "the whole battery / protection
block" — **the power tree only**.

## 3. Integrity baseline (re-verified this session)

- `git rev-parse HEAD == origin/master == 01a38a5…`, worktree clean.
- Authoritative PCB `sha256 63a9bc54e16cd1b2c69ad41cd95a2bb4d3e258503cb12b5628885debf87d6ba9`, size 1475931 — **matches the D-302 record**.
- **432 tracks / 54 vias / 6 copper layers / 41 zones / 324 footprints**; `phaseA_journal.json` **77 entries**.
- **Every one of the 432 routed tracks is an in-scope power-tree net (0 out-of-scope)** → the board carries the Phase-A battery-block copper **ONLY**.
- `router_regression.py` = **ALL 79 CHECKS PASS (G1–G17)** (incl. G17 authoritative-file-unchanged + clean-fixture contract).
- The shared `phaseA_journal.json` was **not** mutated (no scratch route was run).

Reproducible via the committed read-only probe `checks/phaseB_bringup_probe_005.py`
→ `checks/phaseB_bringup_005.json` (PASS, 0 failures).

## 4. The existing Phase-B drivers assume a copper-EMPTY base (the blocker, proven)

Faithful, static evidence (reading the actual journal + the actual driver code —
no proxy, per the D-286/D-300 lesson):

1. **`replay_battery_block.py:40-42`** hard-refuses a non-empty authoritative
   board:
   ```python
   have = [t for t in dst.GetTracks()]
   if have:
       raise SystemExit("authoritative board already carries %d track items" % len(have))
   ```
   Post-D-302 the board carries 432 tracks, so this driver can **never run
   again** — but its promotion role is already fulfilled byte-identically by
   D-302's direct scratch→authoritative copy.

2. **SECTION-17 `AQROOT_REPLAY` (`route_battery_block.py:2297`)** skips every
   `role=='TRUNK+ESCAPE'` journal entry:
   ```python
   for e in jr['journal']:
       if e.get('role') == 'TRUNK+ESCAPE':
           continue
   ```
   The journal has **exactly one** `TRUNK+ESCAPE` entry, and it is the one the
   D-302 lever added to CLOSE the terminal wall and DEFINE the promotion:
   `BAT_PROTECTED_P U11.2→C36.1, w=1.5, reinforcement=True`. A replay would carry
   **76 of 77** items, dropping the wall closure → it would NOT reproduce the
   promoted board (it would re-hit the U11.2 wall or diverge). The replay
   machinery predates the D-297/D-299/D-301/D-302 levers.

3. **`phaseB_compare.py`** requires a `phaseB.json` that was **never produced** —
   no reproduction/compare was ever wired or run for this board.

Journal role census (77 entries): SIG 46, TAP 9, TRUNK 8, SENSE 4, TEST 4,
JOIN 2, RESERVE_PAIR 2, RESERVE_RUN 1, **TRUNK+ESCAPE 1** (the U11 reinforcement).

## 5. The promotion is sound regardless

The authoritative board is byte-identical to a scratch produced by a **genuine
full-authority Phase-A gate** (`run_003t_full.sh 004b2` with
`AQROOT_U18BPP_JOIN=I3 AQROOT_U19CAP=1 AQROOT_LTCGATE_KO=1 AQROOT_U11_RETARGET=1`,
`DRIVER_EXIT=0`, PHASE A COMPLETE) — a real driver in the real order, not a proxy
(D-286-compliant) — with real KiCad DRC showing zero new copper classes and
`router_regression` ALL PASS. The D-271 "independent reproduction" proof is
therefore a **modest-value nicety whose machinery is stale**; re-running it as-is
is not justified — it would be a long, divergence-prone route that demonstrably
drops the U11 closure. If the reproduction proof is ever wanted, the SECTION-17
replay must first be made reinforcement-aware (do not blindly skip the single
`TRUNK+ESCAPE` closure entry) and lever-faithful.

## 6. The real remaining Phase-B (scoped — the next bounded lever)

Rest-of-board = **164 multi-pad nets, 0 routed**, across 9 subsystem sheets +
rails. Largest nets: GND (259 pads, unrouted — the In1/In4 GND plane zones exist
but signal returns/stitching remain), +3V3 (86 pads), `BQ25185_SYS` (16),
`ACC_3V3_SW` (15), `USB_VBUS_CHG` (11), I2C buses (10 each).

| sheet | nets (≥2 pads) | pads |
|---|---|---|
| 09_COMMUNITY_HEADER | 20 | 65 |
| 04_SPI_B_RADIOS_NFC | 20 | 58 |
| 01_POWER_TREE (beyond the protected block) | 18 | 78 |
| (top-level) | 17 | 387 |
| 08_BUTTONS_EXPANDERS | 10 | 33 |
| 03_SPI_A_DISPLAY_SD | 5 | 21 |
| 06_AUDIO | 4 | 10 |
| 02_MCU_CORE | 4 | 13 |
| 07_IR | 4 | 12 |
| 05_I2C_DEVICES | 2 | 5 |
| (remaining single-net groups) | 66 | — |

This is ~85 % of remaining routing and has **no driver** (route_battery_block is
power-tree only). The next lever is a **new, scoped, INCREMENTAL rest-of-board
driver** that:
- LOADS the promoted board and **PRESERVES the accepted Phase-A power-tree
  copper** (never erase/reroute — an accepted invariant);
- routes a **bounded, isolated net-group first**;
- is gated by **real full-board DRC** (D-286);
- promotes **only a genuine no-casualty / no-new-DRC increment**.

The wholesale-copy `replay_battery_block.py` must be generalized for incremental
promotion (copper-empty-base guard removed) or a new incremental promoter
written.

## 7. Opportunity & Simplification Scan (mandated — routing-phase transition)

- Routing the rest of the board is core CTO-authority engineering, **not** an
  owner decision (no product feature / scope / safety / cost / topology change).
- **Decompose by sheet / net-group** so each increment is small, real-DRC-gated
  and independently promotable (matches the D-297 "bare inner In2/In3 signal
  layers are spare capacity" lesson and the direction-2 escape corridors).
- **Retire/generalize** the stale one-shot replay path rather than carry it as a
  trap for a future session.
- No BOM / recoverability / testability / firmware / UX opportunity forces a
  change; the six-layer stack, GND planes (In1/In4), footprints, outline and
  DNP/tuning provisions are frozen and adequate.
- **Open owner decisions: NONE.**

## 8. Integrity & locked constraints preserved

No copper / placement / rule / floor / DRU / topology / footprint / outline
change; authoritative PCB byte-identical (`sha256 63a9bc54…f87d6ba9`); shared
journal at HEAD. Enforced: D-249 (≥1.20 mm BPP), D-269 (0.300 mm current-path),
D-257 via ladder, 0.60 mm BAT_MAIN, 0.200 / applicable 0.150 signal, 0.25 mm
hole-hole, D-275/D-288 bridge, 0.300 BAT_MAIN clearance. D-290 untouched; the
accepted `AQROOT_U18BPP_JOIN` (D-297), `AQROOT_U19CAP` (D-299/G14),
`AQROOT_LTCGATE_KO` (D-301/G15), `AQROOT_U11_RETARGET` (D-302/G16), the D-302
fixture split (G17), `place_003l` (D-285), D-275 and D-277..D-302 all preserved;
frozen `beta-full-reference-v1` untouched. DEVICE_SPEC unchanged (no authoritative
hardware/product fact changed).

## 9. Next task — FBV2-P2-006

Begin rest-of-board routing (§6): build the bounded incremental driver and route
the FIRST isolated net-group (recommend a small self-contained subsystem — a
low-pin-count peripheral or a short bus segment) with real full-board DRC gating
and no Phase-A casualty; promote only on a genuine no-new-DRC increment.

**NO PROGRESS EARNED (no copper routed): PCB routing ~15 %, overall ~76 %,
readiness ~77 % (JLCPCB file unchanged).**
