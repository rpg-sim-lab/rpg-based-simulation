---
status: active
layer: combat
authority: P2
audience: agent
ticket_id: TCK-20261103-NEAR-DEATH-HARDENING-FIRES-WITH-NOTHING-HITTING-THE-SUBJECT
artifact_type: investigation
tags: []
---

# investigation: TCK-20261103-NEAR-DEATH-HARDENING-FIRES-WITH-NOTHING-HITTING-THE-SUBJECT

Counts (hard_count.py 3929aa5a, base e755dc3d1, crowded s42 and s45, 5000t, end hashes equal the plain cells): s42 86 grants = 34 combat hit + 3 hazard + 1 net-zero + 48 town heal; s45 146 = 29 combat hit + 117 town heal. Non-negative hp_delta share 57% and 80%. Max hp gained through non-hit grants: s42 245 over 7 subjects (largest 95), s45 585 over 9 (largest 190).
Code: the phase reads projected hp only and never the origin of the update; positive hp_delta writers: town heal (+1, town_resolution.py Part A), lodging (+5), level-up (+20/level), consume (core_actions.py:398). The hit fact in the update: `CombatUpdate.attacker_id` + `damage_taken` + `hit_tick_set` (set by the hit resolvers combat.py:228/303/404/455/513; the hazard writer world_dynamics.py:104 sets none of them).
Law text: Bible 01:54 only described the accumulator; hardening.py's own docstring says "survives a hit". Tests: none fed the phase a non-negative hp_delta and expected a grant (full tests/ grep).
