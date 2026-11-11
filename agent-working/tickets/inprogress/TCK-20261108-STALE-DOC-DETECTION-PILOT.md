---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261108-STALE-DOC-DETECTION-PILOT
phase: inprogress
date: 2026-11-08
tags: [ai, documentation, governance]
---

# TCK-20261108-STALE-DOC-DETECTION-PILOT

## Title
A read-only stale-doc detection run at a pinned SHA, and an evaluation report the owner uses to scope J3.

## Status
INPROGRESS

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Batches J1-J2 only (plan origin/lead-docs-review-source:agent-working/lead/docs_as_review_source_plan.md (rev 3.2; plan content @ d1fa1263c, pushed at 3ce5747fd; reaches main with lead-planner's PR), "Batch J: old and stale docs"). Owner approval #715 6720445592 ("approve full plan staged, J pilot only, yes to all three"); lead-planner finding 2026-11-08; owner dispatch of PR 1 in the agent-working-planner session 2026-11-08. The owner approved "J pilot only": J3 is not approved. Lands in PR 2 with the drift report it extends.

## Scope
1. J1: a detection mode of the drift-report tool (TCK-20261108-DOC-EVIDENCE-FIELDS-AND-DRIFT-REPORT), run read-only at a pinned SHA. Signals: evidence newer (ranked by lag and count of changed cited paths), unresolved name (reported as unresolved, renames shown via git rename detection), plan lifecycle (non-historical plan whose cited tickets are all done). Output: a ranked list per owning domain (route map).
2. Docs with `reviewed_by` stay quiet until their evidence or text changes again (same git-derived baseline as P1).
3. J2: an evaluation report under agent-working/stored_artifacts/ (.md or .jsonl, never .json: gitignored) with: flagged counts by signal and domain; the false-positive rate on about 20 hand-read docs; recall on the labelled set (items 1, 2, 4 and 6 at 531010a9a; 2 and 4 labelled undetectable by design); a sized J3 proposal. The report states its pin and that it is a docs audit.

## Out of Scope
- J3: fixing, retiring or marking any doc. No doc is edited by this ticket.
- Any test or tuning that targets the known docs (V1): recall is reported, never a threshold.

## Acceptance Criteria
1. The run is pinned and read-only (test: the working tree and docs/ are unchanged after a run).
2. The J2 report gives counts, measured false-positive rate and recall, and names its pin.
3. A reviewed_by doc with unchanged evidence and text is not flagged (test).
4. tests/tools/ passes in a lead slot.

## Related Tickets
- TCK-20261108-EPIC-DOCS-AS-REVIEW-SOURCE
- TCK-20261108-DOC-EVIDENCE-FIELDS-AND-DRIFT-REPORT

## Related Docs
- origin/lead-docs-review-source:agent-working/lead/docs_as_review_source_plan.md (rev 3.2; plan content @ d1fa1263c, pushed at 3ce5747fd; reaches main with lead-planner's PR)

## Related Stored Artifacts
- none

## Related Code Areas
- the drift-report tool from TCK-20261108-DOC-EVIDENCE-FIELDS-AND-DRIFT-REPORT

## Assumptions / Open Questions
- Plan's measured limit: a timestamp signal found 2 of the 4 known stale docs at 531010a9a (misses deterministic_execution.md and hard_law_monitor.md). Stated, not worked around.

## Implementation Notes
(to be filled by the implementer)

## Test Summary
(to be filled by the implementer)

## Files Changed
(to be filled by the implementer)

## Completion Summary
(to be filled by the implementer)
