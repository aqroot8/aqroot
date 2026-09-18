#pragma once
// AQROOT Demo -- the display, brought up far enough to prove its pin map.
//
// PANEL: EastRising ER-TFT035IPS-6, 3.5" IPS, 320x480, ILI9488 COG, 4-wire SPI
// on bus A, through the 50-pin Hirose FH69 at J1.  DEVICE_SPEC section 2 is the
// authority; the KiCad symbol's "ILI9341" text is stale placeholder text and the
// legacy src/config.h repeated it -- D-747 corrected both.
//
// TWO AS-BUILT FACTS SHAPE THIS FILE
//
//   1  THE PANEL IS WRITE-ONLY.  R112 0R is DNP, so DISP_SDO never reaches
//      SPI_A_MISO and there is no read-back path -- no device ID, no register
//      verify, no framebuffer read.  Every claim this file can make is made by
//      the operator's eyes, which is why `fillScreen` exists at all.
//   2  ILI9488 OVER 4-WIRE SPI IS 18 BITS PER PIXEL.  The part does NOT accept
//      the 16-bit RGB565 pixel format over the serial interface that its
//      ILI9341 cousin does; COLMOD must be 0x66 and every pixel is three bytes.
//      Writing RGB565 produces a rolling colour mess, which is exactly the kind
//      of failure that gets blamed on a bad panel.
//
// RESET is not an MCU pin -- it is U2.P04 through the expander -- so the caller
// releases it (DemoExpanders::setDisplayReset) before calling begin().

#include <stdint.h>

#ifdef ARDUINO
#include <Arduino.h>
#include <SPI.h>

#include "aqroot_demo_board.h"

namespace aqroot {

static const uint16_t kDisplayWidth = 320;
static const uint16_t kDisplayHeight = 480;

class Ili9488 {
 public:
  void writeCommand(uint8_t command) {
    digitalWrite(AQROOT_PIN_DISP_DC, LOW);
    digitalWrite(AQROOT_PIN_DISP_CS_N, LOW);
    SPI.transfer(command);
    digitalWrite(AQROOT_PIN_DISP_CS_N, HIGH);
  }

  void writeData(const uint8_t *data, size_t length) {
    digitalWrite(AQROOT_PIN_DISP_DC, HIGH);
    digitalWrite(AQROOT_PIN_DISP_CS_N, LOW);
    for (size_t i = 0; i < length; ++i) SPI.transfer(data[i]);
    digitalWrite(AQROOT_PIN_DISP_CS_N, HIGH);
  }

  void writeCommand(uint8_t command, const uint8_t *data, size_t length) {
    writeCommand(command);
    if (length) writeData(data, length);
  }

  // The STRUCTURAL init only: sleep out, pixel format, orientation, display on.
  //
  // GAMMA AND POWER TABLES ARE DELIBERATELY ABSENT.  0xE0/0xE1/0xC0/0xC1/0xC5
  // are panel-specific and belong to EastRising's initialisation code for this
  // exact module; copying a generic ILI9488 breakout's values here would produce
  // an image that looks plausible and is wrong.  Fit them at first article from
  // the panel vendor's sequence.  Without them the panel still lights and still
  // shows the right geometry, which is all a pin-map proof needs.
  void begin(uint32_t hz = 20000000) {
    // SPI-A is shared with the microSD; hold the card deselected throughout.
    digitalWrite(AQROOT_PIN_SD_CS_N, HIGH);
    pinMode(AQROOT_PIN_DISP_DC, OUTPUT);
    pinMode(AQROOT_PIN_DISP_CS_N, OUTPUT);
    digitalWrite(AQROOT_PIN_DISP_CS_N, HIGH);

    SPI.begin(AQROOT_PIN_SPI_A_SCK, AQROOT_PIN_SPI_A_MISO, AQROOT_PIN_SPI_A_MOSI,
              -1);
    SPI.beginTransaction(SPISettings(hz, MSBFIRST, SPI_MODE0));

    writeCommand(0x01);          // SWRESET -- the panel needs 120 ms after it
    delay(120);

    const uint8_t interface_mode = 0x00;   // B0: SPI, DE polarity default
    writeCommand(0xB0, &interface_mode, 1);

    const uint8_t pixel_format = 0x66;     // 3Ah: 18 bits/pixel.  NOT 0x55.
    writeCommand(0x3A, &pixel_format, 1);

    // 36h MADCTL 0x48 = MX | BGR: portrait, 320 across by 480 down, with the
    // BGR bit set because this panel's colour filter order is BGR.  If red and
    // blue come out swapped at first article, this bit is the one to move.
    const uint8_t madctl = 0x48;
    writeCommand(0x36, &madctl, 1);

    const uint8_t inversion = 0x02;        // B4h: 2-dot inversion
    writeCommand(0xB4, &inversion, 1);
    const uint8_t function[2] = {0x02, 0x02};  // B6h
    writeCommand(0xB6, function, 2);

    writeCommand(0x11);          // SLPOUT
    delay(120);
    writeCommand(0x29);          // DISPON
    delay(20);
    SPI.endTransaction();
  }

  void setWindow(uint16_t x0, uint16_t y0, uint16_t x1, uint16_t y1) {
    const uint8_t columns[4] = {uint8_t(x0 >> 8), uint8_t(x0), uint8_t(x1 >> 8),
                                uint8_t(x1)};
    const uint8_t pages[4] = {uint8_t(y0 >> 8), uint8_t(y0), uint8_t(y1 >> 8),
                              uint8_t(y1)};
    writeCommand(0x2A, columns, 4);   // CASET
    writeCommand(0x2B, pages, 4);     // PASET
    writeCommand(0x2C);               // RAMWR
  }

  // Solid fill.  Three bytes per pixel -- see the header note.
  void fillScreen(uint8_t red, uint8_t green, uint8_t blue,
                  uint32_t hz = 20000000) {
    SPI.beginTransaction(SPISettings(hz, MSBFIRST, SPI_MODE0));
    setWindow(0, 0, kDisplayWidth - 1, kDisplayHeight - 1);
    uint8_t line[kDisplayWidth * 3];
    for (uint16_t x = 0; x < kDisplayWidth; ++x) {
      line[x * 3] = red;
      line[x * 3 + 1] = green;
      line[x * 3 + 2] = blue;
    }
    digitalWrite(AQROOT_PIN_DISP_DC, HIGH);
    digitalWrite(AQROOT_PIN_DISP_CS_N, LOW);
    for (uint16_t y = 0; y < kDisplayHeight; ++y) {
      SPI.writeBytes(line, sizeof(line));
    }
    digitalWrite(AQROOT_PIN_DISP_CS_N, HIGH);
    SPI.endTransaction();
  }

  // Four quadrants in four colours plus a white margin.  A single flat fill
  // cannot tell a working panel from one whose CASET/PASET are being ignored;
  // this one shows the geometry, the orientation and the colour order at once.
  void testPattern(uint32_t hz = 20000000) {
    SPI.beginTransaction(SPISettings(hz, MSBFIRST, SPI_MODE0));
    const uint8_t colours[4][3] = {{0xFC, 0x00, 0x00}, {0x00, 0xFC, 0x00},
                                   {0x00, 0x00, 0xFC}, {0xFC, 0xFC, 0xFC}};
    for (uint8_t quadrant = 0; quadrant < 4; ++quadrant) {
      const uint16_t x0 = (quadrant & 1) ? kDisplayWidth / 2 : 0;
      const uint16_t y0 = (quadrant & 2) ? kDisplayHeight / 2 : 0;
      const uint16_t x1 = uint16_t(x0 + kDisplayWidth / 2 - 1);
      const uint16_t y1 = uint16_t(y0 + kDisplayHeight / 2 - 1);
      setWindow(x0, y0, x1, y1);
      uint8_t line[(kDisplayWidth / 2) * 3];
      for (uint16_t x = 0; x < kDisplayWidth / 2; ++x) {
        line[x * 3] = colours[quadrant][0];
        line[x * 3 + 1] = colours[quadrant][1];
        line[x * 3 + 2] = colours[quadrant][2];
      }
      digitalWrite(AQROOT_PIN_DISP_DC, HIGH);
      digitalWrite(AQROOT_PIN_DISP_CS_N, LOW);
      for (uint16_t y = y0; y <= y1; ++y) SPI.writeBytes(line, sizeof(line));
      digitalWrite(AQROOT_PIN_DISP_CS_N, HIGH);
    }
    SPI.endTransaction();
  }

  void end() { SPI.end(); }
};

}  // namespace aqroot
#endif  // ARDUINO
