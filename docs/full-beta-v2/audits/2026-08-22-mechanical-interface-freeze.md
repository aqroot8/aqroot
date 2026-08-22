# AQROOT Full Beta v2 — Mechanical Interface Freeze Audit

Date: 2026-08-22
Task: **FBV2-MECH-001**
Gate: **FBV2-A2**
Repository HEAD at audit: `e8886d6`
Scope: **documentation only.** No KiCad, PCB, mechanical CAD, firmware or fabrication file was created or modified. `hardware/beta/`, `hardware/beta-dm/` and the untracked `hardware/beta/mechanical/` were **read only**. `hardware/beta-v2/` was not created.

**Deliverable:** [`../mechanical/MECHANICAL_INTERFACE_SPEC.md`](../mechanical/MECHANICAL_INTERFACE_SPEC.md) — the authoritative pre-CAD dimension source.

---

## 1. What this audit had to establish

The gate criterion is not "is the enclosure designed" — it is *"do we have enough
dimensional authority to begin schematic/PCB migration without later discovering
that something does not fit."* Nine specific failure modes are named in the brief.
Each is addressed below.

---

## 2. Sources and their weight

| source | weight |
|---|---|
| `hardware/beta/mechanical/reports/PHASE-1-MECHANICAL-AUDIT.md` (untracked, read only) | **Measured.** Board outline 74 × 155 × 1.6 mm, R3.0 corners, four Ø2.4 mm holes; display panel shadow X12–62 / Y9–78 (**50 × 69 mm**) with an 0.8 mm height limit; battery shadow X20–69 / Y37–77.5 with a 1.2 mm limit; NFC reserved X28–54 / Y15–35 (**26 × 20 mm**) |
| `01 - Hardware Core.md` | Display is 2.8″ 240×320 IPS + FT6236 CTP; J1 = Hirose FH69-50S-0.5SH, footprint VERIFIED_VENDOR_EXACT |
| Beta-DM BOM / measured pad maps | Component identities and counts |
| CTO ruling | 80 × 160 × 23 mm **external**, and the six-face layout |
| Class-typical component figures | Used to size envelopes where no vendor drawing is archived — **marked as typical throughout** |

**The single most important gap, quoted from the Phase-1 audit:** *"Exact
CH280QV10-CT panel outline, thickness, active area, and FPC bend stack are not
archived locally."* The 50 × 69 mm shadow is a measured **keepout**, not a vendor
outline. The display envelope is therefore set at 52 × 71 × 3.0 mm to absorb that
uncertainty — and it is why display size is raised as an open CTO item rather than
quietly assumed.

---

## 3. Orientation — resolved, not assumed

The brief gives face assignments but not an orientation. It is determined by two
independent facts:

1. The Beta-DM board is **74 wide × 155 tall** — portrait.
2. The external target is **80 × 160** — 74→80 and 155→160 map one-to-one.

**The device is portrait: 80 mm (X) × 160 mm (Y) × 23 mm (Z).** Recorded as
**LOCKED** because it follows from measured geometry, not from preference. The
front is therefore display-above-controls, not a landscape gamepad layout.

---

## 4. Z stack-up — the governing result

Three columns were computed with real clearances rather than nominal sums
(spec §3.3). The governing column is **the control region with the battery behind
it**: front shell 2.0 + keypad/travel 1.0 + tact switch 4.3 + PCB 1.6 + battery 8.0
+ clearance 0.6 + rear shell 2.0 = **19.5 mm of 23.0 mm**.

### Verdict: **PASS — not tight. 3.5 mm spare.**

The interesting finding is not that it fits; it is **what to do with the margin.**
Left as air it is wasted. Allocated to the battery it raises the pack from the
5–6 mm a 2000 mAh cell needs to **8.0 mm**, i.e. the **2500–3000 mAh class** — a
25–50% runtime improvement on the figure the existing power budget assumes, for
zero external size change.

The display column consumes only 11.8 mm and the speaker column 13.6 mm, so
neither constrains the design.

**The device could be thinned to ≈20 mm** if industrial design prefers. Not
recommended: 23 mm is a comfortable handheld thickness and the capacity is worth
more than 3 mm.

---

## 5. Cavity and PCB — the consequential result

```
INTERNAL_CAVITY = 75.0 × 155.0 × 18.5 mm     (2.0 mm walls, 1.0/0.5 mm assembly tolerance)
MAX_PCB         = 72.0 × 152.0 mm            (1.5 mm edge clearance)
RECOMMENDED_PCB = 70.0 × 148.0 mm
```

### Beta-DM 74 × 155 mm against a 75 × 155 mm cavity

| axis | board | cavity | clearance |
|---|---|---|---|
| X | 74.0 | 75.0 | **1.0 mm total** |
| Y | 155.0 | 155.0 | **0.0 mm** |

**The existing board is the cavity.** There is no room for the shell lip, six
bosses, ribs, or assembly access — which is the same failure Field Slate v5
documented in its own root-cause section: the envelope was never allowed to drive
a PCB revision.

### Verdict: **SHOULD BE RE-FLOORPLANNED WITH A DIFFERENT OUTLINE**

Not merely reduced. Two independent reasons:

1. **Dimensional.** −4 mm X and −7 mm Y is the minimum to make it fit at all.
2. **Content.** Full Beta v2 removes HOME and the RGB nets, replaces both
   expanders, changes the connector 26 → 20 pins, adds the four-FET P2 protection
   stage and the dead-cell recovery branch, adds the NFC crystal / matching /
   antenna, restores IR TX and RX, and adds the accessory load switch. Reusing the
   Beta-DM floorplan would re-inherit the exact congestion that made `U1.9` (IR TX)
   need a two-object copper release and `U1.36` (IR RX) have **no single-object
   release at all**.

**Re-floorplanning from the cavity is what Field Slate v3 asked for in July and
never got.** This is the task that finally performs it.

---

## 6. NFC versus battery — resolved by plan, not by shielding

The earlier framing was "a LiPo pouch behind the loop kills Q; use ferrite or
offset." The better answer is available for free:

**The display occupies the front upper third, so the rear upper third is empty.**
Put the **NFC loop there (45 × 45 mm)** and the **battery in the rear lower
two-thirds (60 × 75 × 8 mm)**, behind the controls. **Zero overlap** — stated as a
policy, not a mitigation.

Ferrite is still specified (0.3 mm, full loop footprint) because once the battery
is moved away, **the PCB ground pour becomes the dominant near-field threat**.

Two consequential constraints fall out:

- The **two mid-span mounting bosses must sit below Y = 100 mm**, outside the loop
  zone — a boss through the loop would be a metal intrusion in the worst place.
- The **left-side antenna storage channel must terminate below Y = 100 mm**, so the
  stowed whip never lies across the loop. With a 45 mm loop in a 75 mm cavity there
  is ~15 mm of margin each side for the channel.

The Beta-DM NFC reservation was **26 × 20 mm** (measured). **45 × 45 mm is a 3.9×
area increase**, which is the difference between a token loop and one with usable
range at 3.3 V — and 3.3 V is what the design now runs (D-055), having already
accepted ~0.64× antenna current. The loop area is where that is won back.

---

## 7. Acoustics

**Microphone (higher priority).** The ICS-43434 is **bottom-port** — the acoustic
hole is in the PCB under the part. The path is PCB hole → compressed gasket →
front shell aperture, with the **tunnel ≤2.5 mm**; longer tunnels roll off exactly
the high frequencies that carry speech intelligibility. Front face, bottom third.

**Speaker.** Ø20 × 4.0 mm, 8 Ω, ≤1 W, **rear-firing** per the CTO layout, with a
**1.5–2.0 cm³ sealed rear cavity** — without it the low-mid output collapses and
speech sounds thin. Rear lower-right, **≥60 mm from the microphone and on the
opposite face**, and **≥20 mm from the NFC loop** because the magnet is the largest
ferrous mass in the device.

Deliberately not over-engineered: no port, no tuned volume. Half-duplex voice is
adequately served; echo cancellation is firmware, not mechanics.

---

## 8. IR and antenna on the top edge

Both share the top edge, and they conflict in two ways that are easy to miss.

| conflict | resolution |
|---|---|
| Emitter blinds the receiver | **≥15 mm separation** *and* a **mandatory opaque barrier** bonded to both shells. Separation alone does not fix it — the internal reflection path is the one that actually causes self-blinding |
| A fitted whip shadows the IR cone | **≥15 mm** between the antenna bulkhead and the IR windows; antenna on the **left half**, IR on the **right half** |

Emitter axis normal to the top face so the device points like a remote; receiver
FOV ±45°. Pigtail from the module u.FL to the bulkhead with a **5 mm minimum bend
radius and a ≥15 mm service loop** — consistent with D-040, which keeps
controlled-impedance RF off the main PCB.

---

## 9. The nine gate failure modes

| # | risk named in the brief | resolved? | how |
|---|---|---|---|
| 1 | PCB does not fit | **YES** | 70 × 148 target inside a 75 × 155 cavity — 2.5 mm/side beyond minimum |
| 2 | Display does not fit | **YES** | 52 × 71 envelope in an 80 mm-wide front. Even a 3.5″ panel fits — hence open item M-01 is an *opportunity*, not a risk |
| 3 | Battery does not fit | **YES** | 60 × 75 × 8.0 mm, verified against the governing Z column |
| 4 | NFC conflicts with battery | **YES** | Zero-overlap plan split (§6) |
| 5 | Community connector cannot exit | **YES** | 24 × 10 × 9 mm right-angle envelope, right wall, 26 × 12 mm aperture |
| 6 | Antenna connector conflicts with IR | **YES** | Left/right split on the top edge, ≥15 mm |
| 7 | USB/microSD cannot align with the shell | **YES** | Bottom edge, ≥8 mm centre-to-centre, +18 mm microSD insertion travel reserved outside the shell |
| 8 | Speaker/mic cannot be accommodated | **YES** | Speaker column 13.6 mm of 23; mic tunnel ≤2.5 mm |
| 9 | Mounting bosses force a PCB redesign | **YES** | 6 × M2 positions and Ø6.0 mm keepouts specified **before** the floorplan exists — which is the entire point of doing this now |

---

## 10. FBV2-A2 gate

### VERDICT: **PASS**

All nine dimensional dependencies are resolved to the level the gate requires.
What remains is **styling and part selection**, which the brief explicitly states
does not block:

- **M-01 display size** — a *choice*, not a blocker. Either answer fits the cavity;
  only the front layout and J1 change.
- **M-02 battery capacity target** — a *choice* about how to spend confirmed
  margin. Either answer fits.
- M-03/M-04 connector and battery MPNs — envelopes are frozen, which is what
  placement needs.
- M-05 cosmetic surfacing — explicitly excluded from the gate.

**Recommended next: FBV2-S1, schematic migration.** The dimensional authority now
exists, and schematic work does not depend on M-01 or M-02.

**One sequencing caution:** do **not** begin PCB floorplanning (FBV2-P1) until
M-01 is answered. Display size sets the front layout, which sets the rear free
area, which sets the NFC zone. Schematic migration is safe to start immediately;
placement is not.

---

## 11. Honest limitations

Recorded because an interface freeze that overstates its own confidence is worse
than none.

1. **Nothing here has been verified in CAD.** Every derived figure is **TARGET**,
   not LOCKED. The cavity follows from a 2.0 mm wall assumption that is reasonable
   and unverified.
2. **Component dimensions are class-typical** where no vendor drawing is archived
   — tact switch, USB-C, microSD, TSOP, slide switch. Adequate for envelope
   freezing; **must be replaced by vendor drawings at CAD time**.
3. **The display is the weakest input.** Its 50 × 69 mm figure is a measured
   *keepout* from the Beta-DM board, not a vendor outline, and the FPC bend stack
   is unknown. This is why M-01 exists.
4. **The Field Slate guard script is now inconsistent with this document.**
   `tools/check_mechanical_consistency.py` reads the v5 block, which still says
   `INTERNAL_CAVITY_MM: not published`. That was true when written. **This task had
   no authority to modify those files**, so the inconsistency is recorded rather
   than silently patched; reconciling it needs a task with authority over
   `18 - Enclosure Field Slate v5.md` and `tools/`.
5. **No PCB outline has been drawn.** 70 × 148 is a recommendation to the
   floorplanning task, not an Edge.Cuts.

---

## Sources

- `hardware/beta/mechanical/reports/PHASE-1-MECHANICAL-AUDIT.md` — read only, untracked
- `01 - Hardware Core.md`, `15/17/18 - Enclosure Field Slate v3/v4/v5`
- Beta-DM BOM and measured pad maps (FBV2-AUDIT-001)
- [`../mechanical/MECHANICAL_INTERFACE_SPEC.md`](../mechanical/MECHANICAL_INTERFACE_SPEC.md)
