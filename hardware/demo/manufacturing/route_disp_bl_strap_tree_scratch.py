#!/usr/bin/env python3
"""Atomically route/gate the display-backlight strap using the D-505 witness."""
import argparse, hashlib, json, subprocess, sys, tempfile
from collections import Counter
from pathlib import Path
import pcbnew

ROOT = Path(__file__).resolve().parents[3]
BOARD = ROOT / "hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb"
LOCAL = Path(__file__).with_name("route_local_two_pad.py")
LEDGER = Path(__file__).with_name("routing_ledger.py")
NET = "/02_MCU_CORE/DISP_BL_CTL_STRAP"
WIDTH = CLEARANCE = 200_000
ACCEPTED = {"lib_footprint_issues", "hole_clearance", "solder_mask_bridge"}
WITNESS = {
 "U1.16": (((45250000,122285000),(46500000,122285000),(46500000,122785000)),(46500000,122785000)),
 "TP2.1": (((42222198,117760499),(41472198,117760499),(41472198,117010499)),(41472198,117010499)),
 "R109.1": (((51779031,113910322),(52529031,113910322),(52529031,112910322)),(52529031,112910322)),
}
sys.path.insert(0, str(ROOT / "hardware/beta-v2/checks"))
import incremental_router as ir
import qrouter as qr

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def copper(p):
 out=Counter()
 for i in pcbnew.LoadBoard(str(p)).GetTracks():
  if i.GetClass()=="PCB_VIA":
   q=i.GetPosition(); k=(i.GetNetname(),"VIA",i.GetWidth(pcbnew.F_Cu),i.GetDrillValue(),q.x,q.y)
  else:
   e=sorted(((i.GetStart().x,i.GetStart().y),(i.GetEnd().x,i.GetEnd().y)))
   k=(i.GetNetname(),i.GetLayerName(),i.GetWidth(),*e)
  out[k]+=1
 return out
def emit(b,a,z,layer):
 if any(qr.seg_shape_dist(*a,*z,s)<b.margin(s,WIDTH,CLEARANCE,CLEARANCE) for s in b.obstacles(layer,NET)): return False
 b.track(NET,layer,*a,*z,WIDTH); return True
def place(b,path,via):
 if not all(b.point_free(layer,NET,*via,600000,CLEARANCE,CLEARANCE,25000) for layer in b.cu): return False
 if not all(emit(b,a,z,"F") for a,z in zip(path,path[1:])): return False
 b.via(NET,*via,600000,300000); return True
def join(b,a,z,layer):
 direct=qr.join_reserved(b,NET,a,z,WIDTH,CLEARANCE,CLEARANCE,layer=layer)
 if direct.get("ok"): return {**direct,"family":"direct"}
 paths=[(a,(a[0],z[1]),z),(a,(z[0],a[1]),z)]
 x0,x1=sorted((a[0],z[0])); y0,y1=sorted((a[1],z[1]))
 for x in range(x0-2000000,x1+2000001,250000): paths.append((a,(x,a[1]),(x,z[1]),z))
 for y in range(y0-2000000,y1+2000001,250000): paths.append((a,(a[0],y),(z[0],y),z))
 for tested,path in enumerate(paths,1):
  mark=b.mark()
  if all(emit(b,p,q,layer) for p,q in zip(path,path[1:])):
   return {"ok":True,"family":"local_dogleg","tested":tested,
           "waypoints_mm":[[x/1e6,y/1e6] for x,y in path[1:-1]]}
  b.revert(mark)
 return {"ok":False,"reason":"NO_LOCAL_DOGLEG","tested":len(paths)}
def run_case(work,base,layers):
 s=work/f"disp-bl-strap-{layers[0]}-{layers[1]}.kicad_pcb"
 for x in (".kicad_pcb",".kicad_dru",".kicad_pro"): s.with_suffix(x).write_bytes(BOARD.with_suffix(x).read_bytes())
 b=qr.QBoard(s); ir.inject_existing_via_obstacles(b)
 pads={p["ref"] for p in ir.physical_net_pads(b,NET)}
 if pads!={"U1.16","TP2.1","R108.1","R109.1"}: raise RuntimeError(f"unexpected fitted pads: {sorted(pads)}")
 fans={r:place(b,*WITNESS[r]) for r in WITNESS}; joins={}
 first=f"U1_TP2_{layers[0]}"; second=f"TP2_R109_{layers[1]}"
 if all(fans.values()): joins[first]=join(b,WITNESS["U1.16"][1],WITNESS["TP2.1"][1],layers[0])
 if joins.get(first,{}).get("ok"): joins[second]=join(b,WITNESS["TP2.1"][1],WITNESS["R109.1"][1],layers[1])
 result={"fanouts":fans,"joins":joins,"replay":{"ok":False,"reason":"NOT_ATTEMPTED"},"promotion_candidate":False,"path":s}
 if not joins.get(second,{}).get("ok"): return result
 b.save(s)
 rr=subprocess.run([sys.executable,str(LOCAL),"DISP_BL_STRAP_U1_R108","--route",str(s)],text=True,capture_output=True,check=True)
 result["replay"]=json.loads(rr.stdout)["result"]
 if not result["replay"].get("ok"): return result
 d=s.with_suffix(".drc.json")
 subprocess.run(["kicad-cli","pcb","drc","--refill-zones","--save-board","--format","json","--units","mm","--severity-all","--schematic-parity","-o",str(d),str(s)],check=True,text=True,capture_output=True)
 types=Counter(v.get("type","unknown") for v in json.loads(d.read_text()).get("violations",[]))
 lp=s.with_suffix(".ledger.json"); subprocess.run([sys.executable,str(LEDGER),"--board",str(s),str(lp)],check=True,stdout=subprocess.DEVNULL)
 led=json.loads(lp.read_text()); target=next(n for n in led["nets"] if n["net"]==NET)
 after=copper(s); removed,added=base-after,after-base; attr=sum(n for t,n in types.items() if t not in ACCEPTED)
 result.update({"drc_types":dict(types),"attributable_drc_count":attr,"target_open_edges":target["open_edges"],"connectivity":led["connectivity"],"removed_accepted_copper_items":sum(removed.values()),"added_items":sum(added.values()),"wrong_net_additions":sum(n for k,n in added.items() if k[0]!=NET),"candidate_sha256":sha(s)})
 result["promotion_candidate"]=not attr and not removed and not result["wrong_net_additions"] and target["open_edges"]==0
 return result
def main():
 ap=argparse.ArgumentParser(); ap.add_argument("--candidate",type=Path); ap.add_argument("--promote",action="store_true"); a=ap.parse_args()
 before,base=sha(BOARD),copper(BOARD)
 with tempfile.TemporaryDirectory(prefix="aqroot-demo-disp-bl-strap-") as td:
  cases=[run_case(Path(td),base,layers) for layers in (("I2","I3"),("I3","I2"))]
  winners=[c for c in cases if c["promotion_candidate"]]; c=winners[0] if winners else cases[-1]
  if winners and a.candidate: a.candidate.write_bytes(c["path"].read_bytes())
  if a.promote:
   if not winners or sha(BOARD)!=before: raise RuntimeError("refuse promotion: gate failed or authority changed")
   BOARD.write_bytes(c["path"].read_bytes())
  for row in cases: row.pop("path",None)
 print(json.dumps({"schema":2,"authoritative_board_sha256":before,"authoritative_unchanged":sha(BOARD)==before,"cases":cases,"promotion_candidates":len(winners)},indent=2,sort_keys=True))
 return 0 if winners else 2
if __name__=="__main__": raise SystemExit(main())
