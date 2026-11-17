---
status: historical
layer: core
authority: P2
audience: agent
ticket_id: TCK-20261117-KIND-IS-THE-SPECIES-AT-EVERY-WRITER
phase: done
artifact_type: test_plan
date: 2026-11-17
tags: []
---

# Test plan: TCK-20261117-KIND-IS-THE-SPECIES-AT-EVERY-WRITER

- tests/unit/core/test_occupation_field.py (K6c, K6d, per-writer, t0 K6/K7/K9, the context-less legacy-compile pin); test_occupation_fixture_writers.py; test_occupation_label_readers.py (K5).
- tests/arena/test_arena_quests.py (the quest credit survives the goblin move); tests/architecture (name-switch ratchet at 120 rows).
- Targeted sets: core, unit dirs, integration, certification, perf; CI-equivalent lanes; code-health and mypy gates.
- Own-job run: run_step4.sh (6 processes) plus static mode; bars K6/K6b/K7/K8/K9 = 0, logging_errors 0, exceptions {}, twin match, PINNED.

## Proof Plan
- level: unit and integration tests, the architecture ratchet, the CI-equivalent lanes, and a 3-world 5000-tick own-job run (plain plus spied twin)
- proof kind: counts K6, K6b, K7, K8, K9 = 0 (behaviour step; not an identity run)
- oracle source: the designer's counts in 67cc6f6d, 665b9718 and 3045e98a; the spy's own PINNED and twin-hash checks
- expected effect: kind becomes the species id on every writer; occupation carries the label; a writer with no species is refused
- selected commands: run_step4.sh (e29b7023) with m1_step4_spy.py (dd2f9d70) and summarize_step4.py (530cac21) in /mnt/data2/rpg-measure/m1step4; run_targeted.sh; run_ci.sh with lanes_wrap.py
