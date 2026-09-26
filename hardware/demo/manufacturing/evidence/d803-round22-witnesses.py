#!/usr/bin/env python3
"""D-803 / Round-22: reproduce the R22-01, R22-04 and R22-05 witnesses BEFORE
and AFTER (R22-01 the FAP-01 REQA; R22-04 H9's PlatformIO authority; R22-05
the hold-off operator wording against its behaviour).

    python3 hardware/demo/manufacturing/evidence/d803-round22-witnesses.py \
        --before <checkout of d6f67692> [-o evidence/d803-round22-witnesses.json]

Astra R22-01: stale or dead SPI evidence still became an affirmative ("a tag
answered") or a false-negative ("no tag answered") REQA verdict on D-802.
The probe is appended to THIS tree's `test_fap01_image.cpp` as a second
`main()` and uses THIS tree's host model (which carries the D-803 byte-window
failure hooks); only the FIRMWARE sources (`src/demo`, `src/fap01`, `src/hw`)
come from the tree under test.  So BEFORE is D-802's firmware judged by the
D-803 model and AFTER is the working tree's firmware judged by the same one.

Families (each swept over EVERY byte U9 clocks during one T):

  persistent   U9 stops answering from byte k onward (lost MISO or deaf part,
               0x00 or 0xFF fill), tag present and tag absent.  ANY verdict
               ("a tag answered" / "no tag answered") trusts a dead bus.
  recovered    U9 fails for bytes [k, k+w), every w in 1..48, then
               answers again.  A verdict that contradicts the truth -- an
               answer with no tag, "no tag" with a tag, or an ATQA other than
               the tag's -- is a defect.  Run with an instant and a DELAYED
               end of receive (I_rxe two IRQ reads after I_txe).
  stale        a stale I_rxe and a stale two-byte FIFO from before the REQA,
               no tag, and the part deaf across the fresh boundary.
  error_rank   a receive that raised an error (I_col / I_err1 / I_par /
               fifo_ovr / fifo_unf / I_rxs) but no I_rxe and an empty FIFO:
               "no tag answered" is a defect -- the error outranks it.
  healthy      a tag (instant and delayed I_rxe) -> VALID ANSWER 04 00; no
               tag -> "no tag answered".  These must keep passing.
"""
import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]

PROBE = r'''
namespace {
struct Verdict { bool answer, notag, nve; std::string atqa; };
Verdict runT(size_t mark) {
  Verdict v{hasFrom("a tag answered", mark), hasFrom("no tag answered", mark),
            hasFrom("NO VALID EVIDENCE", mark), ""};
  for (size_t i = mark; i < rec().console.size(); ++i) {
    auto p = rec().console[i].find("ATQA ");
    if (p != std::string::npos && v.answer) v.atqa = rec().console[i].substr(p + 5, 5);
  }
  return v;
}
void fieldUp(bool tag, int delay_reads) {
  coldBoot(); keys("N");
  g_radio->nfc_tag_present = tag;
  g_radio->nfc_answer_after_irq_reads = delay_reads;
}
uint64_t bytesOfOneT(bool tag, int delay_reads) {
  fieldUp(tag, delay_reads);
  const uint64_t b0 = g_radio->nfc_bytes; keys("T");
  return g_radio->nfc_bytes - b0;
}
}  // namespace

int main() {
  int healthy_ok = 0, healthy_n = 0;
  auto healthy = [&](bool tag, int d) {
    fieldUp(tag, d); size_t m = rec().console.size(); keys("T");
    Verdict v = runT(m); ++healthy_n;
    bool ok = tag ? (v.answer && v.atqa == "04 00") : (v.notag && !v.answer);
    if (ok) ++healthy_ok;
    std::printf("HEALTHY tag=%d delay=%d answer=%d notag=%d nve=%d atqa=%s ok=%d\n",
                tag, d, v.answer, v.notag, v.nve, v.atqa.c_str(), ok);
  };
  healthy(true, 0); healthy(true, 2); healthy(false, 0);

  // persistent
  int pers_n = 0, pers_trusted = 0, pers_affirm = 0, pers_notag = 0;
  std::string pers_first;
  for (int tag = 0; tag < 2; ++tag)
  for (int d : {0, 2})
  for (int hears = 0; hears < 2; ++hears)
  for (int fill : {0x00, 0xFF}) {
    const uint64_t n = bytesOfOneT(tag, d);
    for (uint64_t k = 0; k < n; ++k) {
      fieldUp(tag, d);
      const uint64_t b0 = g_radio->nfc_bytes;
      g_radio->nfc_glitch_from_byte = b0 + k;
      g_radio->nfc_glitch_until_byte = ~uint64_t(0);
      g_radio->nfc_glitch_fill = uint8_t(fill);
      g_radio->nfc_glitch_part_hears = hears;
      size_t m = rec().console.size(); keys("T");
      g_radio->nfcClearGlitch();
      Verdict v = runT(m); ++pers_n;
      if (v.answer || v.notag) {
        ++pers_trusted; if (v.answer) ++pers_affirm; else ++pers_notag;
        if (pers_first.empty()) {
          char b[160]; std::snprintf(b, sizeof b, "tag=%d delay=%d hears=%d fill=%02X from_byte=%llu/%llu -> %s",
            tag, d, hears, fill, (unsigned long long)k, (unsigned long long)n,
            v.answer ? ("a tag answered ATQA " + v.atqa).c_str() : "no tag answered");
          pers_first = b;
        }
      }
    }
  }
  std::printf("PERSISTENT cases=%d trusted_dead_bus=%d affirmative=%d no_tag=%d\n",
              pers_n, pers_trusted, pers_affirm, pers_notag);
  if (!pers_first.empty()) std::printf("  first: %s\n", pers_first.c_str());

  // recovered
  int rec_n = 0, rec_wrong = 0, rec_false_affirm = 0, rec_false_neg = 0, rec_bad_atqa = 0;
  std::string rec_first;
  for (int tag = 0; tag < 2; ++tag)
  for (int d : {0, 2})
  for (int hears = 0; hears < 2; ++hears)
  for (int fill : {0x00, 0xFF}) {
    const uint64_t n = bytesOfOneT(tag, d);
    for (uint64_t w = 1; w <= 48; ++w)
    for (uint64_t k = 0; k < n; ++k) {
      fieldUp(tag, d);
      const uint64_t b0 = g_radio->nfc_bytes;
      g_radio->nfc_glitch_from_byte = b0 + k;
      g_radio->nfc_glitch_until_byte = b0 + k + w;
      g_radio->nfc_glitch_fill = uint8_t(fill);
      g_radio->nfc_glitch_part_hears = hears;
      size_t m = rec().console.size(); keys("T");
      g_radio->nfcClearGlitch();
      Verdict v = runT(m); ++rec_n;
      bool fa = !tag && v.answer, fn = tag && v.notag,
           ba = tag && v.answer && v.atqa != "04 00";
      if (fa || fn || ba) {
        ++rec_wrong; rec_false_affirm += fa; rec_false_neg += fn; rec_bad_atqa += ba;
        if (rec_first.empty()) {
          char b[200]; std::snprintf(b, sizeof b, "tag=%d delay=%d hears=%d fill=%02X window=[%llu,+%llu)/%llu -> %s %s",
            tag, d, hears, fill, (unsigned long long)k, (unsigned long long)w,
            (unsigned long long)n, v.answer ? "a tag answered ATQA" : "no tag answered",
            v.atqa.c_str());
          rec_first = b;
        }
      }
    }
  }
  std::printf("RECOVERED cases=%d wrong=%d false_affirmative=%d false_negative=%d wrong_atqa=%d\n",
              rec_n, rec_wrong, rec_false_affirm, rec_false_neg, rec_bad_atqa);
  if (!rec_first.empty()) std::printf("  first: %s\n", rec_first.c_str());

  // stale: a stale I_rxe + stale ATQA, no tag, part deaf across the boundary
  int stale_n = 0, stale_affirm = 0;
  {
    const uint64_t n = bytesOfOneT(false, 0);
    for (uint64_t w = 1; w <= 48; ++w)
    for (uint64_t k = 0; k < n; ++k) {
      fieldUp(false, 0);
      g_radio->nfcSetFifo({0x04, 0x00});
      g_radio->nfc_regs[0x1A] = 0x30;
      const uint64_t b0 = g_radio->nfc_bytes;
      g_radio->nfc_glitch_from_byte = b0 + k;
      g_radio->nfc_glitch_until_byte = b0 + k + w;
      g_radio->nfc_glitch_fill = 0x00;
      g_radio->nfc_glitch_part_hears = false;
      size_t m = rec().console.size(); keys("T");
      g_radio->nfcClearGlitch();
      Verdict v = runT(m); ++stale_n; stale_affirm += v.answer;
    }
  }
  std::printf("STALE cases=%d stale_answer_claimed=%d\n", stale_n, stale_affirm);

  // error_rank
  struct E { const char *name; uint8_t main, err, f2; };
  const E es[] = {{"I_col", 0x24, 0x00, 0x00}, {"I_err1", 0x20, 0x10, 0x00},
                  {"I_par", 0x20, 0x40, 0x00}, {"I_crc", 0x20, 0x80, 0x00},
                  {"fifo_ovr", 0x20, 0x00, 0x10}, {"fifo_unf", 0x00, 0x00, 0x20},
                  {"lb_bits", 0x20, 0x00, 0x03}, {"I_rxs_only", 0x20, 0x00, 0x00}};
  int er_n = 0, er_notag = 0;
  for (const E &e : es) {
    fieldUp(true, 0);
    g_radio->nfc_answer_main = e.main; g_radio->nfc_answer_error = e.err;
    g_radio->nfc_answer_fifo2_flags = e.f2; g_radio->nfc_answer_fifo_bytes = 0;
    size_t m = rec().console.size(); keys("T");
    Verdict v = runT(m); ++er_n; er_notag += v.notag;
    std::printf("ERROR_RANK %s -> answer=%d notag=%d nve=%d\n", e.name, v.answer, v.notag, v.nve);
  }
  std::printf("ERROR_RANK cases=%d error_reported_as_no_tag=%d\n", er_n, er_notag);
  std::printf("HEALTHY ok=%d/%d\n", healthy_ok, healthy_n);
  const bool defect = pers_trusted || rec_wrong || stale_affirm || er_notag;
  std::printf("R22-01 %s\n", defect ? "REPRODUCED" : "NOT REPRODUCED");
  return 0;
}
'''


PROBE_R22_05 = r'''
int main() {
  coldBoot();
  size_t mark = rec().console.size();
  keys("J");
  std::string arm;
  for (size_t i = mark; i < rec().console.size(); ++i)
    if (rec().console[i].find("hold-off ARMED") != std::string::npos) arm = rec().console[i];
  const bool recorded = aqroot_hal::nvs().count("aqroot-fap01/holdoff") == 1;
  mcuReset();                       // a POWER CYCLE: fresh parts, NVS kept
  mark = rec().console.size();
  setup(); pump(2);
  const bool restored = hasFrom("hold-off RESTORED", mark);
  aqroot_hal::nvs()["aqroot-fap01/holdoff"] = 0x02;   // a record, nothing armed
  mark = rec().console.size();
  keys("Q");
  const bool q_confirms = hasFrom("NVS confirmed clear", mark);
  const bool q_erased = aqroot_hal::nvs().count("aqroot-fap01/holdoff") == 0;
  const bool says_one_warm = arm.find("ONE warm reset") != std::string::npos;
  const bool says_power_cycle = arm.find("power cycle") != std::string::npos;
  std::printf("ARM_LINE %s", arm.c_str());
  std::printf("recorded=%d power_cycle_restores=%d arm_says_ONE_warm_reset=%d "
              "arm_names_power_cycle=%d Q_confirms_clear=%d Q_erases_stale=%d\n",
              recorded, restored, says_one_warm, says_power_cycle, q_confirms, q_erased);
  const bool defect = restored && (says_one_warm || !says_power_cycle || !q_confirms || !q_erased);
  std::printf("R22-05 %s\n", defect ? "REPRODUCED" : "NOT REPRODUCED");
  return 0;
}
'''


def h9_probe(tree):
    """R22-04: the tree's own H9 with PlatformIO ABSENT, PATH-only, and a
    duplicated conflicting default_envs with PlatformIO absent.  D-802's H9
    block is executed as written (Astra's method); the D-803 tree exposes
    `_h9_evaluate`."""
    import importlib.util, os, shutil, textwrap
    path = tree / "hardware/demo/manufacturing/checks/firmware_hw_map_contract.py"
    sys.path.insert(0, str(path.parent))
    sys.path.insert(0, str(path.parent.parent))
    spec = importlib.util.spec_from_file_location("h9_%d" % abs(hash(str(tree))), path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    ini = (tree / "Firmware/platformio.ini").read_text()
    line = "default_envs = aqroot-demo\n"
    dup = ini.replace(line, "default_envs = aqroot-demo-fap01\n" + line, 1)
    real = m.PIO if Path(m.PIO).exists() else Path(shutil.which("pio") or "")
    absent = Path(tempfile.gettempdir()) / "aqroot-h9-no-such-pio"
    out = {}
    with tempfile.TemporaryDirectory(prefix="d803-h9-") as tmp:
        tmp = Path(tmp)
        for name in ("pio", "platformio"):
            (tmp / name).mkdir()
            (tmp / name / name).symlink_to(real)
        cases = (("pio_absent", ini, ""), ("pio_only_on_PATH", ini,
                 str(tmp / "pio") + ":/usr/bin:/bin"),
                 ("platformio_only_on_PATH", ini,
                  str(tmp / "platformio") + ":/usr/bin:/bin"),
                 ("duplicate_conflicting_default_pio_absent", dup, ""))
        old_path = os.environ.get("PATH", "")
        for case, text, pth in cases:
            if hasattr(m, "_h9_evaluate"):
                ev = m._h9_evaluate(text, absent, pth)
                out[case] = dict(verdict="PASS" if not ev["problems"] else "FAIL",
                                 cross_check=ev["pio_project_config"].get("found_by"),
                                 first_problem=(ev["problems"] or [None])[0])
            else:
                src = path.read_text()
                a = src.index("    h9_problems ="); b = src.index("    # ---- H10", a)
                block = textwrap.dedent(src[a:b])
                fw = tmp / case / "Firmware"; fw.mkdir(parents=True)
                (fw / "platformio.ini").write_text(text)
                m.ROOT = tmp / case; m.PIO = absent
                os.environ["PATH"] = pth
                ns = dict(vars(m)); ns.update(ini_text=text, report={},
                                              PLATFORMIO_INI=fw / "platformio.ini")
                try:
                    exec(compile(block, str(path) + ":H9", "exec"), ns)
                finally:
                    os.environ["PATH"] = old_path
                d = ns["report"]["H9_platformio_default_is_the_release_image"]
                out[case] = dict(verdict=d["verdict"],
                                 cross_check=d["pio_project_config"],
                                 first_problem=(d["problems"] or [None])[0])
    must_fail = ("pio_absent", "duplicate_conflicting_default_pio_absent")
    must_pass = ("pio_only_on_PATH", "platformio_only_on_PATH")
    reproduced = any(out[c]["verdict"] == "PASS" for c in must_fail) or any(
        out[c]["cross_check"] in (None, {"available": False})
        or "UNAVAILABLE" in str(out[c]["first_problem"]) for c in must_pass)
    return dict(cases=out, reproduced=bool(reproduced))


def run(firmware_tree, probe=None):
    fw_test = ROOT / "Firmware"
    fw_src = firmware_tree / "Firmware"
    text = (fw_test / "test/test_fap01_image.cpp").read_text(encoding="utf-8")
    text = text.replace("int main() {", "int released_test_main() {", 1) + (
        probe or PROBE)
    with tempfile.TemporaryDirectory(prefix="d803-witness-") as tmp:
        src = Path(tmp) / "probe.cpp"
        exe = Path(tmp) / "probe"
        src.write_text(text, encoding="utf-8")
        cmd = ["g++", "-std=c++17", "-O1", "-DARDUINO=200", "-DAQROOT_FAP01_DIAGNOSTIC",
               "-DAQROOT_TEST_EXPECT_FAP01", "-DAQROOT_TEST_NFC_SUPPLY_3V3=1",
               "-I", str(fw_test / "test/image"), "-I", str(fw_src / "src/hw"),
               "-I", str(fw_src / "src"), "-I", str(fw_src / "src/fap01"), str(src),
               str(fw_src / "src/demo/main.cpp"),
               str(fw_src / "src/fap01/aqroot_fap01.cpp"),
               str(fw_test / "test/image/image_main.cpp"), "-o", str(exe)]
        build = subprocess.run(cmd, capture_output=True, text=True)
        if build.returncode != 0:
            return dict(compiled=False, stderr=build.stderr[-3000:])
        out = subprocess.run([str(exe)], capture_output=True, text=True,
                             timeout=3600)
        return dict(compiled=True, exit=out.returncode, stdout=out.stdout,
                    reproduced=" REPRODUCED" in out.stdout
                    and "NOT REPRODUCED" not in out.stdout)


def git_sha(tree):
    return subprocess.run(["git", "-C", str(tree), "rev-parse", "HEAD"],
                          capture_output=True, text=True).stdout.strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--before", type=Path, required=True)
    ap.add_argument("-o", dest="out", type=Path)
    args = ap.parse_args()
    report = dict(schema=1, decision="D-803",
                  model="working-tree Firmware/test/image (D-803 byte-window hooks)",
                  before=dict(tree=str(args.before), git_sha=git_sha(args.before)),
                  after=dict(tree="working tree", git_sha_parent=git_sha(ROOT)),
                  probes={"R22-01_reqa_fresh_live": dict(
                      before=run(args.before), after=run(ROOT)),
                          "R22-04_h9_platformio_authority": dict(
                      before=h9_probe(args.before), after=h9_probe(ROOT)),
                          "R22-05_holdoff_operator_wording": dict(
                      before=run(args.before, PROBE_R22_05),
                      after=run(ROOT, PROBE_R22_05))},
                  document_witnesses=(
                      "R22-02 / R22-03 are reproduced in demo_feature_contract "
                      "itself (round22_rins_role_binding.witnesses; "
                      "round22_publication_scope) and as full-gate injections "
                      "in evidence/d803-full-gate-injections.json"))
    text = json.dumps(report, indent=1, sort_keys=True)
    if args.out:
        args.out.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
