---
tags: [hardware, enclosure, mechanical, industrial-design, v5]
status: cto-locked-target
supersedes: "[[17 - Enclosure Field Slate v4]] (envelope), [[15 - Enclosure Field Slate v3]] §2"
---

# AQROOT Enclosure — "Field Slate" v5

**This is the authoritative source for AQROOT mechanical dimensions.** It
supersedes the envelope in [[17 - Enclosure Field Slate v4]] and, through it,
§2 of [[15 - Enclosure Field Slate v3]]. Everything else in v3 — concept,
materials and manufacturing staging, RF crown, rear NFC target, the 7-button
control set, the side antenna holder, and the antenna zoning that
[[12 - RF and Antenna Plan v0.1]] and [[14 - RootProbe Interface v0.1]] depend
on — **remains in force unchanged**.

---

## 1. Dimension authority table

This table exists because an enclosure external dimension was previously used
as though it were a PCB dimension. Each row names its own source. **Never
quote one of these rows as another.**

<!-- machine-readable: tools/check_mechanical_consistency.py parses these keys -->

```
PCB_OUTLINE_MM: 155 x 74
PCB_THICKNESS_MM: 1.6
ENCLOSURE_EXTERNAL_MM: 160 x 80 x 23
INTERNAL_CAVITY_MM: not published
PCB_TO_WALL_CLEARANCE_MM: not published
WALL_THICKNESS_MM: not published
PCB_FIT_STATUS: UNVERIFIED
```

| | value | source of authority |
|---|---|---|
| **A. Current PCB outline** | **155 × 74 × 1.6 mm** | **measured** from Edge.Cuts and confirmed in the exported Gerber |
| **B. Product external enclosure** | **160 × 80 × 23 mm** | **CTO lock** |
| **C. Internal usable cavity** | **TBD** | CAD |
| **D. Required PCB-to-wall clearance** | **TBD** | CAD |
| **E. Wall thickness** | **TBD** | CAD / material / process |
| **F. PCB fit status** | **UNVERIFIED** | requires C, D and E |

Superseded, kept only so the history reads correctly:

| dimension | status |
|---|---|
| 130 × 70 × 23.5 mm (v4) | **SUPERSEDED** |
| 122 × 61 × 23.5 mm (v3) | superseded by v4, remains superseded |
| ~75 × 45 × 16 mm (original pocket-tool concept) | superseded by v3, remains superseded |

---

## 2. Current PCB vs the new enclosure — do not claim fit

| axis | PCB | enclosure external | nominal difference |
|---|---:|---:|---:|
| length | 155 mm | 160 mm | **+5 mm total** |
| width | 74 mm | 80 mm | **+6 mm total** |
| height | 1.6 mm | 23 mm | — |

**This does not prove internal fit, and must not be recorded as if it did.**
That +5 mm and +6 mm is the *entire* budget for two walls, bosses, ribs,
tolerances, button mechanisms and connector clearances on each axis — roughly
2.5 mm and 3.0 mm per side before anything else is subtracted. A 2 mm wall
alone consumes most of it.

**Authoritative status: `CURRENT PCB FIT IN 160 × 80 SHELL — CAD VERIFICATION
REQUIRED`.** It does not become PASS until an internal cavity is published and
measured against the board.

`tools/check_mechanical_consistency.py` enforces this: it reads the real
Edge.Cuts extent and this table, and it reports fit as **UNKNOWN** until
`INTERNAL_CAVITY_MM` and `PCB_TO_WALL_CLEARANCE_MM` exist. It will not compute
a fit from external dimensions.

---

## 3. Why the numbers drifted — chronology from git

Traced through the repository rather than reconstructed from memory.

| date | commit | event |
|---|---|---|
| 2026-07-07 | `ae89dac` | initial docs carry the **~75 × 45 × 16 mm** pocket-tool concept |
| 2026-07-20 | `f36dcc5` | **122 × 61 × 23.5 mm** first appears, in the RF and Antenna Plan |
| 2026-07-21 | `9b828ad` | Field Slate **v3** formalises 122 × 61 × 23.5 mm and states the intent: *"the envelope … must drive at least ONE PCB revision"*, *"the design target that the first PCB is routed against"* |
| 2026-07-27 | `ba8f71f` | the Beta PCB file is created — **no Edge.Cuts yet** |
| 2026-08-10 | `0280924` | first Edge.Cuts, at **72.0 × 148.0 mm**, in a commit titled *"establish **enclosure-driven** PCB floorplan"* |
| 2026-08-10 | `badff22` | **74.0 × 152.0 mm** — *"reconcile PCB floorplan to real footprint geometry"* |
| 2026-08-10 | `8f48aa5` | **74.0 × 155.0 mm** — *"finalize anchor floorplan geometry"*; unchanged ever since |
| 2026-08-15 | untracked | the local mechanical audit measures the board and states the conflict against v3 — but it is **untracked**, so it never reaches the documents |
| 2026-08-20 | `2c73845` | envelope raised to **130 × 70 × 23.5 mm** (v4); still short of the board |
| 2026-08-20 | this pass | envelope raised to **160 × 80 × 23 mm** (v5) |

### Root cause

**The reconciliation step v3 called for was never performed, and nothing in the
repository could detect that.** Specifically:

1. **The PCB was never routed against the envelope.** v3 required the envelope
   to drive at least one PCB revision. When the floorplan was created three
   weeks later it was driven by *component geometry* — the WROOM module, two
   radio modules, a 50-pin display FPC, USB-C, microSD and eight buttons — and
   landed at 72 × 148 mm immediately, already 26 mm longer than the 122 mm
   target. The commit is titled "enclosure-driven", which is what made the gap
   easy to miss: the title asserts the very reconciliation that did not happen.
2. **An external body dimension was treated as an available area.** 122 × 61
   was always an *outside* measurement. No internal cavity dimension has ever
   existed in this repository — that is verified, not assumed — so there was
   never a number the floorplan could have been checked against.
3. **The board grew after the target was set, and nothing re-checked it.** The
   outline moved 72 × 148 → 74 × 152 → 74 × 155 in a single day, purely to
   accommodate real footprints. The enclosure documents were not revisited.

Two things it was **not**:

* **Not an axis or portrait/landscape confusion.** Both figures are portrait
  and the board is larger on *both* axes: 74 > 61 and 155 > 122. Swapping
  axes explains nothing.
* **Not a false claim of fit.** Searching every tracked document finds no
  statement that the PCB fits any enclosure. The failure was silence, not a
  wrong assertion — which is precisely why an automated check is now in place.

---

## 4. Current Beta-DM PCB — frozen

The current board proves the electronics. It is **not** resized, and none of
the following may move for enclosure reasons: `J5`, USB-C, microSD, the
buttons, the antenna connector placement, or Edge.Cuts.

Mechanical optimisation belongs to the later product / Full-Beta revision.

---

## 5. Locked product external layout

Carried forward unchanged from v4.

**Top** — external 433 MHz antenna connector; exact position remains RF/DFM
dependent; it must not compromise the internal 433 / 915 / WiFi antenna
keepouts; the IR aperture stays associated with the crown.

**Left side** — antenna storage / holder channel for the stowed whip. Keep this
side substantially free. **No community GPIO connector here.**

**Right side, upper/middle** — community expansion / `J5`, preferably recessed
and/or keyed. The electrical **26-pin F4 `J5` map is unchanged**; nothing is
repinned.

**Right side, lower** — Volume +, Volume −, Power. This cluster **may move
farther down toward the lower third** where that looks cleaner, avoids
crowding, improves ergonomics or clears `J5`. **Clean industrial design
outranks any fixed vertical coordinate.**

**Bottom** — microSD toward bottom-left, USB-C near bottom-centre; exact
positions driven by the next PCB revision and enclosure CAD.

**Rear** — clean metal-free NFC target, branding, and **no stored antenna
across the NFC target**. The holder stays on the left side.

The next Full-Beta revision must place the `U61` / `J5` cluster around the
right-side exit **before routing begins**.

---

## 6. Reference

* [[17 - Enclosure Field Slate v4]] — envelope superseded by this document
* [[15 - Enclosure Field Slate v3]] — everything except §2 dimensions
* [[12 - RF and Antenna Plan v0.1]] — antenna zoning depends on v3 §4–§7
* `tools/check_mechanical_consistency.py` — the automated guard
* `hardware/beta-dm/BETA-DM-FINAL-DFM.md` — where the 155 × 74 mm figure is
  measured and cross-checked against the exported Gerber
