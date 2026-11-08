---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261108-DOCS-REQUIRING-UPDATE-BUILT-BY-SEARCH
phase: inprogress
date: 2026-11-08
tags: [ai, documentation, process-improvement]
---

# TCK-20261108-DOCS-REQUIRING-UPDATE-BUILT-BY-SEARCH

## Title
Investigate builds "Docs Requiring Update" by search, as required, candidate and excluded lists.

## Status
INPROGRESS

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Batch B, parts F1 and F5 of the plan (origin/lead-docs-review-source:agent-working/lead/docs_as_review_source_plan.md (rev 3.2; plan content @ d1fa1263c, pushed at 3ce5747fd; reaches main with lead-planner's PR), sections "Owner correction (2026-11-07)" F1/F5 and "Normative sources and precedence (R3)"). Owner approval #715 6720445592 ("approve full plan staged, J pilot only, yes to all three"); lead-planner finding 2026-11-08; owner dispatch of PR 1 in the agent-working-planner session 2026-11-08. #837 went through the standard pipeline and still left three satellite docs stale, because Investigate's list is judgment only.

## Scope
1. F1: the investigator (`.claude/agents/investigator.md` and the investigator prompt in `.claude/workflows/implement-ticket.js`) builds `## Docs Requiring Update` from a search over: the changed src paths; their importers (graphify's import graph) and the `registries/mechanisms.yaml` entries whose `implemented_by` cites them; changed public symbols; old-behaviour terms the ticket removes; the topic's canonical doc (topic map P4, when it exists).
2. Output three lists: **required** (normative or canonical docs that state the changed fact), **candidate** (other hits to triage: direct hits, then importer and mechanism hits), **excluded** (history docs per the plan's R3 list, each with its reason). History exclusion covers docs/archive/, docs/audits/, docs/REGISTRY.yaml and plans whose frontmatter status is historical or superseded.
3. F5: the same search covers comments and docstrings in the changed src files that state an invariant, lifecycle, concurrency or recovery behaviour. Other comments are out of scope.
4. Put the search in a reusable tool function (proposed: under `tools/gate_checks/`, shared with F3 in TCK-20261108-DOC-UPDATER-SATELLITE-STEP-AND-STALENESS-ADVISORY and later the P1 drift report), not only in prompt text, so the replay is testable.
5. Keep the existing `docs_to_update` contract consumed by Verify's `check_docs_to_update_coverage` working: required docs feed it; candidates do not make Verify block.
6. Replay fixtures for the #837 and #786 diffs (pinned SHAs), committed for the acceptance test.

## Out of Scope
- doc-updater's satellite step and the gate advisory (sibling ticket, same PR).
- The topic map itself (lead, batch F): use it only if present.
- Editing any doc found by the replay.

## Acceptance Criteria
1. On the #837 and #786 replay fixtures, the search puts plan audit items 1, 2, 5 and 6 in required or candidate, and item 9 (`import_linter_soak_review.md:179`) in excluded with a reason.
2. The noise is reported, not tuned to the known items: candidate count per changed path is recorded in the ticket (plan's measured basis: about 19-25 per path).
3. A test covers each exclusion class and an F5 comment hit.
4. Verify's docs_to_update coverage check still passes for an existing fixture ticket.
5. tests/tools/ passes in a lead slot; paths-guard tests run before push.

## Related Tickets
- TCK-20261108-EPIC-DOCS-AS-REVIEW-SOURCE
- TCK-20261108-DOC-UPDATER-SATELLITE-STEP-AND-STALENESS-ADVISORY
- TCK-20260823-HOTFIX-INVESTIGATOR-EXCLUDED-DOC-BULLET-TEMPLATE-GAP (existing excluded-bullet template)

## Related Docs
- origin/lead-docs-review-source:agent-working/lead/docs_as_review_source_plan.md (rev 3.2; plan content @ d1fa1263c, pushed at 3ce5747fd; reaches main with lead-planner's PR)
- docs/architecture/doc_updater_agent.md

## Related Stored Artifacts
- none

## Related Code Areas
- .claude/agents/investigator.md (`## Docs Requiring Update`, :74; docs_to_update output, :224)
- .claude/workflows/implement-ticket.js (Investigate prompt; Document-Update phase :1211-1273)
- tools/gate_checks/done_checker_static.py (check_docs_to_update_coverage)

## Assumptions / Open Questions
- .claude/workflows/implement-ticket.js and the shared helper's home are unowned in the route map; the plan assigns this work to agent-working. Designer reviews the design (plan.md) before Implement.
- If graphify's import graph is unavailable in a worktree, the search falls back to direct path and symbol hits and says so in its output.

## Implementation Notes
- `tools/gate_checks/docs_search.py::search_docs_for_change` (MARKER-JSON CLI): required / candidate / excluded plus F5 `comment_hits`. Reads through a `DirSource` (working tree) or `GitRefSource` (a pinned ref, so a replay is repeatable). Public symbols are non-underscore `def`/`class` names; only identifier-shaped ones (underscore or two capitals) are searched, a rule about shape, not a stoplist. Old terms: `--old-term` plus public symbols at base and absent at head. Importers: graphify's `imports` edges when the graph was built at HEAD and no ref is pinned, else a regex scan of `src/`; the output names which ran. Mechanism hits come from `registries/mechanisms.yaml` `implemented_by`.
- Exclusion classes (planner decision 2026-11-08): `archive`, `audit`, `registry`, `historical-status`, and the new `review-record` (stem ends `_review`, `_report`, `_audit`). Excluded entries keep their hits and reason. The class excludes 14 files under docs/ (listed in investigation.md); one, `docs/ai/codex_posttool_adapter_exact_config_diff_for_review.md`, looks like a live proposal.
- AC 1's item-9 clause is checked on a third fixture, the #819 diff (`61e984212`), because item 9 (`import_linter_soak_review.md`) cannot be a hit on #837 or #786: neither diff's paths or terms appear in it, and its frontmatter says `status: active`. This was the planner's decision on 2026-11-08 (add the `review-record` class and the third fixture).
- Measured noise (`python3 -m tools.gate_checks.docs_search_replay`, real git at pinned SHAs, docs/ and agent-working/ paths dropped from the changed set): #837 9 code paths -> required 12, candidate 80 (8.9 per path), excluded 74; items 1 and 2 required, item 6 candidate. #786 7 paths -> required 1, candidate 18 (2.6 per path); README.md (item 5) found as a candidate, also without `--old-term`. #819 1 path -> candidate 4, excluded 1 (item 9, `review-record`). The plan's basis was about 19-25 per path before the symbol-shape rule; before it, the first run returned 84 required docs for #837 because one-word names such as `execute` match prose.
- `investigator.md` and the Investigate prompt in `implement-ticket.js` tell the investigator to run the search with the planned code paths and write required as Format 1 bullets and candidate / excluded as tables (a table row never matches the Verify regex, tested).
- Deviation from the ticket text: fixtures are minimal subsets (the cited lines plus one decoy per class); the real-history counts come from the replay script, not from CI.

## Test Summary
- `tests/tools/test_docs_search.py`: 29 tests, all pass (light slot, cores 0-3, MemoryMax 1G).
- Scoped: the 57 test files that mention investigator.md / implement-ticket.js / doc-updater / doc_staleness: 839 passed, 13 skipped, 1 xfailed; `test_agent_working_paths_guard.py` + `test_delivery_pr_render.py` + `tests/docs`: 194 passed.
- `codebase.health check`: exit 0 (2 new report-only rows in src, not from this change).
- Full `tests/tools`: see the final entry below.
- Known gap: none stated beyond the planned-paths limit (the gate-time run uses the real diff).

## Files Changed
tools/gate_checks/docs_search.py; tools/gate_checks/docs_search_replay.py; tests/tools/test_docs_search.py; tests/tools/fixtures/docs_search/**; .claude/agents/investigator.md; .claude/workflows/implement-ticket.js (Investigate prompt); this ticket; staging artifacts.

## Completion Summary
The investigator can build `## Docs Requiring Update` from a pinned, repeatable search with required / candidate / excluded lists and F5 comment hits; the replay finds audit items 1, 2, 5 and 6, excludes item 9 on its own fixture, and the measured noise is recorded above.
