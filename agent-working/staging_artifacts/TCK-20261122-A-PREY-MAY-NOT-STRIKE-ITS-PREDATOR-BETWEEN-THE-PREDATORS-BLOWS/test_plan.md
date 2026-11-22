---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20261122-A-PREY-MAY-NOT-STRIKE-ITS-PREDATOR-BETWEEN-THE-PREDATORS-BLOWS
artifact_type: test_plan
tags: []
---

# test_plan: TCK-20261122-A-PREY-MAY-NOT-STRIKE-ITS-PREDATOR-BETWEEN-THE-PREDATORS-BLOWS

_Written at close of the implementation step, after the change was built and tested._

tests/unit/engine/test_attack_permission_is_symmetric.py (75 tests, executed): B0 2 pairs x 3 seeds; neither-hunts refused both ways; symmetry; real verify_attack_legality path (fed targeting, fed after drop, hungry between blows, fed repositioning 5 ticks and 11 ticks after a hit, reverse hit); window imported not copied; B5. Controls: old hostility.py fails 13 of 75. Existing legality files run one at a time: pass, except test_appraisal.py:175 (owner ask).
