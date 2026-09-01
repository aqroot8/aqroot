# AQROOT Demo — Kickstarter Prototype Scope

## Purpose

AQROOT Demo is a Kickstarter / marketing prototype derived from AQROOT Full Beta v2.

It exists to produce a real working demonstration unit faster while preserving the Full Beta v2 production design separately.

AQROOT Demo must NOT overwrite or redefine the Full Beta v2 production architecture.

## Production reference

Full production design:
- branch: master
- frozen reference tag: beta-full-reference-v2

Demo development:
- branch: aqroot-demo
- workspace: /home/aqroot8/aqroot-demo

## Features that MUST remain functional

- ESP32-S3 main computer
- 16 MB flash / 8 MB PSRAM
- 3.5-inch touchscreen
- D-pad + A/B controls
- physical power switch
- recessed BOOT/recovery
- RGB status indicator

- Wi-Fi
- Bluetooth / BLE
- 433 MHz radio
- internal 433 MHz antenna
- 915 MHz LoRa radio
- one external 915 MHz antenna
- NFC operating from the 3.3 V path
- internal NFC antenna
- IR transmitter
- IR receiver

- speaker
- microphone
- BMI270 6-axis IMU
- microSD
- USB-C data/programming
- USB-C charging

- battery
- charger
- required battery/power safety architecture
- battery fuel gauge

- Qwiic / STEMMA QT connector

## Community Port — Demo requirements

The physical 1x24 Community Port connector MUST remain.

Demo implementation MUST retain:

- required GND contacts
- 3.3 V accessory power
- ONE usable 5 V accessory output
- software-controlled switched 3.3 V accessory power
- software-controlled switched 5 V accessory power
- SDA
- SCL
- Native GPIO A
- Native GPIO B
- Accessory Detect

Expansion GPIO objective:

- reduce XGPIO implementation if this safely simplifies the Demo PCB
- target approximately 2–4 working XGPIOs unless dependency analysis proves a different number is substantially simpler
- unused physical connector positions may remain electrically NC on AQROOT Demo
- Full Beta v2 production retains the complete final expansion architecture

## GPIO expanders

Full Beta v2 uses three PCAL9535A GPIO expanders.

For AQROOT Demo:

REDUCE IF POSSIBLE.

Before removing or DNP'ing any expander, produce a dependency map showing every internal AQROOT feature and Community Port signal that depends on U2, U3, and U23.

An expander may only be removed if all required Demo capabilities above remain functional.

Do not assume all three expanders serve only the Community Port.

## Demo accessory strategy

Do NOT design multiple accessory PCBs unless necessary.

Custom board to design:
- AQROOT Proto / Breadboard Adapter

Existing commercial modules may demonstrate:
- environmental sensing through Qwiic / STEMMA QT
- OLED / secondary display through Qwiic / STEMMA QT
- relay / control through the AQROOT Proto Board initially

Possible later polished accessory:
- AQROOT Relay / Control Board

The Demo PCB must support enough Community Port connectivity for the Proto Board and generic relay/control demonstrations.

## Already unnecessary / DNP

Keep existing Full Beta v2 DNP decisions where applicable.

The optional NFC 5 V PA boost is NOT required for AQROOT Demo.
NFC uses the selected 3.3 V path.

## Marketing integrity

AQROOT Demo is a pre-production prototype.

Do not claim that an electrically unimplemented Demo connector pin is functional.

Production capabilities may be described as planned/final-production capabilities when clearly distinguished from the prototype actually being demonstrated.

## Engineering objective

Optimize for:

1. working customer-visible Kickstarter features
2. reliable demonstration
3. minimum PCB/routing complexity
4. minimum additional custom hardware
5. easy restoration/evolution into Full Beta v2 production architecture

Do not carry difficult production-only routing into AQROOT Demo merely because it exists in Full Beta v2.
