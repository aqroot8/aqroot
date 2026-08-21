# AQROOT Beta-DM — Procurement Release

Companion to [`BETA-DM-MPN-LEDGER.csv`](BETA-DM-MPN-LEDGER.csv),
[`BETA-DM-POFV-CONTROL.md`](BETA-DM-POFV-CONTROL.md) and
[`BETA-DM-FABRICATION-NOTES.md`](BETA-DM-FABRICATION-NOTES.md).

PCB, DRU and Gerbers are **byte-identical** to `b44e865`. The only design-file
change in this pass is one line of `J5` symbol metadata (§8); no electrical
value, footprint or copper was altered.

---

## 1. POFV — vendor-grounded capability gate

The previous revision called these limits "assumed mainstream capability".
Replaced with checked vendor material.

| | |
|---|---|
| source | JLCPCB PCB Capabilities page and "Via Filling Explained" |
| accessed | **2026-08-21** |

| vendor statement | AQROOT worst case | result |
|---|---|---|
| "Compatible with via diameters from **0.15 to 0.55 mm**" for filled-and-capped vias | drills **0.25 – 0.40 mm** | **PASS** |
| "JLCPCB recommends **≤ 0.5 mm finished diameter** for reliable filling" | largest drill **0.40 mm** | **PASS**, 0.10 mm inside the recommendation |
| "Non-conductive fill uses standard epoxy resin to fill the via completely, followed by leveling and copper over-plating" | exactly the specified process | **matches** |
| minimum via hole size 0.15 mm / minimum via diameter 0.25 mm | smallest drill 0.25 mm, smallest via OD 0.55 mm | **PASS** |
| POFV is free on 6-layer and above; **this is a 4-layer board** | — | **chargeable option — confirm at quote** |
| ENIG | not addressed on the via-filling page; ENIG is offered generally | **confirm at quote** |

**Reading of "0.15 to 0.55 mm".** The same source separately lists minimum via
*hole* size 0.15 mm and minimum via *diameter* (pad) 0.25 mm. A 0.15 mm pad is
impossible, so the 0.15–0.55 mm range can only be the **hole**, not the pad.
This matters: our via *outer* diameters run to 0.80 mm, which would fail if the
range were read as pad diameter. **This is the single item to confirm in
writing** — see §2.

Aspect ratio: no mechanical-via limit is published; the only figure given is
for laser microvias, which this board has none of. Our worst case is
**6.40 : 1** (1.6 mm ÷ 0.25 mm), comfortably inside the 10 : 1 that mechanical
POFV processes normally carry.

**Gate result: PASS on published capability, with two items to confirm at
quote** — 4-layer POFV pricing/availability, and that the 0.15–0.55 mm range is
hole diameter.

Sources: [PCB Capabilities](https://jlcpcb.com/capabilities/pcb-capabilities) ·
[Via Filling Explained](https://jlcpcb.com/blog/via-filling-explained) ·
[Free Via-in-Pad on 6-20 Layer PCBs with POFV](https://jlcpcb.com/news/free-via-in-pad-6-20-layer-pcbs-pofv)

---

## 2. POFV production confirmation packet

Send, as one release:

1. `fab/BETA-DM-POFV-VIAS.csv` — 62 rows, 59 distinct vias
2. `fab/BETA-DM-POFV-CONTROL.md` — the process statement
3. the native `aqroot-Beta-DM.kicad_pcb`
4. `fab/gerbers/` — 11 Gerbers, PTH and NPTH drill, maps, `.gbrjob`

Ordering note, verbatim:

> **FILL ALL 59 LISTED VIAS WITH NON-CONDUCTIVE EPOXY. PLANARISE. COPPER CAP /
> PLATE OVER. ENIG FINISH.**
> Do not substitute solder-mask ink plugging, ordinary tenting, or open via
> barrels. Board is 4-layer, 1.6 mm, green mask.

Questions requiring a written answer before fabrication:

1. Confirm the **count of vias you will fill: 59**.
2. Confirm the 0.15–0.55 mm filled-via range refers to **hole diameter**; our
   drills are 0.25 / 0.30 / 0.40 mm and our via outer diameters are 0.55 / 0.60
   / 0.80 mm.
3. Confirm **POFV is available on 4-layer** and quote it.
4. Confirm **ENIG is compatible** with the 4-layer POFV process.

**MANUFACTURER CONFIRMATION STATUS: PENDING.** No confirmation has been
requested or received. It must not be recorded as obtained until a real reply
exists.

---

## 3. Procurement ledger

| status | groups | parts |
|---|---:|---:|
| **RESOLVED** — exact MPN | **27** | **28** |
| **RESOLVED — body offset to confirm** (`J5`) | **1** | **1** |
| **CANDIDATE — DC-bias confirmation required** (`C24`) | **1** | **1** |
| **GENERIC — PURCHASING RULE** | 37 | 101 |
| not a procurement item (`TP1`–`TP15`) | 6 | 15 |
| | **72** | **146** |

Both former blockers moved this pass: `C24` from STOP to a named 0603 part, and
`J5` from STOP to a locked MPN. Neither required a PCB change.

Procurement groups excluding test points: **66**.

### Resolved this pass, with evidence

| ref | MPN | evidence |
|---|---|---|
| `U1` | **ESP32-S3-WROOM-1-N16R8** | N16R8 is locked in `01 - Hardware Core` and the pin map (16 MB flash, 8 MB PSRAM, octal PSRAM consuming GPIO 26–37). `-1` is the PCB-antenna variant, matching the `RF_Module:ESP32-S3-WROOM-1` footprint; `-1U` is the IPEX variant and is **not** the part. LCSC C2913202. |
| `U2`, `U3` | **TCA9535PWR** | The `R` **is** the tape-and-reel suffix — no further suffix is needed. Active, TSSOP-24, large T&R. `TCA9535PWRG4` is a legacy lead-free designator, also active but redundant; do not order it. LCSC C130204. |
| `U10` | **USBLC6-2SC6** | No automotive requirement exists in this project, so the commercial part is correct. `USBLC6-2SC6Y` is the AEC-Q101 variant and is **not** electrically identical — it is *better* (2.5 pF vs 3.5 pF, 10 nA vs 150 nA). Both are pin-compatible SOT-23-6; either works for USB 2.0 Full Speed. Take the `Y` only if stock favours it. |
| `MK1` | **ICS-43434** | `ICS-43434` is the manufacturer part number; `2911502RL` and `1428-1066-2-ND` are *distributor* order codes, not MPNs. Packaging is chosen at the distributor. LCSC C5656610. |
| `J4` | **B2B-PH-K-S(LF)(SN)** | See §6. |

Every §10 hard-lock part is now resolved: BMI270, E07-400M10S, E22-900M22S,
BQ25185DLHR, TPS63020DSJR, TPS61169DCKR, MAX17048G+T10, TCA9517ADGKR,
TPS22918DBVR, CH280QV10-CT, Molex 5025700893, USB4105-GF-A-120, Coilcraft
XFL4020-152MEC / -472MEC, plus the five above.

Sources:
[Espressif part numbers](https://developer.espressif.com/blog/2025/03/espressif-part-numbers-explained/) ·
[ESP32-S3-WROOM-1 datasheet](https://documentation.espressif.com/esp32-s3-wroom-1_wroom-1u_datasheet_en.html) ·
[TI TCA9535PWR](https://www.ti.com/product/TCA9535/part-details/TCA9535PWR) ·
[ST USBLC6-2SC6Y](https://www.st.com/resource/en/datasheet/usblc6-2sc6y.pdf) ·
[TDK ICS-43434](https://www.invensense.tdk.com/en-us/products/microphone/ics-43434) ·
[JST PH series](https://www.jst-mfg.com/product/pdf/eng/ePH.pdf)

---

## 4. C24 — RESOLVED as a populated 0603 part (was: STOP)

### Correction: the SYS requirement IS specified

**A previous revision of this document, and the decisions-log entry it relied
on, both said no SYS bulk requirement existed. That was wrong.** TI specifies
it explicitly. Authority: **BQ25185 datasheet, SLUSF65A — October 2023, revised
January 2026**, §8.2.2.3 *Recommended Passive Components*, page 21:

> "Low ESR ceramic capacitors, such as X7R or X5R, are preferred for input
> decoupling capacitors and should be placed as close as possible to the supply
> and ground pins of the IC. Due to voltage derating of the capacitors, it is
> recommended that **25V rated capacitors are used for the IN and SYS pins**,
> which normally operate at 5V. **After derating, the minimum capacitance must
> be greater than 1µF.**"

| parameter | MIN | NOM | MAX | UNIT |
|---|---:|---:|---:|---|
| **CSYS** — capacitance on SYS pin | **1** | **10** | **100** | μF |
| CBAT — capacitance on BAT pin | 1 | 1 | — | μF |
| CIN — capacitance on IN pin (tVIN_PRESENT > 25 ms) | 1 | | | μF |

`VSYS_REG` = **4.5 V** (page 7); `VMINSYS` = 3.8 V in battery-tracking mode.

So the schematic's 25 V rating was **not arbitrary** — it follows TI's
recommendation directly. Only the 22 µF value and the 0603 package were wrong.

### Which capacitor is actually the SYS capacitor

Measured on the board from `U11.1` (SYS):

| ref | value | pkg | dist. to `U11.1` | GND return | dist. to `U12` SYS input | role |
|---|---|---|---:|---:|---:|---|
| `C28` | 100 nF X7R | 0603 | **2.09 mm** | 2.73 mm | 11.94 mm | BQ25185 HF decoupling |
| **`C24`** | 22 µF 25 V X7R | **0603** | **3.86 mm** | **2.37 mm** | 17.62 mm | **BQ25185 local SYS bulk** |
| `C33` | 10 µF 10 V X7R | 0805 | 8.43 mm | 6.91 mm | 22.21 mm | supplementary SYS bulk |
| `C26` | 10 µF 10 V X7R | 1206 | 20.36 mm | 21.05 mm | **3.63 mm** | **TPS63020 CIN1** |
| `C27` | 10 µF 10 V X7R | 1206 | 20.84 mm | 22.13 mm | **4.70 mm** | **TPS63020 CIN2** |

**This corrects a second error.** The previous pass treated `C26` + `C27` +
`C33` as "30 µF of SYS bulk available without C24". They share the net, but
`C26`/`C27` sit 20 mm from the charger and 3.6–4.7 mm from the TPS63020 — they
are the **buck-boost input capacitors**, doing a different job, and the
decisions log already assigns them as CIN1/CIN2. They are not BQ25185 SYS
decoupling and must not be counted as such.

**`C24` is the BQ25185's local bulk capacitor** — the nearest bulk part to the
SYS pin, with the shortest ground return of any of them.

### §5 decision-tree result

**Branch 1 (DNP) fails.** No *other local* capacitor satisfies the requirement.
The next bulk part, `C33`, is **2.2× further** from the SYS pin with a **2.9×
longer** ground return, against a datasheet that says "as close as possible".
DNP-ing C24 would leave no bulk within 8 mm of the pin.

**Branch 2 succeeds — the existing 0603 land can take a real part.**

| | |
|---|---|
| **candidate MPN** | **Murata `GRM188R61E106KA73D`** |
| nominal | **10 µF** — exactly TI's CSYS **NOM** |
| voltage | **25 V** — exactly TI's recommendation for IN/SYS |
| dielectric | **X5R** — explicitly allowed by TI ("X7R or X5R") |
| package | **0603** — fits the frozen land, **no PCB change** |
| tolerance | ±10 % |
| availability | LCSC **C344022**, stocked by JLCPCB |
| height | `C24` is at (64.0, 70.0) on F.Cu — **clear of the display shadow (X 12–62) and of the bottom-side battery shadow**, so no height conflict |
| resulting total SYS nominal | 10 + 10 + 10 + 10 + 0.1 = **40.1 µF**, inside TI's 1–100 µF |

### DC-bias gate — CLOSED against official Murata data (2026-08-21)

The verification that was outstanding is now done, from the manufacturer, not
from a distributor description.

**Source.** Murata SimSurfing characteristic data, retrieved from Murata's own
characteristic service `https://ds.murata.com/simserve/characsvdownload` for
part number `GRM188R61E106KA73#` — the same data set the SimSurfing viewer
plots. Two characteristics were pulled, `c_dcbias_capacitance` (absolute) and
`c_dcbias_capchange` (percentage), both at the stated measurement condition
**25 °C, AC 1 Vrms**, over 0–25 V in 0.125 V steps. Both files are archived
verbatim in [`datasheets/`](datasheets/), together with the AC-drive curve.
The Murata Reference Sheet `GRM188R61E106KA73-01A` (Jun 16 2026) supplies the
ratings and confirms the part identity; it carries no DC-bias curve, which is
why the characteristic service is the authority here.

**Measured curve at the operating point.**

| DC bias | capacitance | change |
|---:|---:|---:|
| 0 V | 9.8005 µF | 0 % |
| 4.0 V | 5.2321 µF | −46.6 % |
| **4.5 V (VSYS_REG)** | **4.6773 µF** | **−52.275 %** |
| 5.0 V | 4.1936 µF | −57.2 % |
| 25 V (rated) | 0.7212 µF | −92.6 % |

Retention at 4.5 V is **47.7 %** of the measured 0 V value, **46.8 %** of the
10 µF nominal. TI's floor is **>1 µF effective**, so the typical part clears it
by **4.68×**.

**Conservative lower bound.** Each factor is stacked multiplicatively, which
over-derates on purpose — the AC-drive term in particular is measured at 0 V
bias, where the dielectric is most drive-sensitive, and flattens under bias.

| stage | factor | result | margin vs 1 µF |
|---|---|---:|---:|
| Murata typical, 4.5 V, 25 °C, AC 1 Vrms | — | **4.677 µF** | 4.68× |
| − initial tolerance | ×0.90 (±10 %) | **4.210 µF** | 4.21× |
| − X5R temperature variation, −55…+85 °C | ×0.85 (±15 %) | **3.578 µF** | 3.58× |
| − small-signal AC drive (6.820/9.801 µF at 0 V) | ×0.696 | **2.490 µF** | 2.49× |
| − Class-II aging allowance | ×0.90 | **2.241 µF** | **2.24×** |

Even with all four derations applied at once, effective capacitance stays at
**2.24 µF — more than double TI's floor**. The requirement in §2 is met with
comfortable margin.

**Verdict: PASS. `C24` = Murata `GRM188R61E106KA73D`, 10 µF / 25 V / X5R /
0603, LOCKED, FITTED.**

**Value change LANDED.** The schematic symbol now reads `10uF 25V X5R` and
carries `Manufacturer = Murata`, `MPN = GRM188R61E106KA73D`; the regenerated
BOMs follow. **No PCB change was made** — copper, footprints, Edge.Cuts, the
DRU and all seventeen Gerber/drill artifacts are byte-identical, proven by
SHA-256 in [BETA-DM-FINAL-DESIGN-RELEASE.md](BETA-DM-FINAL-DESIGN-RELEASE.md).
Because the board is frozen, the `C24` value text on `F.Fab` still reads
`22uF 25V X7R`. That is **stale metadata only** — `F.Fab` is not exported in
the copper, mask, paste, silkscreen or drill set. Both CPL files were
post-processed so the assembler-facing value column reads `10uF 25V X5R`,
changing that one field and nothing else. **The BOM and the MPN ledger are the
procurement and assembly authority for `C24`**; nothing assembler-facing
carries the old value. The board text is corrected in Full-Beta, not here.

**`C24` remains FITTED — it is not DNP — and no PCB change was made.**

---

## 5. High-capacitance MLCC audit (≥ 10 µF, fitted)

| ref | value | pkg | net | max operating V | rated V | documented requirement | verdict |
|---|---|---|---|---:|---:|---|---|
| `C24` | **10 µF X5R** | 0603 | `BQ25185_SYS` | ~4.5 V | 25 V | **CSYS**: >1 µF effective after DC-bias derating | **PASS — 4.677 µF at 4.5 V, Murata data, §4** |
| `C26` | 10 µF X7R | 1206 | `BQ25185_SYS` | ~4.5 V | 10 V | **CIN1**: combined effective CIN ≥ 10 µF at 4.5 V, each ≥ ~5 µF derated | **PASS on spec**, MPN open |
| `C27` | 10 µF X7R | 1206 | `BQ25185_SYS` | ~4.5 V | 10 V | **CIN2**: as above | **PASS on spec**, MPN open |
| `C33` | 10 µF X7R | 0805 | `BQ25185_SYS` | ~4.5 V | 10 V | none | PASS |
| `C3`, `C10`, `C15` | 10 µF | 0805 | `+3V3` | 3.3 V | (unstated) | none | PASS on rail; rating to state |
| `C29`–`C32` | 22 µF X7R | 1206 | `+3V3` | 3.3 V | 10 V | none | PASS, 3× margin |

**`C26` / `C27` carry a real derating requirement** — combined effective CIN
≥ 10 µF at 4.5 V, each ≥ ~5 µF after DC-bias derating, 10 V minimum, X7R, 1206
preferred. The log also records that **Murata `GRM21BR71A106KE51L` is obsolete
and must not be assigned**. Any candidate MPN for these two must be checked
against its published DC-bias curve at 4.5 V before it is accepted; that check
has **not** been done in this pass, so `C26`/`C27` stay under the purchasing
rule with a derating condition rather than being marked resolved.

`C3`, `C10`, `C15` carry no voltage rating in the schematic at all
(value is just "10uF"/"10uf"). On a 3.3 V rail any 10 V or 16 V part is fine;
the rule in §7 covers them.

---

## 6. `J4` — battery connector

| | |
|---|---|
| land pattern | `Connector_JST:JST_PH_B2B-PH-K_1x02_P2.00mm_Vertical` — **2.00 mm pitch, vertical, through-hole**, 0.75 mm drill, pads 1.20 × 1.75 mm |
| **MPN** | **JST `B2B-PH-K-S(LF)(SN)`** (LCSC C131337) |
| basis | **identical** land pattern to `J6`, which already carries `B2B-PH-K-S` in the schematic — same footprint library, same pitch, same drill |
| mating housing | **JST `PHR-2`** |
| mating contact | **JST `SPH-002T-P0.5S`**, AWG 24–30 |
| current rating | **1 A** per contact |
| polarity | unchanged — pin 1 `BAT_CONNECTOR_P`, pin 2 `GND` |

**Margin note worth recording.** The documented worst-case system burst is
~640 mA at the 3.3 V rail; at a 3.0 V battery through the boost that is roughly
**0.8 A** through this connector, against its **1 A** rating — about 20 %
headroom on momentary bursts. That is acceptable for a demo build and is
ordinary practice for 1S packs on PH, but it is thin enough to re-examine for
the product revision.

---

## 7. Generic passives — approved purchasing rule

37 groups covering 101 parts are generic passives with no MPN in the
repository. Per §21 of the ruling these are released under a **written
purchasing rule** rather than 101 invented part numbers.

**Resistors — all 0603 unless the ledger says otherwise**

* one reputable thin/thick-film 0603 family across all values, single
  manufacturer series where stocked
* **1 %** tolerance as the default; it costs nothing and does no harm
* ≥ 1/10 W, working voltage ≥ 50 V
* these values are **exact and must not be rounded to E24**: `2.55R`,
  `18k 1%`, `180k 1%`, `1M 1%`, `330R 1%`, `470R 1%`, `22R 1%`, `100k 1%`,
  `10k 1%`, `1k 1%`, `100R 1%`
* `0R` jumpers (`R32`, `R35`, `R42`) must carry an adequate current rating —
  `R42` sits on a power node

**Capacitors**

* dielectric **X7R** wherever the schematic says X7R; never substitute Y5V/Z5U
* voltage rating **≥ 2× the rail** for decoupling: 16 V or 25 V on 3.3 V, and
  ≥ 10 V on the 4.5 V SYS rail
* keep the package the board provides — **the land is frozen**, so a part must
  fit the existing 0402 / 0603 / 0805 / 1206 land
* **size bulk MLCCs by effective capacitance at the operating DC bias, not by
  the printed value.** A nominal 22 µF X5R/X7R can lose 30–60 % at its
  operating voltage
* `C26` / `C27` additionally must meet **combined effective CIN ≥ 10 µF at
  4.5 V**, each ≥ ~5 µF derated. **Murata `GRM21BR71A106KE51L` is obsolete and
  must not be used.**
* do not merge groups across incompatible DC-bias requirements just to shorten
  the BOM

**General**

* active lifecycle only; no NRND, no last-time-buy
* prefer parts the assembler stocks as basic/preferred where technically
  equivalent, but **never** downgrade a critical power part to obtain that
  status
* availability is a **snapshot**: record manufacturer, MPN, package, key
  rating, lifecycle, distributor code and the date checked at the time of
  ordering

---

## 8. `J5` — RESOLVED against the Samtec catalog

**Architecture not reopened.** The part is the one the frozen board was
designed for.

| | |
|---|---|
| **MPN** | **Samtec `TSW-113-08-G-D-RA`** |
| orientation | **RIGHT ANGLE** |
| authority | Samtec TSW / HTSW catalog page **F-226**, retrieved 2026-08-21 |

Every published land parameter compared against the actual PCB footprint:

| parameter | footprint | Samtec published | result |
|---|---|---|---|
| positions | 26 | 26 (`113` = 13 per row × 2) | **MATCH** |
| rows | 2 | 2 (`-D` double row) | **MATCH** |
| pitch along row | 2.540 mm | 2.54 mm (.100") | **MATCH** |
| row spacing | 2.540 mm | 2.54 mm (.100") | **MATCH** |
| **PCB hole diameter** | **1.02 mm** | **1.02 ± 0.03 mm (.040")** | **MATCH** |
| post | .025" square | .025" sq post header | **MATCH** |
| lead style `-08`, `-D`, `-RA` | — | C = **5.84 mm** post, E = **2.29 mm** tail, D = **1.52 mm** | published, consistent |

A 2.29 mm tail through a 1.60 mm board leaves **0.69 mm** protrusion — adequate
for a reliable through-hole joint.

The `-RA` table on F-226 lists lead style **`-08`** under **DOUBLE (`-D`)**, so
`TSW-113-08-G-D-RA` is a valid combination of the published option matrix.

### The one dimension still not published

F-226 gives the body outline figures (8.12 / 8.10 / 5.56 / 6.10 / 3.02 /
3.09 mm) and D = 1.52 mm for `-RA`, but it does **not** publish a
hole-row-to-body dimension for the right-angle version. That is exactly the gap
the floorplan commit recorded: the footprint was generated parametrically with
hole rows at **B+1.50 / B+4.04** at **B = 2.54 nominal**, B described as *not
published by Samtec*, window 2.00–3.05 mm. The board's rows sit at **y = 4.040
and 6.580**, consistent with B = 2.54.

**Nothing mismatches.** Every parameter Samtec publishes agrees with the land.
The open item is a dimension the vendor does not publish here, and it governs
where the plastic body sits relative to the north board edge — a mechanical fit
question, not a solderability one. If the real B differs, the **holes are still
correct**; only the body's overhang shifts.

**Recommendation: lock the MPN**, and confirm the body offset against a Samtec
dimensional drawing or a physical sample before the connector is ordered.

### Metadata drift — CORRECTED

The `J5` symbol's `Footprint` field read
`Connector_PinHeader_2.54mm:PinHeader_2x13_P2.54mm_Vertical` while the board
used the right-angle footprint — which is why the first ledger read "vertical".
It now reads `AQROOT_Beta:Samtec_TSW-113-08-G-D-RA`.

Exactly one line changed, in `09_community_header.kicad_sch`. **No footprint
geometry was altered**, schematic parity stays **0**, and the **PCB, DRU and
Gerbers are byte-identical**.

### Mating (§14)

An ordinary **2×13, 2.54 mm IDC socket on ribbon cable** — deliberately a
commodity. Samtec's own cable mates for TSW are the `IDSD` / `IDSS` families,
and F-226 notes that lead style **`-07` is the best mate for IDC cable**; `-08`
is what this board is built for and is not being changed. Any standard 2×13 IDC
socket will mate.

### Future J5 is separate

The product's right-side recessed / keyed expansion interface is a **later
mechanical revision** and has **no authority** over the connector fitted to the
current Beta-DM.

---

## 9. Checks that passed unchanged

* **§17 BOM cross-check** — 146 fitted, 42 DNP, `TP1`–`TP15` excluded from
  placement, `LS1` remains off-board, `U10` remains fitted, **no DNP leak**, no
  missing fitted part.
* **§18 part-name typo audit** — the repository contains **zero** occurrences
  of `TPS6517`. `U16` is `TCA9517ADGKR` in the schematic, the decisions log and
  the build tracker. **The typo was in the report text, not the repository**;
  nothing was changed.
* **§19 mechanical authority** — Field Slate v5 unchanged: PCB 155 × 74 × 1.6,
  external target 160 × 80 × 23, internal cavity TBD, fit **UNVERIFIED**.
  `tools/check_mechanical_consistency.py` still passes and still reports fit as
  UNKNOWN.
* **§20 future layout locks** — unchanged.
