---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20261021-WORKER-CHUNK-EXCEPTION-DROPS-RESULTS-WITHOUT-FAILURE-NOOPS
phase: open
date: 2026-10-21
tags: []
---

# TCK-20261021-WORKER-CHUNK-EXCEPTION-DROPS-RESULTS-WITHOUT-FAILURE-NOOPS

## Title
When a worker chunk future raises, that chunk's results are dropped with no per-entity FAILURE no-ops, which the contract requires, and future.result() has no timeout path

## Status
OPEN

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
Lead-planner-u24 found this on 2026-10-21 by reading the code on origin/main; it was not run. It does not block v1.
- worker_manager.py, around line 176: a chunk future that raises drops that chunk's results without the per-entity FAILURE no-ops the contract requires.
- future.result() has no timeout path.

## Scope
- On a chunk exception or timeout, emit one typed FAILURE no-op per entity in the chunk, so the tick stays deterministic and auditable.
- Add a bounded timeout from the existing config, with no new knob unless the contract names one.
- Tests: a raising chunk gives FAILURE no-ops for exactly its entities; a hung chunk times out the same way.

## Out of Scope
- Anything before v1. The simulation-behaviour freeze holds until the v1 record lands.

## Acceptance Criteria
- The contract's FAILURE no-op rule holds on exception and on timeout, with tests.

## Related Tickets
- TCK-20261019-RECORD-BASELINE-V1 (do after it)

## Related Docs
- docs/engine/

## Related Stored Artifacts
- none

## Related Code Areas
- src/engine/worker_manager.py (~L176), the worker failure contract in docs/engine/

## Assumptions / Open Questions
- This was read from code, not reproduced. Re-verify it before any fix.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
