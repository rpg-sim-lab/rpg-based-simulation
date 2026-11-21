---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261121-RPG-GATE-METRICS-REJECT-A-NON-EATING-KIND-GROUP-AS-UNDECLARED
artifact_type: investigation
tags: []
---

# Investigation

Written at close (2026-11-21) from the executed evidence of this branch; the ticket was filed 'filing only', so no pre-implementation staging artifacts existed.

- Cause (AC1, read from births GO 1, sealed, births head c1183bb24; head caveat vs the finding's d3401ba43): crowded_frontier s42 had a rising of corpse 1000009 (entity 9) into entity 39 at tick 630, s44 of corpse 1000025 (entity 25) into entity 39 at tick 390; both are kind `undead`, which has no diet, so kind group `none`. `_require_declared` (src/observability/rpg_gate_metrics.py) raised because `declared_groups` came only from the compiled world and its spawn sources.
- frontier_living_world already carries `none` on main (6 undead sentinels, ids 39-44, kind undead, profile undead_purpose): the FLW membership probe (S9, script 7bda6314, output sha 08784b9f, origin/main 1708ba481, s42, t0 and t500) found hunger rate 0.0 in every row, no `none` id first seen after t0, no interim or unprofiled counts: verdict (A), the food rows of `none` are wrong in kind (O1.at_risk counted 6 non-eating sentinels).
- The config had no group declarations and the metric module never read it; the harness passed only `--seeds`. The declaration is therefore data in config.yaml passed by the harness (rpg-designer ruling), with a strict loader on the harness side.
- R2 (O2.seeds_with_survivors >= 1, group "*") would cross on main the moment `none` has rows (members 0 everywhere): owner-approved scope (#715 7057159233): R2 applies only to groups with t0 population > 0, with a pooled O2.t0_population (MAX over seeds) guard, a fail-closed `when` scope and a strict `when` loader.
- harness_hash covers the metrics module, rpg_gate_harness.py, rpg_gate_run.py, kernel_pinning.py, PIN_SETTINGS and the config bytes; rpg_gate_baseline.py and rpg_gate_report.py are not hashed.
