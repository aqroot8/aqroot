# FBV2-P2-007 / D-305 — Second rest-of-board incremental increment: the ACC_3V3_CTL accelerometer-3V3 load-switch control group routed and PROMOTED

**Date:** 2026-08-30
**Task:** FBV2-P2-007 — next sharply-bounded incremental rest-of-board routing group
**Decision:** **D-305**
**Result:** **A GOVERNED CTO ACCEPT + PROMOTE.** A second rest-of-board net-group is on the
authoritative board: the reusable incremental router/promoter (`incremental_router.py`)
loaded the D-304 promoted board, routed the ACC_3V3_CTL group **without touching a single
strand of accepted Phase-A or FRONT_RGB copper**, and a real full-board gate proved a
genuine no-casualty / no-new-DRC connectivity increment. Copper PROMOTED. Autonomy
CONTINUES; **no owner decision raised.**

Starting HEAD `6353bd7` (D-304; pushed; `origin/master` identical).

---

## A — THE OBJECTIVE

D-304 delivered the reusable incremental framework and took the first increment (FRONT_RGB).
161 of the 164 rest-of-board multi-pad nets remained unrouted. FBV2-P2-007 takes the next
bounded increment through the same `route → gate → promote` discipline, adding framework
mileage while staying strictly within CTO routing authority.

## B — GROUP SELECTION (measured, not convenient)

Current authoritative geometry was measured first (`incremental_router.py baseline`: sha
`00c93bdb…`, 452 trk / 54 via / 6 layers, ratsnest 701, journal 80, DRC
`{smb1, hc5, lib199, unc499}`), then candidate groups were screened for pad geometry (MST
edges), layer/THT, and — crucially — Phase-A copper congestion within each group's bounding
box (`w/screen_007.py`, READ-ONLY).

- **CHOSEN — ACC_3V3_CTL (accelerometer 3V3 load-switch U20 local control):** two nets,
  `ACC_3V3_EN` (enable: U3.15 → R98/U20.1/TP26, a **4-pad multi-terminal** net, 3-edge MST)
  and `ACC_3V3_ILIM` (current-limit set: R97 → U20.4). Both **Default netclass (0.200 mm
  width / 0.200 mm clearance, NO via), all B.Cu SMD**, a coherent standalone power-gating
  control subsystem in a **low-congestion region** (only 4 Phase-A B.Cu strands within
  bbox + 2 mm; no In-layer or via conflict). Electrically **noncritical low-current control**
  (a static enable line + a µA set-resistor strap) — no rail/RF/USB/high-current/switch-node/
  clock/crystal constraint. It satisfies the "prefer 2–6 nets" preference AND adds a
  **materially new routing primitive vs FRONT_RGB**: the first promoted increment to exercise
  **multi-segment MST routing** (FRONT_RGB's three nets were all single-edge 2-pad).
- **REJECTED — IMU_STRAP (`BMI270_SDO_ADDR`, U4):** the single cleanest region (3-pad, 0
  Phase-A copper within bbox + 2 mm) but only ONE net; kept as the bounded evidence-backed
  fallback had the ACC route failed.
- **REJECTED — PWR_SENSE (`VBUS_PRESENT` + `MAX17048_ALRT_N`):** coherent west power-monitoring
  pair but **12 Phase-A copper items within bbox + 2 mm** (the congested west battery-
  management region) — higher route-interaction risk; deferred.
- **REJECTED — U11_PROG (`ILIM_VSET` + `ISET`):** U11 charge-current programming straps but
  **16 Phase-A B.Cu items in bbox** — the D-302 U11.2 BPP trunk wall region, the most
  congested candidate; deferred, and it adds no multi-terminal mileage (both 2-pad).
- **REJECTED — AUDIO_SPK (`SPK_P/N`, `SPK_P/N_CONN`):** the full speaker path, but F.Cu with
  THT (J6) pads and analog amp outputs near the mic keepout — higher electrical sensitivity;
  deferred until the framework deliberately exercises F.Cu/THT.
- **REJECTED — DISP_RST (`DISP_RST_N`):** a MIX-layer net (F↔B) requiring a via — defers to
  the D-257 via ladder discipline; multilayer/via routing is saved for when a group forces it.
- **EXCLUDED per mandate** — 09_COMMUNITY_HEADER mass, 04_SPI_B_RADIOS_NFC (RF/NFC), USB,
  crystals, GND/+3V3 bulk rails.

## C — THE EXPERIMENT (one foreground run)

```
python3 incremental_router.py baseline           # 452/54/6, ratsnest 701, DRC {smb1,hc5,lib199,unc499}
python3 incremental_router.py route   ACC_3V3_CTL # 4/4 ok; scratch 483 trk / 54 via; AUTH sha unchanged
python3 incremental_router.py gate    ACC_3V3_CTL # PASS (0 checks failed)
python3 incremental_router.py promote ACC_3V3_CTL # gate re-run PASS -> promoted
```

- Routed (all 0.200 mm B.Cu, **0 vias**): `ACC_3V3_EN` R98.1→U20.1 5.761 mm, R98.1→TP26.1
  9.715 mm, TP26.1→U3.15 10.877 mm (3-edge MST); `ACC_3V3_ILIM` R97.1→U20.4 14.033 mm
  (a legal detour around the local pad field). 31 new track segments (ACC_3V3_EN 20,
  ACC_3V3_ILIM 11).
- **GATE = PASS, every check:** Phase-A/FRONT_RGB copper 0 missing; 31 new items, all
  target-net; both nets fully connected (ACC_3V3_ILIM 1→0, ACC_3V3_EN 3→0); 0 prior requested
  pairs regressed; ratsnest 701→697 (exactly −4); no new DRC class; no class increased;
  `unconnected_items` 499→499.

## D — WHAT IS PROMOTED (integrity)

| | pre (D-304) | post (D-305) |
|---|---|---|
| authoritative sha256 | `00c93bdb…dfb72aad` | `f0046eb7…04c7cd41` |
| tracks | 452 | **483** (+31 ACC_3V3_CTL) |
| vias | 54 | **54** (no new via) |
| copper layers / zones | 6 / 41 | 6 / 41 |
| ratsnest | 701 | **697** (−4) |
| journal entries | 80 | **84** (+4 `REST_INC`) |
| real KiCad DRC | `{smb1, hc5, lib199, unc499}` | **identical** |

The board diff is **248 insertions / 0 deletions** in the `.kicad_pcb` (31 new B.Cu track
segments, no line of existing copper altered) and **44 / 0** in the journal (4 `REST_INC`
entries) — ADD-ONLY confirmed at the file level as well as by the gate's copper-superset
check. Every one of the 432 Phase-A tracks, 20 FRONT_RGB tracks and 54 vias is present,
byte/geometry-identical. No placement / DRU / netclass / footprint / value / polarity /
outline / stackup change.

## E — TESTS & REGRESSION CONTRACTS

- **New contract G19** in `router_regression.py` pins the increment on the authoritative
  board: (1) the two ACC nets are fully copper-connected (`GetConnectedItems`), (2) their
  copper is legal (0.200 mm B.Cu, NO via), (3) the increment is ADD-ONLY (FRONT_RGB still 20
  tracks, Phase-A still 432, vias 54, ACC exactly 31).
- **G18 generalised (no behaviour change to its FRONT_RGB claims):** its ADD-ONLY count now
  derives the Phase-A set by excluding **all** journal `role=REST_INC` nets (not just
  FRONT_RGB), so the "Phase-A == 432 trk / 54 via" pin stays true as later increments are
  promoted. `router_regression.py` = **ALL 86 CHECKS PASS (G1–G19)**, run twice, deterministic.
- **New focused probe** `incremental_probe_007.py` (READ-ONLY): re-proves on the live board
  the D-305 fingerprints, prior-copper-preserved-exactly (the D-304 452 trk + 54 via set is a
  subset), the two nets connected, no prior pair regressed, DRC unchanged. ALL PASS.
- **`incremental_probe_006.py`** (the FRONT_RGB live-invariant probe) refreshed to the D-305
  board and its Phase-A-preservation check generalised (exclude all `REST_INC` nets); ALL PASS.
- **`phaseB_bringup_probe_005.py`** (the live integrity/inventory probe) updated to the
  promoted state (483 trk / journal 84; accepted-increment set now FRONT_RGB + ACC_3V3_CTL;
  inventory: 164 rest nets, 5 routed, 159 unrouted). ALL PASS.

## F — OPPORTUNITY & SIMPLIFICATION SCAN (mandated)

- **The framework held with zero new mechanics.** ACC_3V3_CTL needed only a new `GROUPS`
  registry entry — no change to the router, gate or promoter. The multi-terminal net
  (ACC_3V3_EN, 4 pads / 3 MST edges) routed and gated through the existing Prim-MST path,
  so the framework is proven for multi-segment nets, not just 2-pad pairs.
- **No generic need for multilayer/via/bus/transaction semantics yet.** This group is single-
  layer B.Cu, no via, and each net is independently gated; the whole-board gate (D-286) would
  surface any cross-group coupling as a DRC/ratsnest delta — none occurred. Deliberately
  **not** generalised prematurely: MIX-layer/via routing (DISP_RST) and F.Cu/THT (AUDIO_SPK)
  were left for the increment that actually forces them, so the via/D-257 discipline and
  layer-selection mechanics are introduced against a concrete need, not speculatively.
- **Group-transaction semantics:** the current per-group promote is sufficient; no evidence
  yet that a multi-group atomic transaction is needed (each group is small and independently
  reversible). Revisit only if a future subsystem's nets are mutually blocking.
- **BOM / recoverability / testability / firmware / UX / mechanical:** no opportunity or
  constraint forces a change — a noncritical accelerometer-power control pair with no
  footprint/outline/stackup/silk/firmware surface. The six-layer stack's bare inner In2/In3
  remain spare capacity for future congested groups.
- **No irreversible cost, no strategic fork. Open owner decisions: NONE.**

## G — INTEGRITY & ROLLBACK

- Pre-promotion authoritative PCB `sha256 00c93bdb…dfb72aad` (D-304; parent `6353bd7`) is the
  rollback point — restored by `git checkout <parent> -- <pcb>` (+ the journal). The D-302
  rollback tags still stand.
- All locked invariants preserved: no DRU/rule/clearance/stackup/topology/net/footprint/value/
  polarity/outline change; no D-290 reauthorization; no via below the D-257 ladder; D-249
  (≥1.20 mm BPP), D-269 (0.300 mm), 0.60 mm BAT_MAIN, 0.200/0.150 signal, 0.25 hole-hole,
  D-275/D-288 bridge, In1/In4 GND-only, USB/RF/mechanical reservations — all intact. The
  accepted `AQROOT_U18BPP_JOIN` (D-297), `AQROOT_U19CAP` (D-299/G14), `AQROOT_LTCGATE_KO`
  (D-301/G15), `AQROOT_U11_RETARGET` (D-302/G16), the fixture split (G17), the D-304 FRONT_RGB
  increment (G18), `place_003l` (D-285), D-275 and D-277..D-304 all preserved; frozen
  `beta-full-reference-v1` untouched. DEVICE_SPEC unchanged (no hardware/product fact changed).
- Shared `phaseA_journal.json` is the authoritative record (77 Phase-A + 3 FRONT_RGB + 4
  ACC_3V3_CTL = 84); no orphan process.

## H — NEXT (FBV2-P2-008)

Continue rest-of-board routing with the next sharply-bounded group via the same
`incremental_router.py` framework. From the measured geometry, good low-risk B.Cu candidates
remain: the **IMU_STRAP `BMI270_SDO_ADDR`** singleton (0 nearby copper, a clean 3-pad closer),
short isolated 08_BUTTONS_EXPANDERS controls (e.g. `RESERVED_SPARE`), or the west
**PWR_SENSE** pair once its congestion is characterised. The first increment that *forces*
multilayer/via routing (e.g. a MIX-layer net such as `DISP_RST_N`) should introduce the
via/D-257 discipline into the framework deliberately. Defer RF/NFC/USB/community-header mass
and the GND/+3V3 bulk rails until the framework has more mileage. Promote copper only on a
genuine full-board DRC-clean, no-casualty increment. All floors ENFORCED; D-290 stays closed.

**PROGRESS EARNED (second rest-of-board increment): PCB routing ~16 %→~17 %, overall ~76 %,
readiness ~77 % (JLCPCB file unchanged — a small noncritical increment, not fab-readiness).**
