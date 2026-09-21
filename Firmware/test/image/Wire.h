#pragma once
#include <stdint.h>
#include <stddef.h>
#include "Arduino.h"

// D-790 / D789-A04.  The image's `ArduinoI2cBus` talks to this.  The host test
// installs a BOARD MODEL behind it -- two PCAL9535As with PHYSICAL output
// latches and one MAX17048 with real registers -- so a write that "NACKs"
// really does leave the latch where it was.
namespace aqroot_hal {

struct I2cModel {
  virtual ~I2cModel() {}
  virtual bool write(uint8_t addr, const uint8_t *data, size_t len) = 0;
  virtual bool readRegister(uint8_t addr, uint8_t reg, uint8_t *data,
                            size_t len) = 0;
  virtual bool probe(uint8_t addr) = 0;
};

inline I2cModel *&model() {
  static I2cModel *m = nullptr;
  return m;
}

}  // namespace aqroot_hal

class HostWire {
 public:
  bool begin(int = -1, int = -1, uint32_t = 100000) { return opened_ = true; }
  void end() { opened_ = false; }
  void setClock(uint32_t hz) { clock_hz_ = hz; }
  uint32_t clock() const { return clock_hz_; }

  void beginTransmission(uint8_t addr) {
    addr_ = addr;
    tx_.clear();
  }
  size_t write(uint8_t b) { tx_.push_back(b); return 1; }
  size_t write(const uint8_t *b, size_t n) {
    for (size_t i = 0; i < n; ++i) tx_.push_back(b[i]);
    return n;
  }
  uint8_t endTransmission(bool stop = true) {
    (void)stop;
    auto *m = aqroot_hal::model();
    if (!m) return 4;
    if (tx_.empty()) return m->probe(addr_) ? 0 : 2;
    pending_reg_ = tx_[0];
    if (tx_.size() == 1) {
      // address+register only: this is the write phase of a register read.
      return m->probe(addr_) ? 0 : 2;
    }
    return m->write(addr_, tx_.data(), tx_.size()) ? 0 : 2;
  }
  uint8_t requestFrom(uint8_t addr, uint8_t len, bool stop = true) {
    (void)stop;
    auto *m = aqroot_hal::model();
    rx_.assign(len, 0xFF);
    rx_pos_ = 0;
    if (!m || !m->readRegister(addr, pending_reg_, rx_.data(), len)) {
      rx_.clear();
      return 0;
    }
    return len;
  }
  int available() { return int(rx_.size() - rx_pos_); }
  int read() {
    if (rx_pos_ >= rx_.size()) return -1;
    return int(rx_[rx_pos_++]);
  }

 private:
  bool opened_ = false;
  uint32_t clock_hz_ = 0;
  uint8_t addr_ = 0;
  uint8_t pending_reg_ = 0;
  std::vector<uint8_t> tx_;
  std::vector<uint8_t> rx_;
  size_t rx_pos_ = 0;
};
extern HostWire Wire;
