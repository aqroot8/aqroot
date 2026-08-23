# FBV2-S1-007 — Full Beta v2 infrared subsystem (Sheet 07)

**Task gate `FBV2-S1-IR` = PASS.**
Date: 2026-08-23 · Scope: `07_ir.kicad_sch`, project-local symbol library.
Sheets `08`–`09`, the PCB, mechanical CAD, firmware, Beta-DM and frozen Beta are untouched.

**ERC 45 → 45. Zero added, zero removed. Errors unchanged at 2, both inherited.**
311 components, 0 duplicate references, 0 without a footprint, 0 `*_TBD` nets.
`fork_equivalence.py` PASS, `netclass_probe.py` PASS, PCB still bit-identical to Beta-DM.

---

## 1. The whole IR subsystem arrived DNP — for the fourth sheet running

`U6`, `D1`, `Q1`, `R21`, `R22`, `R23`, `R24` and `C11` all came from Beta-DM marked **`DNP`**.
Only `C12`, the local bulk capacitor, was fitted — decoupling for a transmitter that was not
there, exactly the pattern found on sheet 06 with `C9`/`C10` and the MAX98357A.

The brief opens with *"Full Beta v2 IR is a mandatory internal feature."* **All eight are now
fitted.** `R123` is the only DNP part on the sheet and it is deliberately so.

**This is the fourth consecutive migrated sheet where an inherited `DNP` was load-bearing**
(sheet 09's `U16`/`R49`/`R50`/`U15`/`D2`/`D3` at FBV2-S1-005, sheet 06's `U5`/`J6` at
FBV2-S1-006, now all of sheet 07). The pattern is now established well enough to state as a
rule: **a `DNP` flag on a Beta-DM sheet describes what was populated on that reduced build, not
what the architecture requires.** Sheets 08 and 09 should be assumed to carry the same trap.

---

## 2. Transmitter — TSAL6100 locked, and the rating that actually binds

Source: **Vishay document 81009, TSAL6100, Rev 1.8**; and **81010, TSAL6200, Rev 2.4**.

| | **TSAL6100 (locked)** | TSAL6200 (fallback) |
|---|---|---|
| wavelength | 940 nm GaAlAs MQW | 940 nm GaAlAs MQW |
| package | T-1¾, Ø5 mm leaded | **identical** |
| **radiant intensity `Ie`** | **170 mW/sr** typ (80 min) at 100 mA | 72 mW/sr typ (40 min) |
| **half-intensity angle** | **±10°** | **±17°** |
| radiant power `Φe` | 40 mW | 40 mW |
| `VF` at 100 mA | 1.35 typ / 1.6 max | **identical** |
| `IF` continuous | 100 mA | 100 mA |
| **`IFM` repetitive peak** | **200 mA** (tp/T = 0.5, tp = 100 µs) | **200 mA** |
| `IFSM` surge | 1.5 A (t ≤ 5 µs, **single pulse**) | 1.5 A |
| `PV` / `RthJA` / `Tj` | 160 mW / 230 K/W / 100 °C | identical |
| `tr`/`tf` | 15 ns | 15 ns |

### The IFM / IFSM trap the brief warned about

**`IFSM` = 1.5 A is a single-pulse surge for t ≤ 5 µs. It is not a remote-control rating and
cannot be used to justify carrier current.** The rating that governs a 38 kHz burst train is
**`IFM` = 200 mA**, specified at **tp/T = 0.5 with tp = 100 µs** — a *longer* pulse at the same
duty than a 38 kHz carrier produces, so a 26.3 µs period at ≤50 % duty is less stressful than
the specified condition, not more.

### Choosing the peak current

Duty model for a standard NEC frame: ~67.5 ms long, carrier active ~22 ms of it, carrier duty
one third → the LED is on for **≈ 11 %** of a frame.

| candidate | % of `IFM` | `Ie` | avg LED power over a frame | ΔTj | verdict |
|---|---|---|---|---|---|
| 100 mA | 50 % | 170 mW/sr | 15 mW | 3.4 K | safe, but leaves range on the table |
| **150 mA** | **75 %** | **≈ 255 mW/sr** | **25 mW** | **5.7 K** | **SELECTED** |
| 200 mA | 100 % | ≈ 340 mW/sr | 35 mW | 8.1 K | **at the limit — no tolerance margin left** |
| 300 mA | **150 %** | — | — | — | **REJECTED — exceeds the repetitive rating** |

**Thermally none of these is difficult** — 25 mW against a 160 mW `PV` limit, ΔTj under 6 K on
a 230 K/W part. **The binding constraint is `IFM`, and it is a hard one.** 200 mA leaves nothing
for rail, `VF` and resistor tolerance, which alone would push the worst case past the rating;
300 mA is simply out of spec for repetitive use however good the thermal picture looks.

**Range is not the constraint.** The TSOP384xx datasheet quotes **45 m transmission distance
using a TSAL6200 at only `IF` = 50 mA**. The TSAL6100 at 150 mA is roughly 20× that intensity.
Consumer IR needs metres, not tens of metres, so the sensible thing to buy with current is
**margin off-axis and through dirty windows**, not headline range — which is exactly why 75 %
of `IFM` rather than 100 % is the right answer.

### The real weakness of the TSAL6100 is the beam, not the power

**±10° is narrow for a handheld pointing device.** The TSAL6200's ±17° is far more forgiving,
at 2.4× lower on-axis intensity — note that `Ie × φ²` is roughly constant between the two
(170 × 10² ≈ 17 000 vs 72 × 17² ≈ 20 800), so the parts emit similar total power, redistributed.

The brief already anticipates this and authorises the swap. **The fallback is a true drop-in and
this audit confirms why:** identical package and footprint, identical `VF` (1.35 / 1.6 V at
100 mA), identical `IFM` — so **`R24` does not change**, and the only differences are optical.
Carried as **B-66** for first-article ergonomics.

---

## 3. Supply — `+3V3`, reversing the previous direction

The prior architecture direction preferred `BQ25185_SYS` *"so 38-kHz LED current does not pulse
the MCU/radio +3V3 rail."* The brief asked whether that is still correct at the selected current.
**It is not, and the arithmetic is one-sided.**

| | **`+3V3` (selected)** | `SYS` |
|---|---|---|
| rail range | 3.234–3.366 V (regulated ±2 %) | ≈ 3.2–5.0 V (battery + USB) |
| resistor for 150 mA | **12 Ω** | 22 Ω (sized so the top stays inside `IFM`) |
| **peak current across all tolerances** | **118–170 mA (1.44 : 1)** | **64–166 mA (2.6 : 1)** |
| behaviour as the battery drains | **none — regulated** | **IR range visibly shortens** |
| resistor dissipation, instantaneous | 0.27 W | 0.53 W |
| 38 kHz on the shared rail | **≈ 40 mV pk-pk with `C12` = 22 µF** | none |
| cross-sheet dependency | **none** | needs `BQ25185_SYS` published from sheet 01 |

**The noise objection is real but bounded, and the one device that genuinely cares is already
protected by 41 dB.** The IR receiver is the only part in the system whose sensitivity is
specified against supply ripple *at the carrier frequency*, and `R21`/`C11` put it 41 dB below
the rail — see §6. Everything else on `+3V3` already lives with far larger pulsed loads: the
audio amplifier draws **230 mA peaks** switching at 330 kHz, NFC draws 60 mA, the backlight
boost more. A 150 mA peak / 50 mA average IR load at 38 kHz is smaller than what is already
there.

Against that, `SYS` would make **IR range a function of battery charge** — a user-visible
behaviour — and put the worst-case current within reach of `IFM`.

> **Scope note, stated as fact rather than as the reason:** `BQ25185_SYS` is a **sheet-01-local
> net**, not published hierarchically, so routing it to sheet 07 needs a sheet-01 edit that this
> task is not authorised to make. **If `SYS` had won the analysis this would have been reported
> as blocked rather than quietly avoided.** It did not. `ARCHITECTURE.md` lists an
> *"IR LED source-select link (`+3V3` vs `SYS`)"* among its HIGH no-respin provisions; building
> that link is carried as **B-65**, and it is one hierarchical label on sheet 01 plus a DNP
> resistor here.

---

## 4. Current-limit network

```
I = (V_rail - VF - I x RDS(on)) / R
VF(TSAL6100, 150 mA) ~ 1.50 V   interpolated between 1.35 V at 100 mA and 2.2 V at 1 A
AO3400A adds ~5 mV at RDS(on) < 48 mOhm with a 3.3 V gate
R = (3.3 - 1.50 - 0.005) / 0.150 = 11.97 ohm  ->  R24 = 12 R, 1 %, 0805
```

| case | rail | `VF` | `R` | current |
|---|---|---|---|---|
| nominal | 3.30 | 1.50 | 12.00 | **150 mA** |
| worst high | 3.366 | 1.35 | 11.88 | **170 mA** — 85 % of `IFM` |
| worst low | 3.234 | 1.80 | 12.12 | **118 mA** |

`R24` dissipation: 0.27 W instantaneous, ≈ 90 mW during a burst, **≈ 30 mW averaged over a
frame** against a 125 mW 0805 rating.

### `R123` — the no-respin trim, with a hard floor

`R123` is a **DNP 0805 in parallel with `R24`**, so the current can be raised at first article
without desoldering the fitted part:

| fitted | total | peak current |
|---|---|---|
| `R24` alone | 12.0 Ω | 150 mA |
| + 220 Ω | 11.4 Ω | 158 mA |
| + 100 Ω | 10.7 Ω | 168 mA |
| + 68 Ω | 10.2 Ω | 176 mA |
| + 47 Ω | 9.56 Ω | 188 mA |

> **Never below 10 Ω total.** Every value in the table stays inside `IFM` = 200 mA; below 10 Ω
> it does not. This is the first thing to reach for if the **TSAL6200 fallback** is fitted, since
> its `Ie` is 72 mW/sr against 170.

Trimming *down* needs no provision — `R24` itself is an accessible 0805 and can simply be
swapped.

---

## 5. Local reservoir `C12` — 4.7 µF was three times too small

The carrier draws 150 mA at ~⅓ duty, so per carrier period the capacitor must supply

```
Q = I x D x (1 - D) x T = 0.15 x 0.333 x 0.667 x 26.3 us = 0.88 uC
ripple = 0.88 uC / C
```

| `C` | 38 kHz ripple | % of rail |
|---|---|---|
| **4.7 µF (inherited)** | **218 mV** | 6.6 % — too much |
| 10 µF | 88 mV | 2.7 % |
| **22 µF (selected)** | **40 mV** | **1.2 %** |
| 47 µF | 19 mV | 0.6 % |

Design target: keep the carrier below ~1.5 % of the rail. **`C12` = 22 µF, X7R, 16 V, 1210** —
the package and voltage are specified deliberately, because the requirement is **≥ 15 µF
*effective* at 3.3 V DC bias** and a 6.3 V 0805 part would derate to roughly half its marked
value. 47 µF halves the ripple again for more area and cost with no identified victim.

The **burst envelope** — a 50 mA average load stepping on and off on a millisecond timescale —
is not this capacitor's job and does not need to be: it is a 50 mA step on a 2 A buck-boost.

---

## 6. Receiver — TSOP38438, and why the existing filter is exactly right

Source: **Vishay document 82491, TSOP382.., TSOP384.., Rev 2.1, 27-May-2025** (current).

`TSOP38238` → `TSOP38438` is a **pure MPN change**: the parts table shows both series sharing
**the same Minicast package, the same pinning 1 = OUT / 2 = GND / 3 = VS and the same 5.0 × 6.95
× 4.8 mm body**, so the footprint is untouched.

| parameter | value |
|---|---|
| supply | **2.0 – 5.5 V** |
| supply current | 0.25 / **0.35** / 0.45 mA at 3.3 V |
| output | **active low**, `VOSL` 30 mV typ at 0.5 mA |
| **output pull-up** | **internal 30 kΩ** (block diagram) — no external part needed |
| directivity | **±45°** |
| absolute max | `VS` 6 V, `IS` 3 mA, `IO` 5 mA, `Tj` 100 °C, `Ptot` 10 mW |
| min irradiance | 0.12 mW/m² typ (NEC), 0.08 (RC5) |
| ambient tolerance | threshold rises 0.1 → ~1 mW/m² at 10 W/m² (1.4 klx incandescent / 8.2 klx daylight) |

**The output drives GPIO44 directly.** The internal pull-up is why the inherited design has no
external one, and that is correct.

### The supply filter is the load-bearing part of this sheet

The datasheet's application circuit shows exactly the inherited topology — a series `R1` into
`VS` and a shunt `C1` — with the note *"R1 and C1 recommended in case there are strong ripple or
spikes on the supply line."* **Vishay prints the topology but no values**, so the values are
ours and have to be justified. They are:

```
R21 = 100 R, C11 = 4.7 uF  ->  fc = 1 / (2 pi x 100 x 4.7u) = 339 Hz
attenuation at 38 kHz      =  38000 / 339 = 112x = 41 dB
DC drop                    =  0.45 mA x 100 R = 45 mV, so VS ~ 3.25 V
```

**Why 41 dB matters more than it looks:** datasheet **Fig. 7** plots threshold irradiance
against supply ripple *at the carrier frequency*, and that curve is far steeper than the 100 Hz
and 10 kHz ones. The receiver starts degrading at roughly **10 mV RMS** and has **doubled its
threshold by about 50 mV**. Our own transmitter runs at exactly that frequency.

```
rail ripple with C12 = 22 uF : ~40 mV pk-pk  ~=  12 mV RMS
through R21/C11 (41 dB)      :  ~0.1 mV RMS at the receiver VS
margin to the 10 mV knee     :  ~90x
```

> **This is what makes the `+3V3` transmitter decision safe.** Keep `R21`/`C11` as they are; do
> not shrink `C11` for area without redoing this calculation.

---

## 7. Driver — AO3400A retained, and one open item closed

Source: **AOS document AO3400A, Rev 3.1, July 2023** (current).

**The pinout verification note on `Q1` is CLOSED.** The datasheet's SOT-23 top and bottom views
show the lone pin as **Drain** and the paired pins as **Gate** then **Source** — i.e.
**1 = G, 2 = S, 3 = D**, exactly what `Transistor_FET:Q_NMOS_GSD` maps and what the inherited
wiring already used.

| parameter | value | at 150 mA |
|---|---|---|
| `VGS(th)` | 0.65 / 1.05 / **1.45 V** | fully enhanced by a 3.3 V gate |
| `RDS(on)` | < 48 mΩ at `VGS` = 2.5 V | **≈ 5 mV** drop — negligible vs `VF` |
| `ID` / `IDM` | 5.7 A / 30 A | **≈ 38× over-specified** |
| conduction loss | — | 0.15² × 0.036 = **0.8 mW** |
| `VDS` | 30 V | 3.3 V applied |

**Switching at 38 kHz is a non-event.** With `R22` = 100 Ω and a few hundred pF of `Ciss` the
edge is well under 100 ns — about **0.3 %** of the 26.3 µs carrier period — so `R22` buys
gate-loop damping and slower edges (less radiated EMI from the LED loop) at no performance cost.

**The safe-OFF state is proven, not assumed.** `R23` = 100 kΩ to GND with `IGSS` ≤ 100 nA gives
at most **10 mV** on the gate, against a **650 mV** minimum threshold. **No IR emission during
boot, reset, GPIO high-impedance or a firmware crash** — a 65× margin, not a judgement call.

**Footprint:** AOS publishes **no recommended land pattern** in the AO3400A datasheet, so the
industry-standard IPC SOT-23 pattern applies and KiCad's `Package_TO_SOT_SMD:SOT-23` is
IPC-7351-derived. The old *"Footprint BLOCKED: needs the official AOS recommended land pattern"*
note asked for a document that does not exist; it becomes an ordinary **FBV2-S2** footprint-audit
item.

The part is kept rather than downsized because **it is already in the design on sheet 01** — the
same jellybean, one fewer line on the BOM.

---

## 8. Protocol coverage — and a conflict inside the brief

`f0` = 38 kHz with a **3 dB bandwidth of `f0`/10, i.e. `f0` ± 5 % → 36.1–39.9 kHz** (Fig. 5).

| protocol | carrier | relative responsivity | range cost |
|---|---|---|---|
| **NEC, Samsung, Sharp, Mitsubishi** | 38 kHz | **1.00** | none |
| RC5 / RC6 | 36 kHz | ≈ 0.75 | ≈ 13 % |
| Sony SIRC | 40 kHz | ≈ 0.72 | ≈ 15 % |

A 13–15 % range cost on the off-centre carriers is the ordinary compromise for a single-receiver
universal remote and is fine.

### The conflict

The brief §1 locks **`TSOP38438`**. The brief §9 lists **Sony/SIRC** among the protocols the
hardware should support. **Vishay's own suitable-data-format table says those two cannot both be
true**, verbatim from doc 82491 Rev 2.1:

| | TSOP382.. (**AGC2**) | TSOP384.. (**AGC4**) |
|---|---|---|
| NEC code | Yes | **Preferred** |
| RC5/RC6 code | Yes | **Preferred** |
| Thomson RCA 56 kHz | Yes | **Preferred** |
| Sharp code | Yes | **Preferred** |
| **Sony code** | **Yes** | **No** |
| Mitsubishi code | Yes | **Preferred** |
| fluorescent-lamp suppression | Fig. 14 | **Fig. 14 and Fig. 15** |

The mechanism is in Fig. 8: above 35 cycles/burst AGC4 collapses to ~7 % maximum envelope duty
cycle where AGC2 holds ~20 % to 70 cycles, and it demands a gap of **> 15 × burst length**
against AGC2's **> 5 ×**. SIRC's long header and high envelope duty violate that.

**The lock is not wrong — it is a trade, and a defensible one.** AGC4 buys *"Preferred"* status
on five of six protocols and adds suppression of **high-modulation fluorescent interference
(Fig. 15)** that AGC2 does not have. Vishay's own framing: *"the higher the AGC, the better noise
is suppressed, but the lower the code compatibility."*

**Two things make this much smaller than it first looks:**

1. **It is receive-only.** **Transmitting Sony/SIRC is completely unaffected** — the transmitter
   is a carrier and a timing pattern generated by the MCU, and the LED does not care. Only
   *learning* a Sony code from an original remote is at risk.
2. **Reverting is a `lib_id` change and nothing else.** Same package, same pinout, same
   footprint, same filter. **The `TSOP38238` symbol has been deliberately retained in the project
   library** so the swap costs one line.

> **This is the single item surfaced for CTO decision — see §10.**

---

## 9. Power budget and mutual exclusion

| condition | `+3V3` draw |
|---|---|
| LED carrier peak | **150 mA nominal, 170 mA worst case** |
| average during a burst (⅓ carrier duty) | 50 mA |
| **average over an NEC command** (~11 % LED-on) | **≈ 17 mA** |
| receiver, continuous | 0.35 mA |

Compare what the rail already carries: **audio 230 mA peaks**, NFC field ~60 mA, backlight boost
~100 mA. **IR is the smallest pulsed load on the rail.**

> **No new mutual-exclusion rule is proposed.** MX-1 already covers concurrent high-power radio
> operation, and IR does not need to join it: 17 mA average and a 170 mA peak on a 2 A rail does
> not conflict with LoRa TX, 433 MHz TX, the NFC field or maximum speaker output. The brief says
> not to create rules the power budget does not need, and it does not need one.

Thermally: 30 mW in `R24`, 0.8 mW in `Q1`, 25 mW in the LED. Nothing to manage.

---

## 10. Opportunity and simplification scan

| | finding |
|---|---|
| **A. nearly-free capability** | **Sony/SIRC transmission works regardless of the receiver's AGC limitation** — worth documenting so nobody concludes Sony is unsupported outright. `TP39`/`TP40` make the whole subsystem measurable without breaking the loop. |
| **B. legacy components** | **none.** Every part on the sheet earns its place; the gate network and receiver filter both survived audit unchanged. |
| **C. BOM simplification** | `Q1` AO3400A is **already used on sheet 01** — no new line. `R22`/`R23` are 0603 jellybeans. The **TSOP38238 symbol is retained** in the library at zero cost as the documented AGC2 alternative. |
| **D. same-footprint fallback** | **TSAL6200 confirmed a true drop-in** — identical package, `VF` and `IFM`, so `R24` is unchanged (§2). |
| **E. test / rework provisions** | `TP39` (LED current via `R24`), `TP40` (receiver output), `R123` DNP trim, `R24` swappable. |
| **F. sourcing / lifecycle** | TSOP382/384 datasheet is **Rev 2.1 dated 27-May-2025** — current. Worth noting that adjacent Vishay families **TSOP312/314 and TSOP311/313/315 are marked "End of Life August-2024"**; the 382/384 family is **not**. TSAL6100/6200 docs are from 2014 but the parts are current. AO3400A Rev 3.1, July 2023. |

> ### O-5 — NEW, REQUIRES A CTO DECISION
>
> **`TSOP38438` (AGC4) is marked "No" for Sony code by Vishay; `TSOP38238` (AGC2) is marked
> "Yes" and supports every protocol the brief lists.** The §1 lock and the §9 protocol list
> cannot both be satisfied by one receiver.
>
> - **Keep AGC4 (`TSOP38438`)** — better noise immunity, including high-modulation fluorescent
>   interference AGC2 cannot suppress, and *"Preferred"* on NEC, RC5/RC6, Sharp, Mitsubishi and
>   Thomson RCA. **Cost: Sony codes may not be learnable.**
> - **Revert to AGC2 (`TSOP38238`)** — every listed protocol supported including Sony. **Cost:
>   worse noise suppression under fluorescent/LED lighting**, which for a handheld used indoors
>   is not a small thing either.
>
> **Effort is trivial in both directions**: same package, same pinout, same footprint, same
> supply filter, and both symbols are already in the project library. **Nothing else on this
> sheet depends on the choice.** Implemented as locked (`TSOP38438`) pending the ruling.

---

## 11. Self-blinding and mechanical

Handled **mechanically, not electrically**, as the brief directs. The electrical half of the
problem — the transmitter modulating the receiver's supply at exactly its own carrier frequency
— is already solved by `R21`/`C11` at 41 dB (§6).

| requirement | value |
|---|---|
| emitter | **TSAL6100**, T-1¾ Ø5 mm leaded, **±10° half-angle** (was ±17°) |
| receiver | **TSOP38438**, Minicast, ±45° acceptance, 6.0 × 5.6 × 4.7 mm |
| separation | **≥ 15 mm**, both on the top edge |
| barrier | **opaque optical barrier between them**, and the receiver outside the LED emission cone |
| layout | keep the TX current loop away from the receiver supply and return |

**The narrower beam does not relax the barrier requirement — it tightens it.** The TSAL6100 is
**2.4× brighter on axis** than the TSAL6200 the separation figure was written for, so the stray
and internally-reflected energy reaching the receiver goes up even though the direct cone is
narrower. Firmware may additionally ignore RX during local TX; no firmware is implemented here.

---

## 12. Blockers

| id | state |
|---|---|
| **B-65** (new) | **The `+3V3` / `SYS` IR source-select link listed in `ARCHITECTURE.md` cannot be built without a sheet-01 edit.** `BQ25185_SYS` is a sheet-01-local net, not published hierarchically. Building the link is one hierarchical label on sheet 01 plus a DNP resistor here. **OPEN, low** — `+3V3` is the analysed-correct choice (§3), so this is a provision, not a fix. |
| **B-66** (new) | **TSAL6100 ±10° beam ergonomics unvalidated.** The narrow cone is the one real risk in the emitter choice. **OPEN, medium.** First article: if aiming is fussy, fit the TSAL6200 — drop-in, no other change, and `R123` is there to trim the current back up. |
| **B-29 / B-03** | unchanged — footprint audit at FBV2-S2. `Q1`'s SOT-23 land pattern joins that list as an ordinary item now that the "needs the official AOS pattern" blocker is resolved: **AOS publishes none.** |
| **P-18, B-37, B-61…B-64** | unchanged. |

---

## 13. What was NOT done

No second IR LED, no external IR accessory requirement, no multiple emitter angles, no extra
optical channels, no second receiver, no exotic carrier frequency, no dedicated LED-driver IC,
no RF-style test connectors, no analog optical detector, no new GPIO, no firmware.

`IR_TX_GPIO16` and `IR_RX_GPIO44` are unchanged, so the GPIO ledger gains no pins — only the
notes that the transmitter is now a real 150 mA load and the receiver output is active-low with
an internal pull-up.

Sheets `08`–`09` untouched. The PCB is untouched and still bit-identical to Beta-DM.
`hardware/beta-dm/`, `hardware/beta/` and `hardware/beta/mechanical/` are unchanged.
