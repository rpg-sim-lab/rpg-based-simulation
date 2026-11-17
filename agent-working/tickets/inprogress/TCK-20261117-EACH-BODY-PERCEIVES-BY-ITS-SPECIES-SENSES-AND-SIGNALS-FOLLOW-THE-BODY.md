---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20261117-EACH-BODY-PERCEIVES-BY-ITS-SPECIES-SENSES-AND-SIGNALS-FOLLOW-THE-BODY
phase: open
date: 2026-11-17
tags: []
---

# TCK-20261117-EACH-BODY-PERCEIVES-BY-ITS-SPECIES-SENSES-AND-SIGNALS-FOLLOW-THE-BODY

## Title
Each body perceives by its species' senses, and what it gives off follows the body (PERC-02a)

## Status
INPROGRESS

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
PERC-02a, the first half of TCK-20261109-M1-HONEST-PERCEPTION-DEFAULTS: senses derived from the species at read, signals that follow the body, night vision, and a gate error that is not perception.

## Scope
1. The gate resolves catalog.species[species_of(entity)].sense_profile at one read site; no stored field. A species in content with no profile is a typed SenseProfileError; a body whose species is not in content is unprofiled (baseline, counted, DEBUG).
2. emitted_signals(entity, body): visibility by size, noise/vibration by activity, scent and life for the living; body models may declare `signals`.
3. night_vision on the profile (goblin_alert, predator_smell, spider_vibration, undead_dread, new troll_senses); vision counts two levels lower at night otherwise.
4. A gate exception is not perception and logs at ERROR.
5. Divergence 2.210, ledger STRAT-352, Bible 04.

## Out of Scope
- Stealth and concealment; weather's perception multiplier (unread today; it stays unread).
- Balance tuning (Phase 3).

## Acceptance Criteria
- P2: bodies whose derived profile differs from their species' profile: 0; unprofiled bodies in the 3 gate worlds: 0.
- P3: no perception granted below the gate threshold (unit grid).
- Night -2 grid; gate exceptions in a run: 0, each with an ERROR record.
- Static test: perception modules read no `.kind`.

## Related Tickets
- TCK-20261109-M1-HONEST-PERCEPTION-DEFAULTS (parent; closes with 02b)
- TCK-20261117-DECISIONS-SEE-OTHER-BODIES-ONLY-THROUGH-PERCEPTION (02b)

## Related Docs
- docs/plans/systemic_world/m1_kernel_spec_items_2_6.md (Item 3)
- docs/world_rules/knowledge-agency/perception.md (PERC-02, on main with the planner's docs PR)

## Related Stored Artifacts
None.

## Related Code Areas
src/world/perception/, src/engine/appraisal.py, src/engine/hostility.py, src/engine/tactical*.py, data/content/living/

## Assumptions / Open Questions
None open; rulings by rpg-designer relayed by rpg-planner 2026-11-17 (split into 02a/02b; derive at read; unprofiled fixtures counted).

## Implementation Notes
Designer rulings 2026-11-17 via rpg-planner: derive at read (no stored field, no FIELD_RULES row); fixture policy (unprofiled counted, linked to TCK-20261117-TEST-FIXTURES-DECLARE-A-SPECIES-THROUGH-A-HELPER-AND-THE-BUILDER-DEFAULT-GOES). Known: legality.attack_allowed, is_feeding_kill, scorers_support.perceived_hostiles and the other get_neighbor_view sites stay day-by-default until 02b.

Body-model `signals` accepts an optional `magic` key (default none for every body; designer condition 2026-11-17). No production body in data/content declares it in this PR (grep-verified: none); only the test-only fixture in tests/unit/engine/test_pressure_perception_consumers.py does. To go in the PR body.

## Test Summary

## Files Changed

## Completion Summary
