"""Build a stepped east-edge expansion: x 72 -> XNEW between y YTOP and YBOT."""
import re, sys, uuid, shutil
from pathlib import Path
SRC=Path(sys.argv[1]); DEST=Path(sys.argv[2])
XNEW=float(sys.argv[3]); YTOP=float(sys.argv[4]); YBOT=float(sys.argv[5])
INSET=0.5
DEST.mkdir(parents=True, exist_ok=True)
shutil.copy(SRC, DEST/'aqroot-Beta-v2.kicad_pcb')
P=Path('/home/aqroot8/aqroot-demo/hardware/demo/kicad/aqroot-demo')
for s in ('kicad_dru','kicad_pro','kicad_prl'):
    shutil.copy(P/('aqroot-Beta-v2.'+s), DEST/('aqroot-Beta-v2.'+s))
bd=DEST/'aqroot-Beta-v2.kicad_pcb'
src=bd.read_text()
# 1. replace the east edge line (72,148)->(72,0) with the stepped chain
old=re.search(r'\t\(gr_line\s*\n\t\t\(start 72 148\)\s*\n\t\t\(end 72 0\)(.*?)\n\t\)\n', src, re.S)
assert old, "east edge not found"
def line(x0,y0,x1,y1):
    return ('\t(gr_line\n\t\t(start %g %g)\n\t\t(end %g %g)\n\t\t(stroke\n\t\t\t(width 0.1)\n\t\t\t(type default)\n\t\t)\n\t\t(layer "Edge.Cuts")\n\t\t(uuid "%s")\n\t)\n'
            % (x0,y0,x1,y1, uuid.uuid5(uuid.NAMESPACE_URL,'aqroot-demo/edge/%g,%g,%g,%g'%(x0,y0,x1,y1))))
chain = (line(72,148,72,YBOT) + line(72,YBOT,XNEW,YBOT) + line(XNEW,YBOT,XNEW,YTOP)
         + line(XNEW,YTOP,72,YTOP) + line(72,YTOP,72,0))
src = src[:old.start()] + chain + src[old.end():]
# 2. grow the full-board pours
oldpts = '(xy 0.5 0.5) (xy 71.5 0.5) (xy 71.5 147.5) (xy 0.5 147.5)'
newpts = ('(xy 0.5 0.5) (xy 71.5 0.5) (xy 71.5 %g) (xy %g %g) (xy %g %g) (xy 71.5 %g) (xy 71.5 147.5)\n\t\t\t\t(xy 0.5 147.5)'
          % (YTOP+INSET, XNEW-INSET, YTOP+INSET, XNEW-INSET, YBOT-INSET, YBOT-INSET))
n = src.count(oldpts)
src = src.replace(oldpts, newpts)
bd.write_text(src)
print('east edge stepped to x=%g between y=%g and y=%g; pours grown: %d' % (XNEW,YTOP,YBOT,n))
