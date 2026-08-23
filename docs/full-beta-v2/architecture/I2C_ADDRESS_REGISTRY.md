# AQROOT Full Beta v2 — I²C address registry

**Status: NORMATIVE (D-142).** This file is the definitive address map for both the internal
bus and the external community segment. Where an older audit, transcript or README disagrees,
this file wins; [`../CTO_DECISIONS.md`](../CTO_DECISIONS.md) outranks it.

Established: 2026-08-23 (FBV2-S1-005). Updated 2026-08-23 (FBV2-S1-008 — `U23` at `0x22`; FBV2-S1-009 — TCA4307, P-18 closed, bus-scan list corrected).
Derived from a `kicad-cli` netlist export of `hardware/beta-v2/kicad/aqroot-beta-v2/`, not from
a pin-map document. **Regenerate it the same way before quoting it.**

All addresses are **7-bit**. Every device on the design is 7-bit addressed; none uses 10-bit.

---

## 1. Topology — one bus, two segments

```
  ESP32-S3 GPIO1 (SDA) / GPIO2 (SCL)
        │
        ├─ R19 / R20   2.2 k to +3V3          <-- the ONLY internal pull-up pair (D-139)
        │
   I2C_SDA_INT / I2C_SCL_INT   ..... INTERNAL SEGMENT
        ├─ U2   expander        0x20
        ├─ U3   expander        0x21
        ├─ U23  expander        0x22   (NEW, FBV2-S1-008 / D-165)
        ├─ U4   BMI270          0x68   (0x69 available by rework, D-140)
        ├─ U14  MAX17048        0x36
        ├─ J1 pins 44/45 -> ER-TPC035-6 / FT6236   0x38
        ├─ TP4 / TP5
        └─ U16  TCA4307DGKR   IN side (SDAIN / SCLIN)      <-- FBV2-S1-009, FITTED
                   │  VCC = ACC_3V3_SW, EN = ACC_PWR_EN
                   │  unpowered => BOTH sides high-Z (datasheet property)
                   │  1 V precharge; IN is not joined to OUT until STOP or bus idle
                   │  stuck-bus disconnect at 25 ms MIN, then up to 16 SCL recovery pulses
                   ▼  OUT side (SDAOUT / SCLOUT)
        R49 / R50 1.5 k to ACC_3V3_SW  (FITTED)
        R47 / R48 22 R  ──  J5 community port, contacts 2 and 6  ..... EXTERNAL SEGMENT
```

**The two segments are one address space whenever the accessory rail is on.** The buffer is
transparent to addressing; it isolates *electrically*, never *logically*. That is the whole
reason this registry exists.

---

## 2. Internal segment — assigned addresses

| addr | device | ref | strap that sets it | verified |
|---|---|---|---|---|
| **0x20** | 16-bit I/O expander | `U2` | `A0` = `A1` = `A2` = GND | **datasheet, this task** — `0 1 0 0 A2 A1 A0` (TI TCA9535 §7.5.2); PCAL9535A shares the base |
| **0x21** | 16-bit I/O expander | `U3` | `A0` = `+3V3`, `A1` = `A2` = GND | **datasheet, this task** |
| **0x22** | 16-bit I/O expander | `U23` | `A1` = `+3V3`, `A0` = `A2` = GND | **datasheet, FBV2-S1-008** — `0 1 0 0 A2 A1 A0`, PCAL9535A Rev. 2 §7.1 |
| **0x36** | fuel gauge MAX17048 | `U14` | fixed, no strap | **carried** — see §5 |
| **0x38** | capacitive touch, FT6236 in the `ER-TPC035-6` | via `J1` 44/45 | fixed in the module | **carried** — see §5 |
| **0x68** | 6-axis IMU BMI270 | `U4` | `SDO` → GND through **`R118` 0 Ω FIT** | **datasheet, this task** — *"The default I²C address of the device is 0b1101000 (0x68). It is used if the SDO pin is pulled to GND."* |
| *(0x69)* | *same device, rework only* | `U4` | remove `R118`, fit **`R119` 0 Ω** to `+3V3` | **datasheet, this task** — *"The alternative address 0b1101001 (0x69) is selected by pulling the SDO pin to VDDIO."* |

**`U16` TCA4307 has no address.** It is a buffer, not a target. **It does not isolate addressing and is not meant to**: see §3 and D-178.

### Collision audit

- The six live values `0x20, 0x21, 0x22, 0x36, 0x38, 0x68` are **pairwise distinct**. No
  collision. **`0x22` was taken by `U23` at FBV2-S1-008 (D-165)**; it was previously listed as an
  at-risk adjacent-family address and is now a live internal device.
- None falls in the I²C reserved ranges **`0x00`–`0x07`** or **`0x78`–`0x7F`**.
- The general-call address `0x00` is not used by any device here.
- The **three** expanders occupy one address each; the family spans `0x20`–`0x27`, so
  **`0x23`–`0x27`** remain *adjacent-family* addresses and are treated as at-risk (§4).
- **Bus loading with the third device:** the PCAL9535A adds C_i ≤ 6 pF per line, so the measured
  ≈ 85 pF becomes roughly **95 pF** and the rise time with `R19`/`R20` = 2.2 kΩ moves from
  **158 ns to about 177 ns**, against the 300 ns fast-mode limit.
- The IMU's alternate `0x69` is held in reserve and must not be assigned to anything else.

---

## 3. External segment — reserved addresses

| addr | reservation | authority |
|---|---|---|
| **0x50** | optional **AQROOT accessory-identification EEPROM**. Protocol reservation only — no main-board hardware, and **no accessory is required to carry one**. | **D-095 / O-2** |
| 0x20, 0x21, **0x22**, 0x36, 0x38, 0x68 | **RESERVED — an accessory MUST NOT use these.** They are live internal devices and a duplicate would make the touch panel, fuel gauge or expanders unreachable. **`0x22` joined the list at FBV2-S1-008 (D-165).** | D-142 / D-165 |
| 0x69 | **RESERVED** — the IMU's rework address. | D-140 |
| 0x00–0x07, 0x78–0x7F | reserved by the I²C specification. | I²C-bus spec |

> **`0x50` is NOT used internally and must not become an internal address.** That is a standing
> constraint, not a preference.

**P-19 remains FUTURE PROTOCOL SCOPE, not an open hardware question:** the 24Cxx EEPROM family
occupies **`0x50`–`0x57`** depending on its `A0`–`A2` straps. **Only `0x50` is reserved and
D-178 declined to widen it** — there is no concrete multi-EEPROM need today, and reserving eight
addresses against a hypothetical costs accessory authors seven usable addresses.

> **P-18 IS CLOSED — 2026-08-23, D-178 (FBV2-S1-009). NO I²C MUX.** The bus-hang half was already
> answered by the detect-gated rail; the **TCA4307** now answers it structurally, disconnecting a
> stuck bus after 25 ms and clocking it free. **Address collision is not an electrical problem
> and a mux is the wrong tool for it.** The external segment stays one logical address space with
> the internal bus, and allocation is governed by this file. Putting the whole internal AQROOT bus
> behind a mux would add a part, a failure mode and a firmware dependency to solve something a
> published reserved-address policy already solves.

---

## 4. Rules for community accessories

1. **Do not use a reserved address.** The set is `0x20`, `0x21`, **`0x22`**, `0x36`, `0x38`,
   `0x50`, `0x68`, `0x69`, plus the I²C-specification reserved ranges.
2. **Prefer `0x40`–`0x4F` or `0x58`–`0x67`.** These are clear of everything AQROOT uses and
   clear of the expander family's `0x20`–`0x27` block.
3. **Treat `0x22`–`0x27` as at-risk.** They are unassigned today, but they belong to the same
   expander family, and AQROOT may add a third expander (B-37 records that both current
   expanders are effectively full).
4. **A hardware buffer does not fix a collision.** The TCA9517A — and any hot-swap or hot-plug
   replacement for it — passes addresses through unchanged. Collision is a *protocol* problem.
   It is solved by this registry and by the `0x50` ID EEPROM, not by silicon.
5. **A collision is not merely "the accessory does not work".** A duplicate at `0x20`, `0x21`,
   `0x36` or `0x38` takes the **touch panel, the fuel gauge or the button expanders** down with
   it. Those are core-product functions.
6. **`0x68` is the highest-risk address in the map.** MPU6050, MPU9250, ICM-20948 and the
   DS3231/DS1307 RTC families all default to it, which is precisely what a cheap accessory
   module is built from. The `R118`/`R119` strap (D-140) exists so that this can be escaped by
   **rework rather than respin** — but the first defence is this document.

---

## 5. Verification status — stated honestly

| addr | how it is known |
|---|---|
| 0x20 / 0x21 | **Datasheet-cited in FBV2-S1-005.** TI TCA9535 (SCPS243), device-address field `0 1 0 0 A2 A1 A0`; strap levels read from the netlist. |
| 0x68 / 0x69 | **Datasheet-cited in FBV2-S1-005.** `BST-BMI270-DS000-08` Rev 1.6, §6.2 and the primary-interface mapping table. |
| 0x36 | **CARRIED, not re-verified here.** Every fetch of the MAX17048 datasheet failed in this environment (analog.com timed out; the Mouser mirror returned 13 kB of HTML). The value is consistent across the pre-design audit, `ARCHITECTURE.md` and D-095. **B-60 — confirm by bus scan at first article.** |
| 0x38 | **CARRIED, not re-verified here.** FocalTech / display-vendor fetches returned 403 and empty bodies. Consistent across D-074…D-078 and the display closeout, and the same controller was already a known quantity at `0x38` on the previous panel. **B-60 — confirm by bus scan at first article.** |
| 0x50 | Reservation, not a measurement. No hardware exists at this address on the main board. |

**A bus scan at first article closes B-60 in about ten seconds** and is the only honest way to
retire it, so it is a first-article step rather than a document-editing exercise.

---

## 6. Bring-up

Per the standing rule: **100 kHz first, then 400 kHz** after the full bus is validated.
With `R19`/`R20` at 2.2 kΩ the worst-case rise time is **158 ns** against the 300 ns fast-mode
limit — see [`../audits/2026-08-23-s1-i2c-imu-implementation.md`](../audits/2026-08-23-s1-i2c-imu-implementation.md) §5.
The BMI270 additionally supports Fm+ at 1 MHz; nothing else on the bus is qualified for it and
1 MHz is **not** a supported AQROOT bus speed.

**First-article bus scan must report exactly:** `0x20`, `0x21`, **`0x22`**, `0x36`, `0x38`,
`0x68` with no accessory attached. Any other responder is a defect, not a curiosity.

> **CORRECTED 2026-08-23 (FBV2-S1-009).** This list previously omitted **`0x22`**, which has been
> a live internal device since `U23` landed at FBV2-S1-008. A bring-up engineer following the old
> list would have treated the third expander as an unexpected responder — i.e. as a defect.

**The accessory segment is scanned separately**, after `ACC_3V3_SW` is enabled and the TCA4307
reports `READY` high on `TP44`. **Anything answering there at `0x20`, `0x21`, `0x22`, `0x36`,
`0x38`, `0x68` or `0x69` is a non-compliant accessory** (§4), and the buffer will not save it:
the two segments are one address space whenever the rail is on.
