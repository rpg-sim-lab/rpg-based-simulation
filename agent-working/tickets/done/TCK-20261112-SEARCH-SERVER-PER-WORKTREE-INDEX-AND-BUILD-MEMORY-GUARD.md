---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261112-SEARCH-SERVER-PER-WORKTREE-INDEX-AND-BUILD-MEMORY-GUARD
phase: done
date: 2026-11-12
tags: [process-improvement]
---

# TCK-20261112-SEARCH-SERVER-PER-WORKTREE-INDEX-AND-BUILD-MEMORY-GUARD

## Title
A worktree with its own knowledge index starts its own ~400 MB search server, and `knowledge_search.py build` starts with no memory check

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
Finding by lead-planner-u24 (2026-11-12), with the host's swap full and rpg cells blocked on memory. Three
`search_shared.py serve` processes were running at about 400-440 MB each, about 1.28 GB in all: pid 2371946 (main checkout),
2384048 (worktrees/rpg) and 2404154 (worktrees/agent-working-u24). Scoped by agent-working-planner-u24. Lead go: S4
dispatch, #715 6813618993. The lead placed the Makefile line with agent-working for this fix.

Cause (verified): each server has a different `--db`, which is that checkout's own `agent-working/.index/knowledge-index/
knowledge.db`. `search_shared.state_dir()` is keyed on the db path, so one db means one server. `code_tools_dir()` runs
a worktree's own code when that worktree has its own index. The code is the same commit (01296562a) in all three, so
`code_version` is not the difference. Worktrees have their own db because `search_mcp._resolve_index_dir()` prefers the
checkout's OWN index when one exists and falls back to main's only when it doesn't (TCK-20261010). Any `make
knowledge-index[-update]` run in a worktree creates one. 11 u24 worktrees had one, including nonflight, built on 11-11 by
lane B. The build itself loads about 1.5 GB with no cap, and it has no memory check.

## Scope
1. **`tools/search_mcp.py` `_resolve_index_dir`:** use the main checkout's index whenever it exists. Use the checkout's
   own index only when main has none, or when the env opt-in `RPG_SEARCH_OWN_INDEX=1` is set. The same resolution then
   flows into `search_shared` (state dir and code root), so worktree sessions share the main server.
2. **`tools/knowledge_search.py` `build`** (full and `--incremental`): before loading the model, read `MemAvailable` from
   `/proc/meminfo`. If it is below a threshold, the default being 2.5 GB, overridable by `RPG_KNOWLEDGE_BUILD_MIN_MEM_MB`,
   print one line with the numbers and exit non-zero without loading anything. `--force` overrides the check. If meminfo
   can't be read, the build carries on, as today.
3. **`Makefile`** (`knowledge-index-update` / `knowledge-index`): when run in a worktree (git-dir != common-dir), echo one
   line saying sessions there read the main checkout's index, so a worktree build is unused unless `RPG_SEARCH_OWN_INDEX=1`
   is set. Echo only; it doesn't block.
4. **Tests:**
   - `_resolve_index_dir`, 3 tests in `tests/tools/test_search_mcp.py`:
     - main and own both exist → main;
     - only own exists → own;
     - both exist with the opt-in set → own.
   - The build guard, 2 tests in `tests/tools/test_knowledge_search.py`, with an injected meminfo reader:
     - below the threshold → refused, model not loaded;
     - below the threshold with `--force`, or meminfo unreadable → proceeds to the model load (stubbed).

## Out of Scope
- Deleting worktree indexes. That's (0) and the owner's call: data deletion.
- Capping the build's memory (RLIMIT) or changing the embedding model.
- Changing the shared server's idle timeout (1800 s) or its `code_version` keying.
- Making the worktree build write into main's index.

## Acceptance Criteria
1. The 5 new tests pass. Existing `test_search_mcp.py`, `test_knowledge_search.py` and `test_search_shared*.py` pass
   unchanged. Run scoped and single-process. The knowledge build tests are `resource_budget_large`, so mind the host's memory.
2. From a worktree that has its own index, the resolved `_DB_PATH` is the main checkout's, shown by a test or a one-off
   print. No live server is spawned in tests.
3. The guard costs one small file read, with no model load before it.

## Where it rides
This is code, so under #715 6793205403 it stands alone.

## Related Tickets
- TCK-20261010-SEARCH-MCP-WORKTREE-VENV-RESOLUTION (done; the own-then-main fallback this reverses)
- TCK-20261018-SEARCH-SHARED-SINGLE-SERVER-FROM-MAIN-CHECKOUT (done; one server from main's code)
- TCK-20261111-KNOWLEDGE-INDEX-BUILD-MEMORY-BOUNDED (done; test-side soft RLIMIT_AS, no runtime guard)

## Related Docs
- none

## Related Stored Artifacts
- none

## Related Code Areas
- tools/search_mcp.py (`_resolve_index_dir`), tools/search_shared.py (`state_dir`, `code_tools_dir`, unchanged),
  tools/knowledge_search.py (`cmd_build`, `cmd_build_incremental`), Makefile (knowledge-index targets), tests/tools/

## Assumptions / Open Questions
- Simpler-fix check (6698958617): (1) is a few lines and removes the cause. (2) is about 15 lines and prevents the
  memory spike. No measurement runs. Leaves out: a worktree's unmerged doc edits aren't searchable until merged, unless
  the opt-in is set.
- The 2.5 GB default is about 1.5 GB of build plus headroom. It's tunable by env without a code change.

## Implementation Notes
Dispatched by agent-working-planner-u24; lead's S4 record #715 6813618993 (read by me). (1) search_mcp._resolve_index_dir: main checkout's index whenever it exists; own only when main has none, or RPG_SEARCH_OWN_INDEX=1 and own exists; new optional `own_index_opt_in` parameter (None reads the env). (2) knowledge_search: `_mem_available_mb` (/proc/meminfo) and `_memory_guard` run at the top of cmd_build and cmd_build_incremental, before any model import; below 2560 MB (RPG_KNOWLEDGE_BUILD_MIN_MEM_MB overrides) it prints one stderr line with the numbers and returns 3; `--force` overrides; unreadable meminfo proceeds. (3) Makefile: knowledge-index and knowledge-index-update echo one line in a worktree (git-dir != common-dir); echo only. The existing test `test_own_index_wins_when_present` pinned the old order (own wins over main), which this change inverts on purpose, so it was rewritten as `test_main_checkout_index_wins_when_both_exist`; the other resolve tests are unchanged. An autouse fixture in test_knowledge_search.py sets RPG_KNOWLEDGE_BUILD_MIN_MEM_MB=0 so the existing build tests do not depend on host memory.

## Test Summary
Run single-process and only what is stubbed (host at ~1.4 GB available, owner's instruction): tests/tools/test_search_mcp.py plus TestBuildMemoryGuard in test_knowledge_search.py: 46 passed (resolve: main wins, own when main has none, own with the opt-in, opt-in from env; guard: refused with one line and no model load, env threshold, force / unreadable / enough memory proceeds, cmd_build and cmd_build_incremental return the refusal before importing the model, meminfo parsing). Makefile guards test_makefile_uses_resolved_python, test_makefile_interpreter_selection, test_dashboard_makefile_targets: 15 passed. test_search_shared.py: 45 passed, 1 failed: test_state_dir_refuses_the_real_runtime_dir_under_pytest, the same test noted as failing locally before this change (unconfirmed, environmental, CI passes it); search_shared.py is untouched. SKIPPED (resource_budget_large, host short of memory): the rest of tests/tools/test_knowledge_search.py (the build tests). `make knowledge-index` was not run anywhere.

## Files Changed
tools/search_mcp.py; tools/knowledge_search.py; Makefile (2 echo lines); tests/tools/test_search_mcp.py; tests/tools/test_knowledge_search.py; this ticket; docs/REGISTRY.yaml; W46 shards.

## Completion Summary
Worktree sessions now share the main checkout's search server, and a knowledge build refuses to start on a host with less than 2.5 GB available. Known gaps: the knowledge build tests are not run yet (to run before the push ask once memory is back); existing worktree indexes were already removed by the owner.
