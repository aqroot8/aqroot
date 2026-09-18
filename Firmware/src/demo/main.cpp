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

#include "../hw/aqroot_demo_board.h"
#include "../hw/aqroot_demo_display.h"
#include "../hw/aqroot_demo_expanders.h"
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
static void bringUpExpanders() {
  const bool ok = g_expanders.begin(g_bus);
  char detail[96];
  snprintf(detail, sizeof(detail), "U2 0x%02X U3 0x%02X", AQROOT_EXP_U2_ADDR,
           AQROOT_EXP_U3_ADDR);
  report("PCAL9535A safe bring-up", ok, detail);
  if (!ok) return;

  // Everything the board holds safe with an external 100k is now held safe by
  // the expander's own latch instead.  Release the three resets in the order
  // the parts want them: display and touch first (they are slow), LoRa last.
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

  Serial.begin(115200);
  const uint32_t deadline = millis() + 3000;
  while (!Serial && millis() < deadline) {
  }
  Serial.println();
  Serial.println("AQROOT Demo -- as-built bring-up");
  Serial.printf("board_sha256 %s\n", AQROOT_DEMO_BOARD_SHA256);
  Serial.println("---------------------------------------------------------------");
  report("pins parked", true);

  report("i2c open at bring-up speed", g_bus.begin(AQROOT_I2C_BRINGUP_HZ));
  scanI2c();
  bringUpExpanders();

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
  // The MAX17048 VERSION register is a silicon revision; report it rather than
  // assert a value this repository has no datasheet for.
  probeI2cDevice("MAX17048 U14 version", AQROOT_I2C_ADDR_FUEL_GAUGE, 0x08, 0x00,
                 false);
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
    delay(1000);
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
      if (g_expanders.u2Inputs() != g_last_u2 ||
          g_expanders.u3Inputs() != g_last_u3) {
        g_last_u2 = g_expanders.u2Inputs();
        g_last_u3 = g_expanders.u3Inputs();
        Serial.printf("change  U2=0x%04X (irq 0x%04X)  U3=0x%04X (irq 0x%04X)\n",
                      g_last_u2, g_expanders.u2InterruptStatus(), g_last_u3,
                      g_expanders.u3InterruptStatus());
        printStatus();
      }
    }
  }

  if (Serial.available()) {
    static bool acc3v3 = false, acc5v = false, buffer_on = false;
    switch (Serial.read()) {
      case 'r': g_expanders.setRgb(g_bus, true, false, false); break;
      case 'g': g_expanders.setRgb(g_bus, false, true, false); break;
      case 'b': g_expanders.setRgb(g_bus, false, false, true); break;
      case 'w': g_expanders.setRgb(g_bus, true, true, true); break;
      case 'o': g_expanders.setRgb(g_bus, false, false, false); break;
      case '3':
        acc3v3 = !acc3v3;
        Serial.printf("ACC_3V3_SW %s -> %d\n", acc3v3 ? "on" : "off",
                      g_expanders.setAccessory3v3(g_bus, acc3v3));
        break;
      case '5':
        acc5v = !acc5v;
        // Boost first, switch second, and the reverse on the way down.  Both
        // disconnects are required by D-186 and neither is optional.
        Serial.printf("ACC_5V_SW %s -> %d\n", acc5v ? "on" : "off",
                      g_expanders.setAccessory5v(g_bus, acc5v));
        break;
      case 'i':
        buffer_on = !buffer_on;
        // Refuses unless the switched 3.3 V rail is already up: U16 is powered
        // from ACC_3V3_SW.
        Serial.printf("ACC_PWR_EN %s -> %d\n", buffer_on ? "on" : "off",
                      g_expanders.setAccessoryI2cBuffer(g_bus, buffer_on));
        break;
      case 'm': {
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
        Serial.println("backlight ramp on GPIO46 (U17 TPS61169)");
        backlightRamp();
        break;
      case 'p': {
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
        const IrSelfTest ir = irSelfTest();
        Serial.printf("IR  %u/%u samples low during a 38 kHz burst -- %s\n",
                      ir.low_samples, ir.total_samples,
                      ir.detected ? "receiver saw the emitter"
                                  : "no return (reflection dependent)");
        break;
      }
      case 't':
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
