# AQROOT Full Beta v2 — measured GPIO ledger (ESP32-S3-WROOM-1-N16R8, `U1`)

**Status: MEASURED.** Every row below is read from
`hardware/beta-v2/kicad/aqroot-beta-v2/` via a `kicad-cli` netlist export, not
transcribed from a pin-map document. Regenerate it the same way before quoting it.

Date: 2026-08-23 (after FBV2-S1-005, I²C devices and IMU migration)
Authority: [`../CTO_DECISIONS.md`](../CTO_DECISIONS.md) outranks this file.

> **Sheets `06`–`09` are still Beta-DM.** A net listed here as leaving sheet `02`
> may terminate on a *Beta-DM* peripheral until that sheet is migrated. Where the
> v2 destination differs, the row says so.

---

## 1. Ledger

`strap` = the pin is sampled at reset and its level changes chip behaviour.
`exposed` = the net reaches the community connector.

| module pin | GPIO | net | subsystem | role | strap | exposed | notes |
|---|---|---|---|---|---|---|---|
| 3 | `EN` | `Net-(U1-EN)` | reset | reset input | — | no | `R1` 10 k to `+3V3`, `C1` 1 µF to GND |
| 27 | **GPIO0** | `BOOT_N` | boot | strap + button | **YES** | no | `R2` 10 k pull-up, `SW1` direct to GND. **No capacitor** — Espressif forbids bulk C here |
| 39 | GPIO1 | `I2C_SDA_INT` | I²C | bidirectional | — | buffered only | internal bus; the connector sees the `U16` B-side, never this net |
| 38 | GPIO2 | `I2C_SCL_INT` | I²C | output | — | buffered only | as above |
| 15 | **GPIO3** | `BMI270_INT1_STRAP` | IMU | interrupt in | **YES** | no | **`R110` 10 k pull-down** + `R18` 220 Ω series + `TP3`. Closes **B-09**. **FBV2-S1-005: also `RTC_GPIO3`, so EXT0/EXT1 deep-sleep wake works; `INT1` must be push-pull active-high, open-drain FORBIDDEN (D-137)** |
| 4 | GPIO4 | `SPI_B_SCK` | SPI-B | output | — | no | radios + NFC bus |
| 5 | GPIO5 | `SPI_B_MOSI` | SPI-B | output | — | no | |
| 6 | GPIO6 | `SPI_B_MISO` | SPI-B | input | — | no | |
| 7 | GPIO7 | `CC1101_CS_N` | sub-GHz | output | — | no | |
| 12 | GPIO8 | `SX1262_BUSY` | LoRa | input | — | no | |
| 17 | GPIO9 | `NFC_CS_N` | NFC | output | — | no | |
| 18 | GPIO10 | `DISP_CS_N` | display | output | — | no | |
| 19 | GPIO11 | `SPI_A_MOSI` | SPI-A | output | — | no | display + microSD |
| 20 | GPIO12 | `SPI_A_SCK` | SPI-A | output | — | no | |
| 21 | GPIO13 | `SPI_A_MISO` | SPI-A | input | — | no | |
| 22 | GPIO14 | `DISP_DC` | display | output | — | no | |
| 8 | GPIO15 | `CC1101_GDO0` | sub-GHz | input | — | no | |
| 9 | GPIO16 | `IR_TX_GPIO16` | IR | output | — | no | low-side NMOS drive |
| 10 | GPIO17 | `SX1262_CS_N` | LoRa | output | — | no | |
| 11 | GPIO18 | `NFC_IRQ` | NFC | input | — | no | **must never move to GPIO46** (B-19). Confirmed still here |
| 13 | GPIO19 | `USB_D_MCU_N` | USB | native USB D− | — | no | USB Serial/JTAG |
| 14 | GPIO20 | `USB_D_MCU_P` | USB | native USB D+ | — | no | USB Serial/JTAG |
| 23 | GPIO21 | `WAKE_INT_N` | expanders | interrupt in | — | via gate | wire-OR of both expander `INT` pins, `R3` 10 k pull-up. **Not** a strapping pin |
| 28 | GPIO35 | — | — | **UNUSABLE** | — | no | octal PSRAM (N16R8). NC |
| 29 | GPIO36 | — | — | **UNUSABLE** | — | no | as above |
| 30 | GPIO37 | — | — | **UNUSABLE** | — | no | as above |
| 31 | **GPIO38** | **`NATIVE_A`** | community | bidirectional | — | **YES** | **CHANGED FBV2-S1-002.** Was `SX1262_DIO1` |
| 32 | GPIO39 | `I2S_BCLK` | audio | output | — | no | also MTCK — external JTAG is therefore unusable |
| 33 | GPIO40 | `I2S_LRCLK` | audio | output | — | no | also MTDO |
| 34 | GPIO41 | `I2S_SPK_DOUT` | audio | output | — | no | also MTDI |
| 35 | GPIO42 | `I2S_MIC_DIN` | audio | input | — | no | also MTMS |
| 37 | **GPIO43** | `UART0_TXD_DBG` | debug | output | — | **NO (withdrawn)** | **CHANGED FBV2-S1-002.** Was `FAST_IO_U0TXD_ROOTPROBE_CS` on the connector. Now internal only, `TP35` |
| 36 | GPIO44 | `IR_RX_GPIO44` | IR | input | — | no | U0RXD is consumed by IR, so UART0 is **TX-only** |
| 26 | **GPIO45** | `GPIO45_VDDSPI_STRAP` | VDD_SPI | strap | **YES** | no | `TP1`. **`R111` 10 k pull-down FITTED (D-111)** — see §3 |
| 16 | **GPIO46** | `DISP_BL_CTL_STRAP` → `R109` → `DISP_BL_CTL` | display | output | **YES** | no | **CHANGED FBV2-S1-002.** `R108` 10 k pull-down + `R109` 0 Ω isolation link + `TP2` |
| 25 | GPIO48 | `SD_CS_N` | microSD | output | — | no | |

**33 of 33 usable pins are assigned. Zero free native GPIO — B-10 stands.**
GPIO35/36/37 are unusable on the R8 (octal PSRAM) part and stay NC.

**No duplicate assignment exists.** Verified by netlist: every `U1` pin resolves to
exactly one net, and no net name appears on two `U1` pins.

---

## 2. Community exposure

Only **two** native pins reach the connector, and both are now the ones the
architecture intends:

| contact | net | GPIO |
|---|---|---|
| `NATIVE_A` | `NATIVE_A` | **GPIO38** |
| `NATIVE_B` | `NATIVE_B` | **GPIO47** |

`GPIO43` is **withdrawn** (D-106). Every other community contact is an expander
`XGPIO`, the buffered I²C pair, `WAKE_ATTN_N`, `ACC_DETECT_N`, or power.

> D-090's protection — 100 Ω series on both native pins plus the low-capacitance
> TVS array — belongs physically next to the connector and is therefore **sheet
> `09` work**. It does not exist yet. Until it does, `NATIVE_A` / `NATIVE_B` run
> from the MCU to a sheet-`09` boundary that has not been drawn.

---

## 3. Strapping-pin audit

ESP32-S3 samples GPIO0, GPIO3, GPIO45 and GPIO46 at reset. Espressif specifies
setup ≥ 0 ms and **hold ≥ 3 ms** after reset release, and warns explicitly against
bulk capacitance on strapping pins.

| pin | required reset state | external pull | peripheral on the net | can the peripheral overpower the strap? | recovery consequence |
|---|---|---|---|---|---|
| **GPIO0** | HIGH for SPI boot, LOW for download | `R2` 10 k to `+3V3`; `SW1` shorts to GND | none | no — nothing else drives it | held LOW at reset → Joint Download Boot. This is the deliberate recovery entry |
| **GPIO3** | **LOW** | **`R110` 10 k to GND** | BMI270 `INT1` through `R18` 220 Ω | **PROVEN not at reset (FBV2-S1-005)** — `INT1_IO_CTRL` resets to `0x00` so the output driver is *disabled*; firmware cannot enable it before the 8 kB config upload; and ESP32-S3 `tH` = 3 ms with GPIO3 defaulting to *Floating*. **The IMU cannot reach the strap window**, and `R110` alone defines the level | LOW selects the **USB Serial/JTAG** source when `EFUSE_STRAP_JTAG_SEL` is burned. HIGH would select external JTAG on MTMS/MTDI/MTCK/MTDO = **GPIO39–42, which are the I²S bus** — external JTAG is not merely unused here, it is unusable |
| **GPIO45** | **LOW** (VDD_SPI = 3.3 V) | **`R111` 10 k to GND, FITTED (D-111)** | none — `TP1` only | n/a | HIGH at reset would select VDD_SPI = 1.8 V and the 3.3 V flash/PSRAM would not boot. **The level is now held deterministically by `R111`, not by the chip's internal pull-down alone.** No capacitance on the net; no peripheral on the pin |
| **GPIO46** | **LOW** | **`R108` 10 k to GND (new)** | TPS61169 `CTRL` (`U17.4`), through **`R109` 0 Ω** | **NO — proven.** `CTRL`'s only internal element is a **300 kΩ pull-down** (SNVSA40B, D-116) | HIGH at reset makes **Joint Download Boot unreachable**: GPIO0 = 0 alone is not enough, GPIO46 must also be 0 |

### GPIO46 — why 10 kΩ, and why the 0 Ω link

`DISP_BL_CTL` had to move off GPIO47 so GPIO47 could become `NATIVE_B`. GPIO46 is
the only pin left, and it is a strapping pin, so the backlight line now shares a
node that must read **LOW** at reset.

Three things make that safe:

1. **`R108` 10 kΩ pull-down at the MCU pin.** This is the value Espressif's own
   hardware design guidelines call "a strong pull-down" against the chip's 45 kΩ
   internal pull. GPIO46 reads LOW even in the worst case.
2. **`R109` 0 Ω FIT in series to `U17` `CTRL`.** Its original justification — a
   no-respin escape against an unknown `CTRL` pull — is **retired**: `CTRL` is now
   known to contain a **300 kΩ internal pull-down and nothing else**, so it can only
   pull GPIO46 *down*. `R109` is retained because a fitted 0 Ω costs nothing and
   remains a general isolation and rework point. With `R108` in parallel the node
   sees **9.68 kΩ to GND**, and the backlight is off through reset by construction.
3. **`TP2` probes the strap node directly**, so the level is measurable on the
   first board rather than inferred.

**Quantified:** for GPIO46 to read LOW it must sit below `V_IL` = 0.25 × 3.3 V =
0.825 V. With `R108` = 10 kΩ, any internal pull-up on `CTRL` of **≥ 30 kΩ** keeps
the node below that. `CTRL` leakage of ±1 µA moves the node by only ±10 mV.

> **`B-43` CLOSED 2026-08-23 (D-116).** The TPS61169 datasheet **SNVSA40B** specifies
> **`R_PD`, a 300 kΩ internal pull-down on `CTRL`**, with `V_H`/`V_L` = 1.2 / 0.4 V and
> `t_SD` = 2.5 ms. **`CTRL`'s only internal element pulls DOWN — there is no mechanism by
> which the backlight driver can raise the strap**, so GPIO46 safety is proven by
> construction rather than bounded by margin. With `R108` in parallel the node sees
> **9.68 kΩ to GND**, and the backlight is off through reset. `R109` is retained as a
> general isolation and rework point, no longer as the strap defence.

### GPIO3 — the pull-down and the BMI270

With `R110` = 10 kΩ and `R18` = 220 Ω in series, a BMI270 driving `INT1` high must
source 3.3 V / 10.22 kΩ ≈ **323 µA**, and GPIO3 then sits at **3.23 V**, comfortably
above `V_IH` = 0.75 × 3.3 V = 2.475 V.

**This requires `INT1` to be configured push-pull, active-high** — `INT1_IO_CTRL`
with `output_en` = 1, `od` = 0, `lvl` = 1. Open-drain is *incompatible* with a
pull-down and must not be used on this pin.

> **CONFIRMED FROM THE DATASHEET 2026-08-23 (FBV2-S1-005, D-137).** This requirement was
> written here at FBV2-S1-002 from the pull direction alone. It is now backed by the register
> definition: `INT1_IO_CTRL` bit 2 `od` selects push-pull (0) or open-drain (1) and bit 1 `lvl`
> selects active-low (0) or active-high (1), and the register **resets to `0x00`** — which also
> means bit 3 `output_en` = 0, so the pin is high-Z at power-on. It is now a **mandatory
> firmware contract**, recorded on sheet `05` as well as here.

> **`B-44` CLOSED 2026-08-23 (FBV2-S1-005).** `BST-BMI270-DS000-08` Rev 1.6 Table 1 specifies
> the output pads at **`IOH`/`IOL` ≤ 2 mA with `VOH` ≥ 0.8·VDDIO and `VOL` ≤ 0.2·VDDIO**, so
> the 323 µA load is **6× inside spec** and the 47 kΩ fallback below is not needed. The
> original text is kept for the record:
>
> > **`B-44` — the BMI270 `INT` pad drive current was NOT retrieved** (Bosch PDF text
> > layer would not extract). 323 µA is modest for a CMOS pad but is unconfirmed.
> > **Fallback if Bosch specifies less: raise `R110` to 47 kΩ** (70 µA) — a value
> > change with no board change. Confirm at FBV2-S2.

---

## 4. Interrupt and wake architecture

| source | net | lands on | strap risk |
|---|---|---|---|
| both GPIO expanders | `WAKE_INT_N` | GPIO21 | none — GPIO21 is not a strapping pin |
| NFC (`ST25R3916`) | `NFC_IRQ` | GPIO18 | none. **B-19 holds: it must never move to GPIO46**, where a latched-high IRQ would make ROM-download recovery conditional on NFC state |
| LoRa (`SX1262`) | `SX1262_BUSY` | GPIO8 | none |
| LoRa `DIO1` | `SX1262_DIO1` | **no longer the MCU** — routes to the internal expander `U2` (D-089) | n/a |
| sub-GHz (`CC1101`) | `CC1101_GDO0` | GPIO15 | none |
| IMU (`BMI270`) | `BMI270_INT1_STRAP` | GPIO3 | **strap pin** — defined by `R110`, and the IMU is high-Z at reset |
| touch (`FT6236`) | **`TOUCH_INT_N`** — panel pin 46 | **not the MCU** — an internal PCAL9535A input (sheet `08`) | **captured 2026-08-23 (FBV2-S1-003).** Not represented at all on Beta-DM |

**LoRa deep-sleep packet wake remains NOT REQUIRED** (D-041). No GPIO was remapped
to gain RTC wake capability, and none should be.

**No interrupt sits on a strapping pin in a way that can block recovery.** The one
interrupt that does share a strapping pin — the IMU on GPIO3 — is high-impedance at
reset, so it cannot corrupt the strap, and GPIO3 does not gate boot mode at all.

**No user-accessory signal controls a dangerous strap state.** The only two
connector contacts with a direct MCU path are `NATIVE_A` (GPIO38) and `NATIVE_B`
(GPIO47); neither is a strapping pin. `GPIO43`'s withdrawal removed the last
connector-reachable pin that was adjacent to the debug UART.

---

## 5. Service and debug access

| provision | where | why it is enough |
|---|---|---|
| **Native USB Serial/JTAG** on GPIO19/20 | `U1` pins 13/14 → `J3` USB-C | one cable gives console, ROM download **and** JTAG debug. No external debug probe, no FTDI, no JTAG header |
| **`SW1` BOOT** | sheet `02` | electrically real; the product requirement is that it is **mechanically recessed/hidden**, not removed |
| **`TP35` UART0 TXD** *(new)* | GPIO43 | the ROM boot log at 115200 baud is the **only** view of a first board whose USB does not enumerate. This does not duplicate USB — it is what you use when USB is the thing that is broken |
| **`TP1` / `TP2` / `TP3`** | GPIO45 / GPIO46 / GPIO3 | all three strapping pins are measurable |
| **`TP4` / `TP5`** | I²C SDA / SCL | internal bus observable |

**No new debug connector, no new debug IC, and no new user-facing button.** UART0
RX is unavailable (GPIO44 is IR RX), which is acceptable precisely because ROM
download recovery runs over USB Serial/JTAG rather than UART0 — recorded so nobody
later assumes a UART download path exists.

An `EN` test pad was **considered and rejected**: reset can be asserted over USB
Serial/JTAG and by power-cycling, so the pad would be a part with no unique use.
