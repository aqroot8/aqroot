# -*- coding: utf-8 -*-
"""D-360: complete U3 incident-branch and local-neighbor impact map.

Scratch-only characterization over the authoritative board.  For every U3
incident net, record the complete connected copper component and its stable
non-U3 pad anchors.  Then pose U3 at every D-359 orthogonal candidate and map
real DRC, nearby accepted copper, and neighboring footprint envelopes.  The
authoritative PCB is never edited.
"""
import hashlib, json, math, os, shutil, subprocess, sys
import pcbnew

SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)
import incremental_router as IR
import path_role_util as RU

OUT = os.path.join(SP, "u3_impact_map_062.json")
SCRATCH = os.path.join(SP, "w", "U3_IMPACT_MAP_062")
CANDIDATES = [(a, dx, dy) for a in (90, 180, 270)
              for dx, dy in ((0, 0), (-.5, 0), (.5, 0), (0, -.5), (0, .5))]

def mm(v): return round(v / 1e6, 6)

def pad_ref(p):
    return p.GetParentFootprint().GetReference() + "." + p.GetNumber()

def point_segment_distance(p, a, b):
    dx, dy = b.x-a.x, b.y-a.y
    if dx == 0 and dy == 0: return math.hypot(p.x-a.x, p.y-a.y)
    t = max(0.0, min(1.0, ((p.x-a.x)*dx+(p.y-a.y)*dy)/float(dx*dx+dy*dy)))
    return math.hypot(p.x-(a.x+t*dx), p.y-(a.y+t*dy))

def item_row(x):
    if isinstance(x, pcbnew.PCB_VIA):
        p = x.GetPosition()
        return {"kind":"via", "net":x.GetNetname(), "at_mm":[mm(p.x),mm(p.y)],
                "diameter_mm":mm(x.GetWidth(pcbnew.F_Cu)),
                "drill_mm":mm(x.GetDrillValue())}
    return {"kind":"track", "net":x.GetNetname(), "layer":x.GetLayerName(),
            "start_mm":[mm(x.GetStart().x),mm(x.GetStart().y)],
            "end_mm":[mm(x.GetEnd().x),mm(x.GetEnd().y)],
            "width_mm":mm(x.GetWidth())}

def incident_branches(board):
    board.BuildConnectivity(); cc = board.GetConnectivity()
    u3 = board.FindFootprintByReference("U3"); rows = []
    for p in sorted(u3.Pads(), key=lambda q:(q.GetNetname(), q.GetNumber())):
        if not p.GetNetname(): continue
        connected = list(cc.GetConnectedItems(p))
        pads = sorted({pad_ref(x) for x in connected if x.GetClass() == "PAD"})
        copper = [item_row(x) for x in connected if isinstance(x, pcbnew.PCB_TRACK)]
        rows.append({"net":p.GetNetname(), "u3_pad":"U3."+p.GetNumber(),
                     "stable_pad_anchors":[x for x in pads if not x.startswith("U3.")],
                     "component_pad_count":len(pads), "component_copper_count":len(copper),
                     "component_copper":sorted(copper, key=lambda x:json.dumps(x,sort_keys=True))})
    return rows

def nearby_copper(board, fp, clearance=300000):
    rows = []
    for t in board.GetTracks():
        for p in fp.Pads():
            c = p.GetPosition(); radius = max(p.GetSize().x,p.GetSize().y)/2 + clearance
            if isinstance(t, pcbnew.PCB_VIA):
                hit = math.hypot(t.GetPosition().x-c.x,t.GetPosition().y-c.y) <= radius+t.GetWidth(pcbnew.F_Cu)/2
            else:
                hit = point_segment_distance(c,t.GetStart(),t.GetEnd()) <= radius+t.GetWidth()/2
            if hit: rows.append(item_row(t)); break
    return rows

def bbox_gap(a, b):
    ax0, ay0, ax1, ay1 = a.GetX(), a.GetY(), a.GetRight(), a.GetBottom()
    bx0, by0, bx1, by1 = b.GetX(), b.GetY(), b.GetRight(), b.GetBottom()
    dx = max(bx0-ax1, ax0-bx1, 0); dy = max(by0-ay1, ay0-by1, 0)
    return math.hypot(dx, dy)

def neighbor_envelopes(board, u3, radius=300000):
    ub = u3.GetBoundingBox(); rows = []
    for f in board.GetFootprints():
        if f == u3: continue
        gap = bbox_gap(ub, f.GetBoundingBox())
        if gap <= radius:
            rows.append({"ref":f.GetReference(), "gap_mm":mm(gap),
                         "position_mm":[mm(f.GetPosition().x),mm(f.GetPosition().y)]})
    return sorted(rows, key=lambda x:(x["gap_mm"],x["ref"]))

def raw_drc(pcb, tag):
    out = os.path.join(SCRATCH, "drc_"+tag+".json")
    subprocess.run([RU.HP.kicad_cli(),"pcb","drc","--severity-all","--format","json","-o",out,pcb],
                   check=True,capture_output=True,text=True)
    data=json.load(open(out,encoding="utf-8")); os.remove(out)
    rows=[{"type":v.get("type"),"description":v.get("description",""),
           "items":sorted(i.get("description","") for i in v.get("items",[]))}
          for v in data.get("violations",[])]
    return sorted(rows,key=lambda x:(x["type"] or "",x["description"],x["items"]))

def main():
    os.makedirs(SCRATCH,exist_ok=True)
    auth_sha=hashlib.sha256(open(IR.AUTH,"rb").read()).hexdigest()
    base=pcbnew.LoadBoard(IR.AUTH); u0=base.FindFootprintByReference("U3")
    origin=u0.GetPosition(); angle0=u0.GetOrientationDegrees()
    branches=incident_branches(base); rows=[]
    for angle,dx,dy in CANDIDATES:
        tag="r%d_%+d_%+d"%(angle,round(dx*1000),round(dy*1000))
        pcb=os.path.join(SCRATCH,tag+".kicad_pcb"); shutil.copyfile(IR.AUTH,pcb)
        b=pcbnew.LoadBoard(pcb); u=b.FindFootprintByReference("U3")
        u.SetOrientationDegrees(angle0+angle)
        u.SetPosition(pcbnew.VECTOR2I(origin.x+round(dx*1e6),origin.y+round(dy*1e6))); b.Save(pcb)
        violations=raw_drc(pcb,tag)
        relevant=[v for v in violations if any("U3" in s for s in [v["description"]]+v["items"])]
        copper=nearby_copper(b,u); neighbors=neighbor_envelopes(b,u)
        rows.append({"rotation_deg":angle,"offset_mm":[dx,dy],
                     "u3_drc_count":len(relevant),"u3_drc_violations":relevant,
                     "expanded_pad_envelope_copper":copper,
                     "impacted_nets":sorted({x["net"] for x in copper}),
                     "neighbor_footprint_envelopes_0p300mm":neighbors})
        print(tag,"drc",len(relevant),"copper",len(copper),"neighbors",[x["ref"] for x in neighbors])
    best=min(rows,key=lambda x:(len(x["neighbor_footprint_envelopes_0p300mm"]),x["u3_drc_count"],
                                len(x["expanded_pad_envelope_copper"]),x["rotation_deg"],x["offset_mm"]))
    ev={"schema_version":1,"decision":"D-360","source_decision":"D-359",
        "authoritative_board_sha256":auth_sha,
        "authoritative_unchanged":hashlib.sha256(open(IR.AUTH,"rb").read()).hexdigest()==auth_sha,
        "method":"complete_connectivity_components_plus_real_DRC_plus_0.300mm_U3_pad_and_footprint_envelopes",
        "incident_branches":branches,"incident_net_count":len(branches),
        "routed_incident_branch_count":sum(x["component_copper_count"] > 0 for x in branches),
        "incident_copper_count":sum(x["component_copper_count"] for x in branches),
        "candidates":rows,"least_impact_pose":best,
        "conclusion":"complete_U3_branch_and_neighbor_transaction_boundary_mapped"}
    with open(OUT,"w",encoding="utf-8") as f: json.dump(ev,f,indent=2,sort_keys=True)
    print("RESULT",ev["conclusion"],"auth unchanged",ev["authoritative_unchanged"])

if __name__ == "__main__": main()
