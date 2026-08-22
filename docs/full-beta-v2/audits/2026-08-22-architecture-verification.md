# AQROOT Full Beta v2 — Architecture Verification Audit

Date: 2026-08-22
Task: FBV2-ARCH-001 — lock architecture direction and verify high-risk blockers
Repository HEAD at audit: `890db0b` (documentation commit, pushed to `origin/master`)
Scope: **documentation only.** No schematic, PCB, fabrication, BOM, CPL, mechanical or firmware file was modified.

---

## 0. Sources used

Every verdict below is traced to one of these. Where a document could not be
obtained or a value could not be read cleanly, that is stated rather than
inferred.

| # | document | revision / date | how obtained |
|---|---|---|---|
| S1 | **ST25R3916/7 datasheet**, "High performance NFC universal device and EMVCo reader" | **DS12484 Rev 3**, 04-Jun-2020 | already in repo: `hardware/beta/kicad/aqroot-beta/vendor/ST25R3916/` |
| S2 | **ESP32-S3 Series Datasheet** | **v2.2** | espressif.com |
| S3 | **TPS61023 datasheet** | **SLVSF14B**, Sept 2019, rev Aug 2020 | ti.com |
| S4 | **TCA9517A datasheet** | **SCPS245E**, Dec 2012, rev **Oct 2025** | ti.com |
| S5 | **TPS22918 datasheet** | SLVSDS8 | ti.com |
| S6 | **BQ25185 datasheet** | **SLUSF65A**, Oct 2023, rev **Jan 2026** | ti.com |
| S7 | LTC4368 product page / datasheet summary | Rev C | analog.com (search summary — **full datasheet fetch timed out**) |

**S7 is weaker evidence than S1–S6.** The LTC4368 numbers below come from
Analog Devices' own product page and datasheet summary, not from a page-cited
read of the datasheet PDF. Every LTC4368 figure is marked accordingly, and the
`-1` vs `-2` variant difference is explicitly **not** resolved.

---

## A. CTO-ruling implementation record

All rulings A–K recorded. Where verification contradicts a ruling, the ruling is
recorded **as issued** and the contradiction is raised as a pending decision —
this document does not silently overwrite a CTO ruling.

| ruling | recorded as | status |
|---|---|---|
| **A** — 20 pins, C2 provisional, protocol capability over pin count | D-046, D-047, D-048 | Recorded. C2 **not** frozen — see §B, which changes which pin is reclaimed. |
| **B** — remove HOME; Volume never existed; keep D-pad/A/B/Power/BOOT; BOOT electrically real, recessed; ROM-download ≠ OTA recovery | D-010…D-017 (already locked), D-018 added | Recorded. §B finds a proposal that would have **broken** the BOOT recovery path; rejected. |
| **C** — keep ICS-43434 and real speech out; MAX98357A preferred; evaluate EMI/current/gain/cavity | D-026 | Recorded, unchanged. |
| **D** — IR TX+RX mandatory, populated in first fab, stays internal; SYS-fed IR drive is a direction not a lock | D-033, D-034 | Recorded, unchanged. |
| **E** — NFC mandatory in first fab, no DNP shortcut; core coherent with 3.3 V, boost only the TX/PA rail; pin-to-rail not locked until verified | D-035, D-036 | Recorded. **Verification finds the rail split is prohibited by the datasheet** — see §D. Raised as P-10. |
| **F** — remove the dangling RGB architecture, free the expander resources | D-037 | Recorded. Closes P-05. |
| **G** — retire the dedicated RootProbe IRQ, keep FAST_IO capability | D-038 | Recorded. Closes P-06. |
| **H** — investigate freed expander pins for STAT1/STAT2, verify first, do not wire | D-039 | Recorded. See §G. |
| **I** — prefer IPEX → pigtail → bulkhead; no new controlled-impedance RF on the main PCB | D-040 | Recorded. Closes P-08. |
| **J** — LoRa deep-sleep packet wake is not a v2 requirement; do not remap for it | D-041 | Recorded. Closes P-09. **This ruling is what makes the §B substitution free.** |
| **K** — mechanical freeze before placement/routing; 160×80×23 external only | D-060…D-063 (already locked), reaffirmed | Recorded, unchanged. P-07 stays open. |

---

## B. C2 GPIO reclaim verdict

### VERDICT: **FAIL as proposed.** Substitute reclaim: **PASS WITH CIRCUIT CONDITION.**

The proposal was `NATIVE_B` = GPIO18, reclaimed by moving `NFC_IRQ` to GPIO46.
**That specific move must not be made.** A substitute reclaim achieves the same
architectural goal with no loss.

### B.1 What the ESP32-S3 documentation actually says

**S2, §3 "Boot Configurations", Table 3-1 "Default Configuration of Strapping Pins" (p. 32):**

| strapping pin | default configuration | bit value |
|---|---|---|
| GPIO0 | Weak pull-up | 1 |
| GPIO3 | **Floating** | — |
| GPIO45 | Weak pull-down | 0 |
| GPIO46 | Weak pull-down | 0 |

GPIO46 carries **two** boot parameters (S2 §3, p. 32): *chip boot mode* (with
GPIO0) and *ROM message printing*.

**S2, §3.1, Table 3-3 "Chip Boot Mode Control" (p. 33):**

| boot mode | GPIO0 | GPIO46 |
|---|---|---|
| SPI boot mode (default) | 1 | **Any value** |
| Joint download boot mode | 0 | **0** |

**S2, §3, Table 3-2 (p. 33):** hold time `tH` **minimum 3 ms** — "the time
reserved for the chip to read the strapping pin values after CHIP_PU is already
high and before these pins start operating as regular IO pins."

**S2, §3 (p. 32):** "All strapping pins have latches… the pins are freed up to
be used as regular IO pins after reset."

### B.2 Why NFC_IRQ on GPIO46 fails

**S1 confirms the ST25R3916 IRQ is a push-pull, ACTIVE-HIGH output** (S1, Table 2
p. 20 lists IRQ as type `DO`; S1 §4.3.1 "Interrupt interface" and the register
tables state "Active high - Interrupt output pin").

**S1 §4.3.1:** "The IRQ pin transitions to low after the interrupt bit(s) that
caused its transition to high [are read]." IRQ is cleared **only by an SPI read
of the interrupt registers.**

The failure chain:

1. The ST25R3916 has **no reset input**. Confirmed from the measured pad map —
   U9 has no reset pin, and S1 Table 2 lists none. It is reset only by a `Set
   Default` command over SPI, or by removing its supply.
2. Therefore an asserted IRQ **survives an ESP32 reset**. A watchdog reset, a
   crash, or a user-initiated reset while a card is in the field all leave IRQ
   HIGH with no MCU to clear it.
3. In normal boot this is harmless — Table 3-3 says GPIO46 is "Any value" when
   GPIO0 = 1.
4. **But the recovery path is exactly the case where GPIO0 = 0.** When the user
   holds the recessed BOOT button to enter Joint Download Boot, GPIO46 **must**
   be 0. A latched-high NFC IRQ holds it at 1 and the chip boots SPI instead of
   download.

**This makes the last-resort hardware recovery path conditional on NFC
interrupt state.** That directly violates CTO ruling B, which requires physical
BOOT to remain electrically real. It is not an acceptable residual risk: recovery
must work when everything else has failed, and "everything else has failed" is
precisely when a stale NFC interrupt is most likely to be latched.

A resistor divider cannot rescue it. IRQ is push-pull; any pull-down strong
enough to hold GPIO46 low against a driven high would also prevent the pin from
ever reading the interrupt, which is the entire purpose of the connection.

**GPIO45 is not an alternative either.** S2 §3.2, Table 3-4 (p. 33): with the
default `EFUSE_VDD_SPI_FORCE` = 0, GPIO45 = 1 selects the 1.8 V Flash Voltage
Regulator for VDD_SPI. An external device driving GPIO45 high at reset makes the
module fail to boot.

### B.3 The substitute reclaim — recommended

**Move `DISP_BL_CTL` from GPIO47 to GPIO46. Expose GPIO47 as `NATIVE_B`.**

Why this is safe, and better:

| property | evidence |
|---|---|
| Backlight control **idles low** = backlight off | The net drives U17 TPS61169 CTRL. Off is both the correct strap value (0) and the correct safe state. GPIO46's internal **weak pull-down** (S2 Table 3-1) already holds it there before firmware runs. |
| Nothing external fights the pin | The net's only other node is the boost CTRL input. No second driver exists, so the 3 ms `tH` window is trivially satisfied. |
| Recovery is unaffected | Whether GPIO0 is 0 or 1, backlight state is irrelevant to boot mode, and it is 0 either way. |
| ROM-message routing unaffected | GPIO46 = 0 is the default configuration. |
| GPIO47 is a **better** exposed pin than GPIO18 | S2 §2.3.5: GPIO47 is **Priority 2** — "GPIO pins can be freely used without restrictions." GPIO18 is also P2, but see below. |
| GPIO47 has **no power-up glitch** | S2 Table 2-2 "Power-Up Glitches on Pins" (p. 18–19) lists GPIO1–14, XTAL_32K_P/N, GPIO17, GPIO18, GPIO19, GPIO20. **GPIO47 is not in the table.** |
| GPIO18 **does** have a power-up glitch | S2 Table 2-2: GPIO18 has **both** a low-level glitch **and a high-level glitch**, ~60 µs each. A 60 µs high pulse on a connector pin can clock or trigger an accessory. |
| GPIO47 drive strength is 20 mA vs GPIO18's 10 mA | S2 §2.2 note 5 (p. 17): "GPIO17 and GPIO18: 10 mA; GPIO19 and GPIO20: 40 mA; all other pins: 20 mA." |
| 3.3 V operation confirmed for our part | S2 §2.2 note 4 (p. 17): GPIO47/48 run at 1.8 V **only** on the ESP32-S3**R8V**/**R16V** variants. Ours is **ESP32-S3-WROOM-1-N16R8** — not a V variant — so VDD_SPI is 3.3 V and GPIO47 is a 3.3 V pin. |

**The only thing given up is RTC capability** (GPIO47 is outside the GPIO0–21 RTC
range, so an accessory cannot use it as an `ext0`/`ext1` deep-sleep wake source).
That costs nothing, because `WAKE_ATTN_N` on GPIO21 is already the RTC-capable
accessory wake line, and **CTO ruling J removed deep-sleep wake as a driver for
pin remapping.**

### B.4 Circuit conditions attached to the PASS

1. **External pull-down on `DISP_BL_CTL`/GPIO46**, in addition to the internal
   weak pull-down, so the strap level does not depend on an internal pull whose
   value the datasheet does not guarantee over the full reset window.
2. **Series resistor + connector-side ESD on `NATIVE_B`/GPIO47**, matching the
   `FAST_IO` treatment.
3. **Publish the accessory rule** that `NATIVE_B` is undriven and floating until
   firmware configures it.
4. **`NFC_IRQ` stays on GPIO18.** No NFC pin moves.

### B.5 Consequence for the C2 map

C2 is unchanged in shape — 10 XGPIO, 2 native, I²C, WAKE, ACC_3V3_SW, +3V3,
3 GND = 20 pins. Only the identity of `NATIVE_B` changes: **GPIO47, not GPIO18.**

`NATIVE_A` = GPIO43 is unchanged and remains valid (S2 §2.3.5 lists GPIO43/44 as
P3, "UART0 interface", which is exactly the documented `FAST_IO / U0TXD` caveat
already published).

**Note on the accessory-UART idea from the prior audit:** it was premised on
GPIO18 being P1 for `U1RXD`. With GPIO47 as `NATIVE_B`, a hardware UART is still
reachable through the GPIO matrix (S2 §2.3.5, P2), but not via a fixed IO MUX
pin. This is a small loss and should be stated honestly in accessory
documentation rather than marketed as a first-class UART.

---

## C. Reverse-polarity comparison and recommendation

### C.1 The constraint that eliminates most textbook answers

The protected node is **bidirectional**. `BAT_PROTECTED_P` must carry current
*into* the cell when charging and *out of* the cell when discharging. Any
series diode, any single MOSFET with a conducting body diode, and any
unidirectional ideal-diode or eFuse controller therefore either blocks charging
or fails to block a reversed cell in one of the two directions.

This is not a preference — it is why the block was left undrawn. **Back-to-back
(common-source or common-drain) FETs, or a device that integrates them, are
mandatory.**

The mandatory fault case — *reversed battery while USB powers the system* — also
rules out any scheme whose gate drive derives only from the battery, because
with USB present the system rail is alive and will attempt to push current into
a reversed cell.

### C.2 Candidates

| | **X1 — LTC4368-1 + back-to-back N-FETs** | **X2 — discrete back-to-back N-FETs, gate driven from SYS** | **X3 — reverse-current-blocking load switch (TPS2291x class)** |
|---|---|---|---|
| Operating voltage | **2.5 V – 60 V** operating; survives −40 V to 100 V (S7) | Set by FET V<sub>GS(th)</sub> and gate clamp; works across 2.5–4.35 V with logic-level FETs | 1.4 V – 5.5 V (TI TPS22910A/TPS2291x family) |
| Reverse battery | Controller detects negative input, holds both gates off | Source goes negative, V<sub>GS</sub> cannot reach V<sub>th</sub>, both FETs off | Reverse-voltage comparator disables the switch |
| Reverse-current blocking | **Yes, both directions** (two FETs) | **Yes, both directions** | **Yes** — TI states reverse current protection is "always active, even when the power-switch is disabled" |
| USB present + reversed battery | Blocked — controller holds gates off regardless of which side is powered | Blocked — gate reference cannot forward-bias either FET onto a negative source | Blocked, but **see the disqualifier below** |
| Voltage drop | 2 × R<sub>DS(on)</sub>; ~20–40 mΩ total with common logic-level duals | Same, 2 × R<sub>DS(on)</sub> | Single P-FET R<sub>DS(on)</sub>, typically higher at 1S voltages |
| Quiescent current | **~80 µA operating, ~5 µA shutdown** (S7) | **Sub-µA** — gate resistors and leakage only | ~1–10 µA class |
| Part count | Controller + dual N-FET + ~6 passives ≈ 8 | Dual N-FET + 2–3 resistors + gate-clamp zener ≈ 5 | 1 IC + 2 passives ≈ 3 |
| Approx. PCB area | Largest — MSOP/DFN controller plus FETs | Small — one SOT-23-6/DFN dual FET plus 0402s | Smallest |
| Thermal | Negligible at ≤1.5 A with low R<sub>DS(on)</sub> | Negligible | Highest of the three per amp |
| Interrupts both directions | **Yes** | **Yes** | Yes, but unidirectional by architecture |
| Startup | Controlled; controller sequences the gates | **Self-starting**: on first insertion the FET body diodes conduct BAT→SYS at one diode drop, SYS comes up, SYS then enhances the gates | Controlled |
| Availability / package | MSOP-10 / DFN; ADI, higher unit cost | Very high — commodity dual N-FET | High — TI TPS22910A / TPS22912C / TPS22913B/C |
| Failure modes | Controller failure can latch the battery off; 80 µA is a permanent standby load; `-1`/`-2` behaviour **unresolved** | Gate-clamp or resistor failure can leave the pair permanently on (no protection) or permanently off (no battery); needs careful V<sub>GS(max)</sub> design | **Disqualified — see below** |
| Suitable ahead of BQ25185? | Yes | Yes | **No** |

### C.3 Why X3 is disqualified despite being the neatest part

A reverse-current-blocking load switch blocks current from V<sub>OUT</sub> back to
V<sub>IN</sub>. Placed between the connector and the charger's BAT pin, that is
precisely the **charging** direction. It would protect the reversed-battery case
and simultaneously prevent the cell from ever charging. It is the right part for
the accessory rail (§F) and the wrong part for a battery node.

This is recorded because it is an easy and expensive mistake to make: the part
looks ideal on its datasheet and is wrong for this position for a structural
reason.

### C.4 Recommendation

**Recommend X2 — a discrete back-to-back N-channel pair with a gate drive
referenced to the system rail — as the primary architecture, with X1 (LTC4368-1)
retained as the fallback if the CTO wants integrated UV/OV and fault latching.**

Reasoning:

1. **Quiescent current.** X2 costs sub-µA. X1 costs ~80 µA continuously (S7). The
   standby budget is already unmeasured and already suspected to be an order of
   magnitude worse than the ~10–20 µA chip figure. Adding a known 80 µA to an
   unknown baseline is the wrong direction for a device whose headline is
   ~2-week standby.
2. **Voltage headroom.** LTC4368's 2.5 V minimum (S7) sits uncomfortably close to
   a deeply-discharged protected pack. X2's behaviour degrades gracefully instead
   of hitting a controller UVLO.
3. **Part count and area** favour X2, and the first fabrication is the wrong place
   to spend area on features nobody has asked for.
4. **X2 is self-starting** through the body diodes, so a flat unit with a fresh
   cell and no USB still comes up.

**Both X1 and X2 need design work that has not been done**: gate V<sub>GS(max)</sub>
clamping, behaviour during the charge direction when SYS > BAT, ESD at the
connector, and an explicit reversed-battery-with-USB bench test.

### C.5 Flagged for independent Claude CTO second opinion

**This recommendation is explicitly flagged for a second opinion, as instructed.**
The three specific things a reviewer should attack:

1. Whether a discrete gate-drive scheme can be made robust across the full
   2.5–4.35 V cell range **and** the charge direction without a controller.
2. Whether the 80 µA LTC4368 penalty is actually material once the real standby
   budget is measured — if system standby turns out to be ~1 mA, 80 µA is noise
   and X1's robustness wins.
3. Whether the `-1` vs `-2` variant difference (latch-off vs auto-retry)
   changes the recommendation. **This audit could not resolve that difference**
   — the datasheet fetch timed out and the search result's claim was an
   inference from the LTC4366 family, not a verified LTC4368 statement.

### C.6 Non-electrical control that must be recorded alongside it

`J4` is a **JST PH**, which is mechanically keyed. The realistic reversal risk is
not a user plugging the connector in backwards — it is a pack assembled with the
wires crimped into the wrong housing positions. The electrical protection is
defence-in-depth; **pack sourcing and an incoming-inspection polarity check are
the first line** and should be written into the build documentation regardless of
which architecture is chosen.

---

## D. NFC rail / pin table

### D.1 The pin map is verified — and it is correct as built

The prior audit reconstructed U9's pin numbering from a layout-mangled table
extraction. That reconstruction is now **cross-validated against three
independent tables in S1** — Table 2 (pin assignment, p. 20–21), Table 118
(absolute maximum ratings, p. 135) and Table 119 (operating conditions, p. 136),
the latter two of which cite pin *numbers* directly.

| pin | name | type | purpose | required voltage | as built |
|---|---|---|---|---|---|
| 1 | **VDD_IO** | P | Supply level for the digital communication pins | **1.65 – 5.5 V** (S1 T119) | `+3V3` ✓ |
| 2 | CSO | AO | Capacitor sensor output / test output 2 | 3 V domain, 0–5.5 V | `*_TBD` |
| 3 | **VDD_D** | AO | Digital supply **regulator output** — decouple, do not drive | — | local net ✓ |
| 4 | XTO | AO | Crystal oscillator output | 3 V domain | `*_TBD` |
| 5 | XTI | AI/DI | Crystal oscillator input | 3 V domain | `*_TBD` |
| 6 | GND_D | P | Digital ground | 0 V | `GND` ✓ |
| 7 | **VDD_A** | AO | Analog supply **regulator output** — decouple, do not drive | — | local net ✓ |
| **8** | **VDD** | **P** | **Main supply.** Feeds VDD_A + VDD_D regulators | **2.4 – 5.5 V** (S1 T119) | boosted rail |
| 9 | **VDD_RF** | AO | Regulated driver supply, **regulator output** | 5 V domain | local net ✓ |
| **10** | **VDD_TX** | **P** | **Transmitter supply.** Feeds VDD_RF + VDD_AM regulators | **2.4 – 5.5 V** (S1 T119) | boosted rail |
| 11 | **VDD_AM** | AO | Regulated AM-modulation driver supply, **regulator output** | 5 V domain | local net ✓ |
| 12 | GND_DR | P | Antenna driver ground | 0 V | `GND` ✓ |
| 13 | RFO1 | AO | Antenna driver output | 5 V domain | `*_TBD` |
| 14 | **VDD_DR** | P | Antenna driver **positive supply input** | 5 V domain | tied to `NFC_VDD_RF` ✓ **correct** |
| 15 | RFO2 | AO | Antenna driver output | 5 V domain | `*_TBD` |
| 16 | GND_DR | P | Antenna driver ground | 0 V | `GND` ✓ |
| 17 | EXT_LM | AO | External load-modulation gate driver | 5 V domain | `*_TBD` |
| 18 | AAT_A | AO | AAT tune voltage for variable capacitor A | 3 V domain | `*_TBD` |
| 19 | AAT_B | AO | AAT tune voltage for variable capacitor B | 3 V domain | `*_TBD` |
| 20 | **I2C_EN** | DI | Interface select | 5 V domain | **`GND` = SPI mode ✓ correct** |
| 21 | VSS | P | Substrate ground | 0 V | `GND` ✓ |
| 22 | RFI1 | AI | Receiver input | 3 V domain | `*_TBD` |
| 23 | RFI2 | AI | Receiver input | 3 V domain | `*_TBD` |
| 24 | AGDC | AIO | Analog reference voltage | 3 V domain | local net ✓ |
| 25 | CSI | AIO | Capacitor sensor input / test output 1 | 3 V domain | `*_TBD` |
| 26 | GND_A | P | Analog ground | 0 V | `GND` ✓ |
| 27 | IRQ | DO | **Active-high** interrupt output | VDD_IO domain | `NFC_IRQ` ✓ |
| 28 | MCU_CLK | DO | Clock output for MCU | VDD_IO domain | `*_TBD` |
| 29 | BSS | DI | SPI enable (active low) | VDD_IO domain | `NFC_CS_N` ✓ |
| 30 | SCLK | DI | SPI clock | VDD_IO domain | `SPI_B_SCK` ✓ |
| 31 | MOSI | DI | SPI data input | VDD_IO domain | `SPI_B_MOSI` ✓ |
| 32 | MISO | DO_T | SPI data output | VDD_IO domain | `SPI_B_MISO` ✓ |
| 33 | thermal pad | P | — | 0 V | `GND` ✓ |

Cross-check evidence from S1 Table 119: *"Positive supply voltage (**pins 8 and
10**)"*; *"Peripheral communication supply voltage (**pin 1**)"*; *"Negative
supply voltage (**pins 6, 12, 16 and 26**)"*; *"peripheral IO communication pins
(**27 to 32**)"*; 5 V-domain pins *"9, 11, 13, 14, 15, 17, and 20"*; 3 V-domain
pins *"2 to 5, 7, 18, 19 and 22 to 25"*. Every one matches the table above.

### D.2 **The CTO's stated NFC direction cannot be implemented**

**S1, §"Power supply system" (p. 39):**

> "The ST25R3916/7 features three positive supply pins, VDD, VDD_TX and VDD_IO:
> — VDD is the main power supply pin. It supplies the ST25R3916/7 blocks through two regulators (VDD_A, VDD_D)
> — VDD_TX is the transmitter supply pin. It supplies the transmitter via two regulators (VDD_RF, VDD_AM). VDD range from 2.4 to 5.5 V is supported. **VDD and VDD_TX must be connected to the same power supply.**"

And quantitatively:

| parameter | limit | source |
|---|---|---|
| **VDD − VDD_TX**, absolute maximum | **−0.3 to +0.3 V** | S1 Table 118, p. 135 |
| **VDD − VDD_TX**, operating | **−0.2 to +0.2 V** | S1 Table 119, p. 136 |

CTO ruling E asks for the digital/core supply to stay on 3.3 V while only the
transmitter/PA rail is boosted. On this part, the core supply is **VDD** and the
transmitter supply is **VDD_TX**, and they must be within **±0.2 V** of each
other. Splitting them 3.3 V / 5.0 V puts **1.7 V** across that pair — **5.7× the
absolute maximum**. It would damage the device.

**The existing schematic — VDD and VDD_TX both on the boosted rail, VDD_IO on
+3V3 — is correct, and matches S1 exactly.** VDD_IO is genuinely independent
(1.65–5.5 V, its own 6 V absolute maximum, level shifters on the peripheral
pins), and S1 explicitly states "the internal supply voltage can be either higher
or lower than VDD_IO".

**This also corrects the prior audit.** The 2026-08-22 pre-design audit recorded
defect #4, "NFC rail sequencing concern", and recommended feeding VDD from +3V3
and boosting only the PA. **That recommendation was wrong and must not be
implemented.** It was flagged at the time as requiring datasheet verification;
verification has now rejected it.

### D.3 What the real residual concern is

The prior audit's *underlying* worry — a partially-powered device on a live
shared SPI bus — survives, but it is a **sequencing** problem, not a rail-split
problem. With the boost disabled, VDD = VDD_TX = 0 V while VDD_IO = 3.3 V. S1
Table 119 gives VDD a **minimum of 2.4 V** and nowhere authorises 0 V with
VDD_IO live.

Three ways to resolve it, for CTO decision (**P-10**):

| option | effect | cost |
|---|---|---|
| **N1 — 3.3 V-only NFC.** Set the `sup3V` option bit; run VDD = VDD_TX = VDD_IO = 3.3 V. Delete U13, L2, R44, R45, C34, C35, C19, C55. | All three supplies coherent at all times. The condition cannot arise. | Lower RF output power and range. S1 T119 allows 2.4–3.6 V with `sup3V` set. The old pin map already noted "the chip works at 3.3 V (Alpha proved SPI comms at 3.3 V)". |
| **N2 — boost always on while the system is on.** Keep the 5 V rail, never assert the disable. | Full RF power; supplies always valid. | Loses the "zero idle draw when NFC unused" argument. Standby cost must be measured. |
| **N3 — gate VDD_IO with the boost.** Bring VDD_IO up and down with the NFC rail. | Supplies coherent. | Adds a switch, and the SPI pins then float relative to a live bus — arguably worse than the problem. |

**N1 is the recommendation** for a first fabrication that must work: it deletes a
whole converter, deletes the OVP question, deletes the sequencing question, and
removes eight components from the BOM. Range is the price, and range is a
showcase nicety where correctness is not.

### D.4 Oscillator

**S1 §2.2.8 / §4.2.6:** "The quartz crystal oscillator operates with **27.12 MHz**
crystals." S1 features list: "27.12 MHz crystal with fast start-up".

- **Frequency: 27.12 MHz. Not negotiable.**
- **The crystal is mandatory for reader/writer operation.** S1 §4.2 makes the
  oscillator a precondition: setting the `en` bit "enables the quartz crystal
  oscillator and regulators… An interrupt is sent to inform the microcontroller
  when the oscillator amplitude and frequency is stable", and the FIFO and
  PT_memory are only accessible after that.
- XTI can accept an external digital clock, but S1 Table 2 qualifies that as
  "**in test mode** used as digital input (clock)". It is not a supported
  production alternative for our mode.
- **No crystal exists anywhere in the design.** This remains a hard blocker.

### D.5 AAT pins

**AAT is optional.** S1 Table 1 lists Automatic Antenna Tuning as a
feature present on ST25R3916 and absent on ST25R3917, and S1 §4.1 "Power-on
sequence" step 3 reads "**If AAT is used** the tuning procedure must be
performed." AAT_A/AAT_B drive varactor tuning voltages.

For a first fabrication: **do not use AAT.** It requires variable-capacitance
diodes in the matching network and a tuning algorithm in firmware, and S1 §2.2.4
warns that combining hardware wake-up with AAT needs care. A fixed matching
network is the correct first-fab choice; AAT_A/AAT_B can be left unconnected.

### D.6 Mandatory antenna/matching blocks

Not optional, and none of them currently exist: EMC/low-pass filter on RFO1/RFO2,
the matching network, the antenna coil, and the receiver input network into
RFI1/RFI2 with AGDC as the analog reference. S1 recommends 2.2 µF ∥ 10 nF at each
regulator pin and 1 µF ∥ 10 nF at AGDC.

### D.7 Safe default-off behaviour

**S1 §4.2:** "At power-on all its bits are set to 0, the ST25R3916/7 is in
Power-down mode." The RF field is off by default and requires the `en` bit plus
`tx_en` to energise. **The device is safe-by-default at the register level with
no external gating required.** The `NFC_5V_EN` pull-down (R14, 100k) remains
correct as a rail-level control but is not what prevents an unintended field.

---

## E. TPS61023 shutdown verdict

### VERDICT: **True load disconnect is CONFIRMED. The prior audit's concern was wrong. But this makes the NFC sequencing question sharper, not softer.**

**S3 feature list (p. 1):**
- "Typical **0.1 µA shutdown current** from VIN and SW"
- "Pass-through mode when VIN > VOUT"
- "**True disconnection between input and output**"
- "Output overvoltage and thermal shutdown"

**S3 §7.3.2:** "When the voltage at the EN pin is below 0.4 V, the internal
enable comparator turns the device into shutdown mode. In the shutdown mode, the
device is entirely turned off. **The output is disconnected from input power
supply.**"

| question | answer | source |
|---|---|---|
| True load disconnect when disabled? | **Yes** | S3 §7.3.2, feature list |
| Can VIN appear at VOUT with EN low? | **No** | S3 §7.3.2 |
| Shutdown current | **0.1 µA typ, 0.2 µA max** (into VIN and SW, VIN = VSW = 3.6 V, 25 °C) | S3 Table, `ISD` |
| Output behaviour in shutdown | Disconnected; VOUT leakage 4 nA typ / 20 nA max at VOUT = 5.5 V with VIN = 0 | S3, `IVOUT_LKG` |
| Additional load switch required? | **No** — for rail disconnect. **Yes, in effect** — if the CTO wants NFC powered down while VDD_IO stays live, but see §D.3: that state is the problem, not the goal. |

**Output overvoltage protection is integrated:** S3 §7.3.6 — "the TPS61023 has an
output overvoltage protection (OVP) to protect the device if the external
feedback resistor divider is wrongly populated. When the output voltage is above
**5.7 V typically**, the device stops switching." Threshold 5.5 V min / 5.7 V typ
/ 6.0 V max.

**This partially retires the prior audit's "add a TVS clamp" recommendation** —
the open-FB failure mode the clamp was for is already covered by integrated OVP.
A clamp is still worth considering for the *inductor-short* failure mode, which
OVP does not cover.

### E.1 Feedback network — verified, not assumed

Fitted values: R44 = 732 kΩ 1 %, R45 = 100 kΩ 1 %.

S3 gives V<sub>REF</sub> at the FB pin as **595 mV typ (580/610 min/max) in PWM
mode** and **601 mV typ (585 min) in PFM mode**.

- V<sub>OUT</sub>(PWM) = 0.595 × (1 + 732/100) = **4.95 V**
- V<sub>OUT</sub>(PFM) = 0.601 × (1 + 732/100) = **5.00 V**

Both sit inside the 2.2–5.5 V output setting range and **below the 5.5 V minimum
OVP threshold**, so the converter will not trip its own protection. Worst-case
with 1 % resistors and V<sub>REF</sub> at its 610 mV maximum gives ≈ 5.2 V, still
under 5.5 V but with only ~0.3 V of margin.

**The feedback network is correct.** If the CTO chooses N1 (3.3 V-only NFC) the
whole block is deleted and this becomes moot.

---

## F. External I²C / accessory power verdict

### F.1 TCA9517A — **PASS.** This corrects the prior audit.

The pre-design audit stated the TCA9517A "does not advertise an I<sub>off</sub> /
partial-power-down spec the way TCA9617B-class parts do" and flagged it as a
part-selection gate. **That was wrong.** S4 (SCPS245E, revised October 2025)
states the opposite, explicitly:

| requirement | S4 evidence | verdict |
|---|---|---|
| High-Z when unpowered | **Feature list: "High-impedance I²C pins when powered-off"** | **PASS** |
| Tolerates a powered accessory on an unpowered port | **§3 Description: "All inputs and I/Os are over-voltage tolerant to 5.5 V, even when the device is unpowered (VCCB and/or VCCA = 0 V)"** | **PASS** |
| No back-powering | Implied by the above two, and by the power-up circuit below | **PASS** |
| Safe power sequencing | **§9: "VCCB and VCCA can be applied in any sequence at power up. The TCA9517A includes a power-up circuit that keeps the output drivers turned off until VCCB is above 2.5 V and the VCCA is above 0.8 V."** | **PASS** |
| Appropriate for a hot-plug user port | Yes, with the caveat below | **PASS** |

**A structural detail worth recording, found during verification.** S4 §9: "VCCA
is only used to provide the 0.3 × VCCA reference to the A-side input comparators
and for the power-good-detect circuit. **The TCA9517A logic and all I/Os are
powered by the VCCB pin.**"

In the AQROOT wiring, VCCA = `+3V3` (internal, always on) and VCCB =
`ACC_3V3_SW` (the switched accessory rail). So **the entire buffer is powered by
the accessory rail**, and when `ACC_PWR_EN` is deasserted the device is unpowered
and *both* sides go high-Z. That is exactly the §8c requirement — "an open-drain
buffer/gate powered from switched accessory power" — implemented by
construction. The topology is right, and it is right for a reason the original
documentation did not spell out.

**One accessory-facing design rule must be published.** S4 §3: "The type of
buffer design on the B-side prevents it from being used in series with devices
which use static voltage offset… they do not recognize buffered low signals as a
valid low and do not propagate it as a buffered low again." **Accessories must
not place another TCA9517/PCA9515-class buffer in series on the expansion port.**

### F.2 TPS22918 — **FAIL.**

| requirement | S5 evidence | verdict |
|---|---|---|
| Reverse-current blocking | **§11: "Because of the integrated body diode in the MOSFET, a C<sub>IN</sub> greater than C<sub>L</sub> is highly recommended… [current will] flow through the body diode from VOUT to VIN."** | **FAIL — no reverse blocking** |
| Behaviour when `ACC_3V3_SW` is externally driven with VIN low | Current flows through the body diode from VOUT into VIN, i.e. into `+3V3` | **FAIL** |
| Is the QOD topology safe in that condition? | QOD discharges VOUT to ground through an internal path. With an accessory actively driving the rail, QOD fights a powered source — it does not isolate it | **FAIL** |

The prior audit's finding is confirmed by the datasheet, and it directly breaks
the Full Beta v2 requirement that an independently powered accessory must not be
able to power AQROOT through J5.

### F.3 Recommended replacements

All three provide reverse current protection that is **always active, including
while the switch is disabled**, per TI's family documentation:

| MPN | why it is safer | notes |
|---|---|---|
| **TPS22910AYZVR** | Integrated reverse-voltage comparator disables the pass FET when V<sub>OUT</sub> exceeds V<sub>IN</sub>, ~10 µs response; protection active in both ON and OFF states | 1.4–5.5 V input; fastest rise time (~1 µs at 3.3 V) — **may need inrush review** |
| **TPS22912CYFPR** | Same reverse-current architecture, different rise-time grade | Better inrush behaviour than TPS22910A |
| **TPS22913BYFPR** | Same architecture; **~66 µs rise time at 3.3 V** | **Preferred starting point** — the slow rise is the friendliest for a hot-plug accessory rail |

**Verification status:** the reverse-current behaviour above comes from TI
family documentation surfaced in search, **not** from a page-cited read of each
datasheet. Before any of these is placed in a schematic, the exact MPN's
datasheet must be pulled and the reverse-current section cited, and the QOD /
output-discharge behaviour re-checked — the TPS2291x family does **not**
obviously carry the TPS22918's adjustable-QOD pin, so the §8c discharge step may
need an external bleed resistor instead.

**This is a like-for-like architectural swap, not a redesign.** The load-switch
position, its enable source and its rail are unchanged.

---

## G. STAT1 / STAT2 recommendation

**S6 (SLUSF65A), Table 5-1 Pin Functions**, for both STAT1 (pin 9) and STAT2 (pin 3):

> "**Open-drain status output. Can be pulled up with a 1 kΩ to 20 kΩ resistor. Typical pull-up voltage = 1.8 V. Maximum pull-up voltage = 5 V.** See also Section 8.3.10 Status Pins. **Can be left floating if unused.**"

| question | answer |
|---|---|
| Open-drain? | **Yes**, both |
| Required pull-ups | **1 kΩ – 20 kΩ**, external. Not internal. |
| Valid voltage domain | Typical pull-up 1.8 V, **maximum 5 V**. Absolute maximum on all non-IN pins is 5.5 V (S6 §6.1). **3.3 V is within spec.** |
| Sink capability | 20 mA (S6 §6.1, output sink current STAT1/STAT2) — far above what a 10 kΩ pull-up needs |
| Direct to two TCA9535 inputs? | **Yes, appropriate.** TCA9535 inputs are high-Z with no internal pulls, run from `+3V3`, so an open-drain output pulled to `+3V3` gives clean 3.3 V logic levels. |
| Recommended resistors | **10 kΩ to `+3V3`**, matching the existing button pull-ups and comfortably inside the 1 k–20 k window |
| Power-off behaviour | Both `+3V3` and the pull-ups derive from SYS, which derives from IN or BAT. If the charger is unpowered the pull-up rail is unpowered too, so no leakage path exists and no pin is biased through an unpowered device. |

### G.1 A finding that changes the recommendation

**S6 §8.3.10 / Table 7-2:** in one state — charge completed with the charger in
sleep mode — "the STAT1 pin remains stable, while **the STAT2 pin toggles**."

`U2`'s `/INT` is wired-OR onto `WAKE_INT_N` → GPIO21, which is the deep-sleep
wake source. **A toggling STAT2 on a `U2` input would assert `/INT` repeatedly
and wake the MCU on every toggle**, for as long as the unit sits on a charger at
full charge. That is the exact condition a device spends most of its idle life
in.

**Recommendation:**

1. **Connect STAT1 to the freed `U2.P16`** (vacated by HOME). It is stable in
   every state and gives charging / fault / complete indication.
2. **Do not connect STAT2 to an expander input.** Leave it on `TP7`, or connect
   it only if firmware masks the resulting wake events — which means the
   firmware must distinguish "charger present" before entering deep sleep, and
   that is a contract, not a wire.
3. Derive the remaining state from the MAX17048 (state of charge and rate) rather
   than from a second toggling status line.
4. `U2.P17` (freed by retiring the RootProbe IRQ under ruling G) stays available —
   the strongest candidate for it is a **VBUS-present sense**, which the product
   currently lacks entirely and which is more useful than STAT2.

**Not implemented. Recommendation only, per ruling H.**

---

## H. Remaining architecture blockers

| # | blocker | status after this audit |
|---|---|---|
| **B-01** | Reverse-polarity protection does not exist | **Still open.** Architecture recommended (§C), not approved. Fabrication blocker. |
| **B-06** | NFC crystal / matching / antenna undesigned | **Still open and now sharper.** 27.12 MHz crystal confirmed mandatory; no crystal exists. |
| **B-04 / P-07** | Internal enclosure cavity never published | **Still open.** Blocks all placement. |
| **NEW P-10** | NFC supply topology: 3.3 V-only (N1) vs always-on boost (N2) | **New.** Created by §D. Was previously mis-framed as a rail-split. |
| **B-07** | "NFC rail architecture defect" | **RETIRED — the finding was wrong.** VDD/VDD_TX on one boosted rail is correct per S1. Replaced by P-10. |
| **B-08** | WAKE line has no isolation gate | **Still open.** §F.1 shows the I²C path already gets this by construction; the WAKE leg still does not. |
| **B-09** | GPIO3 has no strap-defining pull | **Still open, and stronger than stated.** S2 §3.4: GPIO3 "does not have any internal pull resistors and the strapping value must be controlled by the external circuit that cannot be in a high impedance state." Note S2 Table 3-5 confirms GPIO3 is *ignored* with default eFuses, so the boot risk is low — but the datasheet requirement stands independently. |
| **B-15** | No charge / VBUS telemetry | **Path defined** (§G), not implemented. |
| **B-03** | Footprint audit not performed | **Partially advanced.** U9's 33-pad footprint mapping is now verified correct against S1 Tables 2/118/119. Every other footprint remains unverified. |
| — | TPS22918 lacks reverse blocking | **Confirmed and replacement identified** (§F.3). Exact MPN still needs a page-cited datasheet check. |

---

## I. Items ready to lock

These are verified and carry no unresolved dependency. **Locking is the CTO's
call — this audit only certifies that the evidence is complete.**

| item | basis |
|---|---|
| **U9 footprint pin mapping is correct** | Cross-validated against S1 Tables 2, 118 and 119 |
| **VDD and VDD_TX must share one supply; VDD_IO independent at 3.3 V** | S1 p. 39 + Tables 118/119 |
| **NFC interface strap `I2C_EN` = GND (SPI mode) is correct** | S1 Table 2, pin 20 |
| **NFC crystal frequency = 27.12 MHz, mandatory** | S1 §2.2.8 / §4.2.6 |
| **NFC RF field is safe-by-default at power-on** | S1 §4.2 |
| **TPS61023 provides true load disconnect and integrated OVP** | S3 §7.3.2, §7.3.6 |
| **TPS61023 feedback network R44/R45 is correct** | S3 V<sub>REF</sub> 595/601 mV → 4.95/5.00 V |
| **TCA9517A meets the hot-plug isolation requirement** | S4 SCPS245E feature list + §3 + §9 |
| **BQ25185 STAT1/STAT2 are open-drain, 10 kΩ to +3V3 is in spec** | S6 Table 5-1, §6.1 |
| **`NATIVE_B` = GPIO47 (not GPIO18), with `DISP_BL_CTL` moved to GPIO46** | S2 Tables 3-1, 3-3, 2-2, §2.3.5 |
| **`NFC_IRQ` must NOT move to GPIO46** | S2 Table 3-3 + S1 IRQ latching behaviour |

---

## J. Items requiring independent Claude CTO second opinion

1. **The reverse-polarity recommendation (§C.4)** — flagged as instructed. The
   three attack points are listed in §C.5.
2. **NFC supply topology P-10 (§D.3)** — N1 deletes a converter and eight parts
   at the cost of RF range. That is a product trade, not an engineering one.
3. **The GPIO46 substitution (§B.3)** — a second reviewer should independently
   confirm that no other signal in the design has a better claim on GPIO46, and
   that moving backlight control onto a strapping pin creates no issue during
   the 3 ms `tH` window.
4. **Whether NFC belongs in the first fabrication at all**, given that the
   crystal, matching network and antenna are all undesigned while ruling E makes
   it mandatory. This is a schedule risk, not a technical one, and it is the
   single largest one in the plan.

---

## K. Next engineering gate recommendation

**Recommended next gate: FBV2-A2 — Mechanical interface freeze.**

Not FBV2-S1 (schematic migration), even though the architecture work is now
mostly unblocked. Reasoning:

1. **FBV2-A1 cannot fully close yet** — P-01, P-04, P-07 and the new P-10 are all
   still open, and three of them need CTO input rather than engineering work.
2. **FBV2-A2 is the long-pole item and it is not blocked by anything.** The
   internal cavity has never existed in this repository. Every hour it stays
   unpublished is an hour of placement that cannot start, and unlike the
   electrical questions it needs CAD work, not a decision.
3. The two can run concurrently: mechanical CAD produces the cavity while the CTO
   resolves P-01/P-04/P-10.

**Do not start FBV2-S1 until P-01 (reverse polarity) and P-10 (NFC supply) are
decided.** Both change the power tree, and the power tree is the first sheet in
the migration order.

---

## Corrections to the 2026-08-22 pre-design audit

Recorded explicitly, because an engineering record that quietly fixes its own
mistakes is not a record.

| prior claim | status | correction |
|---|---|---|
| "NFC rail architecture defect… feed the ST25R3916's main VDD from `+3V3` and boost only the transmitter/PA supply" | **WRONG** | S1 requires VDD and VDD_TX within ±0.2 V. The recommendation would have destroyed the part. The as-built rail assignment is correct. |
| "The TCA9517A does not advertise an I<sub>off</sub>/partial-power-down spec" | **WRONG** | S4 explicitly lists "High-impedance I²C pins when powered-off" and 5.5 V tolerance when unpowered. The part passes. |
| "Most non-isolating boost converters pass V<sub>IN</sub> to V<sub>OUT</sub>… confirm true-shutdown behaviour" | **Correctly flagged, now resolved** | S3 confirms true disconnection. The concern was legitimate and the answer is favourable. |
| "Add a TVS/zener clamp on `NFC_5V_PA_PENDING` [for] an open R44" | **Superseded** | S3 §7.3.6 integrated OVP already covers the wrong-divider case. A clamp may still be wanted for inductor-short faults. |
| "`NATIVE_B` = GPIO18 reclaimed by moving `NFC_IRQ` to GPIO46 — low-medium risk" | **WRONG** | It would make ROM download recovery conditional on NFC interrupt state. Substituted (§B.3). |
| "GPIO3 hazard is currently low" | **Accurate but incomplete** | True per S2 Table 3-5 with default eFuses, but S2 §3.4 independently requires GPIO3 not be left high-impedance. |
| U9 pin-number reconstruction | **CONFIRMED CORRECT** | Cross-validated against three independent S1 tables. |
| TPS22918 has no reverse blocking | **CONFIRMED CORRECT** | S5 §11 confirms the integrated body diode conducts VOUT→VIN. |

---

## Sources

- [ST25R3916/7 datasheet DS12484 Rev 3 — STMicroelectronics](https://www.st.com/resource/en/datasheet/st25r3916.pdf) (read from the copy in `hardware/beta/kicad/aqroot-beta/vendor/ST25R3916/`)
- [ESP32-S3 Series Datasheet v2.2 — Espressif](https://www.espressif.com/sites/default/files/documentation/esp32-s3_datasheet_en.pdf)
- [ESP32-S3 USB Serial/JTAG Console — Espressif ESP-IDF](https://docs.espressif.com/projects/esp-idf/en/stable/esp32s3/api-guides/usb-serial-jtag-console.html)
- [TPS61023 datasheet SLVSF14B — Texas Instruments](https://www.ti.com/lit/ds/symlink/tps61023.pdf)
- [TCA9517A datasheet SCPS245E — Texas Instruments](https://www.ti.com/lit/ds/symlink/tca9517a.pdf)
- [TPS22918 datasheet — Texas Instruments](https://www.ti.com/lit/ds/symlink/tps22918.pdf)
- [BQ25185 datasheet SLUSF65A — Texas Instruments](https://www.ti.com/lit/ds/symlink/bq25185.pdf)
- [TPS22910A — Texas Instruments](https://www.ti.com/product/TPS22910A)
- [TPS22913 — Texas Instruments](https://www.ti.com/product/TPS22913)
- [TPS22912C — Texas Instruments](https://www.ti.com/product/TPS22912C)
- [LTC4368 — Analog Devices](https://www.analog.com/en/products/ltc4368.html)
- [Reverse Battery Charger Protection — Analog Devices](https://www.analog.com/en/resources/design-notes/reverse-battery-charger-protection.html)
- [Reverse-Current Circuitry Protection — Analog Devices](https://www.analog.com/en/resources/design-notes/reversecurrent-circuitry-protection.html)
