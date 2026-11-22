---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20261122-TOWN-TILE-HEALING-IGNORES-STARVATION-SO-A-STARVING-BODY-IN-TOWN-NEVER-DIES
artifact_type: test_plan
tags: []
---

# test_plan: TCK-20261122-TOWN-TILE-HEALING-IGNORES-STARVATION-SO-A-STARVING-BODY-IN-TOWN-NEVER-DIES

_Written at close, after the change was built and tested (the design ruling arrived by relay from rpg-planner, rpg-designer option A)._

tests/unit/engine/test_town_heal_starvation_line.py: hunger 95/96/100 no heal; 0-94.9 heals; 94 vs 95; full-health body not healed; starving replay equals the drain's loss; crossing body not healed (direct and through ApplyPath); no-accrual tick still heals. Controls: gate lifted heals; prior-hunger gate heals the crossing body.
Scoped run (executed): tests/unit/engine, tests/unit/resource, interaction recovery, logic guards, vacancy signal, starvation over days, `not slow`: 1611 passed, 4 skipped, 1 xfailed. Parity tool tests: 192 passed.
