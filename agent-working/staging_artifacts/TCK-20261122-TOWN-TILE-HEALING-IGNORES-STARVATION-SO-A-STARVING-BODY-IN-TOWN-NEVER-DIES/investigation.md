---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20261122-TOWN-TILE-HEALING-IGNORES-STARVATION-SO-A-STARVING-BODY-IN-TOWN-NEVER-DIES
artifact_type: investigation
tags: []
---

# investigation: TCK-20261122-TOWN-TILE-HEALING-IGNORES-STARVATION-SO-A-STARVING-BODY-IN-TOWN-NEVER-DIES

_Written at close, after the change was built and tested (the design ruling arrived by relay from rpg-planner, rpg-designer option A)._

- Writer: `src/engine/town_resolution.py` Part A (+1 per town pass, no hunger check). The ticket's `src/systems/` path was wrong.
- Drain: `apply.py` accrues hunger first (biological-due ticks), then tests `STARVING_LINE` on the accrued value (:131-133); apply tick is `state.tick + 1` (`kernel.py:772`).
- So a gate on the prior hunger leaks one heal on the crossing tick. Executed: with a prior-hunger gate the crossing body ends at hp 11 after `ApplyPath.apply_generation`.
- The state hash is not read from RunLedger; unrelated to this change.
