---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261108-DOC-UPDATER-SATELLITE-STEP-AND-STALENESS-ADVISORY
phase: open
date: 2026-11-08
tags: [ai, documentation, process-improvement]
---

# TCK-20261108-DOC-UPDATER-SATELLITE-STEP-AND-STALENESS-ADVISORY

## Title
doc-updater triages candidate satellite docs, and the doc-staleness gate lists untouched docs that cite changed code.

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Batch B, parts F2 and F3 of the plan (origin/lead-docs-review-source:agent-working/lead/docs_as_review_source_plan.md (rev 3.2; plan content @ d1fa1263c, pushed at 3ce5747fd; reaches main with lead-planner's PR), "Owner correction (2026-11-07)" F2/F3, "Normative sources and precedence (R3)", acceptance criteria 1 and 4). Owner approval #715 6720445592 ("approve full plan staged, J pilot only, yes to all three"); lead-planner finding 2026-11-08; owner dispatch of PR 1 in the agent-working-planner session 2026-11-08.

## Scope
1. F2: `.claude/agents/doc-updater.md` Step 0 and "What to Do" gain a satellite step after the required docs. For each candidate from TCK-20261108-DOCS-REQUIRING-UPDATE-BUILT-BY-SEARCH, update it if it restates the changed fact, otherwise report it in `docs_skipped` with a reason. "Never derive yourself" is lifted for candidates only.
2. F2 rules, written into doc-updater's instructions: edit explanatory docs only; change a normative doc only when the ticket itself changes intended behaviour and cites the rule owner's approval, otherwise report the disagreement as a defect or a divergence; never edit history docs; never write a defect into a normative doc as if intended (plan AC 4).
3. Wire the candidate list into the Document-Update phase prompt in `.claude/workflows/implement-ticket.js` (:1211-1273) and its schema if needed.
4. F3: `tools/gate_checks/doc_staleness_check.py` adds an advisory list of docs that cite a changed src file or symbol but were not touched, minus the history exclusion, using the shared search from the sibling ticket. It never blocks. Hits on critical-invariant docs (determinism, conservation, persistence and restore, concurrency, message acknowledgement: plan P5) come first and are named in the close summary.

## Out of Scope
- Building the search (sibling ticket).
- Hand-close doc step (E1 ticket).
- Any blocking behaviour in the gate.

## Acceptance Criteria
1. Plan AC 1 end to end: on the #837 and #786 replay fixtures, F2's instructions plus F3's list cover items 1, 2, 5 and 6, and item 9 is excluded and not edited (a test asserts F2's input marks it excluded).
2. doc_staleness_check.py's exit code is unchanged by the advisory list (test).
3. The critical-invariant ordering has a test.
4. tests/tools/ passes in a lead slot; paths-guard tests run before push.

## Related Tickets
- TCK-20261108-EPIC-DOCS-AS-REVIEW-SOURCE
- TCK-20261108-DOCS-REQUIRING-UPDATE-BUILT-BY-SEARCH

## Related Docs
- origin/lead-docs-review-source:agent-working/lead/docs_as_review_source_plan.md (rev 3.2; plan content @ d1fa1263c, pushed at 3ce5747fd; reaches main with lead-planner's PR)
- docs/architecture/doc_updater_agent.md

## Related Stored Artifacts
- none

## Related Code Areas
- .claude/agents/doc-updater.md (Step 0, :11-34)
- tools/gate_checks/doc_staleness_check.py (check_doc_staleness, :39)
- .claude/workflows/implement-ticket.js (Document-Update, :1211-1273)

## Assumptions / Open Questions
- Owner's proportionate rule: agent-tooling checks over docs stay advisory.

## Implementation Notes
(to be filled by the implementer)

## Test Summary
(to be filled by the implementer)

## Files Changed
(to be filled by the implementer)

## Completion Summary
(to be filled by the implementer)
