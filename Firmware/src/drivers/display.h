#pragma once
// Display driver interface — 2.13" AMOLED (RM69090 driver over SPI)
// Apps and the UI shell call only these functions, never touch registers directly.

void display_init(void);
void display_flush(int x1, int y1, int x2, int y2, const void *pixel_data);
void display_set_brightness(int percent);
