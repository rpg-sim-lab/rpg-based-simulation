---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261020-SUSPENDED-PROJECTS-ARE-NEVER-RESUMED-SLOT-LEAK
phase: done
artifact_type: test_plan
date: 2026-11-17
tags: []
---

# Test plan: TCK-20261020-SUSPENDED-PROJECTS-ARE-NEVER-RESUMED-SLOT-LEAK (N10)

Unit: `tests/unit/strategic/test_suspension_expiry.py` (age 199 / 200, every kind, first-sight stamp, typed end once, canonical dict, the three writers, resume clear, the expiring current project, the freed slots on the strategic pass, dead/inactive), `tests/unit/strategic/test_every_strategic_intent_caller_runs_the_suspension_expiry.py` (static caller test), `tests/unit/engine/test_checkpoint_fields.py` (the `suspended_since` fill). Existing tests edited for the new field only (rpg-planner / rpg-designer approved each): six SUSPENDED fixtures gain `suspended_since=500` (and one hash-neutrality test builds its project with None), the ProjectEnd set gains SUSPENSION_EXPIRED, the near-death assertion expects "" (R2), the checkpoint `_old_shape` helper drops both trailing fields, the arbiter golden sha.

## Proof Plan
- level: unit plus a 3-world 5000-tick spied run with a plain twin
- proof kind: HARD bars L1-L4 = 0 and SUSPENSION_EXPIRED >= 1 (not vacuous); twin hash equal; PINNED; logging_errors 0; exceptions {}
- oracle source: the designer's ruling file (own-job counts) and the spy /mnt/data2/rpg-measure/n10/suspension_spy_6376230d_approved.py
- expected effect: SUSPENDED records end at TTL; at-cap subjects with SUSPENDED records fall after t ~ 770 in the urban corpus runs
- selected commands: tests/unit/strategic, test_checkpoint_fields.py, test_checkpoint_schema.py, test_mechanism_registry_completeness_check.py, tests/architecture; the 26 slow scenario tests; run_cells.sh (f8e01145) with the spy; the two urban corpus tests
