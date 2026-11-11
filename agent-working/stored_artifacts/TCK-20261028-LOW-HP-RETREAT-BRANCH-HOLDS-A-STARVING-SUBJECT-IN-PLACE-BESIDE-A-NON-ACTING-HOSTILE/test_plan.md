---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20261028-LOW-HP-RETREAT-BRANCH-HOLDS-A-STARVING-SUBJECT-IN-PLACE-BESIDE-A-NON-ACTING-HOSTILE
artifact_type: test_plan
---

# Test plan

- tests/unit/tactical/test_low_hp_retreat_gate.py (19 tests): grid rows with and without a destination, the acceptance scene, the prey row, a panic with a destination still flees, an acting hostile keeps the freeze, and a 16-tick kernel row (the idle-update variant fails it from tick 14).
- Guard-drop checks: dropping the need_yields guard, the destination guard or the prey guard each fail the matching row.
- Changed expectation: test_surv07_precedence_grid.py reading-3 below-line row (was the freeze, now EAT).
- Regression: tactical, combat, ai, engine, cognition, strategic and docs suites (1277 and 1892 passed in scoped runs).
- Measurement: 9 pinned cells (evidence/).
