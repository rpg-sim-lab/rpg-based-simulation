---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261121-RPG-GATE-METRICS-REJECT-A-NON-EATING-KIND-GROUP-AS-UNDECLARED
phase: open
date: 2026-11-21
tags: []
---

# TCK-20261121-RPG-GATE-METRICS-REJECT-A-NON-EATING-KIND-GROUP-AS-UNDECLARED

## Title
The rpg gate marks crowded_frontier s42 and s44 `no-data` with `GateDataMissingError: kind group ['none'] seen in the run but not declared` once births add the first non-eating living kind

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Finding from rpg-planner-ubuntu's births gate read (head d3401ba43, local harness, sealed), relayed by lead-planner. Reported, not reproduced here: on crowded_frontier seeds 42 and 44 the metric run gives `[metric_error] GateDataMissingError: kind group ['none'] seen in the run but not declared (declared: ['meat+plant+prepared'])`. The likely cause is births' risen undead, the first non-eating living kind in a gate world (likely, not confirmed).

Where it is raised (read on origin/main c540a0b17): `_require_declared` in `src/observability/rpg_gate_metrics.py` (line 258), not in `tools/test_architecture/rpg_gate_baseline.py` as first relayed. The declared set comes from `declared_groups(world, seeds)`: the groups of the world compiled before any tick, plus the groups of its declared spawn-source kinds (`_spawn_kinds`: camp kinds and `world_boss`). A kind that only appears through births is in neither, so its group (`none`, a kind with no diet) is stray and the run goes no-data. By design, per the module's own docstring: "something seen in the run outside its declared domain is a missing declaration: the run is no-data, never a silently new row."

`python3 -m tools.sessions.route src/observability/rpg_gate_metrics.py` returns rpg-planner (src/**). The harness and the baseline tooling are testing's; the metric module and `tests/simulation_quality/rpg_gate/config.yaml` are rpg's.

## Scope
ORDER (lead-planner, relaying lead-planner-u24): (1) rpg-designer rules first on whether non-eaters form their own kind group or are excluded from the food pools; (2) then testing-planner with rpg-planner decide the metric-module half and how harness-hash comparability is kept; (3) nothing is built before the designer's ruling; (4) never by loosening `GateDataMissingError`. The diff's review stays with lead-planner-u24 (#715 6519647030), so the testing PR diff goes to it. Correction to the relays: the metric-module half is `src/observability/rpg_gate_metrics.py`, not `rpg_gate_baseline.py`.

Decide the fix with rpg-planner (u24); the error is never suppressed or downgraded, and "none" is not silently dropped from the rows. Candidates:
- (A) Declare it: `_spawn_kinds` (or the config) names the kinds a birth or rising can add, so `declared_groups` includes `none` and every seed emits the same rows.
- (B) Make the metrics handle a non-eating group explicitly: a group with no diet is a declared, named case in the food-source and meat-eater rows, with its own stated rule, not a missing declaration.
- (C) Both, if (A) alone leaves rows undefined for a non-eating group (an empty-denominator share must be undefined, not imputed; see TCK-20261020-RPG-GATE-RUN-ROW-SET-IS-DECLARED-NOT-OBSERVED).

Baseline comparability (required in the PR body, not optional): `harness_hash` covers the harness sources, the pin settings, the config bytes and the metrics module's name and source (`rpg_gate_harness.py` docstring). Editing `src/observability/rpg_gate_metrics.py` or the config therefore moves the hash. Per the staleness rules in `docs/plans/test_architecture/reference/rpg_gate_baseline_format.md`, a baseline whose hash differs from the current harness is stale and never yields a pass, so every world's baseline goes stale together; and the rerun-skip's main report with another hash gives the full rerun (`rpg_gate_main_report` / `rpg_gate_report.py`). The change must say which of these holds and how comparability is kept: a re-baseline citing this ticket (the owner's call; `rebaseline` under a ruling; not done by testing), or a change that leaves the hash alone (not possible for the two files above as the hash is defined today). Do not hand-edit baselines, `rpg_gate_known.yaml` or the config's hashed bytes to make a run green. Also decide with the owner whether the re-baseline lands inside an M1 segment (SimQ drift is deferred in M1; this is a gate-harness change, not balance tuning, but the baseline moves with it).

Evidence to collect before choosing: the failing documents (`/data/vboxuser/gate-reports/` is read-only, and the sealed births read lives with rpg-planner-ubuntu), which entity carries group `none` (a risen undead is the suspicion), and whether the same group appears on other worlds or seeds that did not error (a seed set that never births would not show it).

## Out of Scope
- Suppressing, catching or downgrading `GateDataMissingError`, or dropping the stray group from the rows.
- Editing a baseline, `rpg_gate_known.yaml`, or the config to make a run green.
- Any `src/` simulation behaviour (the births work itself).
- Running the gate or any heavy run (heavy slot is held; any run needs lead-planner's GO).

## Acceptance Criteria
1. The cause is stated with evidence: which entity and kind produce group `none`, on which (world, seed), at what tick.
2. A chosen fix, agreed with rpg-planner (u24), with the non-eating group handled by a stated rule in every row it touches (no row left undefined or imputed).
3. A test pins: a run containing a non-eating kind group is not no-data and emits the same row set on every seed of its world; an undeclared group of any other kind still raises.
4. The PR states the new harness hash effect and how baseline comparability is kept (re-baseline ticket and owner approval, or the stale baseline treatment), and the rerun-skip fallback is checked on the first run after.
5. `rpg_gate_known.yaml`, the baselines and the config are not edited to turn a run green.

## Related Tickets
- TCK-20261020-RPG-GATE-RUN-ROW-SET-IS-DECLARED-NOT-OBSERVED (the "declared, not observed" rule this error enforces)
- TCK-20261109-M1-BASIC-WILD-BIRTHS-FOR-EVERY-LIVING-KIND (the births that add the kind)
- TCK-20261119-RPG-GATE-RERUN-ONLY-NEW-ROWS-AND-A-BASELINE-DIFF-AGAINST-MAIN (the rerun-skip a hash move interacts with)

## Related Docs
- `docs/plans/test_architecture/reference/rpg_gate_baseline_format.md` (staleness, "The run row set is declared, not observed")

## Related Stored Artifacts
- rpg-planner-ubuntu's sealed births gate read at d3401ba43 (host-local; not read here).

## Related Code Areas
- `src/observability/rpg_gate_metrics.py` (`_require_declared`, `declared_groups`, `_spawn_kinds`, `declared_wild_meat_eaters`)
- `tests/simulation_quality/rpg_gate/config.yaml` (rpg's; hashed)
- `tools/test_architecture/rpg_gate_harness.py` (`harness_hash`)

## Assumptions / Open Questions
- The cause (births' risen undead) is a suspicion from the reporter, not confirmed.
- Whether non-eaters form their own group or leave the food pools: rpg-designer rules first. Whether (A), (B) or (C): open until that ruling, then with rpg-planner (u24).
- Whether a re-baseline lands inside the M1 segment: open, the owner's call.
- Routing: the metric module is rpg-planner's; this ticket is filed on the testing track because the harness hash and baseline comparability are testing's. rpg-planner or its implementer builds the change.

## Durable state, lifecycle and clocks
None: a gate-harness read model. The baseline files are the durable artefact; this ticket changes none.

## Implementation Notes
Filing only.

## Test Summary
Not applicable.

## Files Changed
This ticket only.

## Completion Summary
Open.
