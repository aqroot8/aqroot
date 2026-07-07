---
tags: [research, competitors]
---

# Competitive Analysis

| Feature | Flipper Zero | Kode Dot | AQROOT |
|---|---|---|---|
| Display | Monochrome 1.4" LCD, button-nav only | 2.13" AMOLED touch, 502x410 | 2.13" AMOLED touch, 502x410 |
| MCU | STM32 | ESP32-S3 (P4 in final Kickstarter spec) | ESP32-S3 |
| NFC/RFID | Built-in | Add-on module | Built-in |
| Sub-GHz | Built-in (CC1101) | Add-on module | Built-in (SX1262) |
| LoRa | No | Add-on bundle | Built-in (SX1262, same chip as sub-GHz) |
| IR | Built-in | Not core | Built-in |
| Wi-Fi/BT | BT only | Built-in | Built-in |
| IMU | No | Built-in (9-axis) | Built-in (6-axis — sufficient for gestures/orientation) |
| Mic/speaker | No | Built-in | Built-in |
| GPIO | Yes (14-pin) | Yes (12 GPIO + magnetic connector) | Yes (12-pin, 3.3V) |
| Battery | ~2000mAh | 500mAh | 1000mAh |
| Dimensions | 100x43x20mm | 73x43x15mm | ~75x45x16mm target |
| Status | Shipping, mature | Crowdfunding, $3.25M+ raised, ships July 2026 | Concept/prototype stage |

## The gap
Nobody combines Flipper's fully built-in radio toolkit with Kode Dot's AMOLED touch/AI
hardware as one non-modular, fully open-source device. That's AQROOT's differentiation.

## Real risks to keep in mind
- Kode Dot has a 15,000+ backer head start and a forming open-source ecosystem (kodeOS).
- Packing NFC + LoRa/sub-GHz + Wi-Fi/BT + IMU onto one small board raises real RF
  coexistence, antenna placement, and battery-life engineering work.
