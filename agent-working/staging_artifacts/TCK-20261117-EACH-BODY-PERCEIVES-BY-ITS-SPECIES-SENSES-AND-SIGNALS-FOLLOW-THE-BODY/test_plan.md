---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20261117-EACH-BODY-PERCEIVES-BY-ITS-SPECIES-SENSES-AND-SIGNALS-FOLLOW-THE-BODY
artifact_type: test_plan
---

# Test plan — TCK-20261117-EACH-BODY-PERCEIVES-BY-ITS-SPECIES-SENSES-AND-SIGNALS-FOLLOW-THE-BODY

- tests/unit/world/test_perc02a_senses_signals_night.py: P2 (every content species derives its own profile; unprofiled = 0), the ruled night_vision set, typed error, signals by size/activity/life, night grid, P3 grid, gate error logged at ERROR, no `.kind` in perception modules.
- Updated setup (assertions kept): test_sense_perception_gate.py, test_archetype_entity_factory.py (properties assertion flips to "not stored": designer derive-at-read ruling, planner-approved), test_pressure_perception_consumers.py.
- Existing suites touched: perception, appraisal, hostility, tactical, scheduler, content catalog/validator, worldbuilding compile.
- CI + rpg-gate-report hard validity rows on the pushed head; the extinction line is read at the run-2 domain boundary. Heavy runs only after HOST FREE.

## Proof Plan
| criterion | level | proof kind | oracle source | expected effect | selected commands |
|---|---|---|---|---|---|
| AC1: derived profile == species' profile, unprofiled 0 | unit | every content species through the gate | rpg-designer ruling | profile_source equals species.sense_profile; unprofiled_counts empty | `pytest -n 1 tests/unit/world/test_perc02a_senses_signals_night.py` |
| AC2: no grant below threshold | unit | hand-built grid | kernel spec P3 | perceived implies confidence >= 0.2 | same |
| AC3: night -2 | unit | grid, day vs night-sighted | owner Q2(a) | day-eyed kinds lose a medium-visibility target at night; night-sighted keep it | same |
| AC4: gate error is not perception | unit | monkeypatched gate | kernel spec point 4 | perceives False and an ERROR record | same |
| AC5: no kind reads | static | source scan | binding rule | no `.kind` in gate.py or signals.py | same |
