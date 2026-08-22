# INDEPENDENT REVIEW — ADVISORY, NOT AUTOMATICALLY AUTHORITATIVE

**Reference:** FBV2-CTO2-PWRNFC-001 — "AQROOT Full Beta v2 Countersign"
**Date archived:** 2026-08-22
**Task:** FBV2-ARCH-002
**Source artifact:** <https://claude.ai/code/artifact/2367caef-2bca-4962-ae39-cd6aebd32163>

---

## Status of this document

This is an **independent second opinion supplied by the CTO**. It is archived here
in full because the engineering record must preserve dissent, not only agreement.

**It is advisory. It is not automatically authoritative.**

- Where this review conflicts with [`../CTO_DECISIONS.md`](../CTO_DECISIONS.md),
  **the CTO decision wins.**
- Where it conflicts with a primary-source verification recorded in
  [`../audits/`](../audits/), the primary source wins.
- Its own closing appendix lists seven claims it could **not** verify from a
  primary source. Those are marked in the text and must not be treated as
  established fact.
- Nothing in this review has been edited, softened, or corrected. Points where
  the primary engineering team disagrees, or where subsequent verification
  reached a different answer, are recorded in
  [`../audits/2026-08-22-architecture-reconciliation.md`](../audits/2026-08-22-architecture-reconciliation.md),
  **not** by altering the text below.

### Reproduction note

The artifact is an HTML page. The text below is a faithful plain-text extraction
of that page's rendered content — every heading, table row, verdict, quotation
and caveat is preserved in document order. Table cells appear as `|`-separated
runs because the source markup was tabular. **The canonical original remains the
artifact at the URL above**; this file exists so the review survives in Git
history independently of that service.

---

AQROOT Full Beta v2 Countersign
 - 
 - 
 - 

 FBV2-CTO2-PWRNFC-001
 Independent second-opinion review
 Advisory only · no repository changes made

# AQROOT Full Beta v2 Countersign

 Five architecture questions, reviewed against current manufacturer documentation rather than against the primary team's conclusions. Three of the five proposals survive with conditions. One contains a part-number choice that would silently break charging. One rests on a premise about a load switch that is correct, and a replacement part that is wrong for a user-accessible pin.

 Product ESP32-S3-WROOM-1-N16R8 handheld, 1S Li-ion
 Constraint Lean Beta-DM bring-up may be skipped
 Posture conservative against self-damage

 Q1 · Reverse batteryAmendedTopology A, but -1 only, plus a fuse and clamp the proposal omits.

 Q2 · NFC supplyN1, conditionalShip 3.3 V. Not the free deletion it is being sold as.

 Q3 · Accessory switchReframedTPS22950C — and the unswitched 3V3 pin is the real hole.

 Q4 · Pin remapPass w/ conditionsLegal, but avoidable. One premise is a myth.

 Q5 · BQ25185 STATConfirmedYour reading is right. Expose both — change the expander.

 Verdicts

 - Q1 · Reverse polarity

 - Q2 · ST25R3916 supply

 - Q3 · Accessory power

 - Q4 · GPIO remap

 - Q5 · BQ25185 status

 Findings

 - Disagreements: engineer

 - Disagreements: CTO proposal

 - Unlisted damage paths

 - Lock / open / reject

 - Next step

 - Unverified claims

## Question 01Reverse-polarity protection on a bidirectional battery node

 One recommended topology, with the exact gate-control mechanism for every required state — and two additions the proposal does not contain.

 VerdictTopology A, amended — LTC4368-1 only, VIN on the cell side, plus a series fuse and a clamp diode.
 The proposal as written does not meet its own stated requirement that “failure mode must not place negative battery voltage onto BQ25185 BAT.”

### First: the fault is real and a keyed connector does not fix it

 Worth stating plainly, because it justifies the whole exercise. The BQ25185 has no reverse-polarity provision on BAT. Its absolute-maximum table gives IN a −0.3 V to +25 V window and lumps every other pin — SYS, BAT, STAT1, STAT2, CE, TS/MR, ISET, ILIM/VSET — into −0.3 V to +5.5 V. A reversed 3.0–4.35 V cell puts roughly −3.0 to −4.35 V on BAT: a DC violation by a factor of ten to fourteen, not a transient margin call. The internal BATFET (115 mΩ) is on the wrong side of that violation and does not help.

 And the usual mechanical answer fails here. Two-pin JST-PH pigtail cells ship with both polarity conventions in the market — the connector keys the housing, not the wiring. A keyed connector protects against a user rotating a plug; it does not protect against a cell vendor crimping to the other convention. Electrical protection is mandatory, and you are right to treat it that way.

### Why option B — “discrete back-to-back N-FETs” — is not merely under-specified

 It is not implementable at 1S without a charge pump, and the obvious workaround is worse than no protection at all. Two mechanisms, stated exactly:

 - N-channel, common source. The shared source node sits at the battery potential, 3.0–4.2 V. The highest rail available to drive the gates is SYS at ~4.5 V. Available VGS is therefore 0.3 V to 1.5 V — below the threshold of every dual N-FET that meets a <30 mΩ target, and far below the 4.5 V at which their RDS(on) is specified. There is no rail on this board that turns those FETs on. A charge pump is not an optimisation here; it is the circuit.

 - P-channel, gates pulled to GND — the seductive low-IQ version. Trace it in the fault state. Cell reversed, BAT = −3.7 V, USB present, SYS = 4.5 V. The common source node charges through the SYS-side body diode to ~3.8 V. Gates are at 0 V, so VGS ≈ −3.8 V — both P-FETs turn hard on and connect SYS directly to a reversed cell. The circuit does not merely fail to protect; it actively creates the short it was added to prevent.

 Making the P-channel version safe requires an active element that pulls the gate up to its source the instant the battery node goes negative — which is precisely the block the LTC4368 integrates and documents. Doing it discretely is six to ten parts of unverifiable analogue behaviour on a board you may never bring up incrementally. Reject B.

### The IQ argument is quantitatively weak

 The case for a discrete solution rests on standby current. Put a number on the thing being optimised:

 Sleep-current budget, order of magnitude
 Block | Typ. sleep I | Source | 

 BQ25185, battery-only mode | 4 µA | Datasheet feature bullet | 

 TPS63020, operating IQ | 25 µA | TI product page | 

 MAX17048 hibernate | ~3 µA | Maxim/ADI | 

 2 × TCA9535 standby | 0.8–17 µA | 0.4–8.7 µA each | 

 ESP32-S3 deep sleep | 7–10 µA | Espressif | 

 Subtotal before protection | ~40–60 µA | — | 

 + LTC4368 operating | 80 µA | ADI product page (EC spread 30–100 µA) | 

 The controller roughly doubles a small number. On a 1500 mAh cell, ~140 µA total is still on the order of a year of shelf life. Trading that for an analogue circuit nobody has validated, on a programme that is considering skipping a bring-up board, is the wrong direction of risk. And the LTC4368's SHDN pin buys a genuine 5 µA hard-off ship mode — a feature you currently do not have.

### The recommended topology, stated exactly

 Lock this configuration

 - Controller: LTC4368-1, MSOP-10 (LTC4368IMS-1#PBF). Production, hand-solderable, 2.5 V to 60 V operating, −40 V protection.

 - Pass element: one independent-dual N-FET wired common source — FDS6898A (SOIC-8, 20 V, 9.4 A, 18 mΩ max at VGS = 2.5 V, VGS(th) 0.5–1.5 V, Rev. 4 Sept 2024).

 - Orientation: VIN = cell side, VOUT/SENSE = SYS / BQ25185 BAT side. This is not arbitrary — see below.

 - Sense resistor: 15–20 mΩ, trip at ±50 mV → ±2.5–3.3 A.

 - RETRY pin: strapped for latch-off, not auto-retry. A reversed cell should stop the board, not chatter at it.

#### Why -1 and not -2 — this is a real bug, not a preference

 The brief lists “LTC4368-1 or LTC4368-2” as if interchangeable. They differ in exactly one parameter, and it is the one that matters for a bidirectional node:

 Part | Forward OC trip | Reverse OC trip | Behaviour on a battery node | 

 LTC4368-1 | +50 mV | −50 mV | Symmetric circuit breaker — passes charge and discharge | 

 LTC4368-2 | +50 mV | −3 mV | Ideal-diode behaviour — opens as soon as charge current flows into the cell | 

 Fit a -2 and the board discharges normally and never charges. That is a week of debugging on a prototype and an easy substitution error at the distributor. Put the suffix in the schematic symbol, the BOM, the assembly note and the bring-up checklist.

#### Why VIN must be the cell side

 ADI documents the negative-supply behaviour on the VIN pin specifically:

 “When VIN goes negative, the reverse VIN comparator closes the internal switch, which in turn connects the gates of the external MOSFETs to the negative VIN voltage… Since the gate voltage of M2 is shorted to VIN, M2 will be turned off and no current can flow from VOUT to VIN.”LTC4368 datasheet, Rev. C (04/21)

 Wire it the other way round — VIN on SYS — and that documented DC blocking mechanism never engages. You fall back on the microsecond overcurrent trip, which is a race rather than a state. The orientation is part of the answer, not an implementation detail.

#### Two additions the proposal is missing

 The requirement is not met as proposed

 Your own requirement reads: “failure mode must not place negative battery voltage onto BQ25185 BAT.” The dominant MOSFET failure mode is drain-source short. A shorted pass FET defeats the LTC4368 entirely and puts the reversed cell straight onto BAT. A protection scheme whose single-point failure reproduces the exact fault it guards is not defence in depth.

 Add, at the cell connector: a 3 A fast-acting fuse in series, and a Schottky clamp (cathode to the BAT net, anode to GND). With a reversed cell and a shorted FET, the clamp holds BAT at roughly −0.35 V while the fuse opens — a brief marginal excursion instead of a sustained −3.7 V one. Two parts, about ten cents, and it converts a board-killer into a serviceable event.

 New risk: the series FETs will brick a deeply discharged pack

 LTC4368 UVLO rises at 1.8–2.4 V and it operates from 2.5 V. Below that, both gates are off and both body diodes are anti-series — nothing can flow in either direction. So: a cell that has over-discharged, or a protected pack whose internal protector has tripped open and reads 0 V at the terminals, can never be recharged by this board. The user experience is “my AQROOT killed the battery.” This is, in my judgement, the most likely field failure in the entire Q1 proposal, and it is a direct consequence of adding the protection.

 Fix: a firmware-gated recovery trickle — 10 kΩ in series with a small FET, from the protected BAT net across to the cell-side net, default off. ~450 µA is enough to lift VIN over UVLO and hand control back to the LTC4368; into a reversed cell it is harmless. Pair it with a BAT_RAW divider to an ESP32 ADC (≥100 kΩ series plus a Schottky clamp to GND, so a negative node clamps at −0.3 V at microamps) so firmware can distinguish no cell / dead cell / reversed cell before it does anything.

 Option C: was there a simpler modern part? No — and here is the sweep

 Roughly 25 candidates were checked against four simultaneous constraints: operates at 3.0 V, blocks bidirectionally, handles 1–3 A, and comes in a package a prototype shop can solder. Every one fails at least one.

 Candidate | Disqualifier | 

 LTC4359 | 4 V minimum; single FET; unidirectional ideal diode | 

 LM74700-Q1 | 3.9 V startup threshold; single FET | 

 LM74722-Q1 | Drives back-to-back FETs at 3 V / 35 µA — but diode-mode only, and WSON-12 | 

 LM66200 | OR-ing dual ideal diode; cannot pass reverse charge current | 

 TPS2660x / TPS1663 | 4.2 V and 4.5 V minimum VIN | 

 TPS25947 | 2.7 V and true RCB — but 428–610 µA IQ and QFN-10, 0.45 mm pitch | 

 TPS22916 | Always-on RCB at 0.5 µA — but 2 A max and WCSP 0.78 mm | 

 MAX17608/12/14 | 4.5 V minimum VIN | 

 MAX40200 | 7 µA, SOT-23-5 — but 1 A max, and it is a diode, not a controller | 

 1S protector + low-side dual FET
S-8261 / BQ2970 + FS8205-class | Does not solve this problem at all. The FET pair sits in the battery return; BAT+ reaches the charger with no series element. Reversed insertion still puts −3.7 V on BQ25185 BAT and also violates the protector's own −0.3 V VDD limit. These parts are designed to live inside a pack where orientation is fixed at manufacture. | 

 Note also: AO8810 and Si6968BEDQ appear in reverse-protection reference material but are common-drain duals. The LTC4368 has a single GATE pin and needs a common-source pair. Specifying either of those against this controller produces a circuit that will not enhance. FDS6898A is an independent dual and can be wired either way.

#### Cost of the recommendation, stated honestly

 15 mΩ sense + 2 × 18 mΩ RDS(on) ≈ 51 mΩ in series with the cell — about 153 mV and 460 mW at a 3 A transient. That is acceptable for the current, but it lands on the fuel gauge: see risk 2 below.

## Question 02ST25R3916 at 3.3 V or 5 V

 Ship N1 — but not for the reason it is being argued, and not as a free deletion.

 VerdictN1 — run VDD, VDD_TX and VDD_IO from +3V3, configure sup3V, delete the TPS61023.
 Conditional on four changes that are not in the proposal, and on keeping the boost footprint unpopulated rather than deleting it from the layout.

### What the documentation actually supports

 The premises in the brief check out. VDD and VDD_TX must share a supply — AN5309 and ST's own moderators state it flatly. VDD_IO is independent, 1.65–5.5 V. sup3V is IO_CONF2 (register 0x01), bit 7; ST's own RFAL sets it automatically by measuring VDD against a 3600 mV threshold, and re-bases the internal regulator ladder from a 3.6 V floor to a 2.4 V floor in 100 mV steps. ST has twice published instructions for running its own evaluation boards entirely at 3.3 V with stock firmware. So N1 is a supported mode, not a hack.

 One correction to the framing: the supported supply is two bands, not a continuum — roughly 2.4–3.6 V and 3.6–5.5 V (an ST moderator puts the upper band's floor at 4.1 V and says intermediate voltages have no working regulator setting). A 3.3 V rail at +10% is 3.63 V, sitting on the seam. Specify the TPS63020 output tightly and do not let anyone “helpfully” raise it.

### What N1 actually costs

 ST is unambiguous and it is not in the brief:

 “Putting VDD=VDD_TX=3V3 will reduce the achievable output power.”ST moderator, ST community — ST25R3916B power supply configuration

 ST publishes no A/m figure at either supply, so here is the arithmetic from ST's own measured regulator data (AN5584): at VDD = 4.98 V the driver supply VDD_RF measures 4.59–4.76 V. Scale the same dropout to a 3.3 V rail and the driver runs at roughly 2.9–3.1 V. Driver segment resistance (2 Ω all-on) is supply-independent, so into an unchanged match:

 Quantity | 5 V mode | 3.3 V mode | Ratio | 

 Driver supply VDD_RF | ~4.6–4.8 V | ~2.9–3.1 V | 0.64× | 

 Antenna current / H-field | reference | — | ~0.64× | 

 Radiated power | reference | — | ~0.41× (−3.8 dB) | 

 Practical read range, coupled loop | reference | — | ~0.7–0.8× | 

 Derived from ST's measured VDD_RF values, not an ST characterisation. Treat as a planning estimate, not a spec.

 For calibration: a third-party 5 V ST25R3916 module reports ~65 mm on NTAG213/216 and ~28 mm on DESFire. Scaled, N1 lands near 45–52 mm and ~20–23 mm. For “tag detect, read, write, normal handheld range” that is a convincing demo. For EMVCo it would not be — and you have explicitly said you do not need that.

### Why I still choose N1 — the argument the brief does not make

 The strongest case for N1 is not BOM or area. It is that N1 removes every voltage above 3.6 V from the board. On a programme that may skip Lean Beta-DM bring-up, a board where no net can exceed the logic domain is categorically safer than one where a 5 V rail sits adjacent to 3.3 V logic. Three specific consequences:

 - The sequencing question disappears. With VDD_IO = VDD there is no VDD_IO-present-while-VDD-absent case and no ESD-diode back-powering path to reason about. This matters more than usual because — see the unverified list — the ST25R3916 absolute-maximum table and any VDD_IO/VDD relationship could not be retrieved with the tooling available. N1 makes that unretrieved page irrelevant. N2 makes it a gating item.

 - A 1 MHz switcher leaves the neighbourhood of a 13.56 MHz receiver. EMD (external modulation disturbance) is what actually limits reliable ISO14443-4 write operations, and a boost converter centimetres from the antenna front-end is a first-order contributor. This partly offsets the lost drive.

 - Battery current. A 5 V / 300 mA transmit burst drawn through a boost from a 3.0 V cell is ~550–600 mA at the cell, right where the cell's impedance is worst.

 To the primary engineer's credit, the TPS61023 “true load disconnect” claim is correct — the datasheet states “true disconnection between input and output during shutdown.” So N2 is not broken. It is simply carrying a 5 V domain, a switcher and a sequencing question for about 3.8 dB you do not need.

### Conditions on N1 — the work that replaces the deleted parts

 Not optional

 - Do not tap VDD/VDD_TX straight off the 3V3 plane. Feed through a ferrite or 0 Ω with ≥47 µF local bulk plus 4.7 µF / 100 nF / 10 nF. Transmit bursts of 100–250 mA with microsecond edges will otherwise modulate the rail feeding the ESP32-S3, the display and the MAX98357A. This is N1's single biggest risk and it is a decoupling and layout problem, not a topology problem.

 - Re-scale the RFI receiver divider. AN5592 targets ~2.7 V at RFI with a 5 V driver. With ~0.64× the transmit amplitude, copying a 5 V reference divider leaves the receiver under-driven. This is the most commonly missed consequence of dropping the supply.

 - Re-tune the match on the real antenna and re-pick the driver resistance (register 0x28) and regulator target. Target impedance (20 Ω differential / 10 Ω single-ended) does not change with supply; the operating point does.

 - Keep the TPS61023 footprint on the PCB, unpopulated. You are proposing to skip the intermediate bring-up board. Deleting the option outright means a range shortfall costs a respin rather than a stuff change.

 Open product decision: ST25R3916 or ST25R3916B

 These are not equivalent, and the choice interacts with N1.

 - ST25R3916B adds Active Wave Shaping, finer TX driver resistance stepping and increased AM modulation depth range — all of which help recover margin at a lower supply.

 - ST25R3916B removes capacitive sensing on CSI/CSO. Capacitive low-power tag detect — noticing a hand approaching before any field is emitted — is a genuinely good showcase behaviour, and only the non-B part has it.

 - Both are ACTIVE (the -AQWT order codes are NRND on both; use -AQET or -BWLT). ST does not mark the non-B as superseded.

 - If you take the B and enable AWS, the VDD_AM capacitor rule changes: 10–50 nF, not 2.2 µF. That is a hardware decision made at schematic time, not a firmware option.

 My inclination is the B with inductive amplitude/phase wake-up, trading the capacitive party trick for waveform quality you will want at 3.3 V — but this is a product call, not an engineering one, and it belongs to you.

## Question 03Switched 3.3 V for third-party accessories

 The part choice is clear. The question is aimed at the wrong pin.

 VerdictTPS22950C for the switched pin — and reject the connector power plan as drawn.
 None of the three candidates named in the brief is the right answer, and the unprotected permanent 3.3 V pin defeats whatever you fit on the switched one.

### The TPS22918 rejection is correct — the datasheet says so itself

 “A CL greater than CIN can cause VOUT to exceed VIN when the system supply is removed. This could result in current flow through the body diode from VOUT to VIN.”TPS22918 datasheet, Application Information

 Confirmed. It also has no current limit, no thermal shutdown, and no internal pull-down on ON — the pin description literally reads “Do not leave floating.” Three independent reasons it does not belong on a user-accessible pin.

### Head-to-head

 Candidates against the stated requirements
 Part | RCB off / on | Current limit | SC + thermal | Default OFF | Package | IQ on / off | Fit | 

 TPS22917 | yes / yes | none | none | 750 kΩ internal | SOT-23-6 | 0.5 µA / 10 nA | 
 No | 

 TPS22913B/C | yes / yes | none | none | not stated | DSBGA 0.9×0.9 only | 2–7 µA / 0.1 µA | 
 No | 

 TPS22950 / 950C | yes / yes | 0.05–3.5 A adj. | yes, 170 °C | 500 kΩ internal | SOT-23-THIN (DDC) | 40 µA / 0.2 µA | 
 Yes | 

 TPS22950L | no / no | latch-off | yes | 500 kΩ | SOT-23-THIN | 40 µA / 0.2 µA | 
 Trap — do not order | 

 TPS25221 | claimed, undocumented | 0.275–2.7 A adj. | 1.5 µs, dual TSD | no internal PD | SOT-23-6 | 75–90 µA / 0.5 µA | 
 Backup only | 

 TPS2553 | no | adjustable | yes | no internal PD | SOT-23-6 | 130 µA / 1 µA | 
 No — see below | 

### Reasoning, and where I disagree with the shortlist

 - TPS22917 is the wrong instinct. It was presumably shortlisted for its 0.5 µA IQ. But this pin is off whenever no accessory is attached, and when it is on, an accessory drawing tens of milliamps makes 40 µA irrelevant. Optimising IQ here and giving up current limiting means an accessory that shorts 3.3 V to ground pulls whatever the TPS63020's 2 A limit will deliver until something in the chain gives up. That is the exact self-damage case this connector exists to survive.

 - TPS22913B/C fails on packaging alone — DSBGA 0.9 × 0.9 mm is not a prototype part, and it also has no current limit.

 - TPS22950 is the only device in the sweep that satisfies every stated requirement simultaneously. 1.8–5.5 V, 41 mΩ, reverse blocking both enabled and disabled, one-resistor adjustable current limit, short-circuit and thermal protection with auto-retry, internal 500 kΩ pull-down so the pin is genuinely OFF with an un-driven net, in a leaded SOT-23-THIN.

 - Order the C variant — that is what is actually stocked in the leaded package (3.2 A, ILIM 0.5–3.5 A). Set ILIM around 600–800 mA for a “several hundred mA” accessory budget.

 - TPS2553 must not be substituted. Its “reverse” feature is a 95–190 mV comparator with a 4 ms deglitch, and TI's own applications engineer states on E2E that in an equal-voltage back-feed “there will never be voltage difference between VIN and VOUT, so the device won't turn off the MOSFET.” It does not block a back-powering accessory.

#### Honest caveats on the recommendation

 The TPS22950's reverse blocking is a comparator that opens the pass FET (~44 mV / ~900 mA, 3 µs response), not a back-to-back blocking pair. A back-powering accessory can push a few hundred milliamps for a few microseconds before it acts. Reverse leakage while off is specified at 38 µA, far leakier than TPS22917's 300 nA. Neither is disqualifying here; both should be known and neither is in the brief.

### The bigger hole: the permanent 3.3 V pin

 Reject as drawn

 The 20-pin allocation exposes permanent 3.3 V alongside the switched rail. That pin is a direct, unprotected, always-live tap from a user-accessible connector onto the system rail — no current limit, no reverse blocking, no fuse. A third-party accessory that shorts it, or back-feeds it from its own supply, takes down the whole board regardless of what is fitted on the switched pin. Protecting one of two power pins is not protection.

 Pick one: (a) delete the permanent pin and make both rails switched — a second TPS22950 with ILIM ≈ 200–300 mA, enabled early in boot, gives accessories an “always on” rail that is still protected; or (b) keep it behind a PTC plus a TVS and accept a slower, cruder response. Option (a) is barely more expensive and is the one I would sign.

 Whatever you choose, both power pins want a TVS at the connector, and the switch's 5.5–6 V absolute maximum should be documented: an accessory applying 5 V survives; one applying 12 V does not.

## Question 0420-pin connector GPIO remap

 Electrically legal. One premise is a widely believed myth. And the whole remap is avoidable.

 VerdictPASS WITH CONDITIONS
 Six conditions, one correction, and a better pin plan that touches no strapping pin and needs no SPI merge.

### GPIO47 on N16R8 — safe

 Confirmed. GPIO47 is module pin 24, type I/O/T, alternate functions SPICLK_P_DIFF / SUBSPICLK_P_DIFF which WROOM-1 does not use. The one published restriction does not apply here — the module datasheet's 1.8 V caveat on GPIO47/48 is specific to modules embedding ESP32-S3R16V. N16R8 embeds ESP32-S3R8, so GPIO47 is a normal 3.3 V I/O. The GPIO48 RGB LED is a DevKitC board part, not a module part. Pass.

### GPIO46 — the premise needs correcting in both directions

 Correction

 GPIO46 is not input-only on ESP32-S3. That belief is true of ESP32-S2 and it migrates constantly. On S3 it is type I/O/T in the module datasheet, and ESP-IDF's own SoC capability header settles it: SOC_GPIO_VALID_OUTPUT_GPIO_MASK is defined equal to SOC_GPIO_VALID_GPIO_MASK with the comment // No GPIO is input only. On S2 the same header explicitly masks BIT46 out. Put this note in the schematic so nobody “fixes” it later.

 So DISP_BL_CTL on GPIO46 is legal, and its reset state helps you: GPIO46 comes up WPD, IE — weak pull-down, input enabled — so it is naturally low through strap sampling. The proposal's dedicated external pull-down is right. It is also incomplete.

#### Conditions

 - 10 kΩ external pull-down. Espressif's internal pull is ~45 kΩ and their own guidance for strap-class pins is a strong external pull.

 - No pull-up anywhere on that net — including inside the backlight driver. This is the condition the proposal misses. Many LED boost drivers and PMOS-gate arrangements have an internal pull-up or require one on EN. A 100 kΩ internal pull-up inside the driver fighting your 10 kΩ still leaves ~300 mV, which is fine — a 10 kΩ one is not. If the backlight enable is active-low or internally pulled up, GPIO46 is disqualified and the remap fails. Check the actual driver before locking.

 - No RC filter and no bulk capacitance on GPIO46. Espressif publishes no numeric capacitance limit for strapping pins — only the qualitative “do not add high-value capacitors.” Keep the node to pad and trace; if the backlight needs soft-start, put it after a buffer.

 - Strap hold is 3 ms minimum after CHIP_PU rises (tH, datasheet Table 3-2). The pull-down must be effective from the moment 3V3 is valid, and nothing may source into the net during that window.

 - GPIO46 is not an RTC GPIO — no RTC hold, no level retention through deep sleep. The backlight always reverts to the pull-down state on sleep entry. Fine for a backlight; document it.

 - Free verification, put it on the bring-up sheet: the ROM boot log prints boot:0xNN where bit 0x04 is the latched GPIO46 level and 0x08 is GPIO0. “boot value shows GPIO46 = 0” is a one-line pass/fail on every unit.

 Agreed on keeping NFC_IRQ off GPIO46 — a latched-high interrupt on a boot strap is exactly the failure that blocks Joint Download Boot. Correct call.

### Where I disagree: GPIO43 / U0TXD on a user connector

 Self-damage path, both directions

 The module actively drives GPIO43 as UART0 TX at 115200 on every single reset, and at high rate throughout any UART flash. NATIVE_A is specified as a bidirectional FAST_IO. A third-party accessory that drives that pin during boot is in push-pull contention with the module's output driver — every boot, forever. “Documented accordingly” does not stop an accessory from driving a pin it was told it could drive. Minimum condition: 220–330 Ω in series at the connector on both native pins. Better: do not use GPIO43.

### A better pin plan — no SPI merge required

 You asked for one. On N16R8 the user-available set is GPIO0–21 and GPIO38–48. GPIO22–25 do not exist; GPIO26–34 are not bonded out; GPIO35/36/37 are bonded to module pins 28/29/30 but are wired to the octal PSRAM — live pads that are electrically dead, which is a trap worth marking DNU on the symbol. GPIO39–42 are the pin-JTAG group, but JTAG source selection via GPIO3 only takes effect once EFUSE_STRAP_JTAG_SEL is burned; from the factory, JTAG comes from USB-Serial-JTAG and GPIO39–42 are ordinary I/O.

 That leaves cleaner candidates than GPIO43:

 Pin | Strapping | Power-up glitch | Boot traffic | RTC / deep-sleep wake | Suitability | 

 GPIO38 | no | none published | none | no | Preferred NATIVE_A | 

 GPIO48 | no | none published | none | no | Preferred NATIVE_B | 

 GPIO47 | no | none published | none | no | Good | 

 GPIO21 | no | none published | none | yes | Best WAKE/ATTN candidate | 

 GPIO15, 16 | no | none published | none | yes | WAKE/ATTN alternates | 

 GPIO43 | no | none published | ROM UART TX, every reset | no | Only with series R | 

 GPIO46 | yes — boot mode | none published | none | no | Internal use only | 

 GPIO19, 20 | no | 60 µs ×2; 3.2 ms / 2 ms total | USB | yes | Reserve for USB recovery | 

 If GPIO38, GPIO48 and GPIO21 are not already committed elsewhere in the pin map, take them. NATIVE_A = GPIO38, NATIVE_B = GPIO48 or 47, WAKE/ATTN = GPIO21, debug UART stays on GPIO43/44 as internal test pads. That removes the strapping-pin dependency, the ROM-chatter dependency and the entire GPIO46 debate in a single move, without merging the two SPI buses. I cannot confirm those three are free — I do not have the full pin map — so this is offered as the preferred option conditional on availability, and the GPIO46 route as the fallback with the six conditions above.

 Hazard the checklist misses: WAKE/ATTN must live in GPIO0–21

 Only GPIO0–21 are RTC GPIOs on ESP32-S3, and only RTC GPIOs can wake from deep sleep (ext0, ext1, and deep-sleep GPIO wake all list “ESP32-S3: 0-21”). If WAKE/ATTN from the expanders lands anywhere in GPIO38–48, deep-sleep wake-on-accessory silently does not work and the failure shows up as “the handheld never wakes,” not as a schematic error. Avoid GPIO1–14 and 17–20 for this net as well — they carry published 60 µs power-up glitches, and GPIO19/20 additionally carry 3.2 ms and 2 ms glitch-plus-delay windows.

#### Recovery hazards — none created, one to avoid creating

 - USB-Serial-JTAG on GPIO19/20 is the recovery path of record and is fully independent of GPIO43/44. Keep the USB-C data pair on it.

 - Erratum USBOTG-4289: on silicon before date code 2219, USB-OTG download is permanently disabled by eFuse. Espressif's own workaround is “download through USB-Serial-JTAG.” Do not architect recovery around USB-OTG.

 - Do not burn USB_PHY_SEL. Routing USB-OTG to the internal PHY is permanent and removes USB-Serial-JTAG. That is an irreversible bricking decision hiding inside a firmware config option — put it on the do-not-do list.

 - Keep GPIO0 off the connector and keep its own pull-up.

 - No PSRAM hazard is created by GPIO46 or GPIO47. Mark GPIO35/36/37 DNU.

## Question 05BQ25185 status pins

 Your reading of the current documentation is correct. The previous engineer's is not. But the fix is not a pin count.

 VerdictExpose STAT1 and STAT2 — and replace the TCA9535 with a maskable expander.
 STAT1 alone cannot tell charging from charge-complete. The wake-loop is real, but it is an expander defect, not a status-pin defect.

### Verification

 Datasheet SLUSF65A (Oct 2023, revised Jan 2026), §7.3.10, verbatim:

 “When no battery is present, the device charges the capacitor on the BAT pin and toggles between charging and charge completed states.”BQ25185 datasheet SLUSF65A, §7.3.10 Status Pins

 Table 7-2 has exactly four rows:

 Table 7-2 — Status Pins State Table
 Charging state | STAT1 | STAT2 | 

 Charge completed, charger in sleep mode, or charge disabled | HIGH | HIGH | 

 Normal charging in progress (including automatic recharge) | HIGH | LOW | 

 Recoverable fault (VIN_OVP, TS HOT, TS COLD, TSHUT, system short) | LOW | HIGH | 

 Non-recoverable / latch-off fault (ILIM or ISET pin short, BATOCP, safety timer) | LOW | LOW | 

 The no-battery limit cycle oscillates between rows 1 and 2. In both, STAT1 is HIGH. Therefore STAT1 is static and STAT2 toggles — the current TI reading is confirmed and the previous engineer's belief (that STAT2 toggles at charge-complete/sleep) is wrong: charge-complete, sleep and charge-disabled are one state with both pins HIGH. TI applications confirms the mechanism explicitly on E2E: “the capacitor on the BAT pin charges and discharges around the battery regulation voltage. This causes STAT2 to blink as the charger toggles between reporting ‘charging’ and ‘charge complete.’”

#### One nuance that matters more than the correction

 There is no battery-absent detector in this device. What you are seeing is the ordinary terminate-and-recharge limit cycle (termination at 10% of ICHG, restart after VRCH = 100 mV of droop) acting on a capacitor instead of a cell. So it fires in any condition where BAT is capacitive: no battery, a pack whose internal protector has tripped open, a cell disconnected at the connector with USB in — and, relevantly to Q1, whenever your new series protection FETs are open. TI publishes no frequency for it, because it has none: the rate is set by CBAT, ICHG and the leakage on the down-slope. It could be a few hertz or a few hundred. Measure it; do not assume “an LED blinks slowly.”

 There is also no supported way to disable it. The only levers are side effects: hold CE high (no charging), leave ILIM/VSET open above 180 kΩ (no charging), or keep a non-CV loop dominant so termination is inhibited. None is a configuration you want to ship.

### Why STAT1-only is the wrong economy

 Look at the table again. STAT1 alone gives you fault / no fault and nothing else — it cannot separate charging from charge-complete, and it cannot separate a recoverable fault from a latch-off fault. The second bit is where nearly all the information is. Dropping it saves one expander input on a device that already has twenty of them. Expose both.

### The wake-loop is real — and it is the expander's fault

 Root cause

 Verified from the TCA9535 datasheet: the device has eight registers — Input Port 0/1, Output Port 0/1, Polarity Inversion 0/1, Configuration 0/1. There is no interrupt mask register. INT asserts on any rising or falling edge of any input and clears only when the port data reverts or the port is read. A pin toggling at tens or hundreds of hertz therefore produces an unmaskable, self-refreshing interrupt storm on the shared wake net, and there is no software mitigation that does not amount to polling.

 And STAT2 is not the only source. Ten of those inputs go to a user-accessible connector. Any accessory that chatters, floats, or is unplugged mid-transaction does exactly the same thing. Removing STAT2 treats one symptom of an architectural defect.

 The single highest-value change in this review

 Replace TCA9535 with NXP PCAL9535A. It is a stated pin-to-pin replacement for PCA9535 in TSSOP24, 1.65–5.5 V, 1.0 µA standby at 3.3 V, and its Agile I/O set is almost a list of this architecture's open problems:

 - Interrupt mask register (4Ah/4Bh) — mask STAT2, mask a chattering accessory pin, mask anything, per pin. Solves Q5 and the accessory-chatter case together.

 - Interrupt status register (4Ch/4Dh) — identify the source without reading both ports, which shortens every wake.

 - Input latch — a short pulse is captured instead of missed.

 - Programmable 100 kΩ pull-up/pull-down per pin — defines the state of ten user-accessible pins with nothing plugged in, and deletes roughly ten external resistors.

 - Programmable output drive strength — limits fault current into a shorted accessory pin.

 - Push-pull or open-drain per bank — lets the connector-facing bank be open-drain, which is the safer default for third-party hardware.

 - It powers up with all interrupts masked, which is the correct default for a user connector and the opposite of the TCA9535's behaviour.

 Cost: a different register map in firmware, and one careful footprint/pinout check. That is a small price for removing an entire class of unfixable-in-software failure.

#### Conditions either way

 - Pull STAT1/STAT2 up to 3V3 with 20 kΩ — the datasheet specifies a 1 kΩ–20 kΩ range and a 5 V maximum pull-up rail. Do not pull to anything higher.

 - Route them to expander inputs whose interrupts are masked by default and unmasked only while firmware is actively watching a charge cycle.

 - Do not use the STAT pins for USB-present detection. The BQ25185 has no power-good output and no “input present” row in the table. Use a protected VBUS divider. This is a gap in the current architecture, not a preference.

## Findings 01Where I disagree with the primary engineer

 - STAT2 does not toggle at charge-complete or in sleep. Those are one state with both pins HIGH. STAT2 toggles in the battery-absent limit cycle. The premise behind “STAT1 only” is factually wrong.

 - “STAT1 only” is also the wrong conclusion from a correct premise. STAT1 is HIGH in both charging and charge-complete; alone it conveys fault/no-fault and nothing more.

 - The discrete back-to-back N-FET recommendation is not under-specified — it is unrealisable at 1S. Available VGS from any rail on this board is 0.3–1.5 V. Without a charge pump there is no gate drive. The P-channel workaround that avoids the charge pump turns both FETs on into a reversed cell.

 - The TPS22918 rejection is right; the replacement reasoning is not. Selecting on IQ for a pin that is off when idle, and giving up current limit and thermal shutdown on a pin the public can short, inverts the priority.

## Findings 02Where I disagree with the primary CTO proposal

 - LTC4368-1 and -2 are presented as interchangeable candidates. They are not. The -2's −3 mV reverse threshold makes it an ideal diode; on a bidirectional battery node it blocks charging. This is a silent, expensive failure.

 - The proposal does not meet its own stated failure requirement. A shorted pass FET — the dominant MOSFET failure mode — places the reversed cell directly on BQ25185 BAT. A series fuse plus a Schottky clamp is required for the requirement as written to be true.

 - The proposal does not address the deep-discharge lockout the protection creates. Below LTC4368 UVLO, both directions are blocked and the pack cannot be revived. This is a new failure mode introduced by the fix.

 - N1 is framed as a simplification. It is a trade. ST states on the record that 3.3 V reduces achievable output power, and the change carries two non-obvious follow-ons — the RFI divider must be re-scaled, and the match and driver settings re-tuned. I still choose N1, but on the sequencing and EMI arguments rather than the BOM argument, and with the boost footprint retained unpopulated.

 - Q4's GPIO46 condition is correct but incomplete. A dedicated pull-down is necessary and not sufficient: it says nothing about pull-ups inside the backlight driver, node capacitance on a strapping pin, the 3 ms strap hold, or the fact that GPIO46 cannot hold state in deep sleep. And the remap is likely avoidable entirely.

 - GPIO43 is exposed to third-party hardware on a pin the module drives every boot. Documentation does not prevent contention; series resistance does.

 - TCA9535 is the wrong expander behind a user-accessible connector with a shared wake line. No interrupt mask means no software fix for any chattering input, of which STAT2 is only the first example found.

 - The 20-pin map spends three pins on GND and two on power but none on accessory detect. Firmware cannot know an accessory is present before it enables the switched rail or chooses pull configurations. Repurpose one XGPIO as ACC_DETECT (accessory straps it to GND); a PCAL9535A's programmable pull-up makes this free.

## Findings 03Self-damage paths not in the brief

 Ordered by how likely I think they are to bite a board that skips Lean Beta-DM bring-up.

 01

##### Deep-discharge lockout — the protection bricks the pack

 Covered in Q1. Series back-to-back FETs plus a controller with a 2.5 V floor means a pack at 0 V can never be recharged. Needs a firmware-gated trickle path and a raw-battery ADC sense to be recoverable.

 02

##### The protection degrades the fuel gauge, and MAX17048 cannot compensate

 The recommended Q1 chain adds ~51 mΩ between cell and system. The MAX17048 is a voltage-only ModelGauge device with no current sense, so it cannot correct for IR drop it does not know about. Put it on the protected side and a 1 A load shifts its reading by ~51 mV — several percent of state-of-charge. Put it on the cell side and it is exposed to the reversed-cell fault it was moved behind the FETs to avoid.

 My inclination is protected side plus minimised total series R and RCOMP tuning, but this is a genuine trade the brief has not made. Flagged as open.

 03

##### I²C on a community connector shares the bus with the fuel gauge and the expanders

 Two failure modes, both certain to occur eventually. Bus hang: an accessory that holds SDA low blinds the MAX17048 and all twenty XGPIO simultaneously — the handheld does not just lose the accessory, it loses its own battery telemetry and its own I/O. Address collision: nothing stops a third-party accessory squatting on 0x36 (MAX17048) or 0x20–0x27 (the expanders).

 Fix: put the accessory bus on its own segment behind a switchable buffer or mux (PCA9543A / TCA9548A class, or a buffer with an enable), so firmware can isolate on fault and the accessory address space is genuinely separate. This is close to mandatory for anything advertised as a community connector.

 04

##### Unprotected permanent 3.3 V pin

 Covered in Q3. Whatever is fitted on the switched pin is irrelevant while an always-live unprotected tap sits two pins away on the same connector.

 05

##### 3V3 rail budget under simultaneous worst case

 TPS63020 delivers 2 A. Under N1 the same rail must serve: MAX98357A peaks above 1 A into 4 Ω at full scale, ST25R3916 transmit bursts of 100–250 mA, the backlight at 60–120 mA, the 915 MHz LoRa TX burst, the 433 MHz transmitter, the SD card and the ESP32-S3's own Wi-Fi peaks. The sum of worst cases plausibly exceeds 2 A at VIN = 3.0 V, and the buck-boost's response is current-limit foldback — meaning brownout resets and SD corruption rather than a clean fault. Build the rail budget explicitly and, if it does not close, gate the radios and audio so they cannot transmit simultaneously.

 06

##### BQ25185 TS/MR is a factory-mode arming pin

 Easy to miss because it looks like a thermistor input. Holding TS/MR low with VIN present for tLPRESS arms factory mode; removing VIN then enters it, disconnecting the battery from SYS. The device looks dead. If that net is long, near a test point, near the connector, or if a pack NTC shorts, you get an unexplained brick. Use the 10 kΩ-to-GND defeat if no NTC is fitted, keep the net short and internal, and never expose it.

 07

##### ESD and EOS on twenty user-accessible pins

 Expander I/O, I²C, WAKE/ATTN and two native ESP32 pins all reach a connector the public plugs things into. Series resistance (100–330 Ω on signals) plus a low-capacitance TVS array is not optional on a board that may not get an incremental bring-up. Watch capacitance on the I²C lines when choosing the array.

 08

##### Irreversible eFuse decisions on the recovery path

 USB_PHY_SEL and DIS_USB_JTAG are permanent and each removes USB-Serial-JTAG, which — given erratum USBOTG-4289 on pre-2219 silicon — is the only reliable recovery path. Put both on an explicit do-not-burn list in the firmware repository, not just in someone's head.

 09

##### GPIO35/36/37 are live pads wired to PSRAM

 They appear on module pins 28/29/30 and will accept a net in the schematic without complaint. Mark them DNU on the symbol; this is a classic N16R8 respin.

 10

##### GPIO43 boot-time push-pull contention

 Covered in Q4. Series resistance at the connector, or a different pin.

## Findings 04Lock now / keep open / reject

 Lock = safe to draw today. Keep open = needs a measurement or a product decision first. Reject = do not draw.

 Decision register
 Status | Item | Note | 

 Lock now | LTC4368-1, MSOP-10, VIN on cell side, RETRY strapped to latch-off | Suffix and orientation both load-bearing | 

 Lock now | FDS6898A independent dual N-FET, wired common source; 15–20 mΩ sense | Not a common-drain dual | 

 Lock now | 3 A fuse + Schottky clamp at the cell connector | Makes the stated failure requirement true | 

 Lock now | TPS22950C (DDC SOT-23-THIN) on the switched accessory rail, ILIM 600–800 mA | Not the L variant | 

 Lock now | PCAL9535A in place of TCA9535 | Pin-to-pin in TSSOP24; adds interrupt mask | 

 Lock now | STAT1 and STAT2 exposed, 20 kΩ to 3V3, interrupts masked by default | Both bits or the table is unreadable | 

 Lock now | GPIO47 as a 3.3 V native expansion signal on N16R8 | Verified; 1.8 V caveat is R16V-only | 

 Lock now | GPIO35/36/37 marked DNU; GPIO0 kept off the connector with its pull-up | | 

 Lock now | USB-Serial-JTAG on GPIO19/20 as recovery; USB_PHY_SEL and DIS_USB_JTAG on a do-not-burn list | | 

 Lock now | Series R + low-capacitance TVS on all 20 connector pins; series R on any native pin exposed | | 

 Lock now | Protected VBUS divider for USB-present detection | BQ25185 has no power-good output | 

 Lock now | TS/MR treated as a factory-mode pin: short net, internal, never exposed | | 

 Keep open | N1 vs N2 — build N1, keep the TPS61023 footprint unpopulated | Decide after antenna range measurement | 

 Keep open | ST25R3916 vs ST25R3916B | Capacitive tag-detect vs AWS; product call. VDD_AM cap differs | 

 Keep open | NATIVE_A/B on GPIO38/48 vs GPIO43/47; DISP_BL_CTL staying put | Depends on the rest of the pin map | 

 Keep open | WAKE/ATTN pin — must be GPIO0–21; GPIO21/15/16 preferred | Confirm against current allocation | 

 Keep open | MAX17048 sense point: cell side vs protected side | ~51 mΩ of uncompensable IR drop | 

 Keep open | Accessory I²C segmentation — buffer vs mux | Bus-hang and address-collision both need it | 

 Keep open | Dead-cell recovery trickle implementation + BAT_RAW ADC sense | Required, mechanism not yet chosen | 

 Keep open | 3V3 rail current budget under simultaneous NFC TX + audio + LoRa + backlight | May force mutual-exclusion in firmware | 

 Keep open | ACC_DETECT pin repurposed from one XGPIO | Free with PCAL9535A pull-ups | 

 Reject | LTC4368-2 on this node | Blocks charge current | 

 Reject | Discrete back-to-back N-FET, and gate-to-GND P-FET, reverse protection at 1S | No gate drive; the P-FET version creates the fault | 

 Reject | 1S pack-protector + low-side dual FET as the reverse-insertion answer | FETs are in the return; BAT+ still reaches the charger | 

 Reject | TPS22918, TPS22917, TPS22913B/C, TPS22950L, TPS2553 on the user-accessible pin | No limit / no RCB / DSBGA, respectively | 

 Reject | Unprotected permanent 3.3 V pin on the community connector | Switch both rails, or PTC + TVS | 

 Reject | “STAT1 only” | Cannot distinguish charging from complete | 

 Reject | TCA9535 behind a user connector on a shared wake path | No interrupt mask register | 

 Reject | Bare GPIO43 to the connector without series isolation | ROM UART drives it every reset | 

 Reject | LTC4368 alone as the answer to “no negative voltage on BQ25185 BAT under failure” | Shorted FET reproduces the fault | 

## Findings 05The next step, before anyone opens the schematic

 Do this first

 Write the state table, then run two bench experiments. Do not select more parts.

 Everything above is derived from documents. Two of the decisions cannot be closed by any document, and one artefact does not exist yet.

### 1 · A signed power/fault state table — one page

 Enumerate every combination of USB in/out × battery {good, absent, deeply discharged, reversed} × ship mode {on, off} × accessory {none, attached, shorted, back-powering}. For each cell, write the required state of: LTC4368 gates, BQ25185 BAT and SYS, TPS63020, TPS22950, expander INT, and the ESP32-S3 boot straps. Any cell you cannot fill in from a sentence in a datasheet is a bring-up experiment, not a schematic decision. This is the artefact that would have caught the -1/-2 issue, the deep-discharge lockout and the STAT2 wake loop before any of them reached a net.

### 2 · Two protoboard experiments, roughly a day and under $100

 Because Lean Beta-DM bring-up may be skipped, these are the only two questions in this review that datasheets cannot answer:

 - Reverse-insertion rig. LTC4368-1 + FDS6898A + BQ25185 on protoboard, with a deliberately reverse-wired cell and a scope on BQ25185 BAT. Confirm: BAT never goes below −0.3 V; the part latches rather than retries; charging works normally with a correct cell; a 2.0 V cell behaves as predicted; and the recovery trickle actually recovers a 0 V pack. Also measure the no-battery STAT2 toggle rate with your intended CBAT — that number decides how urgently the expander change is needed.

 - NFC at 3.3 V on the real antenna. ST25R3916(B) on your intended antenna geometry, VDD = VDD_TX = 3V3, sup3V set, RFI divider re-scaled. Measure read and write range across your actual tag set — NTAG, DESFire, ISO15693 — and measure rail sag on 3V3 during transmit with a scope. If range clears your showcase bar and the rail holds, N1 is confirmed and the boost footprint stays unpopulated forever.

### 3 · Read three pages on paper

 Listed below. All three are load-bearing and none could be retrieved reliably with the tooling available for this review.

## AppendixClaims I could not verify from a primary source

 Stated explicitly so that nothing in this review is mistaken for something it is not.

 - ST25R3916 absolute-maximum table and any VDD_IO-to-VDD relationship (DS12484, Table 118). The datasheet PDF truncated before that page on every retrieval. Under N1 this is moot; under N2 it is a gating item. Read it on paper before choosing N2.

 - BQ25185 recommended-operating VIN row (SLUSF65A §6.4). Text extraction returned a value contradicting the same document's feature bullet, its electrical characteristics and TI's own EVM guide (which says 3.3–18 V). Confirm visually.

 - LTC4368 gate-enhancement minimum at VIN = 3.0 V. The EC table's ΔVGATE row could not be resolved by supply point. This determines your worst-case RDS(on) at low battery. Confirm against the printed Rev. C table.

 - No published numeric capacitance limit for ESP32-S3 strapping pins. Only Espressif's qualitative “do not add high-value capacitors” exists. The Q4 condition is therefore a judgement, not a spec.

 - No published rate for the BQ25185 no-battery STAT2 toggle. TI states the behaviour and not the frequency. Measure it.

 - No ST or third-party comparison of NFC read range at 3.3 V versus 5 V for a 30–50 mm antenna exists that I could find. The 0.7–0.8× estimate in Q2 is arithmetic on ST's measured VDD_RF values, not characterisation data. This is precisely why experiment 2 exists.

 - ST25R3916-DISCO and STEVAL-25R3916B exact VDD rail. VDD_IO = 3V3 is confirmed on both; the VDD/V_RF source was not conclusively readable. The X-NUCLEO-NFC06A1 arrangement (5 V VDD, 3.3 V VDD_IO) is confirmed from UM2615.

 - TPS25221's advertised reverse-current blocking has no functional description, threshold, response time or leakage spec in its datasheet. It is otherwise an excellent SOT-23-6 fit. Do not substitute it for the TPS22950 without bench-verifying the RCB or getting TI to confirm in writing.

#### Primary sources

 LTC4368 datasheet, Rev. C
 onsemi FDS6898A, Rev. 4
 TI BQ25185, SLUSF65A
 TI E2E — BQ25185 STAT2 with no battery
 TI TPS22950
 TI TPS22918
 TI TPS22917
 TI TPS22913
 TI TCA9535
 NXP PCAL9535A
 TI TPS61023
 TI TPS63020
 ST ST25R3916, DS12484
 ST AN5309 — migration guide
 ST AN5584 — thermal design
 ST AN5592 — antenna matching
 ST AN5768 — 39xx to 39xxB
 ST UM2615 — X-NUCLEO-NFC06A1
 ST community — 3916B supply configuration
 Espressif ESP32-S3-WROOM-1 datasheet
 Espressif ESP32-S3 datasheet
 ESP-IDF — GPIO & RTC GPIO (S3)
 esptool — boot mode selection
 ESP32-S3 errata descriptions
 esp-idf soc_caps.h (esp32s3)
 TI SLVA730 — reverse current in load switches

 Independent review, advisory only. No repository was read or modified. Every recommendation above should be checked against the printed datasheet page before it becomes a net.
