---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261111-KNOWLEDGE-INDEX-BUILD-MEMORY-BOUNDED
artifact_type: plan
tags: [documentation, reference]
---

# Plan: TCK-20261111-KNOWLEDGE-INDEX-BUILD-MEMORY-BOUNDED

The plan changed after investigation (see investigation.md): batching the encode is dropped.
1. `tests/conftest.py` (rpg's file; waits for rpg-planner's OK): `setrlimit(RLIMIT_AS, (mem_limit, hard))` with `hard = getrlimit(RLIMIT_AS)[1]`, so only the soft limit is lowered.
2. `pytestmark = pytest.mark.resource_budget_large` in `test_knowledge_search.py` and `test_knowledge_index_staleness.py`, with the VmPeak figures as the reason.
3. `tests/tools/test_conftest_rlimit_soft_only.py`: in a subprocess, a medium test then a large test; the large one sees 8 GB and the hard limit is never lowered.
4. Verify AC2 with a lead-approved chunk run under the 3G wrapper.
