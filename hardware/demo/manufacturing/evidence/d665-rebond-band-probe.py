import sys, json, math
from pathlib import Path
HERE = Path('/home/aqroot8/aqroot-demo/hardware/demo/manufacturing')
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[2] / "hardware/beta-v2/checks"))
import screen_rebond_site as S
import qrouter as qr, incremental_router as ir, maze3d as mz, pcbnew
from route_maze_batch import net_contract, reserved_inner_planes, permitted_layers
BOARD = str(HERE.parents[2] / "hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb")
qb = qr.QBoard(BOARD); ir.inject_existing_via_obstacles(qb)
pad = S.pad_of(qb.b, "U2.3")
p0 = pad.GetPosition(); isl = S.island_of(qb.b, "GND", p0.x, p0.y)
print("island", {k: v for k, v in isl.items() if k != "poly"}, file=sys.stderr)
reserved = reserved_inner_planes(qb.b)
base = net_contract(qb.b, "GND")
far = list(permitted_layers(qb.routable, base["layers"], reserved, "GND"))
G = 25000
field = mz.Field(qb, "GND", base["width"], base["clr_pad"], base["clr"],
                 500000, 250000, G=G, layers=far)
# corridor: segment (53.0,91.45) -> (53.85,82.2) plus the U2.1 B escape
A = (53.0, 91.45); B = (53.85, 82.2)
def dseg(px, py, a, b):
    ax, ay = a; bx, by = b
    dx, dy = bx-ax, by-ay
    t = max(0.0, min(1.0, ((px-ax)*dx + (py-ay)*dy) / (dx*dx+dy*dy)))
    return math.hypot(px-(ax+t*dx), py-(ay+t*dy))
sites = []
for j in range(field.ny):
    y = field.oy + j*G
    row = field.via_ok[j]
    for i in range(field.nx):
        x = field.ox + i*G
        if not row[i]: continue
        if not isl["poly"].Contains(pcbnew.VECTOR2I(int(x), int(y))): continue
        xm, ym = x/1e6, y/1e6
        d = min(dseg(xm, ym, A, B), dseg(xm, ym, (54.1375,91.575), (52.95,91.6)))
        sites.append((round(d,3), round(xm,4), round(ym,4)))
sites.sort(reverse=True)
print("n sites", len(sites))
for s in sites[:25]: print(s)
