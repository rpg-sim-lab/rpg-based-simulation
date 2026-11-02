---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20261101-CLEAR-TARGET-IS-NEVER-APPLIED
phase: open
date: 2026-11-01
tags: []
---

# TCK-20261101-CLEAR-TARGET-IS-NEVER-APPLIED

## Title
`NavigationUpdate.clear_target` is never applied, so three writers that ask to clear a target leave it in place

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Found by lane B during F3 (TCK-20261031-A-SLEEPER-HOLDS-A-DOOR-OR-SERVICE-TILE), verified on origin/main e523f92b2 by the planner. `NavigationUpdate` (src/core/updates.py) has two target-clear fields: `target_clear` (line 171) and `clear_target` (line 176). The apply path reads only `target_clear` (src/engine/patches.py:284); nothing in apply reads `clear_target`. By contrast `clear_path` IS applied (patches.py:286). So every writer that sets `clear_target=True` is a silent no-op on the target:
- src/engine/movement.py:373: `clear_target=replan` (a movement replan keeps its old target);
- src/engine/blacksmith.py:250;
- src/engine/pipeline_phases/actor_validity.py:116.
actor_validity.py:76 also counts `clear_target` as a navigation proposal, so the update looks like it does something. F3 switched its own three uses to `target_clear`; it does not touch these.

## Scope
- Investigate first: for each of the three writers, what clearing the target was meant to do, and how often it fires (counts on the 3-world s42 set).
- Fix: one target-clear field. Either apply `clear_target` as `target_clear`, or remove `clear_target` and move its writers to `target_clear`; the merge (updates.py:198/203) and `is_empty` (187-189) follow.
- A test that each writer's clear actually clears the target after apply.

## Out of Scope
F3's own uses (already `target_clear`). Any change to movement replan logic beyond honouring its clear.

## Acceptance Criteria
- AC1: one target-clear field remains, and it is applied.
- AC2: per-writer counts before the fix, and a test per writer after.
- AC3: hashes are expected to move (behaviour change): deaths by cause per world on the 15-run set, with a STOP on an attributed rise; divergence entry and parity updated.

## Related Tickets
TCK-20261031-A-SLEEPER-HOLDS-A-DOOR-OR-SERVICE-TILE.

## Related Docs
docs/engine/authoritative_mutation_pipeline_contract.md; docs/core/state.md.

## Related Stored Artifacts
None.

## Related Code Areas
src/core/updates.py; src/engine/patches.py; src/engine/movement.py; src/engine/blacksmith.py; src/engine/pipeline_phases/actor_validity.py.

## Assumptions / Open Questions
After F3 and retention land (it moves hashes). Dispatch needs an owner go.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
