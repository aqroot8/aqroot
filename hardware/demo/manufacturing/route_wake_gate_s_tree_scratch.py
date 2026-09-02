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

def compact(points):
    return tuple(p for i, p in enumerate(points) if not i or p != points[i-1])

def leg_paths(a, b):
    yield "direct", compact((a, b))
    yield "x_then_y", compact((a, (b[0], a[1]), b))
    yield "y_then_x", compact((a, (a[0], b[1]), b))

def mixed_join_hub(board, first, start):
    """Join R66 to the qualified hub through one ordinary In2/In3 via."""
    second = "I3" if first == "I2" else "I2"
    hub = R63_FANOUT[-1]
    tested_sites = tested_paths = 0
    # This lattice covers the complete local wake-gate rectangle with a small
    # perimeter allowance.  Endpoint escapes and the R63 hub are already
    # independently qualified, so only the intervening haul is broadened.
    for via in ((x, y) for x in range(45_000_000, 66_000_001, 500_000)
                for y in range(48_000_000, 68_000_001, 500_000)):
        tested_sites += 1
        if not all(board.point_free(layer, NET, *via, 600_000,
                                    200_000, 200_000, 25_000)
                   for layer in board.cu):
            continue
        for left_name, left in leg_paths(start, via):
            for right_name, right in leg_paths(via, hub):
                tested_paths += 1; mark = board.mark()
                left_ok = all(emit(board, first, a, b)
                              for a, b in zip(left, left[1:]))
                if left_ok:
                    board.via(NET, *via, 600_000, 300_000)
                right_ok = left_ok and all(emit(board, second, a, b)
                                           for a, b in zip(right, right[1:]))
                if right_ok:
                    return {"ok": True, "family": "mixed_one_via",
                            "layer_order": [first, second],
                            "leg_families": [left_name, right_name],
                            "transition_via_mm": [via[0]/1e6, via[1]/1e6],
                            "tested_sites": tested_sites,
                            "tested_paths": tested_paths}
                board.revert(mark)
    return {"ok": False, "reason": "NO_MIXED_ONE_VIA_HUB_JOIN",
            "layer_order": [first, second], "tested_sites": tested_sites,
            "tested_paths": tested_paths}

def mixed_two_join_hub(board, first, start):
    """Join R66 to the hub through a first/second/first layer dogleg."""
    second = "I3" if first == "I2" else "I2"
    hub = R63_FANOUT[-1]
    sites = [(x, y) for x in range(45_000_000, 66_000_001, 500_000)
             for y in range(48_000_000, 68_000_001, 500_000)]
    # Board obstacles are static during this search except for same-net trial
    # copper.  Qualify ordinary transition barrels once rather than repeating
    # the full-board point test inside the quadratic via-pair loop.  The only
    # new hole-to-hole relationship is via1/via2, checked explicitly below.
    free_sites = [p for p in sites
                  if all(board.point_free(layer, NET, *p, 600_000,
                                          200_000, 200_000, 25_000)
                         for layer in board.cu)]
    right_options = []
    for via2 in free_sites:
        for right_name, right in leg_paths(via2, hub):
            mark = board.mark()
            if all(emit(board, first, a, b) for a, b in zip(right, right[1:])):
                right_options.append((via2, right_name, right))
            board.revert(mark)
    tested_first_sites = tested_second_sites = tested_paths = 0
    # Build the two outside legs first.  This sharply bounds the cross-layer
    # co-search to transition barrels that are actually reachable from both
    # endpoints, while still covering the complete D-523 local lattice.
    for via1 in free_sites:
        tested_first_sites += 1
        for left_name, left in leg_paths(start, via1):
            outer_mark = board.mark()
            if not all(emit(board, first, a, b) for a, b in zip(left, left[1:])):
                board.revert(outer_mark); continue
            board.via(NET, *via1, 600_000, 300_000)
            for via2, right_name, right in right_options:
                tested_second_sites += 1
                # D-257: 0.30 mm drills require >=0.25 mm hole-to-hole.
                if math.hypot(via2[0]-via1[0], via2[1]-via1[1]) < 550_000:
                    continue
                right_mark = board.mark()
                if not all(emit(board, first, a, b)
                           for a, b in zip(right, right[1:])):
                    board.revert(right_mark); continue
                board.via(NET, *via2, 600_000, 300_000)
                for middle_name, middle in leg_paths(via1, via2):
                    tested_paths += 1; middle_mark = board.mark()
                    if all(emit(board, second, a, b)
                           for a, b in zip(middle, middle[1:])):
                        return {"ok": True, "family": "mixed_two_via",
                                "layer_order": [first, second, first],
                                "leg_families": [left_name, middle_name, right_name],
                                "transition_vias_mm": [[via1[0]/1e6, via1[1]/1e6],
                                                       [via2[0]/1e6, via2[1]/1e6]],
                                "static_legal_sites": len(free_sites),
                                "static_right_options": len(right_options),
                                "tested_first_sites": tested_first_sites,
                                "tested_second_sites": tested_second_sites,
                                "tested_paths": tested_paths}
                    board.revert(middle_mark)
                board.revert(right_mark)
            board.revert(outer_mark)
    return {"ok": False, "reason": "NO_MIXED_TWO_VIA_HUB_JOIN",
            "layer_order": [first, second, first],
            "static_legal_sites": len(free_sites),
            "static_right_options": len(right_options),
            "tested_first_sites": tested_first_sites,
            "tested_second_sites": tested_second_sites,
            "tested_paths": tested_paths}

def run_case(work, r66_site, q10_site, baseline, layer_order=("I2","I3"), mode="one"):
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
            route["join"]=(mixed_two_join_hub(board,layer,escape["via"])
                           if mode == "two" and ref == "R66.1"
                           else mixed_join_hub(board,layer,escape["via"])
                           if mode == "one" and ref == "R66.1"
                           else join_hub(board,layer,escape["via"]))
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
    ap=argparse.ArgumentParser(); ap.add_argument("--candidate",type=Path); ap.add_argument("--promote",action="store_true")
    ap.add_argument("--single-layer",action="store_true",help="reproduce the D-522 planar family")
    ap.add_argument("--two-transition",action="store_true",help="screen the final two-transition family")
    a=ap.parse_args()
    before=sha(BOARD); baseline=copper(BOARD)
    with tempfile.TemporaryDirectory(prefix="aqroot-demo-wake-gate-") as td:
        cases=[]
        for layer_order in (("I2","I3"),("I3","I2")):
            for r66_site in range(8):
                # Do not multiply identical R66 failures by all Q10 sites.
                mode = "planar" if a.single_layer else "two" if a.two_transition else "one"
                first=run_case(Path(td),r66_site,0,baseline,layer_order,mode); cases.append(first)
                if first["promotion_candidate"]: break
                # The two-transition R66 search is the expensive object of
                # this bounded family.  Do not recompute an identical R66
                # witness for seven Q10 variants; a surviving Q10 wall is the
                # explicit successor transaction.
                if len(first["routes"]) == 2 and mode != "two":
                    for q10_site in range(1,8):
                        case=run_case(Path(td),r66_site,q10_site,baseline,layer_order,mode); cases.append(case)
                        if case["promotion_candidate"]: break
                if any(c["promotion_candidate"] for c in cases): break
            if any(c["promotion_candidate"] for c in cases): break
        winners=[c for c in cases if c["promotion_candidate"]]
        if winners and a.candidate: a.candidate.write_bytes(winners[0]["path"].read_bytes())
        if a.promote:
            if not winners or sha(BOARD)!=before: raise RuntimeError("refuse promotion")
            BOARD.write_bytes(winners[0]["path"].read_bytes())
        for c in cases: c.pop("path",None)
    print(json.dumps({"schema":4,"authoritative_board_sha256":before,"authoritative_unchanged":sha(BOARD)==before,
                      "mode":"single_layer" if a.single_layer else "r66_mixed_two_via" if a.two_transition else "r66_mixed_one_via",
                      "search_contract":{"far_endpoint_sites_each":8,
                                           "layer_orders":[["I2","I3"],["I3","I2"]],
                                           "hub_join_families_each":165,
                                           "transition_lattice_mm":{"x":[45,66,.5],"y":[48,68,.5]}},
                      "reserved_r63_fanout":{"path_mm":[[x/1e6,y/1e6] for x,y in R63_FANOUT],
                                                "via_mm":[x/1e6 for x in R63_FANOUT[-1]],
                                                "via_diameter_mm":.6,"via_drill_mm":.3},
                      "cases":cases,"promotion_candidates":len(winners)},indent=2,sort_keys=True)); return 0 if winners else 2
if __name__=="__main__": raise SystemExit(main())
