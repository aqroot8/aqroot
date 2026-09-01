# AQROOT Demo clean synchronized PCB baseline

**Result: PASS.** The Demo PCB under
`hardware/demo/kicad/aqroot-demo/` is synchronized to the approved Demo
schematic topology without routing the four replacement nets. The Full Beta v2
production design under `hardware/beta-v2/` was not changed.

## Promoted baseline

- Footprints: **324 -> 311**.
- Track segments: **925 -> 824**.
- Vias: **87 -> 80**.
- Removed exactly: `U23`, `C83`, `R130`, `TP41`, `R51`-`R54`,
  `R57`-`R60`, and `D3`.
- Removed copper only from `/XGPIO0`-`/XGPIO3`, `/XGPIO8`, `/XGPIO9`,
  and `/08_BUTTONS_EXPANDERS/RESERVED_SPARE`. `/XGPIO6`, `/XGPIO7`, and
  the retired connector-side header nets had no routed copper to remove.
- Retained `/XGPIO4` and `/XGPIO5` unchanged at 9 and 6 copper objects,
  respectively.

A geometric before/after comparison found **zero added track/via geometries**,
**108 removed copper objects**, and no net rename among surviving copper. The
108 removals are exactly the 101 track segments and seven vias on the retired
nets above. Therefore every surviving copper geometry is preserved from the
pre-ECO board, including retained J5, power, USB, RF, NFC, display, audio, IR,
battery, and safety routing.

## Schematic synchronization

`U3` is assigned as approved:

| U3 pad | function |
|---:|---|
| 4 / P00 | `FRONT_RGB_R_N` |
| 5 / P01 | `FRONT_RGB_G_N` |
| 6 / P02 | `FRONT_RGB_B_N` |
| 7 / P03 | `ACC_5V_SW_EN` |
| 8 / P04 | `/XGPIO4` retained |
| 9 / P05 | `/XGPIO5` retained |

Unused U3 P06, P07, P10, and P11 have their schematic-generated unconnected
nets. J5 contacts 9-12 and 15-18 likewise have schematic-generated unconnected
nets. All other J5 assignments are retained, including J5.13/J5.14 XGPIO4/5,
J5.20 wake, and J5.21 Accessory Detect.

## Intentionally unrouted replacement nets

No replacement routing was added:

- `ACC_5V_SW_EN`: U3.7 to the existing U22.1 / TP47.1 / R131.1 endpoints;
  zero tracks and zero vias.
- `FRONT_RGB_R_N`: U3.4 to the retained R124-side copper; open at U3.
- `FRONT_RGB_G_N`: U3.5 to the retained R125-side copper; open at U3.
- `FRONT_RGB_B_N`: U3.6 to the retained R126-side copper; open at U3.

The three retained RGB branches produce the expected three `track_dangling`
DRC markers. `ACC_5V_SW_EN` has no track yet, so it does not produce a dangling
track marker. These four open replacement connections are intentional and are
not baseline failures.

## KiCad 10 DRC and attributable delta

KiCad CLI 10.0.5 was run with all severities and schematic parity against the
promoted board:

```text
kicad-cli pcb drc --format json --severity-all --schematic-parity \
  -o /tmp/aqroot-demo-final-drc.json \
  hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb
```

| DRC class | pre-ECO | synchronized | attribution |
|---|---:|---:|---|
| footprint-library lookup | 199 | 199 | pre-existing environment/library-table warnings |
| hole clearance | 5 | 5 | pre-existing; no delta |
| solder-mask bridge | 1 | 1 | pre-existing; no delta |
| track dangling | 0 | 3 | expected open RGB replacement endpoints |
| clearance | 0 | 0 | no new violation |
| shorting items | 0 | 0 | no new violation |
| tracks crossing | 0 | 0 | no new violation |

The synchronization therefore has **zero newly attributable electrical or
geometric DRC violation** after separating the three expected unrouted RGB
markers. Schematic-parity net conflicts improved from 20 to zero, and the 13
retired footprints are no longer reported as extras.

For rejection evidence, the discarded replacement-routing candidate had 851
tracks and 90 vias and introduced 23 shorting, 39 clearance, four
track-crossing, and 21 additional hole-clearance violations. None of that
copper is present in this promoted baseline.

## Gate result

**PASS.** Retired parts/copper are absent, XGPIO4/XGPIO5 and all surviving
copper are preserved, J5 NC contacts and U3 assignments match the approved
schematic, and the only new DRC markers are expected open RGB endpoints. The
next PCB task should route **`ACC_5V_SW_EN` alone** and gate that route before
attempting any RGB replacement route.
