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
  diagram.json          sim wiring: ESP32-S3 + ILI9341 (the real panel) + 4 nav buttons
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
- The **ILI9341** panel shows the live LVGL dashboard. It is **display-only** — Wokwi has
  no touch model, so clicking the rendered screen does nothing. All input goes through
  the four pushbutton parts next to the board.
- **PREV / NEXT** buttons move the tile selection (a focus outline shows the selected
  tile); **ENTER** opens the selected tool; **BACK** returns to the dashboard. (These
  stand in for the FT6236 touchscreen, which Wokwi cannot model.) Button presses are
  latched by GPIO interrupts, so a quick click registers even though the simulation runs
  slower than real time.
- The **Signal Monitor** and **Scan** screen show a wandering RSSI around −67 dBm at
  915.2 MHz; the **NFC** screen and NFC panel show UID `04 A2 3B 7C 9D 11 22` — all mock
  data from the simulation build.

## What is real vs mocked in simulation

| Subsystem | In `SIMULATION_MODE` | On real hardware |
|---|---|---|
| Display  | ILI9341 (the real panel), real LVGL rendering | LovyanGFX ILI9341 config |
| Touch    | 4 physical buttons (keypad nav)       | FT6236 I2C touch @ 0x38 |
| Radio    | mock RSSI/frames                      | RadioLib SX1262 only — no CC1101 yet |
| NFC      | fixed mock UID + fake write ok        | Adafruit_PN532 — **wrong part**, see below |
| IMU      | mock motion data                      | generic I2C read — insufficient for BMI270 |
| Audio    | silent / timed                        | real ESP32 I2S tone + mic capture |

## Driver status vs the locked Beta design

**Matches the locked design:**
- **Display — ILI9341** (`display.cpp`): the 2.8″ IPS ILI9341 (240×320) **is** the Beta
  panel, Alpha-validated. It is not a stand-in. (A 2.13″ RM69090 AMOLED is a Kickstarter
  stretch-goal board revision; the resolution-independent UI means that swap stays a
  driver-only change if it is ever funded.)
- **Touch — FT6236 @ 0x38** (`touch.cpp`): correct part and address. Register layout at
  0x02 is shared with the CST816 this was originally written against, so the read logic is
  unchanged. **Missing:** the CTP_RST low→high pulse the FT6236 needs before it will
  respond at all.
- **Audio — I2S** (`audio.cpp`): correct interface for the locked ICS-43434 mic +
  MAX98357A amp.

**Does NOT match the locked design — outstanding engineering work:**
- **NFC — PN532 via Adafruit_PN532** (`nfc.cpp`): **wrong chip and wrong bus.** The locked
  front-end is the **ST25R3916 over SPI** (Alpha-validated, IC-ID `0x2A`). Needs a full
  driver rewrite plus the ST RFAL port; the `Adafruit PN532` dependency goes with it.
- **Radio — SX1262 only** (`radio.cpp`): AQROOT is a **dual-radio** device. There is no
  CC1101 driver and no radio manager to enforce one-TX-at-a-time + CS discipline across
  both chips on shared SPI Bus B.
- **IMU** (`sensors.cpp`): the part **is** locked (BMI270 @ 0x68, Alpha-validated), but a
  generic MPU-style register read will not return motion data from a BMI270 — it needs a
  multi-KB config blob uploaded at init. Add the SparkFun BMI270 library and swap the
  register map.
- **Infrared** (`ui/screens/ir_screen.cpp`): UI shell only — there is no `drivers/ir.*`
  yet. IR TX/RX should become an RMT-based driver (native pins 43/44, 38 kHz carrier)
  following the same interface pattern.

- **All pins in `config.h`**: still provisional and currently differ from
  `11 - Beta Pin Map v0.2.md` on every bus (display DC/RST, I2C on 17/18 vs 1/2, radio
  sharing the display bus, I2S on the wrong pins). The Wokwi `diagram.json` mirrors the
  display + button pins, so the sim and firmware stay in sync with each other.

All of the above are tracked in `07 - Build TODO Tracker.md`. They are deliberate,
scheduled work — not oversights.

## Licensing
Firmware is MIT (`../LICENSE-FIRMWARE.md`); hardware design files are CERN-OHL-S v2
(`../LICENSE-HARDWARE.md`).
