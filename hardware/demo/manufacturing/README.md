# AQROOT Demo manufacturing preflight

Status: **BLOCKED** at board completion; no manufacturing candidate is approved.

## NFC U9 refloor preflight rejection (2026-09-02)

The atomic U9 harness now runs real schematic-parity DRC immediately after its
eight-segment withdrawal and fixed 0.5 mm-east move. That preflight rejects the
pose before routing: U9 overlaps C17's courtyard and shifted pads intersect
retained NFC copper (five shorts and one clearance failure). The requested
RFO1-first and VDD_D-lower-first screens also fail independently. All four
registered macro orders stop at the same precondition, so the fixed pose is
parked and cannot emit a candidate. The authoritative board remains
`360b8261...` at 67 open retained nets / 484 edges. Freshly rank an independent
retained net; revisit U9 only as a broader bounded U9/C17/passive refloor with a
complete impacted-copper replay boundary.

## NFC U9 atomic supply-refloor replay screen (2026-09-02)

`route_nfc_u9_supply_refloor_scratch.py` implements the fixed +0.5 mm-east U9
transaction with an exact eight-segment withdrawal boundary, allowlisted replay,
both new supply trees, fitted-connectivity checks, and real refilled parity DRC.
Signal-first is blocked at the shifted RFO1 launch after XIN/XOUT/RFO2 replay;
supply-first is blocked at the VDD_D lower branch after its upper branch. Both
partial candidates are rejected; neither removes copper outside the measured
boundary or adds copper on another net. The authoritative board remains
`360b8261...` at 67 open retained nets / 484 edges. Next enumerate the bounded
within-family orders at this fixed pose, beginning RFO1-first and VDD_D-lower-
first, without weakening the atomic promotion gate.

## NFC U9 supply-refloor pose/impact screen (2026-09-02)

`screen_nfc_u9_supply_refloor.py` tests 36 U9 poses and identifies five that
unlock legal 0.30 mm B.Cu launches for both VDD_D and VDD_A. The lowest-impact
pose translates U9 0.5 mm east without rotation. Its exact accepted-copper
replay boundary is eight pad-attached segments across XIN, XOUT, RFO1, RFO2,
AGDC, and VDD_AM. The deliberately unreplayed pose has 15 attributable real
parity-DRC reports, so no placement or copper is promoted. Board `360b8261...`
and fitted connectivity 67/484 remain unchanged. Next, implement the complete
atomic east-translation/replay plus both supply trees and accept it only if the
full-board preservation, connectivity, and refilled-DRC gate passes.

## NFC VDD_D/VDD_A package-land wall (2026-09-02)

`route_nfc_vdd_da_pair_scratch.py` atomically screens both adjacent ST25R3916
three-land decoupling trees across all eight net and branch orders. Every case
fails before copper emission: U9.3 (`NFC_VDD_D`) has no legal 0.30 mm B.Cu
escape at the qualified 0.20 mm package-land clearance because of U9.4, U9.2,
U9.1, and U9.33; U9.7 (`NFC_VDD_A`) is boxed by U9.8, U9.6, U9.33, and Y1.4.
All scratch runs retain the accepted real refilled schematic-parity DRC
signature of 199 footprint-library, five hole-clearance, and one solder-mask-
bridge report. No copper is promoted; board `360b8261...` and fitted
connectivity 67 open nets / 484 edges are unchanged. Park this planar family.
Next, bound a coherent U9 supply-fanout/nearby-passive placement transaction
covering both rails; do not replay branch ordering in the unchanged geometry.

## External-I2C buffer local-tree wall (2026-09-02)

`route_ext_i2c_buffer_pair_scratch.py` atomically screens both orders of the
four local `EXT_SDA_BUF`/`EXT_SCL_BUF` edges and rejects partial trees. Each
U16-to-pull-up B.Cu leg routes, but neither mixed-face series leg completes
through the qualified ordinary-via In2/In3 framework: U16.7 has no reachable
via site and U16.2 has no inner join after both endpoint reservations. The
SCL-first planar branch also passes the accepted `ACC_3V3_SW` via at
`(55.350,56.550)` by 0.2445 mm against the locked 0.250 mm rule. No copper is
promoted; board `360b8261...`, fitted connectivity 67 open nets / 484 edges,
and real refilled schematic-parity DRC 199/5/1 remain unchanged. Park this
add-only family pending an explicit U16 package-fanout/corridor transaction;
freshly rank another independent retained local cluster next.

## Radio/NFC package-fanout wall narrowed (2026-09-02)

`screen_package_fanout_transaction.py` replaces the generic endpoint search
with explicit package-aware 0.20 mm necks and ordinary 0.60/0.30 mm via sites
for the two remaining control-cluster endpoints.  Real KiCad scratch DRC proves
that neither is an add-only escape: U9.27's only outward route crosses the
accepted `NFC_AGDC` fanout, while U2.20's only inward route crosses the accepted
`BTN_B_N` fanout and violates clearance to the accepted `ACC_5V_SW_EN` via.
The authoritative board remains byte-identical at `360b8261...`; no HDI or
via-in-pad assumption was introduced.  Park `NFC_IRQ` and `SX1262_DIO1` until a
bounded accepted-copper fanout transaction is justified.  Next, rank an
independent retained local cluster; do not replay either unchanged add-only
escape family.

## Radio interrupt/control cluster advance (2026-09-02)

`SX1262_BUSY` is now complete from U1.12 to U8.14 with two ordinary
0.60/0.30 mm vias and a 0.20 mm In2 haul. The add-only route contributes eight
copper objects and 58.702654 mm, removes no accepted copper, and improves fitted
connectivity from 68 to 67 open nets / 485 to 484 open edges; ratsnest improves
514 to 513. Real refilled schematic-parity DRC remains at the accepted 199
footprint-library / 5 hole-clearance / 1 solder-mask-bridge signature.

The same qualified endpoint-reservation framework bounds the other two cluster
members without emitting copper: `NFC_IRQ` has no ordinary-via escape at U9.27
(blocked by U9.28/U9.26/U9.25/U9.33), and `SX1262_DIO1` has none at U2.20
(blocked by U2.21/U2.18/U2.19 and accepted track geometry). Board `360b8261...`;
production hardware is unchanged. Next, screen an explicit package-fanout
transaction for U9.27 and U2.20; do not replay the unchanged generic inner-haul
family.

## LTC4368 fault test-point branch promoted (2026-09-02)

The isolated `TP18.1` island is now joined to the retained
`LTC4368_FAULT_N` safety/status tree. The add-only route is nine 0.20 mm B.Cu
segments totaling 39.822537 mm and uses 0.300 mm clearance; it removes no
accepted copper. All five fitted lands are one island. Real refilled
schematic-parity DRC remains at the accepted 199 footprint-library / 5
hole-clearance / 1 solder-mask-bridge signature; fitted connectivity improves
69→68 open nets and 486→485 edges, and ratsnest improves 515→514. Board
`bbb69e92...`; the production tree is unchanged. Next, screen a coherent
retained sub-GHz/NFC interrupt/control cluster beginning with `NFC_IRQ`,
`SX1262_BUSY`, and `SX1262_DIO1`.

## LED_A explicit perimeter wall (2026-09-02)

`screen_led_a_perimeter.py` reserves J1.1's perpendicular F.Cu launch and
screens 60 deterministic orthogonal corridors at the locked 0.30 mm width and
0.20 mm clearance. The launch is legal in every case, but no corridor reaches
R71.2: 12 block on the lateral leg, 16 on the turn toward the ballast spine,
and 32 on the final approach. No partial or authoritative copper is emitted;
board `a819ade1...`, fitted connectivity 69 open nets / 486 edges, and real
refilled schematic-parity DRC 199/5/1 remain unchanged. Park LED_A until a
bounded J1/ballast placement transaction or changed surrounding geometry is
justified. Next, freshly rank an independent retained local cluster.

## LED_A planar distribution wall (2026-09-02)

The coherent five-land display-backlight anode transaction was screened in
both chain orders at 0.30 mm width and 0.20 mm clearance on F.Cu.  The four
ballast lands R73.2/R70.2/R72.2/R71.2 connect cleanly with fourteen candidate
segments, but the required R71.2-to-J1.1 feed reports `NO_PATH` whether it is
attempted first or last.  The full-board scratch DRC remains exactly 199
footprint-library / 5 hole-clearance / 1 solder-mask-bridge reports and no
partial copper is promoted.  The qualified inner-haul framework correctly
refuses this 0.30 mm current-distribution net as low-speed-signal-only, so that
is not an acceptable fallback.  Board `a819ade1...` remains byte-identical.
Next, reserve explicit F.Cu escapes at J1.1 and the ballast spine and screen a
bounded perimeter waypoint family; do not retry the generic planar chain or
weaken the current-path width.

## USB-C shield tree promoted (2026-09-02)

The five fitted `Net-(J3-SHIELD)` lands are now one connected copper island.
The atomic route attaches `R32.1` through two ordinary 0.60/0.30 mm vias, then
joins all four plated J3 shield stakes on B.Cu. It adds twelve 0.30 mm segments
and two vias, removes no accepted copper, and adds no wrong-net object. Two
clean scratch runs reproduce geometry digest `08990b0b...`. The independent
refilled schematic-parity KiCad DRC remains exactly at the accepted 199
footprint-library / 5 hole-clearance / 1 solder-mask-bridge signature. Fitted
opens improve 70→69 nets and 490→486 edges; ratsnest improves 519→515. Next,
screen the independent local five-land `LED_A` backlight-current distribution
tree as one coherent transaction.

## U2/button pull-up branch wall (2026-09-02)

The coherent `BTN_DOWN_N` / `BTN_LEFT_N` / `BTN_A_N` local-branch batch is not
promotable with either qualified generic topology. The atomic planar screen
fails its first required `U2.14` to `R5.2` branch with `NO_PATH`; the reserved-
via In2/In3 alternative fails earlier because `U2.14` has no legal ordinary
through-via site from B.Cu. Both screens emit zero copper, retain all three
nets at three fitted open edges, and preserve the real refilled schematic-
parity DRC signature of 199/5/1. Park this shared U2-side family; revisit it
only through a bounded U2 package fanout or local placement transaction.
Next, freshly rank an independent retained local cluster.

## NFC VDD_RF package-land wall (2026-09-02)

The adjacent four-land ST25R3916 `NFC_VDD_RF` tree is not promotable with the
proven local planar framework.  A lower-branch-first atomic screen fails before
emitting copper because U9.14 has no legal 0.20 mm B.Cu escape; stable blockers
are U9.15, U9.13, exposed pad U9.33, and U9.10.  Upper/cap-spine generic searches
also exceed the bounded local-search window, so branch order cannot repair the
lower-land precondition.  Real refilled schematic-parity DRC remains 199/5/1,
the target remains three open edges, and board `97d60cde...` is unchanged.
Park the unchanged planar family.  Next, freshly rank an independent retained
local cluster; revisit VDD_RF only with an explicit package-fanout or bounded
local U9/passive placement transaction.

## NFC VDD_AM decoupling-tree promotion (2026-09-02)

The retained ST25R3916 `NFC_VDD_AM` rail now connects U9.11, C51.1, and
C52.1 as one fitted island. The atomic transaction adds 18 B.Cu-only 0.30 mm
segments (60.878940 mm), no vias, removes no accepted copper, and reproduces
a clean result in both branch orders. Real refilled schematic-parity DRC
remains at the accepted 199 footprint-library / 5 hole-clearance / 1
solder-mask-bridge signature. Fitted opens improve 71 to 70 nets and 492 to
490 edges; ratsnest improves 521 to 519. Board SHA-256 is `97d60cde...`.
Next, screen the adjacent four-land `NFC_VDD_RF` supply tree as one coherent
local transaction while preserving all accepted NFC signal/tuning copper.

## U11 adjacent-branch reservation screen (2026-09-02)

`screen_u11_iset_escape_transaction.py` exhausts both branch orders and all
eight 2 mm directional targets for U11.6 (`TS_MR`) and U11.9 (`STAT1`) before
attempting U11.8 (`ISET`): 128 scratch-only cases at 0.20 mm width/clearance on
B.Cu. U11.6 reserves successfully in all 64 TS-first cases. U11.9 has no legal
escape in all 64 STAT1-first cases and after every U11.6 reservation, so zero
case reaches ISET and zero candidate is emitted. The package pocket is parked;
do not retry branch ordering in place. The authoritative board remains
`7a764bac...`. Next, freshly rank an independent retained local net/cluster.

## ISET package-land wall and local-route guard (2026-09-02)

The 5.683 mm `/01_POWER_TREE/ISET` net remains open: U11.8 has no legal
0.20 mm B.Cu escape between U11.6, U11.9, accepted track geometry, and the
board edge. No copper was emitted. A fallback attempt against already-connected
`ILIM_VSET` exposed a duplicate-copper false promotion; the shared local
two-pad gate now requires fitted open-edge reduction before candidate output
or promotion. Regression rejects `ILIM_VSET` at 0→0 and ISET at 1→1. The
authoritative board remains `7a764bac...` and real refilled schematic-parity
DRC remains 199/5/1. Next, reserve the adjacent U11.6/U11.9 branches before a
bounded U11.8 escape attempt; park the pocket if that family is empty.

## NFC AGDC decoupling-tree promotion (2026-09-02)

The fitted C53.1/U9.24/C54.1 tree is complete with 17 add-only 0.30 mm B.Cu
segments (40.626806 mm), no vias, and no accepted-copper removal. Both branch
orders reproduce the same clean geometry. Refilled schematic-parity DRC stays
at 199/5/1; fitted connectivity improves to 71 open nets / 492 open edges and
ratsnest 521. Board SHA-256 is `7a764bac...`. Next, screen the independent
5.683 mm `ISET` charger-programming net; the shorter `ACC_5V_LX` wall remains
parked for its power-core refloor transaction.

## ACC_5V_BOOST_EN planar-tree screen (2026-09-02)

`route_acc_5v_boost_en_tree_scratch.py` atomically screens all six launch
orders for the required U3.16/R102.1/TP30.1/U21.2 boost-enable tree. Every
order closes all three fitted open edges on B.Cu, but real refilled
schematic-parity KiCad DRC rejects every candidate at the same four accepted
accessory-rail vias. Actual clearances are 0.2254--0.2352 mm against the locked
0.250 mm rule. Replaying with a conservative 0.275 mm router search clearance
does not change those four exact crossings, so order and generic planar search
margin are not the lever. No copper is promoted; the authoritative board
remains `86cff98b...` with fitted connectivity 73 open nets / 496 edges and
the accepted 199/5/1 DRC signature. Next, reserve U3.16 and U21.2 escapes and
screen an In2/In3 control haul before attaching R102.1 and TP30.1; do not retry
the unchanged planar family.

## ACC_5V_ILIM route (2026-09-02)

The retained U22 current-limit programming net is promoted from U22.4 to
R101.1 as seven add-only 0.20 mm B.Cu segments (42.417480 mm), with no vias and
no accepted-copper removal. Two clean candidates reproduce identical physical
geometry. The authoritative refilled schematic-parity DRC remains 199/5/1;
the fitted ledger improves from 74 to 73 open nets and 497 to 496 open edges.
Board SHA-256 is `86cff98b...`. Route or bound `ACC_5V_BOOST_EN` next while
preserving the accepted accessory-power core and independent D-186 controls.

## ACC_PWR_EN east-perimeter inner screen (2026-09-02)

The recovered D-440 successor bounds five explicit east-side inner waypoints
from X=64 through 68 mm across both signal inner layers and the first four
reserved via sites at each endpoint.  An initial generic grid-search version
timed out in all 160 cases and was rejected as inconclusive.  The retained
harness instead checks each fixed orthogonal segment directly against exact
router obstacle geometry before emitting it.

All 160 deterministic cases reserve ordinary 0.60/0.30 mm U16.1 and U3.20 B.Cu
escapes, but the first inner leg is blocked in every case.  No join copper is
emitted or promoted.  The authoritative board remains `2830082d...`, target
connectivity remains two open edges, and real refilled schematic-parity DRC
remains 199/5/1.  Park this materially unchanged via-to-east orthogonal family;
freshly rank an independent retained net or coherent local cluster next.

## ACC_PWR_EN reserved-site inner screen (2026-09-02)

The D-439 successor reserves ordinary 0.60/0.30 mm vias from U16.1 and U3.20,
then screens the first four independently ranked sites per endpoint on both
In2 and In3. All 32 atomic cases expose both B.Cu package escapes, but none has
a legal 0.20 mm inner join inside the qualified local-haul envelope. The target
remains at two open edges; real refilled schematic-parity DRC remains 199/5/1;
no accepted copper is removed and no candidate is promoted. Next, screen a
bounded outer-perimeter inner waypoint family rather than replaying either
the generic planar tree or these local site pairs.

## ACC_PWR_EN planar-tree screen (2026-09-02)

`route_acc_pwr_en_tree_scratch.py` atomically screens the required R17.1,
U16.1, and U3.20 accessory-isolation enable tree and rejects partial routes.
The generic 0.20 mm B.Cu topology is not viable: R17.1→U16.1 takes an 85.344 mm
detour with three real accessory-rail clearance violations, and U16.1→U3.20
has no legal 0.20 mm corridor at 0.050 or 0.025 mm grid. Only one of two fitted
edges closes. No candidate is promoted and the authoritative board remains
`2830082d...`. Next, reserve escapes at U16.1/U3.20 and join them on In2/In3
before attaching R17.1; do not retry the generic planar tree.

## Retained XGPIO4/XGPIO5 header-pair promotion (2026-09-02)

The D-437 successor constrains the XGPIO5 header leg through an explicit
`(62.500,30.500)` mm waypoint, clear of both accepted accessory-power barrels.
Two clean XGPIO5-first candidates have identical physical copper geometry. The
promoted atomic pair adds 21 F.Cu segments and no vias: nine segments / 24.844979
mm on XGPIO4 and 12 segments / 20.817576 mm on XGPIO5. Both three-land trees are
connected, no accepted copper is removed, and real refilled schematic-parity
DRC remains exactly 199 footprint-library, five inherited hole-clearance, and
one inherited solder-mask-bridge reports. Fitted opens improve 76→74 nets and
501→497 edges; ratsnest improves 530→526. Board hash is `2830082d...` and
`hardware/beta-v2/` remains untouched.

## Retained XGPIO4/XGPIO5 header-pair screen (2026-09-02)

`route_xgpio45_header_pair_scratch.py` atomically routes and gates the fitted
R55/D4/J5.13 and R56/D4/J5.14 trees without touching their accepted internal
U3 legs. Both launch orders close all four edges, but real schematic-parity DRC
rejects them. With 0.20 mm fine-pad clearance and a conservative 0.275 mm track
search, XGPIO5-first leaves one stable violation: 0.2334 mm from its F.Cu
segment to the accepted `ACC_5V_RAW` via at `(61.375,34.300)`, below the locked
0.250 mm requirement. No copper was promoted. Next, explicitly shape XGPIO5
around that via and replay the complete pair through the same gate.

## Connector-side USB N perimeter enumeration (2026-09-02)

`enumerate_usb_connector_n_fanouts.py` exhaustively checks all four cardinal
and four diagonal F.Cu launch families at both 0.050 and 0.025 mm grids for
J3.A7, J3.B7, and U10.1. J3.A7 and U10.1 expose legal launches at both grids;
J3.B7 exposes zero. Its stable blockers are adjacent J3.A6, the board edge,
J3.A5, and accepted track geometry. The wall is therefore the reversible
connector land pocket, not a downstream pair-join ordering problem.

No copper or placement changed and the authoritative board remains
`2afa51d9...`. Next, bound a local J3/U10 placement transaction that preserves
J3's locked mechanical position and atomically replays every displaced U10
branch; do not weaken the F.Cu-only, 0.23 mm, zero-via USB contract.

## Connector-side USB planar-tree screen (2026-09-02)

`screen_usb_connector_pair.py` treats the reversible USB-C lands and U10 ESD
inputs as two complete three-pad trees. It exhaustively tests both pair orders
and every node-attachment order: 72 atomic cases at the locked 0.23 mm width,
0.20 mm clearance, F.Cu-only, zero-via USB contract.

The P tree completes in all 36 cases where it is attempted first. The N tree
reports `NO_LEGAL_ESCAPE` in every case, including all 36 attempts made before
P adds copper. No complete pair exists in this planar family. The authoritative
board remains byte-identical at `2afa51d9...`; no copper, placement, rule, or
production-hardware change was made.

Next, pre-reserve distinct F.Cu perimeter fanouts for J3.A7, J3.B7, and U10.1
before joining the N tree. If those three launches cannot coexist, bound a
local J3/U10 placement transaction without weakening the USB layer/via
contract. Manufacturing export remains premature and no owner decision is
open.

## V3V3 feedback-tree promotion (2026-09-02)

The retained TPS63020 feedback net is complete across U12.3, R39.2, and
R40.1. A direct B.Cu divider route was blocked, and the first In2 divider
candidate missed a retained D-269 BPP barrel clearance by 0.0575 mm. The
accepted feedback-specific topology instead roots both branches at U12.3:
R40.1 uses In2, R39.2 uses In3, and the branches share one ordinary U12-side
through-via. The final transaction adds ten 0.20 mm tracks and three
0.60/0.30 mm vias, with no accepted-copper removal.

The authoritative refilled schematic-parity DRC remains exactly 199
footprint-library, five inherited hole-clearance, and one inherited
solder-mask-bridge reports. Fitted open nets improve 77 to 76, open edges 503
to 501, and raw ratsnest 532 to 530. Board hash is `2afa51d9...`;
`hardware/beta-v2/` remains untouched. Next, screen connector-side USB D+/D−
as a coherent differential pair. Manufacturing export remains premature and
no owner decision is open.

## U12/L1 buck-boost switch-pair promotion (2026-09-02)

Both retained TPS63020 switch nodes are complete across the paired U12 lands
and L1. The deterministic atomic transaction adds nine B.Cu objects: short
0.20 mm VSON land joins that flare immediately into 0.40 mm switch trunks.
There are no vias and no switching tracks on inner layers. The two completed
paths measure 15.335 mm and 3.977 mm and close four fitted open edges.

The authoritative refilled schematic-parity DRC remains exactly 199 footprint-
library, five inherited hole-clearance, and one inherited solder-mask-bridge
reports. No accepted copper is removed. Fitted open nets improve 79 to 77,
open edges 507 to 503, and raw ratsnest 536 to 532. Board hash is
`3c5d425f...`; `hardware/beta-v2/` remains untouched. Next, screen the local
three-land `V3V3_FB` feedback tree while preserving the completed switch-loop
geometry. Manufacturing export remains premature and no owner decision is
open.

## VBUS-present local-tree promotion (2026-09-02)

`/01_POWER_TREE/VBUS_PRESENT` is complete across C68.1, R105.1, R104.2, and
TP31.1. The deterministic transaction reserves TP31 first with a two-via In3
hop, then closes the three short passive branches on B.Cu. It adds 13 target-net
objects at 0.20 mm, removes no accepted copper, and adds no wrong-net geometry.

The authoritative refilled schematic-parity DRC retains exactly 199 footprint-
library, five inherited hole-clearance, and one inherited solder-mask-bridge
reports. Fitted open nets improve 80 to 79, open edges 510 to 507, and raw
ratsnest 539 to 536. Board hash is `f8d555d4...`; `hardware/beta-v2/` remains
untouched. Next, screen the short L1/U12 buck-boost switching cluster as an
atomic power-aware transaction. Manufacturing export remains premature and no
owner decision is open.

## SPI-A paired J1 fanout wall (2026-09-02)

`screen_spi_a_j1_pair.py` implements the D-427 successor: it reserves distinct
ordinary 0.60/0.30 mm through-via fanouts for adjacent display pads J1.36
(`/SPI_A_SCK`) and J1.34 (`/SPI_A_MOSI`) before either net can claim an inner
haul. It screens the first four ranked escape sites for each pad with both
In2/In3 assignments, for 32 atomic cases total.

No complete pair exists in this bounded family. Eleven cases fail while
reserving the two J1 barrels; of the 21 cases that reserve both, 16 fail the
SCK join to U1.20 and five fail the MOSI join to U1.19. Zero case completes
both three-pad trees, so no partial copper is promoted. The harness is retained
as deterministic wall evidence and the authoritative PCB remains byte-identical
at `7e20e227...`.

The adjacent J1 paired-fanout wall is now parked. Next, promote the independently
complete `/SPI_A_SCK` tree using the already-proven clock-first transaction,
but only after a fresh authoritative refilled schematic-parity DRC,
connectivity/ledger comparison, accepted-copper preservation check, D-269 and
D-186 invariants, and production-tree hash check. `/SPI_A_MOSI` remains a later
critical-path wall; manufacturing export remains premature and no owner
decision is open.

## Audio/radio long-haul screen (2026-09-02)

The generic reserved-escape framework now defines `/I2S_SPK_DOUT` and
`/CC1101_GDO0`. The 33.605 mm speaker-data link reserves ordinary 0.60/0.30 mm
vias from both F.Cu endpoints, but neither In2 nor In3 joins at 0.20 mm; a
same-face search also exceeded the bounded 90-second screen. The 40.033 mm
CC1101 link fails earlier because U7.15 has no reachable legal ordinary via
site from B.Cu. Both runs leave the board byte-identical and refilled parity
DRC at 199/5/1. Do not retry either unchanged topology. Next, rank a short
independent local retained cluster. No owner decision is open.

## SPI-A MISO promotion (2026-09-02)

The fitted MISO topology is U1.21 to microSD J2.7 only. R112 remains DNP, so
the display SDO provision is intentionally excluded and cannot contend with
microSD reads. A generic F.Cu screen reproduced `NO_PATH`; the qualified
endpoint-reservation framework then closed the net with three 0.20 mm F.Cu
segments, three 0.20 mm In2.Cu segments, and two ordinary 0.60/0.30 mm vias.
The route is 28.739064 mm and removes no accepted copper.

The authoritative refilled schematic-parity DRC remains exactly 199 footprint-
library, five inherited hole-clearance, and one inherited solder-mask-bridge
reports. Fitted open nets improve 82 to 81, open edges 513 to 512, and raw
ratsnest 542 to 541. `hardware/beta-v2/` is unchanged and the authoritative
PCB SHA-256 is `7e20e227...`.

Next, screen `/SPI_A_SCK` and `/SPI_A_MOSI` as one bus-aware bounded pair; they
own four remaining fitted open edges. Manufacturing export remains premature
and no owner decision is open.

## Native B endpoint-reservation promotion (2026-09-02)

The D-424 generic F.Cu wall is closed with the already-qualified low-speed
inner-haul framework. U1.24 and R62.1 each use a short 0.20 mm F.Cu escape and
ordinary 0.60/0.30 mm through-via; four 0.20 mm In2.Cu segments join the via
anchors. The complete route is 20.436636 mm, six segments plus two vias, and
adds copper only on `/NATIVE_B`.

The authoritative refilled schematic-parity DRC retains exactly 199 footprint-
library, five inherited hole-clearance, and one inherited solder-mask-bridge
reports. The fitted ledger proves both pads are one island; fitted open nets
improve 83 to 82, open edges 514 to 513, and raw ratsnest 543 to 542. No
accepted copper was removed, `hardware/beta-v2/` is byte-identical, and the
authoritative PCB SHA-256 is `b92701c2...`.

Next, freshly screen `/SPI_A_MISO` as a bus-aware transaction while preserving
the accepted SD/display copper. The accessory-boost, NFC-input, ISET, and USB
walls remain parked; manufacturing export is premature and no owner decision
is open.

## Native GPIO internal-pair screen and Native A promotion (2026-09-02)

A fresh fitted ledger ranked `/NATIVE_A` and `/NATIVE_B` as the shortest
unparked coherent pair of Demo-required internal signal legs. The atomic
`route_native_gpio_pair_scratch.py` harness screens both launch orders. Both
orders produce the same result: Native A closes, while Native B reports
`NO_PATH` at both 0.050 and 0.025 mm grid resolution even when attempted first.

The independent, order-invariant Native A result is promoted from U1.31 to
R61.1: 11 add-only 0.20 mm F.Cu segments, 20.149286 mm, and no vias. The
authoritative refilled schematic-parity KiCad DRC remains exactly 199
footprint-library, five inherited hole-clearance, and one inherited solder-
mask-bridge reports. Fitted open nets improve 84 to 83, fitted open edges 515
to 514, and raw ratsnest 544 to 543. No accepted copper was removed; retained
battery/accessory safety, RGB, XGPIO4/XGPIO5, NFC, and production hardware are
unchanged. Board SHA-256 is `5d5a45c5...`.

Next, screen an explicit endpoint-escape/perimeter corridor for `/NATIVE_B`;
do not repeat the disproven generic same-face path. Manufacturing export
remains premature and no owner decision is open.

## NFC analog-supply legal-via enumeration (2026-09-02)

`enumerate_nfc_supply_corridors.py` applies the D-422 westward U9.7 launch seed
to the accepted board at 0.025 mm resolution and searches for reachable
0.60/0.30 mm through-via sites.  The barrel is checked against B.Cu and In3,
the 0.25 mm hole-clearance floor is enforced, and sites are then filtered
outside a conservative envelope around every accepted `NFC_XIN`/`NFC_XOUT`
track (via radius plus 0.20 mm clearance).

The package side has **zero reachable legal via sites before the oscillator
filter is even applied**.  This is not an inner-layer-capacity wall: C47.1 and
C48.1 expose 204 and 217 legal landing sites respectively.  It sharpens the
D-422 result: its package-local analog barrel was itself non-promotable, and
moving only the inner return cannot repair the transaction.  The authoritative
PCB stays byte-identical at `37718bc7...`; no copper, placement, or rule changed.

This materially unchanged U9.7 west-neck/via family is parked.  Next, select
the highest-ranked independent retained net or small functional cluster from a
fresh fitted ledger.  Revisit the analog supply only with a materially
different package-fanout direction or a bounded local placement transaction;
do not retry westward barrel placement or disturb accepted oscillator copper.

## NFC supply explicit inner-fanout screen (2026-09-02)

The first D-421 follow-on used short westward 0.30 mm B.Cu necks from U9.3 and
U9.7, independent 0.60/0.30 mm through-vias, an In2 digital-supply tree, and an
In3 analog-supply tree to the two decouplers on each rail. This establishes a
concrete non-planar topology rather than repeating the generic B.Cu router.

The candidate is rejected. Real refilled schematic-parity DRC adds two shorts
between `NFC_VDD_A` and the accepted `NFC_XIN` arm, four clearances, one track
crossing, and one hole-clearance report above the accepted 199/5/1 signature.
The digital west-fanout was not the limiting geometry; the analog inner return
entered the completed oscillator envelope. No candidate copper or placement
was retained, and the authoritative PCB remains `37718bc7...`.

Next, enumerate U9.7 analog via sites and In2/In3 corridors outside the entire
`NFC_XIN`/`NFC_XOUT` geometry, then replay both three-land supply trees as one
transaction. Preserve the accepted oscillator and all other NFC copper; do not
repeat the rejected straight analog return through the crystal envelope.

## NFC digital/analog supply launch wall (2026-09-02)

`route_nfc_supply_pair_scratch.py` adds an atomic framework for the two local
three-land `NFC_VDD_D` and `NFC_VDD_A` decoupling trees. Both upper-first and
lower-first orders were screened at 0.30 mm supply width with the existing
0.20 mm UFQFPN escape floor. `U9.3` and `U9.7` both return
`NO_LEGAL_ESCAPE`; all eight arm attempts stop before adding copper.

Both scratch boards reproduce zero target-net geometry and the accepted real
refilled schematic-parity KiCad DRC signature of 199 footprint-library, five
inherited hole-clearance, and one inherited solder-mask-bridge reports. The
authoritative PCB remains byte-identical at `37718bc7...`; accepted NFC signal
copper and `hardware/beta-v2/` are unchanged. Next, screen explicit outward
U9.3/U9.7 fanouts to separate package-local via sites, then close each pair of
decouplers on an inner layer. Do not repeat the generic B.Cu launch family.

## Accessory 5 V raw In3 transition wall (2026-09-02)

`screen_acc_5v_raw_in3_transition.py` bounds the D-419 non-planar alternative:
six courtyard-local U21.6 raw-via sites crossed with two In3 approaches to the
accepted raw-tree via, while the proven generic `ACC_5V_LX` route stays on
B.Cu. All 12 cases fail the real refilled schematic-parity DRC in two clean
runs. The best site, `(56.20,39.40)` mm, still shorts the 0.25 mm U21.6 neck
and 0.90/0.40 mm raw transition barrel to the LX launch; the LX return also
misses the retained raw-tree via by 0.225 mm against the required 0.250 mm.
Moving the transition south only adds conflicts.

No PCB, placement, rule, or accepted copper was promoted; the authoritative
board remains byte-identical at `37718bc7...`. This is the fifth consecutive
non-promoting increment on the materially unchanged boost-core wall, so it is
now **PARKED** under the autonomy policy. Revisit only after surrounding
geometry changes or as part of a justified broader refloor. Next, advance the
independent local NFC supply/decoupling cluster, beginning with a coherent
screen of `NFC_VDD_D` and `NFC_VDD_A`; preserve all accepted NFC signal copper.

## Accessory 5 V R99/raw-neck boundary (2026-09-02)

`screen_acc_5v_raw_neck_refloor.py` tests 16 LX-first combinations: four R99
offsets and four explicit B.Cu raw necks. A 0.5 mm east R99 move is the only
minimum tested placement that removes the L4/R99 courtyard overlap without the
via-in-courtyard and dangling-copper regressions of larger moves. Every LX
route closes. No raw neck passes: north paths collide with retained
BQ25185/ILIM copper; south paths remove crossing reports but still intersect
LX and retain a 0.225 mm versus 0.250 mm raw-clearance miss. KiCad can label a
coincident scratch collision as short versus crossing across runs, while these
engineering predicates reproduce.

No placement or copper is promoted and the board stays byte-identical at
`37718bc7...`. The next bounded transaction should fix R99 at +0.5 mm and
coordinately reserve separate LX/raw south corridors before atomically
replaying FB, enable, input, and GND. Do not retry north necks or larger R99
moves.

## Accessory 5 V power-core replay bound (2026-09-02)

`screen_acc_5v_power_core_refloor.py` advances the U21/L4 refloor from a launch
probe to a complete two-net power-core transaction. It withdraws the 19
accepted `ACC_5V_RAW` objects in scratch, rotates U21 and L4 180 degrees, routes
`ACC_5V_LX` first, then rebuilds the five-endpoint raw-output tree. LX closes in
6.213 mm and the raw tree closes all endpoints. Reversing that order re-boxes
U21.5, so LX-first is now a fixed transaction constraint.

The candidate is rejected, not promoted. The generic inner-layer raw tree adds
one clearance and one track-crossing violation; the placement produces one
courtyard overlap, package-neck width reports, and three additional
solder-mask-bridge reports. The next screen must keep LX first, replay the raw
tree with topology-specific B.Cu geometry while preserving its accepted
C65/R99/C66/TP28/U22 structure where possible, and explicitly clear the U21/L4
courtyard interaction. Only then should FB, enable, input, and GND be replayed
as the remaining half of the six-branch atomic transaction. The authoritative
PCB remains byte-identical at `37718bc7...`.

## Accessory 5 V switch-node refloor bound (2026-09-02)

`screen_acc_5v_lx_refloor.py` closes the first coordinated placement question.
Moving `C65` 1.0 mm east does not open `U21.5`; the launch remains boxed by the
adjacent TPS61023 lands. Rotating `U21` 180 degrees in place does open the
launch. Rotating both `U21` and `L4` 180 degrees reduces the deterministic B.Cu
route from 13.593 mm to 6.255 mm, versus a 3.782 mm pad-to-pad displacement.

This is characterization, not promotable geometry. A `U21` rotation changes
the physical land positions of all six pins, so the next transaction must
withdraw and replay the complete fitted `ACC_5V_FB`, `ACC_5V_BOOST_EN`,
`BQ25185_SYS`, GND, `ACC_5V_RAW`, and `ACC_5V_LX` branches atomically. Preserve
the accepted `ACC_5V_RAW` tree and safe-low enable; minimize the switch loop;
promote only if the full refilled schematic-parity gate and fitted ledger pass.
The authoritative board remains byte-identical at `37718bc7...`.

## Accessory 5 V switch-node wall (2026-09-02)

`ACC_5V_LX` is a fitted two-pad switch node from `U21.5` to `L4.2`, spanning
4.020 mm. The local routing framework now pins its power-specific contract:
B.Cu only, 0.40 mm trunk width, 0.20 mm clearance, and an explicitly reported
0.20 mm U21 package-escape floor. An ordinary 0.40 mm launch returns
`NO_LEGAL_ESCAPE`; the bounded fine-pitch retry also returns
`NO_LEGAL_ESCAPE`, dominated by `U21.4`, accepted `C65.1`/`ACC_5V_RAW`, and
adjacent U21 lands. Two clean screens are identical and emit no scratch copper.

The authoritative PCB remains byte-identical at `37718bc7...`. Its refilled
schematic-parity DRC signature remains exactly 199 footprint-library, five
inherited hole-clearance, and one inherited solder-mask-bridge reports. No
rule, placement, or accepted copper changed. The next bounded tactic is a
coordinated local `U21`/`L4`/`C65` cluster-refloor screen that preserves and
revalidates the accepted `ACC_5V_RAW` transaction while minimizing switch-loop
area; do not retry the generic launch or relax switch-node width/separation.
No owner decision is open.

## MAX17048 alert route promotion (2026-09-02)

`MAX17048_ALRT_N` now connects TP11.1 to U14.5 with an add-only, two-via In3
hop: 4.306134 mm of 0.20 mm copper and two 0.60/0.30 mm through-vias. The
bounded screen proves In2 closed and reproduces identical In3 physical geometry
twice. The refilled full-board KiCad gate retains only the accepted 199
footprint-library, five hole-clearance, and one solder-mask-bridge reports.
No accepted copper was removed; fitted opens improve 85→84 nets and 516→515
edges, and raw ratsnest improves 545→544. Board hash is `37718bc7...` and
`hardware/beta-v2/` remains untouched.

Next, screen the local accessory 5 V boost switching cluster, beginning with
`ACC_5V_LX` and then its feedback branch. Use power-topology-aware geometry;
the switching node must not be handled as a generic signal. No owner decision
is open.

## NFC receiver-input wall (2026-09-02)

The atomic `NFC_RFI1/RFI2` harness closes neither U9 package launch in either
order. The locked 0.30 mm B.Cu trunks cannot escape U9.22/U9.23, and the
courtyard-legal 0.20 mm neck does not change that result. Moving only unrouted
decoupler C17 east by 1.25 mm also leaves both pins trapped by the accepted RFO2
arm and adjacent U9 lands. Both clean baseline orders reproduce the unchanged
board hash `0a5c99d1a97d22a90a353f8d09abcc982d6c1aa46e006404ec8bf211df489486`
and the accepted 199/5/1 DRC signature. No copper or placement was promoted.

This materially unchanged package-edge wall is parked. Next, use a bounded
two-via inner-layer hop for the local `MAX17048_ALRT_N` connection; its generic
direct B.Cu route has `NO_PATH`. Preserve all accepted NFC and power copper.
No owner decision is open.

## NFC antenna pair promotion (2026-09-02)

The symmetric fitted `NFC_ANT_A` and `NFC_ANT_B` four-pad nodes are now
complete. The A/B trees use 14/16 segments and 34.205680/21.063397 mm of
0.30 mm B.Cu with no vias. Each matching resistor retains direct test-point
access, while the antenna connector joins through the receive-divider
capacitor. Both atomic launch orders pass; the promoted A-first order adds
exactly 30 target-net segments and removes no accepted copper.

The authoritative refilled schematic-parity KiCad DRC signature remains 199
footprint-library, five inherited hole-clearance, and one inherited
solder-mask-bridge report, with no attributable class. Fitted connectivity
improves 87 to 85 open nets and 522 to 516 open edges; raw ratsnest improves
551 to 545. Board hash is
`0a5c99d1a97d22a90a353f8d09abcc982d6c1aa46e006404ec8bf211df489486`.

Next is the adjacent symmetric `NFC_RFI1/RFI2` two-pad input pair. Preserve the
completed receive-divider, antenna, EMC/match/output, and crystal copper. MCU
USB and `BQ25185_SYS` remain parked. No owner decision is open.

## NFC EMC pair promotion (2026-09-02)

The symmetric fitted `NFC_EMCA` and `NFC_EMCB` four-pad nodes are now complete.
Each uses 13 segments / 8.755267 mm of 0.30 mm B.Cu with no vias. The atomic
scratch gate closes all eight fitted pads, adds exactly 26 target-net segments,
removes no accepted copper, and retains the refilled schematic-parity KiCad DRC
signature of 199 footprint-library, five inherited hole-clearance, and one
inherited solder-mask-bridge report. Fitted connectivity improves 89 to 87 open
nets and 528 to 522 open edges; raw ratsnest improves 557 to 551. Board hash is
`b1fad08fd1b2039d9e8e72e8cd9e13da6b3d53de0c1b7c6a9b906a961eb66dbe`.

Next is the adjacent symmetric `NFC_ANT_A/B` four-pad pair. Preserve direct
J7/test-point access, the accepted receive-divider branches, and the completed
EMC/match/output network. MCU USB and `BQ25185_SYS` remain parked. No owner
decision is open.

## NFC crystal launch wall (2026-09-02)

`route_nfc_crystal_pair_scratch.py` deterministically screens both complete
three-pad `NFC_XIN`/`NFC_XOUT` launch orders. XIN-first closes XIN and its load
capacitor but boxes `U9.4`; XOUT-first closes XOUT and its load capacitor but
boxes `U9.5`. Both partial candidates retain the accepted real refilled KiCad
DRC signature (199 footprint-library, five inherited hole-clearance, and one
inherited solder-mask-bridge report), so the failure is a shared B.Cu package
launch corridor at adjacent U9 pads rather than a DRC/rule or load-capacitor
wall. No partial crystal copper is promotable. Next, screen an explicit
two-launch geometry that reserves independent north/south exits before either
long crystal join; preserve short, no-via, same-face crystal routing and do not
move the 27.12 MHz crystal unless that bounded geometry is exhausted.

The reserved two-launch alternative is now exhausted and the wall cause is
sharper. `U9.5` (XIN) is north of `U9.4` (XOUT), while the present Y1 orientation
puts pin 3 (XIN) south-east of pin 1 (XOUT); the two required same-face routes
therefore exchange vertical order. An in-place 180-degree Y1 rotation removes
that forced crossover and all four crystal/load-cap edges route with the exact
accepted real KiCad DRC signature. It is not promotable geometry: the sequential
result is 15.602 mm XIN and 7.122 mm XOUT; one load-cap branch necessarily takes
the long outside path in each sequential ordering. The exact path geometry is
reproducible even though generated KiCad UUIDs vary.
`route_nfc_crystal_pair_scratch.py --rotate-crystal-180` preserves this
deterministic proof and refuses candidate emission despite electrical closure.

Next, screen a coherent `Y1`/`C79`/`C80` placement transaction which keeps Y1's
center unless a small translation materially improves both arms, aligns the
rotated pin order with U9, and restores short, balanced crystal and load-cap
branches. Promote placement and both nets only as one add/reposition transaction
after the authoritative full-board gate. No owner decision is open.

That coherent transaction is now promoted. `Y1` rotates 180 degrees in place;
`C79` and `C80` exchange their existing `(28.6,27.1)` and `(28.6,32.9)` mm
positions so both load capacitors remain outside the aligned arms. XIN and XOUT
use 11 and eight add-only 0.20 mm B.Cu segments, respectively, with zero vias;
their complete lengths are 8.537437 and 5.422361 mm. Both launch orders produce
identical geometry digest `0148d20322aa24fc...`.

The authoritative refilled schematic-parity KiCad DRC remains exactly 199
footprint-library, five inherited hole-clearance, and one inherited solder-mask
bridge report. No accepted copper was removed, and the only added copper is 19
segments on the two oscillator nets. The fitted ledger moves 91 to 89 open
nets, 532 to 528 open edges, and raw ratsnest 561 to 557. The authoritative
board hash is `2d54a40da1ec0f53e0cdf75bb35b63cc84aa7d435e8ef0cce896d7dbb69bec1e`.
Battery/accessory-power, RGB, XGPIO4/XGPIO5, and all other NFC paths remain
connected; `hardware/beta-v2/` is untouched.

Next, select the highest-leverage independent retained-net cluster from the
fitted ledger. Keep the materially unchanged MCU USB and `BQ25185_SYS` walls
parked. Manufacturing export remains premature at 89 retained open nets / 528
retained open edges; no owner decision is open.

The deterministic candidate exporter is `export_candidate.sh`. It writes only to
a new caller-supplied directory, generates full/fitted BOMs, an assembly position
file, all six copper layers, paste/mask/silkscreen/outline Gerbers, separate PTH
and NPTH drill files, and then runs `check_candidate.py`. Existing output is never
overwritten.

## 2026-09-02 baseline at `3e241dc`

- Board SHA-256: `cb4774b5ab76eb427bd70f0fb7dde17b7a1d7eb3c860826e94efeb7c9f91e93d`.
- All 14 expected Gerber/job files and both non-empty drill files exported; the
  drill report contains 139 PTH and 7 NPTH holes.
- Full BOM: 310 references. Schematic-fitted BOM: 294 references, with 16 DNP.
- CPL: 263 references.
- Real KiCad DRC: 205 board violations in the accepted baseline classes (199
  footprint-library, 5 hole-clearance, 1 solder-mask bridge), **plus 499
  unconnected-item errors** and 265 schematic-parity warnings.
- The 499 errors prove that the earlier RGB milestone completed only the four
  Demo replacement nets. The retained board is not routing-complete; its
  ratsnest was still 610 after RGB promotion.
- Schematic/PCB population parity is not release-safe: all 16 schematic DNP
  references leak into a PCB-derived CPL because their footprint DNP flags do
  not match: `C21 C22 C34 C35 C81 C82 L2 R44 R45 R68 R93 R107 R112 R119 R123 U13`.
- Procurement coverage is incomplete: 229 fitted references lack an MPN. Most
  are passives and test points, but `J8` is also in this set. This must be
  resolved through an explicit fitted/off-board/test-point population model,
  not by accepting an underspecified grouped BOM.

The generated files from this baseline are characterization artifacts only and
were deliberately not promoted into the repository. The authoritative Demo PCB
and schematic were not changed, and `hardware/beta-v2/` remained untouched.

## Retained-net routing ledger

`routing_ledger.py` is the deterministic connectivity authority for Demo routing
completion. It derives the 294 fitted references from the schematic BOM, removes
only the 16 explicit schematic-DNP references from routing obligations, and uses
KiCad's copper connectivity over distinct physical pad lands. The eight approved
Demo NC contacts are audited by exact identity (`J5.9`-`J5.12` and
`J5.15`-`J5.18`); no other connector contact is exempted.

Run it from the repository root:

```text
hardware/demo/manufacturing/routing_ledger.py /tmp/demo-routing-ledger.json
```

The accepted `988149f` baseline is pinned in `routing-ledger-baseline.json`:
173 retained multi-pad nets, 59 already connected, 114 open, and 581 retained
open edges. This reconciles exactly with KiCad's raw 610-edge ratsnest after
removing the 29 edges owed only by unpopulated DNP pads. `LS1` is correctly
off-board and `BOSS1/BOSS2` are PCB-only mechanical references.

## Next bounded task

The speaker-output cluster was promoted on 2026-09-02. `SPK_P`, `SPK_N`,
`SPK_P_CONN`, and `SPK_N_CONN` now connect `U5` through `R121`/`R122` to `J6`.
The class-D legs use 0.25 mm outer-layer copper with two 0.60/0.30 mm vias per
leg; connector legs remain on F.Cu. The retained ledger moved exactly 581 ->
577 edges and the raw ratsnest 610 -> 606. The authoritative refilled KiCad DRC
remains exactly 199 footprint-library, 5 inherited hole-clearance, and 1
inherited solder-mask-bridge report, with no new attributable class. Board hash:
`b85533a559f81ae8b49366b76ddbfcdaace3a0086c434d525d06eee0893729d4`.

IR routing characterization on 2026-09-02 corrected the earlier cluster
assumption. The fitted-pad ledger proves that `IR_GATE` is a separate long-haul
signal: its three pads (`R22.2`, `Q1.1`, and the safe-off pull-down `R23.1`)
span **110.586 mm** and account for two open edges. The LED-current loop is the
genuinely local cluster: `IR_LED_A` spans 9.282 mm with two open edges and
`IR_LED_K` spans 5.307 mm with one. `R123` is DNP and must not be counted as a
required routing endpoint or used to satisfy fitted connectivity.

A first combined scratch topology was rejected before promotion: forcing all
three nets through one outer/inner-layer pattern crossed accepted top-edge
copper and did not provide a legal local current loop. The authoritative board
did not absorb that attempt.

The separated local-current task was promoted on 2026-09-02. `IR_LED_A` now
connects fitted `R24.1`, `D1.2`, and `TP39.1`; `IR_LED_K` connects `D1.1` to
`Q1.3`. Both use 0.30 mm F.Cu with no vias, preserve the 12 ohm current limit,
leave DNP trim `R123` electrically optional, and keep the emitter/FET loop at
the top edge. The retained ledger moved exactly 577 -> 574 edges and raw
ratsnest 606 -> 603. Real KiCad DRC remains exactly 199 footprint-library, 5
inherited hole-clearance, and 1 inherited solder-mask-bridge report, with no
new attributable class. Board hash:
`ddebb3500f445524bd932aaff055f7c60f6d5bca17cee25f64ed0624d2bfbf67`.

The separated `IR_GATE` task was promoted on 2026-09-02. The FET gate and
reset-safe `R23` pull-down join on 0.20 mm F.Cu at the top edge; a two-via
0.60/0.30 mm In2.Cu haul reaches `R22.2` without bypassing the series gate
resistor. All three fitted pads are one copper island. The retained ledger
moved exactly 574 -> 572 edges and raw ratsnest 603 -> 601. A zone-refilled
full-board KiCad DRC remains exactly 267 total reports / 499 raw unconnected
items, with no `IR_GATE` report or new attributable class. Board hash:
`b74cd3c059c50bc4edeb7ba17b6b20a2067abe19ae31e159bc6d5c517f757b24`.

The first bounded `ACC_5V_RAW` transaction was characterized on 2026-09-02 and
rejected before promotion. The fitted-pad ledger confirms six isolated pads and
five retained open edges across 13.001 mm: `U21.6`, `C65.1`, `C66.1`, `R99.1`,
`TP28.1`, and `U22.2`. This is an `ACC_5V` power-class route, so it requires at
least 0.40 mm track width (0.60 mm preferred), 0.25 mm routed clearance, and a
power via with at least a 0.40 mm drill. The board's 0.25 mm minimum annular
width makes the usable ordinary through-via geometry 0.90/0.40 mm, not the
0.60/0.30 mm signal-via pattern.

A scratch topology kept the U21-to-C65 output connection on B.Cu and attempted
an In3 distribution tree through five 0.80/0.40 mm vias. Real zone-refilled
KiCad DRC rejected it: the proposed pad escapes crossed or shorted the accepted
`ACC_POWER_FAULT_N`, `ACC_DETECT_N`, and `XGPIO5` copper, and the 0.80 mm vias
failed the annular-width/diameter rules. No part of this attempt entered the
authoritative PCB.

The durable wall is endpoint-local rather than an In3 capacity problem.
Accepted B.Cu `ACC_POWER_FAULT_N` and `ACC_DETECT_N` branches bound the U21.6
escape channel on its east and west sides; fitted `TP10` closes its south exit.
At U22.2, the same accepted fault branch crosses the only direct west escape,
while adjacent U22 pads block north, south, and east. A compliant 0.90/0.40 mm
via cannot be placed in either endpoint pocket without colliding with retained
copper or a fitted pad. Blind/microvias and via-in-pad remain excluded: neither
has an approved manufacturing contract, and via-in-pad at the 0.675 x 0.350 mm
U21 land would compromise assembly.

The ordered local-obstacle study on 2026-09-02 disproved both initially proposed
minimal levers without changing the authoritative board. Moving `TP10` alone
cannot expose U21.6: a 0.40 mm B.Cu route from U21.6 toward C65.1 still crosses
the accepted `ACC_POWER_FAULT_N` segment from (59.25, 35.15) to
(59.20, 42.20), independently of TP10's position. The route also confirms that
U21's 0.15 mm package pad-to-pad spacing needs the existing local rule; it is
not permission to relax the 0.25 mm routed-clearance contract elsewhere.

A second scratch candidate removed only that crossing fault segment and the
long U22-side fault segment from (52.35, 56.80) to (52.90, 39.85), preserving
their endpoints with 0.60/0.30 mm through-vias and straight In2 replacements.
Refilled KiCad DRC rejected the candidate with five new clearance violations,
three new hole-clearance violations, and an `ACC_POWER_FAULT_N`/`XGPIO4` short.
The exact endpoint conflicts are TP10 at (59.20, 42.20), R50 at
(52.35, 56.80), TP9 at (52.90, 39.85), L4 at (59.25, 35.15), and the retained
`XGPIO4` In2 haul at the U21-side via. Thus a segment-for-segment layer lift is
not a legal connectivity-preserving refloor. `ACC_POWER_FAULT_N` remains fully
connected on the authoritative board; the retained ledger remains 572 open
edges / 601 raw ratsnest, and board hash remains
`b74cd3c059c50bc4edeb7ba17b6b20a2067abe19ae31e159bc6d5c517f757b24`.

The bounded optional-obstacle placement transaction was characterized on
2026-09-02 and rejected without changing the authoritative board. Moving `TP9`
from (52.25, 39.25) to (49.50, 39.25), `TP10` from (58.50, 42.75) to
(63.50, 42.75), and `R50` from (51.525, 57.735) to (49.50, 57.735) clears all
three previously measured TP9/TP10/R50 conflicts. Straight In3 replacements of
the same two removed `ACC_POWER_FAULT_N` segments then eliminate those endpoint
violations, but real refilled KiCad DRC still rejects the transaction at exactly
the two fixed obstacles: the (59.25, 35.15) via is only 0.045 mm from `L4.2`
and has only 0.195 mm hole clearance, while the (59.20, 42.20) via shorts the
retained `XGPIO4` In2 haul. The moved optional parts introduce no other
geometric DRC class. Therefore optional-part placement alone cannot produce a
legal fault refloor, and no placement or copper was promoted. The authoritative
ledger remains 572 retained open edges / 601 raw ratsnest and board hash remains
`b74cd3c059c50bc4edeb7ba17b6b20a2067abe19ae31e159bc6d5c517f757b24`.

The explicit offset-landing enumeration on 2026-09-02 closes that proposed
segment-local tactic. `enumerate_acc_fault_landings.py` withdraws only the
U21-side fault segment in scratch, replays the proven TP9/TP10/R50 moves, and
uses the established routing geometry engine at 0.025 mm resolution to search
for B.Cu-reachable, all-copper-layer-clear 0.60/0.30 mm signal-via sites within
3.0 mm of both old endpoints. With 0.20 mm signal width/clearance, 0.25 mm hole
clearance, and 0.30 mm material separation between reported sites, both
`(59.25,35.15)` and `(59.20,42.20)` return zero sites and therefore zero
distinct landing pairs. A clean rerun is byte-identical, and the authoritative
board remains unchanged at
`b74cd3c059c50bc4edeb7ba17b6b20a2067abe19ae31e159bc6d5c517f757b24`.

The complete-branch fitted-pad escape screen on 2026-09-02 establishes the
replacement framework's missing prerequisite. After withdrawing all 57 fault
tracks in scratch and replaying the characterized TP9/TP10/R50 moves,
`enumerate_acc_fault_pad_escapes.py` found ordinary B.Cu-to-In3 0.60/0.30 mm
through-via sites from every actual fitted pad: `R103.2` 96, `TP27.1` 96,
`TP33.1` 94, `U20.6` 36, `U22.6` 60, and `U3.18` 24. A clean rerun produced
byte-identical JSON evidence. The authoritative board remained byte-identical
at `b74cd3c059c50bc4edeb7ba17b6b20a2067abe19ae31e159bc6d5c517f757b24`.
Thus the fitted endpoints are not intrinsically boxed after complete branch
withdrawal; the closed tactic was preserving its obsolete intermediate
landings.

The complete replacement transaction was closed in scratch on 2026-09-02 by
`route_acc_fault_branch_scratch.py`. It reserves mutually legal 0.60/0.30 mm
through-via escapes from all six fitted pads, then uses a shortest-edge-first
tree. Four joins close on In3; the locally blocked `U3.18`--`TP33.1` join closes
on In2 in 2.344 mm. All six pads form one branch through five joins. A real
zone-refilled KiCad DRC returns exactly the accepted inherited classes: 199
footprint-library, 5 hole-clearance, and 1 solder-mask bridge, with no new
clearance, shorting, crossing, annular, via-diameter, or dangling report. A
clean rerun returns the same reservations, joins, lengths, and DRC signature.
The authoritative board remains byte-identical at
`b74cd3c059c50bc4edeb7ba17b6b20a2067abe19ae31e159bc6d5c517f757b24`.

The atomic power transaction screen on 2026-09-02 advances the wall to the
package-neck contract. `route_acc_power_transaction_scratch.py` replays the
complete legal fault replacement, joins U21.6 locally to C65.1, and reserves
compliant 0.90/0.40 mm power vias at C65.1, R99.1, C66.1, TP28.1, and U22.2.
Four inner-layer joins close the tree, so all six fitted `ACC_5V_RAW` pads have
a complete scratch topology. In particular, U22.2 is no longer boxed after the
fault refloor; its legal power via lands at (52.600, 43.000) mm.

Real refilled KiCad DRC proves that the remaining failure is intrinsic to the
U21 package launch. A 0.40 mm trace leaving U21.6 has only 0.125 mm clearance
to adjacent switch-node pad U21.5, below the 0.200 mm requirement. A short
0.25 mm by 0.45 mm B.Cu package neck removes that direct conflict, but the
blanket `ACC_5V minimum width` rule rejects the neck; widening after 0.45 mm is
still 0.1709 mm from U21.5. Thus neither moving optional obstacles nor another
inner-layer permutation can satisfy the present simultaneous 0.40 mm minimum
width and 0.20 mm clearance at this fixed 0.15 mm pad-to-pad package geometry.
The authoritative board remains unchanged at `b74cd3c0...`, with 572 retained
open edges / 601 raw ratsnest.

The atomic fault-plus-power transaction was promoted on 2026-09-02. A bounded
0.005 mm sweep found that a 0.505 mm U21.6 neck still violates clearance while
0.510 mm passes. The promoted launch is therefore 0.25 mm wide for 0.510 mm
inside U21's courtyard, then immediately widens to the required 0.40 mm. U21
was added to the existing fine-pitch package-neck width rule alongside the
identical U13 TPS61023 package; the general `ACC_5V` width and 0.25 mm routed
clearance rules remain unchanged outside the courtyard.

The transaction replaces the complete `ACC_POWER_FAULT_N` branch, moves only
optional `TP9`, `TP10`, and `R50`, and closes all six fitted `ACC_5V_RAW` pads
using five 0.90/0.40 mm power vias. Retained open edges move exactly 572 -> 567
and raw ratsnest 601 -> 596; `ACC_5V_RAW` alone changes from five open edges to
zero and no retained net regresses. The authoritative refilled full-board DRC
signature remains exactly 199 footprint-library, 5 inherited hole-clearance,
and 1 inherited solder-mask-bridge report, with no clearance, short, crossing,
width, via, dangling, or schematic-parity regression. Board hash:
`ab4569487b781a164f14d392f7c1159c48fefbdad40522ced42e4af78a71c5b4`.

The first downstream `ACC_5V_SW` screen on 2026-09-02 is characterization-only.
The retained ledger proves seven isolated fitted pads / six open edges:
`U22.5`, `C38.1`, `C67.1`, `TP29.1`, `TP42.1`, `J5.1`, and `J5.24`.
`route_acc_5v_sw_scratch.py` first tested an ordinary 0.40 mm / 0.25 mm-clearance
tree with 0.90/0.40 mm power vias.  The direct transaction stops at U22.5 with
`NO_LEGAL_ESCAPE`: the fixed fine-pitch load-switch output cannot own an
ordinary power via in its package pocket.

The next bounded alternative reused the accepted U21 package-neck pattern: a
0.25 mm local launch from U22.5, widening immediately to 0.40 mm, with nearby
output capacitor C67 intended to own the compliant via.  This advances the
same deterministic screen to C67.1, which also returns `NO_LEGAL_ESCAPE` before
any inner-layer join.  Two clean runs produced byte-identical JSON
(`sha256 3b20c6c52ed474d2195943cc134556a0c85758e0947698daa2afa492067c02b5`)
and the real refilled DRC stayed exactly at the accepted 199 footprint-library,
5 inherited hole-clearance, and 1 inherited solder-mask-bridge reports.  The
authoritative board remains byte-identical at `ab456948...`; accepted U22,
`ACC_5V_SW_EN`, fault, `ACC_5V_RAW`, XGPIO4/5, and battery copper were untouched.

Next, run a bounded C67 placement/landing screen that keeps the capacitor close
to U22 output and preserves its return loop, then replay this complete tree.
If no legal C67 landing exists within that electrical placement envelope, test
a local TP29-owned via branch; do not retry the disproven direct U22.5 via.

The bounded C67 screen on 2026-09-02 corrected a harness-level face assumption:
`C67`, `TP29`, and `TP42` are F.Cu parts, while `U22` and `C38` are on B.Cu.
The original all-B.Cu reservation therefore described the present placement,
not congestion.  The face-aware harness flips C67 to the U22 face and screens
six 0.5 mm-grid placements within 4.4 mm of U22.5.  Every placement reserves all
four SMD exits and completes the six-join fitted-pad tree with ordinary
0.90/0.40 mm power vias; the wall is no longer via capacity or inner-layer
connectivity.

None of the six is promotable as drawn.  Real zone-refilled KiCad DRC attributes
one expected width report to the 0.5125 mm U22.5 package neck in every case; the
Demo DRU package-neck exception currently names U13/U21 but not U22.  Each
straight U22-to-C67 trunk also intersects either C67.2/GND or the retained
`ACC_DETECT_N` B.Cu haul.  This closes blind C67 translation and proves the next
bounded alternative: add U22 to the same tightly courtyard-scoped 0.25 mm neck
contract, then route the B.Cu launch around C67.2 and `ACC_DETECT_N` before
replaying the now-proven face-aware tree.  Do not move or withdraw the retained
detect branch.  The authoritative board remains byte-identical at `ab456948...`.

The recovered `ACC_5V_SW` transaction was promoted on 2026-09-02.  U22.5 uses
the minimum measured 0.25 mm by 0.5125 mm package-local neck before widening to
the unchanged 0.40 mm `ACC_5V` floor; U22 was added only to the existing
courtyard-scoped fine-pitch power-package neck rule.  The remainder of the
route uses 0.40 mm copper and five ordinary 0.90/0.40 mm power vias.  All seven
fitted pads (`U22.5`, `C38.1`, `C67.1`, `TP29.1`, `TP42.1`, `J5.1`, and
`J5.24`) are one copper island, including both required Community Port output
contacts.

The promoted board delta is add-only: 20 tracks, five vias, 73.507 mm, all on
`ACC_5V_SW`; no footprint, accepted copper, or zone was removed or moved.
Retained open edges move exactly 567 -> 561 and raw ratsnest 596 -> 590, with
`ACC_5V_SW` alone changing from six open edges to zero and no retained net
regressing.  The authoritative zone-refilled full-board DRC remains exactly
199 footprint-library, 5 inherited hole-clearance, and 1 inherited
solder-mask-bridge report, with no clearance, short, crossing, width, via,
dangling, or schematic-parity regression.  `ACC_5V_SW_EN`, the independent
boost enable, the fault branch, XGPIO4/5, RGB, and retained battery safety
copper remain connected.  Board hash:
`209987cc3ab432dd6d2bb6c1ff5dfee0b8c0983bc77faace5db5c1904a100934`.

Next, close the coherent `ACC_3V3_SW` switched-output cluster.  It is the
highest-leverage remaining accessory-power fabrication blocker at 14 retained
open edges; preserve U20, its fault branch and safe-state enable, both J5 rail
contacts, and the accepted 5 V transaction.

The first bounded `ACC_3V3_SW` screen on 2026-09-02 is characterization-only.
The fitted-pad ledger confirms 15 isolated pads / 14 open edges.  A generic
face-aware 0.40 mm tree immediately proves U20.5 has no ordinary power escape;
reusing the accepted TPS22950 0.25 mm by 0.5125 mm package-neck pattern clears
U20.5.  The same issue occurs at U16.8; an equally short package-local launch
then reserves all ten SMD escapes, and the scratch forest completes six joins
before the shortest C63.1-to-R63.1 In3 edge returns `NO_PATH`.  Real refilled
DRC on the generic failed-prefix case remains exactly at the accepted 199
footprint-library, 5 inherited hole-clearance, and 1 inherited solder-mask-
bridge reports.  Later incomplete prefixes show only expected neck-width,
dangling-via, and open-forest collision artifacts and are not promotable.

`route_acc_3v3_sw_scratch.py` now preserves this result and bounds alternate-
edge spanning-tree search across the complete finite 15-anchor graph.

The exhaustive alternate-edge screen on 2026-09-02 corrects the apparent
C63/R63 wall.  After 28 rejected corridors it finds all 14 required joins: the
two forest components bridge through `U20.5` to `J8.2`, and the remaining
long-haul branches close through `Q10.1` and `J5.3`.  The inner-layer spanning
tree is therefore feasible without moving retained copper.

The candidate is not promotable because the two manually seeded package-neck
landings precede the generic reservation gate.  Real refilled DRC rejects the
U20 via at `(50.250,64.750)` against retained `ACC_3V3_ILIM`.  It rejects the
U16 via at `(62.500,55.725)` against adjacent `U16.7/EXT_SDA_BUF`, retained
`XGPIO4` on In2, and retained `ACC_5V_SW` on In3.  The only two width reports
are the expected 0.5125 mm package necks; no DRU exception was added because
their landing geometry is not yet legal.  Thus the next bounded task is an
explicit face-aware landing enumeration for `U20.5` and `U16.8`, followed by
replay of this now-proven full spanning tree.  Do not retry either rejected
fixed via and do not withdraw the accepted ILIM, XGPIO4, SDA, or 5 V copper.

The authoritative PCB remains byte-identical at `209987cc...`; no owner
decision is open.

The recovered landing-enumeration candidate after `612b29a` closes the complete
15-pad tree and passes the authoritative refilled KiCad gate. It is promoted as
68 add-only tracks and eleven 0.90/0.40 mm through-vias, all on `ACC_3V3_SW`;
there are zero missing accepted copper objects, zero placement changes, and no
new DRC class. Both Community Port contacts and Qwiic are in the same connected
component as U20.5. The route and its bounded U20/U16 package-neck rules are
pinned in `AQROOT_DEMO_ACC_3V3_SW_ROUTE.md`; the authoritative board hash is
`fd346ae6...`. The prior fixed-landing rejection remains useful negative
evidence, but no longer describes the live routing state.

Manufacturing export resumes after retained routing closes; population-flag
synchronization and MPN coverage remain later release blockers.

The recovered `BQ25185_SYS` scratch harness was bounded and characterized on
2026-09-02.  A 0.050 mm search grid reserves escapes from all 13 fitted pads,
including the charger, main regulator, accessory boost, switch, and local
capacitors.  The outer-layer shortest-edge forest closes eight joins but leaves
four components: the U12/capacitor group, the U21/L4/C64/C33 group, `U11.1`,
and `SW9.2`.  It is therefore not a promotion candidate.

Real refilled KiCad DRC localizes the fixed launch defects.  The explicit
`U11.1` north launch is only 0.047 mm clear of `C23.2` and 0.200 mm clear of
the retained `BAT_PROTECTED_P` corridor, below the 0.200 mm SYS and 0.300 mm
D-269 contracts.  The explicit `U21.3` launch is 0.2126 mm clear of retained
`ACC_DETECT_N`, below the 0.250 mm SYS routed-clearance rule.  One unused
F.Cu-to-B.Cu reservation remains dangling in the incomplete forest.  The
authoritative PCB remains byte-identical at `fd346ae6...`; no accepted copper,
placement, rule, or `hardware/beta-v2/` file changed.

Next, enumerate package-local legal launch anchors for `U11.1` and `U21.3`
instead of retrying their disproven fixed north launches, then reserve an
ordinary power-via/inner-layer bridge between the four proven components.
Preserve the D-269 battery corridor, `ACC_DETECT_N`, and all accepted accessory
power copper.  No owner decision is open.

The focused package-launch enumeration on 2026-09-02 closes the generic radial
escape tactic. `enumerate_bq25185_sys_launches.py` applies the actual local
width/clearance contracts on a 0.025 mm grid and searches reachable ordinary
0.90/0.40 mm B.Cu-to-In3 power-via sites. `U11.1` has zero generic escapes at
0.20 mm width / 0.30 mm D-269 clearance, dominated by adjacent `U11.2` (57
blocked samples). `U21.3` has zero at 0.25 mm / 0.25 mm, dominated by adjacent
`U21.2` (48) and `U21.1` (7). The authoritative board remains byte-identical at
`fd346ae6...`; accepted battery, accessory-power, RGB, and XGPIO4/5 copper is
untouched.

This does not prove the fixed packages unroutable: both are fine-pitch lands
whose accepted solution class is a tightly courtyard-scoped directional neck,
as already used for U20/U21/U22 power pins. Next, add a bounded angular/length
directional-neck sweep for `U11.1` and `U21.3`, immediately widen to their 0.50
mm SYS and 0.80 mm peak-feed trunks, and real-DRC each candidate against the
D-269 corridor and `ACC_DETECT_N`. Replay the four-component inner-layer bridge
only after both launches pass. Do not retry generic `reserve_escape`, the fixed
north launches, or relax either clearance contract. No owner decision is open.

The recovered directional-neck sweep was completed on 2026-09-02. The bounded
5-degree / 0.025 mm enumeration tests every straight package-local neck from
0.20 through 1.50 mm, immediately widens to the required 0.50 mm (`U11.1`) or
0.80 mm (`U21.3`) trunk, and accepts only a trunk ending at a legal ordinary
0.90/0.40 mm through-via. Neither pad has a direct radial neck/trunk/via result.
For `U11.1`, 352 otherwise-clear ray endpoints lack an all-layer via site; for
`U21.3`, 702 do. The finite monotonic-prefix stopping rule makes a clean replay
complete in about two minutes while preserving exhaustive coverage of the
declared rays and lengths. The authoritative PCB remains byte-identical at
`fd346ae6...`; no DRC rule or clearance contract changed.

This closes direct radial ordinary-via placement, not the SYS route or the
fine-pitch launch class. The next highest-leverage bounded task is to retain the
legal directional neck/trunk anchors and enumerate short B.Cu doglegs to nearby
ordinary through-via sites. Only after both package ends have legal sites should
the already-proven four-component inner-layer bridge be replayed. Do not retry
the fixed north launches, generic radial escape, or a via exactly at the ray
endpoint. Blind/microvias remain excluded absent an owner manufacturing
decision; no owner decision is currently open.

The recovered dogleg-landing sweep was completed and replayed cleanly on
2026-09-02. It retains every legal directional neck/trunk anchor from the
previous screen, then searches 0.25--2.00 mm full-width B.Cu doglegs at
5-degree and 0.050 mm resolution for an ordinary 0.90/0.40 mm through-via
site. Both package walls now have solutions: `U11.1` exposes 302 legal anchors
and the bounded result cap of 48 candidate landings; `U21.3` exposes 526
anchors and 48 candidate landings. The first ranked results are respectively a
0.325 mm, 55-degree neck plus 0.250 mm trunk and 0.350 mm dogleg to
`(66.9773,79.3185)`, and a 0.875 mm, 180-degree neck plus 0.250 mm trunk and
0.250 mm dogleg to `(56.0480,39.6349)`.

Two clean runs produced byte-identical JSON (`104fe4e3...`). The authoritative
PCB remains byte-identical at `fd346ae6...`; no accepted copper, placement, or
rule changed. This closes the ordinary-via landing search at both package
walls but is still characterization, not routed copper: the geometric screen
does not replace real KiCad DRC or connectivity validation.

Next, instantiate the shortest ranked landing at each wall in scratch, replay
the already-proven four-component `BQ25185_SYS` inner-layer bridge, and promote
only a complete 13-pad tree that passes the authoritative refilled full-board
KiCad DRC, fitted-pad connectivity, D-269, and accepted-copper preservation
gates. If either first-ranked landing fails real DRC, advance through the
persisted ranked candidates instead of reopening the closed radial searches.
No owner decision is open.

The inner-layer replay on 2026-09-02 closes all 13 fitted pads with twelve
successful joins, but the authoritative real KiCad gate rejects the U11.1
launch: its 0.20 mm package neck is exactly 0.2000 mm from retained
`BAT_PROTECTED_P`, while D-269 requires 0.3000 mm. This is structural at the
adjacent package breakout, so advancing through the other ranked 0.20 mm-local
neck candidates cannot change the limiting clearance. The landing enumerator
now applies 0.300 mm to the U11.1 neck itself and will no longer emit those
false-positive candidates. U21.3 and the complete ordinary-through-via I2/I3
spanning framework are proven reusable; no candidate copper was promoted and
the authoritative board remains unchanged.

The corrected deterministic replay confirms the boundary: U11.1 has zero
legal anchors/candidates (all 72 angular prefixes stop at adjacent U11.2),
while U21.3 retains 526 anchors and 48 bounded candidates. The authoritative
board hash remains `fd346ae6...`.

This is the fifth consecutive non-promoting iteration on the unchanged
`BQ25185_SYS` wall, so the wall is PARKED under the autonomy policy. Revisit it
only after materially changed surrounding geometry, an approved package-local
rule treatment that preserves D-269's safety intent, or a manufacturing-layer
decision. The next bounded iteration must select an independent unrouted
Demo-required net from the routing ledger and make measurable board progress;
do not spend another iteration rescreening this unchanged charger breakout.
No owner decision is currently open.

The next independent increment on 2026-09-02 promotes the local SX1262 module
control strap `DIO2_TXEN`. `route_local_two_pad.py` is a deliberately small
allowlisted harness for deterministic same-face, two-pad Demo nets; its first
use joins adjacent U8.7/U8.8 with three 0.20 mm B.Cu segments (2.320 mm, zero
vias). The authoritative refill and full-board KiCad DRC retain exactly the
accepted 199 footprint-library, 5 inherited hole-clearance, and 1 inherited
solder-mask-bridge reports, with no attributable violation. The fitted pads
are one copper island, ratsnest falls 576 to 575, and an object multiset proves
zero accepted track/via removals or changes and exactly those three additions.
`hardware/beta-v2/` remains byte-identical. Board hash after refill:
`f7b5cda56285d503df16a96a6ef4a68df5a6f979e7b1452b1c63c90160ad3ed0`.

The next highest-leverage independent blocker is the adjacent local power-tree
pair `MAX17048_ALRT_N` (TP11.1/U14.5), followed by other short one-edge local
nets. Keep `BQ25185_SYS` parked until its revisit conditions are met. The RGB
replacement nets, both public XGPIOs, accessory switch enables, and accepted
power/battery copper remain unchanged; no owner decision is open.

The bounded follow-up first closes the direct `MAX17048_ALRT_N` tactic: both
ends are on B.Cu, but the 0.20 mm same-face router finds no legal corridor;
F.Cu is inapplicable because TP11 is a back-side SMD pad. The board stayed
unchanged during both scratch screens. The next coherent local alternative
promotes the symmetric `NFC_MATCH_A` and `NFC_MATCH_B` pair instead. Each arm
is a straight 1.900 mm B.Cu connection with three 0.30 mm segments and zero
vias, satisfying the existing equal-arm/minimum-width NFC rule.

The refilled full-board KiCad gate retains exactly 199 footprint-library, five
inherited hole-clearance, and one inherited solder-mask-bridge reports, with
no attributable violation. Both two-pad nets are single copper islands,
ratsnest falls 575 to 573, and the board diff is exactly six add-only B.Cu
segments on the two allowlisted nets; no zone, via, placement, net assignment,
or accepted copper changes. `hardware/beta-v2/` remains byte-identical. Board
hash after refill: `f449e932ee7374cf6377f75bb7b3624f3a16489b1bd43c1a3d234776d2342609`.

Next, use the fitted-pad ledger to select another bounded local connection;
do not retry `MAX17048_ALRT_N` with the direct same-face tactic and keep
`BQ25185_SYS` parked. Manufacturing export remains premature while 101
retained multi-pad nets are still open. No owner decision is open.

The next independent increment on 2026-09-02 promotes `ILIM_VSET`, the local
BQ25185 charger input-limit programming connection from `R36.1` to `U11.7`.
The deterministic two-pad framework adds five 0.20 mm B.Cu segments (4.809 mm,
zero vias). The authoritative refilled full-board KiCad DRC remains exactly
199 footprint-library, five inherited hole-clearance, and one inherited
solder-mask-bridge report, with no attributable violation; schematic parity
was enabled. Both fitted pads are one copper island, retained open edges move
544 -> 543, raw ratsnest 573 -> 572, and the PCB delta is add-only. Accepted
battery and accessory-power copper, the routed RGB replacements, XGPIO4/5,
and `ACC_5V_SW_EN` remain untouched. Board hash:
`654a9ff75d8e7ff8853297e4b5bd1d4d1f15d8b81bfc7199acec87518bfa4ff1`.

Next, select another independent short fitted-pad edge from the ledger;
`USB_D_ESD_N` is the shortest uncharacterized non-charger candidate. Preserve
the USB differential topology and do not treat a single-leg route as a
promotable pair unless skew/coupling review passes. Keep `BQ25185_SYS` parked.
Manufacturing export remains premature while 100 retained multi-pad nets are
open. No owner decision is open.

The bounded `USB_D_ESD_N/P` screen on 2026-09-02 closes the independent-leg
tactic without changing the authoritative board. `route_usb_esd_pair_scratch.py`
routes both local ESD-to-series-resistor legs sequentially on F.Cu using the
locked 0.23 mm USB width and 0.20 mm clearance. Both routes close with zero
vias, at 13.513695 mm for N and 11.618521 mm for P (1.895174 mm skew).

The real zone-refilled full-board KiCad DRC rejects that topology with exactly
one attributable `diff_pair_gap_out_of_range` error: the two independent
detours separate by 0.7246 mm, above the locked 0.24 mm maximum. All other DRC
classes remain the accepted 199 footprint-library, five inherited hole-
clearance and one inherited solder-mask-bridge reports. Two clean runs produce
byte-identical JSON (`sha256 b2b98236dd9f190d7e48a4efce1cd9d158f5df70ea1da84bf148bdd719b79073`).
The authoritative board remains byte-identical at `654a9ff7...`; retained open
edges remain 543, raw ratsnest 572, and accepted USB, battery, accessory-power,
RGB and XGPIO4/5 copper is untouched.

Next, implement a coordinated paired-path primitive for these two local legs:
0.23 mm width, fixed 0.20 mm gap, F.Cu only, zero vias, with real KiCad pair-gap,
uncoupled-length and skew review. Do not retry the disproven independent-leg
tactic. Keep `BQ25185_SYS` parked. Manufacturing export remains premature while
100 retained multi-pad nets are open; no owner decision is open.

The coordinated follow-up promotes both local USB ESD legs together.  It keeps
the 0.23 mm traces entirely on F.Cu with zero vias, normalizes the shared
corridor inside the 0.18--0.24 mm pair-gap contract, and leaves only the
placement-required endpoint splays uncoupled.  Final lengths are 13.513695 mm N
and 11.878490 mm P; the 1.635205 mm skew is below the already accepted 2.4 mm
intrinsic placement skew and the design intentionally requires no Full-Speed
USB length matching.  Clean replays have identical deterministic evidence.

The authoritative zone-refilled full-board KiCad gate reports exactly the
accepted 199 footprint-library, five inherited hole-clearance and one inherited
solder-mask-bridge issues and no attributable class.  Both nets are single
copper islands; retained open edges fall 543 to 541 and raw ratsnest 572 to
570.  The board delta is exactly 21 add-only F.Cu segments on the pair, with no
accepted copper, placement, via, net assignment, rule, or `hardware/beta-v2/`
change.  Board hash: `103a102c4ecf3bce0f5dca28f6266dd986e094f4256d8c3c8d7d650032ce369c`.

Next, route `/USB_D_MCU_N` and `/USB_D_MCU_P` as one coordinated F.Cu,
zero-via transaction and review the whole connector-to-MCU USB pair.  Do not
promote an independently routed leg.  `BQ25185_SYS` remains parked;
manufacturing export remains premature while 98 retained multi-pad nets are
open, and no owner decision is open.

The next bounded screen closes the generic independent-leg tactic for the
MCU-side USB pair: `/USB_D_MCU_N` has no legal F.Cu path at either 0.050 or
0.025 mm grid resolution, before adding the P leg. No USB copper was promoted.
A genuinely coordinated corridor primitive remains the required next USB
step; do not retry the generic single-leg router or promote one leg alone.

The same iteration extends the local two-pad framework with explicit
schematic-DNP pad exclusion and promotes `DISP_SDO` from fitted `J1.33` to
`TP36.1`, leaving DNP `R112.1` outside the routing obligation. The route is
four add-only 0.20 mm F.Cu segments (4.649 mm), with zero vias and zero removed
accepted copper objects. The authoritative refilled full-board KiCad gate
retains exactly 199 footprint-library, five inherited hole-clearance, and one
inherited solder-mask-bridge report, with no attributable violation. The
fitted ledger moves 541 to 540 open edges, 570 to 569 raw ratsnest, and 98 to
97 open retained nets. All accepted USB, battery, accessory-power, RGB, and
XGPIO4/5 copper remains unchanged; `hardware/beta-v2/` is untouched. Board
hash: `4a6e12756b4fbbc9269a6f18256bc055485740c4d4ecf178455c7d20498a2306`.

Next, build the coordinated MCU-side USB corridor primitive and review the
whole connector-to-MCU pair. `BQ25185_SYS` remains parked. Manufacturing
export remains premature while 97 retained multi-pad nets are open; no owner
decision is open.

The next bounded iteration reconfirmed why the remaining MCU-side USB pair
needs a new primitive: the resistor endpoints are ordered N/P from left to
right while the ESP32 endpoints are P/N, and the generic empty-pair F.Cu
screen still cannot route the N leg at either 0.050 or 0.025 mm resolution.
A coordinated solution must explicitly handle that endpoint crossover while
keeping the pair within its coupling contract; fixed-offset reuse of the ESD
pair and single-leg promotion remain closed.

The independent coherent alternative promoted both USB-C configuration
straps. `Net-(J3-CC1)` connects `J3.A5` to `R31.1` in six F.Cu segments
(11.474888 mm), and `Net-(J3-CC2)` connects `J3.B5` to `R30.1` in eight F.Cu
segments (14.066030 mm). All 14 segments are 0.20 mm wide; there are no vias,
no missing accepted copper objects, and no placement or rule change. The
authoritative refilled, schematic-parity KiCad gate remains exactly 199
footprint-library, five inherited hole-clearance, and one inherited solder-
mask-bridge report. Retained open edges fall 540 -> 538, raw ratsnest 569 ->
567, and open retained nets 97 -> 95. Board hash: `c052390c09b542cbcff7904aa6518bc42f41026aa892e30c6c94405dfa8373e2`.

A same-face `ISET` screen was also rejected before promotion: `U11.8` has no
legal 0.20 mm B.Cu escape between adjacent charger lands, existing copper, and
the board edge. Do not retry that generic tactic. `BQ25185_SYS` remains parked.
The next highest-leverage fabrication blocker is the endpoint-order-aware
coordinated `/USB_D_MCU_N` and `/USB_D_MCU_P` transaction; no owner decision
is open and manufacturing export remains premature.

The bounded endpoint-order crossover screen on 2026-09-02 proves that both MCU
legs are geometrically routable when each uses a symmetric 0.60/0.30 mm
two-via hop: N closes on In2 in 22.027355 mm and P closes on In3 in 24.527890
mm. Real refilled KiCad DRC rejects the complete transaction with five
`items_not_allowed` reports from the locked rule that forbids USB copper on
In2/In3; all other reports remain the accepted 199 footprint-library, five
hole-clearance, and one solder-mask-bridge classes. The authoritative board is
unchanged. Do not weaken the USB layer contract or retry an inner-layer
crossover.

Next, run a bounded R33/R34 order/refloor impact screen. It must first determine
whether endpoint order can be corrected while preserving the accepted
connector-side ESD pair copper; if not, close that tactic without moving parts
and return to an explicitly coupled F.Cu perimeter corridor search. Do not
delete accepted USB copper merely to make the resistor order convenient.

The bounded R33/R34 order screen on 2026-09-02 closes the rigid-pivot refloor
without changing the board. `screen_usb_series_order.py` pins each resistor's
pad 1 to the exact accepted ESD-side copper anchor and enumerates all 16
orthogonal pose combinations twice with byte-identical evidence. None reverses
the MCU-side endpoint order. More strongly, the pad-1 anchors are 3.596114 mm
apart in X and each 0603 pad pair has a 1.650000 mm centre radius, so even
arbitrary continuous rotations leave P pad 2 at least **0.296114 mm** to the
right of N pad 2. The resistor pair therefore cannot correct the N/P crossover
while preserving both accepted pad-1 anchors. Swapping the references or net
identities would instead misconnect the already routed ESD pair and is not an
electrical refloor.

The authoritative PCB remains byte-identical at `c052390c...`; no footprint,
copper, rule, or schematic change was promoted. The next bounded USB tactic is
an explicitly coupled F.Cu perimeter/circumnavigation search that handles the
reversed endpoints as a pair. Do not retry rigid R33/R34 pivots, inner-layer
hops, the generic independent-leg router, or delete the accepted ESD copper.
If that planar search cannot close, park this materially unchanged USB wall and
select another retained net from the fitted-pad ledger.

The bounded whole-board F.Cu perimeter screen on 2026-09-02 closes that final
USB tactic without changing the board. `screen_usb_mcu_perimeter.py` searches
all 4,444,481 legal-grid cells at 0.050 mm resolution with the locked 0.23 mm
width, 0.20 mm clearance, zero vias, and both insertion orders. Each polarity
has eight legal resistor-side launches and only two MCU-side launches. All four
destination-facing ranked launch combinations independently return
`NO_FULL_BOARD_FCU_PATH` before the other polarity is inserted. Two clean runs
are byte-identical (`sha256 2da46557b16b626cd400d4f51d2a4837198e2c0280782c238d21b7cf8efcbdf5`).

The scratch full-board refill/DRC remains exactly 199 footprint-library, five
inherited hole-clearance, and one inherited solder-mask-bridge reports, with no
attributable class. The authoritative PCB remains byte-identical at
`c052390c...`; accepted USB ESD, battery, accessory-power, RGB, and XGPIO4/5
copper is untouched. Together with the rejected inner-layer crossover and the
bounded resistor-pivot proof, the materially unchanged MCU-side USB wall is now
PARKED. Do not retry those tactics or weaken the USB layer/coupling contract.

The next independent bounded task is a coordinated symmetric route screen for
the local `NFC_RFO1`/`NFC_RFO2` pair (one retained open edge each, 4.263 mm and
5.538 mm spans). Preserve the differential NFC output geometry and tuning
network; do not promote one arm alone. The fitted ledger remains 95 open nets /
538 retained open edges, and no owner decision is open.

The coordinated NFC output-arm screen on 2026-09-02 is characterization-only.
The initial 0.20 mm-clearance replay found that route order matters: RFO1-first
boxes U9.15, while RFO2-first geometrically closes both arms. Real KiCad DRC
correctly rejected that replay with three `NFC_RF` clearance violations because
the authoritative routed-clearance contract is 0.25 mm. The harness was then
corrected rather than weakening the rule or promoting partial copper.

At the correct 0.30 mm width / 0.25 mm clearance, both bare launches return
`NO_LEGAL_ESCAPE`. U9.13 and U9.15 are 0.30 mm-wide lands on 0.50 mm pitch, so a
full-width trace has only 0.20 mm to the neighboring U9 land while it remains
inside the package perimeter. This is a package-neck wall, not a downstream
route-capacity wall. Two corrected runs reproduce the same zero-track geometry
hash and accepted refilled schematic-parity DRC signature: 199 footprint-
library, five inherited hole-clearance, and one inherited solder-mask-bridge
report. No NFC copper entered the authoritative PCB, whose hash remains
`c052390c09b542cbcff7904aa6518bc42f41026aa892e30c6c94405dfa8373e2`.

Next, measure the minimum identical neck length needed for U9.13 and U9.15 and
screen a single courtyard-scoped package-launch clearance treatment applied to
both arms. Keep 0.30 mm width and 0.25 mm clearance everywhere outside U9,
B.Cu-only routing, zero vias, and atomic pair promotion; review arm geometry and
the complete NFC tuning path before accepting it. Do not retry the disproven
global 0.20 mm-clearance tactic or promote only one arm. The ledger remains 95
open retained nets / 538 retained open edges, and no owner decision is open.

The follow-up closes and promotes the NFC output pair atomically.  The existing
DRU deliberately applies the 0.25 mm `NFC_RF` routed-clearance rule only when
neither item is a pad, so the routing framework now models that distinction:
0.20 mm to package lands and 0.25 mm to routed copper, without changing the DRU
or reducing the 0.30 mm trace width.  RFO2-first then RFO1 closes on B.Cu with
zero vias.  Both U9 launches are 0.925 mm and both inductor launches are
1.105 mm; total copper is 8.674 mm for RFO2 and 6.074 mm for RFO1.  The 2.600 mm
arm difference is imposed by the existing asymmetric placement, while the
package treatment itself is identical.

Two clean scratch runs reproduce the same routes and geometry digest
`026652a473125bde...`.  The independent refilled schematic-parity KiCad DRC
contains only 199 footprint-library, five inherited hole-clearance, and one
inherited solder-mask-bridge report.  Both RFO nets are one copper island;
retained opens fall 95→93, retained edges 538→536, and ratsnest 567→565.  The
board delta is exactly 12 add-only 0.30 mm B.Cu segments on the two RFO nets,
with no via, footprint, zone, placement, net-assignment, or accepted-copper
removal.  Battery/accessory-power, all three RGB replacements, XGPIO4/XGPIO5,
and `ACC_5V_SW_EN` remain connected; `hardware/beta-v2/` is untouched.  The
authoritative PCB hash is `ed13ce4b547085cd46b7ef01c5965e0d5fa3869581459d0965c4e0ec756efb79`.

Next, take the coherent local `NFC_RXA`/`NFC_RXB` receive pair through the same
scratch-first/full-board gate discipline, then the `NFC_XIN`/`NFC_XOUT` crystal
pair.  Preserve the full tuning path and do not revisit the parked MCU USB wall
without a material geometry change.  Manufacturing export remains premature
at 93 retained open nets / 536 retained open edges; no owner decision is open.

The next bounded increment promotes both three-pad NFC receive arms atomically.
`NFC_RXA` and `NFC_RXB` each use ten add-only 0.30 mm B.Cu segments, total
7.309798 mm, and have zero vias and zero arm-length delta. Two clean scratch
replays reproduce geometry digest `c27a31d182019135...`; generated KiCad UUIDs
vary, while the complete physical geometry is identical.

The authoritative zone-refilled schematic-parity KiCad DRC retains exactly 199
footprint-library, five inherited hole-clearance, and one inherited
solder-mask-bridge reports, with no attributable class. Both receive nets are
single copper islands; retained open nets fall 93→91, retained edges 536→532,
and raw ratsnest 565→561. The board delta is exactly 20 add-only B.Cu segments
on the two allowlisted nets, with no vias or accepted-copper removals. The full
NFC output/matching path, battery/accessory-power copper, RGB replacements,
XGPIO4/XGPIO5, and `ACC_5V_SW_EN` remain connected; `hardware/beta-v2/` is
untouched. Board hash: `c60088214d12c81dcb00c8bc3a12c933efc5d676e034153259ce75d985ca67ee`.

Next, route `NFC_XIN` and `NFC_XOUT` as one coherent crystal transaction and
review the complete oscillator geometry. Keep the MCU USB and `BQ25185_SYS`
walls parked. Manufacturing export remains premature at 91 retained open nets /
532 retained open edges; no owner decision is open.
### ACC_5V boost B.Cu core screen

`screen_acc_5v_bcu_core.py` replays `ACC_5V_LX` first after the 180-degree
`U21`/`L4` rotation, preserves the accepted five-via `ACC_5V_RAW` distribution
tree, and screens five bounded `L4` offsets.  It changes only scratch boards and
reports real refilled KiCad DRC.  The current result closes LX in every case but
proves that moving `L4` alone does not remove the rotated `L4`/`R99` courtyard
overlap; the restored straight U21.6 raw neck also crosses `ACC_DETECT_N` and
misses the power-copper clearance to LX/the accepted raw via.  The next replay
must route that neck around those fixed obstacles and include `R99` in the
minimum placement boundary.

### ACC_5V coordinated corridor screen

`screen_acc_5v_corridor_pair.py` fixes the D-418 R99 placement and bounds 12
explicit LX-inner/raw-outer B.Cu corridors without changing the authoritative
board. All cases fail the real refilled schematic-parity DRC. Increasing the
raw detour westward and southward does not clear the retained `BQ25185_SYS`
field on its return to the accepted raw tree; GND/LX/crossing and clearance
collisions are secondary. Two clean runs reproduce zero candidates, although
KiCad can label coincident geometry as short, crossing, or clearance between
runs. The planar outer-corridor family is parked. Next, screen a package-local
U21.6 transition into the existing In3 raw tree with LX retained on B.Cu before
attempting the full six-branch placement transaction.

## Shared SPI-A clock/data wall (2026-09-02)

The follow-up promotes the independently reproducible clock tree. The shared
harness now accepts `--only sck`/`--only mosi`; `--only sck` closes U1.20,
J1.36, and J2.5 with 14 add-only 0.20 mm F.Cu/In2.Cu segments and four ordinary
0.60/0.30 mm vias (72.751257 mm). Two clean candidates reproduce identical
physical geometry, and the authoritative refilled parity gate retains the
accepted 199/5/1 signature with no attributable class. MOSI remains open and
the paired adjacent-J1 family remains parked. Next, freshly rank an independent
retained net or coherent local cluster; do not retry MOSI without material
geometry change.

`route_spi_a_clock_data_scratch.py` now requires both fitted three-pad trees,
`SPI_A_SCK` and `SPI_A_MOSI`, to close in one add-only transaction.  Both launch
orders pass real refilled schematic-parity DRC with exactly the inherited
199 footprint-library, five hole-clearance, and one solder-mask-bridge reports,
and remove no accepted copper.  Clock-first closes SCK but leaves the MOSI
display branch at `NO_VIA_SITE`; data-first closes MOSI but leaves the SCK
display branch at the same wall.  Pinning the two nets to separate In2/In3
hauls does not change the result because ordinary through vias occupy all
copper layers.

No partial tree is promoted and the authoritative board remains byte-identical
at `7e20e227...`.  The next bounded tactic is to reserve distinct perimeter
fanouts for adjacent J1.34/J1.36 before either long haul, then attach U1 and J2
atomically.  If two legal barrels cannot be exposed, park the paired wall and
independently gate the already reproducible complete SCK tree.  No owner
decision is open.
