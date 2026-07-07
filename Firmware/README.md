# AQROOT firmware

Full working firmware stack for the AQROOT handheld: driver abstraction layer + an
LVGL touch UI (app launcher + tool screens), built on the **Arduino core for ESP32-S3**.
It compiles and runs today — on real hardware once parts arrive, and **right now in the
Wokwi simulator** with radio/NFC/audio mocked so the whole UI is testable end-to-end.

Architecture follows `03 - OS Architecture.md`: apps and the UI shell call only the stable
`src/drivers/*.h` interfaces, never hardware registers, so parts can be swapped without
rewriting the UI.

## Layout

```
Firmware/
  platformio.ini        two envs: esp32-s3-aqroot (hardware) and wokwi (SIMULATION_MODE)
  wokwi.toml            points Wokwi at the wokwi-env build artifacts
  diagram.json          sim wiring: ESP32-S3 + ILI9341 (AMOLED stand-in) + 4 nav buttons
  include/lv_conf.h     LVGL 8.3 configuration
  src/
    config.h            ALL pin assignments + display geometry (one source of truth)
    main.cpp            setup()/loop(): init drivers, LVGL, launcher; input wiring
    drivers/            display, touch, radio, nfc, sensors, audio (real + sim paths)
    ui/
      launcher.*        tile dashboard + Signal Monitor + NFC Tag panels
      screens/          scan, nfc, ir, gpio, bluetooth, tools
```

## Build & flash to real hardware

Requires [PlatformIO](https://platformio.org/) (`pip install platformio` or the VS Code
extension).

```bash
cd Firmware
pio run -e esp32-s3-aqroot                 # build
pio run -e esp32-s3-aqroot -t upload       # flash over USB-C
pio device monitor -b 115200               # serial console
```

The board is `esp32-s3-devkitc-1` for the prototype (bare WROOM-1 module on the final
PCB — same firmware). **Before trusting any peripheral on real hardware, reconcile the
PLACEHOLDER pins in `src/config.h` with the actual PCB pinout** (see the table below).

## Run the Wokwi simulation (no hardware needed)

The `wokwi` build defines `SIMULATION_MODE`. Use the
[Wokwi for VS Code](https://docs.wokwi.com/vscode/getting-started) extension (free, needs
a one-time license) or the Wokwi CLI.

```bash
cd Firmware
pio run -e wokwi                           # build the SIMULATION_MODE firmware
```

Then either:
- **VS Code:** open the `Firmware` folder, press `F1` → **Wokwi: Start Simulator**
  (Wokwi reads `wokwi.toml` + `diagram.json`).
- **CLI:** `wokwi-cli .` from the `Firmware` folder.

### Using the simulation
- The **ILI9341** panel shows the live LVGL dashboard.
- **PREV / NEXT** buttons move the tile selection; **ENTER** opens the selected tool;
  **BACK** returns to the dashboard. (These stand in for the CST816 touchscreen, which
  Wokwi cannot model.)
- The **Signal Monitor** and **Scan** screen show a wandering RSSI around −67 dBm at
  915.2 MHz; the **NFC** screen and NFC panel show UID `04 A2 3B 7C 9D 11 22` — all mock
  data from the simulation build.

## What is real vs mocked in simulation

| Subsystem | In `SIMULATION_MODE` | On real hardware |
|---|---|---|
| Display  | ILI9341 stand-in, real LVGL rendering | LovyanGFX to placeholder ILI9341 config |
| Touch    | 4 physical buttons (keypad nav)       | real CST816 I2C touch |
| Radio    | mock RSSI/frames                      | real RadioLib SX1262 (LoRa + FSK) |
| NFC      | fixed mock UID + fake write ok        | real Adafruit_PN532 read + block write |
| IMU      | mock motion data                      | real generic I2C IMU read |
| Audio    | silent / timed                        | real ESP32 I2S tone + mic capture |

## Driver status: final vs placeholder

**Final choices (real implementations, only wiring is TBD):**
- **Touch — CST816-series** (`touch.cpp`): confirmed final part, real I2C driver.
- **Radio — SX1262 via RadioLib** (`radio.cpp`): confirmed certified module; both LoRa
  and raw sub-GHz FSK/OOK modes implemented.
- **NFC — PN532 via Adafruit_PN532** (`nfc.cpp`): confirmed part; real tag read + Mifare
  Classic block write.

**Placeholder / pending hardware sourcing:**
- **Display panel config** (`display.cpp`): a generic **ILI9341** LovyanGFX config stands
  in for the unsourced 2.13″ **RM69090** AMOLED (502×410). Swap the panel class + geometry
  when the AMOLED arrives; the resolution-independent UI needs no change.
- **IMU part** (`sensors.cpp`): the exact 6-axis IMU (BMI270 vs ICM-42670) is not locked,
  so a **generic MPU-style I2C read** is used with **no external dependency**. When the
  part is chosen, add its library to `platformio.ini` (candidate lines are already noted
  there) and swap the register map / init.
- **Infrared** (`ui/screens/ir_screen.cpp`): UI shell only — there is no `drivers/ir.*`
  yet. IR TX/RX should become an RMT-based driver following the same interface pattern.
- **All pins in `config.h`**: provisional; reconcile with the final PCB pinout. The Wokwi
  `diagram.json` mirrors the display + button pins so the sim and firmware stay in sync.

## Licensing
Firmware is MIT (`../LICENSE-FIRMWARE.md`); hardware design files are CERN-OHL-S v2
(`../LICENSE-HARDWARE.md`).
