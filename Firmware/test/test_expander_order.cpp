// AQROOT Demo -- the safe-ordering test.
//
// The PCAL9535A resets with every pin an INPUT and both OUTPUT registers at
// 0xFF (NXP Rev.2, Tables 7/8).  While the pins are inputs the external pulls
// define their safe physical level.  If firmware clears a direction bit before
// first loading the safe word, however, the reset HIGH latch becomes active.
// Most enable outputs on this board are safe LOW, while the three RGB cathodes
// are safe HIGH, so direction-first can energize a real load for
// as long as the next I2C transaction takes.  On ACC_5V_SW_EN or
// ACC_5V_BOOST_EN that is a live accessory rail; on AMP_SD_MODE it is a pop
// into the speaker; on NFC_5V_EN it is an enable into a DNP boost.
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
};

class RecordingBus : public I2cBus {
 public:
  std::vector<Txn> log;
  uint16_t u2_inputs = 0xFFFF;
  uint16_t u3_inputs = 0xFFFF;
  uint16_t u2_config = 0xFFFF;
  uint16_t u3_config = 0xFFFF;

  bool write(uint8_t address, const uint8_t *data, size_t length) override {
    Txn txn{address, data[0], 0, false};
    if (length == 3) {
      txn.value = uint16_t(data[1]) | uint16_t(uint16_t(data[2]) << 8);
    } else if (length == 2) {
      txn.value = data[1];
    }
    if (txn.reg == Pcal9535a::kRegConfig0) {
      (address == AQROOT_EXP_U2_ADDR ? u2_config : u3_config) = txn.value;
    }
    log.push_back(txn);
    return true;
  }

  bool readRegister(uint8_t address, uint8_t reg, uint8_t *data,
                    size_t length) override {
    log.push_back(Txn{address, reg, 0, true});
    uint16_t value = 0;
    if (reg == Pcal9535a::kRegInput0) {
      value = (address == AQROOT_EXP_U2_ADDR) ? u2_inputs : u3_inputs;
    } else if (reg == Pcal9535a::kRegConfig0) {
      value = (address == AQROOT_EXP_U2_ADDR) ? u2_config : u3_config;
    }
    for (size_t i = 0; i < length; ++i) {
      data[i] = uint8_t(value >> (8 * i));
    }
    return true;
  }

  bool probe(uint8_t) override { return true; }

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

  // Datasheet authority: PCAL9535A Rev.2 Tables 7/8 specify FFh for both
  // OUTPUT-port defaults.  Pin direction still resets to input (FFFFh).  Keep
  // this explicit because the safety reason for latch-before-direction changes
  // completely if somebody imports the old/incorrect 00h assumption.
  constexpr uint16_t kPcalOutputReset = 0xFFFF;
  check("PCAL9535A OUTPUT reset model is FFh/FFh", kPcalOutputReset == 0xFFFF);
  check("direction-first from reset would assert at least one safe-LOW U3 enable",
        (kPcalOutputReset & (bitmask(AQROOT_U3_ACC_5V_SW_EN) |
                             bitmask(AQROOT_U3_ACC_5V_BOOST_EN) |
                             bitmask(AQROOT_U3_ACC_3V3_EN))) != 0);

  // ---- T1: the bring-up order itself ---------------------------------
  RecordingBus bus;
  DemoExpanders expanders;
  check("begin() succeeds against a bus that ACKs", expanders.begin(bus));

  for (uint8_t address : {uint8_t(AQROOT_EXP_U2_ADDR), uint8_t(AQROOT_EXP_U3_ADDR)}) {
    char claim[128];
    const int latch = bus.indexOfWrite(address, Pcal9535a::kRegOutput0);
    const int direction = bus.indexOfWrite(address, Pcal9535a::kRegConfig0);
    const int pull_enable = bus.indexOfWrite(address, Pcal9535a::kRegPullEnable0);
    const int pull_select = bus.indexOfWrite(address, Pcal9535a::kRegPullSelect0);
    const int mask = bus.indexOfWrite(address, Pcal9535a::kRegIrqMask0);

    std::snprintf(claim, sizeof(claim),
                  "0x%02X: output latch is written BEFORE direction", address);
    check(claim, latch >= 0 && direction >= 0 && latch < direction);

    std::snprintf(claim, sizeof(claim),
                  "0x%02X: pull select precedes pull enable", address);
    check(claim, pull_select >= 0 && pull_enable >= 0 && pull_select < pull_enable);

    std::snprintf(claim, sizeof(claim),
                  "0x%02X: pulls and mask are set before the latch", address);
    check(claim, pull_enable < latch && mask >= 0 && mask < latch);

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

  std::printf("\n%s -- %d failure(s)\n", g_failures ? "FAIL" : "PASS", g_failures);
  return g_failures == 0 ? 0 : 1;
}
