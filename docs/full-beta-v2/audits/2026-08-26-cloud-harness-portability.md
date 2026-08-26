# FBV2-CLOUD-001 — Cloud harness portability audit

**Date:** 2026-08-26
**Starting HEAD:** `a1cc687` (= `origin/master`, tracked tree clean)
**Result:** **PASS**

**THIS IS INFRASTRUCTURE / TOOLING WORK. NO PCB PROGRESS IS EARNED.**
No schematic, no authoritative copper, no placement, no electrical architecture,
no mechanical change. **PCB routing stays 0 %. Overall Full Beta v2 stays 74 %.**
Nothing here is a hardware decision and nothing here changes one.

---

## 1. Why this task exists

Every FBV2-P2 verdict so far — 002A through 002J — was measured on one Windows
workstation. That is a single point of failure for the entire evidence chain.
The programme's own standing rule is that progress is *measured, not recorded*;
a measurement that only one machine in the world can reproduce is a step back
toward recording it.

A second worker was brought up to fix that: an Ubuntu 24.04 Google Cloud
instance with KiCad 10.0.5. The harness did not run on it. Not because of
anything about the board — because four scripts carried the development
machine's own filesystem baked in as string literals:

```
KC       = r"P:/New folder (2)/bin/kicad-cli.exe"
AUTH_DIR = r"P:/Vaults/ClaudeVault/AQROOT/hardware/beta-v2/kicad/aqroot-beta-v2"
usage    = "P:/New folder (2)/bin/python.exe" hardware/beta-v2/checks/...
```

None of those is a property of the project. All three are properties of one
person's disk. This task removes them from runtime code and replaces them with
resolution policies.

### The dangerous one

`router_regression.py` and `path_role_util.py` invoke kicad-cli through

```python
subprocess.run([KC, ...], capture_output=True, text=True)
```

with **no `check=True` and no returncode inspection**. On Linux `KC` pointed at
a Windows path that does not exist, so the call raised `FileNotFoundError` — but
only after `capture_output` had already swallowed everything, and the next line
(`json.load(open(out))`) then failed on a DRC report that was never written. The
failure mode of "the DRC tool is not there" was therefore *indistinguishable at
a glance* from an unrelated I/O error, in the exact script whose job is to decide
whether copper is allowed onto the authoritative board. That is the class of
defect the G1 guard was written for, and it had reappeared one layer down.

The fix is not to add `check=True` here (that is a separate behaviour change);
it is that kicad-cli is now **resolved or the run stops loudly**, so an
unresolvable tool can never reach `subprocess.run` in the first place.

---

## 2. Preflight

| item | value |
|---|---|
| HEAD | `a1cc687` |
| `origin/master` | `a1cc687` (identical) |
| tracked tree | clean |
| authoritative PCB | unchanged vs HEAD |
| signal tracks / signal vias | **0 / 0** |
| platform | Linux 6.17.0-1022-gcp, Ubuntu 24.04, x86_64 |
| hostname | `aqroot-worker.us-central1-a.c.aqroot-cloud.internal` |
| Python | 3.12.3 — `/home/aqroot8/Vaults/ClaudeVault/AQROOT/.venv/bin/python3` |
| `import pcbnew` | OK — `10.0.5-10.0.5~ubuntu24.04.1` |
| kicad-cli | `/usr/bin/kicad-cli`, `10.0.5` |
| NumPy | 2.5.2 |
| repo root | `/home/aqroot8/Vaults/ClaudeVault/AQROOT` |

`.venv/` is listed in `.git/info/exclude` and is **not** repository content.

The venv must be created with `--system-site-packages` (or otherwise given the
distribution `pcbnew` on its path); `pcbnew` is not pip-installable — see §7.

---

## 3. Audit table — every ACTIVE portability issue found

Scope: runtime-active code and configuration under `hardware/beta-v2/checks/`.
Historical audit and transcript prose containing old Windows paths was **not**
rewritten — those documents are a record of what was run at the time and
falsifying them would be the same sin the harness exists to prevent.

| # | file | line | issue | class | fix |
|---|---|---|---|---|---|
| 1 | `path_role_util.py` | 6 | `KC = r"P:/New folder (2)/bin/kicad-cli.exe"` — no env override at all | hard-coded KiCad CLI, Windows drive letter, `.exe` | resolved via `HP.kicad_cli()` at call site |
| 2 | `path_role_util.py` | 7 | `AUTH_DIR = r"P:/Vaults/ClaudeVault/AQROOT/hardware/beta-v2/kicad/aqroot-beta-v2"` — absolute repo path incl. Obsidian vault dir | hard-coded repo path, drive letter | `HP.project_dir()`, derived from `__file__` |
| 3 | `router_regression.py` | 48 | `os.environ.get('KICAD_CLI', r'P:/New folder (2)/bin/kicad-cli.exe')` — override existed, but the **default** was a Windows path, so an unset variable on Linux silently produced a non-existent tool | hard-coded KiCad CLI fallback | `HP.kicad_cli()`, loud on failure |
| 4 | `router_regression.py` | 6 | usage line `"P:/New folder (2)/bin/python.exe" ...` | hard-coded interpreter, `.exe` | `python`, with a note on which interpreters qualify |
| 5 | `gate_p2_002f.py` | 13 | usage `"<KICAD>/bin/python.exe"` | `.exe` interpreter assumption | `python` |
| 6 | `net_ledger.py` | 10 | usage `"<KICAD>/bin/python.exe"` | `.exe` interpreter assumption | `python` |
| 7 | `p1_mech_render.py` | 9 | usage `"<KICAD>/bin/python.exe"` | `.exe` interpreter assumption | `python` |
| 8 | `p1_regression.py` | 6 | usage `"<KICAD>/bin/python.exe"` | `.exe` interpreter assumption | `python` |
| 9 | `phaseB_compare.py` | 8 | usage `"<KICAD>/bin/python.exe"` | `.exe` interpreter assumption | `python` |
| 10 | `ring_probe_002f.py` | 16 | usage `"<KICAD>/bin/python.exe"` | `.exe` interpreter assumption | `python` |
| 11 | `fork_equivalence.py` | 79 | required `aqroot-Beta-DM.kicad_prl` / `aqroot-Beta-v2.kicad_prl`, neither of which exists in a fresh clone | non-portable dependency on gitignored local editor state | row removed, ruling documented — see §6 |
| 12 | `router_regression.py`, `path_role_util.py`, `dru_probe.py`, `netclass_probe.py`, `fork_equivalence.py` | — | five independent re-derivations of repo root / project dir; two independent kicad-cli literals | duplicated resolution logic | shared `harness_paths.py` — see §11 |
| 13 | `checks/` | — | no dependency manifest; NumPy (required by `qrouter.py`) was undeclared | reproducibility | `checks/requirements.txt` — see §7 |

**Not defects, checked and cleared:**

- `net.split('/')` throughout `route_battery_block.py` — that `/` is the KiCad
  **net-name hierarchy** separator (`/01_POWER_TREE/BAT_MID`), not a filesystem
  separator. Identical on both platforms.
- Cygwin: no Cygwin-only assumption found anywhere in the active harness.
- No Linux-only absolute path literal (`/usr`, `/opt`, `/home`, `/tmp`) exists
  in active code. The scratch workspace is `checks/w/`, repo-relative.

---

## 4. KiCad CLI resolution policy

One policy, in `harness_paths.kicad_cli()`, used by every active script:

1. **`KICAD_CLI` environment variable.** Accepted as a full path (`os.path.isfile`)
   *or* as a bare command name resolved through `shutil.which`. If it is set but
   resolves to nothing, resolution **continues** to step 2 rather than dying — a
   stale variable from another machine should not defeat a working PATH — but the
   attempt is recorded and reported if everything fails.
2. **`shutil.which("kicad-cli")`** — the Linux/CI/Homebrew case, and the Windows
   case when KiCad's `bin` is on `PATH`.
3. **Documented Windows fallbacks, `os.name == 'nt'` only:**
   `P:/New folder (2)/bin/kicad-cli.exe` (the historical development machine) and
   `C:/Program Files/KiCad/10.0/bin/kicad-cli.exe` (the KiCad 10 installer
   default). A Linux worker never reaches this branch.
4. **Otherwise `SystemExit` with a message naming every location tried and the
   exact fix for both platforms.** There is deliberately **no silent default**: a
   DRC run against a kicad-cli that is not there must never look like a DRC run
   that found nothing wrong.

The result is cached per process.

**Proven on this worker, all four branches:**

| branch | invocation | result |
|---|---|---|
| 1 | `KICAD_CLI=/usr/bin/kicad-cli` | `/usr/bin/kicad-cli` |
| 1, bare name | `KICAD_CLI=kicad-cli` | `/usr/bin/kicad-cli` |
| 1→2 fallthrough | `KICAD_CLI=/no/such/kicad-cli` | `/usr/bin/kicad-cli` (via PATH) |
| 2 | `KICAD_CLI` unset | `/usr/bin/kicad-cli` |
| 4 | unset + `PATH=/nonexistent` | `SystemExit`, message lists what was tried |

`router_regression.py` was run to completion **both** with `KICAD_CLI` set and
with it unset. Both are ALL CHECKS PASS, and in both the G1 guard reports a real
non-trivial DRC histogram (`hole_clearance: 5, lib_footprint_issues: 199,
solder_mask_bridge: 1, unconnected_items: 499`), which is proof kicad-cli
actually ran rather than being quietly skipped.

---

## 5. Authoritative project directory resolution

`harness_paths.project_dir()`:

1. `AQROOT_BETA_V2_PROJECT` if set — and if it is set to something that is not a
   directory, that is a **`SystemExit`, not a silent fallback**. An explicit
   override that is wrong is a mistake to report, not to paper over.
2. Otherwise derived from `harness_paths.py`'s own location:

```
harness_paths.py
  -> hardware/beta-v2/checks/     (os.path.dirname(os.path.abspath(__file__)))
  -> hardware/beta-v2/            (os.pardir)
  -> hardware/                    (os.pardir)
  -> <repository root>            (os.pardir)
  -> hardware/beta-v2/kicad/aqroot-beta-v2
```

`os.pardir` and `os.path.join` throughout, never a literal `'..'` or `'/'`.

It depends on **nothing** outside the repository: not the Windows username, not
the Linux username, not the drive letter, not the mount point, not the home
directory, not the Obsidian vault path. Move or rename the checkout and it
still resolves; that is the whole point.

`PROJECT_CONTEXT` — the `.kicad_dru` / `.kicad_pro` / `fp-lib-table` /
`sym-lib-table` / `libraries` set that must sit beside any `.kicad_pcb` for DRC
to measure against the *project's* rules instead of KiCad's defaults — is now
stated **once**, here, instead of twice with a chance of drifting apart. That
set is the G1 guard of `router_regression.py`, the guard that exists because
FBV2-P2-002A burned a whole routing attempt on a phantom
`clearance:73, lib_footprint_issues:17` offset.

---

## 6. `.kicad_prl` ruling

**RULING: `*.kicad_prl` is NOT part of fork equivalence. Its absence is expected
local state.**

`fork_equivalence.py` required `aqroot-Beta-DM.kicad_prl` and
`aqroot-Beta-v2.kicad_prl` to exist and to match after project-name
normalisation. On this fresh clone the probe failed:

```
FAIL: missing: aqroot-Beta-DM.kicad_prl / aqroot-Beta-v2.kicad_prl
```

A `.kicad_prl` is KiCad's **per-user editor state** — last active layer, open
dialogs, window geometry, local net-inspector column widths. It is generated by
whoever opens the project, it has been in `.gitignore` since before this fork
existed (`*.kicad_prl`, under "KiCad temporary / local-state files"), and it is
therefore not, and never was, part of the fork's provenance. It was comparable
only on the single workstation that happened to have opened both projects in
KiCad. `hardware/beta-dm/kicad/aqroot-beta-dm/` contains no `.kicad_prl` at all.

The probe was asserting a property of one person's KiCad session and calling it
a property of the fork. That row is removed, with the reasoning recorded inline
so it is not re-added.

Explicitly **not** done:

- **No fake `.kicad_prl` was generated** to satisfy the probe. Manufacturing an
  input so a test passes is exactly the failure the probe was written to catch.
- **No local `.kicad_prl` was committed.** One exists on this worker —
  `hardware/beta-v2/kicad/aqroot-beta-v2/aqroot-Beta-v2.kicad_prl`, written by
  KiCad during a `pcbnew` load — and `git status --ignored` confirms it is
  ignored. It stays untracked.
- **The `.gitignore` rule was not weakened.**

Everything else about the probe is untouched: nine sheets, PCB, DRU, PRO, SCH,
README, symbol library, `fp-lib-table`/`sym-lib-table` bit-equality, all 12
inherited footprints, and the five declared footprint additions.

---

## 7. Python dependency reproducibility

Every non-standard import in the active harness was enumerated. The complete
set is `pcbnew` and `numpy` — everything else (`os`, `sys`, `io`, `re`, `json`,
`math`, `hashlib`, `heapq`, `shutil`, `subprocess`, `collections`, `tempfile`,
`time`) is standard library.

Created **`hardware/beta-v2/checks/requirements.txt`**:

```
numpy>=1.24     # qrouter.py -- A*/obstacle grids and geometry maths
```

Nothing else was added. A package is listed only if the harness stops working
without it; "might be useful" is not a reason.

**`pcbnew` is deliberately absent**, and the file says why: it ships with KiCad,
is not on PyPI, and must never be pip-installed. It is supplied by the
*interpreter* — KiCad's bundled `python.exe` on Windows, or a
`--system-site-packages` venv against the distribution KiCad on Linux. An
`import pcbnew` failure means the wrong interpreter is running, not that a
requirement is missing, and the file states that so the next person does not
`pip install pcbnew` and get an unrelated package.

Installed here: NumPy 2.5.2.

---

## 8. Platform differences were NOT hidden

KiCad 10 on Ubuntu prints, on every `import pcbnew`:

```
./kicad/include/properties/property.h(607): assert "m_choices.GetCount() > 0"
failed in PROPERTY_ENUM(): No enum choices defined
```

followed by a run of `Debug: Adding duplicate image handler for ...` lines.

**Nothing was done to suppress this.** No stderr redirection, no warning filter,
no `2>/dev/null` in any committed script. It is upstream noise from the KiCad
Python bindings; the same import goes on to report `10.0.5-10.0.5~ubuntu24.04.1`
and the board loads correctly. Hiding it would also hide the next, real error to
appear on the same channel.

Success is judged by **exit status and actual test results**, which is how all
five suites below were judged.

---

## 9. Full validation suite on Linux

All five run from the repository root with the venv Python.

| script | exit | verdict |
|---|---|---|
| `p1_regression.py` | 0 | **PASS** — `REGRESSION: PASS (0 checks failed)` |
| `router_regression.py` | 0 | **PASS** — `router_regression: ALL CHECKS PASS` (G1–G7 + G8-A..F), 9.1 s |
| `dru_probe.py` | 0 | **PASS** — 16 netclasses / 0 missing, 57 patterns / 0 matching nothing, 224 nets |
| `netclass_probe.py` | 0 | **PASS** — 224 nets scanned, 3 resolve to LED_BOOST, `/07_IR/IR_LED_K` stays Default |
| `fork_equivalence.py` | 0 | **PASS** — 12 inherited footprints bit-identical, 5 declared additions |

`router_regression.py` additionally re-run with `KICAD_CLI` unset: **PASS**.

Selected `router_regression` evidence:

- G1 scratch baseline DRC **==** authoritative baseline DRC —
  `{hole_clearance: 5, lib_footprint_issues: 199, solder_mask_bridge: 1, unconnected_items: 499}`
- G3 LTC_OV min segment 0.250 mm ≥ 0.150 mm floor
- G6 ratsnest deltas exactly as expected (−3 BAT_MID, −2 LTC_OV)
- All five proved land-pattern conflicts unchanged (U11.2 0.200 mm, U14.2/U14.3
  0.240 mm, U18.8/U18.9 0.250 mm)

**No PCB, schematic or rule file was modified to make any test pass.** After the
full suite, `git diff HEAD -- hardware/beta-v2/kicad/ hardware/beta-dm/kicad/` is
empty, and the board still carries **0 signal tracks and 0 signal vias**.

---

## 10. Windows backward-compatibility review

Static review only — no attempt was made to emulate Windows on the cloud worker,
which would produce a result that proves nothing.

| requirement | verdict | evidence |
|---|---|---|
| environment override works | **YES** | `KICAD_CLI` is step 1; `AQROOT_BETA_V2_PROJECT` is step 1. Both exercised. |
| Windows paths still supported when supplied | **YES** | `KICAD_CLI` is used verbatim when `os.path.isfile` accepts it — `C:\...\kicad-cli.exe` passes unchanged into `subprocess.run`. No normalisation, no POSIX-ifying, no `.exe` stripping. |
| no Linux-only literal became mandatory | **YES** | No `/usr`, `/opt`, `/home`, `/tmp` literal exists in active code. The only absolute literals in the harness are the two **Windows** fallbacks, and they are guarded by `os.name == 'nt'`. |
| Windows fallback retained | **YES** | `P:/New folder (2)/bin/kicad-cli.exe` still resolves on the original machine with no configuration at all — behaviour there is unchanged. |
| path handling uses `os.path` / `sys.executable` | **YES** | `os.path.join` / `os.path.dirname` / `os.path.abspath` / `os.pardir` throughout; `shutil.which` for PATH; `sys.executable` for the interpreter. |

**Windows behaviour is strictly a superset of what it was.** The old machine
finds kicad-cli at step 3 exactly where it always did, and `AUTH_DIR` now
resolves to the same `P:/Vaults/ClaudeVault/AQROOT/hardware/beta-v2/kicad/aqroot-beta-v2`
it was hard-coded to — because that *is* where the checkout lives there. Nothing
was taken away; a machine-independent derivation was put underneath it.

---

## 11. `sys.executable` verdict

**No subprocess in the active harness launches a Python interpreter.** The only
`subprocess.run` calls in `hardware/beta-v2/checks/` are the two kicad-cli DRC
invocations (`path_role_util.py:34`, `router_regression.py:113`). There is
therefore no hard-coded interpreter path in runtime code to remove, and none
was introduced.

`harness_paths.python_exe()` returns `sys.executable` and is provided as the
single answer for any future script that does need to spawn one. Hard-coding
either `P:/New folder (2)/bin/python.exe` or a Linux path is precisely the
defect this task removed; the interpreter that can already `import pcbnew` is by
construction the right one to hand a child process.

The six `"<KICAD>/bin/python.exe"` usage lines in active script docstrings were
normalised to `python`. They are documentation, but they are documentation that
was telling a Linux reader to run a Windows binary.

---

## 12. Shared helper — scope of the simplification

Five scripts re-derived the repository root or the project directory
independently, and two carried independent kicad-cli literals. That duplication
is the mechanism by which this defect class recurs: fixing four of five sites is
indistinguishable from fixing all five until the fifth one runs.

**`hardware/beta-v2/checks/harness_paths.py`** (new, ~140 lines including the
rationale) holds exactly four things: `REPO_ROOT`, `project_dir()`,
`kicad_cli()`, `python_exe()`, plus the `PROJECT_CONTEXT` tuple and the project
filename constants.

**This is not a refactor.** Two files were changed to consume it
(`path_role_util.py`, `router_regression.py`); the scripts that already derived
their paths correctly from `__file__` — `dru_probe.py`, `netclass_probe.py`,
`fork_equivalence.py`, `p1_geometry.py` and the rest — were **left alone**. They
were not broken, and rewriting working code during a portability fix is how a
portability fix turns into a regression. `path_role_util.py` keeps `AUTH_DIR`,
`PCBNAME`, `DRUNAME` and `NEEDED` as module attributes so
`replay_battery_block.py` and every other consumer of `RU.*` is unaffected.

kicad-cli is resolved **lazily**, at the call site, not at import. Importing
`path_role_util` on a machine that only needs its `pcbnew` half must not die
because KiCad's CLI is missing.

---

## 13. What was NOT touched

- Schematic — untouched.
- Authoritative PCB copper — untouched, byte-identical to `a1cc687`.
- Placement — untouched.
- Electrical architecture — untouched.
- Mechanical design — untouched.
- `.kicad_dru`, `.kicad_pro`, netclasses — untouched.
- Router algorithms, `qrouter.py`, `route_battery_block.py` logic — untouched.
- Historical audits and transcripts containing old Windows paths — untouched.
- Project percentage — **74 %, unchanged. Routing 0 %, unchanged.**
- B-34 — still **OPEN**. D-256 — still **awaiting the CTO**. Nothing here
  touches either; FBV2-P2-002K is not started.

---

## 14. Standing conclusion

The Full Beta v2 check and routing harness now runs, unmodified, on both the
Windows development machine and the Ubuntu 24.04 cloud worker, and all five
qualification suites PASS on the worker. Every FBV2-P2 verdict from here on is
reproducible on a second machine — which is what makes it evidence rather than
a report.
