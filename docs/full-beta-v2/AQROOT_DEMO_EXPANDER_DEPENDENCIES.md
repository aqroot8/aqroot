# AQROOT Demo — GPIO expander dependency analysis

**Scope:** analysis only. No schematic, PCB, footprint, routing, netlist, BOM, or
manufacturing change is authorized by this document.

**Recommendation:** retain `U2` and `U3`; DNP `U23` only as part of a later,
owner-approved schematic/PCB ECO that moves its four Demo-required outputs to
freed `U3` channels. Retain exactly **two expansion GPIOs: `XGPIO4` and
`XGPIO5`**. Leave the other eight physical Community Port contacts electrically
NC and describe them as NC on the Demo.

## Evidence and decision basis

This map was checked against a fresh `kicad-cli` netlist export of the actual
Beta v2 hierarchy, especially `08_buttons_expanders.kicad_sch` and
`09_community_header.kicad_sch`. The netlist, rather than the older expander
audit, controls where they differ: D-186 subsequently assigned `U23.P04` to
`ACC_5V_SW_EN`. `CTO_DECISIONS.md` remains the highest authority.

The Demo scope requires the six front controls, display/touch, RGB indicator,
LoRa, NFC on 3.3 V, speaker, microSD, charging and safety architecture, the
physical 1x24 port, switched 3.3 V, one usable 5 V output, accessory I2C, two
native GPIOs, Accessory Detect, and approximately 2–4 XGPIOs. A channel is not
treated as removable merely because it is not itself exposed at the port.

---

## AS-BUILT PIN MAP — READ THIS ONE (D-738)

> **EVERYTHING BELOW THIS SECTION IS THE PRE-ECO PLANNING ANALYSIS AND IS
> SUPERSEDED.**  It is kept because its *reasoning* — which channels are
> Demo-required and what breaks without them — is still the record of why the
> allocation is what it is.  Its **pin numbers are not**.  It describes a board
> with `U23` fitted and ten public XGPIO, and its `U2` table predates **D-732**
> (which corrected the port-1 D-pad seat order AND an inverted `P05`/`P06`/
> `P16`/`P17` naming) and **D-733** (which swapped `/ACC_PWR_EN` and
> `/BQ25185_STAT1` between `U2.P17` and `U3.P17`).  **Nine of the sixteen `U2`
> rows below and one `U3` row are wrong against the board.**
>
> D-732 recorded that reading the stale map would have masked
> `4Ah` bit 6 — which it believed was `BQ25185_STAT2` but which is in fact
> `TOUCH_INT_N` — silencing the touch interrupt while leaving `STAT2` free to
> wake the MCU forever.  That defect is exactly what an out-of-date pin map
> costs, so the live map is now published here and is generated from the board.

**Provenance.**  The two tables below are read pin by pin out of
`hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb`
(`sha256 71c4326e8cd704db50f0893b8dc0e2490c8f365aaa826d9b05a37c90a3f535b2`)
using the `AQROOT_Beta:PCAL9535APW` symbol's own pin numbering — pins **4..11 =
`P00`..`P07`**, pins **13..20 = `P10`..`P17`** — and they agree pin for pin with
the notes drawn on `08_buttons_expanders.kicad_sch`, which remain the
schematic-side authority.  **Firmware must use this table or the schematic note,
and no earlier one.**

### `U2` — internal controls and inputs, I2C `0x20` (A0=A1=A2=GND)

| bit | pin | net | dir | function |
|---|---|---|---|---|
| `P00` | 4 | `/TOUCH_RST_N` | OUT | capacitive-touch controller reset (active low) |
| `P01` | 5 | `/SX1262_RST_N` | OUT | LoRa transceiver reset (active low) |
| `P02` | 6 | `/NFC_5V_EN` | OUT | optional NFC 5 V boost enable -- DNP path on Demo |
| `P03` | 7 | `/AMP_SD_MODE` | OUT | class-D amplifier shutdown / mode |
| `P04` | 8 | `/DISP_RST_N` | OUT | display reset (active low) |
| `P05` | 9 | `/SX1262_DIO1` | IN | LoRa interrupt -- **UNROUTED, see D-735** |
| `P06` | 10 | `/TOUCH_INT_N` | IN | touch interrupt, FT6236 (active low) |
| `P07` | 11 | `/SD_CARD_DETECT_N` | IN | microSD card detect, R113 100 k pull-up |
| `P10` | 13 | `/08_BUTTONS_EXPANDERS/BTN_A_N` | IN | A / Select, R4 10 k pull-up |
| `P11` | 14 | `/08_BUTTONS_EXPANDERS/BTN_UP_N` | IN | D-pad Up, R5 10 k pull-up |
| `P12` | 15 | `/08_BUTTONS_EXPANDERS/BTN_DOWN_N` | IN | D-pad Down, R6 10 k pull-up |
| `P13` | 16 | `/08_BUTTONS_EXPANDERS/BTN_LEFT_N` | IN | D-pad Left, R7 10 k pull-up |
| `P14` | 17 | `/08_BUTTONS_EXPANDERS/BTN_RIGHT_N` | IN | D-pad Right, R8 10 k pull-up |
| `P15` | 18 | `/08_BUTTONS_EXPANDERS/BTN_B_N` | IN | B / Back, R9 10 k pull-up |
| `P16` | 19 | `/BQ25185_STAT2` | IN | charger status 2 -- R128 10 k pull-up; **`U11.3` UNROUTABLE, see D-734** |
| `P17` | 20 | `/ACC_PWR_EN` | OUT | `U16` TCA4307 community-port I2C buffer enable, R17 100 k pull-down |

### `U3` — front RGB, accessory power, public XGPIO, I2C `0x21` (A0=+3V3)

| bit | pin | net | dir | function |
|---|---|---|---|---|
| `P00` | 4 | `/08_BUTTONS_EXPANDERS/FRONT_RGB_R_N` | OUT | front RGB red cathode sink, R70/R73 |
| `P01` | 5 | `/08_BUTTONS_EXPANDERS/FRONT_RGB_G_N` | OUT | front RGB green cathode sink |
| `P02` | 6 | `/08_BUTTONS_EXPANDERS/FRONT_RGB_B_N` | OUT | front RGB blue cathode sink |
| `P03` | 7 | `/ACC_5V_SW_EN` | OUT | `U22` TPS22950C 5 V load-switch enable, R131 100 k pull-down |
| `P04` | 8 | `/XGPIO4` | I/O | Community Port expansion GPIO 4 (public) |
| `P05` | 9 | `/XGPIO5` | I/O | Community Port expansion GPIO 5 (public) |
| `P06` | 10 | — | — | **NC-DEMO**, unused spare |
| `P07` | 11 | — | — | **NC-DEMO**, unused spare |
| `P10` | 13 | — | — | **NC-DEMO**, unused spare |
| `P11` | 14 | — | — | **NC-DEMO**, unused spare |
| `P12` | 15 | `/ACC_3V3_EN` | OUT | `U20` switched 3.3 V enable, R98 100 k pull-down |
| `P13` | 16 | `/ACC_5V_BOOST_EN` | OUT | `U21` TPS61023 5 V boost enable, R102 100 k pull-down |
| `P14` | 17 | `/ACC_DETECT_N` | IN | accessory present, R129 100 k pull-up |
| `P15` | 18 | `/ACC_POWER_FAULT_N` | IN | wire-OR fault from `U20`/`U22`, R103 100 k pull-up |
| `P16` | 19 | `/SX1262_RXEN` | OUT | LoRa RF receive-path enable, R74 pull-down |
| `P17` | 20 | `/BQ25185_STAT1` | IN | charger status 1, R127 10 k pull-up |

### Interrupt mask policy, as built

Both `/INT` pins are open-drain and wire-OR onto `WAKE_INT_N` (R3 10 k to
`+3V3`, into `GPIO21`).  The PCAL9535A powers up with **every interrupt masked**
(`4Ah`/`4Bh` = `FFh`).

- **UNMASKED on `U2`:** the six buttons (`P10`–`P15`), `TOUCH_INT_N` (`P06`)
  and `SD_CARD_DETECT_N` (`P07`).  `SX1262_DIO1` (`P05`) is unmaskable in
  principle and is what the schematic note lists, but see fact 1 below — while
  the net is unrouted it must stay MASKED and internally pulled.
- **UNMASKED on `U3`:** `ACC_DETECT_N` (`P14`) and `ACC_POWER_FAULT_N` (`P15`).
- **MASKED, deliberately:** `BQ25185_STAT2` — it is **`4Bh` bit 6 (`P16`)**, not
  `4Ah` bit 6 — because SLUSF65A §7.3.10 says it toggles continuously with no
  battery fitted; and both public XGPIO, which is **MX-9** (an accessory must not
  be able to hold the shared wake line and starve the buttons).

### Two as-built facts firmware must not assume away

1. **`/SX1262_DIO1` (`U2.P05`) is NOT ROUTED.**  D-735 measured the corridor as
   four to five conductors over capacity and the residual is an owner /
   industrial-design decision.  Until it is closed, the LoRa driver must poll
   `GetIrqStatus()` over SPI rather than wait on this bit, and the bit must be
   treated as undefined.  **`/SX1262_DIO1` carries exactly two pads — `U2.9` and
   `U8.13` — and NO pull resistor**, so with the net unrouted `U2.P05` is a
   FLOATING CMOS input.  Firmware must therefore enable the PCAL9535A's own
   **internal 100 k pull-up** on that bit (pull-enable `46h`, pull-selection
   `48h`) and keep its interrupt masked.  The same applies to `U3`'s four
   NC-DEMO channels `P06`, `P07`, `P10` and `P11`, which have no external part
   at all.  This capability is one of the reasons D-061 made the PCAL9535A
   load-bearing; the TCA9535 it replaced has no internal pulls.
2. **`/BQ25185_STAT2` reaches `U2.P16` only through `R128`'s pull-up.**  D-734
   proved `U11.3` cannot be escaped at any manufacturable width — the pocket is
   topologically closed by the package's own geometry — so the charger does not
   drive this bit.  Charge-state decode must use `STAT1` (`U3.P17`) and the
   **MAX17048 fuel gauge** on the same internal bus, and must NOT infer a fault
   from `STAT2`.

---

## Complete pin maps (PRE-ECO PLANNING ANALYSIS — SUPERSEDED, KEPT AS HISTORY)

All three devices also connect to `+3V3`, GND, `I2C_SDA_INT`, `I2C_SCL_INT`,
and the shared active-low `WAKE_INT_N`. Their address straps are `U2=0x20`,
`U3=0x21`, and `U23=0x22`.

### U2 — internal controls and inputs (keep)

| channel | net | controlled/observed function | classification | result if U2 is removed |
|---|---|---|---|---|
| P00 | `TOUCH_RST_N` | touch reset | internal, Demo-required | touch becomes non-deterministic/unrecoverable |
| P01 | `SX1262_RST_N` | LoRa reset | internal, Demo-required | LoRa reset/recovery is lost |
| P02 | `NFC_5V_EN` | optional NFC 5 V boost enable | internal, Demo-DNP path | no Demo loss; NFC remains on selected 3.3 V path |
| P03 | `AMP_SD_MODE` | speaker amplifier enable/mode | internal, Demo-required | speaker amplifier remains shut down/undefined |
| P04 | `DISP_RST_N` | display reset | internal, Demo-required | display reset/recovery is lost |
| P05 | `BQ25185_STAT1` | charger status 1 | internal power telemetry | charging still operates autonomously, but charge-state reporting is lost |
| P06 | `BQ25185_STAT2` | charger status/fault 2 | internal power telemetry | charger fault/status visibility is lost; input is intentionally IRQ-masked |
| P07 | `SD_CARD_DETECT_N` | microSD card detect | internal | card-detect indication is lost; SPI storage can still function if firmware does not require detect |
| P10 | `BTN_UP_N` | D-pad Up | internal, Demo-required | front control breaks |
| P11 | `BTN_DOWN_N` | D-pad Down | internal, Demo-required | front control breaks |
| P12 | `BTN_LEFT_N` | D-pad Left | internal, Demo-required | front control breaks |
| P13 | `BTN_RIGHT_N` | D-pad Right | internal, Demo-required | front control breaks |
| P14 | `BTN_A_N` | A/Select | internal, Demo-required | front control breaks |
| P15 | `BTN_B_N` | B/Back | internal, Demo-required | front control breaks |
| P16 | `TOUCH_INT_N` | touch interrupt | internal, Demo-required | touch events/interrupt operation break |
| P17 | `SX1262_DIO1` | LoRa interrupt | internal, Demo-required | normal SX1262 event/packet operation breaks |

`U2` cannot be DNP. At minimum P00, P01, P03, P04, P10–P17 must remain for the
explicit Demo features. P05–P07 should also remain because they are already
landed, low-complexity observability inputs and preserve the intended charging
and microSD behavior. Only P02 is unnecessary in the selected 3.3 V NFC Demo
configuration; its related optional 5 V NFC branch is already a DNP decision.

### U3 — Community Port, accessory power, and one internal LoRa control (keep)

| channel | net | controlled/observed function | classification | result if U3 is removed |
|---|---|---|---|---|
| P00–P07 | `XGPIO0`–`XGPIO7` | slow bidirectional expansion I/O | Community Port only | corresponding port contacts become NC |
| P10–P11 | `XGPIO8`–`XGPIO9` | slow bidirectional expansion I/O | Community Port only | corresponding port contacts become NC |
| P12 | `ACC_3V3_EN` | `U20` switched 3.3 V enable | Community Port support | required 3.3 V accessory/Qwiic power is unavailable |
| P13 | `ACC_5V_BOOST_EN` | `U21` 5 V boost enable | Community Port support | required 5 V output is unavailable |
| P14 | `ACC_DETECT_N` | dedicated accessory-present input | Community Port, explicitly Demo-required | Accessory Detect breaks |
| P15 | `ACC_POWER_FAULT_N` | wire-OR fault from `U20`/`U22` | Community Port safety/support | controlled fault shutdown/visibility is lost |
| P16 | `SX1262_RXEN` | LoRa RF receive-path enable | **internal**, Demo-required | LoRa receive operation breaks |
| P17 | `ACC_PWR_EN` | enables fitted `U16` TCA4307 | Community Port support | external I2C/Qwiic buffer remains disabled |

`U3` cannot be DNP in place. The exact non-XGPIO channels that must remain are
P12–P17. This is the critical finding that prevents treating `U3` as merely a
Community Port GPIO bank. For the recommended Demo allocation, P04 and P05 also
remain externally exposed as `XGPIO4` and `XGPIO5`; other freed GPIO channels
provide the capacity to absorb the required `U23` outputs in a later ECO.

### U23 — RGB, 5 V load-switch sequencing, and spare capacity (conditional DNP)

| channel | net | controlled/observed function | classification | result if U23 is removed in place |
|---|---|---|---|---|
| P00 | `FRONT_RGB_R_N` | RGB red sink | internal, Demo-required | red status component is lost |
| P01 | `FRONT_RGB_G_N` | RGB green sink | internal, Demo-required | green status component is lost |
| P02 | `FRONT_RGB_B_N` | RGB blue sink | internal, Demo-required | blue status component is lost |
| P03 | `RESERVED_SPARE` | pulled-up test/reserve point | neither Demo feature nor port | no Demo loss |
| P04 | `ACC_5V_SW_EN` | `U22` 5 V load-switch enable | Community Port support, Demo-required | required 5 V contact remains off |
| P05–P07, P10–P17 | unconnected | eleven ordinary spares | unused | no Demo loss |

`U23` cannot simply be DNP on the current schematic. It can be eliminated
without losing a Demo feature because reducing ten XGPIOs to two frees eight
channels on retained `U3`, while `U23` has only four required outputs. A later
ECO should move `FRONT_RGB_R_N`, `FRONT_RGB_G_N`, `FRONT_RGB_B_N`, and
`ACC_5V_SW_EN` to four freed `U3` channels, retaining their existing LED series
resistors and the mandatory `ACC_5V_SW_EN` pull-down. The exact destination
pins should be selected during placement/routing, after freezing P04/P05 as
XGPIO4/XGPIO5; no pin move is authorized here.

If the owner does not approve that reassignment, **keep U23**. DNP'ing it in
place violates both the RGB and usable-5-V Demo requirements.

## Minimum XGPIO requirement and 2/3/4-channel comparison

Accessory Detect uses its dedicated `ACC_DETECT_N` contact and consumes **zero
XGPIOs**. Qwiic sensing and displays consume zero XGPIOs. The Proto/Breadboard
Adapter can expose I2C, both native GPIOs, power, detect, and the retained
XGPIOs. A basic two-relay/control demonstration needs two controllable lines;
using the two XGPIOs leaves both native GPIOs available for timing-sensitive or
other breadboard work. Therefore the practical minimum satisfying all stated
Demo use cases is **two XGPIOs**.

| retained XGPIOs | capability change | expander consequence | routing/parts consequence |
|---|---|---|---|
| **2: XGPIO4, XGPIO5** | two relay/control lines plus both native GPIOs and I2C | keep U2/U3; U23 remains conditionally removable | both channels share existing `D4`; both routes have accepted promoted evidence |
| 3: XGPIO4–XGPIO6 | one extra slow control line | no expander change | adds `R57` and a long route; still uses only `D4`, but XGPIO6 has a documented U3 escape wall |
| 4: XGPIO4–XGPIO7 | two extra slow control lines | no expander change | adds `R57`, `R58` and two difficult routes; still only `D4`, but both channels have documented endpoint walls |

Keeping 2, 3, or 4 XGPIOs does **not** materially change which expanders must
remain: U2 and U3 remain, and U23 can be removed only by relocating its four
required outputs. It does materially change routing risk. The third and fourth
choices are exactly the XGPIO6/XGPIO7 pair for which ordinary through-via escape
was exhausted in D-333/D-340/D-341. They add no new protection-package saving
or feature required by the Demo scope. `XGPIO4`/`XGPIO5` are therefore the
minimum-complexity identities, not arbitrary numbering.

## Parts made unnecessary by the recommended reduction

These are consequences for a future ECO/BOM decision, not changes made now.

- Removing `XGPIO0`–`XGPIO3` makes `R51`–`R54` and the complete four-channel
  TVS `D3` unnecessary; J5 contacts 9–12 become NC.
- Removing `XGPIO6`–`XGPIO9` makes `R57`–`R60` and the complete four-channel
  TVS `D5` unnecessary; J5 contacts 15–18 become NC.
- Retaining `XGPIO4`/`XGPIO5` requires `R55`, `R56`, and `D4`. D4's two unused
  channels may remain unconnected. J5 contacts 13 and 14 remain functional;
  contacts 9–12 and 15–18 must not be marketed as GPIO on the Demo.
- Conditional DNP of `U23` makes its local decoupler `C83`, `R130`, and `TP41`
  unnecessary, and removes the `0x22` address and its I2C/interrupt fanout.
  Its address straps are direct rail connections, not removable resistors.
- `R124`–`R126` and RGB LED `D13` remain required after moving the RGB control
  nets. `R131` and `TP47` remain with moved `ACC_5V_SW_EN`; D-186 explicitly
  makes `R131` mandatory. U21/U22 and their support networks remain required.
- `R98`, `R102`, `R103`, `R129`, and `R17` remain required with U3 P12–P17.
  The internal I2C pull-ups `R19`/`R20` and shared interrupt pull-up `R3` remain
  required because U2/U3 and the other internal I2C devices remain.
- U2 channel pull resistors remain except that the already-DNP NFC 5 V path may
  omit the P02 control branch's associated optional boost population according
  to the existing Demo decision. Do not remove charger, button, touch, display,
  microSD, or LoRa support pulls listed in the U2 table.

## Complexity reduction estimate and approval caveats

Relative to routing all ten XGPIOs and three expanders, the recommendation
eliminates **8 of 10 long Community Port XGPIO routes (80%)**, eight series
resistors, two TVS arrays, one 24-pin expander, its decoupler, one reserved-spare
pull/test branch, and its I2C/address/interrupt fanout. It also avoids the known
XGPIO6/XGPIO7 routing wall. At whole-board level the reduction is more modest:
roughly eight rest-of-board nets plus one local IC fanout, approximately **5%
of the 164-net rest-routing program by net count**, with a disproportionately
large congestion benefit in the U3-to-port corridor. This is an engineering
estimate; it is not a rerouted-board measurement.

Owner approval is required before implementing two coupled departures from Full
Beta v2: (1) eight connector positions will be electrically NC on the Demo, and
(2) eliminating U23 changes the D-186 physical implementation of RGB and 5 V
sequencing. The future ECO must preserve independent `ACC_5V_BOOST_EN` and
`ACC_5V_SW_EN`, their mandatory external pull-downs, the specified staged
power-up/power-down sequence, fault response, RGB safe-off behavior, expander
power-up configuration, and firmware address/pin mapping. If that ECO proves
geometrically worse than keeping U23, retain U23; do not sacrifice the status
indicator or 5 V safety architecture merely to remove the package.

## Final disposition

- **KEEP:** `U2` and `U3`.
- **DNP conditionally:** `U23`, only after its RGB and 5 V switch-enable outputs
  are reassigned to freed U3 pins and the complete safety/DRC/firmware review
  passes. Otherwise keep it.
- **KEEP XGPIO:** exactly **2 — `XGPIO4` and `XGPIO5`**.
- **Estimated routing reduction:** 80% of XGPIO long-haul routing; about 5% of
  the rest-net program by count, plus removal of one expander fanout and major
  congestion/routing-wall avoidance.
- **Owner caveat:** approve the Demo-only NC contacts and the U23-to-U3 output
  reassignment while explicitly preserving D-186 5 V sequencing and safe-state
  behavior.
