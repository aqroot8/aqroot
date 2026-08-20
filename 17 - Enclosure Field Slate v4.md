---
tags: [hardware, enclosure, mechanical, industrial-design, v4]
status: cto-locked-target
supersedes: "[[15 - Enclosure Field Slate v3]] §2 (Dimensions & mass)"
---

# AQROOT Enclosure — "Field Slate" v4 (envelope update)

**This document is the authoritative source for the AQROOT enclosure envelope.**
It supersedes **§2 Dimensions & mass** of [[15 - Enclosure Field Slate v3]] and
nothing else. Every other section of v3 — concept, materials and manufacturing
staging, RF crown, rear NFC target, the 7-button control set, the side antenna
holder, and the antenna zoning that [[12 - RF and Antenna Plan v0.1]] and
[[14 - RootProbe Interface v0.1]] depend on — **remains in force unchanged**.

---

## 1. Envelope — CTO lock

| Property | Value |
|---|---|
| **Body** | **130 × 70 × 23.5 mm** (13.0 × 7.0 × 2.35 cm) |
| With crown | up to **24.5 mm** at the crown — carried over from v3, provisional |
| Mass | 135–165 g (unchanged from v3) |
| Colorway | "Graphite Root" (unchanged from v3) |

| superseded | status |
|---|---|
| **122 × 61 × 23.5 mm** (Field Slate v3) | **SUPERSEDED** |
| ~75 × 45 × 16 mm (original pocket-tool target) | superseded by v3, remains superseded |

The larger footprint is intended as breathing room for the battery, the
antennas, mounting bosses, cabling and clearances, and the shell structure
itself.

This target applies to the Beta-DM physical enclosure, the Beta enclosure
direction, the future Full-Beta PCB revision, and the eventual product
baseline.

---

## 2. Current PCB status

| | |
|---|---|
| Current Beta-DM PCB outline | **74.00 × 155.00 mm**, four R3.0 mm corners, 1.6 mm thick |
| Mounting holes | four Ø2.4 mm at (4, 148), (10.5, 10), (69, 13), (70.5, 144) |
| **Resized in this pass?** | **NO** — the outline is untouched and Edge.Cuts is unchanged |

The current PCB is at fabrication closeout. Its geometry stays frozen unless a
mechanical showstopper forces a revision. The **future Full-Beta PCB revision**
may exploit the larger envelope for easier placement and routing.

---

## 3. OPEN CONFLICT — the current PCB does not fit this envelope

This is recorded, not resolved, and it needs a CTO decision.

The board measures **74 mm wide × 155 mm tall** (verified directly from
Edge.Cuts on both `hardware/beta-dm` and the frozen `hardware/beta` board —
they are identical outlines). Treating the envelope as a portrait handheld,
70 mm wide × 130 mm tall:

| axis | board | envelope outer | shortfall before walls |
|---|---:|---:|---:|
| width | 74.00 mm | 70 mm | **−4.0 mm** |
| length | 155.00 mm | 130 mm | **−25.0 mm** |

The shortfall is larger in practice, because the outer envelope has to contain
the shell walls and a clearance gap. At 2.0 mm walls and 1.5 mm clearance per
side, a 74 × 155 board needs an outer body of roughly **81 × 162 mm**.

So the new envelope moves *toward* the board — 130 × 70 is 8 mm longer and 9 mm
wider than the superseded 122 × 61 — but it does not reach it. The phrase
"breathing room around the current board" does not yet describe this envelope:
against the current PCB it is still an interference, not a clearance.

This conflict is **pre-existing, not introduced by v4**. The untracked
mechanical audit dated 2026-08-15 raised the same point against v3, in the same
terms: a shell cannot be developed honestly until the PCB is reduced or the
product envelope is enlarged.

**Three ways to close it**, for a CTO ruling — no work has been done toward any
of them:

1. **Enlarge the envelope** to roughly 165 × 85 × 23.5 mm and accept a larger
   device.
2. **Shrink the PCB** in the future Full-Beta revision to about 63 × 123 mm so
   it fits a 70 × 130 body with walls and clearance. This is a significant
   placement and routing exercise: the current board is dense and its RF,
   display, battery and NFC keepouts are already tightly packed.
3. **Split the board** into stacked or hinged sections so no single PCB has to
   match the body footprint.

Until one is chosen, **v4's envelope is a product/industrial-design target, not
a mechanical constraint that the current PCB satisfies.** Nothing downstream
should treat the current Beta-DM board as fitting inside it.

---

## 4. What did not change

* No PCB resize, no Edge.Cuts modification, no component movement.
* The crown allowance stays at 24.5 mm; it was not re-evaluated in this pass
  and remains provisional exactly as v3 left it.
* v3's antenna zoning, RF crown definition, rear NFC target, button set and
  side-holder stowage are untouched and remain authoritative.
* `hardware/beta/` is frozen at `beta-full-reference-v1` and was not written to.

---

## 5. Reference

* [[15 - Enclosure Field Slate v3]] — everything except §2 dimensions
* [[12 - RF and Antenna Plan v0.1]] — antenna zoning depends on v3 §4–§7
* [[14 - RootProbe Interface v0.1]] — expansion-zone location
* [[05 - Design Decisions Log]] — historical record; earlier dimension entries
  are deliberately left as written

---

## 6. Two mechanical states — read this before using any number above

There are now **two** distinct mechanical states, and they must not be
conflated.

### A. Current Beta-DM electrical demo PCB

| | |
|---|---|
| PCB | **155 × 74 mm** |
| status | electrically complete; released for fabrication data |
| resize / re-place / re-route for enclosure reasons | **not permitted** |
| Edge.Cuts | unchanged |
| enclosure | a **temporary prototype shell**, larger than the product target |

The Demo-Model enclosure is deliberately not locked here. CAD determines the
minimum practical shell around the 155 × 74 mm board. As a **planning estimate
only** — not a lock — a body in the **~162 × 81 mm minimum class** follows from
2 mm walls plus ~1.5 mm clearance per side. Do not order or model to that
number until wall thickness, connector protrusions, button travel and internal
clearances have been analysed in CAD.

### B. Future AQROOT Beta / Full-Beta / product target

| | |
|---|---|
| external enclosure | **130 × 70 × 23.5 mm — LOCKED** |
| requires | a future PCB placement and routing revision |
| current PCB fits this body | **NO** |

The current board cannot fit 130 × 70 mm, and nothing in this repository should
claim otherwise. §3 above records the measurements.

---

## 7. Locked external layout for the NEXT PCB revision

CTO-locked mechanical direction. It constrains placement on the next revision
and must be satisfied **before** routing begins, not retrofitted after.

### Top

* external **433 MHz antenna connector**
* exact top position remains RF/DFM dependent
* the connector must not compromise the internal 433 / 915 / WiFi antenna
  keepouts
* the IR aperture stays associated with the crown as appropriate

### Left side

* external **antenna storage / holder channel** for the stowed whip
* keep this side substantially free
* **do not** place the community GPIO connector here

### Right side — upper / middle

* **community expansion / J5 interface**
* preferably **recessed and/or keyed** in the final product
* the authoritative electrical **F4 26-pin J5 map is unchanged** unless a later
  explicit electrical revision says otherwise

### Right side — lower

* **Volume +**, **Volume −**, **Power**

This group **may move further down toward the lower third** where that improves
visual spacing, ergonomics, connector clearance, anti-crowding or internal
mechanical clearance. Do not force the controls into the middle if it looks
crowded: **clean industrial design outranks any arbitrary vertical
coordinate.**

### Bottom

* **microSD** access, preferably toward bottom-left
* **USB-C** charge/data, preferably near bottom-centre
* exact positions driven by the next PCB revision and enclosure CAD

### Rear

* clean, **metal-free NFC target zone** preserved
* branding
* **no stored metal antenna across the NFC target** — the antenna holder stays
  on the left side and does **not** move to the rear

---

## 8. Community header — future mechanical direction

The public electrical interface remains the **26-pin F4 `J5` map**. Nothing is
repinned, and the current Beta-DM `J5` is untouched.

For the product, the physical expansion interface should **exit through the
right side** of the enclosure, implemented as a **recessed and/or keyed
connector** rather than permanently exposed male pins.

The next Full-Beta PCB revision must place the `U61` / `J5` cluster around this
mechanical requirement **before routing begins**.
