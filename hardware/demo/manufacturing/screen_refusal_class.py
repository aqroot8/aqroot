#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AQROOT Demo -- WHICH REFUSAL IS THIS, AND WHICH LEVERS CAN TOUCH IT?  (D-676)

A land that will not close refuses for one of FOUR reasons, and each one admits
a DIFFERENT set of levers.  Nothing in this repository read a refusal and said
which:

    NO_SITE      no legal barrel inside this net's own body pour, cut or uncut
                 -> placement / refloorplan.  A relay lever cannot be spent.
    POUR_PRICE   a stitch was laid, it SPLIT a foreign pour, and the split was
                 refused on price
                 -> `--bond-pad` / `--split-bond-pad` (D-675), a wider arm, or
                    a cut that leaves the priced pad on the body side.
    RELAY        a stitch was laid, no pour was severed, and a cut net would
                 not go back
                 -> the joint arm's other barrels, `--ban-net` cut-set retry
                    (D-641), `--detour-own-layer`, `--evict-whole`.
                    `--bond-pad` IS VACUOUS: there is no fragment to price.
    LANE_UNSAT   as RELAY, and the BARE arm puts the cut chain back at its own
                 length with ZERO vias -- D-667's signature that the chain has
                 one path in that pocket and any reservation over it is
                 unsatisfiable by construction
                 -> stop offering barrels.  Route the protected net FIRST
                    (`--evict-whole`, the evicted net REQUESTED first), or move
                    a part.

D-675 closed by prescribing `--split-bond-pad` for `BQ25185_SYS C26.2` and
`GND J3.A12/B1` on the premise that their refusals were under-priced bonds.
Both are `RELAY` -- `pour_severs` is null in every round of both -- so the
prescribed lever was vacuous before it was written, and the artifacts that say
so were already on disk.  D-638 spent ten barrels on `GND J3.A12/B1` and D-676
spent six more; the BARE arm of the FIRST of those runs already carried the
`LANE_UNSAT` signature.

THIS SCREEN LOADS NO BOARD AND ROUTES NOTHING.  It reads
`screen_relay_transaction.py` and `screen_segment_evict.py` artifacts -- the
files a decision already paid for -- and reports, per land, the refusal class
and the levers that class admits and refuses.  It is a READER: every verdict is
a restatement of numbers in the input, and the `why` field names the key it
came from.
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path

SCHEMA = 1

# Which lever may be spent on which class.  The vacuity claims are the point of
# the screen, so each one names the measurement that makes it vacuous.
LEVERS = {
    "NO_SITE": dict(
        applicable=["placement / refloorplan (apply_part_shift.py)",
                    "a coarser or finer --grid (the site set is a lattice "
                    "verdict -- D-675 section 4)",
                    "--shrink on the barrel (screen_via_site_sweep)"],
        vacuous=[("--bond-pad / --split-bond-pad",
                  "no stitch was laid, so no pour was split and there is no "
                  "fragment to price"),
                 ("--ban-net cut-set retry",
                  "the cut pool is not what refused; no site exists to open"),
                 ("--evict-whole / --detour-spec",
                  "a relay lever answers a relay refusal")]),
    "POUR_PRICE": dict(
        applicable=["--split-priced --split-bond-pad NET:REF.NUM (D-675)",
                    "route_maze_batch.py --bond-pad REF.NUM",
                    "a cut that leaves the priced pad on the body side",
                    "--stitch-width / a wider arm"],
        vacuous=[("--ban-net cut-set retry",
                  "the cut set was accepted; the SPLIT was refused")]),
    "RELAY": dict(
        applicable=["more joint barrels (--joint-tries / --joint-knockout-mm)",
                    "--ban-net cut-set retry (D-641)",
                    "--detour-own-layer",
                    "--evict-whole with the evicted net REQUESTED FIRST",
                    "placement / refloorplan"],
        vacuous=[("--bond-pad / --split-bond-pad",
                  "pour_severs is null in every round that laid a stitch: "
                  "this transaction splits no pour, so PP2 never prices a "
                  "fragment and a bond barrel changes nothing")]),
    "LANE_UNSAT": dict(
        applicable=["--evict-whole with the evicted net REQUESTED FIRST",
                    "placement / refloorplan",
                    "a part change that empties the pocket"],
        vacuous=[("--bond-pad / --split-bond-pad",
                  "pour_severs is null: no fragment is priced"),
                 ("more joint barrels",
                  "the BARE arm -- no reservation at all -- returns the cut "
                  "chain's OWN geometry with zero vias, so every barrel in "
                  "the pocket lands on the chain's only path (D-667)"),
                 ("--ban-net cut-set retry",
                  "the refusing chain is the one the land must cut to reach "
                  "its own site")]),
    "COPPER": dict(
        applicable=["--evict-whole with the evicted net REQUESTED FIRST",
                    "placement / refloorplan",
                    "a part change that empties the pocket"],
        vacuous=[("--bond-pad / --split-bond-pad",
                  "no fragment is priced"),
                 ("more joint barrels, --ban-net, --detour-own-layer, a "
                  "bigger max_mm",
                  "the BARE arm -- the cut removed and NOTHING reserved -- "
                  "still refuses: there is no second path for this chain at "
                  "any reservation (D-667)")]),
    "CLOSED_AT_FLOOR": dict(
        applicable=["an owner-grade `.kicad_dru` width grant (D-610, D-630, "
                    "twice RECORDED NOT TAKEN)",
                    "placement / refloorplan, which is the CTO-scope answer"],
        vacuous=[("a gate run at this rung",
                  "the closing stitch is the BOARD minimum 0.150 mm.  Section "
                  "9 grants 0.200 mm anywhere and this net's own netclass asks "
                  "more; promoting it would lay copper narrower than the board "
                  "publishes without the grant that permits it")]),
    "CANDIDATE": dict(
        applicable=["screen_relay_transaction.py --arm joint, which replaces "
                    "this screen's all-layer disc with the stitch that will "
                    "actually be there",
                    "--stitch-rung, to ask at the width the GATE will use"],
        vacuous=[("a gate run on this artifact alone",
                  "a segment-evict relay is priced behind a DISC and at the "
                  "`.kicad_dru` FLOOR rung; neither is the transaction")]),
    "CLOSED": dict(applicable=["none -- this land closed"], vacuous=[]),
}

# The board's own `min_track_width`.  A stitch AT it is not a routed width this
# repository grants; it is the floor a `.kicad_dru` question sits on.
BOARD_TRACK_MIN_NM = 150000


# `was_mm` is written round(x, 4), so a chain put back on its own geometry
# reads up to 5e-5 mm away from it.  One micron is above that and three orders
# of magnitude below the shortest detour this board has ever accepted.
SAME_MM = 1e-3


def _bare_signature(arm):
    """D-667's lane probe, read.  Returns (status, rows):

        None              the arm is absent -- this artifact did not ask
        "SIGNATURE"       every cut chain came back on its OWN geometry with
                          zero vias, so the chain has one path in this pocket
                          and any reservation over it is unsatisfiable
        "ELSEWHERE"       the chains came back, but at least one took a
                          DIFFERENT path -- the pocket has slack and a barrel
                          may yet fit beside it
        "REFUSED"         a chain would not go back with NOTHING reserved --
                          the copper, not the lane
    """
    if arm is None:
        return None, []
    rows = []
    for t in arm.get("tracks") or ():
        was, mm, vias = t.get("was_mm"), t.get("mm"), t.get("vias")
        same = (t.get("ok") and was is not None and mm is not None
                and abs(mm - was) <= SAME_MM and vias == 0)
        rows.append(dict(net=t.get("net"), ok=bool(t.get("ok")),
                         reason=t.get("reason"), was_mm=was, mm=mm, vias=vias,
                         own_geometry_zero_vias=bool(same)))
    if not rows:
        return None, rows
    if not arm.get("all_relaid"):
        return "REFUSED", rows
    return ("SIGNATURE" if all(r["own_geometry_zero_vias"] for r in rows)
            else "ELSEWHERE"), rows


def classify_relay_land(land):
    """One land of a `screen_relay_transaction.py` artifact."""
    arms = land.get("arms") or {}
    bare_fired, bare_rows = _bare_signature(arms.get("bare"))

    # The search arms, best first: an arm that CLOSED settles the land.
    stitching = [n for n in ("joint", "stitch", "disc", "bare") if n in arms]
    rounds, laid, severed, relay_refusals, site_refusals = [], 0, 0, [], []
    closed_by = None
    for name in stitching:
        arm = arms[name]
        if arm.get("all_relaid") and name != "bare":
            closed_by = name
        for r in arm.get("rounds") or ():
            rounds.append(dict(arm=name, **{k: r.get(k) for k in
                                            ("round", "stitch_ok", "reason",
                                             "stitch_mm", "via_xy",
                                             "accepted")}))
            if r.get("stitch_ok"):
                laid += 1
                if r.get("pour_severs"):
                    severed += 1
                sp = r.get("split_price")
                if sp and not (sp.get("ok") if isinstance(sp, dict) else True):
                    severed += 1
                for t in r.get("relays") or ():
                    if not t.get("ok"):
                        relay_refusals.append(dict(arm=name, round=r["round"],
                                                   net=t.get("net"),
                                                   reason=t.get("reason"),
                                                   was_mm=t.get("was_mm")))
            else:
                site_refusals.append(dict(arm=name, round=r.get("round"),
                                          reason=r.get("reason")))

    bare_only = set(stitching) == {"bare"}
    if bare_only:
        # This artifact asked ONE question -- does the cut chain go back with
        # nothing reserved -- and it is the D-667 lane probe, not a site probe.
        if bare_fired == "SIGNATURE":
            cls = "LANE_UNSAT"
            why = ("the BARE arm returned every cut chain's own geometry with "
                   "zero vias: any reservation in this pocket is "
                   "unsatisfiable by construction (D-667)")
        elif bare_fired == "REFUSED":
            cls = "COPPER"
            why = ("the BARE arm refuses with NOTHING reserved: this chain "
                   "has no second path at any reservation")
        else:
            cls = "RELAY"
            why = ("the BARE arm relaid every chain but at least one took a "
                   "DIFFERENT path, so the pocket has slack a barrel may use")
    elif closed_by:
        # AT WHAT WIDTH?  A land that closes only at the board floor has not
        # been routed -- it has raised a width question (D-676).
        w_nm = land.get("stitch_width_nm")
        if w_nm is not None and w_nm <= BOARD_TRACK_MIN_NM:
            cls = "CLOSED_AT_FLOOR"
            why = ("arm %r relaid every cut net, but the stitch is %.3f mm -- "
                   "the BOARD minimum, below the 0.200 mm granted anywhere and "
                   "below this net's own netclass" % (closed_by, w_nm / 1e6))
        else:
            cls, why = "CLOSED", ("arm %r relaid every cut net at %s"
                                  % (closed_by,
                                     "%.3f mm" % (w_nm / 1e6) if w_nm
                                     else "an unrecorded width"))
    elif laid == 0:
        cls = "NO_SITE"
        why = ("no round laid a stitch: %s"
               % (site_refusals[0]["reason"] if site_refusals else "no rounds"))
    elif severed:
        cls, why = "POUR_PRICE", ("%d of %d laid rounds severed a pour or "
                                  "failed its split price" % (severed, laid))
    elif bare_fired == "SIGNATURE":
        cls = "LANE_UNSAT"
        why = ("%d rounds laid a stitch, none severed a pour, every relay "
               "refused, and the BARE arm returned each cut chain's own "
               "geometry with zero vias" % laid)
    else:
        cls = "RELAY"
        why = ("%d rounds laid a stitch, none severed a pour, %d relay "
               "refusals" % (laid, len(relay_refusals)))
    return dict(refusal_class=cls, why=why, rounds_laid=laid,
                rounds_severing_pour=severed,
                bare_arm_signature=bare_fired, bare_arm=bare_rows,
                relay_refusals=relay_refusals, site_refusals=site_refusals,
                rounds=rounds)


def classify_evict_land(net, land):
    """One land of a `screen_segment_evict.py` artifact."""
    v = land.get("verdict") or ""
    unc = land.get("uncut_escape") or {}
    relay = land.get("relay") or {}
    refusals = [dict(net=t.get("net"), reason=t.get("reason"),
                     was_mm=t.get("was_mm"))
                for t in relay.get("tracks") or () if not t.get("ok")]
    if unc.get("ok"):
        cls, why = "CLOSED", "uncut_escape.ok -- no eviction is needed"
    elif v in ("SEGMENT_WALL", "UNSTABLE") or not v.startswith("SEGMENT"):
        # SEGMENT_WALL is the loudest NO_SITE this repository draws: every
        # candidate track was cut and the barrel still has nowhere to land.
        cls, why = "NO_SITE", "verdict %s: %s" % (v, unc.get("reason"))
    elif relay and not relay.get("all_relaid"):
        cls = "RELAY"
        why = ("verdict %s, but %d cut net(s) would not go back behind this "
               "screen's own all-layer disc" % (v, len(refusals)))
    else:
        # AN EVICT THAT OPENS AND RELAYS IS A CANDIDATE, NOT A CLOSURE.  Its
        # relay is priced behind an all-layer disc and its stitch at the DRU
        # floor; the transaction is neither.
        cls, why = "CANDIDATE", ("verdict %s and every cut net relaid behind "
                                 "this screen's disc" % v)
    return dict(refusal_class=cls, why=why, verdict=v,
                uncut_escape=unc.get("reason"), relay_refusals=refusals,
                cut_tracks=len(land.get("cuts") or ()),
                cut_radius_mm=land.get("cut_radius_mm"),
                note="a disc is the most constraining reservation this "
                     "repository draws; a RELAY here is not final until the "
                     "joint arm of screen_relay_transaction.py has been asked")


def read(path):
    d = json.loads(Path(path).read_text(encoding="utf-8"))
    rows = []
    if "lands" in d and isinstance(d.get("lands"), list) \
            and d["lands"] and "arms" in d["lands"][0]:
        kind = "relay_transaction"
        for l in d["lands"]:
            rows.append(dict(land=l.get("land"), net=l.get("net"),
                             **classify_relay_land(l)))
    elif "nets" in d:
        kind = "segment_evict"
        for rec in d["nets"]:
            for l in rec.get("lands") or ():
                key = "%s:%s" % (rec["net"], (l.get("land") or ["?"])[0])
                rows.append(dict(land=key, net=rec["net"],
                                 **classify_evict_land(rec["net"], l)))
    else:
        kind = "unknown"
    return kind, d, rows


def main():
    ap = argparse.ArgumentParser(
        description="classify a land's refusal and name the levers it admits")
    ap.add_argument("artifacts", nargs="+", type=Path,
                    help="screen_relay_transaction.py or "
                         "screen_segment_evict.py artifacts")
    ap.add_argument("--land", action="append", default=[], metavar="NET:REF",
                    help="only these lands.  Repeatable")
    ap.add_argument("--authority-sha", metavar="SHA256",
                    help="the board this decision is about.  Rows taken on "
                         "another board are still read -- a refusal class is "
                         "a fact about the copper that was there -- but the "
                         "report names which sources are current, so a stale "
                         "probe is never mistaken for a live one")
    ap.add_argument("-o", "--out", type=Path)
    a = ap.parse_args()

    want = set(a.land)
    out = []
    for p in a.artifacts:
        kind, d, rows = read(p)
        for r in rows:
            if want and r["land"] not in want:
                continue
            r["source"] = str(p)
            r["source_kind"] = kind
            r["source_sha256"] = hashlib.sha256(p.read_bytes()).hexdigest()
            r["board_sha256"] = d.get("board_sha256")
            r["levers"] = LEVERS[r["refusal_class"]]
            r["bond_pad_applicable"] = (r["refusal_class"] == "POUR_PRICE")
            out.append(r)

    counts = {}
    for r in out:
        counts[r["refusal_class"]] = counts.get(r["refusal_class"], 0) + 1

    # THE MERGE IS THE INSTRUMENT.  A bare probe and a joint search are two
    # FILES; `LANE_UNSAT` is only visible when they are read together, which is
    # exactly why nobody read it.  Strongest evidence wins, in this order.
    RANK = ("CLOSED", "POUR_PRICE", "COPPER", "LANE_UNSAT", "RELAY", "NO_SITE")
    merged = {}
    for r in out:
        merged.setdefault(r["land"], []).append(r)
    merge_rows = []
    for land, rows in sorted(merged.items()):
        seen = {x["refusal_class"] for x in rows}
        fired = any(x.get("bare_arm_signature") == "SIGNATURE" for x in rows)
        laid = any(x.get("rounds_laid") for x in rows)
        if "CLOSED" in seen:
            cls, why = "CLOSED", "at least one artifact closed this land"
        elif "CLOSED_AT_FLOOR" in seen:
            cls = "CLOSED_AT_FLOOR"
            why = ("the only arm that closed this land did so at the BOARD "
                   "minimum track width; the transaction is a `.kicad_dru` "
                   "width grant, not a route")
        elif "POUR_PRICE" in seen:
            cls, why = "POUR_PRICE", "a laid round severed a pour"
        elif "COPPER" in seen:
            cls, why = "COPPER", "the bare probe refuses with nothing reserved"
        elif fired and (laid or "RELAY" in seen or "NO_SITE" in seen):
            cls = "LANE_UNSAT"
            why = ("a joint/disc search laid stitches and every relay refused, "
                   "and a separate BARE probe returned the chain's own "
                   "geometry with zero vias")
        elif "RELAY" in seen:
            cls, why = "RELAY", "stitches were laid and a relay refused"
        elif "CANDIDATE" in seen:
            cls, why = "CANDIDATE", ("a segment-evict opened this land and "
                                     "relaid every cut behind its disc; no "
                                     "arm has closed it at a stated rung")
        else:
            cls, why = "NO_SITE", "no artifact laid a stitch"
        # AN ARTIFACT IS ABOUT THE BOARD IT WAS TAKEN ON.  Merging D-638's
        # probe with D-676's search is only legitimate while both still
        # describe copper that is there, so the report NAMES every board it
        # read and says which rows are the current authority.
        shas = sorted({x.get("board_sha256") for x in rows if
                       x.get("board_sha256")})
        on_authority = [x["source"] for x in rows
                        if a.authority_sha
                        and x.get("board_sha256") == a.authority_sha]
        merge_rows.append(dict(
            land=land, refusal_class=cls, why=why,
            bond_pad_applicable=(cls == "POUR_PRICE"),
            levers=LEVERS[cls],
            rounds_laid=sum(x.get("rounds_laid") or 0 for x in rows),
            bare_signature=fired,
            board_sha256=shas,
            boards_differ=len(shas) > 1,
            sources_on_authority=on_authority,
            authority_sha256=a.authority_sha,
            sources=[x["source"] for x in rows],
            per_source={x["source"]: x["refusal_class"] for x in rows}))

    rep = dict(schema=SCHEMA, merged=merge_rows,
               question="which of NO_SITE / POUR_PRICE / RELAY / LANE_UNSAT "
                        "is this land's refusal, and which levers can touch it",
               method="read-only; no board is loaded and nothing is routed.  "
                      "Every verdict restates numbers already in the named "
                      "artifact and `why` names the key it came from",
               counts=counts, lands=out)
    txt = json.dumps(rep, indent=2, sort_keys=True)
    if a.out:
        a.out.write_text(txt + "\n", encoding="utf-8")
    for r in out:
        print("  %-34s %-11s bond_pad=%-5s  %s"
              % (r["land"], r["refusal_class"],
                 str(r["bond_pad_applicable"]).lower(), r["why"][:80]))
    print("  -- merged across %d artifact(s) --" % len(a.artifacts))
    for r in merge_rows:
        print("  %-34s %-11s bond_pad=%-5s  %s"
              % (r["land"], r["refusal_class"],
                 str(r["bond_pad_applicable"]).lower(), r["why"][:80]))
    if not a.out:
        print(txt)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
