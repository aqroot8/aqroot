#!/usr/bin/env python3
"""Exhaustively screen package-local ordinary-via fanouts from R63.2."""
import hashlib, itertools, json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
BOARD=ROOT/"hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb"
NET="/09_COMMUNITY_HEADER/WAKE_GATE_S"; REF="R63.2"; W=C=200_000
sys.path.insert(0,str(ROOT/"hardware/beta-v2/checks"))
import incremental_router as ir, qrouter as qr

def emit(b,a,z):
    if any(qr.seg_shape_dist(*a,*z,s)<b.margin(s,W,C,C) for s in b.obstacles("B",NET)): return False
    b.track(NET,"B",*a,*z,W); return True

def main():
    before=hashlib.sha256(BOARD.read_bytes()).hexdigest(); seed=qr.QBoard(BOARD)
    p={x["ref"]:x for x in ir.physical_net_pads(seed,NET)}[REF]
    offsets=range(-3_000_000,3_000_001,250_000); tested=0; legal=[]
    b=qr.QBoard(BOARD); ir.inject_existing_via_obstacles(b)
    for dx,dy,axis in itertools.product(offsets,offsets,("x","y")):
        if not dx and not dy: continue
        via=(p["x"]+dx,p["y"]+dy)
        elbow=(via[0],p["y"]) if axis=="x" else (p["x"],via[1])
        pts=tuple(q for i,q in enumerate(((p["x"],p["y"]),elbow,via)) if not i or q!=((p["x"],p["y"]),elbow,via)[i-1])
        tested+=1; mark=b.mark()
        ok=(all(b.point_free(layer,NET,*via,600_000,C,C,25_000) for layer in b.cu)
            and all(emit(b,a,z) for a,z in zip(pts,pts[1:])))
        if ok: legal.append({"via_mm":[via[0]/1e6,via[1]/1e6],"axis":axis,"path_mm":[[x/1e6,y/1e6] for x,y in pts]})
        b.revert(mark)
    print(json.dumps({"schema":1,"authoritative_board_sha256":before,"authoritative_unchanged":hashlib.sha256(BOARD.read_bytes()).hexdigest()==before,"contract":{"net":NET,"pad":REF,"width_mm":.2,"clearance_mm":.2,"via_mm":[.6,.3]},"shapes_tested":tested,"legal_fanout_count":len(legal),"first_legal":legal[:8]},indent=2,sort_keys=True))
    return 0 if legal else 2
if __name__=="__main__": raise SystemExit(main())
