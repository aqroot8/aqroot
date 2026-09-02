# AQROOT Demo compliant refilled PCB baseline

**Result: PASS.** The authoritative Demo PCB at
`hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb` was refilled with
KiCad CLI 10.0.5. The correction is limited to D-269's treatment of retained
`BAT_MAIN`-class vias; no retained track, via, pad, footprint, or net assignment
changed.

## Refill defect and correction

The pre-correction refill was measured directly against the filled polygons of
the In1.Cu and In4.Cu GND zones. Eighteen of 22 retained `BAT_MAIN`-class vias
already had 0.300498--0.300500 mm clearance. Four `BAT_RAW` vias inside the
named low-current divider-tap rule areas refilled at only
0.250499--0.250500 mm:

| net | via coordinate (mm) | before, minimum to GND | after, minimum to GND |
|---|---:|---:|---:|
| `/01_POWER_TREE/BAT_RAW` | (10.500, 63.500) | 0.250499 mm | 0.300500 mm |
| `/01_POWER_TREE/BAT_RAW` | (4.450, 48.250) | 0.250499 mm | 0.300500 mm |
| `/01_POWER_TREE/BAT_RAW` | (10.950, 18.000) | 0.250500 mm | 0.300500 mm |
| `/01_POWER_TREE/BAT_RAW` | (6.400, 70.400) | 0.250500 mm | 0.300500 mm |

D-269's named divider-tap exception is intended to cover only enclosed
low-current track segments. Its condition also excluded vias, allowing those
four antipads to fall back to the GND zones' 0.250 mm clearance. The rule now
keeps the existing track-segment exceptions but explicitly makes every
`BAT_MAIN`-class via subject to the full 0.300 mm D-269 clearance. No global
netclass, board clearance, zone clearance, or safety minimum was reduced.

After a real refill, all 22 retained `BAT_MAIN`-class vias measure
0.300498--0.300500 mm to GND copper on both internal reference planes. This
includes all 12 retained `BAT_PROTECTED_P` vias, whose minimum is 0.300498 mm.

## DRC and preservation evidence

Commands used for the final gate:

```text
kicad-cli pcb drc --refill-zones --save-board --format json --units mm \
  --severity-all --schematic-parity -o /tmp/aqroot-demo-refill-final.json \
  hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb
kicad-cli pcb drc --format report --units mm --severity-all \
  --schematic-parity -o /tmp/aqroot-demo-refill-final.rpt \
  hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb
```

| DRC class | before | after | attribution |
|---|---:|---:|---|
| footprint-library lookup | 199 | 199 | pre-existing environment/library warnings |
| hole clearance | 5 | 5 | pre-existing vendor/mechanical geometry; unchanged |
| solder-mask bridge | 1 | 1 | pre-existing MK1 geometry; unchanged |
| track dangling | 3 | 3 | intentional unrouted RGB replacement endpoints |
| clearance | 0 | 0 | no refill-attributable violation |
| shorting items | 0 | 0 | no refill-attributable violation |
| tracks crossing | 0 | 0 | no refill-attributable violation |

The before/after board comparison found 824 track segments, 80 vias, 1,032
pads, and 41 zones in both boards. Every track/via geometry and net, and every
pad position and net, is identical. Therefore retained connectivity and the
approved Demo schematic topology are unchanged. `XGPIO4` remains seven tracks
and two vias; `XGPIO5` remains four tracks and two vias. `ACC_5V_SW_EN` and all
three `FRONT_RGB_*_N` replacement nets remain at zero tracks and zero vias.

The hash manifest for every file below `hardware/beta-v2/` is unchanged.

## Promotion gate

The refilled Demo baseline passes D-269 without moving retained copper or
weakening a rule. It is safe to retry routing `ACC_5V_SW_EN` as the next
independently gated routing task. Do not route any RGB net in that task.
