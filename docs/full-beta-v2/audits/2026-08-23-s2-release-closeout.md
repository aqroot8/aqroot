# FBV2-S2-002 — Full Beta v2 S2 release closeout

**Date:** 2026-08-23 **Starting HEAD:** `fc490d3` **Working tree:** clean at start
**ERC: 27 violations / 0 errors / 27 warnings — byte-comparable to the FBV2-S2-001 baseline.**
**PCB untouched and still bit-identical to Beta-DM.**

**Result: FBV2-S2 = PASS.** Every exit criterion in the brief is met. Six register items close:
**B-03, B-63, B-70, B-54, B-71** and **O-8**.

---

## 1. What this task actually had to prove

FBV2-S2-001 failed on two of fourteen criteria and refused to soften either. This task closes
both, plus four more. **Nothing here was closed by assertion**: every footprint was compared
dimension-by-dimension against a retrieved manufacturer drawing, and every sourcing figure was
read live from the JLCPCB parts API on 2026-08-23.

---

## 2. B-03 — the eight Tier-2 footprints

All eight are now **Tier 1**, with the numbers recorded in
[`assembly/FOOTPRINT_VERIFICATION_LEDGER.md`](../assembly/FOOTPRINT_VERIFICATION_LEDGER.md) §2A.
Seven matched. **The eighth looked like a genuine defect and was not.**

### The MAX98357A exposed pad

Maxim outline **21-0136** lists exposed-pad variations in which **`T1633-5` is 1.50 / 1.60 /
1.70 mm** while `T1633-2/-4/-7C` are 0.95 / **1.10** / 1.25. The KiCad footprint's own `descr`
cites **21-0136 (T1633-5)** — the 1.60-nominal part — while its land is **1.23 × 1.23**, sized for
the 1.10 family. On the face of it, a footprint that contradicts its own citation on a thermal pad.

**Maxim land pattern 90-0032 Rev E settles it, and the answer is that there is no contradiction.**
The drawing is titled *"PACKAGE LAND PATTERN, [T1633] 16L TQFN, 3X3 MM"* and is issued under
**PKG. CODES [T1633-5], [T1633-5C] and [T1633-7C] together** — **one land for all three**:
EP **1.23 × 1.23**, perimeter pads **0.80 × 0.30**, pitch **0.50**, pad **centreline** span
**2.85**, IPC-7351A, ±0.02. Maxim deliberately specifies a land *smaller* than the T1633-5 pad.

**So the land does not depend on which variant `MAX98357AETE+T` carries** — which is fortunate,
because analog.com, Mouser and LCSC all refused the datasheet in this environment. The comparison
against the library file gives **EP exact, pitch exact, inner pad edge exact at 1.025** (so
EP-to-signal clearance is Maxim's own 0.410 mm), pad centre **+0.0125** — inside the drawing's own
tolerance — pad length **+0.025**, pad width **−0.05**.

**No project-local footprint was created.** Forking a footprint to chase a 0.05 mm width that
buys a side fillet at the cost of a thinner mask dam at 0.5 mm pitch would have been a change for
the sake of having made one. **The right outcome of a verification is sometimes "it was already
correct" — but only after the drawing is read.**

### The crystal

`Y1` was carried as a **CANDIDATE, not a lock**. The Yajingxin data sheet was retrieved and its
*Suggested Layout* panel read: pads **1.4 × 1.2**, column gap **0.8**, row gap **0.5** → centres
**(±1.10, ±0.85)**. `Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm` is **1.4 × 1.2 at (±1.10, ±0.85)** —
**exact**. Electricals confirmed: 27.120000 MHz fundamental, **CL 10 pF, ESR 30 Ω max, drive level
100 µW max, ±10 ppm at 25 °C, ±20 ppm over −40…+85 °C, ageing ±5 ppm/year**. Total ±30 ppm against
the ISO/IEC 14443 carrier requirement of ±516 ppm. **`C362365`, 3,421 in stock — the MPN is now
locked, not proposed.** The netlist confirms pins 1/3 are `NFC_XOUT`/`NFC_XIN` and pins 2/4 are
GND, matching the drawing's own connection diagram.

---

## 3. B-63 — the microphone port existed only as a sentence

`AQROOT_Beta:PUI_DMM-4026-B-I2S_4.0x3.0mm` was already Tier 1 for its pads. Its `descr` then said
the acoustic port was *"NOT PART OF THIS FOOTPRINT … an FBV2-S2 / PCB-stage item."* **A port that
lives in a description is a port that gets forgotten at placement.** It is now drawn:

- **Ø1.05 mm NPTH** concentric with pad 4. **The diameter is not invented** — it is the **inner
  diameter of the manufacturer drawing's own pad-4 GND ring** (ID 1.05 / OD 1.65), i.e. the part's
  own port aperture.
- **Paste pullback:** pad 4 no longer carries `F.Paste`. Its paste is a separate **annular
  aperture, ID 1.25 / OD 1.65** — pulled back **0.10 mm** from the copper inner edge so solder
  cannot wick into the port. **The 0.10 mm is a declared stencil design choice, not a drawing
  dimension**, and the footprint says so. Coverage ≈ 72 % of the ring land.
- **Keepout:** dashed `B.Fab` circle plus a `User.Comments` legend — no copper, vias, silkscreen or
  mask step on **either** face.
- **Orientation:** bottom-port. The part sits on the **top** of the PCB and listens **through** it,
  so **the acoustic path leaves on the bottom face**. The enclosure aperture and any gasket belong
  there, not on the component face. Recorded as **M-14**.

The edited file was re-loaded through KiCad's own `pcbnew` parser: seven signal pads, one
paste-only aperture, one Ø1.05 NPTH, valid.

---

## 4. B-70 — the EMC inductor, and why headline specs were not enough

**`L5`/`L6` = Murata `LQW18AN39NG80D`**, LCSC `C2042966`, 270 in stock. 0603/1608 wire-wound
ceramic, **39 nH ±2 % (G)**, **Rdc 0.20 Ω max**, **SRF 3000 MHz min**, **Q 37 min**, **1 A rated**.

The CTO instruction was *do not lock solely from headline specs*. Checked against **D-134**:

1. **SRF 3000 MHz** is **74×** the 40.68 MHz third harmonic and **149×** the 20.1 MHz EMC corner.
   The part behaves as a pure inductor across the entire band of interest.
2. **X_L = 3.32 Ω at 13.56 MHz** — the reactance D-134 already re-solved the match against when it
   moved `L5`/`L6` from 220 nH to 39 nH.
3. **The DCR is not negligible, and that is the finding.** `R_q` is only **1.1 Ω** per arm.
   Adding **0.20 Ω** max gives **1.30 Ω**, so the network **Q falls from 25.3 to ≈ 21.4, about
   −15 %**. That moves *further into* the safe, under-driven side D-134 deliberately chose, so it
   is **not a stress condition** — but it means **the antenna must be bench-tuned with this exact
   part fitted**, not with an ideal inductor. If field strength comes up short at first article,
   **the first lever is `R_q` 1.1 Ω → 0.9 Ω, not a change to 39 nH.** D-134 forbids moving `L`
   without re-running the whole matching calculation, and that has not been done here.
4. **Coil current ≈ 187 mA worst case against a 1 A rating** — better than 5×.

---

## 5. B-54 — the NFC current allocation, split properly

The ST25R3916 datasheet finally yielded through a **mikroe.com mirror** after st.com timed out
repeatedly. **DS12484 Rev 3, Table 121 (V_DD = 3.3 V)**:

| parameter | typ | max |
|---|---|---|
| `I_PD` power-down | 0.8 µA | 2.5 µA |
| `I_WU` wake-up (logic + RC osc.) | 3.0 µA | 7.0 µA |
| `I_RD` ready mode | — | **7.5 mA** |
| **`I_AL` all active** | **16 mA** | **23 mA** |
| **`I_AL-AM` all active, AM** | 17 mA | **26 mA** |
| `I_AL1` all active, single RX channel | 11 mA | 16 mA |
| `R_RFO` driver output resistance | 1.7 Ω | 4.0 Ω |

**Table 118 gives `I_VDD_LDO` = 350 mA and `I_VDD_EXT` = 500 mA. Those are ABSOLUTE MAXIMUM
RATINGS and are not used as operating currents** — the brief was explicit, and this is exactly the
number a careless budget would have grabbed.

**First-build `+3V3` allocation, field on:**

| term | value | source |
|---|---|---|
| IC, all blocks active with AM | **26 mA** | `I_AL-AM` **max**, not typ |
| RF driver into the D-134 first-build network | **≈ 60 mA** | D-134's own calculation at `C_s` = 300 pF |
| **allocation** | **100 mA** (86 mA + 16 % headroom) | |

**This replaces D-130's ≤ 150 mA estimate, and it vindicates it** — D-130 guessed "20–30 mA of
reader overhead" against a real 26 mA max, and 95–112 mA of driver current against a real ≈ 60 mA
for the network actually fitted.

**TPS63020 re-check.** D-092's enforced worst case is **1.16–1.32 A** and excludes NFC. With
100 mA rather than 150 mA: **1.26–1.42 A = 63–71 % of 2 A** (was 66–74 %). **MX-1 still means the
field is never concurrent with LoRa TX**, MX-2 still caps the speaker during any transmit, and the
IR emitter and the RGB status light — a few mA each — are inside the 16 % headroom. The
accessory-short case is unchanged: **MX-5** disables on `FLT` within 100 ms and **does not
auto-retry into a short**.

> **One guard rail, and it is not optional.** D-134 records that dropping `C_s` from 300 pF to
> 270 pF gives **≈ 257 mA** of driver current. That is **not** covered by this allocation.
> **If bench tuning proposes 270 pF, the rail budget must be re-run before the change is made.**

**B-54 closes as an allocation, which is what was asked for.** A bench measurement at first
article is still scheduled and is still worth taking.

---

## 6. B-71 — and six substitution traps

The full classification is in
[`assembly/FIRST_FIVE_ASSEMBLY_PLAN.md`](../assembly/FIRST_FIVE_ASSEMBLY_PLAN.md). Headlines:

- **46 unique MPNs**, every one with a live LCSC/JLC library state and an explicit route to the
  board. **65 `LCSC` fields were written into the schematic**, so the BOM is now exportable.
- **Two parts are JLC Basic** (`2N7002`, `AO3401A`); the 207 anonymous passives are Basic too.
- **Ten parts have stock short of the first-five need**, one is **not in the library at all**.
  All are handled by **consignment**, which keeps them **machine-placed**.
- **Two through-hole parts per board are hand-soldered**: `J5` and `D1`. **Zero fine-pitch or QFN
  parts are hand-placed.**

**`U2`/`U3`/`U23` is the sharpest case:** three PCAL9535A per board is **fifteen TSSOP-24 at
0.65 mm pitch**, against **one in stock**. Consignment is the whole reason that is not a
hand-assembly problem.

**`J1` improved.** FBV2-S2-001 recorded the display connector as manual assembly. That followed
from **B-47** — no drop-in second source — but it does not follow that JLC cannot place it. **JLC
carries the genuine Hirose `FH69-50S-0.5SH` with 1,072 in stock**, so `J1` is machine-placed. The
single-source risk is exactly what D-194 says it is, and no more.

### The traps

A loose keyword search against the JLC library **returns a plausible wrong part more often than it
returns nothing**. Six were caught by insisting on manufacturer *and* model, not just stock:

| ref | intended | loose search returns | why it is wrong |
|---|---|---|---|
| `D10`–`D12` | Nexperia `BAT54WS,115` | Nexperia **`BAT54W,115`** | ~~single diode vs series pair — a different device~~ ***CORRECTED 2026-08-23 by D-211: `BAT54WS` IS NOT A SERIES PAIR.* SOD-323 is a two-terminal package and `D10`–`D12` are each ONE independent diode; `BAT54W,115` is wrong because it is SOT-323 (SC-70) — a FOOTPRINT mismatch.** |
| `SW1`–`SW7` | C&K `PTS645SM43SMTR92LFS` | G-Switch `GT-TC089A-H043-L1` | different manufacturer, land never checked — **35 placements** |
| `D8` | onsemi `NSR0240HT1G` | FUXINSEMI `SD103AWS` | a different part number entirely |
| `Q4`, `Q6`–`Q9` | onsemi `BSS138LT1G` | LRC `LBSS138LT1G` | different maker — **and the genuine part has 762,522 in stock** |
| `L2`, `L4` | Würth `74438357010` | KOHERelec `SPM4030-1R0M` | different maker's inductor in a switcher |
| `Q2`, `Q3` | onsemi `NTMD4820NR2G` | VBsemi clone | **battery reverse-polarity pass FETs** — silent substitution is forbidden |

**Every one is now recorded in the schematic symbol**, so the warning travels with the design.

### Two MPN strings were wrong in a way that mattered

`J4` and `J6` are the same JST PH header but carried **two different MPN strings**. That is not
cosmetic: the bare order code resolves to `C20504437` with **stock 0**, while
**`B2B-PH-K-S(LF)(SN)` is `C131337` with 378,913 in stock.** `J7` had the identical problem —
`C20088622` stock 0 versus **`C5118738`, 16,260**. Both corrected. `L2`/`L4` carried two spellings
of "Würth" and were normalised. **A BOM that produces two lines for one part, one unfillable, is a
BOM that stalls at the quote.**

---

## 7. O-8 — the 915 MHz antenna, verified rather than accepted

**Taoglas `TI.92.2113`**, locked by CTO ruling and checked against data sheet **SPE-19-8-076/A**:
**902–928 MHz**, **terminal-mount dipole**, **hinged SMA(M)** as standard, **198 ±3.3 mm × Ø13 mm**,
TPEE, 22.5 g, 50 Ω linear omni, **max input power 1 W**, −40…+85 °C, efficiency **80.01 % straight
/ 73.20 % bent**. Taoglas' own words: it *"performs very well in free space, making it an ideal
solution in areas where there may be no ground plane"* — precisely the reason the CTO gave.

**Every stated expectation checks out. Two things are worth saying plainly anyway:**

- **The "2 dBi" is the bent-configuration peak.** The table gives **peak 1.21 dBi straight /
  2.14 dBi bent**, and **average gain is negative in both** (−0.97 / −1.35 dB). **Budget the link
  with the average.**
- **The mating chain is right end to end:** `E22-900M22S` IPEX/MHF1 → Amphenol AMC right-angle plug
  → RG-178 150 mm → **SMA female** bulkhead → **SMA male** on the antenna. **+22 dBm into a 1 W
  rating is better than 6× margin.** No hardware or schematic change was required.

---

## 8. Eight DNP parts still had no recorded reason

The population re-check (§11 of the brief) found **16 DNP parts, of which eight carried no note at
all.** After seven consecutive sheets of load-bearing inherited DNP, an unexplained DNP is the one
thing this project cannot afford to leave lying around.

- **`U13`, `L2`, `R44`, `R45`, `C34`, `C35` are the NFC 5 V boost branch** — TPS61023 + 1 µH +
  feedback divider + output caps, producing `NFC_5V_PA_PENDING` from `BQ25185_SYS`. **DNP is
  correct**: D-055/D-056 select `NFC_SUPPLY` = `+3V3` through `R106` (fitted), and `R107` (DNP) is
  the mutually exclusive link to the 5 V branch. **The branch is preserved, not abandoned** — a
  no-respin escape under D-049 if the 3.3 V field measures short. **Never fit `R106` and `R107`
  together.** Traced through the netlist and confirmed **not** to be an inherited oversight.
- **`R119`** is the BMI270 alternate-address strap. `R118` (fitted, 0 Ω to GND) holds
  `BMI270_SDO_ADDR` low, so the IMU answers at **0x68**, matching the address registry. **`R118`
  and `R119` are mutually exclusive — fitting both shorts `+3V3` to GND through two 0 Ω links.**
- **`R112`** links display `SDO` to the shared `SPI_A_MISO`. DNP so the panel **cannot** drive the
  bus the microSD reads on. Fitting it is a bring-up provision and **must not** be done while
  **MX-8** is relied on.

**All eight now carry a note. Zero DNP parts in the design lack a recorded reason.**

---

## 9. Regression, and what was not touched

- **ERC: 27 / 0 errors / 27 warnings** — the violation-type histogram is **identical** to the
  FBV2-S2-001 baseline. **No warning was "cleaned".** No no-connect, power flag, pin electrical
  type or ERC exclusion was added, removed or altered anywhere.
- **The schematic diff is property-only.** Mechanically verified: after filtering property blocks,
  **not one wire, label, junction, symbol, pin or sheet-pin line changed** in any of the nine
  sheets. Connectivity cannot have moved.
- **The PCB is untouched** and still bit-identical to Beta-DM. No placement, no routing, no
  outline, no mechanical CAD, no firmware, no Beta-DM, no frozen Beta.
- **No product feature was added.** No new rail, no new IC, no new connector, no speculative
  fallback circuitry.
- ~~**No substitute part was adopted.**~~ **SUPERSEDED 2026-08-23 by D-210 / D-211: BOTH WERE SIGNED OFF AND ADOPTED.** Original text: `BAT54WS-7-F` and `0466005.NRHF` are recorded as **candidates
  awaiting sign-off**.
- **Passive values remain unconsolidated**, per FBV2-S2-001.

---

## 10. What is still owed

| item | state |
|---|---|
| NFC matching bench tuning with the real antenna, shell and battery | **expected** — the CTO ruling is explicit that this does not fail S2 |
| ST25R3916 field current measured at first article | scheduled; the allocation now stands on datasheet maxima, not estimates |
| `C_s` 270 pF guard rail | **binding** — re-run the rail budget before any such change |
| `BAT54WS-7-F` / `0466005.NRHF` sign-off | one line each, before the parts order |
| Stock re-check immediately before ordering | six shortfalls are single- or low-double-digit |
