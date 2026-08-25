## 2026-08-25 - the placement question is answered, the block still does not close (FBV2-P2-002F)

**FBV2-P2-002F = FAIL.** Phase A did not complete, so Phase B never ran and
`aqroot-Beta-v2.kicad_pcb` is byte-identical to `24f6611`: zero tracks, zero signal vias. **The
placement ECO is NOT applied to the authoritative board** - section 23 forbids committing an
unproven placement, and a placement that does not pass section 13 is not proven. PCB routing stays
0 %, overall stays 74 %. Full analysis:
[`audits/2026-08-25-p2-battery-placement-eco.md`](audits/2026-08-25-p2-battery-placement-eco.md).

### PR-25 is closed, and closed by measurement

U18 rotates **90 -> 180** and moves **(3.000, 72.400) -> (8.000, 65.250)**. At 002E's pose it sat at
x 1.205..4.795 with R75 immediately south and the R76..R83 divider wall at x 7.300..10.350: every
north-row pin escaped through the same **2.505 mm** corridor, and R75's own 3.35 mm pads stood
between `U18.8` and its Kelvin target. **6 of 8 pins escaped, 7 at best.**

At rot 180 the pin rows face east and west and U18 straddles R75's midline, so `U18.8` and `U18.9`
look straight at `R75.2` and `R75.1`. **8 of 8 escape and 8 of 8 route.** The divider *wall* is
gone - every part is now placed by the U18 pin it serves.

The pose came from 13 284 candidates: 2 490 cleared collision and the section 4 Kelvin envelope,
1 331 kept both Kelvin branches under 10 mm with a legal 1.50 mm trunk, 20 were fully scored, and
the winner was re-confirmed by **routing all eight pins with the real router** against the real
trunk, chain and flare.

### `Q3_CS` closes with zero vias, and the authorised via was declined

Section 5 authorised one `Q3_CS` layer drop. It was measured across four variants of the same
prefix and **not taken**: CS-before-gate closes all twelve connections at Q3 on B.Cu with no vias;
moving Q3 1 mm loses **both** CS nets; and the authorised drop **cannot even start**, because
`Q3.3` has no B.Cu escape left once the gate has routed. The whole price is **2.188 mm** on one
gate link. `LTC_GATE`, which 002E left in two pieces, is now **one connected component**.

### The numbers

| target | 002E | 002F |
|---|---|---|
| U18 signal-pad escapes | 6 of 8 | **8 of 8, all routed** |
| R75 Kelvin mismatch | 20.620 mm | **2.454 mm** |
| `U18.1` VIN tap | 32.204 mm | **1.850 mm** |
| `U14.2` branch | 31.228 mm | **6.387 mm**, U14 did not move |
| worst megohm dead-cell node | 64.01 mm | **18.43 mm** |
| `Q3_CS` | `NO_LEGAL_ESCAPE` | **5.500 mm, zero vias** |
| connections on one scratch board | 60 | **70** |
| ratsnest | 781 -> 718 (-63) | **781 -> 709 (-72)** |
| in-scope nets fully connected | - | **23 of 29** |

DRC was identical to the baseline after every single connection, and there is zero out-of-scope
copper.

### Why it still fails

Section 14 allows no partial pass. Six nets sit in two islands and **four of them are one stranded
pad** - `R80.1`, `U19.2`, `U19.3` - plus the `{TP15, U14.2, U14.3}` MAX17048 island. `U19.2` and
`U19.3` are a U19 placement question of exactly the kind PR-25 answered for U18 (**PR-34, open**).

### Four harness rulings, and one lesson

**PR-30** fine-pitch slack ties break on how many ways out a pad still has. **PR-31** a partner must
sit on the side its pin faces, or the route wraps the package - `U18.10` cost 18.4 mm and took
`U18.2`'s only lane with it. **PR-32** re-measure before every fine-pitch pin. **PR-33** U19 is an
SOT-23-8 on 0.65 mm pitch and had no measured ordering at all; giving it one recovered three pins.

The lesson underneath all four: **an escape proof measures a 0.5 mm stub and a connection is a
route.** Four placements passed the section 12 gate - including its section 3C simultaneity test,
49 escapes laid at once with none lost - and then failed Phase A. The fix was not a better proxy
but a worse-scaling one: route the pin field with the real router, against the copper the plan lays
first.

**B-34 stays open.** Scratch pack-current copper is approximately 64.9 mOhm, essentially unchanged
from 002E, so the ECO cost the load path nothing. Physical validation remains mandatory.

## 2026-08-25 - the block routes, the pin field does not (FBV2-P2-002E)

**FBV2-P2-002E = FAIL.** Phase A did not complete, so Phase B never ran and
`aqroot-Beta-v2.kicad_pcb` is byte-identical to `e09eb35`: zero tracks, zero signal vias. PCB
routing stays 0 %, overall stays 74 %. Full analysis:
[`audits/2026-08-25-p2-battery-authoritative-route.md`](audits/2026-08-25-p2-battery-authoritative-route.md).

**First unresolved FUNCTIONAL connection: `BAT_RAW` `R80.1 -> Q2.7`. Most consequential:
`LTC_GATE` `U18.10 -> Q3.4`.**

### 60 connections, ratsnest -63, and a DRC that never moved

The previous best was 27 connections and -32. This run closed the whole high-current path end to
end - `J4 -> F1 -> Q2 -> Q3 -> R75 -> D9 -> U11.2` - with the `BAT_PROTECTED_P` trunk at its
**1.50 mm target on B.Cu carrying zero vias**, both R75 Kelvin branches, the U11.2 flare, the
MAX17048 taps, and **the dead-cell / recovery network for the first time**. DRC after every single
connection was identical to the baseline: no new violation of any class, ever.

### A segmentation fault, and four more harness defects

`split_at()` replaces one track in `qb.laid` with two, and the mark taken before it is an index
into that same list. Nothing shifted the mark, so `revert()` removed a track belonging to the
**trunk** and left one of the branch's own behind - and a second revert on the same trunk called
`BOARD::Remove` on an item no longer in the list, which segfaults rather than raising. Exit 139 at
`TP34.1`, 55 connections in, with no Python traceback because only the watchdog was armed.

Fixed, made undoable, `faulthandler.enable()` turned on, and pinned by a new **`router_regression`
G7** that checks the arithmetic rather than waiting for a crash. Also fixed: an item budget that
starved the F.Cu fallback and made the router look nondeterministic (**PR-20**); trunks silently
dropping width to buy a layer hop (**PR-21**); and an already-connected check that read a FILE
still holding reverted copper, so connections that had never been routed were counted as done
(**PR-22**).

### Ordering is section 8's, and inside the pin field it is measured

Putting U18's pin field before the trunk let a 0.20 mm sense tap take the 1.20 mm trunk's only
escape from `R75.2` - and copper on this board only accumulates, so no later pass can give it back.
Section 8's order (trunk first) is what buys the 1.50 mm trunk. Inside the pin field there is no
right fixed order at all: three hand-picked ones each moved the casualty. It is now measured by
binary search once per pass, tightest pin first. And section 9's gate-before-CS is proved on Q3,
where the CS route threads both 0.67 mm gaps and leaves `Q3.2` with no escape on any layer.

### What is left is placement, not routing

Nine of the fifteen open connections failed `NO_LEGAL_ESCAPE` at 0 s - the pad cannot emit a legal
track at any width on any layer before pathfinding is even attempted. **U18 escapes 6 of its 8
signal pins here, 7 at best**, because its whole north row shares one ~2.2 mm corridor between the
package and the R76/R77/R78/R79 divider wall. That is **PR-25**, and it needs a placement ruling
rather than another routing attempt. Section 11 forbids weakening the architecture to finish, so
nothing was dropped, re-aimed or re-valued.

**B-34 is not recalculated authoritatively and stays OPEN.** **PM-2 does not close.**

## 2026-08-24 - width becomes a path role, and the board still says no (FBV2-P2-002C)

**FBV2-P2-002C = FAIL.** Phase A did not complete, so Phase B never ran and
`aqroot-Beta-v2.kicad_pcb` is byte-identical to `a52977e`: zero tracks, zero signal vias. PCB
routing stays 0 %, overall stays 74 %. Full analysis:
[`audits/2026-08-24-p2-battery-authoritative-route.md`](audits/2026-08-24-p2-battery-authoritative-route.md).

**First unresolved connection: `LTC_GATE` `Q2.2 -> TP17.1`.**

### D-249: width is a path role

D-245 said `BAT_PROTECTED_P` should be 1.50 mm because it is the one long high-current run. That is
still right. What was wrong is that the rule said it about the NET NAME, and the same net also feeds
the MAX17048 fuel-gauge sense input, the LTC4368 VOUT sense input and a test point - none of which
carries load current, and none of whose land patterns can accept 1.20 mm. **As written, D-245 made
the net unroutable.**

The replacement keeps the trunk floor on the whole net and relaxes it ONLY inside a named rule area
that bounds one approved branch, through `enclosedByArea()`, which requires the WHOLE track to be
inside. A branch that wanders out of its area is measured against the trunk floor and fails.

**Where those rules live turned out to matter as much as what they say.** Section 9 of `.kicad_dru`
already records that KiCad applies the LAST matching rule and that the necking and land-pattern
blocks must sit at the end. Put the path-role rules in section 5b and they are silently overridden
by *"Pad-escape necking - width, fine-pitch power packages"* - which is exactly the trap section 9
was written to warn about. They now live in a new **section 10b at the very end**, widest first and
narrowest last so that overlapping areas resolve to the lower floor instead of a false violation.

### U11.2 did not need the 0.19 mm exception

Section 6 authorised dropping to 0.19 mm if 0.20 mm proved impossible. It is not impossible.
**TI's own DLH0010A land pattern is 0.2 mm pads on 0.4 mm pitch**, so 0.20 mm is the widest copper
that can ever leave that pad - the package is the bottleneck, not the rule - and JLCPCB's live
capability page gives 0.09 / 0.09 mm on 1 oz multilayer, so nothing here is fab-limited. The earlier
"0.195 mm" was an artefact of the router subtracting half a sampling step; with exact
segment-to-shape geometry the answer is **exactly 0.200 mm**.

The measured escape: **0.20 mm for 0.575 mm**, then 0.30, 0.40, 0.60, 0.80, 1.00 and 1.20 mm,
reaching the 1.50 mm trunk 5.079 mm from the pad. No via, no thermal relief, about 4.3 mOhm.

**One part of section 6 is NOT met and is flagged rather than smoothed over.** The neck complies at
0.575 mm against the 1.00 mm cap, but the copper BELOW the 1.20 mm trunk floor runs 4.738 mm. It
cannot be shorter: the nearest point to U11.2 that admits 1.20 mm *and is reachable from the rest of
the net* is 2.511 mm away.

### U14 misses 0.20 mm by five microns

`U14` sits 1.245 mm from the west board edge with its pin row facing that edge. Copper must be
>= 0.500 mm from the edge and >= 0.200 mm from pads whose west edge is at x = 0.895, so a track of
width w needs its centre at x >= 0.500 + w/2 AND x <= 0.695 - w/2 - solvable only for
**w <= 0.195 mm**. Section 5 locked 0.20 mm. It routes at **0.15 mm**, the board's own minimum and
1.7x JLCPCB's, carrying a nanoamp sense input. Flagged for ratification.

A related fix caught a violation on the way: the router now insets the board outline by half the
Edge.Cuts stroke, because copper-to-edge clearance is measured to the LINE, not to the outside of
the stroke. That 25 um is what turned a 0.475 mm edge clearance into a caught error rather than a
committed one.

### What routed

Twenty-seven connections coexisting on one scratch board, each gated on project-context DRC with the
In1 plane refilled every time: the `BAT_PROTECTED_P` trunk `R75 -> D9 -> U11.2` at **94.5 mm,
1.50 mm, B.Cu, ZERO vias**; `BAT_CONNECTOR_P`, `BAT_RAW` and `BAT_MID` at 0.80-1.00 mm; both R75
Kelvin branches at 0.20 mm with zero vias, **7.327 mm on the U18.9 side against 14.588 mm on the
U18.8 side, mismatch 7.261 mm**, both taken directly off the correct R75 pad; the fuel-gauge and
test taps; and three of the six LTC gate connections. Ratsnest 781 -> 749. **Zero new DRC violations
of any class, at every step.**

The only vias in the whole attempt are **four**: the `BAT_SENSE` `Q3 -> R75` trunk and the TP20 stub
hop to F.Cu, because the west margin cannot carry both that trunk and the 1.50 mm
`BAT_PROTECTED_P` past R75 on B.Cu alone.

### B-34 from real copper, and it is worse

Routed copper is **~75.0 mOhm**, not the ~50.6 mOhm the estimate assumed. With F1 at ~25 mOhm,
Q2+Q3 at ~46 mOhm and the BQ25185 BATFET at 115 mOhm the path is **~392 mV / 588 mW at 1.5 A** and
**~457 mV / 800 mW at 1.75 A**. The trunk is at its ruled 1.50 mm; the excess sits in `BAT_MID` and
`BAT_SENSE`, which the corridors forced to 0.80 mm instead of the 1.00 mm class target.
**B-34 stays OPEN - physical validation required.**

### And one weakness worth naming

Section 7 asked that the construction make it IMPOSSIBLE for a long high-current run to masquerade
as a branch. It does not fully manage that yet. The bounded areas are generated from each routed
branch's own bounding box, and three of them are tight - but the C58 decoupling tap's box is
**67 x 23 mm at a 0.80 mm floor**, which is a real hole in the trunk rule. The fix is to build the
area from the route's centre-line rather than its bounding box. That is a router change, not a rule
change, and it is carried as PR-11.

---

## 2026-08-24 - the router on trial, and a rule that cannot be routed (FBV2-P2-002B)

**ROUTER HARNESS QUALIFICATION = PASS.** No copper was committed; the authoritative PCB is
byte-identical to `8b9efba`, zero tracks, zero signal vias. PCB routing stays 0 %, overall stays
74 %. Full evidence:
[`audits/2026-08-24-routing-harness-qualification.md`](audits/2026-08-24-routing-harness-qualification.md).

### The scratch environment, first, because that was the last task's real bug

FBV2-P2-002A spent an entire routing attempt reading a phantom `clearance: 73,
lib_footprint_issues: 17` offset on every net. The cause: a `.kicad_pcb` copied on its own loses
`.kicad_dru`, the `.kicad_pro` netclasses and `fp-lib-table`, and DRC then silently measures against
KiCad **defaults**. Every board in this task is a **complete copy of the whole project directory**,
and the harness refuses to run DRC unless all five of those are present beside it. Required proof
holds exactly: authoritative and scratch baselines are both
`{solder_mask_bridge: 1, unconnected_items: 499}`. **Phantom DRC offset: none.**

### All three defects fixed, and a fourth found

**`track_dangling`** had two causes, and the coordinate one was the smaller. The emitter is now
**integer nanometres end to end**, so a neck's end and a trunk's start are the *same integer* rather
than two floats that agree to a rounding step. But the bigger cause was that **the old router never
checked which layer a pad was on** - it would start a `B.Cu` track at the centre of an `F.Cu`-only
pad, which is a dangling end by construction. That is not hypothetical: **`TP34.1` is an `F.Cu`-only
pad on the otherwise-`B.Cu` net `BAT_CONNECTOR_P`.**

**`track_width`** is now governed by one rule: **the routing rule minimum wins.** The escape width
ladder starts at the trunk width and stops at the applicable floor. It never derives a width from a
pad's short dimension. If nothing at or above the floor can leave the pad, the pad is classified
**NO LEGAL ESCAPE** and **nothing is emitted**.

**`shorting_items`** is fixed by giving the neck the *same* obstacle set as the trunk - foreign pads
as true rotated rounded rectangles rather than bounding boxes, tracks as capsules, every drilled
hole on every layer, rule areas, the board edge - and checking it **analytically**, so a short neck
gets a stricter test than the trunk rather than a weaker one.

**And a fourth defect that was not on the list.** A* proves that *grid cells* are clear; the emitted
track is a *continuous segment* between them and can pass three-quarters of a cell closer to an
obstacle than either endpoint. It duly produced `actual 0.1718 mm` against a 0.2000 mm rule. Every
obstacle now carries a **0.75 x grid guard band**. The price is honest: `R86.2 -> R89.1` no longer
fits at 0.05 mm and needs the local 0.025 mm grid.

### Six of eight cases route clean

`Q2_CS` 5.500 mm, `Q3_CS` 5.500 mm, `BAT_MID` 24.860 mm, `LTC_GATE` 66.982 mm, `LTC_OV` 15.179 mm,
`R86.2 -> R89.1` 45.274 mm. Each on its own fresh project-faithful copy, each with **zero** new DRC
violations of any class, **one** connected copper component after a real save and reload, **no**
foreign pad in the cluster, and the ratsnest falling by **exactly one edge per connection**.

### The two that did not are a rule conflict, and it is the finding of the task

Five pads cannot legally accept the width their rules demand. Bisected to 5 um against the
project's own clearances, and the closed-form arithmetic matches to the bisection step:

| pad | package | floor | widest legal escape |
|---|---|---|---|
| `U18.9` | MSOP-10, 0.50 mm pitch | 0.600 mm | **0.245 mm** |
| `U18.8` | MSOP-10, 0.50 mm pitch | 1.200 mm | **0.245 mm** |
| `U14.2` / `U14.3` | T822, 0.50 mm pitch | 1.200 mm | **0.295 mm** |
| `U11.2` | WSON-10, 0.40 mm pitch | 1.200 mm | **0.195 mm** |

**The problem is rule scope.** `BAT_MAIN`'s 0.60 mm floor and D-245's 1.20 mm floor are written as
**whole-net** constraints, but `BAT_SENSE` is a Kelvin sense line carrying microamps, and
`BAT_PROTECTED_P` carries the pack current *and* feeds the MAX17048's fuel-gauge sense input and a
test point, neither of which carries any current at all. D-245's comment already anticipates a neck
exception; **the rule body does not contain one**, so **as written D-245 makes `BAT_PROTECTED_P`
unroutable.** Section 6 said not to invent an exception and section 17 said not to hide it by
weakening rules. **Nothing in `.kicad_dru` was touched.** It is PR-7, and it needs a ruling.

### What the 1.50 mm trunk actually costs

`R75.2 -> U18.8 -> D9.1 -> C25.1` routes at **1.50 mm in 85.274 mm, 22 segments, B.Cu, ZERO vias**,
every segment at full width except the two mandatory 0.245 mm `U18.8` escapes. Past `C25.1` the
charger cluster caps the trunk at 0.60 mm and `U11.2`'s own land pattern caps it at 0.195 mm.

**And D-245's arithmetic needs correcting.** It used the **71 mm placement span**; the measured
route is **85.3 mm**, because copper goes around things. With the unavoidable `U18.8` neck at
7.8 mOhm in 3.9 mm of copper, `BAT_PROTECTED_P` as actually routable is **~35.7 mOhm**, so the net
gains **~6 mOhm rather than the predicted ~11.7 mOhm**. That does not argue against D-245 - it
argues that the neck exception, when ruled, should carry a bounded length and a stated resistance
budget.

### No placement was moved, and none needed to be

`R86.2 -> R89.1` routes legally at 1.00 mm (45.274 mm) and at 0.60 mm (16.848 mm). `TP15.1 ->
U14.2` routes legally at 0.20 mm (8.82 mm) - it was never a geometry problem, so **moving `TP15`
would not have helped and `U14` was never a candidate.** The <= 2.0 mm allowance was not spent.

### Also landed

**`hardware/beta-v2/checks/router_regression.py`** - 22 assertions across six guards, building and
removing its own throwaway project-faithful workspace, and **pinning the five proved land-pattern
conflicts by their exact widths** so that relaxing a rule or moving a part fails the test instead of
passing silently. **ALL CHECKS PASS.** The router is committed beside it as `qrouter.py` so the two
cannot drift apart.

**Opportunity scan (section 19): no native installed routing mechanism exists.** `kicad-cli pcb` has
no routing subcommand, `pcbnew` exposes no scriptable PNS, `kipy` is not installed, and Freerouting
is not installed - and would be the wrong tool anyway, since Specctra DSN carries netclass width and
clearance but **not** custom `.kicad_dru` rules, so D-245 and the rule areas would be invisible to
it. **Keep the qualified harness.**

---

## 2026-08-24 - a router that refuses to keep bad copper (FBV2-P2-002A)

**FBV2-P2-002A = FAIL. The battery / protection block is NOT routed.** No progress; PCB routing
stays 0 %, overall stays 74 %. Full analysis:
[`audits/2026-08-24-p2-battery-protection-routing.md`](audits/2026-08-24-p2-battery-protection-routing.md).

**The board still carries zero tracks and zero signal vias.** Two of twenty-nine nets came out
DRC-clean; the other twenty-seven were reverted automatically, and the two clean ones went with
them rather than be committed as an unrepresentative fragment.

### The deliverable is the method, and that was the point

FBV2-P2-001 failed because a minimum-spanning-tree router drew straight lines through other pads
and produced 505 violations. Section 4 of this task forbade that class of approach outright. What
replaced it:

**Obstacle-aware A\* on a 0.10 mm grid**, rebuilt per connection from the real board - every
foreign pad, every track already laid, every track-forbidding rule area including the one embedded
inside `U1`'s own footprint, and the board edge, each inflated by (clearance + width/2) so that a
legal path on the grid is a legal track on the board.

**Pad-escape necking**, because a 1.00 mm `BAT_MAIN` trunk physically cannot land on `U18` - an
MSOP-10 on 0.50 mm pitch whose pad-to-pad gap is **0.20 mm**. That is also why the first run
reported "NO PATH" on a 2.44 mm hop: the destination was genuinely unreachable at trunk width,
which is a property of the land pattern rather than a bug.

**Per-net DRC gating.** After every net the board is saved to its own path - so DRC sees the
project's own `.kicad_dru` and netclasses, which a scratch-file approach did not - and any new
violation of any class reverts that net before the next one starts. Violations never accumulate.

That last property is the one that matters: **the router refused to keep anything unclean, and the
result is a board with no copper on it rather than a board with hidden shorts.**

### Three defects remain, and all three are named

**`track_dangling` on seventeen nets** - the escape neck and the trunk do not register as joined at
the launch point. A geometry bug in the emitter, not an electrical problem, but a dangling end is
exactly what must never be committed. **`track_width` on `BAT_MID` and `BAT_SENSE`** - the neck
width is taken from the pad's short dimension and on an SO-8 that falls below the `BAT_MAIN`
0.60 mm floor; **the rule is right and the router is wrong.** **`shorting_items` on six nets** - the
neck is laid without consulting the obstacle grid, so it can cross a neighbour even where the trunk
cannot.

None of them is a reason to change placement, widths or topology.

Two connections have no path at trunk width at all - `R86.2` to `R89.1` and `TP15.1` to `U14.2`,
both in the dense left-margin resistor column. They need either a finer routing grid there or a
2 mm placement nudge, and per section 9 that is **surfaced rather than taken**.

### D-245: one net gets a wider trunk, and only one

`BAT_PROTECTED_P` now has a **scoped per-net override - 1.50 mm target, 1.20 mm floor** - added to
`.kicad_dru` and as row A2 of the ledger. **The `BAT_MAIN` class is untouched**: the other four
battery nets keep 1.00 mm / 0.60 mm, because none of them carries the pack current over anything
like the same distance.

The arithmetic is the whole justification. At about 71 mm this net is **about 69 % of the entire
protection path's copper resistance on its own** - 34.9 mOhm at 1.00 mm against 23.3 mOhm at
1.50 mm - taking path copper from about 50.6 to about 38.9 mOhm and the 1.5 A copper loss from 114
to 88 mW.

The neckdown allowance that comes with it is written as a policy, not a loophole: shortest length
that clears the package, never a traverse, length and width documented per pad, no thermal-relief
or single-via bottleneck. **The 1.20 mm figure is the trunk floor, not a licence for a narrow run.**

### B-34, with the unit confusion corrected

The FBV2-P2-001 write-up's copper figure is **about 50.6 mOhm**, not 525 mOhm. With `F1` about
25 mOhm, the two FETs about 46 mOhm and the BQ25185 BATFET's **115 mOhm**, the path is **about
355 mV / 532 mW at 1.5 A** and **about 414 mV / 724 mW at 1.75 A**. Nothing is clearly unsafe.
**B-34 stays open - physical validation required**, and D-245 takes the copper term to about
38.9 mOhm once the net is actually routed.

**PM-2 does not close.** Its placement correction is approved and retained; closure still waits on
DRC-clean routing, which is what it always said it would.

---

## 2026-08-24 — the ground plane, and a routing attempt that was reverted (FBV2-P2-001)

**FBV2-P2-001 = FAIL. The power tree is NOT routed.** No progress; PCB routing stays 0 %, overall
stays 74 %. Full analysis:
[`audits/2026-08-24-p2-power-routing.md`](audits/2026-08-24-p2-power-routing.md).
New working document: [`pcb/FBV2_P2_POWER_ROUTING.md`](pcb/FBV2_P2_POWER_ROUTING.md).
Pre-routing checkpoint tag **`beta-v2-p2-entry-pass` → `faa0c91`**, annotated and pushed.

**The board still carries zero tracks and zero signal vias.** What it gained is the In1.Cu ground
plane and two corrective placement passes that the routing exposed as prerequisites.

### The ground plane exists, and the regression now knows what it is

In1.Cu is one zone, **one island**, net GND, **9938.9 mm² of a 10656 mm² board — 93.3 %**, with a
solid pad connection and no thermal relief. No split, no analog island, and its single authorised
void — the ESP32 antenna keep-out — is cut by the four-layer rule area that already existed rather
than by a polygon carved by hand. F.Cu and B.Cu pours were deliberately **not** created: they are
the last step of FBV2-P2, and making them now would hide return paths rather than prove them.

`p1_regression.py` had a blanket *"0 fills"* expectation, which was right when nothing was allowed
to exist and wrong the moment a reference plane did. It now checks **0 tracks / 0 vias / 0 outer
pours**, and separately that **In1 is exactly one GND zone of exactly one island** — so a split
reference is a gate failure instead of an invisible mistake.

### PM-2 was closed on incomplete evidence, and the routing is what found it

FBV2-EXP-002 reported PM-2 closed on the chain: `J4 → F1 → Q2 → Q3 → R75 → U18`, 30.86 mm, Kelvin
6.60 mm. **That measurement was real and it is not withdrawn.** But it was reported as though it
closed the whole of PM-2, and it did not. The trip/gate and dead-cell support parts had been packed
into regions chosen while the chain still sat in the right column, and were never re-homed when the
chain moved. Measured on `faa0c91`, before this task touched anything: **`LTC_GATE` — a ≈ 20 µA
charge-pump node holding four pass FETs enhanced — spanned 70.4 mm.** `BAT_SENSE` 61.4. `REF_POL`
51.7. `REC_GATE_N` 50.6.

Routing those as they stood would have knowingly built the defect PM-2 exists to prevent, so the
support network was moved beside the chain it belongs to: **`LTC_GATE` 70.4 → 29.8 mm, `BAT_SENSE`
61.4 → 24.3, `REF_POL` 51.7 → 9.7, `REC_GATE_N` 50.6 → 15.6, `N_POL` 46.4 → 8.3, `LTC_OV`/`LTC_UV`
28.2/15.0 → 8.0/9.1.** No component value, no threshold, no topology and no net changed, and the
1.5 A chain itself did not move.

Twenty-nine power test points moved too. A test point 50 mm from its own net is not access, it is a
stub — and on a 1.5 A net it is a stub that forces load current somewhere it should not go. `TP34`
was 59 mm from `J4`; it is now 4.4 mm.

### Why the routing failed, said plainly

The first router computed a minimum spanning tree over each net's pads and drew each edge as a
direct segment. Inside a compact PM-1 cell that is adequate. Across a board it is not: **it draws
straight lines through other pads.** On 64 nets it produced **505 DRC violations — 102 shorting
items, 112 track crossings, 204 solder-mask bridges, 45 clearance.**

It was reverted in full. Committing 102 electrical shorts into the authoritative board, on the one
task whose subject is the *safety-critical* battery path, was not a defensible option — and a
partial pass would have been the asserted-rather-than-measured progress this file's own rules exist
to prevent. What the next task needs is an obstacle-aware path search or verified hand polylines;
the scope, the widths, the layer policy and the intended topology are all already settled and
written down, so none of that has to be re-derived.

### B-34, recomputed and still open

From the *intended* geometry at ledger widths — **an estimate, not a measurement, and labelled as
one**: copper 50.6 mΩ, fuse ≈ 25 mΩ, the two FETs ≈ 46 mΩ, and the BQ25185 BATFET's **115 mΩ**
dominating. **≈ 355 mV / 532 mW at 1.5 A; ≈ 414 mV / 724 mW at 1.75 A.** Nothing there is clearly
unsafe, so the escalate-and-halt condition did not fire — but an estimate from an unrouted board
cannot close a blocker, so **B-34 stays open, physical validation required.**

One number dominates: `BAT_PROTECTED_P` at ≈ 71 mm is **69 % of the copper resistance on its own**.
Widening it 1.00 → 1.50 mm takes the copper to 38.9 mΩ, at the cost of board area on a face that
has it.

### E-7 closed, with the wording corrected

**The battery envelope is 57 × 75 × 8.0 mm and that is a MAXIMUM reserved envelope.** 57 mm is not
a minimum cell width and not "the lower bound of what fits" — the EXP-002 phrasing was wrong and is
withdrawn. Both verified candidates are 50 mm wide. **The envelope is not shrunk to 50 mm:** the
unused 7 mm preserves alternate- and future-cell flexibility at zero current placement cost, and
reclaiming it would spend the only tolerance the design has against a different cell.

---

## 2026-08-24 — the header, the cell, and the three moves done once (FBV2-EXP-002)

**FBV2-P1 RE-ISSUED = PASS. FBV2-P2 ENTRY = PASS. PM-1, PM-2, PM-3 and PT-1 all CLOSED.**
**No progress earned; overall stays 74%.** Full analysis:
[`audits/2026-08-24-expansion-and-refloorplan-implementation.md`](audits/2026-08-24-expansion-and-refloorplan-implementation.md).
New library part: `Samtec_SSQ-124-02-G-S-RA.kicad_mod`.

**ZERO SIGNAL ROUTING.** 0 tracks, 0 signal vias, 0 electrical copper pours, 499 unrouted.

### The battery gate ran first, and it made the headline claim wrong in the good direction

Nothing authoritative was touched until the 57 × 75 × 8 mm envelope had been checked against cells
somebody can actually buy. Two, from manufacturer datasheets rather than marketplace listings:
**PKCELL `LP785060`** — 7.3 × 50 × 60 mm, 2500 mAh typical / 2375 minimum, PCM fitted with a ≈ 2.8 V
cut-out, ships on a genuine 2-pin JST-PH — and **`LP755070`** — 7.5 × 50 × 70 mm, **3000 mAh
minimum**, PCM fitted at 4.275 V ± 50 mV overcharge with a 2.50 V resume, 500 cycles to 80 %,
0–45 °C charge.

EXP-001 predicted a ≈ 5 % capacity penalty from scaling the volume. **That penalty does not
materialise, and saying so is the point of running the gate: both candidates are 50 mm wide, so the
57 mm limit binds neither of them, and `LP755070` lands at the TOP of D-071's 2500–3000 mAh
target.** The envelope was always larger than the cells that fill it. The capacity target is
unchanged, and the one new item this task raises is the mirror of that finding: **7 mm of the
reservation is now unused** (E-7), which is either reclaimable area or tolerance for a wider cell —
recorded, not decided.

### What was built

`J5` becomes a **Samtec `SSQ-124-02-G-S-RA`**, a 1 × 24 2.54 mm female right-angle socket —
**the same manufacturer as the `BCS-112-S-D-HE` it replaces**, so the account and the small-quantity
behaviour are already known. Body 61.47 mm, pin span 58.42 mm, mates a **.025″ square post**, which
is the ordinary male-header and Dupont standard. `J8`, a **`JST SM04B-SRSS-TB`** Qwiic / STEMMA QT
connector, joins it — **SMT and machine-placed**, so the manual-assembly list stays at two parts.

**All 24 electrical functions are retained and not one protection component was removed.** Twelve
100 Ω GPIO resistors, the 22 Ω I²C pair, the 330 Ω WAKE resistor, four TVS arrays, the TCA4307, both
load switches, the boost, the FLT wire-OR, the `Q10` WAKE gate and the `ACC_DETECT_N` protection are
all present and electrically identical. **The schematic change is a footprint swap plus a pin re-map
on one sheet — no net was created, deleted, split or merged.** The old 2 × 12 footprint stays in the
library: Beta-DM uses it, and it is the fallback if the owner ever reverses this.

Qwiic costs **zero components**. It taps `EXT_SDA` / `EXT_SCL` — downstream of the TCA4307 and the
22 Ω pair, at `D2`'s clamp, the same node as the header — so it inherits the buffer, the pull-ups,
the series resistance and the ESD array. Its power is `ACC_3V3_SW`, and that is architectural rather
than tidy: **`U16`'s own VCC already is**, so an unswitched feed would create a powered-device /
unpowered-bus state. `ACC_5V_SW` is not on it and cannot be.

### ORDER-B, because ORDER-A was safe against the wrong failure

ORDER-A protected against a one-position slip. It did not protect against someone turning the
accessory around. **ORDER-B is symmetric by construction**, so a full 24-pin accessory inserted
180° maps 5V↔5V, GND↔GND, 3V3↔3V3, and 3.3 V logic to 3.3 V logic on every remaining contact.
**Power-to-signal maps under reversal: zero** — proved pin by pin from the exported netlist, not
argued.

The lateral slip stays impossible for the same reason it always was: a mating male body is exactly
60.96 mm, the closed-end recess is 62.5 mm, and 1.54 mm of play against a 2.54 mm pitch is 61 % of
one position. **A pleasant consequence: D-097's asymmetric upper-edge key is no longer needed.**

### The board grew symmetrically, and one reservation turned out to be fiction

70 → 72 mm, **1.0 mm on each side**, so every part shifted +1.0 mm in X and **every part-to-part
relationship on the board is preserved exactly.** Only the edge margins moved, to 1.5 mm on both
sides — the ≥ 1.5 mm rule met exactly, with nothing to spare. The 80 × 160 × 23 enclosure is
untouched.

That last "nothing to spare" exposed something. `ANT433_REGION` was 2.2 mm wide, and 2.2 mm does not
fit inside a 1.5 mm gap. **It never described anything real:** the 433 flex is **0.28 mm thick** and
bonded flat to the cavity wall, so it projects inward by its thickness, not by 2.2 mm. The region is
now re-derived from the part at X −1.40 … −0.60, with 0.6 mm of air to the board edge.

And 3 mm of cell width is the entire price of the interface. A right-angle socket puts its tails
**6.53 mm inboard of its own mating face** — it has to, because it must swallow a 6 mm post — so the
requirement is (board right edge − cell right edge) ≥ 7.83 mm, against 4.00 mm before. Measured
result: tail row at X 65.900, **1.100 mm clear of the cell**, mating face 0.430 mm outboard of the
board edge with **1.070 mm to the wall** for the recess lip.

### Three placement moves, done once

**PM-1.** Converter IC-to-inductor spans fall from 12.96 / 28.56 / 30.50 / **45.90 mm** to
**4.80 / 4.34 / 3.86 / 3.79 mm**. But the brief was explicit that moving the inductor and leaving
the caps remote does not count, so each converter was rebuilt as a **complete power cell** in
electrical order. The clearest case: `D8`, the backlight catch diode, sat **45.7 mm from its own
inductor**; it is now 3.56 mm from `U17` and adjacent to `L3` and `C44`, so the loop that switches
to 39 V on an open-LED fault is local instead of a 76 mm perimeter running 13 mm from the
microphone.

**PM-2.** The 1.5 A protection path goes from **116.7 mm to 30.86 mm** as one monotonic column —
`J4` → `F1` → `Q2` → `Q3` → `R75` — with the Kelvin pair at 6.60 mm. **No FET, no threshold, no
divider value and no recovery branch was altered. D-049 is untouched.** One part could not join the
column and that is recorded rather than hidden: the left margin is also the mandatory 915 coax lane,
which parts ≤ 2.0 mm may share because the cable lies over them, but a **5.75 mm JST-PH with a
mating cable** cannot. `J4` therefore sits at the head of the column, north of the coax's western
excursion, 8.59 mm from `F1`.

**PM-3.** The NFC arms are mirrored about y = 118.000 at **Δx = 0.000 mm and arm-length Δ = 0.000
mm** — same topology, same orientation, same stage order, every pair equidistant from the axis. The
crystal's load capacitors moved from 13–15 mm away on the far side of the IC to beside `Y1`, which
is now 5.40 mm from `U9`. No locked NFC value changed.

**PT-1.** `U11` is out of the battery shadow, 3.5 mm clear of the cell, so its ≈ 0.65 W of charging
dissipation spreads into copper with nothing behind it.

### B-34 improves, and does not close

The brief said not to claim routing losses are zero, so: at 1 oz and 1.0 mm the protection-path
copper falls from **38.8 mΩ** (58 mV / 87 mW at 1.5 A) to **15.2 mΩ** (23 mV / 34 mW) — about 53 mW
better at 1.5 A and 72 mW at 1.75 A. **That is a material improvement and it is not a closure.**
B-34's ≈ 0.70 W is dominated by the BQ25185 BATFET's 115 mΩ and the FET R_DS(on), neither of which
this task should have touched. The copper share of the figure falls from roughly 17 % to 7 %.

### The rest

`BOOT` moved to the bottom band on the **front** face — it is an SMD switch whose actuator faces out
of the front shell, so its Ø2 mm service hole goes in the front wall and is therefore clear of both
the microSD card path and the USB-C plug envelope. **Lower-left was rejected on RF**: that wall *is*
the 433 flex region and the mandatory coax channel. `POWER` stays on the right wall. Retention is
still two M2 — **widening the board did not buy a third, and none was chased.**

Some numbers improved for free: NFC loop to `J5` metal **5.490 → 9.155 mm**, the NFC cable pair
**41.73 → 31.23 mm**, and the display's off-centre offset **3.34 → 2.34 mm**, because symmetric
growth halves it.

**DRC 26 → 1.** The single survivor is the `MK1` netless-NPTH-inside-its-own-GND-ring artefact
accepted at D-227 — still not excluded and still not suppressed. **ERC 0 errors / 27 warnings,
histogram identical. 499 unrouted. Zero placement collisions.** `p1_regression`, `dru_probe`,
`netclass_probe` and `fork_equivalence` all pass.

One check had to be taught something: **`J5`'s courtyard legitimately overhangs the right edge by
0.975 mm.** That is what a right-angle socket is *for*. `p1_regression.py` now measures the mating
face against the wall gap explicitly instead of counting it as a part that has fallen off the board.

---

## 2026-08-24 — the connector fits the users, not the board (FBV2-EXP-001)

**AUDIT = PASS. AUDIT ONLY — no authoritative hardware changed, no progress earned; overall stays
74%.** Full analysis:
[`audits/2026-08-24-expansion-compatibility-audit.md`](audits/2026-08-24-expansion-compatibility-audit.md).
New working document:
[`architecture/EXPANSION_ECOSYSTEM_PROPOSAL.md`](architecture/EXPANSION_ECOSYSTEM_PROPOSAL.md).

**`J5` is unchanged, no sheet was opened, the PCB blob is byte-identical to `HEAD`, no Qwiic
connector exists, `BOOT` and `POWER` have not moved and no PM part moved.** D-081 / D-083 / D-093 /
D-097 remain in force; the proposed supersession is marked **PENDING CTO / OWNER RULING**.

### The answer is yes, and the price is 3.83 millimetres of battery

The owner's intent — ordinary 2.54 mm female sockets down the right side, one pin per line, Dupont
jumpers, Qwiic boards that just plug in — is achievable, and **the electronics behind the connector
need no architectural change whatsoever.** Every series resistor, every TVS array, the TCA4307, both
load switches, the boost and the FLT wire-OR stay exactly as they are. The schematic change is a
footprint swap and a pin re-map on sheet 09.

What does not work is the geometry, and the reason is specific rather than vague. **A right-angle
through-hole socket puts its solder tails 6.5–6.9 mm inboard of its own mating face** — it has to,
because it must swallow a 6 mm male pin. For the mating face to reach the right wall, the tail row
lands at x ≈ 63.5, and that is **inside `BATTERY_SHADOW`, which forbids any through-hole lead.**

> **Requirement: (board right edge − battery right edge) ≥ 7.83 mm. Today it is 4.00 mm.
> Shortfall 3.83 mm.**

Above the battery, where the lead rule does not apply, the right wall offers **41.00 mm** between the
cell and the IR receiver's optical corner. A 1 × 24 body is **61.47 mm**. The largest socket that
fits there is a **1 × 15**, and it would leave nothing for the Qwiic connector or the power switch.
Every other edge was measured and rejected: the left wall **is** the 433 flex region and the mandatory
915 coax channel, the bottom edge is microSD, USB-C and both radio modules, and the top edge is the
IR pair, the opaque barrier and the SMA. Mounting the socket on the rear face moves the conflict from
its leads to its body and gains nothing.

So the recommendation carries two conditions and they are the owner's to take: **PCB 70 → 72 mm**,
which is *already* the documented `FBV2_PCB_MAX_MM` and leaves the 80 × 160 × 23 shell untouched, and
**battery 60 → 57 mm wide — about 5 % of capacity.** With both, the margin is +1.17 mm and the wall
carries the header, the Qwiic connector and the power switch. **Without the battery change the
24-line side header cannot be delivered in this enclosure, and `J5` stays as it is.**

### Two 1 × 12 sockets are rejected on arithmetic, not taste

Both Samtec and Sullins build a 2.54 mm socket body **N × 2.54 + 0.51 mm** long — 1.525 mm of
insulator past the end contact at each end. Butt two of them and their end contacts sit **3.050 mm
apart against a required 2.540 mm pitch: a 0.510 mm interference.** They cannot form a continuous
24-position grid at all. They also need **5.59 mm more wall length** than the single 1 × 24, need two
recesses, and introduce a mis-plug mode the 1 × 24 does not have — a 12-way accessory in the wrong
group. **One 1 × 24. Not two 1 × 12.**

### The parts, verified

**`SSQ-124-02-G-S-RA` (Samtec)** — and Samtec is *the same manufacturer as the present `J5`*, so the
account and the small-quantity behaviour are already known. From the SSW/SSQ datasheet: 01–50
positions per row, `-S` single row, `-RA` right angle available with `-S`, body 61.47 mm, socket-axis
height selectable by lead style, insertion depth 3.68–6.35 mm, **mates .025″ (0.635 mm) square post**
— the Dupont standard — 6.3 A per pin, −55 to +125 °C, 100 cycles at 10 µin Au.

**`JST SM04B-SRSS-TB(LF)(SN)`** for Qwiic — SH series, **1.0 mm** pitch confirmed from JST's own
`eSH.pdf`, 4 circuits, side entry, SMT, 6.0 × 4.25 mm, 1.0 A, 50 V. Pin order is the ecosystem's, not
a choice: **1 GND, 2 3.3 V, 3 SDA, 4 SCL.**

**Sullins `PPTC241LGBN-RC` was verified and deliberately not baselined.** Its drawing is
authoritative and supplied the 6.53 mm depth figure the whole audit turns on — but DigiKey lists the
non-RC variant obsolete at 0 stock, and the 19-way sibling is factory-order only at 1,000 pieces and
11 weeks. **That is the third time this programme has met a catalogue part that is not a stocked
part**, after the Harwin `M20-7881242` and the Amphenol `095-902-568-100`. D-096 keeps earning its
keep.

### Three things confirmed rather than assumed

**Qwiic costs zero components.** It attaches at `EXT_SCL`/`EXT_SDA` — downstream of the 22 Ω
resistors, at `D2`'s clamp, the same node as the header — and inherits the hot-swap buffer, the
1.5 k pull-ups, the series resistance and the ESD array. Its power is `ACC_3V3_SW`, and that is
architectural rather than preferential: **`U16`'s own VCC is already `ACC_3V3_SW`**, so an unswitched
`+3V3` feed would create a powered-device / unpowered-bus state. `ACC_5V_SW` is never exposed.
Three daisy-chained boards on 100 mm cables come to roughly 55–75 pF against a ≤ 200 pF budget —
**no mux, no repeater, and none should be added.**

**A Manual / Bench power mode needs no hardware change for either rail.** Traced pin by pin:
`ACC_DETECT_N` goes through `R64` to `R129` and `U3.P17` and **nowhere else** — there is no AND gate,
no interlock and no bypass between it and the three enables. Detect gating is one hundred percent
firmware policy, while ILIM, reverse-current blocking, thermal shutdown and `FLT` stay in hardware,
and permanent 5 V remains physically impossible because both 5 V enables default OFF through 100 k
pull-downs. B-35 is carried forward unchanged: `FLT` still does not assert on plain current limiting,
which is exactly why bench mode needs its warning.

**BOOT can move without compromising anything.** `SW1` is **SMD**, and the bottom edge has a measured
**11.04 mm** free window between the microSD shell and the USB-C receptacle, with a **14 mm** free
span of enclosure wall for a Ø2 mm tool hole. **Lower-left is rejected on RF**: that wall *is*
`ANT433_REGION`, with the flex bonded 0.2 mm outboard of the board edge, and it is also the mandatory
`COAX_915_CHANNEL` — and P2-R1 already flags board copper in exactly that band as an aggressor.

### The pin order removes two hazards it did not have to

**ORDER-A** puts `3V3 / SDA / SCL / GND` at pins 3-4-5-6 — the same block every maker already knows
from Qwiic — and puts **both 5 V contacts at the two physical ends of the row, each with `GND` as its
only inboard neighbour.** No 5 V pin is adjacent to any signal. The present order has two such
adjacencies. A one-position slip from either 5 V pin now lands on ground: a current-limited short
with `FLT`, not 5 V into a 3.3 V input. All 24 functions are retained exactly — nothing added,
removed or merged.

And the mis-alignment problem turns out not to need a proprietary shroud at all. A mating 1 × 24 male
body is exactly 60.96 mm; a **closed-end recess 62.5 mm long** leaves **1.54 mm of play against a
2.54 mm pitch**, so a one-position shift is physically impossible. **The asymmetric upper-edge key of
D-097 becomes unnecessary.**

### What it costs, said plainly

A single row has **no roll couple** — the 2 × 12 has 7.87 mm of it, which is the direction a
leaned-on accessory actually loads a connector. In yaw the 1 × 24 is 2.09× better, but that is not the
direction that matters. The mitigation is non-electrical: the recess floor, its closed ends, and a
moulded ledge for the accessory board to rest on. **No new electrical connector, no new fastener, and
the manual-assembly list does not grow — the Qwiic part is SMT and machine-placed.**

And **two official full-header accessories should not be stacked.** One at a time; a second board
uses Qwiic or jumper wires. **No AQROOT hub is required and none should be built.**

### Do it once

PM-2's fix is to consolidate the battery-protection block at the battery-entry corner — **exactly the
corner the 1 × 24 now wants.** Deciding the connector separately from PM-1 / PM-2 / PM-3 / PT-1
guarantees a second full placement cycle. The audit therefore ends with a combined sequence: rule on
the changes, fix the outline and the reservations, place the right-wall stack, then PM-2, PT-1, PM-1,
PM-3 and P2-R1 — and **re-issue FBV2-P1**, because a 70 → 72 mm outline change invalidates its PASS.

---

## 2026-08-24 — twenty-two rules that could never fire (FBV2-P2-000)

**FBV2-P2 ENTRY GATE = FAIL on one criterion of thirteen. No progress earned; overall stays 74%.**
Full analysis: [`audits/2026-08-24-p2-entry-audit.md`](audits/2026-08-24-p2-entry-audit.md).
New working documents: [`pcb/FBV2_P2_ROUTING_PLAN.md`](pcb/FBV2_P2_ROUTING_PLAN.md),
[`pcb/FBV2_P2_NETCLASS_LEDGER.csv`](pcb/FBV2_P2_NETCLASS_LEDGER.csv).
New check: `hardware/beta-v2/checks/dru_probe.py`.

**ZERO ROUTING WAS PERFORMED.** No track, no signal via, no electrical pour. 499 unrouted,
unchanged. The only PCB edit is one board-level rule area.

### The rule file had been lying, and there was no way to see it

P2-O5 recorded that `.kicad_dru` *"still references E5/E6 rule areas that the P1 rebuild deleted."*
That was true and it was an understatement. **The file referenced thirty-nine rule areas. The board
contained none of them** — only `MIC_ACOUSTIC_KEEPOUT`, `BOSS1_KEEPOUT`, `BOSS2_KEEPOUT` and one
**unnamed** zone embedded in `U1`. **Twenty-two of seventy-one rules could never fire**: not only
the E6 pockets, but every RF-band rule, every E5/E4 corridor rule, the header reservation, the E2
button escapes, **and the ESP32 antenna rule**.

The reason nothing caught it is worth stating precisely, because it will happen again to somebody
else: **KiCad's `intersectsArea()` and `enclosedByArea()` return `false` for an unknown area name.
They do not warn and they do not error.** A rule whose condition can never be true produces no
violations — which is exactly what a rule being satisfied looks like. DRC was reporting a clean
result against protection that had been deleted three tasks earlier.

The ESP32 antenna was never actually unprotected: the `U1` footprint carries its own embedded rule
area with every keepout flag set on all four copper layers, and that has always been live. But the
*file* said the protection came from a named area that did not exist, and **nothing in the
toolchain could tell the difference.**

**The rule set is rebuilt: 71 → 64 rules, every one checked against the current board, with a
written retirement register (R1–R10) in the file header giving a reason for each of the twenty-two
retirements.** Nothing was retired for convenience. Where the intent survived it was re-expressed
against current objects; where the intent died with the Beta-DM geometry, that is stated as a
finding rather than papered over. **The E6 escape-relief doctrine is explicitly NOT retired** —
own-area sufficiency, `enclosedByArea()` never `intersectsArea()`, the 2.0 mm hard clearance-run
cap kept separate from the 6.0 mm narrow-width review trigger, and last-in-file precedence — even
though its Beta-DM measurements do not transfer to a differently sized, differently placed,
unrouted board (D-233).

**`checks/dru_probe.py` is the part that matters.** It fails if any rule reference stops resolving
or any netclass pattern stops matching. P2-O5 cannot recur silently.

### The highest-current net on the board was on the 0.20 mm default class

The inherited `BAT_MAIN` pattern was the root-sheet path `/BAT_PROTECTED_P`, while every Full Beta
v2 power net lives under `/01_POWER_TREE/`. **It matched nothing.** So
`/01_POWER_TREE/BAT_PROTECTED_P` — 1.5 A sustained — had been routing at 0.20 mm since the fork,
and `BAT_RAW`, `BAT_MID` and `BAT_SENSE`, which all carry the full pack current, were in no class
at all. The same defect killed `NFC_5V_PA` outright: it captured **no net whatsoever**. And
`ACC_5V_LX`, the `U21` accessory-boost switch node, had **never** been in `SWITCH_NODE` — a
1.2 MHz switching node sitting on the ordinary signal class.

**14 netclasses → 18; 62 patterns → 57; every surviving pattern now matches at least one board
net.** Four dead classes were retired, all of which either matched nothing or carried Default
values, so no net's electrical parameters were weakened by a retirement (D-234).

### Retention is locked, and D-226's escalation is closed

**Two currently legal M2 through-board screws are acceptable.** No component moved: the battery was
not reduced, the display was not moved, the SMA was not relocated. Retention is a four-element
architecture — moulded edge-capture rails, **four** rear non-metallic support ribs on reserved
component-free pads, the two screws, and the `J5` backing boss carrying its ≈ 33 N insertion load
into the enclosure rather than into solder joints. Every rib is outside the battery shadow, so no
support compresses the cell; every rib is non-metallic and far outside the Ø58 NFC exclusion. USB
and microSD insertion loads do not depend only on the screws — both connectors sit on the bottom
edge, which carries a continuous rail. **All four routes to a third screw are declined** (D-232).

Three stale mechanical-spec entries went with it: *"Count: 6 × M2"*, the `FBV2_BOSSES: 3 x M2 …
PARTIAL` line, and `FBV2_915_PIGTAIL: 095-902-568-100 … DOES NOT REACH`, which D-223 superseded
two tasks ago.

### What the strategy freeze actually decided

The 4-layer JLCPCB stack is **kept**, and the layer roles are now **enforced by rule rather than
asserted**: In1 solid GND with `severity error` on any non-GND track, and USB, both NFC transmit
arms, the NFC crystal, every switch node, the Class-D output and `BAT_MAIN` all **forbidden on
In2**, because In2's only continuous reference is In1 across a 1.065 mm core. One authorised void
in the plane — the ESP32 antenna keepout, a **6.5 × 44 mm notch on the right edge** in the same
corner as `U1`, `U11`, `U18`, `R75` and `D10`, so every return path there must be planned around a
plane edge.

**The USB answer is short because the design is short.** The ESP32-S3 has no High-Speed PHY, so
this is Full Speed at 12 Mbit/s with a 4–20 ns rise time and a 100 mm critical length. The measured
path is **≈ 40 mm per side, entirely on F.Cu over solid In1**, with an intrinsic placement skew of
2.4 mm = **17 ps** against a ≈ 1 ns budget. **No impedance control, no length matching, zero vias.**
The 90 Ω geometry stays as good practice and is marked STACKUP-TO-CONFIRM for one honest reason:
**the board file carries no physical stackup object at all**, so a fabricator would build to its own
default (P2-O6).

**No length-matching theatre anywhere else either.** SPI-A is 46.4 mm against Beta-DM's 126.5 —
**63 % shorter** — and SPI-B is 113.1 against 144.0, **21 % shorter**. Both are shorter than
versions that were already accepted, so neither gets matching or damping. **The one bus with a real
derived constraint is internal I²C**, at `C_bus ≤ 161 pF` for 400 kHz on 2.2 k pull-ups — a number
that ~100 mm of copper and eight devices is already close to — with 100 kHz as the recorded
fallback (D-235).

**The community-port escape was measured rather than feared.** `J5`'s inter-row channel is
**6.570 mm × 27.94 mm** with eleven inter-pad gaps at two tracks each per layer, three usable
layers, and both ends open: **10 crossings needed, 22 available on F.Cu alone.** M-12's warning
that the right-hand strip was "the most constrained region of the PCB" is discharged. No nudge.

### What fails the gate

**Three electrically required placement moves, and routing must not begin until they are ruled on.**
All three are new, all three are measured from the board, and **none of them existed in Beta-DM to
be carried forward** — the battery-protection block and the NFC front end are both new in Full Beta
v2. FBV2-P1 placed them into free rear pockets and verified every *mechanical* relationship by
script. Nobody had yet looked at either *electrically*. That is what an entry gate is for.

**PM-1 — all four switching converters have their inductor off the IC.** `U12`/`L1` 12.96 mm,
`U13`/`L2` 28.56 mm, `U21`/`L4` 30.50 mm, `U17`/`L3` **45.90 mm**, against a ≤ 5 mm requirement.
The backlight is the worst: `BL_SW` runs `U17.1` → `L3.2` while the catch diode `D8` sits **beside
the IC, 45.7 mm from the inductor**, so the `L3 → D8 → C44` boost energy loop is **≈ 76 mm around**,
switching at 1.2 MHz between 0 V and **up to 39 V** on the open-LED fault TI specifies — down the
left margin, **13 mm from the microphone**, through the band the 433 flex sits against. All four
inductors were placed in the left-margin column at x ≈ 3 while their ICs went elsewhere. That is
systemic, not four coincidences, and **loop area is a placement property that no routing repairs.**

**PM-2 — the single-fault battery-protection block is dispersed over 96 mm.** The 1.5 A path runs
`J4` → `F1` → `Q2` → `Q3` → **79.0 mm** → `R75` → `U11`, ≈ 116.7 mm in total. What is *right* stays
right and is worth saying first: **the Kelvin sense is sound** — `U18`'s SENSE and OUT pins both
land on `R75`'s pads with the controller 4.2 mm away, so the 47 mV measurement across the 15 mΩ
shunt at the 3.125 A trip is not corrupted. What is wrong is everything around it: `LTC_GATE` at
**95.6 mm** is a ≈ 20 µA charge-pump node holding four pass FETs enhanced, with its RC damping
31–45 mm from the FETs; `LTC_OV` and `LTC_UV` carry the **battery trip points** on 3.65 M and 510 k
dividers over 78–82 mm; and `REF_HO`'s two divider halves are **38 mm apart** with the comparator
52 mm from the top resistor. The block sits in three clusters with multi-megohm nodes strung
between them. **Routing cannot make a 3.65 MΩ node that crosses four switching converters immune to
coupled charge.** D-049 and the single-fault architecture are **not** compromised by this finding —
the recommendation moves parts, not circuits — and it returns ≈ 0.13–0.18 W to open blocker B-34.

**PM-3 — the NFC differential front end is not symmetric.** `NFC_MATCH_A` spans 24.18 mm against
`NFC_MATCH_B`'s 34.21 — **10 mm of asymmetry before a single track is drawn.** `L5` and `L6` are
19.8 mm apart on **opposite sides** of `U9`; the antenna nodes differ 8.82 vs 12.49 mm; each EMC
filter node's three capacitors are spread over 13.6–17.2 mm; and the crystal load caps sit 13–15 mm
from `Y1` on the far side of the IC, giving a ≈ 30 mm oscillator loop. With `R_q` at 1.1 Ω per arm
and a network Q of ≈ 21, and mandatory first-article bench tuning, that is not something routing
absorbs (D-236).

A fourth item is recorded but ranked below them: **`U11` dissipates ≈ 0.65 W while charging from
inside the battery shadow**, pressed against the cell it is charging, in a sealed unvented
enclosure (PT-1). *Do not rely on the battery as a heatsink* — this is the one place the board
currently does.

### Validation

**DRC 47 → 26**, and the 21 `clearance` violations closed by **naming the four vendor land patterns
that cause them** — `D2`, `U18`, `U19`, `U21`, all stock KiCad footprints whose minimum pad gap is
0.1500 mm by construction — **without weakening any routing clearance anywhere.** Residue is 24
`silk_over_copper` + 1 `silk_edge_clearance`, which is finishing work P2 owns, and the one `MK1`
`solder_mask_bridge` reviewed and accepted at D-227, still **not excluded and not suppressed**.
**ERC 0 errors / 27 warnings, violation-type histogram identical.** `netclass_probe`,
`p1_regression`, `fork_equivalence` and the new `dru_probe` all PASS. Board 70.000 × 148.000 mm,
placement collisions 0, **499 unrouted, ZERO tracks, ZERO signal vias, ZERO electrical pours.**
Beta-DM, the frozen Beta tree and `hardware/beta/mechanical/` untouched.

### A dead end worth recording

The first attempt to make the ESP32 antenna rule resolvable was to **name the rule area already
embedded in the `U1` footprint**. It works — `pcbnew` reads the name back — but it edits the board
copy of a library footprint, and DRC immediately reported `lib_footprint_mismatch` on `U1`, a class
FBV2-P1-002 had driven to zero. **Tested, observed, reverted.** The board-level duplicate carries
the identical polygon and flags, is visible in the board file, lets other rules name the region, and
leaves the library relationship alone. The reasoning is written into `.kicad_dru` §3 so nobody
re-tries the rename.

---

## 2026-08-24 — the circular keepout that opened the 915 lane (FBV2-P1-002)

**FBV2-P1 PASSES. Overall 68% → 74% — the third of the twelve gates.** Full analysis:
[`audits/2026-08-24-p1-floorplan-closeout.md`](audits/2026-08-24-p1-floorplan-closeout.md).
New working document: [`assembly/IR_LEAD_FORMING.md`](assembly/IR_LEAD_FORMING.md).

### The 915 feed closes, and the reason is width, not length

FBV2-P1-001 failed the gate on the 915 MHz pigtail, and the diagnosis in that audit was only half
right. Length was never the binding constraint: **the SMA is locked to the top-panel LEFT half and
the NFC region owned the entire upper-left**, so a 200 mm or a 300 mm cable would both have had to
cross the clear zone or run inside the 5 mm metal keep-out.

The circular geometry unlocks it — but **not because a circle is smaller than a square.** It is,
only at the corners, and the corners were never in the way. It unlocks it because a circle can be
**re-centred** against a hard right-hand limit in a way a 58-wide rectangle sitting at x −4.5 … 53.5
could not. The width budget is the whole argument: **75 mm of cavity, 58 mm of Ø58 exclusion,
12.1 mm owned by `J5` — 4.9 mm of coax lane, and only if the exclusion is pushed as far right as
`J5` allows.** It now is, with the loop perimeter **5.490 mm** from `J5`'s copper against a ≥ 5 mm
rule.

**NFC clear Ø48, metal exclusion Ø58, both centred doc (30.800, 124.500)**; the 48 × 48 square is
retained but only as the placement-tolerance envelope. The centre moved **+6.30 mm in X**, which is
the 915 solution, and **−1.50 mm in Y**, which buys the SMA its margin (D-224).

**Measured, not estimated: the route is 138.48 mm** including bend allowances, with a **7.42 mm**
minimum available bend radius against the ≥ 5 mm rule and **0.600 mm** at its tightest point to the
Ø58 exclusion — **zero violations** against the 433 flex, the battery, the speaker cavity, the
microSD card-travel volume, the USB aperture, both IR optical regions, the barrier, the community
recess and `J5` (D-222).

**`U7` and `U8` are swapped.** The two Ebyte footprints are dimensionally identical, so the swap
costs **zero plan area** and puts the length-critical 915 module beside the only north-south cable
channel on the board. The 433 flex needs 44 of its 100 mm either way. **The SMA bulkhead moves from
x 12.000 to x 5.000** — still top panel, left half, and the move only *improves* both SMA↔IR rules.

### The cable, and a procurement fix that came free

**`095-902-568-100` → RF Solutions `CBA-UFLSMA20IP`, 200 mm** (D-223). The CTO's own threshold
decides it: 138.48 mm is comfortably ≤ 180 mm, so the 200 mm assembly locks and the 250 mm Taoglas
`CAB.01034` stays a recorded fallback. Verified live under D-096 — DigiKey **ACTIVE, 296 in
stock**; CPC **IP67**, 7 in stock; the manufacturer drawing confirms *UFL right angle · waterproof
SMA female bulkhead straight · heatshrink · RG178*. **Mating verdict: COMPATIBLE** — Hirose U.FL
and I-PEX MHF1 are the same interface and the plug gender is right for the `E22-900M22S` socket.
**Spare 46.52 mm beyond the mandated 15 mm service loop. Feed loss ≈ 0.4 dB.**

**And the superseded part was ACTIVE but 0 in stock on a 12-week factory lead.** The replacement is
stocked at two distributors today.

### Three findings the previous pass had wrong

**The ESP32 thermal vias were never in violation.** The board's global floor is
`min_through_hole_diameter` = **0.20 mm**, not 0.30. The twelve errors P1-001 attributed to them
were **twelve `copper_edge_clearance` errors on `J5`**, whose PTH field ended 0.445 mm from the
board edge against a 0.5 mm rule. `J5` moved **0.070 mm** west and all twelve went away. JLCPCB
capability was verified live anyway — 0.20 mm holes in 0.60 mm pads are **supported at no
premium** — and a **narrowly scoped guard** was added to `.kicad_dru` so the manufacturer's array
stays legal if the global floor is ever raised. **The global minimum was not lowered** (D-228).

**`BOSS2` was never legal.** P1-001 placed it at (59.5, 145.0), inside the **mandatory opaque IR
barrier**. Corrected to (59.0, 145.0), with the barrier **widened 3.0 → 5.0 mm** to fill the whole
inter-window gap — strictly better optically, touching neither window — so barrier and boss are now
one moulded feature (D-226).

**Writing the IR forming requirement found that the formed LED did not fit.** A formed `TSAL6100`
occupies **0.6 mm of bend radius + 2.0 mm of straight lead (Vishay's stated minimum from the epoxy
case) + 8.7 ± 0.3 mm of body = up to 11.6 mm** in +Y from its pads. At P1-001's Y = 143.600 the
dome would have ended **1.2 mm outside the enclosure's external top face**. `D1` moved to
(50.750, 141.400); `TP39` and `R123` moved 1.750 mm to clear it; `U6` needs ≈ 9.0 mm and fits
unmoved (D-229).

### Retention: the honest number is two, and it is escalated

**Ø6.0 keep-out — zero legal sites. Ø4.5 — two.** The display owns X 3.39 … 59.93 on the front and
the battery owns X 6.00 … 66.00 on the rear; between them they leave a **3.39 mm left sliver and a
4.00 mm right sliver, both narrower than a Ø4.5 keep-out**. Only the 23.5 mm bottom band and the
8 mm top band can host a through-board screw at all, and each yields exactly one. The top-left
corner and the left margin are now the mandatory 915 coax channel.

Structural support is completed by the enclosure and needs no PCB holes: moulded edge-capture rails
plus four rear non-metallic support ribs on reserved component-free pads, all outside the battery
shadow. **§9 sets three as the acceptable minimum and this outline yields two — escalated, and the
only new item for CTO decision** (D-226).

### `MK1`, and what did not change

`padstack_invalid` **2 → 0**. The GND ring becomes a plain filled Ø1.65 mm SMD pad with the
concentric Ø1.05 mm **non-plated** hole drilling the centre out — same annulus, no custom pad, no
fake plated through-hole. The paste becomes one filled **C-shaped** polygon, the same ID 1.25 /
OD 1.65 ring with a 20° web. **Acoustic opening, annulus dimensions, paste pullback, keep-out and
microphone location all unchanged** (D-227).

**The display Z stack was not spent.** P1-001's recommendation to raise the display support by
≈ 3 mm as the primary 915 solution is **rejected and withdrawn** — the circular geometry closed the
feed without touching Column A's 9.9 mm of unused Z. The **3.34 mm left offset is accepted as
intentional** (D-225).

### Numbers

**DRC 64 → 47**, every one classified: 24 silkscreen, 21 vendor intra-footprint land patterns for
the P2 rule pass, 1 `MK1` mask-aperture artefact left in place, 1 silk edge. **`padstack_invalid`
2 → 0, `copper_edge_clearance` 12 → 0, `lib_footprint_issues` 3 → 0.** **Nothing was fake-cleaned:
no DRC exclusion, no severity change, no relaxed global rule.** ERC **27 / 0 errors**, histogram
byte-identical. Schematic connectivity **unchanged** — the sheets were not opened. Placement
collisions **0**. **ZERO tracks, ZERO vias, ZERO copper pours; 499 unrouted, the correct P1 state.**
`netclass_probe` **PASS**, `fork_equivalence` **PASS** with Beta-DM and the frozen Beta tree
untouched. **FBV2-P2 has not begun.**

---

## 2026-08-24 — the enclosure-driven floorplan, and the cable that cannot reach (FBV2-P1-001)

**FBV2-P1 DOES NOT PASS. Overall stays 68%.** One gate criterion fails — the 100 mm 915 MHz
pigtail does not reach the top-panel SMA — and the floorplan is otherwise complete and
collision-free. Full analysis:
[`audits/2026-08-24-p1-floorplan-implementation.md`](audits/2026-08-24-p1-floorplan-implementation.md).
New working documents: [`pcb/FBV2_P1_FLOORPLAN.md`](pcb/FBV2_P1_FLOORPLAN.md),
[`pcb/FBV2_P1_KEEPOUTS.md`](pcb/FBV2_P1_KEEPOUTS.md),
[`pcb/FBV2_P1_COORDINATES.csv`](pcb/FBV2_P1_COORDINATES.csv), [`pcb/review/`](pcb/review/).

**PCB modification was authorised for the first time, and the board is no longer Beta-DM.**

### The board was rebuilt, not edited

The pre-P1 PCB was still the inherited Beta-DM geometry — 188 footprints, 2,801 track segments,
424 vias, 43 zones — and a floorplan built around a different component set is not a baseline. So
the file was **stripped to its header, layer stack, `general` and `setup`**, keeping the design
rules byte for byte, and **rebuilt from the current nine-sheet schematic**: 321 footprints, one per
component, references and exact verified footprints preserved, **224 nets over 991 pads**, plus a
70.000 × 148.000 mm outline, 13 named mechanical regions, 4 copper rule areas and 3 M2 bosses.

**The schematic was never opened. ERC 27 / 0 errors, histogram byte-identical. Zero tracks, zero
vias, zero pours. 499 unrouted connections — the correct P1 state.**

**`fork_equivalence` now reports the v2 PCB as changed. That is the point of P1, not a failure**,
and the same run confirms Beta-DM is untouched.

### Six rulings, five clean

**F.Cu is the front and B.Cu is the rear**, and `MK1` sits on **B.Cu listening forward through the
board** — 1.21 mm clear of the LiPo, 67.42 mm from the speaker on the opposite face. The apparent
front-face/bottom-face contradiction was a **nomenclature collision between the enclosure face and
the PCB copper face**, not a requirement conflict.

The rear packs **NFC → battery → speaker** at **48 + 75 + 20 = 143 mm in a 155 mm cavity**, with
zero NFC/battery overlap, 81 mm from the speaker to the loop perimeter, and no attempt to squeeze a
Ø20 driver beside a 60 mm battery in a 75 mm cavity.

**USB-C to microSD achieved 16.40 mm body edge-to-edge** against the new ≥ 8 mm rule — twice what
was asked, measured on verified courtyards rather than the approximate widths.

**The internal 915 whip storage is deleted.** The locked `TI.92.2113` is 198 mm long and the
cavity's longest internal diagonal is 172 mm; it never fitted. The freed left wall goes to the
433 MHz flex, which restores D-118's *LEFT / LOWER-SIDE* placement exactly as locked.

### Only three of six mounting bosses close

A boss is a through-board feature. The display owns X 3.39–59.93 above Y 55, the battery owns
X 6.00–66.00 from Y 23.5 to 98.5, and the NFC zone owns X 0.50–48.50 above Y 102 and forbids screws
outright. **There is no 6 mm-wide side strip anywhere on a 70 mm board, and both top corners are
inside the NFC zone.** A full-board search finds **three** legal M2 positions, and only at a Ø4.5 mm
keepout. **Three fixings will not control flex on a 148 mm span with a battery behind it** — that is
escalated, not accepted.

### The 915 MHz feed is the blocker

Every part taller than about 1.2 mm is excluded from the upper half: the front is display shadow
(F.Cu ≤ 0.8 mm) and the rear is battery (≤ 1.2 mm) then NFC clear zone (≤ 1.0 mm, no shielding
cans). The one free strip above the battery is 16.5 mm wide and already carries `J5`'s 31.6 mm
through-hole field. **A 15.89 × 21.34 × 3.5 mm radio module fits nowhere above Y ≈ 55.**

`U8` therefore sits at the bottom rear, and the routed run to a top-panel SMA is **≈ 190 mm**:
**100 mm is short by ≈ 90 mm, and even the superseded 150 mm is short by ≈ 40 mm.** Length is only
half of it — the SMA is locked to the top-edge **left** half and the NFC 48 × 48 zone owns the whole
upper-left, so any coax from the bottom either crosses the NFC zone or runs inside the 5 mm metal
keepout. **No pigtail length fixes this on its own.**

The recommended resolution costs nothing dimensionally: **raise the display support by ≈ 3 mm.**
Column A of the mechanical spec totals 13.1 mm of the 23 mm budget and carries **9.9 mm of unused
Z**. Spending 3 mm of it puts a 3.5 mm module under the panel, frees the entire upper half, and
lets a short pigtail reach.

### Four things the floorplan found on its own

**The display cannot be centred on the enclosure.** `J5` needs 9.2 mm of board on the right and
cannot sit below the battery, so it takes Y 105–137 beside the display band, pushing the panel
**3.34 mm left of centre**. Widening to 72 mm does not fix it.

**`MK1`'s GND ring fails KiCad 10's padstack validator** — it is drawn as a stroked circle outline
rather than a filled annulus. Dimensionally right, structurally invalid; it must be redrawn before
fabrication.

**The stock ESP32 footprint's twelve thermal vias are 0.2 mm**, below this board's 0.3 mm
minimum-hole rule.

**`netclass_probe` was measuring the wrong board.** Its expectation listed `LED_A1`…`LED_A4` —
*Beta-DM* net names. The v2 schematic has one anode net, `/03_SPI_A_DISPLAY_SD/LED_A`, the net
D-111 deliberately added to `LED_BOOST`. It only passed for the last nine tasks because the PCB was
still Beta-DM's. The expectation now follows the schematic; **the guard — `LED_BOOST` must never
capture the IR transmitter nets — is unchanged and still passes.**

Also recorded, because it is written nowhere else: **`D1` and `U6` are flat-mount leaded parts
whose optical axis is normal to the BOARD**, so both must be **formed 90° at assembly** to look out
of the top panel.

## 2026-08-23 — pre-floorplan authority reconciliation, and a part that was never a series pair (FBV2-MECH-002)

**NO PROGRESS EARNED. Overall stays 68%. FBV2-S2 = PASS is unchanged.** This is a reconciliation
and sign-off task, not a design phase. Full analysis:
[`audits/2026-08-23-pre-floorplan-authority-reconciliation.md`](audits/2026-08-23-pre-floorplan-authority-reconciliation.md).
New working document:
[`mechanical/P1_FLOORPLAN_INPUTS.md`](mechanical/P1_FLOORPLAN_INPUTS.md).

**ERC 27 / 0 errors / 27 — histogram identical. Netlist 224 nets / 991 nodes — IDENTICAL. The
schematic diff is PROPERTY-ONLY. The PCB is byte-identical and still bit-identical to Beta-DM.**

### `BAT54WS` is not a series pair, and this programme said it was six times

FBV2-S2-002 wrote a reasonable-sounding inference into the record: `BAT54S` *is* a series pair, so
`BAT54WS` "must be the SOD-323 version of it". **The `S` in `BAT54WS` is a package code, not a
topology code**, and the claim then propagated into the assembly plan §5 and §8, this changelog,
the progress log, **D-206**, and **the `D10`/`D11`/`D12` symbols themselves**. Each copy cited the
others.

**Three independent proofs that it is wrong:**

- **SOD-323 is a two-terminal package.** A series pair needs three terminals.
- **Every `BAT54WS` in the LCSC library, from eight manufacturers, is catalogued `1 Independent`** —
  Diodes Inc, Changjing, Starsea, Hottech, PANJIT, AnBon. There is no series-pair `BAT54WS` in the
  library to substitute *for*.
- **AQROOT never used a pair.** `D10`, `D11` and `D12` are each one two-pin `Device:D_Schottky` on a
  two-pad `Diode_SMD:D_SOD-323`, and `D10`/`D11` form the ratiometric bridge as **two separate
  matched components**.

**The design was never wrong.** That is exactly why nothing caught it — **the error lived only
where nothing is validated by a tool.** The check that resolves it in one step is the one this task
ran: read the distributor's own parametric field.

Nexperia `BAT54W,115` stays rejected, **for the right reason**: it is **SOT-323 (SC-70)**, a
**footprint** mismatch against `Diode_SMD:D_SOD-323`, and it has 5 in stock against a need of 15.

### Two substitutions signed off, and the consignment list got shorter

| ref | now | LCSC | live state | route |
|---|---|---|---|---|
| `F1` | **Littelfuse `0466005.NRHF`** | **`C57525`** | **29,328** in stock, JLC **Extended** | class C → **class B, machine-placed** |
| `D10`–`D12` | **Diodes Inc `BAT54WS-7-F`** | **`C124205`** | **46,819** in stock, JLC **Extended** | class D → **class B, machine-placed** |

`F1` is the **halogen-free ordering option of the same Littelfuse 466 / Nano2 family** — and the two
LCSC records carry a **character-for-character identical parametric string**, so the distributor's
own data does not distinguish them electrically at all. Same footprint, same function, **not one
net, pin, wire, label or junction touched**.

**The `D10`/`D11` bridge is structurally insensitive to the parameter that changed.**
`INA+ − INA− = (BAT_RAW + V_F11 − V_F10) / 2` — the absolute Schottky drop **cancels**, and only the
mismatch survives. Each leg runs **≈ 1.1 µA** through 4.4 MΩ, six orders of magnitude below the
100 mA rating, and matching **improves** because both diodes now come from one MPN on one order
line. `D12` carries **≈ 16.6 mA worst case against 100 mA continuous — 6×** — and re-solving D-105
with this part's V_F gives **7.9–8.9 mA, still inside the accepted 5–10 mA band, so D-105 needs no
revision.**

**Consignment: 11 → 9 part numbers. Class D is now EMPTY. Hand-soldered parts per board: still
exactly two, `J5` and `D1`.**

### The mechanical spec disagreed with itself in six places

`MECHANICAL_INTERFACE_SPEC.md` is the authority for FBV2-P1, so a stale row in it is a defect that
propagates into a floorplan.

- **NFC zone 45 × 45 → 48 × 48 mm, LOCKED.** The 48 mm figure was ruled at FBV2-S1-004B and already
  sat in this document's own NFC banner. **Four places had never been updated — including the
  machine-readable block a guard script parses.**
- **`J1` land pattern.** Every current claim that `J1` uses the **FH12/FH52E standard land pattern**,
  that **FH52E is a drop-in second source**, or that **mating equivalence was proven**, is removed.
  Current truth: **FH69 dedicated footprint · FH52E not drop-in · single-source connector
  architecture · the genuine Hirose is JLC machine-placeable · re-check stock before ordering.**
- **`J1` is not manual assembly.** M-13 and the header both said it was; D-206/D-207 superseded that
  the same day. **Exactly two parts are manual per board.**
- **Speaker Z column 4.0 → 3.0 mm**, total **13.6 → 12.6 mm**. D-148 locked Ø20 × 3.0 and stated it
  released 1 mm of Z — and the derived column in the same document still summed 4.0.
- **§4.1 content list.** "changes the connector from **26 to 20 pins**" → **24 contacts, 2 × 12 at
  2.54 mm**; "removes HOME **and the RGB nets**" → a **front RGB status light `D13` was added**.
- **IR receiver naming** now puts the locked `TSOP38238` first and `TSOP38438` in parentheses.

### The 8 mm / 15 mm spacing was not a contradiction — and it was not resolved by preference

Both figures were in the document and it would have been easy to strike one. **The trace says
neither is stale.** The **≥15 mm** rule is FBV2-MECH-001, 2026-08-22, **centre-to-centre**, written
against a generic whip shadowing the emitter cone. The **≥8 mm** rule is **D-120**, 2026-08-23,
**edge-to-edge, SMA body to IR aperture**. **M-13 — the latest ruling to touch this, written after
D-120 and with the Amphenol bulkhead already chosen — states both in the same sentence.** So 15 mm
was **re-asserted**, not superseded.

**The actual defect was that neither figure said what it was measured between.** Both now carry an
explicit datum in a new **§8.1 authority trace**, with the consistency check written out: on a
~9.5–11 mm SMA hex body and a ~Ø5.5–6.0 mm aperture, **8 mm edge-to-edge implies ≈ 15.5–16.5 mm
centre-to-centre**, so the two agree and **8 mm is the binding one — satisfy whichever is larger.**
The Amphenol body OD is **CAD-TO-VERIFY**; **B-52 stays open and no CAD was created.**

### Six things P1 cannot floorplan around, surfaced not decided

The sharpest two are arithmetic, not opinion.

**The rear face is over-constrained by ≈ 8 mm.** It must hold, in Y: battery **75** + NFC clear zone
**48** + speaker **Ø20** + the **≥20 mm** speaker-to-loop separation = **163 mm against a 155 mm
cavity**. Putting the speaker beside the battery does not rescue it — a 60 mm battery in a 75.0 mm
cavity leaves **7.5 mm per side** against a Ø20 driver. And that is *before* the 5 mm NFC metal
keepout, the shell lip and the bosses. **All four constraints are currently recorded as binding;
one of them has to give.**

**The internal antenna storage channel cannot hold the locked 915 antenna.** §8 reserves a left-wall
channel *"sized for the stowed whip"*. The locked whip is Taoglas **`TI.92.2113`, 198 ± 3.3 mm ×
Ø13 mm**; the cavity's longest internal diagonal is **≈ 172 mm**. **It does not fit in any
orientation** — and that same left wall is the **LOCKED** mount region for the 433 MHz flex.
Withdrawing the storage requirement would free the entire left wall, which is the largest single
simplification available before floorplanning.

Also raised: the **microphone board-face assignment** (front aperture + bottom-port part = `MK1`
must sit on the copper face away from the front shell, and that side has never been assigned); the
**mid-span boss at Y ≈ 100** now inside the grown NFC keepout; the **microSD ↔ USB-C "≥8 mm
centre-to-centre"** figure, which is smaller than the two bodies physically allow (~11.6 mm before
they touch); and the **150 mm 915 pigtail** in a 155 mm cavity. **No substitution is proposed for
the pigtail — D-195 locked that MPN.**

## 2026-08-23 — S2 release closeout: the footprint that wasn't broken, and six wrong parts (FBV2-S2-002)

**Overall raised 62% → 68%. FBV2-S2 = PASS** — the second of the twelve gates to pass. Full
analysis: [`audits/2026-08-23-s2-release-closeout.md`](audits/2026-08-23-s2-release-closeout.md).
New working document:
[`assembly/FIRST_FIVE_ASSEMBLY_PLAN.md`](assembly/FIRST_FIVE_ASSEMBLY_PLAN.md).

**ERC 27 / 0 errors / 27 — the violation-type histogram is identical to the FBV2-S2-001 baseline.
The schematic diff is property-only. The PCB is untouched and still bit-identical to Beta-DM.**

### The MAX98357A footprint looked broken and was not

Maxim outline **21-0136** lists exposed-pad variations in which **`T1633-5` is 1.50 / 1.60 /
1.70 mm** while `T1633-2/-4/-7C` are 0.95 / **1.10** / 1.25. The KiCad footprint cites
**21-0136 (T1633-5)** in its own `descr` and then draws a **1.23 × 1.23** land — sized for the
1.10 family. That is a footprint contradicting its own citation, on a thermal pad, and the obvious
move was to fork a corrected project-local footprint.

**Maxim land pattern 90-0032 Rev E dissolves it.** The drawing is issued under **PKG. CODES
[T1633-5], [T1633-5C] and [T1633-7C] together** and specifies **one land for all three** — EP
**1.23 × 1.23**, pads **0.80 × 0.30**, pitch **0.50**, centreline span **2.85**. Maxim
deliberately recommends a land smaller than the T1633-5 pad, **so the question of which variant
`MAX98357AETE+T` carries does not have to be answered to get the land right** — which is
fortunate, because analog.com, Mouser and LCSC all refused the datasheet in this environment.

Against the library file: **EP exact, pitch exact, inner pad edge exact at 1.025** — so
EP-to-signal clearance is Maxim's own 0.410 mm — pad centre **+0.0125** (inside the drawing's own
±0.02), length **+0.025**, width **−0.05**. **No project-local footprint was created.** Forking
one to chase 0.05 mm of pad width, buying a side fillet at the cost of a thinner mask dam at
0.5 mm pitch, would have been a change made for the sake of having made one. **The right outcome
of a verification is sometimes "it was already correct" — but only after the drawing is read.**

**All eight remaining Tier-2 footprints are now Tier 1**, compared dimension by dimension. `Y1`'s
land is an **exact** match to the vendor's own Suggested Layout (1.4 × 1.2 at (±1.10, ±0.85)), and
`Y1` itself moves from **candidate to lock** — `C362365`, 3,421 in stock, ±30 ppm total against an
ISO/IEC 14443 requirement of ±516 ppm.

### The microphone port existed only as a sentence

`AQROOT_Beta:PUI_DMM-4026-B-I2S_4.0x3.0mm` was Tier 1 for its pads, and its `descr` then said the
acoustic port was *"NOT PART OF THIS FOOTPRINT … an FBV2-S2 / PCB-stage item."* **A port that
lives in a description is a port that gets forgotten at placement.**

It is now drawn: **Ø1.05 mm NPTH** — **the diameter is not invented, it is the inner diameter of
the manufacturer drawing's own pad-4 GND ring**, i.e. the part's own aperture — plus a **paste
pullback**, pad 4 losing `F.Paste` entirely in favour of a separate **ID 1.25 / OD 1.65** annular
aperture **0.10 mm** back from the copper edge. **The 0.10 mm is a declared stencil design choice,
not a drawing dimension, and the footprint says so.** Keepout marked on `B.Fab` and
`User.Comments`; **bottom-port orientation** — the part listens *through* the board, so the
enclosure aperture belongs on the **bottom** face — recorded as **M-14**.

### Six substitution traps, and two MPN strings that would have stalled the order

All 46 MPNs were checked against **live JLCPCB parts-API state**. A loose keyword search **returns
a plausible wrong part more often than it returns nothing**:

- **`BAT54W,115` offered for `BAT54WS,115`** — ~~a **single diode** for a **series pair**~~ ***CORRECTED 2026-08-23 by D-211: `BAT54WS` IS NOT A SERIES PAIR.* SOD-323 is a two-terminal package and `D10`–`D12` are each ONE independent diode; `BAT54W,115` is wrong because it is SOT-323 (SC-70) — a FOOTPRINT mismatch.**
- **G-Switch `GT-TC089A-H043-L1`** for **C&K `PTS645SM43SMTR92LFS`** — 35 placements
- **FUXINSEMI `SD103AWS`** for **onsemi `NSR0240HT1G`**
- **LRC `LBSS138LT1G`** for **onsemi `BSS138LT1G`**, which has 762,522 in stock
- **KOHERelec `SPM4030-1R0M`** for **Würth `74438357010`**
- a **VBsemi clone** for **onsemi `NTMD4820NR2G` — the battery reverse-polarity pass FETs**

**Every one is now recorded in the schematic symbol itself.** No substitute was adopted;
`BAT54WS-7-F` and `0466005.NRHF` are candidates awaiting sign-off.

**`J4` and `J6` are the same JST PH header and carried two different MPN strings.** Not cosmetic:
the bare order code is `C20504437` with **stock 0**, while `B2B-PH-K-S(LF)(SN)` is `C131337` with
**378,913**. `J7` had the identical fault. **A BOM that produces two lines for one part, one of
which cannot be filled, is a BOM that stalls at the quote stage.**

### The build closes — through consignment, not through hand assembly

**Two through-hole parts per board are hand-soldered (`J5`, `D1`). Zero fine-pitch or QFN parts
are hand-placed.** Ten parts have stock short of the first-five need and one is not in the LCSC
library at all; **all are consigned to JLC and stay machine-placed.** The sharpest case is
`U2`/`U3`/`U23` — **fifteen TSSOP-24 at 0.65 mm pitch against one in stock**. **`J1` improves**:
JLC carries the genuine Hirose `FH69-50S-0.5SH` with 1,072 in stock, so the display connector is
machine-placed after all.

### The NFC numbers are now datasheet numbers

DS12484 Rev 3 finally came through a **mikroe.com mirror** after st.com timed out repeatedly.
**`I_AL-AM` max 26 mA** for the IC with all blocks active plus **≈ 60 mA** for the driver into
D-134's *actual* first-build network → **allocate 100 mA**, replacing D-130's ≤ 150 mA estimate.
**Table 118's 350 mA and 500 mA are absolute maximum ratings and were deliberately not used** —
that is exactly the number a careless budget grabs. TPS63020 lands at **63–71 % of 2 A**.
**One binding guard rail: D-134 records that `C_s` 300 pF → 270 pF draws ≈ 257 mA, which this
allocation does not cover.**

**`L5`/`L6` = Murata `LQW18AN39NG80D`** — and the useful finding is that **the DCR is not
negligible**. `R_q` is only **1.1 Ω** per arm, so **0.20 Ω max drops the network Q from 25.3 to
≈ 21.4**. That moves further into the safe, under-driven side D-134 chose, but **the antenna must
be bench-tuned with this exact part fitted**, and **if the field is short the first lever is `R_q`,
not 39 nH.**

### Eight DNP parts still had no recorded reason

After seven consecutive sheets of load-bearing inherited `DNP`, an unexplained one is the single
thing this project cannot afford to leave lying around. **`U13`, `L2`, `R44`, `R45`, `C34`, `C35`
are the NFC 5 V boost branch** — correct, and a D-049 no-respin escape if the 3.3 V field measures
short. **`R119`** is the BMI270 alternate-address strap, **mutually exclusive with `R118`**.
**`R112`** isolates the display `SDO` from the shared MISO and **must not be fitted while MX-8 is
relied on**. **All eight now carry a note; the design has zero unexplained DNP.**

### O-8 — verified, not accepted

Taoglas **`TI.92.2113`** against **SPE-19-8-076/A**: 902–928 MHz, terminal-mount dipole, hinged
SMA(M), 198 ±3.3 mm × Ø13 mm, 1 W max input, and Taoglas' own statement that it *"performs very
well in free space … where there may be no ground plane."* Every expectation checks out. **Worth
saying anyway: the marketed "2 dBi" is the bent-configuration peak — the table gives 1.21 dBi
straight and negative average gain in both orientations. Budget the link with the average.**

### What was NOT done

No PCB placement, no routing, no outline change, no mechanical CAD, no firmware, no Beta-DM, no
frozen Beta. **No honest ERC warning was "fixed"** — no no-connect, power flag, pin electrical
type or exclusion was added, removed or altered anywhere. **No product feature was added.** No
part was substituted. Passive values remain unconsolidated.

---

# AQROOT Full Beta v2 — Changelog

Chronological engineering changes and why they happened. Newest entries at the
top. Each entry records what changed, not merely that something happened.

This file records **decisions and design changes**. Routine document edits are
not entries. A change that alters what gets built, or what may not be built, is
an entry.

---

## 2026-08-23 — Pre-placement release audit, and NFC was still DNP (FBV2-S2-001)

**Overall HELD at 62%. FBV2-S2 = FAIL on two of fourteen exit criteria** — and the audit earned
its keep on the first one it looked at. Full analysis:
[`audits/2026-08-23-s2-preplacement-release-audit.md`](audits/2026-08-23-s2-preplacement-release-audit.md).
Working documents:
[`assembly/FIRST_FIVE_POPULATION_MATRIX.md`](assembly/FIRST_FIVE_POPULATION_MATRIX.md) ·
[`assembly/SOURCING_LEDGER.md`](assembly/SOURCING_LEDGER.md) ·
[`assembly/FOOTPRINT_VERIFICATION_LEDGER.md`](assembly/FOOTPRINT_VERIFICATION_LEDGER.md) ·
[`assembly/OFF_BOARD_BOM.md`](assembly/OFF_BOARD_BOM.md).

**ERC 27 / 0 errors / 27 — unchanged. PCB untouched and still bit-identical to Beta-DM. No
percentage was awarded, because no gate passed.**

### The NFC chip was still marked DNP

`U9` **ST25R3916-AQET** and its **twelve mandatory supply-decoupling capacitors** were inherited
from Beta-DM marked `DNP` — against **D-035**, *"NFC is mandatory in the FIRST Full Beta v2
fabrication. No DNP showcase shortcut"*, and **D-055**, *"NFC must be FITTED and functional on the
first fabrication."*

**Everything around the chip was already fitted**: the 27.12 MHz crystal, the complete differential
matching network `C69`–`C80` / `L5` / `L6` / `R114`–`R117`, the antenna connector `J7`, the SPI
wiring, the `NFC_SUPPLY` selector. **The first five boards would have been built with a finished
13.56 MHz front end and no NFC chip on it.** All thirteen parts are now FIT.

**This is the seventh consecutive sheet carrying a load-bearing inherited `DNP`, and it is the one
that hid longest.** It survived four migrations because sheet 04's own migration
(FBV2-S1-004/4B/4C) was about the antenna and the matching network — nobody re-read the population
state of the IC underneath it. **The lesson is now a standing one: migrating a subsystem is not the
same as auditing its population.**

### Two carried numbers were wrong, and one register was full of ghosts

**`D-077`'s display second source does not exist.** It states that `J1` is *"laid out on the
FH12/FH52E standard land pattern so `FH52E-50S-0.5SH` is a drop-in second source."* Both Hirose
land patterns were read. **FH69: signal land 0.30 × 1.23, hold-down 0.36 × 4.25 at 28.73 c/c,
overall layout depth 7.38 mm, top-and-bottom two-point contact, back-flip actuator. FH52E: bottom
contact only, front-flip actuator, 0.8 land, 4.6 mm depth datum** — and the FH52 catalogue says in
its own words that its pattern is interchangeable with the **FH12**, not the FH69. **7.38 mm against
4.6 mm: they cannot share pads. The claim is struck**, and `J1` is confirmed as **manual assembly**
for the first five. Placement would otherwise have proceeded believing a second source existed.

**The accessory boost settle delay was derived against the wrong capacitance.** FBV2-S1-009 quoted
the TPS61023's 700 µs soft start as "seven times typical" for a 5 ms wait. The datasheet's
condition line says that 700 µs is at **C_OUT_EFF = 10 µF**. `C65` + `C66` are 2 × 22 µF 10 V X7R
0805, which at 5 V bias retain 40–60 % of nominal — **≈ 20 µF effective, twice the datasheet
condition**. The real margin was **3.5×, not 7×**, and the datasheet publishes no maximum.
**The first-build wait is raised to ≥ 10 ms** — a firmware constant, zero hardware cost, measured
at first article.

**Nine register entries were stale** and were closed on evidence: **P-01** (the reverse-polarity
path is fully built and FBV2-A1 passed in August), **P-04** (NFC is fully designed — and now
fitted), **B-45** (`NATIVE_A`/`NATIVE_B` gained their 100 Ω and TVS at FBV2-S1-009), **B-49**,
**B-51**, **B-53**, **B-68**, plus **B-46** and **B-47** resolved below. A register that carries
ghosts is a register nobody trusts.

### P-14 — the fuel gauge stays where it is

The CTO asked whether the MAX17048 should move to the clean node after the reverse-polarity FETs
but before the 15 mΩ sense resistor. **It should not — and it was never on `BAT_RAW`.** Measured
from the netlist, `U14` `CELL` and `VDD` are **already on `BAT_PROTECTED_P`**, the fully protected
node.

`BAT_SENSE` is the **LTC4368's precision current-sense input**. Hanging a gauge's `VDD` and its
bypass capacitor there puts a **differential capacitance across `R75`** that distorts the
reverse-current comparator during fast current steps, opens a deliberate blind spot in a protection
measurement, and injects I²C transients onto the sense node. **What it would buy is inside the
noise:** 15 mΩ costs 26 mV at the 1.75 A pack worst case, 4.5 mV at typical idle — **≤ 2.6 % SOC at
peak load, < 0.5 % typical** — which is coarser than the MAX17048's own ModelGauge error and is
**compensable in firmware by subtracting I × 15 mΩ**. **Safety outranks SOC accuracy.**

### RF is now fully sourced

**B-49 was never a risk:** Ebyte ships both the `E07-400M10S` and the `E22-900M22S` with **IPEX
*and* stamp holes on the standard part number** — there is no variant selection to get wrong.

**B-51 closed: Amphenol RF `095-902-568-150`**, Part Status **ACTIVE** — AMC right-angle plug →
**SMA straight bulkhead jack, IP67**, RG-178, 50 Ω, **150 mm**, 6 GHz, and Amphenol documents the
AMC series as **"compatible with Hirose U.FL and IPEX MHF1"**. **It is one assembly: pigtail and
panel bulkhead in a single orderable part**, so no separate bulkhead MPN exists or is needed. Loss
≈ 0.4 dB against a +22 dBm module. **433 MHz: Taoglas `FXP450.07.0100C`**, 410–470 MHz, MHF1,
100 mm, stocked at DigiKey/Arrow/TTI.

### B-46 closed, and the guess was right

Molex sales drawing **SD-502570-001 Rev A**, note 4: **CARD INSERTING POSITION = CLOSE, NO CARD =
OPEN.** With the detect lever grounded — the drawing's own pattern labels that land *"Vss :
GROUND"* — and `R113` pulling up, **card present drives `SD_CARD_DETECT_N` LOW**, exactly as D-117
assumed. **No firmware correction, no hardware change.**

### Two undocumented placeholders, one of them dangerous

**`R68` is a 0 Ω DNP bypass across `SW9`, the hard power switch.** Fitting it wires the unit
permanently ON and **defeats the one provision that lets a user power down a hung or unflashed
board** — the architecture is explicit that `SW9` is not a GPIO for exactly that reason. It arrived
from Beta-DM **with no note at all**. It is now marked **DNP AND IT MUST STAY DNP**.

**`C21`/`C22` are dead pads** — DNP with one terminal deliberately no-connect flagged, so fitting
them does nothing. Reserved rework pads by the USB block, usable only by cutting a trace.
Documented, and flagged as deletion candidates at placement.

**Six missing MPNs were added** — `D9` → `PMEG2010AEH,115`, `Q4`/`Q6`–`Q9` → `BSS138LT1G`. **Every
active and every connector now carries an exact MPN, and there are zero unexplained DNP.**

### What fails the gate

**B-03 — eight of twenty-eight critical footprints are traceable to a vendor part but have not been
read against a manufacturer drawing:** the ESP32-S3-WROOM-1 module, the GCT USB-C receptacle, both
JST families, the PTS645 and JS102011SAQN switches, the MAX98357A TQFN exposed pad and the NFC
crystal. The standing instruction is explicit — *do not mark a footprint verified because the
library name looks right* — so they are not marked verified. **They do not block placement; they
block fabrication release.** Fifteen are properly verified, including `U11` BQ25185, checked in
this task against TI's own `DLH0010A` board-layout drawing 4226298/A.

**B-71 (new) — only 7 of 46 unique MPNs carry an LCSC code**, so the JLC Basic/Extended split, the
assembly quote and the manual-placement list cannot be produced from the current metadata.
**B-70 (new) — `L5`/`L6`, the 39 nH NFC EMC inductors, have no MPN at all**; a tuned RF inductor
needs a specified part, not a value and an 0603 outline. **B-54 also sharpens: the ST25R3916 field
current at 3.3 V is still not extracted, and that now loads a rail the part is actually fitted on.**

### O-8 — one new item for the CTO

**The 915 MHz external whip antenna MPN is not selected.** Everything from the module socket to the
panel bulkhead is locked and orderable; the antenna that screws onto the outside is not.
Accessory-class, no board impact — but a range test means nothing without it.

### What was NOT done

No PCB placement, no routing, no outline change, no mechanical CAD, no firmware, no Beta-DM, no
frozen Beta. **No honest ERC warning was "fixed"** — no no-connect, power flag or pin-type was
added or altered anywhere. All seven `PWR_FLAG`s were individually traced to a real supply.
Passive values were **deliberately not consolidated**: doing that before the layout exists
optimises the wrong thing.

---

## 2026-08-23 — Community expansion port, and the schematic migration is complete (FBV2-S1-009)

**Overall 55% → 62%. FBV2-S1 = PASS — the first twelve-gate entry to pass since FBV2-A2.** Task
gate **FBV2-S1-COMMUNITY = PASS**. Full analysis:
[`audits/2026-08-23-s1-community-sheet09-implementation.md`](audits/2026-08-23-s1-community-sheet09-implementation.md);
programme closeout:
[`audits/2026-08-23-s1-schematic-migration-closeout.md`](audits/2026-08-23-s1-schematic-migration-closeout.md).

**ERC 42 / 1 / 41 → 27 / 0 / 27. THE DESIGN HAS ZERO ERC ERRORS FOR THE FIRST TIME.** 321
components, 0 duplicate references, 0 without a footprint, 224 nets, 0 `*_TBD`.
`fork_equivalence.py` PASS with an **empty** "still Beta-DM" list, `netclass_probe.py` PASS, PCB
still bit-identical to Beta-DM.

> **FBV2-S1 = PASS means SCHEMATIC MIGRATION COMPLETE. It does not mean fabrication ready.**
> No placement, no routing, no outline, no DFM, no mechanical CAD, no physical validation.

### Three CTO rulings recorded first

**O-6 RATIFIED (D-175).** `U23`, the third `PCAL9535APW,118` at `0x22`, and the front RGB status
light are now **locked architecture**. **B-37 — "zero expander spare", carried since the first
audit — is retired**: 37 of 48 expander pins are used and eleven are free.

**O-4 APPROVED (D-176).** `U16` TCA9517A → **TI `TCA4307DGKR`, LCSC C880333**, verified live per
D-096 at 3 248 in stock. **It is FITTED; the TCA9517A was DNP.**

**P-18 CLOSED (D-178). No I²C mux.** The external segment stays one logical address space with
the internal bus. **The TCA4307 solves *electrical* fault isolation; the address registry solves
*address* allocation.** A mux would add a part, a failure mode and a firmware dependency to
answer a problem a published reserved-address policy already answers. `0x50` is not widened.

### Sheet 09 was rebuilt, not patched, and what it was hiding

Almost nothing in the inherited Beta-DM community sheet survived contact with the locked v2
architecture — and two of its defects were serious:

- **`J5` contact 1 carried permanent raw `+3V3`**, against D-057.
- **The community port had no power at all.** `01:ACC_3V3_SW` — the real switched rail at `U20` —
  and `09:ACC_3V3_SW`, fed by a **second, DNP** TPS22918 (`U15`) that nobody had noticed was
  there, were **different nets**. `01:ACC_5V_SW` reached nothing outside sheet 01.
- 26-pin 2×13 **male** header, fourteen XGPIO, `FAST_IO_GPIO43_HDR` (withdrawn by D-106),
  `RESERVED_NC`, and `R66` wired straight through with **no isolation FET**.

**This is the sixth consecutive migrated sheet on which an inherited `DNP` was load-bearing** —
`U16`, `R49`, `R50` and six TVS arrays. The pattern first recorded at FBV2-S1-007 held to the
last sheet without a single exception.

### The connector footprint was re-derived from the drawing

`J5` = Samtec **`BCS-112-S-D-HE`**, re-confirmed live: ACTIVE, 385 pieces ship tomorrow. The land
pattern comes from the Samtec **RECOMMENDED PCB LAYOUT, REVISION B, FIG 3** — the
`BCS-1XX-XXX-D-HE-XXX` figure specifically: **2.54 mm within a row, row-to-row .310 ±.002 in =
7.87 ±0.05 mm, .028 in = 0.71 mm PTH**, 27.94 mm pin field. **A vertical 2×12 pattern is not a
substitute — its rows sit 2.54 mm apart.** Odd = row A, even = row B, verified pin by pin against
the netlist; all 24 contacts match D-084. If JLC cannot place a through-hole part automatically
it becomes **manual/secondary assembly for the first five boards**; the connector architecture is
not compromised for SMT convenience.

### The buffer change is not cosmetic

The community port is **hot-plug** and its external segment is **3.3 V only**, so the TCA9517A's
level translation was never used while its hot-insertion and stuck-bus weaknesses were. From
SCPS270B, read in this session: the IN side is not joined to the OUT side until a **STOP or
bus-idle**; **1 V precharge** on all four SDA/SCL pins; **stuck-bus recovery at
`tSTUCKBUS` 25 ms MIN / 40 typ / 65 MAX** followed by **up to 16 pulses on SCLOUT**; **powered-off
high-impedance I²C pins**; 400 kHz max — **fast mode, not 1 MHz**.

**The circular dependency is broken.** `ARCHITECTURE.md` recorded it plainly: *"its disable
control, `ACC_PWR_EN` = `U3` P17, sits behind the bus it protects."* A wedged accessory required
the MCU to command the expander **over the very bus that was wedged**. The buffer now disconnects
and clocks the bus free by itself; `ACC_PWR_EN` is a second, manual lever rather than the only
one.

> **Normative accessory rule (D-177): never hold `EXT_SDA` or `EXT_SCL` low for longer than
> 25 ms** — the `tSTUCKBUS` **minimum**, not the typical. That is a hard limit on clock stretching
> and on slow bit-banged accessory firmware.

### The inherited pull-ups could not have worked

`R49`/`R50` were **4.7 kΩ and DNP**. With `tr` = 0.8473 × R × C and a 200 pF external bus —
≈ 20 pF board, 5 pF connector, ≈ 100 pF for 300 mm of cable, 50 pF module — 4.7 kΩ gives **796 ns
against a 300 ns fast-mode budget: it fails 400 kHz by 2.7× and only ever worked at 100 kHz.**

**1.5 kΩ gives 254 ns and passes fast mode on the static pull-up alone**, with the TCA4307's
2–5 mA rise-time accelerator as margin rather than as the mechanism. Static sink 1.93 mA, inside
the 3 mA an I²C device must sink. **Published accessory rule: ≤ 200 pF for 400 kHz, ≤ 400 pF for
100 kHz bring-up.** The internal bus keeps `R19`/`R20` 2.2 kΩ as its only pair (D-139); nothing
was added there, and no 1 MHz claim is made anywhere.

### Both current limits were re-derived rather than copied

SLVSFJ2B gives **`ILIM` = 1.18 × (R_ILIM in kΩ)^−1.072**, verified against three datasheet rows,
±25 % band.

**3.3 V rail — 1.5 kΩ retained, and it survived a budget that has grown.** The IR transmitter
(+50 mA burst average; its 150 mA peaks come from `C12` 22 µF, not the rail) and the front RGB
(+4.2 mA) push the internal worst case from 769 mA to **≈ 823 mA**. An accessory hard short at the
0.955 A worst-high limit now puts `+3V3` at **1 778 mA = 89 % of the TPS63020's 2 A** — margin
narrowed from 86 %, **still no foldback**. 1.21 kΩ would reach 102 %. Worst-low 0.573 A against
the published 400 mA leaves 43 % headroom.

**5 V rail — 1.65 kΩ retained**, 0.690 A typ / 0.52–0.86 A, 73 % headroom over the published
300 mA and inside the boost's 3.7 A switch limit. Setpoint re-checked at **4.99 V**; peak inductor
current **2.19 A** at `V_SYS` 3.0 V, so **`I_sat` ≥ 3 A is a requirement to confirm at BOM lock
(B-68)**. **Verified from the netlist to be electrically independent of USB `VBUS` and of the NFC
5 V fallback** — only `SYS` and the TPS61023 device family are shared.

**Published limits for the first five boards remain 400 mA and 300 mA TOTAL — the duplicate
contacts share one rail limit and do not multiply it.**

### Splitting the 5 V enables buys more than tidiness

`ACC_5V_EN` becomes **`ACC_5V_BOOST_EN` (`U3` P13 → boost `EN`)** and **`ACC_5V_SW_EN`
(`U23` P04 → switch `ON`)**, each with its own 100 kΩ pull-down — `R102` and the new **`R131`**,
which is mandatory because the TPS22950C's internal 500 kΩ smart pull-down does not satisfy its
own datasheet.

Two gains beyond the obvious. **Two independent series disconnects**: the TPS61023 has *true*
input-to-output disconnection in shutdown and the load switch adds reverse-current blocking, so a
single stuck enable can no longer energise the contact. And **the start-up time becomes a board
constant** — with the load switch still off, the boost starts into a known **44 µF** of
`C65`/`C66` instead of an unknown hot-plugged accessory.

The **5 ms** settle delay is derived, not guessed: the TPS61023 soft start is **700 µs typical
with no published maximum**, so the first build uses 7× typical and measures it (**B-69**).
**No PGOOD IC was added.**

### B-08 exists in copper for the first time

`Q10` 2N7002 between the WAKE contact and `WAKE_INT_N`, gate on `ACC_3V3_SW`. **Orientation is
load-bearing: source to the connector, drain to the internal line**, so with the rail off an
accessory pulling the contact down **reverse-biases the body diode** against the internal 3.3 V.
Reverse the FET and the body diode alone defeats the arrangement. A shorted or hostile accessory
therefore **cannot hold `WAKE_INT_N` low and cannot starve the internal buttons**. `R63` 10 kΩ
must pull to `ACC_3V3_SW`, not `+3V3`, or the contact stays live with the rail off. Recorded
honestly: a hostile accessory *driving* the contact to 5 V injects **≈ 3 mA** through the body
diode and `R66` — bounded, inside every clamp, and the reason `R66` is 330 Ω.

### The ESD arrays were all DNP; they are now fitted

**TI `TPD4E1B06DRLR`** — 4-channel bidirectional, **±12 kV contact / ±15 kV air-gap**, **0.7 pF**
I/O capacitance, 0.5 nA leakage, `VRWM` ±5.5 V. Four arrays cover all sixteen exposed signal
contacts. D-090 protected only the natives and the I²C pair, on the reasoning that the natives are
the only contacts with a direct MCU path; **that under-weighted the XGPIO**, which reach a
PCAL9535A whose destruction costs a board rather than a $0.55 chip. **Deliberately no TVS on
either power rail** — `VRWM` 5.5 V against a 5.0 V nominal rail leaves no working margin, and a
clamp that close leaks and ages. **`TPD2E009DBZR` leaves the BOM**: one TVS MPN now covers
everything.

An inconsistency in D-090 was also closed: **`ACC_DETECT_N` had no series resistor** despite being
exposed and running straight to a PCAL input. It now has 100 Ω like every other signal contact.

### Detect bounce is a firmware problem, and an RC would make it worse

Debounce is **20 ms assert / 20 ms de-assert in firmware**. A passive filter cannot be asymmetric:
the same time constant that suppresses insertion chatter **delays removal detection**, and removal
is the safety-critical edge because **MX-6 requires both rails down within 100 ms of detect loss**.
No RC was added.

### Eighteen abuse cases, none unacceptable

The full matrix is in the audit. Nothing lands on NOT ACCEPTABLE; two rows are firmware-dependent
by design and both are already binding clauses of D-092. Highlights: a reversed accessory cannot
ground contact 23, so **detect never asserts and neither rail is ever enabled**; a one-column
offset is prevented mechanically by the closed-ended recess; `EXT_SDA` or `EXT_SCL` held low is
disconnected within 25–65 ms and clocked free; and 5 V on a logic contact is clamped by the TVS
with 100 Ω limiting the residual into a **5 V-tolerant** PCAL input.

### A correction worth recording

Rebuilding sheet 09 deleted **`#FLG0105`**, a `PWR_FLAG` sitting on the Beta-DM community sheet
that turned out to be **the only power-output driver on the entire GND net**. Its loss made every
GND `power_in` pin in the design undriven. It has been **re-created on sheet 09 with the same
reference and a note explaining its role**, so it is never deleted by accident again. This is not
a fake power flag added to silence a check — it is the restoration of the check's only legitimate
satisfier.

### One new item for the CTO

**O-7:** `R49`/`R50` are 1.5 kΩ sized for a **200 pF** external bus, and that capacitance is an
estimate rather than a measurement. Accept 200 pF as the published 400 kHz ceiling, or drop to
1.0 kΩ and cover 300 pF for 1 mA more static sink. **One 0603 either way, footprint fitted**, so
it closes on the first measured board.

---

## 2026-08-23 — Buttons, expanders and the front RGB status light (FBV2-S1-008)

**Overall 53% → 55%. No gate in the twelve-gate table passed**; the task gate
**FBV2-S1-BUTTONS = PASS**. Full analysis:
[`audits/2026-08-23-s1-buttons-expanders-rgb-implementation.md`](audits/2026-08-23-s1-buttons-expanders-rgb-implementation.md).

**ERC 42 messages / 1 error / 41 warnings — the violation set is identical, line for line, to
the working tree this task resumed from, and better than the 45 / 2 / 43 that stood before
sheet 08 was touched.** Zero new errors. 319 components, 0 duplicate references, 0 without a
footprint, 0 `*_TBD` nets. `fork_equivalence.py` PASS, `netclass_probe.py` PASS, PCB still
bit-identical to Beta-DM. **Sheet 09 untouched.**

### This task was interrupted by a session limit and resumed, not restarted

All FBV2-S1-008 work existed as **uncommitted working-tree change** — nothing staged, no local
commits, local `master` equal to `origin/master` at `d894913`. The interrupted session had done
good work and it was kept: both expanders genuinely converted to `PCAL9535APW,118` with a
purpose-built symbol rather than a rename, addresses `0x20`/`0x21` preserved, HOME deleted
outright, volume buttons not invented, `TOUCH_INT_N` and `SX1262_DIO1` landed with matching root
plumbing, and the RGB part selected, symbolised and footprinted from the manufacturer drawing.
Zero DNP anywhere on the sheet — **the fifth consecutive sheet did not repeat the inherited-DNP
trap**.

It had also written an honest note into the schematic saying the pin budget did not close and
needed a ruling. **That diagnosis was correct**, and closing it is what this entry is about.

### 35 signals, 32 pins — the allocation genuinely fails

| group | pins | held down by |
|---|---:|---|
| safe-state control outputs | 5 | inherited, each with an external pull |
| user buttons | 6 | product lock |
| `TOUCH_INT_N` · `SX1262_DIO1` · `SD_CARD_DETECT_N` | 3 | FBV2-S1-003, D-108, **D-117** |
| `BQ25185_STAT1` · `BQ25185_STAT2` | 2 | **Ruling G** |
| `XGPIO0-9` | 10 | **D-082** |
| accessory control/status | 4 | D-089 / D-094 |
| `SX1262_RXEN` · `ACC_PWR_EN` | 2 | requirement / inherited |
| `RESERVED_SPARE` | 1 | **D-094** |
| front RGB | 3 | this brief |
| **total** | **35** | against **32** |

**Every escape route is closed.** There is **zero free native GPIO** — the ledger measures 33 of
33 assigned and GPIO35/36/37 are the octal PSRAM (B-10) — which also makes **the brief's own
WS2812 escape impossible**, because a smart LED needs RMT on a native pin and an expander cannot
produce it. `RESERVED_SPARE` is mandated by D-094. The ten XGPIO are locked by D-082, which
already surrendered the eleventh to pay for the fifth accessory-control pin. A dedicated I²C LED
driver would be a new part family, a new footprint and a new driver for one indicator.

### The answer is a third expander of the same part number

**`U23` = NXP `PCAL9535APW,118` at `0x22`** (D-165). It adds **no new MPN, no new footprint, no
new firmware driver and no new rail**, costs about $0.55 plus one 0603, and **retires B-37** by
leaving 12 spare I/O — the first slack this programme has ever had. Bus loading goes from five
devices to six: +6 pF maximum per line, ≈ 85 → 95 pF, rise time **158 → ~177 ns against the
300 ns fast-mode limit**.

**It carries the front RGB and the reserved spare, and nothing else** (D-166). That is how the
brief's rule *"preserve core/community/safety functionality before RGB when assigning pins"* is
satisfied **by construction**: delete `U23`, `D13` and `R124`–`R126` and the product loses its
status light and **not one other function**. Had the RGB kept `U2` P05–P07 and the charger
telemetry moved to the new part, declining it would have cost charge state and card detect —
exactly backwards. **Raised as O-6 for ratification.**

**It holds no interrupt source**, so it keeps the `FF` power-up mask and is never read while
servicing `WAKE_INT_N`. The third device costs **zero extra I²C traffic per event**.

### `RESERVED_SPARE` did not exist until now

D-094 has required a reserved expander resource since 2026-08-23 and **no sheet had implemented
it**. It exists now on `U23` P03 with `R130` 100 kΩ and `TP41`, which is where it belongs: a
reserve is worth more sitting beside twelve other free pins than alone on a full device.

`ACC_PWR_EN` is kept on `U3` P17 even though it drives only the DNP `U15`/`U16`, because
retiring it would leave two sheet-09 inputs undriven and sheet 09 is out of scope. **It is the
pin O-4 is expected to free.**

### The RGB is dark by construction, with no parts added to make it so

**`D13` = MEIHUA `MHPA3528RGBCT`, LCSC `C409779`** — confirmed live per D-096: in stock, 69 270
pieces. Common anode, PLCC-4 3.50 × 2.80 × 1.85 mm, 120°, water clear. **Pin 1 = anode,
2 = BLUE, 3 = GREEN, 4 = RED — not the `Device:LED_ARGB` order, which would have swapped red and
blue**, so a dedicated symbol and footprint were built from the manufacturer drawing.

The three resistors are **calculated separately and are deliberately unequal**, because the V_F
in the parts table is quoted at 20 mA and is useless at 1–2 mA; the numbers come off the Fig. 4
low-current curves:

| channel | R | V_F | nominal | corners |
|---|---|---:|---:|---|
| RED | **1 kΩ** | 1.75 V | **1.50 mA** | 1.18 – 1.70 mA |
| GREEN | **680 Ω** | 2.55 V | **1.03 mA** | 0.57 – 1.32 mA |
| BLUE | **390 Ω** | 2.60 V | **1.67 mA** | 0.86 – 2.17 mA |
| white | — | — | **4.20 mA** | 2.60 – 5.18 mA |

**Red gets the least current because it is the most efficient die** — 1070 mcd typ at 20 mA
against 500 for blue — giving roughly 80 / 87 / 42 mcd delivered.

**Default-off needs no external pull-ups.** Configuration 06h = `FF` at power-up makes the three
pins high-impedance inputs, so the cathode path is open and the only current is the **1 µA
leakage limit ≈ 0.05 mcd, invisible**; pull enable 46h = `00`, so the on-die 100 kΩ cannot light
it either; and Output port 02h = `FF`, so the pin **drives HIGH the instant it becomes an
output** — the anode potential — hence no glitch on the transition. **Three external pull-ups
would be three parts that do nothing** (D-169).

**ESD warning recorded in the symbol, the footprint and on the sheet: red is 2000 V HBM but
green and blue are only 150 V.**

**Front-facing is a requirement; the exact front position is deliberately NOT locked** — upper
bezel, lower bezel, beside the display or near the controls are all acceptable, it is **not** a
top-edge part, and it **must** sit behind a diffuser or light pipe with no protruding bare LED.
Placement and CAD own the final position.

### The PCAL9535A conversion is behavioural, and firmware must change

Verified against the primary source, **PCAL9535A Rev. 2, 23 January 2015**, retrieved and read
in this session. The pin-out is identical to the TCA9535 and no wire moved, but **the PCAL9535A
powers up with every interrupt masked, the exact opposite of the TCA9535 — unchanged firmware
sees no interrupts at all** (D-164). Two more contracts are now recorded: **write the Output
port register before the Configuration register**, or the five active-low resets and
`AMP_SD_MODE` glitch to their inactive state on the write that makes them outputs; and **`INT`
clears on a read of the input port register**, so firmware must read 00h/01h after the status
register or the line stays LOW and no further edge appears (D-171).

### Both charger status pins are landed, at 10 kΩ rather than Ruling G's 20 kΩ

SLUSF65A permits 1 kΩ–20 kΩ, so both are legal; 10 kΩ is a stiffer high against 1 µA of expander
leakage, reuses a value already dominant on the sheet, and its 0.33 mA flows only while the
charger is actually holding the pin LOW (D-170). **The decode is now recorded for firmware:**
STAT1 LOW = charging, STAT1 HIGH + STAT2 LOW = fault, both HIGH is **one** combined state
covering charge-complete, sleep and charge-disabled — which is why STAT1 alone was never enough.
**With no battery fitted STAT2 toggles forever**, so its interrupt mask bit stays SET by hardware
default and firmware polls it. That is precisely the capability the TCA9535 lacked, and it is
what makes D-061's family change load-bearing rather than cosmetic.

### The IR receiver reverts to AGC2 — O-5 closed

`U6` is **`TSOP38238`**, with **`TSOP38438` retained as a documented drop-in fallback** whose
symbol stays in the library (D-163). AGC2 is marked *Yes* for all six listed formats including
Sony, where AGC4 is marked **No**; the mechanism is the gap requirement — AGC2 needs > 5 × the
burst and takes 10–70 cycles per burst, AGC4 needs > 15 × and takes only 10–35, and SIRC breaks
the AGC4 limit. **The cost of the revert is the Fig. 15 high-modulation fluorescent suppression**
— a lighting-robustness margin, not a protocol. Every FBV2-S1-007 number survives untouched.

### Smaller findings

- **The switch MPN is real.** `PTS645SM43SMTR92LFS` appears as an orderable line: 1.6 N ± 0.3
  (~163 gf), 100 000 operations, 0.30 mm travel, SPST N.O. momentary, silver gull-wing SMD. The
  0.33 mA held current is **33× the datasheet's 10 µA minimum wetting current**, which had not
  previously been checked.
- **B-67 opened:** Littelfuse publishes **no bounce time** for the PTS645, so the schematic's
  earlier "≤ 5 ms" was not datasheet-backed. Use a 10–20 ms firmware window and measure.
- **Six root-sheet UUIDs were written with the prefix `fb080r00-`.** "r" is not a hex digit and
  KiCad silently reassigns invalid UUIDs on save, which would have destroyed pass traceability
  with no visible failure. Repaired.
- **Sheets 01 and 03 were touched only to publish nets the brief requires landing** — five and
  one local labels promoted to hierarchical, 28 and 5 lines of diff, no component, value,
  topology or DNP state changed (D-174). Without it, STAT1/STAT2 and card detect could not reach
  a PCAL input at all.
- **`MAX17048_ALRT_N` and `VBUS_PRESENT` remain test-point only.** D-089 had pencilled them onto
  `U2`; `TOUCH_INT_N` and `SD_CARD_DETECT_N` arrived later and outrank them. Twelve `U23` pins
  are free if that is ever revisited (D-166).
- **Noted, not actioned:** the project file still carries six stale ERC exclusion comments
  naming the retired `RGB_*_CTL` architecture and an unallocated `SD_CARD_DETECT`. They suppress
  nothing now; removing them strengthens ERC and is a separate hygiene task.

---

## 2026-08-23 — Infrared migrated (FBV2-S1-007)

**Overall 51% → 53%. No gate in the twelve-gate table passed**; the task gate **FBV2-S1-IR =
PASS**. Full analysis:
[`audits/2026-08-23-s1-ir-implementation.md`](audits/2026-08-23-s1-ir-implementation.md).

**ERC 45 → 45: zero added, zero removed.** Errors unchanged at 2, both inherited.
311 components, 0 duplicate references, 0 without a footprint, 0 `*_TBD` nets.

### The whole subsystem arrived DNP — for the fourth sheet running

`U6`, `D1`, `Q1`, `R21`, `R22`, `R23`, `R24` and `C11` all came from Beta-DM marked **`DNP`**.
Only `C12` was fitted — decoupling for a transmitter that was not there, exactly the pattern
found on sheet 06 with `C9`/`C10`. The brief opens with *"Full Beta v2 IR is a mandatory internal
feature"*, so **all eight are now fitted**.

**This is the fourth consecutive migrated sheet where an inherited `DNP` was load-bearing**
(sheet 09's `U16`/`R49`/`R50`/`U15`/`D2`/`D3`, sheet 06's `U5`/`J6`, now all of sheet 07). It is
no longer a coincidence: **a `DNP` on a Beta-DM sheet describes what was populated on that
reduced build, not what the architecture requires. Sheets 08 and 09 must be assumed to carry the
same trap.**

### The rating that binds is not the one that looks biggest

**`IFSM` = 1.5 A is a single-pulse surge for t ≤ 5 µs. It is not a remote-control rating.** The
figure that governs a 38 kHz burst train is **`IFM` = 200 mA**, specified at tp/T = 0.5 with
tp = 100 µs — a *longer* pulse at the same duty than a 38 kHz carrier produces, so the carrier
is less stressful than the specified condition, not more.

| candidate | % of `IFM` | avg LED power over an NEC frame | ΔTj | verdict |
|---|---|---|---|---|
| 100 mA | 50 % | 15 mW | 3.4 K | safe, leaves range on the table |
| **150 mA** | **75 %** | **25 mW** | **5.7 K** | **SELECTED** |
| 200 mA | 100 % | 35 mW | 8.1 K | **no tolerance margin left** |
| 300 mA | **150 %** | — | — | **REJECTED — out of spec** |

**Thermally none of these is difficult** — 25 mW against a 160 mW limit on a 230 K/W part. The
constraint is the repetitive rating, and it is hard. **Range is not the constraint either**: the
receiver datasheet quotes **45 m transmission distance using a TSAL6200 at only 50 mA**, and the
TSAL6100 at 150 mA is roughly 20× that intensity. Current buys off-axis margin, not headline
range.

### The supply preference is reversed — `+3V3`, not `SYS`

| | **`+3V3` (selected)** | `SYS` |
|---|---|---|
| resistor for 150 mA | **12 Ω** | 22 Ω |
| **peak across all tolerances** | **118–170 mA (1.44 : 1)** | **64–166 mA (2.6 : 1)** |
| as the battery drains | **nothing changes** | **IR range visibly shortens** |
| resistor dissipation | 0.27 W | 0.53 W |
| 38 kHz on the shared rail | ≈ 40 mV pk-pk | none |

**The noise objection that motivated `SYS` is real but bounded, and the one device that genuinely
cares is already behind 41 dB.** Everything else on `+3V3` lives with the audio amplifier's
**230 mA peaks** at 330 kHz, a 60 mA NFC field and ~100 mA of backlight boost. A 150 mA peak /
50 mA average IR load is the *smallest* pulsed load on the rail.

> **Scope, stated as fact and not as the reason:** `BQ25185_SYS` is a **sheet-01-local net**, so
> routing it to sheet 07 needs a sheet-01 edit this task is not authorised to make. **Had `SYS`
> won the analysis it would have been reported as blocked rather than quietly avoided.** It did
> not. The `ARCHITECTURE.md` source-select link is carried as **B-65**.

### `C12` was three times too small

Per carrier period the reservoir must supply `Q = I·D·(1−D)·T = 0.88 µC`, so ripple = 0.88 µC / C:

| `C` | ripple | % of rail |
|---|---|---|
| **4.7 µF (inherited)** | **218 mV** | 6.6 % |
| **22 µF (selected)** | **40 mV** | **1.2 %** |
| 47 µF | 19 mV | 0.6 % |

The package and voltage are specified deliberately — **1210 X7R 16 V** — because the requirement
is **≥ 15 µF *effective* at 3.3 V DC bias**, and a 6.3 V 0805 part would derate to roughly half
its marked value.

### The receiver's inherited filter turns out to be the load-bearing part of the sheet

`TSOP38238` → `TSOP38438` is a **pure MPN change** — same Minicast package, same pinning
1 = OUT / 2 = GND / 3 = VS, same footprint. `VS` 2.0–5.5 V, output **active low with an internal
30 kΩ pull-up**, so `OUT` drives GPIO44 directly and no external pull-up is needed.

`R21` 100 Ω + `C11` 4.7 µF match Vishay's application circuit exactly, and **Vishay prints the
topology but no values** — so ours had to be justified rather than inherited:

```
fc = 1 / (2 pi x 100 x 4.7u) = 339 Hz   ->   41 dB at 38 kHz
```

**Why that matters more than it looks:** datasheet **Fig. 7** shows the receiver's threshold
irradiance degrading from roughly **10 mV RMS of supply ripple *at the carrier frequency*** and
doubling by ≈ 50 mV — and our own transmitter runs at exactly that frequency. 40 mV pk-pk on the
rail becomes **≈ 0.1 mV RMS at `VS`, about 90× margin**. **This is what makes sharing `+3V3`
safe. Do not shrink `C11` for area without redoing this calculation.**

### Two inherited open items closed

**The AO3400A pinout is confirmed.** The AOS datasheet's SOT-23 top and bottom views show the
lone pin as **Drain** and the paired pins as **Gate** then **Source** — **1 = G, 2 = S, 3 = D**,
exactly what the symbol maps and the inherited wiring used.

**The `"Footprint BLOCKED: needs the official AOS recommended land pattern"` note asked for a
document that does not exist.** AOS publishes no land pattern in the AO3400A datasheet, so the
industry-standard IPC SOT-23 pattern applies and it becomes an ordinary FBV2-S2 item.

**Safe-OFF is proven, not assumed:** `R23` 100 kΩ with `IGSS` ≤ 100 nA holds the gate at
≤ **10 mV** against a **650 mV** minimum threshold — a 65× margin, so there is no IR emission at
boot, reset, GPIO high-impedance or a firmware crash.

### Protocol coverage — and a conflict inside the brief

`f0` = 38 kHz, 3 dB bandwidth `f0`/10 → 36.1–39.9 kHz. NEC / Samsung / Sharp / Mitsubishi sit at
full sensitivity; RC5/RC6 at 36 kHz and Sony at 40 kHz cost ~13–15 % of range, the ordinary
single-receiver compromise.

**But the brief §1 locks `TSOP38438` while §9 lists Sony/SIRC, and Vishay's suitable-data-format
table says those cannot both be true:** AGC4 is marked **"No" for Sony code** where the AGC2
`TSOP38238` is **"Yes"**. AGC4 is *"Preferred"* for NEC, RC5/RC6, Thomson RCA, Sharp and
Mitsubishi and adds **high-modulation fluorescent suppression (Fig. 15)** AGC2 lacks. Vishay's
framing: *"the higher the AGC, the better noise is suppressed, but the lower the code
compatibility."*

**The lock is a defensible trade, not an error.** Two things shrink it: **it is receive-only —
transmitting Sony/SIRC is completely unaffected**, and **reverting is a `lib_id` change** because
the `TSOP38238` symbol was deliberately retained in the project library. **Raised as O-5.**

### Power budget

150 mA nominal / 170 mA worst-case peak, 50 mA averaged over a burst, **≈ 17 mA averaged over a
whole NEC command**; receiver 0.35 mA continuous. **No new mutual-exclusion rule is proposed** —
MX-1 already covers concurrent high-power radio operation, and the brief says not to create rules
the power budget does not need.

### Nothing else was added

No second IR LED, no external IR accessory requirement, no multiple emitter angles, no extra
optical channels, no second receiver, no exotic carrier frequency, no dedicated LED-driver IC,
no RF-style test connectors, no analog optical detector, no new GPIO. `TP39` (LED current via the
drop across `R24`) and `TP40` (receiver output) added; `R123` DNP trim added with a hard 10 Ω
floor. **B-65 and B-66 opened.**

---

## 2026-08-23 — Audio migrated: microphone replaced, speaker locked (FBV2-S1-006)

**Overall 49% → 51%. No gate in the twelve-gate table passed**; the task gate
**FBV2-S1-AUDIO = PASS**. Full analysis:
[`audits/2026-08-23-s1-audio-implementation.md`](audits/2026-08-23-s1-audio-implementation.md).

**ERC 45 → 45: zero added, zero removed.** Errors unchanged at 2, both inherited.
308 components, 0 duplicate references, 0 without a footprint, 0 `*_TBD` nets.

### The finding that was not on the brief

**`U5` (the MAX98357A) and `J6` (the speaker connector) arrived from Beta-DM marked `DNP`.**
Nobody wrote that down — it is in the inherited file. It means **the entire speaker output path
has never been populated on any AQROOT board**, while `C9` and `C10` *were* fitted, decoupling
an amplifier that was not there.

The brief says voice output remains required and Full Beta v2 is the feature-complete design,
so **both are now fitted**. Everything below — the power budget, the speaker choice, the EMI
provision — describes a path being built for the first time, and bring-up should read it that
way.

**This is the third load-bearing inherited `DNP` in two tasks** (`U16`, `R49`/`R50`, `U15`,
`D2`/`D3` on sheet 09 at FBV2-S1-005). **A `DNP` on a Beta-DM sheet is a statement about the
reduced build, not about the architecture.** Every migrated sheet has to re-decide it.

### The microphone is not a drop-in

| | ICS-43434 | **DMM-4026-B-I2S-R** |
|---|---|---|
| pads | **6** | **7** |
| body | 3.5 × 2.65 × 0.98 mm | **4.00 × 3.00 × 1.00 mm** |
| extra pin | — | **`CONFIG`** — no ICS equivalent |

**The pin count differs**, so both a new symbol and a new footprint were built from the PUI
drawing (Rev A, 5/26/2021). The brief's instruction not to reuse the ICS-43434 footprint was
right for a stronger reason than size.

Every pin re-derived from the data sheet: `LR`→GND selects the **left** slot; **`CONFIG`→GND
is mandatory** (*"Pull to ground. The state of this pin is used at power-up."*); `VDD`
1.62–3.63 V with `C8` 100 nF; and **`R120` 100 kΩ on `I2S_MIC_DIN` is a data-sheet
requirement** — *"The SD trace should have a 100 kΩ pull down resistor to discharge the line
during the time that all microphones on the bus have tri-stated their outputs."* With one
microphone the line still tri-states for the entire unused half of every frame, and the
inherited sheet had no pull-down at all.

**No 1.8 V rail is needed, and that was the single largest risk in the substitution.** The part
is *rated* 1.8 V and PUI's catalogue line reads *"MICROPHONE -26DB 1.8VDC"* — a 1.8 V-only
microphone would have forced a regulator the brief forbids. The data sheet gives an operating
range of **1.5–3.6 V** (pin table 1.62–3.63 V), so `+3V3` and the existing decoupling are the
whole supply design. 820–1000 µA normal, **5 µA sleep**, 20 ms startup, −26 dBFS, 64 dB(A).

### The brief's suggested sample rate cannot be run on the wire

**The microphone's normal-mode input clock is 2.048–4.096 MHz**, and below 320 kHz it sleeps.

| frame | BCLK | verdict |
|---|---|---|
| 16 kHz × 32 | 0.512 MHz | **outside normal mode** |
| 16 kHz × 64 | 1.024 MHz | **outside normal mode** |
| 32 kHz × 64 | 2.048 MHz | exactly on the limit |
| **48 kHz × 64** | **3.072 MHz** | **the data sheet typical, and the MAX98357A's own test condition** |

The amplifier independently restricts LRCLK to 8/16/32/44.1/48/88.2/96 kHz, and 48 kHz is on
that list. **The bus runs at 3.072 MHz and firmware decimates to 16 kHz.** 16 kHz is still the
right *application* rate — it is not a legal *wire* rate for this part. On the bench this would
have looked like *"the microphone sometimes returns silence"*, which is what sleep mode looks
like.

**Everything else about the I²S architecture is valid unchanged**: `BCLK` and `LRCLK` shared,
`MIC_DIN` and `SPK_DOUT` separate, one ESP32-S3 controller in master full duplex. **No pin, net
or GPIO change**, so the GPIO ledger is untouched.

### A gain strap that was mismatched to the rail

Gain is referenced to a 2.1 dBV full-scale DAC output, so `output (dBV) = input (dBFS) + 2.1 +
gain`:

| `GAIN_SLOT` | gain | 0 dBFS asks for | 3.3 V rail gives | result |
|---|---|---|---|---|
| **GND (inherited)** | **12 dB** | **5.07 Vrms** | 2.33 Vrms | **clips above −6.8 dBFS** |
| **VDD (selected)** | **6 dB** | **2.54 Vrms** | 2.33 Vrms | **0 dBFS ≈ the rail** |

At 12 dB the **top 6.8 dB of the digital range was unusable** — clipped by the supply, not the
amplifier. At 6 dB the whole range is usable and the noise floor is lower. **Maximum acoustic
output is identical either way: it is rail-limited, not gain-limited.** One net, no BOM impact.

`SD_MODE` needs **no series resistor** — the data sheet requires ~2 kΩ only when
`VDD < VDDIO`, and here both are the same `+3V3` net. Recorded because it is exactly the part
that gets added "just in case". `R15` 100 kΩ to GND holds shutdown through reset and boot.

**Firmware safety rule, verbatim:** *"Do not remove LRCLK while BCLK is present … can cause
unexpected output behavior, including a large DC output voltage."* Into an 8 Ω voice coil that
is a burnt speaker.

### Speaker — PUI `AS02008MR-LW152-R`

Ø20 ± 0.2 mm × **3 ± 0.2 mm**, **8 Ω ± 15 %**, **0.5 W rated / 0.8 W max**, 86 ± 3 dBA at
0.1 W / 0.1 m, 5 % max distortion, resonance 500 Hz, **response 500–4000 Hz**, metal housing,
Mylar cone, Nd-Fe-B magnet, 2.4 g, **152 mm UL1571 AWG #32 leads, RED (+) / BLACK (−)**.

**The 500–4000 Hz response is the reason to choose it, not a limitation to apologise for.** The
brief asked for intelligible speech and explicitly not music; a driver that puts all of its
0.5 W into the speech band is louder where it matters than a wider-range driver the same size.
It also fits the existing `SPEAKER_ENVELOPE` with 1 mm of depth to spare.

**`J6` is retained** — JST `B2B-PH-K-S` was already the right connector. Mating side
**`PHR-2` + `SPH-002T-P0.5S`**, and JST's applicable wire range is **AWG #32 to #24**, so the
speaker's leads crimp straight in: **no soldering to fit it, no soldering to replace it** — the
same serviceability principle as the NFC antenna (D-128). AWG #32 is the small end of that
range, carried as **B-62** for a first-article pull test rather than asserted.

### Power and the volume ceiling

```
rail limit     3.3 / sqrt(2) = 2.33 Vrms  ->  2.33^2 / 8 = 0.68 W peak
cross-check    data sheet 0.93 W at 3.7 V x (3.3/3.7)^2  = 0.74 W     consistent
current        0.68 W / 0.90 / 3.3 V                      = 230 mA
```

| level | output | +3V3 | vs the 0.5 W rating |
|---|---|---|---|
| 0 dBFS | 0.68 W | 230 mA | above rated, under the 0.8 W max — short alerts only |
| **−6 dBFS (default)** | **0.17 W** | **57 mA** | comfortably inside, ≈ 89 dB SPL at 0.1 m |
| shutdown | — | **0.6 µA** | — |

**No new mutual-exclusion rule is proposed**: MX-1 already covers concurrent high-power
operations, and voice does not need maximum output during radio TX. Thermally irrelevant —
~75 mW in a 1666 mW package.

### EMI — nothing fitted, everything recoverable

The decisive evidence is the data sheet's own **Figure 14, "EMI with 12 in of Speaker Cable and
No Output Filtering"**. AQROOT's lead is 152 mm, **half** that, and the part already uses
edge-rate control plus spread-spectrum modulation around 330 kHz.

**First build: `R121`/`R122` fitted as 0 Ω — the speaker path is a plain wire — with
`C81`/`C82` 1 nF DNP.** If emissions ever need taming, swap the 0 Ω for a ferrite bead and
populate the shunts: four 0603 positions, no respin. A 0603 0 Ω adds ~50 mΩ, i.e. 15 mV at
300 mA against 8 Ω.

**PCB requirement: `SPK_P`/`SPK_N` as a tight, equal-length differential pair from `U5` to
`J6`** whatever is fitted — the most effective EMI control on a filterless Class D output, and
free.

### Acoustics, measured from the drawing

§8.3 is a raster drawing; it was rendered and the pads measured programmatically, and the
geometry closes against the printed dimensions to **0.01 mm**. Pads 0.60 × 0.40 mm, columns
±1.075 mm, rows 0.65 mm, **pad 4 is a GND ring ID 1.05 / OD 1.65 mm**, port on the width
centreline 1.28 mm from the nearest row and 1.00 mm from the short edge, port in the can
Ø0.25 mm.

**It is a bottom-port part: sound enters through a hole in the PCB, so the microphone sits on
the face OPPOSITE the shell aperture.** PCB hole **Ø1.05 mm NPTH** concentric with pad 4 (the
spec previously said Ø0.8–1.0 mm — this is now the manufacturer's number), Ø1.65 mm mask and
copper keepout, Ø2.5 mm component keepout, gasket ID ≥ 1.5 mm, tunnel ≤ 2.5 mm, ≥ 60 mm from
the speaker on opposite faces. **The Nd-Fe-B speaker magnet must also stay clear of the NFC
zone.**

### Echo — no hardware, one free lever

`SD_MODE` is a **hardware mute**: shutdown puts the outputs high-Z at 0.6 µA and removes the
amplifier's own noise floor from the microphone's environment, which a digital mute cannot do.
**First firmware should be half-duplex**, muting via `SD_MODE` while listening; ramp the
digital data down first, because there is no volume ramp-down on entering shutdown. Software
AEC later if barge-in is wanted.

### Nothing added, and no new CTO decision

No codec, no DAC, no analog microphone amplifier, no 1.8 V rail, no acoustic wake detector, no
buzzer, no headphone jack, no second speaker, no hardware AEC, no alternate footprint, no new
GPIO. **BOM consolidation, free: the microphone and the speaker are now both PUI Audio.**

**B-61–B-64 opened.** The microphone is confirmed in live distributor stock (DigiKey 2 807,
Arrow 10 000). **The speaker is not** — PUI's product page would not render here after three
attempts and Digi-Key search is bot-protected. Its datasheet is served live from PUI's API
today, but D-096 asks for a live listing and that is not one, so it is carried as **B-61**.

**One probe was extended rather than silenced.** `fork_equivalence.py` asserted the `.pretty`
directory was bit-identical to Beta-DM's, which stopped being true the moment a migrated sheet
locked a new part. It now asserts every **inherited** footprint is still bit-identical and none
was deleted, and that every **addition is declared** in an `ADDED_FOOTPRINTS` table naming the
task that added it. An undeclared footprint is still a failure.

---

## 2026-08-23 — I²C devices and IMU migrated (FBV2-S1-005)

**Overall 47% → 49%. No gate in the twelve-gate table passed**; the task gate
**FBV2-S1-I2C-IMU = PASS**. Full analysis:
[`audits/2026-08-23-s1-i2c-imu-implementation.md`](audits/2026-08-23-s1-i2c-imu-implementation.md).
New registry:
[`architecture/I2C_ADDRESS_REGISTRY.md`](architecture/I2C_ADDRESS_REGISTRY.md).

**ERC 46 → 45: zero added, one removed.** Errors unchanged at 2, both inherited.

### First: a number this programme has been repeating is wrong

FBV2-S1-004, 004B and 004C all quote **"ERC 68"**. The stored reports say **46**.

| report | messages | errors | warnings |
|---|---|---|---|
| `FBV2-S1-004-erc.rpt` | 46 | 2 | 44 |
| `FBV2-S1-004B-erc.rpt` | 46 | 2 | 44 |
| `FBV2-S1-004C-erc.rpt` | 46 | 2 | 44 |
| **`FBV2-S1-005-erc.rpt`** | **45** | **2** | **43** |

The **deltas** those tasks reported — "zero added, zero removed" — are correct and
reproducible from the stored files. Only the absolute figure was wrong, and it was carried
for three tasks. Sheet `04`'s migration genuinely took the count **64 → 46**.

A second trap, worth writing down because it will catch someone again:
`kicad-cli sch erc --severity-all` also counts **Exclusions** and reports **104** on the same
unmodified design. Every number in this programme is `--severity-error --severity-warning`,
matching the stored reports' own `Report includes: Errors, Warnings` header.
**Compare like with like or the gate is meaningless.**

### The BMI270 was re-derived, and it was already right

The brief said not to copy Beta-DM's straps blindly. Every one was checked against
**`BST-BMI270-DS000-08` Rev 1.6** (150 pages, fetched and extracted in full):

| pin | as drawn | Bosch |
|---|---|---|
| 1 `SDO` → GND | 0x68 | *"the default I²C address … 0b1101000 (0x68) … if the SDO pin is pulled to GND"* |
| 12 `CSB` → VDDIO | I²C mode | *"it is recommended to hard-wire the CSB line to VDDIO"* |
| 2 `ASDx` / 3 `ASCx` → VDDIO | secondary I/F unused | *"can be connected to VDDIO or left unconnected. **Do not connect to GND.**"* |
| 9 `INT2`, 10 `OCSB`, 11 `OSDO` → DNC | unused | *"If INT1 and/or INT2 are not used, please do not connect them (DNC)."* |
| `C6` / `C7` 100 nF at pins 5 and 8 | decoupling | *"recommended to use 100nF decoupling capacitors at pin 5 (VDDIO) and pin 8 (VDD)"* |

**Nothing was wrong.** That is the honest outcome and it is worth stating rather than dressing
up as a discovery (D-136). `VDD` 1.71–3.6 V, `VDDIO` 1.2–3.6 V, **no sequencing or slew-rate
constraint**, `tPO` 2 ms, FIFO 2048 B, 8 kB config upload after every POR. **`B-44` CLOSED**:
pad drive `IOH`/`IOL` ≤ 2 mA against a 323 µA load.

**One capability the brief asked about does not exist: the BMI270 has NO tap or double-tap
feature**, in any configuration. Its feature set is significant motion / any motion / motion
detect / no motion / stationary detect / wrist wear wakeup / wrist-worn step counter and
detector / activity change / push arm down / pivot up / wrist jiggle / flick in-out. So
wake-on-motion, significant motion, orientation, raise-to-wake (*"wrist wear wakeup"*) and the
FIFO are all supported; **tap is not**, and no hardware is proposed to compensate.

### The real defect was on the bus

Measured from the netlist rather than assumed — two expanders, the IMU, the fuel gauge, the
TCA9517A A-side, the touch controller through the 50-pin display flex, two test points, ~120 mm
of trace — the internal bus carries **≈ 85 pF worst case**.

| `R` | `t_r` = 0.8473·R·C at 85 pF | 100 kHz (1000 ns) | 400 kHz (300 ns) |
|---|---|---|---|
| **4.7 kΩ inherited** | **338 ns** | pass | **FAIL** |
| **2.2 kΩ selected** | **158 ns** | pass | **pass, 47 % margin** |

At a *typical* 60 pF, 4.7 kΩ gives 239 ns and passes. **That is the worst kind of defect — it
works on the bench and fails on the unit with the longest flex and the widest tolerances**, and
the programme's own 100 kHz-then-400 kHz bring-up rule would have found it late, on hardware,
as an intermittent. Sink current was checked before the change, as the brief required:
**1.32 mA at `VOL` 0.4 V**, against BMI270 2 mA, expander SDA 6 mA, the I²C-specification
minimum of 3 mA and an absolute floor of 967 Ω (D-139).

**There is exactly one pull-up pair on the internal net.** `R49`/`R50` are DNP and sit on the
switched accessory segment, on the far side of `U16`. The sheet note now says so, so nobody
adds a second pair helpfully.

### `0x68` becomes a rework instead of a respin

`SDO` was **hard-wired to GND**. Under D-049 that made an address collision a trace cut at a
0.25 mm pad. It is now `R118` 0 Ω **FIT** to GND (0x68) and `R119` 0 Ω **DNP** to `+3V3`
(0x69) — **fit one only; fitting both shorts `+3V3` to GND**.

**`0x68` is the single most collision-prone address on a community I²C bus.** MPU6050,
MPU9250, ICM-20948 and the DS3231/DS1307 RTC families all default to it, and those are exactly
the parts a hobbyist accessory is built from. **Reserving an address in a document does not stop
a $2 module from arriving at it.** Two 0603 pads, one populated (D-140).

### GPIO3: a timing proof, and a firmware constraint that falls out of it

1. `INT1_IO_CTRL` **resets to `0x00`** — the output driver is **disabled** at POR.
2. Firmware cannot enable it before the 8 kB config upload.
3. ESP32-S3 strap hold time **`tH` = 3 ms min**, and **GPIO3 defaults to "Floating"** with no
   internal pull, so `R110` alone defines the strap.

**The IMU physically cannot reach the strapping window.** And because `R110` is a pull-**down**:
**`INT1_IO_CTRL.od` = 0 (push-pull) and `.lvl` = 1 (active high) are MANDATORY; open-drain is
FORBIDDEN** — an open-drain output into a pull-down never produces an edge, and the interrupt
would be silently dead in a way that looks like a firmware bug for a week. GPIO3 = `RTC_GPIO3`,
so **EXT0/EXT1 deep-sleep wake works**, and active-high into a pull-down is exactly the polarity
it wants (D-137).

**Moving the interrupt behind a PCAL9535A is rejected** — it would put motion wake behind an
I²C transaction that cannot wake the SoC from deep sleep, `U2` is 16/16, and the boot-safety
reason that might have justified it does not exist.

### `INT2` stays DNC (D-138)

Bosch instructs DNC for unused interrupt pins; one pin is sufficient because *"if just one
interrupt pin is used all interrupts may be mapped to this interrupt pin"*, with the source read
from `INT_STATUS_0`/`INT_STATUS_1`; and two pins in latched mode would import a mapping
partition the design does not otherwise have. **`RESERVED_SPARE` is not consumed.** Pad 9 exists
on the land pattern, so a future second interrupt is a wire — which is what D-049 asks for.

### The IMU stays powered (D-141)

Accel-only low power is **down to 4 µA** plus **≈ 3 µA** of advanced features (10 µA spec'd at
25 Hz). A load switch would save **≈ 9 µA** while destroying wake-on-motion, forcing an 8 kB
config upload on every resume, and consuming one of the design's last expander pins. Nine
microamps is below the SoC's own deep-sleep floor.

### Land pattern verified — the "DO NOT ROUTE" note is discharged (D-143)

§8.3 is a **raster drawing**: no vector geometry, and nothing in the text layer but
*"Pad tolerance: ±50 µm"*. It was rendered at 12× and the pads measured programmatically,
calibrated on the printed 0.5 mm pitch. **Every printed dimension reproduces** — 0.5, 0.25,
0.475, 0.675, 0.925, 3.0, 2.5 — as do the pad sizes, the ±1.1625 columns, the ±0.9125 rows
and, critically, **the peripheral pin order 1–4 left / 5–7 bottom / 8–11 right / 12–14 top**.
That last one is the error that would have been fatal and silent.

### P-18 — characterised, not decided, and the characterisation moves the problem

**`U16` TCA9517A, `R49`/`R50`, `U15` and `D2`/`D3` are ALL DNP.** There is no fitted external
I²C path today, so whatever is chosen at Sheet 09 migration costs **no rework**.

TI settles the powered-off case: *"**VCCA is only used to provide the 0.3 × VCCA reference** …
**The TCA9517A logic and all I/Os are powered by the VCCB pin.**"* `VCCB` = `ACC_3V3_SW`, so a
de-asserted accessory rail leaves the buffer **completely unpowered and high-Z on both sides** —
a **harder** disconnect than an I²C mux, which stays powered.

**The weakness is not the buffer. It is the location of its disable control.** `ACC_PWR_EN` is
`U3` P17 — an expander output sitting behind the very bus a broken accessory would hold low. A
9-clock recovery pulse train frees the common case for nothing; a hard short escapes only via a
`+3V3` power cycle, because an MCU reset does not reset the expanders.

> **O-4 — NEW, REQUIRES A CTO DECISION.** Evaluate replacing `U16` with a **TCA4307-class
> hot-swap I²C buffer with stuck-bus recovery**, at Sheet 09 migration. The community header is
> a **hot-plug connector by definition**, and this is the only option that both **pre-charges on
> insertion** and **recovers a stuck bus without the host**. No rework cost, no net BOM, and the
> TCA9517A's one unique capability — level translation — is unused, because sheet `09` already
> declares *"COMMUNITY HEADER LOGIC = 3.3 V ONLY"* and `VCCB` is 3.3 V. Against: **not
> pin-compatible**, so the `U16` area must be re-routed, and the MPN must come from a **live
> listing** before any lock (D-096). **Nothing is implemented; `U16` remains TCA9517A.**

**No buffer of any kind solves address collision.** A repeater, a hot-swap buffer and a mux all
pass addresses through unchanged. That is a protocol problem, closed by the new registry (D-142)
and the `0x50` ID EEPROM — not by silicon.

### Blockers

**B-44 CLOSED.** **B-59 opened** — `ER-TPC035-6` touch-flex pull-ups unknown; direction is safe,
first-article measurement. **B-60 opened** — `0x36` and `0x38` are carried, not datasheet-cited;
every Analog Devices and FocalTech fetch failed here, and **a first-article bus scan closes it in
ten seconds**, which is more honest than editing a document.

### One inherited discrepancy, recorded and left alone

`U2`/`U3` still carry the schematic value **`TCA9535PWR`** while **D-061 locked NXP
`PCAL9535APW,118`**. The address base is identical (`0100 A2A1A0`), so nothing here depends on
it — and both parts live on **sheet 08**, which is not authorised in this task. Flagged now so
it is not discovered at BOM time.

---

## 2026-08-23 — NFC ferrite orientation corrected and first-build matching closed (FBV2-S1-004C)

**Overall 45% → 47%. No gate in the twelve-gate table passed**; the task gate
**FBV2-S1-NFC-MATCHING = PASS**. Full analysis:
[`audits/2026-08-23-s1-nfc-matching-closeout.md`](audits/2026-08-23-s1-nfc-matching-closeout.md).

**ERC 68 → 68: zero added, zero removed.** *(the 68 is a transcription error corrected in FBV2-S1-005 — the stored reports say 46 → 46. The delta was right.)*

### Two defects found that were not on the brief

**1. The RX divider would have over-driven the receiver.** At full field the first-build
network puts **49.5 V pk-pk differential** across the coil — **24.8 V pk-pk per side**. The
placeholder 47 pF / 220 pF divider has a ratio of 0.176 and would therefore have placed
**≈ 4.4 V pk-pk on `RFI1`/`RFI2`, against a 3.0 V regulated analog rail**. That is a
part-stress condition, not a tuning imperfection, and it had been carried since the topology
was first drawn without ever being checked against a real antenna voltage.

**2. The E24 grid is brutally steep at the series matching capacitor.** `C_s` sits close to
series resonance where `dZ/dC` is enormous, and the two E24 neighbours of the ideal 284 pF
are not close in effect at all:

| `C_s` per leg | Z differential | RF power | driver current |
|---|---|---|---|
| 270 pF | ≈ 16 Ω | 0.55 W | **≈ 257 mA — over budget** |
| *284 pF (ideal)* | *36 Ω* | *0.247 W* | *≈ 115 mA* |
| **300 pF (selected)** | **≈ 68 Ω** | **0.13 W** | **≈ 60 mA** |

### Antenna variant corrected — A → B (D-131)

**`FXC.46.52.0075X.A.dg` is superseded. `FXC.46.52.0075X.B.dg` is locked.** Verified verbatim
from Taoglas `SPE-24-8-104-B`: *"NFC Flex Antenna (46*0.3mm) with a **Reverse Ferrite Layer**
and adhesive backing"*, *"13.56 MHz Antenna"*, *"Diameter: 46mm"*,
*"FXC.46.52.0075X.B.dg - NFC with ferrite and 75mm Twisted Pair 28AWG cable with ACH(F)
connector"*, *"Peel and stick 3M adhesive"*.

Per APN-24-8-001 the variants differ **only in stack order**:

| variant | stack, outside → inside | intended mounting |
|---|---|---|
| A | flex antenna / ferrite / **adhesive** | onto a **PCB or component surface** |
| **B** | **adhesive** / flex antenna / ferrite | to the **INSIDE of the enclosure**, reading through it |

**AQROOT bonds to the inner rear shell and reads outward — the B case exactly.** With the A
version the ferrite would sit **between the coil and the tag**, which is the one place a flux
director must never be.

**Connector, cable, diameter, adhesive and interface are unchanged, so `J7` and the board
are unaffected.** This is a purchasing-line change caught **before antennas were ordered** —
which is exactly why FBV2-S1-004B surfaced it. **No `…A.dg` reference remains anywhere in
`hardware/beta-v2/`.**

### B-version parameters (D-132)

`La` **1.10 µH**, `Rs` **1.50 Ω**, `Q` **60.37**, `SRF` **395 MHz**; `ωL` = **93.72 Ω**.

The published triple is coherent to **~3 %** — `Q` 60.37 with 1.10 µH implies `Rs` 1.55 Ω
rather than 1.50 Ω, ordinary rounding between separately-published figures. Recorded rather
than smoothed over. `Rs` = 1.50 Ω is used for damping because that is the resistance which
physically adds to `R_q`. **The 395 MHz SRF is a large improvement on the A version's
148 MHz**, so the coil behaves as a clean inductor across the band.

### Target impedance derived, not borrowed (D-133)

**The previous 20 Ω/side figure is discarded — it was an assumption with nothing behind it.**

AN5276 offers two design intents: maximum power transfer, or *"a certain current
consumption"*. AQROOT has a locked budget (D-130: ≤ 150 mA from `+3V3` with the field on,
~20–30 mA of it reader overhead), so the second intent **determines** the target:

```
driver budget        115 mA x 3.3 V              = 0.380 W in
at ~65 % efficiency                              = 0.247 W RF
differential square wave at VDD_TX = 3.3 V:
  fundamental RMS = (4/pi) * 3.3 / sqrt(2)       = 2.971 V
  Z = 8.827 / 0.247                              = 35.7 ohm differential
```

> **First-build target: Z ≈ 36 Ω differential (18 Ω per side), Q ≈ 25.**

No EMVCo constraint applies, so Q is set purely by ISO/IEC 14443 bandwidth at 106 kbit/s.

### First-build matching set — and one deliberate bias (D-134)

| ref | was | **now** | basis |
|---|---|---|---|
| `R114`, `R115` | 1R0 | **1R1 1 %** | `Q` 62.5 → **25.3**; depends on the antenna alone |
| `C71`, `C72` | 300 pF | **300 pF** | ideal 284 pF; E24 chosen on the **safe, low-current** side |
| `C73`, `C74` | 1.8 nF | **1.5 nF** | re-solved for the resulting match |
| `L5`, `L6` | 220 nH | **39 nH** | EMC cut-off |
| `C69`, `C70` | 220 pF | **100 pF** | EMC cut-off |
| `C75`, `C77` | 47 pF | **27 pF** | RFI divider — safety fix |
| `C76`, `C78` | 220 pF | **620 pF** | RFI divider — safety fix |

**300 pF is chosen on purpose.** On a first board an *under*-driven antenna is a
one-component swap, while an *over*-driven one risks the driver and the `+3V3` budget on
first power-up. 187 mA of coil current in a 46 mm loop is still a serviceable field —
roughly 72 % of what the 36 Ω design would produce.

**B-56 is CLOSED.** With the 1.6 nF total shunt, 39 nH puts the EMC cut-off at
**20.1 MHz** — outside AN5276's forbidden 13–14 MHz band. **The previous 220 nH pair sat at
7.6 MHz, below the carrier**, and also presented 18.7 Ω of series reactance that was badly
perturbing the match.

**Every value is still marked `TUNE`, but `TUNE` now means "expected to move at first
article", not "unknown".** Each is a **CALCULATED FIRST-BUILD VALUE** with its arithmetic
recorded — a different thing from the placeholders it replaced.
**CALCULATED FIRST-BUILD VALUE is not FINAL TUNED VALUE.**

### RFI input safety (D-135)

```
old:  ratio 47 / 267  = 0.176   ->  24.8 V pp * 0.176   = 4.4 V pp   vs a 3.0 V rail
new:  ratio 27 / 647  = 0.0417  ->  24.8 V pp * 0.0417  = 1.03 V pp  -> > 3x headroom
```

Purely capacitive, no DC path; it adds ≈ 26 pF of shunt at the antenna node, small against
`C_p` = 1.5 nF. **No 5 V reference divider was reused blindly** — the ratio comes from this
design's own antenna voltage at 3.3 V. The receiver's exact linear range could not be
extracted from DS12484 (**B-58**), so the first-article `RFI` measurement is a **pass/fail
gate**, not an optimisation.

### AN5276 — closed on substance, not on process

ST's governing rules were obtained and applied: a one-stage EMC filter of series inductor
plus parallel capacitor; *"the EMC cutoff frequency must not be comprised between 13 and
14 MHz"*; an L-topology match of one series and two parallel capacitors in differential
topology; and a capacitive divider back into `RFI`. **The captured topology already matched
that description — only the values changed.**

**The Rev 6 PDF still would not load in this environment** — st.com and the Mouser mirrors
timed out, and a direct download returned bot-protection HTML. **B-48 is closed on
substance; the `STSW-ST25R004` run against a measured antenna impedance is carried as
B-57** and is required before fabrication.

### The 5 V fallback is preserved and was NOT tuned for

The first-build network is a 3.3 V design. Moving to ~5 V later needs a firmware supply
change (clear `sup3V`), **revalidation of matching, damping and the RFI divider** — the
driver amplitude rises ~1.5×, so `RFI` would sit near 1.5 V pk-pk, still inside the rail but
it must be re-checked rather than assumed — and possibly a passive retune. **It needs no PCB
respin, no antenna replacement and no ST25R3916 replacement.**

### First-article tuning is required before anything is called final

And it must be done with the **rear shell fitted, the antenna adhered in its final position,
the PCB installed, the battery installed and the ferrite in its final orientation**. Every
conductor and dielectric within a few centimetres is part of an inductive near-field antenna,
so bench tuning on a bare board proves nothing about the product. The ten-step procedure —
measure installed impedance, run the tool, verify resonance, Q, differential match, `RFI`
voltage and driver current, then NFC-A/B/F/V tags and read/write distance through the shell —
is in the audit.

### Mechanical

Antenna **`FXC.46.52.0075X.B.dg`**; **adhesive side directly against the inner rear
surface**; field **outward through the rear plastic shell**; **ferrite faces inward** toward
the PCB and battery. **≥ 48 × 48 mm** clear zone, no battery or speaker-magnet overlap, no
screws or bosses through the active zone, no 433 MHz flex crossing it. No enclosure
external-size change.

### Nothing new added, and no new CTO decision requested

No AAT varactors, no extra RF switch, no extra external 433 connector, no custom NFC PCB
antenna, no RF TVS. The one candidate considered — an **E48 280 pF `C_s`** to land exactly on
36 Ω instead of 68 Ω — was rejected for the first build because it commits to a target
impedance nobody has measured yet. **It is a first-article component choice.**

---

## 2026-08-23 — NFC IC and antenna FINAL LOCK (FBV2-S1-004B)

**Overall 43% → 45%. No gate in the twelve-gate table passed**; the task gate
**FBV2-S1-NFC-ANTENNA-LOCK = PASS**. Full analysis:
[`audits/2026-08-23-s1-nfc-antenna-closeout.md`](audits/2026-08-23-s1-nfc-antenna-closeout.md).

**ERC 68 → 68: zero added, zero removed — the violation lists are identical.** *(the 68 is a transcription error corrected in FBV2-S1-005 — the stored reports say 46 → 46.)*
301 components, 0 duplicate references, 0 without a footprint.

### B-06 is closed

*"NFC is undesigned, not merely unrouted"* has been on the blocker list since the
pre-design audit. It is not true any more. **Crystal, matching topology, antenna,
connector and supply all exist.** What remains is *tuning*, which is a bench activity,
not a design gap.

### NFC IC locked — P-17 CLOSED (D-126)

**`ST25R3916-AQET`. The B variant is not adopted.** CTO reasons as given: non-B is active
production; it **preserves capacitive low-power sensing**; AQROOT is not an EMVCo payment
terminal; AWS is not worth trading sourcing simplicity and feature breadth for; and the
first build already has 3.3 V operation plus a no-respin 5 V fallback. This agrees with
FBV2-S1-004's recommendation on independent grounds — the non-B is the **only one of the
two with an LCSC part number (`C5267441`)**, and therefore the only one with a JLCPCB
assembly path, at roughly half the unit cost.

**MPN metadata verified present in the schematic, not merely in prose:** `Value`, `MPN`,
`Manufacturer` and `LCSC` all carry it.

`U9`'s `Package` description was **rewritten**. It still named `NFC_5V_PA_PENDING` as the
supply and told the reader the RF and oscillator pins were *"on explicit named TBD nets —
DO NOT ROUTE"*. Both statements stopped being true in FBV2-S1-004.

### NFC antenna locked — B-53 CLOSED (D-127)

**Taoglas `FXC.46.52.0075X.A.dg`, off-board.** Verified verbatim from `SPE-22-8-131-C`:

| | |
|---|---|
| Description | *"Circular Form Factor Flexible Near Field Communications Antenna"* |
| Frequency | **13.56 MHz** |
| Diameter | **46 mm** |
| Ordering line | *"Thickness: 0.27 mm - FXC.46.52.0075X.A.dg - NFC with ferrite and 75mm Twisted Pair 28AWG cable with ACH(F) connector"* |
| Adhesive | *"Peel and stick 3M adhesive"* |
| Typical interrogation distance | **40 mm** |

**This replaces the abstract 45 × 45 mm custom-antenna assumption.** It keeps the antenna
**off the main PCB**, which is what avoids putting a 45 × 45 mm keepout through the ground
plane of a board that already carries three radios.

**The electrical triple — `L` = 1.09 µH, `Rs` = 1.6 Ω, `Q` ≈ 58 — is used as supplied, and
it checks out internally:** `ωL/Rs` = 92.87 / 1.6 = **58.0 exactly**. It could **not** be
re-extracted from the datasheet, whose electrical table is an image, so it is recorded for
first-article confirmation (**B-55**) — which costs nothing, because the match has to be
re-derived from measurement regardless.

### Board-side connector — mating proven (D-128)

**`J7` = JST `BM02B-ACHSS-GAN-ETF`.** ACH series, 2 circuits, 1.20 mm pitch, SMT, gold,
**2.0 A / 50 V**, −25…+85 °C, 1.4 mm high × 4.3 mm wide; **Active, 30,004 in stock,
$0.52 @ 1, MOQ 1**.

**Mating is proven, not assumed:** the header's mating housing is **`ACHR-02V-S`** — an ACH
receptacle, which is exactly the *"ACH(F) connector"* Taoglas fits to the `FXC.46` cable —
and the antenna's 28 AWG wire is the gauge JST rates the series at. **The antenna is
replaceable without soldering.** KiCad's footprint is named for this exact MPN.

**Correction to the brief: JST classes ACH as a TOP-ENTRY header, not right-angle.** JST's
own words: *"the socket half is mated with the header from the vertical direction, while
the wires come out from the horizontal direction of the socket connector."* Digi-Key's
parametric says "Right Angle", which most likely describes the cable exit; Newark, JST and
KiCad's own footprint name all say top entry / vertical. **The part is right and
unchanged** — the consequence is that **`J7` needs mating clearance above it** while the
cable leaves horizontally. FBV2-P1 placement note.

### Matching network — one number that can be trusted, and one that must not be built (D-129)

**`R114`/`R115` (`R_q`): 0 Ω → `1R0 TUNE`. This is the solid value**, because it depends on
the antenna alone:

```
Q0       = wL / Rs = 92.87 / 1.6      = 58.0     (far too high for ISO14443 bandwidth)
R_total  = wL / 26                    = 3.57 ohm
2 * R_q  = 3.57 - 1.6                 = 1.97 ohm  ->  R_q = 1R0 per leg,  Q = 25.8
```

**`C71`/`C72` (`C_s`): 100 pF → 300 pF. `C73`/`C74` (`C_p`): 100 pF → 1.8 nF.** Both follow
from an L-match lifting the damped 1.8 Ω per side to an **assumed 20 Ω per side** driver
target — the right shape and the right order of magnitude, **not a validated match**,
because AN5276 still would not load.

> **`L5`/`L6` and `C69`/`C70` were deliberately NOT re-derived, and are now inconsistent
> with the network around them.** With `C_p` at 1.8 nF the shunt on that node rose by an
> order of magnitude, and 220 nH against ~2 nF resonates near **7.6 MHz — below the
> 13.56 MHz carrier**, which would attenuate the carrier rather than the harmonics.
> **NOBODY MAY BUILD TO THE CURRENT EMC VALUES.** The on-sheet note says so in those words.
> **B-56.**

Everything stays `TUNE`, everything is 0603 and hand-reworkable, and **switching to the 5 V
fallback is a re-tune of these same passives, never a respin**.

### NFC field current — B-54 downgraded (D-130)

DS12484's current tables still would not text-extract, so this is derived and labelled as
such: a 3.3 V differential square-wave driver into the assumed 40 Ω differential match
delivers ≈ **0.22 W** of RF; at 60–70 % driver efficiency that is **95–112 mA** from `+3V3`,
plus ~20–30 mA of reader-mode overhead.

> **Budget ≤ 150 mA from `+3V3` with the field on.**

Against D-092's enforced case (1.16–1.32 A) that takes the TPS63020 to **≈ 66–74 % of 2 A**
— comfortable — and **MX-1 means the NFC field is never concurrent with LoRa TX anyway.**
**No simultaneous RF operation is claimed.** The datasheet figure or a bench measurement is
still owed before fabrication.

### Mechanical

**NFC antenna clear region: 48 × 48 mm minimum** — 46 mm antenna plus installation
tolerance. Rear upper region, no battery overlap, ferrite face toward the internal
electronics and ground plane, no speaker-magnet overlap, no bosses or screws through the
active zone, and the stored 433 MHz flex must not cross it. **No enclosure external-size
change.**

Two constraints follow from the parts rather than the zone: **`J7` needs vertical mating
clearance**, and **the antenna cable is 75 mm**, so `J7` must sit within 75 mm of routed
cable length of the antenna position — cheap to honour now, expensive after placement.

### Nothing prohibited was added

No full RF test connector, no AAT varactor network, no extra RF switches — no technical
blocker required any of them. `TP37`/`TP38` on the antenna terminals, `TP32` on
`NFC_SUPPLY` and the accessible `R106` FIT / `R107` DNP source-select links were already in
place. `J7` is the interface the locked antenna requires, not an addition.

**A reference collision was caught before it reached the netlist:** the new connector was
first drawn as `J6`, which is already the speaker connector on sheet `06`. It is `J7`.

### Flagged for CTO decision — the ferrite is directional

Taoglas catalogues an otherwise identical **reverse-ferrite** version of this same 46 mm
antenna with the same ACH(F) cable. Which one is correct depends on which face bonds to the
enclosure wall: the ferrite must end up **between the coil and the metal it is shielding** —
the PCB ground plane and the battery. **Zero board change and zero schematic change either
way; it is a purchasing line item** — but ordering the wrong orientation costs a lead time,
not a rework, so it must be settled against the actual enclosure stack **before the first
antennas are ordered**.

### Not done, and not claimed

Sheets `05`–`09`, the PCB, mechanical CAD, firmware and the Beta-DM / frozen-Beta trees
untouched. **No RF tuning performed and none claimed.** B-48, B-49, B-50, B-51 and B-52
remain open from FBV2-S1-004.

---

## 2026-08-23 — Radios and NFC migrated (FBV2-S1-004)

**Overall 40% → 43%. No gate in the twelve-gate table passed**; the task gate
**FBV2-S1-RADIOS-NFC = PASS**. FBV2-S1 is **4 of 9 sheets**. Full analysis:
[`audits/2026-08-23-s1-radios-nfc-implementation.md`](audits/2026-08-23-s1-radios-nfc-implementation.md).

**ERC: 4 errors → 2. Total 86 → 68. Zero added, eighteen removed.** This is the first
migration task to *reduce* the project's error count, and it did it by deleting
placeholder architecture rather than by suppressing anything.

**Zero `*_TBD` nets remain anywhere in the project.** Sheet 04 alone retired fourteen.

### RF architecture locked (D-118)

| band | architecture |
|---|---|
| **433 MHz / CC1101** | **INTERNAL** flex. `U7` IPEX → 100 mm coax → Taoglas `FXP450.07.0100C` against a plastic wall |
| **915 MHz / SX1262** | **EXTERNAL.** `U8` IPEX → short pigtail → **top-panel SMA female bulkhead**, user-changeable |

**Neither band has a motherboard 50 Ω RF trace, matching network, RF switch or diplexer.**
Both modules present their own matched 50 Ω port, so the board's RF involvement at 433 and
915 MHz is *zero copper*. This **supersedes the internal-FXP890 plan for 915 MHz** in
`12 - RF and Antenna Plan v0.1`; 433 MHz is unchanged.

**The `U7` IPEX socket must stay service-accessible with the shell open.** If internal
433 MHz performance disappoints on the first units the flex unplugs and an external pigtail
replaces it — **no PCB respin**. That is an FBV2-P1 placement constraint, and it is the
whole reason the internal antenna is an acceptable first-build risk.

### 433 antenna verified, mating proven rather than assumed (D-119)

Taoglas datasheet `SPE-23-8-180-A`, verbatim: *"410-470MHz Flexible PCB Antenna with 100mm
1.37 IPEX MHFI"*. **47 × 17 × 0.28 mm**, adhesive mount, gain −0.36 / −1.57 / −0.05 dBi,
**Active, 54 in stock, $5.52 @ 1, MOQ 1**.

**The connector question is settled by two documents, not by inference:** the antenna
terminates in **IPEX MHF I**, and Ebyte's manual lists the `E07-400M10S` interface as
**IPEX-1 / stamp hole**. MHF I, IPEX-1 and U.FL are one mating interface. No cable variant
is required.

**Mechanical reservation recorded for FBV2-P1:** plastic wall, LEFT/LOWER-SIDE region,
**not laid on the PCB**, and clear of the LiPo, the NFC loop and its ferrite, the speaker
magnet, large ground pours, metal bosses, the USB shell, the 915 bulkhead and pigtail, and
the IR structures. The 100 mm cable decouples the antenna body from the module, so the zone
is a mechanical choice.

### 915 external interface defined (D-120)

`U8` **IPEX-1/MHF-I plug** → **1.13 mm or RG-178, 100–150 mm** → **SMA FEMALE bulkhead**.
Loss **≤ 0.3 dB** at 915 MHz — negligible against +22 dBm.

**Female is deliberate.** The 915 MHz LoRa ecosystem is SMA-male antennas onto female
jacks; RP-SMA is a Wi-Fi convention and would force users onto an adapter for nothing. No
proprietary interface.

**The interface is locked; the assembly MPN is not** — under D-096 a pigtail part number
must come from a live listing (**B-51**). Top panel: **≥ 8 mm** edge-to-edge between the SMA
body and either IR aperture, pigtail clear of the optical path (**B-52**, no CAD created).

### Both module stamp-hole feeds are now explicit no-connects (D-121)

`U7.21` and `U8.21` `ANT` are the alternative 50 Ω stamp-hole pads; AQROOT feeds both
modules through their IPEX sockets. `CC1101_ANT_TBD`, `RF_ANT_TBD`, `CC1101_RF_TBD` and
`SX1262_RF_TBD` are retired — **the last two were orphan labels on stubs connected to
nothing, and were two of the project's four ERC errors.**

### NFC supply — B-41 CLOSED (D-122)

`U9` pin 8 `VDD` and pin 10 `VDD_TX` leave the Beta-DM boost output and sit on
**`NFC_SUPPLY`**; `VDD_IO` stays on `+3V3`. First build **`NFC_SUPPLY` = `+3V3`** through
the `R106` FIT link; the `R107` DNP link is still the one-resistor 5 V fallback. **NFC is
never connected to the community 5 V rail.** **Firmware must set `sup3V`.**

The select network built in FBV2-S1-001 finally drives something:

```
/NFC_SUPPLY  (7)  R106.2 R107.2 TP32.1 C19.1 C55.1 U9.8[VDD] U9.10[VDD_TX]
```

Sheet 01 received **two label changes and one `PWR_FLAG` — no component, value or topology
change**: its `NFC_SUPPLY` label became hierarchical so the net can leave, and its
`NFC_5V_PA_PENDING` hierarchical label became local because that net no longer needs to
cross. The root crossing was **renamed rather than removed and re-added**, so no ERC entry
was created. The `PWR_FLAG` is **D-102-compliant**: the rail is genuinely `+3V3` through a
0 Ω link, KiCad cannot propagate a driver across a passive, and **the netlist is unchanged
by it**.

### NFC clock resolved (D-123)

DS12484 §2.2.8: *"The quartz crystal oscillator operates with 27.12 MHz crystals."*

**`Y1` = 27.12 MHz, 10 pF load, SMD 3225 4-pad**, with `C79`/`C80` **10 pF 50 V C0G TUNE**.
Candidate **`TXM27.12M0004322DBBDO00T`, LCSC `C362365`** — ±10 ppm, ESR 30 Ω, −40…+85 °C,
**3,420 in stock, $0.078**, JLCPCB-compatible, and a **candidate against a live listing,
not a lock** (D-096).

Load-cap sizing is stated openly rather than asserted: `C_L = C/2 + C_stray` gives ≈ 14 pF
ideal, **ST's own NUCLEO and DISCO boards populate 10 pF**, so the design starts at 10 pF
and trims — the right value depends on finished-board stray capacitance that does not exist
yet.

### NFC front end — real topology, honest values (D-124)

```
RFOx ── L_EMC ──┬── C_EMC ── GND
                ├── C_p   ── GND        (two trim positions, on purpose)
                └── C_s ── R_q ── NFC_ANT_x ── TP37 / TP38
NFC_ANT_x ── C_rx_s ──┬── C_rx_p ── GND
                      └── R_rx ── RFIx
```

Every part is **0603 and hand-reworkable**; every RF capacitor is **50 V C0G**, because the
antenna tank swings far above the 3.3 V driver supply and a 16 V part there would be a
latent field failure.

Two deliberate choices: **`C_EMC` and `C_p` are two separate shunt footprints on one node**,
giving two trim positions instead of one; and **`R_q` is fitted at 0 Ω rather than omitted**,
so raising damping is a component change and not a bodge.

> **All values are INITIAL and labelled `TUNE`.** They cannot be finalised until the
> 45 × 45 mm antenna impedance is measured and **STSW-ST25R004** is run against it, and
> **AN5276 could not be retrieved this session** — every st.com fetch timed out (**B-48**).
> **No value here is presented as an ST reference figure.**

`TP37`/`TP38` on the antenna terminals are not optional diagnostics — without probing those
two nodes the network cannot be tuned at all.

**Unused pins are explicit no-connects with recorded reasons**, not undecided ones:
`AAT_A`/`AAT_B` (AAT drives external varactors, and DS12484 warns against AAT with hardware
wake-up), `CSI`/`CSO` (capacitive sensing unused), `EXT_LM` (the internal load modulator is
used), `MCU_CLK` (the ESP32-S3 has its own clocks).

### CC1101 and SX1262

`U7`: SPI-B unchanged, `CSN` with a 10 kΩ pull-up so it is deselected through reset, `GDO0`
to GPIO15, `GDO2` still omitted, `VCC` = `+3V3`, decoupling local. No reset pin exists — the
CC1101 is reset by SPI command.

`U8`: SPI-B unchanged, `BUSY` **direct to GPIO8**, `NSS` direct with a pull-up, `NRST` from
the expander. **`SX1262_DIO1` is published as a hierarchical net** for sheet `08` to land on
the internal PCAL9535A (D-089) — it no longer reaches the MCU, because GPIO38 is now
`NATIVE_A`. Semtech §13.3.4 confirmed DIO1 is a level-holding, SPI-cleared IRQ, so an
expander input is a safe destination and a stuck-high DIO1 can no longer touch a strapping
pin, which was the reason for moving it. `DIO2`→`TXEN` on-module, `RXEN` from the expander,
`DIO3` internal TCXO at 2.2 V. LoRa deep-sleep packet wake remains **not a requirement**.

### Power budget — one rail change, and it is not yet covered (D-125)

Sheet 04 adds no new rail. But with `VDD`/`VDD_TX` on `+3V3`, **the NFC PA load moves off
`BQ25185_SYS`-via-`U13` and onto the TPS63020**, drawing proportionally more current at
3.3 V for the same field power.

**`I_VDD_TX` at 3 V supply mode was not extracted this session (B-54)**, so D-092's
58–66 % TPS63020 figure **must not be quoted as covering the NFC field in this form**.

**MX-1 is unchanged and binding: at most ONE of {Wi-Fi TX, LoRa TX +22 dBm, sub-GHz TX, NFC
field} at a time.** Firmware constraints recorded by this sheet: set `sup3V`; enable SX1262
**DIO2-as-RF-switch** or `TXEN` never asserts and TX silently fails; configure the driver
for **TCXO**; drive all three bus-B chip selects high before init and use a bus mutex.

### ESD — nothing added, and that is the finding

The 915 MHz bulkhead sees only the E22's own matched front end through a shielded pigtail —
no board trace, no exposed IC pin. An RF TVS transparent enough not to cost link budget at
+22 dBm is a real choice with real loss; **measure before adding**. The NFC loop is
magnetically coupled with series capacitors acting as a DC block. The module coax is
internal and shielded. **No random RF TVS parts were fitted.**

### Recommended, not locked — both need CTO sign-off

**P-17 — keep the non-B `ST25R3916-AQET`.** Same 32-UFQFPN package; Mouser 3,243 in stock;
**LCSC `C5267441` at ~$3.37 gives a JLCPCB assembly path the B does not have**, at roughly
half the unit cost. The B's advantages are EMVCo PCD L1 3.2a compliance and a better AWS
implementation — **AQROOT is not an EMVCo terminal**, so neither serves a stated priority,
and the B's `-AQWT` variant is a stock trap (0 units, restock quoted January 2028).
Switching would also require AN5768 and re-proving footprint equivalence. Flagged rather
than locked because it touches read range at the margin.

**B-53 — NFC antenna architecture.** Recommendation: **purchased flex + ferrite**. A
main-board loop needs a **45 × 45 mm keepout in the ground plane on every layer** in the
rear upper third, with the battery directly behind it. **The schematic is neutral**:
whichever is chosen lands on `NFC_ANT_A`/`NFC_ANT_B` and the front end does not change.

### Opened

**B-48** AN5276 not retrieved; matching values are initial. **B-49** IPEX socket population
must be confirmed with the supplier for the exact ordered `U7`/`U8` MPNs — the whole
zero-board-RF plan collapses if stamp-hole units arrive. **B-50** FXP450 bend radius,
adhesive and clearance guidance not retrieved. **B-51** 915 pigtail MPN not selected.
**B-52** SMA-vs-IR top-panel spacing recorded but no CAD. **B-53**, **B-54** as above.

### Not done, and not claimed

Sheets `05`–`09` untouched. PCB untouched and still **bit-identical** to Beta-DM. No
footprint verified with a pad-overlap assertion (**B-29**). No RF tuning performed — and
none is claimed.

---

## 2026-08-23 — Display, touch, backlight and microSD migrated (FBV2-S1-003)

**Overall 37% → 40%. No gate in the twelve-gate table passed**; the task gate
**FBV2-S1-DISPLAY-SD = PASS**. FBV2-S1 is **3 of 9 sheets**. Full analysis:
[`audits/2026-08-23-s1-display-sd-implementation.md`](audits/2026-08-23-s1-display-sd-implementation.md).

### The inherited `J1` would have produced a dead display, twice over

`J1` still used the **2.8-inch `CH280QV10_CT_50P`** pin table while its Value and
Footprint fields already read `FH69-50S-0.5SH`. Pin count matched, connector matched,
ERC was silent. The pin **functions** did not match the locked `ER-TFT035IPS-6`:

| panel pin | old symbol | ER-TFT035IPS-6 | consequence |
|---|---|---|---|
| 1 / 2 / 3 | LEDK / LED-A1 / LED-A2 | **LEDA / LEDK / LEDK** | **backlight reverse-biased — no light** |
| 4, 5, 6 | LED-A3, LED-A4, IM0 | **NC** | anodes driven into NC pins |
| 7, 8, 9 | IM1, IM2, IM3 | **IM0, IM1, IM2** | by luck all three were already `+3V3` = `1 1 1` |
| **36 / 37** | WR_RS → `DISP_DC` / RS_SCL → `SPI_A_SCK` | **WRX(SCL) / D-CX** | **clock and D/C swapped — no valid command ever reaches the panel** |
| 46 | CTP_IRQ, unused | CTP IRQ | touch interrupt not represented at all |

**Neither fault is visible from a pin count, a connector MPN or an ERC run.** A new
project-library symbol **`ER-TFT035IPS-6_50P`** was authored with the vendor's table
verbatim, deliberately keeping the old pin geometry so the migration is a
pin-function change rather than a redraw. `CH280QV10_CT_50P` stays in the library —
Beta-DM still uses it — and is dropped from sheet `03`'s symbol cache.

**The PO must name BOTH `ER-TFT035IPS-6` and `ER-TPC035-6`. The vendor's CST340 touch
variant is NOT authorised without a new engineering review** — the FT6236 address,
the driver and the `TOUCH_RST_N` enumeration pulse are all locked around FT6236.

### `R111` fitted — GPIO45 closed (D-111)

10 kΩ, `GPIO45_VDDSPI_STRAP` → GND. VDD_SPI is now held LOW deterministically instead
of relying on the chip's internal pull-down alone. `TP1` retained, no capacitance on
the net, no peripheral on GPIO45.

### B-43 closed with a primary source (D-116)

TPS61169 datasheet **SNVSA40B**: **`R_PD` — CTRL pin internal pull-down resistor —
300 kΩ**, with `V_H`/`V_L` = 1.2 / 0.4 V and `t_SD` = 2.5 ms.

**`CTRL`'s only internal element pulls DOWN.** There is no mechanism by which the
backlight driver can raise the GPIO46 strap. With `R108` 10 kΩ in parallel GPIO46 sees
**9.68 kΩ to GND** — stronger than the strap provision alone — and the backlight is off
through reset by construction. `R109` is retained: its strap-escape justification is
retired, but a fitted 0 Ω costs nothing as a general isolation point. **GPIO46 strap
safety was not weakened for backlight convenience.**

### Backlight re-derived, not copied (D-115)

From SNVSA40B `V_REF` = **188 / 204 / 220 mV**:

* **`R69` = 1.87 Ω ±1 %** — an E96 stocked value, so no substitution was needed.
  **I_LED = 100.5 / 109.1 / 117.6 mA.** The panel is rated **120 mA maximum** with a
  90 mA life point: the worst-case corner sits **2.0 % below the maximum and never
  above it**. Per-LED current *falls* from 20 mA to 18.2 mA, so LED life improves.
* **`R70`–`R73` = 4 × 33 Ω in parallel = 8.25 Ω** on the single `LED_A` node. Four
  footprints retained and repurposed: quarter the per-part dissipation (24.6 mW in an
  0603 rated 100 mW) and three DNP-able trim steps available as pure rework.
* **Peak switch current 263 mA at 1.2 MHz (4.6×) and 309 mA at the 0.75 MHz minimum
  (3.9×)** against the 1.2 A minimum limit. `L3` 10.7×. **`D8` NSR0240 at 2.1× is the
  tightest item and is retained**; a same-footprint 0.5 A uprate is recommended, not
  required. **B-32 closed** — `C43` 4.7 µF X5R sits on `U17` `VIN`.

### Display SDO — **DNP**, and the reasoning is on the record (D-114)

The vendor says of pin 33 *"leave the pin open when not in use"* and does **not**
specify SDO's high-Z behaviour while `CSX` is high. SPI-A is shared with the microSD.

**The risk is asymmetric: fitting `R112` puts a core feature at risk of bus contention
to gain a feature nothing uses — AQROOT never reads the display.** `R112` is therefore
**0 Ω DNP**, with `TP36` on the panel side so SDO release can be characterised on the
first board without fitting anything. This closes **B-28** with the *opposite* default
to the one FBV2-DISP-002 sketched, which wrote "fit a 0 R" before weighing which of the
two features is load-bearing. **No series resistance was added to the `SPI_A_MISO` bus
itself** — the microSD `DAT0` path stays direct.

### Touch gains an interrupt

`CTP_IRQ` (panel pin 46) was not represented at all on Beta-DM. It now leaves the sheet
as **`TOUCH_INT_N`** and lands on an internal PCAL9535A input with sheet `08`. FT6236 at
**0x38** and the `TOUCH_RST_N` safe state are unchanged. **No second I²C pull-up pair
was added** — the internal bus keeps its single locked `R19`/`R20` pair, and a
panel-side pair would halve the effective pull-up for nothing. **`RESERVED_SPARE` was
not consumed.**

### microSD — the `*_TBD` net is gone (D-117)

`SD_CARD_DETECT_TBD` was a **one-pad net**: a switch terminal with no pull and no
destination. It is now **`SD_CARD_DETECT_N`** — `J2.10` DET-SW with **`R113` 100 kΩ to
`+3V3`**, `J2.11` DETECT_LEVER grounded — a real two-state signal whose destination is
an internal PCAL9535A input on sheet `08`. Polarity assumes the usual push-push
convention (**LOW = card present**); the Molex drawing would not load, so this is
assumed, not confirmed (**B-46**) — and the exposure is nil, because polarity is a
firmware constant on an expander input, never a board change.

Molex `5025700893` is **retained** — no lifecycle, mechanical or electrical reason to
change it was found. DAT1/DAT2 stay NC as validated on Beta-DM.

### `J1` footprint audit (D-113)

Measured from the footprint file: **50 pads, 0.500 mm pitch with no drift across all 49
gaps, 24.500 mm span, 0.300 × 1.230 mm pads, 2 hold-downs at ±14.365 mm.** Every
measurable parameter **PASSES** against the archived Hirose figures.

**FH52E is NOT claimed as a drop-in and `J1` did NOT move to the FH52E land pattern.**
FBV2-DISP-002 proposed that on the strength of a Hirose note that FH69 *also* fits the
FH52E pattern — which proves one direction only. Full footprint **and mechanical**
equivalence was not demonstrated from both drawings, so it is not asserted.
**Consequence: there is currently no JLCPCB assembly path for `J1`** (FH69 is not in
LCSC; FH52E is, as `C7465440`). **B-47** — settle at FBV2-S2, before placement.

### SPI-A stays passive

Both chip selects are pulled to `+3V3`, so display and microSD are deselected through
reset. **No bus mux and no series damping were added** — damping belongs with real trace
lengths, which do not exist until FBV2-P1. The ILI9488's 18-bit / 3-byte-per-pixel SPI
writes are accepted with **no architecture change and no new native GPIO**.

### Battery target unchanged

The backlight is the only load this task moved: **+11 mA at the pack** at default
brightness (118 → 129 mA). Runtime improves for any baseline browsing current above
**44 mA**, and the Beta-DM backlight alone draws 118 mA — so **60 × 75 × 8 mm /
~2500–3000 mAh gives equal or better runtime by a wide margin.** At a representative
250 mA the ratio is 1.20 at 2500 mAh and 1.44 at 3000 mAh.

### A latent defect caught by inspection, not by a check

The `LED_BOOST` netclass listed the four old anode nets by exact name and had no entry
for the new single `LED_A`, so the anode would have fallen to **Default clearance** at
FBV2-P2. `netclass_probe.py` reads the *board*, which is still Beta-DM, so no probe
would have caught it. `/03_SPI_A_DISPLAY_SD/LED_A` was added to `LED_BOOST`.

### ERC

**4 errors → 4 errors; the error report is byte-identical to after FBV2-S1-002.** Total
63 → 64: two `isolated_pin_label` warnings added for the `TOUCH_INT_N` crossing, one
removed because `SD_CARD_DETECT_TBD` ceased to exist.

Sheet `03` carries **18 inherited `pin_to_pin` warnings** — DB17–DB0 tied to a flagged
`GND` net. The count is unchanged from Beta-DM and **they were deliberately not
silenced**: re-typing the panel's parallel data pins as `passive` would clear all 18 and
would also make the symbol lie about the part.

### Not done, and not claimed

Sheets `04`–`09` untouched. PCB untouched and still **bit-identical** to Beta-DM. No
footprint verified against a vendor drawing with a pad-overlap assertion (**B-29**). No
MPN newly locked. **B-15** unchanged.

---

## 2026-08-23 — Power-tree rulings closed, MCU core migrated (FBV2-S1-002)

**Overall 34% → 37%. No gate in the twelve-gate table passed**; the task gate
**FBV2-S1-MCU-CORE = PASS**. FBV2-S1 itself is **2 of 9 sheets**. Full analysis:
[`audits/2026-08-23-s1-mcu-core-implementation.md`](audits/2026-08-23-s1-mcu-core-implementation.md);
measured pin ledger and strap audit:
[`architecture/GPIO_LEDGER.md`](architecture/GPIO_LEDGER.md).

### P-20 closed — `R95` = 560 Ω, and B-27 is amended rather than left wrong

Recovery current recomputed from the captured circuit: **8.36 mA** at VBUS 5.0 V into
a 0 V pack, **7.93–8.80 mA** across 4.75–5.25 V. That is inside the accepted 5–10 mA
band and restores the ≈ 8 mA the architecture assumed, which is what **B-26** is
measured against.

**680 Ω was not an arbitrary capture value.** It is exactly the value that produces
B-27's recorded ≈ 13 mA single-fault ceiling: `(5.00 − 0.32 + 4.2) / 680 = 13.06 mA`.
With 560 Ω the ceiling becomes **≈ 15.9 mA nominal, ≈ 16.6 mA worst case** — 0.0066 C
on a 2500 mAh pack, still bounded by `R95`, still unidirectional through `D12`, still
self-annunciating. **B-27 is restated in place.** The trade is explicit: ~21 % more
recovery current for ~22 % more single-fault current, and the CTO ruled for recovery.

### P-21 closed — OV trip **derived**, not typed

The datasheet threshold was obtained first (LTC4368, Farnell mirror `2243878`):
`V_OV` **492.5 / 500 / 507.5 mV** rising, hysteresis **20 / 25 / 32 mV**, UV/OV leakage
**10 nA max**, features page "Adjustable **±1.5 %**".

`R77` **4.02 M → 3.65 M 1 %**, `R78` unchanged at 442 k:
`0.500 × (3.65 M + 442 k) / 442 k` = **4.629 V**.

| | |
|---|---|
| Nominal trip | **4.63 V** |
| Comparator + 1 % resistors | **4.48 – 4.78 V** |
| Including 10 nA max pin leakage | 4.44 – 4.82 V |
| Release (25 mV hysteresis × 9.258) | **4.40 V** nominal |

Above a 4.35 V-class pack with 129 mV of worst-case margin, 420 mV below the 5.05 V
first capture, and **no lockout hazard** because release sits above the float voltage.
`3.65 M` is already carried by `R91`, so this **removes** a BOM line.

### P-22 closed — scripted KiCad edits, under eight conditions

The blanket Beta-DM prohibition is superseded by **D-107**: deterministic; narrowly
scoped; source-controlled and diffable; the project parses afterwards; netlist
validation; ERC against a stated baseline; preservation checks; and the output
reviewed against the CTO task item by item. **Scripts may not be used to bypass
engineering review** — a script that cannot show all eight is an unreviewed change.

### `02_MCU_CORE` migrated

* **GPIO38 = `NATIVE_A`** and **GPIO47 = `NATIVE_B`** — the two native community
  fast-IO signals (D-084/D-108). `SX1262_DIO1` **no longer reaches the MCU**; under
  D-089 it terminates on the internal expander `U2`, which is sheet `08`.
* **GPIO46 = `DISP_BL_CTL`.** GPIO46 is a strapping pin that **must read LOW at reset**
  — GPIO0 = 0 alone does not select Joint Download Boot, GPIO46 = 0 is also required.
  Three provisions make that safe: **`R108` 10 kΩ pull-down at the pin** (Espressif's
  own "strong pull-down" against the 45 kΩ internal pull), **`R109` 0 Ω FIT** isolating
  the TPS61169 `CTRL` so the strap survives even if `CTRL` sources current — failure
  direction "backlight off" — and **`TP2` on the strap node** so the level is measured.
  No capacitance was added; Espressif forbids bulk C on strapping pins.
  Quantified: any `CTRL` internal pull-up **≥ 30 kΩ** keeps GPIO46 below `V_IL`.
* **GPIO43 withdrawn from the community port** (D-106) — internal UART0 TXD only, with
  **`TP35`**. Consequence recorded: GPIO44 is IR RX, so **UART0 is TX-only**, and ROM
  download recovery is via the native **USB Serial/JTAG on GPIO19/20, never UART0**.
* **GPIO3 strap defined — B-09 CLOSED** (D-109). `R110` 10 kΩ pull-down. LOW is the
  only correct level: GPIO3 = 1 would select external JTAG on MTMS/MTDI/MTCK/MTDO =
  **GPIO39–42, which are the I²S bus**. **BMI270 `INT1` is bound to push-pull
  active-high; open-drain must never be configured on this pin.** The IMU cannot corrupt
  the strap at reset — `INT1` is high-Z until firmware enables it.
* **`R111` 10 kΩ GPIO45 pull-down placed DNP.** GPIO45 selects VDD_SPI (LOW = 3.3 V) and
  today is held only by the chip's internal pull-down while an exposed test pad sits on
  the net. Fitting it is referred to the CTO — see below.
* `TEST_GPIO45` / `TEST_GPIO46` renamed to `GPIO45_VDDSPI_STRAP` / `DISP_BL_CTL_STRAP`
  under D-100.

**`NFC_IRQ` verified still on GPIO18.** B-19 holds: it must never move to GPIO46.

### No new debug hardware

**D-110.** The service interface is the native USB Serial/JTAG on GPIO19/20 — one
USB-C cable gives console, ROM download and JTAG debug. No debug connector, no debug
IC, no JTAG header, no new user-facing button; `SW1` BOOT stays electrically real and
becomes mechanically recessed. **One test pad added — `TP35` on UART0 TXD** — because
the ROM boot log is the only view of a board whose USB will not enumerate, which is the
one failure USB cannot diagnose. An `EN` pad was considered and **rejected**.

### ERC

**5 errors on the Beta-DM baseline → 4. Zero new errors. `02_MCU_CORE` reports nothing
at all.** Warnings 55 → 63. All eight additions are root-sheet `isolated_pin_label`
entries on cross-sheet signals with one end drawn: `NATIVE_A`/`NATIVE_B` (await sheet
`09`), `SX1262_DIO1` (awaits sheet `08`), `FAST_IO_U0TXD_ROOTPROBE_CS` (dies with the
20-pin port). **Each was left standing deliberately** — silencing them by adding a test
point to an orphaned net is the same anti-pattern as a `PWR_FLAG` that hides a missing
driver.

### Opened

**B-43** TPS61169 `CTRL` internal-pull spec **not retrieved** — TI's PDF text layer
would not extract. The design is safe for any pull-up ≥ 30 kΩ and `R109` is the escape,
but the number is a blocker, not an assumption.
**B-44** BMI270 `INT` pad drive current **not retrieved** — Bosch's PDF likewise.
Fallback: `R110` → 47 kΩ, a value change with no board change.
**B-45** `NATIVE_A`/`NATIVE_B` still have **no D-090 series resistors and no TVS**. They
are the only two contacts with a direct MCU path. Sheet `09` work.

### Referred to the CTO

**Fit `R111`?** GPIO45 relies on the internal pull-down alone to hold VDD_SPI at 3.3 V,
with an exposed test pad on the net; a GPIO45 that reads HIGH at reset selects 1.8 V and
the 3.3 V flash and PSRAM do not boot. **Recommendation: fit it.** Placed DNP rather
than fitted because changing the electrical design of a strapping pin is a CTO call, not
a capture decision.

### Not done, and not claimed

Sheets `03`–`09` untouched. PCB untouched and still **bit-identical** to Beta-DM. No
footprint verified. No MPN locked. **B-15** unchanged — no telemetry crossing to
`U2`/`U3` exists.

---

## 2026-08-23 — Full Beta v2 power tree CAPTURED (FBV2-S1-001)

**The first Full Beta v2 design-file work.** `hardware/beta-v2/` is created, forked
from Beta-DM, and `01_power_tree.kicad_sch` now carries the Full Beta v2 power
architecture. Full analysis:
[`audits/2026-08-23-s1-power-tree-implementation.md`](audits/2026-08-23-s1-power-tree-implementation.md).

**Overall 31% → 34%. FBV2-S1 does NOT pass.** Its exit criterion requires *every*
schematic change in the migration order to be landed. One sheet of nine carries the
v2 architecture; the other eight are byte-equivalent copies of Beta-DM. What passes
is the task gate **FBV2-S1-POWER-TREE**.

### What is now in the file

136 parts on `01_POWER_TREE`, all with footprints assigned:

* **Battery reverse protection, P2** — `J4` → `F1` 5 A → `BAT_RAW` → `Q2` (stage A)
  → `BAT_MID` → `Q3` (stage B) → `BAT_SENSE` → `R75` 15 mΩ → `BAT_PROTECTED_P` →
  `U11` BAT. Controller `U18` LTC4368-1: `RETRY` grounded (latch-off), `UV` unused
  via 510 k to VIN per the datasheet, `OV` divider, 22 k/4.7 nF gate RC, `SHDN`
  pull-up with an N-FET pull-down, `D9` secondary negative clamp. Two stages in
  **two packages**, common-source pairs — **B-01 is closed at schematic level.**
* **Autonomous dead-cell recovery** — `U19` TLV7032 with a ratiometric polarity
  bridge (matched `D10`/`D11` Schottkys make the trip supply-independent at
  `BAT_RAW` = 0 and block pack drain when USB is absent), a handoff comparator
  asserting below ≈ 2.63 V of pack, a three-input **series** AND (`Q6`/`Q7`/`Q8`),
  `Q9` inverting `FAULT`, and `Q5`/`R95`/`D12` injecting current-limited,
  unidirectional charge. USB-powered and firmware-independent.
* **Accessory power** — `+3V3` → `U20` TPS22950C → `ACC_3V3_SW` and `BQ25185_SYS` →
  `U21` TPS61023 (4.99 V) → `U22` TPS22950C → `ACC_5V_SW`, both `FLT` pins wire-ORed
  onto `ACC_POWER_FAULT_N`. **D-088 BOM consolidation honoured exactly**: `L4` is the
  same Würth MPN as `L2`, `R99`/`R100` are the same 732 k/100 k divider as `R44`/`R45`,
  `C65`/`C66` mirror `C34`/`C35`. One boost family, one load-switch family, differing
  only in `R_ILIM` (1.5 k and 1.65 k, the values D-086/D-087 specify).
* **NFC no-respin source select** — `R106` 0 Ω **FIT** from `+3V3`, `R107` 0 Ω **DNP**
  from the boost.
* **Telemetry** — `VBUS_PRESENT` divided to 2.97 V at VBUS 5.0 V, so raw VBUS never
  reaches the expander; `LTC4368_FAULT_N`; `ACC_POWER_FAULT_N`; 19 test points.

### ERC: zero introduced

Beta-DM baseline **58** → Beta-v2 at resume **60** → Beta-v2 now **55**. The lists were
diffed, not counted. **Nothing was added.** Three inherited violations were retired: a
dangling root `BAT_PROTECTED_P` label, and two `isolated_pin_label` on
`BAT_CONNECTOR_P`, which was a one-pad net in Beta-DM and is now real.

**This is not "ERC clean" and must not be quoted as such.** 55 inherited violations
remain on the unmigrated sheets and belong to FBV2-S2.

Three defects were closed to get there: the missing `BAT_PROTECTED_P` label on the
`U11` pin-2 stub; a `PWR_FLAG` on `VREC_VCC`, whose drive arrives through `R84` and so
cannot be inferred by ERC — the electrical connection to VBUS was already correct and
no net was joined, split or renamed; and an orphaned wire and label left on the **root**
sheet when the `BAT_PROTECTED_P` hierarchical pin was removed.

### `U18` package corrected — a locked decision had been contradicted

`U18` LTC4368-1 had been assigned a **DFN-10 with an exposed pad**. FBV2-PWR-002 locks
the package policy for this circuitry: *"leaded and inspectable … no BGA, no WLCSP, no
bottom-terminated parts."* A DFN-10 is bottom-terminated, on the most safety-critical
part on the board. Corrected to `Package_SO:MSOP-10_3x3mm_P0.5mm` (the locked candidate
is `LTC4368IMS-1#PBF`, MSOP-10) in both the sheet and the project symbol library.
**The land pattern is still unverified** — that is FBV2-S2.

### `R_FB_TOP 1M` — an inherited net-name defect, fixed in v2

A literal net label reading `R_FB_TOP 1M` — a value annotation placed as a label.
`R39` is indeed 1 MΩ. The net is the TPS63020 `+3V3` feedback midpoint; renamed
**`V3V3_FB`** in `hardware/beta-v2/` only. Beta-DM is frozen and keeps it. All 56 labels
on the sheet were audited for embedded values, spaces, near-duplicate rails and isolated
single-pin nets; nothing else was found, and no correct name was touched.

### Fork provenance is now measured, not asserted

`checks/fork_equivalence.py` re-derives the classification of every forked file from
disk; `reports/FBV2-S1-fork-equivalence.md` pins the result. Sheets `02`–`09` are
byte-equivalent after normalising the project name **only**; `.kicad_pcb`, `.kicad_dru`,
both lib-tables and all 12 project footprints are **bit-identical**; `.kicad_pro` differs
by project name alone, so no design rule or netclass changed. `hardware/beta-dm/`,
`hardware/beta/` and `hardware/beta/mechanical/` are unchanged.

`checks/netclass_probe.py` had been copied without repointing and was still testing
**Beta-DM's** files from inside the v2 tree. Repointed; still PASS.

### Opened

**B-41** `NFC_SUPPLY` has no consumer — `U9` `VDD`/`VDD_TX` are still on
`NFC_5V_PA_PENDING` on sheet `04`, which this task could not modify. The v2 NFC supply
architecture is **half implemented**.
**B-42** the NFC source select is mutually exclusive **by fit state only**; fitting both
0 Ω links shorts `+3V3` to the boost output. Needs an assembly-note requirement.
**P-20** `R95` = 680 R against a locked 560 R. Injection falls to ≈ 6.9 mA, moving the
wrong way against **B-26**. Recorded, **not** silently changed — a value in a locked
architecture is changed by a ruling, not by a capture task.
**P-21** `OV` trip captured at 5.05 V against a documented ≈ 4.6 V.
**P-22** the standing *"no automatic KiCad file generation"* rule was overtaken: this
capture was scripted. Recorded in place and flagged for ratification or reinstatement
rather than treated as repealed.

### Recorded

**D-099** `U18` package corrected to MSOP-10. **D-100** net names describe nets, not
component values. **D-101** `TP34` added on `BAT_CONNECTOR_P`. **D-102** `PWR_FLAG` is
permitted only where a rail is genuinely driven and KiCad cannot infer it — never to
silence an error. **D-103** `BAT_PROTECTED_P` is local to `01_POWER_TREE`.

### Not done, and not claimed

No PCB work of any kind — `aqroot-Beta-v2.kicad_pcb` is still the Beta-DM board, bit for
bit, and does not match this schematic. No footprint verified. No MPN locked. Sheets
`02`–`09` untouched. `B-15` stays open: the `VBUS_PRESENT` divider exists but no charge
or VBUS telemetry crossing to `U2`/`U3` does.

---

## 2026-08-23 — Community connector CORRECTED and final-locked (FBV2-COMM-002)

Documentation only. No design file touched. `hardware/beta-v2/` was not created.

**This entry corrects an error rather than adding progress, and the percentage is
held at 31% accordingly.**

### Harwin `M20-7881242` is rejected

The CTO's lifecycle finding stands and is corroborated:
**`harwin.com/products/M20-7881242` returns HTTP 404** — the part number does not
resolve to a live catalogue item.

It should never have been recorded as locked. **The MPN was configured from the
Harwin catalogue's ordering scheme** (`M20-78` + `8` for double row + `12` per row
+ `42` for gold+tin) rather than taken from a live listing, and FBV2-COMM-001's own
limitations section said so in as many words: *"It should be verified against a
live distributor listing before the BOM is issued."* The flag was right; the part
was written into the locked documents anyway.

That gap is now closed by rule rather than by intention. **D-096: a part number
configured from an ordering scheme is a hypothesis, not a selection. Every MPN
entering a locked document must first be confirmed against a live manufacturer or
distributor record showing lifecycle status and stock.** It applies to every
subsequent selection in the programme.

`M20-7881242` has been struck through in place — not deleted — in
`CTO_DECISIONS.md`, `ARCHITECTURE.md`, `MECHANICAL_INTERFACE_SPEC.md`,
`PROGRESS.md` and the FBV2-COMM-001 changelog entry.

### Connector re-locked: Samtec `BCS-112-S-D-HE`

.100 in / 2.54 mm, **2 × 12 / 24 contacts**, **FEMALE** Tiger Claw™ dual-beam
receptacle, **horizontal (right-angle) entry**, **through-hole**, **30 µin
selective gold** in the contact area with matte tin on the tail (D-093).

**ACTIVE**, with **385 pieces shipping next-day** from Samtec at **MOQ 1**
($7.314 @ 1, $5.667 @ 100). Digi-Key lists the series as *Active*. Body
**30.48 (L) × 8.13 (D) × 5.33 (H) mm**. **4.6 A per contact** mated with TSW,
450 VAC / 636 VDC, **−55 to +125 °C**, glass-filled LCP UL94 V-0, UL E111594,
halogen-free, MSL 1.

**The footprint is new and is not interchangeable with anything already drawn:**
2 × 12 plated through-holes, 2.54 mm within a row, **7.87 ± 0.05 mm *between*
rows** — the horizontal-entry tails splay outward — with **0.71 mm drills** and a
27.94 mm end-hole span. B-29 is re-scoped to this pattern.

### Why the locked MPN is `-S` and not the `-L` that was proposed

This is what verifying the extended-life information was for.

Samtec's own design-qualification report (187544 Rev 1) gives **100 mating cycles
for BOTH** the 10 µin (`-L`) and 30 µin (`-S`) gold options. The E.L.P.
extended-durability data — **2 500 cycles** — is qualified **by similarity at
30 µin gold only**.

So at `-L` the community port would have been rated **100 cycles**, which is
*worse* than the 300 gold cycles of the part just rejected. For a
**user-swappable community port on a maker platform, mating-cycle life is a
first-order product parameter**, not a detail. The `-S` upgrade costs **$2.88 per
board at quantity one — roughly $14 across the first five boards** — for the only
plating with extended-life evidence behind it. Same body, same footprint, one
character of the part number. **`BCS-112-L-D-HE` is retained as a plating-only
cost-down alternate requiring no board change.**

**Recorded honestly as B-39:** the 2 500-cycle figure is **by similarity**, and the
only count formally qualified for BCS itself is **100 cycles**. Samtec must confirm
the rating for `BCS-112-S-D-HE` before the production run. The design assumption
for the first five boards is *"≥ 100 cycles qualified, 2 500 supported by
similarity at 30 µin gold."* **It is not claimed as 2 500.**

### Commodity 2.54 mm compatibility is preserved — with one rule

BCS accepts standard **0.64 mm (.025 in) square posts**, and the horizontal-entry
engagement window is **4.34 mm to 6.35 mm**. An ordinary 2 × 12 2.54 mm header with
a ~6.0 mm post qualifies. **Extra-long-pin headers (8.13 mm / .320 in posts) must
NOT be used** — they exceed the window. Reference accessory mate:
**`TSW-112-07-L-D`** (5.84 mm post), or a `-RA` right-angle variant for a coplanar
accessory. That one sentence is what preserves the entire reason for choosing
2.54 mm in the first place.

### Enclosure keying and load path locked (D-097)

The connector carries **no integrated key** — the BCS polarized-position option
exists but consumes a contact, which D-081 forbids. So: the socket face is recessed
**≥ 1.5 mm** behind the right wall and the recess walls form the shroud; an
**asymmetric rib/step on the upper edge only** blocks upside-down insertion (the
two mating rows are just 2.54 mm apart, so the key must be unambiguous rather than
a chamfer); the recess is **closed at both ends** with ≤ 0.3 mm clearance so a
one-column offset is mechanically impossible; a moulded **shelf and backing rib
capture the connector body**; and the accessory shell bottoms on an **enclosure
boss** so the insertion force is never carried by the 24 solder joints.

Insertion force is **≈ 33 N average** (24 × 1.39 N) with **withdrawal ≈ 20 N
average** — better than the ≈ 48 N maximum of the rejected part. These are Samtec
*averages*; Samtec's own note explains the peak occurs during the contact-spreading
stage and exceeds the average, so the load path is sized with that acknowledged
rather than assumed away.

### Z-stack rechecked, and it improves

| layer | Harwin (rejected) | **Samtec BCS** |
|---|---|---|
| Connector body above PCB | 8.10 mm | **5.33 mm** |
| **Column total of the 23.0 mm external budget** | **22.30 mm** | **19.53 mm** |
| **Spare** | **0.70 mm** | **3.47 mm** |

**The connector region is no longer the sole governing column** — it is now level
with the control region's 19.5 mm. **3.47 mm is real, usable clearance**, which is
the standard the ruling demanded. The 5.33 mm figure is read from the Samtec series
print and cross-checked three ways (the `-S-HE` view differs by exactly one 2.54 mm
row pitch; the vertical `-D-TE` body width is .20 in; the vertical insulation height
of 7.37 mm matches). It must still be confirmed against the individual 3D model at
FBV2-P1 — **M-09, downgraded to LOW**, and the conclusion survives even a 2.8 mm
error.

### Electrical allocation unchanged

The BCS has the same 2 × 12 topology with the mating rows stacked vertically, so
**D-082 and D-084 transfer unchanged.** Power and ground remain distributed across
columns 2, 5, 8 and 11; every power contact is still vertically GND-paired; all
3.3 V is in row A and all 5 V in row B; both native pins still flank the GND at
pin 9; the detect strap is still one 0 Ω link between pins 21 and 23. **The entire
mis-insertion argument carries over intact.**

### The three opportunity rulings

**O-1 APPROVED** (D-094). The two TPS22950C `FLT` outputs are open-drain and are
**wire-OR'd into `ACC_POWER_FAULT_N`** — one 100 kΩ pull-up, one PCAL9535A input at
`U3` P15. **`U3` P16 becomes `RESERVED_SPARE` with no function assigned**, brought
out to a test pad with a 100 kΩ pull-up so it reads a defined level and can be
pressed into service by a wire and a firmware change rather than a respin. Rev 1
now retains an expander resource for recovery. Rail attribution is by **controlled
isolation** (MX-5a): disable one rail and observe whether the fault clears. **B-37
is half closed** — `U2` still has zero spare.

**O-2 APPROVED** (D-095). **External I²C address `0x50` is reserved** for an
optional AQROOT accessory-identification EEPROM — **protocol reservation only, no
main-board hardware, and no accessory is required to carry one.** It joins the
reserved table with 0x38, 0x68, 0x36, 0x20 and 0x21. One thing flagged rather than
locked (**P-19**): the 24Cxx family spans **0x50–0x57**, so an AQROOT ID EEPROM
must strap A0–A2 = 0, and 0x51–0x57 remain unreserved.

**O-3 REJECTED** (D-095). The accessory TPS61023 5 V rail is **not** connected to
the NFC fallback — no DNP link, no shared node beyond `SYS`. Sharing the TPS61023
*device family* is the extent of the BOM consolidation, exactly as D-056 intended.

### Accessory limits, and the rule most likely to be misread

**`ACC_3V3_SW` = 400 mA total. `ACC_5V_SW` = 300 mA total** for the first five
boards (D-098). Later targets of 600–800 mA and 500 mA require measured bring-up
and a CTO ruling; the hardware change is one 0603 resistor per rail.

> **The duplicate contacts SHARE the rail limit. They do not double it.**
> `ACC_5V` pin 10 + pin 22 = **300 mA combined, not 300 mA each.** There is one load
> switch and one current limit per rail; the second contact halves contact
> resistance and eases routing, and adds no current budget. This must appear in
> accessory documentation in these words.

### Two new opportunities, flagged not locked

**N-1** — publish an accessory reference design: the 2 × 12 footprint, the
4.34–6.35 mm post-length rule, the detect-strap pattern, the shared-rail current
rule and a board-outline template that fits the recess. High value,
documentation-only, zero main-board cost — but it is a deliverable this task was
not authorized to create. **N-2** — accessory retention: withdrawal force is only
≈ 20 N average with no latch, so an enclosure friction detent or a captive fastener
is worth considering; it is a mechanical and ergonomic trade-off for enclosure CAD.

Full analysis:
[`audits/2026-08-23-community-connector-correction.md`](audits/2026-08-23-community-connector-correction.md).

---

## 2026-08-23 — Community expansion port and accessory power LOCKED (FBV2-COMM-001)

Documentation only. No design file touched. `hardware/beta-v2/` was not created.
**This was the last architecture closeout before schematic implementation.**

**COMMUNITY PORT LOCK = PASS. P-02, P-15, P-16 and B-08 all CLOSED.** No
architecture item now gates any schematic sheet.

### The 20-pin community port architecture is superseded

**D-059 and D-062 no longer describe this product** and nothing downstream may
cite them. The principles that survive are carried forward explicitly rather than
inherited: no duplicate GPIO (D-042), native and XGPIO documented distinctly
(D-045), no permanent raw `+3V3` (D-057), TPS22950C (D-058), native pair GPIO38 +
GPIO47 (D-063).

**New port: 2 rows × 12, 24 ACTIVE contacts, FEMALE on the device, male on the
accessory** (D-081). **10 XGPIO + 2 native + 2 I²C + 1 WAKE/ATTN + 2 switched
3.3 V + 2 switched 5 V + 4 GND + 1 `ACC_DETECT_N`** (D-082). Only the rails and
ground are duplicated, each a single net; **no GPIO is duplicated**. XGPIO falls
from 11 to 10, and **that one surrendered pin is exactly what pays for the fifth
accessory-control expander pin** — the arithmetic is tight to the pin.

### ~~Connector: Harwin `M20-7881242`~~ — **CORRECTED 2026-08-23, see FBV2-COMM-002**

> **This selection was WRONG and is superseded.** `M20-7881242` is obsolete and
> `harwin.com` returns HTTP 404 for it. The MPN had been configured from the
> catalogue ordering scheme rather than taken from a live listing — which the same
> entry's own limitations section had flagged. **The connector is now Samtec
> `BCS-112-S-D-HE`.** The reasoning below about *why keying must come from the
> enclosure at 2.54 mm* remains correct and still applies.

2.54 mm, 2×12, **female horizontal (right-angle) PC-tail socket**, through-hole
with two-point solder fixing, gold+tin. **3 A per contact, 300 mating cycles,
30 mΩ, 800 V AC proof, −40…+105 °C, UL94V-0.** Body ≈ 30.68 × 7.87 × 8.10 mm.
Mates with **any standard 2×12 0.64 mm square-post male header** (D-083).

A finding worth stating plainly: **at 2.54 mm there is effectively no mainstream
board-mount FEMALE connector with an integrated shroud and key.** The ubiquitous
shrouded, polarized 2.54 mm part is the *male* IDC box header, which is the wrong
gender. Samtec's Mini Mate `IPL1` is properly keyed, shrouded and latching — and
is a male box header whose mate is a Samtec part, so makers could not build
accessories from commodity components. 2.00 mm systems (Hirose DF11, Molex
Milli-Grid) do give a connector-side key and are ~20 % shorter, but they abandon
standard 2.54 mm male pins, which is the entire reason the pitch was chosen.

**So the key and the shroud come from the enclosure** — an asymmetric recess with
an off-centre lead-in rib, closed at both ends. That is explicitly permitted by
the ruling, it costs nothing in BOM, and it preserves the US$0.10 pin header as
the accessory interface.

### Pin ordering, and the mis-insertion proof

`1 XGPIO0 · 2 EXT_SCL · 3 ACC_3V3_SW · 4 GND · 5 XGPIO1 · 6 EXT_SDA ·
7 NATIVE_A · 8 XGPIO2 · 9 GND · 10 ACC_5V_SW · 11 NATIVE_B · 12 XGPIO3 ·
13 XGPIO4 · 14 WAKE_ATTN_N · 15 ACC_3V3_SW · 16 GND · 17 XGPIO5 · 18 XGPIO6 ·
19 XGPIO7 · 20 XGPIO8 · 21 GND · 22 ACC_5V_SW · 23 ACC_DETECT_N · 24 XGPIO9`
(D-084).

The ordering is not cosmetic. **Every power contact is vertically paired with
GND**, which is the constraint that forced power into columns 2, 5, 8 and 11 — so
**a row-swapped accessory can only ever produce a current-limited rail-to-ground
short, never 5 V on a logic pin.** All 3.3 V lives in row A and all 5 V in row B,
so a row-to-row bridge inside an accessory can short a rail to ground but never
5 V to 3.3 V. Both native fast pins flank the single GND at pin 9, which serves as
their return reference and separates them from each other. The I²C pair flanks the
GND at pin 4 for the same reason.

**The detect strap is one 0 Ω link between pins 21 and 23**, at the very end of the
row — the simplest accessory implementation possible. And because a flipped
accessory's strap lands in the other row, **a flipped accessory cannot assert
`ACC_DETECT_N`, so neither rail is ever enabled.** The mis-insertion case is
passively safe and self-announcing: the accessory simply does not come up.

A one-column lateral shift cannot be prevented electrically and is prevented
mechanically — the recess must be closed at both ends.

### Accessory detect

`ACC_DETECT_N` is pulled up to `+3V3` by AQROOT and grounded by the accessory
(D-085). Because the pull-up and the expander both run from `+3V3`, **detection
works with both accessory rails off**, which is the ordering the ruling demanded
and is what makes the flipped-accessory argument hold. **Neither rail may be
enabled unless detect is asserted.** As a free by-product, `U3`'s `/INT` is
wired-OR onto `WAKE_INT_N` → GPIO21, so **plugging or unplugging an accessory
raises an interrupt and can wake the device** at zero hardware cost.

### 3.3 V rail: TPS22950C confirmed line by line

`+3V3 → TPS22950C → ACC_3V3_SW` (D-086). Verified against SLVSFJ2B: `VIN`
1.8–5.5 V (so the same part works at 5 V too), **RCB = Yes** for the C variant,
`ILIM` **0.5–3.5 A** adjustable, auto-retry, TSD 170 °C, open-drain `FLT`, DDC
SOT-23-thin, 41 mΩ at 3.3 V, 550 µs slow turn-on so enabling the rail cannot step
`+3V3`. Default OFF with a **mandatory external 100 kΩ pull-down** — the internal
500 kΩ smart pull-down exists but the datasheet still says *"do not leave
floating"*.

### 5 V rail: a second TPS61023 and a second TPS22950C

`BQ25185_SYS → TPS61023 @ 5.0 V → TPS22950C → ACC_5V_SW` (D-087). **Not USB VBUS,
not the NFC fallback rail, tied to neither**; the only shared node is `SYS` on the
input side.

**Yes, reuse the TPS61023 — it is the right part, not merely the convenient one.**
0.5–5.5 V in, 2.2–5.5 V out, **3.7 A valley switch limit**, 94 % at 3.6 V → 5 V,
**true input-to-output disconnection in shutdown** at 0.1 µA, OVP, short-circuit
and thermal protection, SOT-563. Computed capability at 5 V is **≈ 2.3 A from a
3.0 V battery and ≈ 2.8 A from 3.6 V** — six to ten times what is being asked of
it. The limiter is the inductor, not the IC, so **1 µH with `I_sat` ≥ 3 A** is
specified (B-38). It shares its inductor, feedback divider and capacitors with the
DNP NFC fallback boost, so both circuits are one BOM line.

**Yes, use TPS22950C on both rails** (D-088). Same MPN, same footprint, same
safe-state pull-down, same `FLT` handling — **only `R_ILIM` differs**.

**Every back-feed path is closed**: accessory → boost (RCB, and constant reverse
blocking whenever `ON` is low, which is the default); `ACC_5V` → USB `VBUS`
(three series barriers — the switch's RCB, the boost's true disconnection, and the
BQ25185 power path); `ACC_5V` → `NFC_SUPPLY` (physically separate boost, separate
net, NFC on `+3V3` with its boost DNP on build 1).

### Why the published limits are below the CTO's targets on build 1

Recommended, **not fabrication-locked**: `R_ILIM` = **1.5 kΩ** on 3.3 V (≈ 0.76 A
typ) with a **published 400 mA continuous**, and **1.65 kΩ** on 5 V (≈ 0.69 A typ)
with a **published 300 mA continuous**.

Nothing about the switch or the connector prevents 800 mA — the TPS22950C is a
3.2 A part and the contacts are rated 3 A each. **The TPS63020 does.** The
TPS22950C is a *constant-current* limiter, so a shorted accessory holds `ILIM`
until thermal shutdown. Stacked on the internal worst case, `R_ILIM` = 1.15 kΩ
(600 mA published) drives `+3V3` to **101 % of the regulator's 2 A rating** —
foldback, brownout, SD corruption. At 1.5 kΩ the same fault reaches **86 %**. The
CTO's 600–800 mA target is met by changing one 0603 resistor once the internal
worst case is measured on real boards. That is D-049 applied exactly as intended.

**A structural advantage worth recording:** because the 5 V rail is boosted from
`SYS` rather than derived from `+3V3`, it consumes **none** of the TPS63020's 2 A
budget. Deriving it from `+3V3` would have cost roughly 500 mA of that budget.

### One honest caveat on fault visibility

SLVSFJ2B Table 9-1 is explicit: **`FLT` asserts on thermal shutdown and reverse
current only.** An output short leaves `FLT` **Hi-Z** while the device
current-limits. In practice a hard short dissipates 2.5–3.5 W in a SOT-23-thin
package and reaches the 170 °C TSD within tens of milliseconds, at which point
`FLT` does assert — but a **partial** overload that stays inside the thermal
envelope is invisible to the host. Firmware must not treat `FLT` as a complete
overcurrent indication (B-35). This is recorded because the ruling asked for
exactly this honesty rather than an invented fault output.

### Expander verdict: all five fit — exactly, with nothing left over

`U3` = **16/16**: `XGPIO0-9`, `ACC_3V3_EN`, `ACC_5V_EN`, `ACC_DETECT_N`,
`ACC_3V3_FAULT`, `ACC_5V_FAULT`, `SX1262_RXEN`. `U2` = **16/16**: the five pins
freed by removing HOME, the RGB LED and the RootProbe IRQ are exactly consumed by
`BQ25185_STAT1/2`, `MAX17048_ALRT_N`, `VBUS_PRESENT` and `SX1262_DIO1` (D-089).
Nothing was stolen — GPIO38 and GPIO47 remain the published natives, and SPI, I²S
and every internal MCU signal are untouched. One expander pin drives both the 5 V
boost `EN` and the 5 V switch `ON`.

**The design now has zero spare expander capacity anywhere (B-37).** That is the
price of fitting five accessory signals, and it is recorded as a standing
constraint rather than buried.

### Logic safety

**Every signal contact is 3.3 V CMOS. The 5 V power contact does not make any
signal 5 V-tolerant** (D-090). 100 Ω series on every XGPIO and both natives, 22 Ω
on the buffered I²C pair, 330 Ω on WAKE, plus a low-capacitance TVS array on the
two natives and the I²C pair — **the natives are the only contacts with a direct
path to the MCU**, and 5 V through 100 Ω is ≈ 11 mA into the clamp, inside
tolerance but with no sacrificial part in between. **Bidirectional level
translators are rejected**: they do not protect the A-side, they add direction
ambiguity on genuinely bidirectional GPIO, and they would imply 5 V logic is
supported, which it is not.

### B-08 closed with one MOSFET

A single N-channel pass gate between `WAKE_ATTN_N_HDR` and `WAKE_INT_N`, **gate
driven by `ACC_3V3_SW`** (D-091). The signal is only ever pulled low, so an N-FET
pass gate is sufficient. With accessory power off — the default — **a shorted
accessory pin can no longer hold `WAKE_INT_N` low, so internal button wake can
never be blocked.** Consequence, stated rather than hidden: accessory-initiated
wake now requires the rail to stay enabled during sleep (B-36).

### Power budget and the binding firmware contract

Naive simultaneity reaches **1 698 mA at `+3V3` = 85 % of the TPS63020's 2 A**
before transients — the P-15 concern, now quantified. With mutual exclusion
enforced the design case is **1 169 mA (58 %)**, or 1 314 mA (66 %) at the Wi-Fi
peak, and **1.65 A at the pack** (≈ 0.60 C on the 2 750 mAh class cell).

**MX-1…MX-9 are binding** (D-092): one high-power radio at a time; audio capped
during any transmit; rails detect-gated; 3.3 V enabled before 5 V by ≥ 5 ms; `FLT`
handled within 100 ms with a user action required rather than an endless
auto-retry into a short; both rails dropped on detect loss; 5 V disabled below
`V_BAT` 3.4 V and 3.3 V below 3.2 V; SPI-A arbitration; `U3` XGPIO interrupts
masked by default.

**A new thermal finding:** at 1.75 A the BQ25185 BATFET (115 mΩ) plus the
reverse-protection path costs **≈ 0.70 W and ≈ 0.40 V** inside a sealed
enclosure (B-34). BQ25185 supports 3.125 A discharge so the current is in spec,
but the loss and the `SYS` droop near a flat battery are real and are a further
argument for conservative first-build accessory limits.

### Mechanical: the connector region is now the governing Z column

2.0 shell + **8.10 connector** + 1.6 PCB + 8.0 battery + 0.6 + 2.0 shell =
**22.30 mm of the 23.0 mm external budget — 0.70 mm spare** (M-09). That displaces
the control region's 19.5 mm. Relief exists: the battery is 60 mm wide in a 75 mm
cavity, so the outer ~5 mm of each PCB edge has nothing behind it. The 8.10 mm
figure is read from the series catalogue and **must be re-confirmed against the
individual part drawing at FBV2-P1**. Insertion force reaches **48 N** (24 × 2.0 N
max) and must be carried by an enclosure boss, not by the PCB joints (M-10).

### Three opportunities flagged, deliberately not locked

**O-1** wire-OR the two `FLT` lines to recover one expander pin — slack versus
per-rail diagnostics, in a design that now has zero spare anywhere. **O-2** reserve
an I²C address for an accessory-ID EEPROM — zero hardware cost, but a
product/protocol decision that interacts with P-18. **O-3** a DNP 0 Ω link letting
the accessory boost also serve the NFC 5 V fallback — saves a part, but couples
NFC PA current to the accessory load, which is exactly what D-056 avoided. All
three need a CTO ruling.

Full analysis:
[`audits/2026-08-23-community-expansion-closeout.md`](audits/2026-08-23-community-expansion-closeout.md).

---

## 2026-08-23 — Display, connector and backlight LOCKED (FBV2-DISP-002)

Documentation only. No design file touched. `hardware/beta-v2/` was not created.

**FBV2-DISP-LOCK = PASS. M-06 CLOSED. M-07 CLOSED.** Sheet
`03_spi_a_display_sd` is unblocked, which removes the last gate on FBV2-S1.

**Display LOCKED: EastRising `ER-TFT035IPS-6` + `ER-TPC035-6`** (D-074) — 3.5″
IPS 320×480, **ILI9488** COG, **FocalTech FT6236** capacitive touch at **I²C
0x38**, assembled outline **56.54 × 84.96 × 3.95 ± 0.25 mm**, active
48.96 × 73.44 mm, 300 cd/m², 500:1, 80/80/80/80.

**FPC LOCKED (D-075): one 50-pin tail, 0.50 mm pitch, BOTTOM CONTACT,
0.30 ± 0.03 mm thick, 25.5 ± 0.15 mm wide, 30 ± 0.5 mm free length.** Display
*and* touch leave on that single tail — touch on pins 44–47. All three of the
parameters D-049 forbids guessing are printed in the vendor's own datasheet
(Rev 2.0, 18-Aug-2025). No second connector, no soldered flying lead.

**`J1` LOCKED: Hirose `FH69-50S-0.5SH`** (D-076). The compatibility argument is
the point: it is made from **both manufacturers' drawings**, not from a matching
pin count. The display tail is 0.30 ± 0.03 mm and the connector requires
0.30 ± 0.05 mm; the tail is bottom-contact and **FH69 accepts top *and* bottom
contacts** on a 2-point design. **The classic dead-first-article failure — an FPC
facing the wrong way — cannot occur with this pair.** Digi-Key: Active, 1,907 in
stock, US$2.16 @ 1, MOQ 1.

**`J1` is laid out on the FH12-horizontal / FH52E standard land pattern, not on
FH69's dedicated pattern** (D-077). Hirose states FH69 fits that pattern, and
doing so makes **`FH52E-50S-0.5SH` (LCSC `C7465440`, JLCPCB-orderable)** a genuine
drop-in second source with no board change. That is D-049 applied to a connector.

**D-073 is resolved, and the answer is that the connector was never the problem.**
As a by-product, `ER-TFT035-6` with CTP measures **56.54 × 84.96 mm** — the same
figures to 0.01 mm as Chenghao's `CH350HV40A-CT`, with the same active area and
the same 6-LED parallel backlight. The two are, to a high confidence, the same
glass from the same upstream supplier, and Chenghao's *"pin pitch 0.3 ~ 0.4 mm"*
is very likely a datasheet defect conflating tail thickness (0.3 mm) and conductor
width (0.35 mm) with pitch. **That is an inference, not a proof**, and Chenghao
stays rejected — a supplier that cannot state its own pitch cannot be designed
against. What it does retire is the fear that the *family* uses a sub-0.5 mm
pitch. It does not.

**ST7796S is formally rejected on availability, not on merit** (D-078). Eleven
suppliers were surveyed — Newhaven, Riverdi, EastRising, Winstar, Raystar, Focus
LCDs, DisplayModule, VIEWE, Chenghao and the hobby vendors. **No ST7796S / ST7796U
3.5″ 320×480 IPS module with a capacitive touch panel, a named touch controller
and a complete public FPC specification exists from a production supplier.**
ST7796S appears only on hobby breakouts (excluded by the brief), on touch-less
LCMs, or with ambiguous FPC data. Every candidate that meets the full requirement
set carries ILI9488. The cost is quantified: **+50 % SPI-A traffic; 46 ms
(21.7 fps) for a full 320×480 frame at 80 MHz FSPI IO_MUX against 31 ms for
ST7796S.** Accepted for menus, graphs, logs and status screens.

**Rejections, each on a recorded ground:** Riverdi `RVT35HITNWC00-B` — 59.56 ×
**93.34 × 5.66 mm** and a **10-LED, 14–16 V, 100 mA** backlight (~1.5 W). Focus
LCDs' IPS parts — **End of Life / NRND**, US$109 for 8 pcs. Focus `E35RG73248…-C`
— 61.90 × 91.04 mm and **two** connectors. Winstar `WF35UTYAIDNN0` and Raystar
`RFI350U-AYW-DNN` — excellent LCMs, **no touch variant**. Newhaven — current 3.5″
IPS is **640×480 MIPI DSI**, which the ESP32-S3 cannot drive. DisplayModule
`DM-TFT35-431` — ST7796S but **no documented touch controller**.

**Backlight closed (D-079). The TPS61169 stays, and for a structural reason:**
`U17` boosts from **`+3V3`**, not from the battery. A 6-LED *parallel* array sits
at only ~3.0–3.2 V, and a boost cannot regulate below its own input — had the
driver been fed from `VSYS` (3.0–4.35 V) this panel would have forced a buck-boost
or a linear sink. From a fixed 3.3 V, a modest ballast lifts the output to
~4.15 V and the converter stays firmly in boost at every corner.

New values: **`R69` (RSET) 2.55 R → 1.87 R ±1 %** → 109 mA typ, 100.5–117.6 mA
over the VREF band, always under the panel's 120 mA maximum. **`R70`–`R73`
4 × 39 R → 4 × 33 R, all in parallel on the single `LED_A` net** = 8.25 R, which
reuses the existing footprint group, quarters per-part dissipation to 24.6 mW and
leaves three DNP-able trim steps. Margins: **switch peak 263 mA against a 1.2 A
limit (4.6×)**; `L3` 12.5×; `D8` 2.1×; `C44` unchanged at 1.28× against the 39 V
OVP worst case. `L3`, `D8` and `C44` are all retained.

**The backlight is cheaper than FBV2-DISP-001 feared.** That audit assumed
6 × 20 mA and predicted roughly +50 %. The real panel is specified at **120 mA
maximum / 90 mA life point across six chips**, so per-LED current *falls* from
20 mA to 15 mA. At default brightness the pack sees **129 mA against Beta-DM's
118 mA — about +9 %** for 1.56× the screen area and 2× the pixels, and LED life
improves rather than degrades.

**Electrically the migration is free** (D-080). 4-wire SPI is selected by hard-tying
IM2/IM1/IM0 = 1/1/1 to VDDI, and the panel's SCK/MOSI/MISO/CS/DC/RESET land on the
existing GPIO12/11/13/10/14 and `U60 P04`; touch lands on the existing I²C bus with
the **same FT6236 at the same 0x38**, `TOUCH_RST_N` still on `U60 P00`. **Zero new
native GPIO. No new rail. No level shifting. No SPI bus merge.** B-10 is unaffected.

**One caution, mitigated by design:** the ILI9488's `SDO` behaviour on a bus shared
with microSD is not stated in the datasheet, and ILI9488 modules have a field
reputation for holding SDO driven. A **0 R `R_SDO` series link plus a test point**
lets the display be made write-only at bring-up without a respin, a trace cut or a
bodge (B-28).

**Mechanical PASS with margin.** 56.54 × 84.96 × **4.20 mm max** inside the
60 × 90 × 4.5 envelope; 9.23 mm of cavity each side; **70.04 mm** of the 155 mm
cavity height left for the D-pad, A/B and the mic aperture; front stack 7.30 mm
plus the 8.0 mm battery = 15.30 mm of the 18.5 mm cavity, **3.20 mm spare**. The
6 mm FPC bend corridor is retained and is generous against the ≥3 mm a 0.30 mm
tail needs. **One new placement coupling:** at 2.3 mm the connector cannot sit in
the display shadow (0.8 mm limit), so it competes for the space below the panel
(B-33 / M-08).

**Procurement risk LOW**, with two MEDIUM items that are closed on the purchase
order rather than in the design: the vendor also sells a **CST340** touch panel
for this size, so the PO must name `ER-TPC035-6`; and the datasheet carries a
**"Backlight Update" revision**, so Rev 2.0 must be archived in-repo and cited by
revision in the MPN ledger. Against that, EastRising publishes a written
**≥10-year continuity-supply commitment** — the only candidate in the survey that
does — at **MOQ 1**, in stock, **US$15.57 per display in prototype quantity**.

Full analysis:
[`audits/2026-08-23-display-procurement-lock.md`](audits/2026-08-23-display-procurement-lock.md).

---

## 2026-08-22 — Display size ruled 3.5″; MPN deliberately not locked (FBV2-DISP-001)

Documentation only. No design file touched.

**Battery envelope LOCKED** at 60 × 75 × 8.0 mm, ~2500–3000 mAh (D-071).
**Display size LOCKED at 3.5 inch** (D-072). **Display MPN and J1 are deliberately
NOT locked** (D-073), and the reasoning matters more than the conclusion.

**Was the old J1 ever compatible? UNPROVEN — not YES, not NO.** No source
obtainable to this audit states the CH280QV10-CT's FPC pitch, and the Phase-1
mechanical audit independently recorded the same gap. **J1 was selected without a
display FPC drawing on file and has never been proven to mate.** Its footprint is
verified against the *Hirose* drawing, which proves the connector footprint is
right and proves nothing about the display. The CTO's suspicion is strengthened by
the successor part in the same family quoting **0.3–0.4 mm**, not 0.5 mm — if that
is the family convention, the 2.8″ part may never have mated either.

**The 3.5″ candidate CH350HV40A-CT was verified and it fits** — 320×480 IPS,
ILI9488, 56.54 × 84.96 × 3.97 mm, active 48.96 × 73.44 mm, 50-pin, 6-LED parallel
backlight. It clears the ≤60 × 90 × 4.5 mm envelope and leaves 70 mm of the
155 mm cavity height for the controls. **Four defects stop it being locked:**
ILI9488 **cannot send RGB565 over SPI** and takes 3 bytes/pixel, a 1.5× bandwidth
penalty an ST7796S-class part simply does not have; the vendor states **"pin pitch
0.3 ~ 0.4 mm"**, a *range*, which directly violates D-049's *"no dependence on
undocumented pin pitch"*; module thickness is quoted as both 3.97 and 2.4 mm in the
same document; and the touch controller is never named.

**What is locked instead is the interface requirement** — 3.5″ IPS 320×480,
ST7796S/ST7796U preferred, I²C CTP of the FT6336U class, single documented FPC
pitch with 0.5 mm strongly preferred. **The mating connector cannot be chosen
until the panel's pitch, pin count and contact side are confirmed**; choosing one
now would repeat the exact mistake this audit found.

**ESP32-S3 SPI verdict: PASS, with no bus merge and no radio change.** The panel
touches only SPI-A; SPI-B keeps the radios and NFC. Usefully, `SPI_A_MOSI`/`SCK`/
`MISO` sit on GPIO11/12/13 and `DISP_CS` on GPIO10 — exactly the ESP32-S3 **FSPI
IO_MUX** pins, so the display bus already has the 80 MHz fast path rather than the
40 MHz matrix route. At 80 MHz an ST7796S-class controller writes a full 320×480
RGB565 frame in ~31 ms, the same as today's 2.8″ panel at 40 MHz — **the user
experience does not regress.** With ILI9488 it is ~46 ms instead.

**Backlight rises from 4 LEDs to 6 (+50 %)**, taking browsing draw from ~100 mA to
~130 mA — but D-071's larger pack takes capacity from 2000 mAh to ~2750 mAh, so
**runtime is flat to slightly better.** Neither ruling alone would have achieved
that. The TPS61169 `RSET` (2.55R) and its current capability must be re-derived for
six LEDs (M-07).

M-01 and M-02 closed. **M-06** (display MPN / FPC) and **M-07** opened. FBV2-A2
stays PASS. **No gate passed, so the percentage holds at 25 %.**

---

## 2026-08-22 — Mechanical interfaces frozen; **FBV2-A2 PASSED** (FBV2-MECH-001)

Documentation only. No design file touched. `hardware/beta/mechanical/` was read
only and is unmodified.

**FBV2-A2 = PASS.** Three of twelve gates now pass. New authoritative pre-CAD
source: `mechanical/MECHANICAL_INTERFACE_SPEC.md`, with every row marked LOCKED,
TARGET or TBD — and **nothing marked LOCKED on the strength of derivation alone.**

**Device orientation was resolved, not assumed.** The Beta-DM board is 74 × 155
(portrait) and the external target is 80 × 160; the axes map one to one. The
device is portrait, so the front is display-above-controls.

**23 mm passes with 3.5 mm spare**, and the interesting question was what to do
with the margin. The governing column is the control region with the battery
behind it: 19.5 mm of 23.0 mm. Left as air the margin is wasted; allocated to the
battery it raises the pack from the 5–6 mm a 2000 mAh cell needs to **8.0 mm**,
i.e. the **2500–3000 mAh class** — a 25–50% runtime gain for zero external size
change.

**The Beta-DM outline cannot be reused, and the reason is stark.** Against the
derived 75 × 155 mm cavity, the 74 × 155 mm board leaves 1.0 mm of clearance in X
and **zero in Y**. There is no room for the shell lip, six bosses, ribs or
assembly access. Combined with the v2 content changes — 20-pin connector, P2
four-FET stage, dead-cell recovery branch, NFC crystal and matching, restored IR,
new expanders — the verdict is **re-floorplan with a different outline**, targeting
**70 × 148 mm**. This is the PCB revision Field Slate v3 required in July and never
received.

**NFC and battery are separated in plan rather than stacked.** Because the display
occupies the front upper third, the rear upper third is free — NFC loop there
(45 × 45 mm), battery in the rear lower two-thirds. **Zero overlap is the policy,
not a mitigation.** Ferrite is still specified, because once the battery moves away
the PCB ground pour becomes the dominant near-field threat. The loop grows from
Beta-DM's measured 26 × 20 mm to 45 × 45 mm — a **3.9× area increase**, which is
where the range lost to 3.3 V NFC operation (D-055) is won back. Two constraints
fall out: the mid-span bosses and the left-side antenna storage channel must both
stay below Y = 100 mm.

**Acoustics and IR specified to interface level.** The ICS-43434 is bottom-port, so
the mic path is PCB hole → gasket → shell aperture with the tunnel ≤2.5 mm; longer
tunnels roll off exactly the frequencies that carry speech. Speaker rear-firing,
Ø20 × 4 mm, with a 1.5–2.0 cm³ **sealed** rear cavity, ≥60 mm from the mic and on
the opposite face. IR emitter and receiver ≥15 mm apart on the top edge with a
**mandatory opaque barrier** — separation alone does not fix self-blinding,
because the internal reflection path is the one that actually causes it.

**Honest limits recorded rather than glossed:** nothing is CAD-verified, several
component figures are class-typical, and the display is the weakest input — its
50 × 69 mm figure is a measured *keepout*, not a vendor outline, and the FPC bend
stack is unknown. That is why display size is raised as an open item.

Two CTO decisions opened: **M-01 display size** (the cavity comfortably accepts
3.2″ or 3.5″; blocks PCB floorplanning but not schematic migration) and **M-02
battery capacity target**. **P-07 closed.**

Progress 20% → 25%. Next gate: **FBV2-S1, schematic migration.**

---

## 2026-08-22 — Battery safety architecture finalised; **FBV2-A1 PASSED** (FBV2-PWR-002)

Documentation only. No design file touched.

**FBV2-A1 = PASS** — the first gate to pass since FBV2-A0, and the largest
remaining architecture unknown. All six criteria closed, all 13 power/fault cases
defined, no power-tree branch TBD. Next gate: **FBV2-A2, mechanical interface
freeze.**

**Candidate B selected and specified to component level** (D-065). The design
turns on one structural fact: **no passive switch can distinguish a 0 V cell from
a reversed one** — an N-FET referenced to a positive rail sees V_GS ≈ +3 V at 0 V
and ≈ +6.7 V at −3.7 V, so a reversed cell turns it *harder on*; the P-FET
arrangement fails the same way. An active, GND-referenced comparison is therefore
mandatory. The chosen sensing network is a **matched ratiometric bridge** whose
trip condition reduces to **V_BAT = 0 independent of VBUS** — supply-independence
by construction rather than by trimming. Handoff is taken from the **LTC4368
`FAULT` pin**, which is asserted precisely while VIN is below UVLO, so the
protection controller itself decides when it has taken over — no extra threshold,
no possibility of both paths being active. Recovery current **5–10 mA** (~0.004 C),
supplied from **VBUS rather than SYS** so the branch is dead by construction
without USB and costs **zero battery-side standby**.

**The pass path changes to P2** — two back-to-back stages in **two separate
packages**. A precise finding corrected the earlier account: **P1 fails one of the
two single-FET-short cases, not both.** A short on the `BAT_RAW`-side FET is
already blocked by its partner; it is specifically the **`BAT_PROT`-side** FET
whose short lets a reversed cell through. P2 leaves one complete back-to-back pair
intact under any single short, and additionally keeps the LTC4368's electronic
breaker functional with a FET shorted. Two die sharing one leadframe cannot be
called independent, so the two stages must not share a package.

**The previous fuse-and-clamp compliance argument is withdrawn as invalid.** A
Schottky sitting at ≈0.8–1.0 V does not protect a −0.3 V absolute maximum, and
ruling D was right to refuse it. With isolation doing the work, the **clamp is
demoted to secondary** duty (ESD, transient, double-fault) and the **fuse is
resized 3 A → ≈5 A**, because it is now a backstop that must not pre-empt the
3.33 A electronic breaker. Its one genuinely irreplaceable role is a harness short
between `BAT_RAW` and GND *upstream* of the FETs, where the breaker cannot act.
**PTC remains rejected.**

**Honest residual, recorded rather than smoothed over:** Candidate B is *not*
tolerant to every single failure — four failures each individually enable current
into a reversed cell. It meets the requirement as written because `R_LIM` bounds
every one to **≈13 mA (~0.007 C)**, `D_REC` keeps the branch unidirectional under
all faults, and the condition is self-annunciating. A fully redundant variation is
documented and **not** recommended: it would trade that bounded residual for a
permanent oscillation in the far more common battery-absent state.

**PCAL9535APW,118 locked for both expanders** (D-066), closing the four facts the
previous audit could not verify. **GPIO38 + GPIO47 remain locked** (D-067).

Progress 15% → 20%, held deliberately low: two of twelve gates, both paper, with
mechanical untouched.

---

## 2026-08-22 — Power architecture closed to a single open decision (FBV2-PWR-001)

Documentation only. No design file touched.

**Expander family locked** (D-061): both `U2` and `U3` become NXP
`PCAL9535APW,118` (LCSC C2669683) — an architecture lock, with the land-pattern
audit still required before fabrication. **Native pair locked** (D-063):
`NATIVE_A` = GPIO38, `NATIVE_B` = GPIO47, with `SX1262_DIO1` moving to the
internal expander and `BUSY` staying native. GPIO43 leaves the public connector.

**The SX1262 lock condition was met from a primary source.** Semtech
`DS.SX1261-2.W.APP` Rev. 1.2 §13.3.4 states verbatim that a DIO mapped to one IRQ
clears when that flag clears, and that with several IRQs mapped *"the DIO remains
set to one until all bits mapped to the DIO in the IRQ register are cleared."*
DIO1 is level-held, so an expander input with no capture register can service it.

**Two prior positions were corrected by the full LTC4368 datasheet.** P-13 is
**closed**: inrush is a designed parameter, `I_INRUSH = (C_OUT/C_GATE) ×
I_GATE(UP)`, giving ≈350 mA against a 3.33 A trip — and RETRY latch-off applies
to *forward* overcurrent only, while reverse faults reconnect automatically once
VOUT falls 100 mV below VIN. The earlier concern rested on an incomplete reading.

**The fuse-and-clamp language correction (D-064) was justified, and the analysis
vindicates it.** At the 20–25 A a 1S pack can deliver, a Schottky clamp sits at
≈0.8–1.0 V — about **3× the BQ25185 `BAT` −0.3 V absolute maximum**. The clamp
improves the excursion roughly fourfold but does **not** bring it inside the
limit. Both elements remain **REQUIRED** — the fuse because without it the clamp
is a permanent short across a Li-ion cell — but the residual is now named (P-12)
rather than assumed away. A **PTC is rejected** for this position: too slow, and
its auto-retry re-applies the fault every cycle.

**Dead-cell recovery is now the only thing blocking FBV2-A1.** The LTC4368 cannot
help here — VIN is the supply pin with a 2.2 V UVLO, and VOUT is a sense input
whose charge-pump role only engages above ~5 V, so system-side power cannot run
the controller. A single MOSFET also cannot distinguish a 0 V cell from a
reversed one: **both turn it more on**, so an explicit GND-referenced sensing
element is mandatory. Four candidates analysed; **Candidate B** — a
hardware-qualified comparator interlock, no firmware dependency, ~0 A into a
reversed cell — is recommended for the product, with service-only accepted as
defensible for the first five boards. **Not approved, so the gate is not passed.**

Progress 13% → 15%. **FBV2-A1 FAIL, 5 of 6 criteria closed.**

---

## 2026-08-22 — Critical architecture reconciled; no-respin policy established (FBV2-ARCH-002)

Documentation only. No design file touched.

**New standing policy: FIRST FIVE FULL BETA PCBAs — NO-RESPIN RECOVERY POLICY
(D-049).** Full Beta v2 Revision 1 must be designed so that reasonable
configuration and performance uncertainty is recoverable through *planned*
component rework — DNP/FIT options, 0 Ω source-selection links, accessible tuning
passives, test points — rather than through a board respin. Safety-critical power
paths are explicitly excluded: no ad-hoc bypasses around battery protection
merely for reworkability.

**An independent second-opinion review was archived verbatim** at
`reviews/2026-08-22-independent-cto-power-nfc-review.md`, marked
**ADVISORY — NOT AUTOMATICALLY AUTHORITATIVE**. It corrected the primary
engineering work on three points, and the corrections were accepted:

- **Discrete back-to-back N-FET reverse protection is withdrawn.** It is not
  under-specified but *unrealisable at 1S* — available V<sub>GS</sub> from any rail
  on this board is 0.3–1.5 V, and the P-channel variant that avoids a charge pump
  turns both FETs hard on into a reversed cell, creating the fault it was added to
  prevent. **LTC4368-1 adopted** (the `-2`'s −3 mV reverse trip would block
  charging outright).
- **"STAT1 only" was wrong, and so was the premise behind it.** BQ25185 SLUSF65A
  §7.3.10 places the STAT2 toggle in the **battery-absent** limit cycle, not in
  charge-complete/sleep — those are one state with both pins HIGH. STAT1 alone
  conveys only fault/no-fault. **Both are exposed**, with the wake-storm solved by
  changing the expander rather than by dropping a signal.
- **TPS22913B/C was the wrong replacement** for TPS22918 — DSBGA 0.9 × 0.9 mm only,
  and no current limit. **TPS22950C** adopted: RCB confirmed for the C variant
  (the L variant has none), leaded SOT-23-thin, adjustable limit, thermal
  shutdown.

**Verified this pass.** The TPS61169 `CTRL` pin has an internal **pull-down**,
which closes the last blocking condition on moving `DISP_BL_CTL` to GPIO46 and
frees GPIO47. **GPIO38 replaces GPIO43** as `NATIVE_A`, removing ROM-UART
push-pull contention from the public connector entirely.

**The mandatory power/fault state table now exists** — eleven cases across USB,
battery, power-switch and accessory states. Cases 1, 2, 5, 6, 8, 9 and 10 are OK
or correctly blocked. **Case 4 (dead cell) and Case 11 (hot insertion) are
UNRESOLVED and block schematic lock**, and Case 7 (shorted pass FET + reversed
cell) is only survivable with a series fuse and a Schottky clamp, which are
therefore required rather than optional.

**NFC ships at 3.3 V with a full no-respin 5 V fallback.** Two mutually exclusive
0 Ω links guarantee the sources can never be shorted. Pre-fit the inductor, the
FB divider and both boost capacitors; keep the TPS61023 and the 5 V link DNP.
Conversion is 3–9 soldering operations with exactly one fine-pitch part — no BGA
or QFN rework, no trace cuts, no bodge wires.

**Volume Up/Down removed from the Full Beta v2 mechanical requirements.**

**FBV2-A1 assessed: CANNOT PASS.** Four of eight criteria are resolved (20-pin
map, default NFC, NFC fallback, accessory power). Four remain — expander family,
native pair, reverse-protection topology completeness, and power-tree stability —
and three of those close with document reads. Progress 10% → 13%.

---

## 2026-08-22 — Architecture direction locked, blockers verified (FBV2-ARCH-001)

Documentation only. No design file touched. Commit `890db0b` pushed to
`origin/master` (`b8b5ebd..890db0b`).

**CTO rulings A–K recorded** as D-018, D-026, D-033…D-041, D-046…D-048. Four
pending decisions closed: P-05 (RGB removed), P-06 (RootProbe IRQ retired),
P-08 (IPEX → pigtail → bulkhead), P-09 (LoRa deep-sleep wake not required).

**Verification against vendor datasheets changed three things.**

- **The NFC supply split cannot be built.** ST25R3916 DS12484 Rev 3 p. 39: *"VDD
  and VDD_TX must be connected to the same power supply"*, with the difference
  capped at ±0.3 V absolute maximum. The requested 3.3 V / 5 V split would apply
  1.7 V across that pair. **The as-built rail assignment is correct**, and the
  pre-design audit's recommendation to change it was wrong and is withdrawn. The
  real residual question — what VDD does while the boost is off — is now P-10,
  with a 3.3 V-only NFC option that would delete eight components.
- **The proposed native-GPIO reclaim would have broken recovery.** Moving
  `NFC_IRQ` to GPIO46 makes ROM download boot conditional on NFC interrupt state,
  because the ST25R3916 IRQ is active-high, latches until read over SPI, and is
  not reset by an ESP32 reset. Substituted: move `DISP_BL_CTL` to GPIO46 and
  expose **GPIO47** as `NATIVE_B`. GPIO47 is strictly better — no power-up glitch,
  20 mA drive, unrestricted priority — and D-041 removed the only reason to want
  GPIO18's RTC capability.
- **`TPS22918` fails the accessory-isolation requirement.** Its integrated body
  diode conducts VOUT→VIN, so a powered accessory can back-power `+3V3`.
  Replacement identified in the TPS22913B/C class.

**Two prior findings were confirmed wrong and are corrected in the record:** the
TCA9517A *does* guarantee high-impedance pins when powered off and 5.5 V
tolerance while unpowered, so it passes; and the TPS61023 *does* provide true
load disconnect plus integrated output OVP.

Reverse-polarity architecture compared across three candidates and **discrete
back-to-back N-FETs recommended** over the LTC4368-1, primarily on quiescent
current (sub-µA vs ~80 µA) — flagged for independent second opinion as
instructed. A reverse-current-blocking load switch was evaluated and
**disqualified for this position**: it would block the charging direction.

Progress raised 8% → 10%. **No gate passed.** FBV2-A1 remains IN PROGRESS with
P-01, P-02, P-04, P-07 and P-10 open. **FBV2-A2 (mechanical interface freeze)
recommended as the next gate** — it is the long pole and nothing blocks it.

---

## 2026-08-22 — Full Beta v2 engineering record established (FBV2-DOC-001)

Documentation infrastructure only. No design file was touched.

- Created `docs/full-beta-v2/` as the authoritative engineering record.
- Established the precedence rule: `CTO_DECISIONS.md` outranks audits, which
  outrank architecture notes, which outrank transcripts.
- Made `transcripts/` append-only.
- Preserved the 2026-08-22 pre-design engineering audit verbatim under
  `audits/`, pinned to repository HEAD `b8b5ebd`.
- Preserved the FBV2-AUDIT-001 CTO prompt and Claude Code response verbatim
  under `transcripts/`.
- Opened the gate table FBV2-A0 through FBV2-B3 and recorded FBV2-A0 as PASS.

---

## 2026-08-22 — Full Beta v2 direction established

- **Beta-DM fabrication paused before payment.** The design-side release stands
  and no money has been committed. Beta-DM is retained as the preserved fallback
  and manufacturing baseline, not cancelled.
- **Full Beta v2 made the primary design.**
- **Decided not to blindly continue frozen Full Beta.** Its freeze recorded 281
  unconnected items and 58 ERC violations; it is a feature reference, not a
  fabrication-ready baseline. Its decisions are re-verified rather than
  inherited.
- **Beta-DM becomes the implementation / manufacturing baseline.** Full Beta v2
  is derived from it — its resolved MPNs, its validated blocks, its routing and
  DFM lessons.
- **Removed HOME from the future product.**
- **Volume Up / Down removed from the enclosure plan.** Audit finding: they
  never existed electrically. `SW2`-`SW8` are UP / DOWN / LEFT / RIGHT / A / B /
  HOME. Volume controls existed only in Field Slate v5 section 5, which must be
  corrected so enclosure CAD is not driven by phantom controls.
- **Physical BOOT retained but hidden/recessed.** It remains the last-resort
  recovery path when flash is blank or hard-bricked.
- **Software recovery required in addition to physical recovery**, with ROM
  download mode and firmware/OTA recovery held explicitly distinct — they fail
  in different situations and must never be conflated in UI copy.
- **Microphone retained** (ICS-43434 I2S MEMS, carried forward unchanged).
- **Speech output retained.** Not downgraded to a buzzer. MAX98357A-style I2S
  Class-D remains the leading architecture; the audit found no materially
  simpler option, because the ESP32-S3 has no DAC.
- **IR retained internally** — not removed, not moved to an accessory.
- **Community expansion target changed from 26 pins to 20 pins**, with a future
  requirement that the connector be keyed, shrouded/polarized and recessed.
- **External I2C retained**, pending validation of its protection, buffering and
  backfeed behaviour before architecture lock.
- **First Full Beta v2 pre-design audit completed** — read-only, pinned to
  repository HEAD `b8b5ebd`, zero repository changes. It established the
  measured GPIO budget (zero free native pins), three candidate 20-pin connector
  architectures, and the blocker set B-01 through B-16 now tracked in
  [PROGRESS.md](PROGRESS.md).
