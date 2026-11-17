---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261111-KNOWLEDGE-INDEX-BUILD-MEMORY-BOUNDED
artifact_type: test_plan
tags: [delivery]
---

# Test plan: TCK-20261111-KNOWLEDGE-INDEX-BUILD-MEMORY-BOUNDED

- Regression (subprocess, so the pytest process keeps its limits): medium then large in one process gives soft 4 GB then 8 GB, hard limit never lowered. It fails on the current conftest and passes after the fix.
- The existing `test_conftest_resource_budget.py` tests stay green.
- AC2: `test_knowledge_search.py` and `test_knowledge_index_staleness.py` pass under the 3G wrapper, as they do in the g-m chunk (needs a lead go; the build tests take about 18 minutes in total).
- Not tested: embedding contents are untouched, so no probe-set comparison is needed.
