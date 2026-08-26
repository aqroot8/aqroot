# FBV2-CLOUD-001 — Make the Full Beta v2 harness portable (Windows + Linux)

**Date:** 2026-08-26
**Starting HEAD:** `a1cc687`
**Worker:** `aqroot-worker.us-central1-a.c.aqroot-cloud.internal` — Ubuntu 24.04, KiCad 10.0.5
**Result:** **PASS**

**Infrastructure / tooling only. NO PCB PROGRESS EARNED. Overall stays 74 %, routing stays 0 %.**

Full audit: [`audits/2026-08-26-cloud-harness-portability.md`](../audits/2026-08-26-cloud-harness-portability.md)

---

## What this was

The first AQROOT task on the Google Cloud Linux worker. Not a routing task —
no copper, no placement, no schematic, no architecture. The single question was
whether the *committed* check and routing scripts run on a second machine.

They did not. Four scripts carried the Windows development workstation's own
filesystem as string literals: `P:/New folder (2)/bin/kicad-cli.exe`,
`P:/Vaults/ClaudeVault/AQROOT/hardware/beta-v2/kicad/aqroot-beta-v2`, and
`"<KICAD>/bin/python.exe"` usage lines. Thirteen active portability defects in
total, tabulated in §3 of the audit.

## The one that mattered

`router_regression.py` had a `KICAD_CLI` override already — but its **default**
was the Windows path. Unset on Linux, it produced a kicad-cli that does not
exist, and because both DRC call sites use
`subprocess.run(..., capture_output=True)` with no returncode check, the failure
was swallowed and surfaced one line later as a missing JSON file. "The DRC tool
is absent" was indistinguishable from an I/O error, inside the script that
decides whether copper may touch the authoritative board. That is the G1 defect
class from FBV2-P2-002A, reappearing one layer down.

kicad-cli is now resolved-or-stopped-loudly, so an unresolvable tool cannot
reach `subprocess.run` at all.

## What was done

- **New `hardware/beta-v2/checks/harness_paths.py`** — one place for
  `kicad_cli()`, `project_dir()`, `python_exe()`, `REPO_ROOT`, and the
  `PROJECT_CONTEXT` set that the G1 guard depends on.
  - **kicad-cli:** `KICAD_CLI` → `shutil.which` → documented Windows fallbacks
    (`os.name == 'nt'` only) → **loud `SystemExit`, never a silent default**.
  - **project dir:** `AQROOT_BETA_V2_PROJECT`, else derived from `__file__` by
    walking `checks/ → beta-v2/ → hardware/ → repo root`. No username, no mount
    point, no home directory, no vault path.
  - **interpreter:** `sys.executable`, always.
- **`path_role_util.py` and `router_regression.py`** consume it. Nothing else
  was rewritten — the scripts that already derived their paths from `__file__`
  were left alone. Not a refactor.
- **`.kicad_prl` removed from fork equivalence.** It is per-user KiCad editor
  state, gitignored since before the fork, and absent from a fresh clone —
  `beta-dm` has none at all. The probe was asserting a property of one person's
  KiCad session. **No fake `.prl` was generated and no local one was committed.**
- **`checks/requirements.txt`** — `numpy>=1.24`, and nothing else. `pcbnew` is
  deliberately excluded with the reason stated in the file: it comes from KiCad,
  not from pip.
- Six `.exe` usage lines in active docstrings normalised to `python`.

## What was deliberately not done

- Historical audits and transcripts containing old Windows paths were **not**
  rewritten. They record what was run at the time.
- KiCad 10's `PROPERTY_ENUM` assertion noise on Ubuntu is **not suppressed**.
  Suppressing it would hide the next real error on the same channel. Success was
  judged by exit status and test results.
- No PCB, schematic or rule file was touched to make a test pass.

## Validation on Linux — all five PASS

| script | exit | verdict |
|---|---|---|
| `p1_regression.py` | 0 | **PASS** (0 checks failed) |
| `router_regression.py` | 0 | **PASS** — ALL CHECKS, G1–G7 + G8-A..F, 9.1 s |
| `dru_probe.py` | 0 | **PASS** — 16 netclasses, 57 patterns, 0 missing |
| `netclass_probe.py` | 0 | **PASS** — 224 nets, 3 LED_BOOST |
| `fork_equivalence.py` | 0 | **PASS** — 12 inherited footprints bit-identical |

`router_regression.py` re-run with `KICAD_CLI` **unset**: PASS. G1 reports a
real DRC histogram in both runs, which is what proves kicad-cli actually ran.

## Board state — unchanged

Authoritative PCB byte-identical to `a1cc687`. **0 signal tracks, 0 signal vias.**
Schematic untouched. Placement untouched. B-34 still OPEN, D-256 still awaiting
the CTO.

**FBV2-P2-002K NOT STARTED. Nothing was routed.**
