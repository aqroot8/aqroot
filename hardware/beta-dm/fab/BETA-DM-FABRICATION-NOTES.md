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

**Ready to order the bare PCB: yes**, with the POFV process of §5 and the ENIG
finish of §8 on the order.

**Ready for PCBA: not yet.** Two gates remain: the manufacturer must confirm in
writing that they will fill and cap all 59 vias (§5), and the 40 generic passive
procurement groups still marked MPN SELECTION REQUIRED must be resolved (§8).

---

## 5. Open via barrels inside paste apertures — RESOLVED BY POFV

**CTO process ruling: the selected vias are NON-CONDUCTIVE EPOXY FILLED,
PLANARISED and COPPER CAPPED (POFV).**

The board carries **62 via / paste-aperture intersections across 59 distinct
vias**, re-derived from the released board by the same drill-edge criterion §2
uses for `R2.1`. Solder-mask ink plugging, tenting alone, and
accept-and-inspect are **not** acceptable resolutions, and no copper was
modified to avoid the process.

The complete list, the capability gate, the fabricator communication
requirements and the post-POFV stencil policy are in
[BETA-DM-POFV-CONTROL.md](BETA-DM-POFV-CONTROL.md) and
[BETA-DM-POFV-VIAS.csv](BETA-DM-POFV-VIAS.csv).

Capability gate result: **PASS** — drills 0.25–0.40 mm, via outer diameters
0.55–0.80 mm, annular 0.150–0.200 mm, aspect ratio 4.0:1–6.4:1, minimum
hole-to-hole 0.400 mm.

After POFV, **open barrels inside a fitted paste aperture: 0.**

`R2.1` itself is *not* in the set — its barrel sits 0.125 mm outside the paste
aperture, exactly as §2 documents. Including it in the same fill operation is
recommended but optional.

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

## 8. Fabrication stack, surface finish and remaining order choices

Verified against the board file:

| parameter | value | source |
|---|---|---|
| layers | 4 (`F.Cu`, `In1.Cu`, `In2.Cu`, `B.Cu`) | board |
| finished thickness | **1.6 mm** | board |
| solder mask | **GREEN** | §1, CTO ruling |
| **surface finish** | **ENIG** | **CTO target** |
| copper weight | **1 oz outer / 0.5 oz inner** | project architecture |
| via fill | **POFV on 59 vias** | §5, CTO ruling |
| min track width | 0.150 mm | measured |
| min drill | **0.20 mm** | measured, 9 PTH tools |
| min via | 0.50 / 0.25 mm | measured |
| min annular ring (plated) | 0.125 mm | measured |
| min hole-to-hole | 0.400 mm | measured |
| min mask web, different nets | 0.150 mm | measured |
| mask expansion | `pad_to_mask_clearance = 0` | board |
| **controlled impedance** | **NOT ordered** | see below |

**ENIG** is the selected finish: it gives the flat surface the 0.5 mm-pitch and
fine-pitch parts need, and it is the normal companion to filled-and-capped
via-in-pad structures. No incompatibility between ENIG and a 4-layer POFV
process is known. **If the fabricator's actual quote or configuration makes
ENIG incompatible with the selected 4-layer POFV process, stop and report — do
not silently accept HASL**, which would defeat both the fine-pitch assembly and
the flat capped-via surface.

**Controlled impedance is deliberately NOT ordered.** No authoritative AQROOT
document specifies a controlled stack-up, and the RF paths were not designed
against one. Adding an impedance requirement after routing is complete would be
inventing a specification the board was never designed to meet.

**Remaining order choices, still open:**

* panelisation, tooling strips and fiducials — none present in the data
* IPC class and electrical test
* solder-mask and silkscreen colour of the legend (mask colour itself is locked
  green by §1)
* **procurement**: see [BETA-DM-MPN-LEDGER.csv](BETA-DM-MPN-LEDGER.csv). Of 66
  fitted procurement groups, 22 carry an exact MPN, 4 have the part locked with
  only an order code or variant to confirm, and 40 generic passive groups
  covering 104 parts are marked **MPN SELECTION REQUIRED**. No MPN has been
  invented.
