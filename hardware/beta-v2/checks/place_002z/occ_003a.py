# -*- coding: utf-8 -*-
"""FBV2-P2-003A / D-273 -- READ-ONLY B.Cu occupancy map (no wave, no copper).

Builds ONE coarse blocked-grid via qb.grid() for a BAT_PROTECTED_P 1.50 mm
trunk over the working window and prints it as ASCII so the genuinely free
long-route lanes around the western control block are visible.  This lays no
copper and runs no search.
"""
import os, sys, math
SP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, SP)
import qrouter as QR
import battery_route_plan as PL

BOARD = os.path.join(SP, 'w', 'c3repro003a_parent', 'aqroot-Beta-v2.kicad_pcb')
NET = PL.N + 'BAT_PROTECTED_P'
W150 = 1500000
CP, CT = 200000, 300000


def main():
    qb = QR.QBoard(BOARD)
    qb.wide_nets = frozenset(PL.N + n for n in ('BAT_CONNECTOR_P', 'BAT_RAW',
                             'BAT_MID', 'BAT_SENSE', 'BAT_PROTECTED_P'))
    G = 500000  # 0.5 mm cells -- coarse, just to see lanes
    x0, y0, x1, y1 = 0, 55000000, 72000000, 100000000
    blk = qb.grid('B', NET, W150, CP, CT, x0, y0, x1, y1, G)
    ny, nx = blk.shape
    marks = {}
    for ref in ('R75.2', 'D9.1'):
        p = qb.pads.get((NET, ref))
        if p:
            marks[(int((p['x'] - x0) // G), int((p['y'] - y0) // G))] = ref[0]
    # reservation end + node centroid + node west edge
    for (mx, my, ch) in ((10800000, 73000000, 'r'),   # reservation staging end
                         (58360000, 75080000, 'N'),   # node centroid
                         (38480000, 75000000, 'W')):   # node west edge (approx)
        marks[(int((mx - x0) // G), int((my - y0) // G))] = ch
    print('B.Cu occupancy  x %.0f..%.0f  y %.0f..%.0f mm  G=%.2f  (%dx%d)'
          % (x0 / 1e6, x1 / 1e6, y0 / 1e6, y1 / 1e6, G / 1e6, nx, ny))
    print('  #=blocked  .=free   S=R75.2 D=D9.1 r=resv-end W=node-west N=node-centroid')
    # x axis ruler every 10mm
    hdr = '     '
    for i in range(nx):
        xmm = (x0 + i * G) / 1e6
        hdr += ('|' if abs(xmm - round(xmm / 10) * 10) < 0.25 and i % 2 == 0 else ' ')
    print(hdr)
    for j in range(ny):
        ymm = (y0 + j * G) / 1e6
        row = '%5.1f' % ymm
        for i in range(nx):
            if (i, j) in marks:
                row += marks[(i, j)]
            else:
                row += '#' if blk[j, i] else '.'
        print(row)
    return 0


if __name__ == '__main__':
    sys.exit(main())
