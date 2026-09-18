#pragma once
// AQROOT — central hardware configuration.
//
// ===================================================================================
// THIS FILE DOES NOT DESCRIBE THE AQROOT **DEMO** BOARD BEING FABRICATED.
//
// Demo's as-built pin, expander and address map is GENERATED from the board itself and
// lives at `src/hw/aqroot_demo_board.h`.  Build the Demo board's firmware with
//
//     pio run -e aqroot-demo
//
// Every pin below is a Beta-era PLACEHOLDER and several of them collide with real Demo
// functions (this file puts I2C on 17/18 where the Demo board has SPI-A MOSI and NFC
// IRQ; it puts the display on 10/11/12/13 where the Demo board has DISP_CS, SPI-A MOSI,
// SPI-A SCK and SPI-A MISO).  Flashing an image built from this file onto an assembled
// Demo board drives the wrong pins.
//
// The `#error` below is what stops that happening by accident: a real-hardware build
// has to say, in its own environment, that it accepts placeholder pins.
// ===================================================================================
#if !defined(SIMULATION_MODE) && !defined(CONFIG_AQROOT_DM) && \
    !defined(AQROOT_ACK_PLACEHOLDER_PINS)
#error "src/config.h carries Beta-era PLACEHOLDER pins and is NOT the AQROOT Demo map. \
Build the Demo board with `pio run -e aqroot-demo` (src/hw/aqroot_demo_board.h), or \
define AQROOT_ACK_PLACEHOLDER_PINS to build the legacy application anyway."
#endif
//
// ONE source of truth for pin assignments and display geometry. The Wokwi diagram.json
// is wired to match the DISPLAY_* and BTN_* pins below, so the simulation and the driver
// code never drift apart.
//
// PLACEHOLDER WARNING: every pin here is provisional and must be reconciled with the final
// PCB pinout once the board is routed. They are grouped so the swap is mechanical. The
// values were chosen to (a) be valid GPIOs on the ESP32-S3-WROOM-1 N16R8 module and
// (b) avoid the pins the N16R8 reserves for its octal flash/PSRAM (GPIO26–GPIO37).
//
// ============================== PART DECISIONS (LOCKED) ==============================
// This file predates several locked part decisions. The CORRECT parts are:
//
//   Display : ER-TFT035IPS-6, 3.5" IPS, 320x480, ILI9488 COG, 4-wire SPI
//             <- CORRECTED.  This file previously named an ILI9341 2.8" 240x320 as
//                "THE REAL PART"; DEVICE_SPEC.md section 2 locks the 3.5" ILI9488, and
//                the KiCad symbol's ILI9341 text is stale placeholder text.  The
//                DISPLAY_WIDTH/DISPLAY_HEIGHT below are STILL 240x320 because the Wokwi
//                diagram.json is wired to them; the Demo panel geometry belongs to the
//                Demo display driver, not to the simulator.
//   Touch   : FT6236-family @ I2C 0x38               <- NOT CST816 @ 0x15
//   NFC     : ST25R3916 over SPI                     <- NOT PN532 over I2C
//   Radio   : DUAL — CC1101 *and* SX1262 on shared SPI Bus B, one-TX-at-a-time
//   IMU     : BMI270 @ I2C 0x68 (needs a config-blob upload before data works)
//   Audio   : PUI DMM-4026-B-I2S-R mic + MAX98357A amp over I2S
//             <- CORRECTED.  The ICS-43434 is RETIRED; DEVICE_SPEC.md section 8 fits
//                the DMM-4026-B-I2S-R bottom-port MEMS part.
//   Expanders: NXP PCAL9535APW,118 x2 (U2 @ 0x20, U3 @ 0x21)
//             <- CORRECTED.  The TCA9535 block further down this file is the WRONG
//                PART: it has no internal pull-up/pull-down registers, no interrupt
//                mask and no interrupt-status register, and the AQROOT Demo bring-up
//                depends on all three.  The real driver is src/hw/pcal9535a.h.
//
// See "05 - Design Decisions Log.md", "11 - Beta Pin Map v0.2.md", and -- for anything
// that will be flashed onto an assembled AQROOT Demo board --
// docs/full-beta-v2/DEVICE_SPEC.md plus the generated src/hw/aqroot_demo_board.h.
//
// OUTSTANDING FIRMWARE WORK (tracked in "07 - Build TODO Tracker.md" — deliberately NOT
// done as part of a docs cleanup): replace the PN532/I2C NFC driver with an ST25R3916 SPI
// driver, add a CC1101 driver + dual-radio manager, add an RMT IR driver, add the BMI270
// library + config blob, add the FT6236 reset pulse, and reconcile every pin below with
// Beta Pin Map v0.2 (all buses currently differ). Do not change the pins below casually:
// the Wokwi simulation (diagram.json) is wired to match them.

// ---------------------------------------------------------------------------------------
// Display resolution
//
// The real panel is a 2.8" IPS ILI9341 at 240x320 portrait — this IS the Beta part, not a
// stand-in. A 2.13" RM69090 AMOLED (502x410) is a Kickstarter STRETCH-GOAL board revision,
// not the baseline. The UI is laid out relative to DISPLAY_WIDTH/DISPLAY_HEIGHT so it
// re-flows if the AMOLED revision is ever funded.
#define DISPLAY_WIDTH   240
#define DISPLAY_HEIGHT  320

// ---------------------------------------------------------------------------------------
// Display SPI bus (ILI9341 — the real Beta panel). Pin numbers below are still placeholder
// wiring; the panel choice is not. Mirrored in diagram.json for the Wokwi model.
#define DISP_SPI_HOST   1        // SPI2_HOST / HSPI
#define DISP_SCK        12
#define DISP_MOSI       11
#define DISP_MISO       13
#define DISP_CS         10
#define DISP_DC         9
#define DISP_RST        14
#define DISP_BL         21       // backlight / AMOLED enable (PWM brightness)

// ---------------------------------------------------------------------------------------
// Shared I2C bus: FT6236 touch, BMI270 IMU. (NFC is NOT on I2C — see below.)
// Beta uses SDA=1 / SCL=2; the pins below are placeholder wiring matched to the Wokwi sim.
#define I2C_SDA         17
#define I2C_SCL         18
#define I2C_FREQ_HZ     400000

#define TOUCH_I2C_ADDR  0x38     // FT6236-family — Alpha-validated, LOCKED (was 0x15 CST816)
#define IMU_I2C_ADDR    0x68     // BMI270 — Alpha-validated, LOCKED

// ---------------------------------------------------------------------------------------
// I2C GPIO EXPANDERS — *** WRONG PART FOR AQROOT DEMO. ***  The fitted devices are two
// NXP PCAL9535APW,118 (U2 @ 0x20, U3 @ 0x21), not TCA9535PWR, and the Demo bring-up
// uses three registers the TCA9535 does not have: 46h/47h + 48h/49h internal pulls,
// 4Ah/4Bh interrupt mask, 4Ch/4Dh interrupt status.  The Demo driver and the as-built
// bit map are `src/hw/pcal9535a.h` and `src/hw/aqroot_demo_board.h`; nothing below this
// line describes the board being fabricated.
//
// 2x Texas Instruments TCA9535PWR (LOCKED 2026-07-27; replaced the
// MCP23017). U60 = internal (buttons + control), U61 = external (community header).
// 16 genuinely bidirectional I/O each: Port 0 = P00..P07, Port 1 = P10..P17.
//
// NO DRIVER EXISTS YET. See "07 - Build TODO Tracker.md" and "11 - Beta Pin Map v0.2.md"
// §7 for the authoritative pin maps. ONE address-parameterised driver must serve BOTH
// devices — they are the same silicon at two addresses; do not write two drivers.
//
// *** THIS PART IS DATASHEET-TRUSTED, NOT BENCH-VALIDATED. *** The Alpha expander test used
// an MCP23017 (a different part, different register map, different interrupt model). First
// hardware validation of the TCA9535PWR happens on Beta.
//
// DO NOT PORT MCP23017 ASSUMPTIONS. There is no IODIR, GPPU, GPINTEN, INTF, INTCAP, IOCON,
// DEFVAL or INTCON on this part, and NO internal pull-ups at all — every pull is external.
// Each device has ONE open-drain active-low /INT (not INTA/INTB); both are wired-OR onto
// the WAKE_INT_N net, which terminates at ESP32 GPIO21 (RTC-capable, deep-sleep wake).
//
// Interrupt handling contract:
//   * /INT asserts while an input differs from the value last read out of its Input Port
//     register, and clears when that register is read. Nothing latches a transient.
//   * There is NO interrupt-source register. On every WAKE_INT_N assertion, read BOTH input
//     port registers from BOTH devices and diff against the driver's own previous snapshot.
//   * Treat WAKE_INT_N as LEVEL-sensitive and re-check that it released — two devices share
//     the net, so an edge-only handler will miss a second, overlapping assertion.
//   * ROOTPROBE_IRQ_READY_N (U60 P17) is level-held until acknowledged, never pulsed.
//
// Bring the bus up at 100 kHz, then verify 400 kHz.
#define EXP_U60_I2C_ADDR  0x20   // internal: A2=GND, A1=GND, A0=GND
#define EXP_U61_I2C_ADDR  0x21   // external: A2=GND, A1=GND, A0=+3V3

// TCA9535 register set — this is the COMPLETE set. There are eight registers and no others.
#define TCA9535_REG_INPUT_0    0x00   // read-only; reading deasserts /INT for Port 0
#define TCA9535_REG_INPUT_1    0x01   // read-only; reading deasserts /INT for Port 1
// D-753: these two comments said "resets to 0x00" and that is wrong for this
// register pair on the TCA9535 AND on the PCAL9535A this board actually fits
// (NXP Rev.2 tables 7/8: Output port 0/1 power up at 1111 1111).  RETIRED
// PROSE -- the Demo expander layer is Firmware/src/hw/pcal9535a.h, not this.
#define TCA9535_REG_OUTPUT_0   0x02   // output latch, resets to 0xFF
#define TCA9535_REG_OUTPUT_1   0x03   // output latch, resets to 0xFF
#define TCA9535_REG_POLARITY_0 0x04   // keep at 0x00 — invert in firmware, not in hardware
#define TCA9535_REG_POLARITY_1 0x05   // keep at 0x00 — invert in firmware, not in hardware
#define TCA9535_REG_CONFIG_0   0x06   // direction: 1 = input, 0 = output; resets to 0xFF
#define TCA9535_REG_CONFIG_1   0x07   // direction: 1 = input, 0 = output; resets to 0xFF

// SAFE-STATE ORDERING (hard requirement): write the safe value into the OUTPUT register
// (0x02/0x03) BEFORE clearing the matching CONFIG bit (0x06/0x07) from input to output.
// Config resets to all-inputs and the output latches reset to 0x00, which is NOT the safe
// state for every net — setting direction first can glitch NFC_5V_EN, AMP_SD_MODE or
// ACC_PWR_EN at boot. Set the latch, then the direction.

// WRONG PART / WRONG BUS — pending rewrite. The locked NFC front-end is the ST25R3916 over
// SPI, not a PN532 over I2C. These IRQ/RESET defines belong to the PN532 driver that still
// needs replacing (see "07 - Build TODO Tracker.md"). Kept only so the current build links.
#define NFC_IRQ         15
#define NFC_RESET       16

// ---------------------------------------------------------------------------------------
// Radio SPI (SX1262 certified module, e.g. Ebyte E22). PLACEHOLDER pins — must match the
// final PCB. Shares the display SPI clock/data lines with a separate chip-select.
//
// INCOMPLETE: AQROOT is a DUAL-radio device — a CC1101 sits alongside the SX1262 on shared
// SPI Bus B (Beta: SCK=4/MOSI=5/MISO=6, CC1101 CS=7/GDO0=15, SX1262 CS=17/DIO1=18/BUSY=8/
// RST=3). There are no CC1101 defines here and no CC1101 driver yet. A radio manager must
// enforce one-TX-at-a-time and drive the idle radio's CS HIGH — a floating CS on the idle
// radio corrupts shared MISO (validated the hard way in Alpha).
#define RADIO_SCK       12
#define RADIO_MOSI      11
#define RADIO_MISO      13
#define RADIO_NSS       8
#define RADIO_DIO1      38
#define RADIO_BUSY      39
#define RADIO_RST       40

// ---------------------------------------------------------------------------------------
// Audio I2S — ICS-43434 MEMS mic in + MAX98357A Class-D amp out (both LOCKED parts; the
// ICS-43434 replaced the popular INMP441, which is discontinued). The MAX98357A shutdown
// pin lives on the internal GPIO expander as a slow enable (net AMP_SD_MODE = U60 P03, a
// TI TCA9535PWR at I2C 0x20), so audio can be power-gated when idle. An external pull holds
// it in SHUTDOWN until firmware drives it.
// Beta pins are BCLK=39/LRCLK=40/DOUT=41/DIN=42. PLACEHOLDER pins below.
#define I2S_BCLK        41
#define I2S_LRCLK       42
#define I2S_DOUT        45       // to speaker amp
#define I2S_DIN         2        // from digital mic
#define AUDIO_SAMPLE_RATE 16000

// ---------------------------------------------------------------------------------------
// GPIO tool header test pins used by gpio_screen (real digital out/in). PLACEHOLDER.
#define GPIO_TEST_OUT   47
#define GPIO_TEST_IN    48

// ---------------------------------------------------------------------------------------
// SIMULATION-ONLY navigation buttons.
//
// Wokwi has no capacitive-touch model, so the sim build maps four pushbuttons (wired in
// diagram.json, active-low with internal pull-ups) to an LVGL keypad for tile navigation.
// On real hardware these are ignored — the FT6236 touchscreen drives the UI.
#define BTN_PREV        4        // move focus up/left  (LV_KEY_PREV)
#define BTN_NEXT        5        // move focus down/right (LV_KEY_NEXT)
#define BTN_ENTER       6        // activate focused tile (LV_KEY_ENTER)
#define BTN_BACK        7        // return to the launcher home screen

// =======================================================================================
// BETA DM (DEMO MODEL) FEATURE GATES  --  CONFIG_AQROOT_DM
//
// Beta DM is a hardware DERIVATIVE of the full Beta (hardware/beta-dm/), not a firmware
// fork. ONE source tree, one extra build configuration: PlatformIO env
// `esp32-s3-aqroot-dm` defines CONFIG_AQROOT_DM. Nothing else changes.
//
// The gates below say what the DM BOARD does not populate, so driver code can compile the
// corresponding hardware access out and the UI can present the feature as unavailable
// (or simulated) instead of talking to a part that is not there. Restoring a feature for
// the Final product is deleting a gate, never re-merging a fork.
//
// Authoritative scope: hardware/beta-dm/BETA-DM-SCOPE-LEDGER.md
//                      hardware/beta-dm/BETA-DM-DNP-LIST.md
// =======================================================================================
#ifdef CONFIG_AQROOT_DM

// Speaker output: U5 MAX98357A and J6 are DNP; I2S_SPK_DOUT and AMP_SD_MODE are not
// routed on the DM board. The ICS-43434 microphone is UNAFFECTED and must still work.
#define AQROOT_HAS_SPEAKER        0
#define AQROOT_HAS_MIC            1

// NFC: U9 ST25R3916 is DNP for SPI-B bus safety (its chip select has no copper, so a
// populated part could contend on the bus the LoRa demo depends on). No NFC antenna or
// matching network exists either. Firmware must NEVER assert an NFC transaction on DM.
#define AQROOT_HAS_NFC            0

// Infrared: receiver deferred; transmitter deferred pending a routing ruling.
#define AQROOT_HAS_IR_RX          0
#define AQROOT_HAS_IR_TX          0

// Everything the DM demo depends on stays on.
#define AQROOT_HAS_LORA           1   // SX1262 / 915 MHz  -- flagship two-unit demo
#define AQROOT_HAS_SUBGHZ         1   // CC1101 / 433 MHz
#define AQROOT_HAS_DISPLAY        1
#define AQROOT_HAS_TOUCH          1
#define AQROOT_HAS_SDCARD         1
#define AQROOT_HAS_IMU            1
#define AQROOT_HAS_BUTTONS        1
#define AQROOT_HAS_HEADER_J5      1

#else   // full Beta / Final

#define AQROOT_HAS_SPEAKER        1
#define AQROOT_HAS_MIC            1
#define AQROOT_HAS_NFC            1
#define AQROOT_HAS_IR_RX          1
#define AQROOT_HAS_IR_TX          1
#define AQROOT_HAS_LORA           1
#define AQROOT_HAS_SUBGHZ         1
#define AQROOT_HAS_DISPLAY        1
#define AQROOT_HAS_TOUCH          1
#define AQROOT_HAS_SDCARD         1
#define AQROOT_HAS_IMU            1
#define AQROOT_HAS_BUTTONS        1
#define AQROOT_HAS_HEADER_J5      1

#endif  // CONFIG_AQROOT_DM
