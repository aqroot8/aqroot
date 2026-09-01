# -*- coding: utf-8 -*-
"""D-353: atomically promote the already-certified D-352 U20 transaction.

Refuses stale authority/candidate/evidence.  Promotion updates the PCB and its
topological journal together; live fingerprint and regression contract are
separate reviewed source changes in the same commit.
"""
import hashlib, json, os, shutil, subprocess, sys, tempfile

SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)
import incremental_router as IR
import u20_closed_branch_053 as D351
import u20_transaction_gate_054 as D352

BASE = '2cdc9f338db3fc0ed7a49db365c267a50b25f497ffc32aef9cf74eac9cbc09c4'
JOURNAL = os.path.join(SP, 'phaseA_journal.json')

EDGES = [
    ('/ACC_3V3_EN', 'R98.1', 'U20.1', 'ACC_3V3_CTL'),
    ('/ACC_3V3_EN', 'U20.1', 'TP26.1', 'ACC_3V3_CTL'),
    ('/ACC_3V3_EN', 'TP26.1', 'U3.15', 'ACC_3V3_CTL'),
    ('/01_POWER_TREE/ACC_3V3_ILIM', 'R97.1', 'U20.4', 'ACC_3V3_CTL'),
    ('/ACC_POWER_FAULT_N', 'R103.2', 'U20.6', 'ACC_POWER_FAULT_N'),
    ('/ACC_POWER_FAULT_N', 'U20.6', 'TP27.1', 'ACC_POWER_FAULT_N'),
    ('/ACC_POWER_FAULT_N', 'R103.2', 'U22.6', 'ACC_POWER_FAULT_N'),
    ('/ACC_POWER_FAULT_N', 'TP27.1', 'U3.18', 'ACC_POWER_FAULT_N'),
    ('/ACC_POWER_FAULT_N', 'U3.18', 'TP33.1', 'ACC_POWER_FAULT_N'),
]

def sha(path):
    return hashlib.sha256(open(path, 'rb').read()).hexdigest()

def main():
    if sha(IR.AUTH) != BASE:
        raise SystemExit('REFUSE: authoritative board is not D-343 baseline')
    run = subprocess.run([sys.executable, D352.__file__])
    ev = json.load(open(D352.OUT, encoding='utf-8'))
    if (run.returncode or ev.get('verdict') != 'PASS'
            or sha(D351.PCB) != ev.get('candidate_board_sha256')):
        raise SystemExit('REFUSE: D-352 candidate certification did not reproduce')
    jr = json.load(open(JOURNAL, encoding='utf-8'))
    if len(jr) != 132:
        raise SystemExit('REFUSE: journal is not the pinned 132-entry baseline')
    affected = {'/ACC_3V3_EN', '/01_POWER_TREE/ACC_3V3_ILIM', '/ACC_POWER_FAULT_N'}
    kept = [e for e in jr if e.get('net') not in affected]
    if len(jr) - len(kept) != 4:
        raise SystemExit('REFUSE: expected exactly four superseded control entries')
    for net, a, b, group in EDGES:
        kept.append(dict(net=net, a=a, b=b, role='REST_INC', layer='B.Cu',
                         w=0.2, requested_connected=True, group=group,
                         transaction='D-353'))
    if len(kept) != 137:
        raise SystemExit('REFUSE: replacement journal cardinality mismatch')

    board_tmp = IR.AUTH + '.d353.tmp'
    journal_tmp = JOURNAL + '.d353.tmp'
    shutil.copyfile(D351.PCB, board_tmp)
    with open(journal_tmp, 'w', encoding='utf-8') as f:
        json.dump(kept, f, indent=1)
        f.write('\n')
    os.replace(board_tmp, IR.AUTH)
    os.replace(journal_tmp, JOURNAL)
    print('PROMOTED D-353: %s -> %s ; journal 132 -> 137' %
          (BASE[:16], sha(IR.AUTH)[:16]))
    return 0

if __name__ == '__main__':
    sys.exit(main())
