---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261115-SEARCH-STALE-FLAG-CHECKS-THE-INDEXED-CHECKOUT
artifact_type: test_plan
tags: [ai, mcp]
---

# Test Plan — TCK-20261115-SEARCH-STALE-FLAG-CHECKS-THE-INDEXED-CHECKOUT

## Regression Surface

Unit/tools (all under `tests/tools/`):
- `tests/tools/test_knowledge_index_staleness.py` (fixture db at `<root>/index/knowledge.db`, explicit root; must pass unchanged, incl. `_mcp` helper with one-arg `index_staleness` lambda)
- `tests/tools/test_search_mcp.py` (`_resolve_index_dir` tests, degraded-staleness test at ~476)
- `tests/tools/test_knowledge_search.py` (fast tests; `-m "not slow and not extra_slow"`)

Integration / arena-combat: none affected.

## New Tests Required

All in `tests/tools/test_knowledge_index_staleness.py` (temp dirs, no real index), using a layout-faithful fixture: `<main>/agent-working/.index/knowledge-index/knowledge.db` built from `<main>`, plus a separate `<wt>` checkout with the same files at different mtimes.
1. `test_worktree_reading_the_main_index_is_not_stale` (unit; AC1): call `index_staleness(main_db)` with no root, cwd/`_REPO_ROOT_STR` patched to `<wt>`; assert None although `<wt>` mtimes differ.
2. `test_a_change_in_the_indexed_checkout_is_reported_once` (unit; AC2): bump one main file; assert `{"changed": 1, "new": 0, "removed": 0}` with no root passed.
3. `test_root_is_derived_from_db_path_not_repo_root` (unit; AC3): `db_path` in another checkout compares against that checkout (assert via a changed file only present there); explicit `corpus_root` still wins.
4. `test_non_standard_db_layout_falls_back_to_repo_root` (unit; AC3 fallback; also covers existing `<root>/index/` shape and never raising).
5. `test_own_index_opt_in_compares_against_the_worktree` (unit; AC1/scope 3): own index db in `<wt>` -> compared against `<wt>`; a worktree change reports stale.
6. `test_cli_query_and_mcp_agree` (unit; AC3/scope 2): `cmd_query` with `Namespace(db_path=main_db, corpus_root=None, ...)` prints no stale line, and `search_mcp._run_search(with_staleness=True)` with `_DB_PATH=main_db` returns no `stale` key.

## Proof Plan

| AC | level | proof kind | oracle source | expected effect | selected commands |
|---|---|---|---|---|---|
| AC1 | unit + one live check | regression | ticket AC1; `docs/guidelines/agent_working_environment.md` "When the index is stale"; parity: none | no `stale` key / no stderr line for unchanged main corpus | pytest cmd below; live: `python3 tools/knowledge_search.py query "<q>" --top-k 1 --db-path <main checkout index>` run in a worktree, recorded in Test Summary |
| AC2 | unit | regression | ticket AC2; TCK-20261006-KNOWLEDGE-INDEX-STALE-WARNING; parity: none | `{"changed":1,...}` counted once | pytest cmd below |
| AC3 | unit | invariant (single root rule) | ticket AC3 / owner decision #715 6894176292; parity: none | root derived from `db_path`; fallback `_REPO_ROOT_STR`; explicit root wins | pytest cmd below |
| AC4 | scoped suite | regression | ticket AC4; `docs/guides/delivery_process.md` CI Failure Triage | scoped tools tests pass; slow-marker failures classified | pytest cmd below |

Negative cases: unreadable/missing manifest still `{"unknown": True}`; odd db layout does not raise. Non-functional: staleness stays stat-only (~0.1 s).

## Scoped Pytest Commands

```
python3 -m pytest tests/tools/test_knowledge_index_staleness.py tests/tools/test_search_mcp.py -q
python3 -m pytest tests/tools/test_knowledge_search.py -m "not slow and not extra_slow" -q
```
Test Summary must state this marker filter. The four known slow tests (`test_query_completes_within_2_seconds`, `test_build_docs_chunk_count_exceeds_500`, `test_build_completes_under_five_minutes`, `test_existing_ticket_query_still_works`) are excluded by it; if run, classify timing failures per CI Failure Triage.

## Anti-Drift Test Guards

- `test_the_stat_walk_covers_exactly_what_the_build_indexed` (corpus set unchanged).
- `test_an_excluded_docs_subtree_never_counts`, manifest-unknown parametrized test (payload shape unchanged).
- `_resolve_index_dir` tests in `test_search_mcp.py` (index choice unchanged).
