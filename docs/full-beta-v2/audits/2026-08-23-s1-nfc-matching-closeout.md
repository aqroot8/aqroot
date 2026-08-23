# FBV2-S1-004C — NFC ferrite orientation correction and first-build matching closeout

**Task:** FBV2-S1-004C. **Date:** 2026-08-23.
**Repository HEAD at task start:** `3debec8` (FBV2-S1-004B).
**Scope:** sheet `04_spi_b_radios_nfc` and documentation only. Sheets `05`–`09`, the PCB,
mechanical CAD, firmware, Beta-DM, frozen Beta and `hardware/beta/mechanical/` were **not**
touched.

---

## 0. Result

| gate | verdict |
|---|---|
| **FBV2-S1-NFC-MATCHING** (task gate) | **PASS** |
| **FBV2-S1** (programme gate) | **STILL OPEN — 4 of 9 sheets** |

**ERC: 68 → 68. Zero added, zero removed. Errors remain 2, both inherited.**

Two things this task found that were not on the brief:

1. **The previous RX divider would have over-driven the receiver.** 47 pF / 220 pF puts
   ≈ **4.4 V pk-pk** on `RFI1`/`RFI2` against a **3.0 V** regulated analog rail. That is a
   part-stress defect, not a tuning preference, and it is fixed here (§6).
2. **The E24 grid is brutally steep at the series matching capacitor.** 270 pF and 300 pF
   per leg bracket the ideal 284 pF and produce **16 Ω and 68 Ω** differential respectively
   — a 4× swing in load impedance for one step on the value grid (§5.3). The first-build
   value is deliberately chosen on the **low-current** side of the ideal, and the reasoning
   is on the record.

---

## 1. Antenna variant corrected — A → B

**SUPERSEDED:** `FXC.46.52.0075X.A.dg`.
**LOCKED:** **`FXC.46.52.0075X.B.dg`**.

Verified **verbatim** from the Taoglas B-version datasheet **`SPE-24-8-104-B`**:

| | |
|---|---|
| Part No | **FXC.46.B Series** |
| Description | *"NFC Flex Antenna (46*0.3mm) with a **Reverse Ferrite Layer** and adhesive backing"* |
| Features | *"13.56 MHz Antenna"*, *"**Reverse Ferrite Layer**"*, *"Flexible Low Profile Embedded"* |
| Diameter | **46 mm** |
| Ordering line | *"**FXC.46.52.0075X.B.dg** - NFC with ferrite and 75mm Twisted Pair 28AWG cable with ACH(F) connector"* |
| Adhesive | *"Peel and stick 3M adhesive"* |
| Compliance | RoHS & REACH |

### Why the B version is the right part, in one sentence

Per Taoglas **APN-24-8-001**, the two variants differ only in **stack order**:

| variant | stack, outside → inside | intended mounting |
|---|---|---|
| **A** | Flex PCB antenna / Ferrite / **Adhesive** | bonded **onto a PCB, component or device surface** |
| **B** | **Adhesive** / Flex PCB antenna / Ferrite | bonded **to the INSIDE of the enclosure**, reading **through** it |

**AQROOT bonds the antenna to the inside of the rear plastic shell and reads outward
through it.** That is the B case exactly. With the A version the ferrite would sit between
the coil and the outside world — i.e. between the antenna and the tag — which is the one
place a flux director must never be.

**The connector, cable, diameter, adhesive and interface are unchanged**, so `J7`
(`BM02B-ACHSS-GAN-ETF`, mating `ACHR-02V-S`) and the board are unaffected. **This is a
purchasing-line change with a schematic-metadata consequence and no board consequence** —
which is exactly what FBV2-S1-004B flagged and why it was flagged before antennas were
ordered.

**The MPN was updated everywhere it appears** in the schematic: `J7`'s `Note` property and
the on-sheet antenna note. No `…A.dg` reference remains anywhere in `hardware/beta-v2/`.

---

## 2. B-version electrical parameters

Used as the design basis, as instructed:

| parameter | value |
|---|---|
| Frequency | **13.56 MHz** |
| `La` | **1.10 µH** |
| `Rs` | **1.50 Ω** |
| `Q` | **60.37** |
| `SRF` | **395 MHz** |

**Consistency check — and the small discrepancy, stated rather than smoothed over:**

```
w    = 2 * pi * 13.56e6                    = 8.5199e7 rad/s
wL   = 8.5199e7 * 1.10e-6                  = 93.72 ohm
Q    = wL / Rs = 93.72 / 1.50              = 62.5     (published: 60.37)
```

The published triple is coherent to about **3 %** — `Q` = 60.37 with `La` = 1.10 µH implies
`Rs` = 1.55 Ω rather than 1.50 Ω. That is ordinary rounding between separately-published
figures and it is well inside the tolerance any of these parts carries. **`Rs` = 1.50 Ω is
used for the damping calculation** (it is the resistance that physically adds to `R_q`), and
`Q₀` is quoted as the published 60.37 where the datasheet figure is meant.

**The SRF at 395 MHz is a large improvement over the A version's 148 MHz** — far from
13.56 MHz, so the coil behaves as a clean inductor across the band of interest.

> The datasheet's electrical table is an image, as it was for the A version, so these
> numbers come from the CTO's manufacturer data rather than from this session's own
> extraction. **B-55 is carried forward unchanged**, and it costs nothing: the network gets
> re-derived from a measured impedance at first article regardless.

---

## 3. AN5276 — what was obtained, and what was not

**Honest statement of source access.** The AN5276 Rev 6 PDF **still would not load in this
environment** — st.com timed out on every attempt, the Mouser mirrors timed out, and a
direct download returned a bot-protection HTML page rather than the document.

**What was obtained is ST's own text of the governing design rules**, which is what the
calculation actually needs:

| rule | ST's wording |
|---|---|
| Signal path | *"From the ST25R3916 antenna driver output pins RFO1 and RFO2, the TX signal goes through the EMC filter into the matching network and to the antenna. The RX signal coming from the antenna is led through the capacitive voltage divider back into the ST25R3916 receiver input pins RFI1 and RFI2."* |
| EMC filter | *"The EMC filter is a one stage filter built up of a series inductor and a parallel capacitor to ground."* |
| **EMC cut-off** | *"The EMC cutoff frequency must not be comprised between 13 and 14 MHz."* |
| Matching | *"The matching network in L topology follows the EMC filter and consists of **one series and two parallel capacitors**, in differential topology. The purpose of the matching network is to match the antenna to a desired impedance value so that, depending on the application, either a **maximum power transfer** from the ST25R3916 to the antenna or **a certain current consumption** is achieved."* |
| RX divider | *"As the voltage on the antenna can be high, a capacitive voltage divider is needed."* |

**The captured topology already matches ST's description** — one-stage EMC filter, then an
L-topology match, then a capacitive divider back into `RFI`. Nothing structural changed;
only the values did.

**B-48 is closed on substance**: the design rules were obtained and applied, and the network
is now internally coherent instead of self-contradictory. **It is not closed on process**:
the `STSW-ST25R004` / eDesignSuite run against a *measured* antenna impedance is still
required before fabrication, and is carried as **B-57**.

---

## 4. Target impedance — derived, not borrowed

**The 20 Ω/side figure from the previous draft is discarded.** It was an assumption with
nothing behind it.

AN5276 offers two design intents: maximum power transfer, or **a certain current
consumption**. AQROOT has a locked current budget from D-130 — **≤ 150 mA from `+3V3` with
the field on**, of which ~20–30 mA is reader-mode overhead — so the second intent is the one
that actually applies here, and it *determines* the target rather than leaving it open:

```
driver budget            = 150 - 30                          = 120 mA  (take 115 mA)
driver input power       = 3.3 V * 115 mA                    = 0.380 W
at ~65 % driver efficiency, RF into the match                = 0.247 W
differential square wave, amplitude ~ VDD_TX = 3.3 V:
  fundamental amplitude  = (4/pi) * 3.3                      = 4.202 V peak
  fundamental RMS                                            = 2.971 V
  Z_target = V_rms^2 / P = 8.827 / 0.247                     = 35.7 ohm differential
```

> **First-build target: Z ≈ 36 Ω differential (18 Ω per side), Q ≈ 25.**

This is a real design target traceable to a locked budget, and it sits inside the range ST's
own tool would produce for a 3.3 V supply. **No EMVCo constraint applies**, so nothing forces
a lower Q or a specific waveform envelope; the Q target is set purely by ISO/IEC 14443
bandwidth at 106 kbit/s.

---

## 5. First-build matching network

### 5.1 Damping — `R114` / `R115`: 1R0 → **1R1 1%**

```
Q0        = wL / Rs = 93.72 / 1.50           = 62.5   (published 60.37)
R_total   = wL / Q_target = 93.72 / 25       = 3.749 ohm
2 * R_q   = 3.749 - 1.50                     = 2.249  ->  R_q = 1R1 per leg (E24)
Q_actual  = 93.72 / (1.50 + 2.20)            = 25.3
```

**This remains the most trustworthy number on the sheet** — it depends only on the antenna's
own `La` and `Rs`, and an undamped Q-62 antenna would be far too narrow to modulate cleanly
at 106 kbit/s.

### 5.2 Match — `C71`/`C72` (`C_s`) and `C73`/`C74` (`C_p`)

L-match from the damped antenna up to the driver, per side:

```
R_low  = R_total / 2 = 3.70 / 2              = 1.85 ohm
R_high = 18 ohm  (36 ohm differential, from the current budget)
Q_m    = sqrt(18 / 1.85 - 1)                 = 2.955
X_ser  = Q_m * R_low                         = 5.467 ohm, net INDUCTIVE
  coil reactance per side = wL / 2           = 46.86 ohm
  so the series capacitor must present       = 46.86 - 5.467 = 41.39 ohm
  C_s(ideal, per leg)                        = 283.6 pF
X_sh   = R_high / Q_m = 18 / 2.955           = 6.091 ohm
  C_p(ideal, per leg)                        = 1.927 nF
```

### 5.3 The E24 problem, and the deliberate choice made

`C_s` sits close to series resonance, where `dZ/dC` is enormous. The two E24 neighbours of
the ideal 284 pF are not close in effect at all:

| `C_s` per leg | series total | net series X | resulting Z (diff) | RF power | driver current |
|---|---|---|---|---|---|
| 270 pF | 135 pF | +6.82 Ω | **≈ 16 Ω** | 0.55 W | **≈ 257 mA — over budget** |
| *284 pF (ideal)* | *142 pF* | *+10.93 Ω* | *36 Ω* | *0.247 W* | *≈ 115 mA* |
| **300 pF** | **150 pF** | **+15.47 Ω** | **≈ 68 Ω** | **0.13 W** | **≈ 60 mA** |

> **`C_s` = 300 pF per leg is selected**, giving ≈ **68 Ω differential**, ≈ **0.13 W** into
> the antenna, an antenna current of √(0.13/3.70) ≈ **187 mA RMS**, and a driver draw of
> ≈ **60 mA**.

**This is deliberately the low-current side of the ideal, and the reasoning is the point:**
on a first board an *under*-driven antenna is a one-component swap, while an *over*-driven
one risks the driver and the `+3V3` budget on first power-up. 187 mA of coil current in a
46 mm loop is a perfectly serviceable field — roughly 72 % of what the 36 Ω design would
produce — so the cost is a modest range reduction that is recoverable by rework.

Reaching the 36 Ω target needs ≈ 284 pF per leg, i.e. an E48 280 pF or a 270 pF + 15 pF
pair. **That is a first-article decision made against a VNA, not a decision to make now.**

With `C_s` = 300 pF the shunt is re-solved for the resulting Q_m = 4.18:

```
R_high(per side) = 1.85 * (1 + 4.18^2)       = 34.2 ohm
X_sh   = 34.2 / 4.18                         = 8.18 ohm  ->  C_p = 1.435 nF  ->  1.5 nF (E24)
```

**`C73` / `C74` = 1.5 nF.**

### 5.4 EMC filter — `L5`/`L6`: 220 nH → **39 nH**, `C69`/`C70`: 220 pF → **100 pF**

This is the value set that FBV2-S1-004B flagged as unbuildable, and it is now fixed rather
than carried forward.

`C_EMC` and `C_p` share a node, so the filter sees the **total** shunt:

```
C_total = C_EMC + C_p = 100 pF + 1500 pF      = 1.6 nF
f_c     = 1 / (2*pi*sqrt(39 nH * 1.6 nF))     = 20.1 MHz
```

| check | result |
|---|---|
| AN5276: cut-off must **not** lie between 13 and 14 MHz | **20.1 MHz — outside the forbidden band, and above the carrier** |
| Previous state | 220 nH with ≈ 2 nF → **7.6 MHz, below the 13.56 MHz carrier** — it would have attenuated the carrier instead of the harmonics |
| Perturbation of the match | `X_L` at 13.56 MHz = 8.52e7 × 39 nH = **3.32 Ω**, small against the 34.2 Ω per-side `R_high`. The old 220 nH presented **18.7 Ω** and was badly perturbing the match as well as mis-siting the filter |

**B-56 is CLOSED.**

### 5.5 The complete first-build set

| ref | role | was | **first-build value** | class |
|---|---|---|---|---|
| `L5`, `L6` | EMC inductor | 220 nH | **39 nH** | CALCULATED FIRST-BUILD |
| `C69`, `C70` | EMC capacitor | 220 pF | **100 pF 50 V C0G** | CALCULATED FIRST-BUILD |
| `C71`, `C72` | TX series `C_s` | 300 pF | **300 pF 50 V C0G** | CALCULATED FIRST-BUILD *(ideal 284 pF; E24 chosen on the safe side)* |
| `C73`, `C74` | TX shunt `C_p` | 1.8 nF | **1.5 nF 50 V C0G** | CALCULATED FIRST-BUILD |
| `R114`, `R115` | damping `R_q` | 1R0 | **1R1 1 %** | CALCULATED FIRST-BUILD |
| `C75`, `C77` | RX divider series | 47 pF | **27 pF 50 V C0G** | CALCULATED FIRST-BUILD — **safety fix, §6** |
| `C76`, `C78` | RX divider shunt | 220 pF | **620 pF 50 V C0G** | CALCULATED FIRST-BUILD — **safety fix, §6** |
| `R116`, `R117` | RFI series | 1 k | **1 k** (unchanged) | isolation; RC pole with ~5 pF input C is ≈ 32 MHz, clear of 13.56 MHz |
| `C79`, `C80` | crystal load | 10 pF | **10 pF** (unchanged) | trims on the finished board |

**Every one is still marked `TUNE`** and every one is 0603 and hand-reworkable. **`TUNE`
here means "expected to move at first article", not "unknown"** — each value above is now a
calculated first-build value with the arithmetic recorded, which is a different thing from
the placeholders this task replaced.

**CALCULATED FIRST-BUILD VALUE ≠ FINAL TUNED VALUE.** Nothing in this task is a final tuned
value, and §8 says what has to happen before anything may be called one.

---

## 6. RFI input safety — a real defect found and fixed

This was asked for as a safety check rather than a range tune, and it earned its place.

**Antenna voltage at full field with the first-build network:**

```
antenna current  = sqrt(P / R_total) = sqrt(0.13 / 3.70)   = 0.187 A RMS
differential coil voltage = I * wL = 0.187 * 93.72         = 17.5 V RMS = 49.5 V pk-pk
per side, referred to ground                               = 24.8 V pk-pk
```

**The previous divider:**

```
ratio = 47 / (47 + 220) = 0.176   ->  RFI = 24.8 * 0.176   = 4.4 V pk-pk per side
```

> **4.4 V pk-pk on a pin whose regulated analog rail is 3.0 V.** That divider was carried
> over as a placeholder and had never been checked against a real antenna voltage. It is a
> **part-stress condition, not a tuning imperfection.**

**The new divider:**

```
ratio = 27 / (27 + 620) = 0.0417  ->  RFI = 24.8 * 0.0417  = 1.03 V pk-pk per side
```

| check | verdict |
|---|---|
| RFI amplitude at full field | **≈ 1.0 V pk-pk per side** |
| Against the 3.0 V regulated analog rail | **> 3× headroom** |
| DC path into `RFI` | **none** — the divider is purely capacitive and `C_s` is itself a DC block |
| Loading of the antenna node | series 27 pF with 620 pF ≈ **26 pF** of added shunt, small against `C_p` = 1.5 nF; folded into the tool run |
| 5 V reference divider reused blindly? | **No.** The ratio was derived from this design's own antenna voltage at 3.3 V |

**Verdict: SAFE by design at 3.3 V first-build operation, with the exact receiver linear
range to be confirmed by measurement at first article.** DS12484's `RFI` input-range table
did not survive text extraction, so the ~1 V pk-pk working point is chosen as a conventional
receiver operating level with large margin to the rail rather than against a quoted limit —
recorded as **B-58**.

---

## 7. The 5 V fallback is preserved and is NOT tuned for

**The first-build network is tuned for 3.3 V only.** Nothing here was compromised to
half-suit 5 V.

Switching `NFC_SUPPLY` from 3.3 V to ~5 V later — fit `R107`, lift `R106` on sheet 01 —
**requires**:

* a **firmware supply-configuration change** (clear `sup3V`);
* **revalidation of the matching, the damping and the RFI divider**, because the driver
  amplitude rises by ~1.5×, which raises antenna voltage and therefore the `RFI` level by
  the same factor — at the current ratio that would be ≈ 1.5 V pk-pk, still inside the rail,
  but it must be re-checked rather than assumed;
* **potentially retuning the passives**, since the optimum load impedance moves with supply.

**It does NOT require**: a PCB respin, an antenna replacement, or an ST25R3916 replacement.

That is the whole value of the DNP link, and it is intact.

---

## 8. First-article tuning plan

**No value in this design may be called a final tuned value until this has been done.**

**Conditions — all of them, simultaneously.** NFC is an inductive near-field system; every
conductor and every dielectric within a few centimetres is part of the antenna. Tuning on a
bare board tells you almost nothing about the product.

* **rear plastic shell fitted**
* **antenna adhered in its final position on the inner rear surface**, ferrite inward
* **PCB installed in its final position**
* **battery installed**
* **ferrite in final orientation** (B-version stack: adhesive outward, ferrite inward)

**Procedure:**

1. **Measure the installed antenna impedance.** With the assembly complete and `J7`
   unplugged, measure `La`, `Rs` and `Q` at 13.56 MHz at the cable end. Expect them to differ
   from the datasheet's free-space figures — that difference is the point of measuring.
2. **Run `STSW-ST25R004` / ST eDesignSuite** with the measured impedance, `VDD_TX` = 3.3 V,
   and a target of ≈ 36 Ω differential. Compare its output against §5.5.
3. **Verify resonance.** Probe `NFC_ANT_A` / `NFC_ANT_B` at `TP37` / `TP38`; confirm the
   resonance sits at 13.56 MHz after the network is fitted.
4. **Verify Q.** From the measured bandwidth; target ≈ 25, and confirm the ISO/IEC 14443
   pulse shape at 106 kbit/s is clean.
5. **Verify the differential match.** Confirm the impedance presented to the driver, and
   confirm the symmetry between the two legs.
6. **Verify `RFI` voltage.** Measure `RFI1`/`RFI2` amplitude at full field. **This is a
   pass/fail safety gate, not an optimisation** — if it exceeds the receiver's range, stop
   and re-divide before continuing.
7. **Measure the actual driver current** from `+3V3` with the field on, and check it against
   the ≤ 150 mA budget (**B-54**).
8. **Test representative tags across all four technologies** — NFC-A, NFC-B, NFC-F, NFC-V.
9. **Record practical read and write distance** for each, through the rear shell.
10. **Repeat the range check with the shell finally assembled and screwed down**, not
    hand-held together — the last few tenths of a millimetre of standoff matter.

Only after step 10 may any value be reclassified from `CALCULATED FIRST-BUILD` to
`FINAL TUNED`.

---

## 9. Mechanical record

| item | value |
|---|---|
| Antenna | **Taoglas `FXC.46.52.0075X.B.dg`** |
| Stack | **adhesive / flex antenna / ferrite** (reverse ferrite) |
| Mount | **adhesive side directly against the INNER REAR enclosure surface** |
| Field direction | **outward, through the rear plastic shell** |
| Ferrite | **faces inward, toward the PCB and battery** |
| Clear zone | **≥ 48 × 48 mm** |
| Keepouts | no battery overlap; no speaker-magnet overlap; **no screws or bosses through the active zone**; the stored 433 MHz flex must not cross the active region |
| Cable | 75 mm — bounds how far `J7` may sit from the antenna position |
| `J7` | JST ACH is a **top-entry** header: it needs vertical mating clearance, and the wires leave horizontally |

**No enclosure external-size change.**

---

## 10. Opportunity and simplification scan

Final sheet-04 scan. **Nothing new is proposed.**

| explicitly not added | why |
|---|---|
| AAT varactors | prohibited by the brief, and unnecessary: a static plastic-shell environment does not need dynamic detuning compensation |
| Extra RF switch | no requirement |
| Extra external 433 connector | the `U7` IPEX already *is* the service port |
| Custom NFC PCB antenna | the whole point of the locked flex is to avoid a 45 × 45 mm ground-plane keepout |
| RF TVS | still no demonstrated need (FBV2-S1-004 §7) |

The one candidate considered and rejected: **an E48 280 pF `C_s`** to land exactly on the
36 Ω target rather than 68 Ω. Rejected for the first build because it commits to a target
impedance that has not been measured yet, and because 0603 C0G at E48 is a narrower supply
base than E24 for no benefit before the VNA session. **It is a first-article component
choice, and §8 step 2 will settle it.** No CTO decision is needed now.

---

## 11. ERC and gate

| measurement | errors | warnings | total |
|---|---|---|---|
| after FBV2-S1-004B | 2 | 66 | 68 |
| **after this task** | **2** | 66 | **68** |

**Zero added, zero removed — the violation lists are identical.** The two remaining errors
are inherited (`ROOTPROBE_IRQ_READY_N`, `RESERVED_NC`), both on unmigrated sheets.

### Sheet-04 close conditions

| condition | state |
|---|---|
| Exact B-version antenna recorded | **met** — `FXC.46.52.0075X.B.dg` in `J7`'s metadata and the sheet note; **no `A.dg` reference remains anywhere in `hardware/beta-v2/`** |
| Invalid EMC values replaced | **met** — 220 nH / 220 pF → 39 nH / 100 pF, cut-off 7.6 MHz → **20.1 MHz** |
| First-build network internally coherent | **met** — damping, match, EMC corner and RX divider all derived from one antenna model and one current budget, and they agree |
| No `*_TBD` NFC nets | **met** — none anywhere in the project |
| 3.3 V RFI input safety verified | **met, and it found a defect** — 4.4 V pk-pk → **1.03 V pk-pk** |
| No new ERC errors | **met** |

**Validation:** all ten sheets parse with balanced structure and CRLF preserved; netlist
export succeeds; 301 components, 0 duplicate references, 0 without a footprint;
`fork_equivalence.py` **PASS**; `netclass_probe.py` **PASS**.

---

## 12. Blockers

| # | blocker | status |
|---|---|---|
| ~~**B-56**~~ | EMC filter values inconsistent; cut-off below the carrier | **CLOSED** — 39 nH / 100 pF, **f_c = 20.1 MHz**, outside AN5276's forbidden 13–14 MHz band |
| ~~**B-48**~~ | AN5276 not retrieved; the driver target impedance was an assumption | **CLOSED ON SUBSTANCE.** ST's design rules were obtained and applied, and the target is now derived from the D-130 current budget rather than assumed. **The Rev 6 PDF still would not load in this environment** — see **B-57** |
| **B-57** | **`STSW-ST25R004` / eDesignSuite run against a *measured* antenna impedance has not been performed** | **OPEN, high.** Required before fabrication; §8 step 2 |
| **B-58** | **`RFI` receiver linear-range spec not extracted** from DS12484 (table is an image). The ≈1 V pk-pk working point is a conventional level with > 3× rail margin, not a figure quoted against a limit | **OPEN, medium.** Confirm at first article; §8 step 6 is a pass/fail gate |
| **B-55** | `La`/`Rs`/`Q` not independently re-extracted (B-version table is an image; the published triple is coherent to ~3 %) | **OPEN, low.** The network is re-derived from measurement anyway |
| **B-54** | ST25R3916 field current at 3.3 V | **OPEN, downgraded.** Estimate ≤ 150 mA stands; the first-build network draws ≈ 60 mA at the driver, comfortably inside it. Measure at §8 step 7 |
| **B-49** | IPEX socket population on the ordered `U7`/`U8` | **STILL OPEN, high** — hard procurement deadline |
| **B-50**, **B-51**, **B-52** | FXP450 mechanical data; 915 pigtail MPN; SMA-vs-IR CAD | **STILL OPEN** |

---

## 13. What must happen next

1. **Do not start sheet `05`.**
2. **Order the B version.** The A version is superseded and must not be ordered.
3. Run the tool against a measured impedance (**B-57**) — it also closes most of **B-55**.
4. **B-49** remains the item with a real external deadline.
5. Sheet `08` remains the highest-value next migration.

---

## Sources

* Taoglas **`SPE-24-8-104-B`** — FXC.46.B Series datasheet. Verbatim: *"NFC Flex Antenna
  (46*0.3mm) with a Reverse Ferrite Layer and adhesive backing"*, *"13.56 MHz Antenna"*,
  *"Reverse Ferrite Layer"*, *"Diameter: 46mm"*, *"FXC.46.52.0075X.B.dg - NFC with ferrite
  and 75mm Twisted Pair 28AWG cable with ACH(F) connector"*, *"Peel and stick 3M adhesive"*.
* Taoglas **APN-24-8-001** — A vs B stack order and intended mounting (via the CTO brief).
* **ST AN5276** — design rules quoted in §3: one-stage EMC filter, the 13–14 MHz cut-off
  exclusion, L-topology matching with one series and two parallel capacitors, and the
  capacitive divider requirement.
* **ST25R3916 datasheet DS12484 Rev 1** — regulated voltages in 3 V supply mode; pin
  functions.
* `hardware/beta-v2/reports/FBV2-S1-004C-erc.rpt`, `…/FBV2-S1-fork-equivalence.md`.
* [`2026-08-23-s1-nfc-antenna-closeout.md`](2026-08-23-s1-nfc-antenna-closeout.md) — the
  antenna and connector lock this task corrects and completes.
