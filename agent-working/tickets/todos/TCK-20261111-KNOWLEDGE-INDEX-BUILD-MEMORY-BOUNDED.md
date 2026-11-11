---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261111-KNOWLEDGE-INDEX-BUILD-MEMORY-BOUNDED
phase: open
date: 2026-11-11
tags: [delivery]
---

# TCK-20261111-KNOWLEDGE-INDEX-BUILD-MEMORY-BOUNDED

## Title
The knowledge-index build tests get the address space they need: the resource budget lowers only the soft limit, and the build tests are marked large

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
On host ubuntu, the knowledge-search build tests fail under the lead slot cap
(`systemd-run --user --scope -p MemoryMax=3G -p MemorySwapMax=0`) with `MemoryError`. CI passes, so the failure is
local only. Seen on main 5c6990e51 in the tests/tools [g-m] chunk:
- test_knowledge_search build: MemoryError x2 (17,224 chunks);
- test_knowledge_index_staleness: "no such table: knowledge_vec" x2 (the build died before the
  table was written);
- one anomaly-validator SystemError as a casualty.
Max RSS reached about 1.09 GB before the failure.
The ticket was filed assuming `tools/knowledge_search.py` encodes all texts in one call and needs batching. Investigation
(Implementation Notes) shows that is not the cause: the cause is the pytest address-space limit.

## Scope
- Investigate (done): peak RSS and peak virtual size of the full and the incremental build under the 3G cap, and which
  limit refuses the allocation.
- `tests/conftest.py`: lower only the SOFT `RLIMIT_AS`, keeping the hard limit (an unprivileged process can never raise a lowered
  hard limit, so the first test's budget fixed the cap for every later test, and `resource_budget_large` / `extra_slow`
  silently kept the medium cap). rpg owns that file; the edit waits for rpg-planner's OK.
- Mark the knowledge build and staleness tests (`test_knowledge_search.py`, `test_knowledge_index_staleness.py`)
  `resource_budget_large`: they need about 4.7-4.9 GB of address space.
- A regression test: a medium test followed by a large test in one process sees the large address space.

## Out of Scope
- Batching the encode (dropped: the arrays are about 26 MB; the build is not memory-bound).
- Changing the embedding model or the chunking, and re-enabling the post-commit reindex by default.

## Acceptance Criteria
1. `make knowledge-index` and `make knowledge-index-update` complete under the 3G wrapper on host ubuntu. Peak RSS is reported in the PR. (Met by the runs below, before any change.)
2. The tests/tools [g-m] chunk's knowledge-search and index-staleness tests pass under the wrapper.
3. A medium test followed by a large test in one process: the large test sees an 8 GB soft limit, and the hard limit is not lowered.

## Related Tickets
- TCK-20261111-POST-COMMIT-REINDEX-OPT-IN
- TCK-20260612-LOCAL-CTX-OPS (incremental build)

## Related Docs
- docs/guidelines/agent_working_environment.md (command reference)

## Related Stored Artifacts

## Related Code Areas
- tools/knowledge_search.py, tests/tools/test_knowledge_search*.py, test_knowledge_index_staleness*.py

## Assumptions / Open Questions
- About 1.09 GB peak RSS under a 3G cap suggests a single large allocation fails, not a slow
  climb. Investigate confirms or refutes this before any batching is designed.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
