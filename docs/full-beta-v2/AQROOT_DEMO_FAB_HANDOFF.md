# AQROOT Demo — FABRICATION HANDOFF


> # **STATUS: READY FOR FABRICATION — BOARD AUTHORITY `8c548ece` (through D-776, 2026-09-19).**
>
> **This banner supersedes every status block below it.**  D-765's banner, which
> stood here unchanged through D-766…D-770, is retained as history.
>
> **The path from there to here, in one line each:**
>
> * **D-766** closed external review round 2's second item (firmware fault /
>   warm-reset handling) and found five more defects on the way — `Q11` a 30 V
>   part on a node this board publishes at 39 V, a GND barrel inside `L4`'s
>   printed no-via strip, a `MAX17048` `VCELL` read 16× low, a non-deterministic
>   ampacity audit, and `LAND8` blind to rotated instances.
> * **D-767** asked both of D-766's defect classes of the whole board and
>   corrected an arithmetic error in D-766 itself.
> * **D-768** found the **released BOM naming the wrong display**, and proved the
>   BOM-row leg of `F7` load-bearing by walking into it.
> * **D-769** found the other superseded part name (`U8`'s retired `FXP890`
>   antenna) and turned `F7` into a registry.
> * **D-770** re-declared readiness on board `5849b658`.
> * **The CTO withdrew that declaration for one item** — *D-098 locks first-five
>   `ACC_3V3_SW` = 400 mA total and `ACC_5V_SW` = 300 mA total; the 2.7 kΩ
>   `TPS22950-Q1` settings guarantee only ~277 mA per rail* — and **D-771 closes
>   it**, together with a second defect of the same shape that chasing it exposed
>   in the battery protection chain.
>
> **D-771 in three sentences.**  `R97` → **1.78 kΩ** and `R101` → **2.32 kΩ**
> (moved again to **2.37 kΩ** by D-773 below), so each accessory rail
> **GUARANTEES** the budget D-098 publishes for it — **0.428 A against 400 mA
> and 0.315 A against 300 mA as fitted** — instead of the 0.277 A the old
> setting guaranteed.  `R75` → **10 mΩ**, because ADI guarantees the `LTC4368`'s forward
> threshold only as 40/50/60 mV and at 15 mΩ the **LATCHING** breaker's band
> overlapped the charger's **RECOVERABLE** `IBAT_OCP` band — so on an unlucky
> unit the latching protection fired first.  **Zero copper objects moved**; every
> copper Gerber is byte-identical to the D-770 package apart from its timestamp.
>
> **Full D-771 verification:** promotion PASS with 0 objects added or removed;
> connectivity 174 retained / 173 connected / 1 owner-approved open (`U11.3`) /
> **0 unapproved**; KiCad DRC **199 `lib_footprint_issues`, all warnings, zero
> other classes**, 17 unconnected; parity **246 warnings / 0 errors**; protected
> copper 15 nets / 406 objects, differences `{}`; `D-186`/`D-269` live and true;
> rail ampacity `all_ok`; **F1–F7 PASS**; **FAB1–FAB15 PASS**, sourcing
> **252/252**, coverage 1.0; **19 standing contracts, none failing**; firmware
> **H1–H6 PASS** and four PlatformIO builds SUCCESS; `hardware/beta-v2`
> UNTOUCHED.  There is **no open owner decision** and **no unresolved Demo
> fabrication blocker**.  Residual risks are named in `CTO_DECISIONS.md` **D-771
> §10** and **D-770 §5**.
>
> **D-772 then found the bad input to the clause D-771 had just built.**
> `F6`'s internal `+3V3` load was a hand-written `1.0 A`, and every margin the
> contract reports is a function of it.  The repository's own last derivation
> (823 mA) contains **no NFC line at all** — `U9` was DNP when it was written and
> **D-192 fitted it**, **D-205** allocated 100 mA with the field on — and it
> counts *"the worst single radio"*, which is not true of a board whose `U8` is
> an external module on its own `+3V3` pin.  The budget is now **nine cited
> lines, summed: 1.063 A**, and `F6` reads the board's own `+3V3` net so no fitted
> consumer can go unbudgeted.  **No PCB, schematic, value or MPN change**; every
> Gerber and CSV in the package is byte-identical.  `F6` runs **eighteen**
> controls.
>
> **D-773 then derived the last constant in that chain.**  The 5 V rail's
> setpoint was **4.95 V** in the contract and **4.99 V** in `ARCHITECTURE.md`,
> *both* from `VREF` = 0.6 V — and TI publishes **580 / 595 / 610 mV**.  Over
> `R99`/`R100` the real band is **4.742 / 4.950 / 5.165 V**; costed at the
> worst-case high, D-771's `R101` = 2.32 kΩ left **0.52 %** of pack margin, so
> `R101` → **2.37 kΩ**, the E96 value nearest the centre of its own legal window
> (2.298–2.478 kΩ).  `F6` also refuses a divider whose worst case reaches the
> `TPS61023`'s own `VOVP` minimum; it clears by 6.1 %.  **The board's thinnest
> margin is 1.6 %** and it is a compound-fault state whose consequence is a
> recoverable hiccup; at a conforming accessory load it is 7.3 %.
>
> **D-774 closed the same class one step over, with no board change at all.**
> `screen_bom_sourcing` states a **2× capacitor derating rule** and a 48-node
> voltage table, and runs it **only while proposing a part for an UNSOURCED
> line** — of which this BOM has had none since D-615, so the rule had never
> been applied to a fitted part.  Run against them: **every fitted capacitor
> survives its node's absolute maximum**; five 10 V X7R parts on 5 V-class rails
> sit at **1.91–1.94×** against the 2× convention and are accepted as named,
> reasoned exceptions (the bias loss the convention exists for is already in
> D-186's 44 µF nominal sizing, and a 22 µF 16 V X7R is not an 0805 part).  Two
> node declarations on the rail D-773 had just derived were corrected.  `F8` is
> the new clause; the fabrication package is **byte-untouched**.
>
> **D-775 closes the later CTO normal-concurrency hold.**  F6 had still priced
> D-098's simultaneous normal 400 mA + 300 mA load as an ideal source, and
> firmware used the same 3.50 V floor for one or two rails.  MAX17048 actually
> measures `BAT_PROTECTED_P`, the same node as BQ25185 BAT, so D-775 starts at
> that real measurement point and **solves the floor rather than asserting it**.
> Four live PCB paths are extracted every run, hot-copper scaling is applied,
> BQ25185 BATFET uses TI's 140 mΩ max with a declared 1.40× low-VBAT/high-current
> allowance, and TPS22950-Q1 RON is included.  The worse path-bound result for
> 10% OCP headroom is **3.7622 V**, rounded upward to **3.80 V**; single-rail
> requirement is only 3.1232 V, so the existing 3.50 V floor stays.  Firmware
> enforces **3.50 V single / 3.80 V dual**, fails closed on unreadable VCELL and
> sheds 5 V first below the dual floor.  At the live board the simultaneous
> published load models **2.2499 A, 12.20% below** `IBAT_OCP` minimum.  F6 and
> the firmware host suite cross-check the same policy with destructive controls.
> **No PCB, schematic, BOM, CPL, Gerber or drill artifact changed.**
>
> **The assembly PDFs print `RELEASE D-773`.**

---

> **D-776 corrected a false as-built instruction and made the class computable.**
> The generated map told firmware to infer charging state from *VBUS presence*,
> and `/01_POWER_TREE/VBUS_PRESENT` — a fitted 150k/220k divider with an RC
> filter — reaches `TP31` and nothing else.  Two more of the same shape were
> undeclared: the `LTC4368`'s latching FAULT output and the `TPS63020`'s POWER
> GOOD.  The list of probed-but-unreadable nets is now **derived off the copper**
> and the generator refuses to emit on a gap in either direction.  **Firmware
> must display state-of-charge, not a charging state.**  The board fix — moving
> `R104`/`R105`/`C68`/`TP31` beside `U3`, zero BOM change — is measured and is a
> **REV-B** item; no promised capability is missing.  No copper moved.
>

## ENGINEERING HANDOFF — D-777 · D-778 · D-779, board `880a2ece`, 2026-09-19

> **THE ROUND-3 EXTERNAL REVIEW HOLD ON D-776 IS CLOSED.**  All six reproduced
> items are corrected by measurement, and **NOT ONE COPPER OBJECT MOVED**: every
> copper Gerber, both drill files and `Edge_Cuts` are byte-identical to the
> D-776 package apart from timestamps.  One BOM row changed — `C85`
> 100 nF → 1 µF, onto a line this board already buys.
>
> **1 · THE BATTERY CONNECTOR HAD NO RATING IN THIS REPOSITORY (D-777).**  `J4`
> is a JST `B2B-PH-K-S(LF)(SN)`, published at **2 A AC/DC (AWG #24)** — the
> **lowest number in the whole battery path**, below the `BQ25185`'s 2.5625 A
> `IBAT_OCP` minimum, D-771's 3.960 A breaker and `F1`'s 5 A fuse.  D-775's
> published simultaneous envelope sat at **2.2715 A, 13.6 % over**, and D-776
> passed in that state.  Holding it under 2 A by `VCELL` alone needs a
> **4.16 V** pack, so the bounded term is the **internal** one: while BOTH
> accessory rails are enabled, firmware **reserves** the sub-GHz TX path, the
> NFC field and the IR transmitter, enforced in `SpiBusB::beginTransmit`.  The
> connection carries **1.8797 A, 6.0 % inside its published rating**.
>
> > **REVIEWER, READ THIS ONE CLOSELY.**  This is the only change in the cycle
> > that constrains product behaviour.  **Neither published budget moves** —
> > `ACC_3V3_SW` 400 mA and `ACC_5V_SW` 300 mA are both still guaranteed, and
> > each rail alone still runs to a 3.50 V cell with all three subsystems fully
> > available.  What is bounded is a *concurrency*: an accessory holding **both**
> > switched rails cannot coincide with a sub-GHz transmit, the NFC field or an
> > IR burst.  It is the same shape as D-775's VCELL condition and is in
> > DEVICE_SPEC §6.3a's mandatory accessory-facing wording.  **The alternative
> > considered and rejected was a 4.16 V dual-rail floor, which would have
> > deleted the simultaneous capability in all but name.**  The permanent fix —
> > JST `B2B-XH-A`, 3 A, confirmed live, `C158012` — is **deferred to REV-B**
> > because it needs an owner protected-copper exception on `BAT_CONNECTOR_P`,
> > grows the courtyard against a 0.52 mm gap to `C60`, moves a part already
> > carrying an `MK10` `DISPLAY_SHADOW` finding, and requires re-terminating the
> > selected pack's leads.  **CTO_DECISIONS D-777 §6 carries the full costing.**
>
> **2 · THE DERATING RULE WAS RUN AGAINST THE SPECIFICATION, NOT THE PART
> (D-778).**  **Twenty-four value strings understate the part the BOM buys** —
> `C20` reads 10 V and buys a 25 V part — so three of D-774's five exceptions
> were against a rating this board does not have.  Ratings now come from the
> part, joined reference → LCSC → the committed live distributor record; **all
> 76 fitted capacitors are covered** and a missing record is a refusal.  Nothing
> fails its node's absolute maximum; **the exception list drops from five to
> two**, removed by the clause rather than by hand.
>
> **3 · AN EXTRACTED DATASHEET CHANGED A UNIT AND A PROOF WAS BUILT ON IT
> (D-779).**  D-766's `Q11` conduction proof read *"VGS(th) … at **ID = 250 mA**"*;
> the datasheet says **250 µA**.  The PDF text extraction maps Symbol-font `Ω`
> to `W` and `µ` to `m` — the same table also reads `RDS(ON) 160mW` (the
> committed JLCPCB record says **160 mΩ**) and `IDSS 1 mA at 44 V` (**44 mW
> standing** in a SOT-23).  **The artifact is isolated**: of fifteen archived
> vendor texts this is the only one with bare `W` suffixes *and* zero `µ`
> glyphs.  The real ordering margin was therefore smaller than the 2.06 ×
> claimed by an **unpublished** amount, so `C85` 100 nF → **1 µF** makes the
> invariant independent of that band — worst-case `tau` 19.6 → **147 ms**, the
> window in which the ordering can fail **407 → 44 mV** against a **104 mV** bar
> taken from the datasheet's own guaranteed conduction point.
>
> **4 · FOUR MORE OF THE SAME SHAPE (D-779).**  *"A hiccup that auto-retries"*
> was **half** of SLUSF65B 6.3.7.3 — 4 to 7 consecutive trips in a 2 s window
> leave the BATFET off **until a valid VIN is connected**, so a sustained
> accessory overcurrent is a battery-only dead stop the user clears with USB;
> `F6` now parses the limit rather than quoting the sentence.  The firmware
> fault path could **forget a failed shutdown**, and its blanket safe-state
> fallback **did not tell its caller** it had dropped all three accessory
> outputs.  A successful I²C read was treated as a measurement, so **`0xFFFF`
> decoded to 5.1199 V and authorised the second rail** — now a 2.50–4.50 V
> plausibility band, `HIBRT = 0x0000` for freshness, and a settled post-enable
> recheck.  D-751's control had gone **vacuous** and is replaced one layer down
> rather than deleted.
>
> **5 · THE INSTRUCTIONS AND THE PACKAGE (D-779).**  This handoff told the
> assembler to trim `J4` to **0.80 mm**, which is the `DISPLAY_SHADOW`
> **ALLOWANCE** and was never the target — D-770 retightened `J4-T1` to
> **≤ 0.50 mm** with `J4-T2` inspect-after-cutting and `J4-T3`'s ≤ 0.10 mm
> polyimide patch.  **169 of 252 fitted placements are on the BOTTOM side** and
> no placement convention was stated anywhere — now **derived** into the fab
> notes from the position file itself, bottom-side rotation convention included,
> with a mandatory placement preview.  And the package **never stated its own
> stackup, finish or test requirement** in anything a human reads, and
> **nothing required a bare-board electrical test**: ampacity is sized on
> **0.0152 mm** inner foil and `J4`'s trim on the **1.5744 mm** declared stack,
> both now named as not substitutable, with **E-test required on every panel**.
>
>     connectivity     174 retained, 173 connected, 1 owner-approved open
>                      (U11.3), 0 UNAPPROVED open edges, ratsnest 17
>     KiCad DRC        ZERO violations of every class; 17 unconnected (the
>                      approved set); parity 246 WARNING / 0 ERRORS
>     protected copper 15 nets / 406 objects, IDENTICAL to d776
>     ampacity         all_ok, byte-identical to d776
>     features         F1-F8 PASS
>     battery pack     B1-B8 PASS, byte-identical to d776
>     land / mech      LAND1-LAND8, MK1-MK10 PASS, 315/315 MATCH
>     fab package      re-exported; FAB1-FAB15 PASS, provenance PASS,
>                      0 unsourced lines
>     contracts        19 standing contracts ran, ALL PASS; every report
>                      byte-identical to d776 except demo_feature, leaf_land
>                      and the two carrying the board digest
>     firmware         H1-H6 PASS; 165 host claims, 20 destructive controls,
>                      NONE uncaught; four builds SUCCESS
>     hardware/beta-v2 UNTOUCHED
>
> **WHAT THIS ITERATION COULD NOT CLOSE, AND IT IS EXTERNAL**: fabricator
> written acceptance of the `J3` NPTH concession, the `MK1` acoustic mask
> opening, the POFV process for 136 lands, the 38 sub-floor via rings, the 21
> sub-0.125 mm mask dams, the exact 6-layer / 0.0152 mm-inner stack, the stepped
> profile and tooling, ENIG, and bare-board electrical test.  **All of these are
> now declared in the fab notes; the confirmation is an order-time action with
> the board house** (risk §8).

## ENGINEERING HANDOFF — D-776, board `8c548ece`, 2026-09-19

### Final board status

Six layers, **77.0 × 148.0 mm**, `JLC06161H-7628` stack (1 oz outer / 0.5 oz
inner), **fabrication-ready**.  Board authority **`8c548ece`**.

### Major design changes in this round

Five decisions in the final closure sequence. D-771–D-774 closed stated numbers/rules
that were not derived or applied; D-775 closed the cross-domain gap between the
normal accessory-load model and the firmware VCELL policy. **No copper moved in
D-775**, and the fabrication package remains the D-773 package bound to board
`8c548ece`.

| | what was wrong | fix |
|---|---|---|
| **D-771** | the board **published an accessory budget its own limiter could refuse to deliver** (D-098's 400/300 mA against a guaranteed 0.277 A), and the protection chain was **ordered against a 50 mV typical** so the LATCHING breaker's real band overlapped the RECOVERABLE charger trip | `R97` → **1.78 kΩ**, `R101` → 2.32 kΩ, `R75` → **10 mΩ** |
| **D-772** | the internal `+3V3` term every margin depends on was a **hand-written `1.0`**, missing the NFC front end `D-192` fitted and assuming a "worst single radio" nothing enforces | **nine cited lines, summed: 1.063 A**, gated against the board's own `+3V3` net |
| **D-773** | the 5 V setpoint was **4.95 V here and 4.99 V there, both from a `VREF` TI does not publish** | setpoint **derived** (4.742 / 4.950 / 5.165 V); `R101` → **2.37 kΩ**, the E96 value nearest the centre of its computed legal window |
| **D-774** | the **2× capacitor derating rule had never once been run** against a fitted part | `F8`; five named, reasoned exceptions; two node declarations corrected |
| **D-775** | D-098 normal 400/300 mA concurrency was still an ideal-source calculation and firmware had one 3.50 V floor | live-board/path-bound solver + **3.50 V single / 3.80 V dual** firmware policy; fail-closed/5V-first shedding host tests and F6 controls |
| **D-776** | the as-built limits told firmware to infer charging state from **VBUS presence**, and no VBUS-present signal reaches firmware; two more unreadable signals were undeclared | the probed-but-unreadable list is **computed off the copper** (28 nets, 7 signals) and the generator refuses to emit on a gap in either direction; four new controls; board fix measured and deferred to Rev-B |

### Connectivity

**174** retained multi-pad nets, **173 connected**, **1 owner-approved open**
(`U11.3` `/BQ25185_STAT2`, D-742), **0 UNAPPROVED open edges**, raw ratsnest 17.
The three RGB replacement nets (`FRONT_RGB_R_N`/`_G_N`/`_B_N`) are whole with
zero open edges.  Approved NCs are exactly the eight `J5` positions Demo scope
names.

### DRC

**199 violations, ALL `lib_footprint_issues`, ALL WARNING, ZERO of every other
class.**  17 unconnected items (the owner-approved `U11.3` and its ratsnest
family).  Schematic/PCB parity **246 warnings, 0 ERRORS**.

### Safety and power

`D-186` and `D-269` are **live `dru_contracts` and TRUE on this board**, and the
battery protection is **materially better than at D-770**: the recoverable
`IBAT_OCP` band (2.5625–3.6875 A) now sits **entirely below** the latching
`LTC4368` breaker (3.960–6.061 A) with 6.9 % of ordering margin, where at 15 mΩ
the two **overlapped by 1.05 A**.  Rail ampacity `all_ok`; the two accessory
rails and `+3V3` are measured for the first time.  Both accessory rails
**GUARANTEE** the budget D-098 publishes (+7.0 % and +4.9 %). D-775 separately
proves normal simultaneous 400/300 mA operation at the enforced **3.80 V VCELL**
floor with **12.20%** modeled margin to BQ25185 OCP minimum; single-rail cases
at 3.50 V retain **30.69% / 25.55%**. Battery-pack contract `B1–B8` PASS.

**The thinnest margin on this board is 1.6 %**, named exactly: the 5 V accessory
**in overcurrent** while every internal subsystem runs at once, on a charger at
the −18 % corner, cell at 3.0 V, boost at the top of its band — six unlucky
corners at once, consequence a **recoverable `IBAT_OCP` hiccup**.  That is a fault-envelope number;
D-775's normal conforming dual-rail operating contract is **12.20%** at its
firmware-enforced 3.80 V VCELL floor.

### USB / RF / NFC / features

`F1–F8` PASS.  Retained RF (SX1262 + CC1101), NFC (ST25R3916 front end with
`RF1–RF5` symmetry), USB, display, audio, IR, microSD and accessory power all
present, fitted and whole.  `LAND1–LAND8` and `MK1–MK11` PASS.

### Manufacturing package

`FAB1–FAB15` PASS.  **29 files, 24 deterministic**, release **`D-773`**.
Sourcing **252/252 orderable, coverage 1.0**, 0 unsourced lines.  Gerbers,
drills, BOM (125 lines), CPL, fabrication notes and assembly drawings all
regenerated and checked.  **19 standing contracts, none failing.**  Firmware
`H1–H6` PASS; the D-775 power-policy host test passes **23/23** and all three
of its destructive C++ controls are caught (the dual floor collapsed onto the
single floor, an unreadable gauge failing open, and the 5 V-first shed order
lost); all four PlatformIO environments build SUCCESS.
**`hardware/beta-v2` UNTOUCHED — 0 modified paths across the whole round.**

### Significant remaining prototype risks

1. **`U11.2`'s `BAT` land** — 0.200 mm `DLH0010A` package land, model ceiling
   **51.5 K** at the 2.438 A sustained worst case.  The model ignores lateral
   spreading, conduction and convection, and the copper is necked for only
   0.575 mm against a ≈2.6 mm thermal length.  **First-article thermal
   measurement at the 3.0 V corner with both accessory rails loaded.**
2. **`U11.3` / `STAT2` intentionally unconnected**, owner-approved (D-742), with
   `R128`/`TP7` retained for probe and bodge.
3. **The 1.6 % compound-fault margin** above — measure `IBAT_OCP` behaviour with
   a deliberately overloaded 5 V accessory at first article.
4. **The 5 V rail's −5.2 % low corner** (4.69 V at the connector at the bottom of
   the boost's own setpoint band).  Inherent to the `TPS61023`'s ±2.5 % reference,
   not to the divider.
5. **`L2`'s DNP strip**, **`D8`'s 1.0 V margin**, **`Q11`'s deliberate 2.06×
   ordering margin** — all carried from D-770 §5 unchanged.
6. **Procurement, not design**: the touch silicon (`CST026` vs `FT6236` — the PO
   must name **both** `ER-TFT035IPS-6` and `ER-TPC035-6`), the panel FPC tail
   thickness against the Hirose `FH69`, and nine BOM lines under 10× the
   first-five need.
7. **Enclosure CAD** — BOOT face, power-switch position, 1×24 wall aperture,
   corner radii — remains CAD-TO-VERIFY and is not PCB work.

### Recommended post-Kickstarter improvements

* **Re-spin `U11`'s `BAT` escape** — a charger whose `STAT2` pin is not adjacent
  to `BAT`, or a package with a land taller than 0.200 mm, closes both risk 1 and
  risk 2 at once.
* **A tighter 5 V reference** for the accessory boost would close risk 4; the
  divider cannot.
* **Widen the accessory envelope** to D-098's 600–800 mA / 500 mA targets once
  first-article measurements replace the stacked worst cases this round had to
  assume — the limiting term is the compounded internal `+3V3` budget, which a
  real measurement will shrink.
* **Read capacitor ratings from the released BOM row** rather than the value
  string, closing `F8`'s stated 39-part boundary (the leg D-768 proved
  load-bearing for `F7`).


> # **STATUS: NOT READY — READINESS WITHDRAWN, ONE OF TWO CAUSES CLOSED (D-765, 2026-09-18).**
>
> **BOARD AUTHORITY `9e4728ae`** (copper byte-identical to `1a06b058`; only the two
> accessory-limiter footprint `descr`/`Value` fields and a `.kicad_dru` comment
> section changed).  External review round 2 withdrew D-764's declaration for **two**
> items:
>
> 1. **An unsupported `TPS22950C` `ILIM` setting — CLOSED BY D-765.**  D-753's
>    0.407 A envelope is retained in full, but the `TPS22950C`'s OWN specified
>    `ILIM` range is **0.5–3.5 A** (`SLVSFJ2B` §5 Device Comparison Table), so the
>    setting sat 19 % below its recommended operating condition.  `U20`/`U22` are
>    now the **`TPS22950-Q1`** (`SLVSGP6A`, orderable **`TPS22950CQDDCRQ1`**, LCSC
>    **`C17349276`**), specified **0.05–3.5 A**, on the **same `DDC0006A` land
>    pattern and pinout**, with the same auto-retry, RCB, `FLT` semantics and TSD,
>    plus AEC-Q100 grade 1.  **No resistor, no copper and no envelope number
>    changed.**  `F6` now refuses any `ILIM` outside the fitted part's own published
>    range and runs eight controls.
> 2. **Firmware fault / warm-reset handling — STILL OPEN.**  Not part of the D-765
>    transaction.  **This is why readiness is NOT re-declared here.**
>
> Full D-765 verification: promotion 16/16 with 0 objects added or removed; routing
> 173/174 with only owner-approved `U11.3`; DRC 199 `lib_footprint_issues` all
> warnings; parity 246 warnings / 0 errors; protected copper identical; F1–F6 and
> FAB1–FAB15 PASS; assembly PDFs now print `RELEASE D-765`.  There is **no open
> owner decision** and **no unresolved PCB or fab-data blocker**.
>
> **D-764's declaration text is retained below as history.**
>
> **STATUS WAS: `DEMO_READY_FOR_FAB` — DECLARED AT D-764, 2026-09-18, ON BOARD
> AUTHORITY `1a06b058`.** This superseded every earlier readiness declaration.
> The PCB itself is unchanged since D-759. D-764 closes release/assembly ambiguity:
> all five leaded THT refs (`J4`, `J5`, `J6`, `D1`, `U6`) are now unambiguously
> hand-soldered after reflow, the current 1×24 J5 identity/drill is the only current
> assembly authority, and the released top/bottom assembly PDFs carry **D-764, full
> board SHA256, side/mirror convention, pin-1/polarity and manual-operation notes**.
> `FAB14` reads those facts back from the PDFs and `FAB15` checks the board-derived
> manual THT route. `MK11` additionally pins SW1/SW9/J5 board-side enclosure
> geometry. Fresh release verification is `evidence/d764-release-verification.json`.
> **No open owner decision and no unresolved PCB/fab-data blocker.** §8 separates
> order-time fabricator confirmations, first-article validation and enclosure-CAD
> closure from the frozen PCB release.

**Board:** `hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb`
**Authority:** `sha256 9e4728aebc8d449b32fe0d45f1fb81d4e00bf91baf1f61924048763168b7b7fd` (D-765; copper byte-identical to D-759's `1a06b058…`)
**Package:** `hardware/demo/fab/` — board-derived fabrication geometry remains D-759 authority; D-764 regenerates it deterministically and replaces the assembly PDFs/manifest with release-identified versions
**Date:** 2026-09-18 · **Decisions:** D-742 … D-765 · **Prepared for:** independent CTO review / first-five prototype order

> **THIS HANDOFF HAS BEEN REOPENED AND RE-ISSUED TWICE.**  It was first written
> at `c7f5c618`.  An external first-spin review (Fable 5.1 + Astra) found four
> real defects in that package — a `J5` BOM identity naming the superseded 2×12
> `BCS-112-S-D-HE`, a physically floating `U14` `QSTRT`, a charger-input audit
> computed at the wrong inner-copper thickness, and two boost converters with no
> local input capacitor.  **D-750 closed all four and dispositioned the other
> nine; D-751 finished the transaction at `bdf1376c`.**
>
> **AN INDEPENDENT RE-REVIEW THEN HELD D-751 ON ONE NAMED BLOCKER, AND CLOSING
> IT UNCOVERED FOUR MORE.**  `Q11`'s gate could not share `U17`'s `CTRL`
> (**D-752**); the feature contract's *"IR transmitter"* row named the backlight
> boost (**D-752**); two accessory states a user could reach already tripped the
> pack protection (**D-753**); the `PCAL9535A`'s output ports reset to `FFh`, not
> `00h` (**D-754**); and a stray *"5 A"* in a parsed `.kicad_dru` comment became
> a published rail current (**D-753**).  Two further items — the panel drawing
> and ST `AN5276` — proved retrievable after all and are now closed on primary
> sources (**D-754**, **D-755**).  Read
> `audits/2026-09-18-d750-first-spin-review-dispositions.md` and the D-752…D-756
> entries in `CTO_DECISIONS.md` beside this file.

---

## 1. Final board status

77.000 × 148.000 mm stepped outline, 6 copper layers, 3552 tracks, 918 vias,
71 zones, 315 footprints, 298 fitted references and 16 schematic-DNP.
*(D-752 fitted `D14`, `R132` and `C85`, the backlight-disconnect gate hold; the
track and footprint counts move with them.)*

| measure | value |
|---|---|
| retained multi-pad nets | **174** |
| connected retained nets | **173** |
| retained open edges | 1 |
| **unapproved open edges** | **0** |
| approved Demo NC | `J5.9`–`J5.12`, `J5.15`–`J5.18` — expected == observed |
| approved unrouted | `U11.3` only, under the 2026-09-17 owner decision |
| open owner decisions | **none** |
| board authority `sha256` | **`9e4728ae…`** (D-765; copper byte-identical to D-759's `1a06b058…`) |
| standing contracts | **19 run, 19 pass** |
| mechanical keep-out contract | **MK1–MK11 pass, 14 live controls** |
| open CAD items | **2** — rear component profile, §5b |

The single unrouted contact is `/BQ25185_STAT2` at `U11.3`. The owner approved
shipping it bare on 2026-09-17; `routing_ledger.py` re-proves that declaration
against the board on every run — the pad must exist, its part be fitted, it must
still carry `/BQ25185_STAT2`, it must still be stranded, and `R128` and `TP7`
must still be fitted — and **fails if any of those stops being true**.

## 2. Major design changes in this cycle

**BOARD AUTHORITY `1a06b058` (D-759).**  The `D-757`…`D-761` cycle laid **no new
routed copper at all** — it moved one solder-mask state, one mounting hole, and a
great many claims that nothing had ever checked.

**THE `D-757` … `D-765` CYCLE, IN ONE PARAGRAPH EACH:**

* **`D-757`** — the **NFC first-article tuning terminals were printed over**.
  `D-755` measured a 0.325 mm pad-to-via bridge on both match arms and concluded
  *"no mask removal"*; it never asked whether the two `GND` via caps were
  EXPOSED, and this board's setup tents every via on both masks.  POFV
  copper-capping happens BEFORE solder mask and does not help a tented via.  Both
  terminals are now B.Mask exposed / F.Mask tented, the released bottom-mask
  Gerber opens a 0.600 mm window at each, and **`FAB13`** holds it with four live
  controls.  See §8b.
* **`D-758`** — **WRONG, AND REVERTED IN FULL BY `D-759`.**  It read
  `FBV2_P1_KEEPOUTS.md` §1 as the current register when that file's own header
  says every section-1 X gains **+1.000 mm**, and moved both boss keep-outs and
  `BOSS2` onto the superseded datum.  What survives from it is the
  `--rule-area-recentred` declaration in `verify_promotion` and the probe of the
  five DRC rules this board sets to `ignore` — which is the thread that found the
  real defect.
* **`D-759`** — **`BOSS1`'s HOLE was the one object on this board that never took
  the `FBV2-EXP-002` re-base.**  It sat 1.000 mm west of its own keep-out, so four
  pours stood **0.2505 mm from the edge of a 2.200 mm NPTH**; it now stands
  **1.1505 mm**.  One footprint moved; `verify_promotion` reads 16/16 with **zero
  objects added and zero removed**.  `mechanical_keepout_contract` is the
  eighteenth standing contract and the first that looks at the enclosure; it
  refuses both the board that came before it and `D-758`'s mistake.  See §5a.
* **`D-760`** — **three height rules that had never been compared with a part**,
  two of them not met; the off-board cell dimension wrong by 3 mm; `RIB_R2`
  retired because `D-719` re-floorplanned a converter into it; and a contract
  caught emitting a non-deterministic field.  See §5b.
* **`D-761`** — a board-to-cavity clearance stale by two revisions (**1.500 mm,
  not 2.500 mm — the rule met exactly**), a milestone coordinate snapshot that
  read like a live source, and the **≥ 15 mm IR TX↔RX rule met by 0.133 mm** with
  nothing watching it.  `MK9` watches it now.
* **`D-762`** — the last `2_OPEN` land-pattern identity (`J8`, the Qwiic /
  STEMMA QT side-entry JST SH) was closed against JST's own drawing, the two
  Ebyte radio-module lands were re-proved independently from their vendor manuals,
  and `LAND7` now refuses any open land identity, missing cited drawing, changed
  drawing hash or tier-1 row with no recorded dimensions.  The PCB did not move.
* **`D-763`** — the assembly/enclosure interface was checked across faces rather
  than only by component body.  `J4` is mounted on `B.Cu`, but its 3.4 mm THT
  leads emerge under the display on `F.Cu`; after the 1.5744 mm board they stand
  **1.8256 mm proud**, 1.0256 mm above the display-shadow allowance.  The first
  five therefore carry a NORMATIVE `J4-T1`/`J4-T2`/`J4-T3` operation: solder,
  trim both leads/fillets to a verified conductive profile **≤0.50 mm above
  F.Cu**, inspect *after* cutting and rework any fillet the cutter damaged, then
  cover both joints with a **≤0.10 mm polyimide patch**, then fit the panel.
  (**The ≤0.80 mm figure this bullet used to carry was the DISPLAY_SHADOW
  ALLOWANCE, not the trim requirement** — D-770 retightened the trim to 0.50 mm
  precisely because meeting a 0.80 mm limit with 0.80 mm of conductor is zero
  margin, and D-779 corrects the instruction that had kept quoting it.)  `MK10`
  checks every opposite-face THT lead in every height-limited region and has four
  dedicated destructive controls.  The board, Gerbers, drills, BOM/CPL and
  firmware remain byte-for-byte on the D-759 authority.
* **`D-764`** — release instructions were made as strict as the PCB. The normative
  first-five plan no longer sends `U6`/`J4`/`J6` through a machine-placement class
  or carries the retired BCS J5. `FAB15` derives the five leaded THT refs from the
  board and refuses stale/manual-routing regressions. Assembly drawings now print
  release, authoritative board SHA, explicit top/bottom mirror convention, pin-1
  and manual-operation notes; `FAB14` reads the PDFs back and its critical-reference
  check was strengthened during CTO review so worksheet text cannot satisfy it by
  itself. `MK11` pins SW1, SW9 and current J5 board-side enclosure geometry.
  Fabrication artwork geometry is unchanged; regenerated Gerber/drill normalized
  hashes are identical.
* **`D-765`** — **the accessory limiter silicon was corrected, and the gate learned
  the word for the act.** D-753's envelope is retained to the digit, but the
  `TPS22950C` it ran on is specified `ILIM` **0.5–3.5 A** (`SLVSFJ2B` §5) and the
  board programs **0.407 A** — below its own recommended operating condition, on
  the one element between a user's accessory and the pack. The 0.05 A floor D-753
  reasoned from belongs to the base `TPS22950`, **WCSP-only**. `U20`/`U22` are now
  the **`TPS22950-Q1`** / **`TPS22950CQDDCRQ1`** / LCSC **`C17349276`** — same
  `DDC0006A` land pattern, same pinout, same `ILIM` equation and EC rows, same
  auto-retry, same always-on true RCB, same `FLT` semantics, same 170 °C TSD,
  `ILIM` specified **0.05–3.5 A**, AEC-Q100 grade 1, ≈ US$0.03/device. **No
  resistor, no copper, no envelope number changed**; the `.kicad_dru` **parsed**
  class table is proven byte-identical. `F6` gained three clauses — including
  "the setting must be inside the fitted part's own published range" over the
  resistor's whole tolerance band — and now runs **eight** controls, one of which
  is the board D-753 shipped. Both TPS22950 datasheets are now ARCHIVED in
  `vendor/TI/`; neither had ever been committed. `routing_ledger` also gained a
  population/board reconciliation guard after `kicad-cli sch export bom` was found
  to **exit 0 while silently dropping an entire sheet**, which had made the ledger
  report 114 nets instead of 174. Assembly PDFs print `RELEASE D-765`.

**THREE PARTS WERE FITTED AND THE COPPER MOVED** (D-750 and D-751); the
D-742…D-745 entries below are retained as the history of the previous cycle.

0. **THE FOUR FIRST-SPIN-REVIEW DEFECTS** (D-750, full disposition in
   `audits/2026-09-18-d750-first-spin-review-dispositions.md`):
   **`J5`** now names Samtec `SSQ-124-02-G-S-RA` / LCSC `C3323671` in every
   derived field, not the 2×12 part D-237 superseded eight months ago;
   **`U14.6` `QSTRT`** is wired to `GND` — it was floating behind a deliberate
   `no_connect`, and on a 3 µA part that is both a quiescent-current and a
   state-of-charge defect; **`audit_rail_ampacity.py`** computes at the board's
   own declared **0.0152 mm** inner foil and the charger input was re-laid
   **250.8 → 189.8 mm, 440 → 216 mΩ**, which is what buys the 360 min
   `tMAXCHG` its margin; and **`C83`/`C84`**, two 10 µF parts on the existing
   `C33`/`C64` BOM line, give `U21` and `U13` the local input capacitance they
   never had (nearest was 36.6 mm, *named* input part 93.5 mm).
0a. **`Q11` — THE BACKLIGHT CAN BE TURNED OFF NOW.** TI guarantees the
   `TPS61169` OFF only when the LED array's minimum Vf exceeds the maximum
   VIN; this panel is **2.9–3.2 V on a 3.3 V rail**, so the shutdown DC path
   converged at **≈ 25 mA** — a fifth of full brightness and 82 mW, with no
   firmware mitigation because `+3V3` is switched by the `SW9` slide switch.
   One **`AO3422`** (LCSC `C37130`, **55 V** `BVDSS`; D-766 re-rated it from the
   30 V `AO3400A`, which `Q1` still carries) in the panel cathode return.  Outside the regulation loop by construction, so the 109 mA setpoint
   is unchanged.  **D-751 routed its three nets** — D-750 had fitted it and left
   them open — and **D-752 took its gate off `DISP_BL_CTL`**, where a PWM low
   phase would have opened the string under an actively switching converter
   (§8 risk 10).  The gate now sits on its own `BL_DISC_G`, held up through
   every low phase by `D14` + `C85` and pulled down by `R132` (τ = 22 ms).

1. **The charger could not complete a charge, and now can.** `R37` 1 kΩ → **390 Ω**
   (`ICHG` 300 mA → **769 mA**) and `R36` 18 kΩ → **13 kΩ** (input limit ILIM500 →
   **ILIM1100**, `VBATREG` unchanged at **4.2 V**, `VLOWV` unchanged at 3.0 V).
   SLUSF65B rev B (Aug 2026) halved the fast-charge safety timer `tMAXCHG` from
   720 to 360 min; at 300 mA the charger delivered 1800 mAh against a
   2500–3000 mAh cell, stopped at 60–72 % SoC and latched a **non-recoverable
   fault** that `/CE` — hard-tied to GND — cannot clear. New margin **286 min at
   3000 mAh, 238 at 2500**, against 360.
2. **The charger status decode was inverted on `STAT1`** in both schematic sheets
   and four documents — `STAT1` LOW is a **fault**, not "charging". Corrected
   everywhere; D-170's decode paragraph is superseded.
3. **Documentation, gates and measurement** — everything else in D-742…D-745.

## 3. Connectivity

`routing_ledger.py`: 173 of 174 retained multi-pad nets connected, `unapproved_open_edges`
**0**. KiCad reports 17 unconnected items and **every one is accounted for**: 16
are pads of the sixteen schematic-DNP references (`U13` and its NFC-5 V boost
network, the DNP 0 Ω bypasses, the DNP speaker-filter caps) and the seventeenth
is `U11.3`.

`checks/demo_feature_contract.py` asserts the product absolutely, from
`AQROOT_DEMO_SCOPE.md`'s own lists: **40 features, 71 references, 106 nets** —
every part on the board *and fitted*, every net whole or covered by a named owner
decision, the approved-NC set exactly the eight `J5` positions, and every exposed
`J5` signal contact reaching an ESD array. **All four clauses PASS**, with nine
controls proving none of them is vacuous.

## 4. DRC

| run | result |
|---|---|
| `--severity-all --schematic-parity` | 199 `lib_footprint_issues` — **every one severity WARNING** — 17 unconnected, 246 parity warnings, **0 parity errors**, and **zero** of every other violation class |
| all five IGNORED rules promoted to error | 2 `missing_courtyard` (`BOSS1`/`BOSS2` mounting bosses), 5 `track_not_centered_on_via`, **zero new**. **D-758 ASKED WHAT THOSE TWO MEANT** and the answer was two real mechanical defects — see §5a. The five off-centre joins are measured: every one lands its track end inside the via pad and over the barrel, so each is annular-ring copper and not a tangency; none appears in `connection_width`'s below-strict set. `evidence/d758-switched-off-drc-tests.json` |
| `connection_width`, probed at 0.20 mm | 85 distinct pairs, 76 benign acute throats, 9 below 0.15 mm, **none load-bearing** |
| pour islands | 95 filled islands over six layers, **zero orphans** |

`min_connection` is 0.000 mm in board setup, so KiCad never runs
`connection_width` — the same defect class D-738 found in
`solder_mask_min_width`. It is probed in a scratch copy and the board setup is
deliberately left alone; the measurement is the deliverable.

## 5a. Mechanical retention — the two M2 bosses and the rear ribs (D-759)

**Read every mechanical coordinate on the RE-BASED datum.** `FBV2_P1_KEEPOUTS.md`
section 1 is written on the pre-`FBV2-EXP-002` 70.000 mm board; the file's own
header says the board grew symmetrically to 72.000 mm and that **every section-1
X coordinate gains +1.000 mm**. The board proves it: `U6` fits only the re-based
`IR_RX_OPTICAL`, `J3` only the re-based `USB_APERTURE`, `MK1` only the re-based
`MIC_ACOUSTIC`. `mechanical_keepout_contract` clause **MK1** re-proves this
against the board before any other clause asks its question.

| | registered (re-based) | as built |
|---|---|---|
| `BOSS1` hole | doc **(41.000, 12.000)** | 41.000, 12.000 — **moved +1.000 mm at D-759** |
| `BOSS1_KEEPOUT` | X 38.75 … 43.25, Y 9.75 … 14.25 | as registered, unchanged |
| `BOSS2` hole | doc **(60.000, 145.000)** | 60.000, 145.000 — unchanged |
| `BOSS2_KEEPOUT` | X 57.75 … 62.25, Y 142.75 … 147.25 | as registered, unchanged |

**`BOSS1`'s hole was the one object on this board that never took the re-base.**
It sat at doc `x = 40.000` while its own keep-out sat at the re-based
38.75 … 43.25, centred on 41.000 — so the west of the Ø4.500 mm region the
footprint requires was unprotected:

| | before D-759 | now |
|---|---|---|
| nearest pour fill to the `BOSS1` hole centre | **1.3505 mm** | **2.2500 mm** |
| pour to the edge of the 2.200 mm NPTH | **0.2505 mm** | **1.1505 mm** |
| routed copper inside Ø4.500 | 3 objects (`/SX1262_RXEN`) | **none** |
| nearest routed copper | — | 2.3000 mm (`F.Cu` `/SD_CS_N`) |

Against this board's own published **0.200 mm** NPTH-to-copper figure that is
5.75× the margin instead of 1.25×. `BOSS2` measures the same 2.2500 mm / 1.1505 mm
and has no routed copper within 3.200 mm. Its Ø4.500 mm keep-out lies **wholly
inside** the re-based opaque `IR_BARRIER` (X 57.500 … 62.500) that D-226 widened
3.0 → 5.0 mm specifically to carry it, and **0.000 mm** into either optical
window.

**`RIB_R2` IS RETIRED.** The rear support rib registered at X 66.20 … 69.70
(67.20 … 70.70 re-based), doc Y 45 … 64 and described as *"component-free,
verified"* is where D-719 re-floorplanned the `TPS63020`: `C28`, `C31`, `R39`,
`R40` and `U12` are inside it. **Do not mould a rib there** — it would land on a
3 × 3 mm QFN. Its replacement is measured and component-free:

| rib | region (re-based doc datum) | length | note |
|---|---|---|---|
| `RIB_R2A` | **X 65.50 … 69.00, Y 36.00 … 48.00** | 12.00 mm | top edge **1.00 mm** from the A/B control row at Y 49.000 |
| optional second bearing | X 70.00 … 73.50, Y 58.00 … 71.50 | 13.50 mm | brackets the A/B row from above, in the D-709 east step |

Both are clear of every back-side part with 0.25 mm of margin, east of the
re-based `BATTERY_SHADOW` (X 7.00 … 64.00) so no support compresses the LiPo, and
far outside the Ø58 metal exclusion. `RIB_R1`, `RIB_R3` and `RIB_B1` are
re-measured and still component-free.

**FIRST ARTICLE:** confirm both Ø2.2 mm NPTH positions against the enclosure CAD
before tooling the bosses. Evidence: `evidence/d759-mechanical-datum.json`,
`evidence/d759-boss-clearance.json`,
`evidence/d759-mechanical_keepout-contract.json`.

## 5b. Rear component profile and the battery (D-760) — **OPEN CAD ITEM**

`FBV2_P1_KEEPOUTS.md` §3 carries three height rules and **until D-760 not one of
them had ever been compared with a part**. Two of the three call themselves
*"measured Beta-DM limit, retained"* — a heuristic carried forward, not a stack
calculation. `mechanical_keepout_contract` **MK8** now measures every fitted part
in each region against its package's published maximum.

| region | face | retained limit | **measured profile** | gap | what sets it |
|---|---|---|---|---|---|
| `DISPLAY_SHADOW` | F.Cu | ≤ 0.8 mm | **0.60 mm** | **MET**, 0.20 mm spare | `D2`/`D4`/`D5` SOT-563 |
| `BATTERY_SHADOW` | B.Cu | ≤ 1.2 mm | **1.80 mm** | **+0.60 mm** | `C26`, `C29`, `C30` 1206 bulk MLCC |
| `NFC_CLEAR_D48` | B.Cu | ≤ 1.0 mm | **1.40 mm** | **+0.40 mm** | `J7` JST ACH connector |

**Every figure is sourced.** The `C_1206` 1.80 mm is Murata's own `GRM31C`
T = 1.6 ± 0.2 mm; `J7`'s 1.40 mm is JST's `eACH` *"low profile type, height
1.4 mm and width 4.3 mm"*; `U20`'s SOT-23-6 is **1.10 mm** from TI's own
`DDC0006A` outline — **not** the 1.45 mm the SOT-23 family would have given,
which is why the table reads the PART and not the family.

**WHAT IS BEING ASKED OF CAD.** These are not defects in the copper and moving
ten parts to satisfy a retained heuristic would be the wrong trade. What the
enclosure needs is the **real** rear profile, and it is now stated: **1.80 mm
inside `BATTERY_SHADOW` and 1.40 mm inside `NFC_CLEAR_D48`**. Close the stack
against those numbers, not against 1.20 / 1.00. The cell envelope has room to
help: it is **57 × 75 × 8.0 mm MAX** and both named candidates are **7.3 and
7.5 mm** thick, so 0.5–0.7 mm of the reserved envelope is already unused.

**WHAT IS REQUIRED NOW, NOT DEFERRED.** The `BATTERY_SHADOW` parts are hard
points against a soft pouch. `OFF_BOARD_BOM.md` now carries a **0.5 mm compliant
insulating sheet**, cut to the 57 × 75 mm footprint, adhesive to the PCB, as a
REQUIRED off-board item. It spreads the load and insulates the pack from rear
copper. **It does not close the 0.60 mm gap and is not offered as if it did.**

`J7` — the NFC antenna's own connector — is recorded in the register's §4 with
its measured intrusion: **0.870 mm inside the Ø48 CLEAR region and 0.130 mm
OUTSIDE the Ø46 coil**, so the coil does not sit on it.

**And the off-board cell dimension was wrong.** `OFF_BOARD_BOM.md` told a buyer
**60 × 75 × 8.0 mm**; D-239/D-243 narrowed the envelope to **57 mm** — the price
of the `J5` right-angle side header — and the board's `BATTERY_SHADOW` is 57 mm
wide. Corrected. Both named candidate cells are 50 mm wide, so nothing that was
going to be ordered is affected; the document was.

Evidence: `evidence/d760-mechanical_keepout-contract.json`.

## 5. Safety and power

* **D-269 / D-186 proven.** `protected_copper` is byte-identical across every
  decision in this cycle. D-186's split — two independent series disconnects with
  their own external pull-downs — is now machine-checked by name (`R102`, `R131`,
  `TP47`); on Demo the `ACC_5V_SW_EN` bit sits on `U3` P03 rather than D-186's
  `U23` P04 because `U23` is removed by scope, and the split and pull-downs, not
  the bit, are what D-186 requires. D-187's isolation FET and the four
  expander safe-state pulls are required by name too.
* **`VBATREG` is unchanged at 4.2 V.** The charger ECO moved only the input
  current limit and the charge current; nothing in the protection architecture
  moved.
* **Absolute power audit, CORRECTED AT D-750 AND RE-JUSTIFIED AT D-751.**
  `audit_rail_ampacity.py` walks each rail's *carrying path* — not its net —
  self-checks by re-deriving `.kicad_dru` section 5's published table, and
  reports temperature rise rather than pass/fail. It now also **reads the
  board's own `(stackup)` back and fails itself if its constants disagree**:
  the inner foil is **0.0152 mm**, not the nominal half-ounce 0.0174 mm the
  tool used to assume, so every inner figure it published before D-750 was
  14.5 % optimistic. **Six rails, all pass**; four carry **named,
  length-bounded exceptions** with controls that fail when they are removed,
  mis-scoped or overrun, and two of those four — the SYS trunk to the southern
  boosts — are rails **nothing had ever measured**, against a section 5 note
  that had asked for them since D-185.
  Each exception's residual is now DERIVED from the board's real dielectrics
  (`In2.Cu` is 0.4000 mm of core from `In1` and 0.2028 mm of prepreg from
  `In3`) rather than from a remembered stackup: **1.45 K** on the charger
  input against the isolated-coupon curve's 66.5 K.

## 6. USB / RF / NFC

* **USB** — differential pair on `F.Cu` over `In1` with no vias, per `.kicad_dru`
  section 6; DRC clean. `USB_VBUS_RAW` carries 1.1 A with a 5.4 K rise.
* **RF** — `rf_symmetry` and `keepout_stackup` contracts byte-identical; the
  ESP32-S3 antenna keep-out and the manufacturer-precedence rule are intact.
* **NFC** — measured, not asserted. Decoupling is **4.64–7.39 mm from the pin on
  every `U9` driver rail** (`VDD_RF` 2.92 nH, 0.249 Ω at 13.56 MHz ≈ **62 mV of
  ripple at the 250 mA peak**). Further than ST's reference layout, and not
  improvable without moving `U9`'s block on a board where every corridor probe
  returns 0.0 mm. All eighteen `TUNE` parts and both antenna test points
  (`TP37`, `TP38`) are present, so first-article tuning is possible.

## 7. Manufacturing package

`FAB1` provenance · `FAB2` fill · `FAB3` layers · `FAB4` drill · `FAB5` CPL ·
`FAB6` BOM · `FAB7` sourcing · `FAB8` outline · `FAB9` via-in-pad ·
`FAB10` via geometry · `FAB11` mask dams · **`FAB12` identity** — **all PASS**
at this authority, with **seven live negative controls refused inside the
gate**.

**`FAB12` IS NEW AT D-750 AND IS THE ANSWER TO HOW `J5` SURVIVED.** Every
other check in the package asks whether the package is internally CONSISTENT,
and a consistently regenerated *wrong identity* is invisible to a consistency
check. `FAB12a` reads each BOM row's OWN WORDS — a stated `A × B` geometry, a
contact count, a pitch — against the footprint's OWN PADS; run against the
stale released package it reports exactly the real defect and nothing else
(*`J5` row says `2x12`, footprint is `1 × 24`*). `FAB12b` pins **41 critical
identities** by name against both the BOM and the board. D-751 added the
controls that prove neither half is vacuous: they **put the `J5` defect back**
three ways, and `FAB5` mutates one row of the real `pos-fitted` file four ways
(180° rotation, +10 mm, flipped side, duplicated row).

`contract_regression` runs **17 contracts: all ran, all PASS**, and at D-756
**fifteen of them come back byte-identical to the `d753` artifacts** — the two
that moved, moved by exactly what changed. `protected_copper` is **IDENTICAL**
throughout: the fifteen protected nets and their 406 objects did not move
through any of this, across D-750, D-751, D-752, D-753 and D-756.

The assembly BOM carries **123 lines and 252 fitted references, 252 of them
orderable** (coverage 1.0). D-752 added ONE purchasing identity — `D14`, LCSC
`C2128`, a JLCPCB **BASIC** `1N4148WS` on the `SOD-323` land pattern the board
already carries for `D8`/`D10`/`D11`/`D12` — while `C85` and `R132` joined
existing lines. D-753 then RETIRED one: `R97` and `R101` both became 2.7 kΩ on a
single new BASIC line (LCSC `C13167`), which also retired `R101`'s superseded
`ERJ-PA3F1651V`, an EXTENDED part with 2 763 in stock.  **D-771 SPLIT THAT LINE
AGAIN AND MOVED A THIRD**: `R97` → `0603WAF1781T5E` (LCSC `C22849`, 1.78 kΩ),
`R101` → `0603WAF2371T5E` (`C25964`, 2.37 kΩ at D-773; `0603WAF2321T5E` /
`C22905` / 2.32 kΩ at D-771) and `R75` →
`CRA2512-FZ-R010ELF` (`C840621`, 10 mΩ).  All three are the SAME series, the
SAME manufacturer and the SAME land pattern as the parts they replace, so no
footprint, no copper and no assembly step changes — the two 0603 resistors are
`expand` rather than `BASIC`, because 1.78 kΩ and 2.37 kΩ are E96 values and
JLCPCB lists no BASIC part at either.

**THE VIA-IN-PAD COUNT MOVED 135 → 136 AND THE ONE THAT MOVED IT IS NAMED.**
`Q11.3`'s tap put a 0.600/0.300 barrel at `(10.950, 112.800)`, half inside the
drain land — it could not go north, where `SW3.1`'s F.Cu pad blocks a through
hole. It is an ordinary member of the declared population and is measured as
one: **same net**, 0.300 mm drill (one of the four already in use), and
**4.08 % of the land open** against a mean of 6.89 % and a maximum of 38.16 %.
It is filled, capped and plated by the same process the other 129 barrels
already require, and it is in the `MANIFEST` and the fab notes like every other.
The mask-dam population is **unchanged at 21**.

The package declares, in generated notes with `MANIFEST` rows: **via-in-pad in
136 solderable lands** (resin-filled, capped, plated), **38 vias below the
board's own annular floor** on named net- and area-scoped licences, and **21
solder-mask dams below 0.125 mm**, of which four `U9` corners are 0.0621 mm
between different nets.

## 7a. Demo firmware — the as-built hardware layer (D-747, D-748)

**The board is programmed with `pio run -e aqroot-demo`, and nothing else.**
`Firmware/src/config.h` is the legacy Beta application's map; its placeholder
pins do not merely go stale, they **collide** with real Demo functions (I2C on
GPIO17/18 where this board has SPI-A MOSI and the NFC IRQ; the display on
GPIO10/11/12/13 where it has `DISP_CS_N`, SPI-A MOSI, SPI-A SCK and SPI-A MISO).
That file now raises a compile `#error` for any real-hardware build that has not
explicitly acknowledged it.

**The pin map is GENERATED, not written.** `Firmware/src/hw/aqroot_demo_board.h`
is emitted pad by pad out of `aqroot-Beta-v2.kicad_pcb` and the cached
`ESP32-S3-WROOM-1` symbol — 84 symbols, with the I2C addresses derived from the
`A0`/`A1`/`A2` strap pads rather than typed — and the seventeenth standing
contract fails if the committed header is not byte-identical to what the board
says today. The reason is in the record: D-732 found the hand-maintained
expander table inverted on `P05`/`P06`, and reading it would have masked `4Ah`
bit 6 believing it was `BQ25185_STAT2` when it is `TOUCH_INT_N`.

| claim | result |
|---|---|
| `firmware_hw_map` contract, H1–H6 | **all PASS**, 11 policy controls all REFUSED |
| expander safe-ordering host test | **59 claims PASS**, **6** controls all caught |
| SPI-B arbiter host test | **22 claims PASS**, 3 controls all caught |
| `pio run` over all four environments | **4 SUCCESS** |

**D-750 AND D-751 CHANGED THE FIRMWARE'S FAULT BEHAVIOUR, AND THE SECOND ONE
FOUND A BUG THE FIRST HAD LEFT HALF-FIXED.** An external review observed that
shutdown must attempt every reachable independent control even after one I2C
error. It was right in three places: `begin()` and `service()` each
short-circuited on `||`, so a NACK from `U2` meant `U3` — which owns
`NFC_5V_EN`, both radio resets and both transmit enables, and whose input port
carries `ACC_POWER_FAULT_N` — was never configured or never serviced; and each
accessory shutdown gave up after its first failed write. All repaired at
D-750. ***D-751 then wrote the test, and the test found the rest***:
`writeOutputs` only moves the driver's shadow when the bus ACKs, so a NACKed
load-switch write left `ACC_5V_SW_EN` HIGH in the shadow and the following
unconditional boost-disable **re-sent that stale bit** — one NACK would have
left the accessory load switch commanded ON during exactly the fault the
shutdown was called for. `Pcal9535a::clearBits` takes both bits down in one
transaction, so a shutdown needs **one** surviving write rather than all of
them. The bus in the host test can now refuse a chosen transaction and still
log it, and all four failure modes are **mechanised controls** the contract
puts back on every run.

**What the first board's operator gets.** At boot: every pin parked, both
expanders brought up latch-before-direction and their direction registers read
back, the three resets released through `U2`, the BMI270 identified at
`CHIP_ID 0x24`, I2C raised to 400 kHz only after every device answers, and all
three SPI-B devices identified — the CC1101 through a BURST-flagged header
(address `0x30` *without* the burst bit is the `SRES` strobe and would reset the
radio instead of identifying it), the SX1262 by its `0x1424` sync word, the
ST25R3916 in SPI **mode 1**. On the console: `d` runs a raw microSD `CMD0`/`CMD8`
— **the only test on this board that proves SPI-A MISO**, since `R112` is DNP and
the card is the sole reader on that net — plus backlight, IR loopback, tone,
microphone, display test pattern, and the accessory power tree operated in its
required order. **Nothing energises at boot.**

**Three as-built facts the assembly and test team must know.**
`ChargerState` has three values and **none of them is "charging"**: `STAT1` LOW
is a directly observed fault, `STAT1` HIGH is ambiguous, and the console prints
that ambiguity in words. The panel is **write-only** (`R112` DNP) so the display
can only be confirmed by eye. `MK1` and `U5` share one `/I2S_BCLK` and one
`/I2S_LRCLK`, so exactly one I2S controller may master them.

## 8. Significant remaining prototype risks

1. **Charge-current ECO is unverified in hardware.** Derived from SLUSF65B and
   TI's own worked examples, but never measured. `TREG` at 100 °C bounds the
   thermal risk — the part reduces its own charge current rather than
   overheating — and `TSHUT` at 150 °C is not approached. **First article must
   measure charge current, total charge time and `U11` case temperature, in the
   enclosure, with the frozen first-five pack: **Adafruit Product 328, protected
   2500 mAh JST-PH**.  The 3000 mAh alternative is no longer the first-five
   build because it is the least-margin timer/thermal corner.
2. **Charger input trunk is 189.8 mm / 216 mΩ** against a 65 mm straight line,
   **improved at D-750 from 250.8 mm / 440 mΩ** by a parallel anchor-to-anchor
   conductor and one widened In2 segment. 237 mV of drop and 0.26 W at 1.1 A.
   The earlier figures were also computed at the wrong inner-copper thickness;
   at the real 0.0152 mm the pre-D-750 board was **487 mΩ and 536 mV**, and at
   that resistance the charger **exceeded the 360 min `tMAXCHG`** on an
   ordinary 4.65–4.75 V source at a 150–300 mA system load. At 235 mΩ every
   case in the source envelope terminates with at least **65 min to spare**.
   Still accepted as `.kicad_dru` section 5a — a residual, not a defect, and
   its 1.45 K plane-coupled rise is derived from the board's own dielectrics.
   **Measure `VIN` at `U11.10` while charging.**
3. **Charging from a 500 mA-class source will not complete a cycle** inside
   `tMAXCHG`. The USB-C port is a plain 5.1 kΩ Rd sink and does not read the
   source's Rp advertisement; VINDPM folds the input back as `VIN` sags.
   **Published in `DEVICE_SPEC`: charge from a 1 A or better source.**
4. **NFC read range** — see §6. Tune `L5`/`L6`/`C69`–`C72` at first article.
5. **`J5` recess is an enclosure requirement with a hard number.** The mating
   face is at `x = 72.430`, the board edge over `J5`'s span at `x = 72.000`, and
   there is **6.070 mm of air** between the mating face and the east cavity
   face. Against a Samtec `SSQ` insertion depth of 3.68–6.35 mm, **the east wall
   must step inward to follow the board's own step** over `y ≈ 8.475 … 69.945`.
   A straight east wall leaves the Community Port unusable.
6. **`M-09` fits at its bound, not with measured clearance.**
   `2.0 + 8.50 + 1.6 + 8.0 + 0.6 + 2.0 = 22.70 of 23.0 mm`. 8.51 mm is the
   connector insulator's largest dimension, so the column is an upper bound —
   but only **0.30 mm** of spare. CAD-to-verify against the Samtec 3D model.
7. **Charger fault granularity.** With `STAT2` unlanded, `STAT1` LOW is a
   directly observed fault but recoverable versus non-recoverable is not
   distinguishable, and charging versus charge-complete is an **inference**.
8. **Fabricator acceptance still to be obtained at order time** — the `J3` NPTH
   concession, the `MK1` acoustic mask opening, the POFV process for 136 lands,
   the 38 sub-floor via rings and the 21 sub-0.125 mm mask dams are all declared
   in the fab notes and must be confirmed in writing before the order is placed.
8b. **The battery connection is inside its rating by 6.0 %, not by margin to
   spare** (D-777).  `J4`'s published 2 A is the lowest number in the battery
   path and the board has **no accessory current measurement**, so an accessory
   drawing MORE than its published budget is not refusable: it must exceed the
   published 5 V budget by **+19.4 %** before the connection leaves its rating
   and by **+89.6 %** before the charger acts.  Between those nothing on this
   board objects.  Closing it needs accessory current sensing or the **JST
   `B2B-XH-A` 3 A** connector — both REV-B, costed in CTO_DECISIONS D-777 §6.
   **A first-article temperature-rise measurement on `J4` at the worst
   permitted sustained load is required at bring-up.**
8c. **Sub-GHz TX, the NFC field and the IR transmitter are unavailable while
   BOTH switched accessory rails are enabled** (D-777).  A concurrency
   condition, not a capability removal: each rail alone leaves all three
   available, and both published budgets are unchanged.  In DEVICE_SPEC §6.3a's
   mandatory accessory-facing wording.
8d. **`Q11`'s conduction at the held gate rests on an extrapolation, and the
   design is insensitive to it** (D-779).  `VGS` at the hold is 2.396 V, 104 mV
   below the AO3422's nearest guaranteed `RDS(on)` point — where it is
   guaranteed to pass 1.5 A, 13.8× what this string asks.  `U17` regulates
   `LED_BOOST` until `R69` sees 204 mV, so even a pessimistic 10 Ω channel
   costs 1.09 V and 0.119 W and does not move the LED setpoint.
8a. **THE DISPLAY TAIL'S PIN-1 END IS NOW PROVED FROM THE VENDOR DRAWING**
   (first-spin review item 5 — **CLOSED**, superseding the "must be settled
   before the panel is mated" text this entry used to carry). Earlier sessions
   recorded the `ER-TFT035IPS-6` drawing as unobtainable; `buydisplay.com`
   returns **HTTP 403 to non-browser clients**, and the Wayback Machine's
   2025-01-09 snapshot serves the identical 24-page PDF
   (`sha256 f8822bd3…a371`). **Section 3.3, the capacitive-touch outline
   drawing, settles it in two mutually-confirming views**: the module FRONT view
   — the one labelled *3.5" 320×480 Pixels* — shows the tail leaving the BOTTOM
   edge with **`50` on the LEFT and `1` on the RIGHT**, and the REAR view on the
   same sheet, carrying the component-area callout and the `FPC+PI` 0.3 ± 0.03 mm
   stiffener dimension, labels **`1` on the LEFT and `50` on the RIGHT** — the
   consistent mirror. **Pin 1 is the RIGHT-hand end of the tail viewed from the
   display face, tail down.**
   `J1` is on `F.Cu`; KiCad's top view IS the front view and `+x` is to the
   right, so **`J1` pin 1 at `x = 44.910` is the RIGHT-hand end** and pin 50 at
   `x = 20.410` the left. The panel mounts on the front face and its tail bends
   about a **horizontal** axis down to board level into `J1` below the display
   band (§21, 6 mm bend corridor); a horizontal-axis bend **preserves
   left/right**, and no route around a board edge and up the rear is specified.
   **PIN 1 MEETS PIN 1 — no mirror, and `J1` is correctly oriented for this
   panel.** The same sheet's backlight schematic — one common `LED-A`, **six
   diodes in parallel** with cathodes grouped `LED-K1`/`LED-K2` onto tail pins 2
   and 3, `U = 2.9–3.2 V`, `I = 120 mA` — independently corroborates D-079, the
   D-750 true-off analysis and the D-752 open-LED argument.
   **The incoming diode-mode test is RETAINED**, not because the orientation is
   open but because it costs nothing and catches a mis-built tail or a
   substituted module: the panel's own pins 1/2/3 are `LEDA`/`LEDK`/`LEDK` and
   48/49/50 are `GND`, so a meter reads an LED forward drop of ~2.5–2.9 V
   between the outermost contact and its two neighbours at the pin-1 end and a
   dead short at the other. Evidence:
   `evidence/d754-display-tail-orientation.json`.

8b. **NFC MATCHING: THE PRIMARY SOURCE IS NOW ON THE RECORD, AND THE TUNE IS A
   MEASURED 0.325 mm FIT** (item 6 — **ADJUDICATED**, superseding the "could not
   be retrieved" text this entry used to carry). `st.com` refuses every direct
   fetch from this environment and Mouser serves a JavaScript challenge; the
   Wayback Machine's 2025-03-23 snapshot of **AN5276 Rev 6 (May 2023)** does not.
   **Figure 2 is the topology**, and the board matches it element for element
   with ONE exception:
   `L5`/`L6` = `L_EMC1/2`; `C69`+`C73` and `C70`+`C74` = `C_EMC1/2`;
   `C71`/`C72` = `Cs1/Cs2`; **`Cp1`/`Cp2` — ABSENT**; `R114`/`R115` = `R1`/`R2`.
   ***The 1.1 Ω series resistors are NOT a deviation***: the earlier note read
   AN5276's `RQ` — the PARALLEL Q-adjust resistor of §4 — as the topology
   element, and Figure 2 in fact puts `R1`/`R2` **in series** between the
   matching node and the antenna, which is exactly what `R114`/`R115` are.
   The receive divider is tapped after them, at the antenna, where AN5276 taps
   it at the matching node — so the divider's capacitance does **not** substitute
   for `Cp`.
   **NO BOARD CHANGE, AND THE REASON IS MEASURED.** The rows either side of the
   matching nodes are full — `y = 25.700` carries `C73`, `R116`, `C76` and
   `y = 34.300` their exact mirrors — and the inboard space carries the
   `NFC_RFI1/2` runs and their barrels; there is no symmetric site for a `Cp`
   pair, and `Cp`'s VALUE cannot be derived before the antenna is built and
   measured, so nothing could be baselined anyway.
   **THE FIT IS BETTER THAN D-751 RECORDED IT.** That entry described "an
   ordinary 0402 tacked across a measured 0.500 mm gap" to B.Cu `GND` **fill**,
   which would mean removing solder mask. The real geometry: on each arm the
   matching node's own SOLDER PAD faces a `GND` **via** at the same `x` —
   `C71.2` → via `(43.500, 26.700)` and `C72.2` → via `(43.500, 33.300)` — at an
   edge-to-edge gap of **0.325 mm on both arms, mirror-exact about
   `y = 30.000`**. An 0402 bridges that with ≈0.34 mm of overlap at each end;
   both vias are on the fill-and-cap-plate instruction already in the fab notes,
   so each presents a planar solderable land. **No cut track, no symmetry loss.**
   ***AND THE MASK STATE IS NOW PART OF THE DESIGN, WHICH IT WAS NOT WHEN THIS
   ITEM WAS FIRST WRITTEN*** (**D-757**). This board's setup tents every via on
   both masks, so on the package D-756 declared, both of those via caps were
   PRINTED OVER and the bridge above was geometrically right and physically
   impossible — copper-capping happens before solder mask and does not help a
   tented via. Both terminals are now explicitly **B.Mask exposed / F.Mask
   tented** in the board file, the released bottom-mask Gerber carries a
   0.600 mm opening at each, the fab notes carry a **DO NOT TENT** instruction
   naming both coordinates, and `fab_package_contract` clause **FAB13** holds
   all of it with four live negative controls — one of which puts the tented
   via back. The foreign-net solder-mask web at each terminal is **0.325 mm**,
   2.6× the 0.125 mm floor. Evidence:
   `evidence/d757-fab13-pre-declared-package-refused.json`,
   `evidence/d757-fab-package-contract.json`.
   Obtain the measured antenna equivalent circuit, run the
   ST25R matching tool, and record the final `Cs`/`Cp`/`R` values in
   `CTO_DECISIONS.md` before any second article. Evidence:
   `evidence/d755-nfc-matching-adjudication.json`.

9. **Demo firmware is a BRING-UP LAYER, not the application** (D-747, D-748).
   The as-built hardware definition, the PCAL9535A driver, the safe bring-up
   sequence, the SPI-B arbiter, the identity probes and the console exercises all
   exist and are machine-checked — see §7a. What does **not** exist is the
   application: no LVGL UI, no LoRa or sub-GHz protocol stack, no NFC stack, no
   file system, and **no BMI270 configuration file**, so the IMU proves its bus
   and address but returns no motion data yet. Three values in the map are
   REPORT-ONLY because this repository holds no datasheet for them: the MAX17048
   version register, the touch controller ID and the ST25R3916 identity byte.
   The ILI9488 gamma and power tables are deliberately absent and must come from
   EastRising's sequence for this exact module at first article. **None of these
   is a fabrication blocker**; all are application work that continues during
   fabrication.

10. **`Q11`'s GATE HOLD IS LOAD-BEARING AND MUST SURVIVE ANY REVISION**
   (D-752; this entry SUPERSEDES the D-751 text, which had the argument
   backwards). TI `SNVSA40B` §6.3.5 makes `CTRL` an **analog** dimming input —
   the part chops its internal 204 mV reference at the duty cycle and filters
   it, so *"only the WLED DC current is modulated"* and **the converter keeps
   switching through every PWM low phase**; shutdown needs `CTRL` low for more
   than `tSD`, 2.5 ms max. The state that must never occur is *converter
   switching with `Q11` off*: `FB` collapses under the 30 mV open-LED
   threshold, `SW` ramps to `VOVP_SW` (36 / 37.5 / 39 V), and the panel cathode
   — `Q11`'s drain — follows the anode to the **39 V** this board's own
   `.kicad_dru` publishes for `LED_BOOST`.
   `D14`/`C85`/`R132` make that unreachable by construction: the gate follows
   the ENVELOPE of `DISP_BL_CTL` with **τ = 22 ms**, so `Q11` cannot open
   before **5.14 ms** at worst-case tolerance while `U17` is in shutdown by
   2.5 ms — **2.06× margin, waveform-independent, no firmware sequencing**.
   **AND D-766 RE-RATED THE SILICON, WHICH IS WHY 2.06× IS ENOUGH.** D-752 wrote
   *"the `AO3400A` is a 30 V part"* and left the 30 V part fitted; a single
   component failure — an unfitted `C85`, an open `D14`, a shorted `R132` —
   re-creates the forbidden state, and a protection element has to survive the
   fault it exists to prevent. `Q11` is now the **`AO3422`**, `BVDSS` **55 V**
   min, **41 % margin** over the published 39 V, same SOT-23 and same
   1 = G / 2 = S / 3 = D. Its higher `VGS(th)` max (2.00 V against 1.45 V) is
   what moves the ordering margin 4.6× → 2.06×, and that is accepted
   deliberately: with a 55 V part, losing the ordering costs a **recoverable**
   `U17` open-LED latch instead of avalanche in an under-rated FET.
   `demo_feature_contract.py` **F5** refuses any board that collapses the two
   nets, drops `C85`, substitutes a Schottky for `D14`, or retunes `R132` — and,
   since D-766, any board whose disconnect FET has no published rating, is rated
   under the ceiling **parsed out of the `.kicad_dru`**, is not enhanced by the
   held gate, or would open before `U17`'s `tSD`.
   **A revision that wants to PWM `Q11` independently must re-rate it to at
   least 40 V `VDS` first.**

11. **THE ACCESSORY ENVELOPE IS BOUNDED BY SILICON, THE PUBLISHED BUDGET IS
   GUARANTEED, THE PROTECTION CHAIN IS ORDERED OVER TOLERANCE, AND ONE THERMAL
   RESIDUAL IS NAMED** (D-753; limiter silicon corrected by D-765 to the
   `TPS22950-Q1`, which is specified from 0.05 A; **budget and chain corrected by
   D-771**).

   **`R97` = 1.78 kΩ (D-771) and `R101` = 2.37 kΩ (D-773)**, both 2.7 kΩ until
   D-771 and 1.5 kΩ / 1.65 kΩ before that. D-098 locks the first five boards at
   **`ACC_3V3_SW` = 400 mA TOTAL** and **`ACC_5V_SW` = 300 mA TOTAL** — the two
   duplicate `J5` contacts on each rail SHARE that limit — and at 2.7 kΩ each
   limiter **GUARANTEED only 0.277 A**. The board published a budget its own
   silicon could refuse to deliver. It now guarantees **0.428 A** and **0.315 A**
   (7.0 % and 4.9 % over) and passes no more than **0.849 A** / **0.624 A** over
   −40…+125 °C, over the programming resistor's own 1 % band as well.

   **AND THE INTERNAL TERM THE ENVELOPE RUNS ON WAS A HAND-WRITTEN CONSTANT**
   (D-772).  It read 1.0 A; the repository's own last derivation (823 mA)
   contains **no NFC line at all**, because `U9` was DNP when it was written and
   **D-192 fitted it**, and it counts *"the worst single radio"*, which is not
   true of a board whose `U8` is an external module on its own `+3V3` pin.  The
   budget is now **itemised, cited and SUMMED** — nine lines, **1.063 A** — and
   `F6` reads the board's own `+3V3` net so no fitted consumer can go
   unbudgeted.

   At the 3.0 V cell corner with that 1.063 A internal load, no state a user can
   reach exceeds the `BQ25185` `IBAT_OCP` **minimum of 2.5625 A**.  The thinnest
   margin on this board is **1.6 %** and it is the 5 V accessory **in
   overcurrent** while every internal subsystem runs at once, on a charger at the
   −18 % corner of its band, with the cell at 3.0 V and the boost at the top of
   its own setpoint band; its consequence is an `IBAT_OCP` hiccup that
   **re-enables the BATFET after `tREC_SC`**, which D-771 guaranteed happens
   before the latching breaker on every unit.  **D-779 completes that sentence
   from SLUSF65B 6.3.7.3: 4 to 7 consecutive trips inside a 2 s window leave the
   BATFET OFF until a valid VIN is connected**, so a SUSTAINED battery
   overcurrent is a battery-only dead stop the user clears with USB rather than
   an indefinite retry.  At a conforming accessory load the margin is **7.3 %**.  A
   *simultaneous double limiter fault* reaches **3.558 A**, still 10.2 % below
   the breaker's guaranteed minimum.

   **AND THE 5 V SETPOINT ITSELF WAS A CONSTANT FROM A WRONG REFERENCE**
   (D-773).  This contract carried 4.95 V and `ARCHITECTURE.md` published
   4.99 V, *both* derived from `VREF` = 0.6 V; TI `SLVSF14B` gives the
   `TPS61023`'s FB reference as **580 / 595 / 610 mV** — and **`R99`'s own
   symbol note had carried the correct 0.595 V all along**.  Over `R99`/`R100`
   at their 1 % bands the real setpoint is **4.742 / 4.950 / 5.165 V**; the
   envelope now runs on the worst-case high, and `F6` refuses a divider whose
   worst case reaches the part's own `VOVP` minimum of 5.5 V (it clears by
   **6.1 %**).  That correction is what moved `R101` to **2.37 kΩ** — the E96
   value nearest the centre of its own legal window, **2.298–2.478 kΩ**.

   **AND THE CHAIN WAS ORDERED AGAINST A TYPICAL.** ADI guarantees the
   `LTC4368`'s forward threshold only as **40 / 50 / 60 mV**; at the old `R75`
   15 mΩ the LATCHING breaker's real band was **2.640–4.040 A**, overlapping the
   charger's RECOVERABLE 2.5625–3.6875 A. **`R75` is now 10 mΩ** — same Bourns
   `CRA2512-FZ` series, same 2512 land, same 3 W — and the breaker is
   **3.960–6.061 A**, entirely above it. `demo_feature_contract.py` **F6**
   recomputes all of it from `R97`, `R101`, `U20`, `U22`, **`R75` and `U18`**,
   with **twenty-one** live controls — including the internal budget with its
   NFC line missing, which is the budget as it actually stood from D-192 — and
   refuses a limiter its own converter cannot source.

   **THE RESIDUAL:** `BAT_MAIN` copper is sized for 1.5 A sustained, and the
   worst *sustained* case — both accessories at their guaranteed current with
   the full internal load — is **1.977 A at 3.7 V and 2.438 A at the 3.0 V
   corner**, on one unavoidable 5.525 mm × 0.200 mm segment (`U11`'s `DLH0010A`
   pin-2 `BAT` land). *D-098's PUBLISHED budget alone is 2.375 A at that corner
   and has been since 2026-08-23, so the requirement did not move; the hardware's
   ability to meet it did.* The plane-coupled ceiling is **51.5 K** over the
   adjacent `In4` plane at 2.438 A, from a model that ignores lateral spreading,
   conduction and convection, on copper that is necked for only 0.575 mm before
   it tapers to 1.2 mm. **Measure that segment at first article with both
   accessory rails loaded and the cell at 3.0 V.**

   **AND THE TWO ACCESSORY RAILS THEMSELVES ARE NOW MEASURED** (`.kicad_dru`
   §5f, new at D-771): `ACC_3V3_SW` 224 mΩ / 82.1 K IPC / 2.29 K plane-coupled on
   `In2.Cu`, `ACC_5V_SW` 111 mΩ / 40.8 K / 1.24 K on `In3.Cu`, both declared with
   length budgets. What a conforming accessory sees at the published budget is
   **3.18 V** on `ACC_3V3_SW`, and on `ACC_5V_SW` **4.69 V at the bottom of the
   boost's own setpoint band** (4.742 V − 49 mV of track + `RON` drop) against a
   4.95 V typical.

12. **`J4` BATTERY-CONNECTOR LEAD TRIM IS A RELEASE ASSEMBLY REQUIREMENT,
   NOT AN OPTIONAL REWORK** (D-763).  `J4` is the only through-hole part whose
   body is on `B.Cu`.  JST's `ePH.pdf` gives a 3.4 mm lead below the seating
   plane; the board is 1.5744 mm thick, leaving **1.8256 mm** above `F.Cu` under
   the display where the `DISPLAY_SHADOW` allowance is **0.80 mm**.  On every
   first-five unit: solder `J4` from the FRONT, trim both leads/fillets to a
   verified conductive profile **≤0.50 mm above the F.Cu surface** (`J4-T1`),
   inspect the profile AFTER cutting and rework any fillet the cutter cracked,
   lifted or removed (`J4-T2`), then cover both inspected joints with a
   high-temperature polyimide patch **≤0.10 mm thick** (`J4-T3`) before the
   display goes on.  Conductor plus insulation must remain under the 0.80 mm
   allowance.  **The 0.80 mm figure is the ALLOWANCE, never the trim target**:
   D-770 retightened the requirement to 0.50 mm because meeting an 0.80 mm limit
   with 0.80 mm of conductor is zero margin, and D-779 corrects the two places
   in this handoff that had gone on quoting the allowance as the instruction.
   The governing instruction is `assembly/THT_LEAD_TRIM.md`; `MK10` refuses an
   undeclared or insufficient trim.  This is an assembly closure, not a PCB ECO.

## 9. Recommended post-Kickstarter improvements

1. **Charger input as a star, not a daisy chain** — a direct `R35` → `U11.10`
   trunk on outer copper retires the section-5a exception and ~0.4 W of loss.
2. **A charger whose `STAT2` is not adjacent to `BAT`**, or a package with a land
   taller than 0.200 mm. Rotating or moving `U11` cannot help: `BAT` is pin 2 and
   `STAT2` pin 3 in every DLH0010A.
3. **Bring `/CE` under firmware control** so a safety-timer fault can be cleared
   without a USB re-plug.
4. **Read the Type-C Rp advertisement** instead of relying on VINDPM.
5. **Re-floorplan the `U9` NFC block** so decoupling sits at the pins.
6. **Restore the full ten-XGPIO expansion architecture** and `U23`.

---

## 10. What a reviewer should read, in order

1. `CTO_DECISIONS.md` — **D-763 through D-750** at the top; these entries are
   the external-review closure and the later mechanical/manufacturing re-checks.
2. `CURRENT_STATE.md` §1.
3. `hardware/demo/manufacturing/evidence/d763-release-verification.json` — the
   current connectivity, DRC/parity, `FAB1`–`FAB13`, 19-contract regression,
   battery, firmware and mechanical release summary.  Read the referenced
   `d763-*` contract artifacts beside it for the live negative controls.
3a. `Firmware/src/hw/aqroot_demo_board.h` — the generated as-built map, and the
   only pin map that describes this board.
4. `hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_dru` **section 5a** — the
   one named ampacity exception, written in full with its measurements.
5. `DEVICE_SPEC.md` **§0a** — the Demo delta every Kickstarter claim must read.
6. `hardware/demo/kicad/aqroot-demo/vendor/` — the TI and Samtec datasheets this
   cycle's conclusions are drawn from, with their hashes.
