#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""READ-ONLY -- D-663: CAN THE U11 POCKET HOLD BOTH?

The D-659/D-663 three-object cut frees `BQ25185_SYS`'s `B.Cu` pour to bond
`U11.1`.  Every transaction that spends it must then give `U11.10`
(`USB_VBUS_CHG`) a new escape.  This probe asks the geometric question that
decides whether any such transaction can exist: lay ONE straight `B.Cu`
conductor from `U11.10`'s land to a point on the pocket boundary, refill with
KiCad's own filler, and ask whether `U11.1` is still in `U12.1`'s cluster.

Idealised on purpose: no via, no DRC, no lattice -- the narrowest width the
`.kicad_dru` courtyard neck grants (0.200 mm) and a straight line.  A wall here
is a wall for every real route, because every real route is at least this.
Nothing is written; the authority is opened, copied and re-checked.
"""
import hashlib, json, math, os, shutil, sys, tempfile
import pcbnew

SRC = "/home/aqroot8/aqroot-demo/hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb"
CUT = [("T", "/01_POWER_TREE/USB_VBUS_CHG", (66800000, 79446400), (68800000, 78946400)),
       ("T", "/01_POWER_TREE/ISET",         (70200000, 81100000), (70900000, 79400000)),
       ("V", "/01_POWER_TREE/USB_VBUS_CHG", (66800000, 79446400), None)]
PAD = (68600000, 78600000)          # U11.10
WIDTHS = (200000, 350000)


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def boundary():
    out = []
    x = 66.4
    while x <= 71.2001:
        out.append((x, 76.4)); out.append((x, 81.6))
        x += 0.4
    y = 76.4
    while y <= 81.6001:
        out.append((66.4, y)); out.append((71.2, y))
        y += 0.4
    return sorted(set(round(a, 3) for a in ()) or out)


def clusters_of(board, net):
    board.BuildConnectivity()
    conn = board.GetConnectivity()
    pads = [p for f in board.GetFootprints() for p in f.Pads()
            if p.GetNetname() == net and p.GetNumber()]

    def pid(p):
        q = p.GetPosition()
        return (p.GetParentFootprint().GetReference(), p.GetNumber(), q.x, q.y)

    ids = {pid(p): p for p in pads}
    parent = {k: k for k in ids}

    def find(k):
        while parent[k] != k:
            parent[k] = parent[parent[k]]
            k = parent[k]
        return k

    for p in pads:
        a = pid(p)
        for it in conn.GetConnectedItems(p):
            if it.GetClass() == "PAD" and pid(it) in ids:
                ra, rb = find(a), find(pid(it))
                if ra != rb:
                    parent[ra] = rb
    groups = {}
    for k in ids:
        groups.setdefault(find(k), []).append("%s.%s" % (k[0], k[1]))
    return sorted(sorted(v) for v in groups.values())


def main():
    src_sha = sha(SRC)
    tmp = tempfile.mkdtemp(prefix="d663coexist-")
    for ext in ("kicad_pcb", "kicad_pro", "kicad_dru"):
        shutil.copy(SRC.replace("kicad_pcb", ext), os.path.join(tmp, "base." + ext))
    base = os.path.join(tmp, "base.kicad_pcb")
    b = pcbnew.LoadBoard(base)
    doomed = []
    for t in b.GetTracks():
        n = t.GetNetname()
        if t.GetClass() == "PCB_VIA":
            q = t.GetPosition()
            for k, net, a, _ in CUT:
                if k == "V" and net == n and (q.x, q.y) == a:
                    doomed.append(t)
        else:
            s, e = t.GetStart(), t.GetEnd()
            for k, net, a, z in CUT:
                if k == "T" and net == n and {(s.x, s.y), (e.x, e.y)} == {a, z}:
                    doomed.append(t)
    assert len(doomed) == 3, doomed
    for t in doomed:
        b.Remove(t)
    pcbnew.SaveBoard(base, b)

    def freed_groups(extra=None, width=0):
        bb = pcbnew.LoadBoard(base)
        if extra is not None:
            t = pcbnew.PCB_TRACK(bb)
            t.SetStart(pcbnew.VECTOR2I(PAD[0], PAD[1]))
            t.SetEnd(pcbnew.VECTOR2I(int(extra[0] * 1e6), int(extra[1] * 1e6)))
            t.SetWidth(width)
            t.SetLayer(bb.GetLayerID("B.Cu"))
            t.SetNetCode(bb.GetNetsByName()["/01_POWER_TREE/USB_VBUS_CHG"].GetNetCode())
            bb.Add(t)
        pcbnew.ZONE_FILLER(bb).Fill(bb.Zones())
        return clusters_of(bb, "/01_POWER_TREE/BQ25185_SYS")

    def bonded(groups):
        for g in groups:
            if "U11.1" in g:
                return "U12.1" in g, g
        return False, []

    ctrl = freed_groups()
    ok0, g0 = bonded(ctrl)
    print("control (3 objects out, no escape): U11.1 bonded to U12.1 =", ok0, g0)

    rows = []
    for w in WIDTHS:
        for s in boundary():
            ok, g = bonded(freed_groups(s, w))
            rows.append(dict(to_mm=list(s), width_mm=w / 1e6, bonded=bool(ok),
                             island=g))
            print(f"  w{w/1e6:.3f} -> {s}  bonded={ok}")
    survivors = [r for r in rows if r["bonded"]]
    doc = dict(schema=1, decision="D-663",
               question=("does ANY straight B.Cu conductor from U11.10 to the "
                         "pocket boundary leave the freed BQ25185_SYS pour "
                         "bonding U11.1 to U12.1?"),
               method=("authority copied; the D-659 three-object cut removed; "
                       "one straight B.Cu track added per trial at the width "
                       "the .kicad_dru courtyard neck grants and at the "
                       "VBUS_CHG class floor; pcbnew.ZONE_FILLER per trial; "
                       "clusters read off GetConnectivity; nothing written"),
               board=SRC, board_sha256=src_sha,
               control_bonded=bool(ok0), control_island=g0,
               trials=len(rows), survivors=len(survivors),
               survivor_rows=survivors, rows=rows,
               verdict=("POCKET_HOLDS_BOTH" if survivors else
                        "POCKET_HOLDS_ONE"),
               authoritative_unchanged=(sha(SRC) == src_sha))
    out = sys.argv[1] if len(sys.argv) > 1 else "evidence/d663-u11-coexist.json"
    with open(out, "w") as f:
        json.dump(doc, f, indent=1, sort_keys=True)
        f.write("\n")
    print("verdict:", doc["verdict"], "survivors:", len(survivors), "of", len(rows))
    print("wrote", out)


main()
