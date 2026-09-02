#!/usr/bin/env python3
"""Enumerate NFC analog-supply via pairs outside accepted crystal copper.

This is a scratch-only successor to D-422.  It does not emit copper.  The
package-side seed is the already-proven short westward U9.7 neck; candidate
through-via sites must be reachable on B.Cu, legal on every copper layer, and
outside the complete accepted XIN/XOUT copper envelope.  Each candidate is
then tested for an In3 corridor to a legal via site reachable from C47/C48.
"""

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BOARD = ROOT / "hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb"
sys.path.insert(0, str(ROOT / "hardware/beta-v2/checks"))
import incremental_router as ir  # noqa: E402
import qrouter as qr  # noqa: E402

NET = "/04_SPI_B_RADIOS_NFC/NFC_VDD_A"
CRYSTAL_NETS = {
    "/04_SPI_B_RADIOS_NFC/NFC_XIN",
    "/04_SPI_B_RADIOS_NFC/NFC_XOUT",
}
G = 25_000
WIDTH = 300_000
PACKAGE_NECK = 200_000
CLEARANCE = 200_000
VIA_DIA = 600_000
VIA_DRILL = 300_000
HOLE_CLEARANCE = 250_000


def mm(value):
    return round(value / 1e6, 3)


def oscillator_envelope(board):
    """Axis-aligned no-via envelope around all accepted oscillator copper."""
    items = [item for item in board.b.GetTracks()
             if item.GetNetname() in CRYSTAL_NETS]
    if not items:
        raise RuntimeError("accepted oscillator copper is missing")
    xs = [point for item in items for point in (item.GetStart().x, item.GetEnd().x)]
    ys = [point for item in items for point in (item.GetStart().y, item.GetEnd().y)]
    # Via copper must clear a 0.20 mm oscillator track by 0.20 mm.  Inflate by
    # via radius + routed clearance; the result conservatively includes the
    # complete accepted trace geometry rather than only the Y1 courtyard.
    inflate = VIA_DIA // 2 + CLEARANCE
    return min(xs) - inflate, min(ys) - inflate, max(xs) + inflate, max(ys) + inflate


def outside(site, envelope):
    x, y = site
    x0, y0, x1, y1 = envelope
    return x < x0 or x > x1 or y < y0 or y > y1


def legal_on_all_copper(board, site):
    """A through via must clear obstacles on every copper layer."""
    x, y = site
    return all(board.point_free(layer, NET, x, y, VIA_DIA,
                                CLEARANCE, CLEARANCE, G)
               for layer in board.cu)


def reachable_on_inner(board, start, targets):
    span = 12_000_000
    region = board.free_region("I3", NET, WIDTH, CLEARANCE, CLEARANCE, G,
                               start, start[0] - span, start[1] - span,
                               start[0] + span, start[1] + span)
    if region is None:
        return []
    mask, ox, oy, grid = region
    ny, nx = mask.shape
    reached = []
    for target in targets:
        i = int((target[0] - ox) // grid)
        j = int((target[1] - oy) // grid)
        if 0 <= i < nx and 0 <= j < ny and mask[j, i]:
            reached.append(target)
    return reached


def scan():
    board = qr.QBoard(BOARD)
    ir.inject_existing_via_obstacles(board)
    pads = {pad["ref"]: pad for pad in ir.physical_net_pads(board, NET)}
    envelope = oscillator_envelope(board)

    # D-422 proved this westward U9.7 package neck.  The seed is deliberately
    # outside the UFQFPN body but still close enough that this enumeration does
    # not silently substitute a different package-launch tactic.
    package_seed = {"x": 30_900_000, "y": pads["U9.7"]["y"], "w": 200_000,
                    "ln": pads["U9.7"]["x"] - 30_900_000}
    all_package_sites = board.via_sites(
        "B", "I3", board.nets[NET], package_seed, PACKAGE_NECK, VIA_DIA,
        CLEARANCE, CLEARANCE, G, span=8_000_000, via_drill=VIA_DRILL,
        hole_clr=HOLE_CLEARANCE, limit=128, separation=250_000)
    all_package_sites = [site for site in all_package_sites
                         if legal_on_all_copper(board, site)]
    package_sites = [site for site in all_package_sites if outside(site, envelope)]

    cap_sites = []
    cap_rows = []
    for ref in ("C47.1", "C48.1"):
        pad = pads[ref]
        escapes = board.escape(pad, "B", WIDTH, WIDTH, CLEARANCE, CLEARANCE,
                               G, board.ex0 - 2_000_000, board.ey0 - 2_000_000)
        sites = []
        for escape in (escapes or [])[:8]:
            sites.extend(board.via_sites(
                "B", "I3", board.nets[NET], escape, WIDTH, VIA_DIA,
                CLEARANCE, CLEARANCE, G, span=5_000_000,
                via_drill=VIA_DRILL, hole_clr=HOLE_CLEARANCE,
                limit=32, separation=250_000))
        sites = [site for site in set(sites) if legal_on_all_copper(board, site)]
        sites.sort(key=lambda p: math.hypot(p[0]-pad["x"], p[1]-pad["y"]))
        cap_sites.extend(sites)
        cap_rows.append({"pad": ref, "escape_count": len(escapes or []),
                         "site_count": len(sites),
                         "sites_mm": [[mm(x), mm(y)] for x, y in sites[:16]]})

    ranked = []
    for site in package_sites:
        reached = reachable_on_inner(board, site, cap_sites)
        if reached:
            nearest = min(reached, key=lambda p: math.hypot(p[0]-site[0], p[1]-site[1]))
            ranked.append({"package_via_mm": [mm(site[0]), mm(site[1])],
                           "nearest_cap_via_mm": [mm(nearest[0]), mm(nearest[1])],
                           "straight_span_mm": round(math.hypot(nearest[0]-site[0], nearest[1]-site[1])/1e6, 3),
                           "reachable_cap_sites": len(reached)})
    ranked.sort(key=lambda row: (row["straight_span_mm"], row["package_via_mm"]))
    return envelope, package_seed, all_package_sites, package_sites, cap_rows, ranked


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    before = hashlib.sha256(BOARD.read_bytes()).hexdigest()
    envelope, seed, all_sites, sites, caps, ranked = scan()
    report = {
        "schema": 1,
        "board": str(BOARD.relative_to(ROOT)),
        "authoritative_board_sha256": before,
        "authoritative_unchanged": before == hashlib.sha256(BOARD.read_bytes()).hexdigest(),
        "net": NET,
        "method": "D422_west_neck_25um_all_layer_via_and_In3_reachability",
        "oscillator_no_via_envelope_mm": [mm(v) for v in envelope],
        "package_seed_mm": [mm(seed["x"]), mm(seed["y"])],
        "all_reachable_package_site_count": len(all_sites),
        "nearest_reachable_package_sites_mm": [[mm(x), mm(y)] for x, y in all_sites[:16]],
        "outside_envelope_package_site_count": len(sites),
        "cap_landings": caps,
        "corridor_candidate_count": len(ranked),
        "ranked_corridors": ranked[:32],
        "promotion_candidate": False,
    }
    encoded = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(encoded, encoding="utf-8")
    else:
        print(encoded, end="")
    return 0 if report["authoritative_unchanged"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
