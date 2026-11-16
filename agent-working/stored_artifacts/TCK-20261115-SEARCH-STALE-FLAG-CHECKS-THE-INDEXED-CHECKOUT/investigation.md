---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261115-SEARCH-STALE-FLAG-CHECKS-THE-INDEXED-CHECKOUT
artifact_type: investigation
tags: [ai, mcp]
---

# Investigation — TCK-20261115-SEARCH-STALE-FLAG-CHECKS-THE-INDEXED-CHECKOUT

Search order followed: `search_docs` (surfaced TCK-20261006-KNOWLEDGE-INDEX-STALE-WARNING and the live false positive, `stale: {changed: 5683, new: 49}`, in this very worktree), then `graphify query` (no useful code nodes for the topic), then targeted reads.

## Current Behavior

- `tools/search_mcp.py:63-84` `_resolve_index_dir(own_index_dir, own_root, main_root, own_index_opt_in)` returns the main checkout's index dir when it has a db, else the own dir; `RPG_SEARCH_OWN_INDEX=1` picks own when it exists. `search_mcp.py:87-90` binds `_INDEX_DIR` and `_DB_PATH` from it at import.
- `tools/search_mcp.py:156` `_run_search` calls `_ks.index_staleness(_DB_PATH)` with no corpus root.
- `tools/knowledge_search.py:673-700` `index_staleness(db_path, corpus_root=None)`: with no root it uses `Path(_REPO_ROOT_STR)` (this checkout, line 45/681), then compares `_corpus_source_paths(root)` and `os.path.getmtime(root / p)` against the manifest `db_path.parent/manifest.json`. A manifest built in the main checkout (paths relative, mtimes of main files) compared with a worktree's files gives thousands of `changed`. That is the bug.
- `knowledge_search.py:1097-1108` `cmd_query`: `db_path = args.db_path or _DEFAULT_DB`; passes `args.corpus_root` (when the arg exists) else None. So `query --db-path <main index>` run in a worktree has the same mismatch. The CLI default db is this checkout's own index and `_REPO_ROOT_STR` is its root, so that case is already consistent.
- Layout: `KNOWLEDGE_INDEX = agent-working/.index/knowledge-index` (`tools/agent_working_paths.py:36-39`), so db = `<root>/agent-working/.index/knowledge-index/knowledge.db`; the owning root is `db_path.parent` minus the 3 trailing parts of `KNOWLEDGE_INDEX`. `_write_manifest` is built with corpus root "." (`knowledge_search.py:~620-634`), so manifest paths are relative to the owning root.

## Mechanics / Engine Constraints

None from `docs/mechanics/` or `docs/engine/` (tooling only; no simulation behavior). Constraints that do apply:
- `index_staleness` must stay stat-only, never raise, and return None / dict / `{"unknown": True}` (docstring `knowledge_search.py:674-679`, and `docs/guidelines/agent_working_environment.md` "When the index is stale").
- Decision logic only; no index is rebuilt or moved (ticket Out of Scope).
- Decided root rule (owner, #715 6894176292, option b): when no `corpus_root` is passed, derive the root from `db_path` (the checkout owning the index); fall back to `_REPO_ROOT_STR` only when it cannot be derived. Scope item 1's "resolve once next to `_INDEX_DIR`" is therefore satisfied by the single derivation inside `index_staleness`: the MCP call needs no change beyond (optionally) nothing, and the CLI is fixed by the same code. Explicit `corpus_root` (CLI `--corpus-root`, test fixtures) still wins.

## Docs Requiring Update

Ran `python3 tools/gate_checks/docs_search.py --changed-file tools/search_mcp.py --changed-file tools/knowledge_search.py`. Two normative "required" hits (`knowledge_gateway_mcp_contract.md`, `redaction_retention_policy.md`) only cite `search_mcp.py` by path and do not state the staleness fact; read and rejected. Real fact-bearing doc:

- `docs/guidelines/agent_working_environment.md`: "When the index is stale" (l.452-463) says each worktree searches its own index and both paths compare against files on disk; it must state that the check compares the checkout that owns the index (main checkout for a worktree using the shared index, derived from `db_path`), and fix the now-wrong "each worktree searches its own index" sentence.

### Candidate docs (triage)

| path | hit kinds | first hit line |
|---|---|---|
| docs/plans/agent_infrastructure/AI_FIRST_SDLC_ARCHITECTURE_EVOLUTION_PLAN.md | path, symbol | 351 (P-6 defect row; Phase 5 item 1 may be marked done) |
| docs/plans/agent_infrastructure/AI_FIRST_SDLC_ARCHITECTURE_AUDIT.md | path, symbol | 438 / 464 (describes this defect; record of the audit, likely leave) |
| docs/ai/ticket-lifecycle.md | path, symbol | 609 |
| docs/engine/contracts/knowledge_gateway_mcp_contract.md | path | 40 |
| docs/parity_ledger/infrastructure.yaml | path, symbol | 6975 (unrelated BM25 entry; no staleness entry exists) |

### Excluded docs

| path | reason | hits |
|---|---|---|
| docs/brainstorm/agent-working-design/ai_first_architecture_maturity_review.html | review-record | 418 |
| docs/engine/contracts/knowledge_gateway_mcp/*.md (audit_phase0_5, keep_or_deprecate_decision, measurement_baseline_contract, phase1_baseline_comparison, phase4_workflow_recommendation) | historical-status | various |
| docs/plans/archive/** | historical-status | various |

Comment hits to update: `knowledge_search.py:676` docstring ("`corpus_root` defaults to this checkout's root") must change to "the checkout owning `db_path`"; `knowledge_search.py:51` comment is about `_INDEX_DIR`, unaffected.

## Parity Ledger Overlap

No entry covers index staleness (grep of `docs/parity_ledger/*.yaml` finds only unrelated "stale citation" text; `infrastructure.yaml` 6975-7003 is the BM25 fusion entry, not touched). No P0 entries. No ledger update required.

## Prior Work

- `agent-working/tickets/done/TCK-20261006-KNOWLEDGE-INDEX-STALE-WARNING.md` introduced `index_staleness`; tests in `tests/tools/test_knowledge_index_staleness.py`.
- TCK-20261112-SEARCH-SERVER-PER-WORKTREE-INDEX-AND-BUILD-MEMORY-GUARD (#888) introduced the shared main index and the regression.
- AUDIT/EVOLUTION_PLAN P-6 name this exact defect (`knowledge_search.py:681`).

## Risks and Open Questions

- Oracle: no Mechanics/Engine doc; oracle is the ticket ACs and the existing staleness docstring. Not `unresolved`.
- Derivation robustness: a `db_path` not shaped `<root>/agent-working/.index/knowledge-index/knowledge.db` (all existing tests use `<root>/index/knowledge.db`) must fall back to `_REPO_ROOT_STR` and not raise. Do not use `Path.resolve()` blindly: worktree `graphify-out` is a symlink, and resolving a symlinked index dir could point at a different root. Decide resolve vs not and test it.
- Behavior change for the CLI `--db-path /elsewhere/...` with the standard layout: now compares against that checkout. That is the intended AC3 outcome.
- AC1 live check cannot be a unit test; the implementer must run `python3 tools/knowledge_search.py query "<q>" --top-k 1 --db-path <main checkout index>` in a worktree and record it. Note the main checkout's own files may differ from the build (branch), which would legitimately still report stale.
- AC4 timing-bounded slow tests: classify per CI Failure Triage; state the marker filter used.
- Existing mcp test `_mcp` helper (`test_knowledge_index_staleness.py:131-133`) and `test_search_mcp.py:476` monkeypatch `index_staleness` as `lambda db:` / `lambda p:`; keeping the MCP call as `index_staleness(_DB_PATH)` (one positional arg) avoids breaking them.

## Anti-Drift Hazards

- Do not touch `_resolve_index_dir`, index location, or rebuild logic. Do not change which files `_corpus_source_paths` counts (a test asserts it equals the build's set).
- Do not add a second root rule in `search_mcp` that can drift from the CLI; the derivation lives in one place (`knowledge_search.py`).
- Do not change the stale payload shape or the `(abs diff > 0.01)` tolerance.
- Item 3 of Phase 5 (worktree searching its own branch content) is out of scope.
