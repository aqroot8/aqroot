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

#include <stddef.h>
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
// [D-795 / R14-02: THE PARAGRAPH BELOW IS D-794's ARGUMENT AND IT WAS ONE
// STEP SHORT.  A 0x00 read-back is also what an unanswering bus returns.  The
// liveness-qualified sequence that replaces it follows this block.]
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
// ===========================================================================
// D-795 / R14-02.  A SAFE-LOOKING DEFAULT IS NOT A RESPONSE.
//
// ROUND-14, IN ITS OWN WORDS: "An all-zero/unreadable U9 SPI response must
// NEVER count as confirmed FIELD OFF merely because Operation Control reset
// value is 0x00.  A retained physical field with ignored commands and
// zero-filled reads was reproduced while software set confirmed_off=1,
// allowed accessory power and released the burst slot."
//
// IT REPRODUCES, AND THE REASON IS ONE SENTENCE OF D-794's OWN ARGUMENT.
// D-794 read Operation control back and accepted 0x00 -- and 0x00 is ALSO
// what a MISO line reads when nothing is driving it low-to-high: a U9 whose
// chip select never asserts, a MISO pulled down, a part with no supply.  The
// value that proves the field is off is the same value that proves nothing
// answered.  So the read-back is only a verification once it has been
// preceded by a proof that the part on the other end is ALIVE and IS an
// ST25R3916, and followed by a proof that it still is.
//
// THE SEQUENCE, EVERY STEP FROM DS12484 Rev 3:
//
//   1  IDENTITY.  IC identity 3Fh (section 4.5.80, Table 117, read only):
//      ic_type4..0 = 0b00101.  With those five bits fixed the byte lies in
//      0x28..0x2F, so neither an all-zero nor an all-ones bus can pass.
//
//   2  CHALLENGE.  No-response timer register 2, 11h (section 4.5.23,
//      Table 50: type RW, every bit default 0).  Write 0x5A, read it back;
//      write 0xA5, read it back.  Two complementary patterns prove that
//      writes LAND and that reads are LIVE -- a stuck line cannot return both
//      and a bus that echoes the previous byte returns the wrong one.  The
//      register is chosen because it is inert: it defines a timeout that only
//      runs once a transmission has ENDED or a Start No-response timer
//      command is sent (Table 49's comment), and neither happens here.
//
//   3  SET DEFAULT, C1h (section 4.4.1, Table 13 operation mode ALL):
//      "resets all registers to their default state".
//
//   4  PROOF THAT SET DEFAULT RAN.  11h must now read 0x00, its Table 50
//      default -- it held 0xA5 a moment ago.  A part that ignores Set default
//      is caught HERE, by a register that has no other reason to change,
//      rather than being inferred from 02h (which a part might hold at 0x00
//      for another reason).
//
//   5  THE OVERHEAT FRAME, FCh / 04h / 10h, which section 4.1 requires after
//      power-on AND after Set default.
//
//   6  OPERATION CONTROL WRITTEN TO 0x00 EXPLICITLY.  R14-02 notes that the
//      archived text has a Set-default ambiguity; writing Table 21's all-zero
//      power-down value directly removes the dependency on it.
//
//   7  OPERATION CONTROL READ BACK, 02h == 0x00: `en`, `rx_en`, `tx_en`, `wu`
//      and `en_fd_c` all clear -- Power-down, no oscillator, no transmitter.
//
//   8  IDENTITY AGAIN.  The zero in step 7 is only meaningful if the part is
//      still the one that answered step 1.
//
// ANY failure leaves the field UNKNOWN.  UNKNOWN refuses accessory power by
// name and owns the burst slot; `DemoBringupApp` keeps asking until it is
// proved, and revokes a confirmation the moment liveness is lost again.
// ===========================================================================
enum class NfcQuiesceStep : uint8_t {
  Confirmed = 0,
  NoBus,               // the SPI-B hold was refused
  IdentityBefore,      // step 1
  ChallengeWrite,      // step 2
  SetDefaultIgnored,   // step 4
  OperationControl,    // step 7
  IdentityAfter,       // step 8
  // D-796 / D796-10: a field-owning NFC session holds U9; the quiesce did
  // not touch the part and proves nothing about its field.
  OwnedBySession,
};

inline const char *nfcQuiesceStepName(NfcQuiesceStep s) {
  switch (s) {
    case NfcQuiesceStep::Confirmed: return "confirmed";
    case NfcQuiesceStep::NoBus: return "SPI-B hold refused";
    case NfcQuiesceStep::IdentityBefore:
      return "no live ST25R3916 identity before the quiesce";
    case NfcQuiesceStep::ChallengeWrite:
      return "the 11h register challenge did not read back";
    case NfcQuiesceStep::SetDefaultIgnored:
      return "Set default did not reset 11h to its 0x00 default";
    case NfcQuiesceStep::OperationControl:
      return "Operation control 02h did not read 0x00";
    case NfcQuiesceStep::IdentityAfter:
      return "the ST25R3916 identity was lost after the quiesce";
    case NfcQuiesceStep::OwnedBySession:
      return "a field-owning NFC session holds U9; not touched";
  }
  return "unknown";
}

struct NfcQuiesceReport {
  bool confirmed = false;
  NfcQuiesceStep failed_at = NfcQuiesceStep::NoBus;
  uint8_t identity_before = 0x00;
  uint8_t identity_after = 0x00;
  uint8_t challenge_readback[2] = {0x00, 0x00};
  uint8_t after_set_default = 0xFF;
  uint8_t operation_control = 0xFF;
};

// DS12484 Rev 3 Table 117: ic_type4..0 = 0b00101 in bits 7..3.
inline bool st25r3916IdentityIsValid(uint8_t identity) {
  return uint8_t((identity >> 3) & 0x1F) == 0x05;
}

namespace st25r3916_spi {
// Table 11: {00, A5..A0} write, {01, A5..A0} read, {11, ...} direct command.
constexpr uint8_t kRegisterRead = 0x40;
constexpr uint8_t kRegisterWrite = 0x00;
constexpr uint8_t kSetDefault = 0xC1;            // Table 13, section 4.4.1
constexpr uint8_t kRegOperationControl = 0x02;   // Table 21
constexpr uint8_t kRegNoResponseTimer2 = 0x11;   // Table 50, RW, default 0x00
constexpr uint8_t kRegIcIdentity = 0x3F;         // Table 117, RO
constexpr uint8_t kChallenge[2] = {0x5A, 0xA5};

// One framed transfer of `n` bytes; returns false if the bus hold is refused.
inline bool frame(SpiBusB &bus, const uint8_t *out, uint8_t *in, size_t n) {
  SPI.beginTransaction(SPISettings(4000000, MSBFIRST, SPI_MODE1));
  bool ok = false;
  {
    SpiBusB::Hold hold(bus, SpiBDevice::St25r3916);
    if (hold.ok()) {
      for (size_t i = 0; i < n; ++i) {
        const uint8_t r = SPI.transfer(out[i]);
        if (in) in[i] = r;
      }
      ok = true;
    }
  }
  SPI.endTransaction();
  return ok;
}
inline bool readRegister(SpiBusB &bus, uint8_t addr, uint8_t *value) {
  const uint8_t out[2] = {uint8_t(kRegisterRead | (addr & 0x3F)), 0x00};
  uint8_t in[2] = {0, 0};
  if (!frame(bus, out, in, 2)) return false;
  *value = in[1];
  return true;
}
inline bool writeRegister(SpiBusB &bus, uint8_t addr, uint8_t value) {
  const uint8_t out[2] = {uint8_t(kRegisterWrite | (addr & 0x3F)), value};
  return frame(bus, out, nullptr, 2);
}
inline bool command(SpiBusB &bus, uint8_t code) {
  return frame(bus, &code, nullptr, 1);
}
}  // namespace st25r3916_spi

inline NfcQuiesceReport st25r3916QuiesceReport(SpiBusB &bus) {
  using namespace st25r3916_spi;
  NfcQuiesceReport r;
  // Once a live ST25R3916 has been identified, every failure path below still
  // WRITES Table 21's power-down value before it returns.  The write is never
  // TRUSTED -- the verdict stays UNKNOWN -- but a part that is half-answering
  // is more likely to be quiet after it than before, and it costs nothing.
  auto best_effort_power_down = [&bus]() {
    (void)writeRegister(bus, kRegOperationControl, 0x00);
  };
  // D-796 / D796-10: a field-owning session's field is ITS field.  The
  // quiesce would challenge 11h and Set-default the part out from under it,
  // so it refuses by name and touches nothing.
  if (nfcFieldSessionOwnsU9(bus)) {
    r.failed_at = NfcQuiesceStep::OwnedBySession;
    return r;
  }
  // 1  identity
  if (!readRegister(bus, kRegIcIdentity, &r.identity_before)) return r;
  if (!st25r3916IdentityIsValid(r.identity_before)) {
    r.failed_at = NfcQuiesceStep::IdentityBefore;
    return r;
  }
  // 2  challenge
  for (int i = 0; i < 2; ++i) {
    if (!writeRegister(bus, kRegNoResponseTimer2, kChallenge[i]) ||
        !readRegister(bus, kRegNoResponseTimer2, &r.challenge_readback[i])) {
      r.failed_at = NfcQuiesceStep::NoBus;
      return r;
    }
    if (r.challenge_readback[i] != kChallenge[i]) {
      r.failed_at = NfcQuiesceStep::ChallengeWrite;
      best_effort_power_down();
      return r;
    }
  }
  // 3  Set default
  if (!command(bus, kSetDefault)) return r;
  // The part re-initialises; give the oscillator and regulator teardown the
  // same order of settling the CC1101 path allows.
  delay(1);
  // 4  Set default really ran
  if (!readRegister(bus, kRegNoResponseTimer2, &r.after_set_default)) return r;
  if (r.after_set_default != 0x00) {
    r.failed_at = NfcQuiesceStep::SetDefaultIgnored;
    best_effort_power_down();
    return r;
  }
  // 5  the overheat frame, section 4.1
  const uint8_t overheat[3] = {0xFC, 0x04, 0x10};
  if (!frame(bus, overheat, nullptr, 3)) return r;
  // 6  Operation control written to its all-zero power-down value
  if (!writeRegister(bus, kRegOperationControl, 0x00)) return r;
  // 7  and read back
  if (!readRegister(bus, kRegOperationControl, &r.operation_control)) return r;
  if (r.operation_control != 0x00) {
    r.failed_at = NfcQuiesceStep::OperationControl;
    return r;
  }
  // 8  still alive, still an ST25R3916
  if (!readRegister(bus, kRegIcIdentity, &r.identity_after)) return r;
  if (!st25r3916IdentityIsValid(r.identity_after)) {
    r.failed_at = NfcQuiesceStep::IdentityAfter;
    return r;
  }
  r.failed_at = NfcQuiesceStep::Confirmed;
  r.confirmed = true;
  return r;
}

// D-795 / R14-02.  THE LIVENESS PROBE A CONFIRMED-QUIET PART MUST KEEP
// PASSING.  Identity plus a one-pattern challenge on the same inert register,
// restored to its default afterwards so nothing the quiesce proved is undone.
//
// D-796 / D796-10.  THIS PROBE WRITES REGISTER 11h, SO IT MAY ONLY RUN WHILE
// NOTHING ELSE OWNS U9.  Register 11h is inert only while the field is off:
// it is the No-response timer, which a FIELD-OWNING session arms for its own
// transactions.  So while a session holds the ownership token
// (`nfcFieldSessionOwnsU9`) this function returns false WITHOUT selecting the
// part -- never a proof, never a write.  Callers use
// `st25r3916LivenessProbe` below, which reports that case as `Deferred`
// rather than as a lost part.
inline bool st25r3916StillAlive(SpiBusB &bus, uint8_t *identity_out) {
  using namespace st25r3916_spi;
  if (nfcFieldSessionOwnsU9(bus)) {
    if (identity_out) *identity_out = 0x00;
    return false;
  }
  uint8_t id = 0x00, back = 0x00, restored = 0xFF;
  const bool read = readRegister(bus, kRegIcIdentity, &id);
  if (identity_out) *identity_out = id;
  if (!read || !st25r3916IdentityIsValid(id)) return false;
  if (!writeRegister(bus, kRegNoResponseTimer2, kChallenge[1]) ||
      !readRegister(bus, kRegNoResponseTimer2, &back) ||
      back != kChallenge[1]) {
    return false;
  }
  if (!writeRegister(bus, kRegNoResponseTimer2, 0x00) ||
      !readRegister(bus, kRegNoResponseTimer2, &restored) ||
      restored != 0x00) {
    return false;
  }
  // And the field is still where the quiesce left it.
  uint8_t op = 0xFF;
  return readRegister(bus, kRegOperationControl, &op) && op == 0x00;
}

// D-796 / D796-05 item 4 + D796-10.  THE PROBE THE SCHEDULER CALLS.
//
// Three answers, not two.  A part that answered the challenge is `Alive`; a
// part that did not is `Lost` and revokes the OFF confirmation.  But a probe
// that could not be RUN -- SPI-B already selected by another transaction, or
// a field-owning session holding U9 -- is `Deferred`: it says nothing about
// the part, and reporting it as `Lost` would revoke on a scheduling accident
// while reporting it as `Alive` would extend a confirmation nobody checked.
inline NfcLivenessResult st25r3916LivenessProbe(SpiBusB &bus,
                                                uint8_t *identity_out) {
  if (identity_out) *identity_out = 0x00;
  if (nfcFieldSessionOwnsU9(bus)) return NfcLivenessResult::Deferred;
  if (bus.selected() != SpiBDevice::None) return NfcLivenessResult::Deferred;
  return st25r3916StillAlive(bus, identity_out) ? NfcLivenessResult::Alive
                                                : NfcLivenessResult::Lost;
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
  // D-795 / R14-02: the whole liveness-qualified report, so the console can
  // say WHICH step failed rather than only that it did.
  NfcQuiesceReport nfc;
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
  r.nfc = st25r3916QuiesceReport(bus);
  r.nfc_confirmed = r.nfc.confirmed;
  r.nfc_operation_control = r.nfc.operation_control;
  return r;
}

}  // namespace aqroot
#endif  // ARDUINO
