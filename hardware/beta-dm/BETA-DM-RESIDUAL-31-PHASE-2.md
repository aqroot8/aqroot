# Beta-DM — residual-31 architecture, phase 2

**SCRATCH ONLY. No real-board copper was written; the PCB and the DRU are
byte-identical to `073c898`.** No pours, no component moves, no DNP decisions,
no rule exception.

**Result: the header architecture is NOT PROVEN.** The authorised 12.825 mm
`/SX1262_RXEN` release does open the corridor — all 28 `XGPIO` commodities route
— but the negotiated-congestion solve does **not converge** in either order, and
the commodity it starves is **`/SX1262_RXEN` itself**. The release moves the
shortage rather than removing it.

Outside the header cluster the news is better: **three residuals are now proven
closable**, one of them with no release at all, after two modelling defects were
found and fixed.

---

## 1. Starting state

| item | measured |
|---|---|
| HEAD | `073c898`, `origin/master...HEAD = 0 0` |
| DRC | 0 errors, 240 warnings, 216 unconnected |
| ledger | 216 = A 55 + B 130 + C 31 |
| `hardware/beta/` | empty diff vs `beta-full-reference-v1` |

## 2. The authorised release, re-identified and asserted

| uuid | layer | from | to | length |
|---|---|---|---|---|
| `f4200001-5e60-4b8c-9d03-c10000000001` | B.Cu | (22.325, 10.600) | (17.500, 10.600) | 4.825 mm |
| `f4200003-5e60-4b8c-9d03-c10000000003` | B.Cu | (17.500, 13.500) | (25.500, 13.500) | 8.000 mm |
| | | | **total** | **12.825 mm** |

Assertions all PASS: exactly 2 objects · both `/SX1262_RXEN` · both B.Cu · total
12.825 mm · neither is a via · neither on In2 (so the E5 crossing is untouched)
· neither inside an RF band · UUID prefixes as expected.

### `/SX1262_RXEN` fitted endpoints, read from the board

| pad | position | layers |
|---|---|---|
| `U3.19` | (22.325, 9.438) | B.Cu |
| `U8.6` | (72.000, 129.650) | B.Cu |
| `R74.1` | (69.975, 129.700) | F.Cu |

Net total 18 segments, 4 vias, 196.827 mm, netclass `E5_CROSSING`. Releasing the
two jumpers leaves **three** islands, because the 2.900 mm B.Cu run
(17.500, 10.600)–(17.500, 13.500) between them becomes orphan copper with no
pad. A clean practical release would add it (3 objects, 15.725 mm) — flagged for
ruling, **not taken**, since §1 authorises exactly two.

## 3. Release minimisation

| set | objects | length | reachable |
|---|---|---|---|
| the 2 RXEN segments alone | 2 | 12.825 mm | 0 / 22 |
| **header cluster + the 2 RXEN segments** | **268 seg, 28 via** | **318.496 mm** | **22 / 22** |
| + the five ordinary local signal nets | 346 seg, 34 via | 485.704 mm | 22 / 22 |

The five ordinary local signal nets (`Net-(U15-CT)`, `BMI270_INT1_STRAP`,
`DISP_CS_N`, `Net-(U1-EN)`, `FAST_IO_U0TXD_ROOTPROBE_CS`) buy nothing and are
**dropped from scope** — 78 segments, 6 vias and 167.208 mm removed from the
phase-1 diagnostic set.

## 4. Negotiated congestion — the decisive result

38 commodities in one simultaneous problem: 14 `XGPIO`, 14 `XGPIO*_HDR`,
`FAST_IO_GPIO43_HDR`, `WAKE_ATTN_N_HDR`, both ext-I²C header links,
`ACC_3V3_SW` (at P3V3 geometry), `ACC_PWR_EN`, the three `U15`/`U16` nets, and
**`/SX1262_RXEN` as a simultaneous commodity**, so the J5 routes could not eat
the corridor the RXEN re-land needs. Per-net obstacle maps never contain another
net's copper — other nets are present cost, not obstacles.

| iter | pfac | conflicts (constrained) | conflicts (longest) | unjoined | total mm |
|---|---|---|---|---|---|
| 0 | 0.60 | 17 016 | 17 383 | 4 | 819 / 823 |
| 1 | 1.08 | 15 961 | 15 959 | 4 | 767 / 772 |
| 2 | 1.94 | 13 906 | 14 536 | 3 | 772 / 774 |
| 3 | 3.50 | 13 992 | 14 085 | 3–4 | 811 / 815 |
| 4 | 6.30 | 13 185 | — | 4 | 796 |
| 5 | 11.34 | 13 355 | 14 319 | 3–4 | 828 / 870 |
| 6 | 20.41 | 13 208 | 14 369 | 4 | 829 / 853 |
| 7 | 36.73 | 12 287 | 14 125 | 3–4 | 836 / 867 |
| 8 | 66.12 | 12 809 | 13 488 | 4 | 840 / 855 |
| 9 | 119.02 | 13 306 | 13 177 | 4 | 876 / 836 |

**NOT CONVERGED, both orders** (1983 s and 1902 s). The conflict count plateaus
at 12 300–14 400 from iteration 2 onward while the present-cost factor rises
**198×**, and the route length inflates instead of falling. That is the
signature of a saturated corridor, not of a bad search.

### What actually fails — and it is not the XGPIOs

Both orders end with the **identical** open set:

| commodity | joins still open |
|---|---|
| `ACC_3V3_SW` | 1 |
| `ACC_PWR_EN` | 1 |
| **`/SX1262_RXEN`** | **2** |

**All 14 `XGPIO` and all 14 `XGPIO*_HDR` commodities joined in both orders.**
The corridor released by taking out the two RXEN jumpers is consumed by the J5
traffic, and the net that paid for it cannot get back in. §8 anticipated this
and required RXEN to be a simultaneous commodity; it was, and it still loses.

Corridor capacity measured independently: at the tightest cut (x = 28,
y 8.6…17.5) there are **18** 0.20 mm track slots after the release, against a
demand of 14 `XGPIO` plus `ACC_PWR_EN`, `ACC_3V3_SW` and `RXEN`. The margin is
one or two lanes — which is why the negotiation cannot find a separation.

## 5. Two modelling defects found and fixed

Both were making the board look more sealed than it is. Neither affects any
landed copper.

1. **Own-net through-hole hole clearance** (found in phase 1, fixed here):
   `min_hole_clearance` was stamped around a net's **own** drilled pads. KiCad
   exempts same-net items from clearance, so every J5 pin read as unreachable to
   its own net.
2. **Exact-tangency rejection** (new): the raster used `<=` when stamping
   obstacle discs and capsules, so a cell sitting **exactly** at the clearance
   limit was discarded. KiCad flags a violation only when clearance is *below*
   the minimum. This had already cost a legal R2 via site, and it is what made
   `U11.9` read as having zero free cells.

Re-tested after both fixes: the current board with nothing released is still
**0 / 22** in the header cluster, so the phase-1 conclusion there stands and no
ledger entry changes. The non-J5 picture does change — see below.

## 6. `BQ25185_STAT1` pad escape — §14

| item | measured |
|---|---|
| package | `Texas_DLH0010A_WSON-10-1EP_2.2x2mm_P0.4mm_EP0.9x1.5mm`, F.Cu, 12 pads |
| pitch | **0.400 mm** |
| `U11.9` pad | (66.100, 66.600), **0.750 × 0.200 mm**, copper x 65.725…66.475 |
| neighbour gap | `U11.8` / `U11.10` pad-edge gap **0.200 mm** |
| between-pin escape | needs 0.20 + 0.20 + 0.20 = **0.600 mm** → **impossible**, as expected for the pitch |
| outboard escape at y = 66.600 | clearance **0.3000 mm** — **exactly** the 0.300 mm a 0.20 mm centreline needs |
| free cells at the pad | **11** (phase 1 reported 0 — that was the tangency defect) |
| first true obstruction | an `/01_POWER_TREE/ISET` **via** at x ≈ 67.0–67.5, clearance falling to −0.05 mm |

**The failure was router modelling, not geometry.** The existing DRU
"Pad-escape necking" rules for `U11` set width 0.20 mm and clearance 0.20 mm —
they grant no relaxation, and none is needed. The outboard neck is legal at the
ordinary rules, exactly at the limit, and the real obstruction is an ordinary
`ISET` via that can be moved.

**Result: `BQ25185_STAT1` routes** — 28.007 mm, 70 segments — after releasing
local ordinary `ISET` / `USB_VBUS_CHG` copper. No exception, no lock.

## 7. The non-J5 eight

| residual | outcome |
|---|---|
| `TEST_GPIO46` | **CLOSED with no release at all** — 130.826 mm, 296 seg. Phase 1 called it sealed; that was the tangency defect |
| `BQ25185_STAT1` | **CLOSED** — 28.007 mm, 70 seg, with 15 ordinary power-tree objects (30.381 mm) released |
| `BQ25185_STAT2` | **CLOSED** — 24.666 mm, 54 seg, same release |
| `TEST_GPIO45` | **OPEN** — `DISP_BL_CTL` alone is not enough once `TEST_GPIO46` takes its corridor; its wall also includes `I2S_MIC_DIN`, `SD_CS_N` and `BTN_HOME_N`, all preserve-list |
| `Net-(SW9-A)` `TP13` | **OPEN under policy** — reachable only by releasing 63 objects of `BTN_A_N`/`BTN_B_N`/`BTN_DOWN_N`/`+3V3`; the button nets are preserve-list, so **STOP** |
| `Net-(U15-QOD)`, `Net-(U16-SCLB)`, `Net-(U16-SDAB)` | inside the header cluster — they joined in the negotiated solve, but that solve did not converge overall |

Two of the re-lands for the power-tree release (`ISET`, `BAT_PROTECTED_P`) were
left open by the sequential pass and would need the same negotiated treatment.

## 8. `TEST_GPIO45` / `TEST_GPIO46` — §15, returned for ruling, no scope change taken

Both are MCU test points (`TP1` ↔ `U1.26`, `TP2` ↔ `U1.16`). Neither has been
reclassified or removed.

* **Electrical role**: bring-up/debug access to two spare ESP32-S3 GPIOs. No DM
  demo function depends on them.
* **Required for fabrication?** No. They are not part of the programming path —
  `BOOT_N`, USB and the UART/RootProbe access are all separately routed.
* **Cost to route**: `TEST_GPIO46` closes at **130.826 mm / 296 segments** with
  no release — an unusually long haul for a test point, and it consumes corridor
  that the residual programme needs. `TEST_GPIO45` does not close without
  touching preserve-list copper.
* **Alternative access**: `TP6`, `TP7`, `TP12`, `TP13` and the RootProbe header
  already provide instrumented test access; `U1.16`/`U1.26` are also reachable
  at the module castellations during bring-up.
* **Recommendation for CTO**: accept `TEST_GPIO46` only if its length is
  acceptable, and rule separately on `TEST_GPIO45` — either authorise a
  preserve-list release for it, or accept it as a documented open test point.
  **No decision taken in this pass.**

## 9. Preservation

PCB and DRU byte-identical to `073c898`; `hardware/beta/` empty diff.
`BOOT_N`, `WAKE_INT_N`, the R2 candidate-B escape, I2S, internal I²C, SPI-A,
SPI-B, USB, backlight, buttons, CC1101, every SX1262 control other than the two
authorised scratch-released segments, the RXEN In2/E5 crossing, Edge.Cuts and
the mounting holes are all untouched. No pours. No rule exception.

## 10. What a next pass would need

The corridor is saturated at roughly 18 lanes against 17 demands. Options, in
increasing cost:

1. **More negotiation budget** — 30–50 iterations with layer-biased costs and a
   reserved RXEN lane. Cheapest, but the plateau across 10 iterations at two
   orders is not encouraging.
2. **Give RXEN a different route entirely** — it originates at `U3.19` and its
   destination is the In2 E5 crossing at (27.000, 12.250). A dedicated In2 or
   F.Cu escape avoiding the B.Cu corridor would return two lanes to the J5 set.
   This is the most promising direction and needs no new lock.
3. **Widen the corridor** — the resistor bank `R51`…`R64` pads are their own
   wall, so this means a component move, which is out of scope.
