# Full Beta v2 — six-layer stackup, POFV fabrication note, impedance register

**D-258 (FBV2-P2-002M).** Status: **ARCHITECTURE RULED AND PROVEN ON SCRATCH;
NOT YET APPLIED TO THE AUTHORITATIVE BOARD.** The local six-layer battery gate
(FBV2-P2-002M §14) did not pass, and §16 conditions the authoritative lock on
that gate. See the 002M audit for the two blockers.

---

## 1. The ruling

| item | value |
|---|---|
| manufacturer | JLCPCB |
| copper layers | **6** |
| nominal thickness | **1.6 mm** |
| stackup | **JLC06161H-7628** impedance-control |
| outer copper | 1 oz |
| inner copper | 0.5 oz |
| process | **NO HDI. No blind vias, no buried vias, no laser microvias.** |
| via-in-pad | filled + capped ordinary **THROUGH** via (POFV), **only where explicitly ruled** |

## 2. Layer roles

```
L1  F.Cu     components, critical / high-speed / RF signals, local power
L2  In1.Cu   SOLID GND PLANE
L3  In2.Cu   internal signals + slow power distribution
L4  In3.Cu   internal signals + slow power distribution
L5  In4.Cu   SOLID GND PLANE
L6  B.Cu     components, local signals, battery / high-current copper
```

**Neither GND plane is ever split into power islands.** The only authorised
void remains the ESP32 antenna keepout, which is a manufacturer requirement and
overrides plane continuity locally on every layer.

**High-current battery copper stays on 1 oz OUTER copper.** At 0.5 oz an inner
layer needs 2.73 mm for 1.5 A at a 10 K rise — the board's own `.kicad_dru`
arithmetic — which defeats the purpose of moving it there. The board already
carries `BAT_MAIN is outer-layer only`, and 002M's router now honours it by
construction: `connect_hop` offers the new internal layers to control nets and
never to a wide net.

## 3. Stackup geometry as authored

```
F.SilkS
F.Paste
F.Mask        0.0100
F.Cu          0.0350      1 oz
prepreg 7628  0.2104      <- outer dielectric, same as JLC04161H-7628
In1.Cu        0.0152      0.5 oz   GND
core FR4      0.2000
In2.Cu        0.0152      0.5 oz   signal
prepreg 7628  0.6312      (3 plies)
In3.Cu        0.0152      0.5 oz   signal
core FR4      0.2000
In4.Cu        0.0152      0.5 oz   GND
prepreg 7628  0.2104      <- outer dielectric
B.Cu          0.0350      1 oz
B.Mask        0.0100
B.Paste
B.SilkS
                          TOTAL 1.6028 mm
```

**The outer 0.2104 mm figure is carried over from the four-layer design and is
the one number this stack shares with it.** The INNER distribution above is
**DERIVED** so the stack totals 1.6 mm at 1 oz outer / 0.5 oz inner. It is
recorded as a derivation and **must be confirmed against JLCPCB's published
JLC06161H-7628 table before Gerbers are ordered.** Do not quote it as
manufacturer data.

---

## 4. POFV — the Q3.3 via-in-pad fabrication note

**THIS IS A PROCESS ORDER, NOT A GEOMETRY.** Gerbers alone do not force a
fabricator to select it, and a via inside a pad that is merely tented,
mask-plugged or left open **wicks solder out of the joint**.

| field | value |
|---|---|
| component / pad | **Q3 pin 3** (`Q3_CS`), `Package_SO:SOIC-8_3.9x4.9mm_P1.27mm` |
| pad size | 1.950 × 0.600 mm |
| via type | **ordinary THROUGH via** (L1–L6) |
| via diameter | **0.35 mm** |
| drill | **0.20 mm** |
| pad copper remaining | **0.125 mm each side** across the pad width |
| required process | **PLATED OVER FILLED VIA — resin-filled, capped and plated, planarised** |
| NOT acceptable | tented via · soldermask-plugged via · open via · blind or buried via · laser microvia |

**Why this pad and no other.** FBV2-P2-002L measured `Q3.3` as having **no legal
escape at 0.25, 0.20 or 0.15 mm**, blocked by `Q3.2` and `Q3.4` — its own
neighbours on a row where `Q3_CS` owns pins 1/3 and `LTC_GATE` owns pins 2/4
across a single B.Cu slot. Both D-257 via geometries failed identically, and
they had to: a via needs a landing site, a landing site must be **reached** from
the pad, and no via size helps a pad that cannot emit copper at all.

Six layers alone do **not** fix this — `Q3.3` still has no B.Cu escape from
which to reach an external via. The POFV is what closes it, and it is applied to
**one pad**. `Q3.1` keeps an ordinary external via: it has four escape
directions and does not need a premium process.

Measured on scratch: `Q3_CS Q3.3 → Q3.1` routes **4.626 mm at 0.25 mm on
In2.Cu**, two 0.35/0.20 vias, and `LTC_GATE Q3.2 → Q3.4` gets the B.Cu slot back
at **5.500 mm with zero vias** — the right answer for a MOSFET gate drive and
the reason one premium via is worth buying.

---

## 5. Impedance impact register

**No impedance-sensitive net was routed in 002M.** The four-layer widths must
not be carried over on the assumption that a similar outer prepreg means an
unchanged impedance: the reference distance is only one of the inputs, and the
return-path layer changes for anything that used In2 as a reference.

| net / class | old reference | new intended reference | recalculation |
|---|---|---|---|
| **USB D+/D−** (`USB_D`, 0.25 mm, 0.55/0.25 vias) | F.Cu over In1.Cu, 0.2104 mm; In2 excursion already forbidden | F.Cu over In1.Cu, 0.2104 mm — unchanged pairing | **YES** — differential pair, must be re-solved against the six-layer dielectric constants even though the geometry looks identical |
| **915 MHz feed** (`NFC_RF` / RF controls, 0.4 mm) | F.Cu over In1.Cu | F.Cu over In1.Cu | **YES** — 50 Ω single-ended; re-solve |
| **433 MHz controlled traces** | outer over In1.Cu | outer over In1.Cu | **YES** if any length is controlled; confirm which arms are |
| **NFC transmit arms** (`NFC_RF`, via-prohibited by rule) | B.Cu over In1.Cu across the full 4-layer core | **B.Cu over In4.Cu, 0.2104 mm** — a much closer reference than before | **YES** — this is the biggest change in the table; the tuning network assumptions must be re-derived |
| **NFC_RX / NFC_OSC** | outer over In1.Cu | outer over nearest plane | **YES** where tuning-sensitive |
| **Display / high-speed SPI** (`LED_BOOST`, SPI groups) | outer over In1.Cu | outer over nearest plane | **YES** for any pair declared controlled; none is today |
| `SWITCH_NODE` | outer only, never In2 | outer only, never In2 **or In3** | **NO** — not impedance-controlled; the rule is extended, not recalculated |

**Structural check (002M §3): the migration does not invalidate the USB, RF or
display PLANNING assumptions.** Every one of those blocks keeps an outer layer
against a solid plane at the same 0.2104 mm, which is the property the plans
depend on. What changes is the numeric width, and that is what this register
schedules. The NFC transmit arms are the exception worth flagging: their
reference moves from the far side of a 1.065 mm core to In4 at 0.2104 mm, which
is a real electrical change and not a width tweak.
