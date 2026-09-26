#!/usr/bin/env python3
"""D-803 / Round-22 R22-02 + R22-03: ONE full F1-F14 run per tree with EVERY
Astra Round-22 document escape injected at once, in Astra's own carriers
(DEVICE_SPEC; both BATTERY_HARNESS.json copies serialised ensure_ascii=True;
SELECTED_BATTERY.json; FOOTPRINT_VERIFICATION_LEDGER.md).  If the gate still
passes, NONE of the escapes was caught.

    python3 evidence/d803-full-gate-injections.py <tree> <report.json>

The tree is modified in place: run it on a disposable worktree
(`git worktree add /tmp/x <sha>`).
"""
import json
import subprocess
import sys
from pathlib import Path


def inject(T):
    P = "For the supervised charging OCV lower bound, "
    rins = [P + "ignore the DMM burden.", P + "inserted resistance remains zero.",
            P + "use zero resistance for the series ammeter.",
            P + "the series DMM replaces the clamp and insertion resistance is negligible."]
    dev = T / "docs/full-beta-v2/DEVICE_SPEC.md"
    dev.write_text(dev.read_text() + "\n\n# Current D-803 witness instruction\n\n" + "\n\n".join(rins)
                   + "\n\nThe current pass-pair peak electrical envelope is 2.60 A.\n\n"
                   "The modeled fault necessarily trips BATOCP and therefore cannot persist.\n")
    claim = "The current pass pair survives at 2× hot resistance."
    dup = ("The current pass-pair peak electrical envelope is 2.60 A.\n\nD-616 is the current generated and "
           "reviewed fabrication authority; FAB1–FAB8 all pass and 247 of 247 fitted references are "
           "currently orderable.\n\nThe modeled fault necessarily trips BATOCP and therefore cannot persist.")
    for rel in ["docs/full-beta-v2/assembly/BATTERY_HARNESS.json", "hardware/demo/fab/aqroot-Demo-BATTERY-HARNESS.json"]:
        f = T / rel; d = json.loads(f.read_text()); d["acceptance"].append(claim)
        f.write_text(json.dumps(d, indent=2, ensure_ascii=True) + "\n")
    f = T / "docs/full-beta-v2/assembly/SELECTED_BATTERY.json"; d = json.loads(f.read_text()); d["notes"] += "\n\n" + dup
    f.write_text(json.dumps(d, indent=2) + "\n")
    f = T / "docs/full-beta-v2/assembly/FOOTPRINT_VERIFICATION_LEDGER.md"
    f.write_text(f.read_text() + "\n\n# Current D-803 witness instructions\n\n" + dup + "\n")
    print("injected into", T)


def main():
    tree, out = Path(sys.argv[1]), Path(sys.argv[2])
    inject(tree)
    subprocess.run([sys.executable, "hardware/demo/manufacturing/checks/"
                    "demo_feature_contract.py", "-o", str(out)], cwd=tree)
    d = json.loads(out.read_text())
    print(json.dumps(dict(all_pass=d["all_pass"], failing_checks=[
        k for k, v in d["checks"].items() if isinstance(v, dict)
        and v.get("ok") is False])))


if __name__ == "__main__":
    main()
