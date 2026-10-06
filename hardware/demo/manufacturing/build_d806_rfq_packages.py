#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AQROOT Demo -- D-806 RFQ / technical-review packages (JLCPCB and vendor-neutral).

Built ONLY from the released fab package (`hardware/demo/fab`, its MANIFEST must verify)
and the D-806 decision documents.  Nothing here orders, pays, uploads or authorizes
anything: every README states it.  Output is byte-deterministic (fixed zip timestamps,
sorted entries), so the SHA256SUMS of a rebuild are the same.

    python3 build_d806_rfq_packages.py [--out delivery]
"""
import argparse
import csv
import hashlib
import io
import json
import shutil
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
FAB = ROOT / "hardware/demo/fab"
DOCS = ROOT / "docs/full-beta-v2/assembly"
EVID = HERE / "evidence"
ZIP_TIME = (2026, 10, 6, 0, 0, 0)
R = "D806"


def sha256(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def verify_manifest():
    m = json.loads((FAB / "MANIFEST.json").read_text())
    bad = [f["path"] for f in m["files"] if sha256(FAB / f["path"]) != f["sha256"]]
    if bad:
        raise SystemExit("fab MANIFEST does not verify: %s" % bad)
    return m


def det_zip(path, entries):
    """entries: list of (arcname, bytes)."""
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for name, data in sorted(entries):
            zi = zipfile.ZipInfo(name, ZIP_TIME)
            zi.external_attr = 0o644 << 16
            zi.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(zi, data)


def jlc_bom():
    rows = list(csv.DictReader(open(FAB / "aqroot-Demo-BOM-assembly.csv", newline="")))
    out = io.StringIO()
    w = csv.writer(out, lineterminator="\r\n")   # the D-805 JLCPCB files are CRLF
    w.writerow(["Comment", "Designator", "Footprint", "LCSC Part #", "Manufacturer Part Number",
                "Manufacturer", "Quantity"])
    for r in rows:
        w.writerow([r["Value"], r["Refs"], r["Footprint"], r["LCSC"], r["MPN"], r["Manufacturer"], r["Qty"]])
    return out.getvalue().encode()


def jlc_cpl():
    rows = list(csv.DictReader(open(FAB / "aqroot-Demo-pos-fitted.csv", newline="")))
    out = io.StringIO()
    w = csv.writer(out, lineterminator="\r\n")   # the D-805 JLCPCB files are CRLF
    w.writerow(["Designator", "Mid X", "Mid Y", "Rotation", "Layer"])
    for r in rows:
        w.writerow([r["Ref"], r["PosX"], r["PosY"], r["Rot"], r["Side"].capitalize()])
    return out.getvalue().encode()


def facts(m):
    j = json.loads((EVID / "d806-jlc-manufacturing-contract.json").read_text())["checks"]
    return dict(
        board=m["source"]["board_sha256"], manifest=sha256(FAB / "MANIFEST.json"),
        j2=j["JLC1_J2_shell_land_to_routed_edge"]["board"]["shell_land_to_edge_min_mm"],
        j2g=j["JLC1_J2_shell_land_to_routed_edge"]["gerber"]["shell_land_to_edge_min_mm"],
        u9b=j["JLC2_U9_pre_cam_gap_board"]["min_gap_mil"],
        u9g=j["JLC3_U9_gap_gerber_and_board_wide_floor"]["u9_window_min_gap_mil"],
        u9g_mm=j["JLC3_U9_gap_gerber_and_board_wide_floor"]["u9_window_min_gap_mm"],
        post=j["JLC3_U9_gap_gerber_and_board_wide_floor"]["modelled_post_cam_mil"],
        bw=j["JLC3_U9_gap_gerber_and_board_wide_floor"]["board_wide_min_gap_mil"],
        vias=j["JLC4_via_outer_minus_hole"]["board"]["vias"],
        via_in_pad=m["via_in_pad"]["solderable_lands_with_an_open_barrel"],
        barrels=m["via_in_pad"]["distinct_barrels"],
        fitted=j["JLC5_reference_designator_mapping"]["fitted"])


def requirements(f, vendor):
    jl = vendor == "JLCPCB"
    return f"""AQROOT D-806 -- {'JLCPCB ' if jl else ''}RFQ / TECHNICAL REVIEW REQUIREMENTS
Board sha256 {f['board']}
Fab MANIFEST sha256 {f['manifest']}

THIS PACKAGE IS FOR QUOTATION AND DFM/DFA REVIEW ONLY.  IT DOES NOT AUTHORIZE FABRICATION,
ASSEMBLY, COMPONENT PURCHASE, OR ANY NON-CANCELLABLE PROCUREMENT.  Do not start any work
until a separate written order authorization is issued by the owner.

1. QUANTITY
- 2 fully assembled PCBAs.  The bare-board MOQ may be higher: quote the bare-board quantity
  your process requires and assemble only 2.
- Quote PCB, components, assembly, tooling/stencil/engineering fees, inspection and
  shipping separately where possible; state MOQ / attrition.

2. EXACT PARTS -- NO SUBSTITUTION
- Exact manufacturer part numbers only.  NO substitution, "equivalent" or alternate of any
  kind without written approval naming the reference and the part.
- If a line cannot be sourced, say so and quote it as CUSTOMER-SUPPLIED (consigned) for
  MACHINE placement; see AQROOT_{R}_Sourcing_Decision_Record.md.  Fine-pitch / RF / power
  parts stay on the machine line even when consigned.
- J5 is Samtec SSQ-124-02-G-S-RA exactly (mechanically critical; customer-supplied; hand
  soldered after reflow).  Do not move, trim or substitute J5.
- U1 is ESP32-S3-WROOM-1-N16R8 exactly.
- Do not populate any DNP reference (AQROOT_{R}_DNP.csv).

3. REQUIRED MANUAL APPROVAL GATES -- NO AUTOMATIC CONFIRMATION
- PRODUCTION FILE CONFIRMATION: REQUIRED, MANUAL.  Return the CAM/production files (incl.
  the profile/rout preview, any panel drawing and the stackup) for written approval.
- PARTS PLACEMENT CONFIRMATION: REQUIRED, MANUAL.  Return the placement preview (side,
  position, rotation, pin 1) for written approval before assembly.
- Do NOT auto-confirm either gate.  Silence is not approval.
- Do NOT change copper, pads, drills, solder mask, paste, plated slots, outline/profile,
  component placement, stackup or BOM without written approval.  Any CAM/profile/stackup/
  placement change requires written approval.

4. JLCPCB ENGINEERING REVIEW 2026-10-06 -- ITEM BY ITEM (D-806 response)
- J2 microSD edge clearance: J2 moved 0.150 mm inward (outline unchanged).  J2 shell lands
  now stand {f['j2']:.3f} mm from the routed J2 tab edge (Gerber-measured {f['j2g']:.3f} mm);
  requirement >= 0.25 mm on a non-V-cut edge, D-806 target >= 0.30 mm: MET.  NO V-SCORE on
  any edge of this board.
- U9 different-net clearance: U9's eight corner lands were heel-trimmed 0.030 mm.  U9
  pre-CAM minimum different-net gap {f['u9g']:.3f} mil ({f['u9g_mm']:.4f} mm) from the Gerbers
  ({f['u9b']:.3f} mil from the board polygons); requirement >= 5.2 mil, target >= 6.0 mil:
  MET.  Modelled post-CAM (-1.2 mil) {f['post']:.3f} mil >= 4.0 mil.  Board-wide minimum
  different-net gap in these Gerbers: {f['bw']:.3f} mil.  Please confirm post-CAM >= 4.0 mil.
- Via outer diameter >= hole + 0.20 mm: every one of the board's {f['vias']} vias now meets
  it (35 grown from 0.35/0.20 to 0.40/0.20 mm; drills unchanged).
- Reference designators: the production silkscreen intentionally carries none.  Use
  AQROOT_{R}_Reference_Locator_Top.pdf / _Bottom.pdf (A3, 2.5:1, every one of the {f['fitted']}
  fitted references labelled at its CPL centroid, 10 mm grid, index pages) and
  AQROOT_{R}_Reference_Index.csv; the KiCad assembly drawings remain included.
- "Stepped board profile": replaced by an explicit drawing.  See AQROOT_{R}_Board_Profile.pdf
  (+ .json): two bottom tabs (J2_TAB X 6.000-24.000, J3_TAB X 36.500-49.500, 3.000 mm below
  the main bottom edge, R1.000 drawn inside fillets, R0.500 outside corners), an east step
  (X 72.000 -> 77.000 between Y 70.500 and 104.005, two sharp inside corners), four plated
  routed slots.  Do not normalise, straighten, square or fill any of it.
- Board thickness: see section 6 -- HOLD.
- Standard PCBA edge rails: see AQROOT_{R}_Panel_Edge_Rail_Strategy.md.  Finished-board
  outline after depanelization must equal the profile drawing exactly.
- Production file / placement confirmation: section 3.

5. PCB
- 6-layer FR-4, Tg >= 150 C, ENIG, 1 oz outer / 0.5 oz inner (see the stackup spec).
- Minimum finished drill 0.20 mm.  Through vias only; no blind, buried or micro vias.
- VIA-IN-PAD / LAND-INTERSECTING VIAS: {f['barrels']} barrels open into {f['via_in_pad']} solderable
  lands (listed in the fab notes and MANIFEST via_in_pad).  They REQUIRE resin fill,
  planarization and copper capping (POFV / VIPPO-equivalent planar solderable process).
  Applying the process to every via is acceptable.  Shipping them open is not.
- Preserve routed/plated slots (Excellon G85) as slots.  100 % bare-board electrical test.

6. BOARD THICKNESS -- HOLD (owner approval required)
- Acceptance stays 1.5744 +/- 0.10 mm until the owner decides otherwise in writing.
{'- JLCPCB stated nominal 1.6 mm +/-10 % (1.44-1.76 mm).  That is recorded as a VENDOR' if jl else '- A vendor band wider than the acceptance (e.g. 1.6 mm +/-10 %) is a VENDOR'}
  EXCEPTION requiring written owner approval -- NOT accepted by this package.  Evidence:
  J6 (JST B2B-PH-K-S, through-hole) is rated for 0.8-1.6 mm board; see
  AQROOT_{R}_Board_Thickness_Position.md.
- Please state the finished-thickness band you can hold on the declared stack (or your
  proposed equivalent stack, layer by layer, for written approval), and whether a maximum
  of 1.60 mm is available.

7. ASSEMBLY
- Place from AQROOT_{R}_{'JLCPCB_' if jl else ''}CPL.csv (= aqroot-Demo-pos-fitted.csv; Y is NEGATIVE, Y-up
  frame; bottom-side rotation as seen from the TOP -- read the fab notes CPL section).
- X-ray first article for bottom-terminated packages incl. U11, U9, U12 and the ESP32
  module ground pad.
- J4 is a manual battery pigtail land (no part, not in the CPL).  D1/U6 need the documented
  manual lead forming.  J5, J6, D1, U6 are post-reflow through-hole operations.

PLEASE RETURN
- Total / PCB / components / assembly / tooling / shipping, lead time, MOQ / attrition.
- Written answers: J2 edge acceptance; U9 post-CAM >= 4.0 mil; via-in-pad process; the
  thickness band you can hold; profile/rout preview incl. tabs, fillets, sharp corners and
  slots; your panel / edge-rail proposal and depanelization method; any line you cannot
  source.

NO FABRICATION, ASSEMBLY OR NON-CANCELLABLE PROCUREMENT IS AUTHORIZED BY THIS PACKAGE.
"""


def readme(f, vendor, files):
    jl = vendor == "JLCPCB"
    head = "AQROOT D-806 -- %s PCB/PCBA RFQ PACKAGE" % ("JLCPCB" if jl else "PROTOTYPE (VENDOR-NEUTRAL, e.g. PCBWay)")
    online = """
Online PCB configuration to prepare (quote only):
- FR-4, 6 layers, Tg >= 150 C (e.g. S1000H Tg155)
- 1.6 mm nominal -- thickness tolerance: HOLD, see RFQ_REQUIREMENTS section 6
- ENIG; 1 oz outer / 0.5 oz inner
- 0.20 mm minimum via hole; epoxy filled & capped vias (POFV)
- Flying-probe full electrical test
- Standard PCBA, both sides; manual component matching; exact MPNs
- Production file confirmation: YES (manual).  Parts placement confirmation: YES (manual).
- No V-score.  Edge rails: per AQROOT_D806_Panel_Edge_Rail_Strategy.md.
""" if jl else ""
    return (head + "\n\nBoard sha256 %s\nFab MANIFEST sha256 %s\n" % (f["board"], f["manifest"])
            + "\nQuantity: 2 assembled PCBAs (bare-board MOQ may be higher).\n" + online
            + "\nRead RFQ_REQUIREMENTS.txt first.  Files:\n"
            + "".join("- %s\n" % n for n in files)
            + "\nThis package is for quotation and DFM/DFA review only.  It does NOT authorize\n"
              "fabrication, assembly, payment or any non-cancellable procurement.\n")


def stackup():
    s = (FAB / "aqroot-Demo-FAB-NOTES.md").read_text()
    i = s.index("## Stackup, finish and required process")
    j = s.index("\n## ", i + 5)
    return ("AQROOT D-806 - PCB STACKUP SPECIFICATION (extract of the fabrication notes)\n\n"
            + s[i:j].strip()
            + "\n\nD-806 THICKNESS POSITION: acceptance 1.5744 +/- 0.10 mm is UNCHANGED; a vendor band such\n"
              "as 1.6 mm +/-10 % is a vendor exception requiring written owner approval (HOLD).\n"
              "See AQROOT_D806_Board_Thickness_Position.md.\n")


def build(vendor, out_root, m):
    f = facts(m)
    name = "AQROOT_D806_JLCPCB_RFQ" if vendor == "JLCPCB" else "AQROOT_D806_Prototype_PCBA_RFQ"
    d = out_root / name
    if d.exists():
        shutil.rmtree(d)
    d.mkdir(parents=True)
    g = FAB / "gerbers"
    gz = d / ("AQROOT_%s_Gerbers.zip" % R)
    det_zip(gz, [(p.name, p.read_bytes()) for p in sorted(g.iterdir()) if p.is_file()])
    files = {
        "AQROOT_%s_Fabrication_Notes.md" % R: (FAB / "aqroot-Demo-FAB-NOTES.md").read_bytes(),
        "AQROOT_%s_Stackup_Specification.txt" % R: stackup().encode(),
        "AQROOT_%s_DNP.csv" % R: (FAB / "aqroot-Demo-DO-NOT-POPULATE.csv").read_bytes(),
        "AQROOT_%s_Assembly_Top.pdf" % R: (FAB / "aqroot-Demo-assembly-top.pdf").read_bytes(),
        "AQROOT_%s_Assembly_Bottom.pdf" % R: (FAB / "aqroot-Demo-assembly-bottom.pdf").read_bytes(),
        "AQROOT_%s_Reference_Locator_Top.pdf" % R: (FAB / "aqroot-Demo-assembly-locator-top.pdf").read_bytes(),
        "AQROOT_%s_Reference_Locator_Bottom.pdf" % R: (FAB / "aqroot-Demo-assembly-locator-bottom.pdf").read_bytes(),
        "AQROOT_%s_Reference_Index.csv" % R: (FAB / "aqroot-Demo-assembly-ref-index.csv").read_bytes(),
        "AQROOT_%s_Board_Profile.pdf" % R: (FAB / "aqroot-Demo-board-profile.pdf").read_bytes(),
        "AQROOT_%s_Board_Profile.json" % R: (FAB / "aqroot-Demo-board-profile.json").read_bytes(),
        "AQROOT_%s_Sourcing_Decision_Record.md" % R: (DOCS / "D806_SOURCING_DECISION_RECORD.md").read_bytes(),
        "AQROOT_%s_Board_Thickness_Position.md" % R: (DOCS / "D806_BOARD_THICKNESS_POSITION.md").read_bytes(),
        "AQROOT_%s_Panel_Edge_Rail_Strategy.md" % R: (DOCS / "D806_PANEL_AND_EDGE_RAIL_STRATEGY.md").read_bytes(),
        "RFQ_REQUIREMENTS.txt": requirements(f, vendor).encode(),
    }
    if vendor == "JLCPCB":
        files["AQROOT_%s_JLCPCB_BOM.csv" % R] = jlc_bom()
        files["AQROOT_%s_JLCPCB_CPL.csv" % R] = jlc_cpl()
    else:
        files["AQROOT_%s_BOM_assembly.csv" % R] = (FAB / "aqroot-Demo-BOM-assembly.csv").read_bytes()
        files["AQROOT_%s_BOM_full.csv" % R] = (FAB / "aqroot-Demo-BOM-full.csv").read_bytes()
        files["AQROOT_%s_CPL.csv" % R] = (FAB / "aqroot-Demo-pos-fitted.csv").read_bytes()
        files["AQROOT_%s_CPL_all_incl_DNP.csv" % R] = (FAB / "aqroot-Demo-pos-all.csv").read_bytes()
    names = sorted(list(files) + [gz.name])
    rd = "README_JLCPCB.txt" if vendor == "JLCPCB" else "README.txt"
    files[rd] = readme(f, vendor, names).encode()
    for n, b in files.items():
        (d / n).write_bytes(b)
    sums = "".join("%s  ./%s\n" % (sha256(d / n), n) for n in sorted(list(files) + [gz.name]))
    (d / "SHA256SUMS.txt").write_text(sums)
    entries = [("%s/%s" % (name, p.name), p.read_bytes()) for p in sorted(d.iterdir())]
    z = out_root / (name + ".zip")
    det_zip(z, entries)
    return dict(dir=str(d.relative_to(ROOT)), zip=str(z.relative_to(ROOT)), zip_sha256=sha256(z),
                files=len(entries), sha256sums_sha256=sha256(d / "SHA256SUMS.txt"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=ROOT / "delivery")
    a = ap.parse_args()
    m = verify_manifest()
    # the JLCPCB BOM must be the D-805 JLCPCB BOM, byte for byte: D-806 changes no BOM line
    rep = dict(manifest_sha256=sha256(FAB / "MANIFEST.json"), board_sha256=m["source"]["board_sha256"],
               packages=[build("JLCPCB", a.out, m), build("NEUTRAL", a.out, m)])
    print(json.dumps(rep, indent=1))


if __name__ == "__main__":
    main()
