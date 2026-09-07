"""D-657: does SHRINKING the two `Net-(U11-TS_MR)` barrels re-bond `R39.1`?

`screen_pour_cut_blame.py` names the cut that severs `R39.1` -- the top of the
`TPS63020`'s own 1 M / 180 k `+3V3` feedback divider -- from the `+3V3` plane:
TWO 0.600/0.300 barrels at (64.700, 70.500) and (66.600, 70.900), on
`Net-(U11-TS_MR)`, the `BQ25185`'s 10 k TS/MR strap.  A 0.600 mm barrel with
the zone's 0.250 mm clearance is a 1.100 mm hole through BOTH `+3V3` planes.

Removing them is not the only move.  A barrel is a HOLE WHOSE DIAMETER IS A
CHOICE, and this net carries microamps: the ladder below asks the cheapest
question first -- how SMALL must those two barrels be for KiCad's own filler to
pour `R39.1` back onto the plane, with the strap left exactly where it is?

Every rung is a geometry this board's own `.kicad_dru` already licenses
somewhere: 0.50/0.25 is the smallest the board floor allows unlicensed,
0.45/0.20 and 0.35/0.20 are D-257's `FINE_ESC_*` escape-via rungs.

    python3 d657-barrel-shrink-probe.py OUT.json
"""
import hashlib, json, shutil, subprocess, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent.parent
ROOT = HERE.parents[2]
BOARD = ROOT / "hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb"
CUT = HERE / "screen_pour_cut_blame.py"
NET = "+3V3"
STRAP = "Net-(U11-TS_MR)"
SITES = [(64700000, 70500000), (66600000, 70900000)]
WORK = Path("/tmp/d657_barrel_shrink")
RUNGS = [("0 as built 0.600/0.300", 600000, 300000),
         ("1 board floor 0.500/0.250", 500000, 250000),
         ("2 FINE_ESC 0.450/0.200", 450000, 200000),
         ("3 FINE_ESC 0.350/0.200", 350000, 200000),
         ("4 removed entirely (the D-657 cut-blame answer)", 0, 0)]


def _child():
    import pcbnew
    board, dia, drill = sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
    b = pcbnew.LoadBoard(board)
    n = 0
    for t in list(b.GetTracks()):
        if t.Type() != pcbnew.PCB_VIA_T or t.GetNetname() != STRAP:
            continue
        p = t.GetPosition()
        if (p.x, p.y) not in SITES:
            continue
        if dia == 0:
            b.Remove(t)
        else:
            t.SetWidth(dia)
            t.SetDrill(drill)
        n += 1
    b.Save(board)
    (Path(board).parent / "edited.json").write_text(json.dumps(dict(vias=n)))
    return 0


if len(sys.argv) > 1 and sys.argv[1] == "--edit-via":
    raise SystemExit(_child())

OUT = Path(sys.argv[1])
sha = hashlib.sha256(BOARD.read_bytes()).hexdigest()
WORK.mkdir(parents=True, exist_ok=True)
rows = []
for name, dia, drill in RUNGS:
    d = WORK / name.split()[0]
    d.mkdir(parents=True, exist_ok=True)
    for suf in (".kicad_pcb", ".kicad_dru", ".kicad_pro"):
        shutil.copy(BOARD.with_suffix(suf), (d / BOARD.name).with_suffix(suf))
    subprocess.run([sys.executable, __file__, "--edit-via", str(d / BOARD.name),
                    str(dia), str(drill)], capture_output=True, text=True)
    res = d / "result.json"
    if res.exists():
        res.unlink()
    subprocess.run([sys.executable, str(CUT), "--fill", str(d / BOARD.name),
                    NET, str(res)], capture_output=True, text=True)
    part = json.loads(res.read_text())["partition"]
    strap = json.loads((d / "result_strap.json").write_text("{}") or "{}") \
        if False else None
    # the strap's own connectivity is the control: a rung that re-bonds R39.1
    # by STRANDING the strap has not solved anything
    rs = d / "result_strap.json"
    subprocess.run([sys.executable, str(CUT), "--fill", str(d / BOARD.name),
                    STRAP, str(rs)], capture_output=True, text=True)
    sp = json.loads(rs.read_text())["partition"]
    r39 = [c for c in part if "R39.1" in c][0]
    rows.append(dict(rung=name, via_dia_nm=dia, via_drill_nm=drill,
                     vias_edited=json.loads((d / "edited.json").read_text())["vias"],
                     plane_clusters=len(part),
                     r39_cluster_size=len(r39),
                     r39_bonded=(len(r39) > 1),
                     strap_clusters=len(sp), strap_partition=sp,
                     strap_intact=(len(sp) == 1)))
    print("%-48s +3V3 clusters %d  R39.1 bonded %-5s  strap intact %s"
          % (name, len(part), rows[-1]["r39_bonded"], rows[-1]["strap_intact"]))
OUT.write_text(json.dumps(dict(
    schema=1, decision="D-657", board=str(BOARD), board_sha256=sha,
    net=NET, strap=STRAP, sites_mm=[[s[0] / 1e6, s[1] / 1e6] for s in SITES],
    question="how SMALL must the two Net-(U11-TS_MR) barrels be for KiCad's "
             "own filler to pour R39.1 -- the TPS63020's +3V3 feedback divider "
             "top -- back onto the plane, with the strap left where it is?",
    method="pcbnew.ZONE_FILLER over a private copy per rung; both the PLANE's "
           "partition and the STRAP's own partition read off GetConnectivity, "
           "so a rung that re-bonds the divider by stranding the strap is "
           "visible as such; authoritative board never written",
    authoritative_unchanged=hashlib.sha256(BOARD.read_bytes()).hexdigest() == sha,
    rungs=rows), indent=1, sort_keys=True))
print("wrote", OUT)
