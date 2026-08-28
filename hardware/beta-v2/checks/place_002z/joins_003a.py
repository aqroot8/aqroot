# -*- coding: utf-8 -*-
"""FBV2-P2-003A / D-273 -- READ-ONLY: exact node-copper join points.

For each proposed channel-exit waypoint, report the nearest point on the large
eastern BAT_PROTECTED_P node copper (cluster 1) -- the true continuous join
coordinate a bounded family would target.  No routing, no copper laid.
"""
import os, sys, math
SP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, SP)
import qrouter as QR
import path_role_util as RU
import battery_route_plan as PL

BOARD = os.path.join(SP, 'w', 'c3repro003a_parent', 'aqroot-Beta-v2.kicad_pcb')
NET = PL.N + 'BAT_PROTECTED_P'

# candidate channel-exit waypoints (mm) just west of the node, per latitude
EXITS = {'north': (37.0, 64.0), 'mid': (36.0, 75.0), 'south': (37.0, 89.0),
         'chan_w': (30.0, 75.0)}


def main():
    qb = QR.QBoard(BOARD)
    # restrict "node" to cluster1 by excluding the small west/thin copper:
    # nearest_on_net over the whole net, but node copper dominates x>=38.
    for name, (xm, ym) in EXITS.items():
        x, y = int(xm * 1e6), int(ym * 1e6)
        best = RU.nearest_on_net(qb.b, NET, 'B.Cu', x, y)
        if best:
            d, px, py, t = best
            print('exit %-7s (%.2f,%.2f) -> nearest BPP copper (%.3f,%.3f)  '
                  'gap %.3f mm  on seg (%.2f,%.2f)-(%.2f,%.2f) w=%.2f'
                  % (name, xm, ym, px / 1e6, py / 1e6, d / 1e6,
                     t.GetStart().x / 1e6, t.GetStart().y / 1e6,
                     t.GetEnd().x / 1e6, t.GetEnd().y / 1e6, t.GetWidth() / 1e6))
    return 0


if __name__ == '__main__':
    sys.exit(main())
