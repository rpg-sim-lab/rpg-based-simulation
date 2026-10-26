---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20261023-CHECKPOINT-RESTORE-DRAWS-STATELESS-RANDOMS-FROM-SEED-ZERO
phase: plan
date: 2026-10-26
tags: []
---

# Plan: restore a checkpoint with the episode's real base seed (#593 F3)

## Verified facts (on origin/main)
- `ScenarioCheckpointer.restore` (src/engine/scenario_checkpoint.py:83-85) builds `DeterministicRNG(base_seed=0)` then `set_state(state.rng_checkpoint)`.
- `set_state` restores only the per-domain stateful streams (`_rng_map`). The stateless API (`get_float`, `get_int`, `choice`, `weighted_choice`, `sample`, src/platform/rng.py:96-132) seeds from `_composite_seed(self._base_seed, ...)`. A second effect of seed 0: a domain not yet in `_rng_map` at the checkpoint is lazily seeded in `_get_rng` from `_base_seed ^ (domain.value << 16)`, so stateful draws from a domain first used after the restore are wrong too.
- The episode seed is already inside the pickled `AuthoritativeState` (`state.seed`); `_build_kernel` (scenario_runtime.py:418-423) uses `DeterministicRNG(base_seed=initial_state.seed)` (seed 0 only when there is no initial state). So no checkpoint format change is needed: nothing is added to the header, the format stays as in docs/engine/scenario_runtime_contract.md.
- Why nothing caught it: the existing checkpoint tests build the service without `initial_state`, i.e. seed 0, where base_seed=0 is correct. paired/gate runs never restore.
- Callers: only `src/api/routes/scenarios.py` (restore endpoint) and tests.

## Change (src only: one line + comment)
`rng = DeterministicRNG(base_seed=state.seed)`; replace the comment at :83-84 with the actual rule: "the base seed must be the episode seed (state.seed), because set_state restores only the stateful per-domain streams; the stateless get_*/choice/sample draws and any domain first used after the restore are derived from base_seed".
No change to rng.py, kernel, hasher, or Lane A's files.

## Tests (tests/unit/engine/test_scenario_checkpointer.py, new cases)
1. Unit, fast: save a seeded state (seed e.g. 12345) to a checkpoint, restore, assert `svc._kernel._rng.seed == 12345` and that `get_int`/`get_float` for a fixed (domain, tick, entity, sub_id) equal those of a `DeterministicRNG(12345)`; plus a lazily-seeded stateful draw from a domain absent from the checkpoint equals a fresh seeded RNG's. This fails on main (seed 0).
2. Equivalence (marked slow if it ticks real worlds): build a service with `initial_state` of seed != 0 (same way tests/perf builds `state`), run N ticks, checkpoint, restore into a new service, run K more; compare the final canonical state hash and a sample of stateless draws with an unbroken N+K service. Pick small N,K (e.g. 5 + 5) on frontier_living_world. First confirm on main that it FAILS (red) before the fix, so the test proves the bug; record the red/green in the ticket.
3. Existing checkpoint tests (seed 0) stay green; run tests/unit/engine/test_scenario_checkpointer.py, tests/api/test_scenario_runtime_api.py, tests/integration/scenarios/test_scenario_runtime_service.py.

## Determinism / blast radius
Only the restore path changes. A fresh run, paired runs and the gate never call restore, so every existing hash is unchanged; I will still show it with a 1-world 1000-tick hash base vs new only if you want it (not needed to claim, restore is not on that path). Seed-0 episodes restore exactly as before.

## Docs / parity
- docs/engine/scenario_runtime_contract.md "Checkpoint Format": add one sentence that the restored RNG uses `state.seed` (the stateless draws are not in the checkpoint). Check whether a parity ledger entry for INFRA-215 needs `v2_evidence` touched (I will look; it is infrastructure.yaml).
- Add a bug-fix line in docs/guidelines/intentional_divergences.md only if the contract previously claimed restore equals unbroken (will check; otherwise none).

## Heavy work
None to plan with; test 2 is a ~10 tick run (seconds). No host measurement needed, so I can code it while Lane A's probe holds the host, but I will not start until you confirm the plan.

## Process
Tier standard (ticket says so): ticket to inprogress at implementation start (the file is currently carried in my H2 branch under todos/, and I will add it to this branch from there once H2 lands, to avoid a double add), investigation.md + test_plan.md + this plan to stored_artifacts at close. One PR, label for:lead-planner. Push needs your go and the user's yes in my terminal.

## Questions for the planner
1. Is a real (small, seconds) run in test 2 acceptable while Lane A's probe holds the host? It is a single process, a few ticks.
2. The ticket file is not on main yet (only in my unpushed H2 branch). OK to carry it by copying into this branch and letting the second branch's merge reconcile (same content), or do you prefer F3 wait until H2 merges?
