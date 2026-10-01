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
