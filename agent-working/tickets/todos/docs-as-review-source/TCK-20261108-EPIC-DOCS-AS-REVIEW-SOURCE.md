---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261108-EPIC-DOCS-AS-REVIEW-SOURCE
phase: open
date: 2026-11-08
tags: [ai, documentation, governance, delivery, process-improvement]
---

# TCK-20261108-EPIC-DOCS-AS-REVIEW-SOURCE

## Title
Documents are the review source and stay correct: agent-working's batches B, C, D, E1, E2, J1-J2 and Q5.

## Status
EPIC_SCOPED

## Tier
epic

## Type
feature

## Priority
P1

## Request Summary
Owner approval #715 6720445592 ("approve full plan staged, J pilot only, yes to all three"); lead-planner finding 2026-11-08; owner dispatch of PR 1 in the agent-working-planner session 2026-11-08. The plan is the single source: origin/lead-docs-review-source:agent-working/lead/docs_as_review_source_plan.md (rev 3.2; plan content @ d1fa1263c, pushed at 3ce5747fd; reaches main with lead-planner's PR). This epic tracks only agent-working's batches. Batches A (rpg/lead/perf parts), F, G, H and I belong to other seats; I waits on owner dispositions.

## Scope
Children, in SEQUENCE.md order:
| Batch | Ticket | Tier | PR |
|---|---|---|---|
| B (F1, F5) | TCK-20261108-DOCS-REQUIRING-UPDATE-BUILT-BY-SEARCH | standard | 1 |
| B (F2, F3) | TCK-20261108-DOC-UPDATER-SATELLITE-STEP-AND-STALENESS-ADVISORY | standard | 1 |
| E1 (F4, P3 DoD, P5 rules without P1, CLAUDE.md lines) | TCK-20261108-DOC-STEP-ON-HAND-CLOSES-AND-REVIEW-RULES | hotfix | 1 |
| C + E2 + Q5 | TCK-20261108-DOC-EVIDENCE-FIELDS-AND-DRIFT-REPORT | standard | 2 |
| J1-J2 | TCK-20261108-STALE-DOC-DETECTION-PILOT | standard | 2 |
| D (P2) | TCK-20261108-PROJECT-FACTS-PAGE-GENERATED | standard | 3 |

## Out of Scope
- J3 (stale-doc remediation): not approved; scoped later by the owner from the J2 report.
- Batches A, F, G, H, I and their doc fixes (other seats).
- Seeding verified_by on any doc: that is batch H, under P1's rule.

## Acceptance Criteria
1. Every child ticket is in agent-working/tickets/done/.
2. The plan's acceptance criteria 1, 2, 3, 4 (doc-updater instructions part), 5 and 6 hold for the parts these children own.

## Related Tickets
- TCK-20261107-EVERY-PR-CLOSES-A-TICKET (PR rules these PRs follow)

## Related Docs
- origin/lead-docs-review-source:agent-working/lead/docs_as_review_source_plan.md (rev 3.2; plan content @ d1fa1263c, pushed at 3ce5747fd; reaches main with lead-planner's PR)
- docs/architecture/doc_updater_agent.md
- docs/audits/D25_engine_docs_drift.md

## Related Stored Artifacts
- none

## Related Code Areas
- .claude/agents/investigator.md, .claude/agents/doc-updater.md, .claude/workflows/implement-ticket.js
- tools/gate_checks/doc_staleness_check.py, tools/validate_frontmatter.py, tools/agent-monitoring/

## Assumptions / Open Questions
- Copying the plan into tickets is not allowed (define-once rule, lead 2026-11-08); children cite its sections.
- CLAUDE.md edits are approved in principle; the owner reviews the actual diff before merge.

## Implementation Notes
(to be filled by the implementer)

## Test Summary
(to be filled by the implementer)

## Files Changed
(to be filled by the implementer)

## Completion Summary
(to be filled by the implementer)
