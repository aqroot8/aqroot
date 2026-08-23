# FBV2-S1 — Schematic migration closeout

**Gate: FBV2-S1 = PASS.** All **nine** schematic sheets carry the Full Beta v2
architecture. No sheet is byte-equivalent to Beta-DM any longer.

**Date:** 2026-08-23. **Scope:** non-PCB closeout across the whole schematic.

> **FBV2-S1 completion means SCHEMATIC MIGRATION COMPLETE.**
> **It does NOT mean fabrication ready.** No PCB placement, no routing, no
> outline, no DFM, no mechanical CAD, no physical validation has been done, and
> several open items below must close before FBV2-S2.

---

## 1. Sheet-by-sheet migration record

| sheet | task | landed | headline |
|---|---|---|---|
| `01_POWER_TREE` | FBV2-S1-001 | ✔ | LTC4368-1 + P2 reverse-polarity path, autonomous dead-cell recovery, accessory 3.3 V and 5 V rails |
| `02_MCU_CORE` | FBV2-S1-002 | ✔ | GPIO38/47 native pair, `DISP_BL_CTL` moved to GPIO46 with a strap pull-down, `GPIO43` withdrawn |
| `03_SPI_A_DISPLAY_SD` | FBV2-S1-003 | ✔ | ER-TFT035IPS-6 + FH69-50S-0.5SH, backlight re-derived, `SD_CARD_DETECT_N` made real |
| `04_SPI_B_RADIOS_NFC` | FBV2-S1-004/4B/4C | ✔ | CC1101 + SX1262 modules, ST25R3916 antenna and matching locked |
| `05_I2C_DEVICES` | FBV2-S1-005 | ✔ | BMI270 verified line by line, internal pull-ups 4.7 k → 2.2 k |
| `06_AUDIO` | FBV2-S1-006 | ✔ | PUI microphone replacing the obsolete ICS-43434, MAX98357A gain corrected to 6 dB |
| `07_IR` | FBV2-S1-007 | ✔ | TSAL6100 + AO3400A, 150 mA = 75 % of `IFM`, `+3V3` supply, filter quantified |
| `08_BUTTONS_EXPANDERS` | FBV2-S1-008 | ✔ | three PCAL9535A, six buttons, front RGB, charger telemetry landed |
| `09_COMMUNITY_HEADER` | **FBV2-S1-009** | ✔ | BCS-112 24-contact port, TCA4307 buffer, WAKE isolation FET, split 5 V enables |

**`fork_equivalence.py` `SHEETS` list is empty.** Every sheet is declared
`changed` and measured `changed`.

---

## 2. Closeout checks

| check | result |
|---|---|
| all 9 sheets migrated | **PASS** |
| hierarchical labels resolve | **PASS** — zero `hier_label_mismatch`, zero `label_dangling`, zero errors of any class |
| no stale old architecture | **PASS** — no `TCA9535PWR`, `TPS22918`, `TCA9517A`, `M20-7881242`, `Conn_02x13`, `XGPIO10`–`14`, `RESERVED_NC`, `FAST_IO`, `ROOTPROBE_IRQ_READY_N`, `RGB_R/G/B_CTL` or `BTN_HOME_N` as live parts or nets. The strings survive only inside explanatory `Note` fields that record what was replaced and why |
| no `*_TBD` release nets | **PASS** — 0 of 224 nets |
| GPIO ledger agrees with the netlist | **PASS** — all 41 `U1` pins re-read; 33 of 33 usable GPIO assigned, GPIO35/36/37 unconnected (octal PSRAM), no duplicate net on any two `U1` pins |
| I²C registry agrees with the netlist | **PASS** — see §4 |
| three PCAL addresses are 0x20 / 0x21 / 0x22 | **PASS** — `U2` A2A1A0 = GND/GND/GND, `U3` = GND/GND/+3V3, `U23` = GND/+3V3/GND |
| community allocation agrees with D-084 | **PASS** — all 24 contacts verified pin by pin |
| native GPIO38 / GPIO47 preserved | **PASS** — `U1.31` = `NATIVE_A`, `U1.24` = `NATIVE_B`, both reaching `J5` through 100 Ω and a TVS channel |
| no boot-strap regression | **PASS** — GPIO0 `BOOT_N`, GPIO3 `BMI270_INT1_STRAP`, GPIO45 `GPIO45_VDDSPI_STRAP`, GPIO46 `DISP_BL_CTL_STRAP` all unchanged, all with their pulls |
| power-fault signals land correctly | **PASS** — both `FLT` wire-OR to `ACC_POWER_FAULT_N` → `U3` P15 with one 100 kΩ pull-up |
| display / touch / card-detect endpoints intact | **PASS** — `DISP_RST_N` `U2` P04, `TOUCH_RST_N` `U2` P00, `TOUCH_INT_N` `U2` P16, `SD_CARD_DETECT_N` `U2` P07 |
| radios / NFC / audio / IR intact | **PASS** — `CC1101_GDO0` GPIO15, `SX1262_BUSY` GPIO8 (native, as required), `SX1262_DIO1` `U2` P17, `SX1262_RXEN` `U3` P16, `NFC_IRQ` GPIO18, I²S on GPIO39–42, `IR_TX` GPIO16, `IR_RX` GPIO44 |
| component reference uniqueness | **PASS** — 321 components, **0 duplicates**, **0 missing footprints** |

**No check was weakened to pass.** No fake no-connects, no fake power flags and
no pin-electrical-type edits were made. The one `PWR_FLAG` touched
(`#FLG0105`) was **re-created**, not invented: the sheet-09 rebuild had deleted
the design's only GND power-output driver, and restoring it returns the check to
the state it was in, with a note explaining its role so it is never deleted
again.

---

## 3. ERC across the migration

| point | messages | errors | warnings |
|---|---|---|---|
| Beta-DM baseline, before any migration | 45 | 2 | 43 |
| after FBV2-S1-008 | 42 | 1 | 41 |
| **after FBV2-S1-009** | **27** | **0** | **27** |

**The design has zero ERC errors for the first time.** The 27 remaining warnings
are all pre-existing and all previously explained:

- **18 ×** `pin_to_pin` — `J1` unused display data bus tied to GND, which the
  panel datasheet requires verbatim; bidirectional-versus-power-output is a stock
  symbol pin-type artefact.
- **2 ×** `pin_to_pin` — BMI270 `ASDx`/`ASCx` tied to VDDIO, which Bosch requires
  (*"Do not connect to GND"*).
- **1 ×** `pin_to_pin` — MAX98357A exposed thermal pad to GND.
- **6 ×** `unconnected_wire_endpoint` — parked RF/antenna stubs on the certified
  radio modules, marked DO NOT ROUTE.

Measured with the programme's historical metric (errors + warnings, **not**
`--severity-all`).

---

## 4. I²C address map, measured

| address | device | ref | strap |
|---|---|---|---|
| **0x20** | PCAL9535A | `U2` | A0 = A1 = A2 = GND |
| **0x21** | PCAL9535A | `U3` | A0 = `+3V3`, A1 = A2 = GND |
| **0x22** | PCAL9535A | `U23` | A1 = `+3V3`, A0 = A2 = GND |
| **0x36** | MAX17048 fuel gauge | `U14` | fixed |
| **0x38** | FT6236 touch, via `J1` 44/45 | — | fixed in the module |
| **0x68** | BMI270 IMU | `U4` | `SDO` → GND (`R118`) |

**Expected first-article bus scan with no accessory fitted:
`0x20`, `0x21`, `0x22`, `0x36`, `0x38`, `0x68` — and nothing else.**
`0x69` stays reserved as the BMI270 rework address; `0x50` stays reserved for the
optional accessory-ID EEPROM and **is not widened to `0x50`–`0x57`**.

`U16` is a repeater and has no address. **P-18 is closed with no mux**: the two
segments are one address space whenever the accessory rail is on, which is
deliberate — the TCA4307 solves *electrical* fault isolation and the registry
solves *address* allocation.

---

## 5. Expander allocation, measured — 48 pins across three devices

| device | used | spare |
|---|---|---|
| `U2` 0x20 — internal control and user input | **16 / 16** | 0 |
| `U3` 0x21 — community and accessory | **16 / 16** | 0 |
| `U23` 0x22 — status light, reserve, 5 V switch enable | **5 / 16** | **11** |
| **total** | **37 / 48** | **11** |

`U23`: `FRONT_RGB_R/G/B_N` on P00–P02, `RESERVED_SPARE` on P03,
**`ACC_5V_SW_EN` on P04** (new at FBV2-S1-009).

**B-37 is retired.** The programme carried "zero expander spare" from its first
audit until FBV2-S1-008.

---

## 6. What FBV2-S1 does *not* mean

The migration is complete. **The board is not.** Before FBV2-S2:

| # | blocker |
|---|---|
| **P-04** | NFC first-fab inclusion and antenna implementation |
| **B-47** | `J1` FH52E second source and land pattern — **there is currently no JLC assembly path for `J1`** |
| **footprints** | Only the display connector, the microphone, the RGB LED and the community connector have been audited against manufacturer drawings. **Every other footprint remains unverified** (B-03) |
| **PCB** | Placement, routing, outline and the enclosure fit are all untouched, and the inherited outline is **155 × 74 mm against a 160 × 80 target with the fit UNVERIFIED** |
| **O-7** | external I²C pull-up value against measured bus capacitance |
| **B-68 / B-69** | accessory boost inductor I_sat; measured TPS61023 start-up time |
| **B-35 / B-36 / B-46** | `FLT` coverage, accessory wake in sleep, card-detect polarity |
| **assembly** | the BCS-112 is through-hole and may need manual placement on the first five boards |

**Neither FBV2-S2 nor any PCB work was started in this task.**
