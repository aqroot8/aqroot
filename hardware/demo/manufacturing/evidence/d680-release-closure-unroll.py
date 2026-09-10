#!/usr/bin/env python3
"""Unroll a --release closure: run apply_part_shift, read the RELEASE_WOULD_STRAND
points it names, add them as --release-point, repeat.  Stops when the closure
terminates or when a refusal names a PAD -- which is the tool telling us the
chain ends on a land the move does not touch, and is not ours to release."""
import json, subprocess, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
CAND = HERE / "cand.kicad_pcb"
SRC = Path("/home/aqroot8/aqroot-demo/hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2")

ref, dx, dy = sys.argv[1], sys.argv[2], sys.argv[3]
nets = sys.argv[4].split(",")
BARE = len(sys.argv) > 5 and sys.argv[5] == "--bare"
bare = []
report = HERE / ("%s.json" % ref.lower())
points = []
for rnd in range(12):
    cmd = [sys.executable, str(HERE.parents[2] / "apply_part_shift.py"),
           "--board", str(CAND), "--ref", ref, "--dx-nm", dx, "--dy-nm", dy,
           "--release", "--apply", "--report", str(report)]
    for n in nets:
        cmd += ["--release-net", n]
    for (n, x, y) in points:
        cmd += ["--release-point", "%s:%s,%s" % (n, x, y)]
    for q in bare:
        cmd += ["--release-bare-pad", q]
    subprocess.run(cmd, capture_output=True, text=True)
    d = json.loads(report.read_text())
    if d["verdict"] == "PASS" or d["applied"]:
        print("round %d: %s applied=%s released=%d"
              % (rnd, d["verdict"], d["applied"], d["released_count"]))
        print(json.dumps(d["released_objects"], indent=1))
        sys.exit(0)
    ref_ = [r for r in d["release_refusals"]]
    pad_stops = [r for r in ref_ if r.get("pads")]
    if pad_stops:
        if BARE:
            for r in pad_stops:
                for q in r["pads"]:
                    if q not in bare:
                        bare.append(q)
            print("round %d: naming bare pads %s" % (rnd, bare))
            continue
        print("round %d: STOPS AT A PAD -- %s" % (rnd, json.dumps(pad_stops)))
        sys.exit(2)
    new = [(r["net"], r["at_mm"][0], r["at_mm"][1]) for r in ref_
           if r["reason"] == "RELEASE_WOULD_STRAND"]
    new = [p for p in new if p not in points]
    if not new:
        print("round %d: no progress; refusals %s" % (rnd, json.dumps(ref_)[:400]))
        sys.exit(3)
    points += new
    print("round %d: +%d points (%d total)" % (rnd, len(new), len(points)))
print("did not converge")
sys.exit(4)
