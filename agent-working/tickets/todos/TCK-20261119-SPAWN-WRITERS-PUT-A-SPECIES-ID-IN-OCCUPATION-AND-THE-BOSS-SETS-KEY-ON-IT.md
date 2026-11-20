---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20261119-SPAWN-WRITERS-PUT-A-SPECIES-ID-IN-OCCUPATION-AND-THE-BOSS-SETS-KEY-ON-IT
phase: open
date: 2026-11-19
tags: []
---

# TCK-20261119-SPAWN-WRITERS-PUT-A-SPECIES-ID-IN-OCCUPATION-AND-THE-BOSS-SETS-KEY-ON-IT

## Title
Spawn writers put a species id in `occupation`, and the observability boss and spawn-cadence sets key on that occupation literal

## Status
OPEN

## Tier
standard

## Type
refactor

## Priority
P3

## Request Summary
This is a follow-up from rpg-designer's H2 ruling on TCK-20261119-OCCUPATION-READS-COMPARED-WITH-A-NON-LIVING-SPECIES-ID-MISS-THE-WORLD-BOSS, relayed by lead-planner-u24 on 2026-11-19. Filed by rpg-planner, filing only.

Under kind=species (M1 step 4/5), `occupation` is the label or role and the species lives in `kind`. Several spawn writers still put a species id into `occupation`, and two observability sets key on those occupation literals (inspected, as cited by the designer):
- Writers:
  - src/world/calamity.py:83 "world_boss"
  - src/world/boss.py:265 "dragonkin"
  - src/certification/scenarios.py:74 "monster"
  - src/systems/world_systems/generator.py:325 "goblin" is LISTED, and left for later.
- Sets: src/core/entity_kind_constants.py:7 BOSS_ENTITY_OCCUPATIONS and :9 SPAWN_CADENCE_EXCLUDED_OCCUPATIONS.
- Readers: src/observability/event_shapers.py:1134 and :1207, the extraction at resources.py:88, and world.py:114.

## Scope
These constraints were ruled by rpg-designer BEFORE code:
1. RE-KEY FIRST, then fix the writers. The sets and readers stop keying on occupation literals before any writer changes, so no classification goes missing in between.
2. Boss-ness is a DECLARED property: a boss spawn source or a boss role in content. It is NOT species_of. A compiled dragonkin must not become a boss.
3. The sets move into data/, validated at load (the owner's settings-in-data rule).
4. Then the writers put a role or label in `occupation`, or none, and the species stays in `kind`. generator.py:325 is out of scope here (see Out of Scope).

## Out of Scope
- generator.py:325 "goblin" (listed; its own later step).
- Changing which bodies spawn, or boss behaviour.
- The H2 hotfix itself (its own ticket).

## Acceptance Criteria
- Hash-equal on the gate worlds, before and after (an S9 record if it needs a kernel run).
- A flag-ON unit test (ENABLE_WORLD_BOSS_SPAWN) classifies the calamity world boss, the boss-place dragonkin and a compiled dragon_cult_champion EXACTLY as before. The boss/event/cadence classification is unchanged.
- No observability set keys on an occupation literal. A source scan pins it.
- The sets are in data/, validated at load, and part of the run identity under the settings rule.
- The pre-push run covers tests/unit/** by directory plus statics. Any existing test-expectation change is an owner ask.

## Related Tickets
- TCK-20261119-OCCUPATION-READS-COMPARED-WITH-A-NON-LIVING-SPECIES-ID-MISS-THE-WORLD-BOSS (H2; the parent ruling)
- TCK-20261118-A-SECOND-WORLD-BOSS-SPAWNS-BECAUSE-THE-DEDUPE-READS-THE-OCCUPATION (#964, merged)
- TCK-20261109-M1-KIND-ALWAYS-MEANS-SPECIES-AND-OCCUPATION-IS-ITS-OWN-FIELD
- TCK-20261119-THE-CALENDAR-IS-DECLARED-IN-CONFIGURATION-NOT-IN-CODE (settings-in-data conditions)

## Related Docs
- docs/core/entities.md (kind and occupation), divergence 2.208 (the mirror is gone), docs/guides/feature_flags.md (ENABLE_WORLD_BOSS_SPAWN)

## Related Stored Artifacts
- None.

## Related Code Areas
- src/core/entity_kind_constants.py, src/observability/event_shapers.py, src/world/calamity.py, src/world/boss.py, src/certification/scenarios.py, resources.py (extraction), world.py

## Assumptions / Open Questions
- Where the declared boss property lives (a spawn-source tag on the body, or a content boss role) is for rpg-designer to rule at dispatch.

## Durable state, lifecycle and clocks
No new durable state is expected. If the boss property becomes a spawn-source tag on the body, it is set once at spawn and never changed, so it needs a typed field, checkpoint coverage and a fill rule for old saves. That is decided at dispatch. No clock is read.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
