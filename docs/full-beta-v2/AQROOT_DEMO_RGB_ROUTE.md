# AQROOT Demo RGB replacement-route promotion

**Result: PASS.** The authoritative Demo PCB now connects all three replacement
RGB sink nets from `U3.P00`-`P02` to the retained `R124`-`R126` branches. This
completes the only three intentionally open Demo replacement nets after the
accepted `ACC_5V_SW_EN` route.

## Promoted copper

The bounded route order was green, red, then blue. Each branch uses two ordinary
0.60/0.30 mm through-vias and a 0.200 mm In2.Cu haul between short B.Cu escapes.
The retained resistor-side copper was used as the destination; no accepted
copper or component placement was removed or changed.

Relative to commit `eacf65b`, the board adds 25 tracks and six vias, all on:

- `/08_BUTTONS_EXPANDERS/FRONT_RGB_R_N`
- `/08_BUTTONS_EXPANDERS/FRONT_RGB_G_N`
- `/08_BUTTONS_EXPANDERS/FRONT_RGB_B_N`

The accepted-copper multiset comparison reports zero missing objects. Board
connectivity reports `R124.1` to `U3.4`, `R125.1` to `U3.5`, and `R126.1` to
`U3.6` connected; the full-board ratsnest drops exactly **613 -> 610**.

## Authoritative KiCad gate

KiCad CLI 10.0.5 refilled zones, saved the board, and ran all severities with
schematic parity:

```text
kicad-cli pcb drc --refill-zones --save-board --format json --units mm \
  --severity-all --schematic-parity -o /tmp/aqroot-demo-rgb-authoritative.json \
  hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb
```

| DRC class | `eacf65b` | RGB routed | attributable delta |
|---|---:|---:|---:|
| footprint-library lookup | 199 | 199 | 0 |
| hole clearance | 5 | 5 | 0 |
| solder-mask bridge | 1 | 1 | 0 |
| track dangling | 3 | 0 | -3 |
| clearance | 0 | 0 | 0 |
| shorting items | 0 | 0 | 0 |
| tracks crossing | 0 | 0 | 0 |

The remaining parity/library reports are the unchanged project/library-table
baseline classes; no new electrical, geometric, or fabrication blocker is
introduced. The D-269 rule remains active, the retained battery/power copper is
unchanged, `ACC_5V_SW_EN` remains connected, and `ACC_5V_BOOST_EN` remains a
separate net. `XGPIO4`/`XGPIO5` and all Demo NC contacts are unchanged.

`hardware/beta-v2/` is untouched. The promoted Demo PCB SHA-256 is
`cb4774b5ab76eb427bd70f0fb7dde17b7a1d7eb3c860826e94efeb7c9f91e93d`.

## Next fabrication blocker

Demo-required routing is now complete. The next highest-leverage blocker is a
fabrication-release audit followed by generation and inspection of the Demo
BOM/CPL/Gerbers/drills. Do not declare `DEMO_READY_FOR_FAB` until the retained
feature/parity/safety reviews and all manufacturing-output checks pass.
