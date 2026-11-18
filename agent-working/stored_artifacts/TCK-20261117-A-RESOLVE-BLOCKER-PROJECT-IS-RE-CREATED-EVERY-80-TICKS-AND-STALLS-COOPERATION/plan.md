---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20261117-A-RESOLVE-BLOCKER-PROJECT-IS-RE-CREATED-EVERY-80-TICKS-AND-STALLS-COOPERATION
phase: done
artifact_type: plan
date: 2026-11-18
tags: []
---

# Plan: churn fix (divergence 2.214, STRAT-355)

Designer rulings via rpg-planner (#715; blocker-owned clock).
1. A re-inferred blocker merges into the stored one (`merge_inferred_blocker`): suppression and failure count survive.
2. Timeout (50 ticks) ends resolve_blocker ABANDONED/BLOCKER_TIMEOUT, failure_count+1, suppression 100/200/400/800.
3. A congestion blocker is removed only after 200 ticks of observable quiet (no live resolve_blocker names it; counted from last_seen, suppression end and `last_project_end_tick`); removal ends no project.
4. `ProjectState.ended_tick` and `BlockerState.last_project_end_tick` (appended last, omitted while None, FIELD_RULES fill None); the stamp is written by the same StrategicUpdate that ends the project, through one helper `ended_blocker_stamps`.
5. Docs: Bible 04, divergence 2.214, STRAT-355. Tests: lifecycle, end-site source scans, checkpoint fields.
6. Own-job: 3 gate worlds s42 + urban s123, 5000t, spy + plain twin, bars B1-B6 = 0, not vacuous, twin match.
