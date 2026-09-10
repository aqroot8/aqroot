#!/usr/bin/env python3
"""D-680: collect every gate run and probe of the U21/L4 accessory-boost pocket
into one evidence artifact.  Reads the runs' own JSON; transcribes nothing."""
import json, hashlib
from pathlib import Path
HERE = Path("/home/aqroot8/aqroot-demo/hardware/demo/manufacturing")
BOARD = HERE.parent / "kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb"

ARMS = [
    ("sysA", "--partial --join-max-mm 8 (no eviction)"),
    ("sysB", "--split-islands --join-residual --join-max-mm 12 (no eviction)"),
    ("sysC", "windowed eviction FB+BUF, --join-max-mm 30, grid 0.050"),
    ("sysE", "windowed eviction FB+BUF, --join-max-mm 45, grid 0.050"),
    ("sysF", "windowed eviction FB+BUF, --join-max-mm 70, --repair-join-max-mm 15"),
    ("sysG", "windowed eviction FB+BUF, --join-max-mm 0 (unbounded)"),
    ("sysH", "--evict-whole FB+BUF, all three nets REQUESTED, --join-max-mm 0"),
    ("sysI", "windowed eviction, all three REQUESTED, --body-landing"),
    ("sysJ", "--evict-whole, all three REQUESTED, --body-landing"),
    ("sysK", "NO eviction; FB+BUF RELAYED around a 0.90 mm reserved lane"),
    ("sysL", "NO eviction; FB+BUF RELAYED around a 0.75 mm reserved lane, grid 0.025"),
    ("sysM", "NO eviction; FB+BUF RELAYED, 0.75 mm lane, 60 mm budget, grid 0.050"),
    ("fbA", "R100 MOVED to (58.900,42.400); BUF windowed; all three requested"),
    ("fbB", "R100 MOVED to (58.900,42.400); BUF whole; all three requested"),
    ("sysN", "NO eviction; FB+BUF RELAYED with BOTH chains EXTENDED clear of the "
             "lane, 0.75 mm discs, 40 mm budget"),
]
out = dict(schema=1, decision="D-680",
           question="the /01_POWER_TREE/BQ25185_SYS edge that feeds the U21 "
                    "TPS61023 accessory boost: is it closable, at what price, "
                    "and what does the price buy",
           board=str(BOARD),
           board_sha256=hashlib.sha256(BOARD.read_bytes()).hexdigest(),
           arms=[])
for name, why in ARMS:
    p = HERE / "w/d680" / (name + ".json")
    if not p.is_file():
        out["arms"].append(dict(arm=name, why=why, ran=False))
        continue
    d = json.loads(p.read_text())
    rec = dict(arm=name, why=why, ran=True,
               refused_clauses=d["refused_clauses"],
               connectivity=d["connectivity"],
               drc_types=d.get("drc_types"),
               attributable_drc=len(d.get("attributable_drc") or []),
               routed=[dict(net=r.get("net"), ok=r.get("ok"), mode=r.get("mode"),
                            mm=r.get("mm"), vias=r.get("vias"),
                            join=({k: (r.get("residual_join") or {}).get(k)
                                   for k in ("joined", "mm", "vias")}
                                  if r.get("residual_join") else None))
                       for r in d.get("routed", [])],
               repair=[[q.get("net"), q.get("ok"), q.get("mm")]
                       for q in (d.get("plane_repair") or {}).get("routed", [])])
    det = d.get("detour")
    if det:
        rec["detour"] = dict(all_relaid=det.get("all_relaid"),
                             failed=det.get("failed"))
    out["arms"].append(rec)
Path("evidence/d680-boost-pocket-arms.json").write_text(
    json.dumps(out, indent=1) + "\n", encoding="utf-8")
print(json.dumps([{k: a.get(k) for k in ("arm", "refused_clauses")}
                  for a in out["arms"]], indent=1))
