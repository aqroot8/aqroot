# AQROOT Full Beta v2 — FBV2-P1 floorplan inputs

**Status: NORMATIVE HANDOFF.** Created 2026-08-23 at **FBV2-MECH-002**.
Authority: [`MECHANICAL_INTERFACE_SPEC.md`](MECHANICAL_INTERFACE_SPEC.md) and
[`../CTO_DECISIONS.md`](../CTO_DECISIONS.md).

> **This file contains ONLY current physical constraints.** It carries no rationale, no history
> and no superseded value. Where the interface spec still shows a struck or superseded figure,
> **the value here is the current one**. If the two ever disagree, the interface spec is the
> authority and this file is the defect.
>
> **NO COORDINATES ARE INVENTED HERE.** No CAD exists, no PCB outline has been drawn, and nothing
> in this file assigns an X/Y position to any part. It states envelopes, clearances, keepouts and
> relationships — the inputs a floorplan consumes, not the floorplan itself.

**Status key**

| marking | meaning |
|---|---|
| **LOCKED** | CTO ruling or measured from a manufacturer drawing / repository artefact. Do not change at P1. |
| **TARGET** | Derived from a locked input plus stated assumptions. Binding until CAD refutes it. |
| **CAD-TO-VERIFY** | Believed correct, **not** measured. Must be confirmed in CAD before it is relied on. |

---

## 1. Enclosure

| # | constraint | value | status |
|---|---|---|---|
| E-1 | External envelope | **80 × 160 × 23 mm** (X × Y × Z, portrait) | **LOCKED** |
| E-2 | Device orientation | **portrait**, 80 wide × 160 tall | **LOCKED** |
| E-3 | Wall thickness, all faces | **2.0 mm** nominal | **TARGET** |
| E-4 | Internal cavity envelope | **75.0 × 155.0 × 18.5 mm** nominal | **TARGET** |
| E-5 | Shell lip / tongue-and-groove at the seam | **1.0–1.5 mm inward, full perimeter** — reduces E-4 locally | **TARGET** |
| E-6 | Stiffening ribs on the 160 mm spans | **1.5 mm × 3 mm tall**, as needed | **TARGET** |
| E-7 | Governing Z column (control region) | **19.5 mm of 23.0 — 3.5 mm spare** | **TARGET** |
| E-8 | Connector-region Z column | **19.53 mm of 23.0 — 3.47 mm spare** | **TARGET**, body height **CAD-TO-VERIFY** (M-09) |
| E-9 | Speaker-region Z column | **12.6 mm of 23.0 — 10.4 mm spare** | **TARGET** |

---

## 2. PCB

| # | constraint | value | status |
|---|---|---|---|
| P-1 | **PCB maximum outline** | **72.0 × 152.0 mm** | **TARGET** |
| P-2 | **PCB target outline** | **70.0 × 148.0 mm** — the recommended outline | **TARGET** |
| P-3 | PCB thickness | **1.6 mm** | **LOCKED** |
| P-4 | Board edge → cavity wall | **≥ 1.5 mm** | **TARGET** |
| P-5 | Component → shell | **≥ 0.5 mm** | **TARGET** |
| P-6 | Connector → wall | **≥ 0.3 mm** | **TARGET** |
| P-7 | Height under the display (display shadow) | **≤ 0.8 mm** | **LOCKED** (measured, Beta-DM) |
| P-8 | Height under the battery (battery shadow) | **≤ 1.2 mm** | **LOCKED** (measured, Beta-DM) |
| P-9 | Beta-DM 74 × 155 outline | **DOES NOT FIT — re-floorplan required**, not merely reduce | **LOCKED** |

---

## 3. Front face

| # | constraint | value | status |
|---|---|---|---|
| F-1 | Display module envelope | **`ER-TFT035IPS-6` + `ER-TPC035-6`, 56.54 × 84.96 × 3.95 ± 0.25 mm (4.20 max)** | **LOCKED** |
| F-2 | Display active area | **48.96 × 73.44 mm**, 320 × 480, dot pitch 0.153 mm | **LOCKED** |
| F-3 | Display FPC | **one 50-pin, 0.50 mm pitch, BOTTOM-CONTACT tail**, 0.30 ± 0.03 mm thick, **25.5 ± 0.15 mm wide**, **30 ± 0.5 mm free length**; carries display **and** touch (touch on pins 44–47) | **LOCKED** |
| F-4 | **FPC exit direction** | tail exits the **BOTTOM edge of the panel** and folds back under it to `J1` | **LOCKED** |
| F-5 | **FPC bend corridor** | **6 mm retained**; **≥ 3 mm** is the minimum for a 0.30 mm tail | **TARGET** |
| F-6 | **FPC reach** | `J1` must sit within the **30 ± 0.5 mm free tail length** of the panel's FPC exit, after the bend allowance | **LOCKED (part)**, routing **CAD-TO-VERIFY** |
| F-7 | `J1` connector body | Hirose **`FH69-50S-0.5SH`**, right-angle backflip ZIF, **2.3 mm high** | **LOCKED** |
| F-8 | **`J1` cannot sit under the panel** | 2.3 mm against a 0.8 mm display-shadow limit — it must live in the **70.04 mm of cavity below the display**, contested with the D-pad, A/B and the mic aperture (**M-08 / B-33**) | **LOCKED** |
| F-9 | `J1` actuator clearance | backflip ZIF lid needs **vertical swing clearance above the connector**; no component or shell rib may block the lid arc | **CAD-TO-VERIFY** |
| F-10 | `J1` land pattern | **DEDICATED FH69 pattern. No second source. `FH52E-50S-0.5SH` is NOT a drop-in** | **LOCKED** |
| F-11 | D-pad | **4 × `PTS645SM43SMTR92LFS`**, 6.0 × 6.0 × **4.3 mm** each, ~0.25–0.30 mm travel. **Front lower-left** | **LOCKED (part)**, arrangement **TARGET** |
| F-12 | A / B buttons | **2 × `PTS645SM43SMTR92LFS`**, same body. **Front lower-right** | **LOCKED (part)** |
| F-13 | Keypad / plunger stack | **~1.0 mm above the actuator**, included in the governing Z column | **TARGET** |
| F-14 | **RGB status light** | `D13` **`MHPA3528RGBCT`**, PLCC-4 **3.50 × 2.80 × 1.85 mm**, 120° emission, water-clear, **front-facing**. Needs a **diffuser or short light pipe** — no protruding bare LED, no direct line of sight to the die. Output ~80 / 87 / 42 mcd (R/G/B), so the optical path must be **short and low-loss** | **LOCKED (part)**, **position deliberately NOT locked (M-11)** |
| F-15 | **Microphone aperture** | **front face, bottom third, opposite corner from the speaker**; shell aperture **Ø0.8–1.0 mm**, or 3–5 × Ø0.5 mm, acoustic mesh behind | **LOCKED** |
| F-16 | **PCB acoustic hole** | **Ø1.05 mm NPTH**, concentric with `MK1` pad 4 | **LOCKED** (D-203) |
| F-17 | Acoustic keepout | **no copper, mask or component inside Ø1.65 mm** (pad-4 GND ring); **Ø2.5 mm component keepout on the microphone side**; region clear of pours, traces, vias, silk and mask steps **on both faces** | **LOCKED** (M-14) |
| F-18 | Acoustic gasket | closed-cell silicone or poron, **compressed 20–30 %**, **ID ≥ 1.5 mm, OD 4–5 mm**, sealed tunnel | **TARGET** |
| F-19 | Acoustic tunnel length | **≤ 2.5 mm** | **TARGET** |
| F-20 | `MK1` body | PUI **`DMM-4026-B-I2S-R`**, **4.00 × 3.00 × 1.00 mm**, **BOTTOM PORT**, port Ø0.25 ± 0.05 mm on the width centreline 1.00 mm from the short edge | **LOCKED** |
| F-21 | **`MK1` board face** | must be the PCB copper face **pointing AWAY from the front shell**, listening forward through F-16 | **OPEN — see §9 O-1** |

---

## 4. Bottom edge

| # | constraint | value | status |
|---|---|---|---|
| B-1 | USB-C receptacle | GCT **`USB4105-GF-A-120`**, ~**9.2 × 7.35 × 3.26 mm**, top-mount horizontal | **LOCKED (part)**, dims **CAD-TO-VERIFY** |
| B-2 | USB-C position | bottom edge, **centred ± 5 mm** | **TARGET** |
| B-3 | USB-C aperture | must clear the **receptacle mouth**, not just the body | **TARGET** |
| B-4 | microSD socket | Molex **`5025700893`**, ~**14.0 × 14.5 × 1.85 mm**, push-pull | **LOCKED (part)**, dims **CAD-TO-VERIFY** |
| B-5 | microSD position | bottom edge, **left of USB-C** | **TARGET** |
| B-6 | **microSD ↔ USB-C separation** | **UNDER REVIEW — see §9 O-4.** The recorded "≥ 8 mm centre-to-centre" is **smaller than the two bodies allow** | **OPEN** |
| B-7 | **Card insertion path** | the card **protrudes during insertion** — reserve **+18 mm of travel OUTSIDE the shell**, clear of the USB-C aperture and any grip feature | **TARGET** |

---

## 5. Right wall

| # | constraint | value | status |
|---|---|---|---|
| R-1 | Community connector | Samtec **`BCS-112-S-D-HE`**, 2 × 12, **24 active contacts**, 2.54 mm, FEMALE, **horizontal entry** | **LOCKED** |
| R-2 | Body envelope | **30.48 (L) × 8.13 (D) × 5.33 (H) mm** | **LOCKED**, height **CAD-TO-VERIFY** (M-09) |
| R-3 | PCB pin field | **27.94 (X) × 7.87 (Y) mm**, **24 × Ø0.71 mm PTH**; 2.54 mm within a row, **7.87 ± 0.05 mm row-to-row** | **LOCKED** |
| R-4 | To the outside of the 1.30 mm pads | **29.24 × 9.17 mm** | **LOCKED** |
| R-5 | Courtyard | **31.48 × 9.13 mm** | **LOCKED** |
| R-6 | **Routing consequence** | **the only through-hole field on an otherwise all-SMD board** — it blocks routing on **every layer beneath it**, on the most constrained edge (**M-12**) | **LOCKED** |
| R-7 | Position | right wall, **below the display band**, above the power control. The **7.87 mm body depth exceeds the 6.73 mm of PCB clear of the display**, so it **cannot sit beside the panel** | **TARGET** |
| R-8 | Recessed bay | **≥ 1.5 mm below the outer wall face** | **TARGET** |
| R-9 | Wall aperture | **34 × 10 mm nominal**, 0.3 mm clearance to the accessory shell on all sides, plus the keying rib | **TARGET** |
| R-10 | **Keying** | **asymmetric rib/step on the UPPER edge only** — rows are 2.54 mm apart, so the key must be unambiguous, **not a chamfer** | **LOCKED** (D-097) |
| R-11 | **Anti-shift** | recess **CLOSED AT BOTH ENDS**, ≤ 0.3 mm clearance, so a one-column lateral shift is **mechanically impossible** | **LOCKED** (D-097) |
| R-12 | Lead-in | chamfer on all four recess walls | **TARGET** |
| R-13 | **Support / load path** | **≈ 33 N average insertion** (24 × 1.39 N), **peak higher**; withdrawal ≈ 20 N. **Must be carried by a moulded enclosure boss/rib and a backing rib capturing the connector body — not by the solder joints** (**M-10**) | **LOCKED** (D-097) |
| R-14 | Accessory bottoming | the accessory shell **bottoms on an enclosure boss** | **LOCKED** (D-097) |
| R-15 | Mating pin | **0.64 mm (.025 in) square post, engagement 4.34–6.35 mm**. **Extra-long-pin headers (8.13 mm posts) must NOT be used** | **LOCKED** |
| R-16 | Marking | pin-1 triangle; **"COMMUNITY PORT — 3V3 LOGIC ONLY"** and **"5V PIN IS POWER OUTPUT ONLY"** | **LOCKED** (D-090) |
| R-17 | Power switch | `SW9` **`JS102011SAQN`** SPDT slide, ~**4.7 × 2.9 × 2.0 mm** body plus actuator. **Right wall, lower third** | **LOCKED (part)**, position **TARGET** |
| R-18 | **Hidden BOOT access** | **recessed BOOT access on the right wall** — reachable with a tool, **not** by a bare finger, and not a visible user control | **TARGET** |
| R-19 | Assembly | `J5` is **hand-soldered after reflow** — one of exactly **two** manual parts per board | **LOCKED** (D-206/D-207) |

---

## 6. Top edge

| # | constraint | value | status |
|---|---|---|---|
| T-1 | **915 MHz SMA bulkhead** | Amphenol **`095-902-568-150`** — one assembly: AMC right-angle plug → RG-178 → **SMA female straight bulkhead jack, IP67**. Ships with **its own nut and washer** | **LOCKED** |
| T-2 | Panel hole | **Ø6.5 mm clearance hole**, top edge, **left half** | **LOCKED** |
| T-3 | **SMA ↔ IR spacing, rule 1** | **≥ 15 mm CENTRE-TO-CENTRE**, bulkhead hole ↔ either IR window | **LOCKED** |
| T-4 | **SMA ↔ IR spacing, rule 2** | **≥ 8 mm EDGE-TO-EDGE**, SMA **body** ↔ either IR **aperture** | **LOCKED** |
| T-5 | **Which governs** | **BOTH. Satisfy whichever is larger once the real SMA body OD is measured.** On a ~9.5–11 mm hex body and a ~Ø5.5–6.0 mm aperture, T-4 implies ≈ 15.5–16.5 mm centre-to-centre and is therefore the binding one | **CAD-TO-VERIFY** (B-52 OPEN) |
| T-6 | Pigtail routing | **must NOT cross the IR optical path**; **minimum bend radius 5 mm**; **service loop ≥ 15 mm** | **LOCKED** |
| T-7 | **IR TX** | `D1` Vishay **`TSAL6100`**, T-1¾ **Ø5 mm leaded**, **2.54 mm lead pitch**, **±10° half-angle**, 2.4× brighter on axis than the TSAL6200 the layout was first written against. Top edge, **right of centre** | **LOCKED** |
| T-8 | IR TX axis | **normal to the top face, ±0°** | **LOCKED** |
| T-9 | **IR RX** | `U6` Vishay **`TSOP38238`** (`TSOP38438` same-package fallback), ~**6.0 × 5.6 × 4.7 mm** minicast, **±45° FOV**. Top edge, **right end**. **Tallest top-side component on the board** | **LOCKED** |
| T-10 | **IR TX ↔ IR RX separation** | **≥ 15 mm**, receiver **outside the LED emission cone** | **LOCKED** |
| T-11 | **Opaque IR barrier** | **MANDATORY. Full height between the two windows, bonded to BOTH shells.** It blocks the internal reflection path, which is the path that actually causes self-blinding | **LOCKED** |
| T-12 | IR windows | IR-transmissive (visibly opaque acceptable), **recessed 0.5 mm** | **TARGET** |
| T-13 | Top-side height | IR receiver at 4.7 mm **must sit outside the display shadow** — top edge only | **LOCKED** |
| T-14 | `D1` assembly | **hand-soldered after reflow** (through-hole) — the second of exactly two manual parts | **LOCKED** |

---

## 7. Rear face

| # | constraint | value | status |
|---|---|---|---|
| N-1 | **NFC clear zone** | **48 × 48 mm MINIMUM CLEAR REGION**, metal-free | **LOCKED** (D-127/D-128/D-131) |
| N-2 | Antenna | Taoglas **`FXC.46.52.0075X.B.dg`** — **Ø46 mm, 0.3 mm thick, REVERSE ferrite** | **LOCKED** |
| N-3 | Mounting | **adhesive side bonds to the INNER REAR shell surface**; field reads **OUTWARD** through the rear plastic; **ferrite faces INWARD** toward the PCB and battery | **LOCKED** |
| N-4 | Zone location | **rear upper third, centred in X** | **TARGET** |
| N-5 | **Battery overlap** | **ZERO overlap permitted** | **TARGET — policy, not a mitigation** |
| N-6 | Metal keepout | **no metal within 5 mm of the loop perimeter** — screws, bosses, shielding cans included | **TARGET** |
| N-7 | Boss keepout | the two mid-span bosses must sit **outside the loop zone** | **TARGET** — see §9 O-3 |
| N-8 | Matching network | on the PCB, **within 15 mm of the loop feed point** | **TARGET** |
| N-9 | Speaker separation | **≥ 20 mm from the loop perimeter** — the Nd-Fe-B magnet is the largest ferrous mass in the device | **TARGET** — see §9 O-2 |
| N-10 | `J7` mating clearance | JST ACH is **TOP ENTRY** — the socket drops on from above and the wires leave horizontally. **Vertical clearance above `J7` is required** | **LOCKED** |
| N-11 | `J7` reach | **75 mm cable**, so `J7` must lie within **75 mm of ROUTED cable length** of the antenna, clear of the 433 MHz flex | **LOCKED** |
| N-12 | **Battery envelope** | **60 × 75 × 8.0 mm**, ~2500–3000 mAh, 1S Li-ion/LiPo pouch | **LOCKED** (D-071) |
| N-13 | Battery location | **rear lower two-thirds**, behind the controls | **TARGET** |
| N-14 | Battery retention | **adhesive pad plus a moulded rib pocket. NO compression against the shell** | **TARGET** |
| N-15 | Battery connector | JST-PH 2-pin `J4`; **service loop routed away from the NFC zone** | **LOCKED** |
| N-16 | **Speaker** | `LS1` PUI **`AS02008MR-LW152-R`**, **Ø20 ± 0.2 × 3 ± 0.2 mm**, 8 Ω, 0.5 W rated / 0.8 W max, metal housing, **Nd-Fe-B magnet**, 2.4 g | **LOCKED** (D-148) |
| N-17 | Speaker location | **rear, lower-right**, diagonally opposite the microphone, **rear-firing** | **TARGET** — see §9 O-2 |
| N-18 | **Speaker rear cavity** | **1.5–2.0 cm³ SEALED behind the driver.** Without it, low-mid output collapses and speech sounds thin | **LOCKED** (requirement), volume **TARGET** |
| N-19 | Speaker grille | **≥ 25 % open area**, hole pattern Ø0.8–1.0 mm, acoustic mesh behind | **TARGET** |
| N-20 | Speaker ↔ microphone | **≥ 60 mm AND on opposite faces** | **TARGET** |
| N-21 | Magnet clearance | the Nd-Fe-B magnet must stay clear of **both** the NFC zone and the microphone | **TARGET** |

---

## 8. Internal RF, cables and bosses

### 8.1 433 MHz

| # | constraint | value | status |
|---|---|---|---|
| A-1 | Antenna | Taoglas **`FXP450.07.0100C`**, body **47 × 17 × 0.28 mm**, 100 mm cable, I-PEX MHF1 | **LOCKED** |
| A-2 | Mount | **adhesive against a PLASTIC WALL**, **LEFT / LOWER-SIDE internal region** | **LOCKED** |
| A-3 | **Must NOT be laid on the PCB** | explicit prohibition | **LOCKED** |
| A-4 | Clearances | must clear the **LiPo, the NFC loop and its ferrite, the speaker magnet, large ground pours, metal bosses and screws, the USB shell, the 915 bulkhead and pigtail, and the IR structures** | **LOCKED** |
| A-5 | **NFC conflict keepout** | the stored/mounted 433 flex **must not cross the NFC zone**; with a 48 mm zone in a 75.0 mm cavity there is **~13.5 mm of margin each side** — route in that margin | **TARGET** |
| A-6 | **Service access** | the **`U7` IPEX socket must remain reachable with the shell open**, so the flex can be swapped for an external pigtail **without a respin** | **LOCKED** |

### 8.2 Cable lengths

| # | cable | length | status |
|---|---|---|---|
| C-1 | NFC antenna → `J7` | **75 mm** 28 AWG twisted pair, ACH(F) | **LOCKED** (part) |
| C-2 | 433 antenna → `U7` | **100 mm** | **LOCKED** (part) |
| C-3 | 915 `U8` → SMA bulkhead | **150 mm** RG-178 | **LOCKED** (part) — see §9 O-5 |
| C-4 | Speaker → `J6` | **152 ± 10 mm** UL1571 AWG #32, RED (+) / BLACK (−), JST `PHR-2` + `SPH-002T-P0.5S` | **LOCKED** (part) |
| C-5 | Speaker polarity | cone moves **FORWARD** on positive at the **RED** lead = `SPK_P` = `J6` pin 1 | **LOCKED** |
| C-6 | **Crossing rule** | **no antenna cable may cross another antenna's radiating element or the IR optical path**; the NFC pair must stay clear of the 433 flex | **LOCKED** |
| C-7 | RF bend radius | **≥ 5 mm** on RG-178/1.13 mm coax | **LOCKED** |

### 8.3 Mounting bosses

| # | constraint | value | status |
|---|---|---|---|
| M-1 | Count and size | **6 × M2** | **TARGET** |
| M-2 | Arrangement | **4 corners plus 2 mid-span**, nominally at **Y ≈ 50 mm and Y ≈ 100 mm** | **TARGET** — see §9 O-3 |
| M-3 | Corner inset | **5.0 mm from each board edge** | **TARGET** |
| M-4 | Boss keepout | **Ø6.0 mm copper-and-component free**, full height | **TARGET** |
| M-5 | Why six | a **148 mm span on 1.6 mm FR4 with a battery behind it** will flex under button pressure with corner support alone | **TARGET** |
| M-6 | NFC interaction | **no boss or screw may pass through the NFC active zone**, and none within **5 mm of the loop perimeter** | **TARGET** |
| M-7 | Beta-DM comparison | Beta-DM used **four Ø2.4 mm holes** (measured); v2 adds two mid-span | reference |

---

## 9. Items that BLOCK a clean floorplan and need a CTO ruling

**These are surfaced, not decided.** No design change was made for any of them.

| # | item | why it blocks P1 |
|---|---|---|
| **O-1** | **Microphone board-face assignment** | F-15/F-21: the enclosure aperture is on the **FRONT** face, but M-14 says the acoustic path leaves the **PCB's bottom** face. Both are satisfiable **only** if `MK1` is placed on the copper face pointing away from the front shell. **No floorplan exists, so that side has never been assigned.** P1 cannot place `MK1` until it is. |
| **O-2** | **The rear face is over-constrained by ≈ 8 mm** | The rear must simultaneously hold, in Y: battery **75** + NFC clear zone **48** + speaker **Ø20** + the **≥ 20 mm** speaker-to-loop separation = **163 mm** against a **155 mm** cavity. Moving the speaker beside the battery in X does not help: the 60 mm battery in a 75.0 mm cavity leaves **7.5 mm per side** against a Ø20 driver. This is before the 5 mm NFC metal keepout, the shell lip and the bosses. **At least one of {speaker↔loop separation, speaker location/face, battery Y, NFC zone position} must give.** All four are currently recorded as binding. |
| **O-3** | **Mid-span boss at Y ≈ 100 collides with the grown NFC zone** | The zone grew 45 → 48 mm and carries a **5 mm metal keepout**. A boss nominally at Y ≈ 100 now sits on or inside the zone's lower keepout boundary. The boss must move down, or the zone must move up — and the zone is **LOCKED** while the boss is **TARGET**. Confirm the boss may move to **Y ≤ ~95**. |
| **O-4** | **The microSD ↔ USB-C separation figure is not physically achievable** | Recorded as **"≥ 8 mm centre-to-centre"**. The two bodies are ~**14.0 mm** and ~**9.2 mm** wide, so their centres cannot be closer than **≈ 11.6 mm** before they touch, and a wall rib between the apertures pushes that to **≈ 13.6 mm**. The 8 mm figure reads as an **edge-to-edge** number written into a centre-to-centre row. Ruling needed on which it is. |
| **O-5** | **The 915 MHz pigtail is longer than the cavity wants** | `095-902-568-150` is a **150 mm** assembly in a **155 mm** cavity, with a **≥ 5 mm** bend radius and a **≥ 15 mm** service loop, and it **must not cross the IR path**. Roughly 150 mm of RG-178 has to be parked somewhere that is already claimed by the 433 flex, the NFC pair and the battery. **A shorter length in the same Amphenol series would remove a routing problem for no electrical cost** (loss is already negligible at ≈ 0.4 dB). **No substitution is proposed here** — D-195 locked this exact MPN, and changing it is a CTO call. |
| **O-6** | **The internal "antenna storage channel" cannot hold the locked 915 antenna** | §8 of the interface spec reserves a **left-wall storage channel "sized for the stowed whip"**. The locked whip is the Taoglas **`TI.92.2113`, 198 ± 3.3 mm × Ø13 mm**. The cavity is **75 × 155 × 18.5 mm** — its longest internal diagonal is ≈ **172 mm**. **The whip does not fit inside the device in any orientation.** The same left wall is also the **LOCKED** mount region for the 433 MHz flex (A-2). Either the storage requirement is **withdrawn** (the whip is an external accessory on a hinged SMA and is carried separately) or a different antenna is chosen. **Withdrawing it would free the entire left wall for the 433 flex and the cable runs** — the single largest simplification available before floorplanning. |

---

## 10. What this file deliberately does not contain

- **No coordinates.** No origin, no part positions, no outline vertices.
- **No layer or side assignments**, except where a part's own construction forces one (F-16, F-21, R-3).
- **No net, routing or copper decision.** Netclasses, layer stack and impedance are FBV2-P2.
- **No enclosure styling** — radii, texture, branding and surfacing remain M-05 and do not block P1.
- **No new requirement.** Every row above traces to `MECHANICAL_INTERFACE_SPEC.md`, `CTO_DECISIONS.md`,
  `assembly/OFF_BOARD_BOM.md` or a manufacturer drawing already in evidence.
