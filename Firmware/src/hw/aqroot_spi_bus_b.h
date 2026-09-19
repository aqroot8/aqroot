#pragma once
// AQROOT Demo -- the SPI bus B arbiter.
//
// U7 (CC1101, 433 MHz), U8 (SX1262, 915 MHz LoRa) and U9 (ST25R3916, 13.56 MHz
// NFC) share /SPI_B_SCK, /SPI_B_MOSI and /SPI_B_MISO.  Two rules govern that
// bus, and until now both were comments:
//
//   BUS RULE   exactly ONE chip select may be asserted at a time.  Two
//              deselected devices tri-state MISO; two SELECTED devices drive it
//              against each other, and the symptom is intermittent corruption
//              that looks like a marginal trace.
//   RF RULE    exactly ONE transceiver may be KEYED at a time -- the
//              "one-TX-at-a-time" discipline AQROOT_DEMO_SCOPE requires of the
//              retained dual-radio scope.  The two radios have separate
//              antennas but share a supply and a ground return, and the 915 MHz
//              module is a +22 dBm part.
//
// A comment cannot refuse.  This class can, and `Firmware/test/` proves it does.
//
// It is deliberately Arduino-free: `ChipSelects` is the seam, so the refusals
// can be tested on the host exactly as the expander ordering is.

#include <stdint.h>

#include "aqroot_accessory_power_policy.h"

namespace aqroot {

enum class SpiBDevice : uint8_t { None = 0, Cc1101, Sx1262, St25r3916 };

class ChipSelects {
 public:
  virtual ~ChipSelects() {}
  // `asserted` is logical: all three parts use an ACTIVE-LOW select, and the
  // implementation is what knows that.
  virtual void driveSelect(SpiBDevice device, bool asserted) = 0;
};

class SpiBusB {
 public:
  explicit SpiBusB(ChipSelects &selects)
      : selects_(selects), selected_(SpiBDevice::None),
        transmitting_(SpiBDevice::None) {}

  SpiBDevice selected() const { return selected_; }
  SpiBDevice transmitting() const { return transmitting_; }

  // Assert one select.  REFUSES while ANY device holds the bus -- INCLUDING
  // the same one.  An earlier version treated a repeat select as idempotent and
  // the host test caught what that costs: a nested `Hold` on the same device
  // would succeed and then RELEASE the bus at the inner scope's exit, leaving
  // the outer scope transacting against a deselected part.  One holder, one
  // release, no re-entrancy.
  bool select(SpiBDevice device) {
    if (device == SpiBDevice::None) return false;
    if (selected_ != SpiBDevice::None) return false;
    selects_.driveSelect(device, true);
    selected_ = device;
    return true;
  }

  void release() {
    if (selected_ == SpiBDevice::None) return;
    selects_.driveSelect(selected_, false);
    selected_ = SpiBDevice::None;
  }

  // Key a transmitter.  REFUSES while ANY transmitter is keyed, for the same
  // re-entrancy reason as `select`.  The NFC front end counts: its field is a
  // transmitter too, and it shares the supply and the ground return.
  bool beginTransmit(SpiBDevice device) {
    if (device == SpiBDevice::None) return false;
    if (transmitting_ != SpiBDevice::None) return false;
    transmitting_ = device;
    return true;
  }

  void endTransmit(SpiBDevice device) {
    if (transmitting_ == device) transmitting_ = SpiBDevice::None;
  }

  // RAII for the bus rule: a scope that cannot forget to release.
  class Hold {
   public:
    Hold(SpiBusB &bus, SpiBDevice device) : bus_(bus), ok_(bus.select(device)) {}
    ~Hold() { if (ok_) bus_.release(); }
    bool ok() const { return ok_; }
   private:
    SpiBusB &bus_;
    bool ok_;
  };

 private:
  ChipSelects &selects_;
  SpiBDevice selected_;
  SpiBDevice transmitting_;
};

}  // namespace aqroot

#ifdef ARDUINO
#include <Arduino.h>

#include "aqroot_demo_board.h"

namespace aqroot {

// The only place on this board that knows a SPI-B select is active low.
class BoardChipSelects : public ChipSelects {
 public:
  void begin() {
    pinMode(AQROOT_PIN_CC1101_CS_N, OUTPUT);
    pinMode(AQROOT_PIN_SX1262_CS_N, OUTPUT);
    pinMode(AQROOT_PIN_NFC_CS_N, OUTPUT);
    driveSelect(SpiBDevice::Cc1101, false);
    driveSelect(SpiBDevice::Sx1262, false);
    driveSelect(SpiBDevice::St25r3916, false);
  }

  void driveSelect(SpiBDevice device, bool asserted) override {
    const int level = asserted ? LOW : HIGH;
    switch (device) {
      case SpiBDevice::Cc1101:
        digitalWrite(AQROOT_PIN_CC1101_CS_N, level);
        break;
      case SpiBDevice::Sx1262:
        digitalWrite(AQROOT_PIN_SX1262_CS_N, level);
        break;
      case SpiBDevice::St25r3916:
        digitalWrite(AQROOT_PIN_NFC_CS_N, level);
        break;
      default:
        break;
    }
  }
};

}  // namespace aqroot
#endif  // ARDUINO
