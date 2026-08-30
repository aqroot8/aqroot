# FBV2-P2-010 / D-308 — Fifth rest-of-board incremental increment routed + PROMOTED (front-panel RGB status-indicator completion `Net-(D13-RK/GK/BK)`) — the FIRST MULTI-VIA increment

**Date:** 2026-08-30
**Class:** Governed CTO ACCEPT + PROMOTE — routine rest-of-board routing within CTO authority. **No owner decision raised.**
**Starting HEAD:** `c939f35` (D-307; pushed; `origin/master` identical).
**Authoritative PCB:** `sha256 a309f8ce…31279a50` (502 trk / 55 via / 6 layers / 41 zones, ratsnest 693, journal 88) → **`sha256 f4e95decb5be87f6e758f76803e57be68a4437afaef75973518983008559e7ee`** (527 trk / 58 via / 6 layers / 41 zones, ratsnest 690, journal 91).

---

## Summary

The fifth rest-of-board increment is on the authoritative board. The same
`incremental_router.py` (baseline/route/gate/promote), with **zero new
mechanics**, loaded the D-307 promoted board and routed the **front-panel RGB
status-indicator completion** — the three LED-cathode nets `Net-(D13-RK)`,
`Net-(D13-GK)`, `Net-(D13-BK)` — WITHOUT touching a single strand of accepted
Phase-A / FRONT_RGB / ACC / DISP / IMU copper. A real full-board gate proved a
GENUINE no-casualty / no-new-DRC connectivity increment (ratsnest 693→690, DRC
unchanged, **only the In1/In4 GND planes re-poured**, all other 39 zones
byte-identical) → **COPPER PROMOTED.** Autonomy continues; D-275 and D-277..D-307
preserved.

This is a **coherence-maximal** pick and a genuine mechanics milestone:

- **Coherence:** D-304 (`FRONT_RGB`) routed the *expander→resistor* side of the
  front-panel RGB status LED (U23 PCAL9535A GPIO → R124/R125/R126 series limit
  resistors, B.Cu). This increment closes the **same indicator on the
  LED-cathode side** — each series resistor's far pad (R124.2/R125.2/R126.2,
  B.Cu SMD) to the matching cathode of D13 (MHPA3528RGBCT common-anode RGB LED,
  F.Cu SMD). It directly *extends an already-accepted increment* rather than
  bundling unrelated nets — the strongest coherence argument available.
- **Milestone:** it is the **FIRST MULTI-VIA increment.** Each of the three nets
  is a 2-pad CROSS-LAYER net (resistor B.Cu, LED F.Cu) that closes with exactly
  ONE board-legal 0.60/0.30 Default through via — so **three independent vias**
  are laid. This is the single-via-per-edge mechanic proven at D-306
  (`connect_cross`) applied three times, **UNCHANGED**; `refill_planes` re-poured
  In1/In4 ONCE for all three anti-pads. No helper was extended — a multi-net
  group of independent single-via nets is exactly what the existing per-edge
  loop already handles.
- Low current (R-limited 2–6 mA status indicator, non-switching), low
  congestion (6–11 accepted copper items per net bbox+2 mm), all evidence-backed.

---

## A — Group selection (measured; coherent + local + clean, not merely available)

Baseline `a309f8ce…` (502/55/6, ratsnest 693, journal 88). A new READ-ONLY screen
`w/screen_010.py` ranked **all 156 remaining unrouted multi-pad nets** by pad
layers (same-layer vs cross-layer), THT, MST edges/length, **bbox span** (a large
span = long haul = congestion risk) and accepted-copper congestion within
bbox+2 mm, and flagged the D-307 hard walls. The dominant *clean, local,
multi-net* clusters are all in **excluded** categories, which the screen makes
explicit:

| Candidate cluster | Nets | Why excluded / rejected |
|---|---|---|
| **XGPIO0…XGPIO9** (U3 GPIO-expander bank) | 10 | Functionally coherent but **not local** — each net runs from the R51–R60 pack (F.Cu, y≈17–36) to U3 (B.Cu, y≈74–80): ~55 mm cross-board cross-layer hauls. Fails "sharply bounded / local". |
| **NFC front-end** (MATCH/EMC/XIN/XOUT/RFO/RXA/RXB/ANT…) | many | RF/NFC matching + antennas + crystal — **excluded by mandate**. |
| **USB** (D_ESD/D_CONN/D_MCU/VBUS_RAW) | many | USB — **excluded by mandate**. |
| **ACC_5V** boost cluster (LX/FB/SW/RAW/BOOST_EN) | 6 | U21 = TPS61023 **boost (switching)**; `ACC_5V_LX` inductor switch node — excluded; remainder large-span/congested. |
| **IR emitter** `IR_LED_A`/`IR_LED_K` | 2 | The Q1(AO3400A)-switched TSAL6100 IR-LED **drive current** — a switching/high-current output — **excluded**. (`IR_RX_VS_LOCAL` receiver supply is clean but a singleton.) |
| **SPK_P/N / SPK_*_CONN** | 4 | MAX98357A **class-D speaker outputs / connector** — excluded. |
| **XGPIO*_HDR / EXT_* / NATIVE_*_HDR** | many | **community/expansion header (J5/J8) mass routing** — excluded by mandate. |
| **BTN_A/B/UP/DOWN/LEFT/RIGHT_N** | 6 | User buttons SW2–SW7 (F.Cu) → U2 expander (B.Cu): **scattered**, MIX, span 40–66 mm, congested (cu 32–42). Not a local cluster. |
| **U11_PROG**, **PWR_SENSE** | 2+2 | **D-307 characterised hard walls** — excluded from naive retry. |
| **`Net-(D13-RK/GK/BK)`** (FRONT_RGB_LED) | **3** | **SELECTED** — coherent completion of the D-304 indicator, local (span ≤26 mm), clean (cu 6–11), low-current non-switching, three independent single-via cross-layer nets. |

The evidence is decisive: after excluding RF/NFC, USB, crystals/clocks,
switching/high-current, class-D, community-header mass, bulk rails and the two
hard walls, the maximal coherent *clean local* group is the three-net
front-panel-RGB completion. It is preferred to a safe singleton (`RESERVED_SPARE`
B.Cu, `IR_RX_VS_LOCAL` F.Cu) because the mandate wants throughput **beyond**
singletons/two-net clusters and this group is genuinely coherent (one indicator)
— not three unrelated clean nets bundled to hit a count.

## B — Route → gate → promote (one foreground experiment; authoritative untouched)

- **`route FRONT_RGB_LED`** → ALL OK (3/3): `Net-(D13-RK)` D13.4↔R124.2
  (22.532 mm, via@(51.250,96.800)), `Net-(D13-GK)` D13.3↔R125.2 (26.124 mm,
  via@(50.800,98.250)), `Net-(D13-BK)` D13.2↔R126.2 (29.999 mm,
  via@(56.400,103.250)); 25 segments (F.Cu+B.Cu, all 0.200 mm), **3 through vias
  0.60/0.30**; `REFILLED In1/In4 GND plane zones [39,40]` once for the 3
  anti-pads; scratch 527/58; AUTH sha UNCHANGED (`a309f8ce…`).
- **`gate FRONT_RGB_LED`** = **PASS, every check**: no prior copper
  deleted/altered (D-307 502 trk + 55 via multiset is a SUBSET); 28 new items
  (25 trk + 3 via), all target-net; **only In1/In4 (zones 39,40) fill-changed,
  all other 39 zones byte-identical** (net/layers/priority + filled-poly count);
  all three D13 nets fully connected (open edges 1→0 each); 0 prior requested
  pairs regressed; ratsnest 693→690 EXACTLY −3; no new/worse DRC class;
  `unconnected_items` 499→499.
- **`promote FRONT_RGB_LED`** re-ran the gate (PASS), re-verified the AUTH sha
  had not drifted (`a309f8ce…`), copied scratch→authoritative and merged the 3
  route entries as `role=REST_INC`.

## C — What is promoted (integrity)

Authoritative `sha256 a309f8ce…31279a50` → **`f4e95dec…8559e7ee`**; tracks
**502→527** (+25 D13-cathode); vias **55→58** (+3 through vias); 6 layers / 41
zones unchanged; ratsnest **693→690** (−3); journal **88→91** (+3 `REST_INC`).
PCB file diff = **352 insertions / 59 deletions**; the additions are 25 `segment`
+ 3 `via` lines (grep-confirmed **0 `segment`/`via`/`footprint` deletions**), and
all 59 deletions are `(xy …)` point lines inside the **In1/In4 GND plane
`filled_polygon`** re-pour (the three via anti-pads) — the sanctioned via
re-pour, nothing else. Real KiCad DRC **identical**
(`{solder_mask_bridge:1, hole_clearance:5, lib_footprint_issues:199,
unconnected_items:499}`) — 0 clearance, `hole_clearance` unchanged at 5, and **0
violations touch the D13/FRONT_RGB_LED copper** (verified on the promoted board).
Every 432 Phase-A + 20 FRONT_RGB + 31 ACC + 11 DISP + 8 IMU track and all 55
prior vias present byte/geometry-identical; only new copper is the 25 D13
F.Cu+B.Cu tracks and 3 vias. No placement/DRU/netclass/footprint/value/polarity/
outline/stackup change.

## D — Tests

New contract **G22** pins the increment (all three D13 nets connected across
their F/B hop = D13.4-R124.2, D13.3-R125.2, D13.2-R126.2; copper legal = 25 trk
F.Cu+B.Cu 0.200 mm + **three 0.60/0.30 through vias, one per net**; ADD-ONLY =
IMU 8 + DISP 11 + ACC 31 + RGB 20 + Phase-A 432/54). G18–G21 stay green
unchanged — their ADD-ONLY invariants exclude ALL `role=REST_INC` nets
generically and pin `phaseA_via`==54 (add-only via count), so they auto-generalise
as the board's total via count grows 55→58. `router_regression.py` = **ALL CHECKS
PASS (G1–G22), 94 PASS lines, 0 failed**, run twice, deterministic.

New focused probe `incremental_probe_010.py` (READ-ONLY: D-308 fingerprints;
pre-D-308 copper preserved exactly = 502 trk + 55 via; 25-track F+B increment
with 3 through vias; all three D13 nets connected; no pair regressed; DRC
unchanged) ALL PASS. `incremental_probe_006/007/008/009.py` refreshed to the
D-308 board (each still proving its own net intact; `_009`'s "pre-IMU copper"
check generalised to exclude post-IMU increments so it stays green as the board
grows) ALL PASS. `phaseB_bringup_probe_005.py` updated (527/58/91; accepted-
increment set + the three D13 cathode nets; 164 rest nets, **10 routed, 154
unrouted**) ALL PASS.

**Phase-A DRU-synthesis probes (`d269_probe`, `d264_probe`, `dru_probe`) — NOT
part of the maintained increment regression, and NOT regressed by D-308.**
`dru_probe` (2 fails) and `d264_probe` (1 fail, check B) carry the **same
pre-existing reds on the pristine HEAD board** as on D-308 — unchanged.
`d269_probe` C/D is a **flaky borderline**: it injects synthetic BAT_MAIN test
tracks and re-pours *all* zones with KiCad's `ZONE_FILLER` (which — per the D-306
finding — is NOT byte-reproducible), then measures a clearance delta. On repeated
runs it reports a 0.275 mm clearance between **two remote Phase-A items** — an
existing `LTC_GATE` via at (5–8, 60–65) mm and a `BAT_RAW` In2.Cu zone track — on
**HEAD as well as D-308** (my copper is 45 mm away and cannot affect that fill).
The real authoritative board (byte-stable stored fill) is DRC-clean with 0
clearance violations; the flip is a synthetic full-zone-re-pour artifact of a
pre-existing marginal Phase-A spacing, not a D-308 defect. No rule was touched.

## E — Opportunity & Simplification Scan (mandated)

The framework held with **zero new mechanics**. The FIRST multi-via increment
required NO change to `connect_cross`/`refill_planes`/`qrouter.py`: the existing
per-edge loop calls `connect_cross` once per cross-layer edge (three times here)
and `refill_planes` re-pours In1/In4 once for however many vias were laid — a
multi-net group of independent single-via nets is already within the proven
mechanic. The mandated "extend only if genuinely forced" bar was therefore NOT
crossed (no single net forced multiple series vias, a via array, or an In2/In3
inner-signal traverse); the helper was left untouched.

*Simplification observation for future increments (not acted on this cycle to
avoid weakening historical contracts):* the four prior probes now share an
identical five-line `EXPECT_{SHA,TRACKS,VIAS,JOURNAL,RATSNEST}` refresh and an
identical "pre-X copper" generalised-preservation idiom (`PRE_*_GROUPS` exclusion
+ the durable `phaseA==432+54` check). When a sixth increment lands, these four
files could fold their fingerprint constants into one shared
`incremental_fingerprints.py` and their preservation check into one helper,
cutting the per-increment probe edit from "touch 4–5 files" to "append one row".
The G-contract series (G18…G22) is already fully generalised (ADD-ONLY excludes
all REST_INC nets) and needs only its own new block per increment. **Larger
coherent batches are justified going forward** — this increment shows a 3-net /
3-via group gates cleanly — but only where locality + cleanliness hold; the
board's remaining clean local multi-net clusters are mostly in excluded
categories, so batch *size* will stay evidence-limited, not framework-limited.
No BOM/recoverability/testability/firmware/UX/mechanical change forced; In2/In3
remain spare capacity. **Open owner decisions: NONE.**

## F — Integrity & rollback

Rollback = pre-promotion `sha256 a309f8ce…31279a50` (D-307; parent `c939f35`;
restored by `git checkout` of the PCB + journal; the D-302/D-304/D-305/D-306/D-307
rollback points still stand). All locked invariants preserved: no
DRU/rule/clearance/stackup/topology/net/footprint/value/polarity/outline change;
no D-290 reauth; NO via below the D-257 ladder (the three vias are 0.60/0.30
Default through vias ≥ the 0.50 mm `min_via_diameter`); D-249 (≥1.20 mm BPP),
D-269 (0.300 mm), 0.60 mm BAT_MAIN, 0.200/0.150 signal, 0.25 hole-hole,
D-275/D-288 bridge, **In1/In4 GND roles** (only these two planes re-poured, for
the via anti-pads; every other zone byte-identical), USB/RF/mechanical
reservations ENFORCED; `AQROOT_U18BPP_JOIN` (D-297), `AQROOT_U19CAP` (D-299/G14),
`AQROOT_LTCGATE_KO` (D-301/G15), `AQROOT_U11_RETARGET` (D-302/G16), fixture split
(G17), FRONT_RGB (G18/D-304), ACC_3V3_CTL (G19/D-305), DISP_RST_N (G20/D-306),
IMU_ADDR (G21/D-307), `place_003l` (D-285), D-275 and D-277..D-307 preserved;
frozen `beta-full-reference-v1` untouched; DEVICE_SPEC unchanged (no hardware
fact changed); shared journal authoritative (91 entries); no orphan process.

## G — Next: FBV2-P2-011

Continue rest-of-board routing via the same framework (**154 of 164 rest nets
unrouted**). Same-layer (B.Cu/F.Cu), single-via and now **multi-via** cross-layer
groups are all proven; multi-terminal MST proven. Good next low-risk candidates
(screen with `w/screen_010.py`): the U23-local `RESERVED_SPARE` B.Cu 3-pad spare;
short IR-receiver / audio-control non-switching straps (`IR_RX_VS_LOCAL`,
`AMP_SD_MODE`, screen THT/analog first); other short single-via mixed-layer
controls (`TOUCH_RST_N`, `TOUCH_INT_N`, `SD_CARD_DETECT_N`). **Still avoid**
re-attempting `U11_PROG`/`PWR_SENSE` (hard walls) without a placement micro-move
or deliberate multi-via escape; RF/NFC/USB/crystals/community-header/rails/
switching/class-D remain deferred. The XGPIO0…9 bank is a real 10-net coherent
target but only if a **long cross-board cross-layer haul** is accepted — screen
its corridor before committing. The first increment needing MULTIPLE **series**
vias on ONE net / a via array / an In2/In3 inner-signal traverse must extend
`connect_cross`/`refill_planes` deliberately (the current helper handles N
independent single-via nets + the In1/In4 re-pour, which is all this increment
needed).

**PROGRESS EARNED (fifth rest-of-board increment promoted; first multi-via): PCB routing ~18 %→~18 %, overall ~76 %, readiness ~77 % (JLCPCB file unchanged — a small noncritical increment, not fab-readiness).**
