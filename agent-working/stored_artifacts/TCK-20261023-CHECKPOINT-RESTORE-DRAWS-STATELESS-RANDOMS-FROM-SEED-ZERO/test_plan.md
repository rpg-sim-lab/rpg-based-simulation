---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20261023-CHECKPOINT-RESTORE-DRAWS-STATELESS-RANDOMS-FROM-SEED-ZERO
phase: test_plan
date: 2026-10-26
tags: []
---

# Test plan

| Criterion | Test |
|---|---|
| Restored RNG carries the episode seed; stateless draws and a lazily seeded domain equal a fresh RNG with that seed | tests/unit/engine/test_scenario_checkpointer.py::test_restore_rebuilds_rng_with_the_episode_seed (red on main: seed 0 != 12345) |
| Restore at N + K ticks equals unbroken N+K (state hash and sampled stateless draws), seeded world | ...::test_restore_at_n_then_k_ticks_equals_unbroken_n_plus_k (red on main at the draw assertion) |
| Seed-0 checkpoints and the REST/integration restore paths unchanged | existing checkpointer, tests/api/test_scenario_runtime_api.py, tests/integration/scenarios tests |
| Parity ledger INFRA-215 text/test_path updated | parity_ledger tests (101 pass) |
