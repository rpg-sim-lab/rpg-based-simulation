---
status: active
layer: engine
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20261103-THE-CONCURRENT-AND-SEQUENTIAL-EXECUTORS-GIVE-DIFFERENT-WORLDS
tags: []
---

# investigation - TCK-20261103-THE-CONCURRENT-AND-SEQUENTIAL-EXECUTORS-GIVE-DIFFERENT-WORLDS

Cause named by rows (rpg-ubuntu-implementer, crowded s45, 0ed040638 and 0e7b1030c):
- The two executors agree through t600 on the #828 arm; the first hashed split is t601 (entity 30's navigation and task).
- First differing output: the tactical call of entity 30 at t600, STALEMATE_BREAK target (33.18420, 32.38550) sequential vs (40.0, 34.61367) concurrent. `wander_destination` draws from `DeterministicRNG(state.seed)`; the adapter's packet seed is `rng.get_int(Domain.DEFAULT, tick, owner, 0, 1000000)` = 650141 there. Recomputed by hand to all printed digits.
- Second divergence outside the hash: the packet has no `feature_flags`; `combat_actions.py:126` reads ENABLE_COMBAT_ENGAGEMENT as OFF on a packet (state: ON), skipping `apply_combat_learning` (153 vs 241 calls to t2000); entities 16 and 30 differ in cognition contents from t100/t300.
- Silent defaults on a packet (getattr with default): building_tiles, occupancy_snapshot, caches (11,011 reads in 2000 ticks); `clans` via hasattr in core_actions.py:569/625 (not reached in crowded s45).
- Worker exceptions are swallowed by worker_manager (four handlers) into FAILURE no-ops.
- Not causes (shown): route_plans/movement_cache (all route calls come from the apply path), `_freeze_cache` (zero stale hits, 7 keys, 2000 ticks), governor/budget (policy never leaves NORMAL; budget changes nothing).
Evidence: groups_base/out_e34, out_bisect, out_seedfix, out_seedfix2 (scratch trees seedfix_arm, seedfix2_arm).
