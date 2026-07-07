# AQROOT firmware skeleton

Starting driver-abstraction skeleton described in "03 - OS Architecture.md". Build order:
display/touch first, then the app-launcher shell (LVGL 8.3.x), then radio (SX1262 via
RadioLib), then NFC, then sensors/audio last.

Each header in src/drivers/ is a stable interface — apps and the UI shell call these
functions only, never touch hardware registers directly. This is what lets hardware swap
later without rewriting every app.

Prototype stage: dev-board/breakout parts (see 06 - BOM and Cost Tracker.md in the vault).
Final PCB stage: bare ESP32-S3 module + bare PN532 IC + certified SX1262 module, 4-layer
JLCPCB fab with assembly service.

Licensed under MIT (see LICENSE-FIRMWARE.md). Hardware design files are licensed under
CERN-OHL-S v2 (see LICENSE-HARDWARE.md).
