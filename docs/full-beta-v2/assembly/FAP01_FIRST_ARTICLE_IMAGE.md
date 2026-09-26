# FAP-01 — the first-article diagnostic image

**D-801 / `D801-01` (Round-20 Astra `R20-01`).**  Prerequisite `FAP-01` of the
first-article plan (`FIRST_FIVE_ASSEMBLY_PLAN.md` §7d, register
`RELEASE_ACCEPTANCE_REGISTER.json` → `first_article_prerequisites`).

**D-802 (Round-21 `R21-01`..`R21-03`).**  `N` writes and reads back the
ST25R3916's 3.3 V supply mode (`sup3V`) before its regulators are enabled;
`W` is an EXCLUSIVE session for its whole life; `T` reports an answer only
from fresh, validated receive evidence.  §3, §5 and §6 carry the details.

**D-803 (Round-22 `D803-01`, `D803-05`).**  `T` trusts a verdict only from a
`U9` proved live on both sides of every piece of evidence, and every receive /
FIFO error outranks "no tag"; an `H` / `J` hold-off is recorded for the next
FAP-01 boot of ANY kind, so `Q` (`NVS confirmed clear`) comes before power-off
or reflash unless persistence is being tested.

> **NEVER SHIP THIS IMAGE.  IT IS NEVER A DEFAULT.**  It is built and flashed
> only by name, on the bench, for the first-article steps listed below, and the
> board is re-flashed with the release image (`[env:aqroot-demo]`) before it
> leaves the bench.  `checks/firmware_hw_map_contract.py` **H9** refuses any
> `platformio.ini` whose `default_envs` is not exactly and solely `aqroot-demo`
> (including `aqroot-demo-fap01` as, or beside, the default), and **H10**
> refuses the FAP-01 define or `src/fap01/` in any environment but its own.

## 1. What it is

| | |
|---|---|
| PlatformIO environment | **`aqroot-demo-fap01`** (`Firmware/platformio.ini`, `extends = env:aqroot-demo`) |
| define | `AQROOT_FAP01_DIAGNOSTIC` — in this environment ONLY |
| sources | the release `Firmware/src/demo/` + `Firmware/src/hw/`, **plus** `Firmware/src/fap01/` (`aqroot_fap01.h`, `aqroot_fap01.cpp`) |
| libraries | Arduino-ESP32 core only (its bundled `WiFi`, `Preferences`, `SPI`, I2S driver); no external library, like the release image |
| release rules | **unchanged** — the same `setup()` / `loop()`, console keys, D-792 permission table, burst arbiter, quiesce, NFC liveness schedule and gauge load epoch.  H6 re-runs the whole release-image host test (`test_production_image.cpp`) on this build. |

`src/fap01/` refuses to compile without the define (`#error`), every hook in
`src/demo/main.cpp` is inside `#if defined(AQROOT_FAP01_DIAGNOSTIC)`, and the
release `build_src_filter` (`-<*> +<demo/> +<hw/>`) never selects it; the
legacy filter excludes it explicitly (`-<fap01/>`).  The release image with
every FAP-01 key typed into it does nothing (`test_fap01_image.cpp`, release
build, H6).

## 2. Build, flash, and record the source identity

From a CLEAN checkout of the commit being used (the tree must be clean — a
dirty tree has no SHA that describes it):

```sh
git status --porcelain            # must print nothing
git rev-parse HEAD                # RECORD: FAP-01 source SHA
cd Firmware
pio project config --json-output  # confirm: "default_envs": ["aqroot-demo"]
pio run -e aqroot-demo-fap01      # build BY NAME
sha256sum .pio/build/aqroot-demo-fap01/firmware.bin     # RECORD
pio run -e aqroot-demo-fap01 -t upload                  # flash BY NAME
pio device monitor -b 115200      # console: the ESP32-S3 native USB CDC
```

Never run a bare `pio run -t upload` to flash FAP-01: the bare command builds
and uploads the release image only (`default_envs = aqroot-demo`), which is the
intended protection.  After the first-article session, restore the release
image **by name**: `pio run -e aqroot-demo -t upload`.

**Source identity of record** (filled in when the first-article image is cut;
the toolchain is `platform = espressif32@6.9.0`, Arduino-ESP32 2.0.x):

| field | value |
|---|---|
| FAP-01 git SHA (`git rev-parse HEAD`, clean tree) | the D-803 content commit, recorded in `hardware/demo/manufacturing/evidence/d803-review-target.json` (`fap01_image.git_sha`) |
| `firmware.bin` sha256 (`.pio/build/aqroot-demo-fap01/firmware.bin`) | the clean release build of that commit, recorded in the same file (`fap01_image.firmware_bin_sha256`); re-hash the file actually flashed on each unit |
| release image flashed back afterwards, sha256 | `<RECORD PER UNIT>` |

The binary is not claimed to be bit-reproducible across build machines; the
hash recorded is the hash of the file actually flashed, and the SHA is the
source it was built from.

**On the bench, confirm the image before any step.**  The boot console prints,
right after `board_sha256`:

```
FAP-01 FIRST-ARTICLE DIAGNOSTIC IMAGE -- NEVER SHIP, NEVER A DEFAULT
```

If that line is absent, the board is running the release image and none of the
keys below exist.

## 3. The console

FAP-01's keys are **upper case**; the release keys (`r g b w o 3 5 i s d l x t p m`)
work exactly as in the release image.  One key per stimulus; the same key again
stops it; **`Q` stops every FAP-01 stimulus at once**; `?` prints the list.
Every keyed state also stops **on its own** at the bound below (enforced from
the top of every `loop()`; a blocking release test such as a rail admission can
delay the stop by its own length, a few seconds at most, and never removes it).

| key | stimulus | bound | keyed only through / refused when | on stop | serves |
|---|---|---|---|---|---|
| `C` | CC1101 (`U7`) continuous TX, 433.92 MHz, random-TX PN9, PATABLE `0xC0` (module max +10 dBm); keyed state confirmed from MARCSTATE `0x13` | 30 s | `SpiBusB::beginTransmit` — refused while any transmitter or field is keyed, while the radio state is UNKNOWN, or when the D-792 table refuses sub-GHz TX (any accessory rail live) | release quiesce `cc1101Quiesce` (SIDLE/SRES, MARCSTATE `0x01`); if not confirmed the radio state is left UNKNOWN for the quiesce retry | `C-RADIO-QUIESCE-01`, `C-MCU-01` |
| `L` | SX1262 (`U8`) CW, 915.000 MHz, +22 dBm (TCXO on DIO3 at 2.2 V, DIO2 RF switch, `RXEN` left at its safe 0); keyed state confirmed from GetStatus chip mode TX | 30 s | `SpiBusB::beginTransmit`, as `C` | release quiesce `sx1262Quiesce` (SetStandby, STANDBY confirmed) | `C-RADIO-QUIESCE-01` (SX1262 case), `C-MCU-01` |
| `N` | ST25R3916 (`U9`) field ON.  FIRST the supply mode: IO configuration register 2 (`01h`) bit 7 `sup3V` = 1 — `U9`'s VDD is `+3V3` through `R106` (FITTED) with `R107` and `U13` DNP, and DS12484 Rev 3 §4.2.11 / Table 20 make the 5 V mode the power-up and Set-default state — written and READ BACK before `en` and Adjust regulators, and read back again once the field is up; then Operation control `0xC8` (`en`, `rx_en`, `tx_en`), ISO14443A default mode, read back.  If `sup3V` does not read back, the field is refused and no regulator is enabled. | 60 s | `DemoBringupApp::beginNfcFieldSession` — refused unless the field is confirmed off by a live part, no accessory rail is live, the burst slot and the SPI-B transmit slot are free; the liveness probe stands down for the session (D796-10) | Operation control `0x00`, session ended; the field is UNKNOWN until the release quiesce retry re-proves it off | `C-NFC-TUNE-01`, `C-NFC-QUIESCE-01` |
| `T` | one ISO14443A REQA while `N` is on — **report only** (receiver on power-up defaults).  Three verdicts.  **D-803: every piece of evidence has a PROVABLY LIVE `U9` on both sides of it** — the IC identity (`ic_type` 00101b), a 5Ah / A5h challenge on No-response timer 2 read back and restored to its 00h default, and the identity again — taken FIVE times: before the REQA, across the IRQ / FIFO clear, at the fresh boundary, after the REQA and ATQA read, and at the end, so a `U9` that stops answering at any byte (and stays dead) or fails for a few bytes and RECOVERS never yields a verdict it did not earn.  `VALID ANSWER: a tag answered, ATQA xx xx` only when the field and `sup3V` read back, the main / timer / error IRQs were cleared and Clear FIFO sent with a live part, the boundary then read main IRQ, error IRQ and FIFO status all 0, the REQA raised `I_txe` and `I_rxe`, exactly two whole bytes arrived, the FIFO drained, the FINAL FIFO status and IRQs read 0 (nothing arrived the verdict did not see), and the ATQA passes ISO/IEC 14443-3 6.3.2 (exactly one anticollision bit b1..b5, RFU bits clear — `00 00` and `FF FF` fail); `no tag answered` only with the same proof, `I_txe`, no `I_rxs` / `I_rxe`, no error and an empty FIFO.  **Every error outranks both verdicts:** `I_col`, `I_rxs` without `I_rxe`, a CRC / parity / framing error, `fifo_ovr` / `fifo_unf` or an incomplete last byte is `NO VALID EVIDENCE: <reason>` — never `no tag answered` — as are an all-ones or all-zero bus, an ignored command, a stale FIFO or IRQ, a failed transfer and a `U9` that is not answering live — neither an answer nor its absence | one frame | refused without a field, and refused while a `U9` chip-select hold-off (`J`/`K`/`Y`) is armed or pending; a transaction the hold-off interrupts is `NO VALID EVIDENCE` | — | `C-NFC-TUNE-01` tag read (RECORD) |
| `V` | operator **declares the bench source**: no charger — the console cable blocks VBUS and the board runs from the pack or a bench supply at the pack terminals.  The firmware cannot verify it (D-776). | valid 120 s | — | expires | precondition of `W` |
| `W` | Wi-Fi TX burst: raw broadcast probe requests back-to-back at 19.5 dBm, modem sleep off | 10 s, then a 30 s cool-down | asks the release `wifiActivationPermitted()` (the table's Wi-Fi row) and prints its refusal; waives **only** the no-rail CHARGING-row refusal (D-797 / D797-02), and only after `V`, with **both rails off**, no sub-GHz transmitter or NFC field keyed, both confirmed off, amplifier off, no burst, and **no FAP-01 state held or armed** (no held audio or backlight, no chip-select hold-off).  A rail-live Wi-Fi refusal is **never** waived.  **The session is EXCLUSIVE for its whole life (D-802):** while it runs every key is refused — `I`, `x`, `d`, `p`, `m`, `t`, `l`, `3`, `5`, `i`, `A`, `B`, `C`, `L`, `N`, `T`, `G`, `H`/`J`/`K`/`Y`, the RGB keys, `V` — except `W` and `Q` (which stop it), `?` and `s`.  The exclusion ends the moment the session stops (`W`, `Q`, its 10 s bound or a reset); the cool-down gates only another `W`.  The Wi-Fi mode is also told to the table (`noteWifiRadioActive`). | radio OFF, mode cleared | `C-MCU-01` (total while transmitting) |
| `I` | ten 38 kHz NEC frames from `D1` (address `0x00`, command `0x5A`), 50 % carrier duty, ~1.1 s; reports how often `U6` read low | ~1.1 s | the release `x` gates: both rails off, and the burst slot (`BurstLoad::IrTransmit`) — refused while U9 owns it | carrier 0, LEDC detached, `IR_TX` LOW | `C-IR-01` |
| `H` | chip-select hold-off on `U7` `CC1101_CS_N`: the pin is held HIGH while `SpiBusB` believes it selected the part.  Also **recorded in NVS for the NEXT FAP-01 boot of ANY kind** — an `EN` pulse, a **power cycle**, or the first FAP-01 boot after a reflash (D-803).  **Press `Q` and see `NVS confirmed clear` before powering off or reflashing, unless you are intentionally testing persistence.** | 60 s (also 60 s from the boot that restores it) | — | released; the release quiesce retry and probes re-prove the part | `C-RADIO-QUIESCE-01` (held-off case) |
| `J` | chip-select hold-off on `U9` `NFC_CS_N`, immediate; recorded for the next FAP-01 boot of any kind like `H` (`Q` before power-off / reflash) | 60 s | — | released, as `H` | `C-NFC-QUIESCE-01` (UNKNOWN case, idle lift) |
| `K` | `U9` hold-off that begins **700 ms** after the key — press `K` then `3` and it lands inside the first-rail admission's 1300 ms gauge window | 60 s once active | — | as `J` | `C-NFC-QUIESCE-01` (lift during the gauge window) |
| `Y` | `U9` hold-off that begins **2000 ms** after the key — press `Y` then `3` and it lands in the settled recheck after the grant | 60 s once active | — | as `J` | `C-NFC-QUIESCE-01` (lift during the settled recheck) |
| `A` | held audio: the release tone (1 kHz square, amplitude 6000, both slots) held through I2S | 30 min | the release `setAmplifierIntent(true)` — the D-792 mode edge; refused with a rail live (audio has no mode-edge row with a rail live).  Enable the rails AFTER `A` (the rail-edge audio row). While held, `t` and `m` are refused. | I2S uninstalled, amplifier back in shutdown (confirmed, or retried) | `C-THERM-01` |
| `B` | held backlight PWM duty 128/255 (50 %) after the D-784 full-duty prime (255 for 3000 µs first) | 30 min | — (the backlight is in the always-on load); while held, `l` and `p` are refused | duty 0, LEDC detached, `DISP_BL_PWM` LOW | `Q11-TEMP-01`, `C-THERM-01` |
| `G` | raw `VCELL` (MAX17048 register `0x02`) every 10 ms for 2 s, one line each: `vcell t_ms=<ms> raw=0x<hex> V=<volts>`; the start line gives the absolute `millis()`; an all-ones or all-zero register is marked `IMPLAUSIBLE ... not a sample` and counted in the END line (D-802) | 2 s | both rails off (the release blocking-test rule); the NFC liveness schedule is kept between samples | — | `C-GAUGE-EPOCH-01` (register cadence) |
| `Q` | stop every FAP-01 stimulus, release every hold-off and erase the hold-off record, READ BACK: `FAP-01: no hold-off is recorded for the next FAP-01 boot (NVS confirmed clear) -- safe to power off or reflash` (otherwise `NOT CONFIRMED CLEAR -- do not power off or reflash; press Q again`) | — | — | — | all |
| `?` | print the key list | — | — | — | — |

Every keyed state stamps the gauge load epoch (through the release method it
keys, or directly for the held backlight and the field), so a rail admitted
after it is judged on a post-load conversion.

## 4. The first-article steps, key by key

* **`C-RADIO-QUIESCE-01`** — `C`, confirm the carrier on the analyser, then an
  `EN` pulse.  The FAP-01 image reboots through the release boot path; the
  quiesce line is `[PASS] radios quiesced after MCU reset (U7 SRES/SIDLE, U8
  SetStandby, U9 Set default) CC1101 MARCSTATE=0x01 (IDLE), ...`.  Repeat with
  `L`.  Held-off case: `C`, then `H`, then the `EN` pulse — the boot prints
  `FAP-01: chip-select hold-off RESTORED across the reset on U7 CC1101_CS_N`,
  the quiesce reports `(NOT IDLE)`, and `3` / `5` print `ACCESSORY REFUSED: the
  physical transmit state of U7/U8 is UNKNOWN`.  After 60 s (or `H`) the
  hold-off ends and the loop's retry stops the carrier.  (This is the step that
  tests persistence on purpose; in every other step press `Q` — `NVS confirmed
  clear` — before powering off or reflashing.)
* **`C-NFC-QUIESCE-01`** — `N`, then an `EN` pulse: the boot prints `FIELD OFF,
  live identity`.  UNKNOWN case: `J` (then optionally an `EN` pulse; the
  hold-off is restored at boot): `FIELD STATE UNKNOWN` / `NFC OFF confirmation
  REVOKED`, the rail keys refused by name, `d` and `I`/`x` refused with `U9
  owns the burst slot`; `J` again releases and the loop recovers.  Latency with
  a rail live: `3`, then `J` (idle lift), `K` then `3` (inside the gauge
  window), `Y` then `3` (inside the settled recheck) — record the time from the
  lift to the shed against the 820 ms `kNfcRevocationDeadlineMs`.
* **`C-NFC-TUNE-01`** — `N` for the full-drive field (60 s per key press; press
  again to re-key); confirm the `N` line reads `IO configuration 2 0x80: sup3V`;
  scope `VDD_TX`/`VDD_RF` and `+3V3`; `T` for a REQA at 0 / 10 / 30 mm (report
  only — see §6).  Record the verdict word as printed: only `VALID ANSWER` is a
  tag read; `NO VALID EVIDENCE` is a bench fault to investigate, not "no tag".
* **`C-IR-01`** — `I` with the enclosure closed, watching `TP40` and the `R24`
  drop at `TP39`; the console also reports how often `U6` read low during the
  unit's own marks.
* **`C-MCU-01`** — baseline with nothing keyed; transmitting totals with `W`
  (after `V`; Wi-Fi at 19.5 dBm; nothing else can be keyed until it stops), and
  with `C` / `L` for the sub-GHz modules.
* **`C-THERM-01`** — `p` (display up; it leaves the backlight at full on, the
  "full brightness" the step names — do not press `B`, which holds 50 %), then
  `A`, then `3` and `5` (the declared simultaneous pair is the accessory load,
  applied externally; the rails must come AFTER `A`).  The audio hold ends at
  30 min; re-key it (rails off first) to continue a longer soak.
* **`Q11-TEMP-01`** — `l` (the release ramp, with its prime) and `B` (a held
  duty after the prime), at each soak temperature; `B` again / `Q` for OFF,
  then `B` for the ON→OFF→ON restart.
* **`C-GAUGE-EPOCH-01`** — the `p`/`3` timing runs on either image; the register
  cadence is `G` immediately after the controlled 200 mV supply step.

## 5. Safety preconditions — what FAP-01 never waives

* No sub-GHz transmitter is keyed except through `SpiBusB::beginTransmit`, and
  therefore never with an accessory rail live, never beside another
  transmitter or the NFC field, and never while the radio state is UNKNOWN.
* The NFC field is turned on only through `beginNfcFieldSession`: a confirmed-
  off, liveness-proved part, no rail live, the burst slot — and only after the
  3.3 V supply mode (`sup3V`) the fitted `R106` / DNP `R107` population gives
  `U9` has been written and read back (D-802).  The supply mode comes from the
  generated `AQROOT_NFC_ON_3V3`, which the generator derives from that
  population and refuses to emit for any other.
* The one release refusal FAP-01 waives is the Wi-Fi **charging** row with no
  rail live, after the operator's bench declaration, for 10 s at most with a
  30 s cool-down, with nothing else keyed — at the start AND for the whole
  session, because every other key is refused until it stops (D-802).  Wi-Fi
  with a rail live is never permitted.  None of it exists in the release image.
* Audio is energised only through the release mode edge; IR only through the
  release blocking-test rule and burst arbiter; the held backlight duty only
  after the D-784 prime.
* Every stimulus is bounded (table above) and stoppable (`Q`); on stop the
  sub-GHz parts are quiesced by the release quiesce, and anything that cannot
  be confirmed is left UNKNOWN for the release quiesce retry.
* A chip-select hold-off is a fault injection: while it is active the release
  image correctly treats the part as UNKNOWN and refuses rails and bursts.  It
  is bounded to 60 s and is carried into at most ONE next FAP-01 boot — of
  any kind, a power cycle included; `Q` (`NVS confirmed clear`) before
  power-off or reflash unless persistence is being tested.

## 6. Limitations carried openly

* **Register values from datasheets not archived here.**  The CC1101 continuous-
  TX configuration (TI SWRS061 / SmartRF values for 433.92 MHz) and the SX1262
  CW command sequence (Semtech DS.SX1261-2) are not backed by a document in this
  repository; the Ebyte module manuals are (`vendor/Ebyte/`: DIO3 TCXO at 2.2 V,
  DIO2 RF switch, 26 MHz crystal).  Each keyed state is confirmed from the part's
  own status register and refused otherwise, and the bench confirms the carrier
  — which is what the steps measure anyway.  A wrong value shows as a refused
  key, never as an unbounded or unquiesced transmitter.
* **`T` (REQA) is report only.**  The ST25R3916 receiver runs on its power-up
  defaults, not an application stack's analog configuration; a tag that does not
  answer `T` is RECORDED, not failed, and the tag read of `C-NFC-TUNE-01` falls
  back to an application ST25R3916 stack if the defaults are insufficient.  The
  legacy PN532/I2C driver (`Firmware/src/drivers/nfc.cpp`) is the WRONG PART and
  is never a fallback: FAP-01 compiles `src/demo/`, `src/hw/` and `src/fap01/`
  only, with no PN532 dependency (H10).  An answer is claimed only from the
  evidence listed in §3 (D-802, D-803): D-801 printed "a tag answered" for any
  FIFO count of two or more, so an all-ones bus or a stale FIFO read as a tag;
  D-802 still trusted a `U9` that stopped answering late or failed for a few
  bytes and recovered, and reported a receive error without `I_rxe` as "no
  tag".
* **"The capped level" is the release tone.**  No firmware constant anywhere
  defines an audio cap; the ledger's 120 mA line is a declared estimate.  `A`
  holds the release tone (`kAudioCappedAmplitude = 6000`); `C-THERM-01` records
  the current it draws.  If the owner defines a different cap, it changes in
  `src/fap01/aqroot_fap01.h`.
* **The bench declaration (`V`) is the operator's.**  The firmware cannot see
  VBUS (D-776).
* **Hold-off across a reset uses NVS** (`Preferences`, namespace
  `aqroot-fap01`): written only while an immediate hold-off is active, erased on
  release, at its bound, by `Q`, and by the first FAP-01 boot that reads it — so
  it is carried into exactly ONE next FAP-01 boot, of ANY kind: an `EN` pulse, a
  **power cycle**, or the first FAP-01 boot after a reflash (NVS survives all
  three; the release image never reads the record, so it waits).  **Operator
  rule (D-803 / D803-05): press `Q` and see `NVS confirmed clear` before
  powering off or reflashing — EXCEPT when persistence is the thing being
  tested** (the held-off steps in §4, which press `H` / `J` and then pulse `EN`
  on purpose).  A board powered off with a hold-off armed boots its next FAP-01
  image with that select held high for 60 s.

## 7. Host proof

`python3 hardware/demo/manufacturing/checks/firmware_hw_map_contract.py`

* **H6** — `Firmware/test/test_fap01_image.cpp` on the FAP-01 build (every
  stimulus above reachable, gated, bounded, quiesced; 47 destructive controls,
  each caught by the claim it names — ten of them D-803's REQA controls (the
  end-only liveness shape among them), four D-803 hold-off-record controls, and
  13 D-802's: no `sup3V` before the
  regulators, the 5 V mode on this board, the read-back dropped, the BOM
  population flipped under the same image, the Wi-Fi session exclusive only at
  its start or not requiring a quiet board, Clear FIFO not sent or not proved,
  no `I_txe`, no ATQA plausibility, an armed hold-off not refusing, a failed
  transfer not invalid, an all-ones `VCELL` printed as a sample) and on the
  release build (every FAP-01 key inert; the
  define-and-sources leak control caught), plus the whole
  `test_production_image.cpp` on the FAP-01 build.  The host board model judges
  every `en` write and Adjust regulators command against the supply the FAB BOM
  populates (`R106` FIT / `R107` DNP), passed in by H6 independently of the
  image's own constant.
* **H9** — `default_envs` is exactly and solely `aqroot-demo` (parsed, and
  REQUIRED cross-check with `pio project config --json-output`, PlatformIO found
  by the configured path then `pio` / `platformio` on PATH — unavailable is a
  FAIL, D-803); ten destructive controls (missing, legacy, mixed, multi-line,
  FAP-01 as or beside the default, `extra_configs`, a named environment
  removed, a duplicated conflicting and a duplicated identical default) and
  17 end-to-end portability controls (absent tool, PATH-only `pio` /
  `platformio`, a disagreeing PlatformIO, each bad form with and without it).
* **H10** — FAP-01 isolation: only `[env:aqroot-demo-fap01]` compiles
  `src/fap01/` or defines `AQROOT_FAP01_DIAGNOSTIC`; the release `main.cpp`
  preprocesses to no FAP-01 token; `src/fap01/` refuses to compile alone; the
  FAP-01 environment compiles nothing outside `demo/`, `hw/`, `fap01/` and has
  no PN532 dependency, and `src/fap01/` never calls the legacy PN532 driver
  (D-802); and the hold-off operator wording is bound to the documents
  (D-803); fourteen destructive controls.
* **Generator controls** — `AQROOT_NFC_ON_3V3` refuses to emit for `R106` DNP +
  `R107` FIT, `R106` DNP alone, `R107` FIT beside `R106`, or `U13` FIT (four
  controls in the contract's `controls` list).
