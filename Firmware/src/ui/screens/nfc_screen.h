#pragma once
// NFC screen — live tag UID readout and a raw block-write test via the NFC driver.
// (The driver underneath is still the wrong part — PN532/I2C pending an ST25R3916/SPI
// rewrite — but this screen talks only to the stable nfc.h interface, so it is unaffected.)
void nfc_screen_open(void);
