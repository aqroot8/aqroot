#!/usr/bin/env python3
"""Independent Gerber/Excellon CAM extractor for the AQROOT Demo package.

Reads ONLY the released Gerber + Excellon files (no KiCad, no pcbnew), the way
a fab CAM station does, and reports:
  * open-ended conductor draws (an endpoint touching no other same-net copper)
  * same-layer conductor crossings (proper segment intersections), by net pair
  * different-net copper overlap (shorts) per layer
  * different-net copper gaps below a threshold (default 4 mil), per layer
  * drill-linked netlist: components spanning >1 net, nets split over >1 component
Usage: gcam.py GERBER_DIR [--gap-mil 4] [--json OUT]
"""
import argparse, json, math, re, sys
from collections import defaultdict
from pathlib import Path
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union
from shapely.strtree import STRtree
from shapely import affinity

LAYERS = ["F_Cu", "In1_Cu", "In2_Cu", "In3_Cu", "In4_Cu", "B_Cu"]
COORD = re.compile(r"(?:X(-?\d+))?(?:Y(-?\d+))?(?:I(-?\d+))?(?:J(-?\d+))?D0?([123])\*$")


def macro_eval(expr, params):
    e = expr
    for i in sorted(params, reverse=True):
        e = e.replace(f"${i}", repr(params[i]))
    return eval(e.replace("x", "*").replace("X", "*"), {"__builtins__": {}})


def macro_shape(body, params):
    shapes = []
    for prim in body:
        if prim.startswith("0 ") or not prim.strip():
            continue
        f = prim.split(",")
        code = int(f[0])
        v = [macro_eval(x, params) for x in f[1:]]
        if code == 1:
            shapes.append(Point(v[2], v[3]).buffer(v[1] / 2, 32))
        elif code == 4:
            n = int(v[1]); pts = [(v[2 + 2 * k], v[3 + 2 * k]) for k in range(n + 1)]
            shapes.append(affinity.rotate(Polygon(pts), v[-1], origin=(0, 0)))
        elif code == 20:
            ls = LineString([(v[2], v[3]), (v[4], v[5])])
            shapes.append(affinity.rotate(ls.buffer(v[1] / 2, cap_style=2), v[6], origin=(0, 0)))
        elif code == 21:
            shapes.append(affinity.rotate(box(v[3] - v[1] / 2, v[4] - v[2] / 2, v[3] + v[1] / 2, v[4] + v[2] / 2), v[5], origin=(0, 0)))
        else:
            raise SystemExit(f"unsupported macro primitive {code}")
    return unary_union(shapes)


def ap_shape(kind, mods, macros):
    if kind == "C":
        return Point(0, 0).buffer(mods[0] / 2, 32)
    if kind == "R":
        return box(-mods[0] / 2, -mods[1] / 2, mods[0] / 2, mods[1] / 2)
    if kind == "O":
        w, h = mods[0], mods[1]
        if w >= h:
            return LineString([(-(w - h) / 2, 0), ((w - h) / 2, 0)]).buffer(h / 2, 32) if w > h else Point(0, 0).buffer(h / 2, 32)
        return LineString([(0, -(h - w) / 2), (0, (h - w) / 2)]).buffer(w / 2, 32)
    if kind in macros:
        return macro_shape(macros[kind], {i + 1: m for i, m in enumerate(mods)})
    raise SystemExit(f"unsupported aperture {kind}")


def parse_gerber(path):
    txt = path.read_text()
    macros, aps, apfunc = {}, {}, {}
    draws, flashes, regions = [], [], []
    pend_func = None
    cur_ap = None; x = y = 0.0; net = None; comp = None; pin = None
    in_region = False; contour = []; contours = []
    for m in re.finditer(r"%AM([A-Za-z0-9_]+)\*(.*?)%", txt, re.S):
        macros[m.group(1)] = [p.strip().replace("\n", "") for p in m.group(2).split("*") if p.strip()]
    body = re.sub(r"%AM.*?%", "", txt, flags=re.S)
    for raw in body.splitlines():
        ln = raw.strip()
        if not ln or ln.startswith("G04"):
            continue
        if ln.startswith("%TA.AperFunction"):
            pend_func = ln[len("%TA.AperFunction,"):-2]; continue
        if ln.startswith("%TD"):
            if ln == "%TD*%":
                pend_func = None; net = comp = pin = None
            elif ln.startswith("%TD.AperFunction"):
                pend_func = None
            continue
        if ln.startswith("%ADD"):
            m = re.match(r"%ADD(\d+)([A-Za-z0-9_]+),?([^*]*)\*%", ln)
            mods = [float(v) for v in m.group(3).split("X") if v] if m.group(3) else []
            aps[int(m.group(1))] = ap_shape(m.group(2), mods, macros)
            apfunc[int(m.group(1))] = (pend_func or "", m.group(2), mods)
            continue
        if ln.startswith("%TO.N,"):
            net = ln[6:-2].split(",")[0]; continue
        if ln.startswith("%TO.C,"):
            comp = ln[6:-2]; continue
        if ln.startswith("%TO.P,"):
            pin = ln[6:-2]; continue
        if ln.startswith("%"):
            continue
        if ln == "G36*":
            in_region = True; contours = []; contour = []; continue
        if ln == "G37*":
            if len(contour) > 2: contours.append(contour)
            for c in contours:
                p = Polygon(c).buffer(0)
                regions.append(dict(geom=p, net=net, comp=comp))
            in_region = False; continue
        m = re.match(r"^D(\d{2,})\*$", ln)
        if m:
            cur_ap = int(m.group(1)); continue
        if ln.startswith("G01"):
            ln = ln[3:]
            if ln in ("", "*"): continue
        if ln in ("G75*", "G74*", "M02*"):
            continue
        m = COORD.match(ln)
        if not m:
            if ln.startswith("G0") and ln[3:] == "*":
                continue
            raise SystemExit(f"{path.name}: unparsed {ln!r}")
        nx = int(m.group(1)) / 1e6 if m.group(1) else x
        ny = int(m.group(2)) / 1e6 if m.group(2) else y
        d = m.group(5)
        if in_region:
            if d == "2":
                if len(contour) > 2: contours.append(contour)
                contour = [(nx, ny)]
            else:
                contour.append((nx, ny))
        elif d == "1":
            func, kind, mods = apfunc[cur_ap]
            draws.append(dict(a=(x, y), b=(nx, ny), w=mods[0] if kind == "C" else None,
                              ap=cur_ap, func=func, net=net, comp=comp))
        elif d == "3":
            g = affinity.translate(aps[cur_ap], nx, ny)
            flashes.append(dict(geom=g, at=(nx, ny), func=apfunc[cur_ap][0], net=net, comp=comp, pin=pin))
        x, y = nx, ny
    for dr in draws:
        ls = LineString([dr["a"], dr["b"]]) if dr["a"] != dr["b"] else Point(dr["a"])
        dr["geom"] = ls.buffer(dr["w"] / 2, 16)
    return dict(draws=draws, flashes=flashes, regions=regions)


def parse_drill(path):
    tools, hits, cur = {}, [], None
    for ln in path.read_text().splitlines():
        ln = ln.strip()
        m = re.match(r"^T(\d+)C([\d.]+)$", ln)
        if m: tools[int(m.group(1))] = float(m.group(2)); continue
        m = re.match(r"^T(\d+)$", ln)
        if m: cur = int(m.group(1)); continue
        m = re.match(r"^X(-?[\d.]+)Y(-?[\d.]+)(?:G85X(-?[\d.]+)Y(-?[\d.]+))?$", ln)
        if m:
            a = (float(m.group(1)), float(m.group(2)))
            b = (float(m.group(3)), float(m.group(4))) if m.group(3) else a
            hits.append(dict(a=a, b=b, d=tools[cur]))
    return hits


def nn(n):
    return n if n not in (None, "", "N/C") else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dir"); ap.add_argument("--gap-mil", type=float, default=4.0)
    ap.add_argument("--json"); ap.add_argument("--prefix", default="aqroot-Beta-v2-")
    a = ap.parse_args()
    D = Path(a.dir)
    out = dict(source=str(D), layers={}, gap_mil=a.gap_mil)
    layer_polys = {}
    layer_members = {}
    for L in LAYERS:
        g = parse_gerber(D / f"{a.prefix}{L}.gbr")
        items = []  # (geom, net, kind, ref)
        for i, dr in enumerate(g["draws"]): items.append((dr["geom"], nn(dr["net"]), "draw", i))
        for i, fl in enumerate(g["flashes"]): items.append((fl["geom"], nn(fl["net"]), "flash", i))
        for i, rg in enumerate(g["regions"]): items.append((rg["geom"], nn(rg["net"]), "region", i))
        geoms = [it[0] for it in items]
        tree = STRtree(geoms)
        rep = dict(draws=len(g["draws"]), flashes=len(g["flashes"]), regions=len(g["regions"]),
                   unnamed_draws=sum(1 for d in g["draws"] if nn(d["net"]) is None),
                   draw_funcs=sorted({d["func"] for d in g["draws"]}))
        # --- open-ended conductor draws
        opens = []
        for i, dr in enumerate(g["draws"]):
            for end in (dr["a"], dr["b"]):
                p = Point(end)
                touched = []
                for j in tree.query(p.buffer(1e-4)):
                    it = items[j]
                    if it[2] == "draw" and it[3] == i: continue
                    if it[0].distance(p) <= 1e-4:
                        touched.append(it)
                same = [t for t in touched if t[1] == nn(dr["net"])]
                if not same:
                    opens.append(dict(layer=L, at=end, kicad_xy=(end[0], -end[1]), net=dr["net"], w=dr["w"],
                                      other=dr["b"] if end == dr["a"] else dr["a"],
                                      touches_other_net=sorted({str(t[1]) for t in touched})))
        rep["open_ends"] = opens
        # --- same-layer conductor crossings
        segs = [LineString([d["a"], d["b"]]) if d["a"] != d["b"] else None for d in g["draws"]]
        idx = [k for k, s in enumerate(segs) if s is not None]
        st = STRtree([segs[k] for k in idx])
        crossings = defaultdict(list)
        for ii, k in enumerate(idx):
            for jj in st.query(segs[k]):
                kk = idx[jj]
                if kk <= k: continue
                s1, s2 = segs[k], segs[kk]
                if not s1.crosses(s2): continue
                ends = [Point(p) for p in (*s1.coords, *s2.coords)]
                ip = s1.intersection(s2)
                if any(e.distance(ip) < 1e-6 for e in ends): continue
                n1, n2 = nn(g["draws"][k]["net"]), nn(g["draws"][kk]["net"])
                crossings["same" if n1 == n2 else "diff"].append(
                    dict(at=(ip.x, ip.y) if ip.geom_type == "Point" else list(ip.coords)[0], nets=sorted({str(n1), str(n2)})))
        rep["crossings_same_net"] = crossings["same"]
        rep["crossings_diff_net"] = crossings["diff"]
        # --- per-net union, shorts and gaps
        bynet = defaultdict(list)
        unnamed = []
        for k, it in enumerate(items):
            (bynet[it[1]] if it[1] else unnamed).append(it[0])
        nets = {n: unary_union(v) for n, v in bynet.items()}
        for k, gm in enumerate(getattr(unary_union(unnamed), "geoms", [unary_union(unnamed)]) if unnamed else []):
            nets[f"<nonet#{k}>"] = gm
        names = list(nets)
        ntree = STRtree([nets[n] for n in names])
        shorts, gaps = [], []
        half = a.gap_mil * 0.0254 / 2
        for i, n in enumerate(names):
            for j in ntree.query(nets[n].buffer(half * 2.01)):
                if j <= i: continue
                m_ = names[j]
                inter = nets[n].intersection(nets[m_])
                if inter.area > 1e-9:
                    c = inter.centroid; shorts.append(dict(nets=[n, m_], area=inter.area, at=(c.x, c.y)))
                    continue
                dist = nets[n].distance(nets[m_])
                if dist < a.gap_mil * 0.0254:
                    from shapely.ops import nearest_points
                    p1, p2 = nearest_points(nets[n], nets[m_])
                    gaps.append(dict(nets=[n, m_], gap_mm=round(dist, 5), gap_mil=round(dist / 0.0254, 3),
                                     at=(round(p1.x, 4), round(p1.y, 4)), kicad_xy=(round(p1.x, 4), round(-p1.y, 4))))
        rep["shorts"] = shorts
        rep["gaps_below"] = sorted(gaps, key=lambda q: q["gap_mm"])
        rep["unnamed_items"] = len(unnamed)
        # polygons for netlist
        polys = []
        for n, gm in nets.items():
            for p in getattr(gm, "geoms", [gm]):
                polys.append((p, n))
        for p in unary_union(unnamed).geoms if unnamed and hasattr(unary_union(unnamed), "geoms") else ([unary_union(unnamed)] if unnamed else []):
            polys.append((p, None))
        ptree = STRtree([pp for pp, _ in polys])
        members = [dict(pads=set(), vias=0, draws=0, regions=0) for _ in polys]
        for fl in g["flashes"]:
            for k in ptree.query(fl["geom"].centroid):
                if polys[k][0].contains(fl["geom"].centroid):
                    if fl["func"].startswith("ViaPad"): members[k]["vias"] += 1
                    elif fl["comp"] or fl["pin"]: members[k]["pads"].add((fl["pin"] or fl["comp"]).split(",")[0] + "." + (fl["pin"].split(",")[1] if fl["pin"] and "," in fl["pin"] else "?"))
                    break
        for dr in g["draws"]:
            c = Point(dr["a"])
            for k in ptree.query(c):
                if polys[k][0].distance(c) < 1e-6: members[k]["draws"] += 1; break
        layer_polys[L] = polys
        layer_members[L] = members
        out["layers"][L] = rep
        print(f"{L}: draws={rep['draws']} flashes={rep['flashes']} regions={rep['regions']} "
              f"open_ends={len(opens)} cross_same={len(rep['crossings_same_net'])} cross_diff={len(rep['crossings_diff_net'])} "
              f"shorts={len(shorts)} gaps<{a.gap_mil}mil={len(gaps)} unnamed={len(unnamed)}", flush=True)
    # --- drill-linked netlist
    hits = parse_drill(D / f"{a.prefix}PTH.drl")
    parent = {}
    def f(x):
        while parent.setdefault(x, x) != x:
            parent[x] = parent[parent[x]]; x = parent[x]
        return x
    def u(x, y): parent[f(x)] = f(y)
    trees = {L: STRtree([p for p, _ in layer_polys[L]]) for L in LAYERS}
    for L in LAYERS:
        for k in range(len(layer_polys[L])): f((L, k))
    for h in hits:
        hole = LineString([h["a"], h["b"]]).buffer(h["d"] / 2) if h["a"] != h["b"] else Point(h["a"]).buffer(h["d"] / 2)
        hole = Point(h["a"][0], -h["a"][1]) if False else hole
        # drill coords are board coords with Y negated like the Gerbers (absolute origin)
        nodes = []
        for L in LAYERS:
            for k in trees[L].query(hole):
                if layer_polys[L][k][0].intersects(hole):
                    nodes.append((L, k))
        for n2 in nodes[1:]: u(nodes[0], n2)
    comp_nets = defaultdict(set); net_comps = defaultdict(set)
    for L in LAYERS:
        for k, (p, n) in enumerate(layer_polys[L]):
            r = f((L, k)); comp_nets[r].add(n)
            if n: net_comps[n].add(r)
    multi = [sorted(map(str, s)) for s in comp_nets.values() if len({x for x in s if x}) > 1]
    split = {n: len(c) for n, c in net_comps.items() if len(c) > 1 and not n.startswith("<nonet")}
    pieces = defaultdict(lambda: defaultdict(lambda: dict(pads=set(), vias=0, draws=0, layers=set(), bbox=None)))
    for L in LAYERS:
        for k, (p, n) in enumerate(layer_polys[L]):
            if not n or n not in split: continue
            r = f((L, k)); pc = pieces[n][r]; m = layer_members[L][k]
            pc["pads"] |= m["pads"]; pc["vias"] += m["vias"]; pc["draws"] += m["draws"]; pc["layers"].add(L)
            bb = p.bounds
            pc["bbox"] = bb if pc["bbox"] is None else (min(pc["bbox"][0], bb[0]), min(pc["bbox"][1], bb[1]), max(pc["bbox"][2], bb[2]), max(pc["bbox"][3], bb[3]))
    split_detail = {n: [dict(pads=sorted(pc["pads"]), vias=pc["vias"], draws=pc["draws"], layers=sorted(pc["layers"]),
                             kicad_bbox=[round(pc["bbox"][0], 3), round(-pc["bbox"][3], 3), round(pc["bbox"][2], 3), round(-pc["bbox"][1], 3)])
                        for pc in v.values()] for n, v in pieces.items()}
    for n, v in sorted(split_detail.items()):
        print(f"  PIECES {n}:")
        for pc in v: print(f"     pads={pc['pads']} vias={pc['vias']} draws={pc['draws']} layers={pc['layers']} bbox={pc['kicad_bbox']}")
    out["split_detail"] = split_detail
    out["netlist"] = dict(pth_hits=len(hits), components=len(comp_nets), multi_net_components=multi,
                          split_nets=split)
    print(f"netlist: PTH hits={len(hits)} components={len(comp_nets)} multi-net={len(multi)} split-nets={len(split)}")
    for n, c in sorted(split.items()): print(f"  split {n}: {c} pieces")
    if a.json:
        Path(a.json).write_text(json.dumps(out, indent=1, default=str))


if __name__ == "__main__":
    main()
