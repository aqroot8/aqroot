#pragma once
// Radio driver interface — SX1262 (certified module, e.g. Ebyte E22), via RadioLib
// Covers both LoRa and raw sub-GHz FSK/OOK/ASK.

typedef enum {
    RADIO_MODE_LORA,
    RADIO_MODE_SUBGHZ_RAW
} radio_mode_t;

void radio_init(void);
void radio_set_mode(radio_mode_t mode);
void radio_set_frequency(long frequency_hz);
int radio_transmit(const unsigned char *data, int length);
int radio_receive(unsigned char *buffer, int max_length);
