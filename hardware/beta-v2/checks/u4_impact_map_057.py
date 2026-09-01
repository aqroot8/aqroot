# -*- coding: utf-8 -*-
"""D-355: accepted-copper impact map for routing-capable D-354 U4 poses.

Scratch-only characterization.  Move U4 over the authoritative board, retain
all accepted copper, and identify the exact nearby copper and real KiCad DRC
items that bound a future transactional replacement.  The authoritative PCB
is never edited.
"""
import hashlib, json, math, os, shutil, subprocess, sys
import pcbnew

SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)
import incremental_router as IR
import path_role_util as RU

OUT = os.path.join(SP, "u4_impact_map_057.json")
SCRATCH = os.path.join(SP, "w", "U4_IMPACT_MAP_057")
SOURCE = os.path.join(SP, "u4_neighbor_eco_056.json")

def mm(v): return round(v / 1e6, 6)

def point_segment_distance(p, a, b):
    dx, dy = b.x-a.x, b.y-a.y
    if dx == 0 and dy == 0: return math.hypot(p.x-a.x, p.y-a.y)
    t = max(0.0, min(1.0, ((p.x-a.x)*dx+(p.y-a.y)*dy)/float(dx*dx+dy*dy)))
    return math.hypot(p.x-(a.x+t*dx), p.y-(a.y+t*dy))

def track_row(t):
    if t.GetClass() == "PCB_VIA":
        p = t.GetPosition()
        return {"kind":"via", "net":t.GetNetname(), "at_mm":[mm(p.x),mm(p.y)],
                "diameter_mm":mm(t.GetWidth(pcbnew.F_Cu))}
    return {"kind":"track", "net":t.GetNetname(), "layer":t.GetLayerName(),
            "start_mm":[mm(t.GetStart().x),mm(t.GetStart().y)],
            "end_mm":[mm(t.GetEnd().x),mm(t.GetEnd().y)], "width_mm":mm(t.GetWidth())}

def nearby_copper(board, fp, clearance=300000):
    rows = []
    for t in board.GetTracks():
        for p in fp.Pads():
            c = p.GetPosition(); radius = max(p.GetSize().x, p.GetSize().y)/2 + clearance
            if t.GetClass() == "PCB_VIA":
                hit = math.hypot(t.GetPosition().x-c.x, t.GetPosition().y-c.y) <= radius+t.GetWidth(pcbnew.F_Cu)/2
            else:
                hit = point_segment_distance(c, t.GetStart(), t.GetEnd()) <= radius+t.GetWidth()/2
            if hit:
                rows.append(track_row(t)); break
    return rows

def raw_drc(pcb, tag):
    out = os.path.join(SCRATCH, "drc_"+tag+".json")
    subprocess.run([RU.HP.kicad_cli(), "pcb", "drc", "--severity-all", "--format", "json", "-o", out, pcb],
                   check=True, capture_output=True, text=True)
    data = json.load(open(out, encoding="utf-8")); os.remove(out)
    rows = [{"type":v.get("type"), "description":v.get("description", ""),
             "items":sorted(i.get("description", "") for i in v.get("items", []))}
            for v in data.get("violations", [])]
    return sorted(rows, key=lambda r:(r["type"] or "", r["description"], r["items"]))

def main():
    os.makedirs(SCRATCH, exist_ok=True)
    source = json.load(open(SOURCE, encoding="utf-8"))
    candidates = [(r["rotation_deg"], r["offset_mm"]) for r in source["candidates"] if r["route"].get("ok")]
    auth_sha = hashlib.sha256(open(IR.AUTH, "rb").read()).hexdigest()
    base = pcbnew.LoadBoard(IR.AUTH); u0 = base.FindFootprintByReference("U4")
    origin, angle0 = u0.GetPosition(), u0.GetOrientationDegrees(); rows = []
    for angle, (dx, dy) in candidates:
        tag = "r%d_%+d_%+d" % (angle, round(dx*1000), round(dy*1000))
        pcb = os.path.join(SCRATCH, tag+".kicad_pcb"); shutil.copyfile(IR.AUTH, pcb)
        b = pcbnew.LoadBoard(pcb); u = b.FindFootprintByReference("U4")
        u.SetOrientationDegrees(angle0+angle)
        u.SetPosition(pcbnew.VECTOR2I(origin.x+round(dx*1e6), origin.y+round(dy*1e6)))
        b.Save(pcb)
        violations = raw_drc(pcb, tag)
        relevant = [v for v in violations if any("U4" in s for s in [v["description"]]+v["items"])]
        copper = nearby_copper(b, u)
        rows.append({"rotation_deg":angle, "offset_mm":[dx,dy],
                     "u4_drc_violations":relevant, "u4_drc_count":len(relevant),
                     "expanded_pad_envelope_copper":copper,
                     "impacted_nets":sorted(set(x["net"] for x in copper))})
        print(tag, "U4 DRC", len(relevant), "copper", len(copper), "nets", rows[-1]["impacted_nets"])
    best = min(rows, key=lambda r:(r["u4_drc_count"], len(r["expanded_pad_envelope_copper"]), r["rotation_deg"], r["offset_mm"]))
    ev = {"schema_version":1, "decision":"D-355", "source_decision":"D-354",
          "authoritative_board_sha256":auth_sha,
          "authoritative_unchanged":hashlib.sha256(open(IR.AUTH,"rb").read()).hexdigest()==auth_sha,
          "method":"real_DRC_plus_U4_pad_envelope_0.300mm_clearance",
          "routing_capable_candidates":rows, "least_impact_candidate":best,
          "conclusion":"impact_scope_mapped_for_bounded_U4_transactional_replay"}
    with open(OUT,"w",encoding="utf-8") as f: json.dump(ev,f,indent=2,sort_keys=True)
    print("RESULT", ev["conclusion"], "auth unchanged", ev["authoritative_unchanged"])

if __name__ == "__main__": main()
