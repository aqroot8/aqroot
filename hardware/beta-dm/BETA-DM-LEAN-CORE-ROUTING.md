# AQROOT Beta DM — Lean-Core scratch routing study

**SCRATCH ONLY for routing.** No copper was landed. The only real-board change
in this pass is the `U15` / `U16` DNP attribute pair, authorised by §18 after
their dependency audit passed — an object-level PCB diff shows
`pads 0, segments 0, vias 0, zones 0, Edge.Cuts unchanged`. `hardware/beta/`
has an empty diff. No pours, no component moves, no pin renumbered, no area
reclaimed, **no new rule exception**.

Started over from the current real board. The prior C16 release architecture
was **not** inherited.

## Result in one paragraph

The Lean-Core problem is six lines. Five of them have a proven route. The
`BQ25185_STAT1` half of the power-tree work is **fully verified** — released
nets re-landed, KiCad DRC 0 errors, DFM pass. The four XGPIO all join
simultaneously on a **10-object, 6.544 mm** release, with both released nets
re-landing, but that solve does **not separate**, so it is a proven topology
rather than a landable candidate. `BQ25185_STAT2` **does not close**: it and
the battery-rail escape want the same lane out of `U11`'s left column, and with
correct via modelling only one of them can have it.

**`SX1262_RXEN` was not released and is not needed.** `FAST_IO_GPIO43_HDR` was
not touched.

---

## 1. Two router-model corrections found and fixed this pass

Both were making the board look more sealed than it is, and both were caught by
KiCad rather than by the raster.

**A. The raster hardcoded a 0.30 mm via radius**, i.e. modelled every net as
using a 0.60 mm via. `BAT_PROTECTED_P` is BAT_MAIN and its class via is
**0.80 mm**, so its escape was under-stamped by 0.10 mm and KiCad reported a
real 0.1400 mm clearance violation against `U11.1`. `route.Grid.build` now
takes the actual `via_pad` / `via_drill`, and the hole-to-hole margin uses the
real drill radius instead of a fixed 0.15 mm.

**B. The DRU's courtyard clearance relaxation was being ignored.** The board
already ships:

```
(rule "Pad-escape necking - clearance, fine-pitch power packages"
    (constraint clearance (min 0.20mm))
    (condition "(A.intersectsCourtyard('U11') || ...) &&
                (B.intersectsCourtyard('U11') || ...)"))
```

Inside those six courtyards, two objects that both touch the courtyard need
only **0.20 mm**, not the netclass figure. The raster was applying BAT_MAIN's
0.30 mm there — over-constraining the one region where a 0.400 mm-pitch escape
has to happen. This is the rule the board already ships; using it is **not** a
new exception.

**Implementation limit, stated plainly:** KiCad's condition is per **object**
("does this track intersect the courtyard?"). A raster can only express a
**region**. The mask is therefore grown by a heuristic margin, and **KiCad DRC
is the acceptance test, not the heuristic.** Two consequences were measured:

* a 1.5 mm grow closed all four power-tree commodities but produced **9 DRC
  errors**, because it granted 0.20 mm to a via sitting 0.8 mm outside the
  courtyard;
* **via placement is now never relaxed.** The necking rule exists so a
  fine-pitch pad can be escaped by a narrow *track*; it is not a licence to
  drop a 0.80 mm power via into the gap. Seven of those nine errors were
  exactly that.

With vias held strict, the honest answer returns — see §3.

## 2. The four XGPIO

### Selection re-validated

The ranking in [BETA-DM-LEAN-XGPIO-SELECTION.md](BETA-DM-LEAN-XGPIO-SELECTION.md)
was measured against the board alone and is unchanged by the scope cut. It is
re-validated, not re-derived: `XGPIO9`–`XGPIO13` remain disqualified (198-cell
pockets walled by `PAD U3` and `SX1262_RXEN`, with no ordinary release of any
size opening them), `XGPIO0`–`XGPIO3` remain 8× more expensive, and
`XGPIO4`–`XGPIO7` remain the best joint set with `XGPIO8` as the alternate.
**No evidence was found for changing the set. Retained: XGPIO4, 5, 6, 7.**

Removing external I2C and the accessory rail only *reduces* contention, so the
prior selection cannot become worse.

### Release ladder, cheapest scope first

| tier | objects | length | XGPIO reachable |
|---|---:|---:|---:|
| T0 nothing | 0 | 0 mm | **0 / 4** |
| T1 deferred-function copper (10 `XGPIO*_HDR`, ext-I2C, `ACC_3V3_SW`, `Net-(U15-CT)`) | 243 | 203.662 mm | **0 / 4** |
| T2 + ordinary local signals | 271 | 348.793 mm | **0 / 4** |
| T3 + `FAST_IO_GPIO43_HDR` / `WAKE_ATTN_N_HDR` | 336 | 430.301 mm | **4 / 4** |
| T4 + the `SX1262_RXEN` pad escape | 339 | 439.026 mm | 4 / 4 — **no change** |

Two rulings fall straight out:

* **`SX1262_RXEN` is not needed.** T4 adds nothing T3 did not already give.
  §12 is satisfied by not spending it.
* **The `WAKE_ATTN_N_HDR` family is load-bearing and `FAST_IO_GPIO43_HDR` is
  not.** Dropping `FAST_IO_GPIO43_HDR` from the release keeps 4/4, so it is
  left untouched, as §2 requires.

### The release, minimised

Shrunk against all four targets at once, then object by object:

> **The reachability minimum is ONE object** — the 0.60/0.30
> `WAKE_ATTN_N_HDR` via at **(27.991, 14.152)**, 0.000 mm of track.

Every other net in the pool — including all the deferred-function copper — was
dropped from the release with 4/4 still reaching.

But **reachability is not simultaneity**: with that one via released, only one
XGPIO can actually take the corridor. The working release adds the
`FAST_IO_U0TXD_ROOTPROBE_CS` header-band escape:

| net | objects | length | must re-land? |
|---|---:|---:|---|
| `WAKE_ATTN_N_HDR` | 1 (a via) | 0.000 mm | **yes** |
| `FAST_IO_U0TXD_ROOTPROBE_CS` | 9 | 6.544 mm | **yes** |
| **total** | **10** | **6.544 mm** | |

Both are carried as simultaneous commodities, so §15's "all released original
nets re-landed" is enforced by construction rather than checked afterwards.

> A first attempt released every `FAST_IO_U0TXD_ROOTPROBE_CS` object that
> *intersected* the routing window — which took out the 19.15 mm In2 spine
> running from y = 18.6 to y = 37.75, whose far end lies **outside** the
> routable window. The net could then never re-land: that was a tool artifact,
> not a board fact. Scoping the release to the header band (y ≤ 20) cut it from
> 25.694 mm to 6.544 mm and the re-land closes.

### Result

Negotiated congestion, 6 commodities, grid 1081 × 561 at 0.05 mm:

| commodity | segments | vias | length | joined |
|---|---:|---:|---:|---|
| `XGPIO4` | 84 | 1 | **30.464 mm** | yes |
| `XGPIO5` | 102 | 5 | **31.493 mm** | yes |
| `XGPIO6` | 101 | 3 | **31.454 mm** | yes |
| `XGPIO7` | 75 | 4 | **29.707 mm** | yes |
| `WAKE_ATTN_N_HDR` re-land | 0 | 1 | via only | yes |
| `FAST_IO_U0TXD_ROOTPROBE_CS` re-land | 22 | 1 | **7.360 mm** | yes |

**`unjoined 0` — all six, and it holds at every iteration. But NOT CONVERGED.**

| iter | pfac | conflicts | unjoined |
|---:|---:|---:|---:|
| 0 | 0.60 | 1 710 | **0** |
| 3 | 3.50 | 1 842 | **0** |
| 6 | 20.41 | 1 743 | **0** |
| 7 | 36.73 | 1 530 | **0** |
| 9 | 119.02 | 1 436 | **0** |
| 12 | 694.10 | 1 464 | **0** |
| 19 | 42 494 | 1 467 | **0** |
| 21 | 137 681 | 1 514 | **0** |
| 23 | 446 086 | 1 457 | **0** |
| 25 | **1 445 320** | 1 542 | **0** |

A full **26-iteration** run was carried to completion. Residual conflicts sit in
a **1 436 – 1 842** band from the first iteration to the last while the
present-cost factor is raised from 0.60 to **1 445 320 — a factor of 2.4
million**. `unjoined` is 0 at every single iteration.

That is as conclusive as this method gets: **search budget is not the missing
ingredient.** The final iteration's routes are
`XGPIO4` 34.336 mm / `XGPIO5` 32.942 mm / `XGPIO6` 31.665 mm /
`XGPIO7` 31.367 mm, `WAKE_ATTN_N_HDR` one via, `FAST_IO_U0TXD_ROOTPROBE_CS`
7.277 mm — the same topology, never separated.

Joined but not separated, so it is not DRC-clean and it is **not a landable
candidate**. It was deliberately **not** written to a scratch board — with
~1 450 residual conflicts it would report thousands of clearance errors, which
would be a number, not a result.

The `WAKE_ATTN_N_HDR` re-land is worth noting: the whole restoration is **one
via**, put back at a different site. §13's conditions are met — `R66`
functionality intact, the `J5.13` WAKE pin re-lands, and the net returns to its
intended single connected path.

Sequential routing with mutual obstacles was run as a control over 12 orders;
best was **open 3**. Whichever XGPIO is placed first walls the others. That is
why negotiation is the right tool here, and why its plateau is meaningful.

## 3. `BQ25185_STAT1` / `STAT2`

`U11` is a `DLH0010A WSON-10-1EP`, **0.400 mm pitch**, exposed GND pad
0.900 × 1.500 at (65.000, 67.000):

```
left column  x = 63.900              right column x = 66.100
  U11.1 y 66.200  BQ25185_SYS          U11.10 y 66.200  USB_VBUS_CHG
  U11.2 y 66.600  BAT_PROTECTED_P      U11.9  y 66.600  STAT1
  U11.3 y 67.000  STAT2                U11.8  y 67.000  ISET
  U11.4 y 67.400  GND                  U11.7  y 67.400  ILIM_VSET
  U11.5 y 67.800  GND                  U11.6  y 67.800  Net-(U11-TS_MR)
```

Between-pin escape needs 0.20 + 0.20 + 0.20 = 0.600 mm against a 0.400 mm
pitch, and the exposed pad blocks inboard, so **every escape is outboard**.

### The landable candidate — verified

Release **7 objects, 8.500 mm**: the in-window `ISET` run, plus the 0.20 mm
F.Cu neck off `U11.2` and its 0.80/0.40 via. The 0.60 mm BAT_MAIN trunk beyond
that via is **not** released, so no power geometry is re-landed at signal
width.

| net | segments | vias | length | open |
|---|---:|---:|---:|---:|
| `ISET` re-land | 15 | 0 | **7.242 mm** | **0** |
| `BQ25185_STAT1` | 68 | 2 | **28.846 mm** | **0** |
| `BAT_PROTECTED_P` re-land | 2 | 1 | **0.650 mm** | **0** |
| `BQ25185_STAT2` | 0 | 0 | — | **1** |

**KiCad DRC on the refilled scratch board: 0 errors, 240 warnings, warning-type
delta vs the real board NONE, 215 unconnected** (= 216 − `STAT1`).
**DFM: 0 of 3 vias under any fitted body or courtyard**; the 0.80 mm BAT via
clears `U11.1` by 0.6231 mm with a 0.5718 mm mask dam.

One segment needed widening by hand after routing: the router routes a net at a
single width, so the 0.100 mm B.Cu tail that reaches the surviving trunk came
out at 0.20 mm and lands outside `U11`'s courtyard, where `BAT_MAIN minimum
width 0.6000 mm` applies. Widening exactly that segment clears it — what a
person would draw.

### Why `STAT2` does not close

All 24 route orders were tried, at four release sizes, with and without the
courtyard relaxation. **`BQ25185_STAT2` and the `BAT_PROTECTED_P` re-land are
mutually exclusive**, and the two orders that reach open = 1 are not equivalent:

| order | closes | leaves open | landable? |
|---|---|---|---|
| `STAT2` first | `STAT1`, `STAT2`, `ISET` | `BAT_PROTECTED_P` | **no — it severs the battery rail** |
| `STAT1` first | `ISET`, `STAT1`, `BAT_PROTECTED_P` | `STAT2` | **yes** |

DRC scores both identically, because "unconnected item" does not know that one
of them is the battery. The order is chosen by what the net **is**.

The mechanism, measured: `BAT_PROTECTED_P` must neck to 0.20 mm to leave
`U11.2`, must widen to 0.60 mm once outside the courtyard, and its layer
transition needs the class **0.80 mm** via. That via, centred on the y = 66.600
lane with BAT_MAIN's 0.30 mm clearance, occupies y ≈ 65.90 … 67.30 — the whole
of the y = 67.000 lane `U11.3` needs. Releasing the neck lets `STAT2` out;
re-landing the via puts it straight back.

Escalation was tried and made it worse: 8 objects / 10.000 mm still open 1;
10 objects / 17.098 mm **open 2**, because there is then more 0.60 mm trunk to
re-land through a congested area.

**`BQ25185_STAT2`: FAIL this pass.** What it needs is a dedicated `U11`
left-column pass planning `BQ25185_SYS`, `BAT_PROTECTED_P` and `STAT2` as three
parallel 0.20 mm lanes at y = 66.200 / 66.600 / 67.000 — exactly at the legal
limit under the courtyard relaxation — with the 0.80 mm BAT transition via
placed far enough west to clear all three. Hand analysis says that geometry
exists; expressing it needs the **per-object** form of the necking rule, which
a raster cannot represent. That is a hand-placed escape verified by KiCad DRC,
not a raster search, and it is its own pass.

## 4. Preservation

PCB routing byte-identical to `27bf8f9` apart from the two DNP attributes;
DRU untouched; `hardware/beta/` empty diff. `BOOT_N`, **`WAKE_INT_N`**, the R2
candidate-B `+3V3` escape, the microphone I2S, internal I2C, SPI-A, SPI-B, USB,
the backlight, the buttons, `CC1101`, **every `SX1262` control including
`SX1262_RXEN` and the In2/E5 crossing**, Edge.Cuts and the mounting holes are
all untouched — `SX1262_RXEN` was never released, in scratch or otherwise.

## 5. What the next pass needs

1. **A `U11` left-column pad-escape pass**, hand-placed and DRC-verified, for
   `BQ25185_SYS` / `BAT_PROTECTED_P` / `STAT2`. This is the only thing standing
   between the current state and C = 1.
2. **Separation for the four-XGPIO topology.** The routes exist and all six
   commodities join on a 6.544 mm release; what is missing is a conflict-free
   arrangement. Options, cheapest first: a larger negotiation budget with
   layer-biased costs; reserving one lane per XGPIO up front; or spending some
   deferred-function copper and re-landing it, which §15 permits provided every
   released net comes home.
3. **Forbid new via sites inside fitted-footprint courtyards** in the router,
   so candidates are DFM-clean by construction rather than by audit.

Ranked by what the 26-iteration evidence says: **more negotiation budget is
ruled out**. The lever is either extra lane capacity (spend deferred-function
copper and re-land it, which §15 permits) or a different separation strategy —
reserving one lane per XGPIO before routing, rather than negotiating four nets
into a corridor that measurably cannot separate them.
