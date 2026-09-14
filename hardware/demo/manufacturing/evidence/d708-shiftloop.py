#!/usr/bin/env python3
"""Iteratively resolve an apply_part_shift RELEASE closure: re-run, adding a
--release-point for every RELEASE_WOULD_STRAND refusal, until PASS or fixpoint."""
import json, shutil, subprocess, sys, os
from pathlib import Path
src, dest, ref, dx, dy, rot = sys.argv[1:7]
nets = [n for n in sys.argv[7:] if not n.startswith("+")]
extra = [n[1:] for n in sys.argv[7:] if n.startswith("+")]
MAN = Path(__file__).resolve()
CWD = "/home/aqroot8/aqroot-demo/hardware/demo/manufacturing"
rep = "/tmp/aq/shiftloop.json"
pts, seen = [], set()
for it in range(1, 41):
    if Path(dest).exists():
        shutil.rmtree(dest)
    Path(dest).mkdir(parents=True)
    for s in ("kicad_pcb", "kicad_dru", "kicad_pro", "kicad_prl"):
        shutil.copy(Path(src) / ("aqroot-Beta-v2." + s), Path(dest))
    if os.path.exists(rep):
        os.remove(rep)
    cmd = [sys.executable, "apply_part_shift.py",
           "--board", str(Path(dest) / "aqroot-Beta-v2.kicad_pcb"),
           "--ref", ref, "--dx-nm", dx, "--dy-nm", dy, "--rot-deg", rot,
           "--release", "--apply", "--report", rep]
    for n in nets:
        cmd += ["--release-net", n]
    for p in pts:
        cmd += ["--release-point", p]
    cmd += extra
    subprocess.run(cmd, cwd=CWD, capture_output=True)
    if not os.path.exists(rep):
        print("NO REPORT -- tool failed"); sys.exit(2)
    d = json.load(open(rep))
    print("iter %d -> %s released=%d refusals=%d"
          % (it, d["verdict"], d["released_count"], len(d.get("release_refusals", []))))
    if d["verdict"] == "PASS":
        break
    new = {"%s:%s,%s" % (r["net"], r["at_mm"][0], r["at_mm"][1])
           for r in d.get("release_refusals", [])
           if r["reason"] == "RELEASE_WOULD_STRAND"}
    if not new - seen:
        for r in d.get("release_refusals", []):
            print("  REF", r)
        break
    seen |= new
    pts = sorted(seen)
print("verdict", d["verdict"], "released", d["released_count"],
      "courtyard_new", d.get("courtyard_overlaps_new"))
for o in d.get("released_objects", []):
    print("   ", o)
json.dump({"release_points": pts, "release_nets": nets, "extra": extra},
          open("/tmp/aq/shiftloop-spec.json", "w"), indent=1)
