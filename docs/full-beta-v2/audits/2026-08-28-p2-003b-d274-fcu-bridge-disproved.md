# FBV2-P2-003B — D-274: the bounded F.Cu high-current via bridge is disproved; the western margin is saturated on F.Cu exactly as on B.Cu

**Date:** 2026-08-28 · **Task:** FBV2-P2-003B · **Starting HEAD:** `624f085`
**Verdict:** **BRIDGE-PROOF CLOSEOUT — a measured FAIL.** D-273 disproved the long
outer-B.Cu zero-via route and named the next step: a **bounded named-path F.Cu
high-current via bridge** for `BAT_PROTECTED_P`. 003B investigates that bridge on
the reproduced c3 board (U18 8/8, trunk open) with evidence-based via-array
sizing and real obstacle-aware searches, and it **fails**: the two via-array
transitions are individually feasible — a **≥4-via B.Cu→F.Cu array lands on
R75.2's own pad**, and a **≥4-via F.Cu→B.Cu array lands on the eastern node** —
but the **F.Cu traversing segment between them does not exist at the mandatory
≥1.20 mm floor.** A full-trunk-width F.Cu corridor from R75.2 dies at **x ≈ 4.80
mm**, boxed by the western control-net F.Cu crossings (the LTC_GATE vertical at
x = 5.75, the BAT_PROT_SHDN_CTL diagonal, the BAT_RAW run at y = 72.45); only a
**≤ 0.80 mm** trace threads east to x ≈ 11.6 mm, and 0.80 mm is **below the
1.20 mm trunk floor this task may not waive.** The FAIL is corroborated by the
router's own full-budget A*: **NO_PATH at 1.20 and 1.50 mm** to the node, by
region exhaustion. **The western margin is saturated on F.Cu as much as on
B.Cu** — the trunk cannot cross it on either outer layer. `c3_00` remains
**evidence only, not promoted.** The authoritative PCB is unchanged — six copper
layers, **0 signal tracks, 0 signal vias.** **This is NOT an owner decision;** the
next technical task is a **bounded western-corridor control-net vacate ECO** to
open a ≥1.20 mm F.Cu lane for the bridge. B-34 remains open.

---

## 1. The task, the ruling, and what "disproved" means

D-273 closed the long-B.Cu route and framed 003B as CTO/engineering scope:

> "The next technical task is a BOUNDED NAMED-PATH F.Cu HIGH-CURRENT VIA-BRIDGE
> investigation, requiring evidence-based via-array sizing … and full safety /
> DRC / connectivity gates."

003B is that investigation. "Disproved" here is a **routed / obstacle-aware
search fact**, not an analytic clearance: on the reproduced c3 board, no F.Cu
corridor of width ≥ 1.20 mm exists from R75.2's entry-array site to the
`BAT_PROTECTED_P` node island — the western margin is congested on F.Cu by the
control nets, just as D-273 proved it is on B.Cu by the current-carrying copper.

The CTO ruling for this closeout (D-274):

- **The bounded F.Cu high-current via bridge is disproved** at the 1.20 mm floor
  and the 1.50 mm target. The two via arrays exist; the required F.Cu traverse
  does not. It is a measured FAIL, corroborated by the router's own full-budget A*.
- **`c3_00` stays evidence only.** Not promoted; its bit 8
  (`BAT_PROTECTED_P R75.2→U11.2`) remains open.
- **The authoritative PCB is unchanged** — six layers, 0 signal tracks, 0 signal
  vias; no KiCad source mutated.
- **No owner escalation.** Re-routing already-placed control nets to vacate an
  F.Cu corridor is CTO/engineering scope (the same class of move as the D-270
  offload), not a placement or protection-architecture change.
- **Next task: a bounded western-corridor control-net vacate ECO** — move the
  three named F.Cu control crossings out of the x 4.8…11 / y 66…73 window and
  re-measure the ≥1.20 mm F.Cu bridge. It is **not implemented in 003B.**

---

## 2. The board under test, reproduced byte-consistent with D-273

003B reproduces the pinned c3 board with `run_prefix_002z.py place_002z/c3_00.json
c3repro003b` (AUTHORITATIVE placement + pinned `c3_00.json`: R75 `[2.8,65,270]`,
U18 `[4.0,72.9,90]`, R79 east `[9.825,67.825,0]`). The committed result triple
confirms it is the proven-8/8, trunk-open board:

- `place_002z/result_c3repro003b.json`: `applied=true`, `asserted=true`,
  `mismatch=false`, `targets="111111101"`, `u18=8`, `u18_open=[]`, `ledger="7/29"`,
  `sense_mm=13.811`, `returncode=0` — identical to D-273's numbers.
- The one open target is bit 8, `BAT_PROTECTED_P R75.2→U11.2`.

**The exact islands, measured (KiCad `GetConnectedItems`).** The BPP net is in
four B.Cu clusters, and connectivity — not clustering — decides the target:

- **Target island** `{D9.1, C25.1, C36.1, U11.2}` — the east node (x 38.48…66.40)
  plus the C25/C36 F.Cu cap copper (x 11.35…60.6) that ties D9.1's reservation
  stub to the node through **two single 0.80/0.40 vias** at (11.35, 71.3) and
  (60.6, 65.0).
- **Source island** `{R75.2, U18.8}` — R75.2's B.Cu stub (a 1.14 mm island at
  x = 2.80) plus the U18.8 Kelvin tap on In2.
- U14.2/U14.3/TP15.1 and C58.1 are separate sense/dangling copper.

So bit 8 is open **only because the R75.2 source island is not tied to the target
island** — a ~8 mm western gap. D9.1 is already connected to U11.2.

---

## 3. The via-array sizing, from the board's own IPC-2221B arithmetic

`via_array_003b.py` → `place_002z/via_array_003b.json`. A single through via is a
bottleneck the task forbids, so each transition must be a via ARRAY. The sizing
uses the **same IPC-2221B method the `.kicad_dru` section 5 used for the copper
widths**, applied to the plated barrel as an INTERNAL conductor (buried in FR4,
k = 0.024), and is **calibrated** by reproducing the DRU's own figure: BAT_MAIN
outer **0.525 mm** at 1.5 A / 10 K (exact) and inner 2.75 vs 2.734 mm.

- **Barrel** 0.40 mm drill, 25 µm plating (conservative JLC assumption, flagged
  UNVERIFIED): exact-annulus copper area 0.02945 mm² = 45.65 mil².
- **Per-via capacity, internal, 10 K rise: 1.055 A** (external 2.11 A; internal
  20 K 1.43 A). No barrel-to-plane cooling credit is taken — a via is better
  cooled than an equal-area surface trace, so this is conservative.
- **Sizing for the 1.75 A validation case:** ideal-sharing needs 2; the
  **fault-tolerant floor is 3** (3.17 A = 1.81× margin; lose one open via → 2
  remain = 2.11 A > 1.75 A; hottest via under 2:1 imbalance rises ~12.6 K); the
  **design target is 4** (hottest via rises only ~6.5 K under 2:1 imbalance).
- **Array resistance:** N3 = 0.293 mΩ, N4 = 0.220 mΩ (0.88 mΩ/via, the
  `b34_from_copper.R_VIA` figure). Two arrays add ~0.44 mΩ.

---

## 4. The designed bridge mechanism (documented, NOT instantiated)

The path-role mechanism 003B would add, on the D-270 pattern — router-supplied
areas so a rule never names copper that does not exist — authorises **only**:

1. a bounded `BAT_PROT_BRIDGE_ENTRY` area over R75.2's pad admitting a
   B.Cu→F.Cu via array of ≥ 3 (design 4) 0.80/0.40 POWER vias;
2. a bounded `BAT_PROT_BRIDGE_FCU` corridor for the F.Cu traversing segment at
   ≥ 1.20 mm (target 1.50 mm), grown from the run's own copper;
3. a bounded `BAT_PROT_BRIDGE_EXIT` area on the node admitting the F.Cu→B.Cu via
   array.

It authorises **no In1/In2/In3/In4 current copper** and is **not a netclass
exception**. It is **NOT written to any board in 003B**, because the bridge does
not route: instantiating an authorization for copper that cannot be laid would be
precisely the overbroad exception the mechanism must forbid. Its electrical
contract is regression-pinned (§7); its geometric contract — a corridor may not
be a bounding box and may not admit foreign nets — is already enforced by
`dru_probe`'s `corridor_checks` the moment any such area is instantiated.

---

## 5. The measurement — entry and exit feasible, traverse impossible

`bridge_feasibility_003b.py` → `place_002z/bridge_feasibility_003b.json`
(reproducible; lays no permanent copper). QBoard models a through via as copper
on every layer with the GND pours auto-antipadded, so a via site is gated by
In2/In3 signal copper, not the planes.

**ENTRY — feasible.** R75.2 is a 1.225 × 3.35 mm B.Cu SMD pad. A **4-via array
fits on the pad** at 0.9 mm pitch — (2.2, 67.8), (3.1, 67.8), (2.2, 68.7),
(3.1, 68.7) — all clear on every copper layer. F.Cu is **empty within 3.5 mm of
R75.2**, so the array's F.Cu side launches into open copper. (Via-in-pad on the
sense-resistor pad requires plated-over-filled vias — the D-258 POFV process,
already precedented on this board for Q3.3.)

**EXIT — feasible.** A 4-via array lands on the target island at multiple sites:
node-west (527 free sites, x = 38.5), node-interior (855 free sites, x = 45), and
even a 3-via array on the D9 reservation stub (x ≈ 10.5).

**TRAVERSE — impossible at ≥ 1.20 mm.** The decisive measurement, two ways:

- **Flood (how far east a full-width F.Cu corridor reaches from R75.2):**
  @1.50 mm → x = 4.65 mm, **@1.20 mm → x = 4.80 mm**, @1.00 mm → x = 4.95 mm,
  @0.80 mm → x = 11.6 mm. The island's west edge is x = 10.05 mm, so **no corridor
  ≥ 1.00 mm reaches it; only ≤ 0.80 mm threads through.**
- **Full-budget A* (the same `QBoard.search` the router uses), R75.2 → node:**
  to the BPP F.Cu west end (11.35, 71.3) and to (40, 75), **NO_PATH at both 1.20
  and 1.50 mm**, returned in 0.5–0.6 s by exhausting the small reachable F.Cu
  region — a genuine "there is no corridor," not a starved search.

The blocker is the western control-net F.Cu congestion: the **LTC_GATE vertical**
(x = 5.75, y 64.55…70.05), the **BAT_PROT_SHDN_CTL diagonal** (3.92, 74.83) →
(12.78, 63.85) crossing the band at x ≈ 9.4 at y = 68, and the **BAT_RAW run** at
y = 72.45 (x 7.75…19.9), with LTC_GATE_RC and FAULT_N vias between them. A
1.20 mm trunk plus its 0.30 mm D-269 clearance each side needs ~1.8 mm of clear
width, and the gaps between these crossings — and around the ends of the x = 5.75
barrier — are narrower than that on every latitude R75.2 can reach.

---

## 6. What this does and does not prove

- **Proven:** on the reproduced c3 board, no F.Cu corridor of width ≥ 1.20 mm
  joins R75.2 to the `BAT_PROTECTED_P` node island. The two via-array transitions
  the bridge needs are individually feasible; the traverse between them is not.
  Combined with D-273, **the western margin cannot host a ≥ 1.20 mm high-current
  trunk on either outer layer** — the saturation is genuinely in the plane, on
  both faces.
- **The 0.80 mm escape is not a loophole.** A 0.80 mm F.Cu trace does thread east
  (and by IPC would carry ~2.0 A at 10 K), but 0.80 mm is below the **mandatory
  1.20 mm trunk floor** (D-245/D-249), which this task is explicitly forbidden to
  waive. It is recorded, not used.
- **The pre-existing D9→node link is a latent single-via bottleneck.** D9.1 is
  tied to U11.2 through the C25/C36 F.Cu cap copper by two single 0.80/0.40 vias.
  This carries no current today (R75.2 is isolated); it is flagged so any future
  bridge that lands on the D9 stub must also array that crossing, not inherit it.
- **NOT claimed:** nothing here is a routed PASS. `c3_00` is not promoted; no
  authoritative copper is written; no In-layer current path is proposed.

---

## 7. Regression added (does not weaken any constraint)

`via_array_probe.py` — the **via-array sizing contract**, generalized regression
for the bridge's electrical half, and the rejection of undersized exceptions:

1. the method reproduces the DRU's own BAT_MAIN outer 0.525 mm (integrity);
2. per-via capacity 1.055 A internal/10 K;
3. a **single via is REJECTED** for 1.75 A, and a **two-via array is REJECTED**
   (no single-via-fault tolerance);
4. the **≥ 3 floor** carries 1.75 A with one open via; the derivation is
   self-consistent (ideal 2, floor 3, imbalanced → design 4); the floor stays
   < 20 K and the design < 10 K under 2:1 imbalance;
5. an undersized 1- or 2-via transition is rejected by the floor.

**VIA-ARRAY PROBE: PASS.** The overbroad/bounding-box/foreign-net GEOMETRIC
rejection is already carried by `dru_probe`'s `corridor_checks`, so it is not
duplicated. No width, clearance, via, layer or connectivity rule is changed, and
no board is mutated — the contract is deterministic arithmetic.

---

## 8. The CTO recommendation — a bounded western-corridor control-net vacate ECO

Both outer-layer routing options are now spent: D-273 disproved B.Cu (short and
long), 003B disproves the authorized F.Cu via bridge — not because the arrays or
the layer change fail, but because the **western margin has no ≥ 1.20 mm lane
free on F.Cu.** Inner layers are barred for pack current (0.5 oz, 2.73 mm, D-264)
and by this task.

The exact and only obstruction is now named copper: three control-net F.Cu
crossings in the x 4.8…11 / y 66…73 window. The next task is therefore a
**bounded control-net vacate ECO** — re-route the LTC_GATE x = 5.75 vertical, the
BAT_PROT_SHDN_CTL diagonal and the BAT_RAW y = 72.45 run off that window to open a
≥ 1.20 mm F.Cu bridge lane, then route the bridge measured here. This is
**CTO/engineering scope**, the same class of move as the D-270 offload: it
re-routes already-placed control nets, it changes no placement and no protection
architecture, and it must be proven not to regress the eight passing targets or
U18 8/8. **The owner is not in the loop** unless that ECO also fails, at which
point the western-corner oversubscription becomes the placement/architecture
question D-271 first raised.

---

## 9. Suites, state, and the next blocker

**All suites re-run at this commit and PASS:**

- `router_regression` — **ALL CHECKS PASS**, G1–G9 + G10 + G11.
- **`via_array_probe` — PASS** (new).
- `dru_probe`, `d264_probe`, `d266_probe`, `d267_probe`, `d269_probe`,
  `d270_probe`, `netclass_probe` — all exit 0.

**Nothing moved and nothing relaxed:** D9, U18, R75, R76…R83, Q3, the shunt, the
FETs, TP17 and C58 all frozen; `c3_00` NOT promoted; D-249, D-264, D-266, D-267,
D-269, D-270, D-271, D-272, D-273 untouched; the outer-1-oz / zero-via
high-current policy unchanged; current-carrying BAT_MAIN clearance not weakened;
the authoritative PCB is six copper layers with 0 signal tracks and 0 signal vias
and no KiCad source was mutated.

**U19 NOT SEARCHED**; Phase A NOT passed; Phase B NOT run; converter routing NOT
started. **B-34 REMAINS OPEN.**

**The precise next blocker:** `BAT_PROTECTED_P R75.2 → U11.2` (target bit 8) is
open, and neither the short nor the long outer-B.Cu zero-via route (D-273) nor
the authorized F.Cu high-current via bridge (D-274) can close it — the western
margin has no ≥ 1.20 mm high-current lane free on either outer layer. The next
technical task is a **bounded western-corridor control-net vacate ECO** to open
one. **No progress earned: PCB routing stays 0 %, overall stays 74 %.**
