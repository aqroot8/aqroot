# AQROOT Full Beta v2 — Changelog

Chronological engineering changes and why they happened. Newest entries at the
top. Each entry records what changed, not merely that something happened.

This file records **decisions and design changes**. Routine document edits are
not entries. A change that alters what gets built, or what may not be built, is
an entry.

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
