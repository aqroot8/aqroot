# D-766 — round-2 firmware fail-closed closure

Authority: branch `cto/d766-fw-round2`, based on D-765 hardware authority.

Round-2 independent review reproduced two integration defects that the existing driver-level tests did not close:

1. MCU warm reset waited for Serial/USB and an I2C scan before writing the powered PCAL9535A expanders back to their board-safe latches.
2. If the U3 input-port read failed, `ACC_POWER_FAULT_N` became unobservable and `service()` returned false without attempting accessory shutdown.

The repaired Demo entry point opens/recoveries I2C and writes both complete safe latches before `Serial.begin`, the optional three-second console wait, scanning, or peripheral discovery. The Arduino bus performs up to nine SCL recovery clocks plus STOP before `Wire.begin` and fails closed if SDA/SCL remain stuck.

Loss of the U3 fault-input read now latches `fault_observability_lost`, attempts both 5 V and 3.3 V shutdown paths, blocks accessory re-enable, and clears the latch only after a later clean U3 input read. Low/unknown MAX17048 cell voltage also fail-closes accessories, with the Demo operating floor at 3.50 V.

A further CTO check closed the byte-boundary failure case the review mentioned: a failed two-byte PCAL output write now invalidates the software shadow because one port byte may have reached hardware. Safety shutdown then attempts an absolute complete safe-latch write rather than another blind read/modify/write.

Verification:
- expander host test: 85 claims, 0 failures;
- destructive expander controls: 10/10 caught;
- SPI-B host test: 22 claims, 0 failures; 3/3 controls caught;
- new H7 integration gate proves safe PCAL state precedes console/discovery and refuses an early-Serial control;
- all four PlatformIO environments build successfully.

Evidence: `hardware/demo/manufacturing/evidence/d766-firmware-hw-map-contract.json`.
