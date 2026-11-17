---
status: historical
layer: core
authority: P2
audience: agent
ticket_id: TCK-20261117-THE-LABEL-READERS-READ-OCCUPATION-NOT-KIND
phase: done
artifact_type: test_plan
date: 2026-11-17
tags: []
---

# Test plan: TCK-20261117-THE-LABEL-READERS-READ-OCCUPATION-NOT-KIND

Own-job counts (rpg-designer, step-1 rulings and step-3 review):
- K4: 3 plain runs of paired.WORLDS, s42, 5000 ticks, base (step 2 head 1a676e15d) against the step-3 head; whole-doc IDENTICAL, start_hash and final_hash included: 0 differing fields.
- K5: static: no label compare is left on an entity's `kind` outside the ruled files (9 files, each with its reason).

Suites: the observability, world, social, systems, engine, core, domains and gameplay unit suites, the mechanism pin file, tests/integration, certification, arena (not slow), perf; then the CI-equivalent lane set at -n 1.

## Proof Plan
- level: unit plus a 3-world 5000-tick paired identity run
- proof kind: IDENTICAL (nothing moves, hashes included)
- oracle source: the step-2 head's own run
- expected effect: none
- selected commands: run_identical.sh (83aad33c) and compare_identical.py (3b32e5ba) in /mnt/data2/rpg-measure/m1step3; the suites above
