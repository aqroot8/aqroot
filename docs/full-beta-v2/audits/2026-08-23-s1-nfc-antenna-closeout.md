# FBV2-S1-004B — NFC IC and antenna interface final lock

**Task:** FBV2-S1-004B. **Date:** 2026-08-23.
**Repository HEAD at task start:** `09cf768` (FBV2-S1-004).
**Scope:** sheet `04_spi_b_radios_nfc` only, plus documentation. Sheets `05`–`09`, the PCB,
mechanical CAD, firmware and the Beta-DM / frozen-Beta trees were **not** touched.

---

## 0. Result

| gate | verdict |
|---|---|
| **FBV2-S1-NFC-ANTENNA-LOCK** (task gate) | **PASS** |
| **FBV2-S1** (programme gate) | **STILL OPEN — 4 of 9 sheets** |

**ERC: 68 → 68. Zero added, zero removed. Errors remain 2, both inherited.**
The NFC antenna is now a **specific, orderable, off-board assembly on a mating connector** —
not an abstraction.

---

## 1. NFC IC — P-17 CLOSED

**LOCKED: `ST25R3916-AQET` (STMicroelectronics). The B variant is NOT adopted.**

The CTO's reasons are recorded as given: the non-B is active production; it **preserves
capacitive low-power sensing**; AQROOT is not an EMVCo payment terminal; AWS is not worth
trading sourcing simplicity and feature breadth for here; and the first build already has
3.3 V operation plus a no-respin 5 V fallback.

This matches the recommendation FBV2-S1-004 made on independent grounds — the non-B is the
only one of the two with an LCSC part number and therefore a JLCPCB assembly path, at
roughly half the unit cost.

**MPN metadata verified present in the schematic**, not just in prose:

| property | value |
|---|---|
| `Value` | `ST25R3916-AQET` |
| `MPN` | `ST25R3916-AQET` |
| `Manufacturer` | `STMicroelectronics` |
| `LCSC` | `C5267441` |
| `Footprint` | `AQROOT_Beta:ST25R3916_AQET` |

`U9`'s `Package` description property was **rewritten**: it still described the Beta-DM
supply arrangement (`NFC_5V_PA_PENDING`) and told the reader that the RF, oscillator and
AAT pins were "on explicit named TBD nets — DO NOT ROUTE". Both statements became false in
FBV2-S1-004. It now records the locked non-B choice, the `NFC_SUPPLY` arrangement, the
`sup3V` firmware requirement, the four no-connect pin groups, and the fact that every
matching value is `TUNE`.

**P-17 is CLOSED.**

---

## 2. NFC antenna — locked, and verified against the datasheet

**LOCKED: Taoglas `FXC.46.52.0075X.A.dg`, off-board.**

Verified **verbatim** from the Taoglas datasheet `SPE-22-8-131-C`:

| parameter | value | how verified |
|---|---|---|
| Part | **FXC.46 Series** — *"Circular Form Factor Flexible Near Field Communications Antenna"* | datasheet, verbatim |
| Frequency | **13.56 MHz** | datasheet |
| Diameter | **46 mm** | datasheet |
| Thickness | **0.27 mm — `FXC.46.52.0075X.A.dg` — NFC with ferrite and 75 mm Twisted Pair 28AWG cable with ACH(F) connector** | datasheet, verbatim — this is the exact ordering line for our part |
| Ferrite | **integrated** (the `.dg` suffix; the no-ferrite variant `FXC.46.A` is 0.14 mm) | datasheet |
| Adhesive | **Peel and stick 3M** | datasheet |
| Typical interrogation distance | **40 mm** | datasheet |
| Compliance | RoHS & REACH | datasheet |

### The electrical triple — used as given, and flagged

The CTO supplied **L = 1.09 µH, Rs = 1.6 Ω, Q ≈ 58** from manufacturer data, and this task
uses them as the first-build basis exactly as instructed.

**They are internally consistent**, which is a real check and it passes:

```
w   = 2 * pi * 13.56 MHz          = 8.5199e7 rad/s
wL  = 8.5199e7 * 1.09e-6          = 92.87 ohm
Q   = wL / Rs = 92.87 / 1.6       = 58.0     <- matches the supplied Q exactly
```

**What this task could NOT do is re-extract them from the datasheet.** `SPE-22-8-131-C`'s
electrical table is an image; only the header block carries a text layer, and every
mechanical claim above comes from that header. A secondary web summary encountered during
this work quoted **0.72 µH / 0.92 Ω / Q 66.7** for "the FXC.46 series" — those three are
*also* internally consistent (`61.34 / 0.92 = 66.7`), so they belong to *some* real part,
most plausibly the 40 mm `FXC.40`, which the same search returned alongside.

**This is not a challenge to the locked numbers** — an AI-generated search summary that
conflates two datasheets is weak evidence against a CTO-supplied figure. It is recorded as
**B-55**, a low-priority first-article confirmation: read `La`/`Rs`/`Q` off the Taoglas
drawing, or measure the delivered part, before the matching values are finalised. **The
matching network has to be re-derived from a measurement anyway**, so this costs nothing
and closes a loose end.

**The antenna stays off the main PCB.** That was the FBV2-S1-004 recommendation (option B,
purchased flex + ferrite) and it is now the locked architecture — **B-53 is CLOSED**.

---

## 3. Board-side connector — mating proven

**`J7` = JST `BM02B-ACHSS-GAN-ETF`.**

| check | finding | source |
|---|---|---|
| Series | **ACH** | Digi-Key, JST |
| Circuits | **2** | Digi-Key |
| Pitch | **1.20 mm** | Digi-Key |
| Mounting | **SMT** | Digi-Key |
| Contact plating | **Gold** | Digi-Key |
| Rating | **2.0 A / 50 V** | Digi-Key; JST quotes 2.0 A for the 2- and 3-circuit sizes at 28 AWG |
| Temperature | **−25 … +85 °C** | Digi-Key |
| Body | **1.4 mm high, 4.3 mm wide** | JST series description |
| Status / stock / price | **Active**, **30,004 in stock**, **$0.52 @ 1**, $0.3769 @ 100, **MOQ 1** | Digi-Key |
| **Mating receptacle** | **`ACHR-02V-S`** | Digi-Key |
| Footprint | `Connector_JST:JST_ACH_BM02B-ACHSS-GAN-ETF_1x02-1MP_P1.20mm_Vertical` — **the library part is named for this exact MPN** | KiCad 10 |

**Mating compatibility is proven, not assumed.** The header's mating housing is `ACHR-02V-S`
— an **ACH receptacle**, which is precisely the *"ACH(F) connector"* Taoglas fits to the
`FXC.46.52.0075X.A.dg` cable. Both sides name the same series, and the antenna's 28 AWG wire
is the gauge JST rates the series at. **The antenna is replaceable without soldering.**

### One correction to the brief

**The task specified "right-angle SMT". JST classifies ACH as a TOP-ENTRY header.** JST's own
series description: *"the socket half is mated with the header from the vertical direction,
while the wires come out from the horizontal direction of the socket connector."* Newark
lists `BM02B-ACHSS-GAN-TF` as *top entry*, and KiCad's footprint for this exact MPN is
suffixed **`_Vertical`**. Digi-Key's parametric field says "Right Angle", which most likely
describes the **cable exit**, not the mating axis.

**The part is right and unchanged** — the correction is to the descriptor, and it has one
practical consequence: **the socket drops on vertically, so J7 needs mating clearance above
it**, while the cable then leaves horizontally toward the antenna. That is recorded as an
FBV2-P1 placement note, not a part change.

---

## 4. Matching network — what the locked antenna now determines

With a real antenna the network stops being entirely hypothetical. Three values were
re-derived; the rest are still placeholders, and this section says which is which.

### 4.1 Derived from the antenna alone — the solid number

**`R114` / `R115` (`R_q`): 0 Ω → `1R0 TUNE`.**

```
Q0        = wL / Rs = 92.87 / 1.6            = 58.0        (too high for ISO14443 bandwidth)
R_total   = wL / Q_target = 92.87 / 26       = 3.57 ohm
2 * R_q   = 3.57 - 1.6                       = 1.97 ohm    -> R_q = 1R0 per leg (E24)
Q_actual  = 92.87 / (1.6 + 2.0)              = 25.8
```

A reader Q of ~26 is the conventional target band for ISO/IEC 14443 at 106 kbit/s. **This
value depends only on the antenna's own L and Rs**, so it is the most trustworthy number on
the sheet, and it is the one that most directly protects first-board success: an undamped
Q-58 antenna would have far too narrow a bandwidth to modulate cleanly.

### 4.2 Derived with one stated assumption

**`C71` / `C72` (`C_s`, series): 100 pF → `300pF TUNE`.**
**`C73` / `C74` (`C_p`, shunt): 100 pF → `1.8nF TUNE`.**

L-match from the damped antenna resistance up to the driver, per side:

```
R_low  = R_total / 2 = 1.8 ohm            (per side)
ASSUMED driver target R_high = 20 ohm per side (40 ohm differential)
Q_m    = sqrt(20 / 1.8 - 1)               = 3.18
X_ser  = Q_m * R_low = 3.18 * 1.8         = 5.72 ohm, inductive
  coil reactance per side = wL / 2        = 46.4 ohm
  so 1 / (w * C_s) = 46.4 - 5.72          = 40.7 ohm  ->  C_s = 288 pF  -> 300 pF (E24)
X_sh   = R_high / Q_m = 20 / 3.18         = 6.29 ohm  ->  C_p = 1.87 nF -> 1.8 nF (E24)
```

**The 20 Ω/side driver target is an assumption, and it is the weak link.** AN5276 would give
the real figure; it could not be retrieved in FBV2-S1-004 or in this task — every st.com
fetch timed out. The values are therefore the right *shape* and the right *order of
magnitude*, and they are not a validated match.

### 4.3 Explicitly NOT re-derived — and this must not be glossed over

**`L5`/`L6` (220 nH) and `C69`/`C70` (220 pF) — the EMC filter — were left unchanged and are
no longer consistent with the network around them.** With `C_p` now 1.8 nF on the same node,
the shunt capacitance at that point rose by an order of magnitude, and a 220 nH / ~2 nF pair
resonates near **7.6 MHz — below the 13.56 MHz carrier**, which would attenuate the carrier
rather than the harmonics.

**Nobody should build to the current EMC values.** The on-sheet note says so in those words.
Recorded as **B-56**: the EMC filter corner and the split of shunt capacitance between
`C_EMC` and `C_p` must come out of the `STSW-ST25R004` run, not out of this task.

### 4.4 Status of every tuning passive

| ref | role | value | basis |
|---|---|---|---|
| `R114`, `R115` | damping `R_q` | **1R0 TUNE** | **derived from the antenna alone** |
| `C71`, `C72` | series match `C_s` | **300pF TUNE** | derived, one assumption |
| `C73`, `C74` | shunt match `C_p` | **1.8nF TUNE** | derived, one assumption |
| `L5`, `L6` | EMC inductor | 220nH TUNE | **placeholder — not consistent, B-56** |
| `C69`, `C70` | EMC capacitor | 220pF TUNE | **placeholder — not consistent, B-56** |
| `C75`, `C77` | RX divider series | 47pF TUNE | placeholder; the divider ratio must keep `RFIx` in range at full field |
| `C76`, `C78` | RX divider shunt | 220pF TUNE | placeholder |
| `R116`, `R117` | RX series | 1k TUNE | placeholder |
| `C79`, `C80` | crystal load | 10pF TUNE | ST reference boards populate 10 pF; trim on the finished board |

**Every one is 0603 and reachable with a soldering iron.** That is the point: the whole
network is expected to move once, on a bench, with a VNA.

### 4.5 The 5 V fallback still works

Switching `NFC_SUPPLY` from 3.3 V to 5 V — fitting `R107` and lifting `R106` on sheet 01 —
raises the driver output voltage and therefore changes the impedance the match should
present. **That is a re-tune of these same 0603 passives, not a PCB respin.** The fallback
is preserved exactly as D-056 intends, and the cost of exercising it is a bench session.

---

## 5. Test and no-respin provisions — nothing new added

| provision | state |
|---|---|
| `TP32` on `NFC_SUPPLY` | already present (sheet 01) |
| `TP37` / `TP38` on `NFC_ANT_A` / `NFC_ANT_B` | already present — the differential measurement points, and the only way to tune the network |
| Source-select links `R106` (FIT) / `R107` (DNP) | accessible 0603 on sheet 01 |
| `J7` antenna connector | **new** — makes the antenna swappable without soldering |
| Full RF test connector | **not added** |
| AAT varactor network | **not added** |
| Extra RF switches | **not added** |

No technical blocker required any of the three prohibited additions, so none was made.

---

## 6. Mechanical

**NFC antenna clear region: 48 × 48 mm minimum** — the 46 mm antenna plus installation
tolerance. Unchanged from FBV2-S1-004 in every other respect:

* rear upper region;
* **no battery overlap**;
* **ferrite face toward the internal electronics / ground plane**, per the manufacturer's
  stack orientation for the `.dg` (standard-ferrite) variant — see §8;
* no speaker-magnet overlap;
* no metal bosses or screws through the active zone;
* the stored 433 MHz flex must not cross the NFC zone.

**No enclosure external-size change.** The zone is a keepout inside the existing cavity.

**Two placement constraints follow from the parts, not from the zone:**

1. **`J7` needs vertical mating clearance** — the ACH socket drops on from above (§3).
2. **The antenna cable is 75 mm.** `J7` must sit within 75 mm of routed cable length of the
   antenna's position in the rear upper third, with the cable not crossing the 433 MHz flex.
   That is a real constraint on where `J7` can go, and it is the kind of thing that is
   cheap now and expensive after placement.

---

## 7. RF budget — B-54 answered with an estimate

The ST25R3916 current tables in DS12484 still would not survive text extraction, so this is
a **derived conservative estimate**, labelled as such, not a datasheet figure.

```
Driver output, differential square wave, amplitude ~ VDD_TX = 3.3 V
  fundamental differential amplitude  ~ (4/pi) * 3.3        = 4.2 V peak = 2.97 V rms
  into the assumed 40 ohm differential match:
  P_RF = 2.97^2 / 40                                        = 0.22 W
  driver efficiency ~60-70 %  ->  input power               = 0.31 - 0.37 W
  from +3V3                                                 = 95 - 112 mA
plus reader-mode analog/digital/regulator overhead          ~ 20 - 30 mA
```

> **Conservative first-build figure: budget ≤ 150 mA from `+3V3` with the NFC field on.**

Against the TPS63020's 2 A capability, and D-092's enforced design case of 58–66 % (1.16 –
1.32 A), adding 150 mA takes the worst case to **≈ 66–74 %**. That is comfortable — and
**MX-1 means the NFC field is never concurrent with LoRa TX in the first place.**

**No simultaneous RF operation is claimed.** The rule is unchanged and binding: **at most
ONE of {Wi-Fi TX, LoRa TX +22 dBm, sub-GHz TX, NFC field} at a time.**

**B-54 is downgraded, not closed**: an estimate now exists and the budget holds against it,
but the datasheet figure or a bench measurement is still owed before fabrication.

---

## 8. Opportunity and simplification scan

One item is worth surfacing. Everything else on sheet 04 was scanned and rejected as
feature creep or as already covered.

> ### The ferrite is directional, and Taoglas sells both orientations
>
> The locked part is `FXC.46.52.0075X.A.dg` — the **standard ferrite** variant. Taoglas also
> catalogues an otherwise identical **reverse ferrite layer** version of the same 46 mm
> antenna with the same 75 mm ACH(F) cable.
>
> Which one is correct depends on which face is bonded to the enclosure wall: the ferrite
> must end up **between the coil and the metal it is shielding** (the PCB ground plane and
> the battery). If the mechanical design bonds the antenna to the inside of the rear shell
> with the adhesive facing outward, the standard part is right. If the stack ends up
> mirrored, the reverse-ferrite part is the correct order and the standard part will
> underperform.
>
> **Effort: zero board change and zero schematic change — it is the same interface, the same
> connector and the same electrical model. It is a purchasing line item.** But it has to be
> decided against the actual enclosure stack before the first antennas are ordered, because
> ordering the wrong orientation costs a lead time, not a rework.
>
> **Flagged for CTO/user decision. Not changed.**

**No new feature was added.** `J7` is the interface the locked antenna requires, not an
addition.

---

## 9. ERC and validation

| measurement | errors | warnings | total |
|---|---|---|---|
| after FBV2-S1-004 | 2 | 66 | 68 |
| **after this task** | **2** | 66 | **68** |

**Zero added, zero removed — the violation lists are identical.**

| requirement | state |
|---|---|
| No new errors | **met** — the two remaining are inherited (`ROOTPROBE_IRQ_READY_N`, `RESERVED_NC`, both on unmigrated sheets) |
| No `*_TBD` NFC antenna nets | **met** — and no `*_TBD` net of any kind remains in the project |
| Exact antenna connector represented | **met** — `J7`, with `MPN`, `Manufacturer` and a `Mates` note in the schematic metadata |
| Exact NFC MPN represented | **met** — `U9` carries `MPN` and `LCSC` |
| Antenna explicitly off-board | **met** — it terminates on `J7` and an on-sheet note says it does not go on the PCB |
| Sheet 04 otherwise unchanged | **met** — the only edits are `J7` + its two wires and labels, four value changes, `U9`'s description, and four notes |

**Validation:** all ten sheets parse with balanced structure and CRLF preserved; netlist
export succeeds; **301 components, 0 duplicate references, 0 without a footprint**;
`fork_equivalence.py` **PASS**; `netclass_probe.py` **PASS**.

**One reference collision was caught and fixed before it reached the netlist:** the new
connector was first drawn as `J6`, which is already the speaker connector on sheet `06`.
It is `J7`.

---

## 10. Blockers

| # | blocker | status |
|---|---|---|
| ~~**P-17**~~ | ST25R3916 or ST25R3916B | **CLOSED — `ST25R3916-AQET` locked, non-B** |
| ~~**B-53**~~ | NFC antenna architecture undecided | **CLOSED — off-board purchased flex with integrated ferrite, `FXC.46.52.0075X.A.dg`** |
| ~~**B-06**~~ | NFC is undesigned, not merely unrouted | **CLOSED.** Crystal, matching topology, antenna, connector and supply all exist. What remains is tuning, which is a bench activity, not a design gap |
| **B-54** | ST25R3916 field current at 3.3 V | **DOWNGRADED.** Conservative estimate ≤ 150 mA derived (§7) and the budget holds; the datasheet figure or a measurement is still owed |
| **B-55** | **`La`/`Rs`/`Q` not independently re-extracted** — the datasheet's electrical table is an image, and a secondary summary quoted a conflicting triple that most likely belongs to the FXC.40 | **OPEN, low.** Confirm from the Taoglas drawing or measure the delivered part. The match must be re-derived from measurement regardless |
| **B-56** | **EMC filter values are not consistent with the new shunt.** `L5`/`L6` 220 nH with ~2 nF of shunt resonates near 7.6 MHz, below the carrier | **OPEN, high.** Must come out of the `STSW-ST25R004` run. **Do not build to the current EMC values** |
| **B-48** | AN5276 not retrieved; the driver target impedance is an assumption | **STILL OPEN, high** |
| **B-49** | IPEX socket population must be confirmed with the supplier for `U7`/`U8` | **STILL OPEN, high** — hard procurement deadline |
| **B-50**, **B-51**, **B-52** | FXP450 mechanical data; 915 pigtail MPN; SMA-vs-IR CAD | **STILL OPEN** |

---

## 11. What must happen next

1. **Do not start sheet `05`.**
2. Decide the **ferrite orientation** (§8) before antennas are ordered.
3. Obtain AN5276 and run `STSW-ST25R004` against the locked antenna — that single action
   closes **B-48**, **B-56** and most of **B-55**.
4. **B-49** remains the item with a real deadline: confirm IPEX population with Ebyte before
   ordering modules.
5. Sheet `08` remains the highest-value next migration.

---

## Sources

* Taoglas `SPE-22-8-131-C` — FXC.46 Series datasheet. Verbatim: *"Circular Form Factor
  Flexible Near Field Communications Antenna"*, *"13.56 MHz Antenna"*, *"Typical
  interrogation distance: 40 mm"*, *"Diameter: 46 mm"*, *"Thickness: 0.27 mm -
  FXC.46.52.0075X.A.dg - NFC with ferrite and 75mm Twisted Pair 28AWG cable with ACH(F)
  connector"*, *"Peel and stick 3M adhesive"*.
* Digi-Key listing for `BM02B-ACHSS-GAN-ETF` — ACH, 2 pos, 1.20 mm, SMT, gold, 2 A / 50 V,
  −25…+85 °C, Active, 30,004 in stock, $0.52 @ 1, MOQ 1, mates `ACHR-02V-S`.
* JST ACH series description — *"the socket half is mated with the header from the vertical
  direction, while the wires come out from the horizontal direction"*; 1.4 mm high, 4.3 mm
  wide, 2.0 A at 28 AWG.
* Digi-Key / Mouser / LCSC listings for `ST25R3916-AQET` (`C5267441`) and the B variants.
* `hardware/beta-v2/reports/FBV2-S1-004B-erc.rpt`, `…/FBV2-S1-fork-equivalence.md`.
* [`2026-08-23-s1-radios-nfc-implementation.md`](2026-08-23-s1-radios-nfc-implementation.md)
  — the sheet-04 migration this task closes out.
