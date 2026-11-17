---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261103-DELIVERY-GUIDE-PINNED-RUNNER-EVIDENCE-RULE
phase: done
date: 2026-11-03
tags: [delivery, documentation]
---

# TCK-20261103-DELIVERY-GUIDE-PINNED-RUNNER-EVIDENCE-RULE

## Title
The delivery guide states that behaviour evidence comes from the pinned runner

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P1

## Request Summary
rpg-planner sent rpg-designer's final rule text on 2026-11-03 (scope item 4 of
TCK-20261103-A-MEASUREMENT-NOT-ON-THE-PINNED-RUNNER-CALLS-ITSELF-EVIDENCE). The owner approved
agent-working-planner-u24 adding it as a short subsection of `docs/guides/delivery_process.md` through a
normal PR once the cited tickets are on main (#715 6593491826 item 3), and the older-claims sentence
covering `intentional_divergences.md` entries (#715 6593558681 item 2). The cited tickets landed in #833
(9eeb0fd97).

## Scope
- Add `### Behaviour evidence comes from the pinned runner` to `docs/guides/delivery_process.md`, with the
  rule text verbatim and one provenance paragraph (approvals, cause, the enforcing ticket).

## Out of Scope
- The runner marker, the refuse-or-label helper and the close-time flag: those stay in
  TCK-20261103-A-MEASUREMENT-NOT-ON-THE-PINNED-RUNNER-CALLS-ITSELF-EVIDENCE (rpg-planner's).
- Any change to the rule's wording.

## Acceptance Criteria
- The subsection's rule paragraph is byte-identical to the text recorded in the source ticket's
  Implementation Notes.
- The names it cites exist on main: `tools/rpg_measure/`, `tools/test_architecture/rpg_gate_run.py::build_kernel`,
  `src/engine/checkpoint.py::CanonicalStateHasher.get_hash`, and both cited tickets.
- Frontmatter and docs checks pass.

## Related Tickets
- TCK-20261103-A-MEASUREMENT-NOT-ON-THE-PINNED-RUNNER-CALLS-ITSELF-EVIDENCE
- TCK-20261103-STATE-DIGEST-MAY-OMIT-FIELDS-THAT-DECISIONS-READ
- TCK-20261103-THE-CONCURRENT-AND-SEQUENTIAL-EXECUTORS-GIVE-DIFFERENT-WORLDS

## Related Docs
- docs/guides/delivery_process.md

## Related Stored Artifacts
- none

## Related Code Areas
- tools/rpg_measure/, tools/test_architecture/rpg_gate_run.py, src/engine/checkpoint.py

## Assumptions / Open Questions
- `delivery_process.md` routes as unowned; the owner's yes (6593491826) is the authority for this edit.

## Implementation Notes
Placed after the gate override ledger subsection, before `## Branch Naming`: both concern what a verdict rests on.

## Test Summary
Rule paragraph checked byte-identical to the source ticket's recorded text (python substring check: True). Cited names exist on main (`CanonicalStateHasher` at src/engine/checkpoint.py:98, `build_kernel` at tools/test_architecture/rpg_gate_run.py:50, both cited tickets in todos/). `validate_frontmatter.py` OK on the guide and this ticket; `pytest tests/docs` passed.

## Files Changed
- docs/guides/delivery_process.md (new subsection)
- this ticket

## Completion Summary
The delivery guide now carries the pinned-runner evidence rule, verbatim, with its approvals and cause. Enforcement (runner marker, refuse-or-label helper, close-time flag) stays open in TCK-20261103-A-MEASUREMENT-NOT-ON-THE-PINNED-RUNNER-CALLS-ITSELF-EVIDENCE.
