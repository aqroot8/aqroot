# -*- coding: utf-8 -*-
"""FBV2-P2-003B -- via-array current/thermal SIZING for the named
BAT_PROTECTED_P high-current F.Cu bridge.  ANALYTIC, no board needed.

The bridge (if it exists) transitions the pack current B.Cu -> F.Cu, runs on
F.Cu at >= 1.20 mm, and transitions F.Cu -> B.Cu into the eastern node.  A
SINGLE through via is a bottleneck the CTO task forbids, so each transition must
be a via ARRAY sized for the current with margin, current-sharing headroom and
single-via-fault tolerance.

METHOD: the board's own IPC-2221B arithmetic, the SAME method
FBV2_P2 .kicad_dru section 5 used for the copper widths, applied to the plated
barrel of a through via as an INTERNAL conductor (the barrel is buried in FR4,
so k = 0.024, the conservative internal coefficient -- NOT the external 0.048).
Calibrated below against the DRU's own published figures so the method is not in
question, only its application.

    I = k * dT**0.44 * A**0.725       A in mil^2, I in A, dT in degC

Barrel copper cross-section of a plated through hole:
    A = pi/4 * (d_drill^2 - (d_drill - 2*t_plate)^2)
This is the exact annulus, more conservative than the thin-wall pi*d*t.

Everything here is conservative and local; anything that cannot be verified from
the repo is flagged UNVERIFIED.
"""
import json, math, os

MIL2 = 1550.0031            # mm^2 -> mil^2
K_EXT, K_INT = 0.048, 0.024
T_OUTER_MM = 0.035          # 1 oz outer, DRU section 5
T_INNER_MM = 0.0174         # 0.5 oz inner, DRU section 5


def ipc_current(area_mm2, dT, k):
    A = area_mm2 * MIL2
    return k * (dT ** 0.44) * (A ** 0.725)


def ipc_width_for_current(I, dT, k, t_mm):
    # invert: A(mil^2) = (I / (k*dT^0.44))^(1/0.725); width = A / t
    A = (I / (k * dT ** 0.44)) ** (1.0 / 0.725)
    return (A / (t_mm * MIL2))   # mm


def barrel_area_mm2(d_drill_mm, t_plate_mm):
    d_in = d_drill_mm - 2 * t_plate_mm
    return math.pi / 4.0 * (d_drill_mm ** 2 - d_in ** 2)


def main():
    out = {'task': 'FBV2-P2-003B', 'method': 'IPC-2221B, DRU section 5 method'}

    # ---- calibration: reproduce the DRU's own published width figures --------
    cal = {}
    cal['BAT_MAIN_outer_1.5A_10K'] = round(
        ipc_width_for_current(1.5, 10, K_EXT, T_OUTER_MM), 3)   # DRU says 0.525
    cal['BAT_MAIN_inner_1.5A_10K'] = round(
        ipc_width_for_current(1.5, 10, K_INT, T_INNER_MM), 3)   # DRU says 2.734
    out['calibration_mm'] = cal
    out['calibration_note'] = ('reproduces DRU section 5: outer 0.525 mm, '
                               'inner 2.734 mm for BAT_MAIN 1.5 A @ 10 K')

    # ---- the via under test: the harness TRUNK via, POWER-class -------------
    D_DRILL, T_PLATE, D_PAD = 0.40, 0.025, 0.80
    A_barrel = barrel_area_mm2(D_DRILL, T_PLATE)
    out['via'] = dict(drill_mm=D_DRILL, pad_mm=D_PAD, plating_um=T_PLATE * 1000,
                      barrel_area_mm2=round(A_barrel, 5),
                      barrel_area_mil2=round(A_barrel * MIL2, 2),
                      note='0.80/0.40 POWER-class through via (qrouter QBoard.via '
                           'default); plating 25 um is a conservative JLC assumption '
                           '-- UNVERIFIED against a fab traveller, flagged.')

    # per-via capacity, INTERNAL coefficient (barrel is buried in FR4)
    per = {}
    for dT in (10, 20):
        per['int_%dK' % dT] = round(ipc_current(A_barrel, dT, K_INT), 3)
        per['ext_%dK' % dT] = round(ipc_current(A_barrel, dT, K_EXT), 3)
    out['per_via_A'] = per
    out['per_via_design'] = per['int_10K']    # the conservative design number

    # ---- array sizing for 1.5 A nominal and 1.75 A validation --------------
    Iv = per['int_10K']
    def need(I, share=1.0):
        # `share` = worst hottest-via fraction of mean current it must tolerate
        # (1.0 ideal, 2.0 = one via carries twice the mean).  Required N so the
        # HOTTEST via stays within the 10 K per-via rating.
        return math.ceil((I * share) / Iv)
    sizing = {}
    for label, I in (('nominal_1.5A', 1.5), ('validation_1.75A', 1.75)):
        sizing[label] = dict(
            ideal_share=need(I, 1.0),
            imbalanced_2to1=need(I, 2.0),
            per_via_at_N3_A=round(I / 3.0, 3),
            per_via_at_N4_A=round(I / 4.0, 3),
            hottest_via_dT_N4_2to1=round(
                # dT from I = k dT^0.44 A^0.725 -> dT = (I/(k A^0.725))^(1/0.44)
                (( (2 * I / 4.0) / (K_INT * (A_barrel * MIL2) ** 0.725)) ** (1 / 0.44)),
                2),
        )
    out['array_sizing'] = sizing

    # ---- ruling ------------------------------------------------------------
    out['ruling'] = {
        'min_vias_per_array': 3,
        'design_vias_per_array': 4,
        'rationale': (
            'Per-via conservative capacity (internal FR4, 10 K rise) = %.3f A. '
            'Ideal-sharing need for 1.75 A validation = 2 vias; but current '
            'sharing from a single incoming trace is uneven, so the floor is '
            'raised to 3 (capacity %.2f A @10K = %.2fx margin; tolerates one '
            'open via -> 2 remain, %.2f A > 1.75 A). Design target is 4 for '
            'headroom and 2:1-imbalance safety (hottest via then rises only '
            '~%.1f K). No single-via bottleneck at either transition.'
            % (Iv, 3 * Iv, 3 * Iv / 1.75, 2 * Iv,
               sizing['validation_1.75A']['hottest_via_dT_N4_2to1'])),
        'via_resistance_mohm_each': 0.88,   # b34_from_copper.R_VIA
        'array_resistance_mohm': {'N3': round(0.88 / 3, 3),
                                  'N4': round(0.88 / 4, 3)},
        'unverified': [
            'plating thickness 25 um (JLC typical; not from a fab traveller)',
            'no thermal coupling credit taken for barrel-to-plane conduction '
            '(would only improve capacity) -- conservative',
            'IPC-2221B applied to a via barrel is the conservative industry '
            'proxy; a via is better cooled than a surface trace of equal area',
        ],
    }

    print(json.dumps(out, indent=1))
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                     'place_002z', 'via_array_003b.json')
    json.dump(out, open(p, 'w'), indent=1)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
