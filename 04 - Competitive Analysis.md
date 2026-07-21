---
tags: [research, competitors]
---

# Competitive Analysis

| Feature | Flipper Zero | Kode Dot | AQROOT |
|---|---|---|---|
| Display | Monochrome 1.4" LCD, button-nav only | 2.13" AMOLED touch, 502x410 | 2.8" IPS LCD touch, 240x320 (AMOLED = stretch goal) |
| MCU | STM32 | ESP32-S3 (P4 in final Kickstarter spec) | ESP32-S3 |
| NFC/RFID | Built-in | Add-on module | Built-in (ST25R3916) |
| Sub-GHz | Built-in (CC1101) | Add-on module | **Built-in (CC1101)** |
| LoRa | No | Add-on bundle | **Built-in (SX1262 — a SECOND dedicated radio)** |
| IR | Built-in | Not core | Built-in |
| Wi-Fi/BT | BT only | Built-in | Built-in |
| IMU | No | Built-in (9-axis) | Built-in (6-axis BMI270 — sufficient for gestures/orientation) |
| Mic/speaker | No | Built-in | Built-in (ICS-43434 + MAX98357A) |
| GPIO | Yes (14-pin) | Yes (12 GPIO + magnetic connector) | Yes (~7 slow GPIO, 3.3V) + reserved high-speed RootProbe interface |
| Battery | ~2000mAh | 500mAh | 2000mAh |
| Dimensions | 100x43x20mm | 73x43x15mm | ~122x61x23.5mm |
| Status | Shipping, mature | Crowdfunding, $3.25M+ raised, ships July 2026 | Concept/prototype stage |

## The gap
Nobody combines Flipper's fully built-in radio toolkit with Kode Dot's touch/AI hardware as
one non-modular, fully open-source device. That's AQROOT's differentiation.

**The dual-radio base is the wedge.** Flipper has CC1101 but no LoRa. Kode Dot sells both
sub-GHz and LoRa as PAID ADD-ONS. AQROOT ships CC1101 *and* SX1262 built in, at no extra
cost, on a validated shared-SPI architecture — that's the one row in this table where AQROOT
beats both competitors outright rather than trading blows.

**Honest reads on the other rows:** AQROOT is physically the largest of the three, and the
baseline display is an IPS LCD against Kode Dot's AMOLED. Those are deliberate trades — the
larger envelope is what makes a serviceable 433MHz antenna, a 2000mAh cell, and a real
button cluster coexist, and the LCD removes the biggest technical risk (QSPI AMOLED
bring-up) while saving ~$25/unit. Don't paper over either in campaign material.

## Real risks to keep in mind
- Kode Dot has a 15,000+ backer head start and a forming open-source ecosystem (kodeOS).
- Packing NFC + LoRa/sub-GHz + Wi-Fi/BT + IMU onto one small board raises real RF
  coexistence, antenna placement, and battery-life engineering work.
