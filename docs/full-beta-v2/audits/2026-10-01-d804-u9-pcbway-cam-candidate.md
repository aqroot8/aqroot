# D-804 U9 PCBWay CAM clearance candidate

Status: CANDIDATE ONLY — not production-authorized.

## Trigger

PCBWay CAM reported a 1.55 mil minimum copper clearance around the U9
ST25R3916-AQET fine-pitch footprint and requires >=4 mil.

## Bounded change

Only U9 corner-adjacent perimeter lands were changed:
1, 8, 9, 16, 17, 24, 25, 32.

- Pad centers: unchanged
- Pad nominal size: unchanged (0.75 x 0.30 mm / 0.30 x 0.75 mm)
- U9 placement: unchanged
- U9 rotation/side: unchanged
- Board outline: unchanged
- Routing: unchanged
- Component population: unchanged
- MPN: unchanged

The eight affected lands use roundrect ratio 0.50 instead of 0.25.
The footprint-library master was changed identically.

The U9 intra-footprint DRC floor is raised from 0.05 mm to 0.12 mm.

## Measured result

KiCad geometric minimum at the four U9 corner pairs:
- D-803: 0.0621 mm = 2.44 mil
- D-804 candidate: 0.1243 mm = 4.89 mil

The candidate clears a 0.12 mm local DRC floor and fails at 0.13 mm,
which brackets the measured minimum at 0.1243 mm.

Affected corner pairs:
- U9.1 <-> U9.32
- U9.8 <-> U9.9
- U9.16 <-> U9.17
- U9.24 <-> U9.25

Because PCBWay measured the prior CAM output lower than KiCad's geometric
minimum, this candidate is for PCBWay CAM re-check before production approval.

## Verification

After zone refill:
- KiCad DRC: same total retained baseline count; zero U9 local-clearance errors
- land_parity_contract: PASS
- population_contract: PASS
- placement_contract against D-803: PASS
- mechanical_keepout_contract: PASS
- fab_package_contract on regenerated package: PASS

D-803 main worktree was not modified.

## PCBWay CAM / PCBA reconciliation (same day, same candidate)

PCBWay then asked for the stackup, asked about crossed / open-ended traces in its CAM
screenshots, and returned a 123-line BOM quote with 12 notes.  Full matrix and the email
text: `docs/full-beta-v2/assembly/PCBWAY_D804_RESPONSE.md`,
`hardware/demo/manufacturing/evidence/d804-pcbway-response.txt`.

Authoritative changes beyond the U9 corners (all in CHANGELOG D-804):

- **D9** `Diode_SMD:D_SOD-123` → `Diode_SMD:D_SOD-123F` on board and schematic (PCBWay BOM
  note; Nexperia PMEG2010AEH data sheet 8 Oct 2024 Fig. 6 and SOD123F package information
  Fig. 2: 1.1 × 1.1 lands at 2.8 pitch).  Footprint centre, rotation, side, polarity
  (pad 1 = K = `BAT_PROTECTED_P`) unchanged; existing track ends remain inside the new lands.
- **Two D-725 joints** that a CAM end-point check reads as open (In2 `EXT_SDA_BUF` at
  (60.150–60.300, 40.800); B.Cu `BQ25185_SYS` at (57.150, 37.900)) — one same-net,
  same-width segment added to each; nothing removed.
- Zones refilled; a further refill is byte-identical (fill at its fixed point).

Independent Gerber extraction (`evidence/d804-gerber-cam-extract.py`, Gerber + Excellon only):

| | D-803 | D-804 |
|---|---|---|
| open draw ends (all layers) | 3 | **0** |
| different-net gaps < 4 mil | 4 (U9, 2.446 mil) | **0** (min 4.892 mil, U9) |
| different-net gaps < 5 mil | — | 4 (the U9 corners only) |
| different-net crossings / overlaps / shorts | 0 / 0 / 0 | 0 / 0 / 0 |
| same-net same-layer crossings | 133 | 133 |
| split nets (all DNP / approved NC) | 11 | 11 (identical) |

KiCad DRC `--severity-all --schematic-parity`: 199 violations (all `lib_footprint_issues`
warnings), 17 approved unconnected, 246 parity warnings, 0 parity errors — the same multiset
as D-803 except that KiCad anchors R112's (DNP) approved unconnected pair on a track rather
than on U1.21.  Routing ledger: connectivity, approved-NC and approved-unrouted sets identical;
only D9's pad coordinates moved.  Rail ampacity: all_ok, no rail entry changed.
