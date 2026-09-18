// AQROOT Demo -- the SPI bus B arbiter test.
//
// Two rules govern the bus U7, U8 and U9 share, and until D-748 both were
// comments.  A comment cannot refuse; this proves the class does.
//
//   BUS RULE  exactly ONE chip select asserted at a time.  Two selected devices
//             drive MISO against each other and the symptom looks like a
//             marginal trace, not a firmware bug.
//   RF RULE   exactly ONE transceiver keyed at a time -- the one-TX-at-a-time
//             discipline the retained dual-radio Demo scope requires.  The
//             915 MHz module is a +22 dBm part sharing a supply and a ground
//             return with the 433 MHz one and with the NFC field driver.
//
//     g++ -std=c++17 -I ../src/hw -o /tmp/t test_spi_bus_b.cpp && /tmp/t

#include <cstdio>
#include <vector>

#include "aqroot_spi_bus_b.h"

using namespace aqroot;

namespace {

class RecordingSelects : public ChipSelects {
 public:
  std::vector<std::pair<SpiBDevice, bool>> log;
  int asserted = 0;
  int max_concurrent = 0;

  void driveSelect(SpiBDevice device, bool state) override {
    log.emplace_back(device, state);
    asserted += state ? 1 : -1;
    if (asserted > max_concurrent) max_concurrent = asserted;
  }
};

int g_failures = 0;
void check(const char *claim, bool ok) {
  std::printf("[%s] %s\n", ok ? "PASS" : "FAIL", claim);
  if (!ok) ++g_failures;
}

}  // namespace

int main() {
  std::printf("AQROOT Demo -- SPI bus B arbiter\n\n");

  {
    RecordingSelects selects;
    SpiBusB bus(selects);
    check("a first select is accepted", bus.select(SpiBDevice::Cc1101));
    check("a SECOND, different select is REFUSED",
          !bus.select(SpiBDevice::Sx1262));
    check("the refused device's select line was never driven",
          selects.log.size() == 1 && selects.log[0].first == SpiBDevice::Cc1101);
    // NOT idempotent, deliberately: a nested Hold on the same device would
    // otherwise release the bus at the INNER scope's exit and leave the outer
    // scope transacting against a deselected part.
    check("re-selecting the SAME device while held is REFUSED",
          !bus.select(SpiBDevice::Cc1101));
    bus.release();
    check("after release the bus is free", bus.select(SpiBDevice::St25r3916));
    bus.release();
    check("no two selects were ever asserted at once",
          selects.max_concurrent == 1);
    check("every assert was matched by a release", selects.asserted == 0);
  }

  {
    // The RAII hold is what makes a probe that returns early still release.
    RecordingSelects selects;
    SpiBusB bus(selects);
    {
      SpiBusB::Hold hold(bus, SpiBDevice::Sx1262);
      check("Hold takes the bus", hold.ok());
      SpiBusB::Hold nested(bus, SpiBDevice::Cc1101);
      check("a nested Hold on another device is REFUSED", !nested.ok());
      SpiBusB::Hold same(bus, SpiBDevice::Sx1262);
      check("a nested Hold on the SAME device is REFUSED", !same.ok());
    }
    check("the outer Hold still owned the bus when the inner scopes ended",
          selects.asserted == 0);
    check("the bus is released when the Hold leaves scope",
          bus.selected() == SpiBDevice::None);
    check("a refused Hold released nothing it did not take",
          selects.asserted == 0 && selects.max_concurrent == 1);
  }

  {
    RecordingSelects selects;
    SpiBusB bus(selects);
    check("the first transmitter is keyed", bus.beginTransmit(SpiBDevice::Sx1262));
    check("the OTHER radio is REFUSED while it is keyed",
          !bus.beginTransmit(SpiBDevice::Cc1101));
    check("re-keying the SAME transmitter is REFUSED -- same re-entrancy rule",
          !bus.beginTransmit(SpiBDevice::Sx1262));
    check("the NFC field driver is refused too -- it is a transmitter",
          !bus.beginTransmit(SpiBDevice::St25r3916));
    bus.endTransmit(SpiBDevice::Cc1101);
    check("ending a transmit that was never started does not free the bus",
          bus.transmitting() == SpiBDevice::Sx1262);
    bus.endTransmit(SpiBDevice::Sx1262);
    check("the other radio may key once the first has ended",
          bus.beginTransmit(SpiBDevice::Cc1101));
  }

  {
    RecordingSelects selects;
    SpiBusB bus(selects);
    check("SpiBDevice::None is never a valid select", !bus.select(SpiBDevice::None));
    check("SpiBDevice::None is never a valid transmitter",
          !bus.beginTransmit(SpiBDevice::None));
    bus.release();
    check("releasing an unheld bus drives nothing", selects.log.empty());
  }

  std::printf("\n%s -- %d failure(s)\n", g_failures ? "FAIL" : "PASS", g_failures);
  return g_failures == 0 ? 0 : 1;
}
