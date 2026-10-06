AQROOT D-805 - PCBWay REQUOTE PACKAGE (quotation request only - NOT an order)
Previous inquiry: W1187157AS5D1 (D-804)

Revision: D-805.  This package supersedes the D-804 files for QUOTATION purposes.
Nothing in this package authorizes fabrication or assembly.

What changed from D-804 (layout only; same schematic, same BOM, same stackup):
- Board outline: two local tabs on the bottom edge, x 6.0..24.0 mm and x 36.5..49.5 mm,
  extend the profile from Y 148.0 to Y 151.0 mm (1.0 mm drawn inside fillets, 0.5 mm
  outside corners).  Overall extents are now 77.000 x 151.000 mm.
- J3 (USB-C, GCT USB4105-GF-A-120) moved to (43.000, 147.325) rot 0: its mating face is now
  on the J3 tab edge.
- J2 (microSD, Molex 5025700893) moved to (15.000, 142.700) rot 180: its card entry is now
  on the J2 tab edge.
- SW9 (power slide, C&K JS102011SAQN) moved to (75.200, 86.500): actuator past the east edge.
- Local routing around these three parts only.  Pick-and-place: J2, J3 and SW9 rows change.

Contents:
- Gerbers/: complete Gerber and Excellon data (6 copper layers, PTH and NPTH separate).
- Assembly/: BOM, CPL (fitted and all), DNP list, assembly drawings.
- AQROOT_D805_Fab_Notes.md: fabrication notes (board outline and drawn fillets, via-in-pad
  POFV list, mask dams, plated slots).
- AQROOT_D805_Stackup_Specification.txt: preferred 6-layer construction (unchanged from D-804).
- SHA256SUMS.txt.

Fabrication authority: quote from the supplied files.  Do not cut, shave, re-space, reroute
or otherwise modify copper, solder mask, paste, drill or board-outline geometry without
written approval.  The D-804 open items (post-CAM U9 minimum clearance, stackup
confirmation) still apply.
