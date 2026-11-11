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
The knowledge-index build embeds in bounded batches, so it fits under the 3G slot cap

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
On host ubuntu, the knowledge-index build fails under the lead slot cap
(`systemd-run --user --scope -p MemoryMax=3G -p MemorySwapMax=0`). CI passes, so the failure is
local only. Seen on main 5c6990e51 in the tests/tools [g-m] chunk:
- test_knowledge_search build: MemoryError x2 (17,224 chunks);
- test_knowledge_index_staleness: "no such table: knowledge_vec" x2 (the build died before the
  table was written);
- one anomaly-validator SystemError as a casualty.

Max RSS reached about 1.09 GB before the failure. lead also OOMs on `make knowledge-index-update`.
Read on main: `tools/knowledge_search.py` calls `model.encode(texts, ...)` once over every text
(about :786 for the full build, :951 for the incremental one), so the arrays for all chunks and
the tokenizer's batch buffers are in memory together. The post-commit hook runs this same path
with no cap (TCK-20261111-POST-COMMIT-REINDEX-OPT-IN).

## Scope
- Investigate first: measure peak RSS of the full and the incremental build under the 3G cap,
  and find which allocation fails (model load, encode, the numpy concat, or the sqlite vec
  insert).
- Encode and write in fixed-size batches, so peak memory no longer grows with the corpus.
  The index contents must stay identical: the same chunks, ids and vectors (within float
  tolerance), and the same query results on a fixed probe set.
- A test proving the batching is bounded, on a synthetic corpus larger than one batch.

## Out of Scope
- Changing the embedding model or the chunking.
- Re-enabling the post-commit reindex by default.

## Acceptance Criteria
1. `make knowledge-index-update` and a full `make knowledge-index` complete under the 3G
   wrapper on host ubuntu. Peak RSS is reported in the PR.
2. The tests/tools [g-m] chunk's knowledge-search and index-staleness tests pass under the
   wrapper.
3. On a fixed probe set, the top-5 results before and after the change are the same.

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
