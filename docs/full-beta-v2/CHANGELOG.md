# AQROOT Full Beta v2 — Changelog

Chronological engineering changes and why they happened. Newest entries at the
top. Each entry records what changed, not merely that something happened.

This file records **decisions and design changes**. Routine document edits are
not entries. A change that alters what gets built, or what may not be built, is
an entry.

---

## 2026-08-22 — Battery safety architecture finalised; **FBV2-A1 PASSED** (FBV2-PWR-002)

Documentation only. No design file touched.

**FBV2-A1 = PASS** — the first gate to pass since FBV2-A0, and the largest
remaining architecture unknown. All six criteria closed, all 13 power/fault cases
defined, no power-tree branch TBD. Next gate: **FBV2-A2, mechanical interface
freeze.**

**Candidate B selected and specified to component level** (D-065). The design
turns on one structural fact: **no passive switch can distinguish a 0 V cell from
a reversed one** — an N-FET referenced to a positive rail sees V_GS ≈ +3 V at 0 V
and ≈ +6.7 V at −3.7 V, so a reversed cell turns it *harder on*; the P-FET
arrangement fails the same way. An active, GND-referenced comparison is therefore
mandatory. The chosen sensing network is a **matched ratiometric bridge** whose
trip condition reduces to **V_BAT = 0 independent of VBUS** — supply-independence
by construction rather than by trimming. Handoff is taken from the **LTC4368
`FAULT` pin**, which is asserted precisely while VIN is below UVLO, so the
protection controller itself decides when it has taken over — no extra threshold,
no possibility of both paths being active. Recovery current **5–10 mA** (~0.004 C),
supplied from **VBUS rather than SYS** so the branch is dead by construction
without USB and costs **zero battery-side standby**.

**The pass path changes to P2** — two back-to-back stages in **two separate
packages**. A precise finding corrected the earlier account: **P1 fails one of the
two single-FET-short cases, not both.** A short on the `BAT_RAW`-side FET is
already blocked by its partner; it is specifically the **`BAT_PROT`-side** FET
whose short lets a reversed cell through. P2 leaves one complete back-to-back pair
intact under any single short, and additionally keeps the LTC4368's electronic
breaker functional with a FET shorted. Two die sharing one leadframe cannot be
called independent, so the two stages must not share a package.

**The previous fuse-and-clamp compliance argument is withdrawn as invalid.** A
Schottky sitting at ≈0.8–1.0 V does not protect a −0.3 V absolute maximum, and
ruling D was right to refuse it. With isolation doing the work, the **clamp is
demoted to secondary** duty (ESD, transient, double-fault) and the **fuse is
resized 3 A → ≈5 A**, because it is now a backstop that must not pre-empt the
3.33 A electronic breaker. Its one genuinely irreplaceable role is a harness short
between `BAT_RAW` and GND *upstream* of the FETs, where the breaker cannot act.
**PTC remains rejected.**

**Honest residual, recorded rather than smoothed over:** Candidate B is *not*
tolerant to every single failure — four failures each individually enable current
into a reversed cell. It meets the requirement as written because `R_LIM` bounds
every one to **≈13 mA (~0.007 C)**, `D_REC` keeps the branch unidirectional under
all faults, and the condition is self-annunciating. A fully redundant variation is
documented and **not** recommended: it would trade that bounded residual for a
permanent oscillation in the far more common battery-absent state.

**PCAL9535APW,118 locked for both expanders** (D-066), closing the four facts the
previous audit could not verify. **GPIO38 + GPIO47 remain locked** (D-067).

Progress 15% → 20%, held deliberately low: two of twelve gates, both paper, with
mechanical untouched.

---

## 2026-08-22 — Power architecture closed to a single open decision (FBV2-PWR-001)

Documentation only. No design file touched.

**Expander family locked** (D-061): both `U2` and `U3` become NXP
`PCAL9535APW,118` (LCSC C2669683) — an architecture lock, with the land-pattern
audit still required before fabrication. **Native pair locked** (D-063):
`NATIVE_A` = GPIO38, `NATIVE_B` = GPIO47, with `SX1262_DIO1` moving to the
internal expander and `BUSY` staying native. GPIO43 leaves the public connector.

**The SX1262 lock condition was met from a primary source.** Semtech
`DS.SX1261-2.W.APP` Rev. 1.2 §13.3.4 states verbatim that a DIO mapped to one IRQ
clears when that flag clears, and that with several IRQs mapped *"the DIO remains
set to one until all bits mapped to the DIO in the IRQ register are cleared."*
DIO1 is level-held, so an expander input with no capture register can service it.

**Two prior positions were corrected by the full LTC4368 datasheet.** P-13 is
**closed**: inrush is a designed parameter, `I_INRUSH = (C_OUT/C_GATE) ×
I_GATE(UP)`, giving ≈350 mA against a 3.33 A trip — and RETRY latch-off applies
to *forward* overcurrent only, while reverse faults reconnect automatically once
VOUT falls 100 mV below VIN. The earlier concern rested on an incomplete reading.

**The fuse-and-clamp language correction (D-064) was justified, and the analysis
vindicates it.** At the 20–25 A a 1S pack can deliver, a Schottky clamp sits at
≈0.8–1.0 V — about **3× the BQ25185 `BAT` −0.3 V absolute maximum**. The clamp
improves the excursion roughly fourfold but does **not** bring it inside the
limit. Both elements remain **REQUIRED** — the fuse because without it the clamp
is a permanent short across a Li-ion cell — but the residual is now named (P-12)
rather than assumed away. A **PTC is rejected** for this position: too slow, and
its auto-retry re-applies the fault every cycle.

**Dead-cell recovery is now the only thing blocking FBV2-A1.** The LTC4368 cannot
help here — VIN is the supply pin with a 2.2 V UVLO, and VOUT is a sense input
whose charge-pump role only engages above ~5 V, so system-side power cannot run
the controller. A single MOSFET also cannot distinguish a 0 V cell from a
reversed one: **both turn it more on**, so an explicit GND-referenced sensing
element is mandatory. Four candidates analysed; **Candidate B** — a
hardware-qualified comparator interlock, no firmware dependency, ~0 A into a
reversed cell — is recommended for the product, with service-only accepted as
defensible for the first five boards. **Not approved, so the gate is not passed.**

Progress 13% → 15%. **FBV2-A1 FAIL, 5 of 6 criteria closed.**

---

## 2026-08-22 — Critical architecture reconciled; no-respin policy established (FBV2-ARCH-002)

Documentation only. No design file touched.

**New standing policy: FIRST FIVE FULL BETA PCBAs — NO-RESPIN RECOVERY POLICY
(D-049).** Full Beta v2 Revision 1 must be designed so that reasonable
configuration and performance uncertainty is recoverable through *planned*
component rework — DNP/FIT options, 0 Ω source-selection links, accessible tuning
passives, test points — rather than through a board respin. Safety-critical power
paths are explicitly excluded: no ad-hoc bypasses around battery protection
merely for reworkability.

**An independent second-opinion review was archived verbatim** at
`reviews/2026-08-22-independent-cto-power-nfc-review.md`, marked
**ADVISORY — NOT AUTOMATICALLY AUTHORITATIVE**. It corrected the primary
engineering work on three points, and the corrections were accepted:

- **Discrete back-to-back N-FET reverse protection is withdrawn.** It is not
  under-specified but *unrealisable at 1S* — available V<sub>GS</sub> from any rail
  on this board is 0.3–1.5 V, and the P-channel variant that avoids a charge pump
  turns both FETs hard on into a reversed cell, creating the fault it was added to
  prevent. **LTC4368-1 adopted** (the `-2`'s −3 mV reverse trip would block
  charging outright).
- **"STAT1 only" was wrong, and so was the premise behind it.** BQ25185 SLUSF65A
  §7.3.10 places the STAT2 toggle in the **battery-absent** limit cycle, not in
  charge-complete/sleep — those are one state with both pins HIGH. STAT1 alone
  conveys only fault/no-fault. **Both are exposed**, with the wake-storm solved by
  changing the expander rather than by dropping a signal.
- **TPS22913B/C was the wrong replacement** for TPS22918 — DSBGA 0.9 × 0.9 mm only,
  and no current limit. **TPS22950C** adopted: RCB confirmed for the C variant
  (the L variant has none), leaded SOT-23-thin, adjustable limit, thermal
  shutdown.

**Verified this pass.** The TPS61169 `CTRL` pin has an internal **pull-down**,
which closes the last blocking condition on moving `DISP_BL_CTL` to GPIO46 and
frees GPIO47. **GPIO38 replaces GPIO43** as `NATIVE_A`, removing ROM-UART
push-pull contention from the public connector entirely.

**The mandatory power/fault state table now exists** — eleven cases across USB,
battery, power-switch and accessory states. Cases 1, 2, 5, 6, 8, 9 and 10 are OK
or correctly blocked. **Case 4 (dead cell) and Case 11 (hot insertion) are
UNRESOLVED and block schematic lock**, and Case 7 (shorted pass FET + reversed
cell) is only survivable with a series fuse and a Schottky clamp, which are
therefore required rather than optional.

**NFC ships at 3.3 V with a full no-respin 5 V fallback.** Two mutually exclusive
0 Ω links guarantee the sources can never be shorted. Pre-fit the inductor, the
FB divider and both boost capacitors; keep the TPS61023 and the 5 V link DNP.
Conversion is 3–9 soldering operations with exactly one fine-pitch part — no BGA
or QFN rework, no trace cuts, no bodge wires.

**Volume Up/Down removed from the Full Beta v2 mechanical requirements.**

**FBV2-A1 assessed: CANNOT PASS.** Four of eight criteria are resolved (20-pin
map, default NFC, NFC fallback, accessory power). Four remain — expander family,
native pair, reverse-protection topology completeness, and power-tree stability —
and three of those close with document reads. Progress 10% → 13%.

---

## 2026-08-22 — Architecture direction locked, blockers verified (FBV2-ARCH-001)

Documentation only. No design file touched. Commit `890db0b` pushed to
`origin/master` (`b8b5ebd..890db0b`).

**CTO rulings A–K recorded** as D-018, D-026, D-033…D-041, D-046…D-048. Four
pending decisions closed: P-05 (RGB removed), P-06 (RootProbe IRQ retired),
P-08 (IPEX → pigtail → bulkhead), P-09 (LoRa deep-sleep wake not required).

**Verification against vendor datasheets changed three things.**

- **The NFC supply split cannot be built.** ST25R3916 DS12484 Rev 3 p. 39: *"VDD
  and VDD_TX must be connected to the same power supply"*, with the difference
  capped at ±0.3 V absolute maximum. The requested 3.3 V / 5 V split would apply
  1.7 V across that pair. **The as-built rail assignment is correct**, and the
  pre-design audit's recommendation to change it was wrong and is withdrawn. The
  real residual question — what VDD does while the boost is off — is now P-10,
  with a 3.3 V-only NFC option that would delete eight components.
- **The proposed native-GPIO reclaim would have broken recovery.** Moving
  `NFC_IRQ` to GPIO46 makes ROM download boot conditional on NFC interrupt state,
  because the ST25R3916 IRQ is active-high, latches until read over SPI, and is
  not reset by an ESP32 reset. Substituted: move `DISP_BL_CTL` to GPIO46 and
  expose **GPIO47** as `NATIVE_B`. GPIO47 is strictly better — no power-up glitch,
  20 mA drive, unrestricted priority — and D-041 removed the only reason to want
  GPIO18's RTC capability.
- **`TPS22918` fails the accessory-isolation requirement.** Its integrated body
  diode conducts VOUT→VIN, so a powered accessory can back-power `+3V3`.
  Replacement identified in the TPS22913B/C class.

**Two prior findings were confirmed wrong and are corrected in the record:** the
TCA9517A *does* guarantee high-impedance pins when powered off and 5.5 V
tolerance while unpowered, so it passes; and the TPS61023 *does* provide true
load disconnect plus integrated output OVP.

Reverse-polarity architecture compared across three candidates and **discrete
back-to-back N-FETs recommended** over the LTC4368-1, primarily on quiescent
current (sub-µA vs ~80 µA) — flagged for independent second opinion as
instructed. A reverse-current-blocking load switch was evaluated and
**disqualified for this position**: it would block the charging direction.

Progress raised 8% → 10%. **No gate passed.** FBV2-A1 remains IN PROGRESS with
P-01, P-02, P-04, P-07 and P-10 open. **FBV2-A2 (mechanical interface freeze)
recommended as the next gate** — it is the long pole and nothing blocks it.

---

## 2026-08-22 — Full Beta v2 engineering record established (FBV2-DOC-001)

Documentation infrastructure only. No design file was touched.

- Created `docs/full-beta-v2/` as the authoritative engineering record.
- Established the precedence rule: `CTO_DECISIONS.md` outranks audits, which
  outrank architecture notes, which outrank transcripts.
- Made `transcripts/` append-only.
- Preserved the 2026-08-22 pre-design engineering audit verbatim under
  `audits/`, pinned to repository HEAD `b8b5ebd`.
- Preserved the FBV2-AUDIT-001 CTO prompt and Claude Code response verbatim
  under `transcripts/`.
- Opened the gate table FBV2-A0 through FBV2-B3 and recorded FBV2-A0 as PASS.

---

## 2026-08-22 — Full Beta v2 direction established

- **Beta-DM fabrication paused before payment.** The design-side release stands
  and no money has been committed. Beta-DM is retained as the preserved fallback
  and manufacturing baseline, not cancelled.
- **Full Beta v2 made the primary design.**
- **Decided not to blindly continue frozen Full Beta.** Its freeze recorded 281
  unconnected items and 58 ERC violations; it is a feature reference, not a
  fabrication-ready baseline. Its decisions are re-verified rather than
  inherited.
- **Beta-DM becomes the implementation / manufacturing baseline.** Full Beta v2
  is derived from it — its resolved MPNs, its validated blocks, its routing and
  DFM lessons.
- **Removed HOME from the future product.**
- **Volume Up / Down removed from the enclosure plan.** Audit finding: they
  never existed electrically. `SW2`-`SW8` are UP / DOWN / LEFT / RIGHT / A / B /
  HOME. Volume controls existed only in Field Slate v5 section 5, which must be
  corrected so enclosure CAD is not driven by phantom controls.
- **Physical BOOT retained but hidden/recessed.** It remains the last-resort
  recovery path when flash is blank or hard-bricked.
- **Software recovery required in addition to physical recovery**, with ROM
  download mode and firmware/OTA recovery held explicitly distinct — they fail
  in different situations and must never be conflated in UI copy.
- **Microphone retained** (ICS-43434 I2S MEMS, carried forward unchanged).
- **Speech output retained.** Not downgraded to a buzzer. MAX98357A-style I2S
  Class-D remains the leading architecture; the audit found no materially
  simpler option, because the ESP32-S3 has no DAC.
- **IR retained internally** — not removed, not moved to an accessory.
- **Community expansion target changed from 26 pins to 20 pins**, with a future
  requirement that the connector be keyed, shrouded/polarized and recessed.
- **External I2C retained**, pending validation of its protection, buffering and
  backfeed behaviour before architecture lock.
- **First Full Beta v2 pre-design audit completed** — read-only, pinned to
  repository HEAD `b8b5ebd`, zero repository changes. It established the
  measured GPIO budget (zero free native pins), three candidate 20-pin connector
  architectures, and the blocker set B-01 through B-16 now tracked in
  [PROGRESS.md](PROGRESS.md).
