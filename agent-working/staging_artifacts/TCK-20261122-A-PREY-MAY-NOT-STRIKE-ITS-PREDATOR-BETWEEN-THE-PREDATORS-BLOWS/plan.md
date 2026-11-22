---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20261122-A-PREY-MAY-NOT-STRIKE-ITS-PREDATOR-BETWEEN-THE-PREDATORS-BLOWS
artifact_type: plan
tags: []
---

# plan: TCK-20261122-A-PREY-MAY-NOT-STRIKE-ITS-PREDATOR-BETWEEN-THE-PREDATORS-BLOWS

_Written at close of the implementation step, after the change was built and tested._

Make attack permission a property of the pair (decision 47 wild path): faction verdict OR engaged (task names the other, or a hit within ATTACKED_RECENTLY_WINDOW_TICKS, both ways) OR PREDATION either way. Drop the target-task clause. Tests with failing controls; Bible ch02 §7; divergence 2.222; parity COMB-359. Out: choosing to strike back (Step B), faction tables.
