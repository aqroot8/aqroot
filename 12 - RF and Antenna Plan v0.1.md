---
tags: [hardware, beta, rf, antenna, blocking-gate]
status: rf-architecture-draft
---

# AQROOT Beta — RF & Antenna Plan v0.1

**Purpose:** Architectural antenna decisions for the four RF systems, enough to unblock PCB
placement. This is the design-gate the three-way review flagged as blocking PCB layout.
NOT final tuning (that needs RF simulation + measurement on real hardware). This defines
antenna TYPE, rough LOCATION, and KEEP-OUT rules per radio, plus coexistence strategy.

Target: pocket handheld (~130 x 70 x 23.5mm, plastic PC+ABS shell, separate RF crown at top).
Envelope updated by [[17 - Enclosure Field Slate v4]]; the antenna zoning below is
unchanged and still derives from [[15 - Enclosure Field Slate v3]] §4-§7.

---

## Summary table

| RF system | Freq | Antenna type (Beta) | Location | Difficulty | Status |
|---|---|---|---|---|---|
| WiFi / BLE | 2.4 GHz | ESP32-S3 module onboard PCB antenna | Top corner, PCB edge | Easy (done by Espressif) | Decided |
| NFC | 13.56 MHz | PCB/flex loop coil | Rear center (NFC target) | Moderate (well-understood) | Decided |
| LoRa | 915 MHz | Taoglas FXP890 flex, plug-on via module IPEX | Upper sidewall / crown edge | Moderate | Part selected (tune later) |
| Sub-GHz | 433 MHz | Taoglas FXP450 flex, plug-on via module IPEX (still electrically small) | RF crown (max volume) | HARD | Part selected, needs testing |

**Board-level RF scope:** with 433 and 915 on certified modules with IPEX ports, NO RF signal
at either frequency reaches the main PCB — no matching networks, no RF traces, no test
connectors, no controlled-impedance routing for those two radios. NFC is the only remaining
board-level RF design task.

---

## 1. WiFi / BLE — 2.4 GHz (EASIEST — already solved)

- **Antenna:** the ESP32-S3-WROOM-1 module's ONBOARD PCB antenna. We do not design this;
  Espressif did, and it's FCC-certified as part of the module.
- **Our only job = the keep-out.** Follow Espressif's published module keep-out:
  - Module antenna end hangs off the main PCB edge (typically a top corner).
  - NO copper (no ground pour, no traces) under the antenna keep-out area.
  - NO metal near it: keep battery, speaker magnet, shields, screws, dense wiring away.
  - Only plastic (RF-transparent) in front of/around the antenna — no metal enclosure wall.
- **Placement:** upper-RIGHT crown area (per enclosure v3 zoning).
- **Risk:** low. This is the one antenna that's essentially free.

## 2. NFC — 13.56 MHz (magnetic loop, short-range, well-understood)

- **Antenna:** a flat COIL/LOOP (spiral of copper), NOT a conventional antenna. Works by
  near-field magnetic coupling — the user taps a card/tag against it.
- **Type:** etched PCB loop OR a separate flex-PCB loop antenna. Mounted FLAT against the
  inside of the REAR shell (the enclosure's "NFC target" area).
- **Matching network:** a small set of capacitors (and sometimes resistors) tuned so the
  loop resonates at 13.56 MHz. Tuned AFTER the rear shell/battery/PCB positions are fixed.
- **KEEP-OUT rules (critical):**
  - NO metal behind the loop: no battery foil, no ground plane, no screws, no magnets,
    no decorative metal badge.
  - Optional FERRITE backing layer between the loop and any internal metal — evaluate only
    after testing the final stack (ferrite shields the coil from the battery/PCB metal).
  - Keep >~5mm from screws.
- **Power note (from Alpha):** ST25R3916 analog/PA rail on the switched 5V boost for full
  TX range; VDD_IO stays 3.3V (SPI needs no level shifter).
- **Coexistence:** 13.56 MHz is far from the other bands and short-range → minimal
  interference with WiFi/LoRa/sub-GHz. Low coexistence risk.
- **Placement:** rear center (per enclosure v3).
- **Risk:** moderate — coil geometry + matching need tuning, but it's standard NFC design.

## 3. LoRa — 915 MHz (real TX radio, moderate)

- **Antenna — SELECTED:** Taoglas FXP890.07.0100C internal FPC (flexible printed circuit)
  antenna — a thin flexible antenna that adheres inside the enclosure, plugging onto the
  E22-900M22S module's IPEX port via its u.FL cable. See **Beta Hidden-Antenna Picks** at the
  end of this doc for the connector and ordering rules.
- **Location:** along an upper sidewall or the crown edge (per enclosure v3), positioned:
  - Clear of the battery and large grounded/metal structures.
  - Away from the user's normal grip where possible (a hand detunes antennas).
- **Matching network — NOT a board-level item (changed).** The E22-900M22S carries its own RF
  front-end and presents a matched 50-ohm IPEX port. Do NOT design a 915 matching network on
  the main PCB. Nothing at 915 MHz touches our copper.
- **Engineering test access (changed):** the module's IPEX port IS the test port — unplug the
  flex antenna and connect the NanoVNA there. Do NOT add a separate U.FL test connector.
  Range/grip testing in the FINAL enclosure is still required; only the test point moved.
- **Coexistence:** 915MHz sits between 433 and 2.4GHz; physical separation from the 433
  antenna matters (see coexistence section).
- **Placement:** upper-LEFT sidewall / crown edge (per enclosure v3).
- **Risk:** moderate, and LOWER than v0.1 assumed — the module owns the matching, so what's
  left is placement and in-enclosure tuning. The main care item is keeping the antenna body
  off the hand and away from the battery.

## 4. Sub-GHz — 433 MHz (THE HARD ONE)

- **Why hard:** 433 MHz wavelength ~69cm. A full efficient antenna (quarter-wave ~17cm)
  does NOT fit a pocket device. So we MUST use an electrically-shortened, compromised
  antenna, which sacrifices efficiency/range. Every pocket 433MHz device makes this tradeoff.
- **Antenna — SELECTED (supersedes the candidate-form study below):** Taoglas FXP450.07.0100C
  flex/FPC, plugging onto the E07-400M10S module's IPEX port via its u.FL cable. See
  **Beta Hidden-Antenna Picks** at the end of this doc for the connector and ordering rules.
- **Superseded candidate forms — NOT in play for Beta.** These were the options while 433 was
  assumed to be a board-level design (bare CC1101 + our own front-end). The module lock removed
  that assumption; kept only as the record of why a compromised antenna is unavoidable:
  helical spring, meandered PCB trace, shortened monopole / short whip, flexible wire element.
- **Matching network — NOT a board-level item (changed).** The E07-400M10S carries its own RF
  front-end and presents a matched 50-ohm IPEX port. Do NOT design a 433 matching network on
  the main PCB. Nothing at 433 MHz touches our copper.
- **Engineering test access (changed):** the module's IPEX port IS the test port — unplug the
  flex antenna and connect the NanoVNA there. Do NOT add a separate U.FL test connector; there
  is no board-level RF trace to attach one to.
- **Placement:** the antenna's u.FL cable decouples the antenna BODY from the module position,
  so the zoning below still stands — reserve the LARGEST crown volume (per enclosure v3) for
  the FXP450 body, TOP-LEFT, away from the user's grip. Iteration is now placement and
  orientation, not antenna construction.
- **433 antenna launch strategy (sequenced, not a contradiction):**
  - **BASE CERTIFIED DEVICE:** ships with the internal hidden FXP450 flex antenna as the
    default, certified configuration. This is what goes through FCC as the primary device.
  - **EXTERNAL HIGH-GAIN WHIP + SIDE-HOLDER:** launches as an ADVANCED ACCESSORY, separate
    from the base certified config, with its own compliance handling (a user-attachable
    antenna is treated as an accessory pending its own FCC path). The side-holder stows it on
    the device when not in use. Mechanically this is now simpler: the whip attaches to the SAME
    module IPEX port via a u.FL-to-SMA pigtail — the internal flex unplugs, the whip plugs in.
    That physical swap-ability is exactly what makes it a separate cert config, not a bonus.

  So the device is NOT certified with a user-swappable antenna at launch; the whip is an
  accessory added on top. Both the "fixed internal antenna for cert" and the "external whip +
  holder" decisions are correct and coexist — they apply to different configs/timelines.
  See [[05 - Design Decisions Log]] (433 external antenna decision) and
  [[15 - Enclosure Field Slate v3]] §7 (side-holder stowage).
- **Risk:** HIGH — accept a range compromise vs a full-size external whip on the base device.
  Set expectations: a pocket 433 device will not match a Flipper with an external antenna at
  max range, but a well-tuned internal one is serviceable, and the accessory whip closes the
  gap for users who want max range.

---

## 5. Coexistence strategy (the four must not fight each other)

- **Physical separation — spread the antennas to the four corners/zones:**
  - WiFi/BLE: upper-RIGHT crown.
  - Sub-GHz 433: upper-LEFT crown (largest volume).
  - LoRa 915: upper-LEFT sidewall / crown edge (separated from 433 as much as the crown allows).
  - NFC: rear center (different plane entirely — good isolation).
  - The tightest pair is 433 vs 915 (both in the crown region) — maximize their separation
    and consider orientation to reduce coupling.
- **Frequency separation (helps us):** 13.56MHz, 433MHz, 915MHz, 2.4GHz are far apart — no
  harmonic overlaps at the fundamentals that would cause direct in-band interference in
  normal operation. (Watch 2x433=866 near 915 — a 433 harmonic could nick the 915 RX.
  NOTE: board-level filtering is no longer a lever — there is no board RF path to filter on.
  Mitigation is now limited to antenna separation/orientation, the one-TX-at-a-time rule, and
  whatever harmonic suppression the modules already provide. Flag for RF review.)
- **DECISION — one transmitter at a time (firmware-enforced):** design so only ONE radio
  transmits at any instant. This massively simplifies RF coexistence (no two PAs desensing
  each other) and matches real use (you don't WiFi-attack + LoRa-TX + 433-replay at once).
  Multiple radios may RECEIVE simultaneously; only TX is serialized.
- **Ground plane:** solid continuous ground plane under the digital/center zone, with clean
  antenna keep-outs at the crown and rear. The ground plane is the RF foundation — antennas
  reference it. Keep it continuous; avoid slots/splits under/near antennas.
- **Shielding:** consider a can/shield over the noisiest digital section (ESP32 + SPI) if
  RF testing shows digital noise coupling into the sensitive radio RX. Decide after testing.

---

## 6. What this unblocks + what still needs doing

**Unblocks:** PCB placement can now proceed with defined antenna zones and keep-outs — the
enclosure v3 crown/rear zoning and this plan agree.

**Still needs (RF-specific, before/at PCB layout):**
- [x] Select specific off-the-shelf antennas: 915MHz = Taoglas FXP890.07.0100C,
      433MHz = Taoglas FXP450.07.0100C. STILL OPEN: NFC loop (etched vs flex part).
- [ ] ~~Design matching networks for 433 and 915~~ — VOID, on-module. NFC matching network
      still required (values set by simulation/measurement).
- [ ] ~~Place U.FL engineering test connectors for 433, 915~~ — VOID, the module IPEX ports
      serve as test points. Optional NFC test point still worth considering.
- [ ] **VERIFY BEFORE ORDERING:** confirm the exact module variants ship with an IPEX/u.FL
      port and not stamp-hole-only. Ebyte sells both interfaces under similar part numbers,
      and the entire zero-PCB-impact plan collapses if a stamp-hole variant arrives.
- [ ] **Modular-cert check:** the certified modules carry FCC/CE pre-cert only for the antenna
      types/gains in their grant. Swapping in the Taoglas parts may fall outside it and force
      re-evaluation. Confirm with the cert lab BEFORE treating the module pre-cert as a saving
      — this is the main cost risk the module lock was supposed to eliminate.
- [ ] Define exact keep-out dimensions (WiFi from Espressif; others from antenna datasheets).
- [ ] Define the ground-plane strategy in the stackup (likely 4-layer PCB for a clean plane).
- [ ] Decide 433 vs 915 harmonic mitigation — separation/orientation only, since board-level
      filtering is off the table with module RF (see §5) — flag for RF review.
- [ ] PROFESSIONAL RF REVIEW before PCB fab — this plan is architectural; a real RF engineer
      or the cert lab should review antenna placement + matching before committing to copper.
- [ ] Plan for FCC pre-scan: intentional radiators (433, 915, 2.4, 13.56) drive the cert.
      Scope this to the BASE CERTIFIED CONFIG (internal 433 antenna) — the external whip is a
      separate advanced-accessory compliance path, see §4.

**Key honest caveat:** antenna design is the one area where desk-planning only gets you so
far. Final antenna performance MUST be measured on real hardware in the real enclosure with a
real hand grip, and will likely need 1+ iterations (especially 433). This plan makes the
architecture PCB-ready; it does not replace RF measurement/tuning.

---

## 7. Layer stackup implication

The four-radio + ground-plane needs point toward a **4-layer PCB** (signal / ground / power /
signal), not 2-layer. A continuous ground plane is hard to maintain on 2 layers with this
much routing. 4-layer also helps EMI/cert. Budget for 4-layer in the PCB cost.

---

## Beta Hidden-Antenna Picks (post-fab, plug-on - DO NOT ROUTE)
Selected flex/FPC antennas to make Beta look like the final product (hidden antennas).
These plug onto the module IPEX connectors - ZERO PCB impact (no footprint, pad, or routing).

- 915 MHz (E22-900M22S / SX1262): Taoglas FXP890.07.0100C - u.FL / MHF I connector
- 433 MHz (E07-400M10S / CC1101): Taoglas FXP450.07.0100C - u.FL / MHF I connector

Connector note: MUST be u.FL / MHF I variant. MHF II does NOT mate with the module IPEX.
Order timing: after PCB fab (they connect to the module, not the board).
Layout requirement: place each module's antenna end at a board edge with RF keep-out around it
  (no ground pour, no metal, away from battery). This is normal module placement, not a design
  change.
Status: DO NOT ROUTE. Selection recorded; final placement/performance pending post-Kickstarter
  RF pass (NanoVNA + range test). 433 MHz hidden = expected range compromise, acceptable for
  Beta demo.
NFC (13.56 MHz) and WiFi/BLE (2.4 GHz, WROOM onboard) are already internal - not affected.
