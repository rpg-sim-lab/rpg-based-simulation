---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20261021-WORK-ITEM-PRIORITY-LOOKUP-KEY-MISMATCH
phase: open
date: 2026-10-21
tags: []
---

# TCK-20261021-WORK-ITEM-PRIORITY-LOOKUP-KEY-MISMATCH

## Title
The executor looks up local_priority by a packet work_id format that never matches the scheduler's WorkItem work_id, so the priority is always 0. The kernel's sort order also contradicts bounded_concurrency_contract §3.

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
- The WorkItem work_id is "{tick}:{kind_lower}:{id}" (scheduler.py:143).
- executor.py:335/340 looks the priority up by the packet work_id "{tick}:{id}:{KIND}" (lines 189/290), so local_priority is always 0.
- It is latent today: priority is never set, and only CRITICAL work is produced.
- kernel.py:606 sorts by -local_priority (higher first), while bounded_concurrency_contract.md §3 says lower is earlier.

## Scope
- Use one work_id builder for both sides, so the keys match.
- The contract or the code decides the sort direction; fix the other and update the parity entry.
- Add a test: a set priority changes the execution order as the contract says.
- Determinism: the final hash must be unchanged on the 3 gate worlds, since priority is 0 today. If it moves, stop and report.

## Out of Scope
- Anything before v1. The simulation-behaviour freeze holds until the v1 record lands.

## Acceptance Criteria
- The keys match.
- The sort order matches the contract, with a test.
- The hash is unchanged.

## Related Tickets
- TCK-20261019-RECORD-BASELINE-V1 (do after it)

## Related Docs
- docs/engine/

## Related Stored Artifacts
- none

## Related Code Areas
- src/engine/scheduler.py:143, src/engine/executor.py:189/290/335/340, src/engine/kernel.py:606, docs/engine/bounded_concurrency_contract.md §3

## Assumptions / Open Questions
- This was read from code, not reproduced. Re-verify it before any fix.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
