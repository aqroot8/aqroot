// AQROOT — radio driver (SX1262 via RadioLib).
//
// Implements both operating modes required by the interface:
//   * RADIO_MODE_LORA        — LoRa modulation (radio.begin)
//   * RADIO_MODE_SUBGHZ_RAW  — raw sub-GHz FSK/OOK (radio.beginFSK)
//
// The SPI pins at the top of config.h are PLACEHOLDER values and must be reconciled with
// the final PCB pinout. The SX1262 module itself (certified, e.g. Ebyte E22) is a
// permanent choice, so the RadioLib driver code here is real — only the wiring is TBD.
//
// SIMULATION_MODE: Wokwi has no SX1262 model, so all RadioLib calls are compiled out and
// the functions return realistic mock data (a wandering RSSI around -67 dBm at 915.2 MHz,
// matching the dashboard concept) so the scan UI and signal monitor can be tested E2E.

#include "radio.h"
#include "../config.h"
#include <Arduino.h>

static long  s_frequency_hz = 915200000L;  // default 915.2 MHz (matches design concept)
static float s_rssi_dbm     = -67.0f;
static radio_mode_t s_mode  = RADIO_MODE_LORA;

#ifndef SIMULATION_MODE
// ============================ REAL HARDWARE (RadioLib) ============================
#include <RadioLib.h>

static SX1262 s_radio = new Module(RADIO_NSS, RADIO_DIO1, RADIO_RST, RADIO_BUSY);
static volatile bool s_packet_ready = false;

// DIO1 fires when a packet has been received in continuous-RX mode.
static void IRAM_ATTR on_dio1(void) {
    s_packet_ready = true;
}

static void begin_current_mode(void) {
    const float mhz = s_frequency_hz / 1000000.0f;
    if (s_mode == RADIO_MODE_LORA) {
        s_radio.begin(mhz);                 // LoRa defaults (SF9/BW125/CR4:7)
    } else {
        s_radio.beginFSK(mhz);              // raw sub-GHz FSK/OOK
    }
    s_radio.setDio1Action(on_dio1);
    s_radio.startReceive();                 // continuous RX so the UI can poll
    s_packet_ready = false;
}

void radio_init(void) {
    SPI.begin(RADIO_SCK, RADIO_MISO, RADIO_MOSI, RADIO_NSS);
    begin_current_mode();
}

void radio_set_mode(radio_mode_t mode) {
    s_mode = mode;
    begin_current_mode();
}

void radio_set_frequency(long frequency_hz) {
    s_frequency_hz = frequency_hz;
    s_radio.setFrequency(frequency_hz / 1000000.0f);
    s_radio.startReceive();
}

int radio_transmit(const unsigned char *data, int length) {
    int state = s_radio.transmit(const_cast<uint8_t *>(data), length);
    begin_current_mode();                   // return to RX after TX
    return (state == RADIOLIB_ERR_NONE) ? length : -1;
}

int radio_receive(unsigned char *buffer, int max_length) {
    if (!s_packet_ready) {
        return 0;                           // no packet this poll; RSSI holds last value
    }
    s_packet_ready = false;

    int len = s_radio.getPacketLength();
    if (len > max_length) len = max_length;

    int state = s_radio.readData(buffer, len);
    s_rssi_dbm = s_radio.getRSSI();
    s_radio.startReceive();                 // re-arm

    return (state == RADIOLIB_ERR_NONE) ? len : -1;
}

#else
// ============================ SIMULATION (mock data) ============================
void radio_init(void) {}

void radio_set_mode(radio_mode_t mode) { s_mode = mode; }

void radio_set_frequency(long frequency_hz) { s_frequency_hz = frequency_hz; }

int radio_transmit(const unsigned char *data, int length) {
    (void)data;
    return length;                          // pretend the frame went out
}

int radio_receive(unsigned char *buffer, int max_length) {
    // Wander the RSSI so the signal monitor looks alive, and occasionally deliver a
    // short mock frame so the scan screen shows real-looking activity.
    s_rssi_dbm = -67.0f + (float)(random(-80, 81)) / 10.0f;   // ~ -75..-59 dBm

    if (max_length > 0 && random(0, 100) < 25) {
        int len = random(2, (max_length < 8 ? max_length : 8) + 1);
        for (int i = 0; i < len; i++) {
            buffer[i] = (unsigned char)random(0, 256);
        }
        return len;
    }
    return 0;
}
#endif  // SIMULATION_MODE

// --- Telemetry (identical in both builds) ---
float radio_get_rssi(void)     { return s_rssi_dbm; }
long  radio_get_frequency(void){ return s_frequency_hz; }
