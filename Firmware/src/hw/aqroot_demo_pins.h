#pragma once
// AQROOT Demo -- the MCU pin inventory, and the safe state every pin is parked
// in before any driver claims it.
//
// The point of the table is that it is EXHAUSTIVE.  `firmware_hw_map_contract`
// fails if any role the generator emits is missing from the hardware layer, so
// a board revision that adds a pin cannot reach an assembled unit with nothing
// in firmware deciding what that pin does at boot.
//
// THREE STRAPPING PINS CARRY SIGNALS AND ONE MORE IS NOT OURS AT ALL:
//   GPIO0  BOOT_N          R2 10k pull-up + SW1.  Input, and readable as a
//                          recovery button after boot.
//   GPIO3  BMI270_INT1     R110 10k pull-down holds the JTAG-source strap low
//                          through reset; R18 220R isolates the IMU driver.
//                          Input, never an output.
//   GPIO46 DISP_BL_PWM     must be LOW at reset (R108 10k to GND), which also
//                          leaves the backlight boost disabled.  Park it LOW
//                          and only then attach PWM.
//                          D-750 MADE LOW MEAN DARK.  The TPS61169 retains a
//                          DC path from +3V3 through L3/D8 to the panel LEDs
//                          in shutdown, and TI guarantees OFF only when the
//                          array's minimum Vf exceeds the maximum VIN -- this
//                          panel is 2.9-3.2 V on a 3.3 V rail, so it did not.
//                          Q11 (Vishay SQ2364EES) now sits in the panel
//                          cathode return, its gate driven from this line
//                          through D14 / C85 / R132, and R108 holds the line
//                          low, so a firmware crash, a GPIO left in
//                          high-impedance and a reset all leave the screen
//                          dark.  PWM on this pin gates the LED current
//                          directly instead of restarting the converter.
//   GPIO45 VDD_SPI strap   has NO firmware role and is deliberately absent
//                          from this table.  R111 and TP1 are its only load.

#include <stdint.h>

#include "aqroot_demo_board.h"

namespace aqroot {

enum class PinMode : uint8_t {
  InputFloating,     // driven by an external device, no MCU pull
  InputPullUp,       // MCU pull-up needed; nothing external defines the level
  OutputLow,         // park low
  OutputHigh,        // park high
  Peripheral,        // owned by SPI/I2C/I2S/USB/UART -- do not touch as a GPIO
};

struct PinEntry {
  const char *name;
  uint8_t gpio;
  PinMode mode;
};

// The whole of U1's firmware-visible surface, in board-pad order.
static const PinEntry kPins[] = {
    // ---- SPI-B: CC1101 (U7) + SX1262 (U8) + ST25R3916 (U9), one TX at a time
    {"SPI_B_SCK", AQROOT_PIN_SPI_B_SCK, PinMode::Peripheral},
    {"SPI_B_MOSI", AQROOT_PIN_SPI_B_MOSI, PinMode::Peripheral},
    {"SPI_B_MISO", AQROOT_PIN_SPI_B_MISO, PinMode::Peripheral},
    {"CC1101_CS_N", AQROOT_PIN_CC1101_CS_N, PinMode::OutputHigh},
    {"CC1101_GDO0", AQROOT_PIN_CC1101_GDO0, PinMode::InputFloating},
    {"SX1262_CS_N", AQROOT_PIN_SX1262_CS_N, PinMode::OutputHigh},
    {"SX1262_BUSY", AQROOT_PIN_SX1262_BUSY, PinMode::InputFloating},
    {"NFC_CS_N", AQROOT_PIN_NFC_CS_N, PinMode::OutputHigh},
    {"NFC_IRQ", AQROOT_PIN_NFC_IRQ, PinMode::InputFloating},
    // ---- SPI-A: display (J1) + microSD (J2).  MISO reaches the CARD ONLY.
    {"SPI_A_SCK", AQROOT_PIN_SPI_A_SCK, PinMode::Peripheral},
    {"SPI_A_MOSI", AQROOT_PIN_SPI_A_MOSI, PinMode::Peripheral},
    {"SPI_A_MISO", AQROOT_PIN_SPI_A_MISO, PinMode::Peripheral},
    {"DISP_CS_N", AQROOT_PIN_DISP_CS_N, PinMode::OutputHigh},
    {"DISP_DC", AQROOT_PIN_DISP_DC, PinMode::OutputLow},
    {"DISP_BL_PWM", AQROOT_PIN_DISP_BL_PWM, PinMode::OutputLow},
    {"SD_CS_N", AQROOT_PIN_SD_CS_N, PinMode::OutputHigh},
    // ---- I2C, I2S, IR
    {"I2C_SDA", AQROOT_PIN_I2C_SDA, PinMode::Peripheral},
    {"I2C_SCL", AQROOT_PIN_I2C_SCL, PinMode::Peripheral},
    {"I2S_BCLK", AQROOT_PIN_I2S_BCLK, PinMode::Peripheral},
    {"I2S_LRCLK", AQROOT_PIN_I2S_LRCLK, PinMode::Peripheral},
    {"I2S_SPK_DOUT", AQROOT_PIN_I2S_SPK_DOUT, PinMode::Peripheral},
    {"I2S_MIC_DIN", AQROOT_PIN_I2S_MIC_DIN, PinMode::Peripheral},
    {"IR_TX", AQROOT_PIN_IR_TX, PinMode::OutputLow},
    {"IR_RX", AQROOT_PIN_IR_RX, PinMode::InputFloating},
    // ---- straps, wake, expansion, console
    {"BOOT_N", AQROOT_PIN_BOOT_N, PinMode::InputFloating},
    {"BMI270_INT1", AQROOT_PIN_BMI270_INT1, PinMode::InputFloating},
    {"WAKE_INT_N", AQROOT_PIN_WAKE_INT_N, PinMode::InputFloating},
    {"NATIVE_A", AQROOT_PIN_NATIVE_A, PinMode::InputPullUp},
    {"NATIVE_B", AQROOT_PIN_NATIVE_B, PinMode::InputPullUp},
    {"UART0_TXD", AQROOT_PIN_UART0_TXD, PinMode::Peripheral},
};

static const size_t kPinCount = sizeof(kPins) / sizeof(kPins[0]);

#ifdef ARDUINO
#include <Arduino.h>

// Park every firmware-visible pin.  Call FIRST, before any driver.  Peripheral
// pins are left alone -- claiming them as GPIO here would fight the SPI/I2S/USB
// controllers that take them moments later.
inline void parkAllPins() {
  for (size_t i = 0; i < kPinCount; ++i) {
    switch (kPins[i].mode) {
      case PinMode::Peripheral:
        break;
      case PinMode::InputFloating:
        pinMode(kPins[i].gpio, INPUT);
        break;
      case PinMode::InputPullUp:
        pinMode(kPins[i].gpio, INPUT_PULLUP);
        break;
      case PinMode::OutputLow:
        pinMode(kPins[i].gpio, OUTPUT);
        digitalWrite(kPins[i].gpio, LOW);
        break;
      case PinMode::OutputHigh:
        pinMode(kPins[i].gpio, OUTPUT);
        digitalWrite(kPins[i].gpio, HIGH);
        break;
    }
  }
}
#endif  // ARDUINO

}  // namespace aqroot
