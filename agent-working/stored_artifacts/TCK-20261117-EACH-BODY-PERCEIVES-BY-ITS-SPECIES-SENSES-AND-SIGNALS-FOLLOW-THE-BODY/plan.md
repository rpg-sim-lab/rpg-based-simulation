---
status: historical
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20261117-EACH-BODY-PERCEIVES-BY-ITS-SPECIES-SENSES-AND-SIGNALS-FOLLOW-THE-BODY
artifact_type: plan
---

# Plan — TCK-20261117-EACH-BODY-PERCEIVES-BY-ITS-SPECIES-SENSES-AND-SIGNALS-FOLLOW-THE-BODY

## Plan Status
Approved by rpg-designer (relayed by rpg-planner 2026-11-17). Stacked on rpg-night-time-of-day (needs is_night); rebases onto main once the night PR merges.

## Steps
1. Schema: SenseProfileDefinition.night_vision; BodyModelDefinition.signals (validated). Content: night_vision on goblin_alert, predator_smell, spider_vibration, undead_dread; new troll_senses (troll repointed); spirit_body life none.
2. Gate: profile derived from species_of at one read site; SenseProfileError; unprofiled counter; night step (vision -2 rungs unless night_vision); night flag in the context.
3. src/world/perception/signals.py emitted_signals; get_entity_signals delegates.
4. Gate error is not perception (appraisal.perceives, tactical._target_still_perceived: False + ERROR log).
5. night keyword threaded through perceives/appraise/faction_hostile/relation/perceived_hostile/classify_neighbours; passed from the tactical pass, scheduler adjacency wake, opening_steps._hunt_step.
6. Typed content error on the compile, spawn and archetype paths; archetype_factory stops writing sense_profile_id.
7. Tests, docs (Bible 04, divergence 2.210, STRAT-352).

## Scope guards
No kind reads (static test). No new durable state. Out of scope: perceived_neighbours migration and observable intent (02b).
