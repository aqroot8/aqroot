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
    want = {}
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
        note = ("SOURCING %s. %s from the beta-dm audit line %r (%s); "
                "manufacturer %s; %s." % (
                    plan.get("decision", "D-614"), line["how"],
                    basis["prior_value"], basis.get("verdict") or basis["source"],
                    basis["manufacturer_basis"],
                    "; ".join(basis["ruling"] or [])))
        for ref in line["refs"]:
            want[ref] = dict(Manufacturer=line["Manufacturer"],
                             MPN=line["MPN"], LCSC=line["LCSC"],
                             Note_Sourcing=note)

    added, conflicts, already, edited = [], [], [], {}
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
                    if props[name].strip() != value.strip():
                        conflicts.append(
                            "%s already carries %s=%r, the plan says %r"
                            % (ref, name, props[name], value))
                    else:
                        already.append("%s.%s" % (ref, name))
                    continue
                new.append(render(name, value, at))
                added.append(dict(ref=ref, sheet=path.name, property=name,
                                  value=value))
            if new:
                inserts.append((ds_end + 1, "".join(new)))
        if inserts:
            out = lines[:]
            for at_index, text in sorted(inserts, reverse=True):
                out.insert(at_index, text)
            edited[path.name] = "".join(out).encode("utf-8")

    missing = sorted(set(want) - seen)
    doc = dict(schema=1, plan=str(a.plan),
               references_in_plan=len(want),
               references_found=len(seen),
               references_not_in_any_sheet=missing,
               properties_added=len(added),
               properties_already_correct=sorted(already),
               conflicts=conflicts,
               sheets_touched=sorted(edited),
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
            (a.sheets / name).write_bytes(data)
        doc["applied"] = True
        doc["sha256_after"] = {p.name: sha256(p)
                               for p in sorted(a.sheets.glob("*.kicad_sch"))}

    out = json.dumps(doc, indent=1, sort_keys=True, default=str) + "\n"
    if a.out:
        a.out.write_text(out)
    print(json.dumps({k: doc[k] for k in
                      ("references_in_plan", "references_found",
                       "properties_added", "properties_already_correct",
                       "sheets_touched", "conflicts", "applied")},
                     indent=1, sort_keys=True))


if __name__ == "__main__":
    main()
