# AQROOT Beta KiCad Project

This directory contains the canonical KiCad 10 project for the AQROOT Beta main board.

## Current design state

* Digital pin architecture: LOCKED to Beta Pin Map v0.2.4
* Schematic capture: IN PROGRESS
* PCB placement and routing: DO NOT START
* Schematic freeze: BLOCKED pending ERC, footprint audit, RF review, DFM review, and unresolved part selections

## Locked GPIO expanders (v0.2.4, 2026-07-27)

Both I2C GPIO expanders are Texas Instruments TCA9535PWR, replacing the MCP23017.

* U60 = TCA9535PWR, I2C 0x20 (internal: buttons + control), straps A2=GND A1=GND A0=GND
* U61 = TCA9535PWR, I2C 0x21 (community header), straps A2=GND A1=GND A0=+3V3
* Package = PW, TSSOP-24, 0.65 mm pitch
* Symbol = `Interface_Expansion:TCA9535PWR`
* Footprint = `Package_SO:TSSOP-24_4.4x7.8mm_P0.65mm` (NOT yet audited — see rules)
* One open-drain active-low `/INT` per device, both wired-OR onto `WAKE_INT_N` -> ESP32 GPIO21

TCA9535PWR is datasheet-trusted and receives its first hardware validation on Beta. The Alpha
bench test that passed was an MCP23017, a different part.

## Explicit unresolved parts

* External community-header I2C isolator or bus switch
* ACC_PWR_EN accessory load switch

## Rules

* Do not generate or modify KiCad schematic or PCB files automatically.
* KiCad files will be created manually in KiCad 10.0.3.
* Do not assign unverified footprints. The U60/U61 TSSOP-24 footprint above is assigned but NOT
  yet verified against the TI datasheet drawing — audit it before freeze.
* Do not begin PCB routing until the full schematic passes review and ERC.
* Preserve the authoritative GPIO assignments from Beta Pin Map v0.2.4.
* Do not reintroduce MCP23017 nomenclature (GPAn/GPBn, INTA/INTB, IODIR, GPPU, GPINTEN, INTF,
  INTCAP, IOCON, DEFVAL, INTCON). The TCA9535 register set is 0x00-0x07 only.
