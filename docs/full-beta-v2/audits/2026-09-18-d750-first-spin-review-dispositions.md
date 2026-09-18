# D-750 — DISPOSITION OF THE EXTERNAL FIRST-SPIN REVIEW (Fable 5.1 + Astra, 2026-09-18)

> This file answers, item by item, the external first-spin review that REOPENED
> `DEMO_READY_FOR_FAB` at `b593b97`.  Every "CONFIRMED" item is closed with the
> change that closes it; every "HYPOTHESIS" item is adjudicated against the
> authoritative board, schematic and primary vendor data, and is marked either
> **CLOSED**, **CLOSED BY CHANGE**, **FIRST-ARTICLE** (a measurement that can
> only be made on hardware, and which does not block the PCB order) or
> **PROCUREMENT** (a purchasing action, not an engineering one).
>
> The review's own release rule is the bar used here: *"remaining
> first-article/fabricator items are explicitly separated from pre-order
> blockers."*

## 1. J5 RELEASE BOM SEMANTIC DEFECT — **CLOSED BY CHANGE**

CONFIRMED against the release.  `hardware/demo/fab/aqroot-Demo-BOM-assembly.csv`
line 42 paired footprint `AQROOT_Beta:Samtec_SSQ-124-02-G-S-RA` with MPN
`BCS-112-S-D-HE`, LCSC `C5575816` and a "2x12 24-contact" description.  The PCB
carries **one row of 24 through-holes at x = 65.900**, verified pad by pad.

ROOT CAUSE, and it is worth stating because it is the general defect: **D-237
(FBV2-EXP-002) replaced the 2 × 12 BCS with the 1 × 24 SSQ and moved the
`Footprint` and `Datasheet` properties, and left `MPN`, `LCSC`, `Description`,
`Alternate`, `Note` and `Note2` on the superseded part.**  `DEVICE_SPEC.md`,
`SOURCING_LEDGER.md`, `ARCHITECTURE.md` and the footprint library were all
correct; only the purchasing identity was stale, and no gate compared the two.

CLOSED BY:
* The schematic instance now carries `MPN = SSQ-124-02-G-S-RA`,
  `LCSC = C3323671`, a corrected `Description`, a corrected `Alternate`, a
  rewritten engineering `Note` describing a ONE-ROW part, a rewritten `Note2`
  and a new `Note_Sourcing` recording the correction.
* **D-096 SATISFIED LIVE**: `jlc_live.py` read the JLCPCB parts catalogue on
  2026-09-18 and the record is committed at
  `evidence/jlc-live/ssq-124-02-g-s-ra-b06f80e6.json` — Samtec
  `SSQ-124-02-G-S-RA`, LCSC `C3323671`, **Number of Rows 1**, **Number of
  Positions 24P**, pitch 2.54 mm, square hole, **Mounting Type Right Angle**,
  gold, phosphor bronze, −55…+125 °C, `expand` library, **stock 0**.
* The ALTERNATE is also a live record, not a configured guess:
  `SSQ-124-02-F-S-RA` = LCSC `C6686579`, same body and same footprint, plating
  suffix only.  The record's "Contact Plating: Tin" disagrees with Samtec's own
  `-F` = *gold flash on contact, matte tin on tail*; that disagreement is
  RECORDED RATHER THAN RESOLVED and the alternate is marked as needing Samtec
  confirmation before substitution.  `SSQ-124-02-L-S-RA` (10 µin gold) is a
  valid datasheet configuration with **zero distributor records** and is
  therefore NOT baselined — the third time D-096 has refused a configured part
  number on this project.
* **STOCK 0 IS NOT A NEW PROBLEM AND IS CARRIED FORWARD HONESTLY**: `J5` has
  been MANUAL/SECONDARY assembly since FBV2-S1-009 and is bought direct from
  Samtec or a broadline distributor.  The LCSC line exists so the identity is
  machine-checkable, not because the part is ordered there.

A GENERAL GATE, NOT A ONE-OFF FIX — see item 11.

## 2. U14 MAX17048 QSTRT FLOATING — **CLOSED BY CHANGE**

CONFIRMED.  The board net was `unconnected-(U14-QSTRT-Pad6)` and the schematic
carried a deliberate `no_connect` at the QSTRT pin, which is why ERC passed.

This is a real defect independently of the exact datasheet wording.  QSTRT is a
CMOS input with no internal pull on a part whose headline specification is
**3 µA quiescent current**: a floating input can sit in the crossover region and
dominate the whole device's current, and a rising edge on it forces a
quick-start that discards the ModelGauge state and re-estimates state-of-charge
from the instantaneous open-circuit voltage — a wrong battery percentage with no
error indication.

CLOSED BY: the `no_connect` is removed, the pin is wired to `GND` on
`01_power_tree.kicad_sch` (`#PWR0732`), and the board pad is on `GND`.  **It
needed no new copper**: the B.Cu `GND` pour reaches the land, and KiCad's own
connectivity resolves it to the 980-item `GND` cluster after a refill.  The
change also REMOVES one inherited `footprint_symbol_mismatch` parity warning
(46 → 45).

## 3. CHARGER INPUT AUDIT USED THE WRONG INNER-COPPER THICKNESS — **CLOSED BY CHANGE**

CONFIRMED, and the consequence was larger than a number.  See
`.kicad_dru` sections 5 and 5a, which are rewritten, and item 3 of the D-750
decision entry.  Summary:

| | before D-750 | after D-750 |
|---|---|---|
| inner copper used by the audit | 0.0174 mm (nominal half-ounce foil) | **0.0152 mm**, read back from the board's own `(stackup)` |
| `USB_VBUS_CHG` carrying path | 250.784 mm | **189.819 mm** |
| series resistance | 440.2 mΩ *(487.4 at the real copper)* | **215.6 mΩ** |
| drop at 1.1 A | 484 mV *(536 at the real copper)* | **237 mV** |
| dissipation at 1.1 A | 0.533 W *(0.589)* | **0.261 W** |
| worst IPC-2221B rise | 147.6 K *(184.4)* | **66.5 K** |
| derived plane-coupled rise | asserted "of order 1 K" from a WRONG stackup | **1.45 K**, computed from the board |

`audit_rail_ampacity.py` now READS THE STACKUP BACK and fails itself if its
constants and the board disagree, so this cannot drift again.

## 4. U21 TPS61023 INPUT DECOUPLING — **CLOSED BY CHANGE**

CONFIRMED.  The nearest capacitor on `/01_POWER_TREE/BQ25185_SYS` to `U21` was
`C27` at 36.552 mm and the *named* 10 µF input capacitor `C64` was 93.482 mm
away.  The same is true of the second boost, `U13`, which the review did not
name: its nearest was also `C27`, and its named input capacitor `C33` was 88 mm
away.

**THE REVIEW'S SUGGESTED FIX WOULD HAVE CUT THE RAIL.**  `C64` and `C33` cannot
be moved: both are **PASS-THROUGH JUNCTIONS** on the SYS trunk — the 0.8 mm
copper enters their SYS land and leaves it again — so relocating either breaks
the feed to both southern boosts.  That is measurable in the file
(`C64.1` joins `(9.400,120.300)` to `(8.800,118.600)`) and `apply_part_shift.py`
refused the move with `RELEASE_WOULD_STRAND`.

CLOSED BY adding the local bypass neither converter ever had:

* **`C83`** 10 µF 10 V X7R 0805 at `(51.788, 37.000)` B.Cu, **5.818 mm** from
  `U21.3`, tapped to the SYS trunk with 2.4 mm of 0.8 mm B.Cu.
* **`C84`** 10 µF 10 V X7R 0805 at `(54.787, 20.100)` B.Cu, **3.500 mm** from
  `U13.3`, its SYS land landing directly on the 0.8 mm trunk.

Both are the SAME BOM LINE as `C33`/`C64` (YAGEO `CC0805KKX7R7BB106`, LCSC
`C326595`): two pieces added to an existing line, no new purchasing identity.

**AND THE TRUNK ITSELF IS NOW MEASURED.**  Section 5's SYS row had carried
"LOCAL EXCEPTION, NOT ENCODABLE: the U21 accessory boost draws a 2.19 A peak
inductor current from SYS, so the SYS segment that feeds U21 must be sized from
that peak" since D-185, and **nothing had ever checked it** — the only SYS rail
in the ampacity audit was `U11.1 → U12.1`, which is pour-delivered and answers a
different question.  Two rails are added:

| rail | design A | length | R | drop | IPC | plane-coupled |
|---|---|---|---|---|---|---|
| SYS → `U21`/`L4` (5 V accessory) | 1.21 | 201.8 mm | 183.3 mΩ | 222 mV | 58.6 K | **1.16 K** |
| SYS → `U13`/`L2` (NFC 5 V, DNP) | 0.86 | 222.1 mm | 196.5 mΩ | 169 mV | 27.0 K | **0.59 K** |

Declared in `.kicad_dru` section 5c with their numbers.  The design current is
the INPUT AVERAGE; the 2.19 A peak is what `C83` now supplies locally, which is
the whole point of adding it.

## 5. DISPLAY J1 / FPC PIN-1 END AND TAIL ENTRY — **FIRST-ARTICLE, with a definitive incoming test**

NOT CLOSED BY DOCUMENT, and the review is right that the FH69's dual-contact
feature does not by itself prevent a mirrored tail.  The `ER-TFT035IPS-6`
mechanical drawing is not in this repository and the vendor's site is behind a
Cloudflare challenge from this environment, so the drawing could not be
retrieved.  What IS established:

* The **electrical** pin table is verbatim from the vendor datasheet and was
  independently validated at FBV2-S1-005, where it caught two inherited faults
  in `J1` (reversed backlight anode/cathode, swapped SCL / D-CX).
* `J1`'s land pattern is vendor-exact (Hirose FH69 recommended layout) and
  **pin 1 is marked on silkscreen** — a filled circle at footprint-local
  `(13.100, −1.500)`, beside pad 1.  `J1` pin 1 is at board `(44.910, 96.000)`,
  the EAST end; pin 50 is at `(20.410, 96.000)`.
* **THE CONSEQUENCE OF GETTING IT WRONG IS DESTRUCTIVE, NOT MERELY DARK.**
  Mapping pin *N* ↔ pin *51 − N* gives **16 power-to-signal collisions**,
  including `+3V3` onto panel `SCL`/`SDA`/`SCK`/`MOSI`/`SDO`/`CS`/`DC`, and the
  backlight anode — which the `TPS61169` drives to ~4.2 V normally and up to
  39 V into an open LED string — onto panel `GND`.

**THE INCOMING TEST THAT SETTLES IT WITHOUT THE DRAWING**, and it is decisive:
the panel's own pin 1/2/3 are `LED_A`/`LED_K`/`LED_K` and its pins 48/49/50 are
`GND`.  On a bare panel tail, a meter in diode mode reads **an LED forward drop
of roughly 2.5–2.9 V between the outermost contact and its two neighbours at
the PIN-1 END**, and **a dead short to the panel's ground plane at the other
end**.  One measurement, no drawing, no ambiguity.

REQUIRED BEFORE MATING ANY PANEL; **NOT a PCB-order blocker** — `J1`'s land
pattern and pin map are correct for the datasheet pin table either way.
Recorded in the fabrication notes and the assembly plan.

## 6. NFC MATCHING TOPOLOGY — **CLOSED, NO BOARD CHANGE; the tune position is fittable by construction**

CORROBORATED and dispositioned.  The as-built differential arm is

    RFO1 -> L5 39 nH -> node NFC_EMCA { C69 100 pF |GND, C73 1.5 nF |GND }
         -> C71 300 pF (series) -> NFC_MATCH_A -> R114 1R1 -> NFC_ANT_A -> J7

and the only element at `NFC_ANT_A` besides the antenna is the RECEIVE divider
(`C75` 27 pF series, `C76` 620 pF shunt), which presents about 25.9 pF — 453 Ohm
at 13.56 MHz — and is not a matching element.  **The review's structural
observation is correct: there is no dedicated shunt position between the series
capacitors and the antenna.**

WHAT THE REVIEW CONDITIONS THE CHANGE ON COULD NOT BE DONE HERE, AND THAT IS
SAID PLAINLY.  The instruction is *"add tune positions only if the primary-source
analysis supports it"*, and the primary source — ST `AN5276` and the ST25R3916
matching tool — is not in this repository and could not be retrieved (the
vendor sites answer a Cloudflare challenge from this environment).  Evaluating
the as-built set at 13.56 MHz against the LOCKED antenna (Taoglas
`FXC.46.52.0075X.B`: `La` 1.10 uH, `Rs` 1.50 Ohm, plus 2 x `Rq` 1.1 Ohm) gives a
differential input of about **54 - j23 Ohm** against D-133's **36 Ohm** target,
and moving `C73`/`C74` to the far side of `C71`/`C72` does not reach it either
(about 0.07 - j62 Ohm).  **Neither ordering matches with the present values**,
which is consistent with this repository's own standing position — every value
in the NFC front end is marked `TUNE` and first-article tuning with the real
antenna, rear shell, PCB and battery installed is REQUIRED (D-129/D-134).
Changing an RF topology on a recollection of a note I could not read is exactly
the *"do not blindly implement reviewer suggestions"* the review opens with, and
it is not done.

**WHY THIS IS NEVERTHELESS CLOSED AND NOT A PRE-ORDER BLOCKER.**  The reason a
missing tune position is normally unrecoverable is that it cannot be added after
fabrication.  That is not true here, and it is measured rather than assumed:
**`NFC_MATCH_A` and `NFC_MATCH_B` each sit 0.500 mm from B.Cu `GND` fill, on
the same layer**, symmetrically (the fill reaches `(44.611, 28.253)` and
`(44.611, 32.653)` against nodes at `(44.400, 27.800)` and `(44.400, 32.200)`).
A parallel tune element is therefore fittable at first article as an ordinary
0402 tacked across a 0.5 mm span at exactly the right node, on both arms
identically — no board rework, no cut track, no symmetry loss.  The whole NFC
front end is already a first-article tuning exercise; this adds one more
component to that exercise instead of one more component to the BOM.

NAMED FIRST-ARTICLE TASK: obtain `AN5276` and the ST matching tool, re-derive
`C_s` / `C_p` / `R_q` from the MEASURED antenna and ferrite with the rear shell
and battery installed, and fit the parallel element at `NFC_MATCH_A`/`B` if the
derivation calls for one.  Record the final values in `CTO_DECISIONS.md` before
any second article.

## 7. TPS61169 BACKLIGHT TRUE-OFF — **CLOSED BY CHANGE**

CONFIRMED as a design-condition failure and quantified.  The shutdown DC path
is `+3V3 → L3 → D8 → R70‖R73 (8.25 Ω) → six parallel panel LEDs → R69 1.87 Ω →
GND`.  TI guarantees OFF only when the LED array's minimum forward voltage
exceeds the maximum VIN; D-079 records this panel's backlight as **six LEDs in
parallel, 2.9–3.2 V at 120 mA**, and the rail is 3.3 V, so the condition fails.
Solving the network with a white-LED forward curve converges at **≈ 25 mA** —
about a fifth of full brightness, plainly visible in the dark, and ≈ 82 mW of
continuous drain.  **There is no firmware mitigation**: `+3V3` is switched by
`SW9`, a slide switch, so the screen would never go dark while the device is on.

CLOSED BY `Q11`, one `AO3400A` in SOT-23 — **the same BOM line as `Q1`** — in
the panel cathode return between `J1` and the `LED_K` sense node, gate on
`DISP_BL_CTL`.  It is outside the regulation loop by construction (`U17`'s LED
pin and `R69` both sit on the SOURCE), so the 109 mA setpoint and its
100.5–117.6 mA band are unchanged; `RDS(on)` costs ≈ 2.4 mV of headroom.  The
off state is proven rather than assumed: `R108` holds the gate low through
boot, reset, GPIO high-impedance and firmware crash, the body diode is
reverse-biased, and `IDSS` is under 1 µA.

**D-751 CORRECTED ONE SENTENCE OF THIS ITEM, AND CORRECTED IT THE WRONG WAY.**
D-750 had written that PWM "now gates the LED current directly instead of
restarting the converter every cycle".  D-751 replaced that with the claim that
the shared gate is the SAFE arrangement and recorded it as a constraint.
**D-752 read the primary source and found the opposite.**  TI `SNVSA40B` §6.3.5:
the `TPS61169` "chops up the internal 204 mV reference voltage at the duty cycle
of the PWM signal", filters it, and therefore *"only the WLED DC current is
modulated, which is often referred as analog dimming"*.  **The converter keeps
switching through every PWM low phase**; §6.3.3 enters shutdown only after
`CTRL` has been low for longer than `tSD`, 2.5 ms max.  So the shared gate
created exactly the forbidden state on every dimmed frame: `FB` below the 30 mV
open-LED threshold, `SW` at `VOVP_SW` (36 / 37.5 / 39 V), §6.3.2 latching the
part off after three switching cycles, and `Q11`'s DRAIN — the panel cathode —
at ≈ 36 V while `R69` holds its SOURCE at 0 V.  **The `AO3400A` is a 30 V
part.**  The firmware already drives `ledcSetup(5000, 8)` on GPIO46; the first
brightness ramp would have latched the backlight off and over-stressed `Q11`.

**D-752 SEPARATED THE TWO FUNCTIONS IN HARDWARE.**  `Q11`'s gate is now
`/03_SPI_A_DISPLAY_SD/BL_DISC_G`, driven by an ENVELOPE of `DISP_BL_CTL`:
`D14` (1N4148WS, LCSC `C2128`, JLCPCB BASIC, the SOD-323 land this board
already carries) charges `C85` (100 nF) in ≈ 25 µs against `U17`'s 6.5 ms
soft-start, and `R132` (220 k) discharges it with **τ = 22 ms**.  `Q11` cannot
open before **11.4 ms** at worst-case tolerance, and `U17` is in shutdown by
**2.5 ms** — the converter always stops FIRST, for any `CTRL` waveform, with no
firmware sequencing.  `demo_feature_contract.py` **F5** holds the topology with
four live negative controls.  The `RDS(on)` headroom figure is also corrected:
at the worst published 48 mΩ at `VGS` 2.5 V it is **5.2 mV at 109 mA**, not
2.4 mV.

## 8. BATTERY MUST BECOME A FROZEN, QUALIFIED PART — **PROCUREMENT + FIRST-ARTICLE**

Not a PCB defect and not closable by a board change.  The cell envelope, the
two candidate parts (PKCELL `LP755070` 3000 mAh / `LP785060` 2500 mAh, both
PCM-fitted, JST-PH lead) and the protection architecture are locked; what is
open is a PURCHASING decision to name one part and a QUALIFICATION programme.
D-750 contributes the two engineering inputs that decision needs and did not
have:

* **the charge-timer margin across the source envelope** (item 3 and the D-750
  entry): with the corrected 235 mΩ board resistance every case in the envelope
  terminates with at least 65 min of the 360 min `tMAXCHG` to spare, where the
  pre-D-750 board **exceeded the timer** on an ordinary 4.65–4.75 V source at a
  150–300 mA system load;
* **the combined-load concurrency bound** (item 9).

REMAINS OPEN as a product/procurement action; it does not block the PCB order.

## 9. COMBINED-LOAD CONCURRENCY — **CLOSED AS A PUBLISHED LIMIT**

Computed from the board's own published rail currents.  `ACC_3V3_SW` is a load
switch off `+3V3`, so it is part of the `+3V3` draw; `ACC_5V_SW` is a boost off
`SYS`.  At 90 % (buck-boost) and 88 % (boost):

| permitted mode | I(SYS) @ 3.0 V | @ 3.7 V | @ 4.2 V |
|---|---|---|---|
| internal only, full 1.0 A on `+3V3` | 1.22 A | 0.99 A | 0.87 A |
| internal + 3.3 V accessory at 0.40 A | 1.71 A | 1.39 A | 1.22 A |
| internal + 5 V accessory at 0.70 A | 2.55 A | 2.07 A | 1.82 A |
| **all three at published maxima** | **3.04 A** | 2.46 A | 2.17 A |

**THE BOARD CANNOT SUPPORT ALL THREE AT THEIR MAXIMA SIMULTANEOUSLY FROM THE
BATTERY, AND IT WAS NEVER DESIGNED TO.**  `.kicad_dru` section 5 publishes
`BAT_MAIN` at **1.5 A sustained**, which is what the protection path, `Q2`/`Q3`
and the battery trunk are sized for; 3.04 A is also at the `BQ25185`
`IBAT_OCP` trip (3.125 A typical, ±18 %).  The published limit is therefore:

> **AQROOT Demo accessory-power policy.**  The sum of accessory draw is bounded
> by `BAT_MAIN` 1.5 A sustained.  At the 3.0 V end of the cell that is 4.5 W
> total: full internal load (3.67 W) leaves **0.83 W** for accessories — 0.15 A
> at 5 V *or* 0.23 A at 3.3 V.  At 3.7 V the allowance is 1.88 W — 0.33 A at
> 5 V *or* 0.51 A at 3.3 V.  The per-rail figures in section 5 (0.40 A on
> `ACC_3V3`, 0.70 A on `ACC_5V`) are EACH-ALONE maxima, not a simultaneous
> budget.

This is ENFORCEABLE, which is why it is a closure and not a note: both
accessory rails are switched by the MCU through `U3` (`ACC_5V_BOOST_EN`,
`ACC_5V_SW_EN`, `ACC_3V3_EN`), and `ACC_POWER_FAULT_N` already drops both on a
fault.  Recorded in `DEVICE_SPEC.md` and the fabrication notes.

> ### **SUPERSEDED — READ D-753 AND D-765 INSTEAD.  THE PARAGRAPH ABOVE IS WRONG ON THE POINT IT RESTS ON.**
>
> **It is NOT enforceable.**  The independent re-review answered that firmware can
> choose whether a rail is ON and **cannot know what an arbitrary external
> accessory then draws** — this board has **no accessory current measurement** —
> and it is right.  **D-753** replaced the policy with a limit the silicon
> enforces: both `ILIM` resistors to **2.7 kΩ**, so each rail's own limiter
> guarantees **0.277 A** and caps at 0.537 A.  It also measured that at the
> values this disposition shipped, **two states a user could reach with
> conforming accessories already tripped the pack protection** (2.930 A and
> 2.737 A against an `IBAT_OCP` minimum of 2.5625 A).  The per-rail figures
> quoted above (0.40 A / 0.70 A) are retired, and the "0.15 A at 5 V or 0.23 A
> at 3.3 A" allowance is **smaller than what the silicon now guarantees**.
>
> **D-765** then found that the chosen setting was outside the fitted part's own
> specified `ILIM` range (`TPS22950C`: 0.5–3.5 A, `SLVSFJ2B` §5) and replaced
> `U20`/`U22` with the **`TPS22950-Q1`**, specified from 0.05 A, with no
> resistor, copper or envelope change.  The live envelope is
> `checks/demo_feature_contract.py` **F6** and `DEVICE_SPEC` §6.3a; this section
> is retained only as the record of what was closed wrongly.

## 10. SPECIAL FAB PROCESSES — **FABRICATOR CONFIRMATION, already asked by name**

`aqroot-Demo-FAB-NOTES.md` is generated from the board and already NAMES every
one of them with its measured number and asks the fabricator to confirm:
drill-to-copper on the `J3` NPTH pegs (0.2100 mm tracks / 0.2412 mm via against
JLCPCB's published 0.200 mm), the `MK1` acoustic port (Ø1.05 mm unplated hole
through its own Ø1.65 mm land, 0.30 mm annulus, copper deliberately exposed in
the barrel), **129 via barrels opening into 135 solderable lands across 76
components** on 0.20/0.25/0.30/0.40 mm holes with the fill/cap process stated,
sub-floor annular rings, the mask webs (four `U9` UFQFPN corner pairs at or
under 0.100 mm to be GANGED, eight `U12` rows at 0.120 mm to be printed or
ganged), the stepped profile with its two inside corners and their measured
0.941 mm and 0.726 mm relief limits, and the stackup and copper weights.

WHAT THE REVIEW ASKS FOR — *measurable manufacturer acceptance* — is a REPLY,
not a change.  These are **PRE-ORDER PROCUREMENT** items: the package must be
quoted and the fabricator's answers recorded before release to production, and
they are listed as such rather than treated as engineering blockers.  D-750
adds the corrected stackup statement to the `.kicad_dru` header, which had
still described a **4-layer** `JLC04161H-7628` stack with "no physical stackup
object" long after D-263 locked the 6-layer stack and the board declared it.

## 11. SEMANTIC RELEASE GATES — **CLOSED BY CHANGE**

The review's negative controls are correct and the gaps are closed:

* **`FAB5` compared X/Y/side and NOT ROTATION**, and compared reference SETS, so
  a 180°-wrong rotation on a polarised part, a duplicated row, and a corrupted
  `pos-fitted` file (only `pos-all` was ever geometry-checked) all passed.
  `FAB5` now checks **position, side AND rotation on BOTH placement files with
  per-file reference uniqueness**.  The rotation convention is MEASURED, not
  assumed: on the released package all 262 rows satisfy
  `Rot == GetOrientationDegrees()` normalised to (−180, 180] on both sides.
* **`FAB6`/`FAB7` could accept a consistently regenerated wrong identity** —
  which is exactly how item 1 survived eight months of gates, because every
  check asked only whether the package was INTERNALLY consistent.  **`FAB12` is
  new**:
  * **`FAB12a`** reads each BOM row's OWN WORDS — a stated `A × B` geometry, a
    contact/position/pin count, a pitch — against the footprint's OWN PADS, with
    a thermal-pad tolerance so a "10-pin WSON" with eleven lands is not a false
    positive.  Run against the stale released package it reports exactly the
    real defect and nothing else: **`J5` row says `2x12`, footprint is `1 × 24`.**
  * **`FAB12b`** pins **41 critical identities** by name — every connector,
    every converter, every radio, the charger, the fuel gauge, the microphone,
    the protection FETs and the crystal — with MPN, footprint and value, and
    re-checks the footprint against the BOARD as well as the BOM.  It is a
    REGRESSION instrument and says so: it cannot find an identity that was
    already wrong when it was written, which is why `FAB12a` exists beside it.

`route_maze_batch.py`'s promotion clause 8 is also repaired: `--tap-first`
closes an edge with real copper and the maze then reports `already`, so a run
that closed every requested edge read as "nothing happened" and was refused.
The clause now counts taps, which are individually named in the run's own
report.

## 12. FIRMWARE BEFORE DEMO — **CLOSED BY CHANGE (five of six), one PROCUREMENT**

* **MAX17048 `VERSION` read as 16-bit** — CONFIRMED and fixed.  Every MAX17048
  register is 16 bits MSB-first; the probe read ONE byte.  Worse for a
  diagnostic: `VERSION` reads `0x001x` on every part ADI ships, so the MSB is
  `0x00` and the generic "report only" predicate treated `0x00` as a FAILURE —
  **the old code reported a healthy fuel gauge as broken.**
* **Microphone BCLK** — CONFIRMED and fixed.  The capture used 16 kHz in 32-bit
  slots on two channels = **1.024 MHz** BCLK, inside the low-power band of this
  class of I2S MEMS microphone, where a bring-up test that "worked" would have
  proved the wrong thing about the fitted part.  Raised to 48 kHz =
  **3.072 MHz**.  FIRST-ARTICLE: confirm the exact band against the
  `DMM-4026-B-I2S-R` datasheet; the new number is chosen to be inside it rather
  than on its edge.
* **Shutdown must attempt all reachable independent controls after one I2C
  error** — CONFIRMED in three places and fixed in all three.
  `DemoExpanders::begin()` short-circuited on `||`, so a NACK from `U2` meant
  `U3` — which owns `NFC_5V_EN`, both radio resets and both transmit enables —
  was **never driven into its safe state at all**.  `service()` short-circuited
  the same way, and `U3` is the device whose input port carries
  `ACC_POWER_FAULT_N`, so the one bus error that mattered most was also the one
  that stopped the fault being seen.  `setAccessory5v(false)` and
  `setAccessory3v3(false)` each gave up after a failed first write, leaving the
  accessory rail live during exactly the fault they were called for.
* **Diagnostics must not print success after discarded failures** — fixed: the
  fault shutdown's outcome is RECORDED (`faultShutdownSeen()`,
  `faultShutdownOk()`) instead of `(void)`-discarded, and `service()` returns
  false if the shutdown writes failed.
* **PCAL9535A reset defaults and warm-reset retained state** — already
  mechanised at D-747 and re-verified here: the generator refuses to emit
  unless every expander output's safe latch equals the level its fitted
  external pull already holds, and the host test compiles a RECORDING `I2cBus`
  and asserts direction-after-latch ordering with 40 claims and controls that
  catch the reverse.
* **Pin the first-flash `aqroot-demo` image** — **PROCUREMENT**: a release
  artifact to be produced and hashed when boards are ordered, not an
  engineering change.

## 13. RELEASE DOCUMENTATION / MECHANICAL CONTRACT — **PARTLY CLOSED, remainder PROCUREMENT**

Closed here: the `.kicad_dru` stackup header (4-layer → 6-layer, real foil
thickness), the section 5 width table, the section 5a exception and the new
section 5c, the corrected `J5` identity everywhere it is derived, and the
accessory-power policy of item 9.

Remaining as PROCUREMENT / first-article: `BOSS2` coordinate authority and the
coordinate convention statement, assembly-drawing framing/revision/hash, the
exact panel procurement contract (which the item-5 incoming test now makes
checkable), the `J5` enclosure recess dimension, and the M-09 tolerance stack.
None of these changes copper.

---

## SEPARATION REQUIRED BY THE REVIEW'S OWN RELEASE RULE

**PRE-ORDER BLOCKERS — all closed by D-750:** items 1, 2, 3, 4, 7, 9, 11 and
12 (five of six).

**PROCUREMENT / FIRST-ARTICLE — explicitly NOT pre-order blockers:** item 5
(panel tail incoming test, with a decisive procedure), item 6 (NFC re-derivation
from the primary source, with the tune position proved fittable at 0.500 mm),
item 8 (freeze and qualify the cell), item 10 (fabricator acceptance of the
named special processes), item 12's first-flash image, item 13's mechanical
documentation.


---

## D-751 ADDENDUM — WHAT D-750 LEFT OPEN, AND WHAT CLOSING IT FOUND

D-750 was written before its own transaction was finished.  Five corrections to
the record above, all closed at D-751 on board authority `bdf1376c`:

1. **ITEM 7 WAS NOT CLOSED BY CHANGE — `Q11` WAS FITTED AND NOT CONNECTED.**
   The live ledger carried three unapproved open edges, `LED_K`,
   `LED_K_PANEL` and `DISP_BL_CTL`, every one of them a `Q11` pin.  They are
   routed now: three `--tap-first` taps, 16.26 mm of conductor, four barrels.
   The first run was REFUSED because the `LED_K_PANEL` tap landed on the side
   of the In2 run and left 0.44 mm hanging past the T — one `track_dangling`
   warning.  The stub was trimmed to the tap point first.

2. **ITEM 4's `C83` DISTANCE IS NOW DERIVED, NOT ASSERTED.**  An independent
   check asked whether a shorter input loop is available.  It is not, cheaply —
   `TP28`'s land is the only free B.Cu between `C83` and `U21` — and the
   measurement says it does not matter: **`U21.3` is the controller's BIAS pin,
   not the power path** (D-725), so `C83` supports a node carrying the
   inductor's *triangular ripple*, not a switching edge.  5.1 mm of 0.8–1.0 mm
   B.Cu 0.2104 mm over the In4 GND plane is about **1.8 nH**, against roughly
   0.7 nH of ESL inside the 0805 itself; at `V/L` = 3.3 V / 1.0 µH = 3.3 A/µs
   that is **6 mV on a 3.3 V rail**.  Moving it 2 mm closer buys about 2 mV.
   The high-dI/dt loop is the OUTPUT one and `C65.1` is already **1.82 mm**
   from `U21.6`.  Written into `.kicad_dru` section 5c.

3. **ITEM 3's PROSE WAS STILL STALE IN THE TOOL.**  The `.kicad_dru` was
   rewritten; `audit_rail_ampacity.py`'s `accept_reason` still said *"0.15 mm
   from solid GND and +3V3 planes on both faces"*, a stackup this board does
   not have.  It is now the **1.45 K** the tool derives from the board's own
   0.4000 mm core and 0.2028 mm prepreg.

4. **ITEM 11's NEW CLAUSES PASSED VACUOUSLY.**  They were written against
   defects that no longer exist in the package, so every one of them returned
   an empty list — the shape a broken check also has.  `FAB5` now mutates one
   row of the real `pos-fitted` file four ways and `FAB12` **puts the `J5`
   defect back** three ways.  Seven controls, all refused.  This also settles
   the independently-pushed `cto/d750-semantic-gates` branch (`e89aa36`): its
   18 pinned identities are a strict subset of `FAB12b`'s 41, field for field;
   its contribution — live controls inside the gate — is taken, and nothing is
   cherry-picked.

5. **ITEM 12's THREE `||` REPAIRS HAD NO TEST, AND ONE WAS INCOMPLETE.**  A
   recording bus that always ACKs cannot tell an independent sequence from a
   short-circuiting one — which is why the bug survived.  `RecordingBus` takes
   a selective NACK and still logs the refused transaction.  ***Writing that
   test found the rest of the bug***: `writeOutputs` only moves the shadow when
   the bus ACKs, so a NACKed load-switch write left `ACC_5V_SW_EN` HIGH in the
   shadow and the following unconditional boost-disable **re-sent it** — one
   NACK would have left the accessory load switch commanded ON during exactly
   the fault the shutdown was called for.  `Pcal9535a::clearBits` takes both
   bits down in one transaction.  Nine mechanised controls, nine caught.

**AND ONE GATE COULD NOT EXPRESS THE TRANSACTION AT ALL.**
`placement_contract.py` knew `--remove` (D-712) and had no opposite, so fitting
`C83`, `C84` and `Q11` made `PL1` and `PL2` fail however correct the placement
was.  `--add` exists; `PL7` now holds an ADDED pad to the same foreign-copper
clearance a MOVED one gets; and `PL6`, the vacuity screen, was found to be
vacuous itself and must now name its decoy.

**The `AO3400A` was also the only one of 122 assembly BOM lines with no
distributor identity**, and item 7 had just made it a two-piece line.  LCSC
`C20917`, JLCPCB BASIC, verified live per D-096.  122 of 122.
