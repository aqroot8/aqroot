# -*- coding: utf-8 -*-
"""D-356: exact U4 address-strap replacement transaction screen.

Scratch only.  Remove the complete accepted BMI270_SDO_ADDR track branch,
apply the D-355 U4 pose, reserve BMI270_INT1_RAW with the proven inner-haul
mechanism, then replay the address strap.  Every unrelated accepted copper
item and every footprint other than U4 is immutable.
"""
import collections, hashlib, json, os, shutil, sys

import pcbnew

SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)
import incremental_router as IR
import path_role_util as RU
import qrouter as QR
import u4_neighbor_eco_056 as D354

OUT = os.path.join(SP, "u4_closed_branch_058.json")
SCRATCH = os.path.join(SP, "w", "U4_CLOSED_BRANCH_058")
PCB = os.path.join(SCRATCH, RU.PCBNAME)
ADDR = "/05_I2C_DEVICES/BMI270_SDO_ADDR"
RAW = "/05_I2C_DEVICES/BMI270_INT1_RAW"
TARGET = (ADDR, RAW)


def sig(t):
    if t.GetClass() == "PCB_VIA":
        p = t.GetPosition()
        return ("V", t.GetNetname(), p.x, p.y, t.GetWidth(pcbnew.F_Cu),
                t.GetDrill(), int(t.GetViaType()))
    a, z = t.GetStart(), t.GetEnd()
    return ("T", t.GetNetname(), t.GetLayerName(),
            tuple(sorted(((a.x, a.y), (z.x, z.y)))), t.GetWidth())


def copper(board):
    return collections.Counter(sig(t) for t in board.GetTracks())


def pref(p):
    return p.GetParentFootprint().GetReference() + "." + p.GetNumber()


def connected_pairs(board):
    board.BuildConnectivity(); cc = board.GetConnectivity(); out = set()
    for f in board.GetFootprints():
        for p in f.Pads():
            for q in cc.GetConnectedItems(p):
                if q.GetClass() == "PAD" and q.GetParentFootprint() != f:
                    out.add(tuple(sorted((pref(p), pref(q)))))
    return out


def open_edges(board, net):
    board.BuildConnectivity(); cc = board.GetConnectivity()
    pads = [p for f in board.GetFootprints() for p in f.Pads()
            if p.GetNetname() == net]
    seen = set(); comps = 0
    for p in pads:
        key = (pref(p), p.GetPosition().x, p.GetPosition().y)
        if key in seen:
            continue
        comps += 1
        reached = {(pref(q), q.GetPosition().x, q.GetPosition().y)
                   for q in cc.GetConnectedItems(p) if q.GetClass() == "PAD"}
        seen |= reached | {key}
    return max(0, comps - 1)


def route_addr(qb):
    group = IR.GROUPS["IMU_ADDR"]
    nf = IR.resolve_nets(qb, group)[group["nets"][0]]
    pads = IR.physical_net_pads(qb, nf)
    pads.sort(key=lambda p: (p["ref"], p["x"], p["y"]))
    rows = []
    for i, j in IR.mst_edges(pads):
        a, b = pads[i], pads[j]
        r = QR.connect_role(qb, nf, a, b, "B", group["width"],
                            group["clr_pad"], group["clr_trk"])
        rows.append({"a": a["ref"], "b": b["ref"],
                     "ok": bool(r.get("ok")), "reason": r.get("reason")})
        if not r.get("ok"):
            break
    return rows


def main():
    if os.path.exists(SCRATCH):
        shutil.rmtree(SCRATCH)
    os.makedirs(SCRATCH); shutil.copyfile(IR.AUTH, PCB)
    stem = os.path.splitext(RU.PCBNAME)[0]
    for name in (stem + ".kicad_dru", stem + ".kicad_pro", "fp-lib-table", "sym-lib-table"):
        src = os.path.join(RU.AUTH_DIR, name)
        if os.path.exists(src):
            shutil.copyfile(src, os.path.join(SCRATCH, name))
    libs = os.path.join(RU.AUTH_DIR, "libraries")
    if os.path.isdir(libs):
        os.symlink(libs, os.path.join(SCRATCH, "libraries"), target_is_directory=True)

    auth_sha = hashlib.sha256(open(IR.AUTH, "rb").read()).hexdigest()
    base = pcbnew.LoadBoard(IR.AUTH); base_cu = copper(base)
    base_pairs = connected_pairs(base)
    base_drc, _ = RU.drc(IR.AUTH, "u4closed_base", SCRATCH)
    allowed = collections.Counter(s for s in base_cu.elements()
                                  if s[0] == "T" and s[1] == ADDR)

    board = pcbnew.LoadBoard(PCB); removed = collections.Counter()
    for t in list(board.GetTracks()):
        s = sig(t)
        if allowed[s] > removed[s]:
            removed[s] += 1; board.RemoveNative(t)
    u4 = board.FindFootprintByReference("U4"); p = u4.GetPosition()
    u4.SetOrientationDegrees(u4.GetOrientationDegrees() + 270)
    u4.SetPosition(pcbnew.VECTOR2I(p.x + 500000, p.y))
    board.Save(PCB)

    raw = D354.route_raw(PCB)
    qb = QR.QBoard(PCB); IR.inject_existing_via_obstacles(qb)
    addr = route_addr(qb)
    # The RAW inner haul adds two through vias.  Refill both GND reference
    # planes before real DRC so stale pre-transaction zone polygons cannot
    # masquerade as via-to-zone shorts.
    IR.refill_planes(qb.b)
    qb.save(PCB)

    result = pcbnew.LoadBoard(PCB); result_cu = copper(result)
    missing, added = base_cu - result_cu, result_cu - base_cu
    forbidden_missing = missing - allowed
    forbidden_added = [s for s in added.elements() if s[1] not in TARGET]
    broken = sorted(base_pairs - connected_pairs(result))
    opens = {n: open_edges(result, n) for n in TARGET}
    drc, _ = RU.drc(PCB, "u4closed_result", SCRATCH)
    worse = {k: [base_drc.get(k, 0), drc.get(k, 0)]
             for k in sorted(set(base_drc) | set(drc))
             if k != "unconnected_items" and drc.get(k, 0) > base_drc.get(k, 0)}
    passed = (removed == allowed and raw.get("ok") and addr
              and all(r["ok"] for r in addr) and not forbidden_missing
              and not forbidden_added and not broken
              and all(v == 0 for v in opens.values()) and not worse
              and drc.get("unconnected_items", 0) <= base_drc.get("unconnected_items", 0))
    ev = {"schema_version": 1, "decision": "D-356",
          "authoritative_board_sha256": auth_sha,
          "authoritative_unchanged": hashlib.sha256(open(IR.AUTH, "rb").read()).hexdigest() == auth_sha,
          "pose": {"rotation_deg": 270, "offset_mm": [0.5, 0]},
          "replacement_boundary": "complete_BMI270_SDO_ADDR_track_branch",
          "allowed_replacement_items": sum(allowed.values()),
          "removed_items": sum(removed.values()), "raw_route": raw,
          "address_routes": addr, "missing_items_total": sum(missing.values()),
          "added_items_total": sum(added.values()),
          "forbidden_missing_count": sum(forbidden_missing.values()),
          "forbidden_added_count": len(forbidden_added),
          "accepted_pairs_broken": broken, "open_edges_after": opens,
          "drc_before": dict(base_drc), "drc_after": dict(drc),
          "drc_worse": worse, "transaction_candidate": bool(passed),
          "promotion_candidate": False,
          "promotion_blocker": ("replacement_aware_authoritative_full_board_gate_not_yet_executed"
                                if passed else "transaction_screen_failed"),
          "conclusion": ("closed_U4_transaction_candidate" if passed
                         else "U4_closed_branch_replacement_failed")}
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(ev, f, indent=2, sort_keys=True)
    print(json.dumps(ev, indent=2, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
