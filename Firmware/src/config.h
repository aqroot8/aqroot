#pragma once
// AQROOT — central hardware configuration.
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
// ALPHA WIRING: the Alpha bench prototype wiring is documented in "09 - Alpha Pin Bus
// Map.md" at the repo root and does NOT match these placeholders yet — pins differ
// throughout, NFC there is an ST25R3916 on SPI (here: PN532 on I2C), and a CC1101 sits
// alongside the SX1262. Do not change the pins below casually: the Wokwi simulation
// (diagram.json) is wired to match them. Reconcile at real-hardware bring-up.

// ---------------------------------------------------------------------------------------
// Display resolution
//
// The real panel is a 2.13" RM69090 AMOLED at 502x410 (see "01 - Hardware Core.md").
// The placeholder/simulation panel (generic ILI9341) is 240x320 portrait. The UI is
// laid out relative to DISPLAY_WIDTH/DISPLAY_HEIGHT so it re-flows when the real panel
// (and its larger resolution) is dropped in.
#define DISPLAY_WIDTH   240
#define DISPLAY_HEIGHT  320

// ---------------------------------------------------------------------------------------
// Display SPI bus (PLACEHOLDER panel — ILI9341 generic driver, to be swapped for RM69090)
// These same pins are mirrored in diagram.json for the Wokwi ILI9341 stand-in.
#define DISP_SPI_HOST   1        // SPI2_HOST / HSPI
#define DISP_SCK        12
#define DISP_MOSI       11
#define DISP_MISO       13
#define DISP_CS         10
#define DISP_DC         9
#define DISP_RST        14
#define DISP_BL         21       // backlight / AMOLED enable (PWM brightness)

// ---------------------------------------------------------------------------------------
// Shared I2C bus: CST816 touch (final), PN532 NFC (I2C mode), IMU.
#define I2C_SDA         17
#define I2C_SCL         18
#define I2C_FREQ_HZ     400000

#define TOUCH_I2C_ADDR  0x15     // CST816-series (confirmed final part)
#define IMU_I2C_ADDR    0x68     // generic 6-axis IMU (placeholder part)

// PN532 is driven through the Adafruit_PN532 library in I2C mode; it needs IRQ + RESET.
#define NFC_IRQ         15
#define NFC_RESET       16

// ---------------------------------------------------------------------------------------
// Radio SPI (SX1262 certified module, e.g. Ebyte E22). PLACEHOLDER pins — must match the
// final PCB. Shares the display SPI clock/data lines with a separate chip-select.
#define RADIO_SCK       12
#define RADIO_MOSI      11
#define RADIO_MISO      13
#define RADIO_NSS       8
#define RADIO_DIO1      38
#define RADIO_BUSY      39
#define RADIO_RST       40

// ---------------------------------------------------------------------------------------
// Audio I2S (digital mic in + speaker/amp out). PLACEHOLDER pins.
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
// Wokwi has no CST816 touch model, so the sim build maps four pushbuttons (wired in
// diagram.json, active-low with internal pull-ups) to an LVGL keypad for tile navigation.
// On real hardware these are ignored — the CST816 touchscreen drives the UI.
#define BTN_PREV        4        // move focus up/left  (LV_KEY_PREV)
#define BTN_NEXT        5        // move focus down/right (LV_KEY_NEXT)
#define BTN_ENTER       6        // activate focused tile (LV_KEY_ENTER)
#define BTN_BACK        7        // return to the launcher home screen
