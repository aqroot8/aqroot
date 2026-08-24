#!/usr/bin/env python3
"""FBV2-P1-002 - rebuild the MK1 acoustic padstack so KiCad 10 accepts it.

P1-O4: pad 4's GND ring was drawn as a STROKED circle primitive inside a custom
pad.  A stroked circle is an annulus - two boundaries - and KiCad 10's padstack
validator requires a custom pad to resolve to ONE filled polygon.  The same
defect applies to the separate annular paste aperture.  Two DRC errors.

The electrical and acoustic geometry does not change:

  copper GND ring   ID 1.05 / OD 1.65 mm   (PUI DMM-4026-B-I2S-R drawing)
  acoustic opening  Oe1.05 mm NPTH, concentric
  paste pullback    ID 1.25, i.e. 0.10 mm back from the copper inner edge

What changes is only HOW that geometry is expressed:

  * pad 4 becomes a plain FILLED Oe1.65 mm circular SMD pad.  The concentric
    Oe1.05 mm NPTH drills the centre out, so the finished copper is the same
    ID 1.05 / OD 1.65 annulus.  A plain circle is not a custom pad at all, so
    the validator has nothing to reject.  This is NOT a plated through hole -
    the hole stays non-plated and the pad stays SMD.
  * the paste aperture becomes ONE custom pad carrying ONE filled C-shaped
    polygon: the ID 1.25 / OD 1.65 ring with a 20 deg web at the far side.  A
    C is a single simple polygon.  The pad's anchor is a Oe0.20 mm circle sat
    ON the ring band at the point opposite the web, so anchor and primitive
    are one connected region.  Paste coverage 0.860 mm^2 = 67.6 % of the
    copper ring (was 71.6 % for the full annulus); stencil area ratio for the
    0.20 mm band on a 0.12 mm foil is 0.71, above the 0.66 release floor.
  * the NPTH stops opening the solder mask on the COMPONENT side, where pad 4
    already opens it.  Keeping both produced a third error - "rear solder mask
    aperture bridges items with different nets", the netless NPTH aperture
    sitting inside the GND pad's aperture.  The mask opening on the ACOUSTIC
    side, which the gasket needs, is unchanged.
"""
import math, io, os, re

RING_ID_CU, RING_OD = 1.05, 1.65
PASTE_ID = 1.25
WEB_DEG = 20.0
SEG_DEG = 3.0


def c_polygon(cy_sign):
    """C-shaped paste annulus, in pad-local coordinates.

    cy_sign is +1 when the ring centre sits at local +Y (library frame) and
    -1 when it sits at local -Y (the board stores this footprint mirrored).
    The anchor is at local (0, 0), i.e. on the ring at the near side, so the
    web is placed at the far side.
    """
    r_out, r_in = RING_OD / 2.0, PASTE_ID / 2.0
    r_mid = (r_out + r_in) / 2.0
    cy = cy_sign * r_mid
    near = math.degrees(math.atan2(-cy, 0.0))      # anchor bearing from centre
    far = near + 180.0
    a0, a1 = far + WEB_DEG / 2.0, far + 360.0 - WEB_DEG / 2.0
    n = max(2, int((a1 - a0) / SEG_DEG))
    pts = []
    for i in range(n + 1):
        a = math.radians(a0 + (a1 - a0) * i / n)
        pts.append((r_out * math.cos(a), cy + r_out * math.sin(a)))
    for i in range(n, -1, -1):
        a = math.radians(a0 + (a1 - a0) * i / n)
        pts.append((r_in * math.cos(a), cy + r_in * math.sin(a)))
    return pts, r_mid


def fmt(v):
    s = '%.5f' % v
    s = s.rstrip('0').rstrip('.')
    return s if s not in ('', '-0') else '0'


def paste_pad(tab, port_y, uuid):
    """Emit the replacement paste pad.  port_y is the acoustic port's Y in the
    footprint's own frame (+1 in the library, -1 in the board's mirrored copy)."""
    sign = 1 if port_y > 0 else -1
    pts, r_mid = c_polygon(sign)
    anchor_y = port_y - sign * r_mid
    ind = '\t' * tab
    out = [f'{ind}(pad "" smd custom',
           f'{ind}\t(at 0 {fmt(anchor_y)})',
           f'{ind}\t(size 0.2 0.2)',
           f'{ind}\t(layers "{"F" if sign > 0 else "B"}.Paste")',
           f'{ind}\t(options',
           f'{ind}\t\t(clearance outline)',
           f'{ind}\t\t(anchor circle)',
           f'{ind}\t)',
           f'{ind}\t(primitives',
           f'{ind}\t\t(gr_poly',
           f'{ind}\t\t\t(pts']
    for i in range(0, len(pts), 4):
        chunk = ' '.join('(xy %s %s)' % (fmt(x), fmt(y)) for x, y in pts[i:i + 4])
        out.append(f'{ind}\t\t\t\t{chunk}')
    out += [f'{ind}\t\t\t)',
            f'{ind}\t\t\t(width 0)',
            f'{ind}\t\t\t(fill yes)',
            f'{ind}\t\t)',
            f'{ind}\t)',
            f'{ind}\t(uuid "{uuid}")',
            f'{ind})']
    return '\n'.join(out)


def paste_area():
    r_out, r_in = RING_OD / 2.0, PASTE_ID / 2.0
    ring = math.pi * (r_out ** 2 - r_in ** 2) * (360.0 - WEB_DEG) / 360.0
    cu = math.pi * ((RING_OD / 2) ** 2 - (RING_ID_CU / 2) ** 2)
    return ring, cu, 100.0 * ring / cu
