# AQROOT Demo — FABRICATION HANDOFF

**Board:** `hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb`
**Authority:** `sha256 bdf1376cf95289452ca24150eb0738f7a9dacddf40bb422f2575869b05cf1ce6`
**Package:** `hardware/demo/fab/` — 29 files, regenerated at this authority
**Date:** 2026-09-18 · **Decisions:** D-742 … D-751 · **Prepared for:** independent CTO review

> **THIS HANDOFF WAS REOPENED AND RE-ISSUED.**  It was first written at
> `c7f5c618`.  An external first-spin review (Fable 5.1 + Astra) then found
> four real defects in that package — a `J5` BOM identity naming the superseded
> 2×12 `BCS-112-S-D-HE`, a physically floating `U14` `QSTRT`, a charger-input
> audit computed at the wrong inner-copper thickness, and two boost converters
> with no local input capacitor.  **D-750 closed all four and dispositioned the
> other nine items; D-751 finished the transaction and re-ran the whole
> release suite.**  Read
> `audits/2026-09-18-d750-first-spin-review-dispositions.md` beside this file.

---

## 1. Final board status

77.000 × 148.000 mm stepped outline, 6 copper layers, 3550 tracks, 918 vias,
71 zones, 312 footprints, 295 fitted references and 16 schematic-DNP.

| measure | value |
|---|---|
| retained multi-pad nets | **173** |
| connected retained nets | **172** |
| retained open edges | 1 |
| **unapproved open edges** | **0** |
| approved Demo NC | `J5.9`–`J5.12`, `J5.15`–`J5.18` — expected == observed |
| approved unrouted | `U11.3` only, under the 2026-09-17 owner decision |
| open owner decisions | **none** |

The single unrouted contact is `/BQ25185_STAT2` at `U11.3`. The owner approved
shipping it bare on 2026-09-17; `routing_ledger.py` re-proves that declaration
against the board on every run — the pad must exist, its part be fitted, it must
still carry `/BQ25185_STAT2`, it must still be stranded, and `R128` and `TP7`
must still be fitted — and **fails if any of those stops being true**.

## 2. Major design changes in this cycle

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
   One `AO3400A` (same BOM line as `Q1`, LCSC `C20917`) in the panel cathode
   return.  Outside the regulation loop by construction, so the 109 mA setpoint
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

`routing_ledger.py`: 172 of 173 retained nets connected, `unapproved_open_edges`
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
| all five IGNORED rules promoted to error | 2 `missing_courtyard` (`BOSS1`/`BOSS2` mounting bosses), 5 `track_not_centered_on_via`, **zero new** |
| `connection_width`, probed at 0.20 mm | 81 distinct pairs, 74 benign acute throats, 7 below 0.15 mm, **none load-bearing** |
| pour islands | 95 filled islands over six layers, **zero orphans** |

`min_connection` is 0.000 mm in board setup, so KiCad never runs
`connection_width` — the same defect class D-738 found in
`solder_mask_min_width`. It is probed in a scratch copy and the board setup is
deliberately left alone; the measurement is the deliverable.

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

`contract_regression` runs **17 contracts: all ran, all PASS**, with
`protected_copper` **IDENTICAL to the `d746` baseline** — the fifteen protected
nets and their 406 objects did not move through any of this.

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
   enclosure, at the fitted cell capacity.** Prefer the **2500 mAh** end of the
   envelope; 3000 mAh at 40 °C ambient is the least-margin corner.
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

8b. **NFC MATCHING MUST BE RE-DERIVED FROM THE PRIMARY SOURCE** (item 6). There
   is no dedicated shunt position between the series capacitors and the
   antenna, and ST `AN5276` and the ST matching tool could not be retrieved
   from this environment — so the topology was **not** changed on a
   recollection. It is not a pre-order blocker because the tune position is
   **fittable by construction**: `NFC_MATCH_A` and `NFC_MATCH_B` each sit
   **0.500 mm** from B.Cu `GND` fill, on the same layer, symmetrically, so a
   parallel element is an ordinary 0402 tacked across a measured gap at first
   article — no rework, no cut track, no symmetry loss. Obtain `AN5276`,
   re-derive `C_s`/`C_p`/`R_q` from the MEASURED antenna and ferrite with the
   rear shell and battery installed, and record the final values before any
   second article.
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
   — `Q11`'s drain — follows the anode to ≈ 36 V across a **30 V** `AO3400A`.
   `D14`/`C85`/`R132` make that unreachable by construction: the gate follows
   the ENVELOPE of `DISP_BL_CTL` with **τ = 22 ms**, so `Q11` cannot open
   before **11.4 ms** at worst-case tolerance while `U17` is in shutdown by
   2.5 ms — **4.6× margin, waveform-independent, no firmware sequencing**.
   `demo_feature_contract.py` **F5** refuses any board that collapses the two
   nets, drops `C85`, substitutes a Schottky for `D14`, or retunes `R132`.
   **A revision that wants to PWM `Q11` independently must re-rate it to at
   least 40 V `VDS` first.**

11. **THE ACCESSORY ENVELOPE IS NOW BOUNDED BY SILICON, AND ONE THERMAL
   RESIDUAL IS NAMED** (D-753). Both `TPS22950C` `ILIM` resistors are **2.7 kΩ**
   (`R97` was 1.5 kΩ, `R101` 1.65 kΩ), so each accessory rail guarantees
   **0.277 A** and cannot pass more than **0.537 A** over −40…+125 °C. At the
   3.0 V cell corner with the full 1.0 A internal `+3V3` load, no state a user
   can reach exceeds the `BQ25185` `IBAT_OCP` **minimum of 2.5625 A** — the
   worst is 2.229 A, 13 % under — and a *simultaneous double limiter fault*
   reaches 2.886 A, which trips the charger's own OCP and **auto-retries**,
   below the `LTC4368`'s 3.33 A and far below `F1`. `demo_feature_contract.py`
   **F6** recomputes this from the two resistors with four live controls.
   **THE RESIDUAL:** `BAT_MAIN` copper is sized for 1.5 A sustained, and the new
   worst *sustained* case — both accessories at their guaranteed current with
   the full internal load — is 1.69 A at 3.7 V and 2.08 A at the 3.0 V corner,
   on one unavoidable 5.525 mm × 0.200 mm segment (`U11`'s `DLH0010A` pin-2
   `BAT` land). The plane-coupled ceiling is ≈ 37 K over the adjacent `In4`
   plane at 2.08 A, from a model that ignores lateral spreading, conduction and
   convection. **Measure that segment at first article with both accessory rails
   loaded and the cell at 3.3 V.**

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

1. `CTO_DECISIONS.md` — **D-748, D-747, D-745, D-744, D-743, D-742** at the top.
2. `CURRENT_STATE.md` §1.
3. `hardware/demo/manufacturing/evidence/d74[2-8]-*.json`, and in particular
   `d748-release-verification.json` — connectivity, DRC, `FAB1`–`FAB11`, the
   17-contract regression and the firmware contract in one document.
3a. `Firmware/src/hw/aqroot_demo_board.h` — the generated as-built map, and the
   only pin map that describes this board.
4. `hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_dru` **section 5a** — the
   one named ampacity exception, written in full with its measurements.
5. `DEVICE_SPEC.md` **§0a** — the Demo delta every Kickstarter claim must read.
6. `hardware/demo/kicad/aqroot-demo/vendor/` — the TI and Samtec datasheets this
   cycle's conclusions are drawn from, with their hashes.
