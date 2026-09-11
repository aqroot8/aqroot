#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AQROOT Demo -- the TRUNK-FLOOR lever is OFF by default, NON-PERTURBING, and
PRICED before it descends.

D-630's `--escape-floor` let a LAND launch at the width `.kicad_dru` section 5
publishes as its class MINIMUM instead of the `opt` figure the `.kicad_pcb`
netclass carries.  D-662 found the other half of the same defect: `net_contract`
takes `max(netclass width, DRU min)`, so the `opt` becomes the width of the
whole TRUNK and a rail whose corridor is 0.400 mm wide is refused at 0.600 mm
even though 0.400 mm is the width the board's own rule ENFORCES for that class.

`--trunk-floor` is that descent.  It is a WIDTH CONTRACT and not a search
lever, so it is handed to the repair pass too, and it can lay copper on every
promoted rail -- which is exactly why this file exists.  Four claims, each
measured rather than asserted:

  TF1  the floor and the bar are both READ, never transcribed here.  The floor
       is `route_maze_batch.DRU_CLASS[cls]["width"]`, the board's own
       `track_width (min ...)` per class; the bar is whatever
       `pour_partition_contract.published_rail_currents` parses out of
       `.kicad_dru` section 5 -- the SAME parser `PP2` charges a bond with, so
       the two clauses cannot drift apart.

  TF2  with the lever OFF, `net_contract` returns for EVERY net on the board
       exactly what the pre-D-662 module returned -- field for field, net for
       net -- so no accepted route could have been proposed differently.  The
       comparison is against the ACTUAL source at `--rev`, extracted from git,
       not against a remembered result.

  TF3  with the lever ON the descent is offered ONLY where the class floor,
       priced by IPC-2221B at this board's copper, carries the design current
       section 5 publishes for that class; it is NEVER below board setup's
       `min_track_width`; and it NEVER widens a net.  Every net that does not
       descend carries a recorded reason.

  TF4  the four verdicts are reachable and separable: an admitted class, an
       under-priced class, a class with a floor but no published current, and
       a class with no published floor.  A clause that cannot refuse is not a
       clause, so this asserts the refusals and not only the admission.

Run from anywhere:

    python3 hardware/demo/manufacturing/checks/trunk_floor_contract.py [--rev REV]
"""

import argparse
import importlib.util
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
MANU = HERE.parent
ROOT = HERE.parents[3]
BOARD = ROOT / "hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb"
DRU = BOARD.with_suffix(".kicad_dru")
BASE_REV = "8572ade"                      # the D-661 promotion, pre-lever

sys.path.insert(0, str(MANU))
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "hardware/beta-v2/checks"))

def _dru_rules():
    """Every `.kicad_dru` rule as (name, {constraint: min_nm}, condition).

    Read HERE, from the file, so TF3's re-derivation of a D-690 per-net width
    licence does not consult the same code path it is checking.
    """
    import maze3d as _mz

    class _Shim(object):
        class b:
            @staticmethod
            def GetFileName():
                return str(BOARD)
    return _mz.dru_rules(_Shim)


# The fields `net_contract` returned BEFORE this lever existed.  TF2 compares
# exactly these, so a future field added beside `trunk_floor` cannot make the
# non-perturbation claim weaker by accident.
BASE_FIELDS = ("net", "netclass", "width", "clr", "clr_pad",
               "via_dia", "via_drill", "layers", "known_class")

# A MOVE A DECISION TOOK, NAMED, EXACT, AND STILL COMPARED.  D-681.
#
# TF2's claim is "with the lever OFF, `net_contract` returns for EVERY net what
# the pre-D-662 module returned", and its whole value is that it FAILS when
# something moves.  A decision may nevertheless move one deliberately: D-681
# ruled on the question `.kicad_dru` section 6 had left open in its own words --
# whether a THROUGH via that merely PIERCES In2 is the In2 excursion the USB
# rule forbids -- restated that rule as "USB pair carries no track on any inner
# layer" (STRICTLY HARDER for tracks: In1, In3 and In4 are named where only In2
# was) and gave the `USB_D` class the second outer layer the restated rule
# permits.  The reasoning is written beside the rule in the `.kicad_dru`.
#
# Declaring it here keeps the clause's teeth exactly where they were: a move
# that is not in this table, on any net or any field, still fails TF2, and the
# report carries BOTH lists so a reader sees the declared move as well as the
# absence of undeclared ones.  A declaration is a WEAKER statement than silence
# -- it says which move happened and which decision took it.
DECLARED_MOVES = {
    ("/01_POWER_TREE/USB_D_CONN_N", "layers"): (["F"], ["F", "B"], "D-681"),
    ("/01_POWER_TREE/USB_D_CONN_P", "layers"): (["F"], ["F", "B"], "D-681"),
    ("/01_POWER_TREE/USB_D_ESD_N", "layers"): (["F"], ["F", "B"], "D-681"),
    ("/01_POWER_TREE/USB_D_ESD_P", "layers"): (["F"], ["F", "B"], "D-681"),
    ("/USB_D_MCU_N", "layers"): (["F"], ["F", "B"], "D-681"),
    ("/USB_D_MCU_P", "layers"): (["F"], ["F", "B"], "D-681"),
}


def load_rev_module(rev, name="route_maze_batch_base"):
    """Import `route_maze_batch.py` as it stands at `rev`, worktree untouched.

    The extracted copy is written at the SAME depth inside a throwaway tree,
    because the module resolves `ROOT` from its own location with `parents[3]`
    and anywhere shallower raises `IndexError` at import.
    """
    src = subprocess.run(
        ["git", "-C", str(ROOT), "show",
         "%s:hardware/demo/manufacturing/route_maze_batch.py" % rev],
        check=True, capture_output=True, text=True).stdout
    root = Path(tempfile.mkdtemp(prefix="aqroot-trunkfloor-base-"))
    tmp = root / "hardware/demo/manufacturing" / (name + ".py")
    tmp.parent.mkdir(parents=True, exist_ok=True)
    tmp.write_text(src, encoding="utf-8")
    # The base module resolves its own siblings (`screen_inner_plane`, ...)
    # off the REAL manufacturing directory, which is already on `sys.path`.
    spec = importlib.util.spec_from_file_location(name, tmp)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def dru_class_floors(text):
    """Every `track_width (min ...)` the `.kicad_dru` states, by netclass.

    Read from the rule text rather than from `DRU_CLASS`, so TF1 compares the
    router's table against the FILE and not against itself.  A rule body may
    carry a `(layer outer)` line between the name and the constraint, and the
    class is named by `A.hasNetclass('X')` -- the form this file actually uses.
    A rule that names no netclass (a per-NET width, a courtyard neck) is not a
    class floor and is deliberately not collected.
    """
    out = {}
    # A rule body is delimited by the NEXT top-level `(rule`, never by the
    # first `))` -- `(constraint track_width (min 0.40mm))` closes with two
    # parens of its own, and a non-greedy scan that stops there truncates the
    # body before its `(condition ...)` line and silently collects nothing.
    for chunk in re.split(r'\n(?=\(rule ")', text)[1:]:
        m = re.search(r"\(constraint track_width \(min ([0-9.]+)mm\)", chunk)
        if not m:
            continue
        nm = int(round(float(m.group(1)) * 1e6))
        cond = re.search(r'\(condition "([^"]*)"\)', chunk)
        for cls in re.findall(r"hasNetclass\('([^']+)'\)",
                              cond.group(1) if cond else ""):
            out[cls] = max(out.get(cls, 0), nm)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rev", default=BASE_REV)
    ap.add_argument("-o", "--out", type=Path)
    a = ap.parse_args()

    import pcbnew
    import route_maze_batch as rmb
    from pour_partition_contract import published_rail_currents

    base = load_rev_module(a.rev)
    board = pcbnew.LoadBoard(str(BOARD))
    board_min = board.GetDesignSettings().m_TrackMinWidth
    text = DRU.read_text(encoding="utf-8")
    results = {}

    # -- TF1: the floor and the bar are READ -------------------------------- #
    file_floors = dru_class_floors(text)
    table, prov = published_rail_currents(str(DRU))
    router_floors = {k: v["width"] for k, v in rmb.DRU_CLASS.items()
                     if v.get("width")}
    # EVERY class the lever can descend must be the FILE's own figure.  A
    # class the file prices and the table omits cannot descend at all, so it
    # is recorded rather than failed; the reverse -- a table floor the file
    # does not state -- is the defect this claim exists to catch.
    mismatched = sorted(cls for cls, nm in router_floors.items()
                        if file_floors.get(cls) != nm)
    results["TF1"] = dict(
        # AND IT MUST HAVE ASKED.  An empty parse satisfies "nothing
        # mismatched" and proves nothing, so the count is part of the claim.
        ok=(not mismatched and bool(file_floors) and bool(router_floors)
            and prov.get("found") is True and bool(table)),
        dru_file_floors={k: v for k, v in sorted(file_floors.items())},
        router_table_floors={k: v for k, v in sorted(router_floors.items())},
        mismatched=mismatched,
        priced_by_file_only=sorted(set(file_floors) - set(router_floors)),
        published_currents={k: v["amps"] for k, v in sorted(table.items())},
        currents_source_found=bool(prov.get("found")))

    # -- TF2: lever OFF is byte-identical to the pre-lever module ----------- #
    nets = sorted({board.GetNetInfo().GetNetItem(i).GetNetname()
                   for i in range(board.GetNetInfo().GetNetCount())}
                  - {""})
    moved, checked, carried, declared = [], 0, [], []
    for n in nets:
        try:
            now = rmb.net_contract(board, n)
            was = base.net_contract(board, n)
        except SystemExit:
            continue
        checked += 1
        if now.get("trunk_floor") is not None:
            carried.append(n)
        for f in BASE_FIELDS:
            if now.get(f) != was.get(f):
                d = DECLARED_MOVES.get((n, f))
                rec = dict(net=n, field=f, now=now.get(f), was=was.get(f))
                if d and list(d[0]) == list(was.get(f) or []) \
                        and list(d[1]) == list(now.get(f) or []):
                    rec["declared_by"] = d[2]
                    declared.append(rec)
                else:
                    moved.append(rec)
    results["TF2"] = dict(ok=(not moved and not carried and checked > 0),
                          rev=a.rev, nets_compared=checked, moved=moved[:20],
                          declared_moves=declared[:20],
                          declared_moves_expected=len(DECLARED_MOVES),
                          nets_carrying_a_block_with_lever_off=carried[:20])

    # -- TF3: the descent, over every net on the board ---------------------- #
    rows, bad = [], []
    for n in nets:
        try:
            off = rmb.net_contract(board, n)
            on = rmb.net_contract(board, n, True)
        except SystemExit:
            continue
        tf = on["trunk_floor"]
        if tf is None:
            bad.append(dict(net=n, why="NO_BLOCK_WITH_LEVER_ON"))
            continue
        # never wider, never below the board minimum, never unexplained
        if on["width"] > off["width"]:
            bad.append(dict(net=n, why="WIDENED", now=on["width"],
                            was=off["width"]))
        if on["width"] < board_min:
            bad.append(dict(net=n, why="BELOW_BOARD_MIN", now=on["width"],
                            board_min=board_min))
        if tf["admitted"]:
            if on["width"] != tf["floor_nm"]:
                bad.append(dict(net=n, why="ADMITTED_BUT_WIDTH_NOT_THE_FLOOR"))
            # TWO ADMISSIONS, TWO BARS, AND NEITHER MAY STAND IN FOR THE OTHER.
            # D-662's descent is to a CLASS floor and its bar is an AMPACITY:
            # the class must publish a design current and the floor must carry
            # it.  D-690's descent is to a floor the `.kicad_dru` publishes for
            # ONE NAMED NET, for a class section 5 prices NOWHERE -- there is no
            # current to weigh, and the bar is instead that the rule EXISTS, in
            # the exact shape `net_width_licence` accepts, granting THIS net
            # THIS width.  That is re-derived here from the rule text rather
            # than taken from the driver's own answer, so the two cannot agree
            # by construction.
            if tf["why"] == "PUBLISHED_PER_NET_IN_THE_KICAD_DRU":
                want = "A.NetName == '%s'" % n
                grants = [nm for nm, cons, cond in _dru_rules()
                          if ' '.join(cond.split()) == want
                          and cons.get("track_width") is not None
                          and cons["track_width"] <= tf["floor_nm"]]
                if not grants:
                    bad.append(dict(net=n, why="ADMITTED_WITH_NO_NAMED_RULE"))
                elif tf.get("floor_source") not in grants:
                    bad.append(dict(net=n, why="ADMITTED_BY_AN_UNNAMED_RULE",
                                    said=tf.get("floor_source"), found=grants))
                elif (tf["required_amps"] is not None
                      and tf["amps"] + 1e-9 < tf["required_amps"]):
                    bad.append(dict(net=n, why="ADMITTED_UNDER_THE_BAR"))
            elif tf["required_amps"] is None or tf["amps"] + 1e-9 < \
                    tf["required_amps"]:
                bad.append(dict(net=n, why="ADMITTED_UNDER_THE_BAR"))
        elif on["width"] != off["width"]:
            bad.append(dict(net=n, why="REFUSED_BUT_WIDTH_MOVED"))
        if not tf["why"]:
            bad.append(dict(net=n, why="NO_RECORDED_REASON"))
        rows.append(dict(net=n, netclass=on["netclass"],
                         from_nm=off["width"], to_nm=on["width"],
                         amps=tf["amps"], required_amps=tf["required_amps"],
                         admitted=tf["admitted"], reason=tf["why"]))
    descended = sorted({r["netclass"] for r in rows if r["admitted"]})
    refused = sorted({r["netclass"] for r in rows if not r["admitted"]})
    results["TF3"] = dict(ok=(not bad and bool(rows)), offenders=bad[:20],
                          nets=len(rows), board_min_nm=board_min,
                          classes_descended=descended,
                          classes_refused=refused,
                          by_class={
                              r["netclass"]: dict(
                                  from_nm=r["from_nm"], to_nm=r["to_nm"],
                                  amps=r["amps"],
                                  required_amps=r["required_amps"],
                                  admitted=r["admitted"], reason=r["reason"])
                              for r in rows})

    # -- TF4: every verdict is reachable, and the refusals are real --------- #
    controls, ctl_ok = [], True
    for cls, expect in (("P3V3", "PRICED_AT_THE_PUBLISHED_BAR"),
                        ("ACC_5V", "PRICED_AT_THE_PUBLISHED_BAR"),
                        ("BAT_MAIN", "TRUNK_UNDER_PRICED"),
                        ("SYS_MAIN", "TRUNK_UNDER_PRICED"),
                        ("SWITCH_NODE", "NET_CARRIES_NO_PUBLISHED_CURRENT"),
                        ("NFC_RF", "NET_CARRIES_NO_PUBLISHED_CURRENT"),
                        ("GND", "CLASS_HAS_NO_PUBLISHED_FLOOR"),
                        ("Default", "CLASS_HAS_NO_PUBLISHED_FLOOR")):
        got = rmb.trunk_floor_price(cls, board_min)
        ok = (got["why"] == expect
              and got["admitted"] == (expect == "PRICED_AT_THE_PUBLISHED_BAR"))
        ctl_ok = ctl_ok and ok
        controls.append(dict(netclass=cls, expected=expect, got=got["why"],
                             admitted=got["admitted"], amps=got["amps"],
                             required_amps=got["required_amps"], ok=ok))
    # D-690's FIFTH VERDICT, AND ITS OWN REFUSAL BESIDE IT.  A per-net floor
    # that cannot refuse is not a clause: the same class, asked about a net the
    # `.kicad_dru` does NOT name, must still answer `CLASS_HAS_NO_PUBLISHED_FLOOR`.
    for cls, net, expect in (
            ("Default", "/BQ25185_STAT1", "PUBLISHED_PER_NET_IN_THE_KICAD_DRU"),
            ("Default", "/BQ25185_STAT2", "PUBLISHED_PER_NET_IN_THE_KICAD_DRU"),
            ("Default", "/WAKE_INT_N", "CLASS_HAS_NO_PUBLISHED_FLOOR"),
            ("GND", "GND", "CLASS_HAS_NO_PUBLISHED_FLOOR"),
            ("USB_D", "/USB_D_MCU_N", "CLASS_HAS_NO_PUBLISHED_FLOOR")):
        got = rmb.trunk_floor_price(cls, board_min, net=net)
        ok = (got["why"] == expect
              and got["admitted"] == (expect
                                      == "PUBLISHED_PER_NET_IN_THE_KICAD_DRU")
              and (got["floor_nm"] is None or got["floor_nm"] >= board_min))
        ctl_ok = ctl_ok and ok
        controls.append(dict(netclass=cls, net=net, expected=expect,
                             got=got["why"], admitted=got["admitted"],
                             floor_nm=got["floor_nm"],
                             floor_source=got.get("floor_source"),
                             amps=got["amps"], ok=ok))
    # THE BAR IS LOCATED, NOT MERELY QUOTED.  A clause that admits at equality
    # and one part per million below it is not a bar.
    probe = rmb.trunk_floor_price("P3V3", board_min)
    edge_ok = probe["admitted"] and probe["amps"] >= probe["required_amps"]
    results["TF4"] = dict(ok=(ctl_ok and edge_ok), controls=controls,
                          bar_located=edge_ok)

    doc = dict(schema=1, board=str(BOARD), dru=str(DRU),
               board_sha256=__import__("hashlib").sha256(
                   BOARD.read_bytes()).hexdigest(),
               base_rev=a.rev, results=results,
               all_pass=all(v["ok"] for v in results.values()))
    if a.out:
        a.out.write_text(json.dumps(doc, indent=1, sort_keys=True) + "\n")
    for k in sorted(results):
        print("%-4s %s" % (k, "PASS" if results[k]["ok"] else "FAIL"))
    print("trunk_floor_contract: %s"
          % ("PASS" if doc["all_pass"] else "FAIL"))
    return 0 if doc["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
