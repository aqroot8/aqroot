#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AQROOT Demo -- READ-ONLY: WHICH FOREIGN OBJECTS CUT THIS POUR IN PIECES?

D-657.  Every instrument in this directory that meets a fragmented pour asks
the same question in the same direction: *given the cut, what jumper closes
it?*  `screen_island_join.py` offers each orphan island a track to another
cluster, `screen_pour_bridges.py` offers it a barrel, `screen_pad_escape_relief.py`
offers its land a narrower launch.  On `/01_POWER_TREE/BQ25185_SYS` -- this
board's largest residual, six of its retained open edges, and the rail that
carries the `TPS63020`'s `VIN` -- all three refuse at every rung, because the
answer is not a jumper.  A `SYS_MAIN` jumper is 0.800 mm wide and the pockets
these islands sit in are tenths of a millimetre.

So this screen asks the question the other way round:

    the pour is in pieces because FOREIGN COPPER CUT IT.  Which objects, and
    what is the SMALLEST set of them whose absence lets KiCad's own filler
    pour the net back into one piece?

That is a different question with a different answer and a different remedy.
A jumper ADDS copper into a pocket that has no room for it; a cut-blame answer
names copper to MOVE, and `route_maze_batch.py --detour-spec` already removes a
named track and lays it again between its own two ends.  The output of this
screen is therefore a `--detour-spec` draft, not a route.

WHAT IS MEASURED, NOT ASSUMED

  * KiCad's OWN FILLER decides.  Every probe runs `pcbnew.ZONE_FILLER` -- the
    same C++ class `kicad-cli pcb drc --refill-zones` drives -- over the whole
    board and then reads the partition off `GetConnectivity`.  Nothing here
    models a re-pour.  `--cli-control` re-runs one probe through `kicad-cli`
    instead, and the two partitions must agree or the run says so.
  * THE UNIT IS THE ONE A TRANSACTION IS LICENSED IN.  A track description
    together with EVERY exact duplicate of it this board carries is ONE unit
    (D-648 `count`), and a barrel is ONE unit, because a spec that took only
    one of two coincident duplicates would leave the other in the pour.
  * THE AUTHORITATIVE BOARD IS NEVER WRITTEN.  Each probe is a private copy in
    a work directory; the authority's sha256 is taken before and after.
  * A REMOVAL HERE IS A QUESTION, NOT A PROPOSAL.  Nothing promotes.  An object
    this screen names still has to be RELAID somewhere legal, and gate clause 5
    is what prices that.

Q0  baseline: the net's cluster partition as the board stands.
Q1  UPPER BOUND: every removable foreign object in the window at once.  If the
    partition does not improve, the window is the wrong window and the per-net
    and per-object sweeps are skipped.
Q2  each foreign NET alone -- the cheapest answer, when one exists.
Q3  REVERSE-GREEDY minimisation of Q1's open set: offer each unit BACK, longest
    first, and keep it out only if the merge survives without it.  Forward
    greedy would ask O(n^2) refills; this asks n.

    python3 screen_pour_cut_blame.py NET X0 Y0 X1 Y1 [-o OUT.json]
                                     [--layers B.Cu,F.Cu] [--ban NET]...
                                     [--jobs N] [--cli-control]
"""

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
BOARD = ROOT / "hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb"


# --------------------------------------------------------------------------- #
# ONE `LoadBoard` PER PROCESS
# --------------------------------------------------------------------------- #
# `pcbnew.LoadBoard` called twice in one interpreter hands the second board back
# as an unwrapped `SwigPyObject` and every method on it raises -- the limit
# `screen_cut_price.py` and `evidence/d656-sliver-bisect.py` both record.  So a
# probe is a CHILD PROCESS: it loads once, edits, fills, reads and prints.
# --------------------------------------------------------------------------- #

def _edit_child():
    """argv: --edit BOARD REMOVE.json  -- remove the named units and SAVE."""
    import pcbnew
    board, spec = sys.argv[2], Path(sys.argv[3])
    want = {tuple(u) for u in json.loads(spec.read_text())}
    b = pcbnew.LoadBoard(board)
    gone = 0
    for t in list(b.GetTracks()):
        if unit_key(b, t) in want:
            b.Remove(t)
            gone += 1
    b.Save(board)
    (spec.parent / "removed.json").write_text(json.dumps(dict(removed=gone)))
    return 0


def _fill_child():
    """argv: --fill BOARD NET OUT.json [nofill]

    A SEPARATE PROCESS FROM THE EDIT, AND THAT IS NOT TIDINESS.  Removing a
    track and then running `ZONE_FILLER` in the SAME interpreter segfaults
    KiCad 10.0.5 -- the fill walks a connectivity/rtree that still references
    the object Python now owns.  Loading the SAVED board fresh does not.
    """
    import pcbnew
    board, net, out = sys.argv[2], sys.argv[3], Path(sys.argv[4])
    nofill = len(sys.argv) > 5 and sys.argv[5] == "nofill"
    b = pcbnew.LoadBoard(board)
    if not nofill:
        pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    b.BuildConnectivity()
    conn = b.GetConnectivity()
    pads = {}
    for f in b.GetFootprints():
        for p in f.Pads():
            if p.GetNetname() == net and p.GetNumber():
                pads[f.GetReference() + "." + p.GetNumber()] = p
    seen, parts = set(), []
    for k, p in pads.items():
        if k in seen:
            continue
        grp = sorted({i.GetParentFootprint().GetReference() + "." + i.GetNumber()
                      for i in conn.GetConnectedItems(p)
                      if i.GetClass() == "PAD"} | {k})
        grp = [g for g in grp if g in pads]
        seen |= set(grp)
        parts.append(sorted(grp))
    out.write_text(json.dumps(dict(partition=sorted(parts))))
    return 0


def unit_key(board, t):
    """The PHYSICAL identity a `--detour-spec` entry names.

    A via is keyed by its site and geometry on every layer at once; a track by
    net, layer, both ends and width.  Two exact duplicates share a key and are
    therefore ONE unit -- taking one and leaving the other would leave the pour
    cut exactly as it was (D-648).
    """
    import pcbnew
    if t.Type() == pcbnew.PCB_VIA_T:
        p = t.GetPosition()
        return ("via", t.GetNetname(), p.x, p.y, t.GetWidth(), t.GetDrill())
    s, e = t.GetStart(), t.GetEnd()
    a, z = (s.x, s.y), (e.x, e.y)
    if z < a:
        a, z = z, a
    return ("trk", t.GetNetname(), board.GetLayerName(t.GetLayer()),
            a[0], a[1], z[0], z[1], t.GetWidth())


if len(sys.argv) > 1 and sys.argv[1] == "--edit":
    raise SystemExit(_edit_child())
if len(sys.argv) > 1 and sys.argv[1] == "--fill":
    raise SystemExit(_fill_child())


# --------------------------------------------------------------------------- #
# DRIVER
# --------------------------------------------------------------------------- #

def unit_mm(u):
    if u[0] == "via":
        return dict(kind="via", net=u[1], at_mm=[u[2] / 1e6, u[3] / 1e6],
                    dia_mm=u[4] / 1e6, drill_mm=u[5] / 1e6, length_mm=0.0)
    L = ((u[5] - u[3]) ** 2 + (u[6] - u[4]) ** 2) ** 0.5 / 1e6
    return dict(kind="trk", net=u[1], layer=u[2],
                start_mm=[u[3] / 1e6, u[4] / 1e6],
                end_mm=[u[5] / 1e6, u[6] / 1e6],
                width_mm=u[7] / 1e6, length_mm=round(L, 3))


def detour_entry(u, count):
    """The `--detour-spec` entry that names this unit."""
    m = unit_mm(u)
    if m["kind"] == "via":
        return dict(net=m["net"],
                    barrel=dict(at_mm=[round(v, 4) for v in m["at_mm"]],
                                dia_mm=m["dia_mm"], drill_mm=m["drill_mm"]))
    return dict(net=m["net"], layer=m["layer"],
                start_mm=[round(v, 4) for v in m["start_mm"]],
                end_mm=[round(v, 4) for v in m["end_mm"]],
                width_mm=m["width_mm"], count=count)


def _freed(partition, want):
    """Does every `--free` claim hold in this partition?

    A claim is `A.n=B.m` -- these two lands must end in ONE cluster -- or a bare
    `A.n`, which is `A.n` must not be alone.

    THE PAIR IS THE HONEST FORM AND THE DEFAULT IS NOT.  The obvious predicate,
    "the land joins the net's LARGEST cluster", is what `screen_barrel_move.py`
    says, and on `/01_POWER_TREE/BQ25185_SYS` it is a trap: this net's largest
    BASELINE cluster is `{C24.1, C33.1, C64.1, L2.1}` -- three decoupling lands
    and a DNP inductor 90 mm away -- while the cluster that actually delivers
    the rail, `{C28.1, SW9.2, U12.1}`, is SMALLER.  A removal that puts `U11.1`
    where it belongs would tie those two at four lands and be judged against
    whichever sorted first.  So the claim is named, not inferred: `U11.1=U12.1`
    says "the charger's `SYS` output must reach the buck-boost's `SYS` input",
    which is the sentence the transaction is actually being bought for.
    """
    if not partition:
        return False
    where = {}
    for i, c in enumerate(partition):
        for land in c:
            where[land] = i
    for w in want:
        if "=" in w:
            a, z = w.split("=", 1)
            if where.get(a, -1) != where.get(z, -2):
                return False
        else:
            hit = [c for c in partition if w in c]
            if not hit or len(hit[0]) < 2:
                return False
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("net")
    ap.add_argument("window", nargs=4, type=float,
                    metavar=("X0", "Y0", "X1", "Y1"))
    ap.add_argument("--board", type=Path, default=BOARD)
    ap.add_argument("--layers", default=None,
                    help="comma list; default = every layer the net's own "
                         "filled zones occupy")
    ap.add_argument("--ban", action="append", default=[],
                    help="never remove this net's copper (repeatable)")
    ap.add_argument("--work", type=Path, default=None)
    ap.add_argument("--cli-control", action="store_true",
                    help="re-run the Q1 probe through kicad-cli and require "
                         "the two partitions to agree")
    ap.add_argument("--skip-per-net", action="store_true")
    # D-659 -- THE GOAL MAY BE A LAND, NOT THE WHOLE POUR.
    #
    # Until now this screen had exactly one success predicate: the partition
    # must reach the cluster count the ALL-OUT removal reaches.  On `+3V3` that
    # was the right question, because the whole cut was two barrels.  On
    # `/01_POWER_TREE/BQ25185_SYS` at `U11` it is the wrong one and it prices
    # the transaction out: the all-out set frees TWO lands, so the minimisation
    # will not let go of a single object that only the SECOND land needs, and
    # the answer comes back 17 units across five nets.  But the two lands are
    # not worth the same.  `U11.1` is the `BQ25185`'s own `SYS` OUTPUT -- with
    # it severed nothing on this board powers up -- and `C27.1` is its bulk
    # capacitor.  A screen that could only ask for both together could not name
    # the transaction that buys the first one.
    #
    # `--free A.n=B.m` states the goal as a NAMED PAIR that must end in one
    # cluster.  Q1 then tests THAT, the reverse-greedy holds THAT, and
    # `edges_closed` still reports what the whole net gained, so a set bought
    # for one land that happens to free another is not hidden.  See `_freed`
    # for why the pair is named rather than inferred from cluster size.
    ap.add_argument("--free", action="append", default=[],
                    metavar="A.n[=B.m]",
                    help="the goal is that these two lands end in ONE cluster "
                         "(or, bare, that A.n is not alone) -- not that the "
                         "whole pour becomes one piece (repeatable)")
    ap.add_argument("-o", "--out", type=Path)
    a = ap.parse_args()

    import pcbnew
    before = hashlib.sha256(a.board.read_bytes()).hexdigest()
    # THE WORK DIRECTORY IS KEYED ON THE QUESTION, NOT JUST THE BOARD.  Two
    # runs of this screen on the same board -- a different net, or the same net
    # in a different window -- are different questions, and a path that named
    # only the board sha let them share `q0/` and `q1/` and report each other's
    # partitions.  Measured: two concurrent `+3V3` windows disagreed about the
    # BASELINE, which is the one number no removal can move.
    #
    # D-659 -- AND `--ban` IS PART OF THE QUESTION TOO.  "Which objects cut this
    # pour?" and "which objects cut it if the PROTECTED ones are off the table?"
    # are different questions asked of the same net in the same window, and the
    # D-657 key could not tell them apart: the second run would have adopted the
    # first's `q0/`, `q1/` and every `q2_*/` it happened to share a name with
    # and reported the UNBANNED partitions as if the ban had been honoured --
    # which is the one way this screen could say "protected copper is not
    # needed" while measuring a removal that took it.
    tag = hashlib.sha256(
        ("%s|%s|%s|%s|%s|%s"
         % (before, a.net, a.window, a.layers, sorted(a.ban),
            sorted(a.free))).encode()
    ).hexdigest()[:12]
    work = a.work or Path("/tmp/pour_cut_blame_%s" % tag)
    work.mkdir(parents=True, exist_ok=True)

    b = pcbnew.LoadBoard(str(a.board))
    if a.layers:
        layers = set(a.layers.split(","))
    else:
        layers = set()
        for z in b.Zones():
            if z.GetIsRuleArea() or z.GetNetname() != a.net:
                continue
            for lid in z.GetLayerSet().Seq():
                layers.add(b.GetLayerName(lid))
    x0, y0, x1, y1 = [v * 1e6 for v in a.window]
    banned = set(a.ban) | {a.net}

    counts, order = {}, []
    for t in b.GetTracks():
        if t.GetNetname() in banned:
            continue
        if t.Type() == pcbnew.PCB_VIA_T:
            p = t.GetPosition()
            if not (x0 <= p.x <= x1 and y0 <= p.y <= y1):
                continue
        else:
            if b.GetLayerName(t.GetLayer()) not in layers:
                continue
            s, e = t.GetStart(), t.GetEnd()
            if not (x0 <= s.x <= x1 and y0 <= s.y <= y1
                    and x0 <= e.x <= x1 and y0 <= e.y <= y1):
                continue
        k = unit_key(b, t)
        if k not in counts:
            order.append(k)
        counts[k] = counts.get(k, 0) + 1
    del b

    # longest first: a reverse-greedy that offers the EXPENSIVE units back
    # first keeps the removal set cheap to relay.
    order.sort(key=lambda u: (-unit_mm(u)["length_mm"], u[0] != "via", str(u)))

    def probe(tag, remove, cli=False):
        d = work / tag
        d.mkdir(parents=True, exist_ok=True)
        for suf in (".kicad_pcb", ".kicad_dru", ".kicad_pro"):
            src = a.board.with_suffix(suf)
            if src.exists():
                shutil.copy(src, (d / a.board.name).with_suffix(suf))
        brd = d / a.board.name
        spec = d / "remove.json"
        spec.write_text(json.dumps([list(u) for u in remove]))
        res, rem = d / "result.json", d / "removed.json"
        for f in (res, rem):
            if f.exists():
                f.unlink()
        r = subprocess.run([sys.executable, __file__, "--edit", str(brd),
                            str(spec)], capture_output=True, text=True)
        if not rem.exists():
            raise SystemExit("edit %s failed\n%s\n%s"
                             % (tag, r.stdout[-800:], r.stderr[-800:]))
        gone = json.loads(rem.read_text())["removed"]
        nofill = []
        if cli:
            subprocess.run(["kicad-cli", "pcb", "drc", "--refill-zones",
                            "--save-board", "--format", "json", "--units",
                            "mm", "-o", str(d / "drc.json"), str(brd)],
                           capture_output=True, text=True)
            nofill = ["nofill"]
        r = subprocess.run([sys.executable, __file__, "--fill", str(brd),
                            a.net, str(res)] + nofill,
                           capture_output=True, text=True)
        if not res.exists():
            raise SystemExit("fill %s failed\n%s\n%s"
                             % (tag, r.stdout[-800:], r.stderr[-800:]))
        return json.loads(res.read_text())["partition"], gone

    t_all = time.time()
    doc = dict(schema=1, decision="D-657", board=str(a.board),
               board_sha256=before, net=a.net,
               window_mm=list(a.window), layers=sorted(layers),
               banned=sorted(a.ban), free=sorted(a.free),
               goal=("join %s" % ", ".join(sorted(a.free))) if a.free else
                    "pour the whole net back into one piece",
               question="which FOREIGN objects cut this pour into pieces, and "
                        "what is the SMALLEST set whose absence lets KiCad's "
                        "own filler pour it back into one",
               method="pcbnew.ZONE_FILLER (KiCad's own filler) over the whole "
                      "board per probe, partition read off GetConnectivity; "
                      "one LoadBoard per child process; authoritative board "
                      "never written",
               candidates=len(order))

    base, _ = probe("q0", [])
    doc["q0_baseline"] = dict(clusters=len(base), partition=base)
    print("Q0 baseline clusters %d" % len(base), file=sys.stderr, flush=True)

    q1, gone = probe("q1", order)
    doc["q1_upper_bound"] = dict(removed_objects=gone, removed_units=len(order),
                                 clusters=len(q1), partition=q1)
    print("Q1 all-out: %d units / %d objects -> clusters %d (was %d)"
          % (len(order), gone, len(q1), len(base)), file=sys.stderr, flush=True)

    if a.cli_control:
        cli_part, _ = probe("q1cli", order, cli=True)
        doc["cli_control"] = dict(
            partition=cli_part, agrees=(cli_part == q1),
            note="the SAME removal re-poured by kicad-cli and re-read; the "
                 "in-process ZONE_FILLER answer is not trusted on its own")
        print("CLI control agrees: %s" % (cli_part == q1),
              file=sys.stderr, flush=True)

    # THE WINDOW IS JUDGED AGAINST THE GOAL THAT WAS ASKED FOR.  Without
    # `--free` that is "fewer clusters than the baseline"; with it, "these lands
    # are in the body".  A window that shrinks the partition but leaves the
    # named land alone has not held THIS cut and says so.
    if a.free:
        ok1 = _freed(q1, a.free)
        doc["q1_upper_bound"]["freed"] = ok1
    else:
        ok1 = len(q1) < len(base)
    if not ok1:
        doc["verdict"] = "WINDOW_DOES_NOT_HOLD_THE_CUT"
        doc["seconds"] = round(time.time() - t_all, 1)
        _finish(a, doc, before)
        return 0

    target = len(q1)

    def holds(p):
        return _freed(p, a.free) if a.free else len(p) <= target

    if not a.skip_per_net:
        per_net = {}
        for n in sorted({u[1] for u in order}):
            mine = [u for u in order if u[1] == n]
            p, _ = probe("q2_" + n.replace("/", "_").replace("(", "").replace(")", ""),
                         mine)
            per_net[n] = dict(units=len(mine), clusters=len(p), partition=p,
                              alone_sufficient=holds(p))
            print("  Q2 %-40s %2d units -> clusters %d%s"
                  % (n[:40], len(mine), len(p),
                     "   ALONE SUFFICIENT" if holds(p) else ""),
                  file=sys.stderr, flush=True)
        doc["q2_per_net"] = per_net

    keep_out = list(order)
    for u in order:
        trial = [x for x in keep_out if x != u]
        if len(trial) == len(keep_out):
            continue
        p, _ = probe("q3_%d" % order.index(u), trial)
        if holds(p):
            keep_out = trial
            print("  Q3 back  %-56s  still %d" % (str(unit_mm(u))[:56], len(p)),
                  file=sys.stderr, flush=True)
        else:
            print("  Q3 KEEP  %-56s  -> %d" % (str(unit_mm(u))[:56], len(p)),
                  file=sys.stderr, flush=True)

    final, gone = probe("q3_final", keep_out)
    doc["q3_minimal_set"] = dict(
        units=len(keep_out), objects=gone,
        clusters=len(final), partition=final,
        matches_upper_bound=holds(final),
        freed=(_freed(final, a.free) if a.free else None),
        objects_detail=[dict(unit_mm(u), count=counts[u]) for u in keep_out],
        detour_spec=[detour_entry(u, counts[u]) for u in keep_out])
    doc["verdict"] = ("MINIMAL_SET_FOUND" if holds(final)
                      else "REVERSE_GREEDY_DID_NOT_REPRODUCE")
    doc["edges_closed"] = len(base) - len(final)
    doc["seconds"] = round(time.time() - t_all, 1)
    print("Q3 minimal set: %d units / %d objects -> clusters %d, edges closed %d"
          % (len(keep_out), gone, len(final), len(base) - len(final)),
          file=sys.stderr, flush=True)
    _finish(a, doc, before)
    return 0


def _finish(a, doc, before):
    doc["board_sha256_at_write"] = hashlib.sha256(a.board.read_bytes()).hexdigest()
    doc["authoritative_unchanged"] = doc["board_sha256_at_write"] == before
    if a.out:
        a.out.write_text(json.dumps(doc, indent=1, sort_keys=True))
        print("wrote %s" % a.out, file=sys.stderr)
    else:
        print(json.dumps(doc, indent=1, sort_keys=True))


if __name__ == "__main__":
    raise SystemExit(main())
