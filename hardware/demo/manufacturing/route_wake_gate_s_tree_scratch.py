#!/usr/bin/env python3
"""Atomically screen WAKE_GATE_S with the qualified R63 shared fanout reserved."""

import argparse, hashlib, itertools, json, math, subprocess, sys, tempfile
from collections import Counter
from pathlib import Path
import pcbnew

ROOT = Path(__file__).resolve().parents[3]
BOARD = ROOT / "hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb"
LEDGER = Path(__file__).with_name("routing_ledger.py")
NET = "/09_COMMUNITY_HEADER/WAKE_GATE_S"
ACCEPTED = {"lib_footprint_issues", "hole_clearance", "solder_mask_bridge"}
R63_FANOUT = ((55_700_000, 57_735_000), (55_200_000, 57_735_000),
              (55_200_000, 57_985_000))
sys.path.insert(0, str(ROOT / "hardware/beta-v2/checks"))
import incremental_router as ir  # noqa: E402
import qrouter as qr  # noqa: E402

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def copper(p):
    out = Counter()
    for i in pcbnew.LoadBoard(str(p)).GetTracks():
        if i.GetClass() == "PCB_VIA":
            q=i.GetPosition(); k=(i.GetNetname(),"VIA",i.GetWidth(pcbnew.F_Cu),i.GetDrillValue(),q.x,q.y)
        else:
            e=sorted(((i.GetStart().x,i.GetStart().y),(i.GetEnd().x,i.GetEnd().y)))
            k=(i.GetNetname(),i.GetLayerName(),i.GetWidth(),*e)
        out[k]+=1
    return out

def reserve_r63_fanout(path):
    """Install the first D-520-qualified R63.2 B.Cu launch witness."""
    board = pcbnew.LoadBoard(str(path)); net = board.FindNet(NET)
    for start, end in zip(R63_FANOUT, R63_FANOUT[1:]):
        track = pcbnew.PCB_TRACK(board); track.SetNet(net)
        track.SetLayer(pcbnew.B_Cu); track.SetWidth(200_000)
        track.SetStart(pcbnew.VECTOR2I(*start)); track.SetEnd(pcbnew.VECTOR2I(*end))
        board.Add(track)
    via = pcbnew.PCB_VIA(board); via.SetNet(net)
    via.SetPosition(pcbnew.VECTOR2I(*R63_FANOUT[-1]))
    via.SetWidth(600_000); via.SetDrill(300_000)
    via.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); board.Add(via)
    pcbnew.SaveBoard(str(path), board)

def emit(board, layer, a, b):
    for shape in board.obstacles(layer, NET):
        if qr.seg_shape_dist(*a, *b, shape) < board.margin(
                shape, 200_000, 200_000, 200_000):
            return False
    board.track(NET, layer, *a, *b, 200_000)
    return True

def join_hub(board, layer, start):
    hub = R63_FANOUT[-1]
    families = [(start, hub),
                (start, (hub[0], start[1]), hub),
                (start, (start[0], hub[1]), hub)]
    for x in range(45_000_000, 66_000_001, 250_000):
        families.append((start, (x, start[1]), (x, hub[1]), hub))
    for y in range(48_000_000, 68_000_001, 250_000):
        families.append((start, (start[0], y), (hub[0], y), hub))
    for tested, points in enumerate(families, 1):
        mark = board.mark()
        if all(emit(board, layer, a, b) for a, b in zip(points, points[1:])):
            return {"ok": True, "tested": tested,
                    "waypoints_mm": [[x/1e6, y/1e6] for x, y in points[1:-1]],
                    "length_mm": sum(math.hypot(b[0]-a[0], b[1]-a[1])
                                     for a, b in zip(points, points[1:]))/1e6}
        board.revert(mark)
    return {"ok": False, "reason": "NO_HUB_JOIN", "tested": len(families)}

def run_case(work, r66_site, q10_site, baseline, layer_order=("I2","I3")):
    p=work/f"r66-{r66_site}-q10-{q10_site}.kicad_pcb"
    for s in (".kicad_pcb",".kicad_dru",".kicad_pro"): p.with_suffix(s).write_bytes(BOARD.with_suffix(s).read_bytes())
    reserve_r63_fanout(p)
    board=qr.QBoard(p); ir.inject_existing_via_obstacles(board)
    pads={x["ref"]:x for x in ir.physical_net_pads(board,NET)}
    routes=[]
    for ref,site,layer in (("R66.1",r66_site,layer_order[0]),
                           ("Q10.2",q10_site,layer_order[1])):
        escape=qr.reserve_escape(board,NET,pads[ref],200_000,200_000,200_000,
            near="F",far=layer,via_dia=600_000,via_drill=300_000,
            target=R63_FANOUT[-1],site_index=site,site_separation=250_000)
        route={"ref":ref,"layer":layer,"site":site,"escape":escape}
        if escape.get("ok"):
            route["join"]=join_hub(board,layer,escape["via"])
        routes.append(route)
        if not escape.get("ok") or not route.get("join",{}).get("ok"): break
    board.save(p)
    if len(routes) != 2 or not all(x.get("join",{}).get("ok") for x in routes):
        return {"r66_site":r66_site,"q10_site":q10_site,
                "layer_order":layer_order,"routes":routes,
                "reason":"INCOMPLETE_SHARED_HUB_TREE",
                "promotion_candidate":False,"path":p}
    rpt=p.with_suffix(".drc.json")
    subprocess.run(["kicad-cli","pcb","drc","--refill-zones","--save-board","--format","json","--units","mm","--severity-all","--schematic-parity","-o",str(rpt),str(p)],text=True,capture_output=True,check=True)
    violations=json.loads(rpt.read_text()).get("violations",[]); types=Counter(v.get("type","unknown") for v in violations)
    attributable=[v for v in violations if v.get("type") not in ACCEPTED]
    lp=p.with_suffix(".ledger.json"); subprocess.run([sys.executable,str(LEDGER),"--board",str(p),str(lp)],check=True,stdout=subprocess.DEVNULL)
    ledger=json.loads(lp.read_text()); target=next(x for x in ledger["nets"] if x["net"]==NET)
    after=copper(p); removed=baseline-after; added=after-baseline
    ok=(len(routes)==2 and all(x.get("join",{}).get("ok") for x in routes) and target["open_edges"]==0 and not attributable and not removed and all(k[0]==NET for k in added))
    return {"r66_site":r66_site,"q10_site":q10_site,"layer_order":layer_order,"routes":routes,"drc_types":dict(types),"attributable_drc_count":len(attributable),"target_open_edges":target["open_edges"],"connectivity":ledger["connectivity"],"removed_accepted_copper_items":sum(removed.values()),"added_items":sum(added.values()),"wrong_net_additions":sum(n for k,n in added.items() if k[0]!=NET),"promotion_candidate":ok,"candidate_sha256":sha(p),"path":p}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--candidate",type=Path); ap.add_argument("--promote",action="store_true"); a=ap.parse_args()
    before=sha(BOARD); baseline=copper(BOARD)
    with tempfile.TemporaryDirectory(prefix="aqroot-demo-wake-gate-") as td:
        cases=[]
        for layer_order in (("I2","I3"),("I3","I2")):
            for r66_site in range(8):
                # Do not multiply identical R66 failures by all Q10 sites.
                first=run_case(Path(td),r66_site,0,baseline,layer_order); cases.append(first)
                if first["promotion_candidate"]: break
                if len(first["routes"]) == 2:
                    for q10_site in range(1,8):
                        case=run_case(Path(td),r66_site,q10_site,baseline,layer_order); cases.append(case)
                        if case["promotion_candidate"]: break
                if any(c["promotion_candidate"] for c in cases): break
            if any(c["promotion_candidate"] for c in cases): break
        winners=[c for c in cases if c["promotion_candidate"]]
        if winners and a.candidate: a.candidate.write_bytes(winners[0]["path"].read_bytes())
        if a.promote:
            if not winners or sha(BOARD)!=before: raise RuntimeError("refuse promotion")
            BOARD.write_bytes(winners[0]["path"].read_bytes())
        for c in cases: c.pop("path",None)
    print(json.dumps({"schema":3,"authoritative_board_sha256":before,"authoritative_unchanged":sha(BOARD)==before,
                      "search_contract":{"far_endpoint_sites_each":8,
                                           "layer_orders":[["I2","I3"],["I3","I2"]],
                                           "hub_join_families_each":165},
                      "reserved_r63_fanout":{"path_mm":[[x/1e6,y/1e6] for x,y in R63_FANOUT],
                                                "via_mm":[x/1e6 for x in R63_FANOUT[-1]],
                                                "via_diameter_mm":.6,"via_drill_mm":.3},
                      "cases":cases,"promotion_candidates":len(winners)},indent=2,sort_keys=True)); return 0 if winners else 2
if __name__=="__main__": raise SystemExit(main())
