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
(to be filled by the implementer)

## Test Summary
(to be filled by the implementer)

## Files Changed
(to be filled by the implementer)

## Completion Summary
(to be filled by the implementer)
