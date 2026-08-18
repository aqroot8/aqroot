# AQROOT Beta DM — two-unit LoRa acceptance procedure

The flagship Demo Model function is **two physical AQROOT units talking to each
other over a real 915 MHz LoRa link**. This is the acceptance test for it. The
RF link must be real: no loopback, no simulated packets, no shared bus.

If any **GATE** step fails, the board does not pass. Everything else is
measured and recorded, not pass/fail.

---

## 0. Units under test

Two Beta-DM boards, built to `fab/aqroot-Beta-DM-BOM-fitted.csv` and
`fab/aqroot-Beta-DM-pos-fitted.csv`.

**Before power-on, confirm on both boards that `U9` is NOT fitted.** A fitted
`U9` puts a floating chip select on the SPI-B bus this test depends on — see
`fab/ASSEMBLY-DNP-CONTROL.md` §1.1. A board with `U9` fitted is quarantined,
not tested.

Label them **A** and **B** physically. They are not interchangeable during the
test: A is the initiator throughout.

Firmware: one tree, built for env `esp32-s3-aqroot-dm` (`CONFIG_AQROOT_DM`), so
the speaker, physical NFC and IR blocks are compiled out.

## 1. Hardware present on each unit

| function | reference | must be fitted |
|---|---|---|
| MCU | U1 ESP32-S3-WROOM-1 | yes |
| LoRa radio | U8 Ebyte E22-900M22S (SX1262) | yes |
| RF switch hold-off | R74 100 k on `SX1262_RXEN` | yes |
| reset pull-up | R13 on `SX1262_RST_N` | yes |
| CS pull-up | R27 on `SX1262_CS_N` | yes |
| 915 antenna | Taoglas FXP890.07.0100C flex on the U8 IPEX port | yes |
| display + touch | J1 / SPI-A | yes |
| USB | J3 | yes |
| battery / charger | U11 BQ25185, U12 TPS63020, U15 MAX17048 | yes |
| NFC front end | U9 | **NO — DNP** |

## 2. Signal chain, for probing

| signal | MCU pin | radio pin |
|---|---|---|
| `SPI_B_SCK` | U1.4 (IO4) | U8.18 |
| `SPI_B_MOSI` | U1.5 (IO5) | U8.17 |
| `SPI_B_MISO` | U1.6 (IO6) | U8.16 |
| `SX1262_CS_N` | U1.10 (IO17) | U8.19 |
| `SX1262_BUSY` | U1.12 (IO8) | U8.14 |
| `SX1262_DIO1` | U1.31 (IO38) | U8.13 |
| `SX1262_RST_N` | U2.P01 (TCA9535 expander) | U8.15 |
| `SX1262_RXEN` | U3.P16 (TCA9535 expander) | U8.6 |
| `TXEN` | — strapped to `DIO2` on the module | U8.7 ↔ U8.8 |

Note the two control lines that come from **I2C port expanders, not the MCU**:
`RST_N` from U2.P01 and `RXEN` from U3.P16. The internal I2C bus must be up
before the radio can be reset or its RX path enabled. This is the most likely
place for a bring-up surprise, so it is tested explicitly in step 5.

---

## 3. Power and boot — per unit

| # | step | expected | gate |
|---|---|---|---|
| 3.1 | Inspect: `U9` absent, `U13` absent, `U5` absent, `J6` absent | matches the DNP control document | **GATE** |
| 3.2 | Apply USB power | charger LED behaviour per BQ25185; no part gets warm | **GATE** |
| 3.3 | Measure `+3V3` at a test point | 3.30 V ±5 %, ripple recorded | **GATE** |
| 3.4 | Measure `BQ25185_SYS` | within spec; note that `U13`/`L2` are unfitted loads on this rail and their absence is expected | |
| 3.5 | Confirm no current on `NFC_5V_PA_PENDING` | rail dead by design; `R14` holds `NFC_5V_EN` low | |
| 3.6 | MCU boots, serial banner over USB CDC | firmware identifies itself as the DM build | **GATE** |
| 3.7 | Display lights, touch responds | launcher visible | **GATE** |
| 3.8 | Repeat 3.1–3.7 on the second unit | both units pass | **GATE** |

Record for each unit: serial number, build hash, `+3V3` reading, battery voltage.

## 4. Antenna installation — per unit

| # | step | expected |
|---|---|---|
| 4.1 | Confirm the FXP890 flex is seated on the U8 IPEX port | audible/tactile click; cable strain-relieved |
| 4.2 | Confirm the antenna body is not against metal and not under a hand-grip area | per the RF & Antenna Plan |
| 4.3 | Confirm the enclosure region over the antenna is plastic | no metal in front of the radiator |

The board carries **no RF trace**: the module has its own certified front end
and a matched IPEX port, so the antenna path is entirely mechanical. Do not
probe the RF path on the PCB — there is nothing there to probe. If a VNA check
is wanted, unplug the flex and connect at the module's IPEX port; that port is
the test port.

## 5. Radio bring-up — per unit, before any link test

| # | step | expected | gate |
|---|---|---|---|
| 5.1 | I2C scan finds both expanders (U2, U3) | both ACK | **GATE** |
| 5.2 | Drive `SX1262_RST_N` low then high via U2.P01 | radio resets | **GATE** |
| 5.3 | Read SX1262 status over SPI-B | valid response, `BUSY` deasserts | **GATE** |
| 5.4 | Confirm `SX1262_RXEN` idles low at power-up | `R74` holds the RF switch CLOSED before firmware runs — verify with a scope on the first power-up, not just in firmware | **GATE** |
| 5.5 | Read back the radio's own frequency/PA config after init | matches the intended 915 MHz region setting | **GATE** |
| 5.6 | With `U9` unfitted, confirm SPI-B MISO is clean | no contention, no unexpected idle level | **GATE** |

Step 5.6 is the reason U9 is DNP. Capture a scope trace of `SPI_B_MISO` during
a CC1101 transaction with the SX1262 deselected and keep it with the test
record.

## 6. Two-unit link test — the flagship

Configuration: both units on the same 915 MHz channel, same spreading factor,
bandwidth and coding rate; both use a fixed device identity (A = 0x01,
B = 0x02).

### 6.1 Sequence

1. Power both units, let both complete step 5.
2. Put B into receive.
3. A transmits packet *n* carrying: source ID, destination ID, packet counter.
4. B receives, displays the packet, and transmits an ACK carrying: source ID,
   destination ID, the received counter, and B's measured RSSI and SNR for the
   packet it just received.
5. A receives the ACK and displays the round trip.
6. Repeat.

### 6.2 On-screen fields — both units must display all six

| field | on A | on B |
|---|---|---|
| device identity | own ID and peer ID | own ID and peer ID |
| packet counter | last sent / last acked | last received |
| RSSI | of the ACK it received | of the packet it received |
| SNR | of the ACK it received | of the packet it received |
| ACK / status | ACKED / TIMEOUT / CRC-FAIL per packet | SENT-ACK / RX-CRC-FAIL |
| message or telemetry | payload echoed | payload shown |

### 6.3 Counts and thresholds

| # | test | requirement | gate |
|---|---|---|---|
| 6.3.1 | **200 packets**, A→B with ACK, units 1 m apart on a bench | ≥ 99 % ACKed; **zero** counter gaps that are not explained by a logged timeout | **GATE** |
| 6.3.2 | packet counter integrity | B's received counter is strictly monotonic across the run | **GATE** |
| 6.3.3 | RSSI sanity at 1 m | strong and stable; record min/max/mean | |
| 6.3.4 | SNR sanity at 1 m | positive and stable; record min/max/mean | |
| 6.3.5 | reverse direction: 200 packets B→A | ≥ 99 % ACKed | **GATE** |

### 6.4 Room / distance test

| # | test | requirement | gate |
|---|---|---|---|
| 6.4.1 | **50 packets** at ~10 m, same room, line of sight | ≥ 95 % ACKed; RSSI and SNR recorded | **GATE** |
| 6.4.2 | **50 packets** at ~10 m with one interior wall between the units | packets still get through; RSSI/SNR recorded, pass rate recorded | |
| 6.4.3 | walk-away test: A stationary, B carried away until the link drops | record the distance and the last good RSSI/SNR | |

6.4.2 and 6.4.3 are **characterisation, not pass/fail** — 433/915 flex antennas
in a plastic enclosure are placement-sensitive and the numbers are what we want
to learn. But 6.4.1 is a gate: a demo that only works at arm's length is not a
demo.

### 6.5 Coexistence

| # | test | requirement | gate |
|---|---|---|---|
| 6.5.1 | Repeat 6.3.1 with Wi-Fi active on both units | no significant degradation; record the delta | **GATE** |
| 6.5.2 | Repeat 6.3.1 while the CC1101 is initialised but idle | SPI-B arbitration holds; no lost packets from bus contention | **GATE** |

6.5.2 exercises the one-TX-at-a-time radio manager. The idle radio's chip
select must be driven high, not left floating — a floating CS on the idle radio
corrupts shared MISO, which was learned the hard way in Alpha.

## 7. Optional telemetry

With the IMU (`U4` BMI270) fitted and the microphone (`MK1`) fitted, extend the
payload with a live sensor reading — accelerometer magnitude or a microphone
level — and confirm it changes on screen at the far unit when the near unit is
moved or spoken at. This is the most convincing part of the demo and costs no
extra hardware.

Not a gate. If the microphone bus is not yet routed on the unit under test, use
IMU telemetry only.

## 8. What this procedure deliberately does not test

- **NFC** — `U9` and its boost are DNP; there is no NFC hardware to test. Any
  NFC screen in the DM UI must be clearly marked prototype/simulated.
- **Speaker output** — `U5` and `J6` are DNP.
- **IR transmit and receive** — deferred, parts DNP.

## 9. Record to keep

Per unit: serial, firmware hash, `+3V3`, battery voltage, I2C scan result,
SX1262 status read, `SPI_B_MISO` scope trace from 5.6.
Per link run: date, distance, orientation, packet count, ACK rate, RSSI and SNR
min/max/mean, any counter gaps with their logged cause.
