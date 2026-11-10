---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20261103-THE-STARVATION-RECORD-MISSES-MEALS-WITHOUT-AN-INTENT-RESULT
artifact_type: investigation
---

# Investigation — meal writers

Every code path that lowers hunger (grep of hunger_delta / hunger_set / biological_upd under src): 
1. `carried_meal` (core_actions.py:54), source_kind CARRIED_FOOD, stamps last_meal_tick_set.
2. `eat_update` free meal (core_actions.py:67), hunger_delta -40, a direct update with NO transfer and so no intent result, stamps last_meal_tick_set.
3. `corpse_meal` (core_actions.py:89), source_kind CORPSE_FOOD, stamps last_meal_tick_set.
4. `building_services.service_delta` EAT (building_services.py:80), hunger_delta -INN_MEAL_HUNGER, source_kind TOWN_SERVICE on a separate gold charge; it does NOT set last_meal_tick_set.
`hunger_set` has no writer. apply.py only raises hunger. Nothing but a meal lowers hunger today, so a hunger drop is a meal; the docstring lists the four so a fifth writer is a visible change.
Finding outside scope: the authoritative `biological.last_meal_tick` is not stamped by the inn meal (writer 4). Nothing reads the field. Reported, not changed.
The old rule: `_note_attempts` returned early below the escalated line and set the last meal only for an accepted CARRIED_FOOD or INN_MEAL result, so writers 2 and 3 and every sub-line meal were invisible.
