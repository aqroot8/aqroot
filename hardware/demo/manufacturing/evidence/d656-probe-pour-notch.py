"""D-656 PROBE: cut a NOTCH into `B /01_POWER_TREE/BQ25185_SYS POUR 1`'s
outline so the pour stops reaching into the U2/U3 signal pocket, refill with
the real KiCad engine and re-run the real DRC.  Read-only w.r.t. the
authoritative board: every trial is a copy."""
import json, re, shutil, subprocess, sys
from pathlib import Path

SRC, OUT = Path(sys.argv[1]), Path(sys.argv[2])
NOTCH_X1 = float(sys.argv[3])      # notch runs from the pour's west edge to X1
NOTCH_Y0, NOTCH_Y1 = float(sys.argv[4]), float(sys.argv[5])
ZONE = "B /01_POWER_TREE/BQ25185_SYS POUR 1"
# the authoritative outline, read from the board and asserted, never assumed
OLD = "(xy 58.5 72) (xy 71 72) (xy 71 108.5) (xy 58.5 108.5)"
NEW = ("(xy 58.5 72) (xy 71 72) (xy 71 108.5) (xy 58.5 108.5) "
       "(xy 58.5 %g) (xy %g %g) (xy %g %g) (xy 58.5 %g)"
       % (NOTCH_Y1, NOTCH_X1, NOTCH_Y1, NOTCH_X1, NOTCH_Y0, NOTCH_Y0))

OUT.parent.mkdir(parents=True, exist_ok=True)
d = OUT.parent / OUT.stem
d.mkdir(parents=True, exist_ok=True)
for suf in (".kicad_pcb", ".kicad_dru", ".kicad_pro"):
    shutil.copy(SRC.with_suffix(suf), (d / SRC.name).with_suffix(suf))
b = d / SRC.name
text = b.read_text()
i = text.index('(name "%s")' % ZONE)
j = text.index(OLD, i)
b.write_text(text[:j] + NEW + text[j + len(OLD):])

rc = subprocess.run(["kicad-cli", "pcb", "drc", "--refill-zones", "--save-board",
                     "--format", "json", "--units", "mm", "--severity-all",
                     "-o", str(d / "drc.json"), str(b)],
                    capture_output=True, text=True)
doc = json.loads((d / "drc.json").read_text())
types = {}
for v in doc.get("violations", []):
    types[v["type"]] = types.get(v["type"], 0) + 1
part = subprocess.run([sys.executable, str(Path(__file__).parent / "mt/probe_mt.py"),
                       "--partition", str(b)], capture_output=True, text=True)
res = {"schema": 1, "source": str(SRC), "zone": ZONE,
       "notch_mm": {"x_to": NOTCH_X1, "y0": NOTCH_Y0, "y1": NOTCH_Y1},
       "new_outline": NEW, "drc_exit": rc.returncode, "drc_types": types,
       "partition": json.loads(part.stdout), "board": str(b)}
OUT.write_text(json.dumps(res, indent=1, sort_keys=True))
print("exit %d  %s  groups %d" % (rc.returncode, types, len(res["partition"])))
print("wrote", OUT)
