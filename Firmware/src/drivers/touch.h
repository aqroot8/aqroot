#pragma once
// Touch driver interface — CST816-series capacitive touch controller over I2C

typedef struct {
    int x;
    int y;
    int pressed;
} touch_point_t;

void touch_init(void);
touch_point_t touch_get_point(void);
