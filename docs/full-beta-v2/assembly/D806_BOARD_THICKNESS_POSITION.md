# D-806 — BOARD THICKNESS POSITION (JLCPCB 1.6 mm ±10 %)

**Verdict: HOLD — vendor exception requiring written owner approval.  The repository does NOT
prove that the full 1.44–1.76 mm range is mechanically compatible, and one fitted part's own
datasheet is exceeded at the top of that range.**

## What JLCPCB said (2026-10-06)

JLCPCB cannot promise the D-805 custom acceptance band 1.4744–1.6744 mm (stack 1.5744 mm
±0.10 mm).  Their stated process is **nominal 1.6 mm ±10 % (≈ 1.44–1.76 mm)**.

## Where the D-805 band came from

* 1.5744 mm is the arithmetic total of the declared stack (`docs/full-beta-v2/architecture/FBV2_SIXLAYER_STACKUP.md:74`,
  `docs/full-beta-v2/assembly/PCBWAY_STACKUP.md`), not an interface requirement.
* ±0.10 mm entered at D-782 (`export_fab_package.py` stackup notes): "Finished thickness still
  affects enclosure stack and PTH process capability."  No document derives ±0.10 mm from an
  interface.  Nothing in the repository derives ±10 % either.

## Thickness-dependent constraints, interface by interface

| interface | depends on thickness? | evidence | 1.44 mm | 1.76 mm |
|---|---|---|---|---|
| **J6** JST B2B-PH-K-S (fitted THT speaker header) | **yes** | `vendor/JST/jst-ph-connector-ePH.txt:25` — "Applicable PC board thickness: 0.8 mm to 1.6 mm" | inside | **OUTSIDE (by 0.16 mm)** |
| J5 Samtec SSQ-124-02-G-S-RA (THT RA, –02 tail 2.54 mm) | tail protrusion; Z column | no board-thickness range on the Samtec sheet; `MECHANICAL_INTERFACE_SPEC.md` Z column 22.71 / 23.0 mm with the PCB term hard-coded 1.6 (`mechanical_keepout_contract.py`) | protrusion 1.10 mm | protrusion 0.78 mm; Z 22.87 / 23.0 mm on paper — **enclosure CAD not available** |
| J3 GCT USB4105 (top-mount, shell stakes + NPTH pegs) | possibly (shell stakes) | **no GCT drawing in the repository** | unknown | unknown |
| J2 Molex 5025700893 (SMT) | not plausibly | drawing has no PCB-thickness note | not proven | not proven |
| J8 JST SM04B-SRSS-TB (SMT) | no clause | `vendor/JST/jst-sh-connector-eSH-2024-10.txt` | — | — |
| SW9 C&K JS102011SAQN (SMT + moulded pegs) | peg length | **no C&K drawing in the repository** | unknown | unknown |
| SW1–SW7 PTS645 SMT tact | keypad travel referenced across the PCB | Column B 19.5 mm with 3.5 mm spare; plunger travel tolerance not stated | not proven | not proven |
| D1 / U6 formed IR leads | window alignment referenced to F.Cu | `IR_LEAD_FORMING.md` CAD-TO-VERIFY; enclosure Z datum face not stated | not proven | not proven |
| J4 battery pigtail | **no** | trimmed and MEASURED <= 0.50 mm above F.Cu after soldering (`THT_LEAD_TRIM.md` J4-T1) | proven | proven |
| BOSS1/BOSS2, rails, ribs, display stack | capture / Z sums | no screw length, boss height, rail slot width or rib Z dimension in the repository; Columns A/C have ample spare | not provable | not provable |
| RF / USB dielectric bounds | electrical | `PCBWAY_STACKUP.md:52-55` bounds each dielectric; a ±10 % build that moves dielectrics may break them | stack-dependent | stack-dependent |

Note: the D-805 upper bound 1.6744 mm already exceeded J6's datasheet 1.6 mm.  This is a
pre-existing finding surfaced by D-806, not a D-806 regression.

## Position stated to vendors

1. Finished thickness acceptance is **unchanged from D-805 (1.5744 ±0.10 mm)** until the owner
   decides otherwise in writing.
2. JLCPCB's 1.6 mm ±10 % is recorded as a **vendor exception requiring written owner approval**.
   The RFQ asks JLCPCB to state the finished-thickness band they can hold on JLC06161H-7628 (or
   their proposed stack) and to say whether a ≤ 1.60 mm maximum is available.
3. No order may proceed on the thickness question until the owner either (a) accepts JLCPCB's
   band with J6 out of its datasheet range above 1.60 mm, or (b) obtains a tighter vendor band,
   or (c) approves another resolution.  The GCT USB4105 and C&K JS102011SAQN drawings should be
   archived before (a) is chosen.

D-806 invents no enclosure tolerance.
