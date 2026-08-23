"""Full Beta v2 fork-provenance probe.

Run:  python hardware/beta-v2/checks/fork_equivalence.py

hardware/beta-v2/ was forked from hardware/beta-dm/ at FBV2-S1.  This script
re-derives, from the two directories as they stand, exactly which forked files
are still bit-identical to Beta-DM, which are identical after normalising the
embedded project name, and which were deliberately changed by the migration.

It exists because the FBV2-S1 exit criterion demands a *byte-equivalence proof*
and not an assertion.  The programme has already been burned once by progress
that was recorded rather than measured.

Exit code 0 = the fork matches the declared expectation, 1 = it does not.
"""
import hashlib
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DM = os.path.join(HERE, '..', '..', 'beta-dm', 'kicad', 'aqroot-beta-dm')
V2 = os.path.join(HERE, '..', 'kicad', 'aqroot-beta-v2')

DM_PROJ = 'aqroot-Beta-DM'
V2_PROJ = 'aqroot-Beta-v2'

# Same length, so a normalised comparison also proves no length drift.
assert len(DM_PROJ) == len(V2_PROJ)

# Sheets still inherited verbatim from Beta-DM.  A sheet leaves this list the
# moment its FBV2-S1 migration lands, and moves into FILES as 'changed'.
SHEETS = [
    '08_buttons_expanders',
    '09_community_header',
]

# Footprints that exist in Full Beta v2 and not in Beta-DM, with the task that
# added them.  An addition that is not listed here is a probe failure.
ADDED_FOOTPRINTS = {
    'PUI_DMM-4026-B-I2S_4.0x3.0mm.kicad_mod': 'FBV2-S1-006, PUI microphone replacing the ICS-43434',
}

# (dm name, v2 name, expectation)
#   'bit'   -> byte-for-byte identical
#   'norm'  -> identical after project-name normalisation only
#   'changed' -> deliberately modified by FBV2-S1
FILES = (
    [('%s.kicad_sch' % s, '%s.kicad_sch' % s, 'norm') for s in SHEETS]
    + [
        ('01_power_tree.kicad_sch', '01_power_tree.kicad_sch', 'changed'),
        ('02_mcu_core.kicad_sch', '02_mcu_core.kicad_sch', 'changed'),
        ('03_spi_a_display_sd.kicad_sch', '03_spi_a_display_sd.kicad_sch', 'changed'),
        ('04_spi_b_radios_nfc.kicad_sch', '04_spi_b_radios_nfc.kicad_sch', 'changed'),
        ('%s.kicad_pcb' % DM_PROJ, '%s.kicad_pcb' % V2_PROJ, 'bit'),
        ('%s.kicad_dru' % DM_PROJ, '%s.kicad_dru' % V2_PROJ, 'bit'),
        ('%s.kicad_sch' % DM_PROJ, '%s.kicad_sch' % V2_PROJ, 'changed'),
        ('%s.kicad_pro' % DM_PROJ, '%s.kicad_pro' % V2_PROJ, 'changed'),
        ('%s.kicad_prl' % DM_PROJ, '%s.kicad_prl' % V2_PROJ, 'norm'),
        ('fp-lib-table', 'fp-lib-table', 'bit'),
        ('sym-lib-table', 'sym-lib-table', 'bit'),
        ('README.md', 'README.md', 'changed'),
        ('libraries/AQROOT_Beta.kicad_sym', 'libraries/AQROOT_Beta.kicad_sym', 'changed'),
    ]
)


def sha(path):
    return hashlib.sha256(open(path, 'rb').read()).hexdigest()


def norm(path, proj):
    return hashlib.sha256(
        open(path, 'rb').read().replace(proj.encode(), b'PROJECT')
    ).hexdigest()


def classify(dm_path, v2_path):
    if sha(dm_path) == sha(v2_path):
        return 'bit'
    if norm(dm_path, DM_PROJ) == norm(v2_path, V2_PROJ):
        return 'norm'
    return 'changed'


def main():
    fails = []
    rows = []
    for dm_name, v2_name, expect in FILES:
        dm_path = os.path.join(DM, dm_name)
        v2_path = os.path.join(V2, v2_name)
        if not (os.path.exists(dm_path) and os.path.exists(v2_path)):
            fails.append('missing: %s / %s' % (dm_name, v2_name))
            continue
        got = classify(dm_path, v2_path)
        rows.append((v2_name, expect, got, sha(dm_path)[:16], sha(v2_path)[:16]))
        if got != expect:
            fails.append('%s: expected %s, measured %s' % (v2_name, expect, got))

    # Every INHERITED footprint must still be bit-identical.  Full Beta v2 is
    # allowed to ADD footprints -- a migrated sheet that locks a new part needs
    # one -- but it may never modify or delete a footprint it inherited, because
    # those are what Beta-DM would be built from.  Additions must be declared
    # here so a new file cannot appear silently.
    dm_pretty = os.path.join(DM, 'libraries', 'AQROOT_Beta.pretty')
    v2_pretty = os.path.join(V2, 'libraries', 'AQROOT_Beta.pretty')
    dm_mods = sorted(os.listdir(dm_pretty))
    v2_mods = sorted(os.listdir(v2_pretty))
    missing = [m for m in dm_mods if m not in v2_mods]
    added = [m for m in v2_mods if m not in dm_mods]
    if missing:
        fails.append('inherited footprint deleted: %s' % missing)
    for m in added:
        if m not in ADDED_FOOTPRINTS:
            fails.append('undeclared footprint added: %s' % m)
    for m in dm_mods:
        if m in v2_mods and sha(os.path.join(dm_pretty, m)) != sha(os.path.join(v2_pretty, m)):
            fails.append('inherited footprint changed: %s' % m)

    print('%-34s %-8s %-8s %-18s %s' % ('file', 'expect', 'measured', 'beta-dm sha256', 'beta-v2 sha256'))
    for r in rows:
        print('%-34s %-8s %-8s %-18s %s' % r)
    if fails:
        print('  footprint comparison: see failures below')
    else:
        print('  %d inherited footprints compared, all bit-identical' % len(dm_mods))
        for m in added:
            print('  + added by Full Beta v2: %s (%s)' % (m, ADDED_FOOTPRINTS[m]))

    if fails:
        for f in fails:
            print('FAIL: %s' % f)
        return 1
    print('FORK EQUIVALENCE PROBE: PASS')
    return 0


if __name__ == '__main__':
    sys.exit(main())
