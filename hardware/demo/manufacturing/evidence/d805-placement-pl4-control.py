import sys, json, tempfile
from pathlib import Path
sys.path.insert(0, "/home/aqroot8/w/d805-interface/hardware/demo/manufacturing/checks")
import placement_contract as pc
import pcbnew
tmp = Path(tempfile.mkdtemp())
b = pcbnew.LoadBoard(str(pc.BOARD))
f = b.FindFootprintByReference("R113"); f.SetPosition(pcbnew.VECTOR2I(f.GetPosition().x - 600000, f.GetPosition().y))
scratch = tmp / "s" / pc.BOARD.name; scratch.parent.mkdir(); b.Save(str(scratch))
real_stage = pc.stage
def stage(rev, work):
    if rev is None:
        work.mkdir(parents=True, exist_ok=True); t = work / pc.BOARD.name; t.write_bytes(scratch.read_bytes()); return t
    return real_stage(rev, work)
pc.stage = stage
rel = open(__import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)), "d805-placement-releases.txt")).read().split()
sys.argv = ["x", "--move", "J3:0:4625000:180", "--move", "J2:0:5900000:180", "--move", "SW9:8500000:0:0", *rel, "--overlap-ok", "J2:R113", "-o", str(tmp / "o.json")]
import io, contextlib
with contextlib.redirect_stdout(io.StringIO()):
    pc.main()
d = json.load(open(tmp / "o.json"))
print(json.dumps({"PL4": d["checks"]["PL4_no_new_courtyard_overlap"], "declared": d["detail"]["courtyard_overlaps_declared"], "remaining": d["detail"]["courtyard_overlaps_new"]}))
