#!/usr/bin/env python3
"""D-680 CONTROLS for maze3d.Neck's reach.  READ-ONLY.

C1  reach 0 is the pre-D-680 gate: mask_reach == mask, and `licensed` refuses
    ANY polyline that strays at all.
C2  the D-584 shape -- a polyline whose LAST TWO vertices are both outside, so
    a whole segment lies outside every named courtyard -- is REFUSED at a reach
    that is long enough to contain it.
C3  a polyline that starts strictly inside and leaves ONCE, at the end, by less
    than the reach, is ADMITTED.
C4  the same polyline is REFUSED when the stray exceeds the reach.
C5  a polyline whose FIRST vertex is outside is REFUSED.
C6  U21's courtyard east edge, and the copper this board already carries past
    it, are what the change is measured against.
"""
import json, sys
from pathlib import Path
HERE = Path("/home/aqroot8/aqroot-demo/hardware/demo/manufacturing")
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[2] / "hardware/beta-v2/checks"))
import numpy as np
import qrouter as qr, maze3d as mz

BOARD = HERE.parent / "kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb"
MM = qr.MM
qb = qr.QBoard(str(BOARD))
n0 = mz.neck_rule(qb, 1.5, 0.0)
n1 = mz.neck_rule(qb, 1.5, 0.5)
out = dict(schema=1, decision="D-680", board=str(BOARD),
           refs=list(n0.refs), min_w_nm=n0.min_w,
           reach_nm=dict(c0=n0.reach_nm, c1=n1.reach_nm))

P = lambda *xy: [(int(round(a * MM)), int(round(b * MM))) for a, b in xy]
IN = (58.513, 39.900)                 # U21.5 land centre, inside U21
X_EDGE = 58.995                       # U21 courtyard east edge

# C1 -- reach 0 behaves exactly as before
X, Y = np.meshgrid(np.linspace(56.0 * MM, 61.0 * MM, 120),
                   np.linspace(38.0 * MM, 42.0 * MM, 96))
out["c1_mask_reach_equals_mask_at_reach0"] = bool(
    (n0.mask_reach(X, Y) == n0.mask(X, Y)).all())
stray = P(IN, (59.200, 39.900))
out["c1_reach0_refuses_a_stray"] = (not n0.licensed(stray)[0])
out["c1_reach0_admits_contained"] = n0.licensed(P(IN, (58.900, 39.900)))[0]

# C2 -- the D-584 shape: a whole segment outside
d584 = P(IN, (59.100, 39.900), (59.400, 39.900))
ok, mm_out = n1.licensed(d584)
out["c2_d584_shape"] = dict(admitted=bool(ok), outside_mm=round(mm_out / 1e6, 4),
                            why="last TWO vertices outside -> a whole segment "
                                "lies outside every named courtyard")

# C3 -- leaves once, at the end, within reach
c3 = P(IN, (59.260, 39.900))
ok3, s3 = n1.licensed(c3)
out["c3_single_exit_within_reach"] = dict(admitted=bool(ok3),
                                          outside_mm=round(s3 / 1e6, 4))

# C4 -- same shape, stray longer than the reach
n_tiny = mz.neck_rule(qb, 1.5, 0.05)
ok4, s4 = n_tiny.licensed(c3)
out["c4_stray_over_reach"] = dict(reach_mm=0.05, admitted=bool(ok4),
                                  outside_mm=round(s4 / 1e6, 4))

# C5 -- starts outside
c5 = P((59.200, 39.900), (59.400, 39.900))
out["c5_starts_outside"] = dict(admitted=bool(n1.licensed(c5)[0]))

# C6 -- what the board already carries past that courtyard edge
out["c6_u21_courtyard_east_mm"] = X_EDGE
out["c6_existing_u21_6_neck"] = dict(
    net="/01_POWER_TREE/ACC_5V_RAW", width_mm=0.250,
    a_mm=[58.513, 40.400], b_mm=[59.023, 40.400],
    copper_reaches_x_mm=round(59.023 + 0.125, 4),
    past_courtyard_mm=round(59.023 + 0.125 - X_EDGE, 4),
    note="one segment; it MEETS U21's courtyard and real DRC passes it")
out["c6_mask_reach_grew"] = dict(
    at_reach_0=int(n0.mask_reach(X, Y).sum()),
    at_reach_0p5=int(n1.mask_reach(X, Y).sum()))
ok = (out["c1_mask_reach_equals_mask_at_reach0"]
      and out["c1_reach0_refuses_a_stray"]
      and out["c1_reach0_admits_contained"]
      and not out["c2_d584_shape"]["admitted"]
      and out["c3_single_exit_within_reach"]["admitted"]
      and not out["c4_stray_over_reach"]["admitted"]
      and not out["c5_starts_outside"]["admitted"])
out["all_controls_behaved"] = bool(ok)
print(json.dumps(out, indent=1))
Path("evidence/d680-neck-reach-controls.json").write_text(
    json.dumps(out, indent=1) + "\n", encoding="utf-8")
