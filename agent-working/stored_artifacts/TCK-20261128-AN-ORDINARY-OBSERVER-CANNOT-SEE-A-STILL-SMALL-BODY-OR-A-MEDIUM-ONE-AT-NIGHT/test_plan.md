---
status: active
layer: world
authority: P2
audience: agent
ticket_id: TCK-20261128-AN-ORDINARY-OBSERVER-CANNOT-SEE-A-STILL-SMALL-BODY-OR-A-MEDIUM-ONE-AT-NIGHT
artifact_type: test_plan
tags: []
---

# Test plan

**Written at close (2026-11-28).**

- tests/unit/world/test_perception_calibration.py: AC table (day distances per size, night still medium and small, size order, not seen at 40), settings load and validation (missing record, threshold below the still-body ceiling, undeclared size), still-body ceiling value.
- tests/unit/world/test_perc02a_senses_signals_night.py and tests/unit/engine/test_perc02a_review_night_clock_and_lodging.py: the 02a rows re-pointed to the calibrated values (owner-approved reversal); NIGHT_DX = 8.0 for the night rows.
- tests/unit/tactical/test_surv07_hunt_project_grid.py: expectations changed by the calibration (in commit bbce8de04).
- tests/unit/engine/test_content_hotpath_guard.py: mocks carry the new record. Mechanism registry completeness pin 389.
- Scoped gap, not the full suite: tools chunks 0-7, touched unit domains, tests/architecture, registry, code health, import contracts, packages, mypy (all green on bbce8de04).
- Own-job run: the kit (evidence/perception-gate-calibration-kit @ 9622465db) on 3 gate worlds x s42 x 1000 t, base vs fix, H1 hash equality; a collapse to 0 is a STOP. Result: no STOP.
