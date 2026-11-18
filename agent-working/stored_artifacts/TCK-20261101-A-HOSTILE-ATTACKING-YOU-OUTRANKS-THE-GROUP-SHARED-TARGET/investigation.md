---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20261101-A-HOSTILE-ATTACKING-YOU-OUTRANKS-THE-GROUP-SHARED-TARGET
phase: open
date: 2026-11-15
tags: []
---

# TCK-20261101-A-HOSTILE-ATTACKING-YOU-OUTRANKS-THE-GROUP-SHARED-TARGET: investigation

- target_score tactical.py:390-428 key: (not_adjacent, group_bias, is_current_target, -capability_confidence, hp, dist*pressure_dist_mod, id). New term goes after not_adjacent and before group_bias (CONFLICT-04 keeps adjacency first).
- A typed last-hit tick exists: CombatComponent.last_hit_tick. The attacker set comes from ticket 1 (last_hit_attackers).
- N: NEED_WAKE_CADENCE is a scheduler constant with another meaning; a tuning home for N is still to be found (rule: not a number in code). Open question assumed: a hostile targeting but not yet hitting does not count.
