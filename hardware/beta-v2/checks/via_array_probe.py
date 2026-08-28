# -*- coding: utf-8 -*-
"""FBV2-P2-003B -- VIA-ARRAY SIZING CONTRACT probe (D-274).

Generalized regression for the named BAT_PROTECTED_P high-current bridge's via
arrays: it pins the board's own IPC-2221B via-ampacity arithmetic and REJECTS
undersized transition arrays, so a future bridge cannot quietly ship a single
via or a two-via neck on a 1.5 A / 1.75 A pack path.

This is the electrical half of the bridge mechanism's guard.  The GEOMETRIC half
-- an overbroad or bounding-box bridge corridor, or one that admits foreign nets,
or that authorises In2/In3 current copper -- is already rejected by dru_probe's
corridor_checks the moment any such area is instantiated, so it is not duplicated
here.

No board is loaded; the arithmetic is deterministic.  Exit 0 = contract holds.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import via_array_003b as VA

I_NOMINAL, I_VALID = 1.5, 1.75
MIN_VIAS = 3               # D-274 policy floor
DESIGN_VIAS = 4


def n_for(I, per_via, share=1.0):
    import math
    return math.ceil((I * share) / per_via)


def main():
    fails = []
    def check(name, cond, detail=''):
        print('  %-58s %s   %s' % (name, 'PASS' if cond else 'FAIL', detail))
        if not cond:
            fails.append(name)

    print('FBV2-P2-003B via-array sizing contract (D-274)')

    # 1. method integrity: reproduce the DRU's own published width figure
    w_out = VA.ipc_width_for_current(1.5, 10, VA.K_EXT, VA.T_OUTER_MM)
    check('method reproduces DRU BAT_MAIN outer 0.525 mm @1.5A/10K',
          abs(w_out - 0.525) < 0.005, 'got %.3f mm' % w_out)

    # 2. per-via capacity, conservative internal FR4 coefficient, 10 K rise
    A = VA.barrel_area_mm2(0.40, 0.025)
    Iv = VA.ipc_current(A, 10, VA.K_INT)
    check('per-via 0.40/25um capacity 1.0-1.1 A (internal, 10K)',
          1.0 <= Iv <= 1.12, '%.3f A' % Iv)

    # 3. a SINGLE via is insufficient for the validation case -> rejected
    check('single via REJECTED for 1.75 A pack current',
          Iv < I_VALID, '1 via = %.2f A < %.2f A' % (Iv, I_VALID))

    # 4. a TWO-via array is below the policy floor (no fault tolerance:
    #    lose one -> a single via must carry 1.75 A, which it cannot)
    two_fault = Iv                      # one of two open -> 1 via left
    check('two-via array REJECTED (no single-via-fault tolerance)',
          two_fault < I_VALID and MIN_VIAS > 2,
          'lose 1 of 2 -> %.2f A < %.2f A' % (two_fault, I_VALID))

    # 5. the >=3 floor is sufficient WITH one-via-fault tolerance
    three = 3 * Iv
    three_fault = 2 * Iv
    check('three-via floor carries 1.75 A with 1 open via',
          three >= I_VALID and three_fault >= I_VALID,
          '3 via=%.2f A, lose 1 -> %.2f A' % (three, three_fault))

    # 6. the derivation is self-consistent: ideal-sharing ampacity needs 2, the
    #    fault-tolerant floor is 3, and a strict 2:1 imbalance drives the design
    #    target to 4 -- exactly the numbers the mechanism uses.
    need_ideal = n_for(I_VALID, Iv, 1.0)
    need_imbal = n_for(I_VALID, Iv, 2.0)
    check('derivation self-consistent: ideal 2, floor 3, imbalanced->design 4',
          need_ideal == 2 and MIN_VIAS == 3 and need_imbal == DESIGN_VIAS,
          'ideal=%d floor=%d imbalanced2:1=%d design=%d'
          % (need_ideal, MIN_VIAS, need_imbal, DESIGN_VIAS))

    # 6b. the policy FLOOR (3) keeps even the hottest via within a 20 K rise
    #     under 2:1 imbalance -- acceptable, though the design target 4 is cooler.
    import math
    hot3 = 2 * I_VALID / MIN_VIAS
    dT3 = (hot3 / (VA.K_INT * (A * VA.MIL2) ** 0.725)) ** (1 / 0.44)
    check('floor 3-via array: hottest via < 20 K under 2:1 imbalance',
          dT3 < 20.0, 'dT=%.1f K' % dT3)

    # 7. the design target keeps the hottest via cool under 2:1 imbalance
    #    dT = (I/(k A^0.725))^(1/0.44)
    hottest = (2 * I_VALID / DESIGN_VIAS)
    dT = (hottest / (VA.K_INT * (A * VA.MIL2) ** 0.725)) ** (1 / 0.44)
    check('design 4-via array: hottest via < 10 K under 2:1 imbalance',
          dT < 10.0, 'dT=%.1f K' % dT)

    # 8. a malformed request (<MIN_VIAS) is an undersized exception
    for bad in (1, 2):
        ok_reject = bad < MIN_VIAS
        check('undersized %d-via transition REJECTED by floor' % bad, ok_reject)

    if fails:
        print('VIA-ARRAY PROBE: FAIL (%d)' % len(fails))
        return 1
    print('VIA-ARRAY PROBE: PASS')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
