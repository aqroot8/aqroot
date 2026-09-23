# -*- coding: utf-8 -*-
"""AQROOT Demo -- D-797 / D797-05 (Astra R16-03, Fable R16-02).
THE MEANING OF EVERY GUARANTEE KEY, PINNED WHERE THE REGISTRY CANNOT REACH IT.

ROUND-16: after D-796 the verifier re-derived symbol, header, column, unit and
condition from the document -- but it compared them against the registry's
narrative `source` text and the evidence JSON's own claims.  Both are
editable.  A COORDINATED edit (registry source + evidence row + re-pinned
evidence sha256) could re-point a key at a GENUINE row of the same hashed PDF
with the same number but another parameter (VLOWV -> VIN_LOWVZ, both 3.1 V
MAX) or another condition (VBUVLO_HYS VIN = 5 V -> the VIN = 0 V sibling), and
every check agreed with every other check.

THIS FILE IS THE INDEPENDENT AUTHORITY FOR WHAT A KEY MEANS.  It is controlled
verifier code, not evidence: `guarantee_evidence.py` pins its sha256
(`SEMANTICS_SHA256`), loads it by `ast.literal_eval` only (a statement that is
not a literal assignment is refused), and compares the DOCUMENT-DERIVED row
against it field by field.  The registry and the evidence JSON may agree with
this file; they can never redefine it.  The key sets must be EQUAL: a
GUARANTEED_* registry key absent here fails, and a key here that the registry
does not tag GUARANTEED_* fails.

Per key:
  document         a DOCUMENTS id; path + sha256 are pinned below, and the
                   file on disk and the evidence's document entry must both be
                   those bytes at that path
  line             0-based line of the document's `pdftotext -layout` text
  row_sha256       sha256 of that line, whitespace-normalised (the verifier's
                   `_norm`), i.e. the row's own text fingerprint
  symbol           the primary symbol the DOCUMENT gives the row (own symbol
                   cell, sub-row symbol, item number, list code)
  parameter        phrases that must occur in the row's own block (its
                   condition context plus its symbol's line) -- the parameter
                   NAME, which a same-valued foreign row does not carry
  condition        the operating condition that distinguishes this row from
                   its siblings; `condition_scope` says where it must be:
                   VALUE_LINE (on the line that carries the value -- a sibling
                   sub-row's continuation never counts), ROW_CONTEXT (the
                   row's own wrapped condition cell), or None
  table            header_line / header_text (the MIN/TYP/MAX or REQUIREMENT
                   header the row is read under), title (must be in the
                   document's preamble above that header), condition (the
                   table's own blanket condition, or None)
  published_columns  the columns (or direction mark) the row publishes
  value_token      the document's numeric token for the guaranteed value
  unit             the row's own unit token; `dimension` its SI dimension --
                   the registry value must equal value_token x canonical
                   scale(unit), so the schema pins the QUANTITY, not a number
  direction        MIN or MAX, the bound the document publishes
  tag              the registry tag this meaning licenses
"""

SEMANTICS_SCHEMA = "aqroot-guarantee-semantics/1"

DOCUMENTS = {
    "SLUSF65B": {
        "path": "hardware/demo/kicad/aqroot-demo/vendor/BQ25185/"
                "ti-bq25185-slusf65b-2026-08.pdf",
        "sha256": "c73ed7d63e6532bb05e26df30edd37c6ac2de310c1222a84a77625e15e133684",
        "token": "SLUSF65B",
    },
    "ESPRESSIF": {
        "path": "hardware/demo/kicad/aqroot-demo/vendor/Espressif/"
                "esp32-s3-wroom-1-datasheet.pdf",
        "sha256": "27d71971da07c280c6068d08c74720d1a25b8f20cf8494dc1765bdd28d40d435",
        "token": "Espressif",
    },
    "MOLEX_PS": {
        "path": "hardware/demo/kicad/aqroot-demo/vendor/MOLEX/"
                "molex-5055700003-PS-A1.pdf",
        "sha256": "0218c6300aa4e4b4906e7607b7e033ece51c2adc6439ae8be90ce8e659942440",
        "token": "5055700003-PS",
    },
    "PACK": {
        "path": "hardware/demo/kicad/aqroot-demo/vendor/BATTERY/"
                "adafruit-328-785060-specification.pdf",
        "sha256": "826149daa4aa9ba3ab7b635993a022d6521572a44d1d0588171468507b58ecd3",
        "token": "785060",
    },
    "BOURNS_CRA": {
        "path": "hardware/demo/kicad/aqroot-demo/vendor/BOURNS/"
                "bourns-cra-series.pdf",
        "sha256": "1f164410b98c77f69adae78fea4fba158b47fd35c14c241f5af7321b380ee362",
        "token": "Bourns",
    },
}

# The two SLUSF65B Electrical Characteristics tables (page 1 and continued).
_TI_EC_HEADER = "PARAMETER TEST CONDITIONS MIN TYP MAX UNIT"
_TI_TJ = "-40°C < TJ < 125°C"

KEYS = {
    # ---------------------------------------------------------- BQ25185 --
    "bq.ilim_min_A": {
        "document": "SLUSF65B", "line": 310,
        "row_sha256": "736d0fb9e5997392d372dfbc398cb034e8e123dab50c3adc00aac47e17877ef9",
        "symbol": "ILIM", "parameter": ["Input current limit"],
        "condition": "VIN = 5V, ILIM = 1050mA", "condition_scope": "VALUE_LINE",
        "table": {"header_line": 267, "header_text": _TI_EC_HEADER,
                  "title": "5.5 Electrical Characteristics",
                  "condition": _TI_TJ},
        "published_columns": ["MIN", "TYP", "MAX"],
        "value_token": "995", "unit": "mA", "dimension": "A",
        "direction": "MIN", "tag": "GUARANTEED_MIN",
    },
    "bq.ilim_max_A": {
        "document": "SLUSF65B", "line": 310,
        "row_sha256": "736d0fb9e5997392d372dfbc398cb034e8e123dab50c3adc00aac47e17877ef9",
        "symbol": "ILIM", "parameter": ["Input current limit"],
        "condition": "VIN = 5V, ILIM = 1050mA", "condition_scope": "VALUE_LINE",
        "table": {"header_line": 267, "header_text": _TI_EC_HEADER,
                  "title": "5.5 Electrical Characteristics",
                  "condition": _TI_TJ},
        "published_columns": ["MIN", "TYP", "MAX"],
        "value_token": "1100", "unit": "mA", "dimension": "A",
        "direction": "MAX", "tag": "GUARANTEED_MAX",
    },
    "bq.vsys_reg_accuracy": {
        "document": "SLUSF65B", "line": 337,
        "row_sha256": "fcc5930f73403b96c581860fb20fe23637a7701bc2592976a64d4550e8e9f2db",
        "symbol": "VSYS_REG_ACC", "parameter": ["SYS regulation accuracy"],
        "condition": "VIN = 5V, VBAT = 3.6V, RSYS = 100Ω",
        "condition_scope": "VALUE_LINE",
        "table": {"header_line": 332, "header_text": _TI_EC_HEADER,
                  "title": "5.5 Electrical Characteristics (continued)",
                  "condition": _TI_TJ},
        "published_columns": ["MIN", "MAX"],
        "value_token": "2", "unit": "%", "dimension": "1",
        "direction": "MAX", "tag": "GUARANTEED_MAX",
    },
    "bq.ron_bat_max_ohm": {
        "document": "SLUSF65B", "line": 346,
        "row_sha256": "dc5628fbb1d1ae8fbab69e549ad564a7b92b687462dfcedceb13e0ca8ec3c08a",
        "symbol": "RON_BAT", "parameter": ["Battery FET on-resistance"],
        "condition": "VBAT = 4.5V, IBAT = 400mA",
        "condition_scope": "VALUE_LINE",
        "table": {"header_line": 332, "header_text": _TI_EC_HEADER,
                  "title": "5.5 Electrical Characteristics (continued)",
                  "condition": _TI_TJ},
        "published_columns": ["TYP", "MAX"],
        "value_token": "140", "unit": "mΩ", "dimension": "ohm",
        "direction": "MAX", "tag": "GUARANTEED_MAX",
    },
    "bq.ron_in_max_ohm": {
        "document": "SLUSF65B", "line": 347,
        "row_sha256": "dae551f17ef7cac064560407869550b2bd3de742d52b49a9490c5c6aa3312036",
        "symbol": "RON_IN", "parameter": ["Input FET on-resistance"],
        "condition": "VIN = 5V, IIN = 1A", "condition_scope": "VALUE_LINE",
        "table": {"header_line": 332, "header_text": _TI_EC_HEADER,
                  "title": "5.5 Electrical Characteristics (continued)",
                  "condition": _TI_TJ},
        "published_columns": ["TYP", "MAX"],
        "value_token": "470", "unit": "mΩ", "dimension": "ohm",
        "direction": "MAX", "tag": "GUARANTEED_MAX",
    },
    "bq.kiset_min_AOhm": {
        "document": "SLUSF65B", "line": 357,
        "row_sha256": "6124d28ca53c45f341e3aac2a17a0af8b8373930ca7fde24f6beadd5e935571e",
        "symbol": "KISET", "parameter": ["Charge current setting factor"],
        "condition": "10mA < ICHG < 1000mA", "condition_scope": "VALUE_LINE",
        "table": {"header_line": 332, "header_text": _TI_EC_HEADER,
                  "title": "5.5 Electrical Characteristics (continued)",
                  "condition": _TI_TJ},
        "published_columns": ["MIN", "TYP", "MAX"],
        "value_token": "285", "unit": "AΩ", "dimension": "AOhm",
        "direction": "MIN", "tag": "GUARANTEED_MIN",
    },
    "bq.kiset_max_AOhm": {
        "document": "SLUSF65B", "line": 357,
        "row_sha256": "6124d28ca53c45f341e3aac2a17a0af8b8373930ca7fde24f6beadd5e935571e",
        "symbol": "KISET", "parameter": ["Charge current setting factor"],
        "condition": "10mA < ICHG < 1000mA", "condition_scope": "VALUE_LINE",
        "table": {"header_line": 332, "header_text": _TI_EC_HEADER,
                  "title": "5.5 Electrical Characteristics (continued)",
                  "condition": _TI_TJ},
        "published_columns": ["MIN", "TYP", "MAX"],
        "value_token": "315", "unit": "AΩ", "dimension": "AOhm",
        "direction": "MAX", "tag": "GUARANTEED_MAX",
    },
    "bq.iprechg_accuracy": {
        # NOT ICHG_ACC (line 359): the fast-charge accuracy row publishes the
        # same -10 / +10 % and is a different parameter.
        "document": "SLUSF65B", "line": 368,
        "row_sha256": "ba0a8aa7be838a262fa190a7c0f68ba54daa24a1230a588b17e7bdfbfbd0f8e9",
        "symbol": "IPRECHG_ACC", "parameter": ["Precharge current accuracy"],
        "condition": "Fast charge current ≥ 40mA",
        "condition_scope": "VALUE_LINE",
        "table": {"header_line": 332, "header_text": _TI_EC_HEADER,
                  "title": "5.5 Electrical Characteristics (continued)",
                  "condition": _TI_TJ},
        "published_columns": ["MIN", "MAX"],
        "value_token": "10", "unit": "%", "dimension": "1",
        "direction": "MAX", "tag": "GUARANTEED_MAX",
    },
    "bq.vlowv_min_V": {
        "document": "SLUSF65B", "line": 386,
        "row_sha256": "b4f873a0bba0a2d36b94fa2ea18d750223cfa21ccdfbcf5138344400cddc9ff4",
        "symbol": "VLOWV",
        "parameter": ["Precharge to fast charge transition"],
        "condition": "VBAT rising", "condition_scope": "VALUE_LINE",
        "table": {"header_line": 332, "header_text": _TI_EC_HEADER,
                  "title": "5.5 Electrical Characteristics (continued)",
                  "condition": _TI_TJ},
        "published_columns": ["MIN", "TYP", "MAX"],
        "value_token": "2.9", "unit": "V", "dimension": "V",
        "direction": "MIN", "tag": "GUARANTEED_MIN",
    },
    "bq.vlowv_max_V": {
        # NOT VIN_LOWVZ (line 284, "VIN threshold to stop charging", VIN
        # falling, 2.95 TYP / 3.1 MAX V): same number, same column, same
        # unit, same PDF -- another parameter.
        "document": "SLUSF65B", "line": 386,
        "row_sha256": "b4f873a0bba0a2d36b94fa2ea18d750223cfa21ccdfbcf5138344400cddc9ff4",
        "symbol": "VLOWV",
        "parameter": ["Precharge to fast charge transition"],
        "condition": "VBAT rising", "condition_scope": "VALUE_LINE",
        "table": {"header_line": 332, "header_text": _TI_EC_HEADER,
                  "title": "5.5 Electrical Characteristics (continued)",
                  "condition": _TI_TJ},
        "published_columns": ["MIN", "TYP", "MAX"],
        "value_token": "3.1", "unit": "V", "dimension": "V",
        "direction": "MAX", "tag": "GUARANTEED_MAX",
    },
    "bq.vbuvlo_hys_max_V": {
        # The VIN = 5 V sub-row.  Line 391 is its VIN = 0 V sibling
        # (90 / 150 / 210 mV) -- same symbol, same parameter, another
        # operating condition; it is NOT this key.
        "document": "SLUSF65B", "line": 390,
        "row_sha256": "a1674562d58a43a30b78fcb776e2cc7f23588c4fe3ec61d2dfa6472bb0cbd0f9",
        "symbol": "VBUVLO_HYS", "parameter": ["Battery UVLO hysteresis"],
        "condition": "VBAT rising, VIN = 5V", "condition_scope": "VALUE_LINE",
        "table": {"header_line": 332, "header_text": _TI_EC_HEADER,
                  "title": "5.5 Electrical Characteristics (continued)",
                  "condition": _TI_TJ},
        "published_columns": ["MIN", "TYP", "MAX"],
        "value_token": "190", "unit": "mV", "dimension": "V",
        "direction": "MAX", "tag": "GUARANTEED_MAX",
    },
    # -------------------------------------------------- ESP32-S3-WROOM-1 --
    "mcu.ivdd_supply_requirement_A": {
        # a requirement ON THE SUPPLY (Recommended Operating Conditions), MIN
        "document": "ESPRESSIF", "line": 1596,
        "row_sha256": "0d49cf5029a0f5cb2361c4cfb61fb55934899821f4fea13b5ede34b5902eee15",
        "symbol": "IV DD",
        "parameter": ["Current delivered by external power supply"],
        "condition": None, "condition_scope": None,
        "table": {"header_line": 1594,
                  "header_text": "Symbol Parameter Min Typ Max Unit",
                  "title": "Table 6-2. Recommended Operating Conditions",
                  "condition": "Recommended Operating Conditions"},
        "published_columns": ["MIN"],
        "value_token": "0.5", "unit": "A", "dimension": "A",
        "direction": "MIN", "tag": "GUARANTEED_ROC",
    },
    # ------------------------------------------------ Molex 5055700003-PS --
    "path.microlock_contact_initial_max_ohm": {
        "document": "MOLEX_PS", "line": 221,
        "row_sha256": "bb1dba0ed69eef2af5f8fae57c785d4c0430e36fa4967a606ae6eb4e411533f9",
        "symbol": "6.1.1", "parameter": ["Contact Resistance"],
        "condition": "Mate connectors and measured by dry circuit",
        "condition_scope": "ROW_CONTEXT",
        "table": {"header_line": 218,
                  "header_text": "ITEM DESCRIPTION TEST CONDITION REQUIREMENT",
                  "title": "6.1 ELECTRICAL PERFORMANCE", "condition": None},
        "published_columns": ["MAX_WORD"],
        "value_token": "20", "unit": "milliohms", "dimension": "ohm",
        "direction": "MAX", "tag": "GUARANTEED_MAX",
    },
    "path.crimp_max_ohm": {
        "document": "MOLEX_PS", "line": 236,
        "row_sha256": "dc62b60fabd3ff30ad69c83ad74aa8d2c85faea97d58816652fa670a5e6402f9",
        "symbol": "6.1.4",
        "parameter": ["Contact Resistance on", "crimped portion"],
        "condition": "Crimp the applicable wire to the terminal",
        "condition_scope": "ROW_CONTEXT",
        "table": {"header_line": 218,
                  "header_text": "ITEM DESCRIPTION TEST CONDITION REQUIREMENT",
                  "title": "6.1 ELECTRICAL PERFORMANCE", "condition": None},
        "published_columns": ["MAX_WORD"],
        "value_token": "5", "unit": "milliohms", "dimension": "ohm",
        "direction": "MAX", "tag": "GUARANTEED_MAX",
    },
    "path.microlock_contact_aged_max_ohm": {
        "document": "MOLEX_PS", "line": 318,
        "row_sha256": "83c6b28e2a456465b3f7e1d0ad5b217e51f521f70475ebebc38088a574d15696",
        "symbol": "6.2.6",
        "parameter": ["Repeated", "Insertion / Withdrawal", "Contact",
                      "Resistance"],
        "condition": "Insert and withdraw connectors up to 30",
        "condition_scope": "ROW_CONTEXT",
        "table": {"header_line": 316,
                  "header_text": "ITEM DESCRIPTION TEST CONDITION REQUIREMENT",
                  "title": "6.2 MECHANICAL PERFORMANCE CONTINUED",
                  "condition": None},
        "published_columns": ["MAX_WORD"],
        "value_token": "40", "unit": "milliohms", "dimension": "ohm",
        "direction": "MAX", "tag": "GUARANTEED_MAX",
    },
    # ------------------------------------------------------ 785060 pack --
    "path.pack_ac_impedance_max_ohm": {
        "document": "PACK", "line": 64,
        "row_sha256": "13a84738dccc66348cf87a236ed3dc94b7bf56957b830b6f7c5f6406cb3eb8b1",
        "symbol": "Impedance", "parameter": ["Impedance"],
        "condition": "AC 1KHz after 50% charge,25℃",
        "condition_scope": "VALUE_LINE",
        "table": {"header_line": 55,
                  "header_text": "Item Specifications Remark",
                  "title": "3、 Specification", "condition": None},
        "published_columns": ["LE_SIGN"],
        "value_token": "35", "unit": "mΩ", "dimension": "ohm",
        "direction": "MAX", "tag": "GUARANTEED_MAX",
    },
    # --------------------------------------------------------- Bourns CRA --
    "path.r75_sense_tolerance": {
        "document": "BOURNS_CRA", "line": 165,
        "row_sha256": "1419f835cdba409a0bad2f1bc4e318f3c74c5ac0b1e34ebe60a9cbc4e83405d5",
        "symbol": "F", "parameter": ["Resistance Tolerance"],
        "condition": None, "condition_scope": None,
        "table": {"header_line": None, "header_text": "Resistance Tolerance",
                  "title": None, "condition": None},
        "published_columns": ["PLUS_MINUS"],
        "value_token": "1", "unit": "%", "dimension": "1",
        "direction": "MAX", "tag": "GUARANTEED_MAX",
    },
}
