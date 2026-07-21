// AQROOT — NFC driver (PN532 via Adafruit_PN532).
//
// ############################ WRONG PART — PENDING REWRITE ############################
// The PN532 is NOT the AQROOT NFC part. The locked front-end is the ST25R3916 (validated
// on Alpha over SPI: IC Identity reg 0x3F returned 0x2A, IC-type field 0x05). This file
// targets the wrong chip AND the wrong bus (PN532/I2C vs ST25R3916/SPI), and the
// `adafruit/Adafruit PN532` dependency in platformio.ini goes with it.
//
// Kept as-is deliberately: replacing it is real engineering work (the ST RFAL library port
// is the substantial piece), not documentation cleanup, and the current code at least keeps
// the build and the NFC UI screens alive in the meantime. The Alpha raw-SPI probe in
// Alpha-Tests/09_nfc_st25r3916_probe.ino is the foundation to build the real driver on.
//
// Tracked in "07 - Build TODO Tracker.md". See "05 - Design Decisions Log.md" for the
// decision. Do not treat anything below as reflecting the AQROOT hardware design.
// ######################################################################################
//
// SIMULATION_MODE: Wokwi has no PN532 model, so the library calls are compiled out and the
// functions return realistic mock data — a fixed 7-byte UID matching the dashboard concept
// (04 A2 3B 7C 9D 11 22) — so the NFC screen and the home NFC-tag panel work end-to-end.

#include "nfc.h"
#include "../config.h"
#include <Arduino.h>

#ifndef SIMULATION_MODE
// ============================ REAL HARDWARE (Adafruit_PN532) ============================
#include <Wire.h>
#include <Adafruit_PN532.h>

static Adafruit_PN532 s_pn532(NFC_IRQ, NFC_RESET, &Wire);
static bool s_ready = false;

void nfc_init(void) {
    Wire.begin(I2C_SDA, I2C_SCL, I2C_FREQ_HZ);
    s_pn532.begin();
    uint32_t version = s_pn532.getFirmwareVersion();
    if (version) {
        s_pn532.SAMConfig();     // configure the secure-access module for reading
        s_ready = true;
    }
}

// Poll for an ISO14443A tag and copy its UID. Returns UID length in bytes, or 0 if no tag.
int nfc_read_tag(unsigned char *uid_buffer, int max_length) {
    if (!s_ready) return 0;

    uint8_t uid[7] = {0};
    uint8_t uid_len = 0;
    // 100 ms timeout keeps the UI responsive when no tag is present.
    if (s_pn532.readPassiveTargetID(PN532_MIFARE_ISO14443A, uid, &uid_len, 100)) {
        int n = (uid_len < max_length) ? uid_len : max_length;
        memcpy(uid_buffer, uid, n);
        return n;
    }
    return 0;
}

// Raw block write for a Mifare Classic tag: authenticate block 4 with the factory default
// key and write up to 16 bytes. This is the block-write path the Adafruit library
// supports directly; NTAG2xx would use ntag2xx_WritePage instead.
int nfc_write_tag(const unsigned char *data, int length) {
    if (!s_ready) return -1;

    uint8_t uid[7] = {0};
    uint8_t uid_len = 0;
    if (!s_pn532.readPassiveTargetID(PN532_MIFARE_ISO14443A, uid, &uid_len, 500)) {
        return -1;  // no tag to write to
    }

    uint8_t default_key[6] = {0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF};
    const uint8_t block = 4;
    if (!s_pn532.mifareclassic_AuthenticateBlock(uid, uid_len, block, 0, default_key)) {
        return -1;  // authentication failed
    }

    uint8_t page[16] = {0};
    int n = (length < 16) ? length : 16;
    memcpy(page, data, n);
    if (!s_pn532.mifareclassic_WriteDataBlock(block, page)) {
        return -1;
    }
    return n;
}

#else
// ============================ SIMULATION (mock data) ============================
static const unsigned char MOCK_UID[7] = {0x04, 0xA2, 0x3B, 0x7C, 0x9D, 0x11, 0x22};

void nfc_init(void) {}

int nfc_read_tag(unsigned char *uid_buffer, int max_length) {
    int n = (7 < max_length) ? 7 : max_length;
    memcpy(uid_buffer, MOCK_UID, n);
    return n;   // a tag is always "present" in simulation
}

int nfc_write_tag(const unsigned char *data, int length) {
    (void)data;
    return (length < 16) ? length : 16;   // pretend the block write succeeded
}
#endif  // SIMULATION_MODE
