#!/usr/bin/env python3
"""Co-search qualified fanouts and atomically gate the display-backlight strap."""
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
REFS = ("U1.16", "TP2.1", "R109.1")
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
def compact(points): return tuple(p for n,p in enumerate(points) if not n or p != points[n-1])
def candidates(pad):
 px,py=pad["x"],pad["y"]; out=[]
 for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
  for reach in range(750000,2250001,250000):
   shoulder=(px+dx*reach,py+dy*reach)
   for offset in range(-1000000,1000001,250000):
    via=(shoulder[0],shoulder[1]+offset) if dx else (shoulder[0]+offset,shoulder[1])
    out.append((compact(((px,py),shoulder,via)),via))
 return out
def place(b,path,via):
 if not all(b.point_free(layer,NET,*via,600000,CLEARANCE,CLEARANCE,25000) for layer in b.cu): return False
 if not all(emit(b,a,z,"F") for a,z in zip(path,path[1:])): return False
 b.via(NET,*via,600000,300000); return True
def join(b,a,z,layer):
 mark=b.mark()
 if emit(b,a,z,layer): return {"ok":True,"family":"direct","tested":1}
 b.revert(mark)
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
def qualify(seed,pads):
 out={}
 for ref in REFS:
  rows=[]
  for row in candidates(pads[ref]):
   mark=seed.mark()
   if place(seed,*row): rows.append(row)
   seed.revert(mark)
  out[ref]=rows
 return out
def search(pads,qualified,layers,pair_start=0,max_pairs=None):
 b=qr.QBoard(BOARD); ir.inject_existing_via_obstacles(b)
 stats={"endpoint_pairs_tested":0,"first_joins":0,"third_fanouts_tested":0,
        "coherent_triples":0,"second_joins":0,"pair_start":pair_start,
        "pair_stop":None,"search_complete":False}
 # The first join depends only on the U1/TP2 pair.  Keep it placed while
 # screening every R109 fanout instead of recomputing it eleven times.
 pair_index=0
 for u1 in qualified[REFS[0]]:
  for tp2 in qualified[REFS[1]]:
   if pair_index < pair_start:
    pair_index+=1; continue
   if max_pairs is not None and stats["endpoint_pairs_tested"] >= max_pairs:
    stats["pair_stop"]=pair_index
    return None,stats
   pair_index+=1
   stats["endpoint_pairs_tested"]+=1; pair_mark=b.mark()
   if not place(b,*u1) or not place(b,*tp2): b.revert(pair_mark); continue
   first=join(b,u1[1],tp2[1],layers[0])
   if not first.get("ok"): b.revert(pair_mark); continue
   stats["first_joins"]+=1
   for r109 in qualified[REFS[2]]:
    stats["third_fanouts_tested"]+=1; branch_mark=b.mark()
    if not place(b,*r109): b.revert(branch_mark); continue
    stats["coherent_triples"]+=1
    second=join(b,tp2[1],r109[1],layers[1])
    if second.get("ok"):
     stats["second_joins"]+=1
     stats["pair_stop"]=pair_index
     return {"rows":(u1,tp2,r109),"first":first,"second":second},stats
    b.revert(branch_mark)
   b.revert(pair_mark)
 stats["pair_stop"]=pair_index; stats["search_complete"]=True
 return None,stats
def run_case(work,base,layers,pads,qualified,pair_start,max_pairs):
 s=work/f"disp-bl-strap-{layers[0]}-{layers[1]}.kicad_pcb"
 for x in (".kicad_pcb",".kicad_dru",".kicad_pro"): s.with_suffix(x).write_bytes(BOARD.with_suffix(x).read_bytes())
 witness,stats=search(pads,qualified,layers,pair_start,max_pairs)
 result={"layers":layers,"search":stats,"promotion_candidate":False,"path":s,
         "replay":{"ok":False,"reason":"NOT_ATTEMPTED"}}
 if witness is None: return result
 b=qr.QBoard(s); ir.inject_existing_via_obstacles(b)
 fans={r:place(b,*row) for r,row in zip(REFS,witness["rows"])}; joins={}
 first=f"U1_TP2_{layers[0]}"; second=f"TP2_R109_{layers[1]}"
 if all(fans.values()): joins[first]=join(b,witness["rows"][0][1],witness["rows"][1][1],layers[0])
 if joins.get(first,{}).get("ok"): joins[second]=join(b,witness["rows"][1][1],witness["rows"][2][1],layers[1])
 result.update({"fanouts":fans,"joins":joins,"witness":{
  r:{"via_mm":[row[1][0]/1e6,row[1][1]/1e6]} for r,row in zip(REFS,witness["rows"])}})
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
 ap=argparse.ArgumentParser(); ap.add_argument("--candidate",type=Path); ap.add_argument("--promote",action="store_true")
 ap.add_argument("--pair-start",type=int,default=0); ap.add_argument("--max-pairs",type=int)
 ap.add_argument("--layers",choices=("I2-I3","I3-I2","both"),default="both"); a=ap.parse_args()
 if a.pair_start < 0 or (a.max_pairs is not None and a.max_pairs < 1): ap.error("pair bounds must be positive")
 before,base=sha(BOARD),copper(BOARD)
 with tempfile.TemporaryDirectory(prefix="aqroot-demo-disp-bl-strap-") as td:
  seed=qr.QBoard(BOARD); ir.inject_existing_via_obstacles(seed)
  physical={p["ref"]:p for p in ir.physical_net_pads(seed,NET)}
  if set(physical)!={"U1.16","TP2.1","R108.1","R109.1"}: raise RuntimeError(f"unexpected fitted pads: {sorted(physical)}")
  qualified=qualify(seed,physical)
  assignments=(("I2","I3"),("I3","I2")) if a.layers=="both" else (tuple(a.layers.split("-")),)
  cases=[run_case(Path(td),base,layers,physical,qualified,a.pair_start,a.max_pairs) for layers in assignments]
  winners=[c for c in cases if c["promotion_candidate"]]; c=winners[0] if winners else cases[-1]
  if winners and a.candidate: a.candidate.write_bytes(c["path"].read_bytes())
  if a.promote:
   if a.pair_start or a.max_pairs is not None or a.layers != "both": raise RuntimeError("refuse promotion from bounded search")
   if not winners or sha(BOARD)!=before: raise RuntimeError("refuse promotion: gate failed or authority changed")
   BOARD.write_bytes(c["path"].read_bytes())
  for row in cases: row.pop("path",None)
 print(json.dumps({"schema":3,"authoritative_board_sha256":before,"authoritative_unchanged":sha(BOARD)==before,
  "qualified_fanouts":{r:len(v) for r,v in qualified.items()},"cases":cases,"promotion_candidates":len(winners)},indent=2,sort_keys=True))
 return 0 if winners else 2
if __name__=="__main__": raise SystemExit(main())
