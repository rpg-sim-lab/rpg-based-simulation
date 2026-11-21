---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261121-RPG-GATE-METRICS-REJECT-A-NON-EATING-KIND-GROUP-AS-UNDECLARED
artifact_type: plan
tags: []
---

# Plan

Written at close (2026-11-21) from the executed evidence of this branch; the ticket was filed 'filing only', so no pre-implementation staging artifacts existed.

1. config.yaml: `non_eating_kind_groups: {none: {food_metrics: not_applicable}}` and the R2 `when` scope.
2. rpg_gate_baseline.py: GateConfig.non_eating with a strict loader; StopLine.when_row/when_min with a strict `when` loader and a fail-closed scope in stop_lines_crossed.
3. rpg_gate_harness.py / rpg_gate_run.py: hand the declaration to compute and pool (`non_eating=`), only when declared; copy the `not_applicable` key into the seed document.
4. rpg_gate_metrics.py: compute/pool/declared_groups take `non_eating`; the declared group is counted for population, deaths and combat and carries no O1.starved / O1.at_risk / O4.accepted row; a missing food row for any other group raises; a malformed declaration is a ValueError; pooled O2.t0_population (MAX over seeds) with its own POOLED_THRESHOLDS entry.
5. rpg_gate_report.py: print the not-applicable groups and the groups first seen after t0 (peak, end) per world.
6. Tests: metric unit tests, a new tools test file, testing's AC3 pin (cherry-picked); statics on the pinned venv.
Out of scope: running the gate, the re-record (TCK-20261121-RPG-GATE-REBASELINE-AFTER-THE-NONE-KIND-GROUP-HASH-MOVE), any baseline or known-file edit.
