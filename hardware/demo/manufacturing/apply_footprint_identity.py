#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AQROOT Demo -- correct a footprint's IDENTITY on the board, and nothing else.

A footprint's identity is the library it came from and the description that
travels with it.  Neither is copper, neither reaches a Gerber, a drill file, a
position row or a BOM line -- but both decide whether the land can ever be
PROVED, because a footprint that does not name its library has no master to be
compared against, and a footprint whose description drifted from its master is
indistinguishable, to KiCad's own `lib_footprint_mismatch`, from one whose PADS
drifted.

`pcbnew.SaveBoard` rewrites the whole file and would bury a one-token change in
incidental reformatting; the board's authority is a sha256, so this edits the
text.  Following D-615, every edit must NAME the exact string it overwrites and
say how many times that string may occur -- and then the result is re-read
through `pcbnew` and checked against what the edit CLAIMED it would produce, so
a plan that hits the right text in the wrong place still fails.

    python3 hardware/demo/manufacturing/apply_footprint_identity.py \
        --plan PLAN.json [--apply] [-o REPORT.json]

Plan:  {"edits": [{"ref": "J8", "old": "(footprint \\"X\\"", "new": ...,
                   "occurrences": 1, "expect_fpid": "Connector_JST:X",
                   "reason": "..."}]}

`expect_fpid` and `expect_descr` are the post-conditions; at least one must be
given per edit.  Dry-run by default.
"""

import argparse
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BOARD = (ROOT / "hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb")


def verify(path, edits):
    import pcbnew
    board = pcbnew.LoadBoard(str(path))
    out = []
    for e in edits:
        fp = board.FindFootprintByReference(e["ref"])
        got = {"ref": e["ref"],
               "fpid": fp.GetFPIDAsString() if fp else None,
               "descr": fp.GetLibDescription() if fp else None,
               "pads": len(list(fp.Pads())) if fp else None}
        ok = fp is not None
        if "expect_fpid" in e:
            got["fpid_ok"] = fp is not None and got["fpid"] == e["expect_fpid"]
            ok = ok and got["fpid_ok"]
        if "expect_descr" in e:
            got["descr_ok"] = fp is not None and got["descr"] == e["expect_descr"]
            ok = ok and got["descr_ok"]
        if "expect_pads" in e:
            got["pads_ok"] = got["pads"] == e["expect_pads"]
            ok = ok and got["pads_ok"]
        got["ok"] = bool(ok)
        out.append(got)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", type=Path, required=True)
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("-o", "--out", type=Path)
    a = ap.parse_args()

    plan = json.loads(a.plan.read_text(encoding="utf-8"))
    edits = plan["edits"]
    with BOARD.open("r", encoding="utf-8", newline="") as fh:
        text = fh.read()
    original = text

    applied, refused = [], []
    for e in edits:
        if not ({"expect_fpid", "expect_descr"} & set(e)):
            refused.append(dict(e, why="no post-condition named"))
            continue
        n = text.count(e["old"])
        want = e.get("occurrences", 1)
        if n != want:
            refused.append(dict(e, why="found %d occurrences, plan says %d"
                                % (n, want)))
            continue
        if e["new"] in original:
            refused.append(dict(e, why="replacement text already present"))
            continue
        text = text.replace(e["old"], e["new"])
        applied.append({"ref": e["ref"], "occurrences": n,
                        "reason": e.get("reason", "")})

    report = {"schema": 1, "plan": str(a.plan), "applied": applied,
              "refused": refused, "wrote": False,
              "bytes_before": len(original.encode()),
              "bytes_after": len(text.encode())}

    if refused:
        report["verdict"] = "REFUSED"
    elif not a.apply:
        report["verdict"] = "DRY_RUN"
    else:
        backup = BOARD.with_suffix(".kicad_pcb.identity-backup")
        shutil.copyfile(BOARD, backup)
        with BOARD.open("w", encoding="utf-8", newline="") as fh:
            fh.write(text)
        checks = verify(BOARD, edits)
        report["post_conditions"] = checks
        if all(c["ok"] for c in checks):
            backup.unlink()
            report.update(wrote=True, verdict="APPLIED")
        else:
            shutil.copyfile(backup, BOARD)
            backup.unlink()
            report.update(verdict="ROLLED_BACK")

    text_out = json.dumps(report, indent=2, sort_keys=True, default=str)
    if a.out:
        a.out.write_text(text_out + "\n", encoding="utf-8")
    print(text_out)
    return 0 if report["verdict"] in ("APPLIED", "DRY_RUN") else 1


if __name__ == "__main__":
    raise SystemExit(main())
