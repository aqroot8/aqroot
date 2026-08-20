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

This board is **not yet released for fabrication**. GND pours are held and 31
fitted must-work non-GND connections remain open. These notes are recorded now
so the mask ruling and the critical R2 dam are not lost between passes.
