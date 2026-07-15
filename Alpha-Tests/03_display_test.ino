// AQROOT Alpha - Test 3: ILI9341 display test via LovyanGFX (PASSED)
// 2.8" TFT SPI 240x320 capacitive touch board.
// Requires the LovyanGFX library.
#define LGFX_USE_V1
#include <LovyanGFX.hpp>
class LGFX : public lgfx::LGFX_Device {
  lgfx::Panel_ILI9341 _panel;
  lgfx::Bus_SPI _bus;
public:
  LGFX() {
    { auto cfg = _bus.config();
      cfg.spi_host = SPI2_HOST;
      cfg.spi_mode = 0;
      cfg.freq_write = 40000000;
      cfg.pin_sclk = 12;
      cfg.pin_mosi = 11;
      cfg.pin_miso = 13;
      cfg.pin_dc   = 14;
      _bus.config(cfg);
      _panel.setBus(&_bus);
    }
    { auto cfg = _panel.config();
      cfg.pin_cs   = 10;
      cfg.pin_rst  = 21;
      cfg.panel_width  = 240;
      cfg.panel_height = 320;
      _panel.config(cfg);
    }
    setPanel(&_panel);
  }
};
LGFX display;
void setup() {
  Serial.begin(115200);
  display.init();
  display.setRotation(0);
  display.fillScreen(TFT_BLACK);
  display.setTextColor(TFT_WHITE);
  display.setTextSize(3);
  display.setCursor(20, 40);
  display.println("AQROOT");
  display.setTextSize(2);
  display.setCursor(20, 100);
  display.println("Display OK!");
  display.fillRect(20, 150, 60, 60, TFT_RED);
  display.fillRect(90, 150, 60, 60, TFT_GREEN);
  display.fillRect(160, 150, 60, 60, TFT_BLUE);
  Serial.println("Display test done");
}
void loop() {}
