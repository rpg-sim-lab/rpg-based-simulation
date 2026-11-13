---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261112-KNOWLEDGE-STACK-PIN-BUMPS
artifact_type: test_plan
tags: [knowledge-store, setup]
---

# Test plan

## Proof Plan

- level: measurement
- proof kind: eval run plus smokes
- oracle source: the baseline Recall@5/MRR@10 and top-5 doc ids on the current pins
- expected effect: torch bump not lower on either metric; graphify query/update and headroom MCP smokes pass
- selected commands: `knowledge_search.py build --corpus-root` into a scratch tree per venv, then `tools/eval_search.py` and `tools/knowledge_search.py query` under the throwaway venv for 'mechanics damage formula', 'authoritative mutation pipeline contract', 'disk headroom midsession warning', 'regional sovereignty region boundaries', 'pre-push advisory hook'; `graphify query` and `graphify update .` on a scratch copy; `tools/start_headroom_mcp.sh` against the throwaway venv; after the pin edit: `tests/tools/test_code_test_index.py`, `tests/tools/test_graphify_shim.py`, `tests/tools/test_ci_workflow_test_coverage.py`, paths-guard.
