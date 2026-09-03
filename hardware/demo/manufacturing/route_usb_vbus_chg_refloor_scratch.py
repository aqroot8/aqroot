#!/usr/bin/env python3
"""Atomically screen the minimum USB_VBUS_CHG pocket refloor transaction.

Withdraws complete REC_LIM_IN and ILIM_VSET copper on scratch copies, installs
the two qualified governed CHG necks, attempts the complete eleven-land CHG
tree, then replays both withdrawn nets.  Authority is writable only after the
full connectivity and real KiCad DRC gate passes.
"""

import argparse, hashlib, itertools, json, subprocess, sys, tempfile
from collections import Counter
from pathlib import Path
import pcbnew

import route_usb_vbus_chg_tree_scratch as chg
import enumerate_usb_vbus_chg_necks as necks

ROOT = Path(__file__).resolve().parents[3]
BOARD = chg.BOARD
LOCAL = Path(__file__).with_name("route_local_two_pad.py")
LEDGER = Path(__file__).with_name("routing_ledger.py")
WITHDRAWN = ("/01_POWER_TREE/REC_LIM_IN", "/01_POWER_TREE/ILIM_VSET")
REPLAY = {"/01_POWER_TREE/REC_LIM_IN": "REC_LIM_IN",
          "/01_POWER_TREE/ILIM_VSET": "ILIM_VSET"}

sys.path.insert(0, str(ROOT / "hardware/beta-v2/checks"))
import incremental_router as ir  # noqa: E402
import qrouter as qr  # noqa: E402

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def last_json(text):
    decoder=json.JSONDecoder(); records=[]
    for offset,char in enumerate(text):
        if char!="{": continue
        try:
            record,end=decoder.raw_decode(text[offset:]); records.append((end,record))
        except json.JSONDecodeError: pass
    if not records: raise RuntimeError("subprocess emitted no JSON")
    return max(records,key=lambda row:row[0])[1]

def copper(path):
    out=Counter(); b=pcbnew.LoadBoard(str(path))
    for i in b.GetTracks():
        if i.GetClass()=="PCB_VIA":
            p=i.GetPosition(); k=(i.GetNetname(),"VIA",i.GetWidth(pcbnew.F_Cu),i.GetDrillValue(),p.x,p.y)
        else:
            e=sorted(((i.GetStart().x,i.GetStart().y),(i.GetEnd().x,i.GetEnd().y)))
            k=(i.GetNetname(),i.GetLayerName(),i.GetWidth(),*e)
        out[k]+=1
    return out

def withdraw(path):
    b=pcbnew.LoadBoard(str(path)); count=Counter()
    for i in list(b.GetTracks()):
        if i.GetNetname() in WITHDRAWN:
            count[i.GetNetname()]+=1; b.Remove(i)
    b.Save(str(path)); return dict(count)

def mm(v): return round(v*1e6)

def governed_reservation(board, pads, ref, candidate):
    rule=necks.CASES[ref]; p=pads[ref]
    end=tuple(mm(v) for v in candidate["neck_end_mm"])
    via=tuple(mm(v) for v in candidate["via_mm"])
    board.track(chg.NET,"B",p["x"],p["y"],*end,rule["neck_width"])
    board.track(chg.NET,"B",*end,*via,chg.WIDTH)
    board.via(chg.NET,*via,chg.VIA_DIAMETER,chg.VIA_DRILL)
    return {"pad":ref,"ok":True,"governed_neck":True,"via":via,
            "neck_width_mm":rule["neck_width"]/1e6,
            "package_clearance_mm":rule["local_clearance"]/1e6,
            "candidate":candidate}

def build_chg(path, rc, uc):
    board=qr.QBoard(path); ir.inject_existing_via_obstacles(board)
    physical=ir.physical_net_pads(board,chg.NET); pads={p["ref"]:p for p in physical}
    reservations=[governed_reservation(board,pads,"R91.1",rc),
                  governed_reservation(board,pads,"U11.10",uc)]
    anchors=[(r["pad"],r["via"]) for r in reservations]
    centroid=(round(sum(p["x"] for p in physical)/len(physical)),round(sum(p["y"] for p in physical)/len(physical)))
    for ref in chg.PADS:
        if ref in ("R91.1","U11.10"): continue
        p=pads[ref]; r=qr.reserve_escape(board,chg.NET,p,chg.WIDTH,chg.CLEARANCE,chg.CLEARANCE,
            near=chg.face(p),far="I2",G=chg.GRID,fine=25_000,via_dia=chg.VIA_DIAMETER,
            via_drill=chg.VIA_DRILL,target=centroid,site_separation=450_000)
        reservations.append({"pad":ref,**r})
        if not r.get("ok"): return board,reservations,[]
        anchors.append((ref,tuple(r["via"])))
    parent=list(range(len(anchors)))
    def root(i):
        while parent[i]!=i: parent[i]=parent[parent[i]]; i=parent[i]
        return i
    edges=sorted(itertools.combinations(range(len(anchors)),2),key=lambda x:sum((anchors[x[0]][1][a]-anchors[x[1]][1][a])**2 for a in (0,1)))
    joins=[]
    for a,b in edges:
        if root(a)==root(b): continue
        result={"ok":False,"reason":"NO_PATH"}
        for layer in ("I2","I3"):
            mark=board.mark(); result=qr.join_reserved(board,chg.NET,anchors[a][1],anchors[b][1],chg.WIDTH,chg.CLEARANCE,chg.CLEARANCE,layer=layer,G=chg.GRID,fine=25_000)
            if result.get("ok"): result["selected_layer"]=layer; break
            board.revert(mark)
        joins.append({"a":anchors[a][0],"b":anchors[b][0],**result})
        if result.get("ok"): parent[root(b)]=root(a)
        if len({root(i) for i in range(len(anchors))})==1: break
    return board,reservations,joins

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--candidate",type=Path); ap.add_argument("--promote",action="store_true"); ap.add_argument("--case-start",type=int,default=0); ap.add_argument("--case-limit",type=int,default=16); ap.add_argument("--prepare",type=Path); args=ap.parse_args()
    if args.prepare:
        print(json.dumps(withdraw(args.prepare),sort_keys=True)); return 0
    before=sha(BOARD); baseline=copper(BOARD); cases=[]; winner=None
    with tempfile.TemporaryDirectory(prefix="aqroot-demo-chg-refloor-") as td:
        work=Path(td); seed=work/"seed.kicad_pcb"
        for s in (".kicad_pcb",".kicad_dru",".kicad_pro"): seed.with_suffix(s).write_bytes(BOARD.with_suffix(s).read_bytes())
        prepared=subprocess.run([sys.executable,str(Path(__file__)),"--prepare",str(seed)],text=True,capture_output=True,check=True)
        removed=last_json(prepared.stdout)
        nr=subprocess.run([sys.executable,str(Path(necks.__file__)),"--board",str(seed)],text=True,capture_output=True,check=True)
        scans={r["pad"]:r for r in last_json(nr.stdout)["pads"]}
        all_combos=list(itertools.product(scans["R91.1"]["candidates"],scans["U11.10"]["candidates"]))
        combos=all_combos[args.case_start:args.case_start+args.case_limit]
        for idx,(rc,uc) in enumerate(combos,start=args.case_start):
            scratch=work/f"case-{idx}.kicad_pcb"
            for s in (".kicad_pcb",".kicad_dru",".kicad_pro"): scratch.with_suffix(s).write_bytes(seed.with_suffix(s).read_bytes())
            board,reservations,joins=build_chg(scratch,rc,uc); board.save(scratch)
            replay=[]
            if len(joins)==10 and all(j.get("ok") for j in joins):
                for net in WITHDRAWN:
                    run=subprocess.run([sys.executable,str(LOCAL),REPLAY[net],"--route",str(scratch)],text=True,capture_output=True)
                    rec=json.loads(run.stdout); replay.append({"net":net,**rec})
                    if run.returncode or not rec["result"].get("ok"): break
            complete=len(joins)==10 and all(j.get("ok") for j in joins) and len(replay)==2 and all(x["result"].get("ok") for x in replay)
            types=Counter(); attributable=[]; opens={}; drc_exit=None
            if complete:
                drc=scratch.with_suffix(".drc.json"); run=subprocess.run(["kicad-cli","pcb","drc","--refill-zones","--save-board","--format","json","--units","mm","--severity-all","--schematic-parity","-o",str(drc),str(scratch)],text=True,capture_output=True)
                drc_exit=run.returncode; violations=json.loads(drc.read_text()).get("violations",[]); types=Counter(v.get("type","unknown") for v in violations); attributable=[v for v in violations if v.get("type") not in chg.ACCEPTED]
                lp=scratch.with_suffix(".ledger.json"); subprocess.run([sys.executable,str(LEDGER),"--board",str(scratch),str(lp)],check=True,stdout=subprocess.DEVNULL); ledger=json.loads(lp.read_text()); opens={r["net"]:r["open_edges"] for r in ledger["nets"] if r["net"] in (chg.NET,*WITHDRAWN)}
            after=copper(scratch); removed_final=baseline-after; added=after-baseline
            removed_by_net=Counter()
            for key,count in removed_final.items(): removed_by_net[key[0]]+=count
            wrong_removed=sum(count for key,count in removed_final.items() if key[0] not in WITHDRAWN)
            wrong_added=sum(count for key,count in added.items() if key[0] not in (chg.NET,*WITHDRAWN))
            ok=(complete and all(opens.get(n)==0 for n in (chg.NET,*WITHDRAWN)) and not attributable and not wrong_removed and not wrong_added)
            row={"case":idx,"reservations":reservations,"joins":joins,"replay":replay,"open_edges":opens,"drc_exit":drc_exit,"drc_types":dict(types),"attributable_drc_count":len(attributable),"attributable_drc":attributable,"removed_refloor_items":dict(removed_by_net),"removed_wrong_net_items":wrong_removed,"added_wrong_net_items":wrong_added,"promotion_candidate":ok,"path":scratch}; cases.append(row)
            if ok: winner=row; break
        if winner and args.candidate: args.candidate.write_bytes(winner["path"].read_bytes())
        if args.promote:
            if not winner or sha(BOARD)!=before: raise RuntimeError("refuse promotion: full atomic gate failed or authority changed")
            BOARD.write_bytes(winner["path"].read_bytes())
        for c in cases: c.pop("path",None)
    print(json.dumps({"schema":1,"authoritative_board_sha256":before,"authoritative_unchanged":sha(BOARD)==before,"withdrawn_complete_net_items":removed,"candidate_pairs_total":len(all_combos),"case_start":args.case_start,"case_stop":args.case_start+len(combos),"cases_tested":len(cases),"promotion_candidate":winner is not None,"cases":cases},indent=2,sort_keys=True))
    return 0 if winner else 2

if __name__=="__main__": raise SystemExit(main())
