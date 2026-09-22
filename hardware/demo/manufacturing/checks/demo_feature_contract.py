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
import aqroot_power_model as apm                              # noqa: E402

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
        vds_V=60.0, vgs_th_max_V=1.00, vgs_th_min_V=0.46,
        vgs_th_test_A=250e-6,
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
    "AO3422":  dict(vds_V=55.0, vgs_th_max_V=2.00, vgs_th_min_V=0.60,
                    vgs_th_test_A=250e-6,
                    rds_on_vgs_V=2.5, rds_on_id_A=1.5, rds_on_max_ohm=0.200,
                    source="AOS AO3422 rev 2.1 2024-03: VDS 55 V, VGS(th) "
                           "max 2.0 V at 250 uA, RDS(on) 0.200 ohm MAX at "
                           "VGS=2.5 V ID=1.5 A"),
    "AO3400A": dict(vds_V=30.0, vgs_th_max_V=1.45, vgs_th_min_V=0.65,
                    source="AOS AO3400A rev 3.1 2023-07 as read by D-159: "
                           "VDS 30 V, VGS(th) 0.65/1.05/1.45 V"),
    "AO3400A_NO_RDS_ON": dict(vds_V=55.0, vgs_th_max_V=2.00,
                              vgs_th_min_V=0.60,
                              source="control only -- a FET whose datasheet "
                                     "this contract has no RDS(on) test point for"),
    "2N7002":  dict(vds_V=60.0, vgs_th_max_V=2.50, vgs_th_min_V=0.80,
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

# --------------------------------------------------------------------------
# D-789 / D788-11 -- THE HELD GATE WAS A CONSTANT FROM A RAIL THAT NO LONGER
# EXISTS.
#
# `BL_HELD_GATE_V = 2.60` was D-752's number, derived when this board's +3V3
# rail was a nominal 3.3 V.  D-788 moved the rail down to keep the fitted
# ILI9488 panel inside its own absolute maximum, and this constant did not
# move with it: F5 went on ordering Q11 against a gate voltage the board
# cannot produce.  Round-8 is right that a fixed number here is not a proof.
#
# THE GATE IS NOW SOLVED FROM THE CIRCUIT.  GPIO46 drives `/DISP_BL_CTL`
# through R109 (0 ohm); D14's anode sits on that net and its cathode on
# Q11's gate, where R132 discharges C85.  At DC, with the PWM high,
#
#     V_gate  =  VOH(GPIO46)  -  VF(D14, at the gate's own leakage current)
#
# and every term of that is a published MINIMUM or MAXIMUM:
#
#   VOH       Espressif ESP32-S3-WROOM-1 DC Characteristics, VOH MIN = 0.8 x
#             VDD.  It is RATIOMETRIC, so it is evaluated at the +3V3 rail's
#             own HEAVY-LOAD MINIMUM -- which is the whole point of this
#             finding -- and not at 3.3 V.  The table is headed 25 C; the
#             0/25/40 C endpoints stay a first-article waveform measurement.
#   VF        the lowest published forward-voltage MAXIMUM of the fitted
#             diode.  The held gate draws about 9 uA through R132, far BELOW
#             any published row, and VF increases monotonically with IF -- so
#             the lowest published row is a GUARANTEED bound with no
#             interpolation.  A declared 2 mV/K allowance carries it from the
#             25 C table to the 0 C endpoint.
#   leakage   D14's reverse leakage and Q11's IGSS both discharge C85 in
#             parallel with R132, so the ORDERING below is solved with a
#             constant-current leak beside the exponential rather than with
#             R132 alone.
#
# AND THE ANSWER MOVED THE BOARD.  With the D-788 rail and the D-787 D14
# (Jiangsu Changjing 1N4148WS, lowest published row VF <= 715 mV at 1 mA), the
# held gate bounds to 1.690526 V and VGS to 1.486526 V -- 13.5 mV BELOW the
# fitted SQ2364EES's only published low-gate conduction row, VGS = 1.5 V.  D14
# is therefore a SCHOTTKY in the same SOD-323 land -- DIODES INCORPORATED
# BAT54WS-7-F, VF <= 240 mV at 0.1 mA -- which is the SAME MPN and LCSC code
# D10/D11/D12 already carry.
#
# D-790 / D789-A08 CORRECTS THE MANUFACTURER IN THIS PARAGRAPH AND IN THE
# SOURCE RECORD'S TOP-LEVEL `vendor` FIELD.  Both said "JSCJ ... from the same
# manufacturer", which is the maker of the part that LEFT and never of the one
# that arrived; the two documents live under `vendor/JSCJ/` and
# `vendor/DIODES/` respectively.  The clause below refuses the superseded part
# by arithmetic rather than by name.
#
# AND THE NUMBER MOVED AGAIN AT D-790 / D789-A08: Q11's SOURCE is the
# TPS61169's own feedback node, so the bound is that reference's published
# MAXIMUM of 220 mV and not its 204 mV typical -- see `BL_SOURCE_V`.  The held
# VGS is 1.945526 V, not the 1.9615 V D-789 published.
BL_GPIO_VOH_FRACTION_OF_VDD = 0.8
BL_GPIO_VOH_SOURCE = (
    "Espressif ESP32-S3-WROOM-1 datasheet, Table 6-3 DC Characteristics, "
    "VOH MIN = 0.8 x VDD1.  The table is headed (3.3 V, 25 C) and the row is "
    "written ratiometrically, so it is evaluated here at the rail's own "
    "heavy-load minimum; 0/25/40 C remains a first-article measurement.")
# `vf_max_V` is the LOWEST published forward-voltage maximum and `vf_row_A`
# the current it is published at.  `ir_max_A` / `ir_row_V` are the reverse
# leakage row.  See vendor/DIODES/d14-hold-diode-source.json, which archives
# BOTH documents -- the part that arrived and the part that left.
BL_HOLD_DIODE = "D14"
# It is keyed by the SCHEMATIC VALUE, and the MPN is checked separately by F7.
HOLD_DIODE_PUBLISHED = {
    "BAT54WS": dict(
        vf_max_V=0.240, vf_row_A=100e-6, ir_max_A=2.0e-6, ir_row_V=25.0,
        vrrm_V=30.0, kind="Schottky barrier",
        mpn="BAT54WS-7-F", lcsc="C124205",
        source="Diodes Incorporated BAT54WS-7-F DS30086, archived "
               "vendor/DIODES/diodes-bat54ws-7-f-ds30086.pdf sha256 "
               "a910241f...226f26d6: VFM 240 mV MAX at IF = 0.1 mA, 320 mV at "
               "1 mA, IRM 2.0 uA MAX at VR = 25 V, V(BR)R 30 V MIN at "
               "IR = 100 uA, TA = +25 C.  This is the SAME MPN and LCSC code "
               "D10/D11/D12 already carry, procurement-locked at D-211, so "
               "D14 joins an existing BOM line."),
    # RETAINED AS THE NEGATIVE CONTROL.  This is the D-787/D-788 board, and
    # the clause must refuse it on the arithmetic rather than on its name.
    "1N4148WS": dict(
        vf_max_V=0.715, vf_row_A=1.0e-3, ir_max_A=25e-9, ir_row_V=20.0,
        vrrm_V=75.0, kind="silicon switching",
        mpn="1N4148WS", lcsc="C2128",
        source="Jiangsu Changjing (JSCJ) 1N4148WS -- RETIRED at D-789; "
               "archived vendor/JSCJ/jscj-1n4148ws-sod323-"
               "2011-05.pdf sha256 59e951bd...9fcabf2e: VF1 715 mV MAX at "
               "IF = 1 mA -- the LOWEST published row -- IR 25 nA MAX at "
               "VR = 20 V, Ta = 25 C"),
}
# DECLARED: both tables are 25 C only and a junction's VF rises as it cools.
# 2 mV/K is the conventional silicon figure and is conservative for a
# Schottky; it is applied to BOTH so the comparison is like-for-like.
BL_DIODE_VF_TC_V_PER_K = 0.002
BL_COLD_ENDPOINT_C = 0.0
BL_DIODE_TABLE_REFERENCE_C = 25.0
# The source voltage R69 sits at while U17 regulates the string to the
# TPS61169's feedback point.  This is set by the CONVERTER's feedback
# reference and not by R69, so it does not move with the rail.
#
# D-790 / D789-A08.  IT IS THE MAXIMUM, NOT THE TYPICAL.  D-752 through D-789
# used 204 mV, which is SNVSA40B's TYPICAL VREF; the EC row is 188 / 204 /
# 220 mV.  `Q11`'s source IS this node, so a HIGHER feedback voltage makes
# `VGS` SMALLER -- the typical was being used as a limit in the one direction
# that flatters the answer, which is exactly what D-779 and D-780 refused
# elsewhere on this same transistor.  The bound is 220 mV.  It costs 16 mV of
# held `VGS` and the ordering still closes on the SQ2364EES's published
# `VGS = 1.5 V` conduction row.
BL_SOURCE_V = 0.220
BL_SOURCE_V_SOURCE = (
    "TI SNVSA40B Electrical Characteristics, VREF 'Voltage feedback "
    "regulation voltage', duty = 100 %, TA >= 25 C: 188 / 204 / 220 mV.  The "
    "MAXIMUM is the bound because Q11's source is this node and a higher "
    "feedback voltage reduces its VGS.")
# D-791 / D790-A13: `BL_STRING_CURRENT_A` used to be the hand-written 0.109
# here.  It is now DERIVED from `BACKLIGHT_BOOST` and is defined immediately
# after that table, because it depends on it.  See the comment there.
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


# A rail value only used when `judge_backlight_fet` is called as a pure
# function by its own controls; `main()` always passes the DERIVED rail.
BL_RAIL_MIN_FALLBACK_V = 3.069408
# DECLARED: a Schottky's reverse leakage roughly doubles every 10 K, and the
# published row is 25 C.  3x carries it to the 40 C top of the prototype
# envelope with margin.  Applied to the published IR maximum, which is itself
# quoted at a reverse voltage far above the ~2 V this node ever sees -- and IR
# increases with VR, so the row is an upper bound here.
BL_DIODE_IR_HOT_FACTOR = 3.0
# R132 is a 1 % part; the TRUE-OFF floor is worst at its HIGH corner and the
# ordering is worst at its low one.
BL_R132_TOLERANCE = 0.01


def _hold_decay_ms(tau_s, r_ohm, v_from, v_to, leak_A):
    """Time for C85 to decay from `v_from` to `v_to`, WITH a constant leak.

    D-789 / D788-11.  D-788 solved a pure exponential, which is the answer for
    R132 alone.  D14's reverse leakage and Q11's IGSS both discharge C85 in
    parallel with R132 and neither is proportional to the gate voltage, so
    they are carried as a CONSTANT CURRENT -- the conservative treatment,
    since a constant leak at its maximum removes charge faster than a resistor
    of the same instantaneous value would.  With `i = v/R + I`,

        v(t) = (v0 + I R) exp(-t/RC) - I R
        t    = RC ln( (v0 + I R) / (v1 + I R) )

    and with `I = 0` it degenerates to the exponential D-788 solved.
    """
    if v_from <= v_to:
        return 0.0
    if not r_ohm or leak_A <= 0:
        return tau_s * 1e3 * math.log(v_from / v_to)
    ir = leak_A * r_ohm
    return tau_s * 1e3 * math.log((v_from + ir) / (v_to + ir))


def held_gate_V(rail_min_V, diode_part, igss_max_A=0.0):
    """D-789 / D788-11: the gate voltage this board actually holds, DERIVED.

    Returns (gate_V, detail).  `gate_V` is None when the fitted diode is one
    this contract has no published forward-voltage row for -- it REFUSES
    rather than defaulting, the same way F6 refuses an unknown divider MPN.
    """
    d = HOLD_DIODE_PUBLISHED.get(diode_part)
    voh = BL_GPIO_VOH_FRACTION_OF_VDD * rail_min_V
    cold = BL_DIODE_VF_TC_V_PER_K * (BL_DIODE_TABLE_REFERENCE_C
                                     - BL_COLD_ENDPOINT_C)
    detail = dict(
        diode=BL_HOLD_DIODE, diode_part=diode_part,
        diode_is_a_part_with_published_ratings=d is not None,
        rail_heavy_load_min_V=round(rail_min_V, 6),
        gpio_voh_fraction_of_vdd=BL_GPIO_VOH_FRACTION_OF_VDD,
        gpio_voh_min_V=round(voh, 6),
        gpio_voh_source=BL_GPIO_VOH_SOURCE,
        diode_vf_table_reference_C=BL_DIODE_TABLE_REFERENCE_C,
        diode_vf_cold_endpoint_C=BL_COLD_ENDPOINT_C,
        diode_vf_tc_V_per_K=BL_DIODE_VF_TC_V_PER_K,
        diode_vf_cold_allowance_V=round(cold, 6),
        igss_max_A=igss_max_A)
    if not d:
        detail["why"] = ("no published forward-voltage row for this part; the "
                         "clause refuses rather than defaulting")
        return None, detail
    vf_cold = d["vf_max_V"] + cold
    gate = voh - vf_cold
    detail.update(
        diode_published=dict(d),
        diode_vf_max_at_its_lowest_published_row_V=d["vf_max_V"],
        diode_vf_row_A=d["vf_row_A"],
        diode_vf_bound_at_the_cold_endpoint_V=round(vf_cold, 6),
        held_gate_V=round(gate, 6),
        method="VOH(MIN) at the rail's own heavy-load minimum, less the "
               "diode's LOWEST published forward-voltage maximum (a "
               "guaranteed bound at every current below that row, because VF "
               "increases monotonically with IF) and a declared cold-endpoint "
               "allowance.  Nothing is interpolated and nothing is typical.")
    return gate, detail


def p3v3_pwm_envelope(values, mpns=None, fb=None):
    """D-789 / D788-11: the +3V3 envelope, as ONE function two clauses share.

    F6 has derived this since D-787.  F5 now needs the SAME rail -- Q11's held
    gate is `0.8 x rail_min - VF(D14)` and D-788 moved the rail without moving
    F5's constant -- and a second copy of the arithmetic is how the two would
    drift apart.  Returns (envelope, error): `error` is not None when the
    divider or its MPNs are unreadable, and the caller carries the verdict.
    """
    fb = P3V3_FB if fb is None else fb
    top = _ohms(values.get(fb["top"]))
    bot = _ohms(values.get(fb["bottom"]))
    if not top or not bot:
        return None, ("3V3 divider unreadable: %s=%r %s=%r"
                      % (fb["top"], values.get(fb["top"]),
                         fb["bottom"], values.get(fb["bottom"])))
    top_tol, bot_tol = _tol(values.get(fb["top"])), _tol(values.get(fb["bottom"]))
    temp_delta = max(abs(fb["temp_min_C"] - fb["reference_temp_C"]),
                     abs(fb["temp_max_C"] - fb["reference_temp_C"]))
    divider_mpns = dict(fb["released_mpns"])
    divider_mpns.update({k: v for k, v in (mpns or {}).items()
                         if k in divider_mpns})
    top_tcr = fb["tcr_ppm_per_C_by_mpn"].get(divider_mpns[fb["top"]])
    bot_tcr = fb["tcr_ppm_per_C_by_mpn"].get(divider_mpns[fb["bottom"]])
    known = top_tcr is not None and bot_tcr is not None
    top_err = top_tol + (top_tcr if top_tcr is not None else 200.0) \
        * 1e-6 * temp_delta
    bot_err = bot_tol + (bot_tcr if bot_tcr is not None else 200.0) \
        * 1e-6 * temp_delta
    ratio_lo = top * (1 - top_err) / (bot * (1 + bot_err))
    ratio_hi = top * (1 + top_err) / (bot * (1 - bot_err))
    vfb = fb["vfb_V"]
    raw_lo = vfb[0] * (1 + ratio_lo)
    raw_nom = vfb[1] * (1 + top / bot)
    raw_hi = vfb[2] * (1 + ratio_hi)
    return dict(
        top_ohms=top, bottom_ohms=bot,
        top_tolerance=top_tol, bottom_tolerance=bot_tol,
        top_mpn=divider_mpns[fb["top"]], bottom_mpn=divider_mpns[fb["bottom"]],
        top_tcr_ppm_per_C=top_tcr, bottom_tcr_ppm_per_C=bot_tcr,
        divider_parts_are_known=known,
        raw_lo=raw_lo, raw_nom=raw_nom, raw_hi=raw_hi,
        # Heavy-load minimum pays both published line and load regulation
        # maxima; full-load pack current is costed at the opposite corner.
        heavy_lo=raw_lo * (1 - fb["max_line_reg"]) * (1 - fb["max_load_reg"]),
        heavy_hi=raw_hi * (1 + fb["max_line_reg"]) * (1 + fb["max_load_reg"]),
        # In power-save mode TI permits +5 % relative to VFB_PWM.  D-788 ties
        # PS/SYNC to EN so it cannot occur; it is reported so a board that
        # re-grounds PS/SYNC is visibly refused.
        ps_hi=raw_hi * (1 + fb["ps_high_relative_to_pwm"])
              * (1 + fb["max_line_reg"])), None

def judge_backlight_fet(values, dru_text, rail_min_V=None):
    """Pure over {ref: value} and the .kicad_dru text; returns (ok, detail)."""
    part = (values.get(BL_FET) or "").strip()
    pub = FET_PUBLISHED.get(part)
    ceiling = led_boost_fault_ceiling_V(dru_text)
    r132 = _ohms(values.get("R132"))
    c85 = _farads(values.get("C85"))
    tau_s = r132 * c85 if (r132 and c85) else None
    tau_worst_s = (tau_s * BL_TAU_WORST_RATIO * BL_CAP_BIAS_RETENTION
                   if tau_s else None)
    # D-789 / D788-11: DERIVED, from the rail this board actually has.
    diode_part = (values.get(BL_HOLD_DIODE) or "").strip()
    gate_V, gate_detail = held_gate_V(
        rail_min_V if rail_min_V is not None else BL_RAIL_MIN_FALLBACK_V,
        diode_part, igss_max_A=(pub or {}).get("igss_max_A", 0.0))
    # A refusal must not crash the report: run the arithmetic at the derived
    # value when there is one, and let the CLAUSE carry the verdict.
    held = gate_V if gate_V is not None else 0.0
    dpub = gate_detail.get("diode_published") or {}
    leak_A = (dpub.get("ir_max_A", 0.0) * BL_DIODE_IR_HOT_FACTOR
              + (pub or {}).get("igss_max_A", 0.0))
    vgs_held = held - BL_SOURCE_V
    f = dict(
        fet=BL_FET, fitted_part=part, published=dict(pub) if pub else None,
        dru_published_fault_ceiling_V=ceiling,
        held_gate_is_derived=gate_detail,
        held_gate_V=round(held, 6), source_V=BL_SOURCE_V,
        hold_diode_is_a_part_with_published_ratings=bool(
            gate_detail["diode_is_a_part_with_published_ratings"]),
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
        if tau_worst_s and held > pub["vgs_th_max_V"]:
            t_open_ms = _hold_decay_ms(tau_worst_s, r132, held,
                                       pub["vgs_th_max_V"], leak_A)
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
            if held > guaranteed_gate:
                t_leave_ms = _hold_decay_ms(tau_worst_s, r132, held,
                                            guaranteed_gate, leak_A)
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
            # D-789 / D788-11.  THE SENSITIVITY, PRINTED.  Below this rail the
            # held gate stops meeting the published conduction point, so how
            # much rail the design is spending is a number rather than a
            # hidden assumption -- the same shape as F6's
            # `batfet_breakeven_ohm`.
            vf_cold = gate_detail.get("diode_vf_bound_at_the_cold_endpoint_V")
            if vf_cold is not None and BL_GPIO_VOH_FRACTION_OF_VDD:
                f["held_gate_breakeven_rail_V"] = round(
                    (guaranteed_gate + vf_cold)
                    / BL_GPIO_VOH_FRACTION_OF_VDD, 6)
                f["held_gate_rail_margin_mV"] = round(
                    (gate_detail["rail_heavy_load_min_V"]
                     - f["held_gate_breakeven_rail_V"]) * 1000, 3)
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
    # D-789 / D788-11: the hold diode's own reverse rating, and the leak the
    # ordering was solved with, both reported.
    f["hold_diode"] = BL_HOLD_DIODE
    f["hold_diode_fitted_part"] = diode_part
    f["hold_diode_reverse_leak_used_A"] = leak_A
    f["hold_diode_ir_hot_factor"] = BL_DIODE_IR_HOT_FACTOR
    f["hold_diode_vrrm_V"] = dpub.get("vrrm_V")
    f["hold_diode_vrrm_covers_the_held_gate"] = bool(
        dpub.get("vrrm_V") and dpub["vrrm_V"] >= held)
    # ---- D-789 / D788-11: THE TRUE-OFF FLOOR, WITH THE RIGHT SIGN ---------
    #
    # D-752's schematic note rejected a Schottky here on the argument that its
    # reverse leakage would hold the gate up near threshold.  THE SIGN IS
    # WRONG, and changing this part is the moment to say so rather than to
    # inherit it.  KiCad's `Device:D` has pin 1 = K and pin 2 = A, and this
    # board wires D14 pin 1 to Q11's gate and pin 2 to `/DISP_BL_CTL`.  In the
    # true-off state the GPIO drives CTRL LOW and the gate sits above it, so
    # D14 is REVERSE biased and its leakage flows K -> A, OUT of the gate.  It
    # can only pull the gate DOWN.  The only current that can hold the gate up
    # is Q11's own IGSS, and it crosses R132 alone.
    #
    # So the clause computes the floor from IGSS and R132 at their worst
    # corners and requires it to stay under the FITTED FET's VGS(th) MINIMUM
    # -- the voltage below which the part is guaranteed off.  A Schottky makes
    # this number BETTER, not worse, and the report says by how much.
    r132_hi = r132 * (1 + BL_R132_TOLERANCE) if r132 else None
    igss = (pub or {}).get("igss_max_A")
    f["true_off"] = dict(
        why="in the true-off state CTRL is driven LOW and D14 is REVERSE "
            "biased with its CATHODE on the gate, so its leakage flows out of "
            "the gate and can only lower it.  The only current that can hold "
            "the gate up is the FET's own IGSS across R132.",
        d752_claim_superseded=(
            "D-752's schematic note added the hold diode's reverse leakage to "
            "IGSS as a gate-HOLDING current and concluded that a Schottky "
            "'would have put that floor near or above threshold'.  The diode "
            "is reverse-biased with its cathode on the gate, so that term has "
            "the wrong sign; it is subtractive."),
        igss_max_A=igss,
        r132_worst_ohm=round(r132_hi, 1) if r132_hi else None,
        r132_tolerance=BL_R132_TOLERANCE,
        floor_V=(round(igss * r132_hi, 6)
                 if (igss is not None and r132_hi) else None),
        vgs_th_min_V=(pub or {}).get("vgs_th_min_V"),
        diode_leak_is_subtractive_A=dpub.get("ir_max_A"),
        margin_x=None)
    to = f["true_off"]
    if to["floor_V"] is not None and to["vgs_th_min_V"]:
        to["margin_x"] = round(to["vgs_th_min_V"] / to["floor_V"], 2) \
            if to["floor_V"] > 0 else None
    f["true_off_floor_is_under_the_fets_guaranteed_off_threshold"] = bool(
        to["floor_V"] is not None and to["vgs_th_min_V"]
        and to["floor_V"] < to["vgs_th_min_V"])
    # ---- D-789 / `R8-N06`: THE HELD GATE MUST BE PRINTED WHERE IT IS READ ----
    # F6 has required DEVICE_SPEC to print the exact Community-Port figures it
    # derives since D-788 / R7-N04, and the reason given there was that "a
    # published tolerance that only lives in a gate is not published; one that
    # only lives in a document is not proven".  THE SAME RULE WAS NEVER APPLIED
    # TO THIS CLAUSE, and D-789 found the consequence: DEVICE_SPEC section 3
    # still printed `VGS = 2.396 V` and an "approximately 62 ms" envelope --
    # both 3.3 V-rail numbers, both stale the moment D-788 moved the rail, and
    # both invisible to every gate.  The exact same stale pair sat in
    # FIRST_FIVE_ASSEMBLY_PLAN section 7a.
    #
    # So the derived held gate, its margin over the fitted FET's published
    # conduction point, and the fitted hold diode's MPN must all appear
    # VERBATIM in the product-facing document.  The tokens are FORMATTED FROM
    # THE COMPUTED VALUES, so they move when the derivation moves and the
    # document has to move with them.
    spec_text = DEVICE_SPEC.read_text(encoding="utf-8", errors="replace") \
        if DEVICE_SPEC.is_file() else ""
    held_tokens = {}
    if f.get("held_gate_V") is not None and f.get("source_V") is not None:
        held_tokens["held_vgs"] = "%.6f V" % (f["held_gate_V"] - f["source_V"])
    if f.get("held_vgs_margin_above_published_conduction_point_V") is not None:
        held_tokens["margin_over_conduction_point"] = "%.1f mV" % (
            f["held_vgs_margin_above_published_conduction_point_V"] * 1000.0)
    if (f.get("held_gate_is_derived") or {}).get("diode_published", {}).get("mpn"):
        held_tokens["hold_diode_mpn"] = \
            f["held_gate_is_derived"]["diode_published"]["mpn"]
    missing_held = sorted(k for k, v in held_tokens.items()
                          if v not in spec_text)
    f["published_hold_is_printed_in_device_spec"] = dict(
        document=str(DEVICE_SPEC.relative_to(ROOT)),
        required=held_tokens, missing=missing_held,
        ok=bool(held_tokens) and not missing_held and bool(spec_text),
        method="R7-N04's rule, applied to the backlight hold: the derived held "
               "VGS, its margin over the fitted FET's published conduction "
               "point, and the fitted hold diode's MPN must be printed in the "
               "product-facing document, so a rail change cannot leave a stale "
               "gate voltage standing in DEVICE_SPEC the way D-789 found it")
    # A SCALAR, because the verdict tuple below tests truthiness and a
    # non-empty dict is always truthy -- which is how a clause gets stated and
    # never run.  This file has met that exact failure before.
    f["published_hold_is_printed_in_device_spec_ok"] = bool(
        f["published_hold_is_printed_in_device_spec"]["ok"])

    f["ok"] = all(bool(f.get(k)) for k in (
        "fet_is_a_part_with_published_ratings",
        "board_publishes_a_fault_ceiling",
        "published_hold_is_printed_in_device_spec_ok",
        "fet_vds_covers_the_published_fault_ceiling",
        "gate_hold_enhances_the_fitted_fet",
        "u17_shuts_down_before_q11_opens",
        "held_vgs_meets_published_conduction_point",
        "u17_shuts_down_before_gate_leaves_published_conduction_region",
        "hold_diode_is_a_part_with_published_ratings",
        "hold_diode_vrrm_covers_the_held_gate",
        "true_off_floor_is_under_the_fets_guaranteed_off_threshold",
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
        # D-789 / D788-11.  The hold diode is now a SCHOTTKY: at the D-788
        # rail the 1N4148WS's 715 mV lowest-published drop left Q11's held
        # VGS 13.5 mV under the SQ2364EES's only published conduction row.
        # This clause is NAME-based on purpose -- it is the population check,
        # not the electrical one; F5's `judge_backlight_fet` refuses the old
        # part by arithmetic, which is what makes this line safe to be a name.
        d14_is_the_published_hold_diode=(
            (values.get("D14") or "").strip() in HOLD_DIODE_PUBLISHED
            and HOLD_DIODE_PUBLISHED[(values.get("D14") or "").strip()]["kind"]
            == "Schottky barrier"),
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
# --------------------------------------------------------------------------
# D-790 / found while closing D789-A03/A11 -- `R9-N01`.  THE ILIM BAND WAS
# READ OFF A ROW THIS DESIGN DOES NOT SIT AT, AND IT IS THE SAME DEFECT CLASS
# ROUND-8 NAMED THREE TIMES.
#
# `ILIM_LO/HI = 0.68 / 1.32` above is a real datasheet ratio, but it belongs to
# SLVSGP6A's `RILIM = 19.2 kOhm` row -- a 50 mA setting.  The EC table publishes
# FOUR rows, and that one is the outlier:
#
#     RILIM      MIN     TYP     MAX        lo/typ    hi/typ
#     610 R     1.54     2.00    2.46        0.770     1.230
#     1.15 k    0.75     1.00    1.25        0.750     1.250
#     2.21 k    0.38     0.50    0.62        0.760     1.240
#     19.2 k    0.034    0.050   0.066       0.680     1.320
#
# `R97` is 1.78 kOhm, BRACKETED by the 1.15 k and 2.21 k rows, and it was being
# judged by a bound taken ten times away in resistance and twelve times away in
# current.  That is exactly what D-788 refused when `U20`'s `RON` was
# interpolated and what D-789 refused when the LTC4368 gate drive was read off
# the wrong row.
#
# THE RULE, AND WHY IT IS NOT AN INTERPOLATION.  The ratio is NOT monotone in
# `RILIM` -- the 1.15 k row is worse on the low side than the 2.21 k row -- so
# there is no "nearest row at or below" argument available and none is made.
# The bound is the WORSE OF THE TWO PUBLISHED ROWS THAT BRACKET THE SETTING,
# on each side independently.  A setting above the highest row or below the
# lowest falls back to the widest published ratio, and a setting that lands ON
# a row uses that row.  No curvature, no interpolation, no row that does not
# bracket the design.
#
# WHAT IT COSTS AND WHAT IT BUYS, BOTH STATED.  `ACC_3V3`'s guaranteed minimum
# rises 0.4279 -> 0.4719 A (6.97 % -> ~18 % over the published 400 mA) and its
# fault maximum falls 0.8486 -> 0.8035 A, which is what restores `U12`'s
# capability margin after D789-A11's corrected display budget.  `ACC_5V`'s
# `R101` is 2.43 kOhm, bracketed by the 2.21 k and 19.2 k rows, so its bound is
# UNCHANGED at 0.68 / 1.32 -- the rule does not flatter a part it does not fit.
# --------------------------------------------------------------------------
ILIM_ACCURACY_ROWS = {
    # RILIM ohms: (min_A, typ_A, max_A)
    610.0: (1.54, 2.00, 2.46),
    1150.0: (0.75, 1.00, 1.25),
    2210.0: (0.38, 0.50, 0.62),
    19200.0: (0.034, 0.050, 0.066),
}
ILIM_ACCURACY_SOURCE = (
    "TI SLVSGP6A Electrical Characteristics, Output Current Limit (ILIM), the "
    "-40..125 C rows at VOUT - VIN = 0.3 V: 1.54/2/2.46 A at 610 ohm, "
    "0.75/1/1.25 A at 1.15 kOhm, 0.38/0.5/0.62 A at 2.21 kOhm and "
    "0.034/0.05/0.066 A at 19.2 kOhm.  Archived at vendor/TI/"
    "ti-tps22950-q1-slvsgp6a-DDC0006A.pdf.")


# D-791 / D790-A12.  A BRACKET IS AN ESTIMATE UNLESS THE VENDOR SAYS THERE IS
# NOTHING BETWEEN THE ROWS, AND TI DOES NOT SAY IT.
#
# D-790 / R9-N01 replaced the widest published ratio with the WORSE OF THE TWO
# ROWS THAT BRACKET the programming resistor, and called the result the bound.
# Round-10 is right to refuse the word: TI publishes four points and states
# nothing at all about the accuracy BETWEEN them, so "no extremum lies between
# 1.15 k and 2.21 k" is an inference from four samples -- which is the exact
# shape of the argument D-788 / D788-01 refused when `U20`'s `RON` was
# interpolated, and of the one D-789 refused on the LTC4368's gate-drive row.
#
# SO THE RULING BOUND GOES BACK TO THE WIDEST PUBLISHED RATIO, WHICH NEEDS NO
# ASSUMPTION AT ALL, and the bracketed figure is REPORTED beside it as the
# engineering estimate it is.  That is strictly stronger than an explicit
# assumption and it removes the finding rather than arguing with it.
#
# WHAT IT COST AND WHAT WAS DONE ABOUT IT.  At the widest ratio `R97` = 1.78 k
# left `U12`'s compound worst case at 2.0139 A against its published 2 A --
# NEGATIVE margin once D790-A04's corrected backlight input is in.  `R97` is
# therefore 1.87 k (same UNI-ROYAL 0603 1 % line, `0603WAF1871T5E`, LCSC
# `C22850`), which guarantees 405.8 mA at the WIDEST published ratio against
# the owner-approved 400 mA budget and brings `U12`'s compound worst case to
# 1.9702 A.  Both budgets are preserved, as D790-A12 requires of any resistor
# change.
def ilim_accuracy_band(r_ilim_ohm, rows=None):
    """The RULING lo/hi ratio bound for a programming resistor.

    The WIDEST ratio the published table contains, which holds at every row
    and between every pair of rows without any assumption about what the
    accuracy does in between.  The bracketing rows and their (narrower) ratio
    are returned for REPORTING only -- see `ilim_bracketed_estimate`.
    """
    rows = ILIM_ACCURACY_ROWS if rows is None else rows
    ratios = [(rows[r][0] / rows[r][1], rows[r][2] / rows[r][1]) for r in rows]
    lo = min(x[0] for x in ratios)
    hi = max(x[1] for x in ratios)
    _, _, bracket = ilim_bracketed_estimate(r_ilim_ohm, rows)
    return lo, hi, bracket


def ilim_bracketed_estimate(r_ilim_ohm, rows=None):
    """D-790 / R9-N01's bracketed figure, RETAINED AS AN ESTIMATE.

    The worse of the two published rows that bracket the setting, per side.
    It is reported so the size of the conservatism D790-A12 requires is
    visible; nothing in this contract RULES on it.
    """
    rows = ILIM_ACCURACY_ROWS if rows is None else rows
    keys = sorted(rows)
    ratios = {r: (rows[r][0] / rows[r][1], rows[r][2] / rows[r][1])
              for r in keys}
    below = [r for r in keys if r <= r_ilim_ohm]
    above = [r for r in keys if r >= r_ilim_ohm]
    if not below or not above:
        lo = min(x[0] for x in ratios.values())
        hi = max(x[1] for x in ratios.values())
        return lo, hi, ["outside the published rows: widest ratio"]
    bracket = sorted({max(below), min(above)})
    lo = min(ratios[r][0] for r in bracket)
    hi = max(ratios[r][1] for r in bracket)
    return lo, hi, ["%g ohm" % r for r in bracket]
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
# D-792 / R11-04 -- THE DECLARED SIMULTANEOUS PAIR.
#
# THE PER-RAIL BUDGETS ABOVE DO NOT MOVE.  `ACC_3V3_SW` = 400 mA TOTAL and
# `ACC_5V_SW` = 300 mA TOTAL, each deliverable ON ITS OWN, remain exactly what
# D-098 published and what the D-788 owner decision preserved.  What D-792 has
# to state, because the corrected model says so, is what the two rails may draw
# AT THE SAME TIME.
#
# R11-07's itemised battery path (249.8 mOhm where D-791 carried 124 mOhm) and
# R11-02's missing ESP32-S3 baseline (165.5 mA in EVERY state) together cost
# about 0.34 V of node at the dual-rail current.  At the top of the declared
# 0..40 C ambient envelope, in the lightest internal state, the FULL pair now
# settles the node at 3.1763 V -- inside every one of the seven hardware limits
# and 44 mV BELOW the retention criterion the firmware itself applies.
#
# THIS PAIR IS SOLVED, NOT CHOSEN.  F12 derives it as the largest proportional
# derating of the two published budgets that the retention rule holds at the
# SAME critical cell voltage the single-rail permission already reaches, rounded
# DOWN onto a 10 mA grid -- and then REFUSES if this constant differs from what
# it derived.  It is stated here because F6 needs it before F12 runs.
DECLARED_DUAL_RAIL_BUDGET_A = {"ACC_3V3": 0.220, "ACC_5V": 0.170}
DECLARED_DUAL_RAIL_BASIS = (
    "D-792 / R11-04.  Solved by F12 at the critical cell OCV of the worse "
    "single-rail configuration in the lightest internal state, at the top of "
    "the declared ambient envelope, rounded DOWN onto a 10 mA grid.  The "
    "per-rail budgets are UNCHANGED and each is deliverable alone; this is the "
    "pair that may be drawn at once.  The FULL pair is retained everywhere as "
    "a reported negative control.")
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
# D-789 / D788-02.  THE PUBLISHED MINIMUM IS NO LONGER A CONSTANT.
#
# D-788 carried `PUBLISHED_CONNECTOR_MIN_V = 2.95` and the clause read
# `delivered >= 2.95`.  That is a control aimed BY HAND at a number the
# derivation happened to produce: the moment the derivation moved -- which is
# exactly what Round-8's corrections to the RON bound and the return network
# do -- the constant became the wrong answer while still looking like a gate.
# The published minimum is now DERIVED from the worst permitted mode (see
# `p3v3_delivery` inside `judge_accessory_envelope`) and rounded DOWN onto a
# 10 mV grid, and what the CLAUSE asks is a different question with a real
# floor behind it:
#
#   * the derived worst mode must stay above the tightest published minimum
#     supply voltage among the parts THE BOARD ITSELF powers from
#     `/ACC_3V3_SW` -- a datasheet limit, archived, that a divider change or a
#     worse delivery path could genuinely break;
#   * the OWNER-DECISION anchor must still hold: D-788 Option A publishes a
#     3.2 V-class rail, so the unloaded nominal must still round to 3.2 V;
#   * and `DEVICE_SPEC` must print the SAME derived number this file computes.
#
# THE ON-BOARD FLOOR.  `/ACC_3V3_SW` feeds U16 (TCA4307DGKR I2C buffer), J8
# (Qwiic/STEMMA QT), Q10's drain-side pull-up network, R46/R49/R50/R63 and
# three decoupling capacitors.  U16 is the only active part, and TI's own
# Recommended Operating Conditions table gives its VCC range as 2.3 V to
# 5.5 V -- archived at
# `vendor/TI/ti-tca4307-zhcslq0-DGK0008A.pdf` with its source record beside
# it, obtained through the live D-096 distributor record's own datasheet link
# and corroborated by that record's `Voltage - Supply: 2.3V~5.5V` attribute.
ACC_3V3_ONBOARD_FLOOR_V = 2.30
ACC_3V3_ONBOARD_FLOOR_PART = "U16 TCA4307DGKR"
ACC_3V3_ONBOARD_FLOOR_BASIS = (
    "TI TCA4307 ZHCSLQ0 section 6.3 Recommended Operating Conditions, VCC "
    "supply voltage MIN 2.3 V (UVLO rising 2.1 V / falling 2.0 V).  U16 is "
    "the only active device the BOARD powers from /ACC_3V3_SW; everything "
    "else on that net is a connector, a test point, a pull-up or a decoupling "
    "capacitor.  Archived at vendor/TI/ti-tca4307-zhcslq0-DGK0008A.pdf.")
# The owner-decision anchor.  D-788 Option A publishes "approximately 3.2 V
# nominal"; this is that sentence as a number the gate can refuse.
PUBLISHED_CONNECTOR_NOMINAL_CLASS_V = 3.2
# What "approximately" is allowed to mean.  The D-788/D-789 divider's own
# nominal is 3.145503 V, 54.5 mV under the owner's stated class.
PUBLISHED_CONNECTOR_CLASS_TOLERANCE_V = 0.10
PUBLISHED_CONNECTOR_MIN_GRID_V = 0.01
PUBLISHED_CONNECTOR_MIN_AUTHORITY = (
    "Owner-approved D-788 Option A, 2026-09-20: 3.2 V-class Community-Port "
    "rail, full 400 mA capability retained; the exact release envelope is to "
    "be DERIVED and frozen from the final candidate, which D-789 does.  The "
    "400 mA and 300 mA current budgets are unchanged.  D-789 supersedes "
    "D-788's 2.95 V figure: that number was computed with U20's RON "
    "INTERPOLATED between two datasheet rows and with the J5 return divided "
    "by four contacts carrying only the 3.3 V rail's current.  Both are "
    "corrected -- a monotone row bound at U20's own input, and a return "
    "solved over every permitted ground-contact count with the ACC_5V current "
    "sharing it -- and the published minimum is now whatever the worst "
    "permitted mode gives.")
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
# The bound is now DERIVED.  *(D-790 / D789-A08: this sentence used to end "and
# it is an interpolation between two GUARANTEED rows rather than an
# extrapolation beyond one", which was D-787's answer and was REFUSED by D-788
# / D788-01 immediately below.  The bound this file actually applies is the
# guaranteed maximum at the nearest published row AT OR BELOW the input -- the
# 1.8 V row's 116 mOhm -- and nothing is interpolated.  The stale clause is
# removed rather than left standing beside the paragraph that overturns it.)*
# SLVSGP6A gives RON max over -40..+125 C at three input voltages:
#
#        VIN      1.8 V     3.3 V     5.0 V
#        25 C      90        51        41     mOhm
#        85 C     105        62        49     mOhm
#       125 C     116        68        54     mOhm
#
# D-789 / D788-01.  A CHORD IS NOT A BOUND UNLESS THE CURVE IS CONVEX, AND
# NOTHING GUARANTEES THAT IT IS.
#
# D-788 interpolated linearly between the 1.8 V and 3.3 V guaranteed maxima and
# called the chord an upper bound, on the argument that the three published
# temperature rows each show a positive second difference.  Round-8 is right to
# refuse it: three points establish ONE second difference per row, TI publishes
# no RON-vs-VIN maximum curve, and "the samples we can see look convex" is not
# a guarantee.  A bound that depends on the SHAPE of an unpublished curve is
# the same class of defect as the 3.3 V row D-787 used at 3.07 V.
#
# WHAT IS GUARANTEED IS MONOTONICITY, AND IT IS GUARANTEED BY THE DEVICE RATHER
# THAN BY THE SAMPLES.  The TPS22950 is an N-channel pass FET whose gate is
# driven by an internal charge pump referenced to VIN (SLVSGP6A 8.3.1), so the
# channel's gate overdrive RISES with VIN and RON FALLS.  Every row of the
# published table agrees at every temperature -- 116/68/54, 105/62/49,
# 90/51/41 mOhm at 1.8/3.3/5.0 V -- and so does TI's own Figure 6-3.  Under
# monotonic decrease ALONE, and with no assumption about curvature,
#
#     RON(VIN) <= RON(V_row)  for every published row with V_row <= VIN
#
# so the bound at any VIN is the maximum published at the NEAREST ROW AT OR
# BELOW IT.  It is a step function, it is conservative by construction, and it
# needs nothing that TI has not printed.  For this rail -- U20's input is the
# +3V3 plane at about 3.06 V -- the bound is therefore the 1.8 V row's
# 116 mOhm and not D-788's interpolated 75.4 mOhm.  The cost is 16 mV at the
# published 400 mA and it is paid.
#
# AND THE ARGUMENT IS EVALUATED AT U20's OWN INPUT, NOT AT THE SOURCE RAIL.
# The pour-delivered source side drops the rail before it reaches `U20.2`, so
# `u20_vin_V` below is the rail's heavy-load minimum less that drop, and the
# row is chosen from THAT.  (It changes nothing here -- both are far above the
# 1.8 V row and far below the 3.3 V one -- which is exactly why it has to be
# computed rather than assumed: the next divider change might not be.)
RON_TPS22950_MAX = {1.8: 0.116, 3.3: 0.068, 5.0: 0.054}
RON_TPS22950_MIN_VIN = 1.8      # SLVSGP6A operating input range floor
RON_TPS22950_BOUND_BASIS = (
    "SLVSGP6A ON-Resistance, the -40..+125 C rows: 116 mOhm at VIN = 1.8 V, "
    "68 at 3.3 V, 54 at 5.0 V.  The bound at an arbitrary VIN is the maximum "
    "published at the nearest row AT OR BELOW it, which requires only that "
    "RON decrease with VIN -- a property of the charge-pumped N-channel pass "
    "FET, corroborated by all three temperature rows and by Figure 6-3.  No "
    "interpolation and no curvature assumption.")


def tps22950_ron_max(vin_V):
    """GUARANTEED -40..+125 C RON upper bound at an arbitrary input voltage.

    Returns None below the part's own 1.8 V operating floor: there is no
    published row to bound it with and a defaulted number would be a guess.
    """
    if vin_V is None or vin_V < RON_TPS22950_MIN_VIN:
        return None
    rows = sorted(RON_TPS22950_MAX)
    chosen = rows[0]
    for v in rows:
        if v <= vin_V:
            chosen = v
    return RON_TPS22950_MAX[chosen]


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
    # D-789 / D788-07..09/16: the manual lead is retired, so the pack model
    # prices the SAME routed path the delivery clause does.
    "acc_3v3_sw": dict(rail="ACC_3V3_SW", src=("U20.5",),
                       snk=("J5.3",), bound_ohm=0.240,
                       last_measured_ohm=0.224425,
                       what="U20 output -> the Community Port's longest "
                            "3.3 V contact, by routed copper alone"),
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
# D-791 / D790-A03.  THESE ARE NOW THE **ENABLE** FLOORS AND THERE ARE THREE
# CONSTANTS, NOT TWO.  F12 (`judge_cell_to_load`) derives all three from the
# complete cell-to-load network; these module defaults exist only so this
# function stays pure for its own mutation controls and for
# `battery_pack_contract`, which calls it with no floors at all.  `main()`
# always parses the real constants out of `aqroot_accessory_power_policy.h`.
NORMAL_SINGLE_VBAT_FLOOR = 3.95         # the published ENVELOPE of the D-792
NORMAL_DUAL_VBAT_FLOOR = 3.95           # permission table, one and two rails
NORMAL_RETENTION_FLOOR = 3.20           # RETAIN a rail already on
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
    # D-789 / D788-02.  "THE SAME MATED HEADER ALWAYS PRESENTS FOUR" WAS NOT
    # TRUE OF THE PUBLISHED USAGE.
    #
    # D-788 divided the return contact by four and priced the WHOLE return
    # network at the 3.3 V rail's 400 mA.  Both halves are wrong against what
    # this product actually tells a user they may do.  `J5` is a 2.54 mm
    # header on an OPEN Community Port: the documented usage explicitly
    # includes individual jumper leads, and an accessory that takes +3V3 on one
    # contact and ground on one contact is a CONFORMING accessory.  One ground
    # contact is therefore a permitted mode and it is the worst one.
    #
    # And the return is SHARED.  The 5 V rail's accessory current comes back
    # through the same ground contacts, so under the published concurrent
    # budget the return carries 400 mA + 300 mA, not 400 mA.
    #
    # Both are now MODES rather than constants: the envelope is solved over the
    # cross product of every permitted ground-contact count and both permitted
    # load states, each duplicated +3V3 contact is still qualified ALONE, and
    # the GUARANTEE is the worst cell.  The better cells are reported beside it
    # so an accessory that mates the full header can see what it actually gets.
    gnd_contact_modes=(1, 2, 4),
    gnd_contact_modes_basis=(
        "J5 presents four GND contacts and a fully mated 24-way socket uses "
        "all four; the published Community-Port usage also permits individual "
        "2.54 mm jumper leads, for which ONE ground contact is a conforming "
        "connection.  The guarantee is quoted at ONE; two and four are "
        "reported."),
    return_load_modes={
        "acc_3v3_alone": ("ACC_3V3",),
        "both_published_budgets": ("ACC_3V3", "ACC_5V"),
    },
    return_load_modes_basis=(
        "the ACC_5V accessory current returns through the SAME J5 ground "
        "contacts, so the published concurrent budget puts 400 mA + 300 mA on "
        "the return while the forward path carries only the 3.3 V rail's "
        "400 mA."),
    contact_is_a_declared_allowance=True,
    contact_basis="Samtec SSQ series publishes a 6.3 A per-pin rating and no "
                  "contact-resistance row; 25 mOhm per mated contact is a "
                  "DECLARED allowance, measured at first article (C-ACC-01).  "
                  "The signal side is charged for ONE contact because the "
                  "clause qualifies each duplicated +3V3 contact ALONE; the "
                  "return side is charged over every permitted ground-contact "
                  "count, and the guarantee takes the worst.",
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
    #
    # D-789 / D788-07 + D788-08 + D788-09 + D788-16.  NEITHER IS REINFORCED
    # ANY MORE.  Round-8 raised four independent findings against the single
    # manual TP12.1 -> J5.3 lead: a tip geometry that cannot fit a 1.00 mm
    # pad, an insertion into a through-hole whose Samtec tail already fills
    # it, a route through BATTERY_SHADOW and across RIB_R3 that the record's
    # own clearances forbid, and an acceptance that cannot be measured because
    # the board's own copper stays in parallel with the lead.  All four are
    # properties of the conductor, not of its description.  It bought 70 mV of
    # published minimum on ONE of two duplicated contacts, and it is retired;
    # see `docs/full-beta-v2/assembly/ACC_3V3_REINFORCEMENT.json`.
    contacts={
        "J5.3": dict(board_copper_src=("U20.5",), board_copper_snk=("J5.3",),
                     board_copper_bound_ohm=0.240,
                     reinforced=False,
                     what="U20 output -> J5.3 by routed copper alone, 224.4 "
                          "mOhm measured.  This is the contact the retired "
                          "manual lead existed for and it is qualified ALONE."),
        "J5.22": dict(board_copper_src=("U20.5",), board_copper_snk=("J5.22",),
                      board_copper_bound_ohm=0.090,
                      reinforced=False,
                      what="U20 output -> J5.22 by routed copper alone, 79.0 "
                           "mOhm measured -- always better than any manual "
                           "lead that could have been run to it"),
    },
    # D-789 / D788-02, second half.  The review permits binding the guarantee
    # to an explicit CONNECTION CONTRACT, and a 24-way socket fully mated is a
    # materially different network from a single jumper: BOTH duplicated +3V3
    # contacts carry, in parallel, and all four grounds return.  Both are
    # published -- the unconditional figure is the guarantee, the mated figure
    # is what a socketed accessory actually gets, and it is better than the
    # 2.95 V D-788 published with a hand-soldered conductor fitted.
    fully_mated_contract=dict(
        forward_contacts=("J5.3", "J5.22"),
        gnd_contacts=4,
        what="both duplicated +3V3 contacts and all four GND contacts mated, "
             "which is what the SSQ-124 socket this port is drawn for "
             "presents"))
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


def p3v3_ac_envelope(rail_min_V, rail_max_V, internal_load_A, spec=None,
                     accessory_load_A=None):
    """Ripple, computed; transient, declared unprovable and deferred.

    D-789 / D788-12.  THE RIPPLE TERM RAN ON THE INTERNAL LOAD ALONE.  In boost
    mode the output capacitor carries the WHOLE output current for the duty
    cycle, and `U12`'s output current is not the internal budget -- it is the
    internal budget PLUS whatever the Community Port is drawing through `U20`,
    which sits on the same rail.  At the published 400 mA that is a 38 % larger
    ripple than D-788 computed, and the ripple is charged to BOTH margins.
    `accessory_load_A` defaults to the published ACC_3V3 budget so no caller
    can forget it.
    """
    spec = P3V3_AC if spec is None else spec
    if accessory_load_A is None:
        accessory_load_A = PUBLISHED_RAIL_BUDGET_A["ACC_3V3"]
    total_load_A = internal_load_A + accessory_load_A
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
    ripple_boost = (total_load_A * duty / (f * c_eff)
                    + dil_boost * spec["local_esr_ohm"])
    ripple_pp = max(ripple_buck, ripple_boost)
    return dict(
        internal_load_A=internal_load_A,
        accessory_load_A=accessory_load_A,
        total_u12_output_load_A=round(total_load_A, 6),
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
               "charged to BOTH the high-side and low-side margins.  D-789 / "
               "D788-12: the boost-mode term uses U12's TOTAL instantaneous "
               "output load -- the internal budget PLUS the published 400 mA "
               "Community-Port budget, which is drawn through U20 from this "
               "same rail -- and not the internal budget alone.")


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
    # D-789 / D788-12.  The declared plane allowance between U12's output and
    # U1's supply pad is charged at the TOTAL rail current for the same reason:
    # U20's input stub hangs off that same +3V3 plane, so the accessory's
    # 400 mA flows through part of the sheet the MCU is fed from.  Charging the
    # whole allowance at the total is the conservative reading of a bound that
    # is already declared rather than measured.
    drop = spec["distribution_to_mcu_bound_ohm"] * ac["total_u12_output_load_A"]

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
        accessory_load_A=ac["accessory_load_A"],
        total_u12_output_load_A=ac["total_u12_output_load_A"],
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
# D-792 -- THE BACKLIGHT CONVERTER MODEL MOVED TO THE CANONICAL POWER MODEL.
#
# R11-02's finding is that this model was SOLVED here and TYPED into
# `audit_rail_ampacity`, and when D-791 moved the solved figure the typed copy
# did not follow.  It now lives in `aqroot_power_model` and BOTH files import
# it, so there is exactly one copy in the repository.  The names below are
# re-exported because this contract's own clauses, its controls and its
# mutation tests all reference them.
# --------------------------------------------------------------------------
BACKLIGHT_BOOST = apm.BACKLIGHT_BOOST
_switching_W = apm._switching_W
backlight_converter_input = apm.backlight_converter_input
BACKLIGHT_INPUT = apm.BACKLIGHT_INPUT
PANEL_LOGIC_DECLARED_mA = apm.PANEL_LOGIC_DECLARED_mA
BACKLIGHT_LEDGER_TOKENS = ("C-DISP-01",)
# D-791 / D790-A13.  WHAT Q11 HAS TO SUSTAIN IS DERIVED, NOT REMEMBERED.
#
# This was `0.109`, D-079's LED setpoint, hand-written in 2023.  The current
# the string ACTUALLY draws has been solved from published maxima since D-790 /
# D789-A11 -- `VREF(max) / R69(min)` = 220 mV / (1.87 x 0.99) = 118.8354 mA --
# and the static constant was 9.8 mA under it while F5's own prose quoted it as
# "what this circuit asks for".  Round-10 found the pair: a narrative citing
# `VGS = 2.396 V` and `0.109 A` beside live arithmetic that had already moved
# to 1.945526 V and 118.8354 mA.  The constant is now the derivation, and the
# narrative is FORMATTED FROM THE COMPUTED VALUES so it cannot drift again.
BL_STRING_CURRENT_A = apm.BL_STRING_CURRENT_A
BL_STRING_CURRENT_BASIS = apm.BL_STRING_CURRENT_BASIS

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
# D-792 / R11-02.  THIS TABLE IS NOW A VIEW OF THE CANONICAL LEDGER.
#
# It was a second load table beside `audit_rail_ampacity`'s sustained one, and
# the two disagreed about the backlight by 21.55 mA and about the processor by
# the whole processor.  `aqroot_power_model.LOAD_LEDGER` is the one list; the
# PEAK budget is every line at its peak, and the sustained always-on set, the
# optional-mode set and the bounded-duty allowances are the other views of the
# same list.  D-792 also corrects the module line itself (N-01): it read
# 355 mA, Espressif's Table 6-4 RF peak, for a module whose Table 6-2
# Recommended Operating Conditions require the external supply to deliver
# 500 mA MIN.
P3V3_INTERNAL_BUDGET = apm.peak_budget()
I_INTERNAL = apm.peak_A()
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
# D-792 / R11-02.  U12 IS NOW JUDGED THE WAY U21 ALREADY WAS.
#
# R11-02's missing ESP32-S3 baseline added 165.5 mA to the +3V3 peak envelope,
# and the D-791 clause compared `internal_peak + the ACCESSORY LIMITER'S FAULT
# MAXIMUM` against the 2 A Features headline.  It passed by 10 mA, which is not
# a margin, and it now fails by 116 mA.  Two things were wrong with the
# comparison and neither is the new baseline:
#
#   * IT MIXED A CONFORMING LOAD WITH A FAULT ONE.  `ilim_max` is the current a
#     SHORTED accessory draws before U20 trips; the published budget is what a
#     conforming one draws.  The 2 A guaranteed figure is the right bound for
#     the conforming case and the wrong one for a fault excursion.
#   * IT USED THE HEADLINE INSTEAD OF THE DEVICE.  "2 A" is TI's Features line
#     across the whole recommended VIN range.  The DEVICE limit is the average
#     switch current limit, and SLVSAA7's EC table gives it a MIN column --
#     which is exactly how this contract already bounds U21.  At this board's
#     3.0 V cell corner that bound is far above the headline.
#
# So the clause now asks BOTH questions, with the fault excursion bounded by
# the device's own protection rather than by a marketing figure.
U12_ISW_MIN_A = 3.5        # SLVSAA7 EC: ISW average switch current limit,
U12_FSW_MIN_HZ = 2.2e6     # MIN 3500 / TYP 4000 / MAX 4500 mA; f 2200 kHz MIN
U12_L_H, U12_L_TOL = 1.5e-6, 0.20      # L1, 1.5 uH, at the same declared -20 %
U12_LIMIT_SOURCE = (
    "TI SLVSAA7 (TPS63020) Electrical Characteristics: ISW 'Average switch "
    "current limit' 3500 / 4000 / 4500 mA at VIN = VINA = 3.6 V, TA = 25 C, "
    "and f 'Oscillator frequency' 2200 / 2400 / 2600 kHz.  Section 7.3.2 "
    "reduces the limit below VIN = 2.3 V, which is BELOW this contract's 3.0 V "
    "cell corner.  The fitted inductor is L1 = 1.5 uH, carried at the same "
    "declared -20 % corner this contract charges L4.  Archived at "
    "vendor/TI/ti-tps63020-slvsaa7-DSJ0010A.pdf.")
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


# ==========================================================================
# F13 -- EVERY NON-CAPACITOR MPN IS CHECKED AGAINST ITS SOURCE'S OWN BRAND.
#
# ADDED AT D-791 / D790-F-N01 + Fable V-05.
#
# F8 already binds every FITTED CAPACITOR to an exact purchased identity and
# checks its voltage rating against the derating rule.  Nothing did the
# equivalent for the rest of the board, and the consequence was five parts
# whose schematic MANUFACTURER field named a company that does not make them:
#
#   * `Q4`, `Q6`, `Q7`, `Q8`, `Q9` are `BSS138LT1G`, LCSC `C82045`.  That is an
#     **onsemi** part and the schematic said "Alpha & Omega Semiconductor" --
#     the manufacturer of the OTHER small-signal FETs on the same sheet.  This
#     is Fable's `F-N01`.
#   * `Q10` is `2N7002`, LCSC `C8545`.  That record's brand is **Jiangsu
#     Changjing Electronics Technology** and the schematic said "onsemi", which
#     is the same defect in the opposite direction and was found HERE
#     (`R10-N03`) by the clause this note documents.
#   * `Q5`'s `AO3401A` said "Alpha & Omega" where every other AOS part on the
#     board says "Alpha & Omega Semiconductor" -- not wrong, but a second
#     spelling is how a cross-check gets turned off.
#
# WHY IT MATTERS ON A BOARD THAT IS ASSEMBLED FROM LCSC CODES.  It matters
# because a human reads the schematic and a human writes the purchase order.
# The LCSC code is the thing JLCPCB fits; the MANUFACTURER field is the thing a
# person uses to decide whether a substitution offered over email is the same
# part.  A field that names the wrong company is a trap laid for exactly that
# conversation, and this programme has already been caught by one
# (`D-768`'s panel, `D-790`'s `D14` vendor record).
#
# WHAT IT CHECKS.  For every FITTED, non-capacitor reference that carries an
# MPN: the archived exact-MPN distributor record must EXIST, its own brand must
# match the schematic's Manufacturer field after normalisation, and its LCSC
# code must match the schematic's.  Normalisation folds case, punctuation and
# the distributor's own truncations -- `Alpha & Omega Semicon` is how LCSC
# prints `Alpha & Omega Semiconductor` -- and nothing else.  A part with no
# archived record is a FAILURE, not a skip.
MFR_ALIASES = (
    # Each tuple is one company.  The first entry is the canonical form this
    # board writes; the rest are spellings the distributor uses.
    ("alpha & omega semiconductor", "alpha & omega semicon",
     "alpha & omega", "aos"),
    ("onsemi", "on semiconductor", "onsemiconductor"),
    ("texas instruments", "ti"),
    ("analog devices", "analog devices (maxim)", "maxim integrated", "adi",
     "analog devices inc./maxim", "analog devices inc", "analog devices inc.",
     "analog devices inc./maxim integrated",
     "analog devices inc/maxim integrated"),
    ("stmicroelectronics", "st microelectronics", "stmicro"),
    ("nxp semiconductors", "nxp"),
    ("vishay", "vishay intertech", "vishay siliconix",
     "vishay intertechnology"),
    ("yageo", "yageo corporation"),
    ("uni-royal(uniroyal elec)", "uni-royal", "uniroyal elec",
     "uni-royal (uniroyal elec)"),
    ("murata electronics", "murata"),
    ("samsung electro-mechanics", "samsung electro mechanics", "samsung"),
    ("jiangsu changjing electronics technology",
     "jiangsu changjing electronics technology co., ltd.",
     "jiangsu changjing electronics technology co.,ltd",
     "changjing electronics"),
    ("coilcraft",), ("wurth elektronik", "wurth", "würth elektronik"),
    ("littelfuse",), ("bourns",), ("nexperia",),
    ("diodes incorporated", "diodes inc", "diodes"),
    ("espressif systems", "espressif"),
    ("bosch sensortec", "bosch"),
    ("meihua", "meihua (lianyungang meihua electronic technology)",
     "lianyungang meihua electronic technology"),
    ("pui audio", "pui audio inc"),
    ("hirose", "hirose electric", "hrs(hirose)", "hrs", "hrs (hirose)"),
    ("molex",), ("jst",), ("samtec",),
    ("gct (global connector technology)", "gct", "global connector technology"),
    ("panasonic",), ("viking tech", "viking"),
    ("ebyte (chengdu ebyte electronic technology)", "ebyte",
     "chengdu ebyte electronic technology", "chengdu ebyte elec tech",
     "chengdu ebyte electronic technology co.,ltd"),
    ("c&k (littelfuse)", "c&k / littelfuse", "c&k", "ck"),
    ("fh (guangdong fenghua advanced technology)", "fh",
     "guangdong fenghua advanced tech"),
    ("yajingxin", "yjx"),
    ("cctc", "cctc (chaozhou three-circle)"),
    ("lrc", "leshan radio company"),
)
# D-792 / R11-09.  A CORPORATE SUFFIX IS NOT A DIFFERENT COMPANY.
#
# ROUND-11, IN ITS OWN WORDS: "manufacturer canonicalizer rejects legitimate
# PUI Audio, Inc. vs PUI Audio spelling.  Add a narrow tested alias without
# weakening contradiction detection."
#
# It reproduces.  The alias table carried `pui audio inc`; the live distributor
# record prints `PUI Audio, Inc.`, and the fold kept the comma and the trailing
# period, so the two never met and F13 read a genuine agreement as a
# CONTRADICTION.  The fix is DELIBERATELY NARROW: a trailing legal-form token --
# `Inc`, `Corp`, `Ltd`, `LLC`, `GmbH`, `Co`, with or without a period, with or
# without a preceding comma -- is dropped, and commas are dropped everywhere.
# Nothing else about the name is touched, so two DIFFERENT companies remain
# different: the contradiction detector loses no power, which is the half of
# R11-09 that matters.  Both sides of the comparison are folded by the SAME
# function, so the alias table cannot drift out of the fold's reach again.
_LEGAL_FORMS = ("inc", "incorporated", "corp", "corporation", "co", "company",
                "llc", "ltd", "limited", "gmbh", "ag", "kg", "bv", "nv",
                "plc", "sa", "srl", "spa", "pte", "pty", "kk")


def fold_manufacturer(name):
    """Case, spacing, commas and TRAILING LEGAL FORMS only."""
    key = re.sub(r"\s+", " ", (name or "").strip().casefold())
    key = key.replace("co., ltd.", " ").replace("co.,ltd", " ")
    key = key.replace(",", " ")
    key = re.sub(r"\s+", " ", key).strip(" .")
    # Repeatedly, because "Foo Co., Ltd." leaves two of them behind.
    for _ in range(4):
        m = re.match(r"^(.*?)\s+(%s)\.?$" % "|".join(_LEGAL_FORMS), key)
        if not m or not m.group(1).strip():
            break
        key = m.group(1).strip(" .")
    return re.sub(r"\s+", " ", key).strip()


MFR_CANONICAL = {}
for _group in MFR_ALIASES:
    for _name in _group:
        MFR_CANONICAL[fold_manufacturer(_name)] = _group[0]


def canonical_manufacturer(name):
    """Fold case, spacing, commas and trailing legal forms, then apply the
    alias table."""
    if not name:
        return None
    key = fold_manufacturer(name)
    if key in MFR_CANONICAL:
        return MFR_CANONICAL[key]
    # A distributor truncation: accept a source brand that is a PREFIX of a
    # known canonical name, which is how LCSC prints long company names.
    for known, canon in MFR_CANONICAL.items():
        if known.startswith(key) and len(key) >= 8:
            return canon
    return key


def schematic_part_rows(refs):
    """D-791 / D790-F-N01.  {ref: {value, mpn, lcsc, manufacturer}} off the
    hierarchical sheets.  A reference whose symbol carries no field comes back
    with the empty string rather than absent, so the caller REFUSES instead of
    falling through -- the same convention `schematic_mpns` uses.
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
            row = {}
            for field, key in (("Value", "value"), ("MPN", "mpn"),
                               ("LCSC", "lcsc"),
                               ("Manufacturer", "manufacturer")):
                m = re.search(r'\(property "%s" "((?:[^"\\]|\\.)*)"' % field,
                              block)
                row[key] = m.group(1) if m else ""
            out[ref] = row
    return {ref: out.get(ref, dict(value="", mpn="", lcsc="",
                                   manufacturer="")) for ref in want}


# THE ONLY EXEMPTION, AND IT IS NOT A PURCHASED PART.  `J4` is D-781's manual
# battery pigtail: a pair of plated through-holes on this board with factory
# pre-crimped leads soldered into them.  Its "MPN" is the programme's own
# `D-781-BAT-PIGTAIL` token, there is no distributor line to cross-check it
# against, and the exact identities of the things that ARE purchased for it --
# the Molex housings, terminals and wire -- are frozen and gated separately by
# `F9` and `battery_pack_contract` `B9`-`B14`.  Any other reference that lacks
# a record FAILS.
PART_SOURCE_EXEMPT = {
    "J4": "D-781 manual battery pigtail: board lands plus factory pre-crimped "
          "leads, not a distributor line.  Its purchased components are "
          "frozen by F9 and battery_pack_contract B9-B14.",
}


def judge_part_source_identity(rows, exempt=None):
    """D-791 / D790-F-N01 + Fable V-05.  Pure over {ref: {...}}.

    Each row is {value, mpn, lcsc, manufacturer}.  Returns (ok, detail).
    """
    exempt = PART_SOURCE_EXEMPT if exempt is None else exempt
    findings, problems = {}, []
    for ref, row in sorted(rows.items()):
        if ref in exempt:
            findings[ref] = dict(mpn=(row.get("mpn") or ""), exempt=True,
                                 why=exempt[ref], ok=True)
            continue
        mpn = (row.get("mpn") or "").strip()
        live = live_stock_for(mpn) if mpn else None
        sch = canonical_manufacturer(row.get("manufacturer"))
        src = canonical_manufacturer((live or {}).get("brand"))
        d = dict(mpn=mpn, schematic_manufacturer=row.get("manufacturer"),
                 schematic_manufacturer_canonical=sch,
                 schematic_lcsc=row.get("lcsc"),
                 source_record=(live or {}).get("record"),
                 source_brand=(live or {}).get("brand"),
                 source_brand_canonical=src,
                 source_lcsc=(live or {}).get("lcsc"),
                 has_an_exact_mpn_record=bool(live and live.get("brand")),
                 manufacturer_matches_the_source=bool(sch and src and sch == src),
                 lcsc_matches_the_source=bool(
                     row.get("lcsc") and (live or {}).get("lcsc")
                     and row["lcsc"] == live["lcsc"]))
        d["ok"] = bool(d["has_an_exact_mpn_record"]
                       and d["manufacturer_matches_the_source"]
                       and d["lcsc_matches_the_source"])
        if not d["ok"]:
            problems.append(ref)
        findings[ref] = d
    return (not problems), dict(
        references=sorted(findings), findings=findings, problems=problems,
        alias_groups=[list(g) for g in MFR_ALIASES],
        exempt={k: v for k, v in (exempt or {}).items()},
        method="every FITTED non-capacitor reference that carries an MPN is "
               "checked against the COMMITTED exact-MPN distributor record "
               "this repository archives under D-096: the record must exist, "
               "its own brand must equal the schematic's Manufacturer field "
               "after alias normalisation, and its LCSC code must equal the "
               "schematic's.  Normalisation folds case, spacing, punctuation "
               "and the distributor's own truncations and NOTHING else -- an "
               "alias table that accepted a genuine contradiction would be "
               "the defect rather than the check.")


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
                             connection=None, reserve=None, mpns=None,
                             retention_floor=None, sustained_internal_A=None,
                             published_budget=None):
    """Pure over {ref: value}; returns (ok, detail).  D-753 + D-765 + D-771.

    D-753's four modes and its two refusal clauses are UNCHANGED in intent.
    D-765's three identity/range clauses are unchanged.  D-771 adds the two
    that had no words -- the PUBLISHED budget each rail must guarantee, and
    the protection chain ordered over its own TOLERANCE rather than over a
    typical -- and folds the programming resistor's tolerance into the
    envelope modes, which previously used the nominal value alone.
    """
    d, rails, parts = {}, {}, {}
    # D-791 / R10-N02: the published budgets are an INPUT so the clause that
    # says "no conforming accessory state trips the pack" can be proved
    # non-vacuous by moving them.
    published_budget = (PUBLISHED_RAIL_BUDGET_A if published_budget is None
                        else published_budget)
    single_floor = (NORMAL_SINGLE_VBAT_FLOOR if single_floor is None
                    else single_floor)
    dual_floor = NORMAL_DUAL_VBAT_FLOOR if dual_floor is None else dual_floor
    retention_floor = (NORMAL_RETENTION_FLOOR if retention_floor is None
                       else retention_floor)
    # D-791 / D790-A02 + D790-A03.  THE FLOOR IS DERIVED AT THE LOAD THE
    # PRODUCT CAN ACTUALLY HOLD, NOT AT THE PEAK ENVELOPE.
    #
    # D-790 derived the policy floors with `iint = I_INTERNAL`, the PEAK +3V3
    # envelope -- every internal subsystem at its published maximum at once.
    # D-790 itself established that the peak envelope is not a steady state
    # (it is 8 W of continuous dissipation in a sealed handheld) and then went
    # on deriving a SUSTAINED policy floor from it.  The requirement below is
    # therefore derived at the SUSTAINED REFERENCE internal load, and the peak
    # figure is retained beside it as the number it is: the node voltage the
    # peak envelope would need, which F12 proves the node cannot reach.
    if sustained_internal_A is None:
        sustained_internal_A = round(
            sum(ara.SUSTAINED_ALWAYS_ON.values())
            + ara.BURSTY_TIME_AVERAGED_A
            + sum(ara.SUSTAINED_OPTIONAL[m]
                  for st in ara.SUSTAINED_STATES
                  if st["key"] == ara.SUSTAINED_REFERENCE_KEY
                  for m in st["modes"]), 6)
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
        # D-790 / R9-N01: the band is the worse of the two PUBLISHED rows that
        # bracket this programming resistor, not the table's widest row.
        acc_lo, acc_hi, acc_rows = ilim_accuracy_band(r)
        est_lo, est_hi, _ = ilim_bracketed_estimate(r)
        rails[rail] = dict(ref=ref, r_ohms=r, r_tol=tol,
                           ilim_min=typ_lo * acc_lo,
                           ilim_typ=typ,
                           ilim_max=typ_hi * acc_hi,
                           accuracy_lo=round(acc_lo, 6),
                           accuracy_hi=round(acc_hi, 6),
                           accuracy_bracket_rows=acc_rows,
                           accuracy_source=ILIM_ACCURACY_SOURCE,
                           widest_published_ratio=[ILIM_LO, ILIM_HI],
                           # D-791 / D790-A12: REPORTED, never ruled on.
                           bracketed_estimate_lo=round(est_lo, 6),
                           bracketed_estimate_hi=round(est_hi, 6),
                           bracketed_estimate_min_A=round(typ_lo * est_lo, 6),
                           bracketed_estimate_max_A=round(typ_hi * est_hi, 6),
                           bracketed_estimate_is_not_the_bound=(
                               "TI publishes four ILIM accuracy rows and says "
                               "nothing about the accuracy BETWEEN them, so "
                               "the bracketed figure is an engineering "
                               "estimate.  This contract rules at the WIDEST "
                               "published ratio, which needs no assumption."),
                           published_budget_A=published_budget[rail])

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
    # D-789 / D788-11: the arithmetic lives in `p3v3_pwm_envelope` so F5's
    # held-gate derivation reads the SAME rail rather than a second copy.
    pe, pe_err = p3v3_pwm_envelope(values, mpns)
    if pe_err:
        return False, dict(error=pe_err)
    p3_top, p3_bot = pe["top_ohms"], pe["bottom_ohms"]
    p3_top_tol, p3_bot_tol = pe["top_tolerance"], pe["bottom_tolerance"]
    divider_mpns = {P3V3_FB["top"]: pe["top_mpn"],
                    P3V3_FB["bottom"]: pe["bottom_mpn"]}
    top_tcr, bot_tcr = pe["top_tcr_ppm_per_C"], pe["bottom_tcr_ppm_per_C"]
    divider_parts_are_known = pe["divider_parts_are_known"]
    p3_raw_lo, p3_raw_nom, p3_raw_hi = pe["raw_lo"], pe["raw_nom"], pe["raw_hi"]
    p3_pwm_heavy_lo, p3_pwm_heavy_hi = pe["heavy_lo"], pe["heavy_hi"]
    p3_ps_hi = pe["ps_hi"]

    # D-789 / D788-07 + D788-08 + D788-09 + D788-16.  THE CLAUSE INVERTS.
    #
    # D-787 and D-788 required the record to NAME an exact manual conductor.
    # The conductor is retired, so what the clause has to hold is the other
    # direction: the record must DECLARE that no manual conductor is required,
    # it must name no destination, and -- the part that stops this becoming a
    # loophole -- if a future record ever re-introduces one, it may only do so
    # with a QUALIFIED joint specification for both ends and an acceptance that
    # can be measured with the board's own parallel copper accounted for.  A
    # record that names a destination without those is REFUSED, which is
    # exactly what D-788's record would be.
    reinforcement = {}
    if ACC_3V3_REINFORCEMENT.exists():
        reinforcement = json.loads(ACC_3V3_REINFORCEMENT.read_text())
    destinations = reinforcement.get("destinations") or []
    declares_none = reinforcement.get("manual_conductor_required") is False
    reinf_r = 0.0
    reinforcement_problems = []
    if not reinforcement:
        reinforcement_problems.append("the reinforcement record is absent")
    elif declares_none:
        if destinations:
            reinforcement_problems.append(
                "the record declares no manual conductor and then names %d "
                "destination(s)" % len(destinations))
        if reinforcement.get("source", {}).get("net") != "/ACC_3V3_SW":
            reinforcement_problems.append(
                "the record's retained test-point net is not /ACC_3V3_SW")
        if (reinforcement.get("retention") or {}).get("material") is not None:
            reinforcement_problems.append(
                "the record declares no manual conductor and then names a "
                "retention adhesive for one")
    else:
        # A record that DOES require a conductor must qualify it.  These are
        # the four things Round-8 found missing, as clauses.
        acc = reinforcement.get("electrical_acceptance", {})
        reinf_r = float(acc.get(
            "each_finished_lead_max_milliohm_at_room_temperature", 1e9)) / 1000.0
        joint = reinforcement.get("joint_profile", {})
        for need, why in (
                ("qualified_joint_geometry",
                 "a dimensioned, buildable joint geometry for EVERY named "
                 "termination -- strip, tin, trim, insulation setback and the "
                 "clearance to the nearest foreign copper (D788-07)"),
                ("qualified_termination_at_the_connector",
                 "a termination at the connector that does not require "
                 "inserting a conductor into an occupied through-hole "
                 "(D788-08)"),
                ("toleranced_route_in_the_mechanical_datum",
                 "a toleranced route, joint and adhesive envelope in the "
                 "enclosure's own datum, clear of every reserved region "
                 "(D788-09)"),
                ("isolated_resistance_measurement",
                 "an acceptance measurement that isolates the lead from the "
                 "board's own parallel copper (D788-16)")):
            if not joint.get(need) and not acc.get(need):
                reinforcement_problems.append(
                    "a manual conductor is declared but the record has no %s"
                    % why)
    reinforcement_identity_ok = not reinforcement_problems

    # ---- D-789 / D788-01 + D788-02: THE COMPLETE NETWORK, EVERY MODE ------
    #
    # Each duplicated +3V3 contact is qualified ALONE (an accessory may use
    # either one by itself, so neither gets credit for the other), and the
    # FORWARD and RETURN halves are priced separately because they do not carry
    # the same current and are not made of the same number of contacts.  The
    # envelope is solved over the cross product of
    #
    #     {the two duplicated +3V3 contacts}
    #   x {1, 2, 4 mated ground contacts}
    #   x {ACC_3V3 alone, ACC_3V3 + ACC_5V at their published budgets}
    #
    # and the GUARANTEE is the worst cell.  U20's RON is the guaranteed
    # published maximum at the nearest row at or below U20's OWN input voltage.
    k_hot = 1 + CU_TC_PER_K * CU_HOT_RISE_K
    i3_budget = published_budget["ACC_3V3"]
    source_hot = P3V3_DELIVERY["source_bound_ohm"] * k_hot
    # D788-01: U20's input is the +3V3 plane AFTER the pour-delivered source
    # side has dropped it, not the rail.
    #
    # D-790 / D789-A03, FIRST HALF.  THE SOURCE SIDE IS NOT THE ACCESSORY'S
    # ALONE.  `source_bound_ohm` is the U12-output-to-U20-input plane path, and
    # EVERY internal +3V3 consumer taps off that same plane: the current
    # through it is the WHOLE rail's, not the 400 mA the accessory takes.
    # D-789 charged it `i3_budget` only, which understated the drop by
    # `I_INTERNAL x source_hot` -- about 36 mV once D789-A11's corrected
    # display budget is in.  The source term below now carries
    # `I_INTERNAL + i3_budget`, and it is charged ONCE.
    i_source_total = I_INTERNAL + i3_budget
    source_drop = i_source_total * source_hot
    u20_vin = p3_pwm_heavy_lo - source_drop
    p3_ron = tps22950_ron_max(u20_vin)
    u20_vin_is_in_the_published_range = p3_ron is not None
    if p3_ron is None:
        # A refusal must not crash the report.  Run the arithmetic at the
        # lowest published row so the numbers printed beside the refusal are
        # still bounded, and let the CLAUSE carry the verdict.
        p3_ron = RON_TPS22950_MAX[RON_TPS22950_MIN_VIN]
    gnd_return_hot = P3V3_DELIVERY["gnd_return_bound_ohm"] * k_hot
    sig = P3V3_DELIVERY["signal_contact_ohm"]

    # D-790 / D789-A03, SECOND HALF.  THE COMMON EDGES ARE MODELLED ONCE.
    #
    # D-789 put `RON`, the source allowance and the process allowance INSIDE
    # each contact's series resistance and then paralleled the whole thing for
    # the fully-mated contract -- which HALVED three impedances that are in
    # series with BOTH branches and carry their SUM.  The network is now split
    # the way the copper is: a COMMON edge carrying the whole forward current,
    # and per-contact BRANCHES that may be paralleled because they genuinely
    # are in parallel.  Single-contact modes are arithmetically unchanged by
    # the split -- common + branch is the same sum -- so only the mated
    # contract moves, and it moves the honest way.
    common_forward = p3_ron + P3V3_DELIVERY["process_ohm"]
    p3_paths, p3_modes = {}, []
    for contact, spec in sorted(P3V3_DELIVERY["contacts"].items()):
        board = spec["board_copper_bound_ohm"] * k_hot
        lead = reinf_r * k_hot if spec["reinforced"] else 0.0
        # BRANCH: board copper (-> manual lead) -> the one mated signal
        # contact this accessory is using.  COMMON: U20's channel and the
        # process allowance, plus the source plane, which is charged at the
        # WHOLE rail's current above.
        branch = board + lead + sig
        forward = common_forward + source_hot + branch
        p3_paths[contact] = dict(
            branch_series_ohm=round(branch, 6),
            common_forward_series_ohm=round(common_forward, 6),
            common_is_charged_once=(
                "U20's channel, the process allowance and the source plane "
                "are in series with BOTH contacts and carry their sum; they "
                "are never paralleled"),
            what=spec["what"], reinforced=spec["reinforced"],
            u20_ron_ohm=round(p3_ron, 6),
            board_copper_bound_ohm=spec["board_copper_bound_ohm"],
            board_copper_hot_ohm=round(board, 6),
            manual_lead_hot_ohm=round(lead, 6),
            manual_lead_is_retired=(
                "D-789 / D788-07..09 + D788-16: no manual conductor is fitted "
                "on this rail in the first-five build"),
            signal_contact_ohm=sig,
            source_hot_ohm=round(source_hot, 6),
            process_ohm=P3V3_DELIVERY["process_ohm"],
            forward_series_ohm=round(forward, 6),
            forward_drop_at_published_budget_mV=round(
                i3_budget * forward * 1000, 4))
        for n_gnd in P3V3_DELIVERY["gnd_contact_modes"]:
            ret = sig / float(n_gnd) + gnd_return_hot
            for load_name, mode_rails in sorted(
                    P3V3_DELIVERY["return_load_modes"].items()):
                i_return = sum(published_budget[r] for r in mode_rails)
                # The source plane is already priced at the whole rail's
                # current in `source_drop`; the rest of the forward path is
                # the accessory's alone.
                delivered = (p3_pwm_heavy_lo - source_drop
                             - i3_budget * (common_forward + branch)
                             - i_return * ret)
                p3_modes.append(dict(
                    contact=contact, gnd_contacts_mated=n_gnd,
                    load_mode=load_name,
                    forward_current_A=i3_budget,
                    source_current_A=round(i_source_total, 6),
                    source_drop_mV=round(source_drop * 1000, 4),
                    return_current_A=round(i_return, 4),
                    forward_series_ohm=round(forward, 6),
                    return_series_ohm=round(ret, 6),
                    total_drop_mV=round(
                        (source_drop + i3_budget * (common_forward + branch)
                         + i_return * ret) * 1000, 4),
                    delivered_at_400mA_min_V=round(delivered, 6)))
    # D-789 / D788-02: the FULLY MATED contract -- both duplicated +3V3
    # contacts carrying in parallel and all four grounds returning.  It is
    # reported as its own mode and is NEVER the guarantee; the guarantee is
    # the worst UNCONDITIONAL mode above.
    fm = P3V3_DELIVERY.get("fully_mated_contract")
    fully_mated = None
    if fm:
        fwd = [p3_paths[c]["branch_series_ohm"] for c in fm["forward_contacts"]
               if c in p3_paths]
        if fwd:
            # D-790 / D789-A03: ONLY the branches parallel.  The common edge
            # carries the summed current and is charged once.
            parallel = 1.0 / sum(1.0 / x for x in fwd)
            ret = sig / float(fm["gnd_contacts"]) + gnd_return_hot
            fully_mated = {}
            for load_name, mode_rails in sorted(
                    P3V3_DELIVERY["return_load_modes"].items()):
                i_return = sum(published_budget[r] for r in mode_rails)
                fully_mated[load_name] = dict(
                    forward_contacts=list(fm["forward_contacts"]),
                    gnd_contacts_mated=fm["gnd_contacts"],
                    parallel_branch_series_ohm=round(parallel, 6),
                    common_forward_series_ohm=round(common_forward, 6),
                    source_current_A=round(i_source_total, 6),
                    source_drop_mV=round(source_drop * 1000, 4),
                    effective_forward_series_ohm=round(
                        common_forward + parallel, 6),
                    return_series_ohm=round(ret, 6),
                    return_current_A=round(i_return, 4),
                    delivered_at_400mA_min_V=round(
                        p3_pwm_heavy_lo - source_drop
                        - i3_budget * (common_forward + parallel)
                        - i_return * ret, 6))
            fully_mated["what"] = fm["what"]
            fully_mated["is_not_the_guarantee"] = (
                "the GUARANTEE is the worst unconditional mode -- either "
                "duplicated contact alone, one mated ground, both rails "
                "loaded.  This is what a socketed accessory actually gets and "
                "it is published beside it, not instead of it.")
    p3_modes.sort(key=lambda m: m["delivered_at_400mA_min_V"])
    worst_mode = p3_modes[0]
    best_mode = p3_modes[-1]
    worst_contact = worst_mode["contact"]
    p3_delivered_path_ohm = round(
        worst_mode["forward_series_ohm"]
        + worst_mode["return_series_ohm"] * worst_mode["return_current_A"]
        / worst_mode["forward_current_A"], 6)
    p3_delivered_min = worst_mode["delivered_at_400mA_min_V"]
    # D-789 / D788-02 + the memory of D-788's hand-aimed 2.95: the PUBLISHED
    # minimum is DERIVED from the worst permitted mode and rounded DOWN onto a
    # 10 mV grid.  It is not a number this file asserts and the derivation then
    # has to beat.
    p3_published_min = math.floor(p3_delivered_min * 100.0) / 100.0

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
        # D-789 / D788-02: every permitted wiring x load mode, worst first.
        delivery_modes=p3_modes,
        gnd_contact_modes=list(P3V3_DELIVERY["gnd_contact_modes"]),
        gnd_contact_modes_basis=P3V3_DELIVERY["gnd_contact_modes_basis"],
        return_load_modes_basis=P3V3_DELIVERY["return_load_modes_basis"],
        worst_mode=worst_mode,
        best_mode=best_mode,
        worst_contact=worst_contact,
        # D-789 / D788-01: the input the RON row is chosen at, and the row.
        # D-790 / D789-A03: at the WHOLE rail's current through the plane.
        source_current_A=round(i_source_total, 6),
        source_hot_ohm=round(source_hot, 6),
        source_drop_mV=round(source_drop * 1000, 4),
        source_carries_the_whole_rail=(
            "the U12-output-to-U20-input plane is shared with every internal "
            "+3V3 consumer, so it is charged I_INTERNAL + the accessory "
            "budget, once, and never inside a paralleled branch"),
        common_forward_series_ohm=round(common_forward, 6),
        u20_vin_V=round(u20_vin, 6),
        u20_ron_bound_ohm=round(p3_ron, 6),
        u20_ron_bound_basis=RON_TPS22950_BOUND_BASIS,
        u20_vin_is_in_the_published_range=u20_vin_is_in_the_published_range,
        delivered_path_bound_ohm=p3_delivered_path_ohm,
        delivered_at_400mA_min_V=round(p3_delivered_min, 6),
        delivered_at_400mA_full_header_V=round(
            best_mode["delivered_at_400mA_min_V"], 6),
        fully_mated_contract=fully_mated,
        delivered_at_400mA_fully_mated_V=(
            round(fully_mated["both_published_budgets"][
                "delivered_at_400mA_min_V"], 6) if fully_mated else None),
        published_connector_min_V=p3_published_min,
        published_connector_min_is_derived=True,
        published_connector_min_basis=(
            "the WORST of every permitted Community-Port wiring x load mode -- "
            "either duplicated +3V3 contact used alone, one mated ground "
            "contact, and the published 400 mA + 300 mA concurrent budget "
            "sharing that return -- rounded DOWN onto a 10 mV grid.  It is "
            "DERIVED; nothing in this file asserts it."),
        accessory_floor_V=ACC_3V3_ONBOARD_FLOOR_V,
        accessory_floor_basis=ACC_3V3_ONBOARD_FLOOR_BASIS,
        tightest_internal_consumer_max_V=ILI9488["vci_abs_max_V"],
        tightest_internal_consumer="the fitted ILI9488 panel: VCI and IOVCC "
                                   "absolute maximum -0.3..+3.3 V",
        delivered_min_ok=p3_delivered_min >= ACC_3V3_ONBOARD_FLOOR_V,
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
               "mated GND contacts, the ground-return copper and a process "
               "allowance -- and qualifies EACH duplicated contact alone.  "
               "D-789: RON is the guaranteed published maximum at the nearest "
               "row AT OR BELOW U20's OWN input voltage, with no interpolation "
               "and no curvature assumption, and the return is solved over "
               "every permitted ground-contact count with the ACC_5V current "
               "sharing it.")

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
        acc3v3_alone_at_its_budget=ibat(a3["published_budget_A"], 0.0),
        acc5v_alone_at_its_budget=ibat(0.0, a5["published_budget_A"]),
        both_at_the_declared_pair=ibat(DECLARED_DUAL_RAIL_BUDGET_A["ACC_3V3"],
                                       DECLARED_DUAL_RAIL_BUDGET_A["ACC_5V"]),
        acc3v3_alone_at_its_limiter=ibat(a3["ilim_max"], 0.0),
        acc5v_alone_at_its_limiter=ibat(0.0, a5["ilim_max"]),
        both_at_their_guaranteed_currents=ibat(a3["ilim_min"], a5["ilim_min"]),
        both_at_their_published_budgets=ibat(a3["published_budget_A"],
                                             a5["published_budget_A"]),
        both_limiters_in_fault=ibat(a3["ilim_max"], a5["ilim_max"]))
    # ---- D-791 / `R10-N02`, FOUND WHILE CLOSING D790-A04 -----------------
    #
    # THE SET WAS CALLED "REACHABLE" AND WHAT IT ACTUALLY MIXED WAS CONFORMING
    # ACCESSORIES WITH ACCESSORY OVERCURRENTS.
    #
    # D-771 put `acc3v3_alone_at_its_limiter` and `acc5v_alone_at_its_limiter`
    # in the same set as the two published-budget states and required all four
    # to stay under the FIRST protection threshold any unit can trip.  A state
    # "at its limiter" is one in which an accessory is pulling until U20 or U22
    # CURRENT-LIMITS -- for `ACC_5V` that is 0.6078 A against a published
    # 300 mA budget, more than twice it.  That is not a conforming accessory;
    # it is the protection working.
    #
    # It mattered the moment D790-A04 added the four loss terms D-790's
    # backlight model did not have.  `acc5v_alone_at_its_limiter` was 2.5546 A
    # and is now 2.5803 A, against an `IBAT_OCP` minimum of 2.5625 A -- so a
    # clause that had been passing by 7.9 mA now fails by 17.8 mA, on a state
    # that was never a conforming one.
    #
    # THE CLAUSE SPLITS RATHER THAN RELAXES, AND BOTH HALVES ARE STRICTER THAN
    # THE ONE THEY REPLACE WAS ABOUT ITS OWN SUBJECT:
    #
    #   * every state in which BOTH accessories CONFORM -- each rail at or
    #     under the budget the product publishes for it -- must stay under the
    #     first protection threshold ANY unit can trip.  No change, and it
    #     passes with 4.2 % to spare.
    #   * every ACCESSORY OVERCURRENT must land in the RECOVERABLE protection
    #     and BELOW the latching one: under the LTC4368 breaker's guaranteed
    #     minimum trip and under the F1 one-shot fuse, so what a user meets is
    #     a BQ25185 BATOCP hiccup that re-enables the BATFET after tREC_SC and
    #     not a latched board or a blown fuse.  The retry/latch semantics
    #     D-779 read out of SLUSF65B 6.3.7.3 are unchanged and are still a
    #     clause.
    #
    # WHAT IS NOT CLAIMED ANY MORE, STATED PLAINLY: that an accessory pulling
    # twice its published budget, while every internal subsystem runs at its
    # published maximum at once, cannot hiccup the charger.  On a unit whose
    # BATOCP sits at the bottom of its band, it can -- and that is the
    # protection acting on a non-conforming load, which is what it is for.
    # ---- D-792 / R11-04.  THE SIMULTANEOUS CONTRACT MOVED, SO THE SET DID.
    #
    # D-791's conforming set was "both rails at their guaranteed limiter
    # currents" and "both rails at their FULL published budgets".  Two Round-11
    # corrections make the second of those a state the network REFUSES: with
    # R11-07's itemised battery path and R11-02's ESP32-S3 baseline, the FULL
    # pair drawn simultaneously has NO operating point that survives the
    # firmware's own retention criterion at any attainable cell voltage.  F12
    # derives a DECLARED SIMULTANEOUS PAIR instead -- 220 mA + 170 mA -- and
    # that is the contract a conforming accessory obeys.  The per-rail budgets
    # are UNCHANGED and each is deliverable alone, so both single-rail cases are
    # in the conforming set at their FULL published budgets.
    #
    # THE FULL SIMULTANEOUS PAIR IS NOT DELETED; IT IS RECLASSIFIED, AND IT IS
    # STILL BOUND.  It moves to the overcurrent set, where it must land in the
    # RECOVERABLE protection -- below the latching LTC4368 breaker and below the
    # F1 one-shot fuse -- so an accessory pair that ignores the published
    # simultaneous contract meets a BQ25185 BATOCP hiccup and not a latched
    # board.  "Both at their guaranteed limiter currents" moves with it for the
    # same reason: 428 mA on the 3.3 V rail is ABOVE the 400 mA that rail
    # publishes, so it was never a conforming draw in the first place.
    CONFORMING = ("acc3v3_alone_at_its_budget",
                  "acc5v_alone_at_its_budget",
                  "both_at_the_declared_pair")
    ACCESSORY_OVERCURRENT = ("acc3v3_alone_at_its_limiter",
                             "acc5v_alone_at_its_limiter",
                             "both_at_their_guaranteed_currents",
                             "both_at_their_published_budgets",
                             "both_limiters_in_fault")
    REACHABLE = CONFORMING
    # D-771.  The floor a reachable state must stay under is the LOWEST trip
    # ANY protection in the chain can have on ANY unit -- not the charger's
    # alone.  With R75 at 15 mOhm that floor was the charger's 2.5625 A only
    # because the breaker's 2.640 A minimum was never computed.
    first_trip_min = min(IBAT_OCP_A[0], breaker["trip_min_A"])
    d.update(rails_A={k: {kk: (round(vv, 4) if isinstance(vv, float) else vv)
                          for kk, vv in v.items() if kk != "ref"}
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
    # Every state a USER can reach with CONFORMING accessories must stay under
    # the FIRST protection any unit can trip ...
    d["no_conforming_accessory_state_trips_the_pack"] = all(
        modes[k] < first_trip_min for k in CONFORMING)
    # ... and every ACCESSORY OVERCURRENT must land in the RECOVERABLE
    # protection rather than on the latching breaker or the one-shot fuse.
    d["every_accessory_overcurrent_lands_in_the_recoverable_protection"] = all(
        modes[k] < breaker["trip_min_A"] and modes[k] < FUSE_A
        for k in ACCESSORY_OVERCURRENT)
    d["accessory_overcurrent_states"] = {
        k: dict(battery_A=round(modes[k], 4),
                above_the_ibat_ocp_minimum=bool(modes[k] >= IBAT_OCP_MIN),
                below_the_ibat_ocp_maximum=bool(modes[k] < IBAT_OCP_A[2]),
                below_the_latching_breaker_minimum=bool(
                    modes[k] < breaker["trip_min_A"]),
                below_the_one_shot_fuse=bool(modes[k] < FUSE_A))
        for k in ACCESSORY_OVERCURRENT}
    d["conforming_and_overcurrent_sets"] = dict(
        conforming=list(CONFORMING), accessory_overcurrent=list(
            ACCESSORY_OVERCURRENT),
        why="D-791 / R10-N02: a state 'at its limiter' is an accessory pulling "
            "until U20 or U22 current-limits -- 0.6078 A against a published "
            "300 mA budget on ACC_5V.  Calling that user-reachable-and-"
            "conforming was what let one clause answer two different "
            "questions.")
    # Retained under its historical name so a reader diffing this report can
    # see exactly what moved, and REPORTED rather than ruled on.
    d["no_reachable_state_trips_the_pack_historical_definition"] = dict(
        included_accessory_overcurrents=True,
        value=all(modes[k] < first_trip_min
                  for k in ("acc3v3_alone_at_its_limiter",
                            "acc5v_alone_at_its_limiter") + CONFORMING),
        why="the D-771..D-790 definition, kept visible.  It is False on this "
            "candidate at acc5v_alone_at_its_limiter = %.4f A against an "
            "IBAT_OCP minimum of %.4f A." % (
                modes["acc5v_alone_at_its_limiter"], IBAT_OCP_MIN))
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
    d["published_rail_budget_A"] = dict(published_budget)
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
    # D-791 / D790-A10.  THE ORDERING IS ASKED AT BOTH BANDS.
    #
    # The clause that matters is that the RECOVERABLE protection (BQ25185
    # BATOCP, which hiccups and retries) fires BEFORE the LATCHING one (the
    # LTC4368 breaker) on every unit, so a user meets a 250 ms interruption
    # and not a board that has to be power-cycled.  It is judged on the band TI
    # STATES -- widening a band moves BOTH ends, and using a wider MAXIMUM here
    # would be arguing that the recoverable protection fires LATER than TI says
    # it can, which is not the conservative direction for an ORDERING question.
    # The DECLARED WIDER band D790-A10 asks for is reported beside it so the
    # size of the dependency is visible, and the ordering survives it.
    d["recoverable_trip_is_ordered_below_the_latching_breaker"] = (
        IBAT_OCP_A[2] < breaker["trip_min_A"])
    d["ordering_margin_pct"] = round(
        (breaker["trip_min_A"] - IBAT_OCP_A[2]) / breaker["trip_min_A"] * 100.0, 2)
    _assumed_hi = IBAT_OCP_TYP_A * (1.0 + IBAT_OCP_ASSUMED_ACCURACY)
    d["protection_ordering_at_both_bands"] = dict(
        stated_band_A=[round(IBAT_OCP_A[0], 4), IBAT_OCP_TYP_A,
                       round(IBAT_OCP_A[2], 4)],
        stated_accuracy=IBAT_OCP_STATED_ACCURACY,
        assumed_band_A=[round(IBAT_OCP_ASSUMED_MIN_A, 4), IBAT_OCP_TYP_A,
                        round(_assumed_hi, 4)],
        assumed_accuracy=IBAT_OCP_ASSUMED_ACCURACY,
        latching_breaker_min_A=round(breaker["trip_min_A"], 4),
        ordered_at_the_stated_band=bool(IBAT_OCP_A[2] < breaker["trip_min_A"]),
        ordered_at_the_declared_wider_band=bool(
            _assumed_hi < breaker["trip_min_A"]),
        ordering_margin_at_the_wider_band_pct=round(
            (breaker["trip_min_A"] - _assumed_hi) / breaker["trip_min_A"]
            * 100.0, 2),
        condition_source=IBAT_OCP_CONDITION_SOURCE,
        why="D790-A10: TI publishes IBAT_OCP as a TYPICAL at VBAT = 4 V with "
            "no MIN/MAX column and its 18 % accuracy at IBAT = 3.125 A, "
            "TJ = 27 C only.  The SUSTAINED envelope F12 rules on uses the "
            "declared wider band; the fault ORDERING uses the stated one, for "
            "the reason above, and is shown to survive the wider one anyway.")
    d["protection_ordering_survives_the_declared_wider_band"] = bool(
        d["protection_ordering_at_both_bands"][
            "ordered_at_the_declared_wider_band"])
    # ---- D-771 CLAUSE 3: the converters can source what the limiters allow --
    # The CONFORMING worst case and the FAULT coincidence, separately.
    u12_conforming = I_INTERNAL + a3["published_budget_A"]
    u12_load = I_INTERNAL + a3["ilim_max"]
    # U12's own switch-current bound at the cell corner, by the same method
    # this contract already applies to U21.
    u12_duty = 1.0 - (VBAT_CORNER * ETA_U12 / V_3V3)
    u12_ripple = (VBAT_CORNER * u12_duty) / (U12_L_H * (1 - U12_L_TOL)
                                             * U12_FSW_MIN_HZ)
    u12_switch_limited = (1.0 - u12_duty) * (U12_ISW_MIN_A - u12_ripple / 2.0)
    # TPS61023 SLVSF14B equation 1, at the cell corner, with the inductor at
    # its unlucky -20 % corner (larger ripple) and the valley limit at its MIN.
    duty = 1.0 - (VBAT_CORNER * ETA_U21 / V_ACC5V)
    d_ripple = (VBAT_CORNER * duty) / (U21_L_H * (1 - U21_L_TOL) * U21_FSW_HZ)
    u21_capability = (1.0 - duty) * (U21_ILIM_VALLEY_MIN - d_ripple / 2.0)
    d["converter_capability_A"] = dict(
        u12_part="TPS63020", u12_rated_A=U12_IOUT_A,
        u12_vin_floor_V=U12_VIN_FLOOR, u12_worst_case_load_A=round(u12_load, 4),
        u12_conforming_worst_case_A=round(u12_conforming, 4),
        u12_conforming_is_inside_the_guaranteed_output=bool(
            u12_conforming <= U12_IOUT_A),
        u12_fault_coincidence_A=round(u12_load, 4),
        u12_fault_coincidence_exceeds_the_guaranteed_output=bool(
            u12_load > U12_IOUT_A),
        u12_duty=round(u12_duty, 4),
        u12_ripple_A=round(u12_ripple, 4),
        u12_switch_limited_capability_A=round(u12_switch_limited, 4),
        u12_fault_coincidence_is_inside_the_devices_own_limit=bool(
            u12_load <= u12_switch_limited),
        u12_limit_source=U12_LIMIT_SOURCE,
        u12_what_the_fault_coincidence_means=(
            "`ilim_max` is the current a SHORTED accessory draws before U20's "
            "limiter removes it, not a conforming load.  Coinciding it with "
            "the internal PEAK envelope is a fault excursion: it is outside "
            "TI's 2 A Features figure and inside the device's own average "
            "switch current limit at this cell corner, so U12 does not enter "
            "current limit and the rail does not collapse.  What clears the "
            "excursion is U20, whose own limit is what `ilim_max` IS."),
        u12_ok=(VBAT_CORNER > U12_VIN_FLOOR
                and u12_conforming <= U12_IOUT_A
                and u12_load <= u12_switch_limited),
        u21_part="TPS61023", u21_duty=round(duty, 4),
        u21_ripple_A=round(d_ripple, 4),
        u21_capability_A=round(u21_capability, 4),
        u21_worst_case_load_A=round(a5["ilim_max"], 4),
        u21_ok=a5["ilim_max"] <= u21_capability,
        method="U12 from SLVSAA7's own Features figure at VIN > 2.5 V; U21 "
               "from SLVSF14B equation 1 with ILIM_SW at its EC MINIMUM and "
               "L4 at its -20 % corner")
    # ---- D-792 / R11-06 + CONVERGENCE REQUIREMENT 5.  EVERY ENGINEERING
    # INPUT CARRIES A MACHINE-READABLE PROVENANCE TAG, AND A TYPICAL MAY NOT
    # RULE.
    #
    # ROUND-11, IN ITS OWN WORDS: "Tag source values as guaranteed / max /
    # typical / declared estimate.  Do not allow a typical/interpolated value to
    # masquerade as a guaranteed bound."
    #
    # THE PROBLEM IS REAL AND THIS PROGRAMME HAS HIT IT THREE TIMES.  D-789
    # found the LTC4368's 50 mV and the TPS61023's 0.6 V VREF being used as
    # limits when both are TYPICALS; D-790 found `VBUVLO` and `IBAT_OCP` being
    # ruled on at typicals with no MIN/MAX column; R11-10 found the backlight
    # inductor's DCR taken at 52.2 mOhm typical when the manufacturer publishes
    # a 57.4 mOhm MAXIMUM.  Each was caught by a human reading a datasheet.
    # `aqroot_power_model.tag()` attaches provenance to a value at the point of
    # definition and `audit_tags()` REFUSES a release in which a value tagged
    # TYPICAL is used where a bound is required -- so the fourth instance is
    # caught by a gate instead of by a reviewer.
    _tags = apm.audit_tags()
    d["engineering_input_provenance"] = dict(
        _tags, registry=apm.registry(),
        ruling_tags=list(apm.RULING_TAGS),
        why="a TYPICAL may be REPORTED and may SEED a declared widening; it "
            "may never BE the bound.  A DECLARED_ESTIMATE may rule, because it "
            "carries a stated basis, a widening factor and a first-article "
            "measurement of record -- which is what makes it an engineering "
            "allowance rather than a guess.")
    d["no_typical_is_used_as_a_ruling_bound"] = bool(
        not _tags["invalid_ruling_use"])
    d["every_ruling_input_carries_a_provenance_tag"] = bool(
        _tags["ruling_entries"] > 0
        and all(r["tag"] in apm.TAGS for r in apm.registry()))
    # ...and the rule is proved to REFUSE, over a deliberately poisoned copy of
    # the same registry, so the tagging is mechanical rather than decorative.
    _poisoned = apm.registry() + [dict(
        key="control.a_typical_used_as_a_bound", value=1.0, tag=apm.TYPICAL,
        source="NEGATIVE CONTROL", condition=None,
        measurement_of_record=None, widened_from=None,
        used_as_a_ruling_bound=True)]
    d["the_provenance_rule_refuses_a_typical_bound"] = bool(
        apm.audit_tags(_poisoned)["invalid_ruling_use"])

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
            both_at_the_declared_pair=(
                DECLARED_DUAL_RAIL_BUDGET_A["ACC_3V3"],
                DECLARED_DUAL_RAIL_BUDGET_A["ACC_5V"]),
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
    # D-791 / D790-A11.  U22's 54 mOhm ROW BELONGS TO VIN = 5 V AND ITS INPUT
    # IS NOT 5 V.
    #
    # `U22`'s input is `ACC_5V_RAW`, the `TPS61023` boost's own output, and the
    # boost's setpoint is a BAND: its LOW end is the one that matters for a
    # resistance that falls with VIN.  D-790 used the 5 V row anyway, which is
    # the same defect D-788 corrected on `U20` (`R7-D787-02`) and D-789
    # corrected on the LTC4368 gate drive -- a guaranteed row read at a
    # condition the design does not sit at.  The bound is the same monotone
    # rule the rest of this file uses: the published maximum at the nearest row
    # AT OR BELOW the actual input, which for a boost low end of about 4.74 V
    # is the 3.3 V row's 68 mOhm.  The 54 mOhm figure is REPORTED beside it as
    # the expected value it always was.
    u22_vin_min = v5[0]
    ron_a5 = tps22950_ron_max(u22_vin_min)
    u22_vin_is_in_the_published_range = ron_a5 is not None
    if ron_a5 is None:
        ron_a5 = RON_TPS22950_MAX[RON_TPS22950_MIN_VIN]

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

    i3_dual = DECLARED_DUAL_RAIL_BUDGET_A["ACC_3V3"]
    i5_dual = DECLARED_DUAL_RAIL_BUDGET_A["ACC_5V"]
    # D-792 / R11-04: the SIMULTANEOUS case is the DECLARED PAIR.  The FULL
    # pair is retained below as a reported negative control, exactly as F12
    # retains it in its own concurrency table.
    LOADS = (("acc3v3_published", i3_pub, 0.0),
             ("acc5v_published", 0.0, i5_pub),
             ("both_declared_pair", i3_dual, i5_dual))
    bases, requirement = {}, {}
    # D-791 / D790-A10.  THE OCP MINIMUM THE *FLOOR* IS COORDINATED WITH IS
    # THE DECLARED WIDER BAND, not the one TI states at a single current and
    # junction temperature.  The fault screens above keep the stated band, for
    # the reason recorded at IBAT_OCP_CONDITION_SOURCE: widening a band moves
    # BOTH ends and is not conservative in both directions at once.
    ocp_for_floors = IBAT_OCP_ASSUMED_MIN_A
    for basis, ohms in (("live", live_ohms), ("path_bound", bound_ohms)):
        m = _model(ohms)

        def _req(i3, i5, margin, iint, ocp=ocp_for_floors):
            target = ocp * (1.0 - margin)
            lo, hi = 2.5, 4.4
            for _ in range(200):
                mid = 0.5 * (lo + hi)
                if battery_current(m, mid, i3, i5, iint=iint)[0] > target:
                    lo = mid
                else:
                    hi = mid
            return hi

        single = max(_req(i3, i5, NORMAL_OCP_MARGIN_MIN, sustained_internal_A)
                     for name, i3, i5 in LOADS
                     if name != "both_declared_pair")
        dual = _req(i3_dual, i5_dual, NORMAL_OCP_MARGIN_MIN,
                    sustained_internal_A)
        bases[basis] = dict(
            series_ohm={k: round(v, 6) for k, v in m.items()},
            sustained_internal_3v3_A=sustained_internal_A,
            ocp_min_used_A=round(ocp_for_floors, 6),
            required_single_rail_floor_V=round(single, 4),
            required_dual_rail_floor_V=round(dual, 4),
            zero_margin_single_rail_floor_V=round(
                max(_req(i3, i5, 0.0, sustained_internal_A)
                    for name, i3, i5 in LOADS
                    if name != "both_declared_pair"), 4),
            zero_margin_dual_rail_floor_V=round(
                _req(i3_dual, i5_dual, 0.0, sustained_internal_A), 4),
            # RETAINED AND LABELLED: what the PEAK +3V3 envelope would need at
            # this node.  F12 proves the node cannot be there, which is why it
            # is reported rather than enforced.
            peak_envelope_single_rail_floor_V=round(
                max(_req(i3, i5, NORMAL_OCP_MARGIN_MIN, I_INTERNAL)
                    for name, i3, i5 in LOADS
                    if name != "both_declared_pair"), 4),
            peak_envelope_dual_rail_floor_V=round(
                _req(i3_dual, i5_dual, NORMAL_OCP_MARGIN_MIN,
                     I_INTERNAL), 4),
            peak_envelope_floor_is_reported_not_enforced=(
                "the node voltage the PEAK +3V3 envelope would need to stay "
                "inside the OCP margin.  D-790 enforced it as the firmware "
                "floor; D790-A03 shows the node cannot reach it at any "
                "attainable cell voltage, and D-790's own section 4 shows the "
                "peak envelope is not a steady state.  F12 rules."))
        requirement[basis] = (single, dual)
    # THE FIRMWARE MUST SATISFY THE WORSE OF THE TWO BASES.
    req_single = max(v[0] for v in requirement.values())
    req_dual = max(v[1] for v in requirement.values())
    req_single_grid, req_dual_grid = grid_up(req_single), grid_up(req_dual)

    # The cases are reported on the LIVE basis at the floors firmware enforces.
    m_live = _model(live_ohms)
    normal_cases = {}
    for name, i3, i5 in LOADS:
        # D-791 / D790-A03: a RETENTION state is judged at the RETENTION
        # floor.  Judging it at an ENABLE floor asks what the current would be
        # at a node voltage the state has already left, which is how D-790's
        # floors came to describe a node the board never occupies.
        floor = retention_floor
        current, vsys, p = battery_current(m_live, floor, i3, i5,
                                           iint=sustained_internal_A)
        margin = ((ocp_for_floors - current) / ocp_for_floors
                  if current != float("inf") else -float("inf"))
        normal_cases[name] = dict(
            vcell_floor_V=round(floor, 4), delivered_W=round(p, 4),
            internal_3v3_A=sustained_internal_A,
            ocp_min_used_A=round(ocp_for_floors, 6),
            sys_V_at_the_floor=round(vsys, 4), battery_A=round(current, 4),
            sys_V_is_inside_u12s_published_vin_floor=bool(
                vsys >= U12_VIN_FLOOR),
            margin_to_ibat_ocp_min_pct=round(margin * 100.0, 2),
            margin_at_least_the_convention=margin >= NORMAL_OCP_MARGIN_MIN)

    be_margin = breakeven_bat_ohm(m_live, retention_floor, i3_pub, i5_pub,
                                  NORMAL_OCP_MARGIN_MIN)
    be_trip = breakeven_bat_ohm(m_live, retention_floor, i3_pub, i5_pub, 0.0)
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
            "BOTH are the guaranteed TPS22950-Q1 maximum at the nearest "
            "published row AT OR BELOW that switch's OWN input voltage -- the "
            "monotone bound RON_TPS22950_BOUND_BASIS states, with no "
            "interpolation and no curvature assumption.  ACC_3V3's switch sees "
            "the +3V3 plane at this rail's heavy-load minimum less the source "
            "drop, which selects the 1.8 V row's 116 mOhm.  ACC_5V's switch "
            "sees the TPS61023 boost's own LOW setpoint corner, which selects "
            "the 3.3 V row's 68 mOhm.  *(D-791 / D790-A11: this sentence used "
            "to say ACC_3V3's bound was INTERPOLATED between two rows -- which "
            "D-788 / D788-01 had already overturned -- and that ACC_5V 'never "
            "falls below the 3.3 V condition, so its 54 mOhm row applies "
            "directly'.  The 54 mOhm row is the VIN = 5 V row and the boost's "
            "low corner is about 4.74 V, so it did not apply.)*"),
        acc_5v_switch_input_V=round(u22_vin_min, 6),
        acc_5v_switch_row_is_inside_the_published_range=bool(
            u22_vin_is_in_the_published_range),
        acc_5v_switch_expected_5V_row_ohm=ACC_SWITCH_RON_OHM["ACC_5V"],
        # D-791 / D790-A03: the two rail voltages F12 must solve the network
        # with, published here so the two clauses cannot describe different
        # boards.
        v_3v3_used_V=round(V_3V3, 6),
        v_acc5v_used_V=round(V_ACC5V, 6),
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
        ("both_declared_pair_full_internal", i3_dual, i5_dual, I_INTERNAL,
         "dual"),
        # RETAINED as a reported negative reference: the FULL pair, which the
        # D-792 network refuses, is what the legacy 2 A JST-PH comparison below
        # is made against.
        ("both_published_full_internal", i3_pub, i5_pub, I_INTERNAL, "dual"))
    conn_cases, conn_within = {}, (rating is not None)
    for basis, ohms in (("live", live_ohms), ("path_bound", bound_ohms)):
        m = _model(ohms); rows = {}
        for name, i3, i5, iint, which in PERMITTED:
            floor = dual_floor if which == "dual" else single_floor
            cur = battery_current(m, floor, i3, i5, iint=iint)[0]
            inside = bool(rating is not None and cur <= rating + 1e-9)
            # The FULL pair is a REPORTED negative reference, not a permitted
            # state: F12 refuses it and the published simultaneous contract is
            # the declared pair.  It does not gate the connector verdict.
            if name != "both_published_full_internal":
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
        req=_required_internal(m,dual_floor,i3_dual,i5_dual,rating) if rating else float("nan")
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

    # D-791 / D790-A03.  THE FLOOR THAT HAS TO MEET THE OCP REQUIREMENT IS THE
    # RETENTION FLOOR, because it is the one compared against a node that is
    # already carrying the load.  The two ENABLE floors are above it by
    # construction -- each is the retention floor plus the step its own rail
    # will cause -- and the ordering is asserted rather than assumed.
    # D-792 / R11-04: the two ENABLE numbers are now the published ENVELOPE of
    # a TABLE, and the dual envelope may legitimately EQUAL the single one --
    # the dual case is the DERATED pair, which is a lighter load than one rail
    # at its full published budget, so nothing forces it strictly higher.  What
    # must still hold is that neither is below the retention floor and that the
    # retention floor satisfies the OCP coordination requirement derived here.
    d["firmware_floors_meet_the_derived_requirement"] = bool(
        retention_floor >= req_single_grid - 1e-9
        and retention_floor >= req_dual_grid - 1e-9
        and single_floor > retention_floor
        and dual_floor >= single_floor)
    d["normal_operation"]["firmware_retention_floor_V"] = retention_floor
    d["normal_operation"]["floor_roles"] = (
        "retention: the node is already carrying the load.  single/dual "
        "ENABLE: the node is not yet carrying the rail being switched on, so "
        "each anticipates that rail's own node step (D-779, quantified by "
        "F12).  All three are DERIVED by F12; F6 checks that the retention "
        "floor also satisfies the OCP coordination requirement it derives "
        "here, and that the ordering retention < single < dual holds.")
    d["accessory_switch_rons_are_read_at_their_own_input"] = bool(
        u20_vin_is_in_the_published_range and u22_vin_is_in_the_published_range
        and abs(ron_a3 - tps22950_ron_max(u20_vin)) < 1e-12
        and abs(ron_a5 - tps22950_ron_max(u22_vin_min)) < 1e-12)
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
    ok = (d["no_conforming_accessory_state_trips_the_pack"]
          and d["every_accessory_overcurrent_lands_in_the_recoverable_protection"]
          and d["double_fault_stays_inside_the_protection_chain"]
          and d["limiter_silicon_is_a_part_with_a_published_range"]
          and d["ilim_setting_is_inside_the_parts_own_spec_range"]
          and d["one_limiter_mpn_on_both_rails"]
          and d["ilim_band_is_inside_ul2367_recognition"]
          and d["each_rail_guarantees_its_published_accessory_budget"]
          and d["recoverable_trip_is_ordered_below_the_latching_breaker"]
          and d["protection_ordering_survives_the_declared_wider_band"]
          and d["converters_can_source_their_worst_case_rail"]
          and d["no_typical_is_used_as_a_ruling_bound"]
          and d["every_ruling_input_carries_a_provenance_tag"]
          and d["the_provenance_rule_refuses_a_typical_bound"]
          and d["p3v3_divider_parts_have_a_published_temperature_coefficient"]
          and d["p3v3_reinforcement_is_exact_and_bounded"]
          and d["p3v3_delivers_the_published_connector_minimum"]
          and d["p3v3_stays_below_the_tightest_internal_consumer_maximum"]
          and d["boost_setpoint_is_clear_of_its_own_ovp"]
          and d["published_normal_load_respects_vcell_policy"]
          and d["accessory_switch_rons_are_read_at_their_own_input"]
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



# --------------------------------------------------------------------------
# F10 -- THE BATTERY PASS PAIR, SOLVED FOR THE PART THIS BOARD NOW FITS.
#
# ADDED AT D-789 as a BLOCK; REBUILT AT D-790 / D789-A01 as a PROOF.
#
# WHAT D-789 FOUND (`R8-N01`) AND COULD NOT FIX.  The LTC4368 guarantees
# `dVGATE = GATE - VOUT >= 3.0 V` at its lowest published row, `VIN = 2.5 V`,
# with no guaranteed row again until `VIN = 5 V`; this board's `BAT_RAW` lives
# between them, so under the same nearest-row-at-or-below discipline F6 applies
# to `U20`'s RON, 3.0 V is the bound.  The pass pair is FOUR channels in series
# --
#
#   BAT_RAW -[Q2 ch]- Q2_CS -[Q2 ch]- BAT_MID -[Q3 ch]- Q3_CS -[Q3 ch]-
#   BAT_SENSE -[R75]- BAT_PROTECTED_P (= the LTC4368's own VOUT)
#
# -- with BOTH gates of each package on `LTC_GATE` and BOTH sources of each
# package tied, so each package has ONE `VGS`:
#
#   VGS(Q3) = dVGATE - I x (1 x RDS(on) + R75)
#   VGS(Q2) = dVGATE - I x (3 x RDS(on) + R75)
#
# `Q2` is the worse of the two and its worst-case `VGS` is about 2.6-2.8 V.
# The fitted onsemi `NTMD4820N`'s `VGS(th)` MAXIMUM is **3.0 V** and its lowest
# published conduction row is `VGS = 4.5 V`.  So a worst-corner part was not
# guaranteed to be ENHANCED AT ALL -- at `VGS(th)` it passes the 250 uA of its
# own threshold test where this path needs amps -- and there was no bound at
# any gate drive this circuit can produce.  D-789 recorded that and blocked.
#
# D-790 SELECTS THE PART INSTEAD, AND THE SEARCH IS WRITTEN DOWN.  Every
# Alpha & Omega SOIC-8 dual N-channel datasheet was read from the manufacturer
# (150 part numbers, `AO4600`-`AO4898`); exactly TWO publish an `RDS(on)` row
# at `VGS <= 2.5 V`.  `AO4806`'s 22 mOhm row would be better still but the part
# reads stock 0 on the live record and its manufacturer flags it common-drain,
# which this common-SOURCE circuit cannot take on trust.  **`AO4800` is the
# selection**: same SOIC-8 land, same pin function map, `VGS(th)` 0.7 / 1.1 /
# **1.5 V MAX**, and `RDS(on) <= 50 mOhm AT VGS = 2.5 V` -- a GUARANTEED number
# at the gate drive this circuit actually has.  Genuine AOS line, LCSC
# `C17098`, live stock 5347.
#
# AND FABLE'S `AO4800` IS NOT APPROVED ON FABLE'S SAY-SO.  Astra warned that
# the four-channel path may eat too much single-cell headroom, and this file
# reproduces that: solved self-consistently -- the channel resistance sets the
# source offsets, the offsets set `VGS`, `VGS` selects the conduction row, the
# dissipation sets the junction temperature and the junction temperature moves
# the resistance again -- `AO4800` at the PEAK design current and the 40 C top
# of the ambient envelope lands at `VGS(Q2) = 2.49 V`, just UNDER its own
# 2.5 V row.  It closes at the SUSTAINED THERMAL ENVELOPE, which is the
# envelope `D789-A02` establishes is the right one for a steady-state
# question, and this clause rules there and reports the peak beside it.
#
# WHAT IS PROVEN, AND WHAT IS STILL A DECLARED ALLOWANCE.
#   * ENHANCEMENT is GUARANTEED: `VGS(Q2)` clears `VGS(th)` MAX by over a volt
#     at every current in the envelope.  This is the half that decides whether
#     the board runs from its battery at all, and it is now a datasheet fact.
#   * CONDUCTION at 25 C is GUARANTEED by the 2.5 V row.
#   * CONDUCTION AT TEMPERATURE is NOT published at `VGS = 2.5 V` by AOS or by
#     any candidate found; the model carries the datasheet's OWN 25 -> 125 C
#     ratio from its `VGS = 10 V` row (27 -> 40 mOhm) as a DECLARED allowance
#     and says so.  `C-BAT-GATE-01` first-article measurement is the
#     measurement of record.
#   * `VGS` MAXIMUM: the part is +/-12 V and the LTC4368's own maximum at the
#     row AT OR ABOVE this board's `BAT_RAW` maximum -- the `VIN = 5 V` row --
#     is 10.8 V.  Inside, on two published numbers, and checked here.
LTC4368_GATE_DRIVE_ROWS_V = apm.LTC4368_GATE_DRIVE_ROWS_V
LTC4368_GATE_DRIVE_MAX_ROWS_V = apm.LTC4368_GATE_DRIVE_MAX_ROWS_V
LTC4368_GATE_SOURCE = apm.LTC4368_GATE_SOURCE
BAT_RAW_MAX_V = apm.BAT_RAW_MAX_V
PASS_PAIR = apm.PASS_PAIR
PASS_PAIR_LEDGER_TOKENS = (
    "AO4800",
    "C17098",
    "C-BAT-GATE-01",
    "RETIRED",
    "NTMD4820NR2G",
    "dual N-channel in the SOIC-8 dual-MOSFET pinout",
    "live authorised stock ≥ **100**",
)
# The AOS part's marketplace re-marks, which purchasing may NOT substitute.
PASS_PAIR_REFUSED_SOURCES = ("VBsemi", "HXY", "UMW", "JSMSEMI", "MSKSEMI",
                             "TECH PUBLIC")
ltc4368_gate_drive_min_V = apm.ltc4368_gate_drive_min_V
ltc4368_gate_drive_max_V = apm.ltc4368_gate_drive_max_V


def judge_pass_pair_gate(design_amps, vin_min_V, spec=None, rows=None,
                         ambient_C=None, internal_air_C=None,
                         sustained_amps=None, ruling_ratio=None):
    """D-792 / R11-01.  The four-channel model, solved self-consistently, with
    the TEMPERATURE LAW AS AN EXPLICIT SOLVER INPUT.

    Pure.  `aqroot_power_model.solve_pass_pair` takes the 25 -> 125 C
    resistance ratio as an ARGUMENT, so every corner this clause advertises
    actually moves the arithmetic.  D-791's version captured the coefficient
    before the sensitivity could change it and printed three identical cases.
    """
    spec = PASS_PAIR if spec is None else spec
    drive = ltc4368_gate_drive_min_V(vin_min_V, rows)
    drive_max = ltc4368_gate_drive_max_V(BAT_RAW_MAX_V)
    ruling_ratio = (spec["rds_on_hot_ratio"] if ruling_ratio is None
                    else ruling_ratio)
    r25 = spec["rds_on_max_at_that_row_ohm"]
    out = dict(
        references=list(spec["references"]), locked_mpn=spec["locked_mpn"],
        locked_lcsc=spec.get("locked_lcsc"),
        locked_manufacturer=spec.get("locked_manufacturer"),
        retired_mpn=spec.get("retired_mpn"),
        design_amps=design_amps, bat_raw_min_V=vin_min_V,
        bat_raw_max_V=BAT_RAW_MAX_V,
        gate_drive_rows_V=dict(rows or LTC4368_GATE_DRIVE_ROWS_V),
        gate_drive_max_rows_V=dict(LTC4368_GATE_DRIVE_MAX_ROWS_V),
        gate_drive_source=LTC4368_GATE_SOURCE,
        guaranteed_gate_drive_V=drive,
        guaranteed_gate_drive_max_V=drive_max,
        fet_source=spec["source"],
        vgs_th_max_V=spec["vgs_th_max_V"],
        vgs_abs_max_V=spec["vgs_abs_max_V"],
        rds_on_lowest_published_vgs_V=spec["rds_on_lowest_published_vgs_V"],
        rds_on_max_at_that_row_ohm=r25,
        rds_on_hot_ratio=round(ruling_ratio, 6),
        rds_on_hot_ratio_published=spec["rds_on_hot_ratio_published"],
        rds_on_hot_ratio_basis=spec["rds_on_hot_ratio_basis"],
        refused_marketplace_sources=list(PASS_PAIR_REFUSED_SOURCES),
        topology=("BAT_RAW -[Q2]- Q2_CS -[Q2]- BAT_MID -[Q3]- Q3_CS -[Q3]- "
                  "BAT_SENSE -[R75]- BAT_PROTECTED_P, which is the LTC4368's "
                  "own VOUT.  Both gates of each package are on LTC_GATE and "
                  "both sources are tied, so each package has ONE VGS: Q3's "
                  "source is one channel plus R75 above VOUT and Q2's is "
                  "three."))
    if drive is None:
        out.update(ok=False, why="BAT_RAW is below the lowest published "
                                 "LTC4368 gate-drive row; nothing bounds it")
        return False, out

    air_peak = 40.0 if internal_air_C is None else internal_air_C

    def solve(amps, air_C, ratio=None):
        return apm.solve_pass_pair(amps, air_C,
                                   ruling_ratio if ratio is None else ratio,
                                   spec, drive)

    out["peak_case"] = solve(design_amps, air_peak)
    if sustained_amps is not None:
        out["sustained_case"] = solve(sustained_amps, air_peak)
    ruling = out.get("sustained_case") or out["peak_case"]
    out["ruling_case"] = ("sustained" if "sustained_case" in out else "peak")
    out["ruling"] = ruling
    _rule_amps = sustained_amps if sustained_amps is not None else design_amps

    # ---- D-791 / D790-A01.  THE CURRENT AT WHICH THE CONDUCTION ROW RUNS OUT.
    ceiling = apm.conduction_ceiling_A(air_peak, drive, ruling_ratio, spec)
    out["guaranteed_conduction_ceiling_A"] = round(ceiling, 6)
    out["guaranteed_conduction_ceiling"] = dict(
        internal_air_C=round(air_peak, 3),
        lowest_published_row_V=spec["rds_on_lowest_published_vgs_V"],
        hot_ratio_used=round(ruling_ratio, 6),
        ceiling_A=round(ceiling, 6),
        sustained_envelope_A=sustained_amps,
        peak_envelope_A=design_amps,
        sustained_is_inside_the_ceiling=bool(
            sustained_amps is not None and sustained_amps <= ceiling + 1e-9),
        peak_is_inside_the_ceiling=bool(design_amps <= ceiling + 1e-9),
        what_lies_above_it=(
            "the part is still ENHANCED there -- VGS clears the AO4800's "
            "1.5 V VGS(th) MAXIMUM by more than a volt at every current in "
            "this envelope -- but AOS publishes no RDS(on) row below "
            "VGS = 2.5 V, so the resistance is not a guaranteed number.  The "
            "consequence of an unpublished higher resistance is more DROP and "
            "more HEAT, both of which are self-limiting (more drop is less "
            "current) and both of which sit inside a protection chain that "
            "does not depend on how well the pair conducts: the LTC4368 "
            "senses across R75 and pulls the gate DOWN, and the BQ25185's "
            "BATOCP hiccups the BATFET.  It is therefore a PROTECTION-DOMAIN "
            "excursion and not an operating state, and this contract does not "
            "rule there."),
        bounded_duration_basis=(
            "AOS Rev 6.1 Thermal Characteristics publishes TWO junction-to-"
            "ambient figures: 62.5 C/W MAX for t <= 10 s and 90 C/W MAX at "
            "steady state.  A transient above the ceiling is therefore bounded "
            "by the 10 s row -- the only transient thermal number AOS states "
            "numerically; Figure 12's normalised ZthetaJA curve is a graph "
            "this repository cannot read.  The peak electrical envelope is a "
            "short-time-constant question (ampacity, protection ordering, the "
            "J4 connector rating) and is treated as one."),
        theta_ja_10s_C_per_W=spec["theta_ja_10s_C_per_W"],
        theta_ja_steady_C_per_W=spec["theta_ja_steady_C_per_W"])

    # ======================================================================
    # D-792 / R11-01.  THE SENSITIVITY THAT USED TO BE INERT, AND THE THREE
    # THINGS IT NOW HAS TO DO.
    #
    #   1  MOVE.  Each corner is solved with the ratio PASSED IN, and the
    #      clause asserts the answers are DISTINCT and ORDERED -- a higher
    #      coefficient must give a higher channel resistance, a hotter
    #      junction and a SMALLER VGS.  D-791's three cases were byte-
    #      identical and nothing could see it.
    #   2  CROSS.  The clause derives the ratio at which the ruling case
    #      falls to the AO4800's lowest published conduction row, so the
    #      distance between the declared coefficient and the cliff is a
    #      NUMBER.  A control that only asserts "it still passes" cannot
    #      distinguish a 1 % margin from a 100 % one.
    #   3  RULE.  The verdict is taken at the DECLARED RULING RATIO, which is
    #      the published 1.4815 widened to 1.60, and that Boolean is a term
    #      of `ok`.  D-791's pessimistic Boolean was not.
    #
    # THE 2x CASE ASTRA REPRODUCED IS KEPT AND REPORTED, AND IT IS HONEST
    # ABOUT WHAT IT IS.  At a 25 -> 125 C ratio of 2.0 the ruling case does
    # NOT hold the conduction row -- that is Astra's 2.461 V, and with the
    # correct solver this file reproduces it instead of hiding it.  2.0 is the
    # coefficient of a drift-limited high-voltage MOSFET, where RDS(on)
    # follows the bulk mobility as T^2.4; it is not the coefficient of a 30 V
    # trench part, and AOS MEASURES 1.4815 on this die.  The ruling bound is
    # 1.60 and the crossing ratio is published beside it.
    # ======================================================================
    cases = {}
    for name, ratio in (("at_no_temperature_coefficient", 1.0),
                        ("at_the_published_ratio",
                         spec["rds_on_hot_ratio_published"]),
                        ("at_the_declared_ruling_ratio", ruling_ratio),
                        ("at_a_pessimistic_2x_ratio", 2.0)):
        cases[name] = solve(_rule_amps, air_peak, ratio)
    order = [cases["at_no_temperature_coefficient"],
             cases["at_the_published_ratio"],
             cases["at_the_declared_ruling_ratio"],
             cases["at_a_pessimistic_2x_ratio"]]
    crossing = apm.hot_ratio_at_which_the_row_is_lost(
        _rule_amps, air_peak, drive, spec)
    out["hot_ratio_sensitivity"] = dict(
        published_ratio=round(spec["rds_on_hot_ratio_published"], 6),
        declared_ruling_ratio=round(ruling_ratio, 6),
        basis=spec["rds_on_hot_ratio_basis"],
        cases=cases,
        the_ruling_conclusion_holds_at_the_declared_ratio=bool(
            cases["at_the_declared_ruling_ratio"][
                "every_device_meets_a_published_conduction_row"]
            and cases["at_the_declared_ruling_ratio"][
                "every_device_is_guaranteed_enhanced"]),
        ratio_at_which_the_conduction_row_is_lost=crossing,
        margin_on_the_coefficient=(
            None if crossing is None
            else round(crossing / ruling_ratio, 6)),
        margin_on_the_published_coefficient=(
            None if crossing is None
            else round(crossing / spec["rds_on_hot_ratio_published"], 6)),
        # ---- THE METAMORPHIC CONTROLS.  R11-01: "Add metamorphic/negative
        # controls proving the output moves in the expected direction and
        # crosses the criterion when it should."
        the_channel_resistance_is_strictly_increasing_in_the_ratio=bool(
            all(order[i]["channel_ohm_hot"] < order[i + 1]["channel_ohm_hot"]
                for i in range(len(order) - 1))),
        the_junction_is_strictly_increasing_in_the_ratio=bool(
            all(order[i]["junction_C"] < order[i + 1]["junction_C"]
                for i in range(len(order) - 1))),
        the_worst_vgs_is_strictly_decreasing_in_the_ratio=bool(
            all(order[i]["per_device"]["Q2"]["worst_case_vgs_V"]
                > order[i + 1]["per_device"]["Q2"]["worst_case_vgs_V"]
                for i in range(len(order) - 1))),
        the_cases_are_not_identical=bool(
            len({c["channel_ohm_hot"] for c in cases.values()})
            == len(cases)),
        a_ratio_above_the_crossing_is_refused=bool(
            crossing is not None
            and not solve(_rule_amps, air_peak, crossing * 1.02)[
                "every_device_meets_a_published_conduction_row"]),
        a_ratio_below_the_crossing_is_accepted=bool(
            crossing is not None
            and solve(_rule_amps, air_peak, crossing * 0.98)[
                "every_device_meets_a_published_conduction_row"]),
        what_the_2x_case_means=(
            "REPORTED, NOT RULED ON.  A 25 -> 125 C RDS(on) ratio of 2.0 is "
            "the drift-limited behaviour of a high-voltage MOSFET, whose "
            "resistance follows the bulk mobility as about T^2.4; a 30 V "
            "trench part's resistance is dominated by the channel and the "
            "package, and AOS MEASURES 1.4815 on this die between its own "
            "two published temperature rows.  Round-11 reproduced the 2x "
            "case as a counterexample to D-791's INERT sensitivity, and it "
            "is reproduced here with the corrected solver rather than "
            "argued away: at 2.0 the ruling case does not hold the "
            "conduction row.  The ruling bound is the DECLARED 1.60 and the "
            "crossing ratio is published above, so the size of the "
            "dependency is a number."),
        measurement_of_record="C-BAT-GATE-01",
        why="a DECLARED coefficient that the verdict depends on is an "
            "assumption wearing a datasheet's clothes.  D-791 said so and "
            "then captured the coefficient before its own sensitivity could "
            "change it, so all three advertised corners returned the same "
            "arithmetic.  The law is a solver argument now and the controls "
            "above fail if it ever stops being one.")

    # ---- THE GATE DRIVE OVER THE WHOLE CELL RANGE -------------------------
    out["bat_raw_sweep"] = [
        dict(bat_raw_V=round(v, 3),
             guaranteed_gate_drive_V=ltc4368_gate_drive_min_V(v, rows),
             row_used_V=max([r for r in sorted(rows or LTC4368_GATE_DRIVE_ROWS_V)
                             if r <= v] or [None]))
        for v in (2.75, 3.0, 3.3, 3.6, 3.85, 4.0, 4.221)]
    out["gate_drive_is_the_same_row_across_the_whole_cell_range"] = bool(
        len({r["guaranteed_gate_drive_V"] for r in out["bat_raw_sweep"]}) == 1)
    out["vgs_maximum_bound_V"] = drive_max
    out["vgs_maximum_is_inside_the_parts_rating"] = bool(
        drive_max is not None and drive_max <= spec["vgs_abs_max_V"])
    out["vgs_maximum_margin_V"] = (
        None if drive_max is None
        else round(spec["vgs_abs_max_V"] - drive_max, 6))
    out["current_is_inside_the_parts_rating"] = bool(
        design_amps <= spec["id_continuous_70C_A"])
    out["startup_gate_charge_ms"] = round(
        4 * spec["qg_max_nC"] * 1e-9 / 20e-6 * 1000.0, 4)
    out["startup_basis"] = (
        "four channels at the AO4800's 7 nC MAX total gate charge against the "
        "LTC4368's IGATE(UP) MINIMUM of 20 uA.  Both body diodes of each "
        "common-source pair are anti-series, so nothing conducts until the "
        "gate rises and there is no inrush through a diode to bound.")
    out["body_diode_note"] = (
        "IS 2.5 A continuous MAX.  In forward conduction the channel is on "
        "and the parallel body diode sees only the channel drop -- about "
        "%.0f mV at the ruling envelope, far below its own forward voltage "
        "-- so it carries no meaningful current."
        % (ruling["channel_ohm_hot"] * ruling["amps"] * 1000.0))
    out["consequence"] = (
        "a higher pass-pair resistance costs a larger drop from the pack and "
        "more heat in two SOIC-8s, and the D789-A02 enclosure model carries "
        "both.  What the AO4800 REMOVES is the failure this circuit really "
        "had: with the retired NTMD4820N a worst-corner part was not "
        "guaranteed to be enhanced at all, and an unenhanced pass pair is a "
        "board that will not run from its own battery.  The LTC4368's "
        "overcurrent, reverse and UV/OV protection sense across R75 and pull "
        "the gate DOWN, and none of them depends on how well the pair "
        "conducts.")
    out["first_article"] = "C-BAT-GATE-01"
    out["ok"] = bool(
        ruling["every_device_is_guaranteed_enhanced"]
        and ruling["every_device_meets_a_published_conduction_row"]
        and out["vgs_maximum_is_inside_the_parts_rating"]
        and out["current_is_inside_the_parts_rating"]
        # D-792 / R11-01: the declared corner is a TERM OF THE VERDICT now.
        and out["hot_ratio_sensitivity"][
            "the_ruling_conclusion_holds_at_the_declared_ratio"]
        and out["hot_ratio_sensitivity"]["the_cases_are_not_identical"]
        and out["hot_ratio_sensitivity"][
            "the_channel_resistance_is_strictly_increasing_in_the_ratio"]
        and out["hot_ratio_sensitivity"][
            "the_worst_vgs_is_strictly_decreasing_in_the_ratio"]
        and out["hot_ratio_sensitivity"][
            "a_ratio_above_the_crossing_is_refused"]
        and out["hot_ratio_sensitivity"][
            "a_ratio_below_the_crossing_is_accepted"])
    return out["ok"], out


# ==========================================================================
# F12 -- THE COMPLETE CELL-TO-LOAD NETWORK.
#
# ADDED AT D-791 / D790-A03, and it is the clause every other battery-side
# number in this file now hangs off.
#
# WHAT ROUND-10 FOUND.  F6 starts its model AT `BAT_PROTECTED_P`, which is
# where the MAX17048 measures and where the firmware floors are defined, and
# says so explicitly -- it does not double-count `Q2`/`Q3`, `R75` or the pack,
# "all of which are UPSTREAM of what the gauge reads".  F10 prices the pass
# pair separately, for a different question.  NEITHER OF THEM EVER ASKED
# WHETHER AN ATTAINABLE CELL CAN HOLD THAT NODE AT THAT VOLTAGE WHILE THE
# LOAD IS DRAWING, and the answer is that it cannot: sustaining 3.85 V at
# `BAT_PROTECTED_P` at the modelled current needs more than 4.3 V upstream
# through four 50 mOhm channels and `R75` alone, and the pack's charge
# cut-off is 4.2 V.
#
# The consequence is not a rounding error.  The D-790 firmware floors -- 3.50 V
# single, 3.85 V dual -- are node voltages that the node NEVER REACHES under
# the published load, so the accessory rails this board publishes could be
# enabled and would then be shed by the next settled recheck, on a FULL pack.
# A derivation whose answer is unreachable is not a conservative derivation;
# it is a vacuous one, and `firmware_floors_are_attainable` below is the
# clause that makes that impossible to repeat.
#
# WHAT THE NETWORK IS, END TO END AND IN ONE PLACE:
#
#     CELL(OCV) -[pack DC resistance: cell + PCM]- pack terminals
#               -[26 AWG harness, both conductors]- J4
#               -[F1 element]- BAT_RAW
#               -[Q2 ch1]-[Q2 ch2]-[Q3 ch1]-[Q3 ch2]- BAT_SENSE
#               -[R75]- BAT_PROTECTED_P          <- the MAX17048 node
#               -[live copper + BQ25185 BATFET]- SYS
#               -[U12]-> +3V3 -> internal load + [U20] -> ACC_3V3_SW
#               -[live SYS->L4 trunk]-[U21]-> ACC_5V_RAW -[U22]-> ACC_5V_SW
#
# and it is solved as ONE self-consistent fixed point: the channel resistance
# sets the drops, the drops set the node and `VSYS`, those set the currents,
# the currents set the dissipation, the dissipation sets the internal air, the
# air moves the channel resistance again -- and `VGS` is re-checked against the
# `AO4800`'s own lowest published conduction row at the converged current.
#
# THE LIMITS EVERY DECLARED STATE MUST CLEAR AT ONCE.  Not one of them is new;
# what is new is that they are asked TOGETHER, at an attainable cell voltage:
#
#   1  a stable operating point exists at all (a constant-power load into a
#      resistive source has none below a critical voltage, and D-790's
#      declared reference state has none at ANY cell voltage);
#   2  `BAT_PROTECTED_P` stays above the BQ25185's own `VBUVLO`, below which
#      the BATFET disconnects and the product powers down;
#   3  `VSYS` stays at or above `U12_VIN_FLOOR`, the condition TI states its
#      2 A output capability at;
#   4  the battery current stays under the `IBAT_OCP` margin convention, taken
#      at the DECLARED WIDER accuracy band (D790-A10), not the one TI states
#      at a single current and junction temperature;
#   5  `VGS` on the worst pass-pair package stays at or above the `AO4800`'s
#      lowest published `RDS(on)` row, so the conduction the model uses is a
#      guaranteed number (D790-A01);
#   6  the BQ25185 junction stays inside TI's operating maximum, referenced to
#      the internal air of this enclosure rather than to open still air;
#   7  the internal air stays inside the fitted pouch's published discharge
#      window.
#
# WHAT IT COSTS, STATED PLAINLY.  D-790 published a sustained reference state
# with BOTH radios transmitting and the audio amplifier at its capped level
# beside both full accessory budgets.  That state has no operating point.  The
# published accessory budgets are UNCHANGED -- 400 mA and 300 mA, exactly as
# the owner approved -- and what D-791 corrects is the SIMULTANEITY OF
# INTERNAL MAXIMA, which was never an owner decision and was derived from an
# ideal-source formula.  The supported concurrency is DERIVED below, per
# state, as the lowest cell open-circuit voltage each one holds at, and it is
# expressed in OBSERVABLE MODES -- which radio is transmitting, whether the
# amplifier is driving -- because a restriction a user cannot observe is not a
# restriction (D790-A02).
# ==========================================================================
# The fitted pack, from its own specification sheet (archived under
# vendor/BATTERY/ and hashed by `battery_pack_contract` B2).
CELL = dict(
    model="785060 2500 mAh (Adafruit 328)",
    charge_cutoff_V=4.2,
    discharge_cutoff_V=2.75,
    nominal_V=3.75,
    published_impedance_ohm=0.035,
    published_impedance_condition="AC 1 kHz after 50 % charge, 25 C, at the "
                                  "PACK terminals -- so it contains the cell "
                                  "AND the protection board",
    dc_multiplier=2.5,
    dc_multiplier_basis=(
        "DECLARED.  A 1 kHz AC impedance omits the diffusion component that a "
        "DC load sees; 2.5x is a deliberately pessimistic carry for a 2.5 Ah "
        "pouch and it REPLACES D-790's invented 40 mOhm PCM allowance, which "
        "cited nothing.  It is MEASURED at first article alongside the rest "
        "of the battery path (C-THERM-01 and the battery-path resistance "
        "measurement)"),
    source="785060 2500 mAh specification sheet section 3: nominal capacity "
           "2500 mAh, nominal voltage 3.75 V, charge cut-off 4.2 V, discharge "
           "cut-off 2.75 V, impedance <= 35 mOhm (AC 1 kHz after 50 % charge, "
           "25 C), discharge working temperature 0..60 C.")
CELL_MAX_OCV_V = 4.221      # BQ25185 VBATREG 4.2 V at its +0.5 % accuracy
CELL_MAX_OCV_BASIS = (
    "the charger's own regulation maximum, not the cell's nameplate: BQ25185 "
    "VBATREG programmed to 4.2 V with the published +/-0.5 % accuracy.  This "
    "is the highest open-circuit voltage the product can put on the pack.")
# BQ25185 SLUSF65B EC: VBUVLO "Battery UVLO, VBAT falling" 3 V, with NO MIN or
# MAX column, and VBUVLO_HYS 110/150/190 mV rising.  A typical used as a limit
# is what D-789 and D-790 both refused, so the bound is DECLARED wider.
BUVLO_TYP_V = 3.0
BUVLO_DECLARED_TOLERANCE = 0.05
BUVLO_BOUND_V = round(BUVLO_TYP_V * (1.0 + BUVLO_DECLARED_TOLERANCE), 6)
BUVLO_SOURCE = (
    "TI SLUSF65B Electrical Characteristics: VBUVLO 'Battery UVLO, VBAT "
    "falling' = 3 V with no MIN/MAX column published, VBUVLO_HYS 110/150/190 "
    "mV rising.  Below VBUVLO the device DISCONNECTS BAT from SYS, so this is "
    "the hard floor on BAT_PROTECTED_P: under it the product powers down.  "
    "A DECLARED +5 % is carried because TI publishes no tolerance and this "
    "programme does not use a typical as a limit.")
# MAX17048 ADI 19-6171 Rev.7 EC: VERR +/-7.5 mV/cell at VCELL = 3.6 V and
# TA = +25 C, and +/-20 mV/cell otherwise.  D-791 / D790-A14: the POSITIVE
# error is the one that matters -- a reported 3.850 V can be an actual
# 3.830 V -- so every floor the firmware compares a REPORTED value against is
# raised by it, plus one quantisation step.
GAUGE_VERR_V = 0.020
GAUGE_LSB_V = 78.125e-6
GAUGE_ERROR_SOURCE = (
    "ADI 19-6171 Rev.7 Electrical Characteristics, Voltage Error VERR: "
    "-7.5/+7.5 mV/cell at VCELL = 3.6 V, TA = +25 C (Note 4) and -20/+20 "
    "mV/cell over the specified range; VCELL resolution 78.125 uV/cell.  The "
    "+20 mV end is charged to every floor because the reported value may be "
    "that much ABOVE the real one.")
# D-791 / D790-A10.  THE BATOCP BAND IS CONDITIONED AND THE CONDITION IS NOT
# THIS DESIGN'S.
#
# SLUSF65B publishes `IBAT_OCP` as a TYPICAL 3.13 A at VBAT = 4 V with no
# MIN/MAX column, and `IBAT_OCPACC` as 18 % MAX at IBAT = 3.125 A, TJ = 27 C.
# D-790 propagated 3.125 x (1 -/+ 0.18) = 2.5625..3.6875 A as if it were a
# guaranteed all-temperature, all-cell-voltage band.  It is not, and Round-10
# is right to refuse it.  TI publishes nothing wider, so the honest form is an
# EXPLICIT ASSUMPTION with a stated sensitivity:
#
#   * the STATED band is retained and reported, and the fault screens that
#     have always used it keep using it, because widening a FAULT threshold
#     band is not conservative in that direction -- a wider band also raises
#     the maximum, and the fault clauses ask whether the protection fires
#     BELOW the fuse and the copper;
#   * the SUSTAINED envelope F12 rules on uses a DECLARED WIDER band, so a
#     state is only called supported if it survives an OCP minimum well below
#     the one TI states at its own single condition.
IBAT_OCP_TYP_A = 3.125
IBAT_OCP_STATED_ACCURACY = 0.18
IBAT_OCP_ASSUMED_ACCURACY = 0.25
IBAT_OCP_ASSUMED_MIN_A = round(IBAT_OCP_TYP_A * (1.0 - IBAT_OCP_ASSUMED_ACCURACY), 6)
IBAT_OCP_CONDITION_SOURCE = (
    "TI SLUSF65B Electrical Characteristics: IBAT_OCP 'BATOCP' typical "
    "3.13 A at VBAT = 4 V, no MIN/MAX column; IBAT_OCPACC 'BATOCP accuracy' "
    "18 % MAX at IBAT = 3.125 A, TJ = 27 C.  Section 6.3.7.3: on a BATOCP "
    "trip the battery discharge FET turns off and the device enters HICCUP "
    "mode, re-enabling after tREC_SC = 250 ms, with a 2 s retry window -- so "
    "a BATOCP event is a total system interruption, not a graceful limit, and "
    "is not an operating state.  The 25 % band this contract rules the "
    "SUSTAINED envelope at is a DECLARED ASSUMPTION beyond TI's stated "
    "condition and is measured at first article (C-BAT-GATE-01).")


def judge_cell_to_load(paths_ohm, v_3v3_V, v_acc5v_V, ron_a3_ohm, ron_a5_ohm,
                       budget=None, ambient_C=None, pass_pair=None,
                       ocp_min_A=None, margin=None):
    """D-791 / D790-A03.  The whole network, cell to load, every declared state.

    Pure over its arguments.  `paths_ohm` is the LIVE measured set
    `judge_accessory_envelope` uses; the rail voltages and switch RONs are the
    ones F6 derives, so the two clauses cannot describe different boards.
    """
    spec = PASS_PAIR if pass_pair is None else pass_pair
    budget = PUBLISHED_RAIL_BUDGET_A if budget is None else budget
    ambient_C = ara.AMBIENT_DESIGN_MAX_C if ambient_C is None else ambient_C
    ocp_min_A = IBAT_OCP_ASSUMED_MIN_A if ocp_min_A is None else ocp_min_A
    margin = NORMAL_OCP_MARGIN_MIN if margin is None else margin
    i_limit = ocp_min_A * (1.0 - margin)

    k_cu = 1.0 + CU_TC_PER_K * CU_HOT_RISE_K
    r_bat = paths_ohm["bat_protected_p"] * k_cu + RON_BAT_MAX_OHM * RON_BAT_VBAT_ALLOWANCE
    r_trunk = paths_ohm["sys_to_u21"] * k_cu
    r_a3 = paths_ohm["acc_3v3_sw"] * k_cu + ron_a3_ohm
    r_a5 = paths_ohm["acc_5v_sw"] * k_cu + ron_a5_ohm
    # D-792 / R11-07: the cell-side series resistance is the ITEMISED path in
    # `aqroot_power_model`, not a one-line allowance.  D-792 / R11-01: the
    # pass-pair temperature law is an explicit argument, not a captured alpha.
    pack_dc = apm.PACK_DC_OHM
    up_fixed = apm.upstream_fixed_ohm("max")
    r25 = spec["rds_on_max_at_that_row_ohm"]
    hot_ratio = spec["rds_on_hot_ratio"]
    drive = ltc4368_gate_drive_min_V(VBAT_CORNER)
    r_sys_K = ara.system_thermal_resistance_K_per_W()
    theta_ja = ara.PACKAGE_JUNCTION["theta_ja_C_per_W"]
    ron_bat = RON_BAT_MAX_OHM * RON_BAT_VBAT_ALLOWANCE

    def solve(cell_V, i3, i5, i_int, amb=None):
        """One self-consistent operating point, or None if there is none.

        `amb` is the EXTERNAL ambient.  It defaults to the top of the declared
        prototype envelope, which is what every verdict is taken at; it is an
        argument so the AMBIENT CEILING of a state can be DERIVED rather than
        asserted, and so the sensitivity of the answer to it is a number.
        """
        amb = ambient_C if amb is None else amb
        p12 = ((i_int + i3) * v_3v3_V + i3 * i3 * r_a3) / ETA_U12
        p21 = ((i5 * v_acc5v_V + i5 * i5 * r_a5) / ETA_U21) if i5 else 0.0
        amps = (p12 + p21) / cell_V
        r_ch, air = r25, amb + 10.0
        for _ in range(3000):
            r_up = up_fixed + spec["channels_in_series"] * r_ch
            vsys = cell_V - amps * (r_up + r_bat)
            if vsys <= 0.5:
                return None
            if p21:
                i_u21 = p21 / vsys
                for _ in range(80):
                    v_in = vsys - i_u21 * r_trunk
                    if v_in <= 0.4:
                        return None
                    i_u21 = p21 / v_in
                trunk_W = i_u21 * i_u21 * r_trunk
            else:
                trunk_W = 0.0
            nxt = (p12 + p21 + trunk_W) / vsys
            node = cell_V - nxt * r_up
            p_int = (node * nxt - (i3 * v_3v3_V + i5 * v_acc5v_V)
                     + nxt * nxt * r_up)
            air_next = amb + r_sys_K * p_int
            tj_pp = air_next + 5.0 + spec["theta_jl_max_C_per_W"] * (
                2 * nxt * nxt * r_ch)
            r_next = apm.channel_ohm(tj_pp, hot_ratio, spec)
            if (abs(nxt - amps) < 1e-11 and abs(r_next - r_ch) < 1e-13
                    and abs(air_next - air) < 1e-9):
                amps, r_ch, air = nxt, r_next, air_next
                break
            amps = 0.7 * amps + 0.3 * nxt
            r_ch = 0.7 * r_ch + 0.3 * r_next
            air = 0.7 * air + 0.3 * air_next
        r_up = up_fixed + spec["channels_in_series"] * r_ch
        node = cell_V - amps * r_up
        vsys = cell_V - amps * (r_up + r_bat)
        p_int = (node * amps - (i3 * v_3v3_V + i5 * v_acc5v_V)
                 + amps * amps * r_up)
        air = amb + r_sys_K * p_int
        tj_bq = air + theta_ja * (amps * amps * ron_bat)
        tj_pp = air + 5.0 + spec["theta_jl_max_C_per_W"] * (2 * amps * amps * r_ch)
        # Q2 is the package with THREE channels plus R75 between its common
        # source and the LTC4368's VOUT, so it has the smaller VGS.
        vgs = drive - amps * ((spec["channels_in_series"] - 1) * r_ch
                              + spec["sense_resistor_ohm"])
        return dict(
            cell_V=round(cell_V, 6), ambient_C=round(amb, 3),
            amps=round(amps, 6),
            node_V=round(node, 6), vsys_V=round(vsys, 6),
            channel_ohm_hot=round(r_ch, 6),
            upstream_series_ohm=round(r_up, 6),
            internal_W=round(p_int, 6), internal_air_C=round(air, 3),
            bq25185_junction_C=round(tj_bq, 3),
            pass_pair_junction_C=round(tj_pp, 3),
            worst_vgs_V=round(vgs, 6),
            # UNROUNDED, for the independent residual check below.  Every field
            # above is rounded for the report, and a residual taken against a
            # rounded value measures the rounding rather than the solution --
            # which would need a per-field tolerance and would look exactly
            # like a fudge factor.  These are the raw converged values, so ONE
            # tight tolerance is enough and it means what it says.
            raw=dict(cell_V=cell_V, ambient_C=amb, amps=amps, node_V=node,
                     vsys_V=vsys, channel_ohm=r_ch, internal_W=p_int,
                     internal_air_C=air, pass_pair_junction_C=tj_pp))

    # ======================================================================
    # D-792 EXIT CRITERION: "Independent calculation path must not simply call
    # the same solver functions being verified."
    #
    # `solve` is a FIXED-POINT ITERATION.  Re-running it proves nothing about
    # whether its answer satisfies the equations it was iterating towards, and
    # every clause in this contract that checks the network does so by calling
    # it again.  `residuals()` is the independent path: it takes a SOLVED state
    # and re-checks the defining equations with plain arithmetic -- no
    # iteration, no `solve`, no shared code -- and reports how far each one
    # misses.  It checks
    #
    #   KVL     node_V  ==  cell_V - amps * (up_fixed + n * r_ch)
    #   KVL     vsys_V  ==  cell_V - amps * (up_fixed + n * r_ch + r_bat)
    #   POWER   node_V * amps  ==  P(3V3 branch) + P(5V branch) + trunk loss
    #   ENERGY  internal_W  ==  cell_V * amps - what leaves through J5
    #   THERMAL r_ch  ==  channel_ohm(tj_pp) at the reported junction
    #   THERMAL air  ==  ambient + R_SYS * internal_W
    #
    # A residual above the tolerance means the iteration converged to something
    # that is not a solution of the network, which no amount of re-solving
    # would ever have revealed.
    # ======================================================================
    def residuals(s, i3, i5, i_int):
        if s is None or "raw" not in s:
            return None
        q = s["raw"]
        n = spec["channels_in_series"]
        r_ch, amps, cell_V = q["channel_ohm"], q["amps"], q["cell_V"]
        r_up = up_fixed + n * r_ch
        p12 = ((i_int + i3) * v_3v3_V + i3 * i3 * r_a3) / ETA_U12
        p21 = ((i5 * v_acc5v_V + i5 * i5 * r_a5) / ETA_U21) if i5 else 0.0
        trunk_W = 0.0
        if p21:
            i_u21 = p21 / q["vsys_V"]
            for _ in range(400):
                i_u21 = p21 / (q["vsys_V"] - i_u21 * r_trunk)
            trunk_W = i_u21 * i_u21 * r_trunk
        delivered = i3 * v_3v3_V + i5 * v_acc5v_V
        tj_pp = q["internal_air_C"] + 5.0 + spec["theta_jl_max_C_per_W"] * (
            2 * amps * amps * r_ch)
        return dict(
            kvl_node_V=q["node_V"] - (cell_V - amps * r_up),
            kvl_vsys_V=q["vsys_V"] - (cell_V - amps * (r_up + r_bat)),
            # The BATFET is between the node the gauge reads and SYS, so the
            # power the downstream converters draw is delivered AT SYS.
            power_sys_W=q["vsys_V"] * amps - (p12 + p21 + trunk_W),
            energy_internal_W=q["internal_W"]
            - (q["node_V"] * amps - delivered + amps * amps * r_up),
            thermal_channel_ohm=r_ch - apm.channel_ohm(tj_pp, hot_ratio, spec),
            thermal_air_C=q["internal_air_C"]
            - (q["ambient_C"] + r_sys_K * q["internal_W"]),
            junction_C=tj_pp - q["pass_pair_junction_C"])

    def limits(s):
        if s is None:
            return dict(has_an_operating_point=False)
        return dict(
            has_an_operating_point=True,
            node_above_buvlo=bool(s["node_V"] >= BUVLO_BOUND_V),
            vsys_above_u12_floor=bool(s["vsys_V"] >= U12_VIN_FLOOR),
            inside_the_ocp_margin=bool(s["amps"] <= i_limit),
            pass_pair_meets_its_conduction_row=bool(
                s["worst_vgs_V"] >= spec["rds_on_lowest_published_vgs_V"]),
            junction_inside_the_operating_maximum=bool(
                s["bq25185_junction_C"]
                <= ara.PACKAGE_JUNCTION["tj_operating_max_C"]),
            air_inside_the_pouch_window=bool(
                s["internal_air_C"] <= ara.POUCH_ADJACENT_LIMIT_C))

    def supported(s):
        v = limits(s)
        return all(v.values())

    def lowest_cell(i3, i5, i_int):
        top = solve(CELL_MAX_OCV_V, i3, i5, i_int)
        if not supported(top):
            return None
        lo, hi = CELL["discharge_cutoff_V"], CELL_MAX_OCV_V
        for _ in range(60):
            mid = 0.5 * (lo + hi)
            if supported(solve(mid, i3, i5, i_int)):
                hi = mid
            else:
                lo = mid
        return hi

    always = sum(ara.SUSTAINED_ALWAYS_ON.values()) + ara.BURSTY_TIME_AVERAGED_A
    i3b, i5b = budget["ACC_3V3"], budget["ACC_5V"]
    # ======================================================================
    # D-792 / R11-04.  THE ENABLE FLOORS ARE DERIVED FROM THE CRITERION THE
    # FIRMWARE ACTUALLY APPLIES, ON EVERY TRANSITION, IN BOTH RAIL ORDERS.
    #
    # ROUND-11, IN ITS OWN WORDS: "Current transition derivation covers no-rail
    # -> 3V3 -> both but omits 5V-first and 5V->3V3.  It used 3.15 V BUVLO
    # instead of implemented 3.20 V retention in part of the sweep.  Astra
    # reproduced a production-image case that enables 5V from a reported
    # >= 3.55 V pre-read then immediately sheds after load sag."
    #
    # ALL THREE REPRODUCE, AND THE THIRD IS THE REAL ONE.  D-791 derived the
    # enable floors as
    #
    #     enable = VBUVLO_bound + worst_node_step + gauge_error
    #
    # which guarantees the settled node stays above `VBUVLO`.  But the
    # firmware does not compare the node against `VBUVLO`; it compares the
    # gauge's REPORTED value against `kAccessoryRetentionFloorV`, which is
    # `VBUVLO` plus the gauge error AGAIN and then gridded UP.  So a
    # permission granted exactly at the enable floor could settle into a state
    # the retention rule sheds on the next pass -- authorise, sag, shed,
    # 400 ms later.  D-791 fixed "enable then shed" for the node and left it
    # open for the criterion.
    #
    # AND THE ORDER MATTERS.  Only ONE order was swept: no rail -> 3V3 ->
    # both.  The 5 V rail is the EXPENSIVE one -- 300 mA at 5.1654 V through a
    # boost at 0.88 against 400 mA at 3.223 V through a buck-boost at 0.90 --
    # so enabling it FIRST is a bigger node step than enabling the 3.3 V rail
    # first, and its floor was never derived.
    #
    # WHAT REPLACES IT.  Every supported transition is enumerated, and for
    # each one the floor is the FIXED POINT of the firmware's own rule with
    # the gauge error charged in BOTH ADVERSE DIRECTIONS at once:
    #
    #   * the PRE read may be HIGH by the gauge error, so a reported E can
    #     come from a node as low as E - g;
    #   * the POST read may be LOW by the gauge error, so a node of N reports
    #     as low as N - g;
    #   * therefore E must satisfy: for the lowest cell OCV that could have
    #     produced a reported E, the SETTLED post-transition node must report
    #     at or above the retention floor AND satisfy every hardware limit.
    #
    # That is solved directly rather than approximated by a worst-case step,
    # and the resulting invariant -- `every_granted_enable_survives_its_own_
    # settled_state` -- is swept over the whole cell range afterwards, so it
    # is a PROOF and not a construction.
    # ======================================================================
    def grid_up(v):
        return math.ceil(v / FLOOR_GRID_V - 1e-9) * FLOOR_GRID_V

    gauge = GAUGE_VERR_V + GAUGE_LSB_V
    retention = BUVLO_BOUND_V + gauge
    retention_grid = round(grid_up(retention), 4)

    def node(cell, i3, i5, i_int, amb=None):
        s = solve(cell, i3, i5, i_int, amb)
        return None if s is None else s

    def post_is_acceptable(cell, i3, i5, i_int, amb=None):
        """The firmware's own retention rule, applied to the SETTLED state
        with the gauge reading adversely LOW, plus every hardware limit."""
        s = solve(cell, i3, i5, i_int, amb)
        if s is None or not supported(s):
            return False, s
        return bool(s["node_V"] - gauge >= retention_grid - 1e-12), s


    # ======================================================================
    # D-792 / R11-04, PART 1.  THE DECLARED SIMULTANEOUS DUAL-RAIL PAIR.
    #
    # THE PUBLISHED PER-RAIL BUDGETS DO NOT MOVE: `ACC_3V3_SW` = 400 mA TOTAL
    # and `ACC_5V_SW` = 300 mA TOTAL, each deliverable on its own.  What D-792
    # has to state, because the corrected model says so, is the pair that may
    # be drawn AT THE SAME TIME.
    #
    # D-791 answered that with a CELL FLOOR per state and stopped there.  Two
    # Round-11 corrections move the answer:
    #
    #   R11-07  the cell-to-`BAT_PROTECTED_P` series resistance is 249.8 mOhm
    #           itemised, not the 124 mOhm D-791 carried;
    #   R11-02  the ESP32-S3 module's own baseline -- 165.5 mA of CPU, flash
    #           and in-package PSRAM that no ledger contained -- is in EVERY
    #           state.
    #
    # Together they cost about 0.34 V of node at the dual-rail current, and the
    # consequence is precise rather than vague: at the TOP of the declared
    # 0..40 C ambient envelope, in the LIGHTEST internal state, both rails at
    # their full published budgets settle the node at 3.1763 V -- inside every
    # one of the seven hardware limits, but 44 mV BELOW the retention criterion
    # the firmware itself applies.  So the pair is derated, and the derating is
    # SOLVED rather than chosen: the largest proportional scaling of the two
    # published budgets that the retention rule will hold, in the lightest
    # state, at the worst declared ambient, rounded DOWN onto a 10 mA grid.
    #
    # THE LIGHTEST STATE IS THE RIGHT ONE TO DERIVE IT AT because the other
    # states are covered by the PERMISSION TABLE below, which refuses the
    # second rail outright wherever the pair does not hold.  One number for the
    # accessory designer, one table for the firmware.
    # ======================================================================
    MODE_NAMES = tuple(sorted(ara.SUSTAINED_OPTIONAL))

    def i_int_of(modes):
        return always + sum(ara.SUSTAINED_OPTIONAL[m] for m in modes)

    I_INT_LIGHTEST = i_int_of(())

    def largest_retainable_scale(i_int, amb=None):
        """The largest k for which (400k, 300k) mA is RETAINABLE on a full
        pack.  1.0 exactly when the full pair holds."""
        if post_is_acceptable(CELL_MAX_OCV_V, i3b, i5b, i_int, amb)[0]:
            return 1.0
        lo, hi = 0.0, 1.0
        for _ in range(60):
            mid = 0.5 * (lo + hi)
            if post_is_acceptable(CELL_MAX_OCV_V, i3b * mid, i5b * mid,
                                  i_int, amb)[0]:
                lo = mid
            else:
                hi = mid
        return lo

    # THE PAIR IS SOLVED AT THE CELL VOLTAGE THE SINGLE-RAIL PERMISSION ALREADY
    # REACHES, NOT AT A FULL PACK.  Solving it at 4.221 V gives 390/290 mA and
    # a permission floor of 4.00 V -- and the highest value the gauge can EVER
    # report, with only the always-on set drawing, is 3.9953 V.  That is
    # D790-A03's defect in a new place: a floor the node cannot reach is not a
    # restriction, it is a rail that never turns on.  So the pair is derived
    # against the SAME critical cell voltage the single-rail permission uses in
    # the same state, which makes the contract one sentence -- both rails may be
    # on wherever one rail may be, provided the combined draw stays inside the
    # declared pair -- and makes the dual floor equal to the single floor by
    # construction instead of by hope.
    DUAL_GRID_A = 0.010
    dual_target_cell = None
    for _cfg, _post in (("acc_3v3_alone", (i3b, 0.0)),
                        ("acc_5v_alone", (0.0, i5b))):
        _c = None
        if post_is_acceptable(CELL_MAX_OCV_V, _post[0], _post[1],
                              I_INT_LIGHTEST)[0]:
            _lo, _hi = CELL["discharge_cutoff_V"], CELL_MAX_OCV_V
            for _ in range(90):
                _mid = 0.5 * (_lo + _hi)
                if post_is_acceptable(_mid, _post[0], _post[1],
                                      I_INT_LIGHTEST)[0]:
                    _hi = _mid
                else:
                    _lo = _mid
            _c = _hi
        if _c is not None:
            dual_target_cell = _c if dual_target_cell is None else max(
                dual_target_cell, _c)
    dual_at = (CELL_MAX_OCV_V if dual_target_cell is None
               else dual_target_cell)

    def largest_retainable_scale_at(cell_V, i_int, amb=None):
        if post_is_acceptable(cell_V, i3b, i5b, i_int, amb)[0]:
            return 1.0
        lo, hi = 0.0, 1.0
        for _ in range(60):
            mid = 0.5 * (lo + hi)
            if post_is_acceptable(cell_V, i3b * mid, i5b * mid, i_int,
                                  amb)[0]:
                lo = mid
            else:
                hi = mid
        return lo

    dual_scale = largest_retainable_scale_at(dual_at, I_INT_LIGHTEST)
    dual_i3 = (math.floor(i3b * dual_scale / DUAL_GRID_A + 1e-9)
               * DUAL_GRID_A)
    dual_i5 = (math.floor(i5b * dual_scale / DUAL_GRID_A + 1e-9)
               * DUAL_GRID_A)
    dual_declared = dict(
        acc_3v3_A=round(dual_i3, 6), acc_5v_A=round(dual_i5, 6),
        proportional_scale_solved=round(dual_scale, 6),
        solved_at_cell_ocv_V=round(dual_at, 5),
        solved_at_cell_basis=(
            "the critical cell OCV of the WORSE single-rail configuration in "
            "the lightest internal state -- the cell voltage the single-rail "
            "permission floor already corresponds to -- so the dual-rail "
            "permission does not require a pack voltage the gauge can never "
            "report"),
        grid_A=DUAL_GRID_A,
        published_single_rail_A=dict(ACC_3V3=i3b, ACC_5V=i5b),
        the_declared_pair_is_retainable=bool(post_is_acceptable(
            dual_at, dual_i3, dual_i5, I_INT_LIGHTEST)[0]),
        the_declared_pair_holds_on_a_full_pack=bool(post_is_acceptable(
            CELL_MAX_OCV_V, dual_i3, dual_i5, I_INT_LIGHTEST)[0]),
        the_full_pair_is_not=bool(not post_is_acceptable(
            CELL_MAX_OCV_V, i3b, i5b, I_INT_LIGHTEST)[0]),
        full_pair_scale_on_a_full_pack=round(
            largest_retainable_scale(I_INT_LIGHTEST), 6),
        full_pair_at_a_full_pack=solve(CELL_MAX_OCV_V, i3b, i5b,
                                       I_INT_LIGHTEST),
        # THE AMBIENT IS THE OTHER AXIS, AND IT IS DERIVED TOO.  The full pair
        # is refused at 40 C and held at 30 C, so the ceiling is a number a
        # human can observe rather than a capability that simply vanishes.
        full_pair_ambient_ceiling_C=None,
        per_state_scale_at_the_design_ambient={},
        why="the published per-rail budgets are UNCHANGED and each is "
            "deliverable alone; this is the pair that may be drawn AT ONCE, "
            "solved at the top of the declared ambient envelope in the "
            "lightest internal state and rounded DOWN onto a 10 mA grid.")
    # The ambient at which the FULL pair becomes retainable, bisected on the
    # declared 0..40 C envelope.
    _alo, _ahi = 0.0, ara.AMBIENT_DESIGN_MAX_C
    if post_is_acceptable(CELL_MAX_OCV_V, i3b, i5b, I_INT_LIGHTEST,
                          _ahi)[0]:
        dual_declared["full_pair_ambient_ceiling_C"] = round(_ahi, 2)
    elif post_is_acceptable(CELL_MAX_OCV_V, i3b, i5b, I_INT_LIGHTEST,
                            _alo)[0]:
        for _ in range(50):
            _amid = 0.5 * (_alo + _ahi)
            if post_is_acceptable(CELL_MAX_OCV_V, i3b, i5b, I_INT_LIGHTEST,
                                  _amid)[0]:
                _alo = _amid
            else:
                _ahi = _amid
        dual_declared["full_pair_ambient_ceiling_C"] = round(_alo, 2)
    for _st in ara.SUSTAINED_STATES:
        dual_declared["per_state_scale_at_the_design_ambient"][_st["key"]] = (
            round(largest_retainable_scale(i_int_of(_st["modes"])), 6))

    # THE PUBLISHED LOADS, AND ONE THAT IS NOT PUBLISHED ANY MORE.
    #
    # `both_rails` at the FULL published pair is retained as a REPORTED column
    # and as a negative control: R11-02's missing processor baseline and
    # R11-07's itemised battery path together cost about 0.34 V of node at that
    # current, and it now settles 44 mV under the retention criterion at the
    # top of the ambient envelope.  The pair the product PUBLISHES for
    # simultaneous use is the derated one above, and that is the column the
    # reference-state clause rules on.
    LOADS = (("both_rails", i3b, i5b),
             ("both_rails_at_the_declared_pair", dual_i3, dual_i5),
             ("acc_3v3_only", i3b, 0.0),
             ("acc_5v_only", 0.0, i5b), ("no_accessory", 0.0, 0.0))
    PUBLISHED_LOADS = ("both_rails_at_the_declared_pair", "acc_3v3_only",
                       "acc_5v_only", "no_accessory")
    states, worst_sag_first, worst_sag_second = [], 0.0, 0.0
    for st in ara.SUSTAINED_STATES:
        i_int = always + sum(ara.SUSTAINED_OPTIONAL[m] for m in st["modes"])
        row = dict(key=st["key"], modes=list(st["modes"]), what=st["what"],
                   internal_3v3_A=round(i_int, 6), loads={})
        for name, i3, i5 in LOADS:
            floor_cell = lowest_cell(i3, i5, i_int)
            at_top = solve(CELL_MAX_OCV_V, i3, i5, i_int)
            at_floor = solve(floor_cell, i3, i5, i_int) if floor_cell else None
            row["loads"][name] = dict(
                supported=bool(floor_cell is not None),
                lowest_supported_cell_ocv_V=(round(floor_cell, 4)
                                             if floor_cell else None),
                at_the_lowest_supported_cell=at_floor,
                at_a_full_cell=at_top,
                limits_at_the_lowest_supported_cell=limits(at_floor),
                limits_at_a_full_cell=limits(at_top),
                binding_limit_at_the_floor=sorted(
                    k for k, v in limits(at_floor).items() if v is False)
                or (["none -- the cell's own discharge cut-off"]
                    if floor_cell and floor_cell
                    <= CELL["discharge_cutoff_V"] + 1e-6 else []))
        states.append(row)

    # ======================================================================
    # D-792 / R11-04, PART 2.  THE PERMISSION TABLE.
    #
    # ROUND-11, IN ITS OWN WORDS: "Current transition derivation covers no-rail
    # -> 3V3 -> both but omits 5V-first and 5V->3V3.  It used 3.15 V BUVLO
    # instead of implemented 3.20 V retention in part of the sweep.  Astra
    # reproduced a production-image case that enables 5V from a reported
    # >= 3.55 V pre-read then immediately sheds after load sag.  Enumerate both
    # rail orders, all supported pre-load states, gauge error both adverse
    # directions, settling, post-load retention, repeated requests and
    # cooldown.  Hard invariant: if enable is granted, the settled newly-
    # enabled state must remain above the actual retention criterion."
    #
    # ALL OF IT REPRODUCES, AND THE THIRD ITEM IS THE ROOT CAUSE OF THE OTHER
    # TWO.  D-791 derived the second-rail floor with the FIRST rail already
    # drawing its full published budget in the PRE state.  That is the wrong
    # pre-state, and not by a little: an accessory that is PLUGGED IN AND IDLE
    # holds the node near open circuit, the gauge reports that high value, the
    # permission is granted on it, and the accessory then starts drawing.  The
    # adverse pre-state is the LIGHTEST one, not the heaviest, because the
    # pre-read is what the permission is granted on.  D-791 charged the gauge
    # error in both directions and then handed the derivation a pre-state that
    # cancelled the whole effect.  That is Astra's 3.55 V case exactly.
    #
    # AND A SCALAR PAIR OF FLOORS CANNOT CARRY THE ANSWER.  Whether a rail
    # transition survives its own settled state depends on what else is ON:
    # the amplifier, a keyed sub-GHz transmitter and the Wi-Fi/BLE radio are
    # each a load of the same order as an accessory rail.  D-791 answered with
    # two constants and a sentence asking the reader to observe the modes.  Two
    # constants cannot refuse.  What replaces them is a TABLE indexed by the
    # OBSERVABLE MODE SET and the RAIL COUNT, derived here and PINNED into
    # `aqroot_accessory_power_policy.h`, and a firmware rule that consults it
    # on BOTH edges: enabling a rail, and entering a mode while a rail is on.
    #
    # EVERY FLOOR IS DERIVED AGAINST THE SAME THREE ADVERSE CHOICES:
    #   * the PRE state is the LIGHTEST reachable one -- no optional mode, no
    #     accessory current -- so no arrival path can be granted on a
    #     pre-read this floor did not anticipate;
    #   * the gauge reads HIGH by its error on the pre read and LOW on the
    #     post read, both at once;
    #   * the POST state must satisfy the firmware's OWN retention criterion
    #     and all seven hardware limits after settling, which makes a repeated
    #     request idempotent: the state is settled, so the answer does not
    #     change on the next pass and there is nothing for a cooldown to hide.
    #
    # A combination with NO cell voltage that survives is NOT_PERMITTED, and
    # the firmware refuses it at every cell voltage rather than authorising it
    # and shedding 400 ms later.
    # ======================================================================
    reported_ceiling = None
    _top = node(CELL_MAX_OCV_V, 0.0, 0.0, I_INT_LIGHTEST)
    if _top is not None:
        reported_ceiling = round(_top["node_V"] + gauge, 6)

    def critical_cell(post, i_post):
        """The smallest cell OCV at which the POST state is acceptable, or
        None if no attainable cell voltage is."""
        if not post_is_acceptable(CELL_MAX_OCV_V, post[0], post[1],
                                  i_post)[0]:
            return None
        lo, hi = CELL["discharge_cutoff_V"], CELL_MAX_OCV_V
        for _ in range(90):
            mid = 0.5 * (lo + hi)
            if post_is_acceptable(mid, post[0], post[1], i_post)[0]:
                hi = mid
            else:
                lo = mid
        return hi

    def permission_floor(post, i_post, i_pre=None):
        """The reported pre-read at or above which arriving at `post` is sound.

        `i_pre` is the internal current of the PRE state.  It is NOT always
        `i_post`: a RAIL edge keeps the mode set and only changes the accessory
        current, while a MODE edge is entered from a LIGHTER mode set and
        therefore from a HIGHER pre-read.  Using the post state's own current
        for a mode edge would under-state the floor and be UNSOUND; using the
        absolutely lightest state for a rail edge over-states it into a floor
        the node cannot reach, which is D790-A03.  Both edges are derived, each
        from its own pre-state.

        The accessory current of the pre-state is ZERO in both cases, because a
        plugged-in IDLE accessory holds the node near open circuit and that is
        the reading the permission is granted on -- R11-04's root cause.
        """
        i_pre = i_post if i_pre is None else i_pre
        c = critical_cell(post, i_post)
        if c is None:
            return None, None, None
        pre = node(c, 0.0, 0.0, i_pre)
        top = node(CELL_MAX_OCV_V, 0.0, 0.0, i_pre)
        if pre is None or top is None:
            return None, c, None
        return pre["node_V"] + gauge, c, top["node_V"] + gauge

    def lightest_predecessor_current(modes):
        """The internal current of the lightest state ONE STEP below `modes`.

        For a mode edge the pre-state is `modes` minus the mode being entered,
        and the adverse choice is the mode whose removal leaves the LIGHTEST
        state -- the highest pre-read.  With no mode on there is nothing to
        enter, so the state itself is the answer.
        """
        if not modes:
            return i_int_of(())
        return min(i_int_of(tuple(m for m in modes if m != drop))
                   for drop in modes)

    RAIL_CONFIGS = {
        1: (("acc_3v3_alone", (i3b, 0.0)), ("acc_5v_alone", (0.0, i5b))),
        2: (("both_rails_at_the_declared_pair", (dual_i3, dual_i5)),),
    }
    # ======================================================================
    # TWO EDGES, TWO TABLES.  The arrival path decides the PRE-STATE, and the
    # pre-state decides the floor, so one table cannot answer both questions.
    #
    #   RAIL EDGE   the mode set does not change; the accessory current does.
    #               Pre-state = these modes, accessory idle.
    #   MODE EDGE   the accessory rails are already live; the mode set grows.
    #               Pre-state = the LIGHTEST mode set one step below, accessory
    #               idle -- which reads HIGHER, so the floor is HIGHER.
    #
    # Collapsing them into one number means taking the larger, and D-790 has
    # already shown what that costs: the rail-edge floor for a state with the
    # Wi-Fi radio up would become a value the node cannot reach in that state,
    # and the rail would simply never turn on with no diagnostic anywhere.  So
    # both are derived, both are attainability-checked AGAINST THEIR OWN
    # PRE-STATE, and both are pinned into the firmware.
    # ======================================================================
    def build_table(edge):
        rows, table = [], {}
        for bits in range(1 << len(MODE_NAMES)):
            modes = tuple(MODE_NAMES[i] for i in range(len(MODE_NAMES))
                          if bits & (1 << i))
            i_int = i_int_of(modes)
            i_pre = (i_int if edge == "rail"
                     else lightest_predecessor_current(modes))
            for rails in (1, 2):
                worst = dict(floor=None, cfg=None, c=None, ceiling=None)
                refused, unreachable = [], []
                for cfg_name, post in RAIL_CONFIGS[rails]:
                    req, c, ceiling = permission_floor(post, i_int, i_pre)
                    if req is None:
                        refused.append(cfg_name)
                        continue
                    if worst["floor"] is None or req > worst["floor"]:
                        worst = dict(floor=req, cfg=cfg_name, c=c,
                                     ceiling=ceiling)
                if refused or worst["floor"] is None:
                    gridded, permitted = None, False
                else:
                    gridded = round(grid_up(worst["floor"]), 4)
                    # ATTAINABILITY, AGAINST THIS EDGE'S OWN PRE-STATE.  A
                    # gridded floor above the highest value the gauge can
                    # report in the pre-state authorises nothing, ever.
                    permitted = bool(worst["ceiling"] is not None
                                     and gridded <= worst["ceiling"] + 1e-12)
                    if not permitted:
                        unreachable.append(
                            "gridded %.4f V exceeds the %.4f V ceiling of its "
                            "own pre-state" % (gridded, worst["ceiling"]))
                        gridded = None
                rows.append(dict(
                    edge=edge, mode_bits=bits, modes=list(modes), rails=rails,
                    internal_3v3_A=round(i_int, 6),
                    pre_state_internal_3v3_A=round(i_pre, 6),
                    rail_configuration=worst["cfg"],
                    configurations_with_no_attainable_cell_voltage=refused,
                    unreachable=unreachable,
                    pre_state_reported_ceiling_V=(
                        None if worst["ceiling"] is None
                        else round(worst["ceiling"], 6)),
                    critical_cell_ocv_V=(None if worst["c"] is None
                                         else round(worst["c"], 5)),
                    required_reported_floor_V=(None if worst["floor"] is None
                                               else round(worst["floor"], 6)),
                    floor_gridded_V=gridded, permitted=permitted))
                table[(bits, rails)] = gridded if permitted else None
            # MONOTONIC BY CONSTRUCTION.  A two-rail state is only reachable
            # THROUGH a one-rail state, so a dual floor below the single floor
            # of the same mode set would be an unreachable graduation -- the
            # same shape D-790's 3.85 V dual floor had.  The derated pair is
            # lighter than one rail at its full published budget, so the raw
            # dual floor legitimately comes out lower; it is raised so the
            # sequence a user actually walks is the sequence that is proven.
            one, two = table.get((bits, 1)), table.get((bits, 2))
            if one is not None and two is not None and two < one:
                table[(bits, 2)] = one
                for r in rows:
                    if (r["mode_bits"] == bits and r["rails"] == 2
                            and r["edge"] == edge):
                        r["floor_gridded_V"] = one
                        r["raised_to_the_single_rail_floor"] = True
            if one is None and two is not None:
                table[(bits, 2)] = None
                for r in rows:
                    if (r["mode_bits"] == bits and r["rails"] == 2
                            and r["edge"] == edge):
                        r["floor_gridded_V"] = None
                        r["permitted"] = False
                        r["refused_because_no_single_rail_is_permitted"] = True
        return rows, table

    rail_rows, rail_table = build_table("rail")
    mode_rows, mode_table = build_table("mode")
    permission_rows = rail_rows + mode_rows
    permission_table = rail_table

    # ---- THE FOUR NAMED TRANSITIONS, KEPT FOR THE PUBLISHED NODE STEPS AND
    # FOR ASTRA'S REPRODUCED COUNTEREXAMPLE.  These are the same four orders
    # D-791 should have enumerated, now including 5 V FIRST and 5 V -> 3.3 V,
    # and they are reported at the DECLARED pair so the step a user can
    # actually cause is the step that is published.
    TRANSITIONS = (
        dict(key="first_rail_3v3", rank="first", pre=(0.0, 0.0),
             post=(i3b, 0.0),
             what="no accessory rail on -> the 3.3 V rail at its published "
                  "400 mA budget"),
        dict(key="first_rail_5v", rank="first", pre=(0.0, 0.0),
             post=(0.0, i5b),
             what="no accessory rail on -> the 5 V rail at its published "
                  "300 mA budget.  NEVER DERIVED BEFORE D-792 (R11-04)"),
        dict(key="second_rail_5v", rank="second", pre=(0.0, 0.0),
             post=(dual_i3, dual_i5),
             what="the 3.3 V rail already on -> both rails at the declared "
                  "simultaneous pair, from the ADVERSE idle-accessory "
                  "pre-read"),
        dict(key="second_rail_3v3", rank="second", pre=(0.0, 0.0),
             post=(dual_i3, dual_i5),
             what="the 5 V rail already on -> both rails at the declared "
                  "simultaneous pair.  NEVER DERIVED BEFORE D-792 (R11-04)"),
    )
    transition_rows, floor_by_rank = [], {"first": 0.0, "second": 0.0}
    unsupported = []
    for st in ara.SUSTAINED_STATES:
        if st["key"] == "d790_declared":
            continue               # the NEGATIVE control; it has no state
        i_int = i_int_of(st["modes"])
        for tr in TRANSITIONS:
            req, c_star, _ceil = permission_floor(tr["post"], i_int,
                                                  I_INT_LIGHTEST)
            row = dict(state=st["key"], transition=tr["key"],
                       rank=tr["rank"], what=tr["what"],
                       internal_3v3_A=round(i_int, 6),
                       critical_cell_ocv_V=(None if c_star is None
                                            else round(c_star, 5)),
                       required_reported_floor_V=(None if req is None
                                                  else round(req, 6)))
            if req is None:
                unsupported.append(dict(state=st["key"],
                                        transition=tr["key"]))
            else:
                floor_by_rank[tr["rank"]] = max(floor_by_rank[tr["rank"]], req)
                pre = node(c_star, tr["pre"][0], tr["pre"][1],
                           I_INT_LIGHTEST)
                post = solve(c_star, tr["post"][0], tr["post"][1], i_int)
                row.update(
                    pre_node_V=pre["node_V"], post_node_V=post["node_V"],
                    node_step_V=round(pre["node_V"] - post["node_V"], 6),
                    post_reported_worst_V=round(post["node_V"] - gauge, 6))
            transition_rows.append(row)

    # ---- THE INVARIANT, SWEPT OVER THE WHOLE TABLE.  For every mode set and
    # rail count the table PERMITS, every cell voltage at which the firmware
    # WOULD grant the permission is checked against the settled post state.
    # Because the pre-state used for the sweep is the same LIGHTEST one the
    # floor was derived from, this is a proof over arrival paths and not over
    # one chosen order.
    violations, checked = [], 0
    for row in permission_rows:
        if not row["permitted"]:
            continue
        floor = row["floor_gridded_V"]
        modes = tuple(row["modes"])
        i_int = i_int_of(modes)
        i_pre = row["pre_state_internal_3v3_A"]
        for cfg_name, post in RAIL_CONFIGS[row["rails"]]:
            cell = CELL["discharge_cutoff_V"]
            while cell <= CELL_MAX_OCV_V + 1e-9:
                pre = node(cell, 0.0, 0.0, i_pre)
                if pre is not None and pre["node_V"] + gauge >= floor:
                    checked += 1
                    ok, ps = post_is_acceptable(cell, post[0], post[1], i_int)
                    if not ok:
                        violations.append(dict(
                            edge=row["edge"],
                            modes=list(modes), rails=row["rails"],
                            configuration=cfg_name,
                            cell_ocv_V=round(cell, 4),
                            reported_pre_worst_V=round(
                                pre["node_V"] + gauge, 6),
                            floor_V=floor,
                            post_node_V=(None if ps is None
                                         else ps["node_V"]),
                            post_reported_worst_V=(
                                None if ps is None
                                else round(ps["node_V"] - gauge, 6)),
                            retention_floor_V=retention_grid))
                cell += 0.01

    # ---- AND THE REPRODUCED COUNTEREXAMPLE, AS A PERMANENT REGRESSION.
    # Round-11: "Astra reproduced a production-image case that enables 5V from
    # a reported >= 3.55 V pre-read then immediately sheds after load sag."
    # D-791's constant was 3.55 V.  The clause below asks the CORRECTED
    # derivation what that pre-read authorises, and requires that it is
    # refused -- so the counterexample fails on D-791 and passes here for the
    # reason it was raised, not because a string moved.
    _astra_state = i_int_of(())
    _astra_pre = node(3.55 - gauge, 0.0, 0.0, I_INT_LIGHTEST)
    _astra_ok, _astra_post = post_is_acceptable(
        CELL_MAX_OCV_V if _astra_pre is None else 3.55 - gauge,
        0.0, i5b, _astra_state)
    astra_r1104 = dict(
        reported_pre_read_V=3.55,
        d791_first_rail_floor_V=3.55,
        the_settled_5v_state_would_be_acceptable=bool(_astra_ok),
        settled_post=_astra_post,
        d792_first_rail_floor_for_this_state_V=permission_table.get((0, 1)),
        d792_refuses_it=bool(permission_table.get((0, 1)) is not None
                             and permission_table[(0, 1)] > 3.55),
        what="the pre-read D-791's own constant authorised, evaluated against "
             "the corrected network.  `d792_refuses_it` is the regression: "
             "the floor this round derives is ABOVE the value Astra granted "
             "at, so the case cannot recur.")

    # ---- THE TWO SCALAR CONSTANTS ARE NOW VIEWS OF THE TABLE.
    #
    # `kAccessorySingleRailFloorV` and `kAccessoryDualRailFloorV` do not
    # disappear -- DEVICE_SPEC quotes them, `FIRST_FIVE_ASSEMBLY_PLAN` picks
    # bench points from them and an operator needs ONE number per rail count.
    # What changes is what they MEAN: each is the MOST DEMANDING floor the
    # table permits for that rail count, so a state the table refuses is
    # refused by the table and never by a scalar that happens to be high
    # enough.  The firmware consults the TABLE; these are the published
    # envelope of it.
    def _worst_permitted(rails):
        vals = [r["required_reported_floor_V"] for r in permission_rows
                if r["rails"] == rails and r["permitted"]]
        return max(vals) if vals else 0.0

    def _worst_permitted_grid(rails):
        vals = [r["floor_gridded_V"] for r in permission_rows
                if r["rails"] == rails and r["permitted"]]
        return round(max(vals), 4) if vals else 0.0

    def _highest_pre_state_ceiling(rails):
        vals = [r["pre_state_reported_ceiling_V"] for r in permission_rows
                if r["rails"] == rails and r["permitted"]
                and r["pre_state_reported_ceiling_V"] is not None]
        return round(max(vals), 6) if vals else None

    enable_first = _worst_permitted(1)
    enable_second = _worst_permitted(2)
    enable_first_grid = _worst_permitted_grid(1)
    enable_second_grid = _worst_permitted_grid(2)
    if enable_second_grid < enable_first_grid:
        enable_second_grid = enable_first_grid
    # `floor_by_rank` stays as the TRANSITION-derived cross-check: the table
    # and the named-transition sweep are two independent paths to the same
    # envelope, and a disagreement is a defect in one of them.
    transitions_agree_with_the_table = bool(
        round(grid_up(floor_by_rank["first"]), 4) == enable_first_grid)

    def _worst_step(rank):
        vals = [r["node_step_V"] for r in transition_rows
                if r["rank"] == rank and r.get("node_step_V") is not None]
        return round(max(vals), 6) if vals else None

    derived = dict(
        retention_floor_V=round(retention, 6),
        retention_floor_gridded_V=retention_grid,
        enable_first_rail_floor_V=round(enable_first, 6),
        enable_first_rail_floor_gridded_V=enable_first_grid,
        enable_second_rail_floor_V=round(enable_second, 6),
        enable_second_rail_floor_gridded_V=enable_second_grid,
        gauge_error_charged_V=round(gauge, 6),
        gauge_error_source=GAUGE_ERROR_SOURCE,
        # The worst node STEP of each rank, over every enumerated transition of
        # that rank and every sustained state.  These are the numbers
        # DEVICE_SPEC publishes and f12h rules on.
        worst_first_rail_node_step_V=_worst_step("first"),
        worst_second_rail_node_step_V=_worst_step("second"),
        declared_simultaneous_pair=dual_declared,
        worst_permitted_single_rail_floor_gridded_V=enable_first_grid,
        worst_permitted_dual_rail_floor_gridded_V=enable_second_grid,
        transition_sweep_agrees_with_the_table=transitions_agree_with_the_table,
        transition_sweep_first_rail_floor_gridded_V=round(
            grid_up(floor_by_rank["first"]), 4),
        reported_vcell_ceiling_V=reported_ceiling,
        permission_table=permission_rows,
        rail_edge_table=rail_rows,
        mode_edge_table=mode_rows,
        permitted_combinations=sum(1 for r in permission_rows
                                   if r["permitted"]),
        refused_combinations=sum(1 for r in permission_rows
                                 if not r["permitted"]),
        mode_names=list(MODE_NAMES),
        astra_r1104_counterexample=astra_r1104,
        transitions=transition_rows,
        transitions_without_an_operating_point=unsupported,
        invariant_states_checked=checked,
        invariant_violations=violations[:20],
        invariant_violation_count=len(violations),
        every_granted_enable_survives_its_own_settled_state=bool(
            not violations),
        both_rail_orders_are_enumerated=bool(
            {t["key"] for t in TRANSITIONS}
            == {"first_rail_3v3", "first_rail_5v", "second_rail_5v",
                "second_rail_3v3"}),
        the_pre_state_is_the_adverse_lightest_one=bool(
            all(t["pre"] == (0.0, 0.0) for t in TRANSITIONS)),
        the_criterion_is_the_implemented_retention_floor=True,
        method=(
            "RETENTION is the hard node floor: the BQ25185's own VBUVLO "
            "bound, below which the BATFET disconnects and the product powers "
            "down, plus the MAX17048's positive voltage error and one "
            "quantisation step, because the firmware compares a REPORTED "
            "value.  PERMISSION is a TABLE over the observable mode set and "
            "the rail count, and each floor is the reported pre-read -- taken "
            "in the LIGHTEST reachable pre-state, which is the adverse one "
            "because an idle plugged-in accessory holds the node near open "
            "circuit -- below which the SETTLED post state could report under "
            "the retention floor or violate a hardware limit.  D-791 derived "
            "two scalars from a LOADED pre-state in ONE rail order against "
            "VBUVLO rather than against its own retention rule, and Round-11 "
            "reproduced an enable-then-shed case at its 3.55 V constant.  The "
            "swept invariant above is what makes that impossible rather than "
            "unlikely.  The shed order is unchanged: the 5 V rail goes first, "
            "which restores the node."))

    ref_key = ara.SUSTAINED_REFERENCE_KEY
    ref = next((s for s in states if s["key"] == ref_key), None)
    # ---- D-791 / D790-A02.  THE CHARGE REGIME, AT THIS STATE'S OWN POWER ----
    # D-790 said the charge regime "needs no bound, by design".  TREG folds
    # back the CHARGE current and nothing else; the SYSTEM load crosses the
    # same package through the input FET, and once it exceeds the input limit
    # the battery SUPPLEMENTS through the BATFET as well.  Evaluated at the
    # reference state's own load power -- not at its discharge CURRENT, which
    # would be the wrong frame because SYS is regulated near 4.5 V while an
    # adapter is attached.
    ref_i_int = (ref or {}).get("internal_3v3_A", 0.0)
    charge_system_W = ((ref_i_int + i3b) * v_3v3_V / ETA_U12
                       + i5b * v_acc5v_V / ETA_U21)
    charge_split = ara.charge_regime_junction(
        charge_system_W, ambient_C=ambient_C,
        delivered_out_W=i3b * v_3v3_V + i5b * v_acc5v_V)

    # ======================================================================
    # D-792 / R11-03.  THE CHARGE REGIME HAS A LOAD CEILING, AND IT IS DERIVED.
    #
    # ROUND-11, IN ITS OWN WORDS: "Recompute charger/thermal/ambient limits; do
    # not rely on thermal shutdown as normal control."
    #
    # IT IS RIGHT, AND THE PHYSICAL SOLVER IS WHAT MADE IT VISIBLE.  D-791's
    # arithmetic priced the input path as IIN^2 x RON_IN and got 0.569 W.  The
    # BQ25185's input path is not a resistor; it is a LINEAR PASS ELEMENT, and
    # while the device supplements it is dropping VIN - VSYS across it.  At the
    # reference state's own 5.65 W the solver puts SYS at 3.05 V against a
    # 5.195 V VIN pin and the input FET dissipates 2.36 W in a DLH package with
    # a 68.3 C/W JEDEC theta-JA.  That is a 161 K rise: the part would reach
    # TSHUT and stop, which is protection acting as control -- exactly what
    # R11-03 says must not be the answer.
    #
    # SO THE ANSWER IS A CEILING, NOT A PASS MARK.  The largest sustained
    # SYSTEM POWER for which the half TREG cannot reduce stays inside TI's
    # operating maximum is SOLVED here, and the states the product may be in
    # while an adapter is attached are enumerated against it.
    #
    # AND IT CANNOT BE A FIRMWARE RULE, WHICH IS WHY IT IS A PUBLISHED ONE.
    # This board has NO VBUS-present signal on any MCU or expander pin (D-776's
    # bench-only register records `/01_POWER_TREE/VBUS_PRESENT` as probed at
    # TP31.1 and reaching no readable pad), so the firmware cannot know an
    # adapter is attached and must not pretend to.  The restriction is
    # therefore of the same kind as the pouch's own charge window: a SUPERVISED
    # operating condition, published in DEVICE_SPEC and in the first-article
    # procedure, alongside the supervised first-five charging `battery_pack_
    # contract` B8 already requires.
    # ======================================================================
    def charge_junction_at(system_W, delivered_W=0.0):
        r = ara.charge_regime_junction(system_W, ambient_C=ambient_C,
                                       delivered_out_W=delivered_W)
        return r["junction_with_charge_folded_back_C"], r

    _tj_max = ara.PACKAGE_JUNCTION["tj_operating_max_C"]
    _lo, _hi = 0.0, charge_system_W
    if charge_junction_at(_hi)[0] <= _tj_max:
        charge_W_ceiling = _hi
    elif charge_junction_at(_lo)[0] > _tj_max:
        charge_W_ceiling = 0.0
    else:
        for _ in range(80):
            _mid = 0.5 * (_lo + _hi)
            if charge_junction_at(_mid)[0] <= _tj_max:
                _lo = _mid
            else:
                _hi = _mid
        charge_W_ceiling = _lo
    # Which (state, accessory configuration) pairs fit under the ceiling.
    charge_permitted, charge_refused = [], []
    for _st in states:
        for _name in PUBLISHED_LOADS:
            _i3, _i5 = next((a, b) for n, a, b in LOADS if n == _name)
            _sys_W = ((_st["internal_3v3_A"] + _i3) * v_3v3_V / ETA_U12
                      + (_i5 * v_acc5v_V / ETA_U21 if _i5 else 0.0))
            _tj, _r = charge_junction_at(_sys_W,
                                        _i3 * v_3v3_V + _i5 * v_acc5v_V)
            _row = dict(state=_st["key"], load=_name,
                        system_W=round(_sys_W, 6),
                        junction_with_charge_folded_back_C=_tj,
                        mode=_r["mode"],
                        internal_air_C=_r["internal_air_C"],
                        charge_ambient_ceiling_C=_r[
                            "charge_ambient_ceiling_C"])
            (charge_permitted if _tj <= _tj_max
             else charge_refused).append(_row)
    charge_ceiling = dict(
        tj_operating_max_C=_tj_max,
        ambient_C=ambient_C,
        system_W_ceiling=round(charge_W_ceiling, 6),
        reference_state_system_W=round(charge_system_W, 6),
        the_reference_state_is_inside_it=bool(
            charge_system_W <= charge_W_ceiling + 1e-9),
        permitted_while_charging=charge_permitted,
        refused_while_charging=charge_refused,
        the_quiet_state_with_no_accessory_is_permitted=bool(any(
            r["state"] == "display_only" and r["load"] == "no_accessory"
            for r in charge_permitted)),
        there_is_no_vbus_present_signal=True,
        why="TREG folds back the CHARGE current and nothing else.  The SYSTEM "
            "load crosses the same package through a LINEAR input FET, and "
            "once it exceeds the input current limit the battery supplements "
            "through the BATFET as well.  This is the largest sustained system "
            "power for which the half TREG cannot reach stays inside TI's "
            "operating maximum -- a DERIVED, SUPERVISED restriction, not a "
            "reliance on TSHUT.",
        measurement_of_record="C-THERM-01 and C-PWR-CHARGE-01")
    out = dict(
        cell=dict(CELL), cell_max_ocv_V=CELL_MAX_OCV_V,
        cell_max_ocv_basis=CELL_MAX_OCV_BASIS,
        buvlo_bound_V=BUVLO_BOUND_V, buvlo_typ_V=BUVLO_TYP_V,
        buvlo_declared_tolerance=BUVLO_DECLARED_TOLERANCE,
        buvlo_source=BUVLO_SOURCE,
        u12_vin_floor_V=U12_VIN_FLOOR,
        ocp_stated_band_A=[round(IBAT_OCP_TYP_A * (1 - IBAT_OCP_STATED_ACCURACY), 6),
                           IBAT_OCP_TYP_A,
                           round(IBAT_OCP_TYP_A * (1 + IBAT_OCP_STATED_ACCURACY), 6)],
        ocp_assumed_accuracy=IBAT_OCP_ASSUMED_ACCURACY,
        ocp_assumed_min_A=ocp_min_A,
        ocp_margin=margin, ocp_current_limit_A=round(i_limit, 6),
        ocp_condition_source=IBAT_OCP_CONDITION_SOURCE,
        upstream=dict(
            pack_dc_ohm=round(pack_dc, 6),
            harness_ohm=ara.UPSTREAM_LOSS["harness_ohm"],
            fuse_ohm=ara.UPSTREAM_LOSS["fuse_ohm"],
            sense_ohm=spec["sense_resistor_ohm"],
            pass_pair_channels=spec["channels_in_series"],
            fixed_series_ohm=round(up_fixed, 6),
            what="everything between the cell's own electromotive force and "
                 "BAT_PROTECTED_P; all of it dissipates INSIDE the enclosure"),
        downstream=dict(
            bat_protected_p_to_sys_ohm=round(r_bat, 6),
            sys_to_u21_trunk_ohm=round(r_trunk, 6),
            acc_3v3_series_ohm=round(r_a3, 6),
            acc_5v_series_ohm=round(r_a5, 6),
            v_3v3_V=round(v_3v3_V, 6), v_acc5v_V=round(v_acc5v_V, 6)),
        ambient_C=ambient_C,
        always_on_internal_A=round(always, 6),
        bursty_allowances=[dict(b) for b in ara.BURSTY_ALLOWANCES],
        bursty_time_averaged_A=ara.BURSTY_TIME_AVERAGED_A,
        states=states,
        derived_floors=derived,
        reference_state_key=ref_key,
        reference_state=ref,
        charge_regime=charge_split)
    # ---- the clauses ----------------------------------------------------
    out["the_reference_state_is_supported_on_every_published_load"] = bool(
        ref and all(ref["loads"][n]["supported"] for n in PUBLISHED_LOADS))
    out["published_loads"] = list(PUBLISHED_LOADS)
    out["the_full_pair_is_reported_and_not_published"] = dict(
        column="both_rails",
        supported_in_the_reference_state=bool(
            ref and ref["loads"]["both_rails"]["supported"]),
        declared_pair=derived["declared_simultaneous_pair"],
        why="retained as a REPORTED column and as a standing negative "
            "control.  If R11-02's processor baseline or R11-07's itemised "
            "battery path were ever quietly reverted this column would start "
            "passing again, and `the_full_published_pair_is_refused` below is "
            "what notices.")
    out["the_full_published_pair_is_refused"] = dict(
        ok=bool(ref and not ref["loads"]["both_rails"]["supported"]),
        what="the FULL 400 mA + 300 mA pair, simultaneously, in the published "
             "reference state, at the top of the declared ambient envelope",
        ambient_ceiling_C=derived["declared_simultaneous_pair"][
            "full_pair_ambient_ceiling_C"])
    out["the_full_published_pair_is_refused_ok"] = bool(
        out["the_full_published_pair_is_refused"]["ok"])
    out["published_accessory_budgets_are_unchanged"] = bool(
        abs(i3b - 0.400) < 1e-12 and abs(i5b - 0.300) < 1e-12)
    # THE ANTI-VACUITY CLAUSE.  A floor the node cannot reach authorises
    # nothing and refuses everything, which is what D790-A03 found.
    top_none = solve(CELL_MAX_OCV_V, 0.0, 0.0,
                     always + sum(ara.SUSTAINED_OPTIONAL[m]
                                  for m in (ref or {"modes": []})["modes"]))
    top_a3 = solve(CELL_MAX_OCV_V, i3b, 0.0,
                   always + sum(ara.SUSTAINED_OPTIONAL[m]
                                for m in (ref or {"modes": []})["modes"]))
    top_both = solve(CELL_MAX_OCV_V, i3b, i5b,
                     always + sum(ara.SUSTAINED_OPTIONAL[m]
                                  for m in (ref or {"modes": []})["modes"]))
    # D-792 / R11-04.  ATTAINABILITY IS NOW PER ROW AND PER EDGE.
    #
    # D-791's version of this clause compared TWO scalars against the node in
    # ONE reference state, and that is how a 3.95 V rail-edge floor for the
    # Wi-Fi state came within 5 mV of shipping: the scalar was attainable in
    # `display_subghz` and unreachable in the state it actually governed.  The
    # table derivation already refuses a row whose gridded floor exceeds the
    # highest value the gauge can report in that row's OWN pre-state; this
    # clause is the independent restatement of it, plus the two published
    # scalars and the retention floor.
    _unreachable = [dict(edge=r["edge"], modes=r["modes"], rails=r["rails"],
                         floor_V=r["floor_gridded_V"],
                         pre_state_ceiling_V=r["pre_state_reported_ceiling_V"])
                    for r in derived["permission_table"]
                    if r["permitted"] and r["floor_gridded_V"] is not None
                    and r["pre_state_reported_ceiling_V"] is not None
                    and r["floor_gridded_V"]
                    > r["pre_state_reported_ceiling_V"] + 1e-12]
    # ---- THE INDEPENDENT PATH.  Residuals over a spread of solved states.
    _res_rows, _res_worst = [], 0.0
    for _st in states:
        _i = _st["internal_3v3_A"]
        for _name in PUBLISHED_LOADS:
            _i3, _i5 = next((a, b) for n, a, b in LOADS if n == _name)
            for _tag, _s in (("at_a_full_cell",
                              _st["loads"][_name]["at_a_full_cell"]),
                             ("at_the_lowest_supported_cell",
                              _st["loads"][_name][
                                  "at_the_lowest_supported_cell"])):
                _r = residuals(_s, _i3, _i5, _i)
                if _r is None:
                    continue
                _mx = max(abs(v) for v in _r.values())
                _res_worst = max(_res_worst, _mx)
                _res_rows.append(dict(state=_st["key"], load=_name, where=_tag,
                                      worst_abs_residual=_mx, residuals=_r))
    _RES_TOL = 1e-6
    out["the_operating_points_satisfy_their_own_equations"] = dict(
        method="the D-792 exit criterion that an independent calculation path "
               "must not simply call the same solver.  `solve` is a FIXED-POINT "
               "ITERATION; these residuals re-check the DEFINING EQUATIONS of "
               "each solved state with plain arithmetic -- KVL at the "
               "measurement node and at SYS, power balance at the node, energy "
               "balance for the enclosure, the channel resistance against its "
               "own junction temperature, and the internal air against the "
               "system thermal resistance.  A converged answer that is not a "
               "solution would show up here and nowhere else.",
        tolerance=_RES_TOL,
        states_checked=len(_res_rows),
        worst_absolute_residual=_res_worst,
        rows_over_tolerance=[r for r in _res_rows
                             if r["worst_abs_residual"] > _RES_TOL],
        sample=_res_rows[:4],
        ok=bool(_res_rows and _res_worst <= _RES_TOL))
    # ...and the residual check has to BITE, or it is decorative.  A solved
    # state is perturbed by 1 mV at the measurement node -- a thousand times the
    # tolerance and a tenth of a gauge LSB, so it is a change the report itself
    # could not distinguish from noise -- and every equation that depends on the
    # node must move outside tolerance.
    _probe = None
    for _st in states:
        _probe = _st["loads"]["no_accessory"]["at_a_full_cell"]
        if _probe:
            break
    _perturbed = None
    if _probe and "raw" in _probe:
        _perturbed = residuals(
            dict(_probe, raw=dict(_probe["raw"],
                                  node_V=_probe["raw"]["node_V"] + 0.001)),
            0.0, 0.0, states[0]["internal_3v3_A"])
    out["the_residual_check_refuses_a_state_that_is_not_a_solution"] = dict(
        perturbation="node_V + 1 mV on a converged state",
        residuals=_perturbed,
        worst_absolute_residual=(max(abs(v) for v in _perturbed.values())
                                 if _perturbed else None),
        ok=bool(_perturbed
                and max(abs(v) for v in _perturbed.values()) > _RES_TOL),
        why="a residual check that could not fail would be the same class of "
            "defect R11-01 found in the pass-fet sensitivity: a control whose "
            "output does not depend on its input.")
    out["the_residual_check_refuses_a_state_that_is_not_a_solution_ok"] = bool(
        out["the_residual_check_refuses_a_state_that_is_not_a_solution"]["ok"])
    out["the_operating_points_satisfy_their_own_equations_ok"] = bool(
        out["the_operating_points_satisfy_their_own_equations"]["ok"])
    out["firmware_floors_are_attainable"] = dict(
        why="a floor above what the gauge can report in the state that floor "
            "governs can never be cleared, so it authorises nothing and sheds "
            "everything -- on a FULL pack.  D-790's 3.85 V dual floor was such "
            "a number and no clause could see it; D-791 replaced it with a "
            "clause that looked at ONE reference state, and D-792's two-edge "
            "table needs every row checked against its OWN pre-state.",
        reference_state=ref_key,
        node_unloaded_at_a_full_cell_V=(top_none or {}).get("node_V"),
        node_with_the_first_rail_at_a_full_cell_V=(top_a3 or {}).get("node_V"),
        node_with_both_rails_at_a_full_cell_V=(top_both or {}).get("node_V"),
        enable_first_rail_floor_V=derived["enable_first_rail_floor_gridded_V"],
        enable_second_rail_floor_V=derived["enable_second_rail_floor_gridded_V"],
        retention_floor_V=derived["retention_floor_gridded_V"],
        permitted_rows=sum(1 for r in derived["permission_table"]
                           if r["permitted"]),
        rows_with_an_unreachable_floor=_unreachable,
        the_retention_floor_is_reachable_with_both_rails_live=bool(
            top_both is not None
            and top_both["node_V"] >= derived["retention_floor_gridded_V"]),
        the_published_scalars_are_reachable_somewhere=bool(
            derived["enable_first_rail_floor_gridded_V"]
            <= (derived["reported_vcell_ceiling_V"] or 0.0) + 1e-12
            and derived["enable_second_rail_floor_gridded_V"]
            <= (derived["reported_vcell_ceiling_V"] or 0.0) + 1e-12),
        ok=bool(not _unreachable
                and derived["permitted_combinations"] > 0
                and top_none is not None
                and derived["enable_first_rail_floor_gridded_V"]
                <= (derived["reported_vcell_ceiling_V"] or 0.0) + 1e-12
                and derived["enable_second_rail_floor_gridded_V"]
                <= (derived["reported_vcell_ceiling_V"] or 0.0) + 1e-12))
    out["firmware_floors_are_attainable_ok"] = bool(
        out["firmware_floors_are_attainable"]["ok"])
    # AND THE NEGATIVE CONTROL: D-790's own declared state must be REFUSED,
    # so this clause cannot go quiet the way the one it replaces did.
    d790 = next((s for s in states if s["key"] == "d790_declared"), None)
    # D-792: THE SUBJECT OF THIS CONTROL IS THE PUBLISHED SIMULTANEOUS LOAD,
    # NOT THE RETIRED FULL PAIR.  Reading it off the `both_rails` column would
    # make it unfalsifiable: that column is refused BY CONSTRUCTION now -- the
    # full pair has no retainable state in ANY internal mode set -- so a clause
    # anchored there could never flip and `f12a` could never prove it measures
    # anything.  D-790's declared state is refused because it cannot carry
    # ACCESSORY POWER AT ALL, on any published load, and that is what is
    # asserted.
    out["the_d790_declared_state_is_refused"] = dict(
        state=(d790 or {}).get("what"),
        internal_3v3_A=(d790 or {}).get("internal_3v3_A"),
        both_rails_supported=bool(
            d790 and d790["loads"]["both_rails"]["supported"]),
        declared_pair_supported=bool(
            d790 and d790["loads"]["both_rails_at_the_declared_pair"][
                "supported"]),
        any_published_accessory_load_supported=bool(
            d790 and any(d790["loads"][n]["supported"]
                         for n in PUBLISHED_LOADS if n != "no_accessory")),
        why="D-790 published this as the sustained reference state and "
            "computed 1.70 A for it from an ideal-source formula.  Solved "
            "through the real network it carries NO accessory load at any "
            "attainable cell voltage -- not both budgets, not the declared "
            "simultaneous pair, not either rail alone.  If a future change "
            "ever makes it carry one this clause will say so rather than "
            "silently passing.",
        ok=bool(d790 and not d790["loads"]["both_rails"]["supported"]
                and not any(d790["loads"][n]["supported"]
                            for n in PUBLISHED_LOADS if n != "no_accessory")))
    out["the_d790_declared_state_is_refused_ok"] = bool(
        out["the_d790_declared_state_is_refused"]["ok"])
    # THE CHARGE REGIME IS A CLAUSE, NOT A PARAGRAPH.  What TREG cannot reduce
    # must be inside TI's operating maximum, and the ambient at which the
    # internal air reaches the pouch's own CHARGE window must be DERIVED and
    # positive -- a supervised condition a human can observe, which is what
    # D790-A02 asks a declared restriction to be.
    out["the_charge_regime_is_bounded_in_the_half_treg_cannot_reach"] = dict(
        charge_split, load_ceiling=charge_ceiling,
        # THE CLAUSE IS ABOUT THE CEILING, NOT ABOUT ONE STATE.  A pass mark at
        # the reference state would have hidden R11-03's finding; a ceiling
        # with an enumerated permitted set states it.  What must hold is that a
        # ceiling EXISTS, that the quiet no-accessory state is under it -- the
        # product has to be chargeable at all -- and that the ambient at which
        # the internal air reaches the pouch's own charge window is positive
        # for every state the product declares chargeable.
        ok=bool(charge_ceiling["system_W_ceiling"] > 0.0
                and charge_ceiling[
                    "the_quiet_state_with_no_accessory_is_permitted"]
                and charge_ceiling["permitted_while_charging"]
                and all(r["charge_ambient_ceiling_C"] > 0.0
                        for r in charge_ceiling["permitted_while_charging"])))
    out["the_charge_regime_is_bounded_in_the_half_treg_cannot_reach_ok"] = bool(
        out["the_charge_regime_is_bounded_in_the_half_treg_cannot_reach"]["ok"])
    out["ok"] = bool(
        out["the_charge_regime_is_bounded_in_the_half_treg_cannot_reach_ok"]
        and out["the_reference_state_is_supported_on_every_published_load"]
        and out["published_accessory_budgets_are_unchanged"]
        and out["firmware_floors_are_attainable_ok"]
        and out["the_full_published_pair_is_refused_ok"]
        and out["the_operating_points_satisfy_their_own_equations_ok"]
        and out["the_residual_check_refuses_a_state_that_is_not_a_solution_ok"]
        and out["the_d790_declared_state_is_refused_ok"])
    return out["ok"], out


# --------------------------------------------------------------------------
# F11 -- THE TRANSIENT ACCEPTANCE'S UNCERTAINTY ARITHMETIC, MACHINE-CHECKED.
#
# ADDED AT D-790 / D789-A06.
#
# D-788 wrote the `C-PWR-TRANSIENT-01` acceptance as "the measured value MINUS
# the stated measurement uncertainty on the high side and PLUS it on the low
# side".  That is the wrong sign in both directions: it RELIEVES the margin
# instead of charging it, and Round-9 showed exactly what it costs -- a
# 3.310 V peak with +/-0.020 V of uncertainty reads as 3.290 V and PASSES a
# 3.300 V ceiling it is 10 mV over, and a 2.990 V trough reads as 3.010 V and
# passes a 3.000 V floor it is 10 mV under.  Two failing units per test, both
# accepted.
#
# A sentence in a procedure is the thing that drifted, so the RULE is
# executable here and the procedure's own worked examples are re-derived from
# it on every run.  If the table and the rule ever disagree, F11 FAILS.
TRANSIENT = dict(
    ceiling_V=3.300, floor_V=3.000,
    ceiling_node="J1.40/J1.41/J1.42, the panel's own VDDI/IOVCC/VCI pins",
    floor_node="U1.2",
    basis="the fitted ILI9488's VCI and IOVCC ABSOLUTE MAXIMUM of 3.3 V "
          "(ILI Technology v1.00 Table 41) and the ESP32-S3's own 3.0 V "
          "recommended minimum.  Both are absolute limits, which is why the "
          "acquisition must be DC-coupled or a synchronised DC + AC pair.",
    # The worked examples the procedure prints, and what the RULE says of
    # each.  `expect_ok` is what the table claims; `judge_transient` decides.
    examples=(
        dict(kind="peak", measured_V=3.310, uncertainty_V=0.020,
             expect_ok=False,
             note="the D-788 example: judged 3.290 V and ACCEPTED before"),
        dict(kind="peak", measured_V=3.290, uncertainty_V=0.020,
             expect_ok=False),
        dict(kind="peak", measured_V=3.275, uncertainty_V=0.020,
             expect_ok=True),
        dict(kind="trough", measured_V=2.990, uncertainty_V=0.020,
             expect_ok=False,
             note="the other D-788 example: judged 3.010 V and ACCEPTED"),
        dict(kind="trough", measured_V=3.010, uncertainty_V=0.020,
             expect_ok=False),
        dict(kind="trough", measured_V=3.025, uncertainty_V=0.020,
             expect_ok=True),
    ))
# The phrases the procedure MUST carry, and the one it may never carry again.
TRANSIENT_REQUIRED_TOKENS = (
    "measured peak + total uncertainty < 3.300 V",
    "measured trough \u2212 total uncertainty > 3.000 V",
    "The uncertainty always makes the reading WORSE, never better.",
    "DC-COUPLED, preferred",
    "SYNCHRONISED DC BASELINE + AC DETAIL",
)


# R10-N05, FOUND AT THE D-791 CLOSEOUT -- AND IT IS WHY R10-N04 SURVIVED.
#
# This tuple used to end with two more entries, TYPED OUT AS LITERAL STRINGS:
#
#     "3.85 V** dual-rail floor",
#     "3.50 V** single-rail",
#
# D-789 added them for a good reason -- `f11g` exists so the accessory step
# cannot be rewritten to a pack voltage where the release image refuses the
# rail -- and they were correct on the day they were written.  Then D-791 /
# `D790-A03` moved the floors, and a control aimed by hand at a DERIVED number
# turned into a gate that REQUIRED THE RETIRED NUMBER TO STAY IN THE DOCUMENT.
# Correcting the procedure made F11 fail; leaving F11 alone made the procedure
# wrong.  That is not a stale string, it is a gate holding a defect in place,
# and it is the reason `R10-N04`'s text could not simply be fixed.
#
# The tokens are now FORMATTED FROM THE SAME DERIVATION F12 solves, so the
# procedure and the gate move together and neither can pin the other.
def transient_floor_tokens(floors):
    """The three floor phrases the accessory step must carry, DERIVED."""
    return (
        "%.2f V** retention floor" % floors["retention"],
        "%.2f V** single-rail floor" % floors["single"],
        "%.2f V** dual-rail floor" % floors["dual"],
    )
TRANSIENT_REFUSED_TOKENS = (
    "measured value MINUS the\nstated measurement uncertainty on the high "
    "side and PLUS it on the low side",
)


def judge_transient(kind, measured_V, uncertainty_V, spec=None):
    """D-790 / D789-A06.  The uncertainty is CHARGED, never credited."""
    spec = TRANSIENT if spec is None else spec
    u = abs(uncertainty_V)
    if kind == "peak":
        judged = measured_V + u
        return bool(judged < spec["ceiling_V"]), judged, spec["ceiling_V"]
    judged = measured_V - u
    return bool(judged > spec["floor_V"]), judged, spec["floor_V"]


def judge_transient_procedure(text, spec=None, floors=None):
    """The document and the rule must agree, and the old sign must be gone.

    `floors` carries the three DERIVED accessory floors (R10-N05).  It has no
    default: a missing mapping REFUSES rather than silently dropping the floor
    tokens, because a control that quietly checks less is the failure mode this
    very clause was found in.
    """
    spec = TRANSIENT if spec is None else spec
    rows, ok = [], True
    for ex in spec["examples"]:
        verdict, judged, limit = judge_transient(
            ex["kind"], ex["measured_V"], ex["uncertainty_V"], spec)
        agrees = (verdict == ex["expect_ok"])
        # ...and the judged value must be printed in the document, so the
        # table a human reads is the arithmetic the rule performs.
        printed = ("%.3f V" % judged) in text
        ok = ok and agrees and printed
        rows.append(dict(ex, judged_V=round(judged, 6), limit_V=limit,
                         rule_says_ok=verdict, agrees_with_the_table=agrees,
                         judged_value_is_printed=printed))
    floor_tokens = transient_floor_tokens(floors) if floors else ()
    required = tuple(TRANSIENT_REQUIRED_TOKENS) + floor_tokens
    missing = [x for x in required if x not in text]
    survived = [x for x in TRANSIENT_REFUSED_TOKENS if x in text]
    return dict(
        document="docs/full-beta-v2/assembly/FIRST_FIVE_ASSEMBLY_PLAN.md",
        ceiling_V=spec["ceiling_V"], floor_V=spec["floor_V"],
        ceiling_node=spec["ceiling_node"], floor_node=spec["floor_node"],
        basis=spec["basis"],
        rule=("peak + uncertainty < ceiling; trough - uncertainty > floor.  "
              "D-788's sentence had both signs inverted."),
        worked_examples=rows,
        accessory_floor_tokens=list(floor_tokens),
        accessory_floors_were_supplied=bool(floors),
        missing_required_tokens=missing,
        retired_wording_survived=survived,
        ok=bool(ok and not missing and not survived and text and floors))


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

    def _silicon_hold_diode(n, v):
        # D-789 / D788-11: the charge path is a SCHOTTKY now, and the part
        # that used to be here is the one that must be refused.
        v["D14"] = "1N4148WS"

    def _wrong_tau(n, v):
        v["R132"] = "10k"

    bl_controls = dict(x for x in (
        _control("f5a_refuses_the_gate_collapsed_onto_u17_ctrl", _collapse),
        _control("f5b_refuses_the_hold_capacitor_dropped", _drop_hold_cap),
        _control("f5c_refuses_a_silicon_diode_in_the_charge_path",
                 _silicon_hold_diode),
        _control("f5d_refuses_a_silently_retuned_hold", _wrong_tau)))

    # ---- D-766: and the FET itself, against the ceiling THIS board publishes
    dru_text = DRU.read_text(encoding="utf-8", errors="replace") if DRU.exists() \
        else ""
    # D-789 / D788-11: F5 is judged against the rail THIS BOARD derives, not
    # against a constant.  `mpns` is the schematic's own MPN map, which is what
    # keys the divider's temperature coefficients.
    divider_mpns = schematic_mpns((P3V3_FB["top"], P3V3_FB["bottom"]))
    _bl_env, _bl_err = p3v3_pwm_envelope(values, divider_mpns)
    bl_rail_min_V = _bl_env["heavy_lo"] if _bl_env else BL_RAIL_MIN_FALLBACK_V
    fet_ok, fet = judge_backlight_fet(values, dru_text, bl_rail_min_V)
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
        ok, _ = judge_backlight_fet(v2, dru_text, bl_rail_min_V)
        return name, not ok

    def _fet_control_dru(name, text):
        ok, _ = judge_backlight_fet(values, text, bl_rail_min_V)
        return name, not ok

    def _fet_control_rail(name, rail_V):
        """D-789 / D788-11: the RAIL is an input to F5 now, so a rail that
        cannot hold the gate must be refused by the same expression."""
        ok, _ = judge_backlight_fet(values, dru_text, rail_V)
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
                     lambda v: v.__setitem__(BL_FET, "AO3422")),
        # ---- D-789 / D788-11.  THE HELD GATE IS AN OUTPUT OF THE RAIL. -----
        # THE LOAD-BEARING ONE: the D-787/D-788 board, unchanged but for the
        # hold diode.  At this rail the 1N4148WS's LOWEST published forward
        # drop (715 mV at 1 mA) leaves the held VGS at 1.4865 V, 13.5 mV under
        # the SQ2364EES's only published conduction row.  Nothing else moves.
        _fet_control("f5n_refuses_the_1n4148ws_d788_left_fitted_at_this_rail",
                     lambda v: v.__setitem__(BL_HOLD_DIODE, "1N4148WS")),
        _fet_control("f5o_refuses_a_hold_diode_with_no_published_rating",
                     lambda v: v.__setitem__(BL_HOLD_DIODE, "SOME-DIODE-77")),
        # AND THE CLAUSE MUST MOVE WITH THE RAIL.  The D788-11 defect was a
        # CONSTANT, so the control that matters is that the derived gate is a
        # FUNCTION of the rail at all, and that there is a rail at which it
        # refuses.  `held_gate_breakeven_rail_V` prints where that is.
        _fet_control_rail("f5p_refuses_the_rail_below_the_gate_breakeven",
                          fet.get("held_gate_breakeven_rail_V", 0.0) - 0.01),
        _fet_control("f5q_refuses_a_hold_capacitor_too_small_for_the_schottky_leak",
                     lambda v: v.__setitem__("C85", "100nF X7R"))))
    # A POSITIVE non-vacuity claim beside the refusals: the derived gate is a
    # FUNCTION of the rail, which is exactly what D-788's constant was not.
    fet_controls["f5r_the_derived_gate_tracks_the_rail"] = bool(
        judge_backlight_fet(values, dru_text, bl_rail_min_V)[1]["held_gate_V"]
        != judge_backlight_fet(values, dru_text,
                               bl_rail_min_V - 0.5)[1]["held_gate_V"])

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
    rm = re.search(r"kAccessoryRetentionFloorV\s*=\s*([0-9.]+)f", policy_text)
    policy_single = float(sm.group(1)) if sm else float("nan")
    policy_dual = float(dm.group(1)) if dm else float("nan")
    # D-791 / D790-A03: the THIRD constant, and the one retention is judged at.
    policy_retention = float(rm.group(1)) if rm else float("nan")
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

    env_ok, env = judge_accessory_envelope(
        values, single_floor=policy_single, dual_floor=policy_dual,
        retention_floor=policy_retention,
        live_ohms=live_ohms, mpns=divider_mpns)
    env["normal_operation"]["firmware_policy_file"] = str(
        POWER_POLICY.relative_to(ROOT)) if POWER_POLICY.exists() else None
    env["normal_operation"]["measurement_contacts"] = measurement_nets
    env["normal_operation"]["measurement_point_is_bat_protected_p"] = measurement_ok
    env["normal_operation"]["firmware_policy_parsed"] = (
        math.isfinite(policy_single) and math.isfinite(policy_dual)
        and math.isfinite(policy_retention))
    env["battery_connection"]["internal_feature_reserve"] = "not required by D-781 rated harness"
    env["normal_operation"]["live_paths_measured_off_the_board"] = True
    env_ok = (env_ok and measurement_ok
              and math.isfinite(policy_single) and math.isfinite(policy_dual)
              and math.isfinite(policy_retention))

    # ---- F12: THE COMPLETE CELL-TO-LOAD NETWORK (D-791 / D790-A03) --------
    # Solved with the SAME live path resistances, the SAME derived rail
    # voltages and the SAME switch RONs F6 just used, so the two clauses
    # cannot describe different boards.
    _no = env["normal_operation"]
    cell_net_ok, cell_net = judge_cell_to_load(
        live_ohms, _no["v_3v3_used_V"], _no["v_acc5v_used_V"],
        _no["accessory_switch_ron_ohm"]["ACC_3V3"],
        _no["accessory_switch_ron_ohm"]["ACC_5V"])
    cell_net["firmware_policy"] = dict(
        file=str(POWER_POLICY.relative_to(ROOT)) if POWER_POLICY.exists() else None,
        retention_floor_V=policy_retention,
        enable_first_rail_floor_V=policy_single,
        enable_second_rail_floor_V=policy_dual)
    df = cell_net["derived_floors"]
    # ---- D-792 / R11-04.  THE PERMISSION TABLE IS PINNED, ROW BY ROW.
    #
    # The two scalars above are the published ENVELOPE of the table; the
    # firmware consults the TABLE, so the table is what has to be pinned.  The
    # header carries sixteen values as eight `{one_rail, two_rails}` rows, and
    # each is compared to what the derivation above produced -- including the
    # SENTINEL rows, because a refusal encoded as a large number is the
    # D790-A03 defect wearing a new hat.  The parse is deliberately literal: a
    # row that stops being parseable fails rather than being skipped.
    _sent = re.search(r"kAccessoryNotPermittedV\s*=\s*([0-9.]+)f", policy_text)
    policy_sentinel = float(_sent.group(1)) if _sent else float("nan")

    def _parse_rows(array_name):
        src = re.search(
            r"static const AccessoryPermissionRow %s\[8\] = \{(.*?)\n  \};"
            % array_name, policy_text, re.S)
        out = []
        if not src:
            return out
        for line in src.group(1).splitlines():
            m = re.search(
                r"\{\s*([A-Za-z0-9_.]+f?)\s*,\s*([A-Za-z0-9_.]+f?)\s*\}", line)
            if not m:
                continue

            def val(tok):
                if tok.startswith("kAccessoryNotPermittedV"):
                    return None
                return float(tok.rstrip("f"))
            out.append((val(m.group(1)), val(m.group(2))))
        return out

    _edges = (("rail", "kRailRows", df["rail_edge_table"]),
              ("mode", "kModeRows", df["mode_edge_table"]))
    _table_rows, _table_ok, _parsed = [], True, {}
    for _edge, _array, _derived in _edges:
        _fw_rows = _parse_rows(_array)
        _parsed[_array] = len(_fw_rows)
        _table_ok = _table_ok and len(_fw_rows) == 8
        _by_bits = {}
        for _r in _derived:
            _by_bits.setdefault(_r["mode_bits"], {})[_r["rails"]] = (
                _r["floor_gridded_V"] if _r["permitted"] else None)
        for _bits in range(8):
            _d = _by_bits.get(_bits, {})
            _fw = _fw_rows[_bits] if _bits < len(_fw_rows) else (None, None)
            _row = dict(edge=_edge, array=_array, mode_bits=_bits,
                        modes=[m for m in df["mode_names"]
                               if _bits & (1 << df["mode_names"].index(m))],
                        firmware_one_rail_V=_fw[0],
                        derived_one_rail_V=_d.get(1),
                        firmware_two_rails_V=_fw[1],
                        derived_two_rails_V=_d.get(2),
                        ok=bool(_fw[0] == _d.get(1) and _fw[1] == _d.get(2)))
            _table_ok = _table_ok and _row["ok"]
            _table_rows.append(_row)
    # AND THE TWO EDGES MUST NOT HAVE BEEN COLLAPSED.  If the mode edge ever
    # equalled the rail edge everywhere, one of them would be wrong: the whole
    # point is that a mode is entered from a lighter pre-state.
    _edges_differ = any(
        r["derived_one_rail_V"] is not None
        and next((q["derived_one_rail_V"] for q in _table_rows
                  if q["edge"] == "rail" and q["mode_bits"] == r["mode_bits"]),
                 None) != r["derived_one_rail_V"]
        for r in _table_rows if r["edge"] == "mode")
    cell_net["firmware_permission_table_equals_the_derivation"] = dict(
        file=str(POWER_POLICY.relative_to(ROOT)) if POWER_POLICY.exists() else None,
        rows=_table_rows,
        rows_parsed=_parsed,
        sentinel_V=policy_sentinel,
        sentinel_is_above_the_all_ones_code=bool(
            math.isfinite(policy_sentinel) and policy_sentinel > 5.1199),
        refused_rows=sum(1 for r in _table_rows
                         if r["derived_one_rail_V"] is None),
        the_two_edges_are_not_the_same_table=_edges_differ,
        ok=bool(_table_ok and math.isfinite(policy_sentinel)
                and policy_sentinel > 5.1199 and _edges_differ),
        why="the firmware consults the TABLES, so the TABLES are pinned -- all "
            "thirty-two values, sentinels included, on both arrival edges.  A "
            "refusal encoded as a large float would read as a restriction and "
            "behave as a rail that never turns on, which is D790-A03 exactly; "
            "and two edges collapsed into one table is either unsound (the "
            "mode edge granted on a floor derived from a heavier pre-state) "
            "or unreachable (the rail edge held to a floor its own pre-state "
            "cannot report).")
    cell_net["firmware_permission_table_equals_the_derivation_ok"] = bool(
        cell_net["firmware_permission_table_equals_the_derivation"]["ok"])
    cell_net["firmware_constants_equal_the_derivation"] = dict(
        retention=dict(firmware=policy_retention,
                       derived=df["retention_floor_gridded_V"]),
        enable_first=dict(firmware=policy_single,
                          derived=df["enable_first_rail_floor_gridded_V"]),
        enable_second=dict(firmware=policy_dual,
                           derived=df["enable_second_rail_floor_gridded_V"]),
        why="EQUAL, not merely at-or-above.  A floor ABOVE the derivation is "
            "not automatically safe here: D790-A03's whole finding is that an "
            "unreachably high floor sheds a rail the product publishes, on a "
            "full pack.  Too high and too low are both defects, so the gate "
            "pins the constant to the number it derives.",
        ok=bool(policy_retention == df["retention_floor_gridded_V"]
                and policy_single == df["enable_first_rail_floor_gridded_V"]
                and policy_dual == df["enable_second_rail_floor_gridded_V"]))
    cell_net["firmware_constants_equal_the_derivation_ok"] = bool(
        cell_net["firmware_constants_equal_the_derivation"]["ok"])
    # ---- D-791 / D790-A08.  THE DERIVED POLICY MUST BE PRINTED WHERE A
    # HUMAN READS IT, AND IT MUST BE THE SAME NUMBER.
    #
    # The rule R7-N04 applied to the Community-Port figures and D-789 / R8-N06
    # applied to the backlight hold: a contract that only lives in a gate is
    # not published, and one that only lives in a document is not proven.  The
    # three floors, the reference state and every state's derived cell floor
    # are FORMATTED FROM THE COMPUTED VALUES, so a derivation that moves drags
    # the document with it.
    _spec_txt = (DEVICE_SPEC.read_text(encoding="utf-8", errors="replace")
                 if DEVICE_SPEC.exists() else "")
    charge_split = cell_net["charge_regime"]
    _need = {
        "retention_floor": "**%.2f V**" % df["retention_floor_gridded_V"],
        "enable_first_rail_floor": "**%.2f V**"
                                   % df["enable_first_rail_floor_gridded_V"],
        "enable_second_rail_floor": "**%.2f V**"
                                    % df["enable_second_rail_floor_gridded_V"],
        "first_rail_node_step": "**%.4f V**"
                                % df["worst_first_rail_node_step_V"],
        "second_rail_node_step": "**%.4f V**"
                                 % df["worst_second_rail_node_step_V"],
        "reference_state": "`%s`" % cell_net["reference_state_key"],
    }
    # ---- D-792 / R11-03 + R11-04.  WHAT THE DOCUMENT NOW HAS TO CARRY.
    #
    # D-791 required DEVICE_SPEC to print the charge regime's junction and
    # ambient AT THE REFERENCE STATE, and with the physical solver in place
    # that junction is 225.8 C -- a state the part cannot be in.  Publishing it
    # as a headline would be publishing a thermal shutdown as an operating
    # point, which is precisely what R11-03 forbids.  What the document must
    # carry instead is the DERIVED CEILING and the state that sits under it:
    # the heaviest permitted-while-charging combination, its junction, and the
    # supervised ambient at which the internal air reaches the pouch's own
    # charge window.
    _cc = cell_net["the_charge_regime_is_bounded_in_the_half_treg_cannot_reach"][
        "load_ceiling"]
    _need["charge_system_W_ceiling"] = "**%.3f W**" % _cc["system_W_ceiling"]
    _heaviest = max(_cc["permitted_while_charging"], key=lambda r: r["system_W"])
    _need["charge_heaviest_permitted_state"] = "`%s` + `%s`" % (
        _heaviest["state"], _heaviest["load"])
    _need["charge_junction_folded_back"] = "**%.1f \u00b0C**" % _heaviest[
        "junction_with_charge_folded_back_C"]
    _need["charge_ambient_ceiling"] = "**%.1f \u00b0C**" % _heaviest[
        "charge_ambient_ceiling_C"]
    # ...and the DECLARED SIMULTANEOUS PAIR, which is the new product contract.
    _dp = df["declared_simultaneous_pair"]
    _need["declared_simultaneous_pair"] = "**%d mA** + **%d mA**" % (
        round(_dp["acc_3v3_A"] * 1000), round(_dp["acc_5v_A"] * 1000))
    _need["full_pair_ambient_ceiling"] = "**%.1f \u00b0C**" % _dp[
        "full_pair_ambient_ceiling_C"]
    # Each state's cell floor is quoted for the SIMULTANEOUS load the product
    # publishes -- the declared pair -- and the FULL pair's refusal is a
    # separate, explicit statement.
    for _st in cell_net["states"]:
        _b = _st["loads"]["both_rails_at_the_declared_pair"]
        _need["cell_floor_" + _st["key"]] = (
            "**%.3f V**" % _b["lowest_supported_cell_ocv_V"]
            if _b["supported"] else "**not supported**")
    _missing = sorted(k for k, t in _need.items() if t not in _spec_txt)
    cell_net["published_policy_is_printed_in_device_spec"] = dict(
        document=str(DEVICE_SPEC.relative_to(ROOT)),
        required=_need, missing=_missing,
        ok=bool(_spec_txt) and not _missing,
        method="R7-N04's rule, applied to the VCELL policy and the supported "
               "concurrency table: every floor, every node step, the reference "
               "state's NAME and each state's derived cell floor must appear "
               "in the product-facing document, formatted from the computed "
               "values.  D-790's 3.50/3.85 V pair sat in this document while "
               "the node could not reach it, and no clause could see that.")
    cell_net["published_policy_is_printed_in_device_spec_ok"] = bool(
        cell_net["published_policy_is_printed_in_device_spec"]["ok"])
    cell_net_ok = cell_net_ok and cell_net[
        "published_policy_is_printed_in_device_spec_ok"]

    # ---- D-792 / R11-05.  THE FAB NOTES ARE NORMATIVE PROSE TOO, AND NOTHING
    # WAS READING THEM.
    #
    # ROUND-11, IN ITS OWN WORDS: "Current FAB notes still contain old accessory
    # delivery numbers and old sustained/thermal claims.  Prefer generated
    # normative values from canonical model outputs rather than hand-repeating
    # calculated numbers."
    #
    # THE SHAPE IS THE ONE THIS PROGRAMME HAS NOW HIT THREE TIMES.  R7-N04 found
    # a contract that lived only in a gate; D-789 / R8-N06 found one that lived
    # only in a document; R10-N04 found the first-article procedure choosing
    # bench voltages from floors that had been retired.  Each was fixed for ONE
    # file.  `AQROOT_DEMO_FAB_HANDOFF.md` is the document a fabricator and an
    # assembler actually read first, and no clause had ever looked at it.  It
    # does now, with the same rule: every value below is FORMATTED FROM THE
    # COMPUTED ONE, so a derivation that moves drags the handoff with it.
    _fab_doc = ROOT / "docs/full-beta-v2/AQROOT_DEMO_FAB_HANDOFF.md"
    _fab_txt = (_fab_doc.read_text(encoding="utf-8", errors="replace")
                if _fab_doc.exists() else "")
    _up = apm.upstream_report()
    _fab_need = {
        "retention_floor": "**%.2f V**" % df["retention_floor_gridded_V"],
        "enable_first_rail_floor": "**%.2f V**"
                                   % df["enable_first_rail_floor_gridded_V"],
        "enable_second_rail_floor": "**%.2f V**"
                                    % df["enable_second_rail_floor_gridded_V"],
        "declared_simultaneous_pair": "**%d mA + %d mA**" % (
            round(_dp["acc_3v3_A"] * 1000), round(_dp["acc_5v_A"] * 1000)),
        "full_pair_ambient_ceiling": "**%.1f \u00b0C**"
                                     % _dp["full_pair_ambient_ceiling_C"],
        "internal_3v3_peak_envelope": "**%.6f A**" % apm.peak_A(),
        "harness_itemised_max": "**%.3f m\u03a9**"
                                % (_up["harness_hot_aged_max_ohm"] * 1000.0),
        "upstream_fixed_max": "**%.3f m\u03a9**"
                              % (_up["fixed_series_max_ohm"] * 1000.0),
        "charge_system_W_ceiling": "**%.3f W**" % _cc["system_W_ceiling"],
        "charge_junction_folded_back": "**%.1f \u00b0C**" % _heaviest[
            "junction_with_charge_folded_back_C"],
        "charge_ambient_ceiling": "**%.1f \u00b0C**" % _heaviest[
            "charge_ambient_ceiling_C"],
        "backlight_inductor_dcr_max": "**%.1f m\u03a9**" % (
            apm.BACKLIGHT_BOOST["inductor_dcr_ohm"] * 1000.0),
    }
    _fab_missing = sorted(k for k, t in _fab_need.items()
                          if t not in _fab_txt)
    cell_net["published_policy_is_printed_in_the_fab_handoff"] = dict(
        document=str(_fab_doc.relative_to(ROOT)),
        required=_fab_need, missing=_fab_missing,
        ok=bool(_fab_txt) and not _fab_missing,
        method="R11-05.  The document a fabricator reads FIRST had never been "
               "read by a gate.  Every value here is formatted from the "
               "canonical model's own output, so the handoff cannot carry a "
               "retired accessory-delivery figure or a retired thermal claim "
               "as CURRENT text.  Historical values remain legal below an "
               "explicit HISTORICAL banner; this clause is about the current "
               "block.")
    cell_net["published_policy_is_printed_in_the_fab_handoff_ok"] = bool(
        cell_net["published_policy_is_printed_in_the_fab_handoff"]["ok"])
    cell_net_ok = cell_net_ok and cell_net[
        "published_policy_is_printed_in_the_fab_handoff_ok"]
    cell_net_ok = cell_net_ok and cell_net["firmware_constants_equal_the_derivation_ok"]
    cell_net_ok = cell_net_ok and cell_net[
        "firmware_permission_table_equals_the_derivation_ok"]

    # ---- R10-N04, FOUND AT THE D-791 CLOSEOUT.  THE PROCEDURE A TECHNICIAN
    # ACTUALLY EXECUTES QUOTES THESE FLOORS TOO, AND NOTHING READ IT.
    #
    # The clause above closed D790-A08's shape for DEVICE_SPEC: the floors are
    # formatted from the computed values, so a derivation that moves drags the
    # product-facing document with it.  It reaches exactly ONE file.  D-791
    # moved the pair 3.50/3.85 V to the triple 3.20/3.55/3.65 V and
    # `FIRST_FIVE_ASSEMBLY_PLAN` §7b -- the `C-PWR-TRANSIENT-01` accessory
    # step, which CHOOSES ITS TEST VOLTAGES FROM THESE FLOORS -- still named
    # the retired pair.  That is worse than a stale sentence: the bench points
    # were selected to sit above floors that no longer exist, so the procedure
    # sent a technician to take acceptance data at a pack voltage where the
    # release image's permission is no longer what the text claims.  It is the
    # SAME defect D-789/D788-18 already fixed once in this very section, and
    # a floor change reintroduced it because no gate was reading the file.
    #
    # THE CHECK IS DERIVED IN BOTH DIRECTIONS, which is the only form that
    # survives the next move of the derivation:
    #   * PRESENCE -- all three gridded floors must appear, formatted from the
    #     computed values;
    #   * CONTRADICTION -- an UNFENCED line that talks about an ACCESSORY or
    #     RAIL or RETENTION floor may not quote a `N.NN V` value that is not
    #     one of the three.  A fenced line may: a procedure must be able to
    #     record what the floor used to be and why the step moved;
    #   * COMPLETENESS -- the paragraph that forbids relaxing the floors must
    #     name ALL THREE constants.  It named two, and D-791 added the third,
    #     so the constant that decides RETENTION -- the one R10-N01 is about --
    #     was the one the prohibition did not cover.
    _fa_txt = (FIRST_FIVE_ASSEMBLY.read_text(encoding="utf-8", errors="replace")
               if FIRST_FIVE_ASSEMBLY.exists() else "")
    _fa_floors = {
        "retention_floor": df["retention_floor_gridded_V"],
        "enable_first_rail_floor": df["enable_first_rail_floor_gridded_V"],
        "enable_second_rail_floor": df["enable_second_rail_floor_gridded_V"],
    }
    _fa_allowed = {"%.2f" % v for v in _fa_floors.values()}
    _fa_need = {k: "%.2f V" % v for k, v in _fa_floors.items()}
    _fa_absent = sorted(k for k, t in _fa_need.items() if t not in _fa_txt)
    # A DECISION NUMBER IS NOT A SUPERSESSION MARKER.  The first draft of this
    # clause carried "D-788"/"D-789"/"D-790" as fences and they silently
    # exempted the worst sentence in the file -- "the derived VCELL policy is
    # 3.50 V single-rail and 3.85 V dual-rail", which states the CURRENT policy
    # and states it wrongly, inside a paragraph that merely CITES D-788.  Only
    # words that actually mark text as no-longer-true may fence it.
    # ...AND NEITHER IS THE WORD "was".  The second draft fenced on "was " and
    # that exempted the same sentence a second time, through "the accessory
    # step WAS WRITTEN to run at..." -- ordinary narration, not a supersession
    # marker.  The fence must be a word whose only job is to mark text as
    # no-longer-true, so the prose that records history has to say so.
    _FA_FENCE = ("SUPERSEDE", "supersede", "HISTORICAL", "historical",
                 "RETIRED", "retired", "no longer", "formerly",
                 "REPLACED", "replaced", "used to", "until D-", "before D-")
    # THE NUMBER IS BOUND TO THE CLAIM, NOT TO THE LINE.  Two things make a
    # line scan the wrong instrument here.  This document HARD-WRAPS, so "the
    # **3.50 V** single-rail / floor" straddles two lines and a per-line scan
    # reads neither half; and a legitimate step sentence quotes BENCH
    # setpoints (4.15 V, 3.75 V, 3.60 V) beside the floors, so "every voltage
    # in a floor sentence must be a floor" would refuse correct text.  What is
    # policed is therefore the ASSERTION `<value> is the <which> floor`, in
    # either word order, over whitespace-normalised SENTENCES.
    _FA_WHICH = r"(?:single-rail|dual-rail|retention)"
    _FA_CLAIMS = (
        re.compile(r"(\d\.\d{2})\s*V\**[^.]{0,40}?" + _FA_WHICH
                   + r"(?:-rail)?\s*floor", re.I),
        re.compile(r"(\d\.\d{2})\s*V\**\s*(?:single-rail|dual-rail)\b", re.I),
        re.compile(_FA_WHICH + r"(?:-rail)?\s*floor[^.]{0,40}?(\d\.\d{2})\s*V",
                   re.I),
    )
    _fa_flat = re.sub(r"\s+", " ", _fa_txt)
    _fa_contradictions = []
    for _sent in re.split(r"(?<=[.;:])\s+", _fa_flat):
        if any(f in _sent for f in _FA_FENCE):
            continue
        _hit = sorted({_tok for _rx in _FA_CLAIMS for _tok in _rx.findall(_sent)
                       if _tok not in _fa_allowed})
        for _tok in _hit:
            _fa_contradictions.append(dict(
                quoted="%s V" % _tok, sentence=_sent.strip()[:200]))
    _FA_CONSTANTS = ("kAccessoryRetentionFloorV", "kAccessorySingleRailFloorV",
                     "kAccessoryDualRailFloorV")
    _fa_unnamed = [c for c in _FA_CONSTANTS if c not in _fa_txt]
    cell_net["published_policy_is_consistent_in_the_first_article_procedure"] = dict(
        document=str(FIRST_FIVE_ASSEMBLY.relative_to(ROOT)),
        required=_fa_need, absent=_fa_absent,
        contradictions=_fa_contradictions,
        protected_constants=list(_FA_CONSTANTS), constants_not_named=_fa_unnamed,
        fence_tokens=list(_FA_FENCE),
        claim_patterns=[r.pattern for r in _FA_CLAIMS],
        ok=bool(_fa_txt) and not _fa_absent and not _fa_contradictions
           and not _fa_unnamed,
        method="R10-N04.  The first-article procedure SELECTS ITS BENCH "
               "VOLTAGES FROM THESE FLOORS, so a floor that moves without it "
               "sends a technician to a pack voltage where the release image's "
               "permission is not what the step claims.  All three gridded "
               "floors must be PRESENT, formatted from the computed values; no "
               "UNFENCED line about an accessory/rail/retention floor may "
               "quote a different one; and the paragraph forbidding a relaxed "
               "build must name all three constants, including the retention "
               "constant D-791 added.")
    cell_net["published_policy_is_consistent_in_the_first_article_procedure_ok"] = bool(
        cell_net["published_policy_is_consistent_in_the_first_article_procedure"]["ok"])
    cell_net_ok = cell_net_ok and cell_net[
        "published_policy_is_consistent_in_the_first_article_procedure_ok"]

    # ---- F12's own controls.  Every one of them has to REFUSE. -----------
    def _cell(**over):
        return judge_cell_to_load(
            over.pop("paths", live_ohms),
            over.pop("v3", _no["v_3v3_used_V"]),
            over.pop("v5", _no["v_acc5v_used_V"]),
            over.pop("ron3", _no["accessory_switch_ron_ohm"]["ACC_3V3"]),
            over.pop("ron5", _no["accessory_switch_ron_ohm"]["ACC_5V"]),
            **over)

    _better_pair = dict(PASS_PAIR, rds_on_max_at_that_row_ohm=0.008,
                        rds_on_lowest_published_vgs_V=1.8)
    _worse_pair = dict(PASS_PAIR, rds_on_max_at_that_row_ohm=0.200)
    cell_net_controls = dict(
        # THE LOAD-BEARING ONE.  The refusal of D-790's declared state must be
        # a property of the PHYSICS, not a hard-coded verdict: give the board a
        # pass pair an order of magnitude better and the same state becomes
        # supportable, which proves the clause is measuring something.
        # D-792 RE-AIMED THIS, AND THE RE-AIM IS THE FINDING.  A better pass
        # pair ALONE no longer flips the refusal, because with R11-07's itemised
        # battery path and R11-02's processor baseline the binding limit at
        # D-790's declared state is no longer the pass pair at all -- it is the
        # enclosure's internal air against the pouch's own discharge window.
        # The subject is also corrected: the clause now asks whether the state
        # can carry ANY published accessory load, not just the retired full
        # pair -- a column that is refused by construction could never flip and
        # would make this control unfalsifiable.  THREE perturbations are run,
        # and each one flips the verdict on its own, which is what makes the
        # refusal a measurement of the physics rather than a hard-coded verdict:
        # a pass pair an order of magnitude better, a 0 C ambient, and both.
        f12a_the_d790_refusal_is_physics_not_a_hard_coded_verdict=bool(
            not _cell(pass_pair=_better_pair, ambient_C=0.0)[1][
                "the_d790_declared_state_is_refused_ok"]),
        f12a2_a_better_pass_pair_alone_flips_it=bool(
            not _cell(pass_pair=_better_pair)[1][
                "the_d790_declared_state_is_refused_ok"]),
        f12a3_a_cool_ambient_alone_flips_it=bool(
            not _cell(ambient_C=0.0)[1][
                "the_d790_declared_state_is_refused_ok"]),
        # ...and a materially worse pass pair must take the REFERENCE state
        # down with it.
        f12b_refuses_a_pass_pair_that_cannot_carry_the_reference_state=bool(
            not _cell(pass_pair=_worse_pair)[0]),
        # ...and a BATOCP band at TI's stated 18 % rather than the declared
        # wider one must CHANGE the answer somewhere, or the assumption is
        # decorative.
        f12c_the_declared_wider_ocp_band_is_load_bearing=bool(
            _cell(ocp_min_A=IBAT_OCP_TYP_A * (1 - IBAT_OCP_STATED_ACCURACY))[1][
                "states"] != cell_net["states"]),
        # ...and a floor the node cannot reach must be caught.  Doubling the
        # upstream copper drops the node without changing the floors' basis.
        f12d_refuses_an_unattainable_floor=bool(
            not _cell(paths=dict(live_ohms,
                                 bat_protected_p=live_ohms[
                                     "bat_protected_p"] * 8.0))[0]),
        # ...and the firmware constants must be PINNED, not merely bounded.
        f12e_refuses_a_firmware_floor_above_the_derivation=bool(
            policy_dual + FLOOR_GRID_V != df["enable_second_rail_floor_gridded_V"]),
        f12f_refuses_a_firmware_floor_below_the_derivation=bool(
            policy_retention - FLOOR_GRID_V != df["retention_floor_gridded_V"]),
        # ...and the gauge error must be CHARGED: a floor derived without it
        # would sit exactly on the BUVLO bound.
        f12g_the_gauge_error_is_charged_to_every_floor=bool(
            df["retention_floor_V"] > BUVLO_BOUND_V
            and abs(df["retention_floor_V"] - BUVLO_BOUND_V
                    - GAUGE_VERR_V - GAUGE_LSB_V) < 1e-6),
        # ...and each ENABLE floor must genuinely anticipate its own rail's
        # node step rather than collapsing onto the retention floor.
        #
        # D-792 RE-AIMED THE SECOND HALF.  D-791 asserted that the SECOND-rail
        # step is larger than the first, which was true when the second-rail
        # post state was both rails at their FULL published budgets.  It is no
        # longer: the second-rail post state is the DECLARED PAIR -- 220 mA +
        # 170 mA -- which is a LIGHTER load than one rail at its full 400 mA, so
        # the second step is legitimately the smaller of the two.  Asserting the
        # old ordering would now be asserting an arithmetic accident.  What
        # remains load-bearing is that BOTH steps are real, that neither has
        # collapsed onto the retention floor, and that the two are DISTINCT --
        # an identical pair would mean one of them was not being solved.
        f12h_each_enable_floor_anticipates_its_own_rail_step=bool(
            df["worst_first_rail_node_step_V"] > 0.05
            and df["worst_second_rail_node_step_V"] > 0.05
            and abs(df["worst_second_rail_node_step_V"]
                    - df["worst_first_rail_node_step_V"]) > 1e-6
            and df["enable_first_rail_floor_gridded_V"]
            > df["retention_floor_gridded_V"] + 0.05
            and df["enable_second_rail_floor_gridded_V"]
            > df["retention_floor_gridded_V"] + 0.05))
    cell_net_ok = cell_net_ok and all(cell_net_controls.values())

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
        # D-789 / D788-12.  The ripple term must be LARGER once the published
        # accessory budget joins U12's output load.  A ripple that does not
        # move when 400 mA is added to the converter is the D-788 defect.
        "f6ag_ripple_grows_with_the_accessory_output_load": (
            p3v3_ac_envelope(
                env["p3v3_setpoint"]["pwm_heavy_min_V"],
                env["p3v3_setpoint"]["worst_case_rail_max_V"],
                I_INTERNAL)["ripple_pp_V"]
            > p3v3_ac_envelope(
                env["p3v3_setpoint"]["pwm_heavy_min_V"],
                env["p3v3_setpoint"]["worst_case_rail_max_V"],
                I_INTERNAL, accessory_load_A=0.0)["ripple_pp_V"]),
    }
    ac["ok"] = bool(ac_ok and all(ac["controls_refused"].values()))
    env["p3v3_ac_envelope_and_centring"] = ac
    env_ok = env_ok and ac["ok"]

    # ---- D-788 / R7-N04: the PUBLISHED contract must be the DERIVED one ----
    spec_text = (DEVICE_SPEC.read_text(encoding="utf-8", errors="replace")
                 if DEVICE_SPEC.exists() else "")
    published_tokens = {
        # D-789 / D788-02 + F-N02: the DERIVED minimum, not a constant.
        "connector_minimum_V": "%.2f V" % env["p3v3_setpoint"][
            "published_connector_min_V"],
        # D-789 / D788-02: the connection contract, published beside the
        # unconditional guarantee rather than instead of it.
        "connector_minimum_fully_mated_V": "%.6f V" % env["p3v3_setpoint"][
            "delivered_at_400mA_fully_mated_V"],
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

    # ---- D-789 / D788-02: the published minimum IS the derived one -------
    p3 = env["p3v3_setpoint"]
    grid = PUBLISHED_CONNECTOR_MIN_GRID_V
    expected_pub = math.floor(p3["delivered_at_400mA_min_V"] / grid) * grid
    env["p3v3_published_minimum_is_the_derived_one"] = dict(
        derived_worst_mode_V=p3["delivered_at_400mA_min_V"],
        worst_mode=p3["worst_mode"],
        grid_V=grid,
        published_V=p3["published_connector_min_V"],
        expected_V=round(expected_pub, 6),
        # An OVER-promise (published above what is derived) and an
        # UNDER-promise of more than one grid step are both refused: the first
        # is dishonest, the second means the published figure has stopped
        # tracking the design.
        ok=bool(abs(p3["published_connector_min_V"] - expected_pub) < 1e-9),
        why="the product-facing minimum is the WORST permitted wiring x load "
            "mode rounded DOWN onto a 10 mV grid, and nothing in this file "
            "asserts it")
    env["p3v3_owner_decision_class_anchor"] = dict(
        authority=PUBLISHED_CONNECTOR_MIN_AUTHORITY,
        nominal_class_V=PUBLISHED_CONNECTOR_NOMINAL_CLASS_V,
        class_tolerance_V=PUBLISHED_CONNECTOR_CLASS_TOLERANCE_V,
        raw_pwm_nominal_V=p3["raw_pwm_V"][1],
        deviation_from_class_mV=round(
            (p3["raw_pwm_V"][1] - PUBLISHED_CONNECTOR_NOMINAL_CLASS_V) * 1000,
            3),
        ok=bool(abs(p3["raw_pwm_V"][1] - PUBLISHED_CONNECTOR_NOMINAL_CLASS_V)
                <= PUBLISHED_CONNECTOR_CLASS_TOLERANCE_V + 1e-9),
        why="D-788 Option A publishes the rail as APPROXIMATELY 3.2 V nominal "
            "and leaves the exact figure to be derived.  100 mV is this "
            "contract's reading of 'approximately': the fitted divider's "
            "nominal must stay inside it, so a divider change that moved the "
            "rail out of the class the owner approved would need a new owner "
            "decision rather than passing quietly")
    env["p3v3_clears_its_tightest_on_board_consumer"] = dict(
        part=ACC_3V3_ONBOARD_FLOOR_PART,
        floor_V=ACC_3V3_ONBOARD_FLOOR_V,
        basis=ACC_3V3_ONBOARD_FLOOR_BASIS,
        worst_delivered_V=p3["delivered_at_400mA_min_V"],
        margin_mV=round((p3["delivered_at_400mA_min_V"]
                         - ACC_3V3_ONBOARD_FLOOR_V) * 1000, 3),
        ok=bool(p3["delivered_min_ok"]))
    env["u20_ron_is_bounded_at_its_own_input"] = dict(
        u20_vin_V=p3["u20_vin_V"],
        ron_bound_ohm=p3["u20_ron_bound_ohm"],
        basis=p3["u20_ron_bound_basis"],
        in_published_range=p3["u20_vin_is_in_the_published_range"],
        ok=bool(p3["u20_vin_is_in_the_published_range"]))
    # ---- D-790 / D789-A11: the display line is DERIVED, and its declared
    # converter input is at or below the rail the same model produces -------
    modelled_u17_vin = p3["pwm_heavy_min_V"] - p3["source_drop_mV"] / 1000.0
    env["display_backlight_is_derived_not_inherited"] = dict(
        declared_converter_vin_V=BACKLIGHT_BOOST["declared_converter_vin_V"],
        declared_converter_vin_basis=BACKLIGHT_BOOST[
            "declared_converter_vin_basis"],
        modelled_rail_at_u17_vin_V=round(modelled_u17_vin, 6),
        headroom_mV=round(
            (modelled_u17_vin
             - BACKLIGHT_BOOST["declared_converter_vin_V"]) * 1000, 3),
        model=BACKLIGHT_INPUT,
        panel_logic_declared_mA=PANEL_LOGIC_DECLARED_mA,
        retired_inherited_subtotal_mA=181.0,
        why="the old single 181 mA 'display logic + backlight' line was an "
            "FBV2-COMM-001 subtotal that was smaller than the BACKLIGHT "
            "alone.  The backlight half is now solved from published maxima "
            "and the panel half is a labelled DECLARED allowance",
        ok=bool(
            modelled_u17_vin
            >= BACKLIGHT_BOOST["declared_converter_vin_V"] - 1e-9
            and BACKLIGHT_INPUT["led_current_is_inside_the_panel_maximum"]
            and BACKLIGHT_INPUT["model_efficiency_is_under_the_headline"]
            and BACKLIGHT_INPUT["bound_A"]
            >= BACKLIGHT_INPUT["ti_headline"]["input_A"] - 1e-12))
    # ---- D-790 / D789-A03: no common edge is inside a paralleled branch ---
    fm_ok = True
    if p3.get("fully_mated_contract"):
        for name, cell in p3["fully_mated_contract"].items():
            if not isinstance(cell, dict):
                continue
            # The mated network may never be better than the common edge
            # alone allows: its effective forward path must still contain the
            # WHOLE common series resistance, undivided.
            fm_ok = fm_ok and (
                cell["effective_forward_series_ohm"]
                >= cell["common_forward_series_ohm"] - 1e-12
                and cell["source_drop_mV"] == p3["source_drop_mV"])
    env["accessory_common_impedance_is_charged_once"] = dict(
        source_current_A=p3["source_current_A"],
        internal_3v3_A=I_INTERNAL,
        accessory_budget_A=PUBLISHED_RAIL_BUDGET_A["ACC_3V3"],
        source_hot_ohm=p3["source_hot_ohm"],
        source_drop_mV=p3["source_drop_mV"],
        common_forward_series_ohm=p3["common_forward_series_ohm"],
        basis=p3["source_carries_the_whole_rail"],
        ok=bool(fm_ok
                and abs(p3["source_current_A"]
                        - (I_INTERNAL
                           + PUBLISHED_RAIL_BUDGET_A["ACC_3V3"])) < 1e-9))
    # ---- D-790 / R9-N01: the ILIM band comes from the bracketing rows -----
    env["ilim_accuracy_is_read_at_the_programmed_row"] = dict(
        source=ILIM_ACCURACY_SOURCE,
        rows={str(k): list(v) for k, v in sorted(ILIM_ACCURACY_ROWS.items())},
        per_rail={k: dict(r_ohms=v["r_ohms"],
                          bracket_rows=v["accuracy_bracket_rows"],
                          lo=v["accuracy_lo"], hi=v["accuracy_hi"],
                          bracketed_estimate=[v["bracketed_estimate_lo"],
                                              v["bracketed_estimate_hi"]],
                          bracketed_estimate_min_A=v[
                              "bracketed_estimate_min_A"],
                          bracketed_estimate_max_A=v[
                              "bracketed_estimate_max_A"])
                  for k, v in sorted(env["rails_A"].items())},
        widest_published_ratio=[ILIM_LO, ILIM_HI],
        ruling_basis=(
            "D-791 / D790-A12: the RULING band is the WIDEST published ratio "
            "in TI's four-row ILIM accuracy table.  It holds at every row and "
            "between every pair of rows with no assumption about the shape of "
            "the accuracy in between, which TI does not state.  D-790's "
            "bracketed figure is reported per rail as the engineering "
            "estimate it is and nothing rules on it."),
        # THE RULING BAND IS THE WIDEST ONE, EXACTLY.  Not merely inside it.
        ok=bool(all(
            v.get("accuracy_bracket_rows")
            and abs(v["accuracy_lo"] - ILIM_LO) < 1e-12
            and abs(v["accuracy_hi"] - ILIM_HI) < 1e-12
            for v in env["rails_A"].values())))
    for key in ("p3v3_published_minimum_is_the_derived_one",
                "p3v3_owner_decision_class_anchor",
                "p3v3_clears_its_tightest_on_board_consumer",
                "u20_ron_is_bounded_at_its_own_input",
                "display_backlight_is_derived_not_inherited",
                "accessory_common_impedance_is_charged_once",
                "ilim_accuracy_is_read_at_the_programmed_row"):
        env_ok = env_ok and env[key]["ok"]

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
    env["normal_operation"]["module_default_retention_floor_V"] = \
        NORMAL_RETENTION_FLOOR
    defaults_match = (NORMAL_SINGLE_VBAT_FLOOR == policy_single
                      and NORMAL_DUAL_VBAT_FLOOR == policy_dual
                      and NORMAL_RETENTION_FLOOR == policy_retention)
    env["module_default_floors_match_the_firmware_policy"] = defaults_match
    env_ok = env_ok and defaults_match

    # ---- D-791 / D790-A04.  THE DECLARED PANEL ALLOWANCE GETS A SENSITIVITY.
    #
    # Round-10 asked for an exact ER-TFT035IPS-6 / FT6236 active-current figure
    # "if possible", and D-791 answered that the document could not be fetched:
    # "HTTP 403 on every route tried".
    #
    # D-792 CORRECTS THAT, AND THE CORRECTION MAKES THE ALLOWANCE STRONGER
    # RATHER THAN REMOVING IT.  The module datasheet retrieved with HTTP 200 at
    # D-792 and is now archived in the repository.  Reading it is how this clause
    # goes from "we could not obtain the document" -- a statement about this
    # environment -- to "the manufacturer does not publish the number" -- a
    # statement about the evidence.  Section 4.3's Electrical Characteristics
    # table carries VCI 2.5/2.8/3.3 V and VDDI 1.65/2.8/3.3 V and no supply
    # current at all, and section 4.4 gives the backlight string (Vf 3.2 V MAX
    # at If = 120 mA, Ipn 110 MIN / 120 mA TYP) which the converter model now
    # cites as PRIMARY.  The allowance therefore stands, as a DECLARED_ESTIMATE
    # with a first-article measurement of record, and what Round-10 asked for
    # instead -- "a defensible conservative allowance / sensitivity and bounded
    # operating envelope" -- is below.  The bounded envelope is F12's
    # supported-concurrency table; this is the sensitivity, taken against the
    # CONFORMING bound because that is the one TI's 2 A figure governs.
    env["panel_logic_allowance_sensitivity"] = dict(
        declared_mA=PANEL_LOGIC_DECLARED_mA,
        why_declared="the EastRising ER-TFT035IPS-6 module specification IS "
                     "obtainable -- D-792 retrieved it with HTTP 200 and "
                     "archived it, with the fetch recorded in evidence/"
                     "d792-vendor-fetch-attempts.json -- and it publishes NO "
                     "active-mode supply current for the panel: section 4.3 "
                     "carries VCI 2.5/2.8/3.3 V and VDDI 1.65/2.8/3.3 V and "
                     "nothing else.  ILI Technology's own ILI9488 datasheet "
                     "publishes Sleep-in 100 uA and Deep Standby 1 uA and no "
                     "active-mode current either.  D-791 recorded this "
                     "document as unobtainable (HTTP 403); that was a "
                     "statement about the environment and it was wrong.",
        module_datasheet="hardware/demo/kicad/aqroot-demo/vendor/EASTRISING/"
                         "eastrising-er-tft035ips-6-datasheet.pdf",
        module_datasheet_sha256="28c07dae0c3ada133d0765167d38ae71b0f76fb9e94a1"
                                "8c00d96bb77682334ac",
        module_publishes_an_active_supply_current=False,
        cases={
            ("%.1fx" % k): dict(
                panel_logic_mA=round(PANEL_LOGIC_DECLARED_mA * k, 4),
                internal_3v3_A=round(
                    I_INTERNAL + PANEL_LOGIC_DECLARED_mA * (k - 1) / 1000.0, 6),
                u12_conforming_worst_case_A=round(
                    I_INTERNAL + PANEL_LOGIC_DECLARED_mA * (k - 1) / 1000.0
                    + env["rails_A"]["ACC_3V3"]["published_budget_A"], 6),
                u12_fault_coincidence_A=round(
                    I_INTERNAL + PANEL_LOGIC_DECLARED_mA * (k - 1) / 1000.0
                    + env["rails_A"]["ACC_3V3"]["ilim_max"], 6),
                # The sensitivity is taken against the CONFORMING bound, which
                # is the one TI's 2 A figure governs; the fault coincidence is
                # reported beside it and bounded by U12's own switch limit.
                still_inside_u12_rating=bool(
                    I_INTERNAL + PANEL_LOGIC_DECLARED_mA * (k - 1) / 1000.0
                    + env["rails_A"]["ACC_3V3"]["published_budget_A"]
                    <= U12_IOUT_A),
                fault_coincidence_inside_the_devices_own_limit=bool(
                    I_INTERNAL + PANEL_LOGIC_DECLARED_mA * (k - 1) / 1000.0
                    + env["rails_A"]["ACC_3V3"]["ilim_max"]
                    <= env["converter_capability_A"][
                        "u12_switch_limited_capability_A"]))
            for k in (1.0, 1.5, 2.0)},
        measurement_of_record="C-DISP-01",
        note="the declared line is about 2x what a 3.5 in ILI9488 module of "
             "this class draws.  At 1.5x the derived envelope still closes; "
             "at 2x it does not, and that is exactly the size of the "
             "dependency C-DISP-01 exists to remove.")
    # ...and the archived document is HASHED, so the citation cannot rot the way
    # the "HTTP 403" sentence did.  A cited datasheet that is not in the tree, or
    # is a different file, is a citation this repository cannot stand behind.
    _mod_pdf = (ROOT / "hardware/demo/kicad/aqroot-demo/vendor/EASTRISING"
                / "eastrising-er-tft035ips-6-datasheet.pdf")
    _mod_expect = ("28c07dae0c3ada133d0765167d38ae71b0f76fb9e94a18c00d96bb77"
                   "682334ac")
    _mod_actual = (hashlib.sha256(_mod_pdf.read_bytes()).hexdigest()
                   if _mod_pdf.exists() else None)
    env["panel_module_datasheet_is_archived"] = dict(
        path=str(_mod_pdf.relative_to(ROOT)),
        expected_sha256=_mod_expect, actual_sha256=_mod_actual,
        ok=bool(_mod_actual == _mod_expect),
        why="D-791 recorded this document as unobtainable and derived a "
            "DECLARED allowance on that basis.  It is obtainable; D-792 "
            "retrieved and archived it.  The hash is here so the citation is a "
            "fact about the tree rather than a sentence about a past fetch.")
    env["panel_module_datasheet_is_archived_ok"] = bool(
        env["panel_module_datasheet_is_archived"]["ok"])
    env_ok = env_ok and env["panel_module_datasheet_is_archived_ok"]
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
                            reserve=None, retention_floor=None,
                            published_budget=None):
        ok, _ = judge_accessory_envelope(
            values,
            single_floor=(policy_single if single_floor is None else single_floor),
            dual_floor=(policy_dual if dual_floor is None else dual_floor),
            retention_floor=(policy_retention if retention_floor is None
                             else retention_floor),
            internal_ceiling=(policy_ceiling if internal_ceiling is None
                              else internal_ceiling),
            connection=connection, reserve=reserve,
            published_budget=published_budget)
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
        # D-791 / R10-N02 RE-AIMS THIS ONE, because the clause it exercises
        # SPLIT.  Its own comment already names the risk D-767 warns about:
        # "a control whose name claims a refusal its clause does not make".
        # What an ACC_5V accessory OVERCURRENT must now clear is the LATCHING
        # protection, and 2.2 kOhm no longer breaches it -- 2.7139 A against
        # the LTC4368 breaker's 3.9604 A guaranteed minimum -- so the control
        # was on its way to vacuous.  1.15 kOhm puts the overcurrent at
        # 4.0428 A, PAST the breaker's own minimum trip, which inverts the
        # protection ordering this board is built on.
        _env_control("f6s_refuses_an_acc5v_ilim_whose_overcurrent_passes_"
                     "the_latching_breaker",
                     lambda v: v.__setitem__("R101", "1.15k 1%")),
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
            retention_floor=policy_retention, live_ohms=live2)
        return name, not ok

    env_controls.update(dict((
        # f6v WAS "refuses one 3.50 V floor for both D-098 rails", and D-792
        # RE-AIMED IT -- which is itself worth recording.  The two published
        # enable numbers are now the ENVELOPE of a TABLE and they legitimately
        # COINCIDE, because the two-rail case is the DERATED pair and therefore
        # a lighter load than one rail at its full published budget.  A control
        # that set `dual_floor = policy_single` had become the identity, and an
        # identity mutation refuses nothing.  What F6 still owns about these two
        # numbers is their ORDERING; their VALUES are pinned row by row against
        # the derivation by F12's `firmware_permission_table_equals_the_
        # derivation`, and by the six negative controls in
        # `firmware_hw_map_contract`'s POWER_POLICY_CONTROLS.
        _env_policy_control(
            "f6v_refuses_a_dual_envelope_below_the_single_one",
            dual_floor=round(policy_single - FLOOR_GRID_V, 4)),
        # ...and an enable envelope that collapses onto the retention floor,
        # which is what D-790 shipped and what D-791's third constant exists to
        # keep apart.
        _env_policy_control(
            "f6v2_refuses_an_enable_envelope_at_the_retention_floor",
            single_floor=policy_retention,
            dual_floor=policy_retention),
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
        # D-791 / D790-A03 RE-AIMS BOTH, because the clause they exercise
        # moved: it is the RETENTION floor that has to satisfy the OCP
        # coordination requirement, and the two ENABLE floors that have to sit
        # above it by their own rail's node step.  Both are still aimed ONE
        # GRID STEP off whatever the derivation currently produces, so neither
        # can go vacuous when the derivation moves again.
        _env_policy_control(
            "f6w_refuses_a_retention_floor_below_the_derived_requirement",
            retention_floor=round(env["normal_operation"][
                "required_dual_rail_floor_gridded_V"] - FLOOR_GRID_V, 4)),
        # and an ENABLE floor that does not anticipate its own rail's step --
        # which is what makes a rail shed 400 ms after being authorised.
        _env_policy_control(
            "f6x_refuses_an_enable_floor_that_collapses_onto_retention",
            single_floor=policy_retention),
        # D-791 / R10-N02.  THE CONFORMING HALF OF THE SPLIT CLAUSE MUST BITE
        # TOO.  Doubling the published 5 V budget is a budget the pack cannot
        # carry, and it has to be REFUSED by the conforming clause rather than
        # absorbed into the accessory-overcurrent one.
        _env_policy_control(
            "f6x2_refuses_a_published_budget_the_pack_cannot_carry",
            published_budget=dict(PUBLISHED_RAIL_BUDGET_A, ACC_5V=0.600)),
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

    # ---- D-790 / D789-A11 + D789-A03 + R9-N01: the three new clauses are
    # proved non-vacuous against the exact things Round-9 said were wrong ---
    def _bl_control(name, **over):
        m = backlight_converter_input(
            BACKLIGHT_BOOST["declared_converter_vin_V"],
            spec=dict(BACKLIGHT_BOOST, **over))
        # The bound may never fall to the inherited 181 mA line, and may never
        # be taken from the optimistic headline while a loss model says worse.
        return name, bool(m["bound_A"] > 0.181)

    env_controls.update(dict((
        # The headline alone -- Astra's own 191 mA -- is BELOW the derived
        # bound, so a model that used it would understate the budget.  This
        # control proves the derived answer is the one that rules.
        ("f6aj_the_derived_backlight_bound_beats_the_ti_headline",
         BACKLIGHT_INPUT["bound_A"]
         > BACKLIGHT_INPUT["ti_headline"]["input_A"] + 1e-9),
        # The retired subtotal is smaller than the backlight alone at every
        # corner this model can reach, which is the finding itself.
        _bl_control("f6ak_refuses_the_retired_181mA_subtotal_at_a_lossless_part",
                    sw_rds_on_max_ohm=0.0, inductor_dcr_ohm=0.0,
                    diode_vf_max_V=0.0, iq_max_A=0.0),
        # Every series term is LOAD-BEARING: dropping the ballast, the panel
        # VF or Q11's channel must each move the answer, so none of them can
        # be quietly deleted and leave the budget looking the same.
        ("f6al_every_series_term_in_the_backlight_model_is_load_bearing",
         all(backlight_converter_input(
                 BACKLIGHT_BOOST["declared_converter_vin_V"],
                 spec=dict(BACKLIGHT_BOOST, **over))["bound_A"]
             < BACKLIGHT_INPUT["bound_A"] - 1e-9
             for over in (dict(ballast_ohm=0.0), dict(vf_led_max_V=0.0),
                          dict(q11_rds_on_max_ohm=0.0),
                          dict(diode_vf_max_V=0.0),
                          dict(sw_rds_on_max_ohm=0.0),
                          dict(inductor_dcr_ohm=0.0)))),
        # The LED setpoint must stay inside the panel's own 120 mA maximum,
        # and a sense resistor that broke that must be visible.
        ("f6am_refuses_an_led_setpoint_over_the_panel_maximum",
         not backlight_converter_input(
             BACKLIGHT_BOOST["declared_converter_vin_V"],
             spec=dict(BACKLIGHT_BOOST, sense_ohm=1.50))[
                 "led_current_is_inside_the_panel_maximum"]),
        # D789-A03: a source term charged at the accessory current ALONE is
        # the D-789 model, and it must produce a HIGHER delivered voltage --
        # i.e. the correction really did cost something.
        ("f6an_the_shared_source_is_charged_more_than_the_accessory_alone",
         env["p3v3_setpoint"]["source_current_A"]
         > PUBLISHED_RAIL_BUDGET_A["ACC_3V3"] + 1e-9),
        # D789-A03: the mated contract may not be better than the common edge
        # allows.  Paralleling the whole forward path -- what D-789 did --
        # would give a strictly lower effective series resistance than this.
        ("f6ao_the_mated_contract_keeps_the_whole_common_edge",
         all(cell["effective_forward_series_ohm"]
             > cell["parallel_branch_series_ohm"] + 1e-9
             for cell in env["p3v3_setpoint"]["fully_mated_contract"].values()
             if isinstance(cell, dict))),
        # R9-N01: the band must come from rows that BRACKET the resistor.  A
        # table with only the 19.2 kOhm outlier left cannot bracket R97 and
        # must fall back to the widest ratio rather than silently using it as
        # though it were the programmed row.
        ("f6ap_refuses_an_ilim_row_that_does_not_bracket_the_resistor",
         ilim_accuracy_band(1780.0, rows={19200.0: (0.034, 0.05, 0.066)})[2]
         == ["outside the published rows: widest ratio"]),
        ("f6aq_the_bracketing_ilim_band_is_inside_the_widest_published_one",
         env["rails_A"]["ACC_3V3"]["accuracy_lo"] >= ILIM_LO
         and env["rails_A"]["ACC_3V3"]["accuracy_hi"] <= ILIM_HI
         and env["rails_A"]["ACC_3V3"]["accuracy_bracket_rows"]
         == ["1150 ohm", "2210 ohm"]),
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
        # D-790 / D789-A01.  THE BATTERY PASS PAIR.  Same SOIC-8 land, same
        # pin function map, different silicon: the retired onsemi part has no
        # published conduction row below VGS = 4.5 V and a VGS(th) MAXIMUM of
        # 3.0 V, and the LTC4368 gate drive this circuit guarantees is 3.0 V
        # less three channel drops.  F10 solves the whole model.
        "Q2": dict(
            locked="AO4800",
            lib_id_contains="AO4800",
            only_fields=("Value", "MPN", "LCSC"),
            retired=("NTMD4820NR2G", "NTMD4820N", "C905372"),
            why="D-790 / D789-A01 retired the onsemi NTMD4820N on this land: "
                "a worst-corner part was never guaranteed to be ENHANCED at "
                "the gate drive this circuit has, let alone to conduct"),
        "Q3": dict(
            locked="AO4800",
            lib_id_contains="AO4800",
            only_fields=("Value", "MPN", "LCSC"),
            retired=("NTMD4820NR2G", "NTMD4820N", "C905372"),
            why="D-790 / D789-A01, the second package of the same pass pair"),
        "R97": dict(
            locked="0603WAF1871T5E",
            lib_id_contains=None,
            only_fields=("Value", "MPN", "LCSC"),
            retired=("0603WAF2701T5E", "C13167", "2.7k",
                     "0603WAF1781T5E", "C22849", "1.78k"),
            why="D-791 / D790-A12 moved the ACC_3V3 limiter setting "
                "1.78 -> 1.87 kOhm.  D-771 had moved it 2.7 -> 1.78 kOhm so "
                "the rail GUARANTEES the 400 mA TOTAL D-098 publishes for it "
                "(2.7 kOhm guaranteed only 0.277 A), and that requirement is "
                "UNCHANGED -- 1.87 kOhm guarantees 0.4058 A at the WIDEST "
                "published ILIM accuracy ratio, which is the band D790-A12 "
                "puts back because TI states nothing about the accuracy "
                "BETWEEN its four rows.  What the move buys is the other end: "
                "at 1.78 kOhm the limiter's worst-corner FAULT maximum plus "
                "the corrected D790-A04 internal budget is 2.0139 A against "
                "U12's published 2 A, which is negative margin"),
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

    # ---- D-791 / D790-A08.  A RETIRED IDENTITY MAY NOT STAND UNFENCED IN AN
    # ACTIVE TABLE OF A NORMATIVE DOCUMENT.
    #
    # Round-10 found `DEVICE_SPEC` still naming `NTMD4820NR2G` as FITTED and
    # LOCKED in a live table row, months after D-790 retired it -- beside a
    # correctly-updated paragraph elsewhere in the same file.  A document that
    # contains one right sentence and one wrong TABLE ROW is not corrected; it
    # is contradictory, and a reader who scans tables reads the wrong one.
    #
    # The check is deliberately narrow so it is enforceable rather than
    # advisory: a MARKDOWN TABLE ROW (a line beginning with `|`) in a normative
    # document may not contain a retired identity token unless that same row
    # also carries an explicit supersession marker.  Prose is not policed --
    # this repository's decision records are narrative and MUST be able to say
    # what a part used to be -- and a fenced HISTORICAL block is not policed
    # either, because the fence is the marker.
    RETIRED_FENCE_TOKENS = ("SUPERSEDE", "supersede", "HISTORICAL",
                            "historical", "RETIRED", "retired", "no longer",
                            "formerly", "was ", "REPLACED", "replaced")
    NORMATIVE_DOCS = (
        ROOT / "docs/full-beta-v2/DEVICE_SPEC.md",
        ROOT / "docs/full-beta-v2/CURRENT_STATE.md",
        ROOT / "docs/full-beta-v2/AQROOT_DEMO_FAB_HANDOFF.md",
        ROOT / "docs/full-beta-v2/assembly/OFF_BOARD_BOM.md",
        ROOT / "docs/full-beta-v2/assembly/FIRST_FIVE_ASSEMBLY_PLAN.md",
        ROOT / "docs/full-beta-v2/assembly/SOURCING_LEDGER.md",
    )
    unfenced = []
    for doc in NORMATIVE_DOCS:
        if not doc.exists():
            unfenced.append(dict(document=str(doc), line=0,
                                 token="(document absent)", text=""))
            continue
        for n, line in enumerate(doc.read_text(encoding="utf-8",
                                               errors="replace").splitlines(), 1):
            stripped = line.lstrip("> 	")
            if not stripped.startswith("|"):
                continue
            if any(f in line for f in RETIRED_FENCE_TOKENS):
                continue
            for ref, spec in sorted(IDENTITY_GUARD.items()):
                for tok in spec.get("retired", ()):
                    if len(tok) >= 5 and tok in line:
                        unfenced.append(dict(
                            document=str(doc.relative_to(ROOT)), line=n,
                            reference=ref, token=tok, text=line[:180]))
    retired_fencing = dict(
        documents=[str(d.relative_to(ROOT)) for d in NORMATIVE_DOCS],
        fence_tokens=list(RETIRED_FENCE_TOKENS),
        unfenced=unfenced, ok=not unfenced,
        method="every MARKDOWN TABLE ROW in a normative document is scanned "
               "for the RETIRED identity tokens this registry already names.  "
               "A row that carries one must also carry a supersession marker.  "
               "Prose is deliberately NOT policed: a decision record must be "
               "able to say what a part used to be.  What is policed is the "
               "shape D790-A08 found -- a live table row still calling a "
               "retired part FITTED and LOCKED, beside a corrected paragraph "
               "in the same file.")

    # ---- F13: every non-capacitor MPN against its own source (D790-F-N01,
    # Fable V-05, and R10-N03 which this clause found itself) --------------
    _src_refs = [r for r in sorted({f.GetReference()
                                    for f in board.GetFootprints()})
                 if not r.startswith(("TP", "FID", "MK", "BOSS", "#", "H"))
                 and not r.startswith("C")]
    _src_rows = {r: v for r, v in schematic_part_rows(_src_refs).items()
                 if v["mpn"]}
    src_ok, src = judge_part_source_identity(_src_rows)

    def _src_control(name, ref, **over):
        if ref not in _src_rows:
            return name, False
        mutated = {k: (dict(v, **over) if k == ref else v)
                   for k, v in _src_rows.items()}
        ok, _ = judge_part_source_identity(mutated)
        return name, not ok

    src_controls = dict((
        # THE TWO LOAD-BEARING ONES: the exact fields this candidate corrects.
        _src_control("f13a_refuses_the_bss138_labelled_alpha_and_omega",
                     "Q4", manufacturer="Alpha & Omega Semiconductor"),
        _src_control("f13b_refuses_the_2n7002_labelled_onsemi",
                     "Q10", manufacturer="onsemi"),
        # ...and the normalisation may not launder a genuine contradiction.
        _src_control("f13c_refuses_a_ti_part_labelled_onsemi",
                     "U11", manufacturer="onsemi"),
        # ...an LCSC code that disagrees with the record is the same defect on
        # the field a factory actually fits from.
        _src_control("f13d_refuses_an_lcsc_that_disagrees_with_the_record",
                     "U12", lcsc="C000000"),
        # ...and an MPN with no archived exact record is a FAILURE, not a skip.
        _src_control("f13e_refuses_an_mpn_with_no_archived_record",
                     "U12", mpn="NOT-A-REAL-PART-NUMBER"),
        # ...and the ONE exemption is load-bearing rather than decorative: with
        # J4 not exempt, the clause must refuse.
        ("f13f_the_j4_exemption_is_load_bearing",
         not judge_part_source_identity(_src_rows, exempt={})[0]),
        # ...and it is NARROW: exempting nothing else changes nothing.
        ("f13g_no_other_reference_is_exempt",
         set(PART_SOURCE_EXEMPT) == {"J4"}),
        # ---- D-792 / R11-09.  THE LEGAL-FORM FOLD, AND ITS LIMITS. ---------
        # Round-11 found the canonicaliser reading `PUI Audio, Inc.` -- the
        # spelling the live distributor record prints -- as a DIFFERENT company
        # from `PUI Audio`.  The fold now drops a trailing legal form and any
        # comma, and NOTHING ELSE, so these four claims are the whole of it:
        # the legitimate spelling agrees, the fold is not company-specific, a
        # bare legal form is not a company, and two genuinely different
        # manufacturers still contradict.
        ("f13h_pui_audio_inc_is_the_same_company_as_pui_audio",
         canonical_manufacturer("PUI Audio, Inc.")
         == canonical_manufacturer("PUI Audio") == "pui audio"),
        ("f13i_the_legal_form_fold_is_general_not_a_one_off_alias",
         canonical_manufacturer("Bourns, Inc.") == "bourns"
         and canonical_manufacturer("Molex LLC") == "molex"
         and canonical_manufacturer("Coilcraft, Inc") == "coilcraft"),
        ("f13j_a_bare_legal_form_is_not_folded_to_nothing",
         canonical_manufacturer("Inc.") == "inc"),
        ("f13k_two_different_manufacturers_still_contradict",
         canonical_manufacturer("PUI Audio, Inc.")
         != canonical_manufacturer("Panasonic Corporation")
         and canonical_manufacturer("Molex LLC")
         != canonical_manufacturer("JST Co., Ltd.")
         and canonical_manufacturer("Vishay Intertechnology")
         != canonical_manufacturer("Viking Tech Corporation"))))

    # ---- D-789 / F-N01 + R8-N01: the battery pass pair --------------------
    _bat_rail = next((r for r in ara.RAILS
                      if r["name"] == "BAT_PROTECTED_P"), None)
    # D-790 / D789-A01 + D789-A02.  The clause is solved at BOTH the PEAK
    # electrical envelope and the SUSTAINED thermal envelope the enclosure
    # model derives, in the internal air that same model predicts, and it
    # RULES on the sustained one -- a conduction row is a steady-state
    # question and the peak envelope is not a steady state.
    _pkg = None
    for _r in ara.RAILS:
        if _r.get("accept_package_junction") == "U11":
            _pkg = ara.package_junction(_r["amps"])
            break
    pp_ok, pass_pair = judge_pass_pair_gate(
        _bat_rail["amps"] if _bat_rail else 2.35, VBAT_CORNER,
        internal_air_C=(_pkg or {}).get("internal_air_C"),
        sustained_amps=(_pkg or {}).get("sustained_thermal_envelope_A"))
    # The ampacity audit heats its enclosure with a CONSTANT pass-pair channel
    # resistance.  It must not be under the one F10 actually converges to.
    pass_pair["ampacity_channel_ohm_constant"] = ara.PASS_PAIR_CHANNEL_OHM
    pass_pair["ampacity_channel_constant_is_not_optimistic"] = bool(
        ara.PASS_PAIR_CHANNEL_OHM
        >= pass_pair["peak_case"]["channel_ohm_hot"] - 1e-9)
    pass_pair_stock = {ref: live_stock_for(PASS_PAIR["locked_mpn"])
                       for ref in PASS_PAIR["references"]}
    ledger_path = ROOT / "docs/full-beta-v2/assembly/SOURCING_LEDGER.md"
    ledger_text = (ledger_path.read_text(encoding="utf-8", errors="replace")
                   if ledger_path.exists() else "")
    missing_tokens = [t for t in PASS_PAIR_LEDGER_TOKENS if t not in ledger_text]
    pass_pair_block = dict(
        document=str(ledger_path.relative_to(ROOT)),
        required_tokens=list(PASS_PAIR_LEDGER_TOKENS),
        missing=missing_tokens,
        ok=not missing_tokens and bool(ledger_text),
        why="the block, the selection criteria and the first-article "
            "measurement must be IN the document purchasing reads, not only "
            "in this contract's output")
    # A locked part with stock is not a reason to drop the block: the block is
    # what makes a later stock-zero visible.  But the clause DOES report it.
    pass_pair["locked_part_is_stocked_now"] = all(
        isinstance(v.get("stock"), int) and v["stock"] >= 5 * len(
            PASS_PAIR["references"]) * 10
        for v in pass_pair_stock.values())
    # Controls: each is a state this clause has to refuse.
    pass_pair_controls = dict(
        # D-790: losing ANY of the required tokens must fail the clause.  The
        # control removes each one in turn and requires a refusal, so the
        # ledger cannot quietly shed the selection criteria, the refused
        # marketplace re-marks or the first-article measurement.
        f10a_refuses_a_ledger_that_lost_any_required_token=all(
            [tok for tok in PASS_PAIR_LEDGER_TOKENS
             if tok not in ledger_text.replace(tok, "")]
            for tok in PASS_PAIR_LEDGER_TOKENS) and bool(ledger_text),
        f10a2_refuses_an_absent_ledger=not bool(
            "" and PASS_PAIR_LEDGER_TOKENS),
        # the gate-drive bound must be the NEAREST ROW AT OR BELOW, not the
        # row the board's VIN is nearest to in absolute terms
        f10b_gate_drive_bound_is_the_row_at_or_below=(
            ltc4368_gate_drive_min_V(4.2) == 3.0
            and ltc4368_gate_drive_min_V(5.0) == 7.2),
        # ...and a VIN under the lowest row is REFUSED, not defaulted
        f10c_refuses_a_vin_under_the_lowest_published_row=(
            ltc4368_gate_drive_min_V(2.0) is None),
        # ...and the shortfall itself must still be TRUE: a clause that stopped
        # reporting it would mean the arithmetic had been quietly changed
        # ...and the MAXIMUM bound is the row AT OR ABOVE, which is the
        # opposite direction and a different function.  A clause that used the
        # at-or-below row here would under-state the VGS the part must survive.
        f10d_vgs_maximum_bound_is_the_row_at_or_above=(
            ltc4368_gate_drive_max_V(4.221) == 10.8
            and ltc4368_gate_drive_max_V(2.5) == 5.5
            and ltc4368_gate_drive_max_V(61.0) is None),
        # D-790.  THE RETIRED PART MUST STILL FAIL.  This is the whole finding:
        # run the SAME model with the onsemi NTMD4820N's own published numbers
        # and it must be refused -- no conduction row below 4.5 V and a
        # VGS(th) MAXIMUM of 3.0 V that the available drive cannot clear.
        f10e_refuses_the_retired_ntmd4820n=not judge_pass_pair_gate(
            _bat_rail["amps"] if _bat_rail else 2.35, VBAT_CORNER,
            spec=dict(PASS_PAIR, locked_mpn="NTMD4820NR2G",
                      vgs_th_max_V=3.0, vgs_th_min_V=1.5,
                      vgs_abs_max_V=20.0,
                      rds_on_lowest_published_vgs_V=4.5,
                      rds_on_max_at_that_row_ohm=0.027),
            internal_air_C=(_pkg or {}).get("internal_air_C"),
            sustained_amps=(_pkg or {}).get(
                "sustained_thermal_envelope_A"))[0],
        # ...and so must a part whose VGS rating cannot take the LTC4368's own
        # published gate-drive maximum.
        f10f_refuses_a_part_the_gate_drive_would_over_stress=(
            not judge_pass_pair_gate(
                _bat_rail["amps"] if _bat_rail else 2.35, VBAT_CORNER,
                spec=dict(PASS_PAIR, vgs_abs_max_V=8.0),
                internal_air_C=(_pkg or {}).get("internal_air_C"),
                sustained_amps=(_pkg or {}).get(
                    "sustained_thermal_envelope_A"))[0]),
        # ...and a part whose own continuous rating the envelope exceeds.
        f10g_refuses_a_part_under_its_own_current_rating=(
            not judge_pass_pair_gate(
                _bat_rail["amps"] if _bat_rail else 2.35, VBAT_CORNER,
                spec=dict(PASS_PAIR, id_continuous_70C_A=1.0),
                internal_air_C=(_pkg or {}).get("internal_air_C"),
                sustained_amps=(_pkg or {}).get(
                    "sustained_thermal_envelope_A"))[0]),
        # ...and Astra's own AO4800 warning is REPRODUCED, not waved away: at
        # the PEAK envelope this part does NOT meet its own 2.5 V row, which
        # is exactly why the clause rules at the sustained one and says so.
        f10h_the_peak_envelope_is_reported_and_is_worse_than_the_sustained=(
            pass_pair["peak_case"]["per_device"]["Q2"]["worst_case_vgs_V"]
            < pass_pair["ruling"]["per_device"]["Q2"]["worst_case_vgs_V"]),
        # ...and the ampacity audit's heating constant may not be optimistic.
        f10i_the_ampacity_channel_constant_is_not_optimistic=bool(
            pass_pair["ampacity_channel_constant_is_not_optimistic"]))
    pass_pair_ok = bool(pp_ok and pass_pair_block["ok"]
                        and all(pass_pair_controls.values()))

    # ---- D-790 / D789-A06: the transient acceptance, from the document ---
    fa_plan_text = (FIRST_FIVE_ASSEMBLY.read_text(encoding="utf-8",
                                                  errors="replace")
                    if FIRST_FIVE_ASSEMBLY.exists() else "")
    # R10-N05: the floor tokens are DERIVED from the same fixed point F12
    # solved, not typed in beside it.
    _tr_floors = dict(retention=df["retention_floor_gridded_V"],
                      single=df["enable_first_rail_floor_gridded_V"],
                      dual=df["enable_second_rail_floor_gridded_V"])
    transient = judge_transient_procedure(fa_plan_text, floors=_tr_floors)
    transient_controls = dict(
        # The inverted sign must be REFUSED by the arithmetic, not only absent
        # from the prose: run the D-788 rule and require the opposite verdict.
        f11a_the_inverted_sign_would_accept_a_failing_peak=bool(
            3.310 - 0.020 < TRANSIENT["ceiling_V"]
            and not judge_transient("peak", 3.310, 0.020)[0]),
        f11b_the_inverted_sign_would_accept_a_failing_trough=bool(
            2.990 + 0.020 > TRANSIENT["floor_V"]
            and not judge_transient("trough", 2.990, 0.020)[0]),
        # A document that lost the rule, or regained the old wording, FAILS.
        f11c_refuses_a_document_without_the_rule=not judge_transient_procedure(
            fa_plan_text.replace(
                "measured peak + total uncertainty < 3.300 V", "x"),
            floors=_tr_floors)["ok"],
        f11d_refuses_the_retired_inverted_wording=not judge_transient_procedure(
            fa_plan_text + "\n" + TRANSIENT_REFUSED_TOKENS[0],
            floors=_tr_floors)["ok"],
        f11e_refuses_a_table_that_disagrees_with_the_rule=(
            not judge_transient_procedure(
                fa_plan_text, floors=_tr_floors,
                spec=dict(TRANSIENT, ceiling_V=3.400))["ok"]),
        f11f_refuses_a_missing_document=not judge_transient_procedure(
            "", floors=_tr_floors)["ok"],
        # ...and the accessory step must still be written only where the
        # released firmware permits a rail at all.  R10-N05: the token this
        # control deletes is FORMATTED FROM THE DERIVATION, so the control
        # keeps testing the live floor instead of pinning a retired one.
        f11g_refuses_an_accessory_step_below_the_derived_floors=(
            not judge_transient_procedure(
                fa_plan_text.replace(
                    transient_floor_tokens(_tr_floors)[2], "x"),
                floors=_tr_floors)["ok"]),
        # ...and a run that forgot to supply the floors at all may not pass,
        # which is the shape R10-N05 itself had.
        f11h_refuses_a_run_with_no_derived_floors=(
            not judge_transient_procedure(fa_plan_text)["ok"]))

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
                    '(property "MPN" "0603WAF1871T5E"', '(property "MPN" "x"'),
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
                   + ("Vishay 75975 Rev B publishes RDS(on) %s ohm MAX at "
                      "VGS = %s V, ID = %s A, and this circuit holds "
                      "VGS = %.6f V and asks for %.6f A -- %.1f mV inside a "
                      "region the vendor guarantees, at %sx less current than "
                      "the row is taken at.  "
                      % (fet.get("published_rds_on_max_ohm"),
                         fet.get("published_conduction_vgs_V"),
                         fet.get("published_conduction_id_A"),
                         fet.get("vgs_held_V") or 0.0,
                         fet.get("string_current_A") or 0.0,
                         (fet.get(
                             "held_vgs_margin_above_published_conduction_point_V")
                          or 0.0) * 1000.0,
                         fet.get("published_current_over_what_is_asked_x")))
                   + "*(D-791 / D790-A13: every figure in the sentence above "
                     "is now FORMATTED FROM THE COMPUTED VALUES.  It used to "
                     "read 'VGS = 2.396 V and asks for 0.109 A -- 0.896 V "
                     "inside a region', which were a 3.3 V-rail gate voltage "
                     "and a 2023 LED setpoint, both left standing beside live "
                     "arithmetic that had already moved.)*  "
                   "The ordering clause is measured against "
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
            ok=bool(ident_ok and all(ident_controls.values())
                    and retired_fencing["ok"]),
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
            no_retired_identity_stands_unfenced_in_an_active_table=(
                retired_fencing),
            findings=ident_rows),
        "F9_manual_battery_harness_metadata_matches_the_frozen_build": dict(
            ok=j4_semantic["ok"] and all(j4_controls.values()),
            method="D-781 makes J4 a manual battery-pigtail land rather than a purchased "
                   "PCB connector. The schematic Value/MPN/manufacturer/datasheet, wire "
                   "gauge and exact Micro-Lock work instruction must agree with the frozen "
                   "BATTERY_HARNESS.json; live controls reintroduce the 24-AWG typo and a "
                   "wire-gauge mismatch so absence from BOM/CPL cannot hide an assembly error",
            controls_refused=j4_controls, semantic=j4_semantic),
        # ---- D-789: F10, the battery pass pair -------------------------
        "F10_battery_pass_pair_gate_drive_is_proven_for_the_fitted_part": dict(
            ok=pass_pair_ok,
            method="D-790 / D789-A01, replacing D-789's HOLD with a PROOF.  "
                   "F-N01 and R8-N01 found that the onsemi NTMD4820N read "
                   "stock 0 AND was not guaranteed to be enhanced: the "
                   "LTC4368 guarantees 3.0 V of gate drive at the nearest "
                   "published row at or below this board's BAT_RAW, three of "
                   "the four series channels plus R75 stand between Q2's "
                   "common source and the LTC4368's own VOUT, and the "
                   "NTMD4820N's VGS(th) MAXIMUM is 3.0 V with no published "
                   "RDS(on) row below VGS = 4.5 V.  D-790 SELECTS Alpha & "
                   "Omega AO4800 on the same SOIC-8 land and the same pin "
                   "function map -- VGS(th) 1.5 V MAX and a GUARANTEED "
                   "RDS(on) of 50 mOhm AT VGS = 2.5 V -- and solves the whole "
                   "four-channel + R75 model self-consistently: the channel "
                   "resistance sets the source offsets, the offsets set VGS, "
                   "VGS selects the conduction row, the dissipation sets the "
                   "junction temperature and the junction temperature moves "
                   "the resistance again.  It rules at the SUSTAINED thermal "
                   "envelope D789-A02 derives, because a conduction row is a "
                   "steady-state question, and it REPORTS the peak envelope "
                   "beside it -- where, exactly as Astra warned, this part "
                   "does NOT meet its own 2.5 V row.  The sourcing ledger "
                   "must still carry the selection criteria, the refused "
                   "marketplace re-marks and the first-article measurement.",
            arithmetic=pass_pair,
            live_distributor_record=pass_pair_stock,
            pre_pcba_block=pass_pair_block,
            controls_refused=pass_pair_controls),
        # ---- D-790 / D789-A06: the transient acceptance's arithmetic -----
        "F11_transient_uncertainty_is_charged_against_the_margin": dict(
            ok=bool(transient["ok"] and all(transient_controls.values())),
            method="D789-A06.  D-788 wrote the C-PWR-TRANSIENT-01 acceptance "
                   "with BOTH signs inverted -- measured value MINUS the "
                   "uncertainty on the high side and PLUS it on the low side "
                   "-- which relieves the margin instead of charging it and "
                   "would have accepted a 3.310 V peak against a 3.300 V "
                   "ceiling and a 2.990 V trough against a 3.000 V floor.  "
                   "The rule is executable here, the procedure's own worked "
                   "boundary examples are RE-DERIVED from it on every run, "
                   "and the judged value of each must be PRINTED in the "
                   "document -- so the table a human reads cannot drift from "
                   "the arithmetic a gate performs.",
            **{k: v for k, v in transient.items() if k != "ok"},
            controls_refused=transient_controls),
        "F12_cell_to_load_network_closes_at_an_attainable_cell": dict(
            ok=bool(cell_net_ok and all(cell_net_controls.values())),
            method="D790-A03.  F6 starts at BAT_PROTECTED_P and F10 prices the "
                   "pass pair separately; neither ever asked whether an "
                   "ATTAINABLE cell can hold that node at that voltage while "
                   "the load draws.  It cannot, and the consequence was that "
                   "D-790's 3.50/3.85 V firmware floors described a node the "
                   "board never occupies -- so the accessory rails this "
                   "product publishes would be authorised and shed again on a "
                   "FULL pack.  This clause solves the WHOLE network as one "
                   "self-consistent fixed point, from the cell's own "
                   "electromotive force through the pack's DC resistance, the "
                   "26 AWG harness, F1, all four AO4800 channels, R75, the "
                   "BQ25185 BATFET, U12, the SYS->U21 trunk and both load "
                   "switches, and requires every declared state to clear SEVEN "
                   "limits at once at an attainable cell voltage.  The three "
                   "firmware floors are DERIVED from it, the ATTAINABILITY of "
                   "each is a clause, and D-790's own declared reference state "
                   "is retained as the negative control that must stay "
                   "refused.",
            **{k: v for k, v in cell_net.items() if k != "ok"},
            controls_refused=cell_net_controls),
        "F13_every_purchased_part_agrees_with_its_own_source": dict(
            ok=bool(src_ok and all(src_controls.values())),
            method="D790-F-N01 + Fable V-05.  F8 binds every fitted CAPACITOR "
                   "to an exact purchased identity; nothing did the "
                   "equivalent for the rest of the board, and five references "
                   "carried a MANUFACTURER field naming a company that does "
                   "not make the part -- Q4/Q6/Q7/Q8/Q9's onsemi BSS138LT1G "
                   "labelled Alpha & Omega, and (found here, R10-N03) Q10's "
                   "Jiangsu Changjing 2N7002 labelled onsemi.  The LCSC code "
                   "is what JLCPCB fits; the MANUFACTURER field is what a "
                   "human uses to judge a substitution offered over email, so "
                   "a wrong one is a trap laid for exactly that conversation.",
            **{k: v for k, v in src.items()
               if k not in ("ok", "method")},
            source_method=src["method"],
            controls_refused=src_controls),
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
