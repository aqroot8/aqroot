# AQROOT Full Beta v2 — Architecture Reconciliation Audit

Date: 2026-08-22
Task: **FBV2-ARCH-002** — reconcile critical architecture and design first-revision recovery paths
Repository HEAD at audit: `eb47815`
Scope: **documentation only.** No KiCad, PCB, mechanical, firmware, BOM, CPL or Gerber file was created or modified. `hardware/beta-v2/` was not created.

---

## 0. Sources

| # | document | revision / date | how obtained |
|---|---|---|---|
| S1 | ST25R3916/7 datasheet | DS12484 Rev 3, 04-Jun-2020 | in repo |
| S2 | ESP32-S3 Series Datasheet | v2.2 | espressif.com |
| S3 | TPS61023 | SLVSF14B, rev. Aug 2020 | ti.com |
| S4 | TCA9517A | SCPS245E, rev. Oct 2025 | ti.com |
| S6 | BQ25185 | **SLUSF65A**, Oct 2023, rev. **Jan 2026** | ti.com |
| **S8** | **TCA9535** | **SCPS201E**, Aug 2009, rev. **May 2022** | ti.com |
| **S9** | **TPS22950 / TPS22950C / TPS22950L** | **SLVSFJ2B**, Dec 2020, rev. **Feb 2023** | ti.com |
| **S10** | **TPS61169** | (TI, DCK SC70-5) | ti.com |
| **S11** | LTC4368 | Rev. C — product page + search summary | analog.com (**PDF fetch failed twice: timeout, then ECONNRESET**) |
| **S12** | PCAL9535A | — | **PDF NOT OBTAINED.** NXP direct URL returned HTTP 404; Digi-Key mirror HTTP 410; Mouser mirror returned HTML. Evidence is NXP product-page text only. |
| **R1** | Independent review FBV2-CTO2-PWRNFC-001 | 2026-08-22 | archived in `reviews/` |

**S11 and S12 are weaker than the rest and every claim drawn from them is marked
inline.** No verdict below is stated more confidently than its source supports.

---

## A. PCAL9535A replacement audit

### VERDICT: **PASS WITH SCHEMATIC/FIRMWARE CHANGES.** Not "PASS DROP-IN" — and the reason is evidential, not technical.

### A.1 What was verified

**TCA9535 PW (TSSOP-24) pinout — S8 Figure 5-1, fully verified:**

| pin | name | | pin | name |
|---|---|---|---|---|
| 1 | INT | | 24 | VCC |
| 2 | A1 | | 23 | SDA |
| 3 | A2 | | 22 | SCL |
| 4 | P00 | | 21 | A0 |
| 5 | P01 | | 20 | P17 |
| 6 | P02 | | 19 | P16 |
| 7 | P03 | | 18 | P15 |
| 8 | P04 | | 17 | P14 |
| 9 | P05 | | 16 | P13 |
| 10 | P06 | | 15 | P12 |
| 11 | P07 | | 14 | P11 |
| 12 | GND | | 13 | P10 |

**Cross-checked against the measured board.** Every `U2` and `U3` pad-to-net
assignment matches this table exactly — INT on 1, P00–P07 on 4–11, GND on 12,
P10–P17 on 13–20, A0 on 21 (`GND` on U2 → 0x20; `+3V3` on U3 → 0x21), SCL 22,
SDA 23, VCC 24. **The existing schematic pin usage is confirmed correct against
S8.**

**PCAL9535A properties confirmed from NXP product-page text (S12):**

| property | value |
|---|---|
| Package | **TSSOP24 (PCAL9535APW)**, SOT355-1, body width 4.4 mm — same JEDEC outline as TI's PW |
| Register set | *"contains the PCA9535 register set of four pairs of 8-bit configuration, input, output and polarity inversion registers"* — legacy-compatible |
| Agile I/O | programmable output drive strength, latchable inputs, programmable pull-up/pull-down, **maskable interrupt**, **interrupt status register** |
| Power-up default | *"powers up with all I/O interrupts masked, which allows for a board bring-up free of spurious interrupts at power-up"* |
| Supply | 1.65–5.5 V |

### A.2 Why this is not "PASS DROP-IN"

Three separate reasons, in descending order of weight:

1. **The pin table could not be obtained from a primary source.** Three retrieval
   routes failed (NXP 404, Digi-Key 410, Mouser HTML). The pin-for-pin claim
   currently rests on NXP's own marketing statement plus the shared TSSOP24
   outline. That is strong circumstantial evidence and it is **not a cited pin
   table.** **Reading the printed PCAL9535A pinout and comparing it pad-by-pad
   against S8 Figure 5-1 is a required gate before the swap is drawn.**
2. **Firmware must change, and silently fails if it does not.** PCAL9535A powers
   up **with all interrupts masked**; TCA9535 has no mask and asserts
   unconditionally. Firmware carried over unchanged would see **no interrupts at
   all** — no button wake, no accessory attention. This is the opposite of a
   drop-in behaviour and must be an explicit bring-up checklist item.
3. **Schematic changes are available and are a deliberate choice, not automatic.**
   Programmable pulls could delete roughly ten external resistors — but **CTO
   ruling F keeps safety-critical safe-state pulls external**, and correctly so:
   a programmable pull is not present until firmware writes it, which is exactly
   the window the external pulls exist to cover. The resistor deletion should be
   applied only to non-safety-critical inputs, if at all.

### A.3 Recommendation: change **both** U2 and U3

**Yes — one expander family.** Reasons:

- **U3 (external) needs the mask more than U2 does.** Ten of its inputs reach a
  user-accessible connector. Any accessory that chatters, floats or is unplugged
  mid-transaction produces an unmaskable, self-refreshing interrupt storm on the
  shared `WAKE_INT_N` net, with no software mitigation short of polling.
- **U2 (internal) needs it for `STAT2`** (§E below) and for any future chattering
  internal input.
- **Mixed families would be a standing firmware trap** — two register maps, two
  interrupt models, on one bus, distinguished only by address.
- **Programmable pulls on U3 define the state of ten user-accessible pins with
  nothing plugged in**, which today depends on external resistors that do not
  exist.

**Availability, cost and LCSC/JLCPCB stock status: NOT VERIFIED.** No distributor
lookup was performed in this session. This is a procurement gate, and given the
Beta-DM history — where blind BOM regeneration destroyed eight hand-entered MPNs
— it should be closed against the real LCSC part page before the swap is
committed.

---

## B. GPIO38 / GPIO47 verdict

### VERDICT: **OPTION G38 — PASS WITH CONDITIONS.** Recommended native pair: **GPIO38 + GPIO47.**

### B.1 Why GPIO38 is a better `NATIVE_A` than GPIO43

| property | GPIO38 | GPIO43 |
|---|---|---|
| Strapping role | none | none |
| S2 §2.3.5 priority | **P2 — "freely used without restrictions"** | **P3 — "UART0 interface"** |
| Power-up glitch (S2 Table 2-2) | **not listed** | not listed |
| Boot traffic | **none** | **ROM UART TX at every reset, and throughout any UART flash** |
| RTC / deep-sleep wake | no | no |

The decisive point is contention, and it is a **self-damage path in both
directions**: `NATIVE_A` is specified as a bidirectional fast I/O, and the module
actively drives GPIO43 push-pull at every single reset. A third-party accessory
driving that pin during boot is in push-pull contention with the module's output
driver, forever. Documentation does not stop an accessory from driving a pin it
was told it could drive. **GPIO38 removes the hazard rather than mitigating it.**

### B.2 Freeing GPIO38 — moving `SX1262_DIO1` to an internal expander input

**Conditions, all of which must hold:**

| # | condition | status |
|---|---|---|
| C1 | **DIO1 must be level-held until the IRQ flags are cleared**, not a pulse. An expander with no capture register cannot catch a transient. | **UNVERIFIED — see below** |
| C2 | **PCAL9535A must be adopted.** With TCA9535 the shared `/INT` gives no way to tell a LoRa event from a button press without reading four port registers across two devices. PCAL9535A's interrupt-status register identifies the source in one read. | Depends on §A |
| C3 | **It must go on `U2` (internal), never `U3`.** Ruling §4 is explicit and correct — mixing internal radio control with user-facing I/O would let an accessory interfere with the flagship LoRa demo. | Satisfied by design |
| C4 | **`BUSY` stays native and direct.** It is polled tightly around every SPI command. | Already satisfied — `SX1262_BUSY` is on GPIO8 |
| C5 | **Added latency of ~100–300 µs must be acceptable.** | Satisfied — see below |
| C6 | **The external I²C segment must remain isolable**, so a hung accessory cannot block LoRa event detection on the shared bus. | Satisfied by `U16` (S4: high-Z when powered off) |

**On C5 — latency.** LoRa symbol times are milliseconds (SF7/125 kHz ≈ 1.024 ms
per symbol), and the events in question — `TxDone`, `RxDone`, `Timeout`,
`CadDone`, `CrcErr`, `HeaderErr` — are all end-of-operation notifications, not
sample-clock events. A few hundred microseconds of I²C latency is negligible
against that. **Ruling J removes the only case that would have been tight**
(deep-sleep packet wake), because DIO1 no longer needs to be an RTC wake source.

> ### ⚠ C1 could not be verified from a primary source
>
> The SX1261/2 datasheet could not be retrieved: Semtech's own domain did not
> resolve, and the Mouser mirror returned HTML rather than the PDF. **The claim
> that DIO1 is level-held until `ClearIrqStatus` is issued is therefore NOT
> established in this audit**, and I am not asserting it from memory.
>
> **This is the single gate on OPTION G38.** If DIO1 turns out to be a pulse, the
> expander route fails outright and `NATIVE_A` falls back to GPIO43 with series
> resistance. Read the printed SX126x datasheet IRQ section before this is drawn.
>
> Note that the **E22-900M22S module datasheet, not the bare SX1262 datasheet, is
> the binding document** — the module may buffer or re-time DIO1. Both should be
> checked.

### B.3 Freeing GPIO47 — `DISP_BL_CTL` to GPIO46

**The review's blocking condition is now CLOSED.** R1 conditioned GPIO46 on
proving that nothing pulls the backlight-enable net up:

> *"No pull-up anywhere on that net — including inside the backlight driver… If the backlight enable is active-low or internally pulled up, GPIO46 is disqualified and the remap fails. Check the actual driver before locking."*

**Verified against S10 (TPS61169 datasheet, Table 4-1 and the electrical
characteristics table): the `CTRL` pin has an internal PULL-DOWN**
(`RPD — CTRL pin internal pull-down resistor`). It is active-high, and it enters
shutdown when held low for more than 2.5 ms.

An internal pull-down is the correct direction: it reinforces GPIO46's own weak
pull-down (S2 Table 3-1) rather than fighting it. **GPIO46 is cleared to host
`DISP_BL_CTL`**, subject to the conditions below.

**Conditions, carried forward and extended:**

1. **10 kΩ external pull-down** — Espressif's internal pull is ~45 kΩ; a strong
   external pull is their own guidance for strap-class pins.
2. **No RC filter and no bulk capacitance on the GPIO46 net.** If the backlight
   needs soft-start, put it after a buffer. *(S2 publishes no numeric capacitance
   limit for strapping pins — only a qualitative caution. This condition is
   engineering judgement, not a spec.)*
3. **Strap hold ≥ 3 ms** after CHIP_PU rises (S2 Table 3-2, `tH`). The pull-down
   must be effective from the moment 3V3 is valid.
4. **GPIO46 is not an RTC GPIO** — no level retention through deep sleep, so the
   backlight always reverts to the pull-down state on sleep entry. Fine for a
   backlight; must be documented.
5. **Bring-up check, free:** the ROM boot log prints `boot:0xNN`, where bit `0x04`
   is the latched GPIO46 level. "boot value shows GPIO46 = 0" is a one-line
   pass/fail on every unit.
6. **A note in the schematic that GPIO46 is not input-only on ESP32-S3.** That
   belief is true of the S2 and migrates constantly; S2 lists GPIO46 as type
   `I/O/T`.

**One consequence to accept:** S10 notes that in shutdown there is still a DC
path from input to the LEDs through the inductor and Schottky, so the LED array's
forward voltage must exceed the maximum input voltage for the backlight to be
truly dark. That is a backlight-string design constraint, unrelated to GPIO46,
but it lands in the same block and should not be discovered later.

### B.4 Result

| role | pin | freed by |
|---|---|---|
| **`NATIVE_A`** | **GPIO38** | moving `SX1262_DIO1` to a `U2` expander input (conditional on C1) |
| **`NATIVE_B`** | **GPIO47** | moving `DISP_BL_CTL` to GPIO46 (conditions above) |
| `WAKE_ATTN_N` | GPIO21 | unchanged — RTC-capable, correct |
| GPIO43 / GPIO44 | **internal debug UART test pads** | **removed from the connector** |

**If C1 fails**, the fallback is `NATIVE_A` = GPIO43 with 220–330 Ω series
resistance at the connector, connector-side ESD, and a published warning that the
pin emits ROM UART traffic at every reset.

---

## C. Final proposed 20-pin resource count

Per CTO ruling D, with the permanent raw `+3V3` pin removed per ruling C.

| # | signal | class | notes |
|---|---|---|---|
| 1 | `GND` | ground | |
| 2 | `XGPIO0` | expander | |
| 3 | `XGPIO1` | expander | |
| 4 | `XGPIO2` | expander | |
| 5 | `XGPIO3` | expander | |
| 6 | `XGPIO4` | expander | |
| 7 | `NATIVE_A` (GPIO38) | **native** | series R + ESD |
| 8 | `GND` | ground | return for pin 7 |
| 9 | `XGPIO5` | expander | |
| 10 | `XGPIO6` | expander | |
| 11 | `XGPIO7` | expander | |
| 12 | `XGPIO8` | expander | |
| 13 | `I2C_SDA_EXT` | I²C | via `U16`, 22 Ω |
| 14 | `I2C_SCL_EXT` | I²C | via `U16`, 22 Ω |
| 15 | `XGPIO9` | expander | |
| 16 | `XGPIO10` (**or `ACC_DETECT`**) | expander | see below |
| 17 | `NATIVE_B` (GPIO47) | **native** | series R + ESD |
| 18 | `WAKE_ATTN_N` | interrupt | GPIO21, RTC-capable; open-drain gate required |
| 19 | `ACC_3V3_SW` | power | TPS22950C, TVS at connector |
| 20 | `GND` | ground | return for pins 17/19 |

**Count: 11 XGPIO + 2 native + 2 I²C + 1 WAKE + 1 switched power + 3 GND = 20.**
No permanent raw `+3V3`. No duplicated GPIO. **Matches ruling D exactly.**

> **Open recommendation — `ACC_DETECT`.** R1 observes that the map spends three
> pins on ground and one on power but none on accessory detection, so firmware
> cannot know an accessory is present before it enables the switched rail or
> chooses pull configurations. Repurposing **one XGPIO as `ACC_DETECT`** (the
> accessory straps it to GND) is free once PCAL9535A's programmable pull-ups
> exist. That would make it **10 XGPIO + 1 ACC_DETECT**, still 20 pins.
> **Not adopted** — ruling D specifies 11 independent XGPIO, and this would change
> the published count. Raised as **P-16** for the CTO.

---

## D. Power / fault table — headline results

Full analysis: [`../architecture/POWER_FAULT_STATE_TABLE.md`](../architecture/POWER_FAULT_STATE_TABLE.md).

| case | result |
|---|---|
| 1 · Normal battery, no USB | **OK** |
| 2 · Normal battery + USB | **OK — and this is why the `-1` suffix is load-bearing.** LTC4368-**2**'s −3 mV reverse trip opens as soon as charge current flows; a `-2` fitted here discharges normally and never charges |
| 3 · No battery + USB | **DEGRADED with TCA9535, OK with PCAL9535A.** S6 §7.3.10 verbatim: no-battery limit cycle, STAT1 stable, **STAT2 toggles** → unmaskable interrupt storm on the shared wake net |
| 4 · Dead / 0 V battery + USB | **UNRESOLVED — BLOCKS SCHEMATIC LOCK.** LTC4368 UVLO 1.8–2.4 V, 2.5 V minimum operating (S11) → both gates off, body diodes anti-series, **the pack can never be recharged** |
| 5 · Reversed battery, no USB | **BLOCKED correctly** — clamp conducts, fuse opens |
| 6 · **Reversed battery + USB (mandatory)** | **OK** — reverse-VIN comparator ties both gates to negative VIN; BAT protected; **device still boots from USB**, so the fault is diagnosable rather than silent |
| 7 · **One pass FET shorted + reversed battery + USB (mandatory)** | **OK only with fuse + clamp.** Without them, −3.0 to −4.35 V lands on BQ25185 BAT against a −0.3 V absolute maximum — a **10–14× DC violation**. The LTC4368 cannot turn off a shorted FET |
| 8 · Accessory short while enabled | **OK** — TPS22950C current limit + auto-retry + thermal shutdown; core `+3V3` holds |
| 9 · Externally powered accessory, AQROOT off | **OK — conditional on removing the permanent `+3V3` pin.** TPS22950C RCB is active even while disabled; `U16` high-Z when unpowered |
| 10 · USB attached, SW9 off | **OK** — charges with the power switch off; `+3V3` stays at 0 V; boot correctly blocked |
| 11 · Battery inserted with USB present | **UNRESOLVED** — latch-off and hot-insertion inrush interact; unresolvable on paper |

**Six items block schematic lock**, tracked as P-11 … P-16.

---

## E. Reverse-protection and dead-cell recommendation

### E.1 Topology — accepted with the two additions

**LTC4368-1 + independent-dual N-FET, VIN on the cell side, RETRY strapped for
latch-off, plus a series fuse and a Schottky clamp at the cell connector.**

**My prior recommendation of discrete back-to-back N-FETs is withdrawn.** R1
demonstrates it is not merely under-specified but **unrealisable at 1S**, and the
argument is sound and checkable:

- **Common-source N-channel:** the shared source sits at cell potential
  (3.0–4.2 V); the highest rail on the board is SYS at ~4.5 V; available V<sub>GS</sub>
  is therefore **0.3–1.5 V** — below the threshold of any dual meeting a <30 mΩ
  target, and far below the 4.5 V at which R<sub>DS(on)</sub> is specified. **There
  is no rail on this board that turns those FETs on.** A charge pump is not an
  optimisation; it is the circuit.
- **P-channel with gates to GND:** in the fault state (cell reversed, USB present)
  the common source charges through the SYS-side body diode to ~3.8 V, gates sit
  at 0 V, so V<sub>GS</sub> ≈ −3.8 V and **both FETs turn hard on, connecting SYS
  directly to a reversed cell.** The circuit creates the short it was added to
  prevent.

**My IQ argument was also quantitatively weak.** Against a ~40–60 µA board
baseline (BQ25185 4 µA + TPS63020 25 µA + MAX17048 ~3 µA + two expanders + ESP32-S3
deep sleep), the LTC4368's 80 µA roughly doubles a small number and still leaves
~a year of shelf life on a 1500 mAh cell. Trading that for unvalidated analogue
behaviour, on a programme that may skip incremental bring-up, is the wrong
direction of risk. The `SHDN` pin additionally buys a genuine 5 µA hard-off ship
mode the design does not currently have.

**I accept the correction.** CTO ruling A is adopted as recorded.

### E.2 Why `-2` is rejected

Not a preference — a silent, expensive failure. The two parts differ in exactly
one parameter, and it is the one that matters on a bidirectional node: **-1 trips
at ±50 mV symmetric; -2 trips at −3 mV**, which is ideal-diode behaviour. Fit a
`-2` and the board discharges normally and never charges. **Put the suffix in the
schematic symbol, the BOM, the assembly note and the bring-up checklist.**

### E.3 Dead-cell recovery — recommended, not approved

**R1 — a firmware-gated trickle:** ~10 kΩ in series with a small FET from
`BAT_PROT` to `BAT_RAW`, default off, plus a `BAT_RAW` ADC divider (≥100 kΩ
series + Schottky clamp to GND) so firmware can distinguish *no cell* / *dead
cell* / *reversed cell* before acting. ~450 µA is enough to lift VIN over UVLO
and hand control back to the controller; into a reversed cell it is harmless.

**A permanent resistor across the FETs is rejected** — it is an unconditional
path around a safety element and would apply USB-side voltage across a reversed
cell, which the CTO instruction rejects outright.

**Not approved. Tracked as P-11.** Per instruction, no dead-cell solution is
invented here — options are presented and the analysis stops.

### E.4 Fuse and clamp

**Required, not optional.** Case 7 is a stated CTO requirement and is not met
without them: a shorted pass FET is the dominant MOSFET failure mode, and it
reproduces exactly the fault the protection guards.

| item | class | placement |
|---|---|---|
| Fuse | fast-acting, ~3 A, series with cell positive | at the cell connector, before everything |
| Clamp | Schottky, cathode to `BAT_RAW`, anode to GND | adjacent to the fuse |

Values not locked — the fuse rating derives from the peak system current budget
and the clamp's surge rating from the fuse's I²t.

---

## F. Community power recommendation

### VERDICT: **TPS22950C, and remove the permanent raw `+3V3` pin.**

**Verified against S9 (SLVSFJ2B) — §5 Device Comparison Table:**

| device | I<sub>LIM</sub> range | I<sub>MAX</sub> | response | **RCB** |
|---|---|---|---|---|
| TPS22950 | 0.05–3.5 A | 2.7 A | auto-retry | **Yes** |
| **TPS22950L** | 0.5–3.5 A | 2.7 A | latch-off | **No** |
| **TPS22950C** | **0.5–3.5 A** | **3.2 A** | **auto-retry** | **Yes** |

**This table matters**, because the Features bullet reads *"Always-ON reverse
current blocking (TPS22950)"* and names only the base part. §5 is explicit:
**the C variant has RCB; the L variant does not.** Ordering an `L` by mistake
silently deletes the single property the part was chosen for.

Against ruling C's requirements:

| requirement | TPS22950C | source |
|---|---|---|
| 3.3 V operation | 1.8–5.5 V ✓ | S9 Features |
| Default OFF | ✓ smart pull-down, R<sub>PD,ON</sub> 500 kΩ typ | S9 Features |
| Hardware pull-down on ON/EN | ✓ internal — **but S9 Table 6-1 still says "Do not leave floating", so an external pull-down remains mandatory** | S9 §6 |
| Reverse-current blocking | ✓ | S9 §5 |
| Adjustable current limiting | ✓ one resistor to GND | S9 §6 |
| Short-circuit protection | ✓ auto-retry | S9 Features |
| Thermal shutdown | ✓ 170 °C | S9 Features |
| Leaded package | ✓ **DDC (SOT-23-6 thin), 2.90 × 2.80 mm** | S9 Package Information |

**On the ~500 mA target:** TPS22950C's I<sub>LIM</sub> range starts at **0.5 A**,
so 500 mA is the **extreme bottom of the adjustable range**, not a comfortable
setpoint. The base TPS22950 reaches 0.05 A but is WCSP-only and fails the leaded
requirement. **Recommend 600–800 mA**, with R<sub>ILIM</sub> left as an accessible
tuning resistor (§H) so it can be re-set after the accessory power budget exists.
**R<sub>ILIM</sub> not locked**, per ruling C.

**Additional recommendations:**

- **`FLT` (open-drain, pulled low on thermal shutdown or reverse-current) should
  go to a spare `U2` input.** It converts an invisible fault into a UI message,
  and it costs one pin the rebalance already has.
- **TVS on both the switched rail and every signal pin at the connector.** The
  switch's absolute maximum is 5.5–6 V: an accessory applying 5 V survives, one
  applying 12 V does not. Document that.
- Honest caveat: RCB is a comparator (~44 mV / ~900 mA, ~3 µs), not a back-to-back
  blocking pair, so a back-powering accessory can push a few hundred mA for a few
  microseconds. Reverse leakage while off is 38 µA. Neither disqualifies it.

---

## G. NFC default configuration and the no-respin fallback

### G.1 Default first build

Per ruling B, and consistent with P-10's recommendation:

| node | first build |
|---|---|
| `NFC_SUPPLY` | **`+3V3`** |
| ST25R3916 `VDD` (pin 8) | `NFC_SUPPLY` |
| ST25R3916 `VDD_TX` (pin 10) | `NFC_SUPPLY` — **always tied to VDD**, per S1 p. 39 (±0.2 V operating, ±0.3 V abs max) |
| ST25R3916 `VDD_IO` (pin 1) | `+3V3` |
| `sup3V` option bit | **set** — S1 Table 119 gives 2.4–3.6 V with `sup3V` |
| ST25R3916 | **FITTED** |
| Matching network | **FITTED, tuned for 3.3 V operation** |
| Antenna | **FITTED** |
| TPS61023 boost path | **DNP, footprint retained** |

**What 3.3 V costs, stated honestly.** ST states on the record that
*"Putting VDD=VDD_TX=3V3 will reduce the achievable output power."* R1's
arithmetic from ST's measured regulator data (AN5584) puts the driver supply at
~2.9–3.1 V versus ~4.6–4.8 V at 5 V — roughly **0.64× antenna current, ~0.41×
radiated power (−3.8 dB), and ~0.7–0.8× practical read range.** That is a
planning estimate derived from ST's measured VDD_RF values, **not an ST
characterisation**, and R1 flags it as such.

**Why 3.3 V is still right for a first build that may skip incremental bring-up:**
it removes every voltage above 3.6 V from the board, which deletes the
VDD_IO-present-while-VDD-absent sequencing question entirely, and it takes a
1 MHz switcher out of the neighbourhood of a 13.56 MHz receiver front end where
external modulation disturbance is what actually limits reliable write
operations.

**Two conditions that are not in the ruling and must not be lost:**

1. **Do not tap `VDD`/`VDD_TX` straight off the 3V3 plane.** Feed through a
   ferrite or 0 Ω with substantial local bulk. Transmit bursts of 100–250 mA with
   microsecond edges would otherwise modulate the rail feeding the ESP32-S3, the
   display and the audio amplifier. **This is the single biggest risk in the 3.3 V
   configuration, and it is a decoupling and layout problem, not a topology one.**
2. **Re-scale the RFI receiver divider.** ST's application material targets a
   receiver input level derived from a 5 V driver. With ~0.64× the transmit
   amplitude, copying a 5 V reference divider leaves the receiver under-driven.
   R1 identifies this as the most commonly missed consequence of dropping the
   supply.

Also raised by R1 and **not decided here: ST25R3916 vs ST25R3916B.** The B adds
Active Wave Shaping and finer driver stepping (both of which recover margin at
3.3 V) but **removes capacitive sensing on CSI/CSO**, which is what enables
low-power capacitive tag detect. If the B is taken with AWS enabled, the VDD_AM
capacitor rule changes (10–50 nF rather than 2.2 µF) — a schematic-time decision,
not a firmware option. **Product call. Raised as P-17.**

### G.2 The no-respin fallback — FIT/DNP matrix

Architecture:

```
  +3V3 ────────────────[ R_SEL_3V3, 0 Ω ]────┐
                                              ├──── NFC_SUPPLY ──── VDD + VDD_TX
  SYS ──[ TPS61023 + L + FB + CIN/COUT ]──[ R_SEL_5V, 0 Ω ]──┘
```

**The two 0 Ω links are mutually exclusive by construction.** Exactly one is
fitted. There is no BOM configuration in which both are fitted, which satisfies
hard requirements 3 and 4 — `+3V3` and the boost output can never be shorted
together, because they are never simultaneously connected to `NFC_SUPPLY`.

| ref | component | **Build 1 (3.3 V)** | After rework (5 V) | rationale |
|---|---|---|---|---|
| `R_SEL_3V3` | 0 Ω link, `+3V3` → `NFC_SUPPLY` | **FIT** | **REMOVE** | the source selector |
| `R_SEL_5V` | 0 Ω link, boost out → `NFC_SUPPLY` | **DNP** | **FIT** | the source selector |
| `U13` | TPS61023 (SOT-563, 6-pin) | **DNP** | **FIT** | see analysis below |
| `L2` | boost inductor | **FIT** | keep | **safe to pre-fit** |
| `R_FB_TOP` / `R_FB_BOT` | FB divider | **FIT** | keep | **safe to pre-fit** |
| `C_BOOST_IN` | boost input cap (on SYS) | **FIT** | keep | **safe to pre-fit** |
| `C_BOOST_OUT` | boost output cap | **FIT** | keep | **safe to pre-fit** |
| `TP_NFC_SUPPLY` | test point | FIT | keep | required |
| `TP_BOOST_OUT` | test point | FIT | keep | required |
| NFC matching network | discrete L/C | **FIT, 3.3 V tuning** | **re-tune** | accessible passives |
| `C_VDD_AM` | 2.2 µF ∥ 1 nF | FIT | value depends on 3916 vs 3916B + AWS | see P-17 |

### G.3 Which inactive-branch components can safely be pre-fitted — the analysis

The CTO asked specifically, and told me not to assume the split. Each component
is judged on one test: **with `U13` absent and `R_SEL_5V` absent, does fitting
this part load, backfeed or disturb `NFC_SUPPLY` or `SYS`?**

| component | pre-fit? | reasoning |
|---|---|---|
| **Boost inductor `L2`** | **YES** | With `U13` absent, the inductor connects `SYS` to an open `SW` pad. No current path, no load. It is also the **hardest part to hand-place later** (a shielded power inductor with large thermal pads) — exactly the part pre-fitting should target. |
| **FB divider** | **YES** | Connects the (isolated) boost output node to GND through a high-value divider. With `R_SEL_5V` absent, that node is isolated from `NFC_SUPPLY`, so the divider loads nothing. Leakage is a few µA into an open node. |
| **Boost input capacitor** | **YES** | Sits on `SYS`, which is a live rail in both configurations. Extra bulk on SYS is harmless and mildly beneficial. |
| **Boost output capacitor** | **YES** | Sits on the isolated boost output node. With `R_SEL_5V` absent it is a floating capacitor to GND — no path to `NFC_SUPPLY`. |
| **`U13` TPS61023 itself** | **NO — keep DNP** | This is the one that must stay off. Fitted with `SYS` live and `EN` low it would sit in shutdown drawing 0.1 µA (S3), which is harmless in itself — **but S3 §7.3.5 documents pass-through operation when V<sub>IN</sub> > V<sub>OUT</sub>**, and any enable-net fault would energise the isolated node. Leaving it DNP means the 5 V branch is dead by construction rather than by an enable signal. **Safety by absence beats safety by configuration on a first build.** |
| **`R_SEL_5V`** | **NO — keep DNP** | It is the mutual-exclusion element. Fitting it would defeat hard requirement 4. |

**So: fit the inductor, the divider and both capacitors; leave the IC and the
5 V select link DNP.** The CTO's suggested split was close, and the analysis
confirms it with one refinement — the reasoning for keeping `U13` DNP is
pass-through and enable-fault risk, not quiescent current.

### G.4 Conversion procedure for one board

| step | operation | component | difficulty |
|---|---|---|---|
| 1 | **Remove** `R_SEL_3V3` | 0402/0603 0 Ω | trivial — iron or tweezers |
| 2 | **Fit** `R_SEL_5V` | 0402/0603 0 Ω | trivial |
| 3 | **Fit** `U13` TPS61023 | **SOT-563, 6-pin, 0.5 mm pitch** | **the only hard step** — hot air or a fine iron with flux; leaded, visible, inspectable |
| 4 | **Re-tune** the NFC matching network | 2–4 accessible 0402/0603 L/C | moderate, iterative with a VNA |
| 5 | **Re-scale** the RFI receiver divider | 2 accessible resistors | trivial |
| 6 | Firmware: clear `sup3V`, re-run `Adjust Regulators`, re-pick driver resistance | — | none |

**Answers to the CTO's explicit questions:**

- **C — soldering operations:** **2 mandatory + 1 IC + up to 6 tuning passives = 3 to 9 operations.**
- **D — difficult fine-pitch components:** **one.** The TPS61023 in SOT-563 (6 leads, 0.5 mm pitch, 1.6 × 1.2 mm). No BGA, no QFN, no bottom-terminated part.
- **E — practical with hot air / iron / tweezers?** **Yes.** Every part is
  leaded or a chip passive, every joint is visible and inspectable, and nothing
  requires professional BGA/QFN rework. This is squarely within a competent
  prototype bench.
- **F — sufficient test points?** With `TP_NFC_SUPPLY` and `TP_BOOST_OUT`:
  **yes.** `TP_NFC_SUPPLY` confirms the delivered rail; `TP_BOOST_OUT` confirms
  boost regulation independently; and probing both **with `R_SEL_5V` absent
  confirms source isolation** — the boost node should read 0 V while
  `NFC_SUPPLY` reads 3.3 V. Add a third at the ST25R3916 `VDD` pin if area
  permits, to catch a bad select-link joint.
- **G — does keeping the fallback damage anything?**

| dimension | assessment |
|---|---|
| NFC routing | **Minor risk, manageable.** The source selector adds one node between `+3V3` and `VDD`/`VDD_TX`. It must be placed tight to the ST25R3916 so the decoupling and the ferrite/bulk feed (§G.1 condition 1) are not compromised by a detour. **This is the one real layout constraint.** |
| RF performance | **Neutral in the 3.3 V build** — the boost is unpopulated, so nothing switches. Pre-fitting the inductor places a magnetic component near the front end; **keep it outside the antenna keepout**, which the floorplan must respect anyway. |
| PCB area | ~6 extra passive sites plus a SOT-563 footprint. Small. |
| Power integrity | **Slightly positive** — the extra SYS bulk from the pre-fitted input capacitor is free margin. |
| Manufacturability | **Neutral.** One more DNP line on an assembly that already has a DNP control document. |

**No serious technical reason to delete the fallback was found. KEEP IT**, per
the CTO's default, with the single layout constraint that the selector must not
lengthen the ST25R3916 supply feed.

---

## H. General first-revision reworkability audit

Beyond NFC. Classified per the CTO's scheme.

| # | rework point | class | rationale |
|---|---|---|---|
| 1 | **IR LED current-limit resistor** — accessible chip resistor, generously sized pad | **HIGH — include** | Drive current is explicitly a design direction, not a lock (ruling D). Range is the whole point of IR and is unmeasurable until the enclosure window exists. One resistor. |
| 2 | **IR LED source-select link** (`+3V3` vs `SYS`) — 0 Ω, mutually exclusive | **HIGH — include** | Same pattern as NFC, same cost. Lets the rail choice be made after measuring rail droop rather than before. |
| 3 | **NFC matching network** — accessible 0402/0603, not under the antenna | **HIGH — include** | Mandatory. The match cannot be finalised until the real antenna and enclosure exist. |
| 4 | **TPS22950C `R_ILIM`** | **HIGH — include** | Ruling C explicitly defers the value. 500 mA is at the bottom of the C variant's range; the setpoint will move. |
| 5 | **Speaker output EMI filter** — footprints for series ferrites + shunt caps, DNP-capable | **HIGH — include** | Filterless Class-D next to two radios and an NFC loop. EMI is not predictable on paper, and retrofitting a filter with no footprints means a respin. |
| 6 | **VBUS-present sense divider** | **HIGH — include** | New circuit, never built. Divider ratio interacts with the expander's input thresholds. |
| 7 | **Reverse-protection sense resistor** | **HIGH — include** | Sets the trip point, which interacts with hot-insertion inrush (P-13). Accessible value change is the cheapest way to resolve Case 11 on real hardware. |
| 8 | **Charger status pull-ups (STAT1/STAT2)** | **MEDIUM — include if area permits** | 20 kΩ is specified and unlikely to move, but the resistors exist anyway; make them accessible rather than buried. |
| 9 | **RF module control pulls** (`SX1262_RXEN`, resets) | **MEDIUM — include if area permits** | Values are conventional; accessibility costs nothing since the resistors are required regardless. |
| 10 | **External antenna pigtail** — u.FL on the module, bulkhead at the shell | **MEDIUM** | Already inherently reworkable: the pigtail is a cable, not a soldered net. No board provision needed beyond connector access. |
| 11 | **Strap / pull values** (GPIO46 pull-down, GPIO3 pull) | **MEDIUM — include if area permits** | Values are judgement calls (§B.3 condition 2 has no numeric spec), so being able to change them is worth the accessible placement. |
| 12 | **Alternate footprints for major ICs** | **LOW — OMIT** | Per instruction. No concrete case exists for any of them, and dual footprints on an IC compromise layout for a possibility nobody has articulated. |
| 13 | **Alternate expander footprint (TCA9535 / PCAL9535A)** | **LOW — OMIT** | If §A's pinout gate passes, they share a footprint and no alternate is needed. If it fails, the swap does not happen. Either way an alternate footprint buys nothing. |

**Signal-integrity guard:** none of items 1–11 sits on a high-speed net. The two
native connector pins, both SPI buses, the I²S group and the USB pair get **no**
rework provisions — series resistors and test points there would cost signal
integrity for no benefit, which the CTO instruction explicitly forbids.

---

## I. Mechanical specification correction

Documentation only. `hardware/beta/mechanical/` was **not touched** and remains
untracked.

**Volume Up and Volume Down are removed from the Full Beta v2 mechanical
requirements.** They never existed electrically — `SW2`–`SW8` are UP / DOWN /
LEFT / RIGHT / A / B / HOME — and their presence in Field Slate v5 §5 was an
industrial-design leftover that risked driving enclosure CAD toward phantom
controls.

Current external product direction, recorded in
[`../architecture/ARCHITECTURE.md`](../architecture/ARCHITECTURE.md):

| face | contents |
|---|---|
| **Front** | display / touch, D-pad, A/B, microphone aperture |
| **Top** | panel antenna connector, IR TX/RX optical area |
| **Left** | antenna storage |
| **Right** | recessed/keyed 20-pin community connector, Power, hidden/recessed BOOT access if appropriate |
| **Bottom** | USB-C, microSD |
| **Rear** | NFC target, speaker opening, branding |

---

## J. FBV2-A1 gate decision

### VERDICT: **FBV2-A1 CANNOT PASS.**

Assessed against the eight criteria in the ruling:

| # | criterion | status |
|---|---|---|
| 1 | 20-pin resource architecture resolved | **YES** — 11 + 2 + 2 + 1 + 1 + 3 = 20, ruling D satisfied (§C) |
| 2 | Expander family resolved | **NO** — PCAL9535A is PASS-WITH-CHANGES, gated on a pin table that could not be obtained (§A) |
| 3 | Native GPIO pair resolved | **NO** — GPIO38 is gated on unverified SX1262 DIO1 behaviour (§B.2, C1) |
| 4 | Default NFC architecture resolved | **YES** — 3.3 V, `sup3V`, VDD = VDD_TX = `NFC_SUPPLY`, VDD_IO = `+3V3` (§G.1) |
| 5 | NFC no-respin fallback resolved | **YES** — architecture, FIT/DNP matrix and rework procedure all defined (§G.2–G.4) |
| 6 | Community accessory power resolved | **YES** — TPS22950C, permanent `+3V3` removed, ILIM deferred by ruling (§F) |
| 7 | Battery / reverse protection resolved **at topology level** | **NO** — the topology is chosen, but **dead-cell recovery (P-11) and the latch-off/inrush interaction (P-13) both change the power tree**, and Case 7's survivability (P-12) is unmeasured |
| 8 | No unresolved issue can fundamentally change the power-tree architecture | **NO** — P-11 adds a switched path across the pass FETs plus an ADC divider. That is a power-tree change, not a value change |

### What specifically prevents PASS

1. **P-11 — dead-cell recovery is unchosen, and it is a power-tree change.**
   Criterion 8 fails on this alone.
2. **P-13 — latch-off versus hot-insertion inrush is unreconciled.** It may force
   a different retry strapping or an inrush element.
3. **Criterion 3 — the native pair depends on an unverified SX1262 DIO1
   property.** If DIO1 is a pulse rather than level-held, `NATIVE_A` reverts to
   GPIO43 and the connector's protection requirements change.
4. **Criterion 2 — the expander pinout gate is open**, and the decision cascades:
   moving `SX1262_DIO1` to an expander input is only sensible with a maskable
   interrupt and an interrupt-status register.

**Criteria 1, 4, 5 and 6 are genuinely resolved and can be treated as frozen.**
Four of eight is real progress and it is recorded as such — but a gate is a gate.

### What would close it

| item | action | effort |
|---|---|---|
| Criterion 2 | Read the printed PCAL9535A pin table; compare pad-by-pad against S8 Figure 5-1; confirm LCSC stock and MPN | one document, one distributor lookup |
| Criterion 3 | Read the SX126x **and** E22-900M22S IRQ sections; confirm DIO1 is level-held | one document |
| Criteria 7, 8 | CTO decision on P-11; bench resolution of P-13 | one decision + one protoboard experiment |

**Three of the four are document reads.** FBV2-A1 is close, and it should not be
forced.

---

## K. Corrections to my own previous work

Recorded explicitly. An engineering record that quietly fixes its own mistakes is
not a record.

| prior claim (FBV2-ARCH-001) | status | correction |
|---|---|---|
| *"in the charge-complete/sleep state **STAT2 toggles**"* | **WRONG** | S6 §7.3.10 verbatim: the toggle occurs **when no battery is present**. Table 7-2 shows charge-complete, sleep and charge-disabled are **one state with both pins HIGH**. |
| *"Connect STAT1 only; leave STAT2 on its test point"* | **WRONG — and rejected by ruling G** | STAT1 is HIGH in **both** charging and charge-complete, so alone it conveys only fault / no-fault. The second bit carries nearly all the information. **Expose both.** |
| *"Recommend discrete back-to-back N-FETs over LTC4368-1, mainly on quiescent current"* | **WITHDRAWN** | Not merely under-specified — **unrealisable at 1S**. Available V<sub>GS</sub> is 0.3–1.5 V; the P-channel variant turns hard on into a reversed cell. The IQ argument was also weak against a ~40–60 µA baseline. |
| *"A reverse-current-blocking load switch is disqualified for the battery position"* | **CONFIRMED CORRECT** | The direction it blocks is charging. |
| *"TPS22918 fails accessory isolation"* | **CONFIRMED CORRECT** | S5 §11; R1 independently confirms, and adds that it has no current limit, no thermal shutdown and no internal ON pull-down. |
| *"Replace with a TPS22913B/C-class switch"* | **SUPERSEDED** | TPS22913B/C is **DSBGA 0.9 × 0.9 mm only** and has **no current limit** — wrong on both packaging and protection for a user-accessible pin. **TPS22950C** is the correct part. |
| *"`NATIVE_B` = GPIO47, `NATIVE_A` = GPIO43"* | **IMPROVED** | GPIO47 confirmed. GPIO43 replaced by **GPIO38**, removing ROM-UART contention from the connector entirely. |
| *"Move `DISP_BL_CTL` to GPIO46"* | **CONFIRMED, and its open condition now closed** | S10 confirms the TPS61169 `CTRL` pin has an internal **pull-down**, not a pull-up. |
| U9 pin mapping, VDD/VDD_TX inseparability | **CONFIRMED CORRECT** | Unchanged. |

---

## L. Items requiring CTO decision or second opinion

| # | item | why |
|---|---|---|
| **P-11** | Dead-cell recovery architecture | Blocks FBV2-A1. Power-tree change. R1-trickle recommended, not approved |
| **P-12** | BQ25185 BAT survivability of a brief −0.35 V excursion | Abs max is a DC limit, not an energy limit. Bench measurement |
| **P-13** | Latch-off vs hot-insertion inrush | Blocks FBV2-A1. May force different retry strapping |
| **P-14** | MAX17048 sense point — cell side vs protected side | ~51 mΩ of uncompensable IR drop vs exposure to the reversed-cell fault |
| **P-15** | 3V3 rail budget under simultaneous worst case | May force firmware mutual-exclusion between radios and audio |
| **P-16** | Repurpose one XGPIO as `ACC_DETECT`? | Changes the published XGPIO count from 11 to 10 |
| **P-17** | ST25R3916 vs ST25R3916B | Capacitive tag-detect vs Active Wave Shaping. Changes the VDD_AM capacitor. Product call |
| **P-18** | Accessory I²C segmentation — buffer alone, or add a mux? | R1 raises bus-hang and address-collision; a hung accessory currently blinds the fuel gauge and all XGPIO |

---

## Sources

- TI [BQ25185 SLUSF65A](https://www.ti.com/lit/ds/symlink/bq25185.pdf) · [TCA9535 SCPS201E](https://www.ti.com/lit/ds/symlink/tca9535.pdf) · [TPS22950 SLVSFJ2B](https://www.ti.com/lit/gpn/tps22950) · [TPS61169](https://www.ti.com/lit/ds/symlink/tps61169.pdf) · [TPS61023 SLVSF14B](https://www.ti.com/lit/ds/symlink/tps61023.pdf) · [TCA9517A SCPS245E](https://www.ti.com/lit/ds/symlink/tca9517a.pdf) · [TPS22910A](https://www.ti.com/product/TPS22910A)
- ST [ST25R3916 DS12484 Rev 3](https://www.st.com/resource/en/datasheet/st25r3916.pdf) (repo copy)
- Espressif [ESP32-S3 Datasheet v2.2](https://www.espressif.com/sites/default/files/documentation/esp32-s3_datasheet_en.pdf)
- ADI [LTC4368](https://www.analog.com/en/products/ltc4368.html) — **PDF not retrieved; product-page evidence only**
- NXP [PCAL9535A product page](https://www.nxp.com/products/interfaces/ic-spi-i3c-interface-devices/general-purpose-i-o-gpio/low-voltage-16-bit-ic-bus-i-o-port-with-interrupt-and-agile-i-o:PCAL9535A) — **PDF not retrieved; product-page evidence only**
- [Independent review FBV2-CTO2-PWRNFC-001](../reviews/2026-08-22-independent-cto-power-nfc-review.md) — advisory
