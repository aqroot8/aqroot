"""D-657: can the SYS_MAIN contract route U11.1 -> C27.1 (and other SYS pairs)?
Same primitive the gate uses: maze3d.offcentre_route through maze3d.Field at the
net's own contract.  Laid, measured, REVERTED; the board is never written."""
import hashlib, json, sys, time
from pathlib import Path
HERE=Path("/home/aqroot8/aqroot-demo/hardware/demo/manufacturing"); ROOT=HERE.parents[2]
sys.path.insert(0,str(HERE)); sys.path.insert(0,str(ROOT/"hardware/beta-v2/checks"))
BOARD=ROOT/"hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb"
NET="/01_POWER_TREE/BQ25185_SYS"
GRID=int(sys.argv[1]); WIDTH=int(sys.argv[2]); OUT=Path(sys.argv[3]); PAIRS=[p.split("-") for p in sys.argv[4:]]
import qrouter as qr, incremental_router as ir, maze3d as mz
from route_maze_batch import net_contract, permitted_layers, reserved_inner_planes
sha=hashlib.sha256(BOARD.read_bytes()).hexdigest()
qb=qr.QBoard(str(BOARD)); ir.inject_existing_via_obstacles(qb)
reserved=reserved_inner_planes(qb.b); c=net_contract(qb.b,NET)
layers=list(permitted_layers(qb.routable,c["layers"],reserved,NET))
islands=mz.net_islands(qb,NET); pads={p["ref"]:p for isl in islands for p in isl}
field=mz.Field(qb,NET,WIDTH,c["clr_pad"],c["clr"],c["via_dia"],c["via_drill"],
               G=GRID,layers=layers)
rows=[]
for a,b in PAIRS:
    t0=time.time(); m=qb.mark()
    try:
        r=mz.offcentre_route(qb,field,pads[a],pads[b],G=GRID)
    finally:
        qb.revert(m)
    rec=dict(pair="%s->%s"%(a,b),seconds=round(time.time()-t0,1),
             ok=bool(r and r.get("ok")),result=r if isinstance(r,dict) else str(r))
    rows.append(rec)
    print("  %-18s ok=%-5s %s  %.0fs"%(rec["pair"],rec["ok"],
          json.dumps({k:v for k,v in (r or {}).items() if k in
          ("mm","vias","layers","reason","why")})[:220],time.time()-t0),
          file=sys.stderr,flush=True)
OUT.write_text(json.dumps(dict(schema=1,decision="D-657",board=str(BOARD),
    board_sha256=sha,net=NET,grid=GRID,layers=layers,
    contract=dict(width=WIDTH,netclass_width=c["width"],clr=c["clr"],via_dia=c["via_dia"],via_drill=c["via_drill"]),
    authoritative_unchanged=hashlib.sha256(BOARD.read_bytes()).hexdigest()==sha,
    pairs=rows),indent=1,sort_keys=True))
