# AQROOT Demo — exact hardware simplification implementation plan

**Status:** implementation plan only. This document does not authorize or make a
schematic, PCB, netlist, BOM, routing, footprint, or manufacturing-file change.

**Decision:** keep `U2` and `U3`; retain exactly `XGPIO4` and `XGPIO5`; remove/DNP
`U23` only in the same atomic ECO that moves its four Demo-required outputs to
`U3.P00`–`P03`. Preserve the complete switched-accessory-power architecture.

## 1. Evidence and constraints

This plan was checked against a fresh KiCad 10 netlist export of the actual Full
Beta v2 hierarchy and against the live PCB, not inferred from an old pinout. The
authority order used was `CTO_DECISIONS.md`, current schematic/PCB, Demo scope,
then the architecture registries. In particular, the current design is ORDER-B:
`J5.21` is Accessory Detect and `J5.8` is Native B. Older pre-ORDER-B contact
numbers in historical decisions or ledgers do not override the netlist.

The current schematic has **no unassigned U3 I/O**. “Free U3 pin” below means a
pin made free by the same Demo ECO when its public XGPIO function is retired. It
does not mean the pin is free on the unmodified Full Beta v2 design.

## 2. Exact U23-to-U3 reassignment

| required function | current U23 source | current package pin/net | Demo U3 destination | destination package pin | required retained support |
|---|---|---|---|---|---|
| RGB red sink | `U23.P00` | pin 4, `FRONT_RGB_R_N` | `U3.P00` | pin 4 (currently `XGPIO0`) | `R124`, `D13` |
| RGB green sink | `U23.P01` | pin 5, `FRONT_RGB_G_N` | `U3.P01` | pin 5 (currently `XGPIO1`) | `R125`, `D13` |
| RGB blue sink | `U23.P02` | pin 6, `FRONT_RGB_B_N` | `U3.P02` | pin 6 (currently `XGPIO2`) | `R126`, `D13` |
| 5 V load-switch enable | `U23.P04` | pin 8, `ACC_5V_SW_EN` | `U3.P03` | pin 7 (currently `XGPIO3`) | `R131`, `TP47`, `U22` |

This mapping is fixed for the Demo ECO. It keeps the RGB channels in order,
keeps the safety-critical enable separate from the RGB outputs, leaves
`U3.P04/P05` and their already accepted copper untouched as `XGPIO4/XGPIO5`, and
does not use `U3.P06/P07`, whose ordinary through-via escape is the documented
D-333/D-340/D-341 routing wall.

### Are the destination pins truly free?

| destination | schematic today | PCB today | state after the atomic Demo ECO |
|---|---|---|---|
| `U3.4/P00` | connected to `/XGPIO0` and `R51.1` | not free; `/XGPIO0` is routed (19 tracks, 1 via) | free only after `XGPIO0` and its copper are retired; then assign `FRONT_RGB_R_N` |
| `U3.5/P01` | connected to `/XGPIO1` and `R52.1` | not free; `/XGPIO1` is routed (19 tracks, 1 via) | free only after `XGPIO1` and its copper are retired; then assign `FRONT_RGB_G_N` |
| `U3.6/P02` | connected to `/XGPIO2` and `R53.1` | not free; `/XGPIO2` is routed (8 tracks, 2 vias) | free only after `XGPIO2` and its copper are retired; then assign `FRONT_RGB_B_N` |
| `U3.7/P03` | connected to `/XGPIO3` and `R54.1` | not free; `/XGPIO3` is routed (22 tracks, 1 via) | free only after `XGPIO3` and its copper are retired; then assign `ACC_5V_SW_EN` |

Therefore **none is currently free in either representation**. The reassignment
must be one atomic schematic/netlist operation; never temporarily merge an
internal control net with a Community Port contact.

## 3. Exact net changes

### Delete as functional nets

- Delete internal nets `/XGPIO0`, `/XGPIO1`, `/XGPIO2`, `/XGPIO3`, `/XGPIO6`,
  `/XGPIO7`, `/XGPIO8`, and `/XGPIO9`.
- Delete connector-side nets
  `/09_COMMUNITY_HEADER/XGPIO0_HDR`–`XGPIO3_HDR` and
  `/09_COMMUNITY_HEADER/XGPIO6_HDR`–`XGPIO9_HDR` after their J5 contacts are
  explicitly marked no-connect.
- Delete `/08_BUTTONS_EXPANDERS/RESERVED_SPARE`; it has no Demo function.
- Remove the U23-only branches of `+3V3`, GND, `I2C_SDA_INT`, `I2C_SCL_INT`, and
  `WAKE_INT_N`. Do **not** delete or rename those shared nets.
- The generated `unconnected-(U23-Pxx-Padxx)` nets disappear with `U23`; they are
  not design nets to preserve.

### Keep or reassign

- Keep `FRONT_RGB_R_N`, `FRONT_RGB_G_N`, `FRONT_RGB_B_N`, and
  `ACC_5V_SW_EN`, changing only their expander endpoints per section 2.
- Keep `/XGPIO4`, `/XGPIO5`, `XGPIO4_HDR`, and `XGPIO5_HDR` unchanged.
- Keep all non-XGPIO J5 nets unchanged, including both power contacts on each
  switched rail, buffered SDA/SCL, both native GPIOs, `WAKE_ATTN_N`, and
  `ACC_DETECT_N`.
- On the schematic, place explicit no-connect flags on `J5.9`–`J5.12` and
  `J5.15`–`J5.18`. Do not leave misleading XGPIO labels or protection stubs on
  those contacts.

## 4. XGPIO disposition

| identity | current U3 channel/pin | Demo disposition | J5 contact |
|---|---:|---|---:|
| `XGPIO0` | P00 / pin 4 | **internally reused** as `FRONT_RGB_R_N`; no public XGPIO | 9 = NC-DEMO |
| `XGPIO1` | P01 / pin 5 | **internally reused** as `FRONT_RGB_G_N`; no public XGPIO | 10 = NC-DEMO |
| `XGPIO2` | P02 / pin 6 | **internally reused** as `FRONT_RGB_B_N`; no public XGPIO | 11 = NC-DEMO |
| `XGPIO3` | P03 / pin 7 | **internally reused** as `ACC_5V_SW_EN`; no public XGPIO | 12 = NC-DEMO |
| `XGPIO4` | P04 / pin 8 | **KEEP** | 13 |
| `XGPIO5` | P05 / pin 9 | **KEEP** | 14 |
| `XGPIO6` | P06 / pin 10 | **NC-DEMO**; U3 channel left unused | 15 = NC-DEMO |
| `XGPIO7` | P07 / pin 11 | **NC-DEMO**; U3 channel left unused | 16 = NC-DEMO |
| `XGPIO8` | P10 / pin 13 | **NC-DEMO**; U3 channel left unused | 17 = NC-DEMO |
| `XGPIO9` | P11 / pin 14 | **NC-DEMO**; U3 channel left unused | 18 = NC-DEMO |

Firmware must expose only XGPIO4 and XGPIO5 on the Demo. P00–P03 are internal
outputs and must never be advertised or configured as accessory GPIOs.

## 5. J5 Demo disposition, all 24 contacts

| J5 | actual Beta v2 net | Demo disposition |
|---:|---|---|
| 1 | `ACC_5V_SW` | **KEEP** — switched 5 V output |
| 2 | GND | **KEEP** |
| 3 | `ACC_3V3_SW` | **KEEP** — switched 3.3 V output |
| 4 | `EXT_SDA` | **KEEP** — buffered SDA |
| 5 | `EXT_SCL` | **KEEP** — buffered SCL |
| 6 | GND | **KEEP** |
| 7 | `NATIVE_A_HDR` | **KEEP** — Native A / ESP32 GPIO38 |
| 8 | `NATIVE_B_HDR` | **KEEP** — Native B / ESP32 GPIO47 |
| 9 | `XGPIO0_HDR` | **NC-DEMO** |
| 10 | `XGPIO1_HDR` | **NC-DEMO** |
| 11 | `XGPIO2_HDR` | **NC-DEMO** |
| 12 | `XGPIO3_HDR` | **NC-DEMO** |
| 13 | `XGPIO4_HDR` | **KEEP** — working slow expansion GPIO |
| 14 | `XGPIO5_HDR` | **KEEP** — working slow expansion GPIO |
| 15 | `XGPIO6_HDR` | **NC-DEMO** |
| 16 | `XGPIO7_HDR` | **NC-DEMO** |
| 17 | `XGPIO8_HDR` | **NC-DEMO** |
| 18 | `XGPIO9_HDR` | **NC-DEMO** |
| 19 | GND | **KEEP** |
| 20 | `WAKE_ATTN_N_HDR` | **KEEP** — retains the existing accessory-wake gate |
| 21 | `ACC_DETECT_N_HDR` | **KEEP** — Accessory Detect |
| 22 | `ACC_3V3_SW` | **KEEP** — duplicate contact on the same switched rail |
| 23 | GND | **KEEP** |
| 24 | `ACC_5V_SW` | **KEEP** — duplicate contact on the same switched rail |

Both contacts on a rail share its existing total current limit; they do not
double it. Keeping both does not duplicate the switching circuitry and preserves
the reversal-safe ORDER-B physical interface. At least one 5 V contact remains
usable even if the Demo adapter elects to populate only one mating position.

## 6. Parts disposition

### Remove or DNP with U23

- `U23` — PCAL9535A at 0x22.
- `C83` — U23 local 100 nF decoupler.
- `R130` and `TP41` — `RESERVED_SPARE` pull-up and test point.

The U23 address straps are direct rail connections, so there are no address
resistors to remove. Removing U23 also removes its local I2C and `WAKE_INT_N`
fanout; `R19`, `R20`, and `R3` remain because U2/U3 and the internal bus remain.

### Remove or DNP with the eight retired public XGPIOs

- `R51`–`R54` (`XGPIO0`–`XGPIO3`) and the complete TVS array `D3`.
- `R57`–`R60` (`XGPIO6`–`XGPIO9`).
- Keep `D4`, because its channels 1 and 2 protect XGPIO4 and XGPIO5; leave its
  channels 3 and 4 unconnected.
- Keep `D5`, despite removing XGPIO8/9, because its other two channels protect
  `WAKE_ATTN_N_HDR` and `ACC_DETECT_N_HDR`; leave the former XGPIO8/9 channels
  unconnected.
- Keep `R55` and `R56` for XGPIO4/XGPIO5.

### Must remain

- `D13`, `R124`, `R125`, and `R126` for the RGB indicator.
- `R131` 100 kΩ and `TP47` on `ACC_5V_SW_EN`.
- `R98`, `R102`, `R103`, `R129`, and `R17` on the retained U3 accessory
  control/status channels.
- `R19`, `R20`, and `R3` for internal I2C and the shared interrupt.
- The native GPIO and external-I2C protection/series/pull networks, including
  `D2`, `R47`–`R50`, `R61`, and `R62`.
- The Accessory Detect and wake networks, including `R64`, `TP43`, `Q10`,
  `R63`, and `R66`.

The already-approved optional NFC 5 V PA boost remains DNP/removed according to
the Demo 3.3 V NFC decision; it is unrelated to the accessory 5 V rail and must
not be confused with `U21/U22`.

## 7. Accessory-power circuitry that must remain

The following topology is indivisible for the Demo:

1. **Switched 3.3 V:** `+3V3` -> `U20` TPS22950C -> `ACC_3V3_SW`, with
   `ACC_3V3_EN` from `U3.P12`/pin 15, mandatory `R98` 100 kΩ pull-down, the
   existing current-limit resistor `R97`, rail capacitors `C37`, `C39`, and
   `C63`, and fault output into `ACC_POWER_FAULT_N`.
2. **5 V generation:** `BQ25185_SYS` -> `U21` TPS61023 5 V boost ->
   `ACC_5V_RAW`, with `ACC_5V_BOOST_EN` from `U3.P13`/pin 16, mandatory `R102`
   100 kΩ pull-down, `L4`, feedback divider `R99/R100`, input capacitor `C64`,
   and output capacitors `C65/C66`.
3. **Switched/protected 5 V:** `ACC_5V_RAW` -> `U22` TPS22950C -> `ACC_5V_SW`,
   with moved `ACC_5V_SW_EN` from `U3.P03`/pin 7, mandatory `R131` 100 kΩ
   pull-down, `TP47`, current-limit resistor `R101`, rail capacitors `C38` and
   `C67`, reverse blocking, and fault output into `ACC_POWER_FAULT_N`.
4. **Fault handling:** retain the wire-OR of `U20.FLT` and `U22.FLT`, `R103`
   pull-up, test points, and `U3.P15`/pin 18 input.
5. **Detect and external I2C isolation:** retain `ACC_DETECT_N` on `U3.P14`,
   `ACC_PWR_EN` on `U3.P17`, `U16` TCA4307, `R17` safe-low pull-down, external
   pull-ups `R49/R50`, series resistors `R47/R48`, and the Qwiic `J8` path.

No accessory-power IC, current-limit element, fault path, external safe-state
pull, or TCA4307 support part becomes optional merely because U23 is removed.

## 8. D-186 and safe-state/sequencing preservation

D-186 remains fully preserved because the two 5 V controls remain independent:

- `ACC_5V_BOOST_EN`: `U3.P13` -> `U21.EN`, externally low by `R102`.
- `ACC_5V_SW_EN`: moved to `U3.P03` -> `U22.ON`, externally low by `R131`.

The PCAL9535A powers up with all pins high-impedance inputs, output registers
HIGH, pulls disabled, and interrupts masked. The external pull-downs therefore
hold `U20`, `U21`, `U22`, and `U16` safely off/isolated before firmware runs.
The RGB remains dark at reset because its cathode sinks are high-impedance and
then transition to output-HIGH before any active-low colour is asserted.

Firmware ordering is mandatory:

- Power-up: verify `ACC_DETECT_N`; assert `ACC_3V3_EN`; wait at least 5 ms;
  assert `ACC_5V_BOOST_EN`; wait at least 5 ms; then assert
  `ACC_5V_SW_EN`.
- Power-down: deassert `ACC_5V_SW_EN`; wait/confirm the contact is off;
  deassert `ACC_5V_BOOST_EN`; then deassert `ACC_3V3_EN` and `ACC_PWR_EN` in
  the existing controlled shutdown flow.
- Detect loss or `ACC_POWER_FAULT_N` assertion still causes prompt reverse-order
  shutdown. Preserve the existing controlled-isolation method for identifying
  which wire-OR fault source asserted.
- Configure U3 output-port values before changing configuration bits to output.
  Initialize P00–P02 HIGH (RGB off) and P03 LOW/off by external pull; never allow
  P03 to share the XGPIO firmware table.

The first article must re-measure the D-186 5 ms converter-settle assumption and
verify both independent disconnects, reverse-current blocking, detect-loss
shutdown, fault shutdown, and no 5 V contact pulse during reset or I2C recovery.

## 9. PCB copper made obsolete

On the current Beta v2 PCB, the following already-routed internal XGPIO copper
becomes obsolete and must be removed only during the later hardware ECO:

| retired net | current routed copper |
|---|---:|
| `/XGPIO0` | 19 tracks, 1 via, 91.475 mm |
| `/XGPIO1` | 19 tracks, 1 via, 84.499 mm |
| `/XGPIO2` | 8 tracks, 2 vias, 53.817 mm |
| `/XGPIO3` | 22 tracks, 1 via, 118.261 mm |
| `/XGPIO8` | 6 tracks, 1 via, 43.794 mm |
| `/XGPIO9` | 17 tracks, 1 via, 75.200 mm |
| **total** | **91 tracks, 7 vias, 467.046 mm** |

`/XGPIO6` and `/XGPIO7` have no routed track/via copper, so their removal avoids
the documented routing wall rather than deleting accepted copper. Connector-side
`XGPIO*_HDR` nets are presently unrouted and disappear rather than being routed.

The existing U23-to-RGB copper (20 B.Cu tracks total: red 6, green 7, blue 7)
also becomes obsolete when U23 is removed. New U3-to-`R124/R125/R126` routes are
required. `ACC_5V_SW_EN` is presently unrouted, so no accepted enable-route copper
is lost. U23-local branches of the shared supply/I2C/interrupt nets become
obsolete, but shared-net copper serving other devices must not be removed.

Before deleting any track, select by net and prove that no retained pad pair
loses connectivity; do not use a geometric area deletion around U3/U23.

## 10. Expected routing reduction

Relative to completing Full Beta v2 as drawn:

- Eight of ten long public XGPIO paths disappear (80%).
- Ten currently open connector-side connections disappear: eight retired
  `XGPIO*_HDR` nets plus the two presently unrouted internal XGPIO6/XGPIO7 paths.
- The known XGPIO6/XGPIO7 boxed-endpoint wall is eliminated.
- U23 removes one 24-pin package and its local power/I2C/interrupt fanout.
- Four internal routes are still required after reassignment: three RGB sinks
  and `ACC_5V_SW_EN`. Thus the conservative net-program reduction is about
  **six open connections**, before counting U23 local fanout/ratsnest edges.

The benefit is larger than the raw count: it removes six long accepted XGPIO
routes (467 mm and seven vias), avoids two hard routes, and replaces them with
four board-internal control runs. Do not claim an exact final ratsnest reduction
until the Demo schematic is regenerated and the candidate PCB is measured.

## 11. Safe implementation and rollback order

1. Tag/record the current Demo branch and copy the Full Beta v2 KiCad project to
   a Demo-specific project path. Never edit the frozen production reference.
2. Make a **schematic-only atomic ECO**: mark J5 NC contacts; remove the eight
   XGPIO protection branches; move the four control nets to U3; remove U23 and
   its local support. Do not touch power circuitry.
3. Export a fresh netlist and mechanically verify every U2/U3 pin, all 24 J5
   contacts, all accessory-power endpoints, and that 0x22 is absent while 0x20
   and 0x21 remain. Run ERC. Commit this as a rollback boundary.
4. Update firmware pin/address tables in a separate commit: remove U23/0x22,
   expose only XGPIO4/5, apply the new U3 output masks, and retain D-186 ordering.
   Bench-test the register sequence against a mocked/fixture expander before PCB
   routing changes.
5. In a scratch PCB candidate, update from schematic while preserving footprints
   and existing retained copper. First delete only net-identified obsolete copper;
   then prove retained-route connectivity and DRC equivalence.
6. Route the safety-critical `ACC_5V_SW_EN` first and gate it electrically. Route
   the three RGB nets second. Do not move or weaken `R131`; do not accept a route
   that couples the enable to a public contact or creates a reset pulse.
7. Route the two retained XGPIO header paths and all retained non-XGPIO Community
   Port connections. Run full ERC, DRC, netlist-to-PCB comparison, connectivity,
   creepage/clearance, and manufacturing checks.
8. Bring up with accessory power loads disconnected: verify reset-safe OFF, RGB
   off, expander enumeration (0x20/0x21 only), then 3.3 V switching, boost-only
   settling, 5 V load-switch turn-on, reverse shutdown, detect loss, both fault
   sources, TCA4307 isolation/recovery, and finally rated dummy loads.
9. Populate/market J5.9–12 and J5.15–18 as **NC on AQROOT Demo**. Do not use Full
   Beta v2 “10 XGPIO” claims for Demo hardware.
10. Promote the PCB only after all gates pass. If the four replacement routes or
    D-186 tests fail, revert the schematic-only ECO and keep U23; never recover
    schedule by collapsing the two 5 V enables or deleting switched power.

Each stage is independently revertible. U23 removal, pin reassignment, and the
eight NC connector contacts are one functional change and must never be released
partially.

## 12. GO / NO-GO

**GO, conditional, for removing U23:** the capacity and exact reassignment close
electrically, and the Demo loses no required feature. Proceed only through the
atomic U23-to-U3 ECO and only if the new U3-to-RGB/`ACC_5V_SW_EN` routes pass full
connectivity, DRC, reset-safe, and sequencing validation. Otherwise keep U23.

**NO-GO for simplifying or removing switched accessory power:** retain U20, U21,
U22, U16, both independent 5 V enables, all mandatory external pulls, fault and
detect paths, and the D-186 staged sequence. U23 removal is acceptable only
because `ACC_5V_SW_EN` moves intact; it is not permission to collapse the power
architecture.
