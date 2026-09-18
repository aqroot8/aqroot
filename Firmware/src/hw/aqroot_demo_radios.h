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

}  // namespace aqroot
#endif  // ARDUINO
