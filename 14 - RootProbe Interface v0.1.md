---
tags: [hardware, beta, rootprobe, expansion, phase2]
status: interface-design-draft
---

# AQROOT RootProbe — Accessory Interface Spec v0.1

**What this is:** the electrical + mechanical interface between the AQROOT main board and
the RootProbe coprocessor accessory. RootProbe is the flagship add-on: an intelligent
logic-analyzer / bus-sniffer / GPIO-tooling module aimed at the security audience.

**Why an interface spec now:** the three-way review established that RootProbe CANNOT be raw
MCP23017 expander pins (I2C-mediated GPIO is far too slow for logic-analysis). RootProbe must
be its own coprocessor (RP2040-class MCU) that does the fast capture locally and talks to
AQROOT over a defined board-to-board link. This spec defines that link so the main-board
connector can be placed during PCB layout. RootProbe itself is a Phase-2 product; this spec
only reserves the interface on the main board.

---

## 1. Architecture (why a coprocessor, restated)

The main ESP32-S3 does NOT do the high-speed capture. RootProbe's own MCU does:
- High-speed sample capture (logic analyzer, bus sniffing).
- Triggering and protocol decode.
- Local sample buffering (RAM on the RootProbe board).
- Voltage-level protection / translation on the probe tips (target signals may be 1.8-5V).

AQROOT is the "host + display + storage + UI"; RootProbe is the "capture engine." They talk
over a moderate-speed link — AQROOT sends commands ("start capture, trigger on X"), RootProbe
streams back decoded results or buffered samples. The heavy timing work stays local to
RootProbe, so the link between them does NOT need to carry raw high-speed captures in real time.

This mirrors how real logic analyzers work (capture pod + host).

---

## 2. Signals crossing the interface

Minimum viable interface (what the main-board connector must carry):

| Signal | Direction | Purpose |
|---|---|---|
| **3V3** | AQROOT -> RootProbe | Regulated 3.3V power to run the RootProbe MCU + logic (budget below) |
| **GND** (x2-3) | shared | Multiple grounds for signal integrity + return current |
| **SPI SCK** | AQROOT -> RootProbe | High-speed data link clock (main sample/result transfer) |
| **SPI MOSI** | AQROOT -> RootProbe | Host -> coprocessor data (commands, config) |
| **SPI MISO** | RootProbe -> AQROOT | Coprocessor -> host data (results, buffered samples) |
| **SPI CS** | AQROOT -> RootProbe | Chip select for the RootProbe SPI link |
| **I2C SDA** | bidirectional | Low-speed management / housekeeping / ID / config |
| **I2C SCL** | AQROOT -> RootProbe | I2C clock (management bus) |
| **IRQ / READY** | RootProbe -> AQROOT | RootProbe signals "data ready / trigger hit / attention" |
| **RESET** | AQROOT -> RootProbe | Host can reset the coprocessor |
| **MODULE_DETECT / ID** | RootProbe -> AQROOT | Tells AQROOT a module is attached + which type |

Optional / future (reserve if pins allow):
| Signal | Direction | Purpose |
|---|---|---|
| **USB D+ / D-** | passthrough | Let RootProbe expose USB directly (firmware update / high-bandwidth dump) |
| **5V / VSYS** | AQROOT -> RootProbe | Higher-voltage rail if RootProbe needs it (e.g. level transl/analog) |
| **BOOT/PROG** | AQROOT -> RootProbe | Put RootProbe MCU in bootloader for firmware update over the link |

---

## 3. Connector pin count target

Minimum viable: ~11 signals (3V3, 2xGND, 4xSPI, 2xI2C, IRQ, RESET, DETECT) = ~12 pins.
Comfortable (with USB passthrough + 5V + boot + extra GND): ~16-18 pins.

**Recommendation: target a ~16-18 pin board-to-board connector** to leave room for the
optional signals (USB passthrough is the big one — it future-proofs RootProbe for high-
bandwidth dumps and self-contained firmware update). A high-density board-to-board connector
(e.g. a fine-pitch mezzanine/FPC or a spring-pogo array) fits the "clean base enclosure"
requirement from the enclosure design.

---

## 4. How this maps to the AQROOT main board

The RootProbe SPI link and I2C management need HOST pins on the ESP32-S3 side. Two options,
to decide at schematic time:

- **Option A - dedicated SPI:** give RootProbe its own SPI peripheral + CS. Cleanest, but
  the pin budget is tight (v0.2 shows native pins nearly full). Likely needs 1-2 freed pins.
- **Option B - share an existing SPI bus:** hang RootProbe off an existing SPI bus (e.g. the
  radio bus B) as another CS'd device. Cheaper on pins, but RootProbe then contends with the
  radios for the bus (only one at a time). Since RootProbe use (bench bus-sniffing) rarely
  overlaps with active radio TX, this is probably acceptable.
- **I2C management** shares the existing I2C bus (SDA=1/SCL=2) - RootProbe gets its own I2C
  address for housekeeping. Cheap (no new pins). Must be strapped clear of the reserved
  addresses (0x20, 0x21, 0x36, 0x38, 0x68 - and the whole 0x20-0x27 MCP23017 block).

### IRQ/READY - DECIDED 2026-07-26: expander pin, NOT a native pin

**The RootProbe host IRQ goes on MCP23017 0x20 GPB7** (the one spare expander pin), reserved
now and wired when RootProbe is actually built in Phase 2.

Rationale: **RootProbe does its high-speed capture locally on its own MCU.** The line crossing
to AQROOT is only "data ready / trigger hit / attention" - a notification, not a sampling
signal. Nothing about capture fidelity depends on how fast the host learns that a buffer is
ready, because the timing-critical work already completed on the coprocessor and the samples
are sitting in RootProbe's own RAM. Expander latency (tens to hundreds of microseconds) is
therefore harmless here, which is exactly the case the earlier "should ideally be a native
pin" note failed to make. That note is superseded.

Two bonuses fall out of the choice:
- GPB7 sits on Port B, which already has interrupt-on-change enabled for the button cluster,
  so the RootProbe IRQ routes through INTB -> GPIO21 and **can wake AQROOT from deep sleep**
  at no extra cost.
- It keeps the "don't let a Phase-2 accessory consume scarce native pins" principle intact on
  the one pin it was most tempting to break it for. The native budget is closed at 29 assigned
  / 0 unassigned (see [[11 - Beta Pin Map v0.2]] §1) and RootProbe no longer has a claim on it.

### DETECT + RESET - solvable without dedicated pins

- **MODULE_DETECT:** RootProbe has its own MCU and its own I2C address. Detection = "does the
  coprocessor answer on the management bus." No dedicated pin needed for the basic case.
- **RESET:** issue it as an I2C management command. A hardware reset line is only worth a pin
  if Phase-2 bring-up proves the coprocessor can wedge badly enough to stop answering I2C - a
  question that cannot be answered before RootProbe exists. If it turns out to be needed, the
  accessory-side load switch (power-cycling the module) is the fallback that costs no host pin.
- **SPI CS is the one signal that genuinely still needs resolving in Phase 2.** A per-transaction
  chip select cannot live behind an I2C expander at usable speed. Options when RootProbe is
  built: displace a native assignment, or assert CS across a whole command/result burst (one
  expander write to assert, the SPI burst, one to deassert) which is workable for a
  command-response protocol but not for fine-grained toggling. Do not pre-solve this now.

**Honest pin-budget note:** the main-board map has ZERO free native pins. RootProbe is a
Phase-2 accessory, so the approach stands: reserve the CONNECTOR footprint, reserve 0x20 GPB7
for the IRQ, share SPI bus B + I2C, and settle the CS question when RootProbe is actually
built. Do NOT let RootProbe force main-board pin decisions before it exists - just don't paint
the board into a corner that makes it impossible.

---

## 5. Power budget for RootProbe

RootProbe draws from the AQROOT 3V3 rail (or a dedicated switched feed):
- RP2040-class MCU: ~30-50 mA active.
- Local RAM / capture buffer: ~10-30 mA.
- Level-translation / protection buffers: ~10-40 mA depending on channels.
- LEDs / misc: ~5 mA.
- Total: ~55-125 mA when active.

The TPS63020 (2A) has ample headroom for this on top of the main-device draw. BUT: RootProbe
should be power-gated (a load switch on its 3V3 feed, enabled only when a module is attached +
in use) so an unused/absent module draws zero. The MODULE_DETECT line + a load switch handle
this. This fits the "power-gate everything" strategy.

---

## 6. Mechanical (defer to enclosure CAD, noted here)

- Connector at the upper-rear / rear-facing crown area (per enclosure v3 expansion zone).
- Recessed connector field with a replaceable protective cover.
- Alignment features (keyed edges / locating pins) so the module seats correctly.
- Optional screw point or stronger retention for the intelligent module (heavier than a
  simple GPIO add-on).
- NOT a full-length rail or permanent protruding dock (per enclosure v3 red lines).

---

## 7. What this unblocks / what stays open

**Unblocks:** the main-board PCB can reserve the RootProbe connector footprint + rough signal
routing, so the base device is "RootProbe-ready" without RootProbe existing yet.

**Stays open (Phase 2, when RootProbe is actually designed):**
- The **SPI CS** host pin (Option A vs B above) — the only signal still needing a native-pin
  decision. IRQ/READY is settled (0x20 GPB7), DETECT and RESET are handled over I2C.
- Exact connector part (pin count, pitch, mezzanine vs pogo vs FPC).
- RootProbe's own board design (RP2040-class MCU, capture front-end, level protection).
- Number of logic-analyzer channels + max sample rate (defines RootProbe's own silicon).
- Whether USB passthrough is included in v1 of RootProbe.

**Key principle:** reserve the interface now (so the base board isn't painted into a corner),
but do NOT let a Phase-2 accessory drive scarce main-board pin decisions before it's real.
Reserve the connector + a sensible signal set; finalize when RootProbe is built.
