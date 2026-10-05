#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AQROOT Demo -- the EXTERNAL-INTERFACE DATUM contract (ID1-ID9), D-805.

WHY THIS FILE EXISTS.  D-804 shipped `J3` (USB-C) and `J2` (microSD) facing INTO
the board.  Every gate passed, because no gate asked which way a connector
opens: `mechanical_keepout_contract` MK1 asks an X-only datum question of `J3`,
MK11 pins `SW1` / `SW9` / `J5` coordinates, and nothing reads a mating face.
And the `J2` footprint's own drawing said the card entered from the wrong side.

So the facing is DERIVED HERE FROM THE FOOTPRINT GEOMETRY ON THE BOARD, not
from a stored angle, and compared with `interface_datums.json`:

    ID1  J3 USB-C: the mating face is the F.Fab body edge OPPOSITE the contact-
         land row.  It must point the declared way (+Y, out of the bottom
         edge) and lie ON the board outline at the declared Y.
    ID2  J2 microSD: the card-entry edge is the body edge on the CONTACT-TAIL
         side (Molex SD-502570-001 sheet 1).  Same two tests.  Its card-travel
         envelope (card width x eject stroke, beyond the face) must lie wholly
         outside the board and meet no other footprint's courtyard (SW4 named).
    ID3  SW9 power slide: the actuator tip is the F.Fab extent away from the
         land row; it must point +X, stand at the declared X past the board
         edge, and the body face must sit on the edge (body over board).
    ID4  J5, J8, SW1 and SW4 are where the datum file puts them (unchanged).
    ID5  BOSS1 / BOSS2 are where the datum file puts them (unchanged).
    ID6  The outline is the declared one: bbox, main bottom edge Y 148, east
         max X 77, and NOTHING below Y 148 except inside the declared tabs.
    ID7  Each tab edge is reached by the interface it exists for (J2 / J3 face
         on its tab edge) -- a tab with no connector at it is refused.
    ID8  Enclosure arithmetic: every tab edge keeps the declared gap to the
         cavity wall, and every interface states its recess to the exterior.
    ID9  NOT VACUOUS.  J3 and J2 turned 180 deg in memory (the D-804 mistake)
         must each FAIL their clause; SW9 put back at its D-804 position must
         FAIL ID3; a 0.1 mm J8 nudge must FAIL ID4; a tab widened 1 mm must
         FAIL ID6.

    python3 checks/interface_datum_contract.py [--board B] [-o OUT.json]
"""
import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

import pcbnew

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
BOARD = ROOT / "hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb"
DATUMS = HERE.parent / "interface_datums.json"
TOL = 0.01
MM = 1e6


def sha256(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def fab_box(f):
    xs, ys = [], []
    for g in f.GraphicalItems():
        if g.GetLayer() in (pcbnew.F_Fab, pcbnew.B_Fab) and g.GetClass() != "PCB_TEXT":
            bb = g.GetBoundingBox()
            xs += [bb.GetX(), bb.GetRight()]
            ys += [bb.GetY(), bb.GetBottom()]
    w = 0.1 * MM / 2      # fab strokes are 0.1 mm; report the drawn line centre
    return (min(xs) + w) / MM, (min(ys) + w) / MM, (max(xs) - w) / MM, (max(ys) - w) / MM


def centroid(pads):
    pts = [p.GetPosition() for p in pads]
    return (sum(p.x for p in pts) / len(pts) / MM, sum(p.y for p in pts) / len(pts) / MM)


def axis(dx, dy):
    if abs(dx) >= abs(dy):
        return "+X" if dx > 0 else "-X"
    return "+Y" if dy > 0 else "-Y"


def edge_of(box, d):
    x0, y0, x1, y1 = box
    return {"+X": x1, "-X": x0, "+Y": y1, "-Y": y0}[d]


def outline(board):
    poly = pcbnew.SHAPE_POLY_SET()
    board.GetBoardPolygonOutlines(poly, False)
    return poly


def on_outline(poly, x, y, tol=0.05):
    p = pcbnew.VECTOR2I(int(x * MM), int(y * MM))
    o = poly.Outline(0)
    return o.SquaredDistance(p) <= (tol * MM) ** 2


def facing(f, rear_pads, toward_rear):
    """Direction of the interface face.  toward_rear=False: face is OPPOSITE the
    land row (USB-C mating face, slide actuator).  True: face is ON the land-row
    side (Molex 502570 card entry over its contact tails)."""
    box = fab_box(f)
    cx, cy = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
    px, py = centroid(rear_pads)
    d = axis(px - cx, py - cy) if toward_rear else axis(cx - px, cy - py)
    return d, edge_of(box, d), box


def id_connector(board, ref, spec, toward_rear, poly):
    f = board.FindFootprintByReference(ref)
    if ref == "J3":
        pads = [p for p in f.Pads() if p.GetNumber()[:1] in "AB"]
    else:
        pads = [p for p in f.Pads() if p.GetNumber() in [str(i) for i in range(1, 9)]]
    d, face, box = facing(f, pads, toward_rear)
    mid = ((box[0] + box[2]) / 2, face) if d in ("+Y", "-Y") else (face, (box[1] + box[3]) / 2)
    on_edge = on_outline(poly, *mid)
    tol = spec.get("face_tolerance_mm", TOL)
    key = "face_y" if d in ("+Y", "-Y") else "face_x"
    row = dict(ref=ref, derived_outward=d, declared_outward=spec["outward"],
               face=round(face, 4), declared_face=spec.get("face_y"),
               face_midpoint=[round(mid[0], 4), round(mid[1], 4)],
               face_on_board_outline=on_edge, fab_box=[round(v, 4) for v in box])
    row["ok"] = (d == spec["outward"] and abs(face - spec["face_y"]) <= tol
                 and (on_edge or not spec.get("on_board_edge")))
    return row


def id2_travel(board, spec, poly):
    """The card-travel envelope (card width x eject stroke) beyond the card-entry
    edge, in whatever direction the footprint derives.  It must lie wholly off
    the board and meet no other courtyard."""
    f = board.FindFootprintByReference("J2")
    pads = [p for p in f.Pads() if p.GetNumber() in [str(i) for i in range(1, 9)]]
    d, face, box = facing(f, pads, True)
    w, s = spec["card"]["width_mm"], spec["card"]["eject_mm"]
    cx, cy = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
    e = 0.01
    env = {"+Y": (cx - w / 2, face + e, cx + w / 2, face + s), "-Y": (cx - w / 2, face - s, cx + w / 2, face - e),
           "+X": (face + e, cy - w / 2, face + s, cy + w / 2), "-X": (face - s, cy - w / 2, face - e, cy + w / 2)}[d]
    rect = pcbnew.SHAPE_POLY_SET()
    rect.NewOutline()
    for x, y in ((env[0], env[1]), (env[2], env[1]), (env[2], env[3]), (env[0], env[3])):
        rect.Append(int(x * MM), int(y * MM))
    inside_board = poly.Collide(rect)
    hits = sorted({g.GetReference() for g in board.GetFootprints() if g.GetReference() != "J2"
                   for lay in (pcbnew.F_CrtYd, pcbnew.B_CrtYd)
                   if g.GetCourtyard(lay).OutlineCount() and g.GetCourtyard(lay).Collide(rect)})
    return dict(ok=(d == spec["outward"] and not inside_board and not hits),
                derived_outward=d, envelope=[round(v, 3) for v in env],
                envelope_meets_board=inside_board, courtyards_met=hits,
                named_parts_met=[r for r in spec["travel_must_not_meet"] if r in hits])


def id3(board, spec, poly):
    f = board.FindFootprintByReference("SW9")
    pads = [p for p in f.Pads() if p.GetNumber() in ("1", "2", "3")]
    d, tip, box = facing(f, pads, False)
    body_face = tip - spec["actuator_mm"]
    p = f.GetPosition()
    row = dict(derived_outward=d, declared_outward=spec["outward"], actuator_tip_x=round(tip, 4),
               declared_tip_x=spec["actuator_tip_x"], body_face_x=round(body_face, 4),
               declared_body_edge_x=spec["body_edge_x"],
               body_face_on_board_outline=on_outline(poly, body_face, p.y / MM),
               position=[p.x / MM, p.y / MM])
    row["ok"] = (d == spec["outward"] and abs(tip - spec["actuator_tip_x"]) <= TOL
                 and abs(body_face - spec["body_edge_x"]) <= TOL and row["body_face_on_board_outline"])
    return row


def id_fixed(board, refs, spec):
    rows, ok = {}, True
    for ref in refs:
        f = board.FindFootprintByReference(ref)
        s = spec[ref]
        p = f.GetPosition()
        r = dict(position=[round(p.x / MM, 4), round(p.y / MM, 4)], declared=s["position"],
                 rotation=round(f.GetOrientationDegrees(), 3), declared_rotation=s.get("rotation", 0.0))
        r["ok"] = (abs(p.x / MM - s["position"][0]) <= 1e-4 and abs(p.y / MM - s["position"][1]) <= 1e-4
                   and abs(((f.GetOrientationDegrees() - r["declared_rotation"] + 180) % 360) - 180) <= 1e-3)
        rows[ref] = r
        ok = ok and r["ok"]
    return dict(ok=ok, parts=rows)


def id5(board, mounting):
    return id_fixed(board, list(mounting), {k: dict(position=v) for k, v in mounting.items()})


def id6(board, spec, poly):
    bb = poly.BBox()
    box = [bb.GetX() / MM, bb.GetY() / MM, bb.GetRight() / MM, bb.GetBottom() / MM]
    o = poly.Outline(0)
    stray = []
    for i in range(o.PointCount()):
        q = o.CPoint(i)
        x, y = q.x / MM, q.y / MM
        # a tab owns its straight sides plus its concave fillets (one radius outboard)
        if y > spec["main_bottom_y"] + 1e-6 and not any(
                t["x"][0] - t["concave_fillet_r"] - 1e-6 <= x <= t["x"][1] + t["concave_fillet_r"] + 1e-6
                and (t["x"][0] - 1e-6 <= x <= t["x"][1] + 1e-6 or y <= spec["main_bottom_y"] + t["concave_fillet_r"] + 1e-6)
                for t in spec["tabs"]):
            stray.append([round(x, 3), round(y, 3)])
    ok = (all(abs(a - b) <= 0.06 for a, b in zip(box, spec["bbox"])) and not stray
          and box[2] <= spec["east_max_x"] + 0.06)
    return dict(ok=ok, bbox=[round(v, 3) for v in box], declared_bbox=spec["bbox"],
                points_below_main_edge_outside_tabs=stray, outline_vertices=o.PointCount())


def id7(rows, tabs):
    out, ok = {}, True
    owner = {"J2_TAB": "J2", "J3_TAB": "J3"}
    for t in tabs:
        r = rows[owner[t["name"]]]
        x = r["face_midpoint"][0]
        hit = t["x"][0] < x < t["x"][1] and abs(r["face"] - t["edge_y"]) <= 0.25
        out[t["name"]] = dict(owner=owner[t["name"]], owner_face=r["face_midpoint"], ok=hit)
        ok = ok and hit
    return dict(ok=ok, tabs=out)


def id8(datums):
    enc, o = datums["enclosure"], datums["outline"]
    rows = {}
    for t in o["tabs"]:
        gap = enc["cavity_face_south_y"] - t["edge_y"]
        rows[t["name"]] = dict(gap_to_cavity_wall_mm=round(gap, 3), declared=o["local_tab_to_wall_gap_mm"],
                               ok=abs(gap - o["local_tab_to_wall_gap_mm"]) <= 1e-6 and gap > 0)
    i = datums["interfaces"]
    rows["J3_recess_to_exterior_mm"] = round(enc["exterior_south_y"] - i["J3"]["face_y"], 3)
    rows["J2_latched_card_below_exterior_mm"] = round(enc["exterior_south_y"] - (i["J2"]["face_y"] + i["J2"]["card"]["lock_mm"]), 3)
    rows["J2_ejected_card_proud_of_exterior_mm"] = round(i["J2"]["face_y"] + i["J2"]["card"]["eject_mm"] - enc["exterior_south_y"], 3)
    rows["SW9_tip_below_exterior_mm"] = round(enc["exterior_east_x"] - i["SW9"]["actuator_tip_x"], 3)
    rows["SW9_tip_into_wall_mm"] = round(i["SW9"]["actuator_tip_x"] - enc["cavity_face_east_x"], 3)
    ok = (all(r["ok"] for k, r in rows.items() if isinstance(r, dict))
          and rows["J3_recess_to_exterior_mm"] <= i["J3"]["allowed_recess_mm"] + 1e-9
          and rows["J2_ejected_card_proud_of_exterior_mm"] > 0
          and rows["SW9_tip_into_wall_mm"] > 0)
    return dict(ok=ok, rows=rows)


def run(board, datums):
    poly = outline(board)
    i = datums["interfaces"]
    rows = {"J3": id_connector(board, "J3", i["J3"], False, poly),
            "J2": id_connector(board, "J2", i["J2"], True, poly)}
    checks = {
        "ID1_J3_usb_c_mating_face_outward_on_edge": rows["J3"],
        "ID2_J2_card_entry_outward_on_edge": dict(rows["J2"], travel=id2_travel(board, i["J2"], poly)),
        "ID3_SW9_actuator_outward_past_edge": id3(board, i["SW9"], poly),
        "ID4_unchanged_interfaces_J5_J8_SW1_SW4": id_fixed(board, ["J5", "J8", "SW1", "SW4"], i),
        "ID5_mounting_holes_unchanged": id5(board, datums["mounting"]),
        "ID6_outline_is_the_declared_one": id6(board, datums["outline"], poly),
        "ID7_every_tab_is_reached_by_its_interface": id7(rows, datums["outline"]["tabs"]),
        "ID8_enclosure_arithmetic": id8(datums),
    }
    checks["ID2_J2_card_entry_outward_on_edge"]["ok"] = (
        rows["J2"]["ok"] and checks["ID2_J2_card_entry_outward_on_edge"]["travel"]["ok"])
    return checks


def controls(board, datums):
    ctl = {}
    i = datums["interfaces"]

    def turned(ref, clause):
        f = board.FindFootprintByReference(ref)
        was = f.GetOrientationDegrees()
        f.SetOrientationDegrees(was + 180.0)
        bad = not run(board, datums)[clause]["ok"]
        f.SetOrientationDegrees(was)
        return bad
    ctl["J3_turned_180_like_D804_is_refused"] = turned("J3", "ID1_J3_usb_c_mating_face_outward_on_edge")
    ctl["J2_turned_180_like_D804_is_refused"] = turned("J2", "ID2_J2_card_entry_outward_on_edge")

    # J2 put back at its D-804 placement: refused, and its card travel meets SW4 (the brief's conflict)
    j2 = board.FindFootprintByReference("J2")
    was, wr = j2.GetPosition(), j2.GetOrientationDegrees()
    j2.SetOrientationDegrees(0.0)
    j2.SetPosition(pcbnew.VECTOR2I(int(15.0 * MM), int(136.8 * MM)))
    t = id2_travel(board, i["J2"], outline(board))
    ctl["J2_at_its_D804_placement_is_refused_and_its_travel_meets_SW4"] = (not t["ok"]) and "SW4" in t["named_parts_met"]
    j2.SetOrientationDegrees(wr)
    j2.SetPosition(was)

    sw9 = board.FindFootprintByReference("SW9")
    was = sw9.GetPosition()
    sw9.SetPosition(pcbnew.VECTOR2I(int(66.7 * MM), was.y))
    ctl["SW9_at_its_D804_position_is_refused"] = not run(board, datums)["ID3_SW9_actuator_outward_past_edge"]["ok"]
    sw9.SetPosition(was)

    j8 = board.FindFootprintByReference("J8")
    was = j8.GetPosition()
    j8.SetPosition(pcbnew.VECTOR2I(was.x + 100000, was.y))
    ctl["a_0_100_mm_J8_nudge_is_refused"] = not run(board, datums)["ID4_unchanged_interfaces_J5_J8_SW1_SW4"]["ok"]
    j8.SetPosition(was)

    wide = json.loads(json.dumps(datums))
    wide["outline"]["tabs"][1]["x"] = [37.5, 49.5]
    ctl["a_tab_wider_than_declared_is_refused"] = not id6(board, wide["outline"], outline(board))["ok"]

    far = json.loads(json.dumps(datums))
    far["enclosure"]["cavity_face_south_y"] = 152.0
    ctl["a_tab_gap_other_than_declared_is_refused"] = not id8(far)["ok"]
    # the facing derivation must agree with the D-804 board's known-wrong state when J3 is turned
    return dict(ok=all(ctl.values()), controls=ctl)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--board", type=Path, default=BOARD)
    ap.add_argument("--datums", type=Path, default=DATUMS)
    ap.add_argument("-o", "--out", type=Path)
    a = ap.parse_args()
    board = pcbnew.LoadBoard(str(a.board))
    datums = json.loads(a.datums.read_text())
    checks = run(board, datums)
    checks["ID9_not_vacuous"] = controls(board, datums)
    doc = dict(schema=1, decision=datums["decision"], board=str(a.board), board_sha256=sha256(a.board),
               datums=str(a.datums), datums_sha256=sha256(a.datums), checks=checks,
               all_pass=all(c["ok"] for c in checks.values()))
    text = json.dumps(doc, indent=1, sort_keys=True)
    if a.out:
        a.out.write_text(text + "\n", encoding="utf-8")
    print(text)
    for k, c in sorted(checks.items()):
        print(" %-50s %s" % (k, "PASS" if c["ok"] else "FAIL"), file=sys.stderr)
    return 0 if doc["all_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
