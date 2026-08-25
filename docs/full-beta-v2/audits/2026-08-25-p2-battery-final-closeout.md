# FBV2-P2-002G / 002H — routing truth, and what the full prefix actually costs

**Date:** 2026-08-25 · **Tasks:** FBV2-P2-002G and FBV2-P2-002H
**Repository HEAD at start:** `984423c` · **Rollback tag:**
`beta-v2-p2-battery-pre-authoritative` → `984423c`

> **RESULT: INCOMPLETE. No authoritative signal copper was written and the
> placement ECO was NOT applied to the authoritative board.**
> `aqroot-Beta-v2.kicad_pcb` is byte-identical to `984423c` — zero signal
> tracks, zero signal vias, In1.Cu GND plane intact.
>
> **What DID close is the thing that made every previous number untrustworthy:
> PR-39.** Router success now means real connectivity between the pads that were
> actually requested, and it is pinned by six regression cases.

---

## 1. PR-39 — router success must mean real connectivity

`run()` has three fallbacks that may REPLACE the requested endpoint: the node
retarget, the hop-to-node, and a `'(node)'` request. Every one of them kept the
requested pad name in the log line, in the journal and in the routed count while
building somewhere else entirely.

The instance that exposed it:

    TAP BAT_RAW R79.1 -> R80.1   5.276 mm

Measured on the board, those pads are **12.030 mm** apart — 5.276 mm is **43.9 %**
of the straight line between them — and the number of `BAT_RAW` track endpoints
inside `R80.1`'s pad is **zero**. R79.1 was already on the node, so the
"successful" connection laid a **redundant loop** and left `R80.1` alone.

**A section 18 replay would have reproduced it faithfully**, because the journal
said it was real.

### The contract now

A route is SUCCESS only if, after the copper is on the board, the **requested**
start pad and the **requested** end pad are in the same connectivity component.
Retargeting is still allowed — it is often the right topology — but only when it
genuinely joins what was asked for. The journal records `requested_a`,
`requested_b`, `actual_a`, `actual_b`, `retargeted` and `requested_connected`;
a retarget that leaves the named pad isolated is reverted, prints
`NOT_CONNECTED`, and does not increment the count.

### Regression, `router_regression` G8 — ALL CHECKS PASS

| case | what it pins |
|---|---|
| **G8-A** | a direct named pair routes and the requested pads connect |
| **G8-B** | a fallback that genuinely joins the requested pads is still SUCCESS |
| **G8-C** | copper laid but requested end isolated → **must FAIL** |
| **G8-D** | the journal records requested AND actual endpoints |
| **G8-E** | save/reload preserves the connectivity verdict |
| **G8-F** | the ledger reports the isolated net as unconnected |

All previous cases (G1…G7) still pass.

> One trap worth recording: G8-D originally did `import route_battery_block`.
> That module calls `main()` at import, so the regression silently started a
> Phase A run inside itself. It reads the source file now.

---

## 2. `net_ledger.py` — connectivity is the primary truth

Routed-connection counts are a secondary metric. FBV2-P2-002F reported **70** and
**71** connections on boards where four pads were sitting in their own islands.
`net_ledger.py` reports, for every in-scope net, how many connected components
its pads fall into — measured on a board that has been **saved and reloaded**.

Phase completion is judged there and nowhere else.

---

## 3. PR-40 — the full prefix is the qualification model

A candidate is **not** route-qualified because it passes a bare-board escape
check, a simultaneous-stub check, or a reduced-prefix probe. Each of those has
now been wrong at least once:

| model | verdict it gave | what actually happened |
|---|---|---|
| bare-board escape | U18 8/8, U19 7/7 | four placements failed Phase A |
| simultaneous stub escape (§3C) | 49 escapes, 0 lost | the same four failed |
| reduced-prefix real-router probe | C00: U19 **7/7**, `R80.1` **CONNECTED** | full prefix: `R80.1` **NOT_CONNECTED**, `D12.1 → R77.1` **NOT_CONNECTED**, `LTC_SHDN U18.6 → Q4.3` **NO_PATH** |

`AQROOT_PROBE_PASS1` therefore runs the **real driver, in the real order**, and
stops after pass 1 — which is exactly the copper that exists around the remaining
bottlenecks — emitting the per-net ledger plus the named target pairs. It is not
a proxy for Phase A; it *is* Phase A's first pass.

**The honest cost of that ruling: about 40 minutes per candidate.** Probing eight
candidates costs roughly five hours before a single complete Phase A begins.
Since the probe is pass 1 of Phase A anyway, the efficient structure is to run
Phase A directly on each candidate family and judge it by the ledger — the same
cost, strictly more information — inside the three-family cap.

### C01, measured on the full prefix

    targets 0011111   U19 5/7   ledger 22/29

`LTC_SHDN`, `LTC_GATE`, `Q3_CS`, the `BAT_PROTECTED_P` trunk and the `U14` branch
all hold. `BAT_RAW` does not.

---

## 4. Two defects of my own, found by measuring rather than assuming

### The joint search was never joint

The candidate assembler carried a stray `break`, so **all eight "joint"
candidates shared one R80/R81 pose** — `R80 (8.000, 68.000) rot 180`,
`R81 (5.500, 70.500) rot 90`. Only U19 was ever varied. Every candidate therefore
failed `R80.1` in exactly the same way, and the sweep was spending forty minutes
a candidate to re-learn it. **R80's pose has never actually been searched.**

### `R80.1` was never sealed

Measured on the finished C01 board:

    R80.1  (8.825, 68.000)   ESCAPES 0.20 mm (2 directions)

    BAT_RAW islands = 3
       {C59.1, F1.2, Q2.7, Q2.8, R86.2, R89.1, TP16.1}   the battery node
       {R77.1, R79.1, R80.1, U18.1}                       the divider chain
       {D12.1}

**`R80.1` is already joined to the divider chain.** The gap is the *chain* island
reaching the *battery node*, and the plan bridges them with exactly two entries —
`R80.1 → Q2.7` and `D12.1 → R77.1` — both of which failed, leaving the closure
stage as the last chance.

**PR-41: the closure stage was handing those microamp pads the BAT_MAIN trunk
ladder `[1.00, 0.80, 0.60]`.** `BAT_RAW` is a WIDE net, so every one of its pads
inherited the trunk ladder — including the LTC4368 divider chain, which D-249
rules at 0.20 mm and which this plan routes as TAPs everywhere else. Asking a
0.20 mm-class pad for 0.60 mm minimum is why `R80.1 → (node)` returned
`NO_LEGAL_ESCAPE`.

**This is PR-37's defect one net over**, and it was diagnosed the same way — by
measuring the pad instead of believing the failure message.

### PR-41 is validated, and it is not sufficient

A full Phase A on C00 with PR-41 applied produced **zero `NO_LEGAL_ESCAPE`
results anywhere in the run**, against C01 where `R80.1 -> (node)` failed with
exactly that. The width-rule defect is gone. What replaced it:

    BAT_RAW   R80.1 -> (node)   NO_PATH   729s

`NO_LEGAL_ESCAPE` means the pad could not take the width it was asked for.
`NO_PATH` means the pad escaped fine and the corridor was full. **PR-41 fixed
the thing it named and revealed the thing underneath**, which is contention.

---

## 4b. PR-42 and PR-43 — what the contention actually is

### PR-42: the joint search, made joint

With the stray `break` removed, the same search yields **six distinct R80
poses** instead of one, including `(7.00, 62.50)` — nowhere near the pose every
prior candidate shared. U19's box (y 8…34) and the R80/R81 box (y 56…78) are
disjoint and share no net, so they are **independent axes**: a full
40 × 20 × 20 cross would spend the candidate budget re-probing one R80 pose
under a different U19. The search sweeps each axis instead, and spends most of
the budget on the pad that is actually failing.

An `AQROOT_SEARCH_ONLY` guard regenerates the candidate list without running the
40-minutes-a-candidate probe.

### The corridor exists — measured

A bare-board flood on C00, used strictly as a **negative** test (PR-40: presence
proves nothing, absence would be decisive):

    R80.1  (9.325, 68.000)   ->  Q2.7, Q2.8, F1.2, C59.1     at 0.20 mm
    D12.1  (10.950, 17.000)  ->  Q2.7, Q2.8, F1.2, C59.1     at 0.20 mm

Both bridges reach the battery node on an empty board. **So no R80 pose is
required to make this routable, and the remaining candidate budget should not be
spent on R80.** That is the opposite of what PR-34 assumed, and it is the first
measurement that could distinguish the two.

### PR-43: schedule by corridor scarcity, not by net role

    R80.1 -> Q2.7     21.5 mm
    D12.1 -> R77.1    45.5 mm

Both are `TAP` by role, so PR-36 scheduled the whole tap group after the trunk,
the BAT_MAIN chain **and U18's eight-pin field**. That ordering is right for a
tap in the usual sense — short, local, several ways out. These two are not that:
they are the LTC4368 divider chain's only link to the battery node, and their
only corridor is the west margin at x 4…10 — the same margin the 1.50 mm
`BAT_PROTECTED_P` trunk, `BAT_SENSE` and `BAT_MID` have already taken.

So the two long bridges are scheduled **with the chain**, by the same scarcity
argument PR-18 used for the trunk itself, and the genuinely local taps stay where
they are. U18's pins are short and have alternatives; these have one corridor
each.

**PR-43 is applied and UNPROVEN.** Its Phase A was killed before it reached the
first bridge. It costs nothing in placement and is the cheapest remaining
hypothesis, so it should be the first thing the next task runs.

---

## 5. State at the end of this session

| | |
|---|---|
| authoritative PCB | **byte-identical to `984423c`** — 0 signal tracks, 0 signal vias |
| placement ECO applied to it | **NO** |
| rollback tag | `beta-v2-p2-battery-pre-authoritative` → `984423c`, pushed |
| PR-39 | **CLOSED**, regression-tested |
| PR-40 | **implemented**, and it has already rejected a candidate a cheaper model passed |
| PR-41 | **validated as a real fix** (0 `NO_LEGAL_ESCAPE` board-wide), **not sufficient** |
| PR-42 | joint search fixed — 6 distinct R80 poses where there was 1 |
| PR-43 | applied, **unproven** — its Phase A was killed before the first bridge |
| Phase A | **not passed** |
| Phase B | **NOT RUN** |
| manifest | **not created** |
| B-34 | **OPEN** — physical first-article validation remains mandatory |
| PCB routing | **0 %** · overall Full Beta v2 **74 %** |

**No progress was earned and none is claimed.**

---

## 6. What the next task needs

1. **Run one Phase A with PR-43.** It is applied, it costs no placement change,
   and it is the only untested hypothesis that matches the measured evidence —
   the corridor exists on a bare board, so the failure is contention and
   contention is an ordering question.
2. **Do not spend the candidate budget on R80.** The bare-board flood shows both
   bridges reach the battery node from the existing pose. PR-34 assumed R80
   needed the PR-25 treatment; that assumption is now measured against, and the
   six new R80 poses are a fallback, not the first move.
3. `U19` still reaches only 5/7 under the full prefix, and `U19.8 -> C60.1` is
   `NO_PATH` across a 2.668 mm gap. **That** is still a placement question, and
   it is the part of PR-34 that survives.
4. **Run Phase A directly per candidate family** rather than probe-then-Phase-A;
   the probe is pass 1, so the two-step costs double for no extra information.

---

## 7. A process note, recorded because it cost more than any defect here

Across FBV2-P2-002F, 002G and 002H the largest single consumer of session budget
was not routing, searching or diagnosis — it was **polling the router log in a
tight loop while a correctly-armed monitor was already waiting to report the same
event.** The monitors worked; they were simply not trusted. Every conclusion in
this document came from a measurement that took seconds once the right question
was asked, and the questions were delayed by the polling, not by the tooling.
