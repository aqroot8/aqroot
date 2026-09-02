#!/usr/bin/env python3
import csv
import hashlib
import json
import re
import sys
from pathlib import Path


def refs(cell: str) -> set[str]:
    result: set[str] = set()
    for token in cell.split(","):
        token = token.strip()
        match = re.fullmatch(r"([A-Z#]+)(\d+)-([A-Z#]*)(\d+)", token)
        if match and (not match.group(3) or match.group(1) == match.group(3)):
            prefix = match.group(1)
            result.update(f"{prefix}{number}" for number in range(int(match.group(2)), int(match.group(4)) + 1))
        elif token:
            result.add(token)
    return result


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as stream:
        return list(csv.DictReader(stream))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    if len(sys.argv) != 3:
        raise SystemExit("usage: check_candidate.py OUTPUT_DIRECTORY BOARD")
    output = Path(sys.argv[1]).resolve()
    board = Path(sys.argv[2]).resolve()
    fitted = read_csv(output / "aqroot-demo-bom-fitted.csv")
    full = read_csv(output / "aqroot-demo-bom-full.csv")
    cpl = read_csv(output / "aqroot-demo-cpl.csv")

    fitted_refs = set().union(*(refs(row["Refs"]) for row in fitted))
    full_refs = set().union(*(refs(row["Refs"]) for row in full))
    dnp_refs = set().union(*(refs(row["Refs"]) for row in full if row["DNP"].strip()))
    cpl_refs = {row["Ref"] for row in cpl}
    missing_mpn = sorted(set().union(*(refs(row["Refs"]) for row in fitted if not row["MPN"].strip())))
    missing_lcsc = sorted(set().union(*(refs(row["Refs"]) for row in fitted if not row["LCSC"].strip())))

    expected_gerbers = {
        "aqroot-Beta-v2-F_Cu.gtl", "aqroot-Beta-v2-In1_Cu.g1",
        "aqroot-Beta-v2-In2_Cu.g2", "aqroot-Beta-v2-In3_Cu.g3",
        "aqroot-Beta-v2-In4_Cu.g4", "aqroot-Beta-v2-B_Cu.gbl",
        "aqroot-Beta-v2-F_Paste.gtp", "aqroot-Beta-v2-B_Paste.gbp",
        "aqroot-Beta-v2-F_Silkscreen.gto", "aqroot-Beta-v2-B_Silkscreen.gbo",
        "aqroot-Beta-v2-F_Mask.gts", "aqroot-Beta-v2-B_Mask.gbs",
        "aqroot-Beta-v2-Edge_Cuts.gm1", "aqroot-Beta-v2-job.gbrjob",
        "aqroot-Beta-v2-PTH.drl", "aqroot-Beta-v2-NPTH.drl", "drill-report.txt",
    }
    actual = {path.name for path in (output / "gerbers").iterdir() if path.is_file()}
    empty = sorted(path.name for path in (output / "gerbers").iterdir() if path.is_file() and path.stat().st_size == 0)
    drill_report = (output / "gerbers/drill-report.txt").read_text(encoding="utf-8")
    pth = re.search(r"Total plated holes count (\d+)", drill_report)
    npth = re.search(r"Total unplated holes count (\d+)", drill_report)

    blockers = []
    if missing_mpn:
        blockers.append("fitted BOM has references without an MPN")
    if expected_gerbers - actual or empty:
        blockers.append("manufacturing plot set is incomplete or empty")
    if not pth or not npth:
        blockers.append("drill report lacks PTH/NPTH totals")
    if dnp_refs & cpl_refs:
        blockers.append("DNP references leaked into CPL")

    report = {
        "result": "BLOCKED" if blockers else "PASS",
        "board_sha256": sha256(board),
        "counts": {
            "full_bom_references": len(full_refs),
            "fitted_bom_references": len(fitted_refs),
            "dnp_references": len(dnp_refs),
            "cpl_references": len(cpl_refs),
            "fitted_without_mpn": len(missing_mpn),
            "fitted_without_lcsc": len(missing_lcsc),
            "pth_holes": int(pth.group(1)) if pth else None,
            "npth_holes": int(npth.group(1)) if npth else None,
        },
        "reference_checks": {
            "dnp_in_cpl": sorted(dnp_refs & cpl_refs),
            "cpl_not_in_fitted_bom": sorted(cpl_refs - fitted_refs),
            "fitted_bom_not_in_cpl": sorted(fitted_refs - cpl_refs),
        },
        "missing_mpn_references": missing_mpn,
        "missing_lcsc_references": missing_lcsc,
        "missing_plot_files": sorted(expected_gerbers - actual),
        "unexpected_plot_files": sorted(actual - expected_gerbers),
        "empty_plot_files": empty,
        "blockers": blockers,
    }
    (output / "preflight.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 1 if blockers else 0


if __name__ == "__main__":
    raise SystemExit(main())
