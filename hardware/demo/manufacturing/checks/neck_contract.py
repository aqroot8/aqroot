#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AQROOT Demo -- the pad-escape necking lever is OFF by default and NON-PERTURBING.

The `--neck` lever added to `maze3d` in D-584 lets a pad that has NO legal
launch at its net's contract width launch instead at the `.kicad_dru`
pad-escape necking minimum.  That is a genuine widening of what the router may
propose, so the contract this file pins is the OTHER half of it: with the lever
unset the module must behave EXACTLY as the version that produced every
promoted route up to and including D-583.

Three claims, each measured rather than asserted:

  N1  the necking rule the router uses is READ from the board's own
      `.kicad_dru` -- same minimum width, same ten courtyards, no transcription;
  N2  with `neck=None`, `pad_escapes` returns escapes IDENTICAL to the D-583
      module's, pad for pad and layer for layer, over every pad that owns an
      open edge -- so no accepted route can move;
  N3  with the lever ON, a neck is offered ONLY where the full-width set is
      empty AND the pad is inside one of the named courtyards, and every
      offered stub is within the length bound AND lies wholly inside a named
      courtyard -- the condition under which the board's own rule licences it,
      measured after D-584's first cut returned three real `track_width` DRC
      errors on the 0.764 mm of a `U9.10` stub that strayed outside `U9`.

N2 compares against the ACTUAL D-583 source, extracted from git, not against a
remembered result.  Run from anywhere:

    python3 hardware/demo/manufacturing/checks/neck_contract.py [--rev REV]
"""

import argparse
import importlib.util
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
MANU = ROOT / "hardware/demo/manufacturing"
BOARD = ROOT / "hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb"
DRU = BOARD.with_suffix(".kicad_dru")
BASE_REV = "c5f983f"                      # the D-583 ledger commit

sys.path.insert(0, str(MANU))
sys.path.insert(0, str(ROOT / "hardware/beta-v2/checks"))


def load_rev_module(rev, name="maze3d_base"):
    """Import `maze3d.py` as it stands at `rev`, without touching the worktree."""
    src = subprocess.run(
        ["git", "-C", str(ROOT), "show",
         "%s:hardware/demo/manufacturing/maze3d.py" % rev],
        check=True, capture_output=True, text=True).stdout
    # `maze3d` resolves the beta-v2 `checks/` directory from its OWN location
    # with `parents[3]`, so the extracted copy is written at the SAME depth
    # inside a throwaway tree.  Anywhere shallower and the import raises
    # IndexError before a single escape has been compared.
    root = Path(tempfile.mkdtemp(prefix="aqroot-neck-base-"))
    tmp = root / "hardware/demo/manufacturing" / (name + ".py")
    tmp.parent.mkdir(parents=True, exist_ok=True)
    tmp.write_text(src, encoding="utf-8")
    spec = importlib.util.spec_from_file_location(name, tmp)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def key(escapes):
    """The part of an escape set that must not move: where and how wide."""
    return [(e["layer"], e["x"], e["y"], e["w"], round(e["ln"], 3),
             tuple(e.get("path") or ())) for e in escapes]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rev", default=BASE_REV)
    ap.add_argument("--limit", type=int, default=12)
    ap.add_argument("-o", "--out", type=Path)
    a = ap.parse_args()

    import qrouter as qr
    import incremental_router as ir
    import maze3d as mz
    from route_maze_batch import net_contract
    base = load_rev_module(a.rev)

    qb = qr.QBoard(str(BOARD))
    ir.inject_existing_via_obstacles(qb)
    results = {}

    # -- N1: the rule is the board's own ----------------------------------- #
    nk = mz.neck_rule(qb)
    text = DRU.read_text(encoding="utf-8")
    m = re.search(r'\(rule "Pad-escape necking - width[^"]*"\s*'
                  r'\(constraint track_width \(min ([0-9.]+)mm\)\)\s*'
                  r'\(condition "([^"]*)"\)\)', text)
    want_min = int(round(float(m.group(1)) * qr.MM))
    want_refs = tuple(re.findall(r"A\.intersectsCourtyard\('([^']+)'\)", m.group(2)))
    results["N1"] = dict(
        ok=(nk is not None and nk.min_w == want_min
            and tuple(nk.refs) == want_refs),
        dru_min_nm=want_min, router_min_nm=(nk and nk.min_w),
        dru_refs=list(want_refs), router_refs=list(nk.refs) if nk else None,
        courtyards_found=sorted(nk.polys) if nk else None)

    # -- N2 / N3 over every pad that owns an open edge ---------------------- #
    ledger = json.loads(subprocess.run(
        [sys.executable, str(MANU / "routing_ledger.py"), "--board", str(BOARD)],
        check=True, capture_output=True, text=True).stdout)
    open_nets = [r["net"] for r in ledger["nets"] if r["open_edges"] > 0]

    moved, offered, pads_seen = [], [], 0
    for net in open_nets:
        c = net_contract(qb.b, net)
        islands = mz.net_islands(qb, net)
        if len(islands) < 2:
            continue
        main_isl = max(islands, key=len)
        pads = [p for g in islands if g is not main_isl for p in g]
        args = (c["width"], c["clr"], c["clr"], c["via_dia"], c["via_drill"])
        f_base = base.Field(qb, net, *args, G=100000, layers=c["layers"])
        f_off = mz.Field(qb, net, *args, G=100000, layers=c["layers"])
        f_on = mz.Field(qb, net, *args, G=100000, layers=c["layers"], neck=nk)
        for p in pads:
            pads_seen += 1
            b = key(base.pad_escapes(qb, f_base, p, None, a.limit))
            o = key(mz.pad_escapes(qb, f_off, p, None, a.limit))
            if b != o:
                moved.append(dict(net=net, pad=p["ref"],
                                  base=len(b), off=len(o)))
            on = mz.pad_escapes(qb, f_on, p, None, a.limit)
            necked = [e for e in on if e.get("neck")]
            if necked:
                offered.append(dict(
                    net=net, pad=p["ref"], full_width_escapes=len(o),
                    in_courtyard=nk.contains(p["x"], p["y"]),
                    stubs=[dict(layer=e["layer"],
                                width_mm=round(e["w"] / 1e6, 3),
                                stub_mm=round(e["ln"] / 1e6, 3),
                                outside_courtyard_mm=e["neck_outside_mm"])
                           for e in necked]))
        print("  %-46s %d pads" % (net, len(pads)), file=sys.stderr, flush=True)

    results["N2"] = dict(ok=not moved, pads_compared=pads_seen,
                         base_rev=a.rev, moved=moved[:20])
    # A necked stub must be a LAST RESORT (no full-width escape), start at a pad
    # the rule names, stay within the length bound, and -- the clause D-584's
    # first cut lacked -- lie WHOLLY inside a named courtyard.  KiCad matches
    # `intersectsCourtyard` per track object, so a stub that leaves the
    # courtyard is judged by the netclass width floor and fails DRC; that is not
    # a theory, it is the three `track_width` errors the first run returned.
    bad = [o for o in offered
           if o["full_width_escapes"] or not o["in_courtyard"]
           or any(s["stub_mm"] > nk.max_nm / 1e6 + 1e-9 for s in o["stubs"])
           or any(s["outside_courtyard_mm"] != 0.0 for s in o["stubs"])]
    results["N3"] = dict(ok=not bad, neck_max_mm=nk.max_nm / 1e6,
                         pads_offered_a_neck=len(offered),
                         violations=bad, offered=offered)

    out = dict(schema=1, board=str(BOARD), board_sha256=ledger["board_sha256"],
               checks=results,
               all_pass=all(v["ok"] for v in results.values()))
    text = json.dumps(out, indent=1, sort_keys=True, default=str)
    if a.out:
        a.out.write_text(text + "\n", encoding="utf-8")
    print(text)
    for k in ("N1", "N2", "N3"):
        print("  %s %s" % (k, "PASS" if results[k]["ok"] else "FAIL"),
              file=sys.stderr)
    return 0 if out["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
