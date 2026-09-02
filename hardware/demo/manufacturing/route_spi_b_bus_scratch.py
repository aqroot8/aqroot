#!/usr/bin/env python3
"""Screen the three shared SPI-B four-endpoint trees as one atomic batch."""
import hashlib, itertools, json, subprocess, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BOARD = ROOT / "hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb"
LOCAL = Path(__file__).with_name("route_local_two_pad.py")
LEDGER = Path(__file__).with_name("routing_ledger.py")
NETS = ("/SPI_B_SCK", "/SPI_B_MOSI", "/SPI_B_MISO")
LEGS = {
    net: tuple(f"SPI_B_{net.rsplit('_',1)[-1]}_{leg}" for leg in ("U8_U7", "U7_U1", "U1_U9"))
    for net in NETS
}

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    before = sha(BOARD); cases = []
    with tempfile.TemporaryDirectory(prefix="aqroot-demo-spi-b-") as td:
        work = Path(td)
        for order in itertools.permutations(NETS):
            scratch = work / ("-".join(n.rsplit("_",1)[-1] for n in order) + ".kicad_pcb")
            for suffix in (".kicad_pcb", ".kicad_dru", ".kicad_pro"):
                scratch.with_suffix(suffix).write_bytes(BOARD.with_suffix(suffix).read_bytes())
            routes = []
            for net in order:
                for leg in LEGS[net]:
                    run = subprocess.run([sys.executable, str(LOCAL), leg, "--route", str(scratch)], text=True, capture_output=True)
                    row = json.loads(run.stdout); routes.append(row)
                    if run.returncode or not row["result"].get("ok"): break
                if not routes[-1]["result"].get("ok"): break
            ledger_path = scratch.with_suffix(".ledger.json")
            subprocess.run([sys.executable, str(LEDGER), "--board", str(scratch), str(ledger_path)], check=True, stdout=subprocess.DEVNULL)
            ledger = json.loads(ledger_path.read_text())
            opens = {r["net"]: r["open_edges"] for r in ledger["nets"] if r["net"] in NETS}
            failed = next((r for r in routes if not r["result"].get("ok")), None)
            cases.append({"order": list(order), "routes_completed": len(routes),
                          "failure_leg": failed["name"] if failed else None,
                          "failure": failed["result"].get("reason") if failed else None,
                          "open_edges": opens,
                          "complete": all(opens.get(n)==0 for n in NETS)})
    report = {"schema": 1, "authoritative_board_sha256": before, "authoritative_unchanged": sha(BOARD)==before, "contract": {"width_mm": .2, "clearance_mm": .2, "via_mm": [.6,.3], "characterization_only": True}, "cases": cases, "promotion_candidate": False}
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if any(c["complete"] for c in cases) else 2

if __name__ == "__main__": raise SystemExit(main())
