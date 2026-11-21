---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261121-RPG-GATE-METRICS-REJECT-A-NON-EATING-KIND-GROUP-AS-UNDECLARED
artifact_type: test_plan
tags: []
---

# Test plan

Written at close (2026-11-21) from the executed evidence of this branch; the ticket was filed 'filing only', so no pre-implementation staging artifacts existed.

- tests/unit/observability/test_rpg_gate_metrics.py: a declared `none` is counted with no food row; eaters keep theirs; no declaration raises; another undeclared group still raises; malformed declarations raise ValueError; a missing food row is no-data; empty declaration is byte-identical; pooled O2.t0_population is the MAX over seeds (1 member in 2 of 5 seeds applies R2).
- tests/unit/tools/test_rpg_gate_non_eating.py: shipped config loads; six malformed shapes raise BaselineError; child arguments; run child passes the declaration and writes the doc key; report prints not-applicable and first-seen-after-t0; R2 scope (t0 group vs none, fail closed, six malformed whens, shipped R2); C3 `none` 0 vs reference 0 is a pass.
- tests/unit/tools/test_rpg_gate_non_eating_pins.py (testing, cherry-picked): R2 scope per (world, group) and the candidate's handling of the declared group.
- Executed at d6483a7f0: by-directory tests/unit/** (only the 5 known grade-stability rows fail, equal to main's recorded values), tests/architecture 245, tests/simulation_quality/rpg_gate 8; at e4854e43e: tests/unit/tools 1423, rpg_gate 8, architecture 245; statics on the pinned venv clean.
- Not run: a main gate run (step 2 of the re-record ticket).
