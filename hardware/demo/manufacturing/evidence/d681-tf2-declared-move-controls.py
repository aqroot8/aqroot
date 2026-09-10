#!/usr/bin/env python3
"""D-681 CONTROLS: TF2's DECLARED_MOVES table must not be a hole.

Three probes, all in-process, board never written:
  A  the six declared moves are recognised and TF2 passes  (the live state)
  B  an UNDECLARED move on another class still FAILS TF2
  C  a DECLARED pair whose was/now do NOT match the actual move still FAILS
"""
import json, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
MANU = HERE.parent
sys.path.insert(0, str(MANU))
sys.path.insert(0, str(MANU / "checks"))
import importlib.util

spec = importlib.util.spec_from_file_location(
    "tfc", str(MANU / "checks/trunk_floor_contract.py"))
tfc = importlib.util.module_from_spec(spec)
# import without running __main__
src = (MANU / "checks/trunk_floor_contract.py").read_text()
ns = {"__name__": "tfc_probe", "__file__": str(MANU / "checks/trunk_floor_contract.py")}
exec(compile(src.split("def main(")[0], "trunk_floor_contract.py", "exec"), ns)

import route_maze_batch as rmb
DECL = ns["DECLARED_MOVES"]
BASE_FIELDS = ns["BASE_FIELDS"]


def judge(was_layers, now_layers, net, decl):
    """The exact predicate TF2 applies to one moved field."""
    d = decl.get((net, "layers"))
    return bool(d and list(d[0]) == list(was_layers or [])
                and list(d[1]) == list(now_layers or []))


out = dict(schema=1, decision="D-681",
           question="is TF2's DECLARED_MOVES table a named exception or a hole",
           probes=[])
# A: the live declaration
out["probes"].append(dict(
    control="declared_move_is_recognised", expected=True,
    got=judge(["F"], ["F", "B"], "/USB_D_MCU_P", DECL),
    why="the exact move D-681 took"))
# B: an undeclared net
out["probes"].append(dict(
    control="undeclared_net_still_fails", expected=False,
    got=judge(["B"], ["B", "I2"], "/04_SPI_B_RADIOS_NFC/NFC_RFO1", DECL),
    why="a class D-681 did not name"))
# C: a declared net whose was/now do not match
out["probes"].append(dict(
    control="declared_net_wrong_move_still_fails", expected=False,
    got=judge(["F"], ["F", "B", "I2"], "/USB_D_MCU_P", DECL),
    why="the declared pair is the WHOLE claim, not just the net name"))
out["probes"].append(dict(
    control="declared_net_wrong_base_still_fails", expected=False,
    got=judge(["B"], ["F", "B"], "/USB_D_MCU_P", DECL),
    why="a different starting contract is a different move"))
out["ok"] = all(p["got"] == p["expected"] for p in out["probes"])
out["declared_entries"] = len(DECL)
Path(HERE / "d681-tf2-declared-move-controls.json").write_text(
    json.dumps(out, indent=1) + "\n", encoding="utf-8")
print(json.dumps({"ok": out["ok"],
                  "probes": [[p["control"], p["got"]] for p in out["probes"]]},
                 indent=1))
