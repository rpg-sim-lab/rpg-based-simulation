---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20261117-SPLIT-EVENT-SHAPERS-BELOW-ITS-LINE-CEILINGS
phase: open
date: 2026-11-17
tags: []
---

# TCK-20261117-SPLIT-EVENT-SHAPERS-BELOW-ITS-LINE-CEILINGS

## Title
Split the per-domain shapers out of event_shapers.py so it comes back under its line ceilings

## Status
OPEN

## Tier
standard

## Type
refactor

## Priority
P3

## Request Summary
Filed by rpg-planner on 2026-11-17. Step 3 of TCK-20261109-M1-KIND-ALWAYS-MEANS-SPECIES-AND-OCCUPATION-IS-ITS-OWN-FIELD moved the label readers from `kind` to `occupation`. In `src/observability/event_shapers.py` that added an `occupation_of` import and one `occupation = occupation_of(new_ent)` read, which pushed two line_count rows of `codebase/baselines/code_health_exceptions.jsonl` over:
- module-length 2011 → 2013;
- `WorldDynamicsShaper.shape` function-length 181 → 182.

The owner chose to raise both to the new values exactly, each citing this ticket as `retiring_ticket` (#715 6934602208, under the raise rule 6785100551). It is the second raise for the kind=species item; the first nine are owned by TCK-20261117-PAY-DOWN-THE-NINE-LINE-CEILINGS-THE-OCCUPATION-FIELD-RAISED. The file is a 2,000-line hotspot with no paydown ticket until now.

## Scope
1. Move each per-domain shaper class (world dynamics, progression, social and the rest) out of `event_shapers.py` into its own module under `src/observability/`, re-exported from `event_shapers.py` so importers don't change.
2. Break `WorldDynamicsShaper.shape` into per-event-type helpers.
3. `python3 -m codebase.health move` the moved rows, then `tighten`, so both raised rows are at or below their pre-raise ceilings and no longer cite this ticket.
4. Behaviour-neutral: the pinned event-extractor characterization tests pass unchanged, plus an IDENTICAL proof on the 3 gate worlds at s42 (an owner run ask).

## Out of Scope
- Any change to what an event shaper emits.
- Other code-health rows.

## Acceptance Criteria
- `event_shapers.py` module-length ≤ 2011 and `WorldDynamicsShaper.shape` ≤ 181 (or their successors after a move), with neither row citing this ticket.
- The characterization tests are unchanged and pass; IDENTICAL proof on the 3 gate worlds at s42.

## Related Tickets
- TCK-20261109-M1-KIND-ALWAYS-MEANS-SPECIES-AND-OCCUPATION-IS-ITS-OWN-FIELD (raised them)
- TCK-20261117-PAY-DOWN-THE-NINE-LINE-CEILINGS-THE-OCCUPATION-FIELD-RAISED (the first raise)

## Related Docs
- docs/guidelines/agent_working_environment.md ("Reading code-health results on a PR"); docs/guidelines/python_code_standard.md §4

## Related Stored Artifacts
None.

## Related Code Areas
- src/observability/event_shapers.py; tests/unit/observability/

## Assumptions / Open Questions
- Dispatch is a later owner ask, after Milestone 1's RPG queue allows (RPG first, #715 6911759453).

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
