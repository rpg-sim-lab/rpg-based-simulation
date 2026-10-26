---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20261023-CHECKPOINT-RESTORE-DRAWS-STATELESS-RANDOMS-FROM-SEED-ZERO
phase: done
date: 2026-10-23
tags: []
---

# TCK-20261023-CHECKPOINT-RESTORE-DRAWS-STATELESS-RANDOMS-FROM-SEED-ZERO

## Title
A restored checkpoint rebuilds DeterministicRNG with base_seed=0, so stateless draws after a restore differ from the unbroken run (#593 F3)

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
#593 F3 (comments 6345868460, 6345945757, 6346376586; verified on main by rpg-planner 2026-10-22). `src/engine/scenario_checkpoint.py:83-85` builds `DeterministicRNG(base_seed=0)` on restore with the comment "base_seed is irrelevant post-restore", but `set_state` restores only the per-domain streams, and the stateless `get_int`/`get_float` seed from `_composite_seed(self._base_seed, ...)` (`src/platform/rng.py:85-102`). `scenario_runtime.py:420` builds with `base_seed=initial_state.seed` (`:423` consistent per ubuntu's correction). A restored seeded episode therefore diverges from the unbroken run.

## Scope
1. Restore with the episode's real base seed (from the checkpoint header or state), not 0; fix the stale comment at :83-84.
2. Sizing/regression test: restore at tick N, run K ticks, compare final hash and stateless draws with an unbroken run of N+K.

## Out of Scope
Other checkpoint fields (F1, perf's scheme bump).

## Acceptance Criteria
- A restore-at-N + K run equals the unbroken N+K run (state hash and a sample of stateless draws) on at least one seeded world.
- The comment at scenario_checkpoint.py:83-84 states the actual rule.

## Related Tickets
TCK-20261019-RECORD-BASELINE-V1 (v1 recorded 341f700d0; after-v1 work).

## Related Docs
#593 (lead-planner relays); docs/plans/architecture/faster_feature_testing_draft_tickets.md; docs/engine/performance_contract.md.

## Related Stored Artifacts
agent-working/stored_artifacts/TCK-20261023-CHECKPOINT-RESTORE-DRAWS-STATELESS-RANDOMS-FROM-SEED-ZERO/{plan,investigation,test_plan}.md

## Related Code Areas
src/engine/scenario_checkpoint.py; src/platform/rng.py; src/engine/scenario_runtime.py

## Assumptions / Open Questions
Determinism finding; paired/gate runs never restore, so v1 is unaffected.

## Implementation Notes
Restore now builds `DeterministicRNG(base_seed=state.seed)`; the comment states the rule. No checkpoint format change (the seed is in the pickled state). docs/engine/scenario_runtime_contract.md and parity INFRA-215 updated. The F3 ticket moved here from the unpushed H2 branch (single copy). Plan approved by rpg-planner 2026-10-26.

## Test Summary
Two new tests in tests/unit/engine/test_scenario_checkpointer.py, both red on main (rng.seed 0 vs 12345; restored stateless draw 0.989 vs unbroken 0.402) and green with the fix. Note: the N+K state hash was equal even on main in this movement world (its first ticks do not feed a stateless draw into hashed state), so the draw/seed assertions are what prove the bug. Green: checkpointer + scenario API (24), scenario integration (30), parity ledger (101). Paired/gate runs never restore; no hash proof applies.

## Files Changed
src/engine/scenario_checkpoint.py; tests/unit/engine/test_scenario_checkpointer.py; docs/engine/scenario_runtime_contract.md; docs/parity_ledger/infrastructure.yaml (INFRA-215).

## Completion Summary
A restored checkpoint now keeps the episode's real base seed, so stateless draws and domains first used after the restore match the unbroken run.
