---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20261023-CHECKPOINT-RESTORE-DRAWS-STATELESS-RANDOMS-FROM-SEED-ZERO
phase: investigation
date: 2026-10-26
tags: []
---

# Investigation

- `ScenarioCheckpointer.restore` built `DeterministicRNG(base_seed=0)` and then `set_state(rng_checkpoint)`. `set_state` restores only the stateful per-domain `random.Random` streams. `get_float/get_int/choice/weighted_choice/sample` seed from `_composite_seed(self._base_seed, ...)`, and a domain absent from `_rng_map` is seeded lazily from `_base_seed ^ (domain.value << 16)`. Both used seed 0 after a restore.
- The episode seed is in the pickled `AuthoritativeState` (`state.seed`); `ScenarioRuntimeService._build_kernel` already uses it (seed 0 only without an initial state). No format change is needed.
- Why unnoticed: existing checkpoint tests build the service without `initial_state` (seed 0, where the old code was correct); paired/gate runs never restore.
- Observed on main with a seed-12345 movement world (30 entities, N=5, K=5): restored `rng.seed == 0`; the stateless `get_float(TACTICAL, 10, 1, 0)` differed (0.989 restored vs 0.402 unbroken). The canonical state hash at N+K was equal in that world: its first 10 ticks do not feed a stateless draw into hashed state, so the hash check alone would not have caught the bug; the draw and seed assertions do.
- Callers of restore: src/api/routes/scenarios.py and tests only.
