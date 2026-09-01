# AQROOT Demo schematic ECO verification

**Result: PASS.** The schematic-only atomic ECO was applied under
`hardware/demo/kicad/aqroot-demo/`. The PCB and firmware were not updated.

## Implemented

- Removed `U23` (0x22), `C83`, `R130`, and `TP41`.
- Reassigned `U3.P00`–`P03` to `FRONT_RGB_R_N`, `FRONT_RGB_G_N`,
  `FRONT_RGB_B_N`, and `ACC_5V_SW_EN`, respectively.
- Retained only public `XGPIO4` and `XGPIO5` with `R55`, `R56`, `D4`, and
  `D5`; removed `R51`–`R54`, `R57`–`R60`, and `D3`.
- Marked `J5.9`–`J5.12` and `J5.15`–`J5.18` explicitly NC.
- Preserved `D13`, `R124`–`R126`, `R131`, `TP47`, U2/U3, both native GPIOs,
  external SDA/SCL, Accessory Detect on `J5.21`, and the complete switched
  3.3 V / 5 V accessory-power and fault architecture.

## KiCad 10 validation

Validation used KiCad CLI 10.0.5 against
`aqroot-Beta-v2.kicad_sch`:

```text
kicad-cli sch export netlist -o /tmp/aqroot-demo-eco/final.net aqroot-Beta-v2.kicad_sch
kicad-cli sch erc -o /tmp/aqroot-demo-eco/final-erc.rpt aqroot-Beta-v2.kicad_sch
ERC: 0 errors, 920 warnings
```

The warnings are existing project/library and pin-type warning classes; the
ECO introduces no ERC error. The fresh netlist verifies:

- `U23` and all 0x22 support are absent; `U2` and `U3` remain.
- `U3.4/P00` = RGB R, `U3.5/P01` = RGB G, `U3.6/P02` = RGB B, and
  `U3.7/P03` = `ACC_5V_SW_EN`.
- `/XGPIO4` is `U3.8` through `R55`; `/XGPIO5` is `U3.9` through `R56`.
- J5 contacts 9, 10, 11, 12, 15, 16, 17, and 18 export as unconnected;
  J5.21 remains `ACC_DETECT_N_HDR`.
- J5.7/J5.8 remain the two native GPIOs; J5.4/J5.5 remain SDA/SCL.
- `ACC_3V3_SW`, `ACC_5V_RAW`, and `ACC_5V_SW` retain their planned power
  endpoints.
- `ACC_5V_BOOST_EN` remains on `U3.P13` with `R102` and U21; independent
  `ACC_5V_SW_EN` remains on `U3.P03` with `R131`, `TP47`, and U22.

The Demo PCB file remains byte-identical at SHA-256
`a4b93b9bc71da5e491022d65a8393fee7b11232b6b976d3d0702efd6eae1f782`.
It is safe to proceed to the separate PCB-update stage, subject to that
stage's connectivity, DRC, routing, reset-safe, and D-186 sequencing gates.
