import pathlib,zipfile,hashlib,json,re,io,csv,subprocess
repo=pathlib.Path('/home/aqroot8/w/d806-jlcpcb')
out=repo/'delivery/vendor-ready-d806';out.mkdir(exist_ok=True)
base=repo/'delivery/AQROOT_D806_JLCPCB_RFQ.zip'
with zipfile.ZipFile(base) as z:
 source={pathlib.PurePosixPath(n).name:z.read(n) for n in z.namelist() if not n.endswith('/')}
fab=source['AQROOT_D806_Fabrication_Notes.md'].decode()
def section(start,end):
 t=fab[fab.index(start):];return t[:t.index(end)] if end else t
def table(t):
 m=re.search(r'(?m)^\|.*(?:\n\|.*)*',t);assert m;return m.group()
stacktable=table(section('## Stackup','## Routed slots'))
viatable=table(section('## Via geometry','## Solder-mask'))
masktable=table(section('## Solder-mask','## NFC first'))
slottable=table(section('## Routed slots','## Component placement'))
pintable=table(section('## PIN-1','## Manufacturer'))
stack="""AQROOT D-806 - PCB stackup
Units: mm. Six copper layers. Nominal order thickness: 1.6 mm.

"""+stacktable+"""
Outer copper: 0.0350 mm; inner copper: 0.0152 mm on all four inner layers.
FR-4 laminate, Tg >=150 C; ENIG finish.
Declared total stack: 1.5744 mm. Existing finished-thickness request: +/-0.10 mm.
Thickness remains unresolved: see Board_Thickness.txt. Please provide the guaranteed
finished-thickness range and proposed layer-by-layer stackup. No substitute stackup
or copper weight is accepted without written approval.
100% bare-board electrical test on every delivered circuit is required.
"""
thickness="""AQROOT D-806 - Finished board thickness

This item remains open and must be resolved before production approval.

The existing thickness request is 1.5744 +/-0.10 mm (1.4744-1.6744 mm).
JLCPCB has stated 1.6 mm +/-10% (1.44-1.76 mm); this wider range has not been accepted.

J6, JST B2B-PH-K-S, is specified for a PCB thickness of 0.8-1.6 mm.
Both the previous requested upper limit and JLCPCB's upper limit exceed 1.6 mm.
Compatibility of the complete enclosure and connectors over either range has
not been established.

Please state the tightest guaranteed finished-thickness range available on the
requested six-layer stackup, including whether an upper limit of 1.60 mm is possible.
Any alternative requires written approval after mechanical review.
"""
notes="""AQROOT D-806 - Fabrication and assembly notes
Revision date: 2026-10-06. Units: mm unless indicated otherwise.
Quotation and process review only; production has not been authorized.

1. Outline and routing
Use aqroot-Demo-board-profile.pdf and its JSON coordinate list. Overall extents:
77 x 151 mm. Main body: 72 x 148 mm. Preserve the two bottom connector tabs,
their R1.0 inside fillets and R0.5 outside corners, and the east step.
No V-scoring. At the two sharp inside step corners, retain a routing fillet
with radius <=1.0 mm. Do not over-cut or add corner relief toward copper.
Nearest copper distances at (72,104.005) and (72,70.500), in the Y-down board
frame, are 0.941 mm and 0.726 mm respectively. Return the actual routing/profile
preview and tool radius for approval.

J2 microSD shell-land clearance to the routed edge is 0.363 mm.
U9 minimum different-net clearance measured in the supplied Gerbers is 6.562 mil.
Board-wide different-net minimum is 5.906 mil. Please confirm the finished
post-CAM U9 clearance remains >=4.0 mil. These are supplied-Gerber measurements,
not measurements of your processed production files.

2. Drills and small vias
Minimum via drill: 0.20 mm. Through vias only.
All 915 vias meet outer diameter >= drill diameter +0.20 mm.
The following smaller via geometries require process confirmation:

"""+viatable+"""

J3 USB-C locating holes: two 0.65 mm NPTH pegs have a 0.1944 mm distance to
their own connector contacts. Please confirm this vendor land pattern.
Clearance from those NPTH pegs to other routed copper is >=0.200 mm.
MK1 microphone acoustic port: 1.05 mm unplated hole concentric with a 1.65 mm
GND land, leaving a 0.30 mm annulus. Do not plate, fill or tent the acoustic port.

3. Filled and capped vias
129 distinct barrels intersect 134 solderable lands across 77 components.
Resin-fill, planarize and copper-cap all listed sites to leave solderable lands.
See Via_In_Pad_Sites.csv. Applying this process to all vias is acceptable.
The microphone acoustic hole is excluded from via filling.

Two optional NFC tuning terminals must also be filled/capped and remain
solderable on B.Mask, with F.Mask tented:
GND vias at (43.500,26.700) and (43.500,33.300), diameter/drill 0.60/0.30.
Their copper-edge gap to C71.2/C72.2 is 0.325 mm. Do not close these B.Mask openings.

4. Solder mask and stencil
Supplied mask expansion is 0.000 mm. Please do not apply a default expansion.
The measured mask openings below need process confirmation:

"""+masktable+"""

USB-C same-net pad pairs and the microphone port-ring opening are intentional.
For U12's different-net 0.120 mm webs, advise whether they can be retained.
Any proposed gang opening or other mask change must be shown for written approval.
Stencil apertures remain separate per pad; do not merge paste apertures.

5. Plated routed slots
Preserve all four Excellon G85 slots as plated slots:

"""+slottable+"""

6. Placement
Use aqroot-Demo-pos-fitted.csv. There are 251 fitted references: 83 top, 168 bottom.
The all-placement file includes DNPs and is not the assembly population list.
X increases right; Y increases upward and is negative across this board.
Rotation is counterclockwise. Bottom-side rotation is viewed from the TOP
through the board (KiCad convention); mirror only if required by your toolchain.
The supplied locator PDFs use a Y-down grid; their reference index lists CPL coordinates.
Return a placement preview for side, rotation and pin-1 approval before assembly.

Use exact approved MPNs. J5: Samtec SSQ-124-02-G-S-RA. U1: ESP32-S3-WROOM-1-N16R8.
Do not fit DNPs or add a header at J4. No accessory reinforcement wire is fitted
between TP12 and J5.3; TP12 and TP25 remain test points.

7. Manual operations and first article
J5 and J6 are post-reflow through-hole operations. D1 TSAL6100 and U6 TSOP38238
require manual optical alignment and lead-forming; the final U6 forming geometry
and enclosure/window alignment are currently under mechanical review.
Do not perform IR forming or final IR installation until a verified assembly
drawing has been issued and approved. Quote these operations separately.

J4 is a manual 26-AWG battery pigtail. See Battery_Harness.json and J4_Work_Instruction.txt.
Inspect the first assembled unit, including X-rays of U11, U9, U12 and the
ESP32 module ground pad, before releasing the remaining assembled unit.

8. Approvals
Provide the proposed stackup, processed production files, routing/panel drawing,
placement preview and any requested deviations for written approval.
Please list any capability limitations, unavailable components or extra charges.
This RFQ does not authorize manufacturing, payment or component procurement.

Pin-1 and polarity reference (CPL coordinates, Y up):

"""+pintable+"\n"
j4="""AQROOT D-806 - J4 battery pigtail work instruction

No PCB connector is fitted at J4. Use 26-AWG red/black conductors and the exact
Molex pre-crimps 2175012101 / 2175011101, housing 5055700201.
Battery-side mating plug: 2137192021; terminal: 2137201000.
Controlling mated-harness rating: 2.6 A at AWG26.
Cavity 1: BAT+ / red / J4.1. Cavity 2: GND / black / J4.2.

Finished plated-hole diameter must be >=0.70 mm (nominal drill 0.75 mm).
Verify one exact tinned conductor passes freely; no force or strand shaving.
Insert from B.Cu; solder, trim, clean and inspect from F.Cu.
Finished conductive profile must be <=0.50 mm above F.Cu, without sharp tips or debris.
If trimming disturbs a joint, rework and remeasure.
Cover both inspected joints with a high-temperature polyimide patch <=0.10 mm thick.
Conductive profile plus insulation must remain <0.80 mm.

Apply DOWSIL 3145 RTV MIL-A-46146 gray only to insulated pigtails on clean B.Cu mask,
beginning beyond inspected solder fillets. Bond at least 8 mm of insulated lead;
retain >=35 mm free wire from the housing before bundling.
Apply/cure at 25 +/-5 C and 40-70% RH, bead <=1.0 mm.
Movement is permitted only after a passed tack-free check and no earlier than 4 h;
do not load the joints. Full cure hold is >=72 h before pull/thermal tests,
enclosure checks or shipment. Keep adhesive and the solder-wick transition clear
of the battery pouch and coax. Disconnect by gripping housings, never the wires.

Verify polarity with a DMM before battery connection. Record conductor/hole fit,
terminal retention, cured strain relief, service loop and first-article thermal rise.
Battery_Harness.json contains the detailed acceptance criteria.
"""
panel="""AQROOT D-806 - Panel and edge rails (proposal for vendor review)

The finished single-board outline must remain as supplied. No V-scoring.
Quote removable assembly rails and return a panel drawing for written approval.
Allow >=2.0 mm clearance to overhanging connectors and SW9.
Do not place breakaway tabs/nubs on the J2/J3 connector tab edges, their fillets,
or the east step face. Keep breakaway tabs >=1.0 mm from copper.

Suggested 1-up frame: 2.0 mm routed gap, west/east conveyor rails 5.0 mm wide,
with north/south bars. East rail inner edge >=X81.0; south bar inner edge >=Y153.0.
Potential west-edge tab centers: Y36,74,101,136; north-edge centers: X15,32.
These positions are proposals only and need vendor copper/component checks.
Do not place tabs beside J5's right-angle overhang.
Add fiducials/tooling holes on rails only.

After depanelization, finish permitted tab remnants flush, with protrusion <=0.10 mm
and no intrusion into the drawn outline. Leave connector edges and the step untouched.
Please propose your tooling, tab positions and depanelization method.
"""
sourcing="""AQROOT D-806 - Component sourcing

Quote exact manufacturer part numbers from the BOM; substitutions require written approval.
Please refresh availability and state unavailable lines, MOQ, attrition and lead time.
The previous JLCPCB stock survey is dated 2026-09-26 and is not current inventory.

Lines previously requiring sourcing attention:
U9 ST25R3916-AQET
U18 LTC4368IMS-1#TRPBF
U19 TLV7032DDFR
U2/U3 PCAL9535APW,118
D2/D4/D5 TPD4E1B06DRLR
L4 74438357010
MK1 DMM-4026-B-I2S-R
J5 SSQ-124-02-G-S-RA
R40 RT0603BRD07189KL (MOQ issue)

If an exact part cannot be sourced, quote customer-consigned placement and list
required quantities/attrition. No parts purchase has been authorized.
Fine-pitch/RF/power parts should be vendor-assembled, including consigned parts.
J5 may be consigned and hand-soldered after reflow. J6, D1/U6 and J4 are manual
operations; IR forming awaits the verified mechanical assembly drawing.
"""
manifest=json.loads((repo/'hardware/demo/fab/MANIFEST.json').read_text())
buf=io.StringIO();w=csv.writer(buf);w.writerow(['Land','Layer','Via_X_mm_Ydown','Via_Y_mm_Ydown','Via_Diameter_mm','Drill_mm','Net'])
for row in manifest['via_in_pad']['lands']:w.writerow([row['land'],row['layer'],row['x'],row['y'],row['via_dia_mm'],row['drill_mm'],row['net']])
keep={
'AQROOT_D806_Assembly_Bottom.pdf':'aqroot-Demo-assembly-bottom.pdf',
'AQROOT_D806_Assembly_Top.pdf':'aqroot-Demo-assembly-top.pdf',
'AQROOT_D806_Board_Profile.json':'aqroot-Demo-board-profile.json',
'AQROOT_D806_Board_Profile.pdf':'aqroot-Demo-board-profile.pdf',
'AQROOT_D806_DNP.csv':'aqroot-Demo-DO-NOT-POPULATE.csv',
'AQROOT_D806_Gerbers.zip':'AQROOT_D806_Gerbers.zip',
'AQROOT_D806_Reference_Index.csv':'aqroot-Demo-assembly-ref-index.csv',
'AQROOT_D806_Reference_Locator_Bottom.pdf':'aqroot-Demo-assembly-locator-bottom.pdf',
'AQROOT_D806_Reference_Locator_Top.pdf':'aqroot-Demo-assembly-locator-top.pdf',
}
for vendor,origin in [('JLCPCB','AQROOT_D806_JLCPCB_RFQ.zip'),('PCBWay','AQROOT_D806_Prototype_PCBA_RFQ.zip')]:
 with zipfile.ZipFile(repo/'delivery'/origin) as z:
  src={pathlib.PurePosixPath(n).name:z.read(n) for n in z.namelist() if not n.endswith('/')}
 files={dst:src[name] for name,dst in keep.items()}
 if vendor=='JLCPCB':
  files['AQROOT_D806_JLCPCB_BOM.csv']=src['AQROOT_D806_JLCPCB_BOM.csv']
  files['aqroot-Demo-pos-fitted.csv']=src['AQROOT_D806_JLCPCB_CPL.csv']
 else:
  files['aqroot-Demo-BOM-assembly.csv']=src['AQROOT_D806_BOM_assembly.csv']
  files['aqroot-Demo-BOM-full.csv']=src['AQROOT_D806_BOM_full.csv']
  files['aqroot-Demo-pos-fitted.csv']=src['AQROOT_D806_CPL.csv']
  files['aqroot-Demo-pos-all.csv']=src['AQROOT_D806_CPL_all_incl_DNP.csv']
 for n,t in [('Fabrication_Assembly_Notes.md',notes),('Stackup.txt',stack),('Board_Thickness.txt',thickness),('Panel_Edge_Rails.txt',panel),('Component_Sourcing.txt',sourcing),('J4_Work_Instruction.txt',j4),('Via_In_Pad_Sites.csv',buf.getvalue())]: files[n]=t.encode()
 files['Battery_Harness.json']=(repo/'hardware/demo/fab/aqroot-Demo-BATTERY-HARNESS.json').read_bytes()
 # Retain names printed in the unchanged drawings and protect fabrication bytes.
 with zipfile.ZipFile(io.BytesIO(files['AQROOT_D806_Gerbers.zip'])) as gz:
  assert gz.testzip() is None
  assert all(not pathlib.PurePosixPath(n).is_absolute() and '..' not in pathlib.PurePosixPath(n).parts for n in gz.namelist())
  assert not any(pathlib.PurePosixPath(n).suffix.lower() in {'.py','.sh','.exe','.js','.bat','.ps1'} for n in gz.namelist())
 files['README.txt']=f"""AQROOT D-806 - {vendor} quotation package
Issued 2026-10-06. Request: 2 assembled PCBAs; quote the required bare-board MOQ separately.

This package replaces D-805 for this quotation. The BOM identities and circuit are unchanged.
Changes: J2 moved inward 0.150 mm (edge clearance 0.363 mm); eight U9 corner lands
shortened 0.030 mm (Gerber clearance 6.562 mil); 35 vias enlarged to 0.40/0.20 mm.
Board outline unchanged. Readable reference locator and dimensioned profile PDFs are included.

Read Fabrication_Assembly_Notes.md, Stackup.txt, Board_Thickness.txt and Panel_Edge_Rails.txt.
Use the fitted placement CSV and BOM; do not fit DNPs.
Board thickness and IR lead-forming/mechanical alignment remain open.
Please quote PCB, parts, assembly/manual operations, tooling, inspection, freight,
lead time and any MOQ/attrition separately.

Please return production files, stackup, panel/routing drawing and placement preview
for written approval before production. No automatic release.
Changes or substitutions require written approval.
Quotation only: fabrication, assembly, payment and component procurement are not authorized.

Board SHA256: 0e59fb64fe72b0a54b9feea96c19bcaec2db52a82a871bcec270e064d7fda547
Files are listed with SHA256 checksums in SHA256SUMS.txt.
""".encode()
 root=f'AQROOT_D806_{vendor}_Submission'
 sums=''.join(f'{hashlib.sha256(data).hexdigest()}  {name}\n' for name,data in sorted(files.items()))
 files['SHA256SUMS.txt']=sums.encode()
 dest=out/(root+'.zip')
 with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  for name,data in sorted(files.items()):
   zi=zipfile.ZipInfo(root+'/'+name,date_time=(2026,10,6,0,0,0));zi.compress_type=zipfile.ZIP_DEFLATED;zi.external_attr=0o100644<<16;z.writestr(zi,data)
 with zipfile.ZipFile(dest) as z:
  assert z.testzip() is None
  for line in sums.splitlines():
   sha,name=line.split('  ',1);assert hashlib.sha256(z.read(root+'/'+name)).hexdigest()==sha
  for name,dst in keep.items():assert z.read(root+'/'+dst)==src[name]
  assert len(z.namelist())==len(set(z.namelist()))
 print(json.dumps({'vendor':vendor,'path':str(dest),'bytes':dest.stat().st_size,'sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'files':len(files),'fabrication_bytes_unchanged':True,'checksums_pass':True}))

