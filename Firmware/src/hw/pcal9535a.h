#pragma once
// AQROOT Demo -- NXP PCAL9535A, one address-parameterised driver for BOTH
// devices.  They are the same silicon at two addresses (U2 = 0x20, U3 = 0x21);
// do not write two drivers.
//
// THIS IS NOT A TCA9535 AND IT IS NOT AN MCP23017.  The PCAL9535A adds the
// 40h..4Fh "Agile I/O" block on top of the eight PCA9535-compatible registers,
// and this board's bring-up depends on three of those extensions:
//
//   46h/47h + 48h/49h  internal 100k pull-up/pull-down.  U3's four NC-DEMO
//                      spares and U2's TOUCH_INT_N have NO external part at
//                      all, and a floating CMOS input on an interrupt-enabled
//                      pin holds the shared wake line forever.
//   4Ah/4Bh            per-bit interrupt mask.  Reset value is FFh -- every
//                      interrupt masked -- so a bit only wakes the MCU if
//                      firmware unmasks it.
//   4Ch/4Dh            interrupt STATUS.  The PCA9535/TCA9535 have no such
//                      register and force a snapshot diff; here the part names
//                      the bit that changed.  Reading the INPUT port is still
//                      what CLEARS the condition.
//
// INTERRUPT CONTRACT (both devices wire-OR their open-drain /INT onto
// WAKE_INT_N through R3 10k):
//   * /INT asserts while an input differs from the value last READ OUT of the
//     input port register, and clears when that register is read.  Nothing
//     latches a transient unless the input-latch registers (44h/45h) are used.
//   * WAKE_INT_N is LEVEL sensitive.  Two devices share it, so an edge-only
//     handler misses a second overlapping assertion -- service BOTH devices
//     and re-check that the line released.

#include <stddef.h>
#include <stdint.h>

#include "aqroot_i2c.h"

namespace aqroot {

class Pcal9535a {
 public:
  // ---- PCA9535-compatible core ----
  static const uint8_t kRegInput0 = 0x00;
  static const uint8_t kRegInput1 = 0x01;
  static const uint8_t kRegOutput0 = 0x02;
  static const uint8_t kRegOutput1 = 0x03;
  static const uint8_t kRegPolarity0 = 0x04;
  static const uint8_t kRegPolarity1 = 0x05;
  static const uint8_t kRegConfig0 = 0x06;   // 1 = input, 0 = output
  static const uint8_t kRegConfig1 = 0x07;
  // ---- PCAL9535A extensions ----
  static const uint8_t kRegDriveStrength00 = 0x40;
  static const uint8_t kRegInputLatch0 = 0x44;
  static const uint8_t kRegInputLatch1 = 0x45;
  static const uint8_t kRegPullEnable0 = 0x46;
  static const uint8_t kRegPullEnable1 = 0x47;
  static const uint8_t kRegPullSelect0 = 0x48;  // 1 = pull-up, 0 = pull-down
  static const uint8_t kRegPullSelect1 = 0x49;
  static const uint8_t kRegIrqMask0 = 0x4A;     // 1 = masked
  static const uint8_t kRegIrqMask1 = 0x4B;
  static const uint8_t kRegIrqStatus0 = 0x4C;
  static const uint8_t kRegIrqStatus1 = 0x4D;
  static const uint8_t kRegOutputConfig = 0x4F;

  // A 16-bit word in this driver is PORT0 in the low byte and PORT1 in the
  // high byte, so bit index n is P0n for n < 8 and P1(n-8) above -- exactly
  // the numbering `aqroot_demo_board.h` emits.
  struct Config {
    uint16_t output_latch;   // safe levels, written FIRST
    uint16_t direction;      // 1 = input, 0 = output
    uint16_t pull_enable;    // 1 = internal 100k engaged
    uint16_t pull_up;        // 1 = pull-up, 0 = pull-down (where enabled)
    uint16_t irq_mask;       // 1 = masked
  };

  explicit Pcal9535a(uint8_t address)
      : address_(address), shadow_(0xFFFF), shadow_valid_(false) {}

  uint8_t address() const { return address_; }
  uint16_t outputShadow() const { return shadow_; }
  bool outputShadowValid() const { return shadow_valid_; }

  bool probe(I2cBus &bus) { return bus.probe(address_); }

  // SAFE BRING-UP ORDER -- this is the whole reason the class exists.
  //
  // The part resets with CONFIG = FFh (all inputs) and THE OUTPUT LATCHES AT
  // FFh TOO.  NXP PCAL9535A Rev. 2 tables 7 and 8 give Output port 0 (02h) and
  // Output port 1 (03h) a power-on default of 1111 1111.
  //
  // D-753 CORRECTED THIS COMMENT, WHICH SAID 00h, AND THE CORRECTION MAKES THE
  // ORDERING MATTER MORE, NOT LESS.  Under the false 00h model an active-HIGH
  // enable was safe by accident if the direction bit went first; under the real
  // FFh it is DRIVEN HIGH.  Six of this board's expander outputs have a safe
  // level of 0 -- ACC_5V_SW_EN, ACC_5V_BOOST_EN, ACC_3V3_EN, AMP_SD_MODE,
  // NFC_5V_EN, ACC_PWR_EN -- and every one of them is an enable whose POR latch
  // value is the UNSAFE one.  Clearing a direction bit before the latch holds
  // the right value therefore drives the wrong level for as long as it takes to
  // issue the next transaction: on ACC_5V_SW_EN or ACC_5V_BOOST_EN that is a
  // live accessory rail; on AMP_SD_MODE it is a pop into the speaker; on
  // NFC_5V_EN it is an enable into a DNP boost.  The three RGB cathodes are
  // safe at 1 and happen to agree with the POR value; they are not what this
  // order exists for.
  //
  // Cold POR and MCU-only warm reset need the SAME first action.  On cold POR
  // CONFIG is FFh so changing OUTPUT is electrically inert; on a warm MCU reset
  // the expander can still be driving the PREVIOUS application's outputs, so the
  // first transaction must overwrite the complete output latch with the board's
  // safe word.  Only then is it safe to spend bus transactions on pulls/masks.
  // NXP also recommends programming Output Port Configuration (4Fh) before
  // making pins outputs; AQROOT uses push-pull, therefore 4Fh = 00h explicitly.
  // Direction remains LAST so a cold-POR input can never expose the reset FFh
  // latch as an active-high enable.
  bool apply(I2cBus &bus, const Config &config) {
    shadow_valid_ = false;
    if (!writeOutputs(bus, config.output_latch)) return false;
    if (!writePortPair(bus, address_, kRegPullSelect0, config.pull_up)) return false;
    if (!writePortPair(bus, address_, kRegPullEnable0, config.pull_enable)) return false;
    if (!writePortPair(bus, address_, kRegIrqMask0, config.irq_mask)) return false;
    if (!writePortPair(bus, address_, kRegPolarity0, 0x0000)) return false;
    if (!writeRegister(bus, address_, kRegOutputConfig, 0x00)) return false;
    if (!writePortPair(bus, address_, kRegConfig0, config.direction)) return false;
    return true;
  }

  // Reading the input port is what DEASSERTS /INT for this device.
  bool readInputs(I2cBus &bus, uint16_t *value) {
    uint8_t raw[2] = {0, 0};
    if (!bus.readRegister(address_, kRegInput0, raw, sizeof(raw))) return false;
    *value = uint16_t(raw[0]) | uint16_t(uint16_t(raw[1]) << 8);
    return true;
  }

  // Which bits caused the current assertion.  Read this BEFORE `readInputs`:
  // the input read is what clears the condition.
  bool readInterruptStatus(I2cBus &bus, uint16_t *value) {
    uint8_t raw[2] = {0, 0};
    if (!bus.readRegister(address_, kRegIrqStatus0, raw, sizeof(raw))) return false;
    *value = uint16_t(raw[0]) | uint16_t(uint16_t(raw[1]) << 8);
    return true;
  }

  bool readConfig(I2cBus &bus, uint16_t *value) {
    uint8_t raw[2] = {0, 0};
    if (!bus.readRegister(address_, kRegConfig0, raw, sizeof(raw))) return false;
    *value = uint16_t(raw[0]) | uint16_t(uint16_t(raw[1]) << 8);
    return true;
  }

  bool writeOutputs(I2cBus &bus, uint16_t value) {
    if (!writePortPair(bus, address_, kRegOutput0, value)) {
      // A failed two-byte output write leaves the physical latch state UNKNOWN:
      // some I2C controllers/slaves can accept the first data byte before the
      // transaction fails on the second.  Never keep using the pre-write shadow
      // for read-modify-write after that ambiguity.
      shadow_valid_ = false;
      return false;
    }
    shadow_ = value;
    shadow_valid_ = true;
    return true;
  }

  bool writeBit(I2cBus &bus, uint8_t index, bool level) {
    if (!shadow_valid_) return false;  // refuse a blind read-modify-write
    const uint16_t mask = uint16_t(1u << index);
    const uint16_t next = level ? uint16_t(shadow_ | mask)
                                : uint16_t(shadow_ & uint16_t(~mask));
    return writeOutputs(bus, next);
  }

  // D-751/D-766.  A FAILED WRITE MAKES THE SHADOW UNKNOWN.  D-751 first
  // prevented a refused load-switch clear from being reasserted by a later
  // single-bit write.  Round-2 review adds the byte-boundary case: a failed
  // two-byte transaction can have changed only one output-port byte.  In that
  // case no software shadow is trustworthy, so writeOutputs() invalidates it.
  // `clearBits` is therefore only usable while the shadow is valid; safety
  // callers must fall back to an ABSOLUTE full safe-latch write after failure.
  bool clearBits(I2cBus &bus, uint16_t mask) {
    if (!shadow_valid_) return false;  // warm reset: full safe latch first
    return writeOutputs(bus, uint16_t(shadow_ & uint16_t(~mask)));
  }

  static bool bitOf(uint16_t word, uint8_t index) {
    return (word & uint16_t(1u << index)) != 0;
  }

 private:
  uint8_t address_;
  uint16_t shadow_;
  bool shadow_valid_;
};

}  // namespace aqroot
