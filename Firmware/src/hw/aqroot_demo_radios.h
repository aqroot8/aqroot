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
// D-794 / R13-03.  THE IDENTITY IS NOW ASSERTED, NOT MERELY REPORTED, BECAUSE
// THE DATASHEET THAT WAS SUPPOSED TO BE MISSING IS IN THE ARCHIVE.
//
// D-793's comment here said "this programme has no ST25R3916 datasheet in the
// repository", so this probe could only claim LIVENESS -- a value that is
// neither 0x00 nor 0xFF proves SCK, MOSI, MISO and NFC_CS_N are where the map
// says -- and deferred the identity to first article.  The datasheet is
// `hardware/beta/kicad/aqroot-beta/vendor/ST25R3916/ST25R3916_DS12484_Rev3.pdf`
// and has been since the Beta board was drawn.
//
// DS12484 Rev 3 section 4.5.80, Table 117, IC identity register, address 3Fh,
// type R: bits 7..3 are `ic_type4..0` with defaults 0,0,1,0,1 and bits 2..0 are
// `ic_rev2..0`.  So the DEVICE TYPE is `(identity >> 3) & 0x1F == 0x05` and is
// a property of the part rather than of the die spin; the REVISION is reported
// beside it and is deliberately NOT asserted, for the same reason the CC1101's
// VERSION is not.  A wrong part in this socket now fails the probe instead of
// reading "alive".
inline DeviceIdentity probeSt25r3916(SpiBusB &bus) {
  const uint8_t kReadRegister = 0x40;
  const uint8_t kIcIdentity = 0x3F;
  const uint8_t kIcTypeSt25r3916 = 0x05;   // Table 117 ic_type4..0 defaults

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
  // The device TYPE is asserted; the revision in bits 2..0 is not.
  id.matches = id.alive
            && (uint8_t((identity >> 3) & 0x1F) == kIcTypeSt25r3916);
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
//   ST25R3916  QUIESCED AND VERIFIED AT D-794 -- see the block below, which
//            replaces D-793's "no datasheet in the repository".
// ===========================================================================
// ===========================================================================
// D-794 / R13-03.  THE THIRD RADIO, AND THE DATASHEET WAS IN THE REPOSITORY
// THE WHOLE TIME.
//
// ROUND-13, IN ITS OWN WORDS: "ST25R3916 can retain a physical RF field across
// MCU-only reset while software authority restarts with no burst owner.
// D-793 reset reconciliation covers CC1101/SX1262 but leaves NFC untouched.
// Use the exact ST25R3916 primary-documented mechanism to disable/reset the
// field and verify the physical state before accessory/burst/radio authority
// becomes permissive.  If field-off cannot be confirmed, represent NFC as
// UNKNOWN and block conflicting power/burst authority.  Do not assume 'stop
// all activities' is sufficient for every retained state; use datasheet
// semantics and reinitialize configuration as required."
//
// D-793'S REASON FOR LEAVING IT ALONE WAS FACTUALLY WRONG, AND THAT IS THE
// FINDING.  The comment this block replaces said "this repository holds no
// datasheet for it".  It does:
//     hardware/beta/kicad/aqroot-beta/vendor/ST25R3916/ST25R3916_DS12484_Rev3.pdf
//     sha256 6cac393e345ead685360befd6098d5aec7fbb1088b76ec33d1317a1c1a9773f6
// It has been in the tree since the Beta board was drawn.  A refusal justified
// by an absent document, where the document is present, is not conservatism --
// it is a wrong premise that happened to point at the cautious answer, and
// R12-03's own instruction ("do not blindly add resets without primary-device
// semantics") was satisfiable from the archive on the day it was written.
// This is the second time this programme has found a specification it already
// owned; the first was the Molex connector at R12-01.
//
// WHAT THE PRIMARY DOCUMENT ACTUALLY SAYS.  DS12484 Rev 3:
//
//   section 4.4.1, Set default -- direct command code C0/C1h -- "puts the
//   ST25R3916/7 in the same state as power-up initialization: performs Stop
//   all activities command, resets all registers to their default state,
//   clears all collision bits".  Table 13 lists its Operation mode as ALL, so
//   unlike most direct commands it does NOT require `en` to be set first: a
//   part left in Ready mode with the field up accepts it, and so does one in
//   power-down.
//
//   section 4.2, Operating modes -- "At power-on all its bits are set to 0,
//   the ST25R3916/7 is in Power-down mode."  And Table 21, Operation control
//   register, address 02h: bit 7 `en` (oscillator and regulators), bit 6
//   `rx_en`, bit 3 `tx_en` ("1: Enables Tx operation"), bit 2 `wu`, bits 1:0
//   `en_fd_c`.  Every default is 0.
//
//   Table 11, SPI operation modes: the first two bits of the first byte are
//   the mode.  `00` + addr is a register WRITE, `01` + addr is a register
//   READ, `11` is a direct command.  So `0x42` reads 02h and `0xC1` is Set
//   default.
//
// SO THE MECHANISM IS EXACT AND IT IS VERIFIABLE.  Set default returns the
// part to power-up state, which is Power-down with `tx_en` = 0 and `en` = 0 --
// the field OFF, by the datasheet's own definition of the power-on state.  The
// Operation control register is then READ BACK, and the quiesce is CONFIRMED
// only when it reads 0x00.  Nothing is assumed from the fact that the write
// ACKed: a part that answers SPI and keeps driving RFO1/RFO2 is precisely the
// state being defended against.
//
// WHY "STOP ALL ACTIVITIES" IS NOT THE COMMAND USED, which R13-03 asks about
// by name.  Section 4.4.2 lists what it stops -- FIFO, transmission and
// reception, the timers -- and it leaves the Operation control register
// ALONE.  A part with `en` and `tx_en` set is still generating an unmodulated
// carrier after it, because the carrier is not an "activity"; it is the
// register state.  It is also only accepted while `en` is set (Table 13),
// so on a part in some other mode it does nothing at all.  Set default is
// both stronger and unconditional.
//
// AND THE OVERHEAT FRAME IS RE-SENT, because section 4.1 requires it "after
// power-on AND Set default command" -- `FCh / 04h / 10h` -- and Set default
// has just undone it.  Leaving it out would quiet the field and leave the
// thermal protection where a reset put it, which is the "reinitialize
// configuration as required" half of R13-03.
// ===========================================================================
inline bool st25r3916Quiesce(SpiBusB &bus, uint8_t *opcontrol_out) {
  // Table 11: {00, A5..A0} write, {01, A5..A0} read, {11, ...} direct command.
  const uint8_t kRegisterRead = 0x40;
  const uint8_t kRegisterWrite = 0x00;
  const uint8_t kSetDefault = 0xC1;          // Table 13, section 4.4.1
  const uint8_t kRegOperationControl = 0x02;  // Table 21
  // Section 4.1: the overheat-protection frame, required after Set default.
  const uint8_t kOverheatFrame[3] = {0xFC, 0x04, 0x10};

  uint8_t op = 0xFF;
  SPI.beginTransaction(SPISettings(4000000, MSBFIRST, SPI_MODE1));
  {
    SpiBusB::Hold hold(bus, SpiBDevice::St25r3916);
    if (!hold.ok()) {
      SPI.endTransaction();
      if (opcontrol_out) *opcontrol_out = op;
      return false;
    }
    SPI.transfer(kSetDefault);
  }
  SPI.endTransaction();
  // The part re-initialises; give the oscillator and regulator teardown the
  // same order of settling the CC1101 path allows, then restore the thermal
  // protection section 4.1 requires after this command.
  delay(1);
  SPI.beginTransaction(SPISettings(4000000, MSBFIRST, SPI_MODE1));
  {
    SpiBusB::Hold hold(bus, SpiBDevice::St25r3916);
    if (!hold.ok()) {
      SPI.endTransaction();
      if (opcontrol_out) *opcontrol_out = op;
      return false;
    }
    for (uint8_t b : kOverheatFrame) SPI.transfer(b);
  }
  SPI.endTransaction();
  // READ BACK.  This, and not the ACK, is the physical verification.
  SPI.beginTransaction(SPISettings(4000000, MSBFIRST, SPI_MODE1));
  {
    SpiBusB::Hold hold(bus, SpiBDevice::St25r3916);
    if (!hold.ok()) {
      SPI.endTransaction();
      if (opcontrol_out) *opcontrol_out = op;
      return false;
    }
    SPI.transfer(uint8_t(kRegisterRead | (kRegOperationControl & 0x3F)));
    op = SPI.transfer(0x00);
  }
  SPI.endTransaction();
  (void)kRegisterWrite;
  if (opcontrol_out) *opcontrol_out = op;
  // Table 21: every bit defaults to 0, and that is Power-down -- no
  // oscillator, no regulator, no transmitter.  `tx_en` alone is not enough to
  // check: `en` set with `tx_en` clear still runs the analogue front end, and
  // a part that answered 0xFF answered nothing.
  return op == 0x00;
}

struct RadioQuiesce {
  bool cc1101_confirmed = false;
  uint8_t cc1101_marcstate = 0xFF;
  bool sx1262_confirmed = false;
  uint8_t sx1262_status = 0xFF;
  // D-794 / R13-03: no longer "unknown but bounded".  The field is commanded
  // off with the part's own documented mechanism and CONFIRMED from its own
  // Operation control register, or it is UNKNOWN and every conflicting
  // permission is refused.
  bool nfc_confirmed = false;
  uint8_t nfc_operation_control = 0xFF;
  bool nfcFieldStateIsUnknown() const { return !nfc_confirmed; }
  bool ok() const {
    return cc1101_confirmed && sx1262_confirmed && nfc_confirmed;
  }
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
  // D-794 / R13-03: the NFC front end is a powered peripheral that can be
  // sustaining a material load, and it is quiesced on the same path and to
  // the same standard as the other two.
  r.nfc_confirmed = st25r3916Quiesce(bus, &r.nfc_operation_control);
  return r;
}

}  // namespace aqroot
#endif  // ARDUINO
