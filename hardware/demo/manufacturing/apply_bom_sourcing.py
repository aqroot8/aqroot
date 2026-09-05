#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AQROOT Demo -- write the RULED sourcing identity into the schematic.

`screen_bom_sourcing.py` decides; this writes.  It consumes that screen's
`--plan` and adds `Manufacturer` / `MPN` / `LCSC` properties -- the three the
fabrication package's BOM exporter reads -- plus a one-line `Note_Sourcing`
recording WHERE the identity came from, to the named symbols and to nothing
else.

WHY A TEXT EDIT AND NOT KICAD.  Same reason `apply_schematic_population.py`
gives for the board: these ten sheets are compared by content, and opening and
re-saving them through KiCad would rewrite every one of them.  This inserts
property blocks after each symbol's own `Datasheet` property, copying that
property's placement so the new fields land where KiCad would have put them,
and touches no other byte.  The sheets are CRLF and stay CRLF: they are read
and written as BYTES.

WHAT IT REFUSES.  A symbol that already carries one of these properties with a
DIFFERENT value -- because overwriting a part number that someone chose
deliberately is how `C26` came to carry `C24`'s LCSC code.  A reference the plan
names that no sheet holds.  A plan line missing any of the three fields.  Every
refusal is fatal and nothing is written.

CORRECTING an identity that is already there is a different act from adding
one, so it is spelled differently.  A plan line may carry

    "replaces": {"MPN": "<the exact string that must be there now>", ...}

and only then is the property rewritten -- and only if the file really does
hold that exact string.  Anything else is a fatal conflict.  The point is that
a correction must NAME what it is overwriting, so a plan cannot silently
clobber a decision it never read.

A plan may also carry a top-level

    "text_replaces": [{"file": "<path relative to the repo root>",
                       "old": "...", "new": "...", "why": "..."}]

for the two things that are NOT instance properties and still carry a part
identity: the CACHED library symbol inside a sheet, and the project's own
`.kicad_sym`.  Leaving those stale is how a corrected instance gets silently
un-corrected the next time someone updates symbols from the library.  Same
rule: the old string must occur EXACTLY ONCE in that file or nothing is
written.

    python3 apply_bom_sourcing.py --plan PLAN.json [--apply] [-o OUT]

Without `--apply` it is a DRY RUN: it reports every property it would add and
writes nothing.
"""

import argparse
import hashlib
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SHEETS = ROOT / "hardware/demo/kicad/aqroot-demo"

SYMBOL = re.compile(r'^\t\(symbol\r?\n$')
SYMBOL_END = re.compile(r'^\t\)\r?\n$')
REFERENCE = re.compile(r'^\t\t\(property "Reference" "([^"]+)"\r?\n$')
PROPERTY = re.compile(r'^\t\t\(property "([^"]+)" "(.*)"\r?\n$')
PROP_END = re.compile(r'^\t\t\)\r?\n$')
AT = re.compile(r'^\t\t\t\(at .*\r?\n$')

FIELDS = ("Manufacturer", "MPN", "LCSC", "Note_Sourcing")


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def symbols(lines):
    """Yield (ref, {property name: value}, datasheet_end_index, at_line)."""
    i, n = 0, len(lines)
    while i < n:
        if not SYMBOL.match(lines[i]):
            i += 1
            continue
        j, ref, props, ds_end, at = i + 1, None, {}, None, None
        while j < n and not SYMBOL_END.match(lines[j]):
            m = PROPERTY.match(lines[j])
            if m:
                name, value = m.group(1), m.group(2)
                props[name] = value
                k = j + 1
                first_at = None
                while k < n and not PROP_END.match(lines[k]):
                    if first_at is None and AT.match(lines[k]):
                        first_at = lines[k]
                    k += 1
                if name == "Reference":
                    ref = value
                if name == "Datasheet":
                    ds_end, at = k, first_at
                j = k + 1
                continue
            j += 1
        yield ref, props, ds_end, at
        i = j + 1


def render(name, value, at):
    """A hidden property block in this file's own house style."""
    eol = "\r\n" if at.endswith("\r\n") else "\n"
    body = at.rstrip("\r\n")
    return "".join(l + eol for l in [
        '\t\t(property "%s" "%s"' % (name, value.replace('"', "'")),
        body,
        "\t\t\t(hide yes)",
        "\t\t\t(show_name no)",
        "\t\t\t(do_not_autoplace no)",
        "\t\t\t(effects",
        "\t\t\t\t(font",
        "\t\t\t\t\t(size 1.27 1.27)",
        "\t\t\t\t)",
        "\t\t\t)",
        "\t\t)"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", type=Path, required=True)
    ap.add_argument("--sheets", type=Path, default=SHEETS)
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("-o", "--out", type=Path)
    a = ap.parse_args()

    plan = json.loads(a.plan.read_text())
    want, replaces = {}, {}
    for line in plan["graft"]:
        if not str(line.get("Manufacturer") or "").strip():
            raise SystemExit("refusing: plan line %r has no Manufacturer"
                             % line["value"])
        if not (str(line.get("MPN") or "").strip()
                or str(line.get("LCSC") or "").strip()):
            raise SystemExit("refusing: plan line %r is not orderable -- it "
                             "carries neither an MPN nor an LCSC code"
                             % line["value"])
        basis = line["basis"]
        # A plan may state its own provenance sentence.  The graft plan
        # D-614 wrote could not -- every one of its lines came from the same
        # place -- but D-615's come from a distributor record with a DATE on
        # it, and that date is the evidence D-096 asks for.
        note = line.get("note") or (
            "SOURCING %s. %s from the beta-dm audit line %r (%s); "
            "manufacturer %s; %s." % (
                plan.get("decision", "D-614"), line["how"],
                basis["prior_value"], basis.get("verdict") or basis["source"],
                basis["manufacturer_basis"],
                "; ".join(basis["ruling"] or [])))
        for ref in line["refs"]:
            want[ref] = dict(Manufacturer=line["Manufacturer"],
                             MPN=line["MPN"], LCSC=line["LCSC"],
                             Note_Sourcing=note)
            replaces[ref] = dict(line.get("replaces") or {})

    added, conflicts, already, rewrites, edited = [], [], [], [], {}
    seen = set()
    for path in sorted(a.sheets.glob("*.kicad_sch")):
        raw = path.read_bytes().decode("utf-8")
        lines = raw.splitlines(keepends=True)
        inserts = []
        for ref, props, ds_end, at in symbols(lines):
            if ref not in want:
                continue
            seen.add(ref)
            if ds_end is None or at is None:
                conflicts.append("%s has no Datasheet property to place beside"
                                 % ref)
                continue
            new = []
            for name in FIELDS:
                value = want[ref][name]
                if not str(value).strip():
                    continue
                if name in props:
                    if props[name].strip() == value.strip():
                        already.append("%s.%s" % (ref, name))
                    elif name in replaces.get(ref, {}):
                        expect = replaces[ref][name]
                        if props[name].strip() != str(expect).strip():
                            conflicts.append(
                                "%s.%s is %r; the plan says it is replacing"
                                " %r" % (ref, name, props[name], expect))
                        else:
                            rewrites.append(dict(
                                ref=ref, sheet=path.name, property=name,
                                was=props[name], value=value))
                    else:
                        conflicts.append(
                            "%s already carries %s=%r, the plan says %r"
                            % (ref, name, props[name], value))
                    continue
                new.append(render(name, value, at))
                added.append(dict(ref=ref, sheet=path.name, property=name,
                                  value=value))
            if new:
                inserts.append((ds_end + 1, "".join(new)))
        mine = [r for r in rewrites if r["sheet"] == path.name]
        if inserts or mine:
            out = lines[:]
            for at_index, text in sorted(inserts, reverse=True):
                out.insert(at_index, text)
            for r in mine:
                old = '\t\t(property "%s" "%s"' % (r["property"], r["was"])
                new_line = '\t\t(property "%s" "%s"' % (r["property"],
                                                        r["value"])
                hits = [i for i, l in enumerate(out)
                        if l.rstrip("\r\n") == old]
                if len(hits) != 1:
                    conflicts.append(
                        "%s.%s: %d line(s) match the text being replaced,"
                        " expected exactly one" % (r["ref"], r["property"],
                                                   len(hits)))
                    continue
                eol = out[hits[0]][len(out[hits[0]].rstrip("\r\n")):]
                out[hits[0]] = new_line + eol
            edited[path.name] = "".join(out).encode("utf-8")

    # The identities that are not instance properties.  These run AFTER the
    # property edits and against their result, because the same sheet holds
    # both the instance and its cached library copy -- counting occurrences in
    # the original file would see the one this run has already corrected.
    staged = {str(a.sheets / name): data.decode("utf-8")
              for name, data in edited.items()}
    text_edits = []
    for rep in plan.get("text_replaces") or []:
        target = ROOT / rep["file"]
        key = str(target)
        if key not in staged:
            if not target.exists():
                conflicts.append("%s does not exist" % rep["file"])
                continue
            staged[key] = target.read_bytes().decode("utf-8")
        n = staged[key].count(rep["old"])
        if n != 1:
            conflicts.append(
                "%s: the text being replaced occurs %d time(s), expected"
                " exactly one" % (rep["file"], n))
            continue
        staged[key] = staged[key].replace(rep["old"], rep["new"], 1)
        text_edits.append(dict(rep, path=target))
    for rep in text_edits:
        edited[str(rep["path"])] = staged[str(rep["path"])].encode("utf-8")

    missing = sorted(set(want) - seen)
    doc = dict(schema=1, plan=str(a.plan),
               references_in_plan=len(want),
               references_found=len(seen),
               references_not_in_any_sheet=missing,
               properties_added=len(added),
               properties_rewritten=rewrites,
               text_replaces=[dict(file=r["file"], why=r.get("why"))
                              for r in text_edits],
               properties_already_correct=sorted(already),
               conflicts=conflicts,
               sheets_touched=sorted(Path(k).name for k in edited),
               sha256_before={p.name: sha256(p)
                              for p in sorted(a.sheets.glob("*.kicad_sch"))},
               added=added, applied=False)

    if conflicts or missing:
        doc["refused"] = True
        out = json.dumps(doc, indent=1, sort_keys=True, default=str) + "\n"
        if a.out:
            a.out.write_text(out)
        print(out)
        raise SystemExit("refusing: %d conflict(s), %d missing reference(s)"
                         % (len(conflicts), len(missing)))

    if a.apply and edited:
        for name, data in edited.items():
            path = Path(name) if Path(name).is_absolute() else a.sheets / name
            path.write_bytes(data)
        doc["applied"] = True
        doc["sha256_after"] = {p.name: sha256(p)
                               for p in sorted(a.sheets.glob("*.kicad_sch"))}

    out = json.dumps(doc, indent=1, sort_keys=True, default=str) + "\n"
    if a.out:
        a.out.write_text(out)
    print(json.dumps({k: doc[k] for k in
                      ("references_in_plan", "references_found",
                       "properties_added", "properties_rewritten",
                       "text_replaces",
                       "properties_already_correct",
                       "sheets_touched", "conflicts", "applied")},
                     indent=1, sort_keys=True))


if __name__ == "__main__":
    main()
