---
status: active
layer: core
authority: P1
audience: agent
ticket_id: TCK-20261124-NAVIGATION-STATE-MOVES-OUT-OF-STATE-PY
phase: open
date: 2026-11-24
tags: []
---

# TCK-20261124-NAVIGATION-STATE-MOVES-OUT-OF-STATE-PY

## Title
NavigationComponent moves out of src/core/state.py into its own core module, retiring the one-line size raise

## Status
OPEN

## Tier
standard

## Type
refactor

## Priority
P2

## Request Summary
Retiring ticket for the proposed +1 line raise of src/core/state.py (1672 to 1673) caused by #996's arrived_this_attempt field (owner ask drafted 2026-11-24; record the owner's answer id here). Precedent: #715 6785100551 and TCK-20261111-SPLIT-UPDATES-PY-INTO-UPDATE-MODELS.

## Scope
1. Move NavigationComponent (state.py:496, about 83 lines) and its canonical helpers into a new core module, re-exported from src/core/state.py so every importer keeps working.
2. A pure move: an AST check shows 0 differing definitions (the updates.py precedent).
3. Old checkpoints still load (a test with a pickle that names src.core.state.NavigationComponent).
4. Lower the state.py module-length ceiling to the new size in the same change.

## Out of Scope
- Any behaviour change.

## Acceptance Criteria
1. 0 differing definitions by AST.
2. An old-checkpoint load test passes.
3. The state.py ceiling is lowered and the raise is retired; the code health check is clean.

## Related Tickets
- TCK-20261123-A-SUBJECT-REMEMBERS-WHY-A-PLACE-FAILED-AND-RECONSIDERS-IT-BY-THAT-REASON (#996)
- TCK-20261111-SPLIT-UPDATES-PY-INTO-UPDATE-MODELS

## Related Docs
- docs/plans/systemic_world/experience_memory_design.md
- docs/mechanics/04_strategic_cognition.md

## Related Stored Artifacts
- none yet

## Related Code Areas
- src/core/state.py, codebase/baselines/code_health_exceptions.jsonl

## Assumptions / Open Questions
- Filed under the owner's scope freeze (#715 7132422805): a follow-up, not part of the PR it came from.

## Durable state, lifecycle and clocks
To be set at planning.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
