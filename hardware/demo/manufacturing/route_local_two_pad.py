#!/usr/bin/env python3
"""Route an allowlisted local two-pad Demo net with a real KiCad scratch gate."""

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BOARD = ROOT / "hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb"
sys.path.insert(0, str(ROOT / "hardware/beta-v2/checks"))
import incremental_router as ir  # noqa: E402
import qrouter as qr  # noqa: E402

ROUTES = {
    "IR_RX_MCU_TP": {
        "net": "/IR_RX_GPIO44",
        "pads": ("U1.36", "TP40.1"),
        "ignored_connected_pads": ("U6.1",),
        "layer": "F", "width": 200_000, "clearance": 200_000,
        "inner_long_haul_plan": {
            "a": "U1.36", "b": "TP40.1", "a_near": "F", "b_near": "F",
            "inner": ["I2", "I3"],
        },
    },
    "IR_RX_TP_RECEIVER": {
        "net": "/IR_RX_GPIO44",
        "pads": ("TP40.1", "U6.1"),
        "ignored_connected_pads": ("U1.36",),
        "layer": "F", "width": 200_000, "clearance": 200_000,
        "inner_long_haul_plan": {
            "a": "TP40.1", "b": "U6.1", "a_near": "F", "b_near": "F",
            "inner": ["I2", "I3"],
        },
    },
    "TCA4307_READY_IC_PULLUP": {
        "net": "/09_COMMUNITY_HEADER/TCA4307_READY",
        "pads": ("U16.5", "R46.2"),
        "ignored_connected_pads": ("TP44.1",),
        "layer": "B", "width": 200_000, "clearance": 200_000,
    },
    "TCA4307_READY_PULLUP_TP": {
        "net": "/09_COMMUNITY_HEADER/TCA4307_READY",
        "pads": ("R46.2", "TP44.1"),
        "ignored_connected_pads": ("U16.5",),
        "layer": "B", "width": 200_000, "clearance": 200_000,
        "inner_long_haul_plan": {
            "a": "R46.2", "b": "TP44.1", "a_near": "B", "b_near": "B",
            "inner": ["I2", "I3"],
        },
    },
    "ACC_DETECT_HDR_TVS_RESISTOR": {
        "net": "/09_COMMUNITY_HEADER/ACC_DETECT_N_HDR",
        "pads": ("D5.6", "R64.2"),
        "ignored_connected_pads": ("TP43.1", "J5.21"),
        "layer": "F", "width": 200_000, "clearance": 200_000,
    },
    "ACC_DETECT_HDR_RESISTOR_TESTPOINT": {
        "net": "/09_COMMUNITY_HEADER/ACC_DETECT_N_HDR",
        "pads": ("R64.2", "TP43.1"),
        "ignored_connected_pads": ("D5.6", "J5.21"),
        "layer": "F", "width": 200_000, "clearance": 200_000,
    },
    "ACC_DETECT_HDR_RESISTOR_CONNECTOR": {
        "net": "/09_COMMUNITY_HEADER/ACC_DETECT_N_HDR",
        "pads": ("R64.2", "J5.21"),
        "ignored_connected_pads": ("D5.6", "TP43.1"),
        "layer": "F", "width": 200_000, "clearance": 200_000,
    },
    "SW9_A_U12_PULLDOWN": {
        "net": "Net-(SW9-A)",
        "pads": ("U12.12", "R43.1"),
        "ignored_connected_pads": ("TP13.1", "SW9.1"),
        "ignored_dnp_pads": ("R68.2",),
        "layer": "B", "width": 200_000, "pad_clearance": 200_000,
        "clearance": 300_000,
        "inner_long_haul_plan": {
            "a": "U12.12", "b": "R43.1", "a_near": "B", "b_near": "B",
            "inner": ["I2", "I3"],
        },
    },
    "SW9_A_U12_TESTPOINT": {
        "net": "Net-(SW9-A)",
        "pads": ("U12.12", "TP13.1"),
        "ignored_connected_pads": ("R43.1", "SW9.1"),
        "ignored_dnp_pads": ("R68.2",),
        "layer": "B", "width": 200_000, "pad_clearance": 200_000,
        "clearance": 300_000,
    },
    "SW9_A_TESTPOINT_SWITCH": {
        "net": "Net-(SW9-A)",
        "pads": ("TP13.1", "SW9.1"),
        "ignored_connected_pads": ("R43.1", "U12.12"),
        "ignored_dnp_pads": ("R68.2",),
        "layer": "B", "width": 200_000, "pad_clearance": 200_000,
        "clearance": 300_000,
        "inner_long_haul_plan": {
            "a": "TP13.1", "b": "SW9.1", "a_near": "B", "b_near": "F",
            "inner": ["I2", "I3"],
        },
    },
    "WAKE_ATTN_HDR_TVS_RESISTOR": {
        "net": "/09_COMMUNITY_HEADER/WAKE_ATTN_N_HDR",
        "pads": ("D5.4", "R66.2"),
        "ignored_connected_pads": ("J5.20",),
        "layer": "F", "width": 200_000, "clearance": 200_000,
    },
    "WAKE_ATTN_HDR_TVS_CONNECTOR": {
        "net": "/09_COMMUNITY_HEADER/WAKE_ATTN_N_HDR",
        "pads": ("D5.4", "J5.20"),
        "ignored_connected_pads": ("R66.2",),
        "layer": "F", "width": 200_000, "clearance": 200_000,
    },
    "U12_PS_SYNC_PULLDOWN_TP": {
        "net": "Net-(U12-PS_SYNC)",
        "pads": ("R42.2", "TP14.1"),
        "ignored_connected_pads": ("U12.13",),
        "layer": "B", "width": 200_000, "clearance": 200_000,
    },
    "U12_PS_SYNC_PULLDOWN_IC": {
        "net": "Net-(U12-PS_SYNC)",
        "pads": ("R42.2", "U12.13"),
        "ignored_connected_pads": ("TP14.1",),
        "layer": "B", "width": 200_000, "clearance": 200_000,
    },
    "U12_PS_SYNC_PULLDOWN_IC_INNER": {
        "net": "Net-(U12-PS_SYNC)",
        "pads": ("R42.2", "U12.13"),
        "ignored_connected_pads": ("TP14.1",),
        "layer": "B", "width": 200_000, "clearance": 200_000,
        "inner_long_haul_plan": {
            "a": "R42.2", "b": "U12.13", "a_near": "B", "b_near": "B",
            "inner": ["I2", "I3"],
        },
    },
    "U12_PG_PULLUP_TP": {
        "net": "Net-(U12-PG)",
        "pads": ("R41.2", "TP8.1"),
        "ignored_connected_pads": ("U12.14",),
        "layer": "B", "width": 200_000, "clearance": 200_000,
    },
    "U12_PG_PULLUP_IC": {
        "net": "Net-(U12-PG)",
        "pads": ("R41.2", "U12.14"),
        "ignored_connected_pads": ("TP8.1",),
        "layer": "B", "width": 200_000, "clearance": 200_000,
    },
    "GPIO45_VDDSPI_U1_R111": {
        "net": "/02_MCU_CORE/GPIO45_VDDSPI_STRAP",
        "pads": ("U1.26", "R111.1"),
        "ignored_connected_pads": ("TP1.1",),
        "layer": "F", "width": 200_000, "clearance": 250_000,
        "inner_long_haul_plan": {
            "a": "U1.26", "b": "R111.1", "a_near": "F", "b_near": "F",
            "inner": ["I2", "I3"],
        },
    },
    "GPIO45_VDDSPI_R111_TP1": {
        "net": "/02_MCU_CORE/GPIO45_VDDSPI_STRAP",
        "pads": ("R111.1", "TP1.1"),
        "ignored_connected_pads": ("U1.26",),
        "layer": "F", "width": 200_000, "clearance": 200_000,
    },
    "SPI_A_SCK_DISPLAY": {
        "net": "/SPI_A_SCK",
        "pads": ("U1.20", "J1.36"),
        "ignored_connected_pads": ("J2.5",),
        "layer": "F", "width": 200_000, "clearance": 200_000,
        "inner_long_haul_plan": {
            "a": "U1.20", "b": "J1.36", "a_near": "F", "b_near": "F",
            "inner": ["I2", "I3"],
        },
    },
    "SPI_A_SCK_SD": {
        "net": "/SPI_A_SCK",
        "pads": ("U1.20", "J2.5"),
        "ignored_connected_pads": ("J1.36",),
        "layer": "F", "width": 200_000, "clearance": 200_000,
        "inner_long_haul_plan": {
            "a": "U1.20", "b": "J2.5", "a_near": "F", "b_near": "F",
            "inner": ["I2", "I3"],
        },
    },
    "SPI_A_MOSI_DISPLAY": {
        "net": "/SPI_A_MOSI",
        "pads": ("U1.19", "J1.34"),
        "ignored_connected_pads": ("J2.3",),
        "layer": "F", "width": 200_000, "clearance": 200_000,
        "inner_long_haul_plan": {
            "a": "U1.19", "b": "J1.34", "a_near": "F", "b_near": "F",
            "inner": ["I2", "I3"],
        },
    },
    "SPI_A_MOSI_SD": {
        "net": "/SPI_A_MOSI",
        "pads": ("U1.19", "J2.3"),
        "ignored_connected_pads": ("J1.34",),
        "layer": "F", "width": 200_000, "clearance": 200_000,
        "inner_long_haul_plan": {
            "a": "U1.19", "b": "J2.3", "a_near": "F", "b_near": "F",
            "inner": ["I2", "I3"],
        },
    },
    "SPI_A_MISO": {
        "net": "/SPI_A_MISO",
        "pads": ("U1.21", "J2.7"),
        # R112 is deliberately DNP: fitting it would connect display SDO to
        # the microSD read bus.  Route only the fitted MCU/socket endpoints.
        "ignored_dnp_pads": ("R112.2",),
        "layer": "F",
        "width": 200_000,
        "clearance": 200_000,
        "inner_long_haul_plan": {
            "a": "U1.21", "b": "J2.7",
            "a_near": "F", "b_near": "F",
            "inner": ["I2", "I3"],
        },
    },
    "NATIVE_A": {
        "net": "/NATIVE_A",
        "pads": ("U1.31", "R61.1"),
        "layer": "F",
        "width": 200_000,
        "clearance": 200_000,
    },
    "NATIVE_B": {
        "net": "/NATIVE_B",
        "pads": ("U1.24", "R62.1"),
        "layer": "F",
        "width": 200_000,
        "clearance": 200_000,
        # The generic same-face route is a reproduced D-424 wall.  Reuse the
        # qualified low-speed endpoint-reservation framework: give each F.Cu
        # endpoint its own short escape/via, then join on a signal inner layer.
        "inner_long_haul_plan": {
            "a": "U1.24", "b": "R62.1",
            "a_near": "F", "b_near": "F",
            "inner": ["I2", "I3"],
        },
    },
    "I2S_SPK_DOUT": {
        "net": "/I2S_SPK_DOUT",
        "pads": ("U1.34", "U5.1"),
        "layer": "F",
        "width": 200_000,
        "clearance": 200_000,
        # Same-face search is unbounded in the live congestion and the
        # deterministic reserved-via screen reaches both endpoints but finds
        # no In2/In3 join.  Keep this explicit plan as the reproducible wall.
        "inner_long_haul_plan": {
            "a": "U1.34", "b": "U5.1",
            "a_near": "F", "b_near": "F",
            "inner": ["I2", "I3"],
        },
    },
    "I2S_MIC_DIN_MCU_PULLDOWN": {
        "net": "/I2S_MIC_DIN",
        "pads": ("U1.35", "R120.1"),
        "ignored_connected_pads": ("MK1.7",),
        "layer": "F", "width": 200_000, "clearance": 200_000,
        "inner_long_haul_plan": {
            "a": "U1.35", "b": "R120.1", "a_near": "F", "b_near": "F",
            "inner": ["I2", "I3"],
        },
    },
    "I2S_MIC_DIN_MCU_MIC": {
        "net": "/I2S_MIC_DIN",
        "pads": ("R120.1", "MK1.7"),
        "ignored_connected_pads": ("U1.35",),
        "layer": "F", "width": 200_000, "clearance": 200_000,
        "inner_long_haul_plan": {
            "a": "R120.1", "b": "MK1.7", "a_near": "F", "b_near": "B",
            "inner": ["I2", "I3"],
        },
    },
    "I2S_BCLK_MCU_AMP": {
        "net": "/I2S_BCLK",
        "pads": ("U1.32", "U5.16"),
        "ignored_connected_pads": ("MK1.6",),
        "layer": "F", "width": 200_000, "clearance": 200_000,
        "inner_long_haul_plan": {
            "a": "U1.32", "b": "U5.16", "a_near": "F", "b_near": "F",
            "inner": ["I2", "I3"],
        },
    },
    "I2S_BCLK_MCU_MIC": {
        "net": "/I2S_BCLK",
        "pads": ("U1.32", "MK1.6"),
        "ignored_connected_pads": ("U5.16",),
        "layer": "F", "width": 200_000, "clearance": 200_000,
        "inner_long_haul_plan": {
            "a": "U1.32", "b": "MK1.6", "a_near": "F", "b_near": "B",
            "inner": ["I2", "I3"],
        },
    },
    "I2S_LRCLK_MCU_AMP": {
        "net": "/I2S_LRCLK",
        "pads": ("U1.33", "U5.14"),
        "ignored_connected_pads": ("MK1.5",),
        "layer": "F", "width": 200_000, "clearance": 200_000,
        "inner_long_haul_plan": {
            "a": "U1.33", "b": "U5.14", "a_near": "F", "b_near": "F",
            "inner": ["I2", "I3"],
        },
    },
    "I2S_LRCLK_MCU_MIC": {
        "net": "/I2S_LRCLK",
        "pads": ("U1.33", "MK1.5"),
        "ignored_connected_pads": ("U5.14",),
        "layer": "F", "width": 200_000, "clearance": 200_000,
        "inner_long_haul_plan": {
            "a": "U1.33", "b": "MK1.5", "a_near": "F", "b_near": "B",
            "inner": ["I2", "I3"],
        },
    },
    "CC1101_GDO0": {
        "net": "/CC1101_GDO0",
        "pads": ("U1.8", "U7.15"),
        "layer": "F",
        "width": 200_000,
        "clearance": 200_000,
        "inner_long_haul_plan": {
            "a": "U1.8", "b": "U7.15",
            "a_near": "F", "b_near": "B",
            "inner": ["I2", "I3"],
        },
    },
    "BQ25185_STAT1_U2_PULLUP": {
        "net": "/BQ25185_STAT1", "pads": ("U2.9", "R127.2"),
        "ignored_connected_pads": ("U11.9", "TP6.1"),
        "layer": "B", "width": 200_000, "clearance": 200_000,
    },
    "BQ25185_STAT1_PULLUP_CHARGER": {
        "net": "/BQ25185_STAT1", "pads": ("R127.2", "U11.9"),
        "ignored_connected_pads": ("U2.9", "TP6.1"),
        "layer": "B", "width": 200_000, "clearance": 200_000,
        "inner_long_haul_plan": {
            "a": "R127.2", "b": "U11.9", "a_near": "B", "b_near": "B",
            "inner": ["I2", "I3"],
        },
    },
    "BQ25185_STAT1_PULLUP_TP": {
        "net": "/BQ25185_STAT1", "pads": ("R127.2", "TP6.1"),
        "ignored_connected_pads": ("U2.9", "U11.9"),
        "layer": "B", "width": 200_000, "clearance": 200_000,
    },
    "BQ25185_STAT2_U2_PULLUP": {
        "net": "/BQ25185_STAT2", "pads": ("U2.10", "R128.2"),
        "ignored_connected_pads": ("U11.3", "TP7.1"),
        "layer": "B", "width": 200_000, "clearance": 200_000,
    },
    "BQ25185_STAT2_PULLUP_CHARGER": {
        "net": "/BQ25185_STAT2", "pads": ("R128.2", "U11.3"),
        "ignored_connected_pads": ("U2.10", "TP7.1"),
        "layer": "B", "width": 200_000, "clearance": 200_000,
        "inner_long_haul_plan": {
            "a": "R128.2", "b": "U11.3", "a_near": "B", "b_near": "B",
            "inner": ["I2", "I3"],
        },
    },
    "BQ25185_STAT2_PULLUP_TP": {
        "net": "/BQ25185_STAT2", "pads": ("R128.2", "TP7.1"),
        "ignored_connected_pads": ("U2.10", "U11.3"),
        "layer": "B", "width": 200_000, "clearance": 200_000,
    },
    "CC1101_CS_MCU_PULLUP": {
        "net": "/CC1101_CS_N",
        "pads": ("U1.7", "R28.2"),
        "ignored_connected_pads": ("U7.19",),
        "layer": "F", "width": 200_000, "clearance": 200_000,
        "inner_long_haul_plan": {
            "a": "U1.7", "b": "R28.2", "a_near": "F", "b_near": "F",
            "inner": ["I2", "I3"],
        },
    },
    "CC1101_CS_MCU_RADIO": {
        "net": "/CC1101_CS_N",
        "pads": ("U1.7", "U7.19"),
        "ignored_connected_pads": ("R28.2",),
        "layer": "F", "width": 200_000, "clearance": 200_000,
        "inner_long_haul_plan": {
            "a": "U1.7", "b": "U7.19", "a_near": "F", "b_near": "B",
            "inner": ["I2", "I3"],
        },
    },
    "SX1262_CS_MCU_PULLUP": {
        "net": "/SX1262_CS_N",
        "pads": ("U1.10", "R27.2"),
        "ignored_connected_pads": ("U8.19",),
        "layer": "F", "width": 200_000, "clearance": 200_000,
    },
    "SX1262_CS_MCU_RADIO_DIRECT": {
        "net": "/SX1262_CS_N",
        "pads": ("U1.10", "U8.19"),
        "ignored_connected_pads": ("R27.2",),
        "layer": "F", "width": 200_000, "clearance": 200_000,
        "inner_long_haul_plan": {
            "a": "U1.10", "b": "U8.19", "a_near": "F", "b_near": "B",
            "inner": ["I2", "I3"],
        },
    },
    "SX1262_CS_MCU_RADIO": {
        "net": "/SX1262_CS_N",
        "pads": ("R27.2", "U8.19"),
        "ignored_connected_pads": ("U1.10",),
        "layer": "F", "width": 200_000, "clearance": 200_000,
        "inner_long_haul_plan": {
            "a": "R27.2", "b": "U8.19", "a_near": "F", "b_near": "B",
            "inner": ["I2", "I3"],
        },
    },
    "SX1262_RST_EXPANDER_PULLDOWN": {
        "net": "/SX1262_RST_N",
        "pads": ("U2.5", "R13.1"),
        "ignored_connected_pads": ("U8.15",),
        "layer": "B", "width": 200_000, "clearance": 200_000,
        "inner_long_haul_plan": {
            "a": "U2.5", "b": "R13.1", "a_near": "B", "b_near": "F",
            "inner": ["I2", "I3"],
        },
    },
    "SX1262_RST_PULLDOWN_RADIO": {
        "net": "/SX1262_RST_N",
        "pads": ("R13.1", "U8.15"),
        "ignored_connected_pads": ("U2.5",),
        "layer": "F", "width": 200_000, "clearance": 200_000,
        "inner_long_haul_plan": {
            "a": "R13.1", "b": "U8.15", "a_near": "F", "b_near": "B",
            "inner": ["I2", "I3"],
        },
    },
    "SX1262_RXEN_EXPANDER_PULLDOWN": {
        "net": "/SX1262_RXEN",
        "pads": ("U3.19", "R74.1"),
        "ignored_connected_pads": ("U8.6",),
        "layer": "B", "width": 200_000, "clearance": 200_000,
        "inner_long_haul_plan": {
            "a": "U3.19", "b": "R74.1", "a_near": "B", "b_near": "B",
            "inner": ["I2", "I3"],
        },
    },
    "SX1262_RXEN_PULLDOWN_RADIO": {
        "net": "/SX1262_RXEN",
        "pads": ("R74.1", "U8.6"),
        "ignored_connected_pads": ("U3.19",),
        "layer": "B", "width": 200_000, "clearance": 200_000,
        "inner_long_haul_plan": {
            "a": "R74.1", "b": "U8.6", "a_near": "B", "b_near": "B",
            "inner": ["I2", "I3"],
        },
    },
    "BOOT_MCU_PULLUP": {
        "net": "/02_MCU_CORE/BOOT_N",
        "pads": ("U1.27", "R2.2"),
        "ignored_connected_pads": ("SW1.1",),
        "layer": "F", "width": 200_000, "clearance": 200_000,
        "inner_long_haul_plan": {
            "a": "U1.27", "b": "R2.2", "a_near": "F", "b_near": "F",
            "inner": ["I2", "I3"],
        },
    },
    "BOOT_MCU_SWITCH": {
        "net": "/02_MCU_CORE/BOOT_N",
        "pads": ("U1.27", "SW1.1"),
        "ignored_connected_pads": ("R2.2",),
        "layer": "F", "width": 200_000, "clearance": 200_000,
        "inner_long_haul_plan": {
            "a": "U1.27", "b": "SW1.1", "a_near": "F", "b_near": "F",
            "inner": ["I2", "I3"],
        },
    },
    "LED_K_DISPLAY_DRIVER": {
        "net": "/03_SPI_A_DISPLAY_SD/LED_K",
        "pads": ("J1.2", "U17.3"),
        "ignored_connected_pads": ("J1.3", "R69.1"),
        # The generic inner-haul planner is intentionally limited to 0.20 mm
        # signals.  This scratch-only search width is widened to the 0.30 mm
        # backlight-current contract before the authoritative DRC gate.
        "layer": "F", "width": 200_000, "clearance": 300_000,
        "inner_long_haul_plan": {
            "a": "J1.2", "b": "U17.3", "a_near": "F", "b_near": "B",
            "inner": ["I2", "I3"],
        },
    },
    "LED_K_DRIVER_SENSE": {
        "net": "/03_SPI_A_DISPLAY_SD/LED_K",
        "pads": ("U17.3", "R69.1"),
        "ignored_connected_pads": ("J1.2", "J1.3"),
        "layer": "B", "width": 300_000, "clearance": 300_000,
    },
    "EXT_SDA_BUF_PULLUP": {
        "net": "/09_COMMUNITY_HEADER/EXT_SDA_BUF",
        "pads": ("U16.7", "R49.2"),
        "ignored_connected_pads": ("R48.1",),
        "layer": "B", "width": 200_000, "clearance": 200_000,
    },
    "EXT_SDA_BUF_SERIES": {
        "net": "/09_COMMUNITY_HEADER/EXT_SDA_BUF",
        "pads": ("U16.7", "R48.1"),
        "ignored_connected_pads": ("R49.2",),
        "layer": "B", "width": 200_000, "clearance": 200_000,
        "inner_long_haul_plan": {
            "a": "U16.7", "b": "R48.1", "a_near": "B", "b_near": "F",
            "inner": ["I2", "I3"],
        },
    },
    "EXT_SCL_BUF_PULLUP": {
        "net": "/09_COMMUNITY_HEADER/EXT_SCL_BUF",
        "pads": ("U16.2", "R50.2"),
        "ignored_connected_pads": ("R47.1",),
        "layer": "B", "width": 200_000, "clearance": 200_000,
    },
    "EXT_SCL_BUF_SERIES": {
        "net": "/09_COMMUNITY_HEADER/EXT_SCL_BUF",
        "pads": ("U16.2", "R47.1"),
        "ignored_connected_pads": ("R50.2",),
        "layer": "B", "width": 200_000, "clearance": 200_000,
        "inner_long_haul_plan": {
            "a": "U16.2", "b": "R47.1", "a_near": "B", "b_near": "F",
            "inner": ["I2", "I3"],
        },
    },
    "NFC_IRQ": {
        "net": "/NFC_IRQ",
        "pads": ("U1.11", "U9.27"),
        "layer": "F", "width": 200_000, "clearance": 200_000,
        "inner_long_haul_plan": {
            "a": "U1.11", "b": "U9.27", "a_near": "F", "b_near": "B",
            "inner": ["I2", "I3"],
        },
    },
    "SX1262_BUSY": {
        "net": "/SX1262_BUSY",
        "pads": ("U1.12", "U8.14"),
        "layer": "F", "width": 200_000, "clearance": 200_000,
        "inner_long_haul_plan": {
            "a": "U1.12", "b": "U8.14", "a_near": "F", "b_near": "B",
            "inner": ["I2", "I3"],
        },
    },
    "SX1262_DIO1": {
        "net": "/SX1262_DIO1",
        "pads": ("U2.20", "U8.13"),
        "layer": "B", "width": 200_000, "clearance": 200_000,
        "inner_long_haul_plan": {
            "a": "U2.20", "b": "U8.13", "a_near": "B", "b_near": "B",
            "inner": ["I2", "I3"],
        },
    },
    "DIO2_TXEN": {
        "net": "/04_SPI_B_RADIOS_NFC/DIO2_TXEN",
        "pads": ("U8.7", "U8.8"),
        "layer": "B",
        "width": 200_000,
        "clearance": 200_000,
    },
    "MAX17048_ALRT_N": {
        "net": "/01_POWER_TREE/MAX17048_ALRT_N",
        "pads": ("TP11.1", "U14.5"),
        "layer": "B",
        "width": 200_000,
        "clearance": 200_000,
    },
    "ILIM_VSET": {
        "net": "/01_POWER_TREE/ILIM_VSET",
        "pads": ("R36.1", "U11.7"),
        "layer": "B",
        "width": 200_000,
        "clearance": 200_000,
    },
    "ISET": {
        "net": "/01_POWER_TREE/ISET",
        "pads": ("R37.1", "U11.8"),
        "layer": "B",
        "width": 200_000,
        "clearance": 200_000,
    },
    "BQ25185_TS_MR": {
        "net": "Net-(U11-TS_MR)",
        "pads": ("U11.6", "R38.1"),
        "layer": "B",
        "width": 200_000,
        "clearance": 200_000,
        # D-448 proved U11.6 has a legal B.Cu reservation even though the
        # adjacent U11.8/U11.9 pocket is blocked.  Keep the long charger-
        # control haul off the congested component face.
        "inner_long_haul_plan": {
            "a": "U11.6", "b": "R38.1",
            "a_near": "B", "b_near": "B",
            "inner": ["I2", "I3"],
        },
    },
    "BQ25185_TS_MR_PLANAR": {
        "net": "Net-(U11-TS_MR)",
        "pads": ("U11.6", "R38.1"),
        "layer": "B",
        "width": 200_000,
        "clearance": 200_000,
    },
    "MCU_EN_U1_C1": {
        "net": "Net-(U1-EN)",
        "pads": ("U1.3", "C1.2"),
        "ignored_connected_pads": ("R1.1",),
        "layer": "F", "width": 200_000, "clearance": 200_000,
        # The same-face natural MST is the D-321 wall.  Reserve the two boxed
        # endpoints and move the short reset-sensitive leg to a signal inner.
        "inner_long_haul_plan": {
            "a": "U1.3", "b": "C1.2", "a_near": "F", "b_near": "F",
            "inner": ["I2", "I3"],
        },
    },
    "MCU_EN_C1_R1": {
        "net": "Net-(U1-EN)",
        "pads": ("C1.2", "R1.1"),
        "ignored_connected_pads": ("U1.3",),
        "layer": "F", "width": 200_000, "clearance": 200_000,
        "inner_long_haul_plan": {
            "a": "C1.2", "b": "R1.1", "a_near": "F", "b_near": "F",
            "inner": ["I2", "I3"],
        },
    },
    "DISP_BL_STRAP_U1_TP2": {
        "net": "/02_MCU_CORE/DISP_BL_CTL_STRAP",
        "pads": ("U1.16", "TP2.1"),
        "ignored_connected_pads": ("R108.1", "R109.1"),
        "layer": "F", "width": 200_000, "clearance": 200_000,
    },
    "DISP_BL_STRAP_U1_TP2_INNER": {
        "net": "/02_MCU_CORE/DISP_BL_CTL_STRAP",
        "pads": ("U1.16", "TP2.1"),
        "ignored_connected_pads": ("R108.1", "R109.1"),
        "layer": "F", "width": 200_000, "clearance": 200_000,
        "inner_long_haul_plan": {
            "a": "U1.16", "b": "TP2.1", "a_near": "F", "b_near": "F",
            "inner": ["I2", "I3"],
        },
    },
    "DISP_BL_STRAP_TP2_R109": {
        "net": "/02_MCU_CORE/DISP_BL_CTL_STRAP",
        "pads": ("TP2.1", "R109.1"),
        "ignored_connected_pads": ("U1.16", "R108.1"),
        "layer": "F", "width": 200_000, "clearance": 200_000,
    },
    "DISP_BL_STRAP_TP2_R109_INNER": {
        "net": "/02_MCU_CORE/DISP_BL_CTL_STRAP",
        "pads": ("TP2.1", "R109.1"),
        "ignored_connected_pads": ("U1.16", "R108.1"),
        "layer": "F", "width": 200_000, "clearance": 200_000,
        "inner_long_haul_plan": {
            "a": "TP2.1", "b": "R109.1", "a_near": "F", "b_near": "F",
            "inner": ["I2", "I3"],
        },
    },
    "DISP_BL_STRAP_U1_R108": {
        "net": "/02_MCU_CORE/DISP_BL_CTL_STRAP",
        "pads": ("U1.16", "R108.1"),
        "ignored_connected_pads": ("TP2.1", "R109.1"),
        "layer": "F", "width": 200_000, "clearance": 200_000,
        "inner_long_haul_plan": {
            "a": "U1.16", "b": "R108.1", "a_near": "F", "b_near": "F",
            "inner": ["I2", "I3"],
        },
    },
    "LTC4368_FAULT_TP18": {
        "net": "/01_POWER_TREE/LTC4368_FAULT_N",
        "pads": ("R82.1", "TP18.1"),
        "ignored_connected_pads": ("U18.7", "R81.2", "Q9.1"),
        "layer": "B",
        "width": 200_000,
        "clearance": 300_000,
    },
    "BTN_DOWN_U2_PULLUP": {
        "net": "/08_BUTTONS_EXPANDERS/BTN_DOWN_N",
        "pads": ("U2.14", "R5.2"),
        "ignored_connected_pads": ("SW3.1",),
        "layer": "B", "width": 200_000, "clearance": 200_000,
        "inner_long_haul_plan": {
            "a": "U2.14", "b": "R5.2", "a_near": "B", "b_near": "B",
            "inner": ["I2", "I3"],
        },
    },
    "BTN_LEFT_U2_PULLUP": {
        "net": "/08_BUTTONS_EXPANDERS/BTN_LEFT_N",
        "pads": ("U2.15", "R6.2"),
        "ignored_connected_pads": ("SW4.1",),
        "layer": "B", "width": 200_000, "clearance": 200_000,
        "inner_long_haul_plan": {
            "a": "U2.15", "b": "R6.2", "a_near": "B", "b_near": "B",
            "inner": ["I2", "I3"],
        },
    },
    "BTN_A_U2_PULLUP": {
        "net": "/08_BUTTONS_EXPANDERS/BTN_A_N",
        "pads": ("U2.17", "R8.2"),
        "ignored_connected_pads": ("SW6.1",),
        "layer": "B", "width": 200_000, "clearance": 200_000,
        "inner_long_haul_plan": {
            "a": "U2.17", "b": "R8.2", "a_near": "B", "b_near": "B",
            "inner": ["I2", "I3"],
        },
    },
    "ACC_5V_LX": {
        "net": "/01_POWER_TREE/ACC_5V_LX",
        "pads": ("U21.5", "L4.2"),
        "layer": "B",
        # Keep the complete switch node on the component-side outer layer and
        # at the locked SWITCH_NODE width floor.  Victim-net separations are
        # enforced independently by the board DRU during the full-board gate.
        "width": 400_000,
        "clearance": 200_000,
        "floor_override": {"U21.5": 200_000},
    },
    "BL_SW_U17_L3": {
        "net": "/03_SPI_A_DISPLAY_SD/BL_SW",
        "pads": ("U17.1", "L3.2"),
        "ignored_connected_pads": ("D8.2",),
        "layer": "B",
        "width": 400_000,
        "clearance": 200_000,
        # The SOT-23 driver land needs a short package neck before the
        # switch-node trunk reaches its locked 0.40 mm width.
        "floor_override": {"U17.1": 200_000},
    },
    "BL_SW_L3_D8": {
        "net": "/03_SPI_A_DISPLAY_SD/BL_SW",
        "pads": ("L3.2", "D8.2"),
        "ignored_connected_pads": ("U17.1",),
        "layer": "B",
        "width": 400_000,
        "clearance": 200_000,
        "floor_override": {"D8.2": 200_000},
    },
    "LED_A_R73_R70": {
        "net": "/03_SPI_A_DISPLAY_SD/LED_A",
        "pads": ("R73.2", "R70.2"),
        "ignored_connected_pads": ("R71.2", "R72.2", "J1.1"),
        "layer": "F", "width": 300_000, "clearance": 200_000,
    },
    "LED_A_R70_R72": {
        "net": "/03_SPI_A_DISPLAY_SD/LED_A",
        "pads": ("R70.2", "R72.2"),
        "ignored_connected_pads": ("R73.2", "R71.2", "J1.1"),
        "layer": "F", "width": 300_000, "clearance": 200_000,
    },
    "LED_A_R72_R71": {
        "net": "/03_SPI_A_DISPLAY_SD/LED_A",
        "pads": ("R72.2", "R71.2"),
        "ignored_connected_pads": ("R73.2", "R70.2", "J1.1"),
        "layer": "F", "width": 300_000, "clearance": 200_000,
    },
    "LED_A_R71_J1": {
        "net": "/03_SPI_A_DISPLAY_SD/LED_A",
        "pads": ("R71.2", "J1.1"),
        "ignored_connected_pads": ("R73.2", "R70.2", "R72.2"),
        "layer": "F", "width": 300_000, "clearance": 200_000,
    },
    "ACC_5V_ILIM": {
        "net": "/01_POWER_TREE/ACC_5V_ILIM",
        "pads": ("U22.4", "R101.1"),
        "layer": "B",
        "width": 200_000,
        "clearance": 200_000,
    },
    "ACC_5V_BOOST_EN_U3_R102": {
        "net": "/ACC_5V_BOOST_EN",
        "pads": ("U3.16", "R102.1"),
        "ignored_connected_pads": ("TP30.1", "U21.2"),
        "layer": "B", "width": 200_000, "pad_clearance": 200_000,
        "clearance": 275_000,
    },
    "ACC_5V_BOOST_EN_U3_U21_INNER": {
        "net": "/ACC_5V_BOOST_EN",
        "pads": ("U3.16", "U21.2"),
        "ignored_connected_pads": ("R102.1", "TP30.1"),
        "layer": "B", "width": 200_000, "clearance": 200_000,
        # D-443 proved that every complete planar tree crosses the already
        # accepted accessory-rail via field.  Reserve both IC escapes first
        # and carry the long control haul on a signal inner layer.
        "inner_long_haul_plan": {
            "a": "U3.16", "b": "U21.2",
            "a_near": "B", "b_near": "B",
            "inner": ["I2", "I3"],
        },
        "via_dia": 500_000,
        "via_drill": 300_000,
    },
    "ACC_5V_BOOST_EN_R102_TP30": {
        "net": "/ACC_5V_BOOST_EN",
        "pads": ("R102.1", "TP30.1"),
        "ignored_connected_pads": ("U3.16", "U21.2"),
        "layer": "B", "width": 200_000, "pad_clearance": 200_000,
        "clearance": 275_000,
    },
    "ACC_5V_BOOST_EN_TP30_U21": {
        "net": "/ACC_5V_BOOST_EN",
        "pads": ("TP30.1", "U21.2"),
        "ignored_connected_pads": ("U3.16", "R102.1"),
        "layer": "B", "width": 200_000, "pad_clearance": 200_000,
        "clearance": 275_000,
    },
    "USB_CC1": {
        "net": "Net-(J3-CC1)",
        "pads": ("J3.A5", "R31.1"),
        "layer": "F",
        "width": 200_000,
        "clearance": 200_000,
    },
    "USB_CC2": {
        "net": "Net-(J3-CC2)",
        "pads": ("J3.B5", "R30.1"),
        "layer": "F",
        "width": 200_000,
        "clearance": 200_000,
    },
    "DISP_SDO": {
        "net": "/03_SPI_A_DISPLAY_SD/DISP_SDO",
        "pads": ("J1.33", "TP36.1"),
        "ignored_dnp_pads": ("R112.1",),
        "layer": "F",
        "width": 200_000,
        "clearance": 200_000,
    },
    "USB_D_ESD_N": {
        "net": "/01_POWER_TREE/USB_D_ESD_N",
        "pads": ("R33.1", "U10.6"),
        "layer": "F",
        "width": 230_000,
        "clearance": 200_000,
    },
    "USB_D_ESD_P": {
        "net": "/01_POWER_TREE/USB_D_ESD_P",
        "pads": ("R34.1", "U10.4"),
        "layer": "F",
        "width": 230_000,
        "clearance": 200_000,
    },
    "USB_D_MCU_N": {
        "net": "/USB_D_MCU_N",
        "pads": ("R33.2", "U1.13"),
        "layer": "F",
        "width": 230_000,
        "clearance": 200_000,
    },
    "USB_D_MCU_P": {
        "net": "/USB_D_MCU_P",
        "pads": ("R34.2", "U1.14"),
        "layer": "F",
        "width": 230_000,
        "clearance": 200_000,
    },
    "XGPIO4_HDR_TVS": {
        "net": "/09_COMMUNITY_HEADER/XGPIO4_HDR",
        "pads": ("R55.2", "D4.1"),
        "ignored_connected_pads": ("J5.13",),
        "layer": "F", "width": 200_000, "pad_clearance": 200_000,
        "clearance": 275_000,
    },
    "XGPIO4_HDR_J5": {
        "net": "/09_COMMUNITY_HEADER/XGPIO4_HDR",
        "pads": ("D4.1", "J5.13"),
        "ignored_connected_pads": ("R55.2",),
        "layer": "F", "width": 200_000, "pad_clearance": 200_000,
        "clearance": 275_000,
    },
    "XGPIO5_HDR_TVS": {
        "net": "/09_COMMUNITY_HEADER/XGPIO5_HDR",
        "pads": ("R56.2", "D4.3"),
        "ignored_connected_pads": ("J5.14",),
        "layer": "F", "width": 200_000, "pad_clearance": 200_000,
        "clearance": 275_000,
    },
    "XGPIO5_HDR_J5": {
        "net": "/09_COMMUNITY_HEADER/XGPIO5_HDR",
        "pads": ("D4.3", "J5.14"),
        "ignored_connected_pads": ("R56.2",),
        "layer": "F", "width": 200_000, "pad_clearance": 200_000,
        "clearance": 275_000,
        # Keep the long header leg north-east of the accepted ACC_5V_RAW via
        # at (61.375, 34.300).  The generic diagonal clears its barrel by only
        # 0.2334 mm against the locked 0.250 mm routed-clearance rule.
        "waypoints": ((62_500_000, 30_500_000),),
    },
    "NFC_MATCH_A": {
        "net": "/04_SPI_B_RADIOS_NFC/NFC_MATCH_A",
        "pads": ("C71.2", "R114.1"),
        "layer": "B",
        "width": 300_000,
        "clearance": 200_000,
    },
    "NFC_MATCH_B": {
        "net": "/04_SPI_B_RADIOS_NFC/NFC_MATCH_B",
        "pads": ("C72.2", "R115.1"),
        "layer": "B",
        "width": 300_000,
        "clearance": 200_000,
    },
    "NFC_RFO1": {
        "net": "/04_SPI_B_RADIOS_NFC/NFC_RFO1",
        "pads": ("U9.13", "L5.1"),
        "layer": "B",
        "width": 300_000,
        # U9 is a 0.50 mm-pitch UFQFPN.  The board rules intentionally apply
        # the 0.25 mm routed-clearance floor only when neither item is a pad;
        # use the ordinary 0.20 mm package-land clearance until the trace has
        # cleared the package, then retain 0.25 mm against routed copper.
        "pad_clearance": 200_000,
        "clearance": 250_000,
    },
    "NFC_RFO2": {
        "net": "/04_SPI_B_RADIOS_NFC/NFC_RFO2",
        "pads": ("U9.15", "L6.1"),
        "layer": "B",
        "width": 300_000,
        "pad_clearance": 200_000,
        "clearance": 250_000,
    },
    "NFC_RFI1": {
        "net": "/04_SPI_B_RADIOS_NFC/NFC_RFI1",
        "pads": ("U9.22", "R116.2"),
        "layer": "B",
        "width": 300_000,
        "pad_clearance": 200_000,
        "clearance": 250_000,
        "floor_override": {"U9.22": 200_000},
    },
    "NFC_RFI2": {
        "net": "/04_SPI_B_RADIOS_NFC/NFC_RFI2",
        "pads": ("U9.23", "R117.2"),
        "layer": "B",
        "width": 300_000,
        "pad_clearance": 200_000,
        "clearance": 250_000,
        "floor_override": {"U9.23": 200_000},
    },
    "NFC_AGDC_UPPER": {
        "net": "/04_SPI_B_RADIOS_NFC/NFC_AGDC",
        "pads": ("U9.24", "C53.1"),
        "ignored_connected_pads": ("C54.1",),
        "layer": "B", "width": 300_000,
        "pad_clearance": 200_000, "clearance": 250_000,
        "floor_override": {"U9.24": 200_000},
    },
    "NFC_AGDC_LOWER": {
        "net": "/04_SPI_B_RADIOS_NFC/NFC_AGDC",
        "pads": ("U9.24", "C54.1"),
        "ignored_connected_pads": ("C53.1",),
        "layer": "B", "width": 300_000,
        "pad_clearance": 200_000, "clearance": 250_000,
        "floor_override": {"U9.24": 200_000},
    },
    "NFC_VDD_D_UPPER": {
        "net": "/04_SPI_B_RADIOS_NFC/NFC_VDD_D",
        "pads": ("U9.3", "C45.1"),
        "ignored_connected_pads": ("C46.1",),
        "layer": "B", "width": 300_000, "clearance": 200_000,
        "floor_override": {"U9.3": 200_000},
    },
    "NFC_VDD_D_LOWER": {
        "net": "/04_SPI_B_RADIOS_NFC/NFC_VDD_D",
        "pads": ("U9.3", "C46.1"),
        "ignored_connected_pads": ("C45.1",),
        "layer": "B", "width": 300_000, "clearance": 200_000,
        "floor_override": {"U9.3": 200_000},
    },
    "NFC_VDD_A_UPPER": {
        "net": "/04_SPI_B_RADIOS_NFC/NFC_VDD_A",
        "pads": ("U9.7", "C47.1"),
        "ignored_connected_pads": ("C48.1",),
        "layer": "B", "width": 300_000, "clearance": 200_000,
        "floor_override": {"U9.7": 200_000},
    },
    "NFC_VDD_A_LOWER": {
        "net": "/04_SPI_B_RADIOS_NFC/NFC_VDD_A",
        "pads": ("U9.7", "C48.1"),
        "ignored_connected_pads": ("C47.1",),
        "layer": "B", "width": 300_000, "clearance": 200_000,
        "floor_override": {"U9.7": 200_000},
    },
    "NFC_VDD_AM_UPPER": {
        "net": "/04_SPI_B_RADIOS_NFC/NFC_VDD_AM",
        "pads": ("U9.11", "C51.1"),
        "ignored_connected_pads": ("C52.1",),
        "layer": "B", "width": 300_000, "clearance": 200_000,
        "floor_override": {"U9.11": 200_000},
    },
    "NFC_VDD_AM_LOWER": {
        "net": "/04_SPI_B_RADIOS_NFC/NFC_VDD_AM",
        "pads": ("U9.11", "C52.1"),
        "ignored_connected_pads": ("C51.1",),
        "layer": "B", "width": 300_000, "clearance": 200_000,
        "floor_override": {"U9.11": 200_000},
    },
    "NFC_VDD_RF_UPPER": {
        "net": "/04_SPI_B_RADIOS_NFC/NFC_VDD_RF",
        "pads": ("U9.9", "C49.1"),
        "ignored_connected_pads": ("U9.14", "C50.1"),
        "layer": "B", "width": 300_000, "clearance": 200_000,
        "floor_override": {"U9.9": 200_000},
    },
    "NFC_VDD_RF_LOWER": {
        "net": "/04_SPI_B_RADIOS_NFC/NFC_VDD_RF",
        "pads": ("U9.14", "C50.1"),
        "ignored_connected_pads": ("U9.9", "C49.1"),
        "layer": "B", "width": 300_000, "clearance": 200_000,
        "floor_override": {"U9.14": 200_000},
    },
    "NFC_VDD_RF_CAP_JOIN": {
        "net": "/04_SPI_B_RADIOS_NFC/NFC_VDD_RF",
        "pads": ("C49.1", "C50.1"),
        "ignored_connected_pads": ("U9.9", "U9.14"),
        "layer": "B", "width": 300_000, "clearance": 200_000,
    },
    "NFC_RXA_UPPER": {
        "net": "/04_SPI_B_RADIOS_NFC/NFC_RXA",
        "pads": ("C75.2", "C76.1"),
        "ignored_connected_pads": ("R116.1",),
        "layer": "B",
        "width": 300_000,
        "clearance": 250_000,
    },
    "NFC_RXA_LOWER": {
        "net": "/04_SPI_B_RADIOS_NFC/NFC_RXA",
        "pads": ("C76.1", "R116.1"),
        "ignored_connected_pads": ("C75.2",),
        "layer": "B",
        "width": 300_000,
        "clearance": 250_000,
    },
    "NFC_RXB_LOWER": {
        "net": "/04_SPI_B_RADIOS_NFC/NFC_RXB",
        "pads": ("C77.2", "C78.1"),
        "ignored_connected_pads": ("R117.1",),
        "layer": "B",
        "width": 300_000,
        "clearance": 250_000,
    },
    "NFC_RXB_UPPER": {
        "net": "/04_SPI_B_RADIOS_NFC/NFC_RXB",
        "pads": ("C78.1", "R117.1"),
        "ignored_connected_pads": ("C77.2",),
        "layer": "B",
        "width": 300_000,
        "clearance": 250_000,
    },
    "NFC_XIN_CRYSTAL": {
        "net": "/04_SPI_B_RADIOS_NFC/NFC_XIN",
        "pads": ("U9.5", "Y1.3"),
        "ignored_connected_pads": ("C80.1",),
        "layer": "B",
        "width": 200_000,
        "clearance": 200_000,
    },
    "NFC_XIN_CAP": {
        "net": "/04_SPI_B_RADIOS_NFC/NFC_XIN",
        "pads": ("Y1.3", "C80.1"),
        "ignored_connected_pads": ("U9.5",),
        "layer": "B",
        "width": 200_000,
        "clearance": 200_000,
    },
    "NFC_XOUT_CRYSTAL": {
        "net": "/04_SPI_B_RADIOS_NFC/NFC_XOUT",
        "pads": ("U9.4", "Y1.1"),
        "ignored_connected_pads": ("C79.1",),
        "layer": "B",
        "width": 200_000,
        "clearance": 200_000,
    },
    "NFC_XOUT_CAP": {
        "net": "/04_SPI_B_RADIOS_NFC/NFC_XOUT",
        "pads": ("Y1.1", "C79.1"),
        "ignored_connected_pads": ("U9.4",),
        "layer": "B",
        "width": 200_000,
        "clearance": 200_000,
    },
    "NFC_EMCA_L": {
        "net": "/04_SPI_B_RADIOS_NFC/NFC_EMCA",
        "pads": ("L5.2", "C71.1"),
        "ignored_connected_pads": ("C69.1", "C73.1"),
        "layer": "B", "width": 300_000, "clearance": 250_000,
    },
    "NFC_EMCA_SHUNT": {
        "net": "/04_SPI_B_RADIOS_NFC/NFC_EMCA",
        "pads": ("C71.1", "C73.1"),
        "ignored_connected_pads": ("C69.1", "L5.2"),
        "layer": "B", "width": 300_000, "clearance": 250_000,
    },
    "NFC_EMCA_CAP": {
        "net": "/04_SPI_B_RADIOS_NFC/NFC_EMCA",
        "pads": ("C73.1", "C69.1"),
        "ignored_connected_pads": ("C71.1", "L5.2"),
        "layer": "B", "width": 300_000, "clearance": 250_000,
    },
    "NFC_EMCB_L": {
        "net": "/04_SPI_B_RADIOS_NFC/NFC_EMCB",
        "pads": ("L6.2", "C72.1"),
        "ignored_connected_pads": ("C70.1", "C74.1"),
        "layer": "B", "width": 300_000, "clearance": 250_000,
    },
    "NFC_EMCB_SHUNT": {
        "net": "/04_SPI_B_RADIOS_NFC/NFC_EMCB",
        "pads": ("C72.1", "C74.1"),
        "ignored_connected_pads": ("C70.1", "L6.2"),
        "layer": "B", "width": 300_000, "clearance": 250_000,
    },
    "NFC_EMCB_CAP": {
        "net": "/04_SPI_B_RADIOS_NFC/NFC_EMCB",
        "pads": ("C74.1", "C70.1"),
        "ignored_connected_pads": ("C72.1", "L6.2"),
        "layer": "B", "width": 300_000, "clearance": 250_000,
    },
    "NFC_ANTA_MATCH": {
        "net": "/04_SPI_B_RADIOS_NFC/NFC_ANT_A",
        "pads": ("R114.2", "C75.1"),
        "ignored_connected_pads": ("J7.1", "TP37.1"),
        "layer": "B", "width": 300_000, "clearance": 250_000,
    },
    "NFC_ANTA_CONN": {
        "net": "/04_SPI_B_RADIOS_NFC/NFC_ANT_A",
        "pads": ("C75.1", "J7.1"),
        "ignored_connected_pads": ("R114.2", "TP37.1"),
        "layer": "B", "width": 300_000, "clearance": 250_000,
    },
    "NFC_ANTA_TP": {
        "net": "/04_SPI_B_RADIOS_NFC/NFC_ANT_A",
        "pads": ("R114.2", "TP37.1"),
        "ignored_connected_pads": ("C75.1", "J7.1"),
        "layer": "B", "width": 300_000, "clearance": 250_000,
    },
    "NFC_ANTB_MATCH": {
        "net": "/04_SPI_B_RADIOS_NFC/NFC_ANT_B",
        "pads": ("R115.2", "C77.1"),
        "ignored_connected_pads": ("J7.2", "TP38.1"),
        "layer": "B", "width": 300_000, "clearance": 250_000,
    },
    "NFC_ANTB_CONN": {
        "net": "/04_SPI_B_RADIOS_NFC/NFC_ANT_B",
        "pads": ("C77.1", "J7.2"),
        "ignored_connected_pads": ("R115.2", "TP38.1"),
        "layer": "B", "width": 300_000, "clearance": 250_000,
    },
    "NFC_ANTB_TP": {
        "net": "/04_SPI_B_RADIOS_NFC/NFC_ANT_B",
        "pads": ("R115.2", "TP38.1"),
        "ignored_connected_pads": ("C77.1", "J7.2"),
        "layer": "B", "width": 300_000, "clearance": 250_000,
    },
}


def ledger_net(board: Path, net: str, report: Path):
    subprocess.run([
        sys.executable, str(ROOT / "hardware/demo/manufacturing/routing_ledger.py"),
        "--board", str(board), str(report),
    ], check=True, text=True, capture_output=True)
    ledger = json.loads(report.read_text())
    return next(item for item in ledger["nets"] if item["net"] == net)


def route(path: Path, name: str):
    rule = ROUTES[name]
    board = qr.QBoard(path)
    ir.inject_existing_via_obstacles(board)
    pads = {p["ref"]: p for p in ir.physical_net_pads(board, rule["net"])}
    ignored = set(rule.get("ignored_dnp_pads", ())) | set(
        rule.get("ignored_connected_pads", ())
    )
    unexpected_ignored = ignored - set(pads)
    if unexpected_ignored:
        raise RuntimeError(f"missing declared DNP pads: {sorted(unexpected_ignored)}")
    pads = {ref: pad for ref, pad in pads.items() if ref not in ignored}
    if set(pads) != set(rule["pads"]):
        raise RuntimeError(f"unexpected fitted pads: {sorted(pads)}")
    a, b = (pads[ref] for ref in rule["pads"])
    if rule.get("inner_long_haul_plan"):
        group = {
            "width": rule["width"],
            "clr_pad": rule.get("pad_clearance", rule["clearance"]),
            "clr_trk": rule["clearance"],
            "via_dia": rule.get("via_dia", 600_000),
            "via_drill": rule.get("via_drill", 300_000),
            "inner_long_haul_plan": rule["inner_long_haul_plan"],
        }
        attempts = ir.route_inner_long_haul_plan(
            board, rule["net"], list(pads.values()), group
        )
        result = attempts[-1][3]
        result["attempt"] = attempts[-1][2]
        result["inner"] = attempts[-1][4]
    elif rule.get("waypoints"):
        nodes = [a] + [
            {"ref": f"(waypoint-{index})", "x": x, "y": y,
             "anchor": True, "net": rule["net"]}
            for index, (x, y) in enumerate(rule["waypoints"], 1)
        ] + [b]
        legs = []
        for left, right in zip(nodes, nodes[1:]):
            leg = qr.connect_role(
                board, rule["net"], left, right, rule["layer"], rule["width"],
                rule.get("pad_clearance", rule["clearance"]), rule["clearance"],
                G=25_000,
            )
            legs.append(leg)
            if not leg.get("ok"):
                break
        result = {
            "ok": len(legs) == len(nodes) - 1 and all(leg.get("ok") for leg in legs),
            "waypoints": [[x / 1e6, y / 1e6] for x, y in rule["waypoints"]],
            "legs": legs,
            "mm": sum(leg.get("mm", 0) for leg in legs),
        }
    elif rule.get("floor_override"):
        result = qr.connect(
            board, rule["net"], a, b, rule["layer"], rule["width"],
            rule["width"], rule.get("pad_clearance", rule["clearance"]),
            rule["clearance"], G=25_000,
            floor_override=rule["floor_override"],
        )
    else:
        result = qr.connect_role(
            board, rule["net"], a, b, rule["layer"], rule["width"],
            rule.get("pad_clearance", rule["clearance"]), rule["clearance"],
            G=25_000,
        )
    board.save(path)
    print(json.dumps({"name": name, "rule": rule, "result": result}, sort_keys=True))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("name", choices=sorted(ROUTES))
    parser.add_argument("--route", type=Path, help=argparse.SUPPRESS)
    parser.add_argument("--candidate", type=Path)
    parser.add_argument("--promote", action="store_true")
    args = parser.parse_args()
    if args.route:
        route(args.route, args.name)
        return 0

    before = hashlib.sha256(BOARD.read_bytes()).hexdigest()
    with tempfile.TemporaryDirectory(prefix="aqroot-demo-local-") as temporary:
        before_net = ledger_net(
            BOARD, ROUTES[args.name]["net"], Path(temporary) / "before-ledger.json"
        )
        scratch = Path(temporary) / BOARD.name
        for suffix in (".kicad_pcb", ".kicad_dru", ".kicad_pro"):
            scratch.with_suffix(suffix).write_bytes(BOARD.with_suffix(suffix).read_bytes())
        routed = json.loads(subprocess.run(
            [sys.executable, __file__, args.name, "--route", str(scratch)],
            check=True, text=True, capture_output=True,
        ).stdout)
        drc = Path(temporary) / "drc.json"
        completed = subprocess.run([
            "kicad-cli", "pcb", "drc", "--refill-zones", "--save-board",
            "--format", "json", "--units", "mm", "--severity-all",
            "--schematic-parity", "-o", str(drc), str(scratch),
        ], text=True, capture_output=True)
        violations = json.loads(drc.read_text()).get("violations", [])
        accepted = {"lib_footprint_issues", "hole_clearance", "solder_mask_bridge"}
        attributable = [v for v in violations if v.get("type") not in accepted]
        types = {}
        for violation in violations:
            kind = violation.get("type", "unknown")
            types[kind] = types.get(kind, 0) + 1
        candidate = scratch.read_bytes()
        after_net = ledger_net(
            scratch, ROUTES[args.name]["net"], Path(temporary) / "after-ledger.json"
        )
    connectivity_progress = after_net["open_edges"] < before_net["open_edges"]
    promotion = (
        routed["result"].get("ok", False)
        and not attributable
        and connectivity_progress
    )
    if args.candidate and promotion:
        args.candidate.write_bytes(candidate)
    if args.promote:
        if not promotion or before != hashlib.sha256(BOARD.read_bytes()).hexdigest():
            raise RuntimeError("refuse promotion: gate failed or authority changed")
        BOARD.write_bytes(candidate)
    print(json.dumps({
        "schema": 1, "authoritative_board_sha256": before,
        "authoritative_unchanged": before == hashlib.sha256(BOARD.read_bytes()).hexdigest(),
        "route": routed, "drc_exit": completed.returncode, "drc_types": types,
        "attributable_drc": attributable, "promotion_candidate": promotion,
        "connectivity": {
            "before_open_edges": before_net["open_edges"],
            "after_open_edges": after_net["open_edges"],
            "progress": connectivity_progress,
        },
        "candidate_sha256": hashlib.sha256(candidate).hexdigest(),
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
