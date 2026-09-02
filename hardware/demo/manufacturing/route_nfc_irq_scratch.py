#!/usr/bin/env python3
"""Atomically route and gate the fitted NFC IRQ link."""

import argparse, hashlib, json, math, subprocess, sys, tempfile
from collections import Counter
from pathlib import Path
import pcbnew

ROOT = Path(__file__).resolve().parents[3]
BOARD = ROOT / "hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb"
LEDGER = Path(__file__).with_name("routing_ledger.py")
NET = "/NFC_IRQ"; WIDTH = CLEARANCE = 200_000
U9_VIA = (35_000_000, 36_000_000)
U9_PATH = ((34_750_000, 32_275_000), (34_750_000, 33_000_000),
           (35_000_000, 33_000_000), U9_VIA)
ACCEPTED = {"lib_footprint_issues", "hole_clearance", "solder_mask_bridge"}
sys.path.insert(0, str(ROOT / "hardware/beta-v2/checks"))
import incremental_router as ir
import qrouter as qr

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

def emit(board, a, b, layer):
    for shape in board.obstacles(layer, NET):
        if qr.seg_shape_dist(*a, *b, shape) < board.margin(shape, WIDTH, CLEARANCE, CLEARANCE): return False
    board.track(NET, layer, *a, *b, WIDTH); return True

def corridors(a, b):
    yield (a, b)
    yield (a, (a[0], b[1]), b); yield (a, (b[0], a[1]), b)
    for x in range(3_000_000, 68_000_001, 2_000_000): yield (a, (x, a[1]), (x, b[1]), b)
    for y in range(38_000_000, 118_000_001, 2_000_000): yield (a, (a[0], y), (b[0], y), b)

def join(board, a, b, layer):
    for index, points in enumerate(corridors(a, b)):
        mark = board.mark()
        if all(emit(board, p, q, layer) for p, q in zip(points, points[1:])):
            return {"ok": True, "case": index, "waypoints_mm": [[x/1e6,y/1e6] for x,y in points[1:-1]],
                    "mm": sum(math.hypot(q[0]-p[0],q[1]-p[1]) for p,q in zip(points,points[1:]))/1e6}
        board.revert(mark)
    return {"ok": False, "reason": "NO_STAGED_CORRIDOR"}

def run_case(work, inner, site, baseline):
    scratch = work / f"{inner}-{site}.kicad_pcb"
    for suffix in (".kicad_pcb", ".kicad_dru", ".kicad_pro"): scratch.with_suffix(suffix).write_bytes(BOARD.with_suffix(suffix).read_bytes())
    board = qr.QBoard(scratch); ir.inject_existing_via_obstacles(board)
    pads = {p["ref"]:p for p in ir.physical_net_pads(board, NET)}
    if set(pads) != {"U1.11", "U9.27"}: raise RuntimeError(sorted(pads))
    fanout = (all(board.point_free(layer, NET, *U9_VIA, 600_000, CLEARANCE, CLEARANCE, 25_000) for layer in board.cu)
              and all(emit(board,a,b,"F") for a,b in zip(U9_PATH,U9_PATH[1:])))
    if fanout: board.via(NET,*U9_VIA,600_000,300_000)
    u1 = qr.reserve_escape(board, NET, pads["U1.11"], WIDTH, CLEARANCE, CLEARANCE, near="F", far=inner,
                           via_dia=600_000, via_drill=300_000, target=U9_VIA, site_index=site, site_separation=300_000) if fanout else {"ok":False}
    joined = join(board,u1["via"],U9_VIA,inner) if u1.get("ok") else u1
    result={"inner":inner,"site":site,"fanout":fanout,"u1":u1,"join":joined,"promotion_candidate":False,"path":scratch}
    if not joined.get("ok"): return result
    board.save(scratch); drc=scratch.with_suffix(".drc.json")
    subprocess.run(["kicad-cli","pcb","drc","--refill-zones","--save-board","--format","json","--units","mm","--severity-all","--schematic-parity","-o",str(drc),str(scratch)],check=True,capture_output=True,text=True)
    types=Counter(v.get("type","unknown") for v in json.loads(drc.read_text()).get("violations",[]))
    lp=scratch.with_suffix(".ledger.json"); subprocess.run([sys.executable,str(LEDGER),"--board",str(scratch),str(lp)],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    ledger=json.loads(lp.read_text()); target=next(n for n in ledger["nets"] if n["net"]==NET)
    after=copper(scratch); removed=baseline-after; added=after-baseline; attributable=sum(n for t,n in types.items() if t not in ACCEPTED)
    result.update({"drc_types":dict(types),"attributable_drc_count":attributable,"target_open_edges":target["open_edges"],
      "connectivity":ledger["connectivity"],"removed_accepted_copper_items":sum(removed.values()),"added_items":sum(added.values()),
      "wrong_net_additions":sum(n for k,n in added.items() if k[0]!=NET),"candidate_sha256":sha(scratch)})
    result["promotion_candidate"] = not attributable and not removed and not result["wrong_net_additions"] and target["open_edges"]==0
    return result

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--candidate",type=Path); ap.add_argument("--promote",action="store_true"); args=ap.parse_args()
    before=sha(BOARD); baseline=copper(BOARD)
    with tempfile.TemporaryDirectory(prefix="aqroot-demo-nfc-irq-") as td:
        matrix=(("I2",0),) if args.promote else tuple((layer,site) for layer in ("I2","I3") for site in range(8))
        cases=[run_case(Path(td),*case,baseline) for case in matrix]; winners=[c for c in cases if c["promotion_candidate"]]
        if winners and args.candidate: args.candidate.write_bytes(winners[0]["path"].read_bytes())
        if args.promote:
            if not winners or sha(BOARD)!=before: raise RuntimeError("refuse promotion")
            BOARD.write_bytes(winners[0]["path"].read_bytes())
        for c in cases: c.pop("path",None)
    print(json.dumps({"schema":1,"authoritative_board_sha256":before,"authoritative_unchanged":sha(BOARD)==before,"cases":cases,"promotion_candidates":len(winners)},indent=2,sort_keys=True))
    return 0 if winners else 2

if __name__=="__main__": raise SystemExit(main())
