---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20261019-V8-UNSOURCED-ADD-EXAMPLES-NAME-THE-ENTITY
phase: open
date: 2026-10-19
tags: [observability]
---

# TCK-20261019-V8-UNSOURCED-ADD-EXAMPLES-NAME-THE-ENTITY

## Title
V8's examples name each unsourced entity and its tick, the way V5's out-of-world examples already do

## Status
OPEN

## Tier
hotfix

## Type
repair

## Priority
P2

## Request Summary
The agreed V8 contract (TCK-20261013-RPG-GATE-V8-SPAWN-SOURCE-CHECK, and its format doc) says each example names the entity id and the tick, so that a red can be traced. On main, the examples are aggregate only:
- `rpg_gate_metrics._check_unsourced_adds` returns `{"adds": "<group>|unsourced", "count": n}`;
- `RunLedger._count_adds` keeps counts only.

V5 already does this properly with `out_of_world_examples`, a bounded list capped at `MAX_EXAMPLES`. Testing-planner raised this (#653 records it as a known gap).

## Scope
- In `src/observability/run_ledger.py`:
  - add `_unsourced_examples: List[Dict]`, reset in the same place as `_out_of_world_examples`;
  - in `_count_adds`, when the source is UNSOURCED and the list is below `MAX_EXAMPLES`, append `{"entity_id", "tick", "kind_group"}`. Pass the tick into `_count_adds`; the hook already has it;
  - emit `unsourced_examples` in the ledger summary, next to `out_of_world_examples`.
- In `src/observability/rpg_gate_metrics.py`, have V8 return `list(ledger["unsourced_examples"])` as its examples. The count stays the sum of the `|unsourced` adds.
- Add unit tests: the cap, field names and tick for an unsourced add, no example for a sourced add, and the reset between runs.
- Update the format doc's V8 row if its example shape is written there.

## Out of Scope
- Any change to how adds are counted, to V8's pass/fail, or to which spawns are sourced.
- testing's test_v8_fires case (a) tightening (testing-implementer, after this lands).

## Acceptance Criteria
- A run with an unsourced mid-run add makes V8 emit an example with its entity_id, tick and kind_group.
- The examples are capped at MAX_EXAMPLES. V8's counts and verdicts are identical before and after on the 3 gate worlds (seed 42).
- The simulation is unchanged: the final hash is identical. The ledger is an observer.

## Related Tickets
- TCK-20261013-RPG-GATE-V8-SPAWN-SOURCE-CHECK (V8 contract)
- testing PR #653 (records this gap)

## Related Docs
- the rpg gate format doc (V8 row)

## Related Stored Artifacts
- none

## Related Code Areas
- src/observability/run_ledger.py (`_count_adds` ~L172, `_out_of_world_examples` ~L72/L285, summary ~L303)
- src/observability/rpg_gate_metrics.py (`_check_unsourced_adds` ~L200)

## Assumptions / Open Questions
- The harness hash may move only because of the new field; testing-planner agreed to that.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
