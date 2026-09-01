# -*- coding: utf-8 -*-
"""D-349: geometric accepted-copper impact map for the six D-347 U20 wins.

This is scratch-only characterization.  It rotates/translates U20 over the
unchanged authoritative copper, records real KiCad DRC descriptions, and maps
every copper item whose geometry enters the moved footprint's expanded pad
envelope.  No routing or authoritative-board mutation is performed.
"""
import hashlib, json, math, os, shutil, subprocess, sys
import pcbnew

SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)
import incremental_router as IR
import path_role_util as RU

OUT = os.path.join(SP, "u20_impact_map_051.json")
SCRATCH = os.path.join(SP, "w", "U20_IMPACT_MAP_051")
CANDIDATES = ((90, 0, 0), (90, 0, .5), (180, 0, 0),
              (180, .5, 0), (180, 0, .5), (180, 1, 0))

def mm(v): return round(v / 1e6, 6)

def point_segment_distance(p, a, b):
    px, py = p.x, p.y; ax, ay = a.x, a.y; bx, by = b.x, b.y
    dx, dy = bx-ax, by-ay
    if dx == 0 and dy == 0: return math.hypot(px-ax, py-ay)
    t = max(0.0, min(1.0, ((px-ax)*dx+(py-ay)*dy)/float(dx*dx+dy*dy)))
    return math.hypot(px-(ax+t*dx), py-(ay+t*dy))

def track_row(t):
    if t.GetClass() == "PCB_VIA":
        p = t.GetPosition()
        return {"kind":"via", "net":t.GetNetname(), "at_mm":[mm(p.x),mm(p.y)],
                "diameter_mm":mm(t.GetWidth(pcbnew.F_Cu))}
    a, b = t.GetStart(), t.GetEnd()
    return {"kind":"track", "net":t.GetNetname(), "layer":t.GetLayerName(),
            "start_mm":[mm(a.x),mm(a.y)], "end_mm":[mm(b.x),mm(b.y)],
            "width_mm":mm(t.GetWidth())}

def raw_drc(pcb, tag):
    out = os.path.join(SCRATCH, "drc_%s.json" % tag)
    subprocess.run([RU.HP.kicad_cli(), "pcb", "drc", "--severity-all", "--format", "json",
                    "-o", out, pcb], check=True, capture_output=True, text=True)
    data = json.load(open(out, encoding="utf-8")); os.remove(out)
    return [{"type":v.get("type"), "description":v.get("description", ""),
             "items":[i.get("description", "") for i in v.get("items", [])]}
            for v in data.get("violations", [])]

def nearby_copper(board, u20, clearance=300000):
    pads = list(u20.Pads()); rows = []
    for t in board.GetTracks():
        hit = False
        for p in pads:
            c = p.GetPosition(); radius = max(p.GetSize().x, p.GetSize().y)/2 + clearance
            if t.GetClass() == "PCB_VIA":
                hit = math.hypot(t.GetPosition().x-c.x, t.GetPosition().y-c.y) <= radius+t.GetWidth(pcbnew.F_Cu)/2
            else:
                hit = point_segment_distance(c, t.GetStart(), t.GetEnd()) <= radius+t.GetWidth()/2
            if hit: break
        if hit: rows.append(track_row(t))
    return rows

def main():
    os.makedirs(SCRATCH, exist_ok=True)
    auth_sha = hashlib.sha256(open(IR.AUTH, "rb").read()).hexdigest()
    base = pcbnew.LoadBoard(IR.AUTH); u0 = base.FindFootprintByReference("U20")
    origin = u0.GetPosition(); angle0 = u0.GetOrientationDegrees(); rows = []
    for angle, dx, dy in CANDIDATES:
        tag = "r%d_%+d_%+d" % (angle, round(dx*1000), round(dy*1000))
        pcb = os.path.join(SCRATCH, tag+".kicad_pcb"); shutil.copyfile(IR.AUTH, pcb)
        b = pcbnew.LoadBoard(pcb); u = b.FindFootprintByReference("U20")
        u.SetOrientationDegrees(angle0+angle)
        u.SetPosition(pcbnew.VECTOR2I(origin.x+round(dx*1e6), origin.y+round(dy*1e6)))
        b.Save(pcb)
        violations = raw_drc(pcb, tag)
        relevant = [v for v in violations if any("U20" in s for s in [v["description"]]+v["items"])]
        copper = nearby_copper(b, u)
        rows.append({"rotation_deg":angle, "offset_mm":[dx,dy],
                     "u20_drc_violations":relevant, "u20_drc_count":len(relevant),
                     "expanded_pad_envelope_copper":copper,
                     "impacted_nets":sorted(set(x["net"] for x in copper))})
        print(tag, "U20 DRC", len(relevant), "copper", len(copper),
              "nets", rows[-1]["impacted_nets"])
    best = min(rows, key=lambda r:(r["u20_drc_count"], len(r["expanded_pad_envelope_copper"])))
    result = {"schema_version":1, "decision":"D-349", "authoritative_board_sha256":auth_sha,
              "authoritative_unchanged":hashlib.sha256(open(IR.AUTH,"rb").read()).hexdigest()==auth_sha,
              "method":"real_DRC_plus_U20_pad_envelope_0.300mm_clearance",
              "candidates":rows, "least_impact_candidate":best,
              "conclusion":"impact_scope_mapped_for_bounded_control_copper_replacement"}
    with open(OUT,"w",encoding="utf-8") as f: json.dump(result,f,indent=2,sort_keys=True)
    print("RESULT", result["conclusion"], "auth unchanged", result["authoritative_unchanged"])

if __name__ == "__main__": sys.exit(main())
