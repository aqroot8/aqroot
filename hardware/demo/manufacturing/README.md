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
remains byte-identical. Do not retry the three nets as one nominally local
batch. Next, route and independently gate only `IR_LED_A` and `IR_LED_K`,
targeting exactly three retained open edges with deliberate outer-layer copper;
preserve the locked 12 ohm `R24` current limit, `R123` DNP trim option, test
point `TP39`, and the compact `D1`-`Q1` pulsed-current loop. Then route
`IR_GATE` as a separate low-speed long-haul task while preserving `R22` and
the `R23` reset-safe pull-down. Manufacturing export resumes only after all
retained connections are closed. Population-flag synchronization and MPN
coverage remain subsequent release blockers.
