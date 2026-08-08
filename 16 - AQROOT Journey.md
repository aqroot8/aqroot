---
tags: [project, journey, history, aqroot]
status: living
---

# 16 — The AQROOT Journey

A chronological account of how AQROOT got from a concept note to a nearly-complete Beta
schematic, including the parts that went wrong. This is the narrative companion to
[[05 - Design Decisions Log]] — the log records *what* was decided and is authoritative; this
records *how it went* and what the project learned.

**Span:** 2026-07-07 → 2026-08-08 (~1 month, 163 commits).
**Current state:** Beta schematic captured, 186 components, **172 of 186 footprinted**, no
connectors outstanding. Not fab-released — see [[#What is still open]].

---

## Phase 0 — Concept and a firmware skeleton (2026-07-07)

The project started as vault notes plus, unusually, a **complete first firmware pass on day
one**: LVGL 8.3 app-launcher shell, display/touch glue, radio, NFC and sensor drivers, and a
Wokwi simulation target so the UI could be exercised with no hardware at all. See
[[Firmware/README]] and [[03 - OS Architecture]].

That ordering mattered later. Writing the drivers first exposed which buses and pins the
design actually needed, which is what made the Alpha bring-up a *validation* exercise rather
than an exploration.

## Phase 1 — Alpha: prove every chip on real hardware (2026-07-12 → 07-26)

The Alpha was a hand-wired devkit rig whose only job was to answer *"does this part work, on
this bus, at this address?"* before any of it reached a schematic. Results in
[[Alpha-Tests/HARDWARE-NOTES]] and [[09 - Alpha Pin Bus Map]].

| Subsystem | Outcome |
|---|---|
| Display + touch | PASS. Also found the gotcha that the FT6236 stays asleep until `CTP_RST` is pulsed — it does **not** appear on an I2C scan without it |
| CC1101 sub-GHz | PASS — SPI init and live RF reception |
| SX1262 + **dual-radio** | PASS — **the two-radio architecture was validated on hardware**, which is the project's core competitive wedge |
| ST25R3916 NFC | PASS — the hardest chip, IC-ID `0x2A`. Also surfaced that full RF TX needs a **switched 5V PA rail**, which reshaped the power tree |
| microSD | PASS — raw SPI `CMD0` returned `0x01` |
| BMI270 IMU | PASS at I2C `0x68` |
| IR | PASS — full TX→RX loopback |
| Audio | Amp PASS with real speaker output; **mic inconclusive, then confirmed dead**. First live capture deferred to Beta rather than faked |
| MCP23017 expander | PASS — 49/49 clean loopback *(but see the reversal below)* |
| TPS63020 3.3V rail | PASS — held regulation from a 3.4 V input, confirming true buck-boost behaviour |
| bq25185 charger | PASS — charging confirmed. **"ALPHA HARDWARE VALIDATION COMPLETE"** |

**A bench incident during this phase** — a reversed battery — produced the standing
**reverse-polarity protection requirement** that still gates fabrication today.

## Phase 2 — The pre-schematic review, and a pin budget that didn't close (2026-07-26)

A three-way design review (internal / ChatGPT / Fable 5) run deliberately *before* capture.
It found real errors: `GPIO43`/`GPIO44` were reversed in the map, and **IR TX was assigned to
GPIO43 — the ROM boot-log pin, which would have fired the IR LED driver at 100–500 mA on
every single reset.** A gate pull-down does not fix an actively-driven UART output. IR TX
moved to GPIO16.

The deeper problem was that the ESP32-S3's native pins simply did not go around. The
resolution was structural rather than arithmetic: **a second GPIO expander**, `GPIO21`
reclaimed as the RTC-capable wake interrupt, `GPIO43` multiplexed as
`FAST_IO / U0TXD / ROOTPROBE_CS`, and the community header moved entirely onto expander pins.
See [[11 - Beta Pin Map v0.2]] §6a–§9a.

## Phase 3 — Part selection, and one conclusion that didn't survive (2026-07-27 → 08-02)

**The MCP23017 reversal is the most instructive episode in the project.** v0.2.1 had recorded
a *correction* claiming the expander had 16 fully bidirectional GPIO, replacing an earlier
"14 bidirectional + 2 output-only" figure, and every pin-budget number was recalculated on
that basis. Re-checked against current MCP23017 I2C silicon, **the correction was itself
wrong** — and it had been bench-validated, which is exactly why it was believed.

The fix was not to argue the pin map down but to **change the part**: TI **TCA9535PWR ×2**
(U60 @ 0x20, U61 @ 0x21), which genuinely has 16 bidirectional I/O. The cost was honest and
recorded: the Alpha expander pass **does not carry over**, because it tested a different chip.
The TCA9535 has **never been bench-validated on AQROOT** and its first hardware validation
happens on Beta.

This phase also locked the TPS63020 3.3V block and the USB-C 5V sink front end, and
established a discipline that held for the rest of the project:

> **Candidate ≠ decision.** Proposed part numbers are recorded so they aren't lost, but they
> are never written into a schematic, a BOM, or a status report as selected parts until they
> clear their stated criteria against the manufacturer datasheet.

**Reverse-polarity protection was PARKED, not solved.** The leading candidate (ADI LTC4368-1
driving back-to-back N-FETs) is documented along with an explicit *rejected* list, and final
topology lock was assigned to a professional power/DFM review. **That gate still blocks PCB
routing and fab release for the whole board** — see [[07 - Build TODO Tracker]].

## Phase 4 — Schematic capture (2026-07-27 → 08-06)

Captured sheet by sheet in KiCad 10.0.3: MCU core, I2C, audio, IR, SPI-A, SPI-B radios and
NFC, the power tree, and the community header with its internal hierarchy. Then root-level
wiring, deferred sheet-pin termination, and an ERC pass that **documented intentional
exclusions** (reverse-polarity placeholder, RGB, RootProbe, RF-TBD) rather than globally
weakening the rules.

The standing rule from this phase: **narrow, documented exclusions only — never a global
severity change.**

## Phase 5 — Physical closure: turning placeholders into real parts (2026-08-07 → 08-08)

The largest and most demanding stretch — 80 commits in two days — replacing functional
placeholder symbols with **real parts carrying verified land patterns**. A footprint
verification policy was established first:

- **Class A** (ordinary JEDEC leaded packages) — an IPC generic land pattern is acceptable
- **Class B** (exposed-pad, magnetics, connectors, switches, RF modules) — **vendor-exact
  geometry required, no exceptions**

and a standing prohibition that shaped everything after it:

> **Do not fabricate** land-pattern dimensions, package codes, saturation currents, DCR,
> current ratings or mechanical dimensions. If the document cannot be reached, the item stays
> **BLOCKED** and is reported as blocked.

That rule was honoured even when it was expensive. Work was repeatedly stopped and reported
rather than guessed: U9 was blocked when `st.com` proved unreachable by every method; J2 sat
blocked across **eight** separate sessions while the Molex drawing was chased; a raster
measurement that failed its own sanity check (12.23 mm derived against a 14.0 mm label) was
**discarded rather than used**.

**What closed:**

| Ref | Part | Note |
|---|---|---|
| J1 | Hirose **FH69-50S-0.5SH** 50-pin FPC | Replaced an **obsolete** FCI 62684. Panel locked to SPI mode II with readback (IM3:IM0 = 1110); backlight = TPS61169DCKR + 4×39R + 2.55R RSET |
| J2 | Molex **5025700893** microSD | 14 lands, 1.1 pitch, 7.7 span, 14.3 shell outer — the last connector |
| U7 | Ebyte **E07-400M10S** (CC1101, 433 MHz) | Certified module, not a bare IC |
| U8 | Ebyte **E22-900M22S** (SX1262, 915 MHz) | Certified module |
| U9 | ST **ST25R3916-AQET** | UFQFPN32 + the 10 ST-specified decoupling caps C45–C54 |
| U12 | TI **TPS63020 DSJ** | Exposed pad with slots, resolved at 900 dpi |
| SW9 | C&K **JS102011SAQN** | Vendor-exact |

**The price paid for the E22.** Locking the physical SX1262 module required an `RXEN` control
for its RF switch — `DIO2` handles `TXEN` inside the module, but `RXEN` needs a host line, and
**the design had no free GPIO left.** Rather than inventing a pin or changing the MCU map, the
last community GPIO was reclaimed: **U61 P16, `XGPIO14` → `SX1262_RXEN`**. The header now
publishes **14 user GPIO (XGPIO0–13)**, its physical pin retained as `RESERVED_NC`, and
XGPIO0–13 were **not** renumbered so no accessory pinout shifts.

This has a marketing consequence that is recorded rather than buried: the old claim *"15 user
GPIO still exceeds Kode Dot's 14"* **is no longer true** — AQROOT now ties at 14. See
[[04 - Competitive Analysis]], which already advised never to compete on GPIO counts.

---

## What the project learned

**Bench-validate before capture, and re-check even validated conclusions.** The MCP23017
episode proves both halves: validation caught real gotchas the datasheets didn't advertise,
and a bench pass still wasn't enough to keep a wrong conclusion alive.

**ERC is not a connectivity check.** The lesson was learned the hard way. When U9 was first
integrated, deleting the symbol left its fifteen old wires behind, and the new pins silently
bound to them — six pins landed on wrong nets, including `XTO` on `NFC_CS_N` and `RFO1` on
`GND`. **A pad-count check passed 33/33 on that broken run.** What caught it was an
**expected-net-map audit**: writing the intended pin-to-net table *before* validating, then
comparing every pin against the exported netlist. That audit is now mandatory for every
integration, along with an **explicit deletion set** for the old symbol's wires, labels and
orphaned power symbols.

**Report blocked as blocked.** Roughly a third of Phase 5's commits are documentation of work
that could *not* be completed, with the exact retrieval routes attempted. That is what made
the eventual closures fast and trustworthy when the documents finally arrived.

**Correct the register, don't rewrite it.** U7 and U8 were transposed in an internal blocker
register, and two task briefs were written on top of that error. The schematic was treated as
authoritative and the rows were **annotated in place** rather than silently fixed. Same
approach for the superseded GPIO count in [[11 - Beta Pin Map v0.2]].

**Tooling has its own failure modes.** Naive paren counting corrupted two sheets because
property values legitimately contain parentheses — a balance assertion passed since parens
inside strings are balanced. **Quote-aware paren counting is now mandatory** for any
s-expression tooling in this repo.

## What is still open

**Blocking fabrication:**

- [ ] **Reverse-polarity protection topology** — parked pending professional power/DFM review
      with an LTspice charge-path case and ADI FAE confirmation. **Blocks routing and fab
      release for the entire board**, not just the power sheet
- [ ] **Pre-fab BOM-validation pass** — every capacitor MPN with DC-bias-derated effective
      capacitance, and the inductor with DCR/Isat/Irms evidence

**Schematic completeness:**

- [ ] 14 components still without footprints: `C12 C18 C19 LS1 R24 SW1`–`SW8 U14`
- [ ] Card detect on J2 is captured but **unrouted with no GPIO allocated** — needs a pin-map
      revision or a formal decision to drop the feature
- [ ] 16 deferred `*_TBD` nets (crystal, matching, AAT, antenna) — intentional, not oversights
- [ ] **Re-establish the absolute ERC baseline under one fixed `kicad-cli` invocation.** The
      "0 real violations" figure quoted in earlier sessions does not reproduce; changes are
      currently validated by *delta*, which is sound but not a substitute

**Never yet validated on hardware:**

- [ ] **TCA9535PWR** (U60 + U61) — first-ever validation happens on Beta
- [ ] **MAX17048** fuel gauge — never bench-validated on AQROOT
- [ ] **ICS-43434 mic** — first live capture still outstanding
- [ ] True standby current — **the ~2-week figure is an ESTIMATE and must not be published**

**Firmware debt created by locked hardware decisions:**

- [ ] Replace the PN532 I2C NFC driver with an **ST25R3916 SPI** driver
- [ ] Add a CC1101 driver and a **dual-radio manager** enforcing one-TX-at-a-time — which must
      now also drive `SX1262_RXEN` on U61 P16
- [ ] Add a TCA9535 driver, a real RMT-based IR driver, and reconcile `config.h` with
      [[11 - Beta Pin Map v0.2]]

---

## Related

[[00 - Overview]] · [[01 - Hardware Core]] · [[05 - Design Decisions Log]] ·
[[06 - BOM and Cost Tracker]] · [[07 - Build TODO Tracker]] · [[11 - Beta Pin Map v0.2]] ·
[[12 - RF and Antenna Plan v0.1]] · [[13 - Power Budget and Battery Runtime v0.1]] ·
[[15 - Enclosure Field Slate v3]] · [[Alpha-Tests/HARDWARE-NOTES]] · [[Firmware/README]]
