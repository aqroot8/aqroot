# FBV2-P2-003S / D-292 — the owner-approved bounded LTC4368/R75 placement micro-ECO (D-291) is screened to EXHAUSTION: no bounded U18/R75 delta LEGALLY co-closes the U18 escape field; the wall is now proven sharper than D-290 — U18 carries CURRENT-PATH nets on BOTH edges (BAT_PROTECTED_P west / BAT_RAW east) at 0.5 mm pitch, so a rigid move only trades which edge breaches the 0.300 mm D-269 floor; closing BAT_PROTECTED_P re-escalates to a genuine OWNER decision (direction-2 or a re-authorized routing lever)

- **Task:** FBV2-P2-003S · **Decision:** **D-292** · **Result:** FAIL (governed evidence / NO PROGRESS; no promotion)
- **Starting HEAD:** `951d7bf` (D-291 owner approval record)
- **Ending HEAD:** this commit (docs + gitignored scratch evidence only; **no source, no copper, no placement, no rule change**)
- **Authoritative PCB:** UNCHANGED — six copper layers, **0 signal tracks, 0 signal vias**; placement untouched (C36 home 63.75,73.75,0°; U18 002F-routing pose 8.0,65.25,180°; R75 002F pose 2.8,65.0,-90° via b1_r75rot). No DRC absorbed into the authoritative board.

## 0. Charter

D-291 (Alpha) authorized a **bounded D-284/285-class LTC4368/R75 placement micro-ECO** to
open a *second, independent* escape for the `BAT_PROTECTED_P` trunk pad **U18.8** and
co-close U18.7/U18.8/U18.9, with every floor/rule/frozen-part preserved and engineering
proof a separate CTO gate. 003S is that engineering gate: build the cheapest defensible
bounded U18/R75 placement screen, reject any candidate with a bare-placement short /
sub-floor clearance / hole breach / real courtyard conflict / un-escapable required pin,
take the first genuinely valid candidate to a supervised full Phase-A run, and — per the
explicit charter — **stop with exact evidence if the cheap screen decisively exhausts the
bounded approved space rather than broadening scope.**

## 1. Instruments (all gitignored scratch under `checks/w/`)

- `w/geom_003s.py` / `w/region_003s.py` — exact D-286 placed-board geometry + western
  collision-headroom map (U18 pins, R75/R80/R81/R83/R77/R79/Q3 pad extents).
- `w/screen_003s.py` — reuses the D-286 `screen_003n` machinery (real full-placement
  `kicad-cli` DRC + real `qb.escape`) on `w/cand_003s/*.json`; rejects any candidate that
  adds a hard-class DRC (short / clearance / hole / courtyard) vs the `place_003l`-only
  clean reference or leaves a required U18 pin un-escapable.
- `w/run_003s.sh` / `w/batch_003s.sh` — the co-closure vehicle. **`AQROOT_LOCAL=R80`**
  (narrower west-margin prefix: U18 8-pin field + D-266 Kelvin reservations + trunk +
  BAT_MAIN + BAT_RAW bridges; skips the east taps/gauge) was validated **byte-identical to
  `D256` on the U18.7/8/9 verdict** (both: U18.9 JOINED, U18.7 closed 9.728 mm, U18.8 sole
  NO_RESERVATION/NO_VIA_SITE) and is ~2.7× faster (R80 ≈ 350 s vs D256 ≈ 915 s here). Full
  recipe otherwise per the phaseA repro recipe (SIXLAYER, ECO_002F, D256=GSQ, Q3_POFV,
  D266, D267=F1, TRUNK_LAST, U18_ORDER=6,10,7,1,3,2, D279, D280, D270=BRIDGES,
  BRIDGE_EARLY, BRIDGE_SOUTH, ECO_EXTRA=place_003l, PLACE_JSON=candidate).
- Baseline `r80bl` (b1_r75rot, U18/R75 at their 002F poses): **conn 19, DRC clean, U18.8
  the sole open pad** — the exact D-290 clash reproduced.

## 2. The bounded space and how it is boxed (w/region_003s.py, measured)

- **U18** (LTC4368, MSOP-10, 0.5 mm pitch) at (8.0,65.25,180°): **west** column x=5.9 —
  U18.6(66.25,LTC_SHDN→R80.2 N), U18.7(65.75,FAULT_N→R81.2 N), **U18.8(65.25,
  BAT_PROTECTED_P→R75.2)**, U18.9(64.75,BAT_SENSE→R75.1 S), U18.10(64.25,LTC_GATE→R76 S);
  **east** column x=10.1 — **U18.1(64.25,BAT_RAW→R77.1)**, U18.2(64.75,LTC_UV→R79.2),
  U18.3(65.25,LTC_OV→R77.2), U18.4/5 GND.
- **R75** (2.8,65.0,-90°): R75.2 (BAT_PROTECTED_P) y=67.963 — **2.7 mm NORTH of U18.8**
  (why U18.8 must escape north); R75.1 (BAT_SENSE) y=62.038 south. Pad extent
  x[2.188,3.412] y[60.363,69.638].
- **R75 is boxed on all four sides:** **Q3** (frozen, BAT_SENSE current path) north edge
  y=59.575 sits 0.788 mm below R75's south edge → R75 may move south at most ≈0.55 mm
  before the 0.200 mm floor; **board edge** to the west (pad already at x=2.188); **U18's
  courtyard** to the east (an R75 east move of +0.9 mm bare-shorts/overlaps — `s_r75e`,
  `s_r75e_n075` REJECT); R80/R81 to the north (moving R75.2 north is the wrong way). So
  R75 has ≈0.55 mm of purely-southern freedom and nothing else.
- **U18** has ≈2.7 mm of north headroom (to R80 south y=69.2) and ≈1 mm south (to R77);
  west and south translations bare-overlap R75/R77 courtyards (`s_w05`, `s_s05` REJECT).

## 3. The screen (all runs on `AQROOT_LOCAL=R80`; baseline conn 19, U18.8 legally open)

Bare-placement (real `kicad-cli` DRC vs the `place_003l` clean reference): 16/18 lawful
placements PASS; the two REJECTs are `s_s05` (U18 south, courtyard) and `s_w05` (U18 west,
courtyard); `s_r75e`/`s_r75e_n075` REJECT (R75 east courtyard/short).

Co-closure (does U18.7 **and** U18.8 **and** U18.9 — and every other required U18 pin —
close **legally**?). **No candidate beats the baseline's conn 19, and the maximum legal
state leaves U18.8 open:**

| candidate | U18 Δ (mm) | R75 | conn | outcome |
|---|---|---|---|---|
| `r80bl` (baseline) | home | home | **19** | U18.8 open (NO_VIA_SITE); all else closed; **DRC clean** |
| `s_e05/e10/e15` | east +0.5/+1.0/+1.5 | home | 19 | U18.8 open — east translation is invariant (never nears R75.2) |
| `s_r75smax` | home | south 0.55 | 19 | U18.8 open — R75-south-alone is neutral |
| `s_n05` | north +0.5 | home | 18 | U18.8 **closes** (inner I2), **U18.7 GATE_REJECTED** 0.25<0.30 |
| `s_n075` | north +0.75 | home | 18 | U18.8 closes, U18.7 open |
| `s_n10` | north +1.0 | home | 17 | U18.8 closes, U18.7 open, U18.2 open |
| `s_n115` | north +1.125 | home | 16 | U18.8 reopens + east opens (non-monotonic) |
| `s_n125` | north +1.25 | home | 17 | **all 5 west close**, but **east U18.1/U18.2/U18.3** GATE_REJECTED 0.275/0.296/0.284 < 0.300 |
| `s_ne0707` | NE +0.75/+0.75 | home | 19 | **PHASE A COMPLETE (fail=None) — but ILLEGAL: absorbs a 0.1248 mm BAT_RAW↔BAT_PROTECTED_P D-269 breach** |
| `s_e10n075` | E+1.0/N+0.75 | home | 18 | U18.2 open + clearance:1 |
| `s_align` | N+2.15 / R75 s0.55 | south | 17 | breaks the **U18.9 Kelvin** (U18.8 + U18.9 both open) |
| `s_alignB` | N+1.75 / R75 s0.5 | south | 18 | U18.7 + U18.1 open |
| `s_alignC` | N+1.95 / R75 s0.55 | south | 17 | U18.8 open |

## 4. Root cause — sharper than D-290: current-path nets on BOTH edges of U18

D-290 established the west three-into-one-corner (U18.7/U18.8/U18.9 at 0.5 mm pitch, room
for two) as an irreducible placement-geometry mutual-exclusion at fixed placement. 003S
tests the owner-approved placement lever and finds the wall is **broader**:

- **U18 carries a current-path net on EACH edge:** `BAT_PROTECTED_P` (U18.8, west) and
  `BAT_RAW` (U18.1, east). Both are `current path role` nets bound by the **0.300 mm D-269
  routed clearance** to their 0.5 mm-pitch neighbours.
- **A rigid U18 translation cannot change the 0.5 mm pitch on either edge — it only shifts
  which edge breaches 0.300 mm.** Moving U18 **north** raises U18.8 toward the fixed R75.2
  and does open a legal inner-I2 via for U18.8 (the "second escape" the micro-ECO sought —
  it genuinely exists), but the same north move crowds the **east** `BAT_RAW`/`LTC_UV`/
  `LTC_OV` escapes toward R77/R79 until they breach 0.300 mm (s_n125: 0.275/0.284/0.296
  mm) or lose their lane (s_n075/s_n10/s_e10n075: U18.2 NO_LEGAL_ESCAPE). At the low end
  (s_n05..s_n10) it is **U18.7** that breaks (its 0.15 mm B.Cu neck lands 0.250 mm from
  U18.8's new inner via — the exact D-290 arithmetic, casualty merely relocated).
- **The single "complete" candidate proves the point by breaking the floor.** `s_ne0707`
  is the only placement that reaches PHASE A COMPLETE — and it does so **only by absorbing
  a genuine 0.1248 mm clearance** between a `BAT_RAW` B.Cu track (9.25 mm @ 0.65,70.65) and
  a `BAT_PROTECTED_P` B.Cu track (1.35 mm @ 1.5,68.325), i.e. **41 % of the 0.300 mm D-269
  current-path floor**, in the tight west margin. Two current-path nets physically cannot
  both leave U18's 0.5 mm-pitch field with legal clearance; forcing both to close crams
  them to 0.125 mm. Per the task's own reject criteria (sub-floor clearance) and the
  D-286 no-absorption discipline, `s_ne0707` is **disqualified, not promoted**, and no full
  Phase-A run is warranted (the congested full run is *less* forgiving than this cheap
  R80 vehicle, so it would breach at least as hard).
- **R75 cannot relieve either edge:** it is boxed on all four sides; its only motion
  (≤0.55 mm south) drags R75.1 away from U18.9 and **breaks the Kelvin pair** (s_align:
  conn 17, U18.9 GATE_REJECTED). R75-south-alone (s_r75smax) is neutral (U18.8 stays 2.16
  mm north of R75.2).

**No bounded U18/R75 placement delta legally co-closes the U18 escape field. The maximum
legal state is the baseline: conn 19 with U18.8 open. Every move either leaves U18.8 open
(east/R75-alone), trades U18.8 for U18.7 or the east current-path pins (north), breaks the
Kelvin pair (R75-south + north align), or completes only by absorbing the D-269 floor
(s_ne0707).**

## 5. Why this re-escalates to an OWNER decision

The levers that *could* still open a third simultaneous current-path escape all fall
OUTSIDE the D-291 approved envelope:

1. **U18 rotation** (0/90/270°) relocates the `BAT_PROTECTED_P` trunk pad U18.8 off the
   west edge, which is a **western-block refloorplan** requiring R75/the D-275 bridge and
   the whole U18 field order to be redone — direction-2, not a D-284/285-class micro-ECO,
   and a direct risk to the frozen D-275/D-288 bridge.
2. **Moving the escape targets** R77/R79 (east) or R80/R81 (north) so a current-path net
   escapes a different corridor — outside the "U18/R75 only" scope; a refloorplan.
3. **A routing lever** (the D-290-refuted off-layer vacate of U18.7, or a U18.8 POFV/inner
   reorder) — its source was deliberately **reverted at D-290** and re-adding it re-opens a
   closed CTO decision; not a placement ECO.

Per the standing policy (CURRENT_STATE §5/§8, restated at D-289/D-290) and the 003S
charter's explicit instruction to **stop at exact-evidence exhaustion rather than broaden
scope**, the bounded U18/R75 placement space is decisively exhausted and closing
`BAT_PROTECTED_P` (U18.8) is again a genuine **OWNER decision** — now with the additional,
harder finding that the constraint is a *both-edges current-path* footprint geometry, so
even the approved micro-ECO cannot resolve it without either direction-2 (spread the
LTC4368 block / relocate an escape target) or re-authorizing a routing-side lever.

## 6. Integrity

No source, copper, placement or rule change survives this task; the authoritative PCB is
byte-identical (six layers, 0 tracks, 0 vias). **No DRC absorbed** into the authoritative
board — the lone `s_ne0707` absorption is the *disqualifier* on a throwaway scratch board,
explicitly rejected, never accepted. `place_003l` (D-285) preserved; D-275 and D-277..D-291
preserved; the 0.200 mm clearance, 0.25 mm hole-to-hole, **0.300 mm D-269 current-path**,
≥1.20 mm BPP trunk, 0.60 mm BAT_MAIN floors, six-layer stack/GND/safety/topology/net/
footprint/value/polarity and frozen `beta-full-reference-v1` all ENFORCED and untouched.
`phaseA_journal.json` restored to HEAD. `JLCPCB_READINESS` unchanged. Scratch evidence
(gitignored `checks/w/`): `cand_003s/*.json`, `screen_003s_results.json`,
`phaseA_003s_*.json`, `log_003s_*.txt`, `log_{batch,nsweep,conf,ne}_003s.txt`,
`drc_ne0707_check.json`. **NO PROGRESS EARNED: PCB routing 0 %, overall 74 %, readiness
~77 %.**
