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

# TCK-20261101-A-HOSTILE-ATTACKING-YOU-OUTRANKS-THE-GROUP-SHARED-TARGET: plan

Blocked on ticket 1's record. 1. Add the term (0 if the hostile is in last_hit_attackers and tick - last_hit_tick <= N else 1) before group_bias. 2. N from tuning/content, with a test that changing it changes the window. 3. Unit rows: t894 pick (27 over shared 30), plain focus fire unchanged, attacker is the shared target, N configurable, two-attacker group hit. 4. Paired Tier 1/Tier 2 deaths base vs fix on the standard seeds (needs lead-planner go per run set). 5. Bible ch.02, combat_movement.yaml, divergence 2.149. Hot-loop timing NOT MEASURED.
