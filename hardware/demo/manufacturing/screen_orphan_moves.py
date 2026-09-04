#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AQROOT Demo -- READ-ONLY: OFFER EVERY MOVE THE BOARD OWNS TO EVERY ORPHAN.

D-611.  The D-610 addendum found `maze3d.relief_stitch` recording lands it had
never asked about under `NO_ESCAPE` -- the same word a MEASURED refusal uses --
and ruled that the next task was a measurement, not a route.  This is that
instrument, and it is general: it does not name a land, a net or a lever.  It
enumerates every ORPHAN ISLAND of every pour-owning net on the board and offers
each one, independently and read-only, the moves this board actually owns.

THE TWO MOVES, AND THEY AIM AT DIFFERENT COPPER.

  RELIEF   `maze3d.stitch_pad` -- escape the pad, run a little, drop a barrel
           INTO THE PLANE BODY.  Every relief the doctrine has ever spent is
           this move.  It needs the pour to REACH the land.

  JOIN     `maze3d.route_join` against the MAIN island's nearest pads -- the
           whole-board, all-layer maze the plane-less nets use, and the one
           `join_residual_islands` drives.  It aims at COPPER THAT IS ALREADY
           CONNECTED, not at the pour's own body, so a pour that does not
           reach the land does not by itself refuse it.

THE TWO RUNGS, AND THEY BRACKET THE WHOLE LADDER.

  ORDINARY   the netclass width and the 0.650/0.400 mm POWER-class barrel.
             A move that opens HERE needs no licence, no rule area and no
             narrow copper.  It is ordinary board copper.

  PERMISSIVE 0.200 mm -- the `.kicad_dru` pad-escape necking rule's own
             minimum, the narrowest width this board grants ANYWHERE -- and
             the 0.350/0.200 mm D-257 fine-pitch barrel, the smallest hole
             its process licenses.  Nothing coarser than ORDINARY and nothing
             finer than PERMISSIVE can be asked for, so a move that refuses
             at PERMISSIVE refuses on the whole ladder.

THE BRACKET IS SOUND BECAUSE THE FIELD IS MONOTONE IN BOTH LEVERS.  `Field`
blocks a cell when copper of the given width plus its clearance does not fit,
and `via_ok` blocks one when the barrel plus its clearance does not; both relax
as the number shrinks, and `body_landing` is derived from the same field, so
the landing set only grows.  D-610's 36-rung `U12.4` grid is the empirical
check: it opened at exactly the PERMISSIVE corner and refused at all 34 others.

READING THE ANSWERS.  `stitch_pad` distinguishes the two walls and the
distinction is the whole value of this screen:

  NO_LEGAL_ESCAPE    the LAND cannot launch a track of that width at all --
                     a pocket wall, and narrowing the run is the lever;
  NO_BODY_VIA_SITE   the land escapes and runs, and then there is NOWHERE IN
                     THE PLANE BODY for the barrel to land -- a POUR-SHAPE
                     wall.  No relief licence can move it, because no licence
                     changes where the copper is poured.

NOTHING IS WRITTEN.  Every trial is laid and REVERTED; the board is opened
read-only and never saved.  A move reported OPEN here is a licence to spend a
gate run, not a promise: the full-board gate remains the only thing that
promotes copper.

    usage: screen_orphan_moves.py GUARD.json OUT.json [BOARD.kicad_pcb]
"""

import hashlib
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parents[2] / "hardware/beta-v2/checks")]

import qrouter as qr                                   # noqa: E402
import maze3d as mz                                    # noqa: E402
import route_maze_batch as rb                          # noqa: E402
import routing_ledger as rl                            # noqa: E402
import incremental_router as ir                        # noqa: E402
import pcbnew                                          # noqa: E402

# Every number below is one this board's own `.kicad_dru` already names.
PERMISSIVE_W = 200000               # "Pad-escape necking - width, fine-pitch"
PERMISSIVE_VIA = (350000, 200000)   # D-257 FINE_ESC_* geometry
ORDINARY_VIA = rb.BRIDGE_LADDER[0]  # (650000, 400000) POWER class floor
NEAR = 8                            # `join_residual_islands`'s own default

# A JOIN THAT OPENS IS NOT YET A JOIN THIS BOARD WOULD TAKE.  `route_join` is
# unbounded; the DRIVER bounds it, and for an electrical reason -- a
# plane-served island reached by a long lateral haul has traded a bond for
# inductance and spent outer-layer capacity the unrouted signal nets still
# need.  A screen that reported the raw `ok` would hand a reader a promotion
# the driver would refuse, which is the D-610-addendum mistake wearing the
# other hat.  Every join here is therefore reported against the driver's OWN
# standing bound and labelled `TOO_LONG` when it exceeds it.
JOIN_MAX_MM = rb.REPAIR_JOIN_MAX_MM     # 8.0 mm


# THE PROPOSER AND THE LEDGER DO NOT AGREE ABOUT WHAT AN ORPHAN IS, AND THE
# LEDGER IS THE ONE THE GATE BELIEVES.  `routing_ledger.py` counts a net's open
# edges over the pads of SCHEMATIC-FITTED references only -- a land on a
# do-not-populate part has nothing soldered to it, so no connection is missing
# from the assembled Demo and the ledger never records the edge as open.
# `maze3d.net_islands` has no population model at all: it islands every pad of
# the net.  So the proposer sees orphans the gate cannot count, and a
# transaction that closed one would spend copper, barrels and possibly a
# LICENCE for an improvement clause 4 must score as zero.
#
# This is not hypothetical on this board.  `/01_POWER_TREE/BQ25185_SYS` islands
# TEN ways for `net_islands` and EIGHT for the ledger; the two extra are
# `R68.1` and `U13.3`, both DNP -- and `U13.3` is the single closest-to-bound
# join this screen finds anywhere.  Every island is therefore labelled with the
# population of its lands, and a DNP-only island is named as one.
def fitted_refs():
    """The schematic's FITTED reference set -- the ledger's own authority."""
    fitted, dnp = rl.schematic_population()
    return set(fitted), set(dnp)


def main():
    if len(sys.argv) < 3:
        raise SystemExit(__doc__.strip().splitlines()[-1].strip())
    guard = json.loads(Path(sys.argv[1]).read_text())
    out_path = Path(sys.argv[2])
    board = Path(sys.argv[3]) if len(sys.argv) > 3 else rb.BOARD

    fitted, dnp = fitted_refs()
    doc = dict(schema=1, board=str(board),
               schematic_dnp=sorted(dnp),
               board_sha256=hashlib.sha256(board.read_bytes()).hexdigest(),
               guard=str(sys.argv[1]), near=NEAR,
               rungs=dict(ordinary=dict(via=list(ORDINARY_VIA)),
                          permissive=dict(width=PERMISSIVE_W,
                                          via=list(PERMISSIVE_VIA))),
               nets={})

    qb = qr.QBoard(str(board))
    ir.inject_existing_via_obstacles(qb)
    pour_nets = sorted(n for n in {p["net"] for p in qb.pads.values()}
                       if mz.has_plane(qb, n) and len(mz.net_islands(qb, n)) > 1)
    del qb
    ref = pcbnew.LoadBoard(str(board))
    reserved = rb.reserved_inner_planes(ref)
    contract = {n: rb.net_contract(ref, n) for n in pour_nets}
    del ref

    for net in pour_nets:
        c = contract[net]
        rec = dict(netclass=c["netclass"], class_width=c["width"],
                   clr=c["clr"], clr_pad=c["clr_pad"],
                   body=None, islands={})
        for rung, w, via in (("ordinary", c["width"], ORDINARY_VIA),
                             ("permissive", PERMISSIVE_W, PERMISSIVE_VIA)):
            t0 = time.time()
            qb = qr.QBoard(str(board))
            ir.inject_existing_via_obstacles(qb)
            layers = rb.permitted_layers(qb.routable, c["layers"],
                                         reserved, net)
            field = mz.Field(qb, net, w, c["clr_pad"], c["clr"], via[0],
                             via[1], G=100000, layers=layers,
                             neck=mz.neck_rule(qb),
                             guard=rb.guard_for(guard, net))
            land, _ = mz.body_landing(qb, net, field)
            islands = mz.net_islands(qb, net)
            main = max(islands, key=len)
            rec["body"] = sorted(p["ref"] for p in main)
            plain = mz._meets_floors(via[0], via[1],
                                     rb.via_floors(c["netclass"]))
            for island in islands:
                if island is main:
                    continue
                key = ",".join(sorted(p["ref"] for p in island))
                refs = {p["ref"].split(".")[0] for p in island}
                slot = rec["islands"].setdefault(key, dict(
                    population=("DNP_ONLY" if refs and refs <= dnp
                                else "FITTED" if refs <= fitted
                                else "MIXED"),
                    dnp_refs=sorted(refs & dnp)))

                # MOVE 1 -- RELIEF.  Every land of the island, independently.
                relief = {}
                for pad in island:
                    m = qb.mark()
                    r = mz.stitch_pad(qb, field, pad, max_mm=8.0,
                                      escape_limit=12, land_ok=land)
                    qb.revert(m)
                    relief[pad["ref"]] = dict(
                        ok=bool(r.get("ok")), reason=r.get("reason"),
                        mm=r.get("mm"), layer=r.get("layer"),
                        via_xy=r.get("via_xy"))

                # MOVE 2 -- JOIN, at the MAIN island's nearest pads.
                dst = mz.nearest_pads(island, main, NEAR)
                m = qb.mark()
                j = mz.route_join(qb, field, island, dst, escape_limit=12,
                                  via_cost_mm=1.5)
                qb.revert(m)

                slot[rung] = dict(
                    width=w, via_dia=via[0], via_drill=via[1],
                    plain_barrel=plain,
                    relief=relief,
                    relief_ok=sorted(k for k, v in relief.items() if v["ok"]),
                    join=dict(ok=bool(j.get("ok")), reason=j.get("reason"),
                              why=(str(j.get("why"))[:200]
                                   if j.get("why") else None),
                              mm=j.get("mm"), vias=j.get("vias"),
                              layers=j.get("layers"),
                              max_mm=JOIN_MAX_MM,
                              within_bound=bool(
                                  j.get("ok")
                                  and (j.get("mm") or 0.0) <= JOIN_MAX_MM),
                              dst_pads=sorted(p["ref"] for p in dst)))
                sys.stderr.write(
                    "  %s %s %s relief=%s join=%s\n"
                    % (net, rung, key,
                       (sorted(k for k, v in relief.items() if v["ok"])
                        or sorted({v["reason"] for v in relief.values()})),
                       ("%s %.3fmm %sv"
                        % ("OK" if (j["mm"] or 0.0) <= JOIN_MAX_MM
                           else "TOO_LONG", j["mm"], j.get("vias"))
                        if j.get("ok") else j.get("reason"))))
                sys.stderr.flush()
            del qb, field
            sys.stderr.write("%s %s %.1fs\n" % (net, rung, time.time() - t0))
            sys.stderr.flush()
            doc["nets"][net] = rec
            out_path.write_text(json.dumps(doc, indent=1, sort_keys=True,
                                           default=str) + "\n")

    # The one summary a reader needs: what, if anything, is CLOSABLE, and how.
    closable, out_of_bound, dnp_only = [], [], []
    for net, rec in doc["nets"].items():
        for key, slots in rec["islands"].items():
            if slots.get("population") == "DNP_ONLY":
                # Not a candidate at all: the ledger does not count this edge,
                # so closing it cannot be an improvement.
                dnp_only.append(dict(net=net, island=key,
                                     dnp_refs=slots.get("dnp_refs")))
                continue
            for rung in ("ordinary", "permissive"):
                s = slots.get(rung) or {}
                if s.get("relief_ok"):
                    closable.append(dict(net=net, island=key, rung=rung,
                                         move="relief",
                                         pads=s["relief_ok"]))
                if (s.get("join") or {}).get("within_bound"):
                    closable.append(dict(net=net, island=key, rung=rung,
                                         move="join", mm=s["join"]["mm"],
                                         vias=s["join"]["vias"]))
                elif (s.get("join") or {}).get("ok"):
                    out_of_bound.append(dict(net=net, island=key, rung=rung,
                                             move="join", mm=s["join"]["mm"],
                                             vias=s["join"]["vias"],
                                             max_mm=JOIN_MAX_MM))
    doc["closable"] = closable
    doc["out_of_bound"] = out_of_bound
    doc["dnp_only_islands"] = dnp_only
    doc["join_max_mm"] = JOIN_MAX_MM
    doc["orphan_islands"] = sum(len(r["islands"]) for r in doc["nets"].values())
    out_path.write_text(json.dumps(doc, indent=1, sort_keys=True,
                                   default=str) + "\n")
    print("nets=%d orphan_islands=%d closable=%d out_of_bound=%d dnp_only=%d"
          % (len(doc["nets"]), doc["orphan_islands"], len(closable),
             len(out_of_bound), len(dnp_only)))


if __name__ == "__main__":
    main()
