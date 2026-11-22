---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20261122-TOWN-TILE-HEALING-IGNORES-STARVATION-SO-A-STARVING-BODY-IN-TOWN-NEVER-DIES
artifact_type: plan
tags: []
---

# plan: TCK-20261122-TOWN-TILE-HEALING-IGNORES-STARVATION-SO-A-STARVING-BODY-IN-TOWN-NEVER-DIES

_Written at close, after the change was built and tested (the design ruling arrived by relay from rpg-planner, rpg-designer option A)._

1. Gate the town-tile +1 in `src/engine/town_resolution.py` Part A on the one `STARVING_LINE` (option A, designer ruling).
2. Read the hunger the apply path will test the drain against: the post-accrual hunger of apply tick `state.tick + 1`. Extract that expression as `biological_needs.hunger_after_accrual` and use it in both `apply.py` and the gate.
3. Tests with failing controls; Bible ch01 line; divergence 2.220 (Bug Fix); parity PROG-138.
Out: the paid bed, the inn and the vitality AP; the weakened half speed; PASSIVE_HEAL_AMT.
