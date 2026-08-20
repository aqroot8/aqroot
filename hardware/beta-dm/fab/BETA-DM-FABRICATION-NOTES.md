# AQROOT Beta-DM — fabrication notes

Binding notes for the **Beta-DM** fabrication build only. They do not apply to
Full Beta and they do not decide anything for the Final product.

---

## 1. Solder mask colour — GREEN

**Beta-DM solder mask is GREEN. This is a CTO ruling for this fabrication build
and it is not a default, a placeholder, or a supplier's choice.**

| | |
|---|---|
| Beta-DM solder mask | **GREEN** |
| substitution allowed? | **NO.** Do not silently accept black, white, blue, matte or any other mask on this build |
| what this decides | the Beta-DM fabrication build only |
| what this does **not** decide | Full Beta, the Final-product colour decision, enclosure appearance, or any PCB electrical architecture |

Reason it is binding rather than cosmetic: the R2 power-via escape (§2) is
accepted on a **0.125 mm solder-mask dam**. Green LPI is the best-characterised
and highest-resolution mask any of the candidate fabs offer. Dark and white
masks are generally coarser at small dam widths, so a colour substitution would
silently move a feature this build depends on. If a supplier proposes another
colour, that is an engineering change, not a finish change, and it must come
back for a ruling.

Put **"SOLDER MASK: GREEN — DO NOT SUBSTITUTE"** on the fab drawing and in the
order notes.

---

## 2. Critical feature — the R2 power-via solder-mask bridge

**This is the tightest mask feature on the board and it must survive
fabrication review. Do not let a fab "optimise", widen, or remove it.**

| item | value |
|---|---|
| feature | solder-mask dam between the `R2.1` pad opening and the `+3V3` power-via barrel |
| via | (21.900, 37.400), 0.65 mm pad / 0.40 mm drill, annular 0.125 mm |
| `R2.1` pad | (21.175, 37.500), 0.800 × 0.950 roundrect, net `+3V3` |
| **mask dam width** | **0.1250 mm** |
| board mask expansion | `pad_to_mask_clearance = 0` — the mask opening **is** the pad copper, board-wide |
| via tenting | **tented both sides** (board default front/back yes) |
| via fill state | **not** covered, plugged, capped or filled — plain tented via |
| via position | under the `R2` 0603 body, between the terminations |
| paste | no paste aperture over the via; the drill edge is 0.125 mm outside the paste opening |

### What the fab must not do

1. **Do not increase solder-mask expansion.** Any positive expansion eats the
   0.125 mm dam and merges the `R2.1` opening with the via barrel.
2. **Do not remove the tenting** over this via, on either side.
3. **Do not substitute a coarser mask** — see §1.
4. **Do not "clean up" the dam** by opening the via. If the dam is reported as
   below the house minimum, stop and return the query; do not resolve it
   unilaterally.

### What the fab may do

Plugging or capping this via is **acceptable and welcome** if offered at no
schedule cost — it strictly reduces the wicking risk. It is not required.

### Why it matters

If the dam is lost, printed paste on `R2.1` has a continuous path into a
0.40 mm through-barrel. At reflow that starves the `R2.1` joint — a classic
0603 tombstone — and can push solder out on F.Cu. The via sits under the body,
so the defect is not inspectable after assembly and rework means removing the
part.

The earlier geometry, via at (21.850, 37.400), gave only a **0.075 mm** dam and
overlapped the `R2.1` pad copper by 0.050 mm. It was **rejected on DFM** and
replaced; see
[BETA-DM-R2-POWER-VIA-DFM.md](../BETA-DM-R2-POWER-VIA-DFM.md).

---

## 3. Population

`D2`–`D7` (header shunt ESD arrays) and the other DNP parts are **not
populated** on Beta-DM. The authoritative lists are
[ASSEMBLY-DNP-CONTROL.md](ASSEMBLY-DNP-CONTROL.md),
`aqroot-Beta-DM-DO-NOT-POPULATE.csv` and `aqroot-Beta-DM-BOM-fitted.csv`.
`U10` (USBLC6-2SC6) **is fitted**.

---

## 4. Status

**Copper is complete and the board is released for fabrication data.**

| | |
|---|---|
| DRC | 0 errors, 240 warnings (silk only), 0 schematic-parity issues |
| Ledger | `103 = A64 + B1(0) + B2(18) + C0 + D21` |
| Fitted must-work non-GND unrouted | **0** |
| Fitted GND pads off the main GND island | **0** |
| Outer GND pours | present on `F.Cu` and `B.Cu`, solid-connected |
| Board outline | 155 x 74 mm, unchanged |

The earlier note here - "not yet released, 31 fitted must-work non-GND
connections remain open" - is superseded. Those closed across the Lean GPIO,
GND closeout and pour passes.

**Ready to order the PCB: yes.** **Ready to assemble: not until section 5 is
decided.**

---

## 5. Open via barrels inside paste apertures — ASSEMBLY DECISION REQUIRED

§2 protects the `R2.1` mask dam because printed paste with a path into a
through-barrel starves the joint. That reasoning is right, and the final DFM
sweep found it applies to **more pads than `R2.1`**.

Measured on the released board, by the same criterion §2 uses — distance from
the **drill edge** to the pad's paste aperture:

| | |
|---|---|
| `R2.1` (the documented critical feature) | **+0.125 mm dam** — barrel is outside the aperture, as designed |
| vias whose **barrel falls inside** a paste aperture | **63** |
| of those, on exposed/thermal pads | 11 — normal practice, not a concern |
| of those, on large IC / connector pads | 32 — low risk, large paste volume |
| **of those, on small fitted discrete or fine-pitch pads** | **20 pads across 17 references** |

The 17 references, worst first:

| ref/pad | pad | drill | barrel inside aperture by | net |
|---|---|---:|---:|---|
| `C13.1` | 0.90×0.95 | 0.40 | **0.200 mm** | `+3V3` |
| `R9.1` | 0.80×0.95 | 0.40 | **0.200 mm** | `+3V3` |
| `R5.1` | 0.80×0.95 | 0.40 | 0.150 mm | `+3V3` |
| `J3.A12`, `J3.B1` | 0.60×1.15 | 0.30 | 0.150 mm | `GND` |
| `R70.2` | 0.80×0.95 | 0.30 | 0.150 mm | `LED_A1` |
| `R26.2` | 0.80×0.95 | 0.30 | 0.150 mm | `DISP_CS_N` |
| `R42.2` | 0.80×0.95 | 0.30 | 0.150 mm | `U12-PS_SYNC` |
| `C1.2` | 0.90×0.95 | 0.30 | 0.150 mm | `U1-EN` |
| `R2.2` | 0.80×0.95 | 0.30 | 0.150 mm | `BOOT_N` |
| `U12.14` | 0.24×0.60 | 0.30 | 0.120 mm | `U12-PG` |
| `C16.2` | 0.90×0.95 | 0.30 | 0.085 mm | `GND` |
| `C8.2` | 0.90×0.95 | 0.30 | 0.075 mm | `GND` |
| `R26.1` | 0.80×0.95 | 0.40 | 0.041 mm | `+3V3` |
| `U14` (shield pad) | 0.34×0.62 | 0.25 | 0.033 mm | — |
| `C1.1` | 0.90×0.95 | 0.30 | 0.025 mm | `GND` |
| `R42.1` | 0.80×0.95 | 0.30 | 0.025 mm | `GND` |

Every one is **same-net** — these are deliberate fan-out vias placed in their
own pads, so there is no short risk. The risk is solder wicking at reflow, and
it is worst on `C13.1`, `R9.1` and `R5.1`, which are 0603 `+3V3` terminations
over a 0.40 mm barrel.

**This is not a board defect and no copper was changed to address it.** It is a
process choice, and it must be made before assembly. Two ways to close it, in
order of preference:

1. **Resin-plug and cap-plate the vias** (JLCPCB "via in pad" / POFV option, or
   equivalent). This removes the wicking path entirely, helps `R2.1` as well
   (§2 already welcomes it), and needs no data change. It carries cost and
   schedule.
2. **Local stencil aperture reduction** over the 20 pads listed above, so paste
   is not printed across the barrel. A stencil-only change; the PCB data is
   untouched. Use this if plugging is not available.

Doing nothing is a third option and is defensible for a two-unit demo build
where every joint can be inspected and reworked — but it must be a decision,
not an oversight. `U12.14` is the one to watch: a 0.30 mm barrel in a
0.24 × 0.60 mm fine-pitch pad is the least reworkable of the set.

---

## 6. Silkscreen

The board carries 138 instances of reference-designator text over a solder-mask
opening. **The released Gerbers resolve this in data:** they were plotted with
soldermask subtraction, so `F_Silkscreen` and `B_Silkscreen` contain a
clear-polarity block that removes silk everywhere a mask opening exists. No
silkscreen ink is printed on a solderable surface.

Do not re-plot the silkscreen without that subtraction.

Three silkscreen items are clipped by the board outline (`D7` reference, and
two `U1` outline segments that extend 0.15 mm past the west edge) and one
reference (`U4`) is 0.70 mm tall against the 0.80 mm board minimum. All four
are cosmetic and are accepted for this build.

---

## 7. Copper to board edge — `J2` exception

Minimum copper-to-edge on the board is **0.213 mm**, at the `J2` microSD shell
ground tab. This is vendor land-pattern geometry (Molex 5025700893), it is
scoped in the DRU by a dedicated `edge_clearance min 0.20mm` rule, and it is
**not** a relaxation of the 0.5 mm board-wide rule. Everything else clears
0.5 mm; the filled pours are inset 0.600 mm by construction.

**Fab confirmation item:** confirm 0.20 mm copper-to-outline is within house
capability for a routed edge.

---

## 8. Fabrication stack and remaining order choices

Verified against the board file:

| parameter | value | source |
|---|---|---|
| layers | 4 (`F.Cu`, `In1.Cu`, `In2.Cu`, `B.Cu`) | board |
| finished thickness | **1.6 mm** | board |
| solder mask | **GREEN** | §1, CTO ruling |
| min track width | 0.150 mm | measured |
| min drill | **0.20 mm** | measured, 9 PTH tools |
| min via | 0.50 / 0.25 mm | measured |
| min annular ring (plated) | 0.125 mm | measured |
| min hole-to-hole | 0.400 mm | measured |
| min mask web, different nets | 0.150 mm | measured |
| mask expansion | `pad_to_mask_clearance = 0` | board |
| via tenting | front and back, no per-via override | board |

**Order choices that are NOT decided and must not be assumed:**

* surface finish (ENIG vs HASL) — ENIG is the sensible default for the
  0.5 mm-pitch and fine-pitch parts on this board, but it is not chosen here
* outer / inner copper weight (1 oz assumed, not stated anywhere)
* impedance control — **not specified**; no controlled-impedance stack-up has
  been declared, and the RF paths have not been designed against one
* via plugging / POFV — see §5
* panelisation, tooling strips, fiducials — none present in the data
* IPC class and E-test — not specified
* MPN / manufacturer fields in the BOM are **empty** for every line; part
  selection is not captured in the schematic and must be supplied before any
  assembly quote
