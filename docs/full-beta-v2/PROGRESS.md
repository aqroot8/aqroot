# AQROOT Full Beta v2 Progress

**Status: LIVING DASHBOARD.**

Date: 2026-08-24 (updated after **FBV2-P2-002B — routing harness qualification.
**HARNESS QUALIFICATION = PASS.** All three router defects fixed and proved fixed on real geometry;
the two remaining cases are a **proved land-pattern / rule conflict** on five fine-pitch pads,
surfaced for a CTO ruling. **No copper committed; the board is byte-identical to `8b9efba`.**
**PCB routing stays 0 %; overall stays 74 %**; previously **FBV2-P2-002A — battery / protection routing attempt.
**FAIL: the block is NOT routed and nothing was committed as copper.** Delivered D-245 and a
working obstacle-aware router with per-net DRC gating. **PCB routing stays 0 %; overall stays
74 %**; previously **FBV2-P2-001 — power-routing attempt. **FAIL: the power tree is
NOT routed and the attempt was reverted.** Delivered the In1.Cu GND plane and the PM-2 support /
test-point placement corrections. **PCB routing stays 0 %; overall stays 74 %**; previously
**FBV2-EXP-002 — standard expansion interface implemented and
the combined re-floorplan executed. **FBV2-P1 RE-ISSUED = PASS, FBV2-P2 ENTRY = PASS, PM-1/PM-2/PM-3
and PT-1 CLOSED. NO PROGRESS EARNED — P1 was re-earned, not newly earned; overall stays 74%**;
previously **FBV2-EXP-001 — expansion ecosystem compatibility and
pre-routing architecture audit. AUDIT = PASS; **AUDIT ONLY, NO AUTHORITATIVE HARDWARE CHANGE, NO
PROGRESS EARNED: overall stays 74%**; previously **FBV2-P2-000 — P2 pre-routing entry gate and routing strategy
freeze. **FBV2-P2 ENTRY = FAIL** on one criterion of thirteen; **NO PROGRESS EARNED: overall stays
74%**, FBV2-P1 = PASS unchanged**; previously **FBV2-P1-002 — P1 closeout; **FBV2-P1 PASSES**; overall 68% → 74%**; previously **FBV2-P1-001 — enclosure-driven floorplan built; **FBV2-P1 DOES NOT PASS** on the 915 MHz pigtail reach; overall stays 68%**; previously FBV2-MECH-002 — pre-floorplan authority reconciliation and final
procurement sign-offs. NO PROGRESS EARNED: overall stays 68%, FBV2-S2 = PASS unchanged**; previously
FBV2-S2-002 — S2 release closeout, FBV2-S2 = PASS)
Repository HEAD at last update: `8b9efba` (FBV2-P2-002A)

---

## How percentages work here

**A percentage increases only when a gate passes.** It does not increase because
work was done, because a document was written, or because something looks close
to finished. A gate passes when its exit criterion is met and that fact is
recorded in this file with a date.

This rule exists because the programme has already been burned once by
progress that was asserted rather than measured: the enclosure reconciliation
that Field Slate v3 required was recorded as done in a commit title
("enclosure-driven PCB floorplan") while it had not happened. Percentages here
are gate-backed or they are not written.

Corollary: percentages can go **down** if a gate is later found not to have been
met.

---

## Beta-DM (preserved fallback / manufacturing baseline)

| item | status |
|---|---|
| PCB / design | **100%** |
| Fabrication | **PAUSED BEFORE PAYMENT** |
| Overall Beta-DM | **~81%** |
| Role | Preserved fallback and manufacturing baseline |

Beta-DM is not cancelled. It is the programme's insurance policy: a
design-side-complete board with DRC 0 errors and a generated fabrication package
that can be built if Full Beta v2 stalls. It must remain preserved
(CTO decision D-005).

---

## Full Beta v2

| phase | status |
|---|---|
| Requirements / product direction | **100%** |
| Pre-design audit | **100%** |
| Architecture freeze | **IN PROGRESS** |
| Schematic migration | **100%** — **all nine sheets landed. `fork_equivalence.py`'s "still Beta-DM" list is EMPTY.** |
| PCB placement | **100%** — **FBV2-P1 RE-ISSUED AND RE-PASSED on the new 72 × 148 outline (FBV2-EXP-002)** |
| PCB routing | **0%** — entry gate PASS; **two routing attempts, both correctly reverted**, then the router itself put on trial and **QUALIFIED** at FBV2-P2-002B: six of eight real-geometry cases route with zero new DRC violations and correct connectivity after save/reload, and the two that do not are a **proved rule conflict**, not a router fault. The **In1.Cu GND plane is valid (1 island, 93.3 %)**; the board still has **zero tracks and zero signal vias** |
| DFM / release | **0%** |
| Physical validation | **0%** |

### Overall Full Beta v2: **~74%**

#### How 74% was reached — FBV2-P1-002

**Raised 68% → 74% by FBV2-P1-002, and FBV2-P1 = PASS** — the third of the twelve gates to pass,
and the first that is about physical geometry rather than about the schematic. The increment
matches the established method: FBV2-S1 awarded +7 and FBV2-S2 awarded +6 on the same twelve-gate
table.

**What the gate actually proves.** There is now a complete, collision-free, enclosure-driven
placement of all 321 schematic components on a 70 × 148 mm outline, and **every mechanical
relationship in it is re-derived from the board file by a committed script**
(`hardware/beta-v2/checks/p1_regression.py`) rather than asserted. The 915 MHz feed — the one
criterion that failed at FBV2-P1-001 — closes on a **measured 138.48 mm** routed path to an exact,
in-stock, orderable assembly with 46.52 mm of spare.

**That is not the same as "ready to route."** No track, via or pour exists; 499 connections are
unrouted, which is the correct P1 state. `.kicad_dru` still references E5/E6 rule areas the P1
rebuild deleted, and those must be re-created or retired before routing starts — a P2 entry
condition, recorded as P2-O5. **— CLOSED 2026-08-24 at FBV2-P2-000 (D-233), and it was 39 areas
and 22 inert rules, not just the E6 pockets.**

**One item is escalated and does not fail the gate:** the outline yields **two** legal
through-board M2 positions, not the three the closeout task assumed. Structural support is
completed by enclosure edge-capture rails and four reserved rear rib pads, which need no PCB holes.
A third screw would need a narrower battery, a narrower display, the SMA off the top-left, or an M2
with ≈ 1.4 mm of board to the edge — ~~**all CTO calls, none taken**~~ (D-226). **— CLOSED 2026-08-24 by D-232: two M2 is ACCEPTABLE, all four routes to a third are DECLINED, and retention is locked as a four-element architecture.**

### FBV2-EXP-001 — expansion ecosystem audit: **PASS.** No percentage earned.

**Held at 74%.** FBV2-EXP-001 is an audit and changed no authoritative hardware: the PCB blob is
byte-identical to `HEAD`, no sheet was opened, `J5` is unchanged, no Qwiic connector exists, `BOOT`
and `POWER` have not moved and no PM part moved.

**The product intent is achievable and the electronics need no architectural change — but the
interface does not fit the current floorplan, and the shortfall is paid in battery width.** A
right-angle through-hole socket puts its solder tails **6.5–6.9 mm inboard of its own mating face**,
so for the face to reach the right wall the tail row lands at x ≈ 63.5, **inside the battery
envelope**, where `BATTERY_SHADOW` forbids any through-hole lead. **Measured requirement:
(board right edge − battery right edge) ≥ 7.83 mm. Today it is 4.00 mm. Shortfall 3.83 mm.** Above
the battery the right wall offers only **41.00 mm** against the 1 × 24's **61.47 mm** body; the
largest socket that fits there is a 1 × 15, and that leaves nothing for Qwiic or the power switch.
Every other edge was tested and rejected — left is the 433 flex and the mandatory coax channel,
bottom is USB-C / microSD / both radios, top is the IR pair and the SMA.

**Two 1 × 12 sockets are rejected on geometry, not preference.** Samtec and Sullins both build a
2.54 mm body **N × 2.54 + 0.51 mm** long, so two butted bodies place their end contacts **3.050 mm
apart against a 2.540 mm pitch — a 0.510 mm interference.** They cannot form a continuous 24-position
grid, they need **5.59 mm MORE** wall length than the single 1 × 24, and they add a mis-plug mode the
1 × 24 does not have.

**Recommendation: one `SSQ-124-02-G-S-RA` (Samtec — the same manufacturer as the present `J5`) plus
one `SM04B-SRSS-TB` Qwiic connector, CONDITIONAL on two owner rulings**: **E-1** PCB 70 → 72 mm
(already the documented `FBV2_PCB_MAX_MM`; the 80 × 160 × 23 shell is unchanged) and **E-2** battery
60 → 57 mm wide, ≈ **−5 % capacity**. **If E-2 is declined the 24-line side header cannot be
delivered in this enclosure and `J5` stays as it is.**

**Three things were confirmed rather than assumed.** **(1)** Qwiic needs **no new components**: it
attaches at `EXT_SCL`/`EXT_SDA`, downstream of the 22 Ω resistors and at `D2`'s clamp, inheriting the
`TCA4307`, the 1.5 k pull-ups, the series resistance and the TVS; power is `ACC_3V3_SW` because
`U16`'s own VCC already is. **(2)** A **Manual / Bench power mode needs NO hardware change for either
rail** — `ACC_DETECT_N` reaches nothing but an expander input, so detect gating is entirely firmware
policy, while ILIM, reverse-current blocking, thermal shutdown and `FLT` stay in hardware.
**(3)** `SW1` **BOOT is SMD** and a measured **11.04 mm** bottom-edge window exists between the
microSD shell and the USB-C receptacle, with a **14 mm** free enclosure span for the tool hole — while
**lower-left BOOT is rejected on RF**, because that wall *is* the 433 flex region and the mandatory
915 coax channel.

**PM-2 and the new header want the same corner.** PM-2's fix is to consolidate the battery-protection
block at the battery-entry corner — exactly where the 1 × 24 now goes. **A combined re-floorplan
sequence is recommended so the connector change, PM-1, PM-2, PM-3 and PT-1 are solved once.** The
outline change invalidates the current FBV2-P1 PASS, so **FBV2-P1 would have to be re-issued.**

New: [`architecture/EXPANSION_ECOSYSTEM_PROPOSAL.md`](architecture/EXPANSION_ECOSYSTEM_PROPOSAL.md),
[`audits/2026-08-24-expansion-compatibility-audit.md`](audits/2026-08-24-expansion-compatibility-audit.md).
**D-081 / D-083 / D-093 / D-097 remain in force; supersession is marked PENDING CTO / OWNER RULING.**

### FBV2-EXP-002 — expansion interface built and the combined re-floorplan executed

**Held at 74%.** **FBV2-P1 was RE-ISSUED and PASSES; FBV2-P2 ENTRY was re-run and PASSES.** Neither
earns a percentage: the outline, the battery and `J5` all changed, so the P1 gate had to be re-run
in full — but P1 was **re-earned, not newly earned**, and the gate-backed method does not pay twice
for one gate. P2 entry earns none by its own terms.

**The battery gate ran first, and it changed the story.** Before any authoritative file was touched,
the 57 × 75 × 8 mm envelope was checked against real purchasable cells: **PKCELL `LP785060`
(7.3 × 50 × 60 mm, 2500 mAh typ, PCM fitted, JST-PH lead)** and **`LP755070` (7.5 × 50 × 70 mm,
**3000 mAh min**, PCM fitted, 500 cycles to 80%)** — both from manufacturer datasheets, neither a
marketplace mystery cell. **The predicted −5% capacity penalty does not materialise: both candidates
are 50 mm wide, so the 57 mm limit does not bind either of them, and `LP755070` sits at the TOP of
D-071's 2500–3000 mAh target.** The envelope was always larger than the cells that fill it.

**`J5` is now a Samtec `SSQ-124-02-G-S-RA` 1 × 24 2.54 mm female right-angle socket** — same
manufacturer as the part it replaces — with **`J8`, a `JST SM04B-SRSS-TB` Qwiic / STEMMA QT
connector, added for zero components** on the protected external I²C node. **All 24 electrical
functions are retained and not one protection part was removed.**

**ORDER-B is safe under 180° reversal by construction**, which is why it supersedes ORDER-A: a full
accessory inserted backwards maps 5V↔5V, GND↔GND, 3V3↔3V3 and 3.3 V logic to 3.3 V logic on every
remaining contact — **power-to-signal maps under reversal: ZERO**, proved pin by pin from the
netlist. The one-position slip stays physically impossible: a 60.96 mm male body in a closed-end
62.5 mm recess leaves **1.54 mm of play against a 2.54 mm pitch**, and **D-097's asymmetric key is
no longer needed.**

**The board grew SYMMETRICALLY, 70 → 72 mm**, so every part shifted +1.0 mm in X and every
part-to-part relationship is preserved; only the edge margins moved, to **1.5 mm on both sides —
the rule met exactly, with nothing to spare.** The enclosure is untouched. `ANT433_REGION` had to be
**re-derived rather than shifted**: its old 2.2 mm reservation does not fit a 1.5 mm gap and never
described anything real, since the flex is 0.28 mm thick and bonded flat to the wall.

> **PM-1, PM-2, PM-3 AND PT-1 ARE ALL CLOSED.** Converter IC-to-inductor spans fall to
> **4.80 / 4.34 / 3.86 / 3.79 mm** from 12.96 / 28.56 / 30.50 / **45.90 mm**, and each is now a
> complete power cell rather than an inductor moved next to an IC — `D8`, which sat **45.7 mm from
> its own inductor**, is now 3.56 mm from `U17`. The 1.5 A protection path is **30.86 mm, from
> 116.7 mm**, as one monotonic column, with the Kelvin pair at 6.60 mm and **no topology change:
> D-049 is untouched**. The NFC arms are mirrored at **Δx = 0.000 mm and arm-length Δ = 0.000 mm**.
> `U11` is out of the battery shadow. **B-34 improves by ≈ 53 mW at 1.5 A but does NOT close** — its
> 0.70 W is dominated by the BATFET, not by copper, and that is said rather than glossed.

**`BOOT` moved to the bottom band on the front face**; **lower-left was rejected on RF**, because
that wall *is* the 433 flex region and the mandatory coax channel. **POWER stays on the right wall.**
**Retention is still two M2** — widening the board did not buy a third and none was chased.

**DRC 26 → 1** (the `MK1` artefact accepted at D-227, still not suppressed); **ERC 0 errors / 27
warnings, histogram identical; 499 unrouted; ZERO tracks, ZERO signal vias, ZERO electrical pours.**

New: [`audits/2026-08-24-expansion-and-refloorplan-implementation.md`](audits/2026-08-24-expansion-and-refloorplan-implementation.md).

### FBV2-P2-000 — pre-routing entry gate: **FAIL.** No percentage earned.

**Held at 74%.** FBV2-P2-000 is an entry gate and earns no progress by its own terms. It closed
every routing precondition except one — and the one it did not close is the one it existed to find.

**The rule set was not merely stale; 22 of 71 rules could never fire.** `.kicad_dru` referenced
**39 rule areas and the board contained none of them.** P2-O5 had recorded this as *"E5/E6 rule
areas"*; measured, it was **every RF-band rule, every E5/E4 corridor rule, the header reservation,
the E2 button escapes and the ESP32 antenna rule as well.** KiCad's `intersectsArea()` returns
**false** for an unknown name — no warning, no error — so a rule that can never fire is
indistinguishable from a rule being satisfied. The set is rebuilt to **64 live rules** with a
written retirement register, and **`checks/dru_probe.py` now fails the build if any reference stops
resolving** (D-233).

**The netclass table had been lying since the fork.** The `BAT_MAIN` pattern was the root-sheet
path `/BAT_PROTECTED_P` while every v2 power net lives under `/01_POWER_TREE/`. **It matched
nothing, so the highest-current net on the board — 1.5 A sustained — was routing on the 0.20 mm
Default class**, and `BAT_RAW`, `BAT_MID` and `BAT_SENSE` were in no class at all. `NFC_5V_PA`
captured **no net whatsoever**. `ACC_5V_LX`, a 1.2 MHz boost switch node, had **never** been in
`SWITCH_NODE`. **14 classes → 18, 62 patterns → 57, and every surviving pattern now matches at
least one net** (D-234).

**Retention is LOCKED and D-226's escalation is closed. Two M2 is acceptable** — no component
moved, no battery reduced, no display moved, no SMA relocated — with retention completed by
moulded edge-capture rails, **four** rear non-metallic support ribs, the two screws, and the `J5`
backing boss carrying its ≈ 33 N insertion load into the enclosure rather than into solder joints
(D-232).

> **WHAT FAILS THE GATE — three electrically required placement moves, none fixable by routing
> (D-236).** **PM-1:** all four switching converters have their inductor **12.96–45.90 mm** from
> their own IC — the backlight's `L3 → D8 → C44` boost loop is **≈ 76 mm around**, switching to
> **39 V** on an open-LED fault, 13 mm from the microphone. **PM-2:** the single-fault
> battery-protection block is dispersed across three clusters over **96 mm**, with 2.2–3.65 MΩ
> trip-point nodes and a **≈ 20 µA charge-pump gate node spanning 95.6 mm** past four converters.
> **PM-3:** the two NFC matching arms differ by **10 mm before a track is drawn**, with `L5` and
> `L6` on opposite sides of `U9`. **All three are new; none existed in Beta-DM to be carried
> forward.** FBV2-P1 verified every *mechanical* relationship by script — nobody had yet looked at
> these blocks *electrically*.

**Everything else is closed and written down.** Stackup retained and layer roles now enforced by
rule; one solid In1 with a single authorised void; USB confirmed as Full Speed, ≈ 40 mm, F.Cu only,
**zero vias, no length matching**; SPI-A **63 % shorter** and SPI-B **21 % shorter** than the
Beta-DM versions that were accepted, so neither gets damping; internal I²C given a **derived
C_bus ≤ 161 pF budget**; and the community-port escape measured as **10 crossings needed against
22 available on one layer** — no nudge required. **DRC 47 → 26. ERC unchanged at 0 errors / 27
warnings. 499 unrouted, ZERO tracks, ZERO vias, ZERO pours** (D-235).

New: [`pcb/FBV2_P2_ROUTING_PLAN.md`](pcb/FBV2_P2_ROUTING_PLAN.md),
[`pcb/FBV2_P2_NETCLASS_LEDGER.csv`](pcb/FBV2_P2_NETCLASS_LEDGER.csv),
[`audits/2026-08-24-p2-entry-audit.md`](audits/2026-08-24-p2-entry-audit.md).

<details>
<summary>Superseded — the 68% assessment as written at FBV2-S2-002 and held through FBV2-P1-001</summary>

### Overall Full Beta v2: **~68%**

**Raised 62% → 68% by FBV2-S2-002, and FBV2-S2 = PASS** — the second of the twelve gates to
pass. **B-03, B-63, B-70, B-54, B-71 and O-8 all close.** The design is now **fabrication-release
ready at schematic level**: every footprint is manufacturer-drawing verified, every one of the 46
MPNs has an explicit first-five route to the board, and every DNP part carries a recorded reason.

**That is not the same as "ready to fabricate."** No PCB placement or routing exists, and the
NFC matching network still requires bench tuning at first article — which the CTO ruling is
explicit does not fail this gate.

</details>

<details>
<summary>Superseded — the 62% assessment as written at FBV2-S2-001</summary>

**HELD at 62% by FBV2-S2-001. FBV2-S2 = FAIL on two of fourteen exit criteria, so no
percentage was awarded.** A percentage rises when a gate passes, and this one did not.

</details>

**The audit earned its keep on the first thing it looked at.** `U9` **ST25R3916-AQET** and its
twelve mandatory supply-decoupling capacitors were still marked **`DNP`**, against **D-035** and
**D-055**, while the 27.12 MHz crystal, the complete matching network, the antenna connector and
the SPI wiring around them were all **FITTED**. **The first five boards would have carried a
finished 13.56 MHz front end with no NFC chip on it.** All thirteen parts are now FIT (D-192).
**That is the seventh consecutive sheet with a load-bearing inherited `DNP`, and the one that hid
longest** — sheet 04's own migration was about the antenna, so nobody re-read the population state
of the IC underneath.

**`D-077`'s display second source does not exist.** Both Hirose land patterns were read: FH69 is
**7.38 mm** deep with a 0.30 × 1.23 signal land and **top-and-bottom two-point contact**; FH52E is
**4.6 mm** deep, **bottom contact only**, and its own catalogue says its pattern is interchangeable
with the **FH12**. **They cannot share pads. The drop-in claim is struck** and `J1` is confirmed as
manual assembly (D-194).

**Two more carried numbers were corrected:** the accessory boost settle delay was derived against
the datasheet's 10 µF condition when `C65`/`C66` give ≈ 20 µF effective at 5 V bias, so the real
margin was 3.5× and not 7× — **raised to ≥ 10 ms** (D-198); and **`R68`, a 0 Ω DNP with no note at
all, turned out to be a bypass across `SW9`** that would wire the unit permanently ON and defeat
the only way to power down a hung board (D-199).

**P-14 resolved:** the MAX17048 **stays on `BAT_PROTECTED_P`** — it was never on `BAT_RAW`, and
moving it to the LTC4368's precision sense node would trade a ≤ 2.6 % SOC error for a differential
capacitance across the current-sense resistor. **Safety outranks SOC accuracy** (D-193).

**Nine stale register entries were closed on evidence** — P-01, P-04, B-45, B-46, B-47, B-49,
B-51, B-53, B-68 — and **three new items opened**: B-70, B-71 and O-8.

**What fails the gate: B-03** — 15 of 28 critical footprints are drawing-verified with a citation,
**eight are not** — and **B-71**, only 7 of 46 unique MPNs carry an LCSC code, so the assembly
classification cannot be produced. **Neither blocks PCB placement; both block fabrication
release.**

**ERC 27 / 0 errors / 27, unchanged. 0 duplicate references, 0 unresolved footprint references,
0 missing MPNs on actives or connectors, 0 orphan nets, 0 `*_TBD`, 0 unexplained DNP, and 0
same-text local labels split across sheets.** PCB untouched and still bit-identical to Beta-DM.

<details>
<summary>Superseded — the ~62% assessment as written at FBV2-S1-009</summary>


**Raised 55% → 62% by FBV2-S1-009, and FBV2-S1 = PASS — the first twelve-gate
entry to pass since FBV2-A2 on 2026-08-22.** The task gate
**FBV2-S1-COMMUNITY = PASS** (2026-08-23).

> **FBV2-S1 = PASS means SCHEMATIC MIGRATION COMPLETE. It does NOT mean
> fabrication ready.** No placement, no routing, no outline, no DFM, no
> mechanical CAD and no physical validation exist. See §"What FBV2-S1 does not
> mean" in
> [`audits/2026-08-23-s1-schematic-migration-closeout.md`](audits/2026-08-23-s1-schematic-migration-closeout.md).

**ERC 42 / 1 / 41 → 27 / 0 / 27. The design has ZERO ERC errors for the first
time in the programme.** 321 components, 0 duplicate references, 0 without a
footprint, 224 nets, 0 `*_TBD`. `fork_equivalence.py` PASS, `netclass_probe.py`
PASS, PCB still bit-identical to Beta-DM.

**Three CTO rulings were recorded before the work started.** **O-6 RATIFIED** —
`U23` and the front RGB are locked architecture and **B-37 is retired**, with 37
of 48 expander pins used and eleven free. **O-4 APPROVED** — `U16` becomes TI
`TCA4307DGKR`, fitted, replacing a DNP TCA9517A. **P-18 CLOSED with no mux** —
the TCA4307 solves *electrical* fault isolation and the address registry solves
*address* allocation.

**Sheet 09 had to be rebuilt, and it was hiding two serious defects.** `J5`
contact 1 carried **permanent raw `+3V3`**, against D-057. And **the community
port had no power at all**: `01:ACC_3V3_SW`, the real switched rail at `U20`, and
`09:ACC_3V3_SW`, fed by a **second, DNP TPS22918** nobody had noticed, were
**different nets**; `01:ACC_5V_SW` reached nothing outside sheet 01.

**The sixth consecutive migrated sheet carried a load-bearing inherited `DNP`** —
`U16`, `R49`, `R50` and six TVS arrays. The pattern recorded at FBV2-S1-007 held
to the last sheet without a single exception.

**Two numbers that had been carried were wrong and are now derived.** The
inherited external I²C pull-ups were **4.7 kΩ**, which gives **796 ns against a
300 ns fast-mode budget** at a 200 pF external bus — they could never have worked
at 400 kHz. They are now **1.5 kΩ = 254 ns**. And the 3.3 V `R_ILIM` was
re-derived against a budget that has grown by the IR transmitter and the RGB:
the accessory-short case moved from 86 % to **89 % of the TPS63020's 2 A**, so
1.5 kΩ still holds — but it was checked, not copied.

</details>

**Eight of nine schematic sheets are migrated. Only sheet `09` remains.**

**The task was interrupted by a session limit and resumed rather than restarted.**
All of its work existed as uncommitted working-tree change; it was inspected,
classified and finished. The interrupted session had converted both expanders
properly, deleted HOME, landed `TOUCH_INT_N` and `SX1262_DIO1`, selected and
verified the RGB part — and had written an honest note into the schematic saying
the pin budget did not close. **That diagnosis was correct.**

**35 committed signals against 32 expander pins, and every escape closed.** There
is **zero free native GPIO** (B-10; GPIO35/36/37 are the octal PSRAM), which makes
the brief's own WS2812 escape **impossible** — a smart LED needs RMT on a native
pin. `RESERVED_SPARE` is mandated by D-094, the ten XGPIO are locked by D-082, and
an LED driver IC would be a new part family for one indicator. **`U23`, a third
`PCAL9535APW,118` at `0x22`, closes it** with no new MPN, no new footprint, no new
driver and no new rail — and **retires B-37** with 12 spare I/O, the first slack
this programme has had. **Raised as O-6 for ratification.**

**Core, community and safety functions were placed before the RGB by
construction.** `U23` carries the status light and the reserved spare and nothing
else, so declining O-6 costs the light and **not one other function**.

**`RESERVED_SPARE` did not exist before this task.** D-094 had required it since
2026-08-23 and no sheet had implemented it.

**The fifth consecutive migrated sheet did NOT repeat the inherited-DNP trap** —
sheet 08 carries zero DNP parts, and HOME was deleted outright rather than marked
`DNP`.

**ERC 42 / 1 error / 41 warnings — identical violation set to the working tree
this task resumed from, and better than the 45 / 2 / 43 that stood before sheet 08
was touched.** Zero new errors. PCB still bit-identical to Beta-DM; sheet 09
untouched.

**The whole IR subsystem arrived DNP — for the fourth sheet running.** `U6`,
`D1`, `Q1`, `R21`, `R22`, `R23`, `R24` and `C11` were all marked `DNP`; only the
local bulk capacitor was fitted, decoupling a transmitter that was not there.
All eight are now fitted (D-153). **This is no longer a coincidence: a `DNP` on a
Beta-DM sheet describes what was populated on that reduced build, not what the
architecture requires. Sheets 08 and 09 must be assumed to carry the same trap.**

**The rating that binds an IR LED is not the one that looks biggest.** `IFSM` =
1.5 A is a **single-pulse surge for t ≤ 5 µs** and cannot justify carrier current;
the governing figure for a 38 kHz burst train is **`IFM` = 200 mA**. Peak current
is set at **150 mA — 75 % of `IFM`** — with 200 mA rejected for leaving no
tolerance margin and **300 mA rejected as out of spec** however comfortable the
thermals look (D-155). Thermally none of them is hard: 25 mW against a 160 mW
limit, ΔTj under 6 K. Range is not the constraint either — the receiver
datasheet quotes **45 m using a TSAL6200 at only 50 mA**.

**The supply preference is reversed: `+3V3`, not `SYS`** (D-156). On the
regulated rail 12 Ω gives **118–170 mA across every tolerance**; on `SYS` the
same job gives **64–166 mA**, so **IR range would visibly shorten as the battery
drains**. The noise objection that motivated `SYS` is answered by `C12` (40 mV of
38 kHz, 1.2 % of rail) and by the fact that **the only device specified against
carrier-frequency supply ripple — the IR receiver — already sits behind 41 dB**.

**`C12` was three times too small.** 4.7 µF gives 218 mV of carrier ripple;
**22 µF gives 40 mV**, and the part is specified 1210 X7R 16 V because the
requirement is ≥ 15 µF *effective* at 3.3 V bias (D-158).

**Two inherited open items closed.** The **AO3400A pinout is confirmed
1 = G, 2 = S, 3 = D** from the AOS datasheet, matching the existing wiring; and
the *"needs the official AOS land pattern"* blocker asked for a document that
**does not exist**, so it becomes an ordinary FBV2-S2 footprint item (D-159).
Safe-OFF is now proven rather than assumed: `R23` holds the gate at ≤ 10 mV
against a 650 mV threshold, a 65× margin.

**The receiver's existing supply filter turns out to be the load-bearing part of
the sheet.** `R21`/`C11` give **41 dB at 38 kHz**, and datasheet Fig. 7 shows the
receiver degrading from roughly **10 mV RMS of supply ripple at the carrier
frequency**. 40 mV on the rail becomes 0.1 mV at `VS` — **~90× margin**, and that
is what makes sharing `+3V3` safe (D-160).

**ERC 45 → 45: zero added, zero removed.** 311 components, 0 duplicates,
0 without a footprint, 0 `*_TBD` nets.

> **O-5 — NEW, REQUIRES A CTO DECISION. The receiver lock conflicts with the
> protocol list.** The brief locks `TSOP38438`; the brief also lists Sony/SIRC.
> **Vishay marks AGC4 "No" for Sony code** where the AGC2 `TSOP38238` is "Yes".
> The lock is a defensible trade — AGC4 is *"Preferred"* on five of six protocols
> and suppresses high-modulation fluorescent interference AGC2 cannot — but it is
> a trade. **It is receive-only: transmitting Sony is unaffected**, and reverting
> is a `lib_id` change because **the `TSOP38238` symbol was deliberately kept in
> the library**. Implemented as locked pending the ruling.

**B-65, B-66 opened.**

Full analysis:
[`audits/2026-08-23-s1-ir-implementation.md`](audits/2026-08-23-s1-ir-implementation.md).

<details>
<summary>Superseded — the ~51% assessment (FBV2-S1-006)</summary>

**Raised 49% → 51% by FBV2-S1-006.** **No gate in the twelve-gate table passed.**
The task gate **FBV2-S1-AUDIO = PASS** (2026-08-23).

**The finding that was not on the brief: the speaker output path has never been
built.** `U5` (the MAX98357A) and `J6` (the speaker connector) arrived from
Beta-DM marked **`DNP`** — while `C9` and `C10` *were* fitted, decoupling an
amplifier that was not there. Voice output is required, so **both are now
fitted** (D-144). This is the **third load-bearing inherited `DNP` in two
tasks**; a `DNP` on a Beta-DM sheet describes the reduced build, not the
architecture, and every migrated sheet has to re-decide it.

**The microphone replacement is not a drop-in.** PUI **`DMM-4026-B-I2S-R`** has
**seven pads, not six**, so a new symbol and a new footprint were built from the
manufacturer drawing. Its extra pin, **`CONFIG`, must be tied to GND** and has no
ICS-43434 equivalent. **`R120` 100 kΩ on `I2S_MIC_DIN` is a data-sheet
requirement** — `SD` tri-states for the whole unused half of every frame and the
inherited sheet had no pull-down at all (D-145).

**No 1.8 V rail is needed, and that was the biggest risk in the swap.** The part
is *rated* 1.8 V and PUI's catalogue line reads *"MICROPHONE -26DB 1.8VDC"*, but
its operating range is **1.5–3.6 V**, so `+3V3` and the existing `C8` are the
whole supply design.

**The brief's suggested 16 kHz cannot be run on the wire.** The microphone needs
**BCLK 2.048–4.096 MHz**; 16 kHz × 64 = 1.024 MHz is outside it, and below
320 kHz the part sleeps. **The bus runs at 48 kHz × 64 = 3.072 MHz and firmware
decimates to 16 kHz** (D-146). On the bench this would have looked like *the
microphone sometimes returns silence*.

**A gain strap was mismatched to the rail.** At `GAIN_SLOT` = GND (12 dB) a
0 dBFS sample asks for **5.07 Vrms** and the 3.3 V rail gives **2.33 Vrms** — the
**top 6.8 dB of the digital range was clipped by the supply**. `GAIN_SLOT` moves
to VDD = **6 dB**, where 0 dBFS lands on the rail. Maximum loudness is unchanged;
it is rail-limited, not gain-limited (D-147).

**Speaker locked: PUI `AS02008MR-LW152-R`** — Ø20 × 3 mm, 8 Ω, 0.5 W rated /
0.8 W max, 86 dBA at 0.1 W / 0.1 m, **500–4000 Hz voice band**, 152 mm AWG #32
leads that **crimp straight into the existing `J6` JST PH**, so the speaker is
replaceable without soldering (D-148). **Default maximum software volume
−6 dBFS → 0.17 W, ≈ 57 mA**; 0 dBFS (0.68 W, 230 mA) exceeds the rated power and
must not be continuous (D-149).

**EMI: nothing fitted.** The MAX98357A data sheet's own Figure 14 shows
compliance with **12 in of speaker cable and no filter at all**, and AQROOT's
lead is half that. `R121`/`R122` are fitted 0 Ω — a plain wire — with
`C81`/`C82` 1 nF DNP as the no-respin recovery (D-150).

**ERC 45 → 45: zero added, zero removed.** 308 components, 0 duplicates,
0 without a footprint, 0 `*_TBD` nets.

**No new item requires a CTO decision.** Every change sits inside the brief's own
instructions. **B-61–B-64 opened**; the microphone is confirmed in live
distributor stock, the speaker is **not**, and is carried as B-61 rather than
called confirmed.

Full analysis:
[`audits/2026-08-23-s1-audio-implementation.md`](audits/2026-08-23-s1-audio-implementation.md).

</details>

<details>
<summary>Superseded — the ~49% assessment (FBV2-S1-005)</summary>

**Raised 47% → 49% by FBV2-S1-005.** **No gate in the twelve-gate table passed.**
The task gate **FBV2-S1-I2C-IMU = PASS** (2026-08-23).

**First, a correction to a number this file has been repeating.** FBV2-S1-004,
004B and 004C all quote **"ERC 68"**. The stored reports do not say that — they
say **46**. The *deltas* those tasks reported ("zero added, zero removed") are
correct and reproducible; only the absolute figure was wrong, and it has been
carried for three tasks. **Sheet `04`'s migration genuinely took the count from
64 to 46.** Separately: `kicad-cli sch erc --severity-all` also counts
**Exclusions** and reports 104 on the same unmodified design. Every number in
this programme is `--severity-error --severity-warning`. **Compare like with like
or the gate is meaningless.**

**Nothing on Sheet 05 was wrong, and that is the honest headline.** The brief said
not to copy Beta-DM's BMI270 straps blindly. Every one of them was re-derived from
`BST-BMI270-DS000-08` Rev 1.6 — `SDO`→GND for 0x68, `CSB`→VDDIO because Bosch
recommends hard-wiring it, `ASDx`/`ASCx`→VDDIO with Bosch's explicit ***"Do not
connect to GND"***, `INT2`/`OCSB`/`OSDO` DNC as instructed, 100 nF at pins 5 and 8
— and they were all already correct (D-136).

**The one real defect was on the bus, not the IMU.** Measured from the netlist, the
internal I²C bus carries **≈ 85 pF worst case** (two expanders, the IMU, the fuel
gauge, the TCA9517A A-side, the touch controller through the 50-pin display flex,
two test points, ~120 mm of trace). At **4.7 kΩ** that is `t_r` = **338 ns — past
the 300 ns fast-mode limit** — while a typical 60 pF gives 239 ns and passes.
**A part that works on the bench and fails on the unit with the longest flex.**
`R19`/`R20` → **2.2 kΩ**: **158 ns, 47 % margin**, sink current **1.32 mA** against
a 2 mA BMI270 / 6 mA expander / 3 mA specification floor (D-139).

**`0x68` is now escapable by rework instead of a respin.** `SDO` was hard-wired to
GND, so an address collision meant cutting a trace at a 0.25 mm pad. It is now
`R118` 0 Ω **FIT** to GND (0x68) and `R119` 0 Ω **DNP** to `+3V3` (0x69), **fit one
only**. `0x68` is the most collision-prone address on a community bus — MPU6050,
ICM-20948 and the DS3231 RTC all default to it, and those are exactly what a
hobbyist accessory is built from (D-140).

**B-44 CLOSED.** The BMI270 pad drive is **`IOH`/`IOL` ≤ 2 mA**, and the strap load
draws **323 µA** — 6× inside spec.

**GPIO3 boot safety is now a timing proof, not a margin argument.** `INT1_IO_CTRL`
resets to `0x00` (output disabled); firmware cannot enable it before the 8 kB
config upload; and the ESP32-S3 strap hold time is **`tH` = 3 ms** with GPIO3
defaulting to **Floating**, so `R110` alone defines the strap. **The IMU cannot
reach the strapping window.** The pull-down also *dictates* the firmware
configuration: **push-pull + active-high are mandatory and open-drain is
forbidden**, because an open-drain output into a pull-down never produces an edge.
GPIO3 = `RTC_GPIO3`, so EXT0/EXT1 deep-sleep wake works and active-high is the
right polarity (D-137).

**The IMU stays permanently powered. No load switch** — it would save ≈ 9 µA and
destroy wake-on-motion (D-141).

**The BMI270 land pattern is verified and its "DO NOT ROUTE" gate is discharged.**
§8.3 is a raster drawing, so it was rendered at 12× and measured programmatically:
every printed dimension reproduces — 0.5, 0.25, 0.475, 0.675, 0.925, 3.0, 2.5 — as
does the peripheral pin order, which is the error that would have been fatal and
silent (D-143).

**ERC 46 → 45: zero added, one removed.** 303 components, 0 duplicates, 0 without a
footprint.

**One item needs a CTO decision: O-4** — evaluate a **TCA4307-class hot-swap I²C
buffer with stuck-bus recovery** in place of `U16`, at Sheet 09 migration. See the
audit; nothing is implemented.

Full analysis:
[`audits/2026-08-23-s1-i2c-imu-implementation.md`](audits/2026-08-23-s1-i2c-imu-implementation.md).
Registry:
[`architecture/I2C_ADDRESS_REGISTRY.md`](architecture/I2C_ADDRESS_REGISTRY.md).

</details>

<details>
<summary>Superseded — the ~47% assessment (FBV2-S1-004C)</summary>

**Raised 45% → 47% by FBV2-S1-004C.** **No gate in the twelve-gate table passed.**
The task gate **FBV2-S1-NFC-MATCHING = PASS** (2026-08-23).

**Two defects were found that were not on the brief.**

**The RX divider would have over-driven the receiver.** At full field the antenna
sits at 24.8 V pk-pk per side; the placeholder 47 pF / 220 pF divider would have
put **≈ 4.4 V pk-pk on `RFI1`/`RFI2` against a 3.0 V regulated rail**. That is
part stress, not mistuning. The new 27 pF / 620 pF divider gives **≈ 1.0 V pk-pk,
over 3× headroom** (D-135).

**The E24 grid is brutally steep at the series matching capacitor.** 270 pF and
300 pF per leg bracket the ideal 284 pF and give **16 Ω and 68 Ω** differential —
a 4× swing in load for one step on the grid. **300 pF was chosen on purpose**, the
low-current side: an under-driven antenna is a component swap, an over-driven one
risks the driver and the rail on first power-up (D-134).

**The antenna variant is corrected — A → B.** `FXC.46.52.0075X.**B**.dg`, reverse
ferrite, bonds **adhesive-side to the inner rear shell** and reads outward with the
ferrite facing **inward**. With the A version the ferrite would have sat between
the coil and the tag (D-131). **Board unaffected — `J7`, cable and connector are
identical.**

**B-56 CLOSED:** the EMC filter moved from a cut-off of **7.6 MHz — below the
carrier** — to **20.1 MHz**, outside AN5276's forbidden 13–14 MHz band.

**ERC 68 → 68: zero added, zero removed.** *(the 68 is a transcription error corrected in FBV2-S1-005 — the stored reports say 46 → 46. The delta was right.)*

Full analysis:
[`audits/2026-08-23-s1-nfc-matching-closeout.md`](audits/2026-08-23-s1-nfc-matching-closeout.md).

</details>

<details>
<summary>Superseded — the ~45% assessment (FBV2-S1-004B)</summary>

**Raised 43% → 45% by FBV2-S1-004B.** **No gate in the twelve-gate table passed.**
The task gate **FBV2-S1-NFC-ANTENNA-LOCK = PASS** (2026-08-23).

**B-06 is CLOSED.** *"NFC is undesigned, not merely unrouted"* has been true since
the pre-design audit and is not true any more: **crystal, matching topology,
antenna, connector and supply all exist**. What remains is tuning, which is a bench
activity, not a design gap.

**Two locks and a proven mate.** NFC IC = **`ST25R3916-AQET`**, non-B (**P-17
CLOSED**). NFC antenna = **Taoglas `FXC.46.52.0075X.A.dg`**, off-board, 46 mm
circular flex with integrated ferrite (**B-53 CLOSED**). Board side =
**`J7` JST `BM02B-ACHSS-GAN-ETF`**, whose mating housing `ACHR-02V-S` is exactly
the ACH(F) connector Taoglas fits to that antenna's cable — so **the antenna is
replaceable without soldering**.

**The matching network now has one number that can be trusted**: `R_q` = 1 Ω per
leg, derived from the antenna alone, taking `Q` from 58 to 25.8. `C_s` and `C_p`
follow from an L-match with a stated assumption. **The EMC pair was deliberately
NOT re-derived and is flagged as unbuildable as it stands** (**B-56**) — the whole
network waits on `STSW-ST25R004`.

**ERC 68 → 68: zero added, zero removed.** *(the 68 is a transcription error corrected in FBV2-S1-005 — the stored reports say 46 → 46. The delta was right.)*

Full analysis:
[`audits/2026-08-23-s1-nfc-antenna-closeout.md`](audits/2026-08-23-s1-nfc-antenna-closeout.md).

</details>

<details>
<summary>Superseded — the ~43% assessment (FBV2-S1-004)</summary>

**Raised 40% → 43% by FBV2-S1-004.** **No gate in the twelve-gate table passed.**
The task gate **FBV2-S1-RADIOS-NFC = PASS** (2026-08-23).

**This is the first migration task to REDUCE the project's error count.** ERC went
**4 errors → 2**, total **86 → 68**, with **zero added and eighteen removed** — and
it did so by deleting placeholder architecture, not by suppressing checks.

**Zero `*_TBD` nets remain anywhere in the project.** Sheet 04 alone retired
fourteen. NFC stopped being a promise: a real **27.12 MHz crystal** (`Y1`, LCSC
`C362365`) and a real **differential matching topology** now exist, with every value
labelled `TUNE` because they cannot be finalised without a measured antenna.

**B-41 is CLOSED** — `U9` `VDD`/`VDD_TX` finally sit on `NFC_SUPPLY`, so the 3.3 V
FIT / 5 V DNP select built in FBV2-S1-001 now drives something.

**RF architecture locked (D-118):** 433 MHz **internal** Taoglas `FXP450.07.0100C`
(mating **proven**, not assumed), 915 MHz **external** to a top-panel **SMA female**
bulkhead. Neither band puts a single millimetre of RF trace on the board.

**Two items are recommended, not locked, and need CTO sign-off:** **P-17** (keep the
non-B ST25R3916 — it is the only one of the two with a JLCPCB path) and **B-53** (NFC
antenna architecture — recommendation is a purchased flex + ferrite).

Full analysis:
[`audits/2026-08-23-s1-radios-nfc-implementation.md`](audits/2026-08-23-s1-radios-nfc-implementation.md).

</details>

<details>
<summary>Superseded — the ~40% assessment (FBV2-S1-003)</summary>

**Raised 37% → 40% by FBV2-S1-003.** **No gate in the twelve-gate table passed.**
The task gate **FBV2-S1-DISPLAY-SD = PASS** (2026-08-23).

**The most valuable thing this task produced is a fault it found.** The inherited
`J1` still carried the **2.8-inch panel's pin table** while its Value and Footprint
already read FH69. Against the locked `ER-TFT035IPS-6` it was wrong in **two
independent dead-on-arrival ways**: the backlight anode and cathode were reversed
(pin 1 is LEDA, not LEDK), and the SPI clock and data/command lines were swapped
(pins 36/37). **Neither is visible from a pin count, a connector MPN or an ERC
run.** A new symbol was authored with the vendor pin table verbatim.

`R111` is **FITTED** (D-111), closing the GPIO45 item. **B-43 is CLOSED with a
primary source** — the TPS61169 `CTRL` pin has a **300 kΩ internal pull-down**, so
it cannot raise the GPIO46 strap under any condition (D-116). **B-32 and B-28 are
also closed**, the latter with `R112` **DNP** rather than fitted, because the
display SDO risks the microSD to gain a feature AQROOT never uses.

**ERC: 4 errors → 4 errors, the error report byte-identical to after FBV2-S1-002.**
Total 63 → 64.

Full analysis:
[`audits/2026-08-23-s1-display-sd-implementation.md`](audits/2026-08-23-s1-display-sd-implementation.md).

</details>

<details>
<summary>Superseded — the ~37% assessment (FBV2-S1-002)</summary>

**Raised 34% → 37% by FBV2-S1-002.** **No gate in the twelve-gate table passed.**
The task gate **FBV2-S1-MCU-CORE = PASS** (2026-08-23).

**Three CTO pending decisions closed and a second sheet migrated.** `R95` locked at
**560 Ω** (D-105) and the LTC4368 OV trip **derived** to **4.63 V** from the
datasheet's 492.5/500/507.5 mV threshold rather than typed in (D-104). The blanket
"no scripted KiCad edits" rule is superseded by an **eight-condition** standing
process rule (D-107). `02_MCU_CORE` carries the v2 GPIO architecture:
**GPIO38 = `NATIVE_A`**, **GPIO47 = `NATIVE_B`**, **GPIO46 = `DISP_BL_CTL`** with a
dedicated strap pull-down and an isolation link, **GPIO43 withdrawn** from the
community port, and **GPIO3's missing strap pull added — B-09 CLOSED.**

**ERC: 5 errors on the Beta-DM baseline → 4. Zero new errors; `02_MCU_CORE` reports
nothing at all.** Warnings 55 → 63, all eight being root-sheet `isolated_pin_label`
entries on cross-sheet signals whose far end is an unmigrated sheet. **They were
left standing on purpose** — clearing them by adding a test point to an orphaned net
is the same anti-pattern as a `PWR_FLAG` that hides a missing driver.

**Honest accounting on B-27.** 680 Ω was not arbitrary: it was exactly the value
that produced B-27's recorded ≈ 13 mA single-fault ceiling. Locking 560 Ω raises
that ceiling to **≈ 15.9 mA nominal / ≈ 16.6 mA worst case**, and **B-27 is amended
in place rather than left reading a number that is no longer true.**

Full analysis:
[`audits/2026-08-23-s1-mcu-core-implementation.md`](audits/2026-08-23-s1-mcu-core-implementation.md).
Measured pin ledger and strap audit:
[`architecture/GPIO_LEDGER.md`](architecture/GPIO_LEDGER.md).

</details>

<details>
<summary>Superseded — the ~34% assessment (FBV2-S1-001)</summary>

**Raised 31% → 34% by FBV2-S1-001.** **No gate in the twelve-gate table passed.**
The task gate **FBV2-S1-POWER-TREE = PASS** (2026-08-23), on the same basis as
FBV2-DISP-LOCK and FBV2-COMM-LOCK before it.

**This is the first Full Beta v2 design-file work in the programme.**
`hardware/beta-v2/` exists, forked from Beta-DM with a **re-runnable**
byte-equivalence proof, and `01_power_tree.kicad_sch` carries the Full Beta v2
power architecture: reverse protection P2 with `U18` LTC4368-1, autonomous
dead-cell recovery, both accessory rails, the NFC no-respin source select, and
`VBUS_PRESENT` telemetry. 136 parts, all with footprints assigned. **B-01 is
closed at schematic level** — `BAT_CONNECTOR_P` is no longer a one-pad net.

**Why this is +3% and not more.** `01_POWER_TREE` is one sheet of nine, and it is
the only one carrying the v2 architecture; the other eight are byte-equivalent
copies of Beta-DM. Assigned footprints are **not verified** footprints. And the
PCB is untouched — `aqroot-Beta-v2.kicad_pcb` is still bit-identical to the
Beta-DM board and does not match this schematic.

**ERC: zero introduced.** Beta-DM baseline **58** → Beta-v2 **55**, lists diffed
rather than counted; three inherited violations retired, none added. That is
**not** "ERC clean" — 55 inherited violations remain on the unmigrated sheets and
belong to FBV2-S2.

**One locked decision had been contradicted and is corrected**: `U18` LTC4368-1
carried a **DFN-10 exposed-pad** footprint against a package policy that forbids
bottom-terminated parts anywhere in the battery-protection circuitry. Moved to
MSOP-10. **Two value deviations were found and deliberately NOT changed** — `R95`
680 R against a locked 560 R (**P-20**) and an `OV` trip of 5.05 V against a
documented ≈ 4.6 V (**P-21**). A value in a locked architecture is changed by a
ruling, not by a capture task.

Full analysis:
[`audits/2026-08-23-s1-power-tree-implementation.md`](audits/2026-08-23-s1-power-tree-implementation.md).

</details>

<details>
<summary>Superseded — the ~31% assessment (FBV2-COMM-002)</summary>

**Held at 31%.** FBV2-COMM-002 **corrected an error rather than adding progress**:
the connector locked by FBV2-COMM-001, Harwin `M20-7881242`, turned out to be
obsolete, and has been replaced by Samtec **`BCS-112-S-D-HE`**. The percentage does
not rise for repairing something that should not have been recorded as locked.

It does not fall either. Nothing that was genuinely achieved has been lost: the
24-contact allocation, the pin ordering, both accessory rails, the expander
architecture and the firmware contract all stand unchanged, and the replacement is
better on every measured axis — active and next-day stocked, a lower 5.33 mm
profile (Z spare 0.70 mm → **3.47 mm**), 4.6 A per contact, and extended-life
plating available. Three CTO opportunity rulings (O-1, O-2, O-3) were also
implemented.

**The percentage rule was applied honestly in both directions**: a correction is
not progress, and a corrected error is not a regression in what was actually built.

</details>

<details>
<summary>Superseded — the ~31% assessment as first written (FBV2-COMM-001)</summary>

**No gate in the twelve-gate table passed.** FBV2-COMM-LOCK is a *task* gate, not
one of the twelve, and it **PASSED** (2026-08-23, FBV2-COMM-001).

Raised three points. This was **the last architecture closeout before schematic
implementation**, and it earns three points for a specific reason: it closes the
final three pending CTO decisions that gated a schematic sheet — **P-02** (the
connector), **P-15** (the rail budget) and **P-16** — plus the long-standing
**B-08** WAKE-isolation defect, and it does so with a purchasable connector MPN, a
locked 24-contact pin ordering with a written mis-insertion proof, two protection
ICs verified line by line against their datasheets, and a binding firmware
mutual-exclusion contract.

It is **not** more than three because nothing was built, `hardware/beta-v2/` still
does not exist, and the design now has **zero spare expander capacity anywhere**
(B-37) — a constraint that will bite the first time a new I²C-mediated signal is
wanted.

</details>

<details>
<summary>Superseded — the ~28% assessment (FBV2-DISP-002)</summary>

**No gate in the twelve-gate table passed.** FBV2-DISP-LOCK is a *task* gate, not
one of the twelve, and it **PASSED** (2026-08-23, FBV2-DISP-002).

Raised three points, and **only** three, for a specific reason: this is the first
task in the programme that locked a **physical part with a purchasable MPN, a
mating connector proven from both manufacturers' drawings, and a driver circuit
re-derived to component values.** Everything before it was architecture on paper.
The three points are for **M-06 and M-07 closing**, which removes the last gate on
FBV2-S1 — sheet `03_spi_a_display_sd` is now unblocked and every sheet in the
migration can start.

It is **not** more than three because nothing was built: no schematic exists, no
board exists, `hardware/beta-v2/` does not exist, and the mating pair is proven on
paper rather than by a mated sample.

</details>

<details>
<summary>Superseded — the ~25% assessment (FBV2-MECH-001)</summary>

**FBV2-A2 PASSED** (2026-08-22, FBV2-MECH-001). Three of twelve gates now pass.
Every dimensional dependency that could have forced a late PCB redesign is
resolved: cavity, PCB envelope, battery, NFC/battery separation, connector exit,
antenna-vs-IR, USB/microSD, acoustics and mounting bosses.

Raised five points and **no more**. All three passed gates remain paper gates —
**no schematic exists, no PCB exists, no CAD exists**, and every mechanical figure
is TARGET (derived) rather than LOCKED (measured in CAD).

</details>

<details>
<summary>Superseded estimates</summary>

**~28%** — FBV2-DISP-002. **~25%** — FBV2-MECH-001. **~20%** — FBV2-PWR-002.
**~15%** — FBV2-PWR-001. **~13%** — FBV2-ARCH-002. **~10%** — FBV2-ARCH-001.
**~8%** — FBV2-DOC-001.
</details>

### Previous estimate: ~20%

**FBV2-A1 PASSED** (2026-08-22, FBV2-PWR-002) — the first gate to pass since
FBV2-A0, and the largest remaining architecture unknown. All six criteria closed;
all 13 power/fault cases have defined safe behaviour; no power-tree branch remains
TBD.

Raised five points, and **deliberately not more.** Two of twelve gates have
passed and both are paper gates — no schematic exists, no board exists, and
**FBV2-A2 (mechanical) has not started**, with an internal cavity that has never
existed in this repository. Architecture certainty is not the same as progress
toward a working unit.

<details>
<summary>Superseded estimates</summary>

**~15%** — FBV2-PWR-001. **~13%** — FBV2-ARCH-002. **~10%** — FBV2-ARCH-001.
**~8%** — FBV2-DOC-001.
</details>

### Previous estimate: ~15%

Raised from ~13% by **two points** for FBV2-PWR-001: five of the six FBV2-A1
criteria are now closed, the complete battery-protection topology is specified
element by element, and P-13 was closed outright by primary-source evidence.

**No gate passed. FBV2-A1 remains FAIL — but one CTO decision now closes it.**

<details>
<summary>Superseded estimates</summary>

**~13%** — FBV2-ARCH-002. **~10%** — FBV2-ARCH-001. **~8%** — FBV2-DOC-001.
</details>

### Previous estimate: ~13%

Raised from ~10% by **three points** for FBV2-ARCH-002: four of the eight
FBV2-A1 criteria are now genuinely resolved, the mandatory power/fault state
table exists, and the NFC no-respin fallback is fully specified down to a
FIT/DNP matrix and a rework procedure.

**No gate passed. FBV2-A1 explicitly CANNOT PASS** — see the gate table.

<details>
<summary>Superseded estimate</summary>

**~10%** — recorded 2026-08-22 after FBV2-ARCH-001.
</details>

### Previous estimate: ~10%

Raised from ~8% by **two points only**, and only because FBV2-ARCH-001 closed
four pending CTO decisions (P-03, P-05, P-06, P-08, P-09) and verified nine
architecture facts against vendor datasheets.

**No gate passed.** FBV2-A1 is still IN PROGRESS. The estimate stays deliberately
low because the largest remaining unknowns — mechanical cavity, connector freeze,
reverse-polarity architecture, NFC supply topology — are all still upstream of
any drawing, and three of the four need a CTO decision rather than engineering
work.

---

## Gate table

| gate | description | status | date |
|---|---|---|---|
| **FBV2-A0** | Pre-design audit | **PASS** | 2026-08-22 |
| **FBV2-A1** | CTO architecture decisions | **PASS** | 2026-08-22 |
| **FBV2-A2** | Mechanical interface freeze | **PASS** | 2026-08-22 |
| **FBV2-S1** | Schematic migration / rearchitecture | **PASS 2026-08-23.** `hardware/beta-v2/` was forked from Beta-DM with a re-runnable byte-equivalence proof, and **all nine sheets** — `01_POWER_TREE`, `02_MCU_CORE`, `03_SPI_A_DISPLAY_SD`, `04_SPI_B_RADIOS_NFC`, `05_I2C_DEVICES`, `06_AUDIO`, `07_IR`, `08_BUTTONS_EXPANDERS` and `09_COMMUNITY_HEADER` — now carry the v2 architecture (FBV2-S1-001 … 009). **All nine task gates PASS and `fork_equivalence.py`'s "still Beta-DM" list is EMPTY.** Closeout verified 321 components with 0 duplicates and 0 missing footprints, 224 nets with 0 `*_TBD`, the GPIO ledger re-read pin by pin with no boot-strap regression, three PCAL addresses at 0x20/0x21/0x22, the 24-contact allocation matching D-084, and **ERC 27 / 0 errors / 27**. **This gate is about the schematic and nothing else — it is not a fabrication-readiness statement.** | 2026-08-23 |
| **FBV2-S2** | ERC + footprint audit | **NOT STARTED** | — |
| **FBV2-P1** | Floorplan / placement | **NOT STARTED** | — |
| **FBV2-P2** | Routing | **NOT STARTED** | — |
| **FBV2-D1** | DRC / DFM / fab package | **NOT STARTED** | — |
| **FBV2-F1** | Fabrication / PCBA | **NOT STARTED** | — |
| **FBV2-B1** | Safe first power-up | **NOT STARTED** | — |
| **FBV2-B2** | Subsystem validation | **NOT STARTED** | — |
| **FBV2-B3** | Full showcase validation | **NOT STARTED** | — |

### Gate exit criteria

| gate | passes when |
|---|---|
| FBV2-A0 | A read-only audit pinned to a repository HEAD exists in `audits/`. **Met 2026-08-22.** |
| FBV2-A1 | Every item in the Pending CTO Decisions table of [CTO_DECISIONS.md](CTO_DECISIONS.md) is closed into a locked `D-xxx` ruling. |
| FBV2-A2 | Internal cavity X/Y/Z, wall thickness and PCB-to-wall clearance are published, and every dimensional dependency that could force a late PCB redesign is resolved. **Met 2026-08-22** via [mechanical/MECHANICAL_INTERFACE_SPEC.md](mechanical/MECHANICAL_INTERFACE_SPEC.md). ⚠ **`tools/check_mechanical_consistency.py` still reports UNKNOWN** — it parses the Field Slate v5 block, and FBV2-MECH-001 had **no authority** to modify `tools/` or the Field Slate. Reconciling the guard is a follow-up task, not a gate condition, because the guard reads a Beta-DM-era document rather than the v2 spec. |
| FBV2-S1 | `hardware/beta-v2/` exists, forked from Beta-DM with a byte-equivalence proof, and every schematic change in the migration order is landed. **Half met 2026-08-23:** the fork and its proof exist (`hardware/beta-v2/checks/fork_equivalence.py`, `hardware/beta-v2/reports/FBV2-S1-fork-equivalence.md`); **7 of 9 sheets** are landed. |
| FBV2-S2 | 0 ERC errors, 0 schematic-parity issues, and every project-library footprint verified against a vendor drawing with a per-footprint pad-overlap assertion. |
| FBV2-P1 | Outline derived from the published cavity; all mechanical keepouts instantiated; IR TX/RX escapes proven at placement time; U3/connector cluster placed at the right-side exit. |
| FBV2-P2 | Ratsnest zero including GND; no pin-specific budget exceptions. |
| FBV2-D1 | 0 DRC errors, 0 unconnected, same-net hole-to-hole checked at warning level, POFV control regenerated, BOM/CPL diffed against the MPN ledger rather than regenerated blind. |
| FBV2-F1 | Boards and assemblies received against a confirmed production file set. |
| FBV2-B1 | `+3V3` overshoot below 3.6 V; reversed-battery-with-USB fault test passed; no smoke, no thermal runaway. |
| FBV2-B2 | Each subsystem independently demonstrated. |
| FBV2-B3 | Full showcase demonstration on real hardware. |

---

## Current blockers

Carried from the pre-design audit (2026-08-22). Each maps to a pending CTO
decision or a mandatory gate.

### Fabrication blockers — cannot release to fab

| # | blocker | evidence | owner |
|---|---|---|---|
| **B-01** | **Reverse-polarity protection does not exist.** `BAT_CONNECTOR_P` is a single-pad net (`J4.1` only). Nothing bridges it to `BAT_PROTECTED_P`. The Design Decisions Log marks the block `DO NOT ROUTE. DO NOT RELEASE TO FAB.` A board built as-is will not run from battery at all. | Measured from the PCB pad-to-net map | CTO (P-01) |
| **B-02** | **Power / self-damage gates unresolved.** Regulator overshoot, NFC boost OVP, accessory-power reverse blocking, charger thermals, RF/audio/IR brownout budget. | Audit section 12 | Engineering + CTO (D-072) |
| **B-03** | **Footprint audit not performed.** Several project-library footprints are custom or explicitly marked "intended, not verified" — TCA9535PWR, `J5` Samtec, ST25R3916, MK1 custom pad ring, Ebyte modules, Coilcraft, TPS63020, MAX17048, BMI270, Hirose FPC. | Audit section 12 item 13 | Engineering (FBV2-S2) |

### Design blockers — cannot start placement

| # | blocker | evidence | owner |
|---|---|---|---|
| **B-04** | **Internal enclosure cavity has never been published.** `INTERNAL_CAVITY_MM: not published`, `WALL_THICKNESS_MM: not published`, `PCB_FIT_STATUS: UNVERIFIED`. The v2 board outline is a derived number and cannot be derived without it. | Field Slate v5 dimension authority table | CTO (P-07) |
| **B-05** | **20-pin connector architecture not locked.** C1/C2/C3 proposed, none approved. | Audit sections 6-7 | CTO (P-02) |
| **B-06** | **NFC is undesigned, not merely unrouted.** No 27.12 MHz crystal exists in the BOM; no matching network; no antenna. 13 dangling `*_TBD` nets on U9. | Measured: 13 single-pad nets on U9 | CTO (P-03, P-04) |

### Architecture defects — must be resolved in migration

| # | defect | evidence |
|---|---|---|
| ~~**B-07**~~ | ~~NFC rail architecture defect.~~ **RETIRED 2026-08-22 — the finding was wrong.** DS12484 Rev 3 p. 39 requires VDD and VDD_TX to share one supply; Tables 118/119 cap their difference at ±0.3 V abs max / ±0.2 V operating. The as-built assignment is **correct**. The residual sequencing question is now **P-10**. | ST25R3916 DS12484 Rev 3, Tables 2 / 118 / 119 |
| ~~**B-08**~~ | ~~WAKE line has no isolation gate.~~ **BUILT 2026-08-23 (FBV2-S1-009, D-187):** `Q10` 2N7002 with `R63` 10 k to `ACC_3V3_SW`, orientation verified. | Measured: `WAKE_GATE_S` = `Q10.2`, `R63.2`, `R66.1` |
| **B-09** | **GPIO3 has no strap-defining pull.** Required by the pin map, not implemented. Hazard currently low (the S3 ignores the GPIO3 strap unless `JTAG_SEL_ENABLE` is burned) but it leaves a CMOS input floating at reset. | Measured: `BMI270_INT1_STRAP` = `R18.2`, `TP3.1`, `U1.15` |
| **B-10** | **Zero free native GPIO.** 29 assigned + 2 strap test pads + 2 USB = 31 of 31 usable. | Measured from U1 pads |
| **B-11** | **GPIO18 / GPIO38 documentation mismatch.** The pin map states GPIO18 = SX1262 DIO1 and GPIO38 = NFC IRQ. The hardware is the reverse. | Measured from U1 pads |
| **B-12** | **Possible LoRa wake defect.** `SX1262_DIO1` on GPIO38 is not RTC-capable, so wake-on-LoRa-packet is impossible in the current pinout. | Consequence of B-11 |
| **B-13** | **RGB LED nets dangling.** `RGB_R/G/B_CTL` exist with one pad each; no LED part exists. | Measured: 3 single-pad nets |
| **B-14** | **RootProbe cannot connect.** `ROOTPROBE_IRQ_READY_N` has no header pin. | Measured: net = `R11.2`, `U2.20` |
| **B-15** | **No charge or VBUS telemetry.** `BQ25185_STAT1` reaches `TP6` only, `STAT2` reaches `TP7` only, `MAX17048_ALRT_N` reaches `TP11` only. No VBUS-present sense exists. The product cannot report charging state. | Measured from the PCB |

### Documentation defects

| # | defect |
|---|---|
| **B-16** | Field Slate v5 section 5 still lists "Volume +, Volume −, Power" on the right side. Volume controls have never existed electrically. The locked external layout text needs a CTO-approved correction so enclosure CAD is not driven by phantom controls. |

---

### FBV2-A1 gate assessment (2026-08-22, FBV2-PWR-002) — **PASS**

| criterion | status |
|---|---|
| Dead-cell recovery topology explicit | **YES** — Candidate B specified to component level: ratiometric bridge, thresholds, defaults, 3-input AND, FAULT handoff, full failure analysis |
| Main reverse protection single-FET-short tolerant | **YES** — P2, two back-to-back stages in **two separate packages**. Isolation, not fault-clearing time |
| All power/fault states have defined safe behaviour | **YES** — 13 of 13 |
| No additional power-tree branch remains TBD | **YES** — the recovery branch was the last one |

**FBV2-A1 = PASS.** Component-value optimisation (exact `R_LIM`, FET MPN, fuse
rating, divider trim) moves to schematic design.

**Next gate: FBV2-A2 — MECHANICAL INTERFACE FREEZE.** Long pole, nothing blocks
it. **Do not start FBV2-S1 before the placement constraints exist.**

<details>
<summary>Superseded — FBV2-A1 assessment (FBV2-PWR-001, FAIL)</summary>

### FBV2-A1 gate assessment (2026-08-22, FBV2-PWR-001)

| # | criterion | status |
|---|---|---|
| 1 | PCAL9535A choice closed | **YES** — D-061; no pin/package incompatibility found |
| 2 | GPIO38/GPIO47 closed | **YES** — D-063; DIO1 level-hold confirmed verbatim from Semtech §13.3.4 |
| 3 | NFC architecture closed | **YES** — D-055/D-056 |
| 4 | Community power architecture closed | **YES** — D-057/D-058 |
| 5 | 20-pin resource architecture closed | **YES** — D-062 |
| 6 | **Reverse-protection topology complete, no major new power-tree branch TBD** | **NO — P-11** |

**Verdict: FAIL.** Criteria 1–5 are closed and the reverse-protection topology
itself is complete (controller, dual N-FET, R_SENSE 15 mΩ, R_GATE 22 kΩ,
C_GATE 1 nF, UV recommended unused, OV divider, RETRY grounded, SHDN pull-up to
VIN, FAULT, fuse, clamp). **The dead-cell recovery branch (P-11) is a new
power-tree branch and is not chosen.** Per the CTO's instruction — *"Do not pass
the gate merely because a preferred idea exists"* — the gate is not passed.

**One decision closes it.** Selecting Candidate B or Candidate D closes criterion
6; P-12 then carries into the schematic phase as a bench item, since it changes
no topology.

</details>

### Blockers added or changed by FBV2-P2-000 (2026-08-24)

| # | item | status |
|---|---|---|
| **PM-1** | **ALL FOUR SWITCHING CONVERTERS HAVE THEIR INDUCTOR OFF THE IC.** `U12`/`L1` **12.96 mm**, `U13`/`L2` **28.56 mm**, `U21`/`L4` **30.50 mm**, `U17`/`L3` **45.90 mm**, against ≤ 5 mm. The backlight's `L3 → D8 → C44` boost loop is **≈ 76 mm around**, switching at 1.2 MHz to **up to 39 V** on an open-LED fault, down the left margin **13 mm from `MK1`**. All four inductors sit in the left-margin column at x ≈ 3 while their ICs are elsewhere | **OPEN — P2 ENTRY BLOCKER, CTO DECISION (D-236).** Loop area is a placement property; no routing repairs it |
| **PM-2** | **THE SINGLE-FAULT BATTERY-PROTECTION BLOCK IS DISPERSED OVER 96 mm** across three clusters. `LTC_GATE` **95.6 mm** (≈ 20 µA charge-pump node, damping 31–45 mm from the FETs), `BAT_SENSE` **96.5 mm** (1.5 A **and** the FET source reference), `LTC_OV`/`LTC_UV` 78.4/81.7 mm (**the battery trip points**, on 3.65 M / 510 k dividers), `VBRIDGE_TOP` 90.1, `VREF_TOP` 80.8, `REF_HO` 82.4 mm (2.2–3.65 MΩ dead-cell reference nodes; `REF_HO`'s two divider halves are **38 mm apart**). Total 1.5 A path ≈ **116.7 mm** | **OPEN — P2 ENTRY BLOCKER, CTO DECISION (D-236).** **The Kelvin sense itself is SOUND and D-049 is NOT compromised** — the recommendation moves parts, not topology. It also returns ≈ 0.13–0.18 W to **B-34** |
| **PM-3** | **THE NFC DIFFERENTIAL FRONT END IS NOT SYMMETRIC.** `NFC_MATCH_A` **24.18 mm** vs `NFC_MATCH_B` **34.21 mm** — 10 mm of asymmetry before a track is drawn; `L5`/`L6` **19.8 mm apart on opposite sides of `U9`**; antenna nodes 8.82 vs 12.49 mm; crystal load caps **13–15 mm from `Y1` on the far side of the IC** | **OPEN — P2 ENTRY BLOCKER, CTO DECISION (D-236).** With `R_q` 1.1 Ω/arm and Q ≈ 21 (D-204), routing cannot absorb it |
| **PT-1** | **`U11` BQ25185 dissipates ≈ 0.65 W while charging from INSIDE `BATTERY_SHADOW`**, doc (56.000, 32.000) on B.Cu, ≈ 10 mm inside the pouch envelope, in a sealed unvented enclosure against a 0–45 °C charge window | **OPEN, medium — ROUTING-STAGE ITEM (D-235).** Composes with PM-2 and B-34. **No thermal path may depend on the battery** |
| **P2-O6** | **The board file carries NO physical stackup object at all** (nor does Beta-DM's), so a fabricator builds to its own default and no impedance control is ordered | **OPEN, low — DFM / RELEASE ITEM (D-235).** Does not block routing: the one impedance-sensitive net is Full-Speed USB over ≈ 40 mm |
| **P2-R1** | **The 433 flex sits 0.2 mm outboard of the LEFT board edge** over doc Y 1.5 … 48.5, so board copper in X 0 … 3.0 of that band is an **aggressor into** it | **OPEN — ROUTING-STAGE ITEM (D-235).** Deliberately **not** instantiated as a rule area until PM-1 settles which parts occupy that band |
| ~~**P2-O5**~~ | ~~`.kicad_dru` references deleted E5/E6 rule areas~~ | **CLOSED 2026-08-24 (D-233), and it was 39 areas and 22 inert rules — not just the E6 pockets.** `checks/dru_probe.py` stops it recurring |
| ~~**B-63**~~ | ~~The PCB acoustic hole and the pad-4 paste pullback are not in the microphone footprint~~ | **STALE — already closed by D-203 and rebuilt by D-227. The register lists it twice; the later entry is wrong. Do not carry it forward** |
| ~~**B-64**~~ | ~~The PCB still carries `MK1` with the ICS-43434 footprint~~ | **STALE — closed by the FBV2-P1 rebuild; the PUI footprint is on the board, verified 2026-08-24. Do not carry it forward** |
| **B-34** | ≈ 0.70 W and ≈ 0.40 V in the BATFET + protection path at 1.75 A in a sealed enclosure | **OPEN, medium — unchanged, but now quantified further: PM-2's dispersal adds ≈ 0.13 W at 1.5 A / 0.18 W at 1.75 A on top, and PM-2 gives most of it back** |
| **O-5** | IR receiver AGC4 (`TSOP38438`) vs the Sony/SIRC protocol list | **OPEN — FIRST-ARTICLE ITEM, still needs a CTO ruling.** Receive-only; reverting is a `lib_id` change. **No routing impact**, classified and carried forward unchanged |

### Blockers added or changed by FBV2-COMM-002 (2026-08-23)

| # | blocker | status |
|---|---|---|
| ~~D-083~~ | **Harwin `M20-7881242` REJECTED as obsolete** — `harwin.com` returns HTTP 404 for it. The MPN had been *configured from the catalogue ordering scheme*, and FBV2-COMM-001 §15 had flagged exactly that risk | **CORRECTED.** Replaced by Samtec `BCS-112-S-D-HE` (D-093) |
| **D-096** | **New standing rule:** a part number configured from an ordering scheme is a hypothesis, not a selection. Every MPN written into a locked document must first be confirmed against a live manufacturer or distributor record showing lifecycle and stock | **STANDING** |
| **B-39** | **Mating-cycle rating unconfirmed.** Only **100 cycles** is formally qualified for BCS; the **2 500-cycle** E.L.P. figure is **by similarity at 30 µin gold**. Confirm the rated count for `BCS-112-S-D-HE` with Samtec before production | **OPEN, medium.** Procurement |
| **B-40** | Which mating row terminates in which PTH row of the 7.87 mm pattern must be read off the Samtec print, not assumed | **OPEN, low.** FBV2-S2 |
| **B-29** | **Re-scoped.** The footprint must now be drawn to Samtec FIG 3 `BCS-1XX-XXX-D-HE`: 2 × 12 PTH, **2.54 mm within a row, 7.87 ± 0.05 mm between rows, 0.71 mm drill** — *not* interchangeable with any vertical 2×12 pattern | **OPEN, medium.** FBV2-S2 |
| ~~**B-37**~~ | Zero spare expander capacity | **RETIRED 2026-08-23 (D-175).** `RESERVED_SPARE` lives on `U23` P03 with `R130` and `TP41`, and eleven further `U23` pins are free |
| **M-09** | Connector body height | **DOWNGRADED to LOW.** Z column falls from 22.30 mm to **19.53 mm of 23.0 — 3.47 mm spare**; it is no longer the sole governing column. Confirm 5.33 mm against the Samtec 3D model at FBV2-P1 |
| **M-10** | Insertion load path | **DOWNGRADED.** ≈ **33 N average** (was ≈ 48 N max), peak higher. Enclosure boss still required (D-097) |
| **P-19** | The 24Cxx family spans `0x50`–`0x57`; only `0x50` is reserved. May need widening if multi-EEPROM accessories appear | **OPEN, low.** CTO, with P-18 |
| ~~O-1~~ | Wire-OR the `FLT` lines | **APPROVED and implemented** (D-094) |
| ~~O-2~~ | Accessory-ID EEPROM address `0x50` | **APPROVED and implemented** (D-095) |
| ~~O-3~~ | Share the accessory boost with the NFC fallback | **REJECTED and struck** (D-095) |

**Two NEW opportunities are flagged for a CTO ruling and were deliberately NOT
locked:** **N-1** publish an accessory reference design (footprint, the 4.34–6.35 mm
post-length rule, the detect-strap pattern, the shared-rail current rule, a board
template) — high value, documentation-only; **N-2** accessory retention — withdrawal
force is only ≈ 20 N average with no latch, so an enclosure detent or captive
fastener is worth considering.

### Blockers added or changed by FBV2-COMM-001 (2026-08-23)

| # | blocker | status |
|---|---|---|
| ~~P-02~~ | Freeze the 20-pin connector | **CLOSED** — the 20-pin architecture is **superseded**; the port is 2×12 / 24 active contacts, female, `Harwin M20-7881242` (D-081…D-085) |
| ~~P-15~~ | 3V3 rail budget under simultaneous worst case | **CLOSED** — binding mutual-exclusion contract MX-1…MX-9 (D-092) |
| ~~P-16~~ | Repurpose one XGPIO as `ACC_DETECT`? | **CLOSED** — dedicated contact (pin 23) and dedicated `U3` input (D-082/D-085) |
| ~~B-08~~ | **WAKE line has no isolation gate** — a shorted accessory pin can permanently block internal button wake | **CLOSED IN COPPER 2026-08-23 (FBV2-S1-009, D-187).** `Q10` 2N7002, gate on `ACC_3V3_SW`, **source to the connector and drain to the internal line** so the body diode blocks with the rail off. Until this task the gate existed only as a decision |
| **B-34** | ≈ **0.70 W of series loss and ≈ 0.40 V of drop** in the BQ25185 BATFET (115 mΩ) + reverse-protection path at 1.75 A, inside a sealed enclosure | **OPEN, medium.** FBV2-S1 thermal review |
| **B-35** | **`TPS22950C` `FLT` does not assert on plain current limiting** — only on thermal shutdown and reverse current. A hard short reaches TSD in tens of ms and is then reported; a **partial** overload is invisible to the host | **OPEN, documented.** Firmware contract |
| **B-36** | Accessory-initiated wake now requires `ACC_3V3_SW` to remain enabled during sleep — a consequence of the B-08 gate | **OPEN, policy.** FBV2-B2 |
| ~~**B-37**~~ | ~~ZERO spare expander capacity on BOTH `U2` and `U3`~~ | **RETIRED 2026-08-23 (FBV2-S1-009, D-175).** O-6 ratified: `U23` is locked architecture. **37 of 48 expander pins used, ELEVEN spare** plus the formal `RESERVED_SPARE`. The programme carried this constraint from its first audit |
| **B-38** | The 5 V boost inductor must be **1 µH with `I_sat` ≥ 3 A** to survive a fault at the load switch's worst-high limit | **OPEN, low.** FBV2-S1 |
| **M-09** | The **connector region is the new governing Z column** — 22.30 mm of 23.0 mm external, 0.70 mm spare | **OPEN.** FBV2-P1 |
| **M-10** | Up to **48 N** insertion force; the enclosure must carry it on a boss/rib | **OPEN.** Enclosure CAD |
| **P-18** | External-I²C segmentation | **UNCHANGED, NOW PRECISELY CHARACTERISED (FBV2-S1-005).** `U16`, `R49`/`R50`, `U15` and `D2`/`D3` are **all DNP** — there is no fitted external I²C path today, so the choice costs no rework. TI: *"the TCA9517A logic and all I/Os are powered by the `VCCB` pin"*, and `VCCB` = `ACC_3V3_SW`, so a de-asserted rail leaves the buffer **unpowered and high-Z on both sides** — harder than a mux. **The weakness is not the buffer, it is the location of its disable control**: `ACC_PWR_EN` is `U3` P17, behind the bus it protects. 9-clock recovery frees the common case for free; a hard short needs a `+3V3` power cycle, since an MCU reset does not reset the expanders. **Address collision is not solvable by any buffer** — closed by D-142 instead. Decision deferred to Sheet 09 via **O-4** |

**Three opportunities are flagged for a CTO ruling and were deliberately NOT
locked:** wire-OR the two `FLT` lines to recover one expander pin; reserve an I²C
address for an accessory-ID EEPROM; a DNP 0 Ω link letting the accessory boost also
serve the NFC 5 V fallback.

### Blockers added or changed by FBV2-DISP-002 (2026-08-23)

| # | blocker | status |
|---|---|---|
| ~~M-06~~ | Display MPN and FPC interface | **CLOSED** — `ER-TFT035IPS-6` + `ER-TPC035-6`; 50-pin, 0.50 mm, **bottom contact**, 0.30 ± 0.03 mm; FT6236 @ 0x38 (D-074/D-075) |
| ~~M-07~~ | Backlight driver re-derivation | **CLOSED** — TPS61169 retained from `+3V3`; `R69` = 1.87 R, `R70`–`R73` = 4 × 33 R; switch-peak margin 4.6× (D-079) |
| **B-28** | **ILI9488 `SDO` on the shared SPI-A bus is unverified.** Mitigated by design: fit a 0 R `R_SDO` isolation link plus a test point so the display can be made write-only without a respin | **OPEN, mitigated.** Closes at FBV2-B2 |
| **B-29** | **`J1` footprint must be redrawn** on the FH12-horizontal / FH52E standard land pattern (D-077) and verified with a per-footprint pad-overlap assertion against **both** connector drawings | **OPEN.** Closes at FBV2-S2 — folds into B-03 |
| **B-30** | The datasheet does not name which FPC pin feeds the FT6236 VDD. Immaterial here — VDDI, VCI and the CTP supply are all `+3V3` | **OPEN, informational.** First article |
| **B-31** | Display FPC contact plating is not stated; Hirose recommends gold | **OPEN, low.** PO / first article |
| **B-32** | Confirm ≥ 4.7 µF X5R input decoupling local to `U17` `VIN` — input ripple current rises ~47 % | **OPEN, low.** FBV2-S1 |
| **B-33** | **The 2.3 mm `J1` cannot sit in the display shadow** (0.8 mm limit). It competes for the 70.04 mm below the panel with the D-pad, A/B and the mic aperture | **OPEN.** Placement coupling; closes at FBV2-P1 (tracked as M-08 in the mechanical spec) |

**Two MEDIUM procurement risks remain and neither is a design change:** the vendor
also sells a CST340 touch panel for this size, so the purchase order must name
`ER-TPC035-6`; and the datasheet carries a "Backlight Update" revision, so
Rev 2.0 (18-Aug-2025) must be archived in-repo and cited by revision in the MPN
ledger.

### Blockers added or changed by FBV2-PWR-002 (2026-08-22)

| # | blocker | status |
|---|---|---|
| ~~B-20~~ | Dead-cell lockout created by the reverse protection | **CLOSED** — autonomous hardware-qualified recovery branch (D-065), specified to component level. No firmware dependency |
| ~~B-21~~ | Shorted pass FET reproduces the guarded fault | **CLOSED by isolation** — P2, two stages, two packages. The old fuse+clamp compliance argument is **withdrawn as invalid** |
| ~~B-23~~ | PCAL9535A facts unverified | **CLOSED** — CTO verified NXP Rev 2 (D-066). Land-pattern audit remains a separate pre-fab gate |
| **B-26** | **Pack-protector release current.** Recovery injects ~8 mA; a 1S protector needing more than ~10 mA to release its over-discharge latch would not be revived | **OPEN — part-dependent.** Verify against the chosen pack. Does not change topology |
| **B-27** | **Recovery branch is not tolerant to every single failure** — four failures each enable current into a reversed cell | **ACCEPTED, BOUNDED.** `R_LIM` caps every case at ≈13 mA (~0.007 C); `D_REC` keeps the branch unidirectional; the fault is self-annunciating |

<details>
<summary>Superseded — FBV2-A1 gate assessment (FBV2-ARCH-002)</summary>

### FBV2-A1 gate assessment (2026-08-22, FBV2-ARCH-002)

| # | criterion | status |
|---|---|---|
| 1 | 20-pin resource architecture resolved | **YES** — 11 XGPIO + 2 native + 2 I²C + 1 WAKE + 1 switched power + 3 GND = 20 |
| 2 | Expander family resolved | **NO** — PCAL9535A pin table not retrievable from a primary source |
| 3 | Native GPIO pair resolved | **NO** — GPIO38 gated on unverified SX1262 DIO1 level-hold behaviour |
| 4 | Default NFC architecture resolved | **YES** — 3.3 V, `sup3V`, VDD = VDD_TX = `NFC_SUPPLY`, VDD_IO = `+3V3` |
| 5 | NFC no-respin fallback resolved | **YES** — FIT/DNP matrix + rework procedure complete |
| 6 | Community accessory power resolved | **YES** — TPS22950C, permanent `+3V3` pin removed |
| 7 | Battery/reverse protection resolved at topology level | **NO** — dead-cell recovery and inrush/latch interaction both change the power tree |
| 8 | No unresolved issue can change the power-tree architecture | **NO** — P-11 adds a switched path across the pass FETs plus an ADC divider |

**Closing actions:** three of the four gaps are document reads (PCAL9535A pin
table; SX126x + E22 IRQ sections). The fourth is one CTO decision (P-11) plus one
protoboard experiment (P-13).

</details>

### Blockers added or changed by FBV2-S1-004C (2026-08-23)

| # | blocker | status |
|---|---|---|
| ~~**B-56**~~ | EMC filter values inconsistent; cut-off below the carrier | **CLOSED.** 39 nH / 100 pF → **f_c = 20.1 MHz**, outside AN5276's forbidden 13-14 MHz band. The old pair sat at **7.6 MHz** and also presented 18.7 Ω of series reactance that was perturbing the match |
| ~~**B-48**~~ | AN5276 not retrieved; the driver target impedance was an assumption | **CLOSED ON SUBSTANCE.** ST's design rules were obtained and applied and the target is now **derived from the D-130 current budget** (≈ 36 Ω differential) rather than assumed. **The Rev 6 PDF still would not load in this environment** — see B-57 |
| **B-57** | **`STSW-ST25R004` / eDesignSuite run against a MEASURED antenna impedance has not been performed** | **OPEN, high.** Required before fabrication. It also closes most of B-55 |
| **B-58** | **`RFI` receiver linear-range spec not extracted** from DS12484 — the table is an image. The ≈ 1 V pk-pk working point is a conventional level with > 3× rail margin, not a figure quoted against a limit | **OPEN, medium.** First-article step 6 is a **pass/fail gate**, not an optimisation |
| **B-55** | `La`/`Rs`/`Q` not independently re-extracted | **OPEN, low.** The B-version published triple is coherent to ~3 % (`Q` 60.37 with 1.10 µH implies `Rs` 1.55 Ω, not 1.50 Ω). The network is re-derived from measurement anyway |
| **B-54** | ST25R3916 field current at 3.3 V | **OPEN, downgraded further.** The first-build network draws **≈ 60 mA at the driver**, comfortably inside the ≤ 150 mA budget. Measure at first article |

### Blockers added or changed by FBV2-S1-004B (2026-08-23)

| # | blocker | status |
|---|---|---|
| ~~**B-06**~~ | NFC is undesigned, not merely unrouted | **CLOSED 2026-08-23.** Crystal, matching topology, antenna, connector and supply all exist. What remains is tuning, not design |
| ~~**B-53**~~ | NFC antenna architecture undecided | **CLOSED by D-127** — off-board Taoglas `FXC.46.52.0075X.A.dg` on a JST ACH connector |
| ~~**P-17**~~ | ST25R3916 or ST25R3916B | **CLOSED by D-126** — `ST25R3916-AQET`, non-B |
| **B-54** | ST25R3916 field current at 3.3 V | **DOWNGRADED.** Conservative estimate **≤ 150 mA** derived; TPS63020 worst case ≈ 66-74 % of 2 A and MX-1 keeps the field off during LoRa TX. Datasheet figure or measurement still owed |
| **B-55** | **`La`/`Rs`/`Q` not independently re-extracted** — the Taoglas electrical table is an image, and a secondary summary quoted a conflicting triple that most likely belongs to the FXC.40 | **OPEN, low.** The supplied triple is internally consistent (`ωL/Rs` = 58.0 exactly). Confirm at first article; the match must be re-derived from measurement regardless |
| **B-56** | **EMC filter values are inconsistent with the new shunt.** `L5`/`L6` 220 nH against ~2 nF resonates near **7.6 MHz — below the 13.56 MHz carrier** | **OPEN, high. Do not build to the current EMC values.** Must come out of the `STSW-ST25R004` run |

### Blockers added or changed by FBV2-S1-004 (2026-08-23)

| # | blocker | status |
|---|---|---|
| ~~**B-41**~~ | `NFC_SUPPLY` has no consumer | **CLOSED 2026-08-23 by D-122.** `U9` `VDD`/`VDD_TX` moved off the Beta-DM boost output; the 3.3 V FIT / 5 V DNP select now drives something |
| **B-06** | NFC is undesigned, not merely unrouted | **LARGELY CLOSED.** A real 27.12 MHz crystal and a real differential matching topology exist; only the antenna choice (B-53) and the tuning values (B-48) remain |
| **B-48** | **AN5276 not retrieved** — every st.com fetch timed out. All matching and RX-divider values are **initial values** | **OPEN, high.** Run STSW-ST25R004 against a measured antenna impedance before the BOM gate. No value is presented as an ST reference figure |
| ~~**B-49**~~ | **CLOSED 2026-08-23 (D-195) — THERE WAS NEVER A RISK.** Ebyte ships both modules with **IPEX *and* stamp holes on the standard part number**; no variant selection exists to get wrong. Original text: **IPEX socket population must be confirmed with the supplier** for the exact ordered `U7`/`U8` MPNs — Ebyte sells IPEX and stamp-hole variants under similar numbers | **OPEN, high.** The entire zero-board-RF plan collapses if stamp-hole units arrive. Hard procurement deadline |
| **B-50** | FXP450 bend radius, adhesive, ground clearance and temperature not retrieved — the datasheet is image-based beyond page 1 | **OPEN, medium.** Mechanical input for FBV2-P1 |
| ~~**B-51**~~ | **CLOSED 2026-08-23 (D-195): Amphenol RF `095-902-568-150`, Part Status ACTIVE** — AMC R/A plug → SMA straight bulkhead jack, IP67, RG-178, 50 Ω, 150 mm, 6 GHz. **One assembly: pigtail and bulkhead in a single orderable part.** Original text: 915 MHz pigtail assembly MPN not selected — the interface is locked, the part is not (D-096) | **OPEN, medium** |
| **B-52** | Top-panel spacing between the SMA bulkhead and the IR apertures recorded (**≥ 8 mm**, pigtail clear of the optical path) but **no CAD exists** | **OPEN, medium** |
| ~~**B-53**~~ | **CLOSED 2026-08-23 (D-200) — STALE**, decided by D-131: purchased flex + ferrite, `FXC.46.52.0075X.B.dg`, **B variant** locked. Original text: **NFC antenna architecture undecided** — main-board loop vs purchased flex + ferrite vs daughter antenna | **OPEN, high.** Recommendation: **flex + ferrite**. A main-board loop needs a 45 × 45 mm ground-plane keepout on every layer with the battery behind it |
| **B-54** | **ST25R3916 field current at 3.3 V not extracted.** The NFC PA load has moved from `SYS` to `+3V3`, so the TPS63020 budget does not yet include it | **OPEN, high.** D-092's 58-66 % figure must not be quoted as covering the NFC field in this form |

### Blockers added or changed by FBV2-S1-003 (2026-08-23)

| # | blocker | status |
|---|---|---|
| ~~**B-43**~~ | TPS61169 `CTRL` internal-pull specification not retrieved | **CLOSED 2026-08-23 by D-116.** SNVSA40B: **`R_PD` = 300 kΩ internal PULL-DOWN**, `V_H`/`V_L` 1.2/0.4 V. `CTRL` can only pull GPIO46 down — the strap is safe by construction, not merely by margin |
| ~~**B-32**~~ | Confirm ≥ 4.7 µF X5R local to `U17` `VIN` | **CLOSED** — `C43` 4.7 µF 0805 on `+3V3` at `U17.5`, marked `4.7uF 10V X5R` |
| ~~**B-28**~~ | ILI9488 `SDO` on a shared bus | **CLOSED by D-114** — `R112` 0 Ω **DNP**, `TP36` on the panel side. Opposite default to the one FBV2-DISP-002 sketched, because fitting risks the microSD to gain a feature nothing uses |
| ~~**B-46**~~ | **CLOSED 2026-08-23 (D-196) — THE ASSUMPTION WAS RIGHT.** Molex SD-502570-001 Rev A note 4: CARD INSERTING POSITION = CLOSE, NO CARD = OPEN, so with the lever grounded and `R113` pulling up, **LOW = card present**. No firmware correction, no hardware change. Original text: **microSD detect-switch polarity assumed, not confirmed** — the Molex drawing would not load. `SD_CARD_DETECT_N` assumes switch-closes-on-insertion | **OPEN, low.** Firmware constant on a PCAL9535A input; never a board change |
| ~~**B-47**~~ | **RESOLVED 2026-08-23 (D-194) — OUTCOME B, NOT COMPATIBLE, AND D-077'S DROP-IN CLAIM IS STRUCK.** FH69 layout depth **7.38 mm** with a 0.30 × 1.23 land and top-and-bottom two-point contact; FH52E **4.6 mm**, bottom contact only, and its catalogue points at the **FH12** pattern. `J1` keeps the dedicated FH69 footprint and is **MANUAL ASSEMBLY** for the first five. Original text: **FH52E second source and land-pattern migration unresolved.** Drop-in equivalence was **not** asserted without both Hirose drawings, so `J1` stays on the FH69-dedicated pattern | **OPEN, medium. There is currently no JLCPCB assembly path for `J1`.** Settle at FBV2-S2, before placement |
| **B-29** | `J1` land pattern verified with a pad-overlap assertion | **STILL OPEN, advanced.** Pad geometry measured: 50 pads, 0.500 mm pitch with no drift, 24.500 mm span, 0.300 × 1.230 mm pads, 2 hold-downs. The assertion itself is FBV2-S2 |

### Blockers and opportunities CLOSED by FBV2-S2-002 (2026-08-23)

**FBV2-S2 = PASS.** Six items close. Full analysis:
[`audits/2026-08-23-s2-release-closeout.md`](audits/2026-08-23-s2-release-closeout.md).
New working document:
[`assembly/FIRST_FIVE_ASSEMBLY_PLAN.md`](assembly/FIRST_FIVE_ASSEMBLY_PLAN.md).

| # | item | status |
|---|---|---|
| ~~**B-03**~~ | Footprint audit | **CLOSED 2026-08-23 by D-201/D-202.** All eight remaining Tier-2 footprints compared **dimension by dimension** against retrieved manufacturer drawings — **23 of 28 critical footprints are now Tier 1** and none was promoted on the strength of its name. **The MAX98357A looked like a real defect and was not:** Maxim land pattern **90-0032 Rev E** is issued for `T1633-5`, `-5C` **and** `-7C` together and specifies **one** land for all three, so the 1.23 mm EP does not depend on which variant the part carries. **No project-local footprint was created** — both deviations are ≤ 0.05 mm and on the safe side. `Y1`'s land is an **exact** match to the vendor's Suggested Layout |
| ~~**B-63**~~ | Microphone acoustic footprint | **CLOSED 2026-08-23 by D-203.** **Ø1.05 mm NPTH** (the drawing's own pad-4 ring ID — not invented), **paste pullback** to a separate ID 1.25 / OD 1.65 annular aperture (the 0.10 mm pullback is a **declared stencil choice**, and the footprint says so), keepout marked on `B.Fab` + `User.Comments`, **bottom-port orientation** recorded as **M-14**. Re-parsed through `pcbnew` to confirm validity |
| ~~**B-70**~~ | NFC EMC inductor MPN | **CLOSED 2026-08-23 by D-204.** Murata **`LQW18AN39NG80D`**, `C2042966`, 270 in stock. **Not locked from headline specs:** SRF 74× the third harmonic, X_L 3.32 Ω as D-134 assumed, **DCR 0.20 Ω max against `R_q` 1.1 Ω drops network Q 25.3 → ≈ 21.4** — further into the safe side, but **the antenna must be bench-tuned with this exact part fitted**, and the first lever if the field is short is `R_q`, **not** 39 nH |
| ~~**B-54**~~ | ST25R3916 field current at 3.3 V | **CLOSED 2026-08-23 by D-205.** DS12484 Rev 3 retrieved through a mirror. **`I_AL-AM` max 26 mA (IC) + ≈ 60 mA (driver into D-134's actual network) → allocate 100 mA.** **The 350 mA / 500 mA figures are ABSOLUTE MAXIMA and were deliberately not used.** TPS63020 **63–71 % of 2 A**. **Binding guard rail: a `C_s` move to 270 pF would draw ≈ 257 mA and requires the rail budget to be re-run first** |
| ~~**B-71**~~ | LCSC / JLC / manual assembly classification | **CLOSED 2026-08-23 by D-206/D-207.** All **46 MPNs** classified against live JLCPCB parts-API state; **65 `LCSC` fields written into the schematic**. **Two hand-soldered THT parts per board, zero hand-placed fine-pitch or QFN.** Ten stock shortfalls + one library gap, all handled by **consignment**. **Six substitution traps caught**, including `BAT54W` offered for `BAT54WS` and a clone for the **battery reverse-polarity pass FETs**. **`J1` improves to machine-placed** — JLC stocks the genuine Hirose. ***CORRECTED 2026-08-23 (D-211): the `BAT54W` trap was recorded as "single diode vs series pair". `BAT54WS` IS NOT A SERIES PAIR — SOD-323 is a two-terminal package and `D10`–`D12` are each one independent diode. `BAT54W,115` is wrong because it is SOT-323 (SC-70), a FOOTPRINT mismatch.*** |
| ~~**O-8**~~ | 915 MHz external antenna | **CLOSED 2026-08-23 by D-209.** Taoglas **`TI.92.2113`** verified against **SPE-19-8-076/A**. Every expectation in the CTO ruling checks out. **The marketed "2 dBi" is the bent-configuration peak — average gain is negative in both orientations, so budget the link with the average.** No hardware or schematic change required |
| — | **DNP hygiene** | **D-208.** Eight DNP parts still had **no recorded reason**: the six-part NFC 5 V boost branch (`U13`, `L2`, `R44`, `R45`, `C34`, `C35` — correct, and a D-049 no-respin escape), `R119` (BMI270 alternate address; **mutually exclusive with `R118`**) and `R112` (display `SDO` isolation; **must not be fitted while MX-8 is relied on**). **The design now has zero unexplained DNP** |

### Blockers added or changed by FBV2-S1-002 (2026-08-23)

| # | blocker | status |
|---|---|---|
| ~~**B-09**~~ | GPIO3 has no strap-defining pull; a CMOS input floats at reset | **CLOSED 2026-08-23 by D-109.** `R110` 10 kΩ pull-down at the MCU pin. LOW is the only correct level — GPIO3 = 1 would select external JTAG on GPIO39-42, which are the I²S bus. BMI270 `INT1` is bound to push-pull active-high; open-drain is forbidden on this pin |
| **B-43** | **TPS61169 `CTRL` internal-pull specification not retrieved** — TI's PDF text layer would not extract this session | **OPEN, low.** The GPIO46 strap is safe for any internal pull-up ≥ 30 kΩ with `R108` = 10 kΩ, and `R109` 0 Ω is the isolation escape. Confirm at FBV2-S2 |
| ~~**B-44**~~ | BMI270 `INT` pad drive current not retrieved | **CLOSED 2026-08-23 by D-136.** `BST-BMI270-DS000-08` Rev 1.6 Table 1: **`IOH`/`IOL` ≤ 2 mA, `VOH` ≥ 0.8·VDDIO, `VOL` ≤ 0.2·VDDIO.** The `R18` + `R110` load draws **323 µA — 6× inside spec** — and GPIO3 settles at 3.23 V. The 47 kΩ fallback is not needed. |
| **B-59** | **`ER-TPC035-6` touch-flex I²C pull-ups unknown.** If the module carries its own, the effective internal pull-up drops below 2.2 kΩ | **OPEN, low.** Direction is safe (faster edges); sink current stays inside every device even at a 1 kΩ equivalent. **First-article measurement** |
| **B-65** | **The `+3V3` / `SYS` IR source-select link listed in `ARCHITECTURE.md` cannot be built without a sheet-01 edit.** `BQ25185_SYS` is a sheet-01-local net, not published hierarchically. Building it is one hierarchical label on sheet 01 plus a DNP resistor on sheet 07 | **OPEN, low.** A provision, not a fix — `+3V3` is the analysed-correct choice (D-156) |
| **B-66** | **TSAL6100 ±10° beam ergonomics unvalidated.** The narrow cone is the one real risk in the emitter choice | **OPEN, medium.** First article: if aiming is fussy, fit the **TSAL6200** — a proven drop-in with identical package, `VF` and `IFM`, so `R24` is unchanged and `R123` trims the current back up |
| **B-61** | **`AS02008MR-LW152-R` availability not confirmed from a live listing.** PUI's product page would not render here after three attempts and Digi-Key search is bot-protected. The datasheet is served live from PUI's API today and the sibling `AS02008MR-R` is catalogued — but **D-096 asks for a live listing and that is not one** | **OPEN, medium.** Procurement, before the BOM gate |
| **B-62** | **AWG #32 into JST PH `SPH-002T-P0.5S` is the small end of the #32–#24 applicable range.** Inside spec, but a crimp pull test belongs at first article | **OPEN, low.** First article |
| **B-63** | **The PCB acoustic hole and the pad-4 paste pullback are not in the microphone footprint.** Ø1.05 mm NPTH concentric with pad 4, and a stencil aperture kept back from the hole edge so solder cannot wick into the port | **OPEN.** PCB stage / FBV2-S2 |
| **B-64** | **The PCB still carries `MK1` with the ICS-43434 footprint.** Part of the standing transitional state — the board is bit-identical to Beta-DM and matches no migrated sheet. Recorded so the microphone change is not lost when the PCB is redone | **OPEN.** FBV2-P1 |
| **B-60** | **`0x36` (MAX17048) and `0x38` (FT6236) are not datasheet-cited.** Every Analog Devices and FocalTech fetch failed here — analog.com timed out, the Mouser mirror returned HTML, focuslcds returned 403 | **OPEN, low.** Consistent across every prior audit and almost certainly right, but *almost certainly* is not this programme's standard. **A first-article bus scan closes it in ten seconds** |
| ~~**B-45**~~ | **CLOSED 2026-08-23 (D-200) — STALE.** `R61`/`R62` 100 Ω plus two `D2` TVS channels landed at FBV2-S1-009. Original text: **`NATIVE_A` / `NATIVE_B` have no protection yet.** D-090 requires 100 Ω series on both native pins plus a low-capacitance TVS array; both belong beside the connector | **OPEN, high.** These are the only two contacts with a direct MCU path. Sheet `09` work |
| **B-27** | Recovery branch is not tolerant to every single failure | **AMENDED 2026-08-23 by D-105.** The ceiling is **≈ 15.9 mA nominal / ≈ 16.6 mA worst case**, not ≈ 13 mA — 680 Ω was the value that produced the old figure. Still ~0.0066 C, still bounded, still self-annunciating |
| **B-15** | No charge or VBUS telemetry reaches the MCU | **STILL OPEN, unchanged by this task.** The crossings are sheet `08`/`09` |

### Blockers added or changed by FBV2-S1-001 (2026-08-23)

| # | blocker | status |
|---|---|---|
| **B-41** | **`NFC_SUPPLY` has no consumer.** The 3.3 V-FIT / 5 V-DNP source select exists on `01_POWER_TREE`, but `U9` `VDD` and `VDD_TX` are still on `NFC_5V_PA_PENDING` — the Beta-DM arrangement — because they live on sheet `04`, which FBV2-S1-001 was not authorised to modify | **OPEN, high.** The v2 NFC supply architecture is **half implemented**. First item of the sheet-`04` migration |
| **B-42** | **The NFC source select is mutually exclusive by FIT STATE ONLY.** Fitting both `R106` and `R107` shorts `+3V3` to the 5 V boost output. Nothing in copper prevents it | **OPEN, low.** Inherent to a 0 Ω source-select and exactly the mechanism D-049 asks for, but it must become an assembly-note and fab-drawing requirement |
| ~~**B-01**~~ | Reverse-polarity protection does not exist; `BAT_CONNECTOR_P` is a single-pad net | **CLOSED AT SCHEMATIC LEVEL 2026-08-23.** `BAT_CONNECTOR_P` = `J4.1` + `F1.1` + `TP34.1`; the full P2 chain to `BAT_PROTECTED_P` is captured. **Not closed at board level** — the PCB is still the Beta-DM board |
| **B-15** | No charge or VBUS telemetry | **STILL OPEN, advanced.** The `VBUS_PRESENT` divider (2.97 V at VBUS 5.0 V) now exists, as do `BQ25185_STAT1/2` and `ACC_POWER_FAULT_N`. **CLOSED FOR CHARGE STATE 2026-08-23 (FBV2-S1-008, D-170):** `BQ25185_STAT1` and `BQ25185_STAT2` now land on `U2` P05/P06 with 10 kΩ pull-ups, and the Table 7-2 decode is recorded. **`VBUS_PRESENT` and `MAX17048_ALRT_N` remain test-point only** — D-089 had pencilled them onto `U2`, but `TOUCH_INT_N` and `SD_CARD_DETECT_N` arrived later and outrank them (D-166). **Twelve `U23` pins are free** if that is revisited, so it is a wire and a firmware change rather than a respin |
| **B-03** | Footprint audit not performed | **STILL OPEN — AND IT IS THE FBV2-S2 EXIT-GATE FAILURE.** 2026-08-23: **15 of 28 critical footprints are manufacturer-drawing verified with a cited document number and revision** (13 project-local plus `U11` BQ25185, checked against TI drawing 4226298/A, plus the PCAL9535A SOT355-1). **EIGHT remain traceable-but-unread**: ESP32-S3-WROOM-1, GCT USB4105, JST ACH, JST PH, PTS645, JS102011SAQN, the MAX98357A TQFN exposed pad and the NFC crystal. **They block fabrication release, not placement.** Earlier text: **STILL OPEN, widened.** `U18` LTC4368-1 had been assigned a **DFN-10 exposed-pad** footprint against the locked *"no bottom-terminated parts"* package policy; corrected to MSOP-10. The land pattern itself is still unverified, and `U18`-`U22`, `Q2`-`Q9`, `D9`-`D12`, `F1`, `R75`, `L4` all join the FBV2-S2 list |

### Pending decisions opened by FBV2-S1-001

| # | item |
|---|---|
| **P-20** | **`R95` = 680 R against a locked `R_LIM` of 560 R.** Recovery injection falls from ≈ 8.4 mA to **≈ 6.9 mA** into a 0 V pack, moving the wrong way against **B-26**. Keep 680 R or restore 560 R |
| **P-21** | **`OV` trip captured at 5.05 V** (`R77` 4.02 M / `R78` 442 k) against a documented *"divider ≈ 4.6 V"*. Confirm the captured number or correct it |
| **P-22** | The standing *"do not generate or modify KiCad files automatically"* rule was overtaken — this capture was scripted, then verified with `kicad-cli` ERC and a netlist export. **Ratify or reinstate.** Recorded in place, not treated as repealed |

### Blockers added or changed by FBV2-PWR-001 (2026-08-22)

| # | blocker | status |
|---|---|---|
| **B-20** | Dead-cell lockout created by the reverse protection | **STILL OPEN — P-11.** Now fully characterised: LTC4368 VIN UVLO 1.8/2.2/2.4 V; VOUT is a *sense* input and its charge-pump role only applies above ~5 V, so **system-side power cannot run the controller**. No inherent recovery path exists. Four candidate architectures analysed; **B recommended** |
| **B-21** | Shorted pass FET reproduces the guarded fault | **BOUNDED, not closed.** Clamp + fuse reduce the excursion from ≈−3.7 V to ≈−1 V, still ~3× the −0.3 V DC abs max. Residual is **P-12** |
| ~~B-22~~ | Latch-off vs hot-insertion inrush | **CLOSED.** Inrush is a designed parameter; latch-off applies to forward OC only |
| **B-23** | PCAL9535A pin table not obtainable from a primary source | **STILL OPEN, but no longer blocking.** Architecture locked by D-061; four secondary-sourced facts deferred to the land-pattern audit |
| ~~B-24~~ | SX1262 DIO1 level-hold unverified | **CLOSED** — confirmed verbatim from Semtech §13.3.4 (Rev. 1.2; re-confirm against V2.2 pre-fab) |

### Blockers added or changed by FBV2-ARCH-002 (2026-08-22)

| # | blocker | status |
|---|---|---|
| **B-20** | **Dead-cell lockout created by the reverse protection.** Below LTC4368 UVLO (1.8–2.4 V) both gates are off and the body diodes are anti-series — a ~0 V pack can never be recharged. | **OPEN — P-11. Blocks FBV2-A1.** |
| **B-21** | **Shorted pass FET reproduces the guarded fault.** Without a fuse + Schottky clamp, −3.0 to −4.35 V lands on BQ25185 BAT against a −0.3 V abs max — a 10–14× DC violation. | **Mitigation identified** (fuse + clamp, required not optional); survivability of the residual excursion is **P-12**. |
| **B-22** | **Latch-off vs hot-insertion inrush unreconciled.** | **OPEN — P-13. Blocks FBV2-A1.** |
| **B-23** | **PCAL9535A pin table not obtainable** from a primary source (NXP 404, Digi-Key 410, Mouser HTML). | **OPEN.** Blocks criterion 2. One document read. |
| **B-24** | **SX1262 DIO1 level-hold behaviour unverified** (Semtech domain did not resolve; Mouser mirror returned HTML). | **OPEN.** Blocks criterion 3. Read the SX126x **and** E22-900M22S IRQ sections. |
| **B-25** | **Permanent raw `+3V3` connector pin** — unprotected always-live tap; defeats whatever is fitted on the switched pin. | **CLOSED by D-057** — pin removed from the 20-pin map. |
| ~~B-18~~ | TPS22918 lacks reverse-current blocking | **CLOSED by D-058** — replaced with TPS22950C (RCB confirmed for the C variant). My earlier TPS22913B/C suggestion was **wrong** — DSBGA-only and no current limit. |

### Blockers added or changed by FBV2-ARCH-001 (2026-08-22)

| # | blocker | status |
|---|---|---|
| **B-17** | **NFC supply topology undecided (P-10).** With TPS61023 true load disconnect confirmed, disabling the boost leaves VDD = VDD_TX = 0 V while VDD_IO = 3.3 V — unauthorised by DS12484 Table 119 (VDD min 2.4 V). | **OPEN — CTO decision.** N1 (3.3 V-only, delete the boost) recommended. |
| **B-18** | **`TPS22918` has no reverse-current blocking.** Datasheet confirms the integrated body diode conducts VOUT→VIN. An externally powered accessory can back-power `+3V3` through `ACC_3V3_SW`. | **OPEN.** Replacement identified (TPS22913B/C class); exact MPN needs a page-cited datasheet check. |
| **B-19** | **`NFC_IRQ` must never move to GPIO46.** A latched-high IRQ would block Joint Download Boot and make ROM-download recovery conditional on NFC state. | **CLOSED as a design rule** — recorded so it cannot be reintroduced. |
| ~~B-11 / B-12~~ | GPIO18/GPIO38 documentation mismatch and LoRa wake | **Mismatch still to fix in migration.** The *wake* consequence is retired by D-041 — LoRa deep-sleep packet wake is not a v2 requirement. |
| **B-16** | Field Slate v5 §5 lists phantom Volume controls | **Still open.** Needs a CTO-approved text correction. |

**Retired by verification:** B-07 (see above). **Partially advanced:** B-03 — `U9`'s
33-pad footprint mapping is now verified correct against three independent
DS12484 tables; every other footprint remains unverified.

---

## Change log for this file

| date | change |
|---|---|
| 2026-08-24 | **FBV2-EXP-001. Expansion ecosystem compatibility and pre-routing architecture AUDIT = PASS. AUDIT ONLY — NO AUTHORITATIVE HARDWARE CHANGE, NO PROGRESS EARNED; overall stays 74%.** **THE 24-LINE SIDE HEADER DOES NOT FIT THE CURRENT FLOORPLAN, AND THE NUMBER IS EXACT.** A right-angle THT socket puts its tails **6.5–6.9 mm inboard of its own mating face** (Sullins 1-row RA drawing 10493), so the tail row lands at x ≈ 63.5 — **inside `BATTERY_SHADOW`, which forbids any through-hole lead**. **Requirement: (board right edge − battery right edge) ≥ 7.83 mm; today 4.00 mm; SHORTFALL 3.83 mm.** Above the battery the wall offers **41.00 mm** against a **61.47 mm** body — a 1 × 15 is the largest that fits and leaves nothing for Qwiic or POWER. Left wall = 433 flex + mandatory coax channel; bottom = USB-C/microSD/both radios; top = IR pair + SMA. **All rejected on measurement.** **TWO 1 × 12 REJECTED ON GEOMETRY:** both Samtec and Sullins build the body **N × 2.54 + 0.51 mm**, so two butted bodies sit **3.050 mm apart against a 2.540 mm pitch — 0.510 mm interference**; they cannot form a continuous 24-grid, need **5.59 mm MORE** wall than one 1 × 24, and add a wrong-group mis-plug mode. **RECOMMENDED: one Samtec `SSQ-124-02-G-S-RA` (same manufacturer as the present `J5`; 01–50 positions/row, `-S` single row, `-RA` right angle, body 61.47 mm, 6.3 A/pin, accepts .025″ square post) + one `JST SM04B-SRSS-TB` Qwiic (SH 1.0 mm, 1 GND / 2 3V3 / 3 SDA / 4 SCL), CONDITIONAL on E-1 PCB 70 → 72 mm (already `FBV2_PCB_MAX_MM`, enclosure unchanged) and E-2 battery 60 → 57 mm, ≈ −5 % capacity.** **Sullins `PPTC241LGBN-RC` verified and deliberately NOT baselined — 0 stock, non-RC obsolete, sibling factory-order at 1,000 MOQ / 11 weeks: the third catalogue-part-is-not-a-stocked-part trap after Harwin M20 and the Amphenol pigtail.** **ALL 24 FUNCTIONS RETAINED**; recommended **ORDER-A** puts `3V3/SDA/SCL/GND` at pins 3-4-5-6 and **both 5 V contacts at the two physical ends with GND as their only neighbour — no 5 V pin is adjacent to any signal, removing two adjacencies the present order has**. **A closed-end 62.5 mm recess gives 1.54 mm of play against a 2.54 mm pitch, so a one-position shift is physically impossible — no proprietary shroud, and the asymmetric key (D-097) becomes unnecessary.** **QWIIC ADDS ZERO COMPONENTS:** it attaches at `EXT_SCL`/`EXT_SDA`, downstream of the 22 Ω resistors and at `D2`'s clamp, inheriting the `TCA4307`, the 1.5 k pull-ups, the series R and the TVS; **power is `ACC_3V3_SW` because `U16`'s own VCC already is**, and `ACC_5V_SW` is never exposed. Budget ≈ 55–75 pF for three daisy-chained boards against ≤ 200 pF — **no mux, no repeater.** **MANUAL/BENCH POWER NEEDS NO HARDWARE CHANGE FOR EITHER RAIL:** traced pin by pin, `ACC_DETECT_N` reaches nothing but `U3.P17`, so detect gating is entirely firmware, while ILIM, RCB, TSD and FLT stay in hardware; permanent 5 V remains physically impossible. **BOOT → bottom edge** (a measured 11.04 mm window; `SW1` is SMD; 14 mm free enclosure span for the tool hole); **lower-left BOOT REJECTED ON RF** — that wall *is* the 433 flex region and the mandatory coax channel. **0x50 stays an optional single-accessory convention needing a firmware signature, no PCB change.** **PM-2 AND THE NEW HEADER WANT THE SAME CORNER**, so a **COMBINED RE-FLOORPLAN** is recommended — outline and reservations, then the right-wall stack, then PM-2, PT-1, PM-1, PM-3, P2-R1 — and **FBV2-P1 would have to be re-issued** because the outline change invalidates its PASS. **VALIDATION: PCB blob `22c03150…` identical to HEAD; ERC 27 / 0 errors; DRC 26; 499 unrouted; 0 tracks / 0 vias / 0 pours; outline 70 × 148 unchanged; collisions 0; `p1_regression`, `dru_probe`, `netclass_probe`, `fork_equivalence` all PASS; Beta-DM, the frozen Beta tree and `hardware/beta/mechanical/` untouched.** **D-081 / D-083 / D-093 / D-097 REMAIN IN FORCE — supersession is PENDING CTO / OWNER RULING.** |
| 2026-08-24 | **FBV2-EXP-002. FBV2-P1 RE-ISSUED = PASS. FBV2-P2 ENTRY = PASS. PM-1, PM-2, PM-3 and PT-1 ALL CLOSED. NO PROGRESS EARNED — P1 was RE-earned, not newly earned; overall stays 74%.** **THE BATTERY GATE RAN FIRST AND CHANGED THE STORY:** before any authoritative file was touched, the 57 × 75 × 8 mm envelope was checked against **PKCELL `LP785060` (7.3 × 50 × 60 mm, 2500 mAh typ / 2375 min, PCM fitted, JST-PH lead)** and **`LP755070` (7.5 × 50 × 70 mm, 3000 mAh min / 3050 typ, PCM fitted, 4.275 V overcharge with 2.50 V resume, 500 cycles to 80%)**, both manufacturer datasheets. **THE PREDICTED −5% PENALTY DOES NOT MATERIALISE — both candidates are 50 mm wide, so the 57 mm limit binds neither, and `LP755070` sits at the TOP of D-071's 2500–3000 mAh target.** **`J5` → Samtec `SSQ-124-02-G-S-RA` 1 × 24 2.54 mm FEMALE RIGHT-ANGLE** (same manufacturer as the BCS it replaces; 01–50 positions/row, `-S` single row, `-RA`, body 61.47 mm, mates .025″ square post, 6.3 A/pin) with **`J8` `JST SM04B-SRSS-TB` Qwiic / STEMMA QT added for ZERO components** on `EXT_SDA`/`EXT_SCL` downstream of `U16` and the 22 Ω pair at `D2`'s clamp, powered from `ACC_3V3_SW` because **`U16`'s own VCC already is** — no buffer, no mux, no repeater, no extra pull-ups, no second TVS, and `ACC_5V_SW` never exposed. **ALL 24 FUNCTIONS RETAINED; NOT ONE PROTECTION PART REMOVED; the schematic change is a footprint swap plus a sheet-09 pin re-map — no net created, deleted, split or merged.** **ORDER-B SUPERSEDES ORDER-A BECAUSE IT IS SAFE UNDER 180° REVERSAL BY CONSTRUCTION: 5V↔5V, GND↔GND, 3V3↔3V3 and 3.3 V logic ↔ 3.3 V logic everywhere else — POWER-TO-SIGNAL MAPS UNDER REVERSAL: ZERO**, proved pin by pin from the netlist; the one-position slip stays impossible (60.96 mm male body, closed-end 62.5 mm recess, **1.54 mm of play against a 2.54 mm pitch**) and **D-097's asymmetric key is no longer needed.** **BOARD 70 → 72 mm SYMMETRICALLY** so every part shifted +1.0 mm in X and every part-to-part relationship is preserved; enclosure untouched; wall gap 2.5 → **1.5 mm both sides, the rule met EXACTLY**; **`ANT433_REGION` RE-DERIVED rather than shifted** because its 2.2 mm reservation never described anything real — the flex is 0.28 mm thick and bonded flat to the wall. **BATTERY 60 → 57 mm MAX: that 3 mm is the entire price of the header**, since a right-angle socket puts its tails 6.53 mm inboard of its mating face and needs (board right − cell right) ≥ 7.83 mm against 4.00. Measured: tail row X 65.900, **1.100 mm clear of the cell**, mating face 0.430 mm outboard with **1.070 mm to the cavity wall**. **PM-1: 12.96/28.56/30.50/45.90 → 4.80/4.34/3.86/3.79 mm**, each a COMPLETE POWER CELL — `D8`, which sat **45.7 mm from its own inductor**, is now 3.56 mm from `U17`, so the 39 V open-LED loop is local instead of a 76 mm perimeter 13 mm from the microphone. **PM-2: the 1.5 A path is 116.7 → 30.86 mm** as one monotonic column, Kelvin pair 6.60 mm, **NO FET, threshold, divider or recovery branch altered — D-049 UNTOUCHED**; **`J4` is the one part that could not join it and that is recorded, not hidden** — the left margin is also the coax lane, which parts ≤ 2.0 mm may share but a 5.75 mm connector cannot, so it sits at the column's head 8.59 mm from `F1`. **PT-1: `U11` out of `BATTERY_SHADOW` to (67.500, 70.200), 3.5 mm clear of the cell.** **B-34 RE-ESTIMATED, NOT CLAIMED ZERO: 38.8 → 15.2 mΩ, ≈ 53 mW better at 1.5 A — it IMPROVES MATERIALLY BUT DOES NOT CLOSE**, because its 0.70 W is dominated by the BATFET's 115 mΩ, which this task correctly did not change. **PM-3: the NFC arms mirror at Δx = 0.000 mm and arm-length Δ = 0.000 mm**, `Y1` 5.40 mm from `U9` with its load caps local, **no locked NFC value changed**. **`BOOT` → (28.300, 6.000) FRONT face** in the measured 11.04 mm window, tool hole in the FRONT wall so it clears both the card path and the USB-C plug; **LOWER-LEFT REJECTED ON RF.** **POWER stays on the right wall. Retention still TWO M2 — widening the board did not buy a third and none was chased.** **NFC loop ↔ `J5` metal improves 5.490 → 9.155 mm; NFC pair 41.73 → 31.23 mm; display offset 3.34 → 2.34 mm.** **`J5`'s courtyard overhangs the right edge by 0.975 mm — that is what a right-angle socket is FOR — and `p1_regression` now tests it explicitly instead of counting it as a part off the board.** **DRC 26 → 1** (the `MK1` artefact accepted at D-227, still NOT excluded and NOT suppressed); **ERC 0 errors / 27 warnings, histogram identical; 499 unrouted; ZERO tracks, ZERO signal vias, ZERO electrical pours; ZERO placement collisions**; `p1_regression`, `dru_probe`, `netclass_probe` and `fork_equivalence` all PASS with the **BCS 2 × 12 footprint RETAINED in the library, not deleted**, as Beta-DM's part and the fallback. **ONE NEW OWNER ITEM — E-7: the 57 mm envelope is now the LOWER bound of what fits, not a target; both cells are 50 mm wide, leaving 7 mm of reservation unused. Recorded, not decided.** |
| 2026-08-24 | **FBV2-P2-000. FBV2-P2 ENTRY GATE = FAIL on one criterion of thirteen. NO PROGRESS EARNED — overall stays 74%, FBV2-P1 = PASS unchanged.** **THE INHERITED RULE SET WAS NOT MERELY STALE: 22 OF 71 RULES COULD NEVER FIRE.** `.kicad_dru` referenced **39 rule areas and the board contained NONE of them** — not only the E6 pockets P2-O5 named, but **every RF-band rule, every E5/E4 corridor rule, the header reservation, the E2 button escapes and the ESP32 antenna rule**. KiCad's `intersectsArea()` returns **false** for an unknown name with no warning and no error, so a rule that can never fire looks exactly like a rule being satisfied. **Rebuilt to 64 live rules with a written RETIREMENT REGISTER (R1–R10) giving a reason for each of the 22 retirements**; the E6 escape-relief DOCTRINE is preserved in full even though its Beta-DM measurements are not. **`checks/dru_probe.py` is new and now fails the build if any rule reference or netclass pattern stops resolving — P2-O5 cannot recur silently** (D-233). **THE NETCLASS TABLE HAD BEEN LYING SINCE THE FORK:** `BAT_MAIN`'s pattern was the root-sheet path `/BAT_PROTECTED_P` while every v2 power net lives under `/01_POWER_TREE/`, so **it matched nothing and the highest-current net on the board — 1.5 A sustained — was routing at 0.20 mm**; `BAT_RAW`, `BAT_MID`, `BAT_SENSE` were in no class at all; `NFC_5V_PA` captured **no net whatsoever**; and **`ACC_5V_LX`, the `U21` boost SWITCH NODE, had never been in `SWITCH_NODE`**. **14 classes → 18, 62 patterns → 57, every surviving pattern now matches at least one net; four dead classes retired without weakening any net's parameters** (D-234). **RETENTION LOCKED AND D-226 CLOSED: two M2 is ACCEPTABLE**, no component moved, with rails + four rear non-metallic ribs + two screws + the `J5` backing boss, and three stale mechanical-spec entries corrected in the same pass (D-232). **ROUTING STRATEGY FROZEN:** stackup retained and **layer roles now ENFORCED BY RULE**, one solid In1 with a single authorised void (the 6.5 × 44 mm ESP32 notch), **USB confirmed FULL SPEED at ≈ 40 mm on F.Cu with ZERO vias and no length matching**, SPI-A **63 % shorter** and SPI-B **21 % shorter** than accepted Beta-DM versions so neither gets damping, internal I²C given a derived **C_bus ≤ 161 pF** budget, and the `J5` escape measured at **10 crossings needed against 22 available on one layer** — no nudge required (D-235). **WHAT FAILS THE GATE: THREE ELECTRICALLY REQUIRED PLACEMENT MOVES, SURFACED NOT DECIDED (D-236).** **PM-1** — all four switching converters have their inductor **12.96–45.90 mm** off the IC, the backlight loop **≈ 76 mm around** switching to **39 V** on an open-LED fault, 13 mm from `MK1`. **PM-2** — the single-fault battery-protection block dispersed across three clusters over **96 mm**, with 2.2–3.65 MΩ trip nodes and a **≈ 20 µA gate node spanning 95.6 mm**; the Kelvin sense itself is sound and D-049 is not compromised. **PM-3** — the NFC matching arms differ by **10 mm before a track is drawn**. **All three are NEW and none existed in Beta-DM: P1 verified every MECHANICAL relationship by script, and nobody had yet looked at these blocks ELECTRICALLY.** **DRC 47 → 26** (all 21 `clearance` violations closed by naming the four vendor land patterns that cause them, no routing clearance weakened); **ERC 0 errors / 27 warnings, histogram identical**; **499 unrouted, ZERO tracks, ZERO signal vias, ZERO electrical pours**; `netclass_probe`, `p1_regression`, `fork_equivalence` and the new `dru_probe` all PASS; **Beta-DM, the frozen Beta tree and `hardware/beta/mechanical/` untouched.** **ROUTING DOES NOT BEGIN UNTIL PM-1, PM-2 AND PM-3 ARE RULED ON.** |
| 2026-08-24 | **FBV2-P1-002. FBV2-P1 PASSES. Overall 68% → 74% — the third twelve-gate pass.** **THE 915 FEED CLOSES ON MEASURED GEOMETRY: 138.48 mm routed** from `U8` IPEX (9.00, 16.60) up the left rear channel to the SMA at (5.00, 148.00), **7.42 mm minimum available bend radius**, **0.600 mm** at its tightest to the Ø58 NFC exclusion and **ZERO violations** against the 433 flex, the battery, the speaker cavity, the microSD card travel, the USB aperture, both IR windows, the barrier, the community recess and `J5`. **The fix was WIDTH, not length** — the SMA is locked to the top-panel left half and the NFC region owned the whole upper-left, so no cable length could ever have worked. **NFC becomes CIRCULAR: clear Ø48, metal exclusion Ø58, centre doc (30.800, 124.500)**, the 48 × 48 square retained only as the placement-tolerance envelope; **+6.30 mm in X is the entire 915 solution** (75 mm cavity − 58 mm exclusion − 12.1 mm of `J5` = 4.9 mm of lane, and only pushed hard right — loop-to-`J5` now **5.490 mm** against ≥ 5) and **−1.50 mm in Y** buys the SMA its margin. **The radial clearance was NOT reduced: the Ø58 circle is inscribed in the superseded 58 × 51 rectangle**, so only the four corners are reclaimed. **Cost stated plainly:** NFC clear ↔ battery 3.50 → **2.00 mm, still ZERO overlap**; battery inside the Ø58 1.50 → 3.00 mm (D-224). **`U7`/`U8` SWAPPED for zero plan area** (identical footprints) and the **SMA moved x 12.000 → 5.000**, improving both SMA↔IR rules (D-222). **CABLE RE-SELECTED: RF Solutions `CBA-UFLSMA20IP`, 200 mm, IP67, RG-178, U.FL R/A → SMA(F) bulkhead** — ACTIVE, **296 in stock at DigiKey**, spare **46.52 mm** beyond the 15 mm service loop, loss ≈ 0.4 dB, **U.FL↔MHF1 COMPATIBLE**; **and it fixes a procurement risk — the superseded Amphenol part was 0 in stock on a 12-week lead** (D-223). **THREE FINDINGS THE PREVIOUS PASS HAD WRONG:** the ESP32 0.2 mm thermal vias were **never in violation** (global floor is 0.20 mm, not 0.30) — the twelve errors were **`copper_edge_clearance` on `J5`**, fixed by a **0.070 mm** nudge, with JLCPCB capability verified live and a **narrowly scoped guard** added that does **not** lower the global minimum (D-228); P1-001's **`BOSS2` was inside the mandatory opaque IR barrier and was never legal** — corrected, and the barrier **widened 3.0 → 5.0 mm** to fill the inter-window gap and carry the boss (D-226); and writing the IR forming requirement showed **the formed `TSAL6100` dome would have finished 1.2 mm OUTSIDE the shell** — `D1` moved to (50.750, 141.400), `TP39`/`R123` 1.750 mm, `U6` fits unmoved (D-229). **`MK1` PADSTACK FIXED, `padstack_invalid` 2 → 0**, with the Ø1.05 NPTH, the ID 1.05 / OD 1.65 annulus, the 0.10 mm paste pullback, the keep-out and the mic location **all unchanged** — and **no fake plated through-hole** (D-227). **B-52's floorplan half CLOSED** on the Ø9.238 hex / Ø10.2 washer envelope; only an enclosure-CAD residual remains (D-230). **DISPLAY: 3.34 mm left offset ACCEPTED as intentional and the Z stack NOT spent** — P1-001's raise-the-display recommendation is rejected and withdrawn (D-225). **RETENTION: the outline yields TWO legal M2 positions, not three — ESCALATED**, with support completed by edge-capture rails and four reserved rear rib pads that need no PCB holes (D-226). **DRC 64 → 47, every one classified; `padstack_invalid` 2 → 0, `copper_edge_clearance` 12 → 0, `lib_footprint_issues` 3 → 0; nothing fake-cleaned — no exclusion, no severity change, no relaxed global rule.** ERC 27 / 0 errors, histogram byte-identical; schematic connectivity UNCHANGED; **placement collisions 0**; **ZERO tracks, ZERO vias, ZERO pours, 499 unrouted.** `netclass_probe` PASS, `fork_equivalence` PASS with Beta-DM and the frozen Beta tree untouched. **FBV2-P2 has not begun.** |
| 2026-08-24 | **FBV2-P1-001. FBV2-P1 DOES NOT PASS. Overall stays 68% — no progress awarded.** **PCB modification authorised for the first time; the v2 board is no longer Beta-DM.** The board was **rebuilt from the current nine-sheet schematic**: pre-P1 file stripped to header, layer stack, `general` and `setup` (design rules byte-identical), **all Beta-DM footprints, tracks, vias, zones and graphics removed**, **321 footprints re-created one per component**, **224 nets / 991 pads** applied, plus a **70.000 x 148.000 x 1.6 mm** outline — **the TARGET, not the 72 x 152 maximum** — 13 named mechanical regions, 4 copper rule areas and 3 M2 NPTH bosses. **F.Cu 120 / B.Cu 201.** **Datum: lower-left board corner, X right, Y up; `Y_kicad = 148.000 - Y_doc`.** **SIX RULINGS RECORDED (D-214...D-219):** `F.Cu`=FRONT / `B.Cu`=REAR with **`MK1` on B.Cu listening forward through the board, 1.21 mm clear of the LiPo and 67.42 mm from the speaker** (**O-1 closed**); rear packing **NFC -> battery -> speaker, 48+75+20 = 143 mm in 155 mm** with **zero NFC/battery overlap** (**O-2 closed as a FALSE conflict**); **USB/microSD 16.40 mm BODY edge-to-edge** against the new >= 8 mm rule (**O-4 closed**); **internal 915 whip storage DELETED — the locked `TI.92.2113` is 198 mm against a 172 mm internal diagonal and never fitted; the freed LEFT wall restores D-118's LEFT/LOWER-SIDE 433 flex placement** (**O-6 closed**). **ZERO placement conflicts** on a side-aware review of all 321 courtyards; FPC margin **15.8 mm**, IR TX-RX **15.00 mm**, SMA-IR **39.55 mm centre / 31.05 mm edge**, NFC **48 x 48**. **THE GATE FAILS ON ONE CRITERION (D-218): the 100 mm 915 pigtail is SHORT BY ~90 mm** — every part taller than ~1.2 mm is excluded from the upper half, so `U8` sits at the bottom rear and the routed run is **~190 mm**; even the superseded 150 mm is short by ~40 mm, **and no length fixes it while the SMA is locked to the top-LEFT behind the NFC zone**. Recommended: **raise the display support ~3 mm into Column A's 9.9 mm of unused Z.** **ONLY 3 OF 6 M2 BOSSES CLOSE** (D-216) — no 6 mm side strip exists between the display, battery and NFC zone. **FOUR NEW ITEMS (D-221): the display cannot be centred (3.34 mm left of centre because `J5` must sit beside the panel band); `MK1`'s ring pad fails KiCad 10's padstack validator; the stock ESP32 footprint's 0.2 mm thermal vias break the 0.3 mm min-hole rule; and `netclass_probe` had been measuring Beta-DM net names — expectation corrected to the schematic, guard unchanged and still passing.** **ERC 27 -> 27, zero errors, histogram byte-identical. Schematic connectivity UNCHANGED. ZERO tracks, ZERO vias, ZERO pours; 499 unrouted, which is correct at P1.** `fork_equivalence` now reports the v2 PCB as **changed — the intended outcome of P1** — and confirms **Beta-DM and the frozen Beta tree untouched.** |
| 2026-08-23 | **FBV2-MECH-002. NO PROGRESS EARNED — overall stays 68%, FBV2-S2 = PASS unchanged.** **This was a reconciliation and sign-off task, not a design phase.** **Two procurement substitutions SIGNED OFF AND ADOPTED**: `F1` → **Littelfuse `0466005.NRHF`, `C57525`, 29,328 in stock, JLC Extended** — the halogen-free ordering option of the same 466/Nano2 family, and **the two LCSC records carry a character-for-character identical parametric string** (D-210); `D10`–`D12` → **Diodes Inc `BAT54WS-7-F`, `C124205`, 46,819 in stock, JLC Extended** (D-211). **THE "SERIES PAIR" SOURCING ERROR IS CORRECTED PROGRAMME-WIDE: `BAT54WS` IS NOT A SERIES PAIR** — SOD-323 is a two-terminal package, every `BAT54WS` in the LCSC library from eight manufacturers is catalogued **1 Independent**, and `D10`/`D11`/`D12` are each one two-pin `Device:D_Schottky` on a two-pad footprint, with `D10`/`D11` forming the ratiometric pair as **two separate components**. **The design was never wrong; six documents were.** `BAT54W,115` stays rejected **because it is SOT-323 (SC-70) — a footprint mismatch, not a diode count.** **Electrically verified, no material mismatch**: the bridge comparison `(BAT_RAW + V_F11 − V_F10)/2` **cancels the absolute drop** and runs at **≈1.1 µA through 4.4 MΩ**; `D12` sees **≈16.6 mA worst case against 100 mA — 6×**, and D-105's 5–10 mA band **needs no revision**. **Consignment 11 → 9 part numbers; CLASS D IS EMPTY; still exactly two hand-soldered parts per board (`J5`, `D1`).** **MECHANICAL AUTHORITY RECONCILED (D-212)**: **NFC zone 45×45 → 48×48 LOCKED** (stale in four places including the machine-readable block); **every current FH12/FH52E land-pattern and second-source claim REMOVED** — FH69 dedicated, not drop-in, single-source, **machine-placeable**; **`J1` is NOT manual assembly**; speaker Z column **4.0 → 3.0 mm (13.6 → 12.6)**; **"26 to 20 pins" → 24 contacts 2×12**; **"removes the RGB nets" → a front RGB `D13` was ADDED**. **915 SMA↔IR spacing TRACED, NOT resolved by preference: BOTH rules are current** — ≥15 mm **centre-to-centre** (FBV2-MECH-001) and ≥8 mm **edge-to-edge** (D-120), **re-asserted together by M-13**; the real defect was that neither said what it measured between, and both now carry a datum in a new §8.1. **B-52 stays OPEN, no CAD created.** **New handoff: `mechanical/P1_FLOORPLAN_INPUTS.md`, 120 constraints, no invented coordinates.** **SIX BLOCKERS SURFACED FOR CTO RULING (D-213)**, the two sharpest being arithmetic: **the rear face is over-constrained by ≈8 mm** (battery 75 + NFC 48 + speaker Ø20 + 20 mm separation = 163 in a 155 mm cavity) and **the internal antenna storage channel cannot hold the locked `TI.92.2113` whip** (198 mm against a 172 mm internal diagonal). **ERC 27 → 27, zero errors, histogram identical. Netlist 224 nets / 991 nodes IDENTICAL. Schematic diff PROPERTY-ONLY. PCB byte-identical and still bit-identical to Beta-DM.** |
| 2026-08-23 | FBV2-S2-002. **Overall raised 62% -> 68%. FBV2-S2 = PASS** - the second twelve-gate pass. **B-03 CLOSED**: all eight remaining Tier-2 footprints compared dimension-by-dimension against retrieved manufacturer drawings, 23 of 28 now Tier 1; the **MAX98357A "contradiction" dissolved** when Maxim land pattern **90-0032 Rev E** turned out to specify **one land for `T1633-5`, `-5C` and `-7C` together**, so **no project-local footprint was created**; `Y1` locked (`C362365`, 3,421 in stock) with an **exact** land match (D-201, D-202). **B-63 CLOSED**: the microphone acoustic port is now **drawn** - Ø1.05 NPTH from the drawing s own ring ID, paste pulled back 0.10 mm as a declared stencil choice, keepout and bottom-port orientation recorded as **M-14** (D-203). **B-70 CLOSED**: Murata **`LQW18AN39NG80D`** - and **the DCR is a first-order term**, dropping network Q 25.3 -> 21.4 against `R_q` = 1.1 Ohm, so the antenna must be tuned with this exact part fitted and **the first lever is `R_q`, not 39 nH** (D-204). **B-54 CLOSED**: DS12484 Rev 3 retrieved through a mirror; **`I_AL-AM` max 26 mA + ~60 mA driver -> allocate 100 mA**, the **350/500 mA abs-max figures deliberately NOT used**, TPS63020 **63-71 % of 2 A**, with a **binding guard rail** on any `C_s` move to 270 pF (D-205). **B-71 CLOSED**: all 46 MPNs classified against live JLCPCB parts-API state, **65 `LCSC` fields written into the schematic**, **two hand-soldered THT parts per board and zero hand-placed fine-pitch**, ten stock shortfalls handled by **consignment**, **six substitution traps caught** including `BAT54W` offered for `BAT54WS` (~~single vs series pair~~ - ***CORRECTED 2026-08-23 by D-211: `BAT54WS` IS NOT A SERIES PAIR.* SOD-323 is a two-terminal package and `D10`-`D12` are each ONE independent diode; `BAT54W,115` is wrong because it is SOT-323 (SC-70) - a FOOTPRINT mismatch.**) and a clone for the **battery reverse-polarity pass FETs**; **`J1` improves to machine-placed** (D-206, D-207). **O-8 CLOSED**: Taoglas **`TI.92.2113`** verified against SPE-19-8-076/A - and **the marketed "2 dBi" is the bent peak; average gain is negative in both orientations** (D-209). **Eight DNP parts still had no recorded reason and now do; the design has zero unexplained DNP** (D-208). **ERC 27 / 0 errors / 27, histogram identical.** **The schematic diff is PROPERTY-ONLY** - not one wire, label, junction, symbol or pin line changed. **PCB untouched and still bit-identical to Beta-DM.** |
| 2026-08-23 | FBV2-S2-001. **Overall HELD at 62% - FBV2-S2 = FAIL on two of fourteen exit criteria, and a failed gate awards no percentage.** **THE AUDIT FOUND A FABRICATION-BLOCKING DEFECT ON THE FIRST THING IT LOOKED AT: `U9` ST25R3916-AQET AND ITS TWELVE MANDATORY DECOUPLING CAPACITORS WERE STILL MARKED DNP**, against D-035 and D-055, while the crystal, the complete matching network, the antenna connector and the SPI wiring around them were all FITTED - **the first five boards would have carried a finished 13.56 MHz front end with no NFC chip on it**. All thirteen are now FIT (D-192). **Seventh consecutive sheet with a load-bearing inherited DNP, and the one that hid longest.** **`D-077`'S DISPLAY SECOND SOURCE DOES NOT EXIST** - both Hirose land patterns read: FH69 is 7.38 mm deep, 0.30 x 1.23 land, top-and-bottom two-point contact; FH52E is 4.6 mm, bottom contact only, and its own catalogue points at the FH12 pattern. **The drop-in claim is struck; `J1` is manual assembly** (D-194, B-47 resolved). **P-14 RESOLVED: the MAX17048 STAYS on `BAT_PROTECTED_P`** - it was never on `BAT_RAW`, and moving it to the LTC4368's precision sense node would trade a <= 2.6 % SOC error for a differential capacitance across the current-sense resistor (D-193). **O-7 CLOSED as Option A**: `R49` = `R50` = 1.5 k, published contract <= 200 pF at 400 kHz and <= 400 pF at 100 kHz, per UM10204 (D-191). **B-69 CORRECTED**: the 700 us soft start is specified at 10 uF and `C65`/`C66` give ~20 uF effective at 5 V bias, so the margin was 3.5x not 7x - **settle delay raised to >= 10 ms** (D-198). **B-68 CLOSED** - Wurth 74438357010 Isat 6.2 A against a 2.19 A peak; `L1` recorded at 1.4x as the tightest magnetics margin on the board; **two stale 'FOOTPRINT STILL BLOCKED' notes withdrawn** (D-197). **B-46 CLOSED and the guess was right** - Molex SD-502570-001 Rev A: card inserted = CLOSE, so LOW = card present (D-196). **B-49 and B-51 CLOSED** - Ebyte ships both modules with IPEX **and** stamp holes on the standard MPN, and the 915 MHz interface is **Amphenol `095-902-568-150`, ACTIVE**, one assembly carrying both the pigtail and the panel bulkhead (D-195). **P-01, P-04, B-45, B-53 closed as STALE** (D-200). **`R68`, a 0 R DNP with no note, is a BYPASS ACROSS `SW9` that would wire the unit permanently ON and defeat the only way to power down a hung board - now marked MUST STAY DNP**; `C21`/`C22` identified as dead pads; **six missing MPNs added, so every active and connector now carries an exact MPN** (D-199). **306 FITTED / 16 DNP / 0 unexplained DNP.** **B-70, B-71 and O-8 opened.** **FAILS: B-03 - 15 of 28 critical footprints drawing-verified, EIGHT traceable-but-unread; and B-71 - only 7 of 46 unique MPNs carry an LCSC code, so the JLC classification cannot be produced. Neither blocks placement; both block fabrication release.** ERC 27 / 0 / 27 unchanged; 0 duplicate refs, 0 unresolved footprints, 0 orphan nets, 0 same-text split labels; all seven PWR_FLAGs traced to a real supply. **PCB untouched and still bit-identical to Beta-DM. No PCB placement or routing was started.** |
| 2026-08-23 | FBV2-S1-009. Overall raised 55% → 62%. **FBV2-S1 = PASS — the first twelve-gate entry to pass since FBV2-A2.** Task gate **FBV2-S1-COMMUNITY = PASS**. **`09_COMMUNITY_HEADER` MIGRATED — THE SCHEMATIC MIGRATION IS COMPLETE, all nine sheets, and `fork_equivalence.py`'s "still Beta-DM" list is EMPTY.** Three CTO rulings recorded first: **O-6 RATIFIED** (`U23` + front RGB are locked architecture, **B-37 RETIRED** with 11 spare expander pins, D-175); **O-4 APPROVED** (`U16` TCA9517A → TI **`TCA4307DGKR`**, LCSC C880333, verified live at 3248 in stock, **FITTED** where the old part was DNP, D-176); **P-18 CLOSED with NO MUX** — the buffer solves electrical isolation, the address registry solves addresses (D-178). **SHEET 09 WAS REBUILT, NOT PATCHED, AND WAS HIDING TWO SERIOUS DEFECTS: `J5` contact 1 carried PERMANENT RAW +3V3 against D-057, and THE COMMUNITY PORT HAD NO POWER AT ALL** — `01:ACC_3V3_SW` and `09:ACC_3V3_SW` were different nets, the latter fed by a second, DNP TPS22918 (`U15`), and `01:ACC_5V_SW` reached nothing outside sheet 01 (D-189). Also removed: the 26-pin 2x13 **male** header, XGPIO10-13, `FAST_IO_GPIO43_HDR`, `RESERVED_NC`. **SIXTH CONSECUTIVE SHEET WITH A LOAD-BEARING INHERITED DNP** — `U16`, `R49`, `R50` and six TVS arrays. **Connector footprint re-derived from the Samtec RECOMMENDED PCB LAYOUT REV B FIG 3**: 2.54 mm in row, **7.87 ±0.05 mm row-to-row**, 0.71 mm PTH, 27.94 mm pin field — a vertical 2x12 is NOT a substitute; all 24 contacts verified pin by pin against D-084 (D-179, D-180). **THE INHERITED 4.7 k EXTERNAL I2C PULL-UPS COULD NEVER HAVE WORKED** — 796 ns against a 300 ns fast-mode budget at 200 pF; now **1.5 k = 254 ns**, with a published accessory ceiling of 200 pF at 400 kHz and 400 pF at 100 kHz (D-181). **Both current limits RE-DERIVED, not copied**: 3.3 V stays 1.5 k but the accessory-short case moved 86% → **89% of the TPS63020's 2 A** because of the IR transmitter and the RGB (D-184); 5 V stays 1.65 k, setpoint re-checked at 4.99 V, peak inductor current 2.19 A so **I_sat >= 3 A must be confirmed (B-68)**, and the rail is verified independent of USB VBUS and the NFC fallback (D-185). **5 V ENABLES SPLIT** — `ACC_5V_BOOST_EN` on `U3` P13 and `ACC_5V_SW_EN` on **`U23` P04**, each with its own 100 k pull-down (`R131` new), giving two independent series disconnects and making the boost start into a known 44 uF instead of an unknown accessory; the 5 ms settle delay is **7x the 700 us typical soft start, which has no published maximum (B-69)** (D-186). **B-08 CLOSED IN COPPER** — `Q10` 2N7002 with the source facing the connector so the body diode blocks with the rail off; the 5 V-injection residual is bounded at ~3 mA and is why `R66` is 330R (D-187). **ALL SIX TVS ARRAYS WERE DNP AND ARE NOW FITTED** — one `TPD4E1B06DRLR` MPN covers all sixteen exposed contacts at 0.7 pF, `TPD2E009DBZR` leaves the BOM, and **deliberately no TVS on either rail** because VRWM 5.5 V against a 5.0 V rail has no margin; `ACC_DETECT_N` gains the 100R series D-090 had omitted (D-188). **Hot-plug detect bounce is firmware, 20 ms/20 ms — an RC would DELAY REMOVAL DETECTION, and removal is the safety-critical edge under MX-6** (D-183). Eighteen-case abuse matrix run: **nothing NOT ACCEPTABLE**. `#FLG0105`, deleted by the rebuild, turned out to be **the only power-output driver on the entire GND net** and was re-created with a note. **B-68, B-69 opened; O-7 raised** (1.5 k sized for an estimated 200 pF). **ERC 42 / 1 / 41 → 27 / 0 / 27 — ZERO ERRORS FOR THE FIRST TIME.** PCB untouched and still bit-identical to Beta-DM. **FBV2-S2 and PCB work NOT started.** |
| 2026-08-23 | FBV2-S1-008. Overall raised 53% → 55%. **No gate in the twelve-gate table passed**; the task gate **FBV2-S1-BUTTONS = PASS**. **`08_BUTTONS_EXPANDERS` MIGRATED — eight of nine sheets done.** **Task was INTERRUPTED by a session limit and RESUMED**; all work was uncommitted working-tree change, was inspected and classified, and nothing valid was discarded. **Both expanders are NXP `PCAL9535APW,118`, verified against the primary datasheet (Rev. 2, 23-Jan-2015) and NOT treated as a behavioural drop-in** — it powers up with **all interrupts masked**, the opposite of the TCA9535, so unchanged firmware sees no interrupts at all (D-164). `U2` = **0x20**, `U3` = **0x21**, preserved. **THE ALLOCATION GENUINELY FAILS: 35 committed signals against 32 pins**, with every escape closed — zero free native GPIO (B-10) makes the brief's own **WS2812 escape impossible**, `RESERVED_SPARE` is mandated by D-094 and the ten XGPIO by D-082. **Closed by `U23`, a THIRD `PCAL9535APW,118` at `0x22`: no new MPN, no new footprint, no new driver, no new rail, and B-37 RETIRED with 12 spare I/O** (D-165, **O-6 raised**). **Core, community and safety functions placed before the RGB by construction** — `U23` carries only the light and the spare, so declining O-6 costs nothing else (D-166). **`RESERVED_SPARE` DID NOT EXIST before this task**; it is now `U23` P03 with `R130` 100 k and `TP41` (D-173). **Front RGB LOCKED: MEIHUA `MHPA3528RGBCT` (LCSC C409779), common anode, PLCC-4, three unequal resistors 1k/680R/390R = 1.50/1.03/1.67 mA, white 4.20 mA** (D-167, D-168) — **dark by construction with NO external pull-ups**, because 06h = FF makes the pins high-Z and 02h = FF makes them drive HIGH on the transition (D-169). **Both charger STAT pins landed at 10 kΩ**, with the no-battery STAT2 toggle handled by the interrupt mask (D-170). **`TOUCH_INT_N`, `SD_CARD_DETECT_N` and `SX1262_DIO1` landed; `SX1262_BUSY` stays native; `SX1262_RXEN` stays expander-controlled with its pull-down.** **Six buttons, HOME deleted outright, volume not invented**, `PTS645SM43SMTR92LFS` verified orderable and the 10 µA wetting-current minimum checked for the first time (D-172). **O-5 CLOSED — IR receiver reverts to `TSOP38238` (AGC2), `TSOP38438` retained as a documented fallback** (D-163). **B-67 opened** — no published bounce time for the PTS645. Six root-sheet UUIDs with the non-hex prefix `fb080r00-` repaired. **ERC 42 / 1 / 41 — identical violation set to the recovered tree and better than the 45 / 2 / 43 pre-sheet-08 baseline; zero new errors.** PCB untouched and still bit-identical to Beta-DM. **Sheet 09 untouched.** |
| 2026-08-23 | FBV2-S1-007. Overall raised 51% → 53%. **No gate in the twelve-gate table passed**; the task gate **FBV2-S1-IR = PASS**. **`07_IR` MIGRATED.** **The whole IR subsystem arrived DNP — eight parts — and is now FITTED** (D-153), **the fourth consecutive sheet with a load-bearing inherited DNP; sheets 08 and 09 must be assumed to carry the same trap**. **IR TX locked Vishay `TSAL6100`**, with the **TSAL6200 fallback proven a true drop-in** — identical package, `VF` and `IFM`, so `R24` is unchanged (D-154). **Peak current 150 mA = 75 % of `IFM`**: `IFSM` 1.5 A is a **single-pulse ≤ 5 µs surge and cannot justify carrier current**; 200 mA leaves no tolerance margin and **300 mA is out of spec** (D-155). **Supply preference REVERSED to `+3V3`, not `SYS`** — regulated gives 118–170 mA against 64–166 mA on `SYS`, where **IR range would visibly shorten as the battery drains** (D-156). **`R24` 18 Ω → 12 Ω plus `R123` DNP parallel trim, never below 10 Ω total** (D-157). **`C12` 4.7 µF → 22 µF**: 4.7 µF gave 218 mV of carrier ripple, 22 µF gives 40 mV (D-158). **AO3400A pinout CONFIRMED 1 = G / 2 = S / 3 = D and the "needs the official AOS land pattern" blocker CLOSED — AOS publishes none**; safe-OFF proven at 10 mV against a 650 mV threshold (D-159). **Receiver `TSOP38238` → `TSOP38438`, a pure MPN change**, and the inherited `R21`/`C11` filter is now **quantified at 41 dB at 38 kHz against a Fig. 7 knee of ~10 mV RMS — ~90× margin, and it is what makes sharing `+3V3` safe** (D-160). **No new mutual-exclusion rule** — IR averages 17 mA against the audio amplifier’s 230 mA peaks (D-161). `TP39`/`TP40` added. **O-5 raised for CTO: Vishay marks AGC4 "No" for Sony code**, conflicting with the brief’s own protocol list; receive-only, and reverting is a `lib_id` change because the `TSOP38238` symbol was kept. **B-65, B-66 opened.** **ERC 45 → 45, zero added, zero removed.** PCB untouched and still bit-identical to Beta-DM. |
| 2026-08-23 | FBV2-S1-006. Overall raised 49% → 51%. **No gate in the twelve-gate table passed**; the task gate **FBV2-S1-AUDIO = PASS**. **`06_AUDIO` MIGRATED.** **`U5` and `J6` arrived from Beta-DM marked DNP — the speaker output path had never been built — and are now FITTED** (D-144), the third load-bearing inherited DNP in two tasks. **Microphone locked: PUI `DMM-4026-B-I2S-R` replacing the obsolete ICS-43434 — SEVEN pads, not six, so a new symbol and footprint were built from the manufacturer drawing**; `CONFIG`→GND is mandatory and has no ICS equivalent; **`R120` 100 kΩ on `I2S_MIC_DIN` is a data-sheet requirement the inherited sheet lacked**; **no 1.8 V rail is needed** despite the 1.8 V rating (D-145). **The brief’s 16 kHz cannot be run on the wire**: the microphone needs BCLK 2.048–4.096 MHz, so **the bus runs 48 kHz × 64 = 3.072 MHz and firmware decimates** (D-146). **MAX98357A retained, PRODUCTION, MPN `MAX98357AETE+T`; `GAIN_SLOT` GND → VDD (12 dB → 6 dB)** because at 12 dB the top **6.8 dB of digital range was clipped by the 3.3 V rail** (D-147). **Speaker locked: PUI `AS02008MR-LW152-R`**, Ø20 × 3 mm, 8 Ω, 0.5/0.8 W, 500–4000 Hz voice band, AWG #32 leads crimping straight into the existing `J6` — replaceable without soldering (D-148). **Default max software volume −6 dBFS → 0.17 W, ≈ 57 mA**; 0 dBFS is 0.68 W / 230 mA and must not be continuous (D-149). **EMI: nothing fitted** — the data sheet’s Figure 14 shows compliance with 12 in of cable and no filter; `R121`/`R122` 0 Ω fitted, `C81`/`C82` 1 nF DNP (D-150). Acoustic interface measured from the drawing: **Ø1.05 mm PCB hole, bottom port, mic on the face opposite the aperture** (D-151). No hardware AEC; `SD_MODE` is already a hardware mute for half-duplex voice (D-152). **B-61–B-64 opened.** **ERC 45 → 45, zero added, zero removed.** PCB untouched and still bit-identical to Beta-DM. |
| 2026-08-23 | FBV2-S1-005. Overall raised 47% → 49%. **No gate in the twelve-gate table passed**; the task gate **FBV2-S1-I2C-IMU = PASS**. **`05_I2C_DEVICES` MIGRATED.** **Reported-ERC correction: FBV2-S1-004 / 004B / 004C quoted "68"; the stored reports say 46** — the deltas were always right, the absolute number was not. **BMI270 re-derived from `BST-BMI270-DS000-08` Rev 1.6 and every inherited strap proved correct** (D-136); **B-44 CLOSED** (`IOH`/`IOL` ≤ 2 mA vs a 323 µA load). **The BMI270 has NO tap or double-tap feature in any configuration** — stated because the brief asked for it. **GPIO3 boot safety is now a timing proof**: `INT1_IO_CTRL` resets to output-disabled, `tH` = 3 ms, GPIO3 defaults Floating, so **the IMU cannot reach the strap window**; the pull-down makes **push-pull + active-high mandatory and open-drain forbidden** (D-137). **`INT2` stays DNC; `RESERVED_SPARE` untouched** (D-138). **Internal I²C pull-ups 4.7 kΩ → 2.2 kΩ** — at ≈ 85 pF measured, 4.7 kΩ gives `t_r` **338 ns and FAILS the 300 ns fast-mode limit**; 2.2 kΩ gives 158 ns at 1.32 mA sink (D-139). **BMI270 address made strappable: `R118` 0 Ω FIT → 0x68, `R119` 0 Ω DNP → 0x69, fit one only** (D-140). **IMU permanently powered, no load switch** — saves 9 µA, costs wake-on-motion (D-141). **`I2C_ADDRESS_REGISTRY.md` created and normative** (D-142). **BMI270 land pattern verified against §8.3 by rendering and measuring the drawing — "DO NOT ROUTE" discharged** (D-143). **B-59, B-60 opened.** **O-4 flagged for CTO: TCA4307-class hot-swap buffer with stuck-bus recovery at Sheet 09** — nothing implemented. **ERC 46 → 45, zero added, one removed.** PCB untouched and still bit-identical to Beta-DM. |
| 2026-08-23 | FBV2-S1-004C. Overall raised 45% → 47%. **No gate in the twelve-gate table passed**; the task gate **FBV2-S1-NFC-MATCHING = PASS**. **Antenna corrected A → B: `FXC.46.52.0075X.B.dg`, reverse ferrite**, bonds adhesive-side to the **inner rear shell**, ferrite facing inward — with the A version the ferrite would have sat between the coil and the tag (D-131). Board unaffected. **B-version parameters adopted**: `La` 1.10 µH, `Rs` 1.50 Ω, `Q` 60.37, `SRF` 395 MHz (D-132). **Target impedance DERIVED from the D-130 current budget — ≈ 36 Ω differential, Q ≈ 25 — the earlier 20 Ω/side assumption is discarded** (D-133). **First-build set calculated**: `R_q` 1R1 (Q 25.3), `C_s` 300 pF, `C_p` 1.5 nF, EMC **39 nH / 100 pF → f_c 20.1 MHz** — **B-56 CLOSED**, the old pair sat at 7.6 MHz below the carrier (D-134). **RFI SAFETY DEFECT FOUND AND FIXED**: the placeholder 47 pF / 220 pF divider would have put ≈ **4.4 V pk-pk on RFI against a 3.0 V rail**; new 27 pF / 620 pF gives ≈ 1.03 V pk-pk (D-135). **B-48 closed on substance**; **B-57, B-58 opened**. First-article tuning **required** with rear shell, antenna, PCB and battery all installed. **ERC 68 → 68, zero added, zero removed.** *(the 68 is a transcription error corrected in FBV2-S1-005; the stored reports say 46 → 46. The delta was right.)* | Overall raised 43% → 45%. **No gate in the twelve-gate table passed**; the task gate **FBV2-S1-NFC-ANTENNA-LOCK = PASS**. **NFC IC LOCKED `ST25R3916-AQET`, non-B — P-17 CLOSED** (D-126). **NFC antenna LOCKED Taoglas `FXC.46.52.0075X.A.dg`, off-board** — 13.56 MHz, 46 mm circular flex, 0.27 mm with ferrite, 3M peel-and-stick, 75 mm 28 AWG twisted pair, ACH(F), 40 mm typical read distance, all verified verbatim from `SPE-22-8-131-C` — **B-53 CLOSED** (D-127). **`J7` = JST `BM02B-ACHSS-GAN-ETF`** added between the matching network and the antenna; mating **proven** via `ACHR-02V-S` = the antenna's own ACH(F) housing, so **the antenna is replaceable without soldering** (D-128). **Brief corrected: JST classes ACH as TOP ENTRY, not right-angle** — the part is right, `J7` needs mating clearance above it. **Matching re-derived against the real antenna**: `R_q` 0 R → **1R0** (`Q` 58 → 25.8, derived from the antenna alone), `C_s` → **300 pF**, `C_p` → **1.8 nF** from an L-match with a stated assumption; **`L5`/`L6` + `C69`/`C70` deliberately NOT re-derived and flagged unbuildable (B-56)** (D-129). **NFC field current estimated ≤ 150 mA at 3.3 V; B-54 downgraded** (D-130). **B-06 CLOSED.** Mechanical: NFC clear region **48 × 48 mm**. **ERC 68 → 68, zero added, zero removed.** *(the 68 is a transcription error corrected in FBV2-S1-005; the stored reports say 46 → 46. The delta was right.)* B-55, B-56 opened. One item flagged for CTO: the **ferrite is directional** and Taoglas sells a reverse-ferrite variant — zero board change, but it must be settled against the enclosure stack before antennas are ordered. | Overall raised 40% → 43%. **No gate in the twelve-gate table passed**; the task gate **FBV2-S1-RADIOS-NFC = PASS**. **`04_SPI_B_RADIOS_NFC` MIGRATED.** **RF architecture locked (D-118):** 433 MHz internal Taoglas `FXP450.07.0100C` (IPEX MHF-I mating **proven** against the module's IPEX-1 socket), 915 MHz external to a top-panel **SMA female** bulkhead; **no board RF trace, matching network, switch or diplexer in either band**; the `U7` IPEX must stay service-accessible. Both module stamp-hole pins are explicit no-connects. **NFC: B-41 CLOSED** — `VDD`/`VDD_TX` moved to `NFC_SUPPLY` = `+3V3` (D-122, `sup3V` firmware requirement); **`Y1` 27.12 MHz crystal** + load caps (D-123); **real differential matching and RX-divider topology** with every value `TUNE` and two trim positions per TX leg (D-124); `AAT`, `CSI/CSO`, `EXT_LM`, `MCU_CLK` explicit no-connects with recorded reasons. **`SX1262_DIO1` published for sheet 08.** **Zero `*_TBD` nets remain in the project.** **ERC 4 errors → 2, total 64 → 46, zero added** — the first migration task to reduce the error count. **P-17 recommended for closure (keep the non-B); B-53 opened** (antenna architecture). B-48, B-49, B-50, B-51, B-52, B-54 opened. PCB untouched and still bit-identical to Beta-DM. | Overall raised 37% → 40%. **No gate in the twelve-gate table passed**; the task gate **FBV2-S1-DISPLAY-SD = PASS**. **`R111` FITTED** (D-111). **`03_SPI_A_DISPLAY_SD` MIGRATED:** new `ER-TFT035IPS-6_50P` symbol with the vendor pin table verbatim, **catching two dead-on-arrival faults in the inherited `J1`** — reversed backlight anode/cathode and swapped SCL / D-CX. Touch gains `TOUCH_INT_N` (panel pin 46, previously unrepresented). Backlight re-derived: `R69` **1.87 Ω**, `R70`–`R73` **4 × 33 Ω**, I_LED **109 mA typ / 117.6 mA worst case** against a 120 mA panel maximum; peak switch current 4.6× (3.9× at f_SW min). `SD_CARD_DETECT_TBD` → **`SD_CARD_DETECT_N`** with a 100 kΩ pull-up. `R112` 0 Ω **DNP** isolates the display SDO from the shared SPI-A. **B-43, B-32, B-28 CLOSED; B-46, B-47 opened.** `/03_SPI_A_DISPLAY_SD/LED_A` added to the `LED_BOOST` netclass — a latent FBV2-P2 defect no probe would have caught. **ERC 4 errors → 4 errors, error report byte-identical.** PCB untouched and still bit-identical to Beta-DM. | Overall raised 34% → 37%. **No gate in the twelve-gate table passed**; the task gate **FBV2-S1-MCU-CORE = PASS**. **P-20, P-21 and P-22 CLOSED** (D-104…D-110). `R95` locked at **560 Ω** — recovery **8.36 mA** nominal, and **B-27's ceiling amended to ≈ 15.9 mA** because 680 Ω was the value that produced its old ≈ 13 mA figure. LTC4368 **OV trip derived to 4.63 V** (`R77` 3.65 M / `R78` 442 k) from the datasheet's 492.5/500/507.5 mV threshold; **removes a BOM line**. Scripted KiCad edits permitted under an **eight-condition** standing rule. **`02_MCU_CORE` MIGRATED:** GPIO38 = `NATIVE_A`, GPIO47 = `NATIVE_B`, GPIO46 = `DISP_BL_CTL` with `R108` 10 kΩ strap pull-down + `R109` 0 Ω isolation link + `TP2`, GPIO43 withdrawn from the community port (`TP35` UART0 TXD), **GPIO3 strap closed — B-09 retired**, `R111` 10 kΩ GPIO45 pull-down placed **DNP**. **ERC 5 errors → 4, zero new; `02_MCU_CORE` clean.** B-43, B-44, B-45 opened. **NO NEW DEBUG HARDWARE** — USB Serial/JTAG is the service interface. PCB untouched and still bit-identical to Beta-DM. | Overall raised 31% → 34%. **No gate in the twelve-gate table passed**; the task gate **FBV2-S1-POWER-TREE = PASS**. **First Full Beta v2 design-file work.** `hardware/beta-v2/` forked from Beta-DM with a **re-runnable** byte-equivalence proof; **`01_POWER_TREE` CAPTURED** — P2 reverse protection with `U18` LTC4368-1, autonomous dead-cell recovery, `ACC_3V3`/`ACC_5V` on one consolidated boost + load-switch BOM, NFC 3V3-FIT/5V-DNP select, `VBUS_PRESENT` telemetry, 19 test points, 136 parts. **ERC 58 baseline → 55, zero introduced** (three inherited violations retired). **B-01 closed at schematic level.** `U18` package corrected from a policy-violating DFN-10 to MSOP-10. Inherited `R_FB_TOP 1M` net label renamed `V3V3_FB`. **D-099…D-103 recorded; B-41, B-42, P-20, P-21, P-22 opened.** PCB untouched and still bit-identical to Beta-DM. |
| 2026-08-22 | Created. FBV2-A0 recorded as PASS. Initial blocker set B-01 through B-16 imported from the pre-design audit. |
| 2026-08-22 | FBV2-ARCH-001. Overall raised 8% → 10%; **no gate passed.** B-07 retired as incorrect. B-17/B-18/B-19 added. FBV2-A2 marked as the recommended next gate. |
| 2026-08-22 | FBV2-ARCH-002. Overall raised 10% → 13%; **no gate passed. FBV2-A1 assessed CANNOT PASS** (4 of 8 criteria). B-18 closed, B-25 closed. B-20…B-24 added. P-11…P-18 opened. Standing **NO-RESPIN RECOVERY POLICY** (D-049) established. |
| 2026-08-22 | FBV2-PWR-001. Overall raised 13% → 15%; **no gate passed. FBV2-A1 FAIL, 5 of 6 criteria closed.** D-061…D-064 recorded. **P-13 and B-24 closed** by primary-source evidence; B-22 closed. Complete battery-protection topology specified. Fuse **REQUIRED**, clamp **REQUIRED**, PTC **REJECTED**. |
| 2026-08-22 | FBV2-DISP-001. **No gate passed — percentage holds at 25%.** D-071/D-072/D-073 recorded. Display size LOCKED at **3.5″**; battery envelope LOCKED. **Display MPN and J1 deliberately NOT locked** — old-J1 compatibility is **UNPROVEN**. ESP32-S3 SPI verdict **PASS** (FSPI IO_MUX, 80 MHz, no bus merge). M-01/M-02 closed; **M-06/M-07 opened.** |
| 2026-08-22 | FBV2-MECH-001. Overall raised 20% → 25%. **FBV2-A2 = PASS.** D-069/D-070 recorded; cavity **75.0 × 155.0 × 18.5 mm** derived; PCB target **70 × 148**; **P-07 closed**; M-01/M-02 opened. Beta-DM 74 × 155 outline ruled **RE-FLOORPLAN REQUIRED**. Next gate: **FBV2-S1**. |
| 2026-08-23 | FBV2-COMM-002. **Overall HELD at 31% — a correction is not progress.** **Harwin `M20-7881242` REJECTED as obsolete** (404 on harwin.com; the MPN had been configured from an ordering scheme, which FBV2-COMM-001 had flagged). **Connector re-locked: Samtec `BCS-112-S-D-HE`** — 2×12 female Tiger Claw, horizontal entry, through-hole, 30 µin gold, ACTIVE, 385 pcs next-day, MOQ 1, 4.6 A/contact. `-S` chosen over the proposed `-L` because Samtec qualifies **both** platings at only **100 cycles** and the **2 500-cycle** extended-life data exists **only at 30 µin gold** — +$2.88/board. **Z column improves 22.30 → 19.53 mm of 23.0 (3.47 mm spare).** Pin ordering and electrical architecture **unchanged**. **O-1 approved** (`FLT` wire-OR → `ACC_POWER_FAULT_N`, `U3` P16 = `RESERVED_SPARE`), **O-2 approved** (I²C `0x50` reserved for an accessory-ID EEPROM), **O-3 rejected**. D-093…D-098 recorded; B-39, B-40, P-19 opened; B-37, M-09, M-10 downgraded. |
| 2026-08-23 | FBV2-COMM-001. Overall raised 28% → 31%. **No gate in the twelve-gate table passed**; the task gate **FBV2-COMM-LOCK = PASS**. **The 20-pin community port is SUPERSEDED.** New port **2×12, 24 active contacts, FEMALE device side**, ~~`Harwin M20-7881242`~~ *(rejected as obsolete 2026-08-23 — see FBV2-COMM-002)*, keying and shroud from the enclosure. Pin ordering locked with every power contact GND-paired so no row swap can put 5 V on a logic pin. **New 5 V accessory rail** `SYS → TPS61023 → TPS22950C → ACC_5V_SW`, and `+3V3 → TPS22950C → ACC_3V3_SW`; **one load-switch MPN and one boost MPN across both rails**. D-081…D-092 recorded. **P-02, P-15, P-16 and B-08 CLOSED**; B-34…B-38, M-09, M-10 opened. **Zero spare expander capacity now remains anywhere.** |
| 2026-08-23 | FBV2-DISP-002. Overall raised 25% → 28%. **No gate in the twelve-gate table passed**; the task gate **FBV2-DISP-LOCK = PASS**. **Display LOCKED** — EastRising `ER-TFT035IPS-6` + `ER-TPC035-6` (ILI9488 + FT6236 @ 0x38), 56.54 × 84.96 × 3.95 mm, one 50-pin 0.50 mm **bottom-contact** 0.30 mm FPC. **`J1` LOCKED** — Hirose `FH69-50S-0.5SH`, mating proven from both manufacturers' drawings, on the FH12/FH52E land pattern for a JLC second source. **Backlight closed** — TPS61169 retained, `R69` 2.55 R → **1.87 R**, `R70`–`R73` 4 × 39 R → **4 × 33 R**. D-074…D-080 recorded. **M-06 and M-07 CLOSED**; B-28…B-33 opened. ST7796S formally rejected on availability (D-078). |
| 2026-08-22 | FBV2-PWR-002. Overall raised 15% → 20%. **FBV2-A1 = PASS** — first gate since A0. D-065…D-068 recorded. Pass path changed to **P2** (4 FETs, 2 packages). Dead-cell recovery specified to component level. **P-11, P-12, B-20, B-21, B-23 closed**; B-26/B-27 opened. Clamp **demoted to secondary**, fuse **resized 3 A → ≈5 A**. Next gate: **FBV2-A2**. |
