#!/usr/bin/env python3
"""AQROOT Full Beta v2 - FBV2-P1 mechanical review drawing.

Draws the enclosure cavity, the PCB outline and every FBV2-P1 mechanical
reservation into one legible SVG, in the P1 doc datum (origin lower-left,
Y up).  The KiCad layer plots beside it are the authority for what is IN the
board file; this drawing exists so the relationships can actually be read.

    python hardware/beta-v2/checks/p1_mech_render.py out.svg
"""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import p1_geometry as G

SCALE = 5.0          # px per mm
PAD = 26.0           # mm of paper around the cavity
LEGEND_W = 84.0      # mm of legend column


def build():
    x0, y0, x1, y1 = G.CAVITY
    W = (x1 - x0 + 2 * PAD + LEGEND_W) * SCALE
    Ht = (y1 - y0 + 2 * PAD) * SCALE
    ox, oy = (PAD - x0) * SCALE, (PAD - y0) * SCALE

    def X(v):
        return ox + v * SCALE

    def Y(v):
        return Ht - (oy + v * SCALE)

    s = []
    a = s.append
    a('<svg xmlns="http://www.w3.org/2000/svg" width="%.0f" height="%.0f" '
      'viewBox="0 0 %.0f %.0f">' % (W, Ht, W, Ht))
    a('<rect width="100%" height="100%" fill="#ffffff"/>')
    a('<g font-family="DejaVu Sans, Verdana, sans-serif">')

    def rect(r, stroke, fill='none', dash=None, w=1.0, op=1.0):
        d = ' stroke-dasharray="%s"' % dash if dash else ''
        a('<rect x="%.2f" y="%.2f" width="%.2f" height="%.2f" fill="%s" '
          'fill-opacity="%.2f" stroke="%s" stroke-width="%.2f"%s/>'
          % (X(r[0]), Y(r[3]), (r[2] - r[0]) * SCALE, (r[3] - r[1]) * SCALE,
             fill, op, stroke, w, d))

    def circ(cx, cy, dia, stroke, fill='none', dash=None, w=1.4, op=1.0):
        d = ' stroke-dasharray="%s"' % dash if dash else ''
        a('<circle cx="%.2f" cy="%.2f" r="%.2f" fill="%s" fill-opacity="%.2f" '
          'stroke="%s" stroke-width="%.2f"%s/>'
          % (X(cx), Y(cy), dia / 2.0 * SCALE, fill, op, stroke, w, d))

    def poly(pts, stroke, w=2.2, dash=None):
        d = ' stroke-dasharray="%s"' % dash if dash else ''
        pth = ' '.join('%.2f,%.2f' % (X(p[0]), Y(p[1])) for p in pts)
        a('<polyline points="%s" fill="none" stroke="%s" stroke-width="%.2f" '
          'stroke-linejoin="round" stroke-linecap="round"%s/>' % (pth, stroke, w, d))

    def txt(t, x, y, size=3.0, col='#222', anchor='middle', weight='normal'):
        a('<text x="%.2f" y="%.2f" font-size="%.1f" fill="%s" text-anchor="%s" '
          'font-weight="%s">%s</text>'
          % (X(x), Y(y) + size * SCALE * 0.12, size * SCALE * 0.42, col, anchor, weight,
             t.replace('&', '&amp;').replace('<', '&lt;')))

    # ---- cavity and board ------------------------------------------------
    rect(G.CAVITY, '#888', '#fbfbfb', dash='10 6', w=1.6)
    txt('ENCLOSURE CAVITY 75.0 x 155.0', (x0 + x1) / 2, y1 + 2.0, 3.0, '#666')
    rect((0, 0, G.BOARD_W, G.BOARD_H), '#111', '#ffffff', w=2.4)

    # ---- rear reservations ------------------------------------------------
    rect(G.BATTERY, '#c98a00', '#ffd98a', op=0.45, w=1.4)
    txt('BATTERY 57 x 75 x 8.0 MAX', 36, 62, 3.4, '#8a5f00', weight='bold')
    txt('rear, B.Cu <= 1.2 mm, no compression', 36, 57, 2.6, '#8a5f00')

    rect(G.SPEAKER, '#7a4fbf', '#d9c6f2', op=0.5, w=1.4)
    circ(58, 11, 20, '#7a4fbf', 'none', w=1.2)
    txt('SPEAKER D20 x 3', 59, 17.6, 2.6, '#4b2f80')
    txt('sealed cavity', 58, 4.0, 2.4, '#4b2f80')

    # ---- NFC --------------------------------------------------------------
    circ(G.NFC_CX, G.NFC_CY, G.NFC_METAL_D, '#0b6bcb', '#cfe4fb', dash='7 5', w=2.0, op=0.45)
    circ(G.NFC_CX, G.NFC_CY, G.NFC_CLEAR_D, '#0b6bcb', '#9ccaf7', w=2.4, op=0.45)
    rect((G.NFC_CX - 24, G.NFC_CY - 24, G.NFC_CX + 24, G.NFC_CY + 24), '#0b6bcb',
         dash='3 4', w=1.0)
    a('<line x1="%.2f" y1="%.2f" x2="%.2f" y2="%.2f" stroke="#0b6bcb" stroke-width="1"/>'
      % (X(G.NFC_CX - 3), Y(G.NFC_CY), X(G.NFC_CX + 3), Y(G.NFC_CY)))
    a('<line x1="%.2f" y1="%.2f" x2="%.2f" y2="%.2f" stroke="#0b6bcb" stroke-width="1"/>'
      % (X(G.NFC_CX), Y(G.NFC_CY - 3), X(G.NFC_CX), Y(G.NFC_CY + 3)))
    txt('NFC CLEAR D48', G.NFC_CX, G.NFC_CY + 9, 3.6, '#08498c', weight='bold')
    txt('METAL EXCLUSION D58', G.NFC_CX, G.NFC_CY + 4.4, 3.0, '#08498c')
    txt('centre %.1f, %.1f' % (G.NFC_CX, G.NFC_CY), G.NFC_CX, G.NFC_CY - 5.5, 2.8, '#08498c')
    txt('48 x 48 placement box', G.NFC_CX, G.NFC_CY - 10, 2.6, '#3f83c9')

    # ---- display / front --------------------------------------------------
    rect(G.DISPLAY, '#2f7d32', dash='6 4', w=1.4)
    txt('DISPLAY SHADOW (front)', (G.DISPLAY[0] + G.DISPLAY[2]) / 2, G.DISPLAY[1] + 3.0,
        2.8, '#2f7d32')

    # ---- 433 flex ---------------------------------------------------------
    rect(G.ANT433, '#b3202e', '#f6b3ba', op=0.8, w=1.2)
    txt('433 FLEX', -8.5, 25, 2.8, '#8c1622')
    txt('47 x 17', -8.5, 21.5, 2.4, '#8c1622')
    poly(G.ANT433_PATH, '#b3202e', 1.8, dash='5 3')
    txt('433 lead 44 / 100 mm', 26, 25.5, 2.5, '#8c1622')

    # ---- 915 coax ---------------------------------------------------------
    poly(G.COAX_PATH, '#d2691e', 3.2)
    for p in G.COAX_PATH:
        a('<circle cx="%.2f" cy="%.2f" r="2.6" fill="#d2691e"/>' % (X(p[0]), Y(p[1])))
    txt('915 COAX CHANNEL', 17.5, 88, 3.2, '#a04b12', anchor='start', weight='bold')
    txt('CBA-UFLSMA20IP, 200 mm', 17.5, 84, 2.7, '#a04b12', anchor='start')
    txt('routed 138.5 mm', 17.5, 80.5, 2.7, '#a04b12', anchor='start')

    # ---- SMA --------------------------------------------------------------
    circ(G.SMA_X, G.SMA_Y, G.SMA_WASHER_D, '#d2691e', '#ffd9b3', w=1.2, op=0.8)
    circ(G.SMA_X, G.SMA_Y, G.SMA_HOLE_D, '#a04b12', '#ffffff', w=1.6)
    txt('SMA', G.SMA_X + 11, G.SMA_Y + 1.5, 3.0, '#a04b12', anchor='start', weight='bold')
    txt('D6.5 panel hole, x=%.1f' % G.SMA_X, G.SMA_X + 11, G.SMA_Y - 2.5, 2.5, '#a04b12',
        anchor='start')

    # ---- IR ---------------------------------------------------------------
    rect(G.IR_TX_OPT, '#444', '#eeeeee', w=1.2, op=0.9)
    txt('IR TX', 52.25, 143.5, 2.6, '#333')
    rect((56.5, 140, 61.5, 148), '#000', '#cccccc', w=1.4, op=0.9)
    txt('BARRIER', 59.0, 143.5, 2.2, '#000')
    rect(G.IR_RX_OPT, '#444', '#eeeeee', w=1.2, op=0.9)
    txt('IR RX', 65.75, 143.5, 2.6, '#333')

    # ---- apertures --------------------------------------------------------
    rect(G.USB_AP, '#555', dash='4 3', w=1.0)
    txt('USB-C', 42, -2.2, 2.4, '#555')
    rect(G.USD_AP, '#555', dash='4 3', w=1.0)
    txt('microSD + 22 mm card travel', 14, -8.0, 2.4, '#555')
    rect(G.COMM_RECESS, '#555', dash='4 3', w=1.0)
    txt('J5 COMMUNITY RECESS', 65, 121, 2.4, '#555')

    # ---- bosses and ribs --------------------------------------------------
    for nm, bx, by in (('BOSS1', 40.0, 12.0), ('BOSS2', 59.0, 145.0)):
        circ(bx, by, 4.5, '#8b0000', '#ffb3b3', w=1.6, op=0.9)
        circ(bx, by, 2.2, '#8b0000', '#ffffff', w=1.4)
        txt(nm, bx, by - 4.6, 2.6, '#8b0000', weight='bold')
    for nm, r in (('RIB_R1', (67.20, 24.00, 70.70, 44.00)),
                  ('RIB_R2', (67.20, 45.00, 70.70, 64.00)),
                  ('RIB_R3', (67.20, 76.00, 70.70, 97.00)),
                  ('RIB_B1', (45.00, 21.20, 48.60, 23.30))):
        rect(r, '#0f7b6c', '#b9e6de', w=1.2, op=0.85)
        cx, cy = (r[0] + r[2]) / 2, (r[1] + r[3]) / 2
        txt(nm, cx, cy - 0.6, 2.2, '#0b5a4f')
    rect((-1.50, 24.00, 6.00, 110.00), '#d2691e', dash='5 4', w=1.0)
    txt('COAX_915_CHANNEL', 16.0, 66.0, 2.6, '#a04b12', anchor='start')

    # ---- modules ----------------------------------------------------------
    rect((1.055, 1.455, 16.945, 22.795), '#333', '#ffffff', w=1.2, op=0.0)
    txt('U8 915', 9.0, 20.0, 2.6, '#111', weight='bold')
    rect((18.055, 1.455, 33.945, 22.795), '#333', '#ffffff', w=1.2, op=0.0)
    txt('U7 433', 26.0, 20.0, 2.6, '#111', weight='bold')
    a('<circle cx="%.2f" cy="%.2f" r="3.2" fill="none" stroke="#d2691e" stroke-width="1.6"/>'
      % (X(G.U8_IPEX[0]), Y(G.U8_IPEX[1])))
    txt('IPEX', 12.6, 16.6, 2.2, '#a04b12', anchor='start')
    rect((1.205, 47.705, 4.795, 52.295), '#111', '#ffffff', w=1.0, op=0.0)
    txt('MK1', 8.0, 50.0, 2.4, '#111', anchor='start')

    # ---- legend -----------------------------------------------------------
    lx = x1 + 6.0
    ly = y1 - 4.0
    txt('AQROOT FULL BETA v2 - FBV2-P1 MECHANICAL REVIEW', lx, ly, 3.6, '#111',
        anchor='start', weight='bold')
    ly -= 5.5
    for line, col in (
            ('Doc datum: origin at the lower-left board corner, X right, Y up, mm.', '#444'),
            ('Y_kicad = 148.000 - Y_doc.  NOTHING HERE IS ROUTED COPPER.', '#444'),
            ('', '#444'),
            ('NFC        clear D48 / metal exclusion D58, centre 30.8, 124.5', '#08498c'),
            ('           48 x 48 box kept as the placement tolerance envelope', '#08498c'),
            ('915        U8 IPEX (9.0, 16.6) -> left channel -> SMA (5.0, 148.0)', '#a04b12'),
            ('           routed 138.5 mm + 15 mm service loop = 153.5 of 200 mm', '#a04b12'),
            ('           tightest clearance to the D58 exclusion: 0.600 mm', '#a04b12'),
            ('433        U7 IPEX (26.0, 16.6) -> left wall flex, 44 of 100 mm', '#8c1622'),
            ('battery    60 x 75 x 8.0, UNCHANGED, zero overlap with the D48 clear', '#8a5f00'),
            ('speaker    D20 x 3 sealed, UNCHANGED, 80.9 mm from the loop', '#4b2f80'),
            ('retention  2 x M2 through-board + edge-capture rails + 4 rib pads', '#8b0000'),
            ('           NO third legal M2 site exists - escalated to the CTO', '#8b0000'),
            ('display    3.34 mm left of the board centreline - ACCEPTED', '#2f7d32'),
    ):
        txt(line, lx, ly, 2.8, col, anchor='start')
        ly -= 4.2

    a('</g></svg>')
    return '\n'.join(s)


if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else 'mech.svg'
    open(out, 'w', encoding='utf-8').write(build())
    print('wrote', out)
