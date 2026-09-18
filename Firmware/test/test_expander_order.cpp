// AQROOT Demo -- the safe-ordering test.
//
// The PCAL9535A resets with every pin an INPUT and -- D-753, corrected from
// 0x00 -- EVERY OUTPUT LATCH AT 0xFF.  NXP Rev. 2 tables 7 and 8 give Output
// port 0 (02h) and Output port 1 (03h) a power-on default of 1111 1111.
// Six of this board's expander outputs are safe at 0 and three -- the RGB
// cathodes -- are safe at 1, so a bring-up that clears a direction bit before
// the latch holds the right value drives the wrong level onto a real load for
// as long as the next I2C transaction takes.  THE REAL DEFAULT MAKES THIS
// WORSE: every one of the six safe-at-0 outputs is an ENABLE, and 0xFF is the
// unsafe value for all six.  On ACC_5V_SW_EN or ACC_5V_BOOST_EN that is a live
// accessory rail; on AMP_SD_MODE it is a pop into the speaker; on NFC_5V_EN it
// is an enable into a DNP boost.
//
// That ordering is not visible in a compile and it is not visible in DRC.  It
// is visible HERE, on a host build with no ESP32 present, because `I2cBus` is
// an interface and this file implements a recording one.
//
//     g++ -std=c++17 -I ../src/hw -o /tmp/t test_expander_order.cpp && /tmp/t

#include <cstdint>
#include <cstdio>
#include <cstring>
#include <string>
#include <vector>

#include "aqroot_demo_expanders.h"

using namespace aqroot;

namespace {

struct Txn {
  uint8_t address;
  uint8_t reg;
  uint16_t value;   // 16-bit for port-pair writes, 8-bit widened otherwise
  bool is_read;
  bool nacked = false;   // D-751: the transaction was ATTEMPTED and refused
};

class RecordingBus : public I2cBus {
 public:
  std::vector<Txn> log;
  uint16_t u2_inputs = 0xFFFF;
  uint16_t u3_inputs = 0xFFFF;
  uint16_t u2_config = 0xFFFF;
  uint16_t u3_config = 0xFFFF;
  // Warm MCU reset model: the PCALs remain powered and may retain arbitrary
  // previous output commands.  Start HIGH to make stale active-high enables
  // maximally visible until firmware overwrites the complete safe latch.
  uint16_t u2_output = 0xFFFF;
  uint16_t u3_output = 0xFFFF;

  // ---- D-751: SELECTIVE NACK -------------------------------------------
  // T10 exists because an independent-failure bug is invisible to a bus that
  // always ACKs: the `||` short circuits that D-750 repaired all passed every
  // test in this file, because no test had ever refused a transaction.  A
  // failed transaction is still LOGGED -- the whole question is whether the
  // firmware ATTEMPTED the other device, so an attempt that was refused must
  // remain visible.
  int fail_address = -1;         // -1 = never fail
  int fail_reg = -1;             // -1 = any register at that address
  bool fail_once = false;        // fail only the FIRST match, then behave
  int failures_injected = 0;

  bool shouldFail(uint8_t address, uint8_t reg) {
    if (fail_address < 0 || int(address) != fail_address) return false;
    if (fail_reg >= 0 && int(reg) != fail_reg) return false;
    if (fail_once && failures_injected > 0) return false;
    ++failures_injected;
    return true;
  }

  bool write(uint8_t address, const uint8_t *data, size_t length) override {
    Txn txn{address, data[0], 0, false};
    if (length == 3) {
      txn.value = uint16_t(data[1]) | uint16_t(uint16_t(data[2]) << 8);
    } else if (length == 2) {
      txn.value = data[1];
    }
    const bool nack = shouldFail(address, txn.reg);
    txn.nacked = nack;
    log.push_back(txn);
    if (nack) return false;
    if (txn.reg == Pcal9535a::kRegConfig0) {
      (address == AQROOT_EXP_U2_ADDR ? u2_config : u3_config) = txn.value;
    } else if (txn.reg == Pcal9535a::kRegOutput0) {
      (address == AQROOT_EXP_U2_ADDR ? u2_output : u3_output) = txn.value;
    }
    return true;
  }

  bool readRegister(uint8_t address, uint8_t reg, uint8_t *data,
                    size_t length) override {
    const bool nack = shouldFail(address, reg);
    log.push_back(Txn{address, reg, 0, true, nack});
    if (nack) return false;
    uint16_t value = 0;
    if (reg == Pcal9535a::kRegInput0) {
      value = (address == AQROOT_EXP_U2_ADDR) ? u2_inputs : u3_inputs;
    } else if (reg == Pcal9535a::kRegOutput0) {
      value = (address == AQROOT_EXP_U2_ADDR) ? u2_output : u3_output;
    } else if (reg == Pcal9535a::kRegConfig0) {
      value = (address == AQROOT_EXP_U2_ADDR) ? u2_config : u3_config;
    }
    for (size_t i = 0; i < length; ++i) {
      data[i] = uint8_t(value >> (8 * i));
    }
    return true;
  }

  bool probe(uint8_t) override { return true; }

  int countWrites(uint8_t address, uint8_t reg, size_t from = 0) const {
    int n = 0;
    for (size_t i = from; i < log.size(); ++i) {
      if (!log[i].is_read && log[i].address == address && log[i].reg == reg) ++n;
    }
    return n;
  }

  // Index of the first write of `reg` to `address`, or -1.
  int indexOfWrite(uint8_t address, uint8_t reg) const {
    for (size_t i = 0; i < log.size(); ++i) {
      if (!log[i].is_read && log[i].address == address && log[i].reg == reg) {
        return int(i);
      }
    }
    return -1;
  }

  int indexOfRead(uint8_t address, uint8_t reg) const {
    for (size_t i = 0; i < log.size(); ++i) {
      if (log[i].is_read && log[i].address == address && log[i].reg == reg) {
        return int(i);
      }
    }
    return -1;
  }

  uint16_t valueWritten(uint8_t address, uint8_t reg) const {
    const int index = indexOfWrite(address, reg);
    return index < 0 ? 0 : log[size_t(index)].value;
  }
};

int g_failures = 0;

void check(const char *claim, bool ok) {
  std::printf("[%s] %s\n", ok ? "PASS" : "FAIL", claim);
  if (!ok) ++g_failures;
}

}  // namespace

int main() {
  std::printf("AQROOT Demo -- expander safe-ordering test\n");
  std::printf("board_sha256 %s\n\n", AQROOT_DEMO_BOARD_SHA256);

  // ---- T0: a fresh MCU must not invent the retained PCAL latch --------
  // On an MCU-only reset the expanders remain powered.  The software object is
  // new but the hardware output latch is whatever the old firmware left there,
  // so a read-modify-write against an invented shadow is unsafe.
  {
    RecordingBus blind;
    Pcal9535a fresh(AQROOT_EXP_U3_ADDR);
    check("fresh PCAL software shadow is explicitly INVALID",
          !fresh.outputShadowValid());
    check("blind writeBit before safe-latch synchronization is REFUSED",
          !fresh.writeBit(blind, AQROOT_U3_ACC_5V_SW_EN, false) && blind.log.empty());
  }

  // ---- T1: the bring-up order itself ---------------------------------
  RecordingBus bus;
  DemoExpanders expanders;
  check("begin() succeeds against a bus that ACKs", expanders.begin(bus));
  check("warm reset: first bus write forces U2 safe latch",
        bus.log.size() >= 2 && !bus.log[0].is_read &&
            bus.log[0].address == AQROOT_EXP_U2_ADDR &&
            bus.log[0].reg == Pcal9535a::kRegOutput0 &&
            bus.log[0].value == kU2SafeLatch);
  check("warm reset: second bus write forces U3 safe latch before policy traffic",
        bus.log.size() >= 2 && !bus.log[1].is_read &&
            bus.log[1].address == AQROOT_EXP_U3_ADDR &&
            bus.log[1].reg == Pcal9535a::kRegOutput0 &&
            bus.log[1].value == kU3SafeLatch);

  for (uint8_t address : {uint8_t(AQROOT_EXP_U2_ADDR), uint8_t(AQROOT_EXP_U3_ADDR)}) {
    char claim[128];
    const int latch = bus.indexOfWrite(address, Pcal9535a::kRegOutput0);
    const int direction = bus.indexOfWrite(address, Pcal9535a::kRegConfig0);
    const int pull_enable = bus.indexOfWrite(address, Pcal9535a::kRegPullEnable0);
    const int pull_select = bus.indexOfWrite(address, Pcal9535a::kRegPullSelect0);
    const int mask = bus.indexOfWrite(address, Pcal9535a::kRegIrqMask0);
    const int output_config = bus.indexOfWrite(address, Pcal9535a::kRegOutputConfig);

    std::snprintf(claim, sizeof(claim),
                  "0x%02X: safe output latch is the FIRST write to this device", address);
    check(claim, latch >= 0 &&
          (pull_select < 0 || latch < pull_select) &&
          (pull_enable < 0 || latch < pull_enable) &&
          (mask < 0 || latch < mask) &&
          (output_config < 0 || latch < output_config) &&
          (direction < 0 || latch < direction));

    std::snprintf(claim, sizeof(claim),
                  "0x%02X: pull select precedes pull enable", address);
    check(claim, pull_select >= 0 && pull_enable >= 0 && pull_select < pull_enable);

    std::snprintf(claim, sizeof(claim),
                  "0x%02X: output configuration is PUSH-PULL before direction", address);
    check(claim, output_config >= 0 && direction >= 0 && output_config < direction &&
                     bus.valueWritten(address, Pcal9535a::kRegOutputConfig) == 0x0000);

    std::snprintf(claim, sizeof(claim),
                  "0x%02X: direction is LAST among safety configuration writes", address);
    check(claim, direction > latch && direction > pull_enable && direction > mask &&
                     direction > output_config);

    // D-753.  THE ORDERING IS NON-VACUOUS AGAINST THE PART'S REAL POR VALUE.
    // NXP tables 7/8: both output ports power up at 0xFF.  So for every output
    // bit whose safe latch is 0, the direction bit going first would drive it
    // HIGH -- and this asserts that such a bit EXISTS on each device, which is
    // what makes "latch before direction" a requirement rather than a habit.
    const uint16_t kPorOutput = 0xFFFF;      // NXP PCAL9535A Rev.2, tables 7/8
    const uint16_t latch_value = bus.valueWritten(address, Pcal9535a::kRegOutput0);
    const uint16_t direction_value =
        bus.valueWritten(address, Pcal9535a::kRegConfig0);
    const uint16_t outputs = uint16_t(~direction_value);
    std::snprintf(claim, sizeof(claim),
                  "0x%02X: at least one OUTPUT is safe at 0 and so disagrees "
                  "with the 0xFF power-on latch", address);
    check(claim, (outputs & uint16_t(kPorOutput & ~latch_value)) != 0);

    std::snprintf(claim, sizeof(claim),
                  "0x%02X: polarity inversion is left at 0 (invert in firmware)",
                  address);
    check(claim, bus.valueWritten(address, Pcal9535a::kRegPolarity0) == 0x0000);
  }

  // ---- T2: the words written are the as-built ones --------------------
  check("U2 latch is the safe word",
        bus.valueWritten(AQROOT_EXP_U2_ADDR, Pcal9535a::kRegOutput0) == kU2SafeLatch);
  check("U3 latch is the safe word (RGB dark)",
        bus.valueWritten(AQROOT_EXP_U3_ADDR, Pcal9535a::kRegOutput0) == kU3SafeLatch);
  // ...AND SAID INDEPENDENTLY OF THAT CONSTANT.  The two claims above compare
  // the bus against `kU2SafeLatch`/`kU3SafeLatch`, so an edit that moves the
  // constant moves both sides and proves nothing.  D13's anode is +3V3, so the
  // cathode bits must be HIGH at boot, and that is a fact about the BOARD.
  check("the RGB cathodes are HIGH (dark) at boot -- D13's anode is +3V3",
        (bus.valueWritten(AQROOT_EXP_U3_ADDR, Pcal9535a::kRegOutput0) & kRgbMask) ==
            kRgbMask);
  check("U2 direction matches the as-built input set",
        bus.valueWritten(AQROOT_EXP_U2_ADDR, Pcal9535a::kRegConfig0) == kU2Inputs);
  check("U3 direction matches the as-built input set",
        bus.valueWritten(AQROOT_EXP_U3_ADDR, Pcal9535a::kRegConfig0) == kU3Inputs);

  // ---- T3: every accessory enable is LOW after bring-up ---------------
  const uint16_t u3_latch = bus.valueWritten(AQROOT_EXP_U3_ADDR,
                                             Pcal9535a::kRegOutput0);
  check("ACC_5V_BOOST_EN is low after bring-up",
        (u3_latch & bitmask(AQROOT_U3_ACC_5V_BOOST_EN)) == 0);
  check("ACC_5V_SW_EN is low after bring-up",
        (u3_latch & bitmask(AQROOT_U3_ACC_5V_SW_EN)) == 0);
  check("ACC_3V3_EN is low after bring-up",
        (u3_latch & bitmask(AQROOT_U3_ACC_3V3_EN)) == 0);
  check("SX1262_RXEN is low after bring-up",
        (u3_latch & bitmask(AQROOT_U3_SX1262_RXEN)) == 0);
  const uint16_t u2_latch = bus.valueWritten(AQROOT_EXP_U2_ADDR,
                                             Pcal9535a::kRegOutput0);
  check("NFC_5V_EN is low after bring-up (U13 is DNP)",
        (u2_latch & bitmask(AQROOT_U2_NFC_5V_EN)) == 0);
  check("AMP_SD_MODE is low after bring-up (amplifier shut down)",
        (u2_latch & bitmask(AQROOT_U2_AMP_SD_MODE)) == 0);
  check("ACC_PWR_EN is low after bring-up (accessory bus isolated)",
        (u2_latch & bitmask(AQROOT_U2_ACC_PWR_EN)) == 0);
  check("the three resets are ASSERTED by the safe latch",
        (u2_latch & (bitmask(AQROOT_U2_DISP_RST_N) |
                     bitmask(AQROOT_U2_TOUCH_RST_N) |
                     bitmask(AQROOT_U2_SX1262_RST_N))) == 0);

  // ---- T4: the interrupt mask policy ---------------------------------
  const uint16_t u2_mask = bus.valueWritten(AQROOT_EXP_U2_ADDR,
                                            Pcal9535a::kRegIrqMask0);
  const uint16_t u3_mask = bus.valueWritten(AQROOT_EXP_U3_ADDR,
                                            Pcal9535a::kRegIrqMask0);
  check("BQ25185_STAT2 is MASKED -- U11.3 is unconnected (D-742)",
        (u2_mask & bitmask(AQROOT_U2_BQ25185_STAT2)) != 0);
  check("both public XGPIO are MASKED -- MX-9",
        (u3_mask & bitmask(AQROOT_U3_XGPIO4)) != 0 &&
            (u3_mask & bitmask(AQROOT_U3_XGPIO5)) != 0);
  check("all six buttons are UNMASKED",
        (u2_mask & kButtonMask) == 0);
  check("SX1262_DIO1 is UNMASKED -- D-740 routed it",
        (u2_mask & bitmask(AQROOT_U2_SX1262_DIO1)) == 0);
  check("TOUCH_INT_N is UNMASKED and carries the internal pull-up",
        (u2_mask & bitmask(AQROOT_U2_TOUCH_INT_N)) == 0 &&
            (bus.valueWritten(AQROOT_EXP_U2_ADDR, Pcal9535a::kRegPullEnable0) &
             bitmask(AQROOT_U2_TOUCH_INT_N)) != 0 &&
            (bus.valueWritten(AQROOT_EXP_U2_ADDR, Pcal9535a::kRegPullSelect0) &
             bitmask(AQROOT_U2_TOUCH_INT_N)) != 0);
  check("SX1262_DIO1 carries NO internal pull (push-pull driver)",
        (bus.valueWritten(AQROOT_EXP_U2_ADDR, Pcal9535a::kRegPullEnable0) &
         bitmask(AQROOT_U2_SX1262_DIO1)) == 0);
  check("the four NC-DEMO spares are pulled up and masked",
        (bus.valueWritten(AQROOT_EXP_U3_ADDR, Pcal9535a::kRegPullEnable0) &
         kU3SpareMask) == kU3SpareMask &&
            (u3_mask & kU3SpareMask) == kU3SpareMask);

  // ---- T5: accessory 5 V sequencing ----------------------------------
  {
    RecordingBus five;
    DemoExpanders local;
    local.begin(five);
    const size_t mark = five.log.size();
    local.setAccessory5v(five, true);
    int boost_on = -1, switch_on = -1;
    for (size_t i = mark; i < five.log.size(); ++i) {
      if (five.log[i].is_read || five.log[i].reg != Pcal9535a::kRegOutput0) continue;
      if (boost_on < 0 && (five.log[i].value & bitmask(AQROOT_U3_ACC_5V_BOOST_EN))) {
        boost_on = int(i);
      }
      if (switch_on < 0 && (five.log[i].value & bitmask(AQROOT_U3_ACC_5V_SW_EN))) {
        switch_on = int(i);
      }
    }
    check("5 V up: the BOOST enable leads the LOAD SWITCH (D-186)",
          boost_on >= 0 && switch_on >= 0 && boost_on < switch_on);

    const size_t down = five.log.size();
    local.setAccessory5v(five, false);
    int boost_off = -1, switch_off = -1;
    for (size_t i = down; i < five.log.size(); ++i) {
      if (five.log[i].is_read || five.log[i].reg != Pcal9535a::kRegOutput0) continue;
      if (switch_off < 0 && !(five.log[i].value & bitmask(AQROOT_U3_ACC_5V_SW_EN))) {
        switch_off = int(i);
      }
      if (boost_off < 0 && !(five.log[i].value & bitmask(AQROOT_U3_ACC_5V_BOOST_EN))) {
        boost_off = int(i);
      }
    }
    check("5 V down: the LOAD SWITCH opens before the BOOST",
          switch_off >= 0 && boost_off >= 0 && switch_off < boost_off);
  }

  // ---- T6: the accessory I2C buffer cannot precede its own supply -----
  {
    RecordingBus buffer;
    DemoExpanders local;
    local.begin(buffer);
    check("ACC_PWR_EN is REFUSED while ACC_3V3_SW is down (U16 is fed from it)",
          !local.setAccessoryI2cBuffer(buffer, true));
    check("ACC_PWR_EN is accepted once ACC_3V3_EN is asserted",
          local.setAccessory3v3(buffer, true) &&
              local.setAccessoryI2cBuffer(buffer, true));
  }

  // ---- T7: service() reads status before it clears the condition ------
  {
    RecordingBus svc;
    DemoExpanders local;
    local.begin(svc);
    svc.log.clear();
    local.service(svc);
    const int status = svc.indexOfRead(AQROOT_EXP_U2_ADDR, Pcal9535a::kRegIrqStatus0);
    const int input = svc.indexOfRead(AQROOT_EXP_U2_ADDR, Pcal9535a::kRegInput0);
    check("service() reads the interrupt STATUS before the INPUT port",
          status >= 0 && input >= 0 && status < input);
    check("service() reads BOTH devices -- WAKE_INT_N is a wired-OR",
          svc.indexOfRead(AQROOT_EXP_U3_ADDR, Pcal9535a::kRegInput0) >= 0);
  }

  // ---- T8: a fault drops both disconnects without being asked --------
  {
    RecordingBus fault;
    DemoExpanders local;
    local.begin(fault);
    local.setAccessory3v3(fault, true);
    local.setAccessory5v(fault, true);
    // ACC_POWER_FAULT_N is active low.
    fault.u3_inputs = uint16_t(0xFFFF & ~bitmask(AQROOT_U3_ACC_POWER_FAULT_N));
    fault.log.clear();
    local.service(fault);
    check("a reported accessory fault is seen", local.accessoryFault());
    bool five_down = false, three_down = false;
    for (const Txn &txn : fault.log) {
      if (txn.is_read || txn.reg != Pcal9535a::kRegOutput0) continue;
      if (txn.address != AQROOT_EXP_U3_ADDR) continue;
      if (!(txn.value & bitmask(AQROOT_U3_ACC_5V_BOOST_EN)) &&
          !(txn.value & bitmask(AQROOT_U3_ACC_5V_SW_EN))) {
        five_down = true;
      }
      if (!(txn.value & bitmask(AQROOT_U3_ACC_3V3_EN))) three_down = true;
    }
    check("a fault drops the 5 V boost AND the 5 V load switch", five_down);
    check("a fault drops the switched 3.3 V rail", three_down);
  }

  // ---- T9: the charger decode is STAT1-only and never claims charging -
  {
    RecordingBus charger;
    DemoExpanders local;
    charger.u3_inputs = uint16_t(0xFFFF & ~bitmask(AQROOT_U3_BQ25185_STAT1));
    local.begin(charger);
    check("STAT1 LOW decodes as FAULT (SLUSF65B Table 6-2)",
          local.charger() == ChargerState::Fault);
    RecordingBus ok;
    DemoExpanders high;
    ok.u3_inputs = 0xFFFF;
    high.begin(ok);
    check("STAT1 HIGH decodes as NOT-FAULTED, not as charging",
          high.charger() == ChargerState::NotFaulted);
  }

  // ---- T10: ONE DEVICE'S BUS ERROR MUST NOT SILENCE THE OTHER --------
  // D-750 repaired three `||` short circuits and D-751 proves them.  Each
  // claim below is stated twice: once against a bus that REFUSES a chosen
  // transaction, and once against the same bus with nothing injected, so the
  // control cannot pass because the sequence never ran.
  {
    // T10a: begin().  U2's very first configuration write NACKs.  U3 owns
    // NFC_5V_EN, both radio resets and both transmit enables; it must still be
    // driven into its safe state.
    RecordingBus hurt;
    hurt.fail_address = AQROOT_EXP_U2_ADDR;   // every U2 transaction
    DemoExpanders local;
    const bool ok = local.begin(hurt);
    check("begin(): a U2 bus failure is REPORTED", !ok);
    check("begin(): U3's safe latch is written ANYWAY after U2 fails",
          hurt.indexOfWrite(AQROOT_EXP_U3_ADDR, Pcal9535a::kRegOutput0) >= 0);
    check("begin(): U3's direction is written ANYWAY after U2 fails",
          hurt.indexOfWrite(AQROOT_EXP_U3_ADDR, Pcal9535a::kRegConfig0) >= 0);
    check("begin(): U3's latch is still the as-built safe word",
          hurt.valueWritten(AQROOT_EXP_U3_ADDR, Pcal9535a::kRegOutput0) ==
              kU3SafeLatch);
    check("begin(): the U2 write really was refused (control is not vacuous)",
          hurt.failures_injected > 0);

    RecordingBus well;
    DemoExpanders healthy;
    check("begin(): the same sequence SUCCEEDS with nothing injected",
          healthy.begin(well) && well.failures_injected == 0);
  }
  {
    // T10b: service().  U2's input read NACKs.  U3 is the device whose input
    // port carries ACC_POWER_FAULT_N.
    RecordingBus hurt;
    DemoExpanders local;
    local.begin(hurt);
    hurt.log.clear();
    hurt.fail_address = AQROOT_EXP_U2_ADDR;
    hurt.fail_reg = Pcal9535a::kRegInput0;
    const bool ok = local.service(hurt);
    check("service(): a U2 input-read failure is REPORTED", !ok);
    check("service(): U3's input port is read ANYWAY after U2 fails",
          hurt.indexOfRead(AQROOT_EXP_U3_ADDR, Pcal9535a::kRegInput0) >= 0);
    check("service(): U3's interrupt status is read ANYWAY",
          hurt.indexOfRead(AQROOT_EXP_U3_ADDR, Pcal9535a::kRegIrqStatus0) >= 0);
    check("service(): the U2 read really was refused", hurt.failures_injected > 0);
  }
  {
    // T10c: the 5 V shutdown.  The FIRST output write to U3 NACKs; the second
    // must still be attempted AND must take both bits down, because a failed
    // write leaves the driver's shadow holding ACC_5V_SW_EN high (D-751
    // `clearBits`).
    RecordingBus hurt;
    DemoExpanders local;
    local.begin(hurt);
    local.setAccessory5v(hurt, true);
    const size_t mark = hurt.log.size();
    hurt.fail_address = AQROOT_EXP_U3_ADDR;
    hurt.fail_reg = Pcal9535a::kRegOutput0;
    hurt.fail_once = true;
    const bool ok = local.setAccessory5v(hurt, false);
    check("5 V down: a NACK on the first write is REPORTED", !ok);
    check("5 V down: the SECOND write is attempted anyway",
          hurt.countWrites(AQROOT_EXP_U3_ADDR, Pcal9535a::kRegOutput0, mark) >= 2);
    bool both_down = false;
    for (size_t i = mark; i < hurt.log.size(); ++i) {
      const Txn &t = hurt.log[i];
      if (t.is_read || t.nacked || t.address != AQROOT_EXP_U3_ADDR) continue;
      if (t.reg != Pcal9535a::kRegOutput0) continue;
      if (!(t.value & bitmask(AQROOT_U3_ACC_5V_BOOST_EN)) &&
          !(t.value & bitmask(AQROOT_U3_ACC_5V_SW_EN))) {
        both_down = true;
      }
    }
    check("5 V down: one SURVIVING write takes the boost AND the switch down",
          both_down);
  }
  {
    // T10d: the 3.3 V shutdown spans TWO DEVICES.  A U2 failure must not leave
    // U3's switched rail on.
    RecordingBus hurt;
    DemoExpanders local;
    local.begin(hurt);
    local.setAccessory3v3(hurt, true);
    const size_t mark = hurt.log.size();
    hurt.fail_address = AQROOT_EXP_U2_ADDR;
    hurt.fail_reg = Pcal9535a::kRegOutput0;
    const bool ok = local.setAccessory3v3(hurt, false);
    check("3.3 V down: a U2 NACK is REPORTED", !ok);
    bool rail_down = false;
    for (size_t i = mark; i < hurt.log.size(); ++i) {
      const Txn &t = hurt.log[i];
      if (t.is_read || t.nacked || t.address != AQROOT_EXP_U3_ADDR) continue;
      if (t.reg != Pcal9535a::kRegOutput0) continue;
      if (!(t.value & bitmask(AQROOT_U3_ACC_3V3_EN))) rail_down = true;
    }
    check("3.3 V down: U3 drops ACC_3V3_EN even though U2 failed", rail_down);
  }
  {
    // T10e: a fault shutdown whose writes fail must SAY SO.  D-750 replaced
    // two `(void)` discards with a recorded outcome precisely so a diagnostic
    // cannot print success after throwing the answer away.
    RecordingBus hurt;
    DemoExpanders local;
    local.begin(hurt);
    local.setAccessory3v3(hurt, true);
    local.setAccessory5v(hurt, true);
    hurt.u3_inputs = uint16_t(0xFFFF & ~bitmask(AQROOT_U3_ACC_POWER_FAULT_N));
    hurt.log.clear();
    hurt.fail_address = AQROOT_EXP_U3_ADDR;
    hurt.fail_reg = Pcal9535a::kRegOutput0;
    const bool ok = local.service(hurt);
    check("fault shutdown: service() returns FALSE when its writes fail", !ok);
    check("fault shutdown: it is RECORDED as having run",
          local.faultShutdownSeen());
    check("fault shutdown: it is RECORDED as having FAILED",
          !local.faultShutdownOk());

    RecordingBus clean;
    DemoExpanders good;
    good.begin(clean);
    good.setAccessory3v3(clean, true);
    good.setAccessory5v(clean, true);
    clean.u3_inputs = uint16_t(0xFFFF & ~bitmask(AQROOT_U3_ACC_POWER_FAULT_N));
    check("fault shutdown: the SAME path reports OK on a healthy bus",
          good.service(clean) && good.faultShutdownSeen() &&
              good.faultShutdownOk());
  }
  {
    // T10f / D-766: Astra round-2 reproduced the missing case.  U3's input
    // register is the ONLY observation of ACC_POWER_FAULT_N.  If that read
    // fails while output writes still work, loss of observability must itself
    // force both accessory rails down and block re-enable until a good read.
    RecordingBus hurt;
    DemoExpanders local;
    local.begin(hurt);
    check("lost-fault-read setup: 3.3 V can be enabled",
          local.setAccessory3v3(hurt, true));
    check("lost-fault-read setup: 5 V can be enabled",
          local.setAccessory5v(hurt, true));
    const size_t mark = hurt.log.size();
    hurt.fail_address = AQROOT_EXP_U3_ADDR;
    hurt.fail_reg = Pcal9535a::kRegInput0;
    hurt.fail_once = true;
    check("lost U3 fault-input read is REPORTED", !local.service(hurt));
    check("lost U3 fault-input read is LATCHED as unknown",
          local.faultObservabilityLost());
    check("lost U3 fault-input read ATTEMPTS shutdown writes",
          hurt.countWrites(AQROOT_EXP_U3_ADDR, Pcal9535a::kRegOutput0, mark) >= 2);
    check("lost U3 fault-input read leaves all accessory enables LOW",
          !(hurt.u3_output & bitmask(AQROOT_U3_ACC_3V3_EN)) &&
          !(hurt.u3_output & bitmask(AQROOT_U3_ACC_5V_SW_EN)) &&
          !(hurt.u3_output & bitmask(AQROOT_U3_ACC_5V_BOOST_EN)));
    check("re-enable is REFUSED while fault observability is lost",
          !local.setAccessory3v3(hurt, true) &&
          !local.setAccessory5v(hurt, true));

    hurt.fail_address = -1;
    hurt.fail_reg = -1;
    hurt.fail_once = false;
    check("a later clean U3 read restores fault observability",
          local.service(hurt) && !local.faultObservabilityLost());
    check("accessory re-enable is allowed only after recovery",
          local.setAccessory3v3(hurt, true));
  }

  std::printf("\n%s -- %d failure(s)\n", g_failures ? "FAIL" : "PASS", g_failures);
  return g_failures == 0 ? 0 : 1;
}
