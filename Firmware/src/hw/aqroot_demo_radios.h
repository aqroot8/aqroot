#pragma once
// AQROOT Demo -- identity probes for the three devices on SPI bus B.
//
// These exist for ONE purpose: to prove, on the first assembled board, that the
// as-built pin map in `aqroot_demo_board.h` is right.  A wrong CS, a swapped
// MOSI/MISO or a reset line left asserted all present identically at the
// application layer -- as a peripheral that "doesn't work" -- and all three are
// distinguishable here in a few microseconds.
//
// SHARED BUS, ONE TRANSACTION AT A TIME.  U7 (CC1101), U8 (SX1262) and U9
// (ST25R3916) share SCK/MOSI/MISO.  Every probe below goes through
// `SpiBusB::Hold`, which REFUSES a second concurrent select rather than
// trusting each caller to release -- see `aqroot_spi_bus_b.h`.  They also use
// three DIFFERENT SPI modes and clock rates, so each probe re-states the
// settings it needs rather than inheriting whatever the last caller left
// behind.

#include <stdint.h>

#ifdef ARDUINO
#include <Arduino.h>
#include <SPI.h>

#include "aqroot_demo_board.h"
#include "aqroot_spi_bus_b.h"

namespace aqroot {

struct DeviceIdentity {
  const char *device;
  uint32_t raw;        // what came back
  uint32_t expected;   // 0xFFFFFFFF when the value is report-only
  bool alive;          // the bus answered with something that is not a stuck rail
  bool matches;        // raw == expected, when there is an expected value
};

static const uint32_t kIdentityReportOnly = 0xFFFFFFFFu;

// ---------------------------------------------------------------------------
// CC1101 (U7, Ebyte E07-400M10S) -- 433 MHz
//
// THE CLASSIC TRAP IS IN THIS PROBE.  Header byte is {R/W, BURST, addr[5:0]}.
// Address 0x30 with BURST CLEAR is the SRES command strobe; address 0x30 with
// BURST SET is the PARTNUM status register.  Reading PARTNUM without the burst
// bit RESETS the radio instead of identifying it.
inline DeviceIdentity probeCc1101(SpiBusB &bus) {
  const uint8_t kReadBurst = 0xC0;
  const uint8_t kPartnum = 0x30;
  const uint8_t kVersion = 0x31;

  DeviceIdentity refused;
  refused.device = "CC1101 U7";
  refused.raw = 0;
  refused.expected = kIdentityReportOnly;
  refused.alive = false;
  refused.matches = false;

  SPI.beginTransaction(SPISettings(4000000, MSBFIRST, SPI_MODE0));
  SpiBusB::Hold hold(bus, SpiBDevice::Cc1101);
  if (!hold.ok()) {
    SPI.endTransaction();
    return refused;
  }
  // The CC1101 holds SO high until its crystal is stable; the datasheet's own
  // access sequence is to wait for it to fall before the first header byte.
  const uint32_t deadline = millis() + 10;
  while (digitalRead(AQROOT_PIN_SPI_B_MISO) == HIGH && millis() < deadline) {
  }
  SPI.transfer(uint8_t(kReadBurst | kPartnum));
  const uint8_t partnum = SPI.transfer(0x00);
  SPI.transfer(uint8_t(kReadBurst | kVersion));
  const uint8_t version = SPI.transfer(0x00);
  SPI.endTransaction();

  DeviceIdentity id;
  id.device = "CC1101 U7";
  id.raw = uint32_t(partnum) << 8 | version;
  id.expected = kIdentityReportOnly;   // VERSION varies by die revision
  id.alive = (partnum != 0xFF) && (version != 0x00) && (version != 0xFF);
  // PARTNUM is 0x00 on every CC1101 -- the discriminating half is that VERSION
  // is neither of the two values a dead bus returns.
  id.matches = (partnum == 0x00) && id.alive;
  return id;
}

// ---------------------------------------------------------------------------
// SX1262 (U8, Ebyte E22-900M22S) -- 915 MHz LoRa
//
// Reset is NOT an MCU pin: it is U2.P01 through the expander, so the caller
// must have released it already.  BUSY (GPIO8) must be low before any command.
// The identity used here is the LoRa sync word at 0x0740/0x0741, which resets
// to 0x1424 -- a two-byte constant is a far stronger pin-map proof than a
// status byte whose every bit pattern looks plausible.
inline bool sx1262WaitBusy(uint32_t timeout_ms = 20) {
  const uint32_t deadline = millis() + timeout_ms;
  while (digitalRead(AQROOT_PIN_SX1262_BUSY) == HIGH) {
    if (millis() > deadline) return false;
  }
  return true;
}

inline DeviceIdentity probeSx1262(SpiBusB &bus) {
  DeviceIdentity id;
  id.device = "SX1262 U8";
  id.expected = 0x1424;
  id.raw = 0;
  id.alive = false;
  id.matches = false;
  if (!sx1262WaitBusy()) return id;

  SPI.beginTransaction(SPISettings(8000000, MSBFIRST, SPI_MODE0));
  SpiBusB::Hold hold(bus, SpiBDevice::Sx1262);
  if (!hold.ok()) {
    SPI.endTransaction();
    return id;
  }
  SPI.transfer(0x1D);          // ReadRegister
  SPI.transfer(0x07);          // address 0x0740
  SPI.transfer(0x40);
  SPI.transfer(0x00);          // one NOP status byte before the data
  const uint8_t msb = SPI.transfer(0x00);
  const uint8_t lsb = SPI.transfer(0x00);
  SPI.endTransaction();

  id.raw = uint32_t(msb) << 8 | lsb;
  id.alive = (id.raw != 0x0000) && (id.raw != 0xFFFF);
  id.matches = (id.raw == id.expected);
  return id;
}

// ---------------------------------------------------------------------------
// ST25R3916 (U9) -- 13.56 MHz NFC
//
// SPI MODE 1 on this part, not mode 0 -- the other two devices on the same bus
// are mode 0, which is exactly why every probe restates its own settings.
// Operation byte is {mode[1:0], addr[5:0]}; 0b01 is "read register".
//
// The identity register is read and REPORTED, not asserted: this programme has
// no ST25R3916 datasheet in the repository, and D-742 is a standing reminder of
// what happens when a decode is carried from memory.  Liveness is the claim --
// a value that is neither 0x00 nor 0xFF proves SCK, MOSI, MISO and NFC_CS_N are
// all where the map says.  Confirm the exact identity at first article.
inline DeviceIdentity probeSt25r3916(SpiBusB &bus) {
  const uint8_t kReadRegister = 0x40;
  const uint8_t kIcIdentity = 0x3F;

  DeviceIdentity id;
  id.device = "ST25R3916 U9";
  id.raw = 0;
  id.expected = kIdentityReportOnly;
  id.alive = false;
  id.matches = false;

  SPI.beginTransaction(SPISettings(4000000, MSBFIRST, SPI_MODE1));
  SpiBusB::Hold hold(bus, SpiBDevice::St25r3916);
  if (!hold.ok()) {
    SPI.endTransaction();
    return id;
  }
  SPI.transfer(uint8_t(kReadRegister | (kIcIdentity & 0x3F)));
  const uint8_t identity = SPI.transfer(0x00);
  SPI.endTransaction();

  id.raw = identity;
  id.alive = (identity != 0x00) && (identity != 0xFF);
  id.matches = id.alive;
  return id;
}

// ===========================================================================
// D-793 / R12-03.  QUIESCING THE TRANSCEIVERS, BEFORE ANYTHING IS PERMITTED.
//
// ROUND-12: "On every relevant boot/warm-reset/recovery path, explicitly
// quiesce/reset and verify CC1101 before permitting accessory power or any
// second transmitter.  If physical state cannot be confirmed, represent it as
// UNKNOWN/pessimistic and refuse conflicting permissions."
//
// U7 and U8 sit on +3V3.  An MCU reset does not touch that rail, so whatever
// the previous image left them doing they are still doing.  Neither
// `SpiBusB::transmitting_` nor `DemoBringupApp::subghz_tx_` can know that --
// both are C++ members and both are zero after a reset -- and parking a chip
// select changes nothing about a PA that is already keyed.
//
// WHAT EACH PART'S OWN SEMANTICS SUPPORT:
//
//   CC1101   SIDLE (strobe 0x36) leaves TX/RX for IDLE; SRES (strobe 0x30,
//            BURST CLEAR -- the trap `probeCc1101` documents) resets the whole
//            chip.  MARCSTATE (0x35, BURST SET, so header 0xF5) reads the main
//            radio control state machine, and 0x01 is IDLE.  So the quiesce is
//            ORDERED and then VERIFIED from the part's own register.
//   SX1262   SetStandby(0x80) with 0x00 selects STDBY_RC; GetStatus (0xC0)
//            returns a status byte whose bits [6:4] are the chip mode, 0x02
//            STBY_RC and 0x03 STBY_XOSC.  BUSY must be low before and after.
//   ST25R3916  DELIBERATELY NOT TOUCHED.  This repository holds no datasheet
//            for it and D-742 is the standing reminder of what a decode
//            carried from memory costs; a guessed register write could
//            ENERGISE a field rather than quiet one.  Its field is carried in
//            the canonical ledger as a bounded-duty allowance inside the
//            ALWAYS-ON set, so a retained field is already inside every floor
//            in the permission table.  Reported as UNKNOWN, not asserted.
// ===========================================================================
struct RadioQuiesce {
  bool cc1101_confirmed = false;
  uint8_t cc1101_marcstate = 0xFF;
  bool sx1262_confirmed = false;
  uint8_t sx1262_status = 0xFF;
  bool nfc_field_state_is_unknown = true;   // see above; bounded, not proven
  bool ok() const { return cc1101_confirmed && sx1262_confirmed; }
};

inline bool cc1101Quiesce(SpiBusB &bus, uint8_t *marcstate_out) {
  const uint8_t kSidle = 0x36;
  const uint8_t kSres = 0x30;          // BURST CLEAR -- the strobe, not PARTNUM
  const uint8_t kReadBurst = 0xC0;
  const uint8_t kMarcstate = 0x35;
  const uint8_t kMarcstateIdle = 0x01;

  SPI.beginTransaction(SPISettings(4000000, MSBFIRST, SPI_MODE0));
  SpiBusB::Hold hold(bus, SpiBDevice::Cc1101);
  if (!hold.ok()) {
    SPI.endTransaction();
    return false;
  }
  // The part holds SO high until its crystal is stable; its own access
  // sequence is to wait for the fall before the first header byte.
  uint32_t deadline = millis() + 10;
  while (digitalRead(AQROOT_PIN_SPI_B_MISO) == HIGH && millis() < deadline) {
  }
  SPI.transfer(kSidle);                // leave TX/RX
  SPI.transfer(kSres);                 // and reset the part outright
  // SRES holds SO high again until the reset completes.
  deadline = millis() + 10;
  while (digitalRead(AQROOT_PIN_SPI_B_MISO) == HIGH && millis() < deadline) {
  }
  SPI.transfer(uint8_t(kReadBurst | kMarcstate));
  const uint8_t marc = SPI.transfer(0x00);
  SPI.endTransaction();
  if (marcstate_out) *marcstate_out = marc;
  return (marc & 0x1F) == kMarcstateIdle;
}

inline bool sx1262Quiesce(SpiBusB &bus, uint8_t *status_out) {
  if (!sx1262WaitBusy()) return false;
  SPI.beginTransaction(SPISettings(8000000, MSBFIRST, SPI_MODE0));
  {
    SpiBusB::Hold hold(bus, SpiBDevice::Sx1262);
    if (!hold.ok()) {
      SPI.endTransaction();
      return false;
    }
    SPI.transfer(0x80);                // SetStandby
    SPI.transfer(0x00);                // STDBY_RC
  }
  SPI.endTransaction();
  if (!sx1262WaitBusy()) return false;
  uint8_t status = 0xFF;
  SPI.beginTransaction(SPISettings(8000000, MSBFIRST, SPI_MODE0));
  {
    SpiBusB::Hold hold(bus, SpiBDevice::Sx1262);
    if (!hold.ok()) {
      SPI.endTransaction();
      return false;
    }
    SPI.transfer(0xC0);                // GetStatus
    status = SPI.transfer(0x00);
  }
  SPI.endTransaction();
  if (status_out) *status_out = status;
  const uint8_t chip_mode = uint8_t((status >> 4) & 0x07);
  return chip_mode == 0x02 || chip_mode == 0x03;   // STBY_RC / STBY_XOSC
}

inline RadioQuiesce quiesceRadios(SpiBusB &bus) {
  RadioQuiesce r;
  r.cc1101_confirmed = cc1101Quiesce(bus, &r.cc1101_marcstate);
  r.sx1262_confirmed = sx1262Quiesce(bus, &r.sx1262_status);
  return r;
}

}  // namespace aqroot
#endif  // ARDUINO
