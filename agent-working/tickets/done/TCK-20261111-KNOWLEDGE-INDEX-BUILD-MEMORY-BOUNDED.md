---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261111-KNOWLEDGE-INDEX-BUILD-MEMORY-BOUNDED
phase: done
date: 2026-11-11
tags: [delivery]
---

# TCK-20261111-KNOWLEDGE-INDEX-BUILD-MEMORY-BOUNDED

## Title
The knowledge-index build tests get the address space they need: the resource budget lowers only the soft limit, and the build tests are marked large

## Status
DONE

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
Premise corrected (lead, 11-11): lead never ran `make knowledge-index-update` on this host; its 'the model OOMs here' came from the pytest MemoryError. Ticket rewritten at investigation (title, scope, ACs; batching dropped). See `investigation.md` for the measurements: full build rc 0, peak RSS 1.40 GB, peak virtual 4.68 GB; incremental rc 0, 1.57 GB and 4.85 GB; the same incremental build under `ulimit -v 4 GB` fails loading the model (`unable to mmap`). `tests/conftest.py` set `RLIMIT_AS` for every test (4 GB at the medium budget), hard limit included, so the build tests were refused address space and the first test's cap bound all later tests.
Changes: (1) `tests/conftest.py` lowers only the soft limit, clamped to an inherited finite hard limit (rpg-planner's conditions; rpg-planner OK given via lead-planner-u24; a cross-domain edit); (2) `pytestmark = resource_budget_large` on `test_knowledge_search.py` and `test_knowledge_index_staleness.py`; (3) regression test `tests/unit/test_conftest_rlimit_soft_only.py`; (4) `test_conftest_resource_budget.py` updated where it pinned the old hard=soft pair; (5) the staleness `_query` helper also tolerates the empty fixture db's `OperationalError` (the two 'no such table: knowledge_vec' failures were this fixture, not a build that died; the helper's docstring already says the warning prints before any search work).
Thread counts for the record: torch 2, cpu_count 6, affinity 2 under taskset 4-5; CI has different counts, so its VmPeak is probably lower. No change for CI.

## Test Summary
Regression: `tests/unit/test_conftest_rlimit_soft_only.py` 5 passed on the new conftest and 4 of 5 fail on the old one. `test_conftest_resource_budget.py` passes. Under the 3G wrapper (lead's go): `test_knowledge_index_staleness.py` 14 passed on the synced tree. `test_knowledge_search.py` (before the sync with main): 107 passed, 4 failed; the two MemoryError build failures no longer occur. The 4 left are time limits on this 2-core host: two live queries took 5.3-5.4 s against a 2 s SLA, and two real builds (`test_build_docs_chunk_count_exceeds_500`, `test_build_completes_under_five_minutes`) hit their subprocess timeouts because the full build takes about 18 minutes here. They are not memory failures, are not addressed, and are Known gaps below.

## Files Changed
tests/conftest.py (cross-domain: rpg), tests/unit/test_conftest_rlimit_soft_only.py, tests/tools/test_conftest_resource_budget.py, tests/tools/test_knowledge_search.py, tests/tools/test_knowledge_index_staleness.py, stored artifacts (investigation, plan, test_plan)

## Completion Summary
Known gap: four time-based tests in `test_knowledge_search.py` still fail on this host (query SLA 2 s vs about 5.3 s; real builds slower than their subprocess timeouts). The build itself is not memory-bound and the pytest address-space cap no longer binds a large test; the knowledge build and staleness tests now run under the large budget.
