---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261116-THIRTEEN-DEAD-KNOWLEDGE-GATEWAY-DOCS-MOVE-TO-THE-ARCHIVE
phase: done
date: 2026-11-16
tags: [documentation, mcp]
---

# TCK-20261116-THIRTEEN-DEAD-KNOWLEDGE-GATEWAY-DOCS-MOVE-TO-THE-ARCHIVE

## Title
Thirteen knowledge-gateway (KGMCP) documents whose code was removed in #147 still sit in docs/engine/contracts as if current; move them to docs/archive/knowledge_gateway_mcp/, keep the one live spec, and leave no dead path behind

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P3

## Request Summary
Owner decisions on #715, both given in lead-planner's session by AskUserQuestion:
- 6911224913, Q1: "Move to archive (Recommended)", i.e. move the knowledge-gateway documents in docs/engine to the docs archive and mark them historical. The code was removed in #147 (2026-09-08).
- 6911534263: "Keep it, archive the 13 (Recommended)". redaction_retention_policy.md stays in place as active, because it is the live spec (§2-§9) of tools/write_path_guard.py, which the secret-scan PreToolUse hook runs. Its dead paths get fixed. The other 13 move.

The move list and the inbound references were measured by agent-working-designer at origin/main db6b4579d. The source is the main checkout's `.claude/handover/drafts/kgmcp_archive_move_list.md`, section "Update 2026-11-16". This ticket carries the edits in full, so the draft is not needed to do the work. rpg-planner-ubuntu filed it at lead-planner's request, because docs/engine is the rpg domain's. Filing only: dispatch needs a separate owner go.

## Scope
### A. The move (rpg lane), `git mv` so history is kept
Target for every file: `docs/archive/knowledge_gateway_mcp/<same file name>`.
1. `docs/engine/contracts/knowledge_gateway_mcp_contract.md`. Status changes from active to `status: historical`. It is the only active file among the 13.
2. These 12, all already `status: historical`, from `docs/engine/contracts/knowledge_gateway_mcp/`:
   - `audit_phase0_5.md`
   - `cache_migration_plan.md`
   - `evidence_cache_identity_contract.md`
   - `keep_or_deprecate_decision.md`
   - `measurement_baseline_contract.md`
   - `phase1_baseline_comparison.md`
   - `phase2_baseline_recomparison.md`
   - `phase3_pilot_acceptance_measurement.md`
   - `phase4_direct_tool_comparison.md`
   - `phase4_warm_direct_tool_comparison.md`
   - `phase4_workflow_recommendation.md`
   - `phase5_repeated_demand_measurement.md`

These stay where they are: `redaction_retention_policy.md`, which stays active, and the nine non-markdown files in `docs/engine/contracts/knowledge_gateway_mcp/`. The nine are five `*.schema.json`, three `provider_capabilities_*.json` and `shared_enums.schema.json`; `git ls-files 'docs/engine/contracts/knowledge_gateway_mcp*'` lists them. Every path to them is unchanged.

### B. The rewrite rule, for every reference in a live file
- `docs/engine/contracts/knowledge_gateway_mcp/<name>.md` becomes `docs/archive/knowledge_gateway_mcp/<name>.md`, for the 12 names in A.2 only.
- `docs/engine/contracts/knowledge_gateway_mcp_contract.md` becomes `docs/archive/knowledge_gateway_mcp/knowledge_gateway_mcp_contract.md`.
- Never rewrite a reference to `redaction_retention_policy.md`, or to a `.json` file in that directory.
- The rule also applies inside the 13 moved files, where they cite each other, so the archive holds no dead link to a sibling. A moved file that cites a schema keeps the `docs/engine/...` schema path.
- Test code that builds a path from parts needs the edits in D below, because a string replace does not see it.

### C. Edits in rpg-owned files (rpg lane)
- `docs/parity_ledger/infrastructure.yaml`: 18 lines name a moved file (rpg-planner-ubuntu, measured at db6b4579d with AC2's pattern): 9473, 9513, 9578, 9587, 9863, 9896, 9983, 10055, 10213, 10343, 10542, 10560, 10565, 10575, 10598, 10685, 10715, 10812. The draft's estimate of about ten, near 9385-9473, was low. Apply rule B through `tools/parity_ledger_writer.py`, not a full-file YAML rewrite. Record `git diff --stat` before and after; the diff must touch only those lines. Leave unchanged the other `knowledge_gateway_mcp` mentions in the ledger (e.g. 9385, 9410, 9462: the removed `tools/knowledge_gateway_mcp.py` and `tests/tools/test_knowledge_gateway_mcp.py`, and doc-id strings). They record what was true when each entry was written, and no moved file is named there.
- `docs/guidelines/intentional_divergences.md`, 2 lines, about 1298 and 1318: apply rule B. Line about 1305 names a schema, which stays, so it is unchanged.
- `docs/engine/contracts/knowledge_gateway_mcp/redaction_retention_policy.md` stays, status active. List its dead paths, which point at removed gateway files, with the dead-path script in D's check. Decide per path: rewrite to the archive path where the target moved; reword without a path where the target file was removed.

### D. Edits in agent-working-owned files (agent-working lane)
1. `tests/tools/test_evidence_cache_identity_contract.py`, lines 27-33. TRAP: one `_CONTRACTS_DIR` builds the paths of both the moving `.md` files and the schemas that stay. Split it exactly so:
   ```
   _CONTRACTS_DIR = _REPO_ROOT / "docs" / "engine" / "contracts" / "knowledge_gateway_mcp"
   _ARCHIVE_DIR = _REPO_ROOT / "docs" / "archive" / "knowledge_gateway_mcp"

   _IDENTITY_CONTRACT_MD = _ARCHIVE_DIR / "evidence_cache_identity_contract.md"
   _EVIDENCE_KINDS_SCHEMA = _CONTRACTS_DIR / "evidence_identity_kinds.schema.json"
   _MIGRATION_PLAN_MD = _ARCHIVE_DIR / "cache_migration_plan.md"
   _SHARED_ENUMS = _CONTRACTS_DIR / "shared_enums.schema.json"
   _REQUEST_SCHEMA = _CONTRACTS_DIR / "knowledge_context_request.schema.json"
   ```
   In the module docstring (lines 6-7), say that the two `.md` files now live in `docs/archive/knowledge_gateway_mcp/` and the schema stays.
2. `tests/docs/test_phase4_direct_tool_comparison_doc.py`, lines 12-19: in `_DOC_PATH`, replace the parts `"engine" / "contracts" / "knowledge_gateway_mcp"` with `"archive" / "knowledge_gateway_mcp"`.
3. `tests/docs/test_phase4_workflow_recommendation_doc.py`, lines 17-50: make the same replacement in `_RECOMMENDATION_DOC` and in three `_REAL_CITED_PATHS` entries: `phase1_baseline_comparison.md`, `phase2_baseline_recomparison.md` and `phase3_pilot_acceptance_measurement.md`. The fourth entry, `RETRO-2026-W33.md`, is unchanged.
4. `tests/docs/test_redaction_retention_policy_doc.py`: unchanged, because its file stays.
5. Docstrings and comments only, no behaviour change:
   - `tests/tools/test_retrieval_cache.py` names `cache_migration_plan.md`: rewrite it.
   - `tests/tools/test_write_path_guard.py` names `redaction_retention_policy.md`: unchanged.
   - `tools/write_path_guard.py` line about 61, a comment naming `phase2_baseline_recomparison.md`: rewrite to the archive path.
6. `tests/tools/fixtures/kgmcp_phase4_direct_tool_comparison_results.json` names `measurement_baseline_contract.md` and `knowledge_gateway_mcp_contract.md`. Read it first. If the strings are recorded evidence text that no test asserts as a path, leave them and say so in the Test Summary. If a test asserts the path, rewrite it.
7. `tools/retrieval_cache.py`, lines 802 and 883. Both docstrings name `tools/knowledge_gateway_mcp.py::_run_knowledge_status()`, a file removed in #147. No move is involved: name what replaced it, or word the docstring without a path. Owner: `tools/retrieval_cache.py` routes as unowned. This ticket assigns the edit to the agent-working lane, because the module's tests (`tests/tools/test_retrieval_cache.py`, `tests/tools/test_evidence_cache_identity_contract.py`) are agent-working's. It's a docstring-only change.
8. Docs in agent-working's owns:
   - `docs/plans/knowledge-gateway-mcp-proposal.md`, about 30 mentions: apply rule B. It may also get a `status: historical` banner, but the rewrite still applies, so that no dead path remains.
   - `docs/plans/agent_infrastructure/ai_first_hardening_epics/standalone_items.md`, one path (`keep_or_deprecate_decision.md`): apply rule B.
   - `docs/observability/retrieval_retention_redaction_policy.md` names `redaction_retention_policy.md`: unchanged.

### E. Checked, no change needed (rpg-planner-ubuntu, origin/main db6b4579d)
`git grep 'engine/contracts/knowledge_gateway_mcp'` also matches three test files the draft did not list. Each uses the string as a synthetic doc id or temp-dir name inside its own fixture tree, not as a path to a real file:
- `tests/tools/test_knowledge_search.py`:841/850/895/904 (`.../knowledge_gateway_mcp/foo` under a tmp `docs_root`)
- `tests/tools/test_search_mcp.py`:94
- `tests/tools/test_search_server.py`:188 (a `new_scheme` doc-id string)

Leave them, unless the implementer finds one that reads a real file.

## Out of Scope
- Moving or editing the nine `.json` files, or `redaction_retention_policy.md`'s location or status.
- Extracting the redaction spec into a new document (option C, not chosen).
- Search ranking of historical docs (owner Q2) and the four report-only doc-truth checks (owner Q3). Those are agent-working-designer's docs-truth plan, not this ticket.
- Rewriting history: `agent-working/tickets/**`, `agent-working/stored_artifacts/**`, monitoring shards, `agent-working/handover-transit/**`, and the generated `docs/REGISTRY.yaml`, which the close step regenerates.
- Any `src/` change.

## Acceptance Criteria
1. The 13 files exist under `docs/archive/knowledge_gateway_mcp/`, moved by `git mv`, so `git log --follow` reaches their history. None remain at their old paths. `knowledge_gateway_mcp_contract.md` has `status: historical`. `redaction_retention_policy.md` and the nine `.json` files are unchanged in place.
2. No old path is left: `git grep -nE 'docs/engine/contracts/knowledge_gateway_mcp(_contract\.md|/(audit_phase0_5|cache_migration_plan|evidence_cache_identity_contract|keep_or_deprecate_decision|measurement_baseline_contract|phase1_baseline_comparison|phase2_baseline_recomparison|phase3_pilot_acceptance_measurement|phase4_direct_tool_comparison|phase4_warm_direct_tool_comparison|phase4_workflow_recommendation|phase5_repeated_demand_measurement)\.md)' -- . ':!agent-working/tickets' ':!agent-working/stored_artifacts' ':!agent-working/agent-monitoring' ':!agent-working/handover-transit' ':!docs/REGISTRY.yaml'` prints nothing. The path-from-parts edits in D.1-D.3 are made.
3. Dead paths fall. Run the dead-path measure from agent-working-designer's docs-truth plan (section 6) over `docs/` before and after, on the same base. The count of KGMCP-related dead paths goes down and no new dead path appears. Record both counts and the commands in the Test Summary.
4. `tools/retrieval_cache.py` no longer names `tools/knowledge_gateway_mcp.py`.
5. `docs/parity_ledger/infrastructure.yaml` changed only on the evidence lines that name moved files. Show `git diff --stat` and the line list. These ledger tests pass: `pytest tests/tools/test_parity_ledger_schema.py tests/tools/test_parity_ledger_check.py tests/codebase/test_parity_ledger_schema_gate.py`, capped.
6. Scoped tests pass, run capped (3G scope, swap 0, CPUs 4-5, PYTHONHASHSEED=0): `pytest tests/docs/test_phase4_direct_tool_comparison_doc.py tests/docs/test_phase4_workflow_recommendation_doc.py tests/docs/test_redaction_retention_policy_doc.py tests/tools/test_evidence_cache_identity_contract.py tests/tools/test_write_path_guard.py tests/tools/test_retrieval_cache.py`. Also run `tests/tools/test_generate_registry.py` after the close-step regeneration.
7. Two-lane review, each by PR comment or message:
   - rpg (rpg-planner-ubuntu): the parity ledger edit, the intentional_divergences lines, the move and status flip, and the redaction-policy dead-path fixes.
   - agent-working (agent-working-planner or agent-working-designer): the tests/docs, tests/tools and tools/ edits, including the `_CONTRACTS_DIR` split and `tools/retrieval_cache.py`.

## Related Tickets
- TCK-20260908-KGMCP-DELETE-ARCHIVED-GATEWAY (removed the gateway code, #147)
- TCK-20260909-KGMCP-DOC-STATUS-SWEEP (flipped 11 of 12 docs to historical)
- TCK-20260907-KGMCP-REDACTION-EXTRACT-ARCHIVE (extracted tools/write_path_guard.py)
- TCK-20261031-EPIC-AI-FIRST-SDLC-EVOLUTION (the docs-truth plan these owner decisions answer)

## Related Docs
- docs/engine/contracts/knowledge_gateway_mcp_contract.md and docs/engine/contracts/knowledge_gateway_mcp/ (before the move)
- docs/archive/README.md (archive conventions)
- docs/guidelines/intentional_divergences.md, docs/parity_ledger/infrastructure.yaml

## Related Stored Artifacts
None. The move list is the main checkout's untracked `.claude/handover/drafts/kgmcp_archive_move_list.md`. Everything needed is copied into Scope.

## Related Code Areas
- tools/write_path_guard.py
- tools/retrieval_cache.py
- tests/docs/test_phase4_*_doc.py
- tests/docs/test_redaction_retention_policy_doc.py
- tests/tools/test_evidence_cache_identity_contract.py
- tests/tools/test_retrieval_cache.py
- tests/tools/test_write_path_guard.py

## Assumptions / Open Questions
- Lane split in one change: the rpg lane does A, C and the in-archive rewrite; the agent-working lane does D. The owner's dispatch go names who implements. One implementer can do both, with both reviews.
- The dead-path script is the one in the docs-truth plan's section 6. If it isn't on main when this is dispatched, the implementer runs the same measure from the draft plan and cites its sha256.
- The docs search index, rebuilt by `make knowledge-index-update` from the main checkout, will drop the old paths. That runs after merge, not in this change.

## Implementation Notes
- Out of Scope narrowed by rpg-planner-ubuntu: the nine .json files are not moved; one description string in evidence_identity_kinds.schema.json is rewritten to the archive path so it does not become a dead path. (Ruling in the dispatch thread.)
- Parity ledger: edited by exact-line replacement, not tools/parity_ledger_writer.py (its CLI is --check only; its write_entry rewrites the whole shard, which is the churn the ticket rule meant to avoid; accepted by rpg-planner-ubuntu). `git diff --stat docs/parity_ledger/infrastructure.yaml`: before empty, after 18 insertions and 18 deletions, on exactly lines 9473, 9513, 9578, 9587, 9863, 9896, 9983, 10055, 10213, 10343, 10542, 10560, 10565, 10575, 10598, 10685, 10715, 10812. `parity_ledger_writer.py --check` exit 0.
- Fixture tests/tools/fixtures/kgmcp_phase4_direct_tool_comparison_results.json left unchanged: recorded measurement text, no test asserts those paths (tests/docs/test_phase4_direct_tool_comparison_doc.py reads entry ids, routing shapes and verdicts; test_knowledge_gateway_archival.py lists only the file name), and it sits under tests/, outside AC3's docs/ measure. Excluded from AC2 for that reason.
- redaction_retention_policy.md stays active in place. Its 22 dead tool/test paths (pointing at gateway files removed in #147 or their archive copies) were reworded without a directory path (the file name stays as a name); 9 paths to moved docs were rewritten to the archive. tools/write_path_guard.py::ALLOWED_SOURCE_TYPES is a live file the measure flags only because of its `::` suffix; unchanged.
- tools/retrieval_cache.py lines 802 and 883: docstring-only, no function replaced the removed status reporter, so they say "the knowledge-status report (gateway removed in #147)".
- Rule B was applied inside the 13 moved files; knowledge_gateway_mcp_contract.md has status historical.

## Test Summary
Scoped run (3 GB scope, swap 0, CPUs 4-5, PYTHONHASHSEED=0): tests/docs/test_phase4_direct_tool_comparison_doc.py, test_phase4_workflow_recommendation_doc.py, test_redaction_retention_policy_doc.py, tests/tools/test_evidence_cache_identity_contract.py, test_write_path_guard.py, test_retrieval_cache.py, the three parity ledger tests (tests/tools/test_parity_ledger_schema.py, test_parity_ledger_check.py, tests/codebase/test_parity_ledger_schema_gate.py) and tests/tools/test_knowledge_gateway_archival.py: 202 passed. After the schema string edit and registry regeneration: test_evidence_cache_identity_contract, tests/docs/test_doc_path_existence.py, tests/tools/test_generate_registry.py: 90 passed, 1 xfailed.
AC2: the specified `git grep -nE` prints nothing with tests/tools/fixtures/kgmcp_phase4_direct_tool_comparison_results.json excluded (recorded text, see Implementation Notes); with it included it prints that fixture's 15 lines only.
AC3 dead-path measure (backticked src/tools/tests/.claude/.github/registries/docs/frontend/scripts paths in tracked docs/**/*.md except docs/archive/, checked against git ls-files and parent dirs; script per docs_truth_plan.md section 6, sha256 98c39dbeaa7c5daa..., run at the same base 026e18323 plus this branch): before total dead 1476 (KGMCP-related 150, 309 files with dead paths); after 1355 (KGMCP-related 39, 297 files). No dead path is new once the file move is accounted for (0). Of the drop, 99 dead references lived in the 13 moved files, which leave the measure because it skips docs/archive/; the other KGMCP drop is the 18 rewritten + 22 reworded paths in live files.
Known gap: the measure treats a `path::symbol` token as a dead path, so tools/write_path_guard.py::ALLOWED_SOURCE_TYPES (a live file) still counts.
Known gap: this change moves docs only; no sim runs, no src change, hot-loop timing not applicable.

## Files Changed

## Completion Summary
Thirteen dead knowledge-gateway documents moved to docs/archive/knowledge_gateway_mcp/ by git mv (history kept); the contract is status historical; redaction_retention_policy.md and the nine .json files stay (one schema description string rewritten). Every live reference follows rule B, the test path-from-parts are split, and the dead-path count over docs/ fell from 1476 to 1355. Two-lane review pending: rpg-planner-ubuntu (ledger, divergences, move and status, redaction fixes) and agent-working (tests/docs, tests/tools, tools/). Not pushed.
