#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AQROOT Demo -- D-795 / R14-06, D-796 / R15-03 + R15-04.
A GUARANTEE IS BOUND TO THE PRIMARY ROW THE DOCUMENT ITSELF PUBLISHES.

ROUND-14 moved the guaranteed rows out of the model into
`evidence/guaranteed-rows.json`, pinned by sha256, and re-found each row's
text in its archived primary document.  ROUND-15 (Astra R15-03, Fable R15-04)
showed that this still trusted the JSON for everything that MEANS anything:

  * Astra's UNRELATED-ROW REPIN: point a key at a genuine but unrelated row of
    the same hashed PDF, re-pin the JSON -- accepted, because the row text was
    real and nothing asked whether it was THIS quantity's row;
  * Fable's FABRICATED HEADER: the JSON said which columns the row had and
    which of them was MIN/TYP/MAX; a TYP-only row could be given a MAX header;
  * Fable's THREE-EDIT ATTACK: retag a typical, add a JSON row, re-pin.

WHAT THE JSON MAY NOW SAY, AND WHAT IT MAY NOT.  An evidence row carries a
LOCATOR and a set of CLAIMS.  The locator is `line`, a 0-based index into the
document's `pdftotext -layout` text, plus `row_text`, that line verbatim
(whitespace-normalised) -- if either drifts, the row is refused, loudly.  The
claims (`symbol`, `parameter`, `condition`, `table_condition`, `unit`,
`scale`, `value_token`, `bound`, `published_columns`) are each RECOMPUTED FROM
THE DOCUMENT and compared; the JSON can only be refused by being wrong.  From
the document text alone this module derives:

  identity   the document's sha256 and an identity token in its own text;
  header     the table header nearest ABOVE the row on the same page -- a
             MIN/TYP/MAX/UNIT header, an ITEM ... REQUIREMENT header, or (for
             an ordering-code list) the list heading above the bullet;
  columns    every cell of the row is placed under the header label whose
             centre is nearest its own centre in the -layout text, so WHICH
             column a number sits in is the document's, not the JSON's;
  symbol     the row's own symbol cell (or, for a sub-row, the symbol cell
             beside it plus the symbol named in the sub-row's own condition,
             or the item number vertically centred inside the value's cell);
             it must equal the claim AND be named by the registry entry's own
             source text -- so re-pointing a key needs the model edited too;
  value      the published cell whose number x the unit's CANONICAL scale is
             the registry value -- scale is a function of the document's unit,
             never a free JSON number;
  direction  MIN or MAX from the column the value sits in; for a requirement
             cell, a MAX./MIN. word attached to it or a <= / >= sign before
             it; for an ordering code, a +/- tolerance.  GUARANTEED_MAX needs
             MAX, GUARANTEED_MIN needs MIN, GUARANTEED_ROC needs the claimed
             one.  A value in a TYP column can never carry a guarantee;
  unit       the row's own unit cell (or the unit attached to the value), whose
             dimension must also match the registry key's unit suffix;
  condition  the claimed condition must be in the row's own condition text
             (its line plus value-free continuation lines, never a sibling
             sub-row), and the claimed table condition in the table preamble.

So certainty for a quantity takes a hashed vendor document that publishes a
MIN or MAX for THAT symbol, at THAT condition, in THAT unit.  The Round-15
attacks, and the other ways a transcription can lie, are executable
destructive controls in `destructive_controls()`, run on in-memory copies
only; `verdict()` requires every one of them to be caught for the reason it
exists, and an unmutated copy to pass.

D-797 / D797-05 (Astra R16-03, Fable R16-02): THE MEANING IS PINNED, NOT
NARRATED.  D-796 derived the row's semantics from the document, but compared
them with the registry's `source` prose and the evidence JSON's claims -- both
editable.  A coordinated edit of registry + evidence + evidence hash re-points
a key at a GENUINE row with the same number and another parameter or
condition (VLOWV -> VIN_LOWVZ; VBUVLO_HYS VIN = 5 V -> its VIN = 0 V sibling;
IPRECHG_ACC -> ICHG_ACC; ILIM MAX -> the same row's MIN), and every D-796
check agrees.  `checks/guarantee_semantics.py` is now the independent
authority: per key it pins the document (path + sha256), the row's line and
text fingerprint, the table header and title, the symbol, the parameter name,
the distinguishing operating condition and where it must sit, the published
columns, value token, unit, dimension, direction and tag.  That file is
controlled verifier code, pinned here by sha256 (`SEMANTICS_SHA256`) and
loaded as literals only.  Every document-derived field is compared with the
SCHEMA (problems prefixed `SCHEMA:`); the registry key set of GUARANTEED_*
entries must EQUAL the schema's key set.  The coordinated controls first
prove the document-only (D-796) audit ACCEPTS the attack -- so the control is
not vacuous -- and then that the schema refuses it for its named reason.
"""

import ast
import copy
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
EVIDENCE = ROOT / "hardware/demo/manufacturing/evidence/guaranteed-rows.json"
SCHEMA = "aqroot-guarantee-evidence/2"
# D-797 / D797-05: the independent semantic schema and its pin.  Editing the
# schema file needs this constant edited too -- both are verifier code.
SEMANTICS = Path(__file__).resolve().with_name("guarantee_semantics.py")
SEMANTICS_SHA256 = ("cf8be679b05b9ec11fbf609ee606f269"
                    "6ab57984ff44cdefe902588842a0a222")
SEMANTICS_SCHEMA = "aqroot-guarantee-semantics/1"
TYP_WORDS = re.compile(r"\btyp(ical)?\b|typ only|no min|no max", re.I)

# The document's unit decides the scale and the dimension.  These are
# physics, not evidence: they are not in the JSON and cannot be edited there.
UNITS = {
    "A": (1.0, "A"), "mA": (1e-3, "A"),
    "V": (1.0, "V"), "mV": (1e-3, "V"),
    "Ω": (1.0, "ohm"), "mΩ": (1e-3, "ohm"), "milliohms": (1e-3, "ohm"),
    "AΩ": (1.0, "AOhm"),
    "%": (1e-2, "1"),
}
KEY_SUFFIX_DIMENSION = {"A": "A", "V": "V", "ohm": "ohm", "AOhm": "AOhm"}

_MMT_LABELS = {"min", "typ", "max", "nom", "unit"}
_REQ_LABELS = {"requirement", "specifications"}
_CELL = re.compile(r"\S+(?: \S+)*")
_NUM = re.compile(r"^[-+]?\d+(?:\.\d+)?$")
_SYMBOL_SHAPE = re.compile(r"^(?:[A-Z][A-Za-z0-9_]*(?: [A-Z]{1,4})?"
                           r"|\d+(?:\.\d+)+)$")
_REQ_VALUE = re.compile(
    r"^(?P<pre>[≤≥])?\s*(?P<num>[-+]?\d+(?:\.\d+)?)\s*"
    r"(?P<unit>[A-Za-zΩ%]+)(?:\s+(?P<word>MAX|MIN)\.?)?$")
_LIST_VALUE = re.compile(
    r"^•\s*(?P<code>[A-Z0-9]{1,3})\s*=\s*±\s*(?P<num>\d+(?:\.\d+)?)\s*"
    r"(?P<unit>%)$")


def _glyphs(t):
    # One spelling per glyph: en dash and minus sign as '-', the ohm sign
    # (U+2126) as capital omega (U+03A9) -- PDF extraction emits either.
    t = (t or "").replace("–", "-").replace("−", "-")
    return t.replace("Ω", "Ω")


def _norm(t):
    return re.sub(r"\s+", " ", _glyphs(t)).strip()


def _squash(t):
    return re.sub(r"\s+", "", _glyphs(t)).casefold()


def _sha_bytes(b):
    return hashlib.sha256(b).hexdigest()


_SHA_CACHE = {}
_TEXT_CACHE = {}


def _sha(path):
    path = Path(path)
    if path not in _SHA_CACHE:
        _SHA_CACHE[path] = _sha_bytes(path.read_bytes())
    return _SHA_CACHE[path]


def document_text(path):
    path = Path(path)
    if path in _TEXT_CACHE:
        return _TEXT_CACHE[path]
    if path.suffix.lower() == ".pdf":
        out = subprocess.run(["pdftotext", "-layout", str(path), "-"],
                             capture_output=True, text=True)
        txt = out.stdout
    else:
        txt = path.read_text(encoding="utf-8", errors="replace")
    _TEXT_CACHE[path] = txt
    return txt


def document_lines(path):
    # split on '\n' ONLY: str.splitlines() would also split on the form feed
    # pdftotext puts at each page start, and shift every locator.
    return document_text(path).split("\n")


def _cells(line):
    line = _glyphs(line.expandtabs(8))
    return [dict(s=m.start(), e=m.end(), c=(m.start() + m.end()) / 2.0,
                 t=m.group()) for m in _CELL.finditer(line)]


def _is_page_start(line):
    return "\f" in line


# ---------------------------------------------------------------- header --
def _header_of(cells):
    labs = [c["t"].casefold() for c in cells]
    if len(set(labs) & _MMT_LABELS) >= 3 and ({"min", "max"} & set(labs)):
        return "TABLE"
    if (set(labs) & _REQ_LABELS) and labs and labs[0] == "item":
        return "REQUIREMENT"
    return None


def find_header(lines, i, reach=150):
    """The nearest table header ABOVE line i, on the same page."""
    for k in range(i - 1, max(-1, i - reach), -1):
        cells = _cells(lines[k])
        kind = _header_of(cells)
        if kind:
            return k, kind, cells
        if _is_page_start(lines[k]):
            return None
    return None


def _preamble(lines, h):
    out = []
    for k in range(h - 1, max(-1, h - 6), -1):
        if lines[k].strip():
            out.append(_norm(lines[k]))
        if len(out) == 3 or _is_page_start(lines[k]):
            break
    return " ".join(reversed(out))


def _label_of(cell, header):
    best = sorted(header, key=lambda h: abs(h["c"] - cell["c"]))
    return best[0]["t"].upper() if best else None


def _symbol_cell(cells, header):
    """A line's symbol cell: its first cell, symbol-shaped, ending before the
    header's second label starts."""
    if not cells or len(header) < 2:
        return None
    c = cells[0]
    if c["e"] < header[1]["s"] and _SYMBOL_SHAPE.match(c["t"]):
        return c["t"]
    return None


def _value_cells(cells, header, kind):
    out = []
    for c in cells:
        lab = _label_of(c, header)
        if kind == "TABLE" and lab in ("MIN", "TYP", "MAX", "NOM") \
                and (_NUM.match(c["t"]) or c["t"] in ("-", "—")):
            out.append(dict(c, label=lab))
        elif kind == "REQUIREMENT" and lab in ("REQUIREMENT",
                                               "SPECIFICATIONS") \
                and _REQ_VALUE.match(c["t"]):
            out.append(dict(c, label=lab))
    return out


def _sym_eq(a, b):
    return bool(a) and bool(b) and _squash(a) == _squash(b)


def _word_in(word, text):
    return re.search(r"(?<![A-Za-z0-9_])" + re.escape(word) +
                     r"(?![A-Za-z0-9_])", text or "") is not None


# ------------------------------------------------------------ derivation --
def derive_row(lines, i, registry_value):
    """Everything the DOCUMENT says about line i, independent of any JSON
    claim except the registry value it is asked to locate.  Returns a dict
    with `problems` for anything the document itself refuses."""
    d = dict(line=i, problems=[])
    if not (0 <= i < len(lines)):
        d["problems"].append("locator line %r is outside the document" % i)
        return d
    cells = _cells(lines[i])
    d["row_text"] = _norm(lines[i])

    # ---- an ordering-code list ("• F = ±1 %") has no table header -------
    lst = [c for c in cells if _LIST_VALUE.match(c["t"])]
    if lst:
        c = lst[0]
        m = _LIST_VALUE.match(c["t"])
        heading = None
        for k in range(i - 1, max(-1, i - 5), -1):
            for h in _cells(lines[k]):
                if c["s"] - 8 <= h["s"] <= c["s"] + 2 \
                        and not h["t"].startswith("•"):
                    heading = h["t"]
                    break
            if heading or _is_page_start(lines[k]):
                break
        scale = UNITS[m.group("unit")][0]
        v = float(m.group("num"))
        bound = None
        if abs(v * scale - registry_value) <= 1e-9 * max(1, abs(v)):
            bound = "MAX"
        elif abs(-v * scale - registry_value) <= 1e-9 * max(1, abs(v)):
            bound = "MIN"
        d.update(kind="LIST", header=[heading] if heading else [],
                 header_line=None, symbols=[m.group("code")],
                 symbol_rule="list code", unit=m.group("unit"),
                 published_columns=["PLUS_MINUS"], value_token=m.group("num"),
                 bound=bound, parameter_text=heading or "", context="",
                 preamble="", cell_span=[i, i], context_lines=[i])
        if heading is None:
            d["problems"].append("the ordering-code bullet has no heading")
        if bound is None:
            d["problems"].append("the +/- code %s is not the registered "
                                 "value" % c["t"])
        return d

    hdr = find_header(lines, i)
    if hdr is None:
        d["problems"].append("no MIN/TYP/MAX or REQUIREMENT table header "
                             "above this line on its page")
        return d
    h, kind, header = hdr
    d.update(kind=kind, header_line=h,
             header=[x["t"].upper() for x in header],
             preamble=_preamble(lines, h))
    vals = _value_cells(cells, header, kind)
    if not vals:
        d["problems"].append("the located line publishes no value under the "
                             "table's value columns")
        return d

    # ---- value, column, unit, direction ---------------------------------
    hits = []
    if kind == "TABLE":
        unit = next((c["t"] for c in cells
                     if _label_of(c, header) == "UNIT"), None)
        d["unit"] = unit
        d["published_columns"] = [v["label"] for v in vals
                                  if _NUM.match(v["t"])]
        scale = UNITS.get(unit, (None,))[0]
        if scale is None:
            d["problems"].append("the row's unit %r has no canonical scale"
                                 % (unit,))
            return d
        for v in vals:
            if _NUM.match(v["t"]) and abs(float(v["t"]) * scale -
                                          registry_value) <= \
                    1e-9 * max(1.0, abs(registry_value)):
                hits.append(v)
        if len(hits) != 1:
            d["problems"].append(
                "the registered value %r is published %d times on this row "
                "(cells %s, unit %s)" % (registry_value, len(hits),
                                         [v["t"] for v in vals], unit))
            return d
        v = hits[0]
        d["value_token"] = v["t"]
        d["value_column"] = v["label"]
        d["bound"] = v["label"] if v["label"] in ("MIN", "MAX") else None
        span_end = i
    else:
        for v in vals:
            m = _REQ_VALUE.match(v["t"])
            sc = UNITS.get(m.group("unit"), (None,))[0]
            if sc is not None and abs(float(m.group("num")) * sc -
                                      registry_value) <= \
                    1e-9 * max(1.0, abs(registry_value)):
                hits.append((v, m))
        if len(hits) != 1:
            d["problems"].append(
                "the registered value %r is published %d times in this "
                "row's requirement column (cells %s)"
                % (registry_value, len(hits), [v["t"] for v in vals]))
            return d
        v, m = hits[0]
        d["unit"] = m.group("unit")
        d["value_token"] = m.group("num")
        span_end = i
        if m.group("pre") == "≤":
            bound, how = "MAX", "LE_SIGN"
        elif m.group("pre") == "≥":
            bound, how = "MIN", "GE_SIGN"
        elif m.group("word"):
            bound, how = m.group("word"), m.group("word") + "_WORD"
        else:
            bound = how = None
            # the direction word may continue the cell on the next line(s)
            for k in range(i + 1, min(len(lines), i + 3)):
                if _is_page_start(lines[k]):
                    break
                for c in _cells(lines[k]):
                    if c["t"].rstrip(".") in ("MAX", "MIN") and \
                            c["s"] <= v["e"] + 4 and c["e"] >= v["s"] - 4:
                        bound, how, span_end = (c["t"].rstrip("."),
                                                c["t"].rstrip(".") + "_WORD",
                                                k)
                        break
                if bound:
                    break
        d["bound"] = bound
        d["value_column"] = v["label"]
        d["published_columns"] = [how] if how else []
    d["cell_span"] = [i, span_end]

    # ---- symbol ---------------------------------------------------------
    own = _symbol_cell(cells, header)
    syms, rule = [], None
    if own:
        syms, rule = [own], "the row's own symbol cell"
    else:
        near = []
        for step in (-1, 1):
            for k in range(i + step, i + 3 * step, step):
                if not (0 <= k < len(lines)) or _header_of(_cells(lines[k])):
                    break
                s = _symbol_cell(_cells(lines[k]), header)
                if s:
                    near.append((abs(k - i), k, s))
                    break
        # (ii) a sub-row: the symbol beside it, and named in its own text
        for _dist, _k, s in sorted(near):
            if _word_in(_squash(s), _squash(d["row_text"])) or \
                    _word_in(s, d["row_text"]):
                syms.append(s)
                rule = "sub-row: symbol cell adjacent and named in the row"
        # (iii) the symbol is vertically centred inside the value's own cell
        for k in range(i + 1, span_end):
            s = _symbol_cell(_cells(lines[k]), header)
            if s:
                syms.append(s)
                rule = "symbol cell inside the value's multi-line cell"
    d["symbols"] = syms
    d["symbol_rule"] = rule

    # ---- the row's own text: condition context, parameter words ---------
    ctx = [i]
    for step in (-1, 1):
        for k in range(i + step, i + 3 * step, step):
            if not (0 <= k < len(lines)) or _is_page_start(lines[k]) and \
                    step == 1:
                break
            kc = _cells(lines[k])
            if _header_of(kc) or _value_cells(kc, header, kind):
                break
            s = _symbol_cell(kc, header)
            if s and not any(_sym_eq(s, x) for x in syms):
                break
            ctx.append(k)
            if _is_page_start(lines[k]):
                break
    ctx.sort()
    d["context_lines"] = ctx
    d["context"] = " ".join(_norm(lines[k]) for k in ctx)
    return d


# ----------------------------------------------------------------- audit --
def _check_row(key, reg_entry, e, docs):
    why = []
    d = docs.get(e.get("document"))
    if d is None:
        return ["names an unknown document %r" % (e.get("document"),)], None
    f = ROOT / d["path"]
    if not f.exists():
        return ["its document %s is absent" % d["path"]], None
    lines = document_lines(f)
    tok = d.get("token")
    if not tok or tok not in document_text(f):
        why.append("the document's identity token %r is not in its own "
                   "text" % (tok,))
    try:
        rv = float(reg_entry["value"])
        line = int(e["line"])
    except (KeyError, TypeError, ValueError):
        return why + ["the evidence row has no integer `line` locator or the "
                      "registry value is not a number"], None
    der = derive_row(lines, line, rv)
    why += der["problems"]
    # locator anchor
    if _norm(e.get("row_text")) != der.get("row_text"):
        why.append("row_text is not document line %d (which reads %r)"
                   % (line, der.get("row_text")))
    if der["problems"]:
        return why, der
    # symbol: document <-> claim <-> model's own citation
    sym = e.get("symbol")
    if not sym:
        why.append("the evidence row declares no symbol")
    elif not any(_sym_eq(sym, s) for s in der["symbols"]):
        why.append("the row's own symbol is %s, not the declared %r"
                   % (der["symbols"] or "absent", sym))
    src = reg_entry.get("source") or ""
    if sym and not (_word_in(_squash(sym), _squash(src))
                    or _word_in(sym, src)):
        why.append("the registry entry's own source text never names the "
                   "symbol %r: the evidence is for another quantity" % sym)
    # header / columns
    if e.get("published_columns") != der.get("published_columns"):
        why.append("the claimed published columns %r are not the document's "
                   "%r (header %r)" % (e.get("published_columns"),
                                       der.get("published_columns"),
                                       der.get("header")))
    # direction
    want = {"GUARANTEED_MAX": "MAX", "GUARANTEED_MIN": "MIN"}.get(
        reg_entry.get("tag"), e.get("bound"))
    if der.get("bound") not in ("MIN", "MAX"):
        why.append("the value sits in the document's %s column: only a MIN "
                   "or MAX can carry a guarantee"
                   % (der.get("value_column"),))
    elif der["bound"] != want:
        why.append("the document publishes this value as a %s, but the "
                   "registry tag %s needs a %s"
                   % (der["bound"], reg_entry.get("tag"), want))
    if e.get("bound") != der.get("bound"):
        why.append("the claimed bound %r is not the document's %r"
                   % (e.get("bound"), der.get("bound")))
    # value, unit, scale
    if str(e.get("value_token")) != str(der.get("value_token")):
        why.append("the claimed value token %r is not the document's %r"
                   % (e.get("value_token"), der.get("value_token")))
    unit = der.get("unit")
    if e.get("unit") != unit:
        why.append("the claimed unit %r is not the row's unit %r"
                   % (e.get("unit"), unit))
    scale, dim = UNITS.get(unit, (None, None))
    try:
        if scale is None or abs(float(e.get("scale")) - scale) > 1e-15:
            why.append("the declared scale %r is not the canonical %r for "
                       "unit %r" % (e.get("scale"), scale, unit))
    except (TypeError, ValueError):
        why.append("the declared scale is not a number")
    kdim = KEY_SUFFIX_DIMENSION.get(key.rsplit("_", 1)[-1], "1")
    if dim is not None and dim != kdim:
        why.append("the row's unit %r is a %s, the key %s is a %s"
                   % (unit, dim, key, kdim))
    # condition and parameter text
    cond = e.get("condition")
    tcond = e.get("table_condition")
    if der["kind"] != "LIST" and not (cond or tcond):
        why.append("the evidence row states no condition")
    if cond and _squash(cond) not in _squash(der.get("context")):
        why.append("the condition %r is not this row's own condition text "
                   "%r" % (cond, der.get("context")))
    if tcond and _squash(tcond) not in _squash(der.get("preamble")):
        why.append("the table condition %r is not in the table preamble %r"
                   % (tcond, der.get("preamble")))
    par = e.get("parameter")
    if der["kind"] == "LIST" and not par:
        why.append("the evidence row names no parameter")
    if par:
        if der["kind"] == "LIST":
            if _norm(par) != _norm(der.get("parameter_text")):
                why.append("the list heading is %r, not %r"
                           % (der.get("parameter_text"), par))
        elif not all(_word_in(w, der["context"]) for w in par.split()):
            why.append("the parameter %r is not in the row" % par)
        if _squash(par) not in _squash(src):
            why.append("the registry source never names the parameter %r"
                       % par)
    # the row's OWN line and its symbol's line -- not a continuation line,
    # which in a -layout table may be the next row's wrapped description
    own = [lines[k] for k in der["cell_span"]] + [
        lines[k] for k in der["context_lines"]
        if any(_sym_eq(s, (_cells(lines[k]) or [dict(t="")])[0]["t"])
               for s in der["symbols"])]
    if der["kind"] == "TABLE" and TYP_WORDS.search(_norm(" ".join(own))):
        why.append("the row's own text calls it typical")
    return why, der


# ------------------------------------------------ D-797 semantic schema --
def _literal(node, env):
    """A literal, or a NAME bound earlier in the schema file to a literal.
    Anything else -- a call, an attribute, an operator -- is refused."""
    if isinstance(node, ast.Name):
        if node.id not in env:
            raise ValueError("unbound name %r" % node.id)
        return copy.deepcopy(env[node.id])
    if isinstance(node, ast.Dict):
        return {_literal(k, env): _literal(v, env)
                for k, v in zip(node.keys, node.values)}
    if isinstance(node, (ast.List, ast.Tuple)):
        vals = [_literal(x, env) for x in node.elts]
        return vals if isinstance(node, ast.List) else tuple(vals)
    return ast.literal_eval(node)


def load_semantics(text=None):
    """(schema, problems).  The schema module is PARSED, never imported or
    executed: only a docstring and `NAME = <literal>` statements are allowed,
    and its bytes must be the ones `SEMANTICS_SHA256` pins."""
    raw = SEMANTICS.read_bytes() if text is None else text.encode("utf-8")
    problems = []
    if _sha_bytes(raw) != SEMANTICS_SHA256:
        problems.append("SCHEMA: the guarantee semantics schema's sha256 %s "
                        "is not the verifier's pinned %s: the schema was "
                        "edited without re-pinning it in the verifier"
                        % (_sha_bytes(raw), SEMANTICS_SHA256))
    env = {}
    try:
        tree = ast.parse(raw.decode("utf-8"))
        for i, st in enumerate(tree.body):
            if i == 0 and isinstance(st, ast.Expr) and \
                    isinstance(getattr(st, "value", None), ast.Constant):
                continue
            if not (isinstance(st, ast.Assign) and len(st.targets) == 1 and
                    isinstance(st.targets[0], ast.Name)):
                raise ValueError("line %d is not a literal assignment"
                                 % st.lineno)
            env[st.targets[0].id] = _literal(st.value, env)
    except (SyntaxError, ValueError) as ex:
        return None, problems + ["SCHEMA: the semantics schema is not a "
                                 "literal-only module: %s" % ex]
    if env.get("SEMANTICS_SCHEMA") != SEMANTICS_SCHEMA:
        problems.append("SCHEMA: the semantics schema is %r, not %r"
                        % (env.get("SEMANTICS_SCHEMA"), SEMANTICS_SCHEMA))
    return dict(documents=env.get("DOCUMENTS") or {},
                keys=env.get("KEYS") or {}), problems


def _block_text(lines, der):
    """The row's own block: its condition context plus the line(s) that
    carry its symbol cell (a sub-row's parameter name sits on the symbol's
    line).  Never a line past the next header."""
    ks = set(der.get("context_lines") or []) | set(der.get("cell_span") or [])
    i = der["line"]
    for k in range(max(0, i - 3), min(len(lines), i + 4)):
        c = _cells(lines[k])
        if c and any(_sym_eq(s, c[0]["t"]) for s in der.get("symbols") or []):
            ks.add(k)
    return " ".join(_norm(lines[k]) for k in sorted(ks))


def _check_semantics(key, reg_entry, e, docs, der, lines, pin, sem_docs):
    """Compare the DOCUMENT-derived row with the SCHEMA's pinned meaning.
    The registry and the evidence JSON are checked for agreement with the
    schema too, but neither is ever the authority."""
    why = []
    # -- the tag, and the QUANTITY (value token x canonical unit scale) -----
    if reg_entry.get("tag") != pin.get("tag"):
        why.append("SCHEMA: the registry tag %s is not the schema's %s"
                   % (reg_entry.get("tag"), pin.get("tag")))
    scale, dim = UNITS.get(pin.get("unit"), (None, None))
    if scale is None or dim != pin.get("dimension"):
        why.append("SCHEMA: the schema's unit %r is not a canonical unit of "
                   "dimension %r" % (pin.get("unit"), pin.get("dimension")))
    else:
        want = float(pin["value_token"]) * scale
        try:
            rv = float(reg_entry.get("value"))
        except (TypeError, ValueError):
            rv = None
        if rv is None or abs(rv - want) > 1e-9 * max(1.0, abs(want)):
            why.append("SCHEMA: the registry value %r is not the schema's "
                       "pinned quantity %s %s = %r %s"
                       % (reg_entry.get("value"), pin["value_token"],
                          pin["unit"], want, dim))
    kdim = KEY_SUFFIX_DIMENSION.get(key.rsplit("_", 1)[-1], "1")
    if pin.get("dimension") != kdim:
        why.append("SCHEMA: the schema's dimension %r is not the key's %r"
                   % (pin.get("dimension"), kdim))
    # -- document identity: path + sha256, on disk and in the evidence -----
    sd = sem_docs.get(pin.get("document")) or {}
    ed = docs.get(e.get("document")) or {}
    if not sd:
        why.append("SCHEMA: the schema names document %r, which it does not "
                   "pin" % pin.get("document"))
        return why
    if ed.get("path") != sd.get("path") or ed.get("sha256") != sd.get(
            "sha256"):
        why.append("SCHEMA: the evidence reads document %r (%s, %s), not the "
                   "schema's pinned document %r (%s, %s)"
                   % (e.get("document"), ed.get("path"),
                      str(ed.get("sha256"))[:12], pin.get("document"),
                      sd.get("path"), str(sd.get("sha256"))[:12]))
    # -- the locator and the row's own text fingerprint ---------------------
    if e.get("line") != pin.get("line"):
        why.append("SCHEMA: the evidence locates line %r, the schema anchors "
                   "line %r" % (e.get("line"), pin.get("line")))
    if not der or der.get("row_text") is None:
        return why
    fp = _sha_bytes(der["row_text"].encode("utf-8"))
    if fp != pin.get("row_sha256"):
        why.append("SCHEMA: the located row's text fingerprint %s is not the "
                   "schema's %s (the row reads %r)"
                   % (fp[:16], str(pin.get("row_sha256"))[:16],
                      der["row_text"]))
    if der.get("problems"):
        return why
    # -- symbol ------------------------------------------------------------
    if not any(_sym_eq(pin.get("symbol"), s) for s in der.get("symbols")
               or []):
        why.append("SCHEMA: the document row's symbol is %s, not the "
                   "schema's %r" % (der.get("symbols") or "absent",
                                    pin.get("symbol")))
    # -- table identity: header line, header text, title, table condition --
    tb = pin.get("table") or {}
    if der.get("kind") == "LIST":
        if der.get("header") != [tb.get("header_text")]:
            why.append("SCHEMA: the document's list heading is %r, not the "
                       "schema's %r" % (der.get("header"),
                                        tb.get("header_text")))
    else:
        h = der.get("header_line")
        htxt = _norm(lines[h]) if h is not None else None
        if h != tb.get("header_line") or htxt != tb.get("header_text"):
            why.append("SCHEMA: the document's table header is line %r %r, "
                       "not the schema's line %r %r"
                       % (h, htxt, tb.get("header_line"),
                          tb.get("header_text")))
        if tb.get("title") and _squash(tb["title"]) not in _squash(
                der.get("preamble")):
            why.append("SCHEMA: the schema's table title %r is not above the "
                       "row's header (preamble %r)"
                       % (tb["title"], der.get("preamble")))
        if tb.get("condition") and _squash(tb["condition"]) not in _squash(
                der.get("preamble")):
            why.append("SCHEMA: the schema's table condition %r is not in the "
                       "document's preamble %r"
                       % (tb["condition"], der.get("preamble")))
    # -- published columns, direction, value token, unit -------------------
    if der.get("published_columns") != pin.get("published_columns"):
        why.append("SCHEMA: the document row publishes columns %r, the "
                   "schema's published columns are %r"
                   % (der.get("published_columns"),
                      pin.get("published_columns")))
    if der.get("bound") != pin.get("direction"):
        why.append("SCHEMA: the document publishes this value as a %s, the "
                   "schema's direction is %s"
                   % (der.get("bound"), pin.get("direction")))
    if str(der.get("value_token")) != str(pin.get("value_token")):
        why.append("SCHEMA: the document's value token %r is not the "
                   "schema's %r" % (der.get("value_token"),
                                    pin.get("value_token")))
    if der.get("unit") != pin.get("unit"):
        why.append("SCHEMA: the document row's unit %r is not the schema's "
                   "unit %r" % (der.get("unit"), pin.get("unit")))
    # -- the distinguishing operating condition ----------------------------
    cond, scope = pin.get("condition"), pin.get("condition_scope")
    if cond:
        where = {"VALUE_LINE": der.get("row_text"),
                 "ROW_CONTEXT": der.get("context")}.get(scope)
        if where is None:
            why.append("SCHEMA: condition scope %r is not VALUE_LINE or "
                       "ROW_CONTEXT" % (scope,))
        elif _squash(cond) not in _squash(where):
            why.append("SCHEMA: the schema's condition %r is not on the "
                       "row's own %s %r: another operating condition's row"
                       % (cond, scope, where))
    # -- the parameter's NAME, in the row's own block ----------------------
    if der.get("kind") != "LIST":
        blk = _block_text(lines, der)
        for p in pin.get("parameter") or []:
            if _squash(p) not in _squash(blk):
                why.append("SCHEMA: the schema's parameter %r is not in the "
                           "row's own block %r: another parameter's row"
                           % (p, blk))
    # -- the evidence's claims must also AGREE with the schema -------------
    for f, pv in (("symbol", pin.get("symbol")),
                  ("bound", pin.get("direction")),
                  ("unit", pin.get("unit")),
                  ("value_token", pin.get("value_token")),
                  ("published_columns", pin.get("published_columns")),
                  ("condition", pin.get("condition"))):
        ev = e.get(f)
        if f == "condition" and pv is None:
            continue
        same = (_norm(str(ev)) == _norm(str(pv))) if f in (
            "symbol", "condition") else ev == pv
        if not same:
            why.append("SCHEMA: the evidence claims %s=%r, the schema pins %r"
                       % (f, ev, pv))
    return why


def audit(registry, pinned_sha256, evidence_path=None, evidence=None,
          evidence_text=None, semantics_text=None, document_only=False):
    """Returns (ok, report).

    evidence_text: the evidence file's CONTENT (checked against the pin),
    for in-memory controls that model an edited-and-re-pinned file.
    semantics_text: the schema file's content, for the control that edits
    the schema without re-pinning it.
    document_only: the D-796 audit with the D-797 schema switched OFF --
    used ONLY by the destructive controls, to prove a coordinated attack is
    accepted without the schema (so its control is not vacuous)."""
    path = EVIDENCE if evidence_path is None else Path(evidence_path)
    problems = []
    sem, sem_problems = (None, []) if document_only else load_semantics(
        semantics_text)
    problems += sem_problems
    if not document_only and sem is None:
        sem = dict(documents={}, keys={})
    if evidence is None:
        if evidence_text is None:
            if not path.exists():
                return False, dict(problems=["the guarantee evidence file %s "
                                             "is absent" % path])
            raw = path.read_bytes()
        else:
            raw = evidence_text.encode("utf-8")
        actual = _sha_bytes(raw)
        if actual != pinned_sha256:
            problems.append("the guarantee evidence file's sha256 %s is not "
                            "the pinned %s: it was edited without re-pinning"
                            % (actual, pinned_sha256))
        evidence = json.loads(raw.decode("utf-8"))
    if evidence.get("schema") != SCHEMA:
        problems.append("the evidence schema is %r, not %r"
                        % (evidence.get("schema"), SCHEMA))
    docs = evidence.get("documents") or {}
    for dk, d in docs.items():
        f = ROOT / d["path"]
        if not f.exists():
            problems.append("document %s (%s) is absent" % (dk, d["path"]))
        elif _sha(f) != d["sha256"]:
            problems.append("document %s's sha256 does not match its pin"
                            % dk)
    rows = evidence.get("rows") or {}
    reg = {}
    for r in registry:
        reg.setdefault(r["key"], r)
    guaranteed = sorted(k for k, r in reg.items()
                        if str(r.get("tag", "")).startswith("GUARANTEED"))
    if sem is not None:
        # D-797 / D797-05: the key sets are EQUAL, in both directions
        for key in guaranteed:
            if key not in sem["keys"]:
                problems.append(
                    "SCHEMA: %s is tagged %s in the registry but has no "
                    "pinned semantics in the schema" % (key, reg[key]["tag"]))
        for key in sorted(sem["keys"]):
            if key not in guaranteed:
                problems.append(
                    "SCHEMA: %s is pinned in the schema as %s but the "
                    "registry does not tag it GUARANTEED (%s)"
                    % (key, sem["keys"][key].get("tag"),
                       (reg.get(key) or {}).get("tag", "absent")))
        for dk, sd in sorted(sem["documents"].items()):
            f = ROOT / sd.get("path", "")
            if not f.is_file():
                problems.append("SCHEMA: pinned document %s (%s) is absent"
                                % (dk, sd.get("path")))
            elif _sha(f) != sd.get("sha256"):
                problems.append("SCHEMA: pinned document %s's bytes are not "
                                "the schema's sha256" % dk)
    checked = []
    for key in guaranteed:
        r = reg[key]
        e = rows.get(key)
        if e is None:
            problems.append("%s is tagged %s with NO primary-row evidence"
                            % (key, r["tag"]))
            checked.append(dict(key=key, ok=False, problems=[
                "no primary-row evidence"]))
            continue
        why, der = _check_row(key, r, e, docs)
        if TYP_WORDS.search(str(r.get("condition") or "")):
            why.append("its registry condition says TYP/typical/no min-max")
        pin = (sem or {}).get("keys", {}).get(key)
        if pin is not None:
            d_ = docs.get(e.get("document")) or {}
            f_ = ROOT / d_.get("path", "")
            why += _check_semantics(key, r, e, docs, der or {},
                                    document_lines(f_) if f_.is_file()
                                    else [], pin, sem["documents"])
        for w in why:
            problems.append("%s: %s" % (key, w))
        der = der or {}
        checked.append(dict(
            key=key, tag=r["tag"], value=r["value"],
            document=e.get("document"), line=e.get("line"),
            derived=dict((k, der.get(k)) for k in (
                "kind", "header_line", "header", "symbols", "symbol_rule",
                "value_token", "value_column", "published_columns", "bound",
                "unit", "context", "preamble")),
            pinned=None if pin is None else dict(
                (k, pin.get(k)) for k in (
                    "document", "line", "symbol", "condition",
                    "value_token", "unit", "direction")),
            ok=not why, problems=why))
    for key in rows:
        if key not in guaranteed:
            problems.append("evidence row %s belongs to no GUARANTEED_* "
                            "registry entry (stale or a re-tag in waiting)"
                            % key)
    return (not problems), dict(
        evidence=str(path.relative_to(ROOT)) if path.is_absolute() else
        str(path), pinned_sha256=pinned_sha256, rows=checked,
        guaranteed_entries=guaranteed, documents=sorted(docs),
        semantics=None if document_only else dict(
            path=str(SEMANTICS.relative_to(ROOT)),
            pinned_sha256=SEMANTICS_SHA256,
            keys=sorted((sem or {}).get("keys", {})),
            documents=sorted((sem or {}).get("documents", {}))),
        problems=problems)


# ---------------------------------------------------- destructive controls --
def _relabel(registry, key, **fields):
    out, hit = [], False
    for r in registry:
        r = dict(r)
        if r["key"] == key:
            r.update(fields)
            hit = True
        out.append(r)
    if not hit:
        out.append(dict(dict(key=key, value=None, tag="TYPICAL", source="",
                             condition=None), **fields))
    return out


def _find_line(doc_path, first_cell, contains=""):
    lines = document_lines(ROOT / doc_path)
    for i, l in enumerate(lines):
        c = _cells(l)
        if c and c[0]["t"] == first_cell and _squash(contains) in _squash(l):
            return i
    raise LookupError("%s: no line starting %r containing %r"
                      % (doc_path, first_cell, contains))


def destructive_controls(registry, evidence_text=None):
    """Each Round-15 attack, and the other ways a transcription can lie,
    applied to an IN-MEMORY copy of the registry and the evidence file (the
    files on disk are never touched), with the evidence RE-PINNED to its own
    new sha256 -- so the only thing that can refuse it is the document.

    Returns {control: caught}.  A control is caught only if the audit fails
    AND one of its problems is the one the control exists to provoke -- a
    control refused for some unrelated reason is not a caught control."""
    if evidence_text is None:
        evidence_text = EVIDENCE.read_text(encoding="utf-8")
    base = json.loads(evidence_text)
    ti = base["documents"]["SLUSF65B"]["path"]

    def run(rows_over=None, reg=None, doc_over=None, drop=(),
            document_only=False, semantics_text=None):
        ev = copy.deepcopy(base)
        for k in drop:
            ev["rows"].pop(k, None)
        for k, v in (rows_over or {}).items():
            ev["rows"][k] = dict(ev["rows"].get(k) or {}, **v)
        for k, v in (doc_over or {}).items():
            ev["documents"][k] = dict(ev["documents"][k], **v)
        text = json.dumps(ev, indent=1, ensure_ascii=False, sort_keys=True)
        return audit(registry if reg is None else reg,
                     _sha_bytes(text.encode("utf-8")), evidence_text=text,
                     document_only=document_only,
                     semantics_text=semantics_text)

    def coordinated(*needles, **attack):
        """D-797: a coordinated registry + evidence + re-pinned hash edit.
        Caught only if the document-only (D-796) audit ACCEPTS it -- else the
        control would not be proving the schema -- AND the full audit refuses
        it for the named SCHEMA reason."""
        return run(document_only=True, **attack)[0] and caught(
            run(**attack), *needles)

    def caught(result, *needles):
        ok, rep = result
        blob = " | ".join(rep["problems"])
        return (not ok) and all(n in blob for n in needles)

    def row_at(first, contains=""):
        i = _find_line(ti, first, contains)
        return dict(line=i, row_text=_norm(document_lines(ROOT / ti)[i]))

    c = {}
    # 0. the unmutated copy, re-serialised and re-pinned, must PASS -- or
    #    every control below is vacuous
    ok0, rep0 = run()
    c["an_unmutated_repinned_copy_passes"] = ok0

    # (a) Astra: VLOWV's MAX 3.1 V re-pointed at VIN_LOWVZ's genuine
    #     "2.95 3.1 V" row (3.1 V, MAX column, same hashed PDF), re-pinned
    c["a_unrelated_row_repin_is_refused"] = caught(
        run({"bq.vlowv_max_V": row_at("VIN_LOWVZ")}),
        "bq.vlowv_max_V", "not the declared 'VLOWV'")
    # (a') ...and with the symbol claim changed to match that row: the model's
    #     own source text still cites VLOWV
    c["a_unrelated_row_repin_with_its_symbol_is_refused"] = caught(
        run({"bq.vlowv_max_V": dict(row_at("VIN_LOWVZ"),
                                    symbol="VIN_LOWVZ",
                                    condition="VIN falling")}),
        "bq.vlowv_max_V", "never names the symbol 'VIN_LOWVZ'")

    vdppm = row_at("VDPPM")
    typ_row = dict(document="SLUSF65B", symbol="VDPPM", unit="V", scale=1.0,
                   value_token="0.1", bound="MAX",
                   condition="VBAT = 3.6V, VSYS = VDPPM + VBAT",
                   row_token="VDPPM", **vdppm)
    reg_vdppm = _relabel(registry, "bq.vdppm_V", tag="GUARANTEED_MAX",
                         role="DEVICE_BOUND", condition="VBAT = 3.6 V")
    # (b) Fable: a fabricated MIN/TYP/MAX header claim on a TYP-only row --
    #     refused by the document AND (D-797) by the schema, which pins no
    #     meaning for bq.vdppm_V at all
    c["b_fabricated_header_is_refused"] = caught(
        run({"bq.vdppm_V": dict(typ_row,
                                published_columns=["MIN", "TYP", "MAX"])},
            reg=reg_vdppm),
        "bq.vdppm_V", "not the document's ['TYP']",
        "SCHEMA: bq.vdppm_V is tagged GUARANTEED_MAX in the registry but has "
        "no pinned semantics")
    # (c) Fable's three edits: retag TYP as GUARANTEED_MAX, add an honest-
    #     looking evidence row, re-pin -- the document has no MAX for VDPPM
    c["c_three_edit_typ_to_max_is_refused"] = caught(
        run({"bq.vdppm_V": dict(typ_row, published_columns=["TYP"])},
            reg=reg_vdppm),
        "bq.vdppm_V", "sits in the document's TYP column")
    # (d) a published MAXIMUM reversed into GUARANTEED_MIN
    c["d_direction_flip_max_to_min_is_refused"] = caught(
        run({"bq.ilim_max_A": dict(bound="MIN")},
            reg=_relabel(registry, "bq.ilim_max_A", tag="GUARANTEED_MIN")),
        "bq.ilim_max_A", "publishes this value as a MAX")
    c["d_direction_flip_of_the_tag_alone_is_refused"] = caught(
        run(reg=_relabel(registry, "bq.ron_in_max_ohm",
                         tag="GUARANTEED_MIN")),
        "bq.ron_in_max_ohm", "needs a MIN")
    # (e) a TYP-only single-value row (VSYS_REG 4.5 V) promoted by inventing
    #     a MAX header for it
    c["e_typ_only_single_value_with_invented_max_is_refused"] = caught(
        run({"bq.vsys_reg_V": dict(
            document="SLUSF65B", symbol="VSYS_REG", unit="V", scale=1.0,
            value_token="4.5", bound="MAX", published_columns=["MAX"],
            condition="VIN = 5V, VBATREG ≤ 4.3V", row_token="VSYS_REG",
            **row_at("VSYS_REG"))},
            reg=_relabel(registry, "bq.vsys_reg_V", tag="GUARANTEED_MAX",
                         role="DEVICE_BOUND", condition="VBATREG <= 4.3 V")),
        "bq.vsys_reg_V", "sits in the document's TYP column")
    # (f) a row whose symbol is not the key's declared symbol: RON_IN's real
    #     row claimed as RON_BAT, with the model source edited to cite it
    reg_f = [dict(r, source=(r.get("source") or "") + " RON_BAT")
             if r["key"] == "bq.ron_in_max_ohm" else r for r in registry]
    c["f_symbol_mismatch_is_refused"] = caught(
        run({"bq.ron_in_max_ohm": dict(symbol="RON_BAT")}, reg=reg_f),
        "bq.ron_in_max_ohm", "not the declared 'RON_BAT'")
    # (g) the wrong condition's sub-row: VBUVLO_HYS is published twice; the
    #     VIN = 0 V row's MAX (210 mV) bound under the VIN = 5 V condition
    if "bq.vbuvlo_hys_max_V" in base["rows"]:
        c["g_sibling_row_at_another_condition_is_refused"] = caught(
            run({"bq.vbuvlo_hys_max_V": dict(
                row_at("VBUVLO_HYS", "VIN = 0V"), value_token="210")},
                reg=_relabel(registry, "bq.vbuvlo_hys_max_V", value=0.210)),
            "bq.vbuvlo_hys_max_V", "not this row's own condition")
    # (h) a scale that is not the unit's: mA declared as A
    c["h_declared_scale_is_not_free_is_refused"] = caught(
        run({"bq.ilim_max_A": dict(scale=1.0)}),
        "bq.ilim_max_A", "not the canonical")
    # (i) a unit claim that is not the row's
    c["i_unit_claim_is_refused"] = caught(
        run({"bq.ron_bat_max_ohm": dict(unit="Ω")}),
        "bq.ron_bat_max_ohm", "not the row's unit")
    # (j) a locator that drifted: the right text, the wrong line
    c["j_locator_drift_is_refused"] = caught(
        run({"bq.kiset_max_AOhm": dict(
            line=base["rows"]["bq.kiset_max_AOhm"]["line"] + 1)}),
        "bq.kiset_max_AOhm", "row_text is not document line")
    # (k) a document whose bytes are not the pinned bytes
    c["k_document_hash_is_refused"] = caught(
        run(doc_over={"SLUSF65B": dict(sha256="0" * 64)}),
        "SLUSF65B's sha256 does not match")
    # (l) an evidence file edited without re-pinning
    ok_l, rep_l = audit(registry, "0" * 64, evidence_text=evidence_text)
    c["l_unpinned_evidence_edit_is_refused"] = (
        not ok_l and "without re-pinning" in " | ".join(rep_l["problems"]))
    # (m) a guarantee with no evidence row at all
    c["m_guarantee_without_evidence_is_refused"] = caught(
        run(drop=("bq.kiset_min_AOhm",)),
        "bq.kiset_min_AOhm is tagged GUARANTEED_MIN with NO primary-row")
    # (n) a MAX-word requirement read as a MIN (Molex 6.1.1)
    c["n_requirement_word_direction_flip_is_refused"] = caught(
        run({"path.microlock_contact_initial_max_ohm": dict(bound="MIN")},
            reg=_relabel(registry, "path.microlock_contact_initial_max_ohm",
                         tag="GUARANTEED_MIN")),
        "path.microlock_contact_initial_max_ohm", "publishes this value as "
        "a MAX")

    # ------------------------------------------------------------------
    # D-797 / D797-05 (Astra R16-03, Fable R16-02).  COORDINATED edits: the
    # attacker ALSO rewrites the registry's source/condition prose and the
    # evidence claims to describe the new row truthfully, and re-pins the
    # evidence hash.  `coordinated` requires the D-796 document-only audit
    # to ACCEPT each one, and the schema to refuse it for its named reason.
    # ------------------------------------------------------------------
    def reg_edit(key, **fields):
        return _relabel(registry, key, **fields)

    # (r16-a) VLOWV (precharge->fast-charge, VBAT rising, 3.1 V MAX)
    #     re-pointed at VIN_LOWVZ (stop-charging, VIN falling, 3.1 V MAX)
    c["r16_a_coordinated_vlowv_repointed_to_vin_lowvz_is_refused"] = \
        coordinated(
            "bq.vlowv_max_V: SCHEMA: the document row's symbol is "
            "['VIN_LOWVZ'], not the schema's 'VLOWV'",
            rows_over={"bq.vlowv_max_V": dict(
                row_at("VIN_LOWVZ"), symbol="VIN_LOWVZ", row_token="VIN_LOWVZ",
                condition="VIN falling", published_columns=["TYP", "MAX"])},
            reg=reg_edit("bq.vlowv_max_V",
                         source="TI SLUSF65B EC: VIN_LOWVZ, VIN threshold to "
                                "stop charging, 2.95 / 3.1 V MAX, VIN falling.",
                         condition="VIN falling, -40..125 C"))
    # (r16-b) VBUVLO_HYS moved from the VIN = 5 V sub-row to the VIN = 0 V
    #     sibling (210 mV MAX), with the registry value and prose following
    c["r16_b_coordinated_vbuvlo_hys_moved_to_vin_0v_sibling_is_refused"] = \
        coordinated(
            "bq.vbuvlo_hys_max_V: SCHEMA: the schema's condition "
            "'VBAT rising, VIN = 5V' is not on the row's own VALUE_LINE",
            rows_over={"bq.vbuvlo_hys_max_V": dict(
                row_at("VBUVLO_HYS", "VIN = 0V"), value_token="210",
                condition="VBAT rising, VIN = 0V")},
            reg=reg_edit("bq.vbuvlo_hys_max_V", value=0.210,
                         source="TI SLUSF65B EC: VBUVLO_HYS, Battery UVLO "
                                "hysteresis, VBAT rising, VIN = 0V: 90 / 150 "
                                "/ 210 mV -- the MAX column.",
                         condition="VBAT rising, VIN = 0 V"))
    # (r16-c) a fabricated MAX header on a PINNED key: RON_BAT publishes
    #     TYP/MAX; the evidence claims a MIN/TYP/MAX header
    c["r16_c_fabricated_max_header_on_a_pinned_key_is_refused"] = caught(
        run({"bq.ron_bat_max_ohm": dict(
            published_columns=["MIN", "TYP", "MAX"])}),
        "bq.ron_bat_max_ohm: SCHEMA: the evidence claims published_columns="
        "['MIN', 'TYP', 'MAX'], the schema pins ['TYP', 'MAX']")
    # (r16-d) MIN/MAX reversed on the GENUINE row: ILIM's MAX key re-valued
    #     to the same row's genuine MIN (995 mA) and retagged GUARANTEED_MIN
    c["r16_d_coordinated_min_max_reversal_is_refused"] = coordinated(
        "bq.ilim_max_A: SCHEMA: the document publishes this value as a MIN, "
        "the schema's direction is MAX",
        rows_over={"bq.ilim_max_A": dict(value_token="995", bound="MIN")},
        reg=reg_edit("bq.ilim_max_A", value=0.995, tag="GUARANTEED_MIN"))
    # (r16-e) unit / scaling substitution: the mV row's 190 registered as
    #     190 V, with unit and scale claimed to match
    c["r16_e_unit_scaling_substitution_is_refused"] = caught(
        run({"bq.vbuvlo_hys_max_V": dict(unit="V", scale=1.0)},
            reg=reg_edit("bq.vbuvlo_hys_max_V", value=190.0)),
        "bq.vbuvlo_hys_max_V: SCHEMA: the registry value 190.0 is not the "
        "schema's pinned quantity 190 mV")
    # (r16-f) GENERIC coordinated repoint: IPRECHG_ACC (precharge, +/-10 %)
    #     moved to ICHG_ACC (fast charge, +/-10 %) -- same PDF, same table,
    #     same number, same column, another parameter
    c["r16_f_coordinated_evidence_registry_hash_repoint_is_refused"] = \
        coordinated(
            "bq.iprechg_accuracy: SCHEMA: the document row's symbol is "
            "['ICHG_ACC'], not the schema's 'IPRECHG_ACC'",
            rows_over={"bq.iprechg_accuracy": dict(
                row_at("ICHG_ACC"), symbol="ICHG_ACC", row_token="ICHG_ACC",
                condition="VIN = 5V, fast charge current ≥ 40mA")},
            reg=reg_edit("bq.iprechg_accuracy",
                         source="TI SLUSF65B EC: ICHG_ACC, charge current "
                                "accuracy, -10 / +10 %.",
                         condition="VIN = 5 V, fast charge current >= 40 mA"))
    # (r16-g) a NEW guarantee the schema never licensed, on a genuine MAX
    #     row with truthful registry prose and evidence
    c["r16_g_registry_guarantee_absent_from_schema_is_refused"] = \
        coordinated(
            "SCHEMA: bq.ichg_accuracy is tagged GUARANTEED_MAX in the "
            "registry but has no pinned semantics in the schema",
            rows_over={"bq.ichg_accuracy": dict(
                base["rows"]["bq.iprechg_accuracy"], **dict(
                    row_at("ICHG_ACC"), symbol="ICHG_ACC",
                    row_token="ICHG_ACC",
                    condition="VIN = 5V, fast charge current ≥ 40mA"))},
            reg=reg_edit("bq.ichg_accuracy", value=0.10,
                         tag="GUARANTEED_MAX", role="DEVICE_BOUND",
                         source="TI SLUSF65B EC: ICHG_ACC -10 / +10 %.",
                         condition="VIN = 5 V"))
    # (r16-h) a schema key the registry silently demoted (evidence dropped
    #     with it): the guarantee disappears, and the schema notices
    c["r16_h_schema_key_missing_from_registry_is_refused"] = coordinated(
        "SCHEMA: bq.kiset_min_AOhm is pinned in the schema as GUARANTEED_MIN "
        "but the registry does not tag it GUARANTEED",
        drop=("bq.kiset_min_AOhm",),
        reg=reg_edit("bq.kiset_min_AOhm", tag="TYPICAL"))
    # (r16-i) document identity: the evidence re-points SLUSF65B at another
    #     archived file, with that file's genuine sha256
    alt = str(Path(ti).with_suffix(".txt"))
    if (ROOT / alt).is_file():
        c["r16_i_document_identity_substitution_is_refused"] = caught(
            run(doc_over={"SLUSF65B": dict(
                path=alt, sha256=_sha(ROOT / alt))}),
            "SCHEMA: the evidence reads document 'SLUSF65B' (%s" % alt)
    # (r16-j) the schema itself edited without re-pinning it in the verifier
    sem_text = SEMANTICS.read_text(encoding="utf-8")
    c["r16_j_schema_edit_without_repin_is_refused"] = caught(
        run(semantics_text=sem_text.replace('"symbol": "VLOWV"',
                                            '"symbol": "VIN_LOWVZ"', 1)),
        "the schema was edited without re-pinning it in the verifier")
    # (r16-k) the schema is DATA: a statement that is not a literal
    #     assignment is refused, never executed
    c["r16_k_schema_with_code_is_refused"] = caught(
        run(semantics_text=sem_text + "\nKEYS.clear()\n"),
        "not a literal-only module")
    return c


def verdict(registry, pinned_sha256):
    ok, rep = audit(registry, pinned_sha256)
    controls = destructive_controls(registry)
    rep["destructive_controls"] = controls
    rep["every_destructive_control_caught"] = bool(controls) and all(
        controls.values())
    return bool(ok and rep["every_destructive_control_caught"]), rep


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    import aqroot_power_model as apm                          # noqa: E402
    ok, rep = verdict(apm.registry(), apm.GUARANTEE_EVIDENCE_SHA256)
    for r in rep["rows"]:
        print("%-4s %-40s %-15s %s" % ("PASS" if r["ok"] else "FAIL",
                                       r["key"], r.get("tag"),
                                       "; ".join(r["problems"])))
    for k, v in rep["destructive_controls"].items():
        print("%-7s %s" % ("OK" if v else "MISSED", k))
    for p in rep["problems"]:
        print("PROBLEM", p)
    dc = rep["destructive_controls"]
    print("SEMANTICS %s sha256 %s: %d keys pinned"
          % (rep["semantics"]["path"], rep["semantics"]["pinned_sha256"][:16],
             len(rep["semantics"]["keys"])))
    print("KEYS authenticated %d/%d; CONTROLS caught %d/%d"
          % (sum(1 for r in rep["rows"] if r["ok"]), len(rep["rows"]),
             sum(1 for v in dc.values() if v), len(dc)))
    print("VERDICT", "PASS" if ok else "FAIL")
    sys.exit(0 if ok else 1)
