#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AQROOT Demo -- a narrow escape is a CURRENT decision, and the SCHEMATIC
already says which lands carry current.

D-628 made pour severance a PRICED question: `PP2` admits a split only when the
conductor replacing the severed copper carries the design current `.kicad_dru`
section 5 publishes for that pour's NET.  That clause is right for a rail and
it is the reason nothing has moved on the escape-relief front since D-610,
because it charges EVERY land of `+3V3` the whole eighty-pad rail's **1.0 A**:

    D-610 promoted `U12.4` at 0.200 mm -- 0.742 A against 1.0 A -- and had to
    rule it "ONE NECK, KNOWINGLY DERATED, BECAUSE THE ALTERNATIVE IS AN OPEN
    RAIL".  That ruling is sound, and it is sound BECAUSE `U12.4` is the
    `TPS63020`'s own `VOUT`: the whole rail really does pass through it.

    `U4.12` is the `BMI270`'s `CSB` pin.  Bosch's own instruction, quoted in
    this board's schematic note, is "hard-wire the CSB line to VDDIO"; it
    selects I2C mode and it is a HIGH-IMPEDANCE INPUT.  Charging that land
    1.0 A is not conservatism, it is a category error, and it has been
    silently refusing the only instrument that can reach the land.

THE DISCRIMINATOR IS PUBLISHED, STRUCTURED AND ALREADY IN THIS REPOSITORY.
KiCad's own netlist carries a `pintype` for every node, straight from the
symbol the schematic instantiates.  `power_in` / `power_out` is a SUPPLY PORT:
current for the device behind it flows through this copper.  `input`,
`output`, `bidirectional`, `tri_state` are SIGNAL pins: no device draws its
supply through them.  This file reads that field and nothing else, so the
verdict is the schematic's, not the reader's.

  LL1  A LAND IS CLASSIFIED FROM THE SCHEMATIC, PER PIN.

         SUPPLY_PORT        `pintype` is `power_in` or `power_out`.  Current
                            for whatever is behind this pin flows here.

         SIGNAL_PIN         `pintype` is `input`, `output`, `bidirectional`,
                            `tri_state`, `open_collector`, `open_emitter`,
                            `unspecified` or `no_connect`.  A device pin that
                            is not a supply port; its current is its own drive
                            or leakage, never the rail's.

         BOUNDED_PASSIVE    `pintype` is `passive`, the part has exactly TWO
                            terminals, and its VALUE publishes a resistance of
                            at least `LEAF_MIN_OHMS`.  Then the current in this
                            copper is bounded above by V/R WHATEVER the far
                            terminal reaches -- the resistor is the bound, and
                            it is a published figure.

         UNBOUNDED_PASSIVE  any other `passive`: a 0 R link, an inductor, a
                            ferrite, a capacitor, a switch, a connector
                            contact, a test point.  Current through it is NOT
                            bounded by anything this file can read.

  LL2  AN ISLAND IS A SIGNAL LEAF only when it holds at least one land and
       EVERY land on it is `SIGNAL_PIN` or `BOUNDED_PASSIVE`.  One supply port
       or one unbounded passive and the island is `RAIL`.

  LL3  A CONDUCTOR SERVING A SIGNAL-LEAF ISLAND IS NOT A RAIL CONDUCTOR.  No
       device draws its supply through it, so the published rail current does
       not bind it and the D-628 bar does not apply.  What binds it is the
       board's own `min_track_width` and whatever the `.kicad_dru` licenses
       where the copper actually lies -- which is the ordinary signal contract
       this board applies to every signal net it has ever routed.

  LL4  OTHERWISE THE RAIL BAR STANDS, UNCHANGED.  This clause only ever
       REMOVES a charge that was never owed; it never lowers one that is.

  LL5  THE BOUND IS COMPUTED AT A VOLTAGE ABOVE EVERY RAIL THIS BOARD CARRIES
       (`BOUND_VOLTS`, 5.5 V -- above `BAT_MAIN`'s 4.35 V ceiling and above
       USB VBUS's 5.25 V), so a reported bound is an upper bound whatever the
       net.  The bound is CORROBORATION.  The VERDICT is structural: an island
       with no supply port on it is not fed through this copper, and that is
       true at any voltage.

  LL6  THE CONTROLS DRIVE THE SAME `classify_land` THE VERDICT DOES, and they
       run on EVERY board.  A clause that cannot refuse is not a clause: the
       controls below require the classifier to refuse this board's real supply
       ports by name and to admit its real straps by name, and to find at least
       one land of every class board-wide.  A control that misbehaves FAILS the
       contract.

WHAT THIS FILE DOES NOT DO.  It does not decide whether copper is routable,
where it may lie, or whether a licence exists: `.kicad_dru`, KiCad's DRC and
the gate keep those questions.  It answers exactly one: IS THIS A RAIL
CONDUCTOR?  A `SIGNAL_LEAF` verdict is a licence to STOP CHARGING the rail
current, and nothing else.

    python3 leaf_land_contract.py [--board B] [--net N ...] [-o OUT]
"""
import argparse
import hashlib
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
PROJECT = ROOT / "hardware/demo/kicad/aqroot-demo"
BOARD = PROJECT / "aqroot-Beta-v2.kicad_pcb"
SCHEMATIC = PROJECT / "aqroot-Beta-v2.kicad_sch"
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(ROOT / "hardware/beta-v2/checks"))

# 1 kOhm at 5.5 V is 5.5 mA.  The figure is not tuned to any land on this
# board: it is the decade at which a resistor stops being a series element in
# a power path and becomes a pull, and every pull this board fits is 2.2 k or
# larger.  A 220 R series signal resistor is REFUSED by it, which is correct --
# a 220 R in a rail would be a current-limiting element and its copper carries
# whatever the rail delivers into it.
LEAF_MIN_OHMS = 1000.0

# Above `BAT_MAIN`'s 4.35 V charge ceiling and above USB VBUS's 5.25 V maximum,
# so V/R is an upper bound on ANY net of this board.  See LL5.
BOUND_VOLTS = 5.5

SUPPLY_TYPES = frozenset(("power_in", "power_out"))
SIGNAL_TYPES = frozenset(("input", "output", "bidirectional", "tri_state",
                          "open_collector", "open_emitter", "unspecified",
                          "no_connect", "free"))

SUPPLY_PORT = "SUPPLY_PORT"
SIGNAL_PIN = "SIGNAL_PIN"
BOUNDED_PASSIVE = "BOUNDED_PASSIVE"
UNBOUNDED_PASSIVE = "UNBOUNDED_PASSIVE"
UNRESOLVED = "UNRESOLVED"

LEAF_CLASSES = frozenset((SIGNAL_PIN, BOUNDED_PASSIVE))


# --------------------------------------------------------------------------- #
# the netlist, read as KiCad wrote it
# --------------------------------------------------------------------------- #
_TOK = re.compile(r'\s*(?:("(?:[^"\\]|\\.)*")|(\()|(\))|([^\s()"]+))')


def read_sexp(text):
    pos, stack, cur, n = 0, [], [], len(text)
    while pos < n:
        m = _TOK.match(text, pos)
        if not m:
            break
        pos = m.end()
        if m.group(2):
            stack.append(cur)
            cur = []
        elif m.group(3):
            done, cur = cur, stack.pop()
            cur.append(done)
        elif m.group(1):
            cur.append(m.group(1)[1:-1].encode().decode("unicode_escape"))
        else:
            cur.append(m.group(4))
    return cur[0] if len(cur) == 1 else cur


def kids(node, tag):
    return [c for c in node if isinstance(c, list) and c and c[0] == tag]


def val(node, tag, default=None):
    for c in node or ():
        if isinstance(c, list) and c and c[0] == tag:
            return c[1] if len(c) > 1 else True
    return default


def netlist(schematic: Path):
    """{(ref, pin): node} and {ref: comp}, exported by kicad-cli itself."""
    with tempfile.TemporaryDirectory(prefix="aqroot-ll-") as tmp:
        out = Path(tmp) / "n.net"
        subprocess.run(["kicad-cli", "sch", "export", "netlist",
                        "--format", "kicadsexpr", "-o", str(out),
                        str(schematic)],
                       check=True, text=True, capture_output=True)
        doc = read_sexp(out.read_text(encoding="utf-8"))
    comps = {val(c, "ref"): c for c in kids(kids(doc, "components")[0], "comp")}
    nodes = {}
    for nt in kids(kids(doc, "nets")[0], "net"):
        name = val(nt, "name")
        for nd in kids(nt, "node"):
            nodes[(val(nd, "ref"), val(nd, "pin"))] = dict(
                net=name, pintype=val(nd, "pintype"),
                pinfunction=val(nd, "pinfunction"))
    return nodes, comps


# --------------------------------------------------------------------------- #
# the published resistance
# --------------------------------------------------------------------------- #
_MULT = {"": 1.0, "R": 1.0, "K": 1e3, "M": 1e6}
# "100k", "4.7k", "1M", "220R", "0R", and the "4k7" form.  A tolerance or
# power suffix may follow as a separate word and is ignored; ANYTHING ELSE --
# "10uF 10V X7R", "1uH", "SW_SPDT", "BMI270" -- fails to parse and the land is
# UNBOUNDED, which is the refusing answer.
_R_PLAIN = re.compile(r"^(\d+(?:\.\d+)?)\s*([RKM]?)$", re.I)
_R_INFIX = re.compile(r"^(\d+)([RKM])(\d+)$", re.I)


def parse_resistance(value):
    if not value:
        return None
    head = value.split()[0]
    m = _R_PLAIN.match(head)
    if m:
        return float(m.group(1)) * _MULT[m.group(2).upper()]
    m = _R_INFIX.match(head)
    if m:
        return (float(m.group(1)) + float("0." + m.group(3))) \
            * _MULT[m.group(2).upper()]
    return None


def terminal_count(comp, nodes, ref):
    return sum(1 for (r, _p) in nodes if r == ref)


# --------------------------------------------------------------------------- #
# LL1 -- the classifier the controls drive
# --------------------------------------------------------------------------- #
def classify_land(ref, pin, nodes, comps, bound_volts=BOUND_VOLTS):
    node = nodes.get((ref, pin))
    if node is None:
        return dict(land="%s.%s" % (ref, pin), klass=UNRESOLVED, ohms=None,
                    bound_amps=None, pintype=None, pinfunction=None,
                    value=None,
                    why="this pad has no node in the schematic netlist -- a "
                        "board/schematic parity failure, not a leaf")
    comp = comps.get(ref)
    value = val(comp, "value") if comp else None
    t = (node["pintype"] or "").lower()
    rec = dict(land="%s.%s" % (ref, pin), pintype=t,
               pinfunction=node["pinfunction"], value=value, ohms=None,
               bound_amps=None)
    if t in SUPPLY_TYPES:
        rec.update(klass=SUPPLY_PORT,
                   why="the schematic declares this pin '%s': it is a SUPPLY "
                       "PORT and the device behind it draws through this "
                       "copper" % t)
        return rec
    if t in SIGNAL_TYPES:
        rec.update(klass=SIGNAL_PIN,
                   why="the schematic declares this pin '%s': a device SIGNAL "
                       "pin, which draws no supply through this copper" % t)
        return rec
    if t == "passive":
        terminals = terminal_count(comp, nodes, ref)
        ohms = parse_resistance(value)
        rec["ohms"] = ohms
        if terminals == 2 and ohms is not None and ohms >= LEAF_MIN_OHMS:
            rec.update(klass=BOUNDED_PASSIVE,
                       bound_amps=round(bound_volts / ohms, 9),
                       why="a two-terminal part whose published value %s is "
                           "%.0f ohm >= %.0f ohm, so the current here is at "
                           "most %.3f mA at %.2f V whatever the far terminal "
                           "reaches" % (value, ohms, LEAF_MIN_OHMS,
                                        1000.0 * bound_volts / ohms,
                                        bound_volts))
            return rec
        rec.update(klass=UNBOUNDED_PASSIVE,
                   why="a 'passive' terminal of a part with %d terminal(s) and "
                       "value %r: no published resistance >= %.0f ohm bounds "
                       "the current in this copper"
                       % (terminals, value, LEAF_MIN_OHMS))
        return rec
    rec.update(klass=UNBOUNDED_PASSIVE,
               why="unrecognised pintype %r -- refused, because a class this "
                   "file does not know is not a class it may admit" % t)
    return rec


# --------------------------------------------------------------------------- #
# LL2/LL3 -- the island verdict
# --------------------------------------------------------------------------- #
def decide(land_refs, nodes, comps, bound_volts=BOUND_VOLTS):
    """`land_refs` are "REF.NUM" strings.  Returns the island's verdict."""
    lands = []
    for r in land_refs:
        ref, _, pin = r.rpartition(".")
        lands.append(classify_land(ref, pin, nodes, comps, bound_volts))
    refused = [l for l in lands if l["klass"] not in LEAF_CLASSES]
    leaf = bool(lands) and not refused
    bounds = [l["bound_amps"] for l in lands if l["bound_amps"] is not None]
    return dict(
        verdict="SIGNAL_LEAF" if leaf else "RAIL",
        admitted=leaf,
        lands=lands,
        refused_lands=[l["land"] for l in refused],
        bounded_amps_total=(round(sum(bounds), 9) if bounds else None),
        why=("every land on this island is a device SIGNAL pin or a bounded "
             "passive: NO SUPPLY PORT is fed through this copper, so the "
             "published rail current does not bind it (LL3)"
             if leaf else
             ("this island is empty" if not lands else
              "%s is %s, so the rail bar stands unchanged (LL4)"
              % (refused[0]["land"], refused[0]["klass"]))))


# --------------------------------------------------------------------------- #
# LL6 -- controls
# --------------------------------------------------------------------------- #
# Each entry is (land, required class).  These are read off THIS board's own
# schematic and each one is a sentence the `.kicad_dru` or the schematic note
# already states in prose.
CONTROLS = (
    # supply ports that must be REFUSED
    ("U1.2", SUPPLY_PORT),        # ESP32-S3-WROOM-1 3V3
    ("U4.5", SUPPLY_PORT),        # BMI270 VDDIO -- C7's own pin
    ("U4.8", SUPPLY_PORT),        # BMI270 VDD   -- C6's own pin
    ("U12.10", SUPPLY_PORT),      # TPS63020 VIN
    ("U11.1", SUPPLY_PORT),       # BQ25185 SYS  -- a power_out
    ("U9.16", SUPPLY_PORT),       # ST25R3916 driver ground
    ("U13.3", SUPPLY_PORT),       # TPS61023 VIN
    # signal pins that must be ADMITTED
    ("U4.12", SIGNAL_PIN),        # BMI270 CSB, hard-wired to VDDIO per Bosch
    ("U4.2", SIGNAL_PIN),         # BMI270 ASDx, unused secondary interface
    ("U4.3", SIGNAL_PIN),         # BMI270 ASCx, unused secondary interface
    # bounded passives that must be ADMITTED
    ("R129.1", BOUNDED_PASSIVE),  # 100 k ACC_DETECT_N pull-up top
    ("R127.1", BOUNDED_PASSIVE),  # 10 k BQ25185_STAT1 pull-up top
    # unbounded passives that must be REFUSED
    ("R118.1", UNBOUNDED_PASSIVE),   # 0 R address strap link
    ("L4.1", UNBOUNDED_PASSIVE),     # 1 uH inductor
    ("SW9.2", UNBOUNDED_PASSIVE),    # SPDT switch contact
    ("C24.1", UNBOUNDED_PASSIVE),    # 10 uF bulk capacitor
)


def controls(nodes, comps, bound_volts=BOUND_VOLTS):
    out = []
    for land, want in CONTROLS:
        ref, _, pin = land.rpartition(".")
        got = classify_land(ref, pin, nodes, comps, bound_volts)
        out.append(dict(land=land, want=want, got=got["klass"],
                        ok=got["klass"] == want, pintype=got["pintype"],
                        value=got["value"], ohms=got["ohms"],
                        bound_amps=got["bound_amps"]))
    return out


def coverage(nodes, comps, bound_volts=BOUND_VOLTS):
    """Every class must EXIST on this board, or the classifier is untested."""
    seen = {}
    for (ref, pin) in nodes:
        k = classify_land(ref, pin, nodes, comps, bound_volts)["klass"]
        seen[k] = seen.get(k, 0) + 1
    return seen


# --------------------------------------------------------------------------- #
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--board", type=Path, default=BOARD)
    ap.add_argument("--schematic", type=Path, default=SCHEMATIC)
    ap.add_argument("--net", action="append", default=[],
                    help="judge the islands of this net (repeatable).  "
                         "Default: every net that owns a filled pour.")
    ap.add_argument("--bound-volts", type=float, default=BOUND_VOLTS)
    ap.add_argument("-o", "--out", type=Path)
    a = ap.parse_args()

    import qrouter as qr
    import maze3d as mz

    nodes, comps = netlist(a.schematic)
    ctl = controls(nodes, comps, a.bound_volts)
    cov = coverage(nodes, comps, a.bound_volts)
    ctl_ok = all(c["ok"] for c in ctl)
    cov_ok = all(cov.get(k, 0) > 0 for k in
                 (SUPPLY_PORT, SIGNAL_PIN, BOUNDED_PASSIVE,
                  UNBOUNDED_PASSIVE))

    qb = qr.QBoard(str(a.board))
    nets = list(a.net)
    if not nets:
        nets = sorted({z.GetNetname() for z in qb.b.Zones()
                       if not z.GetIsRuleArea() and z.IsFilled()
                       and z.GetNetname()})
    report = []
    for net in nets:
        islands = mz.net_islands(qb, net)
        if not islands:
            continue
        body = max(islands, key=len)
        for isl in islands:
            refs = sorted(p["ref"] for p in isl)
            d = decide(refs, nodes, comps, a.bound_volts)
            report.append(dict(net=net, is_body=(isl is body),
                               pads=len(refs), island_lands=refs, **d))

    unresolved = [r for r in report
                  if any(l["klass"] == UNRESOLVED for l in r["lands"])]
    ok = ctl_ok and cov_ok and not unresolved
    doc = dict(
        schema=1, board=str(a.board),
        board_sha256=hashlib.sha256(a.board.read_bytes()).hexdigest(),
        schematic=str(a.schematic),
        schematic_sha256=hashlib.sha256(a.schematic.read_bytes()).hexdigest(),
        leaf_min_ohms=LEAF_MIN_OHMS, bound_volts=a.bound_volts,
        ok=ok, controls_ok=ctl_ok, coverage_ok=cov_ok,
        controls=ctl, coverage=cov,
        unresolved_islands=[r["island_lands"] for r in unresolved],
        islands=report,
        what=("LL1-LL6: which islands of a pour-served net are fed through "
              "this copper, decided from KiCad's own pintype field"))
    text = json.dumps(doc, indent=1, sort_keys=True)
    if a.out:
        a.out.write_text(text + "\n", encoding="utf-8")
    for r in report:
        if r["is_body"]:
            continue
        print("%-32s %-11s %-2d %s%s"
              % (r["net"][:32], r["verdict"], r["pads"],
                 ",".join(r["island_lands"][:4]),
                 "" if r["admitted"] else "  <- " + r["why"][:70]))
    print("controls %s (%d/%d)  coverage %s %s"
          % ("PASS" if ctl_ok else "FAIL",
             sum(1 for c in ctl if c["ok"]), len(ctl),
             "PASS" if cov_ok else "FAIL", cov))
    print("leaf_land_contract: %s" % ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
