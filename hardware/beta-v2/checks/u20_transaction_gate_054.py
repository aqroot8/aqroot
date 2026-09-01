# -*- coding: utf-8 -*-
"""D-352: replacement-aware authoritative gate for the D-351 U20 transaction.

This is deliberately promotion-free.  It regenerates the D-351 candidate from
the committed authoritative PCB, then proves that the only permitted mutation
is the complete ACC_3V3_EN/ACC_3V3_ILIM track-branch replacement plus U20's
declared pose change.  All other copper and footprint poses are immutable.
"""
import collections, hashlib, json, os, subprocess, sys

import pcbnew

SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)
import incremental_router as IR
import path_role_util as RU
import u20_closed_branch_053 as D351

OUT = os.path.join(SP, "u20_transaction_gate_054.json")
CONTROL = D351.CONTROL
TARGET = D351.TARGET


def sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def pose(fp):
    p = fp.GetPosition()
    return (p.x, p.y, round(fp.GetOrientationDegrees(), 6), fp.GetLayerName())


def main():
    auth_sha = sha(IR.AUTH)
    run = subprocess.run([sys.executable, D351.__file__], text=True,
                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    candidate = D351.PCB
    d351 = json.load(open(D351.OUT, encoding="utf-8"))
    failures = []

    def chk(name, ok, detail):
        print("  %s %-48s %s" % ("PASS" if ok else "FAIL", name, detail))
        if not ok:
            failures.append(name)

    chk("D-351 candidate regenerated", run.returncode == 0 and d351.get("transaction_candidate"),
        "return=%d transaction_candidate=%s" % (run.returncode, d351.get("transaction_candidate")))
    chk("authoritative PCB remained byte-identical", sha(IR.AUTH) == auth_sha, auth_sha)
    if failures:
        json.dump({"schema_version": 1, "decision": "D-352", "verdict": "FAIL",
                   "failures": failures, "d351_output": run.stdout[-4000:]},
                  open(OUT, "w", encoding="utf-8"), indent=2, sort_keys=True)
        return 1

    ab = pcbnew.LoadBoard(IR.AUTH)
    rb = pcbnew.LoadBoard(candidate)
    ab.BuildConnectivity(); rb.BuildConnectivity()
    ac, rc = D351.copper(ab), D351.copper(rb)
    missing, added = ac - rc, rc - ac
    allowed = collections.Counter(s for s in ac.elements()
                                  if s[0] == "T" and s[1] in CONTROL)
    chk("missing copper is within declared boundary", not (missing - allowed),
        "missing=%d forbidden=%d allowed=%d" %
        (sum(missing.values()), sum((missing - allowed).values()), sum(allowed.values())))
    chk("replacement boundary was exercised completely", sum(missing.values()) > 0,
        "missing=%d" % sum(missing.values()))
    forbidden_added = [s for s in added.elements() if s[1] not in TARGET]
    chk("all added copper belongs to transaction nets", not forbidden_added,
        "added=%d forbidden=%d" % (sum(added.values()), len(forbidden_added)))

    ap = {f.GetReference(): pose(f) for f in ab.GetFootprints()}
    rp = {f.GetReference(): pose(f) for f in rb.GetFootprints()}
    moved = {r: (ap.get(r), rp.get(r)) for r in sorted(set(ap) | set(rp))
             if ap.get(r) != rp.get(r)}
    u0, u1 = ap["U20"], rp["U20"]
    expected_u20 = (u0[0], u0[1] + 500000, round((u0[2] + 180) % 360, 6), u0[3])
    chk("only U20 placement changed", set(moved) == {"U20"}, "moved=%s" % sorted(moved))
    chk("U20 pose delta is exactly 180deg/+0.5mm Y", u1 == expected_u20,
        "before=%s after=%s expected=%s" % (u0, u1, expected_u20))

    broken = sorted(D351.connected_pairs(ab) - D351.connected_pairs(rb))
    opens = {n: D351.open_edges(rb, n) for n in TARGET}
    chk("no baseline pad connectivity regressed", not broken, "broken=%d" % len(broken))
    chk("all transaction nets are fully connected", all(v == 0 for v in opens.values()), str(opens))
    rats0 = ab.GetConnectivity().GetUnconnectedCount(True)
    rats1 = rb.GetConnectivity().GetUnconnectedCount(True)
    chk("full-board ratsnest strictly decreased", rats1 < rats0, "%d -> %d" % (rats0, rats1))

    drc0, _ = RU.drc(IR.AUTH, "u20txn_base", D351.SCRATCH)
    drc1, _ = RU.drc(candidate, "u20txn_candidate", D351.SCRATCH)
    worse = {k: [drc0.get(k, 0), drc1.get(k, 0)]
             for k in sorted(set(drc0) | set(drc1))
             if k != "unconnected_items" and drc1.get(k, 0) > drc0.get(k, 0)}
    chk("real KiCad DRC has no new/worse class", not worse, str(worse))
    chk("DRC unconnected_items did not increase",
        drc1.get("unconnected_items", 0) <= drc0.get("unconnected_items", 0),
        "%d -> %d" % (drc0.get("unconnected_items", 0), drc1.get("unconnected_items", 0)))

    verdict = "PASS" if not failures else "FAIL"
    ev = {"schema_version": 1, "decision": "D-352", "verdict": verdict,
          "promotion_performed": False, "authoritative_board_sha256": auth_sha,
          "candidate_board_sha256": sha(candidate), "allowed_replacement_items": sum(allowed.values()),
          "missing_items": sum(missing.values()), "added_items": sum(added.values()),
          "moved_footprints": moved, "open_edges_after": opens,
          "ratsnest_before": rats0, "ratsnest_after": rats1,
          "drc_before": dict(drc0), "drc_after": dict(drc1), "drc_worse": worse,
          "failures": failures,
          "next": "atomic promotion plus accepted-copper/journal/fingerprint/probe contract re-pin"}
    json.dump(ev, open(OUT, "w", encoding="utf-8"), indent=2, sort_keys=True)
    print("D-352 TRANSACTION GATE: %s" % verdict)
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
