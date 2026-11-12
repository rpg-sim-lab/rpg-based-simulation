---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261112-KNOWLEDGE-STACK-PIN-BUMPS
phase: open
date: 2026-11-12
tags: [knowledge-store, setup]
---

# TCK-20261112-KNOWLEDGE-STACK-PIN-BUMPS

## Title
requirements-knowledge.txt takes graphifyy 0.9.104, torch 2.15.0+cpu and headroom-ai 0.43.1, each smoke-tested

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
Owner decision on Dependabot #882 (#715 6812820923; lead-planner's review is PR comment 6812660165,
option A). #882 is closed unmerged. It bumped these three pins with no checks. It dropped torch's
`+cpu` label, so a PyPI install pulls the CUDA wheels. It also failed CI on
`tests/tools/test_code_test_index.py::TestRequirementsPin`. platform adds a Dependabot `ignore` for the
three packages separately. agent-working bumps them here, by hand, with a smoke test for each:

| Package | Now | Target | Published (checked 2026-11-12) |
|---|---|---|---|
| graphifyy | 0.9.70 | 0.9.104 | yes (PyPI latest is 0.9.106; take 0.9.104 as the owner named it) |
| torch | 2.13.0+cpu | 2.15.0+cpu | yes, cp312 x86_64 on download.pytorch.org/whl/cpu |
| headroom-ai | 0.37.0 | 0.43.1 | yes (PyPI latest is 0.44.0; take 0.43.1) |

## Scope
1. Disk first: `python3 tools/sessions/disk_headroom.py`, and record the free space on / and /data.
   Lead's figures on 11-12 are 8.1G on / and 16G on /data. Stop and report if /data is under 10 GB free.
2. **No venv build without a heavy-slot go from lead-planner**, for each run. Builds and index runs go
   under `systemd-run --user --scope -q -p MemoryMax=3G -p MemorySwapMax=0 taskset -c 4-5`.
3. Baseline on the current pins: `make eval-search`, then record Recall@5 / MRR@10.
4. Build a throwaway venv on /data with the three new pins. Never touch the main `.venv-knowledge` until
   the results are in. Install torch from the CPU index:
   `pip install torch==2.15.0+cpu --index-url https://download.pytorch.org/whl/cpu`. That index is
   reachable on ubuntu and blocked on u24desktop, so run this on ubuntu.
5. Smoke tests in the throwaway venv:
   - **torch / embeddings:** build a scratch index, run the same eval, and compare top-5 doc ids on the
     5 fixed spot-check queries from TCK-20261014-KNOWLEDGE-STACK-PIN-AND-EMBEDDING-MAJOR's
     `test_plan.md`.
   - **graphifyy:** read the changelog from 0.9.70 to 0.9.104 and record CLI or graph-format changes. On a
     scratch copy, run `graphify query "<topic>"` and `graphify update .`. If the `graphify-out/` format or
     node ids change, say so and stop before touching the shared graph. A bump can change local graph
     output, so record it either way.
   - **headroom-ai:** follow the trial pin's rules (TCK-20260916-HEADROOM-TRIAL-ISOLATION-AND-REVERT).
     Start `tools/start_headroom_mcp.sh` against the throwaway venv. Check that it lists its tools and
     answers one call. Base package only, no extras. Never run `headroom wrap`.
6. Decision rule: take each pin whose smoke test passes, and for torch only if Recall@5 and MRR@10 are not
   lower than the baseline. If one fails, take the others and record the failing one with its reason.
7. Update `requirements-knowledge.txt`:
   - Keep `torch==2.15.0+cpu`, with the label.
   - Refresh the graphifyy pin comment, which still cites 0.9.70.
   - Update the version pins in `tests/tools/test_code_test_index.py::TestRequirementsPin` and in
     `tests/tools/test_graphify_shim.py` (`PIN = "0.9.70"`).
   - Update the pin note in `docs/guidelines/agent_working_environment.md` (the dated 10-24 paragraph
     names torch 2.13.0+cpu; add a dated line, don't rewrite history).
8. With a further lead go, rebuild the main `.venv-knowledge` and the real index. Then remove the throwaway
   venv and the scratch index, and report the space recovered.

## Out of Scope
- `uv.lock` / `pyproject.toml`, and the other 17 #882 updates (platform's regrouped PR).
- `.github/dependabot.yml` (platform's ignore entry).
- Rebuilding the shared `graphify-out/` beyond the smoke test.
- Any major version, or versions past the three targets.

## Acceptance Criteria
1. `requirements-knowledge.txt` pins `graphifyy==0.9.104`, `torch==2.15.0+cpu` and `headroom-ai==0.43.1`,
   unless the ticket records why one was not taken.
2. Both pin tests pass and name the new graphifyy version.
3. The ticket records: disk before and after, baseline and candidate Recall@5/MRR@10, the 5 spot-check
   comparisons, the graphifyy changelog note and smoke result, the headroom smoke result, and the
   decision for each package.
4. `search_docs` answers from the main checkout after the rebuild, and headroom's MCP server starts from
   `.mcp.json`.
5. No throwaway venv or scratch index is left behind.

## Related Tickets
- TCK-20261024-KNOWLEDGE-STACK-SECURITY-BUMPS (last bump; same procedure)
- TCK-20261024-GRAPHIFY-ON-PATH-IS-NOT-THE-PINNED-VERSION
- TCK-20260916-HEADROOM-TRIAL-ISOLATION-AND-REVERT
- TCK-20261014-KNOWLEDGE-STACK-PIN-AND-EMBEDDING-MAJOR (spot-check queries)

## Related Docs
- docs/guidelines/agent_working_environment.md
- pyproject.toml (the torch CPU-index note)

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20261024-KNOWLEDGE-STACK-SECURITY-BUMPS/

## Related Code Areas
- requirements-knowledge.txt, tests/tools/test_code_test_index.py, tests/tools/test_graphify_shim.py,
  tools/start_headroom_mcp.sh, tools/knowledge_search.py

## Assumptions / Open Questions
- PR #882 and the u24 twin: check #634 and `git ls-remote origin` before dispatch. No u24 branch
  touches these pins as of 2026-11-12.
- The new head of this branch needs its own owner push yes, as usual.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
