"""D-656: WHICH of a run's new objects makes the `copper_sliver`?

KiCad names the violation with an EMPTY item list, so the only authoritative
answer is a bisection under the REAL fill engine and the REAL DRC: take the
gate's own candidate, delete ONE of the objects this run ADDED, refill, re-run
DRC, and ask whether the sliver is still there.  An object whose absence clears
it is NECESSARY to it.

ONE PROBE PER PROCESS.  `pcbnew.LoadBoard` called too many times in one
interpreter hands back an unwrapped `SwigPyObject` and segfaults -- the limit
`screen_cut_price.py` already records -- so the driver re-execs itself.

    python3 bisect_obj.py AUTH.kicad_pcb CAND.kicad_pcb NET OUT.json [tag which]
"""
import json, shutil, subprocess, sys
from pathlib import Path
import pcbnew

AUTH, CAND, NET, OUT = (Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3],
                        Path(sys.argv[4]))
IS_PROBE = len(sys.argv) > 6
WORK = OUT.parent / (OUT.stem + "_work")
WORK.mkdir(parents=True, exist_ok=True)


def sigs(path):
    b = pcbnew.LoadBoard(str(path))
    out = set()
    for t in b.GetTracks():
        s, e = t.GetStart(), t.GetEnd()
        out.add((t.Type() == pcbnew.PCB_VIA_T, t.GetNetname(), t.GetLayer(),
                 s.x, s.y, e.x, e.y))
    return out


added = sorted(a for a in (sigs(CAND) - sigs(AUTH)) if a[1] == NET)


def probe(keep, tag):
    d = WORK / tag
    d.mkdir(parents=True, exist_ok=True)
    for suf in (".kicad_pcb", ".kicad_dru", ".kicad_pro"):
        shutil.copy(CAND.with_suffix(suf), (d / CAND.name).with_suffix(suf))
    b = pcbnew.LoadBoard(str(d / CAND.name))
    want = {a for a in added if a not in keep}
    for t in list(b.GetTracks()):
        s, e = t.GetStart(), t.GetEnd()
        k = (t.Type() == pcbnew.PCB_VIA_T, t.GetNetname(), t.GetLayer(),
             s.x, s.y, e.x, e.y)
        if k in want:
            b.Remove(t)
    b.Save(str(d / CAND.name))
    subprocess.run(["kicad-cli", "pcb", "drc", "--refill-zones", "--save-board",
                    "--format", "json", "--units", "mm", "--severity-all",
                    "-o", str(d / "drc.json"), str(d / CAND.name)],
                   capture_output=True, text=True)
    doc = json.loads((d / "drc.json").read_text())
    return sum(1 for v in doc.get("violations", [])
               if v["type"] == "copper_sliver")


if IS_PROBE:
    tag, which = sys.argv[5], sys.argv[6]
    keep = (added if which == "-1" else [] if which == "all"
            else [x for i, x in enumerate(added) if i != int(which)])
    print("SLIVER %d" % probe(keep, tag))
    sys.exit(0)


def child(tag, which):
    r = subprocess.run([sys.executable, __file__, str(AUTH), str(CAND), NET,
                        str(OUT), tag, which], capture_output=True, text=True)
    for line in r.stdout.splitlines():
        if line.startswith("SLIVER "):
            return int(line.split()[1])
    raise SystemExit("probe %s failed\n%s\n%s"
                     % (tag, r.stdout[-400:], r.stderr[-400:]))


print("run added %d objects of %s" % (len(added), NET))
rows = [{"tag": "all", "kept": len(added), "sliver": child("all", "-1")},
        {"tag": "none", "kept": 0, "sliver": child("none", "all")}]
print("   all  sliver %d      none sliver %d"
      % (rows[0]["sliver"], rows[1]["sliver"]))
culprits = []
for i, a in enumerate(added):
    n = child("drop%02d" % i, str(i))
    rows.append({"tag": "drop%02d" % i, "object": str(a), "sliver": n})
    print("   drop%02d %-64s sliver %d" % (i, str(a)[:64], n))
    if n == 0:
        culprits.append(str(a))
        print("      ^^ NECESSARY: without this object the sliver is GONE")
OUT.write_text(json.dumps({"schema": 1, "authority": str(AUTH),
                           "candidate": str(CAND), "net": NET,
                           "added": [str(a) for a in added],
                           "necessary": culprits, "probes": rows}, indent=1))
print("wrote", OUT)
