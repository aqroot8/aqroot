#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AQROOT Demo -- READ-ONLY: what does a corridor's WHOLE-TRACK cut cost the
CUT NET, counted by KiCad's own connectivity engine?

D-641.  `screen_corridor_detour.py` demands that every cut track be RELAID
between its own two ends, and calls the corridor `UNRELAYABLE` when one will
not go back.  For a POUR net that demand can be simply wrong -- D-639 measured
`GND C37.2` closing because KiCad's real refill flowed the `B.Cu` pour into the
channel a detour had vacated -- so before a relay refusal is read as a wall,
ask what the cut actually COSTS.
`screen_segment_evict.connectivity_price` already answers exactly that question
for a disc cut; a corridor cut is the same question with `stubs_mm: []`, the
whole track gone and nothing put back.

ONE NET PER PROCESS.  `pcbnew.LoadBoard` called a second time in one
interpreter hands back an unwrapped `SwigPyObject`, so the driver re-execs
itself once per net and once for the union.  Nothing here touches the
authoritative board: every cut is applied to a copy in a temporary directory
that is then thrown away.

    python3 screen_cut_price.py SURVEY.json OUT.json
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parents[0]
ROOT = Path(__file__).resolve().parents[3]
BOARD = ROOT / "hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb"


def collect(doc):
    cuts = []
    for rec in doc["nets"]:
        for e in rec["edges"]:
            for o in (e.get("minimal") or {}).get("objects", []):
                cuts.append(dict(net=o["net"], a_mm=o["a_mm"], b_mm=o["b_mm"],
                                 stubs_mm=[], mm=o["mm"], layer=o["lkey"]))
    return cuts


def child():
    sys.path.insert(0, str(HERE))
    sys.path.insert(0, str(ROOT / "hardware/beta-v2/checks"))
    import pcbnew                                          # noqa: F401
    import qrouter                                         # noqa: F401
    from screen_segment_evict import connectivity_price
    cuts = json.loads(Path(sys.argv[2]).read_text())
    with tempfile.TemporaryDirectory() as td:
        r = connectivity_price(BOARD, cuts, td)
    Path(sys.argv[3]).write_text(json.dumps(r, sort_keys=True))


def price(cuts, tag):
    with tempfile.TemporaryDirectory() as td:
        ci = Path(td) / "cuts.json"
        co = Path(td) / "out.json"
        ci.write_text(json.dumps(cuts))
        p = subprocess.run([sys.executable, __file__, "--child", str(ci),
                            str(co)], capture_output=True)
        if not co.exists():
            return dict(error="child failed", tag=tag,
                        stderr=p.stderr.decode()[-400:])
        return json.loads(co.read_text())


def main():
    survey, out = Path(sys.argv[1]), Path(sys.argv[2])
    doc = json.loads(survey.read_text())
    cuts = collect(doc)
    by_net = {}
    for c in cuts:
        by_net.setdefault(c["net"], []).append(c)
    res = dict(schema=1, survey=str(survey),
               survey_board_sha256=doc["board_sha256"],
               board=str(BOARD),
               question=("does removing this corridor cut cost the CUT NET any "
                         "connectivity at all -- counted by KiCad's own "
                         "BuildConnectivity over that net's pads, on a scratch "
                         "copy, against the fill that is really on the board"),
               method=("screen_segment_evict.connectivity_price with "
                       "stubs_mm: [] -- the whole track goes, nothing is put "
                       "back, no relay; one net per child process"),
               cut_tracks=len(cuts),
               per_net={n: price(cs, n) for n, cs in sorted(by_net.items())},
               whole_cut=price(cuts, "ALL"))
    out.write_text(json.dumps(res, indent=1, sort_keys=True) + "\n")
    print(json.dumps(res, indent=1, sort_keys=True))


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--child":
        child()
    else:
        main()
