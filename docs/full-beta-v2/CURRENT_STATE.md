# AQROOT Full Beta v2 — CURRENT STATE (durable checkpoint)

> Checkpoint/index only. Authority precedence: **CTO_DECISIONS.md > accepted
> audits/engineering evidence > CURRENT_STATE.md > summaries/transcripts/session
> memory.** If this file conflicts with higher-authority evidence, repair this file.
>
> **PRODUCT-SPEC AUTHORITY.** For any external / mechanical / marketing claim — renders,
> website, Kickstarter, enclosure/industrial-design briefs, product descriptions, spec
> sheets — the authoritative current-product spec/index is **`docs/full-beta-v2/DEVICE_SPEC.md`**
> (created FBV2-P2-004A / D-301). It is **MANDATORY** to consult before making any such
> claim; do not publicly claim a dimension, capacity, antenna count, connector, protocol,
> frequency, feature or internal component unless DEVICE_SPEC marks it MARKETING-SAFE.
> This file references DEVICE_SPEC rather than duplicating full specs.

## 1. Authoritative HEAD
- **Demo D-462 (GPIO45 VDD_SPI strap promoted):** U1.26, fitted 10 kOhm
  R111.1, and TP1.1 are now one copper island through 23 add-only 0.20 mm
  segments (19 F.Cu / four In2.Cu) and two ordinary vias. Both branch orders
  pass the atomic gate; independent refilled parity DRC remains 199/5/1 with
  no attributable class. Connectivity improves 67->66 open retained nets and
  484->482 edges; ratsnest 513->511. Board `e1d5d5d8...`; accepted copper,
  D-269/D-186, RGB, XGPIO4/XGPIO5, Demo NCs, and production hardware remain
  intact. **Next:** screen `Net-(U11-TS_MR)` using D-448's proven U11.6 escape,
  without reopening the parked U11.8/U11.9 package pocket. No owner decision.
- **Demo D-461 (fixed U9 east-refloor parked):** the new post-move/pre-route
  parity-DRC gate proves the +0.5 mm-east pose is illegal before branch ordering:
  U9 overlaps C17's courtyard and shifted pads intersect retained NFC copper
  (five shorts plus one 0.1229/0.2000 mm clearance failure). RFO1-first also has
  `NO_LEGAL_ESCAPE`; VDD_D-lower-first has `NO_PATH`. Four macro orders now stop
  at preflight, preventing partial or misleading candidates. Board `360b8261...`
  and 67/484 connectivity remain authoritative. **Next:** freshly rank an
  independent retained net; U9 requires a broader U9/C17/passive transaction,
  not another order replay at the fixed pose. No owner decision.
- **Demo D-460 (U9 atomic refloor/replay framework bounded):** the complete
  scratch transaction withdraws exactly eight accepted U9-attached segments,
  moves U9 0.5 mm east, scopes all additions to the eight affected/new NFC nets,
  and requires fitted connectivity plus real refilled parity DRC before any
  promotion. Signal-first reaches RFO1 `NO_LEGAL_ESCAPE` after restoring
  XIN/XOUT/RFO2; supply-first reaches VDD_D-lower `NO_PATH` after closing its
  upper branch. Both candidates are rejected with no removal outside the exact
  replay boundary and no wrong-net additions. Board `360b8261...` and 67/484
  connectivity remain authoritative. **Next:** enumerate bounded within-family
  orders at the fixed pose, starting RFO1-first and VDD_D-lower-first; accept
  only the complete atomic transaction. No owner decision.
- **Demo D-459 (U9 supply-refloor pose/impact screen):** 36 bounded U9 poses
  (0/90/180/270 degrees over a +/-0.5 mm, 0.5 mm grid) expose five poses where
  both `NFC_VDD_D` and `NFC_VDD_A` have legal 0.30 mm B.Cu launches. The
  minimum-change winner is U9 +0.5 mm east at 0 degrees; rotation is unnecessary.
  Its atomic replay boundary is exactly eight accepted U9-attached segments:
  XIN/XOUT (one each), RFO1/RFO2 (one each), AGDC (two), and VDD_AM (two).
  Unreplayed real parity DRC has 15 attributable reports, as expected for a
  characterization pose, so neither placement nor copper is promoted. Board
  `360b8261...`, connectivity 67/484, and production hardware remain unchanged.
  **Next:** atomically translate U9 +0.5 mm east, withdraw/replay exactly those
  six accepted nets, place/route both VDD_D/VDD_A trees, and require the full
  accepted-copper/connectivity/refilled-DRC gate before promotion. No owner decision.
- **Demo D-458 (NFC VDD_D/VDD_A local pair bounded):** all eight atomic
  net/branch orders for the adjacent three-land `NFC_VDD_D` and `NFC_VDD_A`
  decoupling trees fail before emitting copper. U9.3 has no legal 0.30 mm B.Cu
  escape at the qualified 0.20 mm package-land clearance (blocked by U9.4,
  U9.2, U9.1, and U9.33); U9.7 is equivalently blocked by U9.8, U9.6, U9.33,
  and Y1.4. The authoritative board remains `360b8261...`, fitted connectivity
  remains 67/484, and all scratch gates retain real refilled parity DRC 199/5/1.
  **Next:** bound one coherent U9 supply-fanout/nearby-passive placement
  transaction covering VDD_D and VDD_A; do not replay planar branch order.
  No owner decision.
- **Demo D-457 (external-I2C buffer local trees bounded):** both orders of the
  coherent `EXT_SDA_BUF`/`EXT_SCL_BUF` four-edge transaction were screened.
  The local U16-to-pull-up B.Cu branches route, but the mixed-face series legs
  fail the qualified ordinary-via inner framework: U16.7 has no via site and
  the U16.2 leg has no In2/In3 join. SCL-first also places its otherwise legal
  pull-up branch 0.2445 mm from the accepted `ACC_3V3_SW` via at
  (55.350,56.550), below the locked 0.250 mm rule. No partial copper is
  promoted; board `360b8261...`, fitted connectivity 67/484, real refilled
  parity DRC 199/5/1, and production hardware are unchanged. **Next:** freshly
  rank another independent retained local cluster; revisit this pair only with
  an explicit U16 package-fanout/corridor transaction. No owner decision.
- **Demo D-456 (radio interrupt/control cluster advanced):** the retained
  `SX1262_BUSY` signal now connects U1.12 to U8.14 through one short F.Cu
  escape, one short B.Cu escape, two ordinary 0.60/0.30 mm vias, and a
  0.20 mm In2 haul (58.702654 mm total). Eight add-only copper objects close
  the net; fitted connectivity improves 68→67 open nets / 485→484 edges and
  ratsnest 514→513. Real refilled schematic-parity DRC remains 199/5/1 and
  no accepted copper is removed. The same bounded framework emits no copper
  for `NFC_IRQ` because U9.27 has no legal ordinary-via escape, or for
  `SX1262_DIO1` because U2.20 has none; their stable blockers are recorded by
  the reusable allowlisted cases. Board `360b8261...`; D-269/D-186, RGB,
  XGPIO4/XGPIO5, Demo NCs, and production hardware remain intact. **Next:**
  bound a package-fanout transaction for U9.27 and U2.20 before retrying either
  long haul; do not replay the unchanged generic inner-haul family. No owner
  decision.
- **Demo D-455 (LTC4368 fault test-point branch promoted):** the isolated
  `TP18.1` island is now joined to the retained `LTC4368_FAULT_N` safety/status
  tree by nine add-only 0.20 mm B.Cu segments (39.822537 mm), routed with the
  stricter 0.30 mm clearance. The five fitted lands are one island; fitted
  connectivity improves 69→68 open nets / 486→485 edges and ratsnest 515→514.
  Real refilled schematic-parity DRC remains 199/5/1, with no accepted copper
  removed. Board `bbb69e92...`; D-269/D-186, RGB, XGPIO4/XGPIO5, Demo NCs, and
  production hardware remain intact. **Next:** screen a coherent retained
  sub-GHz/NFC interrupt/control cluster, beginning with the one-edge
  `NFC_IRQ`, `SX1262_BUSY`, and `SX1262_DIO1` signals. No owner decision.
- **Demo D-454 (LED_A explicit perimeter family bounded):** 60 fixed F.Cu
  corridors reserve the legal J1.1 perpendicular launch across three depths,
  five turn columns, and four ballast-spine approach rows at the locked 0.30 mm
  width / 0.20 mm clearance. None reaches R71.2: 12 block on the lateral leg,
  16 on the turn toward the spine, and 32 on the final approach. No copper is
  promoted; board `a819ade1...`, fitted connectivity 69 open nets / 486 edges,
  and refilled parity DRC 199/5/1 remain unchanged. Park this wall until a
  bounded placement transaction or materially changed geometry is justified.
  **Next:** freshly rank an independent retained local cluster.
- **Demo D-453 (LED_A planar family bounded):** both orders of the coherent
  five-land 0.30 mm F.Cu chain connect all four ballast lands but reproduce the
  same `NO_PATH` on the final R71.2-to-J1.1 feed, whether that feed is first or
  last. No partial copper is promoted; scratch refilled schematic-parity DRC
  remains 199/5/1 and board `a819ade1...` is byte-identical. The qualified
  inner-haul framework correctly refuses a wide/current net. **Next:** reserve
  explicit J1.1 and ballast-spine F.Cu escapes and bound a perimeter-waypoint
  family without reducing the 0.30 mm current-path width. No owner decision.
- **Demo D-452 (USB-C shield tree promoted):** all four plated J3 shield stakes
  and R32.1 now form one fitted copper island through twelve add-only 0.30 mm
  F.Cu/B.Cu segments and two ordinary 0.60/0.30 mm vias. The dedicated
  resistor-side hop preserves the accepted USB signal/CC fanout; no accepted
  copper is removed and no wrong-net object is added. Two scratch runs
  reproduce geometry digest `08990b0b...`; independent refilled schematic-
  parity DRC remains at the accepted 199/5/1 signature. Fitted opens improve
  70→69 nets and 490→486 edges; ratsnest 519→515. Board `a819ade1...`;
  D-269/D-186, RGB, XGPIO4/XGPIO5, Demo NCs, and production hardware remain
  intact. **Next:** coherently screen the local five-land `LED_A` backlight-
  current distribution tree. No owner decision.
- **Demo D-451 (U2/button pull-up family bounded):** an atomic three-net batch
  targeted the equivalent U2-to-pull-up branches of `BTN_DOWN_N`, `BTN_LEFT_N`,
  and `BTN_A_N`. The generic B.Cu topology fails its first branch with
  `NO_PATH`; the qualified reserved-via In2/In3 alternative fails earlier
  because U2.14 exposes no legal ordinary through-via site. Both screens emit
  zero copper, retain each target at three fitted open edges, and preserve real
  refilled schematic-parity DRC at 199/5/1. Board `97d60cde...` and production
  hardware are unchanged. Park this shared U2-side family; revisit only through
  a bounded U2 package-fanout or local placement transaction. **Next:** freshly
  rank an independent retained local cluster. No owner decision.
- **Demo D-450 (NFC VDD_RF planar family bounded):** the retained four-land
  U9.9/U9.14/C49.1/C50.1 rail remains open.  A lower-branch-first atomic screen
  emits no copper because U9.14 has no legal 0.20 mm B.Cu escape; stable
  blockers are U9.15, U9.13, U9.33, and U9.10.  The generic upper and capacitor-
  spine searches also exceed the bounded local-search window, so branch order
  cannot cure the lower-land precondition.  Real refilled schematic-parity DRC
  remains 199/5/1, target connectivity stays at three open edges, board
  `97d60cde...` is byte-identical, and production hardware is untouched.  Park
  the unchanged planar family. **Next:** freshly rank an independent retained
  local cluster; revisit VDD_RF only with an explicit package fanout or bounded
  local U9/passive placement transaction. No owner decision.
- **Demo D-449 (NFC VDD_AM tree promoted):** the retained ST25R3916 analog-
  modulator rail now connects U9.11, C51.1, and C52.1 as one island through
  18 add-only 0.30 mm B.Cu segments (60.878940 mm), with no vias, placement
  change, or accepted-copper removal. Both branch orders close the tree and
  pass real refilled schematic-parity DRC at the accepted 199/5/1 signature.
  Fitted opens improve 71→70 nets and 492→490 edges; ratsnest 521→519.
  Board `97d60cde...`; D-269/D-186, RGB, XGPIO4/XGPIO5, Demo NCs, accepted
  NFC tuning copper, and production hardware remain intact. **Next:** screen
  the adjacent retained `NFC_VDD_RF` four-land supply tree as one coherent
  local transaction. No owner decision.
- **Demo D-448 (U11 branch-order family exhausted):** a deterministic 128-case
  scratch screen tried both U11.6/U11.9 reservation orders and all eight 2 mm
  directions per land at locked 0.20 mm B.Cu width/clearance before U11.8 ISET.
  U11.6 reserves in all 64 TS-first cases; U11.9 has no legal escape in all 64
  STAT1-first cases and after every TS reservation. Zero case reaches ISET and
  no copper is emitted. Board `7a764bac...` and production hardware are
  unchanged. Park this package pocket and freshly rank an independent retained
  local net/cluster. No owner decision.
- **Demo D-447 (ISET wall + promotion guard):** the 5.683 mm charger-current
  programming net remains open because U11.8 has no legal 0.20 mm B.Cu escape;
  blockers are adjacent U11.6/U11.9, accepted tracks, and the board edge. No
  copper was emitted. An adjacent fallback revealed that the local router could
  propose duplicate coincident copper on an already-connected net; the shared
  gate now requires fitted open-edge reduction before candidate output or
  promotion. `ILIM_VSET` correctly rejects at 0→0 and ISET at 1→1. Board
  `7a764bac...`, accepted 199/5/1 DRC, D-269/D-186, RGB, XGPIO4/XGPIO5, Demo
  NCs, and production hardware remain unchanged. **Next:** reserve the local
  U11.6/U11.9 branch geometry before attempting U11.8; park the pocket if that
  bounded family is empty. No owner decision.
- **Demo D-446 (NFC AGDC tree promoted):** C53.1, U9.24, and C54.1 now form
  one connected island through 17 add-only 0.30 mm B.Cu segments
  (40.626806 mm), with no vias, inner copper, placement change, or accepted-
  copper removal. Both branch orders reproduce the same lengths and clean
  result. Real refilled schematic-parity DRC remains 199/5/1; fitted opens
  improve 72→71 nets and 494→492 edges, and ratsnest 523→521. D-269/D-186,
  RGB, XGPIO4/XGPIO5, approved Demo NCs, accepted NFC differential/tuning
  copper, and production hardware remain intact. Board `7a764bac...`.
  **Next:** screen the independent 5.683 mm `ISET` charger-programming net;
  leave the shorter parked `ACC_5V_LX` switch-node wall for its defined
  power-core refloor transaction. No owner decision.
- **Demo D-445 (backlight switch node promoted):** the compact post-refloor
  `BL_SW` cluster now connects U17.1, L3.2, and D8.2 with nine add-only
  0.40 mm B.Cu segments (16.204500 mm), no vias, and no accepted-copper
  removal. The atomic harness also rejects stacked branch output by collapsing
  its one exact same-net launch duplicate before the gate. Two clean candidates
  reproduce geometry digest `c403c986...`. Real refilled schematic-parity DRC
  remains 199/5/1; fitted opens improve 73→72 nets and 496→494 edges, and
  ratsnest 525→523. D-269/D-186, RGB, XGPIO4/XGPIO5, approved Demo NCs, and
  production hardware remain intact. Board `71958623...`. **Next:** screen the
  independent local `NFC_AGDC` analog-decoupling tree, preserving the accepted
  NFC differential/tuning geometry and all parked walls. No owner decision.
- **Demo D-444 (ACC_5V_BOOST_EN IC-first inner family bounded):** the atomic
  D-443 successor reserves the U3.16/U21.2 IC escapes before any passive
  branch.  A 0.60/0.30 mm ordinary through via cannot escape U3.16; the
  board-minimum ordinary 0.50/0.30 mm family reserves both IC endpoints but
  finds no 0.20 mm In2/In3 join.  No partial copper is emitted, real refilled
  parity DRC remains 199/5/1, fitted connectivity remains 73/496, and board
  `86cff98b...` plus production hardware are unchanged.  Both IC-first
  through-via families and the D-443 planar family are parked. **Next:**
  freshly rank an independent retained net or coherent local cluster outside
  parked walls. No owner decision.
- **Demo D-443 (ACC_5V_BOOST_EN planar family bounded):** a new atomic harness
  screens all six branch orders for U3.16/R102.1/TP30.1/U21.2. Every order
  reaches zero fitted open edges, but real refilled schematic-parity DRC
  rejects all candidates at the same four accepted accessory-rail vias
  (0.2254--0.2352 mm actual versus 0.250 mm required). A conservative
  0.275 mm router search margin reproduces the same crossings, proving branch
  order and generic B.Cu planar margin are not the lever. No copper is
  promoted; board `86cff98b...`, fitted connectivity 73/496, D-269/D-186,
  RGB, XGPIO4/XGPIO5, approved Demo NCs, and production hardware are unchanged.
  **Next:** reserve U3.16/U21.2 endpoint escapes and screen an In2/In3 control
  haul before attaching R102.1/TP30.1. No owner decision.
- **Demo D-442 (ACC_5V_ILIM promoted):** the retained U22 current-limit setting
  net now connects U22.4 to R101.1 with seven add-only 0.20 mm B.Cu segments
  (42.417480 mm), no vias, no accepted-copper removal, and deterministic replay
  geometry.  Real refilled schematic-parity DRC remains 199/5/1; fitted opens
  improve 74→73 nets and 497→496 edges, and ratsnest 526→525.  D-269/D-186,
  all RGB replacements, XGPIO4/XGPIO5, and approved Demo NC contacts remain
  intact. Board `86cff98b...`; production hardware is untouched. **Next:**
  route or bound the independent `ACC_5V_BOOST_EN` tree, preserving the accepted
  accessory-power core and both independent D-186 disconnect controls. No owner
  decision.
- **Demo D-441 (ACC_PWR_EN east-perimeter inner family bounded):** the recovered
  successor now uses exact fixed-segment legality instead of a generic search
  timeout.  All 160 combinations of five east X waypoints, In2/In3, and four
  U16.1/U3.20 reserved-via sites reserve both package escapes but fail the first
  orthogonal inner leg.  No join copper is emitted; target connectivity remains
  two open edges, refilled parity DRC remains 199/5/1, and board `2830082d...`
  plus production hardware are unchanged.  This unchanged orthogonal family is
  parked. **Next:** freshly rank an independent retained net or coherent local
  cluster, excluding all parked families. No owner decision.
- **Demo D-440 (ACC_PWR_EN reserved-site inner family bounded):** all 32
  combinations of the first four U16.1/U3.20 ordinary-via sites on In2/In3
  reserve both B.Cu package escapes, but none has a legal 0.20 mm inner join
  inside the qualified local-haul envelope. No copper is promoted; target
  connectivity remains two open edges, refilled parity DRC remains 199/5/1,
  and board `2830082d...` plus production hardware are unchanged. **Next:**
  screen a bounded outer-perimeter inner waypoint family; do not replay the
  generic planar or enumerated local-inner families. No owner decision.
- **Demo D-439 (ACC_PWR_EN planar tree bounded):** the fresh-ledger-selected
  three-land accessory-isolation control does not admit a generic 0.20 mm B.Cu
  tree. R17.1→U16.1 detours 85.344 mm and adds three accessory-rail clearance
  violations; U16.1→U3.20 reports `NO_PATH` at 0.050/0.025 mm. No partial
  copper is promoted; board `2830082d...` and production hardware are
  unchanged. **Next:** pre-reserve U16.1/U3.20 package escapes and screen an
  In2/In3 join, then attach R17.1 atomically. No owner decision.
- **Demo D-438 (retained XGPIO4/XGPIO5 header pair promoted):** an explicit
  `(62.500,30.500)` mm waypoint keeps XGPIO5 clear of both accepted
  accessory-power barrels. The atomic XGPIO5-first transaction adds 21 F.Cu
  segments and no vias, removes no accepted copper, and connects both complete
  R55/D4/J5.13 and R56/D4/J5.14 trees. Real refilled parity DRC remains
  199/5/1; fitted opens improve 76→74 nets and 501→497 edges, and ratsnest
  530→526. Board `2830082d...`; production hardware is untouched. **Next:**
  freshly rank an independent retained net or coherent local cluster, excluding
  all parked materially unchanged walls. No owner decision.
- **Demo D-437 (retained XGPIO4/XGPIO5 header pair bounded):** the atomic gate
  closes all four connector-side edges in both launch orders, but real KiCad
  DRC rejects promotion. The best split-clearance result leaves XGPIO5 only
  0.2334 mm from the accepted `ACC_5V_RAW` via at `(61.375,34.300)` versus the
  locked 0.250 mm rule. Board `2afa51d9...` and production hardware are
  unchanged. **Next:** explicit XGPIO5 waypoint/corridor path-shaping around
  that via, then complete atomic pair replay. No owner decision.
- **Demo D-436 (U10-only USB refloor rejected):** a deterministic 50-case
  ±1.0 mm/0.5 mm-grid/0°–180° U10 placement screen proves every case retains
  the fixed J3.B7 zero-launch precondition under the locked F.Cu-only,
  0.23 mm/0.20 mm/zero-via USB contract. All cases are pruned before accepted
  U10 branches are withdrawn; two clean runs are identical. Board
  `2afa51d9...` and production hardware are unchanged. The connector-side USB
  wall is parked pending a justified connector-footprint or copper-contract
  change. **Next:** coherently screen retained Demo-required XGPIO4/XGPIO5
  connector-side header trees. No owner decision.
- **Demo D-435 (connector-side USB N launch pocket bounded):** exhaustive
  cardinal/diagonal F.Cu launch enumeration at 0.050 and 0.025 mm grids finds
  legal launches for J3.A7 and U10.1, but zero for J3.B7. Stable blockers are
  adjacent J3.A6, the board edge, J3.A5, and accepted track geometry, so the
  wall precedes any downstream pair join. Board `2afa51d9...` and production
  hardware are unchanged. **Next:** bound a local J3/U10 placement transaction,
  keeping J3 mechanically fixed and atomically replaying all displaced U10
  branches under the locked F.Cu-only/0.23 mm/zero-via USB contract. No owner
  decision.
- **Demo D-434 (connector-side USB planar tree wall bounded):** a new
  exhaustive coherent-pair screen tests both pair orders and all 36 attachment
  orders for each three-land connector tree under the locked 0.23 mm width,
  0.20 mm clearance, F.Cu-only, zero-via contract. Across 72 cases, the P tree
  completes whenever attempted first (36/36), but the N tree returns
  `NO_LEGAL_ESCAPE` in every case, both before and after P. No complete pair
  exists and no copper is promoted; board `2afa51d9...` and production hardware
  are unchanged. **Next:** explicitly enumerate F.Cu perimeter fanouts for the
  two N connector lands and U10.1 before joining them; if none coexist, bound a
  local USB connector/ESD placement transaction without weakening the USB
  layer/via contract. No owner decision.
- **Demo D-433 (V3V3 feedback tree promoted):** retained U12.3, R39.2, and
  R40.1 now form one island through separate 0.20 mm In2/In3 branches and
  three ordinary 0.60/0.30 mm vias, with one U12-side barrel shared by both
  branches. The add-only transaction contributes 13 objects, preserves the
  completed switch nodes, and retains the accepted refilled parity DRC
  signature of 199/5/1. Fitted opens improve 77→76 nets and 503→501 edges;
  ratsnest 532→530. Board `2afa51d9...`; production hardware is untouched.
  **Next:** screen the connector-side USB D+/D− pair as one coherent
  differential transaction. No owner decision.
- **Demo D-432 (U12/L1 switch pair promoted):** both buck-boost switch nodes
  now connect their paired U12 lands to L1 with nine add-only B.Cu objects,
  short 0.20 mm package joins, immediate 0.40 mm trunks, and no vias or inner
  switching copper. The two paths are 15.335 mm and 3.977 mm. Refilled parity
  DRC remains 199/5/1; fitted opens improve 79→77 nets and 507→503 edges, and
  ratsnest 536→532. Board `3c5d425f...`; production hardware is untouched.
  **Next:** screen the local three-land `V3V3_FB` feedback tree without
  disturbing the completed switch geometry. No owner decision.
- **Demo D-431 (VBUS-present local tree promoted):**
  `/01_POWER_TREE/VBUS_PRESENT` now connects fitted C68.1, R105.1, R104.2,
  and TP31.1 with 13 add-only objects: two ordinary 0.60/0.30 mm through-vias
  and 0.20 mm B.Cu/In3.Cu copper. The TP31 branch reserves the In3 hop first;
  the remaining passive branches close on B.Cu. Refilled parity DRC remains
  199/5/1, with no accepted-copper removal or wrong-net addition. Fitted opens
  improve 80→79 nets and 510→507 edges; ratsnest 539→536. Board
  `f8d555d4...`; production hardware is untouched. **Next:** screen the short
  local retained buck-boost L1/U12 switching cluster as a power-aware atomic
  transaction, preserving the new VBUS-present tree. No owner decision.
- **Demo D-430 (audio/radio long-haul characterization):** reserved-escape
  screens bound two freshly ranked nets without PCB change. `/I2S_SPK_DOUT`
  reserves both endpoint vias but has no 0.20 mm In2/In3 join;
  `/CC1101_GDO0` cannot expose an ordinary through-via from U7.15 B.Cu.
  Refilled parity DRC remains 199/5/1 and board `aed8d911...` is byte-identical.
  **Next:** rank a short independent local retained cluster. No owner decision.
- **Demo D-429 (SPI-A clock tree promoted):** `/SPI_A_SCK` now connects fitted
  U1.20, J1.36, and J2.5 with 14 add-only 0.20 mm track segments and four
  ordinary 0.60/0.30 mm through-vias (72.751257 mm total) on F.Cu/In2.Cu.
  Two clean candidates reproduce identical physical geometry. The authoritative
  refilled parity DRC stays at the accepted 199/5/1 signature; fitted opens
  improve 81→80 nets and 512→510 edges, and ratsnest 541→539. Board
  `aed8d911...`; MOSI remains open and its unchanged adjacent-J1 wall remains
  parked. **Next:** freshly rank an independent retained net or coherent local
  cluster; do not retry MOSI without a material fanout/refloor change. No owner
  decision.
- **Demo D-428 (SPI-A paired J1 fanout wall PARKED):** the D-427 successor
  pre-reserves distinct ordinary 0.60/0.30 mm through-via fanouts for J1.36
  (`/SPI_A_SCK`) and adjacent J1.34 (`/SPI_A_MOSI`) before either inner haul.
  Across both In2/In3 assignments and the first four ranked sites per pad, all
  32 atomic cases fail: 11 at paired barrel reservation, 16 at the SCK MCU
  join, and five at the MOSI MCU join. Zero complete tree pair exists and no
  partial copper is promoted; board `7e20e227...` and production hardware are
  unchanged. **Next:** promote the independently complete clock-first SCK tree
  through a fresh full gate, leaving MOSI open and parked for a materially new
  fanout/refloor transaction. No owner decision.
- **Demo D-427 (SPI-A shared clock/data wall bounded):** both complete-tree
  launch orders are clean but mutually exclude the adjacent J1 display via
  pocket: clock-first closes SCK and leaves MOSI one edge open; data-first
  closes MOSI and leaves SCK one edge open.  Separate In2/In3 assignment does
  not solve a through-via-site wall.  No partial tree or copper is promoted;
  the board remains `7e20e227...` with the accepted 199/5/1 DRC signature.
  **Next:** atomically pre-reserve distinct J1.34/J1.36 perimeter fanouts before
  either haul; fall back to an independently gated complete SCK promotion only
  if the paired reservation is impossible. No owner decision.
- **Demo D-426 (SPI-A MISO promoted):** `/SPI_A_MISO` now connects fitted pads
  U1.21 and J2.7 using three 0.20 mm F.Cu escape segments, two ordinary
  0.60/0.30 mm vias, and three 0.20 mm In2.Cu segments (28.739064 mm total).
  R112 stays DNP and display SDO therefore remains isolated from the microSD
  read bus. The change is add-only; refilled parity DRC stays at the accepted
  199/5/1 signature. Fitted opens improve 82→81 nets and 513→512 edges;
  ratsnest improves 542→541. Board `7e20e227...`; production hardware is
  untouched. **Next:** atomically screen `/SPI_A_SCK` and `/SPI_A_MOSI`, which
  together own four fitted open edges, without disturbing accepted bus copper.
  No owner decision.
- **Demo D-425 (Native B internal leg promoted):** `/NATIVE_B` now connects
  U1.24 to R62.1 through two short 0.20 mm F.Cu escapes, ordinary 0.60/0.30 mm
  through-vias at (44.050,132.450) and (43.850,114.800) mm, and a 0.20 mm In2
  join. The 20.436636 mm add-only route is six segments plus two vias and
  removes no accepted copper. The refilled parity DRC stays at the accepted
  199/5/1 signature; fitted opens improve 83→82 nets and 514→513 edges, and
  ratsnest 543→542. Board `b92701c2...`; production hardware is untouched.
  **Next:** bus-aware bounded screen of `/SPI_A_MISO`, preserving accepted
  SD/display copper and excluding every parked unchanged wall. No owner decision.
- **Demo D-424 (Native A internal leg promoted):** `/NATIVE_A` now connects
  U1.31 to R61.1 with 11 add-only 0.20 mm F.Cu segments (20.149286 mm), no
  vias, and no accepted-copper removal. Both A-first and B-first atomic screens
  reproduce the same result: Native A closes, while `/NATIVE_B` has no generic
  0.20 mm F.Cu path. The refilled parity DRC stays at the accepted 199/5/1
  signature; fitted opens improve 84→83 nets and 515→514 edges, and ratsnest
  544→543. Board `5d5a45c5...`; production hardware is untouched. **Next:**
  explicit endpoint-escape/perimeter screening for Native B. No owner decision.
- **Demo D-423 (NFC analog west-via family PARKED):** a deterministic 0.025 mm
  enumeration finds zero legal 0.60/0.30 mm through-via sites reachable from
  the D-422 westward U9.7 neck, before the accepted oscillator envelope is
  excluded. C47.1/C48.1 independently expose 204/217 legal landing sites, so
  the wall is the package-local barrel pocket rather than In3 capacity. No
  copper/placement/rule change; board remains `37718bc7...` and production is
  untouched. **Next:** freshly rank an independent retained net/small cluster;
  revisit NFC_VDD_A only with a different fanout direction or local placement
  transaction. No owner decision.
- **Demo D-422 (NFC supply inner-fanout topology bounded):** explicit westward
  U9.3/U9.7 necks and independent via/inner-layer trees advance beyond the
  generic launch wall, but the first analog In3 corridor crosses accepted
  `NFC_XIN` copper (2 shorts, 4 clearances, 1 crossing, +1 hole-clearance).
  Nothing was promoted; board remains `37718bc7...` and production hardware is
  untouched. **Next:** enumerate analog supply via/corridor sites outside the
  complete oscillator envelope, preserving the independent fanout topology
  and every accepted NFC segment. No owner decision.
- **Demo D-421 (NFC VDD_D/VDD_A generic launches bounded):** both atomic
  upper-first and lower-first supply-tree orders fail before emitting copper:
  U9.3 and U9.7 each report `NO_LEGAL_ESCAPE` at the 0.20 mm UFQFPN escape
  floor. Both refilled parity screens retain exactly the accepted 199/5/1 DRC
  signature; board remains `37718bc7...` and `hardware/beta-v2/` is untouched.
  **Next:** explicitly reserve outward U9.3/U9.7 fanouts and independent local
  via sites, then join each decoupler pair on an inner layer. No owner decision.
- **Demo D-420 (accessory boost In3 transition bounded; wall PARKED):** all
  12 package-local U21.6 raw-via/In3-return combinations fail real refilled
  parity DRC twice while LX remains on B.Cu. The best case still physically
  shorts the raw neck/barrel to the LX launch and leaves 0.225 mm to the
  retained raw-tree via against 0.250 mm required clearance. Board remains
  `37718bc7...`; no geometry/rule/copper promoted. This is the fifth unchanged
  boost-wall characterization, so policy parks it. **Next:** screen the
  independent local `NFC_VDD_D`/`NFC_VDD_A` supply-decoupling cluster while
  preserving accepted NFC signal copper. No owner decision.
- **Demo D-419 (accessory boost planar crossover bounded; no PCB change):**
  with R99 fixed +0.5 mm east, 12 coordinated B.Cu LX/raw outer-corridor cases
  all fail the real refilled parity DRC. Moving the raw detour farther west and
  south never clears its invariant return through retained `BQ25185_SYS`; GND,
  LX, crossing, and clearance collisions remain secondary. Two clean runs
  reproduce zero candidates (KiCad varies coincident-item classifications).
  Board remains `37718bc7...`; `hardware/beta-v2/` is untouched. **Next:**
  screen a courtyard-local U21.6 raw transition to the accepted In3 raw tree,
  retaining LX on B.Cu; do not widen the disproven planar family. No owner
  decision.
- **Demo D-418 (accessory boost R99/raw-neck boundary; no PCB change):** the
  16-case LX-first screen finds +0.5 mm east as the minimum tested R99 move
  that clears the rotated L4 courtyard without the via/dangling regressions of
  larger moves. All LX routes close; no explicit raw neck passes. North paths
  hit retained BQ25185/ILIM copper. South paths avoid crossing reports but
  still collide with LX and miss raw clearance (0.225 mm actual versus 0.250 mm
  required). The board remains `37718bc7...`; `hardware/beta-v2/` is untouched.
  **Next:** fix R99 at +0.5 mm, coordinately reserve nonintersecting LX/raw
  south corridors, then replay FB/EN/input/GND atomically. Do not retry north
  necks or larger R99 moves. No owner decision.
- **Demo D-417 (accessory boost B.Cu topology bounded; no PCB change):** five
  LX-first, accepted-raw-tree-preserving cases all close `ACC_5V_LX`
  (5.255–6.255 mm), but no `L4`-only offset clears real KiCad DRC.  The remaining
  minimum wall is explicit: rotated `L4` overlaps `R99`, while the straight
  U21.6 raw-tree neck crosses accepted `ACC_DETECT_N` and violates clearance to
  LX/the accepted raw via at (55.85,38.00).  Board remains `37718bc7...` and
  `hardware/beta-v2/` is untouched. **Next:** include `R99` in the bounded
  placement transaction and route the raw B.Cu neck around those three fixed
  obstacles, then replay FB/EN/input/GND atomically. No owner decision.
- **Demo D-416 (accessory boost power-core replay bounded; no PCB change):**
  the 180-degree U21/L4 refloor is order-sensitive. LX-first closes
  `ACC_5V_LX` in 6.213 mm, after which all five `ACC_5V_RAW` endpoints close;
  raw-first re-boxes U21.5. The generic inner-layer raw replay is not
  promotable: real KiCad DRC reports a clearance, track crossing, courtyard
  overlap, package-neck width reports, and three extra solder-mask bridges.
  The authoritative board remains `37718bc7...`; accepted copper and
  `hardware/beta-v2/` are untouched. **Next:** LX-first topology-specific B.Cu
  replay of the accepted raw-output tree, resolve the U21/L4 courtyard
  interaction, then replay FB/EN/input/GND and gate all six branches atomically.
  No owner decision.
- **Demo D-415 (accessory boost refloor lever bounded; no PCB change):** moving
  `C65` 1.0 mm east does not open `U21.5`. Rotating U21 180 degrees does;
  rotating both U21 and L4 180 degrees gives the shorter screened switch route
  (6.255 mm versus 13.593 mm). This is characterization only because all six
  U21 endpoint branches must be atomically replayed. The authoritative board
  remains `37718bc7...`; `hardware/beta-v2/` is untouched. **Next:** implement
  the complete six-branch U21 refloor/replay transaction, preserving the
  accepted ACC_5V_RAW tree and reset-safe enable, then run the authoritative
  refilled full-board and fitted-ledger gates. No owner decision.
- **Demo D-414 (accessory 5 V switch-node wall; no PCB change):**
  `ACC_5V_LX` is a 4.020 mm fitted `U21.5`–`L4.2` switch node. The new bounded
  power-aware screen proves no legal B.Cu launch at either the locked 0.40 mm
  trunk width or the courtyard-scoped 0.20 mm U21 escape floor; blockers are
  adjacent U21 lands and accepted `C65.1`/`ACC_5V_RAW` geometry. Two clean
  screens emit no copper. The authoritative board stays `37718bc7...` with the
  accepted 199/5/1 DRC signature and `hardware/beta-v2/` untouched. **Next:**
  coordinated local `U21`/`L4`/`C65` cluster-refloor screen, preserving and
  revalidating accepted `ACC_5V_RAW` copper and minimizing switch-loop area.
  No owner decision.
- **Demo D-413 (fuel-gauge alert promoted):** `MAX17048_ALRT_N` is complete
  from TP11.1 to U14.5 with 4.306134 mm of 0.20 mm copper and two 0.60/0.30 mm
  through-vias on an In3 hop. In2 is proven closed; two clean In3 screens
  reproduce identical physical geometry. The authoritative refilled full-board
  gate remains the accepted 199 footprint-library / 5 hole-clearance / 1
  solder-mask-bridge signature, with no accepted copper removed. Fitted opens
  improve 85→84 nets and 516→515 edges; raw ratsnest improves 545→544. Board
  hash `37718bc7...`; `hardware/beta-v2/` is untouched. **Next:** bounded,
  power-aware routing of the accessory 5 V boost switching cluster, beginning
  with `ACC_5V_LX`; do not route it as an ordinary signal. No owner decision.
- **Demo D-412 (NFC receiver-input wall; no authoritative PCB change):** both
  `NFC_RFI1/RFI2` launch orders fail at U9.22/U9.23 even with the DRU-legal
  0.20 mm courtyard neck; moving only unrouted C17 1.25 mm east does not clear
  the accepted RFO2/package-land obstruction. The refilled full-board signature
  remains the accepted 199 footprint-library / 5 hole-clearance / 1 solder-mask
  bridge classes and board hash `0a5c99d1...`. The wall is parked. **Next:**
  screen `MAX17048_ALRT_N` with a bounded two-via inner-layer hop; direct B.Cu
  is closed. No owner decision is open.
- **FBV2-P2-097 / D-395 (complete fault replay + detect-wall obstacle-class
  attribution; no authoritative PCB change):** deterministic replay of the
  37.496 mm TP33.1↔TP27.1 B.Cu suffix closes ACC_POWER_FAULT_N and preserves
  relocated XGPIO0 with zero open edges. After the proven detect prefix,
  removing seven local non-detect vias or 18 local non-detect tracks within
  3.0 mm of U3.17 changes U3.17 reachable sites on In2 and In3, while every
  R129.2 site remains unchanged. The detect wall is therefore local mixed
  copper at U3.17. Evidence: `u3_detect_obstacle_attribution_097.py` / `.json`.
  This is characterization; required branches were withdrawn, no detect join
  or promotion candidate exists, and the board remains byte-identical
  (`a4b93b9b…`); no owner decision; readiness remains 78%. **Next:** rank the
  seven local vias individually, then local tracks only if necessary; retain
  only a complete detect join with every displaced branch replayed, attribute
  the five D-388 residual clearances, and run the corrected full-board gate.
- **FBV2-P2-096 / D-394 (fault-component attribution; no authoritative PCB
  change):** the D-393 In3 endpoint join is electrically connected through
  U3.18. The one remaining ACC_POWER_FAULT_N component is TP33.1 alone; the
  prior manual prefix omitted this sixth pad. Four direct 0.200 mm B.Cu
  attachments close the complete fault branch, with TP33.1↔TP27.1 shortest at
  37.496 mm; only TP33.1↔U3.18 is blocked. Evidence:
  `u3_fault_component_attribution_096.py` / `.json`. This is characterization,
  not a complete fault/detect transaction or promotion candidate. Board remains
  byte-identical (`a4b93b9b…`); no owner decision; readiness remains 78%.
  **Next:** replay the shortest TP33.1↔TP27.1 suffix deterministically, then
  attribute/relocate the U3.17/R129.2 detect wall and the five D-388 residual
  clearances before the corrected full-board gate.
- **FBV2-P2-095 / D-393 (minimum-scope XGPIO relocation/replay; no
  authoritative PCB change):** complete XGPIO0 replacement closes on In2 via
  `(58.95,20.15)/(61.15,75.15)` mm and exposes 1 In2 + 4 In3 U3.18 sites. A
  ranked replay geometrically reserves and joins the fault endpoint pair on
  In3 via `(56.55,65.90)/(52.70,78.45)` mm, but KiCad still reports one fault
  open component; ACC_DETECT_N also retains one open at its R129.2↔U3.17
  `NO_PATH` edge. Nearest-rank XGPIO0/In3 and
  XGPIO1/In2/In3 replacements do not close. No complete transaction exists,
  so no DRC promotion gate or copper promotion was performed. Evidence:
  `u3_p18_xgpio_via_relocation_095.py` / `.json`. Board remains byte-identical
  (`a4b93b9b…`); no owner decision; readiness remains 78%. **Next:** attribute
  the fault candidate's remaining connectivity discontinuity, then the
  U3.17/R129.2 obstacle after the proven XGPIO0/In2 prefix; relocate/replay the
  minimum blocking geometry and also attribute the five D-388 residual
  clearances before promotion.
- **FBV2-P2-094 / D-392 (U3.18 blocking-via minimum-cardinality rank; no
  authoritative PCB change):** all eight individual D-391 transaction-via
  withdrawals were screened deterministically. XGPIO0 `(52.75,78.35)` alone
  exposes 1 In2 + 4 In3 U3.18 sites and XGPIO1 `(55.40,79.00)` alone exposes
  4 In2 + 3 In3 sites; each other singleton exposes zero. Thus the minimum
  blocking set has cardinality one and the next transaction needs to relocate
  only XGPIO0 or XGPIO1, not all eight nearby vias. A clean rerun reproduced
  `u3_p18_via_subset_rank_094.json` byte-for-byte; the ordered-prefix probe
  passes in all cases. This is sensitivity-only evidence because the withdrawn
  required route was not replayed. Board remains byte-identical
  (`a4b93b9b…`); no owner decision; readiness remains 78%. **Next:** compare
  bounded minimum-scope relocation/replay of XGPIO0 versus XGPIO1 (XGPIO0
  first), retain only a complete XGPIO branch that permits complete fault and
  detect replay, then run the corrected full-board gate; also attribute the
  five D-388 residual clearances before promotion.
- **FBV2-P2-093 / D-391 (U3.18 obstacle withdrawal sensitivity; no
  authoritative PCB change):** six controlled scratch cases show that
  withdrawing adjacent ACC_5V_BOOST_EN/SX1262_RXEN copper does not change the
  zero-site U3.18 wall. Withdrawing the eight D-386 transaction vias within
  3.0 mm (XGPIO9/3/0/1/5/4/2 and ACC_3V3_EN) exposes four U3.18 sites on each
  inner layer. This isolates the movable obstacle class but does not identify
  the minimum via subset or preserve the eight required routes, so it is not a
  promotion candidate. Evidence/harness: `u3_p18_obstacle_attribution_093.py`
  / `.json`. Board remains byte-identical (`a4b93b9b…`); no owner decision;
  readiness remains 78%. **Next:** rank individual/subset via withdrawals and
  relocate/replay the smallest blocking set before complete fault/detect replay;
  also attribute the five D-388 residual clearances before promotion.
- **FBV2-P2-092 / D-390 (collision-branch explicit via-site enumeration; no
  authoritative PCB change):** after each D-389 proven local prefix,
  ACC_POWER_FAULT_N has 3 reachable TP27.1 sites on In2 and 4 on In3 but zero
  U3.18 sites, while ACC_DETECT_N has sites at both endpoints yet none of 24
  distinct pairs joins. Ordinary through-via enumeration is therefore closed.
  Prefix-only real KiCad DRC retains known incomplete-transaction via and
  clearance regressions; no copper is promoted. Evidence/harness:
  `u3_collision_branch_viasite_enum_092.py` / `.json`. Board remains
  byte-identical (`a4b93b9b…`); no owner decision; readiness remains 78%.
  **Next:** attribute U3.18/U3.17 endpoint-neighborhood obstacles and screen
  minimum-scope adjacent-branch geometry/reflooring, prioritizing U3.18; also
  attribute the five D-388 residual clearances before promotion.
- **FBV2-P2-091 / D-389 (fresh collision-branch replay order screen; no
  authoritative PCB change):** after reconstructing D-386 and withdrawing both
  dominant collision branches, generic complete-branch MST replay fails in
  both orders. ACC_POWER_FAULT_N closes three local B.Cu edges then fails
  TP27.1→U3.18 (`NO_LEGAL_ESCAPE`); ACC_DETECT_N closes R129.2→R64.1 across
  layers then fails R129.2→U3.17 (`NO_PATH`). One exact duplicate via is
  removed from each candidate. Corrected same-basename, zone-refilled real
  KiCad DRC does not reintroduce either branch's collisions and retains the
  five D-388 isolated clearances, but both candidates are electrically open.
  Evidence/harness: `u3_collision_branch_replay_091.py` / `.json`. Board
  remains byte-identical (`a4b93b9b…`); no owner decision; readiness remains
  78%. **Next:** explicitly enumerate reachable legal via sites for the
  U3.18/TP27.1 and U3.17/R129.2 endpoint pairs after the ordered prefix, test
  only distinct site pairs, then attribute the five isolated clearances.
- **FBV2-P2-090 / D-388 (dominant collision branch withdrawal; no authoritative
  PCB change):** after reconstructing the complete D-386 In3 transaction with
  the corrected real-DRC setup, withdrawing all 57 ACC_POWER_FAULT_N tracks
  reduces added copper collisions 22→7; also withdrawing all 22 ACC_DETECT_N
  tracks plus its via reduces them 7→5. Thus the two retained branches explain
  17/22 collision reports. Five isolated retained-branch clearances, nine
  dangling transaction vias, and one duplicate/co-located hole remain. The
  scratch candidates are electrically open and not promotable. Evidence/harness:
  `u3_collision_branch_withdrawal_090.py` / `.json`. Board remains byte-identical
  (`a4b93b9b…`); no owner decision; readiness remains 78%. **Next:** freshly
  replay complete ACC_POWER_FAULT_N and ACC_DETECT_N after the D-386 ordered
  prefix, deduplicate/remove transaction vias, then run the corrected
  same-basename/refilled real-KiCad DRC gate and attribute the five residual
  clearances.
- **FBV2-P2-089 / D-387 (D-386 violation attribution; no authoritative PCB
  change):** corrected scratch DRC requires the authoritative project basename
  and a zone refill; D-386's 112-clearance headline mixed in harness artifacts.
  Exact item-level baseline subtraction attributes the dominant genuine
  collision set to retained B.Cu ACC_POWER_FAULT_N (15 reports against XGPIO1,
  XGPIO2, and XGPIO6), with two ACC_DETECT_N/XGPIO0 collisions and isolated
  endpoint clearances. Duplicate/co-located and dangling transaction vias also
  remain, so the candidate is not promotable. Evidence/harness:
  `u3_transaction_violation_attribution_089.py` / `.json`. Board remains
  byte-identical (`a4b93b9b…`); no owner decision; readiness remains 78%.
  **Next:** withdraw and freshly replay complete ACC_POWER_FAULT_N after the
  D-386 ordered transaction, then ACC_DETECT_N only if still required, using
  the corrected same-basename/refilled real-DRC gate.
- **FBV2-P2-088 / D-386 (complete ACC_3V3_EN branch replacement; no
  authoritative PCB change):** after the selected D-385 XGPIO9/In2 then
  XGPIO8/In3 ordered prefix, complete ACC_3V3_EN closes on In3 through
  `(53.65,62.35)/(53.05,80.80)` mm and both local B.Cu leaves close.  In2
  fails at R98.1 (`NO_VIA_SITE`).  The unaffected accepted boundary restores
  exactly, but real KiCad DRC remains strongly regressed (12 shorts, 112
  clearances, two crossings, and other via/rule classes), so this is not a
  promotion candidate.  Evidence/harness: `u3_acc_en_inner_replay_088.py` /
  `.json`.  Board remains byte-identical (`a4b93b9b…`); no owner decision;
  readiness remains 78%. **Next:** attribute the complete In3 transaction's
  violations by collision source and route, then reroute the minimum dominant
  geometry before a replacement-aware authoritative gate.  Do not introduce
  blind vias without an owner manufacturing decision.
- **FBV2-P2-087 / D-385 (ordered U3.14-first adjacent-branch refloor; no
  authoritative PCB change):** after the proven six-route prefix, 32 XGPIO9
  pair specifications become available.  Both screened In2 specifications
  close complete XGPIO9 and then XGPIO8 on In3, with exact restoration of the
  remaining accepted boundary.  ACC_3V3_EN still cannot attach at U3.15 to its
  retained B.Cu anchor 7.634 mm away (`NO_LEGAL_ESCAPE`).  The incomplete
  scratch candidate has real KiCad DRC regressions (12 shorts, 111 clearances,
  and other classes), so it is not promotable.  Evidence/harness:
  `u3_ordered_p13_p15_refloor_087.py` / `.json`.  Board remains byte-identical
  (`a4b93b9b…`); no owner decision; readiness remains 78%. **Next:** replace
  complete ACC_3V3_EN after the selected U3.14-first XGPIO9/XGPIO8 prefix;
  enumerate explicit reachable U3.15 sites if direct replacement cannot close.
  Do not introduce blind vias without an owner manufacturing decision.
- **FBV2-P2-086 / D-384 (U3.14 obstacle attribution and R7-only minimum-scope
  cluster screen; no authoritative PCB change):** after replaying the sole
  viable seven-route prefix, ten R7 translations from 0.25–1.00 mm expose zero
  U3.14 sites on In2 or In3. The wall is dominated by U3.15, U3.13, and local
  track copper; moving R7 west only replaces R7.2 with C4.2, and offsets of
  0.50 mm or more break both accepted R7 pad-pair contracts. All incomplete
  candidates retain real KiCad DRC regressions. Evidence/harness:
  `u3_xgpio9_r7_cluster_086.py` / `.json`. Board remains byte-identical
  (`a4b93b9b…`); no owner decision; readiness remains 78%. **Next:** bounded
  ordered local refloor of complete XGPIO8/XGPIO9/ACC_3V3_EN branches, reserve
  U3.14 first, then replay U3.13 and U3.15 while preserving the earlier prefix;
  do not introduce blind vias without an owner manufacturing decision.
- **FBV2-P2-085 / D-383 (XGPIO5/XGPIO4 layer-allocation permutation; no
  authoritative PCB change):** all four In2/In3 allocations were replayed.
  Only the existing XGPIO5=In3/XGPIO4=In2 allocation preserves all seven
  routes; the other three stop at XGPIO1 or XGPIO3. Four explicit U3.14 ranks
  on both inner layers remain unreachable in the sole viable prefix. Exact
  boundary withdrawal passes. Evidence/harness:
  `u3_xgpio9_layer_permute_085.py` / `.json`. Board remains byte-identical
  (`a4b93b9b…`); no owner decision; readiness remains 78%. **Next:** bounded
  U3.14 endpoint-neighborhood obstacle attribution and minimum-scope cluster
  geometry while preserving the proven seven-route prefix; do not retry layer
  permutations or introduce blind vias without an owner manufacturing decision.
- **FBV2-P2-084 / D-382 (XGPIO9 explicit via-site enumeration; no
  authoritative PCB change):** after the seven-route D-380 prefix, bounded
  rank enumeration exposes four reachable R60.1-side sites on each of In2 and
  In3, but no reachable U3.14-side site on either layer. Thus there are zero
  distinct endpoint pairs and zero joins. Exact boundary withdrawal passes;
  the scratch prefix retains the known real KiCad DRC regressions.
  Evidence/harness: `u3_xgpio9_viasite_enum_084.py` / `.json`. Board remains
  byte-identical (`a4b93b9b…`); no owner decision; readiness remains 78%.
  **Next:** boundedly permute the proven XGPIO5/XGPIO4 inner-layer choices,
  retaining only prefixes that close all seven routes, and probe whether any
  allocation exposes a legal U3.14 site before considering endpoint-cluster
  geometry; blind vias remain excluded absent an owner manufacturing decision.
- **FBV2-P2-083 / D-381 (complete-XGPIO9 inner replacement; no authoritative
  PCB change):** after the seven-route D-380 prefix, complete XGPIO9
  replacement cannot reserve the moved U3.14-side escape on either In2 or In3;
  both independently owned attempts return `NO_LEGAL_ESCAPE`. Exact boundary
  withdrawal and unrelated-copper preservation pass, but neither attempt
  reaches its join and incomplete scratch layouts retain real KiCad DRC
  regressions. Evidence/harness: `u3_xgpio9_inner_replay_083.py` / `.json`.
  Board remains byte-identical (`a4b93b9b…`); no owner decision; readiness
  remains 78%. **Next:** enumerate and explicitly select reachable legal via
  sites at R60.1 and U3.14 after the D-380 prefix, then test joins only across
  distinct site pairs.
- **FBV2-P2-082 / D-380 (deterministic XGPIO8 transaction replay; no
  authoritative PCB change):** D-379's shortest explicit In3 pair at
  `(54.45,33.00)/(55.70,81.70)` mm closes complete XGPIO8 after the six-route
  D-377 prefix. Exact boundary withdrawal and unrelated-copper preservation
  pass, and all seven replaced branches have zero open edges. Replay advances
  to XGPIO9/U3.14, whose retained B.Cu anchor 7.208 mm away returns
  `NO_LEGAL_ESCAPE`. The incomplete scratch layout adds 48 non-unconnected real
  KiCad DRC violations, so no transaction is promoted. Evidence/harness:
  `u3_xgpio8_transaction_replay_082.py` / `.json`. Board remains byte-identical
  (`a4b93b9b…`); no owner decision; readiness remains 78%. **Next:** replace
  complete XGPIO9 after the seven selected routes, then continue the remaining
  U3 terminal schedule only while each branch closes.
- **FBV2-P2-081 / D-379 (XGPIO8 explicit via-site enumeration; no
  authoritative PCB change):** after the six-route D-377 prefix, bounded rank
  enumeration finds two reachable R59.1-side and three U3.13-side legal In3
  sites. All six distinct site pairs join; the shortest is
  `(54.45,33.00)/(55.70,81.70)` mm at 49.187 mm. In2 remains closed because
  R59.1 has no reachable site. The incomplete prefix retains real KiCad DRC
  regressions, so no transaction is promoted. Evidence/harness:
  `u3_xgpio8_viasite_enum_081.py` / `.json`. Board remains byte-identical
  (`a4b93b9b…`); no owner decision; readiness remains 78%. **Next:** replay
  complete XGPIO8 with the shortest In3 pair after the D-377 prefix and continue
  the remaining U3 terminal schedule only while each branch closes.
- **FBV2-P2-080 / D-378 (complete-XGPIO8 inner replacement; no authoritative
  PCB change):** after the six-route D-377 prefix, complete XGPIO8 replacement
  cannot reserve the R59.1-side escape on either In2 or In3; both attempts
  return `NO_VIA_SITE`. There is no transaction candidate and incomplete
  scratch layouts retain real KiCad DRC regressions. Evidence/harness:
  `u3_xgpio8_inner_replay_080.py` / `.json`. Board remains byte-identical
  (`a4b93b9b…`); no owner decision; readiness remains 78%. **Next:** enumerate
  and explicitly select reachable legal via sites at R59.1 and U3.13 after the
  D-377 prefix, then test joins only across distinct site pairs.
- **FBV2-P2-079 / D-377 (complete-XGPIO0 inner replacement; no authoritative
  PCB change):** after the D-376 prefix, complete XGPIO0 replacement closes on
  In2 through `(58.95,20.15)/(61.15,75.15)` mm via sites; In3 fails its join
  with `NO_PATH`. Replay advances to XGPIO8/U3.13, whose retained B.Cu anchor
  9.555 mm away also returns `NO_PATH`, so there is no promotable transaction.
  Evidence/harness: `u3_xgpio0_inner_replay_079.py` / `.json`. Board remains
  byte-identical (`a4b93b9b…`); no owner decision; readiness remains 78%.
  **Next:** replace the complete XGPIO8 branch after the six selected routes,
  then continue the terminal schedule only while each branch closes.
- **FBV2-P2-078 / D-376 (XGPIO1 explicit via-site enumeration; no
  authoritative PCB change):** explicit rank selection finds a second legal
  R52.1-side In3 via site at `(62.75,78.55)` mm. Paired with the U3.5-side
  `(55.40,24.95)` mm site, XGPIO1 closes directly; the rank-zero pair repeats
  the D-375 no-path result. Replay advances to XGPIO0/U3.4, whose retained B.Cu
  anchor 6.351 mm away returns `NO_LEGAL_ESCAPE`, so there is no promotable
  transaction. Evidence/harness: `u3_xgpio1_viasite_enum_078.py` / `.json`.
  Board remains byte-identical (`a4b93b9b…`); no owner decision; readiness
  remains 78%. **Next:** replace the complete XGPIO0 branch after the five
  selected inner routes, then continue the terminal schedule only while each
  branch closes.
- **FBV2-P2-077 / D-375 (XGPIO1 target-bias/via-site characterization; no
  authoritative PCB change):** 45 combinations of endpoint target-score bias
  all reserve the same In3 via pair at `(55.40,24.95)/(58.55,76.65)` mm. The
  only distinct pair fails its direct join and the compact D-374-derived staged
  set; target scoring cannot expose another legal site and is closed.
  Evidence/harness: `u3_xgpio1_viasite_077.py` / `.json`. Board remains
  byte-identical (`a4b93b9b…`); no owner decision; readiness remains 78%.
  **Next:** add a bounded reachable-via-site enumeration/explicit-selection
  capability, especially at U3.5, then join only distinct enumerated pairs.
- **FBV2-P2-076 / D-374 (XGPIO1 staged-waypoint characterization; no
  authoritative PCB change):** after the four selected inner replacements,
  XGPIO1 reserves both In3 endpoints at `(55.40,24.95)/(58.55,76.65)` mm.
  Seventeen deterministic line-relative anchors were screened: six are blocked,
  two fail the R52-side first leg, and nine fail the U3-side second leg. No
  complete XGPIO1 route or transaction candidate exists; generic single-anchor
  staging is closed. Evidence/harness: `u3_xgpio1_waypoint_076.py` / `.json`.
  Board remains byte-identical (`a4b93b9b…`); no owner decision; readiness
  remains 78%. **Next:** bounded In3 endpoint-reservation target-bias/via-site
  sweep for XGPIO1, especially U3.5, then test direct/staged joins only across
  distinct legal via-site pairs.
- **FBV2-P2-075 / D-373 (complete-XGPIO1 inner replacement characterization;
  no authoritative PCB change):** after XGPIO6/XGPIO7 reservation and the
  selected In3 XGPIO5, In2 XGPIO4, In3 XGPIO2, and In3 XGPIO3 replacements,
  direct complete-branch replacement does not close XGPIO1 on either inner
  layer. In2 fails to reserve moved U3.5 (`NO_VIA_SITE`); In3 reserves its
  endpoint escapes but the long join fails `NO_PATH`. Both incomplete
  candidates have 16 added non-unconnected real KiCad DRC violations and are
  not promotable. Evidence/harness: `u3_xgpio1_inner_replay_075.py` / `.json`.
  Board remains byte-identical (`a4b93b9b…`); no owner decision; readiness
  remains 78%. **Next:** bounded XGPIO1-specific In3 staged-waypoint/anchor
  sweep after the four selected inner routes, preserving earlier transaction
  copper; do not retry the generic direct inner haul.
- **FBV2-P2-074 / D-372 (complete-XGPIO3 inner replacement characterization;
  no authoritative PCB change):** after XGPIO6/XGPIO7 reservation and the
  selected In3 XGPIO5, In2 XGPIO4, and In3 XGPIO2 replacements, XGPIO3 cannot
  reserve U3.7 on In2 but closes on In3 through `(55.10,29.75)/(60.90,78.85)`
  mm via sites. Replay advances to XGPIO1/U3.5, whose retained B.Cu anchor
  4.700 mm away fails `NO_LEGAL_ESCAPE`. The incomplete candidate restores
  158 remaining accepted copper items but still has real KiCad DRC regressions
  and is not promotable. Evidence/harness: `u3_xgpio3_inner_replay_074.py` /
  `.json`. Board remains byte-identical (`a4b93b9b…`); no owner decision;
  readiness remains 78%. **Next:** replace the complete XGPIO1 branch after
  In3 XGPIO3, then continue only if it closes.
- **FBV2-P2-073 / D-371 (complete-XGPIO2 inner replacement characterization;
  no authoritative PCB change):** after XGPIO6/XGPIO7 reservation, In3
  XGPIO5, and In2 XGPIO4 replay, XGPIO2 cannot reserve U3.6 on In2 but closes
  on In3 through `(54.95,27.30)/(61.90,77.85)` mm via sites. Replay advances
  to XGPIO3/U3.7, whose retained B.Cu anchor 4.699 mm away fails `NO_PATH`.
  The incomplete candidate restores 180 remaining accepted copper items but
  still has real KiCad DRC regressions and is not promotable. Evidence/harness:
  `u3_xgpio2_inner_replay_073.py` / `.json`. Board remains byte-identical
  (`a4b93b9b…`); no owner decision; readiness remains 78%. **Next:** replace
  the complete XGPIO3 branch after In3 XGPIO2, then continue only if it closes.
- **FBV2-P2-072 / D-370 (complete-XGPIO4 inner replacement characterization;
  no authoritative PCB change):** after XGPIO6/XGPIO7 reservation and D-369's
  selected In3 XGPIO5 route, the exact nine-item XGPIO4 branch is replaced
  cleanly by the qualified native-face/through-via haul on either In2 or In3.
  XGPIO4 is fully connected in both candidates; In2 is lower impact (nine
  clearance regressions versus ten) and replay advances to XGPIO2/U3.6, whose
  retained B.Cu anchor 3.964 mm away fails `NO_LEGAL_ESCAPE`. Incomplete replay
  still has real KiCad DRC regressions and is not promotable. Evidence/harness:
  `u3_xgpio4_inner_replay_072.py` / `.json`. Board remains byte-identical
  (`a4b93b9b…`); no owner decision; readiness remains 78%. **Next:** replace
  the complete XGPIO2 branch with the same terminal-specific inner-haul
  mechanism after In3 XGPIO5 and In2 XGPIO4, then continue only if it closes.
- **FBV2-P2-071 / D-369 (complete-XGPIO5 inner replacement characterization;
  no authoritative PCB change):** after XGPIO6/XGPIO7 reservation at the
  selected U3/R58 layout, the exact six-item XGPIO5 branch is replaced cleanly
  by the qualified D-331 native-face/through-via haul on either In2 or In3.
  XGPIO5 is fully connected in both candidates; replay advances to XGPIO4/U3.8,
  whose retained B.Cu anchor 3.714 mm away fails `NO_PATH`. In3 is the lower-
  impact XGPIO5 choice (one crossing versus two), but incomplete replay still
  has real KiCad DRC regressions and is not promotable. Evidence/harness:
  `u3_xgpio5_inner_replay_071.py` / `.json`. Board remains byte-identical
  (`a4b93b9b…`); no owner decision; readiness remains 78%. **Next:** replace
  the complete XGPIO4 branch with the same terminal-specific inner-haul
  mechanism after the In3 XGPIO5 route, then continue only if it closes.
- **FBV2-P2-070 / D-368 (local-scar replay characterization; no authoritative
  PCB change):** twelve scratch candidates combine the D-367 U3/R58 layout
  with six radial scar boundaries (0.35–2.00 mm) and both outer-layer replay
  orders. All reserve XGPIO6/XGPIO7 but fail first at XGPIO5/U3.9. Boundaries
  through 1.00 mm retain its unusable 5.890 mm B.Cu anchor (`NO_PATH`);
  1.50/2.00 mm remove that anchor and expose only a 49.590 mm F.Cu route
  (`NO_LEGAL_ESCAPE`). All candidates regress real KiCad DRC. Evidence/harness:
  `u3_local_scar_replay_070.py` / `.json`. Board remains byte-identical
  (`a4b93b9b…`); no owner decision; readiness remains 78%. **Next:** replace
  the complete XGPIO5 branch with a terminal-specific inner-layer haul to a
  stable non-U3 anchor, then extend only if that first-branch mechanism closes.
- **FBV2-P2-069 / D-367 (D-366 winner rank and exact replay; no authoritative
  PCB change):** real KiCad DRC/accepted-pair ranking selects R58 -0.5 mm north
  from the three pair-reserving layouts (16 added non-unconnected violations,
  tied with +0.5 mm east; -1.0 mm north adds 22).  After XGPIO6/XGPIO7 reserve,
  exact restoration of all 199 U3 incident items still causes 13 shorts, seven
  clearances and one crossing; XGPIO5/U3.9 again cannot attach to its retained
  B.Cu anchor 5.890 mm away (`NO_PATH`).  The R58 header-side connection was
  explicitly checked and remains closed.  Evidence/harness:
  `u3_r58_impact_replay_069.py` / `.json`. Board remains byte-identical
  (`a4b93b9b…`); no owner decision; readiness remains 78%. **Next:** map only
  the local collision-producing U3 branch geometry at the selected layout and
  replay that bounded corridor freshly; do not retry exact accepted templates.
- **FBV2-P2-068 / D-366 (U3/R57/R58 endpoint-cluster characterization; no
  authoritative PCB change):** with U3 held at 180°/+0.5 mm north after exact
  withdrawal of its 199 physical incident items and R57 fixed, three of nine
  R58 translations reserve both XGPIO6/XGPIO7 when XGPIO6 routes first: +0.5
  mm east, -0.5 mm north, and -1.0 mm north. Every candidate preserves unrelated
  accepted copper. Evidence/harness: `u3_r57_r58_refloor_068.py` / `.json`.
  Board remains byte-identical (`a4b93b9b…`); no owner decision; readiness
  remains 78%. **Next:** real-DRC/accepted-impact rank the three winners, then
  run exact complete affected-branch replay for the best legal layout before
  any replacement-aware promotion gate.
- **FBV2-P2-067 / D-365 (expanded U3 corridor characterization; no
  authoritative PCB change):** after exact withdrawal of the 199 physical
  accepted items in the eleven U3 incident branches, 48 larger U3 poses
  (90°/180°/270° with cardinal/diagonal 1.0/1.5 mm offsets) were screened in
  both XGPIO6/XGPIO7 orders. No pose reserves both routes: failures total 90
  `NO_VIA_SITE` and six `NO_LEGAL_ESCAPE`; 27 scratch candidates additionally
  fail the conservative frozen-signature filter. Evidence/harness:
  `u3_corridor_refloor_067.py` / `.json`. Board remains byte-identical
  (`a4b93b9b…`); no owner decision; readiness remains 78%. **Next:** bounded
  U3/R57/R58 endpoint-cluster refloorplan with complete affected-branch replay;
  do not retry U3-only poses or use blind vias without an owner manufacturing
  decision.
- **FBV2-P2-066 / D-364 (U3 topology-aware replay characterization; no
  authoritative PCB change):** XGPIO6 again reserves on In2 after the complete
  U3 incident cut-through. All 199 unique accepted branch-copper signatures
  restore exactly, preserving the eleven branches' accepted topology, but the
  180°/+0.5 mm-north U3 pose produces 12 real shorts, six clearances and one
  In2 crossing. XGPIO5/U3.9 is 5.890 mm from its retained B.Cu anchor and the
  first terminal attachment returns `NO_PATH`. Evidence/harness:
  `u3_topology_replay_066.py` / `.json`. Board remains byte-identical
  (`a4b93b9b…`); no owner decision; readiness remains 78%. **Next:** broader
  U3/local-corridor refloorplan for coherent XGPIO6/XGPIO7, explicitly excluding
  the D-359–D-364 pose/mechanism wall.
- **FBV2-P2-065 / D-363 (U3 XGPIO6 replay characterization; no authoritative
  PCB change):** the proven XGPIO6 In2 route reserves successfully after the
  exact 211-item/11-branch U3 boundary is withdrawn.  The first generic replay
  (`XGPIO5`) then fails `NO_LEGAL_ESCAPE`, because that primitive discards the
  accepted branch's inner-haul topology; it is not a valid transaction
  disproof.  Evidence/harness: `u3_xgpio6_replay_065.py` / `.json`. **Next:**
  build a deterministic topology-aware schedule for all eleven branches using
  their accepted routing roles, reserve XGPIO6 first, and run the replacement
  gate only if complete replay closes.  XGPIO7 remains deferred.  Board remains
  byte-identical (`a4b93b9b…`); no owner decision; readiness remains 78%.
- **FBV2-P2-064 / D-362 (U3 cut-through characterization; no authoritative
  PCB change):** the exact 211-item/11-branch U3 incident boundary was withdrawn
  scratch-only before pair reservation at the D-360 180°/+0.5 mm-north pose.
  XGPIO6 then routes on In2 when first, while XGPIO7 still returns
  `NO_VIA_SITE` both first and second. Accepted incident copper is therefore
  not the XGPIO7 wall cause; replay was correctly skipped because the pair
  cannot reserve. Board remains byte-identical (`a4b93b9b…`). Evidence:
  `u3_cutthrough_064.py` / `.json`. **Next:** reserve XGPIO6 alone and test
  complete incident-branch replay as a replacement transaction; keep XGPIO7
  deferred pending a broader refloorplan or owner-approved process change. No
  owner decision; readiness 78%.

- **FBV2-P2-063 / D-361 (U3 neighbor-cluster characterization; no
  authoritative PCB change):** 30 non-rigid U3/C5/TP33 layouts around the
  D-360 180°/+0.5 mm-north U3 seed were screened in both XGPIO6/XGPIO7 orders.
  Every one of the 60 attempts returns `NO_VIA_SITE`; moving C5 or TP33 does
  not improve real KiCad DRC and breaks 18–22 accepted cluster pad pairs.
  Those envelope neighbors are not the endpoint-wall cause. Board remains
  byte-identical (`a4b93b9b…`). Evidence: `u3_neighbor_cluster_063.py` /
  `.json`. **Next:** exact scratch cut-through using D-360's complete U3
  incident-branch boundary: withdraw those branches, reserve XGPIO6/XGPIO7
  first, and test complete replay while freezing all unrelated copper. No
  owner decision; readiness 78%.

- **FBV2-P2-062 / D-360 (U3 impact characterization; no authoritative PCB
  change):** complete connectivity-component mapping covers all 24 U3 incident
  pads and the eleven routed signal branches (211 copper items) at stable non-U3
  anchors.  Of the 15 D-359 poses, 180°/+0.5 mm north has the smallest combined
  real-DRC/neighbor boundary, but still enters 32 accepted items on 14 nets and
  overlaps the C5 and TP33 footprint envelopes.  Thus U3-only replay is not a
  closed transaction.  Board remains byte-identical (`a4b93b9b…`). Evidence:
  `u3_impact_map_062.py` / `.json`. **Next:** bounded non-rigid U3/C5/TP33
  cluster screen around the 180°/+0.5 mm-north seed, with all mapped U3 branches
  transactionally replayable and unrelated copper frozen. No owner decision;
  readiness 78%.

- **FBV2-P2-061 / D-359 (U3 pose characterization; no authoritative PCB
  change):** 15 orthogonal U3 poses (90°/180°/270°, each at origin and cardinal
  ±0.5 mm) were screened scratch-only for XGPIO6/XGPIO7 in both deterministic
  orders. All 30 attempts stop at `NO_VIA_SITE`; every pose also breaks 16–18
  accepted U3 pad pairs and adds real DRC findings. Board remains byte-identical
  (`a4b93b9b…`). Evidence: `u3_pose_eco_061.py` / `.json`. **Next:** map the
  complete U3 incident accepted-copper branches and local-neighbor collision
  boundary, then screen an exact replacement/refloorplan transaction; do not
  retry U3-only translation or rotation. No owner decision; readiness 78%.

- **FBV2-P2-060 / D-358 (U4 TRANSACTION PROMOTED):** the D-357-certified
  replacement transaction is authoritative. U4 moved exactly 270°/+0.5 mm
  east; the complete `BMI270_SDO_ADDR` branch was replayed and
  `BMI270_INT1_RAW` is now connected through legal F.Cu/In3.Cu/B.Cu copper
  with two 0.60/0.30 through vias. No unrelated copper or baseline pad
  connectivity regressed. G1–G47, probes 006–028 and Phase-B pass; real KiCad
  DRC remains exactly 5 hole-clearance / 1 mask-bridge / 199 library-footprint /
  499 unconnected-item findings. Board `a4b93b9b…`, 925 tracks / 87 vias /
  journal 138 / ratsnest 643; Phase-B 37/164 routed, 127 unrouted. **Next:**
  bounded U3 plus neighbor-cluster refloorplan with accepted-copper replay for
  the coherent XGPIO6/XGPIO7 pair. No owner decision; readiness remains 78%.

- **FBV2-P2-059 / D-357 (replacement-gate characterization; no authoritative
  PCB change):** the independent replacement-aware full-board gate regenerates
  and certifies D-356. Only U4 moves, exactly 270°/+0.5 mm east; all missing
  copper is inside the complete declared `BMI270_SDO_ADDR` branch, all added
  copper belongs to the two transaction nets, both nets are connected, and no
  baseline pad connectivity regresses. Ratsnest improves 644→643; real KiCad
  DRC remains exactly 5 hole-clearance / 199 library-footprint / 1 mask-bridge /
  499 unconnected findings. Board remains byte-identical (`02e263a7…`).
  Evidence: `u4_transaction_gate_059.py` / `.json`. **Next:** atomically promote
  the candidate and re-pin journal, fingerprints, probes, G-contract, ledger,
  and wall state. No owner decision; readiness 78%.

- **FBV2-P2-058 / D-356 (closed U4 transaction candidate; no authoritative
  change):** the exact U4 270°/+0.5 mm-east scratch transaction removes the
  complete eight-track `BMI270_SDO_ADDR` branch, reserves the new
  `BMI270_INT1_RAW` In3 haul, and replays the address strap. Both transaction
  nets are fully connected; no baseline pad pair regresses; unrelated copper
  is unchanged; real KiCad DRC remains exactly at 5 hole-clearance, 199 library,
  1 solder-mask and 499 unconnected findings after reference-plane refill.
  Board remains byte-identical (`02e263a7…`). Evidence:
  `u4_closed_branch_058.py` / `.json`. **Next:** independently regenerate and
  certify this candidate with the replacement-aware full-board transaction
  gate; do not promote before PASS.

- **FBV2-P2-057 / D-355 (U4 accepted-copper impact map; no authoritative
  change):** all ten D-354 routing-capable 180°/270° poses were measured with
  real KiCad DRC plus a conservative 0.300 mm expanded U4-pad envelope. The
  least-impact pose is U4 270°/+0.5 mm east: zero U4-attributable DRC findings,
  no neighbor footprint move, and the sole nearby `XGPIO8` F.Cu track remains
  legal. The only mandatory connectivity casualty is the complete accepted
  `BMI270_SDO_ADDR` strap branch already identified by D-354. Board remains
  byte-identical (`02e263a7…`). Evidence: `u4_impact_map_057.py` / `.json`.
  **Next:** exact scratch transaction at 270°/+0.5 mm east, replacing/replaying
  the complete address-strap branch and adding `BMI270_INT1_RAW` while freezing
  XGPIO8 and all unrelated copper; run the replacement-aware full-board gate
  only if the candidate is clean. No owner decision; readiness 78%.
- **FBV2-P2-056 / D-354 (U4 pose characterization; no authoritative change):**
  recovered and corrected the unfinished U4-neighbor ECO harness, then screened
  19 rotation/translation poses with the accepted reserved-escape inner-haul
  framework and real KiCad DRC. All five 180° poses and all five 270° poses route
  `BMI270_INT1_RAW`; every 0°/90° pose fails. None is add-only promotable: each
  routing-capable pose breaks both accepted U4 address-strap pad pairs and adds
  real clearance/hole-clearance/dangling or short findings. The authoritative
  board remains byte-identical (`02e263a7…`). Evidence:
  `u4_neighbor_eco_056.py` / `.json`. **Next:** impact-map accepted copper for
  the best 180°/270° poses and define the smallest exact transactional replay
  boundary before any placement/copper promotion. No owner decision; readiness 78%.
- **FBV2-P2-055 / D-353 (U20 TRANSACTION PROMOTED):** the D-352-certified
  replacement transaction is now authoritative. U20 moved exactly 180°/+0.5 mm
  north; the complete `ACC_3V3_EN`/`ACC_3V3_ILIM` branches were transactionally
  replaced and all six `ACC_POWER_FAULT_N` terminals are connected. No unrelated
  copper or baseline pad connectivity regressed. G1–G46, probes 006–028 and
  Phase-B pass; real KiCad DRC remains exactly 5 hole-clearance / 1 mask-bridge /
  199 library-footprint / 499 unconnected-item findings with no new copper class.
  Board `02e263a7…`, 918 tracks / 85 vias / journal 137 / ratsnest 644; Phase-B
  36/164 routed, 128 unrouted. **Next:** bounded U4-neighbor cluster ECO with
  accepted-copper replay for `BMI270_INT1_RAW`. No owner decision; readiness 78%.
- **FBV2-P2-054 / D-352 (replacement-gate characterization; no authoritative PCB
  change):** the deterministic replacement-aware full-board gate certifies D-351's
  exact U20 pose/copper transaction, preserves all unrelated copper/placement and
  baseline pad connectivity, closes all three transaction nets, improves ratsnest
  649→644, and leaves real KiCad DRC unchanged. G1–G45 and all standing probes pass on
  the untouched authority. Evidence: `u20_transaction_gate_054.py` / `.json`. Board
  remains `2cdc9f33…`. **Next:** atomically promote the candidate and re-pin journal,
  fingerprint, focused probe, G-contract, ledger and wall state. No owner decision;
  readiness 78%.
- **FBV2-P2-053 / D-351 (characterization; no copper/placement change):** the D-350
  boundary was expanded to the complete accepted `ACC_3V3_EN`/`ACC_3V3_ILIM` branches
  (31 B.Cu segments) at their pad anchors. At U20 180°/+0.5 mm north with controls
  reserved before FAULT, scratch routing connects both controls and all six
  `ACC_POWER_FAULT_N` terminals, preserves every baseline pad pair and all unrelated
  copper including XGPIO8, and leaves real KiCad DRC unchanged. This is a transaction
  candidate, not a promotion: the authoritative gate is add-only and has not certified
  intentional replacement/placement. Board `2cdc9f33…` remains unchanged. Evidence:
  `u20_closed_branch_053.json` / `.py`. **Next:** implement and run a replacement-aware
  authoritative full-board gate, transactionally re-pin accepted-copper contracts, and
  promote only on full PASS. No owner decision; readiness 78%.
- **FBV2-P2-052 / D-350 (characterization; no copper/placement change):** the D-349
  eight-item replacement scope was executed at U20 180°/+0.5 mm north. Exactly one EN and
  seven ILIM segments were removed in scratch; XGPIO8 and every other accepted item stayed
  frozen, both controls regained zero open edges, and no baseline pad pair broke. The fault route
  still returns `NO_PATH` even when reserved first, while real KiCad DRC adds two dangling retained-
  stub violations. Thus the eight items are a collision scope, not a topologically complete replay
  boundary; board `2cdc9f33…` remains unchanged. Evidence: `u20_local_replacement_052.json` / `.py`.
  **Next:** expand only along the two control branches to nearest stable pad/branch anchors, freeze
  XGPIO8/unrelated copper, and gate the placement/copper transaction. No owner decision; readiness 78%.
- **FBV2-P2-051 / D-349 (characterization; no copper/placement change):** the
  required geometric accepted-copper impact map bounded all six D-347 rotation winners with
  real KiCad DRC plus a 0.300 mm expanded U20-pad envelope. The least-impact pose is U20
  180°/+0.5 mm north: its six U20-related violations touch only legacy B.Cu on
  `ACC_3V3_ILIM`/`ACC_3V3_EN` (two shorts, three clearances, one mask bridge). The accepted
  XGPIO8 F.Cu long-haul enters the 2D envelope but causes no real violation; no neighboring
  footprint must move. Authoritative board remains byte-identical (`2cdc9f33…`). Evidence/harness:
  `u20_impact_map_051.json` / `.py`. **Next:** bounded scratch replacement/replay of only the
  eight mapped local control-copper items for the 180°/+0.5 mm north pose, freezing XGPIO8 and
  all other accepted copper; promote only if exact connectivity and the authoritative full-board
  gate pass. Open owner decisions: NONE; readiness 78%.
- **FBV2-P2-050 / D-348 (characterization; no copper/placement change):** exact
  add-only preservation was tested across all six D-347 rotation winners. Zero is promotable:
  the rotated U20 lands overlap unchanged legacy copper and create 2–7 real shorts per pose;
  none closes both controls and `ACC_POWER_FAULT_N`. Even the least disruptive 180°/+0.5 mm
  north pose preserves every baseline pad pair and reconnects both controls but retains two
  shorts, three clearances, two dangling-track errors, and no fault path. The authoritative board
  remains byte-identical (`2cdc9f33…`). Evidence/harness: `u20_exact_replay_050.json` / `.py`.
  **Next:** bounded wider U20/R97/R98 neighbor-cluster refloorplan with a geometric accepted-copper
  impact map and exact signature preservation; do not retry rotation over fixed legacy copper.
  Open owner decisions: NONE; readiness 78%.
- **FBV2-P2-049 / D-347 (characterization; no copper/placement change):** a bounded
  15-candidate orthogonal U20 rotation/non-rigid screen found six geometry/DRC-neutral
  routes, including an in-place 90° rotation that replays both controls and closes all six
  `ACC_POWER_FAULT_N` terminals with no broken baseline cluster pair. Promotion was correctly
  rejected by the full regression: the generic replay changes pinned accepted-copper signatures
  (`ACC` 31→23 tracks and Phase-A classification 432→484), causing 20 add-only contract failures.
  The authoritative board remains byte-identical (`2cdc9f33…`). Evidence/harness:
  `u20_rotation_eco_049.json` / `.py`. **Next:** use the proven in-place 90° geometry but build
  an exact accepted-copper-signature preservation/replay ECO for the affected U20 control lands;
  promote only after the unchanged full-board gate passes. Open owner decisions: NONE; readiness 78%.
- **FBV2-P2-048 / D-346 (characterization; no copper/placement change):** the coordinated
  `U20/R97/R98` rigid-cluster replay screen removed the accepted `ACC_3V3_EN`/`ACC_3V3_ILIM`
  copper in scratch, translated all three footprints together through 16 cardinal 0.25–1.00 mm
  candidates, replayed both control nets, and retried the full six-terminal `ACC_POWER_FAULT_N`
  route. All DRC-neutral east/north candidates replay both controls without losing a baseline
  cluster connection, but all 16 still fail the fault route at `U20.6`; zero promotion candidates.
  The authoritative board remains byte-identical (`2cdc9f33…`). Evidence/harness:
  `u20_cluster_eco_048.json` / `.py`. **Next:** bounded non-rigid/rotation refloorplan of the same
  three-part cluster, explicitly changing the U20.6 outward escape orientation; do not retry rigid
  translation. Open owner decisions: NONE; readiness 78%.
- **FBV2-P2-047 / D-345 (characterization; no copper/placement change):** the bounded `U20` placement-ECO impact map screened 16 scratch-only translations (cardinal ±0.25/0.50/0.75 mm plus ±0.50 mm diagonals) against the actual six-terminal `ACC_POWER_FAULT_N` route and real KiCad DRC. All 16 routes fail (`NO_LEGAL_ESCAPE` or `NO_PATH`) and every placement worsens DRC; north/south moves ≥0.50 mm also break 3–4 accepted U20 pad connections. The deterministic 4 mm neighbor map reduces the local replay cluster to `U20` + `R97` + `R98`. Authoritative board remains byte-identical (`2cdc9f33…`). Evidence/harness: `u20_endpoint_eco_047.json` / `.py`. **Next:** bounded coordinated `U20/R97/R98` refloorplan with an explicit replay plan for accepted `ACC_3V3_EN` and `ACC_3V3_ILIM` copper; do not retry U20 translation alone. Open owner decisions: NONE; readiness 78%.
- **FBV2-P2-046 / D-344 (characterization; no copper change):** bounded reuse of the accepted D-343 reserved-escape framework closed both remaining candidate questions without touching the authoritative PCB. `BMI270_INT1_RAW` cannot obtain a legal ordinary 0.60/0.30 mm through-via site from `U4.4` on In2 or In3. The multi-terminal owned-anchor screen for `ACC_POWER_FAULT_N` cannot escape `U20.6` at 0.200 mm on B.Cu; accepted tracks and neighboring `U20.5/U20.1/U20.4` lands bind the pocket before an anchor can form. Board remains byte-identical (`2cdc9f33…`). Evidence: `boxed_endpoint_reuse_046.json`. **Next:** bounded U20 plus local-neighbor placement-ECO impact map with accepted-copper replay; do not retry either endpoint route in place. Open owner decisions: NONE; readiness 78%.
- **FBV2-P2-045 / D-343 (promoted):** the accepted reserved-escape/inner-haul framework now closes the boxed two-pad `DISP_BL_CTL` backlight logic-control leg. `R109.2` escapes F.Cu, `U17.4` escapes B.Cu, and two ordinary 0.60/0.30 mm through vias join on In3. The authoritative full-board gate passed: five new copper items in scope, accepted copper preserved, `open_edges 1→0`, ratsnest 650→649, and real KiCad DRC unchanged. Board `2cdc9f33…`, 870 tracks / 85 vias / journal 132; Phase-B 35/164 routed. **Next:** reuse the now-proven boxed-endpoint mechanism on `BMI270_INT1_RAW` if its two endpoints admit legal reservations; otherwise characterize `ACC_POWER_FAULT_N` with a bounded multi-terminal anchor plan. Open owner decisions: NONE; readiness 78%.
- **FBV2-P2-044 / D-342 (characterization; no copper change):** exhausted all three two-endpoint permutations for an ordinary-through-via inner-layer anchor on the boxed `Net-(U1-EN)` reset RC network. Every pair can reserve and join on In2, but two permutations still cannot attach `U1.3` to `C1.2`; the third completes only with a 58.457 mm F.Cu pull-up attach (68.294 mm total), rejected as an excessive reset-sensitive detour. The prototype was removed and the authoritative board remains byte-identical (`d52daca8…`). Compact evidence: `mcu_en_inner_anchor_042.json`. **Next:** apply the layer-changing boxed-endpoint framework to `DISP_BL_CTL[_STRAP]`, `BMI270_INT1_RAW`, or `ACC_POWER_FAULT_N`, whose electrical role and geometry may admit a short attachment; do not retry MCU EN without a bounded U1/C1 neighbor-cluster ECO and accepted-copper replay plan. Open owner decisions: NONE; readiness 78%.
- **FBV2-P2-043 / D-341 (characterization; no copper/placement change):** the mandated U3-cluster accepted-copper impact map screened 16 scratch translations (cardinal ±0.25/0.50/1.00 mm plus ±0.50 mm diagonals) with the actual D-331 inner-haul primitive. All 32 XGPIO6/7 attempts fail `NO_LEGAL_ESCAPE` or `NO_VIA_SITE`; every placement also introduces real KiCad copper/clearance errors (and larger moves break 5–13 of the 13 accepted U3 pad pairs). The authoritative D-339 board remains byte-identical (`d52daca8…`). Compact deterministic evidence: `u3_endpoint_eco_041.json`; rerunnable harness: `u3_endpoint_eco_041.py`. **Next:** stop translating U3; advance the generic boxed-pad endpoint framework on `MCU_EN_RC`, `DISP_BL_CTL[_STRAP]`, `BMI270_INT1_RAW`, or `ACC_POWER_FAULT_N`, where an ordinary through-via remains physically possible. XGPIO6/7 require a materially larger neighbor-cluster re-floorplan or an owner-approved blind-via process. Open owner decisions: NONE; readiness 78%.
- **FBV2-P2-042 / D-340 (characterization; no copper change):** bounded the generic boxed-endpoint owned-copper anchor at the shared XGPIO6/XGPIO7 wall. Both endpoints have legal 0.200 mm outer-layer escapes, but neither U3.10 nor U3.11 can reach a through-via site that is legal on all six copper layers. A 20 mm reachability span and the board-minimum 0.50/0.30 mm through-via do not change that result; via-in-pad is physically unavailable on the 0.40 mm-tall U3 lands. The D-339 board remains byte-identical (`d52daca8…`, 867 tracks / 83 vias / ratsnest 650 / journal 131). **Next:** apply the boxed-endpoint screen to other qualified endpoints that admit ordinary through-vias; keep XGPIO6/XGPIO7 deferred pending a bounded U3-cluster accepted-copper impact map. Blind-via use would require an owner manufacturing-process decision and was not assumed. Readiness remains 78%.
- **FBV2-P2-041 / D-339 (promoted):** reused the accepted J1 `connector_fanout_plan` for adjacent `DISP_DC`; `U1.22↔J1.37` now has reserved F.Cu endpoint escapes, two ordinary 0.60/0.30 mm vias and an In2 haul. The authoritative 10-check gate passed: accepted copper preserved, `open_edges 1→0`, ratsnest 651→650, zero new/increased DRC class, unconnected_items 499 unchanged. Board `d52daca8…`, 867 tracks / 83 vias / journal 131; G1–G44, probes 006–028 and Phase-B pass (34/164 routed, 130 unrouted). **Next:** implement the generic boxed-pad endpoint-anchor framework, beginning with the shared XGPIO6/XGPIO7 endpoint/via-site wall; then apply it to other boxed endpoints where geometry qualifies. Open owner decisions: NONE; readiness 78%.
- **FBV2-P2-040 / D-338 (promoted):** implemented the missing bounded J1 `connector_fanout_plan`; `DISP_CS_N` now escapes `J1.38` and `R26.2` onto In2 with two 0.60/0.30 mm vias, then closes locally to `U1.18` on F.Cu. The authoritative full-board gate passed all 10 checks: accepted copper preserved, 3 pads one cluster (`open_edges 2→0`), ratsnest 653→651, zero new/increased DRC class, unconnected_items 499 unchanged. Board `7940bda8…`, 863 tracks / 81 vias / journal 130. **Next:** bounded framework reuse for adjacent `DISP_DC` (`J1.37↔U1.22`), then return to boxed endpoints. Open owner decisions: NONE; readiness 78%.
- **FBV2-P2-039 / D-337 (characterization; no copper or placement promotion):** D-336 recovery was independently reproduced (72 candidates plus G1-G42/probes/Phase-B/DRC). Eight coordinated cardinality-3 R5/R8/R6 layouts then yielded no complete route in 24 attempts. The remaining west-button wall is the fixed U2/pull-up cluster. D-332 stays byte-identical (`e5e6f4fc…`, 856/79, ratsnest 653, journal 128). **Next:** bounded J1 display-fanout framework; retain the larger U2 cluster ECO as fallback. Open owner decisions: NONE; readiness 78.
- **FBV2-P2-038 / D-336 (characterization; no copper or placement promotion):** 72 scratch cardinality-1 R5/R8/R6 moves (±0.5/1.0 mm, native/180°) were screened; conflicts reject most and every legal candidate remains `NO_PATH`/`NO_LEGAL_ESCAPE`. D-332 remains byte-identical (`e5e6f4fc…`, 856/79, ratsnest 653, journal 128), with G1–G42 + probes 023–027 + Phase-B + DRC unchanged and zero clearance class. **Next:** bounded coordinated west-button pull-up-column spread. Open owner decisions: NONE; readiness 78.
- **FBV2-P2-037 / D-335 (characterization; no copper change):** bounded 1.5/2.5 mm owned-B.Cu staging followed by a locked via/F.Cu transition fails at `R5.2` and `R8.2` before a staging corridor exists; the prototype was removed. D-332 remains byte-identical (`e5e6f4fc…`, 856/79, ratsnest 653, journal 128), with G1–G42 + probes 023–027 + Phase-B + KiCad DRC unchanged and zero clearance class. **Next:** bounded pull-up placement ECO screen for the west-button family. Open owner decisions: NONE; readiness 78.
- **FBV2-P2-036 / D-334 (characterization; no copper change):** bounded same-face anchor staging can move the boxed MCU EN pad, but cannot reach `C1.2`; the prototype was rejected and removed. D-332 remains byte-identical (`e5e6f4fc…`, 856/79, ratsnest 653, journal 128), and fresh G1–G42 + probes 023–027 + Phase-B + KiCad DRC pass with zero clearance class. **Next:** layer-changing/owned-copper endpoint framework for the coherent west-button family. Open owner decisions: NONE; readiness 78.
- **FBV2-P2-035 / D-333 (characterization; no copper change):** XGPIO6/XGPIO7 were fast-screened with the accepted D-331 inner-haul framework and both stopped at endpoint via-site reservation, before any promotable haul. The D-332 board remains byte-identical (`e5e6f4fc…`, 856 tracks / 79 vias / ratsnest 653 / journal 128). The wall registry now prevents blind replay. **Next:** bounded generic boxed-pad endpoint-anchor framework. Open owner decisions: NONE; readiness 78.
- **FBV2-P2-034 / D-332 (routine D-331 framework reuse; XGPIO4/XGPIO5 BATCH PROMOTED):** authoritative board `sha256 e5e6f4fc97c2677270f542f65d0037fb1329110a2ac844e84d2140f363d56e7d`, 856 tracks / 79 vias / 6 layers / 41 zones / ratsnest 653 / journal 128. The coherent low-speed batch adds 11 tracks and four standard vias on native outer escapes + In2 long hauls; both nets are connected and all accepted copper is preserved. G1–G42 PASS, probes 023–027 PASS, Phase-B PASS (32/164 routed, 132 unrouted), independent DRC unchanged with zero copper-clearance class. Compact evidence: `hardware/beta-v2/checks/routing_ledger.json`. **Next:** fast-screen XGPIO6/XGPIO7 as the remaining inner-haul batch, then generic boxed endpoints. Open owner decisions: NONE; readiness 78.
- **FBV2-P2-033 / D-331 (new In2/In3 low-speed long-haul framework; XGPIO2 PROMOTED):** GPT added an explicit opt-in framework that reserves each endpoint's native outer-layer escape, places one ordinary 0.60/0.30 through via per end, and joins the long haul on In2 (fallback In3); wide/high-current nets are refused and ordinary groups remain unchanged. `XGPIO2` passed the unchanged D-286 gate and was promoted: `sha256 98181354b3378e9cfb527e858b5120704adfa628c25ce8e6a351267a4f71e098`, 845 tracks / 75 vias / 6 layers / 41 zones / ratsnest 655 / journal 126. Copper: 8 tracks (2 F.Cu + 2 In2.Cu + 4 B.Cu), two vias; no prior regression or new DRC. G1–G41 PASS twice; probes 006–027 + Phase-B PASS; 30/164 rest nets routed. **Next:** small coherent XGPIO4/5/6/7 batch reuse after live fast screen. Open owner decisions: NONE; readiness 78. Full evidence: [`audits/2026-08-31-p2-033-d331-in2-long-haul-framework-xgpio2-promoted.md`](audits/2026-08-31-p2-033-d331-in2-long-haul-framework-xgpio2-promoted.md).
- **FBV2-P2-032 / D-330 (button-family framework fast screen; NO COPPER CHANGE):** pushed `5e73555` on `master` (`origin/master` equal). D-328's F.Cu endpoint hop does not generalize to `BTN_DOWN_N`/`BTN_A_N` (`NO_PATH`), and the bounded split In2/In3 join variant has no legal locked 0.60/0.30 via site at the binding endpoint on either signal layer. Dead candidates did not consume the full promotion suite. D-325 duplicate-pad support remains generic; D-328 remains accepted where geometry supports it; the three boxed west endpoints defer to the generic boxed-endpoint framework. Authoritative board remains byte-identical to D-328 (`27db293c…`, 837 tracks / 73 vias / ratsnest 656 / journal 125); G1–G40 PASS. **Next:** build the bounded In2/In3 long-haul framework for west XGPIO/appropriate low-speed signals, then return to generic boxed endpoints. Open owner decisions: NONE. Full evidence: [`audits/2026-08-31-p2-032-d330-button-family-framework-fast-screen.md`](audits/2026-08-31-p2-032-d330-button-family-framework-fast-screen.md).
- **FBV2-P2-031 / D-329 (framework-first transition boundary; NO COPPER CHANGE):** pushed `f02ea04` on `master` (`origin/master` equal). The owner-approved framework-first + coherent-batch strategy is active with the SAME D-286 full-board promotion gate. `routing_walls.json` records nine evidence-backed walls; the router blocks blind retries unless an explicit replacement framework is declared. G1–G40 PASS. Authoritative PCB remains byte-identical to D-328 (`sha256 27db293c8325832f585244b9d601103e8d72a6fcff13434a685f9472c21395c3`, 837 tracks / 73 vias / ratsnest 656 / journal 125). **Next:** finish the remaining `SWx` buttons as one bounded coherent batch where live geometry supports the accepted duplicate-pad/hop-anchor mechanics; then build the bounded In2/In3 long-haul framework for west XGPIO/appropriate low-speed hauls. Open owner decisions: NONE. Routing ~19%, overall 76%, readiness 78. Full evidence: [`audits/2026-08-31-p2-031-d329-routing-wall-registry-framework-first-transition.md`](audits/2026-08-31-p2-031-d329-routing-wall-registry-framework-first-transition.md).
- **FBV2-P2-030 / D-328 (this checkpoint — TWENTY-FIRST REST-OF-BOARD INCREMENT PROMOTED; GPT transition acceptance PASS):** GPT directly implemented, gated and promoted `BTN_RIGHT_N` without Claude. The D-327 common endpoint wall was closed by a bounded, opt-in hop-anchor plan: `R7.2↔U2.16` escapes locally on B.Cu through two ordinary 0.60/0.30 vias and joins on F.Cu; both physical `SW5.1` lands attach to the already-owned R7-side F.Cu via anchor. No rule, clearance, placement, footprint, topology or layer role changed; every group without the explicit plan remains on the old MST path. Full D-286 gate PASS: 18 new items in scope, four physical pads one cluster (`open_edges 3→0`), ratsnest 659→656, zero prior regressions, no new/increased DRC. Authoritative board `sha256 27db293c8325832f585244b9d601103e8d72a6fcff13434a685f9472c21395c3`, 837 tracks / 73 vias / 6 layers / 41 zones / journal 125. Copper is 16 tracks (12 F.Cu + 4 B.Cu) + two vias; nearest prior barrel 0.886 mm. `router_regression.py` G1–G39 PASS twice; `incremental_probe_006..026` + Phase-B PASS; independent DRC unchanged. **Next:** fresh evidence screen of `BTN_DOWN_N`/`BTN_A_N`/`BTN_LEFT_N` for safe reuse of the hop-anchor topology or select the next clean functional net; promote only on full gate PASS. Open owner decisions: NONE. Routing ~19%, overall 76%, readiness 78. Full evidence: [`audits/2026-08-31-p2-030-d328-btn-right-hop-anchor-promoted.md`](audits/2026-08-31-p2-030-d328-btn-right-hop-anchor-promoted.md).
- **FBV2-P2-029 / D-327 (this checkpoint — CHARACTERIZATION, NO COPPER CHANGE):** GPT directly executed the first hardware task under the new primary-engineer ownership policy. Three west navigation-button candidates were screened, scratch-routed and gated; all hit the same short B.Cu pull-up/PCAL9535A expander endpoint wall. `BTN_DOWN_N` routed its long west haul but not `R5.2↔U2.14`; `BTN_RIGHT_N` produced no legal copper; `BTN_A_N` routed its cross-haul and duplicate switch-land edge but not `R8.2↔U2.17`, so gate correctly rejected `open_edges 3→1`. Authoritative board remains byte-identical to D-326: `sha256 adbea36b8bbcfa393f2810e989c93dbcfab4052b5538f9a7169bc71ff98b3e3f`, 821 tracks / 71 vias / 6 layers / 41 zones / ratsnest 659 / journal 122. `router_regression.py` G1–G38 PASS twice; `incremental_probe_006..025` + Phase-B PASS; independent DRC unchanged. **Next:** bounded generic expander-endpoint escape improvement, then promote the first west button only on full D-286 PASS. Open owner decisions: NONE. Routing ~19%, overall 76%, readiness 78. Full evidence: [`audits/2026-08-31-p2-029-d327-west-button-expander-escape-characterization-no-promote.md`](audits/2026-08-31-p2-029-d327-west-button-expander-escape-characterization-no-promote.md).
- **FBV2-P2-028 / D-326 (this checkpoint — TWENTIETH REST-OF-BOARD INCREMENT PROMOTED; the navigation
  D-pad UP button `BTN_UP_N`, the SECOND net of the `SWx` user-button family, on the accepted D-325
  duplicate-ref MST framework with ZERO router-logic change; CLEANER than `BTN_B_N` — ONE through via, not
  two; AUTH `sha256 adbea36b8bbcfa393f2810e989c93dbcfab4052b5538f9a7169bc71ff98b3e3f`, 821 tracks / 71 vias /
  6 layers / 41 zones / ratsnest 659 / journal 122):** a governed CTO **ACCEPT + PROMOTE**. `BTN_UP_N` =
  {`SW2.1` button (two F.Cu tact-switch lands at `(60.220,96.750)`/`(68.180,96.750)`, the same 4-pin `PTS645`
  duplicate pad-"1" topology as SW7), `R4.2` pull-up (B.Cu), `U2.13` PCAL9535A expander GPIO (B.Cu)}. Two
  read-only screens on the live D-325 board (`w/screen_020.py` congestion + a faithful `physical_net_pads`
  MST vet) ranked it the CLEANEST of the five remaining nav buttons: shortest cross-haul **12.33 mm** and
  lowest congestion **201** (vs `BTN_A` 42.35/429, `BTN_DOWN` 44.00/352, `BTN_LEFT` 50.15/568, `BTN_RIGHT`
  56.89/508), because SW2 is in the SAME open south button field where `BTN_B_N` (SW7) already passed.
  `Net-(SW9-A)` (power-domain, touches U12.12 converter) and `BOOT_N` (characterized sensitive boot strap)
  EXCLUDED. **MST:** `SW2.1a↔SW2.1b` (7.96 mm SAME-LAYER F.Cu land-run, NO via — the D-325 lever edge) +
  `R4.2↔U2.13` (SAME-LAYER B.Cu run, NO via) + `U2.13↔SW2.1` (ONE 0.60/0.30 through via at `(61.100,95.400)`,
  In1/In4 re-poured once); **21 trk (6 F.Cu + 15 B.Cu) + 1 via.** ZERO router-logic change (a `GROUPS` entry +
  comment only). **Gate (real full-board, D-286) PASS all 10:** all four physical pads one cluster
  (`open_edges 3→0`, both `SW2.1` lands driven), ratsnest 662→659 (−3), no new/worse DRC (`clearance` 0),
  `unconnected_items` 499→499; realized copper 6.370 mm clear of `BAT_PROTECTED_P` (zero D-269), via 4.804 mm
  from the nearest barrel. **Tests (deterministic twice):** `router_regression.py` ALL PASS **G1–G38** (new G38
  pins the increment; G37 the D-325 framework lever retained; G1–G37 unchanged); `incremental_probe_006..025`
  + `phaseB_bringup_probe_005` (821/71/122; 28 routed rest nets, 136 unrouted) PASS; `live_fingerprint.py`
  bumped once; `phaseB` roster extended by `BTN_UP_N`; independent kicad-cli DRC identical to D-325;
  D-269/D-264/DRU A/B (committed D-325 vs promoted D-326) in the documented battery/power-tree intrinsic-flake
  envelope (`d269` PASS↔FAIL(2) both, `d264` 2-failed both, `dru` FAIL(2)=FAIL(2)), none involving `BTN_UP_N`.
  **NOTE:** the mandate quoted the pre-work sha as `…b973f5231e76…`; the live board / `live_fingerprint.py` /
  D-325 commit / this file all agree the true D-325 sha is `35d32343…b952e5390898764fd326742dc88b5e146cf0c5f292dc14a220`
  (they share only the 16-char prefix) — work proceeded on the verified live value, the mandate tail being a
  transcription artifact. **Open owner decisions: NONE;** autonomy continues. Starting HEAD `4028157` (D-325;
  pushed; `origin/master` identical). Rollback: pre-promotion `sha256 35d32343af5146b952e5390898764fd326742dc88b5e146cf0c5f292dc14a220`
  (committed D-325, HEAD `4028157`). **136/164 rest nets unrouted; PCB routing ~19 %, overall ~76 %, readiness
  ~78 % (JLCPCB file unchanged).** This checkpoint is written in the D-326 commit; a fresh session must confirm
  the live tip. Full analysis:
  [`audits/2026-08-31-p2-028-d326-twentieth-rest-of-board-incremental-increment-btn-up-n-promoted.md`](audits/2026-08-31-p2-028-d326-twentieth-rest-of-board-incremental-increment-btn-up-n-promoted.md).
- **FBV2-P2-027 / D-325 (prior checkpoint — DUPLICATE-REF MST FRAMEWORK FIX + `BTN_B_N` PROMOTED, the
  NINETEENTH rest-of-board increment and the FIRST that needed a framework change; AUTH
  `sha256 35d32343af5146b952e5390898764fd326742dc88b5e146cf0c5f292dc14a220`, 800 tracks / 70 vias / 6 layers /
  41 zones / ratsnest 662 / journal 119):** a governed CTO **ACCEPT + PROMOTE**. **Root cause:** `SW7`
  (Button_Switch_SMD:`SW_SPST_PTS645Sx43SMTR92`) is a 4-pin tact switch whose two mechanically-linked
  terminals BOTH carry pad number "1" on `BTN_B_N` at `(49.520,96.750)` and `(57.480,96.750)`, 7.96 mm apart;
  `qrouter.QBoard._scan` keys `self.pads[(net,"REF.NUM")]` so the second land overwrote the first and was
  invisible to the MST (D-323 gate FAIL `open_edges 2→1`), and `cmd_gate.net_open_edges()` ref-deduped the two
  lands in its own cluster count. **Fix (bounded, generic, deterministic; `incremental_router.py` ONLY,
  `qrouter.py` untouched → G1–G35 byte-identical):** `physical_net_pads()` keys MST nodes by physical
  `(ref,x,y)` (ordinary unique-pad nets return the exact `net_pads()` objects → byte-identical); `net_open_edges()`
  rewritten as a physical-pad union-find that counts copper clusters over physical lands, matching KiCad's own
  ratsnest. **Increment:** `BTN_B_N` (`SW7.1` button F.Cu / `R9.2` pull-up B.Cu / `U2.18` expander B.Cu) MST
  hubbed on `R9.2` → BOTH `SW7.1` lands (two 0.60/0.30 through vias in the OPEN south button field, In1/In4
  re-poured) + `R9.2→U2.18` B.Cu; 19 trk (3 F.Cu + 16 B.Cu) + 2 vias. **Gate (real full-board) PASS all 10:**
  all four physical pads one cluster (`open_edges 3→0`, both `SW7.1` lands driven), ratsnest 665→662 (−3), no
  new/worse DRC (`clearance` 0), `unconnected_items` 499→499; realized copper 10.68 mm clear of
  `BAT_PROTECTED_P` (zero D-269). **Tests (deterministic twice):** `router_regression.py` ALL PASS **G1–G37**
  (new G36 pins the increment, new G37 pins the framework lever; G1–G35 unchanged); `incremental_probe_006..024`
  + `phaseB_bringup_probe_005` (800/70/119; 27 routed, 137 unrouted) PASS; `live_fingerprint.py` bumped once;
  independent kicad-cli DRC identical to D-323; D-269/D-264/DRU A/B (committed D-323 vs promoted D-325) in the
  documented battery/power-tree intrinsic-flake envelope (`d269` FAIL(2)/`dru` FAIL(2) identical both, `d264` B
  no worse than A), none involving `BTN_B_N`. The whole `SWx` user-button family is now routable. **Open owner
  decisions: NONE;** autonomy continues. Starting HEAD `45f45bc` (D-324; pushed; `origin/master` identical).
  **137/164 rest nets unrouted; PCB routing ~19 %, overall ~76 %, readiness ~78 % (JLCPCB file unchanged).**
  This checkpoint is written in the D-325 commit; a fresh session must confirm the live tip.
- **FBV2-P2-026 / D-324 (prior checkpoint — CHARACTERIZATION, NO COPPER CHANGE; the board is byte-identical
  to committed D-323, `sha256 a7bf8bdc…`, 781 tracks / 68 vias / 6 layers / 41 zones / ratsnest 665 /
  journal 116):** a governed CTO **CHARACTERIZATION** — three genuinely-functional open-region candidates
  across three different subsystems were vetted and scratch-routed and **ALL hit characterized pad-escape
  walls at 0.200 mm**, so nothing was promotable via the proven mechanics without a deferred framework change
  (kept deferred by this mandate); autonomy CONTINUES, **no owner decision.** Starting HEAD `89acc71` (D-323;
  pushed; `origin/master` identical). ZERO copper change, ZERO router-logic change (three additive `GROUPS`
  characterization entries + comments only — the `MCU_EN_RC`/`DISP_CS_N`/`BTN_B_N` do-not-retry-record
  pattern). A fresh read-only screen (`w/screen_020.py`) measured all 138 unrouted rest nets (38 ALLOW / 100
  EXCL); the 38 ALLOW resolve to ~6 already-characterized walls + ~7 `SWx` duplicate-ref buttons (deferred) +
  converter/USB-C role-traps + the `BQ25185_STAT` power-tree pair + three huge hauls + only THREE
  genuinely-clean functional candidates. A read-only geometry vet (`w/vet_021.py`) measured the three, each
  then scratch-routed: **(1) `BMI270_INT1_RAW`** (BMI270 IMU INT1 sensor-side leg `U4.4` B → series `R18.1` F,
  R18-isolated from the D-318 MCU-side strap; would COMPLETE the IMU interrupt path like D-308 completed
  D-304) → FAIL `NO_FAR_RUN` at 0.200 mm (R18.1 boxed in the dense MCU-south pocket, no F.Cu exit; the
  `MCU_EN_RC` class); **(2) `ACC_POWER_FAULT_N`** (ACC 3V3 power-fault status `U20.6`+`U22.6`/`R103.2`/`TP27`+
  `TP33` → `U3.18`, all B.Cu) → FAIL `NO_LEGAL_ESCAPE` on `U20.6` (boxed by own-part pads U20.5/U20.1/U20.4;
  3 of 5 edges route but the net can't complete; the `ISET`/`XGPIO2` boxed-pin class); **(3) `DISP_BL_CTL`**
  (backlight-driver control leg `R109.2` F → `U17.4` TPS61169 CTRL logic input B, R109-isolated) → FAIL
  `NO_FAR_RUN` at 0.200 mm (R109.2 in the same U1.16/backlight cluster that walled `DISP_BL_CTL_STRAP` at
  D-323). None has a bounded fix; all three `GROUPS` entries carry their OUTCOME annotation. Board untouched
  (`sha256 a7bf8bdc…` re-verified before/after; route writes only gitignored scratch;
  `incremental_baseline_006.json` reverted stale-by-design). Integrity all PASS: `router_regression` G1–G35
  deterministic twice; `incremental_probe_006..023` + `phaseB_bringup_probe_005` (781/68/116; 26 routed, 138
  unrouted) PASS; NO fingerprint bump / NO new probe (no copper — the D-315 precedent); independent kicad-cli
  DRC identical (clearance 0); D-269/D-264/DRU trivially unchanged (byte-identical board → no regression
  possible). **STRUCTURAL FINDING:** after 18 promoted increments the readily-clean open-region functional
  seam reachable by the proven F/B same-layer + single-through-via mechanics is essentially mined out — the
  138 remaining rest nets are dominated by role-excluded traps (~100), characterized walls, the `SWx`
  duplicate-ref button family, the saturated west-XGPIO F.Cu corridor, J1 display-FPC hauls, and boxed
  MCU/IC-pin pockets. **P2-027 recommendation:** explicitly SELECT one deferred bounded framework task — the
  **duplicate-ref MST** (unlocks the ~7-net `SWx` user-input button family; `BTN_B_N` already routed ALL OK
  at D-323, failed only on the collapse — highest value) is recommended, or the In2/In3 inner-layer west-XGPIO
  traverse. Rollback: not applicable (no copper change). Full analysis:
  [`audits/2026-08-31-p2-026-d324-characterization-three-pad-escape-walls-no-promote.md`](audits/2026-08-31-p2-026-d324-characterization-three-pad-escape-walls-no-promote.md).
  **138/164 rest nets unrouted; PCB routing ~18 %, overall ~76 %, readiness ~78 % (JLCPCB file unchanged).**
- **FBV2-P2-025 / D-323 (prior checkpoint — EIGHTEENTH REST-OF-BOARD INCREMENT PROMOTED; the accelerometer/
  add-on presence-detect `ACC_DETECT_N`, a 3-pad cross-layer net = ONE 0.60/0.30 through via + ONE same-layer
  B.Cu run, in an OPEN region whose realized copper clears `BAT_PROTECTED_P` by 3.88 mm (zero D-269); a genuine
  functional detect, promoted after the cleaner-class `DISP_BL_CTL_STRAP` hit a characterized local wall and
  `BTN_B_N` failed the gate on a duplicate-ref tact-switch connectivity limit; ZERO router-logic change):** a
  governed CTO **ACCEPT + PROMOTE** — `ACC_DETECT_N` (`R64.1` detect divider F.Cu + `R129.2` series B.Cu +
  `U3.17` PCAL expander GPIO B.Cu) is on the authoritative board with **no Phase-A / prior-increment casualty
  and no new DRC**; autonomy CONTINUES, **no owner decision.** Starting HEAD `36ffb2d` (D-322; pushed;
  `origin/master` identical; AUTH `a861e30e…`, 759/67, ratsnest 667, journal 114). A read-only screen
  (`w/screen_020.py`) measured the remaining unrouted rest nets (auto-classifier trap re-confirmed:
  converter-switching `Net-(L1/U12/U13-*)`/`BL_SW`, IR-emitter `IR_LED_A/K`, USB-C `Net-(J3-*)` rejected on
  measured role). A focused read-only geometry vet (`w/vet_021.py`, re-verified live) measured the
  genuinely-functional shortlist: `ACC_DETECT_N` (3-pad, 1 via, edges 19.64 mm CROSS + 19.31 mm same-B, cong
  103, straight-MST **2.750 mm** from BPP), `DISP_BL_CTL_STRAP` (4-pad F.Cu, no via, cong 185, 37.854 mm),
  `BTN_B_N` (3-pad, 1 via, cong 141, 11.025 mm). **DISP_BL_CTL_STRAP characterized wall (cleaner class, tested
  FIRST):** the display backlight-control strap (`U1.16` MCU / `TP2.1` / `R108.1`+`R109.1`, isolated by R109
  from the downstream `DISP_BL_CTL`→`U17.4` driver) returned `NO_PATH` at 0.200 mm on **ALL THREE** MST edges
  (5.44 + 10.30 + 24.77 mm; none even at the 0.05/0.025 mm fine grid) — the dense MCU/backlight pad pocket
  (cong 185; vet nearest-copper 0.022 mm to the accepted D-318 `BMI270_INT1_STRAP`, 0.111 mm to
  `SD_CARD_DETECT_N`) boxes every terminal (the `MCU_EN_RC` boxed-pocket lesson repeated); `GROUPS` annotated
  (do NOT retry at 0.200 mm). **`BTN_B_N` gate-fail on a duplicate-ref connectivity limit (routed OK, NOT
  promoted):** the nav/boot button (`SW7.1` F.Cu → `R9.2` pull-up B.Cu → `U2.18` expander B.Cu) routed ALL OK
  but SW7 is a 4-pin tactile switch whose two mechanically-linked terminals BOTH carry pad "1" on `BTN_B_N` at
  (49.520,96.750) and (57.480,96.750), 7.96 mm apart; the framework's per-ref MST (`pads_by_ref`) collapses
  them to one node → the second terminal is never driven → one permanent open ratsnest edge (open_edges 2→1,
  gate FAIL). A connectivity gap of the WHOLE duplicate-ref button family, NOT a copper casualty — the
  authoritative board was never touched; `GROUPS` annotated (deferred "duplicate-ref MST" framework task).
  **SELECTED** `ACC_DETECT_N` (three distinct-ref pads, gates clean). New `GROUPS['ACC_DETECT_N']` (`layer='B'`,
  Default 0.200 mm, `via_dia`/`via_drill` 0.60/0.30, no `via_offset`); `incremental_router.py`/`qrouter.py`
  routing logic UNCHANGED. **Route** ALL OK (`R129.2↔U3.17` 35.311 mm B.Cu + `R129.2↔R64.1` 20.861 mm B+F-via;
  22 seg = 3 F.Cu + 19 B.Cu, 1 through via @(57.900,38.800)). **Promoted:** `sha256 a861e30e…` →
  **`a7bf8bdc11f1bc39303c6f6b6c801e3a4a575add64596cc4be20745c57f9f626`**; tracks 759 → **781** (+22: 3 F.Cu +
  19 B.Cu 0.200 mm); vias 67 → **68** (+1 through via); 6 layers / 41 zones; ratsnest 667 → **665** (−2);
  journal 114 → **116** (+2 REST_INC edges). **Gate PASS every check** (real full-board, D-286: 0 Phase-A
  altered, 22 new items + 1 via all target-net, only In1/In4 GND planes re-poured for the anti-pad — other 39
  zones identical, net open_edges 2→0, 0 prior pairs regressed, via 34.157 mm from every barrel + realized
  copper 3.8831 mm from BPP, ratsnest −2 exact, no new/worse DRC, unconnected 499→499). **INTEGRITY / TESTS:**
  `router_regression.py` ALL PASS **G1–G35** twice (deterministic, 555 lines / 143 PASS, identical G-verdicts;
  new **G35** pins connectivity + copper legality 22 trk 3 F.Cu/19 B.Cu + 1 through via + via ≥0.80 mm from
  barrels + ADD-ONLY); new `incremental_probe_023.py` PASS; `_006..022` + `phaseB_bringup_probe_005`
  (781/68/116; **26 routed rest nets, 138 unrouted**) PASS. **Probe via-total generalization** (first new via
  since D-316, board total 67→68): the no-via probes `incremental_probe_018..022` had their board-total pin
  generalized from a hard-coded `67` to `len(via) == EXPECT_VIAS` (the `live_fingerprint` SoT) with each
  probe's per-net `len(i_via) == 0` contract KEPT — semantically sound + regression-safe (all 8 prior
  via-probes already pin the total via `EXPECT_VIAS`); `incremental_probe_023.py`'s board-total pin aligned to
  the same convention (per-net `i_via == 1` kept). `live_fingerprint.py` bumped once (D-323);
  `incremental_baseline_006.json` left stale-by-design (reverted — the gate computes its baseline live).
  Independent kicad-cli DRC `{solder_mask_bridge:1, hole_clearance:5, lib_footprint_issues:199,
  unconnected_items:499}` (`clearance` 0), A/B identical on committed D-322 vs promoted D-323. **D-269/D-264/DRU
  board-swap A/B** (committed D-322 vs promoted D-323, via `AQROOT_BETA_V2_PROJECT` override, 4 runs each):
  `dru` FAIL(2)=FAIL(2) **IDENTICAL**; `d269` flips (promoted PASS,FAIL(2),FAIL(2),FAIL(2) / committed
  FAIL(2)×4, count always 2) and `d264` flips (promoted 2,1,2,3 / committed 2,1,2,1) — the documented intrinsic
  non-determinism, not a regression (new copper is peripheral, realized 3.88 mm from BPP near R64/R129/U3.17,
  away from the BAT-divider/sense corridors these synthetic probes test); live AUTH sha re-verified
  `a7bf8bdc…` after the swap. **Open owner decisions: NONE;** `JLCPCB_READINESS` ~78 % (authoritative; JLCPCB
  file unchanged). Rollback: pre-promotion `sha256 a861e30e…` (committed D-322, parent `36ffb2d`). **Next:
  FBV2-P2-026 — route the next clean rest-of-board increment (single net or small coherent local group in an
  open region — a fresh screen pick) at its netclass Default under the D-286 gate; add
  `incremental_probe_024.py`+`G36` on promote; continue avoiding the west XGPIO corridor, `U11_PROG`/
  `PWR_SENSE`, RF/NFC/USB/crystals/switching/class-D/rails/community-header mass, the auto-ALLOW
  converter-switching/USB-C connector traps, and every characterized wall (`MCU_EN_RC`, the J1
  display-connector haul `DISP_CS_N`/`DISP_DC`, `BOOT_N`, the `DISP_BL_CTL_STRAP` boxed pocket); do NOT retry
  the `SWx` duplicate-ref button family until a duplicate-ref MST lands; hold the inner-layer west-XGPIO haul as
  a deferred framework task; 138/164 rest nets unrouted.** Full analysis:
  [`audits/2026-08-31-p2-025-d323-eighteenth-rest-of-board-incremental-increment-acc-detect-n-promoted.md`](audits/2026-08-31-p2-025-d323-eighteenth-rest-of-board-incremental-increment-acc-detect-n-promoted.md).
  This checkpoint is written in the D-323 commit; a fresh session must confirm the live tip.
- **FBV2-P2-024 / D-322 (prior checkpoint — SEVENTEENTH REST-OF-BOARD INCREMENT PROMOTED; the reserved/spare
  community expander GPIO `RESERVED_SPARE`, a 3-pad ALL-B.Cu SAME-LAYER MST with NO via, in an OPEN region
  15.5 mm clear of `BAT_PROTECTED_P`; the held clean alternate, promoted after the meaningful display-control
  candidates `DISP_CS_N`/`DISP_DC` hit a characterized J1 display-FPC-connector wall and `BOOT_N` routed only
  via poor 2.5× detours; ZERO router-logic change):** a governed CTO **ACCEPT + PROMOTE** — `RESERVED_SPARE`
  (`R130.2` + `TP41.1` test point + `U23.7` PCAL community expander, all B.Cu SMD) is on the authoritative
  board with **no Phase-A / prior-increment casualty and no new DRC**; autonomy CONTINUES, **no owner
  decision.** Starting HEAD `e3e2a8d` (D-321; pushed; `origin/master` identical; AUTH `68d44b54…`, 749/67,
  ratsnest 669, journal 112). A fresh read-only screen (`w/screen_020.py`) measured all **140** unrouted rest
  nets → **40 ALLOW / 100 EXCL** (auto-classifier trap re-confirmed: converter-switching `Net-(L1/U12/U13-*)`/
  `BL_SW`, IR-emitter `IR_LED_A/K`, USB-C `Net-(J3-*)` rejected on measured role). A focused read-only geometry
  vet (`w/vet_021.py`) measured the mandate's shortlist + two other genuinely-functional candidates:
  `RESERVED_SPARE` (B.Cu, cong 84, short 3.5+9.8 mm edges, **15.5 mm clear of BPP → zero D-269**), `DISP_CS_N`
  (F.Cu, cong 184), `DISP_DC` (F.Cu, cong 203), `BOOT_N` (F.Cu, cong 231), `DISP_BL_CTL_STRAP` (F.Cu, cong
  185). **J1 display-FPC-connector wall characterized (prefer meaningful function over a spare):** the
  strongest meaningful pick `DISP_CS_N` (the display SPI chip-select `U1.18` MCU + `R26.2` series + `J1.38`
  display FPC, the direct analog of D-321's `SD_CS_N`) was scratch-tested FIRST — its short MCU-side edge
  `R26.2↔U1.18` (2.5 mm) routes clean off the series resistor, but the long `J1.38↔R26.2` haul to the tight
  display connector returns `NO_PATH` at 0.200 mm (none even at the 0.05/0.025 mm fine grid); `DISP_DC` (`U1.22
  → J1.37`, the adjacent FPC pin, single 38.5 mm haul off the boxed MCU pad) ALSO returns `NO_PATH` — confirming
  the J1 display-connector interior haul as a **shared local wall**. `GROUPS['DISP_CS_N']`/`['DISP_DC']`
  annotated (do NOT naively retry the connector haul at 0.200 mm). **`BOOT_N` set aside:** the meaningful non-J1
  alternative (ESP32 boot-mode strap `SW1.1` + `R2.2` + `U1.27` GPIO0) routed ALL OK but only via poor 2.5×
  detours (`R2.2↔U1.27` 62.9 mm vs 25.4 mm straight; `U1.27↔SW1.1` 47.2 mm vs 22.4 mm) = ~110 mm of meandering
  copper across the congested MCU interior for a boot-critical strap whose reset-level sensitivity the mandate
  flagged — not equally clean, so the meaningful>spare rule does not force it. **SELECTED** the held clean
  alternate `RESERVED_SPARE` (all three pads B.Cu → both MST edges SAME-LAYER B.Cu runs with NO via, the
  cleanest class). `GROUPS['RESERVED_SPARE']` already existed (held since D-321); `incremental_router.py`/
  `qrouter.py` routing logic UNCHANGED. **Route** ALL OK (two B.Cu runs R130.2↔U23.7 4.434 mm + U23.7↔TP41.1
  10.939 mm, 10 seg, 0 via). **Promoted:** `sha256 68d44b54…` →
  **`a861e30e5760515288ef9a3fc0c21ea6d3e9c31409f9181dd66d56ed0628efd1`**; tracks 749 → **759** (+10 B.Cu
  0.200 mm); vias **67** (unchanged — no via); 6 layers / 41 zones; ratsnest 669 → **667** (−2); journal 112 →
  **114** (+2 REST_INC edges). **Gate PASS every check** (real full-board, D-286: 0 Phase-A altered, 10 new
  items all target-net, 0 zones fill-changed — no via, net open_edges 2→0, 0 prior pairs regressed, ratsnest
  −2 exact, no new/worse DRC, unconnected 499→499). **INTEGRITY / TESTS:** `router_regression.py` ALL PASS
  **G1–G34** twice (deterministic; new **G34** pins connectivity + B.Cu legality + 0 vias + ADD-ONLY); new
  `incremental_probe_022.py` PASS; `_006..021` + `phaseB_bringup_probe_005` (759/67/114; **25 routed rest nets,
  139 unrouted**) PASS; `live_fingerprint.py` bumped once (D-322); `incremental_baseline_006.json` left
  stale-by-design (reverted — the gate computes its baseline live). Independent kicad-cli DRC
  `{solder_mask_bridge:1, hole_clearance:5, lib_footprint_issues:199, unconnected_items:499}` (`clearance` 0,
  0 schematic-parity). **D-269/D-264/DRU board-swap A/B** (committed D-321 vs promoted D-322, via
  `AQROOT_BETA_V2_PROJECT` override): `d269` FAIL(2)=FAIL(2) and `dru` FAIL(2)=FAIL(2) **IDENTICAL**; `d264`
  differed in single runs (3 vs 2) but four-run repeats proved intrinsic (flips 1,2,2,2 on the byte-identical
  committed D-321 board and 2,1,1,3 on the byte-identical promoted D-322 board) — the documented intrinsic
  non-determinism, not a regression (new copper is B.Cu near U23/R130/TP41, ~15 mm from the BAT-divider/sense
  corridors these synthetic probes test); live AUTH sha re-verified `a861e30e…` after the swap. **Open owner
  decisions: NONE;** `JLCPCB_READINESS` ~78 % (authoritative; JLCPCB file unchanged). Rollback: pre-promotion
  `sha256 68d44b54…` (committed D-321, parent `e3e2a8d`). **Next: FBV2-P2-025 — route the next clean
  rest-of-board increment (single net or small coherent local group in an open region — a fresh screen pick) at
  its netclass Default under the D-286 gate; add `incremental_probe_023.py`+`G35` on promote; continue avoiding
  the west XGPIO corridor, `U11_PROG`/`PWR_SENSE`, RF/NFC/USB/crystals/switching/class-D/rails/community-header
  mass, the auto-ALLOW converter-switching/USB-C connector traps, the `MCU_EN_RC` characterized wall and the
  J1 display-connector-haul wall (`DISP_CS_N`/`DISP_DC`); hold the inner-layer west-XGPIO haul as the deferred
  framework task; 139/164 rest nets unrouted.** Full analysis:
  [`audits/2026-08-31-p2-024-d322-seventeenth-rest-of-board-incremental-increment-reserved-spare-promoted.md`](audits/2026-08-31-p2-024-d322-seventeenth-rest-of-board-incremental-increment-reserved-spare-promoted.md).
  This checkpoint is written in the D-322 commit; a fresh session must confirm the live tip.
- **FBV2-P2-023 / D-321 (prior checkpoint — SIXTEENTH REST-OF-BOARD INCREMENT PROMOTED; the microSD SPI
  chip-select `SD_CS_N`, a genuine functional point-to-point control, 3-pad ALL-F.Cu SAME-LAYER MST with NO
  via, in an OPEN region 50.1 mm clear of `BAT_PROTECTED_P`; the mandate's headline candidate `Net-(U1-EN)`
  hit a characterized local wall and was set aside; ZERO router-logic change):** a governed CTO **ACCEPT +
  PROMOTE** — `SD_CS_N` (`U1.25` ESP32 MCU + `R25.2` + `J2.2` microSD socket, all F.Cu SMD), the microSD SPI
  chip-select control line, is on the authoritative board with **no Phase-A / prior-increment casualty and no
  new DRC**; autonomy CONTINUES, **no owner decision.** Starting HEAD `bb7fed4` (D-320; pushed; `origin/master`
  identical; AUTH `4e706490…`, 729/67, ratsnest 671, journal 110). A fresh read-only screen (`w/screen_020.py`)
  measured all **141** unrouted rest nets → **41 ALLOW / 100 EXCL**; the auto-classifier trap re-confirmed
  (converter-switching `Net-(L1-Pad1/2)`/`Net-(U13-SW/FB)`/`Net-(U12-*)`/`BL_SW`, IR-emitter power
  `IR_LED_A/K`, and USB-C connector `Net-(J3-CC1/CC2/SHIELD)` nets rejected on measured role). A focused
  read-only geometry vet (`w/vet_021.py`) measured the genuinely-clean functional shortlist: `Net-(U1-EN)`
  (cong 66), `RESERVED_SPARE` (cong 84), `SD_CS_N` (cong 102, **50.1 mm clear of `BAT_PROTECTED_P` → zero
  D-269**), `BOOT_N`/`DISP_DC` (cong 203). **MCU_EN_RC characterized wall (treat EN/BOOT sensitivity
  carefully):** the lowest-congestion candidate `Net-(U1-EN)` (ESP32 EN power-on-reset RC: `U1.3` EN + `R1.1`
  pull-up + `C1.2` filter cap) was scratch-tested FIRST and hit a LOCAL WALL — its natural MST short edge
  `C1.2↔U1.3` (7.81 mm) returns `NO_PATH` at 0.200 mm (none even at the 0.05/0.025 mm fine grid) in the dense
  U1-EN pad pocket (the D-320 `IR_TX_GPIO16` detour copper 0.101 mm from the straight line), and the other
  edge `U1.3↔R1.1` only routes with a 58.46 mm detour (2.6× the 22.28 mm straight) — a poor path for a reset
  line also carrying a 0.335 mm `USB_D_MCU_N` proximity flag; `GROUPS['MCU_EN_RC']` annotated **do NOT naively
  retry**, NOT promoted. **SELECTED** `SD_CS_N` — the held functional alternate, a genuine functional
  POINT-TO-POINT control (the microSD chip-select travels with its own synchronous SPI-A bus, benign
  coupling), all three pads on F.Cu → both MST edges SAME-LAYER F.Cu runs with NO via (cleanest class), zero
  D-269 — over `RESERVED_SPARE` (a spare of lower merit; routed ALL OK on scratch and HELD for FBV2-P2-024).
  New single-net `GROUPS['SD_CS_N']`; `incremental_router.py`/`qrouter.py` routing logic UNCHANGED. **Route**
  ALL OK (two F.Cu runs J2.2↔U1.25 48.420 mm + U1.25↔R25.2 21.081 mm, 20 seg, 0 via). **Promoted:**
  `sha256 4e706490…` → **`68d44b54df91d607f689215c0da5db249b13fcd1ac189b9ab78ceb6366d25e46`**; tracks 729 →
  **749** (+20 F.Cu 0.200 mm); vias **67** (unchanged — no via); 6 layers / 41 zones; ratsnest 671 → **669**
  (−2); journal 110 → **112** (+2 REST_INC edges). **Gate PASS every check** (real full-board, D-286: 0
  Phase-A altered, 20 new items all target-net, 0 zones fill-changed — no via, net open_edges 2→0, 0 prior
  pairs regressed, ratsnest −2 exact, no new/worse DRC, unconnected 499→499). **INTEGRITY / TESTS:**
  `router_regression.py` ALL PASS **G1–G33** twice (deterministic; new **G33** pins connectivity + F.Cu
  legality + 0 vias + ADD-ONLY); new `incremental_probe_021.py` PASS; `_006..020` + `phaseB_bringup_probe_005`
  (749/67/112; **24 routed rest nets, 140 unrouted**) PASS; `live_fingerprint.py` bumped once (D-321);
  `incremental_baseline_006.json` left stale-by-design (reverted — the gate computes its baseline live).
  Independent kicad-cli DRC `{solder_mask_bridge:1, hole_clearance:5, lib_footprint_issues:199,
  unconnected_items:499}` (`clearance` 0, 0 schematic-parity). **D-269/D-264/DRU board-swap A/B** (committed
  D-320 vs promoted D-321, via `AQROOT_BETA_V2_PROJECT` override): `dru` FAIL(2)=FAIL(2) **IDENTICAL**; `d269`
  and `d264` differed in single runs but four-run repeats proved intrinsic (`d269` flips FAIL,PASS,FAIL,PASS
  and `d264` flips 2,2,3,2 on the byte-identical D-320 board) — the documented intrinsic non-determinism, not
  a regression (new copper is F.Cu near U1.25/J2.2/R25.2, ~50 mm from the BAT-divider/sense corridors these
  synthetic probes test); live AUTH sha re-verified `68d44b54…` after the swap. **Open owner decisions: NONE;**
  `JLCPCB_READINESS` unchanged (~77 %). Rollback: pre-promotion `sha256 4e706490…` (committed D-320, parent
  `bb7fed4`). **Next: FBV2-P2-024 — route the next clean rest-of-board increment (single net or small coherent
  local group in an open region — e.g. `RESERVED_SPARE`, `BOOT_N`, `DISP_DC`, or a fresh screen pick) at its
  netclass Default under the D-286 gate; add `incremental_probe_022.py`+`G34` on promote; continue avoiding
  the west XGPIO corridor, `U11_PROG`/`PWR_SENSE`, RF/NFC/USB/crystals/switching/class-D/rails/community-header
  mass, the auto-ALLOW converter-switching/USB-C connector traps, and the `MCU_EN_RC` characterized wall; hold
  the inner-layer west-XGPIO haul as the deferred framework task; 140/164 rest nets unrouted.** Full analysis:
  [`audits/2026-08-31-p2-023-d321-sixteenth-rest-of-board-incremental-increment-sd-cs-n-promoted.md`](audits/2026-08-31-p2-023-d321-sixteenth-rest-of-board-incremental-increment-sd-cs-n-promoted.md).
  This checkpoint is written in the D-321 commit; a fresh session must confirm the live tip.
- **FBV2-P2-022 / D-320 (prior checkpoint — FIFTEENTH REST-OF-BOARD INCREMENT PROMOTED; the IR transmit
  carrier CONTROL leg `IR_TX_GPIO16`, a dedicated 2-pad point-to-point net, SAME-LAYER F.Cu MST with NO via, in
  an OPEN region 35.2 mm clear of `BAT_PROTECTED_P`; ZERO router-logic change):** a governed CTO **ACCEPT +
  PROMOTE** — `IR_TX_GPIO16` (U1.9 ESP32 GPIO16 → R22.1 series-drive resistor, both F.Cu SMD), the MCU-side
  low-current control leg of the IR transmit path, is on the authoritative board with **no Phase-A /
  prior-increment casualty and no new DRC**; autonomy CONTINUES, **no owner decision.** Starting HEAD
  `8d27e3a` (D-319; pushed; `origin/master` identical; AUTH `57dcc8af…`, 716/67, ratsnest 672, journal 109). A
  fresh read-only screen (`w/screen_020.py`) measured all **142** unrouted rest nets → **42 ALLOW / 100 EXCL**;
  the auto-classifier trap re-confirmed (several auto-ALLOW nets are actually converter-switching —
  `Net-(L1-Pad1/2)`, `Net-(U13-SW/FB)`, `Net-(U12-*)`, `BL_SW` — or USB-C connector — `Net-(J3-CC1/CC2/SHIELD)`
  — nets, all rejected on measured role). A focused read-only geometry vet (`w/vet_021.py`) measured the
  genuinely-clean functional shortlist AND **verified the isolation the mandate required**: the net
  `/IR_TX_GPIO16` = {`U1.9`, `R22.1`}; the far side `R22.2` belongs to the SEPARATE net `IR_GATE` ({`Q1.1`,
  `R22.2`, `R23.1`} = the Q1 gate/switch node) and the emitter-power path is `IR_LED_A`/`IR_LED_K` (D1 anode /
  Q1 drain) — both EXCLUDED switching/emitter nets, NOT part of this increment; series resistor R22 isolates
  the low-current MCU control leg from the switching output. Shortlist: **`IR_TX_GPIO16`** (2-pad F.Cu
  same-layer, netclass Default, NO via, congestion 38, **35.2 mm clear of `BAT_PROTECTED_P` → zero D-269
  involvement**), `Net-(U1-EN)` (cong 59, 2 MST edges incl. a 22 mm haul 0.335 mm from the USB_D_MCU_N diff
  pair, EN a more sensitive reset line), `RESERVED_SPARE` (cong 84, a spare of lower merit). **SELECTED**
  `IR_TX_GPIO16` — the best coherent low-risk *and meaningful* increment: simplest topology (2-pad, 1 MST edge,
  all F.Cu → NO via, no In1/In4 re-pour), a genuine functional MCU control role (not a spare, not switching/
  rail/RF-NFC/USB/bus-clock/community), the lowest congestion of the functional set, and completely clear of
  the D-269 wall. New single-net `GROUPS['IR_TX_GPIO16']`; `incremental_router.py`/`qrouter.py` routing logic
  UNCHANGED. **Route** ALL OK (single F.Cu run R22.1↔U1.9, a legal same-layer detour to 23.153 mm / 13 seg
  around the GND pinch on the straight 8.35 mm path, 0 via). **Promoted:** `sha256 57dcc8af…` →
  **`4e706490389655cb8b68f8c15249a813072f36a9ea9e6ffaeb1fdd2194c0bf34`**; tracks 716 → **729** (+13 F.Cu
  0.200 mm); vias **67** (unchanged — no via); 6 layers / 41 zones; ratsnest 672 → **671** (−1); journal 109 →
  **110** (+1 REST_INC edge). **Gate PASS every check** (real full-board, D-286: 0 Phase-A altered, 13 new
  items all target-net, 0 zones fill-changed — no via, net open_edges 1→0, 0 prior pairs regressed, ratsnest −1
  exact, no new/worse DRC, unconnected 499→499). **INTEGRITY / TESTS:** `router_regression.py` ALL PASS
  **G1–G32** twice (deterministic; new **G32** pins connectivity + F.Cu legality + 0 vias + ADD-ONLY); new
  `incremental_probe_020.py` PASS; `_006..019` + `phaseB_bringup_probe_005` (729/67/110; **23 routed rest nets,
  141 unrouted**) PASS; `live_fingerprint.py` bumped once (D-320); `incremental_baseline_006.json` left
  stale-by-design (reverted — the gate computes its baseline live). Independent kicad-cli DRC `{solder_mask_
  bridge:1, hole_clearance:5, lib_footprint_issues:199, unconnected_items:499}` (`clearance` 0). **D-269/D-264/
  DRU board-swap A/B** (committed D-319 vs promoted D-320, via `AQROOT_BETA_V2_PROJECT` override): `d269`
  FAIL(2)=FAIL(2) and `dru` FAIL(2)=FAIL(2) **IDENTICAL**; `d264` flips on both byte-identical boards
  (demonstrated D-320 1,2,2,1 and D-319 2,1,2,2 in four runs each) — the documented intrinsic non-determinism,
  not a regression (new copper is F.Cu near U1 at y≈111–119, ~35 mm from the BAT-divider/sense corridors these
  synthetic probes test); live AUTH sha re-verified `4e706490…` after the swap. **Open owner decisions: NONE;**
  `JLCPCB_READINESS` unchanged (~77 %). Rollback: pre-promotion `sha256 57dcc8af…` (committed D-319, parent
  `8d27e3a`). **Next: FBV2-P2-023 — route the next clean rest-of-board increment (single net or small coherent
  local group in an open region — e.g. `Net-(U1-EN)`, `RESERVED_SPARE`, `BOOT_N`, or a fresh screen pick) at
  its netclass Default under the D-286 gate; add `incremental_probe_021.py`+`G33` on promote; continue avoiding
  the west XGPIO corridor, `U11_PROG`/`PWR_SENSE`, RF/NFC/USB/crystals/switching/class-D/rails/community-header
  mass and the auto-ALLOW converter-switching/USB-C connector traps; hold the inner-layer west-XGPIO haul as
  the deferred framework task; 141/164 rest nets unrouted.** Full analysis:
  [`audits/2026-08-31-p2-022-d320-fifteenth-rest-of-board-incremental-increment-ir-tx-gpio16-promoted.md`](audits/2026-08-31-p2-022-d320-fifteenth-rest-of-board-incremental-increment-ir-tx-gpio16-promoted.md).
  This checkpoint is written in the D-320 commit; a fresh session must confirm the live tip with
  `git rev-parse HEAD` and `git rev-parse origin/master`.
- **FBV2-P2-021 / D-319 (FOURTEENTH REST-OF-BOARD INCREMENT PROMOTED; the debug-console
  UART transmit line `UART0_TXD_DBG`, a dedicated 2-pad point-to-point net, SAME-LAYER F.Cu MST with NO via, in
  an OPEN region 31.3 mm clear of `BAT_PROTECTED_P`; ZERO router-logic change):** a governed CTO **ACCEPT +
  PROMOTE** — `UART0_TXD_DBG` (U1.37 ESP32 MCU → TP35.1 debug test point, both F.Cu SMD), the debug console
  UART0 transmit output, is on the authoritative board with **no Phase-A / prior-increment casualty and no new
  DRC**; autonomy CONTINUES, **no owner decision.** Starting HEAD `c7313cc` (D-318; pushed; `origin/master`
  identical; AUTH `78bf82da…`, 709/67, ratsnest 673, journal 108). A fresh read-only screen
  (`w/screen_020.py`) measured all **143** unrouted rest nets → **43 ALLOW / 100 EXCL**; the auto-classifier
  trap re-confirmed (several auto-ALLOW nets are actually converter-switching — `Net-(L1-Pad1/2)`,
  `Net-(U13-SW/FB)`, `Net-(U12-*)`, `BL_SW`, the 16-pad power net `BQ25185_SYS` — or USB-C connector —
  `Net-(J3-CC1/CC2/SHIELD)` — nets, all rejected on measured role). A focused read-only geometry vet
  (`w/vet_021.py`) measured the genuinely-clean functional shortlist: **`UART0_TXD_DBG`** (2-pad F.Cu
  same-layer, netclass Default, NO via, congestion 9, **31.3 mm clear of `BAT_PROTECTED_P` → zero D-269
  involvement**), `IR_TX_GPIO16` (cong 38), `Net-(U1-EN)` (cong 56), `RESERVED_SPARE` (cong 84), and the
  vetted `BQ25185_STAT1/STAT2` pair — **REJECTED as NOT low-risk** (STAT2 straight-MST runs **0.024 mm** from
  `BAT_PROTECTED_P`, both 4-pad hauls thread the U11/BQ25185 power-tree wall; the mandate's "do not force a
  pair across a characterized power-tree wall" applies). `IR_LED_A/IR_LED_K` set aside (the IR emitter
  power/Q1 switch node — honor the switching-output exclusion). **SELECTED** `UART0_TXD_DBG` — the best
  coherent low-risk increment: simplest topology (2-pad, 1 MST edge, all F.Cu → NO via, no In1/In4 re-pour),
  clean electrical role (noncritical low-speed debug output, not switching/rail/RF-NFC/USB/bus-clock/
  community), lowest congestion, and completely clear of the D-269 wall. New single-net
  `GROUPS['UART0_TXD_DBG']`; `incremental_router.py`/`qrouter.py` routing logic UNCHANGED. **Route** ALL OK
  (single 31.755 mm F.Cu run, 0 via). **Promoted:** `sha256 78bf82da…` →
  **`57dcc8affb6c0f85f747fba025463b9cf0897c6712709692151020f56fdb8adf`**; tracks 709 → **716** (+7 F.Cu
  0.200 mm); vias **67** (unchanged — no via); 6 layers / 41 zones; ratsnest 673 → **672** (−1); journal 108 →
  **109** (+1 REST_INC edge). **Gate PASS every check** (real full-board, D-286: 0 Phase-A altered, 7 new items
  all target-net, 0 zones fill-changed — no via, net open_edges 1→0, 0 prior pairs regressed, ratsnest −1
  exact, no new/worse DRC, unconnected 499→499). **INTEGRITY / TESTS:** `router_regression.py` ALL PASS
  **G1–G31** twice (deterministic; new **G31** pins connectivity + F.Cu legality + 0 vias + ADD-ONLY); new
  `incremental_probe_019.py` PASS; `_006..018` + `phaseB_bringup_probe_005` (716/67/109; **22 routed rest nets,
  142 unrouted**) PASS; `live_fingerprint.py` bumped once (D-319); `incremental_baseline_006.json` left
  stale-by-design (reverted — the gate computes its baseline live). Independent kicad-cli DRC `{solder_mask_
  bridge:1, hole_clearance:5, lib_footprint_issues:199, unconnected_items:499}` (`clearance` 0). **D-269/D-264/
  DRU board-swap A/B** (committed D-318 vs promoted D-319, via `AQROOT_BETA_V2_PROJECT` override): `d269`
  FAIL(2)=FAIL(2) and `dru` FAIL(2)=FAIL(2) **IDENTICAL**; `d264` flips 1↔2 on the **byte-identical** D-319
  board (demonstrated 1,2,2,1 in four runs) — the documented intrinsic non-determinism, not a regression (new
  copper is F.Cu near U1 at y≈108–137, 31 mm+ from the BAT-divider/sense corridors these synthetic probes
  test); live AUTH sha re-verified `57dcc8af…` after the swap. **Open owner decisions: NONE;**
  `JLCPCB_READINESS` unchanged (~77 %). Rollback: pre-promotion `sha256 78bf82da…` (committed D-318, parent
  `c7313cc`). **Next: FBV2-P2-022 — route the next clean rest-of-board increment (single net or small coherent
  local group in an open region — e.g. `IR_TX_GPIO16`, `Net-(U1-EN)`, `RESERVED_SPARE`, or a fresh screen
  pick) at its netclass Default under the D-286 gate; add `incremental_probe_020.py`+`G32` on promote; continue
  avoiding the west XGPIO corridor, `U11_PROG`/`PWR_SENSE`, RF/NFC/USB/crystals/switching/class-D/rails/
  community-header mass and the auto-ALLOW converter-switching/USB-C connector traps; hold the inner-layer
  west-XGPIO haul as the deferred framework task; 142/164 rest nets unrouted.** Full analysis:
  [`audits/2026-08-31-p2-021-d319-fourteenth-rest-of-board-incremental-increment-uart0-txd-dbg-promoted.md`](audits/2026-08-31-p2-021-d319-fourteenth-rest-of-board-incremental-increment-uart0-txd-dbg-promoted.md).
  This checkpoint is written in the D-319 commit; a fresh session must confirm the live tip with
  `git rev-parse HEAD` and `git rev-parse origin/master`.
- **FBV2-P2-020 / D-318 (prior checkpoint — THIRTEENTH REST-OF-BOARD INCREMENT PROMOTED; the IMU/I2C-local
  interrupt strap `BMI270_INT1_STRAP`, 4-pad ALL-F.Cu same-layer MST with NO via; the FIRST clean increment
  OUTSIDE the saturated west-XGPIO F.Cu corridor; ZERO router-logic change):** a governed CTO **ACCEPT +
  PROMOTE** — `BMI270_INT1_STRAP` (R18.2/R110.1/TP3.1 F.Cu → U1.15 MCU GPIO), the MCU-side leg of the BMI270
  IMU INT1 interrupt, is on the authoritative board with **no Phase-A / prior-increment casualty and no new
  DRC**; autonomy CONTINUES, **no owner decision.** Starting HEAD `cacb68d` (D-317; pushed; `origin/master`
  identical). **The stale §5 (which still said FBV2-P2-018) was first repaired to the D-317 truth.** A fresh
  read-only screen (`w/screen_020.py`) measured all **144** unrouted rest nets (pad layers/span/MST/via-need/
  congestion/netclass + category screen) → **44 ALLOW / 100 EXCL** (rejected: west/east XGPIO corridor, RF/NFC/
  radio incl. `04_SPI_B`, USB, shared bus data/clocks, switching/boost/class-D, community-header mass,
  `U11_PROG`, `PWR_SENSE`, rails); the cleanest ALLOW no-via singletons were vetted on merit (several
  auto-ALLOW nets are actually converter-switching / USB-C connector nets — rejected). **SELECTED**
  `BMI270_INT1_STRAP` (the mandate's welcomed IMU/I2C-local category); all four pads on F.Cu → the 4-pad MST
  is **three SAME-LAYER F.Cu runs with NO via** — the cleanest class (no via, no In1/In4 re-pour, no
  via-clearance risk). New single-net `GROUPS['IMU_INT1_STRAP']`; `incremental_router.py`/`qrouter.py` routing
  logic UNCHANGED. **Promoted:** `sha256 d730c74d…` → **`78bf82da537a22697a860c23822599246e0534a8c4c311e12bc3d5b857a28816`**;
  tracks 691 → **709** (+18 F.Cu 0.200 mm); vias **67** (unchanged — no via); 6 layers / 41 zones; ratsnest
  676 → **673** (−3); journal 105 → **108** (+3 REST_INC edges). **Gate PASS every check** (real full-board,
  D-286: 0 Phase-A altered, 18 new items all target-net, 0 zones fill-changed — no via, net open_edges 3→0, 0
  prior pairs regressed, ratsnest −3 exact, no new/worse DRC, unconnected 499→499). **INTEGRITY / TESTS:**
  `router_regression.py` ALL PASS **G1–G30** twice (deterministic; new **G30** pins connectivity + F.Cu
  legality + 0 vias + ADD-ONLY); new `incremental_probe_018.py` PASS; `_006..017` + `phaseB_bringup_probe_005`
  (709/67/108; **21 routed rest nets, 143 unrouted**) PASS; `live_fingerprint.py` bumped once (D-318).
  Independent kicad-cli DRC `{solder_mask_bridge:1, hole_clearance:5, lib_footprint_issues:199,
  unconnected_items:499}` (`clearance` 0, 0 schematic-parity). **D-269/D-264/DRU board-swap A/B** (committed
  D-316 vs promoted D-318, via `AQROOT_BETA_V2_PROJECT` override): verdicts **IDENTICAL** (`d269` FAIL(2),
  `d264` 2-failed, `dru` FAIL(2) on both) — the known pre-existing synthetic/intrinsic flakes, not regressions
  (new copper is F.Cu near U1, far from the BAT tree the synthetic probes test); live AUTH sha re-verified
  `78bf82da…` after the swap. **Open owner decisions: NONE;** `JLCPCB_READINESS` unchanged (~77 %). Rollback:
  pre-promotion `sha256 d730c74d…` (committed D-316, parent `cacb68d`). **Next: FBV2-P2-021 — route the next
  clean rest-of-board increment (single net or small coherent local group in an open region — the vetted
  alternates `UART0_TXD_DBG`/`RESERVED_SPARE`/`BQ25185_STAT1+2`, or a fresh screen pick) at its netclass
  Default under the D-286 gate; add `incremental_probe_019.py`+`G31` on promote; continue avoiding the west
  XGPIO corridor, `U11_PROG`/`PWR_SENSE`, RF/NFC/USB/crystals/switching/class-D/rails/community-header mass;
  hold the inner-layer west-XGPIO haul as the deferred framework task; 143/164 rest nets unrouted.** Full
  analysis:
  [`audits/2026-08-31-p2-020-d318-thirteenth-rest-of-board-incremental-increment-imu-int1-strap-promoted.md`](audits/2026-08-31-p2-020-d318-thirteenth-rest-of-board-incremental-increment-imu-int1-strap-promoted.md).
  This checkpoint is written in the D-318 commit; a fresh session must confirm the live tip with
  `git rev-parse HEAD` and `git rev-parse origin/master`.
- **FBV2-P2-019 / D-317 (prior checkpoint — the SINGLE west XGPIO net `XGPIO2` is now a MEASURED
  CORRIDOR-CAPACITY WALL on the live D-316 board; NOT PROMOTED; ZERO authoritative copper change):** a governed
  CTO **CHARACTERIZATION** — `XGPIO2` (R53.1 F.Cu → U3.6 B.Cu), named at D-316 as the next single-net candidate,
  does **NOT** route on the live D-316 board; the authoritative PCB is **byte-identical to committed D-316**
  (`sha256 d730c74d186ebcc7d2f0aa513776778ce1cb9c9659029a2fffd5e2261e3ac97d`, 691 trk / 67 via / 6 layers / 41
  zones / ratsnest 676 / journal 105). Autonomy CONTINUES, **no owner decision.** Starting HEAD `6410e1f` (D-316;
  pushed; `origin/master` identical). **The pre-D-316 0.6859 mm BPP margin did NOT survive**, exactly as the task
  required verifying: `XGPIO2` alone @ 0.200 mm Default → **FAIL NO_FAR_RUN** (`w/screen_019.py`, one managed
  foreground process, 67 existing barrels injected incl. the D-316 XGPIO3 via) — escape from U3.6 succeeds but the
  long ~116 mm F.Cu haul from R53.1 has no legal 0.200 mm corridor. The **one authorized bounded alternative**,
  the existing D-310 `via_offset` transition relocation (2.5 mm, ZERO new router logic; `w/screen_019_offset.py`),
  **also FAILs NO_FAR_RUN** → the wall is the **haul corridor**, not the via site. **This is the D-315 wall
  realized:** D-315 proved the west F.Cu corridor admits ONE 116 mm haul; D-316 spent it on the `XGPIO3` haul (now
  REAL laid copper); `XGPIO2` (R53, U3.6) is the blocked second parallel haul. On the D-314 board `XGPIO2` alone
  routed at (55.300,78.150), but that site is now 0.450 mm centre-to-centre from the D-316 XGPIO3 barrel
  (55.300,77.700) — a hole-hole 0.150 mm < 0.25 collision. **INTEGRITY (board PRISTINE):** `sha256 d730c74d…`
  before/after both screens (no `route`/`gate`/`promote`; only gitignored `w/{SGL019_2,SGL019O_2}` scratch; no
  orphan; git tree clean). `router_regression.py` ALL PASS **G1–G29** twice (deterministic); `incremental_probe_006..017`
  + `phaseB_bringup_probe_005` (691/67/105; 20 routed rest nets, 144 unrouted) all PASS; `live_fingerprint.py` SoT
  still at D-316. Independent kicad-cli DRC `{solder_mask_bridge:1, hole_clearance:5, lib_footprint_issues:199,
  unconnected_items:499}` (clearance 0) matches the D-316 gate. D-269/D-264/DRU board-swap trivially byte-identical
  (current board IS committed D-316 → no regression possible; `d269` FAIL(2)/`d264` 2-failed/`dru` FAIL(2) are the
  known synthetic/intrinsic flakes characterized at D-316). **Opportunity:** the west F.Cu corridor is now
  saturated for single hauls — the remaining west members `XGPIO2/4/5/6/7` all contend for the one spent corridor
  as *second* hauls (do NOT keep retrying them); the In2/In3 inner signal layers remain fully available and an
  **inner-layer west-XGPIO haul** is the now concretely-justified deferred **framework** task. **Open owner
  decisions: NONE;** `JLCPCB_READINESS` unchanged (~77 %). Rollback: none needed (no authoritative change; HEAD
  advances by documentation only). **Next: FBV2-P2-020 — route the next clean rest-of-board increment OUTSIDE the
  saturated west XGPIO F.Cu corridor (single net or small coherent group) at its netclass Default under the D-286
  gate; add `incremental_probe_018.py`+`G30` on promote; do NOT retry single west XGPIO F.Cu hauls, the
  XGPIO2+XGPIO3 PAIR, or `U11_PROG`/`PWR_SENSE`; hold the inner-layer west-XGPIO haul as the deferred framework
  task; 144/164 rest nets unrouted.** Full analysis:
  [`audits/2026-08-31-p2-019-d317-xgpio2-single-west-corridor-capacity-wall-post-d316-characterized-no-promote.md`](audits/2026-08-31-p2-019-d317-xgpio2-single-west-corridor-capacity-wall-post-d316-characterized-no-promote.md).
  This checkpoint is written in the D-317 commit; a fresh session must confirm the live tip with
  `git rev-parse HEAD` and `git rev-parse origin/master`.
- **FBV2-P2-018 / D-316 (prior checkpoint — TWELFTH REST-OF-BOARD INCREMENT PROMOTED; a SINGLE west XGPIO net
  `XGPIO3` at the 0.200 mm Default clearance; the D-315 positive lead realised; ZERO router-logic change):** a
  governed CTO **ACCEPT + PROMOTE** — `XGPIO3` (R54.1 F.Cu → U3.7 B.Cu), the fifth XGPIO0..9 bank member, is
  routed at the **0.200 mm Default clearance** (NOT the 0.300 mm blanket the D-313/D-314 pilot PAIRS used) and
  promoted; no Phase-A / prior-increment casualty, no new DRC class, autonomy CONTINUES, **no owner decision.**
  Starting HEAD `9f108bb` (D-315; pushed; `origin/master` identical). **Promoted:** `sha256 95bc07be…` →
  **`d730c74d186ebcc7d2f0aa513776778ce1cb9c9659029a2fffd5e2261e3ac97d`**; tracks 669 → **691** (+22); vias 66 →
  **67** (+1); 6 layers / 41 zones; ratsnest 677 → **676** (−1); journal 104 → **105** (+1 REST_INC). **Why
  0.200 mm is correct (not rule weakening):** D-269's 0.300 mm governs clearance to `BAT_PROTECTED_P`; a single
  west haul clears BPP by ≥0.47 mm, so D-269 is satisfied **by geometry** (measured haul→BPP **0.4739 mm ≥
  0.300**) and the real full-board D-269-aware KiCad DRC (D-286 gate) arbitrates — reporting no new/worse class.
  The 0.300 mm blanket was over-conservative for west members (the D-315 Opportunity Scan flag), reserved now for
  paths that actually approach BPP (the D-313 east pilot). **WIP recovery (gitignored scratch, ZERO routing-logic
  change):** the preserved `w/screen_018.py` re-screen had stalled before persisting evidence — it imported
  `haul_bpp_min`/`BPP` from `w/xgpio23_pair200_017.py`, whose full XGPIO2+XGPIO3 PAIR routing driver runs at
  module level, so the import re-routed the D-315 wall every load (a cross-module recurrence of the D-314
  module-level-driver bug); fix = drop the import, inline the self-contained helper, screen only `/XGPIO3`. Live
  re-screen reproduced the D-315 record (via (55.300,77.700), exv 0.7038 mm, hole 1.0038 mm, haul→BPP 0.4739 mm).
  **INTEGRITY:** `route`→`gate`→`promote` on the real full-board (23 new in-scope items, only In1/In4 re-poured,
  0 regressed); `router_regression.py` ALL PASS **G1–G29** twice (deterministic; new **G29** pins connectivity +
  copper legality + via clearance + D-269 0.4739 mm + ADD-ONLY); new `incremental_probe_017.py` PASS;
  `_006..016` + `phaseB_bringup_probe_005` (691/67/105; **20 routed rest nets, 144 unrouted**) PASS;
  `live_fingerprint.py` bumped once. Real DRC `{solder_mask_bridge:1, hole_clearance:5, lib_footprint_issues:199,
  unconnected_items:499}` (clearance 0), independently confirmed by kicad-cli. **D-269/D-264/DRU board-swap A/B**
  (committed D-314 vs promoted D-316): `dru` FAIL(2) + `d264` FAIL B/C identical on both; `d269` flipped
  PASS/FAIL, but flips across repeated runs on the **byte-identical D-314 parent** too → intrinsic probe flake
  (synthetic injection + non-reproducible full-zone re-pour), not a regression (XGPIO3 ~45 mm from the TAPs it
  examines); D-316 board restored + sha re-verified after the swap. **Open owner decisions: NONE;**
  `JLCPCB_READINESS` unchanged (~77 %). Rollback: pre-promotion `sha256 95bc07be…` (committed D-314, parent
  `9f108bb`). **Next: FBV2-P2-019 — the next single west XGPIO member (one net at a time; do NOT force PAIRS), or
  the next clean local group; 144/164 rest nets unrouted.** Full analysis:
  [`audits/2026-08-31-p2-018-d316-twelfth-rest-of-board-incremental-increment-single-west-xgpio3-promoted.md`](audits/2026-08-31-p2-018-d316-twelfth-rest-of-board-incremental-increment-single-west-xgpio3-promoted.md).
  This checkpoint is written in the D-316 commit; a fresh session must confirm the live tip with
  `git rev-parse HEAD` and `git rev-parse origin/master`.
- **FBV2-P2-017 / D-315 (prior checkpoint — XGPIO2+XGPIO3 SOUTH-WEST PAIR = MEASURED CORRIDOR-CAPACITY WALL;
  NOT PROMOTED; ZERO authoritative copper change; board byte-identical to committed D-314):** a governed CTO
  **CHARACTERIZATION** — the named candidate, the XGPIO2+XGPIO3 adjacent pair (`XGPIO2` R53.1 F.Cu → U3.6 B.Cu
  + `XGPIO3` R54.1 F.Cu → U3.7 B.Cu, the next south-west west-edge pair north of the D-314 XGPIO0/1), does
  **NOT** promote; the authoritative PCB is **untouched** (`sha256 95bc07be30598df44e5096fd3c51729aa61cdbefd9c9855297e3737ea0b3a605`,
  669 trk / 66 via / ratsnest 677 / journal 104); autonomy CONTINUES, **no owner decision.** Starting HEAD
  `8de847b` (D-314; pushed; `origin/master` identical). D-314 predicted the "XGPIO-lower-first self-separates"
  recipe would carry this pair; the task required **revalidating that hypothesis on the live D-314 board** →
  **disproved for this pair.** **MEASURED EVIDENCE (all on gitignored scratch, authoritative untouched, one
  managed process at a time):** (1) BOTH route orders FAIL at the D-269 0.300 mm floor (`w/screen_016_one.py`):
  XGPIO2 **U3.6 NO LEGAL ESCAPE** — a flanked middle pin boxed by U3.7/U3.4 + 8 via obstacles (incl. the
  accepted XGPIO0/XGPIO1 barrels); XGPIO3 far-run R54.1→via blocked; order-independent (`qb.escape` tries all
  8 directions). (2) Per-clearance isolation (`w/xgpio23_clr_017.py`, each net ALONE): at **0.200 mm** each
  routes; at **0.300 mm** XGPIO2 fails escape (pad-limited), XGPIO3 fails NO_FAR_RUN (track-limited) — the
  0.300 mm blanket over-constrains the whole 116 mm haul to clear 0.300 from ALL copper. (3) The **one bounded
  evidence-backed alternative** — per-region `clr_pad=0.200`/`clr_trk=0.300` (correct-per-region: every
  BAT_PROTECTED_P pad is B.Cu ≥9 mm away, the only BPP copper near the F.Cu haul is its F.Cu trunk; **NOT** rule
  weakening) fixes the escape but both nets still **FAIL NO_FAR_RUN** — the D-313+D-314-congested corridor
  admits ONE 0.300 mm-clearance haul, not two. (4) PAIR @ 0.200 mm also fails (2nd net NO_FAR_RUN — two parallel
  hauls from adjacent R53/R54 contend for one corridor), but a **SINGLE** west XGPIO net at 0.200 mm routes
  CLEAN and keeps D-269 with margin: **XGPIO2 haul→BPP 0.6859 mm, XGPIO3 0.4739 mm (both ≥0.300)**. **INTEGRITY
  (board PRISTINE):** `sha256 95bc07be…` before/after; `router_regression.py` ALL PASS G1–G28 twice
  (deterministic); `incremental_probe_006..016` + `phaseB_bringup_probe_005` (669/66/104) all PASS; real DRC
  `{solder_mask_bridge:1, hole_clearance:5, lib_footprint_issues:199, unconnected_items:499}` (clearance 0);
  D-269/D-264/DRU board-swap trivially byte-identical (current board IS committed D-314 → no regression
  possible). **NO promote, NO rule/logic change; `via_offset` cannot help (relocates via after escape); a
  spatially-varying clearance is out-of-bounds and unnecessary.** **Opportunity & Simplification:** the 0.300 mm
  blanket XGPIO clearance is over-conservative for west members whose haul clears BPP by ≥0.47 mm — use 0.200 mm
  Default + real-gate D-269 arbitration; **do not force adjacent PAIRS** for the congested northern west members
  (route one net at a time); In2/In3 inner signal layers a deferred capacity option. **Open owner decisions:
  NONE;** `JLCPCB_READINESS` unchanged (~77 %). Rollback: none needed (no authoritative change). **Next:
  FBV2-P2-018 — route a SINGLE west XGPIO net (recommended `XGPIO3` via exv 0.704 mm; or `XGPIO2` BPP 0.686 mm)
  at `clr_pad=clr_trk=0.200` (NOT the 0.300 mm blanket), route→gate→promote under the D-286 real full-board gate
  (D-269-aware DRC arbitrates BPP), add `incremental_probe_017.py`+`G29`; do NOT re-attempt the XGPIO2+XGPIO3
  PAIR or `U11_PROG`/`PWR_SENSE`; 145/164 rest nets unrouted.** Full analysis:
  [`audits/2026-08-31-p2-017-d315-xgpio2-3-southwest-pair-corridor-capacity-wall-characterized-no-promote.md`](audits/2026-08-31-p2-017-d315-xgpio2-3-southwest-pair-corridor-capacity-wall-characterized-no-promote.md).
  This checkpoint is written in the D-315 commit; a fresh session must confirm the live tip with
  `git rev-parse HEAD` and `git rev-parse origin/master`.
- **FBV2-P2-016 / D-314 (prior checkpoint — ELEVENTH REST-OF-BOARD INCREMENT PROMOTED; the FIRST WEST XGPIO
  members, promoted after a governed recovery of the west-pair corridor screen, at the D-269 corridor
  clearance, zero router-logic change):** a governed CTO **ACCEPT + PROMOTE** — the XGPIO west-edge SOUTH pilot
  **`XGPIO1`** (R52.1 F.Cu → U3.5 B.Cu) + **`XGPIO0`** (R51.1 F.Cu → U3.4 B.Cu), the two SOUTHERNMOST members
  of the eight-net **west** XGPIO group the D-313 study had deferred as an ordering-sensitive shared-via-pocket
  hazard, are on the authoritative board with **no Phase-A / prior-increment casualty and no new DRC**; autonomy
  CONTINUES, **no owner decision.** Starting HEAD `0faf85b` (D-313; pushed; `origin/master` identical). **RECOVERY
  (gitignored scratch only, ZERO routing-logic change):** the one-order runner `w/screen_016_one.py` imported the
  ranker `w/screen_016.py`, whose full 14-pair driver ran at **module level** — every import re-ran the whole
  screen and died before the single pair's ledger write (empty ledger, byte-identical SCR16_* AUTH-copy dirs, no
  durable evidence); fix = guard the driver behind `if __name__ == '__main__':`. **MEASURED EVIDENCE** (live D-313
  board, D-269 0.300 mm, no via_offset; only missing/high-value southern orders re-run, one managed foreground
  process at a time): both priority pairs CONCLUSIVE — each has exactly ONE clean order = **XGPIO1-first**:
  `XGPIO0/1` (`1_0_0`) CLEAN via-via **2.129 mm** / BPP 2.038 / exv 3.607; `XGPIO1/2` (`1_2_1`) CLEAN via-via 2.044
  / BPP 2.006; the reverse orders B-FAIL (the southern net routed first boxes XGPIO1 out). XGPIO1 routes first (via
  lands in the shared pocket at (55.40,79.00)); the southern net sees that laid via as a real `qb.via()` obstacle
  and self-separates WEST off it (XGPIO0 → (52.75,78.35)) — unlike the NORTHERN pins (XGPIO6/7 collide onto the
  identical cell). **SELECTION:** `XGPIO0`+`XGPIO1`, XGPIO1-first (minimum coherent clean west pair; best margins;
  southernmost/most-independent). New `GROUPS` entry `XGPIO_PILOT_W` (`nets=['XGPIO1','XGPIO0']`,
  `clr_pad=clr_trk=300000`, no via_offset); `incremental_router.py`/`qrouter.py` routing logic UNCHANGED. **GATE**
  (real full-board, D-286): `route` ALL OK (XGPIO1 via@(55.400,79.000), XGPIO0 via@(52.750,78.350); 38 seg + 2
  vias; AUTH sha unchanged during route); `gate` PASS every check (0 Phase-A altered, 40 new items all target-net,
  only In1/In4 re-poured, both nets fully connected, 0 prior pairs regressed, ratsnest 679→677 −2, no new DRC).
  **Promoted:** `sha256 a0d6fead…` → **`95bc07be30598df44e5096fd3c51729aa61cdbefd9c9855297e3737ea0b3a605`**;
  tracks 631→**669** (+38); vias 64→**66** (+2 through vias); 6 layers / 41 zones; ratsnest 679→**677** (−2);
  journal 102→**104** (+2 REST_INC); PCB diff **404 ins / 36 del** — 40 `(segment)`/`(via)` added (0 seg/via/fp
  del), all 36 dels In1/In4 re-pour; real KiCad DRC error-severity identical (`solder_mask_bridge:1 +
  hole_clearance:5 + lib_footprint_issues:199 + unconnected_items:499`; 0 `clearance`). **Tests:** new **G28**
  (both nets connected across the U3 F/B hop; copper legal 38 trk + 2× 0.60/0.30 vias; both vias ≥0.80 mm from
  every barrel, min **4.207 mm**; **D-269 0.300 mm BAT_PROTECTED_P clearance kept, F.Cu edge gap 2.2382 mm**;
  ADD-ONLY); G18–G27 auto-generalise → `router_regression.py` **ALL PASS (G1–G28)**, deterministic (run twice);
  new `incremental_probe_016.py` PASS; `_006..015` + `phaseB_bringup_probe_005` (669/66/104; 19 routed rest nets,
  145 unrouted) PASS; `live_fingerprint.py` bumped once; real-board `kicad-cli` DRC + pcbnew ratsnest 677 re-run
  independently — no new `clearance`; `d269`/`dru` board-swap A/B **BYTE-IDENTICAL** on committed D-313 vs promoted
  D-314; `d264` differed on a borderline U18 sense item (`R75.2→U18.8`) far from the XGPIO copper — **proven
  intrinsic non-determinism** (re-run on the identical D-314 board flipped 2→1→3 fails), NOT a regression.
  **Opportunity & Simplification:** the SOUTH of the west group is now open with the same zero-mechanism recipe
  (route at the D-269 floor, XGPIO-lower-first so the southern neighbour self-separates west); the characterised
  crowding is specifically the NORTHERN pins; In2/In3 remain fully available; recovery-runner hardening
  (`__main__` guard + durable ledger) is a reusable lever. **Open owner decisions: NONE;** `JLCPCB_READINESS`
  unchanged (~77 %). Rollback: pre-promotion `sha256 a0d6fead…` (D-313; parent `0faf85b`). Next: **FBV2-P2-017 —
  the next XGPIO south-west pilot (`XGPIO2/3`, screened live with the XGPIO-lower-first recipe), or the next clean
  local group; 145 of 164 rest nets unrouted; `U11_PROG`/`PWR_SENSE` remain characterised walls.** Full analysis:
  [`audits/2026-08-30-p2-016-d314-eleventh-rest-of-board-incremental-increment-xgpio-west-south-pilot-promoted.md`](audits/2026-08-30-p2-016-d314-eleventh-rest-of-board-incremental-increment-xgpio-west-south-pilot-promoted.md).
  This checkpoint is written in the D-314 commit; a fresh session must confirm the live tip with
  `git rev-parse HEAD` and `git rev-parse origin/master`.
- **FBV2-P2-015 / D-313 (TENTH REST-OF-BOARD INCREMENT PROMOTED; the FIRST XGPIO0..9 bank
  members, promoted after a full evidence-first READ-ONLY corridor study, at the D-269 corridor clearance):** a
  governed CTO **ACCEPT + PROMOTE** — the XGPIO east-edge pilot **`XGPIO8`** (R59.1 F.Cu → U3.13 B.Cu) +
  **`XGPIO9`** (R60.1 F.Cu → U3.14 B.Cu), two adjacent community-header GPIO nets on consecutive PCAL9535A U3
  pins, are on the authoritative board with **no Phase-A / prior-increment casualty and no new DRC**; autonomy
  CONTINUES, **no owner decision.** Starting HEAD `1eb80a9` (D-312; pushed; `origin/master` identical). Each
  `/XGPIOx` is a 2-pad cross-layer net: the 100 R community-header series resistor R5x.1 (F.Cu top pack, y≈17–36)
  → the U3 expander pin (B.Cu mid-board, y≈74–80); one MST edge, one F↔B through via. **EVIDENCE-FIRST STUDY**
  (`w/xgpio_study_015.py`, READ-ONLY, all ten nets): **all ten escape U3 cleanly** — NOT a pad-escape wall like
  the D-309 U2 family; the escape goes NORTH into open board (away from the completed U2 via cluster at y≈82–92),
  every default via site ≥3.1 mm clear of every existing barrel, ZERO existing vias in any XGPIO bbox → **no
  `via_offset` needed**; **shared-corridor / ordering sensitivity is real** — the 8 west-edge nets funnel their via
  into ONE small pocket north of U3 (independent offset sites collide; XGPIO6/7 pick the IDENTICAL cell) whereas
  the **east pair XGPIO8+XGPIO9 separates cleanly (2.7 mm)** = an independent legal corridor; the corridor crosses
  NO mechanical/RF/USB reservation; netclass Default (0.200/0.200, normal via, In1.Cu forbidden). **THE REAL WALL
  + CORRECT FIX:** at the default 0.200 mm the candidates routed geometrically but FAILED the real gate with new
  `clearance` — root cause across all four is the **D-269 BAT_MAIN routed-clearance rule (0.300 mm)** to the
  52.4 mm×1.30 mm `BAT_PROTECTED_P` protected-battery F.Cu trunk that sweeps diagonally across the exact y≈73–82
  XGPIO via band (copper landed 0.244–0.281 mm from it). Fix = route the group at the **0.300 mm D-269 clearance
  floor** — the correct clearance, NOT a new mechanism (only the group `clr_pad`/`clr_trk` parameter; no
  `incremental_router.py`/`qrouter.py` logic change); all six screened candidates (4–9) then pass individually.
  **Route/gate/promote (member-by-member then combined):** each member gated PASS individually; `route XGPIO_PILOT`
  ALL OK (XGPIO8 via@(58.60,72.95), XGPIO9 via@(58.45,75.65) — XGPIO9 re-routed around XGPIO8's laid via); `gate`
  PASS every check (ratsnest 681→679 EXACTLY −2, only In1/In4 re-poured, 0 prior pairs regressed, no new DRC).
  **Promoted:** `sha256 d6e0148a…` → **`a0d6fead125295441dda0f0008c1261f5c1cec39edb2b8c7bd925b214e7207eb`**;
  tracks 608→**631** (+23); vias 62→**64** (+2 through vias); 6 layers / 41 zones; ratsnest 681→**679** (−2);
  journal 100→**102** (+2 REST_INC); PCB diff **316 ins / 66 del** — 23 `(segment)` + 2 `(via)` added (0 seg/via/fp
  del), all xy dels In1/In4 re-pour; real KiCad DRC error-severity identical (`solder_mask_bridge:1 +
  hole_clearance:5 + lib_footprint_issues:199 + unconnected_items:499`; 0 `clearance`). **Tests:** new **G27**
  (both nets connected across the U3 F/B hop; copper legal 23 trk + 2× 0.60/0.30 vias; both vias ≥0.80 mm from
  every barrel, min 4.700 mm; **D-269 0.300 mm BAT_PROTECTED_P clearance kept, measured 0.3516 mm**; ADD-ONLY);
  G18–G26 auto-generalise → `router_regression.py` **ALL PASS (G1–G27)**, deterministic; new `w/xgpio_study_015.py`
  + `incremental_probe_015.py` PASS; `_006..014` + `phaseB_bringup_probe_005` (631/64/102; 17 routed rest nets, 147
  unrouted) PASS; `live_fingerprint.py` bumped once; real-board `kicad-cli` DRC + pcbnew ratsnest 679 re-run
  independently — no new `clearance`; `d269`/`d264`/`dru` board-swap A/B **BYTE-IDENTICAL** on committed D-312 vs
  promoted D-313 (not regressed). **Opportunity & Simplification:** staged small-adjacent-pilot routing is safer
  than a blind ten-via bank (members coupled — west nets contend for one via pocket, the whole bank shares the
  D-269 corridor); the east pair is the naturally-independent island. **In2/In3 remain fully available** (routed on
  F/B outer layers only — inner-signal capacity deliberately preserved for the denser west members). **Open owner
  decisions: NONE;** `JLCPCB_READINESS` unchanged (~77 %). Rollback: pre-promotion `sha256 d6e0148a…` (D-312;
  parent `1eb80a9`). Next: **FBV2-P2-016 — the next XGPIO adjacent pilot (west-edge members, staggering the
  north-of-U3 via pocket), or the next clean local group; 147 of 164 rest nets unrouted; `U11_PROG`/`PWR_SENSE`
  remain characterised walls.** Full analysis:
  [`audits/2026-08-30-p2-015-d313-tenth-rest-of-board-incremental-increment-xgpio-east-pilot-promoted.md`](audits/2026-08-30-p2-015-d313-tenth-rest-of-board-incremental-increment-xgpio-east-pilot-promoted.md).
  This checkpoint is written in the D-313 commit; a fresh session must confirm the live tip with
  `git rev-parse HEAD` and `git rev-parse origin/master`.
- **FBV2-P2-013 / D-311 (EIGHTH REST-OF-BOARD INCREMENT PROMOTED; the hardest D-309 U2 escape
  sibling completed with the D-310 bounded via-site offset, zero per-net tuning):** a governed CTO **ACCEPT +
  PROMOTE** — the audio-amp SD/mode-select strap **`AMP_SD_MODE`** (MAX98357 static logic strap, R15.1/U5.4 F.Cu
  → U2.7 B.Cu; **NOT** the class-D output) is on the authoritative board with **no Phase-A / FRONT_RGB / ACC /
  DISP / IMU / FRONT_RGB_LED / IR_RX_VS / TOUCH casualty and no new DRC**; autonomy CONTINUES, **no owner
  decision.** Starting HEAD `67d3ff6` (D-310; pushed; `origin/master` identical). `AMP_SD_MODE` was one of the
  two remaining U2 west-edge escape siblings the D-310 via-offset unlocked, and the **hardest D-309 wall**
  (via-blind default via 0.100 mm from the accepted D-306 `DISP_RST_N` barrel; D-309 +7). **No new routing
  mechanics** — the only `incremental_router.py` change is `via_offset=2500000` on the pre-existing
  `AMP_SD_MODE`/`SD_DETECT` GROUPS entries (+ annotations); the D-310 always-on existing-via injection
  (`qrouter.py` untouched) + opt-in bounded offset applied with **zero per-net tuning**. **Re-screen on the LIVE
  D-310 board was essential** (`w/screen_013.py`): the two new D-310 TOUCH vias shifted the geometry —
  `AMP_SD_MODE` DEFAULT via 0.100 mm from `DISP_RST_N` (CLASH), 2.5 mm offset → (51.55,90.20) 1.760 mm clear
  (nearest now `TOUCH_RST_N`), 3.5 mm collapses onto the fresh TOUCH via (0.206 mm) → **2.5 mm correct, not
  more**. **Each sibling tested separately on scratch** (`route`+`gate` both PASS independently; functionally
  distinct → NOT bundled); `AMP_SD_MODE` promoted as the single D-311 increment, `SD_CARD_DETECT_N` held for
  FBV2-P2-014. **Promoted:** `sha256 856f7a8a…` → **`9bf429cec07654d4522121d2fb595204d06f5173ae629f2292c4d0cb9f68b314`**;
  tracks 561→**580** (+19: 18 F.Cu + 1 B.Cu fan-out); vias 60→**61** (+1 offset through via); 6 layers / 41
  zones; ratsnest 685→**683** (−2); journal 96→**98** (+2 REST_INC); PCB diff **236 ins / 48 del** — 19
  `(segment)` + 1 `(via)` added (0 seg/via/fp del), all 48 dels In1/In4 `(xy …)` anti-pad lines; real KiCad DRC
  error-severity identical (`solder_mask_bridge:1 + hole_clearance:5`; 0 `clearance`). **Tests:** new **G25**;
  G18–G24 auto-generalise → `router_regression.py` **ALL PASS (G1–G25)**, deterministic; new
  `incremental_probe_013.py` PASS; `_006..012` + `phaseB_bringup_probe_005` (580/61/98; 14 routed rest nets, 150
  unrouted) PASS; `live_fingerprint.py` bumped once; real-board `kicad-cli` DRC + pcbnew ratsnest 683 re-run
  independently — no new `clearance`; `d269`/`d264`/`dru` board-swap A/B **BYTE-IDENTICAL** on committed D-310 vs
  promoted D-311 (not regressed). **Opportunity & Simplification:** reusable mechanism, individually gated — both
  siblings closed with zero per-net tuning (the offset is a genuine reusable primitive) but the long hauls
  (58/80 mm) touch different regions and the via geometry is sensitive to earlier increments' copper (the 3.5 mm
  AMP site collapsed onto the fresh D-310 TOUCH via) → each U2-family net must still be screened live + gated on
  the full board; **do NOT auto-bundle**. **Open owner decisions: NONE;** `JLCPCB_READINESS` unchanged (~77 %).
  Rollback: pre-promotion `sha256 856f7a8a…` (D-310; parent `67d3ff6`). Next: **FBV2-P2-014 — the second U2
  sibling `SD_CARD_DETECT_N` (U2.11, `via_offset=2.5 mm` set, proven clean on scratch — re-screen/route/gate on
  the D-311 board), or another clean local group; 150 of 164 rest nets unrouted; `U11_PROG`/`PWR_SENSE` remain
  characterised walls.** Full analysis:
  [`audits/2026-08-30-p2-013-d311-eighth-rest-of-board-incremental-increment-amp-sd-mode-u2-escape-via-offset-promoted.md`](audits/2026-08-30-p2-013-d311-eighth-rest-of-board-incremental-increment-amp-sd-mode-u2-escape-via-offset-promoted.md).
  This checkpoint is written in the D-311 commit; a fresh session must confirm the live tip with
  `git rev-parse HEAD` and `git rev-parse origin/master`.
- **FBV2-P2-012 / D-310 (SEVENTH REST-OF-BOARD INCREMENT PROMOTED; the D-309 U2 B.Cu ESCAPE
  WALL BROKEN by a bounded via-site offset + existing-via awareness):** a governed CTO **ACCEPT + PROMOTE** — the
  display/touch control pair `TOUCH_RST_N` + `TOUCH_INT_N` (capacitive-touch reset + interrupt, display FPC J1 →
  touch-controller U2), **the group D-309 measured as a WALL**, is on the authoritative board with **no Phase-A /
  FRONT_RGB / ACC / DISP / IMU / FRONT_RGB_LED / IR_RX_VS casualty and no new DRC**; autonomy CONTINUES, **no
  owner decision.** Starting HEAD `f2bcac1` (D-309; pushed; `origin/master` identical). **(1) Root cause of the
  D-309 wall — the router was BLIND to existing vias.** `qrouter.QBoard._scan` builds obstacles from footprint
  pads + `PCB_TRACK` but iterates `GetTracks()` and `continue`s on `PCB_VIA`, so every accepted through-via is
  invisible to escape/via_site/connect_role. U2.4/.7/.8/.11 stack on U2's WEST edge (x=54.14); the accepted D-306
  `DISP_RST_N` via sits at (52.95,87.0), 1.19 mm west of that column, so a westward cross-layer escape lands the
  new via (and threads its F.Cu run) right past the barrel; only real DRC caught it (D-309 +3; measured this
  cycle `AMP_SD_MODE` default via 0.100 mm copper to `DISP_RST_N`). **(2) The fix — two generic, bounded,
  `qrouter.py`-UNTOUCHED mechanisms in `connect_cross`.** (a) EXISTING-VIA AWARENESS — every accepted `PCB_VIA`
  barrel/hole is injected as an obstacle onto the per-route `QBoard` instance (mirroring `QBoard.via()`
  item-for-item), so escape/via_site/**connect_role's track search** respect accepted vias (add-only, per-route,
  generic; touches only the transient route QBoard so G-contract fixtures are unaffected); (b) BOUNDED VIA-SITE
  OFFSET — a group opts in with `via_offset` and the F↔B transition is deliberately walked ~2.5 mm off the
  nearest congesting barrel via `_offset_via_site` (a short host-face B.Cu fan-out) — the first increment that
  PLANS a via site; groups without `via_offset` are byte-identical to D-306/D-308. **(3) Screen (real-geometry
  clearance, READ-ONLY `w/geom_012.py` + `w/screen_012.py`, before any gate):** `AMP_SD_MODE` default via 0.70 mm
  from DISP = 0.100 mm CLASH (confirms D-309 +7); `TOUCH_RST_N`/`SD_DETECT` default vias clear the barrel but
  their tracks thread the west column (D-309 +3/+2); at 2.5 mm offset all four clear (via↔via 2.6–7.8 mm);
  `TOUCH_INT_N` on U2's EAST edge already 5.9 mm clear. Per the task preference the coherent display/touch PAIR
  was taken (both pass); unrelated nets NOT bundled. **(4) The gate (real full-board, D-286):** `route TOUCH_CTL`
  ALL OK (injected 58 existing-via obstacles): J1.47↔R12.1 22.217 mm F.Cu + R12.1↔U2.4 28.553 mm cross-via@(52.95,
  92.10); J1.46↔U2.19 54.708 mm cross-via@(61.15,88.85); 26 seg + 2 through vias; In1/In4 re-poured. (First
  attempt with via-offset ALONE still failed +3 — the via-blind track router threaded the F.Cu run 0.05 mm from
  the DISP barrel; the existing-via injection made connect_role via-aware and the re-route was clean — the offset
  fixes the via, the injection fixes the tracks.) `gate` = PASS every check: prior copper 0 missing (D-309 535
  trk + 58 via a SUBSET); 28 new items all target-net; only zones 39/40 re-poured, all other 39 byte-identical;
  both nets connected open-edges 2→0 and 1→0; 0 prior pairs regressed; **ratsnest 688→685 EXACTLY −3**; real DRC
  no new/worse class (`clearance` 0→0). **GATE PASS.** **(5) Promoted:** `sha256 5c5cae79…a339f63` →
  **`856f7a8adf0db9b114b9f09d7469308f921bc897aaf2ddce7f1c15c40a197114`**; tracks **535→561** (+26: 21 F.Cu + 5
  B.Cu fan-out); vias **58→60** (+2 offset through vias); 6 layers / 41 zones; ratsnest **688→685** (−3); journal
  **93→96** (+3 `REST_INC`); PCB file diff **310 ins / 40 del** — additions 26 `(segment)` + 2 `(via)` (0
  seg/via/fp del), all 40 del are In1/In4 `filled_polygon` xy (2 via anti-pads); real KiCad DRC error-severity
  identical (`solder_mask_bridge:1 + hole_clearance:5`; 0 `clearance`). **(6) Tests:** new contract **G24** (both
  nets connected across the U2 F/B hop; copper legal 26 trk 0.200 mm F.Cu+B.Cu + 2×0.60/0.30 through vias; the
  offset cleared both vias of every existing via — min TOUCH-via↔other-via **4.998 mm** ≥0.80 mm; ADD-ONLY
  IR_RX_VS 8 + RGB_LED 25 + IMU 8 + DISP 11 + ACC 31 + RGB 20 + Phase-A 432/54); G18–G23 auto-generalise →
  `router_regression.py` **ALL CHECKS PASS (G1–G24), 102 PASS lines**, deterministic; new probe
  `checks/incremental_probe_012.py` PASS; `_006..011` PASS unchanged (pre-X checks auto-generalise);
  `phaseB_bringup_probe_005` updated (561/60/96; 13 routed rest nets, 151 unrouted) PASS; real-board `kicad-cli`
  DRC + pcbnew ratsnest 685 re-run independently — no new `clearance`. `d269`/`d264`/`dru` NOT regressed — a
  **board-swap A/B test proves BYTE-IDENTICAL verdicts (`diff` empty) on the committed D-309 and promoted D-310
  boards** (pre-existing BAT_*/LTC power-tree reds far from the mid-board TOUCH copper). **(7) Opportunity &
  Simplification:** the via-site metadata is deliberately REUSABLE without hiding corridor coupling — the
  existing-via injection is unconditional (fixes a latent gap for EVERY future cross-layer increment) and
  re-proven by the defensive `_clears_existing_vias` guard for all groups; `via_offset` is an opt-in bounded
  scalar biasing "away from the nearest existing via" (a general rule), now available to the rest of the U2
  family; sibling U2 groups `AMP_SD_MODE`/`SD_DETECT` NOT bundled (task preference; annotated with clean measured
  2.5 mm sites). **Open owner decisions: NONE;** `JLCPCB_READINESS` unchanged (~77 %). Rollback: pre-promotion
  `sha256 5c5cae79…a339f63` (D-309; parent `f2bcac1`). Next: **FBV2-P2-013 — the U2 escape family is UNLOCKED:
  complete it (`AMP_SD_MODE` U2.7, `SD_CARD_DETECT_N` U2.11 both measured clean at 2.5 mm offset — add
  `via_offset` and route/gate), or another clean local group; 151 of 164 rest nets unrouted; `U11_PROG`/
  `PWR_SENSE` remain characterised walls.** Full analysis:
  [`audits/2026-08-30-p2-012-d310-seventh-rest-of-board-incremental-increment-touch-ctl-u2-escape-via-offset-promoted.md`](audits/2026-08-30-p2-012-d310-seventh-rest-of-board-incremental-increment-touch-ctl-u2-escape-via-offset-promoted.md).
  This checkpoint is written in the D-310 commit; a fresh session must confirm the live tip with
  `git rev-parse HEAD` and `git rev-parse origin/master`.
- **FBV2-P2-011 / D-309 (SIXTH REST-OF-BOARD INCREMENT PROMOTED; cleanest class, NO via;
  display/touch U2-escape wall characterised; shared live-fingerprint helper landed):** a governed CTO
  **ACCEPT + PROMOTE** — the IR receiver (U6) local filtered supply `IR_RX_VS_LOCAL` (series filter R21.2 +
  decoupling C11.1 → U6.3 THT supply pin, all same-layer F.Cu, **NO via**) is on the authoritative board, with
  **no Phase-A / FRONT_RGB / ACC / DISP / IMU / FRONT_RGB_LED casualty and no new DRC**; autonomy CONTINUES,
  **no owner decision.** Starting HEAD `49528f2` (D-308; pushed; `origin/master` identical). **(1) Same
  `incremental_router.py`, ZERO new routing mechanics** — the proven same-layer no-via class (like D-307 but on
  F.Cu); `connect_cross`/`refill_planes`/`qrouter.py` untouched. **(2) Candidate selection — EARNED on gate
  evidence, not defaulted.** FOUR groups routed on scratch + put through the REAL full-board gate: the
  task-preferred **display/touch group** `TOUCH_CTL` (`TOUCH_RST_N`+`TOUCH_INT_N`) and `AMP_SD_MODE`,
  `SD_DETECT` (`SD_CARD_DETECT_N`) each routed ALL OK on the scratch router but **FAILED the real gate with NEW
  `clearance` (+3 / +7 / +2)** — long cross-board hauls (33–68 mm) whose cross-layer via lands in the
  **congested U2 B.Cu escape beside the accepted D-306 `DISP_RST_N` via** (U2.4/.7/.11/.19 sit beside U2.8): a
  CHARACTERISED WALL, deferred to FBV2-P2-012 with a deliberate U2-escape corridor plan (failing `GROUPS`
  entries annotated). The 'favor display/touch IF clean' preference was honored — tried first, empirically shown
  NOT clean. CHOSE **`IR_RX_VS`** — pristine (cu 0), local NE-corner cluster, same-layer F.Cu, no via.
  **(3) The gate (real full-board, D-286):** `route IR_RX_VS` → ALL OK (C11.1↔R21.2 3.113 mm + R21.2↔U6.3
  9.291 mm; 8 F.Cu segments 0.200 mm, no via); prior copper deleted/altered = 0 (D-308 527 trk + 58 via multiset
  a SUBSET); 8 new items all target-net; **ALL 41 zones byte-identical** (no via ⇒ no plane re-pour);
  `IR_RX_VS_LOCAL` fully connected (open-edges 2→0); 0 prior pairs regressed; pcbnew **ratsnest 690→688** (−2);
  real kicad-cli DRC no new/worse class. **GATE PASS.** **(4) Promoted:** authoritative
  `sha256 f4e95dec…8559e7ee` → **`5c5cae79465416c81f9d7b8dba5b2e3a3325bd9a0680b65103badf0e1a339f63`**; tracks
  **527→535** (+8); vias **58** (no via); 6 layers / 41 zones; ratsnest **690→688** (−2); journal **91→93** (+2
  `REST_INC`); PCB file diff **64 ins / 0 del** — all 8 additions `(segment)` F.Cu (0 seg/via/fp del, 0 zone
  change; cleanest class, tied D-307); real KiCad DRC **identical**
  (`{solder_mask_bridge:1, hole_clearance:5, lib_footprint_issues:199, unconnected_items:499}`).
  **(5) Tests:** new contract **G23** (G18–G22 stay green unchanged — ADD-ONLY auto-generalises) →
  `router_regression.py` **ALL CHECKS PASS (G1–G23), 98 PASS lines**, deterministic; new probe
  `checks/incremental_probe_011.py` PASS; `_006/_007/_008/_009/_010` + `phaseB_bringup_probe_005` refreshed to
  the D-309 board (535/58/93; 11 routed rest nets, 153 unrouted) PASS; real-board `kicad-cli` DRC + pcbnew
  ratsnest 688 re-run independently — no new `clearance`. The Phase-A DRU-synthesis probes `d269`/`d264`/`dru`
  are NOT part of the maintained regression and NOT regressed — a **board-swap A/B test proves BYTE-IDENTICAL
  verdicts on the committed D-308 and promoted D-309 boards** (pre-existing BAT_*/LTC power-tree reds ~60 mm
  from my copper; the flaky `d269` full-zone-re-pour proxy was NOT mistaken for authoritative DRC).
  **(6) Opportunity & Simplification (ACTED-ON — the exact one D-308 §E pre-flagged):** introduced
  **`checks/live_fingerprint.py`**, a single source-of-truth `EXPECTED` dict (sha/tracks/vias/layers/zones/
  ratsnest/journal) bumped ONCE per promotion; all six probes refactored to import it, replacing the ~25
  identical per-increment `EXPECT_*` hand-edits — a pure DRY consolidation weakening NO historical contract
  (each probe still asserts live-board == EXPECTED and keeps its own structural checks), all six PASS.
  **Open owner decisions: NONE;** `JLCPCB_READINESS` unchanged (~77 %). Rollback: pre-promotion
  `sha256 f4e95dec…8559e7ee` (D-308; parent `49528f2`). Next: **FBV2-P2-012 — the U2 B.Cu escape corridor
  (plan a via SITE off U2's edge to clear the `DISP_RST_N` barrel, unlocking the display/touch/SD/audio-strap
  family), or another clean local no-via/single-via group; `U11_PROG`/`PWR_SENSE` + the four U2-escape
  candidates remain characterised walls — do NOT re-attempt naively.** Full analysis:
  [`audits/2026-08-30-p2-011-d309-sixth-rest-of-board-incremental-increment-ir-rx-vs-promoted.md`](audits/2026-08-30-p2-011-d309-sixth-rest-of-board-incremental-increment-ir-rx-vs-promoted.md).
- **FBV2-P2-010 / D-308 (FIFTH REST-OF-BOARD INCREMENT PROMOTED; the FIRST MULTI-VIA
  increment):** a governed CTO **ACCEPT + PROMOTE** — the front-panel RGB status-indicator completion (three
  LED-cathode nets `Net-(D13-RK)`/`Net-(D13-GK)`/`Net-(D13-BK)`) is on the authoritative board, closing the
  D-304 `FRONT_RGB` indicator on the LED side, with **no Phase-A / FRONT_RGB / ACC / DISP / IMU casualty and no
  new DRC**; autonomy CONTINUES, **no owner decision.** Starting HEAD `c939f35` (D-307; pushed; `origin/master`
  identical). **(1) Same `incremental_router.py`, ZERO new mechanics** — the FIRST multi-via increment needed NO
  change to `connect_cross`/`refill_planes`/`qrouter.py`: the existing per-edge loop lays one 0.60/0.30 Default
  through via per cross-layer edge (three times) and `refill_planes` re-pours In1/In4 once for all vias; a
  multi-net group of independent single-via nets is already within the D-306-proven mechanic. **(2) Group
  selection (measured; coherent + local + clean — baseline `a309f8ce…` 502/55/6, ratsnest 693, journal 88; new
  READ-ONLY screen `w/screen_010.py` ranking ALL 156 remaining unrouted multi-pad nets by pad layers / THT / MST
  / bbox-span / congestion).** CHOSE **FRONT_RGB_LED** (`Net-(D13-RK/GK/BK)`, R124.2/R125.2/R126.2 B.Cu → D13
  MHPA3528 cathodes F.Cu) — the coherent completion of the D-304 indicator, local (span ≤26 mm), clean (cu
  6–11), low-current non-switching; three independent single-via cross-layer nets. Excluded with evidence:
  XGPIO0…9 bank (~55 mm cross-board hauls — not local), NFC/RF/USB/crystals, ACC_5V boost (switching), IR-LED
  drive (Q1-switched), SPK class-D, community J5/J8 headers, scattered BTN_x_N buttons, U11_PROG + PWR_SENSE
  (D-307 hard walls). A coherent 3-net group preferred to a safe singleton to show throughput beyond
  singletons/2-net clusters WITHOUT bundling unrelated nets. **(3) The gate (real full-board, D-286):** `route
  FRONT_RGB_LED` → ALL OK (25 segments F.Cu+B.Cu 0.200 mm + 3 through vias 0.60/0.30; In1/In4 zones [39,40]
  re-poured once); prior copper deleted/altered = 0 (D-307 502 trk + 55 via multiset a SUBSET); 28 new items all
  target-net; ONLY zones 39/40 fill-changed, all other 39 zones byte-identical; all three D13 nets fully
  connected (open-edges 1→0 each); 0 prior pairs regressed; pcbnew **ratsnest 693→690** (−3); real kicad-cli DRC
  no new/worse class. **GATE PASS.** **(4) Promoted:** authoritative `sha256 a309f8ce…31279a50` →
  **`f4e95decb5be87f6e758f76803e57be68a4437afaef75973518983008559e7ee`**; tracks **502→527** (+25 D13-cathode);
  vias **55→58** (+3 through vias); 6 layers / 41 zones unchanged; ratsnest **693→690** (−3); journal **88→91**
  (+3 `REST_INC`); PCB file diff **352 ins / 59 del** — additions are 25 `segment` + 3 `via` lines (zero
  segment/via/footprint deletions, grep-confirmed); all 59 deletions are In1/In4 GND `filled_polygon` xy (the 3
  via anti-pads); real KiCad DRC **identical** (`{solder_mask_bridge:1, hole_clearance:5, lib_footprint_issues:199,
  unconnected_items:499}` — 0 clearance, hole_clearance unchanged at 5, 0 violations touch the D13 copper).
  **(5) Tests:** new contract **G22** (G18–G21 stay green unchanged — ADD-ONLY invariants exclude all `REST_INC`
  nets and pin `phaseA_via`==54, auto-generalising as total vias grow 55→58) → `router_regression.py` **ALL
  CHECKS PASS (G1–G22), 94 PASS lines**, deterministic; new probe `checks/incremental_probe_010.py` ALL PASS;
  `checks/incremental_probe_006/007/008/009.py` refreshed to the D-308 board (`_009` pre-IMU-copper check
  generalised) ALL PASS; `checks/phaseB_bringup_probe_005.py` updated (527/58/91; 10 routed rest nets, 154
  unrouted) ALL PASS. The Phase-A DRU-synthesis probes `d269`/`d264`/`dru_probe` are NOT part of the maintained
  increment regression and NOT regressed by D-308 (`dru_probe`(2)/`d264`(1) carry the SAME pre-existing reds on
  pristine HEAD; `d269` C/D is a flaky borderline between two REMOTE Phase-A items under KiCad's
  non-byte-reproducible full-zone re-pour — it flips on HEAD too; the byte-stable authoritative board is
  DRC-clean). **Open owner decisions: NONE;** `JLCPCB_READINESS` unchanged (~77 %). Rollback: pre-promotion
  `sha256 a309f8ce…31279a50` (D-307; parent `c939f35`). Next: **FBV2-P2-011 — continue rest-of-board routing
  (next bounded group, same framework); the two congested regions (BQ25185/BPP trunk, west BAT trunk) remain
  characterised hard walls — do NOT re-attempt naively.** Full analysis:
  [`audits/2026-08-30-p2-010-d308-fifth-rest-of-board-incremental-increment-front-rgb-led-promoted.md`](audits/2026-08-30-p2-010-d308-fifth-rest-of-board-incremental-increment-front-rgb-led-promoted.md).
  This checkpoint is written in the D-308 commit; a fresh session must confirm the live tip with
  `git rev-parse HEAD` and `git rev-parse origin/master`.
- **FBV2-P2-009 / D-307 (FOURTH REST-OF-BOARD INCREMENT PROMOTED; the promoted fallback was
  EARNED, not defaulted to):** a governed CTO **ACCEPT + PROMOTE** — a fourth rest-of-board net (the BMI270 IMU
  I2C address-select strap `BMI270_SDO_ADDR`) is on the authoritative board, with **no Phase-A / FRONT_RGB / ACC /
  DISP casualty and no new DRC**; autonomy CONTINUES, **no owner decision.** Starting HEAD `73ea58e` (D-306;
  pushed; `origin/master` identical). **(1) Same `incremental_router.py`, ZERO new mechanics** — a same-layer
  B.Cu multi-terminal net routed through the existing Prim-MST + `connect_role` path; the D-306
  via/`connect_cross`/`refill_planes` machinery reused byte-for-byte correctly did NOT engage (no via ⇒ no plane
  re-pour ⇒ all 41 zones byte-identical). **(2) Group selection (measured; highest-value low-risk, not merely the
  shortest net — baseline `9c0586d8…` 494/55/6, ratsnest 695, journal 86; refined READ-ONLY screen
  `w/screen_009.py` reporting MST/layer/THT, group bbox, accepted-copper congestion within bbox+1/+2 mm and a
  footprint-local coherence dump; all candidate nets confirmed Default netclass from the board).** Five candidates
  recorded. CHOSE PRIMARY **U11_PROG** (`ILIM_VSET`+`ISET`, coherent same-chip BQ25185 charger current-program
  straps) — a clean singleton is NOT bundled with unrelated nets to hit a count, and the favored IMU/I2C family
  has no clean local *pair* (the only other U4 net `BMI270_INT1_RAW` is a ~46 mm haul to the MCU). Fallbacks:
  **PWR_SENSE** (`VBUS_PRESENT`+`MAX17048_ALRT_N`), then pristine **IMU_ADDR** (`BMI270_SDO_ADDR`, 0 nearby
  copper). Rejected: IMU_INT1 (17 mm MCU-adjacent single strap), IMU_COMBO (52 mm half-board span, needs a via);
  excluded per mandate community-header/RF/NFC/USB/crystals/switching (ACC_5V boost)/rails/class-D SPK.
  **(3) Two congested primaries EMPIRICALLY DISPROVEN (one foreground run each, authoritative untouched):**
  `route U11_PROG` → INCOMPLETE (1/2): `ILIM_VSET` clean (4.857 mm) but `ISET` R37.1→**U11.8 NO LEGAL ESCAPE** —
  boxed by BQ25185 pins U11.6/U11.9 + board edge (pad-local wall, order-independent); `route PWR_SENSE` →
  INCOMPLETE (2/4): R104.2→TP31.1 + TP11.1→U14.5 **no legal corridor** even at the 0.025 mm fine grid (west
  `BAT_PROTECTED_P` trunk); both confirm the congestion screen, AUTH sha UNCHANGED after each, no rule weakened.
  **(4) The pristine fallback, EARNED — the gate (real full-board, D-286):** `route IMU_ADDR` → ALL OK (R118.1↔
  R119.2 2.709 mm, R119.2↔U4.1 3.454 mm; 8 segments; 0.200 mm B.Cu, 0 via; 3-pad/2-edge MST); prior copper
  deleted/altered = 0 (D-306 494 trk + 55 via multiset is a SUBSET); every new item a target-group net; ZERO
  zones fill-changed (no via); `BMI270_SDO_ADDR` fully connected (open-edges 2→0); 0 prior pairs regressed; pcbnew
  **ratsnest 695→693** (−2); real kicad-cli DRC no new/worse class. **GATE PASS.** **(5) Promoted:** authoritative
  `sha256 9c0586d8…3f62259` → **`a309f8ce022b48ef04baa2fef591c64eb1a643049ad31220a9cff24831279a50`**; tracks
  **494→502** (+8 BMI270_SDO_ADDR); vias **55** (no new via); 6 layers / 41 zones unchanged; journal **86→88**
  (+2 `REST_INC`); PCB file diff **64 ins / 0 del** — pure ADD-ONLY (8 B.Cu `segment` lines; zero
  segment/via/footprint/filled_polygon deletions, grep-confirmed; cleanest increment yet); real KiCad DRC
  **identical** (`{solder_mask_bridge:1, hole_clearance:5, lib_footprint_issues:199, unconnected_items:499}`).
  **(6) Tests:** new contract **G21** (G18–G20 stay green unchanged — ADD-ONLY invariants already exclude all
  `REST_INC` nets generically) → `router_regression.py` **ALL 92 CHECKS PASS (G1–G21)**, deterministic; new probe
  `checks/incremental_probe_009.py` ALL PASS; `checks/incremental_probe_006/007/008.py` refreshed to the D-307
  board (`_008` pre-DISP-copper check generalised) ALL PASS; `checks/phaseB_bringup_probe_005.py` updated
  (502/55/88; 7 routed rest nets, 157 unrouted) ALL PASS. **Open owner decisions: NONE;** `JLCPCB_READINESS`
  unchanged (~77 %). Rollback: pre-promotion `sha256 9c0586d8…3f62259` (D-306; parent `73ea58e`). Next:
  **FBV2-P2-010 — continue rest-of-board routing (next bounded group, same framework); the two congested regions
  (BQ25185/BPP trunk, west BAT trunk) are now characterised hard walls — do NOT re-attempt naively.** Full
  analysis:
  [`audits/2026-08-30-p2-009-d307-fourth-rest-of-board-incremental-increment-imu-addr-promoted.md`](audits/2026-08-30-p2-009-d307-fourth-rest-of-board-incremental-increment-imu-addr-promoted.md).
- **FBV2-P2-008 / D-306 (THIRD REST-OF-BOARD INCREMENT PROMOTED; FIRST VIA / MIXED-LAYER
  PRIMITIVE):** a governed CTO **ACCEPT + PROMOTE** — a third rest-of-board net is on the authoritative board,
  and for the first time the increment uses a **via / mixed-layer route**, with **no Phase-A / FRONT_RGB / ACC
  casualty and no new DRC**; autonomy CONTINUES, **no owner decision.** Starting HEAD `c22b9fd` (D-305; pushed;
  `origin/master` identical). **(1) Same `incremental_router.py`, minimally extended** — three generic mechanics,
  each forced by a concrete need: `edge_plan` (per-edge layer decision — same-layer B.Cu groups stay
  byte-identical), `connect_cross` (composes only proven `qrouter` primitives escape→via_site→via→two anchored
  `connect_role` runs, so **`qrouter.py` is untouched** and the battery driver unaffected), `refill_planes`
  (re-pours only In1/In4 when a via was laid). **(2) Group selection (measured, prefer a new safe primitive —
  baseline `f0046eb7…` 483/54/6, ratsnest 697, journal 84; `w/screen_007.py`, READ-ONLY):** CHOSE **DISP_RST
  (`/DISP_RST_N`)** — one 3-pad display-reset net with pads NOT all on one layer (R16.1/J1.10 F.Cu, U2.8 B.Cu):
  MST = one SAME-LAYER edge (R16.1↔J1.10, first incremental F.Cu run) + one CROSS-LAYER edge (J1.10↔U2.8, first
  incremental via / mixed-layer route, ONE 0.60/0.30 Default through via ≥ 0.50 mm min_via), low congestion (2
  Phase-A items in bbox+2 mm), NONCRITICAL low-speed reset. Rejected: AUDIO_SPK (F.Cu+THT but class-D SWITCHING
  outputs, excluded), U11_PROG (16 items, coupled to safety-critical BPP path), PWR_SENSE (12 items, congested);
  FALLBACK held (not needed): IMU_STRAP `BMI270_SDO_ADDR` B.Cu singleton; excluded per mandate
  community-header/RF/NFC/USB/crystals/rails. **(3) First-via blocker, characterised (not brute-forced):** the
  through via pierces the In1/In4 GND planes; the stale plane fill had no anti-pad (first gate: `clearance` ×2 +
  `hole_clearance` ×2 at (52.95,87.0)). Focused evidence — a plain refill drifts ONLY zones 39/40 (In1/In4 GND,
  +35 pts each, a stored-vs-current `ZONE_FILLER` discrepancy independent of the via) and no other zone — so
  `route` re-pours EXACTLY In1/In4 when a via was laid; DRC returns to baseline IDENTICALLY (plane byte-equality
  NOT claimed; standard = DRC-neutral + "only In1/In4 changed"). **(4) The gate (real full-board, D-286):** prior
  copper deleted/altered = 0 (D-305 483 trk + 54 via multiset is a SUBSET); every new item a target-group net;
  ONLY In1/In4 GND planes re-poured (all other 39 zones identical); DISP_RST_N fully connected across the hop
  (open-edges 2→0); 0 prior pairs regressed; pcbnew **ratsnest 697→695** (−2); real kicad-cli DRC no new/worse
  class. **GATE PASS.** **(5) Promoted:** authoritative `sha256 f0046eb7…04c7cd41` → **`9c0586d8…e3f62259`**;
  tracks **483→494** (+11 DISP_RST_N); vias **54→55** (+1 F↔B through via); 6 layers / 41 zones unchanged;
  journal **84→86** (+2 `REST_INC`); board diff **470 ins / 336 del** (all 336 deletions are In1/In4
  `filled_polygon` xy — the plane re-pour; zero deleted segment/via/footprint lines); real KiCad DRC **identical**
  (`{solder_mask_bridge:1, hole_clearance:5, lib_footprint_issues:199, unconnected_items:499}`). **(6) Tests:**
  new contract **G20** (+ G18/G19 generalised to pin `phaseA_via`==54 instead of `all_via`==54) →
  `router_regression.py` **ALL 89 CHECKS PASS (G1–G20)**, deterministic; new probe
  `checks/incremental_probe_008.py` ALL PASS; `checks/incremental_probe_006/007.py` refreshed ALL PASS;
  `checks/phaseB_bringup_probe_005.py` updated (494/55/86; 6 routed rest nets, 158 unrouted) ALL PASS. **Open
  owner decisions: NONE;** `JLCPCB_READINESS` unchanged (~77 %). Rollback: pre-promotion `sha256
  f0046eb7…04c7cd41` (D-305; parent `c22b9fd`). Next: **FBV2-P2-009 — continue rest-of-board routing (next
  bounded group, same framework).** Full analysis:
  [`audits/2026-08-30-p2-008-d306-third-rest-of-board-incremental-increment-disp-rst-via-promoted.md`](audits/2026-08-30-p2-008-d306-third-rest-of-board-incremental-increment-disp-rst-via-promoted.md).
  This checkpoint is written in the D-306 commit; a fresh session must confirm the live tip with
  `git rev-parse HEAD` and `git rev-parse origin/master`.
- **FBV2-P2-007 / D-305 (SECOND REST-OF-BOARD INCREMENT PROMOTED):** a governed CTO
  **ACCEPT + PROMOTE** — a second rest-of-board net-group is on the authoritative board, with **no Phase-A /
  FRONT_RGB casualty and no new DRC**; autonomy CONTINUES, **no owner decision.** Starting HEAD `6353bd7`
  (D-304; pushed; `origin/master` identical). **(1) Same reusable lever** `checks/incremental_router.py`
  (no new mechanics — only a new `GROUPS` entry). **(2) Group selection (measured, `incremental_router.py
  baseline` + `w/screen_007.py`, READ-ONLY):** CHOSE **ACC_3V3_CTL** (`/ACC_3V3_EN` + `/01_POWER_TREE/
  ACC_3V3_ILIM`) — accelerometer 3V3 load-switch (U20) local control: enable (U3.15 → R98/U20.1/TP26, a
  4-pad multi-terminal net) + current-limit set (R97 → U20.4); both Default netclass (0.200 mm width /
  clearance, **no via**), all B.Cu SMD, low-congestion (only 4 Phase-A B.Cu strands within bbox + 2 mm),
  NONCRITICAL low-current control; **adds the multi-segment MST primitive** (FRONT_RGB were all single-edge
  2-pad). Rejected: IMU_STRAP `BMI270_SDO_ADDR` (clean but singleton — kept as fallback), PWR_SENSE (12
  nearby copper, congested), U11_PROG (16 nearby, D-302 wall region), AUDIO_SPK (F.Cu/THT/analog), DISP_RST
  (MIX-layer needs a via); excluded per mandate community-header/RF/NFC/USB/crystals/rails. **(3) The gate
  (real full-board, D-286):** prior copper deleted/altered = 0 (D-304 452 trk + 54 via multiset is a SUBSET);
  every new item a target-group net; both nets fully copper-connected (ACC_3V3_ILIM 1→0, ACC_3V3_EN 3→0); 0
  prior requested pairs regressed; pcbnew **ratsnest 701→697** (−4); real kicad-cli DRC no new/worse class.
  **GATE PASS.** **(4) Promoted:** authoritative `sha256 00c93bdb…dfb72aad` → **`f0046eb7…04c7cd41`**; tracks
  **452→483** (+31 ACC_3V3_CTL); vias **54** (no new via); 6 layers / 41 zones unchanged; journal **80→84**
  (+4 `REST_INC`); board diff **248 ins / 0 del** (ADD-ONLY at file level); real KiCad DRC **identical**
  (`{solder_mask_bridge:1, hole_clearance:5, lib_footprint_issues:199, unconnected_items:499}`). **(5)
  Tests:** new contract **G19** (+ G18 generalised to exclude all `REST_INC` nets) → `router_regression.py`
  **ALL 86 CHECKS PASS (G1–G19)**, deterministic; new probe `checks/incremental_probe_007.py` ALL PASS;
  `checks/incremental_probe_006.py` refreshed ALL PASS; `checks/phaseB_bringup_probe_005.py` updated
  (483/84; 5 routed rest nets, 159 unrouted) ALL PASS. **Open owner decisions: NONE;** `JLCPCB_READINESS`
  unchanged (~77 %). Rollback: pre-promotion `sha256 00c93bdb…dfb72aad` (D-304; parent `6353bd7`). Next:
  **FBV2-P2-008 — continue rest-of-board routing (next bounded group, same framework).** Full analysis:
  [`audits/2026-08-30-p2-007-d305-second-rest-of-board-incremental-increment-acc-3v3-ctl-promoted.md`](audits/2026-08-30-p2-007-d305-second-rest-of-board-incremental-increment-acc-3v3-ctl-promoted.md).
  This checkpoint is written in the D-305 commit; a fresh session must confirm the live tip with
  `git rev-parse HEAD` and `git rev-parse origin/master`.
- **FBV2-P2-006 / D-304 (FIRST REST-OF-BOARD INCREMENT PROMOTED):** a governed CTO
  **ACCEPT + PROMOTE** — the first rest-of-board copper is on the authoritative board, with **no Phase-A
  casualty and no new DRC**; autonomy CONTINUES, **no owner decision.** Starting HEAD `50149f4` (D-303;
  pushed; `origin/master` identical). **(1) The reusable lever:** `checks/incremental_router.py` — a scoped
  INCREMENTAL router/promoter (commands `baseline`/`route`/`gate`/`promote`) that loads the promoted board via
  `qrouter.QBoard` (all existing copper is an OBSTACLE; new copper is ADDED, never `Remove()`d), routes a
  bounded named net-GROUP into a scratch copy `checks/w/INC_<GROUP>/` (authoritative project untouched during
  the experiment — sha256 verified unchanged after `route`), and PROMOTES only on a real full-board gate PASS.
  **(2) Group selection (measured, `w/measure_rest_006.py`, READ-ONLY):** CHOSE **FRONT_RGB**
  (`/08_BUTTONS_EXPANDERS/FRONT_RGB_R_N|G_N|B_N`) — front-panel RGB status-LED control (U23 expander →
  R124/125/126), 6 pads, all B.Cu SMD, Default netclass (0.200 mm width / 0.200 mm clearance, **no via**),
  region carries **ZERO Phase-A copper** (isolated), NONCRITICAL, no rail/RF/USB/HV/clock constraint; rejected
  07_IR (F.Cu/THT near edge, moderate-current emitter), 01_POWER_TREE short pairs (power-adjacent), 05_I2C
  single net; excluded per mandate community-header/RF/NFC/USB/crystals/rails. **(3) The gate (real
  full-board, D-286):** Phase-A copper deleted/altered = 0 (D-302 copper-item multiset is a SUBSET of the
  routed items); every new item a target-group net; each target net fully copper-connected
  (`GetConnectedItems`, 1→0); 0 prior Phase-A requested pairs regressed (71); pcbnew **ratsnest 704→701**
  (−3); real kicad-cli DRC no new/worse class. **GATE PASS.** **(4) Promoted:** authoritative
  `sha256 63a9bc54…f87d6ba9` → **`00c93bdb…dfb72aad`**; tracks **432→452** (+20 FRONT_RGB); vias **54** (no
  new via); 6 layers / 41 zones unchanged; journal **77→80** (+3 `REST_INC`); real KiCad DRC **identical**
  (`{solder_mask_bridge:1, hole_clearance:5, lib_footprint_issues:199, unconnected_items:499}`). **(5)
  Tests:** new contract **G18** + `router_regression.py` **ALL 82 CHECKS PASS (G1–G18)**, deterministic; new
  probe `checks/incremental_probe_006.py` ALL PASS; `checks/phaseB_bringup_probe_005.py` updated to the
  promoted state (452/80; 3 routed rest nets, 161 unrouted) ALL PASS. **Open owner decisions: NONE;**
  `JLCPCB_READINESS` unchanged (~77 %). Rollback: pre-promotion `sha256 63a9bc54…f87d6ba9` (D-302; parent
  `50149f4`). Next: **FBV2-P2-007 — continue rest-of-board routing (next bounded group, same framework).**
  Full analysis:
  [`audits/2026-08-30-p2-006-d304-first-rest-of-board-incremental-increment-front-rgb-promoted.md`](audits/2026-08-30-p2-006-d304-first-rest-of-board-incremental-increment-front-rgb-promoted.md).
  This checkpoint is written in the D-304 commit; a fresh session must confirm the live tip with
  `git rev-parse HEAD` and `git rev-parse origin/master`.
- **FBV2-P2-005 / D-303 (prior checkpoint — PHASE-B BRING-UP):** a governed CTO **CHARACTERIZATION +
  INTEGRITY + SCOPING** milestone on the promoted board — **no copper change, authoritative PCB byte-identical
  (`sha256 63a9bc54…f87d6ba9`), autonomy CONTINUES, no owner decision.** Starting HEAD `01a38a5` (D-302; pushed;
  `origin/master` identical). **(1) Exact Phase-B definition (from the code):** "Phase B" here is the
  battery-block REPLAY / IDEMPOTENCE verification of the D-271 discipline, **NOT** rest-of-board routing —
  `replay_battery_block.py` (verbatim scratch→authoritative promotion), `route_battery_block.py` SECTION 17
  `AQROOT_REPLAY` (independent journal reproduction, frozen order / pinned widths / `passes=2`, on a clean
  scratch), `phaseB_compare.py` (the A-vs-B gate); the driver is **power-tree scoped ONLY**. **(2) Integrity
  re-verified:** `HEAD == origin/master == 01a38a5`, clean; PCB `sha256 63a9bc54…f87d6ba9` / size 1475931;
  **432 tracks / 54 vias / 6 layers / 41 zones / 324 footprints**; journal **77 entries**; **all 432 routed
  tracks are in-scope power-tree nets (0 out-of-scope) → Phase-A battery-block copper ONLY**;
  `router_regression.py` = **ALL 79 CHECKS PASS (G1–G17)**; shared journal not mutated. **(3) The existing
  Phase-B drivers assume a copper-EMPTY base (the sharply-characterized blocker, proven):**
  `replay_battery_block.py:40-42` refuses a non-empty authoritative board (`raise SystemExit`) → post-promotion
  (432 tracks) it can never re-run (role already fulfilled byte-identically by D-302); SECTION-17 replay
  (`:2297`) SKIPS every `role=='TRUNK+ESCAPE'` entry — **exactly the one entry defining the promotion**
  (`BAT_PROTECTED_P U11.2→C36.1, w=1.5, reinforcement=True`) → a replay carries 76/77 items, drops the wall
  closure, would NOT reproduce the board; `phaseB_compare.py` needs a `phaseB.json` never produced. The replay
  machinery predates the D-297/D-299/D-301/D-302 levers and is **stale**. **(4) The promotion is sound
  regardless:** byte-identical to a scratch from a GENUINE full-authority Phase-A gate (`run_003t_full.sh 004b2`,
  `DRIVER_EXIT=0`, PHASE A COMPLETE) — real driver / real order, not a proxy (D-286) — DRC zero new copper
  classes, regression ALL PASS. **(5) Real remaining Phase-B, scoped (next lever):** rest-of-board = **164
  multi-pad nets, 0 routed** across 9 subsystem sheets + rails (GND 259 pads, +3V3 86; 09_COMMUNITY_HEADER 20
  nets, 04_SPI_B_RADIOS_NFC 20, 01_POWER_TREE-beyond-block 18, top 17, 08_BUTTONS_EXPANDERS 10, …) = ~85 % of
  remaining routing with **NO driver** — the next lever is a **new scoped INCREMENTAL driver** that loads the
  promoted board, **PRESERVES the Phase-A copper** (never erase/reroute), routes a bounded isolated net-group
  first, gated by real full-board DRC (D-286), promoted only on a genuine no-casualty / no-new-DRC increment.
  Added `checks/phaseB_bringup_probe_005.py` (READ-ONLY, reproducible; ALL PASS). **Open owner decisions: NONE;**
  `JLCPCB_READINESS` unchanged (~77 %). Next: **FBV2-P2-006 — begin rest-of-board routing.** Full analysis:
  [`audits/2026-08-30-p2-005-d303-phaseB-bringup-characterization-integrity-scope.md`](audits/2026-08-30-p2-005-d303-phaseB-bringup-characterization-integrity-scope.md).
  This checkpoint is written in the D-303 commit; a fresh session must confirm the live tip with
  `git rev-parse HEAD` and `git rev-parse origin/master`.
- **FBV2-P2-004B2 / D-302 (prior checkpoint — FIRST AUTHORITATIVE COPPER):** the **first authoritative
  Phase-A copper promotion** is COMMITTED. The verified `AQROOT_U11_RETARGET`→`C36.1` full-run board
  (`run_004b2_full.log`, `DRIVER_EXIT=0`, PHASE A COMPLETE) becomes the authoritative PCB — **byte-identical**
  to the `checks/w/FULL003T_004b2_u11retarget` scratch (`sha256 63a9bc54…f87d6ba9`): **432 tracks, 54 vias,
  6 copper layers, direction-2 placement** (fingerprint `397dffe1f77e4d10`), **ratsnest 704 (−77)**, 41 zones,
  and a **77-entry `phaseA_journal.json`** (incl. the `U11.2→C36.1` `reinforcement:True` tap that closes the
  D-301 wall as a SHORT ≥1.20 mm on-net reinforcement, not a cross-board trunk). It carries the **regenerated
  DRU** it requires (67→119 rules; the accepted D-249/D-257/D-258/D-263/D-264/D-266/D-269 per-net escape/tap/
  stub/trunk/clearance rule set — **not a relaxation**; the old HEAD DRU is stale because without those named
  rules DRC would spuriously flag legal accepted copper). Real KiCad DRC on the authoritative board =
  `{hole_clearance:5, lib_footprint_issues:199, solder_mask_bridge:1, unconnected_items:499}` — **ZERO new
  copper DRC classes** (the D-301 scratch `track_width:1` is resolved). **PHASE A COPPER ONLY — NOT ALL ROUTING
  COMPLETE** (ratsnest 704 / unconnected_items 499: Phase B and the remaining nets are unrouted). The
  router-regression harness was made compatible with a routed authoritative board (routine engineering, **not**
  an owner decision): a new copper-CLEAN `scratch_clean()` fixture feeds the primitive vehicles (CASES G2–G6,
  CONFLICTS, G7, G8, G9, G11, G12) while G1/G10 + the real-DRC/probe/judge harnesses keep validating the real
  routed board; CONFLICTS `U18.8`/`U18.9` re-pinned 0.250→**0.245 mm** (U18 moved by the accepted placement;
  still ≪ floor → conflict PRESERVED); new contract **G17** guards the promotion. `router_regression.py` =
  **ALL 79 CHECKS PASS (G1–G17)**, run twice, deterministic; `u11_retarget_probe_004b.py` = ALL PASS.
  **Rollback preserved:** pre-promotion PCB `sha256 2235e273…d642d7e` (parent `56d0ebe`) + tags
  `beta-v2-p2-battery-pre-authoritative` / `beta-v2-p2-pre-sixlayer-authoritative`. Mandated **Opportunity &
  Simplification Scan** (§9a): the fixture split makes the harness robust to every future promotion; **Open
  owner decisions: NONE.** `JLCPCB_READINESS` NOT edited (conservative: keep ~77 %, not fab-ready — Phase-A
  only). Next: **FBV2-P2-005 — Phase B bring-up on the promoted board** (screen full DRC per D-286, promote
  only on a genuine gate PASS). Full analysis:
  [`audits/2026-08-30-p2-004b2-d302-first-authoritative-phasea-copper-promotion-regression-fixture-fix.md`](audits/2026-08-30-p2-004b2-d302-first-authoritative-phasea-copper-promotion-regression-fixture-fix.md).
  This checkpoint is written in the D-302 commit; a fresh session must confirm the live tip with
  `git rev-parse HEAD` and `git rev-parse origin/master`.
- **FBV2-P2-004A / D-301 (prior checkpoint):** a governed **CTO ACCEPT + COMMIT + overall-run FAIL**
  — the `AQROOT_LTCGATE_KO` **path-shaping** lever (a net-foreign central-lane keep-out installed for
  exactly the `LTC_GATE U18.10→Q3.4` join and lifted right after, on the proven `AQROOT_U19CAP`
  mechanism — **NOT a re-order**, which D-300 refuted) was full-authority-gate-run
  (`AQROOT_U18BPP_JOIN=I3 AQROOT_U19CAP=1 AQROOT_LTCGATE_KO=1 … 004a_ltcgate1`, secs 1500.2,
  `checks/w/phaseA_003t_full_004a_ltcgate1.json`, judged by `w/judge_004a.py`) and proved a
  **GENUINE +1**: vs the D-299/003Y2 baseline connections **72→73**, ratsnest 705/−76 → 704/−77,
  journal 75→76, connected-set diff **GAINED 1 (`LTC_GATE Q3.4↔U18.10`, F.Cu, 2× 0.35 FINE_ESC vias,
  8.556 mm) / LOST 0** — not a swap; vs 003W it also preserves the D-299 U19 pins (LOST 0); final DRC
  **identical** (`{hole_clearance:5, lib_footprint_issues:199, solder_mask_bridge:1, track_width:1,
  unconnected_items:499}`), no new class, no sub-0.50 non-fine via. The real cause of the wall was
  **D-269 alone** (clearance 0.2803 vs 0.300 mm; FINE_ESC legalises the D-257 via, so no D-249
  track_width violation in the real path). So `AQROOT_LTCGATE_KO` is **ACCEPTED and COMMITTED** (banked
  env-gated / **OFF by default**, byte-identical when unset, pinned by **G15**); production WIP was
  **pruned to the narrow lever** (the bulky ~118-line in-run probe `_ltcgate_probe`/`AQROOT_LTCGATE_PROBE`
  removed; evidence lives in the audit/artifacts). **Copper is NOT promoted** — 004A is the FIRST run to
  close every upstream wall and reach the final `u11_escape()` step, which now FAILs: the terminal wall
  advances to **`U11.2 escape: none exists`** (the `BAT_PROTECTED_P` 1.5 mm high-current trunk endpoint;
  a structural ≥1.20 mm-trunk NO_LEGAL_PATH, the D-273/274/281/282/283 class — not a ~20 µm DRC pinch).
  **Readiness/progress UNCHANGED; autonomy CONTINUES** (no owner decision). Mandated Opportunity &
  Simplification Scan (§9a): the U11.2 wall is reducible (a short on-net ≥1.20 mm tap beats a cross-board
  trunk); no BOM/capability/architecture opportunity forces a change; **Open owner decisions: NONE.** Also
  created at this safe boundary: **`docs/full-beta-v2/DEVICE_SPEC.md`** (authoritative current-product
  spec/index). Next: **FBV2-P2-004B** — the `U11.2` BPP trunk-endpoint retarget lever (§5). This checkpoint
  is written in the D-301 commit; a fresh session must confirm the live tip with `git rev-parse HEAD` and
  `git rev-parse origin/master`.
- **FBV2-P2-003Z / D-300 (this checkpoint):** a governed **CTO FAIL / lever refutation + WIP retirement**
  — the `AQROOT_LTCGATE` **defer-to-congestion** lever (a pure re-order: pull `LTC_GATE U18.10→Q3.4`
  out of section `8b` and re-queue it LAST as a `13z` stage) was full-authority-gate-run
  (`AQROOT_U18BPP_JOIN=I3 AQROOT_U19CAP=1 AQROOT_LTCGATE=1 … 003z3_ltcgate`, secs 1497.0,
  `checks/w/phaseA_003t_full_003z3_ltcgate.json`, judged by `w/judge_003z.py`) and proved
  **behaviourally identical to D-299/003Y2**: connections 72=72, skipped 101=101, ratsnest 705/−76
  = 705/−76, journal 75=75, connected-set diff **GAINED 0 / LOST 0**, the SAME `LTC_GATE U18.10→Q3.4`
  terminal wall with the SAME `track_width` (D-249 min 1.2000 mm; actual 0.2000 mm) + `clearance`
  (D-269 0.3000 mm; actual 0.2803 mm) rejections, final DRC histogram identical. **A pure re-order is a
  NULL OPERATION on this wall** — the driver's `connect_role` greedily re-takes the identical
  rule-violating central path even queued last. The focused `ltcgate_join_probe_003z.py` was a
  **false-positive proxy** (its post-hoc `connect_role` on the SAVED board found a legal ~10.5 mm west
  detour that the real in-run driver never takes; per D-286 a proxy cannot override the full gate). So
  the lever and its **G15** WIP are **REJECTED/RETIRED** via an exact reverse patch scoped to the two
  tracked files (`git diff -- route_battery_block.py router_regression.py | git apply -R`, NOT a broad
  reset; post-revert `git hash-object` = `HEAD:` blob for each, `git grep` for the retired symbols NO
  match), and the false-positive probe is **retired** (untracked, never committed) so **no artifact
  claims the lever works**. **Copper is NOT promoted** — full Phase-A still FAILs at the unchanged
  `LTC_GATE U18.10→Q3.4` wall; **readiness/progress UNCHANGED; autonomy CONTINUES** (no owner decision).
  Mandated **Opportunity & Simplification Scan** (§9a): no product-capability / BOM / recoverability /
  testability / manufacturing / firmware / UX / future-option opportunity justifies changing
  architecture; **Open owner decisions: NONE.** Next: **FBV2-P2-004A** — the `LTC_GATE U18.10→Q3.4`
  **path-shaping** lever (a central-lane keep-out forcing the proven west detour — NOT a re-order, §5).
  This checkpoint is written in the D-300 commit; a fresh session must confirm the live tip with
  `git rev-parse HEAD` and `git rev-parse origin/master`.
- **FBV2-P2-003Y / D-299 (prior checkpoint):** a governed **CTO ACCEPT + COMMIT + overall-run FAIL + HANDOFF**
  — the D-298 U19 CAPACITY lever's **full-authority gate COMPLETED** and it is a **GENUINE +2** connected-set
  gain (NOT the D-296 swap): vs the D-297 003W baseline (conn 70) connections **70→72**, and the connected-set
  diff GAINED **exactly 2** — `N_BATDIV R89.2→U19.6` and `REC_BAT_LOW (node)→U19.7` (both SIG, F.Cu, 2 vias,
  board-legal 0.60/0.30) — with **LOST 0**; `LTC4368_FAULT_N` detours CLEANLY (`R82.1→Q9.1` 77.567 mm, not the
  terminal wall); final DRC **identical** to 003W, no sub-0.50 non-fine via. So `AQROOT_U19CAP` is **ACCEPTED and
  COMMITTED** (banked env-gated / **OFF by default**, byte-identical when unset, pinned by **G14**). **Copper is
  NOT promoted** — full Phase-A still FAILs, the terminal wall newly ADVANCING **past the whole U19 field** to
  `LTC_GATE U18.10→Q3.4` (candidate join paths **DRC-gate-rejected** by the frozen **D-249** BPP 1.20 mm
  trunk-width and **D-269** BAT_MAIN 0.300 mm clearance rules — actual 0.20 mm / 0.2803 mm; NOT `NO_PATH`). The
  gate artifact is `checks/w/phaseA_003t_full_003y2_u19cap.json` (secs 1463.2, judged by `w/judge_003y2.py`); the
  shared `phaseA_journal.json` was restored byte-identical to HEAD and no process remains. **Readiness/progress
  UNCHANGED; autonomy CONTINUES** (no owner decision). Next: **FBV2-P2-003Z** — the `LTC_GATE U18.10→Q3.4` join
  corridor lever (§5). This checkpoint is written in the D-299 commit; a fresh session must confirm the live tip
  with `git rev-parse HEAD` and `git rev-parse origin/master`.
- **FBV2-P2-003X / D-298 (prior checkpoint):** a governed **CTO IMPLEMENT + SCREEN + HANDOFF** — the
  bounded U19 CAPACITY lever (`AQROOT_U19CAP`: reserve the U19.7/U19.6 shared east escape lane so
  `LTC4368_FAULT_N` detours, and close `REC_BAT_LOW U19.7` before `N_BATDIV U19.6`) is implemented
  env-gated / **OFF by default**, pinned by regression **G14**, and **screened DRC-clean** on the real
  003W full-run board (both boxed U19 pins escape SIMULTANEOUSLY onto bare In3/In2 with the only
  board-legal 0.65/0.40 via — a capacity ADD, categorically distinct from the refuted D-296 swap).
  **Copper is NOT promoted** — the ~22-min full-authority gate (net +2 vs swap; FAULT_N clean detour)
  has not run (exceeds the ACP cap; may not be backgrounded). Source is left **uncommitted** (docs
  committed) per the 003X discipline; **autonomy CONTINUES** (no owner decision raised). Next:
  **FBV2-P2-003Y** executes the gate (§5).
- **FBV2-P2-003W / D-297 milestone commit (prior checkpoint):** a governed **ACCEPT of a
  SECONDARY lever + a governed FAIL of the overall Phase-A run** (source + docs + probe commit);
  **autonomy CONTINUES** (a normal Phase-A FAIL is not a stop reason; no owner decision raised).
  003W implemented the D-295/D-296 SECONDARY lever — an env-gated (`AQROOT_U18BPP_JOIN`, **OFF by
  default**) override that completes the `BAT_PROTECTED_P U18.8 → R75.2` reserve **JOIN on In3**
  instead of the severed In2 lane — as a +25/−1-line change to `checks/route_battery_block.py`, pinned
  by a **G13** regression contract in `checks/router_regression.py` and the measured-record probe
  `checks/u18_i3_join_probe_003w.py`. **The wall (D-294/295):** at the direction-2 placement
  `t_a_r77e15n10_r79e15n10` the two 0.35/0.20 **THROUGH** reserve vias land at `R75.2`(2.800,66.800)
  and `U18.8`(7.200,66.500) on In2, and their In2 JOIN is `NO_PATH` — a `BAT_RAW` 0.600 mm
  current-path wall runs vertically on In2 at x≈6.4→6.65 (y 50.45→70.40), severing the west→east
  lane. **The lever:** the reserve vias are THROUGH vias (copper on every layer), so the join is
  electrically identical on In2 or In3; **In3.Cu is a routable six-layer signal layer**
  (`ROUTABLE[6]=('F','B','I2','I3')`) that is **EMPTY across the whole corridor** on the real
  full-run board (2 In3 tracks board-wide, none here; no In3 pour — only the In1/In4 GND planes), so
  `AQROOT_U18BPP_JOIN=I3` completes the ONE branch on In3 with **NO new via, NO DRU/floor change, NO
  topology change**; unset → the join stays on `va[2]` (In2), byte-identical to every prior run. **The
  probe** (on the actual full-run routed board, throwaway copy): In2 join `NO_PATH`, In3 join **ok
  4.410 mm**, real KiCad DRC **ZERO new classes**, `via_dangling` **1→0**. **The full authority gate**
  (`checks/w/phaseA_003t_full_003w_u18bpp_i3.json`, secs 1272.5) vs the D-294 baseline
  `w/phaseA_003t_full_e15n10cto.json`: connections **69→70** (+1), skipped-already-connected **98→99**
  (+1 — one downstream `BAT_PROTECTED_P` pad now found already-joined on the closed net; a positive
  sign, not a loss), ratsnest **708/−73 → 707/−74**, journal **72→73** (+1: `JOIN U18.8→R75.2` layer
  **I3**, 4.410 mm, **0 vias**), DRC `via_dangling` **1→0** with **no new class**
  (`{hole_clearance:5, lib_footprint_issues:199, solder_mask_bridge:1, track_width:1,
  unconnected_items:499}`), terminal fatal wall **UNCHANGED** (`REC_BAT_LOW U19.7→(node)
  NO_LEGAL_ESCAPE`, `N_BATDIV U19.6` next-in-line). **The decisive diff is a STRICT PURE GAIN:** the
  entire journal delta is **exactly one added JOIN entry with NOTHING lost** — the categorical
  opposite of D-296's 1-for-1 swap; the In3 join takes routing capacity from **no other net** (In3 is
  unused), so no casualty is possible and none occurs. **Ruling:** the SECONDARY lever is a genuine,
  board-legal, verified net gain — **ACCEPTED** and retained env-gated/OFF-by-default in tracked
  source (byte-identical when unset), pinned by G13 + the probe. **But copper is NOT promoted:**
  Phase-A copper promotes only on a full-authority PASS (D-286), and the run still FAILs on the
  unchanged saturated U19 field — so the authoritative board stays six layers / 0 tracks / 0 vias and
  **readiness/progress DO NOT move.** D-297 **banks** the U18.8 closure in source: once the U19 field
  is separately enlarged, this lever (ON) yields the U18.8 join for free (no new via, no new DRC).
  **No copper, no placement, no rule, no floor, no topology/footprint/outline change; no DRC absorbed;
  no promotion.** `/home/aqroot8/.aqroot-autopilot-stop` is ABSENT; autonomy continues with
  **FBV2-P2-003X** (§5) — a bounded U19 capacity lever for the simultaneous `REC_BAT_LOW U19.7` +
  `N_BATDIV U19.6` closure. Prior milestone: `27f9790` (D-296, 003V PRIMARY reservation family
  refuted). This checkpoint is written in the same commit; a fresh session must confirm the live tip
  with `git rev-parse HEAD` and `git rev-parse origin/master`.
- **Prior FBV2-P2-003V / D-296 milestone:** a governed **FAIL / primary-family refutation** commit
  (docs only); **autonomy CONTINUES**. 003V implemented the D-295 PRIMARY lever — an env-gated
  (`AQROOT_U19_RESV`, OFF by default) reservation of `REC_BAT_LOW U19.7`'s B.Cu escape scored toward
  Q7.1 — and full-gate-ran it twice. **RESV (0.35/0.20)** is behaviourally identical to D-294 (the
  corridor-less sub-minimum via is rejected on `via_diameter`/`annular_width`, the reservation is
  dropped, the run falls through unchanged; connected-set diff EMPTY both ways). **RESV2 (0.60/0.30
  board-legal)** FIRES and CLOSES U19.7 (rung self-corrects to the ordinary Default 0.60/0.30) — but
  it is a bounded **ordering trade**: conn 69 / skip 98 / ratsnest 708/−73 all unchanged, DRC
  identical, the terminal wall merely MOVES to `N_BATDIV U19.6`. **The decisive diff (D-294→RESV2) is
  a strict 1-for-1 swap:** GAINED `REC_BAT_LOW U19.7→Q7.1`, LOST `REF_POL TP24.1→U19.2`, count 68→68 —
  the U19 field is capacity-saturated, so reserving U19.7's lane only chooses which neighbour is
  abandoned. Positive finding recorded (the mechanism is REAL, U19.7 closable in principle,
  board-legal) but a swap is not a net gain, so per D-286 nothing promotes copper. **The
  `AQROOT_U19_RESV` source WIP was RETIRED** via an exact reverse patch (`git apply -R`; worktree blob
  `bba62d35…` = `HEAD:checks/route_battery_block.py`, `git grep U19_RESV` no match). No source/copper/
  placement/rule change survived; no DRC absorbed; no promotion. Prior milestone: `a2e27fc` (D-295).
- **Prior FBV2-P2-003U / D-295 milestone:** a governed **characterization / NO-PROGRESS + HANDOFF**
  commit (docs only); autonomy CONTINUES. 003U proved both D-294 walls are FULL-RUN-EMERGENT
  ordering/congestion casualties and NO cheap vehicle judges either at the direction-2 placement. The
  PRIMARY (`REC_BAT_LOW U19.7`) was diagnosed EXACTLY and shown REDUCIBLE-in-principle (it escaped
  cleanly in 003O as `U19.7→Q7.1` F.Cu 14.907 mm; direction-2's +2-connection congestion **swapped
  `VREC_VCC`'s two segments' layers** — `U19.8→C60.1` went B.Cu(0 via)→F.Cu(2 via) — so U19.8's
  pad-escape now occupies the F lane immediately south of U19.7 that carried U19.7 in 003O; `U19.8`
  ×26 the dominant blocker; U19.7 is a greedy-tightest-first casualty and, as a `(node)` join,
  ineligible for the D-278 inner hop guarded `and not node`). The SECONDARY (U18.8 I2 join corridor)
  is a full-congestion I2 pinch. The ~22-min governing gate cannot run foreground under the ACP
  10-min cap, so 003U delivered a precise CTO handoff. No source/copper/placement/rule change; no DRC
  absorbed; no promotion. Prior milestone: `36662db` (D-294).
- **HEAD == origin/master:** yes (committed and pushed at milestone closeout).
- **Prior milestones (full detail in §4 and CTO_DECISIONS):** `27f9790` D-296 (003V) PRIMARY
  reservation family refuted / WIP retired; `a2e27fc` D-295 (003U) two-walls characterization +
  handoff; `36662db` D-294 (003T) direction-2 executed / full gate FAIL; `9c708f3` D-293 owner
  approval of direction 2.

## 2. Mission
- Deliver Full Beta v2 to **READY FOR JLCPCB** — a fabricable, assembly-ready
  authoritative board with all governing routing / DRC / ERC / connectivity / safety
  gates passing and the final JLCPCB deliverables generated and reviewed.
- Terminal condition: **READY FOR JLCPCB**.

## 3. Current phase / gate
- **Phase P2 — battery/power-block Phase-A routing is COMPLETE and PROMOTED (D-302).** The authoritative
  board carries **432 tracks / 54 vias / 6 layers** of Phase-A battery-block copper (all in-scope power-tree
  nets, 0 out-of-scope), DRC zero new copper classes, `router_regression` ALL 79 PASS.
- **FBV2-P2-005 / D-303 defined "Phase B" and scoped the real remaining routing.** In-repo "Phase B"
  (`replay_battery_block.py` / SECTION-17 `AQROOT_REPLAY` / `phaseB_compare.py`) is the battery-block
  replay/idempotence verification and is now **stale + assumes a copper-empty base** (do NOT naively re-run;
  see §1). The promotion is sound without it (rests on a genuine full-authority gate, D-286).
- **Current fabrication blocker (updated by D-323): rest-of-board routing — IN PROGRESS, incrementally.**
  The reusable incremental router/promoter (`checks/incremental_router.py`) is proven across EIGHTEEN promoted
  increments: of the 164 rest-of-board multi-pad nets, **26 are routed (FRONT_RGB 3 + ACC 2 + DISP 1 + IMU 1 +
  FRONT_RGB_LED 3 + IR_RX_VS 1 + TOUCH_CTL 2 + AMP_SD_MODE 1 + SD_CARD_DETECT_N 1 + XGPIO8/XGPIO9 2 +
  XGPIO1/XGPIO0 2 + XGPIO3 1 + BMI270_INT1_STRAP 1 + UART0_TXD_DBG 1 + IR_TX_GPIO16 1 + SD_CS_N 1 +
  RESERVED_SPARE 1 + ACC_DETECT_N 1), 138 remain UNROUTED** across 9 subsystem sheets + rails; ratsnest
  **665**. Each future group is added to the `incremental_router.py` registry and routed → gated (real
  full-board DRC, D-286) → promoted on a genuine no-casualty / no-new-DRC increment (FBV2-P2-026, §5). The
  board carries Phase-A battery-block copper (432 trk / 54 via) **plus** the eighteen rest increments (349 trk
  / 14 via). **FBV2-P2-025 / D-323 added the accelerometer/add-on presence-detect `ACC_DETECT_N` (R64.1
  divider F.Cu / R129.2 series B.Cu / U3.17 PCAL expander GPIO B.Cu, a 3-pad cross-layer net = ONE 0.60/0.30
  through via + ONE same-layer B.Cu run) — a genuine functional detect, promoted in an OPEN region (realized
  copper 3.88 mm clear of `BAT_PROTECTED_P`) after the cleaner-class `DISP_BL_CTL_STRAP` hit a characterized
  local wall (all 3 MST edges `NO_PATH` at 0.200 mm) and `BTN_B_N` failed the gate on a duplicate-ref
  tact-switch connectivity limit: tracks 759→781, vias 67→68, ratsnest 667→665, journal 114→116, no new DRC,
  `router_regression` ALL PASS G1–G35.** **FBV2-P2-024 / D-322 added the reserved/spare community expander GPIO `RESERVED_SPARE` (R130.2 / TP41.1 test
  point / U23.7 PCAL expander, 3-pad ALL-B.Cu SAME-LAYER MST, NO via) — the held clean alternate, promoted in an
  OPEN region 15.5 mm clear of `BAT_PROTECTED_P` after the meaningful display-control candidates
  `DISP_CS_N`/`DISP_DC` hit a characterized J1 display-FPC-connector wall and `BOOT_N` routed only via poor 2.5×
  detours: tracks 749→759, vias 67 unchanged, ratsnest 669→667, journal 112→114, no new DRC,
  `router_regression` ALL PASS G1–G34.** **FBV2-P2-023 / D-321 added the microSD
  SPI chip-select `SD_CS_N` (J2.2 socket / R25.2 / U1.25 MCU, a genuine functional point-to-point control,
  3-pad ALL-F.Cu SAME-LAYER MST, NO via) — a clean increment in an OPEN region 50.1 mm clear of
  `BAT_PROTECTED_P` (the mandate's headline candidate `Net-(U1-EN)` hit a characterized local wall and was set
  aside): tracks 729→749, vias 67 unchanged, ratsnest 671→669, journal 110→112, no new DRC,
  `router_regression` ALL PASS G1–G33.** **FBV2-P2-022 / D-320 added the IR transmit carrier control leg
  `IR_TX_GPIO16` (U1.9 ESP32 GPIO16 → R22.1 series-drive resistor, dedicated 2-pad point-to-point, SAME-LAYER
  F.Cu MST, NO via; the low-current MCU control GPIO isolated by series R22 from the IR_GATE switch node and the
  IR_LED_A/K emitter power) — a clean increment in an OPEN region 35.2 mm clear of `BAT_PROTECTED_P`: tracks
  716→729, vias 67 unchanged, ratsnest 672→671, journal 109→110, no new DRC, `router_regression` ALL PASS
  G1–G32.** **FBV2-P2-021 / D-319 added the debug-console UART transmit line `UART0_TXD_DBG` (U1.37 →
  TP35.1, dedicated 2-pad point-to-point, SAME-LAYER F.Cu MST, NO via) — a clean increment in an OPEN region
  31.3 mm clear of `BAT_PROTECTED_P`: tracks 709→716, vias 67 unchanged, ratsnest 673→672, journal 108→109, no
  new DRC, `router_regression` ALL PASS G1–G31.** **FBV2-P2-020 / D-318 added the IMU/I2C-local interrupt strap
  `BMI270_INT1_STRAP` (4-pad ALL-F.Cu same-layer MST, NO via) — the first clean increment OUTSIDE the saturated
  west-XGPIO F.Cu corridor (D-317 mandate): tracks 691→709, vias 67 unchanged, ratsnest 676→673, journal
  105→108, no new DRC, `router_regression` ALL PASS G1–G30.** **FBV2-P2-019 / D-317 added NO
  copper** — it characterised the XGPIO2+XGPIO3 south-west PAIR as a corridor-capacity wall at the D-269 0.300 mm
  clearance (both orders fail; U3.6 flanked-middle-pin escape box + two parallel 116 mm hauls exceed the corridor;
  the one bounded clr_pad/clr_trk split still NO_FAR_RUN) and proved a **single** west XGPIO net routes clean at
  0.200 mm keeping ≥0.474 mm to BPP — the next path. Fingerprints for all increment probes
  are centralised in `checks/live_fingerprint.py` (D-309). **D-310 gave `connect_cross` existing-via awareness
  (qrouter._scan omits `PCB_VIA`; injected per-route) + a bounded `via_offset`, breaking the U2 escape wall**
  (`qrouter.py` untouched); **D-311/D-312 reused it byte-for-byte to complete the U2 family; D-313 opened the
  XGPIO0..9 bank** with the east-edge pilot XGPIO8+XGPIO9 (no via_offset — clean north escape) at the **D-269
  0.300 mm corridor clearance** (the `BAT_PROTECTED_P` trunk crosses the XGPIO via band); **D-314 opened the WEST
  XGPIO group** with the SOUTH pilot XGPIO1+XGPIO0, routed XGPIO1-first so the southern net self-separates west
  off XGPIO1's laid via (no via_offset, same D-269 0.300 mm clearance, zero router-logic change). Characterised
  walls (do NOT naively retry): `U11_PROG`/`PWR_SENSE` (D-307, hard pad-escape/corridor). **U2 escape family —
  COMPLETE:** `DISP_RST_N` (D-306), `TOUCH_RST_N`/`TOUCH_INT_N` (D-310), `AMP_SD_MODE` U2.7 (D-311),
  `SD_CARD_DETECT_N` U2.11 (D-312). **XGPIO0..9 bank — east pair (D-313) + west SOUTH pair XGPIO0/1 (D-314) done;
  4 west members remain (XGPIO2..7).** **D-315 (FBV2-P2-017) MEASURED that the NORTHERN west members cannot be
  routed as ADJACENT PAIRS:** the XGPIO2+XGPIO3 pair is a corridor-capacity wall at the D-269 0.300 mm clearance
  (U3.6 flanked-middle-pin escape box; two parallel 116 mm hauls exceed the corridor even split clr_pad/clr_trk).
  The "XGPIO-lower-first self-separates" recipe is SOUTH-specific and does NOT transfer north. **The clean path is
  SINGLE-net at the 0.200 mm Default clearance** (measured: XGPIO2 haul→BPP 0.686 mm, XGPIO3 0.474 mm, both
  ≥0.300 — the 0.300 mm blanket is over-conservative here and it is what saturates the corridor). Route the
  remaining west members ONE net at a time; screen each live before routing.
- **Historical Phase-A blocker context (all CLOSED under D-302), updated by D-301.** Direction-2 (D-294) plus the accepted bounded
  levers (D-297 U18.8 In3-join, D-298/D-299 U19CAP, **D-301 LTC_GATE_KO**) have resolved the west/BAT_RAW,
  U18.8, the saturated U19 dead-cell field **and** the `LTC_GATE U18.10→Q3.4` join; **the SINGLE remaining
  Phase-A fabrication blocker is now `U11.2 escape: none exists`** — the `BAT_PROTECTED_P` **1.5 mm
  high-current trunk endpoint** (`u11_escape()`, `route_battery_block.py:2149`, run LAST after the whole
  queue). It lays a dedicated ≥1.20 mm B.Cu trunk from `U11.2`=(66.400,78.200) (EAST node cluster) to
  `D9.1`=(11.350,72.500) (WEST mass) — a **~55 mm cross-board wide trunk**. The BPP backbone is otherwise
  connected (R75.2→bridge→C36.1 node; C58.1→D9.1 TAP; C36/C25/C58/D9.1 already joined via R75.2; U11.2 has
  its 0.20 mm SENSE tie, not a current path). The single ≤~1.30 mm central channel is already occupied by
  the south bridge + R75.2 trunk, so a second parallel 1.50 mm trunk has **NO legal path** — a **structural
  ≥1.20 mm-trunk NO_LEGAL_PATH** (the D-273/274/281/282/283 class), **NOT** a ~20 µm DRC pinch like
  LTC_GATE. It is reducible in principle within CTO scope: U11.2 is IN the east node (already on-net with
  D9.1 via the bridge), so a short on-net ≥1.20 mm tap should replace the cross-board trunk (FBV2-P2-004B,
  §5). Status of the prior walls (all now closed under the full gate):
  - **`LTC_GATE U18.10→Q3.4` — CLOSED under the full gate (D-301), lever committed.** The
    `AQROOT_LTCGATE_KO` path-shaping keep-out forces the join onto the clean F.Cu west detour (8.556 mm),
    a genuine +1 (LOST 0), no new DRC; the real cause was D-269 alone (~19.7 µm), not D-249. ACCEPTED and
    COMMITTED env-gated / OFF-by-default (G15).
  - **U18.8 (`BAT_PROTECTED_P`) — CLOSED IN PRINCIPLE, banked (D-297).** The In3 reserve-JOIN lever
    is an ACCEPTED, board-legal +1 net gain (`U18.8→R75.2` on In3, 4.410 mm, 0 vias, `via_dangling`
    cleared, no new DRC). It is retained OFF-by-default in source and turns ON in the 003X full run;
    it is NOT yet promoted because the full run still fails on U19.
  - **REF_POL R87.2 F-corridor wall — PAST under direction-2** (+2 connections vs 003O); re-verify
    downstream on a full PASS.
  - **U19 dead-cell field — CLOSED under the full gate (D-299), lever committed.** D-296 proved a
    single-pin reservation only SWAPS the casualty; D-298 built the capacity ADD (`AQROOT_U19CAP`:
    reserve the U19.7/U19.6 shared east lane so `LTC4368_FAULT_N` detours + close U19.7 before U19.6);
    the FBV2-P2-003Y full-authority gate confirmed a **genuine +2** (both `REC_BAT_LOW U19.7` and
    `N_BATDIV U19.6` close, LOST 0, board-legal 0.60/0.30 vias, FAULT_N clean, DRC identical). ACCEPTED
    and COMMITTED env-gated / OFF-by-default (G14); re-verify downstream on a full PASS.
  - **`LTC_GATE U18.10→Q3.4` — the terminal blocker (D-299), re-order REFUTED (D-300).** Candidate paths
    DRC-gate-rejected by the frozen D-249 (BPP 1.20 mm trunk width) and D-269 (BAT_MAIN 0.300 mm
    clearance) rules. D-300 (003Z) tested the `AQROOT_LTCGATE` **defer-to-congestion re-order** (route the
    join LAST) under the full gate → **behaviourally identical to D-299** (gained 0 / lost 0, same wall,
    same rejections): a pure re-order is a **null operation** here — `connect_role` re-takes the identical
    central path even queued last, and the focused probe that predicted a west detour was a false-positive
    proxy. The wall stays a **bounded path-shaping** lever within CTO scope: force the proven ~10.5 mm west
    detour by blocking the central lane (FBV2-P2-004A, §5). NOT an owner decision.
  - **BAT_RAW R89.1/R86.2 divider taps** — a capacity symptom, not a width lever; re-verify on a full
    PASS.

## 4. Last accepted milestone
- **Latest milestone — FBV2-P2-004A · Decision:** **D-301** · **Result (a governed ACCEPT + COMMIT +
  overall-run FAIL, no copper):** THE `AQROOT_LTCGATE_KO` PATH-SHAPING LEVER'S FULL-AUTHORITY GATE
  CONFIRMED A **GENUINE +1** (closes `LTC_GATE U18.10→Q3.4`, LOST 0, no new DRC) — so the minimum
  OFF-by-default lever + **G15** are **ACCEPTED and COMMITTED** (byte-identical when unset); COPPER IS NOT
  PROMOTED because full Phase-A still FAILs at the newly-exposed `U11.2` BPP trunk wall (the FIRST run to
  reach the final `u11_escape()` step), so readiness/progress DO NOT MOVE. Gate:
  `AQROOT_U18BPP_JOIN=I3 AQROOT_U19CAP=1 AQROOT_LTCGATE_KO=1 bash w/run_003t_full.sh 004a_ltcgate1 …` →
  `checks/w/phaseA_003t_full_004a_ltcgate1.json` (secs 1500.2, driver exited clean; shared journal restored
  byte-identical to HEAD; no process remains), judged by `w/judge_004a.py`. vs 003Y2: conn 72→73, ratsnest
  705/−76→704/−77, journal 75→76, connected-set diff GAINED 1 (`LTC_GATE Q3.4↔U18.10`, F.Cu, 2× 0.35
  FINE_ESC vias, 8.556 mm) / LOST 0; vs 003W GAINED 3 / LOST 0 (preserves the D-299 U19 pins); DRC
  identical, no sub-0.50 non-fine via. Production WIP pruned to the narrow lever (bulky in-run probe
  removed). A governed CTO ACCEPT + COMMIT + overall-run FAIL, NOT an owner decision; autonomy CONTINUES;
  no copper/placement/rule/floor/topology change, no DRC absorbed, no promotion, D-275 and D-277..D-300
  preserved. Tests: `router_regression.py` ALL PASS incl. **G15** (lever OFF by default → byte-identical;
  `=1` arms the validated default; explicit override parses; scoped to `LTC_GATE U18.10→Q3.4`, KO lifted
  after). Also created: **`docs/full-beta-v2/DEVICE_SPEC.md`**. Evidence of record: audit
  [`audits/2026-08-30-p2-004a-d301-ltcgate-ko-path-shaping-lever-full-gate-plus1-accepted-committed-u11-trunk-wall.md`](audits/2026-08-30-p2-004a-d301-ltcgate-ko-path-shaping-lever-full-gate-plus1-accepted-committed-u11-trunk-wall.md);
  committed source (`checks/route_battery_block.py` `AQROOT_LTCGATE_KO` lever, `checks/router_regression.py`
  G15); gitignored full-gate artifact (`checks/w/phaseA_003t_full_004a_ltcgate1.json`, `w/judge_004a.py`).
- **Prior milestone — FBV2-P2-003Z · Decision:** **D-300** · **Result (a governed FAIL, no copper):**
  THE `AQROOT_LTCGATE` DEFER-TO-CONGESTION LEVER'S FULL-AUTHORITY GATE COMPLETED AND IT IS
  **BEHAVIOURALLY IDENTICAL TO D-299** (GAINED 0 / LOST 0, SAME `LTC_GATE U18.10→Q3.4` TERMINAL WALL,
  SAME D-249 track_width / D-269 clearance REJECTIONS, IDENTICAL FINAL DRC) — SO A PURE RE-ORDER IS A
  **NULL OPERATION** ON THIS WALL: THE LEVER AND ITS **G15** WIP ARE **REJECTED/RETIRED** AND THE
  FALSE-POSITIVE PROBE IS **RETIRED**; COPPER IS NOT PROMOTED, READINESS/PROGRESS UNCHANGED, AUTONOMY
  CONTINUES. The gate `AQROOT_U18BPP_JOIN=I3 AQROOT_U19CAP=1 AQROOT_LTCGATE=1 bash w/run_003t_full.sh
  003z3_ltcgate …` → `checks/w/phaseA_003t_full_003z3_ltcgate.json` (secs 1497.0, driver exited clean;
  shared `phaseA_journal.json` restored byte-identical to HEAD; no process remains), judged by
  `python3 w/judge_003z.py`. vs the 003Y2 baseline (D-299): connections 72=72, skipped 101=101, ratsnest
  705/−76 = 705/−76, journal 75=75, connected-set diff GAINED 0 / LOST 0; the failing rung is the same
  two frozen owner rules (`track_width` D-249 min 1.2000 mm actual 0.2000; `clearance` D-269 0.3000 mm
  actual 0.2803); no sub-0.50 non-fine via. Deferring the join to route LAST changed nothing — the
  driver's `connect_role` greedily re-takes the identical rule-violating central path. The probe
  (`ltcgate_join_probe_003z.py`) predicted a legal ~10.5 mm west detour via post-hoc `connect_role` on
  the SAVED board, but that never reproduces the real in-run state — a D-286 proxy the full gate
  overrode. RETIRED via exact reverse patch scoped to `checks/route_battery_block.py` +
  `checks/router_regression.py` (`git apply -R`; post-revert `git hash-object` = `HEAD:` blob for each;
  `git grep LTCGATE|13z|ltcgate_join_probe` NO match); probe removed; `router_regression.py` ALL PASS
  (G12/G13/G14; G15 gone). Mandated Opportunity & Simplification Scan recorded (§9a): no
  capability/BOM/architecture opportunity; next best lever is path-shaping (force the west detour), the
  bounded neighbour placement ECO is the fallback; **Open owner decisions: NONE.** A governed CTO FAIL,
  NOT an owner decision (no floor relaxed, no frozen part moved, no DRU change, no D-249/D-269
  relaxation); no copper/placement/rule/topology change, no DRC absorbed, no promotion, D-275 and
  D-277..D-299 preserved. Evidence of record: audit
  [`audits/2026-08-30-p2-003z-d300-ltcgate-defer-to-congestion-lever-refuted-false-positive-probe-retired.md`](audits/2026-08-30-p2-003z-d300-ltcgate-defer-to-congestion-lever-refuted-false-positive-probe-retired.md);
  gitignored evidence (`checks/w/phaseA_003t_full_003z3_ltcgate.json`, `w/judge_003z.py`,
  `w/FULL003T_003z*_ltcgate/`, `w/TEST003Z_*/`, `w/run_003z_ltcgate.log`).
- **Last ACCEPTED milestone — Task:** FBV2-P2-003Y · **Decision:** **D-299** · **Result:** THE D-298 U19 CAPACITY LEVER'S
  FULL-AUTHORITY GATE COMPLETED AND IT IS A **GENUINE +2** CONNECTED-SET GAIN (NOT THE D-296 SWAP) — SO
  `AQROOT_U19CAP` IS **ACCEPTED AND COMMITTED** (banked env-gated / OFF-by-default, byte-identical when
  unset, pinned by **G14**); BUT COPPER IS NOT PROMOTED BECAUSE FULL PHASE-A STILL FAILs, THE TERMINAL
  WALL NEWLY ADVANCING PAST THE WHOLE U19 FIELD TO `LTC_GATE U18.10→Q3.4`, SO READINESS/PROGRESS DO NOT
  MOVE. The governing foreground run `AQROOT_U18BPP_JOIN=I3 AQROOT_U19CAP=1 bash w/run_003t_full.sh
  003y2_u19cap …` → `checks/w/phaseA_003t_full_003y2_u19cap.json` (secs 1463.2, driver exited clean;
  shared `phaseA_journal.json` restored byte-identical to HEAD; no process remains), judged by
  `checks/w/judge_003y2.py`. vs the D-297 003W baseline `w/phaseA_003t_full_003w_u18bpp_i3.json` (conn
  70): connections **70→72**, skipped **99→101**, ratsnest **707/−74→705/−76**, journal **73→75**; the
  connected-set diff GAINED **exactly 2** — `N_BATDIV R89.2→U19.6` and `REC_BAT_LOW (node)→U19.7` (both
  SIG, F.Cu, 2 vias, board-legal 0.60/0.30) — and LOST 0 (`U19.7` 15.621 mm, `U19.6` 9.52 mm). Both
  boxed U19 pins close SIMULTANEOUSLY for a strict +2 with nothing lost — the categorical opposite of
  D-296's 1-for-1 swap. `LTC4368_FAULT_N` DETOURS CLEANLY (all three branches on B.Cu; `R82.1→Q9.1`
  77.567 mm; not the terminal wall). Final DRC histogram IDENTICAL to 003W (`{hole_clearance:5,
  lib_footprint_issues:199, solder_mask_bridge:1, track_width:1, unconnected_items:499}`, no new
  class/increase); no sub-0.50 non-fine via (run via diameters 0.35/0.60/0.65/0.80). The new terminal
  wall `LTC_GATE U18.10→Q3.4` is candidate-paths-found-but-DRC-gate-rejected by the frozen D-249 (BPP
  1.20 mm, actual 0.20) and D-269 (BAT_MAIN 0.300 mm, actual 0.2803) rules — a bounded reducible
  corridor/ordering wall within CTO scope. A governed CTO ACCEPT + COMMIT + overall-run FAIL, NOT an
  owner decision (no floor relaxed, no frozen part moved, no DRU change); autonomy CONTINUES; no
  copper/placement/rule/floor/topology change, no DRC absorbed, no promotion, D-275 and D-277..D-298
  preserved. Tests: `router_regression.py` ALL PASS incl. **G14** (lever OFF by default → byte-identical;
  `AQROOT_U19CAP` activates; reserved-lane geometry spans U19.7/U19.6; hooks scoped to the U19 east lane
  + REC_BAT_LOW-before-N_BATDIV). Evidence of record: audit
  [`audits/2026-08-30-p2-003y-d299-u19cap-full-gate-plus2-accepted-committed-ltc-gate-wall.md`](audits/2026-08-30-p2-003y-d299-u19cap-full-gate-plus2-accepted-committed-ltc-gate-wall.md);
  committed source (`checks/route_battery_block.py` `AQROOT_U19CAP` lever, `checks/router_regression.py`
  G14); gitignored full-gate artifact (`checks/w/phaseA_003t_full_003y2_u19cap.json`, `w/judge_003y2.py`).
- **Prior milestone — FBV2-P2-003W · Decision:** **D-297** · **Result:** THE SECONDARY U18.8 I2-JOIN LEVER
  (the D-295/D-296 HANDOFF) COMPLETES `BAT_PROTECTED_P U18.8→R75.2` ON In3 FOR A **GENUINE +1
  CONNECTED-SET GAIN** — A PURE JOIN WITH NO CASUALTY, NO NEW VIA, NO NEW DRC CLASS, AND THE LONE
  `via_dangling` CLEARED — SO IT IS **ACCEPTED** AND RETAINED ENV-GATED / OFF-BY-DEFAULT IN TRACKED
  SOURCE; BUT COPPER IS NOT PROMOTED (THE FULL RUN STILL FAILs ON THE SATURATED U19 FIELD), SO
  READINESS/PROGRESS DO NOT MOVE. The reserve vias are THROUGH vias, so the join is electrically
  identical on In2/In3; In3.Cu is a routable six-layer signal layer (`ROUTABLE[6]=('F','B','I2','I3')`)
  EMPTY across the whole corridor (only In1/In4 GND pours), so `AQROOT_U18BPP_JOIN=I3` completes the
  ONE branch on In3 within D-257/D-266 mechanics. Probe (on the actual full-run routed board): In2
  `NO_PATH`, In3 **ok 4.410 mm**, real KiCad DRC ZERO new classes, `via_dangling` 1→0. Full gate
  (`w/phaseA_003t_full_003w_u18bpp_i3.json`, secs 1272.5) vs the D-294 baseline
  `w/phaseA_003t_full_e15n10cto.json`: connections **69→70**, skipped-already-connected **98→99**,
  ratsnest **708/−73→707/−74**, journal **72→73** (+1 `JOIN U18.8→R75.2` I3 4.410 mm 0 vias),
  `via_dangling` **1→0** with no new DRC class, terminal fatal wall UNCHANGED (`REC_BAT_LOW U19.7`,
  `N_BATDIV U19.6` next). The entire journal delta is EXACTLY one added JOIN with NOTHING lost — the
  opposite of D-296's swap; the In3 join takes capacity from no other net (In3 unused). A governed CTO
  ACCEPT + overall-run FAIL, NOT an owner decision (no floor relaxed, no frozen part moved, direction-2
  not exhausted); autonomy CONTINUES; no copper/placement/rule/floor/topology change, no DRC absorbed,
  no promotion, D-275 and D-277..D-296 preserved. Tests: `router_regression.py` ALL PASS incl. new
  **G13** (In3 routable; lever OFF by default → byte-identical; `=I3` activates; non-I2/I3 never
  activates; override scoped to exactly `BAT_PROTECTED_P U18.8→R75.2`); `u18_i3_join_probe_003w.py`
  ALL PASS. Evidence of record: audit
  [`audits/2026-08-30-p2-003w-d297-secondary-u18bpp-i3-join-lever-net-gain-accepted.md`](audits/2026-08-30-p2-003w-d297-secondary-u18bpp-i3-join-lever-net-gain-accepted.md);
  committed source (`checks/route_battery_block.py`, `checks/router_regression.py` G13,
  `checks/u18_i3_join_probe_003w.py`); gitignored scratch (`checks/w/phaseA_003t_full_003w_u18bpp_i3.json`,
  `w/FULL003T_e15n10cto/`, `w/TEST003W_PROBE/`, `w/run_003t_full.sh`,
  `w/cand_003t/t_a_r77e15n10_r79e15n10.json`).
- **Prior milestone — FBV2-P2-003V · Decision:** **D-296** · **Result:** THE PRIMARY U19.7
  ESCAPE-RESERVATION LEVER (the D-295 handoff) FIRES AND CLOSES U19.7 WITH A BOARD-LEGAL 0.60/0.30
  VIA, BUT IT IS A BOUNDED ORDERING TRADE WITH NO CONNECTED-SET PROGRESS — IT MERELY CHOOSES WHICH PIN
  OF THE SATURATED U19 FIELD IS THE CASUALTY (RESV2 GAINED `REC_BAT_LOW U19.7→Q7.1`, LOST `REF_POL
  TP24.1→U19.2`; conn 69/skip 98/ratsnest 708/−73 all unchanged; DRC identical; wall moves U19.7→U19.6;
  requested-connected 68→68). RESV (0.35/0.20) is behaviourally identical to D-294 (illegal
  sub-minimum via dropped; diff EMPTY both ways). REJECTED for production; the `AQROOT_U19_RESV` source
  WIP RETIRED via exact reverse patch (worktree blob `bba62d35…` = `HEAD:checks/route_battery_block.py`;
  `git grep U19_RESV` no match). Positive finding preserved (mechanism real, U19.7 closable in
  principle, board-legal). A governed FAIL, NOT an owner decision; autonomy CONTINUES; no
  source/copper/placement/rule change, no DRC absorbed, no promotion, D-275 and D-277..D-295 preserved.
  Evidence of record: audit
  [`audits/2026-08-30-p2-003v-d296-primary-reservation-lever-ordering-trade-no-progress-retired.md`](audits/2026-08-30-p2-003v-d296-primary-reservation-lever-ordering-trade-no-progress-retired.md);
  gitignored evidence (`checks/w/phaseA_003t_full_003v_u19resv.json`, `…_u19resv2.json`,
  `w/FULL003T_003v_u19resv*/`, `w/TEST003V_U19RESV/`).
- **Prior milestone — FBV2-P2-003U · Decision:** **D-295** · **Result:** THE TWO D-294 WALLS ARE
  FULL-RUN-EMERGENT ORDERING/CONGESTION CASUALTIES — NO CHEAP VEHICLE JUDGES EITHER AT THE DIRECTION-2
  PLACEMENT — AND THE PRIMARY (`REC_BAT_LOW U19.7`) IS DIAGNOSED EXACTLY AND SHOWN
  REDUCIBLE-IN-PRINCIPLE; THE GOVERNING ~22-min FULL GATE CANNOT RUN FOREGROUND UNDER THE ACP 10-min
  CAP, SO 003U DELIVERS A PRECISE CTO HANDOFF. A governed CTO characterization / NO-PROGRESS + HANDOFF,
  NOT an owner decision; autonomy CONTINUES; no source/copper/placement/rule change, no DRC absorbed,
  no promotion, D-275 and D-277..D-294 preserved. Evidence of record: audit
  [`audits/2026-08-30-p2-003u-d295-two-walls-full-run-emergent-ordering-cheap-vacuous-handoff.md`](audits/2026-08-30-p2-003u-d295-two-walls-full-run-emergent-ordering-cheap-vacuous-handoff.md).
- **Prior milestone — FBV2-P2-003T · Decision:** **D-294** · **Result:** DIRECTION 2 (D-293)
  EXECUTED — A FOCUSED MINIMUM CANDIDATE (`t_a_r77e15n10_r79e15n10`) GENUINELY EXISTS, BUT THE
  GOVERNING FULL AUTHORITY GATE FAILs, SO NO CANDIDATE IS PROMOTABLE. Direction-2 is PRODUCTIVE (+2
  connections vs 003O, `REF_POL R87.2` wall now past) but INCOMPLETE (U18.8 I2 join `NO_PATH`; new
  terminal `REC_BAT_LOW U19.7 NO_LEGAL_ESCAPE`). A governed CTO FAIL, NOT an owner decision; autonomy
  CONTINUES; no promotion, D-275 and D-277..D-293 preserved. Evidence: audit
  [`audits/2026-08-30-p2-003t-d294-direction2-full-gate-fail-u18-corridor-u19-escape.md`](audits/2026-08-30-p2-003t-d294-direction2-full-gate-fail-u18-corridor-u19-escape.md).
- **Prior milestone — FBV2-P2-003S · Decision:** **D-292** · **Result:** THE OWNER-APPROVED BOUNDED
  LTC4368/R75 PLACEMENT MICRO-ECO (D-291) IS SCREENED TO EXHAUSTION — NO BOUNDED U18/R75 PLACEMENT
  LEGALLY CO-CLOSES THE U18 ESCAPE FIELD (a both-edges current-path footprint geometry). A governed
  CTO FAIL that re-raised the OWNER decision (resolved by D-293). Evidence: audit
  [`audits/2026-08-29-p2-003s-d292-u18-r75-placement-microeco-exhausted.md`](audits/2026-08-29-p2-003s-d292-u18-r75-placement-microeco-exhausted.md).
- **Prior milestones — D-290/D-289/D-288/D-287/D-286** (full detail in CTO_DECISIONS and the audits):
  D-290 the last routing-only U18 co-closure lever refuted (owner decision, resolved by D-293);
  D-289 the 003P WIP retired and U18 co-closure refuted; D-288 the D-275 south-bridge entry-array
  two-layer tie fixed (`via_dangling`-clean, electrical pass); D-287 direction-1 space exhausted
  (27/27); D-286 the gate baseline measured on the actual complete pre-copper placement (regression
  G12).

## 5. Next task — FBV2-P2-025 (route the next clean rest-of-board increment in an OPEN region; continue avoiding the saturated west-XGPIO F.Cu corridor)

- **Where 025 left it (D-323 — PROMOTED, eighteenth increment).** EIGHTEEN increments promoted; **138 of 164
  rest nets unrouted**; authoritative `sha256 a7bf8bdc…c57f9f626` (781 trk / 68 via / 6 layers / 41 zones /
  ratsnest 665 / journal 116). FBV2-P2-025 ran the evidence-first read-only screen (`w/screen_020.py`) of the
  remaining unrouted rest nets, then a focused geometry vet (`w/vet_021.py`, re-verified live) of the
  genuinely-functional shortlist (`ACC_DETECT_N` cong 103 / straight-MST 2.750 mm from BPP, `DISP_BL_CTL_STRAP`
  cong 185, `BTN_B_N` cong 141). **The cleaner-class candidates were tested FIRST.** `DISP_BL_CTL_STRAP` (the
  display backlight-control strap `U1.16` MCU / `TP2.1` / `R108.1`+`R109.1`, isolated by R109 from the
  downstream `DISP_BL_CTL`→`U17.4` driver) returned `NO_PATH` at 0.200 mm on **ALL THREE** MST edges
  (5.44 + 10.30 + 24.77 mm; none even at the 0.05/0.025 mm fine grid) — the dense MCU/backlight pad pocket
  (cong 185; vet nearest-copper 0.022 mm to the accepted D-318 `BMI270_INT1_STRAP`) boxes every terminal (the
  `MCU_EN_RC` boxed-pocket lesson repeated); `GROUPS['DISP_BL_CTL_STRAP']` annotated (do NOT retry at 0.200 mm).
  `BTN_B_N` (nav/boot button `SW7.1` → `R9.2` → `U2.18`) routed ALL OK but **failed the gate on connectivity** —
  SW7 is a 4-pin tactile switch whose two mechanically-linked terminals BOTH carry pad "1" on `BTN_B_N` at
  (49.520,96.750) and (57.480,96.750), 7.96 mm apart, and the per-ref MST (`pads_by_ref`) collapses them to one
  node → the second terminal is never driven → one permanent open ratsnest edge (open_edges 2→1); a connectivity
  gap of the WHOLE duplicate-ref button family (deferred "duplicate-ref MST" framework task), NOT a copper
  casualty — the authoritative board was never touched. **SELECTED** the genuine functional 3-distinct-ref
  detect `ACC_DETECT_N` (`R64.1` divider F.Cu / `R129.2` series B.Cu / `U3.17` expander GPIO B.Cu, a cross-layer
  net = ONE 0.60/0.30 through via `R64.1↔R129.2` + ONE same-layer B.Cu run `R129.2↔U3.17`), in an OPEN region
  whose realized copper clears `BAT_PROTECTED_P` by **3.8831 mm** (zero D-269 involvement); the via lands in the
  open north @(57.900,38.800), 34.157 mm from every barrel. Gate PASS every check; `router_regression` ALL PASS
  G1–G35; `incremental_probe_023.py`+`G35` added; the no-via probes `_018..022` + `_023` generalized their
  board-total via pin to `EXPECT_VIAS` (per-net `i_via` contract kept — first new via since D-316);
  `live_fingerprint.py` bumped once. `MCU_EN_RC`, the J1 display-connector haul (`DISP_CS_N`/`DISP_DC`), the
  `DISP_BL_CTL_STRAP` boxed pocket, and the `SWx` duplicate-ref button family are characterized — do NOT naively
  retry; `BOOT_N` set aside (sensitive, poor path).
- **(superseded D-322 note) FBV2-P2-024 promoted `RESERVED_SPARE`; `BOOT_N` (the meaningful non-J1 alternative, ESP32
  boot-mode strap) routed ALL OK but only via poor 2.5× detours (~110 mm of meandering copper for a boot-critical
  strap) — not equally clean, set aside (sensitivity treated carefully). It then PROMOTED the held clean alternate
  `RESERVED_SPARE` — the reserved/spare community expander GPIO (R130.2 / TP41.1 test point / U23.7 PCAL
  expander), a 3-pad ALL-B.Cu SAME-LAYER MST with **NO via** (the cleanest class), in an OPEN region **15.5 mm
  clear of `BAT_PROTECTED_P`** (zero D-269 involvement). Gate PASS every check; `router_regression` ALL PASS
  G1–G34; `incremental_probe_022.py`+`G34` added; `live_fingerprint.py` bumped once. `MCU_EN_RC` (`Net-(U1-EN)`)
  and the J1 display-connector haul (`DISP_CS_N`/`DISP_DC`) are characterized walls — do NOT naively retry;
  `BOOT_N` set aside (sensitive, poor path).
- **The lever (FBV2-P2-026) — route the next clean rest-of-board increment in an OPEN, UNCONGESTED region**
  (a single net or small coherent local group). Re-run / extend the evidence-first live screen (`w/screen_020.py`
  is the reusable read-only inventory + category screen; its auto-classifier is a FIRST pass only — several
  auto-ALLOW nets are actually converter-switching — `Net-(L1-Pad1/2)`, `Net-(U13-SW/FB)`, `Net-(U12-*)`,
  `BL_SW`, the 16-pad power net `BQ25185_SYS` — or USB-C connector — `Net-(J3-CC1/CC2/SHIELD)` — nets, and must
  be vetted on measured geometry before selection; `w/vet_021.py` is the reusable read-only geometry vet:
  netclass, MST edges, straight-path nearest-other copper, and `BAT_PROTECTED_P`/D-269 proximity). Prefer a
  spatially coherent local low-speed control/peripheral group or one high-information singleton with a materially
  distinct clean primitive (remaining buttons/expander controls, IMU/I2C-local controls, IR-receiver-side
  low-current controls, or other local noncritical nets). Register the selected 1–6-net GROUP in
  `incremental_router.py` at its netclass Default (reuse the proven same-layer / MST / mixed-layer / via
  mechanics; extend only if forced by measured evidence), `route`→`gate`→`promote` under the D-286 real
  full-board gate. On promote add `incremental_probe_024.py` + a `G36` contract (net(s) connected, copper legal,
  all vias clear every barrel, applicable D-269/BPP kept by real DRC, ADD-ONLY) and bump `live_fingerprint.py`
  once. **Do NOT** retry the `MCU_EN_RC` (`Net-(U1-EN)`) characterized wall, the J1 display-connector haul
  (`DISP_CS_N`/`DISP_DC`) characterized wall, the `DISP_BL_CTL_STRAP` boxed-pocket wall (all 3 MST edges
  `NO_PATH` at 0.200 mm), the `SWx` duplicate-ref button family (`BTN_B_N` etc. — `pads_by_ref` MST collapses
  the duplicate pad-"1" terminals; needs a duplicate-ref MST framework task first), single west XGPIO F.Cu hauls
  (`XGPIO2`/`XGPIO4`/`XGPIO5`/`XGPIO6`/`XGPIO7` — corridor-capacity walled as second hauls), the `XGPIO2`+`XGPIO3`
  PAIR (D-315 wall), or `U11_PROG`/`PWR_SENSE` (hard walls); avoid RF/NFC matching/antennas, USB, crystals/clocks,
  switching/high-current/class-D outputs (incl. the IR-emitter power/Q1 switch node `IR_LED_A`/`IR_LED_K`), bulk
  rails, and community-header mass routing, and the auto-ALLOW converter-switching/USB-C connector traps above.
  Hold the **inner-layer (In2/In3) west-XGPIO haul** as the concretely-justified deferred **framework** task (out
  of scope for a single-net increment). Promote **only a genuine no-casualty / no-new-DRC increment** (the gate
  enforces this). All floors ENFORCED; no DRU/rule relaxation, no D-290 reauth, no topology/footprint/outline
  change. If no candidate promotes, commit the exact characterization and define FBV2-P2-026.
- **(historical) Next task as of FBV2-P2-007 (continue rest-of-board routing, next bounded group)**
- **Where 006 left it (D-304).** The reusable incremental router/promoter `checks/incremental_router.py`
  EXISTS and is proven: it loaded the D-302 promoted board, routed the FRONT_RGB indicator group (3 nets, 20
  B.Cu tracks, no via) with a real full-board gate (Phase-A copper preserved exactly, 0 casualty, ratsnest
  704→701, DRC unchanged), and PROMOTED it (authoritative `sha256 00c93bdb…`; 452 trk / 54 via; journal 80).
  **161 of the 164 rest-of-board nets remain unrouted.**
- **The lever (FBV2-P2-007).** Pick the next sharply-bounded group from measured geometry
  (`w/measure_rest_006.py` ranks candidates), add it to the `GROUPS` registry in `incremental_router.py`, then
  `route` → `gate` → `promote`. Good next candidates: the remaining short, isolated 08_BUTTONS_EXPANDERS /
  01_POWER_TREE-local / 05_I2C control pairs, then short bus segments; **defer** the RF/NFC radios, USB,
  community-header mass and GND/+3V3 bulk rails until the framework has more mileage. Promote **only a genuine
  no-casualty / no-new-DRC increment** (the gate enforces this). All floors ENFORCED (D-249 ≥1.20 mm BPP,
  D-269 0.300 mm, D-257 via ladder, 0.60 mm BAT_MAIN, 0.200/0.150 signal, 0.25 hole-hole, D-275/D-288 bridge);
  no DRU/rule relaxation, no D-290 reauth, no topology/footprint/outline change. Add a G-contract per accepted
  group (G18 is the FRONT_RGB template).
- **Superseded (kept for context) — FBV2-P2-004B (the `U11.2` BPP trunk-endpoint retarget lever), CLOSED by
  D-302.** `LTC_GATE U18.10→Q3.4` is CLOSED (accepted `AQROOT_LTCGATE_KO`
  lever). The full run is the FIRST to reach the final `u11_escape()` step, and the single terminal
  Phase-A wall is now **`U11.2 escape: none exists`**. Copper is still NOT promoted.
- **Root cause (measured, `checks/w/phaseA_003t_full_004a_ltcgate1.json` + `w/run_004a_full.log`,
  no new long route).** `u11_escape()` (`route_battery_block.py:2149`) lays the U11.2 end of the
  `BAT_PROTECTED_P` high-current trunk LAST: escape `D9.1` at `W_TRUNK_BPP=1.50 mm`, flare `U11.2`
  (1.50→0.20 mm SENSE neck), `connect_role(launch→D9.1)` at 1.50/1.20 mm, `gate()`. Geometry:
  `U11.2`=(66.400,78.200) in the EAST `BAT_PROTECTED_P` node cluster; `D9.1`=(11.350,72.500) in the WEST
  mass — a **~55 mm cross-board ≥1.20 mm B.Cu trunk**. The BPP backbone is otherwise connected
  (R75.2→(stage) TRUNK 14.458 mm F.Cu; EARLY SOUTH BRIDGE land C36.1 70.925 mm; C58.1→D9.1 TAP 5.092 mm;
  C36/C25/C58/D9.1 "already joined via R75.2"); U11.2 already has its 0.20 mm SENSE tie (5.525 mm, not a
  current path). The single ≤~1.30 mm central channel is already occupied by the south bridge + R75.2
  trunk, so a second parallel 1.50 mm trunk has **NO legal path** — a **structural ≥1.20 mm-trunk
  NO_LEGAL_PATH** (the D-273/274/281/282/283 class), NOT a ~20 µm DRC pinch.
- **The lever (build ONE, env-gated OFF-by-default) — RETARGET, NOT a cross-board trunk.** U11.2 is IN
  the east node, already on-net with D9.1 via the bridge/R75.2 backbone, so close the U11.2 trunk
  endpoint as a **SHORT wide tap into the nearest already-connected ≥1.20 mm BPP node copper** (candidate:
  `C36.1`=(63.75,73.75), ~2.9 mm east, or the bridge landing) instead of the distant `D9.1`. Keep
  `AQROOT_U18BPP_JOIN=I3`, `AQROOT_U19CAP=1`, `AQROOT_LTCGATE_KO=1` **ON** (all accepted). The tap must
  remain a legal **≥1.20 mm** current path (D-249/D-269/0.60 mm BAT_MAIN ENFORCED — no width waiver; this
  is a high-current safety-relevant net), and 004B must **verify the retarget preserves a valid
  high-current path** (U11 load current still reaches the bulk-cap/protection output at ≥1.20 mm; a short
  tap that leaves U11 fed only through the thin cap-via tie would be a functional regression, not a gain).
  **Fallback** (only if no legal on-net tap sites the ≥1.20 mm path): a bounded immediate-neighbour
  placement ECO to open a ≥1.20 mm `U11.2` corridor, re-screened with real full-placement DRC (D-286).
  If the ≥1.20 mm trunk truly cannot be closed within CTO-scope routing/tap/bounded-ECO (the
  D-281/282/283 western-corridor wall genuinely re-surfacing as unsolvable without a topology/mechanical
  change), that would re-raise an OWNER decision — but 004B must first exhaust the bounded retarget.
- **The governing run (CTO, persistent terminal, ~25 min):**
  `cd hardware/beta-v2/checks && cp phaseA_journal.json /tmp/phaseA_journal.HEAD.json &&
  AQROOT_U18BPP_JOIN=I3 AQROOT_U19CAP=1 AQROOT_LTCGATE_KO=1 <u11-retarget env> bash w/run_003t_full.sh
  004b_u11 w/cand_003t/t_a_r77e15n10_r79e15n10.json && cp /tmp/phaseA_journal.HEAD.json phaseA_journal.json`.
  **Judge by the full-run connected-set diff** vs `w/phaseA_003t_full_004a_ltcgate1.json`: the run must
  close the `U11.2` trunk endpoint for a real net gain with no new DRC class and no lost connection, and
  preserve the high-current path. **Do not trust a focused/post-hoc probe** (the D-300 lesson).
  **Promote copper only on a genuine full-authority Phase-A PASS** (D-286). All floors ENFORCED; D-290
  stays closed.
- **Downstream, still CTO-scope:** on a full PASS, re-verify the (now-past) `REF_POL R87.2` F-corridor
  and the BAT_RAW R89.1/R86.2 divider taps.

## 6. Authoritative PCB state
- **Routing/promotion (D-322): Phase-A copper + SEVENTEEN rest-of-board increments.** Authoritative board =
  **six copper layers, 759 signal tracks, 67 vias, 41 zones** (verified `sha256 a861e30e5760515288ef9a3fc0c21ea6d3e9c31409f9181dd66d56ed0628efd1`),
  carrying the **432-track Phase-A battery block (D-302) PLUS** FRONT_RGB 20 (D-304) + ACC 31 (D-305) + DISP 11/1
  via (D-306) + IMU_ADDR 8 (D-307) + FRONT_RGB_LED 25/3 via (D-308) + IR_RX_VS 8 (D-309) + TOUCH_CTL 26/2 via
  (D-310) + AMP_SD_MODE 19/1 via (D-311) + SD_CARD_DETECT_N 28/1 via (D-312) + XGPIO8/XGPIO9 23/2 via (D-313) +
  XGPIO1/XGPIO0 38/2 via (D-314) + XGPIO3 22/1 via (D-316) + BMI270_INT1_STRAP 18/0 via (D-318) +
  UART0_TXD_DBG 7/0 via (D-319) + IR_TX_GPIO16 13/0 via (D-320) + SD_CS_N 20/0 via (D-321) +
  **RESERVED_SPARE 10/0 via (D-322)**; ratsnest
  **667**; journal **114** (77 Phase-A + 37 `REST_INC`); real KiCad DRC unchanged
  (`{solder_mask_bridge:1, hole_clearance:5, lib_footprint_issues:199, unconnected_items:499}`);
  **139 rest-of-board nets remain unrouted.** `router_regression.py` ALL PASS (G1–G34). Rollback: pre-D-322
  `sha256 68d44b54…6d25e46` (committed D-321, parent `e3e2a8d`).
- **(historical) Routing/promotion (D-313): Phase-A copper + TEN rest-of-board increments.** Authoritative board =
  **six copper layers, 631 signal tracks, 64 vias, 41 zones** (verified `sha256 a0d6fead…e7207eb`), carrying the
  **432-track Phase-A battery block (D-302) PLUS** FRONT_RGB 20 (D-304) + ACC 31 (D-305) + DISP 11/1 via (D-306)
  + IMU 8 (D-307) + FRONT_RGB_LED 25/3 via (D-308) + IR_RX_VS 8 (D-309) + TOUCH_CTL 26/2 via (D-310) + AMP_SD_MODE
  19/1 via (D-311) + SD_CARD_DETECT_N 28/1 via (D-312) + XGPIO8/XGPIO9 23/2 via (D-313); ratsnest **679**; journal
  **102** (77 Phase-A + 25 `REST_INC`); real KiCad DRC unchanged
  (`{solder_mask_bridge:1, hole_clearance:5, lib_footprint_issues:199, unconnected_items:499}`); **147
  rest-of-board nets remain unrouted.** `router_regression.py` ALL PASS (G1–G27). Rollback: pre-D-313
  `sha256 d6e0148a…aabc5f1b8` (D-312; parent `1eb80a9`).
- **(historical) Routing/promotion (D-304): Phase-A copper + first rest-of-board increment.** Authoritative board =
  **six copper layers, 452 signal tracks, 54 vias, 41 zones** (verified `sha256 00c93bdb…dfb72aad`), carrying
  the **432-track Phase-A battery block (D-302) PLUS the 20-track FRONT_RGB indicator increment (D-304)**;
  ratsnest **701**; journal **80** (77 Phase-A + 3 `REST_INC`); real KiCad DRC unchanged
  (`{solder_mask_bridge:1, hole_clearance:5, lib_footprint_issues:199, unconnected_items:499}`); 161 rest-of-
  board nets remain unrouted. `router_regression.py` ALL 82 PASS (G1–G18). Rollback: pre-D-304
  `sha256 63a9bc54…f87d6ba9` (D-302; parent `50149f4`).
- **(historical) Routing/promotion (D-302): FIRST AUTHORITATIVE COPPER PROMOTED.** Authoritative board = **six copper
  layers, 432 signal tracks, 54 vias, 41 zones** (verified `sha256 63a9bc54…f87d6ba9`, size 1475931), carrying
  **Phase-A battery-block copper ONLY** (all 432 tracks in-scope power-tree; 0 out-of-scope); direction-2
  placement (fingerprint `397dffe1f77e4d10`; U18 moved to (8.0,66.5,180°), C36.1 at (63.750,74.325)); 77-entry
  `phaseA_journal.json`; regenerated 119-rule DRU (the accepted D-249/D-257/D-258/D-263/D-264/D-266/D-269
  per-net set, NOT a relaxation). Real KiCad DRC `{hole_clearance:5, lib_footprint_issues:199,
  solder_mask_bridge:1, unconnected_items:499}` — zero new copper classes. **Rest of board (164 multi-pad
  nets, 9 sheets + rails) UNROUTED** (ratsnest 704 / unconnected 499). **Rollback:** pre-promotion PCB
  `sha256 2235e273…d642d7e` (parent `56d0ebe`, tag `beta-v2-p2-pre-copper-authoritative`).
- **(historical) prior authoritative PCB state before D-302** = six copper layers, 0 signal tracks, 0 signal
  vias (`sha256 2235e273…d642d7e`, byte-identical to the pre-promotion HEAD). All 003O/003T/003W bridge/
  full-run copper lived only in gitignored scratch (`checks/w/`) and override files; the natural-run
  003O result `checks/phaseA_003o_b1_r75rot_cto.json` is committed as evidence of record, and the
  003T/003W full-authority results stay gitignored under scratch
  (`checks/w/phaseA_003t_full_e15n10cto.json`, `…003w_u18bpp_i3.json`, `FULL003T_e15n10cto/`).
- **Banked in source (D-297), NOT in copper:** the OFF-by-default `AQROOT_U18BPP_JOIN` In3-join lever
  (byte-identical when unset) closes `U18.8→R75.2` for a proven +1 gain when ON; it awaits the U19
  field closure and a full Phase-A PASS before any copper is promoted.
- **Banked in source (D-299), NOT in copper:** the OFF-by-default `AQROOT_U19CAP` U19 east-lane
  reservation + U19.7-first lever (byte-identical when unset), pinned by regression **G14** and now
  **gate-validated as a genuine +2** (FBV2-P2-003Y: closes `REC_BAT_LOW U19.7` + `N_BATDIV U19.6`, LOST
  0, board-legal 0.60/0.30 vias, FAULT_N clean, DRC identical). Source (`checks/route_battery_block.py`,
  `checks/router_regression.py`) is **COMMITTED**; it awaits the `LTC_GATE` closure and a full Phase-A
  PASS before any copper is promoted. Full-gate artifact (gitignored):
  `checks/w/phaseA_003t_full_003y2_u19cap.json`, judged by `checks/w/judge_003y2.py`.
- `phaseA_journal.json` at its committed HEAD state (driver never authoritatively invoked; the shared
  journal was backed up and restored around the full run; scratch churn discarded).
- PCB routing **0 %**; overall repo progress **74 %**.

## 7. Locked invariants (reference the D-xxx rulings, not the history)
- **D-275** forced-south `BAT_PROTECTED_P` bridge geometry (lane + landing proven). **D-288** the
  entry-array two-layer tie is FIXED (rotation-aware in-pad `scan_entry_sites` + symmetric B.Cu
  tie-stub, `via_dangling`-clean; an electrical pass, not merely geometric). The **0.60 mm BAT_MAIN
  minimum width** rule is a hard floor.
- **D-277..D-280** U19/deadcell escape + C61 landing-guard gains.
- **D-281/282/283** western-corridor route-scope fixes exhausted; **D-284 (OWNER)** approved
  landing-opening direction 1; **D-285** `place_003l` opens the C36.1 landing (clean).
- **D-286** the gate baseline is measured on the actual complete pre-copper placement; candidate
  placements must be screened with real full-placement DRC; a genuine placement short must be
  surfaced, never absorbed. **No proxy (focused vehicle / partial run) promotes copper — only a
  genuine full-authority Phase-A PASS does.** Regression G12 pins the corrected baseline order.
- **D-287** the bounded direction-1 placement space is EXHAUSTED (27/27); a `via_dangling` item is a
  genuine electrical fault and MUST fail.
- **D-289/D-290** the residual U18.8 `BAT_PROTECTED_P` escape is a **placement-geometry
  mutual-exclusion** at the 0.5 mm pad pitch vs the 0.300 mm current-path floor (D-269); the
  routing-only co-closure space (off-layer vacate of U18.7) is REFUTED — no routing-only site
  remains, so the U18.8 escape was an OWNER decision, **RESOLVED by D-293 (direction 2 authorized).**
- **D-293 (OWNER)** authorized **direction 2** — bounded LTC4368-block spread / escape-target
  relocation (R77/R79 east, R80/R81 north) so `BAT_RAW` (U18.1 east) and `BAT_PROTECTED_P` (U18.8
  west) escape through independent corridors — without relaxing D-269 or any floor, without accepting
  U18.8 open, without re-litigating D-290.
- **D-294 (003T)** direction 2 was EXECUTED under full CTO authority: a focused minimum candidate
  exists but the full gate FAILs, so no candidate is promotable. Direction-2 is PRODUCTIVE (+2 vs
  003O, `REF_POL R87.2` now past) but INCOMPLETE. **A focused `fail=None` is VACUOUS vs the congested
  full run — judge Phase-A changes by the full-run connected-set diff, promote copper only on
  full-authority evidence.**
- **D-295 (003U)** the two D-294 walls are full-run-emergent ordering/congestion casualties and no
  cheap vehicle judges either at the direction-2 placement; the PRIMARY (`REC_BAT_LOW U19.7`) is
  reducible-in-principle (direction-2's +2-connection congestion swapped `VREC_VCC U19.8`'s pad-escape
  from B.Cu onto the F lane U19.7 needs); both bounded levers are judgeable only by the ~22-min full
  gate. The U19.7 wall is an ordering class, NOT a D-289/290/292 placement mutual-exclusion.
- **D-296 (003V)** the PRIMARY U19.7 escape-reservation family is **REFUTED**: with a board-legal
  0.60/0.30 via the reservation fires and closes U19.7, but the U19 dead-cell field is
  **capacity-saturated on F.Cu/B.Cu**, so a single-pin reservation is a bounded **ordering trade** —
  it swaps the casualty (U19.7 ⇄ U19.2, wall U19.7→U19.6), earning NO net connected-set progress. Do
  NOT re-try single-pin U19 reservation; the U19 field needs a lever that ENLARGES capacity, not one
  that re-orders it.
- **D-297 (003W)** the SECONDARY U18.8 I2-join is closed by a **capacity add, not an ordering trade**:
  the reserve vias are THROUGH vias, In3.Cu is a routable six-layer signal layer that is bare across
  this corridor, so completing `U18.8→R75.2` on In3 (`AQROOT_U18BPP_JOIN=I3`) is a **genuine +1
  connected-set gain with no casualty, no new via, no new DRC class, and clears `via_dangling`** —
  because it takes capacity from no other net. **ACCEPTED and banked env-gated/OFF-by-default in
  source; copper is NOT promoted while the full run still FAILs on the U19 field.** The general lesson:
  the bare inner signal layers In2/In3 are unused capacity in this corridor and are the correct
  vehicle for enlarging a saturated F.Cu/B.Cu field (the U19 direction for 003X).
- **D-298 (003X)** the U19 field is closable by a **capacity ADD, not a swap**: U19.6/U19.7 (BOTTOM
  SOT-23-8) are pad-boxed N/S; their shared EAST lane is walled by the same `LTC4368_FAULT_N`
  cross-board run; POFV is DRU-barred (U19.6/U19.7 lack the D-257 fine-via exception the other three
  U19 pins have), so the escape needs a clear lateral lane + the legal 0.65/0.40 via. The
  `AQROOT_U19CAP` lever **reserves the shared east lane** (FAULT_N detours) and **closes U19.7 before
  U19.6** — both then escape, screened DRC-clean. IMPLEMENTED, regression-pinned (G14), OFF-by-default.
  Categorically distinct from the refuted D-296 single-pin lateral swap.
- **D-299 (003Y)** the D-298 lever's **full-authority gate CONFIRMED a genuine +2** (both `REC_BAT_LOW
  U19.7` and `N_BATDIV U19.6` close, LOST 0, board-legal 0.60/0.30 vias, `LTC4368_FAULT_N` detours
  clean, DRC identical) — so `AQROOT_U19CAP` is **ACCEPTED and COMMITTED** (banked OFF-by-default).
  **Copper NOT promoted** (D-286): full Phase-A still FAILs, the terminal wall newly advancing past the
  whole U19 field to **`LTC_GATE U18.10→Q3.4`** — candidate join paths found but **DRC-gate-rejected**
  by the frozen **D-249** (BPP 1.20 mm trunk, actual 0.20) and **D-269** (BAT_MAIN 0.300 mm clearance,
  actual 0.2803) rules; a bounded reducible corridor wall, NOT `NO_PATH`.
- **D-300 (003Z)** the `LTC_GATE U18.10→Q3.4` **defer-to-congestion re-order** (`AQROOT_LTCGATE`: pull
  the join out of section 8b, re-queue it LAST) is **REFUTED** — the full gate is behaviourally
  identical to D-299 (gained 0 / lost 0, same wall, same D-249/D-269 rejections, identical DRC): **a
  pure re-order is a NULL OPERATION** on this wall because the driver's `connect_role` greedily
  re-takes the identical rule-violating central path even when queued last. Do NOT re-try ordering on
  this wall. The focused `ltcgate_join_probe_003z.py` was a **false-positive proxy** — its post-hoc
  `connect_role` on the SAVED board found a ~10.5 mm west detour the real in-run driver never takes; per
  D-286 a post-hoc/focused proxy cannot override the full gate. The correct lever is **path-shaping**
  (physically block the central lane to force the detour), not ordering (FBV2-P2-004A, §5). The lever +
  its G15 WIP were retired via exact reverse patch; the probe was retired.
- Rule floors ENFORCED: **0.200 mm** clearance, **0.25 mm** hole-to-hole, **0.300 mm** current-path
  routed clearance (D-269), **≥1.20 mm** BPP trunk width (D-249), **0.60 mm** BAT_MAIN minimum width.
  Six-layer stack, GND, netclasses, footprints, polarity, safety set — all frozen. Frozen
  `beta-full-reference-v1` untouched.

## 8. Open owner decisions
- **NONE. D-293 resolved the last owner decision (direction 2 authorized); D-294..D-301 each re-raised
  none.** Direction 2 is being executed under full CTO authority; the U18.8 wall is closed in principle
  by the accepted D-297 In3-join lever, the U19 field by the committed D-299 U19CAP lever, and the
  `LTC_GATE U18.10→Q3.4` join by the committed D-301 LTCGATE_KO lever (all banked OFF-by-default in
  source). The sole remaining Phase-A blocker — `U11.2 escape: none exists` (the BPP 1.5 mm high-current
  trunk endpoint) — is **bounded CTO-scope routing work (a trunk-endpoint retarget), not an owner
  decision** (no floor relaxed, no frozen part moved, no DRU change, no D-249/D-269 relaxation); the D-301
  mandated Opportunity & Simplification Scan (§9a) found **no** irreversible opportunity loss or strategic
  fork. Autonomy CONTINUES with **FBV2-P2-004B** (§5). Only if the ≥1.20 mm BPP trunk truly cannot be
  closed within CTO-scope routing/tap/bounded-ECO would an OWNER decision re-surface; 004B must first
  exhaust the bounded retarget. Historical options (B accept-U18.8-open, D re-litigate-D-290) are retained
  only as context and are not active.
- **Nothing has been changed under any decision:** no part moved, no floor relaxed, no DRC absorbed
  into the authoritative board; the authoritative PCB is six layers / 0 tracks / 0 vias.

## 9a. Opportunity & Simplification Scan (D-301, LTC_GATE close / BPP trunk milestone)
- **Mandated bounded scan** at this milestone, grounded in the accepted `AQROOT_LTCGATE_KO` lever and the
  newly-exposed `U11.2` BPP trunk wall (U11.2=(66.400,78.200) EAST node; D9.1=(11.350,72.500) WEST; the
  `u11_escape()` cross-board 1.50 mm trunk has no legal corridor on the saturated western margin).
- **Path-shaping (accepted, cheapest lever).** The `AQROOT_LTCGATE_KO` central-lane keep-out closes the
  LTC_GATE join with **zero BOM/placement/rule impact**, OFF-by-default, byte-identical when unset; the
  probe was pruned (complexity removed). Cheapest, reversible.
- **U11.2 retarget (recommended next lever, 004B).** U11.2 is IN the east node, already on-net with D9.1
  via the bridge, so a **short on-net ≥1.20 mm tap** (e.g. into C36.1) beats the obvious cross-board
  trunk. Reversible, env-gated OFF-by-default. High-current safety-relevant net → must preserve the
  ≥1.20 mm path (no width waiver).
- **Bounded local placement ECO — the fallback** if no legal on-net tap sites the ≥1.20 mm path;
  re-screened with real full-placement DRC (D-286). Larger blast radius, second choice.
- **BOM.** No opportunity — the wall is a routing pinch, not a component gap; the LTC4368 + Q2/Q3
  back-to-back-FET reverse-protection topology is frozen and correct. **No cost lever.**
- **Recoverability (D-049) / testability / manufacturing / firmware / UX.** The accepted lever is a
  low-current internal control-net join with no footprint/outline/stackup/silk/firmware surface. The
  U11.2 trunk is high-current safety-relevant, so 004B must not waive the ≥1.20 mm width.
- **Future option (preserved).** The six-layer stack's bare inner signal layers In2/In3 remain spare
  capacity (the D-297 lesson) — a preserved vehicle if the U11.2 tap corridor proves congested. Nothing
  is foreclosed.
- **Cost classification / conclusion.** No product-capability or BOM opportunity justifies changing
  architecture; no irreversible cost, no strategic fork, no opportunity loss. **Open owner decisions:
  NONE.** The deferred opportunity is only the *technical* 004B lever above, pursued under CTO autonomy.

## 9. JLCPCB readiness
- **JLCPCB readiness ~78 %** (authoritative governance figure; unchanged by D-323 — the rest-of-board
  increments add real authoritative copper but the fabrication package/Gerbers are not yet regenerated, so
  the JLCPCB file itself is unchanged; readiness is not moved absent that evidence).
  `/home/aqroot8/.aqroot-progress.env` unchanged (CTO owns readiness).
- **Repo progress 74 %** (governed value in PROGRESS.md).
- **What remains before fabrication:** close the `U11.2` BPP trunk endpoint (a short on-net ≥1.20 mm tap)
  and complete a full Phase-A PASS at the direction-2 placement (with the accepted D-297/D-299/D-301
  levers ON); promote the authoritative copper; then Phase-B production routing; full DRC/ERC/connectivity
  and
  regression closure on the authoritative board; RF/power/thermal/safety validation; BOM/footprint/
  polarity/DNP + assembly review; board-outline/stackup/fab-rule review; Gerber/drill/BOM/CPL
  generation and independent manufacturing-package review.

## 10. Active orchestration
- **Persistent CTO session:** `agent:main:aqroot-fbv2-cto` — sole owner of Claude engineering
  launches; receives every completion event.
- **Autopilot:** cron/systemd may only WAKE the persistent CTO; it must never launch Claude or become
  a task parent. No owner decision is open; the stop file is ABSENT and the persistent CTO continues
  one-Claude-at-a-time engineering.
- **Should an engineering process be active now?** **Yes.** FBV2-P2-004B implements ONE bounded,
  env-gated (OFF-by-default) `U11.2` **BPP trunk-endpoint retarget** lever (close the U11.2 trunk end as a
  short on-net ≥1.20 mm tap into the nearest already-connected BPP node copper — e.g. C36.1 — instead of
  the cross-board `u11_escape()` run to D9.1; no width waiver, high-current safety-relevant net), validate
  it against `router_regression.py` (authoritative byte-identical), then run the FULL authority gate
  (`AQROOT_U18BPP_JOIN=I3 AQROOT_U19CAP=1 AQROOT_LTCGATE_KO=1 <u11-retarget-lever> bash w/run_003t_full.sh
  004b_u11 w/cand_003t/t_a_r77e15n10_r79e15n10.json`, ~25 min, in a persistent terminal) and judge by the
  full-run connected-set diff vs `w/phaseA_003t_full_004a_ltcgate1.json` (never a focused/post-hoc probe
  — the D-300 lesson), verifying the retarget preserves a valid high-current path. The bounded neighbour
  placement ECO (re-screened full-placement DRC) is the fallback. Promote copper only on a genuine full
  Phase-A PASS.
- **DEVICE_SPEC gate:** before any render / website / Kickstarter / enclosure brief / external-mechanical
  / product-description claim, consult `docs/full-beta-v2/DEVICE_SPEC.md` and claim only MARKETING-SAFE rows.

## 11. Recovery instructions (a fresh CTO/Claude reads these, in order)
0. `docs/full-beta-v2/DEVICE_SPEC.md` — the authoritative current-product spec/index (MCU/radios/antennas/
   power/connectors/mechanical, with LOCKED/FITTED/DNP/UNRESOLVED + MARKETING-SAFE labels). **MANDATORY**
   before any external / mechanical / marketing claim.
1. `docs/full-beta-v2/CTO_DECISIONS.md` — authoritative rulings (latest: **D-301**, FBV2-P2-004A the
   `AQROOT_LTCGATE_KO` **path-shaping** lever ACCEPTED and COMMITTED (genuine +1: closes `LTC_GATE
   U18.10→Q3.4`, LOST 0, no new DRC; OFF-by-default, byte-identical when unset, pinned by G15); copper NOT
   promoted — full Phase-A now FAILs at the newly-exposed `U11.2` BPP 1.5 mm trunk wall; autonomy
   CONTINUES; preceded by **D-300** (003Z re-order refuted) and **D-299** (003Y U19CAP +2 accepted/committed)).
2. Newest audits — `audits/2026-08-30-p2-004a-d301-ltcgate-ko-path-shaping-lever-full-gate-plus1-accepted-committed-u11-trunk-wall.md`,
   then `…-003z-d300-ltcgate-defer-to-congestion-lever-refuted-false-positive-probe-retired.md`,
   then `…-003y-d299-u19cap-full-gate-plus2-accepted-committed-ltc-gate-wall.md`,
   then `…-003x-d298-u19-capacity-east-lane-reservation-lever-screened-clean-handoff.md`,
   then `…-003w-d297-secondary-u18bpp-i3-join-lever-net-gain-accepted.md`,
   then `…-003v-d296-primary-reservation-lever-ordering-trade-no-progress-retired.md`,
   then `…-003u-d295-two-walls-full-run-emergent-ordering-cheap-vacuous-handoff.md`,
   `…-003t-d294-direction2-full-gate-fail-u18-corridor-u19-escape.md`,
   `…-003s-d292-u18-r75-placement-microeco-exhausted.md`,
   `…-003r-d290-off-layer-vacate-refuted-owner-decision.md`, `…-003q-d289-…`, `…-003o-d288-…`.
3. `docs/full-beta-v2/CHANGELOG.md` and `docs/full-beta-v2/PROGRESS.md` (top entries).
4. Git HEAD + recent commits; the 003W instruments — the accepted D-297 lever in
   `hardware/beta-v2/checks/route_battery_block.py` (env `AQROOT_U18BPP_JOIN`, the `main()` join
   site), its **G13** contract in `checks/router_regression.py`, and the measured-record probe
   `checks/u18_i3_join_probe_003w.py`. The fixed bridge sites `bridge_early_003i.py` /
   `bridge_route_003c.py` (D-288).
5. Evidence + recipe + probes: the pinned natural-run
   `hardware/beta-v2/checks/phaseA_003o_b1_r75rot_cto.json`; the governing full recipe
   `w/run_003t_full.sh` + `w/cand_003t/t_a_r77e15n10_r79e15n10.json`; gitignored full-run results
   `w/phaseA_003t_full_e15n10cto.json` (D-294 baseline) and `w/phaseA_003t_full_003w_u18bpp_i3.json`
   (D-297); `place_003l.json`, `place_002z/` candidate set.
- **Never** trust this checkpoint over a conflicting `CTO_DECISIONS.md`; repair this file if they
  diverge.
