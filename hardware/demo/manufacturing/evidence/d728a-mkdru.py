import sys
s = open(sys.argv[1]).read()
s += '''

# =====================================================================
# 21. D-728 OPTION A - ONE SMALL BARREL FOR `U9.14` `VDD_DR`
#
# `U9`'s north row escapes NORTH only (body and thermal pad are south).
# `U9.13` is `RFO1` and `U9.15` is `RFO2`, both bound EAST; `U9.14` is
# `VDD_DR` and is bound WEST.  `NFC_RF` may not leave `B.Cu` and may not
# carry a via, so BOTH arms must cross `VDD_DR`'s lane and `VDD_DR` must
# cross `RFO1`'s: its barrel can only sit in the channel BETWEEN the two
# arms.  With the arms at the 0.200 mm section 9 already grants inside
# `U9`'s courtyard that channel is 34.350 .. 35.150 mm, so a barrel
# centred at x = 34.750 may be at most 0.400 mm across at the 0.200 mm
# pair clearance section 9 also grants.
#
# FABRICATOR CAPABILITY, from section 10 of this file: JLCPCB's verified
# multilayer minimum via hole is 0.15 mm.  0.400 / 0.150 gives a
# 0.125 mm annular ring - the board's own `min_via_annular_width` - and
# avoids the "0.2 or 0.25 mm hole with a via diameter under 0.45 mm"
# surcharge band entirely.
#
# SCOPE.  ONE net, ONE pad-sized rule area, drawn around the one barrel
# it licenses.  The global via floor is NOT lowered.
# ---------------------------------------------------------------------

(rule "D-728 NFC VDD_DR escape barrel - diameter"
	(constraint via_diameter (min 0.40mm) (opt 0.40mm))
	(condition "A.NetName == '/04_SPI_B_RADIOS_NFC/NFC_VDD_RF' && A.enclosedByArea('NFC_VDD_DR_ESCAPE')"))

(rule "D-728 NFC VDD_DR escape barrel - drill"
	(constraint hole_size (min 0.15mm) (opt 0.15mm))
	(condition "A.NetName == '/04_SPI_B_RADIOS_NFC/NFC_VDD_RF' && A.enclosedByArea('NFC_VDD_DR_ESCAPE')"))

(rule "D-728 NFC VDD_DR escape barrel - annular ring"
	(constraint annular_width (min 0.125mm))
	(condition "A.NetName == '/04_SPI_B_RADIOS_NFC/NFC_VDD_RF' && A.enclosedByArea('NFC_VDD_DR_ESCAPE')"))
'''
open(sys.argv[2],'w').write(s)
