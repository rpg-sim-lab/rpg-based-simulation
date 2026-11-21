---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20261121-THE-GATE-PERSON-FLAG-CHECK-SILENTLY-TREATS-A-NON-STRING-FLAG-AS-A-NON-PERSON
phase: open
date: 2026-11-21
tags: []
---

# TCK-20261121-THE-GATE-PERSON-FLAG-CHECK-SILENTLY-TREATS-A-NON-STRING-FLAG-AS-A-NON-PERSON

## Title
The rpg gate's person-flag check (`_is_wild_meat_eater`) silently treats a non-string flag as a non-person; it should refuse one

## Status
OPEN

## Tier
hotfix

## Type
bug

## Priority
P3

## Request Summary
Found by the ubuntu O3 trace lane (rpg-planner-ubuntu, relayed by the ubuntu lead and lead-planner-u24, 2026-11-21). src/observability/rpg_gate_metrics.py (about :141-143) `_is_wild_meat_eater(group, person: str)` tests `person != "1"`. A caller that passes an int 1 gets True, so a person is counted as a wild meat-eater with no error. The O3 trace spy did exactly that, so its preflight counted 88/109 person-on-person hits as O3 hits. That defect was in the trace kit, not the gate. Today's gate caller (`_combat_rows`) passes `_split`'s string fields, so the gate itself is NOT affected (inspected by rpg-planner-ubuntu and rpg-planner).

## Scope
1. Make a non-str person flag a typed error (raise) in `_is_wild_meat_eater`, or normalise it at one documented place. Silent acceptance is not allowed.
2. A unit test: int 1, str "1", str "0" and None. The non-str cases raise (or normalise, as ruled); "1" is a person; "0" is not.
3. Check the other ledger-key string comparisons in rpg_gate_metrics.py for the same pattern (victim_person, outcome) and give them the same treatment.

## Out of Scope
- Any change to O3's meaning, grouping or floors.
- The O3 trace kit (fixed on the ubuntu branch).

## Acceptance Criteria
1. A non-str person flag can't be silently counted.
2. The unit test covers int/str/None.
3. The gate's outputs are byte-identical on a fixed run, since today's caller already passes str. Shown by the existing rpg_gate tool tests unchanged and green.

## Related Tickets
- TCK-20261121-MEAT-EATERS-IN-FRONTIER-LIVING-WORLD-ATTACK-PEOPLE-FORTY-TIMES-MORE-AFTER-THE-NIGHT-AND-SLOT-FIXES (the trace where the spy hit it)

## Related Docs
- docs/observability/ (the rpg gate metrics)

## Related Stored Artifacts
None.

## Related Code Areas
- src/observability/rpg_gate_metrics.py (_is_wild_meat_eater, _combat_rows, _split)

## Assumptions / Open Questions
- Raise vs normalise: raise is preferred (a silent fix hides the caller bug). Confirm at implementation.

## Durable state, lifecycle and clocks
None.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
