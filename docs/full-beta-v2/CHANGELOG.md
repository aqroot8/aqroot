# AQROOT Full Beta v2 — Changelog

Chronological engineering changes and why they happened. Newest entries at the
top. Each entry records what changed, not merely that something happened.

This file records **decisions and design changes**. Routine document edits are
not entries. A change that alters what gets built, or what may not be built, is
an entry.

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
