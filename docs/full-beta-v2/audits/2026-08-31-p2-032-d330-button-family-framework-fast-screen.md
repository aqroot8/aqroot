# FBV2-P2-032 / D-330 — remaining button-family framework fast screen

## Result

**BOUNDED FRAMEWORK CHARACTERIZATION; NO COPPER CHANGE.** On clean pushed D-329 state,
the remaining west-button endpoints were screened without running the expensive promotion gate
on candidates that failed local geometry.

- Replaying D-328's F.Cu endpoint hop for `BTN_DOWN_N` (`R5.2↔U2.14`) and `BTN_A_N`
  (`R8.2↔U2.17`) fails `NO_PATH`: neither pair has the F.Cu corridor that made
  `BTN_RIGHT_N` legal.
- A bounded split-layer variant joined the endpoint pair on In2 or In3 while reserving F.Cu
  attachment through the same through-via anchor. Both inner layers give the same deterministic
  local result: `BTN_DOWN_N` has `NO_VIA_SITE` reachable from `R5.2`; `BTN_A_N` has
  `NO_VIA_SITE` reachable from `U2.17` at the locked 0.60/0.30 via geometry.
- No scratch candidate laid a complete connection; the full promotion gate was correctly not
  spent. The authoritative PCB/journal remain byte-identical to D-328.

The reusable button-family work is now bounded accurately: D-325 duplicate-physical-pad handling
is generic and accepted; D-328 hop-anchor is reusable only where live endpoint geometry admits
both escape sites and a join corridor. It must not be generalized across the three boxed west
endpoints. `BTN_DOWN_N`, `BTN_A_N`, and `BTN_LEFT_N` defer to the generic boxed-endpoint escape
framework rather than blind hop retries.

## Next

Proceed to the owner-prioritized bounded In2/In3 long-haul framework for saturated west XGPIO and
appropriate low-speed hauls. The unchanged D-286 full-board gate remains mandatory for promotion.

