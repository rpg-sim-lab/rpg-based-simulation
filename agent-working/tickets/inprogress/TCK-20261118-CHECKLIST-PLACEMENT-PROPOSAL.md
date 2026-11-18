---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261118-CHECKLIST-PLACEMENT-PROPOSAL
phase: open
date: 2026-11-18
tags: [skills, process-improvement]
---

# TCK-20261118-CHECKLIST-PLACEMENT-PROPOSAL

## Title
Proposal: where the lifecycle and clock checklist should sit so it fires on hand-closed tickets (proposal only)

## Status
INPROGRESS

## Tier
standard

## Type
chore

## Priority
P3

## Request Summary
Owner decision on #715 (via lead-planner, 2026-11-18): "Rethink placement first". The invocation-coverage measurement (1 of 374 closed tickets had an architecture-reviewer pass) means a checklist inside `architecture-reviewer` rarely fires. Propose better placements with trade-offs and how each is measured. The eval on TCK-20261118-ARCH-REVIEWER-LIFECYCLE-TIME-CHECKLIST-EVAL is on hold.

## Scope
Proposal only: candidate placements, binding vs advisory, context cost, false-positive risk, measurement per option, reuse of the committed pre-registration.

## Out of Scope
Editing any agent, skill, template, tool or workflow; running any eval.

## Acceptance Criteria
A proposal the owner can choose from, with measured coverage numbers and the limits of each measurement stated.

## Related Tickets
- TCK-20261118-SIM-ENGINEERING-SKILLS-RESEARCH-PROPOSAL
- TCK-20261118-ARCH-REVIEWER-LIFECYCLE-TIME-CHECKLIST-EVAL (on hold)

## Related Docs
- agent-working/stored_artifacts/TCK-20261118-SIM-ENGINEERING-SKILLS-RESEARCH-PROPOSAL/

## Related Stored Artifacts
- agent-working/staging_artifacts/TCK-20261118-CHECKLIST-PLACEMENT-PROPOSAL/proposal.md

## Related Code Areas
- .github/pull_request_template.md, tools/delivery/pr_render.py, tools/ticket_field_values.py, tools/gate_checks/done_checker_static.py, tools/agent-monitoring/record_hand_orchestrated_closure.py

## Assumptions / Open Questions
See proposal.md.

## Implementation Notes
n/a

## Test Summary
n/a (no code).

## Files Changed
(filled at close)

## Completion Summary
(filled at close)
