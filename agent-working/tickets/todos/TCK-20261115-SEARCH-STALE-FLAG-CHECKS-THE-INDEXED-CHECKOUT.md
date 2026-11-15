---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261115-SEARCH-STALE-FLAG-CHECKS-THE-INDEXED-CHECKOUT
phase: open
date: 2026-11-15
tags: [ai]
---

# TCK-20261115-SEARCH-STALE-FLAG-CHECKS-THE-INDEXED-CHECKOUT

## Title
search_docs's stale flag checks the checkout the index was built from, so a worktree no longer reports a current index as stale.

## Status
OPEN

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
1. In a worktree that reads the main index, `search_docs` reports no `stale` key when the main checkout's corpus matches the manifest. Shown by a test, and by one live check from a worktree recorded in the Test Summary. A worktree's running MCP server still holds the pre-fix code, so the live check is either `python3 tools/knowledge_search.py query "<q>" --top-k 1` run in that worktree, if AC3 makes the CLI follow the same root rule, or a `search_docs` call after that server restarts. Say which.
2. A real change in the indexed checkout is still reported, with a test.
3. The MCP and CLI paths use the same root rule, with a test or a stated reason.
4. The scoped `tests/tools` files pass. Before the run counts a failure in a test with a timing assertion, it is classified per the CI Failure Triage (docs/guides/delivery_process.md). Known case: four `@pytest.mark.slow` tests in `tests/tools/test_knowledge_search.py`, all with time or real-build bounds. They are `TestQueryHappyPath::test_query_completes_within_2_seconds` and three in `TestLiveQueryDocsMechanics`: `test_build_docs_chunk_count_exceeds_500`, `test_build_completes_under_five_minutes` and `test_existing_ticket_query_still_works`. They failed on this 2-core host in agent-working-implementer's local runs on 2026-11-12. The failures are noted, without names, as a Known gap in TCK-20261111-KNOWLEDGE-INDEX-BUILD-MEMORY-BOUNDED. CI never runs them (`-m "not slow and not extra_slow"`), so there is no CI evidence either way. The Test Summary states the marker filter the Test phase used.

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

## Implementation Notes
(to be filled by the implementer)

## Test Summary
(to be filled by the implementer)

## Files Changed
(to be filled by the implementer)

## Completion Summary
(to be filled by the implementer)
