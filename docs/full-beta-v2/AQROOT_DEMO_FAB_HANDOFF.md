# AQROOT Demo — FABRICATION HANDOFF

**Board:** `hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb`
**Authority:** `sha256 c7f5c61896269276ecf680266adf23b36b9adc1f3d89bc93be311174498b7406`
**Package:** `hardware/demo/fab/` — 29 files, regenerated at this authority
**Date:** 2026-09-18 · **Decisions:** D-742 … D-745 · **Prepared for:** independent CTO review

---

## 1. Final board status

77.000 × 148.000 mm stepped outline, 6 copper layers, 3516 tracks, 904 vias,
71 zones, 309 footprints, 292 fitted references and 16 schematic-DNP.

| measure | value |
|---|---|
| retained multi-pad nets | **172** |
| connected retained nets | **171** |
| retained open edges | 1 |
| **unapproved open edges** | **0** |
| approved Demo NC | `J5.9`–`J5.12`, `J5.15`–`J5.18` — expected == observed |
| approved unrouted | `U11.3` only, under the 2026-09-17 owner decision |
| open owner decisions | **none** |

The single unrouted contact is `/BQ25185_STAT2` at `U11.3`. The owner approved
shipping it bare on 2026-09-17; `routing_ledger.py` re-proves that declaration
against the board on every run — the pad must exist, its part be fitted, it must
still carry `/BQ25185_STAT2`, it must still be stranded, and `R128` and `TP7`
must still be fitted — and **fails if any of those stops being true**.

## 2. Major design changes in this cycle

**No copper changed.** The board's track, zone and placement signatures are
byte-identical to the previous authority (`evidence/d743-copper-unchanged.json`);
the hash moved only because two footprint `Value` fields did.

1. **The charger could not complete a charge, and now can.** `R37` 1 kΩ → **390 Ω**
   (`ICHG` 300 mA → **769 mA**) and `R36` 18 kΩ → **13 kΩ** (input limit ILIM500 →
   **ILIM1100**, `VBATREG` unchanged at **4.2 V**, `VLOWV` unchanged at 3.0 V).
   SLUSF65B rev B (Aug 2026) halved the fast-charge safety timer `tMAXCHG` from
   720 to 360 min; at 300 mA the charger delivered 1800 mAh against a
   2500–3000 mAh cell, stopped at 60–72 % SoC and latched a **non-recoverable
   fault** that `/CE` — hard-tied to GND — cannot clear. New margin **286 min at
   3000 mAh, 238 at 2500**, against 360.
2. **The charger status decode was inverted on `STAT1`** in both schematic sheets
   and four documents — `STAT1` LOW is a **fault**, not "charging". Corrected
   everywhere; D-170's decode paragraph is superseded.
3. **Documentation, gates and measurement** — everything else in D-742…D-745.

## 3. Connectivity

`routing_ledger.py`: 171 of 172 retained nets connected, `unapproved_open_edges`
**0**. KiCad reports 17 unconnected items and **every one is accounted for**: 16
are pads of the sixteen schematic-DNP references (`U13` and its NFC-5 V boost
network, the DNP 0 Ω bypasses, the DNP speaker-filter caps) and the seventeenth
is `U11.3`.

`checks/demo_feature_contract.py` asserts the product absolutely, from
`AQROOT_DEMO_SCOPE.md`'s own lists: **40 features, 71 references, 106 nets** —
every part on the board *and fitted*, every net whole or covered by a named owner
decision, the approved-NC set exactly the eight `J5` positions, and every exposed
`J5` signal contact reaching an ESD array. **All four clauses PASS**, with nine
controls proving none of them is vacuous.

## 4. DRC

| run | result |
|---|---|
| `--severity-all --schematic-parity` | 199 `lib_footprint_issues` (warning), 17 unconnected, 246 parity warnings, **0 parity errors** |
| all five IGNORED rules promoted to error | 2 `missing_courtyard` (`BOSS1`/`BOSS2` mounting bosses), 5 `track_not_centered_on_via`, **zero new** |
| `connection_width`, probed at 0.20 mm | 81 distinct pairs, 74 benign acute throats, 7 below 0.15 mm, **none load-bearing** |
| pour islands | 95 filled islands over six layers, **zero orphans** |

`min_connection` is 0.000 mm in board setup, so KiCad never runs
`connection_width` — the same defect class D-738 found in
`solder_mask_min_width`. It is probed in a scratch copy and the board setup is
deliberately left alone; the measurement is the deliverable.

## 5. Safety and power

* **D-269 / D-186 proven.** `protected_copper` is byte-identical across every
  decision in this cycle. D-186's split — two independent series disconnects with
  their own external pull-downs — is now machine-checked by name (`R102`, `R131`,
  `TP47`); on Demo the `ACC_5V_SW_EN` bit sits on `U3` P03 rather than D-186's
  `U23` P04 because `U23` is removed by scope, and the split and pull-downs, not
  the bit, are what D-186 requires. D-187's isolation FET and the four
  expander safe-state pulls are required by name too.
* **`VBATREG` is unchanged at 4.2 V.** The charger ECO moved only the input
  current limit and the charge current; nothing in the protection architecture
  moved.
* **First absolute power audit.** `audit_rail_ampacity.py` walks each rail's
  *carrying path* — not its net — self-checks by re-deriving `.kicad_dru`
  section 5's published table, and reports temperature rise rather than
  pass/fail. All rails pass; two carry **named, length-bounded exceptions** with
  controls that fail when they are removed, mis-scoped or overrun.

## 6. USB / RF / NFC

* **USB** — differential pair on `F.Cu` over `In1` with no vias, per `.kicad_dru`
  section 6; DRC clean. `USB_VBUS_RAW` carries 1.1 A with a 5.4 K rise.
* **RF** — `rf_symmetry` and `keepout_stackup` contracts byte-identical; the
  ESP32-S3 antenna keep-out and the manufacturer-precedence rule are intact.
* **NFC** — measured, not asserted. Decoupling is **4.64–7.39 mm from the pin on
  every `U9` driver rail** (`VDD_RF` 2.92 nH, 0.249 Ω at 13.56 MHz ≈ **62 mV of
  ripple at the 250 mA peak**). Further than ST's reference layout, and not
  improvable without moving `U9`'s block on a board where every corridor probe
  returns 0.0 mm. All eighteen `TUNE` parts and both antenna test points
  (`TP37`, `TP38`) are present, so first-article tuning is possible.

## 7. Manufacturing package

`FAB1` provenance · `FAB2` fill · `FAB3` layers · `FAB4` drill · `FAB5` CPL ·
`FAB6` BOM · `FAB7` sourcing · `FAB8` outline · `FAB9` via-in-pad ·
`FAB10` via geometry · `FAB11` mask dams — **all PASS** at this authority.
`contract_regression` runs **16 contracts: all ran, all PASS,
`all_identical_where_comparable` TRUE, `vacuous` FALSE.**

The package declares, in generated notes with `MANIFEST` rows: **via-in-pad in
135 solderable lands** (resin-filled, capped, plated), **38 vias below the
board's own annular floor** on named net- and area-scoped licences, and **21
solder-mask dams below 0.125 mm**, of which four `U9` corners are 0.0621 mm
between different nets.

## 8. Significant remaining prototype risks

1. **Charge-current ECO is unverified in hardware.** Derived from SLUSF65B and
   TI's own worked examples, but never measured. `TREG` at 100 °C bounds the
   thermal risk — the part reduces its own charge current rather than
   overheating — and `TSHUT` at 150 °C is not approached. **First article must
   measure charge current, total charge time and `U11` case temperature, in the
   enclosure, at the fitted cell capacity.** Prefer the **2500 mAh** end of the
   envelope; 3000 mAh at 40 °C ambient is the least-margin corner.
2. **Charger input trunk is 250.8 mm / 440 mΩ** against a 65 mm straight line,
   because the net was laid as a minimum spanning tree through the north-west
   recovery cluster. 484 mV of drop and 0.53 W at 1.1 A. Measured: no shorter
   path exists on any layer at any width, and in-place widening is worth under
   5 %. Accepted as `.kicad_dru` section 5a, the board's one named ampacity
   exception. **Measure `VIN` at `U11.10` while charging.**
3. **Charging from a 500 mA-class source will not complete a cycle** inside
   `tMAXCHG`. The USB-C port is a plain 5.1 kΩ Rd sink and does not read the
   source's Rp advertisement; VINDPM folds the input back as `VIN` sags.
   **Published in `DEVICE_SPEC`: charge from a 1 A or better source.**
4. **NFC read range** — see §6. Tune `L5`/`L6`/`C69`–`C72` at first article.
5. **`J5` recess is an enclosure requirement with a hard number.** The mating
   face is at `x = 72.430`, the board edge over `J5`'s span at `x = 72.000`, and
   there is **6.070 mm of air** between the mating face and the east cavity
   face. Against a Samtec `SSQ` insertion depth of 3.68–6.35 mm, **the east wall
   must step inward to follow the board's own step** over `y ≈ 8.475 … 69.945`.
   A straight east wall leaves the Community Port unusable.
6. **`M-09` fits at its bound, not with measured clearance.**
   `2.0 + 8.50 + 1.6 + 8.0 + 0.6 + 2.0 = 22.70 of 23.0 mm`. 8.51 mm is the
   connector insulator's largest dimension, so the column is an upper bound —
   but only **0.30 mm** of spare. CAD-to-verify against the Samtec 3D model.
7. **Charger fault granularity.** With `STAT2` unlanded, `STAT1` LOW is a
   directly observed fault but recoverable versus non-recoverable is not
   distinguishable, and charging versus charge-complete is an **inference**.
8. **Fabricator acceptance still to be obtained at order time** — the `J3` NPTH
   concession, the `MK1` acoustic mask opening, the POFV process for 135 lands,
   the 35 sub-floor via rings and the 21 sub-0.125 mm mask dams are all declared
   in the fab notes and must be confirmed in writing before the order is placed.
9. **Demo firmware does not exist yet** for the charger and expanders. The
   hardware documentation it must be written from is now correct — in particular
   the corrected `STAT1` polarity, which a driver written from the old note would
   have inverted.

## 9. Recommended post-Kickstarter improvements

1. **Charger input as a star, not a daisy chain** — a direct `R35` → `U11.10`
   trunk on outer copper retires the section-5a exception and ~0.4 W of loss.
2. **A charger whose `STAT2` is not adjacent to `BAT`**, or a package with a land
   taller than 0.200 mm. Rotating or moving `U11` cannot help: `BAT` is pin 2 and
   `STAT2` pin 3 in every DLH0010A.
3. **Bring `/CE` under firmware control** so a safety-timer fault can be cleared
   without a USB re-plug.
4. **Read the Type-C Rp advertisement** instead of relying on VINDPM.
5. **Re-floorplan the `U9` NFC block** so decoupling sits at the pins.
6. **Restore the full ten-XGPIO expansion architecture** and `U23`.

---

## 10. What a reviewer should read, in order

1. `CTO_DECISIONS.md` — **D-745, D-744, D-743, D-742** at the top.
2. `CURRENT_STATE.md` §1.
3. `hardware/demo/manufacturing/evidence/d74[2-6]-*.json`.
4. `hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_dru` **section 5a** — the
   one named ampacity exception, written in full with its measurements.
5. `DEVICE_SPEC.md` **§0a** — the Demo delta every Kickstarter claim must read.
6. `hardware/demo/kicad/aqroot-demo/vendor/` — the TI and Samtec datasheets this
   cycle's conclusions are drawn from, with their hashes.
