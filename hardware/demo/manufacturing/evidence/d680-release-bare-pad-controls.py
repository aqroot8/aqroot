#!/usr/bin/env python3
"""D-680 CONTROLS for apply_part_shift.py --release-bare-pad.  READ-ONLY apart
from a private copy of the board in a temp directory.

C1  WITHOUT the flag the move is REFUSED, with RELEASE_WOULD_STRAND naming the
    stationary land -- byte for byte the pre-D-680 behaviour.
C2  WITH the flag naming that land the move is APPLIED, and the land is reported
    in `bare_pads_released`, so what the transaction now owes is written down.
C3  the flag does NOT admit a point where a TRACK still survives: naming a land
    whose point still has a surviving track is still refused.
"""
import json, shutil, subprocess, sys, tempfile
from pathlib import Path
HERE = Path(__file__).resolve().parents[1]
SRC = HERE.parent / "kicad/aqroot-demo/aqroot-Beta-v2"
APP = HERE / "apply_part_shift.py"
# The release closure of R100's move, UNROLLED BY THE TOOL ITSELF: run it, take
# the RELEASE_WOULD_STRAND points it names that are NOT on a pad, add them as
# --release-point, repeat.  Nothing here is transcribed.
POINTS = []


def run(bare, extra_points=()):
    tmp = Path(tempfile.mkdtemp(prefix="bare-"))
    for ext in (".kicad_pcb", ".kicad_dru", ".kicad_pro"):
        shutil.copy(SRC.with_suffix(ext), tmp / ("b" + ext))
    rep = tmp / "r.json"
    cmd = [sys.executable, str(APP), "--board", str(tmp / "b.kicad_pcb"),
           "--ref", "R100", "--dx-nm", "400000", "--dy-nm", "9400000",
           "--release", "--release-net", "/01_POWER_TREE/ACC_5V_FB",
           "--release-net", "GND", "--apply", "--report", str(rep)]
    for n, x, y in list(POINTS) + list(extra_points):
        cmd += ["--release-point", "%s:%s,%s" % (n, x, y)]
    for q in bare:
        cmd += ["--release-bare-pad", q]
    subprocess.run(cmd, capture_output=True, text=True)
    d = json.loads(rep.read_text())
    shutil.rmtree(tmp, ignore_errors=True)
    return d


for _ in range(12):
    _d = run([])
    _new = [(r["net"], repr(r["at_mm"][0]), repr(r["at_mm"][1]))
            for r in _d["release_refusals"]
            if r["reason"] == "RELEASE_WOULD_STRAND" and not r.get("pads")]
    _new = [q for q in _new if q not in POINTS]
    if not _new:
        break
    POINTS += _new

out = {"schema": 1, "decision": "D-680",
       "closure_points_named_by_the_tool": [[n, x, y] for n, x, y in POINTS],
       "what": "apply_part_shift.py --release-bare-pad",
       "move": "R100 +0.400 / +9.400 mm"}
a = run([])
out["c1_without_the_flag"] = dict(
    verdict=a["verdict"], applied=a["applied"],
    refusals=a["release_refusals"])
b = run(["R99.2"])
out["c2_with_the_flag"] = dict(
    verdict=b["verdict"], applied=b["applied"],
    released_count=b["released_count"],
    bare_pads_released=b.get("bare_pads_released"),
    release_bare_pads_requested=b.get("release_bare_pads_requested"),
    refusals=b["release_refusals"])
# C3: the same flag with the closure NOT unrolled -- a surviving TRACK is still
# a refusal, so naming the land buys nothing where the chain is still attached
c = subprocess_out = None
tmp = Path(tempfile.mkdtemp(prefix="bare3-"))
for ext in (".kicad_pcb", ".kicad_dru", ".kicad_pro"):
    shutil.copy(SRC.with_suffix(ext), tmp / ("b" + ext))
rep = tmp / "r.json"
subprocess.run([sys.executable, str(APP), "--board", str(tmp / "b.kicad_pcb"),
                "--ref", "R100", "--dx-nm", "400000", "--dy-nm", "9400000",
                "--release", "--release-net", "/01_POWER_TREE/ACC_5V_FB",
                "--release-net", "GND", "--release-bare-pad", "R99.2",
                "--apply", "--report", str(rep)], capture_output=True, text=True)
c = json.loads(rep.read_text())
shutil.rmtree(tmp, ignore_errors=True)
out["c3_surviving_track_is_still_a_refusal"] = dict(
    verdict=c["verdict"], applied=c["applied"],
    refusals=c["release_refusals"])
out["all_controls_behaved"] = bool(
    out["c1_without_the_flag"]["verdict"] == "FAIL"
    and not out["c1_without_the_flag"]["applied"]
    and any(r.get("pads") == ["R99.2"]
            for r in out["c1_without_the_flag"]["refusals"])
    and out["c2_with_the_flag"]["applied"]
    and out["c2_with_the_flag"]["bare_pads_released"]
    and not out["c3_surviving_track_is_still_a_refusal"]["applied"])
print(json.dumps(out, indent=1))
Path(HERE / "evidence/d680-release-bare-pad-controls.json").write_text(
    json.dumps(out, indent=1) + "\n", encoding="utf-8")
