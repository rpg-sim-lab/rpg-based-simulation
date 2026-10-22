---
status: active
layer: economy
authority: P1
audience: agent
ticket_id: TCK-20261022-NO-MEAT-DECAYED-RECORD-FOR-A-CARCASS-RE-ADDED-ON-ITS-DECAY-TICK
phase: open
date: 2026-10-22
tags: []
---

# TCK-20261022-NO-MEAT-DECAYED-RECORD-FOR-A-CARCASS-RE-ADDED-ON-ITS-DECAY-TICK

## Title
No MEAT_DECAYED record for a carcass that a same-tick partial take re-adds on its decay tick (emitter-only, hash-neutral; (a1) of the v1 V2 split)

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P0

## Request Summary
v1 gate run 39710919027 (main e6a6a3e10) failed V2 on crowded_frontier/44 (decay records 148 vs vanished 145) and frontier_living_world/46 (139 vs 138). Trace (rpg-implementer, `/mnt/data/scratch-rpg-implementer/v1_v2_meat_trace.md`): a carcass due to decay is partly eaten the same tick (EAT, CORPSE_FOOD, accepted); the world-dynamics step has written MEAT_DECAYED from the tick-start state; `apply_plan.py` ~265-277 pops the body and re-inserts it from `corpses_add_or_update`, so the body survives a tick and the record is false (crowded/44 t1604 body 1000007 3.0; frontier/46 t2575 body 1000030 1.0). Conservation holds (residual 0).

OWNER DECISION 2026-10-22 14:07 +07 (AskUserQuestion in the rpg-planner session, "Split (Recommended)"), designer recommendation: SPLIT. (a1) = THIS ticket before v1: make the record true about the world as built, without changing the world. (b1) = TCK-20261022-A-CARCASS-EATEN-ON-ITS-DECAY-TICK-STILL-DECAYS-ON-TIME after v1 (apply order, the law), disclosed in v1 as N16.

## Scope
1. Extend the MEAT_DECAYED filter in `src/engine/economy.py` (`_without_decay_of_looted_bodies`, ~261-287): a body that is in the update's `corpses_remove` AND re-added in `corpses_add_or_update` in the same resolution gets no decay record (it did not leave; it is recorded when it actually leaves). Whole-body loot behaviour unchanged. Cover the lifecycle phase's second resolution as the existing filter does.
2. Tests: unit fixtures for the two traced cases (partial take on the decay tick -> no record that tick, record of the remainder the tick it leaves; last meat taken on the decay tick -> no meat record) plus the existing `tests/unit/engine/test_meat_decay_record_and_whole_loot.py` unchanged.
3. Parity: amend the existing MEAT-DECAYED-V2 parity entry's evidence for the re-added case (no Bible change; the decay-timing deviation is N16, owned by (b1)).

## Out of Scope
Any change to `apply_plan.py`, corpse lifecycle, decay timing or world state ((b1)). Gate metric changes (fix the emitter, never the check). v1 disclosure text (rpg-designer).

## Acceptance Criteria
- HASH-NEUTRAL PROOF (designer condition 1): `paired.py --base e6a6a3e10 --new <fix sha> --seeds 42..46 --self-check off --jobs 1`, 3 worlds, 5000 ticks, PYTHONHASHSEED=0, audit_mode: start and final hashes equal in all 15 runs and every counter equal EXCEPT the MEAT_DECAYED count/quantity, which drops by exactly 3.0 on crowded_frontier/44 and 1.0 on frontier_living_world/46 and nowhere else. Any other difference: STOP, report to rpg-planner (the split collapses; back to the owner).
- V2 0 violations on crowded/44 and frontier/46 at the fix sha (ledger check); unit tests pass; code health 0 new / 0 worse; mypy clean.
- `tools/rpg_measure/arm_child.py` hash unchanged (72320cac).

## Related Tickets
TCK-20261022-A-CARCASS-EATEN-ON-ITS-DECAY-TICK-STILL-DECAYS-ON-TIME ((b1), removes this filter); TCK-20261019-MEAT-DECAYED-IS-WRITTEN-FROM-THE-APPLIED-OUTCOME-V2 (whole-body case); TCK-20261019-RECORD-BASELINE-V1.

## Related Docs
docs/mechanics/03_economic_laws.md 3.2; docs/parity_ledger/ (MEAT-DECAYED-V2 entry).

## Related Stored Artifacts
/mnt/data/scratch-rpg-implementer/v1_v2_meat_trace.md; v2meat/focus_crowded44.json; v2meat/focus_frontier46.json (scratch; summarise into investigation.md).

## Related Code Areas
src/engine/economy.py; src/engine/world_dynamics.py (`_meat_decayed_events`); src/observability/run_ledger.py (reader only).

## Assumptions / Open Questions
- MEAT_DECAYED is read only by observability (run_ledger, rpg_gate_metrics) and world events are not in CanonicalStateHasher, so hash-neutral is expected; the proof decides.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
