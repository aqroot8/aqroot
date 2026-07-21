#pragma once
// Display driver interface — 2.8" IPS ILI9341, 240x320, 4-wire SPI (the real Beta panel).
// A 2.13" RM69090 AMOLED is a Kickstarter stretch-goal board revision, not the baseline.
// Apps and the UI shell call only these functions, never touch registers directly.

void display_init(void);
void display_flush(int x1, int y1, int x2, int y2, const void *pixel_data);
void display_set_brightness(int percent);
