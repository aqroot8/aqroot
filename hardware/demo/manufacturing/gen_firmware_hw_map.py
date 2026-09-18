#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AQROOT Demo -- GENERATE THE FIRMWARE HARDWARE MAP FROM THE BOARD ITSELF.

WHY THIS EXISTS.  `docs/full-beta-v2/AQROOT_DEMO_EXPANDER_DEPENDENCIES.md`
records, in its own words, what a stale pin map costs: D-732 found that reading
the superseded table would have masked `4Ah` bit 6 -- believed to be
`BQ25185_STAT2`, in fact `TOUCH_INT_N` -- silencing the touch interrupt while
leaving a second input free to wake the MCU forever.  That table was corrected
by hand.  A hand-corrected table drifts again.

So the firmware's hardware definition is not written.  It is GENERATED, pin by
pin, out of `aqroot-Beta-v2.kicad_pcb` and the `RF_Module:ESP32-S3-WROOM-1`
symbol cached inside `aqroot-Beta-v2.kicad_sch`, and
`checks/firmware_hw_map_contract.py` re-runs this generator and fails if the
committed header is not byte-identical to what the board says today.

WHAT IS *NOT* IN THE BOARD.  Direction, active level, safe boot latch value,
interrupt mask and internal-pull policy are ENGINEERING INTENT, not copper.
They live in `MCU_POLICY` / `EXPANDER_POLICY` below.  The generator refuses to
emit unless every policy row is corroborated by the board:

  * the row's net is on the exact pad the row claims, and
  * every OUTPUT's safe latch level equals the level its EXTERNAL PULL
    establishes while the expander is still high-impedance, or carries an
    explicit `safe_basis` naming why there is no pull, and
  * every UNMASKED INPUT has a defined idle level -- an external pull, an
    internal pull, or a named push-pull driver, and
  * every pad of every expander and of `U1` is accounted for: no bit is
    silently absent from the map.

    python3 hardware/demo/manufacturing/gen_firmware_hw_map.py [--check]
"""

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

import pcbnew

ROOT = Path(__file__).resolve().parents[3]
PROJECT = ROOT / "hardware/demo/kicad/aqroot-demo"
BOARD = PROJECT / "aqroot-Beta-v2.kicad_pcb"
SCHEMATIC = PROJECT / "aqroot-Beta-v2.kicad_sch"
MCU_SHEET = PROJECT / "02_mcu_core.kicad_sch"
OUT_H = ROOT / "Firmware/src/hw/aqroot_demo_board.h"
OUT_JSON = ROOT / "Firmware/src/hw/aqroot_demo_board.json"

POWER_NETS = {"GND", "+3V3"}

# ---------------------------------------------------------------------------
# THE FOUR MODULE PADS WHOSE SYMBOL NAME IS NOT ITS GPIO NUMBER.
#
# Everything else in the cached `RF_Module:ESP32-S3-WROOM-1` symbol names its
# own GPIO (`IO4`, `IO45`, ...).  These four name the FUNCTION Espressif
# silkscreens on the module, and the GPIO behind each is fixed silicon.  Three
# of the four are corroborated by this board's own net names -- `RXD0` carries
# `/IR_RX_GPIO44`, and `USB_D-`/`USB_D+` carry `/USB_D_MCU_N`/`_P`, which are
# the ESP32-S3's native USB pins and exist nowhere else on the die.
MODULE_PIN_ALIASES = {
    "USB_D-": ("IO19", "native USB D- (USB Serial/JTAG)"),
    "USB_D+": ("IO20", "native USB D+ (USB Serial/JTAG)"),
    "RXD0":   ("IO44", "UART0 RX"),
    "TXD0":   ("IO43", "UART0 TX"),
}

# ---------------------------------------------------------------------------
# MCU POLICY -- keyed by the module pad number on `U1`.
#
# `role`     the C identifier the firmware uses
# `kind`     PIN | STRAP | BUS | FIXED | NC
# `net`      the net the board MUST carry on that pad
# `note`     why firmware has to care
MCU_POLICY = {
    3:  dict(role=None, kind="FIXED", net="Net-(U1-EN)",
             note="module EN / reset; RC only, no firmware access"),
    4:  dict(role="SPI_B_SCK", kind="BUS", net="/SPI_B_SCK",
             note="shared SPI-B: CC1101 + SX1262 + ST25R3916"),
    5:  dict(role="SPI_B_MOSI", kind="BUS", net="/SPI_B_MOSI", note="shared SPI-B"),
    6:  dict(role="SPI_B_MISO", kind="BUS", net="/SPI_B_MISO", note="shared SPI-B"),
    7:  dict(role="CC1101_CS_N", kind="PIN", net="/CC1101_CS_N",
             note="433 MHz E07 chip select, active low"),
    8:  dict(role="CC1101_GDO0", kind="PIN", net="/CC1101_GDO0",
             note="433 MHz packet/sync interrupt; GDO2 is NOT wired on this board"),
    9:  dict(role="IR_TX", kind="PIN", net="/IR_TX_GPIO16",
             note="drives Q1 gate through R22 100R; R23 100k gate pull-down; ACTIVE HIGH"),
    10: dict(role="SX1262_CS_N", kind="PIN", net="/SX1262_CS_N",
             note="915 MHz E22 chip select, active low"),
    11: dict(role="NFC_IRQ", kind="PIN", net="/NFC_IRQ",
             note="ST25R3916 IRQ, push-pull, ACTIVE HIGH; no external pull"),
    12: dict(role="SX1262_BUSY", kind="PIN", net="/SX1262_BUSY",
             note="SX1262 BUSY; must be low before any command"),
    13: dict(role=None, kind="FIXED", net="/USB_D_MCU_N",
             note="native USB D-, 22R series; owned by the USB Serial/JTAG peripheral"),
    14: dict(role=None, kind="FIXED", net="/USB_D_MCU_P",
             note="native USB D+, 22R series; owned by the USB Serial/JTAG peripheral"),
    15: dict(role="BMI270_INT1", kind="STRAP", net="/BMI270_INT1_STRAP",
             strap_level=0, strap_part="R110", strap_why=(
                 "GPIO3 is the JTAG-source strap.  R110 10k to GND holds it low "
                 "through reset; R18 220R isolates the BMI270 INT1 driver so the "
                 "IMU cannot fight the strap at boot"),
             note="BMI270 INT1, push-pull from the IMU, ACTIVE HIGH"),
    16: dict(role="DISP_BL_PWM", kind="STRAP", net="/02_MCU_CORE/DISP_BL_CTL_STRAP",
             strap_level=0, strap_part="R108", strap_why=(
                 "GPIO46 must be LOW at reset.  R108 10k to GND does that AND "
                 "leaves the backlight boost U17 disabled until firmware drives it"),
             note="U17 TPS61169 WLED boost enable / PWM brightness through R109 0R"),
    17: dict(role="NFC_CS_N", kind="PIN", net="/NFC_CS_N",
             note="ST25R3916 chip select, active low"),
    18: dict(role="DISP_CS_N", kind="PIN", net="/DISP_CS_N",
             note="display chip select, active low"),
    19: dict(role="SPI_A_MOSI", kind="BUS", net="/SPI_A_MOSI",
             note="shared SPI-A: display + microSD"),
    20: dict(role="SPI_A_SCK", kind="BUS", net="/SPI_A_SCK", note="shared SPI-A"),
    21: dict(role="SPI_A_MISO", kind="BUS", net="/SPI_A_MISO",
             note="shared SPI-A -- reaches the microSD ONLY.  R112 0R is DNP, so the "
                  "display SDO is ISOLATED and the panel CANNOT be read back"),
    22: dict(role="DISP_DC", kind="PIN", net="/DISP_DC",
             note="display data/command"),
    23: dict(role="WAKE_INT_N", kind="PIN", net="/WAKE_INT_N",
             note="shared open-drain wake line: U2./INT, U3./INT and the accessory "
                  "attention path through Q10.  R3 10k pull-up.  LEVEL sensitive, "
                  "ACTIVE LOW, RTC-capable for deep-sleep wake"),
    24: dict(role="NATIVE_B", kind="PIN", net="/NATIVE_B",
             note="Community Port native GPIO B, J5.8 through R62 100R, D2 ESD"),
    25: dict(role="SD_CS_N", kind="PIN", net="/SD_CS_N",
             note="microSD chip select, active low"),
    26: dict(role=None, kind="STRAP", net="/02_MCU_CORE/GPIO45_VDDSPI_STRAP",
             strap_level=0, strap_part="R111", strap_why=(
                 "GPIO45 selects VDD_SPI.  R111 10k to GND is the ONLY load besides "
                 "TP1.  Firmware must never claim this pin"),
             note="VDD_SPI strap -- NOT A FIRMWARE PIN"),
    27: dict(role="BOOT_N", kind="STRAP", net="/02_MCU_CORE/BOOT_N",
             strap_level=1, strap_part="R2", strap_why=(
                 "GPIO0 download strap.  R2 10k to +3V3; SW1 pulls it to GND"),
             note="recessed BOOT/recovery button SW1; readable as a user button "
                  "after boot, ACTIVE LOW"),
    28: dict(role=None, kind="NC", net=None,
             note="IO35 -- octal PSRAM, unusable, left NC"),
    29: dict(role=None, kind="NC", net=None,
             note="IO36 -- octal PSRAM, unusable, left NC"),
    30: dict(role=None, kind="NC", net=None,
             note="IO37 -- octal PSRAM, unusable, left NC"),
    31: dict(role="NATIVE_A", kind="PIN", net="/NATIVE_A",
             note="Community Port native GPIO A, J5.7 through R61 100R, D2 ESD"),
    32: dict(role="I2S_BCLK", kind="BUS", net="/I2S_BCLK",
             note="shared I2S bit clock: MAX98357A out + DMM-4026 mic in"),
    33: dict(role="I2S_LRCLK", kind="BUS", net="/I2S_LRCLK", note="shared I2S word clock"),
    34: dict(role="I2S_SPK_DOUT", kind="PIN", net="/I2S_SPK_DOUT",
             note="I2S data to the MAX98357A"),
    35: dict(role="I2S_MIC_DIN", kind="PIN", net="/I2S_MIC_DIN",
             note="I2S data from the DMM-4026-B-I2S MEMS microphone"),
    36: dict(role="IR_RX", kind="PIN", net="/IR_RX_GPIO44",
             note="TSOP38238 demodulated output, ACTIVE LOW, internally pulled up; "
                  "Vs fed through R21 100R + C11"),
    37: dict(role="UART0_TXD", kind="FIXED", net="/02_MCU_CORE/UART0_TXD_DBG",
             note="debug UART TX to TP35 only -- there is NO USB-UART bridge; the "
                  "console is the native USB CDC"),
    38: dict(role="I2C_SCL", kind="BUS", net="/I2C_SCL_INT",
             note="internal I2C clock, R20 2.2k pull-up"),
    39: dict(role="I2C_SDA", kind="BUS", net="/I2C_SDA_INT",
             note="internal I2C data, R19 2.2k pull-up"),
}

# ---------------------------------------------------------------------------
# EXPANDER POLICY.  Bit -> pad on the PCAL9535APW is fixed silicon:
# pins 4..11 = P00..P07, pins 13..20 = P10..P17.
#
# `safe`       the value written into the OUTPUT latch BEFORE the direction bit
#              is cleared.  SLVSFJ2B-class parts and the PCAL9535A alike power
#              up as INPUTS with the latch at 0x00, so setting direction first
#              would glitch anything whose safe level is 1.
# `safe_basis` external_pull  -- an external resistor already holds this level
#                                while the expander is high-Z, and the contract
#                                CHECKS that the resistor exists and points the
#                                right way
#              load_off       -- there is no pull; the level that leaves the
#                                LOAD de-energised is named here instead
# `irq`        UNMASKED | MASKED   (PCAL9535A 4Ah/4Bh; reset value is all-masked)
# `pull`       NONE | UP | DOWN    (PCAL9535A 46h..49h internal 100k)
EXPANDER_BIT_PAD = {}
for _i in range(8):
    EXPANDER_BIT_PAD["P0%d" % _i] = 4 + _i
    EXPANDER_BIT_PAD["P1%d" % _i] = 13 + _i

EXPANDER_POLICY = {
    "U2": {
        "addr_strap": {"A0": 21, "A1": 2, "A2": 3},
        "role": "internal controls, front buttons and internal status inputs",
        "bits": {
            "P00": dict(role="TOUCH_RST_N", net="/TOUCH_RST_N", dir="OUT",
                        active="LOW", safe=0, safe_basis="external_pull",
                        pull="NONE", irq="MASKED",
                        note="capacitive touch controller reset, through J1.47.  "
                             "R12 100k to GND holds the panel in reset until "
                             "firmware releases it"),
            "P01": dict(role="SX1262_RST_N", net="/SX1262_RST_N", dir="OUT",
                        active="LOW", safe=0, safe_basis="external_pull",
                        pull="NONE", irq="MASKED",
                        note="E22/SX1262 reset.  R13 100k to GND holds the LoRa "
                             "module in reset at boot"),
            "P02": dict(role="NFC_5V_EN", net="/NFC_5V_EN", dir="OUT",
                        active="HIGH", safe=0, safe_basis="external_pull",
                        pull="NONE", irq="MASKED", hold_safe=True,
                        note="U13 NFC 5 V boost enable.  U13 IS DNP ON DEMO -- NFC "
                             "runs from +3V3 through R106 0R -- so R14 100k to GND "
                             "is the ONLY thing defining this node and firmware must "
                             "never assert it"),
            "P03": dict(role="AMP_SD_MODE", net="/AMP_SD_MODE", dir="OUT",
                        active="HIGH", safe=0, safe_basis="external_pull",
                        pull="NONE", irq="MASKED",
                        note="MAX98357A SD_MODE.  R15 100k to GND = amplifier SHUT "
                             "DOWN at boot.  Driven to +3V3 the part leaves shutdown "
                             "and selects a SINGLE I2S slot (MAX98357A Table 1 top "
                             "band); write the mono sample into BOTH slots so the "
                             "channel decision cannot silence the speaker"),
            "P04": dict(role="DISP_RST_N", net="/DISP_RST_N", dir="OUT",
                        active="LOW", safe=0, safe_basis="external_pull",
                        pull="NONE", irq="MASKED",
                        note="display reset, through J1.10.  R16 100k to GND holds "
                             "the panel in reset at boot"),
            "P05": dict(role="SX1262_DIO1", net="/SX1262_DIO1", dir="IN",
                        active="HIGH", pull="NONE", idle_basis="push_pull_driver",
                        irq="UNMASKED",
                        note="LoRa interrupt, ROUTED at D-740 (U2.9 -> U8.13).  The "
                             "SX1262 drives DIO1 PUSH-PULL, so the internal 100k "
                             "must stay OFF -- a pull only fights it.  The driver "
                             "takes the interrupt and does NOT poll GetIrqStatus()"),
            "P06": dict(role="TOUCH_INT_N", net="/TOUCH_INT_N", dir="IN",
                        active="LOW", pull="UP", idle_basis="internal_pull",
                        irq="UNMASKED",
                        note="touch interrupt through J1.46.  NOTHING ON THIS BOARD "
                             "pulls this net -- the only other pad is the display "
                             "FPC -- so the internal 100k pull-up is REQUIRED: with "
                             "the panel unplugged an unmasked floating input would "
                             "hold the shared wake line and starve the buttons"),
            "P07": dict(role="SD_CARD_DETECT_N", net="/SD_CARD_DETECT_N", dir="IN",
                        active="LOW", pull="NONE", idle_basis="external_pull",
                        irq="UNMASKED",
                        note="microSD card detect, R113 100k pull-up"),
            "P10": dict(role="BTN_A_N", net="/08_BUTTONS_EXPANDERS/BTN_A_N", dir="IN",
                        active="LOW", pull="NONE", idle_basis="external_pull",
                        irq="UNMASKED", note="A / Select, SW6, R4 10k pull-up"),
            "P11": dict(role="BTN_UP_N", net="/08_BUTTONS_EXPANDERS/BTN_UP_N", dir="IN",
                        active="LOW", pull="NONE", idle_basis="external_pull",
                        irq="UNMASKED", note="D-pad Up, R5 10k pull-up"),
            "P12": dict(role="BTN_DOWN_N", net="/08_BUTTONS_EXPANDERS/BTN_DOWN_N",
                        dir="IN", active="LOW", pull="NONE",
                        idle_basis="external_pull", irq="UNMASKED",
                        note="D-pad Down, R6 10k pull-up"),
            "P13": dict(role="BTN_LEFT_N", net="/08_BUTTONS_EXPANDERS/BTN_LEFT_N",
                        dir="IN", active="LOW", pull="NONE",
                        idle_basis="external_pull", irq="UNMASKED",
                        note="D-pad Left, R7 10k pull-up"),
            "P14": dict(role="BTN_RIGHT_N", net="/08_BUTTONS_EXPANDERS/BTN_RIGHT_N",
                        dir="IN", active="LOW", pull="NONE",
                        idle_basis="external_pull", irq="UNMASKED",
                        note="D-pad Right, R8 10k pull-up"),
            "P15": dict(role="BTN_B_N", net="/08_BUTTONS_EXPANDERS/BTN_B_N", dir="IN",
                        active="LOW", pull="NONE", idle_basis="external_pull",
                        irq="UNMASKED", note="B / Back, SW7, R9 10k pull-up"),
            "P16": dict(role="BQ25185_STAT2", net="/BQ25185_STAT2", dir="IN",
                        active="LOW", pull="NONE", idle_basis="external_pull",
                        irq="MASKED", carries_information=False,
                        note="charger STAT2.  U2.19 is routed to R128/TP7 and reads a "
                             "static HIGH, but U11.3 SHIPS UNCONNECTED by owner "
                             "decision D-742 -- the charger never drives it, so the "
                             "bit carries NO INFORMATION.  MASKED, and firmware must "
                             "not decode it"),
            "P17": dict(role="ACC_PWR_EN", net="/ACC_PWR_EN", dir="OUT",
                        active="HIGH", safe=0, safe_basis="external_pull",
                        pull="NONE", irq="MASKED",
                        note="U16 TCA4307 Community-Port I2C buffer enable.  R17 100k "
                             "to GND keeps the accessory bus isolated at boot"),
        },
    },
    "U3": {
        "addr_strap": {"A0": 21, "A1": 2, "A2": 3},
        "role": "front RGB, accessory power tree and the two public XGPIO",
        "bits": {
            "P00": dict(role="FRONT_RGB_R_N", net="/08_BUTTONS_EXPANDERS/FRONT_RGB_R_N",
                        dir="OUT", active="LOW", safe=1, safe_basis="load_off",
                        pull="NONE", irq="MASKED",
                        note="D13 red cathode through R124 1k; anode is +3V3, so the "
                             "LED is dark at 1 and dark again while the expander is "
                             "high-Z"),
            "P01": dict(role="FRONT_RGB_G_N", net="/08_BUTTONS_EXPANDERS/FRONT_RGB_G_N",
                        dir="OUT", active="LOW", safe=1, safe_basis="load_off",
                        pull="NONE", irq="MASKED",
                        note="D13 green cathode through R125 680R"),
            "P02": dict(role="FRONT_RGB_B_N", net="/08_BUTTONS_EXPANDERS/FRONT_RGB_B_N",
                        dir="OUT", active="LOW", safe=1, safe_basis="load_off",
                        pull="NONE", irq="MASKED",
                        note="D13 blue cathode through R126 390R"),
            "P03": dict(role="ACC_5V_SW_EN", net="/ACC_5V_SW_EN", dir="OUT",
                        active="HIGH", safe=0, safe_basis="external_pull",
                        pull="NONE", irq="MASKED",
                        note="U22 TPS22950C 5 V accessory load-switch ON.  D-186 makes "
                             "R131 100k to GND MANDATORY: the TPS22950C's internal "
                             "500k smart pull-down is not sufficient on its own and "
                             "the PCAL powers up high-impedance.  This is the SECOND "
                             "of D-186's two independent series disconnects; the "
                             "first is ACC_5V_BOOST_EN on U3.P13"),
            "P04": dict(role="XGPIO4", net="/XGPIO4", dir="IN",
                        active="HIGH", pull="UP", idle_basis="internal_pull",
                        irq="MASKED",
                        note="public Community-Port expansion GPIO, J5.13 through "
                             "R55 100R, D4 ESD.  Boots as an INPUT with the internal "
                             "100k pull-up so an empty header reads a defined 1.  "
                             "MASKED is MX-9: an accessory must not be able to hold "
                             "the shared wake line and starve the buttons"),
            "P05": dict(role="XGPIO5", net="/XGPIO5", dir="IN",
                        active="HIGH", pull="UP", idle_basis="internal_pull",
                        irq="MASKED",
                        note="public Community-Port expansion GPIO, J5.14 through "
                             "R56 100R, D4 ESD.  See XGPIO4"),
            "P06": dict(role="SPARE_U3_P06", net=None, dir="IN", active="HIGH",
                        pull="UP", idle_basis="internal_pull", irq="MASKED",
                        note="NC-DEMO spare.  No external part at all, so the internal "
                             "pull-up is what keeps a CMOS input from floating"),
            "P07": dict(role="SPARE_U3_P07", net=None, dir="IN", active="HIGH",
                        pull="UP", idle_basis="internal_pull", irq="MASKED",
                        note="NC-DEMO spare -- see SPARE_U3_P06"),
            "P10": dict(role="SPARE_U3_P10", net=None, dir="IN", active="HIGH",
                        pull="UP", idle_basis="internal_pull", irq="MASKED",
                        note="NC-DEMO spare -- see SPARE_U3_P06"),
            "P11": dict(role="SPARE_U3_P11", net=None, dir="IN", active="HIGH",
                        pull="UP", idle_basis="internal_pull", irq="MASKED",
                        note="NC-DEMO spare -- see SPARE_U3_P06"),
            "P12": dict(role="ACC_3V3_EN", net="/ACC_3V3_EN", dir="OUT",
                        active="HIGH", safe=0, safe_basis="external_pull",
                        pull="NONE", irq="MASKED",
                        note="U20 TPS22950C switched 3.3 V accessory rail ON.  "
                             "R98 100k to GND"),
            "P13": dict(role="ACC_5V_BOOST_EN", net="/ACC_5V_BOOST_EN", dir="OUT",
                        active="HIGH", safe=0, safe_basis="external_pull",
                        pull="NONE", irq="MASKED",
                        note="U21 TPS61023 5 V accessory boost ON.  R102 100k to GND "
                             "is MANDATORY per D-186.  FIRST of the two independent "
                             "series disconnects; ACC_5V_SW_EN is the second, and the "
                             "5 V rail requires BOTH"),
            "P14": dict(role="ACC_DETECT_N", net="/ACC_DETECT_N", dir="IN",
                        active="LOW", pull="NONE", idle_basis="external_pull",
                        irq="UNMASKED",
                        note="accessory present at J5.21, R129 100k pull-up, R64 100R "
                             "series, D5 ESD"),
            "P15": dict(role="ACC_POWER_FAULT_N", net="/ACC_POWER_FAULT_N", dir="IN",
                        active="LOW", pull="NONE", idle_basis="external_pull",
                        irq="UNMASKED",
                        note="wire-OR fault flag from U20 and U22, R103 100k pull-up.  "
                             "A fault here must drop BOTH accessory enables"),
            "P16": dict(role="SX1262_RXEN", net="/SX1262_RXEN", dir="OUT",
                        active="HIGH", safe=0, safe_basis="external_pull",
                        pull="NONE", irq="MASKED",
                        note="E22 RF receive-path enable, R74 100k to GND.  TXEN is "
                             "NOT an MCU pin: U8.7/U8.8 are driven by the SX1262's own "
                             "DIO2, so firmware must enable DIO2-as-RF-switch"),
            "P17": dict(role="BQ25185_STAT1", net="/BQ25185_STAT1", dir="IN",
                        active="LOW", pull="NONE", idle_basis="external_pull",
                        irq="MASKED",
                        note="charger STAT1, R127 10k pull-up.  SLUSF65B Table 6-2: "
                             "LOW = CHARGER FAULT, DIRECTLY OBSERVED.  HIGH is "
                             "AMBIGUOUS between charging and complete because STAT2 "
                             "is unconnected.  MASKED and POLLED rather than wired to "
                             "the wake line: STAT1 only moves on fault entry/exit, and "
                             "the board carries no NTC (R38 10k to GND is SLUSF65B's "
                             "own 'TS function not required' network), so there is no "
                             "temperature-boundary source of chatter to wake on"),
        },
    },
}

# ---------------------------------------------------------------------------
# FIXED-FUNCTION FACTS the firmware cannot discover but must not get wrong.
# Each carries the board evidence the contract re-checks.
I2C_DEVICES = [
    dict(role="EXPANDER_U2", addr=None, ref="U2", note="PCAL9535A, internal controls"),
    dict(role="EXPANDER_U3", addr=None, ref="U3", note="PCAL9535A, accessory + RGB"),
    dict(role="FUEL_GAUGE", addr=0x36, ref="U14",
         note="MAX17048G+T10.  ALRT (U14.5) reaches TP11 ONLY -- it is NOT wired to "
              "the MCU or to either expander, so the gauge must be POLLED"),
    dict(role="IMU", addr=0x68, ref="U4",
         note="BMI270.  R118 0R to GND is FITTED and R119 is DNP, so SDO is low and "
              "the address is 0x68.  INT1 arrives on GPIO3 through R18 220R"),
    dict(role="TOUCH", addr=0x38, ref="J1",
         note="FT6236-family on the display FPC.  INT on U2.P06, RST on U2.P00"),
]


def board_sha256():
    return hashlib.sha256(BOARD.read_bytes()).hexdigest()


def module_pin_names():
    """pad number -> the name the cached WROOM-1 symbol gives it."""
    txt = MCU_SHEET.read_text(encoding="utf-8")
    start = txt.index('(symbol "RF_Module:ESP32-S3-WROOM-1"')
    depth = 0
    for stop in range(start, len(txt)):
        if txt[stop] == "(":
            depth += 1
        elif txt[stop] == ")":
            depth -= 1
            if depth == 0:
                break
    block = txt[start:stop + 1]
    names = {}
    for name, number in re.findall(
            r'\(name\s+"([^"]*)"\s*\(effects.*?\(number\s+"([^"]*)"', block, re.S):
        names.setdefault(number, name)
    return names


_BOARD_CACHE = None
_FITTED_CACHE = None


def load_board():
    """Pad/value tables for the whole board.  Cached: `build()` is called once
    per non-vacuity control and `LoadBoard` is the expensive part."""
    global _BOARD_CACHE
    if _BOARD_CACHE is not None:
        return _BOARD_CACHE
    board = pcbnew.LoadBoard(str(BOARD))
    pads = {}          # ref -> {pad number -> netname}
    values = {}        # ref -> value
    for footprint in board.GetFootprints():
        ref = footprint.GetReference()
        values[ref] = footprint.GetValue()
        table = pads.setdefault(ref, {})
        for pad in footprint.Pads():
            number = pad.GetNumber()
            if number:
                table.setdefault(number, pad.GetNetname())
    _BOARD_CACHE = (pads, values)
    return _BOARD_CACHE


def net_members(pads):
    members = {}
    for ref, table in pads.items():
        for number, net in table.items():
            if net:
                members.setdefault(net, set()).add("%s.%s" % (ref, number))
    return members


def external_pull(net, pads, values, fitted):
    """The rail an external FITTED two-pad resistor ties `net` to, if any."""
    if not net:
        return None
    for ref, table in pads.items():
        if not re.fullmatch(r"R\d+", ref) or ref not in fitted:
            continue
        nets = {number: value for number, value in table.items() if value}
        if len(nets) != 2:
            continue
        rails = [value for value in nets.values() if value in POWER_NETS]
        others = [value for value in nets.values() if value == net]
        if len(rails) == 1 and others:
            return dict(part=ref, value=values.get(ref, ""),
                        rail=rails[0], level=1 if rails[0] == "+3V3" else 0)
    return None


def fitted_refs():
    """(fitted, dnp) from the schematic's own DNP field.  Cached -- the export
    shells out to `kicad-cli`."""
    global _FITTED_CACHE
    if _FITTED_CACHE is None:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import routing_ledger
        _FITTED_CACHE = routing_ledger.schematic_population()
    return _FITTED_CACHE


def pcal_address(ref, pads):
    """0x20 | A0 | A1<<1 | A2<<2, read off the strap pads."""
    strap = EXPANDER_POLICY[ref]["addr_strap"]
    addr = 0x20
    detail = {}
    for name, pad in strap.items():
        net = pads[ref][str(pad)]
        if net == "+3V3":
            bit = 1
        elif net == "GND":
            bit = 0
        else:
            raise SystemExit("%s.%s (%s) is neither +3V3 nor GND: %r"
                             % (ref, pad, name, net))
        detail[name] = dict(pad=pad, net=net, bit=bit)
        addr |= bit << {"A0": 0, "A1": 1, "A2": 2}[name]
    return addr, detail


def build():
    pads, values = load_board()
    fitted, dnp = fitted_refs()
    names = module_pin_names()
    members = net_members(pads)
    problems = []

    # ---- U1 -------------------------------------------------------------
    mcu = []
    u1 = pads["U1"]
    for pad in sorted(int(n) for n in u1 if n.isdigit()):
        net = u1[str(pad)]
        if net in POWER_NETS:
            continue
        policy = MCU_POLICY.get(pad)
        if policy is None:
            problems.append("U1.%d carries %r and has no policy row" % (pad, net))
            continue
        want = policy["net"]
        have = None if net.startswith("unconnected-") else net
        if want != have:
            problems.append("U1.%d: policy says %r, board says %r" % (pad, want, have))
            continue
        symbol = names.get(str(pad), "?")
        gpio_name, alias_note = MODULE_PIN_ALIASES.get(symbol, (symbol, None))
        match = re.fullmatch(r"IO(\d+)", gpio_name)
        gpio = int(match.group(1)) if match else None
        row = dict(pad=pad, symbol=symbol, gpio=gpio, net=have,
                   role=policy["role"], kind=policy["kind"], note=policy["note"])
        if alias_note:
            row["alias_note"] = alias_note
        for key in ("strap_level", "strap_part", "strap_why"):
            if key in policy:
                row[key] = policy[key]
        if policy["kind"] == "STRAP":
            pull = external_pull(have, pads, values, fitted)
            if pull is None:
                problems.append("U1.%d %s is a STRAP with no fitted external pull"
                                % (pad, policy["role"]))
            elif pull["level"] != policy["strap_level"]:
                problems.append(
                    "U1.%d %s straps to %d but %s ties it to %s"
                    % (pad, policy["role"], policy["strap_level"], pull["part"],
                       pull["rail"]))
            elif pull["part"] != policy["strap_part"]:
                problems.append("U1.%d strap part is %s, policy names %s"
                                % (pad, pull["part"], policy["strap_part"]))
            else:
                row["strap_pull"] = pull
        mcu.append(row)

    # A role is a C identifier: two rows sharing one emits a duplicate #define
    # and the second silently wins.  A GPIO is derived from the pad, so the
    # collision that can actually happen is on the NAME.
    seen_gpio, seen_role = {}, {}
    for row in mcu:
        if row["gpio"] is None or row["role"] is None:
            continue
        if row["gpio"] in seen_gpio:
            problems.append("GPIO%d claimed by both %s and %s"
                            % (row["gpio"], seen_gpio[row["gpio"]], row["role"]))
        seen_gpio[row["gpio"]] = row["role"]
        if row["role"] in seen_role:
            problems.append("role %s claimed by both U1.%d and U1.%d"
                            % (row["role"], seen_role[row["role"]], row["pad"]))
        seen_role[row["role"]] = row["pad"]

    # ---- expanders ------------------------------------------------------
    expanders = {}
    for ref in ("U2", "U3"):
        spec = EXPANDER_POLICY[ref]
        addr, strap_detail = pcal_address(ref, pads)
        if ref not in fitted:
            problems.append("%s is not fitted" % ref)
        bits = []
        for bit in sorted(EXPANDER_BIT_PAD, key=lambda b: EXPANDER_BIT_PAD[b]):
            pad = EXPANDER_BIT_PAD[bit]
            net = pads[ref][str(pad)]
            row_policy = spec["bits"].get(bit)
            if row_policy is None:
                problems.append("%s %s (pad %d) has no policy row" % (ref, bit, pad))
                continue
            have = None if net.startswith("unconnected-") else net
            if row_policy["net"] != have:
                problems.append("%s %s (pad %d): policy says %r, board says %r"
                                % (ref, bit, pad, row_policy["net"], have))
                continue
            row = dict(bit=bit, pad=pad, net=have, role=row_policy["role"],
                       dir=row_policy["dir"], active=row_policy["active"],
                       pull=row_policy["pull"], irq=row_policy["irq"],
                       note=row_policy["note"])
            if "carries_information" in row_policy:
                row["carries_information"] = row_policy["carries_information"]
            if row_policy.get("hold_safe"):
                row["hold_safe"] = True
            pull = external_pull(have, pads, values, fitted)
            if pull:
                row["external_pull"] = pull
            if row_policy["dir"] == "OUT":
                row["safe"] = row_policy["safe"]
                row["safe_basis"] = row_policy["safe_basis"]
                if row_policy["safe_basis"] == "external_pull":
                    if pull is None:
                        problems.append(
                            "%s %s %s claims safe_basis=external_pull with no fitted "
                            "external pull" % (ref, bit, row_policy["role"]))
                    elif pull["level"] != row_policy["safe"]:
                        problems.append(
                            "%s %s %s safe latch is %d but %s ties the net to %s"
                            % (ref, bit, row_policy["role"], row_policy["safe"],
                               pull["part"], pull["rail"]))
                elif row_policy["safe_basis"] == "load_off":
                    if pull is not None:
                        problems.append(
                            "%s %s %s claims safe_basis=load_off but %s pulls it to %s"
                            % (ref, bit, row_policy["role"], pull["part"], pull["rail"]))
                else:
                    problems.append("%s %s unknown safe_basis %r"
                                    % (ref, bit, row_policy["safe_basis"]))
                if row_policy["pull"] != "NONE":
                    problems.append("%s %s is an OUTPUT with internal pull %s"
                                    % (ref, bit, row_policy["pull"]))
            else:
                row["idle_basis"] = row_policy["idle_basis"]
                basis = row_policy["idle_basis"]
                if basis == "external_pull" and pull is None:
                    problems.append("%s %s %s claims an external pull it does not have"
                                    % (ref, bit, row_policy["role"]))
                if basis == "internal_pull" and row_policy["pull"] == "NONE":
                    problems.append("%s %s %s claims an internal pull but pull is NONE"
                                    % (ref, bit, row_policy["role"]))
                if basis == "internal_pull" and pull is not None:
                    problems.append(
                        "%s %s %s enables an internal pull against external %s"
                        % (ref, bit, row_policy["role"], pull["part"]))
                if basis == "push_pull_driver" and row_policy["pull"] != "NONE":
                    problems.append("%s %s %s must not pull against a push-pull driver"
                                    % (ref, bit, row_policy["role"]))
                if row_policy["irq"] == "UNMASKED" and basis not in (
                        "external_pull", "internal_pull", "push_pull_driver"):
                    problems.append("%s %s is UNMASKED with an undefined idle level"
                                    % (ref, bit))
            bits.append(row)
        expanders[ref] = dict(ref=ref, addr=addr, addr_strap=strap_detail,
                              role=spec["role"], bits=bits)

    # ---- fixed facts ----------------------------------------------------
    devices = []
    for entry in I2C_DEVICES:
        row = dict(entry)
        if row["addr"] is None:
            row["addr"] = expanders[row["ref"]]["addr"]
        devices.append(row)

    limits = [
        dict(key="CHARGER_STAT2_UNCONNECTED", value=True,
             evidence="U11.3 carries /BQ25185_STAT2 and is UNROUTED "
                      "(owner decision 2026-09-17, D-742)",
             firmware="STAT1 LOW is a directly observed charger fault.  STAT1 HIGH is "
                      "AMBIGUOUS.  Any charging-versus-complete claim must be labelled "
                      "an INFERENCE from VBUS presence plus the MAX17048 trend."),
        dict(key="DISPLAY_SDO_ISOLATED", value=True,
             evidence="R112 0R is DNP, so /03_SPI_A_DISPLAY_SD/DISP_SDO never reaches "
                      "/SPI_A_MISO",
             firmware="The panel is WRITE-ONLY.  Never read back a display register; "
                      "SPI-A MISO belongs to the microSD alone."),
        dict(key="FUEL_GAUGE_ALRT_NOT_WIRED", value=True,
             evidence="/01_POWER_TREE/MAX17048_ALRT_N reaches TP11 and U14.5 only",
             firmware="Poll the MAX17048.  There is no alert interrupt path."),
        dict(key="ACC_BUS_READY_NOT_WIRED", value=True,
             evidence="/09_COMMUNITY_HEADER/TCA4307_READY reaches TP44 and U16.5 only",
             firmware="The accessory-bus READY flag is a bench probe, not a readable "
                      "signal.  Confirm the accessory bus by addressing it."),
        dict(key="NFC_ON_3V3", value=True,
             evidence="R106 0R FIT ties /NFC_SUPPLY to +3V3; R107 and U13 are DNP",
             firmware="NFC runs from the 3.3 V path.  Never assert NFC_5V_EN."),
        dict(key="SX1262_TXEN_IS_DIO2", value=True,
             evidence="U8.7/U8.8 carry /04_SPI_B_RADIOS_NFC/DIO2_TXEN, which no MCU or "
                      "expander pin touches",
             firmware="Configure the SX1262 to drive DIO2 as the RF switch; only RXEN "
                      "is under firmware control (U3.P16)."),
        dict(key="CC1101_GDO2_NOT_WIRED", value=True,
             evidence="only /CC1101_GDO0 leaves U7 to the MCU",
             firmware="Route every CC1101 status assertion through GDO0."),
        dict(key="I2S_CLOCKS_ARE_SHARED", value=True,
             evidence="MK1.6 and U5.16 both sit on /I2S_BCLK, and MK1.5 and U5.14 both "
                      "sit on /I2S_LRCLK -- one clock pair, two devices",
             firmware="ONE I2S peripheral must own BCLK and LRCLK.  Running a second "
                      "controller as a master on the same pins puts two drivers on "
                      "each clock.  Use full-duplex master (TX to U5, RX from MK1) in "
                      "the application, or one direction at a time in bring-up."),
        dict(key="SHARED_SPI_B_ONE_TX", value=True,
             evidence="U7, U8 and U9 share /SPI_B_SCK, /SPI_B_MOSI and /SPI_B_MISO",
             firmware="One transceiver transmits at a time; deselect the other two "
                      "before any transmit."),
        dict(key="NO_BATTERY_NTC", value=True,
             evidence="U11.6 TS/MR carries only R38 10k to GND -- SLUSF65B section "
                      "8.3.9's 'TS function not required' network",
             firmware="The charger does not measure pack temperature.  Do not report "
                      "a battery temperature, and do not expect TS faults."),
    ]

    doc = dict(
        generated_by="hardware/demo/manufacturing/gen_firmware_hw_map.py",
        board=BOARD.name,
        board_sha256=board_sha256(),
        mcu=dict(module="ESP32-S3-WROOM-1-N16R8", ref="U1", pins=mcu),
        expanders=expanders,
        i2c=dict(sda_gpio=seen_gpio and None, devices=devices),
        limits=limits,
    )
    # sda/scl come from the MCU table so they cannot be typed twice
    doc["i2c"]["sda_gpio"] = next(r["gpio"] for r in mcu if r["role"] == "I2C_SDA")
    doc["i2c"]["scl_gpio"] = next(r["gpio"] for r in mcu if r["role"] == "I2C_SCL")
    return doc, problems


# ---------------------------------------------------------------------------
def wrap(text, width, lead):
    words, lines, line = text.split(), [], lead
    for word in words:
        if len(line) + 1 + len(word) > width and line.strip() != lead.strip():
            lines.append(line.rstrip())
            line = lead + word
        else:
            line = line + (" " if line.strip() != lead.strip() else "") + word
    lines.append(line.rstrip())
    return lines


def emit_header(doc):
    out = []
    a = out.append
    a("// AQROOT DEMO -- AS-BUILT HARDWARE DEFINITION.  DO NOT EDIT BY HAND.")
    a("//")
    a("// Generated by %s" % doc["generated_by"])
    a("// from %s" % doc["board"])
    a("// board_sha256 %s" % doc["board_sha256"])
    a("//")
    a("// Every pin, bit and address below was read out of that board file.  Direction,")
    a("// active level, safe boot latch, interrupt mask and internal-pull policy are")
    a("// engineering intent and live in the generator, where each row is checked")
    a("// against the copper before it is emitted:  an OUTPUT's safe latch must equal")
    a("// the level its external pull already holds, and an UNMASKED INPUT must have a")
    a("// defined idle level.")
    a("//")
    a("// checks/firmware_hw_map_contract.py re-runs the generator and FAILS if this")
    a("// file is not byte-identical to what the board says today.")
    a("#pragma once")
    a("")
    a('#define AQROOT_DEMO_BOARD_SHA256 "%s"' % doc["board_sha256"])
    a("")
    a("// " + "=" * 84)
    a("// ESP32-S3-WROOM-1-N16R8 (U1) -- GPIO by role")
    a("// " + "=" * 84)
    for row in doc["mcu"]["pins"]:
        if row["role"] is None or row["gpio"] is None:
            continue
        a("")
        a("// U1.%-2d %-5s %s" % (row["pad"], row["symbol"], row["net"]))
        for line in wrap(row["note"], 92, "//   "):
            a(line)
        if "strap_why" in row:
            for line in wrap("STRAP: " + row["strap_why"], 92, "//   "):
                a(line)
        a("#define AQROOT_PIN_%-18s %d" % (row["role"], row["gpio"]))
    a("")
    a("// Pads with no firmware role, recorded so nothing reclaims them.")
    for row in doc["mcu"]["pins"]:
        if row["role"] is not None and row["gpio"] is not None:
            continue
        label = row["net"] or "(no net)"
        a("//   U1.%-2d %-5s %-42s %s" % (row["pad"], row["symbol"], label, row["note"]))
    a("")
    a("// " + "=" * 84)
    a("// I2C -- internal bus")
    a("// " + "=" * 84)
    a("#define AQROOT_I2C_SDA_GPIO %d" % doc["i2c"]["sda_gpio"])
    a("#define AQROOT_I2C_SCL_GPIO %d" % doc["i2c"]["scl_gpio"])
    a("// R19/R20 are 2.2k pull-ups.  Bring the bus up at 100 kHz, then verify 400 kHz.")
    a("#define AQROOT_I2C_BRINGUP_HZ  100000")
    a("#define AQROOT_I2C_RUN_HZ      400000")
    for device in doc["i2c"]["devices"]:
        a("")
        for line in wrap(device["note"], 92, "//   "):
            a(line)
        a("#define AQROOT_I2C_ADDR_%-14s 0x%02X" % (device["role"], device["addr"]))
    a("")
    a("// " + "=" * 84)
    a("// PCAL9535A EXPANDERS -- bit map, direction, safe boot latch, mask, pull")
    a("// " + "=" * 84)
    a("//")
    a("// Pins 4..11 are P00..P07 and pins 13..20 are P10..P17 on the PCAL9535APW.")
    a("// A bit index below is PORT*8 + BIT, so P00..P07 are 0..7 and P10..P17 are 8..15,")
    a("// which is the order the driver's 16-bit port words use.")
    for ref in ("U2", "U3"):
        expander = doc["expanders"][ref]
        a("")
        a("// ---- %s @ 0x%02X -- %s" % (ref, expander["addr"], expander["role"]))
        strap = expander["addr_strap"]
        a("//      address strap: %s" % ", ".join(
            "%s=%s" % (name, strap[name]["net"]) for name in ("A0", "A1", "A2")))
        a("#define AQROOT_EXP_%s_ADDR 0x%02X" % (ref, expander["addr"]))
        for row in expander["bits"]:
            index = (0 if row["bit"][1] == "0" else 8) + int(row["bit"][2])
            a("")
            a("// %s %s (pad %d) %s -- %s, active %s, IRQ %s, internal pull %s%s"
              % (ref, row["bit"], row["pad"], row["net"] or "NC-DEMO", row["dir"],
                 row["active"], row["irq"], row["pull"],
                 ", safe latch %d (%s)" % (row["safe"], row["safe_basis"])
                 if row["dir"] == "OUT" else ""))
            for line in wrap(row["note"], 92, "//   "):
                a(line)
            a("#define AQROOT_%s_%-22s %d" % (ref, row["role"], index))
    a("")
    a("// " + "=" * 84)
    a("// AS-BUILT LIMITS -- facts firmware cannot discover and must not get wrong")
    a("// " + "=" * 84)
    for limit in doc["limits"]:
        a("")
        for line in wrap("EVIDENCE: " + limit["evidence"], 92, "//   "):
            a(line)
        for line in wrap("FIRMWARE: " + limit["firmware"], 92, "//   "):
            a(line)
        a("#define AQROOT_%-34s %d" % (limit["key"], 1 if limit["value"] else 0))
    a("")
    return "\n".join(out)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true",
                        help="do not write; exit non-zero if the tree is stale")
    parser.add_argument("--out-dir", type=Path, default=None)
    args = parser.parse_args()

    doc, problems = build()
    if problems:
        print("BOARD DISAGREES WITH THE POLICY TABLE -- refusing to emit:")
        for problem in problems:
            print("  *", problem)
        return 2

    header = emit_header(doc)
    payload = json.dumps(doc, indent=2, sort_keys=True) + "\n"
    out_h = (args.out_dir / OUT_H.name) if args.out_dir else OUT_H
    out_json = (args.out_dir / OUT_JSON.name) if args.out_dir else OUT_JSON

    if args.check:
        stale = []
        for path, want in ((OUT_H, header), (OUT_JSON, payload)):
            if not path.exists() or path.read_text(encoding="utf-8") != want:
                stale.append(path.relative_to(ROOT).as_posix())
        if stale:
            print("STALE: " + ", ".join(stale))
            return 1
        print("fresh: %s, %s" % (OUT_H.name, OUT_JSON.name))
        return 0

    out_h.parent.mkdir(parents=True, exist_ok=True)
    out_h.write_text(header, encoding="utf-8")
    out_json.write_text(payload, encoding="utf-8")
    print("wrote %s (%d lines) and %s" % (out_h, header.count("\n") + 1, out_json))
    return 0


if __name__ == "__main__":
    sys.exit(main())
