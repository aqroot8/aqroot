# -*- coding: utf-8 -*-
"""FBV2-P2-039 -- bounded coordinated west-button pull-up-column screen.

Scratch only.  Moves the three still-unrouted pull-ups together, leaving U2,
R4/R7/R9, switches, accepted copper, rules and topology fixed.  Each legal
layout is tested against all three four-physical-pad button nets.
"""
import json, os, shutil, sys
import pcbnew

SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)
import incremental_router as IR
import path_role_util as RU
import qrouter as QR
from west_button_eco_038 import legal

OUT = os.path.join(SP, "w", "ECO_039")
TARGETS = (("BTN_DOWN_N", "R5"), ("BTN_A_N", "R8"), ("BTN_LEFT_N", "R6"))

# Coordinated, cardinality-3 layouts.  The first family translates the whole
# unrouted column west; the second staggers its centre member farther west;
# the third combines a west translation with the small vertical slack left
# between fixed accepted R4/R9.  No accepted-button pull-up is moved.
LAYOUTS = [
    ("west05", {"R5": (-0.5, 0), "R8": (-0.5, 0), "R6": (-0.5, 0)}),
    ("west10", {"R5": (-1.0, 0), "R8": (-1.0, 0), "R6": (-1.0, 0)}),
    ("west15", {"R5": (-1.5, 0), "R8": (-1.5, 0), "R6": (-1.5, 0)}),
    ("west20", {"R5": (-2.0, 0), "R8": (-2.0, 0), "R6": (-2.0, 0)}),
    ("centre15", {"R5": (-0.5, 0), "R8": (-1.5, 0), "R6": (-0.5, 0)}),
    ("centre20", {"R5": (-1.0, 0), "R8": (-2.0, 0), "R6": (-1.0, 0)}),
    ("spread05", {"R5": (-1.0, 0.25), "R8": (-1.0, -0.25), "R6": (-1.0, 0.25)}),
    ("spread10", {"R5": (-1.5, 0.25), "R8": (-1.5, -0.25), "R6": (-1.5, 0.25)}),
]


def route_net(pcb, net):
    qb = QR.QBoard(pcb)
    IR.inject_existing_via_obstacles(qb)
    if net in IR.GROUPS:
        group = dict(IR.GROUPS[net])
        group.pop("hop_anchor_plan", None)
    else:
        group = dict(layer="B", width=200000, clr_pad=200000,
                     clr_trk=200000, via_dia=600000, via_drill=300000,
                     nets=[net])
    nf = IR.resolve_nets(qb, group)[net]
    pads = IR.physical_net_pads(qb, nf)
    pads.sort(key=lambda x: (x["ref"], x["x"], x["y"]))
    rec = []
    for i, j in IR.mst_edges(pads):
        a, b = pads[i], pads[j]
        layer, kind = IR.edge_plan(a, b, group)
        if kind == "same":
            r = QR.connect_role(qb, nf, a, b, layer, group["width"],
                                group["clr_pad"], group["clr_trk"])
        else:
            r = IR.connect_cross(qb, nf, a, b, group)
        rec.append(dict(a=a["ref"], b=b["ref"], kind=kind,
                        ok=bool(r.get("ok")), reason=r.get("reason")))
        if not r.get("ok"):
            break
    return len(rec) == len(pads) - 1 and all(x["ok"] for x in rec), rec


def main():
    os.makedirs(OUT, exist_ok=True)
    results = []
    for tag, moves in LAYOUTS:
        base = os.path.join(OUT, tag)
        os.makedirs(base, exist_ok=True)
        placed = os.path.join(base, RU.PCBNAME)
        shutil.copyfile(IR.AUTH, placed)
        board = pcbnew.LoadBoard(placed)
        fps = {f.GetReference(): f for f in board.GetFootprints()}
        for ref, (dx, dy) in moves.items():
            p = fps[ref].GetPosition()
            fps[ref].SetPosition(pcbnew.VECTOR2I(p.x + int(dx * 1e6),
                                                p.y + int(dy * 1e6)))
        conflicts = []
        for ref in moves:
            ok, why = legal(board, ref)
            if not ok:
                conflicts.append("%s:%s" % (ref, why))
        if conflicts:
            results.append(dict(layout=tag, legal=False, conflicts=conflicts))
            print(tag, "COLLISION", ",".join(conflicts))
            shutil.rmtree(base)
            continue
        board.Save(placed)
        row = dict(layout=tag, legal=True, moves=moves, routes={})
        for net, _ in TARGETS:
            trial = os.path.join(base, net)
            os.makedirs(trial, exist_ok=True)
            pcb = os.path.join(trial, RU.PCBNAME)
            shutil.copyfile(placed, pcb)
            ok, rec = route_net(pcb, net)
            row["routes"][net] = dict(ok=ok, route=rec)
            print(tag, net, "PASS" if ok else rec[-1].get("reason", "FAIL"))
            if not ok:
                shutil.rmtree(trial)
        results.append(row)
    with open(os.path.join(OUT, "results.json"), "w") as f:
        json.dump(results, f, indent=1, sort_keys=True)
    wins = [(r["layout"], n) for r in results if r.get("legal")
            for n, v in r["routes"].items() if v["ok"]]
    print("RESULT", wins if wins else "NO SUCCESS", "in", len(LAYOUTS), "layouts")
    return 0 if wins else 1


if __name__ == "__main__":
    sys.exit(main())
