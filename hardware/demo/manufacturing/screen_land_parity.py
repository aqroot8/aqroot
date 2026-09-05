#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AQROOT Demo -- prove every LAND on the board against its library master.

The fabrication package has no contract that a land pattern is the right land
pattern.  D-615 found the class is real (`U18` was ordered in a DFN body on an
MSOP-10 land) and closed that one instance from the PART side, by reading the
distributor's package field.  This module asks the same question from the BOARD
side, and it asks it of the geometry rather than of a name.

KiCad already owns the comparison -- `lib_footprint_mismatch`, "footprint does
not match copy in library".  On this machine it has never run.  KiCad's stock
footprint libraries are installed under `/usr/share/kicad/footprints` but no
global `fp-lib-table` was ever written (that happens on the first GUI launch,
and nothing here has ever launched a GUI), so the project resolves exactly ONE
nickname -- its own `AQROOT_Beta` -- and every other footprint on the board
reports `lib_footprint_issues`: *"the current configuration does not include
the footprint library 'Resistor_SMD'"*.  **199 of them, which is the whole
number this repository has carried as an INHERITED DRC class since before the
router existed.**  It is not a nuisance count.  It is 199 lands whose master
was never opened -- the fifth instance of one failure (D-607, D-610, D-611,
D-613): a check that reads clean because it was never asked.

So this module does two things:

  * it RESOLVES the libraries the way a normal KiCad installation does -- the
    project table plus the stock table KiCad itself ships at
    `template/fp-lib-table` -- and
  * it compares, pad by pad, in the footprint's OWN un-rotated frame, every
    property that reaches the fabricator: number, position, size, shape and its
    corner ratios, drill and drill shape, pad type, layer set, rotation, offset,
    die length, and any local mask/paste/clearance override.

The verdict per reference is one of:

    MATCH        every pad identical to the master, to the nanometre
    MISMATCH     at least one pad differs -- named, with both values
    NO_MASTER    the nickname resolves to no library, or the library has no
                 such footprint
    NO_NICKNAME  the board footprint carries a bare name and no library at all,
                 so it has no master to be compared against

`NO_MASTER` and `NO_NICKNAME` are NOT passes.  They are the residual: lands that
no upstream review stands behind, and which need a datasheet ruling of their
own.  Reporting them as anything else would be the D-611 failure again.

Read-only.  It loads the committed board and the libraries and writes nothing
but its report.

    python3 hardware/demo/manufacturing/screen_land_parity.py -o REPORT.json \
        [--worklist RESIDUAL.csv] [--perturb REF] [--verbose]

`--perturb REF` is the negative control: it grows one pad of one reference by a
micron in memory before comparing, and the run is only trustworthy if that
reference then reports MISMATCH.
"""

import argparse
import csv
import json
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PROJECT = ROOT / "hardware/demo/kicad/aqroot-demo"
BOARD = PROJECT / "aqroot-Beta-v2.kicad_pcb"

# Where KiCad's own stock libraries live.  The nickname->directory mapping is
# taken from the table KiCad SHIPS, not invented here, so this module registers
# exactly what a first GUI launch would have registered.
STOCK_ROOTS = [Path(p) for p in (
    os.environ.get("AQROOT_KICAD_SHARE", ""), "/usr/share/kicad",
    "/usr/local/share/kicad", "/opt/kicad/share/kicad") if p]

LIB_RE = re.compile(r'\(lib\s+\(name\s+"?([^")]+)"?\)\s*\(type\s+"?([^")]+)"?\)'
                    r'\s*\(uri\s+"?([^")]+)"?\)')


def read_lib_table(path, subst):
    """nickname -> directory, from a `fp-lib-table`, ${VAR} expanded."""
    out = {}
    if not Path(path).exists():
        return out
    for name, kind, uri in LIB_RE.findall(Path(path).read_text(encoding="utf-8")):
        if kind != "KiCad":
            continue
        for var, val in subst.items():
            uri = uri.replace("${%s}" % var, str(val))
        out[name] = Path(uri)
    return out


def resolve_libraries():
    """The project's own nicknames PLUS KiCad's stock table, project first."""
    share = next((r for r in STOCK_ROOTS
                  if (r / "template/fp-lib-table").exists()
                  and (r / "footprints").is_dir()), None)
    stock = {}
    if share is not None:
        # KICAD<n>_FOOTPRINT_DIR: the version digits vary, so substitute every
        # *_FOOTPRINT_DIR spelling the shipped table actually uses.
        text = (share / "template/fp-lib-table").read_text(encoding="utf-8")
        subst = {v: share / "footprints"
                 for v in set(re.findall(r"\$\{(\w*FOOTPRINT_DIR)\}", text))}
        stock = read_lib_table(share / "template/fp-lib-table", subst)
    proj = read_lib_table(PROJECT / "fp-lib-table", {"KIPRJMOD": PROJECT})
    merged = dict(stock)
    merged.update(proj)          # project nicknames shadow stock ones
    return merged, sorted(proj), share


def mirror_layer(name):
    """F.Cu <-> B.Cu and every other front/back pair; inner layers unchanged."""
    if name.startswith("F."):
        return "B." + name[2:]
    if name.startswith("B."):
        return "F." + name[2:]
    return name


def pad_sig(pad, flip=False, copper_layers=0):
    """Everything about a pad that reaches the fabricator, footprint-local.

    A footprint placed on B.Cu is the SAME land, mirrored.  When `flip` is set
    the board pad is normalised back into the master's frame -- local Y and pad
    rotation negated, every layer mapped through KiCad's own `FlipLayer` -- so a
    bottom-side part is compared against its real master and is not refused for
    being on the bottom.  Nothing else about a pad changes under a flip.
    """
    import pcbnew
    p = pad.GetFPRelativePosition()
    off = pad.GetOffset()
    d = pad.GetDrillSize()
    layers = tuple(sorted(mirror_layer(pcbnew.LayerName(l)) if flip
                          else pcbnew.LayerName(l)
                          for l in pad.GetLayerSet().Seq()))
    rot = pad.GetFPRelativeOrientation().AsDegrees()
    return (
        int(p.x), int(-p.y if flip else p.y),
        int(pad.GetSizeX()), int(pad.GetSizeY()),
        int(d.x), int(d.y), int(pad.GetDrillShape()),
        int(pad.GetShape()), int(pad.GetAttribute()), int(pad.GetProperty()),
        layers,
        round((-rot if flip else rot) % 360.0, 6),
        int(off.x), int(-off.y if flip else off.y),
        round(float(pad.GetRoundRectRadiusRatio()), 9),
        round(float(pad.GetChamferRectRatio()), 9),
        int(pad.GetChamferPositions()),
        int(pad.GetPadToDieLength()),
        pad.GetLocalClearance(), pad.GetLocalSolderMaskMargin(),
        pad.GetLocalSolderPasteMargin(),
        (None if pad.GetLocalSolderPasteMarginRatio() is None
         else round(float(pad.GetLocalSolderPasteMarginRatio()), 9)),
        bool(pad.GetKeepTopBottom()), bool(pad.GetRemoveUnconnected()),
    )


FIELDS = ("x_nm", "y_nm", "size_x_nm", "size_y_nm", "drill_x_nm", "drill_y_nm",
          "drill_shape", "shape", "pad_type", "property", "layers",
          "rotation_deg", "offset_x_nm", "offset_y_nm", "roundrect_ratio",
          "chamfer_ratio", "chamfer_positions", "pad_to_die_nm",
          "local_clearance", "local_mask_margin", "local_paste_margin",
          "local_paste_ratio", "keep_top_bottom", "remove_unconnected")


def pads_of(fp, flip=False, copper_layers=0):
    """number -> sorted list of signatures (a number may land more than once)."""
    out = {}
    for pad in fp.Pads():
        out.setdefault(pad.GetNumber(), []).append(
            pad_sig(pad, flip, copper_layers))
    return {k: sorted(v, key=repr) for k, v in out.items()}


def compare(board_fp, master_fp, verbose, flip=False, copper_layers=0):
    a = pads_of(board_fp, flip, copper_layers)
    b = pads_of(master_fp)
    diffs = []
    for num in sorted(set(a) - set(b)):
        diffs.append({"pad": num, "issue": "pad_not_in_master"})
    for num in sorted(set(b) - set(a)):
        diffs.append({"pad": num, "issue": "pad_missing_from_board"})
    for num in sorted(set(a) & set(b)):
        if len(a[num]) != len(b[num]):
            diffs.append({"pad": num, "issue": "land_count",
                          "board": len(a[num]), "master": len(b[num])})
            continue
        for i, (x, y) in enumerate(zip(a[num], b[num])):
            for f, bv, mv in zip(FIELDS, x, y):
                if bv != mv:
                    diffs.append({"pad": num, "land": i, "issue": f,
                                  "board": bv, "master": mv})
    return diffs if verbose else diffs[:12], len(diffs)


def survey(perturb=None, verbose=False):
    """Every board footprint against its library master.  The single place the
    comparison is done; `land_parity_contract.py` calls this, not a copy."""
    import pcbnew
    libs, project_nicknames, share = resolve_libraries()
    board = pcbnew.LoadBoard(str(BOARD))
    copper_layers = board.GetCopperLayerCount()

    if perturb:
        pad = list(board.FindFootprintByReference(perturb).Pads())[0]
        pad.SetSizeX(pad.GetSizeX() + 1000)

    rows, cache = [], {}
    for fp in board.GetFootprints():
        fpid = fp.GetFPID()
        nick = fpid.GetLibNickname().wx_str()
        name = fpid.GetLibItemName().wx_str()
        row = {"ref": fp.GetReference(), "library": nick, "footprint": name,
               "identity": "%s:%s" % (nick, name),
               "value": fp.GetValue(), "pads": len(list(fp.Pads())),
               "dnp": bool(fp.IsDNP()),
               "excluded_from_bom": bool(fp.IsExcludedFromBOM())}
        if not nick:
            row.update(verdict="NO_NICKNAME",
                       reason="board footprint carries no library nickname")
        elif nick not in libs:
            row.update(verdict="NO_MASTER",
                       reason="nickname %r resolves to no library" % nick)
        elif not (libs[nick] / (name + ".kicad_mod")).exists():
            row.update(verdict="NO_MASTER",
                       reason="library %r has no footprint %r" % (nick, name))
        else:
            key = (nick, name)
            if key not in cache:
                cache[key] = pcbnew.FootprintLoad(str(libs[nick]), name)
            master = cache[key]
            if master is None:
                row.update(verdict="NO_MASTER", reason="master failed to load")
            else:
                diffs, n = compare(fp, master, verbose,
                                   bool(fp.IsFlipped()), copper_layers)
                row.update(verdict="MATCH" if not n else "MISMATCH",
                           flipped=bool(fp.IsFlipped()),
                           master=str(libs[nick] / (name + ".kicad_mod")),
                           project_owned=nick in project_nicknames,
                           diff_count=n, diffs=diffs)
        rows.append(row)
    return rows, libs, sorted(project_nicknames), share, copper_layers


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-o", "--out", type=Path)
    ap.add_argument("--worklist", type=Path)
    ap.add_argument("--perturb", help="negative control: grow one pad by 1 um")
    ap.add_argument("--verbose", action="store_true")
    a = ap.parse_args()

    rows, libs, project_nicknames, share, copper_layers = survey(
        a.perturb, a.verbose)

    rows.sort(key=lambda r: (r["verdict"] != "MISMATCH", r["ref"]))
    counts = {}
    for r in rows:
        counts[r["verdict"]] = counts.get(r["verdict"], 0) + 1

    # A land is only PROVEN when it matched a master that some upstream review
    # stands behind.  A project-owned master was drawn here, so matching it
    # proves the board agrees with this repository -- not with a datasheet.
    proven = [r for r in rows
              if r["verdict"] == "MATCH" and not r.get("project_owned")]
    self_consistent = [r for r in rows
                       if r["verdict"] == "MATCH" and r.get("project_owned")]
    residual = [r for r in rows if r["verdict"] != "MATCH"]
    fitted = [r for r in rows if not r["dnp"] and not r["excluded_from_bom"]]

    report = {
        "schema": 1,
        "board": str(BOARD.relative_to(ROOT)),
        "kicad_share": str(share) if share else None,
        "libraries_resolved": len(libs),
        "copper_layers": copper_layers,
        "project_nicknames": project_nicknames,
        "perturbed": a.perturb,
        "footprints": len(rows),
        "fitted_purchased": len(fitted),
        "counts": counts,
        "upstream_proven": len(proven),
        "project_master_only": len(self_consistent),
        "residual": len(residual),
        "residual_refs": sorted(r["ref"] for r in residual),
        "rows": rows,
    }
    text = json.dumps(report, indent=2, sort_keys=True, default=str)
    if a.out:
        a.out.write_text(text + "\n", encoding="utf-8")
    if a.worklist:
        with a.worklist.open("w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(["ref", "verdict", "library", "footprint", "value",
                        "pads", "dnp", "reason_or_first_diff"])
            for r in residual:
                d = r.get("reason") or json.dumps(r.get("diffs", [])[:1])
                w.writerow([r["ref"], r["verdict"], r["library"],
                            r["footprint"], r["value"], r["pads"],
                            int(r["dnp"]), d])
    print(json.dumps({k: v for k, v in report.items() if k != "rows"},
                     indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
