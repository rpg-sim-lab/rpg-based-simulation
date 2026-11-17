---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261107-PINNED-RUNNER-RULE-EXECUTOR-CLAUSE-AFTER-837
phase: done
date: 2026-11-07
tags: [delivery, documentation]
---

# TCK-20261107-PINNED-RUNNER-RULE-EXECUTOR-CLAUSE-AFTER-837

## Title
The pinned-runner rule's executor clause is replaced now that #837 has merged

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P2

## Request Summary
`docs/guides/delivery_process.md` "Behaviour evidence comes from the pinned runner" (added by
TCK-20261103-DELIVERY-GUIDE-PINNED-RUNNER-EVIDENCE-RULE, #834) said the pinned runner was the measuring ruler
"until TCK-20261103-THE-CONCURRENT-AND-SEQUENTIAL-EXECUTORS-GIVE-DIFFERENT-WORLDS closes". That ticket closed in
#837 (531010a9a). rpg-designer, the rule's author, gave the replacement text (2026-11-07, revised the same day to
drop a worker-failure-count sentence that had nothing to check). The owner approved it (#715 6700862118). Under the
owner's PR-size rule (#715 6697748243) this rides in the next implementation PR, not a PR of its own.

## Scope
- Replace the executor clause with rpg-designer's text, filling the two test paths from #837 as merged.
- Add "The executor clause was updated on #837's merge" to the Ruled-by note.

## Out of Scope
- Any other sentence of the rule, including the STATE-DIGEST clause.
- The enforcement work in TCK-20261103-A-MEASUREMENT-NOT-ON-THE-PINNED-RUNNER-CALLS-ITSELF-EVIDENCE.

## Acceptance Criteria
- The new clause matches rpg-designer's final text, with real paths for both placeholders.
- Both cited tests exist on main; the field-parity test passes.
- The rest of the paragraph is unchanged.

## Related Tickets
- TCK-20261103-DELIVERY-GUIDE-PINNED-RUNNER-EVIDENCE-RULE
- TCK-20261103-THE-CONCURRENT-AND-SEQUENTIAL-EXECUTORS-GIVE-DIFFERENT-WORLDS
- TCK-20261103-A-MEASUREMENT-NOT-ON-THE-PINNED-RUNNER-CALLS-ITSELF-EVIDENCE

## Related Docs
- docs/guides/delivery_process.md

## Related Stored Artifacts
- none

## Related Code Areas
- tests/unit/kernel/test_executor_context_parity.py, tests/integration/kernel/test_executor_equivalence_long.py

## Assumptions / Open Questions
- Field-parity tests cited: `test_every_packet_field_equals_the_states_value_at_each_stage` (every PR) and its
  gate-world twin `test_every_packet_field_equals_the_states_value_on_a_gate_world` (slow lane), both at rpg-designer's
  request (2026-11-07): the twin is the one that checks a real world.

## Implementation Notes
Draft kept at the main checkout's `.claude/handover/drafts/pinned-runner-executor-clause-2026-11-07.md`.

## Test Summary
Both cited tests exist on main 531010a9a+. `pytest tests/unit/kernel/test_executor_context_parity.py::test_every_packet_field_equals_the_states_value_at_each_stage`: 4 passed. `pytest tests/docs`: 92 passed, 1 skipped, 1 xfailed. `validate_frontmatter.py` OK on the guide.

## Files Changed
- docs/guides/delivery_process.md (executor clause, Ruled-by note)
- this ticket

## Completion Summary
The pinned-runner rule now states the executors agree since #837, names the field-parity test that holds it and the long equivalence test's Failure-to-No-Op check, and keeps pre-#837 claims labelled as sequential-reference. Committed locally; rides the next implementation PR (#715 6697748243).
