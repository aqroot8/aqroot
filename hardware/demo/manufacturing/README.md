# AQROOT Demo manufacturing preflight

Status: **BLOCKED** at board completion; no manufacturing candidate is approved.

The deterministic candidate exporter is `export_candidate.sh`. It writes only to
a new caller-supplied directory, generates full/fitted BOMs, an assembly position
file, all six copper layers, paste/mask/silkscreen/outline Gerbers, separate PTH
and NPTH drill files, and then runs `check_candidate.py`. Existing output is never
overwritten.

## 2026-09-02 baseline at `3e241dc`

- Board SHA-256: `cb4774b5ab76eb427bd70f0fb7dde17b7a1d7eb3c860826e94efeb7c9f91e93d`.
- All 14 expected Gerber/job files and both non-empty drill files exported; the
  drill report contains 139 PTH and 7 NPTH holes.
- Full BOM: 310 references. Schematic-fitted BOM: 294 references, with 16 DNP.
- CPL: 263 references.
- Real KiCad DRC: 205 board violations in the accepted baseline classes (199
  footprint-library, 5 hole-clearance, 1 solder-mask bridge), **plus 499
  unconnected-item errors** and 265 schematic-parity warnings.
- The 499 errors prove that the earlier RGB milestone completed only the four
  Demo replacement nets. The retained board is not routing-complete; its
  ratsnest was still 610 after RGB promotion.
- Schematic/PCB population parity is not release-safe: all 16 schematic DNP
  references leak into a PCB-derived CPL because their footprint DNP flags do
  not match: `C21 C22 C34 C35 C81 C82 L2 R44 R45 R68 R93 R107 R112 R119 R123 U13`.
- Procurement coverage is incomplete: 229 fitted references lack an MPN. Most
  are passives and test points, but `J8` is also in this set. This must be
  resolved through an explicit fitted/off-board/test-point population model,
  not by accepting an underspecified grouped BOM.

The generated files from this baseline are characterization artifacts only and
were deliberately not promoted into the repository. The authoritative Demo PCB
and schematic were not changed, and `hardware/beta-v2/` remained untouched.

## Retained-net routing ledger

`routing_ledger.py` is the deterministic connectivity authority for Demo routing
completion. It derives the 294 fitted references from the schematic BOM, removes
only the 16 explicit schematic-DNP references from routing obligations, and uses
KiCad's copper connectivity over distinct physical pad lands. The eight approved
Demo NC contacts are audited by exact identity (`J5.9`-`J5.12` and
`J5.15`-`J5.18`); no other connector contact is exempted.

Run it from the repository root:

```text
hardware/demo/manufacturing/routing_ledger.py /tmp/demo-routing-ledger.json
```

The accepted `988149f` baseline is pinned in `routing-ledger-baseline.json`:
173 retained multi-pad nets, 59 already connected, 114 open, and 581 retained
open edges. This reconciles exactly with KiCad's raw 610-edge ratsnest after
removing the 29 edges owed only by unpopulated DNP pads. `LS1` is correctly
off-board and `BOSS1/BOSS2` are PCB-only mechanical references.

## Next bounded task

The speaker-output cluster was promoted on 2026-09-02. `SPK_P`, `SPK_N`,
`SPK_P_CONN`, and `SPK_N_CONN` now connect `U5` through `R121`/`R122` to `J6`.
The class-D legs use 0.25 mm outer-layer copper with two 0.60/0.30 mm vias per
leg; connector legs remain on F.Cu. The retained ledger moved exactly 581 ->
577 edges and the raw ratsnest 610 -> 606. The authoritative refilled KiCad DRC
remains exactly 199 footprint-library, 5 inherited hole-clearance, and 1
inherited solder-mask-bridge report, with no new attributable class. Board hash:
`b85533a559f81ae8b49366b76ddbfcdaace3a0086c434d525d06eee0893729d4`.

IR routing characterization on 2026-09-02 corrected the earlier cluster
assumption. The fitted-pad ledger proves that `IR_GATE` is a separate long-haul
signal: its three pads (`R22.2`, `Q1.1`, and the safe-off pull-down `R23.1`)
span **110.586 mm** and account for two open edges. The LED-current loop is the
genuinely local cluster: `IR_LED_A` spans 9.282 mm with two open edges and
`IR_LED_K` spans 5.307 mm with one. `R123` is DNP and must not be counted as a
required routing endpoint or used to satisfy fitted connectivity.

A first combined scratch topology was rejected before promotion: forcing all
three nets through one outer/inner-layer pattern crossed accepted top-edge
copper and did not provide a legal local current loop. The authoritative board
did not absorb that attempt.

The separated local-current task was promoted on 2026-09-02. `IR_LED_A` now
connects fitted `R24.1`, `D1.2`, and `TP39.1`; `IR_LED_K` connects `D1.1` to
`Q1.3`. Both use 0.30 mm F.Cu with no vias, preserve the 12 ohm current limit,
leave DNP trim `R123` electrically optional, and keep the emitter/FET loop at
the top edge. The retained ledger moved exactly 577 -> 574 edges and raw
ratsnest 606 -> 603. Real KiCad DRC remains exactly 199 footprint-library, 5
inherited hole-clearance, and 1 inherited solder-mask-bridge report, with no
new attributable class. Board hash:
`ddebb3500f445524bd932aaff055f7c60f6d5bca17cee25f64ed0624d2bfbf67`.

The separated `IR_GATE` task was promoted on 2026-09-02. The FET gate and
reset-safe `R23` pull-down join on 0.20 mm F.Cu at the top edge; a two-via
0.60/0.30 mm In2.Cu haul reaches `R22.2` without bypassing the series gate
resistor. All three fitted pads are one copper island. The retained ledger
moved exactly 574 -> 572 edges and raw ratsnest 603 -> 601. A zone-refilled
full-board KiCad DRC remains exactly 267 total reports / 499 raw unconnected
items, with no `IR_GATE` report or new attributable class. Board hash:
`b74cd3c059c50bc4edeb7ba17b6b20a2067abe19ae31e159bc6d5c517f757b24`.

The first bounded `ACC_5V_RAW` transaction was characterized on 2026-09-02 and
rejected before promotion. The fitted-pad ledger confirms six isolated pads and
five retained open edges across 13.001 mm: `U21.6`, `C65.1`, `C66.1`, `R99.1`,
`TP28.1`, and `U22.2`. This is an `ACC_5V` power-class route, so it requires at
least 0.40 mm track width (0.60 mm preferred), 0.25 mm routed clearance, and a
power via with at least a 0.40 mm drill. The board's 0.25 mm minimum annular
width makes the usable ordinary through-via geometry 0.90/0.40 mm, not the
0.60/0.30 mm signal-via pattern.

A scratch topology kept the U21-to-C65 output connection on B.Cu and attempted
an In3 distribution tree through five 0.80/0.40 mm vias. Real zone-refilled
KiCad DRC rejected it: the proposed pad escapes crossed or shorted the accepted
`ACC_POWER_FAULT_N`, `ACC_DETECT_N`, and `XGPIO5` copper, and the 0.80 mm vias
failed the annular-width/diameter rules. No part of this attempt entered the
authoritative PCB.

The durable wall is endpoint-local rather than an In3 capacity problem.
Accepted B.Cu `ACC_POWER_FAULT_N` and `ACC_DETECT_N` branches bound the U21.6
escape channel on its east and west sides; fitted `TP10` closes its south exit.
At U22.2, the same accepted fault branch crosses the only direct west escape,
while adjacent U22 pads block north, south, and east. A compliant 0.90/0.40 mm
via cannot be placed in either endpoint pocket without colliding with retained
copper or a fitted pad. Blind/microvias and via-in-pad remain excluded: neither
has an approved manufacturing contract, and via-in-pad at the 0.675 x 0.350 mm
U21 land would compromise assembly.

The ordered local-obstacle study on 2026-09-02 disproved both initially proposed
minimal levers without changing the authoritative board. Moving `TP10` alone
cannot expose U21.6: a 0.40 mm B.Cu route from U21.6 toward C65.1 still crosses
the accepted `ACC_POWER_FAULT_N` segment from (59.25, 35.15) to
(59.20, 42.20), independently of TP10's position. The route also confirms that
U21's 0.15 mm package pad-to-pad spacing needs the existing local rule; it is
not permission to relax the 0.25 mm routed-clearance contract elsewhere.

A second scratch candidate removed only that crossing fault segment and the
long U22-side fault segment from (52.35, 56.80) to (52.90, 39.85), preserving
their endpoints with 0.60/0.30 mm through-vias and straight In2 replacements.
Refilled KiCad DRC rejected the candidate with five new clearance violations,
three new hole-clearance violations, and an `ACC_POWER_FAULT_N`/`XGPIO4` short.
The exact endpoint conflicts are TP10 at (59.20, 42.20), R50 at
(52.35, 56.80), TP9 at (52.90, 39.85), L4 at (59.25, 35.15), and the retained
`XGPIO4` In2 haul at the U21-side via. Thus a segment-for-segment layer lift is
not a legal connectivity-preserving refloor. `ACC_POWER_FAULT_N` remains fully
connected on the authoritative board; the retained ledger remains 572 open
edges / 601 raw ratsnest, and board hash remains
`b74cd3c059c50bc4edeb7ba17b6b20a2067abe19ae31e159bc6d5c517f757b24`.

The bounded optional-obstacle placement transaction was characterized on
2026-09-02 and rejected without changing the authoritative board. Moving `TP9`
from (52.25, 39.25) to (49.50, 39.25), `TP10` from (58.50, 42.75) to
(63.50, 42.75), and `R50` from (51.525, 57.735) to (49.50, 57.735) clears all
three previously measured TP9/TP10/R50 conflicts. Straight In3 replacements of
the same two removed `ACC_POWER_FAULT_N` segments then eliminate those endpoint
violations, but real refilled KiCad DRC still rejects the transaction at exactly
the two fixed obstacles: the (59.25, 35.15) via is only 0.045 mm from `L4.2`
and has only 0.195 mm hole clearance, while the (59.20, 42.20) via shorts the
retained `XGPIO4` In2 haul. The moved optional parts introduce no other
geometric DRC class. Therefore optional-part placement alone cannot produce a
legal fault refloor, and no placement or copper was promoted. The authoritative
ledger remains 572 retained open edges / 601 raw ratsnest and board hash remains
`b74cd3c059c50bc4edeb7ba17b6b20a2067abe19ae31e159bc6d5c517f757b24`.

The explicit offset-landing enumeration on 2026-09-02 closes that proposed
segment-local tactic. `enumerate_acc_fault_landings.py` withdraws only the
U21-side fault segment in scratch, replays the proven TP9/TP10/R50 moves, and
uses the established routing geometry engine at 0.025 mm resolution to search
for B.Cu-reachable, all-copper-layer-clear 0.60/0.30 mm signal-via sites within
3.0 mm of both old endpoints. With 0.20 mm signal width/clearance, 0.25 mm hole
clearance, and 0.30 mm material separation between reported sites, both
`(59.25,35.15)` and `(59.20,42.20)` return zero sites and therefore zero
distinct landing pairs. A clean rerun is byte-identical, and the authoritative
board remains unchanged at
`b74cd3c059c50bc4edeb7ba17b6b20a2067abe19ae31e159bc6d5c517f757b24`.

The complete-branch fitted-pad escape screen on 2026-09-02 establishes the
replacement framework's missing prerequisite. After withdrawing all 57 fault
tracks in scratch and replaying the characterized TP9/TP10/R50 moves,
`enumerate_acc_fault_pad_escapes.py` found ordinary B.Cu-to-In3 0.60/0.30 mm
through-via sites from every actual fitted pad: `R103.2` 96, `TP27.1` 96,
`TP33.1` 94, `U20.6` 36, `U22.6` 60, and `U3.18` 24. A clean rerun produced
byte-identical JSON evidence. The authoritative board remained byte-identical
at `b74cd3c059c50bc4edeb7ba17b6b20a2067abe19ae31e159bc6d5c517f757b24`.
Thus the fitted endpoints are not intrinsically boxed after complete branch
withdrawal; the closed tactic was preserving its obsolete intermediate
landings.

The complete replacement transaction was closed in scratch on 2026-09-02 by
`route_acc_fault_branch_scratch.py`. It reserves mutually legal 0.60/0.30 mm
through-via escapes from all six fitted pads, then uses a shortest-edge-first
tree. Four joins close on In3; the locally blocked `U3.18`--`TP33.1` join closes
on In2 in 2.344 mm. All six pads form one branch through five joins. A real
zone-refilled KiCad DRC returns exactly the accepted inherited classes: 199
footprint-library, 5 hole-clearance, and 1 solder-mask bridge, with no new
clearance, shorting, crossing, annular, via-diameter, or dangling report. A
clean rerun returns the same reservations, joins, lengths, and DRC signature.
The authoritative board remains byte-identical at
`b74cd3c059c50bc4edeb7ba17b6b20a2067abe19ae31e159bc6d5c517f757b24`.

The atomic power transaction screen on 2026-09-02 advances the wall to the
package-neck contract. `route_acc_power_transaction_scratch.py` replays the
complete legal fault replacement, joins U21.6 locally to C65.1, and reserves
compliant 0.90/0.40 mm power vias at C65.1, R99.1, C66.1, TP28.1, and U22.2.
Four inner-layer joins close the tree, so all six fitted `ACC_5V_RAW` pads have
a complete scratch topology. In particular, U22.2 is no longer boxed after the
fault refloor; its legal power via lands at (52.600, 43.000) mm.

Real refilled KiCad DRC proves that the remaining failure is intrinsic to the
U21 package launch. A 0.40 mm trace leaving U21.6 has only 0.125 mm clearance
to adjacent switch-node pad U21.5, below the 0.200 mm requirement. A short
0.25 mm by 0.45 mm B.Cu package neck removes that direct conflict, but the
blanket `ACC_5V minimum width` rule rejects the neck; widening after 0.45 mm is
still 0.1709 mm from U21.5. Thus neither moving optional obstacles nor another
inner-layer permutation can satisfy the present simultaneous 0.40 mm minimum
width and 0.20 mm clearance at this fixed 0.15 mm pad-to-pad package geometry.
The authoritative board remains unchanged at `b74cd3c0...`, with 572 retained
open edges / 601 raw ratsnest.

The atomic fault-plus-power transaction was promoted on 2026-09-02. A bounded
0.005 mm sweep found that a 0.505 mm U21.6 neck still violates clearance while
0.510 mm passes. The promoted launch is therefore 0.25 mm wide for 0.510 mm
inside U21's courtyard, then immediately widens to the required 0.40 mm. U21
was added to the existing fine-pitch package-neck width rule alongside the
identical U13 TPS61023 package; the general `ACC_5V` width and 0.25 mm routed
clearance rules remain unchanged outside the courtyard.

The transaction replaces the complete `ACC_POWER_FAULT_N` branch, moves only
optional `TP9`, `TP10`, and `R50`, and closes all six fitted `ACC_5V_RAW` pads
using five 0.90/0.40 mm power vias. Retained open edges move exactly 572 -> 567
and raw ratsnest 601 -> 596; `ACC_5V_RAW` alone changes from five open edges to
zero and no retained net regresses. The authoritative refilled full-board DRC
signature remains exactly 199 footprint-library, 5 inherited hole-clearance,
and 1 inherited solder-mask-bridge report, with no clearance, short, crossing,
width, via, dangling, or schematic-parity regression. Board hash:
`ab4569487b781a164f14d392f7c1159c48fefbdad40522ced42e4af78a71c5b4`.

The first downstream `ACC_5V_SW` screen on 2026-09-02 is characterization-only.
The retained ledger proves seven isolated fitted pads / six open edges:
`U22.5`, `C38.1`, `C67.1`, `TP29.1`, `TP42.1`, `J5.1`, and `J5.24`.
`route_acc_5v_sw_scratch.py` first tested an ordinary 0.40 mm / 0.25 mm-clearance
tree with 0.90/0.40 mm power vias.  The direct transaction stops at U22.5 with
`NO_LEGAL_ESCAPE`: the fixed fine-pitch load-switch output cannot own an
ordinary power via in its package pocket.

The next bounded alternative reused the accepted U21 package-neck pattern: a
0.25 mm local launch from U22.5, widening immediately to 0.40 mm, with nearby
output capacitor C67 intended to own the compliant via.  This advances the
same deterministic screen to C67.1, which also returns `NO_LEGAL_ESCAPE` before
any inner-layer join.  Two clean runs produced byte-identical JSON
(`sha256 3b20c6c52ed474d2195943cc134556a0c85758e0947698daa2afa492067c02b5`)
and the real refilled DRC stayed exactly at the accepted 199 footprint-library,
5 inherited hole-clearance, and 1 inherited solder-mask-bridge reports.  The
authoritative board remains byte-identical at `ab456948...`; accepted U22,
`ACC_5V_SW_EN`, fault, `ACC_5V_RAW`, XGPIO4/5, and battery copper were untouched.

Next, run a bounded C67 placement/landing screen that keeps the capacitor close
to U22 output and preserves its return loop, then replay this complete tree.
If no legal C67 landing exists within that electrical placement envelope, test
a local TP29-owned via branch; do not retry the disproven direct U22.5 via.

The bounded C67 screen on 2026-09-02 corrected a harness-level face assumption:
`C67`, `TP29`, and `TP42` are F.Cu parts, while `U22` and `C38` are on B.Cu.
The original all-B.Cu reservation therefore described the present placement,
not congestion.  The face-aware harness flips C67 to the U22 face and screens
six 0.5 mm-grid placements within 4.4 mm of U22.5.  Every placement reserves all
four SMD exits and completes the six-join fitted-pad tree with ordinary
0.90/0.40 mm power vias; the wall is no longer via capacity or inner-layer
connectivity.

None of the six is promotable as drawn.  Real zone-refilled KiCad DRC attributes
one expected width report to the 0.5125 mm U22.5 package neck in every case; the
Demo DRU package-neck exception currently names U13/U21 but not U22.  Each
straight U22-to-C67 trunk also intersects either C67.2/GND or the retained
`ACC_DETECT_N` B.Cu haul.  This closes blind C67 translation and proves the next
bounded alternative: add U22 to the same tightly courtyard-scoped 0.25 mm neck
contract, then route the B.Cu launch around C67.2 and `ACC_DETECT_N` before
replaying the now-proven face-aware tree.  Do not move or withdraw the retained
detect branch.  The authoritative board remains byte-identical at `ab456948...`.

The recovered `ACC_5V_SW` transaction was promoted on 2026-09-02.  U22.5 uses
the minimum measured 0.25 mm by 0.5125 mm package-local neck before widening to
the unchanged 0.40 mm `ACC_5V` floor; U22 was added only to the existing
courtyard-scoped fine-pitch power-package neck rule.  The remainder of the
route uses 0.40 mm copper and five ordinary 0.90/0.40 mm power vias.  All seven
fitted pads (`U22.5`, `C38.1`, `C67.1`, `TP29.1`, `TP42.1`, `J5.1`, and
`J5.24`) are one copper island, including both required Community Port output
contacts.

The promoted board delta is add-only: 20 tracks, five vias, 73.507 mm, all on
`ACC_5V_SW`; no footprint, accepted copper, or zone was removed or moved.
Retained open edges move exactly 567 -> 561 and raw ratsnest 596 -> 590, with
`ACC_5V_SW` alone changing from six open edges to zero and no retained net
regressing.  The authoritative zone-refilled full-board DRC remains exactly
199 footprint-library, 5 inherited hole-clearance, and 1 inherited
solder-mask-bridge report, with no clearance, short, crossing, width, via,
dangling, or schematic-parity regression.  `ACC_5V_SW_EN`, the independent
boost enable, the fault branch, XGPIO4/5, RGB, and retained battery safety
copper remain connected.  Board hash:
`209987cc3ab432dd6d2bb6c1ff5dfee0b8c0983bc77faace5db5c1904a100934`.

Next, close the coherent `ACC_3V3_SW` switched-output cluster.  It is the
highest-leverage remaining accessory-power fabrication blocker at 14 retained
open edges; preserve U20, its fault branch and safe-state enable, both J5 rail
contacts, and the accepted 5 V transaction.

The first bounded `ACC_3V3_SW` screen on 2026-09-02 is characterization-only.
The fitted-pad ledger confirms 15 isolated pads / 14 open edges.  A generic
face-aware 0.40 mm tree immediately proves U20.5 has no ordinary power escape;
reusing the accepted TPS22950 0.25 mm by 0.5125 mm package-neck pattern clears
U20.5.  The same issue occurs at U16.8; an equally short package-local launch
then reserves all ten SMD escapes, and the scratch forest completes six joins
before the shortest C63.1-to-R63.1 In3 edge returns `NO_PATH`.  Real refilled
DRC on the generic failed-prefix case remains exactly at the accepted 199
footprint-library, 5 inherited hole-clearance, and 1 inherited solder-mask-
bridge reports.  Later incomplete prefixes show only expected neck-width,
dangling-via, and open-forest collision artifacts and are not promotable.

`route_acc_3v3_sw_scratch.py` now preserves this result and bounds alternate-
edge spanning-tree search across the complete finite 15-anchor graph.

The exhaustive alternate-edge screen on 2026-09-02 corrects the apparent
C63/R63 wall.  After 28 rejected corridors it finds all 14 required joins: the
two forest components bridge through `U20.5` to `J8.2`, and the remaining
long-haul branches close through `Q10.1` and `J5.3`.  The inner-layer spanning
tree is therefore feasible without moving retained copper.

The candidate is not promotable because the two manually seeded package-neck
landings precede the generic reservation gate.  Real refilled DRC rejects the
U20 via at `(50.250,64.750)` against retained `ACC_3V3_ILIM`.  It rejects the
U16 via at `(62.500,55.725)` against adjacent `U16.7/EXT_SDA_BUF`, retained
`XGPIO4` on In2, and retained `ACC_5V_SW` on In3.  The only two width reports
are the expected 0.5125 mm package necks; no DRU exception was added because
their landing geometry is not yet legal.  Thus the next bounded task is an
explicit face-aware landing enumeration for `U20.5` and `U16.8`, followed by
replay of this now-proven full spanning tree.  Do not retry either rejected
fixed via and do not withdraw the accepted ILIM, XGPIO4, SDA, or 5 V copper.

The authoritative PCB remains byte-identical at `209987cc...`; no owner
decision is open.

The recovered landing-enumeration candidate after `612b29a` closes the complete
15-pad tree and passes the authoritative refilled KiCad gate. It is promoted as
68 add-only tracks and eleven 0.90/0.40 mm through-vias, all on `ACC_3V3_SW`;
there are zero missing accepted copper objects, zero placement changes, and no
new DRC class. Both Community Port contacts and Qwiic are in the same connected
component as U20.5. The route and its bounded U20/U16 package-neck rules are
pinned in `AQROOT_DEMO_ACC_3V3_SW_ROUTE.md`; the authoritative board hash is
`fd346ae6...`. The prior fixed-landing rejection remains useful negative
evidence, but no longer describes the live routing state.

Manufacturing export resumes after retained routing closes; population-flag
synchronization and MPN coverage remain later release blockers.

The recovered `BQ25185_SYS` scratch harness was bounded and characterized on
2026-09-02.  A 0.050 mm search grid reserves escapes from all 13 fitted pads,
including the charger, main regulator, accessory boost, switch, and local
capacitors.  The outer-layer shortest-edge forest closes eight joins but leaves
four components: the U12/capacitor group, the U21/L4/C64/C33 group, `U11.1`,
and `SW9.2`.  It is therefore not a promotion candidate.

Real refilled KiCad DRC localizes the fixed launch defects.  The explicit
`U11.1` north launch is only 0.047 mm clear of `C23.2` and 0.200 mm clear of
the retained `BAT_PROTECTED_P` corridor, below the 0.200 mm SYS and 0.300 mm
D-269 contracts.  The explicit `U21.3` launch is 0.2126 mm clear of retained
`ACC_DETECT_N`, below the 0.250 mm SYS routed-clearance rule.  One unused
F.Cu-to-B.Cu reservation remains dangling in the incomplete forest.  The
authoritative PCB remains byte-identical at `fd346ae6...`; no accepted copper,
placement, rule, or `hardware/beta-v2/` file changed.

Next, enumerate package-local legal launch anchors for `U11.1` and `U21.3`
instead of retrying their disproven fixed north launches, then reserve an
ordinary power-via/inner-layer bridge between the four proven components.
Preserve the D-269 battery corridor, `ACC_DETECT_N`, and all accepted accessory
power copper.  No owner decision is open.

The focused package-launch enumeration on 2026-09-02 closes the generic radial
escape tactic. `enumerate_bq25185_sys_launches.py` applies the actual local
width/clearance contracts on a 0.025 mm grid and searches reachable ordinary
0.90/0.40 mm B.Cu-to-In3 power-via sites. `U11.1` has zero generic escapes at
0.20 mm width / 0.30 mm D-269 clearance, dominated by adjacent `U11.2` (57
blocked samples). `U21.3` has zero at 0.25 mm / 0.25 mm, dominated by adjacent
`U21.2` (48) and `U21.1` (7). The authoritative board remains byte-identical at
`fd346ae6...`; accepted battery, accessory-power, RGB, and XGPIO4/5 copper is
untouched.

This does not prove the fixed packages unroutable: both are fine-pitch lands
whose accepted solution class is a tightly courtyard-scoped directional neck,
as already used for U20/U21/U22 power pins. Next, add a bounded angular/length
directional-neck sweep for `U11.1` and `U21.3`, immediately widen to their 0.50
mm SYS and 0.80 mm peak-feed trunks, and real-DRC each candidate against the
D-269 corridor and `ACC_DETECT_N`. Replay the four-component inner-layer bridge
only after both launches pass. Do not retry generic `reserve_escape`, the fixed
north launches, or relax either clearance contract. No owner decision is open.

The recovered directional-neck sweep was completed on 2026-09-02. The bounded
5-degree / 0.025 mm enumeration tests every straight package-local neck from
0.20 through 1.50 mm, immediately widens to the required 0.50 mm (`U11.1`) or
0.80 mm (`U21.3`) trunk, and accepts only a trunk ending at a legal ordinary
0.90/0.40 mm through-via. Neither pad has a direct radial neck/trunk/via result.
For `U11.1`, 352 otherwise-clear ray endpoints lack an all-layer via site; for
`U21.3`, 702 do. The finite monotonic-prefix stopping rule makes a clean replay
complete in about two minutes while preserving exhaustive coverage of the
declared rays and lengths. The authoritative PCB remains byte-identical at
`fd346ae6...`; no DRC rule or clearance contract changed.

This closes direct radial ordinary-via placement, not the SYS route or the
fine-pitch launch class. The next highest-leverage bounded task is to retain the
legal directional neck/trunk anchors and enumerate short B.Cu doglegs to nearby
ordinary through-via sites. Only after both package ends have legal sites should
the already-proven four-component inner-layer bridge be replayed. Do not retry
the fixed north launches, generic radial escape, or a via exactly at the ray
endpoint. Blind/microvias remain excluded absent an owner manufacturing
decision; no owner decision is currently open.

The recovered dogleg-landing sweep was completed and replayed cleanly on
2026-09-02. It retains every legal directional neck/trunk anchor from the
previous screen, then searches 0.25--2.00 mm full-width B.Cu doglegs at
5-degree and 0.050 mm resolution for an ordinary 0.90/0.40 mm through-via
site. Both package walls now have solutions: `U11.1` exposes 302 legal anchors
and the bounded result cap of 48 candidate landings; `U21.3` exposes 526
anchors and 48 candidate landings. The first ranked results are respectively a
0.325 mm, 55-degree neck plus 0.250 mm trunk and 0.350 mm dogleg to
`(66.9773,79.3185)`, and a 0.875 mm, 180-degree neck plus 0.250 mm trunk and
0.250 mm dogleg to `(56.0480,39.6349)`.

Two clean runs produced byte-identical JSON (`104fe4e3...`). The authoritative
PCB remains byte-identical at `fd346ae6...`; no accepted copper, placement, or
rule changed. This closes the ordinary-via landing search at both package
walls but is still characterization, not routed copper: the geometric screen
does not replace real KiCad DRC or connectivity validation.

Next, instantiate the shortest ranked landing at each wall in scratch, replay
the already-proven four-component `BQ25185_SYS` inner-layer bridge, and promote
only a complete 13-pad tree that passes the authoritative refilled full-board
KiCad DRC, fitted-pad connectivity, D-269, and accepted-copper preservation
gates. If either first-ranked landing fails real DRC, advance through the
persisted ranked candidates instead of reopening the closed radial searches.
No owner decision is open.

The inner-layer replay on 2026-09-02 closes all 13 fitted pads with twelve
successful joins, but the authoritative real KiCad gate rejects the U11.1
launch: its 0.20 mm package neck is exactly 0.2000 mm from retained
`BAT_PROTECTED_P`, while D-269 requires 0.3000 mm. This is structural at the
adjacent package breakout, so advancing through the other ranked 0.20 mm-local
neck candidates cannot change the limiting clearance. The landing enumerator
now applies 0.300 mm to the U11.1 neck itself and will no longer emit those
false-positive candidates. U21.3 and the complete ordinary-through-via I2/I3
spanning framework are proven reusable; no candidate copper was promoted and
the authoritative board remains unchanged.

The corrected deterministic replay confirms the boundary: U11.1 has zero
legal anchors/candidates (all 72 angular prefixes stop at adjacent U11.2),
while U21.3 retains 526 anchors and 48 bounded candidates. The authoritative
board hash remains `fd346ae6...`.

This is the fifth consecutive non-promoting iteration on the unchanged
`BQ25185_SYS` wall, so the wall is PARKED under the autonomy policy. Revisit it
only after materially changed surrounding geometry, an approved package-local
rule treatment that preserves D-269's safety intent, or a manufacturing-layer
decision. The next bounded iteration must select an independent unrouted
Demo-required net from the routing ledger and make measurable board progress;
do not spend another iteration rescreening this unchanged charger breakout.
No owner decision is currently open.
