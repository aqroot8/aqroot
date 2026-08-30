# FBV2-P2-008 / D-306 — Third rest-of-board incremental increment: the DISP_RST_N display-reset control net (first F.Cu run + first cross-layer through via) routed and PROMOTED

**Date:** 2026-08-30
**Task:** FBV2-P2-008 — next sharply-bounded incremental rest-of-board routing group, preferably exercising the next safe routing primitive
**Decision:** **D-306**
**Result:** **A GOVERNED CTO ACCEPT + PROMOTE.** A third rest-of-board net is on the
authoritative board and — for the first time — the increment exercises a **via / mixed-layer
route**. The reusable incremental router/promoter (`incremental_router.py`) loaded the D-305
promoted board, routed `DISP_RST_N` with a pure-F.Cu run and one board-legal F↔B through via,
re-poured **only** the In1/In4 GND planes to open the via's anti-pad, and a real full-board
gate proved a genuine no-casualty / no-new-DRC connectivity increment. Copper PROMOTED.
Autonomy CONTINUES; **no owner decision raised.**

Starting HEAD `c22b9fd` (D-305; pushed; `origin/master` identical).

---

## A — THE OBJECTIVE

D-304/D-305 delivered the reusable incremental framework and took two increments (FRONT_RGB,
ACC_3V3_CTL), **both B.Cu / no-via**. FBV2-P2-008 takes the next bounded increment through the
same `route → gate → promote` discipline AND deliberately introduces one genuinely useful new
routing primitive: a **controlled mixed-layer route with a board-legal via** (plus a pure-F.Cu
run), against a concrete need rather than speculatively.

## B — GROUP SELECTION (measured, not convenient)

Current authoritative geometry was measured first (`incremental_router.py baseline`: sha
`f0046eb7…`, 483 trk / 54 via / 6 layers, ratsnest 697, journal 84, DRC `{smb1, hc5, lib199,
unc499}`), then candidate groups were screened for pad geometry, layer/THT, and Phase-A copper
congestion within each group's bounding box (`w/screen_007.py`, READ-ONLY).

- **CHOSEN — DISP_RST (`DISP_RST_N`, display-reset control):** one 3-pad net whose pads do
  **not** all share a layer — `R16.1` and `J1.10` are F.Cu SMD, `U2.8` is B.Cu SMD. Its MST is
  one **SAME-LAYER edge** (`R16.1↔J1.10`, a pure F.Cu run — the **first incremental F.Cu
  route**) and one **CROSS-LAYER edge** (`J1.10↔U2.8`, closed by **one board-legal F↔B through
  via** — the **first incremental via / mixed-layer route**). The via is the **Default
  netclass** geometry the DRC enforces here: **0.60 mm diameter / 0.30 mm drill** (≥ the
  0.50 mm `min_via_diameter` and 0.30 mm drill floor — **not a microvia, not a via-in-pad**).
  **Low congestion** (only 2 Phase-A copper items within bbox + 2 mm). Electrically
  **noncritical low-speed control** (a reset line) — no rail/RF/USB/high-current/switch-node/
  clock/crystal constraint. It satisfies the mandate to add a **materially distinct primitive**
  vs the two B.Cu increments.
- **REJECTED — AUDIO_SPK (`SPK_P/N`, `SPK_P/N_CONN`):** geometrically isolated (0 nearby
  copper) and would exercise F.Cu + THT (J6) at once, BUT `SPK_P/N` are **class-D amplifier
  outputs** — switching nodes with EMI/return-path sensitivity the mandate explicitly excludes
  ("switching/high-current paths"); a generic autorouted F.Cu run is electrically
  inappropriate. Deferred until a group needs THT without switching sensitivity.
- **REJECTED — U11_PROG (`ILIM_VSET` + `ISET`):** U11 (LTC4368/DLH0010A) current-limit
  programming straps, **16 Phase-A items in bbox** and electrically coupled to the
  safety-critical BPP protection path — highest interaction risk; deferred.
- **REJECTED — PWR_SENSE (`VBUS_PRESENT` + `MAX17048_ALRT_N`):** west power-monitoring pair
  against the U14 fuel-gauge west-edge mechanical strip, **12 Phase-A items in bbox** (congested
  west region) — higher risk, no new primitive; deferred.
- **FALLBACK held (not needed) — IMU_STRAP (`BMI270_SDO_ADDR`):** the cleanest B.Cu singleton
  (0 nearby copper) was kept as the simple-B.Cu fallback per mandate, to be taken only if every
  new-primitive candidate were disproven. DISP_RST was **not** disproven, so the fallback stays
  a future increment.
- **EXCLUDED per mandate** — 09_COMMUNITY_HEADER mass, 04_SPI_B_RADIOS_NFC (RF/NFC), USB,
  crystals, GND/+3V3 bulk rails.

## C — THE EXPERIMENT (one foreground run) + THE NEW-PRIMITIVE BLOCKER, CHARACTERISED

```
python3 incremental_router.py baseline          # 483/54/6, ratsnest 697, DRC {smb1,hc5,lib199,unc499}
python3 incremental_router.py route   DISP_RST   # 2/2 ok; scratch 494 trk / 55 via; AUTH sha unchanged
python3 incremental_router.py gate    DISP_RST   # PASS (0 checks failed)
python3 incremental_router.py promote DISP_RST   # gate re-run PASS -> promoted
```

- Routed: `DISP_RST_N` `R16.1↔J1.10` **10.881 mm on F.Cu** (0.200 mm, no via); `J1.10↔U2.8`
  **18.081 mm** as a cross-layer route — F.Cu run + **one 0.60/0.30 through via at
  (52.950, 87.000)** (beside U2.8) + short B.Cu stub into U2.8. **11 new track segments +
  1 via.**
- **THE FIRST-VIA BLOCKER, MEASURED AND RESOLVED (not brute-forced):** the through via is
  copper on all six layers, so it pierces the **In1.Cu and In4.Cu GND reference planes**. On
  first gate the via was legally clear of every track/pad (via placed via `QBoard.via_site`,
  which enforces all-layer clearance + net-agnostic hole-to-hole), but the **stale plane fill**
  (poured before the via existed) had no anti-pad, so DRC reported **`clearance` ×2 +
  `hole_clearance` ×2** at (52.95, 87.0) against the In1/In4 GND zones (actual 0.000 mm). The
  fix is the standard, necessary one: **re-pour the two penetrated GND planes** to carve the
  anti-pad. Focused evidence bounded the re-pour: a plain refill of the authoritative board
  drifts **only** zones 39/40 (In1/In4 GND, +35 poly-points each — a stored-vs-current
  `ZONE_FILLER` discrepancy independent of the via) and **no other zone**; the F.Cu/B.Cu GND
  pours and all 39 other zones are refill-stable. So `route` now re-pours **exactly** In1/In4
  when (and only when) a via was laid; DRC returns to baseline **identically**.
- **GATE = PASS, every check:** Phase-A copper 0 missing; 12 new items (11 trk + 1 via), all
  target-net; **only In1/In4 GND planes re-poured, all other 39 zones identical**; DISP_RST_N
  fully connected across the hop (open edges 2→0); 0 prior requested pairs regressed; ratsnest
  697→695 (exactly −2); no new DRC class; no class increased; `unconnected_items` 499→499.

## D — WHAT IS PROMOTED (integrity)

| | pre (D-305) | post (D-306) |
|---|---|---|
| authoritative sha256 | `f0046eb7…04c7cd41` | `9c0586d8…e3f62259` |
| tracks | 483 | **494** (+11 DISP_RST_N) |
| vias | 54 | **55** (+1 F↔B cross-layer through via) |
| copper layers / zones | 6 / 41 | 6 / 41 |
| ratsnest | 697 | **695** (−2) |
| journal entries | 84 | **86** (+2 `REST_INC`) |
| real KiCad DRC | `{smb1, hc5, lib199, unc499}` | **identical** |

The `.kicad_pcb` diff is **470 insertions / 336 deletions**. The insertions are the 11 new
F.Cu/B.Cu track segments, the one via, and the re-poured In1/In4 plane polygons; **all 336
deletions are In1/In4 `filled_polygon` xy content** (the plane re-pour) — **zero deleted
`segment`, `via` or `footprint` lines**, confirmed by grep. Every one of the 432 Phase-A + 20
FRONT_RGB + 31 ACC_3V3_CTL tracks and all 54 prior vias is present byte/geometry-identical (the
gate's copper-superset check). No placement / DRU / netclass / footprint / value / polarity /
outline / stackup change; the two GND planes keep their net, layer, priority and clearance —
**only their fill polygons update** to carry the via anti-pad, proven DRC-neutral.

## E — TESTS & REGRESSION CONTRACTS

- **New contract G20** in `router_regression.py` pins the increment on the authoritative board:
  (1) `DISP_RST_N` is fully copper-connected across the F/B hop (`J1.10` joined to both `R16.1`
  and `U2.8`), (2) its copper is legal — 11 tracks spanning **F.Cu AND B.Cu** at 0.200 mm with
  **exactly one 0.60/0.30 through via**, (3) the increment is ADD-ONLY (RGB 20, ACC 31, Phase-A
  432 trk / 54 via all preserved).
- **G18/G19 generalised (no behaviour change to their claims):** their ADD-ONLY via count now
  pins **`phaseA_via` = 54** (vias not owned by any `REST_INC` net) instead of `all_via == 54`,
  so the Phase-A-vias-preserved pin stays green as increments add their own vias (D-306 is the
  first, +1). `router_regression.py` = **ALL 89 CHECKS PASS (G1–G20)**, run twice, deterministic.
- **New focused probe** `incremental_probe_008.py` (READ-ONLY): re-proves on the live board the
  D-306 fingerprints, prior-copper-preserved-exactly (the D-305 483 trk + 54 via set is a
  subset), DISP_RST_N spanning F.Cu + B.Cu with one legal 0.60/0.30 through via, full
  cross-hop connectivity, no prior pair regressed, DRC unchanged. ALL PASS.
- **`incremental_probe_006/007.py`** (the FRONT_RGB / ACC live-invariant probes) refreshed to
  the D-306 board; `_007`'s prior-copper check generalised to exclude all `REST_INC` nets so it
  stays green under later increments. ALL PASS.
- **`phaseB_bringup_probe_005.py`** (the live integrity/inventory probe) updated to the promoted
  state (494 trk / 55 via / journal 86; accepted-increment set now FRONT_RGB + ACC_3V3_CTL +
  DISP_RST_N; inventory: 164 rest nets, **6 routed, 158 unrouted**). ALL PASS.

## F — OPPORTUNITY & SIMPLIFICATION SCAN (mandated)

- **What the first via increment truly needed — and nothing more.** The framework gained
  exactly three generic mechanics, each forced by a concrete need: (1) a **per-edge layer
  decision** (`edge_plan`) — same-layer edges route on the shared layer (so all-B / all-F /
  THT groups are unchanged and byte-identical), cross-layer edges get a via; (2) a
  **`connect_cross`** helper that composes only proven `qrouter` primitives
  (`escape` → `via_site` → `via` → two anchored `connect_role` runs) — **no change to
  `qrouter.py`**, so the load-bearing battery driver is untouched; (3) a **`refill_planes`**
  step that re-pours only the In1/In4 GND planes when a via was laid. Per-group `via_dia`/
  `via_drill` metadata was added to `GROUPS`; groups without it (the B.Cu ones) never hit the
  via path. **Deliberately NOT generalised:** no via-ladder abstraction, no blind/buried/
  microvia path, no multi-via arrays — those await the increment that forces them.
- **The gate already handled vias generically** (`_via_sig` fingerprint; ratsnest-drop by net
  open-edges) — only a **zone-preservation proof** had to be added: every zone's identity
  (net/layers/priority) unchanged and only the In1/In4 plane **fill** may move. This is the
  right altitude: the gate proves the re-pour is surgical without hard-coding the drift.
- **The zone re-pour is a genuine finding, transparently bounded.** Unlike the B.Cu increments
  (byte-clean, 0 deletions), a plane-piercing via forces a plane re-pour; the stored plane fill
  is not byte-reproducible by the current `ZONE_FILLER`, so plane byte-equality is **not**
  claimed — DRC-neutrality + "only In1/In4 changed" is the promotable standard, proven.
- **BOM / recoverability / testability / firmware / UX / mechanical:** no opportunity or
  constraint forces a change — a noncritical display-reset line with no footprint/outline/
  stackup/silk/firmware surface. Inner In2/In3 signal layers remain spare for congested groups.
- **No irreversible cost, no strategic fork. Open owner decisions: NONE.**

## G — INTEGRITY & ROLLBACK

- Pre-promotion authoritative PCB `sha256 f0046eb7…04c7cd41` (D-305; parent `c22b9fd`) is the
  rollback point — restored by `git checkout <parent> -- <pcb>` (+ the journal). The D-302/
  D-304/D-305 rollback points still stand.
- All locked invariants preserved: no DRU/rule/clearance/stackup/topology/net/footprint/value/
  polarity/outline change; no D-290 reauthorization; **no via below the D-257 ladder** (the
  0.60/0.30 through via is the Default netclass geometry, ≥ 0.50 mm `min_via_diameter`); D-249
  (≥1.20 mm BPP), D-269 (0.300 mm), 0.60 mm BAT_MAIN, 0.200/0.150 signal, 0.25 hole-hole,
  D-275/D-288 bridge, **In1/In4 GND roles** (the planes stay GND — only their fill re-poured to
  carry the via anti-pad), USB/RF/mechanical reservations — all intact. `AQROOT_U18BPP_JOIN`
  (D-297), `AQROOT_U19CAP` (D-299/G14), `AQROOT_LTCGATE_KO` (D-301/G15), `AQROOT_U11_RETARGET`
  (D-302/G16), the fixture split (G17), FRONT_RGB (G18/D-304), ACC_3V3_CTL (G19/D-305),
  `place_003l` (D-285), D-275 and D-277..D-305 all preserved; frozen `beta-full-reference-v1`
  untouched. DEVICE_SPEC unchanged (no hardware/product fact changed).
- Shared `phaseA_journal.json` is the authoritative record (77 Phase-A + 3 FRONT_RGB + 4
  ACC_3V3_CTL + 2 DISP_RST = 86); no orphan process.

## H — NEXT (FBV2-P2-009)

Continue rest-of-board routing with the next sharply-bounded group via the same
`incremental_router.py` framework. **158 of 164 rest nets remain unrouted.** The via/mixed-layer
primitive is now proven, so both same-layer and single-via cross-layer groups are routable.
Good low-risk candidates: the **IMU_STRAP `BMI270_SDO_ADDR`** B.Cu singleton (0 nearby copper,
the held fallback), short isolated 08_BUTTONS_EXPANDERS controls, or another short mixed-layer
control net. The next increment to need **multiple vias / a via array / an inner-signal-layer
(In2/In3) traverse** should extend `connect_cross`/`refill_planes` for that case deliberately
(the current helper handles exactly one via and re-pours exactly the In1/In4 GND planes). Defer
RF/NFC/USB/community-header mass and the GND/+3V3 bulk rails. Promote copper only on a genuine
full-board DRC-clean, no-casualty increment. All floors ENFORCED; D-290 stays closed.

**PROGRESS EARNED (third rest-of-board increment; first via/mixed-layer primitive): PCB routing
~17 %→~18 %, overall ~76 %, readiness ~77 % (JLCPCB file unchanged — a small noncritical
increment, not fab-readiness).**
