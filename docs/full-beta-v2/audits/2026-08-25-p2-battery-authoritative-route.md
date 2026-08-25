# FBV2-P2-002E — Resuming battery / protection routing from the clean checkpoint

**Date:** 2026-08-25 · **Task:** FBV2-P2-002E — resume battery / protection routing from the
`e09eb35` checkpoint
**Repository HEAD at start:** `e09eb35`
**Result: FBV2-P2-002E = FAIL. PHASE A DID NOT COMPLETE, SO PHASE B WAS NOT RUN.**
**The authoritative PCB is byte-identical to `e09eb35`: zero tracks, zero signal vias.**

> **First unresolved FUNCTIONAL connection, by section 8's own numbering: `BAT_RAW`
> `R80.1 → Q2.7`** — the LTC4368 divider chain `{R77.1, R79.1, R80.1, U18.1}` never joins the raw
> battery node `{F1.2, Q2.8, Q2.7, C59.1}`. **The most consequential one is `LTC_GATE`
> `U18.10 → Q3.4`**: the gate-drive net finishes in two pieces, `{U18.10, R76.1, TP17.1}` and
> `{Q2.2, Q2.4, Q3.2, Q3.4}`, so the LTC4368 GATE output is not connected to the FETs it drives.
>
> **What did land, and it is the most this block has ever reached.** 60 connections coexisted on one
> scratch board with **zero new DRC violations of any class at every step**, ratsnest **781 → 718
> (−63)** against the previous best of −32. The whole high-current path is closed end to end —
> `J4 → F1 → Q2 → Q3 → R75 → D9 → U11.2` — with the **`BAT_PROTECTED_P` trunk at its 1.50 mm target
> on B.Cu carrying zero vias**, both R75 Kelvin branches genuine, the U11.2 flare measured, the
> MAX17048 taps in, the dead-cell network **routed for the first time**, and TP17 reduced from the
> 24.1 mm second-route it wanted to a **5.741 mm stub**.
>
> **15 in-scope connections remain open**, and they are not spread evenly: they cluster on pins that
> physically cannot escape. That is a placement finding, not a router finding, and section 11 is
> explicit that the architecture is not to be weakened to finish. So it was not.

---

## 1. Preflight

| check | result |
|---|---|
| HEAD / `origin/master` | both `e09eb35` |
| Tracked working tree | clean; only the expected long-standing untracked paths |
| Authoritative tracks / signal vias | **0 / 0** |
| In1 plane | 1 zone, 1 island, net GND |
| DRC baseline | **1** (`solder_mask_bridge`, MK1, D-227) + **499** unconnected; ratsnest **781** |
| ERC | **0 errors / 27 warnings** |
| `p1_regression` / `router_regression` / `dru_probe` / `netclass_probe` / `fork_equivalence` | **PASS ×5** |
| Frozen trees (`hardware/beta-dm/`, `hardware/beta/`, Beta-DM Gerber ZIP, tag `beta-v2-p2-entry-pass`) | untouched |

The approved placement baseline was verified pad-by-pad rather than assumed: `TP17` (12.500,
76.000) B.Cu, `C58` (13.000, 68.500) B.Cu, `C59` (8.000, 41.500) rot 90 B.Cu. All three match §3.

---

## 2. Five harness defects, and one of them was a segmentation fault

Section 2 says not to redevelop the router unless a NEW reproducible bug appears. Five did. None of
them is in `qrouter.py`; all five are in the driver and the plan, which is where the previous task
had not yet been stressed because it had never routed this far.

### PR-15 — `split_at` corrupted `qb.laid`, and the second corruption SEGFAULTED

`split_at()` replaces ONE track in `qb.laid` with TWO, so that a branch joining the middle of a
trunk becomes an exact three-way endpoint instead of a `track_dangling` report. The mark taken
before the split is an **index into that same list**. Inserting an extra entry ahead of the mark
shifts everything after it by one, so `revert()` then removed a track belonging to the **trunk** and
left one of the branch's own behind. Do it twice on the same trunk and the second revert calls
`BOARD::Remove` on an item that is no longer in the list — which segfaults the interpreter rather
than raising.

That is exactly how the first run died: **exit 139 at `BAT_CONNECTOR_P TP34.1` after 55
connections**, with no Python traceback at all because only `dump_traceback_later` was armed and not
`faulthandler.enable()`.

Fixed by shifting the mark with the list and keeping enough state to put the trunk back; the split
is now fully undoable. `faulthandler.enable()` is on, so a future crash names the call.
**`router_regression` gains G7**, which is arithmetic rather than a crash test: lay copper, mark,
split an earlier track, undo, revert, and require the board and the laid list to be exactly what
they were. G7 passes; all previous checks still pass.

### PR-20 — the item budget was starving the fallbacks, and it looked like a nondeterministic router

Both topology fallbacks are guarded by `time.time() - t0 < ITEM_BUDGET`. When the B.Cu width ladder
alone ran past the budget, the F.Cu hop was **never attempted**. `BAT_SENSE Q3.6 → R75.1` routed in
86 s on one run and returned `NO_PATH` after 167 s on the next **with identical copper in front of
it** — the only difference was how busy the machine was. Section 13 allows ten minutes per
connection; the budget now sits inside that at 420 s.

### PR-21 — a trunk was silently losing width to buy a layer hop

The hop fallback used the narrowest rung only. That took `BAT_SENSE Q3.6 → R75.1` down to 0.60 mm
to cross to F.Cu — trading 4.4 mΩ of B-34 for two vias worth 1.8 mΩ, silently. TRUNK roles now try
the full ladder across a hop and that connection lands at **1.00 mm**. Signal and tap roles still
use the narrowest rung, where the hop really is about topology.

### PR-22 — connectivity was being read from a file that held reverted copper

The already-connected check re-read the `.kicad_pcb` from disk. `gate()` **saves before it judges**,
so after a REJECTED connection the file still carried copper that had since been reverted out of
memory. The next item asked that file whether its two pads were already joined, was told yes, and
was skipped. Connections that had never been routed were being counted as done — `Q2_CS Q2.1 →
Q2.3` was skipped "already joined" on a board where it did not exist. Connectivity is now judged on
the live board.

### PR-16 — the section 9 stub cap belongs to TP17, not to every test point

A 10 mm cap on all TEST branches rejected `TP20` at 14.712 mm against a limit nobody wrote. Section
9 sets 10 mm for **TP17**; section 4 gives the other test taps a WIDTH ruling and no length ruling.
The cap is now TP17's alone.

> **A process note worth recording.** Several intermediate runs contradicted each other because
> `taskkill` was being given the Cygwin PID from `ps -W` column 1 instead of the Windows PID in
> column 4, so killed router processes kept running and two of them wrote the same scratch directory
> and the same log. Every conclusion in this document comes from the final single-process run.

---

## 3. Ordering: three rulings from section 8 and section 9 that the plan was not following

### PR-18 — the trunk goes before the pin field (section 8 order 1)

The queue used to open with U18's whole pin field, on the argument that an MSOP-10 pin has a
0.325 mm escape window and no second chance. True, but it inverts the scarcity: a 0.20 mm sense tap
that lands **on** `R75.2` takes the 1.20 mm trunk's only escape from that pad, and no later pass can
give it back because copper on this board only ever accumulates. `BAT_PROTECTED_P R75.2 → D9.1`
came back `NO_LEGAL_ESCAPE` at 0 s once `U18.8`'s tap had gone in first.

**A wide corridor cannot be recovered; a 0.20 mm one usually can.** With section 8's order the trunk
lands at **20.416 mm, 1.50 mm, B.Cu, zero vias** — its target width, not its floor.

### PR-17 / PR-19 — the pin-field order is MEASURED, not guessed

Three hand-picked orders inside U18 each simply moved the casualty: inner pins first lost `U18.10`
and `U18.1` to `NO_PATH`; outer pins first lost `U18.9` — the **Kelvin branch section 10 makes
mandatory** — to `NO_LEGAL_ESCAPE`. There is no fixed right order, because the window each pin has
left depends on the copper already laid.

So it is measured. Before each pass, every remaining fine-pitch pin is asked by binary search how
wide a track can still legally leave it, and the tightest goes first. Measuring **once per pass**
is what holds: re-measuring before every item picks whichever pin is locally tightest and then lays
a route that closes two others — it took U18 from 7 escapes of 8 down to 6.

### PR-23 — section 9's gate-before-CS, proved on Q3

Section 9 is explicit: *"Route the actual gate-drive network FIRST: U18 gate control, Q2 gates, Q3
gates."* The plan had the FET sense pairs first, on the argument that `Q*_CS` is boxed between two
gate pads while `LTC_GATE` has an F.Cu hop. On Q3 that is simply not what happens: the 0.25 mm CS
route threads both 0.67 mm inter-pad gaps and **`Q3.2` is left with `NO_LEGAL_ESCAPE` — no width, no
layer, nothing.** With section 9's order the whole FET gate network closes (`Q3.2 ↔ Q3.4`,
`Q2.2 ↔ Q2.4`, `Q3.2 ↔ Q2.2`) and `Q3_CS` is the one that fails instead. That is the right trade and
it is the one section 9 already made.

### PR-24 — close what is still open, before the test points

The plan names ONE pad pair per connection, and when that exact pair has no corridor the net stays
open even though the pad may be one short tap from copper the net already owns. Connectivity does
not care which pair carries it. A closure stage now offers every still-open pad a tap on the nearest
legal point of its own net, **after** the named plan and **before** any test point, so a test point
still cannot take a functional corridor. 84 of its entries were correctly skipped as already joined.

---

## 4. What Phase A actually laid — measured, not asserted

Scratch board, one project-faithful copy, saved / reloaded / refilled / DRC'd after **every** single
connection. **DRC at the end is identical to the baseline**: `{'solder_mask_bridge': 1,
'unconnected_items': 499}` — no new violation of any class, at any step.

| path | routed | width | vias | layer |
|---|---|---|---|---|
| `BAT_CONNECTOR_P` `J4.1 → F1.1` | 9.871 mm | 1.00 mm | 0 | B.Cu |
| `BAT_RAW` load `F1.2 → Q2.8 → Q2.7` | 7.996 mm | 1.00 / 0.80 mm | 0 | B.Cu |
| `BAT_MID` `Q2.5 → Q2.6 → Q3.8 → Q3.7` | 18.106 mm | 1.00 / 0.80 mm | 0 | B.Cu |
| `BAT_SENSE` load `Q3.5 → Q3.6 → R75.1` | 17.553 mm | **1.00 mm** | 2 | B.Cu + F.Cu |
| `BAT_SENSE` **Kelvin** `R75.1 → U18.9` | **3.179 mm** | 0.20 mm | 0 | B.Cu |
| `BAT_PROTECTED_P` **Kelvin** `R75.2 → U18.8` | **23.799 mm** | 0.20 mm | 0 | B.Cu |
| `BAT_PROTECTED_P` trunk `R75.2 → D9.1` | 20.416 mm | **1.50 mm** | **0** | B.Cu |
| `BAT_PROTECTED_P` `U11.2 → D9.1` incl. flare | 73.615 mm | 1.50 mm | **0** | B.Cu |
| `BAT_RAW` VIN tap `U18.1 → R77.1` | **32.204 mm** | 0.20 mm | 0 | B.Cu |
| `U14.2 → TP15.1` (MAX17048) | **31.228 mm** | **0.15 mm** | 0 | B.Cu |
| `C59.1 → F1.2` (BAT_RAW bulk) | 3.407 mm | 0.60 mm | 0 | B.Cu |
| `C58.1 → D9.1` (BAT_PROTECTED_P bulk) | 4.557 mm | **1.50 mm** | 0 | B.Cu |
| `LTC_GATE` `TP17.1` stub | **5.741 mm** | 0.25 mm | 0 | B.Cu |
| `TP34.1` stub | 1.523 mm | 0.60 mm | 0 | B.Cu |

**R75 Kelvin mismatch: 23.799 − 3.179 = 20.620 mm.** Both branches originate at the correct R75 pad
and neither carries load current, so the mismatch is a *noise-coupling and layout-quality* issue
rather than a measurement-accuracy one — but at 7.5× it is much worse than FBV2-P2-002C's 7.261 mm
and it is the direct cost of the trunk now taking its corridor first.

### The U11.2 escape, re-measured on this placement

Unchanged from the ruling and still inside it: **0.20 mm neck 0.575 mm long**, then a strictly
monotonic flare 0.30 → 0.40 → 0.60 → 0.80 → 1.00 → 1.20 → 1.50, **no via, no thermal relief**,
**4.214 mΩ** over 4.878 mm of escape. **Sub-1.20 mm length is 4.737 mm against section 5's 5.25 mm
cap — inside it**, and the 0.20 mm section is 0.575 mm against a 0.75 mm cap. §5 satisfied in full.

### Path-role corridors (PR-11)

All five fixed corridors plus two bounded shunt stubs are centre-line capsules generated from their
own routed copper at 0.10 mm per side. Fill ratios 0.08 – 0.48 against their bounding boxes — i.e.
a corridor covers between 8 % and 48 % of the box a box-rule would have opened. No corridor is a
rectangle, none is a large dead area, and the widest (`BAT_PROT_TAP_U14`, 14.5 mm² over a
9.34 × 19.31 mm span) follows a 31 mm branch at 0.15 mm.

---

## 5. The 15 connections that would not route, and why they are a placement finding

| net | open clusters |
|---|---|
| `LTC_GATE` | `{U18.10, R76.1, TP17.1}` ‖ `{Q2.2, Q2.4, Q3.2, Q3.4}` |
| `BAT_RAW` | node ‖ `{R77.1, R79.1, R80.1, U18.1}` ‖ `D12.1` ‖ `R86.2` ‖ `R89.1` ‖ `TP16.1` |
| `LTC_UV` | `U18.2` ‖ `R79.2` |
| `LTC4368_FAULT_N` | `{Q9.1, R81.2, R82.1}` ‖ `U18.7` ‖ `TP18.1` |
| `Q3_CS` | `Q3.1` ‖ `Q3.3` |
| `REF_POL` | `{R87.2, R88.1, TP24.1}` ‖ `U19.2` |
| `N_POL` | `{R85.2, TP23.1, U19.3}` ‖ `R86.1` |
| `N_BATDIV` | `{C61.1, U19.6}` ‖ `{R89.2, R90.1}` |
| `BAT_SENSE` / `BAT_PROT_SHDN_CTL` | `TP20.1` ‖ node · `TP19.1` ‖ node |

**Nine of the fifteen failed with `NO_LEGAL_ESCAPE` at 0 s** — the pad cannot emit a legal track at
any width on any layer, before pathfinding is even attempted. That is not a search failure. `U18.2`
and `U18.7` are interior pins of an MSOP-10 whose neighbours have already taken the only corridor;
`Q3.1`/`Q3.3` are the CS pair sealed by the gate routes section 9 requires to go first; `R86.1`,
`R89.1`, `U19.2` are dead-cell divider pins in the same congested west margin.

**U18 escapes 6 of its 8 signal pins on this placement.** The best any ordering achieved was 7 of 8.
The constraint is geometric: U18 occupies x 1.23 – 4.83 and the divider wall R76/R77/R78/R79 sits at
x 7.00 – 10.33, so **every north-row pin escapes through the same ~2.2 mm corridor and there is no
second one.**

---

## 6. Timing and the watchdog (section 13)

| | |
|---|---|
| Phase A wall clock | **4 749.8 s** (1 h 19 m), 3 passes |
| Longest single route | **245.9 s** — `REC_DIODE_IN` `TP22.1 → R95.2` |
| Routes over 150 s | 2 (245.9 s, 171.2 s) |
| Routes over 600 s | **0** |
| Watchdog interventions | **none required in the final run.** The 900 s watchdog fired its periodic traceback dumps and no connection was ever inside one. |
| Diagnostic captures | **1**, in the FIRST run: the segfault at `TP34.1`, diagnosed to `split_at`/`revert` index arithmetic (PR-15) and fixed. |

No silent multi-hour run occurred. Every stall this task saw was diagnosed to a specific call.

---

## 7. B-34 from Phase A copper (scratch, NOT authoritative)

Phase B did not run, so **B-34 is not recalculated against authoritative copper and does not
change.** The scratch figures are recorded because they are the best evidence available and because
they move in the right direction:

| segment | length | widths | copper | vias |
|---|---|---|---|---|
| `BAT_CONNECTOR_P` | 11.394 mm | 1.00 / 0.60 | 6.09 mΩ | 0 |
| `BAT_RAW` (load portion) | 7.996 mm | 1.00 / 0.80 | ≈ 4.4 mΩ | 0 |
| `BAT_MID` | 18.106 mm | 1.00 / 0.80 | 9.30 mΩ | 0 |
| `BAT_SENSE` (load) | 17.553 mm | 1.00 | ≈ 8.6 mΩ | 2 (1.76 mΩ) |
| `BAT_PROTECTED_P` trunk | 93.509 mm at 1.50 | 1.50 | ≈ 30.6 mΩ | 0 |
| `U11.2` escape | 4.878 mm | 0.20 → 1.50 | 4.21 mΩ | 0 |

**Copper total on the pack-current path ≈ 65 mΩ**, against ≈ 75 mΩ measured at FBV2-P2-002C and
≈ 50.6 mΩ originally assumed. At 1.5 A that is ≈ 98 mV / 146 mW of copper loss and at 1.75 A
≈ 114 mV / 199 mW, **before** F1, Q2/Q3 R_DS(on) and the BQ25185 BATFET, which dominate the total
and are not copper. **B-34 STAYS OPEN — physical validation required**, exactly as expected.

---

## 8. Issues raised for CTO / owner ruling

| id | issue | status |
|---|---|---|
| **PR-25** | **U18 cannot escape all eight signal pins where it sits.** 6 of 8 on the final run, 7 of 8 at best, across four different orderings. The whole north row shares one ~2.2 mm corridor between U18 (x ≤ 4.83) and the divider wall (x ≥ 7.00). **Needs a placement decision** — move the R76/R77/R78/R79 wall east, or rotate/reposition U18 — not another routing attempt. | **OPEN — placement ruling required.** |
| **PR-26** | **`Q3_CS` and `LTC_GATE` cannot both escape Q3's south row.** The pins interleave (CS on 1/3, GATE on 2/4) with 0.67 mm gaps; whichever goes first seals the other. Section 9 makes GATE first, so `Q3_CS` is the casualty. Q2's identical row routes both, so this is Q3's local congestion, not the package. | **OPEN — needs a Q3-area placement or a deliberate `Q3_CS` via-drop ruling.** |
| **PR-27** | **`REC_DIODE_IN` spans 64.464 mm and `VREC_VCC` 60.053 mm on megohm-impedance dead-cell nodes.** Section 11 asks for short high-impedance paths. Values and topology are untouched, but these lengths are a leakage and noise-injection risk that a ratiometric comparator network should not carry. | **OPEN — needs either a placement fix or an explicit acceptance.** |
| **PR-28** | **`U18.1` VIN tap routed 32.204 mm against section 4's preferred 10 mm maximum**, and the **R75 Kelvin mismatch is 20.620 mm**. Both are consequences of the trunk taking its corridor first (PR-18), which is the correct priority. | **OPEN — accept, or re-place U18 with PR-25.** |
| **PR-29** | **`U14.2` routed 31.228 mm at 0.15 mm against section 4's 15 mm maximum branch length** for the MAX17048 taps. The width ruling is met; the length ruling is not. | **OPEN — needs a length ruling or a U14 placement fix.** |

---

## 9. What was NOT done, deliberately

* **No authoritative copper was written.** Section 14 and section 19 are unconditional about this
  and Phase A did not pass. `aqroot-Beta-v2.kicad_pcb` is byte-identical to `e09eb35`.
* **PM-2 does not close.** Section 16 requires a routed, clean, authoritative block.
* **B-34 is not closed** and is not recalculated authoritatively.
* **No architecture was weakened to finish.** Section 11 forbids it: D10/D11 stay separate matched
  parts, the ratiometric topology, every threshold and every value are untouched, and no
  connection was dropped or re-aimed to make a number look better.
* **No converter, bus or out-of-scope copper exists.** Scope audit on the scratch board:
  **zero out-of-scope nets carry copper.**
* **No progress was earned.** PCB routing stays 0 %; Full Beta v2 stays **74 %**.
