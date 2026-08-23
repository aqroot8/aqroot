# FBV2-S1-004 — Full Beta v2 radios and NFC migration (sheet 04)

**Task:** FBV2-S1-004. **Date:** 2026-08-23.
**Repository HEAD at task start:** `8556683` (FBV2-S1-003).
**Scope:** sheet `04_spi_b_radios_nfc`, plus two net-label changes on sheet `01` and the
matching root-sheet rename that item 6 could not be satisfied without (§3). Sheets `05`–`09`
were **not** modified. The PCB was **not** touched. `hardware/beta-dm/`, `hardware/beta/`
and `hardware/beta/mechanical/` were **not** touched.

---

## 0. Result

| gate | verdict |
|---|---|
| **FBV2-S1-RADIOS-NFC** (task gate) | **PASS** |
| **FBV2-S1** (programme gate) | **STILL OPEN — 4 of 9 sheets** |

**ERC: 4 errors → 2 errors. Total 86 → 68 violations. Zero added, eighteen removed.**
This is the first task in the migration to *reduce* the error count.

**Zero `*_TBD` nets remain anywhere in the project.** Sheet 04 alone retired fourteen of
them.

---

## 1. RF architecture — locked

| band | architecture |
|---|---|
| **433 MHz / CC1101 (`U7`)** | **INTERNAL** flexible antenna. Module IPEX socket → 100 mm micro-coax → Taoglas `FXP450.07.0100C` against a plastic wall. No external bulkhead in the normal product configuration |
| **915 MHz / SX1262 (`U8`)** | **EXTERNAL.** Module IPEX socket → short pigtail → **top-panel SMA bulkhead**. User-changeable antenna |

**Neither band has a motherboard 50 Ω RF trace, a matching network, an RF switch or a
diplexer.** Both modules carry their own matched front end and present a 50 Ω IPEX port.
The board's RF involvement at 433 and 915 MHz is exactly zero copper.

> **This supersedes the earlier internal-FXP890 plan for 915 MHz** recorded in
> `12 - RF and Antenna Plan v0.1`. 433 MHz is unchanged.

**The `U7` IPEX socket must remain service-accessible with the enclosure open.** If internal
433 MHz performance disappoints on the first units, the flex unplugs and an external pigtail
goes in its place — **no PCB respin**. That is the whole point, and it is a placement
constraint for FBV2-P1, not a schematic one.

---

## 2. Antennas

### 2.1 433 MHz — Taoglas `FXP450.07.0100C`

Verified from the Taoglas datasheet (`SPE-23-8-180-A`) and the Digi-Key listing:

| parameter | value | source |
|---|---|---|
| Description | *"410-470MHz Flexible PCB Antenna with 100mm 1.37 IPEX MHFI"* | datasheet, verbatim |
| Frequency | **410 – 470 MHz** (433 MHz is mid-band) | datasheet |
| Dimensions | **47 × 17 × 0.28 mm** | datasheet |
| Cable | **1.37 mm mini-coax, 100 mm** | datasheet |
| Connector | **IPEX MHF I, U.FL compatible** | datasheet |
| Mounting | **Adhesive** | Digi-Key |
| Gain | −0.36 / −1.57 / −0.05 dBi across the three sub-bands | Digi-Key |
| Status / stock / price | **Active**, 54 in stock, **$5.52 @ 1**, $4.16 @ 100, MOQ 1 | Digi-Key |
| Compliance | RoHS & REACH | datasheet |

**Connector-mating verdict: PROVEN COMPATIBLE.** The antenna terminates in **IPEX MHF I**;
the E07-400M10S antenna interface is listed as **IPEX-1 / stamp hole** in Ebyte's own manual
(recorded in `05 - Design Decisions Log`). MHF I, IPEX-1 and U.FL are the same mating
interface. **No connector-variant substitution is needed.**

**What is NOT proven** — and it is a purchasing risk, not a design one: Ebyte sells both
IPEX and stamp-hole variants under similar part numbers, and the IPEX socket must be
**populated on the units actually shipped**. That has been an open procurement-control item
since 2026-08-08 and is restated here as **B-49**, now covering both `U7` and `U8`.

**Not retrieved this session:** minimum bend radius, adhesive type, ground/metal clearance
guidance and operating temperature. The Taoglas datasheet is image-based beyond page 1 and
its text layer carries only the header block. Recorded as **B-50** — these are mechanical
integration inputs for FBV2-P1, not schematic inputs.

### 2.2 Mechanical reservation — an FBV2-P1 keepout, not CAD

**The FXP450 body must mount against a plastic enclosure wall in a dedicated antenna zone,
preferred LEFT / LOWER-SIDE internal region. It must NOT be laid on the PCB.**

Required clearance from — and this list is the requirement, not a preference:

| keep away from | why |
|---|---|
| LiPo battery | a metal-laminate pouch directly behind a 433 MHz radiator detunes and absorbs |
| NFC loop and NFC ferrite | the ferrite is a lossy magnetic sheet at 433 MHz and the loop is a large conductor |
| Speaker magnet | permanent magnet plus a steel basket |
| Large ground-plane regions | the flex is a ground-referenced FPC; copper under it detunes it |
| Metal bosses and screws | resonant scatterers at these dimensions |
| USB connector | large metal shell, and a noise source |
| 915 MHz bulkhead and pigtail | 2 × 433 = 866 MHz sits close to the 915 MHz RX band |
| IR structures | mechanical only — both want the same crown volume |

The 100 mm cable decouples the antenna body from the module position, so the zone can be
chosen on mechanical grounds. **Record as an antenna mechanical keepout for FBV2-P1.**

### 2.3 915 MHz external interface

| element | definition |
|---|---|
| Module side | **IPEX-1 / MHF-I plug** onto the `U8` socket |
| Cable | **1.13 mm micro-coax or RG-178**, **100–150 mm** |
| Panel side | **SMA female (jack), bulkhead, top panel** |
| Cable loss | **≤ 0.3 dB** at 915 MHz over 150 mm for either cable type — negligible against the 22 dBm output |

**Gender: SMA female on the device.** The 915 MHz LoRa antenna ecosystem is overwhelmingly
SMA-male-plug antennas onto SMA-female device jacks; RP-SMA belongs to the Wi-Fi world and
would force users onto an adapter for no benefit. **No proprietary interface is used** — SMA
is entirely practical here.

**No MPN is locked.** Under **D-096** a part number configured from a catalogue scheme is a
hypothesis, and a pigtail assembly is exactly the class of part where that trap is easy. The
*interface* is locked; the assembly MPN is a procurement selection against a live listing
(**B-51**).

**Top-panel coexistence with IR TX and IR RX.** The bulkhead nut and washer need a clear
annulus; the IR emitter and receiver need unobstructed optical apertures on the same top
face. Required spacing is recorded as a constraint — **≥ 8 mm edge-to-edge between the SMA
bulkhead body and either IR aperture**, and the pigtail must not cross the IR optical path.
**No CAD was created** (**B-52**).

---

## 3. NFC supply — B-41 closed

This is the change that item 6 required and that could not be made on sheet 04 alone.

**Before:** `U9` pin 8 `VDD` and pin 10 `VDD_TX` sat on `NFC_5V_PA_PENDING` — the Beta-DM
TPS61023 boost output. The v2 select network (`R106` 0 Ω **FIT** from `+3V3`, `R107` 0 Ω
**DNP** from the boost) existed on sheet 01 and drove **nothing**. That was **B-41**.

**After:**

```
/NFC_SUPPLY  (7)  R106.2  R107.2  TP32.1  C19.1  C55.1  U9.8[VDD]  U9.10[VDD_TX]
/01_POWER_TREE/NFC_5V_PA_PENDING  (6)  C34.2 C35.1 R44.2 TP9.1 U13.6[VOUT] R107.1
```

| requirement | state |
|---|---|
| `VDD` = `NFC_SUPPLY` | **yes**, pin 8 |
| `VDD_TX` = `NFC_SUPPLY` | **yes**, pin 10 |
| `VDD_IO` = `+3V3` | **yes**, pin 1, unchanged |
| First build `NFC_SUPPLY` = `+3V3` | **yes**, through the `R106` FIT link |
| 5 V fallback preserved, no respin | **yes**, `R107` DNP from the boost — one resistor |
| NFC never on the community 5 V rail | **yes.** `ACC_5V_RAW` / `ACC_5V_SW` are a separate boost and load switch and touch nothing here |

**Firmware requirement, binding: `sup3V` must be set.** At 3.3 V the ST25R3916 must be told
it is in 3 V supply mode; leaving it in 5 V mode misconfigures the regulators.

### What this cost, and why it was in scope

Item 6 cannot be satisfied without `NFC_SUPPLY` leaving sheet 01, and the task authorised
"root-sheet/net-label updates required solely by Sheet 04 migration". Sheet 01 received
**exactly two label changes and one flag — no component, value or topology change**:

* its `NFC_SUPPLY` label became a **hierarchical** label, so the net leaves the sheet;
* its `NFC_5V_PA_PENDING` hierarchical label became a **local** label, because with `U9`
  moved that net no longer needs to cross — it is now purely the boost output feeding the
  DNP select link;
* a **`PWR_FLAG`** was added on `NFC_SUPPLY` (see below).

On the root the existing sheet-01↔sheet-04 crossing was **renamed** rather than removed and
re-added, so the net count is unchanged and no ERC entry was created. Sheets `05`–`09` were
not involved.

**The `PWR_FLAG` is D-102-compliant, not ERC suppression.** `NFC_SUPPLY` is genuinely driven
— it is `+3V3` through the `R106` 0 Ω link — and KiCad cannot propagate a driver across a
passive. Same reasoning, and the same test, as `VREC_VCC` on the power tree: **the netlist is
unchanged by the flag.**

---

## 4. CC1101 / `U7` — migration

| check | finding |
|---|---|
| SPI-B wiring | `SCK` 18, `MOSI` 17, `MISO/GDO1` 16 — shared bus B, unchanged |
| CS | `CSN` 19 = `CC1101_CS_N` with `R27` 10 kΩ pull-up to `+3V3` — deselected through reset |
| GDO0 | pin 15 = `CC1101_GDO0` → GPIO15 |
| GDO2 | intentionally omitted, unchanged |
| Reset / control | none — the CC1101 has no reset pin; the module is reset by command over SPI |
| Power | pin 9 `VCC` = `+3V3`; module range 1.8–3.6 V, logic 3.3 V |
| Decoupling | `C16` 100 nF 0603 + `C18` 100 nF 0402 local |
| Safe states | CS pulled high; GDO0 is an input to the MCU |
| Module pin map | GND on 1–5, 11, 12, 20, 22 — matches the Ebyte manual |
| **Antenna** | **pin 21 `ANT` (stamp hole) is now an explicit no-connect.** `CC1101_ANT_TBD` retired |
| Current | 10 dBm class module; the peak TX figure is covered by the MX-1 rule (§8) |

**`CC1101_RF_TBD`** — an orphan label on a 1.27 mm stub connected to nothing — is deleted.
It was one of the project's four ERC **errors**.

---

## 5. SX1262 / `U8` — migration

| check | finding |
|---|---|
| SPI-B | `SCK` 18, `MOSI` 17, `MISO` 16 — unchanged, no bus merge |
| CS | `NSS` 19 = `SX1262_CS_N`, direct to GPIO17, `R28` 10 kΩ pull-up |
| BUSY | pin 14 = `SX1262_BUSY`, **direct to GPIO8** — unchanged, as locked |
| RESET | `NRST` 15 = `SX1262_RST_N`, expander-driven safe state (sheet 08) |
| **DIO1** | pin 13 = **`SX1262_DIO1`, published as a hierarchical net** for sheet 08 to land on the internal PCAL9535A (D-089). It no longer reaches the MCU — GPIO38 is `NATIVE_A` |
| TX/RX mode | `DIO2` (8) strapped to `TXEN` (7) on-module; `RXEN` (6) = `SX1262_RXEN` from the expander. **Firmware must enable SX1262 DIO2-as-RF-switch mode or TXEN never asserts and TX fails** |
| TCXO | `DIO3` is internal, supplying the 32 MHz TCXO at 2.2 V. Firmware must configure the driver for TCXO |
| Power | pin 9 `VCC` = `+3V3`; `C17` 100 nF + `C19`… (decoupling unchanged) |
| **Antenna** | **pin 21 `ANT` (stamp hole) is now an explicit no-connect.** `RF_ANT_TBD` retired |
| Deep-sleep packet wake | **not a requirement** (D-041). No GPIO was remapped for it |

**`SX1262_RF_TBD`** — the second orphan label — is deleted. That is the project's second ERC
error retired by this task.

**DIO1 polarity/behaviour:** SX1262 DIO1 is an active-high, level-holding IRQ that stays
asserted until cleared over SPI (confirmed verbatim from Semtech §13.3.4 in FBV2-PWR-001,
which is why B-24 closed). Landing it on a PCAL9535A input is therefore safe: the expander
latches nothing the MCU cannot clear, and a stuck-high DIO1 can no longer block any
strapping pin — which was the original reason for moving it off GPIO38.

---

## 6. NFC

### 6.1 IC — recommendation, not a silent lock

| | ST25R3916 (currently locked) | ST25R3916B |
|---|---|---|
| Package | `-AQET` **32-UFQFPN 5×5** | `-AQET` **32-UFQFPN 5×5** — same |
| Stock | **Mouser 3,243** | Digi-Key **3,099** (AQET) |
| Price @1 | $6.27 (DK) / **$3.37 (LCSC)** | $6.34 (DK) |
| **LCSC / JLCPCB path** | **YES — `C5267441`** | **none found** |
| Variant trap | — | **`-AQWT` is 0 in stock, restock quoted January 2028** |
| Active Wave Shaping | first-generation | B-series, improved |
| EMVCo | 3.0 analog/digital | PCD L1 **3.2a** |
| Capacitive sensing | **present** | removed |
| RFAL software | supported | supported — one compiler define |
| Migration | none | **AN5768** required; pin/footprint equivalence **not proven this session** |

**Recommendation: KEEP `ST25R3916-AQET`.**

The B's advantages are **EMVCo waveform compliance** and a better AWS implementation.
AQROOT is not an EMVCo terminal. Measured against the stated priorities — reliable NFC
demonstration, normal tag read/write range, first-board success, reasonable standby power,
no unnecessary complexity — the non-B wins on the two that actually bite: it is **already
locked and captured**, and it is the **only one of the two with a JLCPCB assembly path, at
roughly half the unit cost**. Switching would also require reading AN5768 and re-proving
footprint and pin equivalence, neither of which this session could do.

**It is not chosen because "B is newer" is a bad reason — it is chosen because nothing in
the B's delta serves an AQROOT priority, and its delta costs a sourcing path.**

**P-17 is recommended for closure on that basis and is flagged for CTO ratification**, not
silently locked, because the choice touches analog waveform quality and therefore read
range at the margin.

### 6.2 Clock — `NFC_XIN_TBD` / `NFC_XOUT_TBD` retired

DS12484 §2.2.8, verbatim: *"The quartz crystal oscillator operates with 27.12 MHz
crystals."*

```
U9.4 XTO ── NFC_XOUT ── Y1.1        C79 10pF  NFC_XOUT → GND
U9.5 XTI ── NFC_XIN  ── Y1.3        C80 10pF  NFC_XIN  → GND
Y1.2, Y1.4 (shield pads) ── GND
```

| item | value |
|---|---|
| `Y1` | **27.12 MHz, 10 pF load, SMD 3225 4-pad** |
| Candidate MPN | **`TXM27.12M0004322DBBDO00T`** (Yajingxin), **LCSC `C362365`** — ±10 ppm, ESR 30 Ω, −40…+85 °C, **3,420 in stock**, $0.078 |
| `C79` / `C80` | **10 pF 50 V C0G 0603, TUNE** |
| Footprint | `Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm` |

**Load-capacitor sizing, stated honestly.** For `C1 = C2 = C`, `C_L = C/2 + C_stray`. With
`C_L` = 10 pF and stray + pin capacitance ≈ 3 pF the ideal is ≈ 14 pF; **ST's own NUCLEO and
DISCO boards populate 10 pF**. The design starts at **10 pF and trims**, and the footprints
exist to do that. It is marked TUNE because the correct value depends on the finished
board's stray capacitance, which does not exist yet.

The MPN is a **candidate against a live LCSC listing**, not a lock — D-096 applies, and the
crystal must be re-confirmed at the BOM gate.

### 6.3 Matching network — real topology, honest values

The placeholder architecture is gone. What exists now is the ST differential topology, fully
captured, with every element present as a **0603 footprint that can be reworked by hand**:

```
        ┌── C_EMC ──┐   ┌── C_p ──┐
RFO1 ─ L_EMC ─── NFC_EMCA ───────── C_s ── NFC_MATCH_A ── R_q ── NFC_ANT_A ── TP37
        └── GND ────┘   └── GND ──┘
RFO2 ─ L_EMC ─── NFC_EMCB ───────── C_s ── NFC_MATCH_B ── R_q ── NFC_ANT_B ── TP38
                          (mirrored)

NFC_ANT_A ── C_rx_s ── NFC_RXA ──┬── C_rx_p ── GND
                                 └── R_rx ── RFI1        (mirrored to RFI2)
```

| ref | role | initial value | depends on measured antenna? |
|---|---|---|---|
| `L5`, `L6` | EMC filter inductor | **220 nH TUNE** | no — sets the filter corner |
| `C69`, `C70` | EMC filter capacitor | **220 pF 50 V C0G TUNE** | no |
| `C73`, `C74` | parallel/shunt matching | **100 pF 50 V C0G TUNE** | **yes** |
| `C71`, `C72` | series matching | **100 pF 50 V C0G TUNE** | **yes** |
| `R114`, `R115` | damping `R_q` | **0 Ω TUNE** | **yes** |
| `C75`, `C77` | RX divider, series | **47 pF 50 V C0G TUNE** | **yes** |
| `C76`, `C78` | RX divider, shunt | **220 pF 50 V C0G TUNE** | **yes** |
| `R116`, `R117` | RX series resistor | **1 kΩ TUNE** | **yes** |

**Two deliberate design choices:**

* **`C_EMC` and `C_p` are two separate shunt footprints on the same node.** One would be
  electrically sufficient. Two gives **two independent trim positions** instead of one, at
  the cost of two 0603 pads — exactly the kind of no-respin provision D-049 asks for.
* **`R_q` is fitted at 0 Ω, not omitted.** The footprint exists so damping can be raised to
  widen bandwidth and lower Q if read range or waveform shape needs it. Omitting it would
  make that a bodge.

**Voltage rating: 50 V C0G on every RF capacitor.** The antenna node is a resonant tank; with
a 3.3 V driver and realistic Q the voltage across the matching capacitors reaches tens of
volts, far above the driver supply. A 16 V part here would be a latent field failure.

> **The values are INITIAL VALUES and are labelled TUNE on the schematic and in the BOM.**
> They cannot be finalised until the 45 × 45 mm antenna impedance is measured and the ST
> antenna matching tool **STSW-ST25R004** is run against it. **AN5276 could not be retrieved
> this session** — every st.com fetch timed out — so no value here is presented as an ST
> reference figure. Recorded as **B-48**.

`TP37` and `TP38` on `NFC_ANT_A` / `NFC_ANT_B` are the measurement points. Tuning this
network without probing those two nodes is not possible, so they are not optional
diagnostics — they are the instrument interface.

### 6.4 Pins deliberately left unconnected

Six pins carried `*_TBD` labels for no reason other than that nothing had decided about
them. Each is now an **explicit no-connect with a recorded reason**:

| pin | why not used on the first build |
|---|---|
| `AAT_A` (18), `AAT_B` (19) | AAT drives **external variable capacitors** (DS12484 §2.2.4). Fitting varactors and their bias networks is real complexity for a feature that compensates *dynamic* detuning; a rear loop behind ferrite in a plastic shell is a static environment. DS12484 also warns that **AAT combined with hardware wake-up is not recommended** |
| `CSI` (25), `CSO` (2) | capacitive sensing is not implemented. (It is also the one feature the B variant removes — see §6.1) |
| `EXT_LM` (17) | external load-modulation MOSFET gate driver. The internal load modulator is used for card emulation |
| `MCU_CLK` (28) | clock output for the MCU. The ESP32-S3 has its own clocks |

**`I2C_EN` (20) is tied to GND** — SPI mode — unchanged and correct for bus B.

### 6.5 Antenna architecture — recommendation, flagged for decision

| option | assessment |
|---|---|
| **A · PCB loop on the main board** | Needs a **45 × 45 mm keepout in the ground plane on every layer** in the rear upper third of a dense 4-layer board, and the battery sits directly behind that region. Ferrite would have to go between them anyway. Tuning is repeatable in principle but couples to whatever the layout does next door. **Highest first-board risk** |
| **B · purchased flex/FPC NFC antenna with integrated ferrite** | Specified inductance → the matching network can be computed rather than discovered. Ferrite shields the battery by construction. **No hole in the ground plane.** Replaceable during bring-up without a respin. Costs one 2-conductor interface and one assembly step |
| **C · separate daughter antenna** | Everything B gives, plus a board and a connector nobody needs |

**Recommendation: B.** It is the option that maximises first-five-board success, and it is
the only one that does not put a 45 × 45 mm discontinuity into the ground plane of a board
that also has to carry three radios.

**Not locked here.** The trade-off is real — B adds a purchased part, an interface and an
assembly step — and the task is explicit that a new antenna implementation must not be
locked automatically. **Flagged for CTO decision (B-53).**

**The schematic is neutral either way.** The matching network terminates on `NFC_ANT_A` /
`NFC_ANT_B` with a test point on each. A flex antenna lands on those two nets through an
interface part added at that time; an on-PCB loop lands on the same two nets as copper.
**Whichever is chosen, the front end does not change.**

---

## 7. ESD and protection

**Nothing was added, and that is the finding.**

| interface | assessment |
|---|---|
| External 915 MHz bulkhead | The SMA centre pin does present an ESD path. **But the only thing behind it is the E22's own matched front end**, through a coax pigtail with a grounded shield — there is no board trace and no exposed IC pin. An RF TVS at 915 MHz that is transparent enough not to degrade a +22 dBm PA is a real component choice with real loss; adding one speculatively would cost link budget for unquantified benefit. **Recommend: rely on the module front end and the bulkhead's grounded shell for the first build; measure before adding.** |
| Module coax | Shielded, internal, not user-accessible. No protection warranted |
| NFC loop | A magnetically-coupled loop with no galvanic path to the outside world. The matching network's series capacitors are themselves a DC block. No protection warranted |

**No RF TVS parts were added.** Loading an RF path with protection that has not been shown
to be needed is exactly the "random RF TVS" the task warns against.

---

## 8. RF and NFC power budget

**Sheet 04 adds no new rail.** `U7` `VCC`, `U8` `VCC` and `U9` `VDD_IO` all run from `+3V3`,
as before.

**One material change: the NFC field current moves rails.** Previously `U9` `VDD`/`VDD_TX`
came from `NFC_5V_PA_PENDING` — the `U13` TPS61023 boost, whose input is `BQ25185_SYS`. They
now come from `NFC_SUPPLY` = `+3V3`, i.e. **from the TPS63020**. The NFC PA load therefore
moves off `SYS` and onto the main 3.3 V rail, and at 3.3 V it draws proportionally more
current for the same delivered field power.

> **The ST25R3916 field current at 3.3 V was not extracted this session** — DS12484's
> current tables did not survive text extraction. **B-54**: obtain `I_VDD_TX` at 3 V supply
> mode before the rail budget is re-derived. Until then the TPS63020 budget from D-092
> (enforced design case 58–66 % of 2 A) **does not include the NFC field in this form** and
> must not be quoted as if it did.

**The mutual-exclusion rule stands and is unchanged (MX-1, D-092):**

> **At most ONE of {Wi-Fi TX, LoRa TX +22 dBm, sub-GHz TX, NFC field} is active at a time.**
> Multiple radios may receive simultaneously; only transmission is serialised. This is not
> relaxed until measurement proves concurrency safe.

**Firmware constraints recorded by this sheet:**

1. **Set `sup3V`** on the ST25R3916 — it runs at 3.3 V, not 5 V.
2. **Enable SX1262 DIO2-as-RF-switch mode**, or `TXEN` never asserts and TX silently fails.
3. **Configure the SX1262 driver for TCXO** — `DIO3` supplies it at 2.2 V internally.
4. **Drive all three bus-B chip selects high before initialisation** and use a bus mutex;
   `U7`, `U8` and `U9` share SPI-B and all three have hardware pull-ups.
5. **MX-1** as above.

---

## 9. ERC and validation

| measurement | errors | warnings | total |
|---|---|---|---|
| Beta-DM baseline | 5 | 53 | 58 |
| after FBV2-S1-003 | 4 | 82 | 86 |
| **after this task** | **2** | 66 | **68** |

**Zero added. Eighteen removed, two of them errors.**

| removed | class |
|---|---|
| `CC1101_RF_TBD`, `SX1262_RF_TBD` | **`label_dangling` — errors.** Orphan labels on stubs connected to nothing |
| their two wire stubs | `unconnected_wire_endpoint` |
| `CC1101_ANT_TBD`, `RF_ANT_TBD` | `isolated_pin_label` — module stamp-hole pins, now explicit no-connects |
| `NFC_XIN_TBD`, `NFC_XOUT_TBD` | resolved by the crystal |
| `NFC_RFO1_TBD`, `NFC_RFO2_TBD`, `NFC_RFI1_TBD`, `NFC_RFI2_TBD` | resolved by the matching network |
| `NFC_AAT_A_TBD`, `NFC_AAT_B_TBD`, `NFC_CSI_TBD`, `NFC_CSO_TBD`, `NFC_EXT_LM_TBD`, `NFC_MCU_CLK_TBD` | resolved by explicit no-connects with recorded reasons |

**Sheet 04 introduced no violation of any kind.** The remaining 2 errors are inherited
(`ROOTPROBE_IRQ_READY_N` and `RESERVED_NC`, both on unmigrated sheets).

**Validation run:** all ten sheets parse with balanced structure and CRLF preserved; the
sheet was enlarged A4 → A2 to hold the front end; netlist export succeeds; **300 components,
0 duplicate references, 0 without a footprint**; `fork_equivalence.py` **PASS**;
`netclass_probe.py` **PASS**.

---

## 10. Opportunity and simplification scan

| lens | finding | action |
|---|---|---|
| **A · cheap useful capability** | `TP37`/`TP38` on the antenna terminals — without them the matching network cannot be tuned at all | **implemented** |
| **B · unnecessary old circuitry** | Four "RF goes off here" placeholder labels and two orphan stubs describing a board-level RF path that this design has never had; six `*_TBD` NFC pins that were undecided rather than unused | **removed / decided** |
| **C · BOM consolidation** | Every new passive is **0603**, and the values reuse the existing 0603 families. The crystal is the only new package on the sheet. `C_EMC` and `C_rx_p` share 220 pF; `C_s` and `C_p` share 100 pF | — |
| **D · no-respin tuning provisions** | Two shunt trim positions per TX leg instead of one; `R_q` fitted at 0 Ω rather than omitted; `R107` DNP 5 V NFC fallback preserved; the `U7` IPEX unplug path | **implemented / preserved** |
| **E · test points** | `TP37`/`TP38` added. `TP9` (boost) and `TP32` (`NFC_SUPPLY`) already exist on sheet 01. None removed | — |
| **F · serviceability** | The `U7` IPEX socket must stay reachable with the shell open — already CTO-approved, restated as an FBV2-P1 placement constraint | — |

### Items flagged, not added

* **A 915 MHz RF TVS.** Not justified without measurement (§7).
* **An AAT varactor network.** Real added complexity for a feature that compensates dynamic
  detuning we do not expect (§6.4).
* **No new user-visible or product feature was added.**

---

## 11. Blockers

| # | blocker | status |
|---|---|---|
| ~~**B-41**~~ | `NFC_SUPPLY` has no consumer | **CLOSED** — `U9` `VDD`/`VDD_TX` now sit on it (§3) |
| **B-48** | **AN5276 not retrieved** (every st.com fetch timed out). All matching and RX-divider values are initial values | **OPEN, high.** Run STSW-ST25R004 against the measured antenna impedance before the BOM gate |
| **B-49** | **IPEX socket population must be confirmed with the supplier** for the exact ordered `U7` and `U8` MPNs. Ebyte sells IPEX and stamp-hole variants under similar numbers | **OPEN, high.** The entire zero-board-RF plan collapses if stamp-hole units arrive |
| **B-50** | FXP450 bend radius, adhesive, ground-clearance and temperature not retrieved — the datasheet is image-based beyond page 1 | **OPEN, medium.** Mechanical integration input for FBV2-P1 |
| **B-51** | 915 MHz pigtail assembly MPN not selected (interface is locked, part is not) | **OPEN, medium.** D-096 applies |
| **B-52** | Top-panel spacing between the SMA bulkhead and the IR apertures recorded (≥ 8 mm) but **no CAD exists** | **OPEN, medium.** FBV2-P1 / mechanical |
| **B-53** | **NFC antenna architecture undecided** — PCB loop vs flex+ferrite vs daughter | **OPEN, high.** Recommendation is flex+ferrite; the schematic is neutral |
| **B-54** | **ST25R3916 field current at 3.3 V not extracted.** The NFC PA load has moved from `SYS` to `+3V3` and the TPS63020 budget does not yet include it | **OPEN, high.** Re-derive the rail budget once obtained |
| **B-06** | NFC undesigned — no crystal, no matching, no antenna | **LARGELY CLOSED.** Crystal and matching topology now exist; only the antenna choice (B-53) and the tuning values (B-48) remain |
| **P-17** | ST25R3916 or ST25R3916B | **RECOMMENDED FOR CLOSURE — keep the non-B** (§6.1). Flagged for ratification |
| **P-04** | NFC first-fab inclusion | **ANSWERED by the task**: NFC is mandatory and fitted on the first build |

---

## 12. What must happen next

1. **Do not start sheet `05`.**
2. Ratify **P-17** and decide **B-53** (antenna architecture) — both gate the NFC BOM.
3. Obtain AN5276 and run STSW-ST25R004 (**B-48**); obtain `I_VDD_TX` at 3 V (**B-54**).
4. Confirm IPEX population with Ebyte before ordering (**B-49**) — this one has a hard
   procurement deadline ahead of it.
5. Sheet `08` remains the highest-value next migration: it lands `SX1262_DIO1`,
   `TOUCH_INT_N`, `SD_CARD_DETECT_N` and the charger telemetry that keeps **B-15** open.

---

## Sources

* Taoglas `FXP450.07.0100C` datasheet `SPE-23-8-180-A` — 410–470 MHz, 47 × 17 × 0.28 mm,
  100 mm 1.37 mm coax, IPEX MHF I, U.FL compatible. Digi-Key listing for gain, mounting,
  status, stock and price.
* Ebyte `E07-400M10S` and `E22-900M22S` manuals via `05 - Design Decisions Log` — IPEX-1 /
  stamp-hole dual antenna option, pin 21 `ANT` = 50 Ω stamp hole, DIO2→TXEN RF-switch
  control, DIO3 internal TCXO at 2.2 V.
* **ST25R3916 datasheet DS12484 Rev 1** — §2.2.4 AAT drives external variable capacitors and
  is not recommended with hardware wake-up; §2.2.8 *"operates with 27.12 MHz crystals"*;
  pin table for `EXT_LM`, `AAT_A/B`, `CSI/CSO`, `MCU_CLK`.
* LCSC `C362365` — 27.12 MHz, 10 pF, ±10 ppm, ESR 30 Ω, −40…+85 °C, 3,420 in stock.
* Digi-Key / Mouser listings for `ST25R3916-AQET`, `ST25R3916B-AQET`, `ST25R3916-AQWT`,
  `ST25R3916B-AQWT`; LCSC `C5267441`.
* ST community — RFAL supports both devices by compiler define; AN5768 is the migration note.
* `hardware/beta-v2/reports/FBV2-S1-004-erc.rpt`, `…/FBV2-S1-fork-equivalence.md`.
