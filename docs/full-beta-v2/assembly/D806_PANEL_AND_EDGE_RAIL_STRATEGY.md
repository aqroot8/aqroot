# D-806 — PANEL / EDGE-RAIL STRATEGY FOR STANDARD PCBA (PROPOSAL, VENDOR + OWNER APPROVAL REQUIRED)

JLCPCB Standard PCBA needs conveyor edge rails.  D-806 treats this as a **manufacturing process
item**: the delivered single-board Gerbers are NOT changed, and **the finished board after
depanelization must be exactly the profile in `aqroot-Demo-board-profile.pdf` /
`aqroot-Demo-board-profile.json`** (77.000 x 151.000 mm bbox, two bottom tabs, east step).
The ESP32-S3-WROOM-1-N16R8 is kept exactly; nothing is redesigned to qualify for Economic PCBA.

## Constraints the panel must respect (from the board)

* **NO V-SCORE ON ANY EDGE.**  The outline is routed only.  JLCPCB's own 0.25 mm J2 figure is
  for a non-V-cut edge, and V-score cannot follow the tabs, the drawn fillets or the east step.
* Parts at or beyond the outline: `J3` USB-C mating face flush with the J3 tab edge (Y 151.000);
  `J2` card entry 0.150 mm inside the J2 tab edge; `SW9` actuator to X 79.000 (2.0 mm past the
  X 77.000 step face); `J5` body to X 72.975 along Y 7.9–70.5 (mating face 0.43 mm past the X 72.000 edge).  The panel
  frame must clear each by >= 2.0 mm.
* The tab edges (Y 151.000) sit 0.5 mm from the enclosure cavity wall: **no breakaway tab or
  residual nub is allowed on either tab edge, on the drawn fillets, or on the east step face
  (X 77.000)**.  Elsewhere the board has 1.5 mm to the wall.
* Shell lands, slots and copper: keep every breakaway tab >= 1.0 mm from copper.

## Proposed construction (1-up, vendor to confirm or counter-propose)

1. Routed frame: **2.0 mm routed gap** around the whole board; **5.0 mm rails** on the WEST and
   EAST sides (conveyor along Y); north and south frame bars join the rails.  East rail inner edge
   at X >= 81.0 (2.0 mm clear of the SW9 actuator tip); south bar inner edge at Y >= 153.0.
2. **Mouse-bite breakaway tabs** (e.g. 3.0 mm wide, 5 x Ø0.5 mm perforations) ONLY in spans
   with no footprint within 2 mm of the edge, measured from the D-806 board's footprint extents:
   * west edge X 0.000: free spans Y 0–7.5, 30.2–41.6, 69.0–78.8, 95.0–107.7, 124.0–148.0 —
     proposed tabs at Y ≈ 36, 74, 101, 136 (parts sit 0.62 mm from this edge elsewhere);
   * north edge Y 0.000: free spans X 0–40.4 and 49.3–57.7 — proposed tabs at X ≈ 15, 32;
   * **no tab on X 72.000 north of the step**: `J5` occupies Y 7.9–70.5 and overhangs to X 72.975;
   * main bottom edge Y 148.000 between/beside the connector tabs only if the vendor needs a
     south tab (X ≈ 30 or 62), subject to the vendor's copper check.
   Final positions to be checked by the vendor against copper and returned for approval.
3. Fiducials (3) and tooling holes (4 x Ø1.152 mm or the vendor's standard) on the rails only.
4. **Depanelization:** break or rout the tabs, then sand/route the nubs **flush with the drawn
   outline: no residual protrusion > 0.10 mm and no intrusion into the outline.**  Verify the J2
   and J3 tab edges and the east step are untouched.
5. The panel drawing is part of **production-file confirmation** and needs written approval
   before fabrication.  If the vendor's process cannot meet the above with removable rails, that
   is a STOP: D-806 does not redesign the functional outline.
