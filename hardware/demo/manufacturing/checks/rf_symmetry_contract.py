#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AQROOT Demo -- the NFC front-end SYMMETRY contract (RF1-RF5).

`.kicad_dru` section 7 states, in its own words, the one thing about this front
end that it cannot encode:

    NOT ENCODABLE, AND THEREFORE A PLACEMENT PRECONDITION: differential
    symmetry.  MEASURED ON THE CURRENT PLACEMENT the two arms are not
    symmetric -- NFC_MATCH_A spans 24.18 mm and NFC_MATCH_B spans 34.21 mm
    [...] R_q is 1.1 ohm per arm and the network Q is ~21; a 10 mm arm-length
    mismatch is not something routing can absorb.  That is PM-3.

PM-3 has been an OPEN, RECORDED placement defect since FBV2-P2-000, and until
this file nothing on the board could see it change.  `verify_promotion.py`
counts objects and runs KiCad; KiCad has no length rule on these nets;
`routing_ledger.py` counts open edges.  So ANY routing transaction could have
lengthened a 13.56 MHz transmit arm by millimetres and every gate would have
passed it -- and D-621 measured exactly that possibility: with `C17` left in
the receive channel, the only relay of the `NFC_RFO2` dogleg that frees the
channel is **9.470 mm against 2.887 mm**, +6.583 mm on the arm that is ALREADY
the longer one, and no clause would have said a word.

`route_maze_batch.EXCLUDE` was the stand-in.  It held `NFC_RFI1` / `NFC_RFI2`
out of generic maze routing with the note "NFC receive arms: length/symmetry" --
abstention in place of a measurement, which is the same substitution the USB
pair's exclusion made until D-596 replaced it with a real contract.  This file
is the measurement, so the abstention can stop.

    RF1  BOTH TRANSMIT ARMS ARE STILL WHAT THE RULE SET SAYS THEY ARE: copper
         on B.Cu only, zero barrels.  `.kicad_dru` section 7 forbids both by
         name and KiCad enforces it; this clause states it on the object, so a
         report can be read without cross-referencing a DRC log.
    RF2  THE TRANSMIT ARMS' MISMATCH GREW BY NO MORE THAN A DECLARED BUDGET.
         `|len(RFO1) - len(RFO2)|`, measured on the copper, before and after.
         The budget defaults to ZERO: a promotion that spends any of it must
         say so on the command line, and the number lands in the record.
    RF3  THE RECEIVE PAIR IS TOPOLOGICALLY SYMMETRIC: same barrel count, same
         set of layers.  A differential input where one half dives to an inner
         layer and the other does not is a mismatch no length figure reports.
    RF4  THE RECEIVE PAIR'S LENGTH MISMATCH IS NO WORSE THAN THE PLACEMENT'S
         OWN.  Each divider tap sits a fixed straight-line distance from its
         `U9` land, and those two distances already differ; routing may not be
         blamed for that, but it may not exceed it either.  This is a bound the
         board's own geometry states, so it needs no tuning.
    RF5  THE SCREEN IS NOT VACUOUS: a synthetic 1.000 mm extension of the
         LONGER transmit arm on a throwaway copy must break RF2.  It has to be
         the longer one -- lengthening the SHORTER arm makes the mismatch
         smaller and proves nothing, which is what the first run of this probe
         did (2.5999 -> 2.1627 mm on `NFC_RFO1`).

    python3 hardware/demo/manufacturing/checks/rf_symmetry_contract.py \\
        --ref HEAD [--arm-mismatch-budget-mm 0.3] [-o REPORT.json]
"""

import argparse
import json
import math
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
BOARD = ROOT / "hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb"

ARM_A = "/04_SPI_B_RADIOS_NFC/NFC_RFO1"
ARM_B = "/04_SPI_B_RADIOS_NFC/NFC_RFO2"
RX_A = "/04_SPI_B_RADIOS_NFC/NFC_RFI1"
RX_B = "/04_SPI_B_RADIOS_NFC/NFC_RFI2"

# The two ends of each receive half, as REF.PIN.  RF4's bound is the straight
# line between them, which is a placement fact and not a routing choice.
RX_ENDS = {RX_A: ("U9.22", "R116.2"), RX_B: ("U9.23", "R117.2")}


def stage(rev, work):
    work.mkdir(parents=True, exist_ok=True)
    target = work / BOARD.name
    if rev is None:
        target.write_bytes(BOARD.read_bytes())
    else:
        src = BOARD.relative_to(ROOT)
        target.write_bytes(subprocess.run(
            ["git", "-C", str(ROOT), "show", "%s:%s" % (rev, src)],
            capture_output=True, check=True).stdout)
    return target


def read(path):
    """Per-net copper length, barrel count and layer set, plus pad positions."""
    import pcbnew
    board = pcbnew.LoadBoard(str(path))
    nets = {}
    for n in (ARM_A, ARM_B, RX_A, RX_B):
        nets[n] = dict(mm=0.0, vias=0, layers=set(), tracks=0)
    for t in board.GetTracks():
        n = t.GetNetname()
        if n not in nets:
            continue
        if t.GetClass() == "PCB_VIA":
            nets[n]["vias"] += 1
            continue
        s, e = t.GetStart(), t.GetEnd()
        nets[n]["mm"] += math.dist((s.x, s.y), (e.x, e.y)) / 1e6
        nets[n]["layers"].add(board.GetLayerName(t.GetLayer()))
        nets[n]["tracks"] += 1
    pads = {}
    for f in board.GetFootprints():
        for p in f.Pads():
            pads["%s.%s" % (f.GetReference(), p.GetNumber())] = (
                p.GetPosition().x / 1e6, p.GetPosition().y / 1e6)
    out = {n: dict(mm=round(v["mm"], 4), vias=v["vias"], tracks=v["tracks"],
                   layers=sorted(v["layers"])) for n, v in nets.items()}
    return out, pads


def mismatch(state, a, b):
    return round(abs(state[a]["mm"] - state[b]["mm"]), 4)


def placement_bound(pads):
    """RF4's bound: |direct(RX_A) - direct(RX_B)|, in mm."""
    d = {}
    for net, (u9, div) in RX_ENDS.items():
        if u9 not in pads or div not in pads:
            return None, {}
        d[net] = round(math.dist(pads[u9], pads[div]), 4)
    return round(abs(d[RX_A] - d[RX_B]), 4), d


PERTURB = """
import sys
import pcbnew
path, net = sys.argv[1], sys.argv[2]
b = pcbnew.LoadBoard(path)
t = [x for x in b.GetTracks()
     if x.GetClass() == 'PCB_TRACK' and x.GetNetname() == net]
if not t:
    raise SystemExit('RF5: no track on %s' % net)
x = t[0]
s0, e = x.GetStart(), x.GetEnd()
# EXTEND ALONG THE TRACK'S OWN DIRECTION, so the perturbation is exactly
# +1.000 mm of copper.  A blind +1 mm in x can SHORTEN a segment that runs the
# other way, which is what the first run of this probe did.
import math
dx, dy = e.x - s0.x, e.y - s0.y
n = math.hypot(dx, dy) or 1.0
x.SetEnd(pcbnew.VECTOR2I(int(round(e.x + 1000000 * dx / n)),
                         int(round(e.y + 1000000 * dy / n))))
pcbnew.SaveBoard(path, b)
"""


def judge(pre, post, budget_mm):
    spre, ppre = pre
    spost, ppost = post
    arm_pre, arm_post = mismatch(spre, ARM_A, ARM_B), mismatch(spost, ARM_A, ARM_B)
    rx_pre, rx_post = mismatch(spre, RX_A, RX_B), mismatch(spost, RX_A, RX_B)
    bound, direct = placement_bound(ppost)

    arms_clean = []
    for n in (ARM_A, ARM_B):
        v = spost[n]
        if v["vias"] or [L for L in v["layers"] if L != "B.Cu"]:
            arms_clean.append(dict(net=n, vias=v["vias"], layers=v["layers"]))

    rx_routed = all(spost[n]["tracks"] for n in (RX_A, RX_B))
    topo = None
    if rx_routed:
        a, b = spost[RX_A], spost[RX_B]
        if a["vias"] != b["vias"] or a["layers"] != b["layers"]:
            topo = dict(rfi1=dict(vias=a["vias"], layers=a["layers"]),
                        rfi2=dict(vias=b["vias"], layers=b["layers"]))

    checks = dict(
        RF1_transmit_arms_b_cu_only_no_barrel=not arms_clean,
        RF2_arm_mismatch_within_budget=(arm_post <= arm_pre + budget_mm + 1e-9),
        RF3_receive_pair_topologically_symmetric=(topo is None),
        RF4_receive_mismatch_within_placement_bound=(
            True if not rx_routed or bound is None
            else rx_post <= bound + 1e-9),
    )
    detail = dict(
        arm_a=spost[ARM_A], arm_b=spost[ARM_B],
        arm_a_was=spre[ARM_A], arm_b_was=spre[ARM_B],
        arm_mismatch_mm_was=arm_pre, arm_mismatch_mm_now=arm_post,
        arm_mismatch_growth_mm=round(arm_post - arm_pre, 4),
        arm_mismatch_budget_mm=budget_mm,
        arm_violations=arms_clean,
        rx_a=spost[RX_A], rx_b=spost[RX_B],
        rx_a_was=spre[RX_A], rx_b_was=spre[RX_B],
        rx_mismatch_mm_was=rx_pre, rx_mismatch_mm_now=rx_post,
        rx_routed=rx_routed, rx_topology_violation=topo,
        rx_placement_direct_mm=direct,
        rx_placement_mismatch_bound_mm=bound,
    )
    return checks, detail


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ref", default="HEAD",
                    help="git revision holding the PRE-promotion board")
    ap.add_argument("--arm-mismatch-budget-mm", type=float, default=0.0,
                    help="how much TRANSMIT-arm A/B length mismatch this "
                         "promotion declares it spends.  Default 0.0: an arm "
                         "may not get longer relative to its twin unless the "
                         "run says so and the number is recorded")
    ap.add_argument("-o", "--out", type=Path)
    a = ap.parse_args()

    sys.path.insert(0, "/usr/lib/python3/dist-packages")
    tmp = Path(tempfile.mkdtemp(prefix="aqroot-demo-rfsym-"))
    pre_path, post_path = stage(a.ref, tmp / "pre"), stage(None, tmp / "post")
    pre, post = read(pre_path), read(post_path)
    checks, detail = judge(pre, post, a.arm_mismatch_budget_mm)

    probe = tmp / "rf5" / BOARD.name
    probe.parent.mkdir(parents=True, exist_ok=True)
    probe.write_bytes(post_path.read_bytes())
    longer = ARM_A if post[0][ARM_A]["mm"] >= post[0][ARM_B]["mm"] else ARM_B
    subprocess.run([sys.executable, "-c", PERTURB, str(probe), longer],
                   check=True, capture_output=True)
    pchecks, pdetail = judge(pre, read(probe), a.arm_mismatch_budget_mm)
    checks["RF5_screen_is_not_vacuous"] = not pchecks["RF2_arm_mismatch_within_budget"]
    detail["rf5_probe_arm"] = longer
    detail["rf5_probe_arm_mismatch_mm"] = pdetail["arm_mismatch_mm_now"]

    doc = dict(schema=1, ref=a.ref, checks=checks, detail=detail,
               verdict="PASS" if all(checks.values()) else "FAIL")
    text = json.dumps(doc, indent=2, sort_keys=True)
    if a.out:
        a.out.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
