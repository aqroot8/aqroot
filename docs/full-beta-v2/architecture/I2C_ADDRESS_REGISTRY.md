# AQROOT Full Beta v2 — I²C address registry

**Status: NORMATIVE (D-142).** This file is the definitive address map for both the internal
bus and the external community segment. Where an older audit, transcript or README disagrees,
this file wins; [`../CTO_DECISIONS.md`](../CTO_DECISIONS.md) outranks it.

Established: 2026-08-23 (FBV2-S1-005)
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
        ├─ U4   BMI270          0x68   (0x69 available by rework, D-140)
        ├─ U14  MAX17048        0x36
        ├─ J1 pins 44/45 -> ER-TPC035-6 / FT6236   0x38
        ├─ TP4 / TP5
        └─ U16  TCA9517A  A-side
                   │  VCCB = ACC_3V3_SW, EN = ACC_PWR_EN   (U16 is DNP today)
                   │  unpowered => BOTH sides high-Z
                   ▼  B-side
        R47 / R48 22 R  ──  J5 community header    ..... EXTERNAL SEGMENT
        R49 / R50 4.7 k to ACC_3V3_SW  (DNP)
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
| **0x36** | fuel gauge MAX17048 | `U14` | fixed, no strap | **carried** — see §5 |
| **0x38** | capacitive touch, FT6236 in the `ER-TPC035-6` | via `J1` 44/45 | fixed in the module | **carried** — see §5 |
| **0x68** | 6-axis IMU BMI270 | `U4` | `SDO` → GND through **`R118` 0 Ω FIT** | **datasheet, this task** — *"The default I²C address of the device is 0b1101000 (0x68). It is used if the SDO pin is pulled to GND."* |
| *(0x69)* | *same device, rework only* | `U4` | remove `R118`, fit **`R119` 0 Ω** to `+3V3` | **datasheet, this task** — *"The alternative address 0b1101001 (0x69) is selected by pulling the SDO pin to VDDIO."* |

**`U16` TCA9517A has no address.** It is a repeater, not a target.

### Collision audit

- The six live values `0x20, 0x21, 0x36, 0x38, 0x68` are **pairwise distinct**. No collision.
- None falls in the I²C reserved ranges **`0x00`–`0x07`** or **`0x78`–`0x7F`**.
- The general-call address `0x00` is not used by any device here.
- Both expanders occupy **one** address each; the family spans `0x20`–`0x27`, so `0x22`–`0x27`
  are *adjacent-family* addresses and are treated as at-risk (§4).
- The IMU's alternate `0x69` is held in reserve and must not be assigned to anything else.

---

## 3. External segment — reserved addresses

| addr | reservation | authority |
|---|---|---|
| **0x50** | optional **AQROOT accessory-identification EEPROM**. Protocol reservation only — no main-board hardware, and **no accessory is required to carry one**. | **D-095 / O-2** |
| 0x20, 0x21, 0x36, 0x38, 0x68 | **RESERVED — an accessory MUST NOT use these.** They are live internal devices and a duplicate would make the touch panel, fuel gauge or expanders unreachable. | D-142 |
| 0x69 | **RESERVED** — the IMU's rework address. | D-140 |
| 0x00–0x07, 0x78–0x7F | reserved by the I²C specification. | I²C-bus spec |

> **`0x50` is NOT used internally and must not become an internal address.** That is a standing
> constraint, not a preference.

**P-19 remains open:** the 24Cxx EEPROM family occupies **`0x50`–`0x57`** depending on its
`A0`–`A2` straps. Only `0x50` is reserved. If multi-EEPROM accessories appear, the reservation
may have to widen to the full block. Flagged for CTO with P-18.

---

## 4. Rules for community accessories

1. **Do not use a reserved address.** The set is `0x20`, `0x21`, `0x36`, `0x38`, `0x50`, `0x68`,
   `0x69`, plus the I²C-specification reserved ranges.
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

**First-article bus scan must report exactly:** `0x20`, `0x21`, `0x36`, `0x38`, `0x68` with no
accessory attached. Any other responder is a defect, not a curiosity.
