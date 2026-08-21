# AQROOT Beta-DM — Procurement Release

Companion to [`BETA-DM-MPN-LEDGER.csv`](BETA-DM-MPN-LEDGER.csv),
[`BETA-DM-POFV-CONTROL.md`](BETA-DM-POFV-CONTROL.md) and
[`BETA-DM-FABRICATION-NOTES.md`](BETA-DM-FABRICATION-NOTES.md).

PCB, DRU and Gerbers are **byte-identical** to `b44e865`. Nothing electrical
changed in this pass.

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
| **STOP — CTO DECISION** | 2 | 2 |
| **GENERIC — PURCHASING RULE** | 37 | 101 |
| not a procurement item (`TP1`–`TP15`) | 6 | 15 |
| | **72** | **146** |

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

## 4. C24 — STOP, CTO decision required

**This gate fails, and it was already known to fail.** The decisions log
carries "*C24 — SYS bulk, still UNRESOLVED (schematic deliberately unchanged)*"
from 2026-08-07. This pass confirms it independently and adds the missing
circuit facts.

| question | answer |
|---|---|
| circuit role | bulk decoupling on the charger **system rail** |
| connected net | `/01_POWER_TREE/BQ25185_SYS` — `U11.1` (BQ25185 SYS), also feeding `U12.1/10/11` (TPS63020 input), `C26`, `C27`, `C28`, `C33`, `L2.1`, `R68.1`, `SW9.2`, `U13.3` |
| maximum credible voltage | **~4.5 V regulated** (`VSYS_REG` = 4.5 V, documented), worst case ~5.5 V from a high USB VBUS |
| source of the 25 V requirement | **none found.** No document justifies 25 V. Every other capacitor on this same net — `C26`, `C27`, `C33` — is rated **10 V**. |
| required effective capacitance | **not derivable.** No SYS transient or peak-current requirement is documented. The log already refused to invent one, and so does this pass. |
| does an active 0603 part meet it? | **No.** 22 µF at 25 V does not exist in 0603 from any mainstream vendor — the volumetric limit for 0603 X7R is far below it. The log states the same: "*0603 X7R does not reach 22 µF at 25 V*". |

Two independent defects, not one:

1. **The 25 V rating is unjustified** and 5× the actual rail.
2. **The 0603 land cannot host the part** — and the land is on a frozen PCB.

That second point constrains the options, because the previously recorded
direction (22 µF / 10 V / X7R / **1206**, candidate Murata GRM31CR71A226ME15L)
**cannot be assembled on this board** — C24's land is `C_0603_1608Metric`, pads
0.90 × 0.95 mm at (63.225, 70.000). Changing it means moving copper, which this
pass and the board freeze both forbid.

**Options, for a CTO ruling — no work has been done toward any:**

| | option | consequence |
|---|---|---|
| **A** | larger footprint (1206, as previously directed) | **requires a PCB change** — not available while the board is frozen |
| **B** | keep 0603, drop the voltage rating to match the real 4.5 V rail | a 0603 **10 V** part at 22 µF is not available either; **6.3 V** 22 µF X5R 0603 exists but gives only 1.4× margin on a 4.5 V rail and would derate to roughly a quarter of its printed value |
| **C** | keep 0603, reduce the capacitance to something real — e.g. 4.7 µF 10 V X7R or 10 µF 6.3 V X5R | fits the land and the rail; changes the schematic value, so it needs the missing SYS bulk requirement to justify |
| **D** | populate C24 as **DNP** and rely on the bulk already present | `C26` + `C27` + `C33` give **30 µF nominal** on SYS without C24; C24 is 22 of the 52 µF total. Zero board change, zero new part. |

**Option D is the only one that needs no board change and no invented
requirement**, and it is worth serious consideration for a two-unit demo — but
it is a CTO call, because nobody has written down how much bulk SYS actually
needs.

The blocker is unchanged since 2026-08-07: **the minimum acceptable effective
capacitance on SYS must be written down before C24 can be closed.**

---

## 5. High-capacitance MLCC audit (≥ 10 µF, fitted)

| ref | value | pkg | net | max operating V | rated V | documented requirement | verdict |
|---|---|---|---|---:|---:|---|---|
| `C24` | 22 µF X7R | **0603** | `BQ25185_SYS` | ~4.5 V | 25 V | none | **ISSUE — §4** |
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

## 8. `J5` — STOP, footprint/documentation conflict

**Do not select a J5 part yet.**

| question | finding |
|---|---|
| what the PCB land actually is | 26 pads, 13 columns at **2.54 mm** pitch, two rows at y = **4.04** and **6.58** (row spacing 2.540 mm), 1.70 × 1.70 mm rect pads, **1.02 mm drill**, on **B.Cu**, body at (37.0, 0.0) |
| **CURRENT PCB FOOTPRINT EXPECTS** | **RIGHT ANGLE** |
| evidence | the footprint is `AQROOT_Beta:Samtec_TSW-113-08-G-D-RA` (`-RA` = right angle), and the row positions match its documented parametric formula **B+1.50 / B+4.04** generated at **B = 2.54** |
| why row spacing alone proves nothing | a vertical *and* a right-angle 2×13 TSW both have 2.54 mm row spacing — only the library identity and the B-offset formula distinguish them |

**Two blockers, both pre-existing and both recorded in the decisions log:**

1. **Body depth `B` is unverified.** The log states: *"Body depth B and the
   finished-hole requirement are still unverified … Classification:
   BLOCKS_FAB."* The floorplan commit adds that **B is not published by
   Samtec**, with a window of 2.00–3.05 mm, and that the footprint was
   generated at B = 2.54 nominal, classified `VERIFY_BEFORE_PLACEMENT`. Drill
   1.02 and pad 1.7 are also marked VERIFY. **If the real part's B is not
   2.54 mm, the land is in the wrong place** — and the board is frozen.
2. **Symbol/footprint metadata drift.** The PCB uses the right-angle footprint
   while the schematic symbol's `Footprint` field still reads
   `Connector_PinHeader_2.54mm:PinHeader_2x13_P2.54mm_Vertical`. The log
   records this was deliberately left alone as metadata drift. It is exactly
   why the procurement ledger first read "vertical" — the symbol says vertical,
   the board is right-angle.

**Recommendation: resolve `B` against a real Samtec drawing or a physical
sample before selecting any MPN**, and reconcile the symbol field at the same
time. Selecting a vertical part because the ledger said "vertical" would put
the wrong connector on the board; selecting a right-angle part without
confirming `B` risks a land that does not match the part.

The future product wants `J5` recessed on the right side — that is a **later
mechanical revision and has no authority here**. It must not drive the choice
of the part fitted to the current Beta-DM.

### `J5` mating (§14)

Cannot be finalised while the header itself is unresolved. Once `B` is
confirmed and a TSW-113-08-G-D-RA-class part is fixed, the mating side is an
ordinary 2×13 2.54 mm IDC socket on ribbon cable — a commodity, deliberately
not exotic. Record the exact socket with the header.

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
