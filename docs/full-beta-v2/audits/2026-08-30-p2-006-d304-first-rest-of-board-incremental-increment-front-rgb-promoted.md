# FBV2-P2-006 / D-304 — First rest-of-board incremental increment: the FRONT_RGB indicator group routed and PROMOTED

**Date:** 2026-08-30
**Task:** FBV2-P2-006 — first bounded incremental rest-of-board routing group
**Decision:** **D-304**
**Result:** **A GOVERNED CTO ACCEPT + PROMOTE.** The first rest-of-board copper is on the
authoritative board: a reusable, scoped INCREMENTAL router/promoter
(`incremental_router.py`) loaded the D-302 promoted board, routed the FRONT_RGB
front-panel status-LED indicator group **without touching a single strand of
accepted Phase-A copper**, and a real full-board gate proved a genuine
no-casualty / no-new-DRC connectivity increment. Copper PROMOTED. Autonomy
CONTINUES; **no owner decision raised.**

Starting HEAD `50149f4` (D-303; pushed; `origin/master` identical).

---

## A — THE OBJECTIVE

D-303 scoped the real remaining Phase-B: **164 rest-of-board multi-pad nets, 0
routed**, across 9 subsystem sheets + rails, with NO driver (the battery-block
`route_battery_block.py` is power-tree scoped; the in-repo replay machinery
assumes a copper-empty base and is stale — see D-303). FBV2-P2-006 builds the
missing piece and takes the first bounded increment.

## B — GROUP SELECTION (measured, not convenient)

Rest-of-board geometry was measured for every non-rail, non-scope multi-pad net
(`w/measure_rest_006.py`, READ-ONLY: pad coordinates, span, layer, footprint
locality, criticality flags). Candidate groups were screened cheaply:

- **CHOSEN — FRONT_RGB indicator cluster (08_BUTTONS_EXPANDERS):** the three
  nets `FRONT_RGB_R_N` / `FRONT_RGB_G_N` / `FRONT_RGB_B_N` (front-panel RGB
  status-LED control lines: U23 GPIO/LED expander pins 4/5/6 → series resistors
  R124/R125/R126). 6 pads, **all B.Cu SMD**, **Default netclass (0.200 mm width,
  0.200 mm clearance, NO via)**, per-net spans 4.77 / 3.85 / 5.09 mm, tightly
  localised at ≈(50–55.4, 96.8–103.25). **The whole region carries ZERO Phase-A
  copper** (0 B.Cu Phase-A tracks, 0 vias in the box), so the increment is
  genuinely isolated. Electrically **noncritical** (low-speed indicator control),
  no rail/RF/USB/high-current/clock/crystal/switching constraint. High
  information at minimum geometric risk: it exercises the full framework
  (multi-net group routing, fine-pitch B.Cu escape from the U23 0.64 mm pin row,
  connectivity gating, full-board DRC delta, Phase-A preservation).

- **REJECTED — 07_IR local cluster** (`IR_LED_K/A`, `IR_RX_VS_LOCAL`): F.Cu with
  THT pads near the north board edge; IR-emitter drive is moderate-current-ish
  and mixes with a local supply node → higher risk, less cleanly noncritical.
  Deferred.
- **REJECTED — 01_POWER_TREE short pairs** (`ILIM_VSET`, `ISET`,
  `ACC_3V3_ILIM`, `MAX17048_ALRT_N`): geometrically trivial B.Cu pairs, but
  power-tree-adjacent set/limit nets and not a coherent standalone subsystem —
  best kept out of the FIRST increment to avoid any power-interaction ambiguity.
- **REJECTED — 05_I2C_DEVICES `BMI270_SDO_ADDR`**: fine single net, but IMU-
  adjacent and only ONE net (not a "group"); the sheet's other net is a longer
  shared I2C bus.
- **EXCLUDED per mandate** — 09_COMMUNITY_HEADER (community-header mass routing),
  04_SPI_B_RADIOS_NFC (RF/NFC radios), USB, crystals, GND/+3V3 bulk rails.

## C — THE REUSABLE INCREMENTAL DRIVER / PROMOTER (`incremental_router.py`)

A single scoped module with a group registry and four commands
(`baseline` / `route` / `gate` / `promote`). Design invariants, all ENFORCED:

- **PRESERVE PHASE-A EXACTLY.** `qrouter.QBoard` loads the authoritative board
  and treats every existing track/via/pad/keep-out as an obstacle; new copper is
  ADDED (never `Remove()`d). `route` writes only to a scratch copy under
  `checks/w/INC_<GROUP>/` — the authoritative project is never touched during the
  experiment (verified: sha256 unchanged after `route`).
- **REAL FULL-BOARD GATE (D-286).** The gate re-loads the scratch board and
  proves, as independent checks:
  1. **no Phase-A copper deleted or altered** — the pre-promotion D-302
     copper-item multiset (432 tracks + 54 vias, each a geometry signature
     `(net, layer, endpoints, width)` / `(net, pos, dia, drill)`) is a SUBSET of
     the routed board's items (0 missing);
  2. **every new copper item is a target-group net** (0 out-of-scope);
  3. **each target net fully copper-connected** — via `GetConnectedItems(pad)`
     (the KiCad-10 call that works here; `GetConnectedPads` returns [] in this
     build): open edges 1→0 for all three;
  4. **no prior Phase-A requested pair regressed** (belt-and-braces electrical
     re-proof over the 71 requested journal pairs);
  5. **ratsnest dropped by exactly the requested count** (pcbnew
     `GetUnconnectedCount`, the project's connectivity authority: 704 → 701, −3);
  6. **real kicad-cli DRC**: no new class, no class increased, `unconnected_items`
     not increased.
- **PROMOTE only on a genuine PASS.** `promote` re-runs the full gate, re-checks
  the authoritative sha has not drifted, then copies the gated scratch board onto
  the authoritative project and merges the 3 connections into
  `phaseA_journal.json` as `role=REST_INC` entries. It REFUSES to promote a
  failing gate.

**On the DRC-vs-ratsnest metric.** kicad-cli DRC's `unconnected_items` (499)
enumerates a smaller set than pcbnew's ratsnest (704) and never listed the
FRONT_RGB nets even when unrouted, so it does not move when they close. The
connectivity GAIN is therefore judged by the pcbnew ratsnest (the same "ratsnest
704" the D-302 promotion used) plus per-net `GetConnectedItems`; DRC's role in
the gate is LEGALITY (must not introduce a new/worse violation, and its
`unconnected_items` must not increase). Both are satisfied.

## D — THE EXPERIMENT (one foreground run)

```
python3 incremental_router.py baseline     # 432/54/6, ratsnest 704, DRC {smb1,hc5,lib199,unc499}
python3 incremental_router.py route  FRONT_RGB   # 3/3 ok; scratch 452 trk / 54 via; AUTH sha unchanged
python3 incremental_router.py gate   FRONT_RGB   # PASS (0 checks failed)
python3 incremental_router.py promote FRONT_RGB  # gate re-run PASS -> promoted
```

- Routed: `FRONT_RGB_R_N` R124.1→U23.4 5.415 mm, `FRONT_RGB_G_N` R125.1→U23.5
  10.830 mm, `FRONT_RGB_B_N` R126.1→U23.6 7.379 mm (detours around the U23
  fine-pitch pad field; all 0.200 mm B.Cu, **0 vias**).
- **GATE = PASS, every check:** Phase-A copper 0 missing; 20 new items, all
  target-net; 3 nets fully connected (1→0 each); 0 Phase-A pairs regressed;
  ratsnest 704→701 (exactly −3); no new DRC class; no class increased;
  `unconnected_items` 499→499.

## E — WHAT IS PROMOTED (integrity)

| | pre (D-302/D-303) | post (D-304) |
|---|---|---|
| authoritative sha256 | `63a9bc54…f87d6ba9` | `00c93bdb…dfb72aad` |
| tracks | 432 | **452** (+20 FRONT_RGB) |
| vias | 54 | **54** (no new via) |
| copper layers / zones | 6 / 41 | 6 / 41 |
| ratsnest | 704 | **701** (−3) |
| journal entries | 77 | **80** (+3 `REST_INC`) |
| real KiCad DRC | `{smb1, hc5, lib199, unc499}` | **identical** |

Every one of the 432 Phase-A tracks and 54 vias is present, byte/geometry-
identical (proven by the multiset-superset check and re-proven post-promotion by
`incremental_probe_006.py`). The only new copper is the 20 FRONT_RGB B.Cu
tracks. No placement / DRU / netclass / footprint / outline / stackup change.

## F — TESTS & REGRESSION CONTRACTS

- **New contract G18** in `router_regression.py` pins the increment on the
  authoritative board: (1) the three FRONT_RGB nets are fully copper-connected
  (`GetConnectedItems`), (2) their copper is legal (0.200 mm B.Cu, NO via), (3)
  the increment is ADD-ONLY (every non-FRONT_RGB track is still the 432 Phase-A
  tracks; vias unchanged at 54; exactly 20 FRONT_RGB tracks).
  `router_regression.py` = **ALL 82 CHECKS PASS (G1–G18)**, run twice,
  deterministic.
- **New focused probe** `incremental_probe_006.py` (READ-ONLY): re-proves on the
  live board the D-304 fingerprints, Phase-A-preserved-exactly (D-302 copper set
  is a subset), the three nets connected, no Phase-A pair regressed, DRC
  unchanged. ALL PASS.
- **`phaseB_bringup_probe_005.py`** (the live D-303 integrity/inventory probe)
  updated to the promoted state (452 tracks / journal 80; scope predicate now
  accepts promoted rest-of-board increments; inventory: 164 rest nets, 3 routed
  = FRONT_RGB, 161 still unrouted). ALL PASS.

## G — OPPORTUNITY & SIMPLIFICATION SCAN (mandated)

- **The incremental framework is the durable win.** It generalises to every
  future subsystem: each group is small, real-DRC-gated, add-only, independently
  promotable, and CANNOT hide a cross-group casualty (the copper-superset check
  fails the gate if any prior strand changes; the requested-pair re-proof fails
  if any prior connection regresses). The stale one-shot `replay_battery_block.py`
  copper-empty-base machinery is now superseded by an incremental promoter rather
  than carried as a trap.
- **Group-selection method is reusable** — `w/measure_rest_006.py` ranks
  candidate groups by pin count / span / layer / locality / criticality, so
  future increments are chosen from measured geometry, not convenience.
- **No hidden cross-group coupling.** The gate is whole-board (D-286): it would
  surface any coupling as a DRC delta or a ratsnest regression. None occurred.
- **BOM / recoverability / testability / firmware / UX / mechanical:** no
  opportunity or constraint forces a change — this is a noncritical indicator
  cluster with no footprint/outline/stackup/silk/firmware surface. The six-layer
  stack's bare inner In2/In3 remain spare capacity for future congested groups.
- **No irreversible cost, no strategic fork. Open owner decisions: NONE.**

## H — INTEGRITY & ROLLBACK

- Pre-promotion authoritative PCB `sha256 63a9bc54…f87d6ba9` (D-302; parent
  `50149f4`) is the rollback point — restored by `git checkout <parent> --
  hardware/beta-v2/kicad/aqroot-beta-v2/aqroot-Beta-v2.kicad_pcb` (+ the journal).
  The D-302 rollback tags (`beta-v2-p2-pre-copper-authoritative`, etc.) still
  stand.
- All locked invariants preserved: no DRU/rule/clearance/stackup/topology/net/
  footprint/value/polarity/outline change; no D-290 reauthorization; no via below
  the D-257 ladder; D-249 (≥1.20 mm BPP), D-269 (0.300 mm), 0.60 mm BAT_MAIN,
  0.200/0.150 signal, 0.25 hole-hole, D-275/D-288 bridge, In1/In4 GND-only,
  USB/RF/mechanical reservations — all intact. The accepted `AQROOT_U18BPP_JOIN`
  (D-297), `AQROOT_U19CAP` (D-299/G14), `AQROOT_LTCGATE_KO` (D-301/G15),
  `AQROOT_U11_RETARGET` (D-302/G16), the fixture split (G17), `place_003l`
  (D-285), D-275 and D-277..D-303 all preserved; frozen `beta-full-reference-v1`
  untouched. DEVICE_SPEC unchanged (no hardware/product fact changed).
- Shared `phaseA_journal.json` is the authoritative record (77 Phase-A + 3
  REST_INC = 80); no orphan process.

## I — NEXT (FBV2-P2-007)

Continue rest-of-board routing with the next sharply-bounded group via the same
`incremental_router.py` framework (add a group to the registry, `route` → `gate`
→ `promote` on a genuine no-casualty / no-new-DRC increment). Good next
candidates from the measured geometry: the remaining short, isolated
08_BUTTONS_EXPANDERS / 01_POWER_TREE-local / 05_I2C control pairs, then the
short bus segments — deferring the RF/NFC radios, USB, community-header mass and
the GND/+3V3 bulk rails until the framework has more mileage. Promote copper only
on a genuine full-board DRC-clean increment. All floors ENFORCED; D-290 stays
closed.

**PROGRESS EARNED (first rest-of-board copper): PCB routing ~15 %→~16 %, overall
~76 %, readiness ~77 % (JLCPCB file unchanged — a small noncritical increment,
not fab-readiness).**
