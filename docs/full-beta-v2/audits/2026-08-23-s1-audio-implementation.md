# FBV2-S1-006 — Full Beta v2 audio: microphone and speaker (Sheet 06)

**Task gate `FBV2-S1-AUDIO` = PASS.**
Date: 2026-08-23 · Scope: `06_audio.kicad_sch`, project-local libraries.
Sheets `07`–`09`, the PCB, mechanical CAD, firmware, Beta-DM and frozen Beta are untouched.

**ERC 45 → 45. Zero added, zero removed. Errors unchanged at 2, both inherited.**
308 components, 0 duplicate references, 0 without a footprint, 0 `*_TBD` nets.
`fork_equivalence.py` PASS, `netclass_probe.py` PASS, PCB still bit-identical to Beta-DM.

---

## 1. The finding that was not on the brief

**`U5` (the MAX98357A) and `J6` (the speaker connector) arrived from Beta-DM marked `DNP`.**

That is not a note anyone wrote down — it is in the inherited file, and it means **the entire
speaker output path has never been populated on any AQROOT board**. `C9` and `C10` are fitted,
so the rail decoupling for an amplifier that is not there was being built.

The brief says *"Voice OUTPUT remains required."* Full Beta v2 is the feature-complete design.
**Both are now `dnp no` and will be fitted.** Everything downstream in this audit — the power
budget, the speaker choice, the EMI provision — describes a path that is being built for the
first time, and should be read that way at bring-up.

This is the third time an inherited `DNP` has turned out to be load-bearing (`U16`/`R49`/`R50`
on sheet 09 at FBV2-S1-005, `U15` and `D2`/`D3` alongside them). **A `DNP` on a Beta-DM sheet
is a statement about the reduced build, not about the architecture**, and each migrated sheet
has to re-decide it rather than inherit it.

---

## 2. Microphone — ICS-43434 out, PUI `DMM-4026-B-I2S-R` in

Source: **PUI Audio `DMM-4026-B-I2S-R` data sheet, Rev A, 5/26/2021**, fetched live from
`api.puiaudio.com` and read in full.

### It is not a drop-in, and the reason matters

| | ICS-43434 | **DMM-4026-B-I2S-R** |
|---|---|---|
| pads | **6** | **7** |
| body | 3.5 × 2.65 × 0.98 mm | **4.00 × 3.00 × 1.00 mm** |
| extra pin | — | **`CONFIG` (pin 2)** — no ICS equivalent |
| land pattern | 2 columns, ring pad 3 | 2 columns 2.15 mm apart, 0.65 mm rows, **ring pad 4** |

**The pin count differs**, so both the symbol and the footprint are new. The brief's
instruction not to reuse the ICS-43434 footprint was right for a stronger reason than size.

### Every pin re-derived from the data sheet

| pin | name | as drawn | data sheet |
|---|---|---|---|
| 1 | `LR` | **GND** | *"When set low, the microphone outputs its signal in the left channel of the I²S frame."* |
| 2 | `CONFIG` | **GND** | *"Pull to ground. The state of this pin is used at power-up."* **Mandatory.** |
| 3 | `VDD` | `+3V3`, `C8` 100 nF | *"Power, 1.62 to 3.63 V. This pin should be decoupled to GND with a 0.1 µF capacitor."* |
| 4 | `GND` | GND | the ring pad around the acoustic port |
| 5 | `WS` | `I2S_LRCLK` | word select |
| 6 | `SCK` | `I2S_BCLK` | serial clock |
| 7 | `SD` | `I2S_MIC_DIN` + **`R120` 100 kΩ to GND** | *"This pin tri-states when not actively driving the appropriate output channel. The SD trace should have a 100 kΩ pull down resistor to discharge the line during the time that all microphones on the bus have tri-stated their outputs."* |

> **`R120` is a data-sheet requirement, not a design preference.** The inherited sheet had no
> pull-down on `I2S_MIC_DIN`. With one microphone the line still tri-states for the entire
> unused half of every frame, so the input floats half the time.

### Supply — and the 1.8 V rail that is not needed

The part is **rated 1.8 V**, and the vendor's own catalogue line reads *"MICROPHONE -26DB
1.8VDC"*. That was the single largest risk in this substitution: a 1.8 V-only microphone would
have forced a new regulator, which the brief explicitly forbids.

**It does not.** The data sheet gives **operating voltage range 1.5 to 3.6 V** and the pin
table gives **1.62 to 3.63 V**. **3.3 V is inside both.** No new rail, no regulator, no level
shifting — `+3V3` and the existing `C8` are the whole supply design.

| parameter | value |
|---|---|
| supply current, normal | **820–1000 µA** |
| supply current, sleep (clock off) | **5 µA** |
| startup, and wake from sleep | **20 ms** |
| sensitivity | **−26 ±1 dBFS** |
| SNR | 64 dB(A) |
| frequency range | 20 Hz – 20 kHz, pass band 18 kHz at Fs = 48 kHz |
| THD | 1 % at 110 dB SPL |
| PSRR | −86 dBFS (100 mV pp at 217 Hz) |
| data format | **I²S 24-bit data, 18-bit precision, 32-bit word** (six null bits) |
| ESD | 8 kV HBM |
| MSL | 1 |

---

## 3. The clock constraint — the brief's suggested rate cannot be run

This is the second finding worth the task on its own.

**The microphone's normal-mode input clock range is 2.048 – 4.096 MHz.** Below **320 kHz** it
drops into sleep mode. The brief proposes an initial firmware contract of *"approximately
16 kHz, 16-bit speech"*. On the wire that gives:

| frame | BCLK | verdict |
|---|---|---|
| 16 kHz × 32 (mono 16-bit) | 0.512 MHz | **out of normal-mode range** |
| 16 kHz × 64 (stereo 32-bit) | 1.024 MHz | **out of normal-mode range** |
| 32 kHz × 64 | 2.048 MHz | at the exact lower limit — legal, no margin |
| **48 kHz × 64** | **3.072 MHz** | **the data sheet's own typical, comfortably mid-range** |

The MAX98357A independently restricts LRCLK: *"LRCLK ONLY supports 8 kHz, 16 kHz, 32 kHz,
44.1 kHz, 48 kHz, 88.2 kHz, and 96 kHz frequencies"* — 48 kHz is on that list, and 3.072 MHz /
48 kHz is literally the amplifier's electrical-characteristics test condition.

> **Ruling: the shared I²S bus runs at 48 kHz with a 64-BCLK frame = 3.072 MHz. Firmware
> decimates to 16 kHz for speech.** 16 kHz remains the right *application* rate; it is simply
> not a legal *wire* rate for this microphone.

**The bus rate is set by the microphone, not by the amplifier or by the application.** Nothing
about this needs hardware — but it would have been found on the bench as "the microphone
sometimes returns silence", which is what sleep mode looks like.

---

## 4. Full duplex — the existing I²S architecture is valid unchanged

| signal | routing | verdict |
|---|---|---|
| `I2S_BCLK` | `U1` GPIO shared with `MK1` `SCK` and `U5` `BCLK` | **shared — correct** |
| `I2S_LRCLK` | shared with `MK1` `WS` and `U5` `LRCLK` | **shared — correct** |
| `I2S_MIC_DIN` | `MK1` `SD` → MCU only | **separate — correct** |
| `I2S_SPK_DOUT` | MCU → `U5` `DIN` only | **separate — correct** |

One ESP32-S3 I²S controller in master full-duplex mode drives both clocks and runs one input
and one output data line. **No pin, net or GPIO changes were needed**, and the GPIO ledger is
unaffected.

Both devices sit on the **left** slot — the microphone drives it on `DIN`, the amplifier reads
it on `DOUT`. Different wires, so there is no contention.

**Audiophile full duplex is not claimed and is not needed.** What is claimed is that the wiring
supports simultaneous capture and playback on one controller, which it does.

---

## 5. Amplifier — MAX98357A retained, with one strap corrected

**Lifecycle: analog.com lists the MAX98357A as `PRODUCTION` with a live 1ku price.** There is
no sourcing reason to move, so it is retained as the brief expects. Orderable MPN
**`MAX98357AETE+T`** — 16-pin TQFN, −40 to +85 °C, tape and reel — which matches the
`TQFN-16-1EP_3x3mm` footprint already in use. `U5` previously carried no MPN at all.

*(The data sheet obtained here is Rev 7; analog.com now offers Rev 16. The electrical content
used below — supply range, gain table, SD_MODE trip points, output power, EMI figure — is
long-standing, but the revision gap is recorded rather than glossed over.)*

### `GAIN_SLOT` was mismatched to the rail — corrected from 12 dB to 6 dB

Gain is referenced to the DAC's full-scale output of **2.1 dBV**:

```
output (dBV) = input (dBFS) + 2.1 dB + gain
```

| `GAIN_SLOT` | gain | 0 dBFS asks for | rail can deliver (3.3 V) | result |
|---|---|---|---|---|
| GND + 100 k | 15 dB | 7.18 Vrms | 2.33 Vrms | clips above −9.8 dBFS |
| **GND (inherited)** | **12 dB** | **5.07 Vrms** | 2.33 Vrms | **clips above −6.8 dBFS** |
| unconnected | 9 dB | 3.59 Vrms | 2.33 Vrms | clips above −3.7 dBFS |
| **VDD (selected)** | **6 dB** | **2.54 Vrms** | 2.33 Vrms | **0 dBFS ≈ the rail** |
| VDD + 100 k | 3 dB | 1.80 Vrms | 2.33 Vrms | 2.2 dB of range wasted |

At 12 dB the top **6.8 dB of the digital range is unusable** — everything above −6.8 dBFS is
clipped by the supply, not by the amplifier. At 6 dB, digital full scale lands on the rail, the
whole range is usable, and the amplifier's own output noise is lower. **Maximum acoustic output
is identical either way, because it is rail-limited, not gain-limited.** This is a one-net
change with no BOM impact.

### `SD_MODE` — the existing drive is exactly right, and needs no extra parts

`SD_MODE` is a multi-level input, not a logic input:

| level | mode |
|---|---|
| > B2 (**1.4 V** typ) | **Left channel** |
| B1…B2 (0.77…1.4 V) | Right channel |
| B0…B1 (0.16…0.77 V) | (Left/2 + Right/2) |
| < B0 (**0.16 V** typ) | **Shutdown** |

A plain push-pull drive from the expander gives **3.3 V = Left** and **0 V = Shutdown** — the
only two states this design uses. `R15` 100 kΩ to GND (sheet 08) holds it in **shutdown through
reset and boot**, which is the safe state the brief requires, and it is also the companion
resistor the data sheet's own Figure 4/5 show.

> **No series resistor is needed on `SD_MODE`.** The data sheet requires ~2 kΩ only when
> `VDD < VDDIO` — its example is *"VDD < 3.0 V and VDDIO = 3.3 V"*. Here **`VDD` and the
> expander's `VCC` are the same `+3V3` net**, so that condition cannot arise. Recorded because
> it is exactly the kind of part that gets added "just in case" and then has to be justified.

### Other amplifier facts captured

| parameter | value |
|---|---|
| supply | 2.5 – 5.5 V (3.3 V in range); UVLO 1.4/1.8/2.3 V |
| quiescent | **2.4 mA** typ at 3.7 V |
| standby (`SD_MODE` high, BCLK stopped) | **340 µA** typ |
| **shutdown (`SD_MODE` low)** | **0.6 µA** typ, 2 µA max |
| turn-on time | 7 ms |
| speaker current limit | 2.8 A typ, outputs disabled ~100 µs then retried |
| modulation | spread spectrum, ±20 kHz around **330 kHz** |
| click-and-pop | internal, unaffected by power sequencing |

**Firmware safety rule, from the data sheet verbatim:** *"Do not remove LRCLK while BCLK is
present. Removing LRCLK while BCLK is present can cause unexpected output behavior, including a
large DC output voltage."* Into an 8 Ω voice coil that is a burnt speaker, so it is recorded on
the sheet as well as here.

---

## 6. Speaker — PUI Audio `AS02008MR-LW152-R`

Verified verbatim from the PUI drawing (`AS02008MR-LW152-R.idw`, released 1/30/2014):

| parameter | value |
|---|---|
| diameter | **Ø20 ± 0.2 mm** |
| depth | **3 ± 0.2 mm** (flange step 1.2 ± 0.2) |
| impedance | **8 Ω ± 15 %** |
| rated / max input | **0.5 W / 0.8 W** |
| sensitivity | **86 ± 3 dBA @ 0.1 W / 0.1 m** (0.8, 1.0, 1.2, 1.5 kHz) |
| distortion max | 5 % |
| resonance | 500 Hz ± 20 % |
| **frequency range** | **500 – 4000 Hz** |
| housing / cone / magnet | metal / Mylar / **Nd-Fe-B** |
| leads | **152 ± 10 mm, UL1571 AWG #32, RED (+) / BLACK (−)** |
| polarity | cone moves forward on a positive voltage at the positive terminal |
| weight / temp | 2.4 g / −20 to +55 °C, RoHS |

**The 500–4000 Hz response is the reason to choose it, not a limitation to apologise for.**
The brief asked for intelligible speech, alerts and moderate handheld volume, and explicitly
*not* music quality or bass. A driver that puts all of its 0.5 W into the speech band is louder
where it matters than a wider-range driver of the same size. PUI's sibling part is described as
*"designed to be as thin as possible and recreate the human voice with good fidelity"*.

Against the brief's targets: **~20 mm ✓, ≤4–5 mm depth (3 mm) ✓, 8 Ω ✓, 0.5–1 W class ✓,
low cost ✓, small ✓, intelligible voice ✓.** It also fits the existing `SPEAKER_ENVELOPE`
(Ø20 × 4.0 mm) with 1 mm of depth to spare.

### `J6` is retained, and the speaker is replaceable without soldering

The existing `J6` **JST `B2B-PH-K-S`**, 2-pin 2.00 mm, is exactly the "small common connector"
the brief allows. The mating side is a **`PHR-2` housing with `SPH-002T-P0.5S` crimp
contacts**. JST's PH data sheet gives the **applicable wire range as AWG #32 to AWG #24**, and
the speaker's leads are **AWG #32** — the small end of the range, but inside it.

> **So the speaker crimps straight into the connector: no soldering to fit it, no soldering to
> replace it.** That is the same serviceability principle already applied to the NFC antenna
> (D-128). AWG #32 at the limit of the crimp range is carried as **B-62** for a first-article
> pull test rather than asserted.

**No complex connector was added.** `J6` was already there and already correct.

---

## 7. Power, thermal and the sane volume ceiling

At `+3V3` into 8 Ω, with a filterless bridge-tied output:

```
rail-limited Vrms      = 3.3 / sqrt(2)      = 2.33 V
peak output power      = 2.33^2 / 8         = 0.68 W
cross-check: data sheet gives 0.93 W into 8 ohm + 68 uH at VDD = 3.7 V, THD+N 10 %
             0.93 x (3.3/3.7)^2             = 0.74 W      -- consistent
input power at 90 % efficiency              = 0.76 W
current from +3V3 at full output            = 230 mA      + 2.4 mA quiescent
```

| condition | output | +3V3 current | vs the 0.5 W rated speaker |
|---|---|---|---|
| 0 dBFS, clipping | 0.68 W | **≈ 230 mA** | above rated, below the 0.8 W max — short alerts only |
| −3 dBFS | 0.34 W | ≈ 115 mA | at the rating |
| **−6 dBFS (recommended default)** | **0.17 W** | **≈ 57 mA** | **comfortably inside** |
| speech at −6 dBFS, 12 dB crest | ~0.011 W average | ~4 mA average | negligible |
| idle, `SD_MODE` high, BCLK stopped | — | 340 µA | — |
| **shutdown, `SD_MODE` low** | — | **0.6 µA** | — |

> **Recommended default maximum software volume: −6 dBFS**, giving 0.17 W and roughly
> **89 dB SPL at 0.1 m** — loud for a handheld — with an absolute ceiling of −3 dBFS for
> alerts. **0 dBFS must not be used continuously**: it exceeds the speaker's rated power even
> though it stays under its maximum.

**Simultaneous radio cases.** 230 mA peak from `+3V3` is real, and the existing **MX-1** rule
already excludes concurrent high-power operations. Voice does not need maximum amplifier output
during radio TX: at −6 dBFS the draw is 57 mA, which sits alongside anything. **No new rule is
proposed** — the existing one plus a volume ceiling covers it.

**Thermal:** 0.68 W out at 90 % efficiency dissipates ~75 mW in the TQFN, against a 1666 mW
package rating. Not a thermal problem at any volume.

---

## 8. EMI — nothing fitted, everything recoverable

The MAX98357A is filterless by design: *"Maxim's active emissions-limiting edge-rate control
circuitry and spread-spectrum modulation reduces EMI emissions while maintaining up to 92 %
efficiency"*, with the switching frequency randomised ±20 kHz around 330 kHz.

**The decisive evidence is the data sheet's own Figure 14: "EMI with 12 in of Speaker Cable and
No Output Filtering."** AQROOT's speaker lead is 152 mm — **half** the cable length in that
measurement — and the brief says not to fit filters unless the data sheet or an EMC analysis
requires them. It does not.

> **First build: `R121` / `R122` fitted as 0 Ω — the speaker path is a plain wire.
> `C81` / `C82` 1 nF are DNP.**

If conducted or radiated emissions ever need taming — AQROOT does carry 433 MHz, 915 MHz, NFC
and a sensitive microphone — the recovery is to replace the 0 Ω with a ferrite bead
(600 Ω @ 100 MHz class) and populate the shunt capacitors. **Four 0603 positions, one pair
populated with 0 Ω, no respin.** A 0603 0 Ω contributes ~50 mΩ, or 15 mV at 300 mA peak against
8 Ω — electrically invisible, and symmetric across the pair.

**PCB requirement carried forward:** `SPK_P` and `SPK_N` must be routed as a **tight,
equal-length differential pair** from `U5` to `J6` regardless of what is fitted. That is the
single most effective EMI control on a filterless Class D output and it costs nothing.

---

## 9. Acoustics and mechanical

### The microphone port geometry, measured from the drawing

§8.3 of the PUI data sheet is a raster drawing. It was rendered and the pads measured
programmatically, calibrated on the printed 0.65 mm row pitch and 2.15 mm column spacing; the
result closes against the printed dimensions to **0.01 mm**:

| feature | value |
|---|---|
| pads | **0.60 × 0.40 mm**, six, two columns |
| column spacing | **2.15 mm** (±1.075 from centre) |
| row pitch | **0.65 mm** |
| pad 4 (GND) | **ring, ID 1.05 / OD 1.65 mm** |
| port centre | on the package **width centreline**, **1.28 mm** from the nearest pad row and **1.00 mm** from the short edge |
| acoustic port in the can | **Ø0.25 ± 0.05 mm** |
| body | 4.00 × 3.00 × 1.00 mm, ±0.10 |

Closure check: 0.23 (edge → pad-1 edge) + 0.20 + 0.65 + 0.65 + 1.28 + 1.00 = **4.01 mm**
against a 4.00 mm body. The geometry is consistent.

### What this means for the enclosure

**It is a bottom-port microphone: sound enters through a hole in the PCB, not past the part.**
So the microphone is soldered to the face of the PCB **opposite** the aperture, and the
acoustic path is:

```
front shell aperture -> gasket -> PCB acoustic hole (1.05 mm) -> mic port (0.25 mm)
```

| requirement | value | change |
|---|---|---|
| PCB acoustic hole | **Ø1.05 mm NPTH**, concentric with pad 4 | was "Ø0.8–1.0 mm" — now the manufacturer's number |
| PCB keepout | no copper, no mask, no component inside **Ø1.65 mm**; **Ø2.5 mm** component keepout on the mic side | new |
| mic mounting face | the face **opposite** the shell aperture | made explicit |
| gasket | closed-cell silicone or poron, compressed 20–30 %, **ID ≥ 1.5 mm, OD 4–5 mm** | ID now bounded by the 1.05 mm hole |
| shell aperture | Ø0.8–1.0 mm, or 3–5 × Ø0.5 mm, acoustic mesh behind | unchanged |
| tunnel length | **≤ 2.5 mm** | unchanged |
| location | front face, bottom third, opposite corner from the speaker | unchanged |
| separation from speaker | **≥ 60 mm**, opposite faces | unchanged — **the Nd-Fe-B magnet must also stay clear of the NFC zone** |

The speaker envelope tightens from *"Ø20 × 4.0 mm or 15 × 11 × 3.5 mm"* to the fitted part:
**Ø20 × 3.0 mm**, which releases 1 mm of Z in the speaker column. The 1.5–2.0 cm³ sealed rear
cavity requirement is unchanged and still matters more than the driver choice.

---

## 10. Feedback and echo — no hardware, and one free lever

**No hardware echo cancellation, as instructed.** What the hardware already gives:

1. **`SD_MODE` is a hardware mute.** Driving it low puts the amplifier in shutdown with the
   outputs high-Z at 0.6 µA. Asserting it while listening removes not just the audio but the
   amplifier's own noise floor and switching residue from the microphone's environment —
   strictly better than a digital mute, and it costs nothing because the net already exists.
2. **≥60 mm separation on opposite faces**, already in the mechanical spec.
3. **A sealed mic tunnel**, which keeps the speaker's rear-cavity energy out of the port.

**Firmware recommendations (not implemented here):**

- **First firmware should be half-duplex**: mute via `SD_MODE`, or attenuate hard, while
  actively listening for a command. This is the simplest thing that works and it needs no DSP.
- Ramp the digital data down before asserting shutdown — the data sheet notes there is no
  volume ramp-down on entering shutdown.
- Software AEC later if barge-in is wanted. The wiring already supports it; nothing here
  prevents it.

---

## 11. Opportunity and simplification scan

| | finding |
|---|---|
| **A. nearly-free capability** | **`SD_MODE` already provides a hardware mute** for half-duplex voice — no new hardware (§10). The microphone's **sleep mode at 5 µA** when BCLK stops below 320 kHz is a free standby saving. |
| **B. removable legacy** | The `8R_SPEAKER_OFFBOARD` / *"SKU finalises with the enclosure"* placeholder is gone. Nothing else on the sheet is legacy. |
| **C. BOM consolidation** | **The microphone and the speaker are now both PUI Audio** — one vendor, one set of distributors, one datasheet source. `R121`/`R122` are 0603 0 Ω, already a project-standard part. |
| **D. unnecessary power rails** | **None, and one was nearly created.** The microphone is *rated* 1.8 V and the catalogue line says "1.8VDC", but its operating range is 1.62–3.63 V, so **no 1.8 V rail is needed** (§2). |
| **E. no-respin provisions** | `R121`/`R122`/`C81`/`C82` EMI positions (§8). `R120` is a requirement, not a provision. |
| **F. sourcing risks** | Microphone **confirmed in live distributor stock** (DigiKey 2 807, Arrow 10 000, three others at 1 250). **Speaker stock not confirmed** — see B-61. |

> **No new item requires CTO or user approval.** Every change made sits inside the brief's own
> instructions: item 2 (replace the microphone), item 5 (*"verify … gain/mode strap"*), item 8
> (EMI recovery footprints) and item 1 (voice output remains required, which is what un-DNP'ing
> `U5`/`J6` delivers). The one thing that would have been a new feature — a second speaker, a
> buzzer, a codec, a headphone jack, an analog chain — is exactly what the brief forbids, and
> none was added.

---

## 12. Blockers

| id | state |
|---|---|
| **B-61** (new) | **`AS02008MR-LW152-R` availability not confirmed from a live listing.** The PUI product page would not render in this environment after three attempts, and Digi-Key search is bot-protected. The **datasheet is served live from PUI's API today**, and the sibling `AS02008MR-R` is catalogued, but D-096 asks for a live listing and this is not one. **OPEN, medium — procurement check before the BOM gate.** |
| **B-62** (new) | **AWG #32 into JST PH `SPH-002T-P0.5S` is the small end of the #32–#24 range.** Inside spec, but a crimp pull test belongs at first article. **OPEN, low.** |
| **B-63** (new) | **The PCB acoustic hole and the pad-4 paste-aperture pullback are not in the footprint.** Ø1.05 mm NPTH concentric with pad 4, and a stencil aperture kept back from the hole edge so solder cannot wick into the port. **OPEN — PCB stage / FBV2-S2.** |
| **B-64** (new) | **The PCB still carries `MK1` with the ICS-43434 footprint.** Part of the standing transitional state — the board is bit-identical to Beta-DM and matches no migrated sheet. Recorded so the microphone change is not lost when the PCB is redone. **OPEN — FBV2-P1.** |
| **B-29 / B-03** | unchanged — footprint audit at FBV2-S2. The new PUI footprint joins that list; its land pattern is derived from the manufacturer drawing, its paste and courtyard policy is not yet audited. |

---

## 13. What was NOT done

No codec, no DAC, no analog microphone amplifier, no 1.8 V rail, no acoustic wake detector, no
separate buzzer, no headphone jack, no second speaker, no hardware echo cancellation, no
alternate footprint, no new GPIO, no change to the I²S net architecture, no firmware.

Sheets `07`–`09` untouched. The PCB is untouched and still bit-identical to Beta-DM.
`hardware/beta-dm/`, `hardware/beta/` and `hardware/beta/mechanical/` are unchanged.

**One probe was extended rather than silenced.** `fork_equivalence.py` asserted that the
`.pretty` directory was bit-identical to Beta-DM's, which stopped being true the moment a
migrated sheet locked a new part. It now asserts that **every inherited footprint is still
bit-identical and none was deleted**, and that **any addition is declared** in an
`ADDED_FOOTPRINTS` table with the task that added it. An undeclared new footprint is still a
probe failure — the check got stricter about what it actually cares about, not looser.
