# FBV2-S1-009 — Community expansion port, sheet 09

**Task:** migrate the last Full Beta v2 schematic sheet, `09_community_header`.
**Date:** 2026-08-23. **Baseline:** `origin/master` = `8b906af` (FBV2-S1-008 docs).
**Verdict: PASS.** ERC **27 messages, 0 errors, 27 warnings** — down from 42 / 1 / 41.
**The design has zero ERC errors for the first time in the programme.**

**Preflight:** working tree clean, local `master` identical to `origin/master` at
`8b906af`. The only untracked paths were the two that have been present since
2026-08-20/21 (`hardware/beta-dm/fab/*.zip` and `hardware/beta/mechanical/`);
neither was touched. **No partial FBV2-S1-009 work existed.**

---

## 1. What sheet 09 was, and why it was rebuilt rather than patched

The inherited sheet was the Beta-DM community header and **almost nothing in it
survived a comparison against the locked v2 architecture**:

| inherited | required | disposition |
|---|---|---|
| `J5` **2 × 13 = 26 pins**, Samtec `TSW-113-08-G-D-RA`, **MALE** right-angle pin strip | 2 × 12 = 24, `BCS-112-S-D-HE`, **FEMALE** socket | **replaced** |
| **`J5` pin 1 = permanent raw `+3V3`** | forbidden by **D-057** | **deleted** |
| 14 × XGPIO (`XGPIO0`–`XGPIO13`) | **10**, locked by D-082 | `XGPIO10`–`13` **deleted** |
| `FAST_IO_GPIO43_HDR` on pin 23 | withdrawn by **D-106** | **deleted** |
| `RESERVED_NC` on pin 26 | no NC contact (D-081) | **deleted** |
| no `ACC_DETECT_N`, no `ACC_5V_SW`, no `NATIVE_A`/`NATIVE_B` | all four locked | **added** |
| `U15` TPS22918 — a **second, DNP** accessory 3.3 V switch | the rail is `U20` TPS22950C on sheet 01 | **deleted** |
| `09:ACC_3V3_SW` was a **sheet-local net fed by that DNP switch** | must be the real `01:ACC_3V3_SW` | **joined** |
| `U16` TCA9517A level translator, **DNP** | TCA4307 hot-swap buffer (O-4) | **replaced** |
| `R49`/`R50` external pull-ups **4.7 kΩ, DNP** | re-derived and fitted | **1.5 kΩ, FITTED** |
| `D2`–`D7` TVS arrays, **all DNP** | protection on an exposed user port | **4 arrays, FITTED** |
| `R66` 330 Ω wired **straight** from `WAKE_ATTN_N_HDR` to `WAKE_INT_N` | **D-091 isolation FET** | **`Q10` added** |

**The two nets that mattered most were not connected at all.** `01:ACC_3V3_SW`
(the real switched rail at `U20` pin 5) and `09:ACC_3V3_SW` (fed by the DNP
`U15`) were **different nets**, and `01:ACC_5V_SW` reached nothing outside sheet
01. The community port had no power.

**This is the sixth consecutive migrated sheet on which an inherited `DNP` was
load-bearing** — `U16`, `R49`, `R50` and six TVS arrays. The pattern recorded at
FBV2-S1-007 held to the last sheet: **a `DNP` on a Beta-DM sheet describes what
was populated on that reduced build, not what the architecture requires.**

Given that inventory, the sheet was **regenerated from scratch** rather than
patched. `fork_equivalence.py` moves it from `norm` to `changed` and its
`SHEETS` list is now **empty**: no sheet is still byte-equivalent to Beta-DM.

---

## 2. Connector — final lock and footprint verification

**`J5` = Samtec `BCS-112-S-D-HE`.** Re-verified live on 2026-08-23 per **D-096**:
**ACTIVE, 385 pieces ship tomorrow**, $7.314 @ 1 / $5.667 @ 100, UL E111594,
RoHS, halogen-free (Br/Cl per JS-709C), MSL 1, probable COO Malaysia. 2 × 12,
24 contacts, .100 in / 2.54 mm, **FEMALE** Tiger Claw dual-beam pass-through
socket strip, **horizontal (right-angle) entry**, through-hole, 30 µin selective
gold.

**The footprint was re-derived from the manufacturer drawing, not carried
forward.** Samtec *RECOMMENDED PCB LAYOUT FOR BCS-1XX-XXX-X-XX-XXX*,
**REVISION B**, **FIG 3 = `BCS-1XX-XXX-D-HE-XXX`**:

| dimension | drawing | in the footprint |
|---|---|---|
| pitch within a row | **.100 in / 2.54 mm** | 2.54 mm |
| **row to row** | **.310 ± .002 in = 7.87 ± 0.05 mm** | **7.87 mm** |
| hole | **.028 in = 0.71 mm PTH** | 0.71 mm drill, 1.30 mm pad |
| pin-field length | positions × .100 − .100 = **27.94 mm** | 27.94 mm |

**A vertical 2 × 12 pattern is NOT a substitute** — its rows sit 2.54 mm apart,
not 7.87 mm. That is the single most expensive mistake available on this sheet
and it is why the drawing was re-read.

- **Pad numbering: odd = row A, even = row B**, alternating along the length,
  matching **D-084** and matching the `Conn_02x12_Odd_Even` symbol exactly
  (verified pin by pin against the netlist — see §3).
- **Pin 1 is a rectangular pad** with a silkscreen tick and a `PIN 1` legend.
- Body **30.48 × 8.13 × 5.33 mm**; F.Fab outline and a `MATES ->` direction mark;
  courtyard 31.48 × 9.13 mm.
- **No key contact.** The enclosure supplies polarisation and keying (**D-097**).
- **`BCS-112-L-D-HE`** remains a plating-only alternate with an identical
  footprint — but 100 mating cycles against 2 500, which is why `-S` is locked.
- **The Harwin `M20-7881242` is rejected and obsolete** and appears nowhere in
  the design except as a warning inside `J5`'s note.

**Assembly:** if the JLC service cannot place this through-hole part
automatically, it is a **manual / secondary assembly operation for the first five
boards.** The connector architecture is not compromised for SMT convenience.

---

## 3. The 24-contact allocation, verified pin by pin

Read from a `kicad-cli` netlist export and compared against **D-084**, all 24
match:

| pin | net | pin | net |
|---|---|---|---|
| 1 | `XGPIO0` | 2 | `EXT_SCL` |
| 3 | **`ACC_3V3_SW`** | 4 | **GND** |
| 5 | `XGPIO1` | 6 | `EXT_SDA` |
| 7 | `NATIVE_A` (GPIO38) | 8 | `XGPIO2` |
| 9 | **GND** | 10 | **`ACC_5V_SW`** |
| 11 | `NATIVE_B` (GPIO47) | 12 | `XGPIO3` |
| 13 | `XGPIO4` | 14 | `WAKE_ATTN_N` |
| 15 | **`ACC_3V3_SW`** | 16 | **GND** |
| 17 | `XGPIO5` | 18 | `XGPIO6` |
| 19 | `XGPIO7` | 20 | `XGPIO8` |
| 21 | **GND** | 22 | **`ACC_5V_SW`** |
| 23 | `ACC_DETECT_N` | 24 | `XGPIO9` |

- **24 active contacts, no NC, no key contact.**
- **No duplicate GPIO.** Only GND (×4) and the two rails (×2 each) repeat.
- **Every power contact is vertically paired with GND** — 3/4, 9/10, 15/16,
  21/22 — so a row-swap can only make a current-limited rail-to-ground short,
  never 5 V on a logic pin. **All 3.3 V in row A, all 5 V in row B.**

**Accessory-facing wording, recorded on the sheet and required on the
silkscreen and in accessory documentation:**

> **COMMUNITY PORT — 3V3 LOGIC ONLY / 5V PIN IS POWER OUTPUT ONLY**

> The two `ACC_3V3` contacts share the total 3.3 V rail limit. The two `ACC_5V`
> contacts share the total 5 V rail limit. **Duplicate contacts do not multiply
> the available current.**

---

## 4. External I²C — the TCA4307 (O-4 approved)

**`U16` = TI `TCA4307DGKR`, LCSC `C880333`, VSSOP DGK-8.** Verified live per
D-096: **3 248 in stock, ships now**, $2.51 @ 1 / $1.71 @ 1 k. **FITTED** —
it replaces a part that was DNP.

Every claim below is from **SCPS270B (Aug 2020, revised Nov 2023)**, read in this
session:

| parameter | value | why it matters here |
|---|---|---|
| V_CC | **2.3 – 5.5 V** | runs from `ACC_3V3_SW` |
| **powered-off I²C pins** | **high-impedance** | with the rail off the part is invisible to the internal bus **on both sides** — the isolation is structural, not a firmware promise |
| **`EN`** | active **HIGH**, V_IH 0.7 × V_CC, V_IL 0.3 × V_CC | `ACC_PWR_EN`, held LOW by `R17` 100 kΩ on sheet 08 → **isolated until explicitly enabled** |
| **connect condition** | IN is not joined to OUT until a **STOP or bus-idle** | live insertion cannot corrupt a transfer in progress |
| **precharge** | **V_PRE 0.8 / 1.0 / 1.2 V** on all four SDA/SCL pins | limits the charge dumped into parasitic capacitance at insertion |
| **stuck-bus timer** | **t_STUCKBUS 25 ms MIN / 40 ms typ / 65 ms MAX** | the accessory compatibility rule below |
| **recovery** | **up to 16 pulses on SCLOUT**, f 5.5 / 8.5 / 14 kHz | frees a slave that is holding SDA low |
| **`READY`** | **open drain**, high only when `EN` high **and** the sides are connected; V_OL 0.4 V @ 3 mA | the single best bring-up observable on this sheet |
| clock stretching, arbitration, synchronisation | **supported** | |
| **f_SCL max** | **400 kHz** | **fast mode. NOT 1 MHz, and no such claim is made.** |
| rise-time accelerators | **2 – 5 mA** on a rising edge | margin on the pull-ups, not the mechanism |
| I_CC / I_SD | 2.5 mA typ, 4.5 mA max / **10 µA typ, 30 µA max** | |
| UVLO | 2.1 V rising, 2.0 V falling | |
| C_IO (SDA/SCL) | 5 pF typ, 10 pF max | inside the bus budget |

**The circular dependency is broken.** `ARCHITECTURE.md` recorded the weakness
plainly: *"its disable control, `ACC_PWR_EN` = `U3` P17, sits behind the bus it
protects."* A wedged accessory required the MCU to command the expander **over
the very bus that was wedged**. The TCA4307 disconnects and clocks the bus free
**autonomously**, so `ACC_PWR_EN` is now a second, manual lever rather than the
only one.

> ### ACCESSORY COMPATIBILITY RULE — normative
> **An accessory must never hold `EXT_SDA` or `EXT_SCL` low for longer than
> 25 ms**, the t_STUCKBUS **minimum**. That is a hard limit on clock stretching
> and on slow bit-banged accessory firmware. Beyond it the buffer will
> disconnect the accessory and issue up to 16 recovery clocks. The number to
> design against is the **minimum**, not the 40 ms typical.

**`READY` handling.** 10 kΩ to the TCA4307's **own** V_CC (`ACC_3V3_SW`), which
is TI's application value and the value the datasheet's own UVLO
characterisation is specified with. **It is deliberately not pulled to `+3V3`** —
that would push current into an unpowered device's pin and defeat the
powered-off high-impedance property the whole isolation argument rests on. It is
brought out to **`TP44`** and **does not consume a PCAL pin in Rev 1**. Noted:
while `EN` is low the datasheet warns that current flows from V_CC through the
pulled-down `READY` pin — 0.33 mA here — but the rail is OFF by default, so the
no-accessory state costs nothing.

**Cost, stated plainly:** the TCA4307 is roughly **$1.20–2.00 more per board**
than the TCA9517A it replaces. That buys hot-plug tolerance and autonomous
stuck-bus recovery on a **user-facing, hot-pluggable** port, and it removes a
failure mode that had no other fix.

---

## 5. External I²C pull-ups and signal integrity

**The inherited 4.7 kΩ is rejected.** Rise time is
t_r = 0.8473 × R × C.

**Design-point external capacitance = 200 pF**: ≈ 20 pF of board trace, ≈ 5 pF of
connector, ≈ 100 pF for 300 mm of accessory cable, ≈ 50 pF of accessory module.
The I²C specification's own ceiling is 400 pF.

| R | t_r at 200 pF | vs 300 ns (400 kHz) | t_r at 400 pF | vs 1000 ns (100 kHz) |
|---|---|---|---|---|
| **4.7 kΩ (inherited)** | **796 ns** | **FAIL, 2.7×** | 1 592 ns | **FAIL** |
| 2.2 kΩ | 373 ns | fail | 745 ns | pass |
| **1.5 kΩ — SELECTED** | **254 ns** | **PASS** | 508 ns | **PASS** |
| 1.0 kΩ | 169 ns | pass | 339 ns | pass — but 2.9 mA static sink |

**1.5 kΩ passes fast mode on the static pull-up alone**, with the TCA4307's
2–5 mA rise-time accelerator as *margin* rather than as the mechanism. Static
sink to 0.4 V is **1.93 mA**, comfortably inside the 3 mA an I²C device must sink
and inside the buffer's own 4 mA V_OL condition.

> **Published accessory rule:** keep total external bus capacitance **≤ 200 pF
> for 400 kHz** and **≤ 400 pF for the 100 kHz bring-up mode.**

**100 kHz bring-up is retained** and is the recommended first-contact speed.
**No 1 MHz claim is made anywhere** — the buffer is a 400 kHz part.

**The internal bus is untouched:** `R19`/`R20` = 2.2 kΩ remain its **only**
pull-up pair (D-139). No second internal pair was added, and the external
pull-ups hang on `ACC_3V3_SW`, so they disappear with the accessory rail.

**The 22 Ω series resistors are retained and re-justified against the buffer
that is actually fitted.** They sit between the buffer's OUT pins and the
contacts. Delay is negligible — 22 Ω × 200 pF = **4.4 ns** against a 300 ns
budget — and the accelerator's 5 mA costs at most **110 mV** across them. What
they buy is that a short or an ESD strike at the contact is isolated from the
pull-up node and from the buffer pin. The pull-ups are on the **buffer side** so
the accelerator and the pull-up share a node.

---

## 6. Accessory detect

Unchanged in architecture, now actually built: **contact 23, asserted by the
accessory shorting it to the adjacent GND at contact 21 with one 0 Ω link.**

- **The 100 kΩ pull-up is `R129` on sheet 08, at the expander.** Sheet 09 adds
  **no second pull-up** — that was written into `R129`'s note at FBV2-S1-008 and
  is honoured here.
- **`R64` 100 Ω series was added.** D-090 did not list `ACC_DETECT_N`, which was
  an inconsistency: the contact is exposed and runs straight to a PCAL input. It
  now has the same fault-current limit as every other exposed signal, for one
  0603, and it is electrically free behind a 100 kΩ pull-up.
- **`D5` channel 4** protects it.
- **`TP43`** observes it at the connector.
- **Detection works with both rails off**, because the pull-up and the expander
  both run from `+3V3`. That is what makes **MX-3** implementable and what makes
  a flipped accessory passively safe — it cannot ground contact 23, so it never
  receives power.

**Hot-plug bounce — reviewed, and no RC added.** A wiping mechanical contact into
a 100 kΩ pull-up will chatter for a few milliseconds. It is debounced in
**firmware, 20 ms to assert and 20 ms to de-assert.**

> **An RC here would be actively harmful.** The same time constant that
> suppresses insertion chatter also **delays removal detection**, and removal is
> the safety-critical edge: **MX-6 requires both rails down within 100 ms of
> detect loss.** A passive filter cannot be asymmetric; firmware debounce can,
> and costs nothing. **No needless RC components were added.**

---

## 7. 3.3 V accessory rail — R_ILIM re-derived, not copied

**Architecture unchanged:** `+3V3` → **`U20` TPS22950C** → `ACC_3V3_SW`.
**`TPS22950CDDCR`**, DDC / SOT-23-thin 6-pin, confirmed **ACTIVE** at TI on
2026-08-23 per D-096. Retained: reverse-current blocking (always on), adjustable
current limit, open-drain `FLT`, thermal shutdown 170 °C, short protection,
**external 100 kΩ pull-down on `ON` (`R98`)**, default OFF.

**The current-limit equation from SLVSFJ2B §10.2.2 is**

> **I_LIM = 1.18 × (R_ILIM in kΩ)^−1.072**

verified against three datasheet rows: 610 Ω → 2.005 A (table 2.0), 1.15 kΩ →
1.016 A (table 1.0), 2.21 kΩ → 0.504 A (table 0.5). The tolerance band is
**±25 %**.

**Re-derived against the CURRENT power budget**, which has grown since
FBV2-COMM-001 by the infrared transmitter (FBV2-S1-007) and the front RGB
(FBV2-S1-008):

| load | mA on `+3V3` |
|---|---|
| internal subtotal as analysed at FBV2-COMM-001 | 769 |
| **IR transmitter, burst average** (150 mA peak is supplied by `C12` 22 µF, not by the rail) | **+50** |
| front RGB at white | +4.2 |
| `U23` third expander | +0.03 |
| **internal worst case now** | **≈ 823** |

| R_ILIM | I_LIM typ | worst-high | `+3V3` during an accessory hard short | % of the TPS63020's 2 A | verdict |
|---|---|---|---|---|---|
| **1.5 kΩ — RETAINED** | **0.764 A** | **0.955 A** | 823 + 955 = **1 778 mA** | **89 %** | **no foldback, no brownout** |
| 1.21 kΩ | 0.966 A | 1.21 A | 2 033 mA | 102 % | over the rating |
| 1.15 kΩ | 1.016 A | 1.27 A | 2 093 mA | **105 %** | foldback → brownout → SD corruption |

**1.5 kΩ survives re-derivation** — the margin narrowed from 86 % to **89 %**
because of the IR transmitter, and it still holds. Worst-**low** limit is
**0.573 A** against the published 400 mA, so a compliant accessory has **43 %
headroom** and never trips it.

**Published limit for the first five boards: 400 mA TOTAL across both 3.3 V
contacts.** Nothing about the switch or the connector prevents 800 mA — the
**2 A regulator** does, once a fault on top of the internal worst case is
counted. One 0603 lifts it when the real internal figure is measured.

---

## 8. 5 V accessory rail — re-derived

**Architecture unchanged and still fully independent:**
`BQ25185_SYS` → **`U21` TPS61023DRLR** at 5.0 V → **`U22` TPS22950CDDCR** →
`ACC_5V_SW`.

**It is not USB `VBUS`, not the NFC 5 V fallback, and connected to neither.**
Verified from the netlist: `ACC_5V_RAW` touches only `U21`, `U22`, `C65`, `C66`,
`R99` and `TP28`. The NFC fallback (`U13`, `L2`, `C34`, `C35`, `R44`, `R45`) is a
separate, still-DNP branch on `NFC_5V_PA_PENDING`. **Only `SYS` and the TPS61023
device family are shared** — which is the whole extent of D-088's consolidation.

Re-derived from SLVSDK9:

| item | value | check |
|---|---|---|
| feedback | `R99` 732 kΩ / `R100` 100 kΩ, V_REF ≈ 0.6 V (±2.5 %) | V_OUT = 0.6 × (1 + 7.32) = **4.99 V** ✓ |
| inductor | `L4` **1 µH**, Würth `74438357010` WE-MAPI 4030, **FITTED** | peak inductor current at the 0.86 A worst-high limit, V_SYS 3.0 V: I_in 1.59 A + ½ΔI 0.6 A = **2.19 A**, so **I_sat ≥ 3 A is the requirement** — confirm the part's I_sat at BOM lock (**B-68**) |
| switching | **1 MHz** above V_IN 1.5 V, folding to 0.5 MHz below 1 V | ΔI = V_IN × D / (L × f) = 1.2 A pk-pk at V_SYS 3.0 V |
| input cap | `C64` 10 µF | |
| output caps | `C65` + `C66` = **44 µF** | also the load the boost starts into — see §9 |
| **switch current limit** | **3.7 A valley (typ)** | ≫ the 2.19 A peak |
| **shutdown** | **true input-to-output disconnection** | `ACC_5V_RAW` really goes to 0 V when the boost is disabled — this is what makes the split enable worth having |
| minimum `SYS` | V_IN 0.5–5.5 V; **MX-7 disables this rail below V_BAT 3.4 V** long before the converter cares | |
| **start-up** | **t_SS ≈ 700 µs typical**, EN high to V_OUT at target | §9 |
| thermal at 300 mA | P_out 1.5 W, ≈ 0.17 W dissipated at 90 % efficiency in SOT-563 | ≈ 34 K rise; acceptable, measure on the first boards |

**`U22` R_ILIM = 1.65 kΩ retained**, re-derived with the same equation:
**I_LIM = 0.690 A typ, band 0.52 – 0.86 A**. Worst-low 0.52 A against the
published 300 mA gives **73 % headroom**; worst-high 0.86 A is inside the
TPS61023's 3.7 A switch limit with the input current above. **Published limit for
the first five boards: 300 mA TOTAL across both 5 V contacts.**

---

## 9. Split 5 V enables — the CTO reliability refinement

**The single `ACC_5V_EN` is superseded.** It drove both the boost `EN` and the
load-switch `ON` from one expander pin.

| new net | source | destination | safe-state pull |
|---|---|---|---|
| **`ACC_5V_BOOST_EN`** | **`U3` P13** | `U21` `EN` (TPS61023) | `R102` 100 kΩ down, sheet 01 |
| **`ACC_5V_SW_EN`** | **`U23` P04** | `U22` `ON` (TPS22950C) | **`R131` 100 kΩ down, NEW** |

`U23` P04 was a spare. **`U23` is now 5 used / 11 spare**, plus the formal
`RESERVED_SPARE` on P03 — matching the CTO's expectation exactly.

**`R131` is mandatory, not a convenience.** SLVSFJ2B specifies a 500 kΩ smart
pull-down inside the TPS22950C **and still requires an external one**, and the
PCAL9535A powers up with every pin high-impedance. Without it the 5 V contact
would be defined only by leakage between power-on and the first firmware write.
**`TP47`** observes the new enable.

**Power-up sequence (recorded on the sheet and in the firmware contract):**

1. verify `ACC_DETECT_N` asserted
2. `ACC_3V3_EN` = 1
3. wait **≥ 5 ms** (MX-4)
4. `ACC_5V_BOOST_EN` = 1
5. wait **≥ 5 ms** for the converter to settle
6. `ACC_5V_SW_EN` = 1

**Power-down, exactly reversed:** `ACC_5V_SW_EN` → `ACC_5V_BOOST_EN` →
`ACC_3V3_EN`. Detect loss or `FLT` still forces a prompt shutdown (MX-5, MX-6).

**Step 5 is derived, not guessed.** The TPS61023 soft-start is **700 µs typical**
from `EN` high to the output reaching target. The datasheet gives **no maximum**,
so the first build uses **5 ms — seven times typical — and measures it on the
first boards** (**B-69**).

**What the split actually buys, beyond tidiness:**

1. **Two independent series disconnects** in the 5 V path. The TPS61023 has
   *true* input-to-output disconnection in shutdown and the TPS22950C adds
   reverse-current blocking on top. A single stuck enable can no longer energise
   the contact.
2. **The start-up number becomes a board constant.** With `U22` still off, the
   boost starts into a **known 44 µF** of `C65`/`C66` — not into an unknown
   hot-plugged accessory. The old single-enable arrangement made soft-start
   duration an accessory variable.
3. **No PGOOD IC was added**, as instructed.

---

## 10. Power fault

Unchanged and verified: both TPS22950C open-drain `FLT` outputs **wire-OR** into
`ACC_POWER_FAULT_N`, one 100 kΩ pull-up (`R103`), one PCAL input (**`U3` P15**),
two test points (`TP27`, `TP33`). **No separate PCAL input per `FLT`.**

Firmware attribution is unchanged (**MX-5a**): on a fault, disable one rail,
observe whether `ACC_POWER_FAULT_N` clears, identify the rail, shut down safely.

**The honest caveat stands (B-35):** SLVSFJ2B Table 9-1 asserts `FLT` on
**thermal shutdown and reverse current only**. A plain current-limit event leaves
`FLT` high-Z. A hard short reaches TSD within tens of milliseconds and is then
reported; a **partial** overload inside the thermal envelope is invisible to the
host. Firmware must not treat `FLT` as a complete overcurrent indication.

---

## 11. `ACC_PWR_EN`

Retained as the **manual** TCA4307 enable on `U3` P17, with its safe-state
pull-down `R17` 100 kΩ verified present on sheet 08 (netlist: `R17.1`, `U16.1`,
`U3.20`).

**It is no longer the only recovery lever.** The TCA4307 isolates and clocks a
wedged bus free by itself, so the old system-level failure — *"bad accessory
hangs I²C → MCU cannot command the PCAL to disable I²C"* — **is closed**.
`ACC_PWR_EN` is now belt-and-braces: a deliberate, firmware-commanded isolation
on top of an autonomous one.

---

## 12. WAKE / ATTN isolation

`Q10` **2N7002** N-channel pass gate between `WAKE_ATTN_N_HDR` and
`WAKE_INT_N`, **gate driven by `ACC_3V3_SW`** — D-091 as written, and the first
time it has actually existed in copper.

**Orientation is load-bearing and is the whole reason the gate works.** The
**source faces the connector** and the **drain faces the internal line**, so the
body diode's anode is on the accessory side.

- **Rail off:** gate at 0 V, channel off; an accessory pulling the contact to
  ground **reverse-biases** the body diode against the internal 3.3 V. **A
  shorted or hostile accessory cannot hold `WAKE_INT_N` low and cannot starve
  the internal buttons. B-08 is closed in hardware.** Reverse the FET and the
  body diode alone would defeat the arrangement.
- **Rail on:** `R63` 10 kΩ to `ACC_3V3_SW` holds the source near 3.3 V, so
  V_GS ≈ 0 and the FET idles off; the accessory pulling the contact low raises
  V_GS to ≈ 3.3 V, the FET conducts and the internal line follows. Standard
  bidirectional pass gate.
- **`R63` must pull to `ACC_3V3_SW`, not `+3V3`** — a permanent pull-up would
  keep the contact live with the accessory rail off and re-open B-08 from the
  other direction.
- **`R66` 330 Ω is retained and is electrically correct**, sitting between the
  contact and the FET source.

**Residual, bounded and recorded.** If a hostile accessory *drives* the contact
to 5 V while the rail is off, the body diode conducts from source to drain and
injects **(5 − 3.3 − 0.7) / 330 = ≈ 3 mA** into `WAKE_INT_N`. That is inside
every clamp on the net and is precisely why `R66` is 330 Ω rather than 100 Ω.

**Consequence (B-36), documented:** accessory-initiated wake from sleep requires
`ACC_3V3_SW` to remain enabled during sleep, which costs the TPS22950C quiescent
current plus whatever the accessory draws.

---

## 13. Signal protection and the ESD review

| contact group | series | TVS | verdict |
|---|---|---|---|
| `XGPIO0`–`XGPIO9` | **100 Ω** each (`R51`–`R60`) | **`D3`, `D4`, `D5`** | **PROTECTED** |
| `NATIVE_A`, `NATIVE_B` | **100 Ω** (`R61`, `R62`) | **`D2`** | **PROTECTED** — the only two contacts with a direct MCU path, and neither is a strapping pin |
| `EXT_SDA`, `EXT_SCL` | **22 Ω** (`R48`, `R47`) | **`D2`** | **PROTECTED**, and behind a hot-swap buffer |
| `WAKE_ATTN_N` | **330 Ω** (`R66`) | **`D5`** | **PROTECTED**, plus the `Q10` isolation gate |
| `ACC_DETECT_N` | **100 Ω** (`R64`, **new**) | **`D5`** | **PROTECTED** — was a gap in D-090 |
| `ACC_3V3_SW` ×2 | — | **none, deliberately** | **PROTECTED by construction** |
| `ACC_5V_SW` ×2 | — | **none, deliberately** | **PROTECTED by construction** |

**TVS part, verified: TI `TPD4E1B06DRLR` (SLVSBQ8E, Oct 2024).**
4-channel **bi-directional**; **IEC 61000-4-2 ±12 kV contact / ±15 kV air-gap**,
beyond level 4; IEC 61000-4-5 surge **3.0 A (8/20 µs)**; **I/O capacitance
0.7 pF typical**; leakage **0.5 nA maximum**; **V_RWM ±5.5 V**; DRL / SOT-563
1.6 × 1.6 mm; pinout 1 = IO1, 2 = GND, 3 = IO2, 4 = IO3, 5 = NC, 6 = IO4
(confirmed against the netlist). **Sixteen channels are needed and four arrays
are fitted.**

**Two deliberate decisions, both stated rather than assumed:**

1. **The arrays are FITTED, not DNP.** D-090 specified TVS only on the natives
   and the I²C pair, on the reasoning that the natives are the only contacts
   with a direct MCU path. That reasoning under-weights the XGPIO: they run to a
   PCAL9535A, and a destroyed expander costs a board, not a $0.55 chip. The
   footprints already existed and were already marked DNP; **fitting them is
   four SOT-563 parts and 0.7 pF, and shipping a user-accessible connector with
   ten unprotected signal contacts is not a defensible state.** This is a
   low-risk correction, applied, rather than a blocker raised.
2. **No TVS on the two power rails.** **V_RWM is 5.5 V and `ACC_5V_SW` is 5.0 V
   nominal — there is no working margin**, and a clamp that close to the rail
   leaks and ages. The rails are protected instead by their own bulk capacitance
   (`C63`/`C37` on 3.3 V, `C67`/`C38` on 5 V), by the TPS22950C's ratings and by
   the current limit. Adding a 5.5 V array to a 5 V rail would be worse than
   adding nothing.

**No arbitrary RF or high-capacitance protection was added.** 0.7 pF is
negligible even on the 400 kHz I²C pair.

---

## 14. Backpower / abuse matrix

Every row was reasoned against the netlist and the datasheets, not asserted.

| # | condition | result | verdict |
|---|---|---|---|
| 1 | accessory absent | both rails off (`R98`, `R102`, `R131` pull-downs); buffer unpowered and high-Z; `ACC_DETECT_N` high through `R129` | **SAFE** |
| 2 | accessory inserted **reversed** (rows swapped) | every power contact is paired with GND, so the worst case is a **current-limited rail-to-ground short**; and the accessory cannot ground contact 23, so **detect never asserts and neither rail is ever enabled** | **SAFE** |
| 3 | one-column offset attempt | prevented **mechanically** — the enclosure recess is closed at both ends with ≤ 0.3 mm clearance (D-097) | **PROTECTED (mechanical)** |
| 4 | detect missing / not asserted | MX-3 forbids enabling either rail; both pull-downs hold them off in hardware regardless | **SAFE** |
| 5 | `ACC_3V3_SW` shorted to GND | TPS22950C constant-current limits at 0.57–0.96 A → thermal shutdown → `FLT` → auto-retry; `+3V3` reaches **89 % of the 2 A regulator rating**, no foldback | **PROTECTED** |
| 6 | `ACC_5V_SW` shorted to GND | second TPS22950C limits at 0.52–0.86 A; reflected input from `SYS` ≈ 1.33–1.59 A, inside the TPS61023's 3.7 A switch limit; TSD → `FLT` | **PROTECTED** |
| 7 | external 5 V driven **into** `ACC_5V_SW` | TPS22950C **reverse-current blocking is always on** and `V_OUT` abs max is 5.5 V | **PROTECTED** |
| 8 | external voltage driven **into** `ACC_3V3_SW` | same RCB; note the rail also feeds the buffer V_CC and the pull-ups, so an external source **can** power those — bounded by the 5.5 V abs max and by the switch blocking flow back to `+3V3` | **PROTECTED** |
| 9 | signal driven while both rails off | expander pins are high-Z at power-up, 100 Ω in series, TVS clamps at ±5.5 V; the buffer is unpowered and high-Z; `Q10` blocks the WAKE path | **SAFE** |
| 10 | **5 V accidentally applied to a logic contact** | TVS clamps; 100 Ω limits the residual to ≈ 10 mA into the PCAL clamp; the PCAL9535A I/O are **5 V tolerant** (V_I abs max 6.5 V) | **PROTECTED** |
| 11 | `EXT_SDA` held low indefinitely | TCA4307 disconnects after **25–65 ms** and issues up to **16 recovery clocks**; the internal bus is never affected | **PROTECTED** |
| 12 | `EXT_SCL` held low indefinitely | as above | **PROTECTED** |
| 13 | `EXT_SDA` shorted to `EXT_SCL` | the buffer sees both lines low → stuck-bus timeout → disconnect + recovery attempt; internal bus untouched | **PROTECTED** |
| 14 | `WAKE_ATTN_N` held low | with the rail off `Q10` blocks it entirely; with the rail on it asserts a wake, which is the intended function, and **MX-9 keeps the XGPIO masked so the buttons are never starved** | **PROTECTED** |
| 15 | accessory removed while powered | detect de-asserts → **MX-6: both rails down within 100 ms**, 5 V first; the buffer loses V_CC and goes high-Z | **FIRMWARE-DEPENDENT** (hardware bounds it; the 100 ms is a firmware contract) |
| 16 | hot insertion while running | the connector is dual-beam wiping; the TCA4307 precharges to 1 V and will not join the segments until a STOP or idle; rails are still off at that instant because detect has only just asserted | **PROTECTED** |
| 17 | simultaneous 3.3 V + 5 V loading at the published limits | 400 mA + 300 mA; the 5 V rail is boosted from `SYS`, so it consumes **none** of the TPS63020's 2 A budget; `SYS` ≈ 1.75 A at 3.4 V, ≈ 0.6 C on the pack | **SAFE** |
| 18 | battery near the MX-7 cut-off | firmware disables 5 V below V_BAT 3.4 V and 3.3 V below 3.2 V, before the converters misbehave | **FIRMWARE-DEPENDENT** |

**Nothing in the matrix is NOT ACCEPTABLE.** Two rows are firmware-dependent by
design and both are already binding clauses of the D-092 contract; the hardware
bounds the consequence in each case.

---

## 15. Test and no-respin provisions

| signal | provision |
|---|---|
| `ACC_3V3_SW` | **`TP12`** at the connector, plus `TP25` at `U20` — the pair also measures rail drop under load |
| `ACC_5V_SW` | **`TP42`** at the connector, plus `TP29` at `U22` |
| `ACC_DETECT_N` | **`TP43`** on the connector side of `R64` |
| `ACC_POWER_FAULT_N` | `TP27` / `TP33`, already present |
| **TCA4307 `READY`** | **`TP44`** — distinguishes *rail off*, *enabled but never connected* and *connected and healthy* |
| `EXT_SDA` | **`TP45`** | 
| `EXT_SCL` | **`TP46`** |
| `ACC_5V_SW_EN` | **`TP47`** (sheet 01), the new split enable |
| `ACC_3V3_EN`, `ACC_5V_BOOST_EN` | `TP26`, `TP30`, already present |

Ordinary 1.0 mm test pads. **No duplicate connector structures were added.**

---

## 16. Mechanical contract

No CAD was modified. Recorded for **FBV2-P1**:

- **PCB land envelope: 27.94 mm (X, pin field) × 7.87 mm (Y, row-to-row)**, i.e.
  **29.24 × 9.17 mm** to the outside of the 1.30 mm pads. Body envelope
  **30.48 × 8.13 mm**, courtyard **31.48 × 9.13 mm**, height **5.33 mm**.
- 24 × **0.71 mm finished holes** — a through-hole field on a board that is
  otherwise entirely SMD; it constrains routing on every layer beneath it.
- Device side **FEMALE**, in a **right-side recessed bay**, recess **≥ 1.5 mm**,
  **asymmetric upper key/rib**, **closed ends** preventing a one-column offset,
  connector body mechanically supported, **insertion force ≈ 33 N average (peak
  higher) carried by an enclosure boss and never by the 24 solder joints**.
- Wall aperture **≈ 34 × 10 mm** plus the key.
- Z column unchanged at **19.53 mm of the 23.0 mm external budget**.
- **The 80 × 160 × 23 mm enclosure is unchanged.**

---

## 17. Opportunity and simplification scan

| # | checked for | finding |
|---|---|---|
| A | old 20/26-pin remnants | **FOUND AND REMOVED** — the entire 2 × 13 header, `XGPIO10`–`13`, `RESERVED_NC` |
| B | obsolete Harwin references | **none in the design**; the MPN survives only inside `J5`'s note as an explicit warning |
| C | duplicate accessory-power circuitry | **FOUND AND REMOVED** — `U15` TPS22918 was a second, DNP 3.3 V switch feeding a sheet-local `ACC_3V3_SW` that was not the real rail |
| D | unsafe raw `+3V3` exposure | **FOUND AND REMOVED** — inherited `J5` pin 1 was permanent raw `+3V3`, against D-057 |
| E | USB `VBUS` reaching community power | **none** — verified by netlist |
| F | NFC 5 V fallback shared | **none** — `NFC_5V_PA_PENDING` is a separate, still-DNP branch; only `SYS` and the device family are common |
| G | unused FAST_IO / RootProbe architecture | **FOUND AND REMOVED** — `FAST_IO_GPIO43_HDR`, `R67`, and the last `ROOTPROBE` remnant |
| H | BOM consolidation | **TAKEN** — `TPD2E009DBZR` (`D2`, `D7` in the old sheet) is eliminated; **one** TVS MPN now covers all sixteen protected contacts |
| I | no-respin selector / test provisions | **TAKEN** — `TP42`–`TP47`; `READY` observable without consuming a PCAL pin; 11 `U23` spares remain |
| J | protection gaps | **FOUND AND CLOSED** — TVS were all DNP; `ACC_DETECT_N` had no series resistor |
| K | sequencing gaps | **FOUND AND CLOSED** — the single `ACC_5V_EN` is split, per the CTO ruling |

**No new product features were added.**

> ### O-7 — the only NEW item requiring a CTO decision
> **`R49`/`R50` are 1.5 kΩ, sized for a 200 pF external bus. That number is an
> engineering estimate, not a measurement, and it is the one published figure an
> accessory author can violate without knowing.** The options are (a) accept
> 200 pF as the published ceiling for 400 kHz, which is what is implemented and
> documented; or (b) drop to 1.0 kΩ, which covers 300 pF at 400 kHz for 2.9 mA
> of static sink instead of 1.9 mA. **It is one 0603 resistor either way and the
> footprint is fitted**, so this closes on the first measured board rather than
> now. Raised because it is the last un-measured number on the sheet.

---

## 18. Verification

| check | result |
|---|---|
| **ERC** (`--units mm`, errors + warnings, **not** `--severity-all`) | **27 messages, 0 ERRORS, 27 warnings** |
| ERC before this task | 42 / 1 / 41 |
| **delta** | **−15 messages, −1 error, −14 warnings** |
| new errors | **0 — and the design now has zero errors of any kind** |
| what was removed | the inherited `RESERVED_NC` `label_dangling` **error**, and all **14** `isolated_pin_label` warnings — `XGPIO10`–`13`, `FAST_IO_U0TXD_ROOTPROBE_CS`, `NATIVE_A` and `NATIVE_B`, each on both the root and the child sheet |
| what remains | 21 `pin_to_pin` symbol-pin-type artefacts (18 × `J1` unused display bus tied to GND as the panel datasheet requires, 2 × BMI270 `ASDx`/`ASCx` tied to VDDIO as Bosch requires, 1 × MAX98357A thermal pad) and 6 `unconnected_wire_endpoint` on parked RF stubs. **All pre-existing and all previously explained.** |
| **sheets 08 and 09 individually** | **completely clean — zero violations** |
| components | **321**, 0 duplicate references, **0 without a footprint** |
| nets | 224, **0 `*_TBD`** |
| `fork_equivalence.py` | **PASS** — `SHEETS` is now **empty**; all nine sheets are `changed` |
| `netclass_probe.py` | **PASS** — 176 board nets, 6 resolve to `LED_BOOST` |
| PCB | **bit-identical to Beta-DM**, proven by the fork probe |
| obsolete 20-pin / 26-pin connector | **none** |
| Harwin `M20-7881242` | **not present as a part** |
| raw permanent `+3V3` on the port | **none** |
| duplicate GPIO nets | **none** |
| accidental `VBUS` connection | **none** |
| accidental NFC / accessory 5 V connection | **none** |
| both load switches default OFF | **verified** — `R98`, `R102`, `R131` |
| TCA4307 default isolated | **verified** — `EN` = `ACC_PWR_EN`, `R17` 100 kΩ pull-down |
| `U23` P04 = `ACC_5V_SW_EN` | **verified** — `U23.8` → `U22.1` + `R131` + `TP47` |

**One correction worth recording.** Rebuilding the sheet deleted `#FLG0105`, a
`PWR_FLAG` that had been sitting on the Beta-DM community sheet and was **the
only power-output driver on the entire GND net**. Its loss turned every GND
`power_in` pin in the design undriven and produced a `power_pin_not_driven`
error. It has been **deliberately re-created on sheet 09 with the same
reference**, with a note explaining why it exists. This is not a fake power flag
added to silence a check — it is the restoration of the check's only legitimate
satisfier, which the rebuild had removed by accident.

---

## 19. Open items carried forward

| # | item |
|---|---|
| **O-7** | external I²C pull-up value against measured bus capacitance (§17) |
| **B-68** | **new** — confirm the Würth `74438357010` I_sat ≥ 3 A at BOM lock |
| **B-69** | **new** — measure the TPS61023 start-up time; the 5 ms sequencing delay is 7× a *typical* with no published maximum |
| **B-35** | `FLT` does not assert on a plain current-limit event |
| **B-36** | accessory wake in sleep requires `ACC_3V3_SW` to stay on |
| **B-46** | `SD_CARD_DETECT_N` polarity assumed |
| **B-47** | `J1` FH52E second source / land pattern |
| — | published accessory limits are 400 mA and 300 mA on the first five boards |
| — | the connector may need manual assembly on the first five boards |

**FBV2-S2 and PCB work were not started.**
