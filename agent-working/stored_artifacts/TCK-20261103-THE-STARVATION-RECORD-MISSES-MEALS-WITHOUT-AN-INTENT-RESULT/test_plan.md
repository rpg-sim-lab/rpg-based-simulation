---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20261103-THE-STARVATION-RECORD-MISSES-MEALS-WITHOUT-AN-INTENT-RESULT
artifact_type: test_plan
---

# Test plan

- meal with no intent result (free meal) updates last_meal_tick and clears the trail.
- meal below the escalated line updates last_meal_tick.
- attempt below the line still does not count.
- CORPSE_FOOD rejected result is a SCAVENGE attempt; an accepted corpse meal is a meal.
- Each new test fails on the old recorder (checked).
- Regression: test_starvation_death_record.py, test_starvation_verdict.py, rpg_gate/test_v8_fires.py.
- No real-kernel case: the existing kernel test covers the channel; a corpse-meal kernel stage is not cheap.
- Pinned run: end hash base vs fix equal (needs the heavy slot).
