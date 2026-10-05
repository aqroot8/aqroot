import sys, json, subprocess, tempfile, shutil
from pathlib import Path
sys.path.insert(0, "/home/aqroot8/w/d805-interface/hardware/demo/manufacturing/checks")
import placement_contract as pc
import pcbnew
MM = 1_000_000
tmp = Path(tempfile.mkdtemp())
pre = pc.read(pc.stage("HEAD", tmp / "pre"))
claimed = {"J3": (0, 4625000, 180.0), "J2": (0, 5900000, 180.0), "SW9": (8500000, 0, 0.0)}
rel = open(__import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)), "d805-placement-releases.txt")).read().replace("--release ", "").split()
out = {}
# control 1: a POFV barrel 0.100 mm off its land centre is NOT carried -> PL9 must fail
b = pcbnew.LoadBoard(str(pc.BOARD))
for t in b.GetTracks():
    if t.GetClass() == "PCB_VIA" and t.GetNetname() == "/01_POWER_TREE/USB_VBUS_RAW" and abs(t.GetPosition().x - 40600000) < 10 and abs(t.GetPosition().y - 143645000) < 10:
        t.SetPosition(pcbnew.VECTOR2I(t.GetPosition().x, t.GetPosition().y + 100000)); break
p1 = tmp / "c1" / pc.BOARD.name; p1.parent.mkdir(); b.Save(str(p1))
ch, de = pc.judge(pre, pc.read(p1), claimed, tuple(rel))
out["PL9_offset_barrel_is_still_swallowed"] = (not ch["PL9_no_via_swallowed_by_a_moved_land"]) and any(abs(v["at_mm"][1] - 143.745) < 1e-6 for v in de["vias_swallowed_by_moved_lands"])
# baseline on the real board
ch0, de0 = pc.judge(pre, pc.read(pc.stage(None, tmp / "post")), claimed, tuple(rel))
out["real_board_PL9"] = ch0["PL9_no_via_swallowed_by_a_moved_land"]
print(json.dumps(out))
