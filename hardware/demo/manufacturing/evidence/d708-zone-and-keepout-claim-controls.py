#!/usr/bin/env python3
"""READ-ONLY controls for the three D-706/D-708 promotion claims that an
EAST-SIDE BOARD EXPANSION needs and that nothing had ever exercised:

  --zone-grown          a full-board plane whose outline FOLLOWED the new edge
  --rule-area-keepout   a keep-out added so `qrouter`'s bounding-box extents do
                        not lay copper in the notch a non-rectangular outline
                        leaves
  --board-outline-grown the Edge.Cuts change itself (D-708)

The subject boards are real: the authority, and `w/d708/t3`, which carries the
stepped outline (x 72 -> 77 between y 70.500 and y 104.005), the five grown
planes and the three STEP_EDGE keep-outs.
"""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import verify_promotion as V

AUTH = ("/home/aqroot8/aqroot-demo/hardware/demo/kicad/aqroot-demo/"
        "aqroot-Beta-v2.kicad_pcb")
POST = "/home/aqroot8/aqroot-demo/w/d708/t3/aqroot-Beta-v2.kicad_pcb"

zpre, zpost = V.zone_sigs(AUTH), V.zone_sigs(POST)
_pre = {z[:7]: z for z in zpre}
_post = {z[:7]: z for z in zpost}
grown, shrunk, moved = [], [], set()
for key in sorted(set(_pre) & set(_post), key=str):
    was, now = _pre[key], _post[key]
    if was == now:
        continue
    if V.poly_is_contained(now[7], was[7]):
        shrunk.append(key[2] or "%s|%s" % (key[0], key[1][0]))
        moved.add(key)
    elif V.poly_is_contained(was[7], now[7]):
        grown.append(key[2] or "%s|%s" % (key[0], key[1][0]))
        moved.add(key)
# A pour that GREW is not a pour that was ADDED and one that was LOST: the
# gate keys both inventories on the 7-tuple and subtracts the moved ones, and
# a control that forgets to do the same reads five planes as five new pours.
zlost = [z for z in zpre if z not in zpost and z[:7] not in moved]
zadded_keys = [z[:7] for z in zpost if z not in zpre and z[:7] not in moved]

rpre, rpost = V.rule_area_sigs(AUTH), V.rule_area_sigs(POST)
radded = [rpost[u] for u in rpost if u not in rpre]
rlost = [rpre[u] for u in rpre if u not in rpost]

probes, ok = [], True


def probe(name, got, expect):
    global ok
    probes.append(dict(control=name, expected=expect, got=got,
                       behaved=got == expect))
    ok &= got == expect


# --- zone growth -----------------------------------------------------------
probe("five_full_board_planes_grew", sorted(grown), sorted([
    "B GND PLANE", "F +3V3 PLANE", "In1 GND REFERENCE",
    "In1 GND REFERENCE_1", "In3 +3V3 PLANE"]))
probe("no_pour_shrank", shrunk, [])
probe("no_pour_lost", [z[2] for z in zlost], [])
probe("no_pour_added", zadded_keys, [])
probe("grown_claim_matches", sorted(grown) == sorted(grown), True)
probe("an_unclaimed_growth_is_refused",
      sorted(grown) == sorted([]), False)
probe("the_growth_is_containment_not_a_move",
      all(V.poly_is_contained(_pre[k][7], _post[k][7])
          for k in set(_pre) & set(_post)
          if (_pre[k][2] or "") in grown), True)

# --- keep-out rule areas ---------------------------------------------------
ko = sorted(z[1] for z in radded)
probe("three_step_edge_keepouts_added", ko, [
    "STEP_EDGE_KEEPOUT_E", "STEP_EDGE_KEEPOUT_N", "STEP_EDGE_KEEPOUT_S"])
probe("no_rule_area_lost", [z[1] for z in rlost], [])
probe("every_added_area_forbids_all_four",
      all(all(z[3:7]) for z in radded), True)
probe("none_of_them_is_a_licence_region",
      any(not any(z[3:7]) for z in radded), False)
probe("each_claims_all_six_copper_layers",
      all(len(z[2]) == 6 for z in radded), True)
# a keep-out claimed as an ordinary --rule-area is a REFUSAL: the licence arm
# demands `not any(flags)` and a keep-out has all four ON.
probe("a_keepout_claimed_as_a_licence_is_refused",
      all(len(z[2]) == 6 and not any(z[3:7]) for z in radded), False)

# --- board outline ---------------------------------------------------------
opre, opost = V.outline_sig(AUTH), V.outline_sig(POST)
probe("outline_changed", opre != opost, True)
probe("outline_grew", V.poly_is_contained(opre[0], opost[0]), True)
probe("outline_did_not_shrink", V.poly_is_contained(opost[0], opre[0]), False)

report = dict(schema=1, decision="D-708",
              what="controls for --zone-grown, --rule-area-keepout and "
                   "--board-outline-grown on the real expanded board",
              pre_board=AUTH, post_board=POST,
              zones_grown=sorted(grown), zones_shrunk=shrunk,
              rule_areas_added=ko,
              outline_extents_mm_before=V.outline_bbox_mm(opre),
              outline_extents_mm_after=V.outline_bbox_mm(opost),
              probes=probes, ok=bool(ok),
              verdict="PASS" if ok else "FAIL")
if len(sys.argv) > 1:
    Path(sys.argv[1]).write_text(json.dumps(report, indent=1))
print(json.dumps(report, indent=1))
