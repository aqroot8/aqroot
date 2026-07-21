#pragma once
// NFC driver interface.
//
// !! WRONG PART: this interface is currently implemented against a PN532 over I2C. The
// LOCKED NFC front-end is the ST25R3916 over SPI (X-NUCLEO-NFC06A1 in Alpha, IC-ID 0x2A
// confirmed). Wrong chip AND wrong bus — see "05 - Design Decisions Log.md".
//
// The three functions below are the intended stable interface and should survive the
// rewrite unchanged; only the implementation swaps. Rewrite tracked in
// "07 - Build TODO Tracker.md".

void nfc_init(void);
int nfc_read_tag(unsigned char *uid_buffer, int max_length);
int nfc_write_tag(const unsigned char *data, int length);
