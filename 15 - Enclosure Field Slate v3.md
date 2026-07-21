---
tags: [hardware, enclosure, mechanical, industrial-design, v3]
status: approved-direction
---

# AQROOT Enclosure — "Field Slate" v3

**Why this doc exists:** [[12 - RF and Antenna Plan v0.1]] and [[14 - RootProbe Interface v0.1]]
both cite "enclosure v3" as authoritative for antenna zoning, crown volume, rear NFC
placement, expansion-zone location, and mechanical red lines — but the spec lived only in
external documents (Google Drive), not in this repo. Every RF and mechanical conclusion in
those two docs depends on the envelope below. This doc brings the dependency in-repo.

**Status: APPROVED as design DIRECTION (v3) — NOT a mechanical freeze.** Per the §19
principle from the source spec: the envelope, antennas, display, battery, and buttons must
drive at least ONE PCB revision before a joint mechanical-electrical freeze. Treat the
numbers here as the design target that the first PCB is routed against, not as final.

---

## 1. Concept

Self-contained portrait candy-bar handheld. Single-piece feel, field-tool aesthetic — built
to be used one-handed while the other hand holds a probe, a tag, or a target device.

Defining features:
- **RF crown:** a separate RF-transparent polymer section across the TOP of the device,
  housing the antennas and the IR emitter/receiver. Structurally and materially distinct
  from the main shell so RF isn't fighting the body.
- **Flat rear NFC target:** a clean, metal-free flat area on the back face where the user
  taps a card or tag.
- **Physical controls:** D-pad + A/B + Back + Home. Deliberate hardware navigation — the
  touchscreen is primary, but the device stays fully drivable with gloves, in the dark, or
  with a frozen UI.
- **Side antenna holder:** an integrated channel/holder on the SIDE of the device that stows
  the external 433MHz whip when not in use (see §6).

## 2. Dimensions & mass

| Property | Value |
|---|---|
| Body | ~122 x 61 x 23.5 mm |
| With crown | up to 24.5 mm at the crown |
| Mass | 135-165 g |
| Colorway | "Graphite Root" |

> This supersedes the earlier ~75x45x16mm target (see [[05 - Design Decisions Log]]).
> The device is a field tool, not a keyfob — the larger envelope is what makes a serviceable
> 433MHz antenna, a 2000mAh cell, and a real button cluster possible at the same time.

## 3. Materials & manufacturing staging

- **Production shell:** PC+ABS, injection-molded.
- **Low-volume path:** PA12 via MJF (Multi Jet Fusion).
- **RF crown:** RF-transparent polymer, separate part from the main shell.

Staging:
1. **FDM** (existing Kobra S1) — 3-8 units, fit/feel/bring-up.
2. **MJF PA12** — 10-20 units, reviewer seeding + realistic RF measurement.
3. **50-unit pilot run.**
4. **Injection molding** — production.

## 4. Zoning (what docs 12 and 14 depend on)

| Zone | Contents |
|---|---|
| RF crown, top-LEFT | Sub-GHz 433 antenna — largest available volume |
| RF crown, upper-LEFT sidewall / edge | LoRa 915 internal FPC antenna |
| RF crown, upper-RIGHT | WiFi/BLE — ESP32-S3 module onboard antenna + keep-out |
| Crown | IR emitter + receiver |
| Rear, center | NFC loop/coil target — no metal behind |
| Upper-rear / rear-facing crown area | RootProbe expansion connector field |
| Side | External 433 antenna stowage channel |

**Mechanical red lines (from v3):** no full-length rail, no permanently protruding dock.
The base enclosure stays clean when no module is attached.

## 5. Power (mechanical + electrical requirements from v3)

- bq25185 charger + power-path.
- Separate **3.3V buck-boost regulator (TPS63020)** — the bq25185 SYS output is not a clean
  3.3V rail. See [[11 - Beta Pin Map v0.2]] §8.
- Switched **5V boost for the NFC PA rail** only (VDD_IO stays 3.3V).
- **REVERSE-POLARITY PROTECTION at the battery input — mandatory.** Learned the hard way:
  a reverse-wired LiPo JST connector destroyed a bq25185 board during bench testing (see
  [[05 - Design Decisions Log]]).
- **Keyed/standardized battery connector polarity**, and a **battery tray whose geometry
  cannot invite reversed insertion.** This is an enclosure requirement, not just an
  electrical one — the tray shape is the last line of defence.
- Charger thermals: bq25185 is linear. Start Beta at ~500mA charge current and raise only
  after enclosure thermal testing — a sealed shell changes the answer.

## 6. Expansion — two-tier

1. **Community GPIO header** — low-speed, off the MCP23017 expander (~7 slow GPIO, not the
   12 originally advertised; see [[11 - Beta Pin Map v0.2]] §7).
2. **RootProbe coprocessor connector** — footprint RESERVED on the main board, Phase 2
   product. Recessed connector field with a replaceable protective cover, alignment/keying
   features, optional screw retention. See [[14 - RootProbe Interface v0.1]].

## 7. 433 MHz external antenna + side holder

- **Default:** internal electrically-shortened 433 antenna in the crown — modest range,
  fully pocketable, no protrusions.
- **Max range:** screw-on external high-gain whip via U.FL/SMA (Flipper-style).
- **Stowage:** an integrated holder/channel on the SIDE of the shell retains the external
  whip when not in use — never lost, and a distinctive design feature.
- Target antenna size ~8-14cm class; EXACT size decided POST-PCB by measuring candidates on
  real hardware.
- **Cert path (RESOLVED — the two stances are sequenced, not contradictory):** the BASE
  CERTIFIED DEVICE ships with the internal electrically-shortened 433 antenna as its default,
  certified configuration — that is what goes through FCC as the primary device. The external
  high-gain whip + this side-holder launch as an ADVANCED ACCESSORY, separate from the base
  certified config, with their own compliance handling. The device is NOT certified with a
  user-swappable antenna at launch; the whip is added on top. See
  [[12 - RF and Antenna Plan v0.1]] §4 for the full reworded launch strategy.
- **Keep magnets away from the NFC coil** if magnetic retention is ever considered.

## 8. Source documents

The full product sheet and the concept graphic (v3) live in the **ClaudeImages Google Drive
folder**. The product sheet is clean; residual OCR typos exist in the graphic PNG only — if
the graphic and this doc disagree on a number, this doc and the product sheet win.

## 9. Open items

- [ ] Joint mechanical-electrical freeze — blocked on >=1 PCB revision (§19 principle).
- [ ] Exact speaker part + acoustic mounting (depends on final shell internals).
- [ ] Final battery cell size — 2000mAh baseline, 2500-3000mAh if volume allows.
- [ ] Exact RootProbe connector part (pin count, pitch, mezzanine vs pogo vs FPC).
- [ ] Antenna keep-out dimensions from the selected antenna datasheets.
- [x] RESOLVED — doc 12's 433 launch stance and the external antenna + side-holder decision
      are sequenced, not contradictory: internal antenna = base certified device, external
      whip + holder = advanced accessory on its own FCC path. See
      [[12 - RF and Antenna Plan v0.1]] §4.
- [ ] Advanced-accessory FCC path for the external whip — scope and timeline (separate from
      base device certification).
