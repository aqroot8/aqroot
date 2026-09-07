"""D-657: FOUR LEVERS THAT DO NOT MOVE `BQ25185_SYS`, MEASURED NOT ASSUMED.

Before spending a transaction on the pour's CUT, ask whether the pour's own
PARAMETERS answer it -- and whether the 30.363 mm of INERT foreign copper
inside its rectangle is the cut after all.  Each arm edits a private copy,
refills with KiCad's own `ZONE_FILLER`, and reads the partition off
`GetConnectivity`.  The authoritative board is never written.

    A  pad connection THERMAL -> FULL on both SYS zones
       (a 0.20 mm-tall WSON land cannot grow a thermal spoke, so "the relief
        is starving the pads" is the first thing a reader will suspect)
    B  SYS zone priority 0 -> 1, above the board-wide `B GND PLANE`
       (a local power pour that does not outrank the ground plane it lives
        inside is a standard defect; this board has every zone at priority 0)
    C  zone min_thickness 0.200 -> 0.100 mm
       (D-656 raised it and watched pads fall off; this lowers it)
    D  remove ALL 46 INERT track objects screen_inert_copper.py finds inside
       the POUR 1 rectangle -- 29 chains, 30.363 mm of GND and +3V3 B.Cu that
       duplicate a connection their own pour already makes

ONE `LoadBoard` PER PROCESS: the edit and the fill are separate children, because
removing a track and then filling in the same interpreter segfaults KiCad 10.0.5.

    python3 d657-zone-lever-probe.py OUT.json
"""
import hashlib, json, shutil, subprocess, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent.parent          # .../manufacturing
ROOT = HERE.parents[2]
BOARD = ROOT / "hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb"
NET = "/01_POWER_TREE/BQ25185_SYS"
CUT = HERE / "screen_pour_cut_blame.py"
WORK = Path("/tmp/d657_zone_levers")


def _child():
    import pcbnew
    board, arm = sys.argv[2], sys.argv[3]
    b = pcbnew.LoadBoard(board)
    n = 0
    for z in b.Zones():
        if z.GetIsRuleArea() or "BQ25185_SYS" not in z.GetNetname():
            continue
        if arm == "padconn_full":
            z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
        elif arm == "priority_1":
            z.SetAssignedPriority(1)
        elif arm == "minthk_010":
            z.SetMinThickness(100000)
        else:
            raise SystemExit("unknown arm " + arm)
        n += 1
    b.Save(board)
    (Path(board).parent / "edited.json").write_text(json.dumps(dict(zones=n)))
    return 0


if len(sys.argv) > 1 and sys.argv[1] == "--edit-zone":
    raise SystemExit(_child())

OUT = Path(sys.argv[1])
sha = hashlib.sha256(BOARD.read_bytes()).hexdigest()
WORK.mkdir(parents=True, exist_ok=True)


def fresh(tag):
    d = WORK / tag
    d.mkdir(parents=True, exist_ok=True)
    for suf in (".kicad_pcb", ".kicad_dru", ".kicad_pro"):
        shutil.copy(BOARD.with_suffix(suf), (d / BOARD.name).with_suffix(suf))
    return d


def partition(d):
    res = d / "result.json"
    if res.exists():
        res.unlink()
    subprocess.run([sys.executable, str(CUT), "--fill", str(d / BOARD.name),
                    NET, str(res)], capture_output=True, text=True)
    return json.loads(res.read_text())["partition"]


arms = [dict(arm="0 baseline (control)", note="no edit")]
d = fresh("base")
arms[0]["partition"] = partition(d)

for arm, note in (("padconn_full", "both SYS zones pad connection THERMAL -> FULL"),
                  ("priority_1", "both SYS zones priority 0 -> 1, above `B GND PLANE`"),
                  ("minthk_010", "both SYS zones min_thickness 0.200 -> 0.100 mm")):
    d = fresh(arm)
    subprocess.run([sys.executable, __file__, "--edit-zone",
                    str(d / BOARD.name), arm], capture_output=True, text=True)
    arms.append(dict(arm=arm, note=note,
                     zones_edited=json.loads((d / "edited.json").read_text())["zones"],
                     partition=partition(d)))

# D: the INERT removal, taken verbatim from screen_inert_copper.py's own report
inert = json.loads((HERE / "evidence/d657-inert-window.json").read_text())
units, mm = [], 0.0
for ch in inert["chains"]:
    if ch["verdict"] != "INERT":
        continue
    mm += ch["chain_mm"]
    for t in ch["tracks"]:
        a = [int(round(v * 1e6)) for v in t["a_mm"]]
        z = [int(round(v * 1e6)) for v in t["b_mm"]]
        if tuple(z) < tuple(a):
            a, z = z, a
        units.append(["trk", ch["net"], t["layer"], a[0], a[1], z[0], z[1],
                      int(round(t["width_mm"] * 1e6))])
d = fresh("inert")
(d / "remove.json").write_text(json.dumps(units))
subprocess.run([sys.executable, str(CUT), "--edit", str(d / BOARD.name),
                str(d / "remove.json")], capture_output=True, text=True)
arms.append(dict(arm="inert_removal", partition=partition(d),
                 note="every INERT chain screen_inert_copper.py reports inside "
                      "the POUR 1 rectangle, removed at once",
                 chains=sum(1 for c in inert["chains"] if c["verdict"] == "INERT"),
                 track_objects=len(units), inert_mm=round(mm, 3),
                 removed=json.loads((d / "removed.json").read_text())["removed"]))

base = arms[0]["partition"]
for a in arms:
    a["clusters"] = len(a["partition"])
    a["identical_to_baseline"] = (a["partition"] == base)
OUT.write_text(json.dumps(dict(
    schema=1, decision="D-657", board=str(BOARD), board_sha256=sha, net=NET,
    question="do the POUR's own parameters, or the INERT copper inside its "
             "rectangle, answer the BQ25185_SYS residual?",
    method="KiCad's own pcbnew.ZONE_FILLER over a private copy per arm; "
           "partition read off GetConnectivity; authoritative board never written",
    verdict="NO on all four.  every arm's partition is IDENTICAL to the "
            "baseline, cluster for cluster." if all(a["identical_to_baseline"]
                                                    for a in arms)
            else "at least one arm moved the partition -- read the arms",
    authoritative_unchanged=hashlib.sha256(BOARD.read_bytes()).hexdigest() == sha,
    arms=arms), indent=1, sort_keys=True))
for a in arms:
    print("%-24s clusters %d  identical_to_baseline %s"
          % (a["arm"], a["clusters"], a["identical_to_baseline"]))
print("wrote", OUT)
