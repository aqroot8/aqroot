// AQROOT Demo -- MAX17048 safety/readiness host test.
#include <cstdint>
#include <cstdio>

#include "max17048_guard.h"

using namespace aqroot;

namespace {
class GaugeBus : public I2cBus {
 public:
  bool fail_write = false;
  bool fail_hibrt_read = false;
  bool fail_vcell_read = false;
  bool ignore_hibrt_write = false;
  uint16_t hibrt = 0x8030;
  uint16_t vcell = 0xC000;  // 3.840 V
  int hibrt_writes = 0;
  int hibrt_reads = 0;
  int vcell_reads = 0;

  bool write(uint8_t, const uint8_t *data, size_t length) override {
    if (fail_write) return false;
    if (length == 3 && data[0] == Max17048Guard::kRegHibrt) {
      ++hibrt_writes;
      if (!ignore_hibrt_write) {
        hibrt = uint16_t(data[1]) << 8 | uint16_t(data[2]);
      }
    }
    return true;
  }

  bool readRegister(uint8_t, uint8_t reg, uint8_t *data,
                    size_t length) override {
    if (length != 2) return false;
    if (reg == Max17048Guard::kRegHibrt) {
      ++hibrt_reads;
      if (fail_hibrt_read) return false;
      data[0] = uint8_t(hibrt >> 8);
      data[1] = uint8_t(hibrt);
      return true;
    }
    if (reg == Max17048Guard::kRegVcell) {
      ++vcell_reads;
      if (fail_vcell_read) return false;
      data[0] = uint8_t(vcell >> 8);
      data[1] = uint8_t(vcell);
      return true;
    }
    return false;
  }

  bool probe(uint8_t) override { return true; }
};

int failures = 0;
void claim(const char *name, bool ok) {
  std::printf("[%s] %s\n", ok ? "PASS" : "FAIL", name);
  if (!ok) ++failures;
}
}  // namespace

int main() {
  constexpr uint8_t kGauge = 0x36;

  {
    GaugeBus bus;
    Max17048Guard gauge(kGauge);
    float v = 0.0f;
    claim("gauge starts NOT READY", !gauge.activeReady());
    claim("VCELL is refused before verified active-mode configuration",
          !gauge.readVcell(bus, &v) && bus.vcell_reads == 0);
    claim("HIBRT=0 write+readback establishes readiness",
          gauge.configureActiveMode(bus) && gauge.activeReady() &&
          bus.hibrt == 0x0000 && bus.hibrt_writes == 1 &&
          bus.hibrt_reads >= 1);
    claim("plausible active-mode VCELL is accepted",
          gauge.readVcell(bus, &v) && v > 3.83f && v < 3.85f);
  }

  {
    GaugeBus bus;
    Max17048Guard gauge(kGauge);
    bus.fail_write = true;
    claim("failed HIBRT write cannot establish readiness",
          !gauge.configureActiveMode(bus) && !gauge.activeReady());
    bus.fail_write = false;
    float v = 0.0f;
    claim("plausible stale VCELL is refused after HIBRT configuration failure",
          !gauge.readVcell(bus, &v) && bus.vcell_reads == 0);
  }

  {
    GaugeBus bus;
    Max17048Guard gauge(kGauge);
    bus.ignore_hibrt_write = true;
    claim("HIBRT write without exact 0x0000 readback is refused",
          !gauge.configureActiveMode(bus) && !gauge.activeReady());
  }

  {
    GaugeBus bus;
    Max17048Guard gauge(kGauge);
    claim("setup for configuration-loss test", gauge.configureActiveMode(bus));
    bus.hibrt = 0x8030;
    float v = 0.0f;
    claim("later HIBRT drift invalidates readiness before VCELL is trusted",
          !gauge.readVcell(bus, &v) && !gauge.activeReady() &&
          bus.vcell_reads == 0);
  }

  {
    GaugeBus bus;
    Max17048Guard gauge(kGauge);
    claim("setup for implausible sample tests", gauge.configureActiveMode(bus));
    float v = 0.0f;
    bus.vcell = 0xFFFF;
    claim("all-ones VCELL fails closed and invalidates readiness",
          !gauge.readVcell(bus, &v) && !gauge.activeReady());
    claim("explicit reconfiguration is required after invalid sample",
          gauge.configureActiveMode(bus));
    bus.vcell = 0x0000;
    claim("all-zero VCELL fails closed", !gauge.readVcell(bus, &v));
    claim("reconfigure for over-range sample", gauge.configureActiveMode(bus));
    bus.vcell = uint16_t(4.51f / Max17048Guard::kVcellLsbV);
    claim("over-range plausible-looking VCELL fails closed",
          !gauge.readVcell(bus, &v));
  }

  {
    GaugeBus bus;
    Max17048Guard gauge(kGauge);
    claim("setup for VCELL read-failure test", gauge.configureActiveMode(bus));
    bus.fail_vcell_read = true;
    float v = 0.0f;
    claim("VCELL read failure invalidates readiness",
          !gauge.readVcell(bus, &v) && !gauge.activeReady());
    bus.fail_vcell_read = false;
    claim("read recovery alone cannot silently restore readiness",
          !gauge.readVcell(bus, &v));
    claim("explicit HIBRT reconfiguration/readback restores readiness",
          gauge.configureActiveMode(bus));
    claim("VCELL works again only after requalification",
          gauge.readVcell(bus, &v));
  }

  std::printf("\n%s -- %d failure(s)\n",
              failures ? "FAIL" : "PASS", failures);
  return failures ? 1 : 0;
}
