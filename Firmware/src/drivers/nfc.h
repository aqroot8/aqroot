#pragma once
// NFC driver interface — PN532 (breakout for prototype, bare IC + matching network for
// final PCB)

void nfc_init(void);
int nfc_read_tag(unsigned char *uid_buffer, int max_length);
int nfc_write_tag(const unsigned char *data, int length);
