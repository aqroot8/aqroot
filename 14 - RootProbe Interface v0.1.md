---
tags: [hardware, beta, rootprobe, expansion, phase2]
status: interface-design-draft
---

# AQROOT RootProbe — Accessory Interface Spec v0.1

**What this is:** the electrical + mechanical interface between the AQROOT main board and
the RootProbe coprocessor accessory. RootProbe is the flagship add-on: an intelligent
logic-analyzer / bus-sniffer / GPIO-tooling module aimed at the security audience.

**Why an interface spec now:** the three-way review established that RootProbe CANNOT be raw
I2C expander pins (I2C-mediated GPIO is far too slow for logic-analysis). RootProbe must
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
| **SPI CS** | AQROOT -> RootProbe | Chip select for the RootProbe SPI link. **= GPIO43, multiplexed with the header FAST_IO pin (§4)** |
| **I2C SDA** | bidirectional | Low-speed management / housekeeping / ID / config |
| **I2C SCL** | AQROOT -> RootProbe | I2C clock (management bus) |
| **IRQ / READY** | RootProbe -> AQROOT | RootProbe signals "data ready / trigger hit / attention". Net `ROOTPROBE_IRQ_READY_N` -> **U60 P17** (§4). **Open-drain, active-low, and MUST be LEVEL-HELD until acknowledged — not a pulse** |
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
  addresses (0x20, 0x21, 0x36, 0x38, 0x68 - and the whole 0x20-0x27 I2C-expander block, which
  the TCA9535 family occupies).

### IRQ/READY - DECIDED 2026-07-26: expander pin, NOT a native pin

**The RootProbe host IRQ is `ROOTPROBE_IRQ_READY_N` on U60 P17** — U60 being the internal
**TI TCA9535PWR @ 0x20** (part locked 2026-07-27, replacing the MCP23017; see
[[11 - Beta Pin Map v0.2]] §7). The pin is committed now and wired when RootProbe is actually
built in Phase 2. **All 16 U60 pins are assigned — the chip has zero free capacity.**

Rationale: **RootProbe does its high-speed capture locally on its own MCU.** The line crossing
to AQROOT is only "data ready / trigger hit / attention" - a notification, not a sampling
signal. Nothing about capture fidelity depends on how fast the host learns that a buffer is
ready, because the timing-critical work already completed on the coprocessor and the samples
are sitting in RootProbe's own RAM. Expander latency (tens to hundreds of microseconds) is
therefore harmless here, which is exactly the case the earlier "should ideally be a native
pin" note failed to make. That note is superseded.

Two bonuses fall out of the choice:
- P17 sits on U60 Port 1 alongside the button inputs, so the RootProbe IRQ routes through
  U60 `/INT` -> `WAKE_INT_N` -> GPIO21 and **can wake AQROOT from deep sleep** at no extra cost.
- It keeps the "don't let a Phase-2 accessory consume scarce native pins" principle intact on
  the one pin it was most tempting to break it for. (The native budget sits at 29 assigned /
  0 unassigned — see [[11 - Beta Pin Map v0.2]] §1 — but note it is the GPIO43 multiplex below,
  not this IRQ decision, that actually closes it. RootProbe's CS was still outstanding at the
  time this section was first written.)

#### FIRMWARE REQUIREMENT (RootProbe side, added 2026-07-27, NOT optional)

**`ROOTPROBE_IRQ_READY_N` must be asserted and HELD LOW until AQROOT acknowledges it over the
I2C management link. A short pulse is not acceptable and will be lost.**

This is a direct consequence of the expander part change (MCP23017 -> TCA9535PWR). The earlier
version of this decision leaned on the MCP23017's interrupt-on-change hardware, which latched a
change into `INTF`/`INTCAP` so the host could discover a brief event after the fact. **The
TCA9535 has no such hardware — there is no interrupt-capture register of any kind.** Its `/INT`
asserts while an input differs from the last value read out of the Input Port register and
deasserts as soon as that register is read. Nothing records a transient that has already
reverted.

Concretely, a pulsed IRQ can be missed because:
- AQROOT may be in **deep sleep**; the wake path itself takes milliseconds to bring I2C up.
- AQROOT may be **mid-I2C-transaction** with another device on the shared bus.
- U60's single `/INT` **merges the button cluster and this IRQ**, so the driver may be servicing
  a button event when RootProbe pulses — and one Input Port read clears the assertion for
  everything on that port.

Hold the line until acknowledged and none of those matter. Release it only on an explicit
host acknowledgement, not on a timer.

### DETECT + RESET - solvable without dedicated pins

- **MODULE_DETECT:** RootProbe has its own MCU and its own I2C address. Detection = "does the
  coprocessor answer on the management bus." No dedicated pin needed for the basic case.
- **RESET:** issue it as an I2C management command. A hardware reset line is only worth a pin
  if Phase-2 bring-up proves the coprocessor can wedge badly enough to stop answering I2C - a
  question that cannot be answered before RootProbe exists. If it turns out to be needed, the
  accessory-side load switch (power-cycling the module) is the fallback that costs no host pin.
### SPI CS - RESOLVED 2026-07-26: multiplex GPIO43

A per-transaction chip select cannot live behind an I2C expander at usable speed, so CS was the
one RootProbe signal that genuinely required a native pin. With the main-board map at zero
unassigned native pins, that was a **logical contradiction**: the pin budget was documented as
"closed" while this doc still recorded a standing requirement for a native pin that did not
exist. Deferring it to Phase 2 did not make the contradiction go away, it just hid it.

**Resolution: GPIO43 becomes a multiplexed net, `FAST_IO / U0TXD / ROOTPROBE_CS`.**

| Role | Active when |
|---|---|
| **FAST_IO** - community-header native fast pin | a general accessory is attached |
| **ROOTPROBE_CS** - RootProbe SPI chip select | a RootProbe module is attached |
| *(U0TXD - ROM boot-log output)* | *always, at every reset* |

The two accessory roles are **mutually exclusive - the same physical interface, never both at
once.** The net routes to both the community header and the RootProbe connector; only one may
be populated and active. Firmware arbitrates via I2C enumeration (a RootProbe that answers on
the management bus means GPIO43 is ROOTPROBE_CS and must not be driven as FAST_IO), and the
combination is documented as unsupported for users. Series resistors on both connector legs
limit damage if someone ignores that, but that is damage-limiting, not support.

**This is what actually closes the native pin budget** - see [[11 - Beta Pin Map v0.2]] §1 and
§9a. RootProbe now has a native home for CS, an expander home for IRQ (U60 P17), and I2C for
DETECT and RESET. It has no remaining unmet pin requirement.

**FIRMWARE REQUIREMENT (RootProbe side, not optional):** GPIO43 is U0TXD, so the AQROOT ROM
bootloader drives boot-log traffic onto this net at every reset. **RootProbe will therefore see
spurious chip-select activity while AQROOT boots.** RootProbe's MCU must hold its SPI slave
interface disabled/ignored until its own firmware has initialised and the host has made contact
over the I2C management link. An implementation that acts on raw CS edges from power-up will
misbehave on every AQROOT reset. (This is the same hazard that moved IR TX off GPIO43 in pin
map v0.2.1 - a boot-log-driven net is fine for something that can ignore it, and unacceptable
for something that acts on every edge.)

**Honest pin-budget note:** the main-board map has ZERO unassigned native pins; RootProbe fits
by sharing GPIO43, not by having spare capacity. The approach stands: reserve the CONNECTOR
footprint, keep U60 P17 for the IRQ, share SPI bus B + I2C, and route GPIO43 to both
connectors. Do NOT let RootProbe force further main-board pin decisions before it exists - just
don't paint the board into a corner that makes it impossible.

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

**Host-pin assignment is now fully settled — nothing here is open:**
- **SPI data link:** shares SPI Bus B (Option B), CS = GPIO43 multiplexed (see above).
- **IRQ/READY:** `ROOTPROBE_IRQ_READY_N` on **U60 P17** (TCA9535PWR @ 0x20), level-held until
  acknowledged.
- **DETECT:** I2C enumeration on the management bus. **RESET:** I2C management command, with
  the accessory-side load switch as the power-cycle fallback.

**Stays open (Phase 2, when RootProbe is actually designed):**
- Exact connector part (pin count, pitch, mezzanine vs pogo vs FPC).
- RootProbe's own board design (RP2040-class MCU, capture front-end, level protection).
- Number of logic-analyzer channels + max sample rate (defines RootProbe's own silicon).
- Whether USB passthrough is included in v1 of RootProbe.

**Key principle:** reserve the interface now (so the base board isn't painted into a corner),
but do NOT let a Phase-2 accessory drive scarce main-board pin decisions before it's real.
Reserve the connector + a sensible signal set; finalize when RootProbe is built.
