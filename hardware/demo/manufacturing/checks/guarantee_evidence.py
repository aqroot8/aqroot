#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AQROOT Demo -- D-795 / R14-06.  A GUARANTEE IS BOUND TO A PRIMARY ROW.

ROUND-14, IN ITS OWN WORDS: "a TYP-only row cannot become GUARANTEED by
changing the tag plus adding a row to a mutable allow-list.  GUARANTEED_*
must be bound to immutable/hashed primary-source evidence whose row/condition
actually has min/max guarantee semantics.  Reject evidence text/conditions
containing TYP/typical/no min/max when asked to support a guarantee.  Put
GUARANTEED_ROWS/source facts in separately hashed evidence or derive from
archived primary docs; do not let two source edits manufacture certainty."

D-794's `GUARANTEED_ROWS` was a dict in the model: relabel a typical as
GUARANTEED_MAX, add one line to the dict naming a real document and a real
row token, and the audit passed -- two edits in one file.

WHAT REPLACES IT.  `evidence/guaranteed-rows.json` names, for every
GUARANTEED_* key, an ARCHIVED document by path and sha256, and the VERBATIM
row the value is read from, with its column semantics.  At release time this
module:

  1  checks the evidence file against the sha256 PINNED in
     `aqroot_power_model.GUARANTEE_EVIDENCE_SHA256`;
  2  checks every document against its own pinned sha256;
  3  EXTRACTS the document's text (pdftotext -layout) and requires the row --
     every one of its lines, whitespace-normalised, in order -- to be in it;
  4  requires the row's COLUMNS to appear in it, the value to sit in a MIN or
     MAX column (or behind a MAX/MIN word, a <= / >= sign, or a +/- tolerance
     code), and refuses a row whose header has a TYP column and nothing else;
  5  refuses TYP/typical/"no min"/"TYP only" in the condition of anything asked
     to carry a guarantee; and
  6  requires every GUARANTEED_* registry entry to have evidence, and every
     evidence entry to belong to a GUARANTEED_* entry of the same value.

So manufacturing certainty for a typical now takes a vendor PDF that
publishes a MIN or MAX column for it -- which is the point.
"""

import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
EVIDENCE = ROOT / "hardware/demo/manufacturing/evidence/guaranteed-rows.json"
GUARANTEED_SEMANTICS = ("MIN", "MAX", "MAX_WORD", "MIN_WORD", "LE_SIGN",
                        "GE_SIGN", "TOLERANCE_CODE")
TYP_WORDS = re.compile(r"\btyp(ical)?\b|typ only|no min|no max|\bTYP\b",
                       re.I)


def _norm(t):
    # One spelling per glyph: en dash and minus sign as '-', the ohm sign
    # (U+2126) as capital omega (U+03A9) -- PDF extraction emits either.
    t = (t or "").replace("\u2013", "-").replace("\u2212", "-")
    t = t.replace("\u2126", "\u03a9")
    return re.sub(r"\s+", " ", t).strip()


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


_TEXT_CACHE = {}


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


def _row_in_text(lines, text):
    """Every line of the row, normalised, appears in the document, in order,
    within a few lines of the previous one."""
    doc = [_norm(x) for x in text.splitlines()]
    want = [_norm(x) for x in lines]
    for i, d in enumerate(doc):
        if want[0] not in d:
            continue
        j, ok = i, True
        for w in want[1:]:
            hit = next((k for k in range(j + 1, min(j + 5, len(doc)))
                        if w in doc[k]), None)
            if hit is None:
                ok = False
                break
            j = hit
        if ok:
            return True
    return False


def _semantics_ok(entry):
    why = []
    sem = entry.get("semantics")
    row = _norm(" ".join(entry.get("row_lines") or []))
    val = str(entry.get("value_token"))
    if sem not in GUARANTEED_SEMANTICS:
        why.append("semantics %r cannot carry a guarantee" % (sem,))
        return why
    if val not in row:
        why.append("the value token %r is not in the row" % val)
    if sem in ("MIN", "MAX"):
        hdr = entry.get("columns_header") or []
        cols = entry.get("columns") or []
        if len(hdr) != len(cols) or len(cols) < 1:
            why.append("the row's columns do not match its header")
        elif not ({"MIN", "MAX"} & set(hdr)):
            why.append("the row's header has no MIN or MAX column: a TYP-only "
                       "row cannot carry a guarantee")
        elif sem not in hdr or cols[hdr.index(sem)] != val:
            why.append("the value is not in the row's %s column" % sem)
        elif " ".join(cols) not in row:
            why.append("the columns %r do not appear consecutively in the "
                       "row" % (cols,))
    elif sem == "MAX_WORD" and "MAX" not in row:
        why.append("no MAX word in the row")
    elif sem == "MIN_WORD" and "MIN" not in row:
        why.append("no MIN word in the row")
    elif sem == "LE_SIGN" and not re.search("≤\\s*" + re.escape(val), row):
        why.append("no <= sign before the value")
    elif sem == "GE_SIGN" and not re.search("≥\\s*" + re.escape(val), row):
        why.append("no >= sign before the value")
    elif sem == "TOLERANCE_CODE" and "±" not in row:
        why.append("no +/- tolerance in the row")
    return why


def audit(registry, pinned_sha256, evidence_path=None, evidence=None):
    """Returns (ok, report)."""
    path = EVIDENCE if evidence_path is None else Path(evidence_path)
    problems = []
    if evidence is None:
        if not path.exists():
            return False, dict(problems=["the guarantee evidence file %s is "
                                         "absent" % path])
        actual = _sha(path)
        if actual != pinned_sha256:
            problems.append("the guarantee evidence file's sha256 %s is not "
                            "the pinned %s: it was edited without re-pinning"
                            % (actual, pinned_sha256))
        evidence = json.loads(path.read_text(encoding="utf-8"))
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
    checked = []
    for key in guaranteed:
        r = reg[key]
        e = rows.get(key)
        if e is None:
            problems.append("%s is tagged %s with NO primary-row evidence"
                            % (key, r["tag"]))
            continue
        why = []
        d = docs.get(e.get("document"))
        if d is None:
            why.append("names an unknown document %r" % (e.get("document"),))
        else:
            f = ROOT / d["path"]
            if f.exists() and not _row_in_text(e.get("row_lines") or [""],
                                               document_text(f)):
                why.append("its row is NOT in the archived document text")
        why += _semantics_ok(e)
        cond = " ".join(str(x) for x in (r.get("condition"),
                                         e.get("condition")) if x)
        if TYP_WORDS.search(cond):
            why.append("its condition says TYP/typical/no min-max")
        if TYP_WORDS.search(_norm(" ".join(e.get("row_lines") or []))) \
                and e.get("semantics") not in ("MIN", "MAX"):
            why.append("its row text is a typical")
        try:
            scale = float(e.get("scale", 1.0))
            if abs(float(e["value_token"].replace("−", "-")) * scale
                   - float(r["value"])) > 1e-9 * max(1.0, abs(r["value"])):
                why.append("the evidence value %s x %s is not the registered "
                           "value %r" % (e["value_token"], scale, r["value"]))
        except (ValueError, KeyError, TypeError):
            why.append("the evidence value is not a number")
        for w in why:
            problems.append("%s: %s" % (key, w))
        checked.append(dict(key=key, document=e.get("document"),
                            semantics=e.get("semantics"), ok=not why,
                            problems=why))
    for key in rows:
        if key not in guaranteed:
            problems.append("evidence row %s belongs to no GUARANTEED_* "
                            "registry entry (stale or a re-tag in waiting)"
                            % key)
    return (not problems), dict(
        evidence=str(path.relative_to(ROOT)) if path.is_absolute() else
        str(path), pinned_sha256=pinned_sha256, rows=checked,
        guaranteed_entries=guaranteed, documents=sorted(docs),
        problems=problems)
