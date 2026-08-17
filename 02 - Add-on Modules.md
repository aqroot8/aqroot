---
tags: [hardware, add-ons]
---

# Add-on Modules (optional, expansion-port based)

| Add-on | Purpose | Connector |
|---|---|---|
| External whip antenna (SMA) | High-gain option for extended LoRa/sub-GHz range | **u.FL/MHF-I pigtail — see the correction note below.** The base unit has **no** panel SMA jack |
| GPIO/debug breakout | Pogo-pin jig or ribbon header for firmware development, kept off the main shell | Pogo-pin or ribbon |
| External/extended battery pack | Snap-on pack for extended field use | Pogo-pin dock (Kode Dot style — no cable fumbling) |
| Swappable back covers | Color/texture/belt-clip variants, purely cosmetic | Snap-fit, no electronics |

## Correction — the external antenna does not screw into the base unit

This table previously said the external SMA antenna *"screws onto existing SMA
connector."* **There is no SMA connector on the base unit.** The locked Beta radio
architecture, per [[12 - RF and Antenna Plan v0.1]], uses **hidden flex/FPC antennas
on internal u.FL/MHF-I (IPEX) ports** on the E22-900M22S and E07-400M10S modules.

The real upgrade path is: the internal flex antenna **unplugs from the module's IPEX
port**, and a **u.FL-to-SMA pigtail** plus whip goes in its place. That means the
external-antenna option is an **enclosure-opening, certification-affecting swap**, not
a user-facing screw-on accessory — the base certified device ships with the internal
flex antenna as its certified configuration.

Corrected here rather than left standing, because the old wording described a
connector the product does not have.

---

# POST-KICKSTARTER ACCESSORY ROADMAP — INTENT ONLY

> **POST-KICKSTARTER — INTENT ONLY · MAY CHANGE · NOT BETA SCOPE**
>
> Nothing in this section authorizes a change to Beta. The **F4 J5 community header
> is HARD-LOCKED**: pin map, copper, schematic, placement and DRU all stay as they
> are. Everything below is forward-looking product intent for a future revision or a
> future accessory, and may change or be dropped.

## What the community header actually is today

Verified against the landed Beta board, not assumed. J5 is a **26-pin** header:

| Function | Pins | Notes |
|---|---|---|
| `XGPIO0..XGPIO13` | 14 | **I/O-expander pins** — each runs through a series resistor and ESD diode to **U3**, an I²C port expander. They are *not* direct MCU pins and move at I²C rates. |
| `FAST_IO_GPIO43_HDR` | 1 | The **only direct-MCU pin** on the header (U1.37, GPIO43), series-protected by R67. Shared with `ROOTPROBE_CS`. |
| `I2C_SDA_EXT_HDR` / `I2C_SCL_EXT_HDR` | 2 | External I²C, buffered/level-translated through U16 |
| `WAKE_ATTN_N_HDR` | 1 | Accessory wake / attention |
| `+3V3` | 1 | Always-on rail |
| `ACC_3V3_SW` | 1 | Switched accessory rail, gated by U15 (`ACC_PWR_EN`) |
| `RESERVED_NC` | 1 | Not connected |
| `GND` | 5 | J5.2, 7, 20, 24, 25 |

### UART exposed: **NO**  ·  USB exposed: **NO**

This is the important constraint for everything below. Checked directly:

- **No UART.** No TX/RX pair is brought to J5. `FAST_IO_GPIO43_HDR` is GPIO43, which
  *is* U0TXD in silicon, but it is exposed as a single general-purpose fast IO with
  **no RX counterpart** — that is not a UART port.
- **No USB.** `USB_D_MCU_P/N`, `USB_D_CONN_P/N` and the `USB_VBUS_*` nets all live on
  the USB-C connector and power tree. **None of them reach J5.**

So the header's practical ceiling today is **I²C plus one fast MCU pin**. Do not
describe it as a Linux transport.

## A. Linux / Kali companion module

> POST-KICKSTARTER · OPTIONAL · MAY CHANGE · NOT BETA SCOPE

An external Linux/Kali companion — a "compute backpack" — carrying its **own** SoC,
RAM/storage, power architecture and Linux install. Candidate compute classes: Pi
Zero-class, Radxa-class, Luckfox-class, or another Linux-capable SoM/SBC.

Division of responsibility:

| AQROOT | Linux companion |
|---|---|
| RF hardware, NFC, IR, sub-GHz, sensors, GPIO, device-specific real-time work | terminal, network tooling, scripting, compute-heavy workflows, dev environment |

The long-term concept is that **Linux orchestrates and AQROOT performs** the physical
and RF operations, with structured results moving between them.

**The current Beta header does not provide the final Linux transport**, and this
roadmap does not ask it to. See the capability table above.

## B. Final-product companion interface — OPEN post-Beta requirement

AQROOT Final should **evaluate a dedicated higher-bandwidth companion interface**.
Candidates: UART, USB, SPI, or another deliberate accessory transport.

This is **not** a Beta modification request. The hard-locked F4 header stays as it is;
a future hardware revision may add a dedicated companion connector if the accessory
programme justifies it.

## C. Physical keyboard module

> POST-KICKSTARTER · OPTIONAL · MAY CHANGE

A compact QWERTY/thumb keyboard with navigation keys and terminal shortcuts. A
keyboard controller talking **I²C plus a GPIO/interrupt line** is the obvious
prototyping fit for the existing community-header architecture — which makes the
current header *potentially suitable for prototyping*, not a committed final
electrical architecture. That decision belongs to accessory design when it starts.

BLE keyboard input and USB keyboard input (where host/hardware support permits) are
tracked as firmware/software compatibility targets in [[03 - OS Architecture]].

## D. Terminal / compute deck concept

> POST-KICKSTARTER · OPTIONAL · MAY CHANGE

An optional premium accessory, the **AQROOT Terminal Deck**. Possible elements:
physical keyboard, extra battery, Linux compute module, additional storage, USB
expansion. Possible tiers:

1. keyboard only
2. keyboard + battery
3. keyboard + battery + Linux compute

Everything here is post-Kickstarter and may change.

## E. Accessory contention — recorded, not solved

The **keyboard module** and the **Linux compute backpack** may both want the same
community-header physical interface. Possible future answers include a stack-through
connector, a keyboard integrated into the compute deck, an accessory hub, a separate
companion connector, or a wireless keyboard.

**No choice is being made now.** This is recorded so it is not discovered late.

## F. Mechanical readiness — the one live constraint

**DO NOT PHYSICALLY STRAND THE COMMUNITY HEADER.**

Enclosure and mechanical work should preserve:

- physical mating access to J5
- reasonable accessory insertion and removal
- clearance for a rear/bottom accessory where practical
- access to mounting/retention features
- no unavoidable battery-service conflict

and should also weigh RF antenna obstruction, display/button use, USB port access and
enclosure assembly. A future backpack **should not be forced to sit directly over an
antenna region** if that is avoidable — see the hidden-FPC antenna placement in
[[12 - RF and Antenna Plan v0.1]].

This is a **mechanical readiness note only**. It does not authorize any PCB, pin-map,
schematic or DRU change.
