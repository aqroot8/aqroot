#!/usr/bin/env python3
"""D-803: prove the regenerated fab package is manufacturing-geometry
equivalent to the reviewed D-802 package.

    python3 hardware/demo/manufacturing/evidence/d803-geometry-equivalence.py \
        [--parent d6f67692] [-o evidence/d803-geometry-equivalence.json]

Every file under `hardware/demo/fab/` is compared with the same path at the
parent commit.  Gerber, Excellon and gerber-job files are compared after
removing ONLY the lines KiCad stamps with the export time (`TF.CreationDate`,
the `G04 ... date` banner, the drill-file `date` banner, the job file's
`CreationDate`); every other byte -- apertures, coordinates, drill tools and
hits, layer attributes -- must be identical.  BOM / CPL / DNP / off-board CSVs
must be byte-identical.  Anything else (drawings, notes, JSON records,
MANIFEST) is reported as changed or unchanged, with no equivalence claimed.
"""
import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
FAB = "hardware/demo/fab"
STAMP = re.compile(r"TF\.CreationDate|^G04 Created by KiCad .* date |"
                   r"^; DRILL file KiCad .* date |\"CreationDate\"")
GEOMETRY = (".gbr", ".drl", ".gbrjob")
EXACT = (".csv",)


def at(parent, rel):
    run = subprocess.run(["git", "-C", str(ROOT), "show", "%s:%s" % (parent, rel)],
                         capture_output=True)
    return run.stdout if run.returncode == 0 else None


def norm(raw):
    return "\n".join(l for l in raw.decode("utf-8", "replace").splitlines()
                     if not STAMP.search(l))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--parent", default="d6f67692fcc9787ee0d43084a377562f4f26f9b9")
    ap.add_argument("-o", dest="out", type=Path)
    a = ap.parse_args()
    listed = subprocess.run(["git", "-C", str(ROOT), "ls-tree", "-r", "--name-only",
                             a.parent, FAB], capture_output=True, text=True).stdout.split()
    now = sorted(p.relative_to(ROOT).as_posix() for p in (ROOT / FAB).rglob("*")
                 if p.is_file())
    rows, bad = [], []
    for rel in sorted(set(listed) | set(now)):
        old = at(a.parent, rel)
        f = ROOT / rel
        new = f.read_bytes() if f.exists() else None
        row = dict(file=rel, in_parent=old is not None, in_candidate=new is not None)
        if old is None or new is None:
            row["verdict"] = "ADDED" if old is None else "REMOVED"
            if rel.endswith(GEOMETRY + EXACT):
                bad.append(rel)
        elif rel.endswith(GEOMETRY):
            same = norm(old) == norm(new)
            row.update(byte_identical=old == new, geometry_identical=same,
                       differing_lines_removed=[l for l in new.decode(
                           "utf-8", "replace").splitlines() if STAMP.search(l)][:4],
                       verdict="GEOMETRY-IDENTICAL" if same else "GEOMETRY-DIFFERS")
            if not same:
                bad.append(rel)
        elif rel.endswith(EXACT):
            row.update(byte_identical=old == new,
                       verdict="IDENTICAL" if old == new else "DIFFERS")
            if old != new:
                bad.append(rel)
        else:
            row.update(byte_identical=old == new,
                       sha256_parent=hashlib.sha256(old).hexdigest(),
                       sha256_candidate=hashlib.sha256(new).hexdigest(),
                       verdict="UNCHANGED" if old == new else "CHANGED (not geometry)")
        rows.append(row)
    rep = dict(schema=1, decision="D-803", parent=a.parent, files=rows,
               geometry_files=sum(r["file"].endswith(GEOMETRY) for r in rows),
               exact_files=sum(r["file"].endswith(EXACT) for r in rows),
               failures=bad, equivalent=not bad,
               rule="gerber / drill / job files identical after removing only the "
                    "export-time stamp lines; CSVs byte-identical")
    text = json.dumps(rep, indent=1)
    if a.out:
        a.out.write_text(text + "\n")
    print(json.dumps(dict(equivalent=rep["equivalent"], failures=bad,
                          geometry_files=rep["geometry_files"],
                          exact_files=rep["exact_files"],
                          changed_other=[r["file"] for r in rows
                                         if r.get("verdict", "").startswith("CHANGED")]),
                     indent=1))
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
