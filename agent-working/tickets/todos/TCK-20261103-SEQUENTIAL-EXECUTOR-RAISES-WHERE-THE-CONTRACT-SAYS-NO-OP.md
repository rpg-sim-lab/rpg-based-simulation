---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20261103-SEQUENTIAL-EXECUTOR-RAISES-WHERE-THE-CONTRACT-SAYS-NO-OP
phase: open
date: 2026-11-03
tags: []
---

# TCK-20261103-SEQUENTIAL-EXECUTOR-RAISES-WHERE-THE-CONTRACT-SAYS-NO-OP

## Title
An equivalence gap, not a breach: the sequential executor raises on a worker exception while the concurrent path turns it into the contract's no-op (Fallback Equivalence)

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P3

## Request Summary
Requested by rpg-designer on 2026-11-03, after rpg-planner-ubuntu read the contract (relayed, not checked here beyond the lines cited). The concurrent path's no-op on a worker exception follows the contract (:39-40). The sequential path raises instead, so the two aren't equivalent on a failure (Fallback Equivalence): an equivalence gap, not a breach (rpg-planner-ubuntu's correction, via lead-planner-u24).

It matters only if the no-op count from TCK-20261103-THE-CONCURRENT-AND-SEQUENTIAL-EXECUTORS-GIVE-DIFFERENT-WORLDS ever fires: with a zero count, the two paths never differ on it. Owner's answer (#715 6593673717): an undeclared read stops the run, production included, with one written contract exception; other worker errors keep the no-op, counted, and non-zero fails evidence and returns to the owner.

## Scope
1. Watch the no-op count once the executor ticket lands.
2. If it fires, decide with rpg-designer: change sequential, or change the contract. Until then no change: "sequential unchanged or stop" holds.

## Out of Scope
- The executor fix itself.
- Any change to sequential behaviour while the count is zero.

## Acceptance Criteria
- A decision is recorded when the count fires, or the ticket closes with the contract text stating the difference, on rpg-designer's word.
- Hot-loop: no unless a change follows.

## Related Tickets
- TCK-20261103-THE-CONCURRENT-AND-SEQUENTIAL-EXECUTORS-GIVE-DIFFERENT-WORLDS

## Related Docs
- docs/engine/contracts/bounded_concurrency_contract.md (:39-40, Fallback Equivalence)

## Related Stored Artifacts
- None.

## Related Code Areas
- src/engine/executor.py (`LocalSequentialExecutor`, `ConcurrentExecutionAdapter`)

## Assumptions / Open Questions
- Dispatch needs an owner yes, and nothing is dispatchable while the count is zero.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
