# FBV2-P2-014 / D-312 — Ninth rest-of-board incremental increment ROUTED + PROMOTED: microSD card-detect `SD_CARD_DETECT_N` (the last D-309 U2 escape sibling), separately governed

**Date:** 2026-08-30
**Decision:** D-312 (governed CTO ACCEPT + PROMOTE; routine rest-of-board routing within CTO authority — no owner decision)
**Starting HEAD:** `288d7adbb774d7ccd2b12a9a7b0725de9f45d767` (D-311; pushed; `origin/master` identical)
**Pre-promotion PCB:** `sha256 9bf429cec07654d4522121d2fb595204d06f5173ae629f2292c4d0cb9f68b314` — 580 tracks / 61 vias / 6 layers / 41 zones / ratsnest 683 / journal 98
**Promoted PCB:** `sha256 d6e0148a43a42895236b934cb6f7084036e50535a399f42fe09b300aabc5f1b8` — **608 tracks / 62 vias / 6 layers / 41 zones / ratsnest 681 / journal 100**

## Summary

`SD_CARD_DETECT_N` — the microSD socket J2 card-detect switch line (J2.10/R113.2 on F.Cu → U2.11 on B.Cu; noncritical low-speed detect) — is routed and promoted as its **own** increment. It is the SECOND of the two remaining U2 west-edge escape siblings the D-310 via-offset unlocked, and the **last** net of the D-309-characterised U2 escape family. D-311 promoted the sibling `AMP_SD_MODE` alone and deliberately **held** `SD_CARD_DETECT_N` for a separately-governed increment (the two are functionally distinct: audio-amp strap vs microSD detect — no throughput-bundling). D-312 completes the family.

The mechanism is **byte-for-byte the D-310 mechanism, zero per-net tuning** — the `SD_DETECT` GROUPS entry already carried `via_offset=2500000`; no `incremental_router.py` or `qrouter.py` change was made this increment.

## A — Re-screen on the LIVE D-311 board (essential, and it mattered)

D-311 added a new AMP_SD_MODE through via at ~(51.55,90.20), which changes the obstacle field, so `SD_CARD_DETECT_N` **had** to be re-screened on the live D-311 board before routing (`w/screen_014.py`, READ-ONLY, authoritative untouched; reproduces `cmd_route`'s cross-layer edge and measures the DEFAULT and bounded-offset via sites against REAL existing-via copper+hole the router is blind to):

```
SD_CARD_DETECT_N U2.11 (B) -> R113.2 (F)  esc@(52.95,85.10)   [escapes SOUTH]
   DEFAULT    via@(53.000,85.100)  DISP_ctr=1.901  minVIAcu=1.301 hole=1.601 (DISP_RST_N)  CLEAR
   OFF 1.5mm  via@(52.950,83.600)  DISP_ctr=3.400  minVIAcu=2.800 hole=3.100 (DISP_RST_N)  CLEAR
   OFF 2.5mm  via@(53.000,82.550)  DISP_ctr=4.450  minVIAcu=3.850 hole=4.150 (DISP_RST_N)  CLEAR
   OFF 3.5mm  via@(52.850,81.750)  DISP_ctr=5.251  minVIAcu=4.651 hole=4.951 (DISP_RST_N)  CLEAR
```

**Key finding:** `SD_CARD_DETECT_N` escapes U2.11 **SOUTH** (esc y≈85, via y≈82.55), away from the northern via cluster (DISP/TOUCH/AMP all at y≈87–92). **The new D-311 AMP via does not touch it.** The 2.5 mm site at (53.00,82.55) is **3.850 mm** clear of the nearest barrel (DISP_RST_N) — identical to the D-310-board measurement D-311 recorded — and even the via-blind DEFAULT is 1.301 mm clear (the D-309 +2 was TRACK-threading, already fixed by the D-310 always-on existing-via injection, not the via). The 2.5 mm offset stays comfortably clear → **no site adjustment needed** (the task's "at most one bounded offset adjustment" allowance was not consumed).

## B — Route → Gate → Promote (real full-board)

- `route SD_DETECT` → ALL OK (injected 61 existing-via obstacles): J2.10↔R113.2 14.145 mm same-layer F.Cu + R113.2↔U2.11 80.337 mm cross-layer F/B through via 0.60/0.30 @ (53.000,82.550); In1/In4 [39,40] re-poured for the 1 anti-pad. Authoritative sha UNCHANGED after route (scratch-only).
- `gate SD_DETECT` → **PASS every check:** prior copper 0 missing (D-311 580 trk + 61 via a SUBSET); 29 new items all target-net; only zones 39/40 re-poured, all other 39 byte-identical; `SD_CARD_DETECT_N` connected open-edges 2→0; 0 prior requested pairs regressed; **ratsnest 683→681 EXACTLY −2**; no new/worse DRC class, `clearance` 0→0; unconnected_items 499→499.
- `promote SD_DETECT` → re-ran gate PASS, re-verified AUTH sha undrifted, merged 2 REST_INC journal entries.

## C — Promoted delta

| metric | D-311 | D-312 | Δ |
|---|---|---|---|
| tracks | 580 | 608 | +28 (F.Cu + B.Cu fan-out) |
| vias | 61 | 62 | +1 (U2-escape offset through via) |
| copper layers | 6 | 6 | 0 |
| zones | 41 | 41 | 0 |
| ratsnest | 683 | 681 | −2 (net's 2 edges closed) |
| journal | 98 | 100 | +2 REST_INC |

PCB file diff **308 ins / 52 del** — additions 28 `(segment)` + 1 `(via)` (0 segment/via/footprint deletions, grep-confirmed); all xy deletions are In1/In4 `filled_polygon` re-pour (1 via anti-pad). Real KiCad DRC error-severity identical: `{solder_mask_bridge:1, hole_clearance:5, lib_footprint_issues:199, unconnected_items:499}` — 0 `clearance`.

## D — Tests / artifacts

- New contract **G26** (`router_regression.py`): `SD_CARD_DETECT_N` fully copper-connected across the U2 F/B hop (U2.11 joins J2.10 & R113.2); copper legal (28 trk 0.200 mm F.Cu+B.Cu + one 0.60/0.30 through via); **offset cleared the SD via of every existing via — min SD-via↔other-via 4.450 mm ≥ 0.80 mm**; ADD-ONLY (AMP 19 + TOUCH 26 + IR_RX_VS 8 + RGB_LED 25 + IMU 8 + DISP 11 + ACC 31 + RGB 20 + Phase-A 432/54 preserved). G18–G25 auto-generalise.
- `router_regression.py` = **ALL CHECKS PASS (G1–G26)**, run twice, deterministic.
- New `incremental_probe_014.py` PASS (READ-ONLY re-proof on the live board of exactly what the gate promoted).
- `incremental_probe_006..013` PASS unchanged (auto-generalise via the shared `live_fingerprint.py` pin + REST_INC exclusion).
- `phaseB_bringup_probe_005.py` updated (608/62/100; **15 routed rest nets, 149 unrouted**) PASS.
- `live_fingerprint.py` bumped once (single source of truth → D-312).
- Real-board `kicad-cli` DRC + pcbnew ratsnest 681 re-run independently — no new `clearance`.
- **`d269`/`d264`/`dru` NOT regressed** — a board-swap A/B test proves **BYTE-IDENTICAL verdicts** (`diff` empty) on the committed D-311 board and the promoted D-312 board. The pre-existing power-tree reds (BAT_*/LTC synthetic-copper full-zone-re-pour proxies) are ~50 mm from the mid-board SD copper and unchanged; they are NOT part of the maintained regression and were not weakened or misclassified.

## E — Opportunity & Simplification Scan (bounded to the subsystem)

**The U2 escape family is now COMPLETE** (DISP_RST_N via at D-306, TOUCH_RST_N + TOUCH_INT_N at D-310, AMP_SD_MODE at D-311, SD_CARD_DETECT_N at D-312 — every D-309-characterised U2 escape net). The bounded via-site offset + always-on existing-via injection has now cleared four independent cross-board hauls landing on U2's congested west edge with **zero per-net tuning** — a genuine reusable primitive, re-proven.

**Does the completed U2 family justify graduating to the larger XGPIO0..9 corridor study?** Assessed on evidence, NOT wishful thinking:

- **Not yet, not blindly.** The U2 family shared ONE known congested landing zone (U2's west edge next to the DISP_RST_N barrel); the offset always biased away from that one cluster. The XGPIO0..9 bank is a different problem class: **10 separate ~55 mm cross-board hauls** from the MCU-side expander to their loads, each traversing **unknown, un-characterised mid-board congestion**, not a single shared barrel wall. The offset primitive addresses via↔existing-via clashes at a known landing; it does not by itself prove ten long corridors are free.
- **The right next step is a READ-ONLY corridor/congestion STUDY of the XGPIO bank BEFORE committing to route it** — characterise each of the 10 nets' pad-escape, corridor availability, and existing-copper congestion (the `w/screen_0NN.py` pattern), exactly as the U2 wall was characterised on D-309 before it was broken on D-310. This bounds the risk without wishful generalisation.
- **A clean local group may reasonably precede it.** Remaining low-risk local candidates (short single-via controls, `RESERVED_SPARE`, isolated button nets) are getting scarcer but still exist; a local singleton is cheaper evidence-per-increment than a speculative 10-net bank.

No BOM / recoverability / testability / firmware / UX / mechanical change forced by this increment. In2/In3 remain spare. **This is a non-blocking opportunity notice, not an owner decision.**

## F — Rollback

Pre-promotion `sha256 9bf429cec07654d4522121d2fb595204d06f5173ae629f2292c4d0cb9f68b314` (D-311; parent `288d7ad`). Restore that PCB blob to revert; all other tracked changes (fingerprint/regression/probe/journal) are add-only or single-line bumps.

## G — Locked invariants preserved

No DRU / rule / clearance / stackup / topology / net / footprint / value / polarity / outline / placement change; no D-290 reauth. The one new via is D-257-legal 0.60/0.30 (≥ 0.50 min_via, ≥ 0.25 mm hole-hole). D-249 (≥ 1.20 BPP), D-269 (0.300), BAT_MAIN 0.60, D-257/D-258/D-263/D-264/D-266, D-275/D-288, In1/In4 GND roles (only those two planes re-poured), USB/RF/mechanical reservations — all ENFORCED. G18–G26 / D-304..D-311, `place_003l` (D-285), D-275 and D-277..D-311 preserved; frozen `beta-full-reference-v1` untouched; DEVICE_SPEC unchanged (no hardware/product fact changed); shared journal authoritative (100 entries); no orphan process.

## H — Next: FBV2-P2-015

**149 / 164 rest-of-board nets unrouted.** The U2 escape family is complete, so the immediate cheap-local U2 targets are exhausted. Sharply-defined next task:

**FBV2-P2-015 — the XGPIO0..9 bank corridor STUDY (READ-ONLY characterisation first), OR the next clean local group.** Recommended: run a READ-ONLY congestion/corridor screen over the 10-net XGPIO0..9 expander bank (pad-escape, per-net corridor availability, mid-board existing-copper congestion) to decide whether it can be routed as an increment (whole bank or a routable subset) with the proven offset mechanism, or whether a local group should be taken first. Do NOT route XGPIO by assuming the U2 offset transfers to un-characterised long corridors. Still avoid `U11_PROG` / `PWR_SENSE` (characterised hard walls); RF / NFC / USB / crystals / community-header / rails / switching / class-D deferred.

**Progress:** ninth rest-of-board increment; the last D-309 U2 escape sibling completed with the D-310 via-offset, zero per-net tuning, separately governed. PCB routing ~18 %→~18 %, overall ~76 %, readiness ~77 % (JLCPCB file unchanged).
