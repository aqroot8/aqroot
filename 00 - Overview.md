---
tags: [hardware, project, aqroot]
status: concept
---

# AQROOT — Overview

**AQROOT = Access + Query the Root Layer**
- Access: connect to GPIO, NFC, RF, IR, and expansion modules
- Query: read, inspect, test, debug, scan
- Root: operates at the low-level hardware/system layer

Open-source handheld device combining radio tools (NFC, DUAL sub-GHz/LoRa radios, IR) with
a 2.8in IPS touch UI (ILI9341), built on a custom ESP32-S3 firmware/OS. Positioned as a
differentiator against Flipper Zero (radio-only, no touch/WiFi) and Kode Dot (touch/AI-first,
radio features sold as paid add-ons) by shipping ALL of these built-in, no paid modules
required, fully open-source hardware and firmware. The built-in dual-radio base (CC1101 +
SX1262) is the core competitive wedge.

Target scale: ~122x61x23.5mm ("Field Slate" v3 enclosure), 135-165g — a field tool, not a
keyfob. See [[15 - Enclosure Field Slate v3]].

## Links
- [[01 - Hardware Core]]
- [[02 - Add-on Modules]]
- [[03 - OS Architecture]]
- [[04 - Competitive Analysis]]
- [[05 - Design Decisions Log]]
- [[06 - BOM and Cost Tracker]]
- [[07 - Build TODO Tracker]]
- [[08 - Kickstarter and Review Strategy]]
- [[09 - Alpha Pin Bus Map]]
- [[10 - Beta Pin Map]]
- [[11 - Beta Pin Map v0.2]]
- [[12 - RF and Antenna Plan v0.1]]
- [[13 - Power Budget and Battery Runtime v0.1]]
- [[14 - RootProbe Interface v0.1]]
- [[15 - Enclosure Field Slate v3]]
- [[Alpha-Tests/HARDWARE-NOTES]]
- [[Firmware/README]]

## First design concept
![[first-design-concept.png]]
Rendered concept: rugged single-shell body, GPIO breakout on top edge and side edge,
USB-C on the side, D-pad + home/back + confirm buttons below the screen, dashboard UI
showing Scan (Sub-GHz), NFC, Infrared, GPIO, Bluetooth, and Tools tiles, plus a live
signal monitor and NFC tag reader panel. This may change as the design evolves — treat
as a reference, not a final spec.
