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
import argparse, hashlib, json, math, re, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
MFG = HERE.parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(MFG))
import routing_ledger as rl                                  # noqa: E402
import audit_rail_ampacity as ara                            # noqa: E402

DRU = rl.PROJECT / "aqroot-Beta-v2.kicad_dru"
POWER_POLICY = ROOT / "Firmware/src/hw/aqroot_accessory_power_policy.h"
FIRST_FIVE_ASSEMBLY = ROOT / "docs/full-beta-v2/assembly/FIRST_FIVE_ASSEMBLY_PLAN.md"
DEMO_PERIPHERALS = ROOT / "Firmware/src/hw/aqroot_demo_peripherals.h"
# D-788 / R7-D787-06 moved the SHIPPED backlight entry point into its own
# header so a host test can compile and RUN it; F5 reads the production ramp
# from there.
DEMO_BACKLIGHT = ROOT / "Firmware/src/hw/aqroot_demo_backlight.h"
TPS61169_PRIMARY = ROOT / "hardware/demo/kicad/aqroot-demo/vendor/TI/tps61169.pdf"
# D-788 / R7-N04.  THE PUBLISHED NUMBER AN ACCESSORY DESIGNER READS IS IN A
# DIFFERENT FILE FROM THE GATE THAT PROVES IT.  Round-7 found six separate
# stale-document defects and R7-D787-19/20 were two of them; a product-facing
# voltage contract that this contract does not read is the same shape.  F6 now
# requires DEVICE_SPEC to publish the exact figures F6 derives.
DEVICE_SPEC = ROOT / "docs/full-beta-v2/DEVICE_SPEC.md"

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
    # D-780.  The selected part has a PUBLISHED low-gate conduction point
    # BELOW the gate voltage this circuit actually holds.  This is the property
    # D-779 tried to infer for AO3422 from typical gfs and could not guarantee.
    "SQ2364EES-T1_BE3": dict(
        vds_V=60.0, vgs_th_max_V=1.00, vgs_th_test_A=250e-6,
        rds_on_vgs_V=1.5, rds_on_id_A=2.0, rds_on_max_ohm=0.245,
        rds_hot_vgs_V=4.5, rds_hot_id_A=2.0,
        rds_hot_tj_C=175.0, rds_hot_max_ohm=0.600,
        igss_max_A=100e-9,
        source="Vishay SQ2364EES document 75975 Rev B, archived at "
               "vendor/VISHAY/sq2364ees-75975-revb.pdf: SOT-23 1=G 2=S 3=D, "
               "VDS 60 V, VGS(th) 0.46/0.6/1.0 V at 250 uA, IGSS +/-100 nA "
               "at +/-3 V, RDS(on) 0.245 ohm MAX at VGS=1.5 V ID=2 A, and "
               "0.600 ohm MAX at VGS=4.5 V ID=2 A TJ=175 C.  The 1.5 V row "
               "is in the TC=25 C table; first-five validation therefore also "
               "exercises backlight on/off at the declared 0..40 C prototype "
               "qualification endpoints rather than pretending that row is an "
               "all-temperature guarantee."),
    # Kept as a NEGATIVE CONTROL: this is exactly the D-779 board.  Its only
    # published low-gate RDS(on) point is 2.5 V, ABOVE the held 2.396 V, so the
    # new direct clause must refuse it.
    "AO3422":  dict(vds_V=55.0, vgs_th_max_V=2.00,
                    vgs_th_test_A=250e-6,
                    rds_on_vgs_V=2.5, rds_on_id_A=1.5, rds_on_max_ohm=0.200,
                    source="AOS AO3422 rev 2.1 2024-03: VDS 55 V, VGS(th) "
                           "max 2.0 V at 250 uA, RDS(on) 0.200 ohm MAX at "
                           "VGS=2.5 V ID=1.5 A"),
    "AO3400A": dict(vds_V=30.0, vgs_th_max_V=1.45,
                    source="AOS AO3400A rev 3.1 2023-07 as read by D-159: "
                           "VDS 30 V, VGS(th) 0.65/1.05/1.45 V"),
    "AO3400A_NO_RDS_ON": dict(vds_V=55.0, vgs_th_max_V=2.00,
                              source="control only -- a FET whose datasheet "
                                     "this contract has no RDS(on) test point for"),
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
        # ---- D-780: ORDER AGAINST A PUBLISHED CONDUCTION REGION -----------
        # Threshold is an OFF-state boundary, not a load-current guarantee.
        # The old AO3422 board held VGS=2.396 V while its first published
        # RDS(on) point was 2.5 V; D-779 then tried to bridge that unpublished
        # 104 mV gap with TYPICAL transconductance.  That is not a production
        # guarantee.  The selected SQ2364EES publishes RDS(on) MAX at VGS=1.5 V
        # and ID=2 A, so the held gate is 0.896 V INSIDE a characterized
        # conduction region.  The ordering is now direct: U17 must finish its
        # 2.5 ms shutdown before the RC envelope can decay below VGS=1.5 V.
        if tau_worst_s and pub.get("rds_on_vgs_V"):
            guaranteed_vgs = pub["rds_on_vgs_V"]
            guaranteed_gate = guaranteed_vgs + BL_SOURCE_V
            f["published_conduction_vgs_V"] = guaranteed_vgs
            f["published_conduction_id_A"] = pub["rds_on_id_A"]
            f["published_rds_on_max_ohm"] = pub["rds_on_max_ohm"]
            f["string_current_A"] = BL_STRING_CURRENT_A
            f["published_current_over_what_is_asked_x"] = round(
                pub["rds_on_id_A"] / BL_STRING_CURRENT_A, 3)
            f["held_vgs_margin_above_published_conduction_point_V"] = round(
                vgs_held - guaranteed_vgs, 4)
            f["held_vgs_meets_published_conduction_point"] = (
                vgs_held >= guaranteed_vgs)
            t_leave_ms = 0.0
            if BL_HELD_GATE_V > guaranteed_gate:
                t_leave_ms = tau_worst_s * 1e3 * math.log(
                    BL_HELD_GATE_V / guaranteed_gate)
            f["time_to_leave_published_conduction_region_ms"] = round(
                t_leave_ms, 4)
            f["published_conduction_ordering_margin_x"] = round(
                t_leave_ms / BL_TSD_MS, 4)
            f["u17_shuts_down_before_gate_leaves_published_conduction_region"] = (
                f["held_vgs_meets_published_conduction_point"]
                and t_leave_ms > BL_TSD_MS)
            f["channel_drop_at_string_current_mV_at_published_max"] = round(
                BL_STRING_CURRENT_A * pub["rds_on_max_ohm"] * 1e3, 3)
            f["threshold_test_current_A"] = pub.get("vgs_th_test_A")
            # D-788 / R7-D787-14.  THE SCOPE OF THE ROW IS A PROPERTY OF THE
            # ROW, not of a reference name.  Vishay 75975 Rev B prints the
            # 0.245 ohm VGS=1.5 V ID=2 A limit in the TC = 25 C table and
            # publishes no low-gate row at any other temperature, so this
            # clause is a 25 C guarantee and the 0/25/40 C endpoints stay a
            # FIRST-ARTICLE measurement (Q11-TEMP-01), not an inference.
            f["published_low_gate_rds_row_temperature_C"] = pub.get(
                "rds_on_tc_C", 25.0)
            f["published_low_gate_rds_is_25C_only"] = (
                f["published_low_gate_rds_row_temperature_C"] == 25.0)
            f["published_low_gate_rds_scope"] = (
                "RDS(on) MAX %.3f ohm at VGS=%.1f V, ID=%.1f A, TC=%.0f C; no "
                "low-gate row is published at any other temperature, so "
                "0/25/40 C remains a first-article measurement"
                % (pub["rds_on_max_ohm"], guaranteed_vgs, pub["rds_on_id_A"],
                   f["published_low_gate_rds_row_temperature_C"]))
            f["first_five_temperature_validation_required_C"] = [0, 25, 40]
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
        "held_vgs_meets_published_conduction_point",
        "u17_shuts_down_before_gate_leaves_published_conduction_region",
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
# --------------------------------------------------------------------------
# D-788 / R7-D787-01 -- THE PUBLISHED COMMUNITY-PORT MINIMUM, RESTATED.
#
# D-787 published 3.135 V, which is 3.3 V -5 %.  D-788 proves from the fitted
# panel's own datasheet that the rail this port is switched from may never
# exceed 3.3 V -- the ILI9488's ABSOLUTE MAXIMUM on VCI and IOVCC -- so the
# rail's nominal must sit BELOW 3.3 V and a 3.3 V -5 % connector minimum is
# unreachable AT ANY CURRENT, including zero: the rail's own heavy-load
# minimum is 3.0976 V before a single milliohm of delivery loss.
#
# OWNER-APPROVED D-788 OPTION A (2026-09-20).  The first-five product keeps
# the full 400 mA Community-Port current capability and RESTATES the switched
# rail's voltage contract to the corrected shared-rail envelope.  A dedicated
# accessory regulator solely to preserve the former 3.135 V minimum is deferred
# to REV-B.  The GATE is unchanged in strength: the board must still deliver at
# or above the published minimum while the fitted display remains inside its
# hard 3.3 V supply ceiling.
#
# R7-N01 MOVED IT ONCE MORE, 2.98 -> 2.95 V.  The owner's approval names
# "approximately 3.2 V nominal" with working figures of ~3.097..3.252 V unloaded
# and >= 2.98 V at 400 mA, and EXPLICITLY delegates the exact values to the
# final candidate.  Centring the divider inside the 3.000..3.300 V window that
# the ESP32-S3's floor and the panel's absolute maximum leave (R7-N02) moves
# the whole band down by 29 mV, which buys 29 mV of headroom under a DAMAGE
# limit and costs 28 mV of a published tolerance an accessory reads.  Every
# Qwiic/STEMMA QT device this project has qualified operates to 2.7 V or below,
# so no capability is lost; the PUBLISHED NUMBER changes and is stated here.
PUBLISHED_CONNECTOR_MIN_V = 2.95
PUBLISHED_CONNECTOR_MIN_AUTHORITY = (
    "Owner-approved D-788 Option A, 2026-09-20: 3.2 V-class Community-Port "
    "rail, full 400 mA capability retained; exact release envelope derived "
    "from the final D-788 candidate. Dedicated accessory regulator deferred "
    "to REV-B.  R7-N01 freezes that envelope at 3.069408 / 3.145503 / "
    "3.223012 V unloaded and 2.954962 V delivered at the full 400 mA, against "
    "a published 2.95 V minimum; the 400 mA and 300 mA current budgets are "
    "unchanged.")
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
#
# D-788 / R7-D787-02.  A GUARANTEED ROW IS GUARANTEED AT ITS OWN CONDITION.
# D-787 used the 68 mOhm figure, which SLVSGP6A specifies at VIN = 3.3 V, for a
# switch whose input is the +3V3 rail's HEAVY-LOAD MINIMUM -- below 3.3 V, where
# the datasheet publishes a larger number.  Round-7 reproduced the sensitivity
# (105/116 mOhm) and it consumed the whole delivery margin.
#
# The bound is now DERIVED, and it is an interpolation between two GUARANTEED
# rows rather than an extrapolation beyond one.  SLVSGP6A gives RON max over
# -40..+125 C at three input voltages:
#
#        VIN      1.8 V     3.3 V     5.0 V
#        25 C      90        51        41     mOhm
#        85 C     105        62        49     mOhm
#       125 C     116        68        54     mOhm
#
# RON(VIN) is CONVEX-DECREASING in every one of those rows -- the 1.8->3.3 V
# slope is -32.0/-28.7/-26.0 mOhm/V and the 3.3->5.0 V slope is
# -8.2/-7.6/-5.9 mOhm/V, so the second difference is positive at every
# temperature, and Figure 6-3 plots the same shape.  For a convex function the
# CHORD between two points lies ABOVE the curve, so linear interpolation
# between the 1.8 V and 3.3 V guaranteed maxima is an UPPER BOUND at every VIN
# in between.  Outside that span the bound saturates at the nearer row.
RON_TPS22950_MAX = {1.8: 0.116, 3.3: 0.068}


def tps22950_ron_max(vin_V):
    """Guaranteed -40..+125 C RON upper bound at an arbitrary input voltage."""
    lo_v, hi_v = 1.8, 3.3
    lo_r, hi_r = RON_TPS22950_MAX[lo_v], RON_TPS22950_MAX[hi_v]
    if vin_V >= hi_v:
        return hi_r
    if vin_V <= lo_v:
        return lo_r
    return lo_r + (hi_r - lo_r) * (vin_V - lo_v) / (hi_v - lo_v)


# ACC_5V's switch runs from ACC_5V_RAW, which never falls below the 3.3 V row's
# condition, so the same bound applied at 3.3 V covers it; the 54 mOhm 5 V row
# is reported beside it as the expected value rather than used as the bound.
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
    # D-787 / R6-A01. The release no longer claims the 224 mOhm routed
    # U20->J5 path is the guaranteed-delivery path. Both J5 contacts receive
    # independent first-five reinforcement leads from TP12, downstream of U20.
    # The board-owned prefix is therefore U20.5->TP12.1; the manual lead's
    # separately measured <=30 mOhm limit is added by the envelope model.
    "acc_3v3_sw": dict(rail="ACC_3V3_SW", src=("U20.5",),
                       snk=("TP12.1",), bound_ohm=0.080,
                       last_measured_ohm=0.070186,
                       what="U20 output -> TP12 reinforcement source"),
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
# THESE TWO ARE THE MODULE DEFAULTS, AND THEY MUST EQUAL WHAT THE FIRMWARE
# CARRIES.  `main()` always parses the real constants out of
# `aqroot_accessory_power_policy.h` and passes them in; these exist only so
# `judge_accessory_envelope` stays a pure function for its own mutation
# controls and for `battery_pack_contract`, which calls it with no floors at
# all.  D-787 found the failure mode: the derived dual requirement moved to
# 3.8094 V and the firmware to 3.85 V, and this default stayed at D-775's
# 3.80 V, so `battery_pack_contract` -- the one caller that uses the default --
# refused a board every other gate had passed.  `firmware_policy_defaults_match`
# below makes that class of drift a CLAUSE instead of a surprise.
NORMAL_SINGLE_VBAT_FLOOR = 3.50         # D-766's retained policy floor
NORMAL_DUAL_VBAT_FLOOR = 3.85           # D-787's DERIVED requirement, gridded
VBAT_CORNER = 3.0                      # fault-envelope 1S Li-ion corner
# D-774 SWEEP.  Every other physical constant in this file now cites a primary
# source (see ILIM_LO/HI, IBAT_OCP_A, BREAKER_SENSE_mV, BOOST_FB, U12_IOUT_A,
# U21_*, FUSE_A, BL_*).  THESE TWO DO NOT, and are kept because both are
# CONSERVATIVE IN THE DIRECTION THAT MATTERS: a lower efficiency means MORE pack
# current for the same delivered load, so every margin this file reports is
# understated by them.  The TPS63020 near unity ratio at ~1.9 A and the TPS61023
# at 3.0 -> 5.165 V both run above these figures in their own published curves.
ETA_U12 = 0.90                         # TPS63020 buck-boost, conservative
ETA_U21 = 0.88                         # TPS61023 boost, conservative
# D-787 / R6-A01. The main 3.3-V rail is adjustable; a typed 3.3 V constant
# allowed the released divider to violate the accessory connector minimum while
# F6 stayed green. Derive the complete PWM and power-save envelope from the
# fitted divider and TI's published VFB/regulation bands instead.
#
# THE TEMPERATURE COEFFICIENT IS A PROPERTY OF THE PART, NOT OF THE DESIGNATOR.
# A TCR keyed by reference is a hand-written constant that survives a part
# swap: the first D-787 draft carried `R40: 10.0` because the 176 kOhm KOA
# RN73H...B10 it had selected is a 10 ppm part, and that number would have
# stayed put when the part moved.  So the table is keyed by the PURCHASED MPN,
# read off the schematic, and an MPN this table does not know has NO TCR and
# F6 REFUSES rather than defaulting.
P3V3_FB = dict(
    top="R39", bottom="R40", vfb_V=(0.495, 0.500, 0.505),
    max_line_reg=0.005, max_load_reg=0.005, ps_high_relative_to_pwm=0.05,
    reference_temp_C=25.0, temp_min_C=-40.0, temp_max_C=85.0,
    # D-788 / R7-D787-01.  PS/SYNC NO LONGER SITS ON GND.  TI SLVS916I 7.4.4:
    # "To enable power save mode, PS/SYNC must be set low", and the EC table
    # gives VFB_PS as 0.6 % .. 5 % ABOVE VFB_PWM.  U12.13 is now tied to the EN
    # net, so the converter runs FORCED FIXED-FREQUENCY PWM whenever it is
    # enabled and that excursion cannot occur.  The clause below REFUSES a
    # board on which PS/SYNC is grounded again, so this flag cannot drift away
    # from the copper.
    power_save_disabled_by=("U12", "13"),
    power_save_disabled_net="Net-(SW9-A)",
    # Viking Tech ARG03B and YAGEO RT0603 thin film, both 0.1 % / 25 ppm per C,
    # -55..+155 C.  Confirmed live per D-096: evidence/jlc-live/
    # arg03btc1004-*.json (C335092, stock 54774) and
    # rt0603brd07189kl-*.json (RT0603BRD07189KL, C861174, stock 339).
    tcr_ppm_per_C_by_mpn={"ARG03BTC1004": 25.0, "ARG03BTC1783": 25.0,
                          "RT0603BRD07187KL": 25.0,
                          "RT0603BRD07189KL": 25.0},
    released_mpns={"R39": "ARG03BTC1004", "R40": "RT0603BRD07189KL"})

# D-788 / R7-D787-03 -- THE WHOLE LOOP, NOT THE HALF OF IT THAT IS COPPER.
#
# D-787's delivery proof summed U20's RON, the bounded U20->TP12 board copper
# and the manual lead.  Round-7 found that it omitted the SOURCE side (U12's
# output to U20's input, which is pour/plane-delivered and therefore invisible
# to a track-graph measurement), the GROUND RETURN, and the MATING CONTACT
# itself, and left the MEASUREMENT PLANE undefined -- about 28 mOhm of omitted
# series resistance against an 11 mV margin.
#
# THE MEASUREMENT PLANE IS NOW STATED.  The guaranteed voltage is the potential
# between the `ACC_3V3_SW` contact and the `GND` contacts AT THE J5 MATING
# INTERFACE, with the accessory's own plug, cable and connector OUTSIDE the
# guarantee.  Every term below is either measured off the live board, bounded
# by a ceiling the live measurement must clear, or a DECLARED allowance with
# its reason written down.
P3V3_DELIVERY = dict(
    # Pour-delivered, so no track graph reaches it.  The narrow elements are
    # the only ones that matter and they are small: U12's two 0.240 mm DSJ
    # output lands into 1.2 mm of 0.800 mm B.Cu (0.74 mOhm), three 0.600 mm
    # branches to three 0.800 mm plane vias (about 0.9 mOhm in parallel), the
    # In3/F.Cu plane spread over about 35 mm at tens of mm width (under
    # 5 mOhm at the 0.5 oz inner and 1 oz outer sheet resistances this board's
    # own stackup declares), and U20's 2.5 mm 0.400 mm B.Cu input stub
    # (3.1 mOhm).  About 11 mOhm itemised; DECLARED at 25 mOhm, a 2.3x
    # allowance, because a plane path is not track-measurable here.
    source_bound_ohm=0.025,
    source_is_a_declared_allowance=True,
    source_basis="U12 VOUT lands -> B.Cu trunk -> three plane vias -> In3/F.Cu "
                 "+3V3 plane -> U20.2 input stub; itemised at about 11 mOhm "
                 "from the board's own declared copper weights and DECLARED at "
                 "25 mOhm",
    # J5 is Samtec SSQ-124-02-G-S-RA.  Samtec's published datasheet gives a
    # 6.3 A per-pin current rating and NO contact-resistance row, so this is a
    # DECLARED allowance and a first-article measurement, not a datasheet
    # number.  25 mOhm is roughly 2x what a gold-on-phosphor-bronze 2.54 mm
    # contact typically measures.
    signal_contact_ohm=0.025,
    gnd_contacts_in_parallel=4,
    contact_is_a_declared_allowance=True,
    contact_basis="Samtec SSQ series publishes a 6.3 A per-pin rating and no "
                  "contact-resistance row; 25 mOhm per mated contact is a "
                  "DECLARED allowance, measured at first article (C-ACC-01).  "
                  "The signal side is charged for ONE contact because the "
                  "clause qualifies each duplicated contact ALONE; the return "
                  "side divides by the four GND contacts the same mated header "
                  "always presents.",
    # J5 GND contacts -> the +3V3 source's ground reference, through the In1
    # and In4 solid GND planes in parallel plus their vias.  Two 0.5 oz planes
    # in parallel are 0.566 mOhm per square and the route is a couple of
    # squares wide, so this is 1-2 mOhm itemised; DECLARED at 10 mOhm.
    gnd_return_bound_ohm=0.010,
    gnd_return_is_a_declared_allowance=True,
    process_ohm=0.010,
    process_basis="solder joints at the two manual lead terminations and the "
                  "board's own pad/plating tolerance; DECLARED",
    # The two conductors this rail is actually delivered by.  Each is qualified
    # ALONE: an accessory may use either duplicated contact by itself.
    contacts={
        "J5.3": dict(board_copper_src=("U20.5",), board_copper_snk=("TP12.1",),
                     board_copper_bound_ohm=0.075,
                     reinforced=True,
                     what="U20 output -> TP12 reinforcement land, then the "
                          "manual 28 AWG lead to J5.3"),
        "J5.22": dict(board_copper_src=("U20.5",), board_copper_snk=("J5.22",),
                      board_copper_bound_ohm=0.090,
                      reinforced=False,
                      what="U20 output -> J5.22 by routed copper alone; this "
                           "contact needs no manual lead, which is what "
                           "removes D-787's two-conductors-on-one-pad problem"),
    })
# --------------------------------------------------------------------------
# D-788 / R7-D787-01 -- THE TIGHTEST CONSUMER ON THIS RAIL IS THE DISPLAY, AND
# D-787's 3.600 V CEILING WAS NOT ITS NUMBER.
#
# D-787 judged the main rail's high side against a typed
# `tightest_internal_consumer_max_V = 3.6`, which is the ESP32-S3's figure.  The
# FITTED display is EastRising `ER-TFT035IPS-6`, an ILI9488 panel, and ILI
# Technology's own datasheet -- archived at
# `vendor/ILITEK/ilitek-ili9488-v100.pdf` and corroborated line-for-line against
# a second independent mirror -- says:
#
#   Table 41, ABSOLUTE MAXIMUM RATINGS
#       VCI ~ DGND     -0.3 .. +3.3 V
#       IOVCC ~ DGND   -0.3 .. +3.3 V
#       VIN (any logic input)  -0.3 .. IOVCC + 0.3 V
#   Section 17.2, DC CHARACTERISTICS FOR PANEL DRIVING
#       VCI    2.5 / 2.8 / 3.3 V
#       IOVCC  1.65 / 1.8 / 3.3 V
#       VIH    0.7 x IOVCC .. IOVCC
#       Note 2: supply IOVCC equal to or less than VCI
#
# So 3.3 V is BOTH the operating maximum AND the absolute maximum, on BOTH
# supplies.  D-787's derived power-save high side was 3.542487 V -- 242 mV over
# an absolute maximum -- and its NOMINAL 3.308989 V was 9 mV over it.  The
# module reseller's own abs-max row prints 4.6 V; where the two documents
# disagree this clause takes the CONSERVATIVE one, because the silicon that
# fails is the ILI9488's.
#
# SIX CLAUSES, each refused by a control below:
#   1  the rail's worst-case maximum is at or under the panel's absolute max
#   2  ...and under its DC operating maximum (the same 3.3 V here, kept
#      separate so a datasheet revision that splits them still binds)
#   3  the rail's heavy-load minimum is at or above the panel's VCI minimum
#   4  the three supply pads are ONE net
#   5  that net is the MCU's supply net, so VIH <= IOVCC holds by construction
#      and no display input can be driven above its own supply -- which is what
#      a separate display rail would have had to prove the hard way
#   6  the interface-mode straps and RD sit on that same supply
ILI9488 = dict(
    part="ER-TFT035IPS-6 (ILI9488 controller)",
    source="ILI Technology ILI9488 datasheet, version 100, archived at "
           "hardware/demo/kicad/aqroot-demo/vendor/ILITEK/ilitek-ili9488-v100.pdf",
    sha256="aeb23170f809610458e05ab514a5e3017344938ccdba1c2031acb453941df38b",
    vci_abs_max_V=3.3, vci_op_min_V=2.5, vci_op_max_V=3.3,
    iovcc_abs_max_V=3.3, iovcc_op_min_V=1.65, iovcc_op_max_V=3.3,
    input_over_iovcc_abs_max_V=0.3,
    supply_pads=("J1.40", "J1.41", "J1.42"),
    strap_pads=("J1.7", "J1.8", "J1.9", "J1.35"),
    mcu_supply_pads=("U1.2",))
DISPLAY_PRIMARY = (ROOT /
    "hardware/demo/kicad/aqroot-demo/vendor/ILITEK/ilitek-ili9488-v100.pdf")


def judge_display_supply(rail_min_V, rail_max_V, nets_by_contact, spec=None,
                         primary_sha=None):
    """The fitted panel's own limits against the rail it is actually on."""
    spec = ILI9488 if spec is None else spec
    supply_nets = {c: nets_by_contact.get(c) for c in spec["supply_pads"]}
    strap_nets = {c: nets_by_contact.get(c) for c in spec["strap_pads"]}
    mcu_nets = {c: nets_by_contact.get(c) for c in spec["mcu_supply_pads"]}
    one_net = (len(set(supply_nets.values())) == 1
               and None not in supply_nets.values())
    shared = one_net and set(supply_nets.values()) == set(mcu_nets.values())
    abs_max = min(spec["vci_abs_max_V"], spec["iovcc_abs_max_V"])
    d = dict(
        part=spec["part"], source=spec["source"],
        primary_sha256=primary_sha, expected_sha256=spec["sha256"],
        primary_archived=(primary_sha == spec["sha256"]),
        supply_nets=supply_nets, strap_nets=strap_nets,
        mcu_supply_nets=mcu_nets,
        rail_min_V=round(rail_min_V, 6), rail_max_V=round(rail_max_V, 6),
        vci_abs_max_V=spec["vci_abs_max_V"], vci_op_max_V=spec["vci_op_max_V"],
        vci_op_min_V=spec["vci_op_min_V"],
        iovcc_abs_max_V=spec["iovcc_abs_max_V"],
        iovcc_op_min_V=spec["iovcc_op_min_V"],
        display_supply_is_one_net=one_net,
        display_and_mcu_share_one_supply_net=shared,
        rail_max_under_absolute_maximum=(rail_max_V <= abs_max),
        rail_max_under_operating_maximum=(
            rail_max_V <= min(spec["vci_op_max_V"], spec["iovcc_op_max_V"])),
        rail_min_over_operating_minimum=(
            rail_min_V >= max(spec["vci_op_min_V"], spec["iovcc_op_min_V"])),
        absolute_margin_mV=round((abs_max - rail_max_V) * 1000, 4),
        every_display_input_is_at_or_below_its_own_iovcc=shared,
        input_overdrive_V=0.0 if shared else round(rail_max_V - rail_min_V, 6),
        input_overdrive_absolute_limit_V=spec["input_over_iovcc_abs_max_V"],
        strap_pads_are_on_the_display_supply=(
            set(strap_nets.values()) == set(supply_nets.values())),
        method="ILI9488 Table 41 (absolute maxima) and section 17.2 (DC "
               "characteristics for panel driving), read from the archived "
               "primary PDF rather than from the module reseller's summary.")
    d["ok"] = bool(d["primary_archived"] and d["display_supply_is_one_net"]
                   and d["display_and_mcu_share_one_supply_net"]
                   and d["rail_max_under_absolute_maximum"]
                   and d["rail_max_under_operating_maximum"]
                   and d["rail_min_over_operating_minimum"]
                   and d["every_display_input_is_at_or_below_its_own_iovcc"]
                   and d["strap_pads_are_on_the_display_supply"])
    return d["ok"], d


# --------------------------------------------------------------------------
# D-788 / R7-N02 -- A DC BOUND IS NOT THE WHOLE HIGH SIDE, AND THE LOW SIDE HAD
# NO MCU CLAUSE AT ALL.
#
# TWO GAPS, found while closing R7-D787-01 and neither of them raised by
# Round-7:
#
#  (a) THE HIGH SIDE.  `judge_display_supply` compares the rail's DC regulation
#      envelope with an ABSOLUTE MAXIMUM.  Output ripple and load-transient
#      overshoot ride ON TOP of that envelope, and the first D-788 draft left
#      47.97 mV of DC headroom under a DAMAGE limit without pricing either.
#
#  (b) THE LOW SIDE.  The rail's minimum was checked against the panel's VCI
#      2.5 V and against the Community Port's published connector minimum --
#      and NEVER against the ESP32-S3-WROOM-1's own supply minimum, which is
#      the tightest consumer on the whole low side.  Espressif's module
#      datasheet Table (Recommended Operating Conditions), archived at
#      vendor/Espressif/esp32-s3-wroom-1-datasheet.pdf, gives VDD33 as
#      3.0 / 3.3 / 3.6 V.  A rail that had drifted below 3.0 V would have
#      passed every clause in this file.
#
# WHAT IS PROVABLE AND WHAT IS NOT, STATED SEPARATELY.
#
# RIPPLE IS PROVABLE.  Forced PWM (PS/SYNC on EN, R7-D787-01) means continuous
# conduction at the oscillator frequency, and SLVS916I's EC table publishes
# that frequency as 2200 / 2400 / 2600 kHz.  With L at its own published
# minimum and the local output capacitance at a declared effective value, the
# buck-mode and boost-mode ripple expressions in SLVS916I 8.2.2 both evaluate
# to single-digit millivolts, and the worse of the two is charged to BOTH
# margins.
#
# LOAD-TRANSIENT OVERSHOOT IS NOT PROVABLE FROM ANYTHING THIS REPOSITORY CAN
# READ.  TI publishes the TPS6302x load transient as PLOTS (SLVS916I Figures
# 21/22, 50 mV/div, 500 mA -> 1500 mA on the fixed-output TPS63021 with 4 x
# 22 uF) and no numeric overshoot row exists in the EC table.  Reading a bound
# off a plot axis is not primary evidence, so this clause DOES NOT INVENT ONE.
# It does three things instead:
#
#   1  it prices ripple, which it can, and requires the DC+ripple corner to sit
#      inside the panel's absolute maximum AND above the module's own floor;
#   2  it requires the fitted divider to MAXIMISE the smaller of the two
#      remaining headrooms over the E192 0.1 % values that are actually
#      purchasable for R40 -- so the headroom that absorbs the unprovable term
#      is provably the largest this design can have, and the choice is
#      machine-checked rather than argued;
#   3  it requires a NAMED first-article acceptance to exist that measures the
#      real excursion at the display's own supply pins.
#
# THE ASYMMETRY IS WHY (2) MATTERS.  3.3 V is an ABSOLUTE MAXIMUM -- exceeding
# it damages the panel.  3.0 V is a RECOMMENDED MINIMUM -- dropping under it
# browns the MCU out and it reboots.  With 187 kOhm fitted the split was
# 47.97 mV under the damage limit against 96.99 mV over the recoverable one,
# which is the wrong way round; 189 kOhm splits it 76.98 / 69.41 mV.
ESP32S3_WROOM1 = dict(
    part="ESP32-S3-WROOM-1-N16R8",
    source="Espressif ESP32-S3-WROOM-1 datasheet, Recommended Operating "
           "Conditions, archived at hardware/demo/kicad/aqroot-demo/vendor/"
           "Espressif/esp32-s3-wroom-1-datasheet.pdf",
    vdd33_min_V=3.0, vdd33_nom_V=3.3, vdd33_max_V=3.6,
    supply_pads=("U1.2",))

P3V3_AC = dict(
    # SLVS916I EC: oscillator frequency 2200 / 2400 / 2600 kHz.  The MINIMUM is
    # the ripple-worst corner.
    f_switch_min_Hz=2.2e6,
    # Coilcraft XFL4020-152MEC, LCSC C3033018: 1.5 uH +/-20 %, Isat 4.6 A.
    l_nom_H=1.5e-6, l_tol=0.20,
    # C31 + C32, the two 22 uF 1206 X7R parts D-719 brought to 1.58 mm and
    # 3.52 mm of U12's VOUT lands.  The rest of the +3V3 net carries a further
    # ~104 uF nominal, which HELPS and is not counted here.
    local_c_refs=("C31", "C32"), local_c_nom_F=44.0e-6,
    # DECLARED, not measured: X7R tolerance plus DC bias at this rail.  Half of
    # nameplate is the conventional allowance for a 1206 X7R at ~20 % of its
    # rated voltage and it is pessimistic for a 16 V part at 3.2 V.
    local_c_effective_fraction=0.50,
    # DECLARED: effective parallel ESR of two 1206 MLCCs at 2.4 MHz.
    local_esr_ohm=0.002,
    # The rail's own input window: BQ25185 SYS floor to its charge ceiling.
    vin_min_V=3.0, vin_max_V=4.5,
    # The +3V3 plane between U12's output and U1's supply pad: In3 is a filled
    # +3V3 pour, so the delivery is a SHEET, not a track.  DECLARED at 10 mOhm,
    # which is roughly four times the 0.5 oz sheet resistance of the widest
    # plausible path and covers the local stubs and barrels.
    distribution_to_mcu_bound_ohm=0.010,
    # The E192 0.1 % values purchasable for R40 with R39 fixed at 1 MOhm.
    # `stock` is the live D-096 record; None means "no 0.1 % part in the
    # catalogue has any", which is itself a refusal under rule_open_sourcing.
    r40_candidates_ohm={182000.0: 5, 186000.0: 0, 187000.0: 6884,
                        189000.0: 339, 191000.0: 1282, 196000.0: 3},
    first_article_item="C-PWR-TRANSIENT-01",
)


def p3v3_ac_envelope(rail_min_V, rail_max_V, internal_load_A, spec=None):
    """Ripple, computed; transient, declared unprovable and deferred."""
    spec = P3V3_AC if spec is None else spec
    f = spec["f_switch_min_Hz"]
    l_min = spec["l_nom_H"] * (1.0 - spec["l_tol"])
    c_eff = spec["local_c_nom_F"] * spec["local_c_effective_fraction"]
    # Buck mode, VIN at its ceiling: the largest inductor ripple current.
    vin_hi = spec["vin_max_V"]
    dil_buck = rail_max_V * (vin_hi - rail_max_V) / (vin_hi * l_min * f)
    ripple_buck = dil_buck / (8.0 * f * c_eff) + dil_buck * spec["local_esr_ohm"]
    # Boost mode, VIN at its floor: the output capacitor carries the whole load
    # for the duty cycle.
    duty = max(0.0, 1.0 - spec["vin_min_V"] / rail_max_V)
    dil_boost = spec["vin_min_V"] * duty / (l_min * f)
    ripple_boost = (internal_load_A * duty / (f * c_eff)
                    + dil_boost * spec["local_esr_ohm"])
    ripple_pp = max(ripple_buck, ripple_boost)
    return dict(
        f_switch_min_Hz=f, inductor_min_H=l_min,
        local_output_c_refs=list(spec["local_c_refs"]),
        local_output_c_nominal_F=spec["local_c_nom_F"],
        local_output_c_effective_F=c_eff,
        local_output_c_effective_fraction=spec["local_c_effective_fraction"],
        inductor_ripple_buck_A=round(dil_buck, 6),
        inductor_ripple_boost_A=round(dil_boost, 6),
        ripple_buck_mV=round(ripple_buck * 1000, 4),
        ripple_boost_mV=round(ripple_boost * 1000, 4),
        ripple_pp_mV=round(ripple_pp * 1000, 4),
        ripple_pp_V=ripple_pp,
        method="SLVS916I 8.2.2 ripple expressions at the published minimum "
               "oscillator frequency and the inductor's own minimum "
               "inductance, over the declared effective local output "
               "capacitance; the worse of the buck and boost corners is "
               "charged to BOTH the high-side and low-side margins")


def r40_headroom(r40_ohm, r39_ohm, fb, abs_max_V, mcu_min_V,
                 distribution_drop_V):
    """min(headroom under the panel's abs max, headroom over the MCU floor)."""
    delta = max(abs(fb["reference_temp_C"] - fb["temp_min_C"]),
                abs(fb["temp_max_C"] - fb["reference_temp_C"]))
    err = 0.001 + 25.0e-6 * delta          # 0.1 % / 25 ppm on BOTH halves
    lo = r39_ohm * (1 - err) / (r40_ohm * (1 + err))
    hi = r39_ohm * (1 + err) / (r40_ohm * (1 - err))
    raw_lo = fb["vfb_V"][0] * (1 + lo)
    raw_hi = fb["vfb_V"][2] * (1 + hi)
    v_lo = raw_lo * (1 - fb["max_line_reg"]) * (1 - fb["max_load_reg"])
    v_hi = raw_hi * (1 + fb["max_line_reg"]) * (1 + fb["max_load_reg"])
    return dict(r40_ohm=r40_ohm,
                nominal_V=round(fb["vfb_V"][1] * (1 + r39_ohm / r40_ohm), 6),
                rail_min_V=round(v_lo, 6), rail_max_V=round(v_hi, 6),
                display_headroom_mV=round((abs_max_V - v_hi) * 1000, 3),
                mcu_headroom_mV=round(
                    (v_lo - distribution_drop_V - mcu_min_V) * 1000, 3),
                worst_headroom_mV=round(min(abs_max_V - v_hi,
                                            v_lo - distribution_drop_V
                                            - mcu_min_V) * 1000, 3))


def judge_p3v3_ac_and_centring(rail_min_V, rail_max_V, r39_ohm, r40_ohm,
                               internal_load_A, first_article_text,
                               spec=None, fb=None, panel=None, mcu=None):
    spec = P3V3_AC if spec is None else spec
    fb = P3V3_FB if fb is None else fb
    panel = ILI9488 if panel is None else panel
    mcu = ESP32S3_WROOM1 if mcu is None else mcu
    abs_max = min(panel["vci_abs_max_V"], panel["iovcc_abs_max_V"])
    mcu_min = mcu["vdd33_min_V"]
    ac = p3v3_ac_envelope(rail_min_V, rail_max_V, internal_load_A, spec)
    drop = spec["distribution_to_mcu_bound_ohm"] * internal_load_A

    # (1) the DC + ripple corners, both ends.
    high_corner = rail_max_V + ac["ripple_pp_V"]
    low_corner = rail_min_V - ac["ripple_pp_V"] - drop

    # (2) the centring proof: nothing purchasable does better.
    cands = {}
    for r, stock in sorted(spec["r40_candidates_ohm"].items()):
        h = r40_headroom(r, r39_ohm, fb, abs_max, mcu_min, drop)
        h["live_stock"] = stock
        h["purchasable"] = bool(stock) and stock >= 5 * 10
        cands["%g" % r] = h
    fitted = cands.get("%g" % r40_ohm)
    buyable = [h for h in cands.values() if h["purchasable"]]
    best = max((h["worst_headroom_mV"] for h in buyable), default=None)

    d = dict(
        ripple=ac,
        panel_absolute_max_V=abs_max,
        mcu=dict(part=mcu["part"], source=mcu["source"],
                 vdd33_min_V=mcu_min, supply_pads=list(mcu["supply_pads"])),
        distribution_to_mcu_bound_ohm=spec["distribution_to_mcu_bound_ohm"],
        internal_load_A=internal_load_A,
        distribution_drop_to_mcu_mV=round(drop * 1000, 4),
        dc_plus_ripple_high_V=round(high_corner, 6),
        dc_plus_ripple_low_at_the_mcu_V=round(low_corner, 6),
        high_corner_under_absolute_maximum=bool(high_corner <= abs_max),
        low_corner_over_the_mcu_minimum=bool(low_corner >= mcu_min),
        headroom_after_ripple_high_mV=round((abs_max - high_corner) * 1000, 4),
        headroom_after_ripple_low_mV=round((low_corner - mcu_min) * 1000, 4),
        r40_fitted_ohm=r40_ohm,
        r40_candidates=cands,
        best_purchasable_worst_headroom_mV=best,
        fitted_is_the_best_purchasable_centring=bool(
            fitted is not None and fitted["purchasable"] and best is not None
            and fitted["worst_headroom_mV"] >= best - 1e-9),
        load_transient_is_deferred_to_first_article=True,
        load_transient_basis=(
            "TI publishes the TPS6302x load transient only as SLVS916I "
            "Figures 21/22 (50 mV/div, 500 mA -> 1500 mA, TPS63021, 4 x "
            "22 uF); there is no numeric overshoot row in the EC table, so "
            "NO analytic bound is claimed here.  The headroom that has to "
            "absorb it is instead made as large as any purchasable E192 "
            "0.1 % value allows, and the real excursion is MEASURED at first "
            "article.  If that measurement eats the headroom the lever is "
            "C29-C32 on their existing 1206 lands -- more output capacitance, "
            "no PCB change -- because SLVS916I 8.2.2.3 sets no upper limit on "
            "output capacitance"),
        first_article_item=spec["first_article_item"],
        first_article_named=bool(
            spec["first_article_item"] in (first_article_text or "")),
        method="ripple is COMPUTED and charged to both ends; load-transient "
               "overshoot is DECLARED unprovable from published data and "
               "deferred to a named first-article measurement; the divider is "
               "proved to be the best-centred purchasable choice so the "
               "deferred term has the largest headroom this design can give it")
    d["ok"] = bool(d["high_corner_under_absolute_maximum"]
                   and d["low_corner_over_the_mcu_minimum"]
                   and d["fitted_is_the_best_purchasable_centring"]
                   and d["first_article_named"])
    return d["ok"], d


ACC_3V3_REINFORCEMENT = ROOT / "docs/full-beta-v2/assembly/ACC_3V3_REINFORCEMENT.json"
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
    series="Molex Micro-Lock Plus 2.0 W/W",
    what="manual J4 board pigtail plus frozen detachable battery harness",
    harness="docs/full-beta-v2/assembly/BATTERY_HARNESS.json",
    evidence="hardware/demo/kicad/aqroot-demo/vendor/MOLEX/"
             "micro-lock-plus-5055700003-PS-A6.txt",
)


def battery_connection_facts(spec=None):
    """D-781 battery connection, derived from the frozen harness record and
    a concise transcription of Molex primary document 5055700003-PS A6."""
    spec = BATTERY_CONNECTION if spec is None else spec
    d = dict(reference=spec["reference"], series=spec["series"], what=spec["what"],
             harness=spec["harness"], evidence=spec["evidence"], rating_A=None,
             rating_gauge_awg=None, applicable_wire_awg=None,
             pack_lead_awg=None, board_lead_awg=None,
             harness_identity_exact=False, polarity_exact=False,
             board_precrimps_are_primary_source_proven=False,
             rating_was_read_from_primary_transcription=False,
             rated_current_in_harness_matches_primary=False,
             pack_lead_is_inside_the_applicable_wire_range=False,
             board_lead_is_inside_the_applicable_wire_range=False)
    hp = ROOT / spec["harness"]; ep = ROOT / spec["evidence"]
    if not hp.exists() or not ep.exists():
        return d
    h = json.loads(hp.read_text(encoding="utf-8"))
    txt = ep.read_text(encoding="utf-8", errors="replace")
    controlling = h.get("controlling_rating", {})
    gauge = int(controlling.get("wire_AWG", 0) or 0)
    m = re.search(r"AWG%s\s+([0-9.]+)\s*A" % gauge, txt)
    d["rating_A"] = float(m.group(1)) if m else None
    d["rating_gauge_awg"] = gauge or None
    d["applicable_wire_awg"] = [22, 26]
    d["pack_lead_awg"] = h.get("battery_side", {}).get("factory_lead_AWG")
    d["board_lead_awg"] = h.get("board_side", {}).get("wire_AWG")
    d["pack_lead_is_inside_the_applicable_wire_range"] = bool(
        d["pack_lead_awg"] in (22, 24, 26))
    d["board_lead_is_inside_the_applicable_wire_range"] = bool(
        d["board_lead_awg"] in (22, 24, 26))
    exact = (h.get("board_side", {}).get("receptacle_housing") == "5055700201"
             and h.get("board_side", {}).get("precrimp_red", "").startswith("Molex 2175012101")
             and h.get("board_side", {}).get("precrimp_black", "").startswith("Molex 2175011101")
             and h.get("battery_side", {}).get("plug_housing") == "2137192021"
             and h.get("battery_side", {}).get("male_terminal") == "2137201000"
             and h.get("battery_side", {}).get("hand_crimp_tool") == "Molex 213309-5900")
    d["harness_identity_exact"] = exact
    d["board_precrimps_are_primary_source_proven"] = all(x in txt for x in (
        "2175012101 = Micro-Lock Plus 2.0 female-to-pigtail",
        "75.00 mm, 26 AWG, RED, UL 10002",
        "2175011101 = Micro-Lock Plus 2.0 female-to-pigtail",
        "75.00 mm, 26 AWG, BLACK, UL 10002"))
    pol = h.get("polarity", {})
    d["polarity_exact"] = (pol.get("cavity_1") == "BAT+ / red / J4.1"
                            and pol.get("cavity_2") == "GND / black / J4.2")
    d["rating_was_read_from_primary_transcription"] = bool(
        m and "Document: 5055700003-PS" in txt and "Revision A6" in txt)
    d["rated_current_in_harness_matches_primary"] = (
        d["rating_A"] is not None
        and abs(float(controlling.get("rated_current_A", -1)) - d["rating_A"]) < 1e-9)
    bs = h.get("battery_side", {})
    d["battery_lead_insulation_od_must_be_measured"] = (
        bs.get("factory_lead_insulation_OD_mm") == "MEASURE_EACH_INCOMING_PACK")
    d["battery_terminal_od_range_is_frozen"] = (
        bs.get("terminal_allowed_insulation_OD_mm") == [0.90, 1.50]
        and bs.get("first_five_target_insulation_OD_mm") == [0.96, 1.50])
    acceptance = " ".join(h.get("acceptance", []))
    d["finished_j4_hole_fit_check_is_required"] = (
        "actual finished J4 0.75 mm PTH" in acceptance)
    d["normal_rating_basis"] = (
        "Molex 5055700003-PS A6 section 4.2; AWG26 is the lower-rated "
        "conductor on both sides of the 26AWG/26AWG harness")
    return d
P3V3_DUAL_RAIL_RESERVE = ()  # D-781: rated harness restores full feature concurrency
NORMAL_DUAL_INTERNAL_CEILING_A = I_INTERNAL  # no product-visible internal reserve

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
# Round-4 R4-05: RF/crystal capacitors need explicit differential-voltage
# bounds, not a silent "unknown DC node" exemption.  For the ST25R3916 path,
# use the part's 350 mArms internal VDD_RF-regulator current limit as a
# deliberately conservative per-arm ceiling.  At 13.56 MHz: the parallel
# C69+C73 (and C70+C74) shunt is 1.6 nF -> 3.63 Vpk at 350 mArms; each 300 pF
# series match C71/C72 is 19.37 Vpk.  Adding the EMC-node bound, 1.1-ohm
# damping drop, and the <=3 Vpp RFI operating limit bounds the 27 pF receive
# series parts below 25.5 Vpk.  All are fitted 50 V C0G.  First-article NFC
# tuning must still scope RFI <=3 Vpp and record the differential waveforms.
CAP_NON_DC_PROOFS = {
    **{ref: dict(absolute_V=4.0,
                 basis="ST25R3916 <=350 mArms regulated TX ceiling; 1.6 nF EMC shunt at 13.56 MHz gives <=3.63 Vpk; first-article scope")
       for ref in ("C69", "C70", "C73", "C74")},
    **{ref: dict(absolute_V=20.0,
                 basis="ST25R3916 <=350 mArms regulated TX ceiling through 300 pF at 13.56 MHz gives <=19.37 Vpk; first-article scope")
       for ref in ("C71", "C72")},
    **{ref: dict(absolute_V=26.0,
                 basis="receive-series bound: <=4.0 Vpk EMC node + <=19.37 Vpk 300 pF match + <=0.55 Vpk 1.1R damping + <=1.5 Vpk RFI (3 Vpp operating max); first-article scope")
       for ref in ("C75", "C77")},
    **{ref: dict(absolute_V=1.5,
                 basis="ST25R3916 RFI operating amplitude <=3 Vpp = 1.5 Vpk; first-article scope")
       for ref in ("C76", "C78")},
    "C79": dict(absolute_V=3.6,
                 basis="27.12 MHz crystal load on ST25R3916 3.3 V domain"),
    "C80": dict(absolute_V=3.6,
                 basis="27.12 MHz crystal load on ST25R3916 3.3 V domain"),
}
# Bind every non-DC proof to the exact non-ground nets it was derived for.
# A proof for C71 on NFC_EMCA<->NFC_MATCH_A must not silently authorize the
# same reference after one terminal is moved to an unrelated unknown net.
_CAP_NON_DC_NETS = {
    # D-787 / R6-E03. Bind proofs to KiCad's COMPLETE canonical net names.
    # Leaf names are not identities: /OTHER/NFC_EMCA is not the NFC front end.
    "C69": ("/04_SPI_B_RADIOS_NFC/NFC_EMCA",),
    "C70": ("/04_SPI_B_RADIOS_NFC/NFC_EMCB",),
    "C71": ("/04_SPI_B_RADIOS_NFC/NFC_EMCA", "/04_SPI_B_RADIOS_NFC/NFC_MATCH_A"),
    "C72": ("/04_SPI_B_RADIOS_NFC/NFC_EMCB", "/04_SPI_B_RADIOS_NFC/NFC_MATCH_B"),
    "C73": ("/04_SPI_B_RADIOS_NFC/NFC_EMCA",),
    "C74": ("/04_SPI_B_RADIOS_NFC/NFC_EMCB",),
    "C75": ("/04_SPI_B_RADIOS_NFC/NFC_ANT_A", "/04_SPI_B_RADIOS_NFC/NFC_RXA"),
    "C76": ("/04_SPI_B_RADIOS_NFC/NFC_RXA",),
    "C77": ("/04_SPI_B_RADIOS_NFC/NFC_ANT_B", "/04_SPI_B_RADIOS_NFC/NFC_RXB"),
    "C78": ("/04_SPI_B_RADIOS_NFC/NFC_RXB",),
    "C79": ("/04_SPI_B_RADIOS_NFC/NFC_XOUT",),
    "C80": ("/04_SPI_B_RADIOS_NFC/NFC_XIN",),
}
for _ref, _nets in _CAP_NON_DC_NETS.items():
    CAP_NON_DC_PROOFS[_ref]["nets"] = tuple(sorted(_nets))


CAP_DERATE_EXCEPTIONS = {
    "C65": "boost output capacitance, measured against D-773's DERIVED "
           "worst-case setpoint of 5.165 V.  D-186 sizes this rail at 44 uF "
           "NOMINAL across C65+C66 because a 10 V X7R at 5 V bias retains about "
           "half; a 22 uF 16 V X7R is a 1206 part and does not fit the 0805 "
           "land.  Survives the 6.0 V absolute at 1.67x.  THIS ONE IS REAL: "
           "the BOM buys a 10 V part and the value string says 10 V",
    "C66": "the other half of the same 44 uF nominal pair; see C65",
}

# D-783.  A distributor record is usable only when it identifies the SAME
# purchased part, not merely the same LCSC code.  Manufacturer spelling is
# normalized only through explicit aliases observed in the frozen BOM/cache;
# package comes from the KiCad footprint's EIA size and must match the record.
_CAP_MFR_ALIASES = {
    "murata": "murataelectronics",
}


def _norm_cap_mfr(name):
    key = re.sub(r"[^a-z0-9]+", "", (name or "").casefold())
    return _CAP_MFR_ALIASES.get(key, key)


def _bom_cap_package(footprint):
    m = re.search(r"(?:^|:)C_(\d{4})(?:_|$)", footprint or "")
    return m.group(1) if m else ""


def _norm_cap_package(package):
    """Canonical EIA size for BOM/cache comparisons (R6-E04)."""
    raw = (package or "").strip()
    m = re.search(r"(?<!\d)(0201|0402|0603|0805|1206|1210|1812|2010|2512)(?!\d)", raw)
    if m:
        return m.group(1)
    return re.sub(r"[^a-z0-9]+", "", raw.casefold())


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
        bom_mpn = (row.get("MPN") or "").strip()
        bom_mfr = (row.get("Manufacturer") or "").strip()
        bom_footprint = (row.get("Footprint") or "").strip()
        bom_package = _bom_cap_package(bom_footprint)
        record_mpn = (rec.get("componentModelEn") or "").strip()
        record_mfr = (rec.get("componentBrandEn") or "").strip()
        record_package = (rec.get("componentSpecificationEn") or "").strip()
        identity_matches = bool(
            bom_mpn and record_mpn and
            bom_mpn.casefold() == record_mpn.casefold() and
            _norm_cap_mfr(bom_mfr) and
            _norm_cap_mfr(bom_mfr) == _norm_cap_mfr(record_mfr) and
            bom_package and record_package and
            _norm_cap_package(bom_package) == _norm_cap_package(record_package))
        out[ref] = dict(
            lcsc=code, mpn=bom_mpn, manufacturer=bom_mfr,
            bom_footprint=bom_footprint, bom_package=bom_package,
            record_mpn=record_mpn, record_manufacturer=record_mfr,
            record_package=record_package, identity_matches=identity_matches,
            rating_V=rating, read_from=how, record=name,
            describe=rec.get("describe") or "")
    return out


# --------------------------------------------------------------------------
# D-788 / R7-D787-07 -- THE DC BOUND IS BOUND TO THE FULL HIERARCHICAL NET.
#
# `screen_bom_sourcing.NET_MAX_DC` is keyed by LEAF name, because the screen it
# was written for proposes parts for a net NAME.  F8 then looked a pad's node up
# with `canonical if canonical in net_max_dc else leaf`, and that `else leaf`
# is a wildcard over hierarchy: Round-7 put `C20` on `/ALIEN/USB_VBUS_RAW` and
# `C33` on `/ALIEN/BQ25185_SYS` and both inherited the real rails' 5.25/5.5 V
# and 4.5/5.5 V bounds, because the leaf still matched.  A capacitor on a net
# this repository has never established a voltage for was proved safe against a
# voltage established for a different net.
#
# THE MAP IS NOW EXPLICIT AND COMPLETE, keyed by the net name the BOARD carries,
# valued by the `NET_MAX_DC` row it is proven to be.  There is no fallback.  An
# unlisted net is UNKNOWN, and an unknown node has to carry a named non-DC proof
# or the part is refused.  Three clauses keep the map honest: every key must be
# a net that EXISTS on the board, every value must be a `NET_MAX_DC` row, and
# the key's own leaf must EQUAL the row it names unless `PROVEN_DC_ALIASES`
# carries an explicit reason -- so a cross-hierarchy alias can never be silent.
CANONICAL_DC_NETS = {
    "+3V3": "+3V3",
    "GND": "GND",
    "Net-(U1-EN)": "Net-(U1-EN)",
    "/ACC_3V3_SW": "ACC_3V3_SW",
    "/ACC_5V_SW": "ACC_5V_SW",
    "/NFC_SUPPLY": "NFC_SUPPLY",
    "/01_POWER_TREE/ACC_5V_RAW": "ACC_5V_RAW",
    "/01_POWER_TREE/BAT_PROTECTED_P": "BAT_PROTECTED_P",
    "/01_POWER_TREE/BAT_RAW": "BAT_RAW",
    "/01_POWER_TREE/BQ25185_SYS": "BQ25185_SYS",
    "/01_POWER_TREE/LTC_GATE_RC": "LTC_GATE_RC",
    "/01_POWER_TREE/N_BATDIV": "N_BATDIV",
    "/01_POWER_TREE/USB_VBUS_CHG": "USB_VBUS_CHG",
    "/01_POWER_TREE/USB_VBUS_RAW": "USB_VBUS_RAW",
    "/01_POWER_TREE/VBUS_PRESENT": "VBUS_PRESENT",
    "/01_POWER_TREE/VREC_VCC": "VREC_VCC",
    "/03_SPI_A_DISPLAY_SD/BL_DISC_G": "BL_DISC_G",
    "/03_SPI_A_DISPLAY_SD/LED_BOOST": "LED_BOOST",
    "/04_SPI_B_RADIOS_NFC/NFC_AGDC": "NFC_AGDC",
    "/04_SPI_B_RADIOS_NFC/NFC_VDD_A": "NFC_VDD_A",
    "/04_SPI_B_RADIOS_NFC/NFC_VDD_AM": "NFC_VDD_AM",
    "/04_SPI_B_RADIOS_NFC/NFC_VDD_D": "NFC_VDD_D",
    "/04_SPI_B_RADIOS_NFC/NFC_VDD_RF": "NFC_VDD_RF",
    "/07_IR/IR_RX_VS_LOCAL": "IR_RX_VS_LOCAL",
}
# A cross-hierarchy alias may exist only with a reason written down.  It is
# EMPTY on this board and the clause below is what keeps it that way.
PROVEN_DC_ALIASES = {}


def judge_canonical_dc_map(board, net_max_dc, canonical=None, aliases=None):
    """The hierarchical DC map, checked against the board and the DC table."""
    canonical = CANONICAL_DC_NETS if canonical is None else canonical
    aliases = PROVEN_DC_ALIASES if aliases is None else aliases
    info = board.GetNetInfo()
    board_nets = {info.GetNetItem(i).GetNetname()
                  for i in range(info.GetNetCount())}
    problems = []
    for full, key in sorted(canonical.items()):
        if full not in board_nets:
            problems.append("canonical DC net %r is not a net on this board"
                            % full)
        if key not in net_max_dc:
            problems.append("canonical DC net %r names %r, which is not a "
                            "NET_MAX_DC row" % (full, key))
            continue
        if full.rsplit("/", 1)[-1] != key and full not in aliases:
            problems.append("canonical DC net %r aliases the unrelated row %r "
                            "with no entry in PROVEN_DC_ALIASES" % (full, key))
    return (not problems), dict(
        entries=len(canonical), aliases=dict(aliases), problems=problems,
        method="every DC bound is keyed by the FULL hierarchical net the board "
               "carries; there is no leaf fallback, so a net with a different "
               "hierarchy is UNKNOWN and must carry a named non-DC proof")


def judge_capacitor_derating(board, dnp_refs, net_max_dc, exceptions=None,
                             purchased=None, non_dc_proofs=None, canonical_dc=None,
                             net_rewrite=None):
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
    # D-788 / R7-D787-07.  The ONLY DC lookup.  No leaf fallback exists.
    canonical_dc = (CANONICAL_DC_NETS if canonical_dc is None else canonical_dc)
    net_rewrite = net_rewrite or {}
    purchased = purchased_capacitor_ratings() if purchased is None else purchased
    non_dc_proofs = CAP_NON_DC_PROOFS if non_dc_proofs is None else non_dc_proofs
    rows, no_record, identity_mismatch, understated = [], [], [], []
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
        mpn_ok = bool((buy.get("mpn") or "") and (buy.get("record_mpn") or "") and
                      (buy.get("mpn") or "").casefold() ==
                      (buy.get("record_mpn") or "").casefold())
        mfr_ok = bool(_norm_cap_mfr(buy.get("manufacturer")) and
                      _norm_cap_mfr(buy.get("manufacturer")) ==
                      _norm_cap_mfr(buy.get("record_manufacturer")))
        package_ok = bool((buy.get("bom_package") or "") and
                          (buy.get("record_package") or "") and
                          _norm_cap_package(buy.get("bom_package")) ==
                          _norm_cap_package(buy.get("record_package")))
        if not (mpn_ok and mfr_ok and package_ok):
            identity_mismatch.append([
                ref, buy.get("lcsc"), buy.get("mpn"), buy.get("record_mpn"),
                buy.get("manufacturer"), buy.get("record_manufacturer"),
                buy.get("bom_package"), buy.get("record_package")])
            rows.append(dict(
                ref=ref, value=value, lcsc=buy.get("lcsc"), mpn=buy.get("mpn"),
                record_mpn=buy.get("record_mpn"),
                manufacturer=buy.get("manufacturer"),
                record_manufacturer=buy.get("record_manufacturer"),
                bom_package=buy.get("bom_package"),
                record_package=buy.get("record_package"),
                purchased_record_identity_mismatch=True))
            continue
        rating = buy["rating_V"]
        op = ab = 0.0
        unknown, nonground = [], []
        for pad in fp.Pads():
            net = net_rewrite.get(pad.GetNetname(), pad.GetNetname())
            leaf = net.rsplit("/", 1)[-1]
            if leaf == "GND" or not leaf:
                continue
            # R6-E03: non-DC evidence is bound to the complete canonical net.
            # D-788 / R7-D787-07: SO IS THE DC EVIDENCE.  The bound is looked up
            # by the FULL hierarchical name through the explicit canonical map;
            # the `else leaf` fallback that let `/ALIEN/USB_VBUS_RAW` inherit
            # `USB_VBUS_RAW`'s 5.25/5.5 V is gone.
            canonical = net or leaf
            nonground.append(canonical)
            dc_key = canonical_dc.get(canonical)
            if dc_key is not None and dc_key in net_max_dc:
                op = max(op, net_max_dc[dc_key][0])
                ab = max(ab, net_max_dc[dc_key][1])
            else:
                unknown.append(canonical)
        proof = None
        if unknown:
            proof = non_dc_proofs.get(ref)
            actual_nets = sorted(set(nonground))
            proof_nets = sorted(set((proof or {}).get("nets") or ()))
            if not proof or proof_nets != actual_nets:
                unestablished.append([ref, sorted(set(unknown))])
                rows.append(dict(
                    ref=ref, value=value, rating_V=rating,
                    mpn=buy["mpn"], lcsc=buy["lcsc"],
                    nodes_not_established=sorted(set(unknown)),
                    current_non_ground_nodes=actual_nets,
                    named_proof_nodes=proof_nets))
                continue
            # The named bound is differential/peak evidence for THIS exact set
            # of terminals.  If a known DC terminal is also present, retain the
            # larger of that absolute bound and the named differential bound.
            ab = max(ab, float(proof["absolute_V"]))
        if unknown and op == 0.0:
            ok_abs = rating >= ab
            if not ok_abs:
                fails_absolute.append([ref, buy["mpn"], rating, ab])
            spec_ok_abs = True
            if spec_V is not None:
                spec_ok_abs = spec_V >= ab
                if not spec_ok_abs:
                    spec_fails_absolute.append([ref, value, spec_V, ab])
                if spec_V > rating:
                    spec_overstates.append([ref, value, spec_V,
                                            buy["mpn"], rating])
                elif spec_V < rating:
                    understated.append([ref, value, spec_V,
                                         buy["mpn"], rating])
            rows.append(dict(
                ref=ref, value=value, mpn=buy["mpn"], lcsc=buy["lcsc"],
                rating_V=rating, rating_read_from=buy["read_from"],
                rating_record=buy["record"], specified_V=spec_V,
                non_dc_nodes=sorted(set(nonground)), non_dc_absolute_V=ab,
                non_dc_basis=proof["basis"], survives_absolute=ok_abs,
                meets_derating=None,
                specification_survives_absolute=spec_ok_abs,
                excused_by_a_named_exception=False))
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
        purchased_record_identity_mismatches=sorted(identity_mismatch),
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
        method="screen_bom_sourcing.NET_MAX_DC supplies established DC bounds. "
               "RATINGS COME FROM THE EXACT PART THE BOM BUYS -- reference -> "
               "LCSC -> committed distributor record -- and BOM MPN, normalized "
               "manufacturer, and EIA package must all match that record before "
               "its voltage rating is usable.  A fitted capacitor touching any "
               "otherwise unestablished RF/crystal node is REFUSED unless "
               "CAP_NON_DC_PROOFS gives a bound tied to the exact current "
               "non-ground net set; the NFC bounds derive from the ST25R3916 "
               "350 mArms regulated-TX ceiling and 3 Vpp RFI limit and remain "
               "subject to first-article waveform verification.")
    # D-787 / R6-E04.  THE PACKAGE ALIAS RULE IS BOUNDED, AND SAYS SO.
    # `_norm_cap_package` exists so `0805` and `0805 (2012 Metric)` are one
    # package rather than an identity mismatch.  A normalizer that also
    # collapsed two DIFFERENT sizes would silently authorize the wrong part, so
    # the rule is asserted here rather than trusted, and the count of rows it
    # actually changes is printed: on this board it is ZERO, i.e. the rule is
    # currently inert and every identity leg is an exact match.  A metric-only
    # spelling with no EIA code (`1005 Metric`) does NOT normalize and is
    # refused -- conservative in the safe direction.
    alias_rows = sum(
        1 for v in purchased.values()
        if isinstance(v, dict) and (v.get("bom_package") or "")
        and (v.get("record_package") or "")
        and (v["bom_package"].casefold() != v["record_package"].casefold()))
    d["package_alias_rule"] = dict(
        accepts_the_same_size_written_with_its_metric_code=(
            _norm_cap_package("0805 (2012 Metric)")
            == _norm_cap_package("0805")),
        refuses_a_metric_code_for_a_different_size=(
            _norm_cap_package("2012 Metric") != _norm_cap_package("0603")),
        refuses_a_different_eia_size=(
            _norm_cap_package("0201") != _norm_cap_package("0805")),
        refuses_a_metric_only_spelling_with_no_eia_code=(
            _norm_cap_package("1005 Metric") != _norm_cap_package("0402")),
        rows_the_rule_changes_on_this_board=alias_rows)
    d["the_package_alias_rule_is_bounded"] = all(
        v for k, v in d["package_alias_rule"].items() if isinstance(v, bool))
    d["every_fitted_capacitor_has_a_purchased_voltage_rating"] = not no_record
    d["every_fitted_capacitor_has_a_dc_or_named_non_dc_voltage_bound"] = not unestablished
    d["every_purchased_rating_record_matches_bom_identity"] = not identity_mismatch
    # Compatibility alias for existing evidence readers; D-783 broadens this
    # old MPN-only name to the complete MPN/manufacturer/package predicate.
    d["every_purchased_rating_record_matches_the_bom_mpn"] = \
        d["every_purchased_rating_record_matches_bom_identity"]
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
    d["ok"] = (d["the_package_alias_rule_is_bounded"]
               and d["every_fitted_capacitor_has_a_purchased_voltage_rating"]
               and d["every_fitted_capacitor_has_a_dc_or_named_non_dc_voltage_bound"]
               and d["every_purchased_rating_record_matches_the_bom_mpn"]
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


def live_stock_for(mpn):
    """{stock, brand, record} from the COMMITTED exact-MPN distributor record.

    D-787.  `rule_open_sourcing` refuses a candidate whose stock is under the
    first-five liquidity floor -- but only while SELECTING.  Once an MPN is
    written into the schematic nothing looked at stock again, and the first
    D-787 draft shipped a locked `R40` whose live record reads **zero**.  This
    reads the archived record for the exact locked part, so the check is
    deterministic and replays from the committed evidence rather than the
    network.  `None` means no exact-MPN record is archived at all.
    """
    import jlc_live
    path = (MFG / "evidence/jlc-live" / (jlc_live.slug(mpn) + ".json")) \
        if mpn else None
    if not path or not path.exists():
        return None
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    for rec in doc.get("records") or ():
        if (rec.get("componentModelEn") or "").casefold() == mpn.casefold():
            return dict(record=path.name, stock=rec.get("stockCount") or 0,
                        brand=rec.get("componentBrandEn"),
                        lcsc=rec.get("componentCode"),
                        fetched_utc=doc.get("fetched_utc"))
    return dict(record=path.name, stock=None, brand=None, lcsc=None,
                fetched_utc=doc.get("fetched_utc"))


def schematic_mpns(refs):
    """{ref: the MPN the SCHEMATIC buys}, read off the hierarchical sheets.

    D-787.  The PCB footprints carry only Reference/Value, so a part identity
    that a proof depends on -- the TPS63020 divider's tolerance and temperature
    coefficient -- can only be read here.  A reference whose symbol carries no
    MPN comes back as the empty string rather than absent, so a caller keyed on
    it refuses instead of falling through.
    """
    want, out = set(refs), {}
    for sheet in sorted(rl.PROJECT.glob("*.kicad_sch")):
        text = sheet.read_text(encoding="utf-8", errors="replace")
        for ref in want - set(out):
            idx = text.find('(property "Reference" "%s"' % ref)
            if idx < 0:
                continue
            block = text[idx:idx + 9000]
            nxt = block.find('(property "Reference" "', 1)
            if nxt > 0:
                block = block[:nxt]
            m = re.search(r'\(property "MPN" "([^"]*)"', block)
            out[ref] = m.group(1) if m else ""
    return {ref: out.get(ref, "") for ref in want}


def judge_accessory_envelope(values, single_floor=None, dual_floor=None,
                             live_ohms=None, internal_ceiling=None,
                             connection=None, reserve=None, mpns=None):
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

    # ---- D-787 / R6-A01: derive the actual main +3V3 envelope ------------
    p3_top = _ohms(values.get(P3V3_FB["top"]))
    p3_bot = _ohms(values.get(P3V3_FB["bottom"]))
    p3_top_tol = _tol(values.get(P3V3_FB["top"]))
    p3_bot_tol = _tol(values.get(P3V3_FB["bottom"]))
    if not p3_top or not p3_bot:
        return False, dict(error="3V3 divider unreadable: %s=%r %s=%r" %
                           (P3V3_FB["top"], values.get(P3V3_FB["top"]),
                            P3V3_FB["bottom"], values.get(P3V3_FB["bottom"])))
    temp_delta = max(abs(P3V3_FB["temp_min_C"] - P3V3_FB["reference_temp_C"]),
                     abs(P3V3_FB["temp_max_C"] - P3V3_FB["reference_temp_C"]))
    # D-787.  TCR comes from the PURCHASED PART, keyed by MPN.  An MPN this
    # table does not know has no published coefficient here and the clause
    # REFUSES; it does not silently inherit the previous part's number.
    divider_mpns = dict(P3V3_FB["released_mpns"])
    divider_mpns.update({k: v for k, v in (mpns or {}).items()
                         if k in divider_mpns})
    top_tcr = P3V3_FB["tcr_ppm_per_C_by_mpn"].get(divider_mpns[P3V3_FB["top"]])
    bot_tcr = P3V3_FB["tcr_ppm_per_C_by_mpn"].get(
        divider_mpns[P3V3_FB["bottom"]])
    divider_parts_are_known = top_tcr is not None and bot_tcr is not None
    # A refusal must not crash the report: run the arithmetic at a coefficient
    # no thin-film 0603 part exceeds so the numbers printed beside the refusal
    # are still bounded, and let the CLAUSE carry the verdict.
    top_err = p3_top_tol + (top_tcr if top_tcr is not None else 200.0) \
        * 1e-6 * temp_delta
    bot_err = p3_bot_tol + (bot_tcr if bot_tcr is not None else 200.0) \
        * 1e-6 * temp_delta
    p3_ratio_lo = p3_top * (1 - top_err) / (p3_bot * (1 + bot_err))
    p3_ratio_hi = p3_top * (1 + top_err) / (p3_bot * (1 - bot_err))
    p3_vfb = P3V3_FB["vfb_V"]
    p3_raw_lo = p3_vfb[0] * (1 + p3_ratio_lo)
    p3_raw_nom = p3_vfb[1] * (1 + p3_top / p3_bot)
    p3_raw_hi = p3_vfb[2] * (1 + p3_ratio_hi)
    # Heavy-load minimum pays both published line and load regulation maxima.
    p3_pwm_heavy_lo = p3_raw_lo * (1 - P3V3_FB["max_line_reg"]) * (
        1 - P3V3_FB["max_load_reg"])
    # Full-load pack current is costed at the opposite PWM corner.
    p3_pwm_heavy_hi = p3_raw_hi * (1 + P3V3_FB["max_line_reg"]) * (
        1 + P3V3_FB["max_load_reg"])
    # In power-save mode TI permits the output up to +5% relative to VFB_PWM.
    # This is the light-load HIGH-side consumer-safety check.
    p3_ps_hi = p3_raw_hi * (1 + P3V3_FB["ps_high_relative_to_pwm"]) * (
        1 + P3V3_FB["max_line_reg"])

    reinforcement = {}
    if ACC_3V3_REINFORCEMENT.exists():
        reinforcement = json.loads(ACC_3V3_REINFORCEMENT.read_text())
    reinf_r = (float(reinforcement.get("electrical_acceptance", {})
                     .get("each_finished_lead_max_milliohm_at_room_temperature", 1e9))
               / 1000.0)
    reinforcement_identity_ok = bool(
        reinforcement.get("source", {}).get("reference") == "TP12.1"
        and reinforcement.get("source", {}).get("net") == "/ACC_3V3_SW"
        and {x.get("reference") for x in reinforcement.get("destinations", [])}
            == {"J5.3"}
        and reinforcement.get("wire", {}).get("mpn") == "2842/19 RD005"
        and reinforcement.get("wire", {}).get("gauge_awg") == 28
        and reinf_r <= 0.025 + 1e-12)

    # ---- D-788 / R7-D787-02 + R7-D787-03: THE COMPLETE LOOP ---------------
    # Every contact is priced ALONE, forward AND return, from U12's output to
    # the J5 mating interface.  U20's RON is taken at the rail's own heavy-load
    # MINIMUM rather than at the datasheet's 3.3 V condition.
    k_hot = 1 + CU_TC_PER_K * CU_HOT_RISE_K
    p3_ron = tps22950_ron_max(p3_pwm_heavy_lo)
    # Everything in the loop that both duplicated contacts share.
    shared_ohm = (P3V3_DELIVERY["source_bound_ohm"] * k_hot
                  + P3V3_DELIVERY["signal_contact_ohm"]
                  + P3V3_DELIVERY["signal_contact_ohm"]
                  / P3V3_DELIVERY["gnd_contacts_in_parallel"]
                  + P3V3_DELIVERY["gnd_return_bound_ohm"] * k_hot
                  + P3V3_DELIVERY["process_ohm"])
    p3_paths = {}
    for contact, spec in sorted(P3V3_DELIVERY["contacts"].items()):
        board = spec["board_copper_bound_ohm"] * k_hot
        lead = reinf_r * k_hot if spec["reinforced"] else 0.0
        total = p3_ron + shared_ohm + board + lead
        delivered = p3_pwm_heavy_lo - (
            PUBLISHED_RAIL_BUDGET_A["ACC_3V3"] * total)
        p3_paths[contact] = dict(
            what=spec["what"], reinforced=spec["reinforced"],
            u20_ron_ohm=round(p3_ron, 6),
            board_copper_bound_ohm=spec["board_copper_bound_ohm"],
            board_copper_hot_ohm=round(board, 6),
            manual_lead_hot_ohm=round(lead, 6),
            shared_source_return_and_contact_ohm=round(shared_ohm, 6),
            total_series_ohm=round(total, 6),
            drop_at_published_budget_mV=round(
                PUBLISHED_RAIL_BUDGET_A["ACC_3V3"] * total * 1000, 4),
            delivered_at_400mA_min_V=round(delivered, 6))
    worst_contact = min(p3_paths, key=lambda c: p3_paths[c]["delivered_at_400mA_min_V"])
    p3_delivered_path_ohm = p3_paths[worst_contact]["total_series_ohm"]
    p3_delivered_min = p3_paths[worst_contact]["delivered_at_400mA_min_V"]

    p3v3 = dict(
        top=P3V3_FB["top"], bottom=P3V3_FB["bottom"],
        top_ohms=p3_top, bottom_ohms=p3_bot,
        top_tolerance=p3_top_tol, bottom_tolerance=p3_bot_tol,
        top_mpn=divider_mpns[P3V3_FB["top"]],
        bottom_mpn=divider_mpns[P3V3_FB["bottom"]],
        top_tcr_ppm_per_C=top_tcr,
        bottom_tcr_ppm_per_C=bot_tcr,
        divider_parts_are_a_known_precision_selection=divider_parts_are_known,
        temperature_range_C=[P3V3_FB["temp_min_C"], P3V3_FB["temp_max_C"]],
        raw_pwm_V=[round(p3_raw_lo, 6), round(p3_raw_nom, 6), round(p3_raw_hi, 6)],
        pwm_heavy_min_V=round(p3_pwm_heavy_lo, 6),
        pwm_heavy_max_V=round(p3_pwm_heavy_hi, 6),
        power_save_high_if_enabled_V=round(p3_ps_hi, 6),
        power_save_is_disabled=True,
        worst_case_rail_max_V=round(p3_pwm_heavy_hi, 6),
        reinforcement_file=str(ACC_3V3_REINFORCEMENT.relative_to(ROOT)),
        reinforcement_identity_ok=reinforcement_identity_ok,
        each_reinforcement_max_ohm=reinf_r,
        measurement_plane=("the potential between the ACC_3V3_SW contact and "
                           "the GND contacts AT THE J5 MATING INTERFACE; the "
                           "accessory's own plug, cable and connector are "
                           "outside the guarantee"),
        delivery_paths=p3_paths,
        worst_contact=worst_contact,
        delivered_path_bound_ohm=round(p3_delivered_path_ohm, 6),
        delivered_at_400mA_min_V=round(p3_delivered_min, 6),
        published_connector_min_V=PUBLISHED_CONNECTOR_MIN_V,
        tightest_internal_consumer_max_V=ILI9488["vci_abs_max_V"],
        tightest_internal_consumer="the fitted ILI9488 panel: VCI and IOVCC "
                                   "absolute maximum -0.3..+3.3 V",
        delivered_min_ok=p3_delivered_min >= PUBLISHED_CONNECTOR_MIN_V,
        internal_high_ok=p3_pwm_heavy_hi <= ILI9488["vci_abs_max_V"],
        method="TPS63020 VFB_PWM 495/500/505 mV; exact R39/R40 value tolerance "
               "plus selected-part TCR over -40..85 C; TI 0.5% line and 0.5% "
               "load regulation applied pessimistically in BOTH directions.  "
               "D-788: PS/SYNC is tied to EN, so the +5% VFB_PS power-save "
               "excursion cannot occur and the worst-case maximum is the PWM "
               "corner; it is reported anyway so a board that re-grounds "
               "PS/SYNC is visibly refused.  The delivered minimum prices the "
               "COMPLETE loop -- U20's RON taken at the rail's own heavy-load "
               "minimum rather than at the datasheet's 3.3 V condition, the "
               "pour-delivered source side, the bounded hot board copper, the "
               "manual lead at its acceptance, the mated signal contact, the "
               "four parallel mated GND contacts, the ground-return copper and "
               "a process allowance -- and qualifies EACH duplicated contact "
               "alone.")

    # The PACK model must no longer run on a typed 3.3 V. Full normal load is
    # PWM, so use the HIGH PWM/regulation corner: it costs the most battery
    # current and is the conservative direction.
    V_3V3 = p3_pwm_heavy_hi

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
    # ---- D-787 / R6-A01: main +3V3 delivery is an explicit contract -------
    d["p3v3_setpoint"] = p3v3
    d["p3v3_divider_parts_have_a_published_temperature_coefficient"] = (
        divider_parts_are_known)
    d["p3v3_reinforcement_is_exact_and_bounded"] = reinforcement_identity_ok
    d["p3v3_delivers_the_published_connector_minimum"] = p3v3["delivered_min_ok"]
    d["p3v3_stays_below_the_tightest_internal_consumer_maximum"] = p3v3[
        "internal_high_ok"]

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

    # D-788 / R7-N03.  THIS MODEL STILL RAN AT THE 68 mOhm ROW R7-D787-02
    # RETIRED.  The delivery proof above already takes U20's RON at the rail's
    # own heavy-load minimum by interpolating between two GUARANTEED rows, and
    # leaving the raw 3.3 V row in a SECOND place inside the same contract is
    # how a corrected number comes back.  The pack model uses the same bound.
    # It moves the battery current by microamps -- 6.5 mOhm at 0.4 A is 1 mW of
    # 7.2 W -- and that is exactly why it must be the same number: a term this
    # small can only be a consistency question, never a result.
    ron_a3 = p3_ron
    ron_a5 = ACC_SWITCH_RON_OHM["ACC_5V"]

    def _model(ohms):
        """The series terms, hot, from one set of path resistances."""
        return dict(
            bat=ohms["bat_protected_p"] * k_cu + r_batfet,
            trunk=ohms["sys_to_u21"] * k_cu,
            a3=ohms["acc_3v3_sw"] * k_cu + ron_a3,
            a5=ohms["acc_5v_sw"] * k_cu + ron_a5)

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
        accessory_switch_ron_ohm=dict(ACC_3V3=round(ron_a3, 6),
                                      ACC_5V=round(ron_a5, 6)),
        accessory_switch_ron_basis=(
            "ACC_3V3 is the TPS22950-Q1 bound INTERPOLATED between the 1.8 V "
            "(116 mOhm) and 3.3 V (68 mOhm) guaranteed -40..+125 C rows at "
            "this rail's own heavy-load minimum -- the same number the "
            "delivery proof uses, not the raw 3.3 V row R7-D787-02 retired.  "
            "ACC_5V's switch runs from ACC_5V_RAW, which never falls below "
            "the 3.3 V condition, so its 54 mOhm row applies directly"),
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

    # D-781 replaces the 2 A JST-PH board connector with exact factory-precrimped
    # 26 AWG board pigtails and a 26 AWG/26 AWG Micro-Lock Plus W/W harness. The
    # connection is now rated 2.6 A at the controlling AWG26 side, so NORMAL
    # operation no longer needs D-777's RF/NFC/IR reserve.  All product-visible
    # internal loads may coexist with both published accessory-rail budgets.
    reserve_rows, reserve_A, reserve_named_ok = [], 0.0, True
    reserved_internal = I_INTERNAL

    def _required_internal(m, vcell, i3, i5, cap):
        lo, hi = 0.0, 4.0
        for _ in range(300):
            mid = 0.5 * (lo + hi)
            if battery_current(m, vcell, i3, i5, iint=mid)[0] <= cap: lo = mid
            else: hi = mid
        return lo

    PERMITTED = (
        ("no_accessory", 0.0, 0.0, I_INTERNAL, "single"),
        ("acc3v3_published", i3_pub, 0.0, I_INTERNAL, "single"),
        ("acc5v_published", 0.0, i5_pub, I_INTERNAL, "single"),
        ("both_published_full_internal", i3_pub, i5_pub, I_INTERNAL, "dual"))
    conn_cases, conn_within = {}, (rating is not None)
    for basis, ohms in (("live", live_ohms), ("path_bound", bound_ohms)):
        m = _model(ohms); rows = {}
        for name, i3, i5, iint, which in PERMITTED:
            floor = dual_floor if which == "dual" else single_floor
            cur = battery_current(m, floor, i3, i5, iint=iint)[0]
            inside = bool(rating is not None and cur <= rating + 1e-9)
            conn_within = conn_within and inside
            rows[name] = dict(vcell_V=round(floor,4), internal_3v3_A=round(iint,4),
                acc3v3_A=i3, acc5v_A=i5, connection_A=round(cur,4),
                margin_to_the_published_rating_pct=(round((rating-cur)/rating*100,2)
                    if rating else None), inside_the_published_rating=inside)
        full=rows["both_published_full_internal"]
        rows["legacy_2A_jst_ph_would_pass_full_internal"] = dict(
            connection_A=full["connection_A"], legacy_rating_A=2.0,
            would_pass=full["connection_A"] <= 2.0,
            note="negative reference: the D-777 JST-PH connection is not adequate here")
        req=_required_internal(m,dual_floor,i3_pub,i5_pub,rating) if rating else float("nan")
        conn_cases[basis]=dict(cases=rows,
            required_internal_3v3_ceiling_A=(round(req,6) if req==req else None))
    req_ceiling=min(v["required_internal_3v3_ceiling_A"] for v in conn_cases.values()) if rating else None
    reserve_load_bearing=False
    residual=dict(basis="live",vcell_V=round(dual_floor,4),
                  acc3v3_held_at_A=i3_pub,internal_3v3_A=I_INTERNAL)
    if rating is not None:
        def _i5_reaching(cap):
            lo,hi=0.0,2.0
            for _ in range(200):
                mid=0.5*(lo+hi)
                if battery_current(m_live,dual_floor,i3_pub,mid,iint=I_INTERNAL)[0] <= cap: lo=mid
                else: hi=mid
            return lo
        at_rating,at_ocp=_i5_reaching(rating),_i5_reaching(IBAT_OCP_MIN)
        residual.update(acc5v_draw_that_reaches_the_rating_A=round(at_rating,4),
            acc5v_draw_that_reaches_ibat_ocp_min_A=round(at_ocp,4),
            overdraw_to_reach_the_rating_pct=round((at_rating/i5_pub-1)*100,1),
            overdraw_to_reach_ibat_ocp_min_pct=round((at_ocp/i5_pub-1)*100,1),
            note="normal published concurrency is inside the 2.6 A harness rating; accessory overdraw beyond the published budgets remains a first-article abuse case, not an allowed operating state")

    trip = recoverable_trip_facts()
    d["recoverable_trip_behaviour"] = trip
    d["the_recoverable_trips_retry_limit_was_read"] = trip[
        "the_retry_limit_was_read"]

    d["battery_connection"] = dict(
        conn, rating_A=rating,
        first_protection_min_A=round(IBAT_OCP_MIN, 4),
        connector_rating_minus_first_protection_min_A=(
            round(rating - IBAT_OCP_MIN, 4) if rating is not None else None),
        overload_note=("the 2.6 A harness rating is slightly above the charger's "
                       "minimum OCP threshold but below higher OCP corners; normal "
                       "published load concurrency is independently held below both. "
                       "Accessory overdraw is an abuse/fault case and remains a "
                       "first-article thermal/protection validation item"),
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
        method="D-781 reads the 2.6 A AWG26 rating from the local transcription "
               "of Molex 5055700003-PS A6 and cross-checks it against the frozen "
               "BATTERY_HARNESS.json identities, gauges and polarity.  Currents "
               "use the same D-775 sag model at both live and declared path bounds.")
    d["battery_connection_rating_was_read_not_asserted"] = bool(
        rating is not None and conn["rating_was_read_from_primary_transcription"]
        and conn["rated_current_in_harness_matches_primary"])
    d["battery_harness_exact_parts_are_frozen"] = conn["harness_identity_exact"]
    d["battery_board_precrimps_are_primary_source_proven"] = conn["board_precrimps_are_primary_source_proven"]
    d["battery_harness_polarity_is_frozen"] = conn["polarity_exact"]
    d["battery_lead_insulation_od_acceptance_is_frozen"] = bool(
        conn.get("battery_lead_insulation_od_must_be_measured")
        and conn.get("battery_terminal_od_range_is_frozen")
        and conn.get("finished_j4_hole_fit_check_is_required"))
    d["both_harness_wire_gauges_are_supported"] = bool(
        conn["pack_lead_is_inside_the_applicable_wire_range"]
        and conn["board_lead_is_inside_the_applicable_wire_range"])
    d["every_permitted_state_is_inside_the_connections_published_rating"] = conn_within
    d["full_feature_concurrency_needs_no_internal_reserve"] = not reserve_load_bearing
    d["legacy_2A_jst_is_proven_inadequate"] = all(
        not v["cases"]["legacy_2A_jst_ph_would_pass_full_internal"]["would_pass"]
        for v in conn_cases.values())

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
          and d["p3v3_divider_parts_have_a_published_temperature_coefficient"]
          and d["p3v3_reinforcement_is_exact_and_bounded"]
          and d["p3v3_delivers_the_published_connector_minimum"]
          and d["p3v3_stays_below_the_tightest_internal_consumer_maximum"]
          and d["boost_setpoint_is_clear_of_its_own_ovp"]
          and d["published_normal_load_respects_vcell_policy"]
          and d["firmware_floors_meet_the_derived_requirement"]
          and d["every_live_normal_path_is_inside_its_bound"]
          # ---- D-781: rated harness, no D-777 product reserve required ----
          and d["battery_connection_rating_was_read_not_asserted"]
          and d["battery_harness_exact_parts_are_frozen"]
          and d["battery_board_precrimps_are_primary_source_proven"]
          and d["battery_harness_polarity_is_frozen"]
          and d["battery_lead_insulation_od_acceptance_is_frozen"]
          and d["both_harness_wire_gauges_are_supported"]
          and d["every_permitted_state_is_inside_the_connections_published_rating"]
          and d["full_feature_concurrency_needs_no_internal_reserve"]
          and d["legacy_2A_jst_is_proven_inadequate"]
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
    first_five_text = (FIRST_FIVE_ASSEMBLY.read_text(encoding="utf-8", errors="replace")
                       if FIRST_FIVE_ASSEMBLY.exists() else "")
    q11_temp_acceptance_explicit = all(token in first_five_text for token in (
        "Q11-TEMP-01", "0 °C", "25 °C", "40 °C",
        "open-LED latch", "failure blocks that unit"))
    periph_text = (DEMO_BACKLIGHT.read_text(encoding="utf-8", errors="replace")
                   if DEMO_BACKLIGHT.exists() else "")

    # D-787 / Round-6. F5 owns the hardware disconnect and the existence of
    # the shared executable timing seam. Executed startup ordering is proved by
    # firmware_hw_map_contract H6/test_timing_policy.cpp, whose dead-code,
    # reordered, shortened and early-PWM mutations all compile and are caught.
    timing_policy = ROOT / "Firmware/src/hw/aqroot_demo_timing_policy.h"
    timing_text = (timing_policy.read_text(encoding="utf-8", errors="replace")
                   if timing_policy.exists() else "")
    def _code(text):
        """`//` comments removed.  A commented-out call is not a call."""
        return re.sub(r"//[^\n]*", "", text or "")

    def _backlight_prime_ok(periph, seam):
        # THE ORDER, IN THE FILE THAT NOW OWNS IT.  D-785 read these markers out
        # of aqroot_demo_peripherals.h; D-787 moved the ordering into the shared
        # seam; D-788 moved the PRODUCTION ramp that calls it into
        # `aqroot_demo_backlight.h` so a host test can execute it.  This reads
        # the seam and separately requires the production ramp to CALL it.  The
        # behavioural half -- that the order executes, in the SHIPPED callbacks,
        # and that fourteen evasions are caught -- is firmware_hw_map_contract
        # H6 (`test_timing_policy.cpp` and `test_production_timing.cpp`), and
        # that the shipped firmware runs the seam at all is H8.
        periph, seam = _code(periph), _code(seam)
        if "runBacklightRampPolicy(" not in periph:
            return False
        if "kBacklightStartupPrimeUs = 3000" not in seam:
            return False
        markers = ("write_duty(255);",
                   "wait_us(kBacklightStartupPrimeUs);",
                   "for (int duty = 5; duty <= 255; duty += 5)")
        pos = [seam.find(token) for token in markers]
        return all(x >= 0 for x in pos) and pos[0] < pos[1] < pos[2]

    backlight_startup_prime_explicit = _backlight_prime_ok(periph_text,
                                                           timing_text)
    # Load-bearing controls, each restoring one real evasion: the pre-D-784 tick
    # delay, a shortened prime, the hold moved before the full-duty command, and
    # a production ramp that no longer calls the seam at all.
    backlight_prime_control_refuses_tick_delay = not _backlight_prime_ok(
        periph_text,
        timing_text.replace("wait_us(kBacklightStartupPrimeUs);",
                            "wait_ms(2);", 1))
    backlight_prime_control_refuses_short_hold = not _backlight_prime_ok(
        periph_text,
        timing_text.replace("kBacklightStartupPrimeUs = 3000",
                            "kBacklightStartupPrimeUs = 1500", 1))
    backlight_prime_control_refuses_reordered_hold = not _backlight_prime_ok(
        periph_text,
        timing_text.replace(
            "  write_duty(255);\n  wait_us(kBacklightStartupPrimeUs);",
            "  wait_us(kBacklightStartupPrimeUs);\n  write_duty(255);", 1))
    backlight_prime_control_refuses_an_uncalled_seam = not _backlight_prime_ok(
        periph_text.replace("  runBacklightRampPolicy(",
                            "  // runBacklightRampPolicy(", 1),
        timing_text)
    tps61169_primary_archived = (TPS61169_PRIMARY.exists() and
        hashlib.sha256(TPS61169_PRIMARY.read_bytes()).hexdigest() ==
        "7d0b8ace2459a9fd22fe7145086cbad4ccb3bb43219247459313fcba75230151")

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
        # ---- D-780.  A too-small hold must leave the selected part's
        # PUBLISHED conduction region before U17 is guaranteed shut down.
        _fet_control("f5k_refuses_a_10nF_hold_that_leaves_the_published_region_too_early",
                     lambda v: v.__setitem__("C85", "10nF X7R")),
        # A part with no published low-gate conduction point is refused.
        _fet_control("f5l_refuses_a_fet_with_no_published_conduction_point",
                     lambda v: v.__setitem__(BL_FET, "AO3400A_NO_RDS_ON")),
        # THE LOAD-BEARING CONTROL: exactly the D-779 AO3422 board.  Its
        # guaranteed 2.5 V RDS(on) point sits ABOVE the 2.396 V held VGS, so a
        # typical-gfs bridge cannot make it pass this release gate.
        _fet_control("f5m_refuses_the_ao3422_d779_board_below_its_guaranteed_gate_point",
                     lambda v: v.__setitem__(BL_FET, "AO3422"))))

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
    # D-781: the rated battery harness removes the old internal-feature reserve.
    policy_ceiling = None

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

    # D-787 / R6-A01.  THE TRAVELER NAMES PADS; THE BOARD DECIDES WHAT THEY
    # ARE ON.  F6 already checks that the reinforcement record names TP12.1,
    # J5.3 and J5.22 and bounds each finished path.  Nothing checked that those
    # three contacts are actually on `/ACC_3V3_SW`, which is the whole premise
    # -- a lead soldered downstream of U20 only keeps the limiter in series if
    # its source pad really is U20's output net.
    reinf_doc = (json.loads(ACC_3V3_REINFORCEMENT.read_text(encoding="utf-8"))
                 if ACC_3V3_REINFORCEMENT.exists() else {})
    reinf_contacts = [reinf_doc.get("source", {}).get("reference")] + [
        x.get("reference") for x in reinf_doc.get("destinations", [])]
    reinf_contact_nets = {c: nets_by_contact.get(c) for c in reinf_contacts if c}
    reinforcement_contacts_are_on_the_rail = bool(reinf_contact_nets) and all(
        net == "/ACC_3V3_SW" for net in reinf_contact_nets.values())

    divider_mpns = schematic_mpns((P3V3_FB["top"], P3V3_FB["bottom"]))
    env_ok, env = judge_accessory_envelope(
        values, single_floor=policy_single, dual_floor=policy_dual,
        live_ohms=live_ohms, mpns=divider_mpns)
    env["normal_operation"]["firmware_policy_file"] = str(
        POWER_POLICY.relative_to(ROOT)) if POWER_POLICY.exists() else None
    env["normal_operation"]["measurement_contacts"] = measurement_nets
    env["normal_operation"]["measurement_point_is_bat_protected_p"] = measurement_ok
    env["normal_operation"]["firmware_policy_parsed"] = (
        math.isfinite(policy_single) and math.isfinite(policy_dual))
    env["battery_connection"]["internal_feature_reserve"] = "not required by D-781 rated harness"
    env["normal_operation"]["live_paths_measured_off_the_board"] = True
    env_ok = (env_ok and measurement_ok
              and math.isfinite(policy_single) and math.isfinite(policy_dual))

    # ---- D-787 / R6-E07: THE AMPACITY AUDIT'S DESIGN CURRENTS ARE A COPY --
    # `audit_rail_ampacity.RAILS` states a design current per rail with a cited
    # basis.  Every one of those numbers is derived from THIS contract's
    # envelope, and Round-6 found three of them stale -- BAT/SYS still at the
    # 1.50/1.00 A .kicad_dru class currents and P3V3 at 1.849 A -- because
    # nothing made the copy follow the original.  Now it does: each named rail's
    # design current must be at least the envelope number it comes from, so a
    # limiter setting, a divider value or a budget line that moves the envelope
    # FAILS here until the audit is rerun at the new figure.
    worst_battery_A = max(
        c["connection_A"] for base in env["battery_connection"]["bases"].values()
        for k, c in base["cases"].items() if "connection_A" in c
        and not k.startswith("legacy_"))
    ampacity_expected = {
        "ACC_3V3_SW": env["rails_A"]["ACC_3V3"]["ilim_max"],
        "ACC_5V_SW": env["rails_A"]["ACC_5V"]["ilim_max"],
        "P3V3_MAIN": env["converter_capability_A"]["u12_worst_case_load_A"],
        "BAT_PROTECTED_P": worst_battery_A,
        "BQ25185_SYS": worst_battery_A,
    }
    ampacity_rows, ampacity_stale = [], []
    for name, need in sorted(ampacity_expected.items()):
        have = rails_by_name.get(name, {}).get("amps")
        ok = have is not None and have + 1e-9 >= need
        ampacity_rows.append(dict(rail=name, audit_design_A=have,
                                  envelope_requires_A=round(need, 4), ok=ok))
        if not ok:
            ampacity_stale.append(name)
    env["rail_ampacity_design_currents"] = ampacity_rows
    env["rail_ampacity_design_currents_cover_the_envelope"] = not ampacity_stale
    env_ok = env_ok and not ampacity_stale

    # ---- D-788 / R7-D787-01: the fitted panel's own limits, on the live rail
    # and the live nets.  This is the clause that refuses D-787's board.
    display_sha = (hashlib.sha256(DISPLAY_PRIMARY.read_bytes()).hexdigest()
                   if DISPLAY_PRIMARY.exists() else None)
    disp_ok, disp = judge_display_supply(
        env["p3v3_setpoint"]["pwm_heavy_min_V"],
        env["p3v3_setpoint"]["worst_case_rail_max_V"],
        nets_by_contact, primary_sha=display_sha)
    # ...and the PS/SYNC tie the whole high-side bound rests on, read off the
    # board rather than believed.  A board that re-grounds it is refused.
    ps_ref, ps_pin = P3V3_FB["power_save_disabled_by"]
    ps_net = nets_by_contact.get("%s.%s" % (ps_ref, ps_pin))
    disp["power_save_pin"] = "%s.%s" % (ps_ref, ps_pin)
    disp["power_save_pin_net"] = ps_net
    disp["power_save_pin_is_not_grounded"] = (ps_net not in (None, "GND"))
    disp["power_save_pin_matches_the_declared_tie"] = (
        ps_net == P3V3_FB["power_save_disabled_net"])
    disp["rail_max_if_power_save_were_enabled_V"] = \
        env["p3v3_setpoint"]["power_save_high_if_enabled_V"]
    disp["power_save_would_break_the_absolute_maximum"] = (
        env["p3v3_setpoint"]["power_save_high_if_enabled_V"]
        > ILI9488["vci_abs_max_V"])
    disp_ok = bool(disp_ok and disp["power_save_pin_is_not_grounded"]
                   and disp["power_save_pin_matches_the_declared_tie"])
    disp["ok"] = disp_ok
    # Three destructive controls, each restoring one exact D-787 state.
    disp["controls_refused"] = {
        "f6y_refuses_the_d787_power_save_high_side": not judge_display_supply(
            env["p3v3_setpoint"]["pwm_heavy_min_V"], 3.542487,
            nets_by_contact, primary_sha=display_sha)[0],
        "f6z_refuses_the_d787_nominal_setpoint": not judge_display_supply(
            env["p3v3_setpoint"]["pwm_heavy_min_V"], 3.308989,
            nets_by_contact, primary_sha=display_sha)[0],
        "f6aa_refuses_a_display_rail_split_from_the_mcu_rail":
            not judge_display_supply(
                env["p3v3_setpoint"]["pwm_heavy_min_V"],
                env["p3v3_setpoint"]["worst_case_rail_max_V"],
                dict(nets_by_contact, **{"J1.40": "+3V3D", "J1.41": "+3V3D",
                                         "J1.42": "+3V3D"}),
                primary_sha=display_sha)[0],
        "f6ab_refuses_a_missing_or_altered_primary_datasheet":
            not judge_display_supply(
                env["p3v3_setpoint"]["pwm_heavy_min_V"],
                env["p3v3_setpoint"]["worst_case_rail_max_V"],
                nets_by_contact, primary_sha="0" * 64)[0],
    }
    env["display_supply"] = disp
    env_ok = env_ok and disp_ok and all(disp["controls_refused"].values())

    # ---- D-788 / R7-N02: ripple, the MCU's own floor, and the centring ----
    # The clause above is DC.  This one charges the computable AC term to both
    # ends, adds the ESP32-S3-WROOM-1 supply minimum that nothing in this file
    # had ever checked, and PROVES the fitted divider is the best-centred value
    # a purchasable E192 0.1 % part can give -- because the load-transient term
    # is not provable from published data and the headroom that absorbs it must
    # therefore be as large as the design allows.
    fa_text = (FIRST_FIVE_ASSEMBLY.read_text(encoding="utf-8", errors="replace")
               if FIRST_FIVE_ASSEMBLY.exists() else "")
    ac_ok, ac = judge_p3v3_ac_and_centring(
        env["p3v3_setpoint"]["pwm_heavy_min_V"],
        env["p3v3_setpoint"]["worst_case_rail_max_V"],
        env["p3v3_setpoint"]["top_ohms"], env["p3v3_setpoint"]["bottom_ohms"],
        I_INTERNAL, fa_text)
    # Four controls.  Each is a state this clause has to refuse, and the first
    # two are the exact values the D-788 drafts and D-787 carried.
    ac["controls_refused"] = {
        # D-787's power-save corner: over the absolute maximum before ripple.
        "f6ac_refuses_the_d787_power_save_corner": not
        judge_p3v3_ac_and_centring(
            env["p3v3_setpoint"]["pwm_heavy_min_V"], 3.542487,
            env["p3v3_setpoint"]["top_ohms"],
            env["p3v3_setpoint"]["bottom_ohms"], I_INTERNAL, fa_text)[1][
                "high_corner_under_absolute_maximum"],
        # The 187 kOhm first D-788 draft: legal on DC, NOT the best centring.
        "f6ad_refuses_the_187k_draft_as_the_best_centring": not
        judge_p3v3_ac_and_centring(
            env["p3v3_setpoint"]["pwm_heavy_min_V"],
            env["p3v3_setpoint"]["worst_case_rail_max_V"],
            env["p3v3_setpoint"]["top_ohms"], 187000.0, I_INTERNAL, fa_text)[1][
                "fitted_is_the_best_purchasable_centring"],
        # A rail that clears the panel and the connector but not the MODULE.
        "f6ae_refuses_a_rail_under_the_esp32s3_floor": not
        judge_p3v3_ac_and_centring(
            2.990, env["p3v3_setpoint"]["worst_case_rail_max_V"],
            env["p3v3_setpoint"]["top_ohms"],
            env["p3v3_setpoint"]["bottom_ohms"], I_INTERNAL, fa_text)[1][
                "low_corner_over_the_mcu_minimum"],
        # And the deferral is only acceptable while the measurement is NAMED.
        "f6af_refuses_an_unnamed_first_article_transient_acceptance": not
        judge_p3v3_ac_and_centring(
            env["p3v3_setpoint"]["pwm_heavy_min_V"],
            env["p3v3_setpoint"]["worst_case_rail_max_V"],
            env["p3v3_setpoint"]["top_ohms"],
            env["p3v3_setpoint"]["bottom_ohms"], I_INTERNAL, "")[0],
    }
    ac["ok"] = bool(ac_ok and all(ac["controls_refused"].values()))
    env["p3v3_ac_envelope_and_centring"] = ac
    env_ok = env_ok and ac["ok"]

    # ---- D-788 / R7-N04: the PUBLISHED contract must be the DERIVED one ----
    spec_text = (DEVICE_SPEC.read_text(encoding="utf-8", errors="replace")
                 if DEVICE_SPEC.exists() else "")
    published_tokens = {
        "connector_minimum_V": "%.2f V" % PUBLISHED_CONNECTOR_MIN_V,
        "unloaded_minimum_V": "%.6f V" % env["p3v3_setpoint"]["pwm_heavy_min_V"],
        "worst_case_maximum_V": "%.6f V" % env["p3v3_setpoint"][
            "worst_case_rail_max_V"],
        "delivered_at_the_published_budget_V": "%.6f V" % env[
            "p3v3_setpoint"]["delivered_at_400mA_min_V"],
        "acc_3v3_budget": "400 mA",
        "acc_5v_budget": "300 mA",
    }
    missing = sorted(k for k, t in published_tokens.items()
                     if t not in spec_text)
    env["published_contract_matches_device_spec"] = dict(
        document=str(DEVICE_SPEC.relative_to(ROOT)),
        required=published_tokens, missing=missing,
        ok=not missing and bool(spec_text),
        method="the product-facing document must print the SAME figures this "
               "contract derives; a published tolerance that only lives in a "
               "gate is not published, and one that only lives in a document "
               "is not proven")
    env_ok = env_ok and env["published_contract_matches_device_spec"]["ok"]

    env["p3v3_setpoint"]["reinforcement_contact_nets"] = reinf_contact_nets
    env["p3v3_reinforcement_contacts_are_on_the_rail"] = (
        reinforcement_contacts_are_on_the_rail)
    env_ok = env_ok and reinforcement_contacts_are_on_the_rail

    # D-787.  The module defaults must equal the firmware constants, or the
    # callers that use the defaults judge a different board from the one the
    # firmware runs.
    env["normal_operation"]["module_default_single_rail_floor_V"] = \
        NORMAL_SINGLE_VBAT_FLOOR
    env["normal_operation"]["module_default_dual_rail_floor_V"] = \
        NORMAL_DUAL_VBAT_FLOOR
    defaults_match = (NORMAL_SINGLE_VBAT_FLOOR == policy_single
                      and NORMAL_DUAL_VBAT_FLOOR == policy_dual)
    env["module_default_floors_match_the_firmware_policy"] = defaults_match
    env_ok = env_ok and defaults_match

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
        # f6w WAS "refuses the first D-775 draft's asserted 3.75 V", and D-788
        # RE-AIMED IT TWICE -- which is itself the finding.  Capping the main
        # rail at the display's 3.3 V absolute maximum LOWERED the rail, which
        # lowered the pack current the published budgets cost, which lowered
        # the DERIVED dual-rail requirement: 3.8094 V (D-787) -> 3.7142 V (the
        # first D-788 draft) -> 3.6948 V (R7-N01's centred divider).  Each time,
        # the hand-written control value stopped being a destructive value and
        # BECAME the gridded requirement, so the control silently went vacuous
        # while still reading PASS.
        #
        # A CONTROL AIMED BY HAND AT A DERIVED NUMBER IS A BUG WITH A SCHEDULE.
        # Both are now aimed ONE GRID STEP BELOW whatever the derivation
        # currently produces, so they cannot go vacuous again.  THE FIRMWARE
        # FLOORS DO NOT MOVE: 3.85 V and 3.50 V are retained and are now MORE
        # conservative than the derivation demands, which is the safe direction
        # and the one that needs no firmware change.
        _env_policy_control(
            "f6w_refuses_a_dual_rail_floor_below_the_derived_requirement",
            dual_floor=round(env["normal_operation"][
                "required_dual_rail_floor_gridded_V"] - FLOOR_GRID_V, 4)),
        # and the single-rail floor is a clause too, not just the dual one
        _env_policy_control(
            "f6x_refuses_a_single_rail_floor_under_its_own_requirement",
            single_floor=round(env["normal_operation"][
                "required_single_rail_floor_gridded_V"] - FLOOR_GRID_V, 4)),
        # ---- the LIVE inputs.  A path that grows past its declared ceiling
        # must fail rather than be absorbed into the margin.
        _env_ohm_control(
            "f6y_refuses_bat_protected_p_copper_past_its_ceiling",
            bat_protected_p=0.060),
        _env_ohm_control(
            "f6z_refuses_a_sys_to_u21_trunk_past_its_ceiling",
            sys_to_u21=0.260),
    )))

    # ---- D-781 battery-harness controls.  These replace D-777's reserve
    # controls because the rated connection now carries FULL normal concurrency.
    _missing_evidence = dict(BATTERY_CONNECTION,
        evidence="hardware/demo/kicad/aqroot-demo/vendor/MOLEX/not-present.txt")
    _missing_harness = dict(BATTERY_CONNECTION,
        harness="docs/full-beta-v2/assembly/not-present-battery-harness.json")
    _wrong_harness = dict(BATTERY_CONNECTION,
        harness="docs/full-beta-v2/assembly/SELECTED_BATTERY.json")
    _wrong_evidence = dict(BATTERY_CONNECTION,
        evidence="hardware/demo/kicad/aqroot-demo/vendor/JST/jst-ph-connector-ePH.txt")
    env_controls.update(dict((
        ("f6aa_proves_the_legacy_2A_jst_fails_full_feature_concurrency",
         env["legacy_2A_jst_is_proven_inadequate"]),
        _env_policy_control(
            "f6ab_refuses_a_missing_micro_lock_primary_transcription",
            connection=_missing_evidence),
        _env_policy_control(
            "f6ac_refuses_a_missing_frozen_battery_harness",
            connection=_missing_harness),
        _env_policy_control(
            "f6ad_refuses_a_file_that_is_not_the_frozen_harness_schema",
            connection=_wrong_harness),
        _env_policy_control(
            "f6ae_refuses_a_rating_from_the_wrong_connector_family",
            connection=_wrong_evidence),
        ("f6af_full_path_bound_concurrency_has_positive_rating_margin",
         min(v["cases"]["both_published_full_internal"][
             "margin_to_the_published_rating_pct"]
             for v in env["battery_connection"]["bases"].values()) > 0),
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
            # NOT A JLCPCB CATALOGUE LINE.  The panel is bought direct from
            # EastRising and the antenna from an RF distributor, so neither has
            # an exact-MPN JLCPCB record and the D-787 stock clause does not
            # apply to them.  Stated rather than silently skipped.
            stocked=False,
            lib_id_contains="ER-TFT035IPS-6",
            retired=("CH280QV10", "ILI9341", "2.8in", "2.8-inch", "240x320"),
            why="D-074 locked the 3.5in 320x480 ILI9488 panel; D-112 replaced "
                "the 2.8in CH280QV10-CT pin table because it is DEAD ON "
                "ARRIVAL here -- LEDA/LEDK reversed, WRX/D-CX swapped"),
        "U8": dict(
            locked="TI.92.2113",
            stocked=False,            # see J1: not a JLCPCB catalogue line
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
        # ---- D-787 ADDS THE TPS63020 DIVIDER, WHOSE IDENTITY BECAME A PROOF
        # TERM.  Until D-787 these were two ordinary 1 % thick-film parts and
        # nothing depended on which ones they were.  F6 now DERIVES the main
        # +3V3 envelope from their tolerance and their selected-part TCR, so a
        # substitution back onto a 1 % / 100 ppm line would silently break the
        # Community Port's published 3.135 V minimum while every other clause
        # stayed green.  Same `only_fields` treatment as the other passives.
        "R39": dict(
            locked="ARG03BTC1004",
            lib_id_contains=None,
            only_fields=("Value", "MPN", "LCSC"),
            retired=("0603WAF1004T5E", "C22935", "1M 1%"),
            why="D-787 moved the TPS63020 feedback divider's high side to a "
                "0.1 % / 25 ppm thin-film part because F6 now derives the rail "
                "from it; the D-614 1 % / 100 ppm 0603WAF1004T5E cannot hold "
                "the 3.135 V connector minimum at the published 400 mA"),
        "R40": dict(
            locked="RT0603BRD07189KL",
            lib_id_contains=None,
            only_fields=("Value", "MPN", "LCSC"),
            retired=("0603WAF1803T5E", "C22827", "180K 1%",
                     "RN73H1JTTD1763B10", "C4086101", "176K 0.1%",
                     "ARG03BTC1783", "C2441185", "178K 0.1%",
                     "RT0603BRD07187KL", "C861172", "187K 0.1%"),
            why="D-788 moved the TPS63020 feedback divider's low side because "
                "the rail now has a CEILING it did not have: the fitted "
                "ILI9488 panel's VCI and IOVCC absolute maximum is 3.3 V "
                "(Table 41 of the archived primary datasheet), and D-787's "
                "178 kOhm put the nominal 9 mV and the power-save corner "
                "242 mV above it.  R7-N01 then moved it again, 187 -> "
                "189 kOhm, to CENTRE the band: a DC-only bound is not the "
                "whole high side, ripple and load-transient overshoot ride on "
                "top of it, and 187 kOhm left 47.97 mV under a DAMAGE limit "
                "against 96.99 mV over the MCU's RECOVERABLE floor.  The "
                "D-614 180 kOhm 1 % part cannot hold any envelope; the first "
                "D-787 draft's 176 kOhm KOA RN73H1JTTD1763B10 and 186 kOhm "
                "are both UNSTOCKED at 0.1 % and fail this project's own "
                "rule_open_sourcing stock floor"),
        "R97": dict(
            locked="0603WAF1781T5E",
            lib_id_contains=None,
            only_fields=("Value", "MPN", "LCSC"),
            retired=("0603WAF2701T5E", "C13167", "2.7k"),
            why="D-771 moved the ACC_3V3 limiter setting 2.7 -> 1.78 kOhm so "
                "the rail GUARANTEES the 400 mA TOTAL D-098 publishes for it; "
                "2.7 kOhm guaranteed only 0.277 A"),
        "R101": dict(
            locked="0603WAF2431T5E",
            lib_id_contains=None,
            only_fields=("Value", "MPN", "LCSC"),
            retired=("0603WAF2701T5E", "C13167", "2.7k",
                     "0603WAF2321T5E", "C22905", "2.32k",
                     "0603WAF2371T5E", "C25964", "2.37k"),
            why="D-771 moved the ACC_5V limiter setting 2.7 -> 2.32 kOhm so the "
                "rail GUARANTEES the 300 mA TOTAL D-098 publishes for it; "
                "D-773 moved it to 2.37 kOhm after the 5 V setpoint was derived, "
                "and D-787 moves it to 2.43 kOhm so the corrected high-corner "
                "3V3 rail cannot push a user-reachable 5 V limiter state above "
                "BQ25185 IBAT_OCP minimum while still guaranteeing >300 mA."),
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
        # D-787.  A LOCKED PART MUST STILL BE BUYABLE.  D-096 asks for a live
        # record before an MPN is written down; it does not ask again once it
        # IS written down, and the first D-787 draft locked an `R40` whose live
        # JLCPCB record reads stock 0.  A part number confirmed against a
        # record showing zero stock satisfies the letter of that rule and not
        # its purpose, so every locked part carries the archived exact-MPN
        # record and must clear the same first-five liquidity floor
        # `rule_open_sourcing` refuses a CANDIDATE on: five boards x 10.
        d["locked_part_is_a_jlcpcb_catalogue_line"] = spec.get("stocked", True)
        if spec.get("stocked", True):
            live = live_stock_for(spec["locked"])
            need = 5 * 10
            d["live_record"] = live
            d["locked_part_is_stocked"] = bool(
                live and isinstance(live.get("stock"), int)
                and live["stock"] >= need)
            d["locked_part_stock_floor"] = need
            clauses.append("locked_part_is_stocked")
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
        # ---- D-787's two.  THE LOAD-BEARING ONE IS `f7k`: it is exactly the
        # part the first D-787 draft locked -- a real 176 kOhm 0.1 % KOA line
        # whose live JLCPCB record reads stock 0 -- and every other clause in
        # this registry passes on it.  `f7l` is the same defect with no record
        # archived at all, which must also refuse rather than skip.
        "f7k_refuses_a_locked_part_whose_live_record_reads_zero_stock":
            not judge_identity(
                "R40", dict(IDENTITY_GUARD["R40"],
                            locked="RN73H1JTTD1763B10", retired=()),
                _symbol_fields("R40"),
                '"R40","176K 0.1%","Resistor_SMD:R_0603_1608Metric",'
                '"KOA Speer Elec","RN73H1JTTD1763B10","C4086101","Resistor","1",""')[0],
        "f7l_refuses_a_locked_part_with_no_archived_live_record_at_all":
            not judge_identity(
                "R40", dict(IDENTITY_GUARD["R40"],
                            locked="NO-SUCH-PART-9999", retired=()),
                _symbol_fields("R40"),
                '"R40","178K 0.1%","x","x","NO-SUCH-PART-9999","x","x","1",""')[0],
    })

    # ---- D-781: MANUAL J4 METADATA MUST MATCH THE FROZEN HARNESS --------
    # J4 is intentionally absent from the purchased BOM/CPL, so FAB12c proves
    # only that it remains a manual land.  Bind the schematic work instruction
    # to the harness record as well; this catches a plausible wrong-but-consistent
    # prose edit such as the 24-AWG typo found during independent closeout.
    j4 = _symbol_fields("J4")
    j4_inst = j4.get("instance", "") or ""
    def _j4_prop(name, block=j4_inst):
        m = re.search(r'\(property "' + re.escape(name) + r'" "((?:[^"\\]|\\.)*)"', block)
        return m.group(1) if m else None
    j4_harness = json.loads((rl.ROOT / BATTERY_CONNECTION["harness"]).read_text(encoding="utf-8"))
    j4_board_awg = j4_harness.get("board_side", {}).get("wire_AWG")
    j4_pack_awg = j4_harness.get("battery_side", {}).get("factory_lead_AWG")
    j4_rating_awg = j4_harness.get("controlling_rating", {}).get("wire_AWG")
    j4_desc = _j4_prop("Description") or ""
    j4_note = _j4_prop("Note2") or ""
    j4_semantic = dict(
        value=_j4_prop("Value"), mpn=_j4_prop("MPN"), manufacturer=_j4_prop("Manufacturer"),
        datasheet=_j4_prop("Datasheet"), description=j4_desc,
        board_wire_awg=j4_board_awg, battery_wire_awg=j4_pack_awg, rating_wire_awg=j4_rating_awg,
        value_matches=(_j4_prop("Value") == "BATTERY PIGTAIL %sAWG" % j4_board_awg),
        mpn_matches=(_j4_prop("MPN") == "D-781-BAT-PIGTAIL"),
        manufacturer_matches=(_j4_prop("Manufacturer") == "AQROOT manual harness"),
        datasheet_matches=(_j4_prop("Datasheet") == BATTERY_CONNECTION["harness"]),
        description_matches=("Board-side %s AWG red/black wires" % j4_board_awg) in j4_desc,
        note_matches=("2175012101" in j4_note and "2175011101" in j4_note
                      and "%s AWG" % j4_board_awg in j4_note
                      and "5055700201" in j4_note and "2137192021" in j4_note
                      and "2137201000" in j4_note),
        gauges_agree=(j4_board_awg == j4_pack_awg == j4_rating_awg == 26))
    j4_semantic["ok"] = all(v for k, v in j4_semantic.items() if k.endswith("_matches") or k == "gauges_agree")
    bad_j4_inst = j4_inst.replace("Board-side 26 AWG red/black wires",
                                   "Board-side 24 AWG red/black wires", 1)
    bad_desc_m = re.search(r'\(property "Description" "((?:[^"\\]|\\.)*)"', bad_j4_inst)
    bad_desc = bad_desc_m.group(1) if bad_desc_m else ""
    j4_controls = {
        "f9a_refuses_a_24awg_schematic_description_on_the_26awg_harness":
            not (("Board-side %s AWG red/black wires" % j4_board_awg) in bad_desc),
        "f9b_refuses_a_harness_gauge_mismatch": not (j4_board_awg == 24 == j4_pack_awg == j4_rating_awg),
    }

    # ---- F8: the derating rule, applied to the parts this board FITS -----
    import screen_bom_sourcing as sbs                              # noqa: E402
    # D-788 / R7-D787-07: the hierarchical map F8 now looks every DC bound up
    # in, checked against the board and against NET_MAX_DC before it is used.
    dc_map_ok, dc_map = judge_canonical_dc_map(board, sbs.NET_MAX_DC)
    # D-788 / R7-D787-16.  ONE CEILING, TWO FILES.  The sourcing screener
    # proposes parts against `screen_bom_sourcing.LED_BOOST_OVP_MAX_V` and the
    # board publishes its own figure in `.kicad_dru` section 5; Round-7 found
    # them 1 V apart (38 vs 39), which lets the screener propose a part the
    # board's own rules refuse.  They must be the same number.
    dru_ceiling = led_boost_fault_ceiling_V(dru_text)
    sourcing_ceiling = getattr(sbs, "LED_BOOST_OVP_MAX_V", None)
    def _ceiling_agrees(published, constant, board_max, boost, k, a):
        return (published is not None and constant == published
                and board_max == published and boost == published
                and k == published and a == published)

    ceiling_agrees = _ceiling_agrees(
        dru_ceiling, sourcing_ceiling, sbs.BOARD_MAX_DC,
        sbs.NET_MAX_DC["LED_BOOST"][1], sbs.NET_MAX_DC["LED_K"][1],
        sbs.NET_MAX_DC["LED_A"][1])
    cap_ok, caps = judge_capacitor_derating(board, sch_dnp, sbs.NET_MAX_DC)
    caps["canonical_dc_map"] = dc_map
    caps["led_boost_fault_ceiling_V"] = dict(
        published_by_the_rules_file=dru_ceiling,
        screen_bom_sourcing_constant=sourcing_ceiling,
        board_max_dc=sbs.BOARD_MAX_DC,
        led_boost_row=sbs.NET_MAX_DC["LED_BOOST"][1],
        led_k_row=sbs.NET_MAX_DC["LED_K"][1],
        led_a_row=sbs.NET_MAX_DC["LED_A"][1],
        every_backlight_ceiling_agrees=ceiling_agrees)
    cap_ok = cap_ok and dc_map_ok and ceiling_agrees

    def _cap_control(name, **kw):
        # D-788: a control may mutate the canonical map itself, and the map's
        # own three clauses are part of the verdict a control has to break.
        cmap = kw.get("canonical_dc")
        map_ok, _ = judge_canonical_dc_map(board, kw.get("net_max_dc")
                                           or sbs.NET_MAX_DC, canonical=cmap)
        ok, _ = judge_capacitor_derating(board, sch_dnp, **kw)
        return name, not (ok and map_ok)

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
                                  rating_V=6.3))),
        # Round-4 Astra R4-05: changing ONLY the BOM MPN while leaving its
        # LCSC code/value behind must not inherit the old record's rating.
        _cap_control("f8i_refuses_an_mpn_only_identity_downgrade",
                     net_max_dc=sbs.NET_MAX_DC,
                     purchased=dict(
                         purchased_capacitor_ratings(),
                         C44=dict(purchased_capacitor_ratings()["C44"],
                                  mpn="CL21B105KAFNNNE"))),
        _cap_control("f8k_refuses_a_manufacturer_identity_mismatch",
                     net_max_dc=sbs.NET_MAX_DC,
                     purchased=dict(
                         purchased_capacitor_ratings(),
                         C44=dict(purchased_capacitor_ratings()["C44"],
                                  record_manufacturer="Vishay"))),
        _cap_control("f8l_refuses_a_package_identity_mismatch",
                     net_max_dc=sbs.NET_MAX_DC,
                     purchased=dict(
                         purchased_capacitor_ratings(),
                         C44=dict(purchased_capacitor_ratings()["C44"],
                                  record_package="0201"))),
        # A named RF proof is valid only on the exact terminals for which its
        # differential bound was derived; moving the same reference does not
        # carry the old proof with it.
        _cap_control("f8m_refuses_a_non_dc_proof_bound_to_the_wrong_nets",
                     net_max_dc=sbs.NET_MAX_DC,
                     non_dc_proofs=dict(
                         CAP_NON_DC_PROOFS,
                         C71=dict(CAP_NON_DC_PROOFS["C71"],
                                  nets=("NFC_EMCA", "UNRELATED_NET")))),
        # A fitted RF/unknown node is accepted only through the explicit
        # non-DC proof registry.  Remove those proofs and the frozen board must
        # itself fail instead of merely reporting the omission.
        _cap_control("f8j_refuses_unbounded_non_dc_capacitor_nodes",
                     net_max_dc=sbs.NET_MAX_DC,
                     non_dc_proofs={}),
        # ---- D-788 / R7-D787-07.  THE EXACT ROUND-7 COUNTEREXAMPLES.  Each
        # moves a fitted capacitor onto a net whose LEAF still matches a
        # NET_MAX_DC row but whose hierarchy this repository has established
        # nothing about.  Under D-787 both inherited the real rail's bound and
        # F8 passed; both must be refused now.
        _cap_control("f8n_refuses_c20_on_an_alien_hierarchy_usb_vbus_raw",
                     net_max_dc=sbs.NET_MAX_DC,
                     net_rewrite={"/01_POWER_TREE/USB_VBUS_RAW":
                                  "/ALIEN/USB_VBUS_RAW"}),
        _cap_control("f8o_refuses_c33_on_an_alien_hierarchy_bq25185_sys",
                     net_max_dc=sbs.NET_MAX_DC,
                     net_rewrite={"/01_POWER_TREE/BQ25185_SYS":
                                  "/ALIEN/BQ25185_SYS"}),
        # A canonical entry for a net that is NOT on this board is a stale
        # declaration and must refuse rather than sit there.
        _cap_control("f8p_refuses_a_canonical_dc_entry_for_an_absent_net",
                     net_max_dc=sbs.NET_MAX_DC,
                     canonical_dc=dict(CANONICAL_DC_NETS,
                                       **{"/NO_SUCH/USB_VBUS_RAW":
                                          "USB_VBUS_RAW"})),
        # ...and an entry that maps a net onto an UNRELATED row is refused
        # unless PROVEN_DC_ALIASES carries a written reason.
        # D-788 / R7-D787-16: the exact stale 38 V ceiling, put back, in each
        # of the four places that carried it.  The clause must refuse all four.
        ("f8r_refuses_a_sourcing_constant_below_the_published_ceiling",
         not _ceiling_agrees(dru_ceiling, 38.0, sbs.BOARD_MAX_DC,
                             sbs.NET_MAX_DC["LED_BOOST"][1],
                             sbs.NET_MAX_DC["LED_K"][1],
                             sbs.NET_MAX_DC["LED_A"][1])),
        ("f8s_refuses_a_stale_38V_board_wide_ceiling",
         not _ceiling_agrees(dru_ceiling, sourcing_ceiling, 38.0,
                             sbs.NET_MAX_DC["LED_BOOST"][1],
                             sbs.NET_MAX_DC["LED_K"][1],
                             sbs.NET_MAX_DC["LED_A"][1])),
        ("f8t_refuses_a_stale_38V_backlight_anode_or_cathode_row",
         not _ceiling_agrees(dru_ceiling, sourcing_ceiling, sbs.BOARD_MAX_DC,
                             sbs.NET_MAX_DC["LED_BOOST"][1], 38.0,
                             sbs.NET_MAX_DC["LED_A"][1])),
        ("f8u_refuses_a_rules_file_that_publishes_no_ceiling_at_all",
         not _ceiling_agrees(led_boost_fault_ceiling_V("no ceiling here"),
                             sourcing_ceiling, sbs.BOARD_MAX_DC,
                             sbs.NET_MAX_DC["LED_BOOST"][1],
                             sbs.NET_MAX_DC["LED_K"][1],
                             sbs.NET_MAX_DC["LED_A"][1])),
        _cap_control("f8q_refuses_a_silent_cross_hierarchy_alias",
                     net_max_dc=sbs.NET_MAX_DC,
                     canonical_dc=dict(CANONICAL_DC_NETS,
                                       **{"/04_SPI_B_RADIOS_NFC/NFC_ANT_A":
                                          "LED_BOOST"}))))

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
                and fet_ok and all(fet_controls.values())
                and q11_temp_acceptance_explicit
                and backlight_startup_prime_explicit
                and backlight_prime_control_refuses_tick_delay
                and backlight_prime_control_refuses_short_hold
                and backlight_prime_control_refuses_reordered_hold
                and backlight_prime_control_refuses_an_uncalled_seam
                and tps61169_primary_archived),
            method="TI SNVSA40B 6.3.5 makes CTRL an ANALOG dimming input: the "
                   "converter keeps switching through every PWM low phase, so "
                   "Q11's gate may not share it.  The D-752 hold network is "
                   "what keeps the ordering, and four live controls put each "
                   "way of losing it back.  D-766: AND THE SILICON.  Q11's "
                   "drain is the panel cathode, which under open-LED "
                   "protection follows the anode to the ceiling this board's "
                   "OWN .kicad_dru publishes for LED_BOOST -- parsed from that "
                   "file, not restated here -- so the fitted FET's PUBLISHED "
                   "VDS rating must cover it.  "
                   "D-788 / R7-D787-14 REWRITES THE CONDUCTION ARGUMENT AROUND "
                   "THE ROW THAT ACTUALLY CARRIES IT.  The controlling clause "
                   "is the CHARACTERIZED CONDUCTION POINT, not a threshold: "
                   "Vishay 75975 Rev B publishes RDS(on) 0.245 ohm MAX at "
                   "VGS = 1.5 V, ID = 2.0 A, and this circuit holds "
                   "VGS = 2.396 V and asks for 0.109 A -- 0.896 V inside a "
                   "region the vendor guarantees, at 18x less current than the "
                   "row is taken at.  The ordering clause is measured against "
                   "the SAME row: the RC envelope may not decay below "
                   "VGS = 1.5 V until after the TPS61169's 2.5 ms guaranteed "
                   "shutdown.  VGS(th) is retained only as a NECESSARY "
                   "subordinate check and is no longer the argument -- D-779 "
                   "showed a threshold row is an OFF-state boundary taken at "
                   "250 uA and cannot license 109 mA.  THE SCOPE IS STATED: "
                   "the 1.5 V row stands in the TC = 25 C table and Vishay "
                   "publishes no low-gate row at any other temperature, so "
                   "0/25/40 C backlight on/off remains a FIRST-ARTICLE "
                   "measurement (Q11-TEMP-01) and is not inferred here.  "
                   "Nine more live controls, one of which is the 30 V AO3400A "
                   "D-752 left fitted and one the D-779 AO3422 whose only "
                   "published low-gate row sits ABOVE the held gate",
            controls_refused=bl_controls,
            fet_controls_refused=fet_controls,
            temperature_acceptance_marker="Q11-TEMP-01",
            temperature_acceptance_explicit=q11_temp_acceptance_explicit,
            startup_prime_us=3000,
            startup_prime_explicit=backlight_startup_prime_explicit,
            startup_prime_control_refuses_tick_delay=
                backlight_prime_control_refuses_tick_delay,
            startup_prime_control_refuses_short_hold=
                backlight_prime_control_refuses_short_hold,
            startup_prime_control_refuses_reordered_hold=
                backlight_prime_control_refuses_reordered_hold,
            startup_prime_control_refuses_an_uncalled_seam=
                backlight_prime_control_refuses_an_uncalled_seam,
            startup_prime_seam="Firmware/src/hw/aqroot_demo_timing_policy.h",
            startup_prime_behavioural_proof=
                "firmware_hw_map_contract H6 (test_timing_policy.cpp) and H8",
            tps61169_primary_archived=tps61169_primary_archived,
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
        "F9_manual_battery_harness_metadata_matches_the_frozen_build": dict(
            ok=j4_semantic["ok"] and all(j4_controls.values()),
            method="D-781 makes J4 a manual battery-pigtail land rather than a purchased "
                   "PCB connector. The schematic Value/MPN/manufacturer/datasheet, wire "
                   "gauge and exact Micro-Lock work instruction must agree with the frozen "
                   "BATTERY_HARNESS.json; live controls reintroduce the 24-AWG typo and a "
                   "wire-gauge mismatch so absence from BOM/CPL cannot hide an assembly error",
            controls_refused=j4_controls, semantic=j4_semantic),
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
