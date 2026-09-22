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

// D-792 / R11-04.  THE MODE EDGE OF THE ACCESSORY PERMISSION, PUT WHERE THE
// MODE IS ACTUALLY KEYED.
//
// The canonical power ledger carries a sub-GHz transmission as an INCREMENTAL
// mode of the same order as an accessory rail -- 140 mA for the fitted
// E22-900M22S at +22 dBm -- and the D-792 permission table refuses six of its
// sixteen mode/rail combinations outright.  A rule that lived only in the
// accessory-enable path would be half a rule: the user can reach the same
// forbidden state by keying a transmitter while a rail is already live.
//
// So the authority is asked HERE, in `beginTransmit`, which is the one place a
// sub-GHz transmitter can be keyed.  A future TX path cannot bypass it without
// deleting this call, and `Firmware/test/test_spi_bus_b.cpp` proves the refusal
// exists rather than trusting that it does.
//
// THE NFC FRONT END IS DELIBERATELY EXEMPT.  Its field is carried as a
// bounded-duty allowance (25 % of any minute) inside the ALWAYS-ON set of the
// canonical ledger, so it is already inside every floor in the table; gating it
// here would charge it twice and would make a hand-held tap shed an accessory
// rail for no physical reason.
class AccessoryLoadAuthority {
 public:
  virtual ~AccessoryLoadAuthority() {}
  // May a sub-GHz transmitter be keyed right now?  The implementation is the
  // one thing that knows the accessory rail state and the pack voltage.
  virtual bool subGhzTransmitPermitted() = 0;
  // Told on both edges so the authority's own mode state follows the hardware.
  virtual void noteSubGhzTransmitting(bool on) = 0;
};

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
        transmitting_(SpiBDevice::None), authority_(nullptr) {}

  // Set once at bring-up.  Until it is set the bus refuses NOTHING extra, which
  // is why `test_production_callers.cpp` proves `main()` sets it.
  void setAccessoryLoadAuthority(AccessoryLoadAuthority *authority) {
    authority_ = authority;
  }
  AccessoryLoadAuthority *accessoryLoadAuthority() const { return authority_; }

  SpiBDevice selected() const { return selected_; }
  SpiBDevice transmitting() const { return transmitting_; }

  static bool isSubGhz(SpiBDevice device) {
    return device == SpiBDevice::Cc1101 || device == SpiBDevice::Sx1262;
  }

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
    // D-792 / R11-04: the accessory permission's mode edge.  Asked BEFORE the
    // keyed state is recorded, so a refusal leaves the bus exactly as it was.
    if (isSubGhz(device) && authority_ != nullptr &&
        !authority_->subGhzTransmitPermitted()) {
      return false;
    }
    transmitting_ = device;
    if (isSubGhz(device) && authority_ != nullptr) {
      authority_->noteSubGhzTransmitting(true);
    }
    return true;
  }

  void endTransmit(SpiBDevice device) {
    if (transmitting_ != device) return;
    transmitting_ = SpiBDevice::None;
    if (isSubGhz(device) && authority_ != nullptr) {
      authority_->noteSubGhzTransmitting(false);
    }
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
  AccessoryLoadAuthority *authority_;
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
