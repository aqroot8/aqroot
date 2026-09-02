# AQROOT Demo ACC_5V_SW_EN route promotion

**Result: PASS.** The authoritative Demo PCB at
`hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb` now routes only
`ACC_5V_SW_EN`. The board was refilled and checked with KiCad CLI 10.0.5
against commit `2fd0fae` and `AQROOT_DEMO_REFILLED_BASELINE.md`.

## Promoted route

The route connects all four required endpoints:

- `U3.P03` / U3 pad 7
- `U22.ON` / U22 pad 1
- `R131.1`
- `TP47.1`

The added copper is 19 track segments, four 0.60/0.30 mm through-vias, and
78.983 mm of 0.200 mm track. Eleven segments are on B.Cu and eight are on
F.Cu. No retained component or copper was moved. A geometry multiset comparison
against `2fd0fae` found zero removed track/via objects and exactly 23 added
objects, all on `/ACC_5V_SW_EN`.

KiCad connectivity reports all four endpoint pads in the component reached from
U3.7. U3.7 belongs to `/ACC_5V_SW_EN`; U3.16 remains on the separate
`/ACC_5V_BOOST_EN` net. `R131` and `TP47` remain present and connected, so the
D-186 reset-safe pull-down and independent boost/switch sequencing topology are
preserved.

## Refill and DRC gate

KiCad CLI 10.0.5 performed a real zone refill and saved the board:

```text
kicad-cli pcb drc --refill-zones --save-board --format json --units mm \
  --severity-all --schematic-parity -o /tmp/aqroot-demo-acc-final.json \
  hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb
```

The final DRC signature is identical to the authoritative refilled baseline:

| DRC class | baseline | routed/refilled | attributable delta |
|---|---:|---:|---:|
| footprint-library lookup | 199 | 199 | 0 |
| hole clearance | 5 | 5 | 0 |
| solder-mask bridge | 1 | 1 | 0 |
| track dangling | 3 | 3 | 0 |
| clearance | 0 | 0 | 0 |
| shorting items | 0 | 0 | 0 |
| tracks crossing | 0 | 0 | 0 |

The three unchanged dangling markers are the intentional open replacement
endpoints for `FRONT_RGB_R_N`, `FRONT_RGB_G_N`, and `FRONT_RGB_B_N`.

Direct measurement from every retained BAT_MAIN-class via annulus to the
refilled In1.Cu and In4.Cu GND polygon boundary found a minimum of
**0.300499 mm**. All 12 retained `BAT_PROTECTED_P` vias meet the same minimum.

## Preservation gate

- Retained track/via geometry: no removals or net changes.
- `XGPIO4` and `XGPIO5`: unchanged.
- RGB replacement copper: unchanged and still unrouted at U3.
- `ACC_5V_BOOST_EN`: unchanged and independent.
- Demo schematic and DRU: unchanged.
- `hardware/beta-v2/`: unchanged; the authoritative PCB SHA-256 remains
  `a4b93b9bc71da5e491022d65a8393fee7b11232b6b976d3d0702efd6eae1f782`.

The Demo is safe to hand to autonomous completion for the next independently
gated routing increment. It is not yet routing-complete because the three RGB
replacement nets intentionally remain open.
