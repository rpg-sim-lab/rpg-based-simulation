---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20261103-A-GROUP-HIT-RECORDS-ONLY-ITS-FIRST-ATTACKER
phase: open
date: 2026-11-15
tags: []
---

# TCK-20261103-A-GROUP-HIT-RECORDS-ONLY-ITS-FIRST-ATTACKER: plan

1. After the ruling: add CombatUpdate.hit_attackers_set and CombatComponent.last_hit_attackers (default empty tuple); CombatPatch.apply writes it with the other hit fields when hit_landed; resolve_attack, skill, area and opportunity paths write a 1-tuple.
2. _hit_acts_on: hostile.id in last_hit_attackers and window test. last_attacker_id keeps its meaning.
3. FIELD_RULES row, to_canonical_dict, digest version bump v5 with the comment line, TCK-20261103-STATE-DIGEST-MAY-OMIT-FIELDS-THAT-DECISIONS-READ cross-check.
4. felt_swing per the ruling (option b, #634 6883450273): CombatComponent.last_hit_damages tuple[int, ...] parallel to last_hit_attackers (int, since hp and last_hit_damage are int); CombatUpdate.hit_damages_set from simultaneous_intents; last_hit_damage stays the sum. swing = sum of the shares of the set's attackers engaged now; lethal = swing > 0 and swing >= hp. Disclose under 2.204 (text to u24's rpg-planner) and measure felt-lethal holds vs base (count, length, no-hit holds of 50+ ticks).
5. Tests: tests/unit/engine/test_group_hit_records_every_attacker.py (written, 2 red), plus field/digest/checkpoint rows.
6. Docs (ledger ids from COMB-354): Bible ch.04 (and ch.02 if it states the single attacker), parity combat_movement.yaml and strategic_cognition.yaml (row 88 act test), divergence 2.148 (verify free on main before taking).
7. Hot-loop timing NOT MEASURED (perf pause #715 6556861718).
