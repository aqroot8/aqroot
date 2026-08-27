# FBV2-P2-002Y — D-271: the 002W prefix is pinned and deterministic, and the "proven 8/8" board is not reconstructible from committed code

**Date:** 2026-08-27 · **Task:** FBV2-P2-002Y · **Starting HEAD:** `8725eea`
**Verdict:** **DECISION STOP.** The reproduction gap FBV2-P2-002X flagged is
**resolved as a reproducibility defect, not a router defect.** The 002W
qualification prefix is now **pinned and self-describing** (`prefix_002w.py` +
`prefix_002w_manifest.json`), and on the AUTHORITATIVE board this recipe
deterministically reserves `U18.8` at **(3.000, 71.600)** — the blocking site —
at 002T, 002U and HEAD alike. The **"002T-proven (3.750, 71.600)" 8/8 board is
NOT produced by the committed code with any constructible recipe**; it belongs to
a western margin the repository cannot rebuild. **002X's D-269-clearance
hypothesis is superseded** (the pre-D-269 code gives (3.000) too) and its
`BAT_SENSE`-blocker conclusion is **confirmed and tightened** on a reproducible
board: the current-carrying `BAT_SENSE` diagonal seals `U18.7`, so the margin
cannot reach 8/8. The authoritative PCB is unchanged.

---

## 1. What FBV2-P2-002X asked, and the CTO ruling that framed 002Y

002X could not rebuild the "002W 8/8" prefix (`probe_002w_W3.json`, targets
`111111111`, U18 8/8): every recipe it tried landed at 6/8 or 7/8, with the
`U18.8` reservation via at **(3.000, 71.600)** rather than the 002T-recorded
**(3.750, 71.600)**, and it named that a "D-269-clearance / reservation-scoring
interaction." The CTO **declined to accept the `BAT_SENSE`-as-trunk-blocker
conclusion** on a non-reproducing 6/7-of-8 board and ruled 002Y a
**harness/reproducibility and routing investigation**: reproduce the exact
prefix first, root-cause the site drift, make it deterministic and pinned, and
only then re-run the offload/trunk analysis on the reproduced board.

## 2. The site drift is not a clearance interaction — it is recipe non-pinning

The root cause is measured, and it is not the one 002X named.

**(a) The recipe was never pinned.** No committed file stated the exact flags,
order and placement that produce the governed prefix. Each task guessed; each
studied a different board. The committed artefacts are themselves from different
eras — `phaseA.json` records the 002T Kelvin (`U18.8` inner run 6.956 mm) while
`probe_002w_W3.json` records the 002W targets — so there was never one board to
reproduce.

**(b) The placement trap.** `RU.fresh` copies the AUTHORITATIVE six-layer board;
`AQROOT_ECO_002F=1` silently swaps in a placement that differs in **nine parts**
(`U18` and `R76..R83`: authoritative `U18@3.000,72.400`, ECO `U18@8.000,65.250`).
The board 002X studied on disk (`w/X0`) is on the AUTHORITATIVE placement; a run
that adds `ECO_002F` measures a wholly different western margin. The fix is the
driver's own guard: **`AQROOT_EXPECT_PLACEMENT=AUTHORITATIVE`** refuses to route
on the wrong placement, and it is now part of the pinned recipe.

**(c) The site is deterministic and D-269 is not the cause.** With the
AUTHORITATIVE placement, the pinned recipe reserves `U18.8` at **(3.000,
71.600)** on **both** the scored and the nearest-exit attempt, and it does so at
commit `798d0ae` (002T, pre-D-267), `6ebb009` (002U) and `8725eea` (HEAD) —
identical output. So the D-269 clearance rewrite (`6edc34a`) cannot be the cause:
the code before it selects the same site. `reserve_escape` is byte-identical
across 002T→HEAD; the reservation plan and order are byte-identical; there is no
tie-break instability and no state leakage (`fresh` reconstructs the board from
the authoritative source every run).

**(d) The site is the ONLY candidate, and it is not the true blocker.** Instrumented
(`SEAL-DBG`), `U18.8` has exactly one escape/via candidate at that point in the
schedule — (3.000, 71.600) — and laying the reservation there **seals no sibling
pad at reservation time**. `U18.7` is sealed *later and cumulatively* by the
western-margin copper. Forcing `U18.8` onto (3.750, 71.600) does not help: that
via is DRC-illegal on this board (`solder_mask_bridge`, `shorting_items`,
`clearance`), and `U18.7` stays blocked regardless.

## 3. Why the "3.750 / 8-of-8" board cannot be rebuilt

The 002T record and the reproducible board are two different western margins:

| quantity | 002T audit (the "proven" board) | reproducible board (002T/002U/HEAD code) |
|---|---|---|
| `U18.8` reserved via | (3.750, 71.600), nearest-after-retry | **(3.000, 71.600), scored, sole candidate** |
| `R75.2` reserved via | (1.200, 65.700) | **(2.800, 63.200)** |
| `BAT_SENSE Q3.6→R75.1` | **13.532 mm** | **18.200 mm** |
| U18 | 8/8 | **6/8 (open `U18.7`, `U18.8`)** |

Crucially, running the pinned recipe **at the 002T commit itself** reproduces
18.200 mm and (3.000, 71.600), **not** the 13.532 mm / (3.750) the 002T audit
records. The audited numbers therefore describe a board state the committed code
does not produce — the recipe that produced them is lost. This is stated
plainly, not handwaved: it was checked against git history and the stored JSON,
with bounded scratch runs at three commits.

## 4. The true blocker, on a board that reproduces

The 18.200 mm `BAT_SENSE Q3.6→R75.1` current path routes east to x=6.75 and back
as a **diagonal wall (6.75, 62.45) → (2.80, 66.40)** — the exact current-carrying
diagonal FBV2-P2-002X named, here proven on a deterministic board. In this
margin it is `U18.7`'s casualty, one pad west of the trunk's: the pin field
cannot escape `U18.7` past that wall plus the `U18.8` reservation copper. It is a
1.00 mm, 1.5 A shunt sense path — a **current-carrying role**, which D-249/D-264/
D-267/D-269/D-270 all correctly refuse to move, thin, offload or via. **No legal
reservation site and no low-current offload set opens 8/8 on this board.**

## 5. What is delivered — determinism, self-description, a pinned regression

- **`prefix_002w.py`** — the one-command pinned regression. It states the exact
  recipe in-file (`RECIPE`, including `AQROOT_EXPECT_PLACEMENT=AUTHORITATIVE`),
  runs the driver, and checks two gates:
  - **DETERMINISM** (exit 2 on drift): the board must reproduce
    `prefix_002w_manifest.json` — AUTHORITATIVE placement, `U18.8` (3.000,
    71.600), 18.200 mm sense path, U18 6/8 open `U18.7`/`U18.8`. This is the
    guarantee that a future task cannot **unknowingly** study a different board.
  - **GOVERNED GOAL** (exit 1 on failure): U18 8/8 with `U18.8` off the blocking
    site. **This fails on the reproducible board, by design and by the brief** —
    "it must fail when `U18.8` lands at the blocking site or U18 drops below 8/8."
- **`prefix_002w_manifest.json`** — the pinned board fingerprint and the governed
  goal, blessed from a real run.
  **SHA256 `3c7128580053cf5ab3c69774da5405ab4074b309e89da93b58c161b20fd3ecd1`.**
- **`probe_002w_prefix.json` — deliberately NOT tracked.** It is `prefix_002w.py`'s
  `AQROOT_PROBE_OUT` raw dump, regenerated deterministically on every validate run.
  No consumer requires it: the validator compares against the manifest, and every
  number it holds (targets `111010111`, U18 6/8 open `U18.7`/`U18.8`, `U18.8`
  (3.000, 71.600), 18.200 mm sense path) lives in the manifest's `deterministic`
  block. It is `.gitignore`d as a regenerated artifact; re-running the driver
  recreates it byte-for-byte.

## 6. The offload / trunk re-analysis, on the reproduced board

The brief's §5 asks to re-run 002X's per-branch cut analysis **once the 8/8
prefix reproduces**. It does not reproduce — U18 is 6/8 — so the honest result is
§6's alternative: **localise the true current-role blocker and do not infer from
the non-reproducing board.** The blocker is localised (section 4): the
`BAT_SENSE` current-path diagonal, which seals `U18.7` before the trunk is even
reachable at 8/8. The offload study `offload_002x.json` was measured on this same
AUTHORITATIVE placement and already found **no low-current offload set of any
cardinality opens `R75.2→D9.1` at ≥1.20 mm** — only removing `BAT_SENSE` does,
and `BAT_SENSE` is current-carrying. That conclusion stands; what 002Y adds is
that the margin fails one pad earlier, at `U18.7`, for the **same** reason. **No
real B.Cu zero-via trunk was attempted, because the prefix it must sit on is not
8/8; manufacturing a trunk on a 6/8 board would be exactly the kind of pass this
task forbids.**

## 7. Bounding FBV2-P2-002X

- **Superseded:** 002X's attribution of the site drift to a "D-269-clearance /
  reservation-scoring interaction." Measured at three commits, the pre-D-269 code
  selects (3.000, 71.600) too; D-269 changed nothing about this reservation.
- **Superseded:** the framing that reproducing (3.750, 71.600) would change the
  answer. (3.750) is DRC-illegal on the reproducible board and the site is not
  the blocker; the reservation seals no sibling at reservation time.
- **Confirmed and tightened:** the western-margin blocker is a **current-carrying
  role** (`BAT_SENSE`), not low-current copper — now shown on a *deterministic*
  board, and shown to bind at `U18.7` (pin field) as well as at the trunk. The
  architecture question 002X and D-268 raised is unchanged and now rests on
  reproducible evidence.

## 8. Suites and board state

- **Starting HEAD:** `8725eea`. **Ending HEAD:** this commit.
- **Authoritative PCB:** six copper layers (JLC06161H-7628), **0 signal tracks,
  0 signal vias — unchanged.** TP17, C58, placement, topology, netclasses all
  untouched. No placement ECO. No converter, no Phase B, no U19.
- **Standing suites** (`d264_probe`, `d266_probe`, `d267_probe`, `d269_probe`,
  `d270_probe`, `dru_probe`, `netclass_probe`, `router_regression`): **PASS,
  unregressed** (all exit 0, re-run at this commit) — 002Y changes no harness
  rule or routing code.
- **New `prefix_002w.py`** (re-run at this commit): DETERMINISM **PASS** (board
  matches the pinned manifest exactly), GOVERNED GOAL **FAIL — exit 1** (the
  documented reproduction gap; U18 6/8, open `U18.7`/`U18.8`, `U18.8` at the
  blocking site (3.000, 71.600); by design and by the brief).

## 9. Decision required

The margin cannot host `U18` 8/8 **and** the `BAT_SENSE` current path **and** the
≥1.20 mm trunk on B.Cu, and the two roles that collide are both current-carrying.
This is the choice D-268 and 002W/002X already framed, now on ground that
reproduces:

1. **Accept that the western margin is oversubscribed at current-carrying roles**
   and take a protection-architecture decision — the F.Cu via-array bridge or the
   reservation-dependent long B.Cu route (2.29× resistance, quantified in the
   D-267 audit). This is an **OWNER** call.
2. **Or authorise a placement change** to widen the western margin (TP17/C58/
   placement are currently locked). Also an OWNER call.

Neither is taken here. 002Y's job was to make the board reproducible and the
blocker honest, and both are done.

## 10. What was NOT done

D9, U18, R75, R76..R83, Q3, the shunt, the protection FETs, **TP17 and C58** all
frozen. No placement searched, no placement ECO. No signal track and no signal
via written to the authoritative board. No inner-layer trunk, no high-current
via, no long route accepted by default. No netclass, width, clearance, layer,
via, annular or hole rule changed — 002Y adds a pinned regression and a manifest
and changes **no** routing code. D-249, D-264, D-266, D-267, D-269, D-270
untouched. **U19 NOT SEARCHED. Phase A NOT passed. Phase B NOT run. Converter
routing NOT started.** B-34 remains open.
