# FBV2-P1-001 — Full Beta v2 enclosure-driven PCB outline and component floorplan

**Date:** 2026-08-24
**Task:** FBV2-P1-001
**Gate:** **FBV2-P1 — DOES NOT PASS.** One gate criterion fails: the **100 mm 915 MHz pigtail does
not reach** the top-panel SMA. **No progress was awarded. Full Beta v2 stays at 68 %.**
**Starting SHA:** `cbab048411e5e01e73ae7dce1538b0708ca380bc` — matches the expected HEAD.
**Pre-P1 PCB SHA-256:** `aaa04bfbd5d69c5636da1094104081e2729f2bb7d5e07e7353f1f4eafc86a9f2`
— bit-identical to `hardware/beta-dm/kicad/aqroot-beta-dm/aqroot-Beta-DM.kicad_pcb`.

---

## 0. Preflight

| check | result |
|---|---|
| `git status` | clean but for two long-standing untracked paths, both left alone |
| local `master` / `origin/master` | both `cbab048` — in sync |
| staged / uncommitted tracked work | none |
| local-only commits | none |
| current PCB identity | **still the Beta-DM-equivalent board** — 188 footprints, 2 801 segments, 424 vias, 43 zones — exactly as expected |
| untracked, untouched | `hardware/beta-dm/fab/AQROOT-Beta-DM-Gerbers-aa64c16.zip`, `hardware/beta/mechanical/` |

---

## 1. The six rulings, as implemented

| ruling | implementation | verdict |
|---|---|---|
| **P1-A** side convention / microphone | `F.Cu` = FRONT, `B.Cu` = REAR, locked in the board and in every artefact. **`MK1` on B.Cu at (3.000, 50.000)**, bottom-port, listening **forward** through the Ø1.05 mm NPTH; front gasket region reserved on the opposite face; **1.21 mm clear of the LiPo envelope** | **DONE. O-1 closed** |
| **P1-B** rear packing | Y architecture **NFC → battery → speaker**, top to bottom. **48 + 75 + 20 = 143 mm in the 155 mm cavity, 12 mm of real gaps.** Zero NFC/battery overlap; speaker in the bottom band biased lower-right; **no attempt to place the speaker beside the battery** | **DONE. O-2 closed as a false conflict** |
| **bosses** | six M2 remains the TARGET; coordinates derived from the actual placement, not forced to Y = 95. **Only three positions close** — see §5 | **PARTIAL — escalated** |
| **USB / microSD** | **BODY edge-to-edge ≥ 8 mm** adopted; achieved **16.40 mm** on verified courtyards, microSD left of USB-C, independent apertures, ≈ 22 mm of card travel reserved | **DONE, comfortably** |
| **915 pigtail** | `095-902-568-100` **verified live under D-096** and written into every sourcing and mechanical document | **RECORDED — but it does not reach; see §6** |
| **915 whip storage** | every current requirement for an internal storage channel **deleted**; `TI.92.2113` unchanged and explicitly external; **the left wall is now the 433 MHz flex's** | **DONE. O-6 closed** |

### 1.1 D-096 re-verification of the pigtail

Digi-Key record read live on 2026-08-24 for **Amphenol RF `095-902-568-100`**:
**Part Status ACTIVE**; Connector A **SMA Jack, panel mount bulkhead, front-side nut**;
Connector B **U.FL (UMCC) / AMC plug, right angle, free-hanging**; cable **RG-178**;
**50 Ω**; **100.00 mm**; **6 GHz max**. IP67 is carried from the Amphenol series data (D-195); the
manufacturer's own page refuses to serve in this environment and was **not** re-read.

> **Procurement finding, recorded honestly:** the 100 mm variant is ACTIVE but shows **0 in stock
> at Digi-Key with a 12-week factory lead time** and no JLCPCB listing. The 150 mm part it
> supersedes was in the same family. **This is a first-five schedule risk independent of the reach
> problem below.**

---

## 2. Board-side convention, outline and datum

**Datum: origin at the lower-left board corner, X right, Y up.** KiCad's file datum is the
upper-left with Y down, so **`Y_kicad = 148.000 − Y_doc`**; every table in the P1 artefacts uses
the doc datum and the translation is stated in each of them.

**Outline: 70.000 × 148.000 × 1.6 mm — the TARGET, not the maximum.** The complete floorplan
closed on it, so the 72 × 152 envelope was **not** used and no decorative geometry was added. The
board keeps **2.5 mm** to the cavity wall in X and **3.5 mm** in Y, i.e. the deliberate margin the
mechanical spec §4 asks for rather than the 1.5 mm minimum.

---

## 3. Rebuilding the board

The inherited Beta-DM geometry is not a placement baseline for a design whose content has changed,
so the board was rebuilt from the **current nine-sheet schematic**:

- the pre-P1 file was **stripped to its header, layer stack, `general` and `setup`**, so the layer
  names, design rules and constraints are the pre-P1 ones, byte for byte;
- **all** Beta-DM footprints, tracks, vias, zones and graphics were removed;
- **321 footprints were re-created, one per schematic component** — references preserved, exact
  verified footprints preserved, **zero duplicates, zero missing**;
- **224 nets over 991 pads** were applied from the schematic netlist;
- the outline, 13 named mechanical regions, 4 copper rule areas and 3 M2 NPTH bosses were added.

**The schematic was not touched: ERC 27 violations / 0 errors, histogram byte-identical to
FBV2-MECH-002.** No connectivity was altered to make placement easier.

`fork_equivalence` now reports the v2 PCB as **changed** rather than bit-identical. **That is the
intended and expected outcome of P1**, and the same run confirms `hardware/beta-dm/` is untouched.

---

## 4. Placement

Placement followed the required priority order — outline, keepouts and bosses, display and `J1`,
edge connectors, community connector, IR and SMA, the battery / NFC / speaker / microphone
reservations, the ESP32 antenna, the radio modules, controls, power, NFC front end, audio,
expanders, remaining ICs, passives, test points. **Passives were placed last, never first.**

Everything not hand-anchored was seated by **net-affinity clustering**: each part is placed next to
whichever anchored device it shares the most non-power nets with. That keeps each switching
converter with its own inductor and capacitors, keeps the NFC front end short, and puts the three
expanders beside the controls and the community port — without any hand-assignment of 280 parts.

Full detail, coordinates and renders:
[`../pcb/FBV2_P1_FLOORPLAN.md`](../pcb/FBV2_P1_FLOORPLAN.md),
[`../pcb/FBV2_P1_COORDINATES.csv`](../pcb/FBV2_P1_COORDINATES.csv),
[`../pcb/FBV2_P1_KEEPOUTS.md`](../pcb/FBV2_P1_KEEPOUTS.md),
[`../pcb/review/`](../pcb/review/).

### 4.1 Geometry review — zero placement conflicts

A side-aware pairwise review over all 321 courtyards (front and rear may share plan area;
through-hole parts block both faces) returns **zero** courtyard or body overlaps, **zero**
out-of-board parts, **zero** boss-keepout intrusions, **zero** display / battery / NFC height
violations, **zero** B.Cu parts in the sealed speaker cavity, **zero** leads protruding into the
battery, NFC or speaker volume, and **zero** parts inside the ESP32 antenna keep-out or the
microphone acoustic keep-out.

KiCad DRC reports **76 violations and 499 unconnected pads**. The unconnected count is the correct
P1 state. **None of the 76 is a placement collision:** 25 are reference-designator silkscreen,
21 are pad-to-pad adjacency for the router to nudge, **12 are the stock ESP32 footprint's 0.2 mm
thermal vias against the board's 0.3 mm minimum-hole rule**, 12 are board-corner edge clearance,
6 belong to the three mechanical bosses that correctly have no schematic symbol, and 2 are the
`MK1` ring pad — see §7.

---

## 5. Mounting bosses — only three close

Six M2 bosses with a Ø6.0 mm keep-out do **not** fit. The reason is arithmetic, not preference:

- a boss is a through-board feature, so it must clear **both** faces;
- the **display** occupies X 3.39 … 59.93 for Y 55.04 … 140.00 on the front;
- the **battery** occupies X 6.00 … 66.00 for Y 23.50 … 98.50 on the rear;
- the **NFC zone** occupies X 0.50 … 48.50 above Y 102.00 and forbids screws outright;
- that leaves **no 6 mm-wide side strip anywhere**: the left margin is 3.4 mm wide (display) or
  6.0 mm (battery), the right margin 4.0 mm, and the top corners are inside the NFC zone.

A search over the whole board, with the display, battery, NFC, speaker, 433, aperture and
component keep-outs applied, finds **three** legal M2 positions at a **Ø4.5 mm** keep-out:

| boss | X | Y | where |
|---|---|---|---|
| `BOSS1` | 3.500 | 44.000 | left margin, below the display |
| `BOSS2` | 59.500 | 145.000 | top edge, right of the NFC zone, left of the IR windows |
| `BOSS3` | 40.000 | 12.000 | bottom edge, between USB-C and the D-pad column |

**Three M2 fixings on a 148 mm board with a battery behind it will not control flex under button
pressure.** This is escalated, not silently accepted — see §8.

---

## 6. Why FBV2-P1 does not pass: the 915 MHz feed

**Every part taller than about 1.2 mm is excluded from the upper half of the board.** Above
Y ≈ 55 the front face is display shadow (F.Cu ≤ 0.8 mm) and the rear face is first battery
(B.Cu ≤ 1.2 mm) and then NFC clear zone (B.Cu ≤ 1.0 mm, and no shielding cans at all). The one
remaining strip, X 53.5 … 70.0 above the battery, is 16.5 mm wide and already carries `J5`'s
31.6 mm through-hole field. **A 15.89 × 21.34 × 3.5 mm radio module fits nowhere above Y ≈ 55.**

`U8` therefore sits at the bottom rear, and the measured consequence is:

| assembly | routed estimate | verdict |
|---|---|---|
| `095-902-568-100` — **the part this task ruled** | ≈ 190 mm needed | **SHORT BY ≈ 90 mm** |
| `095-902-568-150` — the superseded part | ≈ 190 mm needed | **SHORT BY ≈ 40 mm** |
| `095-902-568-200` | ≈ 190 mm needed | reaches |

**Length is only half of it.** The SMA is locked to the **top edge, left half**, and the NFC
48 × 48 clear zone owns the entire upper-left. A coax from the bottom to the top-left must either
cross the NFC zone or run in the 2.5 mm side gap, **inside the 5 mm metal keep-out**. Neither is
permitted, so **no pigtail length fixes this on its own.**

**Three options, none taken here.**

1. **Raise the display support by ≈ 3 mm.** Column A of the mechanical spec totals 13.1 mm of the
   23 mm budget and carries **9.9 mm of unused Z**; spending 3 mm of it puts the display's rear
   face far enough off the PCB for a 3.5 mm module to live under it. That frees the whole upper
   half, lets `U8` sit beside the NFC zone, and makes a **short** pigtail reach. It costs an
   enclosure change and needs a check that a shielded module behind the panel's metal frame is
   acceptable. **Recommended.**
2. **Move the SMA bulkhead to the top-edge right half** and accept a **200 mm** assembly routed up
   the right wall, clear of the NFC zone. Cheapest in engineering, but it collides with the IR
   crown and reverses a locked face assignment.
3. **Shrink or re-shape the NFC clear region.** The antenna is Ø46 circular; a **Ø48 circular**
   clear zone instead of a 48 × 48 square frees both upper corners and would open a legal coax
   lane. This is a change to a LOCKED requirement and is a CTO call.

---

## 7. Opportunity and simplification scan

**Surfaced, not decided. No feature was added and no locked electrical architecture was changed.**

| # | finding |
|---|---|
| **P1-O1** | **The display cannot be centred on the enclosure.** `J5` needs 9.2 mm of board width on the right and cannot sit below the battery, so it must occupy Y 105 … 137 — beside the display band. The panel therefore sits **3.34 mm left of the board centreline**, and the same amount off the enclosure centreline. Widening the board to 72 mm does not fix it. **This is visible on the front face and needs a ruling.** |
| **P1-O2** | **Only 3 of 6 M2 bosses close** (§5). Options: accept 3 plus moulded edge-capture ribs; reduce the battery or display width; or add a rib bearing on a component-free strip. |
| **P1-O3** | **The 915 feed does not close** (§6). |
| **P1-O4** | **`MK1`'s ring pad fails KiCad 10's padstack validator** — *"custom pad shape must resolve to a single polygon"*. The footprint was built at FBV2-S2-002 from the PUI drawing and is dimensionally right; the GND ring is drawn as a **stroked circle outline**, which the new validator rejects. It must be re-drawn as a filled annulus before fabrication. **Two DRC errors, footprint-level, not a placement error.** |
| **P1-O5** | **The stock `ESP32-S3-WROOM-1` footprint's 12 thermal vias are 0.2 mm**, below this board's 0.3 mm minimum-hole rule. Either the rule or the footprint must move at FBV2-P2. |
| **P1-O6** | **`netclass_probe` was measuring the wrong board.** Its expectation set listed `LED_A1`…`LED_A4` — Beta-DM net names. The Full Beta v2 schematic has **one** anode net, `/03_SPI_A_DISPLAY_SD/LED_A`, the net D-111 deliberately added to `LED_BOOST`. The probe only passed before because the PCB was still Beta-DM's. **Expectation corrected to the schematic; the guard itself — `LED_BOOST` must never capture the IR transmitter nets — is unchanged and still passes.** |
| **P1-O7** | **A region serving two non-conflicting functions.** The ESP32 antenna keep-out and the NFC clear zone are both *absence* requirements. They are on opposite ends of the board here, but the principle is recorded: a copper-free reservation can satisfy an RF keep-out and a magnetic-field clear zone simultaneously. |
| **P1-O8** | **The IR parts are flat-mount footprints that must look out of the TOP panel.** `D1` (5 mm THT LED) and `U6` (3-pin minicast) both have their optical axis normal to the **board**, not to the top face. Both are leaded and must be **formed 90° at assembly**. This is a first-article assembly instruction, and it is not written down anywhere else. |
| **P1-O9** | **Cable lengths after placement.** 433 needs ≈ 36 mm of its 100 mm lead; the speaker needs ≈ 23 mm of its 152 mm lead; NFC needs ≈ 36 mm of its 75 mm lead. **The speaker lead is 6× longer than the run requires** — a shorter lead would remove slack from the battery/NFC region at no cost. |

---

## 8. Validation

| check | result |
|---|---|
| Schematic parses, 9 sheets | **PASS** |
| **ERC** | **27 violations / 0 errors — histogram byte-identical to FBV2-MECH-002** |
| Schematic connectivity | **unchanged** — the schematic files were not opened |
| PCB parses | **PASS** |
| Footprint count vs schematic | **321 / 321**, zero missing, zero duplicate references |
| Board-vs-schematic reference comparison | every board reference resolves to a schematic symbol; the only extra footprints are the **3 mechanical M2 bosses**, deliberately excluded from BOM and position files |
| Placement / courtyard errors | **0** |
| Mechanical conflicts remaining | **0** |
| Height-zone checks | **0 violations** across display, battery, NFC and speaker |
| DRC | **76 violations / 499 unconnected** — none a placement collision (§4.1) |
| `netclass_probe` | **PASS** after the expectation correction (P1-O6) |
| `fork_equivalence` | PCB now **changed** — **expected**, not a failure. Beta-DM confirmed unchanged |
| **Signal routing added** | **ZERO tracks, ZERO vias, ZERO copper pours** |

### 8.1 Trees confirmed untouched

`hardware/beta-dm/` · frozen `hardware/beta/` · `hardware/beta/mechanical/` · every footprint and
symbol library · all nine schematic sheets. **The only design file changed is
`aqroot-Beta-v2.kicad_pcb`.**

---

## 9. Progress

**FBV2-P1 does not pass, so no percentage was awarded. Full Beta v2 remains 68 %.**
The floorplan is complete and collision-free and is ready to be re-gated the moment the 915 MHz
feed is ruled on. **FBV2-P2 has not begun; routing has not begun.**
