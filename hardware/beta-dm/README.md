# AQROOT Beta DM (Demo Model)

`hardware/beta-dm/` is a **derivative of the full Beta**, created from the frozen
full-Beta head `0f53205` (tag `beta-full-reference-v1`).

## What Beta DM is

A physical demo model:

- two-unit AQROOT-to-AQROOT LoRa proof (the flagship demo)
- internal and marketing demonstrations
- selected real hardware demonstrations
- minimum remaining routing and bring-up burden

Beta DM is **not** the final customer product. Features deferred here are deferred
for the DM only; every cut is recorded in [BETA-DM-SCOPE-LEDGER.md](BETA-DM-SCOPE-LEDGER.md)
with its Final-product restoration status.

## What Beta DM is not allowed to touch

`hardware/beta/` is **read-only** for all Beta-DM work. Every Beta-DM commit must
prove `git diff beta-full-reference-v1 -- hardware/beta/` is empty. If Beta changes,
the work is aborted and reverted.

## Layout

```
hardware/beta-dm/
  kicad/aqroot-beta-dm/
    aqroot-Beta-DM.kicad_pro     project
    aqroot-Beta-DM.kicad_sch     root sheet
    aqroot-Beta-DM.kicad_pcb     board
    aqroot-Beta-DM.kicad_dru     design rules (identical to Beta at fork)
    01..09_*.kicad_sch           hierarchy (filenames unchanged from Beta)
    libraries/                   project symbol/footprint libraries (own copy)
    fp-lib-table, sym-lib-table  ${KIPRJMOD}-relative, so they resolve locally
  BETA-DM-SCOPE-LEDGER.md        authoritative scope classification
  BETA-DM-LEAN-SCOPE.md          LEAN Demo Model scope + U15 audit
  BETA-DM-LEAN-XGPIO-SELECTION.md  which four XGPIO stay active, and why
  BETA-DM-LEAN-ROUTING.md        Lean scratch routing study
  BETA-DM-LEAN-RESTORATION.md    Full-Beta restoration ledger for Lean cuts
  BETA-DM-UNROUTED-LEDGER.md     every ratsnest line, A/B/C/D buckets
  BETA-DM-DNP-LIST.md            exact DNP set + U9 bus-safety audit
  BETA-DM-MCU-RELEASE.md         minimum MCU release recomputation
```

## Lean Demo Model scope

Beta-DM is a **Lean** demo model: the J5 expansion header stays physically
complete and Full-Beta-restorable, but only **four** of the fourteen XGPIO are
must-work for the demo, alongside external I2C, FAST_IO, WAKE and 3V3/GND
header access. Start at [BETA-DM-LEAN-SCOPE.md](BETA-DM-LEAN-SCOPE.md).

**Deliberately not copied** (documented rather than duplicated):

- `hardware/beta/kicad/aqroot-beta/floorplan-views/` (16 MB of full-Beta render
  history) — DM regenerates its own views when it needs them
- `hardware/beta/kicad/aqroot-beta/vendor/` (4.7 MB of vendor datasheets) — the
  same documents apply to both branches and are read-only reference

Neither is electrically or semantically part of the design. The copy-equivalence
proof below covers everything that is.

## Fork provenance and copy-equivalence proof

Forked at `0f53205`, tagged `beta-full-reference-v1`.

Full-Beta source hashes at the fork:

| file | sha256 |
|---|---|
| `aqroot-Beta.kicad_pcb` | `d001cf4b22d2dd046d9dd1ad6c6e74728c89c9ada624d428d437472808f0f1df` |
| `aqroot-Beta.kicad_dru` | `a353a608a0c54bbc3d1c07b31d5b728d967c502484aac3c556e4a326e6c25ef6` |
| `aqroot-Beta.kicad_pro` | `6210c704d545210a792f254d16901b85fe121a01411bb934fe67184033e2e7bb` |
| `aqroot-Beta.kicad_sch` | `3243ff8f28bde2c7b5533ba7782299f2d5a74183be7a6b0a24472fcb55c308ab` |

Equivalence of the derivative at creation:

| check | Beta | Beta DM | verdict |
|---|---|---|---|
| PCB bytes | — | — | **byte-identical** (only the filename changed) |
| footprints | 188 | 188 | equal |
| pads / netted pads | 776 / 703 | 776 / 703 | equal |
| track segments | 1517 | 1517 | equal |
| arcs | 0 | 0 | equal |
| vias | 270 | 270 | equal |
| zones (of which rule areas) | 41 (40) | 41 (40) | equal |
| distinct nets on pads | 176 | 176 | equal |
| Edge.Cuts items | 12 | 12 | equal |
| pad→net map sha256 | `19340845d4ff89c936a1b3c0320232ae46c84928fb0cdd6ae8c505aad35c0362` | same | equal |
| exported netlist | 20 622 lines | 20 622 lines | **identical except the source path, the export timestamp and the root sheet filename** — every component, reference, footprint and net node matches |
| DRC | 0 errors, 240 warnings, 281 unconnected, 0 parity | 0 / 240 / 281 / 0 | no regression |
| ERC | 58 violations (5 errors, 53 warnings) | 58 (5 / 53) | no regression |

Only two classes of edit were made to the copy, both mechanical:

1. project files renamed `aqroot-Beta.*` → `aqroot-Beta-DM.*`, and the two
   `filename` fields inside the `.kicad_pro` updated to match;
2. the hierarchical instance project key renamed in every schematic:
   `(project "aqroot-Beta"` / `(project "aqroot-beta"` → `(project "aqroot-Beta-DM"`
   (both spellings existed in the Beta tree; each `(instances ...)` block holds
   exactly one `(project ...)` entry, so the rename creates no duplicates).

All edits were byte-level replacements on files opened in binary mode; CRLF line
endings are preserved verbatim (`.gitattributes` marks KiCad sources `-text`).

## Firmware

Do **not** fork firmware. One tree, one DM build configuration: `CONFIG_AQROOT_DM`
(see `Firmware/src/config.h` and `Firmware/platformio.ini`, env `esp32-s3-aqroot-dm`).
