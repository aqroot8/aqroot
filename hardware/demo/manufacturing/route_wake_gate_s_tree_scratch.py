#!/usr/bin/env python3
"""Atomically screen the retained three-land accessory wake-gate signal."""

import argparse, hashlib, itertools, json, subprocess, sys, tempfile
from collections import Counter
from pathlib import Path
import pcbnew

ROOT = Path(__file__).resolve().parents[3]
BOARD = ROOT / "hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb"
LOCAL = Path(__file__).with_name("route_local_two_pad.py")
LEDGER = Path(__file__).with_name("routing_ledger.py")
NET = "/09_COMMUNITY_HEADER/WAKE_GATE_S"
LEGS = ("WAKE_GATE_PULLUP_SERIES", "WAKE_GATE_SERIES_FET")
ACCEPTED = {"lib_footprint_issues", "hole_clearance", "solder_mask_bridge"}

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

def run_case(work, order, baseline):
    p=work/("-".join(order)+".kicad_pcb")
    for s in (".kicad_pcb",".kicad_dru",".kicad_pro"): p.with_suffix(s).write_bytes(BOARD.with_suffix(s).read_bytes())
    routes=[]
    for leg in order:
        r=subprocess.run([sys.executable,str(LOCAL),leg,"--route",str(p)],text=True,capture_output=True,check=True)
        routes.append(json.loads(r.stdout))
        if not routes[-1]["result"].get("ok"): break
    rpt=p.with_suffix(".drc.json")
    subprocess.run(["kicad-cli","pcb","drc","--refill-zones","--save-board","--format","json","--units","mm","--severity-all","--schematic-parity","-o",str(rpt),str(p)],text=True,capture_output=True,check=True)
    violations=json.loads(rpt.read_text()).get("violations",[]); types=Counter(v.get("type","unknown") for v in violations)
    attributable=[v for v in violations if v.get("type") not in ACCEPTED]
    lp=p.with_suffix(".ledger.json"); subprocess.run([sys.executable,str(LEDGER),"--board",str(p),str(lp)],check=True,stdout=subprocess.DEVNULL)
    ledger=json.loads(lp.read_text()); target=next(x for x in ledger["nets"] if x["net"]==NET)
    after=copper(p); removed=baseline-after; added=after-baseline
    ok=(len(routes)==2 and all(x["result"].get("ok") for x in routes) and target["open_edges"]==0 and not attributable and not removed and all(k[0]==NET for k in added))
    return {"order":order,"routes":routes,"drc_types":dict(types),"attributable_drc_count":len(attributable),"target_open_edges":target["open_edges"],"connectivity":ledger["connectivity"],"removed_accepted_copper_items":sum(removed.values()),"added_items":sum(added.values()),"wrong_net_additions":sum(n for k,n in added.items() if k[0]!=NET),"promotion_candidate":ok,"candidate_sha256":sha(p),"path":p}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--candidate",type=Path); ap.add_argument("--promote",action="store_true"); a=ap.parse_args()
    before=sha(BOARD); baseline=copper(BOARD)
    with tempfile.TemporaryDirectory(prefix="aqroot-demo-wake-gate-") as td:
        cases=[run_case(Path(td),o,baseline) for o in itertools.permutations(LEGS)]; winners=[c for c in cases if c["promotion_candidate"]]
        if winners and a.candidate: a.candidate.write_bytes(winners[0]["path"].read_bytes())
        if a.promote:
            if not winners or sha(BOARD)!=before: raise RuntimeError("refuse promotion")
            BOARD.write_bytes(winners[0]["path"].read_bytes())
        for c in cases: c.pop("path",None)
    print(json.dumps({"schema":1,"authoritative_board_sha256":before,"authoritative_unchanged":sha(BOARD)==before,"cases":cases,"promotion_candidates":len(winners)},indent=2,sort_keys=True)); return 0 if winners else 2
if __name__=="__main__": raise SystemExit(main())
