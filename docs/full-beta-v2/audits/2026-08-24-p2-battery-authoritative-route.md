# FBV2-P2-002C — Battery path-role rules and the first authoritative routing attempt

**Date:** 2026-08-24 · **Task:** FBV2-P2-002C — resolve battery path-role rules and land the first
DRC-clean authoritative routing
**Repository HEAD at start:** `a52977e`
**Result: FBV2-P2-002C = FAIL. PHASE A DID NOT COMPLETE, SO PHASE B WAS NOT RUN.**
**The authoritative PCB is byte-identical to `a52977e`: zero tracks, zero signal vias.**

> **First unresolved connection: `LTC_GATE` `Q2.2 → TP17.1`.** Twenty-seven connections routed and
> coexisted cleanly on one scratch board — the whole high-current battery path, both R75 Kelvin
> branches, the U11.2 flared escape, the fuel-gauge taps, TP15, TP16, TP20, TP34 and the LTC gate
> drive — and then the LTC test-point stub could not be reached on either layer at any legal width.
> §19 is unambiguous about what happens next, so **nothing was written to the authoritative board.**
>
> **What this task did settle is the ruling and the arithmetic.** The path-role construction works,
> the U11.2 escape is measured rather than assumed, and B-34 now has a number taken from real
> copper instead of an estimate — and that number is **worse than the estimate**, which is exactly
> the sort of thing that should not be found late.

---

## 1. Preflight

| check | result |
|---|---|
| HEAD / `origin/master` | both `a52977e` |
| Tag `beta-v2-p2-entry-pass` | `faa0c91`, untouched |
| Authoritative tracks / signal vias | **0 / 0** |
| In1 plane | 1 zone, 1 island, net GND |
| DRC / ERC baselines | **1** (`MK1`, D-227) + 499 unconnected · **0 errors / 27 warnings** |
| `router_regression` / `p1_regression` / `dru_probe` / `netclass_probe` | **PASS / PASS / PASS / PASS** |

---

## 2. D-249 — width is a path role (§2 – §7)

D-245's **intent** stands; its **whole-net implementation** is superseded. The mechanism:

* the **1.20 mm trunk floor applies to the entire net** by default;
* it is relaxed **only inside a named rule area** that bounds one approved branch, through
  `enclosedByArea()`, which requires the **whole track** to lie inside;
* the area rules sit in a new **section 10b at the very end of `.kicad_dru`**, because §9 of that
  file already establishes that the pad-escape necking and land-pattern blocks must come last to
  beat the section-5 rail widths — and these must in turn beat *those*, being the most specific
  statement on the board. Placed in section 5b they were silently overridden by
  *"Pad-escape necking – width, fine-pitch power packages"*, which is exactly the failure §9 warns
  about;
* within 10b the rules run **widest first, narrowest last**, so where areas overlap the lower floor
  governs rather than producing a false violation.

**This was proved to work**: a 0.15 mm fuel-gauge tap and a 1.50 mm trunk coexist on the same net
with no width violation, and a branch leaving its area is measured against the trunk floor.

### 2.1 The ruled widths, and one the brief did not anticipate

| pad / branch | role | ruled | achieved | note |
|---|---|---|---|---|
| `BAT_PROTECTED_P` trunk `R75.2 → D9.1 → U11.2` | high current | 1.50 / 1.20 | **1.50 mm** | §4 |
| `U11.2` | **high-current** fine-pitch endpoint | 0.20 mm | **0.20 mm** | §6 — no 0.19 mm exception needed |
| `U18.8` (LTC4368 **VOUT**) | sense | 0.20 mm | **0.20 mm** | §5 |
| `U18.9` (LTC4368 **SENSE**) | Kelvin | 0.20 mm | **0.20 mm** | §3 |
| `U14.2` / `U14.3` (MAX17048) | fuel-gauge tap | 0.20 mm | **0.15 mm** | **DEVIATION — see §5** |
| `TP15` | test branch | 0.20 mm | **0.20 mm** | §5 |
| **`U18.1` (LTC4368 `VIN`)** | **supply tap — NOT IN §5** | — | **0.20 mm** | **NEW, see §6** |

---

## 3. `U11.2` — the BQ25185 BAT pin (§6)

**A. TI land geometry, re-verified from the datasheet fetched today.** The DLH0010A recommended
land is **10 × (0.5 mm × 0.2 mm) pads on 0.4 mm pitch**. The KiCad footprint uses the same 0.20 mm
pad width and the same 0.4 mm pitch with a longer 0.75 mm toe. **The pad itself is 0.20 mm wide, so
0.20 mm is the widest copper that can ever leave it — the package is the bottleneck, not the rule.**

**B. JLCPCB capability, fetched live from the vendor page today.** Minimum track width / spacing on
a **1 oz multilayer** board is **0.09 / 0.09 mm**; track width tolerance ±20 %. **0.20 mm is 2.2×
the minimum. Nothing here is fab-limited, and the 0.19 mm exception §6 authorised is not needed.**

**C. Every legal launch orientation was tried.** Exact segment-to-shape geometry (no sampling
margin) gives U11.2 a widest legal escape of **exactly 0.200 mm** — the earlier 0.195 mm figure was
an artefact of the router's own conservatism, now removed.

### The measured escape

| segment | width | length |
|---|---|---|
| neck at the pad | **0.20 mm** | **0.575 mm** |
| flare | 0.30 mm | 0.100 mm |
| flare | 0.40 mm | 0.100 mm |
| flare | 0.60 mm | 0.262 mm |
| flare | 0.80 mm | 3.480 mm |
| flare | 1.00 mm | 0.221 mm |
| flare | 1.20 mm | 0.341 mm |
| **total escape** | | **5.079 mm**, then 1.50 mm trunk |

Bounding box 3.28 × 2.80 mm. **Zero vias, no thermal relief.** Resistance **≈ 4.3 mΩ** — at 1.5 A
that is 6.4 mV and 9.7 mW. Current density in the neck is **214 A/mm²**; the neck is 0.575 mm long
and terminates in the pad at one end and widening copper at the other, so it is not a
steady-state-isolated conductor.

### The one part of §6 that is NOT met, stated plainly

§6 caps the neck at **1.00 mm**. The **0.20 mm neck is 0.575 mm and complies.** But the copper
*below the 1.20 mm trunk floor* runs **4.738 mm**, and if §6's "sub-1.20 mm neck" meant that, the
limit is exceeded.

**It cannot be met.** Measured on the real board, the nearest point to `U11.2` that both admits a
1.20 mm track **and is reachable from the rest of the net** is **2.511 mm** away; for 1.50 mm it is
**3.346 mm**. A ≤ 1.00 mm sub-trunk escape does not exist at this pad in this placement. **Flagged
for ratification rather than routed around.**

---

## 4. Phase A — what routed, on one scratch board (§11 – §13)

Every connection: routed → rule areas regenerated → `.kicad_dru` rewritten → In1 refilled → saved →
project-context DRC → diffed against baseline → ratsnest checked. **Any new violation of any class
reverts that connection.** Baseline `{solder_mask_bridge: 1, unconnected_items: 499}`, ratsnest 781.

| role | connection | length | width | layer | vias |
|---|---|---|---|---|---|
| TRUNK | `BAT_PROTECTED_P` `R75.2 → D9.1` | 20.589 mm | **1.50** | B.Cu | 0 |
| TRUNK | `BAT_PROTECTED_P` `U11.2 → D9.1` | 73.937 mm | **1.50** + escape | B.Cu | 0 |
| TAP | `BAT_RAW` `C59.1 → R77.1` | 44.371 mm | 0.30 | B.Cu | 0 |
| SENSE | `BAT_PROTECTED_P` `TP15.1 → U14.2` | 12.068 mm | **0.15** | B.Cu | 0 |
| SENSE | `BAT_PROTECTED_P` `TP15.1 → D9.1` | 14.810 mm | 0.20 | B.Cu | 0 |
| TRUNK | `BAT_CONNECTOR_P` `J4.1 → F1.1` | 13.471 mm | **1.00** | B.Cu | 0 |
| TRUNK | `BAT_RAW` `F1.2 → Q2.8 → Q2.7` | 14.565 mm | **1.00** | B.Cu | 0 |
| TRUNK | `BAT_MID` `Q2.5 → Q2.6 → Q3.8 → Q3.7` | 24.582 mm | 0.80 / 1.00 | B.Cu | 0 |
| TRUNK | `BAT_SENSE` `Q3.5 → Q3.6` | 4.900 mm | 0.80 | B.Cu | 0 |
| TRUNK | `BAT_SENSE` `Q3.6 → R75.1` | 13.783 mm | 0.80 | **F.Cu** | **2** |
| TAP | `BAT_PROTECTED_P` `C58.1 → node` | 19.998 mm | 0.80 | B.Cu | 0 |
| TAP | `BAT_PROTECTED_P` `C25.1 → node` | 8.835 mm | 1.00 | B.Cu | 0 |
| SENSE | `BAT_SENSE` `U18.9 → R75.1` (**Kelvin**) | **7.327 mm** | 0.20 | B.Cu | 0 |
| SENSE | `BAT_PROTECTED_P` `U18.8 → R75.2` (**Kelvin**) | **14.588 mm** | 0.20 | B.Cu | 0 |
| TAP | `BAT_RAW` `R80.1 → Q2.7`, `D12.1 → R77.1`, `TP16.1 → Q2.7`, `R86.2`, `R89.1` | 29.750 / 16.540 / 11.566 / 18.873 / 8.480 mm | 0.40 – 0.60 | B.Cu | 0 |
| SENSE | `BAT_RAW` `U18.1 → node` (**VIN**) | 5.176 mm | 0.20 | B.Cu | 0 |
| TAP | `BAT_SENSE` `TP20.1 → node` | 12.639 mm | 0.60 | **F.Cu** | **2** |
| SIG | `LTC_GATE` `Q3.2 → Q3.4 → Q2.2 → Q2.4` | 24.546 mm | 0.25 | B.Cu | 0 |

**27 routed, 5 more picked up on the way (including TP34), ratsnest 781 → 749. Zero new DRC
violations of any class at every step. Zero shorts, zero crossings, zero dangling ends.**

### Where it stopped

**`LTC_GATE` `Q2.2 → TP17.1`.** `TP17.1` at (14.500, 48.250) escapes freely at 0.895 mm and `Q2.2`
at 0.350 mm, so neither pad is the problem — the corridor between them is gone by the time the
LTC gate network is reached, on B.Cu **and** on F.Cu, down to the board's 0.15 mm minimum. The
fallback ladder (B.Cu pad-to-pad → B.Cu pad-to-node → F.Cu hop → F.Cu hop to node) was exhausted.

**The dead-cell / recovery network (§17) was never reached and is NOT routed.**

---

## 5. The `U14` deviation, and the arithmetic behind it

§5 locked `U14.2` / `U14.3` at **0.20 mm minimum**. **0.20 mm does not physically exist there.**

`U14` sits **1.245 mm from the west board edge with its pin row facing that edge.** The only escape
is the strip between the edge and the pad row. Copper must be ≥ 0.500 mm from the edge, and
≥ 0.200 mm from pads whose west edge is at x = 0.895. A track of width *w* in that strip needs its
centre at `x ≥ 0.500 + w/2` **and** `x ≤ 0.695 − w/2`, which has a solution only for **w ≤ 0.195 mm**.

**A 0.20 mm track misses by 5 microns.** It routes at **0.15 mm** — the board's own
`min_track_width`, 1.7× JLCPCB's multilayer minimum — over 12.068 mm. The MAX17048 sense input
draws nanoamps. **Routed at 0.15 mm and flagged for ratification.**

A second correction fed into this: the router now insets the board outline by **half the Edge.Cuts
stroke (25 µm)**, because copper-to-edge clearance is measured to the line, not to the outside of
the stroke. That is what moved `U14.2`'s widest escape from 0.300 mm to **0.240 mm**, and it caught
a 0.475 mm edge violation that would otherwise have been committed.

---

## 6. `U18.1` — a case §5 did not list

`U18.1` is the LTC4368 **`VIN`** pin. Its widest legal escape is **0.250 mm**, so like `U18.8` and
`U18.9` it cannot take the `BAT_MAIN` 0.60 mm floor.

**It is not a current path.** The symbol library records the part as driving *"back-to-back external
N-channel MOSFETs"*: the pack current flows through `Q2`/`Q3`, and `VIN`, `VOUT` and `SENSE` are
microamp inputs. It was therefore routed at **0.20 mm inside `BAT_RAW_TAP_U18`**, on the same
§2 path-role reasoning the CTO applied to pins 8 and 9. **Recorded here because §5 did not
enumerate it.**

---

## 7. B-34, from real copper (§23)

1 oz outer = 0.491 mΩ/square; a 0.40 mm through via in 1.6 mm with 25 µm plating ≈ 0.88 mΩ.

| segment | length | width | copper |
|---|---|---|---|
| `BAT_CONNECTOR_P` `J4 → F1` | 13.471 mm | 1.00 | 6.61 mΩ |
| `BAT_RAW` `F1 → Q2` | 14.565 mm | 1.00 | 7.15 mΩ |
| `BAT_MID` `Q2 → Q3` | 24.582 mm | 0.80 / 1.00 | 14.46 mΩ |
| `BAT_SENSE` `Q3 → R75` | 18.683 mm | 0.80 | 11.47 mΩ + **1.76 mΩ (2 vias)** |
| `BAT_PROTECTED_P` `R75 → U11` | 94.526 mm | 1.50 + escape | **33.58 mΩ** |
| **routed copper total** | **165.8 mm** | | **≈ 75.0 mΩ** |

| element | value |
|---|---|
| `F1` fuse | ≈ 25 mΩ |
| `Q2` + `Q3` | ≈ 46 mΩ |
| BQ25185 BATFET | **115 mΩ** |
| **TOTAL** | **≈ 261 mΩ** |
| **@ 1.50 A** | **≈ 392 mV, ≈ 588 mW** |
| **@ 1.75 A** | **≈ 457 mV, ≈ 800 mW** |

**This is worse than the FBV2-P2-002A estimate of ≈ 355 mV / 532 mW**, and the reason is copper:
the estimate assumed **50.6 mΩ**; the real routed path is **75.0 mΩ**. The trunk is at its ruled
1.50 mm — the extra resistance is in the BAT_MAIN segments, where the corridors forced 0.80 mm on
`BAT_MID` and `BAT_SENSE` rather than the 1.00 mm class target.

**B-34: OPEN — PHYSICAL VALIDATION REQUIRED.** Nothing here is unsafe, and none of it is committed.

---

## 8. PR-9 and PR-10 (§9)

**PR-10 — the 1.50 mm trunk is KEPT**, as ruled. The old claim of an 11.7 mΩ saving is withdrawn;
the honest figure from this route is that the trunk contributes **33.58 mΩ over 94.5 mm**, and at
the 1.00 mm class target the same path would be ≈ 46 mΩ. **The gain is ≈ 12 mΩ, not the ≈ 6 mΩ
FBV2-P2-002B predicted from the shorter 85.3 mm estimate** — because the route turned out longer,
which cuts both ways.

**PR-9 — `R86 → R89` was not routed as a trunk at all.** Both resistors are divider tops on
megohm-class parts, so they were reclassified as microamp taps and routed at 0.40–0.60 mm in
18.873 + 8.480 mm rather than a 45 mm 1.00 mm detour. That is a better outcome on every axis.

---

## 9. Where the enforcement is still weak, stated rather than glossed

§7 requires that the construction make it **impossible** for a long high-current run to masquerade
as a branch. **It does not fully achieve that yet.** The bounded areas are generated from each
routed branch's own bounding box, and a long branch produces a large box:

| area | size | floor |
|---|---|---|
| `BAT_PROT_ESCAPE_U11` | 3.98 × 3.70 mm | 0.20 mm |
| `BAT_SENSE_KELVIN` | 1.95 × 3.84 mm | 0.20 mm |
| `BAT_PROT_TAP_U18` | 2.50 × 10.31 mm | 0.20 mm |
| `BAT_PROT_TAP_U14` | 11.93 × 13.35 mm | 0.15 mm |
| `BAT_RAW_TAP_U18` | 9.25 × 50.15 mm | 0.20 mm |
| `BAT_STUB_1` (C58 tap) | **67.23 × 22.95 mm** | 0.80 mm |

The first three are tight and do what §7 asks. **The last three are not**, and a 67 × 23 mm area
with a 0.80 mm floor on `BAT_PROTECTED_P` is a real hole in the trunk rule. The fix is a corridor
built from the route's own centre-line rather than its bounding box; that is a router change, not a
rule change, and it is carried as **PR-11**.

---

## 10. Exit state (§19, §20)

| check | result |
|---|---|
| `aqroot-Beta-v2.kicad_pcb` vs `a52977e` | **byte-identical** |
| Authoritative tracks / signal vias | **0 / 0** |
| `.kicad_dru` | **unchanged** — the D-249 block references rule areas that exist only on the scratch board, so committing it would make `dru_probe` fail |
| Authoritative placement, incl. TP34 | **unchanged** |
| DRC / ERC | **1** (`MK1`, not suppressed) + 499 · **0 errors / 27 warnings** |
| `router_regression` | **PASS** — pins re-measured after the exact-distance and edge-inset fixes |
| `p1_regression` / `dru_probe` / `netclass_probe` / `fork_equivalence` | **PASS** |
| Frozen trees | Beta-DM, `hardware/beta/`, `hardware/beta/mechanical/` untouched |
| **PM-2** | **PLACEMENT CORRECTED; CLOSURE STILL PENDING** — §22's conditions require a DRC-clean routed block, and there isn't one |

---

## 11. Carried forward

| # | item |
|---|---|
| **PR-12** | **Phase A stops at `LTC_GATE` `Q2.2 → TP17.1`.** The LTC gate-drive net and the entire dead-cell / recovery network remain unrouted. The congestion is in the left margin between `Q2`/`Q3` and the 0603 divider wall at x = 8.0 / 9.65 |
| **PR-11** | **Bounded areas must be corridors, not bounding boxes** — §9 above |
| **PR-13** | **RATIFY OR REJECT the `U14.2` / `U14.3` 0.15 mm tap.** 0.20 mm is geometrically impossible by 5 µm |
| **PR-14** | **RATIFY the `U11.2` sub-1.20 mm escape length of 4.738 mm.** §6 caps it at 1.00 mm; the nearest reachable 1.20 mm-capable point is 2.511 mm away, so ≤ 1.00 mm does not exist |
| **PR-15** | **`U18.1` was classified as a microamp supply tap** on §2's reasoning. §5 did not list it |
| **PR-16** | **`C59` (1 µF bulk on `BAT_RAW`) needs 44.4 mm of 0.30 mm copper** to reach its net. At that length it is not a decoupling capacitor in any useful sense — a placement finding, not a routing one |
| **B-34** | **OPEN.** ≈ 392 mV / 588 mW at 1.5 A from real copper — worse than the previous estimate |
| **PM-2** | Placement corrected; closure pending |
| **PR-4** | Ground pours and perimeter stitching remain the last step of FBV2-P2 |

---

## 12. What was NOT done

**No copper was committed** — the authoritative board is byte-identical to `a52977e`. **No
`.kicad_dru` change was committed.** **No netclass changed.** **No component moved** — TP34's flip
to B.Cu was validated on scratch and, because Phase B did not run, **was not applied**. **PM-2
untouched.** **The `MK1` artefact was not suppressed.** **No converters, USB, NFC, SPI or I²C were
routed.** **No percentage moved: PCB routing stays 0 %, overall stays 74 %.**
