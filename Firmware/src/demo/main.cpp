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
#include "../hw/aqroot_demo_bringup_app.h"
#include "../hw/aqroot_demo_display.h"
#include "../hw/aqroot_demo_expanders.h"
#include "../hw/aqroot_demo_gauge_bringup.h"
#include "../hw/max17048_guard.h"
#include "../hw/aqroot_demo_timing_policy.h"
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
static bool g_ok = true;
static Max17048Guard g_fuel_gauge(AQROOT_I2C_ADDR_FUEL_GAUGE);

// D-789 / D788-04 + D788-05 + D788-06.  EVERY SAFETY-RELEVANT CALL SITE THIS
// FILE USED TO OWN NOW LIVES IN `../hw/aqroot_demo_bringup_app.h`.
//
// Round-8 reproduced three false greens that were all the same defect: the
// FUNCTIONS D-788 made executable were covered, and the CALLERS of them, which
// lived here, were compiled by no host test at all.  An early return in this
// file's own `configureFuelGaugeActiveMode()`, a duplicate backlight ramp in
// the serial dispatch, and a warm-reset retry with `begin()` removed each
// passed the complete H1-H8 suite.
//
// `Firmware/test/test_production_callers.cpp` constructs `DemoBringupApp` over
// a recording bus with a PHYSICAL-LATCH expander model and drives the real
// methods, and `checks/firmware_hw_map_contract.py` mutates them.  THIS FILE
// MAY NOT REIMPLEMENT ANY OF THEM; `H8_production_callers` refuses a
// `demo/main.cpp` that reaches those behaviours any other way.
//
// D-791 FIRMWARE POLICY, enforced inside the app: hardware current limiting
// remains the absolute safety boundary, and this separate VCELL policy
// enforces the NORMAL D-098 load contract.  D-790's 3.50/3.85 V floors were
// node voltages the node never reaches under the published load (D790-A03);
// `demo_feature_contract` F12 now DERIVES three -- a retention floor at the
// BQ25185's own VBUVLO bound plus the MAX17048's positive voltage error, and
// two ENABLE floors that each add the node step the rail being switched on
// will cause.  The 5 V rail sheds FIRST and the 3.3 V rail keeps its full
// published 400 mA.  Unreadable VCELL is always fail-closed.
static void consoleLog(const char *line) { Serial.println(line); }

using DemoApp = DemoBringupApp<ArduinoI2cBus, void (*)(const char *)>;
static DemoApp g_app(g_bus, g_expanders, g_fuel_gauge, &consoleLog);

static void report(const char *stage, bool ok, const char *detail = nullptr) {
  Serial.printf("[%-4s] %-34s %s\n", ok ? "PASS" : "FAIL", stage,
                detail ? detail : "");
  if (!ok) g_ok = false;
}

// ---------------------------------------------------------------------------
static bool i2cReadByte(uint8_t address, uint8_t reg, uint8_t *value) {
  return g_bus.readRegister(address, reg, value, 1);
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
// D-789 / D788-06.  THE DIAGNOSTIC ITSELF LIVES IN `DemoBringupApp` SO THAT A
// HOST TEST EXECUTES IT.  This wrapper does nothing but turn the app's verdict
// into a console `report` row; it may not re-derive the verdict.
static void releaseExpanderResetLines() {
  const ResetReleaseReport r = g_app.releaseExpanderResetLines();
  char detail[128];
  switch (r.verdict) {
    case ResetRelease::Confirmed:
      snprintf(detail, sizeof(detail),
               "CONFIRMED from U2 output latch 0x%04X", r.latch);
      break;
    case ResetRelease::Unknown:
      snprintf(detail, sizeof(detail),
               "UNKNOWN: a reset write failed and U2's output shadow is "
               "invalid; resets may still be asserted");
      break;
    default:
      if (!g_expanders.ready()) {
        snprintf(detail, sizeof(detail),
                 "expanders were not safely initialised; resets remain "
                 "asserted");
      } else {
        snprintf(detail, sizeof(detail),
                 "FAILED: U2 output latch 0x%04X does not show all three "
                 "released", r.latch);
      }
      break;
  }
  report("reset lines released (U2 P00/P01/P04)", r.ok(), detail);
}

// D-793 / R12-03.  BEFORE ANYTHING IS PERMITTED, THE RADIOS ARE QUIESCED.
//
// U7 and U8 stay powered across an MCU reset, so a transmit this image did not
// start may still be running.  `DemoBringupApp` treats the state as KEYED
// until this returns a CONFIRMED quiesce, which refuses accessory power and
// refuses keying a second transmitter -- the pessimistic direction, for the
// same reason D-783 made the expander latch pessimistic.
static bool bringUpSpiBAndQuiesceRadios() {
  g_selects.begin();
  SPI.begin(AQROOT_PIN_SPI_B_SCK, AQROOT_PIN_SPI_B_MISO, AQROOT_PIN_SPI_B_MOSI,
            -1);
  const RadioQuiesce q = quiesceRadios(g_spi_b);
  g_app.noteRadiosQuiesced(q.cc1101_confirmed && q.sx1262_confirmed);
  // D-794 / R13-03: the NFC front end is quiesced and verified on the same
  // path, and its verdict is reported separately because it gates a
  // different set of permissions -- the burst slot as well as the rails.
  g_app.noteNfcFieldQuiesced(q.nfc_confirmed, q.nfc_operation_control,
                             nfcQuiesceStepName(q.nfc.failed_at));
  char detail[232];
  snprintf(detail, sizeof(detail),
           "CC1101 MARCSTATE=0x%02X (%s), SX1262 status=0x%02X (%s), "
           "ST25R3916 Operation control=0x%02X (%s)",
           q.cc1101_marcstate, q.cc1101_confirmed ? "IDLE" : "NOT IDLE",
           q.sx1262_status, q.sx1262_confirmed ? "STANDBY" : "NOT STANDBY",
           q.nfc_operation_control,
           q.nfc_confirmed ? "FIELD OFF, live identity 0x28..0x2F proved"
                           : "FIELD STATE UNKNOWN");
  report("radios quiesced after MCU reset (U7 SRES/SIDLE, U8 SetStandby, "
         "U9 Set default)", q.ok(), detail);
  return q.ok();
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
  // D-795 / R14-02: a failed identity after an OFF confirmation revokes it.
  g_app.noteNfcLiveness(ids[2].matches, uint8_t(ids[2].raw));
  SPI.end();
}

// D-795 / R14-02.  A CONFIRMED-QUIET ST25R3916 KEEPS PROVING IT IS ALIVE.
static void serviceNfcLiveness() {
  if (!g_app.nfcLivenessDue()) return;
  g_selects.begin();
  SPI.begin(AQROOT_PIN_SPI_B_SCK, AQROOT_PIN_SPI_B_MISO, AQROOT_PIN_SPI_B_MOSI,
            -1);
  uint8_t identity = 0x00;
  const bool alive = st25r3916StillAlive(g_spi_b, &identity);
  SPI.end();
  g_app.noteNfcLiveness(alive, identity);
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

// D-791 / D790-A07.  THE PANEL INITIALISATION, IN ONE PLACE, SO A DEFERRED
// RESET RELEASE REACHES IT TOO.
//
// Round-10: `display_up_` used to survive a later DISP_RST_N pulse, so a
// release that only landed on a `loop()` retry put the console line back to
// "display initialised = 1" with no SPI init behind it and a panel sitting in
// its power-on state.  `DemoBringupApp::releaseDisplayResetIntent()` now takes
// the panel DOWN the moment it asserts the reset, and `displayInitOwed()` is
// true exactly while a confirmed release has no initialisation behind it.
// This function is the only thing in the image that calls
// `noteDisplayInitialised(true)`, and both the console key and the loop's
// deferred completion go through it.
static void runDisplayInitialisation() {
  g_display.begin();
  g_display.testPattern();
  g_display.end();
  // The panel is WRITE-ONLY -- R112 is DNP -- so nothing here can confirm
  // the init took.  The backlight is raised so the operator can.
  pinMode(AQROOT_PIN_DISP_BL_PWM, OUTPUT);
  digitalWrite(AQROOT_PIN_DISP_BL_PWM, HIGH);
  // D-795 / R14-01: stamped AFTER the backlight is raised, because the epoch
  // is measured from the moment the new load is established and the
  // backlight is most of it.
  g_app.noteDisplayInitialised(true);
  Serial.println("display: four quadrants R/G/B/W, backlight ON.");
  Serial.println("  expect 320 wide x 480 tall, portrait, red top-left.");
  Serial.println("  R112 is DNP: there is NO read-back path -- confirm by eye.");
}

// ---------------------------------------------------------------------------
void setup() {
  parkAllPins();

  // D-792 / R11-04.  THE SPI-B TRANSMIT GATE IS WIRED BEFORE ANYTHING ELSE.
  //
  // `SpiBusB` refuses to key a sub-GHz transmitter that the D-792 accessory
  // permission table does not allow in the present mode/rail state, and it asks
  // `g_app` -- the one object that knows the accessory rail state and can read
  // the gauge.  Set here, before the first `probe*()` takes a bus hold, so no
  // code path can reach `beginTransmit` with no authority attached.
  // `test_production_callers.cpp` proves this line exists.
  g_spi_b.setAccessoryLoadAuthority(&g_app);

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
  // D-792 / R11-04.  The SPI-B transmit gate is only a gate if it is WIRED, and
  // a wiring that is only wired in a comment is what Round-8 through Round-11
  // kept finding.  This line makes the attachment OBSERVABLE, so
  // `test_production_image.cpp` can prove it from the console output and a
  // negative control that deletes the call is CAUGHT rather than silent.
  report("SPI-B sub-GHz transmit gate wired to the accessory permission table",
         g_spi_b.accessoryLoadAuthority() == &g_app);
  report("i2c recovered/open at bring-up speed", i2c_open);
  report("PCAL9535A safe latches before console wait", expanders_safe);
  if (!expanders_safe) {
    Serial.println("FATAL: accessory/reset safety state could not be established.");
    return;
  }

  // D-795: the app's rail flags are reconciled from the PHYSICAL latch the
  // moment it is known, rather than trusted from whatever the object held.
  g_app.afterAccessoryChange();
  scanI2c();
  releaseExpanderResetLines();

  // D-793 / R12-03.  AFTER the expander reset release -- U2.P01 is the
  // SX1262's reset, so the part cannot answer before it -- and BEFORE the
  // gauge qualification, the console loop, or anything that could enable an
  // accessory rail.  Until this confirms, `g_app` reports sub-GHz TX as KEYED
  // and every accessory permission is refused.
  (void)bringUpSpiBAndQuiesceRadios();

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
    const bool active = g_app.configureFuelGaugeActiveMode();
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
  Serial.printf("  BOOT_N (SW1) = %d   display initialised = %d%s\n",
                digitalRead(AQROOT_PIN_BOOT_N), g_app.displayIsUp(),
                g_app.displayResetIntentPending()
                    ? "  (DISP_RST_N release UNCONFIRMED)" : "");
  if (g_app.amplifierIntentPending()) {
    Serial.println("  WARNING: AMP_SD_MODE intent unconfirmed -- the "
                   "amplifier may still be energised");
  }
}

void loop() {
  if (!g_expanders.ready()) {
    // Round-4 R4-03: an MCU reset must not turn one failed safe-latch write
    // into an indefinite energized rail.  D-789 / D788-06: the retry itself --
    // bus reopen, the COMPLETE `DemoExpanders::begin`, reset release, run-speed
    // raise and gauge requalification -- lives in `DemoBringupApp` so that
    // `test_production_callers.cpp` executes it against a physical-latch model.
    (void)g_app.serviceExpanderRecovery();
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
      g_app.afterAccessoryChange();
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
      g_app.afterAccessoryChange();
      if (millis() - last_service_error > 1000) {
        last_service_error = millis();
        const char *obs = "available";
        if (g_expanders.faultObservabilityLost()) {
          obs = g_expanders.safeShutdownPending()
              ? "LOST (shutdown pending; output state unknown)"
              : "LOST (output state unconfirmed)";
        }
        Serial.printf("I2C service FAILED; accessory fault observability=%s\n", obs);
      }
    }
  }

  // If boot caught the gauge while MODE.HibStat was still asserted, keep
  // trying to qualify it in the background while accessory power is safely
  // off.  This is liveness only: no rail is energized until qualification and
  // the subsequent VCELL permission both succeed.  D-789 / D788-04: the
  // condition AND the period live in `DemoBringupApp`, which a host test runs.
  (void)g_app.backgroundGaugeRequalification();
  // D-793 / R12-03.  LIVENESS.  A board that failed to quiesce once would
  // otherwise sit with an unknown radio state forever and refuse accessory
  // power with no way back -- the same shape as the expander recovery retry.
  // D-794 / R13-03: the NFC field is part of the same liveness requirement --
  // an unconfirmed field holds a burst slot and refuses accessory power, so a
  // board that gave up on it would refuse both forever.
  if (!g_app.radiosQuiesced() || !g_app.nfcFieldConfirmedOff()) {
    static uint32_t last_quiesce = 0;
    static bool quiesce_retry_started = false;
    const uint32_t now = millis();
    if (!quiesce_retry_started || now - last_quiesce >= kRadioQuiescePeriodMs) {
      quiesce_retry_started = true;
      last_quiesce = now;
      (void)bringUpSpiBAndQuiesceRadios();
    }
  }
  // D-795 / R14-02: liveness of a confirmed-quiet NFC front end.
  serviceNfcLiveness();
  g_app.periodicBatteryGuard();
  // D-790 / D789-A09: any non-accessory command whose write did not land is
  // retried here until the physical latch confirms it.
  (void)g_app.serviceDeferredCommands();
  // D-791 / D790-A07: and a release that only landed on that retry still owes
  // the panel its initialisation.  A confirmed reset release is NOT a
  // confirmed panel initialisation, so the operation the operator asked for is
  // COMPLETED here rather than being reported as done.
  if (g_app.displayInitOwed()) {
    Serial.println("display: DISP_RST_N release landed on retry -- re-running "
                   "the ILI9488 initialisation the reset invalidated");
    runDisplayInitialisation();
  }

  if (Serial.available()) {
    const char key = char(Serial.read());
    switch (key) {
      case 'r': g_expanders.setRgb(g_bus, true, false, false); break;
      case 'g': g_expanders.setRgb(g_bus, false, true, false); break;
      case 'b': g_expanders.setRgb(g_bus, false, false, true); break;
      case 'w': g_expanders.setRgb(g_bus, true, true, true); break;
      case 'o': g_expanders.setRgb(g_bus, false, false, false); break;
      // D-789 / D788-05 + D788-04.  THE ACCESSORY AND BACKLIGHT KEYS ARE
      // DISPATCHED BY `DemoBringupApp`, WHICH A HOST TEST EXECUTES.  Round-8
      // showed that a duplicate live backlight implementation placed here, and
      // a permission path that skipped the gauge qualification, both passed
      // every gate.  This file no longer owns either behaviour: '3', '5', 'i'
      // and 'l' are handled entirely inside the app.
      case '3':
      case '5':
      case 'i':
      case 'l':
        (void)g_app.handleAccessoryConsole(key);
        break;
      case 'm': {
        if (!g_app.blockingDemoTestAllowed("microphone test")) break;
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
        if (!g_app.blockingDemoTestAllowed("microSD test")) break;
        // D-793 / R12-08: at most ONE bursty peripheral at a time, so the
        // permission table can be derived at the worst SINGLE burst instead
        // of the coincident sum of all three.
        if (!g_app.burstAllowed(BurstLoad::MicroSdWrite, "microSD test")) break;
        BurstArbiter::Hold burst(g_app.burstArbiter(),
                                 BurstLoad::MicroSdWrite);
        if (!burst.ok()) break;
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
      case 'p': {
        if (!g_app.blockingDemoTestAllowed("display test")) break;
        // RESET IS NOT AN MCU PIN.  U2.P04 owns it, so the pulse goes through
        // the expander before a single SPI byte is sent.
        //
        // D-790 / D789-A09.  THE RELEASE IS AN INTENT, NOT A FIRE-AND-FORGET.
        // This file used to discard both `setDisplayReset` results and then
        // set `g_display_up = true` unconditionally -- so a NACKed release
        // left the panel held in reset while the console said the display was
        // up.  The pulse-and-release now lives in `DemoBringupApp`, which
        // CONFIRMS it from U2's physical output shadow and keeps retrying from
        // `loop()` if it did not land.
        Serial.println("display: pulsing DISP_RST_N via U2.P04, then ILI9488 init");
        if (!g_app.releaseDisplayResetIntent()) {
          Serial.println("display: ABORTED -- DISP_RST_N release not confirmed; "
                         "no SPI init attempted, retry pending");
          break;
        }
        runDisplayInitialisation();
        break;
      }
      case 'x': {
        if (!g_app.blockingDemoTestAllowed("IR test")) break;
        // D-793 / R12-08: the same serialisation the microSD path takes.
        if (!g_app.burstAllowed(BurstLoad::IrTransmit, "IR test")) break;
        BurstArbiter::Hold burst(g_app.burstArbiter(), BurstLoad::IrTransmit);
        if (!burst.ok()) break;
        const IrSelfTest ir = irSelfTest();
        Serial.printf("IR  %u/%u samples low during a 38 kHz burst -- %s\n",
                      ir.low_samples, ir.total_samples,
                      ir.detected ? "receiver saw the emitter"
                                  : "no return (reflection dependent)");
        break;
      }
      case 't':
        if (!g_app.blockingDemoTestAllowed("audio tone")) break;
        // Leaving shutdown is what makes AMP_SD_MODE observable at all.
        //
        // D-790 / D789-A09.  BOTH WRITES ARE INTENTS AND THE SECOND ONE IS THE
        // SAFETY-RELEVANT ONE.  This file used to discard both results, so a
        // NACKed shutdown left the amplifier physically ENERGISED with nothing
        // watching.  `setAmplifierIntent` confirms from U2's output shadow and
        // leaves a pending retry that `loop()` services.
        Serial.println("1 kHz tone -- amplifier leaving shutdown");
        if (!g_app.setAmplifierIntent(true)) {
          Serial.println("audio: ABORTED -- AMP_SD_MODE enable not confirmed");
          break;
        }
        delay(5);
        Serial.printf("i2s tone %s\n", playTone(1000, 400) ? "played" : "FAILED");
        if (!g_app.setAmplifierIntent(false)) {
          Serial.println("audio: AMPLIFIER SHUTDOWN NOT CONFIRMED -- retry "
                         "pending; do not assume the speaker is quiet");
        }
        break;
      default: break;
    }
  }
}
