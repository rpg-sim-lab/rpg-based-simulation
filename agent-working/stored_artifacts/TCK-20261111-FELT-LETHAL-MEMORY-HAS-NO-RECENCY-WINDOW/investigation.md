---
status: historical
layer: combat
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20261111-FELT-LETHAL-MEMORY-HAS-NO-RECENCY-WINDOW
phase: done
date: 2026-11-12
tags: []
---

# Investigation: the felt-lethal memory (code read on main 5e58ae857, read-only)

Owner approval to run this ticket: #715 6813227854. No src edits until rpg-designer rules on the shape.

## What feeds `felt_lethal_attacker` (src/engine/felt_swing.py:16-29)

Three CombatComponent fields (src/core/state.py:444-446): `last_attacker_id`, `last_hit_tick`, `last_hit_damage`.

The predicate reads only `last_attacker_id` and `last_hit_damage` (felt_swing.py:23-24), plus hp. It never reads `last_hit_tick`.
It returns the attacker when all of these hold:
- `last_hit_damage` is set and `>= combat.hp` (line 24);
- `last_attacker_id` is among `LegalityServiceV2.get_engaged_hostiles(entity, state)` now (line 26; engaged = alive, active, hostile and orthogonally adjacent, legality.py:553-578);
- the attacker is alive (line 29).

## Where each is written (the only write site)

`CombatPatch.apply`, src/engine/patches.py:327-338:
- `last_attacker_id` = `u_com.attacker_id` when a CombatUpdate carries an attacker and `damage_taken > 0`, else unchanged (line 330).
- `last_hit_tick` = `hit_tick_set` when `hit_landed` (attacker set, damage_taken > 0, hit_tick_set not None), else unchanged (line 337).
- `last_hit_damage` = `hit_damage_set` when `hit_landed` and it is not None, else unchanged (line 338).

Producers of `hit_tick_set=state.tick` and `hit_damage_set`: src/engine/combat.py:228, 303, 404, 455, 513. A hazard drain carries no attacker, so it never writes.

## Where each is cleared

Nowhere. The only `replace(...)` site for these three names is patches.py:336-338, and each falls back to the old value. Nothing clears them on regen, on the attacker leaving, on disengagement, or with time. A different attacker's landed hit overwrites all three together. The attacker dying makes the predicate return None (felt_swing.py:29) but does not clear the fields. Checkpoints carry them (checkpoint.py:19, v4 digest hashes `last_hit_damage`).

So a pin ends only when: hp rises above the remembered damage (regen), the attacker leaves adjacency or dies, or a new landed hit replaces the memory.

## An existing recency use, for comparison

src/engine/tactical_threat.py:131-132 treats a hit as a wake only when `tick - last_hit_tick <= NEED_WAKE_CADENCE` and the attacker matches. `last_hit_tick` is written with the other two (patches.py:337) and is used with a window there. `felt_lethal_attacker` does not use it.

## Who consumes the predicate

- 2.202 flight guard: src/engine/tactical_flight_guard.py:67 (`flight_weighs_free_swing`).
- 2.204 step guard: src/engine/movement.py:178 (`_held_by_felt_lethal_swing`); a step off engagement with the felt-lethal attacker engaged is held as a blocked step (`ReasonCode.FELT_LETHAL_FREE_SWING`), unless the step is evasive (skip_oa).

Any change to the predicate moves both guards.

## `stalemate_break_update` and a held subject

src/engine/tactical_hold.py:54-61 builds the STALEMATE_BREAK wander. Its only caller is src/engine/tactical.py:462-464, guarded by `stale_ticks > 10 and not fighting_adjacent`, where `fighting_adjacent = is_adjacent(entity, target)` (tactical.py:455, divergence 2.87). An engaged subject is orthogonally adjacent to its hostile by definition, and a 2.204 pin needs the felt attacker engaged. So for the engaged target the breaker is off. It can fire only for a target that is not adjacent, and cannot release a pin on the felt attacker. The held step leaves position and `wait_count` unchanged (movement.py:171-183), so nothing in the movement path ages the hold either. (`scenario_runtime._stall_counter`, scenario_runtime.py:370-374, is a scenario-level event counter and unrelated.)

## Open (needs the trace)

1. Why the held rows go from every tick to every 10th after about t1960 for e31 (frontier_marches s42).
2. How e31 leaves the engagement before its DEFEAT at t2407.
