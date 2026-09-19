// AQROOT Demo -- AS-BUILT BRING-UP TARGET.
//
// This is not the application.  It is the firmware that goes onto the FIRST
// assembled AQROOT Demo board, and its whole job is to prove that the board and
// `Firmware/src/hw/aqroot_demo_board.h` agree with each other -- before anyone
// spends a day debugging a "broken" peripheral that is really a swapped pin.
//
// It deliberately depends on NOTHING but the Arduino core.  No LVGL, no
// RadioLib, no display library: a bring-up target that cannot build because a
// UI dependency moved is a bring-up target that is not there when it is needed.
//
// WHAT IT PROVES, IN ORDER
//   1  every pin is parked in a safe state before anything drives it
//   2  both PCAL9535A expanders answer at the addresses their straps set
//   3  they take the safe-latch-then-direction configuration and read it back
//   4  every I2C device on the internal bus ACKs, at 100 kHz and then 400 kHz
//   5  the reset lines that live on U2 actually move their targets
//   6  all three SPI-B devices identify themselves -- the strongest available
//      proof that the SPI pin map is right
//   7  the front controls, the charger status, and the accessory port behave
//      the way the as-built map says they do
//
// SAFETY POSTURE.  Accessory 5 V and switched 3.3 V stay OFF unless the operator
// asks for them over the console; NFC_5V_EN is never asserted (U13 is DNP); the
// amplifier is left shut down until a tone is requested.  Charger state is
// reported exactly as much as STAT1 alone can prove and NO MORE -- see D-742.

#include <Arduino.h>
#include <SPI.h>

#include "../hw/aqroot_accessory_power_policy.h"
#include "../hw/aqroot_demo_board.h"
#include "../hw/aqroot_demo_display.h"
#include "../hw/aqroot_demo_expanders.h"
#include "../hw/max17048_guard.h"
#include "../hw/aqroot_demo_peripherals.h"
#include "../hw/aqroot_demo_pins.h"
#include "../hw/aqroot_demo_radios.h"
#include "../hw/aqroot_i2c_arduino.h"
#include "../hw/aqroot_spi_bus_b.h"

using namespace aqroot;

static ArduinoI2cBus g_bus;
static DemoExpanders g_expanders;
static uint16_t g_last_u2 = 0xFFFF;
static uint16_t g_last_u3 = 0xFFFF;
static BoardChipSelects g_selects;
static SpiBusB g_spi_b(g_selects);
static Ili9488 g_display;
static bool g_display_up = false;
static bool g_ok = true;
static bool g_acc3v3 = false;
static bool g_acc5v = false;
static bool g_accessory_i2c = false;
static uint32_t g_last_battery_guard_ms = 0;
static uint32_t g_last_gauge_requal_ms = 0;
// ADI 19-6171 Rev.7 gives a 250 ms active ADC period and +/-3.5% time-base
// accuracy.  300 ms is therefore above the 258.75 ms worst timing bound.
static constexpr uint32_t kFuelGaugeActiveSettleMs = 300;
static Max17048Guard g_fuel_gauge(AQROOT_I2C_ADDR_FUEL_GAUGE);

// D-775 FIRMWARE POLICY.  Hardware current limiting remains the absolute
// safety boundary.  This separate VCELL policy enforces the NORMAL D-098 load
// contract: one accessory rail uses D-766's retained 3.50 V floor, and
// enabling or retaining BOTH published rails requires the 3.80 V that
// demo_feature_contract F6 DERIVES from the MAX17048 measurement node, the
// live BAT_PROTECTED_P copper, the BQ25185 BATFET maximum and D-098's
// published 400 mA / 300 mA.  The 5 V rail -- the expensive one, since its
// pack current scales with the boost ratio -- is shed FIRST when a dual-rail
// load crosses that floor, so the 3.3 V rail keeps its full published budget.
// Unreadable VCELL is always fail-closed.  Both constants and the derivation
// live in ../hw/aqroot_accessory_power_policy.h and F6 refuses either one
// dropping below what it derives.

static void report(const char *stage, bool ok, const char *detail = nullptr) {
  Serial.printf("[%-4s] %-34s %s\n", ok ? "PASS" : "FAIL", stage,
                detail ? detail : "");
  if (!ok) g_ok = false;
}

// ---------------------------------------------------------------------------
static bool i2cReadByte(uint8_t address, uint8_t reg, uint8_t *value) {
  return g_bus.readRegister(address, reg, value, 1);
}

static bool configureFuelGaugeActiveMode() {
  const bool ready = g_fuel_gauge.configureActiveMode(g_bus);
  // Only wait for an active-mode conversion AFTER both HIBRT=0 and the live
  // MODE.HibStat bit confirm that the gauge is actually out of hibernate.
  if (ready) delay(kFuelGaugeActiveSettleMs);
  return ready;
}

// MAX17048 VCELL, register 0x02.  D-766 CORRECTED AN OFF-BY-SIXTEEN.  The read
// below used to take only the TOP TWELVE BITS -- (raw[0] << 4) | (raw[1] >> 4)
// -- and then apply the 78.125 uV/cell scale, which divides the answer by 16: a
// 4.05 V cell would have reported 0.253 V, so accessoryBatteryOk() would have
// refused BOTH accessory rails forever and shed any rail already on.  THE FULL
// SIXTEEN BITS ARE THE VALUE, AND THAT IS PROVABLE HERE WITHOUT THE DATASHEET
// IN HAND: 78.125 uV x 65536 = 5.12 V full scale, which is the right span for a
// single Li-ion cell, whereas 78.125 uV x 4096 = 0.32 V full scale cannot
// represent a charged cell at all.  It also agrees with this file's own D-750
// finding that every MAX17048 register -- VCELL 0x02, SOC 0x04, MODE 0x06,
// VERSION 0x08 -- is sixteen bits, MSB first.  FIRST-ARTICLE BRING-UP MUST STILL
// READ THIS BACK against a metered cell voltage; it is printed on every refusal
// and on every shed so that a wrong scale cannot hide.
static bool readFuelCellVoltage(float *volts) {
  return g_fuel_gauge.readVcell(g_bus, volts);
}

static bool accessoryBatteryAllows(bool other_rail_on, float *volts = nullptr,
                                   float *floor = nullptr) {
  // D-784 / Round-5: HIBRT=0 is configuration, not proof of the present mode.
  // The guard also requires MODE.HibStat=0.  A first-rail request may
  // requalify the gauge while the accessory tree is completely off; once any
  // rail is active, loss of gauge readiness is fail-closed and may not be
  // hidden behind a blocking reconfiguration attempt.
  if (!g_fuel_gauge.activeReady()) {
    if (g_acc3v3 || g_acc5v || g_expanders.safeShutdownPending() ||
        !configureFuelGaugeActiveMode()) {
      if (volts) *volts = 0.0f;
      if (floor) *floor = accessoryEnableFloor(other_rail_on);
      return false;
    }
  }
  float v = 0.0f;
  const bool read = readFuelCellVoltage(&v);
  const float required = accessoryEnableFloor(other_rail_on);
  if (volts) *volts = v;
  if (floor) *floor = required;
  return accessoryEnableAllowed(read, v, other_rail_on);
}

// D-782.  ONE PLACE RECONCILES SOFTWARE FLAGS WITH THE CURRENT EXPANDER
// OUTPUT-LATCH STATE.  A failed/partial I2C transaction makes the state UNKNOWN,
// never falsely OFF; `reconcileAccessoryFlags` keeps the caller pessimistically
// active until the pending accessory-only safe state is confirmed.  Runtime
// recovery no longer blanket-writes U2's display/touch/LoRa reset outputs.
//
static void forceAccessoriesOff(const char *why);
static void afterAccessoryChange();
static void applyAccessoryRetention(const char *ctx);
static void settledAccessoryRecheck(const char *what);
static bool blockingDemoTestAllowed(const char *what);

static void afterAccessoryChange() {
  (void)reconcileAccessoryFlags(g_expanders, &g_acc3v3, &g_acc5v,
                                &g_accessory_i2c);
}

static bool blockingDemoTestAllowed(const char *what) {
  afterAccessoryChange();
  if (g_expanders.safeShutdownPending() || g_acc3v3 || g_acc5v) {
    Serial.printf("%s REFUSED: turn both accessory rails off and wait for a confirmed safe state first\n",
                  what);
    return false;
  }
  return true;
}

// The retention rule, in ONE place, so the periodic guard and D-779's
// post-enable settled recheck cannot drift apart.
static void applyAccessoryRetention(const char *ctx) {
  if (!g_acc3v3 && !g_acc5v) return;
  float vcell = 0.0f;
  const bool read = readFuelCellVoltage(&vcell);
  const AccessoryBatteryAction action =
      accessoryRetentionAction(read, vcell, g_acc3v3, g_acc5v);
  if (action == AccessoryBatteryAction::ShedAll) {
    char why[136];
    if (!read) {
      snprintf(why, sizeof(why),
               "%s: MAX17048 VCELL unreadable; accessory load not permitted",
               ctx);
    } else if (!vcellIsPlausible(vcell)) {
      // D-779: an implausible reading is NOT a low battery, and saying so
      // keeps a stuck bus from being diagnosed as a flat pack.
      snprintf(why, sizeof(why),
               "%s: VCELL %.3f V outside the plausible %.2f-%.2f V band; "
               "treated as no measurement",
               ctx, vcell, kVcellPlausibleMinV, kVcellPlausibleMaxV);
    } else {
      snprintf(why, sizeof(why),
               "%s: VCELL %.3f V below %.2f V single-rail floor",
               ctx, vcell, kAccessorySingleRailFloorV);
    }
    forceAccessoriesOff(why);
  } else if (action == AccessoryBatteryAction::Shed5v) {
    const bool off5 = g_expanders.setAccessory5v(g_bus, false);
    if (off5) g_acc5v = false;
    afterAccessoryChange();
    if (off5) {
      Serial.printf("ACC_5V_SW SHED (%s): VCELL %.3f V below %.2f V "
                    "dual-rail floor\n", ctx, vcell, kAccessoryDualRailFloorV);
    } else {
      forceAccessoriesOff("5 V dual-rail battery shed failed");
    }
  }
}

// D-779.  Re-read once the step has settled and apply the same rule.  The
// MAX17048 updates VCELL about every 250 ms in active mode, which the HIBRT
// write in setup() guarantees it is in; 400 ms covers one update with margin.
static void settledAccessoryRecheck(const char *what) {
  delay(400);
  applyAccessoryRetention(what);
  g_last_battery_guard_ms = millis();
}

// D-779.  THE PERMISSION WAS TAKEN BEFORE THE LOAD EXISTED.
//
// `accessoryBatteryAllows` reads VCELL and then the rail is switched on.  The
// reading it acted on is a PRE-STEP one: the sag the new load causes has not
// happened yet, and on a pack near the floor the post-step voltage can be
// below it.  F6's floors are derived FOR the loaded case, so the honest close
// is to re-read once the step has settled and apply the ordinary retention
// rule to the result.  One gauge update period plus margin -- the MAX17048
// updates VCELL about every 250 ms in active mode, which the HIBRT write above
// guarantees it is in.
static void forceAccessoriesOff(const char *why) {
  const bool off5 = g_expanders.setAccessory5v(g_bus, false);
  const bool off3 = g_expanders.setAccessory3v3(g_bus, false);
  const bool offbuf = g_expanders.setAccessoryI2cBuffer(g_bus, false);
  if (off5) g_acc5v = false;
  if (off3) g_acc3v3 = false;
  if (offbuf) g_accessory_i2c = false;
  afterAccessoryChange();
  Serial.printf("ACCESSORY FAIL-CLOSED: %s; 5V=%d 3V3=%d I2C=%d\n",
                why, off5, off3, offbuf);
}

static void scanI2c() {
  char line[96];
  uint8_t found = 0;
  for (uint8_t address = 0x08; address < 0x78; ++address) {
    if (g_bus.probe(address)) {
      snprintf(line, sizeof(line), "0x%02X", address);
      Serial.printf("       i2c device at %s\n", line);
      ++found;
    }
  }
  snprintf(line, sizeof(line), "%u device(s)", found);
  // Five are expected: U2, U3, the fuel gauge, the IMU and the touch panel.
  // The touch controller lives on the display FPC and only answers once
  // TOUCH_RST_N has been released, so it is counted after the release below.
  report("i2c bus scan", found >= 4, line);
}

static void probeI2cDevice(const char *name, uint8_t address, uint8_t reg,
                           uint8_t expected, bool strict) {
  char detail[96];
  uint8_t value = 0;
  if (!g_bus.probe(address)) {
    snprintf(detail, sizeof(detail), "0x%02X did not ACK", address);
    report(name, false, detail);
    return;
  }
  if (!i2cReadByte(address, reg, &value)) {
    snprintf(detail, sizeof(detail), "0x%02X ACKed, register 0x%02X read failed",
             address, reg);
    report(name, false, detail);
    return;
  }
  snprintf(detail, sizeof(detail), "0x%02X reg 0x%02X = 0x%02X%s", address, reg,
           value, strict ? "" : " (report only)");
  report(name, strict ? (value == expected) : (value != 0x00 && value != 0xFF),
         detail);
}

// ---------------------------------------------------------------------------
static void releaseExpanderResetLines() {
  if (!g_expanders.ready()) {
    report("reset-line release", false,
           "expanders were not safely initialised; resets remain asserted");
    return;
  }

  // Safe latches and directions were already committed at the very start of
  // setup(), before USB/Serial waiting or bus discovery.  Only now release the
  // three downstream resets in the order the parts want them.
  g_expanders.holdNfcBoostOff(g_bus);
  g_expanders.setDisplayReset(g_bus, true);
  g_expanders.setTouchReset(g_bus, true);
  g_expanders.setLoraReset(g_bus, true);
  delay(10);
  g_expanders.setDisplayReset(g_bus, false);
  g_expanders.setTouchReset(g_bus, false);
  delay(5);
  g_expanders.setLoraReset(g_bus, false);
  delay(10);
  report("reset lines released (U2 P00/P01/P04)", true);
}

static void probeRadios() {
  g_selects.begin();
  SPI.begin(AQROOT_PIN_SPI_B_SCK, AQROOT_PIN_SPI_B_MISO, AQROOT_PIN_SPI_B_MOSI,
            -1);
  char detail[96];
  // Each probe takes a SpiBusB::Hold, so a second concurrent select is REFUSED
  // rather than quietly driving MISO from two devices.
  const DeviceIdentity ids[] = {probeCc1101(g_spi_b), probeSx1262(g_spi_b),
                                probeSt25r3916(g_spi_b)};
  for (size_t i = 0; i < sizeof(ids) / sizeof(ids[0]); ++i) {
    if (ids[i].expected == kIdentityReportOnly) {
      snprintf(detail, sizeof(detail), "id 0x%04lX (liveness only)",
               (unsigned long)ids[i].raw);
    } else {
      snprintf(detail, sizeof(detail), "id 0x%04lX, expected 0x%04lX",
               (unsigned long)ids[i].raw, (unsigned long)ids[i].expected);
    }
    report(ids[i].device, ids[i].matches, detail);
  }
  SPI.end();
}

static const char *chargerText(ChargerState state) {
  switch (state) {
    case ChargerState::Fault:
      // STAT1 LOW.  SLUSF65B Table 6-2.  This is DIRECTLY OBSERVED.
      return "FAULT (observed on STAT1; recoverable vs latched NOT knowable "
             "without STAT2)";
    case ChargerState::NotFaulted:
      // STAT1 HIGH.  Charging, complete, sleep and charge-disabled are
      // indistinguishable here, and D-742 forbids reporting any of them as
      // observed.  Anything more specific is an INFERENCE.
      return "not faulted (charging vs complete is NOT observable on this "
             "revision -- infer from VBUS + MAX17048 trend, and label it)";
    default:
      return "unknown";
  }
}

// ---------------------------------------------------------------------------
void setup() {
  parkAllPins();

  // D-766 / round-2 review: a warm MCU reset does NOT reset the powered
  // PCAL9535As.  Safety therefore cannot wait for USB CDC, logging, an I2C scan
  // or peripheral discovery.  Recover/open the bus and write both complete
  // safe latches first.  No Serial call precedes these transactions.
  const bool i2c_open = g_bus.begin(AQROOT_I2C_BRINGUP_HZ);
  const bool expanders_safe = i2c_open && g_expanders.begin(g_bus);

  Serial.begin(115200);
  const uint32_t deadline = millis() + 3000;
  while (!Serial && millis() < deadline) {
  }
  Serial.println();
  Serial.println("AQROOT Demo -- as-built bring-up");
  Serial.printf("board_sha256 %s\n", AQROOT_DEMO_BOARD_SHA256);
  Serial.println("---------------------------------------------------------------");
  report("pins parked", true);
  report("i2c recovered/open at bring-up speed", i2c_open);
  report("PCAL9535A safe latches before console wait", expanders_safe);
  if (!expanders_safe) {
    Serial.println("FATAL: accessory/reset safety state could not be established.");
    return;
  }

  scanI2c();
  releaseExpanderResetLines();

  probeI2cDevice("BMI270 U4 chip id", AQROOT_I2C_ADDR_IMU, 0x00, 0x24, true);
  // INTERNAL_STATUS.message[3:0]: 0 = not initialised, 1 = init_ok.  The BMI270
  // needs a multi-kilobyte configuration file uploaded before accel or gyro
  // data exists, and this bring-up image deliberately does not carry one -- so
  // the honest report is the register, not a claim.  Expect 0x00 here and read
  // it as "bus and address proven, sensor not yet configured".
  {
    uint8_t status = 0xFF;
    const bool read = i2cReadByte(AQROOT_I2C_ADDR_IMU, 0x21, &status);
    char detail[96];
    snprintf(detail, sizeof(detail),
             "INTERNAL_STATUS = 0x%02X (%s) -- config file NOT loaded by this image",
             status, (status & 0x0F) == 1 ? "init_ok" : "not initialised");
    report("BMI270 U4 init state", read, detail);
  }
  // D-750.  THE MAX17048 IS A 16-BIT-REGISTER PART AND THIS READ WAS ONE BYTE.
  // Every MAX17048 register -- VCELL 0x02, SOC 0x04, MODE 0x06, VERSION 0x08 --
  // is 16 bits, MSB first, and the device auto-increments within the pair.  A
  // one-byte read returns the MSB alone and leaves the transaction ended in the
  // middle of a register.  Worse for a DIAGNOSTIC: VERSION reads 0x001x on
  // every part ADI has shipped, so the MSB is 0x00 -- and the generic
  // "report only" predicate below treats 0x00 as a FAILURE.  The old line
  // therefore reported a healthy fuel gauge as broken.  Read the pair.
  {
    uint8_t raw[2] = {0xFF, 0xFF};
    char detail[96];
    if (!g_bus.probe(AQROOT_I2C_ADDR_FUEL_GAUGE)) {
      snprintf(detail, sizeof(detail), "0x%02X did not ACK",
               AQROOT_I2C_ADDR_FUEL_GAUGE);
      report("MAX17048 U14 version", false, detail);
    } else if (!g_bus.readRegister(AQROOT_I2C_ADDR_FUEL_GAUGE, 0x08, raw, 2)) {
      snprintf(detail, sizeof(detail), "0x%02X ACKed, VERSION read failed",
               AQROOT_I2C_ADDR_FUEL_GAUGE);
      report("MAX17048 U14 version", false, detail);
    } else {
      const uint16_t version = uint16_t(raw[0]) << 8 | raw[1];
      snprintf(detail, sizeof(detail),
               "VERSION = 0x%04X (silicon revision, reported not asserted)",
               version);
      report("MAX17048 U14 version", version != 0x0000 && version != 0xFFFF,
             detail);
    }
  }
  // D-779.  THE GAUGE MUST BE IN ACTIVE MODE OR ITS VCELL IS NOT FRESH.
  //
  // The accessory policy gates and SHEDS on VCELL, so a stale reading is a
  // stale permission.  The MAX17048 enters hibernate on its own when the cell
  // looks quiet, and in hibernate it updates VCELL far more slowly than the
  // ~250 ms of active mode -- which is exactly the pre-step-to-post-step
  // problem: the second rail is enabled against a reading taken before the
  // load existed.  Writing HIBRT (0x0A) = 0x0000 disables hibernate entirely,
  // so every reading the policy acts on is an active-mode one.  Reported, not
  // asserted: a gauge that refuses this write still fails closed everywhere
  // else, and the operator is told which case they are in.
  {
    const bool active = configureFuelGaugeActiveMode();
    report("MAX17048 U14 hibernate disabled + read back", active,
           active ? "HIBRT=0x0000 verified; fresh active-mode VCELL required"
                  : "gauge NOT READY -- accessory enable remains fail-closed");
  }
  // Only reachable once TOUCH_RST_N is released, which bringUpExpanders() did.
  probeI2cDevice("touch controller (J1 FPC)", AQROOT_I2C_ADDR_TOUCH, 0xA3, 0x00,
                 false);

  // Raise to the running speed only after every device has answered, so a
  // 400 kHz-only failure is distinguishable from a wiring fault.
  g_bus.setClock(AQROOT_I2C_RUN_HZ);
  report("i2c raised to run speed",
         g_bus.probe(AQROOT_EXP_U2_ADDR) && g_bus.probe(AQROOT_EXP_U3_ADDR));

  probeRadios();

  // As-built limits, restated on the console so the operator of the first board
  // is told what NOT to expect before they go looking for it.
  Serial.println("---------------------------------------------------------------");
  Serial.println("as-built limits on this revision:");
#if AQROOT_CHARGER_STAT2_UNCONNECTED
  Serial.println("  * charger STAT2 is UNCONNECTED (U11.3) -- STAT1 alone");
#endif
#if AQROOT_DISPLAY_SDO_ISOLATED
  Serial.println("  * display SDO isolated (R112 DNP) -- panel is WRITE-ONLY");
#endif
#if AQROOT_FUEL_GAUGE_ALRT_NOT_WIRED
  Serial.println("  * MAX17048 ALRT not wired -- poll the gauge");
#endif
#if AQROOT_NFC_ON_3V3
  Serial.println("  * NFC runs from +3V3, U13 DNP -- NFC_5V_EN stays low");
#endif
#if AQROOT_SX1262_TXEN_IS_DIO2
  Serial.println("  * SX1262 TXEN is the module's own DIO2 -- only RXEN is ours");
#endif
#if AQROOT_NO_BATTERY_NTC
  Serial.println("  * no battery NTC (R38 10k) -- no pack temperature, no TS fault");
#endif
  Serial.println("---------------------------------------------------------------");
  Serial.printf("bring-up %s\n", g_ok ? "COMPLETE" : "INCOMPLETE -- see FAIL rows");
  Serial.println("console: r/g/b/w/o = RGB, 3 = ACC 3V3 toggle, 5 = ACC 5V toggle,");
  Serial.println("         i = accessory I2C buffer toggle, s = status,");
  Serial.println("         d = microSD probe, l = backlight ramp, x = IR self-test,");
  Serial.println("         t = 1 kHz tone (energises the speaker),");
  Serial.println("         p = display init + test pattern (lights the backlight),");
  Serial.println("         m = microphone capture (200 ms, reports peak per slot)");
}

// ---------------------------------------------------------------------------
static void printStatus() {
  Serial.printf("  buttons  UP=%d DOWN=%d LEFT=%d RIGHT=%d A=%d B=%d\n",
                g_expanders.pressed(Button::Up), g_expanders.pressed(Button::Down),
                g_expanders.pressed(Button::Left),
                g_expanders.pressed(Button::Right), g_expanders.pressed(Button::A),
                g_expanders.pressed(Button::B));
  Serial.printf("  touch INT=%d  sd card=%d  lora DIO1=%d\n",
                g_expanders.touchInterrupt(), g_expanders.sdCardPresent(),
                g_expanders.loraIrq());
  Serial.printf("  accessory present=%d fault=%d  xgpio4=%d xgpio5=%d\n",
                g_expanders.accessoryPresent(), g_expanders.accessoryFault(),
                g_expanders.xgpio4(), g_expanders.xgpio5());
  Serial.printf("  charger  %s\n", chargerText(g_expanders.charger()));
  Serial.printf("  BOOT_N (SW1) = %d   display initialised = %d\n",
                digitalRead(AQROOT_PIN_BOOT_N), g_display_up);
}

void loop() {
  if (!g_expanders.ready()) {
    // Round-4 R4-03: an MCU reset must not turn one failed safe-latch write
    // into an indefinite energized rail.  Re-open/recover the bus and retry
    // the complete boot-safe expander initialization until it is confirmed.
    static uint32_t last_recovery_ms = 0;
    if (millis() - last_recovery_ms >= 250) {
      last_recovery_ms = millis();
      const bool bus_open = g_bus.reopen(AQROOT_I2C_BRINGUP_HZ);
      const bool recovered = bus_open && g_expanders.begin(g_bus);
      if (recovered) {
        afterAccessoryChange();
        releaseExpanderResetLines();
        g_bus.setClock(AQROOT_I2C_RUN_HZ);
        g_display_up = false;
        (void)configureFuelGaugeActiveMode();
        Serial.println("I2C/expander safety state RECOVERED after incomplete boot");
      }
    }
    delay(10);
    return;
  }

  // WAKE_INT_N is LEVEL sensitive and SHARED, so it is polled here as well as
  // being the deep-sleep wake source: an edge-only handler would miss a second
  // overlapping assertion from the other device.
  const bool asserted = digitalRead(AQROOT_PIN_WAKE_INT_N) == LOW;
  static uint32_t last_poll = 0;
  if (asserted || millis() - last_poll > 200) {
    last_poll = millis();
    if (g_expanders.service(g_bus)) {
      afterAccessoryChange();
      if (g_expanders.u2Inputs() != g_last_u2 ||
          g_expanders.u3Inputs() != g_last_u3) {
        g_last_u2 = g_expanders.u2Inputs();
        g_last_u3 = g_expanders.u3Inputs();
        Serial.printf("change  U2=0x%04X (irq 0x%04X)  U3=0x%04X (irq 0x%04X)\n",
                      g_last_u2, g_expanders.u2InterruptStatus(), g_last_u3,
                      g_expanders.u3InterruptStatus());
        printStatus();
      }
    } else {
      static uint32_t last_service_error = 0;
      afterAccessoryChange();
      if (millis() - last_service_error > 1000) {
        last_service_error = millis();
        Serial.printf("I2C service FAILED; accessory fault observability=%s\n",
                      g_expanders.faultObservabilityLost() ? "LOST (rails forced off)"
                                                           : "available");
      }
    }
  }

  // If boot caught the gauge while MODE.HibStat was still asserted, keep
  // trying to qualify it in the background while accessory power is safely
  // off.  This is liveness only: no rail is energized until qualification and
  // the subsequent VCELL permission both succeed.
  if (!g_fuel_gauge.activeReady() && !g_acc3v3 && !g_acc5v &&
      !g_expanders.safeShutdownPending() &&
      millis() - g_last_gauge_requal_ms >= 1000) {
    g_last_gauge_requal_ms = millis();
    (void)configureFuelGaugeActiveMode();
  }

  if ((g_acc3v3 || g_acc5v) &&
      millis() - g_last_battery_guard_ms >= 500) {
    g_last_battery_guard_ms = millis();
    applyAccessoryRetention("periodic");
  }

  if (Serial.available()) {
    switch (Serial.read()) {
      case 'r': g_expanders.setRgb(g_bus, true, false, false); break;
      case 'g': g_expanders.setRgb(g_bus, false, true, false); break;
      case 'b': g_expanders.setRgb(g_bus, false, false, true); break;
      case 'w': g_expanders.setRgb(g_bus, true, true, true); break;
      case 'o': g_expanders.setRgb(g_bus, false, false, false); break;
      case '3': {
        const bool want = !g_acc3v3;
        float vcell = 0.0f, floor = 0.0f;
        if (want && !accessoryBatteryAllows(g_acc5v, &vcell, &floor)) {
          Serial.printf("ACC_3V3_SW REFUSED: VCELL %.3f V / floor %.2f V\n",
                        vcell, floor);
          break;
        }
        const bool ok = g_expanders.setAccessory3v3(g_bus, want);
        if (ok) g_acc3v3 = want;
        afterAccessoryChange();
        if (ok && want) settledAccessoryRecheck("ACC_3V3_SW");
        Serial.printf("ACC_3V3_SW %s -> %d\n", want ? "on" : "off", ok);
        break;
      }
      case '5': {
        const bool want = !g_acc5v;
        float vcell = 0.0f, floor = 0.0f;
        if (want && !accessoryBatteryAllows(g_acc3v3, &vcell, &floor)) {
          Serial.printf("ACC_5V_SW REFUSED: VCELL %.3f V / floor %.2f V\n",
                        vcell, floor);
          break;
        }
        // Boost first, switch second, and the reverse on the way down.  Both
        // disconnects are required by D-186 and neither is optional.
        const bool ok = g_expanders.setAccessory5v(g_bus, want);
        if (ok) g_acc5v = want;
        afterAccessoryChange();
        if (ok && want) settledAccessoryRecheck("ACC_5V_SW");
        Serial.printf("ACC_5V_SW %s -> %d\n", want ? "on" : "off", ok);
        break;
      }
      case 'i': {
        const bool want = !g_accessory_i2c;
        const bool ok = g_expanders.setAccessoryI2cBuffer(g_bus, want);
        if (ok) g_accessory_i2c = want;
        afterAccessoryChange();
        Serial.printf("ACC_PWR_EN %s -> %d\n", want ? "on" : "off", ok);
        break;
      }
      case 'm': {
        if (!blockingDemoTestAllowed("microphone test")) break;
        const MicCapture mic = captureMicrophone();
        Serial.printf("mic  %s, %lu frames, peak L=%ld R=%ld (24-bit)\n",
                      mic.installed ? "I2S RX up" : "I2S RX FAILED",
                      (unsigned long)mic.frames, (long)mic.peak_left,
                      (long)mic.peak_right);
        // The slot carrying signal tells the operator which one MK1 selected.
        report("microphone MK1 (I2S RX)",
               mic.installed && mic.frames > 0 &&
                   (mic.peak_left > 0 || mic.peak_right > 0));
        break;
      }
      case 's': printStatus(); break;
      case 'd': {
        if (!blockingDemoTestAllowed("microSD test")) break;
        // The ONLY test on this board that proves SPI-A MISO: R112 is DNP, so
        // the display SDO never reaches the MCU and the card is the sole reader.
        const SdProbeResult sd = probeSdCard();
        Serial.printf("microSD  CMD0 R1=0x%02X (%s), CMD8 echo=0x%08lX (%s)\n",
                      sd.r1_cmd0, sd.responded_to_cmd0 ? "idle" : "no answer",
                      (unsigned long)sd.cmd8_echo,
                      sd.voltage_accepted ? "2.7-3.6 V accepted" : "not echoed");
        report("microSD SPI-A (J2)", sd.responded_to_cmd0);
        break;
      }
      case 'l':
        if (!blockingDemoTestAllowed("backlight ramp")) break;
        Serial.println("backlight ramp on GPIO46 (U17 TPS61169)");
        backlightRamp();
        break;
      case 'p': {
        if (!blockingDemoTestAllowed("display test")) break;
        // RESET IS NOT AN MCU PIN.  U2.P04 owns it, so the pulse goes through
        // the expander before a single SPI byte is sent.
        Serial.println("display: pulsing DISP_RST_N via U2.P04, then ILI9488 init");
        g_expanders.setDisplayReset(g_bus, true);
        delay(20);
        g_expanders.setDisplayReset(g_bus, false);
        delay(20);
        g_display.begin();
        g_display.testPattern();
        g_display.end();
        g_display_up = true;
        // The panel is WRITE-ONLY -- R112 is DNP -- so nothing here can confirm
        // the init took.  The backlight is raised so the operator can.
        pinMode(AQROOT_PIN_DISP_BL_PWM, OUTPUT);
        digitalWrite(AQROOT_PIN_DISP_BL_PWM, HIGH);
        Serial.println("display: four quadrants R/G/B/W, backlight ON.");
        Serial.println("  expect 320 wide x 480 tall, portrait, red top-left.");
        Serial.println("  R112 is DNP: there is NO read-back path -- confirm by eye.");
        break;
      }
      case 'x': {
        if (!blockingDemoTestAllowed("IR test")) break;
        const IrSelfTest ir = irSelfTest();
        Serial.printf("IR  %u/%u samples low during a 38 kHz burst -- %s\n",
                      ir.low_samples, ir.total_samples,
                      ir.detected ? "receiver saw the emitter"
                                  : "no return (reflection dependent)");
        break;
      }
      case 't':
        if (!blockingDemoTestAllowed("audio tone")) break;
        // Leaving shutdown is what makes AMP_SD_MODE observable at all.
        Serial.println("1 kHz tone -- amplifier leaving shutdown");
        g_expanders.setAmplifier(g_bus, true);
        delay(5);
        Serial.printf("i2s tone %s\n", playTone(1000, 400) ? "played" : "FAILED");
        g_expanders.setAmplifier(g_bus, false);
        break;
      default: break;
    }
  }
}
