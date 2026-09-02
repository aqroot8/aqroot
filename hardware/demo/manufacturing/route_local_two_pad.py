#!/usr/bin/env python3
"""Route an allowlisted local two-pad Demo net with a real KiCad scratch gate."""

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BOARD = ROOT / "hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb"
sys.path.insert(0, str(ROOT / "hardware/beta-v2/checks"))
import incremental_router as ir  # noqa: E402
import qrouter as qr  # noqa: E402

ROUTES = {
    "DIO2_TXEN": {
        "net": "/04_SPI_B_RADIOS_NFC/DIO2_TXEN",
        "pads": ("U8.7", "U8.8"),
        "layer": "B",
        "width": 200_000,
        "clearance": 200_000,
    },
    "MAX17048_ALRT_N": {
        "net": "/01_POWER_TREE/MAX17048_ALRT_N",
        "pads": ("TP11.1", "U14.5"),
        "layer": "B",
        "width": 200_000,
        "clearance": 200_000,
    },
    "ILIM_VSET": {
        "net": "/01_POWER_TREE/ILIM_VSET",
        "pads": ("R36.1", "U11.7"),
        "layer": "B",
        "width": 200_000,
        "clearance": 200_000,
    },
    "ISET": {
        "net": "/01_POWER_TREE/ISET",
        "pads": ("R37.1", "U11.8"),
        "layer": "B",
        "width": 200_000,
        "clearance": 200_000,
    },
    "USB_CC1": {
        "net": "Net-(J3-CC1)",
        "pads": ("J3.A5", "R31.1"),
        "layer": "F",
        "width": 200_000,
        "clearance": 200_000,
    },
    "USB_CC2": {
        "net": "Net-(J3-CC2)",
        "pads": ("J3.B5", "R30.1"),
        "layer": "F",
        "width": 200_000,
        "clearance": 200_000,
    },
    "DISP_SDO": {
        "net": "/03_SPI_A_DISPLAY_SD/DISP_SDO",
        "pads": ("J1.33", "TP36.1"),
        "ignored_dnp_pads": ("R112.1",),
        "layer": "F",
        "width": 200_000,
        "clearance": 200_000,
    },
    "USB_D_ESD_N": {
        "net": "/01_POWER_TREE/USB_D_ESD_N",
        "pads": ("R33.1", "U10.6"),
        "layer": "F",
        "width": 230_000,
        "clearance": 200_000,
    },
    "USB_D_ESD_P": {
        "net": "/01_POWER_TREE/USB_D_ESD_P",
        "pads": ("R34.1", "U10.4"),
        "layer": "F",
        "width": 230_000,
        "clearance": 200_000,
    },
    "USB_D_MCU_N": {
        "net": "/USB_D_MCU_N",
        "pads": ("R33.2", "U1.13"),
        "layer": "F",
        "width": 230_000,
        "clearance": 200_000,
    },
    "USB_D_MCU_P": {
        "net": "/USB_D_MCU_P",
        "pads": ("R34.2", "U1.14"),
        "layer": "F",
        "width": 230_000,
        "clearance": 200_000,
    },
    "NFC_MATCH_A": {
        "net": "/04_SPI_B_RADIOS_NFC/NFC_MATCH_A",
        "pads": ("C71.2", "R114.1"),
        "layer": "B",
        "width": 300_000,
        "clearance": 200_000,
    },
    "NFC_MATCH_B": {
        "net": "/04_SPI_B_RADIOS_NFC/NFC_MATCH_B",
        "pads": ("C72.2", "R115.1"),
        "layer": "B",
        "width": 300_000,
        "clearance": 200_000,
    },
    "NFC_RFO1": {
        "net": "/04_SPI_B_RADIOS_NFC/NFC_RFO1",
        "pads": ("U9.13", "L5.1"),
        "layer": "B",
        "width": 300_000,
        # U9 is a 0.50 mm-pitch UFQFPN.  The board rules intentionally apply
        # the 0.25 mm routed-clearance floor only when neither item is a pad;
        # use the ordinary 0.20 mm package-land clearance until the trace has
        # cleared the package, then retain 0.25 mm against routed copper.
        "pad_clearance": 200_000,
        "clearance": 250_000,
    },
    "NFC_RFO2": {
        "net": "/04_SPI_B_RADIOS_NFC/NFC_RFO2",
        "pads": ("U9.15", "L6.1"),
        "layer": "B",
        "width": 300_000,
        "pad_clearance": 200_000,
        "clearance": 250_000,
    },
    "NFC_RFI1": {
        "net": "/04_SPI_B_RADIOS_NFC/NFC_RFI1",
        "pads": ("U9.22", "R116.2"),
        "layer": "B",
        "width": 300_000,
        "pad_clearance": 200_000,
        "clearance": 250_000,
        "floor_override": {"U9.22": 200_000},
    },
    "NFC_RFI2": {
        "net": "/04_SPI_B_RADIOS_NFC/NFC_RFI2",
        "pads": ("U9.23", "R117.2"),
        "layer": "B",
        "width": 300_000,
        "pad_clearance": 200_000,
        "clearance": 250_000,
        "floor_override": {"U9.23": 200_000},
    },
    "NFC_RXA_UPPER": {
        "net": "/04_SPI_B_RADIOS_NFC/NFC_RXA",
        "pads": ("C75.2", "C76.1"),
        "ignored_connected_pads": ("R116.1",),
        "layer": "B",
        "width": 300_000,
        "clearance": 250_000,
    },
    "NFC_RXA_LOWER": {
        "net": "/04_SPI_B_RADIOS_NFC/NFC_RXA",
        "pads": ("C76.1", "R116.1"),
        "ignored_connected_pads": ("C75.2",),
        "layer": "B",
        "width": 300_000,
        "clearance": 250_000,
    },
    "NFC_RXB_LOWER": {
        "net": "/04_SPI_B_RADIOS_NFC/NFC_RXB",
        "pads": ("C77.2", "C78.1"),
        "ignored_connected_pads": ("R117.1",),
        "layer": "B",
        "width": 300_000,
        "clearance": 250_000,
    },
    "NFC_RXB_UPPER": {
        "net": "/04_SPI_B_RADIOS_NFC/NFC_RXB",
        "pads": ("C78.1", "R117.1"),
        "ignored_connected_pads": ("C77.2",),
        "layer": "B",
        "width": 300_000,
        "clearance": 250_000,
    },
    "NFC_XIN_CRYSTAL": {
        "net": "/04_SPI_B_RADIOS_NFC/NFC_XIN",
        "pads": ("U9.5", "Y1.3"),
        "ignored_connected_pads": ("C80.1",),
        "layer": "B",
        "width": 200_000,
        "clearance": 200_000,
    },
    "NFC_XIN_CAP": {
        "net": "/04_SPI_B_RADIOS_NFC/NFC_XIN",
        "pads": ("Y1.3", "C80.1"),
        "ignored_connected_pads": ("U9.5",),
        "layer": "B",
        "width": 200_000,
        "clearance": 200_000,
    },
    "NFC_XOUT_CRYSTAL": {
        "net": "/04_SPI_B_RADIOS_NFC/NFC_XOUT",
        "pads": ("U9.4", "Y1.1"),
        "ignored_connected_pads": ("C79.1",),
        "layer": "B",
        "width": 200_000,
        "clearance": 200_000,
    },
    "NFC_XOUT_CAP": {
        "net": "/04_SPI_B_RADIOS_NFC/NFC_XOUT",
        "pads": ("Y1.1", "C79.1"),
        "ignored_connected_pads": ("U9.4",),
        "layer": "B",
        "width": 200_000,
        "clearance": 200_000,
    },
    "NFC_EMCA_L": {
        "net": "/04_SPI_B_RADIOS_NFC/NFC_EMCA",
        "pads": ("L5.2", "C71.1"),
        "ignored_connected_pads": ("C69.1", "C73.1"),
        "layer": "B", "width": 300_000, "clearance": 250_000,
    },
    "NFC_EMCA_SHUNT": {
        "net": "/04_SPI_B_RADIOS_NFC/NFC_EMCA",
        "pads": ("C71.1", "C73.1"),
        "ignored_connected_pads": ("C69.1", "L5.2"),
        "layer": "B", "width": 300_000, "clearance": 250_000,
    },
    "NFC_EMCA_CAP": {
        "net": "/04_SPI_B_RADIOS_NFC/NFC_EMCA",
        "pads": ("C73.1", "C69.1"),
        "ignored_connected_pads": ("C71.1", "L5.2"),
        "layer": "B", "width": 300_000, "clearance": 250_000,
    },
    "NFC_EMCB_L": {
        "net": "/04_SPI_B_RADIOS_NFC/NFC_EMCB",
        "pads": ("L6.2", "C72.1"),
        "ignored_connected_pads": ("C70.1", "C74.1"),
        "layer": "B", "width": 300_000, "clearance": 250_000,
    },
    "NFC_EMCB_SHUNT": {
        "net": "/04_SPI_B_RADIOS_NFC/NFC_EMCB",
        "pads": ("C72.1", "C74.1"),
        "ignored_connected_pads": ("C70.1", "L6.2"),
        "layer": "B", "width": 300_000, "clearance": 250_000,
    },
    "NFC_EMCB_CAP": {
        "net": "/04_SPI_B_RADIOS_NFC/NFC_EMCB",
        "pads": ("C74.1", "C70.1"),
        "ignored_connected_pads": ("C72.1", "L6.2"),
        "layer": "B", "width": 300_000, "clearance": 250_000,
    },
    "NFC_ANTA_MATCH": {
        "net": "/04_SPI_B_RADIOS_NFC/NFC_ANT_A",
        "pads": ("R114.2", "C75.1"),
        "ignored_connected_pads": ("J7.1", "TP37.1"),
        "layer": "B", "width": 300_000, "clearance": 250_000,
    },
    "NFC_ANTA_CONN": {
        "net": "/04_SPI_B_RADIOS_NFC/NFC_ANT_A",
        "pads": ("C75.1", "J7.1"),
        "ignored_connected_pads": ("R114.2", "TP37.1"),
        "layer": "B", "width": 300_000, "clearance": 250_000,
    },
    "NFC_ANTA_TP": {
        "net": "/04_SPI_B_RADIOS_NFC/NFC_ANT_A",
        "pads": ("R114.2", "TP37.1"),
        "ignored_connected_pads": ("C75.1", "J7.1"),
        "layer": "B", "width": 300_000, "clearance": 250_000,
    },
    "NFC_ANTB_MATCH": {
        "net": "/04_SPI_B_RADIOS_NFC/NFC_ANT_B",
        "pads": ("R115.2", "C77.1"),
        "ignored_connected_pads": ("J7.2", "TP38.1"),
        "layer": "B", "width": 300_000, "clearance": 250_000,
    },
    "NFC_ANTB_CONN": {
        "net": "/04_SPI_B_RADIOS_NFC/NFC_ANT_B",
        "pads": ("C77.1", "J7.2"),
        "ignored_connected_pads": ("R115.2", "TP38.1"),
        "layer": "B", "width": 300_000, "clearance": 250_000,
    },
    "NFC_ANTB_TP": {
        "net": "/04_SPI_B_RADIOS_NFC/NFC_ANT_B",
        "pads": ("R115.2", "TP38.1"),
        "ignored_connected_pads": ("C77.1", "J7.2"),
        "layer": "B", "width": 300_000, "clearance": 250_000,
    },
}


def route(path: Path, name: str):
    rule = ROUTES[name]
    board = qr.QBoard(path)
    ir.inject_existing_via_obstacles(board)
    pads = {p["ref"]: p for p in ir.physical_net_pads(board, rule["net"])}
    ignored = set(rule.get("ignored_dnp_pads", ())) | set(
        rule.get("ignored_connected_pads", ())
    )
    unexpected_ignored = ignored - set(pads)
    if unexpected_ignored:
        raise RuntimeError(f"missing declared DNP pads: {sorted(unexpected_ignored)}")
    pads = {ref: pad for ref, pad in pads.items() if ref not in ignored}
    if set(pads) != set(rule["pads"]):
        raise RuntimeError(f"unexpected fitted pads: {sorted(pads)}")
    a, b = (pads[ref] for ref in rule["pads"])
    if rule.get("floor_override"):
        result = qr.connect(
            board, rule["net"], a, b, rule["layer"], rule["width"],
            rule["width"], rule.get("pad_clearance", rule["clearance"]),
            rule["clearance"], G=25_000,
            floor_override=rule["floor_override"],
        )
    else:
        result = qr.connect_role(
            board, rule["net"], a, b, rule["layer"], rule["width"],
            rule.get("pad_clearance", rule["clearance"]), rule["clearance"],
            G=25_000,
        )
    board.save(path)
    print(json.dumps({"name": name, "rule": rule, "result": result}, sort_keys=True))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("name", choices=sorted(ROUTES))
    parser.add_argument("--route", type=Path, help=argparse.SUPPRESS)
    parser.add_argument("--candidate", type=Path)
    args = parser.parse_args()
    if args.route:
        route(args.route, args.name)
        return 0

    before = hashlib.sha256(BOARD.read_bytes()).hexdigest()
    with tempfile.TemporaryDirectory(prefix="aqroot-demo-local-") as temporary:
        scratch = Path(temporary) / BOARD.name
        for suffix in (".kicad_pcb", ".kicad_dru", ".kicad_pro"):
            scratch.with_suffix(suffix).write_bytes(BOARD.with_suffix(suffix).read_bytes())
        routed = json.loads(subprocess.run(
            [sys.executable, __file__, args.name, "--route", str(scratch)],
            check=True, text=True, capture_output=True,
        ).stdout)
        drc = Path(temporary) / "drc.json"
        completed = subprocess.run([
            "kicad-cli", "pcb", "drc", "--refill-zones", "--save-board",
            "--format", "json", "--units", "mm", "--severity-all",
            "--schematic-parity", "-o", str(drc), str(scratch),
        ], text=True, capture_output=True)
        violations = json.loads(drc.read_text()).get("violations", [])
        accepted = {"lib_footprint_issues", "hole_clearance", "solder_mask_bridge"}
        attributable = [v for v in violations if v.get("type") not in accepted]
        types = {}
        for violation in violations:
            kind = violation.get("type", "unknown")
            types[kind] = types.get(kind, 0) + 1
        candidate = scratch.read_bytes()
    promotion = routed["result"].get("ok", False) and not attributable
    if args.candidate and promotion:
        args.candidate.write_bytes(candidate)
    print(json.dumps({
        "schema": 1, "authoritative_board_sha256": before,
        "authoritative_unchanged": before == hashlib.sha256(BOARD.read_bytes()).hexdigest(),
        "route": routed, "drc_exit": completed.returncode, "drc_types": types,
        "attributable_drc": attributable, "promotion_candidate": promotion,
        "candidate_sha256": hashlib.sha256(candidate).hexdigest(),
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
