#!/usr/bin/env python3
"""D-802 / Round-21: reproduce every R21 FAP-01 witness BEFORE and AFTER.

    python3 hardware/demo/manufacturing/evidence/d802-round21-witnesses.py \
        --before <checkout of e54adcc3> [-o evidence/d802-round21-witnesses.json]

Each probe is Astra's Round-21 reproduction (the forensic bundle under
/tmp/aqroot-forensic-d801-e54adcc3/), appended to the RELEASED
`test_fap01_image.cpp` as a second `main()` and compiled against the tree
under test with the same flags H6 uses:

  R21-01  N, then read IO configuration 2 (01h) bit 7 sup3V from the model,
          and whether any `en` / Adjust regulators ran in the 5 V mode;
  R21-02  V W, then each of I x d C L N A t 3 5 p B, and whether the key ran
          beside the waived Wi-Fi radio;
  R21-03  N, then T with an all-FF bus, an all-zero bus, and a stale FIFO
          count of 2 with writes ignored -- and whether "a tag answered" was
          printed.

The BEFORE tree predates `AQROOT_TEST_NFC_SUPPLY_3V3`; the define is passed
to both and is inert where unused.  R21-04 / R21-05 are document-scanner
witnesses and are reproduced inside `demo_feature_contract.py` itself
(`round21_rins_semantics.witnesses`, `pass_pair.publication.controls
d802_05*`).
"""
import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]

PROBES = {
    "R21-01_sup3v": r'''
int main() {
  coldBoot(); keys("N");
  bool sup3v = (g_radio->nfc_regs[1] & 0x80) != 0;
  std::printf("op=0x%02X io_conf2=0x%02X sup3v=%d field=%d\n",
              (unsigned)g_radio->nfc_operation_control,
              (unsigned)g_radio->nfc_regs[1], sup3v, g_radio->nfcFieldIsUp());
  return 0;
}
''',
    "R21-02_wifi_session": r'''
int main() {
  const char *nexts[] = {"I","x","d","C","L","N","A","t","3","5","p","B"};
  for (auto next : nexts) {
    coldBoot(); keys("VW");
    auto pwm = rec().pwm.size(); auto mark = rec().console.size();
    keys(next);
    bool ran = rec().pwm.size() != pwm || rail3() || rail5() ||
               g_radio->transmitting || g_radio->tx_cw ||
               g_radio->nfcFieldIsUp() || hasFrom("IR ", mark) ||
               hasFrom("microSD  CMD0", mark) || hasFrom("display: pulsing", mark);
    bool refused_by_session = hasFrom("the Wi-Fi burst session is EXCLUSIVE", mark);
    std::printf("SEQ=VW%s wifi=%d ran_beside_wifi=%d refused_by_session=%d\n",
                next, aqroot_hal::wifi().current_mode, ran, refused_by_session);
    keys("Q");
  }
  return 0;
}
''',
    "R21-03_reqa": r'''
int main() {
  const char *names[] = {"all_ff", "all_zero", "stale_count_writes_ignored"};
  for (int fault = 0; fault < 3; ++fault) {
    coldBoot(); keys("N");
    if (fault == 0) g_radio->nfc_ff_fill = true;
    if (fault == 1) g_radio->nfc_zero_fill = true;
    if (fault == 2) { g_radio->nfc_regs[0x1E] = 2; g_radio->nfc_ignores_writes = true; }
    auto mark = rec().console.size(); keys("T");
    std::printf("CASE=%s tag_claimed=%d\n", names[fault],
                hasFrom("a tag answered", mark));
    for (size_t i = mark; i < rec().console.size(); ++i)
      if (rec().console[i].find("REQA") != std::string::npos)
        std::printf("  %s", rec().console[i].c_str());
    g_radio->nfc_ff_fill = g_radio->nfc_zero_fill = false;
    g_radio->nfc_ignores_writes = false;
  }
  return 0;
}
''',
}


def run(tree, name, body):
    fw = tree / "Firmware"
    text = (fw / "test/test_fap01_image.cpp").read_text(encoding="utf-8")
    text = text.replace("int main() {", "int released_test_main() {", 1) + body
    with tempfile.TemporaryDirectory(prefix="d802-witness-") as tmp:
        src = Path(tmp) / "probe.cpp"
        exe = Path(tmp) / "probe"
        src.write_text(text, encoding="utf-8")
        cmd = ["g++", "-std=c++17", "-DARDUINO=200", "-DAQROOT_FAP01_DIAGNOSTIC",
               "-DAQROOT_TEST_EXPECT_FAP01", "-DAQROOT_TEST_NFC_SUPPLY_3V3=1",
               "-I", str(fw / "test/image"), "-I", str(fw / "src/hw"),
               "-I", str(fw / "src"), "-I", str(fw / "src/fap01"), str(src),
               str(fw / "src/demo/main.cpp"),
               str(fw / "src/fap01/aqroot_fap01.cpp"),
               str(fw / "test/image/image_main.cpp"), "-o", str(exe)]
        build = subprocess.run(cmd, capture_output=True, text=True)
        if build.returncode != 0:
            return dict(compiled=False, stderr=build.stderr[-1500:])
        out = subprocess.run([str(exe)], capture_output=True, text=True,
                             timeout=600)
        return dict(compiled=True, exit=out.returncode, stdout=out.stdout)


def git_sha(tree):
    return subprocess.run(["git", "-C", str(tree), "rev-parse", "HEAD"],
                          capture_output=True, text=True).stdout.strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--before", type=Path, required=True)
    ap.add_argument("-o", dest="out", type=Path)
    args = ap.parse_args()
    report = dict(schema=1, decision="D-802",
                  before=dict(tree=str(args.before), git_sha=git_sha(args.before)),
                  after=dict(tree="working tree", git_sha_parent=git_sha(ROOT)),
                  probes={})
    for name, body in PROBES.items():
        report["probes"][name] = dict(before=run(args.before, name, body),
                                      after=run(ROOT, name, body))
    text = json.dumps(report, indent=1, sort_keys=True)
    if args.out:
        args.out.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
