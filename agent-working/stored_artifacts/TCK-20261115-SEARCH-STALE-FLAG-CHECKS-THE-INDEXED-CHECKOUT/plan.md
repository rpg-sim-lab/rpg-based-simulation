---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261115-SEARCH-STALE-FLAG-CHECKS-THE-INDEXED-CHECKOUT
artifact_type: plan
tags: [ai, mcp]
---

# Implementation Plan — TCK-20261115-SEARCH-STALE-FLAG-CHECKS-THE-INDEXED-CHECKOUT

## Summary
`index_staleness` (tools/knowledge_search.py:673) defaults its corpus root to `Path(_REPO_ROOT_STR)` (l.681), the calling checkout, so a worktree reading the main checkout's index compares the wrong files. Per the owner's AC3 decision (option b, #715 6894176292) the fix is one rule in one place: when no `corpus_root` is passed, derive the root from `db_path` by stripping the trailing `KNOWLEDGE_INDEX` parts (`agent-working/.index/knowledge-index`, tools/agent_working_paths.py:39), falling back to `_REPO_ROOT_STR` when `db_path` lacks that shape. Both callers (MCP `search_mcp.py:156` and CLI `knowledge_search.py:1108`) inherit it with no change. Then add tests on a layout-faithful two-checkout fixture and fix the one wrong doc section.

## Steps

### Step 1 - Add the root-derivation helper and use it in `index_staleness`
**Files:** tools/knowledge_search.py
**Change:** Add a small module-level helper (e.g. `_index_owner_root(db_path: Path) -> Path | None`) next to `index_staleness`. `KNOWLEDGE_INDEX` is already imported (knowledge_search.py:48; verified). Logic: `tail = KNOWLEDGE_INDEX.parts` (3 parts); `dir_parts = db_path.parent.parts`; if `dir_parts[-len(tail):] == tail` and there are parts before it, return `Path(*dir_parts[:-len(tail)])`, else None. The manifest is read from `db_path.parent/manifest.json` (l.682) and is built with corpus root "." (investigation), so manifest paths are relative to this owning root. In `index_staleness`, replace l.681 with `root = corpus_root if corpus_root is not None else (_index_owner_root(db_path) or Path(_REPO_ROOT_STR))`. Explicit `corpus_root` still wins. Keep it inside the existing `try`; stat-only; never raises; payload shape and the `> 0.01` tolerance unchanged. Do not call `Path.resolve()` on `db_path`: use the path as passed (decision, see Anti-Drift; a symlinked index dir could resolve to a different root, and the existing behavior never resolved it). Update the docstring (l.676-679) so `corpus_root` "defaults to the checkout that owns `db_path` (derived from the standard index layout), falling back to this checkout's root when `db_path` has another shape".
Other writers/callers of this logic: `search_mcp._run_search` (l.156, one positional arg, unchanged) and `cmd_query` (l.1108, passes explicit root only when `--corpus-root` is given). Nothing writes the manifest here; `_write_manifest` is untouched.
**Do NOT touch:** `search_mcp._resolve_index_dir`/`_INDEX_DIR`/`_DB_PATH`, `_corpus_source_paths`, `_write_manifest`, the stale payload shape, the 0.01 tolerance, `stale_warning`, any index build/move. Do not add a root rule in search_mcp.py. Do not change the MCP call signature: existing tests monkeypatch `index_staleness` with one-arg lambdas (test_knowledge_index_staleness.py:131-133, test_search_mcp.py ~476).
**Verify:** existing `tests/tools/test_knowledge_index_staleness.py` passes unchanged (its `<root>/index/knowledge.db` layout hits the fallback and uses an explicit root).

### Step 2 - Tests for the derivation (AC1, AC2, AC3)
**Files:** tests/tools/test_knowledge_index_staleness.py
**Change:** Add a layout-faithful fixture: `<main>/agent-working/.index/knowledge-index/knowledge.db` with manifest built from `<main>`, plus a separate `<wt>` checkout holding the same files at different mtimes (reuse `corpus`, `_write`, `_bump`, `_load` helpers at l.24-57; read them first). Add, per test_plan.md:
1. `test_worktree_reading_the_main_index_is_not_stale` (monkeypatch `_REPO_ROOT_STR` to `<wt>`; `index_staleness(main_db)` is None). AC1.
2. `test_a_change_in_the_indexed_checkout_is_reported_once` (`{"changed":1,"new":0,"removed":0}`, no root passed). AC2.
3. `test_root_is_derived_from_db_path_not_repo_root` (a file changed only in the other checkout is seen; explicit `corpus_root` still wins). AC3.
4. `test_non_standard_db_layout_falls_back_to_repo_root` (`<root>/index/knowledge.db` and a too-short path; never raises). AC3 fallback.
5. `test_own_index_opt_in_compares_against_the_worktree` (own index db inside `<wt>`; a `<wt>` change reports stale). Scope item 3.
**Do NOT touch:** existing tests' assertions; do not weaken any. No real index; temp dirs only.
**Verify:** `python3 -m pytest tests/tools/test_knowledge_index_staleness.py -q`. Confirm tests 1-3 fail against the pre-Step-1 code (write them first, run red, then Step 1).

### Step 3 - Test that the CLI and MCP paths agree (AC3, scope item 2)
**Files:** tests/tools/test_knowledge_index_staleness.py
**Change:** Add `test_cli_query_and_mcp_agree`: with the Step 2 two-checkout fixture and `_REPO_ROOT_STR` patched to `<wt>`, run `cmd_query` (via the existing `_query` helper l.106, `corpus_root=None`, `db_path=main_db`) and assert no stale stderr line; run `search_mcp._run_search(with_staleness=True)` with `_DB_PATH=main_db` (via `_mcp` helper l.131 pattern, but do NOT replace `index_staleness` with a lambda, so the real function runs) and assert no `stale` key; then bump a main file and assert both report it.
**Do NOT touch:** `_mcp`/`_query` helpers' existing behavior (add a variant only if needed).
**Verify:** `python3 -m pytest tests/tools/test_knowledge_index_staleness.py tests/tools/test_search_mcp.py -q`.
**Depends on:** Steps 1, 2.

### Step 4 - Fix the stale-section doc
**Files:** docs/guidelines/agent_working_environment.md ("When the index is stale", ~l.452-463)
**Change:** Replace "Each worktree searches its own index ..." with the real behavior: a worktree reads the main checkout's index when it has one (`tools/search_mcp.py::_resolve_index_dir`, `RPG_SEARCH_OWN_INDEX=1` opts into its own), and the staleness check compares the manifest with the files of the checkout that owns the index, derived from the `db_path` (falls back to the calling checkout for a non-standard layout; `--corpus-root` overrides on the CLI). State that "stale" still means files changed since the build, including a main checkout on another branch. Keep the rest of the section (payload, stderr line, unknown case) unchanged.
**Do NOT touch:** AI_FIRST_SDLC_ARCHITECTURE_EVOLUTION_PLAN.md P-6 row, AUDIT doc, docs/ai/ticket-lifecycle.md, knowledge_gateway_mcp_contract.md (candidates only, not required; audit docs are records). No parity ledger edit (no staleness entry; no P0 touched). After editing, run `make knowledge-index-update` (a `docs/` file changed) and `make docs-registry` is handled by Finalize.
**Verify:** frontmatter of the doc still valid (`python3 tools/validate_frontmatter.py` on the file); re-read the section against Step 1.

### Step 5 - Scoped suite and live check (AC1 live, AC4)
**Files:** none changed; results go in the ticket's Test Summary (implementer fills).
**Change:** Run `python3 -m pytest tests/tools/test_knowledge_index_staleness.py tests/tools/test_search_mcp.py -q` and `python3 -m pytest tests/tools/test_knowledge_search.py -m "not slow and not extra_slow" -q`. State the marker filter in the Test Summary; the four known slow timing-bound tests (`test_query_completes_within_2_seconds`, `test_build_docs_chunk_count_exceeds_500`, `test_build_completes_under_five_minutes`, `test_existing_ticket_query_still_works`) are excluded by it; if any are run and fail on timing, classify per CI Failure Triage (docs/guides/delivery_process.md) rather than counting as a regression. Live check, from a worktree: `python3 tools/knowledge_search.py query "<q>" --top-k 1 --db-path <main checkout>/agent-working/.index/knowledge-index/knowledge.db`; record the exact command and whether a stderr stale line appeared. It may legitimately still report stale if the main checkout's files differ from the build; if so, record the numbers and say why, do not edit anything to silence it.
**Do NOT touch:** the slow tests, markers, or timing bounds.
**Verify:** all of the above green/recorded.
**Depends on:** Steps 1-4.

## Scope Guards
- No change to `_resolve_index_dir`, index location, index rebuild/move, `_corpus_source_paths`, `_write_manifest`, stale payload shape, tolerance.
- Other Phase 5 items (authority ranking, graph rebuild, handover cap, memory split, provenance labels, E3, worktree searching its own branch content) stay in TCK-20261031-SDLC-CONTEXT-AND-SESSION-RELIABILITY.
- No second root rule in tools/search_mcp.py. No change to the `index_staleness(_DB_PATH)` call shape.
- No mechanics/engine/parity-ledger edits; no simulation code.
- Do not edit tests or docs to make a gate pass.

## Dependency Map
Step 2 (red tests) before Step 1 (fix) is recommended but both are one unit; Step 3 depends on 1 and 2; Step 4 depends on 1 (wording); Step 5 depends on all.

## Acceptance Criteria Map
| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC1 no `stale` for worktree on unchanged main corpus; live check recorded | 1, 5 | `test_worktree_reading_the_main_index_is_not_stale`, `test_cli_query_and_mcp_agree`; live command in Test Summary |
| AC2 real change still reported, once | 1 | `test_a_change_in_the_indexed_checkout_is_reported_once` |
| AC3 one root rule: derive from `db_path`, fall back to `_REPO_ROOT_STR` | 1, 3 | `test_root_is_derived_from_db_path_not_repo_root`, `test_non_standard_db_layout_falls_back_to_repo_root`, `test_cli_query_and_mcp_agree` |
| AC4 scoped tools tests pass, timing failures classified, marker filter stated | 5 | scoped pytest commands in Step 5 |
| Scope 3 own-index opt-in compares against the worktree | 1, 2 | `test_own_index_opt_in_compares_against_the_worktree` |

## Anti-Drift Notes
- Do not use `Path.resolve()` on `db_path` (decision: use as passed; worktree symlinks such as `graphify-out` make blind resolving risky). A relative or odd `db_path` falls back, never raises.
- `index_staleness` must stay stat-only, never raise, return None / dict / `{"unknown": True}`.
- Existing tests use `<root>/index/knowledge.db`: they hit the fallback and must pass unchanged.
- Existing one-arg `index_staleness` monkeypatch lambdas must keep working.
- The main checkout's files may legitimately differ from the build; "stale" means mtimes changed since build.

## Unresolved Questions
None blocking. Non-blocking note: the `Path.resolve()` open item from the investigation is decided here conservatively (no resolve); say so if the owner prefers otherwise.

## Outcome (added at hand-finish, 2026-11-16)
Plan test 4 (the resolver root in the five `TestResolveIndexDir` branches) was dropped: AC3 option (b) leaves no `_INDEX_ROOT`. Step 4 (the AC3 CLI rule) was settled by the owner as (b), #715 6894176292: `index_staleness` derives the root from `db_path`. Two hand fixes after the native Test phase: the staleness test imports `KNOWLEDGE_INDEX` from `tools.agent_working_paths` instead of a literal, and the doc no longer names a `--corpus-root` option that `query` lacks. `make knowledge-index-update` was skipped (see the ticket).
