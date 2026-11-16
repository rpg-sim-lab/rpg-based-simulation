---
status: active
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20261115-AN-EXPLICIT-RUN-ID-DELETES-AN-EXISTING-RUN-DIRECTORY
phase: open
date: 2026-11-15
tags: []
---

# TCK-20261115-AN-EXPLICIT-RUN-ID-DELETES-AN-EXISTING-RUN-DIRECTORY

## Title
A kernel given an explicit run id deletes an existing run directory of that name (rmtree, then create), so two runs that share an id destroy each other's data

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P3

## Request Summary
Raised by platform-implementer in the world-farm review (2026-11-15), and checked by rpg-planner-ubuntu on origin/main.
- `src/engine/run_identity.py:33-35`: for a non-default id, `create_run_directory` calls `repo.create_run(run_id, manifest, overwrite=True)`.
- `src/observability/reporting/artifact_repository.py:72-79`: on an existing dir, `create_run` runs `shutil.rmtree(run_dir)` and then `os.makedirs(..., exist_ok=True)`.
- The only caller is kernel.py:188. Explicit-id kernels are built by the lab, sweep and mining builders (now guarded by the world farm's claim_run_dir), src/observability/readiness/harness.py:105, tools/calibrate_simq.py:309 (a unique id), tools/test_architecture/rpg_gate_run.py, and tools/rpg_measure/arm_child.py (rpgm_<world>_<seed>_<pid>).
Effects:
- A caller without the farm's claim deletes another run's data whenever ids repeat.
- With the claim, there is still a short window between the rmtree and the makedirs in which a second same-id claimer can create the dir and then lose it.

## Scope
1. List every explicit-id caller, and check whether each one relies on replacing its own previous dir. Tests re-running a fixed id are likely.
2. Decide and implement one rule. Options:
   (a) an explicit id refuses an existing dir unless the caller passes an explicit replace flag;
   (b) replace by an atomic rename of a fresh temp dir;
   (c) keep the current behaviour and document it, with the window named.
   Ask rpg-planner (u24) before changing engine run-identity semantics.
3. Tests: two same-id kernel inits, with the second refused or isolated by the chosen rule, plus no change for default ids.

## Out of Scope
The world farm's own refuse and claim helpers (src/observability/world_farm_io.py). Default-id behaviour, which already never touches an existing dir.

## Acceptance Criteria
1. Every explicit-id caller is listed with how it is affected.
2. The chosen rule is implemented and tested, and no simulation hash changes (the run id is a name only; test T7 in the world farm shows this).
3. Docs updated: docs/engine/ run-identity contract if present, and docs/simulation/lab_contract.md if the lab-facing behaviour changes.

## Related Tickets
TCK-20261115-WORLD-FARM-RUNS-WORLDS-SIDE-BY-SIDE-WITHOUT-CLASHING (names this as an open item).

## Related Docs
docs/simulation/lab_contract.md

## Related Stored Artifacts
None.

## Related Code Areas
src/engine/run_identity.py, src/observability/reporting/artifact_repository.py, src/engine/kernel.py:188

## Assumptions / Open Questions
Q1: which rule, (a), (b) or (c)? That's an rpg-planner (u24) call on engine semantics.

## Implementation Notes
Unscheduled; dispatch needs a go. Lands after the world farm merges.

## Test Summary
(not started)

## Files Changed
(not started)

## Completion Summary
(not started)
