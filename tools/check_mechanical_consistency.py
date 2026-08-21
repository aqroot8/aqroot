#!/usr/bin/env python3
"""AQROOT mechanical consistency check.

Extracts the real Edge.Cuts extent from the authoritative PCB and compares it
against the enclosure authority document, so a board dimension and an enclosure
dimension can never again drift apart unnoticed.

It deliberately CANNOT declare a fit from external dimensions alone.  An
external body dimension includes walls, bosses, ribs, tolerances, button
mechanisms and connector clearances; subtracting none of those and calling the
result a fit is exactly the mistake this script exists to prevent.  Fit is
reported UNKNOWN until an internal cavity dimension is published in the
authority document, at which point the real gate runs.

Usage:
    python tools/check_mechanical_consistency.py
    python tools/check_mechanical_consistency.py --pcb <file> --doc <file>

Exit codes: 0 = consistent (or fit unknown, which is not a failure),
            1 = a declared value disagrees with the measured board.
"""
import argparse
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_PCB = os.path.join(
    ROOT, 'hardware', 'beta-dm', 'kicad', 'aqroot-beta-dm', 'aqroot-Beta-DM.kicad_pcb')
DEFAULT_DOC = os.path.join(ROOT, '18 - Enclosure Field Slate v5.md')

SHAPES = re.compile(r'\((gr_line|gr_arc|gr_rect|gr_poly|gr_circle)\b')
POINT = re.compile(r'\((?:start|end|mid|center|xy) (-?[\d.]+) (-?[\d.]+)\)')


def edge_cuts_extent(path):
    """Return (width, length) of the Edge.Cuts bounding box, in mm."""
    with open(path, 'r', encoding='utf-8', errors='replace') as fh:
        s = fh.read()
    xs, ys = [], []
    for m in SHAPES.finditer(s):
        i = m.start()
        depth = 0
        j = i
        while j < len(s):
            c = s[j]
            if c == '(':
                depth += 1
            elif c == ')':
                depth -= 1
                if depth == 0:
                    break
            j += 1
        blk = s[i:j + 1]
        if '"Edge.Cuts"' not in blk:
            continue
        for p in POINT.finditer(blk):
            xs.append(float(p.group(1)))
            ys.append(float(p.group(2)))
    if not xs:
        raise SystemExit('no Edge.Cuts geometry found in %s' % path)
    return max(xs) - min(xs), max(ys) - min(ys)


def declared(doc):
    """Pull the declared values out of the authority table."""
    with open(doc, 'r', encoding='utf-8', errors='replace') as fh:
        t = fh.read()
    out = {}
    m = re.search(r'PCB_OUTLINE_MM:\s*([\d.]+)\s*x\s*([\d.]+)', t)
    if m:
        out['pcb'] = (float(m.group(1)), float(m.group(2)))
    m = re.search(r'ENCLOSURE_EXTERNAL_MM:\s*([\d.]+)\s*x\s*([\d.]+)\s*x\s*([\d.]+)', t)
    if m:
        out['ext'] = tuple(float(m.group(i)) for i in (1, 2, 3))
    m = re.search(r'INTERNAL_CAVITY_MM:\s*([\d.]+)\s*x\s*([\d.]+)\s*x\s*([\d.]+)', t)
    if m:
        out['cavity'] = tuple(float(m.group(i)) for i in (1, 2, 3))
    m = re.search(r'PCB_TO_WALL_CLEARANCE_MM:\s*([\d.]+)', t)
    if m:
        out['clearance'] = float(m.group(1))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--pcb', default=DEFAULT_PCB)
    ap.add_argument('--doc', default=DEFAULT_DOC)
    a = ap.parse_args()

    w, l = edge_cuts_extent(a.pcb)
    d = declared(a.doc)

    print('AQROOT MECHANICAL CONSISTENCY CHECK')
    print('   PCB file  : %s' % os.path.relpath(a.pcb, ROOT))
    print('   Authority : %s' % os.path.relpath(a.doc, ROOT))
    print()
    print('   PCB WIDTH             : %.2f mm   (measured Edge.Cuts)' % w)
    print('   PCB LENGTH            : %.2f mm   (measured Edge.Cuts)' % l)

    bad = False
    if 'pcb' in d:
        dl, dw = d['pcb']
        ok = (abs(dw - w) < 0.05 and abs(dl - l) < 0.05)
        print('   PCB DECLARED          : %.2f x %.2f mm   %s'
              % (dl, dw, 'matches' if ok else '*** DISAGREES WITH THE BOARD ***'))
        if not ok:
            bad = True
    else:
        print('   PCB DECLARED          : not declared in the authority document')

    if 'ext' in d:
        el, ew, eh = d['ext']
        print('   ENCLOSURE EXT WIDTH   : %.2f mm' % ew)
        print('   ENCLOSURE EXT LENGTH  : %.2f mm' % el)
        print('   ENCLOSURE EXT HEIGHT  : %.2f mm' % eh)
    else:
        el = ew = None
        print('   ENCLOSURE EXTERNAL    : not declared')

    print()
    if 'cavity' in d:
        cl, cw, ch = d['cavity']
        clr = d.get('clearance', 0.0)
        need_w = w + 2 * clr
        need_l = l + 2 * clr
        fits = (cw >= need_w and cl >= need_l)
        print('   INTERNAL CAVITY       : %.2f x %.2f x %.2f mm' % (cl, cw, ch))
        print('   PCB + 2x clearance    : %.2f x %.2f mm (clearance %.2f)'
              % (need_l, need_w, clr))
        print('   FIT STATUS            : %s' % ('PASS' if fits else 'FAIL'))
        if not fits:
            bad = True
    else:
        print('   INTERNAL CAVITY       : NOT PUBLISHED')
        print('   FIT STATUS            : UNKNOWN')
        print()
        print('   Fit cannot be computed from external dimensions. Publish')
        print('   INTERNAL_CAVITY_MM and PCB_TO_WALL_CLEARANCE_MM in the')
        print('   authority document and this check becomes a real gate.')
        if el and ew:
            print()
            print('   For information only, NOT a fit result: the external body is')
            print('   %.1f mm longer and %.1f mm wider than the bare board, and all'
                  % (el - l, ew - w))
            print('   of that budget is still unallocated to walls and mechanisms.')

    print()
    print('RESULT: %s' % ('INCONSISTENT' if bad else 'consistent'))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
