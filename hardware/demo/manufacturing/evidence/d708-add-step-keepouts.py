import sys, uuid
from pathlib import Path
bd = Path(sys.argv[1])
RA = """	(zone
		(net 0)
		(net_name "")
		(layers "F.Cu" "B.Cu" "In1.Cu" "In2.Cu" "In3.Cu" "In4.Cu")
		(uuid "%(uuid)s")
		(name "%(name)s")
		(hatch edge 0.5)
		(connect_pads
			(clearance 0)
		)
		(min_thickness 0.25)
		(keepout
			(tracks not_allowed)
			(vias not_allowed)
			(pads not_allowed)
			(copperpour not_allowed)
			(footprints allowed)
		)
		(placement
			(enabled no)
			(sheetname "")
		)
		(fill
			(thermal_gap 0.5)
			(thermal_bridge_width 0.5)
			(island_removal_mode 0)
		)
		(polygon
			(pts
				%(pts)s
			)
		)
	)
"""
areas = [
    ("STEP_EDGE_KEEPOUT_N", [(71.5,-1.0),(78.0,-1.0),(78.0,71.0),(71.5,71.0)]),
    ("STEP_EDGE_KEEPOUT_S", [(71.5,103.505),(78.0,103.505),(78.0,149.0),(71.5,149.0)]),
    ("STEP_EDGE_KEEPOUT_E", [(76.5,71.0),(78.0,71.0),(78.0,103.505),(76.5,103.505)]),
]
txt = bd.read_text().rstrip()
assert txt.endswith(")")
body = ""
for name, pts in areas:
    body += RA % dict(uuid=uuid.uuid5(uuid.NAMESPACE_URL, "aqroot-demo/ko/"+name),
                      name=name,
                      pts=" ".join("(xy %g %g)" % p for p in pts))
bd.write_text(txt[:-1] + body + ")\n")
print("added", len(areas), "keepouts")
