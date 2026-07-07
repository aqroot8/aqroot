#pragma once
// Audio driver interface — I2S digital mic + speaker/buzzer

void audio_init(void);
void audio_play_tone(int frequency_hz, int duration_ms);
int audio_record(unsigned char *buffer, int max_length);
