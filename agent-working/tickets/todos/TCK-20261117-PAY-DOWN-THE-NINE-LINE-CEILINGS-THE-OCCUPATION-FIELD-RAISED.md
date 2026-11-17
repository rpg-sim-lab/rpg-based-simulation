---
status: active
layer: core
authority: P1
audience: agent
ticket_id: TCK-20261117-PAY-DOWN-THE-NINE-LINE-CEILINGS-THE-OCCUPATION-FIELD-RAISED
phase: open
date: 2026-11-17
tags: []
---

# TCK-20261117-PAY-DOWN-THE-NINE-LINE-CEILINGS-THE-OCCUPATION-FIELD-RAISED

## Title
Pay down the nine code-health line ceilings that the occupation field raised by 1-2 lines each

## Status
OPEN

## Tier
standard

## Type
refactor

## Priority
P3

## Request Summary
Filed by rpg-planner on 2026-11-17. Step 2 of TCK-20261109-M1-KIND-ALWAYS-MEANS-SPECIES-AND-OCCUPATION-IS-ITS-OWN-FIELD added `IdentityComponent.occupation` and its plumbing (a carry, copy or write argument at each site). That pushed nine line_count rows of `codebase/baselines/code_health_exceptions.jsonl` over their ceilings by 1-2 lines. The owner chose to raise the nine to their new values exactly, each citing this ticket as `retiring_ticket` (#715 6933841383, under the raise rule #715 6785100551). This ticket pays them back down.

The nine (ceiling before → raised to):
- src/api/presenters/state_presenter.py `StatePresenter.present_entity` 89 → 90
- src/core/builder.py `V2EntityBuilder` 839 → 841
- src/core/state.py `EntityState.to_readonly` 85 → 86
- src/domains/campaigns/orchestrator.py module 1124 → 1126, `CampaignOrchestrator` 1002 → 1004, `CampaignOrchestrator._build_initial_state` 419 → 420, `CampaignOrchestrator._extract_entity_carry_forwards` 86 → 87
- src/entities/archetype_factory.py `ArchetypeEntityFactory.build_entity` 94 → 95
- src/testing/scenario_runner.py `ScenarioRunner.execute` 153 → 154

## Scope
1. Move the hand-written identity-field copies (the campaign carry-forward extract and rebuild, `EntityState.to_readonly`, and the builder's identity assembly) onto one shared helper, so a new identity field is added in one place. That also removes the class of bug the step-2 CI found at apply.py:704, where a hand copy dropped a new slot.
2. Shrink the other rows by a real extraction (no line squeezing), then `python3 -m codebase.health tighten` to lower each row and clear its `retiring_ticket`.
3. Behaviour-neutral: whole-doc IDENTICAL on the 3 gate worlds at s42 (an owner run ask), plus the scoped unit tests.

## Out of Scope
- Any meaning change to kind, occupation or role (those are the kind=species steps).
- Other code-health rows.

## Acceptance Criteria
- Each of the nine rows is back at or below its pre-raise ceiling, or lowered by tighten with the reason stated, and none cites this ticket any more.
- The identity copies go through one helper, with a test that a new identity field survives the carry, the read-only view and the apply-path copy.
- IDENTICAL proof on the 3 gate worlds at s42.

## Related Tickets
- TCK-20261109-M1-KIND-ALWAYS-MEANS-SPECIES-AND-OCCUPATION-IS-ITS-OWN-FIELD (raised them)

## Related Docs
- docs/guidelines/agent_working_environment.md ("Reading code-health results on a PR"); docs/guidelines/python_code_standard.md §4

## Related Stored Artifacts
None.

## Related Code Areas
- The nine files above; src/engine/apply.py (`_fast_replace_identity`)

## Assumptions / Open Questions
- Dispatch is a later owner ask, after Milestone 1's RPG queue allows (RPG first, #715 6911759453).

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
