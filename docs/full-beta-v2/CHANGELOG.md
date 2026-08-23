# AQROOT Full Beta v2 — Changelog

Chronological engineering changes and why they happened. Newest entries at the
top. Each entry records what changed, not merely that something happened.

This file records **decisions and design changes**. Routine document edits are
not entries. A change that alters what gets built, or what may not be built, is
an entry.

---

## 2026-08-23 — Full Beta v2 power tree CAPTURED (FBV2-S1-001)

**The first Full Beta v2 design-file work.** `hardware/beta-v2/` is created, forked
from Beta-DM, and `01_power_tree.kicad_sch` now carries the Full Beta v2 power
architecture. Full analysis:
[`audits/2026-08-23-s1-power-tree-implementation.md`](audits/2026-08-23-s1-power-tree-implementation.md).

**Overall 31% → 34%. FBV2-S1 does NOT pass.** Its exit criterion requires *every*
schematic change in the migration order to be landed. One sheet of nine carries the
v2 architecture; the other eight are byte-equivalent copies of Beta-DM. What passes
is the task gate **FBV2-S1-POWER-TREE**.

### What is now in the file

136 parts on `01_POWER_TREE`, all with footprints assigned:

* **Battery reverse protection, P2** — `J4` → `F1` 5 A → `BAT_RAW` → `Q2` (stage A)
  → `BAT_MID` → `Q3` (stage B) → `BAT_SENSE` → `R75` 15 mΩ → `BAT_PROTECTED_P` →
  `U11` BAT. Controller `U18` LTC4368-1: `RETRY` grounded (latch-off), `UV` unused
  via 510 k to VIN per the datasheet, `OV` divider, 22 k/4.7 nF gate RC, `SHDN`
  pull-up with an N-FET pull-down, `D9` secondary negative clamp. Two stages in
  **two packages**, common-source pairs — **B-01 is closed at schematic level.**
* **Autonomous dead-cell recovery** — `U19` TLV7032 with a ratiometric polarity
  bridge (matched `D10`/`D11` Schottkys make the trip supply-independent at
  `BAT_RAW` = 0 and block pack drain when USB is absent), a handoff comparator
  asserting below ≈ 2.63 V of pack, a three-input **series** AND (`Q6`/`Q7`/`Q8`),
  `Q9` inverting `FAULT`, and `Q5`/`R95`/`D12` injecting current-limited,
  unidirectional charge. USB-powered and firmware-independent.
* **Accessory power** — `+3V3` → `U20` TPS22950C → `ACC_3V3_SW` and `BQ25185_SYS` →
  `U21` TPS61023 (4.99 V) → `U22` TPS22950C → `ACC_5V_SW`, both `FLT` pins wire-ORed
  onto `ACC_POWER_FAULT_N`. **D-088 BOM consolidation honoured exactly**: `L4` is the
  same Würth MPN as `L2`, `R99`/`R100` are the same 732 k/100 k divider as `R44`/`R45`,
  `C65`/`C66` mirror `C34`/`C35`. One boost family, one load-switch family, differing
  only in `R_ILIM` (1.5 k and 1.65 k, the values D-086/D-087 specify).
* **NFC no-respin source select** — `R106` 0 Ω **FIT** from `+3V3`, `R107` 0 Ω **DNP**
  from the boost.
* **Telemetry** — `VBUS_PRESENT` divided to 2.97 V at VBUS 5.0 V, so raw VBUS never
  reaches the expander; `LTC4368_FAULT_N`; `ACC_POWER_FAULT_N`; 19 test points.

### ERC: zero introduced

Beta-DM baseline **58** → Beta-v2 at resume **60** → Beta-v2 now **55**. The lists were
diffed, not counted. **Nothing was added.** Three inherited violations were retired: a
dangling root `BAT_PROTECTED_P` label, and two `isolated_pin_label` on
`BAT_CONNECTOR_P`, which was a one-pad net in Beta-DM and is now real.

**This is not "ERC clean" and must not be quoted as such.** 55 inherited violations
remain on the unmigrated sheets and belong to FBV2-S2.

Three defects were closed to get there: the missing `BAT_PROTECTED_P` label on the
`U11` pin-2 stub; a `PWR_FLAG` on `VREC_VCC`, whose drive arrives through `R84` and so
cannot be inferred by ERC — the electrical connection to VBUS was already correct and
no net was joined, split or renamed; and an orphaned wire and label left on the **root**
sheet when the `BAT_PROTECTED_P` hierarchical pin was removed.

### `U18` package corrected — a locked decision had been contradicted

`U18` LTC4368-1 had been assigned a **DFN-10 with an exposed pad**. FBV2-PWR-002 locks
the package policy for this circuitry: *"leaded and inspectable … no BGA, no WLCSP, no
bottom-terminated parts."* A DFN-10 is bottom-terminated, on the most safety-critical
part on the board. Corrected to `Package_SO:MSOP-10_3x3mm_P0.5mm` (the locked candidate
is `LTC4368IMS-1#PBF`, MSOP-10) in both the sheet and the project symbol library.
**The land pattern is still unverified** — that is FBV2-S2.

### `R_FB_TOP 1M` — an inherited net-name defect, fixed in v2

A literal net label reading `R_FB_TOP 1M` — a value annotation placed as a label.
`R39` is indeed 1 MΩ. The net is the TPS63020 `+3V3` feedback midpoint; renamed
**`V3V3_FB`** in `hardware/beta-v2/` only. Beta-DM is frozen and keeps it. All 56 labels
on the sheet were audited for embedded values, spaces, near-duplicate rails and isolated
single-pin nets; nothing else was found, and no correct name was touched.

### Fork provenance is now measured, not asserted

`checks/fork_equivalence.py` re-derives the classification of every forked file from
disk; `reports/FBV2-S1-fork-equivalence.md` pins the result. Sheets `02`–`09` are
byte-equivalent after normalising the project name **only**; `.kicad_pcb`, `.kicad_dru`,
both lib-tables and all 12 project footprints are **bit-identical**; `.kicad_pro` differs
by project name alone, so no design rule or netclass changed. `hardware/beta-dm/`,
`hardware/beta/` and `hardware/beta/mechanical/` are unchanged.

`checks/netclass_probe.py` had been copied without repointing and was still testing
**Beta-DM's** files from inside the v2 tree. Repointed; still PASS.

### Opened

**B-41** `NFC_SUPPLY` has no consumer — `U9` `VDD`/`VDD_TX` are still on
`NFC_5V_PA_PENDING` on sheet `04`, which this task could not modify. The v2 NFC supply
architecture is **half implemented**.
**B-42** the NFC source select is mutually exclusive **by fit state only**; fitting both
0 Ω links shorts `+3V3` to the boost output. Needs an assembly-note requirement.
**P-20** `R95` = 680 R against a locked 560 R. Injection falls to ≈ 6.9 mA, moving the
wrong way against **B-26**. Recorded, **not** silently changed — a value in a locked
architecture is changed by a ruling, not by a capture task.
**P-21** `OV` trip captured at 5.05 V against a documented ≈ 4.6 V.
**P-22** the standing *"no automatic KiCad file generation"* rule was overtaken: this
capture was scripted. Recorded in place and flagged for ratification or reinstatement
rather than treated as repealed.

### Recorded

**D-099** `U18` package corrected to MSOP-10. **D-100** net names describe nets, not
component values. **D-101** `TP34` added on `BAT_CONNECTOR_P`. **D-102** `PWR_FLAG` is
permitted only where a rail is genuinely driven and KiCad cannot infer it — never to
silence an error. **D-103** `BAT_PROTECTED_P` is local to `01_POWER_TREE`.

### Not done, and not claimed

No PCB work of any kind — `aqroot-Beta-v2.kicad_pcb` is still the Beta-DM board, bit for
bit, and does not match this schematic. No footprint verified. No MPN locked. Sheets
`02`–`09` untouched. `B-15` stays open: the `VBUS_PRESENT` divider exists but no charge
or VBUS telemetry crossing to `U2`/`U3` does.

---

## 2026-08-23 — Community connector CORRECTED and final-locked (FBV2-COMM-002)

Documentation only. No design file touched. `hardware/beta-v2/` was not created.

**This entry corrects an error rather than adding progress, and the percentage is
held at 31% accordingly.**

### Harwin `M20-7881242` is rejected

The CTO's lifecycle finding stands and is corroborated:
**`harwin.com/products/M20-7881242` returns HTTP 404** — the part number does not
resolve to a live catalogue item.

It should never have been recorded as locked. **The MPN was configured from the
Harwin catalogue's ordering scheme** (`M20-78` + `8` for double row + `12` per row
+ `42` for gold+tin) rather than taken from a live listing, and FBV2-COMM-001's own
limitations section said so in as many words: *"It should be verified against a
live distributor listing before the BOM is issued."* The flag was right; the part
was written into the locked documents anyway.

That gap is now closed by rule rather than by intention. **D-096: a part number
configured from an ordering scheme is a hypothesis, not a selection. Every MPN
entering a locked document must first be confirmed against a live manufacturer or
distributor record showing lifecycle status and stock.** It applies to every
subsequent selection in the programme.

`M20-7881242` has been struck through in place — not deleted — in
`CTO_DECISIONS.md`, `ARCHITECTURE.md`, `MECHANICAL_INTERFACE_SPEC.md`,
`PROGRESS.md` and the FBV2-COMM-001 changelog entry.

### Connector re-locked: Samtec `BCS-112-S-D-HE`

.100 in / 2.54 mm, **2 × 12 / 24 contacts**, **FEMALE** Tiger Claw™ dual-beam
receptacle, **horizontal (right-angle) entry**, **through-hole**, **30 µin
selective gold** in the contact area with matte tin on the tail (D-093).

**ACTIVE**, with **385 pieces shipping next-day** from Samtec at **MOQ 1**
($7.314 @ 1, $5.667 @ 100). Digi-Key lists the series as *Active*. Body
**30.48 (L) × 8.13 (D) × 5.33 (H) mm**. **4.6 A per contact** mated with TSW,
450 VAC / 636 VDC, **−55 to +125 °C**, glass-filled LCP UL94 V-0, UL E111594,
halogen-free, MSL 1.

**The footprint is new and is not interchangeable with anything already drawn:**
2 × 12 plated through-holes, 2.54 mm within a row, **7.87 ± 0.05 mm *between*
rows** — the horizontal-entry tails splay outward — with **0.71 mm drills** and a
27.94 mm end-hole span. B-29 is re-scoped to this pattern.

### Why the locked MPN is `-S` and not the `-L` that was proposed

This is what verifying the extended-life information was for.

Samtec's own design-qualification report (187544 Rev 1) gives **100 mating cycles
for BOTH** the 10 µin (`-L`) and 30 µin (`-S`) gold options. The E.L.P.
extended-durability data — **2 500 cycles** — is qualified **by similarity at
30 µin gold only**.

So at `-L` the community port would have been rated **100 cycles**, which is
*worse* than the 300 gold cycles of the part just rejected. For a
**user-swappable community port on a maker platform, mating-cycle life is a
first-order product parameter**, not a detail. The `-S` upgrade costs **$2.88 per
board at quantity one — roughly $14 across the first five boards** — for the only
plating with extended-life evidence behind it. Same body, same footprint, one
character of the part number. **`BCS-112-L-D-HE` is retained as a plating-only
cost-down alternate requiring no board change.**

**Recorded honestly as B-39:** the 2 500-cycle figure is **by similarity**, and the
only count formally qualified for BCS itself is **100 cycles**. Samtec must confirm
the rating for `BCS-112-S-D-HE` before the production run. The design assumption
for the first five boards is *"≥ 100 cycles qualified, 2 500 supported by
similarity at 30 µin gold."* **It is not claimed as 2 500.**

### Commodity 2.54 mm compatibility is preserved — with one rule

BCS accepts standard **0.64 mm (.025 in) square posts**, and the horizontal-entry
engagement window is **4.34 mm to 6.35 mm**. An ordinary 2 × 12 2.54 mm header with
a ~6.0 mm post qualifies. **Extra-long-pin headers (8.13 mm / .320 in posts) must
NOT be used** — they exceed the window. Reference accessory mate:
**`TSW-112-07-L-D`** (5.84 mm post), or a `-RA` right-angle variant for a coplanar
accessory. That one sentence is what preserves the entire reason for choosing
2.54 mm in the first place.

### Enclosure keying and load path locked (D-097)

The connector carries **no integrated key** — the BCS polarized-position option
exists but consumes a contact, which D-081 forbids. So: the socket face is recessed
**≥ 1.5 mm** behind the right wall and the recess walls form the shroud; an
**asymmetric rib/step on the upper edge only** blocks upside-down insertion (the
two mating rows are just 2.54 mm apart, so the key must be unambiguous rather than
a chamfer); the recess is **closed at both ends** with ≤ 0.3 mm clearance so a
one-column offset is mechanically impossible; a moulded **shelf and backing rib
capture the connector body**; and the accessory shell bottoms on an **enclosure
boss** so the insertion force is never carried by the 24 solder joints.

Insertion force is **≈ 33 N average** (24 × 1.39 N) with **withdrawal ≈ 20 N
average** — better than the ≈ 48 N maximum of the rejected part. These are Samtec
*averages*; Samtec's own note explains the peak occurs during the contact-spreading
stage and exceeds the average, so the load path is sized with that acknowledged
rather than assumed away.

### Z-stack rechecked, and it improves

| layer | Harwin (rejected) | **Samtec BCS** |
|---|---|---|
| Connector body above PCB | 8.10 mm | **5.33 mm** |
| **Column total of the 23.0 mm external budget** | **22.30 mm** | **19.53 mm** |
| **Spare** | **0.70 mm** | **3.47 mm** |

**The connector region is no longer the sole governing column** — it is now level
with the control region's 19.5 mm. **3.47 mm is real, usable clearance**, which is
the standard the ruling demanded. The 5.33 mm figure is read from the Samtec series
print and cross-checked three ways (the `-S-HE` view differs by exactly one 2.54 mm
row pitch; the vertical `-D-TE` body width is .20 in; the vertical insulation height
of 7.37 mm matches). It must still be confirmed against the individual 3D model at
FBV2-P1 — **M-09, downgraded to LOW**, and the conclusion survives even a 2.8 mm
error.

### Electrical allocation unchanged

The BCS has the same 2 × 12 topology with the mating rows stacked vertically, so
**D-082 and D-084 transfer unchanged.** Power and ground remain distributed across
columns 2, 5, 8 and 11; every power contact is still vertically GND-paired; all
3.3 V is in row A and all 5 V in row B; both native pins still flank the GND at
pin 9; the detect strap is still one 0 Ω link between pins 21 and 23. **The entire
mis-insertion argument carries over intact.**

### The three opportunity rulings

**O-1 APPROVED** (D-094). The two TPS22950C `FLT` outputs are open-drain and are
**wire-OR'd into `ACC_POWER_FAULT_N`** — one 100 kΩ pull-up, one PCAL9535A input at
`U3` P15. **`U3` P16 becomes `RESERVED_SPARE` with no function assigned**, brought
out to a test pad with a 100 kΩ pull-up so it reads a defined level and can be
pressed into service by a wire and a firmware change rather than a respin. Rev 1
now retains an expander resource for recovery. Rail attribution is by **controlled
isolation** (MX-5a): disable one rail and observe whether the fault clears. **B-37
is half closed** — `U2` still has zero spare.

**O-2 APPROVED** (D-095). **External I²C address `0x50` is reserved** for an
optional AQROOT accessory-identification EEPROM — **protocol reservation only, no
main-board hardware, and no accessory is required to carry one.** It joins the
reserved table with 0x38, 0x68, 0x36, 0x20 and 0x21. One thing flagged rather than
locked (**P-19**): the 24Cxx family spans **0x50–0x57**, so an AQROOT ID EEPROM
must strap A0–A2 = 0, and 0x51–0x57 remain unreserved.

**O-3 REJECTED** (D-095). The accessory TPS61023 5 V rail is **not** connected to
the NFC fallback — no DNP link, no shared node beyond `SYS`. Sharing the TPS61023
*device family* is the extent of the BOM consolidation, exactly as D-056 intended.

### Accessory limits, and the rule most likely to be misread

**`ACC_3V3_SW` = 400 mA total. `ACC_5V_SW` = 300 mA total** for the first five
boards (D-098). Later targets of 600–800 mA and 500 mA require measured bring-up
and a CTO ruling; the hardware change is one 0603 resistor per rail.

> **The duplicate contacts SHARE the rail limit. They do not double it.**
> `ACC_5V` pin 10 + pin 22 = **300 mA combined, not 300 mA each.** There is one load
> switch and one current limit per rail; the second contact halves contact
> resistance and eases routing, and adds no current budget. This must appear in
> accessory documentation in these words.

### Two new opportunities, flagged not locked

**N-1** — publish an accessory reference design: the 2 × 12 footprint, the
4.34–6.35 mm post-length rule, the detect-strap pattern, the shared-rail current
rule and a board-outline template that fits the recess. High value,
documentation-only, zero main-board cost — but it is a deliverable this task was
not authorized to create. **N-2** — accessory retention: withdrawal force is only
≈ 20 N average with no latch, so an enclosure friction detent or a captive fastener
is worth considering; it is a mechanical and ergonomic trade-off for enclosure CAD.

Full analysis:
[`audits/2026-08-23-community-connector-correction.md`](audits/2026-08-23-community-connector-correction.md).

---

## 2026-08-23 — Community expansion port and accessory power LOCKED (FBV2-COMM-001)

Documentation only. No design file touched. `hardware/beta-v2/` was not created.
**This was the last architecture closeout before schematic implementation.**

**COMMUNITY PORT LOCK = PASS. P-02, P-15, P-16 and B-08 all CLOSED.** No
architecture item now gates any schematic sheet.

### The 20-pin community port architecture is superseded

**D-059 and D-062 no longer describe this product** and nothing downstream may
cite them. The principles that survive are carried forward explicitly rather than
inherited: no duplicate GPIO (D-042), native and XGPIO documented distinctly
(D-045), no permanent raw `+3V3` (D-057), TPS22950C (D-058), native pair GPIO38 +
GPIO47 (D-063).

**New port: 2 rows × 12, 24 ACTIVE contacts, FEMALE on the device, male on the
accessory** (D-081). **10 XGPIO + 2 native + 2 I²C + 1 WAKE/ATTN + 2 switched
3.3 V + 2 switched 5 V + 4 GND + 1 `ACC_DETECT_N`** (D-082). Only the rails and
ground are duplicated, each a single net; **no GPIO is duplicated**. XGPIO falls
from 11 to 10, and **that one surrendered pin is exactly what pays for the fifth
accessory-control expander pin** — the arithmetic is tight to the pin.

### ~~Connector: Harwin `M20-7881242`~~ — **CORRECTED 2026-08-23, see FBV2-COMM-002**

> **This selection was WRONG and is superseded.** `M20-7881242` is obsolete and
> `harwin.com` returns HTTP 404 for it. The MPN had been configured from the
> catalogue ordering scheme rather than taken from a live listing — which the same
> entry's own limitations section had flagged. **The connector is now Samtec
> `BCS-112-S-D-HE`.** The reasoning below about *why keying must come from the
> enclosure at 2.54 mm* remains correct and still applies.

2.54 mm, 2×12, **female horizontal (right-angle) PC-tail socket**, through-hole
with two-point solder fixing, gold+tin. **3 A per contact, 300 mating cycles,
30 mΩ, 800 V AC proof, −40…+105 °C, UL94V-0.** Body ≈ 30.68 × 7.87 × 8.10 mm.
Mates with **any standard 2×12 0.64 mm square-post male header** (D-083).

A finding worth stating plainly: **at 2.54 mm there is effectively no mainstream
board-mount FEMALE connector with an integrated shroud and key.** The ubiquitous
shrouded, polarized 2.54 mm part is the *male* IDC box header, which is the wrong
gender. Samtec's Mini Mate `IPL1` is properly keyed, shrouded and latching — and
is a male box header whose mate is a Samtec part, so makers could not build
accessories from commodity components. 2.00 mm systems (Hirose DF11, Molex
Milli-Grid) do give a connector-side key and are ~20 % shorter, but they abandon
standard 2.54 mm male pins, which is the entire reason the pitch was chosen.

**So the key and the shroud come from the enclosure** — an asymmetric recess with
an off-centre lead-in rib, closed at both ends. That is explicitly permitted by
the ruling, it costs nothing in BOM, and it preserves the US$0.10 pin header as
the accessory interface.

### Pin ordering, and the mis-insertion proof

`1 XGPIO0 · 2 EXT_SCL · 3 ACC_3V3_SW · 4 GND · 5 XGPIO1 · 6 EXT_SDA ·
7 NATIVE_A · 8 XGPIO2 · 9 GND · 10 ACC_5V_SW · 11 NATIVE_B · 12 XGPIO3 ·
13 XGPIO4 · 14 WAKE_ATTN_N · 15 ACC_3V3_SW · 16 GND · 17 XGPIO5 · 18 XGPIO6 ·
19 XGPIO7 · 20 XGPIO8 · 21 GND · 22 ACC_5V_SW · 23 ACC_DETECT_N · 24 XGPIO9`
(D-084).

The ordering is not cosmetic. **Every power contact is vertically paired with
GND**, which is the constraint that forced power into columns 2, 5, 8 and 11 — so
**a row-swapped accessory can only ever produce a current-limited rail-to-ground
short, never 5 V on a logic pin.** All 3.3 V lives in row A and all 5 V in row B,
so a row-to-row bridge inside an accessory can short a rail to ground but never
5 V to 3.3 V. Both native fast pins flank the single GND at pin 9, which serves as
their return reference and separates them from each other. The I²C pair flanks the
GND at pin 4 for the same reason.

**The detect strap is one 0 Ω link between pins 21 and 23**, at the very end of the
row — the simplest accessory implementation possible. And because a flipped
accessory's strap lands in the other row, **a flipped accessory cannot assert
`ACC_DETECT_N`, so neither rail is ever enabled.** The mis-insertion case is
passively safe and self-announcing: the accessory simply does not come up.

A one-column lateral shift cannot be prevented electrically and is prevented
mechanically — the recess must be closed at both ends.

### Accessory detect

`ACC_DETECT_N` is pulled up to `+3V3` by AQROOT and grounded by the accessory
(D-085). Because the pull-up and the expander both run from `+3V3`, **detection
works with both accessory rails off**, which is the ordering the ruling demanded
and is what makes the flipped-accessory argument hold. **Neither rail may be
enabled unless detect is asserted.** As a free by-product, `U3`'s `/INT` is
wired-OR onto `WAKE_INT_N` → GPIO21, so **plugging or unplugging an accessory
raises an interrupt and can wake the device** at zero hardware cost.

### 3.3 V rail: TPS22950C confirmed line by line

`+3V3 → TPS22950C → ACC_3V3_SW` (D-086). Verified against SLVSFJ2B: `VIN`
1.8–5.5 V (so the same part works at 5 V too), **RCB = Yes** for the C variant,
`ILIM` **0.5–3.5 A** adjustable, auto-retry, TSD 170 °C, open-drain `FLT`, DDC
SOT-23-thin, 41 mΩ at 3.3 V, 550 µs slow turn-on so enabling the rail cannot step
`+3V3`. Default OFF with a **mandatory external 100 kΩ pull-down** — the internal
500 kΩ smart pull-down exists but the datasheet still says *"do not leave
floating"*.

### 5 V rail: a second TPS61023 and a second TPS22950C

`BQ25185_SYS → TPS61023 @ 5.0 V → TPS22950C → ACC_5V_SW` (D-087). **Not USB VBUS,
not the NFC fallback rail, tied to neither**; the only shared node is `SYS` on the
input side.

**Yes, reuse the TPS61023 — it is the right part, not merely the convenient one.**
0.5–5.5 V in, 2.2–5.5 V out, **3.7 A valley switch limit**, 94 % at 3.6 V → 5 V,
**true input-to-output disconnection in shutdown** at 0.1 µA, OVP, short-circuit
and thermal protection, SOT-563. Computed capability at 5 V is **≈ 2.3 A from a
3.0 V battery and ≈ 2.8 A from 3.6 V** — six to ten times what is being asked of
it. The limiter is the inductor, not the IC, so **1 µH with `I_sat` ≥ 3 A** is
specified (B-38). It shares its inductor, feedback divider and capacitors with the
DNP NFC fallback boost, so both circuits are one BOM line.

**Yes, use TPS22950C on both rails** (D-088). Same MPN, same footprint, same
safe-state pull-down, same `FLT` handling — **only `R_ILIM` differs**.

**Every back-feed path is closed**: accessory → boost (RCB, and constant reverse
blocking whenever `ON` is low, which is the default); `ACC_5V` → USB `VBUS`
(three series barriers — the switch's RCB, the boost's true disconnection, and the
BQ25185 power path); `ACC_5V` → `NFC_SUPPLY` (physically separate boost, separate
net, NFC on `+3V3` with its boost DNP on build 1).

### Why the published limits are below the CTO's targets on build 1

Recommended, **not fabrication-locked**: `R_ILIM` = **1.5 kΩ** on 3.3 V (≈ 0.76 A
typ) with a **published 400 mA continuous**, and **1.65 kΩ** on 5 V (≈ 0.69 A typ)
with a **published 300 mA continuous**.

Nothing about the switch or the connector prevents 800 mA — the TPS22950C is a
3.2 A part and the contacts are rated 3 A each. **The TPS63020 does.** The
TPS22950C is a *constant-current* limiter, so a shorted accessory holds `ILIM`
until thermal shutdown. Stacked on the internal worst case, `R_ILIM` = 1.15 kΩ
(600 mA published) drives `+3V3` to **101 % of the regulator's 2 A rating** —
foldback, brownout, SD corruption. At 1.5 kΩ the same fault reaches **86 %**. The
CTO's 600–800 mA target is met by changing one 0603 resistor once the internal
worst case is measured on real boards. That is D-049 applied exactly as intended.

**A structural advantage worth recording:** because the 5 V rail is boosted from
`SYS` rather than derived from `+3V3`, it consumes **none** of the TPS63020's 2 A
budget. Deriving it from `+3V3` would have cost roughly 500 mA of that budget.

### One honest caveat on fault visibility

SLVSFJ2B Table 9-1 is explicit: **`FLT` asserts on thermal shutdown and reverse
current only.** An output short leaves `FLT` **Hi-Z** while the device
current-limits. In practice a hard short dissipates 2.5–3.5 W in a SOT-23-thin
package and reaches the 170 °C TSD within tens of milliseconds, at which point
`FLT` does assert — but a **partial** overload that stays inside the thermal
envelope is invisible to the host. Firmware must not treat `FLT` as a complete
overcurrent indication (B-35). This is recorded because the ruling asked for
exactly this honesty rather than an invented fault output.

### Expander verdict: all five fit — exactly, with nothing left over

`U3` = **16/16**: `XGPIO0-9`, `ACC_3V3_EN`, `ACC_5V_EN`, `ACC_DETECT_N`,
`ACC_3V3_FAULT`, `ACC_5V_FAULT`, `SX1262_RXEN`. `U2` = **16/16**: the five pins
freed by removing HOME, the RGB LED and the RootProbe IRQ are exactly consumed by
`BQ25185_STAT1/2`, `MAX17048_ALRT_N`, `VBUS_PRESENT` and `SX1262_DIO1` (D-089).
Nothing was stolen — GPIO38 and GPIO47 remain the published natives, and SPI, I²S
and every internal MCU signal are untouched. One expander pin drives both the 5 V
boost `EN` and the 5 V switch `ON`.

**The design now has zero spare expander capacity anywhere (B-37).** That is the
price of fitting five accessory signals, and it is recorded as a standing
constraint rather than buried.

### Logic safety

**Every signal contact is 3.3 V CMOS. The 5 V power contact does not make any
signal 5 V-tolerant** (D-090). 100 Ω series on every XGPIO and both natives, 22 Ω
on the buffered I²C pair, 330 Ω on WAKE, plus a low-capacitance TVS array on the
two natives and the I²C pair — **the natives are the only contacts with a direct
path to the MCU**, and 5 V through 100 Ω is ≈ 11 mA into the clamp, inside
tolerance but with no sacrificial part in between. **Bidirectional level
translators are rejected**: they do not protect the A-side, they add direction
ambiguity on genuinely bidirectional GPIO, and they would imply 5 V logic is
supported, which it is not.

### B-08 closed with one MOSFET

A single N-channel pass gate between `WAKE_ATTN_N_HDR` and `WAKE_INT_N`, **gate
driven by `ACC_3V3_SW`** (D-091). The signal is only ever pulled low, so an N-FET
pass gate is sufficient. With accessory power off — the default — **a shorted
accessory pin can no longer hold `WAKE_INT_N` low, so internal button wake can
never be blocked.** Consequence, stated rather than hidden: accessory-initiated
wake now requires the rail to stay enabled during sleep (B-36).

### Power budget and the binding firmware contract

Naive simultaneity reaches **1 698 mA at `+3V3` = 85 % of the TPS63020's 2 A**
before transients — the P-15 concern, now quantified. With mutual exclusion
enforced the design case is **1 169 mA (58 %)**, or 1 314 mA (66 %) at the Wi-Fi
peak, and **1.65 A at the pack** (≈ 0.60 C on the 2 750 mAh class cell).

**MX-1…MX-9 are binding** (D-092): one high-power radio at a time; audio capped
during any transmit; rails detect-gated; 3.3 V enabled before 5 V by ≥ 5 ms; `FLT`
handled within 100 ms with a user action required rather than an endless
auto-retry into a short; both rails dropped on detect loss; 5 V disabled below
`V_BAT` 3.4 V and 3.3 V below 3.2 V; SPI-A arbitration; `U3` XGPIO interrupts
masked by default.

**A new thermal finding:** at 1.75 A the BQ25185 BATFET (115 mΩ) plus the
reverse-protection path costs **≈ 0.70 W and ≈ 0.40 V** inside a sealed
enclosure (B-34). BQ25185 supports 3.125 A discharge so the current is in spec,
but the loss and the `SYS` droop near a flat battery are real and are a further
argument for conservative first-build accessory limits.

### Mechanical: the connector region is now the governing Z column

2.0 shell + **8.10 connector** + 1.6 PCB + 8.0 battery + 0.6 + 2.0 shell =
**22.30 mm of the 23.0 mm external budget — 0.70 mm spare** (M-09). That displaces
the control region's 19.5 mm. Relief exists: the battery is 60 mm wide in a 75 mm
cavity, so the outer ~5 mm of each PCB edge has nothing behind it. The 8.10 mm
figure is read from the series catalogue and **must be re-confirmed against the
individual part drawing at FBV2-P1**. Insertion force reaches **48 N** (24 × 2.0 N
max) and must be carried by an enclosure boss, not by the PCB joints (M-10).

### Three opportunities flagged, deliberately not locked

**O-1** wire-OR the two `FLT` lines to recover one expander pin — slack versus
per-rail diagnostics, in a design that now has zero spare anywhere. **O-2** reserve
an I²C address for an accessory-ID EEPROM — zero hardware cost, but a
product/protocol decision that interacts with P-18. **O-3** a DNP 0 Ω link letting
the accessory boost also serve the NFC 5 V fallback — saves a part, but couples
NFC PA current to the accessory load, which is exactly what D-056 avoided. All
three need a CTO ruling.

Full analysis:
[`audits/2026-08-23-community-expansion-closeout.md`](audits/2026-08-23-community-expansion-closeout.md).

---

## 2026-08-23 — Display, connector and backlight LOCKED (FBV2-DISP-002)

Documentation only. No design file touched. `hardware/beta-v2/` was not created.

**FBV2-DISP-LOCK = PASS. M-06 CLOSED. M-07 CLOSED.** Sheet
`03_spi_a_display_sd` is unblocked, which removes the last gate on FBV2-S1.

**Display LOCKED: EastRising `ER-TFT035IPS-6` + `ER-TPC035-6`** (D-074) — 3.5″
IPS 320×480, **ILI9488** COG, **FocalTech FT6236** capacitive touch at **I²C
0x38**, assembled outline **56.54 × 84.96 × 3.95 ± 0.25 mm**, active
48.96 × 73.44 mm, 300 cd/m², 500:1, 80/80/80/80.

**FPC LOCKED (D-075): one 50-pin tail, 0.50 mm pitch, BOTTOM CONTACT,
0.30 ± 0.03 mm thick, 25.5 ± 0.15 mm wide, 30 ± 0.5 mm free length.** Display
*and* touch leave on that single tail — touch on pins 44–47. All three of the
parameters D-049 forbids guessing are printed in the vendor's own datasheet
(Rev 2.0, 18-Aug-2025). No second connector, no soldered flying lead.

**`J1` LOCKED: Hirose `FH69-50S-0.5SH`** (D-076). The compatibility argument is
the point: it is made from **both manufacturers' drawings**, not from a matching
pin count. The display tail is 0.30 ± 0.03 mm and the connector requires
0.30 ± 0.05 mm; the tail is bottom-contact and **FH69 accepts top *and* bottom
contacts** on a 2-point design. **The classic dead-first-article failure — an FPC
facing the wrong way — cannot occur with this pair.** Digi-Key: Active, 1,907 in
stock, US$2.16 @ 1, MOQ 1.

**`J1` is laid out on the FH12-horizontal / FH52E standard land pattern, not on
FH69's dedicated pattern** (D-077). Hirose states FH69 fits that pattern, and
doing so makes **`FH52E-50S-0.5SH` (LCSC `C7465440`, JLCPCB-orderable)** a genuine
drop-in second source with no board change. That is D-049 applied to a connector.

**D-073 is resolved, and the answer is that the connector was never the problem.**
As a by-product, `ER-TFT035-6` with CTP measures **56.54 × 84.96 mm** — the same
figures to 0.01 mm as Chenghao's `CH350HV40A-CT`, with the same active area and
the same 6-LED parallel backlight. The two are, to a high confidence, the same
glass from the same upstream supplier, and Chenghao's *"pin pitch 0.3 ~ 0.4 mm"*
is very likely a datasheet defect conflating tail thickness (0.3 mm) and conductor
width (0.35 mm) with pitch. **That is an inference, not a proof**, and Chenghao
stays rejected — a supplier that cannot state its own pitch cannot be designed
against. What it does retire is the fear that the *family* uses a sub-0.5 mm
pitch. It does not.

**ST7796S is formally rejected on availability, not on merit** (D-078). Eleven
suppliers were surveyed — Newhaven, Riverdi, EastRising, Winstar, Raystar, Focus
LCDs, DisplayModule, VIEWE, Chenghao and the hobby vendors. **No ST7796S / ST7796U
3.5″ 320×480 IPS module with a capacitive touch panel, a named touch controller
and a complete public FPC specification exists from a production supplier.**
ST7796S appears only on hobby breakouts (excluded by the brief), on touch-less
LCMs, or with ambiguous FPC data. Every candidate that meets the full requirement
set carries ILI9488. The cost is quantified: **+50 % SPI-A traffic; 46 ms
(21.7 fps) for a full 320×480 frame at 80 MHz FSPI IO_MUX against 31 ms for
ST7796S.** Accepted for menus, graphs, logs and status screens.

**Rejections, each on a recorded ground:** Riverdi `RVT35HITNWC00-B` — 59.56 ×
**93.34 × 5.66 mm** and a **10-LED, 14–16 V, 100 mA** backlight (~1.5 W). Focus
LCDs' IPS parts — **End of Life / NRND**, US$109 for 8 pcs. Focus `E35RG73248…-C`
— 61.90 × 91.04 mm and **two** connectors. Winstar `WF35UTYAIDNN0` and Raystar
`RFI350U-AYW-DNN` — excellent LCMs, **no touch variant**. Newhaven — current 3.5″
IPS is **640×480 MIPI DSI**, which the ESP32-S3 cannot drive. DisplayModule
`DM-TFT35-431` — ST7796S but **no documented touch controller**.

**Backlight closed (D-079). The TPS61169 stays, and for a structural reason:**
`U17` boosts from **`+3V3`**, not from the battery. A 6-LED *parallel* array sits
at only ~3.0–3.2 V, and a boost cannot regulate below its own input — had the
driver been fed from `VSYS` (3.0–4.35 V) this panel would have forced a buck-boost
or a linear sink. From a fixed 3.3 V, a modest ballast lifts the output to
~4.15 V and the converter stays firmly in boost at every corner.

New values: **`R69` (RSET) 2.55 R → 1.87 R ±1 %** → 109 mA typ, 100.5–117.6 mA
over the VREF band, always under the panel's 120 mA maximum. **`R70`–`R73`
4 × 39 R → 4 × 33 R, all in parallel on the single `LED_A` net** = 8.25 R, which
reuses the existing footprint group, quarters per-part dissipation to 24.6 mW and
leaves three DNP-able trim steps. Margins: **switch peak 263 mA against a 1.2 A
limit (4.6×)**; `L3` 12.5×; `D8` 2.1×; `C44` unchanged at 1.28× against the 39 V
OVP worst case. `L3`, `D8` and `C44` are all retained.

**The backlight is cheaper than FBV2-DISP-001 feared.** That audit assumed
6 × 20 mA and predicted roughly +50 %. The real panel is specified at **120 mA
maximum / 90 mA life point across six chips**, so per-LED current *falls* from
20 mA to 15 mA. At default brightness the pack sees **129 mA against Beta-DM's
118 mA — about +9 %** for 1.56× the screen area and 2× the pixels, and LED life
improves rather than degrades.

**Electrically the migration is free** (D-080). 4-wire SPI is selected by hard-tying
IM2/IM1/IM0 = 1/1/1 to VDDI, and the panel's SCK/MOSI/MISO/CS/DC/RESET land on the
existing GPIO12/11/13/10/14 and `U60 P04`; touch lands on the existing I²C bus with
the **same FT6236 at the same 0x38**, `TOUCH_RST_N` still on `U60 P00`. **Zero new
native GPIO. No new rail. No level shifting. No SPI bus merge.** B-10 is unaffected.

**One caution, mitigated by design:** the ILI9488's `SDO` behaviour on a bus shared
with microSD is not stated in the datasheet, and ILI9488 modules have a field
reputation for holding SDO driven. A **0 R `R_SDO` series link plus a test point**
lets the display be made write-only at bring-up without a respin, a trace cut or a
bodge (B-28).

**Mechanical PASS with margin.** 56.54 × 84.96 × **4.20 mm max** inside the
60 × 90 × 4.5 envelope; 9.23 mm of cavity each side; **70.04 mm** of the 155 mm
cavity height left for the D-pad, A/B and the mic aperture; front stack 7.30 mm
plus the 8.0 mm battery = 15.30 mm of the 18.5 mm cavity, **3.20 mm spare**. The
6 mm FPC bend corridor is retained and is generous against the ≥3 mm a 0.30 mm
tail needs. **One new placement coupling:** at 2.3 mm the connector cannot sit in
the display shadow (0.8 mm limit), so it competes for the space below the panel
(B-33 / M-08).

**Procurement risk LOW**, with two MEDIUM items that are closed on the purchase
order rather than in the design: the vendor also sells a **CST340** touch panel
for this size, so the PO must name `ER-TPC035-6`; and the datasheet carries a
**"Backlight Update" revision**, so Rev 2.0 must be archived in-repo and cited by
revision in the MPN ledger. Against that, EastRising publishes a written
**≥10-year continuity-supply commitment** — the only candidate in the survey that
does — at **MOQ 1**, in stock, **US$15.57 per display in prototype quantity**.

Full analysis:
[`audits/2026-08-23-display-procurement-lock.md`](audits/2026-08-23-display-procurement-lock.md).

---

## 2026-08-22 — Display size ruled 3.5″; MPN deliberately not locked (FBV2-DISP-001)

Documentation only. No design file touched.

**Battery envelope LOCKED** at 60 × 75 × 8.0 mm, ~2500–3000 mAh (D-071).
**Display size LOCKED at 3.5 inch** (D-072). **Display MPN and J1 are deliberately
NOT locked** (D-073), and the reasoning matters more than the conclusion.

**Was the old J1 ever compatible? UNPROVEN — not YES, not NO.** No source
obtainable to this audit states the CH280QV10-CT's FPC pitch, and the Phase-1
mechanical audit independently recorded the same gap. **J1 was selected without a
display FPC drawing on file and has never been proven to mate.** Its footprint is
verified against the *Hirose* drawing, which proves the connector footprint is
right and proves nothing about the display. The CTO's suspicion is strengthened by
the successor part in the same family quoting **0.3–0.4 mm**, not 0.5 mm — if that
is the family convention, the 2.8″ part may never have mated either.

**The 3.5″ candidate CH350HV40A-CT was verified and it fits** — 320×480 IPS,
ILI9488, 56.54 × 84.96 × 3.97 mm, active 48.96 × 73.44 mm, 50-pin, 6-LED parallel
backlight. It clears the ≤60 × 90 × 4.5 mm envelope and leaves 70 mm of the
155 mm cavity height for the controls. **Four defects stop it being locked:**
ILI9488 **cannot send RGB565 over SPI** and takes 3 bytes/pixel, a 1.5× bandwidth
penalty an ST7796S-class part simply does not have; the vendor states **"pin pitch
0.3 ~ 0.4 mm"**, a *range*, which directly violates D-049's *"no dependence on
undocumented pin pitch"*; module thickness is quoted as both 3.97 and 2.4 mm in the
same document; and the touch controller is never named.

**What is locked instead is the interface requirement** — 3.5″ IPS 320×480,
ST7796S/ST7796U preferred, I²C CTP of the FT6336U class, single documented FPC
pitch with 0.5 mm strongly preferred. **The mating connector cannot be chosen
until the panel's pitch, pin count and contact side are confirmed**; choosing one
now would repeat the exact mistake this audit found.

**ESP32-S3 SPI verdict: PASS, with no bus merge and no radio change.** The panel
touches only SPI-A; SPI-B keeps the radios and NFC. Usefully, `SPI_A_MOSI`/`SCK`/
`MISO` sit on GPIO11/12/13 and `DISP_CS` on GPIO10 — exactly the ESP32-S3 **FSPI
IO_MUX** pins, so the display bus already has the 80 MHz fast path rather than the
40 MHz matrix route. At 80 MHz an ST7796S-class controller writes a full 320×480
RGB565 frame in ~31 ms, the same as today's 2.8″ panel at 40 MHz — **the user
experience does not regress.** With ILI9488 it is ~46 ms instead.

**Backlight rises from 4 LEDs to 6 (+50 %)**, taking browsing draw from ~100 mA to
~130 mA — but D-071's larger pack takes capacity from 2000 mAh to ~2750 mAh, so
**runtime is flat to slightly better.** Neither ruling alone would have achieved
that. The TPS61169 `RSET` (2.55R) and its current capability must be re-derived for
six LEDs (M-07).

M-01 and M-02 closed. **M-06** (display MPN / FPC) and **M-07** opened. FBV2-A2
stays PASS. **No gate passed, so the percentage holds at 25 %.**

---

## 2026-08-22 — Mechanical interfaces frozen; **FBV2-A2 PASSED** (FBV2-MECH-001)

Documentation only. No design file touched. `hardware/beta/mechanical/` was read
only and is unmodified.

**FBV2-A2 = PASS.** Three of twelve gates now pass. New authoritative pre-CAD
source: `mechanical/MECHANICAL_INTERFACE_SPEC.md`, with every row marked LOCKED,
TARGET or TBD — and **nothing marked LOCKED on the strength of derivation alone.**

**Device orientation was resolved, not assumed.** The Beta-DM board is 74 × 155
(portrait) and the external target is 80 × 160; the axes map one to one. The
device is portrait, so the front is display-above-controls.

**23 mm passes with 3.5 mm spare**, and the interesting question was what to do
with the margin. The governing column is the control region with the battery
behind it: 19.5 mm of 23.0 mm. Left as air the margin is wasted; allocated to the
battery it raises the pack from the 5–6 mm a 2000 mAh cell needs to **8.0 mm**,
i.e. the **2500–3000 mAh class** — a 25–50% runtime gain for zero external size
change.

**The Beta-DM outline cannot be reused, and the reason is stark.** Against the
derived 75 × 155 mm cavity, the 74 × 155 mm board leaves 1.0 mm of clearance in X
and **zero in Y**. There is no room for the shell lip, six bosses, ribs or
assembly access. Combined with the v2 content changes — 20-pin connector, P2
four-FET stage, dead-cell recovery branch, NFC crystal and matching, restored IR,
new expanders — the verdict is **re-floorplan with a different outline**, targeting
**70 × 148 mm**. This is the PCB revision Field Slate v3 required in July and never
received.

**NFC and battery are separated in plan rather than stacked.** Because the display
occupies the front upper third, the rear upper third is free — NFC loop there
(45 × 45 mm), battery in the rear lower two-thirds. **Zero overlap is the policy,
not a mitigation.** Ferrite is still specified, because once the battery moves away
the PCB ground pour becomes the dominant near-field threat. The loop grows from
Beta-DM's measured 26 × 20 mm to 45 × 45 mm — a **3.9× area increase**, which is
where the range lost to 3.3 V NFC operation (D-055) is won back. Two constraints
fall out: the mid-span bosses and the left-side antenna storage channel must both
stay below Y = 100 mm.

**Acoustics and IR specified to interface level.** The ICS-43434 is bottom-port, so
the mic path is PCB hole → gasket → shell aperture with the tunnel ≤2.5 mm; longer
tunnels roll off exactly the frequencies that carry speech. Speaker rear-firing,
Ø20 × 4 mm, with a 1.5–2.0 cm³ **sealed** rear cavity, ≥60 mm from the mic and on
the opposite face. IR emitter and receiver ≥15 mm apart on the top edge with a
**mandatory opaque barrier** — separation alone does not fix self-blinding,
because the internal reflection path is the one that actually causes it.

**Honest limits recorded rather than glossed:** nothing is CAD-verified, several
component figures are class-typical, and the display is the weakest input — its
50 × 69 mm figure is a measured *keepout*, not a vendor outline, and the FPC bend
stack is unknown. That is why display size is raised as an open item.

Two CTO decisions opened: **M-01 display size** (the cavity comfortably accepts
3.2″ or 3.5″; blocks PCB floorplanning but not schematic migration) and **M-02
battery capacity target**. **P-07 closed.**

Progress 20% → 25%. Next gate: **FBV2-S1, schematic migration.**

---

## 2026-08-22 — Battery safety architecture finalised; **FBV2-A1 PASSED** (FBV2-PWR-002)

Documentation only. No design file touched.

**FBV2-A1 = PASS** — the first gate to pass since FBV2-A0, and the largest
remaining architecture unknown. All six criteria closed, all 13 power/fault cases
defined, no power-tree branch TBD. Next gate: **FBV2-A2, mechanical interface
freeze.**

**Candidate B selected and specified to component level** (D-065). The design
turns on one structural fact: **no passive switch can distinguish a 0 V cell from
a reversed one** — an N-FET referenced to a positive rail sees V_GS ≈ +3 V at 0 V
and ≈ +6.7 V at −3.7 V, so a reversed cell turns it *harder on*; the P-FET
arrangement fails the same way. An active, GND-referenced comparison is therefore
mandatory. The chosen sensing network is a **matched ratiometric bridge** whose
trip condition reduces to **V_BAT = 0 independent of VBUS** — supply-independence
by construction rather than by trimming. Handoff is taken from the **LTC4368
`FAULT` pin**, which is asserted precisely while VIN is below UVLO, so the
protection controller itself decides when it has taken over — no extra threshold,
no possibility of both paths being active. Recovery current **5–10 mA** (~0.004 C),
supplied from **VBUS rather than SYS** so the branch is dead by construction
without USB and costs **zero battery-side standby**.

**The pass path changes to P2** — two back-to-back stages in **two separate
packages**. A precise finding corrected the earlier account: **P1 fails one of the
two single-FET-short cases, not both.** A short on the `BAT_RAW`-side FET is
already blocked by its partner; it is specifically the **`BAT_PROT`-side** FET
whose short lets a reversed cell through. P2 leaves one complete back-to-back pair
intact under any single short, and additionally keeps the LTC4368's electronic
breaker functional with a FET shorted. Two die sharing one leadframe cannot be
called independent, so the two stages must not share a package.

**The previous fuse-and-clamp compliance argument is withdrawn as invalid.** A
Schottky sitting at ≈0.8–1.0 V does not protect a −0.3 V absolute maximum, and
ruling D was right to refuse it. With isolation doing the work, the **clamp is
demoted to secondary** duty (ESD, transient, double-fault) and the **fuse is
resized 3 A → ≈5 A**, because it is now a backstop that must not pre-empt the
3.33 A electronic breaker. Its one genuinely irreplaceable role is a harness short
between `BAT_RAW` and GND *upstream* of the FETs, where the breaker cannot act.
**PTC remains rejected.**

**Honest residual, recorded rather than smoothed over:** Candidate B is *not*
tolerant to every single failure — four failures each individually enable current
into a reversed cell. It meets the requirement as written because `R_LIM` bounds
every one to **≈13 mA (~0.007 C)**, `D_REC` keeps the branch unidirectional under
all faults, and the condition is self-annunciating. A fully redundant variation is
documented and **not** recommended: it would trade that bounded residual for a
permanent oscillation in the far more common battery-absent state.

**PCAL9535APW,118 locked for both expanders** (D-066), closing the four facts the
previous audit could not verify. **GPIO38 + GPIO47 remain locked** (D-067).

Progress 15% → 20%, held deliberately low: two of twelve gates, both paper, with
mechanical untouched.

---

## 2026-08-22 — Power architecture closed to a single open decision (FBV2-PWR-001)

Documentation only. No design file touched.

**Expander family locked** (D-061): both `U2` and `U3` become NXP
`PCAL9535APW,118` (LCSC C2669683) — an architecture lock, with the land-pattern
audit still required before fabrication. **Native pair locked** (D-063):
`NATIVE_A` = GPIO38, `NATIVE_B` = GPIO47, with `SX1262_DIO1` moving to the
internal expander and `BUSY` staying native. GPIO43 leaves the public connector.

**The SX1262 lock condition was met from a primary source.** Semtech
`DS.SX1261-2.W.APP` Rev. 1.2 §13.3.4 states verbatim that a DIO mapped to one IRQ
clears when that flag clears, and that with several IRQs mapped *"the DIO remains
set to one until all bits mapped to the DIO in the IRQ register are cleared."*
DIO1 is level-held, so an expander input with no capture register can service it.

**Two prior positions were corrected by the full LTC4368 datasheet.** P-13 is
**closed**: inrush is a designed parameter, `I_INRUSH = (C_OUT/C_GATE) ×
I_GATE(UP)`, giving ≈350 mA against a 3.33 A trip — and RETRY latch-off applies
to *forward* overcurrent only, while reverse faults reconnect automatically once
VOUT falls 100 mV below VIN. The earlier concern rested on an incomplete reading.

**The fuse-and-clamp language correction (D-064) was justified, and the analysis
vindicates it.** At the 20–25 A a 1S pack can deliver, a Schottky clamp sits at
≈0.8–1.0 V — about **3× the BQ25185 `BAT` −0.3 V absolute maximum**. The clamp
improves the excursion roughly fourfold but does **not** bring it inside the
limit. Both elements remain **REQUIRED** — the fuse because without it the clamp
is a permanent short across a Li-ion cell — but the residual is now named (P-12)
rather than assumed away. A **PTC is rejected** for this position: too slow, and
its auto-retry re-applies the fault every cycle.

**Dead-cell recovery is now the only thing blocking FBV2-A1.** The LTC4368 cannot
help here — VIN is the supply pin with a 2.2 V UVLO, and VOUT is a sense input
whose charge-pump role only engages above ~5 V, so system-side power cannot run
the controller. A single MOSFET also cannot distinguish a 0 V cell from a
reversed one: **both turn it more on**, so an explicit GND-referenced sensing
element is mandatory. Four candidates analysed; **Candidate B** — a
hardware-qualified comparator interlock, no firmware dependency, ~0 A into a
reversed cell — is recommended for the product, with service-only accepted as
defensible for the first five boards. **Not approved, so the gate is not passed.**

Progress 13% → 15%. **FBV2-A1 FAIL, 5 of 6 criteria closed.**

---

## 2026-08-22 — Critical architecture reconciled; no-respin policy established (FBV2-ARCH-002)

Documentation only. No design file touched.

**New standing policy: FIRST FIVE FULL BETA PCBAs — NO-RESPIN RECOVERY POLICY
(D-049).** Full Beta v2 Revision 1 must be designed so that reasonable
configuration and performance uncertainty is recoverable through *planned*
component rework — DNP/FIT options, 0 Ω source-selection links, accessible tuning
passives, test points — rather than through a board respin. Safety-critical power
paths are explicitly excluded: no ad-hoc bypasses around battery protection
merely for reworkability.

**An independent second-opinion review was archived verbatim** at
`reviews/2026-08-22-independent-cto-power-nfc-review.md`, marked
**ADVISORY — NOT AUTOMATICALLY AUTHORITATIVE**. It corrected the primary
engineering work on three points, and the corrections were accepted:

- **Discrete back-to-back N-FET reverse protection is withdrawn.** It is not
  under-specified but *unrealisable at 1S* — available V<sub>GS</sub> from any rail
  on this board is 0.3–1.5 V, and the P-channel variant that avoids a charge pump
  turns both FETs hard on into a reversed cell, creating the fault it was added to
  prevent. **LTC4368-1 adopted** (the `-2`'s −3 mV reverse trip would block
  charging outright).
- **"STAT1 only" was wrong, and so was the premise behind it.** BQ25185 SLUSF65A
  §7.3.10 places the STAT2 toggle in the **battery-absent** limit cycle, not in
  charge-complete/sleep — those are one state with both pins HIGH. STAT1 alone
  conveys only fault/no-fault. **Both are exposed**, with the wake-storm solved by
  changing the expander rather than by dropping a signal.
- **TPS22913B/C was the wrong replacement** for TPS22918 — DSBGA 0.9 × 0.9 mm only,
  and no current limit. **TPS22950C** adopted: RCB confirmed for the C variant
  (the L variant has none), leaded SOT-23-thin, adjustable limit, thermal
  shutdown.

**Verified this pass.** The TPS61169 `CTRL` pin has an internal **pull-down**,
which closes the last blocking condition on moving `DISP_BL_CTL` to GPIO46 and
frees GPIO47. **GPIO38 replaces GPIO43** as `NATIVE_A`, removing ROM-UART
push-pull contention from the public connector entirely.

**The mandatory power/fault state table now exists** — eleven cases across USB,
battery, power-switch and accessory states. Cases 1, 2, 5, 6, 8, 9 and 10 are OK
or correctly blocked. **Case 4 (dead cell) and Case 11 (hot insertion) are
UNRESOLVED and block schematic lock**, and Case 7 (shorted pass FET + reversed
cell) is only survivable with a series fuse and a Schottky clamp, which are
therefore required rather than optional.

**NFC ships at 3.3 V with a full no-respin 5 V fallback.** Two mutually exclusive
0 Ω links guarantee the sources can never be shorted. Pre-fit the inductor, the
FB divider and both boost capacitors; keep the TPS61023 and the 5 V link DNP.
Conversion is 3–9 soldering operations with exactly one fine-pitch part — no BGA
or QFN rework, no trace cuts, no bodge wires.

**Volume Up/Down removed from the Full Beta v2 mechanical requirements.**

**FBV2-A1 assessed: CANNOT PASS.** Four of eight criteria are resolved (20-pin
map, default NFC, NFC fallback, accessory power). Four remain — expander family,
native pair, reverse-protection topology completeness, and power-tree stability —
and three of those close with document reads. Progress 10% → 13%.

---

## 2026-08-22 — Architecture direction locked, blockers verified (FBV2-ARCH-001)

Documentation only. No design file touched. Commit `890db0b` pushed to
`origin/master` (`b8b5ebd..890db0b`).

**CTO rulings A–K recorded** as D-018, D-026, D-033…D-041, D-046…D-048. Four
pending decisions closed: P-05 (RGB removed), P-06 (RootProbe IRQ retired),
P-08 (IPEX → pigtail → bulkhead), P-09 (LoRa deep-sleep wake not required).

**Verification against vendor datasheets changed three things.**

- **The NFC supply split cannot be built.** ST25R3916 DS12484 Rev 3 p. 39: *"VDD
  and VDD_TX must be connected to the same power supply"*, with the difference
  capped at ±0.3 V absolute maximum. The requested 3.3 V / 5 V split would apply
  1.7 V across that pair. **The as-built rail assignment is correct**, and the
  pre-design audit's recommendation to change it was wrong and is withdrawn. The
  real residual question — what VDD does while the boost is off — is now P-10,
  with a 3.3 V-only NFC option that would delete eight components.
- **The proposed native-GPIO reclaim would have broken recovery.** Moving
  `NFC_IRQ` to GPIO46 makes ROM download boot conditional on NFC interrupt state,
  because the ST25R3916 IRQ is active-high, latches until read over SPI, and is
  not reset by an ESP32 reset. Substituted: move `DISP_BL_CTL` to GPIO46 and
  expose **GPIO47** as `NATIVE_B`. GPIO47 is strictly better — no power-up glitch,
  20 mA drive, unrestricted priority — and D-041 removed the only reason to want
  GPIO18's RTC capability.
- **`TPS22918` fails the accessory-isolation requirement.** Its integrated body
  diode conducts VOUT→VIN, so a powered accessory can back-power `+3V3`.
  Replacement identified in the TPS22913B/C class.

**Two prior findings were confirmed wrong and are corrected in the record:** the
TCA9517A *does* guarantee high-impedance pins when powered off and 5.5 V
tolerance while unpowered, so it passes; and the TPS61023 *does* provide true
load disconnect plus integrated output OVP.

Reverse-polarity architecture compared across three candidates and **discrete
back-to-back N-FETs recommended** over the LTC4368-1, primarily on quiescent
current (sub-µA vs ~80 µA) — flagged for independent second opinion as
instructed. A reverse-current-blocking load switch was evaluated and
**disqualified for this position**: it would block the charging direction.

Progress raised 8% → 10%. **No gate passed.** FBV2-A1 remains IN PROGRESS with
P-01, P-02, P-04, P-07 and P-10 open. **FBV2-A2 (mechanical interface freeze)
recommended as the next gate** — it is the long pole and nothing blocks it.

---

## 2026-08-22 — Full Beta v2 engineering record established (FBV2-DOC-001)

Documentation infrastructure only. No design file was touched.

- Created `docs/full-beta-v2/` as the authoritative engineering record.
- Established the precedence rule: `CTO_DECISIONS.md` outranks audits, which
  outrank architecture notes, which outrank transcripts.
- Made `transcripts/` append-only.
- Preserved the 2026-08-22 pre-design engineering audit verbatim under
  `audits/`, pinned to repository HEAD `b8b5ebd`.
- Preserved the FBV2-AUDIT-001 CTO prompt and Claude Code response verbatim
  under `transcripts/`.
- Opened the gate table FBV2-A0 through FBV2-B3 and recorded FBV2-A0 as PASS.

---

## 2026-08-22 — Full Beta v2 direction established

- **Beta-DM fabrication paused before payment.** The design-side release stands
  and no money has been committed. Beta-DM is retained as the preserved fallback
  and manufacturing baseline, not cancelled.
- **Full Beta v2 made the primary design.**
- **Decided not to blindly continue frozen Full Beta.** Its freeze recorded 281
  unconnected items and 58 ERC violations; it is a feature reference, not a
  fabrication-ready baseline. Its decisions are re-verified rather than
  inherited.
- **Beta-DM becomes the implementation / manufacturing baseline.** Full Beta v2
  is derived from it — its resolved MPNs, its validated blocks, its routing and
  DFM lessons.
- **Removed HOME from the future product.**
- **Volume Up / Down removed from the enclosure plan.** Audit finding: they
  never existed electrically. `SW2`-`SW8` are UP / DOWN / LEFT / RIGHT / A / B /
  HOME. Volume controls existed only in Field Slate v5 section 5, which must be
  corrected so enclosure CAD is not driven by phantom controls.
- **Physical BOOT retained but hidden/recessed.** It remains the last-resort
  recovery path when flash is blank or hard-bricked.
- **Software recovery required in addition to physical recovery**, with ROM
  download mode and firmware/OTA recovery held explicitly distinct — they fail
  in different situations and must never be conflated in UI copy.
- **Microphone retained** (ICS-43434 I2S MEMS, carried forward unchanged).
- **Speech output retained.** Not downgraded to a buzzer. MAX98357A-style I2S
  Class-D remains the leading architecture; the audit found no materially
  simpler option, because the ESP32-S3 has no DAC.
- **IR retained internally** — not removed, not moved to an accessory.
- **Community expansion target changed from 26 pins to 20 pins**, with a future
  requirement that the connector be keyed, shrouded/polarized and recessed.
- **External I2C retained**, pending validation of its protection, buffering and
  backfeed behaviour before architecture lock.
- **First Full Beta v2 pre-design audit completed** — read-only, pinned to
  repository HEAD `b8b5ebd`, zero repository changes. It established the
  measured GPIO budget (zero free native pins), three candidate 20-pin connector
  architectures, and the blocker set B-01 through B-16 now tracked in
  [PROGRESS.md](PROGRESS.md).
