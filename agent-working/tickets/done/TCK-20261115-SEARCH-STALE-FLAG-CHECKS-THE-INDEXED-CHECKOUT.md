---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261115-SEARCH-STALE-FLAG-CHECKS-THE-INDEXED-CHECKOUT
phase: done
date: 2026-11-15
tags: [ai]
---

# TCK-20261115-SEARCH-STALE-FLAG-CHECKS-THE-INDEXED-CHECKOUT

## Title
search_docs's stale flag checks the checkout the index was built from, so a worktree no longer reports a current index as stale.

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Split from TCK-20261031-SDLC-CONTEXT-AND-SESSION-RELIABILITY (Phase 5, scope item 1) on 2026-11-15. It is the owner's chosen vehicle for the native implement-ticket run, TCK-20260930-NATIVE-PORT-SMALL-TICKET-NATIVE-RUN (#715 6889489078).

Since TCK-20261112-SEARCH-SERVER-PER-WORKTREE-INDEX-AND-BUILD-MEMORY-GUARD (#888), a worktree session's `search_docs` reads the main checkout's index (`tools/search_mcp.py::_resolve_index_dir`). The stale check still passes no corpus root: `search_mcp._run_search` calls `_ks.index_staleness(_DB_PATH)`, so `tools/knowledge_search.py::index_staleness` compares the main index's manifest mtimes against this worktree's files. Every file whose mtime differs between the two checkouts is counted as changed. Evidence: on 2026-11-15, in the agent-working-planner worktree, `search_docs` returned `stale: {changed: 5683, new: 30-35, removed: 0}`. Agents are told to distrust results that carry this flag, so a false positive costs real trust.

## Scope
1. Compare against the checkout that owns the index. When `search_docs` uses the main checkout's index, compare against the main checkout's files. When it uses this checkout's own index (no main index, or `RPG_SEARCH_OWN_INDEX=1`), compare against this checkout, as today. Resolve the root once, next to `_INDEX_DIR`, so the two can't drift.
2. Check the CLI `tools/knowledge_search.py query` path for the same mismatch, and make both paths agree. The `index_staleness` docstring says they can't disagree.
3. Tests in `tests/tools/test_search_mcp.py`, or the existing staleness tests' file, with temp dirs and no real index:
   - a worktree using the main index, where the main checkout is unchanged since the build → not stale, even though the worktree's file mtimes differ;
   - a main-checkout file changed after the build → stale, counted once;
   - the own-index opt-in → compared against the worktree.

## Out of Scope
- The other Phase 5 items (authority ranking, the graph rebuild, the handover cap, the memory split, provenance labels, E3). They stay in TCK-20261031-SDLC-CONTEXT-AND-SESSION-RELIABILITY.
- Rebuilding or moving any index.
- Whether a worktree should search its own branch content: Phase 5 item 3.

## Acceptance Criteria
1. [x] In a worktree that reads the main index, `search_docs` reports no `stale` key when the main checkout's corpus matches the manifest. Shown by a test, and by one live check from a worktree recorded in the Test Summary. The live check is `python3 tools/knowledge_search.py query "<q>" --top-k 1 --db-path <the main checkout's index>`, run in a worktree, which AC3's rule makes compare against the main checkout. Record the command in the Test Summary.
2. [x] A real change in the indexed checkout is still reported, with a test.
3. [x] The MCP and CLI paths use the same root rule: when no corpus root is passed, `index_staleness` derives it from `db_path`, the checkout that owns the index, and falls back to `_REPO_ROOT_STR` only when that can't be derived. A test shows a call with a `db_path` in another checkout compares against that checkout.
4. [x] The scoped `tests/tools` files pass. Before the run counts a failure in a test with a timing assertion, it is classified per the CI Failure Triage (docs/guides/delivery_process.md). Known case: four `@pytest.mark.slow` tests in `tests/tools/test_knowledge_search.py`, all with time or real-build bounds. They are `TestQueryHappyPath::test_query_completes_within_2_seconds` and three in `TestLiveQueryDocsMechanics`: `test_build_docs_chunk_count_exceeds_500`, `test_build_completes_under_five_minutes` and `test_existing_ticket_query_still_works`. They failed on this 2-core host in agent-working-implementer's local runs on 2026-11-12. The failures are noted, without names, as a Known gap in TCK-20261111-KNOWLEDGE-INDEX-BUILD-MEMORY-BOUNDED. CI never runs them (`-m "not slow and not extra_slow"`), so there is no CI evidence either way. The Test Summary states the marker filter the Test phase used.

## Related Tickets
- TCK-20261031-SDLC-CONTEXT-AND-SESSION-RELIABILITY (split from, item 1)
- TCK-20261112-SEARCH-SERVER-PER-WORKTREE-INDEX-AND-BUILD-MEMORY-GUARD (introduced the shared index)
- TCK-20261006-KNOWLEDGE-INDEX-STALE-WARNING (the stale check)
- TCK-20260930-NATIVE-PORT-SMALL-TICKET-NATIVE-RUN (runs this ticket natively)

## Related Docs
- docs/plans/agent_infrastructure/AI_FIRST_SDLC_ARCHITECTURE_EVOLUTION_PLAN.md (P-6, Phase 5)

## Related Stored Artifacts
- none

## Related Code Areas
- tools/search_mcp.py (`_resolve_index_dir`, `_run_search`)
- tools/knowledge_search.py (`index_staleness`, `query`)
- tests/tools/test_search_mcp.py, tests/tools/test_knowledge_search.py

## Assumptions / Open Questions
- The main checkout's own files may be on a different branch than the index build. The manifest records mtimes, not a ref, so "stale" still means "the files changed since the build". That is the intended meaning.
- Run through the native implement-ticket pipeline (TCK-20260930-NATIVE-PORT-SMALL-TICKET-NATIVE-RUN's run plan). Its first attempt carries a deliberate probe tag, and that tag is removed before the pass run.
- AC3 root rule decided by the owner on 2026-11-15, option (b) (#715 6894176292), after the native pass run wf_d6a35058-f5d stopped at the plan gate (NEEDS_HUMAN_INPUT, gv-6b41f8f548964201) to ask. Option (a), keeping the CLI's own-index rule with a stated reason, was not taken because it leaves two rules that can drift.

## Implementation Notes
The code, tests and doc were written by the native pass re-run `wf_f48f4fae-569` (ended `TESTS_FAILED`) and hand-finished on the owner's answer (#715 6894904885).

- `tools/knowledge_search.py`: new `_index_owner_root(db_path)` strips the trailing `KNOWLEDGE_INDEX` parts from `db_path.parent` and returns None for any other layout. `index_staleness` uses `corpus_root` if given, else the derived owner root, else `_REPO_ROOT_STR`. No `Path.resolve()`. `search_mcp.py` is unchanged: `_run_search` calls `index_staleness(_DB_PATH)` and inherits the rule, as does the CLI.
- `docs/guidelines/agent_working_environment.md`, "When the index is stale": rewritten to the post-#888 rule.
- `tests/tools/test_knowledge_index_staleness.py`: six tests on a two-checkout fixture with the real index layout.

**Deviations from the plan, found when checking the native run's work** (the run's own note said "No deviations from the plan"):
- Plan test 4 (the resolver root follows the chosen index dir in the five `TestResolveIndexDir` branches) was dropped. Under AC3 option (b) there is no `_INDEX_ROOT`, so there is nothing for it to test. Its job is done by `test_root_is_derived_from_db_path_not_repo_root`, `test_non_standard_db_layout_falls_back_to_repo_root` and `test_own_index_opt_in_compares_against_the_worktree`.
- The test file hardcoded the literal `knowledge-index`, which `tests/tools/test_agent_working_paths_guard.py::test_no_live_code_names_a_moved_root` rejects (the one real failure in the native Test phase). Fixed by importing `KNOWLEDGE_INDEX` from `tools.agent_working_paths`. The guard is untouched.
- The rewritten doc said "the CLI's `--corpus-root` overrides". `query` has no `--corpus-root` option (only `build` does). The clause is removed.

AC3 root rule: option (b), the owner's choice (#715 6894176292), after `wf_d6a35058-f5d` stopped at the plan gate to ask.

## Test Summary
**What the native run reported, and what was checked** (the run's claims kept as quoted evidence):

| the native run reported | checked |
|---|---|
| "61 passed" (`test_knowledge_index_staleness.py` + `test_search_mcp.py`) | not re-run as that pair; both files are inside the capped chunk runs below, which pass apart from the two named failures |
| "88 passed, 28 deselected" (`test_knowledge_search.py`, `-m "not slow and not extra_slow"`) | consistent: the capped f-l chunk shows 28 deselected |
| "No deviations from the plan" | false: plan test 4 was dropped, and two hand fixes were needed (above) |
| live check printed `40 changed, 57 new, 0 removed` | re-run here: `41 changed, 58 new, 0 removed` (the main checkout kept changing; same cause) |
| doc: "the CLI's `--corpus-root` overrides" | wrong, `query` has no such option; removed |
| Test phase: "57 other failures / 7 errors ... environmental" | confirmed environmental: they were `OSError: Cannot allocate memory` from one uncapped `tests/tools` process (Committed_AS over CommitLimit); none occurred when the same tests ran capped |

**Marker filter of the native Test phase:** `python3 -m pytest tests/tools/ -m "not slow and not extra_slow" -q --tb=line -rf -p no:cacheprovider`, no `-n`, the whole directory in one uncapped process. The four known `@pytest.mark.slow` timing tests in `test_knowledge_search.py` are deselected by that filter.

**Capped confirmation** (repo `.venv` python, `-n 0`, CI marker filter, `systemd-run --user --scope -p MemoryMax=3G -p MemorySwapMax=0 taskset -c 4-5`; MemAvailable 5.0-6.2 GB at each start; Committed_AS 13.4-14.8 GB against CommitLimit 13.48 GB, overcommit 0; no ENOMEM or MemoryError in any log):

| run | passed | failed | skipped | time |
|---|---|---|---|---|
| the 59 failing node ids from `wf_f48f4fae-569` | 59 | 0 | 0 | 67 s |
| `test_[a-c]*` | 924 | 0 | 1 | 85 s |
| `test_[d-e]*` | 867 | 0 | 1 | 95 s |
| `test_[f-l]*` | 832 | 1 | 19 (28 deselected) | 92 s |
| `test_[m-r]*` | 1183 | 0 | 5 | 166 s |
| `test_[s]*` | 1437 | 1 | 0 | 113 s |
| `test_[t-z]*` | 782 | 0 | 2 (1 xfailed) | 36 s |

Failures, classified per the CI Failure Triage: `test_generate_registry.py::TestRealDocsTree::test_check_flag_detects_no_drift_against_real_registry` was registry drift on the uncommitted branch, cleared by `make docs-registry` at close. `test_session_resolve_and_hook.py::test_a_second_live_holder_is_flagged` is a flake (spawns `sleep 30` and reads its process identity); it passed alone in 0.74 s.

Only the 59 failing node ids were extracted from the native run's logs, not the 64 the owner's note named, so the match against the original failure list is indirect; the full six-chunk run covers every file. The four `slow` tests were not run (CI never runs them either). The native run's own window overlapped rpg's scoped pytest for 66 s (12:20:00Z-12:21:06Z), before its Test phase.

**AC1 live check**, run in this worktree: `GRAPHIFY_NO_AUTO_REFRESH=1 python3 tools/knowledge_search.py query "stale index" --top-k 1 --db-path /data/vboxuser/Work/rpg-based-simulation/agent-working/.index/knowledge-index/knowledge.db` printed `knowledge index is stale: 41 changed, 58 new, 0 removed -- run make knowledge-index-update`. On origin/main's unchanged code the same command printed `5683 changed, 35 new, 0 removed` (run by the planner). So the live check shows the false positive gone (5683 to 41); the remaining count is real, since the main index was built on 2026-11-13 and this ticket does not rebuild it. The "no `stale` key when the corpus matches the manifest" half is shown by the tests only.

## Files Changed
- tools/knowledge_search.py
- tests/tools/test_knowledge_index_staleness.py
- docs/guidelines/agent_working_environment.md
- agent-working/tickets/done/TCK-20261115-SEARCH-STALE-FLAG-CHECKS-THE-INDEXED-CHECKOUT.md
- agent-working/stored_artifacts/TCK-20261115-SEARCH-STALE-FLAG-CHECKS-THE-INDEXED-CHECKOUT/ (investigation.md, plan.md, test_plan.md)

## Completion Summary
`index_staleness` derives its corpus root from the `db_path` of the index it checks (standard layout), falling back to the calling checkout, so a worktree reading the main checkout's index compares the main checkout's files. MCP and CLI share the rule with no caller change. Tests cover the worktree, real-change, fallback, own-index and CLI/MCP-agreement cases; the stale-section doc was corrected. Hand-finished after the native run ended `TESTS_FAILED` (#715 6894904885).

`make knowledge-index-update` was not run: from a worktree it builds only the worktree's own index, which nothing reads unless `RPG_SEARCH_OWN_INDEX=1`, and this ticket's Out of Scope bars rebuilding or moving any index. CLAUDE.md's After Work step "run make knowledge-index-update" does nothing useful from a worktree since #888; raised to agent-working-planner.

Known gap: `_resolve_index_dir` and the staleness check are joined only through `_DB_PATH`, and no test runs them together; `TestResolveIndexDir` covers the resolver alone.

Known gap: `tests/tools/test_session_resolve_and_hook.py::test_a_second_live_holder_is_flagged` failed once in the capped `test_[s]*` chunk and passed alone in 0.74 s; it spawns `sleep 30` and reads the process identity, which can race the spawn. One occurrence, not investigated further.
