#!/usr/bin/env python3
"""D-681: collect this decision's runs into tracked evidence.  Reads the runs'
own JSON; transcribes nothing."""
import hashlib, json
from pathlib import Path
HERE = Path("/home/aqroot8/aqroot-demo/hardware/demo/manufacturing")
W = HERE / "w/d681"
BOARD = HERE.parent / "kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb"


def read(p):
    p = Path(p)
    return json.loads(p.read_text()) if p.is_file() else None


def arm(path, why, keys=("refused_clauses", "connectivity", "drc_types")):
    d = read(path)
    if d is None:
        return dict(run=str(path), why=why, ran=False)
    out = dict(run=str(Path(path).relative_to(HERE)), why=why, ran=True)
    for k in keys:
        out[k] = d.get(k)
    out["attributable_drc"] = [v.get("type") for v in (d.get("attributable_drc") or [])]
    out["routed"] = [dict(net=r.get("net"), ok=r.get("ok"), mm=r.get("mm"),
                          vias=r.get("vias"), closed=r.get("closed"),
                          remaining=r.get("remaining"),
                          failures=[f.get("reason") for f in (r.get("failures") or [])])
                     for r in (d.get("routed") or [])]
    det = d.get("detour")
    if det:
        out["detour"] = dict(all_relaid=det.get("all_relaid"),
                             relaid=[[r.get("mm"), r.get("vias")]
                                     for r in (det.get("relaid") or [])],
                             failed=[f.get("reason") for f in (det.get("failed") or [])])
    return out


out = dict(
    schema=1, decision="D-681",
    board=str(BOARD),
    board_sha256=hashlib.sha256(BOARD.read_bytes()).hexdigest(),
    question=("three subjects: (1) the OWNER-APPROVED D-670 / D-655 "
              "/I2C_SCL_INT U14.7 <-> J1.44 transaction, (2) the U21 accessory "
              "boost pocket, (3) the USB data pair and the In2-pierce ruling"),
    i2c_scl_int=[
        arm(W / "i2c/run1.json", "barrel removed, eviction window 0.025 mm too small: removed_count 0"),
        arm(W / "i2c/run2.json", "eviction window corrected; barrel KEPT; 25 -> 24, dangling feeder + 2 slivers"),
        arm(W / "i2c/run3.json", "window widened by the feeder stub; the dangle unrolls one link further"),
        arm(W / "i2c/run4.json", "RELAY form: one object moves, nothing stranded -- but TP19.1 was a MID-POINT TAP and orphaned"),
        arm(W / "i2c/run5.json", "relay + BAT requested so TP19.1 is re-tapped: refused ONLY on 2 copper_sliver"),
        arm(W / "i2c/run6.json", "the sliver diagonal reserved: refused_clauses []"),
        arm(W / "i2c/promote.json", "the authoritative promotion run"),
    ],
    boost_pocket=[
        arm(W / "lx1/run1.json", "C65 to (60.700,42.200) + the U21.4 GND diagonal removed by --detour-spec: LX ROUTES 3.529 mm 0 vias, FIRST TIME EVER"),
        arm(W / "lx1/run2.json", "the same removal RELAID around a reserved LX lane: NO_PATH at 0.300 mm"),
        arm(W / "lx1/run3.json", "U21.4's escape released by the placement transaction + --bond-pad U21.4: PP1-PP4 ALL TRUE, but the 3.842 mm bond track took the LX lane"),
        arm(W / "lx1/run4.json", "--bond-max-mm 1.2: NO_VIA_SITE, and ACC_5V_RAW came back at 75.995 mm"),
        arm(W / "lx1/run5.json", "GND column reserved, --tap-first: LX 3.275 mm, RAW 0 mm by TAP, U21.4 STILL a 0.175 mm2 STRANDED fragment"),
        arm(W / "lx2/run1.json", "the /ACC_DETECT_N channel chain RELAID out of U21's inter-column channel (5.866 mm, 0 vias) + --repair-planes + --join-islands: the channel is clear, U21.4 is STILL STRANDED at 0.279 mm2, and r 0.45 discs over the west 0.075 mm of U21.4/U21.5's own lands cost both nets their licensed neck"),
    ],
    usb=[
        arm(W / "usb/run1.json", "the three USB data edges on the authority: all three NO_PATH at 0.250 mm"),
        arm(W / "usb/run2.json", "D- evicted whole and re-laid: D+ still NO_PATH"),
        arm(W / "usb/run3.json", "+ the I2S_LRCLK relay: D+ ROUTES 10.709 mm 0 vias, and D- then has NO LEGAL ESCAPE from J3.B7"),
        arm(W / "usb/run4.json", "D- first, the I2S chain extended barrel-to-barrel: D- 11.231 mm, D+ NO_PATH"),
        arm(W / "usbmcu/run1.json", "the D-681 In2 RULING on a scratch .kicad_dru: USB_D_MCU_P ROUTES 33.432 mm with 4 vias where it was NO_PATH"),
        arm(W / "usbmcu/run2.json", "the same at 0.025 mm: 35.477 mm, MCU_N still NO_PATH"),
        arm(W / "usbmcu/conn1.json", "the connector half under the same ruling: still NO_PATH -- the J3 fanout is not a layer question"),
    ],
    blame=dict(
        usb_conn_p=read(W / "usb/blame-connp.json") and
        {k: read(W / "usb/blame-connp.json")[k]
         for k in ("net", "a", "b", "layers", "window_nets", "complete")},
        usb_conn_p_minimal=[r for r in (read(W / "usb/blame-connp.json") or {}).get("rows", [])
                            if r.get("step") in ("Q1_UPPER_BOUND", "Q3_MINIMAL_SET",
                                                 "Q4_MINIMAL_OBJECTS")],
        usb_conn_p_ban_partner=[r for r in (read(W / "usb/blame-connp-banN.json") or {}).get("rows", [])],
        usb_mcu_n=[r for r in (read(W / "usbmcu/blame-mcun.json") or {}).get("rows", [])
                   if r.get("step") == "Q1_UPPER_BOUND" or r.get("accepted")],
    ),
    sliver_bisect=dict(
        method=("per-OBJECT removal, refill and REAL kicad-cli DRC, 8.6 s a probe, "
                "over all 40 objects the I2C transaction lays"),
        log="w/d681/i2c/sliv2.log",
        source_object=["trk", "/I2C_SCL_INT", "B.Cu", 56.25, 130.45, 60.20, 136.15, 0.20],
        slivers_with_it=2, slivers_without_it=0,
        others_probed=17, others_that_moved_the_count=0),
)
Path(HERE / "evidence/d681-runs.json").write_text(json.dumps(out, indent=1) + "\n",
                                                  encoding="utf-8")
print(json.dumps([[a.get("run"), a.get("refused_clauses")]
                  for a in out["i2c_scl_int"]], indent=1))
