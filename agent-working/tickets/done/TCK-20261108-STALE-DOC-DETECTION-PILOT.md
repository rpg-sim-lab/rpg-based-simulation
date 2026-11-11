---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261108-STALE-DOC-DETECTION-PILOT
phase: done
date: 2026-11-08
tags: [ai, documentation, governance]
---

# TCK-20261108-STALE-DOC-DETECTION-PILOT

## Title
A read-only stale-doc detection run at a pinned SHA, and an evaluation report the owner uses to scope J3.

## Status
DONE

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
Plan review conditions as in TCK-20261108-DOC-EVIDENCE-FIELDS-AND-DRIFT-REPORT (same PR); the ones that apply here: the sample is drawn by a fixed stride within each signal's ranked list (7/7/6), the verdicts and one-line reasons are mine, and the reviewer spot-checks 5; the report also states the wall time and `git status --porcelain -- docs/` before and after (both empty).
Measured, not tuned: 599 live docs at 5c6990e51, 480 flagged (80%); hand-read FP rate 10 of 20 (50%, or 60% with the 2 unclear counted false); recall on the labelled set 2 of 2 detectable items and 2 of 4 overall, as the plan predicted. No test or threshold targets the known docs; the tests use temp-repo fixtures only.
Hard lines kept: no doc was edited, retired or marked (J3 not approved); no doc received `verified_by` or `reviewed_by`; everything is advisory.
Self-correction recorded: the first draft of the report used 1,182 docs as the denominator (everything read) instead of the 599 live ones; `detect` now returns `live_docs` and the report was corrected before commit.

## Test Summary
- Detect-mode tests are in `tests/tools/test_doc_drift.py` (evidence-newer, unresolved name with rename, plan lifecycle with the real enum, exclusions, read-only and pinned, one-pass cost, reviewed_by quiet/flagged again, jsonl).
- Pilot run: `python3 tools/gate_checks/doc_drift_pilot.py --pin 5c6990e51c2cf1b6f0f842cb969772ba70d46485`: 20.3 s, `git status --porcelain -- docs/` empty before and after.
- Full `tests/tools` + `tests/docs` in a lead slot: requested from the planner before the push.

## Files Changed
tools/gate_checks/doc_drift.py (detect mode), tools/gate_checks/doc_drift_pilot.py, agent-working/stored_artifacts/TCK-20261108-STALE-DOC-DETECTION-PILOT/doc_stale_detection_pilot_5c6990e51.md (the J2 report), tests/tools/test_doc_drift.py.

## Completion Summary
The J1 detection mode and the J2 evaluation report are in. At the pin 5c6990e51 the detector flags 480 of 599 live docs; the hand-read sample shows 50-60% false positives (plan-lifecycle the most precise); recall on the labelled set is 2 of 2 detectable items. A sized J3 proposal is in the report for the owner to scope; nothing was edited.
