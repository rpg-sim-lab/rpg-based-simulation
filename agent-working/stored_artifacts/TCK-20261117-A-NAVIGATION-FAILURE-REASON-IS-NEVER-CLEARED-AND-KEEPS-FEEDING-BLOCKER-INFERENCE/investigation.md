---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20261117-A-NAVIGATION-FAILURE-REASON-IS-NEVER-CLEARED-AND-KEEPS-FEEDING-BLOCKER-INFERENCE
phase: done
artifact_type: investigation
date: 2026-11-18
tags: []
---

# Investigation

- Writers: `patches.py` NavigationPatch is the only assignment besides the builder default. Reader: `infer_blockers` (ACCESS blocker from PATH_NOT_FOUND/STUCK/OSCILLATING) and `information/phase.py` (`claim_failed_search` on any non-None reason).
- First own-job (fixtree_fix2) tripped R1/R3: YIELDING (a moved occupant, no clear), SOURCE_DEPLETED (action writer), OCCUPANCY_CONFLICT (refiner). The v1 spy classified success from `resolve_move`'s return, before the refiners and same-tick writers: a bar omission as well as a real defect.
- Pipeline order (pipeline.py): action_routing, position_swaps, movement_routing. So an action code can already be in `existing` at the swap and movement merge sites; a swapped body is skipped by movement routing. A blanket replace was therefore wrong and provenance tracking was implemented.
- Occupancy_violation step (v1 R3 rows, urban e6 t1130 and crowded e2 t763): see the Test Summary.
