# AQROOT Demo manufacturing preflight

Status: **BLOCKED** at board CONNECTIVITY.  Every fabrication CONTRACT on this
board passes -- package (`FAB1-FAB8`), BOM sourcing (100 % orderable, D-615),
population (`POP1-POP4`), land patterns (`LAND1-LAND6`, 311/311), keep-out
stackup (`KO1-KO5`), pour bonds (`P1-P4`), necks (`N1-N3`), placement
(`PL1-PL7`) and protected copper -- and the residual is **55 retained open
edges across 27 nets**.  Two of them, `USB_D_CONN_P` and the `USB_D_MCU` pair,
are parked on rulings rather than routes (D-618, D-620).

## RUN THIS FIRST: the zero-margin land (2026-09-05, D-620)

    python3 screen_land_escape_margin.py NET [NET ...] [--pad REF.NUM] -o OUT

Before any further routing attempt on this board, ask what a LAND can launch.
It is arithmetic, it needs no search, and it decides which tool the edge needs:

    margin <  0   UNLAUNCHABLE -- the netclass width is wider than this land can
                  ever launch.  Needs a licence or a placement change.
    margin == 0   EXACT -- buildable and unreachable AT THE SAME TIME.  KiCad
                  passes it (the promoted NFC transmit arms ARE this case) but
                  `maze3d.dru_overlay` and `qrouter.QBoard.grid` both add a
                  0.75-CELL guard band, so the required figure is `clr+0.75*G`
                  and strictly exceeds `clr` for EVERY G > 0.  No lattice at any
                  pitch can propose it.  Needs `route_local_two_pad`.
    margin >  0   ordinary; `max_lattice_mm = margin/0.75` is the coarsest
                  lattice whose guard band still fits.

Deterministic; non-vacuous to ONE MICRON (grow `U9.14` by 1 um per side and
`U9.15` flips `EXACT -> UNLAUNCHABLE`).  It measures PADS -- the package's own
arithmetic -- and deliberately not the routed copper around the land, so
`CLEAR` means "this package can launch this width", not "this net routes today".

**The board-wide reading, 109 lands over the 25 open non-pour retained nets:**

    CLEAR         103   path problems, not package problems
    EXACT           2   U11.9 /BQ25185_STAT1, U11.3 /BQ25185_STAT2 @ 0.200 mm
    UNLAUNCHABLE    4   U21.5  ACC_5V_LX    SWITCH_NODE 0.600 vs widest 0.250
                        U9.10  NFC_SUPPLY   P3V3        0.600 vs        0.300
                        U12.10 BQ25185_SYS  SYS_MAIN    0.800 vs        0.600
                        U12.11 BQ25185_SYS  SYS_MAIN    0.800 vs        0.600

`+3V3`'s eight stranded lands read **four EXACT** (`U4.2`/`U4.3`/`U4.5`/`U4.12`,
the BMI270 LGA at 0.600 mm), three CLEAR, one UNLAUNCHABLE (`U5.2`).  So the two
biggest open families on this board are one mechanism, and it is not congestion.

## The U9 north row is full to the micron, and the trade is 1-for-1 (D-620)

    U9.13  NFC_RFO1   NFC_RF   0.300 mm   margin N +0.0000   EXACT
    U9.15  NFC_RFO2   NFC_RF   0.300 mm   margin N +0.0000   EXACT
    U9.14  NFC_VDD_RF Default  0.200 mm   margin N +0.0500   CLEAR
                              0.200 + 0.250 + 0.250 = 0.700 mm, spent exactly

All three remaining `U9` edges are `DETOURABLE` with `NFC_RFO2` irreducible
every time.  Its 3-track cut is `NOT_A_CHAIN`; its SEVEN tracks are one chain
`U9.15 -> L6.1` and the maze relays `NO_PATH` at 0.100, 0.050 AND 0.025 mm --
which §1 says it must.  `route_maze_batch.py` therefore gained an
**exact-geometry relay**: a detour record may name an allowlisted
`route_local_two_pad` route as its fallback (same primitive that laid the
copper; only after the maze refuses; `exact_relay_pads` requires the same net
and the same two ends to the micron; every gate still judges it).

Spent, it priced the trade in both directions:

    RFO2 removed, nothing else      route_local_two_pad relays it   8.674 mm
    RFO2 removed, VDD_RF routed     C49.1 -> U9.14  8.698 mm, 2 vias, 55 -> 54
                                    open edges, GND improves, ZERO attributable
                                    DRC -- and then RFO2: NO_LEGAL_ESCAPE

Either order, one loses.  D-603's *"strict 1-for-1 trade"* is this row having
room for the copper already on it and not one track more.  **Correctly REFUSED;
no copper promoted.**  `NFC_RF` also gained a `width_cap`: the netclass asks
0.400 mm, the land caps it at 0.300 mm, and both promoted arms have always been
0.300 mm.

## USB_D_MCU_N / _P are a SEGMENT_WALL (D-620)

D-583 called them a *"crossing-copper wall"* -- the exact words the D-618
corridor unit was built for -- and nobody had pointed it there.  Pointed there:
hold out EVERY crossing track on the permitted layers (115 and 156, across 41
nets) and both are still `NO_PATH`.  *No detour transaction of any size opens
it.*  Under the `USB_D` single-layer `F.Cu` contract the blockers are pads, vias
and pours, which no eviction may take.  What remains is an `F.Cu` refloorplan of
the MCU fanout or a `.kicad_dru` section-6 ruling on a via that merely PIERCES
`In2`.

## NEXT: C17, priced but not taken

Three `U9` edges sit behind one channel that holds one track.  `C17` -- 100 nF
`+3V3` decoupler at `38.750, 30.250`, internal, no enclosure feature, exactly
what `apply_part_shift.py` and `placement_contract.py` PL1-PL7 were built to
move -- bounds the receive band.  Its move is bounded by three measured things:

    PL5   +0.675 mm   C17.1's +3V3 escape endpoint leaves the land past this
    PL5   +0.450 mm   C17.2's GND  escape endpoint leaves the land past this
    DFM   +0.225 mm   the GND barrel at 40.500,30.200 becomes via-in-pad past this

so a `C17` east transaction must relay BOTH escapes -- the shape D-619 promoted
for `Y1`.  Price it before taking it.

## USB-C data is half real copper, and the other half is a 0.395 mm band (2026-09-05, D-618)

    authority cd680964...  ->  ad708a5248c9e6b6edbf77dbcc2effe19b46f9d09a70243230cc11024ea924e1
    retained open edges     57 -> 56      open retained nets   29 -> 28
    ratsnest                73 -> 72      unconnected items    73 -> 72
    26 objects added, 4 removed and ALL FOUR LICENSED, zero zones, zero rule
    areas, zero .kicad_dru change
    14/14 verify_promotion;  FAB1-FAB8;  LAND1-LAND6;  KO1-KO5;  POP1-POP4;
    P1-P4;  N1-N3;  protected copper 15 nets / 393 objects IDENTICAL

D-583, D-599 and D-602 each refused the `J3 -> U10` USB connector corridor and
each ended by naming the same missing unit: **the SEGMENT.**  `--evict` takes
copper wholly inside a window and `--evict-whole` takes a whole net board-wide;
a track that merely CROSSES is reachable by neither, and D-602 proved no
whole-net eviction of ANY size opens this corridor because `/I2C_SDA_INT` is
load-bearing and cannot rebuild itself.  D-607 built the detour and D-607/D-617
spent it on POUR LANDS, where the reserved site is a DISC around a barrel.

**`screen_corridor_detour.py` is the same question for a LANE** -- read-only,
five questions, and the last two are the ones that make the answer worth a gate
run:

    1   SEGMENT UPPER BOUND   every crossing TRACK out (tracks only: a via has
                              no two ends, a pad is where a part is soldered)
    2   MINIMAL               reverse-greedy, re-proved on the real route_join
    2b  IRREDUCIBLE           per cut net, hold out every crossing track EXCEPT
                              that net's -- a refusal reads "no cut set of ANY
                              size that spares this net opens this corridor"
    3   THE LANE              route the edge for real with the cut held out and
                              sample the reservation off the path the router
                              WON.  D-602: 66 of the 83 cells on the straight
                              J3 -> U10 centreline were already blocked FOR THE
                              USB PAIR ITSELF, so a straight lane is a fiction
    4   THE RELAY             put every cut chain back between its own two ends
                              with the lane in force, in spec order, on a board
                              carrying the previous detour -- D-608's half

    python3 screen_corridor_detour.py NET [NET ...] \
        --plan-out PLAN.json --guard-out LANE.json -o SURVEY.json
    python3 route_maze_batch.py NET [NET ...] \
        --detour-spec PLAN.json --guard LANE.json --promote

`--plan-out` / `--guard-out` write the transaction straight from the
measurement.  Re-derived from the PRE-promotion board with the finished
instrument, both files come back BYTE-IDENTICAL (`ef4a3ea8...`, `30d95325...`).

**SEARCH AT THE GEOMETRY, JUDGE AT THE RATIO, AND THEY ARE NOT THE SAME LEVER.**
A lane is not a disc, so the ceiling is `was + 2*(lane_mm + 2*pi*R)`; beside it
`--max-detour-ratio` (3x) refuses what D-607 called a reroute wearing a detour's
name.  D-617 measured that `max_mm` is ALSO the wavefront budget and a via
spends `via_cost_mm` of it before buying distance, so using the ratio as the
budget reports NO_PATH for routes that exist -- `Net-(J3-CC1)` relays in
**2.359 mm with two barrels** and refuses inside its own 3.924 mm ratio bound.
A rejected relay is also reverted before the next chain is measured: `/SD_CS_N`
reads 13.211 mm / 0 vias without the refused `/I2S_LRCLK` reroute in the way and
16.012 mm / 2 vias with it.

**PROMOTED.**  `USB_D_CONN_N`, `J3.A7`/`B7` -> `U10.1`: **11.323 mm of 0.250 mm
`F.Cu`, ZERO vias, ZERO `In2` pierce** -- `.kicad_dru` section 6 in its own
words -- 1.35x an 8.403 mm direct leg against a 25 mm `diff_pair_uncoupled`
budget.  Three chains moved between their own two ends:

    /I2C_SDA_INT    8.4149 -> 12.0863 mm   2 barrels   F 5.591 + In2 6.496
    /SD_CS_N       12.1504 -> 13.2110 mm   0 barrels   F 13.211
    Net-(J3-CC1)    1.3081 ->  2.3320 mm   2 barrels   F 0.552 + B 1.780

**THE OTHER HALF IS ONE NET.**  `USB_D_CONN_P`: 48 crossing tracks / 11 nets,
all cut and it opens in 6.275 mm -- not a placement wall.  Minimal cut is FOUR
tracks, `/I2S_LRCLK` once and `J3.A1`/`B12`'s ground escape three times, and
question 2b makes it final: **IRREDUCIBLE `GND`.**  The escape will not relay
either.  `evidence/d618-j3-south-band.json`, every figure off the board:

    SOUTH BAND    146.955 + 0.200  ..  148.050 - 0.500   =  0.395 mm
                  ONE 0.250 mm track; two need 0.700 mm
    NORTH PINCH   J3's own NPTH peg east edge      46.215
                  J3's own SH shield land west     46.820      gap 0.605 mm
                  the peg owes hole_clearance 0.250 mm, so the widest track
                  that fits is 0.155 mm.  GND is 0.300 mm: SHORT BY 0.145 mm
                  (board minimum 0.150 mm fits by 5 um -- not a position this
                  project will take, and no licence for it is written)
    SOUTH BARREL  a 0.600 mm via needs centre y >= 147.355 and the edge
                  clearance caps it at y <= 147.250.  NONE fits.

`J3.A1`/`B12` is an `F.Cu`-only SMD land in a `+3V3` pour; its only path to
ground is a track east to a barrel; the only route east is that band; and the
D+ short needs the same band to leave the connector.  **They are competing for
one track's width.**

**PARKED AS A MECHANICAL QUESTION.**  The band needs 0.750 mm and has 0.395 mm;
moving `J3` north by >= **0.355 mm** delivers it and leaves the pinch alone.
`J3` sits on the bottom edge against the enclosure's continuous edge-capture
rail, so that is a mechanical interface change and an owner decision -- recorded
with its exact number, not raised and not taken.

**NEXT: the four `U9` NFC edges** (`NFC_VDD_D`, `NFC_VDD_A`, `NFC_VDD_RF`,
`NFC_RFI1`/`RFI2`, one open edge each at 10.5-18.7 mm).  NFC is Demo-required
and D-607 named the `U9` west channel as one of the four walls the segment unit
was built for; it now has the instrument.

## The BOM is 100 % orderable, and the safety part was ordered in the wrong package (2026-09-05, D-615)

    authority c8e421aa... UNCHANGED -- 0 objects added, 0 removed, no copper
    FAB7 coverage        75.3 %  ->  100.0 %   (186 -> 247 of 247 references)
    needs_a_sourcing_decision   26 lines / 45 parts  ->  ZERO
    fab_package_contract.py     FAB1-FAB8 PASS, for the first time
    14/14 verify_promotion;  POP1-POP4;  P1-P4;  N1-N3
    protected copper 15 nets / 393 objects IDENTICAL

D-614 stopped for a stated reason: **D-096 binds** -- a part number configured
from an ordering scheme is a hypothesis until a distributor record confirms
lifecycle and stock, and that session had none to read.

**THE INSTRUMENT IS A RECORD THAT IS KEPT.**  `jlc_live.py` reads the JLCPCB
parts catalogue -- the same one D-167, D-176, D-179, D-202, D-206, D-210, D-211
and D-223 were confirmed against -- and writes every answer to
`evidence/jlc-live/` with the UTC minute it was read, **225 archived queries**.
It replays the archive unless `--refresh` is given, which is what makes a ruling
built on it reproducible: the four plans D-615 wrote, replayed against the
`HEAD` schematic in an isolated tree, return **all ten sheets AND the project
symbol library BYTE-IDENTICAL, 11 of 11**.

**`rule_open_sourcing.py` -- the gates measure the consequence.**  Land (the
direct `C26` guard), magnitude, tolerance, RANKED dielectric, `net_gate`
unchanged, a NEW dissipation gate built in `net_gate`'s image (2x operating AND
survives single fault), vendor (D-206: *a loose keyword search returns a
plausible WRONG part more often than it returns nothing*) and stock in two
limbs -- the hard one is whether the first build can be bought, the comfort
floor is FLAGGED and never used to refuse a part that already has ten times what
the build needs.

Three things the obvious answer would have got wrong:

    R69 is 1.87 ohm  ->  0603WAF187KT5E  C422967
    0603WAF1873T5E   ->  187 kOhm        C22896
        one character, five orders of magnitude, two catalogue records

    R95's node over-bound UNDERSTATES its dissipation: V^2/R across the node
    gives 54 mW, but the single-fault case puts a reversed cell IN SERIES
    with VBUS and the answer is 154 mW

    R24 and C12's Value strings are LOOSER than their own symbol notes --
    `12R` against "12R 1 percent", `22uF` against "specified X7R 16 V in
    1210".  A 5 % part satisfies the STRING and contradicts the DERIVATION.

The dissipation gate needed 31 node voltages that did not exist, so `NET_MAX_DC`
grew **17 -> 48** established nodes, each naming the supply or part limit that
bounds it.  `LTC_GATE` came from the board itself: the U18 footprint's own
description gives the LTC4368 charge pump **up to 13.1 V above VOUT**.

`R75` is gated on a part CLASS.  `15mR 1% 1W` is satisfied on paper by a thick
film at +/-1500 ppm/degC -- 19 % of drift over -40..+85 degC, on the shunt that
sets the LTC4368's 3.33 A trip.  The gate requires a current-sense / alloy part
at <=100 ppm/degC.

**THE FINDING.**  `screen_part_land_parity.py` asks D-613's `C26` question of
every sourced line at once, against the catalogue's own package field.  119
lines carry a code, 75 are comparable, **74 MATCH and `U18` did not**:

    board land       Package_SO:MSOP-10_3x3mm_P0.5mm
    BOM order code   LTC4368IDD-1#PBF
    live record      DFN-10-EP(3x3), body 0.75 mm  (MS variants 1.1 mm)

`DD` is DFN.  D-099 locked `LTC4368IMS-1#PBF`, MSOP-10, under FBV2-PWR-002 --
*"no bottom-terminated parts"* on the most safety-critical component -- and
corrected the FOOTPRINT while the identity stayed DFN.  The **cached library
symbol AND the project `.kicad_sym`** both still carried it, with a `Package`
field describing a DFN beside a `Footprint` field already reading MSOP-10, so
*Update Symbols from Library* would have undone an instance-only fix.
Corrected to `LTC4368IMS-1#TRPBF`, LCSC `C688401` -- the tape-and-reel order
code of the identical device (D-210's precedent), not an electrical change.

`apply_bom_sourcing.py` gained the primitive that made that auditable: a
correction must NAME the exact string it overwrites -- `replaces` for a symbol
property, `text_replaces` for a file -- or nothing is written.  The third
verdict of the parity screen is **UNCOMPARABLE**, stated out loud for 44 lines,
because a footprint named `MAX17048_T822` names a PART and counting it as a
pass would be D-611's failure again.

**STILL OPEN, AND IT IS PURCHASING.**  Nine lines sit under 10x the first-five
need on the assembler's own catalogue, five reading ZERO (`J5`, `L4`, `MK1`,
`U19`, `U9`; then `Q2`/`Q3` 0, `U2`/`U3` 1, `U18` 3, `D8` 7) -- mostly CONSIGNED
classes under D-206, so a brief to work.  `evidence/d615-purchasing-short.csv`.

**NEXT: NO FABRICATION CONTRACT HERE IS OPEN, so the next blocker is the one no
contract MEASURES -- 199 `lib_footprint_issues` and 48
`footprint_symbol_mismatch` warnings are 247 unproven claims that each LAND
matches its part's datasheet drawing.**  `U18` is the proof the class is real
and that these checks cannot see it: the land was right and the ORDER CODE was
wrong, and nothing here noticed until a distributor was asked.

## The BOM is three quarters orderable -- 122 identities grafted, four gates that had never been run (2026-09-05)

    FAB7 SOURCING   64 -> 186 of 247 orderable    25.9 % -> 75.3 %
    board       c8e421aa...  UNCHANGED, byte for byte
    package     26 of 28 artifacts normalised-sha IDENTICAL to D-613's;
                the two that changed are the two BOM views
    schematic   487 properties across 9 sheets, inserted as text, CRLF kept
    reproduce   screen --plan | apply --apply, replayed against HEAD in an
                isolated tree, returns all ten sheets BYTE-IDENTICAL

    EXACT_PRIOR       31 lines  114 parts   value string and land equal
    CONTAINED_PRIOR    4 lines    7 parts   a ruling, stated and checked
    REFERENCE_RULING   1 line     1 part    J8, from this project's D-238
    TUNE_PENDING       8 lines   16 parts   the VALUE is not final
    NO_CANDIDATE      26 lines   45 parts   a new purchasing decision

**FOUR THINGS THE MECHANICAL ANSWER WOULD HAVE GOT WRONG.**

*(1) The prior's manufacturer column does not describe the approved part.* For a
REJECTED audit row `JLC Manufacturer` names the match that was THROWN OUT, and
**16 of the 31 grafts are REJECTED rows** -- copying it stamps
`Samsung Electro-Mechanics` on Murata's `GRM31CR71E106KA12L`. That is D-613's
`C26` defect rebuilt by machine. The manufacturer is now DERIVED from the
approved MPN's own part-number family and CORROBORATED against the prose.

*(2) The rating belongs to the PART, not to the line.* The first version of this
gate derated the schematic string and refused `C38`/`C67` -- `1uF 10V X7R` on
the 5.5 V `ACC_5V_SW` rail is 1.8x -- but the audit approved a **25 V** part for
exactly that margin. Rating, dielectric, tolerance, capacitance and **land** are
now decoded from the part number (YAGEO `CC`, Samsung `CL`, Murata `GRM`, CCTC
`TCC`, UNI-ROYAL `0603WAF`), each code corroborated by a note in this
repository. The land decode refuses `CL21A475KAQNNNE` on an 0603 line -- the
`C26` defect caught one step earlier, before it can be written.

*(3) The designator is not the identity.* Three beta-dm audit rows name a
different VALUE at the same designator -- `R70`-`R73` 39R there / **33R** here,
`R69` 2.55R / **1.87R**, `R19`/`R20` 4.7k / **2.2k** -- because D-079 re-derived
the backlight against the real panel. Nothing matches on a designator.

*(4) The 0 ohm current gate was never run on five of the eight links.* The
beta-dm note closes it for `R32`/`R35`/`R42`; the Demo has **eight**, and
`R121`/`R122` (speaker) and `R106` (whole NFC front end) were not in that set.
Every grafted 0 ohm reference now carries a number or the line is refused --
`R35` 0.500 A, `R121`/`R122` 0.292 A, `R106` 0.150 A -- against a 1 A jumper.

**TWO DEFECTS IN THE INSTRUMENTS.** The value parser read one suffix letter, so
`15mR` did not parse and **`R75`, the 15 mOhm 1 W battery sense, came back with
no requirement at all**; unreadable values are now REPORTED. And `MANIFEST.json`
hashed only the ROOT schematic sheet while this work changed **nine child sheets
and not one byte of the root** -- all ten are now hashed and FAB1 requires every
one to match.

**THE RESIDUAL IS TWO DIFFERENT THINGS.** FAB7's PASS condition is unchanged,
but the failure is PARTITIONED: **16 parts are `TUNE`** (DEVICE_SPEC s.14, the
NFC matching network, values pending VNA + the ST tool) and no part number can
close them. The real purchasing list is **26 lines / 45 parts**, written out
with requirement and nets in `evidence/d614-sourcing-open.csv`. Two carry
recorded constraints: `C65`/`C66` (S-4/B-69 -- their DC-BIAS-DERATED value sets
the `U21` boost start-up) and `R75`.

**NEXT: rule the 26 open purchasing lines.** D-096 binds -- a part number
configured from an ordering scheme is a hypothesis until a live distributor
record confirms lifecycle and stock. Full notes:
`docs/full-beta-v2/AQROOT_DEMO_FABRICATION_PACKAGE.md`.

## The fabrication package exists, and the review found three things (2026-09-05)

    package    hardware/demo/fab/            28 artifacts, 24 reproducible
    generator  export_fab_package.py         one command, kicad-cli does the drawing
    review     checks/fab_package_contract.py   FAB1-FAB8
    board      c8e421aa...  UNCHANGED   ledger 57 open edges, row for row

    FAB1 PROVENANCE PASS   FAB5 CPL      PASS   247 rows, every X/Y/side matched
    FAB2 FILL       PASS   FAB6 BOM      PASS   4 views partition 310 symbols
    FAB3 LAYERS     PASS   FAB7 SOURCING FAIL   64 of 247 orderable -- 25.9 %
    FAB4 DRILL      PASS   FAB8 OUTLINE  PASS   72.000 x 148.000 mm, delta 0 nm
         802 holes on the board, 802 in the Excellon files, ZERO displaced

**FAB2 is not decoration.** Gerber export does NOT refill zones; it plots the
fill stored in the file. The claim is that the committed board is BYTE-IDENTICAL
after `--refill-zones --save-board`, so the copper these Gerbers plot is the
copper the promotion gate ran DRC on. Without it a stale stored fill ships
copper no check in this repository has ever inspected.

**FINDING 1 -- the BOM asked a supplier to quote forty-six test points.** Every
one of the schematic's 310 symbols says `(in_bom yes)`; 46 are `TestPoint`, and
the BOARD already carried KiCad's exclude-from-BOM attribute on those 46 plus
`BOSS1`/`BOSS2`. Nothing was reading it. The package now emits four views that
PARTITION the schematic once each -- `BOM-assembly` (122 lines / 247 refs),
`DO-NOT-POPULATE` (16), `NON-PURCHASED` (46), `OFF-BOARD` (1) -- and FAB6
refuses any divergence the board does not explain.

**FINDING 2 -- one part number on two land patterns.** `C26` (10 uF 10 V X7R,
1206) carried `C24`'s LCSC `C344022`, a 10 uF 25 V X5R **0603** part, with no
MPN to contradict it. Removed from `C26`: a blank forces a decision, a wrong
code does not.

**FINDING 3 -- `schematic_parity_clean` had never been asked.**
`verify_promotion.stage()` staged the board, the rules and the project and left
the ten `.kicad_sch` sheets behind, so KiCad had no schematic to compare and
returned an empty list. The check read TRUE on every promotion ever gated here.

    staged without the schematics     0 parity entries
    staged with all ten sheets      249 parity entries, 0 ERRORS

Repaired: every sheet is staged, `drc()` reports parity by type and severity,
and the check is `schematic_parity_within_baseline` against a recorded
`INHERITED_PARITY` -- still 14 checks, still 14/14, but the fourteenth means
something now. The 249 are all warnings: 199 symbol/footprint text fields, 48
attribute or library-nickname differences (46 of them the same test-point BOM
flag Finding 1 found independently), 2 board-only mounting bosses. No net, no
pin, no missing footprint.

**THE OPEN BLOCKER.** 183 of the 247 fitted, purchased, on-board references --
70 BOM lines, 110 R / 72 C / 1 J -- carry neither an MPN nor an LCSC code.
`screen_bom_sourcing.py` asks whether this repository already holds a reviewed
answer, under a deliberately brittle rule (value string and footprint leaf equal
character for character, because `10uF 10V X7R` and `10uF` are not the same
specification):

    EXACT_PRIOR    31 lines  114 parts    an audited decision already exists
    NEAR_MISS       0 lines    0 parts
    NO_CANDIDATE   39 lines   69 parts    27 C, 41 R, 1 J

**NEXT: graft the 31 after re-checking each against the Demo's own nets, then
rule on the 39.** Full notes:
`docs/full-beta-v2/AQROOT_DEMO_FABRICATION_PACKAGE.md`.

## The board now states its own population -- sixteen DNP flags carried from the schematic (2026-09-04)

The first fabrication blocker this project has CLOSED rather than characterized.

    authority 12a69da7... -> c8e421aa...
    16 lines changed, ALL of them `(attr smd)` -> `(attr smd dnp)`
    0 objects added   0 removed   0 zones   0 rule areas   0 nets claimed
    position-file rows with --exclude-dnp:   263 -> 247      16 parts, exactly
    14/14 verify_promotion;  POP1-POP4;  P1-P4;  N1-N3
    protected copper 15 nets / 393 IDENTICAL;  ledger 57 edges IDENTICAL

**WHAT WAS WRONG.**  `kicad-cli pcb export pos --exclude-dnp` reads the
FOOTPRINT attribute.  Every footprint said `(attr smd)`, so the exclusion did
nothing: **263 rows with the flag and 263 without**.  A factory handed that file
solders `C21 C22 C34 C35 C81 C82 L2 R107 R112 R119 R123 R44 R45 R68 R93 U13`
onto every Demo unit.  KiCad's own `--schematic-parity` compares nets and
footprint identity, not population, and reports CLEAN -- so
`verify_promotion.py` passed on every promotion ever gated, including the board
that carried this.

**THE CONTRACT MEASURES THE CONSEQUENCE, NOT THE FLAG**
(`checks/population_contract.py`, now part of the standing preflight):

    POP1  every schematic-DNP reference exists AND carries `dnp`
    POP2  no schematic-FITTED reference carries it (not sprayed)
    POP3  the two sets are EQUAL
    POP4  kicad-cli pcb export pos --exclude-dnp omits exactly those
          references and drops NO fitted one          <- the one that matters

**A TEXT EDIT, BECAUSE THE AUTHORITY IS A SHA.**  `pcbnew.SaveBoard` rewrites
the whole file; "Update PCB from Schematic" may move footprints and rebuild
nets.  `apply_schematic_population.py` edits the `(attr ...)` token list of the
named footprints and nothing else, is dry-run by default, prints every line it
touches, and REFUSES if a named footprint has no `(attr ...)` line to append to.

**CLAUSE 4'S CURRENCY IS OPEN EDGES AND THIS TRANSACTION HAS NONE.**  The
ledger reads 57 open edges before and after, row for row.  Clause 4 governs
COPPER transactions; a population fix must carry its own measured improvement,
and POP4 is it.

**NEXT: GENERATE THE DEMO FABRICATION PACKAGE FOR THE FIRST TIME AT THIS
AUTHORITY AND REVIEW IT** -- Gerbers, drills, BOM, CPL.  D-611 and D-612 are the
reason to expect more of exactly this kind: a defect invisible to every check
this repository owns, found only by running the tool a factory runs.

## The relief doctrine is SPENT -- and the board does not carry its own DNP flags (2026-09-04)

D-610's addendum ruled the next task was a MEASUREMENT, not a route.  This is
it, and the answer is unambiguous.  **No copper changed**; the authoritative
board is byte-identical at `12a69da7...`.

New tracked read-only screen **`screen_orphan_moves.py`**.  It names no land,
no net and no lever: it enumerates every ORPHAN ISLAND of every pour-owning net
and offers each one BOTH moves this board owns, at BOTH ends of the ladder.

    RELIEF  maze3d.stitch_pad   a barrel INTO the plane body -- needs the pour
                                to REACH the land
    JOIN    maze3d.route_join   the whole-board maze at the MAIN island's pads,
                                which join_residual_islands drives -- aims at
                                copper that is ALREADY CONNECTED

    ORDINARY    netclass width + 0.650/0.400 mm POWER barrel  (no licence)
    PERMISSIVE  0.200 mm + 0.350/0.200 mm D-257 barrel        (the most this
                board could EVER license)

The bracket is sound because `Field` is MONOTONE in both levers, so a refusal
at PERMISSIVE is a refusal on the whole ladder.

    21 orphan islands   84 measured answers   0 promotable moves
    relief   0 of 21 open at either rung
    join     3 open at PERMISSIVE, ALL THREE over the driver's own 8.0 mm
             REPAIR_JOIN_MAX_MM bound (9.815 / 10.749 / 8.340 mm)

    nets=3  orphan_islands=21  closable=0  out_of_bound=2  dnp_only=2
    (the third open join is the DNP phantom, classified out before the bound)

**THE TWO REFUSAL WORDS MEAN DIFFERENT THINGS.**  `NO_LEGAL_ESCAPE` is a POCKET
wall and narrowing IS the lever -- ten of the FOURTEEN lands that answered it at
ORDINARY escape at 0.200 mm.  `NO_BODY_VIA_SITE` is a POUR-SHAPE wall: the land
escapes, runs, and there is nowhere in the plane BODY for the barrel to land.
**No licence can move it**, because no licence changes where copper is poured.
**17 of the 21 islands answer `NO_BODY_VIA_SITE`** at the permissive corner;
the other four still cannot launch at all.

**ONE OF THE THREE JOINS IS A PHANTOM.**  `routing_ledger.py` -- the file the
gate's clause 4 scores against -- counts open edges over SCHEMATIC-FITTED
references only.  `maze3d.net_islands` has no population model and islands
every pad.  `BQ25185_SYS` islands TEN ways for the proposer and EIGHT for the
ledger; the two extra, `R68.1` and `U13.3`, are DNP -- and `U13.3` is the
closest-to-bound join found anywhere (8.340 mm against 8.0).  At 7.9 mm it
would have been proposed, searched, gated and REFUSED on clause 4 after being
paid for.  The screen now labels every island `FITTED` / `MIXED` / `DNP_ONLY`
from the ledger's own authority.

**AND THE BOARD DOES NOT CARRY THE SCHEMATIC'S DNP FLAGS -- A FABRICATION
BLOCKER** (`evidence/d611-population-trap.json`):

    schematic references marked DNP                   16
    board footprints carrying the DNP attribute        0

A CPL generated from this board would place all sixteen; `kicad-cli
--exclude-dnp` reads the FOOTPRINT attribute and these footprints say
`(attr smd)`.  **KiCad's own `--schematic-parity` does not catch it** -- the
gate reports `schematic_parity_clean: true` on this very board.

**THE LARGEST SIGNAL GROUP REFUSES TOO, AND THE LAYERS ARE HALF EMPTY.**
`/I2C_SCL_INT` (internal I2C clock, 5 open edges) offered the maze in
`--partial` mode closed NONE of eleven MST pairs.  Measured global capacity on
the three layers a signal may use: **F 55.2 % / B 50.9 % / In2 59.2 % FREE**.
The wall is LOCAL pad-pocket congestion, not a full board.

**ONE RULE SENTENCE CORRECTED.**  Section 13 of the `.kicad_dru` read "0.200 mm
... is the ONLY combination that reaches the plane body".  `probe_vout_grid.py`
streams its output after every row and it was STILL RUNNING when D-610 was
written -- the cited file was a 33-of-36 snapshot.  Complete, the grid says
**TWO of 36** reach the body, both at the fine barrel and both from `U12.4`:
0.200 mm over 2.756 mm and 0.150 mm over 2.702 mm.  The promotion is unaffected
and strengthened: 0.150 mm is the `.kicad_pro` `min_track_width`, BELOW the
0.200 mm section 9 grants anywhere, so it is not licensable -- 0.200 mm is both
the wider rung and the only licensable one.  The whole D-610 promotion re-gates
**14/14** against the corrected rule file.

**NEXT.**  The sixteen DNP flags -- the first genuine fabrication-package
blocker, bounded and gateable -- then GENERATE the Demo fabrication package for
the first time at this authority and review it.  **The pour residual is CLOSED
as a routing question:** all 19 ledger-counted open edges on `+3V3`,
`BQ25185_SYS` and `GND` are measured refused by both moves within this board's
own electrical bounds.  Do not replay without a CHANGED BOARD -- a pour shape
or a placement, both decisions above ordinary routing.

## The 3.3 V rail is bonded to its own regulator -- and two defects in the pour-bond guard (2026-09-04)

D-608 discovered that `+3V3` had no connection of any kind to `U12`, the
`TPS63020` that MAKES it: every part on the rail was fed by a plane with no
source, and the Demo could not have worked.  D-609 proved the bond closes and
was refused twice -- six real `track_width` errors, and a `BQ25185_SYS`
regression.  Both refusals are now answered, and **the second one was not the
run's fault**.

    authority 78280a13... -> 12a69da7...
    retained open edges   58 -> 57      improved +3V3      REGRESSED NONE
    unconnected items     74 -> 73      attributable DRC   0
    8 objects added (7 tracks + 1 via), ZERO removed, zero zones
    2 rule areas, both licences AUTHORED BEFORE THE ROUTER RAN
    narrow copper 2.756 mm -- ALL of it strictly LICENSED, none by courtyard
    14/14 verify_promotion, P1-P4, N1-N3;  protected copper 15 nets / 393 IDENTICAL

**THE FIRST WIDTH LICENCE THE ESCAPE-RELIEF DOCTRINE HAS EVER SPENT.**  Section
12 of the `.kicad_dru` licenses a BARREL and says nothing about width.  D-609
ran the `VOUT` bond on the board's `intersectsCourtyard` necking rule alone and
measured what that is worth: of eight narrow tracks, KiCad licensed the **two**
that intersect `U12`'s courtyard and flagged the **six** that do not, and
**zero** were wholly inside one.  `FBV2_P2_ROUTING_PLAN.md` section 17 clause 2
names that shape as the one a relief must never lean on.  New section 13 grants
a track width inside `PAD_ESCAPE_RUN_U12_4` -- `enclosedByArea`, all-or-nothing
per object -- and all seven tracks of the promoted run are licensed by their own
pad's area, proved twice: `audit_narrow_copper.py` reports 7 LICENSED / 0 INSIDE
/ 0 INTERSECTS / 0 OUTSIDE with `unlicensed_mm` 0, and new
`verify_promotion.py --relief-run` grows each track's centreline into the
stadium of its own copper and subtracts it from the area polygon, exactly as
`--bridge` already does for a barrel.

**THE RECTANGLE IS DECLARED, NOT DRAWN ROUND WHAT THE ROUTER LAID.**  A barrel
is a point, so D-606 could size its area from it.  A RUN has an extent, and an
area sized from the run would be a licence whose size the router chooses -- a
blank cheque in the currency this board treats as most expensive.  The
rectangle therefore lives in a tracked spec,
`evidence/d610-relief-run-areas.json`, reviewed and committed WITH the rule, and
`--relief-run-area` draws that rectangle and no other.  `maze3d._run_licence`
refuses `NO_RUN_AREA_SPEC`, `NO_DRU_WIDTH_LICENCE` and
`RUN_OUTSIDE_LICENCE_AREA` inside the proposer.

**TWO DEFECTS IN THE POUR-BOND GUARD** (`evidence/d610-guard-defects.json`), and
between them they are the whole of D-609's `BQ25185_SYS` regression:

  1. **AN ANCHOR NEED NOT BE A PAD.**  `pour_bond_guard.build` dropped every
     island bonding fewer than TWO PADS before either clause was consulted.
     Right for `SMALL_ISLAND`, which builds an MST over the island's pads.
     WRONG for `NO_ESCAPE`, whose own comment already names a VIA as an anchor.
     `BQ25185_SYS` island 3 is **95.410 mm2 and bonds ONE pad -- `U12.1`, which
     `no_escape_pads` reports dead -- plus ONE via**, so nothing kept the
     `VOUT` run out of it.  All 46 previous tubes come back BYTE-IDENTICAL, one
     is added, and two islands now report `NO_ANCHOR` instead of being skipped
     in silence.
  2. **A TUBE HAS A WIDTH PER POINT.**  `geodesic` published the single erosion
     radius the WHOLE path survives as the keepout at every point of it -- which
     is the width of the NARROWEST place.  That tube is 0.200 to 0.350 mm wide
     where it leaves `U12.1` and **0.025 mm at a pour finger twelve millimetres
     away**, so 15.197 mm of bond was published at a 0.275 mm keepout.  Each
     point now carries the widest disc that fits THERE, capped at the spec's own
     `--tube-radius`, so **no keepout anywhere exceeds the 0.375 mm every tube
     on this board already used** and the narrow places are unchanged.  Eight
     tubes across `+3V3`, `GND` and `BQ25185_SYS` were under-protected.
  3. **AND A BARREL IS NOT A TRACK.**  `maze3d.Field` ANDed `via_ok` with the
     guard mask built from the TRACK width, over the layers the net may ROUTE
     on.  A through barrel is copper on every layer and three times as wide.
     The relief planted a 0.65 mm barrel **0.5315 mm** from the tube -- clear of
     the 0.475 mm the track mask asked, **0.0685 mm inside the 0.600 mm the
     barrel owes** -- its antipad ate the tube, KiCad's refill pruned the
     remainder, and `U12.1` came away on a 0.473 mm2 island of its own.

**`--repair-planes` WAS CARRIED AND HAD NOTHING TO DO.**  D-609's fourth
next-step was to re-stitch the `BQ25185_SYS` pour inside the same transaction.
The flag is spent here and `plane_repair.candidates` comes back EMPTY: with the
guard corrected, no pour-owning net regressed at all.  That is D-585's own
stated preference -- "a bond that no router move can restore must not be broken
in the first place" -- and it is the only outcome that could have worked, since
`U12.1` is `NO_LEGAL_ESCAPE` (which is why `no_escape_pads` calls it dead) and
`SW9.2` is D-604's pad that stitches at every rung and closes nothing.

**THE ELECTRICAL RULING, REMADE BECAUSE ITS PREMISE IS GONE.**  D-609 ruled the
bond "SOUND AT TWO PARALLEL NECKS, THIN AT ONE" and required the promoting
transaction to lay both.  It could see two only because a barrel was being
allowed to sit inside the `U12.1` bond tube.  With the guard corrected exactly
ONE neck exists: `U12.5` answers `NO_BODY_VIA_SITE` at every rung of the width
ladder crossed with every rung of the barrel ladder, and only the 0.35/0.20 mm
fine-pitch process reaches the plane body at all
(`evidence/d610-vout-grid.json`).  New `audit_bond_ampacity.py` re-derives
`.kicad_dru` section 5's own printed table to within 0.9 % before it rules on
anything, then measures the bond:

    0.200 mm outer neck, 2.756 mm      0.742 A at dT = 10 K, 1.006 A at 20 K
    series resistance                  6.83 mOhm -- 4.4 mV at the 0.64 A peak
    0.35/0.20 mm barrel, plated wall   1.457 A -- NOT the bottleneck
    P3V3 design current 1.0 A;  measured peak 0.64 A

**One neck is promoted, knowingly derated.**  0.742 A clears the measured peak
by 16 %, clause 4's 6.0 mm width review trigger does not engage at 2.756 mm, and
the alternative is a rail with no source.  This board has taken the trade before
and said so: D-607 promoted a 0.150 mm `GND` bond at board setup's own minimum
because "an open ground contact on the display connector is worse than a thin
one".

**AND ONE MORE HOLE, FOUND BY THE NEW LICENCE.**
`verify_promotion.bridge_proof` read a missing constraint as a ZERO floor, so a
rule area whose rules say nothing about barrels licensed every barrel inside it.
`PAD_ESCAPE_RUN_U12_4` is the first such area to exist and it licensed this
promotion's barrel on a rule that never mentions one.  A licence must now STATE
all three barrel constraints -- the read `maze3d.area_licence` has always made.

**ADDENDUM -- A LAND THAT WAS NEVER ASKED IS NOT A LAND THAT REFUSED.**
`relief_stitch`'s `pads=` filter (`--relief-pad`) skips lands the transaction
did not name, and a skipped island set no `last` entry -- so it fell through to
the `NO_ESCAPE` default, **the same word `stitch_pad` returns when it has
actually looked and found nothing**.  The gate evidence above therefore carries
eight `+3V3` lands -- `U4.2`, `U4.3`, `U4.5`, `U4.8`, `U4.12`, `R129.1`,
`R39.1`, `U5.2` -- recorded as refusals that were **never tried**, because
`--relief-pad` named only `U12.4`/`U12.5`.  A reader pricing the next iteration
off that file would have written the whole `U4` family off unmeasured.  The
label is now `NOT_OFFERED` and it names the lands.  When `pads` is None -- every
caller before D-609 -- the branch cannot be reached and the output is
byte-identical; **zero copper changes and the promoted board is untouched.**

**AND THE PROMOTION IS REPRODUCIBLE, WHICH IS HOW THIS WAS PROVED**
(`evidence/d610-relief-repro.json`).  Driving the proposer at the D-610
pre-promotion authority `78280a13...` carrying the PROMOTED `.kicad_dru` -- the
board, the rules and the `.kicad_pro` together, as D-607 requires -- returns the
stitch object for object: `U12.4`, 0.200 mm, one 0.35/0.20 mm barrel at
(65.2, 98.8), 2.756 mm, inside `PAD_ESCAPE_RUN_U12_4`, bbox identical to the
gate's.  The same run returns the eight islands as `NOT_OFFERED`.

**NEXT, AND IT IS A PLACEMENT QUESTION.**  `L1` sits 0.41 mm off `U12`'s
courtyard and boxes the `VOUT` row into a 1.4 mm corridor that must also carry
`BQ25185_SYS`'s pour bond to `U12.1` and `V3V3_FB`.  That corridor is why one
neck is all the geometry admits.  Moving `L1` changes a switching converter's
own loop -- the highest-risk geometry section 4 of the `.kicad_dru` governs --
and is a Full Beta v2 item, not a Demo edit.  The next Demo routing iteration
should take the `+3V3` `U4` BMI270 family or `GND`'s residual orphans -- but it
must MEASURE them first.  Their `NO_ESCAPE` records were the mislabel above, so
the size of that group is **not yet a board fact**; the first move is a read-only
relief offer naming those eight lands, which is now the cheapest measurement on
the board.

## The U12 VOUT bond is a WIDTH wall, not a pocket wall -- and the own-layer detour built, spent and priced (2026-09-04)

D-608 left one named next task -- bond the `TPS63020`'s own `VOUT` island to
the `+3V3` plane, "the single highest-leverage fabrication blocker on this
board" -- and one named lever for it: let a detour re-lay a track on the layer
it ALREADY lawfully occupies.  Both were done.  **The lever works and the task
it was built for turned out not to need it**, because the wall it was aimed at
was never where D-608 measured it.

    authority 78280a13... UNCHANGED -- no copper promoted this iteration
    +3V3       9 -> 8 open edges AFTER KiCad's own refill   THE BOND WORKS
    BQ25185_SYS 7 -> 8                                       and pays for it
    whole board 58 -> 58, clause 4 REFUSED; 6 real track_width errors, clause 3

**THE LEVER, BUILT AND MEASURED.**  `reserved_inner_planes` is a rule about NEW
copper: do not cut a slot through somebody else's plane.  A DETOUR is not new
copper -- it removes an existing track WHOLE and lays it again between its own
two end coordinates -- so the slot already exists and the only thing in dispute
is where within a millimetre or two of itself it runs.  New
`route_maze_batch.detour_layers` + `--detour-own-layer` +
`screen_segment_evict.py --relay-own-layer` grant exactly that, and grant the
TIGHTEST version of it: a detour that spends the allowance is given **that one
layer and nothing else**, so by construction it can add no via -- a
single-layer `Field` has no second layer to via to -- and can reach no other
plane.  Gate clause `OWN_LAYER_ESCAPED` states that as a refusal anyway, so a
future caller who widens the allowance to a layer SET meets a stop rather than
a silent new hole through a plane.  `land_ok`-style default byte-identity is
preserved: without the flag `detour_layers` returns its input.

**AND IT MOVED THE CENSUS.**  D-608 measured 111 tracks / 969.6 mm on 29
(net, layer) pairs, every one on `In3.Cu`, as `UNDETOURABLE_LAYER` -- cut and
never put back.  Re-priced with the allowance, that refusal is gone and the
survivors answer on GEOMETRY instead: `/01_POWER_TREE/V3V3_FB`, the track that
now crosses the `U12` pocket, comes back `NO_PATH` past an 8 mm reserved disc
inside a 74.4 mm budget -- a corridor question, not a policy one.

**THE BOARD MOVED UNDER THE MEASUREMENT, AND THAT IS THE FIRST LESSON.**
D-608's own join merged `U12.4` and `U12.5` into ONE island, so
`screen_segment_evict.py` -- whose site is decided by whichever pad of an island
is tried first -- now answers with a different pad, a different site
(66.6, 96.0), a different pair of crossing tracks and an **8 mm** disc where
D-608 recorded 0.8 mm.  New `--pad REF.NUM` names the land instead of
inheriting it, and re-asking `U12.5` by name reproduces the new answer rather
than the old one.  **A site measured on a board is a site measured on THAT
board**; a promotion that joins two orphans invalidates every stitch site of
both.

**THE WALL WAS NEVER THE BARREL AND NEVER THE POCKET.  IT WAS THE RUN.**
`w/d609/probe_vout_bond.py` and the new tracked `screen_pad_width_ladder.py` ask the current board
from scratch, rung by rung, one lever each:

    run width   U12.4                     U12.5                    barrel
    0.400 mm    NO_LEGAL_ESCAPE           NO_LEGAL_ESCAPE          0.65/0.40
    0.400+neck  NO_BODY_VIA_SITE          NO_BODY_VIA_SITE         0.65/0.40
    0.350 mm    NO_BODY_VIA_SITE          NO_LEGAL_ESCAPE          0.65/0.40
    0.300 mm    NO_BODY_VIA_SITE          NO_LEGAL_ESCAPE          0.65/0.40
    0.250 mm    NO_BODY_VIA_SITE          NO_LEGAL_ESCAPE          0.65/0.40
    0.200 mm    OK  B.Cu 2.928 mm         OK  B.Cu 3.052 mm        0.65/0.40
    0.150 mm    OK  B.Cu 2.856 mm         OK  B.Cu 3.019 mm        0.65/0.40

At 0.200 mm **both** `VOUT` pins escape, run under 4.2 mm and plant an
**ORDINARY 0.65/0.40 mm POWER-class through barrel inside the plane BODY** --
no relief barrel, no `.kicad_dru` via licence, no segment eviction, nothing
D-606 or D-607 built.  Offered the SAME transaction they take two independent
barrels, `U12.4` -> (65.1, 99.0) in 2.928 mm and `U12.5` -> (64.1, 98.7) in
4.157 mm, which is what the rail actually wants: two parallel paths, not one.

**THE POUR ALTERNATIVE IS PRICED AND REFUSED.**  A bounded `+3V3` pour on
`B.Cu` over the `VOUT` lands would owe no track width at all -- two-dimensional
copper -- and this board already carries two bounded `B.Cu` pours
(`BQ25185_SYS`, 114.2 and 10.8 mm2).  `probe_vout_via_sites.py` maps every
via-legal cell within 4 mm of the pins: at the netclass barrel there are 94, at
the POWER floor 177, and **every one of them is also plane BODY** -- but the
nearest is (65.1, 99.0), **2.0 mm away**, and the corridor to it threads the
0.29 mm gap between `/01_POWER_TREE/V3V3_FB`'s track and `Net-(L1-Pad2)`'s.
A zone cannot thread a corridor a 0.2 mm track barely fits.  The pour is not
the lever here.

**THE GATE RUN, AND WHY BOTH ITS REFUSALS ARE THE ANSWER.**
`--relief-extra-width` adds ONE more rung to the relief ladder and the BOARD,
not the caller, says how narrow it may be: the rung is clamped up to
`min_track_width` and to `maze3d.neck_rule`'s own minimum -- the 0.200 mm the
`.kicad_dru` "Pad-escape necking - width, fine-pitch power packages" rule
already grants inside the ten courtyards it names, `U12` among them.
`--relief-pad` names the lands a relief may be spent on, because offering a
licence or a narrow rung to every orphan on the board is how one measured
exception becomes twenty unmeasured ones.  Run on `+3V3` at
`--relief-via 650000:400000 --relief-extra-width 200000 --relief-pad U12.4
--relief-pad U12.5 --body-landing`:

  1. **THE BOND WORKS.**  After KiCad's own `--refill-zones` the fitted-pad
     ledger moves `+3V3` **9 -> 8**.  The regulator's output island is
     connected to the rail it makes.  8 tracks, 2.787 mm, one 0.65/0.40 barrel
     at (65.2, 99.1), zero rule areas, zero `.kicad_dru` change.
  2. **SIX REAL `track_width` ERRORS**, and they are the doctrine's own
     warning made visible.  New read-only `audit_narrow_copper.py` asks
     where each sub-class-width track lies relative to the courtyards the
     necking rule names, and **agrees with KiCad object for object**: 2 of the
     8 tracks INTERSECT `U12`'s courtyard and KiCad licensed exactly those 2;
     6 lie OUTSIDE every named courtyard -- **2.0196 mm of copper north of
     `U12`, between (65.2, 99.1) and (66.725, 99.375)** -- and KiCad flagged
     exactly those 6 against "P3V3 minimum width on the outer layers".
     **ZERO tracks are WHOLLY INSIDE any courtyard**, so even the two that
     passed did so by `intersectsCourtyard`, which
     `FBV2_P2_ROUTING_PLAN.md` section 17 clause 2 names as the shape a relief
     must never lean on.
  3. **`BQ25185_SYS` 7 -> 8.**  The run crosses that net's `B.Cu` pour and
     severs it, so the whole board trades 58 for 58 and clause 4 refuses a run
     in which any net regresses.  `--repair-planes` exists for exactly this and
     was deliberately not spent on a run clause 3 was already going to refuse.

**THE ELECTRICAL REVIEW THE DOCTRINE ASKS FOR, DONE NOW SO THE NEXT
TRANSACTION IS NOT BLOCKED ON IT.**  Section 17 clause 4 makes a total
narrow-WIDTH run of 6.0 mm a REVIEW TRIGGER, "a new ruling, not an automatic
stop", and clause 6 says widen after escaping.  Two 0.200 mm bonds of 2.928 and
4.157 mm total 7.085 mm and trip it.  IPC-2221B at this board's own copper --
1 oz outer, dT = 10 K, the method that reproduces `.kicad_dru` section 5's own
table (0.300 mm -> 0.999 A against its printed 1.0 A):

    0.200 mm outer   0.745 A at dT=10 K      1.010 A at dT=20 K
    two in parallel  1.489 A at dT=10 K
    P3V3 design current 1.0 A;  measured peak 0.64 A
    R = 7.19 and 10.21 mOhm, 4.22 mOhm in parallel, 4.2 mV at 1.0 A

One neck alone already exceeds the 0.64 A measured peak at dT = 10 K; the pair
exceeds the 1.0 A DESIGN current with margin.  **The ruling is that the bond is
sound at two parallel necks and thin at one**, so the transaction that promotes
it must lay BOTH -- which `relief_stitch` cannot do today, because it breaks
after the first pad of an island that opens.

**NEXT, AND IT IS A SPEC RATHER THAN A SEARCH.**  Author ONE per-pad
`enclosedByArea` WIDTH licence -- the doctrine's own instrument, spent on
WIDTH for the first time -- over x in [65.05, 66.90], y in [98.45, 99.45] mm
with clause 7's 0.150 mm end-cap overhang, and teach the relief emitter to draw
an area around the RUN as well as around the BARREL; add the second parallel
bond; and carry `--repair-planes` so the `BQ25185_SYS` pour this run severs is
re-stitched inside the same transaction.  Then re-gate.  Nothing about that is
a search.

## Segment eviction built and spent: a crossing track is not evicted, it is DETOURED between its own two ends (2026-09-04)

D-602, D-603, D-605 and D-606 each ended by naming the same missing unit, and
D-606 made it the CRITICAL PATH.  Four independent walls ask for it -- the USB
connector corridor, the `U9` west channel, the `GND` and `BQ25185_SYS` pour
residuals -- and every one of them is **a foreign track lying across a pocket
that would otherwise hold a barrel**.  `--evict` removes copper WHOLLY INSIDE a
corridor window; `--evict-whole` removes a whole net board-wide; a track that
merely CROSSES the pocket is reachable by neither, and D-602 proved no whole-net
eviction of any size opens the USB corridor at all.

    whole-board retained open edges   61 -> 59
    unconnected items                 77 -> 75     open retained nets 29 -> 29
    improved  GND (6 -> 4)                         regressed  none
    15 objects added (13 tracks + 2 vias), 2 removed and both licensed
    zero zones, zero rule areas, zero .kicad_dru change, no new licence
    authority 4cd1be8f... -> 77ac2bde... -> cfd10db1...

**WHAT WAS CLOSED IS DEFECTS, NOT COUNTS.**  `U2.2` and `U2.3` are `A1` and
`A2` on the `PCAL9535APW` -- the **I2C ADDRESS STRAPS**.  The schematic ties
both to `GND` to place the expander at 0x20; neither had a ground connection on
the PCB, so the expander behind the D-pad and the A/B buttons would not have
answered at the address the firmware talks to.  `J1.43` is a `GND` contact on
the `FH69-50S-0.5SH` display FPC connector and had no return path.

**THE MEASUREMENT CAME FIRST.**  New read-only `screen_segment_evict.py` asks
the only question that decides whether the unit is worth building -- *is the
pocket full of cuttable copper, or is it full of pads?*  Per open land it cuts
foreign track in the in-memory obstacle model and re-offers the land to the
promoter's own `maze3d.stitch_pad` through the promoter's own `Field`:

    1  UPPER BOUND   cut EVERY unprotected foreign track inside the 8 mm
                     stitch window at once.  Still NO_VIA_SITE => SEGMENT_WALL,
                     a refusal no segment eviction of any size can overturn.
    2  SINGLE        one track at a time; the cheapest possible transaction.
    3  MINIMAL SET   reverse-greedy from "all cut", putting each back and
                     keeping it back whenever the land stays open.

then SHRINKS the cut from the window down a radius ladder to the smallest disc
at the barrel's own site that still opens it, and PRICES every survivor on
KiCad's own `BuildConnectivity` on a scratch copy.  On the promoted D-606 board:

    lands measured                    25 open pour lands
    SEGMENT_OPENS / SEGMENT_SET       11, eight of them under ONE track moved
    smallest cut that opens a land    a disc 0.80 mm across
    SEGMENT_WALL                       5, each with 17-40 foreign BARRELS in
                                       its window -- the one obstacle a split
                                       can never cut
    NOT_A_POCKET                       8 (all five U4 BMI270 lands, U5.2,
                                       U11.1) -- they fail on the ESCAPE, so
                                       segment eviction is not their lever

**A DETOUR, NOT A SPLIT.**  Splitting a track at the pocket boundary leaves two
stubs with FREE ENDS, and D-580's first `--evict` transaction routed, regressed
nothing, re-proposed its evicted net in full and was still REFUSED for three
`track_dangling` warnings.  Removing the crossing track WHOLE and laying it
again BETWEEN ITS OWN TWO END COORDINATES is the same transaction with the trap
taken out: both endpoints keep their exact nanometres, so everything that met
that track still meets it, nothing is stranded, no stub exists to re-join, and
the cut net's cluster count cannot move.  `maze3d.route_points` is the
primitive and the only new thing in the legality argument is that `_emit_path`
gained optional `head`/`tail` exact coordinates -- absent both it is
byte-identical to the one `join_islands` has always called.  The site is held by
an ORDINARY `Field` guard, the object `pour_bond_guard.py` already writes, with
D-602's `exempt` list naming the pour net the pocket is freed FOR.

**THE BOUND IS MEASURED, NOT CHOSEN.**  Walking the whole way round a reserved
circle of radius R adds at most its circumference, so the applier derives
`was + 2*pi*R` and `route_points` refuses anything longer.  The bound exists
because the first unbounded run measured `/NFC_5V_EN` -- 2.500 mm of track --
coming back **21.418 mm** long.  That is a reroute, not a detour.

    run 1  /TOUCH_RST_N              F.Cu    4.800 -> 5.482 mm, 0 vias
           GND U2.2/U2.3 stitched    0.768 mm @ 0.200, one 0.50/0.25 barrel
    run 2  .../LED_BOOST             In2.Cu 18.528 -> 22.497 mm, 0 vias
           GND J1.43 stitched         2.765 mm @ 0.150, one 0.50/0.20 barrel
    run 3  /ACC_DETECT_N CHAIN       B.Cu    5.335 -> 9.042 mm, 2 vias
           +3V3 R129.1 barrel LEGAL and NOT BONDED -- 59 -> 59, REFUSED

Run 2 is promoted at 0.150 mm, board setup's own `min_track_width`, because the
land does not open at 0.200 mm -- measured, at the same barrel -- and an open
ground contact on the display connector is worse than a thin one.

**THE FIRST CHAIN DETOUR, AND WHY IT IS SAFE.**  `/ACC_DETECT_N` reaches the
`+3V3` `R129.1` pocket as two collinear `B.Cu` segments whose junction lies
INSIDE the disc the barrel needs, so detouring either alone would have to
terminate on a point the reservation forbids.  A detour entry may name a
`tracks` CHAIN and be laid between its two free ends -- and what makes that safe
is not that the segments look collinear but that the applier PROVES no via, pad
or third track of that net meets the interior junctions.  A tee stops the run by
name.  The chain routed and the barrel was legal; the refilled ledger still
showed `R129.1` as a component of its own, so clause 4 refused the run.  **A
barrel that is legal is not yet a barrel that CONNECTS** -- D-606's clause-7
lesson, now observed on an UNLICENSED stitch.

**THE GATE IS PARAMETERISED, NOT WEAKENED.**  `--detour-spec` names the
transaction; nothing is searched.  The applier resolves each track EXACTLY and
UNIQUELY and stops rather than guessing; clause 5 licenses the removals by
SIGNATURE in the same shape `--evict` is licensed; a new clause requires EVERY
named detour to have gone back, because the applier has already taken the track
off the board.  `screen_segment_evict.py --plan-out` writes the
`--detour-spec` file straight from the measurement, chains and all.

    python3 hardware/demo/manufacturing/screen_segment_evict.py \
        --guard evidence/d607-pour-bond-guard-next.json \
        --plan-out PLAN.json -o SURVEY.json
    python3 hardware/demo/manufacturing/route_maze_batch.py NET \
        --guard evidence/d607-pour-bond-guard-next.json \
        --detour-spec PLAN.json --stitch-width ... --stitch-via ... \
        --split-islands --promote

**ONE TRAP THIS RUN WALKED INTO, RECORDED SO THE NEXT ONE DOES NOT.**  A scratch
`.kicad_pcb` copied on its own has NO NETCLASSES: `net_contract` reads the class
off `NETINFO_ITEM`, KiCad resolves that through the PROJECT's netclass patterns,
and without the `.kicad_pro` beside it every net reads back `Default`.  A
hand-driven `--propose` on such a copy will route `+3V3` at 0.200 mm with a
0.50/0.25 mm barrel and report it without complaint -- which is how a screening
run here briefly believed a `P3V3` land opened at a contract the DRU forbids.
`gate` copies `.kicad_pcb`, `.kicad_dru` AND `.kicad_pro` together for exactly
this reason; anything driving the proposer by hand owes the same three files.

**PROOF.**  All 14 `verify_promotion.py` checks PASS from the two board files
alone: 2 objects removed and both on claimed evicted nets; 15 added and every
one on a claimed net; tracks 0.150 / 0.200 / 0.300 mm on `F.Cu`/`B.Cu`/`In2.Cu`
only; vias 0.50/0.20 and 0.50/0.25 mm meeting the 0.125 mm annular floor; zone
and rule-area inventory unchanged; real zone-refilled schematic-parity KiCad DRC
199 / 5 / 1 INHERITED with ZERO attributable and ZERO parity errors; unconnected
items 77 -> 75; fill-stable; `hardware/beta-v2/` untouched.  `protected_copper.py`
re-measures 15 protected nets at 393 objects BYTE-IDENTICAL.  P1-P4 and N1-N3
PASS on the regenerated 46-tube guard.

**NEXT: give `stitch_pad` a BODY predicate.**  Run 3 is the whole argument.
`stitch_pad` takes the FIRST legal barrel site by distance and cannot prefer one
that sits over the plane BODY, and it cannot learn that from connectivity
because the proposer does not refill zones -- the same blindness D-605's antipad
predictor had to model GEOMETRICALLY, and the fix is the same shape.

## The escape-relief doctrine, spent for the first time: seven pour lands opened, and the dead-copper clause that had to exist first (2026-09-04)

The three pour-owning nets owned **30 of 68** retained open edges and every
primitive on this board refused them.  D-604 offered `maze3d.stitch_pad` every
rung of width and barrel the netclass and the `.kicad_dru` FLOORS allow --
**0 of 15 on `+3V3`, 0 of 9 on `GND`**.  D-605 offered `maze3d.join_islands`
the same family on the promoted board -- **0 of 32**, because 23 of those
clusters own no filled pour copper at all.  Both refusals were real; neither
named the lever, because both were measuring the wrong thing.

    whole-board retained open edges   68 -> 61
    raw ratsnest                      84 -> 77     open retained nets 29 -> 29
    improved  +3V3 (14 -> 10), GND (9 -> 6)        regressed  none
    23 objects added (16 tracks + 7 vias), ZERO removed, zero zones
    7 rule areas added and audited; 21 new .kicad_dru rules
    authority 3952597e... -> 4cd1be8f...

**THE LEVER WAS NEVER THE WIDTH OR THE RUN.  IT WAS THE BARREL.**  New
read-only `screen_pad_escape_relief.py` offers every orphan land of every
pour-owning net to the promoter's own `stitch_pad`, through the promoter's own
`Field`, at four rungs that move ONE lever each -- so a land that opens says
which licence it needs.  Rung 0 is exactly D-604's contract and reproduces
D-604's verdict before the screen claims anything new:

    rung                                       +3V3     GND      SYS
    0  .kicad_dru floor -- D-604's control      0/14     0/9      1/9
    1  relief WIDTH only     0.20 mm            3/14     0/9      2/9
    2  relief BARREL only    0.35/0.20 mm       5/14     3/9      1/9
    3  both                                     7/14     3/9      3/9
    4  relief barrel at the NETCLASS width      2/14     2/9      1/9

Rung 2 is the whole finding: eight lands escape at the FULL width this board
already allows them -- no narrow copper, no reduced clearance -- and are refused
for one reason each, that no legal barrel fits in the pocket the escape reaches.
Rung 4 then prices the width honestly, so the emitter takes the WIDEST width
that opens each land rather than one figure for all.

**THE DOCTRINE WAS ALREADY STANDING LAW AND HAD NEVER BEEN SPENT.**
`docs/full-beta-v2/pcb/FBV2_P2_ROUTING_PLAN.md` section 17 has carried the E6
escape-relief doctrine since FBV2-P2-000 and records it in its own title as
"NOT yet instantiated": ONE RULE AREA PER PAD, named for that pad,
`enclosedByArea()` never `intersectsArea()`, created only when a MEASURED need
appears -- never a generic relaxation and never a netclass change.  Two of the
seventeen Beta-DM pockets retired by R4 were `E6_U4_5` and `E6_U4_12`.

**NOTHING NEW WAS INVENTED, IN THE RULES OR IN THE CODE.**  0.35 mm on a
0.20 mm hole with a 0.075 mm ring is the plated process the rule file already
licenses by name for D-257, D-266, D-531 and D-595's `POUR_BRIDGE_U11_11`,
against JLCPCB's verified 0.15 mm / approx 0.1275 mm floor -- **no new fab
capability, a new place**.  D-595 had already built the machine, so
`bridge_licence` was factored into `maze3d.area_licence(qb, net, AREA)`, new
`maze3d.relief_stitch` + `route_maze_batch.py --escape-relief` spend it on the
ESCAPE, and gate clause 6 and `verify_promotion.py --bridge` audit it unchanged.

**WHAT WAS CLOSED IS DEFECTS, NOT COUNTS:**

    U17.5   +3V3  0.400 mm  TPS61169 backlight-boost VIN -- the display
                            backlight controller had NO supply-pin connection
                            at all (the LED path +3V3 -> L3 -> BL_SW was already
                            bonded, so pin 5 carries only the part's own current)
    R111.2  GND   0.300 mm  ground end of the 10 k GPIO45_VDDSPI_STRAP pull-down
                            -- an UNDEFINED ESP32-S3 VDD_SPI strap at reset
    C1.1    GND   0.150 mm  return of the 1 uF on Net-(U1-EN), the module's EN
                            reset RC, with one terminal on nothing
    R110.2  GND   0.300 mm  ground end of the 10 k BMI270_INT1_STRAP pull-down
    C5.1    +3V3  0.400 mm  100 nF decoupling that decoupled nothing
    C7.1    +3V3  0.600 mm  100 nF decoupling that decoupled nothing
    R127.1  +3V3  0.600 mm  top of the 10 k BQ25185_STAT1 pull-up

Four of the seven ran at their full netclass width; only `C1.1` at board setup's
own 0.15 mm `min_track_width`, and it is the sole object on the board at that
width, carrying a 10 ms RC's transient return through 12.6 mOhm.

**A BARREL THAT IS LEGAL IS NOT YET A BARREL THAT CONNECTS, AND THE PROPOSER
CANNOT TELL.**  `stitch_pad` proves the geometry of its via; nothing in it
proves the pour UNDER that via is the plane BODY rather than another orphan
piece of the same net.  D-604 had measured this on `BQ25185_SYS` (`SW9.2`
stitched at every rung and closed nothing, three gate runs, 69 -> 69 each) and
run 1 here repeated it on `+3V3`: eight stitches, seven edges, with `R129.1`
laying a via and 0.547 mm of track for ZERO behind a permanent licence.

The obvious fix is wrong, and it was measured wrong.  Run 2 carried the check
in the proposer -- retake `net_islands` after each stitch, revert any land still
open.  It correctly rejected `R129.1` and **also rejected `C7.1`, which run 1
had proved closes**: the proposer reads the pour as filled BEFORE the barrel
existed, and KiCad's refill floods a zone up to a new via of its own net, so a
pre-refill answer is a guess in both directions.  Run 2 was rolled back.

So the question is answered where it is answerable.  **New gate clause 7,
`relief_lands_closed`:** on the refilled candidate's own ledger -- the same
evidence clause 4 uses -- every land a relief stitch served must no longer be a
component of its own, and one that is refuses the whole run.  `R129.1`'s three
rules were deleted and the rule file records why, so nobody re-authors them.
Run 3: seven stitches, seven edges.

**PROOF.**  All 14 `verify_promotion.py` checks PASS from the two board files
alone -- 23 objects added, 0 removed, widths 0.150 / 0.300 / 0.400 / 0.600 mm,
every via 0.35/0.20 and every one of the seven proved DRU-licensed by polygon
subtraction against the area its own rule names, on the net its own rule names.
Real KiCad DRC 199/5/1 inherited, zero attributable, zero parity, unconnected
84 -> 77, fill-stable.  Clause 5 nothing removed; clause 6 rule-area inventory
exactly the seven the emitter asked for, six copper layers each, forbidding
nothing.  `protected_copper.py` 15 nets / 393 objects BYTE-IDENTICAL.
P1-P4 and N1-N3 PASS on the regenerated 46-tube guard.

**BANKED, RE-MEASURED ON THE PROMOTED BOARD** (`d606-relief-next.json`):
`GND` is EXHAUSTED at every rung, 0 of 6 -- five survivors are `NO_VIA_SITE`
(no legal 0.35 mm barrel anywhere within 8 mm of any escape) and `MK1.4` has no
legal escape at 0.150 mm at all.  `+3V3` has two lands left behind a licence,
`U12.4` and `U12.5`, needing a WIDTH relief whose runs measure 2.65 / 3.08 mm --
OVER section 17's 2.0 mm HARD cap on reduced-clearance run length, so the
doctrine refuses them as measured.  `U4` is NOT a licence question: four of the
BMI270's five open lands are `NO_VIA_SITE` even at 0.20 mm with the finest
barrel.

**NEXT: SEGMENT eviction, now the critical path.**  Sixteen of the twenty-five
remaining pour lands are `NO_VIA_SITE` -- not "the barrel is too coarse" but
"there is no site", at the finest geometry this board licenses anywhere -- and
that includes **`U4`, the BMI270 IMU, a MUST-HAVE Demo feature whose five
`+3V3` supply and strap lands are ALL open with no barrel site within 8 mm of
any of them**.  Split a crossing track at a pocket boundary, rip up only the
portion inside, re-join the two stubs around it, hold the lane with
`reserve_corridor.py --from-copper`.  `join_islands` built the re-join whose
terminal is a cell inside existing copper; `relief_stitch` and clause 7 have now
built the half that proves a re-bond actually bonded.  Only the SPLIT is
missing.

## A bridge is a jumper of length zero; the general move PROMOTED, and the In2 pour for BQ25185_SYS priced and REFUSED (2026-09-04)

D-604 left two named levers and this iteration spends one, refuses the other on
a measurement, and closes an edge that **no primitive on this board could
reach** -- because all of them were asking a pad to launch.

    whole-board retained open edges   69 -> 68
    raw ratsnest                      85 -> 84     open retained nets 29 -> 29
    improved  +3V3 (15 -> 14 open edges)           regressed  none
    4 objects added (2 tracks + 2 vias), ZERO removed, zero zones or rule areas
    authority 45eda139... -> 3952597e...

**THE MISSING PRIMITIVE, AND WHY THE THREE THAT EXIST ALL REFUSE.**  A
pour-owning net's open edges are pieces of its own pour that a foreign track has
CUT, and the three pour-owning nets own **31 of the 69 retained open edges**.
`maze3d.stitch_pad` -- and therefore `stitch_net` and `--join-residual` -- asks
the PAD to launch a full-width escape, and D-604 swept every legal rung of width
and barrel and closed **0 of 15 on `+3V3` and 0 of 9 on `GND`**.
`maze3d.bridge_islands` asks for one point inside cluster A's copper on one
layer AND inside cluster B's on ANOTHER; two pieces of the SAME layer's pour
never overlap, so it reports `NO_BRIDGE` on exactly these.

Both are special cases of one move.  A pour island is a two-dimensional
conductor, so a track that STARTS INSIDE IT needs no escape: leave A's copper,
cross the cut, land on B's.  **A bridge is that jumper with length zero.**  New
`maze3d.join_islands` emits it -- `Field` for legality, `wave3d`/`descend3d` for
the corridor, `QBoard.smooth` + `qrouter.simplify` for the geometry, the same
hole-to-hole proof between its own barrels and `verify_laid` to re-prove every
object, and nothing new in the legality argument at all.

**THE ANCHOR CONTRACT IS WHAT MAKES THE TERMINAL PROVABLE.**  A cell that merely
lies inside the filled polygon is not enough: KiCad moves a pour edge by microns
on every refill and the promoted board is refilled.  So a terminal must sit at
least `width/2 + one lattice cell` inside KiCad's own filled polygon, found by
eroding the polygon mask.  A track of that width centred on an anchor lies
WHOLLY inside copper that is already there, so the connection is geometry rather
than a fill artefact, and a cluster with no anchor is reported `NO_ANCHOR`.

**THE FAMILY, SWEPT AT TWO RUNGS EACH** (`screen_island_join.py`, read-only):

    +3V3   netclass 0.60 mm / 0.80-0.40    0 of 15   (severance, below)
    +3V3   DRU floor 0.40 mm / 0.65-0.40   1 of 15   <- PROMOTED
    GND    both rungs                      0 of 9    7 NO_ANCHOR, 2 NO_PATH
    SYS    both rungs                      0 of 9    4 NO_ANCHOR, 5 NO_PATH

`GND`'s nine survivors own no severed pour AT ALL -- seven are bare pads at any
width down to 0.15 mm -- which is D-604's "sealed pockets" from a second angle
and is the strongest evidence yet that the `GND` residual is a fanout wall, not
a routing one.

**THE PROMOTED EDGE.**  `+3V3` `C3.1`/`R2.1`/`R27.1` -> the pour BODY, 2.162 mm,
`In3 -> B -> F`, two 0.65/0.40 mm barrels at (64.3, 98.0) and (63.8, 96.0), the
far terminal a barrel landing inside the body's own `F.Cu` copper -- the bridge
degenerate case at one end of a jumper at the other.  D-604 had listed this exact
cluster as `NO_VIA_SITE`: "no legal 0.80 mm barrel within 8.0 mm of ANY escape".
There is no licence, no rule change and no width relaxation in it; the 0.40 mm
run and the 0.65/0.40 barrel are the `.kicad_dru`'s own `P3V3` outer-layer floor
and POWER-class drill.

**THE BARRELS ARE SCISSORS, AND THE FIRST GATE RUN PROVED IT ON THE BOARD.**  At
the netclass contract the same join closes with two **0.80 mm** barrels at
(64.0, 98.7) and (61.7, 99.1) -- 2.34 mm apart, across the waist of
`/01_POWER_TREE/BQ25185_SYS`'s 98.38 mm2 `B.Cu` island -- and the refill split
that island into 87.39 + 5.74 mm2, `SW9.2` from `U12.1`.  One net improved, one
regressed, 69 -> 69, REFUSED by clause 4.  A through barrel is a hole and an
antipad on EVERY layer, so dropping one in a foreign pour is a slot through that
pour, exactly as a foreign track on a plane layer is.

**AND THE OBVIOUS PRE-FILTER FOR IT DOES NOT WORK.**  The first version retook
every foreign pour net's cluster count from KiCad's own connectivity after
laying the jumper and caught NOTHING: the proposer does not refill zones, so the
foreign pour it reads is still the one filled before the barrel existed.  The
damage is a FILL consequence.  The predictor is therefore GEOMETRIC -- subtract
each barrel's antipad from KiCad's filled polygon and ask whether that net's own
lands are still in ONE piece -- and the two gate runs CALIBRATE its radius:

    antipad radius            run 1 (0.80 mm, REFUSED)   run 2 (0.65 mm, PASSED)
    dia/2 + clr               intact                     intact
    dia/2 + clr + minthk/2    intact                     intact
    dia/2 + clr + minthk      SEVERED                    intact

KiCad's fill holds the pour `clearance` off the barrel and then removes whatever
neck is left thinner than `min_thickness`, so along a neck a barrel deletes
copper out to `clearance + min_thickness`.  That is the only row that reproduces
both verdicts and, being the widest, is also the conservative choice.  A jumper
that trips it is REVERTED, the island is closed to that transaction's barrels
and the search is retried -- so the screen now refuses in 70 seconds what the
whole-board gate refused in six minutes, and screen and gate agree exactly.

**THE In2 POUR IS PRICED AND REFUSED, so it need not be measured again.**  D-604
required the cost before the spend.  A bounded `In2.Cu` pour over the east power
block FILLS legally -- 2 islands, ZERO attributable DRC -- and buys exactly ONE
bridgeable orphan (`SW9.2`/`U12.1`, 92 sites at the fully licensed 0.65/0.40
barrel); the pour alone leaves the board at 69 -> 69.  The price is the WHOLE In2
layer, because `reserved_inner_planes` reserves a LAYER to a net the moment any
filled pour of that net appears on it and In2 is in every net's palette.  One
edge for a third of the remaining routing capacity is not a trade this board can
make.

**AND THE SYS POCKETS ARE MEASURED, NOT INFERRED.**  Its body island is
3.31 mm2 and its orphans lie 0.70, 1.71, 3.84, 9.78, 26.26 and 63.25 mm from it
ON `B.Cu` -- gaps a jumper would cross if a corridor existed.  At the 0.500 mm
`SYS_MAIN` minimum the DRU itself states, a wavefront started inside each island
reaches 54 to 574 cells and **never leaves `B.Cu`**, because only ONE of the
seven islands holds a single legal barrel site.  Six sealed pockets and one open
island.  Narrowing `SYS_MAIN` below 0.50 mm is NOT the answer and was not
attempted: that figure is a 1.0 A current rule with a named 2.19 A local
exception at `U21`, not a routing default.

**RE-PROVED INDEPENDENTLY, all 14 checks PASS** (`verify_promotion.py`): ZERO
objects removed; 4 added (2 tracks + 2 vias) and every one on `+3V3`; tracks at
0.400 mm on `In3`/`B`; barrels 0.65/0.40 mm, above the POWER drill and 0.125 mm
annular floors; zone and rule-area inventories unchanged; KiCad's OWN
unconnected-item count **85 -> 84**; real zone-refilled schematic-parity DRC at
`--severity-all` exactly 199 / 5 / 1 inherited with ZERO attributable and ZERO
parity reports; fill-stable; D-269 / D-186 rule text live; `hardware/beta-v2/`
untouched.  `protected_copper.py`: 15 nets / 393 objects BYTE-IDENTICAL.
`pour_bond_contract.py` P1-P4 and `neck_contract.py` N1-N3 PASS on the
regenerated 46-tube guard.

Usage:

    python3 screen_island_join.py [NET ...] --guard GUARD.json --floors -o OUT.json
    python3 route_maze_batch.py NET --join-islands \
        --stitch-width 400000 --stitch-via 650000:400000 \
        --guard GUARD.json --repair-planes --work DIR --out DIR/run.json [--promote]

Next: **SEGMENT eviction**, now named by FOUR independent walls -- the USB
connector corridor (D-602), the `U9` west channel (D-603), and now both the
`GND` and `BQ25185_SYS` pour residuals, every one of which is a foreign track
lying across copper that would otherwise be one piece.  The unit that removes it
is a split-and-rejoin of that ONE track, not a rip-up of its net; every
ingredient exists (`WithoutObjects`, clause 5's per-signature removal licence,
the bounded 8 mm repair pass, `reserve_corridor.py --from-copper` to hold the
lane afterwards) and what is missing is the split and a re-join allowed to land
on a STUB.  **`join_islands` has just built half of that second half**: a
terminal that is a cell inside existing copper rather than a pad escape is
exactly what a re-join onto a stub needs.

## The ESD ground return: three TPD4E1B06 arrays had an OPEN ground pin, and the netclass width was the only thing stopping them (2026-09-04)

`GND` and `+3V3` between them owned **27 of the board's 72 retained open
edges** -- islands their own pour never reached, the largest remaining family by
a factor of three, and every one of them one `maze3d.stitch_pad` away from
closing: an escape, a short run, one through barrel down to the net's own plane.
So the question was never which net to route next.  It was what CONTRACT the
stitch was being denied at.

    whole-board retained open edges   72 -> 69
    raw ratsnest                      88 -> 85     open retained nets 29 -> 29
    improved  GND (12 -> 9 open edges)             regressed  none
    11 objects added (8 tracks + 3 vias), ZERO removed, zero zones or rule areas
    authority 0b991dc9... -> 45eda139...

**WHAT THE THREE EDGES ARE.**  `D2`, `D4` and `D5` are TPD4E1B06DRLR ESD
protection arrays in SOT-563, and they protect the **Community Port** --
`XGPIO4_HDR`, `XGPIO5_HDR`, `NATIVE_A_HDR`, `NATIVE_B_HDR`, `EXT_SDA`,
`EXT_SCL`, `WAKE_ATTN_N_HDR`, `ACC_DETECT_N_HDR`.  All three had an
**UNCONNECTED GND pin**.  A TVS array whose ground is open clamps nothing; it is
a line on a BOM and no protection at all, on the one connector a Kickstarter
demo hands to a stranger.  That is a functional defect on a user-facing
MUST-HAVE, not a ledger entry.

**THE NETCLASS WIDTH IS A DEFAULT.  THE `.kicad_dru` FLOOR IS THE RULE.**  The
DRU imposes **no `track_width` rule on `GND` at all**, so the board's own floor
for a `GND` track is board setup's 0.15 mm `min_track_width` -- and a SOT-563
land is 0.350 mm wide on 0.5 mm pitch, so a 0.30 mm launch off it does not
physically exist.  All three pads reported `NO_LEGAL_ESCAPE` for that reason and
no other.  The ladder was measured on the promoter's own `stitch_pad`, every
trial reverted:

    w = 0.30 / 0.28 / 0.25 mm ->  0 of 12 islands, at either barrel
    w = 0.23 mm, 0.60/0.30    ->  2      w = 0.20 mm, 0.60/0.30 -> 2
    w = 0.23 mm, 0.50/0.25    ->  3      w = 0.20 mm, 0.50/0.25 -> 3

Both levers are needed for the third pad.  **0.20 mm is chosen over the wider
0.23 mm on INDUCTANCE, not on count**: it lays 0.79 / 0.97 / 2.55 mm against
1.19 / 1.75 / 2.80 mm, and for an ESD return LENGTH is the figure of merit --
TI's own TPD4E1B06 layout guidance is "minimize the length of the ground trace,
use a via directly to the ground plane".  0.20 mm of 1 oz copper carries an 8 kV
IEC 61000-4-2 contact discharge with two orders of magnitude of fusing margin.
Laid **0.200 mm on `F.Cu` into 0.50/0.25 mm barrels onto the `In1`/`In4` `GND`
planes** -- the DRU's own pad-escape necking figure (a rule that already names
the SOT-563 parts `U13` and `U21`) and `min_via_diameter` with exactly the
0.125 mm annular ring, D-601's proven FREE rung.  No licence; `--stitch-width` /
`--stitch-via` already existed and already clamp UP to every DRU floor.

**ONE LATENT DEFECT IN THAT CLAMP, FOUND AND FIXED.**  `--stitch-width` clamped
to `DRU_CLASS[class]["width"]` and nothing else, and for `GND` that floor is
ZERO because the DRU states no width rule for the class -- so the flag would
have accepted a request under board setup's own `min_track_width`.
`--bond-via` already refuses a sub-floor barrel by name; a sub-floor TRACK is
now clamped for the same reason and in the same shape (`BOARD_TRACK_MIN`,
transcribed from `aqroot-Beta-v2.kicad_pro` beside `BOARD_VIA_DIA_MIN` and
`BOARD_HOLE_MIN`).  The promoted run asked for 0.200 mm and is unaffected.

**THE FAMILY IS NOW SWEPT AND BANKED.**  New read-only
`screen_plane_orphans.py` offers every orphan island of every pour-owning net to
`stitch_pad` at each rung from the netclass contract down to the floors the DRU
and board setup state, clamping exactly as `route_maze_batch.propose` clamps so
it can never propose copper the board would refuse.  On the promoted board:

  * `GND` -- **0 of the 9 remaining at EVERY rung down to 0.15 mm /
    0.50-0.20 mm.**  Instrumented directly, those escapes reach free regions of
    19 to 344 lattice cells and **not one via-legal cell among them**: sealed
    pockets, measured rather than inferred.  `--join-residual` at a 15 mm bound
    adds nothing -- all 9 are `NO_PATH` or `NO_LEGAL_ESCAPE_SRC` even at
    0.20 mm.
  * `+3V3` -- **0 of 15 at every LEGAL rung.**  Its floors are not `GND`'s: the
    DRU states 0.40 mm on the outer layers for `P3V3` and "POWER-class vias use
    the 0.40 mm drill", so 0.65/0.40 mm is the finest legal barrel.  A
    0.50/0.25 mm barrel WOULD open `C3.1`, `R127.1`, `U12.4`, `U12.5` and
    `U17.5` and is ILLEGAL on this class -- recorded as the size of the prize
    behind a licence, not as a route.

**AND THE SWEEP NAMED THE NEXT WALL BY ITS ROOT.**
`/01_POWER_TREE/BQ25185_SYS` carries 9 open edges and its `SW9.2` island
stitches at EVERY rung -- and closes nothing, in three separate full gate runs,
69 -> 69 each time.  **`stitch_pad` proves a barrel is LEGAL where it lands, not
that the pour under it is the BODY.**  This net owns two `B.Cu` zones and
nothing else, 1 filled island in one and 7 in the other, so `stitch_net`'s
contract -- "drop the island onto its net's plane" -- has no single plane to
name.  `GND` has `In1` and `In4`; `+3V3` has `In3` (D-580); **`BQ25185_SYS` is
the one pour-owning net on this board with no inner plane at all**, and
`--bridge` cannot help because it joins clusters across LAYERS and this pour has
one.  Width is not the wall either: every residual join is `NO_PATH` at the
0.800 mm netclass width AND at the 0.500 mm figure the DRU itself states as the
`SYS_MAIN` minimum, barrel at the POWER floor -- a 1.6x reduction the board has
already ratified, and it changes zero verdicts.

**RE-PROVED INDEPENDENTLY, all 14 checks PASS** (`verify_promotion.py`): ZERO
objects removed; 11 added (8 tracks + 3 vias) and every one on `GND`; every
track 0.200 mm on `F.Cu`; every barrel 0.50/0.25 mm, above the drill and
0.125 mm annular floors; zone and rule-area inventories unchanged; KiCad's OWN
unconnected-item count **88 -> 85**; real zone-refilled schematic-parity DRC at
`--severity-all` exactly 199 / 5 / 1 inherited with ZERO attributable and ZERO
parity reports; fill-stable; D-269 / D-186 rule text live; `hardware/beta-v2/`
untouched.  `protected_copper.py`: 15 nets / 393 objects BYTE-IDENTICAL.
`pour_bond_contract.py` P1-P4 and `neck_contract.py` N1-N3 PASS on the
regenerated 46-tube guard; `screen_bond_stitch.py` re-derives the same 29-tube
working guard and confirms D-603's free rung still exhausted (0 of 36 bondable).

Usage:

    python3 screen_plane_orphans.py [NET ...] --guard GUARD.json -o OUT.json
    python3 route_maze_batch.py GND --split-islands \
        --stitch-width 200000 --stitch-via 500000:250000 \
        --guard GUARD.json --repair-planes --work DIR --out DIR/run.json [--promote]

Next: **give `BQ25185_SYS` a body.**  Its 9 edges are one problem, not nine, and
the problem is a single-layer pour broken into eight islands.  The bounded form
is a `--plane-outline` `In2.Cu` pour over the island cluster -- `In2` is the only
routable inner layer carrying no pour -- but the cost must be measured before it
is spent: **In2 carries 268 tracks / 2268 mm across 60 nets**, and
`reserved_inner_planes` reserves a LAYER as soon as any pour appears on it, so a
naive whole-layer pour would take a third of the board's routing capacity.  The
cheaper, strictly local alternative is a proposer that names WHICH pour island a
stitch barrel must land in.  SEGMENT eviction (D-602/D-603) stays named and
unbuilt behind both.

Status: **BLOCKED** at board completion; no manufacturing candidate is approved.

## A clearance the board owes a PAD is not the one it owes a TRACK; the display backlight anode PROMOTED, and the free bond rung spent (2026-09-04)

D-601 left a READY PAYLOAD -- seven pads that bond at the board's own
`min_via_diameter` and need no licence -- and a rule that would not bend for
them: bond redundancy closes no edge by construction, and clause 4 requires the
board to IMPROVE, so a robustness batch must ride with a route.  Four partners
were offered and all four declined.  This iteration found the fifth by fixing a
framework defect rather than by searching harder.

    whole-board retained open edges   73 -> 72
    raw ratsnest                      89 -> 88     open retained nets 30 -> 29
    improved  /03_SPI_A_DISPLAY_SD/LED_A          regressed  none
    7 more pads bonded (all GND)      39 of 75 bonded; free rung EXHAUSTED
    26 objects added (17 tracks + 9 vias), ZERO removed, zero zones touched
    authority bfef0aa2... -> 0b991dc9...

**THE DEFECT, AND THE `.kicad_dru` STATES THE INTENT IN ITS OWN WORDS.**  Every
elevated figure in `route_maze_batch.DRU_CLASS["clr"]` -- `LED_BOOST` and
`SWITCH_NODE` at 0.30 mm, `SYS_MAIN` / `ACC_3V3` / `ACC_5V` / `VBUS_CHG` /
`NFC_5V_PA` at 0.25 mm, `BAT_MAIN` at 0.30 mm -- comes from a section-8 "routed
clearance" rule, and **every one of those rules carries
`A.Type != 'Pad' && B.Type != 'Pad'`**.  The section's own header says why:

    Elevated clearances below are ROUTING clearances: they are scoped so
    that vendor land patterns (J1 FH69 0.5 mm pitch, J3 USB-C, U11 WSON
    0.4 mm pitch, U12 VSON, U14 WLP) are judged against the 0.20 mm
    global figure they actually satisfy, not against a routing target.

`net_contract` collapsed both into ONE scalar and every caller handed it to
`maze3d.Field` as BOTH `clr_pad` and `clr_trk`.  So the proposer owed a PAD a
routing target the board judges at 0.20 mm.  That is not conservatism, it is a
DIFFERENT RULE -- and a fine-pitch land pattern is exactly where the extra
tenths decide whether a pin can launch at all.  `maze3d` already models the
distinction correctly (`dru_overlay` and `obs_clearance` raise a track's or a
via's clearance and skip that raise for a pad), so the elevated figure is STILL
applied to routed copper and the only thing the split removes is the raise
against pads.  `BAT_MAIN` is deliberately NOT split: its 0.30 mm figure is
D-269, nothing currently open is `BAT_MAIN`, and a safety ruling should not
depend on reading its rule text the same way twice.  `PAD_CLR_RETAINED` names
that conservatism instead of hiding it.

**PRICED BEFORE IT WAS SPENT, AND IT CHANGES EXACTLY ONE VERDICT.**  New
read-only `screen_pad_clearance.py` builds two `maze3d.Field`s per open retained
net that differ in `clr_pad` ALONE and offers every island-MST edge to the real
`maze3d.route_join` with `emit=False`.  Across all 28 open retained nets on
`bfef0aa2...` one verdict moves: `/03_SPI_A_DISPLAY_SD/LED_A` `J1.1 -> R71.2`
reads `NO_LEGAL_ESCAPE_SRC` at 0.30 mm and ROUTES at 0.20 mm -- the display
backlight anode leaving the J1 FH69 flex land pattern that the DRU header names
by part number.  The necking rule changes nothing anywhere, because necking is a
WIDTH lever and every net measured is already at its class width.  The route the
gate then laid is 10.042 mm, `F -> B -> F`, 2 vias, and **KiCad's own DRC found
zero attributable violations**, which is the empirical half of the argument: the
board really does judge that pad at 0.20 mm.

**THE SEVEN BONDS RODE WITH IT, AND THE LADDER IS NOW SPENT.**  `C25.2`,
`C36.2`, `C5.2`, `R17.2`, `R37.2`, `R97.2`, `R98.2` -- 7 of 7 bonded at
0.50/0.25 mm, 9.952 mm of stub in total, median 1.283 mm -- with the 29-tube
guard `screen_bond_stitch.py --emit-guard` wrote for exactly this payload.  With
both promoted transactions credited, `screen_bond_stitch.py --bonded-from` now
reports **39 of 75 pads bonded and ZERO remaining bondable** at the free rung:
the 36 that are left are `NO_LEGAL_ESCAPE` and `NO_VIA_SITE`, and D-601's ladder
already measured what buys them -- a 0.45/0.20 mm barrel needing a rule-area
licence, worth 4 pads and 3 tubes.  17 of 46 tubes retire; the working guard for
the next run is `evidence/d603-pour-bond-guard-bonded.json`.

**THREE NFC LAYER CONTRACTS WERE MISSING AND A REAL GATE RUN FOUND THEM.**
`.kicad_dru` section 7 states them in words -- "NFC crystal nets stay on B.Cu",
"NFC crystal nets are forbidden on In2", "NFC crystal nets carry no via", and
the same three for the transmit arms -- and `DRU_CLASS` carried `layers=None`
for `NFC_OSC`, `NFC_RF` and `NFC_RX`.  The first `U9` west-channel batch
measured the consequence rather than arguing it: with both supplies closed the
evicted `NFC_XOUT` came back with 0.7211 mm and 1.3416 mm of track on `In2.Cu`
and TWO `F`-to-`B` barrels, and the gate refused the run on four real
`items_not_allowed` reports naming those rules.  The fix is the recipe D-596
already wrote down for `USB_D`: **a SINGLE-layer contract makes the via
inexpressible rather than merely forbidden**, because the maze's via move has no
second layer to land on.  `NFC_RX` is deliberately NOT single-layer -- its rule
disallows a TRACK on `F.Cu` and says nothing about vias or `In2`, so it keeps
`B` and `In2` and the barrel it is allowed to have.  `NFC_RF` also gained the
0.25 mm routed clearance section 8 gives it and its netclass does not.

**THE U9 WEST CHANNEL IS A 1-FOR-1 TRADE, MEASURED IN BOTH ORDERINGS.**  `U9` is
a UFQFPN-32 at 0.5 mm pitch whose exposed pad leaves a **0.175 mm** inner
channel, so no west pin escapes inward and every one must launch straight west
into the same lane.  Supplies first: `NFC_VDD_A` and `NFC_VDD_D` both close and
`NFC_XIN`/`NFC_XOUT` each come back one join short -- **73 -> 73**.  Crystal
first: it rebuilds completely and BETTER than it was (`XIN` 7.237 mm, `XOUT`
4.947 mm, zero vias) and both supplies return to `NO_LEGAL_ESCAPE_DST` --
**73 -> 73**.  A read-only corridor screen on the supplies-first candidate
closes the loop: `NFC_XIN`'s missing join is opened by ripping up `NFC_VDD_A`
ALONE and `NFC_XOUT`'s by `NFC_VDD_D` alone, and the openers are **1.149 mm and
0.583 mm** of route.  The conflict is mutual and TINY, which is why no ordering
and no containment-bounded eviction changes the total.  **That names D-602's
SEGMENT eviction as the unit this wall wants**: an `--evict-whole` cannot
express "give up 1.1 mm of this track and rejoin around it".

**RE-PROVED INDEPENDENTLY, all 14 checks PASS** (`verify_promotion.py`): ZERO
objects removed; 26 added and every one on a claimed net; every track at
0.300 mm; barrels 0.50/0.25 and 0.60/0.30 mm, both above the drill and 0.125 mm
annular floors; zone and rule-area inventories unchanged; KiCad's OWN
unconnected-item count **89 -> 88**; real zone-refilled schematic-parity DRC at
`--severity-all` exactly 199 / 5 / 1 inherited with ZERO attributable and ZERO
parity reports; fill-stable; D-269 / D-186 rule text live; `hardware/beta-v2/`
untouched.  `protected_copper.py`: 15 nets / 393 objects BYTE-IDENTICAL.
`pour_bond_contract.py` P1-P4 and `neck_contract.py` N1-N3 PASS on the
regenerated 46-tube guard.

**THE LEVER IS NOW MEASURED AND SPENT, AND THE RE-RUN FOUND THE NEXT
CANDIDATE AND REFUSED IT.**  Re-run on the promoted board, `0 of 29` open
retained nets change verdict: the pad-clearance split has paid everything it
will pay, which is exactly the number a lever should be retired on.  The re-run
did surface one net whose single open edge routes ALONE --
`/08_BUTTONS_EXPANDERS/BTN_DOWN_N`, offered unguarded -- and three gate runs
priced it.  With the 29-tube guard it is `NO_PATH`: **its only corridor runs
through a still-load-bearing pour-bond neck.**  Guard OFF it routes at
**47.361 mm and 5 vias for an 8.099 mm gap**, closes its edge, and severs a
`GND` bond the repair cannot restore -- **72 -> 72, REFUSED**, D-599's exact
shape.  The 13 pads the repair is offered are the same `NO_VIA_SITE` /
`NO_LEGAL_ESCAPE` set `pour_bond_guard.py` already names, a 0.50/0.25 mm stitch
barrel changes none of them, and the cross-check that closes the loop is that
**none of the 13 is among the four pads D-601's licensed 0.45/0.20 mm rung would
buy**.  So the licence does not open this wall either: it is corridor capacity,
not barrel diameter -- the same diagnosis D-601 reached for the three walls it
offered as partners.  Evidence `d603-clrpad-survey-next.json`,
`d603-btn-down-refusal.json`; the authoritative board is byte-identical across
all three runs.

Usage:

    # which open edges does the PAD clearance decide, on the board as it stands?
    python3 screen_pad_clearance.py --neck -o evidence/SCREEN.json

    # what a promoted iteration of this shape looks like
    python3 route_maze_batch.py NET --partial --repair-planes \
        --guard evidence/d603-pour-bond-guard-bonded.json \
        --bond-via 500000:250000 --bond-pad REF.NUM ... \
        --promote --work DIR --out evidence/RUN.json

## Bond redundancy: 32 guarded pads get a barrel of their own, and the guard shrinks (2026-09-04)

D-599 put three independent nets through the full gate with the pour-bond guard
OFF and all three returned the same shape: the net closes one edge, `GND` opens
one, `--repair-planes` names `GND` as its candidate and cannot re-bond it, board
unchanged, REFUSED.  The reading was that the guard was not costing those edges,
it was correctly PREDICTING a refusal, and that the refusal had a root that was
fixable.  This iteration fixes it.

    whole-board retained open edges   74 -> 73
    raw ratsnest                      90 -> 89
    improved  /I2C_SCL_INT  6 -> 5               regressed  none
    32 pads bonded (28 GND, 4 +3V3)   pour-bond guard 48 -> 34 tubes
    134 objects added (97 tracks + 37 vias), ZERO removed, zero zones touched
    authority b8bb6d98... -> bfef0aa2...

**THE UNIT IS THE PAD, AND D-599's OWN SCREEN HAD THE WRONG ONE.**
`screen_bond_redundancy.py` asked how many legal barrel sites lie inside a
guarded ISLAND and answered in the thousands -- 191532 for `GND` `B` island 13
alone.  Writing the emitter exposed that the number answers the wrong question.
A foreign track does not remove an island, it SPLITS one: a barrel dropped
somewhere inside lands on one side of the cut and every pad on the other side is
orphaned exactly as before.  Redundancy that survives the cut has to hang off
the PAD.  That is also why `bridge_islands` could not be extended to do this --
it answers an island question -- and why the new primitive is `stitch_pad`, the
one every promoted stitch on this board already went through, aimed at a pad
that is ALREADY connected.  The only thing `maze3d.bond_pads` adds is the right
to ask.  No new geometry, no new legality argument, no new proof.

**THE HONEST NUMBER IS 32 OF 75, AND IT IS THE USEFUL ONE.**
`screen_bond_stitch.py` offered every pad end of every live tube to the emitter
on a scratch board.  32 bond; 43 do not, and they fall into the two classes
`pour_bond_guard.py` already names.  `NO_LEGAL_ESCAPE`: `U9.6`/`U9.12`/`U9.26`
inside the ST25R3916's 0.5 mm-pitch land pattern, `J1.7`/`J1.9`/`J1.35`/`J1.40`/
`J1.42` in the display FPC row, `U5.7`, `U14.4`, `U11.4`.  `NO_VIA_SITE`: the
famous fatal four `U3.12`, `R19.1`, `R26.1` and their neighbours, plus the whole
of `GND` island 28 and the `U2`/`U3` expander pocket -- no legal 0.60 mm barrel
within 8 mm of any escape.  One pad, `U14.1`, reached `UNPROVED_GEOMETRY`
against `/01_POWER_TREE/BAT_PROTECTED_P` and was reverted on its own, which is
the per-pad transaction working as designed.

**A TUBE RETIRES ONLY WHEN BOTH ENDS BOND, AND THE SPANNING TREE IS WHY THAT IS
SAFE.**  Dropping a tube whose far end still depends on the pour would strand
that end.  Because the guard's tubes are a spanning tree over an island's pads,
the both-ends rule leaves every still-dependent pad joined by GUARDED tubes to a
component whose boundary pad is bonded -- so no pad loses its last protected
path.  14 of 48 tubes retire under it: `+3V3` island 1, and `GND` islands 7, 17,
23, 30 (both), 32, 34, 38 (both), 42 (both), 46, 49.

**THE CONTROL RUN IS THE PROOF, AND IT IS THE INTERESTING NUMBER.**
`evidence/d600-guard-off-control.json` is the IDENTICAL transaction -- same 32
bonds, same three nets, `--partial --repair-planes` -- with the guard entirely
OFF.  It returns D-599's exact shape: `/I2C_SCL_INT` +1, `GND` -1, repair cannot
re-bond, **74 -> 74, REFUSED**.  With the REDUCED guard on, the router is pushed
off the 34 tubes that are still load-bearing, finds a different path, and costs
`GND` nothing: **74 -> 73, PROMOTED**.  So neither the bonds alone nor dropping
the guard is what closes the edge.  **A pre-filter with its retired tubes
removed is strictly better than no pre-filter** -- and that is a stronger
statement about the guard than D-599 was able to make.

**WHAT THE BOARD GAINS BESIDES ONE EDGE.**  Twenty-eight `GND` pads and four
`+3V3` pads -- decoupling-capacitor returns, `U4`, `U12`, `U14`, `U18`, `U20`,
`U21`, `U9.21`, `J5.23` -- now reach their plane through a track and a through
barrel instead of through a neck of pour, which is a shorter return path, a
thermal via each, and ordinary good practice whatever the router wanted.  Median
`GND` bond is 1.18 mm of stub (`+3V3` 2.24 mm); the longest, `C38.2` at
10.70 mm, is ADDITIONAL to a pour bond that still exists, so it cannot make
anything worse.  All 32 requested bonds succeeded in the promoting run.

**WHAT IT COSTS, MEASURED.**  `/I2C_SDA_INT` `U3.23 -> U4.14` routed guard-off
at 43.13 mm on the UNBONDED board (D-599) and is `NO_PATH` guard-off on the
bonded one: the bond copper took the lane.  That is not a loss -- D-599's gate
refused that route anyway, for the `GND` regression -- but bond copper IS copper
and the next iteration should expect it.  `/08_BUTTONS_EXPANDERS/BTN_DOWN_N` is
`NO_PATH` either way.

**RE-PROVED INDEPENDENTLY, all 14 checks PASS** (`verify_promotion.py`): ZERO
objects removed; 134 added (97 tracks + 37 vias) and every one on a claimed net;
every track at or above 0.200 mm on `F`/`B`/`In2` (0.200 signal, 0.300 `GND`,
0.600 `+3V3`); every barrel 0.60/0.30 or 0.80/0.40 mm, both above the drill and
0.125 mm annular floors; zone and rule-area inventories unchanged with nothing
added to either; KiCad's OWN unconnected-item count **90 -> 89**; real
zone-refilled schematic-parity DRC at `--severity-all` exactly 199 / 5 / 1
inherited with ZERO attributable and ZERO parity reports; fill-stable;
D-269 / D-186 rule text live; `hardware/beta-v2/` untouched.
`protected_copper.py`: 15 nets / 393 objects BYTE-IDENTICAL.
`pour_bond_contract.py` P1-P4 and `neck_contract.py` N1-N3 PASS on the
regenerated 46-tube guard.

**THE BARREL LADDER, MEASURED IMMEDIATELY AFTER (D-601), AND THE FREE RUNG IS
WHERE THE VALUE IS.**  `NO_VIA_SITE` is a function of DIAMETER, so the 43
unbonded pads were re-offered at each rung:

    0.60/0.30 mm  netclass GND via            32 of 75 bonded   12 of 46 tubes
    0.50/0.25 mm  BOARD min_via_diameter      +7  = 39          17 of 46 tubes
    0.45/0.20 mm  needs a rule-area licence   +4  = 43          20 of 46 tubes
    0.35/0.20 mm  the finest licensed process EXACTLY THE SAME ELEVEN

0.50/0.25 mm needs NO licence, meets the 0.125 mm annular floor exactly, and
retires `GND` islands 33 and 35 whole.  A licence buys three more tubes; nothing
below 0.45 mm buys anything.  **The seven free bonds are not promotable on their
own** -- bond redundancy CLOSES NO EDGE by construction and clause 4 requires
the board to improve, so they must ride with a route that closes one, as these
32 rode with `/I2C_SCL_INT`.  Four partners were offered and all four declined
(`/I2C_SDA_INT`, `BTN_DOWN_N`, `/09_COMMUNITY_HEADER/EXT_SDA` `NO_PATH` at the
29-tube guard; `/I2C_SCL_INT` no second edge), which is itself the finding:
**those walls are corridor capacity, not the pour-bond guard.**  Clause 4 was
NOT weakened to admit the batch.  The seven pads, `--bond-via 500000:250000` and
`evidence/d601-pour-bond-guard-bonded.json` are a READY PAYLOAD for the first
future run that closes an edge anywhere on the board.

Usage:

    python3 screen_bond_stitch.py --guard evidence/d600-pour-bond-guard-next.json \
        --bonded-from evidence/d600-bond-batch.json \
        --emit-guard evidence/GUARD-bonded.json -o evidence/SCREEN.json

    python3 route_maze_batch.py NET... --partial --repair-planes \
        --guard evidence/GUARD-bonded.json \
        --bond-via 500000:250000 \
        --bond-pad REF.NUM [--bond-pad REF.NUM ...] \
        --promote --work DIR --out evidence/RUN.json

    # price a sub-floor barrel, which --bond-via refuses by name:
    python3 screen_bond_stitch.py --guard ... --via 450000:200000 -o OUT.json

## Rip-up-and-reroute: the NFC/SPI-B fanout, 2 edges promoted and an analog reference repaired (2026-09-04)

`/NFC_CS_N` read `CROSSING_COPPER_WALL` on the last board -- a refusal, not a
plan.  It reads `RIPUP_WHOLE_SINGLE` on this one, because the screen learned a
question it did not have.

    whole-board retained open edges   76 -> 74
    raw ratsnest                      92 -> 90     open retained nets 32 -> 30
    improved  /NFC_CS_N  /SPI_B_MOSI              regressed  none
    evicted whole  /04_SPI_B_RADIOS_NFC/NFC_AGDC
    authority 83b6a140... -> b8bb6d98...

**THE CAPABILITY -- QUESTION 2W, and it is the question `--evict-whole`
DESERVED ALL ALONG.**  `screen_corridor_blockers.py` asked four questions and
none of them matched the strongest instrument the router has.  Question 2 tries
one foreign net at a time but may only remove copper WHOLLY INSIDE the corridor
window, because that is what a containment-bounded `--evict` executes -- so a
track that merely CROSSES the window is left in place and, when it is the wall,
the screen reports `CROSSING_COPPER_WALL` and stops.  D-596 built
`--evict-whole` for exactly that case: a named net's entire routed copper, every
object, every layer, board-wide, on condition that the net is also REQUESTED and
re-proposed inside the same transaction.  That is an executable unit and the
screen owed it a candidate.  New question **2W** strips one CROSSING net whole
and asks the corridor again, over `crossing_nets` -- every foreign net whose
copper INTERSECTS the window, a superset of question 2's set, because the whole
point is the track question 2 had to leave behind.  Each opener is reported with
the object count a real `--evict-whole` would move and with whether
`protected_copper.py` forbids touching it; a candidate skipped by `--whole-cap`
is REPORTED, not dropped, because "no opener found" and "no opener looked for"
are different answers.  It paid on its first run: `/NFC_CS_N`
`CROSSING_COPPER_WALL` -> `RIPUP_WHOLE_SINGLE /04_SPI_B_RADIOS_NFC/NFC_AGDC`.

**THE EVICTED NET IS THE ONE THAT GAINS MOST, and that was not the plan.**
`NFC_AGDC` is the ST25R3916's analog reference node, and the schematic says of
its decoupling, in the part's own words from ST DS12484: *"Must be placed very
close to the pin during PCB layout."*  It was carrying **17 `B.Cu` tracks and
40.627 mm** of copper to reach two capacitors 6.1 mm and 9.5 mm from the pin.
Rebuilt from bare pads it takes **15 tracks and 22.656 mm** -- `C54.1 -> U9.24`
in 7.58 mm and `C53.1 -> U9.24` in 15.08 mm.  The rip-up repairs a documented
layout requirement that the board was quietly violating; the two closed edges
are the second benefit, not the first.

**THE U9 FANOUT FITS EXACTLY TWO OF THREE, MEASURED IN THREE ORDERINGS.**
`U9.29` (`NFC_CS_N`), `U9.30` (`SPI_B_SCK`) and `U9.31` (`SPI_B_MOSI`) are
adjacent lands on a 0.5 mm-pitch UFQFPN-32, and whichever is routed LAST returns
`NO_LEGAL_ESCAPE_DST` every time:

    CS, SCK, MOSI, AGDC              closes CS + MOSI   74   SCK fails
    SCK, CS, MOSI, AGDC              closes CS + SCK    74   MOSI fails
    SCK, CS, MOSI, AGDC  --neck      closes CS + SCK    74   MOSI fails, necks NONE

`--neck` was VACUOUS for the third promotion running even though `U9` IS one of
the ten courtyards the `.kicad_dru` necking rule names -- the third land is
denied a corridor, not a width, and a width lever cannot buy a corridor.  The
promoted ordering is the first: it is 8.4 mm leaner and one barrel cheaper, and
it leaves the CLOCK rather than a data line to be routed later, on the view that
committing `SPI_B_SCK` to the longest path of the three is the one choice that
is hard to undo.  This is the same **shared-corridor allocation** wall D-596 and
D-598 both recorded; a greedy per-net maze cannot allocate a pin field any more
than it can allocate a corridor.

**RE-PROVED INDEPENDENTLY, all 14 checks PASS** (`verify_promotion.py --evicted`):
15 objects removed and every one on the evicted net; 59 added (47 tracks + 12
vias) and every one on a claimed net; every track 0.200 mm on `F`/`B`/`In2`;
every barrel 0.60/0.30 mm; zone and rule-area inventories unchanged; KiCad's OWN
unconnected-item count **92 -> 90**; real zone-refilled schematic-parity DRC at
`--severity-all` exactly 199 / 5 / 1 inherited with ZERO attributable and ZERO
parity reports; fill-stable; D-269 / D-186 rule text live; `hardware/beta-v2/`
untouched.  `protected_copper.py`: 15 nets / 393 objects BYTE-IDENTICAL.
`pour_bond_contract.py` P1-P4 PASS on the regenerated 48-tube guard and
`neck_contract.py` passes.

**OPEN SI ITEM, RECORDED NOT HIDDEN.**  The two new branches are long:
`/NFC_CS_N` +100.07 mm and `/SPI_B_MOSI` +116.86 mm.  That is PLACEMENT, not
routing -- `U9` sits at (35.8, 27.7) and `U1` at (46, 120), 93 mm apart, and the
straight-line island gap for `NFC_CS_N` is 82.95 mm, so the realized path is
1.21x direct.  At a 10 MHz SPI clock with ~2 ns edges the critical length is
about 50 mm, so these branches are electrically long and want either a reduced
NFC SPI clock or series termination.  **Run the ST25R3916 link at 1-4 MHz on the
Demo** -- NFC throughput is not a demonstrated feature -- and reduce the
ESP32-S3 GPIO drive strength on this bus.  An electrically long connected branch
is strictly better than the open net it replaces, and NFC is a Demo MUST-HAVE.

**TWO NEGATIVE RESULTS BANKED so they are not re-measured.**
`evidence/d599-pour-fill-parameter-screen.json`: the plane-orphan edges
(`+3V3` 15, `GND` 12) are NOT a fill artefact, and the WHOLE fill-parameter
family was measured so it is never measured again.  The pours already connect
pads SOLIDLY -- `(connect_pads yes ...)` in the board file, and in this KiCad
build `ZONE_CONNECTION_FULL == 2` with every pour carrying `padconn 2`, so
**thermal relief is not why any pad on this board is orphan**.  Clearance
0.250 -> 0.200 mm (the DRU floor) ALONE: +634.346 mm2 of fill, ZERO edges.
Min-thickness 0.200 -> 0.150 mm ALONE: ZERO.  0.200 -> 0.127 mm (JLCPCB's
standard-process minimum trace) ALONE: ZERO.  Only 0.127 mm min-thickness
TOGETHER with 0.200 mm clearance moves anything -- **ONE** `GND` land, 74 -> 73.
**REFUSED**: one edge of 74 does not justify taking the whole board's pour
geometry to the process floor on six layers at once, surrendering 0.05 mm of
pour-to-signal margin everywhere and admitting 0.127 mm fill slivers wherever
the filler wants one.

**THE POUR-BOND GUARD WAS MEASURED AND THEN VINDICATED**
(`evidence/d599-guard-cost.json`).  Every promotion since D-585 has carried the
guard and nothing had ever measured what it costs.  Nine open retained nets were
offered every MST edge TWICE on the same board -- `Field(guard=...)` OFF and ON,
311 guarded `F.Cu` cells and 1168 guarded `B.Cu` cells.  Seven are identical
either way; two are not: `/I2C_SCL_INT` `U3.22 -> U4.13` (OK 46.00 mm OFF,
`NO_PATH` ON) and `/I2C_SDA_INT` `U3.23 -> U4.14` (OK 43.13 mm OFF, `NO_PATH`
ON).  The guard is a PRE-FILTER and not the authority -- clause 4 measures
whole-board open edges after the real refill AND after the `--repair-planes`
stitch -- so both were put through the FULL gate WITHOUT it.  **The first is not
a cost at all.**  `/I2C_SCL_INT` routed `U3.22 -> U4.13` in 49.113 mm with 5
vias and closed its edge (6 -> 5) -- and SEVERED a `GND` pour bond, `GND`
12 -> 13, which `--repair-planes` took as its candidate and could NOT re-bond.
Board 74 -> 74, one net improved and one regressed: **REFUSED by clause 4.  The
guard was RIGHT** -- its keep-out was protecting a bond that route really does
cut and the repair really cannot restore.  `/I2C_SDA_INT` and
`/08_BUTTONS_EXPANDERS/BTN_DOWN_N` were each re-gated ALONE, guard off, and
returned **the identical shape**: net improves by one, `GND` regresses by one,
`--repair-planes` names `GND` as its candidate and cannot re-bond it, board
74 -> 74, REFUSED.  Three independent nets, three identical outcomes, zero
attributable DRC in all three.

**THAT CONVERGENCE IS THE REAL FINDING, AND IT IS BIGGER THAN THE GUARD.**  The
`GND` `B.Cu` bond field in this region is SINGLE-POINT everywhere: every route
that wants to cross it cuts the one neck holding an island on, and no barrel the
8 mm repair window can reach puts it back.  The guard is not the wall -- it is a
correct PREDICTION of the wall.  So the honest reading is not "the guard costs
edges"; it is "the guard hides proposals the gate refuses anyway, for a reason
that is fixable at its root".

**THE ROOT IS FIXABLE, AND THE INSTRUMENT NOW EXISTS.**  A `GND` island stranded
on `B.Cu` behind a 0.15 mm neck is two layers away from a `GND` PLANE on `In1`
and another on `In4`.  ONE through barrel dropped inside that island bonds it to
both: the neck stops being the only bond, the tube stops being critical, the
corridor it was freezing opens -- and the board gains a shorter return path and a
thermal via it did not have, which is good practice whatever the router wanted.
New read-only `screen_bond_redundancy.py` sizes that batch: for every island a
guard tube serves, how many LEGAL sites exist inside the island's own filled
copper for a through via on its own net -- using the emitter's own
`Field.via_ok`, keyed by ZONE UUID (D-597's lesson: a net may own two pours on
one layer and the island indices restart in each), and honouring the guard so it
never proposes a barrel that would slot the bond it is repairing.  The `+3V3`
rows are decisive: `F` island 9 has **5984** legal 0.60 mm sites for its two
tubes, island 11 has 961, island 1 has 913, island 18 has 422, while islands 8
and 10 and both `BQ25185_SYS` islands have none.  `maze3d.bridge_islands` will
NOT do this today: it offers a barrel only to a cluster that is electrically
ORPHAN, and these islands are not orphan -- they are connected, through exactly
one fragile neck.  Evidence `evidence/d599-bond-redundancy.json`.

**A PROVENANCE BUG WAS FOUND AND FIXED RATHER THAN ANNOTATED.**
`screen_corridor_blockers.py` hashed the board at WRITE time, and a run of this
length can have a promotion land underneath it -- `d599-corridor-rescreen-a.json`
was stamped `b8bb6d98` for verdicts measured on `83b6a140`.  It now hashes at
LOAD time and reports `board_changed_during_run`; the stale stamp is corrected by
hand in that file with the consequences spelled out.  `--whole-cap` candidates
are now REPORTED in `whole_net_untested_over_cap` rather than silently skipped.

`evidence/d599-usb-corridor-measurement.json`: see below.

**THE USB LINK IS THE NEXT FABRICATION BLOCKER AND IT IS GETTING WORSE.**
USB-C data/programming is a Demo MUST-HAVE and "USB differential routing and
constraints complete" is an explicit release gate; four edges are open.  Measured
on `83b6a140`: question 2W finds NO whole-net opener for either connector edge;
evicting the ENTIRE USB family board-wide leaves `J3 -> U10` and `R33/34 -> U1`
`NO_PATH`, so the wall is not USB-internal; and a free-space BFS over the
router's own blocked grid finds NO `F.Cu` corridor for those two legs at even
the single 0.25 mm width.  Worse, the `USB_D` contract note records the MCU half
routing in 22.771 / 22.344 mm with two vias each under `F+B`; **today
`USB_D_MCU_N` is `NO_PATH` under `F+B` and `USB_D_MCU_P` needs 30.766 mm and
FOUR barrels.**  `.kicad_dru` section 6 reserves this corridor in WORDS and
nothing enforces that on a router, so every whole-board maze batch since has been
free to lay copper in it -- 44 foreign `F.Cu` nets now do.  A greedy whole-net
cut re-opens `J3 -> U10` at 3.51 mm of free path (RECOVERABLE) and `R33/34 ->
U1` only at 76.80 mm for a 21.9 mm leg (NOT recoverable as a lane, against a
25 mm `diff_pair_uncoupled` budget).  The In2 through-via ruling was NOT taken:
it is the cheap answer and it buys nothing here, because `F+B` is already
`NO_PATH` for `MCU_N` with vias permitted, and relaxing a rule that is not the
binding constraint spends safety margin for no connection.

Usage:

    python3 screen_corridor_blockers.py NET [NET ...] --no-minimal -o OUT.json
    # question 2W runs automatically on any CROSSING_COPPER_WALL edge;
    # --no-whole skips it, --whole-cap N bounds the candidate size

    python3 route_maze_batch.py BLOCKED... OPENER --partial \
        --guard evidence/d599-pour-bond-guard-next.json \
        --evict OPENER --evict-whole --promote \
        --work DIR --out DIR/run.json

Next, in order of leverage:

  1. **A corridor RESERVATION the router honours.**  Recovering the USB corridor
     without reserving it loses it again to the next batch.  `maze3d.Field`
     already takes `guard={layer: [(x, y, keepout_nm), ...]}` and
     `route_maze_batch` already has `--guard`; what is missing is an emitter that
     samples a reserved centreline and an `exempt` list on a guard record, since
     `guard_for` exempts only the single net a record names and a corridor must
     exempt a whole netclass.
  2. **A differential-PAIR proposer.**  A per-net maze cannot hold
     `diff_pair_gap` or an uncoupled-length budget -- the first `F/B` USB screen
     was refused by KiCad for exactly that, at 36.653 mm for an 8.465 mm leg.  A
     fat-centreline wavefront at `2*W + gap = 0.70 mm` split into two tracks
     offset by +/-0.225 mm meets the gap by construction.  Its second customer is
     `NFC_RFI1`/`NFC_RFI2`, the two nets `route_maze_batch.EXCLUDE` holds out.
  3. **`/09_COMMUNITY_HEADER/EXT_SDA`, 3 edges, opener `/09_COMMUNITY_HEADER/EXT_SCL`**
     -- named `RIPUP_SINGLE` by this iteration's re-screen and NOT consumed by it.
     Community Port SDA is a Demo scope requirement.  Re-screen before believing
     it: a rip-up verdict is a property of a board, not of a net.

Status: **BLOCKED** at board completion; no manufacturing candidate is approved.

## Accessory-power control: both switched-rail enables improved, 2 edges promoted (2026-09-04)

The Demo scope requires software-controlled switched 3.3 V AND 5 V accessory
power on the Community Port, and both control nets were open.  Both are now one
edge better and neither cost another net anything.

    whole-board retained open edges   78 -> 76
    raw ratsnest                      94 -> 92
    ACC_PWR_EN 2 -> 1                 ACC_5V_BOOST_EN 2 -> 1
    regressed none    authority d8715223... -> 83b6a140...

`screen_corridor_blockers.py` was RE-run on the board D-596 actually promoted
(`d597-corridor-rescreen.json`) before any of its verdicts were believed, because
D-596 measured them one board earlier.  They held, with one instructive change:
`/NFC_CS_N` moved from `RIPUP_SINGLE` to `CROSSING_COPPER_WALL`, because the
opener it named is the net D-596 evicted whole and rebuilt.  **A rip-up verdict
is a property of a board, not of a net.**

The batch that evicts every opener the screen names is not the best batch.  Four
orderings were measured:

    evict EXT_SCL_BUF ACC_POWER_FAULT_N TCA4307_READY ACC_5V_FB
        ACC_5V_BOOST_EN 2 -> 0 (!), ACC_PWR_EN 2 -> 1, and REFUSED:
        three openers could not rebuild, board 78 -> 79
    evict EXT_SCL_BUF alone       ACC_PWR_EN      2 -> 1   78 -> 77  promotable
    evict ACC_5V_FB alone         ACC_5V_BOOST_EN 2 -> 1   78 -> 77  promotable
    evict TCA4307_READY alone     opener ends at 1                   REFUSED
    both promotable evictions     78 -> 76                           PROMOTED

`ACC_POWER_FAULT_N` bought nothing -- `ACC_PWR_EN`'s `R17.1` -> `U3.20` edge
still returns `NO_PATH` with it gone -- so one of the four openers the screen
named was simply wrong.  A fifth ordering that added `/I2C_SCL_INT` also reached
76 and improved a third net, and was refused because `EXT_SCL_BUF` is the opener
for BOTH `ACC_PWR_EN` -> `U16.1` and `I2C_SCL_INT` -> `U16.3` and the `U16`
approach fits one of them.  Same shape as the community-header I2C pair: **a
greedy per-net maze cannot allocate a shared corridor.**

`verify_promotion.py --evicted` re-proves it from the two board files: 28
removed on the two evicted nets, 67 added (58 tracks + 9 vias) on claimed nets,
all 0.200 mm on `F`/`B`/`In2` with 0.60/0.30 barrels, KiCad's own unconnected
count 94 -> 92, DRC exactly 199/5/1 with zero attributable and zero parity
errors.  `protected_copper.py` byte-identical: `/ACC_3V3_SW` and `/ACC_5V_SW_EN`
were named as openers and were never candidates.

## Bounded pour: the charger SYS rail gets local copper, 3 edges promoted (2026-09-04)

`/01_POWER_TREE/BQ25185_SYS` held **10 of the board's 81 open edges** and had
been parked since D-576.  `+3V3` owns `F`/`In3` and `GND` owns `B`/`In1`/`In4`,
and those five pours closed twelve edges each **by the fill alone** -- a pour
bonds every same-net land it overlaps with no track, no barrel and no pad
escape, which is exactly what a net whose every edge reads
`NO_LEGAL_ESCAPE_SRC` needs.  `BQ25185_SYS` had no pour, and could not have a
board-wide one: at equal zone priority two different-net pours retreat from each
other, so a sixth plane would fight the other five over every square millimetre.

So the pour is BOUNDED, and repeatable, one region per cluster of the rail's
lands:

    python3 route_maze_batch.py /01_POWER_TREE/BQ25185_SYS \
        --plane B.Cu \
        --plane-outline 58.5,72.0,71.0,108.5 \
        --plane-outline 55.0,33.0,60.0,42.0 \
        --partial --join-residual --repair-planes \
        --guard evidence/d596-pour-bond-guard-next.json --promote \
        --work DIR --out evidence/d597-sys-pour-batch.json

    whole-board retained open edges   81 -> 78
    raw ratsnest                      97 -> 94
    BQ25185_SYS                       10 -> 7
    regressed none    removed nothing    added 2 objects
    authority db5f997f... -> d8715223...

`--outline` on `screen_plane_only.py` asks the same question read-only, and it
is the cheap move: seven cases (`d597-bounded-pour-screens.json`) showed the
east pour filling in **seven islands** whether the window is 114.5 or
126.3 mm2 and whether the zone clearance is 0.25 or the 0.200 mm floor -- so the
walls between those islands are foreign copper, not fill margin.  It also
refused two candidates before any gate ran: `/NFC_SUPPLY` at the `U9` corner and
`/01_POWER_TREE/ACC_5V_LX` across the switch node both fill and close nothing.

A pour that is not the whole board is named `POUR` and not `PLANE` on the board,
so the zone inventory reads back as what it is.  Gate clause 6 counts added
zones against REQUESTED regions, and `island_removal_mode` is restored on every
region.

**The pour exposed a real defect in the guard.**  `pour_bond_guard.py` keyed a
pour by `(net, layer)`, which stopped being an identity the moment one net owned
two pours on one layer: the first guard run put a tube on the south pour's
island 0 and `pour_bond_contract.py` P2 read it against the east pour's island
0, reporting all 28 points off copper.  P2 was right.  Both modules now carry
the zone UUID; the contract keys by zone and falls back to `(net, layer)` for
older specs.  P1-P4 pass on the regenerated 49-tube guard.

The residual 7 edges are a **0.80 mm corridor** problem -- `SYS_MAIN` is a power
rail and the width is not waived -- plus `U11.1`, pad-boxed against PROTECTED
`BAT_PROTECTED_P` on a 0.4 mm pitch.  `--neck` was vacuous here for the second
promotion running, even though `U11`/`U12`/`U13`/`U21` are four of the ten
courtyards the necking rule names.

## Rip-up-and-reroute: 4 edges promoted, eviction made whole (2026-09-04)

D-585's screen said the same thing about every open net on this board for two
promotions running: 17 `NO_PATH`, 11 `NO_LEGAL_ESCAPE`.  D-594 built `--neck`
for the escape half, and re-running that screen with the lever ON changed
NOTHING -- all 28 nets returned the same reason
(`evidence/d596-neck-screen-vacuous.json`).  The necking rule names ten
fine-pitch power courtyards and every pad still on the escape wall sits outside
all of them.  So this iteration went to the CORRIDOR instead of the terminal.

`screen_corridor_blockers.py` was run for the first time across the `NO_PATH`
set (`evidence/d596-corridor-blockers.json`) and named an executable rip-up for
16 of 26 edges over 12 nets; `/SX1262_DIO1` and `NFC_VDD_RF` are still
unscreened.  Four of those openings became copper:

    whole-board retained open edges   85 -> 81
    raw ratsnest                      101 -> 97
    improved  /I2C_SCL_INT  /NFC_CS_N  /SPI_B_SCK  BTN_DOWN_N
    regressed none
    authority 2140f6a9... -> db5f997f...

Two framework fixes were needed and both are in `route_maze_batch.py`:

  * **Eviction is now CLOSED UNDER DANGLEMENT.**  The first transaction ripped
    `/09_COMMUNITY_HEADER/EXT_SCL` inside the `EXT_SDA` window, routed, regressed
    nothing -- and was refused for three `track_dangling` reports on `In3.Cu`.  A
    via obstructs on every layer so it is evictable anywhere; a track is
    evictable only on a layer the requested nets may route on, and `In3` is a
    RESERVED plane.  The window took the barrels and left the fragments.
    `evict_closure` now measures endpoint support before and after the removals
    and takes anything the removals themselves stranded, reporting what it
    cannot reach in `dangling_unevictable`.
  * **`--evict-whole`** is the honest unit when the point of the rip-up is to
    REROUTE a net rather than clear a strip of it: every routed object of a named
    net, every layer, board-wide, and that net must also be REQUESTED so the
    primary proposer rebuilds it instead of the 8 mm repair pass.  It strands
    nothing and it clears legacy foreign copper off the poured inner plane --
    `In3.Cu` went 115 -> 112 foreign tracks, 996.69 -> 974.88 mm.

`verify_promotion.py --evicted NET` re-proves a rip-up independently: removals
are licensed only on named nets, and KiCad's OWN unconnected-item count is
measured on both boards (101 -> 97), so a rip-up that stranded anything fails
here without this module ever reading a ledger.  All 14 checks PASS; 42 removed
on the three evicted nets, 135 added (108 tracks + 27 vias) all 0.200 mm on
`F`/`B`/`In2` with 0.60/0.30 mm barrels, DRC exactly 199/5/1 with zero
attributable and zero parity errors, fill-stable.  `protected_copper.py`: 15
nets / 393 objects byte-identical.

Usage:

    python3 route_maze_batch.py BLOCKED_NET OPENER_NET --partial --neck \
        --guard evidence/d596-pour-bond-guard-next.json \
        --evict OPENER_NET --evict-whole --promote \
        --work DIR --out DIR/run.json

Next: the screen already names the openers for `/ACC_PWR_EN`,
`/ACC_5V_BOOST_EN` and the second `/SPI_B_SCK` edge.  `/ACC_3V3_SW` and
`FRONT_RGB_R_N` appear as openers and are PROTECTED -- those edges are walls,
not candidates.

Status: **BLOCKED** at board completion; no manufacturing candidate is approved.

## Whole-board all-layer maze router; 21 nets promoted (2026-09-03)

`maze3d.py` + `route_maze_batch.py` replace the hand-authored single-layer
corridor families. `maze3d.route_join` is one multi-source / multi-target
breadth-first wavefront over the whole `(layer, x, y)` lattice with a costed
through-via move, built on the SAME `QBoard.grid` rasteriser, margins and guard
band as the accepted harnesses; `route_maze_batch.py` is the authority that
routes each net at its own DRU-raised netclass contract and refuses to write the
board unless real zone-refilled schematic-parity KiCad DRC is clean outside the
three inherited classes, whole-board retained open edges strictly decrease with
no net regressed, no object is removed, and every added object is on a net that
succeeded. `qrouter.py` and `incremental_router.py` are unmodified.

Twenty-one retained nets promoted in one transaction: whole-board retained open
edges **446 -> 402**, open retained nets **54 -> 33**, each routed net closed to
zero. Independently re-verified from the board files: 0 removed / 439 added
objects all on routed nets, DRC exactly 199 footprint-library / 5
hole-clearance / 1 solder-mask-bridge with zero attributable and zero
schematic-parity reports, board fill-stable. Authority `64e5ae37...` ->
`61df98a1...`; evidence `evidence/d578-maze-batch21.json`
(`97f6ff52...`). D-269/D-186, RGB, XGPIO4/XGPIO5, `ACC_5V_SW_EN`, approved Demo
NC contacts and `hardware/beta-v2/` intact.

Usage:

    python3 route_maze_batch.py NET [NET ...] --work DIR --out DIR/run.json [--promote]

Next: batch the remaining 33 open retained nets through the same gate, splitting
on the first attributable DRC report. Do NOT return to per-net corridor
enumeration for a net this router has not been tried on.

Status: **BLOCKED** at board completion; no manufacturing candidate is approved.

## BQ25185_SYS U11.1 two-net pocket boundary exhausted (2026-09-03)

The governed SYS pocket framework now screens complete-net withdrawal sets of
size one or two. At isolated `U11.1`, all seven single-net and 21 unique two-net
cases inside the 5 mm pocket produce zero new qualified 0.50/0.250 mm SYS
landings using 0.90/0.40 mm power vias. Compact result SHA-256 is
`899dc224d43de8362b86db617975515761e62fe1bba087e0aa6a92cbee0d87a5`.

This closes the local endpoint-refloor family without invalidating the fixed
qualified U11.1 dogleg already used by the atomic harness. Do not replay these
28 cases without changed geometry. Next implement a bounded waypointed join
search from the fixed U11.1 dogleg to the main SYS component, with any winner
passing the existing complete SYS/replay/refilled-parity gate. No candidate
copper was emitted; board `64e5ae37...`, D-269/D-186, RGB, XGPIO4/XGPIO5,
`ACC_5V_SW_EN`, accepted copper, and `hardware/beta-v2/` remain intact.

## BQ25185_SYS corrected 24-case witness window exhausted (2026-09-03)

Corrected case 23 varies the final qualified `U12.10` witness at via
`(66.9327,103.5245)` mm. All 13 governed endpoints reserve and nine joins
complete; all 15 cross-component trials report `NO_PATH`. The same four
components remain: the main U12/SW9/capacitor tree, isolated `U11.1`, the
`C33.1`/`C64.1` pair, and the `L4.1`/`U21.3` pair. Canonical compact-JSON
result SHA-256 is
`81aff166c84908ba8d8bff3373daf5cc3a40eb6103b074138a590189101383ba`.

Cases 0--23 exhaust this corrected witness family. Do not replay or extend it
without materially new board geometry or a broader refloor/bridge transaction.
No replay, DRC, candidate, or promotion is claimed for the incomplete tree;
zero wrong-net additions/removals occurred. Board `64e5ae37...` remains
byte-identical at 54 open retained nets / 446 edges, with SYS at 12 open edges.
Next build a reusable four-component cross-component bridge/refloor search,
beginning with isolated `U11.1`, behind the existing atomic replay and
full-board gate. D-269/D-186, RGB, XGPIO4/XGPIO5, accepted copper, and
`hardware/beta-v2/` remain intact. No owner decision is open.

## BQ25185_SYS corrected twenty-third atomic case bounded (2026-09-03)

Corrected case 22 varies the twenty-third qualified `U12.10` witness at via
`(66.8543,103.5029)` mm. All 13 governed endpoints reserve and nine joins
complete before the finite 24-trial window is exhausted. The same four
components remain: the main U12/SW9/capacitor tree, isolated `U11.1`, the
`C33.1`/`C64.1` pair, and the `L4.1`/`U21.3` pair. All 15 attempted
cross-component joins report `NO_PATH`; canonical compact-JSON result SHA-256
is `c7f13e3177fb612aa3d5a6e2acbac54889105f34344fb7c3c77d04cb28bd2b54`.
No replay, DRC, candidate, or promotion is claimed for an incomplete SYS tree.
The harness reports zero wrong-net additions/removals. Authority remains
`64e5ae37...`, 54 open retained nets / 446 edges; SYS itself remains at 12
open edges. The SYS tree is an immediate board-completion critical path, so
the finite non-overlapping window continues under the routing-wall policy
exception. Continue at case 23 without replaying cases 0--22.

## BQ25185_SYS corrected twenty-second atomic case bounded (2026-09-03)

Corrected case 21 varies the twenty-second qualified `U12.10` witness at via
`(66.8402,103.5250)` mm. All 13 governed endpoints reserve and nine joins
complete before the finite 24-trial window is exhausted. The same four
components remain: the main U12/SW9/capacitor tree, isolated `U11.1`, the
`C33.1`/`C64.1` pair, and the `L4.1`/`U21.3` pair. All 15 attempted
cross-component joins report `NO_PATH`. No replay, DRC, candidate, or
promotion is claimed for an incomplete SYS tree. The harness reports zero
wrong-net additions/removals. Authority remains `64e5ae37...`, 54 open
retained nets / 446 edges; SYS itself remains at 12 open edges. The SYS tree
is an immediate board-completion critical path, so the finite non-overlapping
window continues under the routing-wall policy exception. Continue at case 22
without replaying cases 0--21.

## BQ25185_SYS corrected twenty-first atomic case bounded (2026-09-03)

Corrected case 20 varies the twenty-first qualified `U12.10` witness at via
`(66.9305,103.4996)` mm. All 13 governed endpoints reserve and nine joins
complete before the finite 24-trial window is exhausted. The same four
components remain: the main U12/SW9/capacitor tree, isolated `U11.1`, the
`C33.1`/`C64.1` pair, and the `L4.1`/`U21.3` pair. All 15 attempted
cross-component joins report `NO_PATH`; canonical compact-JSON result SHA-256
is `8a7f46005958b3211cf5fd772cb293f0bc8316fb122e68db7cb43f360261e18c`.
No replay, DRC, candidate, or promotion is claimed for an incomplete SYS tree.
The harness reports zero wrong-net additions/removals. Authority remains
`64e5ae37...`, 54 open retained nets / 446 edges. SYS is an immediate
board-completion critical path, so the finite non-overlapping window continues
under the routing-wall policy exception. Continue at case 21 without replaying
cases 0--20.

## BQ25185_SYS corrected twentieth atomic case bounded (2026-09-03)

Corrected case 19 varies the twentieth qualified `U12.10` witness at via
`(66.9165,103.5217)` mm. All 13 governed endpoints reserve and nine joins
complete before the finite 24-trial window is exhausted. The same four
components remain: the main U12/SW9/capacitor tree, isolated `U11.1`, the
`C33.1`/`C64.1` pair, and the `L4.1`/`U21.3` pair. All 15 attempted
cross-component joins report `NO_PATH`; canonical compact-JSON result SHA-256
is `fe785133400b276bf0d2103b575173af06522d5b384046322e1a12fdd1bb3d6b`.
No replay, DRC, candidate, or promotion is claimed for an incomplete SYS tree.
The harness reports zero wrong-net additions/removals. Authority remains
`64e5ae37...`, 54 open retained nets / 446 edges. SYS is an immediate
board-completion critical path, so the finite non-overlapping window continues
under the routing-wall policy exception. Continue at case 20 without replaying
cases 0--19.

## BQ25185_SYS corrected nineteenth atomic case bounded (2026-09-03)

Corrected case 18 varies the nineteenth qualified `U12.10` witness at via
`(66.8525,103.3775)` mm. All 13 governed endpoints reserve and nine joins
complete before the finite 24-trial window is exhausted. The same four
components remain: the main U12/SW9/capacitor tree, isolated `U11.1`, the
`C33.1`/`C64.1` pair, and the `L4.1`/`U21.3` pair. All 15 attempted
cross-component joins report `NO_PATH`. No replay, DRC, candidate, or
promotion is claimed for an incomplete SYS tree. The harness reports zero
wrong-net additions/removals. Authority remains `64e5ae37...`, 54 open
retained nets / 446 edges. SYS is an immediate board-completion critical path,
so the finite non-overlapping window continues under the routing-wall policy
exception. Continue at case 19 without replaying cases 0--18.

## BQ25185_SYS corrected eighteenth atomic case bounded (2026-09-03)

Corrected case 17 varies the eighteenth qualified `U12.10` witness. All 13
governed endpoints reserve and nine joins complete before the finite 24-trial
window is exhausted. The same four components remain: the main
U12/SW9/capacitor tree, isolated `U11.1`, the `C33.1`/`C64.1` pair, and the
`L4.1`/`U21.3` pair. All 15 attempted cross-component joins report `NO_PATH`;
canonical compact-JSON result SHA-256 is
`0fa78eb48f30f0c266ce337d2404d96e2f491148288b519e235dbdaa3f9a4c41`.
No replay, DRC, candidate, or promotion is claimed for an incomplete SYS tree.
Authority remains `64e5ae37...`, 54 open retained nets / 446 edges. SYS is an
immediate board-completion critical path, so the finite non-overlapping window
continues under the routing-wall policy exception. Continue at case 18 without
replaying cases 0--17.

## BQ25185_SYS corrected seventeenth atomic case bounded (2026-09-03)

Corrected case 16 varies the seventeenth qualified `U12.10` witness. All 13
governed endpoints reserve and nine joins complete before the finite 24-trial
window is exhausted. The same four components remain: the main
U12/SW9/capacitor tree, isolated `U11.1`, the `C33.1`/`C64.1` pair, and the
`L4.1`/`U21.3` pair. All 15 attempted cross-component joins report `NO_PATH`;
canonical compact-JSON result SHA-256 is
`e69d669bfae38cf4e6690e7d2afc564a20779f5e0df6ff936dbb178c875d7ff3`.
No replay, DRC, candidate, or promotion is claimed for an incomplete SYS tree.
Authority remains `64e5ae37...`, 54 open retained nets / 446 edges. SYS is an
immediate board-completion critical path, so the finite non-overlapping window
continues under the routing-wall policy exception. Continue at case 17 without
replaying cases 0--16.

## BQ25185_SYS corrected sixteenth atomic case bounded (2026-09-03)

Corrected case 15 varies the sixteenth qualified `U12.10` witness. All 13
governed endpoints reserve and nine joins complete before the finite 24-trial
window is exhausted. The same four components remain: the main
U12/SW9/capacitor tree, isolated `U11.1`, the `C33.1`/`C64.1` pair, and the
`L4.1`/`U21.3` pair. All 15 attempted cross-component joins report `NO_PATH`;
canonical compact-JSON result SHA-256 is
`d298c15e08fc2cc7f334263ea9fa893b1d4ac09ad22d82c60eac2221bc64802d`.
No replay, DRC, candidate, or promotion is claimed for an incomplete SYS tree.
Authority remains `64e5ae37...`, 54 open retained nets / 446 edges. SYS is an
immediate board-completion critical path, so the finite non-overlapping window
continues under the routing-wall policy exception. Continue at case 16 without
replaying cases 0--15.

## BQ25185_SYS corrected fifteenth atomic case bounded (2026-09-03)

Corrected case 14 varies the fifteenth qualified `U12.10` witness. All 13
governed endpoints reserve and nine joins complete before the finite 24-trial
window is exhausted. The same four components remain: the main
U12/SW9/capacitor tree, isolated `U11.1`, the `C33.1`/`C64.1` pair, and the
`L4.1`/`U21.3` pair. All 15 attempted cross-component joins report `NO_PATH`;
canonical compact-JSON result SHA-256 is
`ce4f75e5352492d43dd6f90f7ff37c0747c3f08678884d709030915cca8e4561`.
No replay, DRC, candidate, or promotion is claimed for an incomplete SYS tree.
Authority remains `64e5ae37...`, 54 open retained nets / 446 edges. SYS is an
immediate board-completion critical path, so the finite non-overlapping window
continues under the routing-wall policy exception. Continue at case 15 without
replaying cases 0--14.

## BQ25185_SYS corrected fourteenth atomic case bounded (2026-09-03)

Corrected case 13 varies the fourteenth qualified `U12.10` witness. All 13
governed endpoints reserve and nine joins complete before the finite 24-trial
window is exhausted. The same four components remain: the main
U12/SW9/capacitor tree, isolated `U11.1`, the `C33.1`/`C64.1` pair, and the
`L4.1`/`U21.3` pair. All 15 attempted cross-component joins report `NO_PATH`;
canonical compact-JSON result SHA-256 is
`7329cabbb30e5f39ce75179ff197a00051e23574a72b9f146a4f5de6e5f22c0d`.
No replay, DRC, candidate, or promotion is claimed for an incomplete SYS tree.
Authority remains `64e5ae37...`, 54 open retained nets / 446 edges. SYS is an
immediate board-completion critical path, so the finite non-overlapping window
continues under the routing-wall policy exception. Continue at case 14 without
replaying cases 0--13.

## BQ25185_SYS corrected thirteenth atomic case bounded (2026-09-03)

Corrected case 12 varies the thirteenth qualified `U12.10` witness. All 13
governed endpoints reserve and nine joins complete before the finite 24-trial
window is exhausted. The same four components remain: the main
U12/SW9/capacitor tree, isolated `U11.1`, the `C33.1`/`C64.1` pair, and the
`L4.1`/`U21.3` pair. All 15 attempted cross-component joins report `NO_PATH`;
canonical compact-JSON result SHA-256 is
`33dab159d6ed1e03791ffae9ddc94b77b5cff74582587fe0dd99c8fc11a02452`.
No replay, DRC, candidate, or promotion is claimed for an incomplete SYS tree.
Authority remains `64e5ae37...`, 54 open retained nets / 446 edges. SYS is an
immediate board-completion critical path, so the finite non-overlapping window
continues under the routing-wall policy exception. Continue at case 13 without
replaying cases 0--12.

## BQ25185_SYS corrected twelfth atomic case bounded (2026-09-03)

Corrected case 11 varies the twelfth qualified `U12.10` witness. All 13
governed endpoints reserve and nine joins complete before the finite 24-trial
window is exhausted. The same four components remain: the main
U12/SW9/capacitor tree, isolated `U11.1`, the `C33.1`/`C64.1` pair, and the
`L4.1`/`U21.3` pair. All 15 attempted cross-component joins report `NO_PATH`;
canonical compact-JSON result SHA-256 is
`d077b3ee6dd432f5360d525a0e5b18191a339f60c1602c22adbdedb9203c5c64`.
No replay, DRC, candidate, or promotion is claimed for an incomplete SYS tree.
Authority remains `64e5ae37...`, 54 open retained nets / 446 edges. SYS is an
immediate board-completion critical path, so the finite non-overlapping window
continues under the routing-wall policy exception. Continue at case 12 without
replaying cases 0--11.

## BQ25185_SYS corrected eleventh atomic case bounded (2026-09-03)

Corrected case 10 varies the eleventh qualified `U12.10` witness. All 13
governed endpoints reserve and nine joins complete before the finite 24-trial
window is exhausted. The same four components remain: the main
U12/SW9/capacitor tree, isolated `U11.1`, the `C33.1`/`C64.1` pair, and the
`L4.1`/`U21.3` pair. All 15 attempted cross-component joins report `NO_PATH`;
canonical structured result SHA-256 is
`10e6f088abefc9a283fc8737b14c9ebb513c44371d7ccf678c5b51cf20327125`.
No replay, DRC, candidate, or promotion is claimed for an incomplete SYS tree.
Authority remains `64e5ae37...`, 54 open retained nets / 446 edges. Continue
at case 11 without replaying cases 0--10.

## BQ25185_SYS corrected tenth atomic case bounded (2026-09-03)

Corrected case 9 varies the tenth qualified `U12.10` witness. All 13 governed
endpoints reserve and nine joins complete before the finite 24-trial window is
exhausted. The same four components remain: the main U12/SW9/capacitor tree,
isolated `U11.1`, the `C33.1`/`C64.1` pair, and the `L4.1`/`U21.3` pair. All
15 attempted cross-component joins report `NO_PATH`. No replay, DRC,
candidate, or promotion is claimed for an incomplete SYS tree. Authority
remains `64e5ae37...`, 54 open retained nets / 446 edges. Continue at case 10
without replaying cases 0--9.

## BQ25185_SYS corrected eighth atomic case bounded (2026-09-03)

Corrected case 7 varies the eighth qualified `U12.10` witness. All 13 governed
endpoints reserve and nine joins complete before the finite 24-trial window is
exhausted. The same four components remain: the main U12/SW9/capacitor tree,
isolated `U11.1`, the `C33.1`/`C64.1` pair, and the `L4.1`/`U21.3` pair. All
15 attempted cross-component joins report `NO_PATH`; canonical structured
result SHA-256 is `a093abe62eb5e92537df5d1e7680d978c4e384270ada02b6e12ea5c17ac8b678`.
No replay, DRC, candidate, or promotion is claimed for an incomplete SYS tree.
Authority remains `64e5ae37...`, 54 open retained nets / 446 edges. Continue
the corrected non-overlapping window at case 8.

## BQ25185_SYS corrected seventh atomic case bounded (2026-09-03)

Corrected case 6 varies the seventh qualified `U12.10` witness. All 13 governed
endpoints reserve and nine joins complete before the finite 24-trial window is
exhausted. The same four components remain: the main U12/SW9/capacitor tree,
isolated `U11.1`, the `C33.1`/`C64.1` pair, and the `L4.1`/`U21.3` pair. All
15 attempted cross-component joins report `NO_PATH`; canonical structured
result SHA-256 is `23653312a82394deb7d7ba595e289188969980295e7ce741241863879290d7fa`.
No replay, DRC, candidate, or promotion is claimed for an incomplete SYS tree.
Authority remains `64e5ae37...`, 54 open retained nets / 446 edges. Continue
the corrected non-overlapping window at case 7.

## BQ25185_SYS corrected sixth atomic case bounded (2026-09-03)

Corrected case 5 varies the sixth qualified `U12.10` witness. All 13 governed
endpoints reserve and nine joins complete before the finite 24-trial window is
exhausted. The same four components remain: the main U12/SW9/capacitor tree,
isolated `U11.1`, the `C33.1`/`C64.1` pair, and the `L4.1`/`U21.3` pair. All
15 attempted cross-component joins report `NO_PATH`. No replay, DRC,
candidate, or promotion is claimed for an incomplete SYS tree. Authority
remains `64e5ae37...`, 54 open retained nets / 446 edges. Continue the
corrected non-overlapping window at case 6.

## BQ25185_SYS corrected fifth atomic case bounded (2026-09-03)

Corrected case 4 varies the fifth qualified `U12.10` witness. All 13 governed
endpoints reserve and nine joins complete before the finite 24-trial window is
exhausted. The same four components remain: the main U12/SW9/capacitor tree,
isolated `U11.1`, the `C33.1`/`C64.1` pair, and the `L4.1`/`U21.3` pair. All
15 attempted cross-component joins report `NO_PATH`; canonical structured
result SHA-256 is `d101bd5b41eaac209299f3ed6eff68aaf7b17ddbf6c830e98f127df8d4a8df96`.
No replay, DRC, candidate, or promotion is claimed for an incomplete SYS tree.
Authority remains `64e5ae37...`, 54 open retained nets / 446 edges. Continue
the corrected non-overlapping window at case 5.

## BQ25185_SYS corrected fourth atomic case bounded (2026-09-03)

Corrected case 3 varies the fourth qualified `U12.10` witness. All 13 governed
endpoints reserve and nine joins complete before the finite 24-trial window is
exhausted. The same four components remain: the main U12/SW9/capacitor tree,
isolated `U11.1`, the `C33.1`/`C64.1` pair, and the `L4.1`/`U21.3` pair. All
15 attempted cross-component joins report `NO_PATH`; canonical structured
result SHA-256 is `494d5275e236545850774b0e914d5049bec333f39639317b6cc0bb11d5a3d3ea`.
No replay, DRC, candidate, or promotion is claimed for an incomplete SYS tree.
Authority remains `64e5ae37...`, 54 open retained nets / 446 edges. Continue
the corrected non-overlapping window at case 4.

## BQ25185_SYS corrected third atomic case bounded (2026-09-03)

Corrected case 2 varies the third qualified `U12.10` witness.  All 13 governed
endpoints reserve and nine joins complete before the finite 24-trial window is
exhausted.  The same four components remain: the main U12/SW9/capacitor tree,
isolated `U11.1`, the `C33.1`/`C64.1` pair, and the `L4.1`/`U21.3` pair.  All
15 attempted cross-component joins report `NO_PATH`; canonical structured
result SHA-256 is `84c78bd6453d0eb0e0e3d206ab69469b1eb8bd585585c4cf53d6e9c67d31e1e5`.
No replay, DRC, candidate, or promotion is claimed for an incomplete SYS tree.
Authority remains `64e5ae37...`, 54 open retained nets / 446 edges. Continue
the corrected non-overlapping window at case 3.

## BQ25185_SYS corrected second atomic case bounded (2026-09-03)

Corrected case 1 varies the next qualified `U12.10` witness and again reserves
all 13 governed SYS endpoints.  It completes nine joins, then exhausts the
finite 24-trial window with the same four components remaining.  The changed
`U12.10` landing does not change the immediate join topology: `U11.1` remains
isolated, while the `C33.1`/`C64.1` and `L4.1`/`U21.3` groups remain separate
from the main tree.  No replay, DRC, candidate, or promotion is claimed for an
incomplete SYS tree.  Authority remains `64e5ae37...`, 54 open retained nets /
446 edges.  Continue the corrected non-overlapping window at case 2.

## BQ25185_SYS corrected first atomic case bounded (2026-09-03)

The D-551 eight-join cap was structurally too small: a 13-land tree requires at
least 12 successful joins.  The harness now defaults to 24 bounded attempts and
rejects any requested limit below 12.  Corrected case 0 places every governed
endpoint and completes nine joins, but exhausts all 24 attempts with four
components remaining.  Fifteen joins report `NO_PATH`, concentrated around
`U11.1` plus the still-separated `C33.1` and accessory-boost group.  No replay,
DRC, candidate, or promotion is claimed for an incomplete SYS tree.  Authority
remains `64e5ae37...`, 54 open retained nets / 446 edges.  Continue at case 1
with the corrected >=12-attempt contract; do not reuse the invalid D-551
eight-attempt results as routing evidence.

## BQ25185_SYS atomic SW9-A refloor harness bounded (2026-09-03)

The recovered D-550 successor now withdraws/replays the complete 27-object
`Net-(SW9-A)` tree, injects qualified U12.10 doglegs before L4, and preserves
the existing all-or-nothing SYS/connectivity/refill/real-DRC gate.  Case windows
are resumable; route children have explicit time/join bounds; child and replay
records use final-JSON extraction because KiCad/SWIG may write diagnostics to
stdout.  An inherited pre-bound run reached case 6 after 46 minutes but emitted
no complete case record or candidate and was safely stopped.  Authority remains
`64e5ae37...`, 54 open retained nets / 446 edges.  Start corrected screening at
case 0; do not treat the partial inherited output as evidence.

## BQ25185_SYS U12.10 pocket boundary qualified (2026-09-03)

The atomic harness can now reserve U12.10 before L4. All 24 L4-witness cases
still stop at `U12.10 NO_FLARE`, proving the immediate wall predates L4. The
governed U12.10 pocket screen tested eight complete nearby accepted nets; only
complete withdrawal of the 27-object `Net-(SW9-A)` tree exposes landings (48).
Canonical result hash is `2a0fc2ba...`; board `64e5ae37...` remains unchanged at
54 open retained nets / 446 edges. Next add complete SW9-A withdrawal/replay and
a qualified U12.10 dogleg to the existing atomic SYS transaction.

## BQ25185_SYS L4/U12.10 coexistence boundary bounded (2026-09-03)

The atomic SYS transaction now includes complete `NFC_ANT_B` withdrawal, a
qualified L4 dogleg, and exact accepted antenna replay. A corrected 24-case
window varies all 24 qualified L4 witnesses first. Every witness reserves with
the preceding ten SYS endpoints, but all stop at `U12.10 NO_FLARE`; therefore
the boundary is joint L4/U12.10 coexistence, not L4 site-zero quality. No
candidate or partial copper is emitted; board `64e5ae37...` remains unchanged
at 54 open retained nets / 446 edges. Next reserve U12.10 before L4 and
co-search both qualified endpoint families, then inventory only the joint
pocket if neither order coexists.

## BQ25185_SYS L4 pocket boundary qualified (2026-09-03)

The generic complete-net pocket screen now covers `L4.1`. All six isolated
nearby-net withdrawals expose 48 governed SYS doglegs. The minimum complete
boundary is the 16 B.Cu segments of `NFC_ANT_B`; the 19-object `ACC_5V_RAW`
tree is the next-smallest fallback. This is characterization only: neither NFC
nor accessory power may remain open. Result hash is `9009241d...`; board
`64e5ae37...` remains byte-identical at 54 open retained nets / 446 edges.
Next add the first L4 witness and complete `NFC_ANT_B` replay to the existing
atomic SYS transaction, accepting only zero-open connectivity and real DRC.

## BQ25185_SYS joint C26/C27/C28 refloor and L4 boundary (2026-09-03)

The atomic SYS transaction now includes complete `Net-(L1-Pad1)` withdrawal,
a qualified C28 dogleg, and exact replay of all five accepted switch-node B.Cu
segments. Eight bounded C26/C27/C28 triples clear the three prior endpoint
walls and stop at pristine `L4.1` with `NO_VIA_SITE`; no partial copper is
emitted. Canonical result hash is `d4bdffe8...`. The authoritative board
remains byte-identical at `64e5ae37...`, 54 open retained nets / 446 edges.
Next inventory complete accepted copper in the L4.1 pocket and screen the
minimum withdrawal/replay boundary, then extend this same 13-land transaction.

## BQ25185_SYS joint C26/C27 refloor and C28 boundary (2026-09-03)

`route_bq25185_sys_ir_refloor_scratch.py` now treats complete
`IR_RX_GPIO44` plus `ILIM_VSET` withdrawal/replay and both qualified SYS
doglegs as one atomic transaction. Eight bounded C26/C27 pairs advance to
`C28.1`, where every case stops before joins with `NO_LEGAL_ESCAPE`; no partial
copper is emitted. The generalized pocket screen tests all six accepted nets
within 5 mm of C28. The minimum complete withdrawal is the five B.Cu objects
of `Net-(L1-Pad1)`, exposing 48 governed 0.50/0.250 mm doglegs with ordinary
0.90/0.40 mm vias. Focused evidence hash is `44b34650...`; the authoritative
board remains byte-identical at `64e5ae37...`, 54 open nets / 446 edges. Next
extend the same transaction with complete L1-pad1 withdrawal/replay and the
qualified C28 witness, then continue the 13-land SYS tree under the full gate.

## BQ25185_SYS C27 minimum pocket-refloor boundary qualified (2026-09-03)

The generalized `screen_bq25185_sys_c26_pocket_refloor.py` inventories all
seven complete accepted copper nets within 5 mm of `C27.1` and tests each on
an isolated scratch board. Every single-net withdrawal exposes exactly 48
ordinary 0.90/0.40 mm SYS via landings, proving that accepted copper occupancy,
not the C27 package geometry, is the wall. The minimum complete boundary is
`/01_POWER_TREE/ILIM_VSET`: nine objects (five B.Cu tracks, two In3.Cu tracks,
and two vias). A focused repeat reproduces the complete case record hash
`dc6f7f38...`. This is characterization only; the authoritative board remains
byte-identical at `64e5ae37...`, 54 open retained nets / 446 edges. Next extend
the atomic SYS/IR harness to withdraw complete `ILIM_VSET`, reserve the first
qualified C27 witness, route the full 13-land SYS tree, and replay both
`IR_RX_GPIO44` and `ILIM_VSET`; accept only on the full-board gate. Preserve
the promoted USB charger tree and the accepted `ACC_5V_SW_EN` route.

## BQ25185_SYS C26 minimum pocket-refloor boundary qualified (2026-09-03)

`screen_bq25185_sys_c26_pocket_refloor.py` inventories every complete accepted
copper net within 5 mm of `C26.2` and tests six isolated single-net withdrawals
against the exhaustive dogleg family. Three open exactly 48 ordinary 0.90/0.40
mm SYS via landings: `/IR_RX_GPIO44` (14 complete-net objects),
`Net-(U12-PS_SYNC)` (33), and `/01_POWER_TREE/USB_VBUS_CHG` (58). U12 PG,
SW9-A, and the GPIO45 strap do not open a landing. The authoritative board is
unchanged at `64e5ae37...`, 54 open retained nets / 446 edges. Next build the
minimum atomic transaction: withdraw complete IR_RX_GPIO44, reserve a qualified
C26 escape, route the full 13-land SYS tree, replay IR_RX_GPIO44, and accept only
on the full-board gate. Do not disturb the newly promoted charger tree.

## BQ25185_SYS C26 dogleg family bounded (2026-09-03)

The recovered dogleg enumerator adds `C26.2` and exact spatial indexes without
changing collision geometry.  A 500-case equivalence test found zero mismatches
against the original predicates, and two runs reproduce report hash
`4eaaa5d5...` in about 49 seconds.  The exhaustive 5-degree / 50-um family
extends 2,422 legal straight anchors but finds zero ordinary 0.90/0.40 mm
all-layer via landings; 2,367,480 terminal sites fail the all-layer test.
Scratch project refilled parity DRC remains 199/5/1.  No copper is promoted;
board `64e5ae37...` remains at 54 open retained nets / 446 edges.  Next
inventory complete accepted copper nets in the C26 pocket and screen the
minimum atomic withdrawal/replay boundary with the full 13-land SYS tree; do
not retry the exhausted straight/dogleg families or weaken 0.50/0.250 mm SYS.

## BQ25185_SYS C26 endpoint wall bounded (2026-09-03)

The complete 13-land SYS harness now reserves `C26.2` before `C24.1`, proving
the wall is intrinsic rather than a reservation-order casualty. C26 has no
generic 0.90/0.40 mm power-via escape. Its new full-geometry directional case
exhausts the 5-degree / 25-um straight-launch family with zero candidates and
no attributable real-DRC report. No copper is promoted; board `64e5ae37...`
remains at 54 open retained nets / 446 edges. Next extend the bounded short-
dogleg screen to C26, then inventory a minimum complete-net pocket refloor if
needed; do not reduce the 0.50/0.250 mm SYS contract.

## USB_VBUS_CHG atomic refloor promoted (2026-09-03)

The D-539 transaction now replays `REC_LIM_IN` on In2 and `ILIM_VSET` on In3,
with 0.200/0.200 mm B.Cu package escapes and ordinary 0.60/0.30 mm transition
vias. The CHG tree preserves the hard 0.35 mm R91 neck, governed 0.20 mm U11
neck, 0.50/0.250 mm hauls, and ordinary 0.90/0.40 mm power vias. Case zero
closes all three complete nets and passes real refilled schematic-parity DRC
at the unchanged 199/5/1 signature with no attributable violation or wrong-net
copper removal/addition. The promoted board is `64e5ae37...`, 54 open retained
nets / 446 edges. Next route the 12-edge `BQ25185_SYS` tree atomically.

## USB_VBUS_CHG minimum refloor transaction bounded (2026-09-03)

`route_usb_vbus_chg_refloor_scratch.py` is the atomic D-539 harness. It removes
complete `REC_LIM_IN` and `ILIM_VSET` copper only on scratch boards, installs
the two qualified governed CHG necks, routes the complete eleven-land tree,
and then replays both removed nets. Case zero closes every CHG join at the
locked 0.50/0.250 mm haul contract but cannot replay `REC_LIM_IN` at
0.200/0.200 mm from Q5.3 to R95.1. Authority remains `801cfa7e...` and no
partial candidate is retained. Next add a bounded joint `REC_LIM_IN` replay
refloor around that complete tree; the larger qualified `REC_GATE_N` boundary
is the fallback. Do not spend the next iteration enumerating equivalent CHG
neck pairs before addressing the replay wall.

## USB_VBUS_CHG minimum pocket-refloor boundary qualified (2026-09-03)

`screen_usb_vbus_chg_pocket_refloor.py` inventories every accepted copper net
with an endpoint inside either 5 mm wall pocket and tests all 14 complete-net
single-withdrawal cases on isolated scratch boards. Three cases open governed
necks: `REC_GATE_N` (18 objects) or the smaller `REC_LIM_IN` (7 objects) at
`R91.1`, and uniquely `ILIM_VSET` (5 objects) at `U11.10`. No safety copper is
changed on authority; board `801cfa7e...` remains unchanged.

The minimum joint boundary is therefore two complete nets and 12 objects:
`REC_LIM_IN` plus `ILIM_VSET`. Next test both R91 alternatives atomically:
withdraw the complete R91 net plus `ILIM_VSET`, reserve both qualified necks,
route the complete 11-land CHG tree, replay both withdrawn nets, and accept
only a full-board PASS. Do not withdraw `BAT_RAW` or `BAT_PROTECTED_P`.

## USB_VBUS_CHG governed-neck family bounded (2026-09-03)

`enumerate_usb_vbus_chg_necks.py` is the reusable D-537 successor to the
whole-tree endpoint screen. It permits only package-local narrowing: 0.30 mm
at `R91.1` with the full 0.250 mm clearance, and the already-governed U11
0.20/0.20 mm fine-pitch neck at `U11.10`. Every route must widen to the locked
0.50/0.250 mm haul and reach an ordinary 0.90/0.40 mm all-layer via.

Both the initial collinear family and the direct/one-elbow 5 x 5 mm dogleg
family produce zero candidates. Existing tracks plus R90/R92 bind the R91
pocket; U11.9, R36, accepted tracks, and the east board edge bind U11. This is
characterization only: board `801cfa7e...` remains unchanged at 55 open nets /
456 edges with real refilled parity DRC 199/5/1. Next inventory complete nets
in both package pockets and screen the minimum atomic withdrawal/replay set
together with the complete 11-land CHG tree.

## USB_VBUS_CHG whole-tree endpoint boundary bounded (2026-09-03)

`route_usb_vbus_chg_tree_scratch.py` is the atomic 11-land successor to the
promoted RAW/shield transaction. It holds the live 0.50 mm width, 0.250 mm
clearance, and 0.90/0.40 mm via contract. Independent screens qualify nine
endpoint escapes; only `R91.1` and `U11.10` have no legal full-width escape.
The complete transaction stops at the first wall and emits no partial candidate.
The authoritative board remains `801cfa7e...`, 55 open nets / 456 edges, with
accepted DRC 199/5/1. Next qualify governed package necks at those two lands and
replay them through this whole-tree gate; keep every inner haul at 0.50 mm.

## USB_VBUS_RAW plus shield atomic refloor promoted (2026-09-03)

`route_usb_vbus_shield_refloor_scratch.py` withdraws the complete old shield
tree, installs the qualified seven-land RAW site-zero route, and replays all
five shield lands in one gated transaction. A 0.20 mm shield replay was
rejected by real DRC; both deterministic orders pass when the live 0.250 mm
VBUS clearance is enforced. Order zero is promoted. RAW is fully connected,
the shield remains fully connected, and the board improves to 55 open retained
nets / 456 edges with real refilled schematic-parity DRC 199/5/1 and no
attributable report. Board SHA-256 is `801cfa7e...`. Next route the adjacent
10-edge `USB_VBUS_CHG` charger-entry tree without disturbing this boundary.

## USB_VBUS_RAW shield-refloor boundary qualified (2026-09-03)

`screen_usb_vbus_bcu_refloor.py` proves the minimum complete-net boundary for
the blocked north-edge haul.  The only accepted B.Cu occupant in the corridor
is `Net-(J3-SHIELD)`.  With its complete 14-object copper tree withdrawn in
scratch, all eight qualified C20 cases close the complete seven-land RAW
geometry at 0.50 mm width / 0.20 mm clearance.  No candidate is emitted because
the shield is not yet replayed.  Board `04dc3e8a...` remains unchanged at 56
open retained nets / 460 edges with authoritative DRC 199/5/1.  Next build one
atomic RAW-plus-shield replay transaction using the site-zero witness.

## USB_VBUS_RAW explicit B.Cu perimeter bounded (2026-09-03)

The atomic RAW-tree harness now screens a finite 0.50 mm B.Cu Manhattan
perimeter family and has a repaired promotion-stage predicate.  Across all
eight qualified C20 escapes, 11,256 explicit direct, orthogonal, north-edge,
vertical-spine, and two-spine paths reject at the first C20-to-J3.A9 join.
Endpoint escapes and both J3 POFVs remain qualified, but no partial candidate
is emitted.  Board `04dc3e8a...` remains unchanged at 56 open nets / 460 edges
with authoritative DRC 199/5/1.  Next bound the complete B.Cu nets occupying
this corridor and test a minimum complete-net withdrawal plus atomic replay;
do not weaken the 0.50/0.20 mm VBUS contract or promote connector islands.

## USB_VBUS_RAW POFV transaction advances to B.Cu haul wall (2026-09-02)

`route_usb_vbus_raw_tree_scratch.py` now carries the complete D-531 boundary:
two named pad-sized J3 rule areas, two 0.35/0.20 mm POFVs inserted atomically,
ordinary 0.80/0.40 mm endpoint vias, a 0.50 mm B.Cu trunk, and a 0.35 mm neck
only inside the U10.5 package escape. C20 endpoint sites 0--7 all coexist with
the first legal U10 escape and both POFVs, but every case returns `NO_PATH` on
the first 0.50 mm C20-to-A9 B.Cu join. Incomplete candidates are rejected; real
scratch DRC finds no POFV-rule violation, and authoritative DRC remains 199/5/1.
Board `04dc3e8a...` stays byte-identical at 56 open nets / 460 edges. Next add
explicit staged B.Cu perimeter corridors between these qualified endpoints and
accept only the complete seven-land tree.

## USB VBUS POFV boundary qualified (2026-09-02)

The D-530 planar-pour/neck successor is now bounded. J3.A9/B4 has no legal
F.Cu launch from 0.50 down through 0.15 mm: both side gaps are exactly the
0.200 mm clearance floor, leaving no positive-width copper throat, while the
verified Ø0.65 locating hole blocks the inward direction. A pour cannot cross
that boundary either. The existing 0.35/0.20 mm plated-over-filled through-via
process fits the 0.60 mm VBUS lands with 0.125 mm host copper per side, matching
the already-fitted Q3.3 process geometry. No rule/copper was changed and board
`04dc3e8a...` stays at 56 open nets / 460 edges. Next implement a tightly
scoped J3 VBUS POFV rule and atomically route both connector islands over an
outer-layer 0.50 mm trunk to C20/R35/U10; partial connector copper is forbidden.

## USB_VBUS_RAW ordinary-track wall bounded (2026-09-02)

Fresh live-ledger ranking selected the previously uncharacterized USB power
entry: `USB_VBUS_RAW` plus `USB_VBUS_CHG` carry 14 retained open edges. The new
atomic seven-land RAW harness uses the locked 0.50 mm `VBUS_CHG` width and
0.20 mm clearance. R35.1-to-C20.1 closes cleanly, but the first connector
branch stops at `J3.A9 NO_LEGAL_ESCAPE`. A separate package screen confirms
zero full-width F.Cu launches from J3.A4, A9, B4, or B9 at both 0.05 and
0.025 mm grids. The scratch partial adds four target-net segments, removes no
copper, and keeps real refilled parity DRC at 199/5/1, but remains three edges
open and is rejected. The authoritative PCB remains byte-identical at
`04dc3e8a...`, 56 open retained nets / 460 edges. Next derive a connector-local
F.Cu power-pour/neck transaction from the actual current and fab geometry,
then attach C20/R35/U10 atomically. Do not retry an ordinary 0.50 mm trace
launch, revive the retired 0.55/0.25 mm via premise, or weaken `VBUS_CHG`.

## NFC_5V_EN mixed-inner cases 12--15 bounded; wall parked (2026-09-02)

The fifth non-promoting iteration paired U2 endpoint site three with all four
TP10 sites on In2. Every endpoint reservation coexists, but each case rejects
all 1,870 ordinary transition sites and 7,218 direct/orthogonal leg
combinations. No candidate or partial copper was emitted; the authoritative
board remains byte-identical at `04dc3e8a...`, 56 open retained nets / 460
edges. Cases 0--15 are exhausted. The materially unchanged `NFC_5V_EN` wall is
now PARKED under the autonomy policy; do not continue into the remaining case
matrix without changed geometry or a broader coherent refloor. Freshly rank an
independent retained control/interface cluster next.

## NFC_5V_EN mixed-inner cases 8--11 bounded (2026-09-02)

The resumable atomic harness paired U2 site two with all four TP10 sites on
In2. Every endpoint reservation coexists, but each case rejects all 1,870
ordinary transition sites and 7,218 direct/orthogonal leg combinations. No
candidate or partial copper was emitted; the authoritative board stays
`04dc3e8a...`, 56 open retained nets / 460 edges, with accepted real refilled
parity DRC 199/5/1. Cases 0--11 are exhausted. This is unchanged-wall iteration
four; run the final bounded window at `--case-start 12`, then park the family
if it fails. Do not replay cases 0--11.

## NFC_5V_EN mixed-inner cases 4--7 bounded (2026-09-02)

The next non-overlapping window pairs U2 endpoint site one with TP10 sites
zero through three on In2. All four escape pairs coexist, but each exhausts
1,870 transition sites and 7,218 leg combinations without a complete
one-transition haul. No candidate or partial copper is emitted. Board
`04dc3e8a...` remains byte-identical at 56 open nets / 460 edges with real
refilled parity DRC 199/5/1. Cases 0--7 are exhausted; this is unchanged-wall
iteration three. Continue at `--case-start 8`; do not replay cases 0--7.

## NFC_5V_EN mixed-inner cases 0--3 bounded (2026-09-02)

The atomic harness now supports four endpoint sites, resumable case windows,
and one ordinary In2/In3 transition in the long haul. Cases 0--3 cover U2 site
zero against TP10 sites zero through three on In2. All four escape pairs
coexist, but each exhausts 1,870 transition sites and 7,218 leg combinations
without a join. The proven local branches are replayed only after a haul
witness, so no partial candidate is emitted. Board `04dc3e8a...` remains
byte-identical at 56 open nets / 460 edges with real refilled parity DRC
199/5/1. Continue at `--case-start 4`; do not replay cases 0--3.

## NFC_5V_EN four-land first family bounded (2026-09-02)

The live fitted tree contains U2.6, U13.2, R14.1, and TP10.1. The new atomic
harness screens both branch orders, both inner layers, and two sites at each
long-haul endpoint. The two local branches close; 12 of 16 cases reserve both
U2/TP10 escapes, but all direct, orthogonal, and 0.5 mm spine joins reject. No
partial candidate is emitted. Board `04dc3e8a...` remains byte-identical at
56 open nets / 460 edges with real refilled parity DRC 199/5/1. Next preserve
the local witnesses and broaden only the haul with more endpoint sites and one
bounded mixed-In2/In3 transition.

## WAKE_GATE_S two-transition R66 haul qualified; wall parked (2026-09-02)

The recovered atomic harness now permits two ordinary transitions in the
R66.1-to-R63.2 shared-hub haul. All eight endpoint sites in both layer orders
close that branch. With each R66 witness reserved, Q10.2 site zero still rejects
all 169 bounded planar joins, so no complete tree or partial candidate is
emitted. Board `04dc3e8a...` remains byte-identical at 56 open nets / 460 edges
and independent real refilled parity DRC remains 199/5/1. This is the fifth
non-promoting unchanged-wall iteration, so WAKE_GATE_S is parked. Next freshly
rank an independent retained cluster; revisit only after changed geometry or
through a broader coherent refloor transaction.

## WAKE_GATE_S one-transition shared-hub family bounded (2026-09-02)

The shared-hub harness now broadens only the R66.1-to-R63 haul through one
ordinary 0.60/0.30 mm In2/In3 transition via. Both layer orders and all eight
qualified R66 endpoint escapes were screened over a 1,763-site local lattice;
each case exhausted 5,193 direct/orthogonal leg pairs without reaching the
qualified hub. Q10 is therefore deliberately not attached and no partial
candidate is emitted. Board `04dc3e8a...` remains byte-identical at 56 open
nets / 460 edges. Next use the fifth and final unchanged-wall iteration for a
bounded two-transition R66-to-hub family; park WAKE_GATE_S if that also fails.

## WAKE_GATE_S explicit shared-hub planar family bounded (2026-09-02)

`route_wake_gate_s_tree_scratch.py` now uses the one qualified R63 via as an
explicit shared hub instead of asking the generic engine for a second barrel.
All eight R66.1 ordinary-via endpoint sites were screened on each signal inner
layer. Every escape is legal, but each rejects all 165 bounded planar joins to
the hub, so Q10 is deliberately not attached and no partial candidate is
emitted. Board `04dc3e8a...` remains byte-identical at 56 open nets / 460
edges. Next preserve the endpoint witnesses and add one bounded In2/In3
transition to the R66-to-hub haul, then attach Q10 and gate the entire tree.

## WAKE_GATE_S qualified-fanout full-tree replay bounded (2026-09-02)

`route_wake_gate_s_tree_scratch.py` now reserves the exact D-520 R63.2 B.Cu
fanout and 0.60/0.30 mm via before both branch orders. Either far branch closes
when first, but the generic two-pad engine tries to allocate a second R63 via
for the other branch and returns `NO_VIA_SITE`; the partial cases also fail
real parity DRC and are never emitted. Board `04dc3e8a...` remains byte-identical
at 56 open nets / 460 edges. Next use the qualified via as one explicit shared
hub, with distinct-layer joins from R66.1 and Q10.2, and accept only the whole
three-land tree.

## WAKE_GATE_S generic tree bounded; R63 fanout qualified (2026-09-02)

The previously uncharacterized retained Community Port wake-gate node has an
atomic two-order tree harness covering fitted R66.1, R63.2, and Q10.2. Both
generic orders stop on the B.Cu R63.2 ordinary-via launch with no partial
copper. A package-local 1,248-shape successor finds two legal fanouts; the
first runs from R63.2 through `(55.2,57.735)` to a 0.60/0.30 mm via at
`(55.2,57.985)` mm. Board `04dc3e8a...` remains byte-identical at 56 open
nets / 460 edges and real refilled parity DRC remains 199/5/1. Next reserve
this exact witness and screen both complete branch orders atomically.

## NFC_IRQ mixed-inner haul family bounded (2026-09-02)

`route_nfc_irq_scratch.py` now preserves the qualified U9.27 front-side fanout
and screens one ordinary In2/In3 transition across the full NFC-to-MCU interior.
All 16 U1 escape cases ran; the three coexisting In3 escapes each exhausted
1,452 transition sites and 5,994 legal direct/orthogonal leg combinations with
no complete link. No partial candidate was emitted. Board `04dc3e8a...` remains
byte-identical at 56 open retained nets / 460 edges. Park this unchanged haul
family; next reserve the qualified CC1101 GDO0 U7.15 fanout and screen its
complete U1.8-to-U7.15 inner-layer haul atomically.

## NFC_IRQ package fanout qualified; planar haul bounded (2026-09-02)

`screen_nfc_irq_u9_fanout.py` corrects the U9.27 layer assumption from the live
PCB and tests 60 package-specific front-side shapes. Twenty-three are legal;
the first clean real-DRC witness reaches an ordinary via at `(35.0,36.0)` mm.
`route_nfc_irq_scratch.py` then treats U1.11-to-U9.27 as one atomic link. Three
of 16 U1 escape cases coexist with the U9 witness, but none of 228 planar
direct/orthogonal/one-spine joins completes. No partial copper is emitted.
Board `04dc3e8a...` remains at 56 open nets / 460 edges with refilled parity
DRC 199/5/1. Next preserve both qualified endpoint escapes and screen one
bounded mixed-In2/In3 haul with a single ordinary transition via.

## WAKE_INT_N mixed-upper cases 48--63 bounded; wall parked (2026-09-02)

The fourth non-overlapping 16-case one-transition-via window preserves the
complete qualified lower tree and reserves both upper escapes in every case,
but all 22,560 transition sites and 49,968 leg combinations reject. No
candidate or partial copper is emitted; board `04dc3e8a...` remains at 56 open
nets / 460 edges with real refilled schematic-parity DRC 199/5/1. Cases 0--63
are exhausted. This is the fifth consecutive non-promoting unchanged-wall
iteration after D-513, so park this family under the autonomy policy. Revisit
only after changed surrounding geometry or through a broader coherent refloor
transaction. Next freshly rank an independent retained routing cluster.

## WAKE_INT_N mixed-upper cases 32--47 bounded (2026-09-02)

The resumable one-transition-via screen now covers cases 32--47. All preserve
the complete qualified lower tree and reserve both upper escapes, but reject
after 22,560 transition sites and 49,968 leg combinations. No candidate is
emitted; board `04dc3e8a...` remains at 56 open nets / 460 edges with real
refilled schematic-parity DRC 199/5/1. Cases 0--47 are exhausted. Continue at
`--case-start 48`; do not replay them.

## WAKE_INT_N mixed-upper cases 16--31 bounded (2026-09-02)

The resumable one-transition-via screen now covers cases 16--31. All preserve
the complete qualified lower tree and reserve both upper escapes, but reject
after 22,560 transition sites and 49,968 leg combinations. No candidate is
emitted; board `04dc3e8a...` remains at 56 open nets / 460 edges with real
refilled schematic-parity DRC 199/5/1. Cases 0--31 are exhausted. Continue at
`--case-start 32`; do not replay them.

## WAKE_INT_N mixed-upper cases 0--15 bounded (2026-09-02)

`route_wake_int_upper_staged_scratch.py` now defaults to a one-via In2/In3
upper join; `--single-layer` retains D-513 reproduction. The first 16 of 128
cases preserve the complete qualified lower tree and have coexisting upper
escapes. All reject after 22,560 transition sites and 49,968 leg combinations.
No partial candidate is emitted; board `04dc3e8a...` remains at 56 open nets /
460 edges with real refilled schematic-parity DRC 199/5/1. Continue at
`--case-start 16`; do not replay cases 0--15.

## WAKE_INT_N upper staged corridor family bounded (2026-09-02)

Recovered `route_wake_int_upper_staged_scratch.py` preserves the exact D-512
U3.1 fanout and replays both proven middle branches before attempting the final
U1.23-to-R3.1 branch. All 128 In2/In3 and 8-by-8 upper endpoint-site cases were
screened. Both ordinary 0.60/0.30 mm endpoint escapes coexist in 112 cases,
but every one rejects all 875 direct/orthogonal/perimeter/vertical/two-spine
corridors (98,000 joins total); 16 cases fail endpoint reservation. No partial
candidate is emitted. Authoritative board `04dc3e8a...` remains byte-identical
at 56 open retained nets / 460 edges and real refilled schematic-parity DRC
199/5/1. Next preserve the entire atomic tree and screen one bounded mixed-
In2/In3 upper haul with an ordinary layer-transition via; do not replay this
exhausted single-layer family.

## WAKE_INT_N U3 fanout and middle chain qualified (2026-09-02)

`screen_wake_int_u3_fanout.py` exhausts 14,355 package-local B.Cu
shoulder/ordinary-via shapes from U3.1 at 0.20 mm width/clearance and finds
nine legal fanouts. The first deterministic shape reaches an ordinary
0.60/0.30 mm via at `(53.75,83.00)` mm. It remains legal while the existing
two-pad framework completes both proven U2.1-to-Q10.3 and Q10.3-to-U1.23
branches in the same scratch transaction. No partial candidate is emitted.
Authoritative board `04dc3e8a...` remains byte-identical at 56 open retained
nets / 460 edges and real refilled schematic-parity DRC 199/5/1. Next preserve
this exact lower witness and broaden only U1.23-to-R3.1 before replaying the
entire five-land tree atomically.

## WAKE_INT_N atomic generic tree bounded (2026-09-02)

`route_wake_int_tree_scratch.py` and four explicit two-pad contracts now cover
all five fitted `/WAKE_INT_N` lands as one no-partial-promotion transaction.
Four bounded rotations put every branch first on pristine geometry. The
U2.1-to-Q10.3 and Q10.3-to-U1.23 branches close through ordinary inner-layer
fanouts, but pristine U3.1-to-U2.1 stops at `U3.1 NO_VIA_SITE` and pristine
U1.23-to-R3.1 stops at `NO_PATH`; the two rotations that first route the clean
middle branches also stop at U1/R3. No complete candidate exists, so real DRC
and promotion are deliberately not asserted. No accepted copper was removed or
wrong-net copper added in scratch, and authoritative board `04dc3e8a...`
remains byte-identical at 56 open retained nets / 460 edges. Next screen one
package-specific U3.1 perimeter fanout family while reserving the already-clean
U2/Q10/U1 middle chain; then broaden only the U1/R3 join if the launch coexists.

## Display-backlight coherent pair wall parked (2026-09-02)

The resumable `route_disp_bl_strap_tree_scratch.py` co-search has now screened
U1.16/TP2.1 fanout-pair indices 0--255 on both distinct short-branch inner-layer
assignments. The final 192--255 window rejects all 64 first joins per assignment
before R109 fanout or replay. No candidate or authoritative copper was emitted;
board `04dc3e8a...` remains 56/460. This materially unchanged wall has reached
the five-iteration budget and is PARKED. Next screen `/WAKE_INT_N` as an atomic
five-land shared-interrupt tree; do not resume at index 256 absent changed
geometry or a broader coherent refloor.

## Display-backlight first-witness join wall bounded (2026-09-02)

`route_disp_bl_strap_tree_scratch.py` now consumes the exact D-505 coherent
fanout witness as one atomic complete-tree transaction. The three F.Cu launches
reserve in both cases, but U1.16-to-TP2.1 cannot join on either In2 or In3 via
the direct path, both orthogonal elbows, or 77 local 0.25 mm one-spine lanes
(79 paths per layer). The TP2/R109 join and qualified U1/R108 replay are never
attempted after that failure, so no partial candidate is emitted. Board
`04dc3e8a...` remains 56 open retained nets / 460 edges. Next co-search the
qualified 21/34/11 fanout sets with branch-join feasibility; do not treat the
first coexistence-only witness as a route witness.

## Display-backlight strap coherent fanouts qualified (2026-09-02)

`screen_disp_bl_strap_fanouts.py` replaces the parked generic endpoint attempt
with an explicit three-land package-pocket reservation screen. It exhaustively
tests 252 perimeter shapes at each of U1.16, TP2.1, and R109.1 and finds 21,
34, and 11 legal ordinary 0.60/0.30 mm fanouts. All three endpoint pairs have
compatible reservations (714, 231, and 374 combinations), and the first
deterministic triple coexists at vias `(46.5,122.785)`,
`(41.472198,117.010499)`, and `(52.529031,112.910322)` mm. The authoritative
board remains byte-identical at `04dc3e8a...`, 56 open retained nets / 460
edges. Next reserve this exact triple, join the short branches on distinct
signal layers, and replay the already-qualified U1.16-to-R108.1 branch as one
complete-tree transaction under the full promotion gate.

## SX1262 DIO1 mixed-inner haul family bounded (2026-09-02)

`route_sx1262_dio1_btn_b_refloor_scratch.py` now preserves the D-503 atomic
boundary while screening one ordinary transition via between In2 and In3.
All 16 U8.13 layer/site cases again coexist with the qualified U2.20 launch.
Each case exhausts 3,021 transition sites and 11,520 direct/orthogonal leg
combinations: 48,336 sites and 184,320 combinations total, with no complete
haul. `BTN_B_N` replay is therefore never attempted and no partial candidate
is emitted. Board `04dc3e8a...` remains 56/460. Park this unchanged-geometry
DIO1 haul wall; next freshly screen an independent retained local cluster
outside the parked power, USB, NFC, audio, shared-bus, and U2-package walls.

## SX1262 DIO1 atomic refloor/haul family bounded (2026-09-02)

`route_sx1262_dio1_btn_b_refloor_scratch.py` implements the D-502 transaction
without touching authority: withdraw all 21 `BTN_B_N` objects, reserve the
qualified U2.20 fanout, route DIO1, then replay all four physical BTN_B lands.
Across eight U8.13 escape sites on each of In2/In3, both endpoint escapes
coexist in all 16 cases. All 1,702 horizontal/vertical/two-spine corridors per
case (27,232 total) are blocked, so BTN_B replay is deliberately not attempted
and no partial copper is emitted. Board `04dc3e8a...` remains 56/460. Next keep
the qualified atomic boundary and screen a bounded mixed-In2/In3 haul using an
intermediate ordinary transition via; do not repeat this single-layer family.

## SX1262 DIO1 U2 refloor boundary qualified (2026-09-02)

`screen_sx1262_dio1_u2_fanout.py` exhaustively tests 5,050 U2.20 B.Cu
perimeter/under-body doglegs. Unchanged geometry has zero legal ordinary
0.60/0.30 mm via fanouts at 0.20 mm width/clearance. A complete-net withdrawal
screen identifies a minimum one-net boundary: withdrawing only the accepted
`BTN_B_N` tree exposes a clean U2.20 path through `(56.75,88.975)` and
`(56.75,87.75)` to a via at `(56.0,87.75)` mm after eight cases. Real refilled
parity DRC adds only the expected scratch dangling via relative to the
withdrawn-board signature. No partial candidate is emitted; board `04dc3e8a...`
remains at 56 open retained nets / 460 edges. Next atomically withdraw/replay
the complete BTN_B tree while routing the qualified DIO1 fanout and full
U2.20-to-U8.13 haul; neither net may be promoted alone.

## CC1101 GDO0 U7 fanout qualified (2026-09-02)

`screen_cc1101_gdo0_u7_fanout.py` turns the generic `U7.15 NO_VIA_SITE`
result into a package-specific launch family. It exhaustively tests 429 B.Cu
west/east shoulder shapes and finds 105 legal ordinary 0.60/0.30 mm via
fanouts at 0.20 mm width/clearance. The first witness at `(18.5, 140.75)` mm
passes real refilled schematic-parity DRC at the accepted 199/5/1 baseline
plus one expected scratch dangling via. It is characterization-only and emits
no partial candidate. Next reserve a qualified U7.15 fanout and the U1.8
launch before screening the complete inner-layer haul atomically.

## BQ25185 shared B.Cu fanout family bounded (2026-09-02)

`screen_bq25185_status_shared_fanout.py` exhaustively qualifies 231 westward
0.20 mm B.Cu doglegs per adjacent U2 status land before considering pairs. The
recovered WIP's biased product-prefix cap was corrected. Neither U2.9 nor
U2.10 has a legal individual dogleg with an ordinary 0.60/0.30 mm via in this
family, so no pair/order or partial candidate exists. Board `be285abf...`
remains byte-identical at 57 open retained nets / 461 edges and real refilled
parity DRC remains 199/5/1. Next use a bounded local U2 status-neighborhood
refloor transaction to open two distinct launches; do not replay this B.Cu
fanout family on unchanged geometry.

## BQ25185 paired status fanout wall bounded (2026-09-02)

`route_bq25185_status_pair_staged_scratch.py` screens both adjacent U2 status
launches before either long haul, across 128 distinct-layer/site/order cases.
Each land can reserve an ordinary via alone, but no U2.9/U2.10 reservation pair
coexists; the second launch always reports `NO_VIA_SITE`. No pull-up join or
partial copper is emitted. Next use a shared package-fanout or bounded local
refloor transaction; do not replay the staged corridors on unchanged geometry.

## SX1262 RX-enable staged family bounded (2026-09-02)

The D-491 successor enumerates four ordinary endpoint sites on both inner
layers and 563 explicit horizontal, vertical, and two-spine corridors for
U3.19-to-R74.1. Twenty of 32 cases reserve both endpoints, but no corridor
joins; 12 fail endpoint coexistence. Atomic gating emits neither the partial
haul nor the otherwise-proven radio leg. Board `be285abf...` remains at 57
open retained nets / 461 edges and real refilled parity DRC remains 199/5/1.
Park this unchanged family and freshly rank an independent retained tree.

## SX1262 RX-enable generic family bounded (2026-09-02)

`route_sx1262_rxen_tree_scratch.py` atomically screens both branch orders for
fitted `/SX1262_RXEN` lands U3.19, R74.1, and U8.6. All are B.Cu lands. The
R74.1-to-U8.6 leg closes on In2 with seven add-only objects, but the independent
U3.19-to-R74.1 leg cannot join its two legal ordinary endpoint escapes on In2
or In3. The clean partial leg is discarded. Board `be285abf...` remains at 57
open retained nets / 461 edges and real refilled parity DRC remains 199/5/1.
Next broaden only the expander-to-pull-down haul with staged/perimeter
corridors, then replay the proven radio leg atomically.

## SX1262 reset package-land wall bounded (2026-09-02)

`route_sx1262_rst_tree_scratch.py` atomically screens both branch orders for
fitted `/SX1262_RST_N` lands U2.5, R13.1, and U8.15. Both orders stop cleanly
because R13.1 has no ordinary 0.60/0.30 mm escape to either In2 or In3. No
candidate or partial copper is emitted. Board `be285abf...` remains at 57 open
retained nets / 461 edges and independent real refilled parity DRC remains
199/5/1. Revisit only through an R13 fanout/refloor transaction or changed
geometry; next screen the independent `/SX1262_RXEN` control tree.

## IR receiver tree promoted (2026-09-02)

`route_ir_rx_tree_scratch.py` atomically screens both branch orders for fitted
`/IR_RX_GPIO44` lands U1.36, TP40.1, and U6.1. Both orders close through In2;
the promoted route adds 14 target-only objects and removes no accepted copper.
The complete tree has zero open edges, fitted board connectivity is 57 open
nets / 461 edges, and independent real refilled parity DRC remains 199/5/1.
Board `be285abf...`; manufacturing export remains premature.

## I2S speaker-data staged family bounded (2026-09-02)

`route_i2s_spk_dout_scratch.py` is the D-430 successor for the live fitted
`/I2S_SPK_DOUT` U1.34/U5.1 link. It enumerates four ordinary-via sites at each
endpoint on both In2 and In3, then screens 1,168 north/west perimeter,
two-spine, and three-spine corridors whenever both endpoints reserve. All 32
site/layer cases ran; eight reserve both endpoints, but no staged join exists.
No partial copper or candidate is emitted. The authoritative board remains
byte-identical at `044ebb60...`, 58 open retained nets / 463 edges, and an
independent real refilled schematic-parity DRC remains 199/5/1. Park this
unchanged audio-data haul wall and freshly rank an independent retained
control tree; manufacturing export remains premature.

## MK1 clock perimeter/three-spine family bounded (2026-09-02)

The paired-clock atomic harness now screens a genuinely broader long-haul
family after D-485: seven north-perimeter lanes, six west-perimeter lanes, the
165 established interior corridors, and 48 west three-spine doglegs per first
clock. Across all 32 qualified fanout/layer/clock/reservation combinations the
U1 and U5 endpoint escapes still reserve, but every first MCU-to-MK1 haul fails
all 226 corridors. No partial candidate or authoritative copper is emitted;
the board remains `044ebb60...` at 58/463. Park this unchanged clock-haul wall.
Next freshly screen the independent fitted `/I2S_MIC_DIN` data tree, then the
remaining audio-data family; do not replay another rectilinear clock corridor
without changed geometry or a broader refloor transaction.

## MCU-hub MK1 clock topology bounded (2026-09-02)

The complete paired-clock harness now implements the D-484 successor topology:
U1 is the hub, MK1 is the long branch, and U5 is attached as the short stub.
All 32 combinations reserve both U1/U5 endpoints, but the first MCU-to-MK1
branch still fails all 165 two-spine corridors on either clock/layer before the
stub is attempted. This proves hub reversal alone does not open the shared
long-haul wall. No partial copper or authoritative board change was emitted;
the board remains `044ebb60...` at 58/463. The next bounded alternative is a
three-spine or perimeter long-haul family, retaining the qualified MK1 fanouts.
The stale BOOT harness now refuses its already-connected D-469 target before
replaying and duplicating accepted vias.

## Complete MK1 clock-tree staged family bounded (2026-09-02)

`route_mk1_i2s_clock_trees_scratch.py` turns the qualified paired microphone
fanouts into one atomic complete-tree screen. It covers all four staggered MK1
layouts, both distinct I2/I3 clock assignments, both clock priorities, and both
amplifier/MCU branch priorities: 32 deterministic cases. Every U1 and U5 clock
endpoint reserves a legal ordinary via, and every microphone-to-amplifier leg
finds a staged corridor. The remaining microphone-hub-to-MCU leg fails all 165
two-spine corridors for whichever clock is attempted first, so no case reaches
the second clock and no scratch result is promotable. No partial copper is
emitted. The authoritative board remains `044ebb60...`; independent saved-refill
schematic-parity DRC is exactly 199/5/1 and connectivity remains 58/463. Do not
repeat this hub-and-two-spine topology. Next screen an MCU-hub tree with the
amplifier as a short branch, or a three-spine/perimeter haul from MK1 to U1.

## MK1 acoustic keepout correction promoted (2026-09-02)

The over-broad 5 x 7 mm `MIC_ACOUSTIC_KEEPOUT` was replaced by a conservative
2 x 2 mm bounding square around the locked footprint's 2.0 mm-diameter dashed
acoustic seal region and concentric 1.05 mm NPTH. Tracks, vias, and pours remain
forbidden on every governed layer inside the full seal region, while MK1.5/6
are no longer incorrectly inside it. A saved real refill retains parity DRC
199/5/1 and fitted connectivity 58/463; exact comparison finds no track, via,
or pad change. All four paired clock-fanout layouts now pass real DRC. Board
`044ebb60...` is promoted. Next extend those qualified fanouts into an atomic
complete BCLK/LRCLK tree screen with distinct staged inner corridors.

## MK1 clock-fanout rule-area wall bounded (2026-09-02)

`screen_mk1_i2s_clock_fanout.py` reserves `/I2S_LRCLK` and `/I2S_BCLK`
together using four staggered ordinary-via layouts east of rear microphone
lands MK1.5/MK1.6. All eight via sites are geometrically clear, but every
two-net candidate is correctly rejected by real refilled schematic-parity DRC:
the board-level 5 x 7 mm `MIC_ACOUSTIC_KEEPOUT` forbids each B.Cu launch while
covering the signal lands themselves. Each case reports exactly two
`items_not_allowed` errors plus the accepted 199/5/1 baseline and two expected
dangling scratch vias. The authoritative board remains byte-identical at
`f4411e57...`, 58 open retained nets / 463 edges. Do not retry another fanout
shape inside the unchanged rule area. Next, audit the rule-area polygon against
the locked acoustic-port keepout and footprint geometry, then transactionally
narrow or split only an over-broad rule area if that preserves the microphone
seal and passes the full board gate.

## I2S clock-pair generic family bounded (2026-09-02)

`route_i2s_clock_pair_scratch.py` atomically screens both fitted three-land
clock trees in eight meaningful clock/branch orders. Exact contracts cover
U1.32/U5.16/MK1.6 (`I2S_BCLK`) and U1.33/U5.14/MK1.5 (`I2S_LRCLK`). For either
clock, the U1-to-U5 branch reserves its endpoints but has no 0.20 mm In2/In3
join. Starting with the microphone branch proves a shared package wall: neither
rear MK1 clock land has a legal ordinary 0.60/0.30 mm via escape in the packed
microphone field. All orders emit zero copper and preserve real refilled
schematic-parity DRC at 199 footprint-library / five hole-clearance / one
solder-mask-bridge reports. Board `f4411e57...` remains at 58 open retained
nets / 463 edges. Next, reserve distinct BCLK/LRCLK rear fanouts as one coherent
MK1 package transaction before attaching U1 and U5; do not replay the unchanged
generic family.

## SX1262 chip-select tree family bounded (2026-09-02)

The retained `/SX1262_CS_N` tree now has exact reusable contracts for fitted
U1.10, R27.2, and U8.19. The bounded screening covers both branch orders and
two hub choices. U1 as hub is impossible because U1.10 has no reachable ordinary
0.60/0.30 mm via site. Using the pull-up as hub also fails independently:
U1.10-to-R27.2 has no legal 0.20 mm F.Cu corridor at either 0.05 or 0.025 mm
search grid, and R27.2 has no reachable ordinary via site for the radio haul.
Both orders emit zero copper and preserve real refilled schematic-parity DRC at
199 footprint-library / five hole-clearance / one solder-mask-bridge reports.
Board `f4411e57...` remains at 58 open retained nets / 463 edges. Park this
unchanged family; next freshly screen the independent retained I2S clock/data
cluster, beginning with the one-edge `/I2S_SPK_DOUT` successor topology only if
new endpoint geometry is available, otherwise `/I2S_BCLK` and `/I2S_LRCLK` as
one coherent clock pair.

## TCA4307 READY staged family bounded (2026-09-02)

`route_tca4307_ready_tree_scratch.py` reserves both READY endpoints once and
atomically screens 612 explicit two-spine inner-layer corridors before replaying
the local U16 branch. Both In2 endpoint vias reserve cleanly, but accepted
geometry blocks every four-leg join; In3 cannot reserve R46.2. The harness
emits no partial copper and retains real refilled schematic-parity DRC at 199
footprint-library / five hole-clearance / one solder-mask-bridge reports. Board
`f4411e57...` remains at 58 open retained nets / 463 edges. Park this unchanged
long-haul family and freshly rank an independent retained tree.

## TCA4307 READY status tree framework advanced (2026-09-02)

The fitted `/09_COMMUNITY_HEADER/TCA4307_READY` tree now has exact local and
long-haul contracts. U16.5-to-R46.2 routes cleanly in scratch with 7.378838 mm
of 0.20 mm B.Cu, reduces target connectivity from two to one open edge, and
retains real refilled schematic-parity DRC at 199 footprint-library / five
hole-clearance / one solder-mask-bridge reports. The independent 74 mm-class
R46.2-to-TP44.1 In2/In3 search exceeded its bounded window and was terminated.
No partial copper was promoted; board `f4411e57...` remains at 58 open retained
nets / 463 edges. Next, stage the test-point haul and replay both legs atomically.

## Community Port Accessory Detect tree promoted (2026-09-02)

The Demo-required `/09_COMMUNITY_HEADER/ACC_DETECT_N_HDR` tree now connects
`D5.6`, series resistor `R64.2`, test point `TP43.1`, and J5 contact 21 as one
fitted copper island. All six branch orders pass the atomic add-only harness.
The accepted route adds 20 F.Cu segments, removes no accepted copper, and adds
no wrong-net object. Independent zone-refilled schematic-parity KiCad DRC
remains exactly 199 footprint-library / five hole-clearance / one solder-mask-
bridge reports. Fitted connectivity improves 59 to 58 open retained nets and
466 to 463 open edges; ratsnest improves 495 to 492. D-269, D-186, the three
RGB replacement nets, XGPIO4/XGPIO5, the approved Demo NC contacts, and
production hardware remain intact. Next, freshly rank the retained accessory-
power control/status trees, beginning with `ACC_5V_BOOST_EN`; manufacturing
export remains premature.

## Physical power-switch enable tree promoted (2026-09-02)

The retained `Net-(SW9-A)` tree now connects `U12.12`, `R43.1`, `TP13.1`,
and physical slide switch `SW9.1`; the `R68.2` bypass remains DNP and is not
treated as a fitted endpoint. The bounded northern-perimeter harness closes the
previous 56 mm-class `U12.12`-to-`R43.1` wall, then atomically replays both
local branches. The accepted route adds 23 segments and four ordinary
0.60/0.30 mm vias, all on `Net-(SW9-A)`, with zero accepted-copper removal.

Independent zone-refilled schematic-parity KiCad DRC remains exactly 199
footprint-library / five hole-clearance / one solder-mask-bridge reports.
Fitted connectivity improves 60 to 59 open retained nets and 469 to 466 open
edges; ratsnest improves 498 to 495. D-269, D-186, all three RGB replacement
nets, XGPIO4/XGPIO5, approved Demo NC contacts, and production hardware remain
intact. Next, freshly rank another independent retained power or interface tree
outside the parked package-fanout walls; manufacturing export remains premature.

## Power-switch enable tree bounded (2026-09-02)

`Net-(SW9-A)` has four fitted lands (U12.12, R43.1, TP13.1, SW9.1); R68.2 is
the DNP alternate strap and is explicitly excluded by the new reusable leg
contracts. U12.12-to-TP13.1 closes on B.Cu. TP13.1-to-SW9.1 first refuses the
incorrect B.Cu-only assumption because SW9 is front-side, then closes through
two ordinary vias and In2. The remaining 56 mm-class U12.12-to-R43.1
endpoint-reserved inner-haul did not complete within 60 seconds. No partial
candidate or authoritative copper was emitted. Next, bound a staged-waypoint
or perimeter inner-haul for that long leg and then replay all three legs as
one atomic tree.

## Community Port wake/attention tree promoted (2026-09-02)

The required `/09_COMMUNITY_HEADER/WAKE_ATTN_N_HDR` tree now connects TVS land
`D5.4`, series resistor `R66.2`, and Community Port contact `J5.20` as one
island. Both atomic branch orders pass. The first B.Cu-only attempt was safely
refused before emitting copper because D5.4 is front-side; the corrected route
adds 15 F.Cu segments / 50.783108 mm at 0.20 mm, with no vias or accepted-copper
removal.

Independent zone-refilled schematic-parity KiCad DRC remains exactly 199
footprint-library / five hole-clearance / one solder-mask-bridge reports.
Fitted connectivity improves 61 to 60 open retained nets and 471 to 469 open
edges; ratsnest improves 500 to 498. Board SHA-256 is `c6959452...`. D-269,
D-186, all RGB replacements, XGPIO4/XGPIO5, approved Demo NC contacts, and
production hardware remain intact. Next, freshly screen the independent
`Net-(SW9-A)` power-enable tree; manufacturing export remains premature.

## TPS63020 PS/SYNC pull-down tree promoted (2026-09-02)

The fitted `Net-(U12-PS_SYNC)` configuration tree now connects `U12.13`,
pull-down `R42.2`, and test point `TP14.1` as one island. The recovered atomic
harness bounds both branch orders plus ordinary-via In2/In3 long-haul
alternatives and refuses partial or stale-target promotion. The accepted route
is add-only: 33 segments / 104.815272 mm of 0.20 mm B.Cu, with no vias and no
accepted-copper removal.

Independent zone-refilled schematic-parity KiCad DRC remains exactly 199
footprint-library / five hole-clearance / one solder-mask-bridge reports.
Fitted connectivity improves 62 to 61 open retained nets and 473 to 471 open
edges; ratsnest improves 502 to 500. Board SHA-256 is `135f3652...`. D-269,
D-186, all RGB replacements, XGPIO4/XGPIO5, approved Demo NC contacts, and
production hardware remain intact. Next, freshly rank another independent
retained tree outside documented unchanged walls; manufacturing export remains
premature.

## Display-backlight control strap wall (2026-09-02)

`route_disp_bl_strap_tree_scratch.py` atomically screens all six orders of the
four-land `DISP_BL_CTL_STRAP` tree. The long U1.16-to-R108.1 branch is legal
through the qualified ordinary-via inner-haul framework, adding eight scratch
objects. Neither short U1.16-to-TP2.1 nor TP2.1-to-R109.1 branch has a legal
route in the current geometry: both the ordinary In2/In3 endpoint-reservation
family and a separate F.Cu planar fallback return `NO_PATH`. No partial copper
is accepted or emitted. Park this unchanged add-only family; revisit only with
an explicit U1/TP2/R109 fanout transaction or changed surrounding geometry.
Freshly rank another independent retained tree next.

## TPS63020 power-good tree promoted (2026-09-02)

The fitted `Net-(U12-PG)` status tree now connects `U12.14`, pull-up `R41.2`,
and test point `TP8.1` as one island. A reusable atomic harness screens both
branch orders and refuses partial promotion. Both orders reproduce the same 16
add-only 0.20 mm B.Cu segments with no vias: 66.680740 mm for the IC branch and
36.121897 mm for the test-point branch. No accepted copper is removed.

Independent zone-refilled schematic-parity KiCad DRC remains exactly 199
footprint-library / five hole-clearance / one solder-mask-bridge reports.
Fitted connectivity improves 63 to 62 open retained nets and 475 to 473 open
edges; ratsnest improves 504 to 502. Board SHA-256 is `fa6ae0b4...`. D-269,
D-186, RGB, XGPIO4/XGPIO5, approved Demo NC contacts, and production hardware
remain intact. Next, freshly rank another independent retained status/control
tree outside documented unchanged walls; manufacturing export remains
premature.

## Parked USB connector-pair preflight hardening (2026-09-02)

A fresh exhaustive run on board `65bf079a...` reproduced D-434: P completes in
all 36 cases where it is first, while N returns `NO_LEGAL_ESCAPE` in all 72
orders because mechanically fixed J3.B7 has no legal 0.23 mm F.Cu launch.
`screen_usb_connector_pair.py` now checks that necessary package-land condition
before constructing any of the 72 router cases and deterministically returns
`REFUSED_FIXED_CONNECTOR_LAND` with zero cases. No board or production hardware
changed. Park this family until a justified connector-footprint or USB copper-
contract change; next freshly rank an independent retained net outside the
documented unchanged walls.

## Connected-target preflight hardening (2026-09-02)

The live routing ledger reports `/01_POWER_TREE/VBUS_PRESENT` as one connected
four-pad island with zero open edges.  Its legacy standalone harness could
still attempt 13 redundant copper objects and duplicate two existing via
locations; real DRC rejected that scratch result with two `holes_co_located`
reports.  `route_vbus_present_tree_scratch.py` now checks fitted connectivity
first and deterministically refuses an already-connected target without
constructing a router board or emitting a candidate.  The authoritative board
remains `65bf079a...`, 63 open retained nets / 475 edges.  Next screen the open
connector-side USB D+/D- pair under its differential-pair constraints.

## ACC_PWR_EN isolation-control tree wall (2026-09-02)

`route_acc_pwr_en_tree_scratch.py` atomically screens the retained U16.1,
R17.1, and U3.20 tree in both orders.  Hub selection at R17 is invalid: its
U16 branch takes an 81.841 mm B.Cu detour with five real clearance reports and
R17 has no ordinary-via site for the long haul.  The bounded alternative keeps
R17 as a local stub and reserves U16/U3 through vias, but neither In2 nor In3
admits the 0.20 mm join.  No candidate or partial copper is promoted.  Park
this add-only family pending a U16 package-fanout/corridor transaction; next
freshly rank an independent retained control tree.

## LED_K perimeter precondition (2026-09-02)

`screen_led_k_perimeter.py` first enumerates a required 0.30 mm-clear ordinary
escape/via from both same-net FPC lands to both signal inner layers. All four
J1.2/J1.3 × In2/In3 combinations have zero 0.60/0.30 mm via sites, so none of
the 576 bounded perimeter families can begin and no partial copper is emitted.
Do not retry ordinary vias or perimeter lanes. Revisit only through a bounded
connector-footprint breakout transaction that proves the LED-current contract;
meanwhile freshly rank an independent retained net.

## LED_K current-width wall (2026-09-02)

`route_led_k_tree_scratch.py` atomically screens J1.2/J1.3, U17.3, and R69.1.
The ordinary inner-haul framework correctly refuses the 0.30 mm current net.
A scratch 0.20 mm search widened to the required 0.30 mm final copper closes
the tree but fails three real `LED_BOOST` 0.30 mm-clearance checks; searching
at true clearance instead returns `NO_LEGAL_ESCAPE` at J1.2. No copper was
promoted. Next, reserve an explicit J1.2 F.Cu escape/via and screen a perimeter
inner-layer corridor before attaching the local B.Cu U17/R69 branch.

## BOOT recovery tree (2026-09-02)

`route_boot_tree_scratch.py` atomically gates both orders of the fitted U1.27,
R2.2, and duplicated SW1.1 recovery tree. The accepted route adds sixteen
0.20 mm tracks and five ordinary vias, closes all three fitted open edges,
removes no accepted copper, and preserves real refilled schematic-parity DRC
at 199/5/1. The east SW1 land uses its own F.Cu escape and joins on In2 because
accepted `SD_CS_N` separates the two switch lands on F.Cu. Next, screen the
independent four-land `LED_K` backlight-return tree.

## CC1101 chip-select tree (2026-09-02)

`route_cc1101_cs_tree_scratch.py` atomically screens both orders of the fitted
U1.7/R28.2/U7.19 tree using the qualified boxed-endpoint inner-haul framework.
The accepted result uses In2 for the pull-up leg and In3 for the radio leg:
eight add-only 0.20 mm tracks (49.438285 mm) and four ordinary vias. Both
orders close the tree with identical physical geometry, zero accepted-copper
removal, and real refilled schematic-parity DRC 199/5/1. Next, freshly screen
the fitted three-land `/02_MCU_CORE/BOOT_N` recovery tree.

## GPIO45 VDD_SPI strap promotion (2026-09-02)

The retained ESP32-S3 strap tree now connects U1.26, R111.1, and TP1.1 as one
fitted copper island. `route_gpio45_vddspi_strap_scratch.py` gates both branch
orders and promotes 23 add-only 0.20 mm segments (19 F.Cu, four In2.Cu) plus two
ordinary 0.60/0.30 mm vias. No accepted copper is removed and no wrong-net item
is added. The real refilled schematic-parity DRC signature remains exactly 199
footprint-library, five hole-clearance, and one solder-mask-bridge reports.
Fitted connectivity improves 67 to 66 open nets and 484 to 482 open edges;
ratsnest improves 513 to 511. Board SHA-256 is `e1d5d5d8...`, and the production
tree is byte-identical. Next, screen the independent `Net-(U11-TS_MR)` control
net using the U11.6 escape proven by D-448; do not reopen the parked U11.8/U11.9
package pocket.

## NFC U9 refloor preflight rejection (2026-09-02)

The atomic U9 harness now runs real schematic-parity DRC immediately after its
eight-segment withdrawal and fixed 0.5 mm-east move. That preflight rejects the
pose before routing: U9 overlaps C17's courtyard and shifted pads intersect
retained NFC copper (five shorts and one clearance failure). The requested
RFO1-first and VDD_D-lower-first screens also fail independently. All four
registered macro orders stop at the same precondition, so the fixed pose is
parked and cannot emit a candidate. The authoritative board remains
`360b8261...` at 67 open retained nets / 484 edges. Freshly rank an independent
retained net; revisit U9 only as a broader bounded U9/C17/passive refloor with a
complete impacted-copper replay boundary.

## NFC U9 atomic supply-refloor replay screen (2026-09-02)

`route_nfc_u9_supply_refloor_scratch.py` implements the fixed +0.5 mm-east U9
transaction with an exact eight-segment withdrawal boundary, allowlisted replay,
both new supply trees, fitted-connectivity checks, and real refilled parity DRC.
Signal-first is blocked at the shifted RFO1 launch after XIN/XOUT/RFO2 replay;
supply-first is blocked at the VDD_D lower branch after its upper branch. Both
partial candidates are rejected; neither removes copper outside the measured
boundary or adds copper on another net. The authoritative board remains
`360b8261...` at 67 open retained nets / 484 edges. Next enumerate the bounded
within-family orders at this fixed pose, beginning RFO1-first and VDD_D-lower-
first, without weakening the atomic promotion gate.

## NFC U9 supply-refloor pose/impact screen (2026-09-02)

`screen_nfc_u9_supply_refloor.py` tests 36 U9 poses and identifies five that
unlock legal 0.30 mm B.Cu launches for both VDD_D and VDD_A. The lowest-impact
pose translates U9 0.5 mm east without rotation. Its exact accepted-copper
replay boundary is eight pad-attached segments across XIN, XOUT, RFO1, RFO2,
AGDC, and VDD_AM. The deliberately unreplayed pose has 15 attributable real
parity-DRC reports, so no placement or copper is promoted. Board `360b8261...`
and fitted connectivity 67/484 remain unchanged. Next, implement the complete
atomic east-translation/replay plus both supply trees and accept it only if the
full-board preservation, connectivity, and refilled-DRC gate passes.

## NFC VDD_D/VDD_A package-land wall (2026-09-02)

`route_nfc_vdd_da_pair_scratch.py` atomically screens both adjacent ST25R3916
three-land decoupling trees across all eight net and branch orders. Every case
fails before copper emission: U9.3 (`NFC_VDD_D`) has no legal 0.30 mm B.Cu
escape at the qualified 0.20 mm package-land clearance because of U9.4, U9.2,
U9.1, and U9.33; U9.7 (`NFC_VDD_A`) is boxed by U9.8, U9.6, U9.33, and Y1.4.
All scratch runs retain the accepted real refilled schematic-parity DRC
signature of 199 footprint-library, five hole-clearance, and one solder-mask-
bridge report. No copper is promoted; board `360b8261...` and fitted
connectivity 67 open nets / 484 edges are unchanged. Park this planar family.
Next, bound a coherent U9 supply-fanout/nearby-passive placement transaction
covering both rails; do not replay branch ordering in the unchanged geometry.

## External-I2C buffer local-tree wall (2026-09-02)

`route_ext_i2c_buffer_pair_scratch.py` atomically screens both orders of the
four local `EXT_SDA_BUF`/`EXT_SCL_BUF` edges and rejects partial trees. Each
U16-to-pull-up B.Cu leg routes, but neither mixed-face series leg completes
through the qualified ordinary-via In2/In3 framework: U16.7 has no reachable
via site and U16.2 has no inner join after both endpoint reservations. The
SCL-first planar branch also passes the accepted `ACC_3V3_SW` via at
`(55.350,56.550)` by 0.2445 mm against the locked 0.250 mm rule. No copper is
promoted; board `360b8261...`, fitted connectivity 67 open nets / 484 edges,
and real refilled schematic-parity DRC 199/5/1 remain unchanged. Park this
add-only family pending an explicit U16 package-fanout/corridor transaction;
freshly rank another independent retained local cluster next.

## Radio/NFC package-fanout wall narrowed (2026-09-02)

`screen_package_fanout_transaction.py` replaces the generic endpoint search
with explicit package-aware 0.20 mm necks and ordinary 0.60/0.30 mm via sites
for the two remaining control-cluster endpoints.  Real KiCad scratch DRC proves
that neither is an add-only escape: U9.27's only outward route crosses the
accepted `NFC_AGDC` fanout, while U2.20's only inward route crosses the accepted
`BTN_B_N` fanout and violates clearance to the accepted `ACC_5V_SW_EN` via.
The authoritative board remains byte-identical at `360b8261...`; no HDI or
via-in-pad assumption was introduced.  Park `NFC_IRQ` and `SX1262_DIO1` until a
bounded accepted-copper fanout transaction is justified.  Next, rank an
independent retained local cluster; do not replay either unchanged add-only
escape family.

## Radio interrupt/control cluster advance (2026-09-02)

`SX1262_BUSY` is now complete from U1.12 to U8.14 with two ordinary
0.60/0.30 mm vias and a 0.20 mm In2 haul. The add-only route contributes eight
copper objects and 58.702654 mm, removes no accepted copper, and improves fitted
connectivity from 68 to 67 open nets / 485 to 484 open edges; ratsnest improves
514 to 513. Real refilled schematic-parity DRC remains at the accepted 199
footprint-library / 5 hole-clearance / 1 solder-mask-bridge signature.

The same qualified endpoint-reservation framework bounds the other two cluster
members without emitting copper: `NFC_IRQ` has no ordinary-via escape at U9.27
(blocked by U9.28/U9.26/U9.25/U9.33), and `SX1262_DIO1` has none at U2.20
(blocked by U2.21/U2.18/U2.19 and accepted track geometry). Board `360b8261...`;
production hardware is unchanged. Next, screen an explicit package-fanout
transaction for U9.27 and U2.20; do not replay the unchanged generic inner-haul
family.

## LTC4368 fault test-point branch promoted (2026-09-02)

The isolated `TP18.1` island is now joined to the retained
`LTC4368_FAULT_N` safety/status tree. The add-only route is nine 0.20 mm B.Cu
segments totaling 39.822537 mm and uses 0.300 mm clearance; it removes no
accepted copper. All five fitted lands are one island. Real refilled
schematic-parity DRC remains at the accepted 199 footprint-library / 5
hole-clearance / 1 solder-mask-bridge signature; fitted connectivity improves
69→68 open nets and 486→485 edges, and ratsnest improves 515→514. Board
`bbb69e92...`; the production tree is unchanged. Next, screen a coherent
retained sub-GHz/NFC interrupt/control cluster beginning with `NFC_IRQ`,
`SX1262_BUSY`, and `SX1262_DIO1`.

## LED_A explicit perimeter wall (2026-09-02)

`screen_led_a_perimeter.py` reserves J1.1's perpendicular F.Cu launch and
screens 60 deterministic orthogonal corridors at the locked 0.30 mm width and
0.20 mm clearance. The launch is legal in every case, but no corridor reaches
R71.2: 12 block on the lateral leg, 16 on the turn toward the ballast spine,
and 32 on the final approach. No partial or authoritative copper is emitted;
board `a819ade1...`, fitted connectivity 69 open nets / 486 edges, and real
refilled schematic-parity DRC 199/5/1 remain unchanged. Park LED_A until a
bounded J1/ballast placement transaction or changed surrounding geometry is
justified. Next, freshly rank an independent retained local cluster.

## LED_A planar distribution wall (2026-09-02)

The coherent five-land display-backlight anode transaction was screened in
both chain orders at 0.30 mm width and 0.20 mm clearance on F.Cu.  The four
ballast lands R73.2/R70.2/R72.2/R71.2 connect cleanly with fourteen candidate
segments, but the required R71.2-to-J1.1 feed reports `NO_PATH` whether it is
attempted first or last.  The full-board scratch DRC remains exactly 199
footprint-library / 5 hole-clearance / 1 solder-mask-bridge reports and no
partial copper is promoted.  The qualified inner-haul framework correctly
refuses this 0.30 mm current-distribution net as low-speed-signal-only, so that
is not an acceptable fallback.  Board `a819ade1...` remains byte-identical.
Next, reserve explicit F.Cu escapes at J1.1 and the ballast spine and screen a
bounded perimeter waypoint family; do not retry the generic planar chain or
weaken the current-path width.

## USB-C shield tree promoted (2026-09-02)

The five fitted `Net-(J3-SHIELD)` lands are now one connected copper island.
The atomic route attaches `R32.1` through two ordinary 0.60/0.30 mm vias, then
joins all four plated J3 shield stakes on B.Cu. It adds twelve 0.30 mm segments
and two vias, removes no accepted copper, and adds no wrong-net object. Two
clean scratch runs reproduce geometry digest `08990b0b...`. The independent
refilled schematic-parity KiCad DRC remains exactly at the accepted 199
footprint-library / 5 hole-clearance / 1 solder-mask-bridge signature. Fitted
opens improve 70→69 nets and 490→486 edges; ratsnest improves 519→515. Next,
screen the independent local five-land `LED_A` backlight-current distribution
tree as one coherent transaction.

## U2/button pull-up branch wall (2026-09-02)

The coherent `BTN_DOWN_N` / `BTN_LEFT_N` / `BTN_A_N` local-branch batch is not
promotable with either qualified generic topology. The atomic planar screen
fails its first required `U2.14` to `R5.2` branch with `NO_PATH`; the reserved-
via In2/In3 alternative fails earlier because `U2.14` has no legal ordinary
through-via site from B.Cu. Both screens emit zero copper, retain all three
nets at three fitted open edges, and preserve the real refilled schematic-
parity DRC signature of 199/5/1. Park this shared U2-side family; revisit it
only through a bounded U2 package fanout or local placement transaction.
Next, freshly rank an independent retained local cluster.

## NFC VDD_RF package-land wall (2026-09-02)

The adjacent four-land ST25R3916 `NFC_VDD_RF` tree is not promotable with the
proven local planar framework.  A lower-branch-first atomic screen fails before
emitting copper because U9.14 has no legal 0.20 mm B.Cu escape; stable blockers
are U9.15, U9.13, exposed pad U9.33, and U9.10.  Upper/cap-spine generic searches
also exceed the bounded local-search window, so branch order cannot repair the
lower-land precondition.  Real refilled schematic-parity DRC remains 199/5/1,
the target remains three open edges, and board `97d60cde...` is unchanged.
Park the unchanged planar family.  Next, freshly rank an independent retained
local cluster; revisit VDD_RF only with an explicit package-fanout or bounded
local U9/passive placement transaction.

## NFC VDD_AM decoupling-tree promotion (2026-09-02)

The retained ST25R3916 `NFC_VDD_AM` rail now connects U9.11, C51.1, and
C52.1 as one fitted island. The atomic transaction adds 18 B.Cu-only 0.30 mm
segments (60.878940 mm), no vias, removes no accepted copper, and reproduces
a clean result in both branch orders. Real refilled schematic-parity DRC
remains at the accepted 199 footprint-library / 5 hole-clearance / 1
solder-mask-bridge signature. Fitted opens improve 71 to 70 nets and 492 to
490 edges; ratsnest improves 521 to 519. Board SHA-256 is `97d60cde...`.
Next, screen the adjacent four-land `NFC_VDD_RF` supply tree as one coherent
local transaction while preserving all accepted NFC signal/tuning copper.

## U11 adjacent-branch reservation screen (2026-09-02)

`screen_u11_iset_escape_transaction.py` exhausts both branch orders and all
eight 2 mm directional targets for U11.6 (`TS_MR`) and U11.9 (`STAT1`) before
attempting U11.8 (`ISET`): 128 scratch-only cases at 0.20 mm width/clearance on
B.Cu. U11.6 reserves successfully in all 64 TS-first cases. U11.9 has no legal
escape in all 64 STAT1-first cases and after every U11.6 reservation, so zero
case reaches ISET and zero candidate is emitted. The package pocket is parked;
do not retry branch ordering in place. The authoritative board remains
`7a764bac...`. Next, freshly rank an independent retained local net/cluster.

## ISET package-land wall and local-route guard (2026-09-02)

The 5.683 mm `/01_POWER_TREE/ISET` net remains open: U11.8 has no legal
0.20 mm B.Cu escape between U11.6, U11.9, accepted track geometry, and the
board edge. No copper was emitted. A fallback attempt against already-connected
`ILIM_VSET` exposed a duplicate-copper false promotion; the shared local
two-pad gate now requires fitted open-edge reduction before candidate output
or promotion. Regression rejects `ILIM_VSET` at 0→0 and ISET at 1→1. The
authoritative board remains `7a764bac...` and real refilled schematic-parity
DRC remains 199/5/1. Next, reserve the adjacent U11.6/U11.9 branches before a
bounded U11.8 escape attempt; park the pocket if that family is empty.

## NFC AGDC decoupling-tree promotion (2026-09-02)

The fitted C53.1/U9.24/C54.1 tree is complete with 17 add-only 0.30 mm B.Cu
segments (40.626806 mm), no vias, and no accepted-copper removal. Both branch
orders reproduce the same clean geometry. Refilled schematic-parity DRC stays
at 199/5/1; fitted connectivity improves to 71 open nets / 492 open edges and
ratsnest 521. Board SHA-256 is `7a764bac...`. Next, screen the independent
5.683 mm `ISET` charger-programming net; the shorter `ACC_5V_LX` wall remains
parked for its power-core refloor transaction.

## ACC_5V_BOOST_EN planar-tree screen (2026-09-02)

`route_acc_5v_boost_en_tree_scratch.py` atomically screens all six launch
orders for the required U3.16/R102.1/TP30.1/U21.2 boost-enable tree. Every
order closes all three fitted open edges on B.Cu, but real refilled
schematic-parity KiCad DRC rejects every candidate at the same four accepted
accessory-rail vias. Actual clearances are 0.2254--0.2352 mm against the locked
0.250 mm rule. Replaying with a conservative 0.275 mm router search clearance
does not change those four exact crossings, so order and generic planar search
margin are not the lever. No copper is promoted; the authoritative board
remains `86cff98b...` with fitted connectivity 73 open nets / 496 edges and
the accepted 199/5/1 DRC signature. Next, reserve U3.16 and U21.2 escapes and
screen an In2/In3 control haul before attaching R102.1 and TP30.1; do not retry
the unchanged planar family.

## ACC_5V_ILIM route (2026-09-02)

The retained U22 current-limit programming net is promoted from U22.4 to
R101.1 as seven add-only 0.20 mm B.Cu segments (42.417480 mm), with no vias and
no accepted-copper removal. Two clean candidates reproduce identical physical
geometry. The authoritative refilled schematic-parity DRC remains 199/5/1;
the fitted ledger improves from 74 to 73 open nets and 497 to 496 open edges.
Board SHA-256 is `86cff98b...`. Route or bound `ACC_5V_BOOST_EN` next while
preserving the accepted accessory-power core and independent D-186 controls.

## ACC_PWR_EN east-perimeter inner screen (2026-09-02)

The recovered D-440 successor bounds five explicit east-side inner waypoints
from X=64 through 68 mm across both signal inner layers and the first four
reserved via sites at each endpoint.  An initial generic grid-search version
timed out in all 160 cases and was rejected as inconclusive.  The retained
harness instead checks each fixed orthogonal segment directly against exact
router obstacle geometry before emitting it.

All 160 deterministic cases reserve ordinary 0.60/0.30 mm U16.1 and U3.20 B.Cu
escapes, but the first inner leg is blocked in every case.  No join copper is
emitted or promoted.  The authoritative board remains `2830082d...`, target
connectivity remains two open edges, and real refilled schematic-parity DRC
remains 199/5/1.  Park this materially unchanged via-to-east orthogonal family;
freshly rank an independent retained net or coherent local cluster next.

## ACC_PWR_EN reserved-site inner screen (2026-09-02)

The D-439 successor reserves ordinary 0.60/0.30 mm vias from U16.1 and U3.20,
then screens the first four independently ranked sites per endpoint on both
In2 and In3. All 32 atomic cases expose both B.Cu package escapes, but none has
a legal 0.20 mm inner join inside the qualified local-haul envelope. The target
remains at two open edges; real refilled schematic-parity DRC remains 199/5/1;
no accepted copper is removed and no candidate is promoted. Next, screen a
bounded outer-perimeter inner waypoint family rather than replaying either
the generic planar tree or these local site pairs.

## ACC_PWR_EN planar-tree screen (2026-09-02)

`route_acc_pwr_en_tree_scratch.py` atomically screens the required R17.1,
U16.1, and U3.20 accessory-isolation enable tree and rejects partial routes.
The generic 0.20 mm B.Cu topology is not viable: R17.1→U16.1 takes an 85.344 mm
detour with three real accessory-rail clearance violations, and U16.1→U3.20
has no legal 0.20 mm corridor at 0.050 or 0.025 mm grid. Only one of two fitted
edges closes. No candidate is promoted and the authoritative board remains
`2830082d...`. Next, reserve escapes at U16.1/U3.20 and join them on In2/In3
before attaching R17.1; do not retry the generic planar tree.

## Retained XGPIO4/XGPIO5 header-pair promotion (2026-09-02)

The D-437 successor constrains the XGPIO5 header leg through an explicit
`(62.500,30.500)` mm waypoint, clear of both accepted accessory-power barrels.
Two clean XGPIO5-first candidates have identical physical copper geometry. The
promoted atomic pair adds 21 F.Cu segments and no vias: nine segments / 24.844979
mm on XGPIO4 and 12 segments / 20.817576 mm on XGPIO5. Both three-land trees are
connected, no accepted copper is removed, and real refilled schematic-parity
DRC remains exactly 199 footprint-library, five inherited hole-clearance, and
one inherited solder-mask-bridge reports. Fitted opens improve 76→74 nets and
501→497 edges; ratsnest improves 530→526. Board hash is `2830082d...` and
`hardware/beta-v2/` remains untouched.

## Retained XGPIO4/XGPIO5 header-pair screen (2026-09-02)

`route_xgpio45_header_pair_scratch.py` atomically routes and gates the fitted
R55/D4/J5.13 and R56/D4/J5.14 trees without touching their accepted internal
U3 legs. Both launch orders close all four edges, but real schematic-parity DRC
rejects them. With 0.20 mm fine-pad clearance and a conservative 0.275 mm track
search, XGPIO5-first leaves one stable violation: 0.2334 mm from its F.Cu
segment to the accepted `ACC_5V_RAW` via at `(61.375,34.300)`, below the locked
0.250 mm requirement. No copper was promoted. Next, explicitly shape XGPIO5
around that via and replay the complete pair through the same gate.

## Connector-side USB N perimeter enumeration (2026-09-02)

`enumerate_usb_connector_n_fanouts.py` exhaustively checks all four cardinal
and four diagonal F.Cu launch families at both 0.050 and 0.025 mm grids for
J3.A7, J3.B7, and U10.1. J3.A7 and U10.1 expose legal launches at both grids;
J3.B7 exposes zero. Its stable blockers are adjacent J3.A6, the board edge,
J3.A5, and accepted track geometry. The wall is therefore the reversible
connector land pocket, not a downstream pair-join ordering problem.

No copper or placement changed and the authoritative board remains
`2afa51d9...`. Next, bound a local J3/U10 placement transaction that preserves
J3's locked mechanical position and atomically replays every displaced U10
branch; do not weaken the F.Cu-only, 0.23 mm, zero-via USB contract.

## Connector-side USB planar-tree screen (2026-09-02)

`screen_usb_connector_pair.py` treats the reversible USB-C lands and U10 ESD
inputs as two complete three-pad trees. It exhaustively tests both pair orders
and every node-attachment order: 72 atomic cases at the locked 0.23 mm width,
0.20 mm clearance, F.Cu-only, zero-via USB contract.

The P tree completes in all 36 cases where it is attempted first. The N tree
reports `NO_LEGAL_ESCAPE` in every case, including all 36 attempts made before
P adds copper. No complete pair exists in this planar family. The authoritative
board remains byte-identical at `2afa51d9...`; no copper, placement, rule, or
production-hardware change was made.

Next, pre-reserve distinct F.Cu perimeter fanouts for J3.A7, J3.B7, and U10.1
before joining the N tree. If those three launches cannot coexist, bound a
local J3/U10 placement transaction without weakening the USB layer/via
contract. Manufacturing export remains premature and no owner decision is
open.

## V3V3 feedback-tree promotion (2026-09-02)

The retained TPS63020 feedback net is complete across U12.3, R39.2, and
R40.1. A direct B.Cu divider route was blocked, and the first In2 divider
candidate missed a retained D-269 BPP barrel clearance by 0.0575 mm. The
accepted feedback-specific topology instead roots both branches at U12.3:
R40.1 uses In2, R39.2 uses In3, and the branches share one ordinary U12-side
through-via. The final transaction adds ten 0.20 mm tracks and three
0.60/0.30 mm vias, with no accepted-copper removal.

The authoritative refilled schematic-parity DRC remains exactly 199
footprint-library, five inherited hole-clearance, and one inherited
solder-mask-bridge reports. Fitted open nets improve 77 to 76, open edges 503
to 501, and raw ratsnest 532 to 530. Board hash is `2afa51d9...`;
`hardware/beta-v2/` remains untouched. Next, screen connector-side USB D+/D−
as a coherent differential pair. Manufacturing export remains premature and
no owner decision is open.

## U12/L1 buck-boost switch-pair promotion (2026-09-02)

Both retained TPS63020 switch nodes are complete across the paired U12 lands
and L1. The deterministic atomic transaction adds nine B.Cu objects: short
0.20 mm VSON land joins that flare immediately into 0.40 mm switch trunks.
There are no vias and no switching tracks on inner layers. The two completed
paths measure 15.335 mm and 3.977 mm and close four fitted open edges.

The authoritative refilled schematic-parity DRC remains exactly 199 footprint-
library, five inherited hole-clearance, and one inherited solder-mask-bridge
reports. No accepted copper is removed. Fitted open nets improve 79 to 77,
open edges 507 to 503, and raw ratsnest 536 to 532. Board hash is
`3c5d425f...`; `hardware/beta-v2/` remains untouched. Next, screen the local
three-land `V3V3_FB` feedback tree while preserving the completed switch-loop
geometry. Manufacturing export remains premature and no owner decision is
open.

## VBUS-present local-tree promotion (2026-09-02)

`/01_POWER_TREE/VBUS_PRESENT` is complete across C68.1, R105.1, R104.2, and
TP31.1. The deterministic transaction reserves TP31 first with a two-via In3
hop, then closes the three short passive branches on B.Cu. It adds 13 target-net
objects at 0.20 mm, removes no accepted copper, and adds no wrong-net geometry.

The authoritative refilled schematic-parity DRC retains exactly 199 footprint-
library, five inherited hole-clearance, and one inherited solder-mask-bridge
reports. Fitted open nets improve 80 to 79, open edges 510 to 507, and raw
ratsnest 539 to 536. Board hash is `f8d555d4...`; `hardware/beta-v2/` remains
untouched. Next, screen the short L1/U12 buck-boost switching cluster as an
atomic power-aware transaction. Manufacturing export remains premature and no
owner decision is open.

## SPI-A paired J1 fanout wall (2026-09-02)

`screen_spi_a_j1_pair.py` implements the D-427 successor: it reserves distinct
ordinary 0.60/0.30 mm through-via fanouts for adjacent display pads J1.36
(`/SPI_A_SCK`) and J1.34 (`/SPI_A_MOSI`) before either net can claim an inner
haul. It screens the first four ranked escape sites for each pad with both
In2/In3 assignments, for 32 atomic cases total.

No complete pair exists in this bounded family. Eleven cases fail while
reserving the two J1 barrels; of the 21 cases that reserve both, 16 fail the
SCK join to U1.20 and five fail the MOSI join to U1.19. Zero case completes
both three-pad trees, so no partial copper is promoted. The harness is retained
as deterministic wall evidence and the authoritative PCB remains byte-identical
at `7e20e227...`.

The adjacent J1 paired-fanout wall is now parked. Next, promote the independently
complete `/SPI_A_SCK` tree using the already-proven clock-first transaction,
but only after a fresh authoritative refilled schematic-parity DRC,
connectivity/ledger comparison, accepted-copper preservation check, D-269 and
D-186 invariants, and production-tree hash check. `/SPI_A_MOSI` remains a later
critical-path wall; manufacturing export remains premature and no owner
decision is open.

## Audio/radio long-haul screen (2026-09-02)

The generic reserved-escape framework now defines `/I2S_SPK_DOUT` and
`/CC1101_GDO0`. The 33.605 mm speaker-data link reserves ordinary 0.60/0.30 mm
vias from both F.Cu endpoints, but neither In2 nor In3 joins at 0.20 mm; a
same-face search also exceeded the bounded 90-second screen. The 40.033 mm
CC1101 link fails earlier because U7.15 has no reachable legal ordinary via
site from B.Cu. Both runs leave the board byte-identical and refilled parity
DRC at 199/5/1. Do not retry either unchanged topology. Next, rank a short
independent local retained cluster. No owner decision is open.

## SPI-A MISO promotion (2026-09-02)

The fitted MISO topology is U1.21 to microSD J2.7 only. R112 remains DNP, so
the display SDO provision is intentionally excluded and cannot contend with
microSD reads. A generic F.Cu screen reproduced `NO_PATH`; the qualified
endpoint-reservation framework then closed the net with three 0.20 mm F.Cu
segments, three 0.20 mm In2.Cu segments, and two ordinary 0.60/0.30 mm vias.
The route is 28.739064 mm and removes no accepted copper.

The authoritative refilled schematic-parity DRC remains exactly 199 footprint-
library, five inherited hole-clearance, and one inherited solder-mask-bridge
reports. Fitted open nets improve 82 to 81, open edges 513 to 512, and raw
ratsnest 542 to 541. `hardware/beta-v2/` is unchanged and the authoritative
PCB SHA-256 is `7e20e227...`.

Next, screen `/SPI_A_SCK` and `/SPI_A_MOSI` as one bus-aware bounded pair; they
own four remaining fitted open edges. Manufacturing export remains premature
and no owner decision is open.

## Native B endpoint-reservation promotion (2026-09-02)

The D-424 generic F.Cu wall is closed with the already-qualified low-speed
inner-haul framework. U1.24 and R62.1 each use a short 0.20 mm F.Cu escape and
ordinary 0.60/0.30 mm through-via; four 0.20 mm In2.Cu segments join the via
anchors. The complete route is 20.436636 mm, six segments plus two vias, and
adds copper only on `/NATIVE_B`.

The authoritative refilled schematic-parity DRC retains exactly 199 footprint-
library, five inherited hole-clearance, and one inherited solder-mask-bridge
reports. The fitted ledger proves both pads are one island; fitted open nets
improve 83 to 82, open edges 514 to 513, and raw ratsnest 543 to 542. No
accepted copper was removed, `hardware/beta-v2/` is byte-identical, and the
authoritative PCB SHA-256 is `b92701c2...`.

Next, freshly screen `/SPI_A_MISO` as a bus-aware transaction while preserving
the accepted SD/display copper. The accessory-boost, NFC-input, ISET, and USB
walls remain parked; manufacturing export is premature and no owner decision
is open.

## Native GPIO internal-pair screen and Native A promotion (2026-09-02)

A fresh fitted ledger ranked `/NATIVE_A` and `/NATIVE_B` as the shortest
unparked coherent pair of Demo-required internal signal legs. The atomic
`route_native_gpio_pair_scratch.py` harness screens both launch orders. Both
orders produce the same result: Native A closes, while Native B reports
`NO_PATH` at both 0.050 and 0.025 mm grid resolution even when attempted first.

The independent, order-invariant Native A result is promoted from U1.31 to
R61.1: 11 add-only 0.20 mm F.Cu segments, 20.149286 mm, and no vias. The
authoritative refilled schematic-parity KiCad DRC remains exactly 199
footprint-library, five inherited hole-clearance, and one inherited solder-
mask-bridge reports. Fitted open nets improve 84 to 83, fitted open edges 515
to 514, and raw ratsnest 544 to 543. No accepted copper was removed; retained
battery/accessory safety, RGB, XGPIO4/XGPIO5, NFC, and production hardware are
unchanged. Board SHA-256 is `5d5a45c5...`.

Next, screen an explicit endpoint-escape/perimeter corridor for `/NATIVE_B`;
do not repeat the disproven generic same-face path. Manufacturing export
remains premature and no owner decision is open.

## NFC analog-supply legal-via enumeration (2026-09-02)

`enumerate_nfc_supply_corridors.py` applies the D-422 westward U9.7 launch seed
to the accepted board at 0.025 mm resolution and searches for reachable
0.60/0.30 mm through-via sites.  The barrel is checked against B.Cu and In3,
the 0.25 mm hole-clearance floor is enforced, and sites are then filtered
outside a conservative envelope around every accepted `NFC_XIN`/`NFC_XOUT`
track (via radius plus 0.20 mm clearance).

The package side has **zero reachable legal via sites before the oscillator
filter is even applied**.  This is not an inner-layer-capacity wall: C47.1 and
C48.1 expose 204 and 217 legal landing sites respectively.  It sharpens the
D-422 result: its package-local analog barrel was itself non-promotable, and
moving only the inner return cannot repair the transaction.  The authoritative
PCB stays byte-identical at `37718bc7...`; no copper, placement, or rule changed.

This materially unchanged U9.7 west-neck/via family is parked.  Next, select
the highest-ranked independent retained net or small functional cluster from a
fresh fitted ledger.  Revisit the analog supply only with a materially
different package-fanout direction or a bounded local placement transaction;
do not retry westward barrel placement or disturb accepted oscillator copper.

## NFC supply explicit inner-fanout screen (2026-09-02)

The first D-421 follow-on used short westward 0.30 mm B.Cu necks from U9.3 and
U9.7, independent 0.60/0.30 mm through-vias, an In2 digital-supply tree, and an
In3 analog-supply tree to the two decouplers on each rail. This establishes a
concrete non-planar topology rather than repeating the generic B.Cu router.

The candidate is rejected. Real refilled schematic-parity DRC adds two shorts
between `NFC_VDD_A` and the accepted `NFC_XIN` arm, four clearances, one track
crossing, and one hole-clearance report above the accepted 199/5/1 signature.
The digital west-fanout was not the limiting geometry; the analog inner return
entered the completed oscillator envelope. No candidate copper or placement
was retained, and the authoritative PCB remains `37718bc7...`.

Next, enumerate U9.7 analog via sites and In2/In3 corridors outside the entire
`NFC_XIN`/`NFC_XOUT` geometry, then replay both three-land supply trees as one
transaction. Preserve the accepted oscillator and all other NFC copper; do not
repeat the rejected straight analog return through the crystal envelope.

## NFC digital/analog supply launch wall (2026-09-02)

`route_nfc_supply_pair_scratch.py` adds an atomic framework for the two local
three-land `NFC_VDD_D` and `NFC_VDD_A` decoupling trees. Both upper-first and
lower-first orders were screened at 0.30 mm supply width with the existing
0.20 mm UFQFPN escape floor. `U9.3` and `U9.7` both return
`NO_LEGAL_ESCAPE`; all eight arm attempts stop before adding copper.

Both scratch boards reproduce zero target-net geometry and the accepted real
refilled schematic-parity KiCad DRC signature of 199 footprint-library, five
inherited hole-clearance, and one inherited solder-mask-bridge reports. The
authoritative PCB remains byte-identical at `37718bc7...`; accepted NFC signal
copper and `hardware/beta-v2/` are unchanged. Next, screen explicit outward
U9.3/U9.7 fanouts to separate package-local via sites, then close each pair of
decouplers on an inner layer. Do not repeat the generic B.Cu launch family.

## Accessory 5 V raw In3 transition wall (2026-09-02)

`screen_acc_5v_raw_in3_transition.py` bounds the D-419 non-planar alternative:
six courtyard-local U21.6 raw-via sites crossed with two In3 approaches to the
accepted raw-tree via, while the proven generic `ACC_5V_LX` route stays on
B.Cu. All 12 cases fail the real refilled schematic-parity DRC in two clean
runs. The best site, `(56.20,39.40)` mm, still shorts the 0.25 mm U21.6 neck
and 0.90/0.40 mm raw transition barrel to the LX launch; the LX return also
misses the retained raw-tree via by 0.225 mm against the required 0.250 mm.
Moving the transition south only adds conflicts.

No PCB, placement, rule, or accepted copper was promoted; the authoritative
board remains byte-identical at `37718bc7...`. This is the fifth consecutive
non-promoting increment on the materially unchanged boost-core wall, so it is
now **PARKED** under the autonomy policy. Revisit only after surrounding
geometry changes or as part of a justified broader refloor. Next, advance the
independent local NFC supply/decoupling cluster, beginning with a coherent
screen of `NFC_VDD_D` and `NFC_VDD_A`; preserve all accepted NFC signal copper.

## Accessory 5 V R99/raw-neck boundary (2026-09-02)

`screen_acc_5v_raw_neck_refloor.py` tests 16 LX-first combinations: four R99
offsets and four explicit B.Cu raw necks. A 0.5 mm east R99 move is the only
minimum tested placement that removes the L4/R99 courtyard overlap without the
via-in-courtyard and dangling-copper regressions of larger moves. Every LX
route closes. No raw neck passes: north paths collide with retained
BQ25185/ILIM copper; south paths remove crossing reports but still intersect
LX and retain a 0.225 mm versus 0.250 mm raw-clearance miss. KiCad can label a
coincident scratch collision as short versus crossing across runs, while these
engineering predicates reproduce.

No placement or copper is promoted and the board stays byte-identical at
`37718bc7...`. The next bounded transaction should fix R99 at +0.5 mm and
coordinately reserve separate LX/raw south corridors before atomically
replaying FB, enable, input, and GND. Do not retry north necks or larger R99
moves.

## Accessory 5 V power-core replay bound (2026-09-02)

`screen_acc_5v_power_core_refloor.py` advances the U21/L4 refloor from a launch
probe to a complete two-net power-core transaction. It withdraws the 19
accepted `ACC_5V_RAW` objects in scratch, rotates U21 and L4 180 degrees, routes
`ACC_5V_LX` first, then rebuilds the five-endpoint raw-output tree. LX closes in
6.213 mm and the raw tree closes all endpoints. Reversing that order re-boxes
U21.5, so LX-first is now a fixed transaction constraint.

The candidate is rejected, not promoted. The generic inner-layer raw tree adds
one clearance and one track-crossing violation; the placement produces one
courtyard overlap, package-neck width reports, and three additional
solder-mask-bridge reports. The next screen must keep LX first, replay the raw
tree with topology-specific B.Cu geometry while preserving its accepted
C65/R99/C66/TP28/U22 structure where possible, and explicitly clear the U21/L4
courtyard interaction. Only then should FB, enable, input, and GND be replayed
as the remaining half of the six-branch atomic transaction. The authoritative
PCB remains byte-identical at `37718bc7...`.

## Accessory 5 V switch-node refloor bound (2026-09-02)

`screen_acc_5v_lx_refloor.py` closes the first coordinated placement question.
Moving `C65` 1.0 mm east does not open `U21.5`; the launch remains boxed by the
adjacent TPS61023 lands. Rotating `U21` 180 degrees in place does open the
launch. Rotating both `U21` and `L4` 180 degrees reduces the deterministic B.Cu
route from 13.593 mm to 6.255 mm, versus a 3.782 mm pad-to-pad displacement.

This is characterization, not promotable geometry. A `U21` rotation changes
the physical land positions of all six pins, so the next transaction must
withdraw and replay the complete fitted `ACC_5V_FB`, `ACC_5V_BOOST_EN`,
`BQ25185_SYS`, GND, `ACC_5V_RAW`, and `ACC_5V_LX` branches atomically. Preserve
the accepted `ACC_5V_RAW` tree and safe-low enable; minimize the switch loop;
promote only if the full refilled schematic-parity gate and fitted ledger pass.
The authoritative board remains byte-identical at `37718bc7...`.

## Accessory 5 V switch-node wall (2026-09-02)

`ACC_5V_LX` is a fitted two-pad switch node from `U21.5` to `L4.2`, spanning
4.020 mm. The local routing framework now pins its power-specific contract:
B.Cu only, 0.40 mm trunk width, 0.20 mm clearance, and an explicitly reported
0.20 mm U21 package-escape floor. An ordinary 0.40 mm launch returns
`NO_LEGAL_ESCAPE`; the bounded fine-pitch retry also returns
`NO_LEGAL_ESCAPE`, dominated by `U21.4`, accepted `C65.1`/`ACC_5V_RAW`, and
adjacent U21 lands. Two clean screens are identical and emit no scratch copper.

The authoritative PCB remains byte-identical at `37718bc7...`. Its refilled
schematic-parity DRC signature remains exactly 199 footprint-library, five
inherited hole-clearance, and one inherited solder-mask-bridge reports. No
rule, placement, or accepted copper changed. The next bounded tactic is a
coordinated local `U21`/`L4`/`C65` cluster-refloor screen that preserves and
revalidates the accepted `ACC_5V_RAW` transaction while minimizing switch-loop
area; do not retry the generic launch or relax switch-node width/separation.
No owner decision is open.

## MAX17048 alert route promotion (2026-09-02)

`MAX17048_ALRT_N` now connects TP11.1 to U14.5 with an add-only, two-via In3
hop: 4.306134 mm of 0.20 mm copper and two 0.60/0.30 mm through-vias. The
bounded screen proves In2 closed and reproduces identical In3 physical geometry
twice. The refilled full-board KiCad gate retains only the accepted 199
footprint-library, five hole-clearance, and one solder-mask-bridge reports.
No accepted copper was removed; fitted opens improve 85→84 nets and 516→515
edges, and raw ratsnest improves 545→544. Board hash is `37718bc7...` and
`hardware/beta-v2/` remains untouched.

Next, screen the local accessory 5 V boost switching cluster, beginning with
`ACC_5V_LX` and then its feedback branch. Use power-topology-aware geometry;
the switching node must not be handled as a generic signal. No owner decision
is open.

## NFC receiver-input wall (2026-09-02)

The atomic `NFC_RFI1/RFI2` harness closes neither U9 package launch in either
order. The locked 0.30 mm B.Cu trunks cannot escape U9.22/U9.23, and the
courtyard-legal 0.20 mm neck does not change that result. Moving only unrouted
decoupler C17 east by 1.25 mm also leaves both pins trapped by the accepted RFO2
arm and adjacent U9 lands. Both clean baseline orders reproduce the unchanged
board hash `0a5c99d1a97d22a90a353f8d09abcc982d6c1aa46e006404ec8bf211df489486`
and the accepted 199/5/1 DRC signature. No copper or placement was promoted.

This materially unchanged package-edge wall is parked. Next, use a bounded
two-via inner-layer hop for the local `MAX17048_ALRT_N` connection; its generic
direct B.Cu route has `NO_PATH`. Preserve all accepted NFC and power copper.
No owner decision is open.

## NFC antenna pair promotion (2026-09-02)

The symmetric fitted `NFC_ANT_A` and `NFC_ANT_B` four-pad nodes are now
complete. The A/B trees use 14/16 segments and 34.205680/21.063397 mm of
0.30 mm B.Cu with no vias. Each matching resistor retains direct test-point
access, while the antenna connector joins through the receive-divider
capacitor. Both atomic launch orders pass; the promoted A-first order adds
exactly 30 target-net segments and removes no accepted copper.

The authoritative refilled schematic-parity KiCad DRC signature remains 199
footprint-library, five inherited hole-clearance, and one inherited
solder-mask-bridge report, with no attributable class. Fitted connectivity
improves 87 to 85 open nets and 522 to 516 open edges; raw ratsnest improves
551 to 545. Board hash is
`0a5c99d1a97d22a90a353f8d09abcc982d6c1aa46e006404ec8bf211df489486`.

Next is the adjacent symmetric `NFC_RFI1/RFI2` two-pad input pair. Preserve the
completed receive-divider, antenna, EMC/match/output, and crystal copper. MCU
USB and `BQ25185_SYS` remain parked. No owner decision is open.

## NFC EMC pair promotion (2026-09-02)

The symmetric fitted `NFC_EMCA` and `NFC_EMCB` four-pad nodes are now complete.
Each uses 13 segments / 8.755267 mm of 0.30 mm B.Cu with no vias. The atomic
scratch gate closes all eight fitted pads, adds exactly 26 target-net segments,
removes no accepted copper, and retains the refilled schematic-parity KiCad DRC
signature of 199 footprint-library, five inherited hole-clearance, and one
inherited solder-mask-bridge report. Fitted connectivity improves 89 to 87 open
nets and 528 to 522 open edges; raw ratsnest improves 557 to 551. Board hash is
`b1fad08fd1b2039d9e8e72e8cd9e13da6b3d53de0c1b7c6a9b906a961eb66dbe`.

Next is the adjacent symmetric `NFC_ANT_A/B` four-pad pair. Preserve direct
J7/test-point access, the accepted receive-divider branches, and the completed
EMC/match/output network. MCU USB and `BQ25185_SYS` remain parked. No owner
decision is open.

## NFC crystal launch wall (2026-09-02)

`route_nfc_crystal_pair_scratch.py` deterministically screens both complete
three-pad `NFC_XIN`/`NFC_XOUT` launch orders. XIN-first closes XIN and its load
capacitor but boxes `U9.4`; XOUT-first closes XOUT and its load capacitor but
boxes `U9.5`. Both partial candidates retain the accepted real refilled KiCad
DRC signature (199 footprint-library, five inherited hole-clearance, and one
inherited solder-mask-bridge report), so the failure is a shared B.Cu package
launch corridor at adjacent U9 pads rather than a DRC/rule or load-capacitor
wall. No partial crystal copper is promotable. Next, screen an explicit
two-launch geometry that reserves independent north/south exits before either
long crystal join; preserve short, no-via, same-face crystal routing and do not
move the 27.12 MHz crystal unless that bounded geometry is exhausted.

The reserved two-launch alternative is now exhausted and the wall cause is
sharper. `U9.5` (XIN) is north of `U9.4` (XOUT), while the present Y1 orientation
puts pin 3 (XIN) south-east of pin 1 (XOUT); the two required same-face routes
therefore exchange vertical order. An in-place 180-degree Y1 rotation removes
that forced crossover and all four crystal/load-cap edges route with the exact
accepted real KiCad DRC signature. It is not promotable geometry: the sequential
result is 15.602 mm XIN and 7.122 mm XOUT; one load-cap branch necessarily takes
the long outside path in each sequential ordering. The exact path geometry is
reproducible even though generated KiCad UUIDs vary.
`route_nfc_crystal_pair_scratch.py --rotate-crystal-180` preserves this
deterministic proof and refuses candidate emission despite electrical closure.

Next, screen a coherent `Y1`/`C79`/`C80` placement transaction which keeps Y1's
center unless a small translation materially improves both arms, aligns the
rotated pin order with U9, and restores short, balanced crystal and load-cap
branches. Promote placement and both nets only as one add/reposition transaction
after the authoritative full-board gate. No owner decision is open.

That coherent transaction is now promoted. `Y1` rotates 180 degrees in place;
`C79` and `C80` exchange their existing `(28.6,27.1)` and `(28.6,32.9)` mm
positions so both load capacitors remain outside the aligned arms. XIN and XOUT
use 11 and eight add-only 0.20 mm B.Cu segments, respectively, with zero vias;
their complete lengths are 8.537437 and 5.422361 mm. Both launch orders produce
identical geometry digest `0148d20322aa24fc...`.

The authoritative refilled schematic-parity KiCad DRC remains exactly 199
footprint-library, five inherited hole-clearance, and one inherited solder-mask
bridge report. No accepted copper was removed, and the only added copper is 19
segments on the two oscillator nets. The fitted ledger moves 91 to 89 open
nets, 532 to 528 open edges, and raw ratsnest 561 to 557. The authoritative
board hash is `2d54a40da1ec0f53e0cdf75bb35b63cc84aa7d435e8ef0cce896d7dbb69bec1e`.
Battery/accessory-power, RGB, XGPIO4/XGPIO5, and all other NFC paths remain
connected; `hardware/beta-v2/` is untouched.

Next, select the highest-leverage independent retained-net cluster from the
fitted ledger. Keep the materially unchanged MCU USB and `BQ25185_SYS` walls
parked. Manufacturing export remains premature at 89 retained open nets / 528
retained open edges; no owner decision is open.

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

The next independent increment on 2026-09-02 promotes the local SX1262 module
control strap `DIO2_TXEN`. `route_local_two_pad.py` is a deliberately small
allowlisted harness for deterministic same-face, two-pad Demo nets; its first
use joins adjacent U8.7/U8.8 with three 0.20 mm B.Cu segments (2.320 mm, zero
vias). The authoritative refill and full-board KiCad DRC retain exactly the
accepted 199 footprint-library, 5 inherited hole-clearance, and 1 inherited
solder-mask-bridge reports, with no attributable violation. The fitted pads
are one copper island, ratsnest falls 576 to 575, and an object multiset proves
zero accepted track/via removals or changes and exactly those three additions.
`hardware/beta-v2/` remains byte-identical. Board hash after refill:
`f7b5cda56285d503df16a96a6ef4a68df5a6f979e7b1452b1c63c90160ad3ed0`.

The next highest-leverage independent blocker is the adjacent local power-tree
pair `MAX17048_ALRT_N` (TP11.1/U14.5), followed by other short one-edge local
nets. Keep `BQ25185_SYS` parked until its revisit conditions are met. The RGB
replacement nets, both public XGPIOs, accessory switch enables, and accepted
power/battery copper remain unchanged; no owner decision is open.

The bounded follow-up first closes the direct `MAX17048_ALRT_N` tactic: both
ends are on B.Cu, but the 0.20 mm same-face router finds no legal corridor;
F.Cu is inapplicable because TP11 is a back-side SMD pad. The board stayed
unchanged during both scratch screens. The next coherent local alternative
promotes the symmetric `NFC_MATCH_A` and `NFC_MATCH_B` pair instead. Each arm
is a straight 1.900 mm B.Cu connection with three 0.30 mm segments and zero
vias, satisfying the existing equal-arm/minimum-width NFC rule.

The refilled full-board KiCad gate retains exactly 199 footprint-library, five
inherited hole-clearance, and one inherited solder-mask-bridge reports, with
no attributable violation. Both two-pad nets are single copper islands,
ratsnest falls 575 to 573, and the board diff is exactly six add-only B.Cu
segments on the two allowlisted nets; no zone, via, placement, net assignment,
or accepted copper changes. `hardware/beta-v2/` remains byte-identical. Board
hash after refill: `f449e932ee7374cf6377f75bb7b3624f3a16489b1bd43c1a3d234776d2342609`.

Next, use the fitted-pad ledger to select another bounded local connection;
do not retry `MAX17048_ALRT_N` with the direct same-face tactic and keep
`BQ25185_SYS` parked. Manufacturing export remains premature while 101
retained multi-pad nets are still open. No owner decision is open.

The next independent increment on 2026-09-02 promotes `ILIM_VSET`, the local
BQ25185 charger input-limit programming connection from `R36.1` to `U11.7`.
The deterministic two-pad framework adds five 0.20 mm B.Cu segments (4.809 mm,
zero vias). The authoritative refilled full-board KiCad DRC remains exactly
199 footprint-library, five inherited hole-clearance, and one inherited
solder-mask-bridge report, with no attributable violation; schematic parity
was enabled. Both fitted pads are one copper island, retained open edges move
544 -> 543, raw ratsnest 573 -> 572, and the PCB delta is add-only. Accepted
battery and accessory-power copper, the routed RGB replacements, XGPIO4/5,
and `ACC_5V_SW_EN` remain untouched. Board hash:
`654a9ff75d8e7ff8853297e4b5bd1d4d1f15d8b81bfc7199acec87518bfa4ff1`.

Next, select another independent short fitted-pad edge from the ledger;
`USB_D_ESD_N` is the shortest uncharacterized non-charger candidate. Preserve
the USB differential topology and do not treat a single-leg route as a
promotable pair unless skew/coupling review passes. Keep `BQ25185_SYS` parked.
Manufacturing export remains premature while 100 retained multi-pad nets are
open. No owner decision is open.

The bounded `USB_D_ESD_N/P` screen on 2026-09-02 closes the independent-leg
tactic without changing the authoritative board. `route_usb_esd_pair_scratch.py`
routes both local ESD-to-series-resistor legs sequentially on F.Cu using the
locked 0.23 mm USB width and 0.20 mm clearance. Both routes close with zero
vias, at 13.513695 mm for N and 11.618521 mm for P (1.895174 mm skew).

The real zone-refilled full-board KiCad DRC rejects that topology with exactly
one attributable `diff_pair_gap_out_of_range` error: the two independent
detours separate by 0.7246 mm, above the locked 0.24 mm maximum. All other DRC
classes remain the accepted 199 footprint-library, five inherited hole-
clearance and one inherited solder-mask-bridge reports. Two clean runs produce
byte-identical JSON (`sha256 b2b98236dd9f190d7e48a4efce1cd9d158f5df70ea1da84bf148bdd719b79073`).
The authoritative board remains byte-identical at `654a9ff7...`; retained open
edges remain 543, raw ratsnest 572, and accepted USB, battery, accessory-power,
RGB and XGPIO4/5 copper is untouched.

Next, implement a coordinated paired-path primitive for these two local legs:
0.23 mm width, fixed 0.20 mm gap, F.Cu only, zero vias, with real KiCad pair-gap,
uncoupled-length and skew review. Do not retry the disproven independent-leg
tactic. Keep `BQ25185_SYS` parked. Manufacturing export remains premature while
100 retained multi-pad nets are open; no owner decision is open.

The coordinated follow-up promotes both local USB ESD legs together.  It keeps
the 0.23 mm traces entirely on F.Cu with zero vias, normalizes the shared
corridor inside the 0.18--0.24 mm pair-gap contract, and leaves only the
placement-required endpoint splays uncoupled.  Final lengths are 13.513695 mm N
and 11.878490 mm P; the 1.635205 mm skew is below the already accepted 2.4 mm
intrinsic placement skew and the design intentionally requires no Full-Speed
USB length matching.  Clean replays have identical deterministic evidence.

The authoritative zone-refilled full-board KiCad gate reports exactly the
accepted 199 footprint-library, five inherited hole-clearance and one inherited
solder-mask-bridge issues and no attributable class.  Both nets are single
copper islands; retained open edges fall 543 to 541 and raw ratsnest 572 to
570.  The board delta is exactly 21 add-only F.Cu segments on the pair, with no
accepted copper, placement, via, net assignment, rule, or `hardware/beta-v2/`
change.  Board hash: `103a102c4ecf3bce0f5dca28f6266dd986e094f4256d8c3c8d7d650032ce369c`.

Next, route `/USB_D_MCU_N` and `/USB_D_MCU_P` as one coordinated F.Cu,
zero-via transaction and review the whole connector-to-MCU USB pair.  Do not
promote an independently routed leg.  `BQ25185_SYS` remains parked;
manufacturing export remains premature while 98 retained multi-pad nets are
open, and no owner decision is open.

The next bounded screen closes the generic independent-leg tactic for the
MCU-side USB pair: `/USB_D_MCU_N` has no legal F.Cu path at either 0.050 or
0.025 mm grid resolution, before adding the P leg. No USB copper was promoted.
A genuinely coordinated corridor primitive remains the required next USB
step; do not retry the generic single-leg router or promote one leg alone.

The same iteration extends the local two-pad framework with explicit
schematic-DNP pad exclusion and promotes `DISP_SDO` from fitted `J1.33` to
`TP36.1`, leaving DNP `R112.1` outside the routing obligation. The route is
four add-only 0.20 mm F.Cu segments (4.649 mm), with zero vias and zero removed
accepted copper objects. The authoritative refilled full-board KiCad gate
retains exactly 199 footprint-library, five inherited hole-clearance, and one
inherited solder-mask-bridge report, with no attributable violation. The
fitted ledger moves 541 to 540 open edges, 570 to 569 raw ratsnest, and 98 to
97 open retained nets. All accepted USB, battery, accessory-power, RGB, and
XGPIO4/5 copper remains unchanged; `hardware/beta-v2/` is untouched. Board
hash: `4a6e12756b4fbbc9269a6f18256bc055485740c4d4ecf178455c7d20498a2306`.

Next, build the coordinated MCU-side USB corridor primitive and review the
whole connector-to-MCU pair. `BQ25185_SYS` remains parked. Manufacturing
export remains premature while 97 retained multi-pad nets are open; no owner
decision is open.

The next bounded iteration reconfirmed why the remaining MCU-side USB pair
needs a new primitive: the resistor endpoints are ordered N/P from left to
right while the ESP32 endpoints are P/N, and the generic empty-pair F.Cu
screen still cannot route the N leg at either 0.050 or 0.025 mm resolution.
A coordinated solution must explicitly handle that endpoint crossover while
keeping the pair within its coupling contract; fixed-offset reuse of the ESD
pair and single-leg promotion remain closed.

The independent coherent alternative promoted both USB-C configuration
straps. `Net-(J3-CC1)` connects `J3.A5` to `R31.1` in six F.Cu segments
(11.474888 mm), and `Net-(J3-CC2)` connects `J3.B5` to `R30.1` in eight F.Cu
segments (14.066030 mm). All 14 segments are 0.20 mm wide; there are no vias,
no missing accepted copper objects, and no placement or rule change. The
authoritative refilled, schematic-parity KiCad gate remains exactly 199
footprint-library, five inherited hole-clearance, and one inherited solder-
mask-bridge report. Retained open edges fall 540 -> 538, raw ratsnest 569 ->
567, and open retained nets 97 -> 95. Board hash: `c052390c09b542cbcff7904aa6518bc42f41026aa892e30c6c94405dfa8373e2`.

A same-face `ISET` screen was also rejected before promotion: `U11.8` has no
legal 0.20 mm B.Cu escape between adjacent charger lands, existing copper, and
the board edge. Do not retry that generic tactic. `BQ25185_SYS` remains parked.
The next highest-leverage fabrication blocker is the endpoint-order-aware
coordinated `/USB_D_MCU_N` and `/USB_D_MCU_P` transaction; no owner decision
is open and manufacturing export remains premature.

The bounded endpoint-order crossover screen on 2026-09-02 proves that both MCU
legs are geometrically routable when each uses a symmetric 0.60/0.30 mm
two-via hop: N closes on In2 in 22.027355 mm and P closes on In3 in 24.527890
mm. Real refilled KiCad DRC rejects the complete transaction with five
`items_not_allowed` reports from the locked rule that forbids USB copper on
In2/In3; all other reports remain the accepted 199 footprint-library, five
hole-clearance, and one solder-mask-bridge classes. The authoritative board is
unchanged. Do not weaken the USB layer contract or retry an inner-layer
crossover.

Next, run a bounded R33/R34 order/refloor impact screen. It must first determine
whether endpoint order can be corrected while preserving the accepted
connector-side ESD pair copper; if not, close that tactic without moving parts
and return to an explicitly coupled F.Cu perimeter corridor search. Do not
delete accepted USB copper merely to make the resistor order convenient.

The bounded R33/R34 order screen on 2026-09-02 closes the rigid-pivot refloor
without changing the board. `screen_usb_series_order.py` pins each resistor's
pad 1 to the exact accepted ESD-side copper anchor and enumerates all 16
orthogonal pose combinations twice with byte-identical evidence. None reverses
the MCU-side endpoint order. More strongly, the pad-1 anchors are 3.596114 mm
apart in X and each 0603 pad pair has a 1.650000 mm centre radius, so even
arbitrary continuous rotations leave P pad 2 at least **0.296114 mm** to the
right of N pad 2. The resistor pair therefore cannot correct the N/P crossover
while preserving both accepted pad-1 anchors. Swapping the references or net
identities would instead misconnect the already routed ESD pair and is not an
electrical refloor.

The authoritative PCB remains byte-identical at `c052390c...`; no footprint,
copper, rule, or schematic change was promoted. The next bounded USB tactic is
an explicitly coupled F.Cu perimeter/circumnavigation search that handles the
reversed endpoints as a pair. Do not retry rigid R33/R34 pivots, inner-layer
hops, the generic independent-leg router, or delete the accepted ESD copper.
If that planar search cannot close, park this materially unchanged USB wall and
select another retained net from the fitted-pad ledger.

The bounded whole-board F.Cu perimeter screen on 2026-09-02 closes that final
USB tactic without changing the board. `screen_usb_mcu_perimeter.py` searches
all 4,444,481 legal-grid cells at 0.050 mm resolution with the locked 0.23 mm
width, 0.20 mm clearance, zero vias, and both insertion orders. Each polarity
has eight legal resistor-side launches and only two MCU-side launches. All four
destination-facing ranked launch combinations independently return
`NO_FULL_BOARD_FCU_PATH` before the other polarity is inserted. Two clean runs
are byte-identical (`sha256 2da46557b16b626cd400d4f51d2a4837198e2c0280782c238d21b7cf8efcbdf5`).

The scratch full-board refill/DRC remains exactly 199 footprint-library, five
inherited hole-clearance, and one inherited solder-mask-bridge reports, with no
attributable class. The authoritative PCB remains byte-identical at
`c052390c...`; accepted USB ESD, battery, accessory-power, RGB, and XGPIO4/5
copper is untouched. Together with the rejected inner-layer crossover and the
bounded resistor-pivot proof, the materially unchanged MCU-side USB wall is now
PARKED. Do not retry those tactics or weaken the USB layer/coupling contract.

The next independent bounded task is a coordinated symmetric route screen for
the local `NFC_RFO1`/`NFC_RFO2` pair (one retained open edge each, 4.263 mm and
5.538 mm spans). Preserve the differential NFC output geometry and tuning
network; do not promote one arm alone. The fitted ledger remains 95 open nets /
538 retained open edges, and no owner decision is open.

The coordinated NFC output-arm screen on 2026-09-02 is characterization-only.
The initial 0.20 mm-clearance replay found that route order matters: RFO1-first
boxes U9.15, while RFO2-first geometrically closes both arms. Real KiCad DRC
correctly rejected that replay with three `NFC_RF` clearance violations because
the authoritative routed-clearance contract is 0.25 mm. The harness was then
corrected rather than weakening the rule or promoting partial copper.

At the correct 0.30 mm width / 0.25 mm clearance, both bare launches return
`NO_LEGAL_ESCAPE`. U9.13 and U9.15 are 0.30 mm-wide lands on 0.50 mm pitch, so a
full-width trace has only 0.20 mm to the neighboring U9 land while it remains
inside the package perimeter. This is a package-neck wall, not a downstream
route-capacity wall. Two corrected runs reproduce the same zero-track geometry
hash and accepted refilled schematic-parity DRC signature: 199 footprint-
library, five inherited hole-clearance, and one inherited solder-mask-bridge
report. No NFC copper entered the authoritative PCB, whose hash remains
`c052390c09b542cbcff7904aa6518bc42f41026aa892e30c6c94405dfa8373e2`.

Next, measure the minimum identical neck length needed for U9.13 and U9.15 and
screen a single courtyard-scoped package-launch clearance treatment applied to
both arms. Keep 0.30 mm width and 0.25 mm clearance everywhere outside U9,
B.Cu-only routing, zero vias, and atomic pair promotion; review arm geometry and
the complete NFC tuning path before accepting it. Do not retry the disproven
global 0.20 mm-clearance tactic or promote only one arm. The ledger remains 95
open retained nets / 538 retained open edges, and no owner decision is open.

The follow-up closes and promotes the NFC output pair atomically.  The existing
DRU deliberately applies the 0.25 mm `NFC_RF` routed-clearance rule only when
neither item is a pad, so the routing framework now models that distinction:
0.20 mm to package lands and 0.25 mm to routed copper, without changing the DRU
or reducing the 0.30 mm trace width.  RFO2-first then RFO1 closes on B.Cu with
zero vias.  Both U9 launches are 0.925 mm and both inductor launches are
1.105 mm; total copper is 8.674 mm for RFO2 and 6.074 mm for RFO1.  The 2.600 mm
arm difference is imposed by the existing asymmetric placement, while the
package treatment itself is identical.

Two clean scratch runs reproduce the same routes and geometry digest
`026652a473125bde...`.  The independent refilled schematic-parity KiCad DRC
contains only 199 footprint-library, five inherited hole-clearance, and one
inherited solder-mask-bridge report.  Both RFO nets are one copper island;
retained opens fall 95→93, retained edges 538→536, and ratsnest 567→565.  The
board delta is exactly 12 add-only 0.30 mm B.Cu segments on the two RFO nets,
with no via, footprint, zone, placement, net-assignment, or accepted-copper
removal.  Battery/accessory-power, all three RGB replacements, XGPIO4/XGPIO5,
and `ACC_5V_SW_EN` remain connected; `hardware/beta-v2/` is untouched.  The
authoritative PCB hash is `ed13ce4b547085cd46b7ef01c5965e0d5fa3869581459d0965c4e0ec756efb79`.

Next, take the coherent local `NFC_RXA`/`NFC_RXB` receive pair through the same
scratch-first/full-board gate discipline, then the `NFC_XIN`/`NFC_XOUT` crystal
pair.  Preserve the full tuning path and do not revisit the parked MCU USB wall
without a material geometry change.  Manufacturing export remains premature
at 93 retained open nets / 536 retained open edges; no owner decision is open.

The next bounded increment promotes both three-pad NFC receive arms atomically.
`NFC_RXA` and `NFC_RXB` each use ten add-only 0.30 mm B.Cu segments, total
7.309798 mm, and have zero vias and zero arm-length delta. Two clean scratch
replays reproduce geometry digest `c27a31d182019135...`; generated KiCad UUIDs
vary, while the complete physical geometry is identical.

The authoritative zone-refilled schematic-parity KiCad DRC retains exactly 199
footprint-library, five inherited hole-clearance, and one inherited
solder-mask-bridge reports, with no attributable class. Both receive nets are
single copper islands; retained open nets fall 93→91, retained edges 536→532,
and raw ratsnest 565→561. The board delta is exactly 20 add-only B.Cu segments
on the two allowlisted nets, with no vias or accepted-copper removals. The full
NFC output/matching path, battery/accessory-power copper, RGB replacements,
XGPIO4/XGPIO5, and `ACC_5V_SW_EN` remain connected; `hardware/beta-v2/` is
untouched. Board hash: `c60088214d12c81dcb00c8bc3a12c933efc5d676e034153259ce75d985ca67ee`.

Next, route `NFC_XIN` and `NFC_XOUT` as one coherent crystal transaction and
review the complete oscillator geometry. Keep the MCU USB and `BQ25185_SYS`
walls parked. Manufacturing export remains premature at 91 retained open nets /
532 retained open edges; no owner decision is open.
### ACC_5V boost B.Cu core screen

`screen_acc_5v_bcu_core.py` replays `ACC_5V_LX` first after the 180-degree
`U21`/`L4` rotation, preserves the accepted five-via `ACC_5V_RAW` distribution
tree, and screens five bounded `L4` offsets.  It changes only scratch boards and
reports real refilled KiCad DRC.  The current result closes LX in every case but
proves that moving `L4` alone does not remove the rotated `L4`/`R99` courtyard
overlap; the restored straight U21.6 raw neck also crosses `ACC_DETECT_N` and
misses the power-copper clearance to LX/the accepted raw via.  The next replay
must route that neck around those fixed obstacles and include `R99` in the
minimum placement boundary.

### ACC_5V coordinated corridor screen

`screen_acc_5v_corridor_pair.py` fixes the D-418 R99 placement and bounds 12
explicit LX-inner/raw-outer B.Cu corridors without changing the authoritative
board. All cases fail the real refilled schematic-parity DRC. Increasing the
raw detour westward and southward does not clear the retained `BQ25185_SYS`
field on its return to the accepted raw tree; GND/LX/crossing and clearance
collisions are secondary. Two clean runs reproduce zero candidates, although
KiCad can label coincident geometry as short, crossing, or clearance between
runs. The planar outer-corridor family is parked. Next, screen a package-local
U21.6 transition into the existing In3 raw tree with LX retained on B.Cu before
attempting the full six-branch placement transaction.

## Shared SPI-A clock/data wall (2026-09-02)

The follow-up promotes the independently reproducible clock tree. The shared
harness now accepts `--only sck`/`--only mosi`; `--only sck` closes U1.20,
J1.36, and J2.5 with 14 add-only 0.20 mm F.Cu/In2.Cu segments and four ordinary
0.60/0.30 mm vias (72.751257 mm). Two clean candidates reproduce identical
physical geometry, and the authoritative refilled parity gate retains the
accepted 199/5/1 signature with no attributable class. MOSI remains open and
the paired adjacent-J1 family remains parked. Next, freshly rank an independent
retained net or coherent local cluster; do not retry MOSI without material
geometry change.

`route_spi_a_clock_data_scratch.py` now requires both fitted three-pad trees,
`SPI_A_SCK` and `SPI_A_MOSI`, to close in one add-only transaction.  Both launch
orders pass real refilled schematic-parity DRC with exactly the inherited
199 footprint-library, five hole-clearance, and one solder-mask-bridge reports,
and remove no accepted copper.  Clock-first closes SCK but leaves the MOSI
display branch at `NO_VIA_SITE`; data-first closes MOSI but leaves the SCK
display branch at the same wall.  Pinning the two nets to separate In2/In3
hauls does not change the result because ordinary through vias occupy all
copper layers.

No partial tree is promoted and the authoritative board remains byte-identical
at `7e20e227...`.  The next bounded tactic is to reserve distinct perimeter
fanouts for adjacent J1.34/J1.36 before either long haul, then attach U1 and J2
atomically.  If two legal barrels cannot be exposed, park the paired wall and
independently gate the already reproducible complete SCK tree.  No owner
decision is open.

# BQ25185 TS/MR add-only wall (2026-09-02)

`route_local_two_pad.py` retains two exact `Net-(U11-TS_MR)` contracts. The
qualified `BQ25185_TS_MR` inner-haul case reserves both B.Cu endpoints but has
no In2/In3 join. `BQ25185_TS_MR_PLANAR` is the independent same-face fallback;
run it only under a 60 second external timeout because the generic planar wave
does not terminate usefully in the current congestion. Neither case emitted
authoritative copper. Park both until surrounding geometry changes; next route
the fitted three-land `Net-(U1-EN)` reset tree atomically.

# ESP32 EN reset tree (2026-09-02)

`route_mcu_en_tree_scratch.py` atomically screens both orders of the two boxed
endpoint legs retained in `route_local_two_pad.py`. The accepted D-464 result
connects U1.3/C1.2/R1.1 with 11 add-only 0.20 mm tracks and four ordinary vias:
the 9.915176 mm U1-to-C1 leg uses In3 and the 36.042111 mm C1-to-R1 leg uses
In2. Both orders produce the same clean connectivity and 199/5/1 refilled
parity-DRC result. Do not restore the rejected D-321 same-face reset detour.
Next, freshly screen the independent three-land `CC1101_CS_N` control tree.

## ACC_5V feedback inner-tree wall (2026-09-02)

`route_acc_5v_fb_tree_scratch.py` atomically screens both branch orders and
both In2/In3 assignments for U21.1, R99.2, and R100.1. It preserves the
0.20 mm feedback width, 0.25 mm routed clearance, and ordinary 0.60/0.30 mm
via contract, and accepts only a complete tree with real refilled parity DRC.
R99.2 has no reachable via site in all four cases. R100.1 can be reached only
when assigned to In3, but that partial branch is rejected because R99 remains
open and the scratch board has two attributable clearances. No candidate is
written and the authoritative PCB is unchanged. Park this inner-only family;
the next ACC_5V_FB attempt belongs inside the existing U21/L4/R99 power-core
refloor transaction.
# BQ25185 dual-status generic family (2026-09-02)

`route_local_two_pad.py` now carries exact fitted contracts for all three
branches of both `/BQ25185_STAT1` and `/BQ25185_STAT2` four-land trees.
`route_bq25185_status_pair_scratch.py` treats the two trees as one atomic unit
and rejects partial status wiring. The generic family is bounded at the two
equivalent expander branches: U2.9-to-R127.2 and U2.10-to-R128.2 both return
`NO_PATH` at 0.05 and 0.025 mm grids with 0.20 mm width/clearance. No copper was
promoted; the next mechanism is a coherent paired U2 package-fanout and
inner-layer join before replaying both complete trees.

## BQ25185 status-neighborhood withdrawal wall (2026-09-02)

`screen_u2_status_neighborhood_refloor.py` bounds the D-495 follow-up without
touching the authoritative board.  It withdraws complete nets, not geometric
fragments, and tests minimum-cardinality subsets of the three routed nets
measured nearest U2.9/U2.10: `/TOUCH_RST_N` (18 copper items), `/DISP_RST_N`
(12), and `/SD_CARD_DETECT_N` (29).  All eight subsets, including withdrawal
of all 59 items, fail all 16 paired ordinary-via launch cases with
`NO_VIA_SITE`.  Board `be285abf...` remains byte-identical.  This local
copper-withdrawal refloor cannot unlock the charger-status pair; park the
unchanged U2 status package wall until a broader component-placement
transaction is justified.  Next freshly screen the independent shared SPI-B
clock/data cluster rather than replaying another U2 fanout family.

## Shared SPI-B four-endpoint batch screen (2026-09-02)

`route_spi_b_bus_scratch.py` treats `/SPI_B_SCK`, `/SPI_B_MOSI`, and
`/SPI_B_MISO` as one coherent fitted-device batch spanning U8, U7, U1, and U9.
It reuses the accepted 0.20 mm, ordinary 0.60/0.30 mm via inner-haul framework
and screens all six bus orders without changing the authoritative board.  The
U8-to-U7 B.Cu leg succeeds for every first-selected net.  MOSI and MISO then
stop at their U7-to-U1 inner launch with `NO_VIA_SITE`; SCK closes U8-to-U7 and
U7-to-U1 but stops at U1-to-U9 with `NO_LEGAL_ESCAPE`.  The identical result
for both relevant permutations makes blind bus-order replay unproductive.
Board `be285abf...` remains byte-identical at 57 open retained nets / 461
edges.  Next reserve the three adjacent U1.4/U1.5/U1.6 and U9.30/U9.31/U9.32
package fanouts as a bounded bus-aware transaction before attempting any long
haul; include the U7.16/U7.17 launch pair in the same capacity screen.

## Shared SPI-B package-fanout capacity screen (2026-09-02)

`screen_spi_b_package_fanouts.py` qualifies every adjacent package land in
isolation across eight site indices and both In2/In3 targets, then reserves
each package group coherently before any long haul.  U1.4/U1.5/U1.6 have
15/10/16 qualified cases and coexist in the first tested combination.  The
binding U7.17/U7.16 pair has 7/6 qualified cases and coexists after nine
ordered combinations.  U9.32 has all 16 generic cases, while U9.30 and U9.31
each fail all 16 with `NO_LEGAL_ESCAPE`; therefore no three-line U9 witness or
partial promotion exists.  The authoritative PCB stays byte-identical at
`be285abf...`, 57 open retained nets / 461 edges.  Next use a package-specific
shared B.Cu perimeter fanout for U9.30/U9.31, reserving both launches before
the D-497 complete-tree replay.

## Shared U9 SPI-B perimeter fanout screen (2026-09-02)

`screen_spi_b_u9_shared_fanout.py` corrects the prior prose layer assumption
from the live PCB: U9.30/U9.31 are F.Cu QFN lands.  It tests 950 explicit
outward shoulder-and-via shapes per land, then reserves both launches in both
orders before accepting a witness.  Each land has 12 legal individual shapes,
but none of the 288 ordered pairs coexist at 0.20 mm width/clearance with
ordinary 0.60/0.30 mm through-vias.  The screen is scratch-only and emits no
partial copper.  Park this unchanged endpoint wall; next freshly screen the
independent fitted `/CC1101_GDO0` two-land control link.
## CC1101 GDO0 complete route (2026-09-02)

`route_cc1101_gdo0_scratch.py` reuses the D-500-qualified U7.15 B.Cu fanout,
screens eight MCU escape sites on each inner signal layer, and accepts only a
complete target-only link after real refill, schematic-parity DRC, fitted
connectivity, and accepted-copper preservation all pass.  In2 rejects all
eight joins; In3 produces eight clean witnesses.  The promoted witness adds
13 target-only objects and 64.957952 mm of track, closes `/CC1101_GDO0`, and
improves retained connectivity to 56 open nets / 460 edges.  Real DRC remains
199 library / five hole / one mask reports.  Next screen `/SX1262_DIO1` only
through a bounded U2.20 package-fanout/refloor transaction, not its parked
ordinary-via family.

## BQ25185 SYS / IR_RX minimum refloor transaction (2026-09-03)

`route_bq25185_sys_ir_refloor_scratch.py` withdraws all 14 accepted
`/IR_RX_GPIO44` objects, replays qualified C26 doglegs, requires the complete
13-land `BQ25185_SYS` tree, and only then replays both IR branches and runs
connectivity plus real refilled parity DRC. The SYS harness now accepts an
explicit C26 witness without weakening its 0.50/0.250 mm haul or 0.90/0.40 mm
power-via contract. All 24 C26 witnesses stop at pristine `C27.1 NO_VIA_SITE`,
even with C27 first. Next inventory the C27 pocket and screen the smallest
joint complete-net withdrawal/replay boundary.

## BQ25185 SYS corrected atomic case 8 (2026-09-03)

The resumable complete-net refloor harness screened corrected case 8 with the
ninth qualified `U12.10` witness. All 13 governed endpoints reserve and nine
joins complete; the other 15 finite trials report `NO_PATH`, leaving the same
four components: the main U12/SW9/capacitor tree, isolated U11.1, C33/C64, and
L4/U21. The incomplete tree correctly prevents all replay, DRC, candidate, and
promotion stages. Board `64e5ae37...` remains byte-identical at 54 open
retained nets / 446 edges. Continue at case 9 without replaying cases 0--8.

## BQ25185_SYS U11 waypoint bridge family bounded (2026-09-03)

The D-576 successor extends the SYS scratch framework with a bounded U11.1
two-leg waypoint bridge search. One representative atomic refloor case was
screened with 48 waypoint trials across In2/In3. Every trial stops on the first
leg with `NO_PATH` at the locked 0.50 mm SYS width; the complete SYS tree still
has four components and cannot be promoted. Authority remains byte-identical
at `64e5ae37...`, with zero attributable DRC delta. Park this unchanged U11
waypoint family until surrounding geometry materially changes and continue on
an independent retained-net transaction.

## MOVING A PART, and the invariant that makes it reviewable (D-619, 2026-09-05)

All five open `U9` NFC edges measure `DETOURABLE` + `UNRELAYABLE`: every
corridor OPENS when its crossing tracks are cut, and the irreducible blocker is
in every case a `.kicad_dru` SINGLE-LAYER net (`NFC_XIN`, `NFC_XOUT`,
`NFC_RFO2`, all `layers_allowed = ['B']`).  A net with one layer and no barrel
has nothing to detour onto.  When the blocker cannot move, the wall must --
`U9.7`'s escape band is `[30.700, 31.050]`, **0.350 mm where two 0.200 mm
tracks need 0.400 mm**, short by FIFTY MICRONS.

    python3 apply_part_shift.py --ref Y1 --dx-nm -300000 [--apply] --report R.json
    python3 checks/placement_contract.py --ref HEAD --move Y1:-300000:0 -o R.json

`apply_part_shift.py` translates ONE footprint by an exact (dx, dy) in
nanometres and REFUSES the move if any track endpoint would leave the pad it
serves or any courtyard would newly overlap -- which is what caps the `Y1` shift
at 0.300 mm, because at 0.500 mm the `GND` stitch barrel at `30.000, 29.500`
leaves `Y1.4`'s land.  `checks/placement_contract.py` is the gate clause that
did not exist: every other check on this board judges COPPER, and a footprint
move changes no track, no via, no zone and no rule area.  PL7 is there because
PL1-PL6 were not enough -- the `Y1` shift alone drops `Y1.4`'s `GND` land onto
three `NFC_XIN` tracks (two shorts, one 0.0389 mm clearance) and PL1-PL6 all
pass.  **A placement transaction must ride with a re-route of whatever it
landed on.**

Two further lessons are in the code, not just the record.  `pour_bond_contract.py`
P2 resolved a tube's island by ORDINAL, so one split island renumbered every
ordinal above it and it reported **33 dead tubes for one real injury**; it now
resolves by GEOMETRY.  And the pour-bond guard and a corridor lane `--guard`
merge into ONE spec -- a lane says where a route may not GO, a bond tube says
which pour copper it may not EAT -- which is how `NFC_VDD_D` was closed without
repeating the refused `NFC_VDD_A` run that cut the `B.Cu` `GND` pour 55 -> 56
islands.
