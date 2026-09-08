# D-664 — THE TAP IS BUILT, AND THE HARNESS THAT WAS SUPPOSED TO POLICE EVERY FRAMEWORK CHANGE HAD NEVER COMPARED ANYTHING

    authority  2900f21a934d9d826644131a90baa36f7dace0db5f50cf2e702e5694f121177f
            -> 2900f21a934d9d826644131a90baa36f7dace0db5f50cf2e702e5694f121177f  (UNCHANGED)
    retained open edges 29 -> 29    open retained nets 16 -> 16
    `hardware/beta-v2` UNTOUCHED.  `hardware/demo/kicad` UNTOUCHED.

**NO COPPER PROMOTED.**  A FRAMEWORK + CHARACTERISATION iteration: one new
router primitive, one new standing contract, one repaired harness, and three
new measurements.  Standing suite **13 contracts, 13/13 RAN, 13/13 PASS**, and
for the first time in this harness's life **13/13 COMPARED and 13/13
IDENTICAL** (`evidence/d664-contract-regression.json`,
`-control.json`).

## 1. THE OMISSION THAT WAS NAMED FOR TWELVE DECISIONS

`maze3d.route_join` closes an island pair PAD TO PAD: `src_pads` and `dst_pads`
are lists of PADS and every escape of every one of them takes part.  That is the
right question for a net with no copper and the WRONG one for a net with
accepted partial copper, and after sixty decisions this board is almost entirely
the second kind.

D-652 measured the gap.  D-655 built `screen_net_tap.py`, which PROVES a
T-junction legal with `maze3d.offcentre_route` and an `anchor=True` end and then
REVERTS it.  There has never been a WRITER, and D-652, D-655, D-661 and D-663
each recorded that as an open next-task — most recently *"THE TAP —
`route_join` may only aim an island at a PAD, and two pockets in this decision
are that omission"*.

## 2. WHAT WAS BUILT

**`maze3d.tap_sites` and `maze3d.join_taps`**, written to the transaction
discipline `hop_net_pads` and `join_orphans` already use: greedy nearest site
with union-find over the net's own islands, each land independent, a failure
reverted alone, a success merging its two groups so the next land is asked on a
board that already carries its copper.  Five clauses:

  * **TAP1** the target is proved by CONNECTIVITY, not by distance — a site is
    accepted only if KiCad's own `CONNECTIVITY_DATA` puts the track or via it
    lies on in the same cluster as a PAD of exactly one island.
  * **TAP2** nothing is removed and nothing is modified — a tap only ADDS
    copper whose far end lies on a conductor this board already carries, so it
    has no relay to judge and no licence to price.
  * **TAP3** the proof is `offcentre_route`'s own and it is the SCREEN's own —
    `emit=False` still lays each tap, proves it with `verify_laid` in exact
    geometry, and reverts it.
  * **TAP4** a tap makes a STUB, so the netclass decides whether it may be
    asked; `USB_D`, `NFC_RF`, `NFC_RX`, `SWITCH_NODE`, `SPK_OUT` refused BY NAME
    before any search.
  * **TAP5** `max_mm` is an electrical bound and a land beyond it is DECLINED
    and reported, never silently dropped.

**`route_maze_batch.py --tap` / `--tap-max-mm` / `--tap-pairs`** — OFF by
default, ONE call site, handed to the PRIMARY proposal and never to the repair
pass, and run AFTER every move that aims at a pad or at the net's own pour, so
it is offered exactly the lands nothing else could close.  Every tap laid is
named in the run's report with its land, its target object, the exact coordinate
on that object, the gap and the copper — because the ledger sees only that an
edge closed and clause 4 cannot tell a T-junction from a pad-to-pad run.

**`checks/tap_contract.py` — the THIRTEENTH standing contract** (TC1 the screen
and the writer name ONE forbidden-class list; TC2 the lever is OFF by default
with one guarded call site; TC3 a DRY `join_taps` over all 15 askable partially
routed nets leaves the board's object census EXACTLY as it found it — 3362
tracks / 828 vias before and after; TC4 all 2128 tap sites over 25 nets lie on a
conductor connectivity puts in ONE island and on a layer the net's contract
allows, zero offenders, and a forbidden netclass is refused BEFORE any search).

## 3. THE TAP LAYS COPPER, AND IT IS SHORTER THAN THE PAD-TO-PAD ANSWER

Measured inside a real gate run on `/09_COMMUNITY_HEADER/EXT_SCL_BUF` after its
`U16` fan-out was evicted (§4):

    lattice   land    target                              gap     copper   vias
    0.050 mm  R50.2   B 56.400,52.800-55.800,53.500      6.922 mm  11.953 mm  0
    0.025 mm  U16.2   B 56.400,52.800-55.800,53.500      2.066 mm   2.979 mm  0

Both restored the net to `open_edges 0` and both passed every preservation
clause.  `route_join`'s only legal question for that island pair was a PAD:
`U16.2 <-> R50.2` at 7.3 mm across the accessory-power pocket.

**AND THE PITCH CHOSE THE LAND AS WELL AS THE PATH.**  At 0.050 mm the greedy
site was `R50.2` at a 6.922 mm stand-off; at 0.025 mm the SAME target object was
reachable from `U16.2` at 2.066 mm, and the transaction shrank by 9 mm of
copper.  This is D-661 §4 and D-663 §4 in a third place: a finer lattice decides
not only WHETHER a transaction routes but HOW BIG IT HAS TO BE.

## 4. `U16.3` IS A TWO-WALL LAND, AND THE FIRST WALL FALLS TO SEVEN OBJECTS

`U16` is the **TCA4307 accessory I²C hot-swap buffer** and `U16.3` is its
internal-side `SCLIN`: an island of one, so the Community Port's buffered SCL
has no clock.  `AQROOT_DEMO_SCOPE.md` lists `SDA`/`SCL` under the Community
Port's MUST-retain contacts.

**WALL 1 — THE LAND.**  D-655 recorded `U16.3` as *"launches nowhere at all"*
and D-664's own screen reproduces it on this authority: `NO OFF-CENTRE LAUNCH at
0.200 mm from any of 41 anchors x 24 directions x 17 lengths; blocked by U16.2
(x6297), U16.4 (x5870), U16.1 (x2158), track (x1041)`
(`evidence/d664-tap-screen.json`).  The pads are the package's own neighbours on
0.65 mm pitch and cannot move; the **track** is
`/09_COMMUNITY_HEADER/EXT_SCL_BUF` `B.Cu` `(55.900,54.375)-(55.900,53.600)`,
which stands 0.4255 mm off the pad's only free end, and its fan-out T at
(56.075, 54.850) sends a second arm diagonally across the same corridor.

A named seven-object eviction of that fan-out
(`--evict /09_COMMUNITY_HEADER/EXT_SCL_BUF --evict-window 54.4,53.15,56.6,55.15`)
**OPENS THE LAND**: the verdict moves from `NO_LEGAL_ESCAPE` to `NO_PATH`.

**WALL 2 — THE CORRIDOR, AND IT DOES NOT FALL TO PITCH.**  With the land open,
all three nearest own-copper targets — `F.Cu` at 6.048, 6.048 and 7.106 mm —
return `NO_PATH` at **0.050 mm AND at 0.025 mm**
(`evidence/d664-tx-u16-g50.json`, `-g25.json`).  Every nearby `/I2C_SCL_INT`
conductor is on `F.Cu` while `U16.3` is a `B.Cu` land, so the tap must also find
a barrel site in the accessory-power pocket, and it cannot.

Both runs were **REFUSED ON `board_improved` ALONE — 14 of 15 clauses PASS**,
including `no_regression`, `pour_partition`, `no_unlicensed_removal`,
`attributable_drc` and `rebond_priced`: the eviction was fully repaired by the
tap and the board came back exactly as it went in (retained open edges 29 -> 29).

## 5. THE HARNESS THAT POLICES FRAMEWORK CHANGES HAD NEVER COMPARED ANYTHING

`checks/contract_regression.py` states its own purpose at the top: *"a framework
change that lays no copper must leave every contract's REPORT byte-identical,
not merely still-passing"*.  It diffs each contract against
`evidence/<baseline>-<name>.json`.

**THAT FILE HAS NEVER EXISTED, FOR ANY PREFIX.**  Every contract is run into a
`tempfile.mkdtemp()` that is discarded when the process ends, and the only
artifact the harness ever wrote is its own summary.  So every row printed
`NO BASELINE`, `identical` was recorded as `null`, and `all_identical` came back
`False` — for **D-633 through D-663 alike**.  D-663's own
`evidence/d663-contract-regression-post.json` carries `"baseline": null` on all
twelve rows.  Read as *"12/12 RAN, 12/12 PASS"* that is true; read as the claim
the file states, it was never asked once.

**THE FIX IS THE MISSING HALF.**  `--emit-baseline PREFIX` KEEPS each contract's
report as `evidence/PREFIX-<name>.json`, which is the file the NEXT decision's
`--baseline PREFIX` reads.  It refuses to emit under the prefix it is diffing
against, because a run that wrote its own baseline and then compared with it
would prove only that a file equals itself.  The summary now also carries
`contracts_compared`, `contracts_without_baseline` and `vacuous`, so the
document can no longer say `all_identical` without saying whether anything was
compared.

    run                                    contracts  compared  identical  vacuous
    d664 --baseline d633 --emit-baseline   13/13 PASS      0          -      TRUE
    d664 --baseline d664 (control)         13/13 PASS     13        13/13   FALSE

The control is the non-vacuity proof: the comparison machinery works, and every
standing contract is deterministic on an unchanged board.  **From D-665 onward
the diff is real.**

## 6. `BQ25185_SYS` `C27.1` REPRODUCES BYTE-IDENTICALLY ON THIS AUTHORITY

D-663 §5(g) named an 8-object cut on three static DC set-point straps that bonds
`C27.1` to `{C28.1, SW9.2, U12.1}`.  Re-screened on `2900f21a` with
`--cli-control` (`evidence/d664-cut-blame-c27-rescreen.json`, 371.7 s):
`MINIMAL_SET_FOUND`, `matches_upper_bound`, `cli_control.agrees`, Q1 upper bound
41 objects, **the same 8 objects to the micron and the same partition**.  D-597's
rule — a rip-up verdict is a property of a BOARD — is satisfied.

**AND THE GEOMETRY BEHIND IT IS NOW MEASURED.**  On the freed board the pour's
new path is a **0.50 mm channel** at y 76.15-76.65 between `C27.2`'s GND pad
(y 75.90) and `U11`'s north pad row (y 76.90), running east to a column at
x 69.2-71.0 that only exists once the channel opens — KiCad had been deleting it
as an isolated island.  A 0.200 mm strap plus its two clearances needs 0.70 mm,
so **the channel holds the pour or the straps, and not both**: `U11.6`
(`TS_MR`), `U11.7` (`ILIM_VSET`) and `U11.8` (`ISET`) are east-row pins whose
only escape is into that channel.  The transaction therefore needs the tap
(`U11.6`'s own copper is 2 mm away, its nearest PAD `R38.1` is 60 mm away) AND a
reserved lane, and it is now expressible for the first time.

## 7. NEXT, IN ORDER OF LEVERAGE

  1. **`BQ25185_SYS` `C27.1` WITH THE TAP AND A RESERVED LANE** — §6.  The
     8 objects are named and re-proved; the tap answers `TS_MR`'s 60 mm rejoin;
     what is still owed is a `reserve_corridor.py` lane along the 0.50 mm
     channel so the relays cannot re-block what the removal freed (D-663 §5(d):
     freeing a pour and then routing the evicted net is a null transaction
     unless the lane is RESERVED).
  2. **`U16.3` NEEDS A BARREL SITE, NOT A PITCH** — §4.  Wall 1 is solved.
     Wall 2 is a `B -> F` transition in the accessory-power pocket; screen it
     with `screen_via_field.py` / `screen_rebond_site.py` before asking the
     router again, and consider offering the tap `In2`/`In3` targets.
  3. `/I2C_SCL_INT` `U14.7 <-> J1.44` remains **the one OPEN OWNER DECISION**
     (D-655 §7), RECORDED NOT TAKEN.
  4. `copper_sliver` localisation remains an OPEN INSTRUMENT GAP.
  5. `hardware/demo/fab` is STALE against `2900f21a`.
