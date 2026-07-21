#pragma once
// Touch driver interface — FT6236-family capacitive touch controller over I2C @ 0x38
// (Alpha-validated, LOCKED). Was previously written against a CST816 @ 0x15; the two share
// the same read layout at register 0x02, so only the address changed.

typedef struct {
    int x;
    int y;
    int pressed;
} touch_point_t;

void touch_init(void);
touch_point_t touch_get_point(void);
