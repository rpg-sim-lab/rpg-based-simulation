---
status: historical
layer: testing
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20261109-FUSED-STRATEGIC-PASS-FAST-PATH-IS-PINNED-BRANCH-BY-BRANCH-AND-AGAINST-THE-SLOW-PATH
phase: done
date: 2026-11-09
tags: [testing]
---

# TCK-20261109-FUSED-STRATEGIC-PASS-FAST-PATH-IS-PINNED-BRANCH-BY-BRANCH-AND-AGAINST-THE-SLOW-PATH: investigation

Finding: the off-cadence fast path in fused_strategic_pass (the block taken when neither concern nor intent evaluation is due, no strategic update is pending and the entity has no blockers or leads) had no test aimed at it. Twelve files call the function.

Read of src/systems/strategic_systems/intelligence.py: the fast path regroups a loaded entity home unless its project has a target_position; an entity-typed objective has no target_position, so the fast path sends such an entity home while the slow path leaves it on the pursuit (defect A, rpg-planner). The fast path also overwrites an earlier phase's target_set; the slow path keeps it (CLEAR-TARGET ticket). The in-function inactive/dead early exit is shadowed by StrategicWorkQueue.build (work_queue.py:31).

The "due" cadence for the differential is concern=1 and intent=1000; with intent also due, evaluate_strategic_intent abandons an entity-targeted project that has no real pursuit, which hides the row-1 difference. Source of the rows and risk order: rpg-planner's read-only review on #715 comment 6736224900.
