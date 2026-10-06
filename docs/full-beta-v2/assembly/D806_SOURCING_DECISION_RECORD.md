# D-806 — SOURCING DECISION RECORD (BOM SHORTAGES / CONSIGNMENT)

**No substitution is made or authorized by D-806.  No procurement — cancellable or not — is
authorized by this record or by any D-806 RFQ package.**  Every MPN below is the exact approved
D-805 MPN; the BOM files are byte-identical to D-805.

## Evidence and its age

* Stock: `hardware/demo/manufacturing/evidence/d803-sourcing-sweep.json` (D-803 live JLCPCB
  parts-API sweep, run 2026-09-26T11:06:44Z–11:07:48Z; raw records in `evidence/jlc-live/`).
  **The counts are 10 days old on 2026-10-06.  A fresh `--refresh` sweep is a standing pre-order
  gate (`assembly/SOURCING_LEDGER.md`); archived counts are not purchasing authority.**
* Franchised-distributor status is on record only for MK1 and J5 (`evidence/d800-broadline-check.json`, 2026-09-24).
* JLCPCB "global sourcing" status is not recorded for any part (unknown).
* Need: 2 PCBAs = BOM qty x 2 (plus vendor attrition, to be quoted).

## Classification

Classes: **(a)** vendor sources the exact MPN; **(b)** owner-supplied / consigned exact MPN;
**(c)** approved-equivalent candidate requiring owner approval; **(d)** hand-installed /
post-reflow by design.  **Fine-pitch IC, RF and power parts default to VENDOR MACHINE ASSEMBLY
even when consigned.**

| refs | exact MPN | LCSC | JLC stock 2026-09-26 (need for 2) | class | assembly | note |
|---|---|---|---|---|---|---|
| U9 | ST25R3916-AQET | C5267441 | **0** (2) | **(b)** consign | vendor, X-ray | UFQFPN-32 0.5 mm; NFC tuning caps take no substitute |
| U18 | LTC4368IMS-1#TRPBF | C688401 | **0** (2) | **(b)** consign | vendor | MSOP-10 0.5 mm, battery protection |
| U19 | TLV7032DDFR | C2871498 | **0** (2) | **(b)** consign | vendor | SOT-23-8 |
| U2, U3 | PCAL9535APW,118 | C2669683 | **1** (4) | **(b)** consign | vendor | TSSOP-24 0.65 mm |
| D2, D4, D5 | TPD4E1B06DRLR | C1972953 | **2** (6; MOQ 31) | **(b)** consign | vendor | SOT-563 0.5 mm |
| L4 | 74438357010 | C5542269 | **0** (2) | **(b)** consign | vendor | power inductor; distributor stock not recorded |
| MK1 | DMM-4026-B-I2S-R | C3171792 | **0**; LCSC listing flagged "no longer manufactured" (2) | **(b)** consign | vendor | DigiKey Active 4,792 (2026-09-24); bottom-port MEMS, port must stay unobstructed |
| R40 | RT0603BRD07189KL | C861174 | 143, **MOQ 302 > stock** (2) | **(a)** only if the owner accepts the MOQ buy, else **(b)** | vendor | 0.1 % divider resistor; no equivalent proposed |
| J5 | SSQ-124-02-G-S-RA | C3323671 | **0**; JLC "no longer manufactured"; Samtec Active (2026-09-24) | **(b)** consign + **(d)** | hand-solder after reflow | mechanically critical: **exact Samtec part only, no substitute**; customer-supply already stated to PCBWay (`evidence/d804-pcbway-response.txt`) |
| Q2, Q3 | AO4800 | C17098 | 8,212 | **(a)** | vendor | traceable genuine AOS lot required (gate B13); re-marked sources rejected |
| U1 | ESP32-S3-WROOM-1-N16R8 | C2913202 | 22,421 | **(a)** | vendor, X-ray EP | exact part kept; NOT redesigned for Economic PCBA; ignore the "N16R8_U2" listing |
| J6, D1, U6 | (BOM MPNs) | — | in stock | **(a)** + **(d)** | hand / lead-formed per `IR_LEAD_FORMING.md` | THT post-reflow operations |
| J4 | — (no part) | — | — | **(d)** | manual battery pigtail land | not in CPL by design (D-781) |
| low-but-sufficient | L1 XFL4020-152MEC (22), Q11 SQ2364EES-T1_BE3 (40), R24 (18), R69 (91), R97 (83), L3 (124), C71/C72 (193), SW9 (262), U8 (484), U7 (603), J1 (748) | | | **(a)**, re-check at order | vendor | a refresh may move any of these to (b) |
| all other lines | as BOM | as BOM | thousands+ | **(a)** | vendor | |

**Class (c): none.**  No equivalent is proposed for any line.  Any equivalent requires the
owner's written approval naming the reference, the MPN and the evidence.

## Instructions carried into the RFQ packages

* Quote the exact MPNs.  Where JLCPCB cannot source a line, say so and quote it as
  **customer-supplied (consigned) for machine placement** — do not substitute.
* Consigned fine-pitch / RF / power parts (U9, U18, U19, U2, U3, D2, D4, D5, L4, MK1) are placed
  by the vendor's line, not by hand.
* J5 is consigned and hand-soldered after reflow; J6, D1, U6 are post-reflow THT operations;
  J4 is a manual pigtail land.
