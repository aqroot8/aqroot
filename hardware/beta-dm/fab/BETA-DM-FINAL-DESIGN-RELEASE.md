# AQROOT Beta-DM — Final Design-Side Release

**Date:** 2026-08-21 · **Scope:** Beta-DM only · **Base:** `d03eab5`

This pass closes the last design-side blocker (`C24` DC bias), locks `J5`, and
assembles the manufacturer submission package. **No routing, no copper change,
no component movement, no `Edge.Cuts` change, no Full-Beta work, and nothing is
ordered.**

| gate | verdict |
|---|---|
| `C24` DC-bias against official Murata data | **PASS** |
| `J5` | **LOCKED PASS** |
| PCB copper / footprints / `Edge.Cuts` / Gerbers | **BYTE-IDENTICAL** |
| DRC | **0 errors** |
| Schematic parity | **0 errors** |
| Unconnected ledger | **103 = A64 + B1(0) + B2(18) + C0 + D21** |
| POFV | **59 vias, PASS** |
| BOM reconciliation | **PASS** |
| POFV manufacturer confirmation | **PENDING** |
| Ready to submit JLCPCB order/quote | **YES** |
| Design-side ready for PCBA | **YES** |
| Actual manufacturer release | **NO** — blocked on production-file confirmation |

---

## 1. `C24` — DC-bias closeout

### 1.1 The requirement

TI **BQ25185**, datasheet **SLUSF65A**, is the authority. `C24` is the local
bulk capacitor on `SYS`.

| parameter | value |
|---|---|
| `CSYS` minimum | 1 µF |
| `CSYS` nominal | **10 µF** |
| `CSYS` maximum | 100 µF |
| after DC-bias derating | **must remain > 1 µF effective** |
| `SYS` operating voltage | ≈ **4.5 V** (`VSYS_REG`) |
| dielectric | X5R or X7R accepted |
| placement | as close as practical to `SYS` and `GND` |

### 1.2 The source

**Murata SimSurfing characteristic data**, pulled from Murata's own
characteristic service, not from a distributor description:

```
https://ds.murata.com/simserve/characsvdownload
  ?ReqType=characsv
  &ReqChara=[{"partnumber":"GRM188R61E106KA73#",
              "chara_type":"c_dcbias_capacitance",   (and c_dcbias_capchange)
              "parameter":{"dc":"","tc":"25","ac":"1"}}]
```

This is the service the SimSurfing characteristics viewer plots from. Both
curves were retrieved at the stated measurement condition **25 °C, AC 1 Vrms**,
0–25 V in 0.125 V steps, and are archived verbatim:

| file | contents |
|---|---|
| [`datasheets/GRM188R61E106KA73-dcbias-capacitance.csv`](datasheets/GRM188R61E106KA73-dcbias-capacitance.csv) | absolute capacitance vs DC bias |
| [`datasheets/GRM188R61E106KA73-dcbias-capchange.csv`](datasheets/GRM188R61E106KA73-dcbias-capchange.csv) | capacitance change rate vs DC bias |
| [`datasheets/GRM188R61E106KA73-acvoltage-capacitance.csv`](datasheets/GRM188R61E106KA73-acvoltage-capacitance.csv) | capacitance vs AC drive level, 0 V bias |

The Murata **Reference Sheet `GRM188R61E106KA73-01A`** (product specifications
as of Jun 16 2026) supplies the ratings and confirms part identity:
1608M (0603), **X5R (EIA)**, **10 µF**, **DC 25 V**, **±10 %**, temperature
coefficient **−15 to +15 %** over **−55 to +85 °C**. It carries no DC-bias
curve — which is exactly why the characteristic service, not the reference
sheet, is the authority for this gate.

### 1.3 The measurement

| DC bias | capacitance | change |
|---:|---:|---:|
| 0 V | 9.8005 µF | 0 % |
| 4.0 V | 5.2321 µF | −46.6 % |
| **4.5 V** | **4.6773 µF** | **−52.275 %** |
| 5.0 V | 4.1936 µF | −57.2 % |
| 25 V (rated) | 0.7212 µF | −92.6 % |

Retention at the 4.5 V operating point is **47.7 %** of the measured 0 V value
and **46.8 %** of the 10 µF nominal.

### 1.4 Conservative lower bound

Every factor is stacked multiplicatively. This deliberately over-derates: the
AC-drive term is measured at 0 V bias, where a Class-II dielectric is most
drive-sensitive, and that sensitivity flattens substantially under bias.

| stage | factor | result | margin vs 1 µF |
|---|---|---:|---:|
| Murata typical @ 4.5 V, 25 °C, AC 1 Vrms | — | **4.677 µF** | **4.68×** |
| − initial tolerance | ×0.90 (±10 %) | **4.210 µF** | 4.21× |
| − X5R temperature variation, −55…+85 °C | ×0.85 (±15 %) | **3.578 µF** | 3.58× |
| − small-signal AC drive (6.820 µF at 0.01 Vrms vs 9.801 µF at 1 Vrms) | ×0.696 | **2.490 µF** | 2.49× |
| − Class-II aging allowance | ×0.90 | **2.241 µF** | **2.24×** |

The headline answer to TI's requirement is the tolerance-only bound,
**4.210 µF**. Even with temperature, AC drive and aging all applied on top,
effective capacitance holds at **2.24 µF — more than twice the floor**.

### 1.5 Verdict

**PASS.**

| | |
|---|---|
| **`C24` final MPN** | **Murata `GRM188R61E106KA73D`** |
| nominal | 10 µF |
| rated | 25 V |
| dielectric | X5R |
| package | 0603 / 1608 metric — the frozen land, unchanged |
| tolerance | ±10 % |
| effective @ 4.5 V | **4.677 µF** |
| worst-case margin vs 1 µF | **4.21×** tolerance-only; **2.24×** fully stacked |
| population | **FITTED** |
| LCSC | C344022 (carried from the previous pass) |

Total `SYS` nominal is now 10 + 10 + 10 + 10 + 0.1 = **40.1 µF**, inside TI's
1–100 µF window.

### 1.6 What landed

Value/metadata only. The schematic symbol `C24` in `01_power_tree.kicad_sch`
now reads `10uF 25V X5R` and carries `Manufacturer = Murata`,
`MPN = GRM188R61E106KA73D`. Nothing on the board moved.

**The assembler-facing exports were corrected.** A raw `kicad-cli` CPL export
takes its `Val` column from the frozen board and so writes `22uF 25V X7R`. Both
CPL files are post-processed so `C24` reads **`10uF 25V X5R`**, changing that
one field and nothing else — `Ref`, `Package`, `PosX`, `PosY`, `Rot` and `Side`
are byte-identical, no other row moves, and each file is a one-line diff. The
step is written into [ASSEMBLY-DNP-CONTROL.md](ASSEMBLY-DNP-CONTROL.md) so it
survives the next regeneration.

**One residual divergence, and it is metadata only.**

| where | reads | status |
|---|---|---|
| PCB `F.Fab` value text | `22uF 25V X7R` | **stale metadata only** — board frozen, `F.Fab` is not a manufacturing layer |
| CPL `Val`, both `pos` files | **`10uF 25V X5R`** | **corrected** |
| BOM + MPN ledger | **`10uF 25V X5R`, Murata `GRM188R61E106KA73D`** | **authoritative** |

`F.Fab` appears in no copper, mask, paste, silkscreen or drill export, so no
manufacturing geometry carries the old value, and nothing assembler-facing does
either. KiCad reports the board/schematic mismatch as exactly one
schematic-parity **warning**; it is documented and **intentional**. The board
text is corrected in Full-Beta, not here.

---

## 2. `J5` — final status

| | |
|---|---|
| **MPN** | **Samtec `TSW-113-08-G-D-RA`** |
| status | **LOCKED FOR BETA-DM** |
| orientation | **RIGHT ANGLE** |
| footprint | `AQROOT_Beta:Samtec_TSW-113-08-G-D-RA` — **PASS** against Samtec published geometry |
| old vertical metadata | **SUPERSEDED / CORRECTED** |

Verified against Samtec catalog F-226: 26 positions, 2 rows, 2.54 mm pitch,
2.54 mm row spacing, 1.02 mm recommended hole — every published parameter
matches the land. Lead style 08 in `-D -RA` gives C = 5.84 mm post and
E = 2.29 mm tail, leaving 0.69 mm protrusion through a 1.6 mm board.

`Manufacturer` and `MPN` are now on the `J5` symbol, so the BOM carries them.
The MPN ledger's `Footprint` column, which still recorded the superseded
vertical footprint, is corrected.

**Not reopened in Beta-DM.** The single open item is unchanged and is a
purchasing check, not a design one: Samtec does not publish a
hole-row-to-body dimension for the right-angle version, so the body offset the
footprint was parameterised on (B = 2.54 mm) must be confirmed against a vendor
drawing or a sample before the connector is ordered. It moves the body relative
to the board edge, not the holes.

---

## 3. Byte-identity proof

Hashes taken before the metadata edits and re-verified after. **All match.**

| artifact | SHA-256 |
|---|---|
| `aqroot-Beta-DM.kicad_pcb` | `aaa04bfbd5d69c5636da1094104081e2729f2bb7d5e07e7353f1f4eafc86a9f2` |
| `aqroot-Beta-DM.kicad_dru` | `050c83fc6838f95313907c0f2991e52048f34ae2eda619a659b3048c9f13ad9b` |

The PCB hash covers copper, every footprint, and `Edge.Cuts` in one figure —
the file was never opened for writing.

All **17** artifacts in `fab/gerbers/` re-verify against their pre-edit
manifest: `F_Cu`, `In1_Cu`, `In2_Cu`, `B_Cu`, `F_Mask`, `B_Mask`, `F_Paste`,
`B_Paste`, `F_Silkscreen`, `B_Silkscreen`, `Edge_Cuts`, `PTH.drl`, `NPTH.drl`,
both drill maps, `.gbrjob`, and the drill report.

Both CPL files were re-exported from the unchanged board and came back
**byte-identical** to the committed versions, confirming the board did not move.
The `C24` `Val` override of §1.6 was then applied on top of that verified
baseline: one field in each file, coordinates, rotation and side untouched.

---

## 4. Checks

| check | result |
|---|---|
| Schematic ERC | **58 violations, identical to the pre-edit report** — pre-existing, unchanged by this pass |
| DRC, errors only | **0 violations** |
| Schematic parity, errors only | **0** |
| Unconnected items | **103** — matches the ledger exactly |
| Schematic parity, warnings | 260 → **261** |

The single net new parity warning is the intended `C24` value divergence of
§1.6. Eight footprints (`C24`, `J4`, `J5`, `MK1`, `U1`, `U2`, `U3`, `U10`) also
swapped a pre-existing `Description`/`Datasheet` warning for a
`Missing symbol field 'Manufacturer' in footprint` warning — KiCad reports one
field mismatch per footprint, and this class already existed on every
MPN-bearing part on the board.

---

## 5. BOM reconciliation

| file | rows | parts |
|---|---:|---:|
| `aqroot-Beta-DM-BOM-full.csv` | 101 | **189** |
| `aqroot-Beta-DM-BOM-fitted.csv` | 72 | **146** |
| `aqroot-Beta-DM-DO-NOT-POPULATE.csv` | 28 | **42** |
| `aqroot-Beta-DM-OFF-BOARD.csv` | 1 | **1** |

146 fitted on-board + 1 off-board + 42 DNP = **189**, the full BOM total.

| requirement | result |
|---|---|
| all fitted refs accounted | **PASS** — 146 |
| all DNP refs accounted | **PASS** — 42, and the DNP set derived from the full BOM matches `DO-NOT-POPULATE.csv` **exactly** |
| no DNP leakage | **PASS** |
| `LS1` | **OFF-BOARD**, in its own file, absent from the fitted BOM |
| `TP1`–`TP15` | present, **non-procurement**, no MPN by design |
| `U10` | **FITTED**, STMicroelectronics `USBLC6-2SC6` |
| `J5` | **`TSW-113-08-G-D-RA`** |
| `C24` | **`GRM188R61E106KA73D`** |

Of the 146 fitted parts, **30 carry an explicit MPN**. The remaining 116 are
64 generic resistors, 37 generic capacitors and 15 test points — the resistors
and capacitors are released under the written purchasing rule in
[BETA-DM-PROCUREMENT-RELEASE.md](BETA-DM-PROCUREMENT-RELEASE.md) §7, and the
test points are not procured.

### 5.1 Three defects found while regenerating

Regenerating the BOM from the schematic surfaced three pre-existing problems.
All are fixed; none touched the board.

1. **Seven fitted parts were tagged `DNP` in the full BOM.** `C1`, `C12`,
   `C18`, `C43`, `C56`, `R43`, `R46` are fitted — they appear in the fitted BOM
   and are absent from `DO-NOT-POPULATE.csv` — but the released full BOM
   labelled them `DNP` because it had been generated without `${DNP}` in
   `--group-by`, so each mixed value-group inherited the flag of its first
   member. Corrected.

2. **`J5`'s footprint in the BOM was the superseded vertical one.** The J5
   metadata fix in `d03eab5` changed the schematic but the BOM CSVs were not
   regenerated afterwards. Corrected.

3. **Eight parts' MPNs existed only in the CSVs.** `J4`, `MK1`, `U1`, `U2`,
   `U3`, `U10` had `Manufacturer`/`MPN` hand-entered into the released BOM but
   absent from the schematic, and `J5` and `C24` had them in the MPN ledger
   only. A clean regeneration would have silently deleted them. All eight now
   carry the fields on the schematic symbol, so the schematic is the single
   source and the BOM is reproducible. The values are unchanged from the MPN
   ledger, which already recorded them as vendor-verified.

The recorded regeneration recipe in
[ASSEMBLY-DNP-CONTROL.md](ASSEMBLY-DNP-CONTROL.md) has been corrected to the
commands that actually reproduce the released files, with the two manual
post-steps written down.

---

## 6. POFV manufacturer submission package

| item | status |
|---|---|
| 59-via POFV CSV | **PRESENT** — [`BETA-DM-POFV-VIAS.csv`](BETA-DM-POFV-VIAS.csv), 62 via/paste intersections across **59 distinct vias** |
| POFV control document | **PRESENT** — [`BETA-DM-POFV-CONTROL.md`](BETA-DM-POFV-CONTROL.md) |
| native PCB | **PRESENT** — `kicad/aqroot-beta-dm/aqroot-Beta-DM.kicad_pcb` |
| Gerbers | **PRESENT** — 11 layer files in `gerbers/` |
| Drills | **PRESENT** — `PTH.drl`, `NPTH.drl`, both drill maps, drill report |
| BOM | **PRESENT** — full, fitted, DNP, off-board |
| CPL | **PRESENT** — `pos-all.csv` (173 rows), `pos-fitted.csv` (131 placeable rows); `C24` value corrected |
| Assembly drawings | **PRESENT** — `assembly-top.pdf`, `assembly-bottom.pdf` |
| Fabrication notes | **PRESENT** — [`BETA-DM-FABRICATION-NOTES.md`](BETA-DM-FABRICATION-NOTES.md) |

62 intersections reduce to 59 distinct vias because one via at
(64.500, 80.500) is shared by four pads. Drill diameters across the set are
**0.25 / 0.30 / 0.40 mm**; outer diameters are 0.55 / 0.60 / 0.80 mm.

### Instruction to the manufacturer

> **ALL 59 LISTED VIAS: NON-CONDUCTIVE EPOXY FILL, PLANARISE, COPPER CAP /
> PLATE OVER.**
>
> Surface finish: **ENIG.** Solder mask: **GREEN.**
>
> Select **CONFIRM PRODUCTION FILE** when the order/quote is submitted.

**JLCPCB production-file confirmation: PENDING.** Not requested, not received,
and not to be marked obtained.

---

## 7. JLC production-file checklist

To be run when the production file arrives. **Production may only be approved
after every line passes.**

| # | check | pass criterion |
|---:|---|---|
| 1 | POFV via layer / list exists | a via-fill list is present in the production file |
| 2 | count matches | exactly **59** vias listed |
| 3 | coordinates | all 59 coordinates from `BETA-DM-POFV-VIAS.csv` represented, none added |
| 4 | no ordinary PTH filled | no via outside the 59 is filled |
| 5 | no solderable through-hole filled | `J1`–`J6`, `SW*`, and every component through-hole untouched |
| 6 | layer count | **4 copper layers** — `F.Cu`, `In1.Cu`, `In2.Cu`, `B.Cu` |
| 7 | board outline | **155 × 74 mm**, 1.6 mm thick |
| 8 | solder mask | **GREEN** |
| 9 | surface finish | **ENIG** |
| 10 | GND pours | `F.Cu` and `B.Cu` outer pours present and solid-connected |
| 11 | RF keepouts | remain empty |
| 12 | `XGPIO5` critical via | present and correct |
| 13 | drill tools | tool table matches `PTH.drl` / `NPTH.drl`; POFV drills are 0.25 / 0.30 / 0.40 mm |
| 14 | DNP handling | unchanged — 42 DNP parts, matching `aqroot-Beta-DM-DO-NOT-POPULATE.csv` |
| 15 | `C24` | fitted as Murata `GRM188R61E106KA73D`, 10 µF / 25 V / X5R; BOM and CPL both read `10uF 25V X5R`. Only the PCB's internal `F.Fab` text is stale (§1.6) |

If the manufacturer's confirmation names a count other than **59**, stop.

---

## 8. Mechanical authority

Unchanged by this pass.

| | |
|---|---|
| PCB | **155 × 74 × 1.6 mm** |
| External enclosure target | **160 × 80 × 23 mm** |
| Internal cavity | **TBD** |
| Fit | **UNVERIFIED UNTIL CAD** |

External layout remains locked: **top** antenna connector; **left** antenna
holder; **right upper/middle** `J5` expansion; **right lower** Volume+,
Volume−, Power, which may move farther down to avoid crowding; **bottom**
microSD and USB-C; **rear** NFC clear.

---

## 9. Final verdict

```
C24 OFFICIAL DC-BIAS SOURCE:      Murata SimSurfing characteristic data
                                  (ds.murata.com/simserve, c_dcbias_capacitance
                                  + c_dcbias_capchange, 25 C / AC 1 Vrms),
                                  archived in fab/datasheets/
C24 NOMINAL:                      10 uF
C24 EFFECTIVE @4.5V:              4.677 uF  (-52.275 %)
C24 WORST-CASE MARGIN VS 1uF:     4.21x  (4.210 uF, -10 % tolerance)
                                  2.24x  (2.241 uF, + X5R temp + AC drive + aging)
C24:                              PASS
C24 FINAL MPN:                    GRM188R61E106KA73D

J5:                               LOCKED PASS
PCB:                              BYTE-IDENTICAL
DRC:                              0 errors
LEDGER:                           103 = A64 + B1(0) + B2(18) + C0 + D21
POFV:                             59 PASS
POFV MANUFACTURER CONFIRMATION:   PENDING
BOM:                              PASS

READY TO SUBMIT JLCPCB ORDER/QUOTE:   YES
DESIGN-SIDE READY FOR PCBA:           YES
ACTUAL MANUFACTURER RELEASE:          NO until production-file confirmation
```

---

## 10. Progress

**Not increased by this pass** — it is a metadata and procurement closeout.

| stage | progress |
|---|---|
| PCB | **100 %** |
| **Overall Beta-DM** | **~81 %** |
| after fabrication + assembly | ~87 % |
| bring-up | ~93 % |
| subsystem validation | ~97 % |
| two-unit LoRa flagship | ~99 % |
| enclosure integration | 100 % |

**DO NOT ORDER. DO NOT START FULL-BETA REDESIGN.**
