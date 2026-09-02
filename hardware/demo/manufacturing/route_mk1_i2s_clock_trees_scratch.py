#!/usr/bin/env python3
"""Screen complete I2S clock trees with the MCU as hub and U5 as a stub."""

import argparse, hashlib, itertools, json, math, subprocess, sys, tempfile
from collections import Counter
from pathlib import Path
import pcbnew

ROOT = Path(__file__).resolve().parents[3]
BOARD = ROOT / "hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb"
LEDGER = Path(__file__).with_name("routing_ledger.py")
sys.path.insert(0, str(ROOT / "hardware/beta-v2/checks"))
import incremental_router as ir  # noqa: E402
import qrouter as qr  # noqa: E402

WIDTH = CLEARANCE = PAD_CLEARANCE = 200_000
ACCEPTED = {"lib_footprint_issues", "hole_clearance", "solder_mask_bridge"}
CLOCKS = {
    "LRCLK": {"net": "/I2S_LRCLK", "mk": "MK1.5", "mcu": "U1.33", "amp": "U5.14",
              "pad": (5.075, 98.280)},
    "BCLK": {"net": "/I2S_BCLK", "mk": "MK1.6", "mcu": "U1.32", "amp": "U5.16",
             "pad": (5.075, 98.930)},
}
LAYOUTS = (
    {"LRCLK": (7.000, 98.280), "BCLK": (7.750, 98.930)},
    {"LRCLK": (7.750, 98.280), "BCLK": (7.000, 98.930)},
    {"LRCLK": (7.000, 98.280), "BCLK": (8.000, 98.930)},
    {"LRCLK": (8.000, 98.280), "BCLK": (7.000, 98.930)},
)
SPINE_X = tuple(range(10_000_000, 66_000_001, 4_000_000))
SPINE_Y = tuple(range(102_000_000, 142_000_001, 4_000_000))

def um(v): return int(round(v * 1_000_000))
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def copper(path):
    out = Counter()
    for item in pcbnew.LoadBoard(str(path)).GetTracks():
        if item.GetClass() == "PCB_VIA":
            p = item.GetPosition(); key = (item.GetNetname(), "VIA", item.GetWidth(pcbnew.F_Cu), item.GetDrillValue(), p.x, p.y)
        else:
            ends = sorted(((item.GetStart().x, item.GetStart().y), (item.GetEnd().x, item.GetEnd().y)))
            key = (item.GetNetname(), item.GetLayerName(), item.GetWidth(), *ends)
        out[key] += 1
    return out

def emit(board, net, layer, a, b):
    blockers = []
    for shape in board.obstacles(layer, net):
        if qr.seg_shape_dist(*a, *b, shape) < board.margin(shape, WIDTH, PAD_CLEARANCE, CLEARANCE):
            blockers.append(shape.tag)
    edge = qr.EDGE_CLR + WIDTH / 2
    if not (board.ex0 + edge <= min(a[0], b[0]) and max(a[0], b[0]) <= board.ex1 - edge and
            board.ey0 + edge <= min(a[1], b[1]) and max(a[1], b[1]) <= board.ey1 - edge):
        blockers.append("board_edge")
    if blockers: return {"ok": False, "blockers": sorted(set(blockers))[:8]}
    board.track(net, layer, *a, *b, WIDTH)
    return {"ok": True, "mm": math.hypot(b[0]-a[0], b[1]-a[1])/1e6}

def staged_join(board, net, layer, a, b):
    tested = 0
    for x in SPINE_X:
        for y in SPINE_Y:
            tested += 1; mark = board.mark()
            points = (a, (x, a[1]), (x, y), (b[0], y), b)
            legs = [emit(board, net, layer, p, q) for p, q in zip(points, points[1:])]
            if all(leg["ok"] for leg in legs):
                return {"ok": True, "tested": tested, "spine_mm": [x/1e6, y/1e6],
                        "mm": sum(leg.get("mm", 0) for leg in legs)}
            board.revert(mark)
    return {"ok": False, "tested": tested, "reason": "NO_STAGED_CORRIDOR"}

def run_case(work, layout, layers, clock_order, branch_order, baseline):
    scratch = work / (f"{clock_order[0]}-{layers['LRCLK']}-{layout['LRCLK'][0]:.2f}.kicad_pcb")
    for suffix in (".kicad_pcb", ".kicad_dru", ".kicad_pro"):
        scratch.with_suffix(suffix).write_bytes(BOARD.with_suffix(suffix).read_bytes())
    board = qr.QBoard(scratch); ir.inject_existing_via_obstacles(board)
    routes = []; hubs = {}
    for name in ("LRCLK", "BCLK"):
        spec = CLOCKS[name]; start = tuple(map(um, spec["pad"])); hub = tuple(map(um, layout[name]))
        if not all(board.point_free(layer, spec["net"], *hub, 600_000, 200_000, 200_000, 25_000) for layer in board.cu):
            return {"promotion_candidate": False, "reason": f"{name}_MK_VIA_BLOCKED"}
        board.track(spec["net"], "B", *start, *hub, WIDTH); board.via(spec["net"], *hub, 600_000, 300_000)
        hubs[name] = hub
    for name in clock_order:
        spec = CLOCKS[name]; layer = layers[name]
        pads = {p["ref"]: p for p in ir.physical_net_pads(board, spec["net"])}
        endpoints = {}
        for role in branch_order:
            ref = spec[role]
            reserved = qr.reserve_escape(board, spec["net"], pads[ref], WIDTH, PAD_CLEARANCE, CLEARANCE,
                near="F", far=layer, via_dia=600_000, via_drill=300_000, target=hubs[name],
                site_index=0, site_separation=300_000)
            routes.append({"clock": name, "role": role, "reserve": reserved})
            if not reserved.get("ok"): return finish(scratch, board, routes, baseline, False)
            endpoints[role] = reserved["via"]
        # D-484 proved that an MK1 hub consumes the available two-spine
        # corridor on the amplifier branch before reaching the MCU.  Reverse
        # the tree: make the MCU escape the hub, take the long MK1 leg first,
        # then attach U5 as the short branch.  branch_order still governs
        # endpoint reservation so both package-order interactions are tested.
        for role, start, end in (("mk", endpoints["mcu"], hubs[name]),
                                 ("amp_stub", endpoints["mcu"], endpoints["amp"])):
            joined = staged_join(board, spec["net"], layer, start, end)
            routes.append({"clock": name, "role": role, "join": joined})
            if not joined.get("ok"): return finish(scratch, board, routes, baseline, False)
    return finish(scratch, board, routes, baseline, True)

def finish(scratch, board, routes, baseline, geometrically_complete):
    board.save(scratch)
    if not geometrically_complete:
        return {"routes": routes, "reason": "INCOMPLETE_STAGED_TREE",
                "promotion_candidate": False, "candidate_sha256": sha(scratch),
                "path": scratch}
    drc = scratch.with_suffix(".drc.json")
    subprocess.run(["kicad-cli", "pcb", "drc", "--refill-zones", "--save-board", "--format", "json",
        "--units", "mm", "--severity-all", "--schematic-parity", "-o", str(drc), str(scratch)],
        text=True, capture_output=True)
    violations = json.loads(drc.read_text()).get("violations", []); types = Counter(v.get("type", "unknown") for v in violations)
    attributable = [v for v in violations if v.get("type") not in ACCEPTED]
    report = scratch.with_suffix(".ledger.json")
    subprocess.run([sys.executable, str(LEDGER), "--board", str(scratch), str(report)], check=True, stdout=subprocess.DEVNULL)
    ledger = json.loads(report.read_text()); targets = {r["net"]: r["open_edges"] for r in ledger["nets"] if r["net"] in {c["net"] for c in CLOCKS.values()}}
    after = copper(scratch); removed = baseline-after; added = after-baseline
    wrong = [list(x) for x in added if x[0] not in {c["net"] for c in CLOCKS.values()}]
    promotion = geometrically_complete and targets == {"/I2S_BCLK": 0, "/I2S_LRCLK": 0} and not attributable and not removed and not wrong
    return {"routes": routes, "drc_types": dict(types), "attributable_drc": attributable,
        "target_open_edges": targets, "connectivity": ledger["connectivity"], "added_items": sum(added.values()),
        "removed_accepted_copper_items": sum(removed.values()), "wrong_net_additions": wrong,
        "promotion_candidate": promotion, "candidate_sha256": sha(scratch), "path": scratch}

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--candidate", type=Path); ap.add_argument("--promote", action="store_true"); args = ap.parse_args()
    before = sha(BOARD); baseline = copper(BOARD); cases=[]
    with tempfile.TemporaryDirectory(prefix="aqroot-demo-mk1-clock-trees-") as td:
        work=Path(td)
        for layout, layer_order, clock_order, branch_order in itertools.product(LAYOUTS, itertools.permutations(("I2","I3")), itertools.permutations(("LRCLK","BCLK")), itertools.permutations(("amp","mcu"))):
            layers={"LRCLK":layer_order[0],"BCLK":layer_order[1]}
            case=run_case(work,layout,layers,clock_order,branch_order,baseline); case.update(layout=layout,layers=layers,clock_order=clock_order,branch_order=branch_order); cases.append(case)
            if case.get("promotion_candidate"): break
        winners=[c for c in cases if c.get("promotion_candidate")]
        if winners and args.candidate: args.candidate.write_bytes(winners[0]["path"].read_bytes())
        if args.promote:
            if not winners or sha(BOARD)!=before: raise RuntimeError("refuse promotion: gate failed or authority changed")
            BOARD.write_bytes(winners[0]["path"].read_bytes())
        for c in cases: c.pop("path",None)
    print(json.dumps({"schema":1,"authoritative_board_sha256":before,"authoritative_unchanged":sha(BOARD)==before,
        "cases":cases,"promotion_candidates":len(winners)},indent=2,sort_keys=True))
    return 0 if winners else 2

if __name__ == "__main__": raise SystemExit(main())
