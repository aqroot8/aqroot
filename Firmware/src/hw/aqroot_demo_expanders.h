#pragma once
// AQROOT Demo -- the U2/U3 policy layer.
//
// `pcal9535a.h` knows the part.  THIS file knows the BOARD: which bit is which
// signal, which way each one is active, what level is safe before the rail is
// trusted, which inputs may wake the MCU, and the order the accessory power
// tree has to be operated in.
//
// Every mask below is COMPUTED from `aqroot_demo_board.h`, which is generated
// from `aqroot-Beta-v2.kicad_pcb` and re-checked by
// `checks/firmware_hw_map_contract.py`.  Nothing here is a transcribed bit
// number, so a board revision that moves a channel moves these masks with it
// and the static_asserts below are what catch a move that does not add up.

#include <stdint.h>

#include "aqroot_demo_board.h"
#include "aqroot_i2c.h"
#include "pcal9535a.h"

namespace aqroot {

constexpr uint16_t bitmask(int index) { return uint16_t(1u << index); }

// ---------------------------------------------------------------------------
// U2 -- internal controls, front buttons, internal status
// ---------------------------------------------------------------------------
constexpr uint16_t kU2Outputs =
    bitmask(AQROOT_U2_TOUCH_RST_N) | bitmask(AQROOT_U2_SX1262_RST_N) |
    bitmask(AQROOT_U2_NFC_5V_EN) | bitmask(AQROOT_U2_AMP_SD_MODE) |
    bitmask(AQROOT_U2_DISP_RST_N) | bitmask(AQROOT_U2_ACC_PWR_EN);

constexpr uint16_t kU2Inputs =
    bitmask(AQROOT_U2_SX1262_DIO1) | bitmask(AQROOT_U2_TOUCH_INT_N) |
    bitmask(AQROOT_U2_SD_CARD_DETECT_N) | bitmask(AQROOT_U2_BTN_A_N) |
    bitmask(AQROOT_U2_BTN_UP_N) | bitmask(AQROOT_U2_BTN_DOWN_N) |
    bitmask(AQROOT_U2_BTN_LEFT_N) | bitmask(AQROOT_U2_BTN_RIGHT_N) |
    bitmask(AQROOT_U2_BTN_B_N) | bitmask(AQROOT_U2_BQ25185_STAT2);

constexpr uint16_t kButtonMask =
    bitmask(AQROOT_U2_BTN_A_N) | bitmask(AQROOT_U2_BTN_B_N) |
    bitmask(AQROOT_U2_BTN_UP_N) | bitmask(AQROOT_U2_BTN_DOWN_N) |
    bitmask(AQROOT_U2_BTN_LEFT_N) | bitmask(AQROOT_U2_BTN_RIGHT_N);

// Safe boot latch.  Every U2 output is safe LOW and every one of them is
// already held there by an external 100k while the expander is high-impedance
// (R12, R13, R14, R15, R16, R17) -- so this word agrees with the copper, and
// the generator refuses to emit the map if it ever stops agreeing.
constexpr uint16_t kU2SafeLatch = 0x0000;

// TOUCH_INT_N is the only U2 input with no external pull: its sole partner is
// the display FPC.  Unmasked and floating, an absent panel would hold
// WAKE_INT_N down forever and starve the buttons.
constexpr uint16_t kU2PullEnable = bitmask(AQROOT_U2_TOUCH_INT_N);
constexpr uint16_t kU2PullUp = bitmask(AQROOT_U2_TOUCH_INT_N);

// UNMASKED: six buttons, touch, card-detect, and the LoRa interrupt D-740
// routed.  MASKED: BQ25185_STAT2 -- U11.3 ships unconnected (owner decision
// D-742), so R128 holds the bit at a static HIGH and it carries no information.
constexpr uint16_t kU2IrqUnmasked =
    kButtonMask | bitmask(AQROOT_U2_TOUCH_INT_N) |
    bitmask(AQROOT_U2_SD_CARD_DETECT_N) | bitmask(AQROOT_U2_SX1262_DIO1);

// ---------------------------------------------------------------------------
// U3 -- front RGB, accessory power tree, public XGPIO
// ---------------------------------------------------------------------------
constexpr uint16_t kU3Outputs =
    bitmask(AQROOT_U3_FRONT_RGB_R_N) | bitmask(AQROOT_U3_FRONT_RGB_G_N) |
    bitmask(AQROOT_U3_FRONT_RGB_B_N) | bitmask(AQROOT_U3_ACC_5V_SW_EN) |
    bitmask(AQROOT_U3_ACC_3V3_EN) | bitmask(AQROOT_U3_ACC_5V_BOOST_EN) |
    bitmask(AQROOT_U3_SX1262_RXEN);

constexpr uint16_t kU3Inputs =
    bitmask(AQROOT_U3_XGPIO4) | bitmask(AQROOT_U3_XGPIO5) |
    bitmask(AQROOT_U3_SPARE_U3_P06) | bitmask(AQROOT_U3_SPARE_U3_P07) |
    bitmask(AQROOT_U3_SPARE_U3_P10) | bitmask(AQROOT_U3_SPARE_U3_P11) |
    bitmask(AQROOT_U3_ACC_DETECT_N) | bitmask(AQROOT_U3_ACC_POWER_FAULT_N) |
    bitmask(AQROOT_U3_BQ25185_STAT1);

constexpr uint16_t kRgbMask =
    bitmask(AQROOT_U3_FRONT_RGB_R_N) | bitmask(AQROOT_U3_FRONT_RGB_G_N) |
    bitmask(AQROOT_U3_FRONT_RGB_B_N);

// The RGB cathodes are the board's only outputs whose safe level is 1: D13's
// anode is +3V3, so a 1 is a dark LED.  Every accessory enable is safe at 0 and
// externally pulled there (R98, R102, R131, R74).
constexpr uint16_t kU3SafeLatch = kRgbMask;

// The two public XGPIO and the four NC-DEMO spares have no external part, so
// the internal 100k is what stops six CMOS inputs from floating.
constexpr uint16_t kU3SpareMask =
    bitmask(AQROOT_U3_SPARE_U3_P06) | bitmask(AQROOT_U3_SPARE_U3_P07) |
    bitmask(AQROOT_U3_SPARE_U3_P10) | bitmask(AQROOT_U3_SPARE_U3_P11);
constexpr uint16_t kU3PullEnable =
    kU3SpareMask | bitmask(AQROOT_U3_XGPIO4) | bitmask(AQROOT_U3_XGPIO5);
constexpr uint16_t kU3PullUp = kU3PullEnable;

// UNMASKED: accessory present and accessory power fault.  The public XGPIO are
// MASKED on purpose (MX-9) -- an accessory must not be able to hold the shared
// wake line and starve the buttons.  BQ25185_STAT1 is masked and polled: it
// moves only on fault entry/exit, and the board carries no NTC, so there is no
// temperature-boundary chatter to wake on.
constexpr uint16_t kU3IrqUnmasked =
    bitmask(AQROOT_U3_ACC_DETECT_N) | bitmask(AQROOT_U3_ACC_POWER_FAULT_N);

// ---------------------------------------------------------------------------
// Arithmetic that must hold for the map to be self-consistent.  These are the
// cheapest possible guard against a future board revision that moves a channel
// and leaves one of the words above behind.
static_assert((kU2Outputs & kU2Inputs) == 0, "U2 bit is both input and output");
static_assert((kU2Outputs | kU2Inputs) == 0xFFFF, "U2 bit unaccounted for");
static_assert((kU3Outputs & kU3Inputs) == 0, "U3 bit is both input and output");
static_assert((kU3Outputs | kU3Inputs) == 0xFFFF, "U3 bit unaccounted for");
static_assert((kU2SafeLatch & kU2Inputs) == 0, "U2 safe latch touches an input");
static_assert((kU3SafeLatch & kU3Inputs) == 0, "U3 safe latch touches an input");
static_assert((kU2PullEnable & kU2Outputs) == 0, "U2 pulls an output");
static_assert((kU3PullEnable & kU3Outputs) == 0, "U3 pulls an output");
static_assert((kU2IrqUnmasked & kU2Outputs) == 0, "U2 unmasks an output");
static_assert((kU3IrqUnmasked & kU3Outputs) == 0, "U3 unmasks an output");
// The one bit on this board that is routed, readable, and carries nothing.
static_assert((kU2IrqUnmasked & bitmask(AQROOT_U2_BQ25185_STAT2)) == 0,
              "BQ25185_STAT2 must stay masked -- U11.3 is unconnected (D-742)");
static_assert(AQROOT_CHARGER_STAT2_UNCONNECTED == 1,
              "this layer decodes STAT1 alone; re-derive it if STAT2 is landed");
static_assert((kU3IrqUnmasked &
               (bitmask(AQROOT_U3_XGPIO4) | bitmask(AQROOT_U3_XGPIO5))) == 0,
              "MX-9: a public XGPIO must not reach the shared wake line");
static_assert(AQROOT_NFC_ON_3V3 == 1, "NFC_5V_EN is only safe while U13 is DNP");

// ---------------------------------------------------------------------------
enum class Button : uint8_t { Up, Down, Left, Right, A, B };

// What STAT1 alone can prove on this revision.  SLUSF65B Table 6-2 collapsed
// onto one pin -- see AQROOT_DEMO_EXPANDER_DEPENDENCIES.md.
enum class ChargerState : uint8_t {
  Unknown,       // not read yet
  Fault,         // STAT1 LOW -- DIRECTLY OBSERVED.  Recoverable vs latched is
                 // NOT distinguishable without STAT2.
  NotFaulted,    // STAT1 HIGH -- AMBIGUOUS between charging, complete, sleep
                 // and charge-disabled.  Never report this as "charging".
};

class DemoExpanders {
 public:
  DemoExpanders()
      : u2_(AQROOT_EXP_U2_ADDR), u3_(AQROOT_EXP_U3_ADDR),
        u2_inputs_(0xFFFF), u3_inputs_(0xFFFF),
        u2_irq_(0), u3_irq_(0), ready_(false),
        fault_shutdown_seen_(false), fault_shutdown_ok_(false),
        fault_observability_lost_(false) {}

  // Probe both devices, drive both into their safe state, then take the first
  // input snapshot -- which also deasserts /INT on both, so WAKE_INT_N is
  // released before anything attaches an interrupt to it.
  bool begin(I2cBus &bus) {
    ready_ = false;

    const Pcal9535a::Config u2 = {kU2SafeLatch, kU2Inputs, kU2PullEnable,
                                  kU2PullUp, uint16_t(~kU2IrqUnmasked)};
    const Pcal9535a::Config u3 = {kU3SafeLatch, kU3Inputs, kU3PullEnable,
                                  kU3PullUp, uint16_t(~kU3IrqUnmasked)};

    // MCU-only reset does NOT reset either PCAL9535A.  Before probing, reading,
    // or reprogramming policy registers, overwrite BOTH complete output latches
    // with their board-safe words.  These two independent writes are attempted
    // unconditionally so one NACK cannot leave the other expander driving stale
    // enables from the previous firmware instance.
    const bool u2_safe = u2_.writeOutputs(bus, kU2SafeLatch);
    const bool u3_safe = u3_.writeOutputs(bus, kU3SafeLatch);
    // D-750.  THESE TWO DEVICES ARE INDEPENDENT AND `||` IS NOT.  The old line
    // short-circuited: if U2's configuration NACKed, U3 was never driven into
    // its safe state at all -- and U3 owns NFC_5V_EN, the SX1262 and CC1101
    // resets and both radio transmit enables, every one of which the PCAL9535A
    // leaves at a 00h latch that its fitted pull-down already holds.  A bus
    // fault on ONE device must not leave the OTHER unconfigured.  Both are
    // attempted, in order, and the verdict is taken afterwards.
    const bool u2_ok = u2_.apply(bus, u2);
    const bool u3_ok = u3_.apply(bus, u3);
    if (!u2_safe || !u3_safe || !u2_ok || !u3_ok) return false;

    // Read the direction back.  A PCAL9535A that NACKed a write mid-sequence
    // would otherwise leave half this board's control lines as inputs and every
    // later write would appear to succeed.
    uint16_t u2_dir = 0, u3_dir = 0;
    if (!u2_.readConfig(bus, &u2_dir) || !u3_.readConfig(bus, &u3_dir)) return false;
    if (u2_dir != kU2Inputs || u3_dir != kU3Inputs) return false;

    if (!u2_.readInputs(bus, &u2_inputs_)) return false;
    if (!u3_.readInputs(bus, &u3_inputs_)) return false;
    u2_irq_ = 0;
    u3_irq_ = 0;
    fault_observability_lost_ = false;
    ready_ = true;
    return true;
  }

  bool ready() const { return ready_; }

  // Service BOTH devices.  Call on every WAKE_INT_N assertion AND poll it --
  // the line is level sensitive and shared, so an edge-only handler misses a
  // second overlapping assertion.  Status is read before the input port
  // because the input read is what clears the condition.
  bool service(I2cBus &bus) {
    // D-750.  THE TWO DEVICES ARE SERVICED INDEPENDENTLY.  A `||` chain here
    // meant a U2 read error skipped U3 entirely, and U3 is the device whose
    // input port carries ACC_POWER_FAULT_N -- so the one bus error that
    // mattered most was also the one that stopped the fault from being seen.
    // Every read is attempted; the verdict is taken at the end; and the fault
    // response below runs on whatever WAS read.
    const bool a = u2_.readInterruptStatus(bus, &u2_irq_);
    const bool b = u3_.readInterruptStatus(bus, &u3_irq_);
    const bool c = u2_.readInputs(bus, &u2_inputs_);
    const bool d = u3_.readInputs(bus, &u3_inputs_);

    // D-765 / round-2 review: losing the U3 INPUT read is itself a loss of
    // safety observability, because ACC_POWER_FAULT_N lives there.  The old
    // code returned false but issued ZERO shutdown writes, so an accessory
    // rail could remain enabled indefinitely while the caller merely knew that
    // service() failed.  Fail closed: if the fault cannot be observed, attempt
    // both independent shutdown paths anyway and forbid re-enable until a
    // later successful U3 input read restores observability.
    if (!d) {
      fault_observability_lost_ = true;
      const bool off5 = setAccessory5v(bus, false);
      const bool off3 = setAccessory3v3(bus, false);
      fault_shutdown_ok_ = off5 && off3;
      fault_shutdown_seen_ = true;
      return false;
    }

    fault_observability_lost_ = false;

    // An observed accessory power fault follows the same fail-closed path.
    if (accessoryFault()) {
      const bool off5 = setAccessory5v(bus, false);
      const bool off3 = setAccessory3v3(bus, false);
      fault_shutdown_ok_ = off5 && off3;
      fault_shutdown_seen_ = true;
      return a && b && c && fault_shutdown_ok_;
    }
    return a && b && c;
  }

  // Did a fault shutdown ever run, and did every write in it succeed?  A
  // diagnostic that prints success without asking this is printing the absence
  // of information (D-750).
  bool faultShutdownSeen() const { return fault_shutdown_seen_; }
  bool faultShutdownOk() const { return fault_shutdown_ok_; }
  bool faultObservabilityLost() const { return fault_observability_lost_; }

  // ---- inputs ----------------------------------------------------------
  bool pressed(Button button) const {
    return !Pcal9535a::bitOf(u2_inputs_, buttonBit(button));  // active low
  }
  bool touchInterrupt() const {
    return !Pcal9535a::bitOf(u2_inputs_, AQROOT_U2_TOUCH_INT_N);
  }
  bool sdCardPresent() const {
    return !Pcal9535a::bitOf(u2_inputs_, AQROOT_U2_SD_CARD_DETECT_N);
  }
  bool loraIrq() const {
    return Pcal9535a::bitOf(u2_inputs_, AQROOT_U2_SX1262_DIO1);  // active high
  }
  bool accessoryPresent() const {
    return !Pcal9535a::bitOf(u3_inputs_, AQROOT_U3_ACC_DETECT_N);
  }
  bool accessoryFault() const {
    return !Pcal9535a::bitOf(u3_inputs_, AQROOT_U3_ACC_POWER_FAULT_N);
  }
  bool xgpio4() const { return Pcal9535a::bitOf(u3_inputs_, AQROOT_U3_XGPIO4); }
  bool xgpio5() const { return Pcal9535a::bitOf(u3_inputs_, AQROOT_U3_XGPIO5); }

  ChargerState charger() const {
    if (!ready_) return ChargerState::Unknown;
    return Pcal9535a::bitOf(u3_inputs_, AQROOT_U3_BQ25185_STAT1)
               ? ChargerState::NotFaulted
               : ChargerState::Fault;
  }

  uint16_t u2Inputs() const { return u2_inputs_; }
  uint16_t u3Inputs() const { return u3_inputs_; }
  uint16_t u2InterruptStatus() const { return u2_irq_; }
  uint16_t u3InterruptStatus() const { return u3_irq_; }

  // ---- outputs ---------------------------------------------------------
  bool setDisplayReset(I2cBus &bus, bool asserted) {
    return u2_.writeBit(bus, AQROOT_U2_DISP_RST_N, !asserted);   // active low
  }
  bool setTouchReset(I2cBus &bus, bool asserted) {
    return u2_.writeBit(bus, AQROOT_U2_TOUCH_RST_N, !asserted);  // active low
  }
  bool setLoraReset(I2cBus &bus, bool asserted) {
    return u2_.writeBit(bus, AQROOT_U2_SX1262_RST_N, !asserted); // active low
  }
  bool setLoraRxEnable(I2cBus &bus, bool on) {
    // TXEN is NOT ours: U8.7/U8.8 are driven by the SX1262's own DIO2.
    return u3_.writeBit(bus, AQROOT_U3_SX1262_RXEN, on);
  }
  bool setAmplifier(I2cBus &bus, bool on) {
    return u2_.writeBit(bus, AQROOT_U2_AMP_SD_MODE, on);
  }
  bool setRgb(I2cBus &bus, bool red, bool green, bool blue) {
    if (!u3_.outputShadowValid()) return false;
    uint16_t next = u3_.outputShadow() | kRgbMask;               // all dark
    if (red) next &= uint16_t(~bitmask(AQROOT_U3_FRONT_RGB_R_N));
    if (green) next &= uint16_t(~bitmask(AQROOT_U3_FRONT_RGB_G_N));
    if (blue) next &= uint16_t(~bitmask(AQROOT_U3_FRONT_RGB_B_N));
    return u3_.writeOutputs(bus, next);
  }

  // NFC_5V_EN exists on the board and must never be asserted while U13 is DNP.
  // It is exposed only as an explicit de-assert so no caller can reach the
  // enable by accident.
  bool holdNfcBoostOff(I2cBus &bus) {
    return u2_.writeBit(bus, AQROOT_U2_NFC_5V_EN, false);
  }

  // ---- accessory power tree -------------------------------------------
  //
  // ORDER IS THE SAFETY PROPERTY.  D-186 requires TWO independent series
  // disconnects on the 5 V accessory output: U21's boost enable and U22's load
  // switch.  Bringing them up boost-first and tearing them down switch-first
  // means the switch is never the thing holding back a live boost output, and
  // a fault at any point leaves at least one disconnect open.
  // TURNING ON IS ORDERED; TURNING OFF IS UNCONDITIONAL.  D-750.  Bringing the
  // rail up must stop at the first failure, because enabling the load switch
  // before the boost is a sequence error.  Bringing it DOWN must not: the load
  // switch and the boost enable are separate registers, a NACK on one says
  // nothing about the other, and a shutdown that gives up halfway leaves the
  // accessory rail live during exactly the fault it was called for.  Both
  // writes are attempted, still in the safe order, and the AND of them is the
  // verdict.
  bool setAccessory5v(I2cBus &bus, bool on) {
    if (on) {
      if (!ready_ || fault_observability_lost_ || accessoryFault()) return false;
      if (!u3_.writeBit(bus, AQROOT_U3_ACC_5V_BOOST_EN, true)) return false;
      return u3_.writeBit(bus, AQROOT_U3_ACC_5V_SW_EN, true);
    }
    // The SAFE ORDER is still switch-then-boost.  First request the switch
    // open, then clear BOTH switch and boost while the shadow is trustworthy.
    // A failed write now invalidates that shadow (D-766), so the fallback below
    // uses the absolute board-safe latch rather than another read/modify/write.
    const bool sw = u3_.writeBit(bus, AQROOT_U3_ACC_5V_SW_EN, false);
    const bool clear = u3_.clearBits(
        bus, uint16_t(bitmask(AQROOT_U3_ACC_5V_SW_EN) |
                      bitmask(AQROOT_U3_ACC_5V_BOOST_EN)));
    // D-766: a failed port-pair write invalidates the software shadow because
    // one byte may have reached the PCAL before the bus error.  Do not stop at
    // a now-impossible read/modify/write: make one absolute full-latch attempt
    // at the board-safe word.  It is intentionally broader than the requested
    // rail shutdown; after an uncertain bus transaction, safety outranks RGB or
    // radio-control state.  We still return false so the fault is not hidden.
    bool fallback = true;
    if (!sw || !clear) fallback = u3_.writeOutputs(bus, kU3SafeLatch);
    return sw && clear && fallback;
  }

  // U16's B-side supply IS ACC_3V3_SW, so the accessory I2C buffer can only be
  // enabled after the switched 3.3 V rail is up, and must be disabled before it
  // goes away.
  bool setAccessory3v3(I2cBus &bus, bool on) {
    if (on) {
      if (!ready_ || fault_observability_lost_ || accessoryFault()) return false;
      return u3_.writeBit(bus, AQROOT_U3_ACC_3V3_EN, true);
    }
    // Same rule as setAccessory5v, and here the two writes are on DIFFERENT
    // DEVICES: a U2 bus error must not leave U3's switched 3.3 V rail on.
    const bool buf = u2_.writeBit(bus, AQROOT_U2_ACC_PWR_EN, false);
    const bool rail = u3_.writeBit(bus, AQROOT_U3_ACC_3V3_EN, false);
    // Same byte-boundary ambiguity as the 5 V path, but across two devices.
    // Independently recover each expander to its absolute safe latch if its
    // requested write failed.  Never let a failure on U2 suppress the U3
    // shutdown attempt, or vice versa.
    bool u2_fallback = true, u3_fallback = true;
    if (!buf) u2_fallback = u2_.writeOutputs(bus, kU2SafeLatch);
    if (!rail) u3_fallback = u3_.writeOutputs(bus, kU3SafeLatch);
    return buf && rail && u2_fallback && u3_fallback;
  }

  bool setAccessoryI2cBuffer(I2cBus &bus, bool on) {
    if (!u3_.outputShadowValid()) return false;
    if (on && !Pcal9535a::bitOf(u3_.outputShadow(), AQROOT_U3_ACC_3V3_EN)) {
      return false;  // U16 is powered from ACC_3V3_SW; bring that up first
    }
    return u2_.writeBit(bus, AQROOT_U2_ACC_PWR_EN, on);
  }

  Pcal9535a &u2() { return u2_; }
  Pcal9535a &u3() { return u3_; }

 private:
  static uint8_t buttonBit(Button button) {
    switch (button) {
      case Button::Up: return AQROOT_U2_BTN_UP_N;
      case Button::Down: return AQROOT_U2_BTN_DOWN_N;
      case Button::Left: return AQROOT_U2_BTN_LEFT_N;
      case Button::Right: return AQROOT_U2_BTN_RIGHT_N;
      case Button::A: return AQROOT_U2_BTN_A_N;
      case Button::B: default: return AQROOT_U2_BTN_B_N;
    }
  }

  Pcal9535a u2_;
  Pcal9535a u3_;
  uint16_t u2_inputs_;
  uint16_t u3_inputs_;
  uint16_t u2_irq_;
  uint16_t u3_irq_;
  bool ready_;
  bool fault_shutdown_seen_;
  bool fault_shutdown_ok_;
  bool fault_observability_lost_;
};

}  // namespace aqroot
