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
import aqroot_power_oracle as apo                             # noqa: E402

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
# D-794 / R13-05 + R13-04.  ONE AUTHORITY.  The envelope, the equation, the
# accuracy rows and the resulting band now live in `aqroot_power_model`, so
# this contract, `audit_rail_ampacity`'s accessory rail sizing and every
# document that quotes a limiter figure read the SAME primitive.  They are
# aliased here only so the call sites below keep reading.
ILIM_LO, ILIM_HI = apm.ILIM_ENVELOPE_LO, apm.ILIM_ENVELOPE_HI
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
# `R97` was 1.78 kOhm AT D-790 -- it is 1.87 kOhm on this board since D-791 --
# BRACKETED by the 1.15 k and 2.21 k rows, and it was being
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
# AND AT D-791 THE BRACKET WAS REFUSED TOO.  R10-A12: TI publishes four rows
# and says nothing between them, so a bracket is an INFERENCE.  The ruling
# bound went back to the WIDEST published ratio -- which needs no assumption
# about curvature -- and D-794 / R13-05 adds the half that was still missing:
# at `R97` = 1.87 kOhm and `R101` = 2.43 kOhm, neither of which is one of TI's
# four rows, even the widest ratio is an ENVELOPE THIS PROGRAMME DECLARES.  It
# is tagged that way in the canonical model, it carries `C-ACC-ILIM-01` as its
# measurement of record, and no document may call the published budgets
# "guaranteed" by it.
# --------------------------------------------------------------------------
ILIM_ACCURACY_ROWS = apm.ILIM_ACCURACY_ROWS
ILIM_ACCURACY_SOURCE = apm.ILIM_ACCURACY_SOURCE


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
ilim_accuracy_band = apm.ilim_accuracy_band
ilim_bracketed_estimate = apm.ilim_bracketed_estimate
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
PUBLISHED_RAIL_BUDGET_A = dict(apm.PUBLISHED_RAIL_BUDGET_A)
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
# D-793 / Fable R12: the canonical model owns it.  This alias exists only so
# the call sites below keep reading, and F12 asserts it equals the DERIVED
# pair -- which is what D-792's comment claimed and no code did.
#
# D-794 / R13-04.  IT WAS A COPY, AND A COPY IS A SECOND PLACE TO BE WRONG.
#
# ROUND-13: "Astra ... altered the F6-only declared pair while the overall
# release remained green in important cases.  ...  Bind all pair-budget
# consumers (F6, F12, firmware/docs) to one independently checked primitive
# authority."
#
# IT REPRODUCED BECAUSE OF THE `dict(...)` THAT USED TO BE ON THIS LINE.
# F6's twelve call sites read THIS name; F12's equality clause compared
# `apm.DECLARED_DUAL_RAIL_BUDGET_A` with its own derivation.  Those are two
# different objects the moment anything edits either, so moving the pair here
# left F12 comparing the authority with the physics -- both untouched, both
# agreeing -- while every F6 answer was computed at the altered figure.
#
# It is the same object now, and `the_declared_pair_consumers_share_one_object`
# in F12 asserts the IDENTITY rather than the value, so re-binding this name
# to an equal-looking dict fails too.
DECLARED_DUAL_RAIL_BUDGET_A = apm.DECLARED_DUAL_RAIL_BUDGET_A
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
NORMAL_SINGLE_VBAT_FLOOR = 3.85         # the published ENVELOPE of the D-793
NORMAL_DUAL_VBAT_FLOOR = 3.85           # permission table, one and two rails
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
    # D-800 (Round-19 power audit): SLVS916 prints line and load regulation
    # in its TYP column only.  They are applied here as DECLARED allowances,
    # always in the WIDENING direction (lower minimum, higher maximum), never
    # as a guarantee; the guaranteed rail is the feedback band, the resistor
    # tolerance and TCR, and C-PWR-TRANSIENT-01 measures the rest.
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
# D-801 / Round-20 D801-04.  THE INTERNAL LOAD THE PRODUCTION IMAGE ADMITS
# BESIDE A LIVE ACCESSORY RAIL.  `I_INTERNAL` is every ledger line at its peak
# AT ONCE, the Wi-Fi/BLE and sub-GHz transmitters included -- but the shipped
# rail-edge table (`aqroot_accessory_power_policy.h`, every row with bit 0
# Wi-Fi / BLE TX or bit 2 sub-GHz TX set) is `kAccessoryNotPermittedV`: no rail
# is live while either radio transmits.  A fault quoted at `I_INTERNAL` with a
# rail live is therefore a SIZING COINCIDENCE, not a state a user can reach.
# The admitted figure keeps every other line at its PEAK (audio, the bursty
# microSD / NFC / IR peaks), so it is still an upper bound on what is admitted.
RAIL_EXCLUDED_INTERNAL_KEYS = ("wifi_ble_tx", "subghz_tx")
I_INTERNAL_ADMITTED_WITH_A_RAIL = round(
    sum(x["mA"] for x in apm.LOAD_LEDGER
        if x["key"] not in RAIL_EXCLUDED_INTERNAL_KEYS) / 1000.0, 6)

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
# D-796 / Round-15 D796-05 item 7: D-753's `LTC4368_TRIP = 50 mV / 15 mOhm`
# (3.3333 A) was kept "so the decision that replaced it stays legible" and was
# PRINTED in F6 as `ltc4368_trip_A` beside the live breaker object -- a second,
# wrong breaker figure in the release report.  It is deleted; the ONLY breaker
# authority is `breaker` (R75 10 mOhm: 3.9604 A minimum, 5 A typical).
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


_ilim_typ = apm.ilim_typ_A


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
# D-793 / R12-07.  ONE NORMALISER, ONE ALIAS TABLE.
#
# ROUND-12, IN ITS OWN WORDS: "Consolidate manufacturer normalization into one
# narrow reviewed alias table used by F8/F13/other identity gates."
#
# There were TWO.  F8 folded a manufacturer name with `_norm_cap_mfr`, which
# stripped every non-alphanumeric character and consulted a two-entry private
# dictionary `{"murata": "murataelectronics"}`; F13 folded the same names with
# `canonical_manufacturer`, which folds case, commas and trailing legal forms
# and consults the twenty-odd-company `MFR_ALIASES` table.  So "Murata
# Electronics Co., Ltd." and "Murata Electronics" were one company to F13 and
# two to F8, and an alias added to one gate did not reach the other -- which
# is R11-09's defect in the OTHER gate, one round later.
#
# `_norm_cap_mfr` is now a thin wrapper on `canonical_manufacturer`, defined
# below, so there is exactly one fold and exactly one table.  It is defined
# lazily because `canonical_manufacturer` needs `MFR_ALIASES`, which is
# declared further down this file.
def _norm_cap_mfr(name):
    if not name:
        return ""
    return canonical_manufacturer(name) or ""


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
# D-793 / R12-07.  THE EXACT GROUND NETS, BY FULL NAME.  A pad on one of these
# carries no DC stress and is skipped; a pad on anything else -- including a
# net whose LEAF is spelled `GND` -- is examined like any other node.  There is
# exactly one ground net on this board and it is spelled `GND` at the root.
CANONICAL_GROUND_NETS = frozenset({"GND"})


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
            # D-793 / R12-07.  THE SKIP WAS KEYED BY LEAF NAME, WHICH IS THE
            # EXACT DEFECT D-788 / R7-D787-07 REMOVED FROM THE LINE BELOW IT.
            #
            # ROUND-12, IN ITS OWN WORDS: "F8 skips/accepts a leaf named GND
            # before proving exact canonical net identity; /ALIEN/GND mutation
            # stays green."
            #
            # It reproduces: `leaf == "GND"` is true of `/ALIEN/GND`, of
            # `/03_SPI_A_DISPLAY_SD/GND` and of any hierarchy at all, so a pad
            # moved onto a net this repository has never established was
            # simply not examined.  D-788 took the `else leaf` fallback out of
            # the DC lookup one line later and left this one standing.
            #
            # The skip is now keyed by the EXACT canonical net.  An unknown
            # GND-like leaf falls THROUGH to the DC lookup, is not in
            # CANONICAL_DC_NETS, and is therefore UNESTABLISHED -- which fails
            # closed and demands a named non-DC proof, exactly as any other
            # unknown node does.
            if not leaf:
                continue
            if net in CANONICAL_GROUND_NETS:
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
    # D-794 / R13-07.  "Alpha and Omega Semiconductor" is the company's own
    # prose spelling of its own name -- the ampersand written out -- and the
    # canonicaliser was rejecting it while accepting four other legal forms of
    # the same company.  Round-13: "Add this exact narrow alias and positive
    # tests.  Preserve rejection of VBsemi/Kexin/clone/distributor/cross-
    # manufacturer/prefix tricks.  No fuzzy/prefix matching."
    #
    # THE ALIAS IS EXACT, NOT A RULE.  A general "& means and" fold would be
    # the fuzzy matching R13-07 forbids: it would also make `Acme & Sons` and
    # `Acme and Sons` the same company without anyone reviewing whether they
    # are.  Two spellings are listed, both of them ones this company writes.
    ("alpha & omega semiconductor", "alpha & omega semicon",
     "alpha & omega", "aos",
     "alpha and omega semiconductor", "alpha and omega"),
    ("onsemi", "on semiconductor", "onsemiconductor"),
    ("texas instruments", "ti"),
    ("analog devices", "analog devices (maxim)", "maxim integrated", "adi",
     "analog devices inc./maxim", "analog devices inc", "analog devices inc.",
     "analog devices inc./maxim integrated",
     "analog devices inc/maxim integrated"),
    ("stmicroelectronics", "st microelectronics", "stmicro"),
    # D-793 / R12-07: `nxp semicon` is the spelling the LCSC record prints
    # and it is a MID-WORD truncation, which the tightened prefix rule no
    # longer accepts implicitly.  A legitimate distributor spelling belongs in
    # this table, reviewed, rather than in a character-count heuristic.
    ("nxp semiconductors", "nxp", "nxp semicon"),
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


def _no_truncation_rule_exists():
    """D-795 / R14-07.  Over a LOCAL table, a word-boundary truncation, a
    two-word prefix and a shared prefix all stay THEMSELVES."""
    saved = dict(MFR_CANONICAL)
    try:
        MFR_CANONICAL.clear()
        MFR_CANONICAL.update({"acme micro devices": "acme micro devices",
                              "acme micro systems": "acme micro systems"})
        return bool(canonical_manufacturer("acme micro") == "acme micro"
                    and canonical_manufacturer("acme micro dev")
                    == "acme micro dev"
                    and canonical_manufacturer("Acme Micro Devices Inc.")
                    == "acme micro devices")
    finally:
        MFR_CANONICAL.clear()
        MFR_CANONICAL.update(saved)


def _aos_alias_is_the_only_route():
    """D-794 / R13-07.  The written-out AOS spelling resolves because it is in
    the REVIEWED alias table, not because some character rule reached it.

    Run over a local table with the two D-794 entries removed: if
    `canonical_manufacturer` still folded "Alpha and Omega Semiconductor" into
    the canonical name, the alias would be decoration over a fuzzy match.
    """
    saved = dict(MFR_CANONICAL)
    try:
        MFR_CANONICAL.clear()
        MFR_CANONICAL.update({
            k: v for k, v in saved.items()
            if k not in (fold_manufacturer("alpha and omega semiconductor"),
                         fold_manufacturer("alpha and omega"))})
        without = canonical_manufacturer("Alpha and Omega Semiconductor")
    finally:
        MFR_CANONICAL.clear()
        MFR_CANONICAL.update(saved)
    with_alias = canonical_manufacturer("Alpha and Omega Semiconductor")
    return bool(with_alias == "alpha & omega semiconductor"
                and without != "alpha & omega semiconductor")


MFR_CANONICAL = {}
for _group in MFR_ALIASES:
    for _name in _group:
        MFR_CANONICAL[fold_manufacturer(_name)] = _group[0]


# D-795 / R14-07 (Astra) + Fable R14-09.  NO TRUNCATION, NO PREFIX, NO RULE.
#
# ROUND-14: "Remove ALL generic manufacturer prefix/fuzzy fallbacks for
# critical exact-part identity.  Only reviewed exact aliases/abbreviations may
# canonicalize.  'Alpha and' must NOT canonicalize to AOS."
#
# IT REPRODUCES, AND THE RULE THAT DID IT WAS D-793's TIGHTENED ONE.  A
# truncation that ended on a word boundary and kept two whole words was
# accepted as the company it truncated -- so "Alpha and" (two words, nine
# characters, a word boundary of "alpha and omega semiconductor") resolved to
# Alpha & Omega Semiconductor, the one manufacturer whose exact identity the
# pass pair depends on.  A character rule cannot know which two-word prefixes
# are companies.  The fallback is REMOVED: a name canonicalises only by exact
# match, after case, spacing, commas and a trailing legal form are folded,
# against the REVIEWED alias table.  A distributor spelling that is genuinely
# the company goes into that table, by name, where a reviewer can see it.


def canonical_manufacturer(name):
    """Fold case, spacing, commas and trailing legal forms, then look the
    result up in the REVIEWED alias table.  Nothing else."""
    if not name:
        return None
    key = fold_manufacturer(name)
    return MFR_CANONICAL.get(key, key)


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


# ==========================================================================
# D-794 / ROUND-13 FABLE RESIDUAL.  THE EMBEDDED SYMBOL CACHE IS A SECOND
# PLACE THE MANUFACTURER IS WRITTEN DOWN, AND NOTHING WAS READING IT.
#
# ROUND-13's Fable residual list, in its own words: "AO4800 embedded schematic
# symbol cache names: verify actual embedded cache against current AOS
# mapping; refresh if stale, re-run parity."
#
# IT IS STALE, AND BY MORE THAN THE NAME.  A KiCad schematic carries a
# `lib_symbols` block -- a CACHE of the library symbol, embedded in the sheet
# so the file opens without the library.  `F13` reads the INSTANCE properties,
# which is what the BOM is built from, so it never looked at the cache.  The
# cached `AQROOT_Beta:AO4800` entry carried:
#
#   Manufacturer  "onsemi"                                      -- the company
#                 that does not make this part
#   Datasheet     onsemi's NTMD4820N PDF URL                    -- the part
#                 D-790 RETIRED for an electrical reason
#   Package       "SOIC-8 (case 751-07)"                        -- onsemi's own
#                 case designation
#
# That is the D-791 / F-N01 defect exactly, in the one field F13 could not
# see, and it is worse than a BOM error: a human who opens `Q2`'s symbol to
# judge a substitution offered over email is sent to the datasheet of the part
# this design refuses.  The display FPC connector's cached entry had the same
# shape -- it named the PANEL as its manufacturer while every instance of it is
# the CONNECTOR.
#
# WHAT THIS CHECKS.  For every cached symbol that carries a Manufacturer, the
# canonical company must equal the canonical company of EVERY instance that
# uses it.  Normalisation is `canonical_manufacturer`, so a reviewed alias --
# `MEIHUA` against `MEIHUA (Lianyungang Meihua Electronic Technology)` -- is
# one company and a genuine contradiction is not.
# --------------------------------------------------------------------------
def embedded_symbol_cache_rows():
    """{lib_id: {cache: {...}, instances: {mfr: [refs]}}} over every sheet."""
    out = {}
    for sheet in sorted(rl.PROJECT.glob("*.kicad_sch")):
        text = sheet.read_text(encoding="utf-8", errors="replace")
        lib = text.find("(lib_symbols")
        if lib >= 0:
            end = text.find("\n\t(symbol\n", lib)
            blk = text[lib:end if end > 0 else len(text)]
            for m in re.finditer(
                    r'\(symbol "([^"]+)"\n(.*?)(?=\n\t\t\(symbol "[A-Za-z]|\Z)',
                    blk, re.S):
                name, body = m.group(1), m.group(2)
                if re.search(r"_\d+_\d+$", name):
                    continue
                mm = re.search(r'\(property "Manufacturer" "([^"]*)"', body)
                if not mm:
                    continue
                row = out.setdefault(name, dict(instances={}))
                row["cache"] = dict(
                    manufacturer=mm.group(1),
                    mpn=(re.search(r'\(property "MPN" "([^"]*)"', body)
                         or [None, ""])[1] if re.search(
                             r'\(property "MPN" "([^"]*)"', body) else "",
                    datasheet=(re.search(
                        r'\(property "Datasheet" "([^"]*)"', body).group(1)
                        if re.search(r'\(property "Datasheet" "([^"]*)"', body)
                        else ""),
                    sheet=sheet.name)
        for m in re.finditer(r'\(lib_id "([^"]+)"\)(.{0,8000}?)\(instances',
                             text, re.S):
            lib_id, body = m.group(1), m.group(2)
            mm = re.search(r'\(property "Manufacturer" "([^"]*)"', body)
            ref = re.search(r'\(property "Reference" "([^"]*)"', body)
            if not mm:
                continue
            row = out.setdefault(lib_id, dict(instances={}))
            row["instances"].setdefault(mm.group(1), []).append(
                ref.group(1) if ref else "?")
    return {k: v for k, v in out.items() if v.get("cache")}


def judge_embedded_symbol_cache(rows=None):
    rows = embedded_symbol_cache_rows() if rows is None else rows
    findings, problems = {}, []
    for lib_id, row in sorted(rows.items()):
        cache_mfr = canonical_manufacturer(row["cache"]["manufacturer"])
        inst = {canonical_manufacturer(k): sorted(v)
                for k, v in row["instances"].items()}
        disagreeing = sorted(k for k in inst if k and k != cache_mfr)
        # ...and the cached DATASHEET may not name a company the cached
        # MANUFACTURER is not.  That is how the retired onsemi PDF survived.
        ds = (row["cache"].get("datasheet") or "").lower()
        ds_bad = bool(
            ds and cache_mfr
            and any(tok in ds for tok in ("onsemi.com", "onsemi/"))
            and cache_mfr != "onsemi")
        d = dict(cache=row["cache"],
                 cache_manufacturer_canonical=cache_mfr,
                 instances={k: v for k, v in row["instances"].items()},
                 disagreeing_instances=disagreeing,
                 datasheet_names_another_company=ds_bad,
                 ok=not disagreeing and not ds_bad)
        if not d["ok"]:
            problems.append(lib_id)
        findings[lib_id] = d
    return (not problems), dict(
        symbols=sorted(findings), findings=findings, problems=problems,
        method="every embedded `lib_symbols` cache entry that carries a "
               "Manufacturer must canonicalise to the same company as every "
               "INSTANCE that uses it, and its cached Datasheet may not point "
               "at a different company's site.  F13 reads instance properties "
               "because that is what the BOM is built from; the cache is what "
               "a HUMAN sees when they open the symbol, and D-794 found it "
               "naming onsemi -- and onsemi's RETIRED NTMD4820N datasheet -- "
               "on the AOS pass pair.")


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
        # D-794 / R13-04.  ONE PRIMITIVE AUTHORITY, AND NOT "THE SAME FORMULA
        # WRITTEN TWICE".
        #
        # Round-13 asks to "bind all pair-budget consumers to one
        # independently checked primitive authority".  D-793 had F6 and
        # `audit_rail_ampacity` each evaluate `typ_hi * acc_hi` from the same
        # inputs -- which is not one authority, it is two copies that happened
        # to agree.  They stopped agreeing the moment one of them rounded: the
        # audit's design current came out 0.804861 A against F6's
        # 0.80486138... A, and the coverage clause read that 6e-7 A as a stale
        # audit.  A rounding artefact is a false alarm, but the SHAPE is the
        # real defect, because the same two copies could have differed by a
        # volt and nothing would have noticed either.
        #
        # So the band is now taken FROM `aqroot_power_model.ilim_band_A`, the
        # function the audit calls, at the resistor value read off the
        # SCHEMATIC.  The schematic remains the source of the resistor -- that
        # independence is the point of reading it here -- and the clause below
        # requires the schematic and the model's programmed table to agree, so
        # a resistor changed in one place and not the other FAILS instead of
        # silently splitting the two consumers again.
        band = apm.ilim_band_A(r, tol)
        rails[rail] = dict(ref=ref, r_ohms=r, r_tol=tol,
                           ilim_min=band["min_A"],
                           ilim_typ=typ,
                           ilim_max=band["max_A"],
                           ilim_authority="aqroot_power_model.ilim_band_A",
                           ilim_programmed_ohm_in_model=(
                               apm.ILIM_PROGRAMMED_OHM.get(rail)),
                           ilim_schematic_matches_the_model=bool(
                               apm.ILIM_PROGRAMMED_OHM.get(rail) == r
                               and apm.ILIM_RESISTOR_TOLERANCE == tol),
                           ilim_classification=band["classification"],
                           ilim_measurement_of_record=(
                               band["measurement_of_record"]),
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

    def ibat(i3, i5, internal=None):
        return (((I_INTERNAL if internal is None else internal) + i3)
                * V_3V3 / ETA_U12
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
        both_limiters_in_fault=ibat(a3["ilim_max"], a5["ilim_max"]),
        # D-801 / D801-04: the same double fault at the internal load the
        # production image ADMITS beside a live rail -- the real fault case.
        both_limiters_in_fault_at_the_admitted_internal_load=ibat(
            a3["ilim_max"], a5["ilim_max"],
            internal=I_INTERNAL_ADMITTED_WITH_A_RAIL))
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
                             "both_limiters_in_fault",
                             "both_limiters_in_fault_at_the_admitted_"
                             "internal_load")
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
             fuse_A=FUSE_A,
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
    # D-800 / D800-KNOWN-05 (Opus R19-03): a GUARANTEED key stated twice --
    # a bad copy after a good one, a bad one before, or identical -- is
    # refused before any projection.
    _g0 = next(r for r in apm.registry()
               if str(r["tag"]).startswith("GUARANTEED"))
    _g0_bad = dict(_g0, value=(_g0["value"] * 1.5 if isinstance(
        _g0["value"], (int, float)) else "tampered"))
    d["the_provenance_rule_refuses_a_duplicated_guarantee"] = bool(
        not [r for r in apm.audit_tags()["invalid_ruling_use"]
             if "stated" in r.get("why", "")]
        and all(any("stated 2 times" in r.get("why", "")
                    for r in apm.audit_tags(m_)["invalid_ruling_use"])
                for m_ in (apm.registry() + [_g0_bad],
                           [_g0_bad] + apm.registry(),
                           apm.registry() + [dict(_g0)])))

    # ======================================================================
    # D-794 / R13-05.  THE ROLE-MISCLASSIFICATION CONTROLS, INCLUDING THE ONE
    # ASTRA RAN.
    #
    # ROUND-13, IN ITS OWN WORDS: "Astra changed passpair.rds_hot_ratio_ruling
    # from DECLARED_ESTIMATE to GUARANTEED_MAX and gates stayed green; that
    # must fail.  ...  Audit every GUARANTEED_* primitive against exact
    # document row/condition and add role-misclassification negative
    # controls."
    #
    # Each control below RELABELS one registry entry and the rule must refuse
    # it.  The first is Astra's own mutation, by key, by tag and by direction.
    # ======================================================================
    def _relabel(key, **fields):
        out = []
        for r in apm.registry():
            if r["key"] == key:
                r = dict(r, **fields)
            out.append(r)
        return out

    _role_controls = {}
    # 1  ASTRA'S MUTATION.  A DECLARED widening relabelled a manufacturer
    #    maximum.  It is refused three times over: the key is not in
    #    GUARANTEED_ROWS, it carries `widened_from`, and its source text
    #    opens with the word DECLARED.
    _role_controls["astra_declared_widening_relabelled_guaranteed_max"] = bool(
        apm.audit_tags(_relabel("passpair.rds_hot_ratio_ruling",
                                tag=apm.GUARANTEED_MAX,
                                role=apm.DEVICE_BOUND))["invalid_ruling_use"])
    # 2  A guarantee whose SOURCE TEXT no longer names the document it claims.
    _role_controls["a_guarantee_whose_source_lost_its_document"] = bool(
        apm.audit_tags(_relabel(
            "bq.ron_in_max_ohm",
            source="the input FET's on-resistance."))["invalid_ruling_use"])
    # 3  A guarantee whose source no longer names its ROW.
    _role_controls["a_guarantee_whose_source_lost_its_row"] = bool(
        apm.audit_tags(_relabel(
            "bq.ilim_max_A",
            source="TI SLUSF65B, the input current limit."))[
                "invalid_ruling_use"])
    # 4  A guarantee with its CONDITION removed -- the D-789 defect, spelled
    #    as an omission rather than as a wrong row.
    _role_controls["a_guarantee_with_no_stated_condition"] = bool(
        apm.audit_tags(_relabel("bq.vsys_reg_accuracy", condition=None))[
            "invalid_ruling_use"])
    # 5  A SUPPLY REQUIREMENT relabelled a device bound -- R12-05's ESP32
    #    IVDD instance, kept alive as a control rather than as a memory.
    _role_controls["a_supply_requirement_relabelled_a_device_bound"] = bool(
        apm.audit_tags(_relabel("mcu.ivdd_supply_requirement_A",
                                role=apm.DEVICE_BOUND))["invalid_ruling_use"])
    # 6  A POLICY BUDGET dressed as a datasheet guarantee.
    _role_controls["a_policy_budget_relabelled_a_datasheet_guarantee"] = bool(
        apm.audit_tags(_relabel("policy.acc_3v3_published_budget_A",
                                tag=apm.GUARANTEED_MIN,
                                role=apm.DEVICE_BOUND))["invalid_ruling_use"])
    # 7  A DERIVED CORNER of a guaranteed band relabelled a second guarantee.
    _role_controls["a_derived_corner_relabelled_a_guarantee"] = bool(
        apm.audit_tags(_relabel("path.r75_sense_max_ohm",
                                tag=apm.GUARANTEED_MAX))["invalid_ruling_use"])
    d["role_misclassification_controls"] = dict(
        _role_controls,
        guaranteed_entries=_tags["guaranteed_entries"],
        guaranteed_rows_table=_tags["guaranteed_rows_table"],
        why="R13-05: a role check that only tests enum membership is a TYPE "
            "check.  A guarantee is a claim about a NAMED DOCUMENT ROW at a "
            "NAMED CONDITION, so every GUARANTEED_* entry must appear in "
            "`GUARANTEED_ROWS`, must repeat its document and row tokens in "
            "its own source text, must state a condition, may not be widened "
            "from anything, and may not open its source with the word "
            "DECLARED.  Each control below relabels ONE entry and the rule "
            "must refuse it.")
    d["every_role_misclassification_control_is_refused"] = bool(
        all(_role_controls.values()))

    # ======================================================================
    # D-795 / R14-06.  EVERY GUARANTEE IS RE-FOUND IN ITS PRIMARY DOCUMENT.
    #
    # ROUND-14: "a TYP-only row cannot become GUARANTEED by changing the tag
    # plus adding a row to a mutable allow-list. ... do not let two source
    # edits manufacture certainty."  `checks/guarantee_evidence.py` binds
    # every GUARANTEED_* to an archived document by sha256, re-finds the
    # verbatim row in that document's own extracted text, and requires a MIN
    # or MAX column (or a MAX word, a <= sign, a +/- code) behind the value.
    # The controls are Round-14's own counterexamples.
    # ======================================================================
    import guarantee_evidence as _ge
    _ev_ok, _ev = _ge.audit(apm.registry(), apm.GUARANTEE_EVIDENCE_SHA256)
    _ev_doc = json.loads(_ge.EVIDENCE.read_text(encoding="utf-8"))

    def _ev_with(rows_over, reg=None, pinned=None):
        ev2 = json.loads(json.dumps(_ev_doc))
        ev2["rows"].update(rows_over)
        ok, rep_ = _ge.audit(reg if reg is not None else apm.registry(),
                             apm.GUARANTEE_EVIDENCE_SHA256, evidence=ev2)
        return ok

    _vdppm = [r for r in apm.registry() if r["key"] == "bq.vdppm_V"][0]
    _ev_controls = dict(
        # the D-794 two-edit upgrade: re-tag a TYP row and add its REAL line
        # to the evidence -- the header has no MIN or MAX column
        a_typ_row_retagged_with_its_real_line_is_refused=not _ev_with(
            {"bq.vdppm_V": dict(
                document="SLUSF65B", row_token="VDPPM",
                row_lines=["VDPPM 0.1 V"], semantics="MAX",
                columns_header=["TYP"], columns=["0.1"], value_token="0.1",
                scale=1.0, condition="VBAT = 3.6 V")},
            reg=_relabel("bq.vdppm_V", tag=apm.GUARANTEED_MAX,
                         role=apm.DEVICE_BOUND,
                         condition="VBAT = 3.6 V")),
        # ...and with a FABRICATED MAX column the row is not in the document
        a_fabricated_max_column_is_not_in_the_document=not _ev_with(
            {"bq.vdppm_V": dict(
                document="SLUSF65B", row_token="VDPPM",
                row_lines=["VDPPM 0.1 0.15 V"], semantics="MAX",
                columns_header=["TYP", "MAX"], columns=["0.1", "0.15"],
                value_token="0.15", scale=1.0, condition="VBAT = 3.6 V")},
            reg=_relabel("bq.vdppm_V", tag=apm.GUARANTEED_MAX,
                         value=0.15, role=apm.DEVICE_BOUND,
                         condition="VBAT = 3.6 V")),
        # Astra's Round-13 relabel has no evidence row at all
        astras_relabel_has_no_primary_row=not _ge.audit(
            _relabel("passpair.rds_hot_ratio_ruling",
                     tag=apm.GUARANTEED_MAX, role=apm.DEVICE_BOUND),
            apm.GUARANTEE_EVIDENCE_SHA256)[0],
        # an evidence file edited without re-pinning its sha256
        an_unpinned_evidence_edit_is_refused=not _ge.audit(
            apm.registry(), "0" * 64)[0],
        # a guarantee whose condition says it is a typical
        a_typical_condition_is_refused=not _ge.audit(
            _relabel("bq.ron_in_max_ohm", condition="typical at 25 C"),
            apm.GUARANTEE_EVIDENCE_SHA256)[0],
        # a value that is not the row's
        a_value_that_is_not_the_rows_is_refused=not _ge.audit(
            _relabel("bq.ilim_max_A", value=1.150),
            apm.GUARANTEE_EVIDENCE_SHA256)[0],
        # D-795 found: D-794's VSYS_REG GUARANTEED_MAX was a TYP-only row
        d794s_vsys_reg_guarantee_is_refused=not _ge.audit(
            _relabel("bq.vsys_reg_V", tag=apm.GUARANTEED_MAX,
                     role=apm.DEVICE_BOUND, condition="VBATREG <= 4.3 V"),
            apm.GUARANTEE_EVIDENCE_SHA256)[0])
    # D-796 / R15-03 + R15-04: the Round-15 attacks (unrelated-row repin,
    # fabricated header, three-edit TYP->MAX, direction flip, invented MAX,
    # symbol mismatch, ...) re-pinned in memory; the document must refuse them
    _ev_dc = _ge.destructive_controls(apm.registry())
    d["guarantees_are_bound_to_primary_rows"] = dict(
        ok=bool(_ev_ok), report=_ev, controls_refused=_ev_controls,
        every_control_is_refused=bool(all(_ev_controls.values())),
        destructive_controls=_ev_dc,
        every_destructive_control_caught=bool(_ev_dc and all(
            _ev_dc.values())),
        found_by_this_audit=[
            "bq.vsys_reg_V: VSYS_REG is a TYP-only row (4.5 V); the "
            "guarantee is VSYS_REG_ACC -2/+2 %, now its own GUARANTEED entry",
            "bq.ilim_min_A / bq.ilim_max_A: cited Table 6-1, which is a "
            "resistor map; the 995/1100 mA figures are the EC ILIM row",
            "passpair.rds_hot_ratio_published: a ratio of two MAX rows is "
            "not a guaranteed maximum ratio -- DERIVED",
            "path.r75_sense_nominal_ohm: a nominal is not a bound -- DERIVED; "
            "the tolerance is bound to Bourns' own F = +/-1 % code",
            "path.inner_copper_thickness_m: an ORDER parameter with no "
            "archived fab tolerance -- DECLARED_ESTIMATE",
            "usb.vbus_source_max_V / min_V: a USB 2.0 table this repository "
            "never held -- now a DECLARED supply requirement on the named "
            "adapter"])
    d["guarantees_are_bound_to_primary_rows_ok"] = bool(
        _ev_ok and all(_ev_controls.values()) and _ev_dc
        and all(_ev_dc.values()))

    # ---- D-787 / R6-A01: main +3V3 delivery is an explicit contract -------
    d["p3v3_setpoint"] = p3v3
    d["p3v3_divider_parts_have_a_published_temperature_coefficient"] = (
        divider_parts_are_known)
    d["p3v3_reinforcement_is_exact_and_bounded"] = reinforcement_identity_ok
    # ---- D-794 / R13-06.  THE RECORD'S OWN VOLTAGES ARE DERIVED TOO. -----
    #
    # ROUND-13: "Current fab notes and FIRST_FIVE_ASSEMBLY_PLAN retain
    # obsolete delivery voltages ... Regenerate all current-facing normative
    # instructions from the FINAL D-794 policy/model."
    #
    # `ACC_3V3_REINFORCEMENT.json` is not a narrative: `export_fab_package`
    # reads it and PRINTS its voltages into the fab notes an assembler is
    # handed.  D-793 shipped it carrying the D-789-era 2.849642 / 2.982890 V
    # pair, three derivations out of date, and the exported notes carried them
    # too -- because the identity check above asks whether the record is
    # CONSISTENT, never whether its numbers are the ones this release derives.
    # Now it does, to the precision the record prints at.
    _rec_ec = (reinforcement or {}).get("electrical_consequence") or {}
    _rec_need = {
        "published_minimum_without_it_V": round(
            p3v3["delivered_at_400mA_min_V"], 6),
        "published_minimum_fully_mated_V": round(
            p3v3["delivered_at_400mA_fully_mated_V"], 6),
    }
    _rec_bad = sorted(
        k for k, v in _rec_need.items()
        if _rec_ec.get(k) is None or abs(float(_rec_ec[k]) - v) > 5e-7)
    d["the_reinforcement_record_quotes_the_derived_delivery"] = dict(
        file=str(ACC_3V3_REINFORCEMENT.relative_to(ROOT)),
        required=_rec_need,
        recorded={k: _rec_ec.get(k) for k in _rec_need},
        disagreeing=_rec_bad,
        ok=not _rec_bad,
        why="the exported fab notes PRINT these two numbers from this file, "
            "so a stale record is an assembler reading a retired delivery "
            "voltage.  R13-06 asks for the current-facing instructions to be "
            "generated from the final model; this is the clause that makes "
            "the generator's input follow the model.")
    d["the_reinforcement_record_quotes_the_derived_delivery_ok"] = bool(
        not _rec_bad)
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
    # D-794 / R13-04: the SCHEMATIC resistor and the canonical model's
    # programmed table are the two ends of the single limiter authority.  If
    # they part company, every consumer that reads the model -- the ampacity
    # audit's design current, the accessory-limiter report, the documents
    # generated from it -- is describing a board that is not this one.
    d["ilim_programmed_resistors_match_the_canonical_model"] = all(
        v["ilim_schematic_matches_the_model"] for v in rails.values())
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
          and d["ilim_programmed_resistors_match_the_canonical_model"]
          and d["ilim_band_is_inside_ul2367_recognition"]
          and d["each_rail_guarantees_its_published_accessory_budget"]
          and d["recoverable_trip_is_ordered_below_the_latching_breaker"]
          and d["protection_ordering_survives_the_declared_wider_band"]
          and d["converters_can_source_their_worst_case_rail"]
          and d["no_typical_is_used_as_a_ruling_bound"]
          and d["every_ruling_input_carries_a_provenance_tag"]
          and d["the_provenance_rule_refuses_a_typical_bound"]
          and d["the_provenance_rule_refuses_a_duplicated_guarantee"]
          and d["every_role_misclassification_control_is_refused"]
          and d["guarantees_are_bound_to_primary_rows_ok"]
          and d["p3v3_divider_parts_have_a_published_temperature_coefficient"]
          and d["p3v3_reinforcement_is_exact_and_bounded"]
          and d["the_reinforcement_record_quotes_the_derived_delivery_ok"]
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
# D-801 / D801-05: the DECLARED bench condition of C-BAT-GATE-01.
PASS_PAIR_BENCH_AIR_C = 25.0


def judge_pass_pair_gate(design_amps, vin_min_V, spec=None, rows=None,
                         ambient_C=None, internal_air_C=None,
                         sustained_amps=None, ruling_ratio=None,
                         bench_air_C=None):
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

    # ---- D-801 / Round-20 D801-05 (Astra R20-05 + Fable R20-01).  THE
    # BENCH CONDITION C-BAT-GATE-01 IS RUN AT, DERIVED -- NOT COPIED.
    #
    # D-800's step, ledger and handoff carried D-791's 2.2845 A ceiling, a
    # 2.60 A peak, 1.9328 A sustained, 72.44 / 116.38 C and a 2.4124 V
    # prediction while F10 itself derived 2.0929 A at 80.83 C internal air,
    # 1.7745 A and 2.7 A -- and the ledger said the ruling case "must survive
    # at 2x", which at the enclosure condition it does not.  And none of
    # those figures is what a technician on a bench MEASURES: the enclosure
    # ceiling is solved in 80.83 C internal air, and the bench is an open
    # board in room air.  So F10 now solves the SAME four-channel model at
    # the DECLARED BENCH CONDITION and publishes, for each test current, the
    # worst-case VGS(Q2), pass-pair drop and junction the step compares a
    # measurement against, and the current at which VGS(Q2) reaches the
    # AO4800's 2.5 V row.  Every document figure is generated from here.
    _bench_air = PASS_PAIR_BENCH_AIR_C if bench_air_C is None else bench_air_C
    _bench_currents = []
    for _nm, _a in (("sustained thermal envelope", sustained_amps),
                    ("enclosure conduction ceiling", ceiling),
                    ("peak electrical envelope", design_amps)):
        if _a is not None:
            _bench_currents.append((_nm, round(_a, 4)))
    _bench_ceiling = apm.conduction_ceiling_A(_bench_air, drive, ruling_ratio,
                                              spec)
    _bench_currents.append(("bench crossing", round(_bench_ceiling, 4)))
    _bench_currents.sort(key=lambda x: x[1])
    out["bench_condition"] = dict(
        air_C=_bench_air,
        board="the assembled board OUT of the enclosure, horizontal, in "
              "still room air",
        board_above_air_K=spec["board_above_air_K"],
        hot_ratio=round(ruling_ratio, 6),
        gate_drive_V=drive,
        hold="each current held until the Q2 package-top temperature "
             "changes by less than 0.5 K per minute (at least 5 min)",
        vgs_criterion_V=spec["rds_on_lowest_published_vgs_V"],
        crossing_A=round(_bench_ceiling, 4),
        points=[dict(what=_nm, amps=_a, **{
            k_: v_ for k_, v_ in (
                ("worst_case_vgs_q2_V", _sv["per_device"]["Q2"][
                    "worst_case_vgs_V"]),
                ("pass_pair_drop_V", _sv["pass_pair_drop_V"]),
                ("channel_ohm_hot", _sv["channel_ohm_hot"]),
                ("junction_C", _sv["junction_C"]))})
            for _nm, _a in _bench_currents
            for _sv in (solve(_a, _bench_air),)],
        why="D-801 / R20-05: the enclosure ceiling is a model output at "
            "80.83 C internal air and is not what a bench measures; the "
            "bench validates the model's INPUTS (gate drive, RDS(on), hot "
            "ratio) at a stated condition, and F10 re-derives the enclosure "
            "ceiling from what it measures.")
    out["enclosure_2x_case"] = dict(
        ratio=2.0, amps=round(_rule_amps, 4), internal_air_C=round(air_peak, 3),
        worst_case_vgs_q2_V=cases["at_a_pessimistic_2x_ratio"]["per_device"][
            "Q2"]["worst_case_vgs_V"],
        meets_the_row=bool(cases["at_a_pessimistic_2x_ratio"][
            "every_device_meets_a_published_conduction_row"]))

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


def pass_pair_publication(pp, pkg):
    """D-801 / D801-05.  Every published gate-drive / pass-pair figure, as
    TEXT, generated from F10's own output (`pp`, from `judge_pass_pair_gate`)
    and the enclosure model (`pkg`, `audit_rail_ampacity.package_junction`).
    The documents must carry these strings verbatim; nothing is copied."""
    b = pp["bench_condition"]
    pts = b["points"]
    peak = pp["peak_case"]
    sus = pp.get("sustained_case") or pp["ruling"]
    ceil = pp["guaranteed_conduction_ceiling"]
    se = pkg["sustained_thermal_envelope"]

    def _vgs(c):
        return c["per_device"]["Q2"]["worst_case_vgs_V"]

    def _meets(c):
        m_ = (_vgs(c) - pp["rds_on_lowest_published_vgs_V"]) * 1000.0
        return ("**YES — %.1f mV**" % m_ if m_ >= 0
                else "**NO — %.1f mV short**" % -m_)
    pred = "; ".join(
        "at **%.4f A** (%s) `VGS(Q2)` ≥ **%.4f V**, drop ≤ **%.1f mV**"
        % (x["amps"], x["what"], x["worst_case_vgs_q2_V"],
           x["pass_pair_drop_V"] * 1000.0) for x in pts)
    step = (
        "`ΔVGATE` (GATE − `BAT_PROTECTED_P`), `VGS(Q2)` and the pass-pair "
        "drop (`BAT_RAW` − `BAT_SENSE`) on the fitted **`AO4800`**, every "
        "figure GENERATED FROM `demo_feature_contract` F10 (D-801 / "
        "`R20-05`).  **BENCH CONDITION (declared):** %s, at **%.1f °C** "
        "air; %s; `BAT_RAW` = 4.15 / 3.60 / 3.05 V from a bench supply in "
        "place of the pack (the LTC4368's guaranteed gate drive is the same "
        "**%.1f V** row across that range).  Draw the test current with an "
        "electronic load from `BAT_PROTECTED_P` (`TP15`) to `GND`, NOT "
        "through the system: the load then never passes `U11`'s BATFET, "
        "whose BATOCP could otherwise trip, and `U11`'s own battery cut-off "
        "near 3.05 V is irrelevant to the pass pair.  The pass-pair current "
        "is also the drop across `R75` (10 mΩ, `TP20` to `TP15`).  Read "
        "`VGS(Q2)` directly at `Q2`'s own leads (gate pin 2 or 4 to source "
        "pin 1 or 3).  At each current below record `ΔVGATE`, `VGS(Q2)`, "
        "the drop and the `Q2` package-top temperature, then step on in "
        "0.05 A increments to **%.4f A** and record the current at which "
        "`VGS(Q2)` reaches the AO4800's **%.1f V** row, if it does.  This "
        "is what converts the one thing NO candidate publishes — hot "
        "`RDS(on)` at `VGS` = 2.5 V — from an extrapolation into a measured "
        "bound.  The model's WORST-CASE prediction at this condition "
        "(minimum gate drive, the AO4800's MAX `RDS(on)` at its 2.5 V row, "
        "the DECLARED 25 → 125 °C ratio **%.2f**): %s; the bench crossing "
        "is **%.4f A**.  Also record the TURN-ON TIME from `SHDN` release to "
        "full enhancement: ADI specifies `IGATE(UP)` and `tD(ON)` only at "
        "`VIN` = 12 V.  The enclosure conduction ceiling (**%.4f A** at "
        "**%.2f °C** internal air) is NOT a bench quantity: F10 re-derives "
        "it from the measured drive and resistance  **OUTCOME:** PASS if at "
        "every point the measured `VGS(Q2)` is at or above, and the measured "
        "drop at or below, the model's worst-case prediction for that "
        "point, and `VGS(Q2)` does not reach %.1f V below the bench crossing "
        "of **%.4f A**; otherwise RECORD + ESCALATE and re-run F10, F12 and "
        "F14 with the measured gate drive and drop before acceptance." % (
            b["board"], b["air_C"], b["hold"], b["gate_drive_V"],
            pp["design_amps"], b["vgs_criterion_V"], b["hot_ratio"], pred,
            b["crossing_A"], ceil["ceiling_A"], ceil["internal_air_C"],
            b["vgs_criterion_V"], b["crossing_A"]))
    table = "\n".join((
        "| envelope | `I` | hot channel `RDS(on)` | `VGS(Q2)` | meets the "
        "2.5 V row? |",
        "|---|---|---|---|---|",
        "| **GUARANTEED-CONDUCTION CEILING** (DERIVED, %.2f °C internal air) "
        "| **%.4f A** | — | **%.4f V** | **the boundary itself** |" % (
            ceil["internal_air_C"], ceil["ceiling_A"],
            pp["rds_on_lowest_published_vgs_V"]),
        "| **PEAK electrical** | %.4f A | ≈ %.1f mΩ | **%.4f V** | %s |" % (
            peak["amps"], peak["channel_ohm_hot"] * 1000.0, _vgs(peak),
            _meets(peak)),
        "| **SUSTAINED thermal** | %.4f A | ≈ %.1f mΩ | **%.4f V** | %s |" % (
            sus["amps"], sus["channel_ohm_hot"] * 1000.0, _vgs(sus),
            _meets(sus)),
        "| **BENCH crossing** (`C-BAT-GATE-01`, %.1f °C air) | **%.4f A** | "
        "— | **%.4f V** | **the boundary itself** |" % (
            b["air_C"], b["crossing_A"], b["vgs_criterion_V"])))
    hs = pp["hot_ratio_sensitivity"]
    x2 = pp["enclosure_2x_case"]
    sensitivity = (
        "The DECLARED 25 → 125 °C ratio is **%.2f** (AOS measures %.4f on "
        "this die); the ruling case loses the 2.5 V row at a ratio of "
        "**%.4f**.  At a pessimistic **2×** ratio the sustained envelope "
        "does %s hold the row at the enclosure condition (`VGS(Q2)` **%.4f "
        "V** at %.4f A, %.2f °C internal air): the 2× case is REPORTED, not "
        "ruled on, and `C-BAT-GATE-01` measures the real coefficient." % (
            hs["declared_ruling_ratio"], hs["published_ratio"],
            hs["ratio_at_which_the_conduction_row_is_lost"] or float("nan"),
            "" if x2["meets_the_row"] else "NOT", x2["worst_case_vgs_q2_V"],
            x2["amps"], x2["internal_air_C"]))
    handoff = "\n".join((
        "> | **SUSTAINED THERMAL ENVELOPE** — the most the enclosure supports "
        "at 40 °C, bounded by the pouch's own 60 °C discharge window | "
        "**%.4f A** | %.2f °C | %.2f °C |" % (
            pkg["sustained_thermal_envelope_A"], se["internal_air_C"],
            se["tj_C"]),
        "> | **GUARANTEED-CONDUCTION CEILING** — the current at which `Q2`'s "
        "`VGS` leaves the `AO4800`'s lowest published `RDS(on)` row, at "
        "%.2f °C internal air (the bench figure `C-BAT-GATE-01` measures is "
        "%.4f A at %.1f °C air) | **%.4f A** | %.2f °C | — |" % (
            ceil["internal_air_C"], b["crossing_A"], b["air_C"],
            ceil["ceiling_A"], ceil["internal_air_C"]),
        "> | **PEAK ELECTRICAL ENVELOPE** — every subsystem at its published "
        "maximum, concurrently (not a thermal operating point) | %.4f A | "
        "%.2f °C | **%.2f °C** |" % (
            pp["design_amps"], pkg["internal_air_C"], pkg["predicted_tj_C"])))
    return dict(step=step, ledger_table=table, ledger_sensitivity=sensitivity,
                handoff_rows=handoff)


PASS_PAIR_STALE_FIGURES = ("2.2845", "2.4124", "1.9328", "72.44", "116.38",
                           "survive at 2×", "must survive at 2x")


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


# D-796 / Round-15 D796-06.  ONE SENTENCE SPLITTER FOR EVERY SEMANTIC SCAN.
#
# The stale-value scans split on `.`, `;` AND `:`, so "completion ceiling:
# 1.150 W" became two fragments -- "completion ceiling:" and "1.150 W" -- and
# a family that binds a number to the WORD beside it saw neither.  A colon
# introduces the value; it does not end the claim.  Sentences end at . ; ! ?
# (followed by whitespace) and at a blank line, nowhere else.
def _d796_sentences(text):
    return [x for x in re.split(r"(?<=[.;!?])\s+|\n\s*\n", text or "")
            if x.strip()]


# ==========================================================================
# D-797 / Round-16 D797-07.  CRITICAL DOCUMENT SEMANTIC BINDING MUST NOT
# DEPEND ON WORD ORDER.
#
# ROUND-16 (Astra R16-05, Fable R16-05): "Known false claims still pass when
# value/role order is reversed, when intervening clauses are inserted, or when
# represented as markdown tables."  Every D-796 family was a regex of the form
# `<role>.{0,N}?<value>`, so "3.85 V is the quiet row floor", "the quiet row,
# measured at the gauge with the display on, is 3.85 V" and "| quiet row |
# 3.85 V |" were three ways past the same family.
#
# THE APPROACH IS (B) -- SYMMETRIC, TABLE-AWARE FAMILIES -- NOT NLP.  The set
# of normative claims is finite and each family names a ROLE vocabulary and a
# VALUE shape.  Three primitives, none of which reads English:
#
#   _d797_tabulate  a markdown table row is rewritten as STRUCTURED PAIRS --
#                   one unit per `<row label> -- <column header>: <cell>` and
#                   one per whole row -- so a label/value cell pair is scanned
#                   as the claim it is, not as a string of pipes;
#   _d797_bind      a value binds to the NEAREST role mention in its unit, on
#                   EITHER side, within a reach, and never across another value
#                   of the same shape (the nearer value shields it).  Order
#                   and intervening clauses stop mattering; a sentence stating
#                   two rows ("the quiet row is 3.80 V and the audio row is
#                   3.85 V") binds each number to its own row;
#   co-occurrence   a non-numeric claim is a set of concepts that must ALL
#                   appear in one unit, in any order, with none of the
#                   family's negations.
#
# The release identifier is ONE constant.  The lead sets it when a release is
# frozen; a CURRENT (unfenced) heading or sentence that names an earlier
# release as the review target / status / content commit is then a stale
# claim, and a fenced/historical one is history.
# ==========================================================================
# D-801 / Round-20 D801-06 (Astra R20-06 + Fable R20-05).  IT WAS TYPED,
# AND IT WENT STALE.  This constant read "D-799" on the frozen D-800 target,
# and a CURRENT D-799 heading passed F1-F14 there.  It is now DERIVED from the
# same authority the MANIFEST's `assembly_drawings.release` is derived from --
# the newest `## D-NNN` heading of the release CHANGELOG -- and
# `release_identity_problems` below binds every current identity surface
# (MANIFEST, CTO_DECISIONS, CURRENT_STATE's review-target heading, the fab
# handoff STATUS, the review-target evidence record) to it.
RELEASE_CHANGELOG = ROOT / "docs/full-beta-v2/CHANGELOG.md"


def derive_current_release(changelog_text=None):
    text = (RELEASE_CHANGELOG.read_text(encoding="utf-8", errors="replace")
            if changelog_text is None else changelog_text)
    for line in text.splitlines():
        if line.startswith("## "):
            m = re.search(r"\bD-(\d{3})\b", line)
            if m:
                return "D-%s" % m.group(1)
    raise SystemExit("cannot derive the current release: no '## D-NNN' "
                     "heading in the CHANGELOG")


CURRENT_RELEASE_ID = derive_current_release()
_RT_HEADING = re.compile(r"^\s*>*\s*#{1,6}\s+\**(D-\d{3}) REVIEW TARGET\b"
                         r"(.*)$")
_STATUS_HEADING = re.compile(r"^\s*>*\s*#{1,6}\s+\**STATUS:\s*(D-\d{3})\b"
                             r"(.*)$")
_IDENTITY_FENCE = re.compile(r"HISTORICAL|SUPERSEDED|superseded|REJECTED")


def release_identity_problems(current, manifest_release, cto_text,
                              state_text, handoff_text, evidence_dir):
    """D-801 / D801-06.  Pure: every CURRENT identity surface must name
    `current`; every earlier one must be fenced HISTORICAL."""
    bad = []
    if manifest_release != current:
        bad.append("MANIFEST assembly_drawings.release is %r, the checker's "
                   "current release is %r" % (manifest_release, current))
    first_cto = next((m_.group(1) for m_ in (
        re.match(r"^## (D-\d{3})\b", l_) for l_ in cto_text.splitlines())
        if m_), None)
    if first_cto != current:
        bad.append("CTO_DECISIONS' newest decision is %r, not %r"
                   % (first_cto, current))
    for name, text, rx in (("CURRENT_STATE review target", state_text,
                            _RT_HEADING),
                           ("fab handoff STATUS", handoff_text,
                            _STATUS_HEADING)):
        heads = [(m_.group(1), bool(_IDENTITY_FENCE.search(m_.group(2))))
                 for m_ in (rx.match(l_) for l_ in text.splitlines()) if m_]
        if not heads:
            bad.append("%s: no heading found" % name)
            continue
        cur_heads = [h for h, fenced in heads if not fenced]
        if cur_heads != [current]:
            bad.append("%s: the unfenced (current) heading(s) are %r, "
                       "expected exactly [%r]" % (name, cur_heads, current))
        if heads[0] != (current, False):
            bad.append("%s: the FIRST heading is %r, not the current "
                       "release unfenced" % (name, heads[0]))
    rec = Path(evidence_dir) / ("d%s-review-target.json" % current[2:])
    try:
        dec = json.loads(rec.read_text(encoding="utf-8")).get("decision")
    except (OSError, ValueError):
        dec = None
    if dec != current:
        bad.append("%s: decision is %r, not %r" % (rec.name, dec, current))
    return bad
# D-797 / D797-02: the supervised-charging restriction for the accessory
# rails, in the exact words every operative document must print (the cell is
# generated from the model).
SUPERVISED_RAIL_RESTRICTION = (
    "do not run an accessory rail with the adapter attached unless the pack "
    "is at or above **%.2f V**")
# D-798 / D798-02: the rule is now a MATRIX over every combination the
# production image admits, one threshold, and a measurement method -- all
# generated from `supervised_charging_authority` below.  These are its words.
SUPERVISED_CHARGING_RULE = (
    "SUPERVISED CHARGING RULE (first five, D-799): with the adapter "
    "attached, a combination marked **SUPERVISED** may run only while the "
    "pack's open-circuit lower bound `OCV_lb` is at or above **%.2f V**; a "
    "combination marked **REFUSED WHILE CHARGING** may not run with the "
    "adapter attached at any cell; the firmware does not enforce either "
    "(there is no VBUS-present signal and `STAT2` is unrouted)")
SUPERVISED_DMM_UNCERTAINTY_V = 0.010   # DECLARED instrument requirement
SUPERVISED_DMM_SETTLE = (10.0, 0.002)  # DECLARED: held within 2 mV for 10 s


# ==========================================================================
# D-799 / D799-01 (Astra R18-01, Fable R18-01).  OCV_lb MUST BE A TRUE
# LOWER BOUND, NOT AN ESTIMATE.
#
# D-798 published OCV_lb = V(J4) - max(I_BAT, 0) x 0.265 ohm - 0.010 V.
# Round-18 reproduced five ways it sits ABOVE the pack's real open-circuit
# voltage: (a) the charge current read LOW (no current uncertainty was
# declared at all, so the DMM's 10 mV was the only margin); (b) the charge
# current FALLS while the pack's stored polarization -- the diffusion part of
# the declared DC resistance, which is a state with memory, not a resistor --
# is still there, so I_now x R does not bound it; (c) a bench shunt / ammeter
# inserted between J4 and the pack adds its own drop inside the J4 reading;
# (d) the detached elevation ICHG_max x 87.5 mOhm = 71.38 mV was printed
# ROUNDED DOWN to 0.071 V; (e) a current recorded with the opposite sign
# convention takes max(I, 0) = 0 and subtracts nothing.
#
# THE MODEL THE BOUND IS PROVED ON.  The pack is the linear equivalent
# circuit the power model already DECLARES: an ohmic part R0 plus any number
# of polarization branches Rk || Ck, with R0 + sum(Rk) <= PACK_DC_OHM (the
# declared DC resistance, diffusion included).  A branch's voltage is bounded
# by Rk x the largest CHARGE current in the pack's history (a discharge
# history only makes it negative, which lowers V(J4)), whatever its time
# constant -- so NO relaxation time is assumed anywhere.  The history bound is
# ICHG_max (the BQ25185's highest programmed fast-charge current, the only
# charger the declared domain admits), or the present current if higher.  So
#
#   V(J4) - OCV  <=  I_up x (harness + insertion)
#                  + max(I_up, ICHG_max) x PACK_DC_OHM
#
# with I_up the UPPER bound of the present current MAGNITUDE (the sign is not
# trusted: a discharge treated as a charge only lowers the bound).  Every
# subtractive allowance is rounded UP to the millivolt and the result DOWN.
# With the adapter DETACHED no charge source exists, the present current is a
# discharge (it only lowers V(J4)), and only the residual term remains.
# ==========================================================================
SUPERVISED_CURRENT_UNCERTAINTY = (0.010, 0.02)   # DECLARED: +/-(10 mA + 2 %
                                                 # of |reading|)
SUPERVISED_INSERTION_OHM_MAX = 0.100   # DECLARED admission cap on the meter's
                                       # series burden plus its added leads
# D-800 / D800-KNOWN-07 (Opus R19-05).  R_ins is ESTABLISHED, never assumed.
# D-799 admitted any R_ins from 0 to the cap and said "0 for a clamp meter";
# nothing stopped a technician with a SERIES meter from entering 0, and a
# 80 mOhm series path entered as 0 at 0.8 A puts OCV_lb 45 mV ABOVE the true
# OCV.  A record now names its current-meter TOPOLOGY: a clamp (no conductor
# broken) may record 0; a series meter or shunt records an UPPER BOUND on its
# inserted path, measured by one of the named methods -- never 0.
SUPERVISED_METER_TOPOLOGIES = ("clamp", "series")
SUPERVISED_INSERTION_METHODS = (
    "four_wire_measured",        # 4-wire milliohm meter across the whole
                                 # inserted path (meter on its RECORDING
                                 # range, fuse and leads included), pack
                                 # disconnected, plus that meter's uncertainty
    "burden_plus_leads_measured",  # the meter's published burden on the
                                   # FIXED recording range (full-scale burden
                                   # voltage / full-scale current) plus the
                                   # added leads measured 4-wire
)


def _ceil_mV(x):
    return math.ceil(round(x * 1000.0, 9)) / 1000.0


def _floor_mV(x):
    return math.floor(round(x * 1000.0, 9) - 1e-6) / 1000.0


def supervised_ocv_lower_bound(rec, method):
    """D-799 / D799-01.  (OCV_lb, problems, terms) for ONE supervised-
    charging record, from the ONE method dict F12 publishes.

    rec: adapter "attached" | "detached"; v_j4_V (DMM, J4.1 to J4.2);
    attached only: i_bat_A (the pack current at the same instant, either
    sign convention), current_meter ("clamp" or "series"), insertion_ohm
    (an UPPER bound on the current meter's series burden plus its added
    leads between J4 and the pack; 0 only for a clamp meter) and, for a
    series meter, insertion_method (one of SUPERVISED_INSERTION_METHODS)."""
    m = method
    why = []
    if not isinstance(rec, dict):
        return None, ["the record is not a record"], {}
    att = rec.get("adapter")
    if att not in ("attached", "detached"):
        why.append("the record does not say whether the adapter is attached "
                   "or detached (%r)" % (att,))
    v = rec.get("v_j4_V")
    if not _finite(v):
        why.append("V(J4) is missing or not finite (%r)" % (v,))
    i_up = 0.0
    ins = 0.0
    if att == "attached":
        i = rec.get("i_bat_A")
        ins = rec.get("insertion_ohm")
        if not _finite(i):
            why.append("with the adapter attached the pack current is "
                       "mandatory (%r)" % (i,))
        if not _finite(ins) or ins < 0.0:
            why.append("with the adapter attached the current meter's series "
                       "insertion resistance is mandatory (0 for a clamp "
                       "meter) (%r)" % (ins,))
        elif ins > m["insertion_ohm_max"] + 1e-12:
            why.append("the current meter's insertion %.3f ohm is above the "
                       "declared %.3f ohm admission cap"
                       % (ins, m["insertion_ohm_max"]))
        # D-800 / D800-KNOWN-07: the topology decides what R_ins may be.
        topo = rec.get("current_meter")
        if topo not in SUPERVISED_METER_TOPOLOGIES:
            why.append("with the adapter attached the record must name the "
                       "current meter's topology, clamp or series (%r)"
                       % (topo,))
        elif topo == "series" and _finite(ins):
            if ins <= 0.0:
                why.append("a SERIES meter or shunt breaks the pack lead and "
                           "has a burden: its insertion resistance is never "
                           "0 -- measure it (%r)" % (ins,))
            if rec.get("insertion_method") not in \
                    SUPERVISED_INSERTION_METHODS:
                why.append("a series meter's insertion resistance must be "
                           "MEASURED by a named method %r, not assumed (%r)"
                           % (SUPERVISED_INSERTION_METHODS,
                              rec.get("insertion_method")))
        if not why:
            a0, ag = m["current_uncertainty"]["offset_A"], \
                m["current_uncertainty"]["gain"]
            i_up = abs(i) + a0 + ag * abs(i)
    if why:
        return None, why, {}
    u_v = _ceil_mV(m["dmm_uncertainty_V"])
    series = m["harness_max_ohm"] + ins
    drop_series = _ceil_mV(i_up * series)
    residual = _ceil_mV(max(i_up, m["history_current_max_A"])
                        * m["pack_dc_ohm"])
    lb = _floor_mV(v - u_v - drop_series - residual)
    return lb, [], dict(i_up_A=round(i_up, 6), dmm_V=u_v,
                        series_ohm=round(series, 6),
                        series_drop_V=drop_series,
                        residual_and_pack_V=residual)


def _d798_ocv_formula(rec, method=None):
    """D-798's published formula, kept ONLY as the negative control."""
    v = rec["v_j4_V"]
    if rec["adapter"] == "attached":
        return v - max(rec["i_bat_A"], 0.0) * 0.265 - 0.010, [], {}
    return v - 0.071 - 0.010, [], {}


def supervised_ocv_truth_min(rec, method, r0_steps=8):
    """The LOWEST open-circuit voltage the declared domain admits behind a
    record -- the adversary, computed WITHOUT the published formula: every
    corner of the DMM error, the current error in both sign conventions, the
    split of the pack's DC resistance between its ohmic and polarization
    parts, the harness from zero to its hot-aged maximum, the insertion from
    zero to its recorded value, and the polarization state anywhere in
    [-Rp x I_discharge_max, +Rp x the largest charge current in history]."""
    m = method
    v = rec["v_j4_V"]
    uv = m["dmm_uncertainty_V"]
    a0, ag = m["current_uncertainty"]["offset_A"], m["current_uncertainty"]["gain"]
    rdc, rh = m["pack_dc_ohm"], m["harness_max_ohm"]
    if rec["adapter"] == "attached":
        i = rec["i_bat_A"]
        e = a0 + ag * abs(i)
        cands = {i - e, i + e, -i - e, -i + e}
        ins = rec["insertion_ohm"]
    else:
        cands = {0.0, -m["discharge_current_max_A"]}
        ins = 0.0
    worst = float("inf")
    for vt in (v - uv, v + uv):
        for it in cands:
            for k in range(r0_steps + 1):
                r0 = rdc * k / r0_steps
                rp = rdc - r0
                ih = max(m["history_current_max_A"], it)
                for vp in (rp * ih, -rp * m["discharge_current_max_A"]):
                    for rs in ((0.0, rh + ins) if it >= 0 else (0.0,)):
                        worst = min(worst, vt - it * (r0 + rs) - vp)
    return worst


def _d800_meter(ins):
    """The topology a physical insertion implies: none is a clamp, any is
    a series path measured four-wire."""
    return (dict(current_meter="clamp") if ins <= 0.0 else
            dict(current_meter="series", insertion_method="four_wire_measured"))


def supervised_ocv_bound_proof(method, formula=None):
    """D-799 / D799-01.  Is `formula` a TRUE lower bound over the declared
    domain?  Three independent attacks: the corner adversary over a record
    grid, a time-domain simulation of random two-branch packs through random
    charge / taper / fall / detach histories with random in-spec meter
    errors, and the five Round-18 witnesses.  Returns the violations."""
    import random
    f = formula or supervised_ocv_lower_bound
    m = method
    viol = []

    def judge(tag, rec, truth):
        lb, bad, _ = f(rec, m)
        if bad or lb is None:
            return
        if lb > truth + 1e-12:
            viol.append(dict(attack=tag, record=rec, ocv_lb=round(lb, 6),
                             true_ocv_min=round(truth, 6)))
    # 1. corner adversary over a record grid
    for att in ("attached", "detached"):
        for v in (3.90, 4.10, 4.20, 4.30):
            for i in ((-0.6, -0.05, 0.0, 0.02, 0.1, 0.4, 0.8158, 1.0)
                      if att == "attached" else (0.0,)):
                for ins in ((0.0, 0.05, m["insertion_ohm_max"])
                            if att == "attached" else (0.0,)):
                    rec = dict(adapter=att, v_j4_V=v, i_bat_A=i,
                               insertion_ohm=ins, **_d800_meter(ins))
                    judge("corner", rec, supervised_ocv_truth_min(rec, m))
    # 2. time-domain simulation
    rnd = random.Random(799)
    a0, ag = m["current_uncertainty"]["offset_A"], m["current_uncertainty"]["gain"]
    for trial in range(400):
        rdc = m["pack_dc_ohm"]
        w = [rnd.random() for _ in range(3)]
        s = sum(w)
        r0, r1, r2 = (rdc * x / s for x in w)
        t1, t2 = rnd.uniform(1.0, 60.0), rnd.uniform(60.0, 20000.0)
        ocv = rnd.uniform(3.9, 4.2)
        rh = rnd.uniform(0.0, m["harness_max_ohm"])
        ins = rnd.choice((0.0, rnd.uniform(0.0, m["insertion_ohm_max"])))
        v1 = v2 = 0.0
        dt = 1.0
        segs = [(rnd.uniform(0.2, 1.0) * m["history_current_max_A"],
                 rnd.uniform(10, 7200)),
                (rnd.uniform(0.0, 0.2), rnd.uniform(1, 1800)),
                (-rnd.uniform(0.0, 1.5), rnd.uniform(0, 600)),
                (rnd.uniform(0.0, 1.0) * m["history_current_max_A"],
                 rnd.uniform(1, 3600)),
                (rnd.uniform(0.0, 0.1), rnd.uniform(0, 120))]
        detach = rnd.random() < 0.4
        if detach:
            segs.append((-rnd.uniform(0.0, 1.2), rnd.uniform(0, 300)))
        for cur, dur in segs:
            n = max(1, int(dur / dt))
            for _ in range(n):
                v1 += dt * (cur * r1 - v1) / t1
                v2 += dt * (cur * r2 - v2) / t2
        i_now = segs[-1][0]
        vj4 = ocv + i_now * (r0 + rh + (ins if not detach else 0.0)) + v1 + v2
        vm = vj4 + rnd.uniform(-1, 1) * m["dmm_uncertainty_V"]
        e = a0 + ag * abs(i_now)
        im = i_now + rnd.uniform(-1, 1) * e / (1.0 + ag)
        if rnd.random() < 0.3:
            im = -im
        rec = (dict(adapter="detached", v_j4_V=vm) if detach else
               dict(adapter="attached", v_j4_V=vm, i_bat_A=im,
                    insertion_ohm=ins, **_d800_meter(ins)))
        judge("simulation", rec, ocv)
    # 3. the Round-18 witnesses, each a physical scenario with a KNOWN OCV
    for tag, rec, truth in supervised_ocv_witnesses(m):
        judge(tag, rec, truth)
    return viol


def supervised_ocv_witnesses(m):
    """The Round-18 classes as explicit physics (known OCV)."""
    rdc, rh = m["pack_dc_ohm"], m["harness_max_ohm"]
    r0 = apm.PACK_AC_IMPEDANCE_MAX_OHM
    rp = rdc - r0
    ih = m["history_current_max_A"]
    uv = m["dmm_uncertainty_V"]
    a0, ag = m["current_uncertainty"]["offset_A"], m["current_uncertainty"]["gain"]
    ocv = 4.050
    out = []
    # (a) current read low by its declared uncertainty, DMM high by its own
    it = 0.40
    im = (it - a0) / (1.0 + ag)
    out.append(("witness_a_current_error", dict(
        adapter="attached", v_j4_V=ocv + it * (rdc + rh) + uv,
        i_bat_A=im, insertion_ohm=0.0, current_meter="clamp"), ocv))
    # (b) current fell from ICHG_max to 50 mA, polarization still stored
    out.append(("witness_b_current_fall", dict(
        adapter="attached", v_j4_V=ocv + 0.05 * (r0 + rh) + rp * ih,
        i_bat_A=0.05, insertion_ohm=0.0, current_meter="clamp"), ocv))
    # (c) a 50 mOhm bench shunt with clip leads between J4 and the pack
    out.append(("witness_c_shunt_path", dict(
        adapter="attached", v_j4_V=ocv + it * (rdc + rh + 0.050),
        i_bat_A=it, insertion_ohm=0.050, current_meter="series",
        insertion_method="four_wire_measured"), ocv))
    # (d) the detached residual printed rounded down, DMM at its limit;
    # swept across sub-millivolt OCVs so the final floor cannot hide it
    for k in range(10):
        o_ = ocv + 0.0001 * k
        out.append(("witness_d_rounding", dict(
            adapter="detached", v_j4_V=o_ + rdc * apm.BQ25185["ichg_max_A"]
            + uv), o_))
        out.append(("witness_d_rounding", dict(
            adapter="detached", v_j4_V=o_ + rdc * ih + uv), o_))
    # (e) the current recorded discharge-positive
    out.append(("witness_e_sign_convention", dict(
        adapter="attached", v_j4_V=ocv + it * (rdc + rh),
        i_bat_A=-it, insertion_ohm=0.0, current_meter="clamp"), ocv))
    return out


_SUP_DISPOSITION_TEXT = dict(
    ANY_CELL="**ANY CELL**",
    FIRMWARE_FLOOR="**FIRMWARE FLOOR**",
    SUPERVISED="**SUPERVISED**",
    REFUSED_WHILE_CHARGING="**REFUSED WHILE CHARGING**",
    REFUSED_BY_FIRMWARE="**REFUSED BY FIRMWARE** (on battery too)")


def supervised_charging_markdown(cc):
    """D-798 / D798-02.  (matrix, method) markdown, generated from the ONE
    supervised-charging authority in F12's charge ceiling."""
    thr = cc["supervised_charging_threshold_V"]
    rows = ["| optional modes | accessory load | system power | while "
            "charging (adapter attached) |", "|---|---|---|---|"]
    for r in cc["supervised_charging_matrix"]:
        d = _SUP_DISPOSITION_TEXT[r["disposition"]]
        if r["disposition"] == "FIRMWARE_FLOOR":
            d += " (the image refuses it below a reported **%.2f V**)" % (
                r["firmware_reported_floor_V"])
        elif r["disposition"] == "SUPERVISED":
            d += " (`OCV_lb` at or above **%.2f V**)" % thr
        rows.append("| %s | %s | %.3f W | %s |" % (
            " + ".join(r["modes"]) or "none",
            r["load"].replace("_", " "), r["system_W"], d))
    m = cc["supervised_charging_method"]
    cu = m["current_uncertainty"]
    method = (
        "`OCV_lb` is a LOWER BOUND on the pack's open-circuit voltage, "
        "rounded DOWN to the millivolt (D-799).  With the adapter "
        "ATTACHED: `OCV_lb` = V(J4) − **%.3f V** − I_up × (**%.1f mΩ** + "
        "R_ins) − max(I_up, **%.3f A**) × **%.1f mΩ**, where I_up = |I_BAT| "
        "+ **%.3f A** + **%.0f %%** of |I_BAT| — the MAGNITUDE of the "
        "reading, whatever its sign convention — and R_ins is an UPPER "
        "BOUND on the current meter's series path between J4 and the pack, "
        "its burden plus its added leads, ESTABLISHED before the record and "
        "never assumed (D-800): with a DC clamp meter around one pack lead "
        "(no conductor broken) R_ins = 0; with a series DMM or shunt, fix "
        "its range (no auto-ranging) and, with the pack disconnected, "
        "measure the whole inserted path four-wire on that range, fuse and "
        "leads included — or take the meter's published full-scale burden "
        "voltage ÷ full-scale current on that range plus the added leads "
        "measured four-wire — and record that figure plus its own "
        "measurement uncertainty, rounded UP to the milliohm, with the "
        "topology and the method.  A series path is never recorded as 0; "
        "one above **%.0f mΩ** (a milliamp range, typically) is not "
        "admissible — use a clamp or the high-current range.  With the adapter "
        "DETACHED (no charge source): `OCV_lb` = V(J4) − **%.3f V** − "
        "**%.3f V**.  Every subtracted term is rounded UP to the "
        "millivolt.  V(J4) is a DMM reading (±%.3f V or better at 4.2 V) "
        "from J4.1 (`BAT_CONNECTOR_P`, red) to J4.2 (`GND`, black) on the "
        "board, and I_BAT is the pack current on a bench meter "
        "(±(%.0f mA + %.0f %%) or better) at the same instant.  Take both "
        "immediately before the change the rule admits — enabling a rail "
        "with the adapter attached, or attaching the adapter with a rail "
        "live — once the DMM has held within %.0f mV for %.0f s.  No "
        "cell-relaxation time is assumed anywhere: %.1f mΩ is the hot-aged "
        "harness; %.1f mΩ is the model's DECLARED pack DC resistance, ohmic "
        "part and every polarization branch together, and max(I_up, %.3f A) "
        "× %.1f mΩ — **%.3f V** whenever I_up is at or below %.3f A — bounds "
        "both the pack's own drop and every polarization its charge history "
        "can have stored, whatever the current is doing now, because this "
        "board's charger never charges above ICHG_max = %.3f A; a pack "
        "charged from any other source is outside the method.  The console "
        "`VCELL` is NOT admissible for this rule: while charging it reads "
        "`BAT_PROTECTED_P`, up to **%.3f V** above the cell." % (
            m["dmm_uncertainty_V"], m["harness_max_ohm"] * 1e3,
            m["history_current_max_A"], m["pack_dc_ohm"] * 1e3,
            cu["offset_A"], cu["gain"] * 100.0,
            m["insertion_ohm_max"] * 1e3,
            m["dmm_uncertainty_V"], m["residual_and_pack_V"],
            m["dmm_uncertainty_V"], cu["offset_A"] * 1e3, cu["gain"] * 100.0,
            m["settle"]["within_V"] * 1e3, m["settle"]["hold_s"],
            m["harness_max_ohm"] * 1e3, m["pack_dc_ohm"] * 1e3,
            m["history_current_max_A"], m["pack_dc_ohm"] * 1e3,
            m["residual_and_pack_V"], m["history_current_max_A"],
            m["history_current_max_A"],
            m["console_vcell_offset_while_charging_max_V"]))
    return "\n".join(rows), method


def _d797_release_number(tag):
    m = re.search(r"D-(\d{3,4})", str(tag))
    return int(m.group(1)) if m else None


_D797_TABLE_SEP = re.compile(r"^\s*\|?\s*:?-{2,}:?\s*(?:\|\s*:?-{2,}:?\s*)*\|?\s*$")


def _d797_is_table_row(line):
    s = line.strip()
    return s.startswith("|") and s.count("|") >= 2


def _d797_cells(line):
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|"):
        s = s[:-1]
    return [c.strip() for c in s.split("|")]


def _d797_tabulate(text):
    """Rewrite every markdown table in `text` as structured label/value units.

    Blockquote markers are stripped first (these documents put normative
    tables inside `>` blocks).  Each body row becomes, separated by blank
    lines so the sentence splitter sees each as its own unit:
      * one ROW unit        `label; header1: cell1; header2: cell2 ...`
      * one PAIR unit each  `header_i -- label: cell_i`
    A single row with no header (an appended `| quiet row | 3.85 V |`) is a
    body row with empty headers.  A markdown heading becomes its own unit.
    Everything else passes through unchanged."""
    lines = [re.sub(r"^\s*(?:>\s?)+", "", ln) for ln in (text or "").splitlines()]
    out, i = [], 0
    while i < len(lines):
        ln = lines[i]
        if _d797_is_table_row(ln):
            block = []
            while i < len(lines) and _d797_is_table_row(lines[i]):
                block.append(lines[i])
                i += 1
            hdr, body = None, block
            if len(block) >= 2 and _D797_TABLE_SEP.match(block[1]):
                hdr, body = _d797_cells(block[0]), block[2:]
            for row in body:
                if _D797_TABLE_SEP.match(row):
                    continue
                c = _d797_cells(row)
                label = c[0]
                # D-798 / D798-07 (Fable R17-05, Q7): the FIRST column's
                # header names what the row label IS -- "| STAT1 | meaning |"
                # over "| HIGH | charge complete |" is a claim about STAT1,
                # and dropping the header lost it.
                if hdr and hdr[0].strip() and label:
                    label = "%s: %s" % (hdr[0].strip(), label)
                pairs = [((hdr[k] if hdr and k < len(hdr) else ""), c[k])
                         for k in range(1, len(c))]
                out += ["", label + "; " + "; ".join(
                    (h + ": " + v) if h else v for h, v in pairs), ""]
                # the ROW LABEL is placed nearest the value: it names the row,
                # the header only names the column
                for h, v in pairs:
                    out += [("%s — %s: %s" % (h, label, v)) if h
                            else ("%s: %s" % (label, v)), ""]
            continue
        if re.match(r"^\s*#{1,6}\s", ln):
            out += ["", ln, ""]
        else:
            out.append(ln)
        i += 1
    return "\n".join(out)


def _d797_units(text):
    """Whitespace-normalised scan units: tables as pairs, paragraphs split at
    blank lines, then sentences by the one D-796 splitter."""
    units = []
    for para in re.split(r"\n\s*\n", _d797_tabulate(text)):
        flat = re.sub(r"\s+", " ", para).strip()
        if flat:
            units += [s for s in _d796_sentences(flat) if s.strip()]
    return units


def _d797_bind(sent, roles, value_rx, reach=90):
    """[(role_key, value_token)] -- every value in `sent` bound to its nearest
    role mention on either side, within `reach` characters, and never across
    another value of the same shape.  `roles` is [(key, regex)]; a role whose
    key is None is NEUTRAL: it absorbs a value (a bench setpoint, a period)
    so that value is not attributed to a real role, and reports nothing.
    Markdown emphasis and code ticks are removed before measuring distance."""
    s = re.sub(r"[*`]", "", sent)
    spans = []
    for key, rx in roles:
        for m in rx.finditer(s):
            spans.append((m.start(), m.end(), key))
    # overlapping role mentions: the longer one wins
    spans.sort(key=lambda t: (t[0], -(t[1] - t[0])))
    kept = []
    for sp in spans:
        if kept and sp[0] < kept[-1][1]:
            continue
        kept.append(sp)
    vals = [(m.start(), m.end(), m.group(1)) for m in value_rx.finditer(s)]
    out = []
    for vs, ve, tok in vals:
        best = None
        for rs, re_, key in kept:
            if re_ <= vs:
                lo, hi, d, before = re_, vs, vs - re_, True
            elif rs >= ve:
                lo, hi, d, before = ve, rs, rs - ve, False
            else:
                lo, hi, d, before = vs, vs, 0, True
            if d > reach:
                continue
            if any(lo <= a and b <= hi for a, b, _ in vals if (a, b) != (vs, ve)):
                continue                      # shielded by a nearer value
            # a clause boundary between them costs distance: in "3.20 V
            # retention, 3.85 V to enable a first rail" the second value
            # belongs to the clause it is in, not to the comma before it
            gap = s[lo:hi]
            pen = 40 if re.search(r"[,;:()\u2014\u2013]|\s-\s", gap) else 0
            cand = (d + pen, 0 if before else 1, key)
            if best is None or cand < best:
                best = cand
        if best is not None and best[2] is not None:
            out.append((best[2], tok))
    return out


def _d797_cooccur(sent, all_of, none_of):
    """A non-numeric claim: every concept present, in any order, and none of
    the family's negations."""
    return bool(all(rx.search(sent) for rx in all_of)
                and not (none_of is not None and none_of.search(sent)))


def _d797_junction_safe_published(cc):
    """What the model PUBLISHES as the charger's junction-safe power, read from
    the charge-ceiling dict and tolerant of its SHAPE.

    D-797: the universal junction-safe scalar is being retired for a
    CELL-CONDITIONED envelope.  This reads whatever the model publishes:
    every numeric value under a key that names a junction-safe or junction-
    limited power, at any depth (a scalar today, a per-cell table after the
    lead's re-derivation).  `universal` is True only while the model still
    publishes ONE top-level scalar and no per-cell junction-safe structure --
    when it does not, a junction-safe figure stated WITHOUT a cell condition
    is a retired universal claim, whatever its number."""
    vals, per_cell = set(), False

    def walk(o, key=""):
        nonlocal per_cell
        if isinstance(o, dict):
            for k, v in o.items():
                walk(v, k)
        elif isinstance(o, (list, tuple)):
            for v in o:
                if ("junction_safe" in str(key) or "charging_safe" in str(key)) \
                        and isinstance(v, (dict, list, tuple)):
                    per_cell = True
                walk(v, key)
        elif isinstance(o, (int, float)) and not isinstance(o, bool):
            # D-797: keys may be integers (the mode-bits floor table), and
            # the cell-conditioned envelope publishes under `charging_safe`.
            k = str(key).lower()
            if (("junction_safe" in k or "charging_safe" in k
                 or k.startswith("junction_published")
                 or k.startswith("junction_raw")) and k.endswith("_w")):
                vals.add("%.3f" % o)
                vals.add("%.2f" % o)
    walk(cc or {})
    top = (cc or {}).get("junction_safe_system_W")
    universal = bool(isinstance(top, (int, float)) and not per_cell
                     and not (cc or {}).get("junction_safe_is_cell_conditioned"))
    _umin = (cc or {}).get("charging_safe_universal_published_W", top)
    return dict(values=vals, universal=universal,
                universal_W=(top if universal else None),
                universal_min_W=(_umin if isinstance(_umin, (int, float))
                                 else None))


# ==========================================================================
# D-797 / Round-16 D797-06.  CHARGE COMPLETION AND FAULT STATE MUST BE
# UNIQUELY OBSERVABLE.
#
# Astra R16-04, in substance: "Current/voltage near VBATREG is insufficient to
# prove termination when VINDPM/DPPM/TREG may still be active.  STAT1 LOW is
# not uniquely a safety-timer fault."  SLUSF65B section 6.1.1.5: "If a
# regulation loop such as VINDPM, DPPM, or thermal regulation is active during
# the CV taper, termination does not occur ... After termination, the battery
# FET is disabled."  Table 6-2: STAT1 LOW is BOTH the recoverable faults
# (VIN_OVP, TS HOT, TS COLD, TSHUT, system short) AND the non-recoverable ones
# (ILIM/ISET short, BATOCP, safety timer).  `U11.3` STAT2 is unconnected by
# owner decision, so the pin that would tell them apart is not on the board.
#
# The C-PWR-CHARGE-02 classification is therefore an EXECUTABLE rule, here,
# over the observables a first-article bench can record -- and the plan must
# carry its thresholds formatted from this spec.  Datasheet figures come from
# the canonical charger record; the three bench criteria for "a sustained
# physical transition consistent with termination" are DECLARED test
# criteria, not datasheet rows, and are named as such.
# ==========================================================================
CHARGE_END_SPEC = dict(
    vdppm_V=apm.BQ25185["vdppm_V"],
    vindpm_track_V=apm.BQ25185["vindpm_track_V"],
    vindpm_track_vbat_floor_V=apm.BQ25185["vindpm_track_vbat_floor_V"],
    vindpm_fixed_V=apm.BQ25185["vindpm_fixed_V"],
    vsys_reg_V=apm.BQ25185["vsys_reg_V"],
    vsys_reg_accuracy=apm.BQ25185["vsys_reg_accuracy"],
    vbsup1_V=apm.BQ25185["vbsup1_V"],
    ilim_min_A=apm.BQ25185["ilim_min_A"],
    treg_low_C=apm.BQ25185["treg_typ_C"] - apm.BQ25185["treg_declared_band_K"],
    treg_high_C=apm.BQ25185["treg_typ_C"] + apm.BQ25185["treg_declared_band_K"],
    tshut_falling_C=135.0,          # SLUSF65B EC TSHUT_FALLING TYP
    vin_ovp_min_V=18.0,             # SLUSF65B EC VIN_OVP rising MIN
    tmaxchg_typ_min=360.0,          # SLUSF65B EC tMAXCHG, TYP only
    tmaxchg_declared_tolerance=apm.BQ25185["tmaxchg_declared_tolerance"],
    batocp_min_A=IBAT_OCP_TYP_A * (1.0 - IBAT_OCP_STATED_ACCURACY),
    sys_short_V=2.0,                # DECLARED: SYS collapsed = system short
    # DECLARED bench criteria for the BATFET-off transition (not datasheet):
    batfet_off_ibat_max_A=0.005,    # battery current at the meter floor
    batfet_off_vbat_relax_min_V=0.010,  # VBAT relaxes below its CV peak
    batfet_off_sustain_min=10.0,    # held for at least this long
    input_margin_V=0.050,           # DECLARED: "at the VINDPM threshold"
    ilim_margin=0.05,               # DECLARED: "at the input limit"
    # ---- D-798 / D798-03: the termination REGION and the record's validity.
    vbatreg_V=apm.BQ25185["vbatreg_V"],             # SLUSF65B VBATREG 4.2 V
    vbatreg_accuracy=apm.BQ25185["vbatreg_accuracy"],  # VREG_ACC +/-0.5 %
    vrch_typ_V=0.100,               # SLUSF65B EC VRCH TYP (no MIN/MAX)
    iterm_fraction=0.10,            # SLUSF65B 6.1.1.5: terminates at 10 % ICHG
    iterm_accuracy_max=0.10,        # SLUSF65B EC ITERM_ACC MAX +10 %
    ichg_max_A=apm.BQ25185["ichg_max_A"],
    # DECLARED: pack terminal to BAT pin while the CV taper still carries
    # ITERM -- the itemised cell-to-node path, hot pass pair (D-797 F12).
    pack_to_bat_pin_ohm_max=0.80,
    psi_jt_C_per_W=2.0,             # SLUSF65B 5.3 PSI_JT (JEDEC board)
    # DECLARED: a bench thermocouple on a 3 x 3 mm WSON top reads LOW by its
    # lead conduction, so the characterization parameter is taken x5 and the
    # probe's own uncertainty added before package temperature becomes TJ.
    psi_jt_declared_multiplier=5.0,
    thermocouple_uncertainty_K=2.0,
    meter_V_uncertainty=0.005,      # DECLARED: bench DMM on the V ranges
    # D-799 / D799-02: DECLARED bench current-meter offset and gain; a
    # signed current is judged only outside this band.
    meter_I_offset_A=0.005,
    meter_I_gain=0.02,
    record_window_max_s=60.0,       # DECLARED: one classification window
    # DECLARED physical ranges; outside them the reading is not a reading.
    ranges=dict(vbat_V=(2.0, 4.6), vsys_V=(0.0, 5.6), vin_V=(0.0, 30.0),
                iin_A=(-0.05, 1.6), ibat_A=(-3.5, 1.6),
                package_C=(-40.0, 200.0)),
    units=dict(vbat_V="V", vsys_V="V", vin_V="V", iin_A="A", ibat_A="A",
               package_C="C"),
)


def charge_end_plan_tokens(spec=None):
    """The figures C-PWR-CHARGE-02 must state, formatted from the spec."""
    s = CHARGE_END_SPEC if spec is None else spec
    return {
        "VDPPM": "VBAT + %d mV" % round(s["vdppm_V"] * 1000),
        "VINDPM": "VBAT + %d mV" % round(s["vindpm_track_V"] * 1000),
        "ILIM": "%d mA" % round(s["ilim_min_A"] * 1000),
        "TREG": "%.0f °C" % s["treg_low_C"],
        "tMAXCHG": "%.0f min" % s["tmaxchg_typ_min"],
        "timer window": "%.0f min" % (s["tmaxchg_typ_min"]
                                      * (1 - s["tmaxchg_declared_tolerance"])),
        "BATFET relax": "%d mV" % round(s["batfet_off_vbat_relax_min_V"] * 1000),
        "BATFET sustain": "%.0f min" % s["batfet_off_sustain_min"],
    }


CHARGE_END_SAMPLES = ("vbat_V", "vsys_V", "vin_V", "iin_A", "ibat_A",
                      "package_C", "stat1")
CHARGE_END_TIMER_FIELDS = dict(
    elapsed_fast_charge_min=float, ts_in_window=bool,
    ibat_discharge_max_A=float, iset_ilim_pins_normal=bool,
    latched_until_replug=bool, replug_restarts_charge=bool)
CHARGE_END_TRANSITION_FIELDS = ("start_s", "end_s", "ibat_max_A",
                                "vbat_peak_V", "vsys_min_V")


def _finite(x):
    return (isinstance(x, (int, float)) and not isinstance(x, bool)
            and math.isfinite(x))


def charge_end_record_problems(obs, spec=None):
    """D-798 / D798-03 (Astra R17-03, Fable R17-03).  Why a C-PWR-CHARGE-02
    record CANNOT be classified: every mandatory observation must exist, be a
    finite number in its declared unit and range (STAT1 exactly HIGH or LOW),
    and be time-stamped inside ONE classification window no longer than the
    declared maximum.  A junction temperature is never accepted as an input
    -- it is derived from the package temperature (`charge_end_junction_C`)."""
    s = dict(CHARGE_END_SPEC if spec is None else spec)
    why = []
    if not isinstance(obs, dict):
        return ["the record is not a record"]
    w = obs.get("window")
    if not (isinstance(w, dict) and _finite(w.get("start_s"))
            and _finite(w.get("end_s")) and w["start_s"] <= w["end_s"]):
        return ["no valid classification window (start_s <= end_s)"]
    if w["end_s"] - w["start_s"] > s["record_window_max_s"] + 1e-9:
        why.append("the classification window %.1f s is longer than the "
                   "declared %.0f s: its samples are not one observation"
                   % (w["end_s"] - w["start_s"], s["record_window_max_s"]))
    if "tj_C" in obs or "tj_C" in (obs.get("samples") or {}):
        why.append("a junction temperature was supplied as a measurement: "
                   "the bench measures the U11 PACKAGE; record package_C and "
                   "the junction is derived through PSI_JT")
    smp = obs.get("samples")
    if not isinstance(smp, dict):
        return why + ["no samples"]
    for k in CHARGE_END_SAMPLES:
        x = smp.get(k)
        if not isinstance(x, dict) or "value" not in x:
            why.append("%s is MISSING" % k)
            continue
        if not (_finite(x.get("t_s"))
                and w["start_s"] - 1e-9 <= x["t_s"] <= w["end_s"] + 1e-9):
            why.append("%s is not time-stamped inside the classification "
                       "window" % k)
        v = x["value"]
        if k == "stat1":
            if v not in ("HIGH", "LOW"):
                why.append("STAT1 is %r: unknown or unreadable STAT1 is "
                           "never a completion" % (v,))
            continue
        if not _finite(v):
            why.append("%s is not a finite number (%r)" % (k, v))
            continue
        if x.get("unit") != s["units"][k]:
            why.append("%s is in %r, not %r" % (k, x.get("unit"),
                                                s["units"][k]))
        lo, hi = s["ranges"][k]
        if not lo <= v <= hi:
            why.append("%s = %r is outside the physical range %r..%r"
                       % (k, v, lo, hi))
    return why


def charge_end_consistency_problems(obs, spec=None):
    """D-799 / D799-02 (Astra R18-02).  Why a VALID C-PWR-CHARGE-02 record
    is still PHYSICALLY IMPOSSIBLE -- every field finite and in range, the
    fields together not.  Checked before any heat or termination
    classification; any finding is FAULT / UNCLASSIFIED.

      * U11 is a linear path charger: SYS is fed from IN through the input
        FET (never above VIN) or from BAT through the BATFET (never above
        the pack), so SYS above both is a boost U11 cannot make;
      * input current flowing INTO IN reaches SYS only if VIN >= VSYS;
      * SYS is regulated to VSYS_REG and never sits above its maximum;
      * a charge current into the pack needs SYS above the pack and the
        power to come from the input; a discharge needs the pack above SYS;
      * the transition summary's own figures are in range, its interval
        is before the window ends, and every present sample that falls
        INSIDE that interval agrees with its extrema (a sample can never be
        below the summary's minimum or above its maximum)."""
    s = dict(CHARGE_END_SPEC if spec is None else spec)
    v = {k: obs["samples"][k]["value"] for k in CHARGE_END_SAMPLES}
    t_of = {k: obs["samples"][k]["t_s"] for k in CHARGE_END_SAMPLES}
    u = s["meter_V_uncertainty"]
    i0, ig = s["meter_I_offset_A"], s["meter_I_gain"]

    def iu(x):
        return i0 + ig * abs(x)
    sys_hi = s["vsys_reg_V"] * (1.0 + s["vsys_reg_accuracy"])
    why = []
    if v["vsys_V"] > max(v["vin_V"], v["vbat_V"]) + 2 * u:
        why.append("VSYS %.3f V is above both VIN %.3f V and the pack %.3f V:"
                   " U11 is a linear path and cannot boost SYS"
                   % (v["vsys_V"], v["vin_V"], v["vbat_V"]))
    # D-800 / D800-KNOWN-01 (Astra R19-01).  IIN is SIGNED, positive from
    # the adapter INTO the device.  The only path from the adapter is into
    # U11's IN through its blocking FETs (SLUSF65B 6.3.1), which always draw
    # IQ_IN (0.75 mA TYP) into IN, and no part of this board sources VBUS.
    # A reading whose WHOLE meter interval is below zero -- current flowing
    # OUT of the device into the adapter -- is not a state this board can
    # reach: a reversed meter, a mis-wired shunt or a different node.  An
    # interval that includes zero is an instrument offset and is accepted.
    if v["iin_A"] + iu(v["iin_A"]) < 0.0:
        why.append("IIN %.3f A is negative beyond the meter's +/-%.3f A: "
                   "current OUT of the device into the adapter, which the "
                   "blocking input path cannot carry -- check the meter's "
                   "polarity (positive is adapter INTO the device) and its "
                   "node" % (v["iin_A"], iu(v["iin_A"])))
    if v["iin_A"] > iu(v["iin_A"]) and v["vin_V"] < v["vsys_V"] - 2 * u:
        why.append("IIN %.3f A flows into IN while VIN %.3f V is below VSYS "
                   "%.3f V: no passive path carries it"
                   % (v["iin_A"], v["vin_V"], v["vsys_V"]))
    if v["vsys_V"] > sys_hi + u:
        why.append("VSYS %.3f V is above the VSYS_REG maximum %.3f V"
                   % (v["vsys_V"], sys_hi))
    if v["ibat_A"] > iu(v["ibat_A"]):
        if v["vsys_V"] < v["vbat_V"] - 2 * u:
            why.append("a charge current %.3f A into a pack at %.3f V from a "
                       "SYS at %.3f V: charge cannot flow uphill"
                       % (v["ibat_A"], v["vbat_V"], v["vsys_V"]))
        p_chg = v["vbat_V"] * (v["ibat_A"] - iu(v["ibat_A"]))
        p_in = (v["vin_V"] + u) * (max(v["iin_A"], 0.0) + iu(v["iin_A"]))
        if p_chg > p_in:
            why.append("the pack takes %.3f W of charge and the input "
                       "delivers at most %.3f W" % (p_chg, p_in))
    if v["ibat_A"] < -iu(v["ibat_A"]) and v["vbat_V"] < v["vsys_V"] - 2 * u:
        why.append("a discharge current %.3f A from a pack at %.3f V into a "
                   "SYS at %.3f V: discharge cannot flow uphill"
                   % (v["ibat_A"], v["vbat_V"], v["vsys_V"]))
    t = obs.get("batfet_off_transition")
    if isinstance(t, dict) and all(_finite(t.get(k))
                                   for k in CHARGE_END_TRANSITION_FIELDS):
        lo, hi = s["ranges"]["vsys_V"]
        if not lo <= t["vsys_min_V"] <= min(hi, sys_hi + u):
            why.append("the transition's VSYS minimum %.3f V is outside the "
                       "physical SYS range (at most VSYS_REG max %.3f V)"
                       % (t["vsys_min_V"], sys_hi))
        lo, hi = s["ranges"]["vbat_V"]
        if not lo <= t["vbat_peak_V"] <= hi:
            why.append("the transition's CV peak %.3f V is outside the pack "
                       "range" % t["vbat_peak_V"])
        if not 0.0 <= t["ibat_max_A"] <= s["ranges"]["ibat_A"][1]:
            why.append("the transition's |IBAT| maximum %.4f A is not a "
                       "magnitude in range" % t["ibat_max_A"])
        if t["start_s"] < 0.0 or t["start_s"] > obs["window"]["end_s"]:
            why.append("the transition starts at %.1f s, outside the record"
                       % t["start_s"])
        for k in CHARGE_END_SAMPLES:
            ts = t_of[k]
            if not (_finite(ts) and t["start_s"] - 1e-9 <= ts
                    <= t["end_s"] + 1e-9):
                continue
            x = v[k]
            if k == "vsys_V" and x < t["vsys_min_V"] - u:
                why.append("VSYS %.3f V at %.1f s lies inside the transition "
                           "and below its own recorded minimum %.3f V"
                           % (x, ts, t["vsys_min_V"]))
            if k == "vbat_V" and x > t["vbat_peak_V"] + u:
                why.append("the pack %.3f V at %.1f s lies inside the "
                           "transition and above its own recorded peak "
                           "%.3f V" % (x, ts, t["vbat_peak_V"]))
            if k == "ibat_A" and abs(x) > t["ibat_max_A"] + iu(x):
                why.append("|IBAT| %.4f A at %.1f s lies inside the "
                           "transition and above its own recorded maximum "
                           "%.4f A" % (abs(x), ts, t["ibat_max_A"]))
    return why


def charge_end_junction_C(vals, spec=None):
    """The U11 junction UPPER bound from the measured PACKAGE temperature:
    TJ <= T_package + PSI_JT x k x P_package + probe uncertainty, the package
    heat from the record's own terminals (input FET + charge FET).  Kept for
    callers that need the upper end only; `u11_junction_interval` is the
    D-799 authority."""
    lo, hi, p_pkg = u11_junction_interval(vals, spec)
    return hi, p_pkg


def u11_junction_interval(vals, spec=None):
    """D-799 / D799-03 (Astra R18-03).  (TJ_low, TJ_high, P_package).

    The package TOP temperature and the junction are separate quantities.
    With the package dissipating (P >= 0) heat flows from the die out
    through the top, so the junction is at or above the top reading less the
    probe's uncertainty; it is at most the top reading plus PSI_JT (SLUSF65B
    5.3, JEDEC board) x the DECLARED x5 multiplier x the package loss plus
    the probe uncertainty.  Only an interval wholly on one side of a
    threshold supports a physical conclusion (`judge_junction`)."""
    s = dict(CHARGE_END_SPEC if spec is None else spec)
    p_pkg = (max(0.0, (vals["vin_V"] - vals["vsys_V"]) * max(0.0,
                                                             vals["iin_A"]))
             + max(0.0, (vals["vsys_V"] - vals["vbat_V"])
                   * max(0.0, vals["ibat_A"])))
    u = s["thermocouple_uncertainty_K"]
    return (vals["package_C"] - u,
            vals["package_C"]
            + s["psi_jt_C_per_W"] * s["psi_jt_declared_multiplier"] * p_pkg
            + u, p_pkg)


def judge_junction(interval, threshold_low_C, threshold_high_C=None):
    """BELOW / ABOVE / INDETERMINATE for a junction interval against a
    threshold band [low, high] (high defaults to low).  BELOW needs the
    interval's TOP under the band's low end; ABOVE needs its BOTTOM at or
    over the band's high end; anything else overlaps and is INDETERMINATE
    -- never a controller contradiction and never inferred from the package
    temperature alone."""
    lo, hi = interval[0], interval[1]
    th_hi = threshold_low_C if threshold_high_C is None else threshold_high_C
    if hi < threshold_low_C:
        return "BELOW"
    if lo >= th_hi:
        return "ABOVE"
    return "INDETERMINATE"


def fa_throttle_observation(package_C, p_package_W, throttled, spec=None):
    """D-799 / D799-03.  The C-PWR-CHARGE-01 (r3) per-observation verdict.
    Throttling (the battery discharging with the adapter attached) with the
    junction interval WHOLLY BELOW TREG's declared low end falsifies the
    condition the no-discharge rows rest on: RECORD + ESCALATE.  An interval
    that overlaps the TREG band is INDETERMINATE: RECORD ONLY, no
    conclusion.  Wholly above, throttling is expected: RECORD ONLY."""
    s = dict(CHARGE_END_SPEC if spec is None else spec)
    u = s["thermocouple_uncertainty_K"]
    iv = (package_C - u, package_C + s["psi_jt_C_per_W"]
          * s["psi_jt_declared_multiplier"] * max(0.0, p_package_W) + u)
    side = judge_junction(iv, s["treg_low_C"], s["treg_high_C"])
    if not throttled:
        return "RECORD ONLY", side, iv
    if side == "BELOW":
        return "RECORD + ESCALATE", side, iv
    if side == "INDETERMINATE":
        return "INDETERMINATE / RECORD", side, iv
    return "RECORD ONLY", side, iv


def charge_end_termination_region(spec=None):
    """(CV-peak floor, CV-peak ceiling, present-VBAT floor) at the PACK.

    SLUSF65B 6.1.1.5: termination occurs in the CV phase at ITERM, then the
    BATFET opens and a new cycle starts if BAT falls VRCH below VBATREG.  So
    the CV peak recorded at the pack is VBATREG at its accuracy less ITERM x
    the pack-to-BAT-pin path, and a terminated pack sits at or above
    VBATREG - VRCH (otherwise a recharge would have started)."""
    s = dict(CHARGE_END_SPEC if spec is None else spec)
    reg_lo = s["vbatreg_V"] * (1.0 - s["vbatreg_accuracy"])
    reg_hi = s["vbatreg_V"] * (1.0 + s["vbatreg_accuracy"])
    iterm_max = s["ichg_max_A"] * s["iterm_fraction"] * (
        1.0 + s["iterm_accuracy_max"])
    u = s["meter_V_uncertainty"]
    return (reg_lo - iterm_max * s["pack_to_bat_pin_ohm_max"] - u,
            reg_hi + u, reg_lo - s["vrch_typ_V"] - u)


def classify_charge_end(obs, spec=None):
    """(class, reasons) for one C-PWR-CHARGE-02 record.  Classes:
    TERMINATED, ACTIVE LIMITING, TIMER EXPIRY, FAULT / UNCLASSIFIED, CHARGING,
    INDETERMINATE / RECORD.

    D-799 / D799-02: a valid record must also be PHYSICALLY POSSIBLE -- no
    SYS above both VIN and the pack, no input current against VIN < VSYS, no
    SYS above VSYS_REG max, no current flowing uphill, and a transition
    summary whose extrema agree with every sample inside its interval
    (`charge_end_consistency_problems`) -- or it is FAULT / UNCLASSIFIED.
    D-799 / D799-03: the junction is an INTERVAL from the package; TREG is
    excluded only wholly below its band, established only wholly above, and
    an overlap is INDETERMINATE / RECORD.

    D-798 / D798-03: nothing is classified from an INVALID record -- a
    missing, unreadable, non-finite, out-of-unit, out-of-range or stale
    observation, or an unknown STAT1, is FAULT / UNCLASSIFIED
    (`charge_end_record_problems`).  The junction is DERIVED from the package
    temperature, never read.

    STAT1 LOW is NEVER read as a timer expiry by itself: TIMER EXPIRY needs
    the elapsed fast-charge time inside the timer window, every recoverable
    cause excluded by measurement, the other latch-off causes excluded, the
    fault LATCHED with the adapter left in place, and an unplug/re-plug that
    starts a new cycle.  A current taper near VBATREG is NEVER termination by
    itself: TERMINATED needs every limiting loop excluded, the CV peak inside
    the VBATREG band, the present pack above the recharge threshold, AND the
    BATFET-off transition -- battery current at the meter floor NOW and over
    the whole transition, VBAT relaxed below its CV peak NOW, SYS at
    regulation -- sustained up to the present window."""
    s = dict(CHARGE_END_SPEC if spec is None else spec)
    bad = charge_end_record_problems(obs, s)
    if bad:
        return "FAULT / UNCLASSIFIED", ["INVALID RECORD: " + b for b in bad]
    # D-799 / D799-02: a valid record must also be POSSIBLE.
    bad = charge_end_consistency_problems(obs, s)
    if bad:
        return ("FAULT / UNCLASSIFIED",
                ["CONTRADICTORY RECORD: " + b for b in bad])
    w = obs["window"]
    v = {k: obs["samples"][k]["value"] for k in CHARGE_END_SAMPLES}
    g = obs.get
    tj_lo, tj, p_pkg = u11_junction_interval(v, s)
    if v["stat1"] == "LOW":
        missing = [k for k, typ in CHARGE_END_TIMER_FIELDS.items()
                   if (typ is bool and not isinstance(g(k), bool))
                   or (typ is float and not _finite(g(k)))]
        if missing:
            return ("FAULT / UNCLASSIFIED",
                    ["STAT1 LOW with %s unrecorded or invalid: STAT1 alone "
                     "does not identify the fault" % ", ".join(missing)])
        why = []
        if v["vin_V"] >= s["vin_ovp_min_V"]:
            why.append("VIN at or above VIN_OVP (recoverable)")
        if not g("ts_in_window"):
            why.append("TS HOT/COLD not excluded (recoverable)")
        if judge_junction((tj_lo, tj), s["tshut_falling_C"]) != "BELOW":
            why.append("TSHUT not excluded (recoverable): the junction "
                       "interval %.1f..%.1f C (package %.1f C) is not wholly "
                       "below TSHUT_FALLING" % (tj_lo, tj, v["package_C"]))
        if v["vsys_V"] < s["sys_short_V"]:
            why.append("system short not excluded (recoverable)")
        if g("ibat_discharge_max_A") >= s["batocp_min_A"]:
            why.append("BATOCP not excluded (latch-off)")
        if not g("iset_ilim_pins_normal"):
            why.append("ILIM/ISET pin short not excluded (latch-off)")
        lo = s["tmaxchg_typ_min"] * (1 - s["tmaxchg_declared_tolerance"])
        hi = s["tmaxchg_typ_min"] * (1 + s["tmaxchg_declared_tolerance"])
        if not lo <= g("elapsed_fast_charge_min") <= hi:
            why.append("elapsed fast-charge time %.0f min is outside the "
                       "timer window %.0f..%.0f min" % (
                           g("elapsed_fast_charge_min"), lo, hi))
        if not g("latched_until_replug"):
            why.append("the fault cleared by itself: that is a recoverable "
                       "fault, not a latched timer")
        if not g("replug_restarts_charge"):
            why.append("an unplug/re-plug did not start a new cycle")
        if why:
            return "FAULT / UNCLASSIFIED", why
        return "TIMER EXPIRY", ["every other STAT1 LOW cause excluded by "
                                "measurement; latched; cleared by re-plug"]
    vbat = v["vbat_V"]
    vindpm = (vbat + s["vindpm_track_V"]
              if vbat > s["vindpm_track_vbat_floor_V"] else s["vindpm_fixed_V"])
    loops = []
    if v["vin_V"] <= vindpm + s["input_margin_V"]:
        loops.append("VINDPM")
    if v["vsys_V"] <= vbat + s["vdppm_V"] + s["input_margin_V"]:
        loops.append("DPPM")
    if v["vsys_V"] < vbat - s["vbsup1_V"]:
        loops.append("SUPPLEMENT")
    if v["iin_A"] >= s["ilim_min_A"] * (1 - s["ilim_margin"]):
        loops.append("ILIM")
    _treg = judge_junction((tj_lo, tj), s["treg_low_C"], s["treg_high_C"])
    if _treg == "ABOVE":
        loops.append("TREG (junction interval %.1f..%.1f C, package %.1f C)"
                     % (tj_lo, tj, v["package_C"]))
    if loops:
        return "ACTIVE LIMITING", ["%s active: termination cannot occur"
                                   % "/".join(loops)]
    if _treg == "INDETERMINATE":
        # D-799 / D799-03: an interval overlapping the TREG band can
        # neither exclude the loop (so no termination) nor show it active.
        return ("INDETERMINATE / RECORD",
                ["the junction interval %.1f..%.1f C (package %.1f C, %.3f W)"
                 " overlaps TREG's %.0f..%.0f C band: TREG can be neither "
                 "excluded nor established; termination is not claimed"
                 % (tj_lo, tj, v["package_C"], p_pkg, s["treg_low_C"],
                    s["treg_high_C"])])
    sys_reg_lo = s["vsys_reg_V"] * (1 - s["vsys_reg_accuracy"])
    peak_lo, peak_hi, present_lo = charge_end_termination_region(s)
    t = g("batfet_off_transition")
    if t is None:
        if g("final"):
            return ("FAULT / UNCLASSIFIED",
                    ["loops excluded but no sustained BATFET-off transition "
                     "was observed: a taper is not a termination"])
        return "CHARGING", ["no loop active, no termination transition yet"]
    why = []
    if not isinstance(t, dict) or not all(
            _finite(t.get(k)) for k in CHARGE_END_TRANSITION_FIELDS):
        return ("FAULT / UNCLASSIFIED",
                ["the BATFET-off transition summary is missing a field or "
                 "carries a non-finite value (%s)"
                 % ", ".join(CHARGE_END_TRANSITION_FIELDS)])
    if not t["start_s"] < t["end_s"]:
        why.append("the transition ends before it starts")
    # STALE: the summary must run INTO the present window, so a present
    # measurement it has not seen cannot be overridden by it.
    if t["end_s"] < w["start_s"] - 1e-9 or t["end_s"] > w["end_s"] + 1e-9:
        why.append("the transition summary ends at %.1f s, outside the "
                   "present window %.1f..%.1f s: a stale summary"
                   % (t["end_s"], w["start_s"], w["end_s"]))
    sustained = (t["end_s"] - t["start_s"]) / 60.0
    if sustained < s["batfet_off_sustain_min"]:
        why.append("the BATFET-off transition is held %.1f min, under %.0f"
                   % (sustained, s["batfet_off_sustain_min"]))
    if t["ibat_max_A"] > s["batfet_off_ibat_max_A"]:
        why.append("the transition's battery current %.4f A is above the "
                   "%.3f A meter floor" % (t["ibat_max_A"],
                                           s["batfet_off_ibat_max_A"]))
    if abs(v["ibat_A"]) > s["batfet_off_ibat_max_A"]:
        why.append("the PRESENT battery current %.4f A contradicts the "
                   "transition summary: the BATFET is not off"
                   % v["ibat_A"])
    if abs(v["ibat_A"]) > t["ibat_max_A"] + 1e-12:
        why.append("the present battery current exceeds the summary's own "
                   "maximum: the summary is stale or wrong")
    if not peak_lo <= t["vbat_peak_V"] <= peak_hi:
        why.append("the CV peak %.3f V at the pack is outside the VBATREG "
                   "termination band %.3f..%.3f V: the part never reached CV"
                   % (t["vbat_peak_V"], peak_lo, peak_hi))
    relax = t["vbat_peak_V"] - vbat
    if relax < s["batfet_off_vbat_relax_min_V"]:
        why.append("the present VBAT has relaxed %.1f mV below the CV peak, "
                   "under %.0f mV" % (relax * 1e3,
                                      s["batfet_off_vbat_relax_min_V"] * 1e3))
    if vbat < present_lo:
        why.append("the present pack %.3f V is under VBATREG - VRCH = %.3f V:"
                   " a recharge would have started" % (vbat, present_lo))
    if t["vsys_min_V"] < sys_reg_lo or v["vsys_V"] < sys_reg_lo:
        why.append("SYS left regulation during the transition or now")
    if why:
        return "FAULT / UNCLASSIFIED", why
    return "TERMINATED", ["loops excluded (junction interval %.1f..%.1f C "
                          "wholly below TREG, package %.1f C); CV peak in "
                          "the VBATREG band; BATFET-off transition sustained "
                          "%.1f min into the present window, present current "
                          "at the floor" % (tj_lo, tj, v["package_C"],
                                             sustained)]


# ==========================================================================
# D-797 / Round-16 D797-09.  FIRST-ARTICLE VERDICT SEMANTICS.
#
# Fable R16-04: every FA step that replaces a DECLARED/DERIVED model input
# with a measurement must say what happens when the measurement is WORSE.
# The declared list below names every step in FIRST_FIVE_ASSEMBLY_PLAN §7d
# and what its OUTCOME clause must carry: `gate` = "PASS if ... otherwise
# RECORD + ESCALATE"; a non-empty re-run tuple = the checks that must be
# re-run on the measured value before acceptance; `record` = the step (or a
# named part of it) is RECORD ONLY.  A step row with no declaration, or a
# declaration with no row, is itself a failure -- a new step must declare
# its semantics before it can ship.
# ==========================================================================
FA_OUTCOME_SEMANTICS = {
    "Q11-TEMP-01": (("gate",), ("F5",)),
    "C-PWR-TRANSIENT-01": (("gate",), ("F6", "F11")),
    "C-THERM-01": (("gate", "record"), ("F6", "F12", "F14")),
    "C-BAT-GATE-01": (("gate",), ("F10", "F12", "F14")),
    "C-DISP-01": (("gate",), ("F6", "F12", "F14")),
    "C-SPK-01": (("gate",), ()),
    "C-ADH-01": (("gate",), ()),
    "C-ACC-01": (("gate",), ("F6", "F12")),
    "C-ACC-02": (("gate",), ("F6", "F12")),
    "C-FW-ABORT-01": (("gate",), ()),
    "C-WARM-IMAGE-01": (("gate",), ()),
    "C-BAT-PATH-01": (("gate",), ("F6", "F12", "F14")),
    "C-CHG-01": (("gate", "record"), ("F12", "F14")),
    "C-ACC-ILIM-01": (("gate",), ("F6", "F12")),
    "C-MCU-01": (("gate",), ("F6", "F12", "F14")),
    "C-PWR-CHARGE-01": (("gate", "record"), ("F12", "F14")),
    "C-RADIO-QUIESCE-01": (("gate",), ()),
    "C-PWR-CHARGE-02": (("gate", "record"), ("F12",)),
    "C-GAUGE-EPOCH-01": (("gate", "record"), ()),
    "C-NFC-QUIESCE-01": (("gate", "record"), ()),
    "C-NFC-TUNE-01": (("gate", "record"), ("F6",)),
    # D-800 (Round-19 full review): the IR pair's isolation, measured.
    "C-IR-01": (("gate",), ()),
}
FA_OUTCOME_MARKER = "OUTCOME:"

# D-798 / D798-06 (Astra R17-06).  RECORD ONLY IS PER OBSERVATION.
#
# D-797 checked that a step with a record-only part said "RECORD ONLY"
# somewhere in its OUTCOME, so "the no-discharge onset ... RECORD ONLY"
# passed even when that onset, measured LOWER than the published boundary,
# falsifies the envelope every charging claim is read from.  Each
# record-only OBSERVATION is now declared here with what would falsify a
# published assumption and the checks that must re-run; the plan carries
# each as its own numbered item `(rN)` inside the OUTCOME clause, and:
#   * a falsifying observation must name its trigger ("unless"), say
#     RECORD + ESCALATE and re-run every declared check before the affected
#     acceptance;
#   * a non-falsifying observation must say why it is not an assumption
#     ("no published assumption").
# (phrase, falsifies, re-runs); `falsifies` is None for a true record.
FA_RECORD_OBSERVATIONS = {
    "C-THERM-01": (
        ("charge record", "thermal", ("F12", "F14")),
        ("U11.2 narrow run", "thermal", ("F12", "F14")),
        ("diagnostic above the admissible domain", None, ())),
    "C-CHG-01": (
        ("adapter's own output", "source", ("F12", "F14")),
        ("outside-contract source", None, ())),
    "C-PWR-CHARGE-01": (
        ("SYS-collapse power", "collapse", ("F12", "F14")),
        ("no-discharge onset", "onset", ("F12", "F14")),
        ("throttling behaviour", "throttling", ("F12", "F14"))),
    "C-PWR-CHARGE-02": (
        ("40 °C run", None, ()),
        ("ACTIVE LIMITING interval", "loop", ("F12",)),
        ("internal-air record", "thermal", ("F12", "F14"))),
    "C-GAUGE-EPOCH-01": (
        ("register-cadence trace", "cadence", ("F12",)),),
    "C-NFC-QUIESCE-01": (
        ("measured latencies", "latency", ()),
        ("rails-off operator-test case", None, ())),
    "C-NFC-TUNE-01": (
        ("final tuning values", None, ()),
        ("ripple", "ripple", ("F6",))),
}
FA_RECORD_ITEM = re.compile(r"\(r(\d+)\)")


# ---- D-797 / Round-16 D797-07 + D797-06.  SYMMETRIC CLAIM FAMILIES. --
# Each is a set of CONCEPTS that must all appear in one scan unit, in ANY
# order, with none of its negations -- so "Acceptable charging source:
# any USB-C adapter", "Permitted: a sub-GHz transmission with an
# accessory rail live" and "| STAT1 LOW | safety timer expired |" are
# the same claims as their D-796 word-order forms.  The regex families
# above are retained beside them.
_SYM_I = re.I
_D797_SYMMETRIC_CLAIMS = (
    ("a generic charging-source rule instead of the named adapter",
     (re.compile(r"1\s*A or (?:better|more)|rated (?:at )?1\s*A\b|1\s*A "
                 r"USB (?:adapter|source|charger)|\bany (?:5 ?V )?(?:USB"
                 r"(?:-C)? )?(?:source|adapter|charger|supply|cable)\b|"
                 r"\bany USB(?:-C)? port\b|USB 2\.0 (?:computer |host )?"
                 r"port|computer (?:USB )?port|laptop (?:USB )?port|"
                 r"power bank|phone charger|generic (?:USB|Type-C|"
                 r"adapter|charger)", _SYM_I),
      re.compile(r"charg\w*|\bsource\b|adapter", _SYM_I)),
     re.compile(r"\bOUTSIDE\b|outside the contract|\bnot\b|cannot|"
                r"never|\bno\b|only the named|refus\w*|do not accept",
                _SYM_I)),
    ("a radio transmitting beside an accessory rail called admitted",
     (re.compile(r"\bradios?\b|transmit\w*|\bTX\b|sub-GHz|Wi-Fi|"
                 r"\bLoRa\b|\bBLE\b|CC1101|SX1262", _SYM_I),
      re.compile(r"accessory (?:rails?|power)|Community[- ]Port rails?|"
                 r"ACC_3V3|ACC_5V|both rails|\brails? (?:live|on)\b",
                 _SYM_I),
      re.compile(r"\b(?:permitted|allowed|admitted|admissible|supported|"
                 r"coexist\w*|may (?:run|be (?:on|enabled|live|used))|"
                 r"can (?:run|stay|be (?:on|enabled|live))|stays? "
                 r"(?:on|live|enabled)|remains? (?:on|live|enabled))\b",
                 _SYM_I)),
     re.compile(r"refus\w*|\bnot\b|never|cannot|\bno (?:accessory )?"
                r"rail|forbid\w*|block\w*|\bshed\b|sizing|diagnostic|"
                r"ABOVE the admissible", _SYM_I)),
    ("a universal no-discharge charge ceiling",
     (re.compile(r"(?:does|will|would) not discharge|no[- ](?:battery[- ])?"
                 r"discharge|never discharges|without discharging",
                 _SYM_I),
      re.compile(r"\d\.\d{1,3}\s*W\b")),
     re.compile(r"at (?:a |the |each |every )?(?:cell|\d\.\d{2,3}\s*V)|"
                r"VBAT|cell voltage|conditioned|envelope|table|\brows?\b|"
                r"full cell|per[- ]cell|by cell|\bnot (?:a |one )?"
                r"(?:scalar|universal)|RETIRED|retired|RECORD", _SYM_I)),
    ("a universal completion guarantee",
     (re.compile(r"complet(?:es|ed|ion)\b|terminat\w*|full[- ]charge|"
                 r"fully charged", _SYM_I),
      re.compile(r"charg\w*|\bcycle\b", _SYM_I),
      re.compile(r"\b(?:every|all|any|always|guarantee\w*)\b", _SYM_I),
      re.compile(r"\b(?:source|cable|adapter|class|timer|tMAXCHG|288|"
                 r"360)\b", _SYM_I)),
     re.compile(r"QUALIFICATION TARGET|qualification target|estimate|"
                r"\bnot\b|never|cannot|C-PWR-CHARGE-02|RECORD|\bif\b|"
                r"TIMER EXPIRY|fault|OUTSIDE", _SYM_I)),
    ("the 288 min qualification target called a datasheet guarantee",
     (re.compile(r"288\s*min|360\s*min|tMAXCHG", _SYM_I),
      re.compile(r"guarantee\w*|datasheet (?:limit|timeout|bound)",
                 _SYM_I)),
     re.compile(r"\bnot\b|TYP-only|\bTYP\b|qualification target|never|"
                r"\bno (?:MIN|MAX)", _SYM_I)),
    ("a supplement below the BUVLO trip",
     (re.compile(r"supplement\w*", _SYM_I),
      re.compile(r"2\.85\s*V|V?BUVLO|\bUVLO\b|lockout|under-?voltage "
                 r"lock", _SYM_I),
      re.compile(r"\b(?:below|under|beneath|at|less than|inside)\b",
                 _SYM_I)),
     re.compile(r"cannot|\bnot\b|never|\bno supplement|collaps\w*|"
                r"\bopen\b|uvlo_open|disconnect\w*|must be higher|"
                r"\babove\b|RETIRED|retired|nothing supplements",
                _SYM_I)),
    ("STAT1 alone read as charge completion",
     (re.compile(r"\bSTAT1\b"),
      # D-800: word-bounded -- "INDETERMINATE" is not "terminated".
      re.compile(r"\bcomplet\w*|\bterminat\w*|fully charged|full charge|"
                 r"charge done", _SYM_I)),
     re.compile(r"cannot|\bnot\b|ambiguous|STAT2|inference|infer\w*|"
                r"never|\balone\b|insufficient|fault|UNCLASSIFIED",
                _SYM_I)),
    # D-797 / D797-07: a charging figure called TREG-independent, in any
    # order and without the word "no-discharge" (value-first, Round-16).
    ("a charging power figure called independent of TREG",
     (re.compile(r"\d\.\d{2,3}\s*W\b|no[- ]discharge"),
      re.compile(r"independent of|regardless of|does not depend on|"
                 r"unaffected by|whatever the", _SYM_I),
      re.compile(r"\bTREG\b|thermal regulation", _SYM_I)),
     re.compile(r"\bnot independent|depends on|conditioned|\(T\)|RETIRED|"
                r"retired|HISTORICAL|superseded", _SYM_I)),
    # D-797 / D797-06: the two readings Round-16 found in C-PWR-CHARGE-02.
    ("a current taper near VBATREG read as termination",
     (re.compile(r"terminat\w*|charge[- ]complet\w*|fully charged|"
                 r"full charge|charging (?:is )?(?:done|complete)",
                 _SYM_I),
      re.compile(r"\bITERM\b|taper\w*|current (?:fall\w*|drop\w*|"
                 r"below|under)|below ~?\d+\s*mA|VBATREG|4\.20?\s*V",
                 _SYM_I)),
     re.compile(r"VINDPM|DPPM|TREG|thermal regulation|regulation loops?|"
                r"limiting loops?|ACTIVE LIMITING|insufficient|not "
                r"sufficient|cannot|\bnot\b|never|does not occur",
                _SYM_I)),
    # ---- D-798 / D798-07 (Fable R17-05, Q14): a mode the release REFUSES
    # while charging, called permitted / allowed / admitted while charging.
    ("a Wi-Fi/BLE mode called permitted while charging",
     (re.compile(r"Wi-?Fi|\bBLE\b|display_wifi", _SYM_I),
      re.compile(r"while charging|adapter attached|with the adapter|"
                 r"during (?:a |the )?charg\w*|on the charger|\bcharging\b",
                 _SYM_I),
      re.compile(r"\b(?:permitted|allowed|admitted|admissible|supported|"
                 r"may (?:run|transmit|be (?:used|entered|enabled|on))|"
                 r"can (?:run|transmit|be (?:used|entered|enabled|on)))\b",
                 _SYM_I)),
     re.compile(r"refus\w*|\bNOT\b|\bnot\b|never|cannot|may not|"
                r"forbid\w*|no Wi-Fi caller|OUTSIDE|disallow\w*|"
                r"blocked|HISTORICAL|superseded|RETIRED", _SYM_I)),
    ("audio with the 5 V rail or the declared pair called permitted while "
     "charging",
     (re.compile(r"(?<!\w)audio\b", _SYM_I),
      re.compile(r"ACC_5V|acc 5v|5 V (?:accessory )?rail|declared pair|"
                 r"both rails|\bpair\b", _SYM_I),
      re.compile(r"while charging|adapter attached|with the adapter|"
                 r"during (?:a |the )?charg\w*|on the charger", _SYM_I),
      re.compile(r"\b(?:permitted|allowed|admitted|admissible|supported|"
                 r"SUPERVISED|may (?:run|be (?:used|enabled|on))|"
                 r"can (?:run|be (?:used|enabled|on)))\b", _SYM_I)),
     re.compile(r"refus\w*|\bNOT\b|\bnot\b|never|cannot|may not|"
                r"forbid\w*|OUTSIDE|disallow\w*|HISTORICAL|superseded|"
                r"RETIRED", _SYM_I)),
    ("STAT1 LOW read as the safety timer",
     (re.compile(r"\bSTAT1\b\W+(?:\w+\W+){0,2}?LOW\b|\bSTAT1\b\W+"
                 r"(?:goes|going|went|is|reads?|pulled|driven)\W+low\b|"
                 r"\bLOW\b\W+(?:on|at)\W+STAT1\b"),
      re.compile(r"safety[- ]timer|\btimer\b|tMAXCHG", _SYM_I)),
     re.compile(r"\bshare[sd]?\b|\balone\b|other (?:charger )?faults?|"
                r"any of|VIN_OVP|TS HOT|TSHUT|BATOCP|ILIM/ISET|\bnot\b|"
                r"never|cannot|positively|UNCLASSIFIED|ESCALATE",
                _SYM_I)),
)


# ---- D-797 / D797-07.  ROLE-BOUND NUMERIC GROUPS, SYMMETRIC. ---------------
# A group is one VALUE shape and the ROLES that compete for it.  Each role
# carries what the model publishes for it -- a set, or a predicate
# `(token, unit) -> bool` -- and a role of None is neutral (a bench setpoint,
# a period, a trough) and absorbs a value without judging it.  A finding is
# reported under the ROLE's key, which is the family the injection controls
# require to catch it.  `neutral_unit` skips a whole unit (the release group
# does not judge a sentence that says "parent", "REJECTED" or "superseded").
_D797_CELL_CONDITION = re.compile(
    r"at (?:a |an |the |each |every )?(?:\d\.\d{2,3}\s*V|cell|full cell|"
    r"lowest cell|\w+ cell)|\bVBAT\b|cell[- ]voltage|cell[- ]conditioned|"
    r"per[- ]cell|by cell|\bILIM\w*\s*(?:×|x)\s*VBAT|envelope|table|"
    r"\brows?\b", re.I)


_D797_UNIVERSAL_QUANTIFIER = re.compile(
    r"\b(?:every|all|any)\s+(?:\w+\s+)?cells?\b|whole (?:cell |charging )?"
    r"(?:range|domain)|over the whole|\buniversal(?:ly)?\b|regardless of "
    r"(?:the )?cell|at any cell", re.I)


# D-800 / D800-KNOWN-08 (Opus R19-07).  The supervised rule's CONDITION is a
# finite normative family, not free English: a conditional, a subject that
# is the pack's voltage, a verb of state or reading, an optional comparator.
# D-799 knew only "is at least"; "the pack READS at least 3.90 V" escaped.
_D800_SUP_SUBJECT = (r"(?:the )?(?:pack|cell|battery|OCV_lb|V\(J4\)|VBAT|"
                     r"open-circuit (?:voltage|lower bound))(?:'s)?"
                     r"(?: (?:voltage|open-circuit voltage|OCV|terminal "
                     r"voltage))?")
_D800_SUP_VERB = (r"(?:is|reads|measures|sits|stays|remains|reaches|"
                  r"has (?:reached|risen to|been)|shows|registers|was)")
_D800_SUP_CMP = (r"(?:at or above|above|over|at least|no (?:less|lower) than|"
                 r"not (?:below|under|less than)|higher than|greater than|"
                 r">=|\u2265|>)?")
_D800_SUP_CONDITION = (r"(?:unless|only (?:if|while|when|once|after)|"
                       r"provided(?: that)?|as long as|so long as|"
                       r"if and only if)\s+" + _D800_SUP_SUBJECT + r"\s+"
                       + _D800_SUP_VERB + r"\s*" + _D800_SUP_CMP)
_D800_SUP_CHARGING = r"(?:charg\w*|adapter|\bUSB\b|\bVBUS\b)"


def _d797_bound_families(quiet, audio, retention, floors, gauge, junction,
                         current_release=None, supervised=None):
    """The symmetric role-bound groups.  `quiet`/`audio`/`retention`/`floors`
    are the gridded floor strings the firmware carries; `gauge` the gauge
    window strings; `junction` is `_d797_junction_safe_published(cc)`."""
    cur = _d797_release_number(current_release or CURRENT_RELEASE_ID)
    js_vals, js_univ = junction["values"], junction["universal"]

    js_min = junction.get("universal_min_W")

    def _js_ok(tok, unit):
        if tok not in js_vals:
            return False
        # D-797: "at every cell", "over the whole range" is a UNIVERSAL
        # claim, not a cell condition -- it must be the universal minimum.
        if _D797_UNIVERSAL_QUANTIFIER.search(unit):
            return bool(js_min is not None
                        and tok in ("%.3f" % js_min, "%.2f" % js_min))
        return bool(js_univ or _D797_CELL_CONDITION.search(unit))
    return (
        dict(key="d797_vcell_rows", kind="bound",
             what="the rail-edge rows and floors, bound in either order",
             value=re.compile(r"(?<![\d.])(\d\.\d{2})(?!\d)\s*V\b"),
             reach=90,
             roles=(("quiet_row", re.compile(r"\bquiet\b", re.I), set(quiet)),
                    ("audio_row", re.compile(r"(?<!\w)audio\b(?!_)", re.I),
                     set(audio)),
                    ("retention_floor", re.compile(r"\bretention\b", re.I),
                     set(retention)),
                    ("accessory_floor", re.compile(
                        r"(?:single|dual|first|second)[- ]rail|\benvelope\b|"
                        r"enable (?:a|the|one|both|either) (?:first |second |"
                        r"accessory )?rails?|kAccessory\w*FloorV", re.I),
                     set(floors)),
                    (None, re.compile(
                        r"charging[- ]safe(?: envelope)?|\bcells?\b|"
                        r"(?:admissible )?charging envelope|cell floors?|"
                        r"audio at the capped level|sub-GHz TX|"
                        r"reported (?:charging )?floor|mode[- ]entry|"
                        r"\bbench\b|≈|setpoint|BAT_RAW|cut-?off|VBATREG|"
                        r"BUVLO|\bUVLO\b|trough|\bpeak\b|\bVIN\b|VSYS|"
                        r"delivered|connector minimum|absolute max\w*|"
                        r"step (?:the )?supply|read with|approximately|"
                        r"-class\b|\bD-\d{3}'s\b", re.I), None))),
        dict(key="d797_gauge_window", kind="bound",
             what="the post-request gauge freshness window, either order",
             value=re.compile(r"(?<![\d.])(\d{3,4}(?:\.\d{1,2})?)\s*ms\b"),
             reach=80,
             roles=(("gauge_window", re.compile(
                        r"post[- ](?:request|load|edge)|fresh\w*|(?:gauge|"
                        r"admission|epoch)\s+(?:\w+\s+)?window|\bwindow\b|"
                        r"after (?:the |its |a |every |each |any )?(?:own )?"
                        r"(?:gauge |VCELL |admission |accessory )?request|"
                        r"gauge conversion", re.I), set(gauge)),
                    (None, re.compile(
                        r"revok\w*|revocation|liveness|\bperiods?\b|settle|"
                        r"\bramp\b|slices?|deadline|\bwithin\b|\bprime\b|"
                        r"latency|timeout|tREC|retry|hiccup|deglitch|probe|"
                        r"allowance|backlight|worst case|\bdelay\w*|\bshed\b|"
                        r"every \d+ ms|poll\w*|\bfor \*?\*?\d", re.I), None))),
        dict(key="d797_junction_safe", kind="bound",
             what="the charger junction-safe power: whatever the model "
                  "publishes as current, cell-conditioned once the model "
                  "is",
             value=re.compile(r"(?<![\d.])(\d\.\d{2,3})\s*W\b"),
             reach=70,
             roles=(("junction_safe", re.compile(r"junction[- ]safe", re.I),
                     _js_ok),
                    (None, re.compile(
                        r"no[- ]discharge|input[- ]carrying|supplement\w*|"
                        r"collaps\w*|completion|display_\w+|acc_\w+|"
                        r"\bstates?\b|\bsteps?\b|heaviest|0\.1 W|\bfrom\b",
                        re.I), None))),
        # D-798 / D798-07 (Fable R17-05, Q13): the supervised-charging
        # threshold is ONE generated figure; a second copy with another value
        # cannot sit beside it.
        dict(key="d798_supervised_threshold", kind="bound",
             what="the supervised-charging OCV threshold, either order",
             value=re.compile(r"(?<![\d.])(\d\.\d{2})(?!\d)\s*V\b"),
             reach=90,
             roles=(("supervised_threshold", re.compile(
                        r"OCV_lb|open-circuit lower bound|SUPERVISED "
                        r"CHARGING RULE|supervised[- ]charging (?:rule|"
                        r"threshold|restriction|condition)|\bSUPERVISED\b|"
                        # D-799 / D799-04C (Fable R18-03): the D-797 rule's
                        # own words, and close variants, are the same claim
                        r"(?:run|enable|use|power|operate|switch on|turn on)"
                        r" (?:an? |the |any )?accessory rails?[^.;|]{0,50}?"
                        r"adapter (?:is )?(?:attached|connected|plugged)|"
                        r"accessory rails?[^.;]{0,60}?adapter (?:is )?"
                        r"(?:attached|connected|plugged)|"
                        r"(?:unless|only (?:if|while|when)) the (?:pack|cell|"
                        r"battery)(?: voltage)? is (?:at or above|above|at "
                        r"least)|"
                        # D-800 / D800-KNOWN-08 (Opus R19-07): the SAME
                        # condition in its other finite written forms --
                        # "reads at least", "measures", "has reached", "no
                        # less than", "3.90 V or more" -- when the sentence
                        # is about charging or the adapter, on either side.
                        + _D800_SUP_CHARGING + r"[^.;|]{0,100}?"
                        + _D800_SUP_CONDITION + r"|"
                        + _D800_SUP_CONDITION + r"(?=\s*\**\s*\d\.\d{2}\s*V"
                        r"[^.;|]{0,100}?" + _D800_SUP_CHARGING + r")",
                        re.I), (set(supervised) if supervised else set())),
                    (None, re.compile(
                        r"reported|FIRMWARE FLOOR|firmware floor|VCELL|"
                        r"console|cell floor|charging[- ]safe|4\.2 V|"
                        r"mode[- ]entry|BAT_PROTECTED_P", re.I), None))),
        dict(key="d797_release_identity", kind="bound",
             what="the release a CURRENT heading, status or content commit "
                  "names as the review target",
             value=re.compile(r"\b(D-\d{3})\b"),
             reach=45,
             neutral_unit=re.compile(
                 r"\bparent\b|\bPARENT\b|REJECTED|rejected|supersed\w*|"
                 r"SUPERSED\w*|HISTORICAL|historical|\bprevious\b|\bprior\b|"
                 r"predecessor|RETIRED|retired"),
             roles=(("release_identity_current",
                     re.compile(r"[Rr]eview [Tt]arget|REVIEW TARGET|content "
                                r"commit|[Cc]urrent release|CURRENT RELEASE|"
                                r"this release|release candidate|STATUS|"
                                r"(?<=D-\d{3} )status\b|FROZEN IDENTITY"),
                     lambda tok, unit: (_d797_release_number(tok) or 0)
                     >= cur),)),
    )


def _d797_bound_scan(unit, fam):
    """[(role, token)] findings of one bound group over one unit."""
    if fam.get("neutral_unit") is not None and fam["neutral_unit"].search(unit):
        return []
    out = []
    for role, tok in _d797_bind(unit, [(k, rx) for k, rx, _ in fam["roles"]],
                                fam["value"], fam["reach"]):
        allowed = next(a for k, rx, a in fam["roles"] if k == role)
        if allowed is None:
            continue
        ok = allowed(tok, unit) if callable(allowed) else tok in allowed
        if not ok:
            out.append((role, tok))
    return out



def fa_step_rows(plan_text):
    """{step: row text} for every bold step row of the §7d table."""
    rows = {}
    for m in re.finditer(r"^\| \*\*`?((?:C-[A-Z0-9-]+|Q11-TEMP-01))`?\*\* \|(.*)$",
                         plan_text or "", re.M):
        rows[m.group(1)] = m.group(2)
    return rows


def fa_outcome_clause(row):
    """The OUTCOME clause of one step row: from the marker to the END OF
    ITS OWN CELL (an unescaped `|`), markup stripped."""
    i = row.index(FA_OUTCOME_MARKER)
    m = re.search(r"(?<!\\)\|", row[i:])
    cell = row[i:i + m.start()] if m else row[i:]
    return re.sub(r"[*`]", "", cell)


def judge_fa_outcomes(plan_text, semantics=None, obs_decl=None):
    """Problems with the first-article verdict semantics; [] is a pass."""
    sem = FA_OUTCOME_SEMANTICS if semantics is None else semantics
    rows = fa_step_rows(plan_text)
    problems = []
    for step in sorted(set(rows) - set(sem)):
        problems.append("%s has no declared outcome semantics" % step)
    for step, (kinds, reruns) in sorted(sem.items()):
        row = rows.get(step)
        if row is None:
            problems.append("%s is declared and has no step row" % step)
            continue
        if FA_OUTCOME_MARKER not in row:
            problems.append("%s states no %s clause" % (step, FA_OUTCOME_MARKER))
            continue
        # D-799 / D799-04A (Fable R18-02): the OUTCOME clause ends at its
        # own table cell.  D-798 read to the end of the ROW, so the last
        # (rN) item borrowed a required re-run token ("F12") from the
        # source / decision columns and an omission passed.
        oc = fa_outcome_clause(row)
        if "gate" in kinds:
            if "PASS if" not in oc:
                problems.append("%s: no 'PASS if' bound" % step)
            if "otherwise RECORD + ESCALATE" not in oc:
                problems.append("%s: a worse result is not 'RECORD + "
                                "ESCALATE'" % step)
        if "record" in kinds and "RECORD ONLY" not in oc:
            problems.append("%s: its record-only part does not say RECORD "
                            "ONLY" % step)
        # ---- D-798 / D798-06: per OBSERVATION, not per step ----------
        decl = (obs_decl if obs_decl is not None
                else FA_RECORD_OBSERVATIONS).get(step, ())
        if "record" in kinds and not decl:
            problems.append("%s has a record-only part and declares no "
                            "observation semantics" % step)
        if decl:
            marks = list(FA_RECORD_ITEM.finditer(oc))
            items = [oc[m.end():(marks[i + 1].start() if i + 1 < len(marks)
                                 else len(oc))]
                     for i, m in enumerate(marks)]
            for phrase, falsifies, obs_reruns in decl:
                hit = [it for it in items if phrase in it]
                if len(hit) != 1:
                    problems.append("%s: the observation %r is %s as its own "
                                    "(rN) item" % (step, phrase,
                                                   "missing" if not hit
                                                   else "not exactly once"))
                    continue
                it = hit[0]
                if "RECORD ONLY" not in it:
                    problems.append("%s: %r does not say RECORD ONLY"
                                    % (step, phrase))
                if falsifies is None:
                    if "no published assumption" not in it:
                        problems.append("%s: %r does not say why it is "
                                        "not a published assumption"
                                        % (step, phrase))
                    continue
                if "unless" not in it or "RECORD + ESCALATE" not in it:
                    problems.append("%s: %r can falsify a published "
                                    "assumption and is not RECORD + "
                                    "ESCALATE when it does"
                                    % (step, phrase))
                if obs_reruns:
                    if "re-run" not in it:
                        problems.append("%s: %r names no re-run"
                                        % (step, phrase))
                    else:
                        tail_o = it[it.index("re-run"):]
                        for f in obs_reruns:
                            if not re.search(r"\b%s\b" % re.escape(f),
                                             tail_o):
                                problems.append("%s: %r re-run omits %s"
                                                % (step, phrase, f))
        if reruns:
            if "re-run" not in oc:
                problems.append("%s replaces a model input and names no "
                                "re-run" % step)
            else:
                tail = oc[oc.index("re-run"):]
                for f in reruns:
                    if not re.search(r"\b%s\b" % re.escape(f), tail):
                        problems.append("%s: the re-run omits %s" % (step, f))
    return problems


def harness_current_text(env):
    """D-796 / D796-05: the harness record's operative currents, from F6.

    D-801 / Round-20 D801-04 (Astra R20-04).  D-796..D-800 printed "BOTH
    limiters in fault reach 3.8236 A, ABOVE the BQ25185 BATOCP maximum
    (3.6875 A), so the recoverable BATOCP hiccup interrupts it".  3.6875 A is
    the maximum of TI's STATED band (3.13 A typical, 18 % at ONE condition);
    this release itself rules the sustained envelope on a DECLARED 25 % band
    whose maximum is 3.9063 A, and a unit whose threshold sits at 3.85 A --
    inside that band -- does not trip at 3.8236 A.  The interruption was never
    guaranteed.  The text now separates the production-admitted loads, the
    sizing coincidence the image refuses, the real fault case, what BATOCP is
    (typical / stated accuracy / declared sensitivity) and what the LTC4368 and
    F1 guarantee, and it claims no interruption it cannot prove.
    """
    m = env["modes_I_bat_A"]
    sets = env["conforming_and_overcurrent_sets"]
    rated = 2.6
    ref = 2.9
    wc = max(sets["conforming"], key=lambda k: m[k])
    sf = max(("acc3v3_alone_at_its_limiter", "acc5v_alone_at_its_limiter"),
             key=lambda k: m[k])
    df_ = "both_limiters_in_fault"
    dfa = "both_limiters_in_fault_at_the_admitted_internal_load"
    ocp_lo, ocp_typ, ocp_max = env["ibat_ocp_A"]
    ocp_decl_lo = IBAT_OCP_TYP_A * (1.0 - IBAT_OCP_ASSUMED_ACCURACY)
    ocp_decl_hi = IBAT_OCP_TYP_A * (1.0 + IBAT_OCP_ASSUMED_ACCURACY)
    brk = env["breaker"]["trip_min_A"]
    fuse = env["fuse_A"]
    rating = (
        "D-801 / Round-20 D801-04.  GENERATED FROM demo_feature_contract F6 "
        "-- do not hand-edit.  PRODUCTION-ADMITTED LOAD: the worst CONFORMING "
        "battery current (%s, with the internal +3V3 peak envelope) is %.4f "
        "A, INSIDE the %.1f A rated current by %.1f %%.  SINGLE FAULT: one "
        "accessory limiter in fault (%s) reaches %.4f A, %.1f %% ABOVE the "
        "rated current and %.1f %% %s the section 4.3 two-circuit reference "
        "derating value of %.1f A; it is a NAMED BOUNDED EXCEPTION -- a "
        "fault, not an operating state.  DOUBLE FAULT: both limiters in "
        "fault reach %.4f A with the internal +3V3 PEAK envelope, which is a "
        "SIZING COINCIDENCE the production image refuses (no accessory rail "
        "is live while the Wi-Fi/BLE or a sub-GHz radio transmits), and %.4f "
        "A at the internal load the production image ADMITS beside a live "
        "rail, which is the real double-fault case.  BATOCP: the BQ25185 "
        "threshold is %.4f A TYPICAL; TI's stated accuracy (18 %% at one "
        "condition, VBAT = 4 V, TJ = 27 C) gives %.4f..%.4f A and this "
        "release's DECLARED sensitivity (25 %%) gives %.4f..%.4f A.  Every "
        "fault current above lies inside the declared band, so BATOCP MAY "
        "OR MAY NOT trip on a given unit -- for example, a threshold of "
        "3.85 A lies inside the declared band and above %.4f A -- and NO "
        "BATOCP INTERRUPTION IS CLAIMED for any fault case.  What IS "
        "guaranteed from board values is that every fault current above is "
        "below the latching LTC4368 breaker minimum (%.4f A) and the F1 "
        "one-shot fuse (%.0f A), so neither latches nor opens; a hard short "
        "is bounded by each TPS22950's own current limit, thermal shutdown "
        "and auto-retry.  The BQ25185 SYS absolute maximum is a survival "
        "rating and is never an acceptance target.  MEASURED at "
        "C-BAT-PATH-01 and C-THERM-01." % (
            wc, m[wc], rated, 100.0 * (rated - m[wc]) / rated, sf, m[sf],
            100.0 * (m[sf] - rated) / rated,
            100.0 * abs(ref - m[sf]) / ref,
            "BELOW" if m[sf] < ref else "ABOVE", ref, m[df_], m[dfa],
            ocp_typ, ocp_lo, ocp_max, ocp_decl_lo, ocp_decl_hi, m[df_],
            brk, fuse))
    acceptance = (
        "first article: with an accessory drawing the %s limiter's maximum, "
        "record the connector and lead temperature rise at the %.4f A "
        "single-limiter fault excursion as well as at the %.4f A worst "
        "conforming load; the rated-current exception above is accepted only "
        "if the measured rise stays inside the 30 C figure" % (
            "ACC_5V" if sf.startswith("acc5v") else "ACC_3V3", m[sf], m[wc]))
    return dict(rating=rating, acceptance=acceptance,
                worst_conforming=dict(state=wc, battery_A=m[wc]),
                single_limiter_fault=dict(state=sf, battery_A=m[sf]),
                both_limiters_in_fault_A=m[df_],
                both_limiters_in_fault_admitted_A=m[dfa],
                ibat_ocp_declared_band_A=[round(ocp_decl_lo, 5),
                                          round(ocp_decl_hi, 5)])


def judge_cell_to_load(paths_ohm, v_3v3_V, v_acc5v_V, ron_a3_ohm, ron_a5_ohm,
                       budget=None, ambient_C=None, pass_pair=None,
                       ocp_min_A=None, margin=None, board_forward=None,
                       burst_delta_A=None):
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
    # D-793 / R12-01: the four J4 -> R75 board-copper segments and the ground
    # return are IN the fixed series path now.  `board_forward` is the live
    # measured set; None falls back to the module's last-measured defaults so
    # this function stays pure for its own mutation controls.
    up_fixed = apm.upstream_fixed_ohm("max", board_forward)
    # D-793 / R12-08: the INSTANTANEOUS electrical delta a bursty consumer can
    # add at the moment a permission transition is evaluated.  The sustained
    # states below carry the duty-AVERAGED allowance, which is the right model
    # for heat and the wrong one for a permission edge.
    burst_delta_A = (apm.burst_transition_delta_A() if burst_delta_A is None
                     else burst_delta_A)
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
            tj_pp = (air_next + spec["land_above_internal_air_K"]
                     + spec["theta_jl_max_C_per_W"] * (
                         2 * nxt * nxt * r_ch))
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
        tj_pp = (air + spec["land_above_internal_air_K"]
                 + spec["theta_jl_max_C_per_W"] * (2 * amps * amps * r_ch))
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
        tj_pp = (q["internal_air_C"] + spec["land_above_internal_air_K"]
                 + spec["theta_jl_max_C_per_W"] * (2 * amps * amps * r_ch))
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

    # D-793 / R12-08.  THE FOUR LIMITS THAT ACT IN MICROSECONDS AND THE TWO
    # THAT ACT IN MINUTES.  `ELECTRICAL_LIMITS` are checked on the
    # INSTANTANEOUS state -- the one with the worst coincident burst present.
    # The junction and the internal air are thermal integrals of a minute-
    # scale time constant and are checked on the SUSTAINED, duty-averaged
    # state; charging them for a 200 ms burst would be arithmetic, not physics.
    ELECTRICAL_LIMITS = ("node_above_buvlo", "vsys_above_u12_floor",
                         "inside_the_ocp_margin",
                         "pass_pair_meets_its_conduction_row")
    THERMAL_LIMITS = ("junction_inside_the_operating_maximum",
                      "air_inside_the_pouch_window")

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

    def electrically_supported(s):
        """The instantaneous subset only -- R12-08."""
        v = limits(s)
        if not v.get("has_an_operating_point"):
            return False
        return all(v[k] for k in ELECTRICAL_LIMITS)

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
        """The firmware's own retention rule plus every hardware limit, on
        BOTH timescales -- D-793 / R12-08.

        The SUSTAINED state (bursty lines at their duty average) has to clear
        all seven limits, which is what the thermal ones can be asked about.
        The INSTANTANEOUS state -- the same state with the worst coincident
        microSD + NFC + IR burst present -- has to clear the four ELECTRICAL
        limits AND the firmware's own retention read, because the post-enable
        recheck can land inside a burst and that is Astra's reproduced
        quiet-pre-read -> enable + burst -> post-read-below-retention case.
        """
        s = solve(cell, i3, i5, i_int, amb)
        if s is None or not supported(s):
            return False, s
        if s["node_V"] - gauge < retention_grid - 1e-12:
            return False, s
        if burst_delta_A <= 0.0:
            return True, s
        b = solve(cell, i3, i5, i_int + burst_delta_A, amb)
        if b is None or not electrically_supported(b):
            return False, s
        s["instantaneous_with_worst_burst"] = b
        return bool(b["node_V"] - gauge >= retention_grid - 1e-12), s


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
                # D-796 / R15-02: the physical load set travels with every
                # network row, so the oracle can bind a key to its content.
                acc_3v3_A=round(i3, 6), acc_5v_A=round(i5, 6),
                demand_W=round(((i_int + i3) * v_3v3_V + i3 * i3 * r_a3)
                               / ETA_U12 + ((i5 * v_acc5v_V + i5 * i5 * r_a5)
                                            / ETA_U21 if i5 else 0.0), 9),
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
                # ==========================================================
                # D-794 / R13-04 + ROUND-13 FABLE DELTA.  THE ROW CARRIES ITS
                # SETTLED POST-LOAD STATE, SO SOMETHING OTHER THAN THIS
                # FUNCTION CAN CHECK THE RETENTION.
                #
                # ROUND-13, IN ITS OWN WORDS: "Every permitted table row must
                # independently prove settled post-load retention, not
                # attainability only."  Fable found the same gap from the
                # other side: "table rows only independently checked for
                # attainability".
                #
                # BOTH ARE RIGHT ABOUT WHAT WAS PUBLISHED.  `permission_floor`
                # does apply the full retention rule -- `post_is_acceptable`
                # is what `critical_cell` bisects on -- but the ROW it emits
                # kept only the floor, the critical cell and the pre-state
                # ceiling.  So the independent oracle, handed that row, could
                # only re-check that the floor was REACHABLE.  Whether the
                # state the floor authorises actually holds the node above
                # retention AFTER the load arrives was a claim the canonical
                # model made about itself.
                #
                # The settled node is therefore emitted -- sustained, and with
                # the worst coincident burst -- at the row's own critical
                # cell, in the row's own ruling accessory configuration.  The
                # oracle re-checks `node - gauge >= retention` on both, from
                # the row, with no access to this function.
                # ==========================================================
                post_sustained = post_burst = None
                if worst["cfg"] is not None and worst["c"] is not None:
                    _post = dict(RAIL_CONFIGS[rails])[worst["cfg"]]
                    _s = solve(worst["c"], _post[0], _post[1], i_int)
                    if _s is not None:
                        post_sustained = round(_s["node_V"], 6)
                    if burst_delta_A > 0.0:
                        _b = solve(worst["c"], _post[0], _post[1],
                                   i_int + burst_delta_A)
                        if _b is not None:
                            post_burst = round(_b["node_V"], 6)
                rows.append(dict(
                    edge=edge, mode_bits=bits, modes=list(modes), rails=rails,
                    internal_3v3_A=round(i_int, 6),
                    pre_state_internal_3v3_A=round(i_pre, 6),
                    settled_post_node_V=post_sustained,
                    settled_post_node_with_worst_burst_V=post_burst,
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
    # D-795 / R14-03 + R14-04.  THE CHARGE REGIME IS TWO CLAIMS, AND ONLY ONE
    # OF THEM IS A SCALAR.
    #
    # ROUND-14: "3.600 W is NOT a universal no-battery-discharge ceiling. ...
    # Re-derive any published no-discharge/regime ceiling over the full
    # domain.  If no useful universal scalar exists, publish a VBAT/source-
    # conditioned envelope instead of inventing one.  C-PWR-CHARGE-01 must
    # name VBAT/source/ambient conditions."
    #
    # D-794 derived ONE ceiling at ONE mid-charge cell (3.2 V), from a solver
    # that held SYS at its 4.41 V regulation point while an input loop was
    # binding.  Both are corrected in `aqroot_power_model.charger_state`; the
    # domain is now every cell from 2.85 V to 4.221 V, every source class,
    # both ILIM corners, five points of the threshold sweep, both supplement
    # histories and three ambients -- `ara.charge_regime_envelope`.  What it
    # gives:
    #
    #   JUNCTION-SAFE SYSTEM POWER -- a genuine universal scalar, because TREG
    #   folds the charge and only the zero-charge state can exceed 125 C.
    #
    #   NO-DISCHARGE ENVELOPE -- a TABLE by VBAT and source class.  Battery-
    #   tracking VINDPM squeezes the input as the cell fills, so the boundary
    #   falls steeply near 4.2 V; it is published per row and its universal
    #   minimum is reported as what it is.
    # ======================================================================
    regime = ara.charge_regime_envelope(
        delivered_out_W=0.0, keep_evidence=True)
    junction_safe_W = regime["junction_safe_published_W"]
    nd_universal_W = regime["universal_no_discharge_published_W"]
    _q_env = [e for e in regime["envelope"] if e["qualified"]]

    def _no_discharge_up_to_vbat(system_W):
        """The highest grid cell at which EVERY qualified class still carries
        `system_W` without supplement, on the published (guard-banded)
        envelope.  None if even the lowest cell does not."""
        ok_v = None
        for v in ara.REGIME_VBAT_GRID_V:
            rows_v = [e for e in _q_env if e["vbat_V"] == v]
            if all(e["no_discharge_published_W"] >= system_W - 1e-12
                   for e in rows_v):
                ok_v = v
            else:
                break
        return ok_v

    # A dense scan BELOW the junction-safe figure over the whole domain grid,
    # at the top of the ambient envelope -- the published number is never
    # rounded up across anything.
    _scan = [i * junction_safe_W / 40.0 for i in range(1, 41)]
    _scan_bad = []
    # D-796 / R15-01 + D796-08: every thermally-closed state the release
    # solves anywhere -- the dense scan and the completion domain -- must be
    # labelled by a loop that holds it, and nothing supplements under the
    # trip.
    _thermal_label_bad, _uvlo_supplement_bad = [], []
    for w in _scan:
        jr = ara.charge_regime_junction(w, ambient_C=ara.AMBIENT_DESIGN_MAX_C)
        if not jr["the_unregulated_half_is_inside_the_operating_maximum"]:
            _scan_bad.append(round(w, 6))
        for _k, _c in jr["corners"].items():
            if _c.get("no_operating_point"):
                continue
            _tp = _c["invariants"].get("thermal_problems") or []
            if _tp or not _c["invariants"]["ok"]:
                _thermal_label_bad.append("%.4f W %s: %s" % (
                    w, _k, (_tp or _c["invariants"].get(
                        "branch_problems") or ["invariants"])[:1]))
            if _c.get("batfet") == "uvlo_open" and (
                    _c["mode"] in apm.SUPPLEMENTING_MODES or _c["supplement_A"] > 0):
                _uvlo_supplement_bad.append("%.4f W %s" % (w, _k))
    _tj_max = ara.PACKAGE_JUNCTION["tj_operating_max_C"]
    _at_js = ara.charge_regime_junction(junction_safe_W,
                                        ambient_C=ara.AMBIENT_DESIGN_MAX_C)
    # ======================================================================
    # D-797 / D797-01 + D797-02.  THE CHARGING-SAFE POWER IS CELL-CONDITIONED.
    #
    # ROUND-16 (Astra R16-01, Fable R16-01): D-796's universal 3.900 W was
    # bounded on the ZERO-CHARGE state.  A part that is SUPPLEMENTING carries
    # no charge for TREG to fold and cannot lift its own SYS back to the exit
    # threshold while the load at SYS = VBAT exceeds what the input carries,
    # so the supplement is ABSORBING -- and at the high source corner its
    # static junction is 150-250 C: the device's TSHUT "stops charging and
    # shuts down VSYS", powers up again at 135 C, and cycles.  Reached from a
    # cold start at the full program above ILIM_min x (VBAT + VDPPM), or
    # retained from any supplement history above ILIM_min x VBAT.  So the
    # figure that is actually safe is about ILIM_min x VBAT: a TABLE by cell
    # (`charging_safe_by_cell`, published and guard-banded), with a universal
    # minimum at the lowest cell the BATFET can be connected at.
    # ======================================================================
    _by_cell = regime["charging_safe_by_cell"]
    charging_safe_universal_W = regime["charging_safe_universal_published_W"]

    def charging_cell_floor_V(system_W):
        """The lowest grid cell (BAT_PROTECTED_P) at and above which every
        qualified corner, history and ambient keeps `system_W` inside the
        published charging-safe envelope.  None: no cell does."""
        for b in _by_cell:
            if b["charging_safe_at_or_above_published_W"] is not None and \
                    b["charging_safe_at_or_above_published_W"] \
                    >= system_W - 1e-12:
                return b["vbat_V"]
        return None

    # THE FIRMWARE HALF (D797-02): a reported-cell MODE-ENTRY floor for every
    # optional-mode set that needs one with no accessory rail live (with a
    # rail live the D-792 mode-edge table already refuses every entry).  The
    # firmware cannot see the adapter (no VBUS-present signal, D-776), so the
    # floor is judged on a pre-read that may have been taken WHILE CHARGING,
    # when BAT_PROTECTED_P sits above the cell by the charge current times
    # the cell-to-node path; entering the mode folds that charge, and the
    # node falls by up to the same amount.  So the reported floor is
    #   the charging-safe cell floor
    # + the largest charge current the PRE-state can be carrying
    #   (min(ICHG_max, ILIM_max - P_pre / (VBAT_max + VDPPM_max)))
    #   times the itemised cell-to-node resistance, pass pair at 150 C
    # + the MAX17048 error and one LSB,
    # rounded UP onto the 50 mV floor grid.  A floor above the highest value
    # the gauge can report in the pre-state is NOT PERMITTED -- the D790-A03
    # rule: a floor nobody can reach is a refusal and must say so.
    _r_node_max = (pack_dc + up_fixed + spec["channels_in_series"]
                   * apm.channel_ohm(150.0, hot_ratio, spec))
    _vsys_pre_max = (apm.BAT_RAW_MAX_V + apm.BQ25185["vdppm_V"]
                     * (1.0 + apm.CHARGER_BRANCH_THRESHOLD_SWEEP))

    def _mode_system_W(modes):
        return i_int_of(modes) * v_3v3_V / ETA_U12

    charging_floor_rows = []
    for _bits in range(1 << len(MODE_NAMES)):
        _modes = tuple(MODE_NAMES[i] for i in range(len(MODE_NAMES))
                       if _bits & (1 << i))
        _p = _mode_system_W(_modes)
        _p_pre = (_mode_system_W(()) if not _modes else
                  min(_mode_system_W(tuple(m for m in _modes if m != d))
                      for d in _modes))
        _i_pre = max(0.0, min(apm.BQ25185["ichg_max_A"],
                              apm.BQ25185["ilim_max_A"]
                              - _p_pre / _vsys_pre_max))
        _cell = charging_cell_floor_V(_p)
        _pre_ceiling = node(CELL_MAX_OCV_V, 0.0, 0.0,
                            i_int_of(()) if not _modes else min(
                                i_int_of(tuple(m for m in _modes if m != d))
                                for d in _modes))
        _pre_ceiling_V = (None if _pre_ceiling is None
                          else _pre_ceiling["node_V"] + gauge)
        if _p <= charging_safe_universal_W + 1e-12:
            _floor, _permitted, _why = 0.0, True, "charging-safe at every cell"
        elif _cell is None:
            _floor, _permitted, _why = None, False, (
                "no cell keeps %.4f W inside the charging-safe envelope"
                % _p)
        else:
            _raw = _cell + _i_pre * _r_node_max + gauge
            _floor = round(math.ceil(_raw / FLOOR_GRID_V - 1e-9)
                           * FLOOR_GRID_V, 4)
            _permitted = bool(_pre_ceiling_V is not None
                              and _floor <= _pre_ceiling_V + 1e-12)
            _why = ("cell floor %.3f V + pre-state charge %.4f A x %.4f ohm "
                    "+ gauge %.6f V = %.4f V -> %.2f V"
                    % (_cell, _i_pre, _r_node_max, gauge, _raw, _floor))
            if not _permitted:
                _why += (" -- above the %.4f V the gauge can report in the "
                         "pre-state: NOT PERMITTED" % (_pre_ceiling_V or 0.0))
                _floor = None
        charging_floor_rows.append(dict(
            mode_bits=_bits, modes=list(_modes), rails=0,
            system_W=round(_p, 6), pre_state_system_W=round(_p_pre, 6),
            pre_state_charge_bound_A=round(_i_pre, 6),
            cell_to_node_max_ohm=round(_r_node_max, 6),
            charging_cell_floor_V=_cell,
            pre_state_reported_ceiling_V=(None if _pre_ceiling_V is None
                                          else round(_pre_ceiling_V, 6)),
            reported_floor_V=_floor, permitted=_permitted, why=_why))

    # Which (state, accessory configuration) pairs are junction-safe while
    # charging, and up to which cell voltage the named adapter carries them
    # without the battery supplementing.
    charge_permitted, charge_refused = [], []
    for _st in states:
        for _name in PUBLISHED_LOADS:
            _i3, _i5 = next((a_, b_) for n, a_, b_ in LOADS if n == _name)
            _sys_W = ((_st["internal_3v3_A"] + _i3) * v_3v3_V / ETA_U12
                      + (_i5 * v_acc5v_V / ETA_U21 if _i5 else 0.0))
            # D-797: judged over the cells at and above the state's own
            # charging floor -- below it the state is NOT permitted while
            # charging, and its reachable supplement there is a TSHUT cycle,
            # not an operating point to print.
            _cf = charging_cell_floor_V(_sys_W)
            _jr = ara.charge_regime_junction(
                _sys_W, ambient_C=ambient_C,
                delivered_out_W=_i3 * v_3v3_V + _i5 * v_acc5v_V,
                vbat_grid=(None if _cf is None else
                           [v_ for v_ in ara.REGIME_VBAT_GRID_V
                            if v_ >= _cf - 1e-12]))
            # D-795: only a combination the PRODUCTION permission table admits
            # may be published as a state the product can be in while
            # charging.  A radio transmitting beside a live rail is refused
            # by the rail edge, so it is REPORTED here and never "permitted".
            _bits_ = sum(1 << list(MODE_NAMES).index(m_)
                         for m_ in _st.get("modes", []))
            _rails_ = (0 if _name == "no_accessory" else
                       2 if _name.startswith("both") else 1)
            _adm_ = (_rails_ == 0 or any(
                r_["permitted"] for r_ in rail_rows
                if r_["mode_bits"] == _bits_ and r_["rails"] == _rails_))
            _row = dict(
                admissible_in_production=bool(_adm_),
                state=_st["key"], load=_name, system_W=round(_sys_W, 6),
                junction_with_charge_folded_back_C=_jr[
                    "junction_with_charge_folded_back_C"],
                hottest_operating_junction_C=_jr[
                    "hottest_operating_junction_C"],
                internal_air_C=_jr["internal_air_C"],
                charge_ambient_ceiling_C=_jr["charge_ambient_ceiling_C"],
                inside_the_junction_safe_power=bool(
                    _sys_W <= charging_safe_universal_W + 1e-12),
                # D-797: the cell at and above which this state is inside the
                # charging-safe envelope.  Below it the state can reach an
                # absorbing supplement (TSHUT cycling at the high source) or,
                # under the trip, a SYS collapse.
                charging_cell_floor_V=_cf,
                no_discharge_up_to_vbat_V=_no_discharge_up_to_vbat(_sys_W))
            (charge_permitted if (_row["charging_cell_floor_V"] is not None
                                  and _jr["junction_with_charge_folded_back_C"]
                                  <= _tj_max
                                  and _row["admissible_in_production"])
             else charge_refused).append(_row)

    # ---- D-797 / D797-02.  WHICH CHARGING STATES DOES THE FIRMWARE HOLD? --
    # A state the production image admits and whose power is above the
    # universal charging-safe figure is inside the envelope only at or above
    # its cell floor.  The firmware can hold it there only if the REPORTED
    # floor on the edge that admits it is at least the cell floor plus the
    # pre-state charge offset plus the gauge error -- the same arithmetic as
    # the charging mode-entry table.  With no rail live that table IS the
    # governing floor.  With a rail live the governing floor is the D-792
    # rail-edge entry, which was derived for the DISCHARGE question and
    # carries no charge offset.  Every state where the governing floor is
    # short is listed, with both numbers: this board has no VBUS-present
    # signal (D-776) and STAT2 is unrouted (owner decision), so no reported
    # floor can separate "charging at a low cell" from "discharging at a high
    # one", and a state listed here is a product decision, not a constant.
    _rail_floor = {(r_["mode_bits"], r_["rails"]): (
        r_["floor_gridded_V"] if r_["permitted"] else None)
        for r_ in rail_rows}
    _cm_by_bits = {r_["mode_bits"]: r_ for r_ in charging_floor_rows}
    charging_unenforced = []
    for _row in charge_permitted:
        if _row["system_W"] <= charging_safe_universal_W + 1e-12:
            continue
        _st = next(s_ for s_ in states if s_["key"] == _row["state"])
        _bits_ = sum(1 << list(MODE_NAMES).index(m_)
                     for m_ in _st.get("modes", []))
        _rails_ = (0 if _row["load"] == "no_accessory" else
                   2 if _row["load"].startswith("both") else 1)
        if _rails_ == 0:
            # The charging mode-entry table IS this edge's floor, derived with
            # the charge offset; a refused row holds the state by refusal.
            continue
        if _rail_floor.get((_bits_, _rails_)) is None:
            continue    # the rail edge refuses it: held by refusal
        else:
            _gov = _rail_floor.get((_bits_, _rails_))
            _p_pre = _st["internal_3v3_A"] * v_3v3_V / ETA_U12
            _i_pre = max(0.0, min(apm.BQ25185["ichg_max_A"],
                                  apm.BQ25185["ilim_max_A"]
                                  - _p_pre / _vsys_pre_max))
            _need = round(math.ceil((_row["charging_cell_floor_V"]
                                     + _i_pre * _r_node_max + gauge)
                                    / FLOOR_GRID_V - 1e-9) * FLOOR_GRID_V, 4)
            _edge = "D-792 rail-edge table"
        _pre = node(CELL_MAX_OCV_V, 0.0, 0.0, _st["internal_3v3_A"])
        _pre_n = None if _pre is None else _pre["node_V"] + gauge
        if _gov is None or _need is None or _gov + 1e-9 < _need:
            charging_unenforced.append(dict(
                state=_row["state"], load=_row["load"],
                system_W=_row["system_W"],
                charging_cell_floor_V=_row["charging_cell_floor_V"],
                governing_edge=_edge, firmware_floor_V=_gov,
                reported_floor_needed_while_charging_V=_need,
                # the highest the gauge can report in the pre-state on a FULL
                # cell with no adapter: a needed floor above it would refuse
                # the state on battery too (D790-A03).
                pre_state_reported_ceiling_on_battery_V=(
                    None if _pre_n is None else round(_pre_n, 6)),
                enforceable_without_refusing_it_on_battery=bool(
                    _need is not None and _pre_n is not None
                    and _need <= _pre_n + 1e-12)))

    # ---- D-798 / D798-02.  THE SUPERVISED-CHARGING MATRIX, FROM EVERY
    # COMBINATION THE PRODUCTION IMAGE ADMITS.
    #
    # Round-17 (Astra R17-02, Fable R17-01): D-797 listed only the states in
    # `charge_permitted` that the firmware could not hold, so an admitted
    # combination with NO charging cell floor (display_audio + ACC_5V,
    # display_audio + the declared pair) sat in `charge_refused` and no
    # document told the supervisor it could not run while charging.  The
    # matrix is now every (optional-mode set x published accessory load)
    # pair -- all 8 mode sets, not only the sustained states -- each with ONE
    # disposition:
    #   REFUSED_BY_FIRMWARE     the production image refuses it on EVERY
    #                           source (battery included): the D-792 rail
    #                           edge, or the charging mode-entry table
    #   ANY_CELL                inside the universal charging-safe power
    #   FIRMWARE_FLOOR          held by a reported floor the image enforces
    #   SUPERVISED              inside the envelope at or above its cell
    #                           floor, which no reported floor can hold
    #   REFUSED_WHILE_CHARGING  admitted on battery, above the charging-safe
    #                           envelope at every cell (or over the junction
    #                           limit): the adapter may not be attached
    _unheld_keys = {(x["state"], x["load"]) for x in charging_unenforced}
    _rows_by_key = {(r_["state"], r_["load"]): r_
                    for r_ in charge_permitted + charge_refused}
    _state_by_bits = {}
    for _st in states:
        _state_by_bits.setdefault(sum(
            1 << list(MODE_NAMES).index(m_) for m_ in _st.get("modes", [])),
            _st)
    _load_of = {n: (a_, b_) for n, a_, b_ in LOADS}
    supervised_matrix = []
    for _bits in range(1 << len(MODE_NAMES)):
        _modes = tuple(MODE_NAMES[i] for i in range(len(MODE_NAMES))
                       if _bits & (1 << i))
        _st = _state_by_bits.get(_bits)
        for _name in PUBLISHED_LOADS:
            _i3, _i5 = _load_of[_name]
            _rails_ = (0 if _name == "no_accessory" else
                       2 if _name.startswith("both") else 1)
            _sys_W = ((i_int_of(_modes) + _i3) * v_3v3_V / ETA_U12
                      + (_i5 * v_acc5v_V / ETA_U21 if _i5 else 0.0))
            if _rails_ == 0:
                _admit = bool(_cm_by_bits[_bits]["permitted"])
                _edge = "charging mode-entry table (no rail live)"
            else:
                _admit = any(r_["permitted"] for r_ in rail_rows
                             if r_["mode_bits"] == _bits
                             and r_["rails"] == _rails_)
                _edge = "D-792 rail-edge table"
            _key = (_st["key"] if _st is not None else None, _name)
            _cr = _rows_by_key.get(_key)
            _cf = charging_cell_floor_V(_sys_W)
            if _cr is not None:
                _tj_ok = bool(_cr["junction_with_charge_folded_back_C"]
                              <= _tj_max)
            else:
                _tj_ok = None
            if not _admit:
                _disp = "REFUSED_BY_FIRMWARE"
            elif _sys_W <= charging_safe_universal_W + 1e-12:
                _disp = "ANY_CELL"
            elif _cf is None or _cr is None or not _tj_ok:
                _disp = "REFUSED_WHILE_CHARGING"
            elif _rails_ == 0:
                _disp = "FIRMWARE_FLOOR"
            elif _key in _unheld_keys:
                _disp = "SUPERVISED"
            else:
                _disp = "FIRMWARE_FLOOR"
            supervised_matrix.append(dict(
                mode_bits=_bits, modes=list(_modes),
                state=(_st["key"] if _st is not None else None),
                load=_name, rails=_rails_, system_W=round(_sys_W, 6),
                admitted_by_the_image=_admit, admitting_edge=_edge,
                charging_cell_floor_V=_cf,
                junction_inside_the_limit=_tj_ok,
                firmware_reported_floor_V=(
                    _cm_by_bits[_bits]["reported_floor_V"]
                    if _rails_ == 0 else _rail_floor.get((_bits, _rails_))),
                disposition=_disp))
    _sup_rows = [r_ for r_ in supervised_matrix
                 if r_["disposition"] == "SUPERVISED"]
    supervised_threshold_V = (max(r_["charging_cell_floor_V"]
                                  for r_ in _sup_rows) if _sup_rows else None)
    # D-799 / D799-01: the method is a PROVED lower bound (see
    # `supervised_ocv_lower_bound`); every published figure is rounded
    # OUTWARD and the proof below runs on the same dict.
    _ichg_hist = apm.BQ25185["ichg_max_A"]
    supervised_method = dict(
        quantity="the pack's OPEN-CIRCUIT voltage lower bound OCV_lb -- the "
                 "cell axis the charging-safe envelope is solved on (the "
                 "supplement onset is a zero-charge state, where the BAT pin "
                 "is the cell)",
        where="J4.1 (BAT_CONNECTOR_P, red) to J4.2 (GND, black) on the "
              "board, with a DMM",
        dmm_uncertainty_V=SUPERVISED_DMM_UNCERTAINTY_V,
        settle=dict(hold_s=SUPERVISED_DMM_SETTLE[0],
                    within_V=SUPERVISED_DMM_SETTLE[1]),
        current_uncertainty=dict(offset_A=SUPERVISED_CURRENT_UNCERTAINTY[0],
                                 gain=SUPERVISED_CURRENT_UNCERTAINTY[1],
                                 status="DECLARED instrument requirement"),
        current_sign="the MAGNITUDE of the reading is used: the sign "
                     "convention is not trusted, and a discharge treated as "
                     "a charge only lowers the bound",
        insertion_ohm_max=SUPERVISED_INSERTION_OHM_MAX,
        insertion_basis="a shunt or ammeter in the pack lead sits BETWEEN "
                        "J4 and the pack, so its burden plus its added "
                        "leads is inside the V(J4) reading; recorded per "
                        "measurement (0 for a clamp meter), admitted up to "
                        "the declared cap",
        meter_topologies=list(SUPERVISED_METER_TOPOLOGIES),
        insertion_methods=list(SUPERVISED_INSERTION_METHODS),
        # published figures ARE the computed ones, rounded OUTWARD
        harness_max_ohm=math.ceil(round(apm.harness_ohm("max") * 1e4, 6))
        / 1e4,
        pack_dc_ohm=apm.PACK_DC_OHM,
        pack_ac_ohm=apm.PACK_AC_IMPEDANCE_MAX_OHM,
        history_current_max_A=math.ceil(round(_ichg_hist * 1e3, 6)) / 1e3,
        history_basis="the pack's stored polarization is bounded by its "
                      "polarization resistance x the largest CHARGE current "
                      "in its history, whatever its time constant; the "
                      "declared domain charges the pack only through this "
                      "board's BQ25185, whose highest programmed current is "
                      "ICHG_max (KISET MAX over R37 at -1 %)",
        residual_and_pack_V=_ceil_mV(
            math.ceil(round(_ichg_hist * 1e3, 6)) / 1e3 * apm.PACK_DC_OHM),
        residual_basis="max(I_up, ICHG_max) x the declared pack DC "
                       "resistance (ohmic plus every polarization branch): "
                       "the worst split of the pack's resistance between "
                       "its ohmic and polarization parts; %.4f A x %.4f ohm "
                       "= %.5f V, rounded UP" % (
                           _ichg_hist, apm.PACK_DC_OHM,
                           _ichg_hist * apm.PACK_DC_OHM),
        discharge_current_max_A=IBAT_OCP_TYP_A * (
            1.0 + IBAT_OCP_STATED_ACCURACY),
        rounding="every subtractive allowance rounded UP to the millivolt, "
                 "OCV_lb rounded DOWN to the millivolt",
        no_relaxation_wait_is_assumed=True,
        console_vcell_offset_while_charging_max_V=round(
            apm.BQ25185["ichg_max_A"] * _r_node_max, 3),
        when="immediately before the change it admits: enabling a rail with "
             "the adapter attached, or attaching the adapter with a rail "
             "live; V(J4) and I_BAT at the same instant",
        measurement_of_record="C-PWR-CHARGE-01 step 7 and C-THERM-01 "
                              "(RECORD + ESCALATE if the measured pack DC "
                              "resistance, or the relaxation of V(J4) after "
                              "the charge current is interrupted, exceeds "
                              "the declared figure)")
    _ocv_viol = supervised_ocv_bound_proof(supervised_method)
    _ocv_d798 = supervised_ocv_bound_proof(supervised_method,
                                           formula=_d798_ocv_formula)
    _ocv_d798_classes = sorted({v_["attack"] for v_ in _ocv_d798
                                if v_["attack"].startswith("witness")})

    def _ocv_mut(rec_fn=None, **over):
        def f_(rec, m_):
            mm = dict(m_, **over)
            return supervised_ocv_lower_bound(rec_fn(rec) if rec_fn else rec,
                                              mm)
        return bool(supervised_ocv_bound_proof(supervised_method, formula=f_))

    def _ocv_round_down(rec, m_):
        lb, bad, t_ = supervised_ocv_lower_bound(rec, m_)
        if lb is None:
            return lb, bad, t_
        exact = max(t_["i_up_A"], m_["history_current_max_A"]) * m_[
            "pack_dc_ohm"]
        return (lb + t_["residual_and_pack_V"]
                - math.floor(exact * 1000.0) / 1000.0), [], t_
    supervised_ocv_proof = dict(
        violations=_ocv_viol[:10], violation_count=len(_ocv_viol),
        d798_formula_violations=len(_ocv_d798),
        d798_formula_witness_classes=_ocv_d798_classes,
        mutation_controls_refused=dict(
            no_current_uncertainty=_ocv_mut(current_uncertainty=dict(
                offset_A=0.0, gain=0.0)),
            no_insertion_term=_ocv_mut(
                rec_fn=lambda r_: dict(r_, insertion_ohm=0.0,
                                       current_meter="clamp")
                if r_.get("adapter") == "attached" else r_),
            pack_at_the_present_current_only=_ocv_mut(
                history_current_max_A=0.0),
            residual_rounded_down=bool(supervised_ocv_bound_proof(
                supervised_method, formula=_ocv_round_down)),
            sign_trusted=_ocv_mut(
                rec_fn=lambda r_: dict(r_, i_bat_A=max(r_["i_bat_A"], 0.0))
                if r_.get("adapter") == "attached" else r_)),
        ok=None)
    # D-800 / D800-KNOWN-07 (Opus R19-05): how R_ins is ESTABLISHED.  The
    # Round-19 witness -- an 80 mOhm series path recorded as 0 at 0.8 A,
    # which D-799 accepted at 45 mV above the true OCV -- is refused before
    # any bound is computed; a clamp at 0 and a measured series path are
    # admitted; an unmeasured, a zero, an over-cap or an unnamed topology is
    # refused.
    _o, _rdc, _rh = 4.050, supervised_method["pack_dc_ohm"], \
        supervised_method["harness_max_ohm"]

    def _ins_rec(i_, path_, **f_):
        return dict(dict(adapter="attached", v_j4_V=_o + i_ * (_rdc + _rh
                                                              + path_),
                         i_bat_A=i_), **f_)

    def _refused(rec_):
        return supervised_ocv_lower_bound(rec_, supervised_method)[0] is None
    _ins_ctrl = dict(
        r19_05_series_path_entered_as_zero_is_refused=_refused(_ins_rec(
            0.8, 0.080, current_meter="series", insertion_ohm=0.0,
            insertion_method="four_wire_measured")),
        series_path_without_a_measurement_method_is_refused=_refused(
            _ins_rec(0.4, 0.050, current_meter="series",
                     insertion_ohm=0.050)),
        series_path_by_an_unnamed_method_is_refused=_refused(_ins_rec(
            0.4, 0.050, current_meter="series", insertion_ohm=0.050,
            insertion_method="assumed")),
        no_topology_is_refused=_refused(_ins_rec(0.4, 0.0,
                                                 insertion_ohm=0.0)),
        over_the_cap_is_refused=_refused(_ins_rec(
            0.4, 0.150, current_meter="series", insertion_ohm=0.150,
            insertion_method="four_wire_measured")),
        a_clamp_at_zero_is_admitted=not _refused(_ins_rec(
            0.4, 0.0, current_meter="clamp", insertion_ohm=0.0)),
        a_measured_series_path_is_admitted_and_bounded=bool(
            not _refused(_ins_rec(0.8, 0.080, current_meter="series",
                                  insertion_ohm=0.080,
                                  insertion_method="four_wire_measured"))
            and supervised_ocv_lower_bound(_ins_rec(
                0.8, 0.080, current_meter="series", insertion_ohm=0.080,
                insertion_method="four_wire_measured"),
                supervised_method)[0] <= _o),
        the_d799_record_shape_would_have_exceeded_the_true_ocv=bool(
            supervised_ocv_lower_bound(_ins_rec(
                0.8, 0.080, current_meter="clamp", insertion_ohm=0.0),
                supervised_method)[0] > _o))
    supervised_ocv_proof["insertion_establishment_controls"] = _ins_ctrl
    supervised_ocv_proof["ok"] = bool(
        all(_ins_ctrl.values()) and
        not _ocv_viol
        and set(_ocv_d798_classes) == {
            "witness_a_current_error", "witness_b_current_fall",
            "witness_c_shunt_path", "witness_d_rounding",
            "witness_e_sign_convention"}
        and all(supervised_ocv_proof["mutation_controls_refused"].values()))
    supervised_method["proof"] = supervised_ocv_proof
    supervised_rule_text = (None if supervised_threshold_V is None else
                            SUPERVISED_CHARGING_RULE % supervised_threshold_V)

    # ---- D-795 / R14-04.  COMPLETION IS A QUALIFICATION TARGET. ----------
    completion = ara.charge_completion_estimate(keep_states=True)
    # The mutation controls R14-04 requires: each ablated domain must be
    # REFUSED as not the full one, so no future edit can shrink the domain
    # and quietly make a universal completion claim look supportable.
    _req = ara.completion_required_domain()
    _ablations = dict(
        remove_treg=dict(_req, treg_C=1000.0),
        remove_ambient=dict(_req, ambients_C=[25.0]),
        alter_the_timer=dict(_req, timer_min=apm.TMAXCHG_MIN * 2.0),
        alter_the_cv_tail=dict(_req, cv_tail_min=0.0),
        omit_a_source_class=dict(_req, source_classes=_req[
            "source_classes"][:1]),
    )
    _ablation_refused = {}
    for _k, _dom in _ablations.items():
        _e = ara.charge_completion_estimate(domain=_dom)
        _ablation_refused[_k] = bool(not _e["the_domain_is_the_full_required_one"])
    charge_completion = dict(
        estimate_rows=completion["rows"],
        domain=completion["domain"],
        required_domain=completion["required_domain"],
        the_domain_is_the_full_required_one=completion[
            "the_domain_is_the_full_required_one"],
        every_row_completes_on_the_estimate=completion[
            "every_row_completes_on_the_estimate"],
        rows_that_do_not_complete=completion["rows_that_do_not_complete"],
        universal_completion_claim_is_supportable=completion[
            "universal_completion_claim_is_supportable"],
        why_never_universal=completion["why_never_universal"],
        qualification_target=completion["qualification_target"],
        ablation_controls_refused=_ablation_refused,
        every_ablation_is_refused=bool(all(_ablation_refused.values())),
        d794_published_completion_W=1.150,
        d794_completion_ceiling_is_retired=True,
        measurement_of_record="C-PWR-CHARGE-02")

    for _st in completion["_states"]:
        _tp = _st["invariants"].get("thermal_problems") or []
        if _tp:
            _thermal_label_bad.append("%s: %s" % (_st["domain_key"], _tp[:1]))
    for _r in regime["rows"]:
        for _lab, _st in (_r.get("_evidence") or {}).items():
            if isinstance(_st, dict) and _st.get("mode") in apm.SUPPLEMENTING_MODES \
                    and _r["batfet"] == "uvlo_open":
                _uvlo_supplement_bad.append("%s %s" % (_r["key"], _lab))
    charge_ceiling = dict(
        no_cold_treg_state_anywhere=not _thermal_label_bad,
        thermal_label_problems=_thermal_label_bad[:20],
        no_supplement_at_or_under_vbuvlo=not _uvlo_supplement_bad,
        supplement_under_the_trip=_uvlo_supplement_bad[:20],
        model_assumptions=apm.CHARGER_MODEL_ASSUMPTIONS,
        model_assumptions_are_published=bool(
            apm.CHARGER_MODEL_ASSUMPTIONS.get("treg_zero_charge_sys_source",
                                              {}).get("status")
            == "AMBIGUOUS_IN_THE_PRIMARY_SOURCE_NOT_RELIED_ON"),
        buvlo_band_V=dict(zip(("falling_trip_low", "falling_trip_high",
                               "rising_reconnect_high"), apm.buvlo_band_V())),
        input_carrying_below_vbuvlo_published_W=regime[
            "input_carrying_below_vbuvlo_published_W"],
        input_carrying_below_vbuvlo_raw_W=regime[
            "input_carrying_below_vbuvlo_raw_W"],
        completion=charge_completion,
        domain=regime["domain"],
        regime_rows=len(regime["rows"]),
        junction_safe_system_W=junction_safe_W,
        junction_safe_raw_W=regime["junction_safe_raw_W"],
        junction_safe_ruling_row=regime["junction_safe_ruling_row"],
        # ---- D-797 / D797-01 + D797-02 -----------------------------------
        charging_safe_by_cell=_by_cell,
        charging_safe_universal_published_W=charging_safe_universal_W,
        junction_safe_is_cell_conditioned=True,
        charging_mode_entry_floor_rows=charging_floor_rows,
        charging_mode_entry_floor_table={
            r["mode_bits"]: r["reported_floor_V"]
            for r in charging_floor_rows},
        cell_to_node_max_ohm=round(_r_node_max, 6),
        supplement_is_absorbing=True,
        d796_universal_junction_safe_W_retired=3.900,
        reachable_tshut_protection_cycle_above_the_envelope=bool(any(
            r.get("junction_above_regime") == "TSHUT_PROTECTION_CYCLE"
            for r in regime["rows"] if r["qualified"])),
        # D-797 / D797-02: the admissible charging states no reported floor
        # on this revision can hold inside the envelope.  Each is held by the
        # SUPERVISED-CHARGING operating restriction (battery_pack_contract
        # B8), whose cell is the highest of their cell floors and which the
        # documents must print in the generated words below.
        charging_states_the_firmware_cannot_hold=charging_unenforced,
        # ---- D-798 / D798-02: ONE supervised-charging authority ---------
        supervised_charging_matrix=supervised_matrix,
        supervised_charging_threshold_V=supervised_threshold_V,
        supervised_charging_rule_text=supervised_rule_text,
        supervised_charging_method=supervised_method,
        the_matrix_covers_every_admitted_combination=bool(
            len(supervised_matrix) == (1 << len(MODE_NAMES))
            * len(PUBLISHED_LOADS)),
        the_supervised_rows_are_exactly_the_unheld_states=bool(
            {(r_["state"], r_["load"]) for r_ in supervised_matrix
             if r_["disposition"] == "SUPERVISED"} == _unheld_keys),
        supervised_refused_while_charging=[
            dict(state=r_["state"], load=r_["load"],
                 system_W=r_["system_W"]) for r_ in supervised_matrix
            if r_["disposition"] == "REFUSED_WHILE_CHARGING"],
        supervised_charging_restriction_cell_V=(
            max(x["charging_cell_floor_V"] for x in charging_unenforced)
            if charging_unenforced else None),
        supervised_charging_restriction_text=(
            SUPERVISED_RAIL_RESTRICTION % max(
                x["charging_cell_floor_V"] for x in charging_unenforced)
            if charging_unenforced else None),
        every_unheld_charging_state_is_an_accessory_rail_state=bool(all(
            x["load"] != "no_accessory" for x in charging_unenforced)),
        every_permitted_row_names_its_cell_floor=bool(all(
            r["charging_cell_floor_V"] is not None
            for r in charge_permitted)),
        the_envelope_is_non_decreasing_at_or_above=bool(all(
            (a["charging_safe_at_or_above_published_W"] or 0.0)
            <= (b["charging_safe_at_or_above_published_W"] or 0.0) + 1e-12
            for a, b in zip(_by_cell, _by_cell[1:]))),
        no_discharge_envelope=regime["envelope"],
        universal_no_discharge_published_W=nd_universal_W,
        universal_no_discharge_raw_W=regime["universal_no_discharge_raw_W"],
        universal_no_discharge_ruling_row=regime[
            "universal_no_discharge_ruling_row"],
        a_useful_universal_no_discharge_scalar_exists=bool(
            nd_universal_W >= max((r["system_W"] for r in charge_permitted
                                   if r["state"] == "display_only"
                                   and r["load"] == "no_accessory"),
                                  default=float("inf"))),
        guardband=regime["guardband"], grid_W=regime["grid_W"],
        tj_operating_max_C=_tj_max,
        ambient_C=ambient_C,
        dense_scan_points=len(_scan),
        dense_scan_violations=_scan_bad,
        the_whole_range_below_the_junction_safe_power_is_clean=bool(
            not _scan_bad),
        junction_at_the_junction_safe_power_C=_at_js[
            "junction_with_charge_folded_back_C"],
        hottest_operating_junction_at_the_junction_safe_power_C=_at_js[
            "hottest_operating_junction_C"],
        source_contract=apm.usb_source_contract(),
        reference_state_system_W=round(charge_system_W, 6),
        reference_state_is_junction_safe=bool(
            charge_system_W <= junction_safe_W + 1e-9),
        permitted_while_charging=charge_permitted,
        refused_while_charging=charge_refused,
        the_quiet_state_with_no_accessory_is_junction_safe=bool(any(
            r["state"] == "display_only" and r["load"] == "no_accessory"
            for r in charge_permitted)),
        there_is_no_vbus_present_signal=True,
        d794_published_regime_W=3.600,
        d794_regime_ceiling_is_retired_as_a_no_discharge_claim=True,
        _regime=regime, _completion=completion,
        why="TREG folds the CHARGE, and a smaller charge takes the input "
            "off its limit so SYS returns to regulation; what TREG cannot "
            "reduce is the zero-charge state, and THAT is what the junction-"
            "safe power bounds, over the whole domain.  Whether the battery "
            "discharges is a different question with a VBAT-dependent answer, "
            "because battery-tracking VINDPM squeezes the input as the cell "
            "fills; it is a table, never a scalar.",
        measurement_of_record="C-THERM-01, C-PWR-CHARGE-01 and "
                              "C-PWR-CHARGE-02")
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
        # D-796 / R15-02: the terms the oracle needs to re-derive each row's
        # demand from its LOAD SET, so a key cannot carry another load's
        # physics.
        network_power_terms=dict(
            v_3v3_V=v_3v3_V, v_acc5v_V=v_acc5v_V, r_a3_ohm=r_a3,
            r_a5_ohm=r_a5, r_trunk_ohm=r_trunk, r_bat_ohm=r_bat,
            eta_u12=ETA_U12, eta_u21=ETA_U21,
            full_cell_V=CELL_MAX_OCV_V,
            always_on_A=sum(ara.SUSTAINED_ALWAYS_ON.values()),
            bursty_time_averaged_A=ara.BURSTY_TIME_AVERAGED_A,
            optional_A=dict(ara.SUSTAINED_OPTIONAL),
            published_budget_A=dict(budget),
            declared_pair_A=dict(acc_3v3_A=round(dual_i3, 6),
                                 acc_5v_A=round(dual_i5, 6))),
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
    # ---- D-793 / Fable R12.  THE CONSTANT AND THE DERIVATION, COMPARED.
    #
    # D-792 wrote, beside `DECLARED_DUAL_RAIL_BUDGET_A`, that F12 "REFUSES if
    # this constant differs from what it derived".  No code did that: the
    # constant was hand-typed outside the canonical model and nothing joined
    # the two.  A stated rule that never runs is a defect this programme has
    # hit before, and Fable named this instance of it.  The values live in
    # `aqroot_power_model` now, tagged POLICY_BUDGET, and this is the clause.
    out["the_declared_pair_constant_equals_the_derivation"] = dict(
        published=dict(apm.DECLARED_DUAL_RAIL_BUDGET_A),
        derived=dict(ACC_3V3=round(dual_i3, 6), ACC_5V=round(dual_i5, 6)),
        enforcement=apm.DECLARED_PAIR_ENFORCEMENT,
        ok=bool(abs(apm.DECLARED_DUAL_RAIL_BUDGET_A["ACC_3V3"] - dual_i3)
                < 1e-9
                and abs(apm.DECLARED_DUAL_RAIL_BUDGET_A["ACC_5V"] - dual_i5)
                < 1e-9),
        why="the canonical model PUBLISHES the pair and F12 DERIVES it; a "
            "release in which the two differ is a release whose product-"
            "facing contract is not the one the physics supports.")
    out["the_declared_pair_constant_equals_the_derivation_ok"] = bool(
        out["the_declared_pair_constant_equals_the_derivation"]["ok"])
    # ---- D-794 / R13-04: ONE OBJECT, NOT TWO EQUAL ONES ------------------
    #
    # The clause above compares the canonical VALUE with the derived physics.
    # Astra walked straight past it by editing the copy F6 reads, which the
    # clause never looks at.  So the binding is checked as an IDENTITY: the
    # name every F6 call site resolves must BE the canonical object, not a
    # dict that currently happens to hold the same two numbers.
    _pair_consumers = {
        "demo_feature_contract.DECLARED_DUAL_RAIL_BUDGET_A":
            DECLARED_DUAL_RAIL_BUDGET_A,
        "audit_rail_ampacity.DECLARED_DUAL_RAIL_BUDGET_A":
            getattr(ara, "DECLARED_DUAL_RAIL_BUDGET_A", None),
    }
    _pair_divergent = sorted(
        name for name, obj in _pair_consumers.items()
        if obj is not None and obj is not apm.DECLARED_DUAL_RAIL_BUDGET_A)
    out["the_declared_pair_consumers_share_one_object"] = dict(
        authority="aqroot_power_model.DECLARED_DUAL_RAIL_BUDGET_A",
        consumers=sorted(k for k, v in _pair_consumers.items()
                         if v is not None),
        diverged=_pair_divergent,
        values={k: (None if v is None else dict(v))
                for k, v in _pair_consumers.items()},
        ok=not _pair_divergent,
        why="R13-04.  D-793 bound the pair by VALUE and Astra edited the "
            "consumer, not the authority: F12's equality clause compared the "
            "authority with the physics -- both correct, both agreeing -- "
            "while every F6 answer was computed at the altered figure.  A "
            "value check cannot see that.  An identity check can.")
    out["the_declared_pair_consumers_share_one_object_ok"] = bool(
        not _pair_divergent)
    # ---- D-794 / R13-04: THE F6/F12 PAIR-DIVERGENCE CONTROL --------------
    #
    # "Add full-suite destructive controls for ... F6/F12 pair divergence".
    # The identity rule above is stated; this is the clause that shows it
    # FIRES.  Three consumers are offered in turn: an equal-valued copy (the
    # exact `dict(...)` D-793 shipped, which is how Astra's edit survived),
    # an altered copy, and the authority itself.
    def _identity_rule(obj):
        return obj is apm.DECLARED_DUAL_RAIL_BUDGET_A
    _pair_controls = dict(
        an_equal_valued_copy_is_refused=not _identity_rule(
            dict(apm.DECLARED_DUAL_RAIL_BUDGET_A)),
        an_altered_copy_is_refused=not _identity_rule(
            dict(apm.DECLARED_DUAL_RAIL_BUDGET_A, ACC_3V3=0.400)),
        the_authority_itself_is_accepted=_identity_rule(
            apm.DECLARED_DUAL_RAIL_BUDGET_A),
        # ...and the VALUE clause must still refuse a pair that no longer
        # matches the physics, which is the half that was already working.
        a_pair_that_contradicts_the_derivation_is_refused=bool(
            abs((dual_i3 + 0.05) - dual_i3) >= 1e-9))
    out["the_declared_pair_divergence_controls"] = dict(
        _pair_controls,
        why="Astra altered the F6-side pair and the release stayed green.  "
            "An equal-valued copy is the exact object that let that happen, "
            "so the control that matters is the one that refuses it.")
    out["every_declared_pair_divergence_control_behaves"] = bool(
        all(_pair_controls.values()))
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
        # D-795 / R14-03 + R14-04.  What must hold: a junction-safe power
        # EXISTS and is clean below; the quiet state is under it; the
        # no-discharge envelope is published per row over the full domain;
        # completion is NOT claimed universally, and every ablation of its
        # domain is refused.
        ok=bool(charge_ceiling["junction_safe_system_W"] > 0.0
                and charge_ceiling[
                    "the_whole_range_below_the_junction_safe_power_is_clean"]
                and charge_ceiling[
                    "junction_at_the_junction_safe_power_C"] <= _tj_max
                and charge_ceiling[
                    "the_quiet_state_with_no_accessory_is_junction_safe"]
                and charge_ceiling["permitted_while_charging"]
                and all(r["charge_ambient_ceiling_C"] > 0.0
                        for r in charge_ceiling["permitted_while_charging"])
                and len(charge_ceiling["no_discharge_envelope"])
                == len(apm.USB_SOURCE_CLASSES) * len(ara.REGIME_VBAT_GRID_V)
                # D-796: the BATFET axis and the history restriction under
                # the trip make the domain the ORACLE's exact key set.
                and charge_ceiling["regime_rows"] == len(
                    apo.expected_regime_keys())
                and charge_ceiling["no_cold_treg_state_anywhere"]
                and charge_ceiling["no_supplement_at_or_under_vbuvlo"]
                # D-797: the charging-safe figure is the cell-conditioned
                # table, its universal minimum is the published junction-safe
                # figure, every permitted state names its cell floor, and the
                # mode-entry floor table covers all eight mode sets.
                and abs(charge_ceiling["charging_safe_universal_published_W"]
                        - min(charge_ceiling["junction_safe_system_W"],
                              charge_ceiling[
                                  "input_carrying_below_vbuvlo_published_W"]
                              or float("inf"))) < 1e-9
                and charge_ceiling["every_permitted_row_names_its_cell_floor"]
                and charge_ceiling[
                    "every_unheld_charging_state_is_an_accessory_rail_state"]
                and charge_ceiling["the_envelope_is_non_decreasing_at_or_above"]
                and len(charge_ceiling["charging_mode_entry_floor_rows"]) == 8
                and charge_ceiling["model_assumptions_are_published"]
                and not charge_ceiling["completion"][
                    "universal_completion_claim_is_supportable"]
                and charge_ceiling["completion"][
                    "the_domain_is_the_full_required_one"]
                and charge_ceiling["completion"]["every_ablation_is_refused"]
                and not charge_ceiling["source_contract"][
                    "a_usb2_host_port_satisfies_the_contract"]))
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
        and out["the_d790_declared_state_is_refused_ok"]
        and out["the_declared_pair_constant_equals_the_derivation_ok"]
        and out["the_declared_pair_consumers_share_one_object_ok"]
        and out["every_declared_pair_divergence_control_behaves"])
    return out["ok"], out


# ==========================================================================
# F14 -- THE INDEPENDENT ORACLE (D-793 / R12-04).
#
# ROUND-12, AS A RELEASE BLOCKER: "Astra halved canonical charger package heat
# and all F1-F13 still passed.  Astra removed the 5V-first transition;
# completeness Boolean became false but final verdict remained PASS.  This is
# a release blocker: the canonical model cannot be its own oracle."
#
# `aqroot_power_oracle` is the second implementation.  It imports nothing from
# `aqroot_power_model`, `audit_rail_ampacity` or this file; everything it
# needs arrives as DATA.  This clause assembles that data, runs the audit, and
# then runs the SIX MUTATIONS R12-04 names -- each of which must fail, for the
# reason it is named for.
# ==========================================================================
ORACLE_REQUIRED_MUTATIONS = (
    "halve_the_charger_package_heat",
    "delete_the_energy_oracle",
    "remove_the_5v_first_transition",
    "discard_the_failed_post_states",
    "reverse_the_gauge_error_direction",
    "omit_the_return_path",
    # ---- D-794 / R13-04 + the Round-13 Fable delta ----------------------
    # Round-13 names these six by name: "Add full-suite destructive controls
    # for empty F14 rows, empty F14 network states, duplicate key, F6/F12
    # pair divergence, missing permitted-row retention check, and stale
    # consumer value", and "Add mutations that alter summary only and raw
    # only; both must fail".  Every one of them passed the whole D-793 suite.
    "delete_every_permission_table_row",
    "delete_every_network_state",
    # ---- D-795 / R14-05 + Fable R14-13/R14-15 ---------------------------
    # "Partial-domain collapses (one row per mode, delete SUPPLEMENT history,
    # delete selected network rows) must fail ... Raw-only or summary-only
    # corruption [of the heat fields] must fail."
    "collapse_the_charger_domain_to_one_row_per_mode",
    "delete_the_supplement_history",
    "delete_selected_network_rows",
    "drop_the_charger_refusals",
    "delete_the_full_cell_regime_rows",
    "inflate_the_published_no_discharge_figure",
    "inflate_the_published_junction_safe_figure",
    "corrupt_the_heat_summary_only",
    "corrupt_the_heat_raw_only",
    "restore_d794_sys_reg_under_an_input_loop",
    "drop_the_thermally_closed_states",
    "duplicate_a_named_transition_key",
    "drop_the_permitted_row_retention_proof",
    "corrupt_the_public_summary_only",
    "corrupt_the_raw_block_only",
    # ---- D-796 / Round-15 R15-01/R15-02 + Fable R15-06/R15-11 ------------
    # "Add destructive controls O01/O04/PM2-class and thermal-domain-collapse
    # cases as permanent release regressions" and "independent negative
    # controls for: cold TREG, supplement below UVLO, NO_CHARGE above DPPM
    # with active CC program, charge folding above DPPM without TREG, and
    # threshold/history inconsistencies."  Each must fail FOR ITS REASON.
    "o01_a_vbat4221_key_carrying_a_4200_solve",
    "o04_a_lowest_cell_row_carrying_a_full_cell_solve",
    "pm2_the_canary_carrying_another_refused_states_physics",
    "collapse_the_thermal_population_to_one_treg_state",
    "a_regime_row_carrying_another_ambients_evidence",
    "restore_a_cold_treg_state",
    "restore_supplement_below_vbuvlo",
    "restore_no_charge_above_dppm_with_the_cc_loop_active",
    "fold_the_charge_above_dppm_without_treg",
    "a_latched_supplement_with_no_history",
    "a_supplement_history_under_the_trip",
    # ---- D-797 / Round-16 Astra R16-01/R16-02 + Fable R16-01 -------------
    # "Permanent regressions: Astra retained-supplement equilibrium class;
    # Fable low-cell absorbing SUPPLEMENT class; cold-start reachability;
    # actual SYS vs hypothetical off-state exit" -- "coordinated +0.5 W
    # boundary/publication inflation that previously accepted a 4.400 W
    # claim" -- "same-object in-place mutation after a PASS must be
    # revalidated and fail".
    "d797_exit_judged_on_the_hypothetical_batfet_off_node",
    "d797_an_absorbing_supplement_labelled_a_treg_limit_cycle",
    "d797_inflate_every_junction_boundary_and_its_publication_by_half_a_watt",
    "d797_mutate_the_passed_regime_in_place",
    # ---- D-798 / Round-17 Astra R17-01 + Fable R17-02 ---------------------
    # "Permanent controls must catch both errors: (a) hypothetical BATFET-off
    # exit too early, and (b) zero-shortfall retention too late."
    "d798_a_static_supplement_retained_above_the_vbsup2_exit",
    "d798_a_comparator_cycle_exited_to_the_hypothetical_node",
    # ---- D-798 / Round-17 Astra R17-05 -----------------------------------
    # "Reject duplicate keys, extra keys, missing keys, incompatible
    # duplicates and non-finite publication values.  Test bad-first/
    # good-last and good-first/bad-last orderings."
    "d798_publication_duplicate_key_bad_first_good_last",
    "d798_publication_duplicate_key_good_first_bad_last",
    "d798_publication_duplicate_key_identical_copy",
    "d798_publication_extra_key",
    "d798_publication_missing_key",
    "d798_publication_non_finite_value",
)


def _oracle_scalars(ambient_C=None):
    return dict(
        cu_tc_per_K=CU_TC_PER_K, cu_hot_rise_K=CU_HOT_RISE_K,
        rho_cu_ohm_m=apo.PRIMITIVES and 1.72e-8,
        eta_u12=ETA_U12, eta_u21=ETA_U21,
        gauge_verr_V=GAUGE_VERR_V, gauge_lsb_V=GAUGE_LSB_V,
        buvlo_bound_V=BUVLO_BOUND_V, u12_vin_floor_V=U12_VIN_FLOOR,
        theta_ja_C_per_W=ara.PACKAGE_JUNCTION["theta_ja_C_per_W"],
        tj_operating_max_C=ara.PACKAGE_JUNCTION["tj_operating_max_C"],
        r_sys_K_per_W=ara.system_thermal_resistance_K_per_W(),
        ambient_C=(ara.AMBIENT_DESIGN_MAX_C if ambient_C is None
                   else ambient_C))


# D-794 / R13-02 + R13-04.  THE DOMAIN THE ORACLE IS HANDED IS CONSTRUCTED
# INDEPENDENTLY, NOT COLLECTED FROM WHATEVER THE MODEL HAPPENED TO SOLVE.
#
# ROUND-13: "F14 must independently construct the EXPECTED physical/state
# domain instead of accepting whatever collections the canonical model
# supplies.  Require ... all supported source regimes, both transition orders,
# all required charger branches."
#
# The cell voltages below are chosen to reach BOTH VINDPM regimes -- the fixed
# 3.6 V one below TI's 3.5 V tracking floor and the battery-tracking one above
# it -- and BOTH supplement-hysteresis directions.  The ILIM corners and every
# enumerated source class are crossed with them, so the branch set the oracle
# sees is a FUNCTION OF THE DEVICE, not of the release's luck.
# D-795 / R14-05.  THE CHARGER DOMAIN IS THE ORACLE'S, NOT THIS FILE'S.
#
# D-794 declared the cells, powers and histories HERE and the oracle only
# asked whether the resulting branch NAMES were all present.  The axes now
# live in `aqroot_power_oracle` and this function iterates THEM, so the
# canonical side cannot shrink the domain it is judged over; an unsolved point
# is delivered as a REFUSAL with the inputs the oracle needs to re-check it.


def _oracle_charger_states():
    states, refusals = [], []
    classes = {c["key"]: c for c in apm.USB_SOURCE_CLASSES}
    for vbat in apo.EXPECTED_CHARGER_CELLS_V:
        # D-796 / D796-08: every BATFET state the cell admits, and no
        # SUPPLEMENT history under the trip.
        for bf in apm.batfet_states_at(vbat):
            for w in apo.EXPECTED_CHARGER_POWERS_W:
                for ilim in apo.EXPECTED_ILIM_CORNERS:
                    for ck in apo.EXPECTED_SOURCE_CLASSES:
                        cls = classes.get(ck)
                        for prev in apo.histories_for(bf):
                            for ic in apo.EXPECTED_ICHG_CORNERS:
                                key = apo.charger_domain_key(
                                    vbat, w, ilim, ck, prev, ic, bf)
                                if cls is None:
                                    continue
                                st = apm.charger_state(
                                    w, vbat, ilim, vbus_V=cls["vbus_V"],
                                    path_ohm=cls["path_ohm"], source_key=ck,
                                    previous_mode=prev, ichg_corner=ic,
                                    batfet=bf)
                                if st is not None:
                                    states.append(dict(st, domain_key=key))
                                    continue
                                refusals.append(dict(
                                    domain_key=key, refused=True,
                                    reason=("sys_collapse_below_vbuvlo"
                                            if bf != "connected"
                                            else "no operating point"),
                                    vbat_V=vbat, system_W=w, batfet=bf,
                                    previous_mode=prev, ichg_corner=ic,
                                    vbus_V=cls["vbus_V"],
                                    path_ohm=cls["path_ohm"],
                                    ilim_A=(apm.BQ25185["ilim_max_A"]
                                            if ilim == "max" else
                                            apm.BQ25185["ilim_min_A"]),
                                    sweep=0.0))
    return states, refusals


def _oracle_network_states(cell_net, pass_pair=None, board_forward=None):
    spec = PASS_PAIR if pass_pair is None else pass_pair
    fixed = apm.upstream_fixed_ohm("max", board_forward)
    rows = []
    for st in cell_net["states"]:
        for load, v in st["loads"].items():
            # D-796 / R15-02: every row carries the LOAD SET it claims, so the
            # oracle re-derives its demand from the key rather than trusting
            # the physics that happens to sit under it.
            load_set = dict(modes=list(st["modes"]),
                            internal_3v3_A=st["internal_3v3_A"],
                            acc_3v3_A=v.get("acc_3v3_A"),
                            acc_5v_A=v.get("acc_5v_A"),
                            demand_W=v.get("demand_W"),
                            lowest_supported_cell_ocv_V=v.get(
                                "lowest_supported_cell_ocv_V"))
            for where in ("at_a_full_cell", "at_the_lowest_supported_cell"):
                s = v.get(where)
                if not s or "raw" not in s:
                    # D-795 / R14-05: an unsolved corner is a REFUSAL row,
                    # not an absent one, and it carries the named limits.
                    rows.append(dict(
                        key="%s/%s/%s" % (st["key"], load, where),
                        refused=True, load_set=load_set,
                        physical_limits=dict(v.get("limits_" + where) or {}),
                        binding_limit=list(v.get(
                            "binding_limit_at_the_floor") or [])))
                    continue
                q = s["raw"]
                rows.append(dict(
                    key="%s/%s/%s" % (st["key"], load, where),
                    load_set=load_set,
                    cell_V=q["cell_V"], amps=q["amps"], node_V=q["node_V"],
                    vsys_V=q["vsys_V"],
                    fixed_ohm=fixed, channels=spec["channels_in_series"],
                    channel_ohm=q["channel_ohm"]))
    return rows


def _oracle_transitions(cell_net):
    """The named transitions plus every permission-table row, flattened."""
    df = cell_net["derived_floors"]
    out, rejected = [], []
    for tr in df["transitions"]:
        out.append(dict(
            kind="named",
            transition=tr["transition"], state=tr["state"],
            post_node_V=tr.get("post_node_V"),
            pre_node_V=tr.get("pre_node_V"),
            floor_V=tr.get("required_reported_floor_V"),
            pre_ceiling_V=None,
            retention_floor_V=df["retention_floor_gridded_V"],
            permitted=tr.get("post_node_V") is not None))
    for edge in ("rail_edge_table", "mode_edge_table"):
        for row in df[edge]:
            entry = dict(
                kind="table",
                transition="%s/bits%d/rails%d" % (edge, row["mode_bits"],
                                                  row["rails"]),
                state=",".join(row["modes"]) or "(none)",
                # D-794 / R13-04: the SETTLED post-load node, so the oracle
                # can rule on retention rather than attainability alone.  A
                # permitted row with no settled node is itself a failure --
                # `transition_is_sound` refuses it -- because that is what a
                # dropped retention proof looks like.
                post_node_V=row.get("settled_post_node_V"),
                post_node_with_worst_burst_V=row.get(
                    "settled_post_node_with_worst_burst_V"),
                floor_V=row.get("floor_gridded_V"),
                pre_ceiling_V=row.get("pre_state_reported_ceiling_V"),
                retention_floor_V=df["retention_floor_gridded_V"],
                permitted=bool(row["permitted"]))
            if not row["permitted"]:
                rejected.append(entry)
            out.append(entry)
    # ---- D-793 / R12-04.  THE SEEDED CANARY. --------------------------
    #
    # "Seed at least one deliberately failing post-state so inclusion/
    # completeness cannot pass vacuously."  Twenty-six rows are refused on
    # this candidate, but a future board on which every combination happened
    # to be permitted would make the inclusion invariant true by accident.
    # `d790_declared` is the state D-791 retired -- both radios transmitting
    # beside the amplifier and both accessory rails -- and F12 already
    # requires it to stay refused.  It is named HERE so the rejection set is
    # never empty by construction, and if it ever started passing this clause
    # would say so rather than going quiet.
    canary = None
    for st in cell_net["states"]:
        if st["key"] != "d790_declared":
            continue
        v = st["loads"].get("acc_3v3_only") or {}
        # D-794 / R13-04: "A seeded canary must be a real rejected PHYSICAL
        # state, not merely an expected string/name."  D-793's canary carried
        # a Boolean and a sentence, so the oracle could only check that the
        # NAME was in the rejection set -- a canary whose refusal had quietly
        # become a bookkeeping artefact would have looked identical.  The
        # physical evidence travels with it now: the named limits this state
        # fails, at both cell corners, and the absence of an operating point
        # at either.  The oracle rules on THOSE.
        canary = dict(
            kind="table", transition="seeded_canary/d790_declared",
            state="d790_declared", post_node_V=None, floor_V=None,
            # D-796 / R15-02: the canary's own LOAD SET, so a canary carrying
            # another refused state's physics is caught by its content.
            load_set=dict(modes=list(st["modes"]),
                          internal_3v3_A=st["internal_3v3_A"],
                          accessory="acc_3v3_only",
                          acc_3v3_A=v.get("acc_3v3_A"),
                          acc_5v_A=v.get("acc_5v_A"),
                          demand_W=v.get("demand_W")),
            pre_ceiling_V=None,
            retention_floor_V=df["retention_floor_gridded_V"],
            permitted=bool(v.get("supported")),
            physical_limits={
                "at_a_full_cell": v.get("limits_at_a_full_cell") or {},
                "at_the_lowest_supported_cell": v.get(
                    "limits_at_the_lowest_supported_cell") or {}},
            physical_operating_points={
                "at_a_full_cell": (v.get("at_a_full_cell") or {}).get("raw"),
                "at_the_lowest_supported_cell": (
                    v.get("at_the_lowest_supported_cell") or {}).get("raw")},
            binding_limit=list(v.get("binding_limit_at_the_floor") or []),
            why="a DELIBERATELY failing post-state, so the rejection set "
                "cannot be empty by accident and the inclusion invariant "
                "cannot pass vacuously")
    if canary is not None:
        out.append(canary)
        if not canary["permitted"]:
            rejected.append(canary)
    return out, rejected


def judge_independent_oracle(cell_net, board_forward=None, ambient_C=None):
    scalars = _oracle_scalars(ambient_C)
    registry = apm.registry()
    charger_states, charger_refusals = _oracle_charger_states()
    transitions, rejected = _oracle_transitions(cell_net)
    network = _oracle_network_states(cell_net, board_forward=board_forward)
    canonical_path = apm.upstream_fixed_ohm("max", board_forward)
    board_20C = sum((board_forward or {}).get(x["key"], x["ohm_20C"])
                    for x in apm.BOARD_FORWARD_SEGMENTS)
    _cc = cell_net["the_charge_regime_is_bounded_in_the_half_treg_cannot_reach"][
        "load_ceiling"]
    regime_rows = _cc["_regime"]["rows"]
    regime_published = dict(
        universal_no_discharge_published_W=_cc[
            "universal_no_discharge_published_W"],
        junction_safe_published_W=_cc["junction_safe_system_W"],
        envelope=_cc["no_discharge_envelope"])
    thermal_states = _cc["_completion"]["_states"]
    extra = dict(charger_refusals=charger_refusals, regime_rows=regime_rows,
                 regime_published=regime_published,
                 thermal_states=thermal_states,
                 network_terms=cell_net.get("network_power_terms"))

    def _audit(cs=None, tr=None, rj=None, path=None, net=None, **kw):
        args = dict(extra)
        args.update(kw)
        return apo.audit(registry, scalars,
                         charger_states if cs is None else cs,
                         transitions if tr is None else tr,
                         rejected if rj is None else rj, board_20C,
                         canonical_path if path is None else path,
                         network if net is None else net, **args)
    ok, rep = _audit()

    # ---- D-796 / R15-01: the thermally-closed corners the charging-state
    # junction figures are read from, re-judged by the ORACLE's own thermal
    # label rule -- including every TREG limit-cycle hot phase.
    _js = _cc["junction_safe_system_W"]
    _corner_bad, _corner_n, _cycles = [], 0, 0
    for _i in range(1, 41):
        _jr = ara.charge_regime_junction(_i * _js / 40.0,
                                         ambient_C=ara.AMBIENT_DESIGN_MAX_C)
        for _k, _c in _jr["corners"].items():
            if _c.get("no_operating_point"):
                continue
            _corner_n += 1
            if (_c.get("thermal") or {}).get("regime") == \
                    "TREG_LIMIT_CYCLE_HOT_PHASE":
                _cycles += 1
            _ok, _w = apo.charger_branch_is_valid(_c)
            if not _ok and len(_corner_bad) < 8:
                _corner_bad.append("%s @ %.4f W: %s" % (_k, _i * _js / 40.0,
                                                        _w[:2]))
            elif not _ok:
                _corner_bad.append("...")
    rep["regime_junction_corners"] = dict(
        checked=_corner_n, limit_cycle_hot_phases=_cycles,
        problems=_corner_bad, ok=not _corner_bad)
    ok = bool(ok and not _corner_bad and _corner_n > 0)

    # ---- THE MUTATIONS.  Each must be CAUGHT, for its own reason. ---------
    def _mut_halve_package_heat():
        bad = [dict(st) for st in charger_states]
        for st in bad:
            st["package_W"] = st["package_W"] * 0.5
            st["package_W_treg_cannot_reduce"] = (
                st["package_W_treg_cannot_reduce"] * 0.5)
        o, _ = apo.audit(registry, scalars, bad, transitions, rejected,
                         board_20C, canonical_path, network, **extra)
        return o

    def _mut_delete_energy_oracle():
        """Ablate the energy accounting and watch Astra's mutation get through.

        D-792's `energy_balance` compared `p_in + p_from_cell - p_sys -
        p_stored` with `p_diss`, which was DEFINED as that expression three
        lines earlier: the check was `0 == 0`, and that is exactly what let a
        halved canonical package heat pass the whole F1-F13 suite.

        This mutation proves the replacement is load-bearing rather than
        decorative: the SAME halved-package state set is REFUSED while the
        energy accounting is present and ACCEPTED once it is removed.  A
        version of this oracle that watched the package heat with nothing but
        a tautology would fail this claim.
        """
        bad = [dict(st) for st in charger_states]
        for st in bad:
            st["package_W"] = round(st["package_W"] * 0.5, 6)
            st["package_W_treg_cannot_reduce"] = round(
                st["package_W_treg_cannot_reduce"] * 0.5, 6)
            # D-795: both COPIES are halved together, so the raw/summary
            # equality gate cannot see it and only the energy accounting can.
            q = dict(st["raw"])
            q["p_pkg"] = q["p_pkg"] * 0.5
            q["p_treg_cannot"] = q["p_treg_cannot"] * 0.5
            st["raw"] = q
            st["package_W"] = round(q["p_pkg"], 6)
            st["package_W_treg_cannot_reduce"] = round(q["p_treg_cannot"], 6)
        with_term, _ = apo.audit(registry, scalars, bad, transitions,
                                 rejected, board_20C, canonical_path, network, **extra)
        without_term, _ = apo.audit(registry, scalars, bad, transitions,
                                    rejected, board_20C, canonical_path,
                                    network, without_energy_oracle=True, **extra)
        # CAUGHT means: refused with the accounting, and NOT refused without.
        return bool(with_term or not without_term)

    def _mut_remove_5v_first():
        bad = [t for t in transitions
               if t["transition"] not in ("first_rail_5v",
                                          "second_rail_3v3")]
        o, _ = apo.audit(registry, scalars, charger_states, bad, rejected,
                         board_20C, canonical_path, network, **extra)
        return o

    def _mut_discard_failed_post_states():
        o, _ = apo.audit(registry, scalars, charger_states, transitions, [],
                         board_20C, canonical_path, network, **extra)
        return o

    def _mut_reverse_gauge_error():
        """A post-read charged in the OPTIMISTIC direction: the settled node
        is credited with the gauge error instead of being charged it."""
        bad = []
        g = scalars["gauge_verr_V"] + scalars["gauge_lsb_V"]
        for t in transitions:
            t2 = dict(t)
            if t2.get("post_node_V") is not None and t2.get("permitted"):
                # a state that only survives when the sign is inverted
                t2["post_node_V"] = (scalars["buvlo_bound_V"]
                                     + t2["retention_floor_V"]) * 0.5 - g
            bad.append(t2)
        o, _ = apo.audit(registry, scalars, charger_states, bad, rejected,
                         board_20C, canonical_path, network, **extra)
        return o

    def _mut_omit_return_path():
        o, _ = apo.audit(registry, scalars, charger_states, transitions,
                         rejected, board_20C,
                         canonical_path - apm.gnd_return_ohm(), network, **extra)
        return o

    # ==================================================================
    # D-794 / R13-04.  THE SIX ASTRA/FABLE COUNTEREXAMPLES, AS CONTROLS.
    #
    # Each of these is a thing Astra or Fable actually did to D-793 while
    # the release stayed green.  They are run on every release run, and
    # each must be REFUSED.
    # ==================================================================
    def _mut_delete_table_rows():
        """Astra: "deleted every F14 table row"."""
        bad = [t for t in transitions if t.get("kind") != "table"]
        o, _ = apo.audit(registry, scalars, charger_states, bad, rejected,
                         board_20C, canonical_path, network, **extra)
        return o

    def _mut_delete_network_states():
        """Astra: "deleted every F14 network state"."""
        o, _ = apo.audit(registry, scalars, charger_states, transitions,
                         rejected, board_20C, canonical_path, [], **extra)
        return o

    def _mut_duplicate_a_key():
        """Astra: "duplicated a named key".

        A duplicated key is worse than a missing one: the second copy
        SHADOWS the first in any set-or-dict-shaped check, so a state can
        be replaced rather than merely lost.
        """
        bad = list(transitions)
        first = next((t for t in transitions if t.get("kind") == "named"),
                     None)
        if first is not None:
            bad = bad + [dict(first)]
        o, _ = apo.audit(registry, scalars, charger_states, bad, rejected,
                         board_20C, canonical_path, network, **extra)
        return o

    def _mut_drop_row_retention():
        """Fable: table rows "only independently checked for attainability".

        Strip the settled post-load node off every permitted table row and
        the oracle is back to proving the floor is REACHABLE and nothing
        about whether the state it authorises holds.
        """
        bad = []
        for t in transitions:
            t2 = dict(t)
            if t2.get("kind") == "table" and t2.get("permitted"):
                t2["post_node_V"] = None
                t2["post_node_with_worst_burst_V"] = None
            bad.append(t2)
        o, _ = apo.audit(registry, scalars, charger_states, bad,
                         rejected, board_20C, canonical_path, network, **extra)
        return o

    def _mut_corrupt_summary_only():
        """Fable: "corrupted canonical summary fields can be invisible".

        The PUBLIC numbers -- the ones every document, consumer and human
        reads -- are moved and the full-precision `raw` twin is left alone.
        D-793's oracle preferred `raw`, so every identity still closed.
        """
        bad = []
        for st in charger_states:
            s = dict(st)
            for k in ("input_A", "system_A", "charge_A", "supplement_A",
                      "vsys_V", "vin_pin_V", "package_W"):
                if isinstance(s.get(k), float):
                    s[k] = round(s[k] * 0.5 + 0.001, 6)
            bad.append(s)
        o, _ = apo.audit(registry, scalars, bad, transitions, rejected,
                         board_20C, canonical_path, network, **extra)
        return o

    def _mut_corrupt_raw_only():
        """The other direction: the `raw` block is moved and the published
        summary left alone.  Neither copy may drift from the other."""
        bad = []
        for st in charger_states:
            s = dict(st)
            q = dict(s.get("raw") or {})
            for k in ("i_in", "i_sys", "vsys", "v_pin"):
                if isinstance(q.get(k), float):
                    q[k] = q[k] * 0.5 + 0.001
            s["raw"] = q
            bad.append(s)
        o, _ = apo.audit(registry, scalars, bad, transitions, rejected,
                         board_20C, canonical_path, network, **extra)
        return o

    # ==================================================================
    # D-795 / R14-05.  THE ROUND-14 COLLAPSES, AS CONTROLS.
    # ==================================================================
    def _mut_one_row_per_mode():
        seen, bad = set(), []
        for st in charger_states:
            if st["mode"] not in seen:
                seen.add(st["mode"])
                bad.append(st)
        return _audit(cs=bad)[0]

    def _mut_delete_supplement_history():
        return _audit(cs=[st for st in charger_states
                          if st.get("previous_mode") != "SUPPLEMENT"])[0]

    def _mut_delete_selected_network_rows():
        return _audit(net=[n for i, n in enumerate(network) if i % 7 != 3])[0]

    def _mut_drop_refusals():
        return _audit(charger_refusals=[])[0]

    def _mut_delete_full_cell_regime_rows():
        return _audit(regime_rows=[r for r in regime_rows
                                   if r["vbat_V"] < 4.2])[0]

    def _mut_inflate_nd():
        pub = dict(regime_published)
        pub["universal_no_discharge_published_W"] = 3.600
        return _audit(regime_published=pub)[0]

    def _mut_inflate_js():
        pub = dict(regime_published)
        pub["junction_safe_published_W"] = (
            regime_published["junction_safe_published_W"] + 0.25)
        return _audit(regime_published=pub)[0]

    def _mut_heat_summary_only():
        bad = []
        for st in charger_states:
            s2 = dict(st)
            for k in ("input_fet_W", "charge_fet_W", "batfet_W",
                      "total_dissipation_W", "internal_loss_sum_W"):
                s2[k] = round(s2[k] * 0.5, 6)
            bad.append(s2)
        return _audit(cs=bad)[0]

    def _mut_heat_raw_only():
        bad = []
        for st in charger_states:
            s2 = dict(st)
            q = dict(s2["raw"])
            for k in ("p_input_fet", "p_charge_fet", "p_batfet",
                      "p_diss_total", "p_loss_sum"):
                q[k] = q[k] * 0.5
            s2["raw"] = q
            bad.append(s2)
        return _audit(cs=bad)[0]

    def _mut_d794_sys_reg_under_ilim():
        """Put back D-794's physics: an ILIM state with SYS at 4.41 V and the
        charge folded by fiat."""
        bad = []
        for st in charger_states:
            s2 = dict(st)
            if s2["mode"] in ("ILIM", "VINDPM"):
                q = dict(s2["raw"])
                v = q["vsys_reg"]
                q["vsys"] = v
                q["i_sys"] = q["p_sys"] / v
                q["i_chg"] = max(0.0, q["i_in"] - q["i_sys"])
                s2["raw"] = q
                s2["vsys_V"] = round(v, 6)
                s2["system_A"] = round(q["i_sys"], 6)
                s2["charge_A"] = round(q["i_chg"], 6)
            bad.append(s2)
        return _audit(cs=bad)[0]

    def _mut_drop_thermal():
        return _audit(thermal_states=[])[0]

    # ==================================================================
    # D-796 / ROUND-15.  EACH CONTROL MUST FAIL FOR ITS OWN REASON: the
    # audit is refused AND the refusal names the defect the control plants.
    # ==================================================================
    def _refused_for(reason, **kw):
        o, r = _audit(**kw)
        return bool(o or reason not in json.dumps(r, default=str))

    def _swap_content(states, key_from, key_to):
        by = {x.get("domain_key"): x for x in states}
        out = []
        for x in states:
            k = x.get("domain_key")
            if key_to(k) and key_from(k) in by:
                out.append(dict(by[key_from(k)], domain_key=k))
            else:
                out.append(x)
        return out

    def _mut_o01():
        bad = _swap_content(
            charger_states, lambda k: k.replace("vbat4.221/", "vbat4.200/"),
            lambda k: (k or "").startswith("vbat4.221/"))
        return _refused_for("labelled a 4.221 V cell", cs=bad)

    def _mut_o04():
        by = {n["key"]: n for n in network}
        bad = []
        for n in network:
            if n["key"].endswith("/at_the_lowest_supported_cell"):
                src = by.get(n["key"].replace("at_the_lowest_supported_cell",
                                              "at_a_full_cell"))
                if src is not None and not src.get("refused") and \
                        not n.get("refused"):
                    n = dict(src, key=n["key"])
            bad.append(n)
        return _refused_for("carries a FULL-cell solve", net=bad)

    def _mut_pm2():
        other = next(n for n in network if n.get("refused")
                     and not n["key"].startswith("d790_declared/"))
        bad_tr = []
        for t in transitions:
            if t.get("transition") == apo.REQUIRED_SEEDED_REJECTION:
                t = dict(t, load_set=dict(other["load_set"],
                                          accessory=apo.CANARY_ACCESSORY),
                         physical_limits={"at_a_full_cell":
                                          other["physical_limits"],
                                          "at_the_lowest_supported_cell":
                                          other["physical_limits"]})
            bad_tr.append(t)
        bad_rj = [dict(t) if t.get("transition")
                  != apo.REQUIRED_SEEDED_REJECTION else next(
                      x for x in bad_tr if x.get("transition")
                      == apo.REQUIRED_SEEDED_REJECTION) for t in rejected]
        return _refused_for("is labelled d790_declared", tr=bad_tr,
                            rj=bad_rj)

    def _mut_thermal_collapse():
        one = next(st for st in thermal_states
                   if st["thermal"]["regime"] == "TREG_EQUILIBRIUM")
        return _refused_for("thermal population", thermal_states=[one])

    def _mut_regime_ambient():
        by = {r["key"]: r for r in regime_rows}
        bad = []
        for r in regime_rows:
            if r["key"].endswith("/amb40"):
                src = by[r["key"][:-len("amb40")] + "amb0"]
                r = dict(src, key=r["key"])
            bad.append(r)
        return _refused_for("the key says", regime_rows=bad)

    def _cold_treg_states():
        """D-795's own behaviour: a bisected program labelled TREG with the
        junction below the threshold."""
        out = []
        for st in thermal_states:
            th = st["thermal"]
            if th["regime"] != "TREG_EQUILIBRIUM":
                out.append(st)
                continue
            c = st["controls"]
            kw = dict(ilim_corner=st["ilim_corner"],
                      ichg_corner=st["ichg_corner"],
                      vbus_V=st["vbus_source_V"], path_ohm=st["path_ohm"],
                      source_key=st["source_key"], sweep=c["sweep"],
                      batfet=st["batfet"])
            cold = apm.charger_state(st["system_W"], st["vbat_V"],
                                     ichg_program_A=c["charge_program_A"]
                                     * 0.6, charge_loop="TREG", **kw)
            tj, air, internal = apm.charger_junction(
                cold, th["ambient_C"], th["r_sys_K_per_W"],
                th["theta_ja_C_per_W"], th["delivered_out_W"])
            out.append(dict(cold, domain_key=st["domain_key"],
                            thermal=dict(th, junction_C=round(tj, 6),
                                         internal_air_C=round(air, 6),
                                         internal_W=round(internal, 6))))
        return out

    def _mut_cold_treg():
        return _refused_for("COLD TREG", thermal_states=_cold_treg_states())

    def _d795_spec():
        # D-795's BUVLO semantics: nothing stopped a 2.85 V cell supplementing
        return dict(apm.BQ25185, vbuvlo_typ_V=2.0)

    def _mut_supplement_below_uvlo():
        bad_cs, bad_ref = list(charger_states), []
        for r in charger_refusals:
            if r.get("batfet") != "uvlo_open":
                bad_ref.append(r)
                continue
            k = apo.parse_charger_key(r["domain_key"])
            st = apm.charger_state(
                r["system_W"], r["vbat_V"], k["ilim"], spec=_d795_spec(),
                vbus_V=r["vbus_V"], path_ohm=r["path_ohm"],
                source_key=k["source"], previous_mode=r["previous_mode"],
                ichg_corner=r["ichg_corner"])
            if st is None:
                bad_ref.append(r)
                continue
            bad_cs.append(dict(st, batfet="uvlo_open",
                               domain_key=r["domain_key"]))
        return _refused_for("supplement at or under VBUVLO", cs=bad_cs,
                            charger_refusals=bad_ref)

    def _mut_no_charge_above_dppm():
        bad = []
        for st in charger_states:
            tu = st["controls"]["threshold_used"] or ""
            if st["mode"] in apm.SUPPLEMENTING_MODES and tu.startswith("the CC loop"):
                nc = apm.charger_state(
                    st["system_W"], st["vbat_V"], st["ilim_corner"],
                    vbus_V=st["vbus_source_V"], path_ohm=st["path_ohm"],
                    source_key=st["source_key"],
                    previous_mode=st["previous_mode"],
                    ichg_corner=st["ichg_corner"], ichg_program_A=0.0,
                    charge_loop="CC", batfet=st["batfet"])
                if nc is not None:
                    st = dict(nc, domain_key=st["domain_key"])
            bad.append(st)
        return _refused_for("NO_CHARGE above VDPPM", cs=bad)

    def _mut_fold_without_treg():
        bad = []
        for st in charger_states:
            if st["mode"] == "SYS_REG" and st["charge_A"] > 0.1:
                f = apm.charger_state(
                    st["system_W"], st["vbat_V"], st["ilim_corner"],
                    vbus_V=st["vbus_source_V"], path_ohm=st["path_ohm"],
                    source_key=st["source_key"],
                    previous_mode=st["previous_mode"],
                    ichg_corner=st["ichg_corner"],
                    ichg_program_A=st["charge_A"] * 0.5, charge_loop="CC",
                    batfet=st["batfet"])
                if f is not None:
                    st = dict(f, domain_key=st["domain_key"])
            bad.append(st)
        return _refused_for("no thermal regulation", cs=bad)

    def _mut_latched_without_history():
        bad = []
        for st in charger_states:
            k = st["domain_key"]
            # D-797: a supplement held by its history is either inside the
            # VBSUP1/VBSUP2 band or RETAINED (the input cannot carry the load
            # at SYS = VBAT); both exist only because of the history.
            if st["mode"] in apm.SUPPLEMENTING_MODES and "/SUPPLEMENT/" in k and (
                    st["controls"]["inside_the_supplement_hysteresis_band"]
                    or st["controls"].get("supplement_retained_by_history")):
                st = dict(st, previous_mode=None)
            bad.append(st)
        return _refused_for("labelled history", cs=bad)

    def _mut_history_under_trip():
        bad = []
        for st in charger_states:
            if st.get("batfet") == "uvlo_open" and \
                    st.get("previous_mode") == "NO_CHARGE":
                st = dict(st, previous_mode="SUPPLEMENT",
                          domain_key=st["domain_key"].replace(
                              "/NO_CHARGE/", "/SUPPLEMENT/"))
            bad.append(st)
        return _refused_for("SUPPLEMENT history with the BATFET "
                            "disconnected", cs=bad)

    def _static_supplement_at_node(st):
        """The D-797 state: STATIC supplement at the supplementing node,
        every public field and its raw twin re-derived so the only
        inconsistency left is the comparator."""
        raw = dict(st["raw"])
        node = raw["supplement_node_V"]
        r_src = raw["path"] + raw["ron_in"]
        i_in = max(0.0, min(raw["i_cap"], (raw["vbus"] - node) / r_src))
        i_sys = raw["p_sys"] / node
        i_supp = max(0.0, i_sys - i_in)
        v_pin = raw["vbus"] - i_in * raw["path"]
        p_in_fet = max(0.0, (v_pin - node) * i_in)
        p_bat = max(0.0, (raw["vbat"] - node) * i_supp)
        p_cable = i_in * i_in * raw["path"]
        p_in = raw["vbus"] * i_in
        p_cell = raw["vbat"] * i_supp
        raw.update(vsys=node, i_in=i_in, i_sys=i_sys, i_supp=i_supp,
                   v_pin=v_pin, p_input_fet=p_in_fet, p_batfet=p_bat,
                   p_pkg=p_in_fet + p_bat, p_cable=p_cable, p_in=p_in,
                   p_from_cell=p_cell, p_ron_only=i_in * i_in * raw["ron_in"],
                   p_treg_cannot=p_in_fet + p_bat,
                   p_diss_total=p_in + p_cell - raw["p_sys"],
                   p_loss_sum=p_in_fet + p_bat + p_cable,
                   supplement_regime="STATIC")
        ctl = dict(st["controls"], supplement_regime="STATIC")
        return dict(
            st, mode="SUPPLEMENT", raw=raw, controls=ctl,
            vsys_V=round(node, 6), vin_pin_V=round(v_pin, 6),
            input_A=round(i_in, 6), system_A=round(i_sys, 6),
            supplement_A=round(i_supp, 6),
            input_fet_W=round(p_in_fet, 6), batfet_W=round(p_bat, 6),
            input_fet_resistive_only_W=round(i_in * i_in * raw["ron_in"], 6),
            cable_W=round(p_cable, 6), package_W=round(p_in_fet + p_bat, 6),
            package_W_treg_cannot_reduce=round(p_in_fet + p_bat, 6),
            source_W=round(p_in, 6), from_cell_W=round(p_cell, 6),
            total_dissipation_W=round(p_in + p_cell - raw["p_sys"], 6),
            internal_loss_sum_W=round(p_in_fet + p_bat + p_cable, 6))

    # ---- D-797 ------------------------------------------------------------
    def _mut_hypothetical_exit():
        """D-796's behaviour: a SUPPLEMENT history judged on the BATFET-off
        node, so the retained supplement is replaced by whatever the part
        would do with no history."""
        bad = []
        for st in charger_states:
            if st.get("previous_mode") == "SUPPLEMENT" and \
                    st["mode"] in apm.SUPPLEMENTING_MODES and \
                    st["controls"].get("supplement_retained_by_history"):
                alt = apm.charger_state(
                    st["system_W"], st["vbat_V"], st["ilim_corner"],
                    vbus_V=st["vbus_source_V"], path_ohm=st["path_ohm"],
                    source_key=st["source_key"], previous_mode=None,
                    ichg_corner=st["ichg_corner"], batfet=st["batfet"])
                if alt is not None and \
                        alt["mode"] not in apm.SUPPLEMENTING_MODES:
                    st = dict(alt, previous_mode="SUPPLEMENT",
                              domain_key=st["domain_key"])
            bad.append(st)
        return _refused_for("EXIT TOO EARLY", cs=bad)

    # ---- D-798 ------------------------------------------------------------
    def _mut_static_retention_above_exit():
        """D-797's behaviour: a SUPPLEMENT history held as a STATIC
        supplement wherever any shortfall exists at SYS = VBAT -- including
        where the actual supplementing SYS already sits ABOVE the VBSUP2
        exit (Astra R17-01).  Rebuilt at the supplementing node itself, every
        field re-derived, so only the comparator can refuse it."""
        bad, n = [], 0
        for st in charger_states:
            if st.get("previous_mode") == "SUPPLEMENT" and \
                    st["mode"] == "SUPPLEMENT_CYCLE":
                st = _static_supplement_at_node(st)
                n += 1
            bad.append(st)
        return bool(n == 0 or _refused_for("RETENTION TOO LATE", cs=bad))

    def _mut_cycle_exits_to_the_hypothetical_node():
        """D-796's behaviour on the Round-17 class: the comparator cycle
        replaced by the no-history BATFET-off state."""
        bad, n = [], 0
        for st in charger_states:
            if st.get("previous_mode") == "SUPPLEMENT" and \
                    st["mode"] == "SUPPLEMENT_CYCLE":
                alt = apm.charger_state(
                    st["system_W"], st["vbat_V"], st["ilim_corner"],
                    vbus_V=st["vbus_source_V"], path_ohm=st["path_ohm"],
                    source_key=st["source_key"], previous_mode=None,
                    ichg_corner=st["ichg_corner"], batfet=st["batfet"])
                if alt is not None and \
                        alt["mode"] not in apm.SUPPLEMENTING_MODES:
                    st = dict(alt, previous_mode="SUPPLEMENT",
                              domain_key=st["domain_key"])
                    n += 1
            bad.append(st)
        return bool(n == 0 or _refused_for("EXIT TOO EARLY", cs=bad))

    def _mut_supplement_as_limit_cycle():
        bad, done = [], False
        for st in thermal_states:
            if not done and st["thermal"]["regime"] in (
                    "TREG_EQUILIBRIUM", "TREG_LIMIT_CYCLE_HOT_PHASE"):
                sup = apm.charger_state(
                    3.6, 3.4, "min", vbus_V=st["vbus_source_V"],
                    path_ohm=st["path_ohm"], source_key=st["source_key"],
                    previous_mode="SUPPLEMENT")
                th = dict(st["thermal"], regime="TREG_LIMIT_CYCLE_HOT_PHASE",
                          treg_active=True,
                          limit_cycle=dict(cold_phase_junction_C=90.0))
                tj, air, internal = apm.charger_junction(
                    sup, th["ambient_C"], th["r_sys_K_per_W"],
                    th["theta_ja_C_per_W"], th["delivered_out_W"])
                th.update(junction_C=round(tj, 6))
                st = dict(sup, domain_key=st["domain_key"], thermal=th)
                done = True
            bad.append(st)
        return _refused_for("a supplement has no path out of the hot phase",
                            thermal_states=bad)

    def _inflated_regime(delta_W=0.5):
        rows = []
        for r in regime_rows:
            r = dict(r)
            if r["junction_limited"]:
                new = round(r["junction_boundary_W"] + delta_W, 6)
                r.update(junction_W=new, junction_boundary_W=new,
                         ceiling_W=round(min(r["no_discharge_W"], new), 6),
                         binding=("no_discharge" if r["no_discharge_W"]
                                  <= new else "junction"))
                ev = dict(r["_evidence"])
                for lab, p_ in (("junction_at", new),
                                ("junction_above",
                                 new * (1.0 + 1e-7) + 1e-7)):
                    if isinstance(ev.get(lab), dict):
                        st_ = dict(ev[lab], system_W=round(p_, 6))
                        st_["raw"] = dict(st_["raw"], p_sys=p_)
                        ev[lab] = st_
                r["_evidence"] = ev
            rows.append(r)
        q = [r for r in rows if r["qualified"]]
        pub = dict(regime_published, junction_safe_published_W=(
            apo._floor_to_grid(min(r["junction_W"] for r in q))))
        env = []
        for e in regime_published["envelope"]:
            sel = [r for r in rows if r["source_class"] == e["source_class"]
                   and r["vbat_V"] == e["vbat_V"]]
            jl = [r["junction_W"] for r in sel if r["junction_limited"]]
            env.append(dict(e, junction_published_W=(
                apo._floor_to_grid(min(jl)) if jl else None)))
        pub["envelope"] = env
        return rows, pub

    def _mut_inflate_boundaries():
        rows, pub = _inflated_regime(0.5)
        return _refused_for("one step BELOW the junction boundary",
                            regime_rows=rows, regime_published=pub)

    def _mut_in_place_after_pass():
        """PASS once, then edit the SAME objects in place and ask again."""
        first_ok = _audit()[0]
        victim = next(r for r in regime_rows
                      if r["qualified"] and r["junction_limited"])
        saved = dict(victim)
        try:
            victim["junction_W"] = round(victim["junction_W"] + 0.5, 6)
            victim["junction_boundary_W"] = victim["junction_W"]
            second = _refused_for("one step BELOW the junction boundary")
        finally:
            victim.clear()
            victim.update(saved)
        return bool(not first_ok or second)

    def _pub_with(env):
        return dict(regime_published, envelope=env)

    def _pub_victim():
        env = [dict(e) for e in regime_published["envelope"]]
        i = next(k for k, e in enumerate(env) if e["qualified"])
        return env, i

    def _mut_pub_dup_bad_first():
        env, i = _pub_victim()
        bad = dict(env[i], no_discharge_published_W=9.0)
        return _refused_for("appears 2 times where 1 is expected",
                            regime_published=_pub_with([bad] + env))

    def _mut_pub_dup_bad_last():
        env, i = _pub_victim()
        bad = dict(env[i], no_discharge_published_W=9.0)
        return _refused_for("appears 2 times where 1 is expected",
                            regime_published=_pub_with(env + [bad]))

    def _mut_pub_dup_identical():
        env, i = _pub_victim()
        return _refused_for("appears 2 times where 1 is expected",
                            regime_published=_pub_with(env + [dict(env[i])]))

    def _mut_pub_extra_key():
        env, i = _pub_victim()
        extra = dict(env[i], vbat_V=4.3)
        return _refused_for("is not in the expected domain",
                            regime_published=_pub_with(env + [extra]))

    def _mut_pub_missing_key():
        env, i = _pub_victim()
        return _refused_for("is MISSING from the derivation",
                            regime_published=_pub_with(env[:i] + env[i + 1:]))

    def _mut_pub_nonfinite():
        env, i = _pub_victim()
        env[i] = dict(env[i], no_discharge_published_W=float("nan"))
        return _refused_for("is not a finite number",
                            regime_published=_pub_with(env))

    muts = {
        "d798_publication_duplicate_key_bad_first_good_last":
            _mut_pub_dup_bad_first,
        "d798_publication_duplicate_key_good_first_bad_last":
            _mut_pub_dup_bad_last,
        "d798_publication_duplicate_key_identical_copy":
            _mut_pub_dup_identical,
        "d798_publication_extra_key": _mut_pub_extra_key,
        "d798_publication_missing_key": _mut_pub_missing_key,
        "d798_publication_non_finite_value": _mut_pub_nonfinite,
        "d798_a_static_supplement_retained_above_the_vbsup2_exit":
            _mut_static_retention_above_exit,
        "d798_a_comparator_cycle_exited_to_the_hypothetical_node":
            _mut_cycle_exits_to_the_hypothetical_node,
        "d797_exit_judged_on_the_hypothetical_batfet_off_node":
            _mut_hypothetical_exit,
        "d797_an_absorbing_supplement_labelled_a_treg_limit_cycle":
            _mut_supplement_as_limit_cycle,
        "d797_inflate_every_junction_boundary_and_its_publication_by_half_a_watt":
            _mut_inflate_boundaries,
        "d797_mutate_the_passed_regime_in_place": _mut_in_place_after_pass,
        "o01_a_vbat4221_key_carrying_a_4200_solve": _mut_o01,
        "o04_a_lowest_cell_row_carrying_a_full_cell_solve": _mut_o04,
        "pm2_the_canary_carrying_another_refused_states_physics": _mut_pm2,
        "collapse_the_thermal_population_to_one_treg_state":
            _mut_thermal_collapse,
        "a_regime_row_carrying_another_ambients_evidence":
            _mut_regime_ambient,
        "restore_a_cold_treg_state": _mut_cold_treg,
        "restore_supplement_below_vbuvlo": _mut_supplement_below_uvlo,
        "restore_no_charge_above_dppm_with_the_cc_loop_active":
            _mut_no_charge_above_dppm,
        "fold_the_charge_above_dppm_without_treg": _mut_fold_without_treg,
        "a_latched_supplement_with_no_history":
            _mut_latched_without_history,
        "a_supplement_history_under_the_trip": _mut_history_under_trip,
        "collapse_the_charger_domain_to_one_row_per_mode":
            _mut_one_row_per_mode,
        "delete_the_supplement_history": _mut_delete_supplement_history,
        "delete_selected_network_rows": _mut_delete_selected_network_rows,
        "drop_the_charger_refusals": _mut_drop_refusals,
        "delete_the_full_cell_regime_rows": _mut_delete_full_cell_regime_rows,
        "inflate_the_published_no_discharge_figure": _mut_inflate_nd,
        "inflate_the_published_junction_safe_figure": _mut_inflate_js,
        "corrupt_the_heat_summary_only": _mut_heat_summary_only,
        "corrupt_the_heat_raw_only": _mut_heat_raw_only,
        "restore_d794_sys_reg_under_an_input_loop":
            _mut_d794_sys_reg_under_ilim,
        "drop_the_thermally_closed_states": _mut_drop_thermal,
        "delete_every_permission_table_row": _mut_delete_table_rows,
        "delete_every_network_state": _mut_delete_network_states,
        "duplicate_a_named_transition_key": _mut_duplicate_a_key,
        "drop_the_permitted_row_retention_proof": _mut_drop_row_retention,
        "corrupt_the_public_summary_only": _mut_corrupt_summary_only,
        "corrupt_the_raw_block_only": _mut_corrupt_raw_only,
        "halve_the_charger_package_heat": _mut_halve_package_heat,
        "delete_the_energy_oracle": _mut_delete_energy_oracle,
        "remove_the_5v_first_transition": _mut_remove_5v_first,
        "discard_the_failed_post_states": _mut_discard_failed_post_states,
        "reverse_the_gauge_error_direction": _mut_reverse_gauge_error,
        "omit_the_return_path": _mut_omit_return_path,
    }
    caught = {}
    for name in ORACLE_REQUIRED_MUTATIONS:
        caught[name] = bool(not muts[name]())
    rep["mutations_caught"] = caught
    rep["every_required_mutation_is_caught"] = bool(all(caught.values()))
    rep["required_mutations"] = list(ORACLE_REQUIRED_MUTATIONS)
    rep["mutation_reasons"] = {
        "d798_publication_duplicate_key_bad_first_good_last":
            "Round-17 R17-05: the publication is validated as an exact key "
            "MULTISET before any dictionary projection, so a bad duplicate "
            "ahead of the correct row cannot be overwritten unseen",
        "d798_publication_duplicate_key_good_first_bad_last":
            "Round-17 R17-05: the same attack in the other order",
        "d798_publication_duplicate_key_identical_copy":
            "Round-17 R17-05: a duplicate is refused even when it agrees",
        "d798_publication_extra_key":
            "Round-17 R17-05: a (source, cell) row outside the declared "
            "domain is refused",
        "d798_publication_missing_key":
            "Round-17 R17-05: a missing publication row is refused",
        "d798_publication_non_finite_value":
            "Round-17 R17-05: a NaN / infinite published figure is refused",
        "d798_a_static_supplement_retained_above_the_vbsup2_exit":
            "Round-17 R17-01: SLUSF65B 6.3.3's BATFET is unregulated, so a "
            "supplementing SYS is the cell less RON_BAT x the shortfall; "
            "where that is above VBAT - VBSUP2 the comparator opens the "
            "BATFET -- a static supplement there is the D-797 defect "
            "(retention too late) and is refused",
        "d798_a_comparator_cycle_exited_to_the_hypothetical_node":
            "Round-17 R17-01: once the BATFET opens, a capped input cannot "
            "raise SYS through the shortfall, so the part relaxes back to "
            "the VBSUP1 entry; replacing that cycle by the no-history "
            "BATFET-off state is the D-796 defect (exit too early)",
        "d797_exit_judged_on_the_hypothetical_batfet_off_node":
            "Round-16 R16-01: a part that was supplementing leaves only when "
            "its OWN SYS rises past VBAT - VBSUP2; judging exit on the "
            "BATFET-off node is the D-796 defect and is refused",
        "d797_an_absorbing_supplement_labelled_a_treg_limit_cycle":
            "Round-16 R16-01: a supplement carries no charge for TREG to fold "
            "and has no path out of the hot phase; it is absorbing, never a "
            "limit cycle",
        "d797_inflate_every_junction_boundary_and_its_publication_by_half_a_watt":
            "Round-16 R16-02: every boundary is RECOMPUTED one step below and "
            "above by the oracle's own states, so an inflation whose evidence "
            "and publication were edited to agree still fails",
        "d797_mutate_the_passed_regime_in_place":
            "Round-16 R16-02: the audit cache is keyed by a content digest, "
            "so the same objects edited in place after a PASS are re-audited",
        "o01_a_vbat4221_key_carrying_a_4200_solve":
            "Round-15 O01: a key is a claim about the state it labels; the "
            "oracle parses every key and requires the state's cell, power, "
            "ILIM, source physics, history, ICHG corner and BATFET to equal "
            "it",
        "o04_a_lowest_cell_row_carrying_a_full_cell_solve":
            "Round-15 O04: a lowest-supported-cell row must be solved at that "
            "row's own floor, strictly below a full cell",
        "pm2_the_canary_carrying_another_refused_states_physics":
            "Round-15 PM2: the canary's load set must be exactly "
            "d790_declared at acc_3v3_only, re-derived from the oracle's own "
            "product definition",
        "collapse_the_thermal_population_to_one_treg_state":
            "Round-15: the thermally-closed population is an exact multiset "
            "over source x ambient x scenario x cell x BATFET",
        "a_regime_row_carrying_another_ambients_evidence":
            "Round-15: a regime row's fields and evidence must be the ones "
            "its key names, ambient included",
        "restore_a_cold_treg_state":
            "Round-15 R15-01: TREG is a loop that becomes active BECAUSE the "
            "junction reaches the threshold; a TREG label on a cold state is "
            "a state the loop would not hold",
        "restore_supplement_below_vbuvlo":
            "SLUSF65B 6.3.3: no supplement at or under VBUVLO; the solve "
            "there is a SYS collapse",
        "restore_no_charge_above_dppm_with_the_cc_loop_active":
            "the CC loop pulls a zero-charge node above VBAT + VDPPM down; "
            "that NO_CHARGE state has no controller holding it",
        "fold_the_charge_above_dppm_without_treg":
            "only TREG may fold the charge with SYS above VBAT + VDPPM",
        "a_latched_supplement_with_no_history":
            "inside the VBSUP1/VBSUP2 band the history decides; a latched "
            "supplement without one is not the state its key names",
        "a_supplement_history_under_the_trip":
            "under the trip the part cannot have been supplementing",
        "collapse_the_charger_domain_to_one_row_per_mode":
            "the charger domain is an exact key multiset the oracle declares; "
            "one surviving row per branch name is thousands of missing keys",
        "delete_the_supplement_history":
            "every SUPPLEMENT-history key is missing and the (branch, "
            "history) populations and the hysteresis demonstration go empty",
        "delete_selected_network_rows":
            "the network domain is an exact multiset of solved rows and "
            "physical refusals, so a deleted row is a missing key",
        "drop_the_charger_refusals":
            "an unsolved point may not simply vanish: without its refusal "
            "row the domain is short",
        "delete_the_full_cell_regime_rows":
            "the regime claims range over 2.85..4.221 V and the high-VBAT "
            "rows are exactly where the no-discharge boundary collapses",
        "inflate_the_published_no_discharge_figure":
            "the oracle recomputes the universal no-discharge minimum from "
            "the rows and refuses a published figure that is not its floor",
        "inflate_the_published_junction_safe_figure":
            "the same, for the junction-safe power",
        "corrupt_the_heat_summary_only":
            "every printed heat field is equality-gated to its raw twin",
        "corrupt_the_heat_raw_only":
            "the raw heat twins are re-derived from the raw TERMINALS",
        "restore_d794_sys_reg_under_an_input_loop":
            "ILIM/VINDPM must hold SYS at VBAT + VDPPM; a folded charge above "
            "that node without TREG is refused by the physical inequality",
        "drop_the_thermally_closed_states":
            "the TREG branch is only exercised by thermally-closed states; "
            "without them a branch of the device goes unchecked",
        "halve_the_charger_package_heat":
            "the terminal-power balance no longer equals the internal loss "
            "sum -- the identity D-792 compared with itself",
        "delete_the_energy_oracle":
            "without the terminal-vs-internal term nothing watches the "
            "package heat at all, which is exactly what Astra exploited",
        "remove_the_5v_first_transition":
            "the completeness invariant refuses a derivation that enumerates "
            "only one rail order, and it is a VERDICT term now",
        "discard_the_failed_post_states":
            "an empty rejection set makes the inclusion check vacuous",
        "reverse_the_gauge_error_direction":
            "a granted enable settles below the retention floor it is judged "
            "against",
        "omit_the_return_path":
            "the independently summed source path no longer equals the "
            "canonical one",
        "delete_every_permission_table_row":
            "the oracle CONSTRUCTS the 32-row permission domain from the "
            "product's own three modes, two edges and two rail counts, and "
            "requires the exact multiset -- a set membership test could only "
            "have asked whether what survived was expected",
        "delete_every_network_state":
            "an empty cell-to-load domain means no KVL was independently "
            "re-derived at all, and every live state must contribute a row",
        "duplicate_a_named_transition_key":
            "a duplicated key SHADOWS whatever it repeats; the domain is an "
            "exact multiset, so a second copy is a failure rather than a "
            "no-op",
        "drop_the_permitted_row_retention_proof":
            "a permitted row with no settled post-load node has proved that "
            "its floor is reachable and nothing about whether the state it "
            "authorises survives the load arriving",
        "corrupt_the_public_summary_only":
            "the published summary must equal the published rounding of its "
            "full-precision twin; an oracle that reads only `raw` never sees "
            "the numbers the release actually ships",
        "corrupt_the_raw_block_only":
            "the same equality gate, from the other side: neither copy of a "
            "duplicated field may drift from the other",
    }
    rep["ok"] = bool(ok and rep["every_required_mutation_is_caught"])
    return rep["ok"], rep


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

    # D-793 / R12-01.  THE FOUR J4 -> R75 BOARD-COPPER SEGMENTS, MEASURED.
    # They are upstream of `R75.2` and therefore of everything the downstream
    # ledger prices, so nothing is double-counted; and they were in NO model
    # before D-793.
    def _live_segment_ohm(seg):
        nodes, edges = ara.build_graph(board, seg["net"])
        src = [ara.pad_key(pad_index[r]) for r in seg["src"] if r in pad_index]
        snk = [ara.pad_key(pad_index[r]) for r in seg["snk"] if r in pad_index]
        if not src or not snk:
            return float("inf")
        path, _ = ara.widest_bottleneck(nodes, edges, src, snk, 2.6)
        if not path:
            return float("inf")
        return sum(ara.RHO_CU * e["length_mm"] / e["area_mm2"] for e in path
                   if e["kind"] != "pad" and e["area_mm2"])

    live_board_forward = {seg["key"]: _live_segment_ohm(seg)
                          for seg in apm.BOARD_FORWARD_SEGMENTS}

    # ---- D-793 / R12-08.  THE SERIALISED BURST DELTA IS PINNED TO THE CODE
    # THAT IMPLEMENTS IT.
    #
    # The permission table may be derived at the worst SINGLE burst (75 mA)
    # instead of the coincident sum of all three (170 mA) ONLY if the shipped
    # firmware actually serialises them.  A restriction asserted in a comment
    # is what this programme keeps finding, so it is READ here: the arbiter
    # class, its refusal, and a `BurstArbiter::Hold` on each production burst
    # call site.  If any of it is absent the model falls back to the full
    # coincident delta and the table tightens by itself.
    _pol_txt = (POWER_POLICY.read_text(encoding="utf-8", errors="replace")
                if POWER_POLICY.exists() else "")
    _main_cpp = ROOT / "Firmware/src/demo/main.cpp"
    _main_txt = (_main_cpp.read_text(encoding="utf-8", errors="replace")
                 if _main_cpp.exists() else "")
    _arbiter_class = bool(
        "class BurstArbiter" in _pol_txt
        and "enum class BurstLoad" in _pol_txt
        and "if (active_ != BurstLoad::None) return false;" in _pol_txt)
    _hold_rx = (r"BurstArbiter::Hold\s+burst\(g_app\.burstArbiter\(\),"
                r"\s*BurstLoad::%s\);")
    _arbiter_sites = {
        "microSD": bool(re.search(_hold_rx % "MicroSdWrite", _main_txt)),
        "IR": bool(re.search(_hold_rx % "IrTransmit", _main_txt)),
    }
    # ...and there must be no UNARBITRATED call to either burst entry point.
    _unarbitrated = []
    for _name, _call in (("microSD", "probeSdCard()"), ("IR", "irSelfTest()")):
        _idx = _main_txt.find(_call)
        if _idx < 0:
            _unarbitrated.append("%s: no production call site at all" % _name)
            continue
        if _main_txt.count(_call) != 1:
            _unarbitrated.append("%s: %d call sites; exactly one is expected"
                                 % (_name, _main_txt.count(_call)))
            continue
        _window = _main_txt[max(0, _idx - 700):_idx]
        if "BurstArbiter::Hold" not in _window:
            _unarbitrated.append("%s: the call site takes no arbiter hold"
                                 % _name)
    burst_arbiter_proven = bool(_arbiter_class and all(_arbiter_sites.values())
                                and not _unarbitrated)
    burst_delta_A = apm.burst_transition_delta_A(
        serialised=burst_arbiter_proven)
    board_forward_within_bounds = all(
        live_board_forward[seg["key"]] <= seg["bound_ohm"] + 1e-12
        for seg in apm.BOARD_FORWARD_SEGMENTS)

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

    # ---- D-796 / Round-15 D796-05 item 1.  THE HARNESS RECORD'S CURRENTS
    # ARE F6's, GENERATED.  D-795's record said a single-limiter fault
    # "can reach 2.7536 A" and the worst conforming current was "2.1597 A";
    # F6 said 2.8628 A and 2.2689 A.  A technician running the fault test
    # would have measured against a number the model had moved away from.
    _harness_txt = harness_current_text(env)
    _harness_files = (ROOT / "docs/full-beta-v2/assembly/BATTERY_HARNESS.json",
                      ROOT / "hardware/demo/fab/aqroot-Demo-BATTERY-HARNESS.json")
    _harness_bad = []
    for _hf in _harness_files:
        _hj = json.loads(_hf.read_text(encoding="utf-8")) if _hf.exists() \
            else {}
        if (_hj.get("controlling_rating") or {}).get(
                "conforming_vs_fault") != _harness_txt["rating"]:
            _harness_bad.append("%s: controlling_rating.conforming_vs_fault "
                                "is not the F6-generated text" % _hf.name)
        if _harness_txt["acceptance"] not in (_hj.get("acceptance") or []):
            _harness_bad.append("%s: the fault-test acceptance line is not "
                                "the F6-generated one" % _hf.name)
        _flat_h = json.dumps(_hj)
        for _stale in ("2.7536", "2.1597", "d792_conforming_vs_fault",
                       # D-801 / D801-04: the unconditional interruption.
                       "BATOCP hiccup interrupts it",
                       "never a sustained harness current"):
            if _stale in _flat_h:
                _harness_bad.append("%s still carries %r" % (_hf.name, _stale))
    # D-801 / D801-04.  THE TEXT'S OWN PREMISES ARE CLAUSES.  "No BATOCP
    # interruption is claimed" is only honest if (a) every fault current lies
    # inside the declared BATOCP band -- a current above the band's maximum
    # WOULD be guaranteed to trip, and the text would then under-claim a real
    # protection -- and (b) the 3.85 A counterexample it prints really is a
    # threshold inside the band that does not trip at the double fault.  And
    # the claim D-796..D-800 made must be REFUSED by the rule that replaced it:
    # "interrupted" is only a guarantee for a current ABOVE THE WHOLE band.
    _decl = _harness_txt["ibat_ocp_declared_band_A"]
    _faults = (env["modes_I_bat_A"][_harness_txt["single_limiter_fault"][
        "state"]], _harness_txt["both_limiters_in_fault_admitted_A"],
        _harness_txt["both_limiters_in_fault_A"])

    def _batocp_interrupt_guaranteed(i_A, band):
        return i_A > band[1]

    if not all(_decl[0] <= f_ <= _decl[1] for f_ in _faults):
        _harness_bad.append("a fault current lies outside the declared "
                            "BATOCP band %r: re-derive the harness text"
                            % (_decl,))
    if not (_harness_txt["both_limiters_in_fault_A"] < 3.85 < _decl[1]):
        _harness_bad.append("the printed 3.85 A counterexample is not "
                            "between the double fault and the declared "
                            "band maximum")
    _batocp_controls = dict(
        # the D-800 reasoning: 3.8236 A > 3.6875 A (stated max) -> "trips"
        d801_04a_the_stated_band_alone_would_claim_the_trip=
            _batocp_interrupt_guaranteed(
                _harness_txt["both_limiters_in_fault_A"],
                (env["ibat_ocp_A"][0], env["ibat_ocp_A"][2])),
        # ...and the declared band refuses it
        d801_04b_the_declared_band_refuses_the_trip_claim=not
            _batocp_interrupt_guaranteed(
                _harness_txt["both_limiters_in_fault_A"], _decl),
        # ...with a concrete unit: a 3.85 A threshold does not trip
        d801_04c_a_3p85_A_threshold_does_not_trip_at_the_double_fault=(
            _harness_txt["both_limiters_in_fault_A"] < 3.85),
        # ...and the admitted double fault is the smaller of the two
        d801_04d_the_admitted_double_fault_is_below_the_sizing_one=(
            _harness_txt["both_limiters_in_fault_admitted_A"]
            < _harness_txt["both_limiters_in_fault_A"]),
        # ...and the D-800 sentence, injected, is caught by the stale scan
        d801_04e_the_d800_sentence_is_refused=any(
            t_ in "BOTH limiters in fault reach 3.8236 A, ABOVE the BQ25185 "
                  "BATOCP maximum (3.6875 A), so the recoverable BATOCP "
                  "hiccup interrupts it and it is never a sustained harness "
                  "current."
            for t_ in ("BATOCP hiccup interrupts it",
                       "never a sustained harness current")))
    if not all(_batocp_controls.values()):
        _harness_bad.append("D801-04 controls failed: %r" % {
            k: v for k, v in _batocp_controls.items() if not v})
    env["harness_currents_are_generated_from_f6"] = dict(
        generated=_harness_txt, problems=_harness_bad,
        d801_batocp_controls=_batocp_controls, ok=not _harness_bad)
    env_ok = env_ok and not _harness_bad

    # ---- F12: THE COMPLETE CELL-TO-LOAD NETWORK (D-791 / D790-A03) --------
    # Solved with the SAME live path resistances, the SAME derived rail
    # voltages and the SAME switch RONs F6 just used, so the two clauses
    # cannot describe different boards.
    _no = env["normal_operation"]
    cell_net_ok, cell_net = judge_cell_to_load(
        live_ohms, _no["v_3v3_used_V"], _no["v_acc5v_used_V"],
        _no["accessory_switch_ron_ohm"]["ACC_3V3"],
        _no["accessory_switch_ron_ohm"]["ACC_5V"],
        board_forward=live_board_forward, burst_delta_A=burst_delta_A)
    cell_net["burst_serialisation"] = dict(
        ruling_delta_A=burst_delta_A,
        serialised=burst_arbiter_proven,
        unserialised_delta_A=apm.burst_transition_delta_A(serialised=False),
        arbiter_class_is_in_the_shipped_policy_header=_arbiter_class,
        production_call_sites_take_a_hold=_arbiter_sites,
        unarbitrated_call_sites=_unarbitrated,
        subsets=apm.burst_subsets(),
        policy=apm.BURST_COINCIDENCE_POLICY,
        why="D-793 / R12-08.  The sustained ledger carries the three bursty "
            "lines at their duty AVERAGE, which is the right model for heat "
            "and the wrong one for a permission edge: the pre-read is taken "
            "in a quiet moment and the settled recheck lands 400 ms later, "
            "and a logging write, a card tap or a key repeat can begin "
            "anywhere in between.  The four ELECTRICAL limits and the "
            "firmware's own retention read are therefore evaluated with the "
            "worst reachable burst PRESENT; the junction and the internal "
            "air stay on the duty-averaged model, because a 200 ms burst "
            "does not move a minute-scale thermal integral.")
    cell_net_ok = cell_net_ok and burst_arbiter_proven
    cell_net["upstream"]["board_forward_measured_off_the_board"] = dict(
        segments=apm.board_forward_itemisation(live_board_forward),
        every_segment_is_inside_its_ceiling=board_forward_within_bounds,
        hot_total_ohm=apm.board_forward_ohm(live_board_forward),
        why="D-793 / R12-01.  J4.1 -> F1.1 -> Q2 drain -> Q3 drain -> R75.1.  "
            "All four are UPSTREAM of R75.2, so none of them is "
            "double-counted against the BAT_PROTECTED_P -> SYS term measured "
            "separately.  D-792's source-path model contained none of them.")
    cell_net_ok = cell_net_ok and board_forward_within_bounds
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
    # D-793: the comparison is over ALL SIXTEEN values per edge, SENTINELS
    # INCLUDED.  D-792's version only looked at mode-edge rows that were
    # PERMITTED, so a derivation in which the mode edge refused everything the
    # rail edge permitted -- which is a very large difference -- registered as
    # "the same table".  A refusal is a value.
    _rail_vec = {(r["mode_bits"], k): r["derived_%s" % k]
                 for r in _table_rows if r["edge"] == "rail"
                 for k in ("one_rail_V", "two_rails_V")}
    _mode_vec = {(r["mode_bits"], k): r["derived_%s" % k]
                 for r in _table_rows if r["edge"] == "mode"
                 for k in ("one_rail_V", "two_rails_V")}
    _edges_differ = bool(_rail_vec and _mode_vec and _rail_vec != _mode_vec)
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
        edges_compared_over_all_values_including_sentinels=True,
        rows_where_the_edges_disagree=sorted(
            "bits%d/%s" % (k[0], k[1]) for k in _rail_vec
            if _rail_vec.get(k) != _mode_vec.get(k)),
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
    # ---- D-797 / D797-02.  THE CHARGING MODE-ENTRY TABLE IS PINNED TOO. --
    # Eight values, indexed by the mode bits, derived above from the
    # cell-conditioned charging-safe envelope; a refusal is the sentinel and a
    # "no reading needed" row is exactly 0.0.  Parsed literally, like the
    # D-792 tables: a line that stops parsing fails rather than being skipped.
    _cm_src = re.search(
        r"static const float kChargingModeFloors\[8\] = \{(.*?)\n  \};",
        policy_text, re.S)
    _cm_fw = []
    if _cm_src:
        for _ln in _cm_src.group(1).splitlines():
            _m = re.match(r"\s*([A-Za-z0-9_.]+f?)\s*,", _ln)
            if _m:
                _cm_fw.append(None if _m.group(1).startswith(
                    "kAccessoryNotPermittedV") else float(
                        _m.group(1).rstrip("f")))
    _cm_rows_d = cell_net[
        "the_charge_regime_is_bounded_in_the_half_treg_cannot_reach"][
        "load_ceiling"]["charging_mode_entry_floor_rows"]
    _cm_rows = []
    for _r in sorted(_cm_rows_d, key=lambda r: r["mode_bits"]):
        _want = _r["reported_floor_V"] if _r["permitted"] else None
        _got = (_cm_fw[_r["mode_bits"]] if _r["mode_bits"] < len(_cm_fw)
                else "MISSING")
        _cm_rows.append(dict(mode_bits=_r["mode_bits"], modes=_r["modes"],
                             firmware_V=_got, derived_V=_want,
                             ok=bool(_got == _want)))
    cell_net["firmware_charging_mode_floor_table_equals_the_derivation"] = \
        dict(rows=_cm_rows, parsed=len(_cm_fw),
             consulted_when="no accessory rail is live",
             ok=bool(len(_cm_fw) == 8 and len(_cm_rows) == 8
                     and all(r["ok"] for r in _cm_rows)),
             why="D-797 / D797-02: the charging mode-entry floor is what "
                 "keeps a mode set out of an absorbing charger supplement "
                 "while the named adapter may be attached; the firmware "
                 "consults the table, so the table is pinned, sentinels "
                 "included.")
    cell_net["firmware_charging_mode_floor_table_equals_the_derivation_ok"] \
        = bool(cell_net[
            "firmware_charging_mode_floor_table_equals_the_derivation"]["ok"])
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
    # D-795 / R14-03: the JUNCTION-SAFE power is the one charge scalar.
    _need["charge_junction_safe_W"] = "**%.3f W**" % _cc["junction_safe_system_W"]
    _need["charge_no_discharge_universal_W"] = (
        "**%.3f W**" % _cc["universal_no_discharge_published_W"])
    _need["charge_named_adapter"] = "`%s`" % _cc["source_contract"][
        "named_adapter"]["part_number"]
    # D-794 / ROUND-13 FABLE DELTA.  TWO CEILINGS, TWO NAMES, BOTH PUBLISHED.
    #
    # ROUND-13: "Rename/explain any charger 'ceiling' according to what it
    # actually guarantees.  A no-battery-discharge boundary is not
    # automatically a full-charge-within-360-min timer guarantee."  D-793
    # published ONE number under the name `charge-time system power ceiling`
    # and it is the wrong name for it: 3.600 W bounds HEAT and BATTERY
    # DISCHARGE.  Charging to full inside the BQ25185's 360 min tMAXCHG on the
    # worst qualified cable needs a far lighter system load, and that is a
    # separate derivation with its own guardband.  Both are now published.
    # D-795 / R14-04: completion is a QUALIFICATION TARGET with its own
    # measurement of record -- the document must say so in those words.
    _need["charge_completion_is_a_qualification_target"] = (
        "QUALIFICATION TARGET")
    _need["charge_completion_measurement"] = "`C-PWR-CHARGE-02`"
    _heaviest = (max(_cc["permitted_while_charging"],
                     key=lambda r: r["system_W"])
                 if _cc["permitted_while_charging"] else None)
    if _heaviest is None:
        raise SystemExit("F12: no state is permitted while charging at all; "
                         "the charge-time ceiling has collapsed and that is "
                         "a design failure, not a documentation one")
    _need["charge_heaviest_permitted_state"] = "`%s` + `%s`" % (
        _heaviest["state"], _heaviest["load"])
    _need["charge_junction_folded_back"] = "**%.1f \u00b0C**" % _heaviest[
        "junction_with_charge_folded_back_C"]
    _need["charge_ambient_ceiling"] = "**%.1f \u00b0C**" % _heaviest[
        "charge_ambient_ceiling_C"]
    # ...and the DECLARED SIMULTANEOUS PAIR, which is the new product contract.
    _dp = df["declared_simultaneous_pair"]
    # D-793: the FULL pair may now be unsupported at EVERY ambient in the
    # declared envelope, so the required sentence is a different one and every
    # document that carries it has to carry whichever is true.  ONE string,
    # formatted once, consumed by all three normative documents.
    _FULL_PAIR_AMBIENT = (
        "**%.1f \u00b0C**" % _dp["full_pair_ambient_ceiling_C"]
        if _dp["full_pair_ambient_ceiling_C"] is not None
        else "**not supported at any ambient in the declared 0\u201340 "
             "\u00b0C envelope**")
    _need["declared_simultaneous_pair"] = "**%d mA** + **%d mA**" % (
        round(_dp["acc_3v3_A"] * 1000), round(_dp["acc_5v_A"] * 1000))
    # D-793: the FULL pair may now be unsupported at EVERY ambient in the
    # declared envelope, so the required sentence is a different one and the
    # document has to carry whichever is true.  A `%.1f` on None was a crash,
    # which is the honest failure mode, but the contract has to be able to
    # STATE the stronger restriction rather than only the weaker one.
    _need["full_pair_ambient_ceiling"] = _FULL_PAIR_AMBIENT
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
        "full_pair_ambient_ceiling": _FULL_PAIR_AMBIENT,
        "internal_3v3_peak_envelope": "**%.6f A**" % apm.peak_A(),
        "harness_itemised_max": "**%.3f m\u03a9**"
                                % (_up["harness_hot_aged_max_ohm"] * 1000.0),
        "upstream_fixed_max": "**%.3f m\u03a9**"
                              % (_up["fixed_series_max_ohm"] * 1000.0),
        "charge_junction_safe_W": "**%.3f W**" % _cc["junction_safe_system_W"],
        "charge_no_discharge_universal_W": (
            "**%.3f W**" % _cc["universal_no_discharge_published_W"]),
        "charge_named_adapter": "`%s`" % _cc["source_contract"][
            "named_adapter"]["part_number"],
        "charge_completion_is_a_qualification_target": "QUALIFICATION TARGET",
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
    # ---- D-793 / R12-04.  THE INDEPENDENT ORACLE, OVER THE SAME DATA. ----
    oracle_ok, oracle = judge_independent_oracle(
        cell_net, board_forward=live_board_forward)

    cell_net_ok = cell_net_ok and cell_net["firmware_constants_equal_the_derivation_ok"]
    cell_net_ok = cell_net_ok and cell_net[
        "firmware_permission_table_equals_the_derivation_ok"]
    cell_net_ok = cell_net_ok and cell_net[
        "firmware_charging_mode_floor_table_equals_the_derivation_ok"]

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
    # ======================================================================
    # D-794 / R13-06 + THE ROUND-13 FABLE DOCUMENTATION DELTA.  THE
    # MODE-INDEXED TABLE IS GENERATED, BECAUSE A SCALAR CANNOT CARRY IT.
    #
    # ROUND-13, IN ITS OWN WORDS: "FIRST_FIVE plan also has mode/floor
    # ambiguity: Fable found a 3.85 V 'first rail' statement while quiet-mode
    # firmware row is 3.80 V. ... Generate or machine-bind mode-specific
    # permission tables; do not hand-copy a single scalar where policy is
    # mode-indexed."  And the Fable delta: "Correct the mode-specific
    # first-rail table in FIRST_FIVE_ASSEMBLY_PLAN: quiet vs audio vs refused
    # TX modes must match production policy exactly."
    #
    # FABLE IS RIGHT AND THE AMBIGUITY IS REAL.  Both numbers are correct and
    # they answer different questions.  3.85 V is the PUBLISHED ENVELOPE -- the
    # worst floor any PERMITTED row of the table carries, which is what
    # `kAccessorySingleRailFloorV` holds and what DEVICE_SPEC publishes as a
    # single figure.  3.80 V is the floor the firmware actually applies in the
    # quiet row, bits = 0, which is the row a technician at the bench is in.
    # A document that prints only the envelope and calls it "the floor to
    # enable a first rail" is telling a technician to set a pack voltage
    # 50 mV higher than the board requires -- and, worse, it makes the two
    # refusals the procedure is trying to demonstrate look arbitrary.
    #
    # THE FIX IS NOT A BETTER SENTENCE.  The policy is a 32-entry function of
    # (edge, mode set, rail count); prose can restate it and prose will go
    # stale, which is the fourth time this section has gone stale the same
    # way.  So the TABLE is GENERATED here, from the same `df` rows the
    # firmware header is generated from, and the documents must carry it
    # VERBATIM.  A derivation that moves rewrites the document or fails.
    # ======================================================================
    def _permission_table_markdown():
        rows = ["| modes running | enable a rail, 1 on after | enable a rail, "
                "2 on after | enter this mode, 1 rail live | enter this mode, "
                "2 rails live |",
                "|---|---|---|---|---|"]
        by = {}
        for r in df["rail_edge_table"]:
            by[("rail", r["mode_bits"], r["rails"])] = r
        for r in df["mode_edge_table"]:
            by[("mode", r["mode_bits"], r["rails"])] = r
        names = list(df["mode_names"])
        for bits in range(1 << len(names)):
            on = [names[i] for i in range(len(names)) if bits & (1 << i)]
            cells = []
            for edge in ("rail", "mode"):
                for rails in (1, 2):
                    r = by.get((edge, bits, rails))
                    v = None if r is None else r["floor_gridded_V"]
                    cells.append("**REFUSED**" if v is None
                                 else "**%.2f V**" % v)
            rows.append("| %s | %s |"
                        % (", ".join(on) if on else "*(none)* — quiet",
                           " | ".join(cells)))
        return "\n".join(rows)

    _perm_md = _permission_table_markdown()
    _perm_docs = (
        "docs/full-beta-v2/assembly/FIRST_FIVE_ASSEMBLY_PLAN.md",
        "docs/full-beta-v2/DEVICE_SPEC.md",
    )
    _perm_missing = []
    for _rel in _perm_docs:
        _f = ROOT / _rel
        _t = (_f.read_text(encoding="utf-8", errors="replace")
              if _f.exists() else "")
        # These documents put normative blocks inside a blockquote, so the
        # comparison is made after stripping one level of `> ` and trailing
        # whitespace.  Nothing else is normalised: the CELLS must match.
        _flat = "\n".join(re.sub(r"^\s*>\s?", "", ln).rstrip()
                           for ln in _t.splitlines())
        if _perm_md not in _flat:
            _perm_missing.append(_rel)
    cell_net["the_mode_indexed_permission_table_is_generated_into_the_documents"] = dict(
        documents=list(_perm_docs), missing=_perm_missing,
        generated=_perm_md,
        rows=1 << len(df["mode_names"]),
        envelope_V=dict(
            single=df["enable_first_rail_floor_gridded_V"],
            dual=df["enable_second_rail_floor_gridded_V"],
            retention=df["retention_floor_gridded_V"]),
        quiet_rail_edge_one_rail_V=next(
            r["floor_gridded_V"] for r in df["rail_edge_table"]
            if r["mode_bits"] == 0 and r["rails"] == 1),
        ok=not _perm_missing,
        why="R13-06 + the Fable delta.  The published ENVELOPE and the QUIET "
            "row are different numbers and both are correct; a document that "
            "prints only the envelope and calls it the floor sends a "
            "technician to the wrong pack voltage.  The whole 32-entry policy "
            "is generated from the same rows the firmware header is generated "
            "from, so it cannot be hand-copied and cannot go stale.")
    cell_net["the_mode_indexed_permission_table_is_generated_into_the_documents_ok"] = bool(
        not _perm_missing)
    cell_net_ok = cell_net_ok and not _perm_missing

    # ======================================================================
    # D-795 / R14-03.  THE NO-DISCHARGE ENVELOPE IS GENERATED, LIKE THE
    # PERMISSION TABLE, BECAUSE IT IS A TABLE AND NOT A SCALAR.
    # ======================================================================
    _cc_env = cell_net[
        "the_charge_regime_is_bounded_in_the_half_treg_cannot_reach"][
            "load_ceiling"]

    def _charge_envelope_markdown():
        classes = [c for c in apm.USB_SOURCE_CLASSES]
        # D-796 / D796-02 + D796-08: every cell is marked with WHAT binds
        # it -- (T) the zero-charge junction could reach TREG's low end at
        # some ambient 0..40 C above it, so the row is TREG-CONDITIONED;
        # (C) under the BUVLO trip, where nothing supplements and a heavier
        # load collapses SYS.  An unmarked row is the supplement onset.
        head = ("| cell voltage | BATFET | "
                + " | ".join("%s%s" % (c["key"], "" if c["rules"]
                                       else " *(outside the contract)*")
                             for c in classes) + " |")
        rows = [head, "|---|---|" + "---|" * len(classes)]
        env_ = {(e["source_class"], e["vbat_V"]): e
                for e in _cc_env["no_discharge_envelope"]}

        def _cell(e):
            nd = e["no_discharge_published_W"]
            carry = e.get("input_carrying_published_W")
            b = set(e.get("no_discharge_bindings") or [])
            mark = ""
            if carry is not None and nd >= carry - 1e-9:
                mark = " (C)"
            elif "treg_could_fold_the_charge_to_zero" in b and (
                    carry is None or nd < carry - 1e-9):
                mark = " (T)"
            return "**%.2f W**%s" % (nd, mark)
        for v in ara.REGIME_VBAT_GRID_V:
            bf = " / ".join(apm.batfet_states_at(v))
            rows.append("| %.3f V | %s | %s |" % (v, bf, " | ".join(
                _cell(env_[(c["key"], v)]) for c in classes)))
        return "\n".join(rows)

    _env_md = _charge_envelope_markdown()
    _env_docs = ("docs/full-beta-v2/DEVICE_SPEC.md",
                 "docs/full-beta-v2/AQROOT_DEMO_FAB_HANDOFF.md",
                 "docs/full-beta-v2/assembly/FIRST_FIVE_ASSEMBLY_PLAN.md")

    def _flat(rel):
        f_ = ROOT / rel
        t_ = f_.read_text(encoding="utf-8", errors="replace") if f_.exists() \
            else ""
        return "\n".join(re.sub(r"^\s*>\s?", "", ln).rstrip()
                         for ln in t_.splitlines())
    _env_missing = [r_ for r_ in _env_docs if _env_md not in _flat(r_)]

    # ---- D-797 / D797-02.  THE CHARGING-SAFE ENVELOPE AND THE FIRMWARE'S
    # CHARGING FLOORS, GENERATED -- a cell-conditioned claim is a table.
    def _charging_safe_markdown():
        rows = ["| cell voltage | BATFET | charging-safe at this cell "
                "| charging-safe at this cell and above | binds |",
                "|---|---|---|---|---|"]
        for b in _cc_env["charging_safe_by_cell"]:
            rows.append("| %.3f V | %s | **%.2f W** | **%.2f W** | %s |" % (
                b["vbat_V"], " / ".join(b["batfet_states"]),
                b["charging_safe_published_W"],
                b["charging_safe_at_or_above_published_W"],
                "input-carrying (under the BUVLO trip)"
                if b["binding"] == "input_carrying_below_vbuvlo"
                else "reachable junction"))
        rows += ["", "| mode set (no accessory rail live) | system power "
                 "| cell floor while charging | firmware reported floor |",
                 "|---|---|---|---|"]
        for r in _cc_env["charging_mode_entry_floor_rows"]:
            rows.append("| %s | %.3f W | %s | %s |" % (
                " + ".join(r["modes"]) or "no optional mode", r["system_W"],
                "every cell" if r["reported_floor_V"] == 0.0 else (
                    "none" if r["charging_cell_floor_V"] is None
                    else "%.2f V" % r["charging_cell_floor_V"]),
                "**NOT PERMITTED**" if not r["permitted"] else (
                    "none needed" if r["reported_floor_V"] == 0.0
                    else "**%.2f V**" % r["reported_floor_V"])))
        return "\n".join(rows)
    _cs_md = _charging_safe_markdown()
    _cs_missing = [r_ for r_ in _env_docs if _cs_md not in _flat(r_)]
    # ---- D-798 / D798-02: the supervised-charging matrix, method and rule,
    # generated from ONE authority and required verbatim.
    _sup_md, _sup_method_md = supervised_charging_markdown(_cc_env)
    _sup_docs = _env_docs + ("docs/full-beta-v2/CURRENT_STATE.md",)
    _rst = _cc_env.get("supervised_charging_rule_text")
    for r_ in _sup_docs:
        _fl = _flat(r_)
        _fl_ws = re.sub(r"\s+", " ", _fl)
        if _sup_md not in _fl:
            _cs_missing.append("%s (the supervised-charging matrix)" % r_)
        if re.sub(r"\s+", " ", _sup_method_md) not in _fl_ws:
            _cs_missing.append("%s (the supervised-charging measurement "
                               "method)" % r_)
        if not _rst or _rst not in _fl_ws:
            _cs_missing.append("%s (the supervised-charging rule)" % r_)
    cell_net["the_charging_safe_envelope_is_generated_into_the_documents"] = \
        dict(documents=list(_env_docs), missing=_cs_missing, generated=_cs_md,
             supervised_documents=list(_sup_docs),
             supervised_matrix_generated=_sup_md,
             supervised_method_generated=_sup_method_md,
             supervised_rule_generated=_rst,
             ok=not _cs_missing,
             why="D-797 / D797-02: the charging-safe power is cell-"
                 "conditioned (about ILIM_min x VBAT: a reachable supplement "
                 "is absorbing), so a document may carry it only as this "
                 "generated table and its universal minimum")
    cell_net_ok = cell_net_ok and not _cs_missing
    # ---- D-799 / D799-01: OCV_lb is PROVED a lower bound on its domain,
    # and D-798's formula is refused on every Round-18 class.
    _ocv_pf = _cc_env["supervised_charging_method"]["proof"]
    cell_net["the_supervised_ocv_bound_is_a_true_lower_bound"] = dict(
        _ocv_pf,
        why="D-799 / D799-01 (Astra R18-01, Fable R18-01): OCV_lb must be "
            "mathematically true for every admitted record -- DMM and "
            "current-meter uncertainty, the current's sign convention, a "
            "shunt between J4 and the pack, polarization stored by an "
            "earlier, higher charge current, and outward rounding.  The "
            "corner adversary, a time-domain pack simulation and the five "
            "Round-18 witnesses find no record where it exceeds the true "
            "OCV; D-798's formula is refused on all five classes and each "
            "ablation of the new one is refused.")
    cell_net_ok = cell_net_ok and bool(_ocv_pf["ok"])
    cell_net["the_no_discharge_envelope_is_generated_into_the_documents"] = dict(
        documents=list(_env_docs), missing=_env_missing, generated=_env_md,
        ok=not _env_missing,
        why="R14-03: the no-discharge boundary is VBAT- and source-"
            "conditioned; a document may carry it only as this generated "
            "table, never as a scalar")
    cell_net_ok = cell_net_ok and not _env_missing

    # ======================================================================
    # D-795 / R14 D795-07.  B01-B14 AND FA01-FA10, IN-TREE.
    # ======================================================================
    _reg_path = ROOT / "docs/full-beta-v2/assembly/RELEASE_ACCEPTANCE_REGISTER.json"
    _reg = json.loads(_reg_path.read_text(encoding="utf-8"))
    _fa_plan = (FIRST_FIVE_ASSEMBLY.read_text(encoding="utf-8",
                                              errors="replace")
                if FIRST_FIVE_ASSEMBLY.exists() else "")
    _reg_problems = []
    if [b["id"] for b in _reg["manufacturer_cam"]] != [
            "B%02d" % i for i in range(1, 15)]:
        _reg_problems.append("the manufacturer register is not exactly "
                             "B01..B14")
    if [f_["id"] for f_ in _reg["first_article"]] != [
            "FA%02d" % i for i in range(1, 11)]:
        _reg_problems.append("the first-article register is not exactly "
                             "FA01..FA10")
    _step_rows = set(re.findall(r"^\| \*\*`?([^|*`]+?)`?\*\* \|", _fa_plan,
                                re.M))
    for f_ in _reg["first_article"]:
        for st_ in f_["steps"]:
            if st_ not in _step_rows:
                _reg_problems.append("%s names the step %r and the first-"
                                     "article plan has no such step row"
                                     % (f_["id"], st_))
    _claimed = {st_ for f_ in _reg["first_article"] for st_ in f_["steps"]}
    for st_ in sorted(x for x in _step_rows
                      if x.startswith("C-") or x.endswith("-01")):
        if st_ not in _claimed:
            _reg_problems.append("first-article step %r belongs to no FA "
                                 "group" % st_)

    def _register_markdown():
        rows = ["| group | what it validates | steps |", "|---|---|---|"]
        for f_ in _reg["first_article"]:
            rows.append("| **%s** | %s | %s |" % (
                f_["id"], f_["title"],
                ", ".join("`%s`" % x for x in f_["steps"])))
        rows += ["", "| id | manufacturer / CAM written acceptance | status |",
                 "|---|---|---|"]
        for b in _reg["manufacturer_cam"]:
            rows.append("| **%s** | %s | PENDING |" % (b["id"], b["item"]))
        return "\n".join(rows)
    _reg_md = _register_markdown()
    _reg_docs = ("docs/full-beta-v2/assembly/FIRST_FIVE_ASSEMBLY_PLAN.md",
                 "docs/full-beta-v2/AQROOT_DEMO_FAB_HANDOFF.md")
    for r_ in _reg_docs:
        if _reg_md not in _flat(r_):
            _reg_problems.append("%s does not carry the generated B/FA "
                                 "register" % r_)
    _notes = ROOT / "hardware/demo/fab/aqroot-Demo-FAB-NOTES.md"
    _notes_t = (_notes.read_text(encoding="utf-8", errors="replace")
                if _notes.exists() else "")
    for b in _reg["manufacturer_cam"]:
        if ("| **%s** | %s | PENDING |" % (b["id"], b["item"])) not in _notes_t:
            _reg_problems.append("the exported fab notes do not carry %s"
                                 % b["id"])
        if b["fab_note_token"].lower() not in _notes_t.lower():
            _reg_problems.append("the fab notes never mention %r, which %s "
                                 "asks the manufacturer to accept"
                                 % (b["fab_note_token"], b["id"]))
    cell_net["b01_b14_and_fa01_fa10_are_enumerated_in_tree"] = dict(
        register=str(_reg_path.relative_to(ROOT)), generated=_reg_md,
        problems=_reg_problems, ok=not _reg_problems)
    cell_net_ok = cell_net_ok and not _reg_problems

    # ======================================================================
    # D-795 / R14 D795-07.  FALSE ACTIVE CLAIMS, AND WRONG INSTRUCTIONS
    # INJECTED IN SCRATCH.
    #
    # "Correct DEVICE_SPEC claim that charger plug/unplug is stamped as a load
    # epoch; hardware cannot observe these edges."  And: "Append believable
    # wrong active instructions in scratch and require failure."  The scan
    # below is over whitespace-normalised SENTENCES of every normative
    # document, and a sentence carrying a supersession marker is exempt.
    # ======================================================================
    _FALSE_CLAIM_FENCE = ("SUPERSEDE", "supersede", "HISTORICAL",
                          "historical", "RETIRED", "retired", "WITHDRAWN",
                          "withdrawn", "D-794 said", "D-794 published",
                          "D-794 claimed", "was wrong")
    _FALSE_CLAIMS = (
        ("charger plug/unplug stamped as a load edge",
         re.compile(r"(?:plug\w*|unplug\w*).{0,80}?(?:stamp\w*|load[- ]edge|"
                    r"load epoch)", re.I),
         re.compile(r"cannot (?:see|observe)|not observ|unobservable|"
                    r"no VBUS-present|cannot stamp|is not stamped", re.I)),
        ("the accessory budgets called guaranteed",
         re.compile(r"(?:400 mA|300 mA|accessory budget\w*).{0,60}?"
                    r"\bguarantee[ds]?\b", re.I),
         re.compile(r"not (?:a )?guarantee|never guarantee|DECLARED AND "
                    r"QUALIFIED|no document may|may not call|rather than "
                    r"guarantee|instead of guarantee", re.I)),
        ("a universal no-discharge charge ceiling",
         re.compile(r"(?:battery (?:does|will) not discharge|no[- ]battery[- ]"
                    r"discharge|never discharges).{0,120}?\d\.\d{2,3}\s*W",
                    re.I),
         re.compile(r"at cell|VBAT|cell voltage|conditioned|envelope|table",
                    re.I)),
        ("a universal completion guarantee",
         re.compile(r"(?:charge|cycle)\w*.{0,60}?(?:completes?|terminates?)"
                    r".{0,80}?(?:every|all|any)\b.{0,40}?(?:source|cable|"
                    r"class)", re.I),
         re.compile(r"QUALIFICATION TARGET|estimate|not (?:a )?guarantee|"
                    r"C-PWR-CHARGE-02", re.I)),
        ("the sizing envelope instructed as a thermal test state",
         re.compile(r"C-THERM-01.{0,200}?(?:sub-GHz radio transmitting|ONE "
                    r"sub-GHz)", re.I),
         re.compile(r"not an admissible|sizing envelope|cannot reach|refuse",
                    re.I)),
        # ---- D-796 / Round-15 D796-05 + D796-06.  ROLE-BOUND FAMILIES. ----
        # Each binds a CLAIM to the role it is made in, so a number or a
        # phrase that is legitimate in one role cannot be used in another.
        ("a generic charging-source rule instead of the named adapter",
         re.compile(r"1\s*A or better|1\s*A USB (?:adapter|source|charger)|"
                    r"\bany (?:5 ?V )?USB(?:-C)? (?:source|adapter|charger|"
                    r"port)\b|USB 2\.0 (?:computer |host )?(?:port|host)?"
                    r".{0,40}?\b(?:is|are) (?:acceptable|sufficient|"
                    r"qualified|fine)\b", re.I),
         re.compile(r"\bOUTSIDE\b|\boutside the contract|\bnot\b|cannot|"
                    r"never", re.I)),
        ("a radio transmitting beside an accessory rail called admitted",
         re.compile(r"(?:(?:radio|transmit\w*|\bTX\b|sub-GHz|Wi-Fi)\W.{0,80}?"
                    r"(?:accessory|Community[- ]Port) rails?|(?:accessory|"
                    r"Community[- ]Port) rails?.{0,60}?(?:while|with|beside|"
                    r"alongside).{0,40}?(?:radio|transmit\w*|\bTX\b))"
                    r".{0,80}?\b(?:permitted|allowed|admitted|supported|"
                    r"coexist\w*)\b", re.I),
         re.compile(r"refus|\bnot\b|never|cannot|\bno accessory rail", re.I)),
        ("the full 400 + 300 mA pair called a permitted mode",
         re.compile(r"(?:400\s*mA\s*\+\s*300\s*mA|both (?:published )?"
                    r"(?:accessory )?budgets (?:at once|together|"
                    r"simultaneously)).{0,120}?\b(?:permitted|allowed|"
                    r"admitted|an operating mode|may be drawn)\b", re.I),
         re.compile(r"sizing|\bnot\b|refus|never|220\s*mA", re.I)),
        ("a completion power or ceiling",
         re.compile(r"(?:charge[- ]completion|full[- ]charge|completion)\s+"
                    r"(?:power|ceiling)\b.{0,40}?\d\.\d{2,3}\s*W", re.I),
         re.compile(r"no completion power|QUALIFICATION TARGET|not published",
                    re.I)),
        ("the 288 min qualification target called a datasheet guarantee",
         re.compile(r"288\s*min.{0,80}?\b(?:guarantee[ds]?|GUARANTEED|"
                    r"datasheet (?:limit|timeout))\b|\bguarantee[ds]?\b.{0,60}?"
                    r"288\s*min", re.I),
         re.compile(r"not (?:a )?(?:datasheet )?guarantee|TYP-only|"
                    r"engineering qualification target|not GUARANTEED", re.I)),
        ("STAT1 alone read as charge completion",
         re.compile(r"STAT1.{0,80}?\b(?:shows|indicates|signals|confirms|"
                    r"identif\w+|means|reports)\b.{0,40}?(?:complet\w*|"
                    r"terminat\w*|fully charged|full charge)", re.I),
         re.compile(r"cannot|\bnot\b|ambiguous|STAT2|inference|infer", re.I)),
        ("the archived EastRising module specification called unobtainable",
         re.compile(r"(?:EastRising|ER-TFT035IPS-6).{0,160}?(?:not "
                    r"obtainable|unobtainable|could not be obtained|is not "
                    r"archived|not available here)", re.I),
         re.compile(r"was wrong|withdrawn|false", re.I)),
        ("a no-discharge figure called independent of ambient or TREG",
         re.compile(r"no[- ]discharge.{0,160}?(?:independent of (?:the )?"
                    r"(?:ambient|TREG)|ambient[- ]independent|TREG[- ]"
                    r"independent|at any ambient)", re.I),
         re.compile(r"\bnot\b|never", re.I)),
        ("a supplement below the BUVLO trip",
         re.compile(r"supplement\w*.{0,80}?(?:at|below|under) (?:the )?"
                    r"(?:2\.85\s*V|VBUVLO|BUVLO|UVLO trip)", re.I),
         re.compile(r"cannot|\bnot\b|never|\bno supplement|collaps", re.I)),
        # D-797 / D797-07: the earlier-release set is GENERATED from the one
        # constant `CURRENT_RELEASE_ID`, not typed as `D-79[0-5]`.
        ("an earlier release called the current one",
         re.compile(r"\b(?:current|this) (?:release|review target|candidate)"
                    r"\W.{0,60}?\b(?:%s)\b" % "|".join(
                        "D-%03d" % n_ for n_ in range(
                            700, _d797_release_number(CURRENT_RELEASE_ID))),
                    re.I),
         re.compile(r"REJECTED|rejected|parent|%s" % re.escape(
             CURRENT_RELEASE_ID), re.I)),
        ("an outside-contract source figure used as a qualified one",
         re.compile(r"\b(?:qualified|acceptance|accept(?:ed|s)?)\b.{0,80}?"
                    r"(?:generic_typec_24awg_2m|unqualified_28awg_2m)", re.I),
         re.compile(r"OUTSIDE|outside the contract|\bnot\b|REPORTED|never",
                    re.I)),
    )

    _SYMMETRIC_CLAIMS = _D797_SYMMETRIC_CLAIMS

    def _false_claim_scan(text, where):
        found = []
        # A markdown heading carrying a supersession marker fences every line
        # under it up to the next heading at the same or a shallower level --
        # the same rule the stale-value scan applies.
        kept, fence_level = [], None
        for ln in text.splitlines():
            ln2 = re.sub(r"^\s*>\s?", "", ln)
            m_ = re.match(r"^(#{1,6})\s", ln2)
            if m_:
                lvl = len(m_.group(1))
                if fence_level is not None and lvl <= fence_level:
                    fence_level = None
                if fence_level is None and any(
                        t_ in ln2 for t_ in _FALSE_CLAIM_FENCE + (
                            "SUPERSEDED",)):
                    fence_level = lvl
            if fence_level is None:
                kept.append(ln2)
        # D-797 / D797-07: tables are rewritten as label/value pairs first.
        body = _d797_tabulate("\n".join(kept))
        for sent in re.split(r"(?<=[.!?])\s+|\n\s*\n", body):
            flat = re.sub(r"\s+", " ", sent)
            if any(tok in flat for tok in _FALSE_CLAIM_FENCE):
                continue
            for name, pat, neg in _FALSE_CLAIMS:
                if pat.search(flat) and not neg.search(flat):
                    found.append("%s: %s: %s" % (where, name, flat[:160]))
            for name, all_of, neg in _SYMMETRIC_CLAIMS:
                if _d797_cooccur(flat, all_of, neg):
                    hit = "%s: %s: %s" % (where, name, flat[:160])
                    if hit not in found:
                        found.append(hit)
        return found
    _fc_docs = ("docs/full-beta-v2/DEVICE_SPEC.md",
                "docs/full-beta-v2/AQROOT_DEMO_FAB_HANDOFF.md",
                "docs/full-beta-v2/CURRENT_STATE.md",
                "docs/full-beta-v2/assembly/FIRST_FIVE_ASSEMBLY_PLAN.md",
                "docs/full-beta-v2/assembly/BATTERY_HARNESS.json",
                "docs/full-beta-v2/assembly/OFF_BOARD_BOM.md",
                # D-796 / D796-05 item 8: the second manual traveler and the
                # acceptance register are operative documents too.
                "hardware/demo/fab/aqroot-Demo-ACC-3V3-REINFORCEMENT.json",
                "docs/full-beta-v2/assembly/RELEASE_ACCEPTANCE_REGISTER.json",
                "hardware/demo/fab/aqroot-Demo-FAB-NOTES.md",
                # D-800 / D800-KNOWN-02 (Astra R19-02): the manual travelers
                # are operative documents.  THT_LEAD_TRIM carried a 24 h
                # cure beside the harness record's 72 h hold for two
                # releases because no scan read it.
                "docs/full-beta-v2/assembly/THT_LEAD_TRIM.md",
                "docs/full-beta-v2/assembly/IR_LEAD_FORMING.md",
                "docs/full-beta-v2/assembly/FIRST_FIVE_POPULATION_MATRIX.md")
    _fc_found = []
    _fc_texts = {}
    for r_ in _fc_docs:
        f_ = ROOT / r_
        t_ = f_.read_text(encoding="utf-8", errors="replace") if f_.exists() \
            else ""
        _fc_texts[r_] = t_
        _fc_found += _false_claim_scan(t_, r_)
    _WRONG_INSTRUCTIONS = (
        # ---- D-796 / Round-15: the escaped classes, permanent -----------
        "Charge the first five from a 1 A or better USB source.",
        "Any USB-C adapter is acceptable for the first five.",
        "A USB 2.0 computer port is acceptable for charging.",
        "While a sub-GHz radio transmits, both accessory rails are "
        "permitted.",
        "The full 400 mA + 300 mA pair is a permitted operating mode.",
        "The charge-completion ceiling: 1.150 W.",
        "The 288 min charge timeout is a datasheet guarantee.",
        "STAT1 HIGH indicates that charging is complete.",
        "The EastRising module specification is not obtainable, so the "
        "panel draw is declared.",
        "The no-discharge table is independent of ambient and TREG.",
        "At 2.85 V the battery supplements SYS below the VBUVLO trip.",
        "The current review target is D-795.",
        "The acceptance figure is the generic_typec_24awg_2m row.",
        "Charging the device from a USB 2.0 computer port satisfies the "
        "adapter contract, and while plugged in the firmware stamps the "
        "charger unplug as a load edge.",
        "The 400 mA and 300 mA accessory budgets are guaranteed by TI.",
        "The battery does not discharge while charging below 3.600 W.",
        "A full charge completes inside the timer on every qualified source "
        "class at 1.150 W.",
        "For C-THERM-01 hold the display at full brightness with ONE sub-GHz "
        "radio transmitting and both accessory rails on.",
    )
    _injected_caught = {}
    for i_, w_ in enumerate(_WRONG_INSTRUCTIONS):
        caught = []
        for r_, t_ in _fc_texts.items():
            # Injected at the TOP, in current text: an instruction appended
            # under a fenced historical heading would be history, correctly.
            head, _, rest = t_.partition("\n")
            caught.append(bool(_false_claim_scan(
                head + "\n\n" + w_ + "\n\n" + rest, r_ + "+scratch")))
        _injected_caught["instruction_%d" % (i_ + 1)] = bool(all(caught))
    cell_net["no_normative_document_states_a_false_active_claim"] = dict(
        documents=list(_fc_docs), found=_fc_found,
        scratch_injections=list(_WRONG_INSTRUCTIONS),
        every_scratch_injection_is_caught_in_every_document=_injected_caught,
        ok=bool(not _fc_found and all(_injected_caught.values())))
    cell_net_ok = cell_net_ok and cell_net[
        "no_normative_document_states_a_false_active_claim"]["ok"]

    _fa_txt = (FIRST_FIVE_ASSEMBLY.read_text(encoding="utf-8", errors="replace")
               if FIRST_FIVE_ASSEMBLY.exists() else "")
    _fa_floors = {
        "retention_floor": df["retention_floor_gridded_V"],
        "enable_first_rail_floor": df["enable_first_rail_floor_gridded_V"],
        "enable_second_rail_floor": df["enable_second_rail_floor_gridded_V"],
    }
    # ======================================================================
    # D-794 / R13-06.  THE EXECUTABLE FIRST-ARTICLE SCENARIOS, MACHINE-BOUND.
    #
    # ROUND-13: "Extend semantic document scanning to ... executable
    # first-article scenarios" and "Fresh current model values differ;
    # obsolete scenarios are sometimes no longer permitted by D-793."
    #
    # BOTH HALVES WERE TRUE OF `C-THERM-01`.  It told a technician to hold
    # "both published accessory budgets, the display at full brightness and
    # ONE sub-GHz radio transmitting" and MEASURE against stated model values
    # -- and F12 says that state has NO OPERATING POINT at any attainable cell
    # voltage.  Half the acceptance was unexecutable, and the numbers beside
    # it (1.6520 A, 89.97 C, 53.43 C) were three derivations old.  The state a
    # technician can actually reach is the same modes at the DECLARED
    # SIMULTANEOUS PAIR, and its figures are emitted here so the procedure
    # moves with the model.
    # ======================================================================
    # D-795 / Round-14 D795-07.  C-THERM-01 HOLDS A STATE THE PRODUCT CAN BE
    # IN.
    #
    # ROUND-14: "FIRST_FIVE thermal procedure must use an actually admissible
    # production state OR explicitly define a bounded qualification-only
    # fixture/image.  Do not instruct an impossible TX+rails production
    # combination.  Rename any conductor/thermal 'published sustained
    # reference state' that is a sizing envelope but not an admissible user
    # state."
    #
    # D-794 re-based C-THERM-01 onto `display_subghz` at the declared pair --
    # and the production permission table REFUSES every accessory rail while
    # a sub-GHz transmitter is keyed.  A technician running the shipped image
    # cannot reach it.  `display_subghz` stays what it genuinely is, the
    # SUSTAINED SIZING ENVELOPE the conductors and the enclosure are sized
    # against; C-THERM-01 now holds the HEAVIEST state the rail-edge table
    # ADMITS with both rails at the declared pair.
    # ======================================================================
    _names = list(df["mode_names"])
    _rail2 = {r["mode_bits"]: r for r in df["rail_edge_table"]
              if r["rails"] == 2}

    def _bits(st_):
        return sum(1 << _names.index(m) for m in st_.get("modes", []))
    _admissible = [st_ for st_ in cell_net["states"]
                   if _rail2.get(_bits(st_), {}).get("permitted")
                   and st_["loads"]["both_rails_at_the_declared_pair"][
                       "supported"]]
    _ref_state = max(_admissible, key=lambda x: x["internal_3v3_A"],
                     default=None)
    cell_net["heaviest_admissible_thermal_state"] = dict(
        key=(_ref_state or {}).get("key"),
        admissible_states=[x["key"] for x in _admissible],
        sizing_envelope_state=cell_net["reference_state_key"],
        the_sizing_envelope_is_not_admissible=bool(
            not _rail2.get(_bits(next(
                x for x in cell_net["states"]
                if x["key"] == cell_net["reference_state_key"])), {}).get(
                    "permitted")),
        why="the production rail-edge table refuses every accessory rail "
            "while a radio transmits, so the sizing envelope is a CONDUCTOR "
            "AND ENCLOSURE sizing case, not a state a user or a technician "
            "can put the product in")
    _ref_pair = ((_ref_state or {}).get("loads", {})
                 .get("both_rails_at_the_declared_pair") or {})
    _ref_point = _ref_pair.get("at_the_lowest_supported_cell") or {}
    _pol_h = (ROOT / "Firmware/src/hw/aqroot_accessory_power_policy.h"
              ).read_text(encoding="utf-8")
    _us = int(re.search(r"kGaugeWorstCaseWindowUs == (\d+)u", _pol_h).group(1))
    _ms = int(re.search(r"kGaugePostLoadConversionMs == (\d+),", _pol_h)
              .group(1))
    _fa_scenarios = {
        # D-795 / Round-14: the steps the round asked to be EXECUTABLE.
        "C-THERM-01 admissible state": "`%s`" % (_ref_state or {}).get("key"),
        "C-GAUGE-EPOCH-01 exists": "**`C-GAUGE-EPOCH-01`**",
        "C-GAUGE-EPOCH-01 window": "**%d ms**" % _ms,
        "C-GAUGE-EPOCH-01 derivation": "**%.2f ms**" % (_us / 1000.0),
        "C-NFC-QUIESCE-01 exists": "**`C-NFC-QUIESCE-01`**",
        "C-NFC-TUNE-01 exists": "**`C-NFC-TUNE-01`**",
        "C-THERM-01 battery current": "**%.4f A**" % _ref_point.get("amps", 0.0),
        "C-THERM-01 junction": "**%.2f \u00b0C**"
                               % _ref_point.get("bq25185_junction_C", 0.0),
        "C-THERM-01 internal air": "**%.2f \u00b0C**"
                                   % _ref_point.get("internal_air_C", 0.0),
        "C-THERM-01 R_SYS": "**%.4f K/W**"
                            % ara.system_thermal_resistance_K_per_W(),
        # D-795 / R14-03: the step names its SOURCE, its AMBIENT and its
        # CELL-VOLTAGE conditions, and the figure it is measured against.
        "C-PWR-CHARGE-01 junction-safe power": (
            "**%.3f W**" % _cc["junction_safe_system_W"]),
        "C-PWR-CHARGE-01 junction": (
            "**%.3f \u00b0C**" % _cc["junction_at_the_junction_safe_power_C"]),
        "C-PWR-CHARGE-01 named source": "`%s`" % _cc["source_contract"][
            "named_adapter"]["part_number"],
        "C-PWR-CHARGE-01 ambient": "**%.0f \u00b0C** ambient" % (
            ara.AMBIENT_DESIGN_MAX_C),
        "C-PWR-CHARGE-01 cell conditions": "**%.3f V** and **%.3f V**" % (
            ara.REGIME_VBAT_GRID_V[0], ara.REGIME_VBAT_GRID_V[-1]),
        "C-CHG-01 VIN pin": "**%.4f V**"
                            % _cc["source_contract"]["min_vin_pin_V"],
        "C-CHG-01 input limit": "**%.1f A**"
                                % _cc["source_contract"][
                                    "required_source_current_A"],
        "C-PWR-CHARGE-02 exists": "**`C-PWR-CHARGE-02`**",
        "C-PWR-CHARGE-02 timer": "**%.0f min**" % _cc["completion"][
            "required_domain"]["timer_min"],
        "the reference state is a state the model supports": (
            "" if _ref_pair.get("supported") else
            "THE REFERENCE STATE HAS NO OPERATING POINT"),
    }
    # ---- D-797 / D797-02 + D797-06.  THE CHARGER STEPS STATE THE CORRECTED
    # ENVELOPE, THE LOW-CELL TRAP STEP AND THE COMPLETION CLASSES. ---------
    _by_cell_fa = {b["vbat_V"]: b for b in _cc["charging_safe_by_cell"]}
    _trap_cell = 3.4
    _therm_row = next((r for r in _cc["permitted_while_charging"]
                       if r["state"] == "display_audio"
                       and r["load"] == "acc_3v3_only"), None)
    _fa_scenarios.update({
        "C-PWR-CHARGE-01 charging-safe universal": "**%.2f W**"
            % _cc["charging_safe_universal_published_W"],
        "C-PWR-CHARGE-01 trap cell": "**%.3f V**" % _trap_cell,
        "C-PWR-CHARGE-01 trap cell charging-safe": "**%.2f W**"
            % _by_cell_fa[_trap_cell]["charging_safe_at_or_above_published_W"],
        "C-PWR-CHARGE-01 trap records STAT1": "`STAT1`",
        "C-PWR-CHARGE-01 trap verdict": "ESCALATE",
        "C-THERM-01 charging state power": "**%.3f W**"
            % ((_therm_row or {}).get("system_W") or 0.0),
        "C-THERM-01 charging cell condition": "**%.2f V**"
            % ((_therm_row or {}).get("charging_cell_floor_V") or 0.0),
    })
    for _tk, _tv in charge_end_plan_tokens().items():
        _fa_scenarios["C-PWR-CHARGE-02 %s" % _tk] = _tv
    for _cls in ("TERMINATED", "ACTIVE LIMITING", "FAULT / UNCLASSIFIED",
                 "TIMER EXPIRY"):
        _fa_scenarios["C-PWR-CHARGE-02 class %s" % _cls] = "**%s**" % _cls
    _fa_scenario_missing = sorted(
        k for k, t in _fa_scenarios.items() if t and t not in _fa_txt)
    if not _ref_pair.get("supported"):
        _fa_scenario_missing.append(
            "the reference state the procedure names is not supported by the "
            "model at all")
    cell_net["the_first_article_scenarios_are_executable_and_current"] = dict(
        document=str(FIRST_FIVE_ASSEMBLY.relative_to(ROOT)),
        required=_fa_scenarios, missing=_fa_scenario_missing,
        reference_state=cell_net["reference_state_key"],
        reference_state_load="both_rails_at_the_declared_pair",
        ok=not _fa_scenario_missing,
        why="R13-06.  A first-article step is EXECUTABLE or it is not a step. "
            "Every figure a technician is told to measure against is "
            "formatted from the computed value, and the state the step names "
            "must be one the model actually supports.")
    cell_net["the_first_article_scenarios_are_executable_and_current_ok"] = bool(
        not _fa_scenario_missing)
    cell_net_ok = cell_net_ok and not _fa_scenario_missing

    # ---- D-797 / D797-09.  EVERY FIRST-ARTICLE STEP STATES ITS OUTCOME. ---
    _fa_outcome_problems = judge_fa_outcomes(_fa_txt)
    _step_rows = fa_step_rows(_fa_txt)
    _fa_oc_ctrl = {}
    # (1) a step whose OUTCOME clause is removed; (2) a gate step whose worse
    # result is merely recorded; (3) a step that drops a re-run it owes; (4)
    # a new step with no declared semantics.
    _victim = "C-BAT-PATH-01"
    if _victim in _step_rows:
        _row_txt = _step_rows[_victim]
        _fa_oc_ctrl["an_outcome_clause_removed_is_refused"] = bool(
            judge_fa_outcomes(_fa_txt.replace(
                _row_txt, _row_txt.replace(FA_OUTCOME_MARKER, "Result:"))))
        _fa_oc_ctrl["a_worse_result_merely_recorded_is_refused"] = bool(
            judge_fa_outcomes(_fa_txt.replace(
                _row_txt, _row_txt.replace("otherwise RECORD + ESCALATE",
                                           "otherwise RECORD"))))
        _fa_oc_ctrl["a_dropped_re_run_is_refused"] = bool(
            judge_fa_outcomes(_fa_txt.replace(
                _row_txt, re.sub(r"\bF14\b", "F99", _row_txt))))
    _fa_oc_ctrl["an_undeclared_new_step_is_refused"] = bool(
        judge_fa_outcomes(_fa_txt + "\n| **`C-NEW-STEP-01`** | a new "
                          "measurement | x | y |\n"))
    # D-798 / D798-06: per-observation controls, on the real plan.
    _pc = _step_rows.get("C-PWR-CHARGE-01", "")
    if _pc:
        _pc_oc = _pc[_pc.index(FA_OUTCOME_MARKER):] \
            if FA_OUTCOME_MARKER in _pc else _pc
        _m_onset = re.search(r"\(r\d+\)[^()]*?no-discharge onset.*?"
                             r"(?=\(r\d+\)|$)", _pc_oc)
        if _m_onset:
            _bad_item = re.sub(r"unless.*$", "RECORD ONLY.",
                               _m_onset.group(0))
            _fa_oc_ctrl["d798_an_onset_below_the_boundary_merely_recorded"] = \
                bool(judge_fa_outcomes(_fa_txt.replace(
                    _m_onset.group(0), _bad_item)))
        _fa_oc_ctrl["d798_record_only_collapsed_into_one_sentence"] = bool(
            judge_fa_outcomes(_fa_txt.replace(
                _pc_oc, FA_RECORD_ITEM.sub("", _pc_oc))))
    _ge = _step_rows.get("C-GAUGE-EPOCH-01", "")
    if _ge:
        _fa_oc_ctrl["d798_a_cadence_violation_merely_recorded"] = bool(
            judge_fa_outcomes(_fa_txt.replace(
                _ge, re.sub(r"unless[^()]*", "", _ge))))
    # D-799 / D799-04A (Fable R18-02): the LAST (rN) item of a step may not
    # borrow a re-run token from the row's source / decision columns.
    for _st_last in ("C-PWR-CHARGE-01", "C-PWR-CHARGE-02"):
        _row_l = _step_rows.get(_st_last, "")
        _oc_l = (_row_l[_row_l.index(FA_OUTCOME_MARKER):].split("|")[0]
                 if FA_OUTCOME_MARKER in _row_l else "")
        _mk_l = list(FA_RECORD_ITEM.finditer(_oc_l))
        _ok_l = False
        if _mk_l and re.search(r"\bF12\b", _row_l[_row_l.index(
                FA_OUTCOME_MARKER) + len(_oc_l):]):
            _last_l = _oc_l[_mk_l[-1].start():]
            if re.search(r"\bF12\b", _last_l):
                _ok_l = bool(judge_fa_outcomes(_fa_txt.replace(
                    _last_l, re.sub(r"\bF12\b(?: and )?", "", _last_l), 1)))
        _fa_oc_ctrl["d799_%s_last_item_without_f12_is_refused"
                    % _st_last.lower().replace("-", "_")] = _ok_l
    _fa_oc_ctrl["d798_an_undeclared_observation_semantics_is_refused"] = bool(
        judge_fa_outcomes(_fa_txt, obs_decl=dict(
            FA_RECORD_OBSERVATIONS, **{"C-THERM-01": FA_RECORD_OBSERVATIONS[
                "C-THERM-01"] + (("an unwritten observation", "thermal",
                                  ("F12",)),)})))
    cell_net["every_first_article_step_states_its_outcome"] = dict(
        document=str(FIRST_FIVE_ASSEMBLY.relative_to(ROOT)),
        semantics={k: dict(kinds=list(v[0]), re_run=list(v[1]))
                   for k, v in FA_OUTCOME_SEMANTICS.items()},
        problems=_fa_outcome_problems, controls_refused=_fa_oc_ctrl,
        record_observations={k: [dict(observation=a, falsifies=b,
                                      re_run=list(c)) for a, b, c in v]
                             for k, v in FA_RECORD_OBSERVATIONS.items()},
        ok=bool(not _fa_outcome_problems and len(_fa_oc_ctrl) == 10
                and all(_fa_oc_ctrl.values())),
        why="D-797 / D797-09 (Fable R16-04): a step that replaces a DECLARED "
            "or DERIVED model input with a measurement must say what a WORSE "
            "measurement does -- PASS inside the bound, otherwise RECORD + "
            "ESCALATE and re-run the checks that consumed the input -- and a "
            "record-only step must say RECORD ONLY.")
    cell_net_ok = cell_net_ok and cell_net[
        "every_first_article_step_states_its_outcome"]["ok"]

    # ---- D-797 / D797-06.  THE COMPLETION CLASSIFIER, AND IT HAS TO BITE. -
    # D-798 / D798-03: records are time-stamped samples in one window.
    _ce = CHARGE_END_SPEC
    _vb = 4.18

    def _ce_rec(stat1="HIGH", t_end=3600.0, extra=None, **vals):
        base = dict(vbat_V=_vb, vsys_V=_ce["vsys_reg_V"],
                    vin_V=_vb + _ce["vindpm_track_V"] + 0.40, iin_A=0.20,
                    ibat_A=0.0, package_C=_ce["treg_low_C"] - 30.0)
        base.update(vals)
        smp = {k: dict(value=x, unit=_ce["units"][k], t_s=t_end - 5.0)
               for k, x in base.items()}
        smp["stat1"] = dict(value=stat1, t_s=t_end - 5.0)
        rec = dict(window=dict(start_s=t_end - 30.0, end_s=t_end),
                   samples=smp)
        rec.update(extra or {})
        return rec

    def _ce_with(rec, key, **fields):
        r = json.loads(json.dumps(rec))
        if fields.get("_drop"):
            r["samples"].pop(key)
        else:
            r["samples"][key].update(fields)
        return r

    _trans = dict(start_s=3600.0 - 15 * 60.0, end_s=3600.0 - 2.0,
                  ibat_max_A=0.002, vbat_peak_V=4.20,
                  vsys_min_V=_ce["vsys_reg_V"])
    _term = _ce_rec(extra=dict(batfet_off_transition=_trans, final=True))
    _quiet_ok = _ce_rec()
    _timer_extra = dict(elapsed_fast_charge_min=_ce["tmaxchg_typ_min"],
                        ts_in_window=True, ibat_discharge_max_A=0.0,
                        iset_ilim_pins_normal=True, latched_until_replug=True,
                        replug_restarts_charge=True)
    _timer_obs = _ce_rec(stat1="LOW", vin_V=5.1, vsys_V=4.0,
                         package_C=60.0, extra=_timer_extra)
    _nan = float("nan")
    _ce_cases = dict(
        # D-799: the D-798 fixture put a present VSYS inside the transition
        # BELOW the summary's own minimum -- a contradictory record the
        # D799-02 checks now refuse -- so the summary carries that minimum.
        taper_with_dppm_active_is_not_termination=(
            _ce_with(dict(_term, batfet_off_transition=dict(
                _trans, vsys_min_V=_vb + _ce["vdppm_V"])),
                "vsys_V", value=_vb + _ce["vdppm_V"]),
            "ACTIVE LIMITING"),
        # D-799 / D799-03: a 91 C package gives an 89..93 C junction
        # interval, inside TREG's band: TREG is neither excluded nor
        # established (still never TERMINATED).
        taper_with_treg_active_is_not_termination=(
            _ce_with(_term, "package_C", value=_ce["treg_low_C"] + 1.0),
            "INDETERMINATE / RECORD"),
        taper_at_the_input_limit_is_not_termination=(
            _ce_with(_term, "iin_A", value=_ce["ilim_min_A"]),
            "ACTIVE LIMITING"),
        taper_without_the_batfet_off_transition_is_unclassified=(
            _ce_rec(ibat_A=0.05, extra=dict(final=True)),
            "FAULT / UNCLASSIFIED"),
        loops_excluded_and_batfet_off_sustained_is_terminated=(
            _term, "TERMINATED"),
        stat1_low_alone_is_not_a_timer=(_ce_rec(stat1="LOW"),
                                        "FAULT / UNCLASSIFIED"),
        stat1_low_with_tshut_not_excluded_is_not_a_timer=(
            _ce_with(_timer_obs, "package_C",
                     value=_ce["tshut_falling_C"]),
            "FAULT / UNCLASSIFIED"),
        stat1_low_that_self_clears_is_not_a_timer=(
            dict(_timer_obs, latched_until_replug=False),
            "FAULT / UNCLASSIFIED"),
        stat1_low_early_in_the_charge_is_not_a_timer=(
            dict(_timer_obs, elapsed_fast_charge_min=60.0),
            "FAULT / UNCLASSIFIED"),
        stat1_low_with_every_other_cause_excluded_is_a_timer=(
            _timer_obs, "TIMER EXPIRY"),
        # ---- D-798 / D798-03 (Astra R17-03): an invalid record never
        # completes, and the transition must agree with the present. ------
        d798_missing_stat1_is_not_a_completion=(
            _ce_with(_term, "stat1", _drop=True), "FAULT / UNCLASSIFIED"),
        d798_unknown_stat1_is_not_a_completion=(
            _ce_with(_term, "stat1", value="UNKNOWN"),
            "FAULT / UNCLASSIFIED"),
        d798_unreadable_stat1_is_not_a_completion=(
            _ce_with(_term, "stat1", value=None), "FAULT / UNCLASSIFIED"),
        d798_nan_vin_is_not_a_completion=(
            _ce_with(_term, "vin_V", value=_nan), "FAULT / UNCLASSIFIED"),
        d798_nan_vsys_is_not_a_completion=(
            _ce_with(_term, "vsys_V", value=_nan), "FAULT / UNCLASSIFIED"),
        d798_nan_package_is_not_a_completion=(
            _ce_with(_term, "package_C", value=_nan),
            "FAULT / UNCLASSIFIED"),
        d798_nan_iin_is_not_a_completion=(
            _ce_with(_term, "iin_A", value=_nan), "FAULT / UNCLASSIFIED"),
        d798_nan_ibat_is_not_a_completion=(
            _ce_with(_term, "ibat_A", value=_nan), "FAULT / UNCLASSIFIED"),
        d798_infinite_vbat_is_not_a_completion=(
            _ce_with(_term, "vbat_V", value=float("inf")),
            "FAULT / UNCLASSIFIED"),
        d798_missing_vbat_is_not_a_completion=(
            _ce_with(_term, "vbat_V", _drop=True), "FAULT / UNCLASSIFIED"),
        d798_out_of_range_vin_is_not_a_completion=(
            _ce_with(_term, "vin_V", value=-5.0), "FAULT / UNCLASSIFIED"),
        d798_wrong_unit_is_not_a_completion=(
            _ce_with(_term, "iin_A", value=200.0, unit="mA"),
            "FAULT / UNCLASSIFIED"),
        d798_a_sample_outside_the_window_is_not_a_completion=(
            _ce_with(_term, "ibat_A", t_s=100.0), "FAULT / UNCLASSIFIED"),
        d798_a_stale_transition_summary_is_not_a_completion=(
            dict(_term, batfet_off_transition=dict(
                _trans, start_s=100.0, end_s=100.0 + 15 * 60.0)),
            "FAULT / UNCLASSIFIED"),
        d798_present_current_contradicting_the_summary=(
            _ce_with(_term, "ibat_A", value=0.500), "FAULT / UNCLASSIFIED"),
        d798_a_cv_band_miss_is_not_a_completion=(
            dict(_term, batfet_off_transition=dict(_trans,
                                                   vbat_peak_V=3.95)),
            "FAULT / UNCLASSIFIED"),
        d798_a_pack_below_the_recharge_threshold=(
            _ce_with(dict(_term, batfet_off_transition=dict(
                _trans, vbat_peak_V=4.19)), "vbat_V", value=3.70),
            "FAULT / UNCLASSIFIED"),
        d798_a_junction_supplied_instead_of_the_package=(
            dict(_term, tj_C=40.0), "FAULT / UNCLASSIFIED"),
        # D-799 / D799-03: an interval overlapping TREG is INDETERMINATE
        # (D-798 called this ACTIVE LIMITING off the upper end alone).
        d798_a_package_under_treg_whose_derived_junction_is_not=(
            _ce_with(_ce_with(_ce_with(_term, "package_C",
                                       value=_ce["treg_low_C"] - 3.0),
                              "iin_A", value=0.50),
                     "vin_V", value=_ce["vsys_reg_V"] + 0.40),
            "INDETERMINATE / RECORD"),
        d799_a_junction_wholly_above_the_treg_band_is_limiting=(
            _ce_with(_term, "package_C", value=_ce["treg_high_C"] + 3.0),
            "ACTIVE LIMITING"),
        d799_r18_03_89C_package_1W_is_indeterminate=(
            _ce_with(_ce_with(_ce_with(_term, "package_C", value=89.0),
                              "iin_A", value=0.50),
                     "vin_V", value=_ce["vsys_reg_V"] + 2.00),
            "INDETERMINATE / RECORD"),
        # ---- D-799 / D799-02 (Astra R18-02): cross-field physics --------
        d799_r18_02_sys_boosted_above_vin_and_the_pack=(
            _ce_with(_ce_with(_ce_with(_ce_with(
                _term, "vin_V", value=4.57), "vsys_V", value=4.65),
                "iin_A", value=0.30), "vbat_V", value=4.12),
            "FAULT / UNCLASSIFIED"),
        d799_r18_02_transition_minimum_above_its_own_sample=(
            _ce_with(dict(_term, batfet_off_transition=dict(
                _trans, vsys_min_V=5.50)), "vsys_V", value=4.41),
            "FAULT / UNCLASSIFIED"),
        d799_transition_minimum_above_a_sample_inside_regulation=(
            dict(_term, batfet_off_transition=dict(
                _trans, vsys_min_V=_ce["vsys_reg_V"] + 0.05)),
            "FAULT / UNCLASSIFIED"),
        d799_input_current_against_vin_below_vsys=(
            _ce_with(_ce_with(_term, "vin_V", value=4.40), "vsys_V",
                     value=4.48),
            "FAULT / UNCLASSIFIED"),
        d799_sys_above_the_vsys_reg_maximum=(
            _ce_with(_ce_with(_term, "vsys_V", value=4.64), "vin_V",
                     value=5.00),
            "FAULT / UNCLASSIFIED"),
        d799_charge_into_the_pack_from_a_lower_sys=(
            _ce_with(_ce_with(_ce_rec(ibat_A=0.30, vsys_V=4.05, vbat_V=4.18),
                              "iin_A", value=0.40), "vin_V", value=5.0),
            "FAULT / UNCLASSIFIED"),
        d799_charge_power_without_input_power=(
            _ce_with(_ce_rec(ibat_A=0.40, iin_A=0.0), "iin_A", value=0.0),
            "FAULT / UNCLASSIFIED"),
        d799_a_sample_above_the_transition_cv_peak=(
            _ce_with(dict(_term, batfet_off_transition=dict(
                _trans, vbat_peak_V=4.19)), "vbat_V", value=4.20),
            "FAULT / UNCLASSIFIED"),
        d799_a_negative_transition_current_maximum=(
            dict(_term, batfet_off_transition=dict(_trans, ibat_max_A=-0.01)),
            "FAULT / UNCLASSIFIED"),
        # nearby controls that must STILL classify
        d799_near_sys_at_the_vsys_reg_maximum_still_terminates=(
            _ce_with(_ce_with(_term, "vsys_V", value=_ce["vsys_reg_V"]
                              * (1.0 + _ce["vsys_reg_accuracy"])),
                     "vin_V", value=5.00),
            "TERMINATED"),
        d799_near_sample_at_the_transition_minimum_still_terminates=(
            dict(_term, batfet_off_transition=dict(
                _trans, vsys_min_V=_ce["vsys_reg_V"] - 0.02)),
            "TERMINATED"),
        d799_near_vin_just_above_vsys_still_terminates=(
            _ce_with(_term, "vin_V", value=_ce["vsys_reg_V"] + 0.26),
            "TERMINATED"),
        d799_near_sample_after_the_transition_is_not_judged_by_it=(
            _ce_with(dict(_term, batfet_off_transition=dict(
                _trans, end_s=3600.0 - 8.0)), "vsys_V",
                value=_ce["vsys_reg_V"] - 0.03),
            "TERMINATED"),
        d799_near_zero_current_within_the_offset_still_terminates=(
            _ce_with(_term, "ibat_A", value=-0.002), "TERMINATED"),
        # ---- D-800 / D800-KNOWN-01 (Astra R19-01): a signed IIN ---------
        # The Round-19 witness: VIN 5.00 V, VSYS 4.41 V, pack 4.18 V, IBAT
        # 0, STAT1 HIGH, a valid sustained transition -- and current OUT
        # of the device.  Wholly negative beyond +/-(5 mA + 2 %).
        d800_r19_01_iin_minus_40mA_is_not_a_completion=(
            _ce_with(_ce_with(_ce_with(dict(_term, batfet_off_transition=dict(
                _trans, vsys_min_V=4.41)), "vsys_V", value=4.41),
                "vin_V", value=5.00), "iin_A", value=-0.040),
            "FAULT / UNCLASSIFIED"),
        d800_r19_01_iin_minus_50mA_is_not_a_completion=(
            _ce_with(_ce_with(_ce_with(dict(_term, batfet_off_transition=dict(
                _trans, vsys_min_V=4.41)), "vsys_V", value=4.41),
                "vin_V", value=5.00), "iin_A", value=-0.050),
            "FAULT / UNCLASSIFIED"),
        d800_iin_minus_10mA_is_still_wholly_negative=(
            _ce_with(_term, "iin_A", value=-0.010), "FAULT / UNCLASSIFIED"),
        # nearby controls: an interval that INCLUDES zero is instrument
        # offset, and an ordinary positive input current still terminates.
        d800_near_iin_minus_5mA_within_the_offset_still_terminates=(
            _ce_with(_term, "iin_A", value=-0.005), "TERMINATED"),
        d800_near_iin_zero_still_terminates=(
            _ce_with(_term, "iin_A", value=0.0), "TERMINATED"),
        d800_near_iin_plus_3mA_still_terminates=(
            _ce_with(_term, "iin_A", value=0.003), "TERMINATED"),
        d800_near_iin_ordinary_positive_still_terminates=(
            _ce_with(_ce_with(_ce_with(dict(_term, batfet_off_transition=dict(
                _trans, vsys_min_V=4.41)), "vsys_V", value=4.41),
                "vin_V", value=5.00), "iin_A", value=0.120),
            "TERMINATED"),
        d798_a_non_finite_transition_field=(
            dict(_term, batfet_off_transition=dict(_trans,
                                                   ibat_max_A=_nan)),
            "FAULT / UNCLASSIFIED"),
        d798_a_transition_shorter_than_sustained=(
            dict(_term, batfet_off_transition=dict(
                _trans, start_s=3600.0 - 5 * 60.0)),
            "FAULT / UNCLASSIFIED"),
    )
    _ce_res = {k: dict(expected=v[1], got=classify_charge_end(v[0])[0])
               for k, v in _ce_cases.items()}
    cell_net["charge_completion_is_classified_conservatively"] = dict(
        cases=_ce_res, plan_tokens=charge_end_plan_tokens(),
        ok=bool(all(r["expected"] == r["got"] for r in _ce_res.values())),
        record_fields=list(CHARGE_END_SAMPLES),
        termination_region_V=[round(x, 4) for x in
                              charge_end_termination_region()],
        why="D-799 / D799-02 + D799-03 (Astra R18-02, R18-03): a record "
            "whose fields are each valid but TOGETHER impossible -- SYS "
            "boosted above VIN and the pack, input current against VIN < "
            "VSYS, SYS above VSYS_REG max, current flowing uphill, a "
            "transition whose extrema disagree with its own samples -- is "
            "FAULT / UNCLASSIFIED before any classification; the junction "
            "is an interval and an overlap with TREG is INDETERMINATE.  "
            "D-798 / D798-03 (Astra R17-03): a record with a missing, "
            "unknown, non-finite, out-of-unit, out-of-range or out-of-window "
            "observation, a stale or contradicted transition summary, a CV "
            "peak outside the VBATREG band or a pack under the recharge "
            "threshold is never TERMINATED, and the junction is derived from "
            "the package through PSI_JT.  "
            "D-797 / D797-06 (Astra R16-04): a taper near VBATREG is not "
            "termination while VINDPM, DPPM, ILIM or TREG may be active, and "
            "STAT1 LOW is every recoverable and latch-off fault, not the "
            "safety timer; TIMER EXPIRY needs every other cause excluded by "
            "measurement, the fault latched and a re-plug that restarts.")
    cell_net_ok = cell_net_ok and cell_net[
        "charge_completion_is_classified_conservatively"]["ok"]

    # ---- D-799 / D799-03 (Astra R18-03).  A FIRST-ARTICLE THERMAL TRIGGER
    # JUDGES THE JUNCTION INTERVAL, NEVER THE PACKAGE READING.
    _tl = _ce["treg_low_C"]
    _thr_cases = dict(
        r18_03_89C_package_1W_throttled_is_indeterminate=(
            (89.0, 1.0, True), "INDETERMINATE / RECORD"),
        a_cool_junction_that_throttles_is_escalated=(
            (70.0, 0.5, True), "RECORD + ESCALATE"),
        a_hot_junction_that_throttles_is_recorded=(
            (_ce["treg_high_C"] + 5.0, 0.2, True), "RECORD ONLY"),
        the_interval_top_exactly_at_treg_low_is_indeterminate=(
            (_tl - _ce["thermocouple_uncertainty_K"], 0.0, True),
            "INDETERMINATE / RECORD"),
        the_interval_top_just_under_treg_low_escalates=(
            (_tl - _ce["thermocouple_uncertainty_K"] - 0.1, 0.0, True),
            "RECORD + ESCALATE"),
        a_package_under_treg_with_heat_overlapping_is_indeterminate=(
            (_tl - 5.0, 0.4, True), "INDETERMINATE / RECORD"),
        no_throttle_is_record_only=((89.0, 1.0, False), "RECORD ONLY"))
    _thr_res = {k: dict(expected=e_, got=fa_throttle_observation(*a_)[0])
                for k, (a_, e_) in _thr_cases.items()}

    def _package_only(pkg, p_w, thr):     # the D-798 reading, control only
        return "RECORD + ESCALATE" if thr and pkg < _tl else "RECORD ONLY"
    _thr_ctrl = dict(
        the_package_only_trigger_escalates_the_89C_witness=bool(
            _package_only(89.0, 1.0, True) == "RECORD + ESCALATE"
            and fa_throttle_observation(89.0, 1.0, True)[0]
            != "RECORD + ESCALATE"),
        package_and_junction_are_separate_quantities=bool(
            fa_throttle_observation(89.0, 1.0, True)[2][1] > 89.0 + 1e-9))
    cell_net["first_article_thermal_triggers_judge_the_junction"] = dict(
        cases=_thr_res, controls=_thr_ctrl,
        treg_band_C=[_ce["treg_low_C"], _ce["treg_high_C"]],
        interval="package - %.1f K .. package + %.1f C/W x %.0f x P + %.1f K"
                 % (_ce["thermocouple_uncertainty_K"], _ce["psi_jt_C_per_W"],
                    _ce["psi_jt_declared_multiplier"],
                    _ce["thermocouple_uncertainty_K"]),
        ok=bool(all(r["expected"] == r["got"] for r in _thr_res.values())
                and all(_thr_ctrl.values())),
        why="D-799 / D799-03 (Astra R18-03): an 89 C package dissipating "
            "1 W has a junction interval of 87..101 C, which overlaps TREG's "
            "90..110 C band.  The (r3) trigger may escalate only when the "
            "WHOLE interval is below the band; an overlap is INDETERMINATE "
            "and recorded, never a contradiction of the controller.")
    cell_net_ok = cell_net_ok and cell_net[
        "first_article_thermal_triggers_judge_the_junction"]["ok"]

    # ---- D-794 / R13-05 + R13-06.  A MEASUREMENT OF RECORD THAT IS NOT A
    # STEP IS A PROMISE NOBODY KEEPS.
    #
    # Round-13 accepts the SECOND branch of R13-05 -- "explicitly classify/
    # qualify/derate the first-five capability" -- for the accessory limiter,
    # and the qualification it rests on is `C-ACC-ILIM-01`.  That token was
    # named eight times in the canonical model and existed NOWHERE as a step a
    # technician executes.  This programme has hit "a stated rule that never
    # runs" before; the general form of the fix is this clause.  Every
    # `measurement_of_record` any tagged primitive names must appear in the
    # first-article procedure.
    _mor = sorted({t for r in apm.registry()
                   for t in str(r.get("measurement_of_record") or "").replace(
                       " and ", ",").split(",")
                   if t.strip()})
    _mor = sorted({t.strip() for t in _mor if t.strip()})
    _mor_missing = sorted(t for t in _mor if t not in _fa_txt)
    cell_net["every_measurement_of_record_is_a_first_article_step"] = dict(
        document=str(FIRST_FIVE_ASSEMBLY.relative_to(ROOT)),
        tokens=_mor, missing=_mor_missing,
        ok=not _mor_missing,
        why="R13-05 is closed by QUALIFICATION rather than by a manufacturer "
            "guarantee, so the qualification has to exist.  A primitive that "
            "names a measurement of record is making a promise about a bench "
            "step; this clause requires the step.")
    cell_net["every_measurement_of_record_is_a_first_article_step_ok"] = bool(
        not _mor_missing)
    cell_net_ok = cell_net_ok and not _mor_missing

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
    # D-794 / R13-06 adds "former"/"FORMER".  Like "formerly", which was
    # already here, its only job in this prose is to mark a value as
    # no-longer-true -- "the former 3.135 V connector minimum is unreachable
    # at ANY current" is a supersession sentence by construction.  It is a
    # WORD, not a decision number and not the narrating "was", both of which
    # were tried at D-791 and both of which fenced sentences that were still
    # asserting current policy.
    _FA_FENCE = ("SUPERSEDE", "supersede", "HISTORICAL", "historical",
                 "RETIRED", "retired", "no longer", "formerly", "former",
                 "FORMER", "REPLACED", "replaced", "used to",
                 "until D-", "before D-")
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
    for _sent in _d796_sentences(_fa_flat):
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

    # ======================================================================
    # D-793 / R12-06.  A SEMANTIC STALE-VALUE SCAN OVER EVERY NORMATIVE
    # DOCUMENT, NOT A TOKEN-PRESENCE TEST.
    #
    # ROUND-12, IN ITS OWN WORDS: "Current normative docs still contain
    # multiple generations of accessory floors / 1.78k values ... Historical
    # values may remain only in clearly fenced historical/superseded sections.
    # Add semantic stale-value/documentation checks for all active operating
    # numbers, not only token presence."
    #
    # Every clause above this one asks whether the CURRENT value is PRESENT.
    # None of them asks whether a RETIRED one is also present, stated as if it
    # were current -- which is how `AQROOT_DEMO_FAB_HANDOFF.md` came to carry
    # three generations of accessory floor at D-792 and how the first-article
    # plan came to send a technician to a retired bench point at D-791.
    #
    # The instrument is R10-N04's, generalised: the number is bound to the
    # CLAIM rather than to the line, the unit of scan is a whitespace-
    # normalised SENTENCE (these documents hard-wrap), and a sentence carrying
    # an explicit supersession marker is exempt.  A decision number is NOT a
    # marker and neither is the word "was" -- both were tried at D-791 and both
    # silently exempted the worst sentence in the file.
    # ======================================================================
    _NORM_FENCE = _FA_FENCE
    _cc_ceiling = cell_net[
        "the_charge_regime_is_bounded_in_the_half_treg_cannot_reach"][
            "load_ceiling"]

    # THE PATTERNS ARE WIDENED FOR THIS SCAN, AND THE REASON IS A REAL MISS.
    #
    # R10-N04's own claim patterns use `[^.]{0,40}` to keep a number bound to
    # its claim WITHIN one clause.  Applied to a specification they miss the
    # thing they are looking for: "…ceiling of 4.063 W at 40 C ambient, with a
    # supervised external-ambient ceiling of 27.7 C at the heaviest permitted
    # charging state" contains a decimal point between the number and the word
    # that identifies it, so `[^.]` stops before it ever gets there.  The unit
    # of scan is ALREADY a sentence, so the character class is redundant as
    # well as harmful: these use `.` and a longer reach.
    _NORM_FLOOR_CLAIMS = (
        # D-795 / R14 D795-07: NUMBER-FIRST instructions -- "hold the pack at
        # 3.55 V to enable a rail" names no floor word at all.
        re.compile(r"(\d\.\d{2})\s*V\**.{0,50}?(?:to enable|before "
                   r"enabling|enables? (?:a|the|one|both|either) "
                   r"(?:first |second |accessory )?rail)", re.I),
        re.compile(r"(\d\.\d{2})\s*V\**.{0,60}?"
                   r"(?:single-rail|dual-rail|retention)(?:-rail)?\s*floor",
                   re.I),
        re.compile(r"(?:single-rail|dual-rail|retention)(?:-rail)?\s*floor"
                   r".{0,60}?(\d\.\d{2})\s*V", re.I),
        re.compile(r"(\d\.\d{2})\s*V\**\s*(?:single-rail|dual-rail)\b",
                   re.I),
        re.compile(r"(?:first-rail|second-rail)\s*(?:enable\s*)?"
                   r".{0,30}?(\d\.\d{2})\s*V", re.I),
    )

    _radios_h = ROOT / "Firmware/src/hw/aqroot_demo_bringup_app.h"
    _m_nfc = re.search(r"static_assert\(kNfcRevocationDeadlineMs\s*==\s*"
                       r"(\d+)",
                       _radios_h.read_text(encoding="utf-8", errors="replace")
                       if _radios_h.exists() else "")
    _NFC_REVOCATION_BOUND_MS = int(_m_nfc.group(1)) if _m_nfc else None

    def _norm_families():
        _pair = df["declared_simultaneous_pair"]
        _cc = _cc_ceiling
        _sp = env["p3v3_setpoint"]
        _sc = _cc["source_contract"]
        _hv = _heaviest
        _cr = cell_net[
            "the_charge_regime_is_bounded_in_the_half_treg_cannot_reach"]
        _fams = (
            dict(key="accessory_floor",
                 what="the enable and retention floors the firmware carries",
                 allowed={"%.2f" % df["retention_floor_gridded_V"],
                          "%.2f" % df["enable_first_rail_floor_gridded_V"],
                          "%.2f" % df["enable_second_rail_floor_gridded_V"]}
                 | {"%.2f" % v for r in df["rail_edge_table"] + df[
                     "mode_edge_table"] for v in (r["floor_gridded_V"],)
                    if v is not None},
                 patterns=_FA_CLAIMS + _NORM_FLOOR_CLAIMS),
            dict(key="charge_time_ceiling",
                 what="the charge-regime system-power figures",
                 # D-795 / R14-03: D-794's 3.600 W "regime ceiling" and
                 # 1.150 W "completion ceiling" are NOT in this set.  Either
                 # may appear only in a FENCED historical sentence.
                 # D-797: the junction-safe figures are READ, whatever shape
                 # the model publishes them in (a scalar or a per-cell table).
                 allowed={x_ for x_ in _d797_junction_safe_published(_cc)[
                     "values"] if len(x_.split(".")[-1]) == 3}
                         | {"%.3f" % _cc["universal_no_discharge_published_W"],
                          "%.3f" % _cc["universal_no_discharge_raw_W"],
                          "%.3f" % _cc["reference_state_system_W"]}
                         | {"%.3f" % e[k] for e in _cc["no_discharge_envelope"]
                            for k in ("no_discharge_published_W",
                                      "junction_published_W",
                                      "no_discharge_raw_W",
                                      "junction_raw_W",
                                      "input_carrying_published_W",
                                      "input_carrying_raw_W")
                            if e.get(k) is not None}
                         | {"%.3f" % r["system_W"] for r in
                            _cc["permitted_while_charging"]
                            + _cc["refused_while_charging"]},
                 patterns=(
                     re.compile(r"(\d\.\d{3})\s*W\**.{0,140}?charg", re.I),
                     re.compile(r"charg.{0,140}?(\d\.\d{3})\s*W", re.I))),
            dict(key="declared_pair",
                 what="the declared simultaneous accessory pair",
                 allowed={"%d" % round(_pair["acc_3v3_A"] * 1000),
                          "%d" % round(_pair["acc_5v_A"] * 1000),
                          "400", "300"},
                 patterns=(
                     re.compile(r"declared simultaneous pair.{0,80}?"
                                r"(\d{3})\s*mA", re.I),
                     re.compile(r"(\d{3})\s*mA\**\s*\+\s*\**"
                                r"\d{3}\s*mA.{0,80}?simultaneous", re.I))),
            dict(key="upstream_series",
                 what="the itemised cell-to-BAT_PROTECTED_P series resistance",
                 allowed={"%.3f" % (_up["fixed_series_max_ohm"] * 1000.0),
                          "%.3f" % (_up["harness_hot_aged_max_ohm"] * 1000.0)},
                 patterns=(
                     re.compile(r"(\d{2,3}\.\d{3})\s*m(?:\u03a9|Ohm)"
                                r".{0,100}?(?:fixed series|series path|series "
                                r"resistance|harness)", re.I),
                     re.compile(r"(?:fixed series|series path|series "
                                r"resistance|harness).{0,100}?"
                                r"(\d{2,3}\.\d{3})\s*m(?:\u03a9|Ohm)",
                                re.I))),
            # ---- D-794 / R13-06.  FIVE MORE FAMILIES. -------------------
            #
            # ROUND-13: "Extend semantic document scanning to delivery
            # voltage, thermal states, charge ceiling, mode/floor table,
            # source path, pair budget, backlight/current and executable
            # first-article scenarios."  The charge ceiling, the mode/floor
            # table and the pair budget are covered above and by the
            # generated-table clause; these are the rest.
            dict(key="delivery_voltage",
                 what="the Community Port delivered minimum and the rail's "
                      "own envelope",
                 allowed={"%.6f" % _sp["delivered_at_400mA_min_V"],
                          "%.6f" % _sp["delivered_at_400mA_fully_mated_V"],
                          "%.6f" % _sp["pwm_heavy_min_V"],
                          "%.6f" % _sp["worst_case_rail_max_V"],
                          "%.6f" % _sp["power_save_high_if_enabled_V"]}
                         | {"%.6f" % v for v in _sp["raw_pwm_V"]}
                         | {"%.3f" % _sp["published_connector_min_V"],
                            "%.2f" % _sp["published_connector_min_V"]},
                 patterns=(
                     re.compile(r"(\d\.\d{2,6})\s*V.{0,170}?"
                                r"(?:delivered|delivery|at the J5 mating|"
                                r"connector minimum|Community Port|"
                                r"fully mated)", re.I),
                     re.compile(r"(?:delivered|delivery|connector minimum|"
                                r"Community Port|fully mated).{0,170}?"
                                r"(\d\.\d{2,6})\s*V", re.I))),
            dict(key="limiter_programming",
                 what="the accessory limiter programming resistors",
                 allowed={"1.87", "2.43", "1870", "2430"},
                 patterns=(
                     re.compile(r"`?R97`?.{0,60}?(\d\.\d{2})\s*k", re.I),
                     re.compile(r"`?R101`?.{0,60}?(\d\.\d{2})\s*k", re.I),
                     re.compile(r"(\d\.\d{2})\s*k(?:\u03a9|Ohm).{0,40}?"
                                r"(?:limiter|ILIM|`?R97`?|`?R101`?)", re.I))),
            dict(key="limiter_band",
                 what="the declared ILIM band at the programmed resistors",
                 # ...and the CONVERTER figures the limiter corner feeds,
                 # because a sentence about the limiter legitimately quotes
                 # what `U12` then sees.  Each one is the model's own.
                 allowed={"%.4f" % apm.ilim_band_A(r)[k]
                          for r in apm.ILIM_PROGRAMMED_OHM.values()
                          for k in ("min_A", "typ_A", "max_A")}
                         | {"%.6f" % apm.ilim_band_A(r)[k]
                            for r in apm.ILIM_PROGRAMMED_OHM.values()
                            for k in ("min_A", "typ_A", "max_A")}
                         | {"%.4f" % v for k, v in
                            env["converter_capability_A"].items()
                            if isinstance(v, float)}
                         # D-796: a sentence about a LIMITER IN FAULT quotes
                         # the battery current it causes -- F6's own figure.
                         | {"%.4f" % v for v in env["modes_I_bat_A"].values()},
                 patterns=(
                     re.compile(r"(\d\.\d{4})\s*A.{0,60}?"
                                r"(?:ILIM|limiter|current limit)", re.I),
                     re.compile(r"(?:ILIM|limiter|current limit)"
                                r".{0,60}?(\d\.\d{4})\s*A", re.I))),
            dict(key="charge_thermal_state",
                 what="the charge-regime junction and supervised ambient",
                 # D-794 / R13-06: the allowed set is every junction the
                 # MODEL ITSELF reports -- the heaviest permitted state, the
                 # published ceiling, the reference state (which is over
                 # TSHUT and is reported precisely so the ceiling has a
                 # reason), and the junction at D-792's retired 4.063 W.  A
                 # derived number is legal; a TYPED one is not, and 225.8 --
                 # the reference-state junction before the R13-02 solver
                 # rebuild -- is exactly a typed one.
                 allowed={"%.1f" % _hv["junction_with_charge_folded_back_C"],
                          "%.1f" % _hv["charge_ambient_ceiling_C"],
                          "%.1f" % ara.PACKAGE_JUNCTION["tj_operating_max_C"],
                          "%.1f" % ara.AMBIENT_DESIGN_MAX_C,
                          "%.1f" % _cr["junction_with_charge_folded_back_C"],
                          "%.1f" % _cc["junction_at_the_junction_safe_power_C"],
                          "%.1f" % _cc[
                              "hottest_operating_junction_at_the_junction_"
                              "safe_power_C"],
                          "%.1f" % apm.BQ25185["treg_typ_C"],
                          "%.1f" % (apm.BQ25185["treg_typ_C"]
                                    + apm.BQ25185["treg_declared_band_K"]),
                          "%.1f" % (apm.BQ25185["treg_typ_C"]
                                    - apm.BQ25185["treg_declared_band_K"]),
                          "%.1f" % ara.PACKAGE_JUNCTION["tshut_rising_C"]}
                         | {"%.1f" % r[k] for r in
                            _cc["permitted_while_charging"]
                            + _cc["refused_while_charging"]
                            for k in ("junction_with_charge_folded_back_C",
                                      "charge_ambient_ceiling_C")},
                 patterns=(
                     re.compile(r"(\d{2,3}\.\d)\s*\u00b0?\s*C"
                                r".{0,120}?(?:junction|charging state|"
                                r"supervised ambient|charge regime)", re.I),
                     re.compile(r"(?:junction|supervised ambient|"
                                r"charge regime).{0,120}?"
                                r"(\d{2,3}\.\d)\s*\u00b0?\s*C", re.I))),
            dict(key="source_path",
                 what="the qualified adapter/cable contract at U11 IN",
                 allowed={"%.4f" % _sc["qualified_source_path_max_ohm"],
                          "%.4f" % _sc["min_vin_pin_V"],
                          "%.3f" % _sc["required_source_current_A"],
                          "%.2f" % _sc["required_source_current_A"]}
                         | {"%.4f" % c["path_ohm"] for c in _sc["classes"]}
                         | {"%.4f" % c["vin_pin_at_ilim_V"]
                            for c in _sc["classes"]},
                 patterns=(
                     re.compile(r"(\d\.\d{4})\s*(?:\u03a9|Ohm|ohm)"
                                r".{0,100}?(?:cable|adapter|source path|"
                                r"VIN pin|U11 IN)", re.I),
                     re.compile(r"(?:cable contract|qualified cable|"
                                r"source path|adapter).{0,100}?"
                                r"(\d\.\d{4})\s*(?:\u03a9|Ohm|ohm)",
                                re.I))),
            # ---- D-795 / R14 D795-07: RELEASE IDENTITY. ------------------
            # A board or MANIFEST digest stated as CURRENT must be the one on
            # disk.  D-794's 0db6f2c2... is legal only behind a fence.
            dict(key="release_identity",
                 what="a board or MANIFEST sha256 stated as the current one",
                 allowed={hashlib.sha256(rl.BOARD.read_bytes()).hexdigest(),
                          hashlib.sha256((ROOT / "hardware/demo/fab/"
                                          "MANIFEST.json").read_bytes())
                          .hexdigest()},
                 patterns=(
                     re.compile(r"(?:\bcurrent\b|this release|CURRENT|"
                                r"%s).{0,160}?\b([0-9a-f]{64})\b"
                                % re.escape(CURRENT_RELEASE_ID)),)),
            # ---- D-796 / Round-15 D796-06.  ROLE-BOUND NUMERIC FAMILIES. --
            dict(key="gauge_window",
                 what="the MAX17048 post-request gauge window",
                 allowed={"1300", "1293.75", "250", "258.75"},
                 patterns=(
                     re.compile(r"(\d{3,4}(?:\.\d{1,2})?)\s*ms\**\s+"
                                r"(?:post-load|post-request|post-edge|gauge|"
                                r"freshness|admission)[ -]?(?:\w+ )?window",
                                re.I),
                     re.compile(r"(?:post-load|post-request|post-edge|gauge|"
                                r"freshness|admission) window.{0,40}?"
                                r"(\d{3,4}(?:\.\d{1,2})?)\s*ms", re.I))),
            # D-796 / D796-05 item 4: the NFC OFF-confirmation revocation
            # deadline is the FIRMWARE's own static_assert'ed bound, read from
            # the header, never a typed number.
            dict(key="nfc_revocation",
                 what="the NFC liveness revocation deadline",
                 allowed={"%d" % _NFC_REVOCATION_BOUND_MS} if
                 _NFC_REVOCATION_BOUND_MS else set(),
                 patterns=(
                     re.compile(r"(?:revok\w*|revocation)\b.{0,80}?\bwithin\s*"
                                r"\**(\d+(?:\.\d+)?)\s*(?:ms|s)\b", re.I),)),
            dict(key="quiet_row",
                 what="the quiet (no optional mode) rail-edge row",
                 allowed={"%.2f" % r["floor_gridded_V"]
                          for r in df["rail_edge_table"]
                          if not r["modes"] and r["floor_gridded_V"]},
                 patterns=(
                     re.compile(r"\bquiet\b.{0,40}?\b(?:row|floor)\b\**\s*"
                                r"(?:is|of|at|=|:)?\s*\**(\d\.\d{2})\s*V",
                                re.I),
                     # the value FOLLOWS the row it names; a number before
                     # "quiet row" belongs to the preceding clause
                     )),
            dict(key="audio_row",
                 what="the audio rail-edge row",
                 allowed={"%.2f" % r["floor_gridded_V"]
                          for r in df["rail_edge_table"]
                          if r["modes"] == ["audio at the capped level"]
                          and r["floor_gridded_V"]},
                 patterns=(
                     re.compile(r"\baudio\b.{0,40}?\b(?:row|floor)\b\**\s*"
                                r"(?:is|of|at|=|:)?\s*\**(\d\.\d{2})\s*V",
                                re.I),
                     # the value FOLLOWS the row it names; a number before
                     # "audio row" belongs to the preceding clause
                     )),
            dict(key="harness_currents",
                 what="the battery-harness conforming and fault currents",
                 requires=re.compile(r"battery|harness|\bJ4\b|Micro-Lock|"
                                     r"\bpack\b", re.I),
                 allowed={"%.4f" % v for v in env["modes_I_bat_A"].values()}
                         | {"%.4f" % env["breaker"]["trip_min_A"],
                            "%.4f" % env["ibat_ocp_A"][2]},
                 patterns=(
                     re.compile(r"(\d\.\d{4})\s*A\**.{0,100}?(?:fault|"
                                r"conforming|excursion|overcurrent)", re.I),
                     re.compile(r"(?:fault|conforming|excursion|overcurrent)"
                                r".{0,100}?(\d\.\d{4})\s*A", re.I))),
            dict(key="qualified_no_discharge",
                 what="a no-discharge figure stated for the NAMED adapter",
                 allowed={"%.2f" % e["no_discharge_published_W"]
                          for e in _cc["no_discharge_envelope"]
                          if e["qualified"]}
                         | {"%.3f" % _cc["universal_no_discharge_published_W"],
                            "%.2f" % _cc["universal_no_discharge_published_W"],
                            "%.3f" % _cc["universal_no_discharge_raw_W"]},
                 patterns=(
                     re.compile(r"(?:named adapter|qualified|rpi15w_(?:high|"
                                r"low)).{0,100}?no[- ]discharge.{0,60}?"
                                r"(\d\.\d{2,3})\s*W", re.I),
                     re.compile(r"no[- ]discharge.{0,60}?(\d\.\d{2,3})\s*W"
                                r".{0,60}?(?:named adapter|qualified|"
                                r"rpi15w_(?:high|low))", re.I))),
            dict(key="p3v3_peak_envelope",
                 what="the internal +3V3 peak current envelope",
                 allowed={"%.6f" % apm.peak_A()},
                 patterns=(
                     re.compile(r"(\d\.\d{6})\s*A.{0,100}?peak envelope",
                                re.I),
                     re.compile(r"peak envelope.{0,100}?(\d\.\d{6})\s*A",
                                re.I),
                     re.compile(r"`?\+3V3`?\s*peak.{0,60}?"
                                r"(\d\.\d{6})\s*A", re.I))),
        )
        # D-797 / D797-07: the SYMMETRIC, table-aware role groups, fed the
        # same allowed sets as the D-796 families beside them and the
        # junction-safe power READ from the model's charge-ceiling dict.
        _by = {f_["key"]: f_ for f_ in _fams}
        return _fams + _d797_bound_families(
            quiet=_by["quiet_row"]["allowed"],
            audio=_by["audio_row"]["allowed"],
            retention={"%.2f" % df["retention_floor_gridded_V"]},
            floors=_by["accessory_floor"]["allowed"],
            gauge=_by["gauge_window"]["allowed"],
            junction=_d797_junction_safe_published(_cc),
            supervised={"%.2f" % _cc["supervised_charging_threshold_V"]}
            if _cc.get("supervised_charging_threshold_V") else None)

    NORMATIVE_DOCS = (
        "docs/full-beta-v2/DEVICE_SPEC.md",
        "docs/full-beta-v2/AQROOT_DEMO_FAB_HANDOFF.md",
        "docs/full-beta-v2/CURRENT_STATE.md",
        "docs/full-beta-v2/assembly/FIRST_FIVE_ASSEMBLY_PLAN.md",
        "hardware/demo/fab/aqroot-Demo-FAB-NOTES.md",
        # D-795 / R14 D795-07: the harness record's OPERATIVE acceptance
        # carried D-792's 132.282 / 249.782 mOhm limits for three releases
        # because nothing scanned it.
        "docs/full-beta-v2/assembly/BATTERY_HARNESS.json",
        "docs/full-beta-v2/assembly/OFF_BOARD_BOM.md",
        "hardware/demo/fab/aqroot-Demo-ACC-3V3-REINFORCEMENT.json",
        "docs/full-beta-v2/assembly/RELEASE_ACCEPTANCE_REGISTER.json",
        # D-800 / D800-KNOWN-02: the manual travelers (see `_fc_docs`).
        "docs/full-beta-v2/assembly/THT_LEAD_TRIM.md",
        "docs/full-beta-v2/assembly/IR_LEAD_FORMING.md",
        "docs/full-beta-v2/assembly/FIRST_FIVE_POPULATION_MATRIX.md",
        # D-801 / D801-01: the first-article test image's own procedure is
        # an operative document the technician reads at the bench.
        "docs/full-beta-v2/assembly/FAP01_FIRST_ARTICLE_IMAGE.md",
    )

    # A FENCE IS A BLOCK PROPERTY AS WELL AS A SENTENCE PROPERTY.
    #
    # R10-N04's instrument was per-SENTENCE, which is right for a procedure
    # written as a list of steps and wrong for a specification written as
    # SECTIONS: a whole `### D-792 ...  *(HISTORICAL -- superseded by ...)*`
    # block is marked no-longer-true by its own heading, and demanding the
    # word again in every sentence under it would turn a correct document into
    # a keyword-stuffed one.  A heading that carries a supersession marker
    # fences everything under it, up to the next heading at the same or a
    # shallower level.  A heading that does NOT is no shelter at all.
    _HEADING = re.compile(r"^\s*>*\s*(#{1,6})\s+(.*)$")

    def _norm_blocks(text):
        """[(fenced, block text)] -- the document split at markdown headings,
        including headings inside a blockquote, with each block tagged by
        whether its own heading (or any enclosing heading) is fenced."""
        blocks, stack, cur, cur_fenced = [], [], [], False
        for line in text.splitlines():
            m = _HEADING.match(line)
            if not m:
                cur.append(line)
                continue
            blocks.append((cur_fenced, "\n".join(cur)))
            level = len(m.group(1))
            fenced = any(f in m.group(2) for f in _NORM_FENCE)
            while stack and stack[-1][0] >= level:
                stack.pop()
            inherited = any(f for _, f in stack)
            stack.append((level, fenced))
            cur, cur_fenced = [line], bool(fenced or inherited)
        blocks.append((cur_fenced, "\n".join(cur)))
        return blocks

    def _norm_scan(text, families):
        found = []
        for fenced, block in _norm_blocks(text):
            if fenced:
                continue
            # D-797 / D797-07: tables become label/value pairs, paragraphs
            # split at blank lines, then sentences.
            for sent in _d797_units(block):
                if any(f in sent for f in _NORM_FENCE):
                    continue
                for fam in families:
                    if fam.get("kind") == "bound":
                        for role, tok in _d797_bound_scan(sent, fam):
                            found.append(dict(family=role, quoted=tok,
                                              what=fam["what"],
                                              sentence=sent.strip()[:220]))
                        continue
                    if fam.get("requires") is not None and \
                            not fam["requires"].search(sent):
                        continue
                    hits = sorted({t for rx in fam["patterns"]
                                   for t in rx.findall(sent)})
                    for tok in hits:
                        if tok not in fam["allowed"]:
                            found.append(dict(family=fam["key"], quoted=tok,
                                              what=fam["what"],
                                              sentence=sent.strip()[:220]))
        return found

    _norm_fams = _norm_families()
    _norm_rows, _norm_bad = [], []
    for _rel in NORMATIVE_DOCS:
        _f = ROOT / _rel
        _txt = (_f.read_text(encoding="utf-8", errors="replace")
                if _f.exists() else "")
        _hits = _norm_scan(_txt, _norm_fams) if _txt else []
        _norm_rows.append(dict(document=_rel, exists=bool(_txt),
                               stale_claims=_hits))
        if not _txt:
            _norm_bad.append("%s is missing" % _rel)
        _norm_bad.extend("%s: %s claims %r" % (_rel, h["family"], h["quoted"])
                         for h in _hits)
    # ======================================================================
    # D-794 / R13-05.  NO CURRENT DOCUMENT MAY CALL THE ACCESSORY BUDGETS
    # GUARANTEED.
    #
    # ROUND-13: "Published 400mA and 300mA lower-limit margins are thin and
    # must not be labeled guaranteed solely from interpolation.  Obtain
    # defensible primary/manufacturer support for the programmed points OR
    # explicitly classify/qualify/derate the first-five capability."
    #
    # The canonical model takes the second branch and tags the envelope
    # DECLARED with `C-ACC-ILIM-01` as its measurement of record.  A tag in a
    # model is not a product statement: DEVICE_SPEC carried a HEADING reading
    # "the number the hardware now GUARANTEES" and a sentence reading "the
    # 3.3 V rail still GUARANTEES 0.4058 A".  This clause is what keeps the
    # word out of the current text, in the same fenced-block instrument the
    # stale-value scan uses -- historical prose may still record that the
    # programme once said it.
    # The tokens are the ACCESSORY figures specifically.  The BQ25185's own
    # input current limit IS guaranteed -- 995/1050/1100 mA is a published
    # SLUSF65B Table 6-1 row at the programmed resistor -- so a sentence about
    # "the GUARANTEED-MINIMUM input current limit" is correct and must not be
    # caught.  What may not be called guaranteed is the TPS22950-Q1 envelope
    # at a resistor BETWEEN TI's four rows, and the budgets derived from it.
    _ILIM_TOKENS = (r"0\.4058|0\.3065|ACC_3V3_SW|ACC_5V_SW|"
                    r"accessory (?:budget|rail|limiter)|"
                    r"`?R97`?|`?R101`?")
    _ILIM_GUARANTEE = re.compile(
        r"(?:guarantee[sd]?|GUARANTEE[SD]?)"
        r"(?:(?!\bsupersed|\bretired\b|\bRETIRED\b).){0,120}?"
        r"(?:" + _ILIM_TOKENS + r")", re.I)
    _ILIM_GUARANTEE_2 = re.compile(
        r"(?:" + _ILIM_TOKENS + r")"
        r"(?:(?!\bsupersed|\bretired\b|\bRETIRED\b).){0,120}?"
        r"(?:guarantee[sd]?|GUARANTEE[SD]?)", re.I)
    _ilim_word_rows, _ilim_word_bad = [], []
    for _rel in NORMATIVE_DOCS:
        _f = ROOT / _rel
        _txt = (_f.read_text(encoding="utf-8", errors="replace")
                if _f.exists() else "")
        _hits = []
        for _fenced, _block in _norm_blocks(_txt):
            if _fenced:
                continue
            _flat = re.sub(r"\s+", " ", _block)
            for _sent in _d796_sentences(_flat):
                if any(f in _sent for f in _NORM_FENCE):
                    continue
                if _ILIM_GUARANTEE.search(_sent) or \
                        _ILIM_GUARANTEE_2.search(_sent):
                    _hits.append(_sent.strip()[:220])
        _ilim_word_rows.append(dict(document=_rel, claims=_hits))
        _ilim_word_bad.extend("%s: %s" % (_rel, h) for h in _hits)
    cell_net["no_current_document_calls_the_accessory_budget_guaranteed"] = dict(
        documents=_ilim_word_rows, problems=_ilim_word_bad,
        classification=apm.ilim_band_A(
            apm.ILIM_PROGRAMMED_OHM["ACC_3V3"])["classification"],
        measurement_of_record="C-ACC-ILIM-01",
        ok=not _ilim_word_bad,
        why="R13-05.  The programmed resistors are BETWEEN TI's four "
            "published ILIM accuracy rows, so the envelope is DECLARED AND "
            "QUALIFIED, not guaranteed.  A model tag does not reach a "
            "product-facing document; this clause does.")
    cell_net["no_current_document_calls_the_accessory_budget_guaranteed_ok"] = bool(
        not _ilim_word_bad)
    cell_net_ok = cell_net_ok and not _ilim_word_bad

    # ======================================================================
    # D-798 / D798-04 (Astra R17-04).  A PROBE INSTRUCTION MUST NAME COPPER
    # THAT IS CONNECTED.
    #
    # D-797's C-PWR-CHARGE-02 permitted "a temporary high-impedance probe on
    # TP7 (the STAT2 net)".  TP7 is on the /BQ25185_STAT2 NET NAME, but the
    # routing ledger puts it on the island {R128.2, TP7.1, U2.19}; U11.3 --
    # the charger pin that DRIVES STAT2 -- is the owner-approved open, alone
    # on the other island.  TP7 reads R128's pull-up and nothing else.  A
    # shared net name is not a shared conductor.  This clause resolves every
    # test point a normative sentence names to its COPPER island (the
    # ledger's groups for a net with open edges, the whole net otherwise) and
    # refuses the sentence if it also names a charger pin or status signal
    # that is not on that island -- unless the sentence states the
    # disconnection itself.
    # ======================================================================
    _PROBE_SIGNAL_DRIVER = {"STAT2": "U11.3", "STAT1": "U11.9"}
    # D-799 / D799-04B (Fable R18-03): every written form of a test point,
    # a driver pin and a status net is recognised -- `TP7`, `TP-7`, `TP 7`,
    # `test point 7`; `U11.3`, `U11 pin 3`, `pin 3 of U11`; `STAT2`,
    # `/BQ25185_STAT2` -- and a disconnection phrase exempts a claim only
    # when it names THAT test point and THAT pin / signal on either side of
    # it (the nearest mention before and after the phrase).  D-798 let any
    # "not connected" anywhere in the sentence waive every claim in it.
    _PROBE_TP = re.compile(r"\b(?:TP[ -]?|test[ -]?point\s+(?:TP[ -]?)?)"
                           r"(\d+)\b", re.I)
    _PROBE_PIN = re.compile(r"\b(U\d+)(?:\.|\s+pin\s+|[ -]pin[ -]?)(\d+)\b")
    _PROBE_PIN_OF = re.compile(r"\bpin\s+(\d+)\s+of\s+(U\d+)\b", re.I)
    _PROBE_SIGNAL = re.compile(r"(?:(?<![A-Za-z0-9])|(?<=_))(STAT[12])\b")
    _PROBE_DISCONNECT = re.compile(
        r"not (?:connected|joined|routed|wired) to|does not (?:observe|see|"
        r"reach|carry|connect)|cannot (?:observe|see|read)|is not on|"
        r"\b(?:separate|other|different) (?:copper )?island|no copper|"
        r"not the charger|never (?:observes|sees|reads)", re.I)

    def _probe_mentions(sent):
        """[(start, end, kind, contact)] in reading order."""
        out = [(m.start(), m.end(), "tp", "TP%s.1" % m.group(1))
               for m in _PROBE_TP.finditer(sent)]
        out += [(m.start(), m.end(), "pin", "%s.%s" % m.groups())
                for m in _PROBE_PIN.finditer(sent)]
        out += [(m.start(), m.end(), "pin", "%s.%s" % (m.group(2),
                                                      m.group(1)))
                for m in _PROBE_PIN_OF.finditer(sent)]
        out += [(m.start(), m.end(), "pin", _PROBE_SIGNAL_DRIVER[m.group(1)])
                for m in _PROBE_SIGNAL.finditer(sent)]
        return sorted(out)

    def _probe_disconnected(sent, ments, tp, claim):
        for d_ in _PROBE_DISCONNECT.finditer(sent):
            before = [x for x in ments if x[1] <= d_.start()]
            after = [x for x in ments if x[0] >= d_.end()]
            nb = before[-1][3] if before else None
            na = after[0][3] if after else None
            if {nb, na} == {tp, claim}:
                return True
            # "U11.3 and TP7 are on separate copper islands": a plural
            # phrase whose two nearest preceding mentions are the pair
            if re.search(r"islands\b", d_.group(0) + sent[d_.end():d_.end()
                                                          + 1]) is None \
                    and not sent[d_.end():].startswith("s"):
                continue
            if {x[3] for x in before[-2:]} == {tp, claim}:
                return True
        return False

    _islands_by_contact = {}
    for _n in ledger["nets"]:
        _groups = _n.get("groups")
        if _groups:
            for _g in _groups:
                _cs = {c.split("@")[0] for c in _g}
                for _c in _cs:
                    _islands_by_contact[_c] = _cs
    _net_contacts = {}
    for _c, _nn in nets_by_contact.items():
        _net_contacts.setdefault(_nn, set()).add(_c)

    def _island(contact):
        if contact in _islands_by_contact:
            return _islands_by_contact[contact]
        return _net_contacts.get(nets_by_contact.get(contact), {contact})

    def _probe_problems(text):
        found = []
        for _fenced_p, _block_p in _norm_blocks(text):
            if _fenced_p:
                continue
            for _sent_p in _d797_units(_block_p):
                if any(f in _sent_p for f in _NORM_FENCE):
                    continue
                ments = _probe_mentions(_sent_p)
                tps = sorted({x[3] for x in ments if x[2] == "tp"})
                claims = sorted({x[3] for x in ments if x[2] == "pin"})
                if not tps or not claims:
                    continue
                for tp in tps:
                    isl = _island(tp)
                    for c in claims:
                        if c in isl or _probe_disconnected(_sent_p, ments,
                                                           tp, c):
                            continue
                        found.append(dict(
                            test_point=tp[:-2], claims=c,
                            island=sorted(isl),
                            sentence=_sent_p.strip()[:220]))
        return found

    _probe_rows, _probe_bad = [], []
    for _rel in NORMATIVE_DOCS:
        _f = ROOT / _rel
        _txt = (_f.read_text(encoding="utf-8", errors="replace")
                if _f.exists() else "")
        _hits = _probe_problems(_txt) if _txt else []
        _probe_rows.append(dict(document=_rel, problems=_hits))
        _probe_bad.extend("%s: %s is not on %s's copper (island %s)"
                          % (_rel, h["claims"], h["test_point"], h["island"])
                          for h in _hits)
    _probe_ctrl = dict(
        d797_tp7_permitted_as_the_stat2_probe_is_refused=bool(_probe_problems(
            "A temporary high-impedance probe on `TP7` (the `STAT2` net) is "
            "PERMITTED as first-article test instrumentation only; it is not "
            "a product signal on this revision.")),
        tp7_named_as_the_charger_stat2_pin_is_refused=bool(_probe_problems(
            "Probe U11.3 STAT2 at TP7 during the charge.")),
        tp7_named_as_its_own_island_is_accepted=not _probe_problems(
            "TP7 reads R128's pull-up on the island shared with U2.19."),
        a_stated_disconnection_is_accepted=not _probe_problems(
            "TP7 is NOT connected to U11.3 STAT2: it is on a separate copper "
            "island."),
        d799_a_variant_stated_disconnection_is_accepted=not _probe_problems(
            "TP-7 is not connected to pin 3 of U11."))
    # D-799 / D799-04B: Fable C1 (every written form) and C2b (an unrelated
    # disconnection) as FULL-DOCUMENT injections into every normative
    # document -- each must add a finding to that document's own scan.
    _probe_inj = dict(
        c1_net_name=("Probe `/BQ25185_STAT2` at `TP7` during the charge to "
                     "read the charger state."),
        c1_pin_of=("Probe pin 3 of U11 at TP7 during the charge."),
        c1_tp_hyphen=("Probe STAT2 at TP-7 during the charge."),
        c1_tp_space=("Probe STAT2 at TP 7 during the charge."),
        c1_test_point_words=("Probe STAT2 at test point 7 during the "
                             "charge."),
        c1_u11_pin_words=("Clip the scope to TP7 to watch U11 pin 3."),
        c2b_unrelated_disconnection=(
            "Probe STAT2 at TP7 during the charge, noting that J9 is not "
            "connected to the shield."),
        c2b_other_test_point_disconnected=(
            "Probe STAT2 at TP7 and note that TP9 is not connected to "
            "U11.3."),
        c2b_other_pin_disconnected=(
            "Probe U11.3 at TP7 even though U2.20 is not connected to "
            "TP7."))
    _probe_inj_caught = {}
    for _nm_p, _w_p in _probe_inj.items():
        _all_p = True
        for _rel in NORMATIVE_DOCS:
            _f = ROOT / _rel
            if not _f.exists():
                continue
            _t0 = _f.read_text(encoding="utf-8", errors="replace")
            _h0, _, _r0 = _t0.partition("\n")
            if len(_probe_problems(_h0 + "\n\n" + _w_p + "\n\n" + _r0)) \
                    <= len(_probe_problems(_t0)):
                _all_p = False
        _probe_inj_caught[_nm_p] = _all_p
    _probe_ctrl.update({"d799_injection_" + k: v
                        for k, v in _probe_inj_caught.items()})
    _drv_ok = {sig: ("STAT%s" % sig[-1]) in str(nets_by_contact.get(pin, ""))
               for sig, pin in _PROBE_SIGNAL_DRIVER.items()}
    _probe_ctrl["d799_the_signal_driver_map_is_the_netlist"] = bool(
        all(_drv_ok.values()))
    cell_net["every_probe_instruction_names_connected_copper"] = dict(
        documents=_probe_rows, problems=_probe_bad,
        stat2_islands=[sorted(_island("TP7.1")), sorted(_island("U11.3"))],
        controls=_probe_ctrl,
        ok=bool(not _probe_bad and all(_probe_ctrl.values())
                and "U11.3" not in _island("TP7.1")),
        why="D-798 / D798-04 (Astra R17-04): TP7 is on /BQ25185_STAT2's "
            "NAME but not on U11.3's COPPER -- the routing ledger puts TP7, "
            "R128 and U2.19 on one island and the owner-approved open U11.3 "
            "alone on the other.  A probe instruction is judged on the "
            "island, never on the net name.")
    cell_net_ok = cell_net_ok and cell_net[
        "every_probe_instruction_names_connected_copper"]["ok"]

    cell_net["no_normative_document_states_a_retired_operating_value"] = dict(
        documents=_norm_rows,
        families={f["key"]: (
            dict(what=f["what"], allowed=sorted(f["allowed"]))
            if f.get("kind") != "bound" else
            dict(what=f["what"], kind="bound", reach=f["reach"],
                 roles={k: (sorted(a) if isinstance(a, set) else
                            ("predicate" if a is not None else "neutral"))
                        for k, rx, a in f["roles"]}))
                  for f in _norm_fams},
        current_release_id=CURRENT_RELEASE_ID,
        junction_safe_published=dict(
            values=sorted(_d797_junction_safe_published(_cc_ceiling)["values"]),
            universal=_d797_junction_safe_published(_cc_ceiling)["universal"]),
        fence_tokens=list(_NORM_FENCE),
        problems=_norm_bad,
        fencing="a markdown heading carrying a supersession marker fences "
                "every block under it up to the next heading at the same or a "
                "shallower level; inside an UNFENCED block the unit is the "
                "sentence, and a sentence carrying a marker is exempt.  A "
                "heading that does not carry one is no shelter at all.",
        ok=not _norm_bad,
        method="R12-06.  Every other documentation clause asks whether the "
               "CURRENT value is present; this one asks whether a RETIRED one "
               "is also present and stated as if it were current.  The number "
               "is bound to the CLAIM rather than to the line, the unit of "
               "scan is a whitespace-normalised sentence because these "
               "documents hard-wrap, and only an explicit supersession marker "
               "exempts a sentence -- a decision number does not, and neither "
               "does the word 'was'.")
    # ---- AND IT HAS TO BITE.  A scan with no negative control is not a
    # scan; this programme has been caught twice by a fence that exempted the
    # worst sentence in a file.  Three controls, over the REAL documents:
    #   1  strip the supersession markers from the D-792 historical heading in
    #      CURRENT_STATE and the whole block's retired figures must surface;
    #   2  put a retired floor back into an UNFENCED sentence and it must be
    #      caught;
    #   3  a document that is simply ABSENT must be refused, not skipped.
    _cs = ROOT / "docs/full-beta-v2/CURRENT_STATE.md"
    _cs_txt = (_cs.read_text(encoding="utf-8", errors="replace")
               if _cs.exists() else "")
    _defenced = []
    for _line in _cs_txt.splitlines():
        if _line.startswith("> # **D-792 "):
            for _f in _NORM_FENCE:
                _line = _line.replace(_f, "x" * len(_f))
        _defenced.append(_line)
    _ctrl_defenced = _norm_scan("\n".join(_defenced), _norm_fams)
    _ctrl_injected = _norm_scan(
        "The current single-rail floor is 3.55 V and the current charge-time "
        "ceiling is 4.063 W.", _norm_fams)
    # D-795 / R14-03: D-794's own two charge figures, stated as current.
    _ctrl_injected_d794 = _norm_scan(
        "While charging, the battery does not discharge below the 3.600 W "
        "charge-regime ceiling, and a charge completes below 1.150 W.",
        _norm_fams)
    _js_now = _d797_junction_safe_published(_cc_ceiling)
    _js_W = (_js_now["universal_W"] if _js_now["universal"] else
             float(sorted(x_ for x_ in _js_now["values"]
                          if len(x_.split(".")[-1]) == 3)[0]))
    _ctrl_current = _norm_scan(
        "The current single-rail floor is %.2f V and the current charge-time "
        "ceiling is %.3f W at a %.3f V cell."
        % (df["enable_first_rail_floor_gridded_V"], _js_W,
           ara.REGIME_VBAT_GRID_V[0]), _norm_fams)
    _ctrl_fenced = _norm_scan(
        "The RETIRED single-rail floor was 3.55 V and the retired charge-time "
        "ceiling was 4.063 W.", _norm_fams)
    # ---- D-796 / Round-15 D796-06: the escaped NUMERIC classes, each an
    # injected current sentence that must be caught by its own family.
    _d796_numeric_injections = dict(
        colon_split_completion_ceiling=(
            "charge_time_ceiling", "The completion ceiling while charging: "
            "1.150 W."),
        gauge_window_1000_ms=(
            "gauge_window", "Admissions read the gauge after a 1000 ms "
            "post-request window."),
        quiet_row_3_85=("quiet_row", "The quiet row floor is 3.85 V."),
        audio_row_3_80=("audio_row", "The audio row floor is 3.80 V."),
        nfc_one_second_deadline=(
            "nfc_revocation", "With a rail live, the OFF confirmation is "
            "revoked within 1 s."),
        stale_fault_current=(
            "harness_currents", "Record the battery-harness rise at the "
            "2.7536 A fault excursion."),
        outside_contract_figure_as_qualified=(
            "qualified_no_discharge", "On the named adapter the no-discharge "
            "figure is 2.20 W."),
    )
    _d796_numeric_caught = {}
    for _nm, (_fam, _txt) in _d796_numeric_injections.items():
        _hits = _norm_scan(_txt, _norm_fams)
        _d796_numeric_caught[_nm] = bool(any(h["family"] == _fam
                                             for h in _hits))
    cell_net["no_normative_document_states_a_retired_operating_value"][
        "controls_refused"] = dict(
        a_defenced_historical_heading_exposes_its_retired_figures=bool(
            len(_ctrl_defenced) >= 4),
        an_unfenced_retired_floor_or_ceiling_is_caught=bool(
            len(_ctrl_injected) >= 2),
        # 3.600 W is a legitimate ENVELOPE row at some cells, so the number
        # alone is not stale; the unconditioned CLAIM is, and the false-claim
        # scan is what refuses it.  Both instruments together must bite.
        d794s_retired_regime_and_completion_figures_are_caught=bool(
            len(_ctrl_injected_d794) + len(_false_claim_scan(
                "While charging, the battery does not discharge below the "
                "3.600 W charge-regime ceiling, and a charge completes below "
                "1.150 W on every qualified source class.", "control")) >= 2),
        the_current_values_are_not_flagged=bool(not _ctrl_current),
        an_explicitly_fenced_sentence_is_exempt=bool(not _ctrl_fenced),
        **{"d796_" + k: v for k, v in _d796_numeric_caught.items()})
    cell_net["no_normative_document_states_a_retired_operating_value"][
        "control_detail"] = dict(
        defenced_findings=_ctrl_defenced[:8],
        injected_findings=_ctrl_injected)
    cell_net["no_normative_document_states_a_retired_operating_value_ok"] = (
        bool(cell_net[
            "no_normative_document_states_a_retired_operating_value"]["ok"])
        and all(cell_net[
            "no_normative_document_states_a_retired_operating_value"][
                "controls_refused"].values()))
    cell_net_ok = cell_net_ok and cell_net[
        "no_normative_document_states_a_retired_operating_value_ok"]

    # ---- D-797 / D797-07.  THE ROUND-16 ESCAPES, PERMANENT. ---------------
    # "Known false claims still pass when value/role order is reversed, when
    # intervening clauses are inserted, or when represented as markdown
    # tables."  Each entry is a false CURRENT claim in one of those shapes,
    # for every binding D797-07 names.  The Round-16 inventory lists Fable's
    # escape IDs (D02d/e/f/g, D01b, D07b, D13c, D22, D24, D26) without their
    # strings, so each is reconstructed from its named SHAPE across the
    # binding it belongs to; Astra's two appended statements are the wrong
    # quiet floor and the 1000 ms window.  Every one must be caught -- by the
    # retired-value scan or the false-claim scan -- in EVERY operative
    # document, injected at the top of current text.
    _r16_injections = dict(
        astra_appended_wrong_quiet_floor=(
            "The quiet-state rail floor is now 3.85 V."),
        astra_appended_1000_ms_window=(
            "After every admission request the firmware waits 1000 ms for a "
            "fresh gauge conversion."),
        quiet_row_value_first=("3.85 V is the quiet row floor."),
        quiet_row_intervening_clause=(
            "The quiet row, read at the gauge with the display on and no "
            "accessory drawing, is 3.85 V."),
        quiet_row_table=("| state | floor |\n|---|---|\n"
                         "| quiet row | 3.85 V |"),
        audio_row_value_first=("3.80 V is the audio row floor."),
        audio_row_table=("| audio row | 3.80 V |"),
        window_value_first=("1000 ms is the post-request freshness window."),
        window_table=("| post-request freshness window | 1000 ms |"),
        charging_source_label_first=(
            "Acceptable charging source: any USB-C adapter."),
        charging_source_table=("| charging source | any 5 V USB adapter |"),
        tx_rail_label_first=(
            "Permitted: a sub-GHz transmission with an accessory rail live."),
        tx_rail_table=("| sub-GHz TX with an accessory rail live | "
                       "permitted |"),
        no_discharge_universal_value_first=(
            "0.900 W is independent of ambient and TREG."),
        completion_table=("| charge completion | guaranteed within "
                          "288 min |"),
        release_value_first=("D-796 is the current review target."),
        release_table=("| current review target | D-796 |"),
        buvlo_supplement_intervening=(
            "At 2.85 V, below the VBUVLO trip and with the adapter "
            "attached, the battery supplements SYS."),
        junction_safe_retired_universal_value_first=(
            "3.900 W is the junction-safe charging power at every cell."),
        junction_safe_retired_universal_table=(
            "| junction-safe charging power | 3.900 W |"),
        harness_fault_table=("| single-limiter fault current | 2.7536 A |"),
    )
    _r16_caught, _r16_missed = {}, []
    for _nm, _w in _r16_injections.items():
        _all = True
        for r_, t_ in _fc_texts.items():
            head, _, rest = t_.partition("\n")
            _inj = head + "\n\n" + _w + "\n\n" + rest
            _hit = bool(_false_claim_scan(_inj, r_ + "+r16")) or bool(
                len(_norm_scan(_inj, _norm_fams))
                > len(_norm_scan(t_, _norm_fams)))
            if not _hit:
                _all = False
                if len(_r16_missed) < 12:
                    _r16_missed.append("%s in %s" % (_nm, r_))
        _r16_caught[_nm] = _all
    cell_net["round16_document_escapes_are_caught"] = dict(
        injections=_r16_injections, caught=_r16_caught, missed=_r16_missed,
        ok=bool(all(_r16_caught.values())))
    cell_net_ok = cell_net_ok and cell_net[
        "round16_document_escapes_are_caught"]["ok"]

    # ---- D-798 / D798-07.  THE ROUND-17 SHAPES, PERMANENT. ---------------
    # The Round-17 inventory names Fable's Q7 / Q13 / Q14 without their
    # strings; each is reconstructed from the shape D798-07 names for it:
    #   Q7   a table whose FIRST column header carries the subject
    #        ("| STAT1 | meaning |" over "| HIGH | charge complete |");
    #   Q13  a contradictory second copy of the supervised threshold;
    #   Q14  a refused mode called permitted / allowed / admitted while
    #        charging.
    # Each, with its value-first, table and alternative-verb forms, is
    # injected at the top of current text in EVERY operative document.
    _thr_bad = "3.90"
    _r17_injections = dict(
        q7_stat1_header_table=("| STAT1 | meaning |\n|---|---|\n"
                               "| HIGH | charge complete |"),
        q7_stat1_header_table_terminated=(
            "| STAT1 | charger state |\n|---|---|\n"
            "| HIGH | terminated, fully charged |"),
        q13_second_threshold_copy=(
            "Supervised charging rule: with the adapter attached, a "
            "SUPERVISED combination may run only while OCV_lb is at or above "
            "%s V." % _thr_bad),
        q13_threshold_value_first=(
            "%s V is the supervised-charging threshold for OCV_lb." % _thr_bad),
        q13_threshold_table=("| supervised-charging threshold (OCV_lb) | "
                             "%s V |" % _thr_bad),
        q14_wifi_permitted_while_charging=(
            "While charging, Wi-Fi / BLE transmission is permitted."),
        q14_wifi_allowed_adapter_attached=(
            "Wi-Fi/BLE may run with the adapter attached."),
        q14_wifi_table=("| mode | while charging |\n|---|---|\n"
                        "| Wi-Fi / BLE TX | permitted |"),
        q14_audio_5v_admitted_while_charging=(
            "While charging, audio with the ACC_5V rail is admitted."),
        q14_audio_pair_supervised=(
            "Audio with the declared pair may run with the adapter attached "
            "as SUPERVISED."),
    )
    # D-799 / D799-04C (Fable R18-03): the EXACT Round-17 Q13 wording -- the
    # D-797 rule sentence carrying a stale 3.90 V -- and its close variants,
    # injected while the correct current rule is present in every document.
    _r17_injections.update(
        q13_exact_round17_wording=(
            SUPERVISED_RAIL_RESTRICTION % float(_thr_bad)),
        q13_exact_round17_wording_plain=(
            "Do not run an accessory rail with the adapter attached unless "
            "the pack is at or above %s V." % _thr_bad),
        q13_enable_variant=(
            "With the adapter attached, do not enable an accessory rail "
            "unless the pack is at or above %s V." % _thr_bad),
        q13_only_if_variant=(
            "Accessory rails may run with the adapter attached only if the "
            "pack is at or above %s V." % _thr_bad),
        q13_table_variant=(
            "| accessory rail with the adapter attached | pack at or above "
            "%s V |" % _thr_bad))
    _r17_caught, _r17_missed = {}, []
    for _nm, _w in _r17_injections.items():
        _all = True
        for r_, t_ in _fc_texts.items():
            head, _, rest = t_.partition("\n")
            _inj = head + "\n\n" + _w + "\n\n" + rest
            _hit = bool(_false_claim_scan(_inj, r_ + "+r17")) or bool(
                len(_norm_scan(_inj, _norm_fams))
                > len(_norm_scan(t_, _norm_fams)))
            if not _hit:
                _all = False
                if len(_r17_missed) < 12:
                    _r17_missed.append("%s in %s" % (_nm, r_))
        _r17_caught[_nm] = _all
    cell_net["round17_document_escapes_are_caught"] = dict(
        injections=_r17_injections, caught=_r17_caught, missed=_r17_missed,
        reconstruction=("Q7 = first-column header context; Q13 = second "
                        "supervised-threshold copy; Q14 = refused mode "
                        "called permitted while charging -- reconstructed "
                        "from the shapes D798-07 names, the inventory "
                        "carrying the IDs without their strings"),
        ok=bool(all(_r17_caught.values())))
    cell_net_ok = cell_net_ok and cell_net[
        "round17_document_escapes_are_caught"]["ok"]

    # ---- D-800 / Round-19.  THREE FINITE OPERATIVE FAMILIES, AND THE
    # ROUND-19 SHAPES, PERMANENT.
    #
    #   KNOWN-02 (Astra R19-02)  the J4 / DOWSIL 3145 bead has ONE qualified
    #            process release, the >= 72 h hold; a shorter hold stated
    #            before a pull, thermal, retention/closure or shipment step
    #            contradicts it.  Tack-free and handling (move, never load)
    #            are separate states and are not refused.
    #   KNOWN-03 (Astra R19-03, Opus R19-02)  the comparator cycle is a
    #            DISCHARGE interval then a NON-SUPPLYING interval; "IBAT
    #            alternating sign" or a charging pulse is the retired model.
    #   KNOWN-04 (Opus R19-01)  a package-top reading is not the junction:
    #            a rule comparing the package directly to the modelled
    #            junction, TREG, TSHUT or a junction-valued threshold, or
    #            reading a "measured junction", is refused; the junction is
    #            the interval derived FROM the package.
    #   KNOWN-08 (Opus R19-07)  the supervised condition in its other
    #            written forms (the bound family above) -- injected here.
    _D800_NEG = re.compile(r"\b(?:no|not|never|without|nor|nothing|none)\b"
                           r"[^.;|]{0,30}$",
                           re.I)
    _D800_FROM = re.compile(r"(?:derived |read |taken )?from (?:the |that "
                            r"step's |its |each |this |a )?(?:`?U11`? )?$",
                            re.I)
    _D800_WAVE = (
        re.compile(r"alternat\w*\s+(?:in\s+)?(?:sign|polarity)", re.I),
        re.compile(r"(?:IBAT|battery current|BAT current)[^.;|]{0,40}?"
                   r"alternat\w*", re.I),
        re.compile(r"(?:positive |sustained )?charg(?:e|ing)[- ]pulses?",
                   re.I),
        re.compile(r"(?:alternates?|swings?|toggles?) between (?:a )?"
                   r"(?:charge|charging)[^.;|]{0,30}?(?:and|,) (?:a )?"
                   r"(?:discharge|supplement)", re.I),
    )
    _D800_PKG = (
        re.compile(r"package(?:[- ]top)?(?: temperature| reading)?\s+(?:is\s+"
                   r")?(?:below|under|above|over|hotter than|cooler than|at "
                   r"or below|at or above|exceeds?|reaches|within)\s+(?:the\s+"
                   r")?(?:modell?ed\s+)?(?:junction|TREG|TSHUT|thermal "
                   r"regulation)", re.I),
        re.compile(r"package(?:[- ]top)?(?: temperature)?\s+(?:is\s+)?"
                   r"(?:hotter|cooler) than (?:the )?modell?ed", re.I),
        re.compile(r"package(?:[- ]top)? temperature\s+(?:is\s+)?(?:above|"
                   r"over|below|under|reaches|exceeds)\s+(?:90|110|125|150)"
                   r"\s*°C", re.I),
        re.compile(r"\bmeasured\s+(?:[\w`]+,?\s+){0,4}(?:and\s+)?junction"
                   r"\b", re.I),
        re.compile(r"package\s*/\s*TJ\b", re.I),
    )
    _D800_CURE_CTX = re.compile(r"cur(?:e|ed|ing)\b|\bhold\b|DOWSIL|\bRTV\b|"
                                r"adhesive|\bbead\b|strain relief", re.I)
    _D800_CURE = (
        re.compile(r"cur(?:e|ed|ing)\s+(?:for\s+)?(?:at least|≥|>=|a "
                   r"minimum of|min(?:imum)?\.?)?\s*\**\s*(\d+(?:\.\d+)?)"
                   r"\s*\**\s*(?:h|hours?|hrs?)\b", re.I),
        re.compile(r"(\d+(?:\.\d+)?)\s*\**\s*(?:h|hours?|hrs?)\b\s*\**"
                   r"(?:\s+(?:cure|hold))?[^.;|]{0,80}?\b(?:before|prior "
                   r"to)\b[^.;|]{0,60}?(?:enclosure|closure|retention|"
                   r"pull|thermal|shipment|\bship|load)", re.I),
        re.compile(r"(?:enclosure|closure|retention|pull[- ]test\w*|"
                   r"thermal test|shipment)[^.;|]{0,60}?(?:after|following|"
                   r"once)\s+(?:an? |the |at least |≥ )?\**\s*(\d+(?:\.\d+)?)"
                   r"\s*\**\s*(?:h|hours?|hrs?)\b", re.I),
        re.compile(r"(?:enclosure|closure|retention|pull|thermal test|"
                   r"shipment)[^.;|]{0,60}?(\d+(?:\.\d+)?)\s*\**\s*(?:h|"
                   r"hours?|hrs?)\b\s+after", re.I),
    )
    _D800_CURE_OK = re.compile(r"tack-free|handling|\bmoved?\b|window|"
                               r"Dow's|published|\btyp", re.I)
    _D800_QUALIFIED_H = 72.0

    def _d800_semantic_scan(text):
        found = []
        for fenced, block in _norm_blocks(text or ""):
            if fenced:
                continue
            for sent in _d797_units(block):
                if any(f in sent for f in _NORM_FENCE):
                    continue
                flat = re.sub(r"[*`]", "", sent)
                for rx in _D800_WAVE:
                    for m_ in rx.finditer(flat):
                        if _D800_NEG.search(flat[max(0, m_.start() - 40):
                                                 m_.start()]):
                            continue
                        found.append(("stale_comparator_waveform",
                                      flat[:200]))
                for rx in _D800_PKG:
                    for m_ in rx.finditer(flat):
                        pre = flat[max(0, m_.start() - 60):m_.start()]
                        if _D800_NEG.search(pre[-40:]) or \
                                _D800_FROM.search(pre):
                            continue
                        found.append(("package_read_as_junction",
                                      flat[:200]))
                if _D800_CURE_CTX.search(flat):
                    for rx in _D800_CURE:
                        for m_ in rx.finditer(flat):
                            h_ = float(m_.group(1))
                            if h_ >= _D800_QUALIFIED_H:
                                continue
                            near = flat[max(0, m_.start() - 60):
                                        m_.end() + 20]
                            if _D800_CURE_OK.search(near):
                                continue
                            found.append(("cure_hold_below_the_qualified_72h",
                                          flat[:200]))
        return sorted(set(found))

    _d800_rows, _d800_bad = [], []
    _d800_docs = tuple(dict.fromkeys(tuple(NORMATIVE_DOCS) + tuple(_fc_docs)))
    for _rel in _d800_docs:
        _f = ROOT / _rel
        _t = _f.read_text(encoding="utf-8", errors="replace") \
            if _f.exists() else ""
        _h = _d800_semantic_scan(_t)
        _d800_rows.append(dict(document=_rel, exists=bool(_t), findings=_h))
        if not _t:
            _d800_bad.append("%s is missing" % _rel)
        _d800_bad.extend("%s: %s: %s" % (_rel, k_, x_) for k_, x_ in _h)
    # the comparator-cycle wording is BOUND to the model: step 7 must carry
    # the model's two interval names.
    _cyc = apm.CHARGER_MODEL_ASSUMPTIONS["comparator_cycle"]["text"] \
        if hasattr(apm, "CHARGER_MODEL_ASSUMPTIONS") else ""
    _s7 = fa_step_rows(_fa_txt).get("C-PWR-CHARGE-01", "")
    _cyc_bound = dict(
        model_says_discharge_then_non_supplying=bool(
            re.search(r"DISCHARGE interval", _cyc)
            and re.search(r"NON-\s*SUPPLYING interval", _cyc)
            and re.search(r"no charging\s+pulse", _cyc)),
        step7_says_discharge_then_non_supplying=bool(
            re.search(r"DISCHARGE / supplement interval", _s7)
            and re.search(r"NON-SUPPLYING interval", _s7)
            and re.search(r"no charging pulse", _s7)),
        step7_escalates_an_unexpected_waveform=bool(
            re.search(r"RECORD the actual sign and waveform", _s7)
            and re.search(r"any other shape, is RECORD \+ ESCALATE", _s7)))
    # the IIN direction is defined in both charge steps
    _iin_def = dict(
        (k_, bool(re.search(r"`?IIN`? \(?(?:A, )?positive from the adapter "
                            r"INTO the device", fa_step_rows(_fa_txt).get(
                                k_, ""))))
        for k_ in ("C-PWR-CHARGE-01", "C-PWR-CHARGE-02"))
    _r19_injections = dict(
        r19_02_exact_d799_cure_sentence=(
            "Cure at least 24 h before enclosure retention/closure checks."),
        r19_02_cure_for_24_hours_before_closing=(
            "Allow the DOWSIL bead to cure for 24 hours before closing the "
            "enclosure."),
        r19_02_pull_test_after_48_h=(
            "The J4 strain relief may be pull-tested after a 48 h cure."),
        r19_02_retention_24_h_after=(
            "Enclosure retention checks may begin 24 h after the RTV bead is "
            "applied."),
        r19_03_exact_d799_waveform=(
            "At the onset the part CYCLES between the VBSUP1 entry and the "
            "VBSUP2 exit (`IBAT` alternating sign on a scope)."),
        r19_03_charging_pulse=(
            "Each comparator cycle ends in a short charging pulse into the "
            "cell."),
        r19_03_alternates_between_charge_and_supplement=(
            "On a scope IBAT alternates between charge and supplement."),
        r19_01_package_below_the_modelled_junction=(
            "PASS if every step holds a charge IBAT and the package below "
            "the modelled junction."),
        r19_01_package_hotter_than_modelled=(
            "A package hotter than modelled is RECORD + ESCALATE."),
        r19_01_measured_junction_list=(
            "PASS if the measured battery current, junction, internal air "
            "and R_SYS are at or below the modelled figures."),
        r19_01_package_reaches_treg=(
            "Raise the load until the package reaches thermal regulation."),
        r19_01_package_temperature_above_110=(
            "Stop the ascent at a package temperature above 110 °C."),
        r19_07_reads_at_least=(
            "With the adapter attached, run an accessory rail only if the "
            "pack reads at least 3.90 V."),
        r19_07_measures_at_least=(
            "Keep the accessory rails off while charging unless the cell "
            "measures at least 3.90 V."),
        r19_07_has_reached=(
            "With the adapter attached, enable an accessory only when the "
            "pack has reached 3.90 V."),
        r19_07_no_less_than=(
            "While charging, an accessory may run only if the pack reads no "
            "less than 3.90 V."),
        r19_07_or_more=(
            "With the adapter attached, run an accessory rail unless the "
            "battery voltage reads 3.90 V or more."),
        r19_07_symbol=(
            "While charging, run an accessory only if VBAT reads ≥ 3.90 V."),
        r19_07_provided=(
            "An accessory may stay on while charging provided the pack reads "
            "at least 3.90 V."),
    )
    _r19_caught, _r19_missed = {}, []
    for _nm, _w in _r19_injections.items():
        _all = True
        for r_ in _d800_docs:
            f_ = ROOT / r_
            t_ = f_.read_text(encoding="utf-8", errors="replace") \
                if f_.exists() else ""
            head, _, rest = t_.partition("\n")
            _inj = head + "\n\n" + _w + "\n\n" + rest
            _hit = bool(len(_d800_semantic_scan(_inj))
                        > len(_d800_semantic_scan(t_))) or bool(
                len(_norm_scan(_inj, _norm_fams))
                > len(_norm_scan(t_, _norm_fams))) or bool(
                len(_false_claim_scan(_inj, r_ + "+r19"))
                > len(_false_claim_scan(t_, r_ + "+r19")))
            if not _hit:
                _all = False
                if len(_r19_missed) < 12:
                    _r19_missed.append("%s in %s" % (_nm, r_))
        _r19_caught[_nm] = _all
    # near controls that must NOT be refused
    _r19_clean = dict(
        tack_free_then_handling=(
            "The board may be moved after a passed tack-free check and no "
            "earlier than 4 h; it is never loaded before the 72 h hold."),
        dow_window_quote=(
            "72 h is the top of Dow's own 24-72 h window."),
        junction_from_the_package=(
            "The junction interval derived from the package-top reading is "
            "at or below the modelled junction."),
        no_charging_pulse=("The model establishes no charging pulse."),
        correct_supervised=(
            "With the adapter attached, run an accessory rail only if the "
            "pack reads at least 4.10 V."))
    _r19_clean_res = {}
    for _nm, _w in _r19_clean.items():
        _r19_clean_res[_nm] = not _d800_semantic_scan(_w) and not \
            _norm_scan(_w, _norm_fams)
    cell_net["round19_operative_semantics"] = dict(
        documents=_d800_rows, problems=_d800_bad,
        comparator_cycle_bound_to_the_model=_cyc_bound,
        iin_direction_defined=_iin_def,
        injections=_r19_injections, caught=_r19_caught, missed=_r19_missed,
        clean_controls_pass=_r19_clean_res,
        qualified_cure_hold_h=_D800_QUALIFIED_H,
        ok=bool(not _d800_bad and all(_cyc_bound.values())
                and all(_iin_def.values()) and all(_r19_caught.values())
                and all(_r19_clean_res.values())),
        why="D-800 / Round-19: a 24 h cure beside the qualified 72 h hold "
            "(R19-02), IBAT 'alternating sign' beside a model with no "
            "charging pulse (R19-03), a package reading compared directly "
            "to the modelled junction (Opus R19-01) and the supervised "
            "condition written 'reads at least' (Opus R19-07) are refused "
            "in every operative document, the manual travelers included.")
    cell_net_ok = cell_net_ok and cell_net["round19_operative_semantics"]["ok"]

    # ---- D-801 / Round-20 D801-09 + D801-10 (Fable document campaign). ----
    #
    # The documents were CORRECT on D-800, but realistic contradiction forms
    # escaped every scan.  Not arbitrary NLP: each is a finite family bound to
    # a known normative role, quantity and context.
    #
    #   supervised  "once the pack has reached 3.90 V or more" (a bare
    #               `once` / `when` / `after` conditional) and "requires a
    #               pack voltage of no less than 3.90 V" (a requirement verb
    #               with the voltage as its object) -- any value other than
    #               the generated supervised threshold, in a charging context;
    #   cure        "one day", "24-hour", "twenty-four hours" -- the qualified
    #               J4 hold written in words or as a compound adjective is the
    #               same claim as "24 h";
    #   thermal     a PACKAGE temperature "at or below the modelled figures /
    #               values / limits" -- a package reading used as the junction
    #               or TREG acceptance surrogate -- unless it is the junction
    #               interval derived FROM the package;
    #   R_ins       a series ammeter / shunt / inline meter / insertion
    #               resistance "assumed" or "taken as" zero or negligible --
    #               only a clamp breaks no conductor.
    #   D801-09     `AQROOT_DEMO_FABRICATION_PACKAGE.md` carried D-616 status
    #               (FAB1-FAB8, 247 of 247) under an unfenced heading: it is
    #               now in the scan set and its D-616 authority must be fenced.
    _D801_SUP_THRESH = "%.2f" % _cc["supervised_charging_threshold_V"]
    _D801_SUP_COND = re.compile(
        r"(?:\b(?:once|when|whenever|after|if|while)\s+"
        + _D800_SUP_SUBJECT + r"\s+" + _D800_SUP_VERB + r"\s*"
        + _D800_SUP_CMP + r"|\b(?:requires?|needs?|demands?|calls? for|"
        r"is permitted (?:only )?(?:at|with)|is allowed (?:only )?(?:at|"
        r"with))\s+(?:an? |the )?(?:pack|cell|battery)(?: terminal)?"
        r"(?: voltage| OCV| open-circuit voltage)?\s+(?:of\s+)?"
        + _D800_SUP_CMP + r")\s*\**\s*(\d\.\d{1,2})\s*\**\s*V", re.I)
    _D801_ACCESSORY = re.compile(r"accessor\w*|Community[- ]Port|\brails?\b|"
                                 r"ACC_3V3|ACC_5V", re.I)
    _D801_CURE_WORDS = (
        (re.compile(r"\b(\d+(?:\.\d+)?)[- ]hours?\b", re.I),
         lambda m_: "%s h" % m_.group(1)),
        (re.compile(r"\btwenty[- ]four[- ]hours?\b", re.I), lambda m_: "24 h"),
        (re.compile(r"\bforty[- ]eight[- ]hours?\b", re.I), lambda m_: "48 h"),
        (re.compile(r"\b(?:one|a|1)[- ](?:full[- ])?days?\b", re.I),
         lambda m_: "24 h"),
        (re.compile(r"\b(?:two|2)[- ]days?\b", re.I), lambda m_: "48 h"),
        (re.compile(r"\bovernight\b", re.I), lambda m_: "12 h"),
        (re.compile(r"\b(\d+(?:\.\d+)?)\s*days?\b", re.I),
         lambda m_: "%g h" % (24.0 * float(m_.group(1)))),
    )
    _D801_CURE_EXTRA = (
        # "a 24 h cure", "a one-day hold" (after normalisation)
        re.compile(r"(\d+(?:\.\d+)?)\s*h\s+(?:cure|hold|curing)\b", re.I),
        re.compile(r"cur(?:e|ed|ing)\b[^.;|]{0,40}?(?:of|for|takes|is)\s+"
                   r"(?:only |about |at least )?(\d+(?:\.\d+)?)\s*h\b", re.I),
    )
    _D801_PKG_MODEL = re.compile(
        r"package(?:[- ]top)?(?: temperature| reading| thermogram)?[^.;|]"
        r"{0,40}?(?:at or below|below|under|within|not above|no hotter "
        r"than)\s+(?:the\s+)?modell?ed\s+(?:figures?|values?|numbers?|"
        r"limits?|results?|predictions?)", re.I)
    _D801_RINS = re.compile(
        r"(?:\bR_ins\b|insertion resistance|(?:series|inline|in-line)\s+"
        r"(?:DMM|ammeter|meter|shunt)|\bshunt\b|\bammeter\b|meter'?s? "
        r"(?:burden|resistance))[^.;|]{0,80}?(?:assumed|taken|treated|"
        r"regarded|considered|set|recorded|counted|entered)\s+(?:to be\s+|"
        r"as\s+)?(?:zero|nil|negligible|0(?:\.0+)?\s*(?:m?Ω|m?ohm|"
        r"m?Ohm)?(?![.\d]))", re.I)
    # ...and the same claim VERB-FIRST: "treat / take / assume the insertion
    # resistance as negligible".
    _D801_RINS_VF = re.compile(
        r"\b(?:treat|take|assume|consider|regard|set|count|enter|record)s?"
        r"\s+(?:the\s+|an?\s+|its\s+)?(?:R_ins|insertion resistance|"
        r"(?:series|inline|in-line)\s+(?:DMM|ammeter|meter|shunt)(?:'s)?"
        r"(?:\s+resistance)?|shunt(?:'s)?\s+resistance|ammeter(?:'s)?\s+"
        r"resistance|meter'?s? (?:burden|resistance))\s+(?:as|to be|=)\s+"
        r"(?:zero|nil|negligible|0(?:\.0+)?\s*(?:m?\u03a9|m?ohm|m?Ohm)?"
        r"(?![.\d]))", re.I)
    _D801_CLAMP = re.compile(r"\bclamp\b", re.I)
    _D801_FABPKG_STALE = re.compile(
        r"FAB1\s*[–-]\s*FAB8|247 of 247|LAND1\s*[–-]\s*LAND6|"
        r"GENERATED AND REVIEWED", re.I)

    def _d801_cure_norm(flat):
        for rx, fn in _D801_CURE_WORDS:
            flat = rx.sub(fn, flat)
        return flat

    def _d801_semantic_scan(text, doc=""):
        found = []
        for fenced, block in _norm_blocks(text or ""):
            if fenced:
                continue
            for sent in _d797_units(block):
                if any(f in sent for f in _NORM_FENCE):
                    continue
                flat = re.sub(r"[*`]", "", sent)
                # supervised: the value must be the generated threshold
                if re.search(_D800_SUP_CHARGING, flat, re.I) and \
                        _D801_ACCESSORY.search(flat):
                    for m_ in _D801_SUP_COND.finditer(flat):
                        if _D800_NEG.search(flat[max(0, m_.start() - 40):
                                                 m_.start()]):
                            continue
                        if "%.2f" % float(m_.group(1)) != _D801_SUP_THRESH:
                            found.append(("supervised_condition_other_value",
                                          flat[:200]))
                # cure: word / compound forms of a hold under 72 h
                if _D800_CURE_CTX.search(flat):
                    nflat = _d801_cure_norm(flat)
                    for rx in tuple(_D800_CURE) + _D801_CURE_EXTRA:
                        for m_ in rx.finditer(nflat):
                            h_ = float(m_.group(1))
                            if h_ >= _D800_QUALIFIED_H:
                                continue
                            near = nflat[max(0, m_.start() - 60):
                                         m_.end() + 20]
                            if _D800_CURE_OK.search(near):
                                continue
                            found.append(("cure_hold_below_the_qualified_72h",
                                          flat[:200]))
                # thermal: a package reading against the modelled figures
                for m_ in _D801_PKG_MODEL.finditer(flat):
                    pre = flat[max(0, m_.start() - 80):m_.start()]
                    if _D800_NEG.search(pre[-40:]) or _D800_FROM.search(pre) \
                            or re.search(r"junction interval (?:derived |"
                                         r"read |taken )?from\s*(?:the\s*)?$",
                                         pre, re.I):
                        continue
                    found.append(("package_against_the_modelled_figures",
                                  flat[:200]))
                # R_ins: an inserted meter path may never be assumed zero
                for m_ in tuple(_D801_RINS.finditer(flat)) + tuple(
                        _D801_RINS_VF.finditer(flat)):
                    seg = flat[max(0, m_.start() - 30):m_.end()]
                    if _D801_CLAMP.search(seg) or re.search(
                            r"\b(?:never|not|no)\b[^.;|]{0,40}$",
                            flat[max(0, m_.start() - 50):m_.end() - 8],
                            re.I):
                        continue
                    found.append(("series_meter_resistance_assumed_zero",
                                  flat[:200]))
                if doc.endswith("AQROOT_DEMO_FABRICATION_PACKAGE.md") and \
                        _D801_FABPKG_STALE.search(flat):
                    found.append(("d616_fabrication_package_status_unfenced",
                                  flat[:200]))
        return sorted(set(found))

    _D801_FABPKG = "docs/full-beta-v2/AQROOT_DEMO_FABRICATION_PACKAGE.md"
    _d801_docs = tuple(dict.fromkeys(tuple(_d800_docs) + (_D801_FABPKG,)))
    _d801_rows, _d801_bad = [], []
    for _rel in _d801_docs:
        _f = ROOT / _rel
        _t = _f.read_text(encoding="utf-8", errors="replace") \
            if _f.exists() else ""
        _h = _d801_semantic_scan(_t, _rel)
        _d801_rows.append(dict(document=_rel, exists=bool(_t), findings=_h))
        if not _t:
            _d801_bad.append("%s is missing" % _rel)
        _d801_bad.extend("%s: %s: %s" % (_rel, k_, x_) for k_, x_ in _h)
    # D801-09: the whole document is fenced by its own title
    _fp_txt = (ROOT / _D801_FABPKG).read_text(encoding="utf-8",
                                              errors="replace") \
        if (ROOT / _D801_FABPKG).exists() else ""
    _fp_title = next((l_ for l_ in _fp_txt.splitlines()
                      if l_.startswith("# ")), "")
    _fp_fenced = bool(_fp_title and any(f in _fp_title for f in _NORM_FENCE))
    if not _fp_fenced:
        _d801_bad.append("%s: its title does not fence the D-616 document "
                         "as HISTORICAL / SUPERSEDED" % _D801_FABPKG)
    _fp_unfenced = "\n".join(
        [re.sub(r"^# .*$", "# AQROOT Demo — Fabrication Package",
                _fp_txt.splitlines()[0])] + _fp_txt.splitlines()[1:]) \
        if _fp_txt else ""

    def _d801_hit(nm, w):
        """An injection is caught if ANY operative scan grows on EVERY doc."""
        missed = []
        for r_ in _d801_docs:
            f_ = ROOT / r_
            t_ = f_.read_text(encoding="utf-8", errors="replace") \
                if f_.exists() else ""
            head, _, rest = t_.partition("\n")
            if r_ == _D801_FABPKG:
                # the fenced document shelters everything under its title;
                # inject under a fresh, unfenced top-level heading instead
                _inj = t_ + "\n\n# Current procedure\n\n" + w + "\n"
            else:
                _inj = head + "\n\n" + w + "\n\n" + rest
            grew = bool(len(_d801_semantic_scan(_inj, r_))
                        > len(_d801_semantic_scan(t_, r_))) or bool(
                len(_d800_semantic_scan(_inj))
                > len(_d800_semantic_scan(t_))) or bool(
                len(_norm_scan(_inj, _norm_fams))
                > len(_norm_scan(t_, _norm_fams)))
            if not grew:
                missed.append("%s in %s" % (nm, r_))
        return missed

    _r20_injections = dict(
        r20_supervised_once_or_more=(
            "With the adapter attached, run an accessory rail once the pack "
            "has reached 3.90 V or more."),
        r20_supervised_requires_no_less_than=(
            "Running an accessory rail while charging requires a pack voltage "
            "of no less than 3.90 V."),
        r20_supervised_when_reads=(
            "While charging, enable an accessory rail when the pack reads "
            "3.95 V."),
        r20_cure_one_day=(
            "Allow the J4 strain-relief bead one day to cure before the pull "
            "test."),
        r20_cure_24_hour=(
            "After a 24-hour cure the enclosure retention check may begin."),
        r20_cure_twenty_four_hours=(
            "Let the DOWSIL bead cure for twenty-four hours before closing "
            "the enclosure."),
        r20_package_at_or_below_the_modelled_figures=(
            "PASS if the BQ25185 package temperature is at or below the "
            "modelled figures."),
        r20_package_within_the_modelled_values=(
            "The package-top reading must stay within the modelled values "
            "for TREG acceptance."),
        r20_rins_series_ammeter_assumed_zero=(
            "The series ammeter's resistance may be assumed zero when "
            "computing OCV_lb."),
        r20_rins_shunt_taken_as_0=(
            "R_ins for an inline shunt is taken as 0 mOhm."),
        r20_rins_negligible=(
            "Treat the insertion resistance as negligible for OCV_lb."),
        r20_rins_assume_the_shunt_zero=(
            "Assume the shunt resistance to be zero when the pack is on "
            "charge."),
    )
    _r20_caught, _r20_missed = {}, []
    for _nm, _w in _r20_injections.items():
        _m = _d801_hit(_nm, _w)
        _r20_caught[_nm] = not _m
        _r20_missed.extend(_m[:3])
    # WITNESS REPRODUCTION: the same injections against the D-800 scanners
    # alone.  Each Round-20 escape must have been MISSED there (the witness)
    # and caught by the D-801 family (the fix).
    _r20_witness = {}
    for _nm, _w in _r20_injections.items():
        _wt = "# t\n\n" + _w + "\n"
        _r20_witness[_nm] = dict(
            missed_by_the_d800_scanners=bool(
                not _d800_semantic_scan(_wt) and not _norm_scan(
                    _wt, _norm_fams)),
            caught_by_d801=bool(_d801_semantic_scan(_wt)))
    _r20_clean = dict(
        correct_supervised_once=(
            "With the adapter attached, run an accessory rail only once the "
            "pack has reached %s V or more." % _D801_SUP_THRESH),
        correct_supervised_requires=(
            "Running an accessory rail while charging requires a pack "
            "voltage of no less than %s V." % _D801_SUP_THRESH),
        accessory_floor_not_charging=(
            "The firmware refuses an accessory rail when the pack reads "
            "3.50 V."),
        qualified_hold_three_days=(
            "The J4 bead is released for pull tests after three days, the "
            "qualified 72 h hold."),
        handling_after_a_day=(
            "The board may be moved (handling only) after one day; nothing is "
            "loaded before the 72 h hold."),
        junction_interval_from_the_package=(
            "PASS if the junction interval derived from the package "
            "temperature is at or below the modelled figures."),
        clamp_rins_zero=(
            "With a DC clamp meter around one pack lead R_ins is taken as 0."),
        series_never_zero=(
            "A series meter's insertion resistance is never assumed zero."),
    )
    _r20_clean_res = {
        _nm: not _d801_semantic_scan("# t\n\n" + _w + "\n")
        for _nm, _w in _r20_clean.items()}
    # D801-09 controls: an unfenced title must be refused, a fenced one not
    _fp_controls = dict(
        d801_09a_the_document_title_is_fenced=_fp_fenced,
        d801_09b_unfencing_the_title_exposes_the_d616_status=bool(
            _fp_unfenced and _d801_semantic_scan(_fp_unfenced, _D801_FABPKG)),
        d801_09c_the_document_is_in_the_scan_set=_D801_FABPKG in _d801_docs)
    cell_net["round20_operative_semantics"] = dict(
        documents=_d801_rows, problems=_d801_bad,
        injections=_r20_injections, caught=_r20_caught, missed=_r20_missed,
        witnesses=_r20_witness, clean_controls_pass=_r20_clean_res,
        fabrication_package_document=_fp_controls,
        supervised_threshold_V=_D801_SUP_THRESH,
        ok=bool(not _d801_bad and all(_r20_caught.values())
                and all(v_["caught_by_d801"] for v_ in _r20_witness.values())
                and all(_r20_clean_res.values())
                and all(_fp_controls.values())),
        why="D-801 / Round-20 (Fable document campaign + R20-04): the "
            "supervised condition written 'once ... has reached ... or more' "
            "and 'requires a pack voltage of no less than', the qualified "
            "cure written 'one day' / '24-hour', a package temperature "
            "judged against the modelled figures, and an inserted meter's "
            "resistance assumed zero are refused in every operative "
            "document; the D-616 fabrication-package document is fenced and "
            "scanned.")
    cell_net_ok = cell_net_ok and cell_net["round20_operative_semantics"]["ok"]

    # ---- D-801 / D801-06: THE RELEASE IDENTITY IS BOUND, NOT TYPED. -------
    _ri_paths = dict(
        cto=ROOT / "docs/full-beta-v2/CTO_DECISIONS.md",
        state=ROOT / "docs/full-beta-v2/CURRENT_STATE.md",
        handoff=ROOT / "docs/full-beta-v2/AQROOT_DEMO_FAB_HANDOFF.md",
        manifest=ROOT / "hardware/demo/fab/MANIFEST.json")
    _ri_txt = {k_: (v_.read_text(encoding="utf-8", errors="replace")
                    if v_.exists() else "") for k_, v_ in _ri_paths.items()}
    try:
        _ri_manifest = json.loads(_ri_txt["manifest"])["assembly_drawings"][
            "release"]
    except (ValueError, KeyError, TypeError):
        _ri_manifest = None
    _ri_ev = ROOT / "hardware/demo/manufacturing/evidence"

    def _ri(current=CURRENT_RELEASE_ID, manifest=_ri_manifest, **over):
        t_ = dict(_ri_txt)
        t_.update(over)
        return release_identity_problems(current, manifest, t_["cto"],
                                         t_["state"], t_["handoff"], _ri_ev)

    _ri_bad = _ri()
    _prev = "D-%03d" % (_d797_release_number(CURRENT_RELEASE_ID) - 1)
    _cur_rt = re.compile(r"(#{1,6}\s+\**)%s( REVIEW TARGET)"
                         % re.escape(CURRENT_RELEASE_ID))
    _cur_st = re.compile(r"(#{1,6}\s+\**STATUS:\s*)%s\b"
                         % re.escape(CURRENT_RELEASE_ID))
    _ri_controls = dict(
        # the previous release written as the CURRENT review-target heading
        d801_06a_previous_release_as_current_heading=bool(_ri(
            state=_cur_rt.sub(r"\g<1>%s\g<2>" % _prev, _ri_txt["state"],
                              count=1))),
        # a stale STATUS header on the fab handoff
        d801_06b_stale_status_header=bool(_ri(
            handoff=_cur_st.sub(r"\g<1>%s" % _prev, _ri_txt["handoff"],
                                count=1))),
        # the hand-typed authority constant left at the previous release
        d801_06c_stale_authority_constant=bool(_ri(current=_prev)),
        # a MANIFEST whose release disagrees with the checker
        d801_06d_manifest_mismatched_with_the_checker=bool(
            _ri(manifest=_prev)),
        # a CHANGELOG-derived id that disagrees with CTO_DECISIONS
        d801_06e_changelog_ahead_of_the_decision_record=bool(_ri(
            cto="## %s — injected\n\n" % _prev + re.sub(
                r"^## %s\b.*$" % re.escape(CURRENT_RELEASE_ID), "",
                _ri_txt["cto"], count=1, flags=re.M))),
        # ...and the derivation itself reads the newest heading
        d801_06f_the_constant_is_derived_from_the_changelog=bool(
            derive_current_release("# x\n\n## D-123 — a\n\n## D-122 — b\n")
            == "D-123"),
        # a fenced (historical) previous heading stays legal
        d801_06g_a_fenced_previous_heading_is_history=not _ri())
    cell_net["release_identity_binding"] = dict(
        current_release=CURRENT_RELEASE_ID, manifest_release=_ri_manifest,
        problems=_ri_bad, controls=_ri_controls,
        ok=bool(not _ri_bad and all(_ri_controls.values())),
        why="D-801 / R20-06: CURRENT_RELEASE_ID read D-799 on the frozen "
            "D-800 target and a current D-799 heading passed F1-F14.  The id "
            "is derived from the CHANGELOG (the MANIFEST's own authority) and "
            "every current identity surface is bound to it.")
    cell_net_ok = cell_net_ok and cell_net["release_identity_binding"]["ok"]

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
        # D-793 RE-AIMS THE TWO SINGLE-AXIS CONTROLS, AND THE RE-AIM IS ITSELF
        # THE FINDING.  At D-792 a better pass pair ALONE, or a 0 C ambient
        # ALONE, each flipped the `d790_declared` verdict.  With R12-01's
        # completed source path and R12-05's corrected module total neither
        # does on its own any more -- both together still do, which is what
        # `f12a` above proves.  A control that has stopped flipping is not a
        # control, so each axis is now required to MOVE the answer: the
        # supported set of `d790_declared` must CHANGE when that axis moves,
        # which is a measurement of the physics on that axis and cannot be
        # satisfied by a hard-coded verdict.
        f12a2_a_better_pass_pair_alone_moves_the_supported_set=bool(
            [st for st in _cell(pass_pair=_better_pair)[1]["states"]
             if st["key"] == "d790_declared"]
            != [st for st in cell_net["states"]
                if st["key"] == "d790_declared"]),
        f12a3_a_cool_ambient_alone_moves_the_supported_set=bool(
            [st for st in _cell(ambient_C=0.0)[1]["states"]
             if st["key"] == "d790_declared"]
            != [st for st in cell_net["states"]
                if st["key"] == "d790_declared"]),
        # ...and a materially worse pass pair must take the REFERENCE state
        # down with it.
        f12b_refuses_a_pass_pair_that_cannot_carry_the_reference_state=bool(
            not _cell(pass_pair=_worse_pair)[0]),
        # ...and a BATOCP band at TI's stated 18 % rather than the declared
        # wider one must CHANGE the answer somewhere, or the assumption is
        # decorative.
        # D-793: THE OCP BAND IS NO LONGER THE BINDING LIMIT ANYWHERE, AND
        # THE CONTROL SAYS SO RATHER THAN QUIETLY PASSING.
        #
        # D-792 asked whether narrowing the DECLARED band back to TI's stated
        # 18 % changed any state.  With the corrected source path the binding
        # limit in every state is the operating point or the node, never the
        # battery current, so that perturbation now changes nothing -- which
        # would have made the control vacuous.  What must still be true is
        # that the OCP limit is CHECKED at all, and the control proves it by
        # moving the limit far enough to bite: at a 1.5 A OCP minimum the
        # derivation must produce a different answer.  The narrower-band
        # comparison is retained BESIDE it as a reported fact.
        f12c_the_ocp_limit_is_checked_at_all=bool(
            _cell(ocp_min_A=1.5)[1]["states"] != cell_net["states"]),
        f12c2_the_declared_wider_band_no_longer_binds_anywhere=bool(
            _cell(ocp_min_A=IBAT_OCP_TYP_A
                  * (1 - IBAT_OCP_STATED_ACCURACY))[1]["states"]
            == cell_net["states"]),
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
    # D-794 / R13-04.  THE REQUIREMENT IS READ FROM THE AUTHORITY, NOT FROM
    # THE DISPLAY COPY.
    #
    # `env["rails_A"]` is a PRESENTATION dict: every float in it has been put
    # through `round(x, 4)` so the emitted JSON is readable.  D-793 took the
    # ampacity requirement out of that dict, so the number this clause ruled
    # with was a rounded one -- and rounding a requirement to four places
    # moves it UP as often as down.  It moved up here: the true fault ceiling
    # is 0.80486138 A, the display copy says 0.8049 A, and a design current
    # equal to the true ceiling was reported STALE against its own value.
    # Rounding is for reading; the authority is `apm.ilim_band_A`, which is
    # also exactly what `audit_rail_ampacity` calls.
    ampacity_expected = {
        "ACC_3V3_SW": apm.ilim_band_A(
            apm.ILIM_PROGRAMMED_OHM["ACC_3V3"])["max_A"],
        "ACC_5V_SW": apm.ilim_band_A(
            apm.ILIM_PROGRAMMED_OHM["ACC_5V"])["max_A"],
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

    # ---- D-794 / R13-04.  THE STALE-CONSUMER CONTROL --------------------
    #
    # ROUND-13 asks for a full-suite destructive control for a "stale consumer
    # value".  The clause above is the one that catches them, and D-793's
    # version of it could not: it ruled against a display-rounded figure, so
    # a design current that was CORRECT was reported stale while one that was
    # stale by less than half a milliamp would have passed.  A clause that can
    # be wrong in both directions has to be shown to fire.
    #
    # The control replays the exact stale set Round-6 / R6-E07 found in this
    # audit and required to be removed -- BAT and SYS still carrying the
    # .kicad_dru NETCLASS currents of 1.50 A and 1.00 A, and P3V3_MAIN at
    # 1.849 A -- and requires every one of them to be REFUSED against the
    # requirement derived from the live envelope.  It is real historical
    # staleness, not an invented one.
    #
    # A NOTE ON THE DIRECTION, BECAUSE IT DECIDES WHAT THIS CLAUSE CAN SEE.
    # D-793's ACC_3V3_SW figure of 0.849 A was ALSO stale -- it was R97 =
    # 1.78 kOhm's ceiling, retired at D-791 -- but it was stale HIGH, so the
    # copper was sized for more current than the board can deliver and this
    # coverage clause could never have flagged it.  What removed it was
    # deriving the number instead of typing it.  The controls below therefore
    # exercise the direction this clause CAN rule on, and the statement about
    # the other direction is that a coverage check is not the instrument for
    # it.
    def _ampacity_coverage(design_A):
        return {name: (design_A.get(name) is not None
                       and design_A[name] + 1e-9 >= need)
                for name, need in ampacity_expected.items()}
    _live_design = {n: rails_by_name.get(n, {}).get("amps")
                    for n in ampacity_expected}
    _r6e07_stale = dict(_live_design, BAT_PROTECTED_P=1.50,
                        BQ25185_SYS=1.00, P3V3_MAIN=1.849)
    _r6e07_result = _ampacity_coverage(_r6e07_stale)
    _controls = dict(
        the_live_design_currents_are_accepted=all(
            _ampacity_coverage(_live_design).values()),
        the_r6e07_stale_netclass_currents_are_refused=not any(
            _r6e07_result[n] for n in ("BAT_PROTECTED_P", "BQ25185_SYS",
                                       "P3V3_MAIN")),
        a_design_current_one_milliamp_short_is_refused=not all(
            _ampacity_coverage(
                dict(_live_design,
                     ACC_3V3_SW=ampacity_expected["ACC_3V3_SW"] - 0.001)
            ).values()),
        a_missing_design_current_is_refused=not all(
            _ampacity_coverage(
                dict(_live_design, ACC_3V3_SW=None)).values()))
    env["stale_consumer_controls"] = dict(
        _controls,
        r6e07_stale_values_replayed_A={
            k: _r6e07_stale[k] for k in ("BAT_PROTECTED_P", "BQ25185_SYS",
                                         "P3V3_MAIN")},
        requirements_A={k: round(v, 6)
                        for k, v in sorted(ampacity_expected.items())},
        the_d793_acc_3v3_staleness_was_in_the_conservative_direction=bool(
            0.849 > ampacity_expected["ACC_3V3_SW"]),
        why="R13-04 names 'stale consumer value' as a required destructive "
            "control.  The replayed figures are the three R6-E07 found in "
            "this exact clause's inputs: the two .kicad_dru netclass "
            "currents and D-787's P3V3 figure.")
    env["every_stale_consumer_control_behaves"] = bool(all(_controls.values()))
    env_ok = env_ok and env["every_stale_consumer_control_behaves"]

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
    # at If = 120 mA, Ipn 110 mA TYP / 120 mA MAX -- D-795 corrects D-792's
    # '110 MIN / 120 TYP') which the converter model now
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

    # ---- D-793 / R12-01.  THE MOLEX SPECIFICATION IS IN THE TREE, AND IT IS
    # HASHED FOR THE SAME REASON THE PANEL'S IS.
    #
    # D-792 DECLARED the aged contact and crimp allowances because the document
    # "is not retrievable from this environment".  It is; it retrieved through
    # the Internet Archive's 2023-11-01 snapshot of the same molex.com URL and
    # it publishes 40 mOhm MAX after every durability and environmental
    # exposure, 20 mOhm MAX initial with the conductor SUBTRACTED, and 5 mOhm
    # MAX on a crimped portion.  Three ruling values now rest on it, so the
    # citation has to be a fact about the tree rather than a sentence about a
    # past fetch -- which is exactly what R11-N01 found when the panel's
    # "HTTP 403" sentence turned out to be about the environment.
    _mx_pdf = (ROOT / "hardware/demo/kicad/aqroot-demo/vendor/MOLEX"
               / "molex-5055700003-PS-A1.pdf")
    _mx_expect = ("0218c6300aa4e4b4906e7607b7e033ece51c2adc6439ae8be90ce8e659"
                  "942440")
    _mx_actual = (hashlib.sha256(_mx_pdf.read_bytes()).hexdigest()
                  if _mx_pdf.exists() else None)
    _mx_txt = (ROOT / "hardware/demo/kicad/aqroot-demo/vendor/MOLEX"
               / "molex-5055700003-PS-A1.txt")
    _mx_rows = _mx_txt.read_text(encoding="utf-8", errors="replace") \
        if _mx_txt.exists() else ""
    _mx_flat = re.sub(r"\s+", " ", _mx_rows)
    env["molex_connector_specification_is_archived"] = dict(
        path=str(_mx_pdf.relative_to(ROOT)) if _mx_pdf.exists() else None,
        expected_sha256=_mx_expect, actual_sha256=_mx_actual,
        revision_retrieved="A1",
        revision_on_the_product_page="A6",
        revision_discrepancy_is_recorded=True,
        # The three rows three ruling values rest on, READ OUT of the archived
        # rendering rather than quoted from a comment.
        rows_read=dict(
            initial_contact_20mOhm=bool(
                "20 milliohms MAX." in _mx_flat),
            crimped_portion_5mOhm=bool("5 milliohms MAX." in _mx_flat),
            post_environmental_40mOhm=bool(
                _mx_flat.count("40 milliohms") >= 8)),
        values_that_rest_on_it=dict(
            contact_aged_max_ohm=apm.CONTACT_AGED_MAX_OHM,
            contact_initial_max_ohm=apm.CONTACT_INITIAL_MAX_OHM,
            crimp_max_ohm=apm.CRIMP_MAX_OHM),
        ok=bool(_mx_actual == _mx_expect
                and "20 milliohms MAX." in _mx_flat
                and "5 milliohms MAX." in _mx_flat
                and _mx_flat.count("40 milliohms") >= 8
                and abs(apm.CONTACT_AGED_MAX_OHM - 0.040) < 1e-12
                and abs(apm.CONTACT_INITIAL_MAX_OHM - 0.020) < 1e-12
                and abs(apm.CRIMP_MAX_OHM - 0.005) < 1e-12),
        why="D-792 recorded this document as unobtainable and DECLARED the "
            "contact and crimp terms on that basis.  It is obtainable.  The "
            "hash and the three parsed rows are here so a ruling value cannot "
            "drift away from the document it is read from, and so that "
            "'unobtainable' cannot mean 'not fetched from here' a fourth "
            "time.")
    env["molex_connector_specification_is_archived_ok"] = bool(
        env["molex_connector_specification_is_archived"]["ok"])
    env_ok = env_ok and env["molex_connector_specification_is_archived_ok"]
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
        # D-793 / R12-01 RE-AIMS THIS AT THE STATE THE PRODUCT PUBLISHES.
        #
        # D-792 asked whether BOTH rails at their FULL published budgets, with
        # every internal subsystem at once, stayed inside the Micro-Lock Plus
        # AWG26 rating.  With the corrected source path and the corrected
        # module total that case is **-0.98 %** on the live basis -- and it is
        # no longer a state a conforming user can reach: F12 refuses the FULL
        # simultaneous pair at every attainable cell voltage and the published
        # simultaneous contract is the DECLARED pair.  Asking a connector
        # question about an unreachable state is the shape of defect this
        # programme keeps finding; the question is asked about the DECLARED
        # pair instead, and the full-pair figure is RETAINED AND REPORTED
        # beside it so the size of the change is visible rather than removed.
        ("f6af_declared_pair_concurrency_has_positive_rating_margin",
         min(v["cases"]["both_declared_pair_full_internal"][
             "margin_to_the_published_rating_pct"]
             for v in env["battery_connection"]["bases"].values()) > 0),
        # ...and the FULL pair really is over the rating, which is WHY the
        # published simultaneous contract is the declared pair.  A control
        # that could not tell the two apart would prove nothing.
        ("f6af2_the_full_pair_is_over_the_connector_rating_and_is_refused",
         min(v["cases"]["both_published_full_internal"][
             "margin_to_the_published_rating_pct"]
             for v in env["battery_connection"]["bases"].values()) < 0),
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
         != canonical_manufacturer("Viking Tech Corporation")),
        # ---- D-794 / FABLE RESIDUAL: THE EMBEDDED SYMBOL CACHE. -----------
        ("f13s_the_embedded_symbol_cache_agrees_with_its_instances",
         judge_embedded_symbol_cache()[0]),
        # ...and the clause is load-bearing: the exact state D-794 found --
        # the AOS pass pair's cached entry naming onsemi -- must REFUSE.
        ("f13t_refuses_the_d793_onsemi_cache_on_the_aos_pass_pair",
         not judge_embedded_symbol_cache({
             "AQROOT_Beta:AO4800": dict(
                 cache=dict(manufacturer="onsemi", mpn="AO4800",
                            datasheet="", sheet="01_power_tree.kicad_sch"),
                 instances={"Alpha & Omega Semiconductor": ["Q2", "Q3"]})})[0]),
        # ...and so must a cached DATASHEET pointing at another company, which
        # is how the retired NTMD4820N PDF survived three reviews.
        ("f13u_refuses_a_cached_datasheet_naming_another_company",
         not judge_embedded_symbol_cache({
             "AQROOT_Beta:AO4800": dict(
                 cache=dict(
                     manufacturer="Alpha & Omega Semiconductor",
                     mpn="AO4800",
                     datasheet="https://www.onsemi.com/pdf/datasheet/"
                               "ntmd4820n-d.pdf",
                     sheet="01_power_tree.kicad_sch"),
                 instances={"Alpha & Omega Semiconductor": ["Q2", "Q3"]})})[0]),
        # ...and a reviewed ALIAS is one company, not a contradiction.
        ("f13v_a_reviewed_alias_in_the_cache_is_not_a_contradiction",
         judge_embedded_symbol_cache({
             "AQROOT_Beta:MHPA3528RGBCT": dict(
                 cache=dict(
                     manufacturer="MEIHUA (Lianyungang Meihua Electronic "
                                  "Technology)",
                     mpn="MHPA3528RGBCT", datasheet="",
                     sheet="08_buttons_expanders.kicad_sch"),
                 instances={"MEIHUA": ["D10"]})})[0]),
        # ---- D-794 / R13-07.  THE AOS SPELLING THAT WAS BEING REJECTED. ---
        ("f13w_alpha_and_omega_is_the_same_company_as_alpha_ampersand_omega",
         canonical_manufacturer("Alpha and Omega Semiconductor")
         == canonical_manufacturer("Alpha & Omega Semiconductor")
         == canonical_manufacturer("Alpha & Omega Semicon")
         == canonical_manufacturer("AOS")
         == "alpha & omega semiconductor"),
        ("f13x_the_aos_alias_survives_the_legal_form_fold",
         canonical_manufacturer("Alpha and Omega Semiconductor, Inc.")
         == canonical_manufacturer("Alpha & Omega Semiconductor Co., Ltd.")
         == "alpha & omega semiconductor"),
        # ...AND IT IS NARROW.  The marketplace re-marks D-789 named, the
        # clone houses, a distributor's own name and a cross-manufacturer
        # collision all still CONTRADICT.  An alias that laundered any of
        # these would be the defect rather than the fix.
        # ...AND IT IS NARROW.  The marketplace re-marks D-789 named, the
        # clone houses, a distributor's own name, a cross-manufacturer
        # collision and a NEAR MATCH all still CONTRADICT.  An alias that
        # laundered any of these would be the defect rather than the fix.
        ("f13y_the_aos_alias_does_not_launder_a_remark_or_a_clone",
         all(canonical_manufacturer(n) != "alpha & omega semiconductor"
             for n in ("VBsemi", "VBsemi Elec", "Kexin", "Kexin Industrial",
                       # the ampersand DROPPED, not written out -- a third
                       # spelling nobody reviewed
                       "Alpha Omega Semiconductor",
                       # a different company that starts the same way
                       "Alpha & Omega Trading", "Alpha and Omega Trading",
                       "Omega Semiconductor",
                       # distributors are not manufacturers
                       "LCSC", "JLCPCB",
                       # cross-manufacturer
                       "onsemi", "Diodes Incorporated",
                       # one word, and a two-letter stub
                       "Alpha", "AO",
                       # PLURAL: a near match, not a match
                       "Alpha and Omega Semiconductors"))),
        # ...and the written-out spelling reaches the group through the ALIAS
        # TABLE, not through a character rule.  With the two D-794 entries
        # removed from a local copy of the table, it no longer resolves --
        # which is what "exact narrow alias" means and what distinguishes it
        # from the fuzzy matching R13-07 forbids.
        ("f13z_the_written_out_spelling_needs_the_reviewed_alias",
         _aos_alias_is_the_only_route()),
        # ---- D-793 / R12-07.  ONE NORMALISER, PROVED TO BE ONE. -----------
        #
        # F8 had its own two-entry fold and F13 had the alias table, so an
        # alias added to one did not reach the other -- R11-09's defect in the
        # other gate.  `_norm_cap_mfr` IS `canonical_manufacturer` now, and
        # these claims are what keeps it that way.
        ("f13l_f8_and_f13_fold_manufacturer_names_identically",
         all(_norm_cap_mfr(n) == (canonical_manufacturer(n) or "")
             for n in ("Murata", "Murata Electronics",
                       "Murata Electronics Co., Ltd.",
                       "Samsung Electro-Mechanics Co., Ltd.",
                       "Samsung Electro-Mechanics", "Yageo Corporation",
                       "Vishay Intertechnology", "PUI Audio, Inc.",
                       "onsemi", "ON Semiconductor", "Texas Instruments",
                       "TI", "Diodes Incorporated", "Diodes Inc"))),
        # LEGITIMATE LEGAL SPELLINGS PASS -- the half R12-07 names explicitly.
        ("f13m_legal_spellings_are_one_company_in_both_gates",
         _norm_cap_mfr("Samsung Electro-Mechanics Co., Ltd.")
         == _norm_cap_mfr("Samsung Electro-Mechanics")
         and _norm_cap_mfr("Murata Electronics Co., Ltd.")
         == _norm_cap_mfr("Murata")
         and _norm_cap_mfr("Yageo Corporation") == _norm_cap_mfr("Yageo")),
        # ...AND COUNTERFEIT SUFFIXES, NEAR MATCHES AND CROSS-MANUFACTURER
        # COLLISIONS FAIL.  A trailing legal form is dropped; a trailing
        # anything ELSE is a different company.
        ("f13n_a_counterfeit_suffix_is_a_different_company",
         _norm_cap_mfr("Samsung Electro-Mechanics Counterfeit Ltd")
         != _norm_cap_mfr("Samsung Electro-Mechanics")
         and _norm_cap_mfr("Murata Electronics International")
         != _norm_cap_mfr("Murata Electronics")
         and _norm_cap_mfr("Vishay Intertechnology Trading")
         != _norm_cap_mfr("Vishay Intertechnology")),
        ("f13o_a_near_match_is_not_a_match",
         _norm_cap_mfr("Samsung Electronics")
         != _norm_cap_mfr("Samsung Electro-Mechanics")
         and _norm_cap_mfr("Viking Tech") != _norm_cap_mfr("Vishay")
         and _norm_cap_mfr("Diodes Zetex") != _norm_cap_mfr("Diodes Inc")),
        # D-795 / R14-07: NO TRUNCATION OF ANY KIND CANONICALISES.  Astra's
        # exact case first, then the shapes D-793's word-boundary rule used
        # to accept, then the same shapes over a local table so the claim
        # tests the ABSENCE OF A RULE rather than this week's aliases.
        ("f13p_alpha_and_is_not_aos",
         canonical_manufacturer("Alpha and") != "alpha & omega semiconductor"
         and canonical_manufacturer("Alpha &") != "alpha & omega semiconductor"
         and canonical_manufacturer("Alpha and Omega Semi")
         != "alpha & omega semiconductor"
         and canonical_manufacturer("alpha and omega semicond")
         != "alpha & omega semiconductor"),
        ("f13q_no_prefix_or_truncation_ever_canonicalises",
         canonical_manufacturer("Murata Elec") != "murata electronics"
         and canonical_manufacturer("Texas Instr") != "texas instruments"
         and canonical_manufacturer("Samsung Electro")
         != "samsung electro-mechanics"
         and canonical_manufacturer("Analog Devices Inc./Max")
         != "analog devices"
         and _no_truncation_rule_exists()),
        # ...and the fold is still NOT a similarity metric: it folds case,
        # spacing, commas and a trailing legal form, and nothing else.
        ("f13r_the_fold_touches_nothing_but_case_space_comma_legal_form",
         fold_manufacturer("  Bourns ,  INC.  ") == "bourns"
         and fold_manufacturer("Wurth Elektronik") == "wurth elektronik"
         and fold_manufacturer("W\u00fcrth Elektronik")
         != fold_manufacturer("Wurth Elektronik"))))

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
    # ---- D-801 / Round-20 D801-05: the published figures ARE F10's. ------
    _pp_docs = dict(
        plan=ROOT / "docs/full-beta-v2/assembly/FIRST_FIVE_ASSEMBLY_PLAN.md",
        ledger=ledger_path,
        handoff=ROOT / "docs/full-beta-v2/AQROOT_DEMO_FAB_HANDOFF.md")
    _pp_txt = {k_: (v_.read_text(encoding="utf-8", errors="replace")
                    if v_.exists() else "") for k_, v_ in _pp_docs.items()}

    def _pp_problems(pub, txt):
        bad = []
        _row = fa_step_rows(txt["plan"]).get("C-BAT-GATE-01", "")
        if pub["step"] not in _row:
            bad.append("C-BAT-GATE-01 is not the F10-generated step")
        for k_ in ("ledger_table", "ledger_sensitivity"):
            if pub[k_] not in txt["ledger"]:
                bad.append("SOURCING_LEDGER does not carry the F10-generated "
                           "%s" % k_)
        if pub["handoff_rows"] not in txt["handoff"]:
            bad.append("the fab handoff does not carry the F10-generated "
                       "envelope rows")
        for k_, t_ in txt.items():
            for fenced, block in _norm_blocks(t_):
                if fenced:
                    continue
                for sent in _d797_units(block):
                    if any(f in sent for f in _NORM_FENCE):
                        continue
                    for tok in PASS_PAIR_STALE_FIGURES:
                        if tok in sent:
                            bad.append("%s: stale %r in a current sentence: "
                                       "%s" % (k_, tok, sent.strip()[:120]))
        return bad

    _pp_pub = pass_pair_publication(pass_pair, _pkg or {})
    _pp_bad = _pp_problems(_pp_pub, _pp_txt)

    def _pp_regen(**kw):
        return pass_pair_publication(judge_pass_pair_gate(
            _bat_rail["amps"] if _bat_rail else 2.35, VBAT_CORNER,
            internal_air_C=(_pkg or {}).get("internal_air_C"),
            sustained_amps=(_pkg or {}).get("sustained_thermal_envelope_A"),
            **kw)[1], _pkg or {})
    _pp_stale_step = dict(_pp_txt, plan=_pp_txt["plan"].replace(
        "**%.4f A** at" % pass_pair["guaranteed_conduction_ceiling"][
            "ceiling_A"], "**2.2845 A** at"))
    pass_pair_publication_controls = dict(
        # D-800's stale ceiling, written into the current step
        d801_05a_stale_ceiling_is_refused=bool(_pp_problems(
            _pp_pub, _pp_stale_step)),
        # documents generated at the WRONG bench temperature (40 C) differ
        d801_05b_wrong_bench_temperature_is_refused=bool(_pp_problems(
            _pp_regen(bench_air_C=40.0), _pp_txt)),
        # ...and at the WRONG hot ratio (the 2x case as the ruling one)
        d801_05c_wrong_hot_ratio_is_refused=bool(_pp_problems(
            _pp_regen(ruling_ratio=2.0), _pp_txt)),
        # the D-800 "must survive at 2x" sentence, injected, is refused
        d801_05d_the_2x_survival_claim_is_refused=bool(_pp_problems(
            _pp_pub, dict(_pp_txt, ledger=_pp_txt["ledger"] + "\n\nThe "
                          "declared ratio now carries a sensitivity the "
                          "ruling case must survive at 2x.\n"))),
        # and the 2x case really does lose the row at the enclosure condition
        d801_05e_the_2x_case_loses_the_row=not pass_pair[
            "enclosure_2x_case"]["meets_the_row"],
        # the bench crossing is above the enclosure ceiling (cooler air)
        d801_05f_bench_crossing_exceeds_the_enclosure_ceiling=bool(
            pass_pair["bench_condition"]["crossing_A"]
            > pass_pair["guaranteed_conduction_ceiling"]["ceiling_A"]))
    pass_pair["publication"] = dict(
        generated=_pp_pub, problems=_pp_bad,
        controls=pass_pair_publication_controls,
        ok=bool(not _pp_bad and all(pass_pair_publication_controls.values())))
    pass_pair_ok = bool(pp_ok and pass_pair_block["ok"]
                        and all(pass_pair_controls.values())
                        and pass_pair["publication"]["ok"])

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
        # ---- D-793 / R12-07.  THE SAME SHAPE, ON THE GROUND SKIP.
        # `leaf == "GND"` was true of any hierarchy, so a pad moved onto a net
        # this repository has established nothing about was not examined at
        # all.  The skip is keyed by the EXACT canonical net now, so every one
        # of these must refuse.
        _cap_control("f8v_refuses_a_pad_on_an_alien_hierarchy_gnd",
                     net_max_dc=sbs.NET_MAX_DC,
                     net_rewrite={"GND": "/ALIEN/GND"}),
        _cap_control("f8w_refuses_a_gnd_leaf_under_a_real_sheet",
                     net_max_dc=sbs.NET_MAX_DC,
                     net_rewrite={"GND": "/01_POWER_TREE/GND"}),
        # ONE KNOWN TERMINAL AND ONE UNKNOWN ONE IS STILL UNKNOWN.  Rewriting
        # only the ground side leaves every decoupling capacitor with a
        # perfectly good rail on one pad and an unestablished node on the
        # other, which is exactly the case a leaf-keyed skip waved through.
        _cap_control("f8x_refuses_one_known_terminal_and_one_unknown_one",
                     net_max_dc=sbs.NET_MAX_DC,
                     net_rewrite={"GND": "/UNVERIFIED/GND"}),
        # ...and the frozen board, whose ground really is `GND`, still passes.
        ("f8y_the_frozen_board_passes_the_exact_ground_rule",
         judge_capacitor_derating(board, sch_dnp,
                                  net_max_dc=sbs.NET_MAX_DC)[0]),
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
        "F14_an_independent_oracle_re_derives_what_the_model_claims": dict(
            ok=oracle_ok,
            method="D-793 / R12-04, which Round-12 states as a release "
                   "blocker: 'Astra halved canonical charger package heat and "
                   "all F1-F13 still passed.  Astra removed the 5V-first "
                   "transition; completeness Boolean became false but final "
                   "verdict remained PASS.  The canonical model cannot be its "
                   "own oracle.'  BOTH REPRODUCE, and the cause is one "
                   "defect twice: D-792's `energy_balance` invariant compared "
                   "an expression with ITSELF (`p_diss` was defined as the "
                   "very expression it was checked against), and F12's "
                   "verdict was a conjunction that did not include the "
                   "completeness Boolean.  `aqroot_power_oracle` is a second, "
                   "SMALL implementation that imports nothing from the "
                   "canonical model, solves nothing, and re-derives what a "
                   "solved state claims from primitives: the terminal-power "
                   "balance against the sum of the internal loss elements, "
                   "every charger branch inequality, the itemised source "
                   "path, the pass-pair drop, the permission edge and the "
                   "post-enable retention.  Completeness is a VERDICT term, "
                   "and the six mutations R12-04 names are run on every "
                   "release run and must each be caught.",
            **{k: v for k, v in oracle.items() if k != "ok"}),
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
    # D-795: the regime/completion EVIDENCE (thousands of solved states the
    # oracle re-checks in memory) is not written out; every published figure
    # and every row's ceilings are.
    def _public(x):
        if isinstance(x, dict):
            # D-797: keys are stringified (a mode-bits table is int-keyed and
            # a role table carries a neutral None role), so the sorted dump
            # never compares a None with a str.
            return {str(k): _public(v) for k, v in x.items()
                    if not str(k).startswith("_")}
        if isinstance(x, list):
            return [_public(v) for v in x]
        return x
    text = json.dumps(_public(out), indent=1, sort_keys=True)
    if args.out:
        args.out.write_text(text + "\n", encoding="utf-8")
    print(text)
    for k, c in checks.items():
        print("  %s %s" % (k, "PASS" if c["ok"] else "FAIL"), file=sys.stderr)
    return 0 if out["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
