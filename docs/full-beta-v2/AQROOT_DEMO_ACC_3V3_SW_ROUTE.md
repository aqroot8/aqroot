# AQROOT Demo ACC_3V3_SW route promotion

**Result: PASS.** The authoritative Demo PCB now connects the complete switched
3.3 V accessory-output tree. This promotion recovers and validates the
unfinished dirty-worktree candidate present after `612b29a`.

## Promoted route

All 15 fitted endpoints are one KiCad-connected copper island:

- `U20.5`, `C37.1`, `C39.1`, `C63.1`, `R46.1`, `R49.1`, `R50.1`, and `R63.1`
- `U16.8`, `Q10.1`, `TP12.1`, and `TP25.1`
- Community Port `J5.3` and `J5.22`, plus Qwiic `J8.2`

Relative to `612b29a`, the PCB change is add-only: 68 track segments, eleven
0.90/0.40 mm through-vias, and 239.570 mm of copper, all on `/ACC_3V3_SW`.
There are 34 B.Cu, 17 In2.Cu, 13 F.Cu, and four In3.Cu segments. The route uses
the bounded package-local fine-pitch escapes at `U20.5` and `U16.8`; the rest
meets the 0.40 mm switched-rail floor. No footprint or accepted track/via was
removed, moved, or reassigned.

The DRU change extends the existing courtyard-scoped fine-pitch power-package
neck rule to `U20` and `U16`. It does not change the 0.35 mm `ACC_3V3` rail
minimum, D-269 clearance, any netclass, or any global manufacturing floor.

## Authoritative KiCad gate

KiCad CLI 10.0.5 refilled and saved the board, then ran all severities with
schematic parity:

```text
kicad-cli pcb drc --refill-zones --save-board --format json --units mm \
  --severity-all --schematic-parity -o /tmp/aqroot-demo-acc-3v3-final.json \
  hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb
```

The final signature is the accepted board signature: 199 footprint-library
lookup warnings, five inherited hole-clearance reports, one inherited
solder-mask bridge, 499 unconnected items, and 265 known schematic-parity
metadata reports. There are zero clearance, shorting, crossing, track-width,
via, annular-ring, drill, or dangling-copper violations.

The routing ledger reports `/ACC_3V3_SW` at zero open edges. Its 14 retained
open edges are closed without regressing any other retained net. The board
still proves `ACC_3V3_EN`, `ACC_POWER_FAULT_N`, `ACC_5V_SW_EN`,
`ACC_5V_BOOST_EN`, `ACC_5V_SW`, both retained XGPIOs, and all three RGB
replacement nets connected.

## Preservation and next blocker

`hardware/beta-v2/` is untouched. The refilled authoritative Demo PCB SHA-256
is `fd346ae6e6c1c7b1b21ab5704fd5a262ea44f4a321dcf3959cd7d845a129c4ce`.

This closes the highest-leverage switched-accessory 3.3 V rail blocker, but the
whole board is not routing-complete: the updated ledger still has 547 retained
open edges across 104 retained nets. The next bounded fabrication blocker is
the highest-impact coherent retained-net routing cluster from that ledger;
manufacturing export remains premature until retained routing and parity are
closed.
