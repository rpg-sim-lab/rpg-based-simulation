---
status: active
layer: combat
authority: P2
audience: agent
ticket_id: TCK-20261103-NEAR-DEATH-HARDENING-FIRES-WITH-NOTHING-HITTING-THE-SUBJECT
artifact_type: plan
tags: []
---

# plan: TCK-20261103-NEAR-DEATH-HARDENING-FIRES-WITH-NOTHING-HITTING-THE-SUBJECT

Base `e755dc3d1`; branch `rpg-near-death-hardening-hit-gate`. Owner rulings: rpg-designer via rpg-planner (the law is "survive a combat hit"; hazard does not count; gate on a typed hit fact, not the sign of hp_delta).

1. `src/engine/pipeline_phases/hardening.py`: add `_records_combat_hit(combat_update, tick)` = `attacker_id is not None and damage_taken > 0 and hit_tick_set == tick` (the predicate CombatPatch uses at patches.py:332-337 to write last_attacker_id / last_hit_tick, plus the tick equality) and `continue` when it is false, after the REJECTED check. Projected-hp test unchanged. LAW block updated.
2. Tests: edit the INPUT only of four existing tests (rpg-planner decision) so their hand-built CombatUpdate carries the hit fact; add `tests/unit/engine/test_near_death_hardening_hit_gate.py` (five rows at max 100).
3. Docs: Bible ch01 line 54; parity rows SOC-042, STRAT-142, TOWN-021 (legacy_verified/null -> verified with test_path and v2_evidence); divergence 2.201 (Bug Fix); parity-ledger schema baseline tightened (3 rows fewer).
4. Out of scope: grant size, the 10% line, the hp<15% PANIC_RETREAT writer, docs/engine (not touched).
5. Measurement (on rpg-planner's slot word): crowded 5x5000 paired against e755dc3d1.
