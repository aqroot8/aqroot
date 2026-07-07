// AQROOT — display driver (LovyanGFX) + LVGL glue.
//
// ============================ PLACEHOLDER PANEL CONFIG ============================
// The LGFX config below drives a GENERIC ILI9341 SPI panel. This is a STAND-IN for the
// final 2.13" RM69090-based AMOLED (502x410), which is not yet sourced. When the AMOLED
// arrives, replace the Panel_ILI9341 instance + its config block with the RM69090 init
// sequence (a QSPI/SPI AMOLED panel class, its own gamma/brightness registers, and
// 502x410 geometry). Everything above this driver — LVGL, the launcher, every screen —
// is resolution-independent and needs no change.
//
// The same ILI9341 config is what the Wokwi simulation renders, so this file compiles and
// runs identically on real hardware (placeholder panel) and in the browser simulator.
// =================================================================================

#include "display.h"
#include "../config.h"

#include <Arduino.h>
#include <lvgl.h>

// LGFX_USE_V1 is defined project-wide in platformio.ini build_flags.
#include <LovyanGFX.hpp>

// --- LovyanGFX device definition for the placeholder SPI panel ---
class LGFX : public lgfx::LGFX_Device {
    lgfx::Panel_ILI9341 _panel;   // PLACEHOLDER: swap for an RM69090 AMOLED panel class
    lgfx::Bus_SPI       _bus;
    lgfx::Light_PWM     _light;

public:
    LGFX() {
        {
            auto cfg = _bus.config();
            cfg.spi_host   = (spi_host_device_t)DISP_SPI_HOST;
            cfg.spi_mode   = 0;
            cfg.freq_write = 40000000;
            cfg.freq_read  = 16000000;
            cfg.spi_3wire  = false;
            cfg.use_lock   = true;
            cfg.dma_channel = SPI_DMA_CH_AUTO;
            cfg.pin_sclk   = DISP_SCK;
            cfg.pin_mosi   = DISP_MOSI;
            cfg.pin_miso   = DISP_MISO;
            cfg.pin_dc     = DISP_DC;
            _bus.config(cfg);
            _panel.setBus(&_bus);
        }
        {
            auto cfg = _panel.config();
            cfg.pin_cs        = DISP_CS;
            cfg.pin_rst       = DISP_RST;
            cfg.pin_busy      = -1;
            cfg.panel_width   = DISPLAY_WIDTH;
            cfg.panel_height  = DISPLAY_HEIGHT;
            cfg.offset_x      = 0;
            cfg.offset_y      = 0;
            cfg.offset_rotation = 0;
            cfg.readable      = false;
            cfg.invert        = false;
            cfg.rgb_order     = false;
            cfg.dlen_16bit    = false;
            cfg.bus_shared    = true;   // SPI bus is shared with the SX1262 radio
            _panel.config(cfg);
        }
        {
            auto cfg = _light.config();
            cfg.pin_bl      = DISP_BL;
            cfg.invert      = false;
            cfg.freq        = 12000;
            cfg.pwm_channel = 7;
            _light.config(cfg);
            _panel.setLight(&_light);
        }
        setPanel(&_panel);
    }
};

static LGFX lcd;

// --- LVGL draw buffers (two partial buffers, 1/8 screen each) ---
static lv_disp_draw_buf_t draw_buf;
static lv_color_t buf_a[DISPLAY_WIDTH * DISPLAY_HEIGHT / 8];
static lv_color_t buf_b[DISPLAY_WIDTH * DISPLAY_HEIGHT / 8];
static lv_disp_drv_t disp_drv;

// LVGL flush callback: hands the dirty rectangle to display_flush() then signals ready.
static void lvgl_flush_cb(lv_disp_drv_t *drv, const lv_area_t *area, lv_color_t *color_p) {
    display_flush(area->x1, area->y1, area->x2, area->y2, color_p);
    lv_disp_flush_ready(drv);
}

void display_init(void) {
    lcd.init();
    lcd.setRotation(0);          // portrait 240x320 on the placeholder panel
    lcd.setSwapBytes(true);      // RGB565 byte order for LVGL -> SPI
    lcd.fillScreen(0x0000);
    display_set_brightness(100);

    lv_init();
    lv_disp_draw_buf_init(&draw_buf, buf_a, buf_b, DISPLAY_WIDTH * DISPLAY_HEIGHT / 8);

    lv_disp_drv_init(&disp_drv);
    disp_drv.hor_res  = DISPLAY_WIDTH;
    disp_drv.ver_res  = DISPLAY_HEIGHT;
    disp_drv.flush_cb = lvgl_flush_cb;
    disp_drv.draw_buf = &draw_buf;
    lv_disp_drv_register(&disp_drv);
    // LVGL timing comes from LV_TICK_CUSTOM (Arduino millis) — see include/lv_conf.h.
}

// Push a block of RGB565 pixels to the panel. Called by LVGL's flush callback; the swap
// set in display_init() converts LVGL's little-endian buffer to the panel byte order.
void display_flush(int x1, int y1, int x2, int y2, const void *pixel_data) {
    const int w = x2 - x1 + 1;
    const int h = y2 - y1 + 1;
    lcd.pushImage(x1, y1, w, h, static_cast<const uint16_t *>(pixel_data));
}

void display_set_brightness(int percent) {
    if (percent < 0)   percent = 0;
    if (percent > 100) percent = 100;
    lcd.setBrightness((percent * 255) / 100);
}
