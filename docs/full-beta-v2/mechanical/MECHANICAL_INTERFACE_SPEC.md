# AQROOT Full Beta v2 — Mechanical Interface Specification

**AUTHORITATIVE PRE-CAD DIMENSION SOURCE.**

Date: 2026-08-22 (updated **2026-08-24 by FBV2-P1-002 — circular NFC geometry D-224, 915 feed and cable D-222/D-223, SMA and B-52 D-230, retention D-226, IR forming D-229**; previously updated 2026-08-23 by FBV2-S2-002 — **microphone acoustic port, M-14**; and by FBV2-DISP-002, FBV2-COMM-001 and FBV2-COMM-002 — display, display connector and community connector LOCKED; annotated 2026-08-23 after FBV2-S1-003; **audio parts LOCKED 2026-08-23 by FBV2-S1-006** — §7 and the envelope table; **IR parts LOCKED 2026-08-23 by FBV2-S1-007** — §8 and the component table; **front RGB status light added 2026-08-23 by FBV2-S1-008** — §9 and M-11; **community connector footprint VERIFIED AND BUILT 2026-08-23 by FBV2-S1-009** — §5 and M-12; **RF off-board interfaces sourced 2026-08-23 by FBV2-S2-001** — §8 and M-13; **PRE-FLOORPLAN AUTHORITY RECONCILIATION 2026-08-23 by FBV2-MECH-002** — NFC clear zone, `J1` land pattern and assembly route, SMA↔IR spacing datum, speaker Z column, §4.1 content list and the machine-readable block; companion handoff [`P1_FLOORPLAN_INPUTS.md`](P1_FLOORPLAN_INPUTS.md))

> **P1 NOTE — FBV2-P1-001 (2026-08-24).** The floorplan now exists. **Board-side convention
> LOCKED: `F.Cu` = FRONT (display, buttons), `B.Cu` = REAR (battery) — D-214.** Rear packing is
> **NFC -> battery -> speaker, 48 + 75 + 20 = 143 mm in the 155 mm cavity — D-215.** The
> **internal 915 MHz whip storage channel is DELETED — D-219**; the LEFT wall now belongs to the
> 433 MHz flex **and to the 915 coax channel**. ~~The **915 pigtail is `095-902-568-100`
> (100 mm) — D-218 — and the P1 geometry proves it DOES NOT REACH** the top-panel SMA~~
> **SUPERSEDED 2026-08-24 by D-223: the pigtail is RF Solutions `CBA-UFLSMA20IP`, 200 mm, IP67,
> RG-178, U.FL right-angle → SMA(F) bulkhead, and the FBV2-P1-002 floorplan measures a 138.48 mm
> routed run against it — 46.52 mm of spare beyond the 15 mm service loop. THE 915 FEED CLOSES
> AND FBV2-P1 PASSES.** Coordinates,
> keepouts and measured clearances live in [`../pcb/FBV2_P1_FLOORPLAN.md`](../pcb/FBV2_P1_FLOORPLAN.md)
> and [`../pcb/FBV2_P1_KEEPOUTS.md`](../pcb/FBV2_P1_KEEPOUTS.md).

> **AUTHORITY NOTE — FBV2-MECH-002 (2026-08-23).** This document is the authoritative pre-CAD dimension
> source for **FBV2-P1** and **must not contain conflicting CURRENT requirements**. Where a superseded
> figure is retained below it is marked ~~struck~~ or explicitly labelled **SUPERSEDED**, and the current
> value is stated next to it. Historical rationale is preserved; only current authority was changed.

> **NFC antenna reservation — FBV2-S1-004B (2026-08-23, D-127 / D-128).**
> **CORRECTED 2026-08-23 (FBV2-S1-004C, D-131): the locked part is the `.B.dg` REVERSE
> FERRITE variant.** The NFC antenna is **off-board and locked**: Taoglas
> **`FXC.46.52.0075X.B.dg`**, **46 mm diameter, 0.3 mm thick, reverse ferrite layer**, 3M
> peel-and-stick, on a **75 mm 28 AWG twisted pair with an ACH(F) connector** that mates
> `J7` on the board.
> **Mounting is now fully specified: the ADHESIVE SIDE bonds directly against the INNER REAR
> enclosure surface; the field reads OUTWARD through the rear plastic shell; the FERRITE
> FACES INWARD**, toward the PCB and battery. Per Taoglas APN-24-8-001 the `.A.dg` variant
> has the opposite stack and is intended for bonding onto a PCB or component surface — with
> it the ferrite would sit between the coil and the tag. **The connector, cable, diameter and
> interface are identical, so the board is unaffected.**
> ~~**Clear region: 48 × 48 mm minimum**~~ **SUPERSEDED 2026-08-24 by D-224. The clear region is Ø48 mm CIRCULAR and the metal exclusion is Ø58 mm CIRCULAR, both centred on doc (30.800, 124.500). The 48 × 48 square is RETAINED but only as the placement / positioning-tolerance envelope for the Ø46 antenna — never again as the metal-free shape. The Ø58 circle is INSCRIBED IN the superseded 58 × 51 rectangular keep-out, so the radial clearance was not reduced; only the four corners are reclaimed.**
> Rear upper region; **no battery overlap**; **ferrite face toward the internal electronics
> and ground plane**, per the manufacturer's stack orientation for the `.dg` variant; no
> speaker-magnet overlap; **no metal bosses or screws through the active zone**; the stored
> 433 MHz flex must not cross the NFC zone. **No enclosure external-size change** — this is
> a keepout inside the existing cavity.
> Two constraints follow from the parts rather than the zone: **`J7` needs vertical mating
> clearance** (JST ACH is a top-entry header — the socket drops on from above and the wires
> leave horizontally), and **the cable is 75 mm**, so `J7` must sit within 75 mm of routed
> cable length of the antenna position, with the cable clear of the 433 MHz flex.

> **RF antenna reservations — FBV2-S1-004 (2026-08-23, D-118 … D-120).**
> **433 MHz:** the Taoglas `FXP450.07.0100C` body is **47 × 17 × 0.28 mm** on a 100 mm
> cable and mounts by **adhesive against a plastic wall** in the **LEFT / LOWER-SIDE**
> internal region. **It must NOT be laid on the PCB**, and must clear the LiPo, the NFC
> loop and its ferrite, the speaker magnet, large ground pours, metal bosses and screws,
> the USB shell, the 915 MHz bulkhead and pigtail, and the IR structures. **The `U7` IPEX
> socket must remain reachable with the shell open** so the flex can be swapped for an
> external pigtail without a respin. Record as an antenna keepout for FBV2-P1.
> **915 MHz:** an **SMA female bulkhead on the top panel**, fed by a 100–150 mm pigtail
> from the `U8` IPEX socket. **≥ 8 mm edge-to-edge between the SMA body and either IR
> aperture**, and the pigtail must not cross the IR optical path (**B-52** — spacing is
> recorded, **no CAD was created**). Nothing dimensional elsewhere in this document changed.

> **Capture note — FBV2-S1-003.** The locked display and connector are now **captured in
> the schematic**: `J1` uses a new `ER-TFT035IPS-6_50P` symbol whose pin table is the
> vendor's own, replacing the 2.8-inch table it had inherited. **`J1` remains on the
> FH69-dedicated land pattern** — the FH52E/FH12 migration proposed by FBV2-DISP-002 was
> **not** performed, because full footprint and mechanical equivalence was not
> demonstrated from both Hirose drawings (**B-47**). The 2.3 mm connector height and the
> B-33 placement constraint are unchanged. **Nothing dimensional in this document changed.**
Task: FBV2-MECH-001
Gate: **FBV2-A2**
Status: interface freeze. **No CAD exists yet. No PCB outline has been drawn.**

> This document supersedes, for Full Beta v2 only, the dimensional content of
> *Enclosure Field Slate v3/v4/v5*. Those remain the historical record and the
> source of the concept, zoning, RF crown and control-set direction.
> `hardware/beta/mechanical/` was **read only** and is unmodified.

---

## 0. How to read this document

| marking | meaning |
|---|---|
| **LOCKED** | CTO ruling, or measured from a repository artefact. Do not change without a CTO decision. |
| **TARGET** | Derived here from a locked input plus stated assumptions. Binding for design work until CAD refutes it. |
| **TBD** | Genuinely undetermined. Must not be treated as a constraint. |

**Nothing is marked LOCKED on the strength of derivation alone.** Every derived
value is TARGET, however confident the arithmetic.

---

## 1. Dimension authority table

| # | key | value | status | source |
|---|---|---|---|---|
| 1 | **EXTERNAL_ENCLOSURE** | **80 × 160 × 23 mm** (X × Y × Z, portrait) | **LOCKED** | CTO ruling. *External only — not PCB, not cavity* |
| 2 | **WALL_THICKNESS** | **2.0 mm** nominal, all faces | **TARGET** | §3 |
| 3 | **INTERNAL_CAVITY** | **75.0 × 155.0 × 18.5 mm** nominal envelope | **TARGET** | §3 |
| 4 | **PCB_MAX** | **72.0 × 152.0 mm** | **TARGET** | §4 |
| 5 | **PCB_TARGET** | **70.0 × 148.0 mm** | **TARGET** | §4 — recommended outline |
| 6 | **PCB_THICKNESS** | **1.6 mm** | **LOCKED** | carried from Beta-DM; measured |
| 7 | **BATTERY_ENVELOPE** | **60 × 75 × 8.0 mm**, ~2500–3000 mAh | **LOCKED** | **D-071** (2026-08-22) |
| 8 | **DISPLAY_ENVELOPE** | module ≤ **60 × 90 mm**, stack ≤ **4.5 mm**. **Fitted part `ER-TFT035IPS-6` + `ER-TPC035-6`: 56.54 × 84.96 × 3.95 ± 0.25 mm (4.20 max)**, active 48.96 × 73.44 | **LOCKED** | **D-072 / D-074.** Locked by FBV2-DISP-002; supersedes the 52 × 71 × 3.0 figure derived from the 2.8″ keepout |
| 9 | **NFC_ZONE** | **48 × 48 mm** minimum clear region, metal-free, rear upper third | **LOCKED** | **D-127 / D-128 / D-131** (FBV2-S1-004B/C) — 46 mm `FXC.46.52.0075X.B.dg` plus installation tolerance. ***The 45 × 45 mm figure carried here until FBV2-MECH-002 was STALE and is SUPERSEDED.*** §6 |
| 10 | **SPEAKER_ENVELOPE** | **Ø20 × 3.0 mm** + **1.5–2.0 cm³** rear cavity | **LOCKED** | **D-148.** Fitted part **PUI `AS02008MR-LW152-R`**, Ø20 ± 0.2 × 3 ± 0.2 mm. Supersedes the Ø20 × 4.0 / 15 × 11 × 3.5 targets and **releases 1 mm of Z** in the speaker column. The rear-cavity requirement is unchanged |
| 11 | **COMMUNITY_CONNECTOR_ENVELOPE** | **30.48 × 8.13 × 5.33 mm** body; **2×12 @ 2.54 mm**, FEMALE, horizontal entry, right wall. Samtec **`BCS-112-S-D-HE`** | **LOCKED** | §5. **D-081/D-093.** Harwin `M20-7881242` **REJECTED as obsolete** |
| 12 | **ANTENNA_CONNECTOR_LOCATION** | top edge, **left half**; **Ø6.5 mm bulkhead clearance hole**; ***P1 FINDING (D-218): with `U8` at the bottom rear the routed coax run is ≈ 190 mm, so neither the 100 mm nor the 150 mm assembly reaches, and a top-LEFT SMA forces the coax across the NFC zone. OPEN for CTO ruling.***; **≥15 mm centre-to-centre from either IR window** *and* **≥8 mm edge-to-edge between the SMA body and either IR aperture**. **Both rules are current — see §8.1** | **LOCKED** (both rules) | **§8.1.** 15 mm: FBV2-MECH-001. 8 mm: **D-120**, restated by **M-13** (FBV2-S2-001) |
| 13 | **USB_LOCATION** | bottom edge, centred ±5 mm | **TARGET** | CTO layout |
| 14 | **MICROSD_LOCATION** | bottom edge, left of USB-C, ≥8 mm centre-to-centre clearance | **TARGET** | CTO layout |
| 15 | **IR_ZONE** | top edge, **right half**; emitter and receiver ≥**15 mm** apart with an opaque barrier | **TARGET** | §8 |
| 16 | **MOUNTING_BOSSES** | **6 × M2**, Ø6.0 mm keepout, 4 corners + 2 mid-span | **TARGET** | §4 |
| 17 | **REQUIRED_CLEARANCES** | PCB edge→cavity wall **≥1.5 mm**; component→shell **≥0.5 mm**; connector→wall **≥0.3 mm** | **TARGET** | §3, §4 |
| 18 | Device orientation | **portrait** — 80 wide × 160 tall | **LOCKED** | Implied by the CTO face assignment and confirmed by the Beta-DM 74 × 155 outline mapping |
| 19 | Display size | **3.5 inch** | **LOCKED** | **D-072** |
| 20 | Display panel MPN / FPC | **`ER-TFT035IPS-6` + `ER-TPC035-6`** — one **50-pin, 0.50 mm pitch, bottom-contact** FPC, **0.30 ± 0.03 mm** thick, 25.5 ± 0.15 mm wide, 30 ± 0.5 mm free length; CTP **FT6236 @ 0x38** on pins 44–47 of the same tail | **LOCKED** | **D-074 / D-075.** M-06 closed |
| 21 | J1 mating connector | **Hirose `FH69-50S-0.5SH`** — 0.5 mm, 50 pos, **top *and* bottom contact**, FPC **0.30 ± 0.05 mm**, height **2.3 mm**, right-angle, backflip ZIF. **`J1` sits on a DEDICATED FH69 LAND PATTERN. There is NO drop-in second source: `FH52E-50S-0.5SH` does NOT share the FH69 land pattern and is NOT a second source. Single-source connector architecture.** **JLC stocks the genuine Hirose part and `J1` is MACHINE-PLACEABLE — re-check stock before ordering.** | **LOCKED** | **D-076.** ***D-077's "FH12 / FH52E standard land pattern, second source FH52E-50S-0.5SH, mating proven from both drawings" is SUPERSEDED — B-47 resolved NOT COMPATIBLE (D-194); machine-placement per D-206 / D-207.*** |
| 22 | Battery SKU | — | **TBD** | envelope LOCKED instead (row 7) |

---

## 2. Component dimensional inventory

Values marked **(measured)** come from repository artefacts. Values marked
**(typical)** are class-typical figures used to size envelopes; they are adequate
for interface freeze and must be replaced by vendor drawings at CAD time.

| item | part | dimensions | notes |
|---|---|---|---|
| **Display** | **3.5″ 320×480 IPS + CTP** (D-072). **`ER-TFT035IPS-6` + `ER-TPC035-6`** | **56.54 × 84.96 × 3.95 ± 0.25 mm**, active **48.96 × 73.44 mm**, dot pitch 0.153 mm, **one 50-pin 0.5 mm bottom-contact FPC**, **6 LED parallel** backlight (2.9–3.2 V, 120 mA max), ILI9488 + FT6236 | **LOCKED (D-074).** ST7796S was preferred and does not exist in a documented CTP module at this size (D-078); the cost is +50 % SPI-A traffic |
| Display connector | **Hirose `FH69-50S-0.5SH`** | 0.5 mm, 50 pos, **top and bottom contact**, FPC 0.30 ± 0.05 mm, **2.3 mm high**, right-angle | **LOCKED (D-076).** ⚠ At 2.3 mm it **cannot sit under the panel** (0.8 mm display-shadow limit) — it must be placed in the 70.04 mm below the display, alongside the D-pad, A/B and mic aperture (**B-33**). The **6 mm FPC bend corridor** is retained and is generous against the ≥3 mm needed for a 0.30 mm tail |
| **Front controls** | SW2–SW7 PTS645SM43SMTR92LFS | 6.0 × 6.0 × **4.3 mm** (typical), ~0.25 mm travel | 6 switches: D-pad ×4, A, B. **Tallest top-side class.** Needs a plunger/keypad stack of ~1.0 mm above the actuator |
| **Power** | SW9 JS102011SAQN | SPDT slide, ~4.7 × 2.9 × 2.0 mm body + actuator (typical) | Right wall, lower third |
| **USB-C** | GCT USB4105-GF-A-120 | ~9.2 × 7.35 × **3.26 mm** (typical), top-mount horizontal | Bottom edge; shell aperture must clear the receptacle mouth |
| **microSD** | Molex 5025700893 | ~14.0 × 14.5 × **1.85 mm** (typical), push-pull | Bottom edge; card protrudes during insertion — reserve **+18 mm** insertion travel outside the shell |
| **Microphone** | **MK1 PUI `DMM-4026-B-I2S-R`** | **4.00 × 3.00 × 1.00 mm** ±0.10 | **BOTTOM PORT** — the acoustic hole is in the PCB beneath the part, so **the microphone is soldered to the face OPPOSITE the shell aperture**. Path is shell aperture → gasket → **Ø1.05 mm PCB hole** → Ø0.25 mm port. **LOCKED D-145 / D-151** |
| **Speaker** | **LS1 PUI `AS02008MR-LW152-R`**, off-board | **Ø20 ± 0.2 × 3 ± 0.2 mm**, 8 Ω ±15 %, 0.5 W rated / 0.8 W max | §7. **LOCKED D-148.** 152 mm AWG #32 leads to `J6`; Nd-Fe-B magnet |
| **IR emitter** | **Vishay `TSAL6100`** | T-1¾, **Ø5 mm** leaded, 2.54 mm lead pitch, **±10° half-angle** | Top edge. **LOCKED D-154.** Beam is **narrower** than the ±17° the layout was first written against and **2.4× brighter on axis** — see §8. Fallback **TSAL6200** (±17°) is a drop-in in the same footprint (**B-66**). Consider a side-view SMD emitter to reduce Z |
| **IR receiver** | **Vishay `TSOP38238`** (AGC2; `TSOP38438` is a documented same-package fallback, D-163) | ~6.0 × 5.6 × **4.7 mm** (typical), minicast, ±45° FOV | Top edge. **Tallest top-side component overall.** **LOCKED D-160**; same package and pinning as the TSOP38238 it replaces |
| **Radios** | E07-400M10S, E22-900M22S | ~3.5 mm (typical) incl. shield | Both carry **IPEX/u.FL** ports |
| **Community connector** | **2×12, 24 active contacts, 2.54 mm, FEMALE** — Samtec `BCS-112-S-D-HE` | body **30.48 × 8.13 × 5.33 mm**, horizontal entry | §5. Keying and shroud come from the **enclosure recess** |
| Expanders / protection | PCAL9535APW (TSSOP24), LTC4368 (MSOP-10), 2 × dual FET (SOIC-8) | ≤1.2 mm | All low-profile; no Z impact |

### 2.1 Height census

| side | tallest | height | constraint |
|---|---|---|---|
| **Top** | **TSOP38238** IR receiver (`TSOP38438` same-package fallback) | **4.7 mm** | Must sit **outside the display shadow**. Top edge only |
| Top (display shadow) | passives only | **≤0.8 mm** | **measured** Beta-DM limit — retain |
| Top (control area) | PTS645 tact switch | **4.3 mm** | |
| **Bottom** | Molex microSD | **1.85 mm** | |
| Bottom (battery shadow) | — | **≤1.2 mm** | **measured** Beta-DM limit — retain |

---

## 3. Enclosure stack-up and cavity derivation

### 3.1 Wall thickness

**2.0 mm nominal.** Suits SLA/CNC prototypes and is a normal ABS/PC injection wall
for a handheld of this size. Below 1.5 mm a 160 mm-long shell flexes noticeably;
above 2.5 mm the cavity loses volume for no structural gain.

### 3.2 Cavity

```
INTERNAL_CAVITY_X = 80  − 2(2.0 wall) − 1.0 (seam/assembly tol) = 75.0 mm
INTERNAL_CAVITY_Y = 160 − 2(2.0 wall) − 1.0                     = 155.0 mm
INTERNAL_CAVITY_Z = 23  − 2(2.0 wall) − 0.5                     = 18.5 mm
```

**This is the nominal envelope only.** Local intrusions reduce it:

| intrusion | typical |
|---|---|
| Shell lip / tongue-and-groove at the seam | 1.0–1.5 mm inward, full perimeter |
| Mounting bosses | ~~Ø6.0 mm × full height, 6 places~~ **SUPERSEDED by D-226: 2 places, Ø4.5 mm keep-out (moulded boss OD 4.0 mm + 0.25 mm per side), plus moulded edge-capture rails and four rear non-metallic support ribs that need no PCB holes** |
| Stiffening ribs | 1.5 mm × 3 mm tall, as needed on the 160 mm spans |
| Connector aperture reinforcement | local |

### 3.3 Z stack-up — three worst-case columns

Computed with real clearances, not nominal sums.

**Column A — display region (rear: NFC)**

| layer | mm |
|---|---|
| Front shell | 2.0 |
| CTP + TFT stack (`ER-TFT035IPS-6` + `ER-TPC035-6`, was 2.9 for the 2.8″) | **3.95 ± 0.25 → 4.20 max** |
| Adhesive / support | 0.5 |
| PCB top components (display shadow limit) | 0.8 |
| PCB | 1.6 |
| Rear air gap | 1.0 |
| NFC ferrite | 0.3 |
| NFC loop (flex) | 0.2 |
| Clearance | 0.5 |
| Rear shell | 2.0 |
| **Total** | **13.1 mm** — 9.9 mm spare *(revised by FBV2-DISP-002 for the locked 4.20 mm max module)* |

**Column B — control region (rear: battery)** ← governing column

| layer | mm |
|---|---|
| Front shell | 2.0 |
| Keypad / plunger + travel | 1.0 |
| PTS645 tact switch | 4.3 |
| PCB | 1.6 |
| **Battery** | **8.0** |
| Clearance | 0.6 |
| Rear shell | 2.0 |
| **Total** | **19.5 mm** — **3.5 mm spare** |

**Column C — speaker region**

| layer | mm |
|---|---|
| Front shell + air | 2.5 |
| PCB top components | 1.5 |
| PCB | 1.6 |
| Speaker driver (`AS02008MR-LW152-R`, ~~4.0~~) | **3.0** |
| Rear acoustic cavity | 2.0 |
| Rear shell | 2.0 |
| **Total** | **12.6 mm** — **10.4 mm spare** *(corrected FBV2-MECH-002: D-148 locked Ø20 × 3.0 mm and states it releases 1 mm of Z in this column; the column had not been updated)* |

### 3.4 Verdict on 23 mm

## **PASS** — not tight.

The governing column consumes 19.5 mm of 23 mm, leaving **3.5 mm**. That margin
should be spent deliberately, not left as air:

- **Recommended:** allocate it to the **battery**, which is why the envelope is set
  at **8.0 mm** rather than the 5–6 mm a 2000 mAh pack would need. This raises the
  practical capacity to the **2500–3000 mAh** class.
- The device could be made thinner (≈20 mm) if industrial design prefers, at the
  cost of that capacity. **Not recommended** — runtime is a headline feature and
  23 mm is already a comfortable handheld thickness.

---

## 4. PCB envelope

```
MAX_PCB_X = 75.0 − 2(1.5 edge clearance) = 72.0 mm
MAX_PCB_Y = 155.0 − 2(1.5)               = 152.0 mm

RECOMMENDED_PCB_X = 70.0 mm
RECOMMENDED_PCB_Y = 148.0 mm
```

The recommendation deliberately leaves **2.5 mm per side** beyond the minimum, for
shell lips, boss intrusion, rib clearance, connector-to-wall tolerance and
assembly access. A board that fills the cavity to the millimetre has no recovery
path if any of those grows.

### 4.1 Comparison with Beta-DM (74 × 155 × 1.6 mm, measured)

| axis | Beta-DM | derived cavity | verdict |
|---|---|---|---|
| X | **74.0** | 75.0 | **1.0 mm total clearance** — no room for bosses, lips or ribs |
| Y | **155.0** | 155.0 | **0.0 mm clearance** — the board *is* the cavity |

## Verdict: **SHOULD BE RE-FLOORPLANNED WITH A DIFFERENT OUTLINE.**

Not merely "needs reduction". Two independent reasons:

1. **Dimensionally it does not fit.** 155 mm of board in a 155 mm cavity leaves
   nothing for the shell lip, six bosses, ribs, or assembly clearance. Reduction of
   **−4 mm X and −7 mm Y** is the minimum.
2. **Its content has changed.** Full Beta v2 removes HOME **and adds a FRONT RGB
   status light `D13`** *(the RGB nets were removed from the Beta-DM control set and a
   deliberate front status light was added instead — D-167, FBV2-S1-008; the earlier
   "removes … the RGB nets" reading is **SUPERSEDED**)*,
   changes both expanders, changes the community connector to **24 contacts in 2 × 12
   at 2.54 mm** *(D-081 / D-083 — the earlier "26 to 20 pins" figure is **SUPERSEDED**)*, adds the
   P2 four-FET protection stage plus the dead-cell recovery branch, adds the NFC
   crystal, matching network and antenna, restores IR TX/RX, and adds the TPS22950C
   accessory switch. Reusing a floorplan built around a different component set
   would inherit the very constraints that made IR TX and IR RX unroutable on
   Beta-DM.

**Re-floorplanning from the cavity is the correct action**, and it is what the
Field Slate v3 requirement ("the envelope must drive at least one PCB revision")
originally asked for and never received.

### 4.2 Mounting and retention — **LOCKED 2026-08-24 (D-232)**

**Retention is a FOUR-ELEMENT architecture, not a screw count.** Three of the four elements are
enclosure features and need no PCB hole. ~~6 × M2~~ ~~3 × M2~~ **— both superseded: this
outline yields TWO legal through-board M2 positions and two is ACCEPTABLE (D-226, D-232).**

| element | value | status |
|---|---|---|
| **A. Moulded edge-capture rails** | continuous on the **RIGHT** and **BOTTOM** board edges; **segmented on the LEFT** to clear the 433 flex (Y 1.5 … 48.5) and the coax channel's western excursion (Y ≈ 112 … 137) | **LOCKED (D-232).** Constrains lateral PCB movement |
| **B. Rear non-metallic support ribs** | **four**, bearing on reserved component-free pads: `RIB_R1` X 66.20…69.70 / Y 24.00…44.00 · `RIB_R2` X 66.20…69.70 / Y 45.00…64.00 · `RIB_R3` X 66.20…69.70 / Y 76.00…97.00 · `RIB_B1` X 44.00…47.60 / Y 21.20…23.30 | **LOCKED (D-232).** `RIB_R2` bears behind the A/B control area; `RIB_B1` + `RIB_R1` bracket the D-pad. **All four verified component-free including through-hole leads** |
| **C. M2 through-board screws** | **TWO.** `BOSS1` doc (40.000, 12.000) · `BOSS2` doc (59.000, 145.000) | **LOCKED (D-226, D-232)** |
| **D. `J5` backing / load path** | `COMM_RECESS` backing boss carries the ≈ 33 N average insertion load (peak higher) **into the ENCLOSURE, not into the PCB solder joints** | **LOCKED (D-097, M-10, D-232)** |
| Boss keepout | ~~**Ø6.0 mm** copper-and-component free~~ **SUPERSEDED by D-226: Ø4.5 mm.** A Ø6.0 keep-out has **ZERO** legal sites on this outline | LOCKED |
| Boss drill | **Ø2.2 mm NPTH** | LOCKED |
| Board edge clearance | **≥ 1.5 mm** to any cavity wall (actual: 2.5 mm in X, 3.5 mm in Y) | LOCKED |

**Constraints the architecture satisfies, verified at FBV2-P2-000:**

* **no support compresses the LiPo** — every rib is outside `BATTERY_SHADOW`;
* **no metal enters the NFC Ø58 exclusion** — every rib is non-metallic and all four are far
  outside it;
* **board flex under D-pad and A/B presses is carried by plastic**, not by 1.6 mm FR4 span;
* **`J5` insertion load is carried by the enclosure**, not by solder joints;
* **USB and microSD insertion loads do not depend only on the M2 screws** — `J3` and `J2` both
  sit on the bottom edge, which carries a **continuous** edge-capture rail, with `BOSS1` 12 mm
  above it. The rail takes the reaction along its whole length; the screw is a secondary path.

**A third M2 may be added later ONLY if enclosure CAD produces a legal location without
sacrificing existing geometry.** D-226's four routes to one — a battery narrower than 60 mm, a
display narrower than 56.54 mm, the SMA off the top-left, or an M2 with ≈ 1.4 mm of board to the
edge — are **all declined** (D-232).

Beta-DM used **four Ø2.4 mm holes (measured)**. v2 trades screw count for a moulded retention
architecture; the reason is arithmetic, not preference — the display owns X 3.39 … 59.93 on the
front and the battery owns X 6.00 … 66.00 on the rear, leaving a 3.39 mm left sliver and a
4.00 mm right sliver, both narrower than a Ø4.5 keep-out.

---

## 5. Community expansion connector

> **SUPERSEDED IN ITS PHYSICAL HALF 2026-08-24 by D-237 / D-240 (FBV2-EXP-002).** The port is
> now a **standard 1 x 24, 2.54 mm, FEMALE, right-angle socket** -- Samtec
> **`SSQ-124-02-G-S-RA`** -- presenting **one pin per line** down the right wall, mating an
> ordinary male header or Dupont jumper. **All 24 electrical functions and every protection
> component below are UNCHANGED**; what changed is the presentation and the pin order
> (**ORDER-B**, which is safe under 180 deg reversal by construction). A **`JST
> SM04B-SRSS-TB` Qwiic / STEMMA QT** connector is added on the protected external I2C node and
> costs zero components. The **closed-end 62.5 mm recess** replaces the D-097 asymmetric key.
> Everything about the 2 x 12 below is retained as the record of what it superseded.


> **The 20-pin / 2×10 / 2.00 mm target is SUPERSEDED by D-081 and D-083
> (FBV2-COMM-001).** The port is now 2×12 at 2.54 mm, female, with keying and
> shrouding provided by the enclosure rather than by the connector.

| property | value | status |
|---|---|---|
| Contact count | **24 ACTIVE** (no NC, no key contact) | **LOCKED** (D-081) |
| Organisation | **2 rows × 12** | **LOCKED** (D-081) |
| Pitch | **2.54 mm** | **LOCKED** (D-083) — chosen so commodity male pin headers mate; that is the whole point for a maker platform |
| Gender | **FEMALE on the device**, male on the accessory | **LOCKED** (D-081) |
| **MPN** | **Samtec `BCS-112-S-D-HE`** — female Tiger Claw dual-beam receptacle, **horizontal entry**, through-hole, **30 µin gold**. **ACTIVE**, MOQ 1, next-day from Samtec | **LOCKED** (D-093) |
| Cost-down alternate | `BCS-112-L-D-HE` (10 µin gold) — identical body, identical footprint, **no board change**; 100-cycle life instead of the 30 µin extended-life data | **recorded** |
| **PCB pattern** | **2 × 12 PTH, 2.54 mm within a row, 7.87 ± 0.05 mm BETWEEN rows, 0.71 mm drill**, 27.94 mm end-hole span (Samtec FIG 3) — **not** interchangeable with a vertical 2×12 pattern | **LOCKED**, footprint to be drawn (B-29) |
| Mating pin | **0.64 mm (.025″) square post, engagement 4.34–6.35 mm.** Reference mate `TSW-112-07-L-D` (5.84 mm post). **Extra-long-pin headers (8.13 mm posts) must not be used** | **LOCKED** |
| Body envelope | **30.48 (L) × 8.13 (D) × 5.33 (H) mm** | **LOCKED**, height to be re-confirmed at FBV2-P1 (**M-09**, now LOW) |
| Orientation | **right-angle, side-exit through the right wall** | **LOCKED** |
| Recess | **≥ 1.5 mm** below the outer wall face | **TARGET** |
| **Keying / polarisation / shroud** | **FROM THE ENCLOSURE (D-097).** An **asymmetric rib/step on the UPPER edge only** — the two mating rows are just 2.54 mm apart, so the key must be unambiguous, not a chamfer. **The recess must be CLOSED AT BOTH ENDS** (≤ 0.3 mm clearance) so a one-column lateral shift is mechanically impossible. A moulded **shelf and backing rib capture the connector body**; the accessory shell bottoms on an **enclosure boss** | **LOCKED** (D-041 satisfied, D-081, D-097) |
| Lead-in | chamfer on all four recess walls | **TARGET** |
| **Insertion load** | **≈ 33 N average** (24 × 1.39 N), peak higher; withdrawal ≈ 20 N average. Must be carried by an enclosure boss/rib | **M-10** |
| Position | right wall, **below the display band**, above the Power control | **TARGET** — the 7.87 mm body depth exceeds the 6.73 mm of PCB clear of the display, so it cannot sit beside the panel |
| Marking | pin-1 triangle; **"COMMUNITY PORT — 3V3 LOGIC ONLY"** and **"5V PIN IS POWER OUTPUT ONLY"** | **LOCKED** (D-090) |

**Footprint built and verified 2026-08-23 (FBV2-S1-009, D-179).**
`AQROOT_Beta:Samtec_BCS-112-S-D-HE`, taken from the Samtec **RECOMMENDED PCB LAYOUT,
REVISION B, FIG 3 (`BCS-1XX-XXX-D-HE-XXX`)** — the horizontal dual-row figure specifically:

| dimension | drawing | footprint |
|---|---|---|
| pitch within a row | .100 in / **2.54 mm** | 2.54 mm |
| **row to row** | **.310 ± .002 in = 7.87 ± 0.05 mm** | 7.87 mm |
| finished hole | **.028 in = 0.71 mm PTH** | 0.71 mm drill, 1.30 mm pad |
| pin-field length | positions × .100 − .100 = **27.94 mm** | 27.94 mm |

**A vertical 2 × 12 pattern is NOT a substitute — its rows sit 2.54 mm apart, not
7.87 mm.** B-29 is closed.

**PCB envelope required, for FBV2-P1 floorplanning:**

| item | value |
|---|---|
| pin field | **27.94 (X) × 7.87 (Y) mm** |
| to the outside of the 1.30 mm pads | **29.24 × 9.17 mm** |
| body | **30.48 × 8.13 × 5.33 mm** |
| courtyard | **31.48 × 9.13 mm** |
| holes | **24 × Ø0.71 mm PTH** |

> **This is the only through-hole field on an otherwise all-SMD board, and it
> constrains routing on every layer beneath it.** Odd contacts are row A, even are
> row B; pad 1 is rectangular with a silkscreen tick and a `PIN 1` legend; the
> F.Fab layer carries a `MATES ->` direction mark.

**Assembly — CURRENT TRUTH (D-206 / D-207, confirmed FBV2-MECH-002):** `J5` **IS** a
**manual / secondary assembly operation for the first five boards** — it is one of
**exactly two** hand-soldered parts per board, the other being `D1` (5 mm THT IR emitter).
*(The earlier conditional phrasing — "if the JLC service cannot place this…" — is resolved:
it cannot, and the part is class E.)* The connector architecture is not compromised for SMT
convenience.

**Wall aperture:** 34 × 10 mm nominal, with 0.3 mm clearance to the accessory shell
on all sides, plus the keying rib.

### 5.1 Z column — the connector region now governs

| layer | mm |
|---|---|
| Front shell | 2.00 |
| **Community connector body** | **5.33** |
| PCB | 1.60 |
| Battery | 8.00 |
| Clearance | 0.60 |
| Rear shell | 2.00 |
| **Total** | **19.53 mm of the 23.0 mm external budget — 3.47 mm spare** |

**With `BCS-112-S-D-HE` the connector region is level with the control region
(19.5 mm) and is no longer the sole governing column** — it was 22.30 mm with the
rejected Harwin part. **3.47 mm is real, usable clearance.** Further relief remains
uncounted: the battery is 60 mm wide in a 75 mm cavity, so the outer ~5 mm of each
PCB edge has nothing behind it. **Confirm the 5.33 mm body height against the
Samtec 3D model at FBV2-P1 (M-09, now LOW).**

---

## 6. Rear architecture — NFC and battery

### 6.1 The decision: separate them in plan, do not stack them

The cleanest resolution to "battery detunes the NFC loop" is **not** to engineer a
shielding stack — it is to **not put them in the same place**.

```
   REAR VIEW (looking at the back of the device)
   ┌─────────────────────────────────────┐ Y = 160 (top)
   │  antenna connector │  IR windows    │
   ├─────────────────────────────────────┤
   │                                     │
   │        NFC LOOP ZONE                │   rear UPPER third
   │        48 × 48 mm                    │   (behind the display)
   │        metal-free, ferrite-backed    │
   │                                     │
   ├─────────────────────────────────────┤ Y ≈ 100
   │                                     │
   │        BATTERY                       │   rear LOWER two-thirds
   │        60 × 75 × 8.0 mm              │   (behind the controls)
   │                                     │
   │                          ┌────────┐ │
   │                          │SPEAKER │ │
   │                          └────────┘ │
   └─────────────────────────────────────┘ Y = 0 (bottom)
     USB-C            microSD
```

**Because the display occupies the front upper third, the rear upper third is
free** — the PCB is the only thing between it and the rear shell. That is the
natural home for the NFC loop, and it costs nothing.

### 6.2 Rules

| rule | value | status |
|---|---|---|
| NFC loop envelope | **48 × 48 mm** minimum clear region | **LOCKED** — D-127 / D-128 / D-131. *(~~45 × 45 mm~~ SUPERSEDED at FBV2-S1-004B; the stale figure survived here until FBV2-MECH-002)* |
| Loop location | rear upper third, centred in X | **TARGET** |
| **Battery / NFC overlap** | **ZERO overlap permitted** | **TARGET** — this is the policy, not a mitigation |
| Ferrite | **0.3 mm layer between the loop and the PCB**, full loop footprint | **TARGET** — the PCB ground pour is the near-field threat once the battery is moved away |
| Metal keepout | no metal within **5 mm** of the loop perimeter, including screws, bosses and shielding cans — **now the Ø58 mm circle, D-224.** Recorded inside it and accepted: the battery pouch foil by 3.000 mm and `D1`'s TSAL6100 leadframe by 2.854 mm; **neither is a screw, a boss or a shielding can, and the Ø48 CLEAR region keeps 2.000 mm of zero-overlap gap to the battery** | **TARGET** |
| Screw/boss keepout | **SUPERSEDED by D-226: there are no mid-span bosses. The outline yields exactly TWO legal through-board M2 positions — doc (40.000, 12.000) and (59.000, 145.000) — both far outside the Ø58 exclusion.** | **LOCKED by measurement** |
| Matching network | on the PCB, **within 15 mm** of the loop feed point | **TARGET** |
| Speaker separation | ≥20 mm from the loop perimeter; the magnet is the largest ferrous mass in the device | **TARGET** |
| ~~**Stored antenna**~~ | **DELETED 2026-08-24 (D-219).** There is no internal antenna storage channel. The left wall carries the **433 MHz flex** at board Y 1.5…48.5, which does not reach the loop zone | **CLOSED** |

### 6.3 Battery

| property | value |
|---|---|
| Envelope | **60 × 75 × 8.0 mm** (TARGET) |
| Volume | ~36 cm³ |
| Practical capacity | **~2500–3000 mAh**, 1S Li-ion/LiPo pouch |
| Chemistry / SKU | **TBD** — envelope frozen instead |
| Retention | adhesive pad plus a moulded rib pocket; **no compression against the shell** |
| PCB features under the battery | **≤1.2 mm** (measured Beta-DM limit, retained) |
| Connector | JST-PH 2-pin, service loop routed away from the NFC zone |

This raises the assumed pack from the 2000 mAh used in the power budget
([[13 - Power Budget and Battery Runtime v0.1]]) to the 2500–3000 mAh class, which
is a **direct consequence of the 3.5 mm of Z margin** found in §3.

---

## 7. Acoustics

### 7.1 Microphone — the higher priority

**LOCKED 2026-08-23 (FBV2-S1-006, D-145 / D-151).** The port geometry below is measured from
the PUI manufacturer drawing, not estimated: §8.3 is a raster drawing, so it was rendered and
the pads measured programmatically, and the result closes against the printed dimensions to
**0.01 mm**.

| requirement | value |
|---|---|
| Part | **PUI Audio `DMM-4026-B-I2S-R`**, 4.00 × 3.00 × 1.00 mm, **bottom-port** |
| Port in the can | **Ø0.25 ± 0.05 mm**, on the package **width centreline**, **1.00 mm** from the short edge |
| Mounting face | **the face OPPOSITE the shell aperture** — sound enters through the PCB, not past the part |
| Path | shell aperture → compressible gasket → **PCB acoustic hole** → microphone port |
| **PCB hole** | **Ø1.05 mm NPTH, concentric with pad 4** — the manufacturer's number, superseding the earlier Ø0.8–1.0 mm estimate |
| PCB keepout | no copper, no solder mask and no component inside **Ø1.65 mm** (the pad-4 GND ring); **Ø2.5 mm** component keepout on the microphone side |
| Gasket | closed-cell silicone or poron, **compressed 20–30%**, **ID ≥ 1.5 mm, OD 4–5 mm**, forming a sealed tunnel |
| Shell aperture | **Ø0.8–1.0 mm**, or 3–5 holes of Ø0.5 mm, with acoustic mesh behind |
| Tunnel length | **≤2.5 mm** — longer tunnels roll off the high frequencies that carry speech intelligibility |
| Location | **front face of the ENCLOSURE, bottom third, opposite corner from the speaker** |
| **Face datum — CLARIFIED FBV2-MECH-002** | **The ENCLOSURE aperture is on the FRONT face.** M-14 says
the acoustic path leaves on *the PCB's BOTTOM face* — that is a statement about the **board**, not the
**enclosure**. The two are only consistent if **`MK1` is placed on the PCB copper face that points AWAY
from the front shell**, listening forward through the Ø1.05 mm hole. **No floorplan exists, so which
copper layer that is has not been fixed** — it is an **FBV2-P1 side-assignment constraint** and it is
**raised for CTO ruling** in the FBV2-MECH-002 audit (§7, item O-1). Nothing here changes the part, the
hole, the gasket or the tunnel length |
| Solder | keep the stencil aperture back from the hole edge so solder cannot wick into the port (**B-63**, PCB stage) |

### 7.2 Speaker

| requirement | value |
|---|---|
| Driver | **PUI Audio `AS02008MR-LW152-R`** — **Ø20 ± 0.2 × 3 ± 0.2 mm**, **8 Ω ±15 %**, **0.5 W rated / 0.8 W max**, 86 ± 3 dBA at 0.1 W / 0.1 m, **500–4000 Hz**, metal housing, Mylar cone, **Nd-Fe-B magnet**, 2.4 g |
| Leads and connector | **152 ± 10 mm UL1571 AWG #32, RED (+) / BLACK (−)**, crimped into a **JST `PHR-2` housing with `SPH-002T-P0.5S` contacts** mating `J6`. **Replaceable without soldering.** AWG #32 is the small end of the PH #32–#24 range — pull-test at first article (**B-62**) |
| Polarity | the cone moves **forward** on a positive voltage at the **RED** lead = `SPK_P` = `J6` pin 1 |
| Firing | **rear-firing** (CTO layout) |
| Rear cavity | **1.5–2.0 cm³ sealed** behind the driver — without it, low-mid output collapses and speech sounds thin |
| Grille | ≥25% open area; hole pattern Ø0.8–1.0 mm; acoustic mesh behind |
| Location | **rear, lower-right**, diagonally opposite the microphone |
| Separation from mic | **≥60 mm** and on opposite faces |
| Magnet clearance | the **Nd-Fe-B magnet must stay clear of the NFC zone** as well as of the microphone — it is the largest ferrous mass in the device |

**Deliberately not over-engineered.** No ported enclosure, no tuned volume, no
resonance targeting. The requirement is intelligible speech and alerts, and a
sealed rear cavity plus honest separation from the microphone achieves it.

### 7.3 Feedback control

Speaker rear + microphone front + ~60 mm of diagonal separation + a sealed mic
tunnel gives adequate acoustic isolation for half-duplex voice. **Full-duplex
echo cancellation is a firmware matter and is not a mechanical requirement.**

---

## 8. Top edge — IR and antenna

```
   TOP EDGE (80 mm wide)
   ┌──────────────────────────────────────────────┐
   │  [ANTENNA]        │ barrier │ [IR TX] [IR RX]│
   │   connector       │         │                │
   └──────────────────────────────────────────────┘
     ← left half →                → right half →
        ≥15 mm c-c to IR window     ≥15 mm apart
        AND ≥8 mm edge-to-edge      (emitter ↔ receiver)
        (SMA body ↔ IR aperture)
```

| requirement | value | reason |
|---|---|---|
| IR emitter location | top edge, right of centre | Natural remote-pointing posture |
| IR receiver location | top edge, right end | |
| **Emitter ↔ receiver separation** | **≥15 mm**, plus an **OPAQUE OPTICAL BARRIER** between them, receiver **outside the LED emission cone** | The TSOP38238 (and its TSOP38438 fallback) is extremely sensitive. **REVISED 2026-08-23 (D-162): the ≥15 mm figure was written against a ±17° TSAL6200. The locked TSAL6100 is 2.4× brighter on axis, so stray and internally-reflected energy reaching the receiver goes UP even though the direct cone is narrower — the narrower beam tightens this requirement rather than relaxing it.** Keep the TX current loop away from the receiver supply and return. The electrical half of self-blinding is already solved by the 41 dB `R21`/`C11` filter |
| **Opaque barrier** | **mandatory**, full height between the two windows, bonded to both shells | Blocks the internal reflection path, which is the one that actually causes self-blinding |
| Emitter axis | **normal to the top face**, ±0° | |
| Receiver FOV | ±45° about the top-face normal | |
| Windows | IR-transmissive (visibly opaque acceptable), recessed 0.5 mm | |
| **Antenna ↔ IR separation** | **BOTH RULES ARE CURRENT: ≥15 mm centre-to-centre** (bulkhead hole ↔ IR window) **and ≥8 mm edge-to-edge** (SMA body ↔ IR aperture) | A fitted whip must not shadow the emitter cone (15 mm); the panel hardware must not crowd the aperture (8 mm). **See §8.1 for the authority trace — neither supersedes the other** |
| Antenna connector | panel/bulkhead, **left half of the top edge** | |
| Pigtail | u.FL → bulkhead, **minimum bend radius 5 mm**, **service loop ≥15 mm** | Per D-040: no controlled-impedance RF on the main PCB |

~~**Antenna storage** runs along the **left wall**, sized for the stowed whip, and **must
terminate below Y = 100 mm**.~~ **DELETED 2026-08-24 by D-219 (O-6 closed).** The locked
915 MHz whip, Taoglas **`TI.92.2113`**, is **198 ± 3.3 mm × Ø13 mm** against a cavity whose
longest internal diagonal is **≈ 172 mm** — **it never fitted inside the device in any
orientation.** It is **removable and carried separately when detached**. **No internal storage
channel, no left-side holder and no requirement forcing the antenna inside the enclosure
remains current.** **The antenna MPN is unchanged.** The freed **LEFT internal wall now belongs
to the 433 MHz flex, its cable and service access** (§8.2 / D-118).

### 8.1 915 MHz SMA ↔ IR spacing — authority trace (FBV2-MECH-002)

Two spacing figures were in this document and they were read as a contradiction. **They are not.**
They measure different things, and the later engineering ruling **added** the second without revoking
the first.

| rule | datum | first stated | latest restatement | status |
|---|---|---|---|---|
| **≥ 15 mm** | **centre-to-centre**, bulkhead clearance hole ↔ IR window | **FBV2-MECH-001**, 2026-08-22 — §8 and dimension row 12, written against a *generic* fitted whip shadowing the emitter cone | **M-13**, FBV2-S2-001, 2026-08-23: *"≥ 15 mm from either IR window"* | **CURRENT — LOCKED** |
| **≥ 8 mm** | **edge-to-edge**, SMA **body** ↔ IR **aperture** | **D-120**, FBV2-S1-004, 2026-08-23, when the 915 MHz external interface was defined (B-52) | **M-13**, FBV2-S2-001, 2026-08-23, with the Amphenol `095-902-568-150` bulkhead known: *"≥ 8 mm edge-to-edge between the SMA body and either IR aperture"* | **CURRENT — LOCKED** |

**Finding: the 8 mm rule did NOT supersede the 15 mm rule.** The most recent ruling to touch this (**M-13**, FBV2-S2-001) states **both, in the same sentence**, so the 15 mm figure is not stale —
it was re-asserted after the 8 mm rule existed. Retaining only 8 mm would have discarded a live
requirement; retaining only 15 mm would have discarded the panel-hardware clearance D-120 added.
**Both are recorded, with their datums made explicit — that is the actual defect that was fixed here:
neither figure previously said what it was measured between.**

**Consistency check (CAD-TO-VERIFY, no CAD in this task).** A standard SMA bulkhead hex is roughly
9.5 mm across flats / ~11 mm across corners, and an IR aperture for the Ø5 mm `TSAL6100` or the
`TSOP38238` lens is roughly Ø5.5–6.0 mm. On those figures, **8 mm edge-to-edge implies ≈ 15.5–16.5 mm
centre-to-centre**, i.e. the two rules are mutually consistent and **8 mm edge-to-edge is the binding
one**. **The Amphenol `095-902-568-150` body OD is NOT measured here** — confirm it against the
manufacturer drawing at FBV2-P1 / enclosure CAD. If the real body proves smaller than assumed, the
15 mm centre rule becomes the binding one instead; **satisfy whichever is larger.** **B-52 stays OPEN**
— spacing is recorded, **no CAD exists**.

---

## 9. Face summary

| face | contents |
|---|---|
| **Front** | Display/touch (upper), D-pad (lower left), A + B (lower right), microphone aperture (bottom, opposite the speaker), **RGB status light (position deliberately not locked — see M-11)** |
| **Top** | Antenna bulkhead connector (left half), IR TX + IR RX windows (right half) with an opaque barrier |
| **Left** | Antenna storage channel, terminating below Y = 100 mm |
| **Right** | **24-contact (2×12) keyed recessed community connector** (upper/middle) — **built and footprint-verified, 30.48 × 8.13 × 5.33 mm body over a 27.94 × 7.87 mm through-hole field** — Power control (lower), recessed BOOT access |
| **Bottom** | USB-C (centre), microSD (left of USB-C) |
| **Rear** | NFC loop zone (upper third), battery (lower two-thirds), speaker opening (lower right), branding |

**REMOVED and not to reappear:** HOME, Volume Up, Volume Down.

---

## 10. Open items

| # | item | why it is open |
|---|---|---|
| ~~M-01~~ | ~~Display size~~ | **CLOSED by D-072 — 3.5 inch.** |
| ~~M-02~~ | ~~Battery capacity target~~ | **CLOSED by D-071 — 60 × 75 × 8.0 mm, ~2500–3000 mAh.** |
| ~~M-06~~ | ~~Display MPN and FPC interface~~ | **CLOSED 2026-08-23 by D-074…D-078.** `ER-TFT035IPS-6` + `ER-TPC035-6`; 50-pin 0.5 mm bottom contact, 0.30 ± 0.03 mm; `J1` = `FH69-50S-0.5SH` |
| ~~M-07~~ | ~~Backlight driver re-derivation~~ | **CLOSED 2026-08-23 by D-079.** TPS61169 retained from `+3V3`; `R69` = 1.87 R, `R70`–`R73` = 4 × 33 R |
| **M-08** | **Connector placement below the display** | The 2.3 mm `J1` competes with the D-pad, A/B and the mic aperture for the 70.04 mm of cavity height under the panel. **Blocks nothing before FBV2-P1** (B-33) |
| ~~M-03~~ | ~~Community connector MPN~~ | **CLOSED 2026-08-23 by D-093** — Samtec `BCS-112-S-D-HE`. *(The D-083 Harwin selection was rejected as obsolete and replaced.)* |
| **M-09** | Confirm the connector body height | **DOWNGRADED to LOW 2026-08-23.** With `BCS-112-S-D-HE` the column is 2.0 shell + **5.33 connector** + 1.6 PCB + 8.0 battery + 0.6 + 2.0 shell = **19.53 mm of 23.0 external, 3.47 mm spare** — level with the control region and **no longer the sole governing column**. The 5.33 mm figure is read from the Samtec series print and cross-checked three ways; **confirm against the individual 3D model at FBV2-P1** |
| **M-10** | **Insertion load path** | **~33 N average** (24 contacts × 1.39 N avg), **peak higher** — Samtec publishes averages, and its own note states the peak occurs during the spreading stage. The enclosure must carry it on a boss or rib (D-097) |
| **M-11** | **Front RGB status-light aperture — NEW 2026-08-23 (FBV2-S1-008)** | **The requirement is FRONT-FACING and visible; the exact front position is deliberately NOT locked.** Upper bezel, lower bezel, beside the display or near the controls are all acceptable. **It is NOT a top-edge part** — the top crown is the IR and antenna region. `D13` is a **surface-mount PLCC-4, 3.50 × 2.80 × 1.85 mm, 120° emission, water-clear lens** on the **front-facing PCB surface**, so the enclosure must provide a **diffuser or light pipe: no protruding bare LED, and no direct line of sight to the die.** A water-clear 120° source behind a bare hole is a point glare source; the diffuser is what makes it read as a status light. **Delivered output is roughly 80 / 87 / 42 mcd (R/G/B)** at 1.0–1.7 mA per channel, so the optical path must not be lossy — budget for a short pipe or a thin diffuser, not a deep light guide. **Placement and CAD own the final position.** Does not block FBV2-A2 |
| **M-12** | **Community connector land field — NEW 2026-08-23 (FBV2-S1-009)** | The footprint is verified against the manufacturer drawing (§5), so this is **not** a dimensional unknown. It is a **floorplanning constraint**: **24 × Ø0.71 mm plated through-holes in a 27.94 × 7.87 mm field**, the only THT field on the board, blocking routing on every layer beneath it, on the **right edge** where the recess and its asymmetric key also live. Combined with M-10's ~33 N insertion load and M-08's contest for the space under the display, **the right-hand strip is now the most constrained region of the PCB.** Does not block FBV2-A2; **must be resolved first at FBV2-P1** |
| **M-14** | **Microphone acoustic port — NEW 2026-08-23 (FBV2-S2-002, D-203/B-63)** | `MK1` is a **BOTTOM-PORT** MEMS microphone. It sits on the **TOP** of the PCB and listens **THROUGH** the board, so **the acoustic path leaves on the BOTTOM face**. The board now carries a **Ø1.05 mm non-plated hole** concentric with pad 4 — the diameter is the PUI drawing's own pad-4 GND-ring inner diameter, i.e. the part's port aperture. **The enclosure aperture and any acoustic gasket belong on the BOTTOM face, not the component face.** The region marked by the dashed `B.Fab` circle in the footprint must stay free of copper pours, traces, vias, silkscreen and mask steps **on both faces** so the port can be sealed. Does not block FBV2-A2; **input to FBV2-P1 and to the enclosure CAD** |
| **M-13** | **Manual-assembly and panel-hardware consequences — NEW 2026-08-23 (FBV2-S2-001), AMENDED 2026-08-23 (FBV2-MECH-002)** | **CURRENT TRUTH: exactly TWO parts are manual / secondary assembly for the first five — `J5` (24 × Ø0.71 mm THT) and `D1` (5 mm THT IR LED).** ~~and now `J1`~~ — **`J1` IS NOT MANUAL. SUPERSEDED by D-206 / D-207: JLC carries the genuine Hirose `FH69-50S-0.5SH` (1,072 in stock, live 2026-08-23), so `J1` is MACHINE-PLACED.** B-47 / D-194 remains correct and unaffected: it says there is **no drop-in second source** for the display connector, which was never a statement about whether JLC can place it. **The 915 MHz interface is now one orderable assembly, Amphenol `095-902-568-150`**, which carries its own **SMA bulkhead with nut and washer**: the panel needs a **Ø6.5 mm clearance hole on the top edge, left half**, **≥ 15 mm from either IR window** and **≥ 8 mm edge-to-edge between the SMA body and either IR aperture** (B-52), with the **right-angle** AMC plug chosen to keep the vertical stack low over a flat-lying module. Does not block FBV2-A2; **input to FBV2-P1 and to the enclosure CAD** |
| M-04 | Battery SKU | Envelope frozen; SKU at procurement |
| M-05 | Cosmetic surfacing, radii, texture, branding | **Does not block FBV2-A2** |

---

## 11. Consistency guard

`tools/check_mechanical_consistency.py` parses the machine-readable block in
*Enclosure Field Slate v5*. That block still reports
`INTERNAL_CAVITY_MM: not published` and `PCB_FIT_STATUS: UNVERIFIED`, which was
**true when written and is now superseded for Full Beta v2 by this document.**

`hardware/beta/mechanical/` and the Field Slate documents were **not modified** —
this task had no authority to touch them. Reconciling the guard script and the
Field Slate block is a follow-up task requiring authority over those files.

```
FBV2_EXTERNAL_MM:        80 x 160 x 23     LOCKED
FBV2_WALL_MM:            2.0               TARGET
FBV2_INTERNAL_CAVITY_MM: 75.0 x 155.0 x 18.5   TARGET
FBV2_PCB_MAX_MM:         72.0 x 152.0      TARGET
FBV2_PCB_TARGET_MM:      72.0 x 148.0      LOCKED (D-239)
FBV2_PCB_THICKNESS_MM:   1.6               LOCKED
FBV2_BATTERY_MM:         57 x 75 x 8.0 MAX  LOCKED (D-239, supersedes D-071 width)
FBV2_BATTERY_CANDIDATES: PKCELL LP785060 7.3x50x60 2500mAh PCM+JST-PH;
                         LP755070 7.5x50x70 3000mAh PCM+leads   VERIFIED (D-239)
FBV2_BATTERY_TARGET_MAH: 2500-3000                     UNCHANGED (D-071)
FBV2_DISPLAY_SIZE_IN:    3.5               LOCKED (D-072)
FBV2_DISPLAY_ENVELOPE_MM: 60 x 90 x 4.5    TARGET
FBV2_DISPLAY_ACTUAL_MM:  56.54 x 84.96 x 3.95+/-0.25   LOCKED (D-074)
FBV2_DISPLAY_MPN:        ER-TFT035IPS-6 + ER-TPC035-6  LOCKED (D-074)
FBV2_DISPLAY_FPC:        50 pin / 0.50 mm / bottom contact / 0.30+/-0.03 mm   LOCKED (D-075)
FBV2_DISPLAY_CONNECTOR:  Hirose FH69-50S-0.5SH         LOCKED (D-076)
FBV2_DISPLAY_CONN_LAND:  FH69 DEDICATED - not FH12/FH52E   LOCKED (D-194)
FBV2_DISPLAY_CONN_2ND:   NONE - single source           LOCKED (D-194)
FBV2_DISPLAY_CONN_ASSY:  MACHINE-PLACED at JLC          LOCKED (D-206/D-207)
FBV2_COMM_CONTACTS:      24 active (1 x 24, one pin per line)  LOCKED (D-237)
FBV2_COMM_PITCH_MM:      2.54                          LOCKED (D-083)
FBV2_COMM_CONNECTOR:     Samtec SSQ-124-02-G-S-RA (1x24 female RA)  LOCKED (D-237)
FBV2_COMM_BODY_MM:       61.47 long, mates .025in square post  LOCKED (D-237)
FBV2_COMM_FOOTPRINT:     1x24 PTH, 2.54 pitch, 1.02 drill, 58.42 pin span   LOCKED (D-237)
FBV2_COMM_KEYING:        CLOSED-END recess 62.5 mm vs 60.96 male body =
                         1.54 mm play on a 2.54 pitch; shift IMPOSSIBLE.
                         D-097 asymmetric key NO LONGER REQUIRED   LOCKED (D-240)
FBV2_COMM_PIN_ORDER:     ORDER-B, 180-deg-reversal safe, 0 power-to-signal  LOCKED (D-240)
FBV2_QWIIC:              JST SM04B-SRSS-TB, 1 GND/2 3V3/3 SDA/4 SCL   LOCKED (D-238)
FBV2_QWIIC_POWER:        ACC_3V3_SW - never ACC_5V_SW              LOCKED (D-238)
FBV2_BOOT_POS:           doc (28.300, 6.000) FRONT face, front-wall tool hole  LOCKED (D-242)
FBV2_POWER_SW_POS:       doc (66.700, 61.500) right wall           LOCKED (D-242)
FBV2_Z_CONNECTOR_COLUMN: 19.53 of 23.0 (3.47 spare)    TARGET (M-09)
FBV2_NFC_ZONE_MM:        48 x 48           LOCKED (D-127/D-128/D-131)
FBV2_SMA_IR_CENTRE_MM:   15.0 min c-c      LOCKED (FBV2-MECH-001, restated M-13)
FBV2_SMA_IR_EDGE_MM:      8.0 min edge     LOCKED (D-120, restated M-13)
FBV2_SPEAKER_Z_COLUMN:   12.6 of 23.0 (10.4 spare)   TARGET
FBV2_MANUAL_ASSY_REFS:   J5, D1            LOCKED (D-206/D-207)
FBV2_PCB_OUTLINE_MM:     72.0 x 148.0 x 1.6            LOCKED (D-239, FBV2-EXP-002)
FBV2_PCB_WALL_GAP_MM:    1.5 both sides - the >= 1.5 rule met EXACTLY   LOCKED (D-239)
FBV2_PCB_DATUM:          lower-left, X right, Y up     LOCKED (D-220)
FBV2_SIDE_CONVENTION:    F.Cu = FRONT, B.Cu = REAR     LOCKED (D-214)
FBV2_MIC_SIDE:           MK1 on B.Cu, listens forward  LOCKED (D-214)
FBV2_REAR_STACK_MM:      NFC 48 + BAT 75 + SPK 20 = 143 of 155   LOCKED (D-215)
FBV2_USB_SD_RULE:        >= 8.0 mm BODY edge-to-edge   LOCKED (D-217)
FBV2_USB_SD_ACTUAL_MM:   16.40                         MEASURED (FBV2-P1)
FBV2_BOSSES:             2 x M2 at dia 4.5 keepout     LOCKED (D-226/D-232/D-242)
                         re-searched on the 72 mm outline: dia6.0 = 0 sites,
                         dia4.5 = 2. Widening bought NO third screw.
FBV2_RETENTION:          rails + 4 ribs + 2 x M2 + J5 backing boss   LOCKED (D-232)
FBV2_SUPPORT_RIBS:       RIB_R1 RIB_R2 RIB_R3 RIB_B1   LOCKED (D-232, non-metallic)
FBV2_915_PIGTAIL:        RF Solutions CBA-UFLSMA20IP (200 mm)   LOCKED (D-223)
FBV2_915_ROUTED_MM:      138.48 of 200, 46.52 spare    MEASURED (FBV2-P1-002)
FBV2_915_WHIP_STORAGE:   NONE - deleted                LOCKED (D-219)
FBV2_DISPLAY_OFFSET_MM:  2.34 LEFT of centre           ACCEPTED, INTENTIONAL (D-225/D-239)
FBV2_Z_VERDICT:          PASS (19.5 of 23.0 on the governing column)
FBV2_PCB_FIT_STATUS:     RE-FLOORPLANNED 72x148 (FBV2-P1 RE-ISSUED = PASS, D-242)
```
