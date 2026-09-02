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

Next, reserve one mutually distinct legal site per fitted fault pad in a single
scratch transaction, connect the In3 branch, and replay all six fitted pads.
Then attempt `ACC_5V_RAW` against that closed replacement and run the
authoritative connectivity and refilled full-board DRC gate. Preserve U21,
U22, L4, C65/C66, every connector, and accepted
`ACC_5V_SW_EN`/`XGPIO4`/`XGPIO5` copper. Promote only a complete branch plus
six-pad power-tree transaction that passes the full gate.
Manufacturing export resumes only after all retained connections are closed;
population-flag synchronization and MPN coverage remain subsequent release
blockers.
