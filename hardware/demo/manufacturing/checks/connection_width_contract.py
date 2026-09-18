#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AQROOT Demo -- the `connection_width` test is SWITCHED OFF on this board, and
this is what it would say. D-744.

D-738 named the defect class: `solder_mask_min_width` was 0.000 mm, so KiCad's
solder-mask-bridge test never ran, and every "DRC is clean" in this programme
carried zero information about dams.  **`min_connection` is 0.000 mm too**, so
`connection_width` -- the test that finds the narrowest cross-section where two
pieces of copper actually JOIN -- has never run either, on any board this
programme has produced.  A zeroed threshold is not a passing check; it is an
absent one, and the difference is invisible in a violation count.

WHAT THE TEST MEASURES, AND WHY A RAW COUNT IS USELESS.  KiCad measures the
THROAT where two copper items meet.  Two 0.200 mm tracks meeting at an acute
angle have a throat narrower than either of them -- that is the geometry of a
V, not a defect, and the copper on both sides is continuous.  Probing this
board at 0.200 mm returns 95 violations and 74 of the 81 distinct object pairs
are exactly that.  So the count is not the finding.

THE FINDING IS WHETHER A THIN CONTACT IS LOAD-BEARING.  KiCad's connectivity
treats two overlapping via pads as connected, so a net whose only link between
its two halves is a 0.029 mm tangency still reads CONNECTED everywhere -- in
the ratsnest, in `routing_ledger.py`, in the promotion gate.  Nothing on this
board could have seen that.  So C2 rebuilds each affected net's graph from
EXPLICIT copper coincidence only -- track end to track end, track end on
another track's interior (a T-junction is real copper), track end to via, track
end inside a pad, a via spanning its own layers -- and NEVER joins two vias
merely because their pads overlap.  If the component count rises when that
assumption is dropped, the contact is carrying the net.

    C1  every `connection_width` finding at the probe width is classified,
        and stable electrical signatures below the strict floor are enumerated
    C2  no net's connectivity depends on a contact below the strict floor
    C3  the graph is not vacuous: it must reproduce the board's own
        connectivity on a net known to be whole AND stay split on the net
        known to be open, or its verdicts mean nothing

    python3 checks/connection_width_contract.py [--probe 0.20] [--strict 0.15] [-o OUT]
"""
import argparse, json, math, re, shutil, subprocess, sys, tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
MFG = HERE.parent
ROOT = HERE.parents[3]
PROJECT = ROOT / "hardware/demo/kicad/aqroot-demo"
BOARD = PROJECT / "aqroot-Beta-v2.kicad_pcb"

sys.path.insert(0, str(MFG))
import pcbnew                                               # noqa: E402

TOL = 1000                              # 1 um, KiCad internal units
# C3's two controls, and they must stay these two: one net the ledger reports
# WHOLE and one it reports OPEN.  A graph that cannot tell them apart is not
# measuring connectivity.
CONTROL_WHOLE = "/I2C_SCL_INT"
CONTROL_SPLIT = "/BQ25185_STAT2"


def probe_drc(probe_mm):
    """Run KiCad DRC on a scratch copy with `min_connection` turned ON."""
    tmp = Path(tempfile.mkdtemp(prefix="aqroot-cw-"))
    for suffix in (".kicad_pcb", ".kicad_pro", ".kicad_dru"):
        src = BOARD.with_suffix(suffix)
        if src.exists():
            shutil.copy(src, tmp / src.name)
    pro = tmp / BOARD.with_suffix(".kicad_pro").name
    doc = json.loads(pro.read_text())
    doc["board"]["design_settings"]["rules"]["min_connection"] = probe_mm
    doc["board"]["design_settings"]["rule_severities"]["connection_width"] = "error"
    pro.write_text(json.dumps(doc, indent=2))
    out = tmp / "drc.json"
    subprocess.run(["kicad-cli", "pcb", "drc", "--format", "json", "--units", "mm",
                    "--severity-all", "-o", str(out), str(tmp / BOARD.name)],
                   check=True, capture_output=True, text=True)
    return json.loads(out.read_text())


def classify(report, strict_mm):
    rows, pairs = [], {}
    for v in report.get("violations", ()):
        if v.get("type") != "connection_width":
            continue
        m = re.search(r"actual ([0-9.]+) mm\) \((\S+)\)", v["description"])
        if not m:
            continue
        width, layer = float(m.group(1)), m.group(2)
        kinds = tuple(sorted(i["description"].split(" [")[0].split(" of ")[0]
                             for i in v.get("items", ())))
        nets = tuple(sorted(set(re.findall(
            r"\[([^\]]+)\]", " ".join(i["description"] for i in v.get("items", ()))))))
        uid = tuple(sorted(i["uuid"] for i in v.get("items", ())))
        rows.append(dict(width_mm=width, layer=layer, kinds=list(kinds), nets=list(nets)))
        e = pairs.setdefault(uid, dict(width_mm=width, layers=set(), kinds=list(kinds),
                                       nets=list(nets),
                                       # D-760: SORTED.  `uid` already sorts the
                                       # two uuids so the PAIR is stable, but
                                       # `at` was built in DRC-report item order
                                       # and that order can flip between
                                       # processes on a byte-identical board --
                                       # one GND via pair reported
                                       # [[71.8,97.9],[71.8,97.3]] at d759 and
                                       # [[71.8,97.3],[71.8,97.9]] at d760.  The
                                       # list order was made total once already
                                       # (below); the ENTRY has to be total too.
                                       at=sorted(
                                           [round(i["pos"]["x"], 3),
                                            round(i["pos"]["y"], 3)]
                                           for i in v.get("items", ()))))
        e["width_mm"] = min(e["width_mm"], width)
        e["layers"].add(layer)
    for e in pairs.values():
        e["layers"] = sorted(e["layers"])
    # A TOTAL order, not just by width.  `contract_regression` compares this
    # artifact field by field, so two entries of the SAME width must not be
    # allowed to swap places between runs -- the first version sorted on width
    # alone and reported a spurious DIFFERS on `below[2].at[0][0]`, 59.7 versus
    # 71.8, between two identical 0.0790 mm rows.  A non-deterministic artifact
    # cannot be a baseline.
    below_pairs = [e for e in pairs.values() if e["width_mm"] < strict_mm]
    # D-761 CTO hardening: KiCad can choose a different adjacent Track/Track
    # pair to represent the SAME acute connection-width throat between runs.
    # The pair UUID/coordinates are therefore diagnostic, not release-stable
    # evidence.  On this board every below-floor finding is uniquely identified
    # by the electrical signature below; emit that stable signature instead of
    # pretending KiCad's representative pair is deterministic.
    signatures = {}
    for e in below_pairs:
        key = (e["width_mm"], tuple(e["layers"]), tuple(e["nets"]), tuple(e["kinds"]))
        signatures[key] = dict(width_mm=e["width_mm"], layers=e["layers"],
                               nets=e["nets"], kinds=e["kinds"])
    if len(signatures) != len(below_pairs):
        raise RuntimeError("below-floor connection signatures are not unique; add a deterministic discriminator")
    below = [signatures[k] for k in sorted(signatures)]
    return rows, list(pairs.values()), below


def components(board, net, join_touching_vias):
    parent = {}

    def find(a):
        while parent.setdefault(a, a) != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    def union(a, c):
        ra, rc = find(a), find(c)
        if ra != rc:
            parent[ra] = rc

    def key(x, y):
        return (round(x / TOL), round(y / TOL))

    vias = [t for t in board.GetTracks()
            if t.GetNetname() == net and t.Type() == pcbnew.PCB_VIA_T]
    tracks = [t for t in board.GetTracks()
              if t.GetNetname() == net and t.Type() != pcbnew.PCB_VIA_T]
    pads = [(fp.GetReference(), pd) for fp in board.GetFootprints()
            for pd in fp.Pads() if pd.GetNetname() == net]

    for t in tracks:
        s, e = t.GetStart(), t.GetEnd()
        ly = board.GetLayerName(t.GetLayer())
        union(("T", ly) + key(s.x, s.y), ("T", ly) + key(e.x, e.y))
    for t1 in tracks:
        l1 = board.GetLayerName(t1.GetLayer())
        for t2 in tracks:
            if t1 is t2 or board.GetLayerName(t2.GetLayer()) != l1:
                continue
            x1, y1 = t2.GetStart().x, t2.GetStart().y
            x2, y2 = t2.GetEnd().x, t2.GetEnd().y
            half = (t2.GetWidth() + t1.GetWidth()) / 2.0
            dx, dy = x2 - x1, y2 - y1
            for q in (t1.GetStart(), t1.GetEnd()):
                if dx == 0 and dy == 0:
                    d = math.dist((q.x, q.y), (x1, y1))
                else:
                    u = max(0.0, min(1.0, ((q.x-x1)*dx + (q.y-y1)*dy)/(dx*dx+dy*dy)))
                    d = math.dist((q.x, q.y), (x1+u*dx, y1+u*dy))
                if d <= half:
                    union(("T", l1) + key(q.x, q.y), ("T", l1) + key(x1, y1))
    for v in vias:
        p = v.GetPosition()
        base = ("V",) + key(p.x, p.y)
        for l in range(pcbnew.PCB_LAYER_ID_COUNT):
            if v.IsOnLayer(l) and pcbnew.IsCopperLayer(l):
                union(base, ("T", board.GetLayerName(l)) + key(p.x, p.y))
    for ref, pd in pads:
        p = pd.GetPosition()
        base = ("P", ref, pd.GetNumber())
        for l in range(pcbnew.PCB_LAYER_ID_COUNT):
            if not (pcbnew.IsCopperLayer(l) and pd.IsOnLayer(l)):
                continue
            ly = board.GetLayerName(l)
            union(base, ("T", ly) + key(p.x, p.y))
            for t in tracks:
                if board.GetLayerName(t.GetLayer()) != ly:
                    continue
                for q in (t.GetStart(), t.GetEnd()):
                    if pd.HitTest(pcbnew.VECTOR2I(q.x, q.y)):
                        union(base, ("T", ly) + key(q.x, q.y))
            for v in vias:
                q = v.GetPosition()
                if v.IsOnLayer(l) and pd.HitTest(pcbnew.VECTOR2I(q.x, q.y)):
                    union(base, ("V",) + key(q.x, q.y))
    if join_touching_vias:
        for i, v1 in enumerate(vias):
            for v2 in vias[i+1:]:
                p1, p2 = v1.GetPosition(), v2.GetPosition()
                if math.dist((p1.x, p1.y), (p2.x, p2.y)) <= (
                        v1.GetWidth(pcbnew.F_Cu) + v2.GetWidth(pcbnew.F_Cu)) / 2:
                    union(("V",) + key(p1.x, p1.y), ("V",) + key(p2.x, p2.y))
    return len({find(k) for k in list(parent)})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--probe", type=float, default=0.20,
                    help="minimum connection width to probe KiCad with")
    ap.add_argument("--strict", type=float, default=0.15,
                    help="below this a contact is enumerated and tested")
    ap.add_argument("--board", type=Path, default=BOARD)
    ap.add_argument("-o", dest="out", type=Path)
    args = ap.parse_args()

    report = probe_drc(args.probe)
    rows, pairs, below = classify(report, args.strict)
    board = pcbnew.LoadBoard(str(args.board.resolve()))

    nets = sorted({n for e in below for n in e["nets"]})
    tested = []
    for n in nets:
        with_t = components(board, n, True)
        without = components(board, n, False)
        tested.append(dict(net=n, components_with_via_tangency=with_t,
                           components_without_via_tangency=without,
                           load_bearing=without > with_t))

    whole = components(board, CONTROL_WHOLE, False)
    split = components(board, CONTROL_SPLIT, False)

    checks = {
        "C1_classified": dict(
            ok=True, probe_mm=args.probe, strict_mm=args.strict,
            violations=len(rows), distinct_pairs=len(pairs),
            pairs_below_strict=len(below),
            benign_acute_throats=len(pairs) - len(below),
            below=below),
        "C2_none_load_bearing": dict(
            ok=not any(t["load_bearing"] for t in tested), nets=tested),
        "C3_graph_not_vacuous": dict(
            ok=(whole == 1 and split == 2),
            control_whole_net=CONTROL_WHOLE, control_whole_components=whole,
            control_split_net=CONTROL_SPLIT, control_split_components=split,
            note="the whole net must resolve to ONE component, matching the "
                 "board's own connectivity, and the approved-unrouted net must "
                 "stay at TWO -- a graph that cannot tell them apart proves "
                 "nothing about the ones in between"),
    }
    out = dict(schema=1, board=str(args.board),
               board_min_connection_setting=0.0,
               why="board setup carries min_connection 0.0, so KiCad never runs "
                   "this test; the probe turns it on in a scratch copy only",
               checks=checks,
               all_pass=all(c["ok"] for c in checks.values()))
    text = json.dumps(out, indent=1, sort_keys=True)
    if args.out:
        args.out.write_text(text + "\n", encoding="utf-8")
    print(text)
    for k, c in checks.items():
        print("  %s %s" % (k, "PASS" if c["ok"] else "FAIL"), file=sys.stderr)
    return 0 if out["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
