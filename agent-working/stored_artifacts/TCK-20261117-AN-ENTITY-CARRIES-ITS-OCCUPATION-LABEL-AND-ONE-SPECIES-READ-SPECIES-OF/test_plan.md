---
status: historical
layer: core
authority: P2
audience: agent
ticket_id: TCK-20261117-AN-ENTITY-CARRIES-ITS-OCCUPATION-LABEL-AND-ONE-SPECIES-READ-SPECIES-OF
phase: done
artifact_type: test_plan
date: 2026-11-17
tags: []
---

# Test plan: TCK-20261117-AN-ENTITY-CARRIES-ITS-OCCUPATION-LABEL-AND-ONE-SPECIES-READ-SPECIES-OF

Own-job counts (rpg-designer, ruling 67cc6f6d and review 39dcca3d):
- K1: 3 plain runs of paired.WORLDS, s42, 5000 ticks, base against the step-2 head; whole-doc equal except the top-level start_hash and final_hash: 0 differing fields.
- K2: for every writer of `kind` in src, one test builds an entity and asserts `occupation == kind`; the t0 test over paired.WORLDS stays.
- K3: static: no production reader of `occupation` outside the carry, copy and presenter sites.

Suites: tests/unit/core (new field, fixture-writer and carry tests), tests/unit/domains/campaigns, tests/unit/api, tests/unit/entities, tests/unit/worldbuilding, tests/architecture, tests/unit/engine, the mechanism registry tests, certification, arena (not slow), perf, scenario runtime API; then the CI-equivalent lane set at -n 1.

## Proof Plan
- level: unit plus a 3-world 5000-tick paired projection
- proof kind: neutral by projection (fates and counters identical, only the state hash moves)
- oracle source: the parent commit's own run (base e72270894)
- expected effect: none on fates and counters; start_hash and final_hash differ by the added field
- selected commands: run_projection.sh (ce09ece3) and compare_projection.py (1bccef76) in /mnt/data2/rpg-measure/m1step2; the scoped suites above
