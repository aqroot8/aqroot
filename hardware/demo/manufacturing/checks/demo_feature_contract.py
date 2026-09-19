#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AQROOT Demo -- is every feature `AQROOT_DEMO_SCOPE.md` says MUST REMAIN
FUNCTIONAL actually on this board and actually wired? D-745.

EVERY OTHER CHECK IN THIS REPOSITORY IS A NO-REGRESSION CHECK.  `routing_ledger`
counts open edges, `contract_regression` diffs against a prior artifact,
`verify_promotion` compares a candidate with an authority.  All of them would
pass, unchanged and green, on a board that had never had a microphone -- because
none of them has ever been told what the product is supposed to DO.

The engineering charter asks for the opposite question before fabrication:
*"retained RF/NFC/USB/display/audio/IR/microSD/power features remain intact"*,
and it asks it ABSOLUTELY.  So this file transcribes `AQROOT_DEMO_SCOPE.md`'s
own list -- feature by feature, in its own words -- into references and nets,
and asserts three things per feature:

    F1  every named reference EXISTS on the board and is FITTED
        (a scope feature implemented by a DNP part is not implemented)
    F2  every named net is a real multi-pad net whose only open edge, if any,
        is one an owner decision covers
    F3  the approved-NC contacts are EXACTLY the eight `J5` positions Demo
        scope names -- no more, and no fewer

The table below is the deliverable, not the code.  It is deliberately verbose
and deliberately quotes the scope document, because the failure mode it guards
against is a board that passes every geometric check while quietly missing
something a backer was promised.

    python3 checks/demo_feature_contract.py [-o OUT.json]
"""
import argparse, json, math, re, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
MFG = HERE.parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(MFG))
import routing_ledger as rl                                  # noqa: E402
import audit_rail_ampacity as ara                            # noqa: E402

DRU = rl.PROJECT / "aqroot-Beta-v2.kicad_dru"
POWER_POLICY = ROOT / "Firmware/src/hw/aqroot_accessory_power_policy.h"

# --------------------------------------------------------------------------
# `AQROOT_DEMO_SCOPE.md` -> board.  `refs` must be FITTED; `nets` must be whole.
# --------------------------------------------------------------------------
FEATURES = (
    dict(scope="ESP32-S3 main computer", refs=("U1",),
         nets=("/02_MCU_CORE/BOOT_N",)),
    dict(scope="16 MB flash / 8 MB PSRAM", refs=("U1",), nets=(),
         note="in-module on the ESP32-S3-WROOM-1 variant; no separate part"),
    dict(scope="3.5-inch touchscreen", refs=("J1",),
         nets=("/DISP_CS_N", "/DISP_DC", "/DISP_RST_N", "/SPI_A_SCK",
               "/SPI_A_MOSI", "/SPI_A_MISO", "/TOUCH_INT_N", "/TOUCH_RST_N",
               "/03_SPI_A_DISPLAY_SD/LED_A", "/03_SPI_A_DISPLAY_SD/LED_K",
               "/DISP_BL_CTL")),
    dict(scope="display backlight true-off disconnect and its gate hold "
               "(D-750 fitted it, D-752 made it safe)",
         refs=("U17", "Q11", "D14", "R132", "C85",
               "L3", "D8", "C44", "R69", "R70", "R71", "R72", "R73",
               "R108", "R109"),
         nets=("/DISP_BL_CTL", "/03_SPI_A_DISPLAY_SD/BL_DISC_G",
               "/03_SPI_A_DISPLAY_SD/BL_SW",
               "/03_SPI_A_DISPLAY_SD/LED_BOOST",
               "/03_SPI_A_DISPLAY_SD/LED_A",
               "/03_SPI_A_DISPLAY_SD/LED_K_PANEL",
               "/03_SPI_A_DISPLAY_SD/LED_K"),
         note="TI SNVSA40B 6.3.3: the TPS61169 keeps a DC path from VIN "
              "through L3 and D8 to the LEDs in shutdown, and guarantees OFF "
              "only when the array's minimum Vf exceeds the maximum VIN.  This "
              "panel is 2.9-3.2 V on a 3.3 V rail, so the screen glows at "
              "about 25 mA whenever SW9 is on -- and SW9 is a slide switch, so "
              "there is no firmware mitigation.  Q11 breaks the panel cathode "
              "return; F5 below is what holds its CONTROL apart from U17's."),
    dict(scope="D-pad + A/B controls",
         refs=("SW2", "SW3", "SW4", "SW5", "SW6", "SW7"),
         nets=("/08_BUTTONS_EXPANDERS/BTN_UP_N", "/08_BUTTONS_EXPANDERS/BTN_DOWN_N",
               "/08_BUTTONS_EXPANDERS/BTN_LEFT_N", "/08_BUTTONS_EXPANDERS/BTN_RIGHT_N",
               "/08_BUTTONS_EXPANDERS/BTN_A_N", "/08_BUTTONS_EXPANDERS/BTN_B_N")),
    dict(scope="physical power switch", refs=("SW9",), nets=()),
    dict(scope="recessed BOOT / recovery", refs=("SW1",),
         nets=("/02_MCU_CORE/BOOT_N",)),
    dict(scope="RGB status indicator", refs=("D13", "R124", "R125", "R126"),
         nets=("/08_BUTTONS_EXPANDERS/FRONT_RGB_R_N",
               "/08_BUTTONS_EXPANDERS/FRONT_RGB_G_N",
               "/08_BUTTONS_EXPANDERS/FRONT_RGB_B_N"),
         note="the three RGB replacement nets the charter names explicitly"),
    dict(scope="Wi-Fi / Bluetooth / BLE", refs=("U1",), nets=(),
         note="in-module radio and antenna on the ESP32-S3-WROOM-1"),
    dict(scope="433 MHz radio + internal 433 antenna", refs=("U7",),
         nets=("/CC1101_CS_N", "/CC1101_GDO0", "/SPI_B_SCK", "/SPI_B_MOSI",
               "/SPI_B_MISO")),
    dict(scope="915 MHz LoRa + one external 915 antenna", refs=("U8",),
         nets=("/SX1262_CS_N", "/SX1262_BUSY", "/SX1262_RST_N", "/SX1262_RXEN",
               "/SX1262_DIO1", "/04_SPI_B_RADIOS_NFC/DIO2_TXEN")),
    dict(scope="NFC operating from the 3.3 V path + internal NFC antenna",
         refs=("U9", "Y1", "L5", "L6"),
         nets=("/NFC_SUPPLY", "/NFC_IRQ", "/NFC_CS_N",
               "/04_SPI_B_RADIOS_NFC/NFC_ANT_A", "/04_SPI_B_RADIOS_NFC/NFC_ANT_B",
               "/04_SPI_B_RADIOS_NFC/NFC_VDD_RF", "/04_SPI_B_RADIOS_NFC/NFC_VDD_AM",
               "/04_SPI_B_RADIOS_NFC/NFC_VDD_A", "/04_SPI_B_RADIOS_NFC/NFC_VDD_D"),
         note="U13, the optional NFC 5 V PA boost, is DNP by Demo scope and is "
              "deliberately NOT required here"),
    dict(scope="IR transmitter", refs=("D1", "Q1", "R22", "R23", "R24"),
         nets=("/IR_TX_GPIO16", "/07_IR/IR_LED_A", "/07_IR/IR_LED_K",
               "/07_IR/IR_GATE"),
         note="D-752 CORRECTED THIS ROW.  It named `U17`, which is the display "
              "BACKLIGHT boost converter and has nothing to do with the IR "
              "path; `U17` exists and is fitted, so F1 passed while requiring "
              "none of the parts that actually emit.  The emitter is `D1` "
              "(TSAL6100), its low-side switch `Q1`, the gate series/pull-down "
              "pair `R22`/`R23` and the ballast `R24`.  `R123` is the DNP "
              "second ballast and is deliberately NOT required."),
    dict(scope="IR receiver", refs=("U6",),
         nets=("/IR_RX_GPIO44", "/07_IR/IR_RX_VS_LOCAL")),
    dict(scope="speaker", refs=("U5",),
         nets=("/I2S_BCLK", "/I2S_LRCLK", "/I2S_SPK_DOUT", "/AMP_SD_MODE",
               "/06_AUDIO/SPK_P", "/06_AUDIO/SPK_N"),
         note="LS1 itself is OFF-BOARD on flying leads -- aqroot-Demo-OFF-BOARD.csv"),
    dict(scope="microphone", refs=("MK1",),
         nets=("/I2S_MIC_DIN", "/I2S_BCLK", "/I2S_LRCLK")),
    dict(scope="BMI270 6-axis IMU", refs=("U4",),
         nets=("/I2C_SDA_INT", "/I2C_SCL_INT",
               "/05_I2C_DEVICES/BMI270_SDO_ADDR")),
    dict(scope="microSD", refs=("J2",),
         nets=("/SD_CS_N", "/SD_CARD_DETECT_N", "/SPI_A_SCK", "/SPI_A_MOSI",
               "/SPI_A_MISO")),
    dict(scope="USB-C data / programming", refs=("J3", "U10"),
         nets=("/01_POWER_TREE/USB_D_CONN_P", "/01_POWER_TREE/USB_D_CONN_N",
               "/01_POWER_TREE/USB_D_ESD_P", "/01_POWER_TREE/USB_D_ESD_N",
               "/USB_D_MCU_P", "/USB_D_MCU_N")),
    dict(scope="USB-C charging", refs=("J3", "R30", "R31", "R35"),
         nets=("/01_POWER_TREE/USB_VBUS_RAW", "/01_POWER_TREE/USB_VBUS_CHG",
               "/01_POWER_TREE/VBUS_PRESENT")),
    dict(scope="battery + connector", refs=("J4", "F1"),
         nets=("/01_POWER_TREE/BAT_PROTECTED_P",)),
    dict(scope="charger", refs=("U11", "R36", "R37", "R38"),
         nets=("/01_POWER_TREE/BQ25185_SYS", "/01_POWER_TREE/ISET",
               "/01_POWER_TREE/ILIM_VSET", "/BQ25185_STAT1"),
         note="/BQ25185_STAT2 is required too and is listed separately below, "
              "because its U11.3 edge is the one an owner decision covers"),
    dict(scope="charger status observability (D-742 owner decision)",
         refs=("R127", "R128", "TP6", "TP7"), nets=("/BQ25185_STAT2",),
         note="U11.3 ships unconnected; R128 and TP7 are retained so the net "
              "stays benchable, and THIS contract is what fails if they are "
              "ever depopulated"),
    dict(scope="required battery/power safety architecture (D-269, D-186)",
         refs=("U18", "Q2", "Q3", "R75", "D9", "U19"),
         nets=("/01_POWER_TREE/BAT_RAW", "/01_POWER_TREE/BAT_MID",
               "/01_POWER_TREE/BAT_SENSE", "/01_POWER_TREE/LTC4368_FAULT_N")),
    dict(scope="battery fuel gauge", refs=("U14",),
         nets=("/I2C_SDA_INT", "/I2C_SCL_INT")),
    dict(scope="main +3V3 rail", refs=("U12", "L1"), nets=("+3V3",)),
    dict(scope="Qwiic / STEMMA QT connector", refs=("J8",),
         nets=("/09_COMMUNITY_HEADER/EXT_SDA", "/09_COMMUNITY_HEADER/EXT_SCL")),
    # ---- Community Port, Demo requirements, in the scope document's order ----
    dict(scope="Community Port: the physical 1x24 connector", refs=("J5",), nets=()),
    dict(scope="Community Port: 3.3 V accessory power", refs=("U20",),
         nets=("/ACC_3V3_SW", "/ACC_3V3_EN", "/01_POWER_TREE/ACC_3V3_ILIM")),
    dict(scope="Community Port: ONE usable 5 V accessory output",
         refs=("U21", "U22", "L4"),
         nets=("/ACC_5V_SW", "/01_POWER_TREE/ACC_5V_RAW",
               "/01_POWER_TREE/ACC_5V_ILIM", "/01_POWER_TREE/ACC_5V_FB")),
    dict(scope="Community Port: software-switched 3.3 V accessory power",
         refs=("U20",), nets=("/ACC_3V3_EN",)),
    dict(scope="Community Port: software-switched 5 V accessory power",
         refs=("U21", "U22", "R102", "R131", "TP47"),
         nets=("/ACC_5V_SW_EN", "/ACC_5V_BOOST_EN"),
         note="ACC_5V_SW_EN connectivity is a named Demo requirement.  D-186 "
              "SPLIT the single ACC_5V_EN into two independent series "
              "disconnects -- ACC_5V_BOOST_EN to U21's EN and ACC_5V_SW_EN to "
              "U22's ON -- each with its OWN external pull-down, because "
              "SLVSFJ2B specifies a 500 kOhm smart pull-down inside the part "
              "AND STILL REQUIRES AN EXTERNAL ONE while the PCAL powers up "
              "high-impedance.  R102 and R131 are therefore MANDATORY, not a "
              "convenience, and this row is what fails if either is ever "
              "dropped.  On Demo the ACC_5V_SW_EN bit sits on U3 P03 rather "
              "than the U23 P04 of D-186, because U23 is removed by scope; the "
              "SPLIT and the pull-downs are what D-186 requires, not the bit."),
    dict(scope="Community Port: SDA and SCL", refs=("U16",),
         nets=("/09_COMMUNITY_HEADER/EXT_SDA", "/09_COMMUNITY_HEADER/EXT_SCL",
               "/ACC_PWR_EN")),
    dict(scope="Community Port: Native GPIO A and B", refs=("J5",),
         nets=("/NATIVE_A", "/NATIVE_B", "/09_COMMUNITY_HEADER/NATIVE_A_HDR",
               "/09_COMMUNITY_HEADER/NATIVE_B_HDR")),
    dict(scope="Community Port: Accessory Detect", refs=("J5",),
         nets=("/ACC_DETECT_N", "/09_COMMUNITY_HEADER/ACC_DETECT_N_HDR")),
    dict(scope="Community Port: the two retained public XGPIO", refs=("U3",),
         nets=("/XGPIO4", "/XGPIO5", "/09_COMMUNITY_HEADER/XGPIO4_HDR",
               "/09_COMMUNITY_HEADER/XGPIO5_HDR"),
         note="Demo scope keeps XGPIO4 and XGPIO5 public and only those two"),
    dict(scope="Community Port: accessory fault telemetry", refs=("U3",),
         nets=("/ACC_POWER_FAULT_N",)),
    dict(scope="GPIO expanders retained by the dependency analysis",
         refs=("U2", "U3"), nets=("/WAKE_INT_N",),
         note="U23 is REMOVED on Demo by scope; it is deliberately not required"),
    dict(scope="safe states that hold while the expanders are high-impedance",
         refs=("R17", "R14", "R3", "R63"),
         nets=("/ACC_PWR_EN", "/NFC_5V_EN", "/WAKE_INT_N"),
         note="R17 100k holds the TCA4307 buffer DISABLED until firmware drives "
              "it; R14 100k holds NFC_5V_EN low, which matters precisely "
              "BECAUSE U13 is DNP -- nothing else defines that node; R3 10k is "
              "the mandatory wire-OR pull-up on WAKE_INT_N and is what makes "
              "the line deterministic before any register is written; R63 pulls "
              "the accessory side of D-187's isolation FET to ACC_3V3_SW and "
              "NOT to +3V3, or the contact stays live with the rail off."),
    dict(scope="accessory wake isolation (D-187, B-08)",
         refs=("Q10", "R63", "R66"),
         nets=("/09_COMMUNITY_HEADER/WAKE_ATTN_N_HDR",
               "/09_COMMUNITY_HEADER/WAKE_GATE_S", "/WAKE_INT_N"),
         note="a hostile accessory must not be able to hold the shared wake "
              "line low and starve the internal buttons"),
    dict(scope="Community Port ESD protection (D-188)",
         refs=("D2", "D4", "D5"), nets=(),
         note="TPD4E1B06DRLR arrays, inherited as DNP and fitted by D-188.  "
              "D-188 named FOUR arrays for a ten-XGPIO port; Demo retains two "
              "XGPIO, so three arrays cover every remaining signal contact.  "
              "F4 derives that coverage from J5 rather than trusting this list"),
)

# Demo scope: "unused physical connector positions may remain electrically NC".
EXPECTED_NC = {"J5.9", "J5.10", "J5.11", "J5.12",
               "J5.15", "J5.16", "J5.17", "J5.18"}



# --------------------------------------------------------------------------
# F5 -- THE BACKLIGHT DISCONNECT'S CONTROL MAY NOT COLLAPSE BACK ONTO U17's.
# D-752.
#
# D-750 fitted `Q11` in the panel cathode return and put its GATE on
# `/DISP_BL_CTL`, the same net as `U17` `CTRL`, on the premise that PWM would
# shut the converter down and open the FET together.  TI SNVSA40B section 6.3.5
# says the opposite in its own words: the part "chops up the internal 204mV
# reference voltage at the duty cycle of the PWM signal", filters it, and
# therefore "only the WLED DC current is modulated, which is often referred as
# analog dimming".  THE CONVERTER KEEPS SWITCHING THROUGH EVERY PWM LOW PHASE;
# shutdown needs CTRL low for longer than tSD, 2.5 ms max.  A shared gate
# therefore opens the LED string while the converter regulates: FB collapses,
# SW ramps to VOVP_SW (36/37.5/39 V), open-LED protection latches the device
# off, and `Q11`'s drain follows the anode to about 36 V across a 30 V
# `AO3400A`.  The firmware already drives 5 kHz LEDC on GPIO46.
#
# The repair is structural rather than procedural: `D14` charges `C85` from
# `/DISP_BL_CTL`, `R132` discharges it, and the gate follows the ENVELOPE of
# CTRL with tau = 22 ms.  `Q11` cannot open until at least 11.4 ms of CTRL-low
# at worst-case tolerance, and `U17` is in shutdown by 2.5 ms -- so the
# converter stops FIRST, for ANY CTRL waveform, including one no firmware ever
# intended.  That ordering is the thing this clause protects, and it is
# protected by MEASUREMENT: the four facts below plus three live controls that
# put each way of losing it back and require F5 to refuse.
# --------------------------------------------------------------------------
BL_GATE = "Q11.1"
BL_HOLD = {"Q11.1", "D14.1", "R132.1", "C85.1"}
BL_CTRL = {"U17.4", "D14.2", "R109.2"}


# --------------------------------------------------------------------------
# D-766 -- THE DISCONNECT FET MUST SURVIVE THE FAULT IT IS THERE TO SURVIVE.
#
# D-752 wrote the number down and left the part fitted: with Q11 open while
# U17 regulates, "the panel cathode, which is Q11's DRAIN, follows the anode to
# ~36 V while R69 holds its SOURCE at 0 V.  THE AO3400A IS A 30 V PART".  The
# .kicad_dru is blunter still, and it is this board's OWN published ceiling for
# that node: "an open-LED fault puts up to 39 V on LED_BOOST".  Every clause in
# F5 measured the SEQUENCING that normally keeps the board out of that state --
# and not one of them could say that the silicon holding the state off was rated
# BELOW it.  An unfitted C85, an open D14 or a shorted R132 each re-create the
# state D-752 removed; a protection element has to survive its own failure mode.
#
# So the ceiling is READ OUT OF THE .kicad_dru rather than restated here, and
# compared against a per-part table of PUBLISHED ratings.  A FET this contract
# has no published rating for is refused rather than assumed.  The same judge
# also measures the two numbers D-752 argued in prose: that the held gate
# actually enhances the FITTED part, and that the gate cannot decay below the
# FITTED part's worst-case threshold before the TPS61169 is guaranteed to have
# shut down.  Swapping a FET with a different VGS(th) silently moves both.
BL_FET = "Q11"


def led_boost_fault_ceiling_V(dru_text):
    """The board's OWN published open-LED ceiling, parsed from its rules file."""
    m = re.search(r"open-LED fault puts up to\s*([\d.]+)\s*V on LED_BOOST",
                  dru_text or "")
    return float(m.group(1)) if m else None


# Published figures, each from a datasheet this repository has actually read.
# (VDS absolute-maximum / BVDSS minimum, and VGS(th) MAXIMUM at the datasheet's
# own threshold test current.)
FET_PUBLISHED = {
    "AO3422":  dict(vds_V=55.0, vgs_th_max_V=2.00,
                    vgs_th_test_A=250e-6,
                    rds_on_vgs_V=2.5, rds_on_id_A=1.5, rds_on_max_ohm=0.200,
                    source="AOS AO3422 rev 2.1 2024-03, archived at "
                           "vendor/AOS/AO3422-rev2p1-2024-03.pdf: VDS abs-max "
                           "55 V, BVDSS 55 V min at ID=10 mA VGS=0, VGS(th) "
                           "0.6/1.3/2.0 V at ID=250 uA, and RDS(on) 200 mOhm "
                           "MAX at VGS=2.5 V ID=1.5 A.  D-779 CORRECTED THE "
                           "THRESHOLD TEST CURRENT: the archived text "
                           "extraction renders this datasheet's Symbol-font "
                           "glyphs as Latin -- Ohm as W and micro as m -- so "
                           "the EC table reads 'ID=250mA', 'RDS(ON) 160mW' and "
                           "'IDSS 1 mA at VDS=44 V'.  The first is 250 uA, and "
                           "the other two are independently disproved: the "
                           "committed JLCPCB record for C37130 says "
                           "160 mOhm@4.5V, and 1 mA of zero-gate leakage at "
                           "44 V would be 44 mW standing in a SOT-23"),
    "AO3400A": dict(vds_V=30.0, vgs_th_max_V=1.45,
                    source="AOS AO3400A rev 3.1 2023-07 as read by D-159: "
                           "VDS 30 V, VGS(th) 0.65/1.05/1.45 V"),
    # D-779's control part: published VDS and VGS(th) but NO guaranteed
    # conduction point, so the band clause has no bar and must refuse.
    "AO3400A_NO_RDS_ON": dict(vds_V=55.0, vgs_th_max_V=2.00,
                              source="control only -- a FET whose datasheet "
                                     "this contract has no RDS(on) test point "
                                     "for"),
    "2N7002":  dict(vds_V=60.0, vgs_th_max_V=2.50,
                    source="onsemi 2N7002 as read by D-187: VDSS 60 V, "
                           "VGS(th) max 2.5 V"),
}
# D-766.  THE FET IS NOT THE ONLY SEMICONDUCTOR ON THAT NODE.  The boost
# rectifier sees the SAME ceiling in reverse: while the TPS61169's internal
# switch is on, SW is pulled near ground and D8 stands off whatever the output
# capacitor holds.  D8 is RETAINED, not changed -- TI SNVSA40B section 7.2.2.2
# NAMES the NSR0240 for this converter and its 40 V VRRM does cover the 39 V --
# but nothing on this board could SAY that, and FIRST_FIVE_ASSEMBLY_PLAN already
# records a live substitution trap on exactly this reference (a keyword search
# for D8 returns FUXINSEMI SD103AWS, "a different part number entirely").  The
# margin is 1.0 V and it is REPORTED on every run so its thinness stays visible.
BL_RECTIFIER = "D8"
RECTIFIER_PUBLISHED = {
    "NSR0240": dict(vrrm_V=40.0,
                    source="onsemi NSR0240HT1G: VRRM 40 V, IF(AV) 250 mA, "
                           "SOD-323; named for the TPS61169 by TI SNVSA40B "
                           "section 7.2.2.2"),
    "PMEG2010AEH": dict(vrrm_V=20.0, source="Nexperia PMEG2010AEH: VRRM 20 V"),
    "BAT54WS": dict(vrrm_V=30.0, source="BAT54WS: VRRM 30 V"),
    "SD103AWS": dict(vrrm_V=40.0,
                     source="FUXINSEMI SD103AWS: VRRM 40 V -- NOT an approved "
                            "substitute for D8; see FIRST_FIVE_ASSEMBLY_PLAN"),
}

# D-752's derived held gate, and the source voltage R69 sits at while U17
# regulates 109 mA through 1.87 ohm to the TPS61169's 204 mV feedback point.
BL_HELD_GATE_V = 2.60
BL_SOURCE_V = 0.204
# D-079's LED setpoint: what Q11 has to sustain for the backlight to be lit.
BL_STRING_CURRENT_A = 0.109
# TI SNVSA40B EC table: CTRL low to shutdown, MAXIMUM.
BL_TSD_MS = 2.5
# D-752's published tolerance band on tau: 19.6 ms worst case, 22.0 ms nominal
# on R132 1 % and C85 10 %.
BL_TAU_WORST_RATIO = 19.6 / 22.0
# D-779.  AND THE CAPACITOR'S DC BIAS, WHICH 100 nF ON A 50 V PART DID NOT NEED.
# C85 moves to 1 uF on the existing 25 V X7R 0603 line, where about 2.6 V of
# bias is no longer negligible.  This is a DECLARED allowance, deliberately
# pessimistic for a 25 V part at 10 % of its rating, and it is applied to tau
# so the ordering below is derived on the retained capacitance and not the
# marked one.
BL_CAP_BIAS_RETENTION = 0.75


def judge_backlight_fet(values, dru_text):
    """Pure over {ref: value} and the .kicad_dru text; returns (ok, detail)."""
    part = (values.get(BL_FET) or "").strip()
    pub = FET_PUBLISHED.get(part)
    ceiling = led_boost_fault_ceiling_V(dru_text)
    r132 = _ohms(values.get("R132"))
    c85 = _farads(values.get("C85"))
    tau_s = r132 * c85 if (r132 and c85) else None
    tau_worst_s = (tau_s * BL_TAU_WORST_RATIO * BL_CAP_BIAS_RETENTION
                   if tau_s else None)
    vgs_held = BL_HELD_GATE_V - BL_SOURCE_V
    f = dict(
        fet=BL_FET, fitted_part=part, published=dict(pub) if pub else None,
        dru_published_fault_ceiling_V=ceiling,
        held_gate_V=BL_HELD_GATE_V, source_V=BL_SOURCE_V,
        vgs_held_V=round(vgs_held, 4),
        tau_nominal_ms=round(tau_s * 1e3, 4) if tau_s else None,
        tau_worst_ms=round(tau_worst_s * 1e3, 4) if tau_worst_s else None,
        tsd_max_ms=BL_TSD_MS,
        fet_is_a_part_with_published_ratings=pub is not None,
        board_publishes_a_fault_ceiling=ceiling is not None,
        vds_margin_V=None, vds_margin_ratio=None, vgs_overdrive_V=None,
        earliest_disconnect_ms=None, ordering_margin_ratio=None,
        fet_vds_covers_the_published_fault_ceiling=False,
        gate_hold_enhances_the_fitted_fet=False,
        u17_shuts_down_before_q11_opens=False)
    if pub and ceiling:
        f["vds_margin_V"] = round(pub["vds_V"] - ceiling, 4)
        f["vds_margin_ratio"] = round(pub["vds_V"] / ceiling, 4)
        f["fet_vds_covers_the_published_fault_ceiling"] = pub["vds_V"] >= ceiling
        f["vgs_overdrive_V"] = round(vgs_held - pub["vgs_th_max_V"], 4)
        f["gate_hold_enhances_the_fitted_fet"] = vgs_held > pub["vgs_th_max_V"]
        if tau_worst_s and BL_HELD_GATE_V > pub["vgs_th_max_V"]:
            t_open_ms = tau_worst_s * 1e3 * math.log(
                BL_HELD_GATE_V / pub["vgs_th_max_V"])
            f["earliest_disconnect_ms"] = round(t_open_ms, 4)
            f["ordering_margin_ratio"] = round(t_open_ms / BL_TSD_MS, 4)
            f["u17_shuts_down_before_q11_opens"] = t_open_ms > BL_TSD_MS
        # ---- D-779: WHAT THE THRESHOLD SPEC ACTUALLY SAYS ------------------
        # D-766 wrote "VGS(th) is specified at ID = 250 mA, and this circuit
        # needs 109 mA -- LESS THAN HALF the threshold test current -- so the
        # device is already passing more than twice what is asked of it".  The
        # test current is 250 MICROamps.  At VGS(th) the part passes 436 times
        # LESS than this string needs, so that sentence was exactly inverted
        # and it is deleted rather than softened.
        #
        # WHAT REPLACES IT IS THE OTHER PUBLISHED POINT.  AOS guarantees
        # RDS(on) <= 200 mOhm at VGS = 2.5 V and ID = 1.5 A -- 13.8x the
        # 109 mA this string draws, only 104 mV above the held VGS.  Between
        # VGS(th) and that point the datasheet says nothing, so the VGS at
        # which Q11 stops sustaining 109 mA is UNPUBLISHED and lies somewhere
        # in that band.
        #
        # THE ORDERING MUST THEREFORE NOT DEPEND ON WHERE IN THE BAND IT IS.
        # `ordering_break_even_vgs_V` is the collapse VGS for which the gate
        # decay takes exactly tSD: a collapse ABOVE it breaks the ordering, one
        # below it does not.  The window in which the ordering can fail is
        # `vgs_held - break_even`, and the bar is NOT a chosen number -- it is
        # the distance from the held VGS up to the datasheet's own guaranteed
        # conduction point.  A collapse inside a window narrower than that
        # would require ID to fall from >= 1.5 A to < 0.109 A across less than
        # 148 mV of gate, which the same datasheet's 11 S transconductance
        # excludes.  At C85 = 100 nF the window was 312 mV against a 104 mV
        # bar; at 1 uF it is 44 mV.
        if tau_worst_s and pub.get("rds_on_vgs_V"):
            guaranteed_vgs = pub["rds_on_vgs_V"]
            f["guaranteed_conduction_vgs_V"] = guaranteed_vgs
            f["guaranteed_conduction_id_A"] = pub["rds_on_id_A"]
            f["string_current_A"] = BL_STRING_CURRENT_A
            f["guaranteed_current_over_what_is_asked_x"] = round(
                pub["rds_on_id_A"] / BL_STRING_CURRENT_A, 3)
            f["held_vgs_below_the_guaranteed_point_V"] = round(
                guaranteed_vgs - vgs_held, 4)
            f["unspecified_conduction_band_V"] = [pub["vgs_th_max_V"],
                                                  round(vgs_held, 4)]
            be_gate = BL_HELD_GATE_V / math.exp(
                BL_TSD_MS / (tau_worst_s * 1e3))
            be_vgs = be_gate - BL_SOURCE_V
            window = max(0.0, vgs_held - be_vgs)
            bar = guaranteed_vgs - vgs_held
            f["ordering_break_even_vgs_V"] = round(be_vgs, 4)
            f["ordering_failure_window_V"] = round(window, 4)
            f["ordering_failure_window_bar_V"] = round(bar, 4)
            f["ordering_band_covered_pct"] = round(
                100.0 * (be_vgs - pub["vgs_th_max_V"])
                / (vgs_held - pub["vgs_th_max_V"]), 2)
            f["the_ordering_does_not_depend_on_the_unspecified_band"] = (
                window < bar)
            f["threshold_test_current_A"] = pub.get("vgs_th_test_A")
    # the rectifier stands off the same ceiling in reverse
    rect_part = (values.get(BL_RECTIFIER) or "").strip()
    rp = RECTIFIER_PUBLISHED.get(rect_part)
    f["rectifier"] = BL_RECTIFIER
    f["rectifier_fitted_part"] = rect_part
    f["rectifier_published"] = dict(rp) if rp else None
    f["rectifier_is_a_part_with_published_ratings"] = rp is not None
    f["rectifier_vrrm_covers_the_published_fault_ceiling"] = bool(
        rp and ceiling and rp["vrrm_V"] >= ceiling)
    f["rectifier_margin_V"] = (round(rp["vrrm_V"] - ceiling, 4)
                               if rp and ceiling else None)
    f["ok"] = all(bool(f.get(k)) for k in (
        "fet_is_a_part_with_published_ratings",
        "board_publishes_a_fault_ceiling",
        "fet_vds_covers_the_published_fault_ceiling",
        "gate_hold_enhances_the_fitted_fet",
        "u17_shuts_down_before_q11_opens",
        "the_ordering_does_not_depend_on_the_unspecified_band",
        "rectifier_is_a_part_with_published_ratings",
        "rectifier_vrrm_covers_the_published_fault_ceiling"))
    return f["ok"], f


def judge_backlight(nets_by_contact, values):
    """Pure over {contact: netname} and {ref: value}; returns (ok, detail)."""
    gate = nets_by_contact.get(BL_GATE)
    ctrl = nets_by_contact.get("U17.4")
    on_gate = {c for c, n in nets_by_contact.items() if n == gate and gate}
    on_ctrl = {c for c, n in nets_by_contact.items() if n == ctrl and ctrl}
    f = dict(
        gate_net=gate, ctrl_net=ctrl,
        gate_is_not_ctrl=bool(gate) and bool(ctrl) and gate != ctrl,
        gate_net_is_exactly_the_hold=on_gate == BL_HOLD,
        ctrl_net_carries_the_diode_anode=on_ctrl == BL_CTRL,
        hold_returns_to_ground=(nets_by_contact.get("R132.2") == "GND"
                                and nets_by_contact.get("C85.2") == "GND"),
        # tau is the whole argument; a silent value change is a silent repeal
        r132_value_is_220k="220k" in (values.get("R132") or ""),
        # D-779 moved it 100 nF -> 1 uF on the EXISTING 1 uF 25 V X7R 0603
        # line, so the ordering no longer rests on where in the AO3422's
        # unspecified conduction band the string current actually collapses.
        c85_value_is_1uF="1uF" in (values.get("C85") or ""),
        # and the OFF floor is held by the diode's PUBLISHED reverse leakage
        d14_is_a_silicon_switching_diode=(values.get("D14") or "").upper()
                                          .startswith("1N4148"),
        gate_contacts=sorted(on_gate), ctrl_contacts=sorted(on_ctrl))
    f["ok"] = all(v for k, v in f.items()
                  if k.startswith(("gate_is", "gate_net_is", "ctrl_net",
                                   "hold_", "r132_", "c85_", "d14_")))
    return f["ok"], f


# --------------------------------------------------------------------------
# F6 -- THE ACCESSORY RAILS MAY NOT PULL THE PACK INTO ITS OWN PROTECTION,
# AND THE PACK PROTECTION MUST NOT FIRE ON A RAIL THE PRODUCT PUBLISHES.
# D-753 (envelope) + D-765 (limiter silicon) + D-771 (this decision).
#
# D-750 answered the external first-spin review's combined-load item with a
# POLICY: *"firmware must not raise both accessory rails to their per-rail
# maxima together"*.  A policy is not an enforcement mechanism.  THIS BOARD HAS
# NO ACCESSORY CURRENT MEASUREMENT -- firmware can choose whether a rail is ON,
# and cannot know what an arbitrary external accessory then draws.  The only
# thing that actually bounds an accessory is the load switch's own current
# limit, and at the values D-750 shipped those limits were far ABOVE what the
# policy permitted.
#
# So this clause computes the envelope from the two resistors that set it, and
# refuses the board if any state the Community Port can reach exceeds the pack
# protection's MINIMUM trip.  TI SLVSFJ2B / SLVSGP6A equation 1:
#
#     ILIM = 1.18 x (R_ILIM[kOhm]) ^ -1.072            (amps, kilohms)
#
# and the part's own EC table brackets that typ at 0.68x / 1.32x over
# -40..+125 C (the widest ratio it publishes, read off the 19.2 kOhm row).
#
# ---- D-771.  TWO THINGS THAT HAD NO WORDS HERE ---------------------------
#
# (1) THE ENVELOPE WAS ONLY EVER CHECKED FROM ABOVE.  Every clause D-753 and
#     D-765 wrote asks "can an accessory pull TOO MUCH".  None of them asks
#     whether the rail can deliver what the product PROMISES.  D-098 locks the
#     first five boards at ACC_3V3_SW = 400 mA TOTAL and ACC_5V_SW = 300 mA
#     TOTAL and requires those numbers to appear in accessory-facing
#     documentation in those words -- and at 2.7 kOhm each limiter GUARANTEES
#     only 0.277 A.  The board published a budget its own silicon could refuse
#     to deliver, on the two contacts the Community Port exists for.
#
# (2) THE CHAIN WAS ORDERED AGAINST A TYPICAL.  `double_fault_stays_inside_the
#     _protection_chain` compared the double-fault current against 3.3333 A --
#     50 mV / 15 mOhm -- as though 50 mV were a limit.  ADI's own EC table
#     (Rev C, archived at vendor/ADI/) guarantees the LTC4368 forward
#     overcurrent threshold only as 40 / 50 / 60 mV over temperature, so at
#     R75 = 15 mOhm +/-1 % the breaker's real band was 2.640 .. 4.040 A.  The
#     board D-765 shipped reaches 2.886 A in double fault -- ABOVE the 2.640 A
#     minimum -- so the clause was FALSE on the board that passed it.  And
#     RETRY is grounded (sheet 01 note, D-050/D-052/D-064/D-068): the LTC4368
#     breaker LATCHES OFF and is cleared only by toggling SHDN, while the
#     BQ25185's IBAT_OCP hiccups and retries.  The two bands overlapped by
#     1.05 A, so on an unlucky unit the LATCHING protection fired first.
#
# BOTH ARE NOW CLAUSES, and both are computed from board values.  R75 moves to
# 10 mOhm, which puts the breaker at 3.960 .. 6.061 A -- ENTIRELY ABOVE the
# IBAT_OCP band's 3.6875 A maximum, so the recoverable protection is now
# guaranteed to act first on every unit rather than on a typical one.
# --------------------------------------------------------------------------
ILIM_R = {"ACC_3V3": "R97", "ACC_5V": "R101"}
ILIM_SWITCH = {"ACC_3V3": "U20", "ACC_5V": "U22"}
ILIM_LO, ILIM_HI = 0.68, 1.32          # SLVSFJ2B/SLVSGP6A EC table, widest row
# D-765.  EACH PART'S OWN SPECIFIED ILIM PROGRAMMING RANGE, from its own
# datasheet -- because D-753 set 0.407 A on a part specified from 0.5 A and
# NOTHING IN THIS CONTRACT COULD SAY THE WORD FOR THAT ACT.  The range is a
# RECOMMENDED OPERATING CONDITION: outside it the datasheet warrants nothing,
# and this is a user-accessible protection element.
ILIM_SPEC_RANGE = {
    # SLVSGP6A section 6.3, single variant, DDC (SOT-23-6) -- THE FITTED PART
    "TPS22950-Q1": (0.05, 3.5),
    # SLVSFJ2B section 5 Device Comparison Table -- the C variant is 0.5 A up,
    # NOT the 0.05 A that belongs to the WCSP-only base TPS22950
    "TPS22950C": (0.50, 3.5),
    "TPS22950": (0.05, 3.5),    # WCSP YBH only; not a leaded option here
    "TPS22950L": (0.50, 3.5),   # latch-off, no RCB; rejected 2026-08-22
}
# UL 2367 recognition, file E169910, stated identically by both datasheets.
UL2367_ILIM_RANGE = (0.066, 2.46)
# D-771.  D-098, 2026-08-23, IN ITS OWN WORDS: "First five boards:
# ACC_3V3_SW = 400 mA TOTAL, ACC_5V_SW = 300 mA TOTAL ... THE TWO DUPLICATE
# CONTACTS ON EACH RAIL SHARE THE RAIL LIMIT - they do not double it ... This
# must appear in accessory-facing documentation in these words."  A number the
# product PUBLISHES is a number the hardware must GUARANTEE.
PUBLISHED_RAIL_BUDGET_A = {"ACC_3V3": 0.400, "ACC_5V": 0.300}
# D-771.  THE PROTECTION CHAIN, OVER TOLERANCE, FROM EACH PART'S OWN TABLE.
SENSE_R = "R75"                        # LTC4368 current-sense element
BREAKER = "U18"
# ADI LTC4368 Rev C, Electrical Characteristics, dVSENSE,F "Overcurrent Fault
# Threshold, Forward (SENSE - VOUT)", the `l` row -- GUARANTEED over the full
# operating temperature range, not a typical.  mV.
BREAKER_SENSE_mV = {
    "LTC4368-1": (40.0, 50.0, 60.0),
    "LTC4368-2": (40.0, 50.0, 60.0),   # same forward row; differs in reverse
}
# REPORTED, NOT ORDERED AGAINST.  The same EC table carries a THIRD forward row
# at `VIN = 12 V, VOUT = 0 V` -- 30 / 50 / 70 mV -- which is a COLLAPSED output,
# i.e. a hard short downstream of the sense element.  It is deliberately not the
# ordering row: the clause below asks which protection fires first on an
# OVERLOAD, where VOUT tracks VIN and the 40/50/60 row applies.  On a genuine
# dead short both protections fire and latching is the wanted behaviour.  It is
# printed so the choice of row is visible rather than implicit.
BREAKER_SENSE_HARD_SHORT_mV = (30.0, 50.0, 70.0)
# D-753's constant, now carried as a BAND.  BQ25185 SLUSF65B: 3.125 A typ +/-18 %.
IBAT_OCP_A = (3.125 * 0.82, 3.125, 3.125 * 1.18)
IBAT_OCP_MIN = IBAT_OCP_A[0]           # retained name; D-753's number, unchanged
# --------------------------------------------------------------------------
# D-775 -- NORMAL D-098 OPERATION IS A SEPARATE CONTRACT FROM LIMITER FAULTS,
# AND ITS FLOOR IS DERIVED RATHER THAN DECLARED.
#
# Everything above this point screens a FAULT: what an accessory can pull
# through a limiter that is doing its job.  None of it asks the other question
# -- what the board costs itself when it HONOURS D-098's published budget.  At
# the bottom of the pack's discharge, ACC_3V3_SW = 400 mA and ACC_5V_SW =
# 300 mA delivered AT THE SAME TIME, on top of every internal subsystem
# running at once, pull the BQ25185 past its own IBAT_OCP minimum.  That is the
# published budget hiccupping the charger, not an accessory misbehaving.
#
# TWO EARLIER ATTEMPTS AND WHAT WAS WRONG WITH EACH.  D-765 screened it from
# 0.36 ohm measured FROM THE CELL -- which double-counts Q2/Q3, R75 and the
# pack's own internal resistance, all UPSTREAM of the node the MAX17048
# actually reads -- and left it REPORT-ONLY because nothing enforced a floor.
# The first D-775 draft fixed the node and made it a clause, but priced it from
# a ROUND 0.250 ohm "bound with contingency" and a flat 60 mW "branch-loss
# allowance", and then checked the margin AT a hand-written 3.75 V floor.  A
# check at an asserted floor is not a derivation: nothing in the repository
# could say why the number was 3.75 and not 3.55 or 3.95.
#
# SO THE FLOOR IS SOLVED FOR.  Every series term is either measured off this
# board on every run or read from the part's own table:
#
#   R_bat      live BAT_PROTECTED_P copper (R75.2 -> U11.2, measured by
#              audit_rail_ampacity's own graph) at CU_HOT_RISE_K, plus the
#              BQ25185 BATFET maximum;
#   R_trunk    live SYS -> L4.1 trunk, the U21 boost's input path;
#   R_a3/R_a5  live accessory-rail copper plus each load switch's own RON max.
#
# and `required_vcell_floor_V` is the VCELL at which the resulting battery
# current reaches IBAT_OCP's MINIMUM less NORMAL_OCP_MARGIN_MIN.  The firmware
# constants in Firmware/src/hw/aqroot_accessory_power_policy.h must be at or
# above it; F6 FAILS if they are not.  THE FLOOR NOW MOVES BY ITSELF: a wider
# +3V3 budget, a different boost setpoint, a re-routed BAT_PROTECTED_P or a new
# limiter setting all change the requirement, and the firmware has to follow.
#
# WHAT IT COST.  On this board the derived dual-rail requirement is 3.7622 V,
# ABOVE the 3.75 V the first draft asserted -- the draft passed only because
# its round 0.250 ohm and flat 60 mW under-counted the accessory-rail copper,
# the two limiters' RON and the SYS->U21 trunk.  The firmware floor moves to
# 3.80 V.  The single-rail requirement is 3.1232 V, so D-766's existing 3.50 V
# policy floor stands unchanged and well clear.
# --------------------------------------------------------------------------
# BQ25185 SLUSF65B Electrical Characteristics, RON_BAT: 115 typ / 140 MAX at
# VBAT = 4.5 V, IBAT = 400 mA.  The EC table header reads "VIN = 5 V, VBAT =
# 3.6 V.  -40 C < TJ < 125 C unless otherwise noted", and the RON_BAT row
# overrides only VBAT and IBAT -- so 140 mOhm is ALREADY the over-temperature
# maximum and no thermal allowance is owed on it.
RON_BAT_MAX_OHM = 0.140
# WHAT IS NOT PUBLISHED: RON_BAT vs VBAT.  The row is specified at 4.5 V and
# this model runs the BATFET at about 3.2 V of SYS with 2.3 A through it; TI
# prints no curve and no second row, and SLUSF65B has no RON figure in its
# Typical Characteristics.  A DECLARED 1.40x allowance covers the gate-drive
# extrapolation.  IT IS NOT LOAD-BEARING BY ACCIDENT: the clause below also
# reports `batfet_breakeven_ohm`, the resistance at which the derived floor
# would stop holding the margin, so how much unpublished degradation is
# tolerated is a printed number rather than a hidden assumption.  At the 3.80 V
# floor the margin survives 1.52x the datasheet maximum and IBAT_OCP's own
# minimum is not reached until 2.18x.
RON_BAT_VBAT_ALLOWANCE = 1.40
# Copper's own temperature coefficient, applied to every LIVE resistance below,
# because audit_rail_ampacity states RHO_CU at 20 C.  65 K is the rise used:
# that same audit's worst ACCEPTED segment rise on THIS rail is 49.6 K over
# ambient (the U11.2 package-land neck), which at a 25 C ambient is 75 C, i.e.
# 55 K above where RHO_CU is stated.
CU_TC_PER_K = 0.00393
CU_HOT_RISE_K = 65.0
# TPS22950-Q1 SLVSGP6A EC, ON-Resistance: the -40..+125 C rows, which is the
# grade-1 part's own widest guaranteed band and the row audit_rail_ampacity
# already quotes for U20.
ACC_SWITCH_RON_OHM = {"ACC_3V3": 0.068, "ACC_5V": 0.054}
# THE PATHS.  `bound_ohm` is a sanity ceiling on the LIVE measurement, not the
# value the model runs at -- the model runs at the measured number, and a live
# path that exceeds its ceiling FAILS loudly instead of being absorbed.  The
# requirement is derived twice, once on the live values and once on the
# ceilings, and the FIRMWARE must satisfy the worse of the two.
NORMAL_PATHS = {
    "bat_protected_p": dict(rail="BAT_PROTECTED_P", src=("R75.2",),
                            snk=("U11.2",), bound_ohm=0.050,
                            last_measured_ohm=0.043116,
                            what="MAX17048 measurement node -> BQ25185 BAT"),
    "sys_to_u21": dict(rail="SYS_TO_ACC5V_BOOST",
                       src=("U12.1", "U12.10", "U12.11",
                            "C24.1", "C26.2", "C28.1"),
                       snk=("L4.1",), bound_ohm=0.200,
                       last_measured_ohm=0.183309,
                       what="SYS -> the ACC_5V boost's input inductor"),
    "acc_3v3_sw": dict(rail="ACC_3V3_SW", src=("U20.5",),
                       snk=("J5.3", "J5.22"), bound_ohm=0.240,
                       last_measured_ohm=0.224426,
                       what="U20 output -> the Community Port 3.3 V contacts"),
    "acc_5v_sw": dict(rail="ACC_5V_SW", src=("U22.5",),
                      snk=("J5.1", "J5.24"), bound_ohm=0.120,
                      last_measured_ohm=0.110567,
                      what="U22 output -> the Community Port 5 V contacts"),
}
# `last_measured_ohm` is the D-773 release run of audit_rail_ampacity.py
# (evidence/d773-rail-ampacity.json, series_resistance_mohm per rail) and is
# only the DEFAULT that keeps judge_accessory_envelope a pure function for its
# own mutation controls.  main() re-measures all four off the live board and
# passes them in; `live_path_ohm` in the report is always the measured set.
# A DECLARED DESIGN CONVENTION, stated as one because it is not a datasheet
# number: normal, conforming, fully-published operation keeps 10 % of headroom
# to the RECOVERABLE IBAT_OCP minimum.  It exists to cover what the model does
# not itemise -- pour-delivered +3V3 distribution, converter efficiency below
# the conservative figures used here, and cell-to-cell spread.  The
# zero-margin floor is reported beside every case so the split between physics
# and convention is visible.
NORMAL_OCP_MARGIN_MIN = 0.10
# Firmware carries a float constant a human reads; the requirement is rounded
# UP onto this grid before it is compared with one.
FLOOR_GRID_V = 0.05
NORMAL_SINGLE_VBAT_FLOOR = 3.50         # D-766's retained policy floor
NORMAL_DUAL_VBAT_FLOOR = 3.80           # D-775's DERIVED requirement, gridded
VBAT_CORNER = 3.0                      # fault-envelope 1S Li-ion corner
# D-774 SWEEP.  Every other physical constant in this file now cites a primary
# source (see ILIM_LO/HI, IBAT_OCP_A, BREAKER_SENSE_mV, BOOST_FB, U12_IOUT_A,
# U21_*, FUSE_A, BL_*).  THESE TWO DO NOT, and are kept because both are
# CONSERVATIVE IN THE DIRECTION THAT MATTERS: a lower efficiency means MORE pack
# current for the same delivered load, so every margin this file reports is
# understated by them.  The TPS63020 near unity ratio at ~1.9 A and the TPS61023
# at 3.0 -> 5.165 V both run above these figures in their own published curves.
V_3V3, ETA_U12 = 3.3, 0.90             # TPS63020 buck-boost, conservative
ETA_U21 = 0.88                         # TPS61023 boost, conservative
# --------------------------------------------------------------------------
# D-773 -- AND THE 5 V RAIL'S OWN SETPOINT WAS A NUMBER, FROM A WRONG REFERENCE.
#
# `V_ACC5V` read `4.95` and `architecture/ARCHITECTURE.md` published `4.99 V`,
# both derived from **VREF = 0.6 V**.  TI `SLVSF14B`'s Electrical
# Characteristics gives the TPS61023's FB reference as **580 / 595 / 610 mV** in
# PWM mode -- the TYPICAL is 595 mV, not 600 -- so neither figure was the
# board's, and the two did not even agree with each other.
#
# The rail's pack cost scales DIRECTLY with this voltage, and it is the term
# that decides the thinnest margin on this board.  So it is DERIVED from the
# board's own `R99`/`R100` over their 1 % bands and the part's own published
# VREF band, the envelope runs on the WORST CASE (highest, because that is what
# costs the most pack current), and the band is reported beside it.
#
# AND THE SAME EC TABLE CARRIES A CLAUSE NOTHING HAD CHECKED: `VOVP`, the
# output over-voltage protection threshold, is **5.5 / 5.7 / 6.0 V rising**.  A
# divider whose WORST-CASE HIGH setpoint reaches the MINIMUM OVP threshold would
# make the converter fault on a good board.  Nothing in this repository had ever
# compared the two.
# --------------------------------------------------------------------------
BOOST_FB = dict(
    ref="U21", top="R99", bottom="R100",
    parts={
        # TI SLVSF14B EC, archived at vendor/TI/.  mV.
        "TPS61023": dict(vref_mV=(580.0, 595.0, 610.0),
                         vovp_V=(5.5, 5.7, 6.0)),
    })
# --------------------------------------------------------------------------
# D-772 -- THE INTERNAL +3V3 LOAD WAS A HAND-WRITTEN CONSTANT, AND IT WAS LOW.
#
# `I_INTERNAL` read `1.0` with the comment "the published internal +3V3 budget",
# and every envelope mode above, every `U12` capability answer and every
# battery-side margin in this contract is a function of it.  Nothing checked it.
#
# THE REPOSITORY'S OWN LAST DERIVATION PREDATES THE PARTS IT HAS TO COVER.
# `audits/2026-08-23-s1-community-sheet09-implementation.md` re-derived the
# internal worst case as 823 mA from an FBV2-COMM-001 subtotal of 769 mA.  That
# subtotal has FIVE lines -- Wi-Fi TX 355, display + backlight 181, touch and
# housekeeping 13, microSD write 100, audio 120 -- and it contains **no NFC
# line at all**, because when it was written `U9` and its twelve decoupling
# capacitors were still DNP.  **D-192 FITTED them**, and **D-205** then
# allocated the NFC front end **100 mA on +3V3 with the field on**.  Nothing
# added that 100 mA to the budget.
#
# AND THE "WORST SINGLE RADIO" ASSUMPTION IS NOT TRUE OF THIS BOARD.  The
# subtotal counts Wi-Fi TX as "the worst single radio".  `U8` is an EXTERNAL
# E22-900M22S module on its own `+3V3` pin, and NOTHING IN HARDWARE STOPS IT
# TRANSMITTING WHILE THE ESP32 DOES -- the one-TX-at-a-time discipline the Demo
# scope states is between the two SUB-GHz radios, which share SPI-B, and not
# between them and the Wi-Fi radio inside `U1`.  A rule no silicon enforces is
# the exact defect D-753 named; this table therefore ADDS the worse sub-GHz
# radio to the Wi-Fi line rather than substituting for it.
#
# So the budget is itemised here, every line cited, and it is SUMMED rather than
# asserted.  `every_fitted_p3v3_consumer_is_budgeted` is what makes it a gate
# rather than a table: the board's own `+3V3` net is read, every FITTED
# non-passive consumer on it is collected, and a consumer no line names is a
# FAILURE.  The next part put on this rail cannot be silently unbudgeted.
#
# WHAT IT COSTS, STATED: the honest figure is 1.063 A against the 1.0 A this
# constant published, so every margin below narrows.  They all still hold --
# see `modes_I_bat_A` and `converter_capability_A` -- and the thinnest is the
# 5 V rail alone at its limiter, which is an accessory FAULT on top of every
# internal subsystem running at once, and whose consequence is a `BQ25185`
# `IBAT_OCP` hiccup that re-enables the BATFET after tREC_SC (D-771 guaranteed
# it acts before the latching breaker on every unit) -- but NOT indefinitely:
# D-779 reads SLUSF65B 6.3.7.3's other half, where 4-7 consecutive trips in a
# 2 s window leave the BATFET off until a valid VIN is connected.
# --------------------------------------------------------------------------
P3V3_INTERNAL_BUDGET = (
    dict(line="Wi-Fi / BLE TX, the worst RF condition the module publishes",
         mA=355.0, refs=("U1",),
         cite="Espressif ESP32-S3-WROOM-1 datasheet v1.8 Table 6-4, archived at "
              "vendor/Espressif/: 355 mA PEAK, 802.11b 1 Mbps @20.5 dBm, and "
              "the table states TX current is rated at 100 % duty.  Table 6-5's "
              "worst BLE row is 344 mA and is NOT added -- one radio inside one "
              "module cannot transmit twice at once"),
    dict(line="sub-GHz TX, the worse of the two shared-bus radios",
         mA=140.0, refs=("U7", "U8"),
         cite="Ebyte E22-M series user manual, archived at vendor/Ebyte/: "
              "emission current 100-140 mA instantaneous @22 dBm for the fitted "
              "E22-900M22S.  The E07-400M10S CC1101 is 35 mA (its own manual "
              "v1.3).  ONLY THE WORSE OF THE TWO is counted, because the Demo "
              "scope holds them to one TX at a time on the shared SPI-B bus -- "
              "but it is ADDED TO the Wi-Fi line and not substituted for it"),
    dict(line="display logic + backlight at maximum",
         mA=181.0, refs=("J1", "U17", "L3"),
         cite="FBV2-COMM-001 internal subtotal, retained"),
    dict(line="audio at the capped level", mA=120.0, refs=("U5",),
         cite="FBV2-COMM-001 internal subtotal, retained; D-161 records the "
              "MAX98357A's 230 mA PEAKS separately as locally supplied"),
    dict(line="microSD write", mA=100.0, refs=("J2",),
         cite="FBV2-COMM-001 internal subtotal, retained"),
    dict(line="NFC front end, field on", mA=100.0, refs=("U9",),
         cite="D-205: DS12484 Rev 3 Table 121 gives I_AL-AM = 26 mA MAX for the "
              "IC with all blocks active and D-134's first-build network draws "
              "about 60 mA at the driver, so the +3V3 allocation with the field "
              "on is 100 mA.  THIS LINE IS THE ONE THE 823 mA FIGURE WAS "
              "MISSING: U9 was DNP when FBV2-COMM-001 was written and D-192 "
              "fitted it.  D-205's own guard rail stands -- a C_s move to 270 pF "
              "would draw about 257 mA and requires this budget to be re-run"),
    dict(line="IR transmitter, burst average", mA=50.0, refs=("D1", "Q1", "R24"),
         cite="D-155 / FBV2-S1-007: the 150 mA peaks are supplied by C12 22 uF "
              "and not by the rail, so the rail sees the burst average"),
    dict(line="touch + housekeeping (both expanders and the IMU)",
         mA=13.0, refs=("U2", "U3", "U4"),
         cite="FBV2-COMM-001 internal subtotal, retained"),
    dict(line="front RGB at white", mA=4.2, refs=("D13",),
         cite="FBV2-S1-008 / D-184's re-derivation"),
)
# THE SUM, NOT AN ASSERTION.  Was a hand-written 1.0.
I_INTERNAL = round(sum(x["mA"] for x in P3V3_INTERNAL_BUDGET) / 1000.0, 4)
I_INTERNAL_PUBLISHED_WAS = 1.0          # the constant D-772 replaced

# --------------------------------------------------------------------------
# D-777 -- THE BATTERY CONNECTION WAS THE ONE ELEMENT OF THE BATTERY PATH THIS
# REPOSITORY HAD NEVER GIVEN A RATING.
#
# D-771 ordered the protection chain over its own tolerance; D-775 derived the
# VCELL floors from the live board; D-772 summed the internal budget.  Every
# one of those asks whether the SILICON survives.  None of them ever asked what
# the CONNECTOR is rated for -- and it is the smallest number in the path by a
# wide margin:
#
#     J4  JST PH  B2B-PH-K-S(LF)(SN)        2.0000 A  (published, AWG #24)
#     BQ25185 IBAT_OCP (recoverable)        2.5625 - 3.6875 A
#     LTC4368 breaker (latching, D-771)     3.9600 - 6.0610 A
#     F1 0466005 one-shot fuse              5.0000 A
#
# So there is a band -- 2.0 A up to the first protection that acts -- in which
# the connector is over its rating and NOTHING on this board objects, and
# D-775's published simultaneous envelope sat inside it at 2.2715 A.
#
# NEITHER NUMBER BELOW IS TYPED HERE.  The rating is PARSED out of the archived
# JST datasheet text and the pack's lead gauge out of the archived Adafruit
# pack specification, exactly as D-774 made the ampacity self-check parse the
# .kicad_dru table it claimed to re-derive.  A connector swap that does not
# bring its own archived rating fails this clause rather than inheriting 2 A.
#
# THE PACK'S LEADS ARE SMALLER THAN THE GAUGE THE RATING IS SPECIFIED AT --
# UL 26AWG against JST's AWG #24 -- so 2 A is an UPPER BOUND on this exact
# connection and not a qualified figure for it.  This contract holds the board
# below the published rating and CTO_DECISIONS D-777 carries the first-article
# temperature-rise measurement that qualifies the rest.
# --------------------------------------------------------------------------
# --------------------------------------------------------------------------
# D-779 -- "A HICCUP THAT AUTO-RETRIES" IS TRUE FOR THREE TRIPS AND NOT FOR THE
# FOURTH.
#
# Every decision from D-753 onward closes its accessory-envelope reasoning with
# the same sentence: the consequence of reaching IBAT_OCP is "a hiccup that
# AUTO-RETRIES", which is what makes the recoverable protection preferable to
# the LTC4368's latching one and is why D-771 ordered them that way.  The
# ordering is right.  The consequence was stated from half the paragraph.
#
# SLUSF65B 6.3.7.3, archived and parsed here rather than quoted: the BATFET is
# re-enabled tREC_SC after each trip, BUT "if the overcurrent condition is
# triggered upon retry 4 to 7 consecutive times within a 2s window, the BATFET
# remains off until a valid VIN is connected".  A SUSTAINED accessory
# overcurrent therefore does not hiccup indefinitely -- it takes the battery
# path down and keeps it down until the user plugs in USB.  That is a
# user-visible, battery-only dead stop, and it is the reason D-775's floors and
# D-777's reserve exist rather than an argument that they are optional.
#
# THE CLAUSE IS THAT THE LIMIT IS READ.  Both the retry-count phrase and the
# recovery condition are parsed out of the archived datasheet; if either stops
# being found, the contract refuses rather than continuing to publish the
# half-sentence.
# --------------------------------------------------------------------------
RECOVERABLE_TRIP = dict(
    part="BQ25185",
    datasheet="hardware/demo/kicad/aqroot-demo/vendor/BQ25185/"
              "ti-bq25185-slusf65b-2026-08.txt",
    section="6.3.7.3 Battery Overcurrent Protection",
    retry_re=r"triggered upon retry\s*(\d+)\s*\n?\s*to\s*(\d+)\s*"
             r"consecutive times within a\s*(\d+)\s*s window",
    recovery_re=r"BATFET remains off until a valid VIN is connected",
)


def recoverable_trip_facts(spec=None):
    """What actually happens at IBAT_OCP, read out of the archived datasheet."""
    spec = RECOVERABLE_TRIP if spec is None else spec
    d = dict(part=spec["part"], section=spec["section"],
             datasheet=spec["datasheet"], retries_before_latch=None,
             window_s=None, recovers_only_on_vin=False)
    f = ROOT / spec["datasheet"]
    if f.exists():
        txt = " ".join(f.read_text(encoding="utf-8",
                                   errors="replace").split())
        m = re.search(spec["retry_re"].replace("\\n?\\s*", "\\s*"), txt)
        if m:
            d["retries_before_latch"] = [int(m.group(1)), int(m.group(2))]
            d["window_s"] = int(m.group(3))
        d["recovers_only_on_vin"] = bool(re.search(spec["recovery_re"], txt))
    d["the_retry_limit_was_read"] = (d["retries_before_latch"] is not None
                                     and d["recovers_only_on_vin"])
    d["consequence"] = (
        "IBAT_OCP hiccups and re-enables the BATFET after tREC_SC, but %s "
        "consecutive trips inside a %s s window leave the BATFET OFF until a "
        "valid VIN is connected -- a sustained accessory overcurrent is a "
        "battery-only dead stop that needs USB to clear, NOT an indefinite "
        "auto-retry" % (
            "-".join(str(x) for x in (d["retries_before_latch"] or ["?"])),
            d["window_s"]))
    return d


BATTERY_CONNECTION = dict(
    reference="J4",
    mpn="B2B-PH-K-S(LF)(SN)",
    series="JST PH",
    what="the battery connection: J4 plus the selected pack's own pigtail",
    datasheet="hardware/demo/kicad/aqroot-demo/vendor/JST/"
              "jst-ph-connector-ePH.txt",
    rating_re=r"Current\s+rating:\s*([0-9.]+)\s*A\s*AC/DC\s*[\uFF08(]\s*"
              r"AWG\s*#?\s*([0-9]+)",
    pack_spec="hardware/demo/kicad/aqroot-demo/vendor/BATTERY/"
              "adafruit-328-785060-specification.txt",
    wire_range_re=r"Conductor\s+size/?\s*AWG\s*#?\s*([0-9]+)\s*to\s*"
                  r"AWG\s*#?\s*([0-9]+)",
    pack_lead_re=r"UL\s*([0-9]+)\s*AWG",
    bom="hardware/demo/fab/aqroot-Demo-BOM-assembly.csv",
)

# THE RESERVE.  Each entry is (firmware token, the P3V3_INTERNAL_BUDGET line it
# names).  A token that matches no line -- or more than one -- is a FAILURE, so
# the firmware header cannot reserve current that no budget line accounts for,
# and a budget line cannot be renamed out from under the firmware that holds it
# off.  See aqroot_accessory_power_policy.h for why these three and not others.
P3V3_DUAL_RAIL_RESERVE = (
    ("inhibit_subghz_tx", "sub-GHz TX"),
    ("inhibit_nfc_field", "NFC front end"),
    ("inhibit_ir_tx", "IR transmitter"),
)

# The firmware-side default, mirroring NORMAL_*_VBAT_FLOOR: main() passes the
# value PARSED out of aqroot_accessory_power_policy.h, and this is what a pure
# call uses so the clause stays live inside every control.
NORMAL_DUAL_INTERNAL_CEILING_A = 0.7732


def battery_connection_facts(spec=None):
    """J4's published rating, READ rather than stated.

    Everything here comes out of an archived file: the current rating and the
    gauge it is specified at from JST's own PH datasheet text, the connector's
    applicable wire range from the same page, the selected pack's lead gauge
    from the Adafruit pack specification, and the connector MPN from the
    RELEASED BOM row.  Anything that cannot be read comes back None and the
    clause that uses it fails -- an unreadable rating is a refusal, not 2 A.
    """
    spec = BATTERY_CONNECTION if spec is None else spec
    d = dict(reference=spec["reference"], mpn=spec["mpn"],
             series=spec["series"], what=spec["what"],
             datasheet=spec["datasheet"], pack_spec=spec["pack_spec"],
             rating_A=None, rating_gauge_awg=None,
             applicable_wire_awg=None, pack_lead_awg=None,
             bom_row_names_the_connector=False)
    ds = ROOT / spec["datasheet"]
    if ds.exists():
        txt = ds.read_text(encoding="utf-8", errors="replace")
        m = re.search(spec["rating_re"], txt)
        if m:
            d["rating_A"] = float(m.group(1))
            d["rating_gauge_awg"] = int(m.group(2))
        w = re.search(spec["wire_range_re"], txt)
        if w:
            d["applicable_wire_awg"] = sorted(
                (int(w.group(1)), int(w.group(2))))
    ps = ROOT / spec["pack_spec"]
    if ps.exists():
        gauges = {int(x) for x in re.findall(
            spec["pack_lead_re"],
            ps.read_text(encoding="utf-8", errors="replace"))}
        if gauges:
            d["pack_lead_awg"] = max(gauges)      # the SMALLEST conductor
    bom = ROOT / spec["bom"]
    if bom.exists():
        for line in bom.read_text(encoding="utf-8",
                                  errors="replace").splitlines():
            head = re.match(r'\s*"([^"]*)"', line)
            refs = {x.strip() for x in (head.group(1) if head else "").split(",")}
            if spec["reference"] in refs and spec["mpn"] in line:
                d["bom_row_names_the_connector"] = True
    rng = d["applicable_wire_awg"]
    d["pack_lead_is_inside_the_applicable_wire_range"] = bool(
        rng and d["pack_lead_awg"] is not None
        and rng[0] <= d["pack_lead_awg"] <= rng[1])
    d["rating_is_specified_at_the_largest_applicable_wire"] = bool(
        rng and d["rating_gauge_awg"] == rng[0])
    d["pack_lead_is_smaller_than_the_rated_gauge"] = bool(
        d["pack_lead_awg"] is not None and d["rating_gauge_awg"] is not None
        and d["pack_lead_awg"] > d["rating_gauge_awg"])
    return d
# Read off the board rather than listed: the source of the rail, and the
# accessory switch whose current this contract budgets SEPARATELY as the whole
# point of the exercise.
P3V3_NOT_A_CONSUMER = ("U12", "U20")
P3V3_PASSIVE_PREFIXES = ("R", "C", "L", "TP", "MK", "FID", "BOSS", "#")
LTC4368_TRIP = 0.050 / 0.015           # D-753's figure, KEPT so the decision
                                       # that replaced it stays legible
FUSE_A = 5.0                           # F1 0466005 one-shot
# D-771.  AND THE CONVERTERS MUST BE ABLE TO SOURCE WHAT THE LIMITERS PERMIT.
# Nothing in this repository had ever asked whether U12 and U21 can deliver the
# current their downstream load switch is allowed to pass.  Both numbers come
# from the fitted part's own datasheet, archived under vendor/.
U12_IOUT_A = 2.0          # SLVSAA7 Features: "Output current for VIN > 2.5 V,
U12_VIN_FLOOR = 2.5       # VOUT = 3.3 V: 2 A"
U21_ILIM_VALLEY_MIN = 2.7  # SLVSF14B EC: ILIM_SW valley current limit, MIN
U21_L_H, U21_L_TOL = 1.0e-6, 0.20      # L4 Wurth 74438357010 WE-MAPI, 1 uH
U21_FSW_HZ = 1.0e6                     # SLVSF14B EC: fSW 1.0 MHz, VIN > 1.5 V


def _farads(value):
    m = re.match(r"\s*([\d.]+)\s*([munp]?)F", value or "")
    if not m:
        return None
    return float(m.group(1)) * {"": 1.0, "m": 1e-3, "u": 1e-6,
                                "n": 1e-9, "p": 1e-12}[m.group(2)]


def _ohms(value):
    m = re.match(r"\s*([\d.]+)\s*([kKmM]?)", value or "")
    if not m:
        return None
    n = float(m.group(1))
    return n * {"": 1.0, "k": 1e3, "K": 1e3, "m": 1e6, "M": 1e6}[m.group(2)]


def _milliohms(value):
    """Ohms from a milliohm sense-resistor value string such as "10mR 1% 3W".

    `_ohms` reads a bare `m` suffix as MEGohms, which is right for the signal
    resistors it was written for and catastrophically wrong for R75.  This is
    the only reader that may be pointed at a current-sense element.
    """
    m = re.match(r"\s*([\d.]+)\s*(m)(?:R|Ohm|Ω)", value or "", re.I)
    if not m:
        return None
    return float(m.group(1)) / 1000.0


def _tol(value):
    """Fractional tolerance written on the part, defaulting PESSIMISTICALLY.

    A resistor whose value string does not state a tolerance is assumed 5 %,
    so an untoleranced ILIM programming resistor is judged over a WIDER band
    rather than a narrower one.
    """
    m = re.search(r"([\d.]+)\s*%", value or "")
    return float(m.group(1)) / 100.0 if m else 0.05


def _ilim_typ(r_ohms):
    """TI equation 1, identical in SLVSFJ2B and SLVSGP6A.  Amps from ohms."""
    return 1.18 * ((r_ohms / 1000.0) ** -1.072)


# --------------------------------------------------------------------------
# F8 -- THE DERATING RULE THIS REPOSITORY STATES, APPLIED TO THE PARTS IT
# ACTUALLY FITS.  D-774.
#
# `screen_bom_sourcing.net_gate` carries the project's rule in its own words --
# *"the project's 2x derating rule against the node's OPERATING maximum, and
# plain survival against its ABSOLUTE maximum"* -- and a table, `NET_MAX_DC`,
# of every node this repository has established a voltage for.
#
# IT HAS NEVER BEEN APPLIED TO A FITTED PART.  `net_gate` runs only while the
# screen is PROPOSING a candidate for an UNSOURCED line, and this BOM has been
# fully sourced since D-615: the screen reports `unsourced_lines: 0` and the
# gate never executes.  The rule governs parts this board might buy in future
# and says nothing about the ones on it -- which is the same shape as D-771's
# published budget, D-772's internal load and D-773's setpoint, one class over.
#
# WHAT IT FINDS, AND WHAT IT DOES NOT.  Every fitted capacitor SURVIVES its
# node's absolute maximum with margin.  Five 10 V X7R parts on 5 V-class rails
# sit at 1.90-1.94x against the 2x CONVENTION, and they are accepted here with
# their numbers rather than silently passed or silently changed:
#
#   * `C20` on `USB_VBUS_RAW`, whose operating figure is the USB 2.0 SOURCE
#     MAXIMUM of 5.25 V rather than a 5.0 V nominal -- 1.90x.
#   * `C65`/`C66` (the boost output) and `C38`/`C67` (the switched rail) against
#     D-773's derived worst-case setpoint of 5.165 V -- 1.94x.
#
# WHY THEY ARE ACCEPTED.  The SAFETY limit for a ceramic is its working voltage
# against the node's ABSOLUTE maximum, and that leg holds at 1.67-1.90x on all
# five.  The 2x convention exists for DC-bias capacitance loss, and that loss is
# already IN the design: D-186 sizes the boost output at 44 uF NOMINAL (2 x
# 22 uF) precisely because a 10 V X7R at 5 V bias retains roughly half, and a
# 22 uF 16 V X7R does not exist in the fitted 0805 land -- it is a 1206 part, so
# "just fit 16 V" is a footprint change on a rail with no electrical problem.
# THE EXCEPTIONS ARE NAMED, SCOPED TO ONE REFERENCE EACH, AND CANNOT GROW
# SILENTLY: a sixth part under 2x fails this clause.
#
# THE BOUNDARY IS STATED, NOT HIDDEN.  A rating is read from the VALUE STRING,
# which 37 of the 76 fitted capacitors carry; the other 39 state only a
# capacitance and their rating lives in the sourced part record.  That count is
# PINNED, so the unrated set cannot quietly grow either.
# --------------------------------------------------------------------------
CAP_DERATE_X = 2.0
# --------------------------------------------------------------------------
# D-778 -- THE RULE WAS RUN AGAINST THE SPECIFICATION AND NOT AGAINST THE PART.
#
# D-774 read every rating out of the VALUE STRING and PINNED the 39 fitted
# capacitors whose value states only a capacitance -- honest about its own
# boundary, but it meant the rule this repository states covered barely half
# the parts on the board, and the half it covered it got WRONG in the safe
# direction.  Twenty-four value strings UNDERSTATE the part that is actually
# bought: `C20` reads `4.7uF 10V X7R` and the BOM buys `CC0805KKX7R8BB475`,
# which is **25 V**; `C38`/`C67` read 10 V and buy 25 V parts.  Three of
# D-774's five named exceptions were therefore exceptions against a rating THIS
# BOARD DOES NOT HAVE.
#
# THE RATING NOW COMES FROM THE PART.  Every fitted capacitor is joined
# BOM reference -> LCSC code -> the committed live distributor record under
# `evidence/jlc-live/`, which is the same D-096 instrument every part selection
# in this repository was confirmed against, replayed rather than re-queried so
# the answer is deterministic.  All 76 are covered; a capacitor whose record
# cannot be found is a REFUSAL, which is what replaces D-774's pinned count.
#
# AND THE SPECIFICATION IS STILL A CLAUSE, because a re-source reads it.
# Leg A is the part that is FITTED: it must survive its node's absolute maximum
# and meet the 2x convention or carry a named exception.  Leg B is the part
# that is SPECIFIED: where the value string states a rating it must also
# survive the node's absolute maximum -- so any conforming re-source is safe --
# and it may never OVERSTATE what the BOM actually buys, which is the dangerous
# direction and the one D-774 could not see at all.
#
# WHAT IS LEFT.  Against the real parts, NOTHING on this board fails its node's
# absolute maximum and NOTHING is under the 2x convention except `C65`/`C66` --
# D-186's 22 uF 10 V X7R boost-output pair, where a 16 V part in the fitted
# 0805 land does not exist and the bias loss the convention exists for is
# already in D-186's 44 uF nominal sizing.  The exception list drops from five
# to two, and `every_exception_is_still_needed` is what removed the other
# three rather than a hand edit.
# --------------------------------------------------------------------------
CAP_PURCHASED = dict(
    bom="hardware/demo/fab/aqroot-Demo-BOM-assembly.csv",
    live_cache="hardware/demo/manufacturing/evidence/jlc-live",
)
CAP_DERATE_EXCEPTIONS = {
    "C65": "boost output capacitance, measured against D-773's DERIVED "
           "worst-case setpoint of 5.165 V.  D-186 sizes this rail at 44 uF "
           "NOMINAL across C65+C66 because a 10 V X7R at 5 V bias retains about "
           "half; a 22 uF 16 V X7R is a 1206 part and does not fit the 0805 "
           "land.  Survives the 6.0 V absolute at 1.67x.  THIS ONE IS REAL: "
           "the BOM buys a 10 V part and the value string says 10 V",
    "C66": "the other half of the same 44 uF nominal pair; see C65",
}


def purchased_capacitor_ratings(spec=None):
    """{ref: the voltage rating of the part the BOM actually buys}.

    Joined reference -> LCSC -> the committed live distributor record.  The
    rating is taken from the record's own `Voltage Rating` attribute, and only
    from its free-text description if the attribute is absent, so the number is
    READ out of the archive rather than parsed out of a sentence where that can
    be avoided.  A reference with no record comes back absent and the clause
    that uses it fails.
    """
    import csv
    spec = CAP_PURCHASED if spec is None else spec
    out = {}
    bom = ROOT / spec["bom"]
    if not bom.exists():
        return out
    rows = {}
    with bom.open(encoding="utf-8", errors="replace") as fh:
        for row in csv.DictReader(fh):
            for ref in (x.strip() for x in (row.get("Refs") or "").split(",")):
                if ref:
                    rows[ref] = row
    live = {}
    cache = ROOT / spec["live_cache"]
    for f in sorted(cache.glob("*.json")) if cache.exists() else ():
        try:
            rec_file = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        for rec in rec_file.get("records", []):
            code = rec.get("componentCode")
            if code and code not in live:
                live[code] = (f.name, rec)
    for ref, row in rows.items():
        if not re.fullmatch(r"C\d+", ref):
            continue
        code = (row.get("LCSC") or "").strip()
        hit = live.get(code)
        if not hit:
            continue
        name, rec = hit
        rating, how = None, None
        for a in rec.get("attributes") or ():
            if a.get("attribute_name_en") == "Voltage Rating":
                m = re.match(r"([\d.]+)\s*V",
                             a.get("attribute_value_name") or "")
                if m:
                    rating, how = float(m.group(1)), "Voltage Rating attribute"
                break
        if rating is None:
            m = re.search(r"(\d+(?:\.\d+)?)\s*V\b", rec.get("describe") or "")
            if m:
                rating, how = float(m.group(1)), "record description"
        if rating is None:
            continue
        out[ref] = dict(lcsc=code, mpn=(row.get("MPN") or "").strip(),
                        rating_V=rating, read_from=how, record=name,
                        describe=rec.get("describe") or "")
    return out


def judge_capacitor_derating(board, dnp_refs, net_max_dc, exceptions=None,
                             purchased=None):
    """D-774, rebuilt at D-778.  The derating rule over the parts this board
    actually BUYS, and the specification a re-source would read.

    LEG A -- the FITTED part.  Its rating is the purchased part's, joined
    through the released BOM to the committed live distributor record.  It must
    survive the node's ABSOLUTE maximum, which is never excused, and meet the
    2x DERATING convention against the node's OPERATING maximum, which a named
    exception may carry.

    LEG B -- the SPECIFIED part.  Where the value string states a rating it
    must survive the node's absolute maximum too, so a conforming re-source is
    safe, and it may never state MORE than the BOM buys.
    """
    exceptions = CAP_DERATE_EXCEPTIONS if exceptions is None else exceptions
    purchased = purchased_capacitor_ratings() if purchased is None else purchased
    rows, no_record, understated = [], [], []
    fails_absolute, under_derate, unestablished = [], [], []
    spec_fails_absolute, spec_overstates = [], []
    rx = re.compile(r"(\d+(?:\.\d+)?)\s*V\b", re.I)
    for fp in board.GetFootprints():
        ref = fp.GetReference()
        if not re.fullmatch(r"C\d+", ref) or ref in dnp_refs:
            continue
        value = fp.GetValue() or ""
        m = rx.search(value)
        spec_V = float(m.group(1)) if m else None
        buy = purchased.get(ref)
        if not buy:
            no_record.append(ref)
            rows.append(dict(ref=ref, value=value,
                             no_purchased_record=True))
            continue
        rating = buy["rating_V"]
        op = ab = 0.0
        unknown = []
        for pad in fp.Pads():
            net = pad.GetNetname()
            key = net.rsplit("/", 1)[-1]
            if key == "GND" or not key:
                continue
            if key in net_max_dc:
                op = max(op, net_max_dc[key][0])
                ab = max(ab, net_max_dc[key][1])
            else:
                unknown.append(key)
        if unknown and op == 0.0:
            unestablished.append([ref, sorted(set(unknown))])
            rows.append(dict(ref=ref, value=value, rating_V=rating,
                             mpn=buy["mpn"], lcsc=buy["lcsc"],
                             nodes_not_established=sorted(set(unknown))))
            continue
        ok_abs = rating >= ab
        ok_der = rating >= CAP_DERATE_X * op
        excused = ref in exceptions
        if not ok_abs:
            fails_absolute.append([ref, buy["mpn"], rating, ab])
        if not ok_der and not excused:
            under_derate.append([ref, buy["mpn"], rating, op,
                                 round(rating / op, 3) if op else None])
        spec_ok_abs = True
        if spec_V is not None:
            spec_ok_abs = spec_V >= ab
            if not spec_ok_abs:
                spec_fails_absolute.append([ref, value, spec_V, ab])
            if spec_V > rating:
                spec_overstates.append([ref, value, spec_V, buy["mpn"], rating])
            elif spec_V < rating:
                understated.append([ref, value, spec_V, buy["mpn"], rating])
        rows.append(dict(ref=ref, value=value, mpn=buy["mpn"],
                         lcsc=buy["lcsc"], rating_V=rating,
                         rating_read_from=buy["read_from"],
                         rating_record=buy["record"],
                         specified_V=spec_V,
                         operating_V=op, absolute_V=ab,
                         derate_x=round(rating / op, 3) if op else None,
                         survives_absolute=ok_abs,
                         meets_derating=ok_der,
                         specification_survives_absolute=spec_ok_abs,
                         excused_by_a_named_exception=excused))
    fitted = len(rows)
    d = dict(
        fitted_capacitors=fitted,
        with_a_purchased_voltage_rating=fitted - len(no_record),
        without_a_purchased_record=sorted(no_record),
        with_a_rating_in_the_value_string=sum(
            1 for r in rows if r.get("specified_V") is not None),
        derating_x=CAP_DERATE_X,
        rows=sorted(rows, key=lambda r: int(r["ref"][1:])),
        named_exceptions={k: exceptions[k] for k in sorted(exceptions)},
        fails_absolute_maximum=sorted(fails_absolute),
        under_derating_without_an_exception=sorted(under_derate),
        specification_fails_absolute_maximum=sorted(spec_fails_absolute),
        specification_overstates_the_purchased_part=sorted(spec_overstates),
        specification_understates_the_purchased_part=sorted(understated),
        on_a_node_with_no_established_voltage=sorted(unestablished),
        method="screen_bom_sourcing.NET_MAX_DC, the SAME table net_gate uses, "
               "read live rather than transcribed.  RATINGS COME FROM THE PART "
               "THE BOM BUYS -- reference -> LCSC -> the committed "
               "evidence/jlc-live record, replayed not re-queried -- and the "
               "VALUE STRING is judged separately as the specification a "
               "re-source would read.  A capacitor on a node the table has no "
               "entry for is REPORTED, not refused: those that land there are "
               "the NFC matching and crystal network, C0G TUNE parts on a "
               "13.56 MHz node whose governing rating is RF PEAK and not a DC "
               "rail voltage, and inventing a DC figure for them would be the "
               "guess this table exists to avoid.  `net_gate` still REFUSES a "
               "new part grafted onto an unestablished node, which is the "
               "right answer for a part nobody has chosen yet")
    d["every_fitted_capacitor_has_a_purchased_voltage_rating"] = not no_record
    d["every_fitted_capacitor_survives_its_nodes_absolute_maximum"] = \
        not fails_absolute
    d["every_shortfall_against_the_derating_rule_is_a_named_exception"] = \
        not under_derate
    d["every_value_string_rating_survives_its_nodes_absolute_maximum"] = \
        not spec_fails_absolute
    d["no_value_string_overstates_the_part_the_bom_buys"] = not spec_overstates
    d["every_exception_is_still_needed"] = sorted(
        k for k in exceptions
        if any(r["ref"] == k and r.get("meets_derating") for r in rows)) == []
    d["ok"] = (d["every_fitted_capacitor_has_a_purchased_voltage_rating"]
               and d["every_fitted_capacitor_survives_its_nodes_absolute_maximum"]
               and d["every_shortfall_against_the_derating_rule_is_a_named_exception"]
               and d["every_value_string_rating_survives_its_nodes_absolute_maximum"]
               and d["no_value_string_overstates_the_part_the_bom_buys"]
               and d["every_exception_is_still_needed"])
    return d["ok"], d


def judge_p3v3_budget(p3v3_consumers, dnp_refs, on_board, budget=None):
    """D-772.  Pure over the board's OWN `+3V3` consumer set.

    `p3v3_consumers` is every FITTED reference with a pad on `+3V3`, already
    filtered of passives and of the two references that are not loads.  A
    consumer no budget line names is a FAILURE -- that is the whole clause, and
    it is what stops the next part put on this rail from being silently
    unbudgeted the way the NFC front end was for 27 days.

    A budget line whose references are ALL absent or DNP is also reported, so a
    line can go stale in the other direction without going unnoticed.
    """
    budget = P3V3_INTERNAL_BUDGET if budget is None else budget
    named, rows = set(), []
    for b in budget:
        live = [r for r in b["refs"] if r in p3v3_consumers]
        present = [r for r in b["refs"]
                   if r in on_board and r not in dnp_refs]
        named.update(b["refs"])
        rows.append(dict(line=b["line"], mA=b["mA"], refs=list(b["refs"]),
                         on_the_p3v3_net=live,
                         line_has_a_live_reference=bool(present),
                         cite=b["cite"]))
    unbudgeted = sorted(p3v3_consumers - named)
    dead_lines = [r["line"] for r in rows if not r["line_has_a_live_reference"]]
    total = round(sum(b["mA"] for b in budget) / 1000.0, 4)
    d = dict(
        lines=rows, total_A=total,
        fitted_p3v3_consumers=sorted(p3v3_consumers),
        unbudgeted_consumers=unbudgeted,
        budget_lines_with_no_live_reference=dead_lines,
        every_fitted_p3v3_consumer_is_budgeted=not unbudgeted,
        every_budget_line_has_a_live_reference=not dead_lines,
        superseded_published_A=I_INTERNAL_PUBLISHED_WAS,
        method="the board's own +3V3 net, minus passives and minus the rail's "
               "source (U12) and the accessory switch (U20) whose current this "
               "contract budgets separately; every remaining FITTED reference "
               "must be named by a budget line, and the envelope runs on the "
               "SUM of the lines rather than on a constant")
    d["ok"] = (d["every_fitted_p3v3_consumer_is_budgeted"]
               and d["every_budget_line_has_a_live_reference"])
    return d["ok"], d


def judge_accessory_envelope(values, single_floor=None, dual_floor=None,
                             live_ohms=None, internal_ceiling=None,
                             connection=None, reserve=None):
    """Pure over {ref: value}; returns (ok, detail).  D-753 + D-765 + D-771.

    D-753's four modes and its two refusal clauses are UNCHANGED in intent.
    D-765's three identity/range clauses are unchanged.  D-771 adds the two
    that had no words -- the PUBLISHED budget each rail must guarantee, and
    the protection chain ordered over its own TOLERANCE rather than over a
    typical -- and folds the programming resistor's tolerance into the
    envelope modes, which previously used the nominal value alone.
    """
    d, rails, parts = {}, {}, {}
    single_floor = (NORMAL_SINGLE_VBAT_FLOOR if single_floor is None
                    else single_floor)
    dual_floor = NORMAL_DUAL_VBAT_FLOOR if dual_floor is None else dual_floor
    bound_ohms = {k: v["bound_ohm"] for k, v in NORMAL_PATHS.items()}
    live_ohms = ({k: v["last_measured_ohm"] for k, v in NORMAL_PATHS.items()}
                 if live_ohms is None else live_ohms)
    internal_ceiling = (NORMAL_DUAL_INTERNAL_CEILING_A
                        if internal_ceiling is None else internal_ceiling)
    reserve = P3V3_DUAL_RAIL_RESERVE if reserve is None else reserve
    for rail, ref in ILIM_R.items():
        switch = ILIM_SWITCH[rail]
        part = (values.get(switch) or "").strip()
        rng = ILIM_SPEC_RANGE.get(part)
        r = _ohms(values.get(ref))
        if not r:
            return False, dict(error="%s value unreadable: %r" % (ref, values.get(ref)))
        tol = _tol(values.get(ref))
        typ = _ilim_typ(r)
        # The setting is judged over the RESISTOR's band, because a 1 % part at
        # its unlucky corner is still the part that gets fitted.  A smaller
        # resistor programs a LARGER limit.
        typ_hi, typ_lo = _ilim_typ(r * (1 - tol)), _ilim_typ(r * (1 + tol))
        parts[rail] = dict(
            ref=switch, value=part, known_part=rng is not None,
            spec_range_A=list(rng) if rng else None,
            setting_band_A=[round(typ_lo, 4), round(typ_hi, 4)],
            setting_inside_spec_range=bool(
                rng and rng[0] <= typ_lo and typ_hi <= rng[1]))
        # D-771: the ENVELOPE band now carries the resistor tolerance too.  It
        # used to be typ*0.68 .. typ*1.32 about the NOMINAL resistor, so a 1 %
        # part at its corner was judged by a limit no part would actually have.
        rails[rail] = dict(ref=ref, r_ohms=r, r_tol=tol,
                           ilim_min=typ_lo * ILIM_LO,
                           ilim_typ=typ,
                           ilim_max=typ_hi * ILIM_HI,
                           published_budget_A=PUBLISHED_RAIL_BUDGET_A[rail])

    # ---- D-771: the protection chain, read from the board, over tolerance --
    r75 = _milliohms(values.get(SENSE_R))
    r75_tol = _tol(values.get(SENSE_R))
    breaker_part = (values.get(BREAKER) or "").strip()
    sense_mv = BREAKER_SENSE_mV.get(breaker_part)
    if not r75 or not sense_mv:
        return False, dict(error="protection chain unreadable: %s=%r %s=%r"
                           % (SENSE_R, values.get(SENSE_R), BREAKER,
                              values.get(BREAKER)))
    breaker = dict(
        ref=BREAKER, part=breaker_part, sense_ref=SENSE_R,
        sense_ohms=r75, sense_tol=r75_tol,
        threshold_mV=list(sense_mv),
        trip_min_A=sense_mv[0] / 1000.0 / (r75 * (1 + r75_tol)),
        trip_typ_A=sense_mv[1] / 1000.0 / r75,
        trip_max_A=sense_mv[2] / 1000.0 / (r75 * (1 - r75_tol)),
        response="LATCH-OFF (RETRY grounded); cleared only by toggling SHDN",
        hard_short_threshold_mV=list(BREAKER_SENSE_HARD_SHORT_mV),
        hard_short_trip_min_A=BREAKER_SENSE_HARD_SHORT_mV[0] / 1000.0
                              / (r75 * (1 + r75_tol)),
        hard_short_row_is_reported_not_ordered_against=(
            "VIN = 12 V, VOUT = 0 V describes a COLLAPSED output; the ordering "
            "clause asks about an OVERLOAD, where VOUT tracks VIN and the "
            "40/50/60 mV row applies.  On a dead short both protections fire "
            "and latching is the wanted behaviour"))

    # ---- D-773: the 5 V setpoint, DERIVED from the board's own divider -----
    r_top, r_bot = _ohms(values.get(BOOST_FB["top"])), \
        _ohms(values.get(BOOST_FB["bottom"]))
    t_top, t_bot = _tol(values.get(BOOST_FB["top"])), \
        _tol(values.get(BOOST_FB["bottom"]))
    boost_part = (values.get(BOOST_FB["ref"]) or "").strip()
    fb_spec = BOOST_FB["parts"].get(boost_part)
    if not r_top or not r_bot or not fb_spec:
        return False, dict(error="5 V boost setpoint unreadable: %s=%r %s=%r "
                                 "%s=%r" % (BOOST_FB["top"],
                                            values.get(BOOST_FB["top"]),
                                            BOOST_FB["bottom"],
                                            values.get(BOOST_FB["bottom"]),
                                            BOOST_FB["ref"], boost_part))
    ratio_lo = (r_top * (1 - t_top)) / (r_bot * (1 + t_bot))
    ratio_hi = (r_top * (1 + t_top)) / (r_bot * (1 - t_bot))
    vref = fb_spec["vref_mV"]
    v5 = (vref[0] / 1000.0 * (1 + ratio_lo),
          vref[1] / 1000.0 * (1 + r_top / r_bot),
          vref[2] / 1000.0 * (1 + ratio_hi))
    # THE ENVELOPE RUNS ON THE WORST CASE.  A higher output costs more pack
    # current for the same delivered accessory current, and this term decides
    # the thinnest margin on this board.
    V_ACC5V = v5[2]
    boost = dict(
        ref=BOOST_FB["ref"], part=boost_part,
        top=BOOST_FB["top"], bottom=BOOST_FB["bottom"],
        top_ohms=r_top, bottom_ohms=r_bot,
        vref_mV=list(vref), vovp_V=list(fb_spec["vovp_V"]),
        setpoint_V=[round(x, 4) for x in v5],
        setpoint_used_by_the_envelope_V=round(V_ACC5V, 4),
        superseded_constant_V=4.95,
        clear_of_its_own_ovp=(v5[2] < fb_spec["vovp_V"][0]),
        ovp_margin_pct=round((fb_spec["vovp_V"][0] - v5[2])
                             / fb_spec["vovp_V"][0] * 100.0, 2),
        method="TI SLVSF14B equation 4 over the board's own R99/R100 and their "
               "1 %% bands, with the part's OWN published VREF band "
               "(580/595/610 mV PWM) -- NOT the 0.6 V both this contract's old "
               "4.95 constant and ARCHITECTURE's published 4.99 V were derived "
               "from")

    def ibat(i3, i5):
        return ((I_INTERNAL + i3) * V_3V3 / ETA_U12
                + i5 * V_ACC5V / ETA_U21) / VBAT_CORNER

    a3, a5 = rails["ACC_3V3"], rails["ACC_5V"]
    modes = dict(
        acc3v3_alone_at_its_limiter=ibat(a3["ilim_max"], 0.0),
        acc5v_alone_at_its_limiter=ibat(0.0, a5["ilim_max"]),
        both_at_their_guaranteed_currents=ibat(a3["ilim_min"], a5["ilim_min"]),
        both_at_their_published_budgets=ibat(a3["published_budget_A"],
                                             a5["published_budget_A"]),
        both_limiters_in_fault=ibat(a3["ilim_max"], a5["ilim_max"]))
    # The user-reachable set.  `both_limiters_in_fault` is NOT in it: it is two
    # simultaneous accessory overcurrents, judged separately below.
    REACHABLE = ("acc3v3_alone_at_its_limiter", "acc5v_alone_at_its_limiter",
                 "both_at_their_guaranteed_currents",
                 "both_at_their_published_budgets")
    # D-771.  The floor a reachable state must stay under is the LOWEST trip
    # ANY protection in the chain can have on ANY unit -- not the charger's
    # alone.  With R75 at 15 mOhm that floor was the charger's 2.5625 A only
    # because the breaker's 2.640 A minimum was never computed.
    first_trip_min = min(IBAT_OCP_A[0], breaker["trip_min_A"])
    d.update(rails_A={k: {kk: round(vv, 4) for kk, vv in v.items() if kk != "ref"}
                      for k, v in rails.items()},
             ilim_resistors={k: v["ref"] for k, v in rails.items()},
             modes_I_bat_A={k: round(v, 4) for k, v in modes.items()},
             ibat_ocp_A=[round(x, 4) for x in IBAT_OCP_A],
             ibat_ocp_min_A=round(IBAT_OCP_MIN, 4),
             breaker={k: (round(v, 4) if isinstance(v, float) else v)
                      for k, v in breaker.items()},
             first_trip_min_A=round(first_trip_min, 4),
             ltc4368_trip_A=round(LTC4368_TRIP, 4), fuse_A=FUSE_A,
             vbat_corner_V=VBAT_CORNER, internal_3v3_A=I_INTERNAL)
    # Every state a USER can reach with conforming accessories must stay under
    # the FIRST protection any unit can trip ...
    d["no_reachable_state_trips_the_pack"] = all(
        modes[k] < first_trip_min for k in REACHABLE)
    # ... and the DOUBLE limiter fault must still land inside the protection
    # chain rather than on the copper or the one-shot fuse.  D-771: against the
    # breaker's GUARANTEED MINIMUM, so the answer does not depend on a unit
    # happening to sit at its typical.
    d["double_fault_stays_inside_the_protection_chain"] = (
        modes["both_limiters_in_fault"] < breaker["trip_min_A"]
        and modes["both_limiters_in_fault"] < FUSE_A)
    d["margin_to_ocp_min_pct"] = round(
        (IBAT_OCP_MIN - max(modes[k] for k in REACHABLE))
        / IBAT_OCP_MIN * 100.0, 2)
    d["margin_to_first_trip_pct"] = round(
        (first_trip_min - max(modes[k] for k in REACHABLE))
        / first_trip_min * 100.0, 2)
    # ---- D-771 CLAUSE 1: the rail must DELIVER what the product publishes ---
    for rail, v in rails.items():
        v["guarantees_published_budget"] = (
            v["ilim_min"] >= v["published_budget_A"])
        v["headroom_over_published_pct"] = round(
            (v["ilim_min"] - v["published_budget_A"])
            / v["published_budget_A"] * 100.0, 2)
    d["rails_A"] = {k: {kk: (round(vv, 4) if isinstance(vv, float) else vv)
                        for kk, vv in v.items() if kk != "ref"}
                    for k, v in rails.items()}
    d["published_rail_budget_A"] = dict(PUBLISHED_RAIL_BUDGET_A)
    d["each_rail_guarantees_its_published_accessory_budget"] = all(
        v["guarantees_published_budget"] for v in rails.values())
    # ---- D-771 CLAUSE 2: the chain must be ordered over TOLERANCE -----------
    # The RECOVERABLE protection (BQ25185 IBAT_OCP: hiccup, then latch-until-
    # VIN after 4-7 trips in 2 s -- see recoverable_trip_behaviour) must
    # act before the LATCHING one (LTC4368 breaker with RETRY grounded) on
    # EVERY unit, which means its whole band must sit below the breaker's.
    d["protection_chain_A"] = dict(
        recoverable_ibat_ocp=[round(x, 4) for x in IBAT_OCP_A],
        latching_breaker=[breaker["trip_min_A"], breaker["trip_typ_A"],
                          breaker["trip_max_A"]],
        one_shot_fuse=FUSE_A)
    d["recoverable_trip_is_ordered_below_the_latching_breaker"] = (
        IBAT_OCP_A[2] < breaker["trip_min_A"])
    d["ordering_margin_pct"] = round(
        (breaker["trip_min_A"] - IBAT_OCP_A[2]) / breaker["trip_min_A"] * 100.0, 2)
    # ---- D-771 CLAUSE 3: the converters can source what the limiters allow --
    u12_load = I_INTERNAL + a3["ilim_max"]
    # TPS61023 SLVSF14B equation 1, at the cell corner, with the inductor at
    # its unlucky -20 % corner (larger ripple) and the valley limit at its MIN.
    duty = 1.0 - (VBAT_CORNER * ETA_U21 / V_ACC5V)
    d_ripple = (VBAT_CORNER * duty) / (U21_L_H * (1 - U21_L_TOL) * U21_FSW_HZ)
    u21_capability = (1.0 - duty) * (U21_ILIM_VALLEY_MIN - d_ripple / 2.0)
    d["converter_capability_A"] = dict(
        u12_part="TPS63020", u12_rated_A=U12_IOUT_A,
        u12_vin_floor_V=U12_VIN_FLOOR, u12_worst_case_load_A=round(u12_load, 4),
        u12_ok=(VBAT_CORNER > U12_VIN_FLOOR and u12_load <= U12_IOUT_A),
        u21_part="TPS61023", u21_duty=round(duty, 4),
        u21_ripple_A=round(d_ripple, 4),
        u21_capability_A=round(u21_capability, 4),
        u21_worst_case_load_A=round(a5["ilim_max"], 4),
        u21_ok=a5["ilim_max"] <= u21_capability,
        method="U12 from SLVSAA7's own Features figure at VIN > 2.5 V; U21 "
               "from SLVSF14B equation 1 with ILIM_SW at its EC MINIMUM and "
               "L4 at its -20 % corner")
    # ---- D-773 CLAUSE: the boost may not set itself into its own OVP -------
    d["boost_setpoint"] = boost
    d["boost_setpoint_is_clear_of_its_own_ovp"] = boost["clear_of_its_own_ovp"]
    # and reported beside it: what the SAME modes look like at the TYPICAL
    # setpoint, so the sensitivity of the thinnest margin is visible rather
    # than buried in one number.
    d["modes_at_typical_setpoint_A_REPORT_ONLY"] = {
        k: round(((I_INTERNAL + i3) * V_3V3 / ETA_U12
                  + i5 * v5[1] / ETA_U21) / VBAT_CORNER, 4)
        for k, (i3, i5) in dict(
            acc3v3_alone_at_its_limiter=(a3["ilim_max"], 0.0),
            acc5v_alone_at_its_limiter=(0.0, a5["ilim_max"]),
            both_at_their_guaranteed_currents=(a3["ilim_min"], a5["ilim_min"]),
            both_at_their_published_budgets=(a3["published_budget_A"],
                                             a5["published_budget_A"]),
            both_limiters_in_fault=(a3["ilim_max"], a5["ilim_max"])).items()}
    d["converters_can_source_their_worst_case_rail"] = (
        d["converter_capability_A"]["u12_ok"]
        and d["converter_capability_A"]["u21_ok"])
    # ---- D-775: THE NORMAL-OPERATION FLOOR, SOLVED FOR --------------------
    # The load-switch maxima above are FAULT ceilings.  This is the other
    # question: what does the board cost itself when it HONOURS D-098's
    # published 400 mA / 300 mA?  See the NORMAL_* comment block for why the
    # floor is derived rather than asserted and what the two earlier attempts
    # got wrong.  VCELL is BAT_PROTECTED_P, so the model starts at that node.
    k_cu = 1.0 + CU_TC_PER_K * CU_HOT_RISE_K
    r_batfet = RON_BAT_MAX_OHM * RON_BAT_VBAT_ALLOWANCE
    i3_pub, i5_pub = a3["published_budget_A"], a5["published_budget_A"]

    def _model(ohms):
        """The series terms, hot, from one set of path resistances."""
        return dict(
            bat=ohms["bat_protected_p"] * k_cu + r_batfet,
            trunk=ohms["sys_to_u21"] * k_cu,
            a3=ohms["acc_3v3_sw"] * k_cu + ACC_SWITCH_RON_OHM["ACC_3V3"],
            a5=ohms["acc_5v_sw"] * k_cu + ACC_SWITCH_RON_OHM["ACC_5V"])

    def battery_current(m, vcell, i3, i5, r_bat=None, iint=None):
        """I_bat at the MAX17048 node, sag-aware and self-consistent.

        The U12 path delivers the internal +3V3 budget plus the published
        accessory current, and pays for its own rail copper and U20's RON; the
        U21 path delivers the published 5 V current at D-773's worst-case
        setpoint, pays for ACC_5V's copper and U22's RON, and its INPUT current
        is taken through the live SYS->U21 trunk, so the trunk loss is solved
        rather than allowed for.
        """
        r_bat = m["bat"] if r_bat is None else r_bat
        iint = I_INTERNAL if iint is None else iint
        p12 = ((iint + i3) * V_3V3 + i3 * i3 * m["a3"]) / ETA_U12
        p21 = ((i5 * V_ACC5V + i5 * i5 * m["a5"]) / ETA_U21) if i5 else 0.0
        current = (p12 + p21) / vcell
        for _ in range(200):
            vsys = vcell - current * r_bat
            if vsys <= 0.0:
                return float("inf"), 0.0, 0.0
            if p21:
                iu = p21 / vsys
                for _ in range(80):
                    vin = vsys - iu * m["trunk"]
                    if vin <= 0.0:
                        return float("inf"), 0.0, 0.0
                    iu = p21 / vin
                trunk_W = iu * iu * m["trunk"]
            else:
                trunk_W = 0.0
            nxt = (p12 + p21 + trunk_W) / vsys
            if abs(nxt - current) < 1e-12:
                current = nxt
                break
            current = nxt
        return current, vsys, p12 + p21 + trunk_W

    def required_floor(m, i3, i5, margin):
        """The VCELL at which I_bat reaches IBAT_OCP_MIN less `margin`."""
        target = IBAT_OCP_MIN * (1.0 - margin)
        lo, hi = 2.5, 4.4
        for _ in range(200):
            mid = 0.5 * (lo + hi)
            if battery_current(m, mid, i3, i5)[0] > target:
                lo = mid
            else:
                hi = mid
        return hi

    def breakeven_bat_ohm(m, vcell, i3, i5, margin):
        """How large the whole BAT path could be before `vcell` stops holding."""
        target = IBAT_OCP_MIN * (1.0 - margin)
        lo, hi = 0.0, 3.0
        for _ in range(300):
            mid = 0.5 * (lo + hi)
            if battery_current(m, vcell, i3, i5, r_bat=mid)[0] <= target:
                lo = mid
            else:
                hi = mid
        return lo

    def grid_up(v):
        return math.ceil(v / FLOOR_GRID_V - 1e-9) * FLOOR_GRID_V

    LOADS = (("acc3v3_published", i3_pub, 0.0),
             ("acc5v_published", 0.0, i5_pub),
             ("both_published", i3_pub, i5_pub))
    bases, requirement = {}, {}
    for basis, ohms in (("live", live_ohms), ("path_bound", bound_ohms)):
        m = _model(ohms)
        single = max(required_floor(m, i3, i5, NORMAL_OCP_MARGIN_MIN)
                     for name, i3, i5 in LOADS if name != "both_published")
        dual = required_floor(m, i3_pub, i5_pub, NORMAL_OCP_MARGIN_MIN)
        bases[basis] = dict(
            series_ohm={k: round(v, 6) for k, v in m.items()},
            required_single_rail_floor_V=round(single, 4),
            required_dual_rail_floor_V=round(dual, 4),
            zero_margin_single_rail_floor_V=round(
                max(required_floor(m, i3, i5, 0.0)
                    for name, i3, i5 in LOADS if name != "both_published"), 4),
            zero_margin_dual_rail_floor_V=round(
                required_floor(m, i3_pub, i5_pub, 0.0), 4))
        requirement[basis] = (single, dual)
    # THE FIRMWARE MUST SATISFY THE WORSE OF THE TWO BASES.
    req_single = max(v[0] for v in requirement.values())
    req_dual = max(v[1] for v in requirement.values())
    req_single_grid, req_dual_grid = grid_up(req_single), grid_up(req_dual)

    # The cases are reported on the LIVE basis at the floors firmware enforces.
    m_live = _model(live_ohms)
    normal_cases = {}
    for name, i3, i5 in LOADS:
        floor = dual_floor if name == "both_published" else single_floor
        current, vsys, p = battery_current(m_live, floor, i3, i5)
        margin = ((IBAT_OCP_MIN - current) / IBAT_OCP_MIN
                  if current != float("inf") else -float("inf"))
        normal_cases[name] = dict(
            vcell_floor_V=round(floor, 4), delivered_W=round(p, 4),
            sys_V_at_the_floor=round(vsys, 4), battery_A=round(current, 4),
            margin_to_ibat_ocp_min_pct=round(margin * 100.0, 2),
            margin_at_least_the_convention=margin >= NORMAL_OCP_MARGIN_MIN)

    be_margin = breakeven_bat_ohm(m_live, dual_floor, i3_pub, i5_pub,
                                  NORMAL_OCP_MARGIN_MIN)
    be_trip = breakeven_bat_ohm(m_live, dual_floor, i3_pub, i5_pub, 0.0)
    live_cu_hot = live_ohms["bat_protected_p"] * k_cu

    d["normal_operation"] = dict(
        measurement_node="BAT_PROTECTED_P (MAX17048 U14.2/U14.3 and BQ25185 U11.2)",
        copper_hot_factor=round(k_cu, 4),
        copper_hot_rise_K=CU_HOT_RISE_K,
        batfet_max_ohm=RON_BAT_MAX_OHM,
        batfet_vbat_allowance=RON_BAT_VBAT_ALLOWANCE,
        batfet_modelled_ohm=round(r_batfet, 6),
        accessory_switch_ron_ohm=dict(ACC_SWITCH_RON_OHM),
        live_path_ohm={k: round(v, 6) for k, v in live_ohms.items()},
        path_bound_ohm={k: v["bound_ohm"] for k, v in NORMAL_PATHS.items()},
        every_live_path_inside_its_bound=all(
            live_ohms[k] <= v["bound_ohm"] for k, v in NORMAL_PATHS.items()),
        bases=bases,
        required_single_rail_floor_V=round(req_single, 4),
        required_dual_rail_floor_V=round(req_dual, 4),
        required_single_rail_floor_gridded_V=round(req_single_grid, 4),
        required_dual_rail_floor_gridded_V=round(req_dual_grid, 4),
        floor_grid_V=FLOOR_GRID_V,
        firmware_single_rail_floor_V=single_floor,
        firmware_dual_rail_floor_V=dual_floor,
        required_margin_to_ibat_ocp_min_pct=NORMAL_OCP_MARGIN_MIN * 100.0,
        ibat_ocp_min_A=round(IBAT_OCP_MIN, 4),
        cases=normal_cases,
        batfet_breakeven_ohm=dict(
            at_the_margin_convention=round(be_margin - live_cu_hot, 6),
            at_the_ibat_ocp_minimum=round(be_trip - live_cu_hot, 6),
            as_a_multiple_of_the_datasheet_max=dict(
                at_the_margin_convention=round(
                    (be_margin - live_cu_hot) / RON_BAT_MAX_OHM, 3),
                at_the_ibat_ocp_minimum=round(
                    (be_trip - live_cu_hot) / RON_BAT_MAX_OHM, 3))),
        method="the floor is SOLVED FOR, not checked at: I_bat is found "
               "self-consistently from the MAX17048 BAT_PROTECTED_P node "
               "through the live hot copper and the BQ25185 BATFET maximum, "
               "with the U21 boost's input current taken through the live "
               "SYS->U21 trunk and each accessory rail paying for its own "
               "copper and its load switch's RON; required_*_floor_V is the "
               "VCELL at which that current reaches IBAT_OCP's minimum less "
               "the margin convention, derived on BOTH the live resistances "
               "and the declared path ceilings, and the firmware constants "
               "must satisfy the worse of the two")
    # ---- D-777: THE BATTERY CONNECTION'S OWN PUBLISHED RATING -------------
    # Same model, one more limit -- and the limit is the LOWEST in the path.
    # The question this answers is not "does the silicon survive" but "does any
    # state firmware is allowed to enter put more current through J4 than JST
    # publishes for it".
    conn = battery_connection_facts(connection)
    rating = conn["rating_A"]

    reserve_rows, reserve_A, reserve_named_ok = [], 0.0, True
    for token, line_key in reserve:
        hits = [x for x in P3V3_INTERNAL_BUDGET if line_key in x["line"]]
        exact = (len(hits) == 1)
        reserve_named_ok = reserve_named_ok and exact
        reserve_A += sum(x["mA"] for x in hits) / 1000.0
        reserve_rows.append(dict(
            firmware_token=token, budget_line=line_key,
            matched=[x["line"] for x in hits],
            refs=sorted({r for x in hits for r in x["refs"]}),
            mA=round(sum(x["mA"] for x in hits), 4),
            names_exactly_one_budget_line=exact))
    reserved_internal = round(I_INTERNAL - reserve_A, 6)

    def _required_internal(m, vcell, i3, i5, cap):
        """The internal +3V3 current at which I_bat reaches `cap` exactly."""
        lo, hi = 0.0, 4.0
        for _ in range(300):
            mid = 0.5 * (lo + hi)
            if battery_current(m, vcell, i3, i5, iint=mid)[0] <= cap:
                lo = mid
            else:
                hi = mid
        return lo

    # PERMITTED states only.  Each rail alone runs at its full published budget
    # down to the single-rail floor with the WHOLE internal budget live; both
    # together run only at or above the dual-rail floor and only with the
    # reserve held off.  `both_published_without_the_reserve` is carried
    # alongside as the figure the reserve exists to remove -- it is REPORTED,
    # never a pass condition, and it is what makes this clause non-vacuous.
    PERMITTED = (
        ("no_accessory", 0.0, 0.0, I_INTERNAL, "single"),
        ("acc3v3_published", i3_pub, 0.0, I_INTERNAL, "single"),
        ("acc5v_published", 0.0, i5_pub, I_INTERNAL, "single"),
        ("both_published_with_the_reserve", i3_pub, i5_pub,
         reserved_internal, "dual"))
    conn_cases, conn_within = {}, (rating is not None)
    for basis, ohms in (("live", live_ohms), ("path_bound", bound_ohms)):
        m = _model(ohms)
        rows = {}
        for name, i3, i5, iint, which in PERMITTED:
            floor = dual_floor if which == "dual" else single_floor
            cur = battery_current(m, floor, i3, i5, iint=iint)[0]
            inside = (rating is not None and cur <= rating + 1e-9)
            conn_within = conn_within and inside
            rows[name] = dict(
                vcell_V=round(floor, 4), internal_3v3_A=round(iint, 4),
                acc3v3_A=i3, acc5v_A=i5,
                connection_A=(round(cur, 4) if cur != float("inf")
                              else "no-converge"),
                margin_to_the_published_rating_pct=(
                    round((rating - cur) / rating * 100.0, 2)
                    if rating and cur != float("inf") else None),
                inside_the_published_rating=inside)
        cur = battery_current(m, dual_floor, i3_pub, i5_pub,
                              iint=I_INTERNAL)[0]
        rows["both_published_without_the_reserve"] = dict(
            vcell_V=round(dual_floor, 4), internal_3v3_A=I_INTERNAL,
            acc3v3_A=i3_pub, acc5v_A=i5_pub,
            connection_A=round(cur, 4),
            margin_to_the_published_rating_pct=(
                round((rating - cur) / rating * 100.0, 2) if rating else None),
            inside_the_published_rating=(rating is not None
                                         and cur <= rating + 1e-9),
            note="REPORTED, NOT A PASS CONDITION.  This is the state D-775 "
                 "permitted and D-777 removed; if it ever comes back inside "
                 "the rating on its own the reserve is no longer load-bearing "
                 "and reserve_is_load_bearing goes false")
        req = _required_internal(m, dual_floor, i3_pub, i5_pub, rating) \
            if rating is not None else float("nan")
        vcell_for_full = None
        if rating is not None:
            lo, hi = 2.5, 6.0
            for _ in range(300):
                mid = 0.5 * (lo + hi)
                if battery_current(m, mid, i3_pub, i5_pub,
                                   iint=I_INTERNAL)[0] > rating:
                    lo = mid
                else:
                    hi = mid
            vcell_for_full = round(hi, 4)
        conn_cases[basis] = dict(
            cases=rows,
            required_internal_3v3_ceiling_A=(round(req, 6)
                                             if req == req else None),
            vcell_the_full_budget_would_need_V=vcell_for_full)
    # THE RESIDUAL, MEASURED RATHER THAN NARRATED.  This board has no accessory
    # current measurement, so an accessory that draws MORE than its published
    # budget is not refusable.  What IS derivable is how far over it has to go
    # before the connection leaves its rating, and how far before the charger's
    # own hiccup takes over -- the band between those two is the only state in
    # which J4 is over its rating with nothing acting.
    residual = dict(
        basis="live", vcell_V=round(dual_floor, 4),
        acc3v3_held_at_A=i3_pub, internal_3v3_A=reserved_internal)
    if rating is not None:
        def _i5_reaching(cap):
            lo, hi = 0.0, 2.0
            for _ in range(200):
                mid = 0.5 * (lo + hi)
                if battery_current(m_live, dual_floor, i3_pub, mid,
                                   iint=reserved_internal)[0] <= cap:
                    lo = mid
                else:
                    hi = mid
            return lo
        at_rating, at_ocp = _i5_reaching(rating), _i5_reaching(IBAT_OCP_MIN)
        residual.update(
            acc5v_draw_that_reaches_the_rating_A=round(at_rating, 4),
            acc5v_draw_that_reaches_ibat_ocp_min_A=round(at_ocp, 4),
            overdraw_to_reach_the_rating_pct=round(
                (at_rating / i5_pub - 1.0) * 100.0, 1),
            overdraw_to_reach_ibat_ocp_min_pct=round(
                (at_ocp / i5_pub - 1.0) * 100.0, 1),
            note="an accessory must exceed its PUBLISHED 5 V budget by the "
                 "first figure before the connection leaves its rating and by "
                 "the second before the BQ25185 hiccups; between them nothing "
                 "on this board acts.  Above it the charger's hiccup makes the "
                 "connector's duty low.  D-777 names this and does not close "
                 "it: closing it needs accessory current measurement or a "
                 "connector rated above IBAT_OCP's minimum")
    req_ceiling = min(v["required_internal_3v3_ceiling_A"]
                      for v in conn_cases.values()
                      if v["required_internal_3v3_ceiling_A"] is not None) \
        if rating is not None else None
    reserve_load_bearing = any(
        not v["cases"]["both_published_without_the_reserve"][
            "inside_the_published_rating"] for v in conn_cases.values())

    trip = recoverable_trip_facts()
    d["recoverable_trip_behaviour"] = trip
    d["the_recoverable_trips_retry_limit_was_read"] = trip[
        "the_retry_limit_was_read"]

    d["battery_connection"] = dict(
        conn, rating_A=rating,
        first_protection_that_acts_A=round(IBAT_OCP_MIN, 4),
        unprotected_band_A=([rating, round(IBAT_OCP_MIN, 4)]
                            if rating is not None else None),
        reserve=reserve_rows,
        residual_overdraw_band=residual,
        reserve_total_A=round(reserve_A, 4),
        full_internal_3v3_A=I_INTERNAL,
        reserved_internal_3v3_A=reserved_internal,
        firmware_internal_ceiling_A=internal_ceiling,
        required_internal_3v3_ceiling_A=(round(req_ceiling, 6)
                                         if req_ceiling is not None else None),
        bases=conn_cases,
        reserve_is_load_bearing=reserve_load_bearing,
        method="the rating, the gauge it is specified at, the connector's "
               "applicable wire range and the pack's own lead gauge are all "
               "PARSED out of archived vendor text; the currents are the same "
               "self-consistent sag model D-775 derives the VCELL floors from, "
               "evaluated at the floors firmware enforces, on BOTH the live "
               "resistances and the declared path ceilings")
    d["battery_connection_rating_was_read_not_asserted"] = (
        rating is not None and conn["rating_gauge_awg"] is not None
        and conn["applicable_wire_awg"] is not None
        and conn["pack_lead_awg"] is not None)
    d["released_bom_names_the_connector_the_rating_belongs_to"] = conn[
        "bom_row_names_the_connector"]
    d["pack_lead_is_inside_the_connectors_applicable_wire_range"] = conn[
        "pack_lead_is_inside_the_applicable_wire_range"]
    d["every_permitted_state_is_inside_the_connections_published_rating"] = \
        conn_within
    d["every_reserve_token_names_exactly_one_budget_line"] = reserve_named_ok
    d["firmware_internal_ceiling_meets_the_derived_requirement"] = (
        req_ceiling is not None
        and internal_ceiling <= req_ceiling + 1e-9)
    d["the_named_reserve_reaches_the_firmware_ceiling"] = (
        reserved_internal <= internal_ceiling + 1e-9)
    d["the_reserve_is_load_bearing"] = reserve_load_bearing

    d["firmware_floors_meet_the_derived_requirement"] = (
        single_floor >= req_single_grid - 1e-9
        and dual_floor >= req_dual_grid - 1e-9)
    d["published_normal_load_respects_vcell_policy"] = all(
        row["margin_at_least_the_convention"] for row in normal_cases.values())
    d["every_live_normal_path_is_inside_its_bound"] = (
        d["normal_operation"]["every_live_path_inside_its_bound"])

    # ---- D-765: the three clauses that had no words before -----------------
    d["limiter_parts"] = parts
    d["ul2367_ilim_range_A"] = list(UL2367_ILIM_RANGE)
    d["limiter_silicon_is_a_part_with_a_published_range"] = all(
        p["known_part"] for p in parts.values())
    d["ilim_setting_is_inside_the_parts_own_spec_range"] = all(
        p["setting_inside_spec_range"] for p in parts.values())
    d["one_limiter_mpn_on_both_rails"] = (
        len({p["value"] for p in parts.values()}) == 1)
    # The UL 2367 recognition range is a narrower, safety-credential bound on
    # the same quantity.  Its LOWER bound is exercised by the f6h control; any
    # setting that breaches its UPPER bound also breaches the pack clause.
    d["ilim_band_is_inside_ul2367_recognition"] = all(
        UL2367_ILIM_RANGE[0] <= v["ilim_min"]
        and v["ilim_max"] <= UL2367_ILIM_RANGE[1] for v in rails.values())
    ok = (d["no_reachable_state_trips_the_pack"]
          and d["double_fault_stays_inside_the_protection_chain"]
          and d["limiter_silicon_is_a_part_with_a_published_range"]
          and d["ilim_setting_is_inside_the_parts_own_spec_range"]
          and d["one_limiter_mpn_on_both_rails"]
          and d["ilim_band_is_inside_ul2367_recognition"]
          and d["each_rail_guarantees_its_published_accessory_budget"]
          and d["recoverable_trip_is_ordered_below_the_latching_breaker"]
          and d["converters_can_source_their_worst_case_rail"]
          and d["boost_setpoint_is_clear_of_its_own_ovp"]
          and d["published_normal_load_respects_vcell_policy"]
          and d["firmware_floors_meet_the_derived_requirement"]
          and d["every_live_normal_path_is_inside_its_bound"]
          # ---- D-777 ----
          and d["battery_connection_rating_was_read_not_asserted"]
          and d["released_bom_names_the_connector_the_rating_belongs_to"]
          and d["pack_lead_is_inside_the_connectors_applicable_wire_range"]
          and d["every_permitted_state_is_inside_the_connections_published_rating"]
          and d["every_reserve_token_names_exactly_one_budget_line"]
          and d["firmware_internal_ceiling_meets_the_derived_requirement"]
          and d["the_named_reserve_reaches_the_firmware_ceiling"]
          and d["the_reserve_is_load_bearing"]
          and d["the_recoverable_trips_retry_limit_was_read"])
    return ok, d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-o", dest="out", type=Path)
    args = ap.parse_args()

    ledger = rl.generate()
    by_net = {n["net"]: n for n in ledger["nets"]}
    fitted = set()
    import pcbnew
    board = pcbnew.LoadBoard(str(rl.BOARD.resolve()))
    on_board = {f.GetReference() for f in board.GetFootprints()}
    sch_fitted, sch_dnp = rl.schematic_population()

    missing_refs, dnp_refs, bad_nets = [], [], []
    rows = []
    for f in FEATURES:
        miss = [r for r in f["refs"] if r not in on_board]
        dnp = [r for r in f["refs"] if r in sch_dnp]
        nets = []
        for n in f["nets"]:
            row = by_net.get(n)
            if row is None:
                nets.append(dict(net=n, present=False))
                bad_nets.append((f["scope"], n, "ABSENT or single-pad"))
                continue
            ok = row["unapproved_open_edges"] == 0
            nets.append(dict(net=n, present=True, pads=row["pads"],
                             open_edges=row["open_edges"],
                             approved_unrouted_edges=row["approved_unrouted_edges"],
                             unapproved_open_edges=row["unapproved_open_edges"],
                             ok=ok))
            if not ok:
                bad_nets.append((f["scope"], n, "unapproved open edge"))
        missing_refs += [(f["scope"], r) for r in miss]
        dnp_refs += [(f["scope"], r) for r in dnp]
        rows.append(dict(scope=f["scope"], note=f.get("note"),
                         refs=list(f["refs"]), missing_refs=miss, dnp_refs=dnp,
                         nets=nets,
                         ok=not miss and not dnp and all(
                             n.get("ok", False) or not n.get("present", False) is False
                             for n in nets) and not any(
                             (not n.get("present")) or (not n.get("ok", True)) for n in nets)))

    # ---- F4: every exposed J5 SIGNAL contact must reach an ESD array -------
    # Derived from the connector, not from a list, so a future revision that
    # exposes a contact without protection fails here rather than in the field.
    # D-188's own words: "shipping a user-accessible connector with ten
    # unprotected signal contacts is not a defensible state".
    esd_nets = set()
    for fp in board.GetFootprints():
        if "TPD4E1B06" in (fp.GetValue() or ""):
            for pd in fp.Pads():
                n = pd.GetNetname()
                if n and n != "GND" and not n.startswith("unconnected-"):
                    esd_nets.add(n)
    POWER_OR_GND = {"GND", "/ACC_3V3_SW", "/ACC_5V_SW"}
    j5 = [f for f in board.GetFootprints() if f.GetReference() == "J5"]
    j5_rows, unprotected = [], []
    for pd in (j5[0].Pads() if j5 else ()):
        contact = "J5.%s" % pd.GetNumber()
        net = pd.GetNetname()
        if contact in EXPECTED_NC or not net or net.startswith("unconnected-"):
            kind = "approved NC"
        elif net in POWER_OR_GND:
            kind = "power or ground"
        else:
            kind = "signal"
            if net not in esd_nets:
                unprotected.append([contact, net])
        j5_rows.append(dict(contact=contact, net=net, kind=kind,
                            esd=net in esd_nets))

    # ---- F5: the backlight disconnect's control, and three live controls --
    nets_by_contact, values = {}, {}
    for fp in board.GetFootprints():
        ref = fp.GetReference()
        values[ref] = fp.GetValue() or ""
        for pd in fp.Pads():
            if pd.GetNumber():
                nets_by_contact["%s.%s" % (ref, pd.GetNumber())] = pd.GetNetname()
    bl_ok, bl = judge_backlight(nets_by_contact, values)

    def _control(name, mutate):
        n2, v2 = dict(nets_by_contact), dict(values)
        mutate(n2, v2)
        ok, _ = judge_backlight(n2, v2)
        return name, not ok            # a control PASSES when F5 REFUSES it

    def _collapse(n, v):
        n[BL_GATE] = n["U17.4"]

    def _drop_hold_cap(n, v):
        n["C85.1"] = "Net-(C85-Pad1)"

    def _schottky(n, v):
        v["D14"] = "BAT54WS"

    def _wrong_tau(n, v):
        v["R132"] = "10k"

    bl_controls = dict(x for x in (
        _control("f5a_refuses_the_gate_collapsed_onto_u17_ctrl", _collapse),
        _control("f5b_refuses_the_hold_capacitor_dropped", _drop_hold_cap),
        _control("f5c_refuses_a_schottky_in_the_charge_path", _schottky),
        _control("f5d_refuses_a_silently_retuned_hold", _wrong_tau)))

    # ---- D-766: and the FET itself, against the ceiling THIS board publishes
    dru_text = DRU.read_text(encoding="utf-8", errors="replace") if DRU.exists() \
        else ""
    fet_ok, fet = judge_backlight_fet(values, dru_text)

    def _fet_control(name, mutate):
        v2 = dict(values)
        mutate(v2)
        ok, _ = judge_backlight_fet(v2, dru_text)
        return name, not ok

    def _fet_control_dru(name, text):
        ok, _ = judge_backlight_fet(values, text)
        return name, not ok

    fet_controls = dict(x for x in (
        # THE LOAD-BEARING ONE: the board D-752 shipped.  Nothing changes but
        # the silicon, every sequencing clause above still passes, and the
        # 30 V rating alone refuses it against the 39 V this board publishes.
        _fet_control("f5e_refuses_the_30V_ao3400a_d752_left_fitted",
                     lambda v: v.__setitem__(BL_FET, "AO3400A")),
        _fet_control("f5f_refuses_a_fet_with_no_published_rating",
                     lambda v: v.__setitem__(BL_FET, "SOME-FET-1234")),
        # a hold capacitor small enough to let the gate reach the FITTED part's
        # worst-case threshold before the TPS61169's 2.5 ms tSD
        _fet_control("f5g_refuses_a_hold_that_opens_before_u17_shuts_down",
                     lambda v: v.__setitem__("C85", "1nF X7R")),
        # and the ceiling must come from the rules file, not from this contract
        _fet_control_dru("f5h_refuses_a_dru_that_no_longer_publishes_a_ceiling",
                         "no ceiling is stated anywhere in this text"),
        # the boost rectifier stands off the same ceiling in reverse
        _fet_control("f5i_refuses_a_20V_schottky_on_the_boost_rectifier",
                     lambda v: v.__setitem__(BL_RECTIFIER, "PMEG2010AEH")),
        _fet_control("f5j_refuses_a_rectifier_with_no_published_rating",
                     lambda v: v.__setitem__(BL_RECTIFIER, "SOME-DIODE-99")),
        # ---- D-779's two.  THE LOAD-BEARING ONE IS THE BOARD D-766 SHIPPED:
        # 100 nF, which still clears the VGS(th) criterion at 2.06x and is
        # refused only by the clause that asks whether the ordering depends on
        # the AO3422's UNPUBLISHED conduction band.  At 100 nF the window in
        # which it can fail is 407 mV against a 104 mV bar; at 1 uF it is 44 mV.
        _fet_control("f5k_refuses_the_100nF_hold_d766_shipped",
                     lambda v: v.__setitem__("C85", "100nF X7R")),
        # and a part whose datasheet gives no guaranteed conduction point
        # cannot be judged against that bar at all, so it is refused rather
        # than passed on the threshold clause alone
        _fet_control("f5l_refuses_a_fet_with_no_published_conduction_point",
                     lambda v: v.__setitem__(BL_FET, "AO3400A_NO_RDS_ON"))))

    # ---- F6: the accessory envelope, and four live controls ---------------
    # D-772 FIRST: the internal +3V3 budget the envelope RUNS ON, read from the
    # board's own net rather than taken on trust.
    p3v3_consumers = set()
    for fp in board.GetFootprints():
        ref = fp.GetReference()
        if ref in P3V3_NOT_A_CONSUMER or ref in sch_dnp:
            continue
        if ref.startswith(P3V3_PASSIVE_PREFIXES):
            continue
        if any(p.GetNetname() == "+3V3" for p in fp.Pads()):
            p3v3_consumers.add(ref)
    budget_ok, budget = judge_p3v3_budget(p3v3_consumers, sch_dnp, on_board)

    def _budget_control(name, mutate_budget):
        b2 = mutate_budget([dict(x) for x in P3V3_INTERNAL_BUDGET])
        ok, _ = judge_p3v3_budget(p3v3_consumers, sch_dnp, on_board,
                                  budget=b2)
        return name, not ok

    budget_controls = dict(x for x in (
        # THE LOAD-BEARING ONE: this is the budget as it actually stood before
        # D-772 -- the NFC line simply absent, which is how the 823 mA figure
        # was carried from D-192 onward while U9 sat FITTED on the rail.
        _budget_control("f6o_refuses_the_budget_with_the_nfc_line_missing",
                        lambda b: [x for x in b
                                   if "NFC front end" not in x["line"]]),
        # any consumer dropped is the same defect one part over
        _budget_control("f6p_refuses_a_budget_that_forgets_the_microsd",
                        lambda b: [x for x in b if "microSD" not in x["line"]]),
        _budget_control("f6q_refuses_a_budget_that_forgets_the_audio_amp",
                        lambda b: [x for x in b if "audio" not in x["line"]]),
        # and a line whose parts have all left the board is stale in the other
        # direction: it inflates the budget with current nothing draws
        _budget_control("f6r_refuses_a_budget_line_with_no_live_reference",
                        lambda b: b + [dict(line="a part that is not on this "
                                                 "board", mA=500.0,
                                            refs=("U999",), cite="control")])))

    # D-775: bind the derived floor to the ACTUAL firmware policy, to the
    # MAX17048 measurement node, and to the FOUR live resistances the
    # derivation needs.  This closes a cross-domain hole in both directions: a
    # correct analytical floor is useless if firmware does not enforce it, and
    # a firmware constant is not proof of the power model.
    policy_text = POWER_POLICY.read_text(encoding="utf-8") if POWER_POLICY.exists() else ""
    sm = re.search(r"kAccessorySingleRailFloorV\s*=\s*([0-9.]+)f", policy_text)
    dm = re.search(r"kAccessoryDualRailFloorV\s*=\s*([0-9.]+)f", policy_text)
    policy_single = float(sm.group(1)) if sm else float("nan")
    policy_dual = float(dm.group(1)) if dm else float("nan")
    # D-777: the internal reserve, read out of the SAME header.  A ceiling with
    # no reserve behind it, or a reserve token the header does not declare, is
    # the cross-domain hole D-775 closed for the floors, one term over.
    cm = re.search(r"kDualRailInternalCeilingA\s*=\s*([0-9.]+)f", policy_text)
    policy_ceiling = float(cm.group(1)) if cm else float("nan")
    policy_reserve_tokens = set(re.findall(r"\binhibit_[a-z0-9_]+\b",
                                           policy_text))
    reserve_tokens_declared = {
        tok: (tok in policy_reserve_tokens)
        for tok, _ in P3V3_DUAL_RAIL_RESERVE}

    # THE MEASUREMENT POINT IS A CLAUSE, not a comment: the whole model rests
    # on the gauge reading the SAME node U11's BAT pin sits on.
    measurement_contacts = ("U14.2", "U14.3", "U11.2")
    measurement_nets = {c: nets_by_contact.get(c) for c in measurement_contacts}
    measurement_ok = all(measurement_nets[c] == "/01_POWER_TREE/BAT_PROTECTED_P"
                         for c in measurement_contacts)

    pad_index = {"%s.%s" % (fp.GetReference(), pd.GetNumber()): pd
                 for fp in board.GetFootprints() for pd in fp.Pads()
                 if pd.GetNumber()}
    rails_by_name = {r["name"]: r for r in ara.RAILS}

    def _live_series_ohm(key):
        """Series resistance of one NORMAL_PATHS entry, off the live board."""
        spec = NORMAL_PATHS[key]
        rail = rails_by_name[spec["rail"]]
        nodes, edges = ara.build_graph(board, rail["net"])
        src = [ara.pad_key(pad_index[r]) for r in spec["src"] if r in pad_index]
        snk = [ara.pad_key(pad_index[r]) for r in spec["snk"] if r in pad_index]
        if not src or not snk:
            return float("inf")
        path, _ = ara.widest_bottleneck(nodes, edges, src, snk, rail["amps"])
        if not path:
            return float("inf")
        return sum(ara.RHO_CU * e["length_mm"] / e["area_mm2"] for e in path
                   if e["kind"] != "pad" and e["area_mm2"])

    live_ohms = {k: _live_series_ohm(k) for k in NORMAL_PATHS}

    env_ok, env = judge_accessory_envelope(
        values, single_floor=policy_single, dual_floor=policy_dual,
        live_ohms=live_ohms, internal_ceiling=policy_ceiling)
    env["normal_operation"]["firmware_policy_file"] = str(
        POWER_POLICY.relative_to(ROOT)) if POWER_POLICY.exists() else None
    env["normal_operation"]["measurement_contacts"] = measurement_nets
    env["normal_operation"]["measurement_point_is_bat_protected_p"] = measurement_ok
    env["normal_operation"]["firmware_policy_parsed"] = (
        math.isfinite(policy_single) and math.isfinite(policy_dual))
    env["battery_connection"]["firmware_reserve_tokens_declared"] = \
        reserve_tokens_declared
    env["battery_connection"]["firmware_ceiling_parsed"] = math.isfinite(
        policy_ceiling)
    env["firmware_declares_every_reserve_token_it_must_hold_off"] = (
        math.isfinite(policy_ceiling) and all(reserve_tokens_declared.values()))
    env["normal_operation"]["live_paths_measured_off_the_board"] = True
    env_ok = (env_ok and measurement_ok
              and math.isfinite(policy_single) and math.isfinite(policy_dual)
              and env["firmware_declares_every_reserve_token_it_must_hold_off"])

    env["p3v3_internal_budget"] = budget
    env["internal_3v3_A"] = I_INTERNAL
    env["every_fitted_p3v3_consumer_is_budgeted"] = budget[
        "every_fitted_p3v3_consumer_is_budgeted"]
    env["every_p3v3_budget_line_has_a_live_reference"] = budget[
        "every_budget_line_has_a_live_reference"]
    env_ok = env_ok and budget_ok

    def _env_control(name, mutate):
        v2 = dict(values)
        mutate(v2)
        ok, _ = judge_accessory_envelope(v2)
        return name, not ok

    def _env_policy_control(name, single_floor=None, dual_floor=None,
                            internal_ceiling=None, connection=None,
                            reserve=None):
        ok, _ = judge_accessory_envelope(
            values,
            single_floor=(policy_single if single_floor is None else single_floor),
            dual_floor=(policy_dual if dual_floor is None else dual_floor),
            internal_ceiling=(policy_ceiling if internal_ceiling is None
                              else internal_ceiling),
            connection=connection, reserve=reserve)
        return name, not ok

    env_controls = dict(x for x in (
        # D-753's four.  These prove the arithmetic still refuses a limit set
        # too HIGH -- the defect D-753 itself existed to remove.  D-771 MOVED
        # f6a's refusing clause and says so rather than leaving the old
        # sentence standing: with the 5 V rail retuned, 1.5 kOhm on R97 no
        # longer reaches the pack's trip, and it is now refused -- ALONE -- by
        # the converter-capability clause, because 1.019 A of worst-case
        # accessory plus the 1.0 A internal budget is more than the TPS63020's
        # own rated 2 A.  A control that refuses for a different reason than
        # its name claims is the defect D-767 named; the name is corrected.
        _env_control("f6a_refuses_the_d750_acc3v3_ilim_u12_cannot_source",
                     lambda v: v.__setitem__("R97", "1.5k 1%")),
        _env_control("f6b_refuses_the_d750_acc5v_ilim",
                     lambda v: v.__setitem__("R101", "1.65k 1%")),
        _env_control("f6c_refuses_a_1k_ilim_on_either_rail",
                     lambda v: v.__setitem__("R101", "1k")),
        _env_control("f6d_refuses_an_unreadable_ilim_value",
                     lambda v: v.__setitem__("R97", "DNP")),
        # D-765's four.  f6e and f6f are the LOAD-BEARING ones: they change
        # NOTHING but the silicon, leave every D-753 mode passing, and are
        # refused only by the new spec-range clause.  f6e IS the board D-753
        # shipped.
        _env_control("f6e_refuses_the_board_d753_actually_shipped",
                     lambda v: v.update(U20="TPS22950C", U22="TPS22950C")),
        _env_control("f6f_refuses_two_different_limiter_mpns",
                     lambda v: v.__setitem__("U22", "TPS22950C")),
        _env_control("f6g_refuses_a_limiter_with_no_published_ilim_range",
                     lambda v: v.__setitem__("U20", "TPS22918")),
        _env_control("f6h_refuses_an_ilim_under_the_parts_own_floor",
                     lambda v: v.__setitem__("R97", "20k 1%")),
        # ---- D-771's six.  The first two are the LOAD-BEARING pair: each is
        # the board a previous decision shipped, and each is refused by a
        # clause that decision's contract could not state.
        # f6i IS THE BOARD D-765 SHIPPED -- 2.7 kOhm on both rails, which
        # guarantees 0.277 A against a PUBLISHED 400 mA / 300 mA.
        _env_control("f6i_refuses_the_board_d765_actually_shipped",
                     lambda v: v.update(R97="2.7k 1%", R101="2.7k 1%")),
        # f6j IS THE SENSE RESISTOR D-765 SHIPPED -- 15 mOhm, which puts the
        # LATCHING breaker's 2.640 A minimum BELOW the recoverable charger
        # trip's 3.6875 A maximum.  Nothing else changes.
        _env_control("f6j_refuses_the_15mOhm_sense_that_overlapped_the_charger",
                     lambda v: v.__setitem__("R75", "15mR 1% 1W")),
        # the published budget must be met on EITHER rail, not just one
        _env_control("f6k_refuses_an_acc5v_ilim_below_the_published_300mA",
                     lambda v: v.__setitem__("R101", "3.3k 1%")),
        # the chain must be READ, not assumed: an unreadable sense element or
        # a breaker this contract has no threshold table for is a refusal,
        # exactly as an unknown limiter MPN is
        _env_control("f6l_refuses_an_unreadable_sense_resistor",
                     lambda v: v.__setitem__("R75", "DNP")),
        _env_control("f6m_refuses_a_breaker_with_no_published_threshold",
                     lambda v: v.__setitem__("U18", "LTC4368-9")),
        # and a limiter the CONVERTER cannot feed is refused even when every
        # battery-side mode passes
        _env_control("f6n_refuses_an_acc3v3_ilim_past_both_bounds",
                     lambda v: v.__setitem__("R97", "1.3k 1%")),
        # ---- D-773's three.
        # THE HONEST STATEMENT OF WHAT MOVED.  D-771's 2.32 kOhm is NOT refused
        # by any clause here and D-773 does not pretend otherwise: at the
        # setpoint this contract now DERIVES it leaves 0.52 % of pack margin,
        # which is a MARGIN the engineering judgement moved, not a clause it
        # broke.  What IS refused is a setting past the bound -- 2.2 kOhm, just
        # below the 2.298 kOhm where the limiter's worst case reaches the pack's
        # own minimum trip at that setpoint.  A control whose name claims a
        # refusal its clause does not make is the defect D-767 named.
        _env_control("f6s_refuses_an_acc5v_ilim_past_the_pack_bound",
                     lambda v: v.__setitem__("R101", "2.2k 1%")),
        # the divider must be READ, and a boost this contract has no VREF
        # table for is a refusal exactly as an unknown limiter MPN is
        _env_control("f6t_refuses_a_boost_with_no_published_vref_band",
                     lambda v: v.__setitem__("U21", "TPS61023X")),
        # and a divider whose worst-case HIGH reaches the part's own OVP
        # minimum would make a good board fault on itself
        _env_control("f6u_refuses_a_divider_that_sets_into_its_own_ovp",
                     lambda v: v.__setitem__("R99", "820k 1%"))))
    # ---- D-775's five.  The floor is DERIVED, so the controls have to prove
    # the derivation REFUSES -- both a floor below what it derives and a model
    # whose live inputs have drifted past what it was derived on.
    def _env_ohm_control(name, **over):
        live2 = dict(live_ohms)
        live2.update(over)
        ok, _ = judge_accessory_envelope(
            values, single_floor=policy_single, dual_floor=policy_dual,
            live_ohms=live2)
        return name, not ok

    env_controls.update(dict((
        # f6v IS THE POLICY THE PRE-D-775 FIRMWARE SHIPPED: one 3.50 V floor
        # for both rails, which at the published 400 + 300 mA leaves 0.36 % of
        # margin to a RECOVERABLE charger trip on the live resistances and is
        # NEGATIVE on the declared ceilings.
        _env_policy_control(
            "f6v_refuses_the_old_single_3p50V_floor_for_both_D098_rails",
            dual_floor=3.50),
        # f6w IS THE FIRST D-775 DRAFT'S ASSERTED 3.75 V.  It is refused by the
        # SAME arithmetic that produced 3.80 -- the draft passed only because
        # its round 0.250 ohm path and flat 60 mW allowance under-counted the
        # accessory-rail copper, the two limiter RONs and the SYS->U21 trunk.
        _env_policy_control(
            "f6w_refuses_the_asserted_3p75V_floor_the_first_draft_carried",
            dual_floor=3.75),
        # and the single-rail floor is a clause too, not just the dual one
        _env_policy_control(
            "f6x_refuses_a_single_rail_floor_under_its_own_requirement",
            single_floor=3.10),
        # ---- the LIVE inputs.  A path that grows past its declared ceiling
        # must fail rather than be absorbed into the margin.
        _env_ohm_control(
            "f6y_refuses_bat_protected_p_copper_past_its_ceiling",
            bat_protected_p=0.060),
        _env_ohm_control(
            "f6z_refuses_a_sys_to_u21_trunk_past_its_ceiling",
            sys_to_u21=0.260),
    )))

    # ---- D-777's six.  The connector rating is the LOWEST number in the
    # battery path, so these controls have to prove the clause refuses in both
    # directions: a reserve that does not cover the demand, and a rating that
    # was taken on trust rather than read.
    _no_reserve = ()
    _short_reserve = tuple(x for x in P3V3_DUAL_RAIL_RESERVE
                           if x[0] != "inhibit_subghz_tx")
    _bad_connection = dict(BATTERY_CONNECTION,
                           datasheet="hardware/demo/kicad/aqroot-demo/vendor/"
                                     "JST/this-file-does-not-exist.txt")
    _wrong_part = dict(BATTERY_CONNECTION, mpn="B2B-XH-A(LF)(SN)")
    env_controls.update(dict((
        # THE LOAD-BEARING ONE.  This is the board EXACTLY as D-775 shipped it:
        # the full 1.0632 A internal budget live while both accessory rails
        # hold their published budgets at the 3.80 V floor -- 2.2715 A through
        # a connector JST publishes at 2 A.  D-776 passed with this state.
        _env_policy_control(
            "f6aa_refuses_the_d775_envelope_that_overran_j4s_published_rating",
            internal_ceiling=I_INTERNAL, reserve=_no_reserve),
        # a reserve that is NAMED but too small is the same defect softened
        _env_policy_control(
            "f6ab_refuses_a_reserve_that_does_not_cover_the_demand",
            internal_ceiling=round(I_INTERNAL - 0.150, 6),
            reserve=_short_reserve),
        # a firmware ceiling ABOVE what the connector requires, with the full
        # reserve still named: the D-775 cross-domain hole, one term over
        _env_policy_control(
            "f6ac_refuses_a_firmware_ceiling_above_the_derived_requirement",
            internal_ceiling=0.950),
        # a ceiling the NAMED reserve cannot actually reach
        _env_policy_control(
            "f6ad_refuses_a_ceiling_the_named_reserve_cannot_reach",
            internal_ceiling=0.600),
        # an unreadable rating is a REFUSAL, not an inherited 2 A
        _env_policy_control(
            "f6ae_refuses_a_connector_whose_rating_cannot_be_read",
            connection=_bad_connection),
        # and the rating must belong to the part the board actually buys
        _env_policy_control(
            "f6af_refuses_a_rating_that_is_not_on_the_released_bom_row",
            connection=_wrong_part),
    )))

    # D-779.  "A hiccup that auto-retries" was half of SLUSF65B 6.3.7.3.  The
    # control removes the half this repository had been leaving out, which is
    # exactly the state every decision from D-753 onward was written in.
    def _trip_control(name, **over):
        d2 = recoverable_trip_facts(dict(RECOVERABLE_TRIP, **over))
        return name, not d2["the_retry_limit_was_read"]

    env_controls.update(dict((
        _trip_control("f6ag_refuses_an_unreadable_ibat_ocp_retry_limit",
                      retry_re=r"this phrase is not in the datasheet"),
        _trip_control("f6ah_refuses_an_unreadable_recovery_condition",
                      recovery_re=r"this phrase is not in the datasheet"),
        _trip_control("f6ai_refuses_a_missing_datasheet",
                      datasheet="vendor/BQ25185/not-archived.txt"),
    )))

    # ---- F7: the DISPLAY IDENTITY, everywhere it is written -------------
    # D-768.  D-074 locked the EastRising ER-TFT035IPS-6 (3.5in 320x480,
    # ILI9488) and D-112 REPLACED the display symbol because the inherited
    # 2.8-inch CH280QV10-CT / ILI9341 pin table was DEAD ON ARRIVAL here --
    # LEDA/LEDK reversed and WRX/D-CX swapped, neither visible from a pin
    # count, a connector MPN or an ERC run.  D-112 fixed the pins and the
    # Description, and LEFT THE RETIRED PANEL'S NAME IN THE MPN AND IN THE
    # PROVENANCE SENTENCE OF THE SAME SYMBOL -- so the symbol's own Package
    # field still credited "SPEC-CH280QV10-CT_Rev.D pages 6-7. TFT driver
    # ILI9341V" for a pin table transcribed from a different datasheet, one
    # field below a Description that said ILI9488.
    #
    # AND IT REACHED THE RELEASED BOM.  J1's Description column in both
    # aqroot-Demo-BOM-full.csv and -assembly.csv read "CH280QV10-CT Rev.D 2.8in
    # 240x320 IPS TFT + CTP" -- the document a human reads to buy the panel,
    # naming the wrong panel, on the connector whose pin table had already been
    # dead on arrival once for exactly this reason.
    #
    # So this clause asserts the locked identity in every place it is written,
    # and refuses any retired panel name anywhere in the display symbol -- with
    # ONE deliberate exception: text that is explicitly ABOUT the retirement.
    # D-769 GENERALISED THIS CLAUSE.  D-768 closed the display instance of a
    # class: a RETIRED part's name left in the fields of the part that replaced
    # it.  The registry below is that class, and every entry is a place this
    # repository has ALREADY recorded a supersession -- nothing is inferred.
    IDENTITY_GUARD = {
        "J1": dict(
            locked="ER-TFT035IPS-6",
            lib_id_contains="ER-TFT035IPS-6",
            retired=("CH280QV10", "ILI9341", "2.8in", "2.8-inch", "240x320"),
            why="D-074 locked the 3.5in 320x480 ILI9488 panel; D-112 replaced "
                "the 2.8in CH280QV10-CT pin table because it is DEAD ON "
                "ARRIVAL here -- LEDA/LEDK reversed, WRX/D-CX swapped"),
        "U8": dict(
            locked="TI.92.2113",
            lib_id_contains=None,
            retired=("FXP890",),
            why="D-198 superseded the internal Taoglas FXP890 flex with the "
                "EXTERNAL TI.92.2113 SMA dipole on a top-panel bulkhead; "
                "DEVICE_SPEC has flagged the schematic text STALE since"),
        # ---- D-771 ADDS THE THREE PASSIVES WHOSE IDENTITY IT MOVED --------
        # The registry was built for SEMICONDUCTOR identities, where the
        # retired name is wrong wherever it appears.  A PASSIVE is different:
        # its symbol Note is expected to say what it replaced and why, and a
        # clause that refused that would refuse the very sentence that records
        # the supersession.  So these three entries carry `only_fields` and
        # look at the PURCHASING identity alone -- Value, MPN, LCSC -- plus the
        # released BOM row, which is the leg D-768 proved load-bearing.  Free
        # prose is out of scope for them BY CONSTRUCTION, not by exemption.
        "R75": dict(
            locked="CRA2512-FZ-R010ELF",
            lib_id_contains=None,
            only_fields=("Value", "MPN", "LCSC"),
            retired=("CRA2512-FZ-R015ELF", "C2073490", "15mR"),
            why="D-771 moved the LTC4368 current sense 15 -> 10 mOhm because "
                "ADI guarantees dVSENSE,F as 40/50/60 mV, so at 15 mOhm the "
                "LATCHING breaker band (2.640-4.040 A) OVERLAPPED the "
                "BQ25185's RECOVERABLE IBAT_OCP band (2.5625-3.6875 A)"),
        "R97": dict(
            locked="0603WAF1781T5E",
            lib_id_contains=None,
            only_fields=("Value", "MPN", "LCSC"),
            retired=("0603WAF2701T5E", "C13167", "2.7k"),
            why="D-771 moved the ACC_3V3 limiter setting 2.7 -> 1.78 kOhm so "
                "the rail GUARANTEES the 400 mA TOTAL D-098 publishes for it; "
                "2.7 kOhm guaranteed only 0.277 A"),
        "R101": dict(
            locked="0603WAF2371T5E",
            lib_id_contains=None,
            only_fields=("Value", "MPN", "LCSC"),
            retired=("0603WAF2701T5E", "C13167", "2.7k",
                     "0603WAF2321T5E", "C22905", "2.32k"),
            why="D-771 moved the ACC_5V limiter setting 2.7 -> 2.32 kOhm so the "
                "rail GUARANTEES the 300 mA TOTAL D-098 publishes for it, and "
                "D-773 moved it again to 2.37 kOhm once the 5 V setpoint was "
                "derived from the board rather than taken from a 0.6 V VREF "
                "that is not what TI publishes"),
    }
    RETIREMENT_MARKERS = ("RETIRED", "CORRECTED THIS FIELD", "corrected this field",
                          "DO NOT INSTANTIATE", "which is NOT the locked",
                          "the RETIRED 2.8-inch", "superseded")

    def _symbol_fields(ref):
        out = {}
        for sheet in sorted(rl.PROJECT.glob("*.kicad_sch")):
            text = sheet.read_text(encoding="utf-8", errors="replace")
            idx = text.find('(property "Reference" "%s"' % ref)
            if idx < 0:
                continue
            start = text.rfind("\n\t(symbol", 0, idx)
            depth, j = 0, start + 1
            while j < len(text):
                if text[j] == "(":
                    depth += 1
                elif text[j] == ")":
                    depth -= 1
                    if depth == 0:
                        break
                j += 1
            blk = text[start:j + 1]
            out["instance"] = blk
            lib = re.search(r'\(lib_id "([^"]+)"', blk)
            out["lib_id"] = lib.group(1) if lib else ""
            break
        libf = rl.PROJECT / "libraries" / "AQROOT_Beta.kicad_sym"
        if libf.exists() and out.get("lib_id"):
            lt = libf.read_text(encoding="utf-8", errors="replace")
            name = out["lib_id"].split(":", 1)[-1]
            i = lt.find('(symbol "%s"' % name)
            if i >= 0:
                depth, j = 0, i
                while j < len(lt):
                    if lt[j] == "(":
                        depth += 1
                    elif lt[j] == ")":
                        depth -= 1
                        if depth == 0:
                            break
                    j += 1
                out["library_symbol"] = lt[i:j + 1]
        return out

    def _bom_row_refs(line):
        """The references a BOM row covers.  D-771: a row groups them --
        `"R97,R101","2.7k 1%",...` -- so a substring test for `"R97"` misses
        the exact row the clause exists to read."""
        m = re.match(r'\s*"([^"]*)"', line)
        return {x.strip() for x in (m.group(1) if m else "").split(",")}

    def judge_identity(ref, spec, fields, bom_text):
        bad = []
        only = spec.get("only_fields")
        for where in ("instance", "library_symbol"):
            blk = fields.get(where) or ""
            for m in re.finditer(r'\(property "([^"]+)" "((?:[^"\\]|\\.)*)"', blk):
                name, txt = m.group(1), m.group(2)
                if only and name not in only:
                    continue
                for tok in spec["retired"]:
                    if tok in txt and not any(k in txt for k in RETIREMENT_MARKERS):
                        bad.append([where, name, tok, txt[:120]])
                        break
        bom_bad = sorted({tok for tok in spec["retired"]
                          for line in bom_text.splitlines()
                          if tok in line and ref in _bom_row_refs(line)})
        want = spec.get("lib_id_contains")
        d = dict(
            reference=ref, why=spec["why"], locked=spec["locked"],
            lib_id=fields.get("lib_id", ""),
            symbol_is_the_locked_part=(True if not want
                                       else want in fields.get("lib_id", "")),
            no_retired_name_in_the_symbol=not bad,
            no_retired_name_on_the_released_bom_row=not bom_bad,
            offending_fields=bad, offending_bom_tokens=bom_bad)
        clauses = ["symbol_is_the_locked_part", "no_retired_name_in_the_symbol",
                   "no_retired_name_on_the_released_bom_row"]
        # D-771.  ABSENCE OF THE OLD NAME IS NOT PRESENCE OF THE NEW ONE.  For a
        # passive the whole identity IS the MPN, so both legs assert it
        # POSITIVELY as well: the symbol's own MPN field and the released BOM
        # row for that reference must both name the locked part.  (For J1/U8 the
        # `lib_id` clause already carries the positive half.)
        if only:
            inst = fields.get("instance") or ""
            m = re.search(r'\(property "MPN" "((?:[^"\\]|\\.)*)"', inst)
            d["symbol_mpn"] = m.group(1) if m else None
            d["symbol_names_the_locked_part"] = (d["symbol_mpn"] == spec["locked"])
            d["bom_row_names_the_locked_part"] = any(
                spec["locked"] in line and ref in _bom_row_refs(line)
                for line in bom_text.splitlines())
            clauses += ["symbol_names_the_locked_part",
                        "bom_row_names_the_locked_part"]
        d["ok"] = all(d[k] for k in clauses)
        return d["ok"], d

    bom_path = rl.ROOT / "hardware/demo/fab/aqroot-Demo-BOM-assembly.csv"
    bom_text = bom_path.read_text(encoding="utf-8", errors="replace") \
        if bom_path.exists() else ""
    ident_rows, ident_ok = {}, True
    for ref, spec in sorted(IDENTITY_GUARD.items()):
        f = _symbol_fields(ref)
        ok, row = judge_identity(ref, spec, f, bom_text)
        ident_rows[ref] = row
        ident_ok = ident_ok and ok

    # LIVE CONTROLS.  Each puts a real, historical defect back.
    j1 = _symbol_fields("J1")
    u8 = _symbol_fields("U8")
    stale_j1 = dict(j1, instance=(j1.get("instance", "")
                                  + '\n(property "Description" "CH280QV10-CT '
                                    'Rev.D 2.8in 240x320 IPS TFT + CTP")'))
    wrong_sym = dict(j1, lib_id="AQROOT_Beta:CH280QV10_CT_50P")
    stale_u8 = dict(u8, instance=(u8.get("instance", "")
                                  + '\n(property "Package" "Antenna: module '
                                    'IPEX/u.FL with Taoglas FXP890.07.0100C")'))
    stale_bom = ('"J1","FH69-50S-0.5SH","x","Hirose","FH69-50S-0.5SH",'
                 '"C25955556","CH280QV10-CT Rev.D 2.8in 240x320",1,')
    ident_controls = {
        "f7a_refuses_the_retired_panel_name_in_the_symbol":
            not judge_identity("J1", IDENTITY_GUARD["J1"], stale_j1, bom_text)[0],
        "f7b_refuses_the_retired_panel_symbol_being_placed":
            not judge_identity("J1", IDENTITY_GUARD["J1"], wrong_sym, bom_text)[0],
        "f7c_refuses_the_retired_panel_name_on_the_released_bom":
            not judge_identity("J1", IDENTITY_GUARD["J1"], j1, stale_bom)[0],
        "f7d_refuses_the_superseded_fxp890_antenna_on_u8":
            not judge_identity("U8", IDENTITY_GUARD["U8"], stale_u8, bom_text)[0],
    }
    # ---- D-771's four.  The first two are the SYMBOL leg on a passive, the
    # second two are the BOM-ROW leg -- including, deliberately, a GROUPED row
    # of the exact shape the released BOM carried until D-771 split it, which
    # the pre-D-771 substring matcher would have walked straight past.
    r75 = _symbol_fields("R75")
    r97 = _symbol_fields("R97")
    stale_r75 = dict(r75, instance=(r75.get("instance", "")
                                    + '\n(property "MPN" "CRA2512-FZ-R015ELF")'))
    stale_r97 = dict(r97, instance=(r97.get("instance", "")
                                    + '\n(property "Value" "2.7k 1%")'))
    grouped_bom = ('"R97,R101","2.7k 1%","Resistor_SMD:R_0603_1608Metric",'
                   '"UNI-ROYAL(Uniroyal Elec)","0603WAF2701T5E","C13167","","2",""')
    sense_bom = ('"R75","15mR 1% 1W","Resistor_SMD:R_2512_6332Metric","BOURNS",'
                 '"CRA2512-FZ-R015ELF","C2073490","","1",""')
    ident_controls.update({
        "f7e_refuses_the_superseded_15mOhm_sense_mpn_on_r75":
            not judge_identity("R75", IDENTITY_GUARD["R75"], stale_r75, bom_text)[0],
        "f7f_refuses_the_superseded_2k7_ilim_value_on_r97":
            not judge_identity("R97", IDENTITY_GUARD["R97"], stale_r97, bom_text)[0],
        "f7g_refuses_the_superseded_ilim_part_on_a_GROUPED_released_bom_row":
            not judge_identity("R101", IDENTITY_GUARD["R101"], r97, grouped_bom)[0],
        "f7h_refuses_the_superseded_sense_part_on_the_released_bom":
            not judge_identity("R75", IDENTITY_GUARD["R75"], r75, sense_bom)[0],
        # and ABSENCE of the retired name is not PRESENCE of the locked one:
        # a BOM with no R75 row at all, and a symbol whose MPN field is simply
        # missing, both carry zero retired tokens and are both refused.
        "f7i_refuses_a_released_bom_with_no_row_for_the_locked_part":
            not judge_identity("R75", IDENTITY_GUARD["R75"], r75, "")[0],
        "f7j_refuses_a_symbol_that_does_not_name_the_locked_part":
            not judge_identity(
                "R97", IDENTITY_GUARD["R97"],
                dict(r97, instance=(r97.get("instance", "") or "").replace(
                    '(property "MPN" "0603WAF1781T5E"', '(property "MPN" "x"'),
                ), bom_text)[0],
    })

    # ---- F8: the derating rule, applied to the parts this board FITS -----
    import screen_bom_sourcing as sbs                              # noqa: E402
    cap_ok, caps = judge_capacitor_derating(board, sch_dnp, sbs.NET_MAX_DC)

    def _cap_control(name, **kw):
        ok, _ = judge_capacitor_derating(board, sch_dnp, **kw)
        return name, not ok

    cap_controls = dict(x for x in (
        # a node declared ABOVE what its capacitor can survive -- the leg no
        # exception may carry
        _cap_control("f8a_refuses_a_capacitor_under_its_nodes_absolute_maximum",
                     net_max_dc=dict(sbs.NET_MAX_DC,
                                     ACC_5V_RAW=(5.165, 12.0, "control"))),
        # the five named exceptions are load-bearing: drop them and the same
        # arithmetic refuses the board
        _cap_control("f8b_refuses_the_board_with_the_exception_list_emptied",
                     net_max_dc=sbs.NET_MAX_DC, exceptions={}),
        # an exception that is no longer needed is itself refused, so the list
        # cannot accumulate
        _cap_control("f8c_refuses_an_exception_that_is_no_longer_needed",
                     net_max_dc=sbs.NET_MAX_DC,
                     exceptions=dict(CAP_DERATE_EXCEPTIONS,
                                     C24="a part that already meets the rule")),
        # ---- D-778's four.  The rating now comes from the PART, so the
        # controls have to prove the join is load-bearing in both directions.
        # THE LOAD-BEARING ONE: this is D-774's own exception list, which
        # carried C20/C38/C67 against a 10 V value string while the BOM buys
        # 25 V parts.  Against the real ratings those three are stale and the
        # same clause that removed them refuses them coming back.
        _cap_control("f8e_refuses_d774s_stale_c20_c38_c67_exceptions",
                     net_max_dc=sbs.NET_MAX_DC,
                     exceptions=dict(
                         CAP_DERATE_EXCEPTIONS,
                         C20="D-774's exception, against a rating the BOM does "
                             "not buy",
                         C38="D-774's exception, against a rating the BOM does "
                             "not buy",
                         C67="D-774's exception, against a rating the BOM does "
                             "not buy")),
        # a capacitor whose purchased record cannot be found is a REFUSAL --
        # this is what replaces D-774's pinned count of unrated value strings
        _cap_control("f8f_refuses_a_capacitor_with_no_purchased_record",
                     net_max_dc=sbs.NET_MAX_DC,
                     purchased={k: v for k, v in
                                purchased_capacitor_ratings().items()
                                if k != "C44"}),
        # the purchased rating is what is judged, so a lower one must refuse
        _cap_control("f8g_refuses_a_purchased_part_under_its_nodes_absolute",
                     net_max_dc=sbs.NET_MAX_DC,
                     purchased=dict(
                         purchased_capacitor_ratings(),
                         C20=dict(purchased_capacitor_ratings()["C20"],
                                  rating_V=4.0))),
        # and a value string may never claim MORE than the BOM buys
        _cap_control("f8h_refuses_a_value_string_that_overstates_the_part",
                     net_max_dc=sbs.NET_MAX_DC,
                     purchased=dict(
                         purchased_capacitor_ratings(),
                         C29=dict(purchased_capacitor_ratings()["C29"],
                                  rating_V=6.3)))))

    nc = ledger["approved_demo_nc"]
    checks = {
        "F1_every_scope_part_fitted": dict(
            ok=not missing_refs and not dnp_refs,
            features=len(FEATURES),
            references=len({r for f in FEATURES for r in f["refs"]}),
            missing_from_board=[list(x) for x in missing_refs],
            populated_as_dnp=[list(x) for x in dnp_refs]),
        "F2_every_scope_net_whole": dict(
            ok=not bad_nets,
            nets=len({n for f in FEATURES for n in f["nets"]}),
            failures=[list(x) for x in bad_nets]),
        "F4_every_exposed_signal_contact_has_esd": dict(
            ok=not unprotected and bool(j5) and bool(esd_nets),
            arrays=sorted({f.GetReference() for f in board.GetFootprints()
                           if "TPD4E1B06" in (f.GetValue() or "")}),
            protected_nets=sorted(esd_nets),
            j5_contacts=j5_rows,
            unprotected_signal_contacts=unprotected,
            note="power and ground contacts are deliberately excluded -- D-188 "
                 "rejected a TVS on either rail because the part's 5.5 V VRWM "
                 "leaves no working margin against a 5.0 V nominal rail"),
        "F5_backlight_disconnect_control_is_independent": dict(
            ok=(bl_ok and all(bl_controls.values())
                and fet_ok and all(fet_controls.values())),
            method="TI SNVSA40B 6.3.5 makes CTRL an ANALOG dimming input: the "
                   "converter keeps switching through every PWM low phase, so "
                   "Q11's gate may not share it.  The D-752 hold network is "
                   "what keeps the ordering, and four live controls put each "
                   "way of losing it back.  D-766: AND THE SILICON.  Q11's "
                   "drain is the panel cathode, which under open-LED "
                   "protection follows the anode to the ceiling this board's "
                   "OWN .kicad_dru publishes for LED_BOOST -- parsed from that "
                   "file, not restated here -- so the fitted FET's PUBLISHED "
                   "VDS rating must cover it, the held gate must enhance the "
                   "FITTED part past its own worst-case VGS(th), and the gate "
                   "may not decay below that threshold before the TPS61169 is "
                   "guaranteed to be in shutdown.  Four more live controls, "
                   "one of which is the 30 V AO3400A D-752 left fitted",
            controls_refused=bl_controls,
            fet_controls_refused=fet_controls,
            fet=fet,
            **{k: v for k, v in bl.items() if k != "ok"}),
        "F6_accessory_envelope_is_bounded_by_hardware": dict(
            ok=env_ok and all(env_controls.values()),
            method="TI equation 1 over the two ILIM resistors AND the two "
                   "limiter part numbers the board actually carries.  D-753: "
                   "no state a user can reach may exceed the BQ25185 "
                   "IBAT_OCP MINIMUM, and the double limiter fault must stay "
                   "inside the protection chain, because the board has no "
                   "accessory current measurement and a policy cannot bound "
                   "what an external accessory draws.  D-765: the setting "
                   "must ALSO sit inside the fitted part's OWN specified ILIM "
                   "range over the programming resistor's tolerance band -- "
                   "TPS22950-Q1 is specified 0.05-3.5 A (SLVSGP6A), the "
                   "TPS22950C it replaces only 0.5-3.5 A (SLVSFJ2B s.5).  "
                   "D-771: the envelope is now checked from BELOW as well -- "
                   "each rail must GUARANTEE the budget D-098 publishes "
                   "(ACC_3V3_SW 400 mA total, ACC_5V_SW 300 mA total), which "
                   "the 2.7 kOhm setting did not; the protection chain is "
                   "read from R75 and U18 over the LTC4368's own guaranteed "
                   "40/50/60 mV threshold band instead of its 50 mV typical, "
                   "so the LATCHING breaker must sit entirely above the "
                   "RECOVERABLE charger trip; both converters must be able "
                   "to source what their load switch is allowed to pass; and "
                   "D-775 binds D-098 normal 400/300 mA operation to the "
                   "firmware VCELL policy with a sag-aware model from the "
                   "MAX17048 BAT_PROTECTED_P measurement point",
            controls_refused=dict(env_controls, **budget_controls), **env),
        "F8_the_derating_rule_is_applied_to_the_parts_this_board_fits": dict(
            ok=cap_ok and all(cap_controls.values()),
            clause="D-774.  screen_bom_sourcing states the project's rule -- "
                   "2x the node's OPERATING maximum AND survival against its "
                   "ABSOLUTE maximum -- and applies it ONLY while proposing a "
                   "part for an UNSOURCED line.  This BOM has had none since "
                   "D-615, so the rule had never once been run against a part "
                   "this board actually fits.  It is now, over the SAME "
                   "NET_MAX_DC table, read live.  Survival against the "
                   "absolute maximum is never excused; a shortfall against the "
                   "2x CONVENTION must be a named, reasoned exception, and an "
                   "exception that is no longer needed is itself refused",
            controls_refused=cap_controls,
            **{k: v for k, v in caps.items() if k != "ok"}),
        "F7_no_retired_part_name_survives_on_the_part_that_replaced_it": dict(
            ok=ident_ok and all(ident_controls.values()),
            method="D-768 found 'CH280QV10-CT Rev.D 2.8in 240x320' on J1's row "
                   "of the RELEASED BOM, and the ER-TFT035IPS-6 symbol's own "
                   "Package field crediting the retired panel's datasheet for "
                   "a pin table D-112 had transcribed from a different one -- "
                   "on the connector whose pin table had ALREADY been dead on "
                   "arrival for exactly that reason. D-769 generalised it: "
                   "every entry in the registry is a supersession this "
                   "repository has already recorded, and the clause asserts "
                   "the locked identity in the placed symbol, in its library "
                   "definition AND on the released BOM row. Checking the "
                   "schematic alone would pass a board whose shipped BOM is "
                   "wrong",
            references=sorted(IDENTITY_GUARD),
            controls_refused=ident_controls,
            findings=ident_rows),
        "F3_approved_nc_exactly_as_scoped": dict(
            ok=(set(nc["observed"]) == EXPECTED_NC
                and not nc["missing"] and not nc["unexpected"]),
            expected=sorted(EXPECTED_NC), observed=nc["observed"],
            missing=nc["missing"], unexpected=nc["unexpected"]),
    }
    out = dict(schema=1, board=ledger["board"],
               board_sha256=ledger["board_sha256"],
               source="docs/full-beta-v2/AQROOT_DEMO_SCOPE.md",
               connectivity=ledger["connectivity"],
               approved_unrouted=ledger["approved_unrouted"]["expected"],
               features=rows, checks=checks,
               all_pass=all(c["ok"] for c in checks.values()))
    text = json.dumps(out, indent=1, sort_keys=True)
    if args.out:
        args.out.write_text(text + "\n", encoding="utf-8")
    print(text)
    for k, c in checks.items():
        print("  %s %s" % (k, "PASS" if c["ok"] else "FAIL"), file=sys.stderr)
    return 0 if out["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
