# Beta-DM — R2 power-via DFM gate

**CLOSED.** The gate below was run as analysis; the CTO then rejected the
landed geometry and approved candidate B, which **is now landed** by a minimum
four-object edit (3 segments + the via). Measured on the real board after
landing: mask dam **0.1250 mm**, copper overlap **0.0000 mm**, ordinary
clearance **0.2000 mm**, KiCad DRC **0 errors**, `BOOT_N` / `WAKE_INT_N` /
`+3V3` one island each and the first two untouched.

Beta-DM solder mask is locked to **GREEN** for this fabrication build; the
0.125 mm dam is accepted under that constraint. See
[fab/BETA-DM-FABRICATION-NOTES.md](fab/BETA-DM-FABRICATION-NOTES.md).

Every number below is measured from `aqroot-Beta-DM.kicad_pcb`, not taken from
any earlier report.

---

## 1. Exact geometry

### R2 — `Resistor_SMD:R_0603_1608Metric`, B.Cu, origin (22.0000, 37.5000), 0°

| feature | geometry |
|---|---|
| courtyard `B.CrtYd` | x 20.5200 … 23.4800, y 36.7700 … 38.2300 (2.960 × 1.460 mm) |
| body outline `B.Fab` | x 21.2000 … 22.8000, y 37.0875 … 37.9125 (1.600 × 0.825 mm) |
| `R2.1` pad | centre (21.1750, 37.5000), 0.800 × 0.950 roundrect r = 0.200, layers B.Cu/B.Mask/B.Paste, net `+3V3`; copper x 20.7750 … 21.5750 |
| `R2.2` pad | centre (22.8250, 37.5000), same size, net `BOOT_N`; copper x 22.4250 … 23.2250 |

Board setup, read from the file: **`pad_to_mask_clearance 0`** and no paste
clearance — so **the solder-mask opening and the paste aperture are both
exactly the pad copper**. Via tenting: **front yes, back yes**;
`covering`, `plugging`, `capping`, `filling` are **all no**. The via record
carries no tenting override, so it inherits the board default.

### The REJECTED via — (21.8500, 37.4000), 0.65 / 0.40, annular 0.1250 mm

| measurement | value |
|---|---|
| via centre to `R2.1` copper edge | 0.2750 mm |
| **via copper vs `R2.1` copper** | **−0.0500 mm → OVERLAP** (same net, so DRC-legal) |
| **drill edge to `R2.1` copper** | **+0.0750 mm** |
| **drill edge to `R2.1` solder-mask opening** | **+0.0750 mm** |
| **drill edge to `R2.1` paste aperture** | **+0.0750 mm** |
| via copper vs `R2.2` (foreign net) | +0.2500 mm, rule 0.200 — PASS |
| drill edge vs `R2.2` copper | +0.3750 mm, rule 0.250 — PASS |
| **via centre inside R2 courtyard** | **YES**, 0.6300 mm inside |
| **via centre inside the R2 body outline** | **YES**, 0.3125 mm inside |
| via tented on B.Cu | yes (inherited), **LPI tent only — not filled, plugged or capped** |

## 2. Why this fails DFM

**The solder-mask dam between the `R2.1` opening and the tented barrel is
0.0750 mm.**

| reference | limit | verdict |
|---|---|---|
| JLCPCB 4-layer minimum solder-mask dam | 0.100 mm | **FAIL** |
| IPC-A-600 class 2 practical web | 0.100 mm | **FAIL** |
| conservative house rule | 0.125 mm | **FAIL** |

Consequences, in order of likelihood:

1. **The dam will not image reliably.** A 0.075 mm LPI web adjacent to an open,
   paste-printed pad is below every fab's minimum. In production it is
   under-cured, thinned or simply absent.
2. **Merged mask opening.** When the dam goes, the `R2.1` opening and the via
   barrel become one opening. There is then a continuous wetting path from the
   printed paste into a 0.40 mm through-hole.
3. **Solder wicking at reflow.** A 0.40 mm barrel is not sealed by tenting —
   LPI bridges a hole, it does not plug it, and 0.40 mm is at or beyond what
   most fabs will guarantee tenting for. Molten solder drawn down the barrel
   gives a starved or open `R2.1` joint, and 0603 chips are strongly prone to
   **tombstoning** when one termination is starved.
4. **Solder egress on F.Cu.** The via is a through via; wicked solder can bead
   out on the opposite side.
5. **The via sits under the physical 0603 body**, between the terminations, so
   none of this is inspectable after assembly and rework means removing the
   part.

**Paste interaction**: the paste aperture equals the pad copper, so printed
paste stops 0.075 mm from the drill edge — directly against the failing dam.

**Assembly / pick-and-place**: the via land plus its tent forms a local rise of
roughly 0.05 mm under the body. On its own that is tolerable for an 0603, whose
standoff is set by its terminations; combined with an unreliable tent it adds
to the tombstoning risk rather than being an independent defect.

**KiCad DRC does not test any of this.** DRC returns 0 errors on the landed
board because the overlap is same-net and no electrical rule is broken. That is
exactly why this gate is separate.

---

## 3. The comparison asked for in §2

Both alternatives keep P3V3 ≥ 0.40 mm, the POWER via at 0.65 / 0.40, and touch
neither `BOOT_N` nor `WAKE_INT_N`.

| | **A — rejected** | **B — LANDED** |
|---|---|---|
| via | (21.8500, 37.4000) | **(21.9000, 37.4000)** — 0.050 mm east |
| escape length | 3.531 mm, 13 seg, 1 via | 3.631 mm, 13 seg, 1 via |
| via copper vs `R2.1` | **overlap 0.0500 mm** | **0.0000 mm — tangent, no overlap** |
| **solder-mask dam** | **0.0750 mm — FAIL** | **0.1250 mm — PASS** |
| drill edge to paste aperture | 0.0750 mm | 0.1250 mm |
| under the R2 body | yes | yes (unavoidable — see below) |
| tightest electrical clearance | 0.2000 mm | 0.2000 mm (via vs `R2.2`) |
| rule exception needed | none | **none** |
| KiCad DRC, zones refilled | 0 errors | **0 errors** |
| `BOOT_N` / `WAKE_INT_N` / `+3V3` | one island each | one island each, **unchanged** |

### Options that do not exist

| option | result |
|---|---|
| **via-free escape** (B.Cu only, no layer change) | **NO PATH** — `R2.1` cannot reach the `+3V3` rail without a via |
| **via outside every component body outline** | **NO ROUTE**, at 0.200 mm *and* at 0.175 mm |
| via with dam ≥ 0.100 mm, rasterised at 0.200 mm | no route found by the raster model |
| via with dam ≥ 0.125 mm | route found — and it measures **legal at the ordinary 0.200 mm** |

The last row is the important one. The 0.175 mm relaxation was only needed to
get the raster model past a cell that sits **exactly** on the 0.200 mm boundary;
exact analytic measurement of the resulting route shows **0 objects below the
ordinary rule**, minimum separation 0.2000 mm, and KiCad agrees with 0 errors.

**So the approved 0.175 mm exception is still NOT NEEDED.** The DFM improvement
is available at ordinary rules. What was wrong in the previous pass was not the
absence of the exception — it was that no DFM audit had been run at all.

### Residual risk of option B, stated honestly

The via remains under the 0603 body; that is unavoidable for any `R2.1` escape
on this board and was proven, not assumed. With a 0.125 mm dam, zero copper
overlap and no paste over the barrel, a tented via under a chip resistor is
ordinary practice. The one item worth a fab note is that a 0.40 mm drill is at
the upper end of what LPI tenting seals; if the CTO wants belt-and-braces,
`plugging`/`covering` can be enabled for this board at a process cost. It is
not required to pass the gate.

---

## 4. `E6_R2_1_CLR` / `E6_R2_1_WIDTH` — keep now, retire before pours

Measured on both the landed board and the option-B scratch:

| area | layers | enclosed P3V3 items | widths |
|---|---|---|---|
| `E6_R2_1_CLR` (22.800, 35.500)–(23.800, 36.500) | F/In1/In2/B | **0** | — |
| `E6_R2_1_WIDTH` (20.625, 35.800)–(23.450, 38.125) | B.Cu | 3 | all **0.40 mm** |

Neither is load-bearing: the clearance area encloses nothing, and everything
inside the width area already meets the **unrelaxed** 0.40 mm floor.

**Latent inheritance risk while they stay in the file — yes, and it is not zero:**

* `E6_R2_1_CLR` grants **0.100 mm** clearance to any P3V3 non-pad copper wholly
  inside a 1 × 1 mm square on all four layers. Exposure is small (a track has to
  fit entirely inside it) but real, and it would be silent.
* `E6_R2_1_WIDTH` grants a **0.15 mm** width floor to P3V3 B.Cu copper wholly
  inside a 2.825 × 2.325 mm rectangle that sits directly over the `R2.1` escape
  region. This is the larger exposure: a future pass could route a 0.15 mm power
  neck there and DRC would not object.

Neither area affects `BOOT_N` or `WAKE_INT_N` — every `E6_R2_1` rule is scoped
`A.hasNetclass('P3V3')` and both nets are `Default`, so **no foreign-net
inheritance is possible**.

**Recommendation: KEEP TEMPORARILY, RETIRE BEFORE FINAL POURS.** Until they are
retired, any new `+3V3` copper in x 20.6 … 23.5, y 35.5 … 38.2 must have its
width and clearance checked by hand, because DRC will not catch a violation
there.

---

## 5. Landing record

Candidate B was landed as the **minimum** change: 10 of the 13 escape segments
were already common to both routes and were left alone.

| | |
|---|---|
| removed | 3 segments + 1 via (`a5e10000-ac94…`, `a5e10000-7889…`, `a5e10000-ac7a…`, `a5e10000-e1e0…`) |
| added | 3 segments + 1 via, UUID prefix `f2b40000` |
| measured on the real board | via exactly (21.900000, 37.400000), 0.650000 / 0.400000, annular 0.1250 mm |
| mask dam | **0.1250 mm** |
| via copper vs `R2.1` | **0.0000 mm — tangent** |
| ordinary clearance | tightest **0.2000 mm** (via vs `R2.2` pad) |
| `R2.2` drill-edge clearance | 0.3250 mm |
| via tenting | inherited, both sides, no per-via override |
| paste over the via | none — drill edge 0.125 mm outside the paste aperture |
| DRU | **unchanged** — no exception created |
| preservation diff | 188 footprints, 776 pad keys, 44 zone definitions, Edge.Cuts identical; 0 objects modified in place |
| `BOOT_N` / `WAKE_INT_N` | byte-identical — 67 seg/5 via/52.445 mm and 178 seg/4 via/97.588 mm |
| `hardware/beta/` | unchanged; no pours
