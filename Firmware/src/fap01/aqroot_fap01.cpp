// AQROOT Demo -- FAP-01, THE FIRST-ARTICLE DIAGNOSTIC IMAGE.  NEVER SHIP IT.
//
// D-801 / D801-01.  The contract, the bounds and the console are documented in
// `aqroot_fap01.h`; the bench procedure is
// `docs/full-beta-v2/assembly/FAP01_FIRST_ARTICLE_IMAGE.md`.
//
// This translation unit exists ONLY in `[env:aqroot-demo-fap01]`: the release
// environment's `build_src_filter` (`-<*> +<demo/> +<hw/>`) never compiles
// `src/fap01/`, and the header this file includes first refuses to compile
// without `AQROOT_FAP01_DIAGNOSTIC`.  `firmware_hw_map_contract` H9/H10 check
// both, and H6 runs `test_fap01_image.cpp` against both builds.

#include "aqroot_fap01.h"

#if !defined(AQROOT_FAP01_DIAGNOSTIC)
#error "aqroot_fap01.cpp compiled without AQROOT_FAP01_DIAGNOSTIC: FAP-01 has leaked into a non-diagnostic build"
#endif

#include <Arduino.h>
#include <Preferences.h>
#include <SPI.h>
#include <driver/i2s.h>
#include <esp_wifi.h>
#include <WiFi.h>

#include "../hw/aqroot_demo_backlight.h"
#include "../hw/aqroot_demo_board.h"
#include "../hw/aqroot_demo_radios.h"

namespace aqroot {
namespace fap01 {
namespace {

Context g_ctx = {nullptr, nullptr, nullptr, nullptr, nullptr};
bool g_ready = false;

struct Timed {
  bool on = false;
  uint32_t start_ms = 0;
};
Timed g_cc_tx, g_sx_cw, g_nfc_field, g_wifi, g_audio, g_backlight;
bool g_bench_declared = false;
uint32_t g_bench_declared_ms = 0;
bool g_wifi_stopped_once = false;
uint32_t g_wifi_stopped_ms = 0;
uint32_t g_wifi_frames = 0;
uint32_t g_audio_phase = 0;
uint8_t g_restored_holdoffs = 0;

// The NVS record that carries an IMMEDIATE hold-off across ONE warm reset,
// so C-RADIO-QUIESCE-01 / C-NFC-QUIESCE-01 can watch the BOOT quiesce run
// against a held-off part.  bit 0 = U7, bit 1 = U9.  It is written only while
// a hold-off is in force, cleared when it is released or reaches its bound,
// and CONSUMED (erased) by the first boot that reads it.
constexpr const char *kNvsNamespace = "aqroot-fap01";
constexpr const char *kNvsHoldOff = "holdoff";
constexpr uint8_t kHoldOffU7 = 0x01;
constexpr uint8_t kHoldOffU9 = 0x02;

void say(const char *line) { Serial.println(line); }

bool expired(const Timed &t, uint32_t bound_ms) {
  return t.on && millis() - t.start_ms >= bound_ms;   // wrap-safe
}

// ---- SPI-B.  Every FAP-01 user begins AND ends the peripheral (D-800). ----
void spiBBegin() {
  g_ctx.selects->begin();
  SPI.begin(AQROOT_PIN_SPI_B_SCK, AQROOT_PIN_SPI_B_MISO, AQROOT_PIN_SPI_B_MOSI,
            -1);
}
void spiBEnd() { SPI.end(); }

// ===========================================================================
// CC1101 (U7, Ebyte E07-400M10S, +10 dBm module, 26 MHz crystal) --
// CONTINUOUS TRANSMIT.
//
// Register values are TI's CC1101 register map (SWRS061) as SmartRF Studio
// emits them for 433.92 MHz, 2-FSK, 1.2 kBaud; the datasheet is NOT archived
// in this repository (only Ebyte's module manual is), so they are carried
// here as the configuration of record and PROVED ON THE BENCH by the thing
// C-RADIO-QUIESCE-01 looks for anyway: a carrier on the spectrum analyser.
// A wrong value shows as no carrier and a refused key -- MARCSTATE is read
// back and only 0x13 (TX) counts as keyed -- never as a hazard: the module's
// PA cannot exceed its +10 dBm.  PKTCTRL0 = 0x22 is RANDOM TX mode with
// infinite length: the part transmits PN9 data from its own generator, so no
// FIFO has to be fed and nothing can underflow into a half-keyed state.
struct RegWrite {
  uint8_t addr;
  uint8_t value;
};
constexpr RegWrite kCc1101ContinuousTx[] = {
    {0x00, 0x2E},  // IOCFG2   GDO2 high impedance
    {0x02, 0x2E},  // IOCFG0   GDO0 high impedance (the MCU pin is an input)
    {0x08, 0x22},  // PKTCTRL0 random TX, infinite length
    {0x0B, 0x06},  // FSCTRL1
    {0x0D, 0x10},  // FREQ2    433.92 MHz at 26 MHz: 0x10B071
    {0x0E, 0xB0},  // FREQ1
    {0x0F, 0x71},  // FREQ0
    {0x10, 0xF5},  // MDMCFG4
    {0x11, 0x83},  // MDMCFG3  1.2 kBaud
    {0x12, 0x00},  // MDMCFG2  2-FSK, no sync word
    {0x15, 0x15},  // DEVIATN  ~5.2 kHz
    {0x18, 0x18},  // MCSM0    calibrate IDLE -> TX
    {0x22, 0x10},  // FREND0   PA_POWER index 0
    {0x23, 0xE9},  // FSCAL3
    {0x24, 0x2A},  // FSCAL2
    {0x25, 0x00},  // FSCAL1
    {0x26, 0x1F},  // FSCAL0
    {0x2C, 0x81},  // TEST2
    {0x2D, 0x35},  // TEST1
    {0x2E, 0x09},  // TEST0
};
constexpr uint8_t kCc1101PatableFullPower = 0xC0;   // ~+10 dBm at 433 MHz
constexpr uint8_t kCc1101MarcstateTx = 0x13;

void waitCc1101SoLow() {
  const uint32_t start = millis();               // wrap-safe
  while (digitalRead(AQROOT_PIN_SPI_B_MISO) == HIGH && millis() - start < 10) {
  }
}

bool cc1101ConfigureAndStrobeTx() {
  bool ok = false;
  SPI.beginTransaction(SPISettings(4000000, MSBFIRST, SPI_MODE0));
  {
    SpiBusB::Hold hold(*g_ctx.spi_b, SpiBDevice::Cc1101);
    if (hold.ok()) {
      waitCc1101SoLow();
      SPI.transfer(0x36);                        // SIDLE
      SPI.transfer(0x3B);                        // SFTX
      for (const RegWrite &w : kCc1101ContinuousTx) {
        SPI.transfer(w.addr);                    // single write, BURST clear
        SPI.transfer(w.value);
      }
      SPI.transfer(0x3E);                        // PATABLE[0]
      SPI.transfer(kCc1101PatableFullPower);
      SPI.transfer(0x35);                        // STX
      ok = true;
    }
  }
  SPI.endTransaction();
  return ok;
}

uint8_t cc1101Marcstate() {
  uint8_t marc = 0xFF;
  SPI.beginTransaction(SPISettings(4000000, MSBFIRST, SPI_MODE0));
  {
    SpiBusB::Hold hold(*g_ctx.spi_b, SpiBDevice::Cc1101);
    if (hold.ok()) {
      waitCc1101SoLow();
      SPI.transfer(uint8_t(0xC0 | 0x35));        // burst read MARCSTATE
      marc = SPI.transfer(0x00);
    }
  }
  SPI.endTransaction();
  return uint8_t(marc & 0x1F);
}

// Stop a sub-GHz transmitter with the release image's OWN quiesce.  A stop
// that cannot be confirmed from the part's register leaves the app's radio
// state UNKNOWN -- sub-GHz counted as keyed, every rail refused -- and the
// release image's quiesce retry takes over.
void releaseSubGhz(SpiBDevice device, bool confirmed_quiet) {
  if (!confirmed_quiet) g_ctx.app->noteRadiosQuiesced(false);
  g_ctx.spi_b->endTransmit(device);
}

void stopCc1101(const char *why) {
  if (!g_cc_tx.on) return;
  g_cc_tx.on = false;
  uint8_t marc = 0xFF;
  spiBBegin();
  const bool idle = cc1101Quiesce(*g_ctx.spi_b, &marc);
  spiBEnd();
  releaseSubGhz(SpiBDevice::Cc1101, idle);
  Serial.printf("FAP-01: CC1101 continuous TX STOPPED (%s) -- SIDLE/SRES, "
                "MARCSTATE=0x%02X (%s)\n", why, marc,
                idle ? "IDLE, quiesced"
                     : "NOT IDLE -- radio state UNKNOWN, quiesce retry owns it");
}

void startCc1101() {
  if (g_wifi.on) {
    say("FAP-01: CC1101 TX REFUSED: the Wi-Fi burst is running (one "
        "transmitter at a time)");
    return;
  }
  // THE ONE WAY A SUB-GHz TRANSMITTER IS KEYED: the release image's gate.
  if (!g_ctx.spi_b->beginTransmit(SpiBDevice::Cc1101)) {
    say("FAP-01: CC1101 TX REFUSED by SpiBusB::beginTransmit -- another "
        "transmitter or field is keyed, the radio state is UNKNOWN, or the "
        "D-792 permission table refuses sub-GHz TX in this mode/rail state");
    return;
  }
  spiBBegin();
  const bool sent = cc1101ConfigureAndStrobeTx();
  uint8_t marc = 0xFF;
  const uint32_t start = millis();
  for (unsigned attempt = 0; attempt < 20; ++attempt) {
    delay(1);
    marc = cc1101Marcstate();
    if (marc == kCc1101MarcstateTx || millis() - start >= 20) break;
  }
  spiBEnd();
  if (!sent || marc != kCc1101MarcstateTx) {
    Serial.printf("FAP-01: CC1101 TX NOT CONFIRMED (MARCSTATE=0x%02X, want "
                  "0x13) -- quiescing and releasing the transmit slot\n", marc);
    g_cc_tx.on = true;
    stopCc1101("keying not confirmed");
    return;
  }
  g_cc_tx.on = true;
  g_cc_tx.start_ms = millis();
  Serial.printf("FAP-01: CC1101 continuous TX KEYED at 433.92 MHz, PATABLE "
                "0x%02X, MARCSTATE=0x13 -- bounded to %lu ms; C again or Q "
                "stops it\n", kCc1101PatableFullPower,
                (unsigned long)kSubGhzTxMaxMs);
}

// ===========================================================================
// SX1262 (U8, Ebyte E22-900M22S) -- CW AT +22 dBm.
//
// The command set is Semtech's SX1261/2 datasheet (DS.SX1261-2), which is NOT
// archived here; the module facts are, in
// `hardware/demo/kicad/aqroot-demo/vendor/Ebyte/ebyte-E22-M-series-usermanual.txt`:
// a 32 MHz TCXO powered from DIO3 at 2.2 V, and DIO2 driving the RF switch
// (this board's TXEN is DIO2; only RXEN, U3.P16, is ours and it stays at its
// safe latch 0).  Keyed state is CONFIRMED from GetStatus chip mode 0x6 (TX).
struct SxCmd {
  uint8_t len;
  uint8_t b[5];
};
constexpr SxCmd kSx1262Cw[] = {
    {2, {0x80, 0x00}},                    // SetStandby(STDBY_RC)
    {5, {0x97, 0x03, 0x00, 0x01, 0x40}},  // SetDIO3AsTCXOCtrl 2.2 V, 5 ms
    {2, {0x89, 0x7F}},                    // Calibrate(all)
    {2, {0x9D, 0x01}},                    // SetDIO2AsRfSwitchCtrl
    {2, {0x8A, 0x01}},                    // SetPacketType(LoRa)
    {5, {0x86, 0x39, 0x30, 0x00, 0x00}},  // SetRfFrequency 915 MHz
    {3, {0x98, 0xE1, 0xE9}},              // CalibrateImage 902-928 MHz
    {5, {0x95, 0x04, 0x07, 0x00, 0x01}},  // SetPaConfig: SX1262 +22 dBm
    {3, {0x8E, 0x16, 0x04}},              // SetTxParams +22 dBm, 200 us ramp
    {1, {0xD1}},                          // SetTxContinuousWave
};

bool sx1262Send(const uint8_t *bytes, uint8_t n, uint8_t *last = nullptr) {
  if (!sx1262WaitBusy()) return false;
  bool ok = false;
  SPI.beginTransaction(SPISettings(8000000, MSBFIRST, SPI_MODE0));
  {
    SpiBusB::Hold hold(*g_ctx.spi_b, SpiBDevice::Sx1262);
    if (hold.ok()) {
      uint8_t r = 0;
      for (uint8_t i = 0; i < n; ++i) r = SPI.transfer(bytes[i]);
      if (last) *last = r;
      ok = true;
    }
  }
  SPI.endTransaction();
  return ok;
}

void stopSx1262(const char *why) {
  if (!g_sx_cw.on) return;
  g_sx_cw.on = false;
  uint8_t status = 0xFF;
  spiBBegin();
  const bool standby = sx1262Quiesce(*g_ctx.spi_b, &status);
  spiBEnd();
  releaseSubGhz(SpiBDevice::Sx1262, standby);
  Serial.printf("FAP-01: SX1262 CW STOPPED (%s) -- SetStandby, status=0x%02X "
                "(%s)\n", why, status,
                standby ? "STANDBY, quiesced"
                        : "NOT STANDBY -- radio state UNKNOWN, quiesce retry "
                          "owns it");
}

void startSx1262() {
  if (g_wifi.on) {
    say("FAP-01: SX1262 CW REFUSED: the Wi-Fi burst is running (one "
        "transmitter at a time)");
    return;
  }
  if (!g_ctx.spi_b->beginTransmit(SpiBDevice::Sx1262)) {
    say("FAP-01: SX1262 CW REFUSED by SpiBusB::beginTransmit -- another "
        "transmitter or field is keyed, the radio state is UNKNOWN, or the "
        "D-792 permission table refuses sub-GHz TX in this mode/rail state");
    return;
  }
  spiBBegin();
  bool sent = true;
  for (const SxCmd &c : kSx1262Cw) sent = sx1262Send(c.b, c.len) && sent;
  uint8_t status = 0xFF;
  const uint8_t get_status[2] = {0xC0, 0x00};
  const bool read = sx1262Send(get_status, 2, &status);
  spiBEnd();
  const bool tx = sent && read && ((status >> 4) & 0x07) == 0x06;
  g_sx_cw.on = true;
  if (!tx) {
    Serial.printf("FAP-01: SX1262 CW NOT CONFIRMED (status=0x%02X, want chip "
                  "mode 0x6 TX) -- quiescing and releasing the transmit slot\n",
                  status);
    stopSx1262("keying not confirmed");
    return;
  }
  g_sx_cw.start_ms = millis();
  Serial.printf("FAP-01: SX1262 CW KEYED at 915.000 MHz, +22 dBm, status=0x%02X "
                "-- bounded to %lu ms; L again or Q stops it\n", status,
                (unsigned long)kSubGhzTxMaxMs);
}

// ===========================================================================
// ST25R3916 (U9) -- THE FIELD, THROUGH A FIELD SESSION (D796-10).
//
// DS12484 Rev 3 (archived): Operation control 02h bit 7 `en` (oscillator and
// regulators), bit 6 `rx_en`, bit 3 `tx_en` ("Enables Tx operation"); direct
// command D6h Adjust regulators (operation mode `en`); the Mode definition
// register 03h defaults to 0x08 = ISO14443A initiator, which Set default has
// just restored.  The field is ON when 02h reads back 0xC8 -- a dead read
// path reads 0x00 or 0xFF and is refused, never mistaken for a field.
void stopNfcField(const char *why) {
  if (!g_nfc_field.on) return;
  g_nfc_field.on = false;
  uint8_t op = 0xFF;
  spiBBegin();
  (void)st25r3916_spi::writeRegister(*g_ctx.spi_b, 0x02, 0x00);
  (void)st25r3916_spi::readRegister(*g_ctx.spi_b, 0x02, &op);
  spiBEnd();
  // D796-10: ending the session does NOT restore the OFF confirmation; the
  // release image's quiesce retry must prove it from a live part.
  g_ctx.app->endNfcFieldSession(*g_ctx.spi_b);
  Serial.printf("FAP-01: NFC field OFF (%s) -- Operation control 0x%02X "
                "written 0x00; field state UNKNOWN until the quiesce retry "
                "proves it off\n", why, op);
}

void startNfcField() {
  if (g_wifi.on) {
    say("FAP-01: NFC field REFUSED: the Wi-Fi burst is running (one "
        "transmitter at a time)");
    return;
  }
  // THE ONE WAY THE FIELD IS TURNED ON: the release image's session gate --
  // confirmed-off live part, no rail live, the burst slot, the SPI-B
  // transmit slot.  It logs its own refusal.
  if (!g_ctx.app->beginNfcFieldSession(*g_ctx.spi_b)) return;
  g_nfc_field.on = true;
  spiBBegin();
  bool w = st25r3916_spi::writeRegister(*g_ctx.spi_b, 0x02, 0x80);   // en
  delay(5);                                                           // oscillator
  w = st25r3916_spi::command(*g_ctx.spi_b, 0xD6) && w;                // Adjust regulators
  delay(5);
  w = st25r3916_spi::writeRegister(*g_ctx.spi_b, 0x02, 0xC8) && w;    // en|rx_en|tx_en
  uint8_t op = 0x00;
  const bool read = st25r3916_spi::readRegister(*g_ctx.spi_b, 0x02, &op);
  spiBEnd();
  if (!w || !read || op != 0xC8) {
    Serial.printf("FAP-01: NFC field NOT CONFIRMED (Operation control reads "
                  "0x%02X, want 0xC8) -- turning it off\n", op);
    stopNfcField("field not confirmed");
    return;
  }
  g_nfc_field.start_ms = millis();
  g_ctx.app->noteMaterialLoadEdge("the FAP-01 NFC field");
  Serial.printf("FAP-01: NFC field ON (Operation control 0x%02X: en, rx_en, "
                "tx_en; ISO14443A default mode) -- bounded to %lu ms; N again "
                "or Q stops it; T sends one REQA\n", op,
                (unsigned long)kNfcFieldMaxMs);
}

// One ISO14443A REQA (DS12484 Table 13, C6h) and whatever ATQA the part
// collects.  REPORT ONLY: the receiver runs on its power-up defaults, not an
// application stack's analog configuration.
void sendReqa() {
  if (!g_nfc_field.on) {
    say("FAP-01: REQA REFUSED: the NFC field is off -- press N first");
    return;
  }
  spiBBegin();
  (void)st25r3916_spi::command(*g_ctx.spi_b, 0xC6);
  uint8_t irq = 0x00;
  const uint32_t start = millis();
  for (unsigned attempt = 0; attempt < 12; ++attempt) {
    uint8_t v = 0x00;
    if (st25r3916_spi::readRegister(*g_ctx.spi_b, 0x1A, &v)) irq |= v;
    if ((irq & 0x10) != 0 || millis() - start >= 10) break;   // I_rxe
    delay(1);
  }
  uint8_t count = 0x00;
  (void)st25r3916_spi::readRegister(*g_ctx.spi_b, 0x1E, &count);
  uint8_t atqa[3] = {0x00, 0x00, 0x00};
  if (count >= 2) {
    const uint8_t out[3] = {0x9F, 0x00, 0x00};                 // FIFO read
    (void)st25r3916_spi::frame(*g_ctx.spi_b, out, atqa, 3);
  }
  spiBEnd();
  Serial.printf("FAP-01: REQA sent -- main IRQ 0x%02X, FIFO %u byte(s), ATQA "
                "%02X %02X (%s; REPORT ONLY)\n", irq, unsigned(count), atqa[1],
                atqa[2], count >= 2 ? "a tag answered" : "no answer");
}

// ===========================================================================
// Wi-Fi -- THE DIAGNOSTIC-ONLY BURST, AND EXACTLY WHAT IT WAIVES.
//
// A broadcast probe request (a frame type ESP-IDF's raw TX API accepts),
// sent back-to-back from `service()` at 19.5 dBm with modem sleep off, so the
// radio is transmitting for as much of the burst as the driver's queue allows
// -- the C-MCU-01 "total while transmitting" state.
const uint8_t kProbeRequest[] = {
    0x40, 0x00, 0x00, 0x00,                          // probe request, duration
    0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF,              // DA broadcast
    0x02, 0xA0, 0x57, 0xFA, 0x01, 0x01,              // SA locally administered
    0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF,              // BSSID broadcast
    0x00, 0x00,                                      // sequence (driver fills)
    0x00, 0x00,                                      // SSID: wildcard
    0x01, 0x08, 0x82, 0x84, 0x8B, 0x96, 0x0C, 0x12, 0x18, 0x24,  // rates
};

bool benchDeclared() {
  return g_bench_declared && millis() - g_bench_declared_ms < kBenchDeclarationMs;
}

void stopWifi(const char *why) {
  if (!g_wifi.on) return;
  g_wifi.on = false;
  WiFi.mode(WIFI_OFF);
  g_ctx.app->noteWifiRadioActive(false);
  g_wifi_stopped_once = true;
  g_wifi_stopped_ms = millis();
  Serial.printf("FAP-01: Wi-Fi burst STOPPED (%s) -- %lu frame(s) queued; "
                "radio OFF\n", why, (unsigned long)g_wifi_frames);
}

void startWifi() {
  const char *why = nullptr;
  if (!benchDeclared()) {
    why = "the bench source is not declared -- connect the console through a "
          "VBUS-blocking adapter, power the pack or bench supply only, then "
          "press V";
  } else if (g_ctx.spi_b->transmitting() != SpiBDevice::None ||
             g_ctx.app->subGhzTransmitting() || g_ctx.app->nfcFieldSessionActive()) {
    why = "a sub-GHz transmitter or the NFC field is keyed (one transmitter "
          "at a time)";
  } else if (!g_ctx.app->radiosQuiesced() || !g_ctx.app->nfcFieldConfirmedOff()) {
    why = "the U7/U8 transmit state or the U9 field is not confirmed off";
  } else if (g_ctx.app->amplifierCountsAsOn() || g_audio.on) {
    why = "the amplifier is (or may be) energised";
  } else if (g_ctx.app->burstArbiter().active() != BurstLoad::None) {
    why = "a burst load holds the arbiter";
  } else if (g_wifi_stopped_once &&
             millis() - g_wifi_stopped_ms < kWifiCooldownMs) {
    why = "the previous burst ended less than 30 s ago (cool-down)";
  }
  if (why != nullptr) {
    Serial.printf("FAP-01: Wi-Fi burst REFUSED: %s\n", why);
    return;
  }
  // ASK THE RELEASE IMAGE'S PERMISSION TABLE FIRST, AND PRINT ITS ANSWER.
  if (!g_ctx.app->wifiActivationPermitted()) {
    AccessoryLoadState after = g_ctx.app->accessoryLoadState();
    after.wifi_tx = true;
    // The ONE refusal FAP-01 may waive: the no-rail CHARGING row, which
    // exists because the firmware cannot see the adapter.  A rail-live row is
    // a D-792 table refusal about the accessory tree and is NEVER waived.
    const bool charging_row_only =
        g_ctx.app->accessoryRailsOn() == 0 &&
        !g_ctx.expanders->safeShutdownPending() &&
        accessoryChargingModeEntryFloor(accessoryLoadBits(after)) >=
            kAccessoryNotPermittedV;
    if (!charging_row_only) {
      say("FAP-01: Wi-Fi burst REFUSED: the release permission table refuses "
          "Wi-Fi with an accessory rail live (or its safe state unconfirmed); "
          "that refusal is never waived -- turn both rails off");
      return;
    }
    say("FAP-01: DIAGNOSTIC WAIVER of the no-rail CHARGING row only (D-797 / "
        "D797-02 refuses Wi-Fi because the firmware cannot see the adapter): "
        "the operator has DECLARED no charger, both rails are off, nothing "
        "else is keyed; bounded burst, never in the release image");
  }
  g_ctx.app->noteWifiRadioActive(true);
  WiFi.mode(WIFI_STA);
  WiFi.setTxPower(WIFI_POWER_19_5dBm);
  (void)esp_wifi_set_ps(WIFI_PS_NONE);
  g_wifi.on = true;
  g_wifi.start_ms = millis();
  g_wifi_frames = 0;
  Serial.printf("FAP-01: Wi-Fi TX burst STARTED (raw probe requests, 19.5 dBm) "
                "-- bounded to %lu ms; W again or Q stops it\n",
                (unsigned long)kWifiBurstMaxMs);
}

void pumpWifi() {
  if (!g_wifi.on) return;
  for (int i = 0; i < 16; ++i) {
    if (esp_wifi_80211_tx(WIFI_IF_STA, kProbeRequest, sizeof(kProbeRequest),
                          true) == ESP_OK) {
      ++g_wifi_frames;
    }
  }
}

// ===========================================================================
// IR -- ten 38 kHz NEC frames from D1 (address 0x00, command 0x5A).
//
// Through the SAME gates as the release `x` self-test: both rails off, and
// the burst slot (`BurstLoad::IrTransmit`), so it cannot overlap a microSD
// write or a live / UNKNOWN NFC field.  ~1.1 s, with a liveness opportunity
// between frames.  D1 is only ever driven at the 50 % carrier duty, in NEC's
// own <= 1/3 on-air duty, and is left LOW (R23 holds Q1 off) at the end.
constexpr uint8_t kIrChannel = 1;
unsigned g_ir_low = 0, g_ir_samples = 0;

void irMark(uint32_t us) {
  ledcWrite(kIrChannel, 128);
  delayMicroseconds(us);
  ++g_ir_samples;
  if (digitalRead(AQROOT_PIN_IR_RX) == LOW) ++g_ir_low;
}
void irSpace(uint32_t us) {
  ledcWrite(kIrChannel, 0);
  delayMicroseconds(us);
}
void irNecFrame(uint8_t address, uint8_t command) {
  irMark(9000);
  irSpace(4500);
  const uint8_t bytes[4] = {address, uint8_t(~address), command,
                            uint8_t(~command)};
  for (uint8_t b : bytes) {
    for (int bit = 0; bit < 8; ++bit) {
      irMark(562);
      irSpace(((b >> bit) & 1) ? 1687 : 562);
    }
  }
  irMark(562);
  irSpace(0);
}

void irNecBurst() {
  if (!g_ctx.app->blockingDemoTestAllowed("FAP-01 IR NEC burst")) return;
  if (!g_ctx.app->burstAllowed(BurstLoad::IrTransmit, "FAP-01 IR NEC burst")) {
    return;
  }
  BurstArbiter::Hold burst(g_ctx.app->burstArbiter(), BurstLoad::IrTransmit);
  if (!burst.ok()) return;
  g_ir_low = 0;
  g_ir_samples = 0;
  ledcSetup(kIrChannel, 38000, 8);
  ledcAttachPin(AQROOT_PIN_IR_TX, kIrChannel);
  const uint32_t t0 = millis();
  for (unsigned frame = 0; frame < kIrNecFrames; ++frame) {
    for (unsigned attempt = 0;
         attempt < kIrNecFramePeriodMs + 20 &&
         millis() - t0 < frame * kIrNecFramePeriodMs;
         ++attempt) {
      (void)g_ctx.app->serviceNfcLiveness();
      delay(1);
    }
    irNecFrame(0x00, 0x5A);
  }
  ledcWrite(kIrChannel, 0);
  ledcDetachPin(AQROOT_PIN_IR_TX);
  pinMode(AQROOT_PIN_IR_TX, OUTPUT);
  digitalWrite(AQROOT_PIN_IR_TX, LOW);
  Serial.printf("FAP-01: IR %u NEC frames (addr 0x00, cmd 0x5A) sent from D1 "
                "in %lu ms; U6 low at %u of %u mark samples (C-IR-01: RECORD); "
                "emitter OFF\n", kIrNecFrames, (unsigned long)(millis() - t0),
                g_ir_low, g_ir_samples);
}

// ===========================================================================
// CHIP-SELECT HOLD-OFF.
void persistHoldOffs() {
  uint8_t mask = 0;
  HoldOffChipSelects &cs = *g_ctx.selects;
  // Only an IMMEDIATE hold-off travels across a reset; a delayed one is a
  // timing experiment on THIS boot.
  if (cs.holdOffActive(SpiBDevice::Cc1101)) mask |= kHoldOffU7;
  if (cs.holdOffActive(SpiBDevice::St25r3916)) mask |= kHoldOffU9;
  Preferences p;
  if (!p.begin(kNvsNamespace, false)) return;
  if (mask == 0) {
    (void)p.remove(kNvsHoldOff);
  } else {
    (void)p.putUChar(kNvsHoldOff, mask);
  }
  p.end();
}

const char *holdOffName(SpiBDevice d) {
  return d == SpiBDevice::Cc1101 ? "U7 CC1101_CS_N" : "U9 NFC_CS_N";
}

void releaseHoldOff(SpiBDevice device, const char *why) {
  HoldOffChipSelects &cs = *g_ctx.selects;
  if (!cs.holdOffArmed(device)) return;
  cs.setHoldOff(device, false);
  persistHoldOffs();
  Serial.printf("FAP-01: chip-select hold-off RELEASED on %s (%s) -- %lu "
                "select(s) were held high; the release image's quiesce retry "
                "and liveness probe re-prove the part\n", holdOffName(device),
                why, (unsigned long)cs.injected());
}

void armHoldOff(SpiBDevice device, uint32_t delay_ms) {
  HoldOffChipSelects &cs = *g_ctx.selects;
  if (cs.holdOffArmed(device)) {
    releaseHoldOff(device, "operator key");
    return;
  }
  cs.setHoldOff(device, true, delay_ms);
  if (delay_ms == 0) persistHoldOffs();
  Serial.printf("FAP-01: chip-select hold-off ARMED on %s -- begins %lu ms "
                "after this key and lasts at most %lu ms; the driver still "
                "believes it selects the part%s\n", holdOffName(device),
                (unsigned long)delay_ms, (unsigned long)kHoldOffMaxMs,
                delay_ms == 0 ? "; it also survives ONE warm reset" : "");
}

// ===========================================================================
// HELD AUDIO -- the release tone, held.
constexpr i2s_port_t kI2sPort = I2S_NUM_0;
constexpr uint32_t kAudioRate = 44100;

void pumpAudio() {
  if (!g_audio.on) return;
  int16_t block[128 * 2];
  const uint32_t step = (kAudioToneHz * 0x10000u) / kAudioRate;
  // At most eight blocks (~23 ms) per call, written without blocking: the DMA
  // holds 6 x 256 frames, so a loop() that returns within ~35 ms keeps the
  // tone continuous and a blocking release test only leaves a gap.
  for (int n = 0; n < 8; ++n) {
    for (size_t i = 0; i < 128; ++i) {
      const int16_t s = (g_audio_phase & 0x8000u) ? int16_t(kAudioCappedAmplitude)
                                                  : int16_t(-kAudioCappedAmplitude);
      block[i * 2] = s;
      block[i * 2 + 1] = s;
      g_audio_phase += step;
    }
    size_t bytes = 0;
    if (i2s_write(kI2sPort, block, sizeof(block), &bytes, 0) != ESP_OK ||
        bytes < sizeof(block)) {
      break;
    }
  }
}

void stopAudio(const char *why) {
  if (!g_audio.on) return;
  g_audio.on = false;
  i2s_zero_dma_buffer(kI2sPort);
  i2s_driver_uninstall(kI2sPort);
  const bool off = g_ctx.app->setAmplifierIntent(false);
  Serial.printf("FAP-01: held audio STOPPED (%s) -- I2S released, amplifier "
                "%s\n", why, off ? "CONFIRMED in shutdown"
                                 : "shutdown NOT CONFIRMED (retry pending)");
}

void startAudio() {
  // THE MODE EDGE: the release image's own amplifier intent, which asks the
  // permission table for the mode set that will exist afterwards and logs
  // its own refusal (a rail live refuses audio's mode-edge row outright).
  if (!g_ctx.app->setAmplifierIntent(true)) {
    say("FAP-01: held audio REFUSED -- the amplifier intent was refused or not "
        "confirmed (see the line above)");
    return;
  }
  i2s_config_t config = {};
  config.mode = i2s_mode_t(I2S_MODE_MASTER | I2S_MODE_TX);
  config.sample_rate = kAudioRate;
  config.bits_per_sample = I2S_BITS_PER_SAMPLE_16BIT;
  config.channel_format = I2S_CHANNEL_FMT_RIGHT_LEFT;
  config.communication_format = I2S_COMM_FORMAT_STAND_I2S;
  config.intr_alloc_flags = 0;
  config.dma_buf_count = 6;
  config.dma_buf_len = 256;
  config.use_apll = false;
  config.tx_desc_auto_clear = true;     // an underrun is silence, not a loop
  i2s_pin_config_t pins = {};
  pins.bck_io_num = AQROOT_PIN_I2S_BCLK;
  pins.ws_io_num = AQROOT_PIN_I2S_LRCLK;
  pins.data_out_num = AQROOT_PIN_I2S_SPK_DOUT;
  pins.data_in_num = I2S_PIN_NO_CHANGE;
  bool up = i2s_driver_install(kI2sPort, &config, 0, nullptr) == ESP_OK;
  if (up && i2s_set_pin(kI2sPort, &pins) != ESP_OK) {
    i2s_driver_uninstall(kI2sPort);
    up = false;
  }
  if (!up) {
    (void)g_ctx.app->setAmplifierIntent(false);
    say("FAP-01: held audio ABORTED -- I2S TX could not be installed; "
        "amplifier returned to shutdown");
    return;
  }
  g_audio.on = true;
  g_audio.start_ms = millis();
  g_audio_phase = 0;
  pumpAudio();
  Serial.printf("FAP-01: held audio STARTED -- 1 kHz square at amplitude %u "
                "(the release tone's level), both slots -- bounded to %lu ms; "
                "A again or Q stops it\n", unsigned(kAudioCappedAmplitude),
                (unsigned long)kThermalHoldMaxMs);
}

// ===========================================================================
// HELD BACKLIGHT DUTY -- only after the D-784 full-duty prime.
constexpr uint8_t kBacklightChannel = 0;   // the release ramp's channel

void stopBacklight(const char *why) {
  if (!g_backlight.on) return;
  g_backlight.on = false;
  ledcWrite(kBacklightChannel, 0);
  ledcDetachPin(AQROOT_PIN_DISP_BL_PWM);
  pinMode(AQROOT_PIN_DISP_BL_PWM, OUTPUT);
  digitalWrite(AQROOT_PIN_DISP_BL_PWM, LOW);
  g_ctx.app->noteMaterialLoadEdge("the FAP-01 held backlight ending");
  Serial.printf("FAP-01: held backlight STOPPED (%s) -- DISP_BL_PWM LOW\n", why);
}

void startBacklight() {
  ledcSetup(kBacklightChannel, kBacklightPwmHz, 8);
  ledcAttachPin(AQROOT_PIN_DISP_BL_PWM, kBacklightChannel);
  runHeldBacklightPolicy(
      [](uint8_t duty) { ledcWrite(kBacklightChannel, duty); },
      [](uint32_t us) { delayMicroseconds(us); }, kHeldBacklightDuty);
  g_backlight.on = true;
  g_backlight.start_ms = millis();
  g_ctx.app->noteMaterialLoadEdge("the FAP-01 held backlight duty");
  Serial.printf("FAP-01: held backlight duty %u/255 after a %lu us full-duty "
                "prime (D-784) -- bounded to %lu ms; B again or Q stops it\n",
                unsigned(kHeldBacklightDuty),
                (unsigned long)kBacklightStartupPrimeUs,
                (unsigned long)kThermalHoldMaxMs);
}

// ===========================================================================
// VCELL CADENCE -- the raw register every 10 ms for 2 s (C-GAUGE-EPOCH-01).
// REPORT ONLY: nothing here feeds a permission.  Rails off, like every
// blocking release test, and the liveness schedule is kept between samples.
void pollVcell() {
  if (!g_ctx.app->blockingDemoTestAllowed("FAP-01 VCELL poll")) return;
  const uint32_t samples = kVcellPollSpanMs / kVcellPollPeriodMs;
  const uint32_t t0 = millis();
  Serial.printf("FAP-01: VCELL poll START at millis=%lu -- %lu samples, one "
                "every %lu ms (raw register 0x02, 78.125 uV/LSB)\n",
                (unsigned long)t0, (unsigned long)samples,
                (unsigned long)kVcellPollPeriodMs);
  unsigned failed = 0;
  for (uint32_t k = 0; k < samples; ++k) {
    for (unsigned attempt = 0;
         attempt < 2 * kVcellPollPeriodMs &&
         millis() - t0 < k * kVcellPollPeriodMs;
         ++attempt) {
      delay(1);
    }
    uint8_t raw[2] = {0xFF, 0xFF};
    const bool ok = g_ctx.bus->readRegister(AQROOT_I2C_ADDR_FUEL_GAUGE, 0x02,
                                            raw, 2);
    const uint32_t t = millis() - t0;
    if (ok) {
      const uint16_t counts = uint16_t(uint16_t(raw[0]) << 8 | raw[1]);
      Serial.printf("vcell t_ms=%lu raw=0x%04X V=%.5f\n", (unsigned long)t,
                    counts, double(counts) * 0.000078125);
    } else {
      ++failed;
      Serial.printf("vcell t_ms=%lu READ FAILED\n", (unsigned long)t);
    }
    (void)g_ctx.app->serviceNfcLiveness();
  }
  Serial.printf("FAP-01: VCELL poll END -- %lu ms, %u read failure(s)\n",
                (unsigned long)(millis() - t0), failed);
}

void help() {
  say("FAP-01 keys (upper case; the release keys still work):");
  say("  C CC1101 continuous TX   L SX1262 CW +22 dBm   N NFC field   T REQA");
  say("  V declare bench source (no charger)   W Wi-Fi TX burst (needs V)");
  say("  I IR NEC burst   H hold-off U7 CS   J hold-off U9 CS");
  say("  K U9 hold-off in 700 ms   Y U9 hold-off in 2000 ms");
  say("  A held audio   B held backlight duty   G VCELL 10 ms poll");
  say("  Q stop every FAP-01 stimulus   ? this list");
}

}  // namespace

// ===========================================================================
void begin(const Context &ctx) {
  g_ctx = ctx;
  g_ready = ctx.app && ctx.spi_b && ctx.selects && ctx.expanders && ctx.bus;
  // A reset stops everything the MCU owned: no radio, no I2S, no LEDC.  The
  // peripherals that outlive it (U7/U8/U9) are the release quiesce's.
  g_cc_tx = Timed();
  g_sx_cw = Timed();
  g_nfc_field = Timed();
  g_wifi = Timed();
  g_audio = Timed();
  g_backlight = Timed();
  g_bench_declared = false;
  g_wifi_stopped_once = false;
  g_wifi_frames = 0;
  g_restored_holdoffs = 0;
  if (!g_ready) return;
  g_ctx.selects->clearAll();
  // ONE boot consumes an armed hold-off -- read, erase, apply.
  Preferences p;
  if (p.begin(kNvsNamespace, false)) {
    const uint8_t mask = p.getUChar(kNvsHoldOff, 0);
    if (mask != 0) (void)p.remove(kNvsHoldOff);
    p.end();
    if (mask & kHoldOffU7) g_ctx.selects->setHoldOff(SpiBDevice::Cc1101, true);
    if (mask & kHoldOffU9) g_ctx.selects->setHoldOff(SpiBDevice::St25r3916, true);
    g_restored_holdoffs = uint8_t(mask & (kHoldOffU7 | kHoldOffU9));
  }
}

void announce() {
  say("===============================================================");
  say("FAP-01 FIRST-ARTICLE DIAGNOSTIC IMAGE -- NEVER SHIP, NEVER A DEFAULT");
  say("  built only by `pio run -e aqroot-demo-fap01` (AQROOT_FAP01_DIAGNOSTIC)");
  say("  release rules unchanged; every FAP-01 stimulus is bounded -- ? lists them");
  say("===============================================================");
  if (g_restored_holdoffs & kHoldOffU7) {
    say("FAP-01: chip-select hold-off RESTORED across the reset on U7 "
        "CC1101_CS_N -- in force for 60000 ms from boot");
  }
  if (g_restored_holdoffs & kHoldOffU9) {
    say("FAP-01: chip-select hold-off RESTORED across the reset on U9 "
        "NFC_CS_N -- in force for 60000 ms from boot");
  }
}

bool anyActive() {
  return g_cc_tx.on || g_sx_cw.on || g_nfc_field.on || g_wifi.on ||
         g_audio.on || g_backlight.on ||
         (g_ready && (g_ctx.selects->holdOffArmed(SpiBDevice::Cc1101) ||
                      g_ctx.selects->holdOffArmed(SpiBDevice::St25r3916)));
}

void stopAll(const char *why) {
  if (!g_ready) return;
  stopWifi(why);
  stopCc1101(why);
  stopSx1262(why);
  stopNfcField(why);
  stopAudio(why);
  stopBacklight(why);
  releaseHoldOff(SpiBDevice::Cc1101, why);
  releaseHoldOff(SpiBDevice::St25r3916, why);
  g_bench_declared = false;
}

void service() {
  if (!g_ready) return;
  // Something outside FAP-01 ended a state it keyed (an expander recovery,
  // a release rule): follow it rather than believe the flag.
  if (g_cc_tx.on && g_ctx.spi_b->transmitting() != SpiBDevice::Cc1101) {
    g_cc_tx.on = false;
  }
  if (g_sx_cw.on && g_ctx.spi_b->transmitting() != SpiBDevice::Sx1262) {
    g_sx_cw.on = false;
  }
  if (g_nfc_field.on && !g_ctx.app->nfcFieldSessionActive()) {
    g_nfc_field.on = false;
  }
  // THE BOUNDS.
  if (expired(g_cc_tx, kSubGhzTxMaxMs)) stopCc1101("30000 ms bound");
  if (expired(g_sx_cw, kSubGhzTxMaxMs)) stopSx1262("30000 ms bound");
  if (expired(g_nfc_field, kNfcFieldMaxMs)) stopNfcField("60000 ms bound");
  if (expired(g_wifi, kWifiBurstMaxMs)) stopWifi("10000 ms bound");
  if (expired(g_audio, kThermalHoldMaxMs)) stopAudio("30 min bound");
  if (expired(g_backlight, kThermalHoldMaxMs)) stopBacklight("30 min bound");
  for (SpiBDevice d : {SpiBDevice::Cc1101, SpiBDevice::St25r3916}) {
    if (g_ctx.selects->holdOffActiveMs(d) >= kHoldOffMaxMs) {
      releaseHoldOff(d, "60000 ms bound");
    }
  }
  if (g_bench_declared && !benchDeclared()) {
    g_bench_declared = false;
    say("FAP-01: bench-source declaration EXPIRED (120 s) -- press V again "
        "before another Wi-Fi burst");
  }
  pumpWifi();
  pumpAudio();
}

bool handleKey(char key) {
  if (!g_ready) return false;
  switch (key) {
    case 'C': g_cc_tx.on ? stopCc1101("operator key") : startCc1101(); return true;
    case 'L': g_sx_cw.on ? stopSx1262("operator key") : startSx1262(); return true;
    case 'N':
      g_nfc_field.on ? stopNfcField("operator key") : startNfcField();
      return true;
    case 'T': sendReqa(); return true;
    case 'V':
      g_bench_declared = true;
      g_bench_declared_ms = millis();
      say("FAP-01: BENCH SOURCE DECLARED by the operator -- no charger: the "
          "console cable blocks VBUS and the board runs from the pack or a "
          "bench supply at the pack terminals.  Valid 120 s; the firmware "
          "CANNOT verify this (D-776)");
      return true;
    case 'W': g_wifi.on ? stopWifi("operator key") : startWifi(); return true;
    case 'I': irNecBurst(); return true;
    case 'H': armHoldOff(SpiBDevice::Cc1101, 0); return true;
    case 'J': armHoldOff(SpiBDevice::St25r3916, 0); return true;
    case 'K': armHoldOff(SpiBDevice::St25r3916, kHoldOffNearDelayMs); return true;
    case 'Y': armHoldOff(SpiBDevice::St25r3916, kHoldOffFarDelayMs); return true;
    case 'A': g_audio.on ? stopAudio("operator key") : startAudio(); return true;
    case 'B':
      g_backlight.on ? stopBacklight("operator key") : startBacklight();
      return true;
    case 'G': pollVcell(); return true;
    case 'Q':
      stopAll("operator Q");
      say("FAP-01: every stimulus STOPPED");
      return true;
    case '?': help(); return true;
    // Release keys whose peripheral a HELD FAP-01 state owns: refused here
    // rather than letting two drivers fight over I2S or LEDC channel 0.
    case 't':
    case 'm':
      if (!g_audio.on) return false;
      say("FAP-01: REFUSED -- the held audio owns I2S; press A to stop it");
      return true;
    case 'l':
    case 'p':
      if (!g_backlight.on) return false;
      say("FAP-01: REFUSED -- the held backlight owns DISP_BL_PWM; press B to "
          "stop it");
      return true;
    default:
      return false;
  }
}

}  // namespace fap01
}  // namespace aqroot
