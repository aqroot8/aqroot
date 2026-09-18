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

# ---------------------------------------------------------------------------
# APPROVED UNROUTED CONTACTS -- D-742, owner decision 2026-09-17.
#
# THIS IS NOT `APPROVED_NC` AND IT MUST NEVER BE FOLDED INTO IT.  A contact in
# `APPROVED_NC` carries NO NET: J5's eight Community-Port positions are NC by
# Demo scope, in the schematic, and the ledger simply does not count them.  A
# contact HERE carries a real net, is a real pad of a fitted part, and is
# genuinely UNROUTED on the board; the owner has ruled that it SHIPS that way.
#
# So the pad is NOT removed from its net and the net's `open_edges` is NOT
# reduced.  `nets[]` keeps telling the copper truth -- which is what
# `neck_contract` and every corridor screen read -- and the GOVERNANCE verdict
# is published beside it as a separate classification:
#
#     retained_open_edges        physical, unchanged
#     approved_unrouted_edges    edges an owner decision covers
#     unapproved_open_edges      the release criterion; must be 0
#
# Hiding the edge instead would have made `neck_contract` N2 VACUOUS -- its
# only compared pad on this board IS `U11.3` -- and would have deleted the
# board's own record of why the pin is bare.
APPROVED_UNROUTED = {
    "U11.3": {
        "net": "/BQ25185_STAT2",
        "decision": "D-742 (owner, 2026-09-17); measured by D-734 and D-741",
        "reason": (
            "DLH0010A package wall.  U11.2's BAT escape sits on its own land "
            "centreline y=78.200 (0.200 mm pad clearance to U11.1's SYS land at "
            "y>=78.500 pins it there); D-269 puts STAT2's top edge at <=77.800 "
            "and U11.4's GND land bottom edge at >=77.700.  The window is "
            "0.100 mm against the board's 0.200 mm published floor, it does not "
            "move with U11 or with any rotation (BAT is pin 2 and STAT2 pin 3 "
            "in every DLH0010A), and a via-in-pad escape needs 0.450 mm across "
            "a 0.750 x 0.200 mm land."
        ),
        "retained_for_rework": ["R128", "TP7"],
        "functional_impact": (
            "Charger STATUS OBSERVABILITY only.  BQ25185 protection behaviour is "
            "unchanged; STAT1 is routed, and the MAX17048 fuel gauge reports pack "
            "voltage and state-of-charge.  Full STAT1+STAT2 charge-state decode is "
            "UNAVAILABLE on this Demo revision and firmware must not report a "
            "charger fault as directly observed."
        ),
    },
}


def _contact(label: str) -> str:
    """`U11.3@66.400,77.800` -> `U11.3`."""
    return label.split("@", 1)[0]


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


def generate(board_path: Path = BOARD) -> dict:
    fitted, dnp = schematic_population()
    board = pcbnew.LoadBoard(str(board_path.resolve()))
    board.BuildConnectivity()
    connectivity = board.GetConnectivity()

    board_refs = {footprint.GetReference() for footprint in board.GetFootprints()}
    pads_by_net = defaultdict(list)
    nc_observed = set()
    # An APPROVED_UNROUTED contact is NOT skipped -- it stays on its net so the
    # copper truth in `nets[]` is unchanged.  What is collected here is only the
    # evidence needed to prove the DECLARATION is not stale: the pad must exist,
    # its part must be fitted, and it must still carry the net the decision names.
    unrouted_seen = {}
    for footprint in board.GetFootprints():
        ref = footprint.GetReference()
        for pad in footprint.Pads():
            contact = f"{ref}.{pad.GetNumber()}"
            if contact in APPROVED_NC:
                nc_observed.add(contact)
                continue
            if contact in APPROVED_UNROUTED:
                unrouted_seen[contact] = {
                    "fitted": ref in fitted,
                    "board_net": pad.GetNetname() if pad.GetNetCode() > 0 else None,
                }
            if ref in fitted and pad.GetNetCode() > 0:
                pads_by_net[pad.GetNetname()].append(pad)

    nets = []
    for net, pads in pads_by_net.items():
        if len(pads) < 2:
            continue
        groups = copper_groups(connectivity, pads)
        xs = [pad.GetPosition().x / 1e6 for pad in pads]
        ys = [pad.GetPosition().y / 1e6 for pad in pads]
        # An open edge is APPROVED only when the island it strands is nothing
        # BUT declared contacts.  An island that also carries an undeclared pad
        # is an ordinary open edge and is counted against the release.
        approved_islands = [
            group for group in groups
            if group and all(_contact(label) in APPROVED_UNROUTED for label in group)
        ]
        open_edges = len(groups) - 1
        approved_edges = min(len(approved_islands), open_edges)
        nets.append({
            "net": net,
            "sheet": sheet(net),
            "pads": len(pads),
            "copper_islands": len(groups),
            "open_edges": open_edges,
            "approved_unrouted_edges": approved_edges,
            "unapproved_open_edges": open_edges - approved_edges,
            "approved_unrouted_contacts": sorted(
                _contact(label) for group in approved_islands for label in group),
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
            "unapproved_open_edges": sum(row["unapproved_open_edges"] for row in rows),
        })

    open_nets = [row for row in nets if row["open_edges"]]
    unapproved_nets = [row for row in nets if row["unapproved_open_edges"]]
    # A declaration is only honoured when the board still agrees with it: the
    # pad exists, its part is fitted, it carries the net the decision names, and
    # it is genuinely stranded.  Anything else is a STALE declaration and is
    # reported so it cannot quietly excuse an edge it no longer describes.
    unrouted_stranded = {
        contact
        for row in nets
        for contact in row["approved_unrouted_contacts"]
    }
    unrouted_report = {}
    for contact, spec in sorted(APPROVED_UNROUTED.items()):
        seen = unrouted_seen.get(contact)
        unrouted_report[contact] = {
            "declared_net": spec["net"],
            "decision": spec["decision"],
            "reason": spec["reason"],
            "retained_for_rework": spec["retained_for_rework"],
            "functional_impact": spec["functional_impact"],
            "pad_on_board": seen is not None,
            "part_fitted": bool(seen and seen["fitted"]),
            "board_net": seen["board_net"] if seen else None,
            "net_matches_decision": bool(seen and seen["board_net"] == spec["net"]),
            "stranded_on_board": contact in unrouted_stranded,
        }
    unrouted_stale = sorted(
        contact for contact, row in unrouted_report.items()
        if not (row["pad_on_board"] and row["part_fitted"]
                and row["net_matches_decision"] and row["stranded_on_board"]))
    # The rework path the owner decision requires must actually be on the board.
    unrouted_rework_missing = sorted(
        f"{contact}:{ref}"
        for contact, spec in APPROVED_UNROUTED.items()
        for ref in spec["retained_for_rework"]
        if ref not in board_refs or ref not in fitted)
    return {
        "schema": 1,
        "board": str(board_path),
        "board_sha256": sha256(board_path),
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
        "approved_unrouted": {
            "expected": sorted(APPROVED_UNROUTED),
            "contacts": unrouted_report,
            "stale": unrouted_stale,
            "rework_parts_missing": unrouted_rework_missing,
        },
        "connectivity": {
            "raw_board_ratsnest": connectivity.GetUnconnectedCount(True),
            "retained_multi_pad_nets": len(nets),
            "connected_retained_nets": len(nets) - len(open_nets),
            "open_retained_nets": len(open_nets),
            "retained_open_edges": sum(row["open_edges"] for row in open_nets),
            "approved_unrouted_edges": sum(row["approved_unrouted_edges"] for row in nets),
            "unapproved_open_retained_nets": len(unapproved_nets),
            "unapproved_open_edges": sum(row["unapproved_open_edges"] for row in nets),
        },
        "sheet_summary": sheet_summary,
        "nets": nets,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", nargs="?", type=Path)
    parser.add_argument("--board", type=Path, default=BOARD)
    args = parser.parse_args()
    if args.output:
        output = args.output.resolve()
        if output == BOARD.resolve() or output.suffix == ".kicad_pcb":
            parser.error("output must be a JSON report path, not a KiCad PCB")
    report = generate(args.board)
    encoded = json.dumps(report, indent=2) + "\n"
    if args.output:
        args.output.write_text(encoded, encoding="utf-8")
    print(encoded, end="")
    nc = report["approved_demo_nc"]
    un = report["approved_unrouted"]
    ok = (not nc["missing"] and not nc["unexpected"]
          and not un["stale"] and not un["rework_parts_missing"])
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
