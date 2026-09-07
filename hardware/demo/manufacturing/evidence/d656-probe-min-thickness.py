"""D-656 READ-ONLY PROBE: does raising `POUR 1`'s own `min_thickness` make
KiCad's filler prune the 0.031 x 0.060 mm crumb that refused the /I2C_SDA_INT
transaction -- and what does it cost the pad partition?  Nothing here touches
the authoritative board: every trial is a copy."""
import json, re, shutil, subprocess, sys
from pathlib import Path

ZONE = "B /01_POWER_TREE/BQ25185_SYS POUR 1"

def set_mt(text, zone_name, mt):
    i = text.index('(name "%s")' % zone_name)
    j = text.index("(min_thickness ", i)
    k = text.index(")", j)
    return text[:j] + "(min_thickness %s" % ("%.4f" % mt).rstrip("0").rstrip(".") + text[k:]

def partition(path):
    import pcbnew
    b = pcbnew.LoadBoard(str(path))
    b.BuildConnectivity()
    conn = b.GetConnectivity()
    pads, parent = {}, {}
    for f in b.GetFootprints():
        for p in f.Pads():
            if p.GetNetname() == "/01_POWER_TREE/BQ25185_SYS" and p.GetNumber():
                k = f.GetReference() + "." + p.GetNumber()
                pads[k] = p; parent[k] = k
    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]; a = parent[a]
        return a
    for k, p in pads.items():
        for it in conn.GetConnectedItems(p):
            if it.GetClass() != "PAD": continue
            o = it.GetParentFootprint().GetReference() + "." + it.GetNumber()
            if o in parent:
                ra, rb = find(k), find(o)
                if ra != rb: parent[ra] = rb
    groups = {}
    for k in parent: groups.setdefault(find(k), []).append(k)
    return sorted(sorted(v) for v in groups.values())

if sys.argv[1] == "--partition":
    print(json.dumps(partition(Path(sys.argv[2]))))
    sys.exit(0)

SRC = Path(sys.argv[1])          # candidate .kicad_pcb (already routed)
OUT = Path(sys.argv[2])
TRIALS = [float(x) for x in sys.argv[3].split(",")]

res = {"schema": 1, "source": str(SRC), "zone": ZONE, "trials": []}
for mt in TRIALS:
    d = OUT.parent / ("mt_%s" % ("%.4f" % mt).rstrip("0").rstrip("."))
    d.mkdir(parents=True, exist_ok=True)
    for suf in (".kicad_pcb", ".kicad_dru", ".kicad_pro"):
        shutil.copy(SRC.with_suffix(suf), (d / SRC.name).with_suffix(suf))
    b = d / SRC.name
    b.write_text(set_mt(b.read_text(), ZONE, mt))
    rc = subprocess.run(["kicad-cli", "pcb", "drc", "--refill-zones",
                         "--save-board", "--format", "json", "--units", "mm",
                         "--severity-all", "-o", str(d / "drc.json"), str(b)],
                        capture_output=True, text=True)
    doc = json.loads((d / "drc.json").read_text())
    types = {}
    for v in doc.get("violations", []):
        types[v["type"]] = types.get(v["type"], 0) + 1
    part = subprocess.run([sys.executable, __file__, "--partition", str(b)],
                          capture_output=True, text=True)
    res["trials"].append({"min_thickness_mm": mt, "drc_exit": rc.returncode,
                          "drc_types": types,
                          "partition": json.loads(part.stdout)})
    print("mt %.4f  exit %d  %s" % (mt, rc.returncode, types))
OUT.write_text(json.dumps(res, indent=1, sort_keys=True))
print("wrote", OUT)
