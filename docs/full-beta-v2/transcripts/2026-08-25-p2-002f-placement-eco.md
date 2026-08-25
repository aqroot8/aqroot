# FBV2-P2-002F — session transcript

**Task:** targeted battery-block placement ECO, then a routeability proof on scratch.
**Result: FAIL** on section 14's no-partial-pass rule. **The authoritative PCB is byte-identical to
`24f6611` and the placement ECO is NOT applied to it.**

## What was run, in order

1. **Preflight** — HEAD `24f6611`, clean tree, PCB `md5 a908ced…` with 0 tracks / 0 vias, In1 plane
   intact, ERC 0/27, DRC `{solder_mask_bridge: 1, unconnected 499}`, ratsnest 781, five probes PASS.
2. **`place_search_002f.py`** — stage 1 enumerated 13 284 U18 poses on a 0.25 mm grid × 4 rotations;
   2 490 cleared courtyard collision, board edge, rule areas and the §4 Kelvin envelope; 1 331 kept
   both Kelvin branches ≤ 10 mm, mismatch ≤ 5 mm and a 1.50 mm `BAT_PROTECTED_P` corridor. Stage 2
   dissolved the divider wall into a service ring. Stage 3 proved escapes on real scratch boards.
3. **Four Phase A attempts diagnosed four placement defects**, each caught only by routing:
   crossing targets, stacked targets, a dead-cell compaction that deleted its own channels, and
   parts on the far side of J4.
4. **`ring_probe_002f.py`** — the ring is now chosen by the real router, laying the plan's own
   prefix (trunk, `U11.2` flare, `BAT_MAIN` chain) before routing all eight U18 pins. **8/8.**
5. **`gate_p2_002f.py`** — section 12 gate, **PASS 11/11**, 49 escapes laid simultaneously, 0 lost.
6. **Phase A run 7** — 70 connections, ratsnest 781 → 709 (−72), DRC identical to baseline at every
   step, zero out-of-scope copper, 23 of 29 in-scope nets single components. **FAIL** on six split
   nets.
7. **Phase B NOT RUN** (section 17 gates it on Phase A).
8. **Validation** — p1_regression, router_regression, dru_probe, netclass_probe, fork_equivalence
   all PASS; ERC 0/27; DRC identical to baseline; netlist byte-verified unchanged (225 nets, 0 pad
   sets differ).

## Process notes worth keeping

* **Seven Phase A attempts were started; four were stopped deliberately** once their placement was
  diagnosed, rather than left to burn an hour proving a known defect. Each stop is recorded with the
  log that justified it (`phaseA_ring1`, `phaseA_ring2`, `phaseA_dcpack`, `phaseA_run6`).
* **The 15-minute watchdog traceback in run 6's log is not a hang** — it is
  `faulthandler.dump_traceback_later` firing on schedule while the process sat inside a `kicad-cli`
  DRC subprocess. No watchdog intervention was needed in any run.
* **Time was lost to polling the run log rather than letting the armed monitors report.** The
  engineering conclusions are unaffected, but the session would have reached the same verdict in far
  fewer steps.

## Files added

| file | what it is |
|---|---|
| `checks/place_search_002f.py` | the bounded U18 pose + ring search (§11) |
| `checks/place_deadcell_002f.py` | the dead-cell cluster optimiser (§6) |
| `checks/ring_probe_002f.py` | ring selection by the **real router** |
| `checks/gate_p2_002f.py` | the section 12 escape-only proof gate |
| `checks/place_p2_002f.py` | the searched placement ECO — **applied to nothing** |
| `checks/phaseB_compare.py` | the section 17 replay comparison (unused; Phase B did not run) |
| `checks/route_battery_block.py` | PR-30, PR-32, PR-33 and the ECO / replay hooks |
