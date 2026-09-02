#!/usr/bin/env python3
"""Generate the authoritative fitted-pad routing ledger for AQROOT Demo."""

import argparse
import csv
import hashlib
import json
import re
import subprocess
import tempfile
from collections import defaultdict
from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[3]
PROJECT = ROOT / "hardware/demo/kicad/aqroot-demo"
BOARD = PROJECT / "aqroot-Beta-v2.kicad_pcb"
SCHEMATIC = PROJECT / "aqroot-Beta-v2.kicad_sch"
APPROVED_NC = {"J5.9", "J5.10", "J5.11", "J5.12", "J5.15", "J5.16", "J5.17", "J5.18"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def expand_refs(cell: str) -> set[str]:
    result = set()
    for token in cell.split(","):
        token = token.strip()
        match = re.fullmatch(r"([A-Z#]+)(\d+)-([A-Z#]*)(\d+)", token)
        if match and (not match.group(3) or match.group(1) == match.group(3)):
            result.update(
                f"{match.group(1)}{number}"
                for number in range(int(match.group(2)), int(match.group(4)) + 1)
            )
        elif token:
            result.add(token)
    return result


def schematic_population() -> tuple[set[str], set[str]]:
    with tempfile.TemporaryDirectory(prefix="aqroot-demo-ledger-") as temporary:
        bom = Path(temporary) / "bom.csv"
        subprocess.run(
            [
                "kicad-cli", "sch", "export", "bom",
                "--fields", "Reference,DNP", "--labels", "Refs,DNP",
                "--group-by", "DNP", "-o", str(bom), str(SCHEMATIC),
            ],
            check=True,
            stdout=subprocess.DEVNULL,
        )
        rows = list(csv.DictReader(bom.open(newline="", encoding="utf-8-sig")))
    fitted = set().union(*(expand_refs(row["Refs"]) for row in rows if not row["DNP"].strip()))
    dnp = set().union(*(expand_refs(row["Refs"]) for row in rows if row["DNP"].strip()))
    return fitted, dnp


def pad_id(pad) -> tuple[str, str, int, int]:
    position = pad.GetPosition()
    return (
        pad.GetParentFootprint().GetReference(),
        pad.GetNumber(),
        position.x,
        position.y,
    )


def pad_label(pad) -> str:
    ref, number, x, y = pad_id(pad)
    return f"{ref}.{number}@{x / 1e6:.3f},{y / 1e6:.3f}"


def copper_groups(connectivity, pads) -> list[list[str]]:
    identities = {pad_id(pad): pad for pad in pads}
    parent = {identity: identity for identity in identities}

    def find(identity):
        while parent[identity] != identity:
            parent[identity] = parent[parent[identity]]
            identity = parent[identity]
        return identity

    def union(left, right):
        left_root, right_root = find(left), find(right)
        if left_root != right_root:
            parent[left_root] = right_root

    for pad in pads:
        this = pad_id(pad)
        for item in connectivity.GetConnectedItems(pad):
            if item.GetClass() == "PAD" and pad_id(item) in identities:
                union(this, pad_id(item))

    groups = defaultdict(list)
    for identity, pad in identities.items():
        groups[find(identity)].append(pad_label(pad))
    return sorted((sorted(group) for group in groups.values()), key=lambda group: (group[0], len(group)))


def sheet(net: str) -> str:
    match = re.match(r"/(\d\d_[^/]+)/", net)
    return match.group(1) if match else ("GLOBAL" if net else "NO_NET")


def generate() -> dict:
    fitted, dnp = schematic_population()
    board = pcbnew.LoadBoard(str(BOARD.resolve()))
    board.BuildConnectivity()
    connectivity = board.GetConnectivity()

    board_refs = {footprint.GetReference() for footprint in board.GetFootprints()}
    pads_by_net = defaultdict(list)
    nc_observed = set()
    for footprint in board.GetFootprints():
        ref = footprint.GetReference()
        for pad in footprint.Pads():
            contact = f"{ref}.{pad.GetNumber()}"
            if contact in APPROVED_NC:
                nc_observed.add(contact)
                continue
            if ref in fitted and pad.GetNetCode() > 0:
                pads_by_net[pad.GetNetname()].append(pad)

    nets = []
    for net, pads in pads_by_net.items():
        if len(pads) < 2:
            continue
        groups = copper_groups(connectivity, pads)
        xs = [pad.GetPosition().x / 1e6 for pad in pads]
        ys = [pad.GetPosition().y / 1e6 for pad in pads]
        nets.append({
            "net": net,
            "sheet": sheet(net),
            "pads": len(pads),
            "copper_islands": len(groups),
            "open_edges": len(groups) - 1,
            "span_mm": round(((max(xs) - min(xs)) ** 2 + (max(ys) - min(ys)) ** 2) ** 0.5, 3),
            "groups": groups,
        })
    nets.sort(key=lambda row: (-row["open_edges"], row["net"]))

    sheet_summary = []
    for name in sorted({row["sheet"] for row in nets}):
        rows = [row for row in nets if row["sheet"] == name]
        sheet_summary.append({
            "sheet": name,
            "nets": len(rows),
            "open_nets": sum(row["open_edges"] > 0 for row in rows),
            "open_edges": sum(row["open_edges"] for row in rows),
        })

    open_nets = [row for row in nets if row["open_edges"]]
    return {
        "schema": 1,
        "board": str(BOARD.relative_to(ROOT)),
        "board_sha256": sha256(BOARD),
        "population": {
            "schematic_fitted_references": len(fitted),
            "schematic_dnp_references": sorted(dnp),
            "fitted_references_missing_from_board": sorted(fitted - board_refs),
            "board_references_not_in_schematic_population": sorted(board_refs - fitted - dnp),
        },
        "approved_demo_nc": {
            "expected": sorted(APPROVED_NC),
            "observed": sorted(nc_observed),
            "missing": sorted(APPROVED_NC - nc_observed),
            "unexpected": sorted(nc_observed - APPROVED_NC),
        },
        "connectivity": {
            "raw_board_ratsnest": connectivity.GetUnconnectedCount(True),
            "retained_multi_pad_nets": len(nets),
            "connected_retained_nets": len(nets) - len(open_nets),
            "open_retained_nets": len(open_nets),
            "retained_open_edges": sum(row["open_edges"] for row in open_nets),
        },
        "sheet_summary": sheet_summary,
        "nets": nets,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", nargs="?", type=Path)
    args = parser.parse_args()
    if args.output:
        output = args.output.resolve()
        if output == BOARD.resolve() or output.suffix == ".kicad_pcb":
            parser.error("output must be a JSON report path, not a KiCad PCB")
    report = generate()
    encoded = json.dumps(report, indent=2) + "\n"
    if args.output:
        args.output.write_text(encoded, encoding="utf-8")
    print(encoded, end="")
    nc = report["approved_demo_nc"]
    return 0 if not nc["missing"] and not nc["unexpected"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
