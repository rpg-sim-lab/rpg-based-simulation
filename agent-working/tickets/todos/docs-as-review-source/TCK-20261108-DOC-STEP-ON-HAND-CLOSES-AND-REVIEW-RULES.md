---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261108-DOC-STEP-ON-HAND-CLOSES-AND-REVIEW-RULES
phase: open
date: 2026-11-08
tags: [ai, documentation, governance, delivery, claude-md]
---

# TCK-20261108-DOC-STEP-ON-HAND-CLOSES-AND-REVIEW-RULES

## Title
Hand-orchestrated closes get the doc step, the Definition of Done records known defects, and the review rules that don't need P1 are written down.

## Status
OPEN

## Tier
hotfix

## Type
chore

## Priority
P1

## Request Summary
Batch E1 of the plan (origin/lead-docs-review-source:agent-working/lead/docs_as_review_source_plan.md (rev 3.2; plan content @ d1fa1263c, pushed at 3ce5747fd; reaches main with lead-planner's PR), F4, P3, P5 and "Normative sources and precedence (R3)"). Owner approval #715 6720445592 ("approve full plan staged, J pilot only, yes to all three"); lead-planner finding 2026-11-08; owner dispatch of PR 1 in the agent-working-planner session 2026-11-08. Depends on batch B (it names B's search as the hand-close step). CLAUDE.md is a governing file: the owner approved the policy in principle and reviews the actual diff before merge.

## Scope
1. F4: CLAUDE.md "After Work" gains one line: run doc-updater, or the F1 search (TCK-20261108-DOCS-REQUIRING-UPDATE-BUILT-BY-SEARCH), before a hand-orchestrated close. `docs/guides/delivery_process.md` carries the detail.
2. P3: the Definition of Done gains the known-defects wording next to "Docs were updated if behavior changed" (CLAUDE.md :244): a found behaviour defect gets a limits line citing its ticket in the same change; the fix PR moves it. Detail in delivery_process.md.
3. P5 rules that don't cite P1, in delivery_process.md: start from documents; scope (docs audit vs implementation audit, a docs-only audit never claims the code correct); pin (R5 wording, including that a branch behind main is a valid subject when the review is about it); fix a wrong explanatory doc in the same PR; a wrong normative doc goes to its rule owner.
4. One CLAUDE.md line for P5 (X27 wording from the plan), pointing to delivery_process.md.
5. CLAUDE.md Mechanics Bible table: add chapter 07 (`07_social_political_dynamics.md`); the table lists 6 of 7.

## Out of Scope
- P5 rules that cite P1 (verified_by, drift, critical-invariant evidence): batch E2, in TCK-20261108-DOC-EVIDENCE-FIELDS-AND-DRIFT-REPORT.
- Any limits entries themselves (batch A, other seats).
- Plan audit item 8 (designer.md/planner.md wording vs #840): judgment item, not in this ticket.

## Acceptance Criteria
1. The CLAUDE.md diff is shown to the owner and gets a direct OK before commit (recorded in Implementation Notes with the answer).
2. Each CLAUDE.md addition is a pointer line; the rule text lives once, in delivery_process.md.
3. Tests that pin CLAUDE.md or delivery_process.md shape (grep tests/ for them) pass.
4. Governing-edit rows appear for the CLAUDE.md edit as the guard records them.

## Related Tickets
- TCK-20261108-EPIC-DOCS-AS-REVIEW-SOURCE
- TCK-20261108-DOCS-REQUIRING-UPDATE-BUILT-BY-SEARCH
- TCK-20261107-EVERY-PR-CLOSES-A-TICKET (last CLAUDE.md pointer-line edit; same pattern)

## Related Docs
- origin/lead-docs-review-source:agent-working/lead/docs_as_review_source_plan.md (rev 3.2; plan content @ d1fa1263c, pushed at 3ce5747fd; reaches main with lead-planner's PR)
- docs/guides/delivery_process.md
- CLAUDE.md

## Related Stored Artifacts
- none

## Related Code Areas
- CLAUDE.md ("After Work", "Definition of Done" :235-244, Mechanics Bible table)
- docs/guides/delivery_process.md

## Assumptions / Open Questions
- CLAUDE.md and delivery_process.md are unowned in the route map; agent-working edited both in #840.

## Implementation Notes
(to be filled by the implementer)

## Test Summary
(to be filled by the implementer)

## Files Changed
(to be filled by the implementer)

## Completion Summary
(to be filled by the implementer)
