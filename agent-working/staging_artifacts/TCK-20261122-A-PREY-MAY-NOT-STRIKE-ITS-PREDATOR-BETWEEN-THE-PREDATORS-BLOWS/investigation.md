---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20261122-A-PREY-MAY-NOT-STRIKE-ITS-PREDATOR-BETWEEN-THE-PREDATORS-BLOWS
artifact_type: investigation
tags: []
---

# investigation: TCK-20261122-A-PREY-MAY-NOT-STRIKE-ITS-PREDATOR-BETWEEN-THE-PREDATORS-BLOWS

_Written at close of the implementation step, after the change was built and tested._

Old attack_allowed allowed a wild-pair strike only if the attacker hunts (PREDATION) or the target's task named the attacker. A predator between blows has payload None, so its prey was refused. The held swing keeps target_id; REPOSITION and the stalemate-break wander drop it. Designer ruled option (b) first (task-read engagement plus recent hit), then CHANGED it on review: a task read lets every attempted attack permit itself (the attack task names its own target; non-combat payloads with a target_id match too), so the final rule has no task read, only the recent hit either way. Limits disclosed in 2.222.
