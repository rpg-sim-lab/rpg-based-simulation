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

# TCK-20261103-A-GROUP-HIT-RECORDS-ONLY-ITS-FIRST-ATTACKER: investigation

- Only caller of resolve_multi_attack: movement.py:362, the opportunity-attack step of a disengaging subject (is_lethal=False). Ordinary attacks use resolve_attack (one attacker).
- combat.py:403 returns attacker_id=valid_attackers[0].id; hit_tick_set=state.tick; hit_damage_set=total_damage (SUM over attackers). patches.py:330-337 writes last_attacker_id, last_hit_tick, last_hit_damage.
- Readers: tactical_threat._hit_acts_on (row 88 (b), id equality); felt_swing.felt_lethal_attacker (reads last_hit_damage as the last attacker's swing: a group hit attributes the sum to attacker 0); death_cause/lifecycle.py:146 (killer = attacker 0).
- Counts of 2+ attacker calls per world: pending run (mc_count.py, groups_base/out_mc), needs lead-planner go.
- Fix shape proposed (C): CombatComponent.last_hit_attackers tuple[int,...] riding last_hit_tick; ruling pending (#634). Rejected: last-writer-wins (fails AC), per-attacker tick map (shared tick, unbounded).
