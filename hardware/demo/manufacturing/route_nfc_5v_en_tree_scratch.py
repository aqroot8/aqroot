#!/usr/bin/env python3
"""Atomically screen and gate the retained three-land NFC_5V_EN tree."""

import argparse, hashlib, json, math, subprocess, sys, tempfile
from collections import Counter
from pathlib import Path
import pcbnew

ROOT = Path(__file__).resolve().parents[3]
BOARD = ROOT / "hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb"
LEDGER = Path(__file__).with_name("routing_ledger.py")
NET = "/NFC_5V_EN"
ACCEPTED = {"lib_footprint_issues", "hole_clearance", "solder_mask_bridge"}
sys.path.insert(0, str(ROOT / "hardware/beta-v2/checks"))
import incremental_router as ir
import qrouter as qr

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def copper(p):
    out = Counter()
    for item in pcbnew.LoadBoard(str(p)).GetTracks():
        if item.GetClass() == "PCB_VIA":
            q = item.GetPosition(); key = (item.GetNetname(), "VIA", item.GetWidth(pcbnew.F_Cu), item.GetDrillValue(), q.x, q.y)
        else:
            ends = sorted(((item.GetStart().x, item.GetStart().y), (item.GetEnd().x, item.GetEnd().y)))
            key = (item.GetNetname(), item.GetLayerName(), item.GetWidth(), *ends)
        out[key] += 1
    return out

def emit(board, layer, a, b):
    if any(qr.seg_shape_dist(*a, *b, shape) < board.margin(shape, 200_000, 200_000, 200_000)
           for shape in board.obstacles(layer, NET)): return False
    board.track(NET, layer, *a, *b, 200_000); return True

def join_inner(board, layer, a, b):
    paths=[(a,b),(a,(b[0],a[1]),b),(a,(a[0],b[1]),b)]
    paths += [(a,(x,a[1]),(x,b[1]),b) for x in range(3_000_000,69_000_001,500_000)]
    paths += [(a,(a[0],y),(b[0],y),b) for y in range(3_000_000,145_000_001,500_000)]
    for tested, points in enumerate(paths,1):
        mark=board.mark()
        if all(emit(board,layer,p,q) for p,q in zip(points,points[1:])):
            return {"ok":True,"tested":tested,"waypoints_mm":[[x/1e6,y/1e6] for x,y in points[1:-1]],"mm":sum(math.hypot(q[0]-p[0],q[1]-p[1]) for p,q in zip(points,points[1:]))/1e6}
        board.revert(mark)
    return {"ok":False,"reason":"NO_INNER_JOIN","tested":len(paths)}

def compact(points):
    return tuple(p for i, p in enumerate(points) if not i or p != points[i-1])

def leg_paths(a, b):
    yield "direct", compact((a, b))
    yield "x_then_y", compact((a, (b[0], a[1]), b))
    yield "y_then_x", compact((a, (a[0], b[1]), b))

def join_mixed(board, first, a, b):
    """Join the haul through one ordinary In2/In3 transition via."""
    second = "I3" if first == "I2" else "I2"
    tested_sites = tested_paths = 0
    # Finite 2 mm lattice spanning the U2/TP10 endpoint rectangle plus a
    # perimeter lane.  Endpoint sites are independently broadened below.
    for via in ((x, y) for x in range(3_000_000, 69_000_001, 2_000_000)
                for y in range(38_000_000, 146_000_001, 2_000_000)):
        tested_sites += 1
        if not all(board.point_free(layer, NET, *via, 600_000,
                                    200_000, 200_000, 25_000)
                   for layer in board.cu):
            continue
        for left_name, left in leg_paths(a, via):
            for right_name, right in leg_paths(via, b):
                tested_paths += 1; mark = board.mark()
                left_ok = all(emit(board, first, p, q)
                              for p, q in zip(left, left[1:]))
                if left_ok:
                    board.via(NET, *via, 600_000, 300_000)
                right_ok = left_ok and all(emit(board, second, p, q)
                                           for p, q in zip(right, right[1:]))
                if right_ok:
                    return {"ok":True,"family":"mixed_one_via",
                            "layer_order":[first,second],
                            "leg_families":[left_name,right_name],
                            "transition_via_mm":[via[0]/1e6,via[1]/1e6],
                            "tested_sites":tested_sites,
                            "tested_paths":tested_paths}
                board.revert(mark)
    return {"ok":False,"reason":"NO_MIXED_ONE_VIA_CORRIDOR",
            "layer_order":[first,second],"tested_sites":tested_sites,
            "tested_paths":tested_paths}

def run_case(path, inner, u2_site, tp_site, order, mixed):
    board = qr.QBoard(path); ir.inject_existing_via_obstacles(board)
    pads = {p["ref"]: p for p in ir.physical_net_pads(board, NET)}
    if set(pads) != {"U2.6", "TP10.1", "R14.1", "U13.2"}: raise RuntimeError(sorted(pads))
    routes = []
    if order == "local-first":
        routes.append(qr.connect_role(board, NET, pads["R14.1"], pads["TP10.1"], "B", 200_000, 200_000, 200_000, G=25_000))
        if not routes[-1].get("ok"): return routes
        routes.append(qr.connect_role(board, NET, pads["U13.2"], pads["TP10.1"], "B", 200_000, 200_000, 200_000, G=25_000))
        if not routes[-1].get("ok"): return routes
    a = qr.reserve_escape(board, NET, pads["U2.6"], 200_000, 200_000, 200_000,
        near="B", far=inner, via_dia=600_000, via_drill=300_000,
        target=(pads["TP10.1"]["x"], pads["TP10.1"]["y"]), site_index=u2_site, site_separation=300_000)
    b = {"ok": False, "reason": "NOT_ATTEMPTED"}
    if a.get("ok"):
        b = qr.reserve_escape(board, NET, pads["TP10.1"], 200_000, 200_000, 200_000,
            near="B", far=inner, via_dia=600_000, via_drill=300_000,
            target=(pads["U2.6"]["x"], pads["U2.6"]["y"]), site_index=tp_site, site_separation=300_000)
    join = {"ok": False, "reason": "NOT_ATTEMPTED"}
    if b.get("ok"):
        join = (join_mixed(board, inner, a["via"], b["via"])
                if mixed else join_inner(board, inner, a["via"], b["via"]))
    routes.append({"ok": a.get("ok") and b.get("ok") and join.get("ok"), "u2_escape": a, "tp_escape": b, "join": join})
    if routes[-1].get("ok") and order == "haul-first":
        routes.append(qr.connect_role(board, NET, pads["R14.1"], pads["TP10.1"], "B", 200_000, 200_000, 200_000, G=25_000))
        if routes[-1].get("ok"):
            routes.append(qr.connect_role(board, NET, pads["U13.2"], pads["TP10.1"], "B", 200_000, 200_000, 200_000, G=25_000))
    if len(routes) == 3 and all(r.get("ok") for r in routes): board.save(path)
    return routes

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--candidate",type=Path); ap.add_argument("--promote",action="store_true")
    ap.add_argument("--single-layer",action="store_true",help="reproduce the D-525 planar family")
    ap.add_argument("--case-start",type=int,default=0)
    ap.add_argument("--case-count",type=int,default=4); args=ap.parse_args()
    before=sha(BOARD); base=copper(BOARD); cases=[]
    with tempfile.TemporaryDirectory(prefix="aqroot-demo-nfc-5v-en-") as td:
        # D-525 already proved both local-first orders.  Screen the expensive
        # broadened haul first and replay both local branches only on success.
        matrix=[(inner,us,ts) for inner in ("I2","I3")
                for us in range(4) for ts in range(4)]
        selected=matrix[args.case_start:args.case_start+args.case_count]
        for inner,us,ts in selected:
                order="haul-first"
                p=Path(td)/f"{order}-{inner}-{us}-{ts}.kicad_pcb"
                for s in (".kicad_pcb",".kicad_dru",".kicad_pro"): p.with_suffix(s).write_bytes(BOARD.with_suffix(s).read_bytes())
                routes=run_case(p,inner,us,ts,order,not args.single_layer); row={"order":order,"inner":inner,"u2_site":us,"tp_site":ts,"routes":routes,"promotion_candidate":False,"path":p}
                if len(routes)==3 and all(r.get("ok") for r in routes):
                    rpt=p.with_suffix(".drc.json"); subprocess.run(["kicad-cli","pcb","drc","--refill-zones","--save-board","--format","json","--units","mm","--severity-all","--schematic-parity","-o",str(rpt),str(p)],check=True,capture_output=True,text=True)
                    types=Counter(v.get("type","unknown") for v in json.loads(rpt.read_text()).get("violations",[])); lp=p.with_suffix(".ledger.json")
                    subprocess.run([sys.executable,str(LEDGER),"--board",str(p),str(lp)],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
                    ledger=json.loads(lp.read_text()); target=next(n for n in ledger["nets"] if n["net"]==NET); after=copper(p); removed=base-after; added=after-base
                    row.update({"drc_types":dict(types),"target_open_edges":target["open_edges"],"connectivity":ledger["connectivity"],"removed_accepted_copper_items":sum(removed.values()),"added_items":sum(added.values()),"wrong_net_additions":sum(v for k,v in added.items() if k[0]!=NET)})
                    row["promotion_candidate"]=(target["open_edges"]==0 and not removed and not row["wrong_net_additions"] and not any(t not in ACCEPTED for t in types))
                cases.append(row)
                if row["promotion_candidate"]: break
        winners=[c for c in cases if c["promotion_candidate"]]
        if winners and args.candidate: args.candidate.write_bytes(winners[0]["path"].read_bytes())
        if args.promote:
            if not winners or sha(BOARD)!=before: raise RuntimeError("refuse promotion")
            BOARD.write_bytes(winners[0]["path"].read_bytes())
        for c in cases: c.pop("path",None)
    print(json.dumps({"schema":1,"authoritative_board_sha256":before,"authoritative_unchanged":sha(BOARD)==before,"mode":"single_layer" if args.single_layer else "mixed_one_via","case_start":args.case_start,"case_count":len(selected),"case_space":len(matrix),"cases":cases,"promotion_candidates":len(winners)},indent=2,sort_keys=True)); return 0 if winners else 2

if __name__ == "__main__": raise SystemExit(main())
