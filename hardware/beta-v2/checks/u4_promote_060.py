# -*- coding: utf-8 -*-
"""D-358: atomically promote the D-357-certified U4 transaction."""
import hashlib, json, os, shutil, subprocess, sys

SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)
import incremental_router as IR
import u4_closed_branch_058 as D356
import u4_transaction_gate_059 as D357

BASE = '02e263a75f88fa965f7a01aa399d84f66d7a64ce0435695701f4f8e47c09b1c5'
JOURNAL = os.path.join(SP, 'phaseA_journal.json')
ADDR = '/05_I2C_DEVICES/BMI270_SDO_ADDR'

EDGES = [
    (ADDR, 'R118.1', 'R119.2', 'B.Cu', 'IMU_ADDR'),
    (ADDR, 'R119.2', 'U4.1', 'B.Cu', 'IMU_ADDR'),
    ('/05_I2C_DEVICES/BMI270_INT1_RAW', 'R18.1', 'U4.4', 'I3.Cu',
     'BMI270_INT1_RAW'),
]


def sha(path):
    return hashlib.sha256(open(path, 'rb').read()).hexdigest()


def main():
    if sha(IR.AUTH) != BASE:
        raise SystemExit('REFUSE: authoritative board is not D-353 baseline')
    run = subprocess.run([sys.executable, D357.__file__])
    ev = json.load(open(D357.OUT, encoding='utf-8'))
    if (run.returncode or ev.get('verdict') != 'PASS'
            or sha(D356.PCB) != ev.get('candidate_board_sha256')):
        raise SystemExit('REFUSE: D-357 candidate certification did not reproduce')
    jr = json.load(open(JOURNAL, encoding='utf-8'))
    if len(jr) != 137:
        raise SystemExit('REFUSE: journal is not the pinned 137-entry baseline')
    kept = [e for e in jr if e.get('net') != ADDR]
    if len(jr) - len(kept) != 2:
        raise SystemExit('REFUSE: expected exactly two superseded address entries')
    for net, a, b, layer, group in EDGES:
        kept.append(dict(net=net, a=a, b=b, role='REST_INC', layer=layer,
                         w=0.2, requested_connected=True, group=group,
                         transaction='D-358'))
    if len(kept) != 138:
        raise SystemExit('REFUSE: replacement journal cardinality mismatch')

    board_tmp = IR.AUTH + '.d358.tmp'
    journal_tmp = JOURNAL + '.d358.tmp'
    shutil.copyfile(D356.PCB, board_tmp)
    with open(journal_tmp, 'w', encoding='utf-8') as f:
        json.dump(kept, f, indent=1)
        f.write('\n')
    os.replace(board_tmp, IR.AUTH)
    os.replace(journal_tmp, JOURNAL)
    print('PROMOTED D-358: %s -> %s ; journal 137 -> 138' %
          (BASE[:16], sha(IR.AUTH)[:16]))
    return 0


if __name__ == '__main__':
    sys.exit(main())
