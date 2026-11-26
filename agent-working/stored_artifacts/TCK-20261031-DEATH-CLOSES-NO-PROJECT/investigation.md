---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261031-DEATH-CLOSES-NO-PROJECT
artifact_type: investigation
tags: []
---

# Investigation: readers of a dead body's live projects (Phase 1 item 1)

Written at dispatch time from a read-only static audit of main d084b9248 (inspected, not executed). Full table was sent to rpg-planner; summary:
- Death authority: `LifecycleSystem.resolve_lifecycle` (lifecycle.py:171, death block ~:264); runs after strategic_intelligence and before capacity_enforcement. Old-age death sets `lifecycle.active=False` and never writes `combat.alive`.
- Typed end: `ProjectEnd` had no DEATH; `end_record` is the one writer of `ended_by`.
- Hash: canonical dict and replay fingerprint carry project status, `ended_by`, `ended_tick` and current_project_id with no alive filter.
- Readers that see a dead body's projects: state presenter, entity inspector, cognition and personality recorders, event shapers / quest extraction, SimQ agency (project_abandoned), canonical dict and fingerprint; capacity_enforcement and redirection once an update is staged; profile_engine strategic scenario (tool).
- Readers that skip dead bodies: the strategic evaluation path (including the :1610 orphan/make-current path, now live_record_route), work_queue, candidate_selector, tactical, guild/paid-info/lodging, cooperation, information, perception, metrics (alive only).
- `blocker_lifecycle.resolve_blockers` has no caller: out of scope.
- Unknown, rides the measured step: event deltas per run, corpse trim by capacity_enforcement (unit-tested here), redirection on the death tick (unit-tested), groups.py:247 same-tick leader death, the passive-death 1-tick lag.

## Answer to the mechanism-registry changed-code advisory (rpg-planner ruling, 2026-11-25)
The advisory named three mechanisms whose cited code changed without their entry changing: `aging_death` and `succession` (lifecycle.py) and `goal_hierarchy` (core/strategic.py). Death of ANY cause (kill, defeat, hazard, passive, old age) ends the body's live projects, so the behaviour belongs to `goal_hierarchy`, not to old age or heirs. `goal_hierarchy` gets the summary sentence "A creature's live projects all end when it dies; the records are kept." and two `implemented_by` entries (`src/core/strategic.py::end_live_on_death`, `src/systems/lifecycle_systems/lifecycle.py::LifecycleSystem::_end_projects_on_death`). `aging_death` and `succession` are unchanged. The mechanism views were regenerated with their generators (verification, priority, registry, system rollup, html); they came out byte-identical, so only registries/mechanisms.yaml changed. `registry.py` validates (110 mechanisms). The completeness test runs later with the other runs.

## Run evidence (executed; written at close, 2026-11-26, after the run)
This section was written at close, not at dispatch; the sections above are the dispatch-time audit (inspected, not executed).
- Run: S9 on #715 (comment 7185997232). Kit 18f7b53c7 (tools/rpg_measure/death_closes_project_*, SHA256SUMS sha256 05d688a9, approved by rpg-designer). BASE main 4af5ef2a3 (spied only) against FIX f5a520daf (plain twin, then spied). crowded_frontier, frontier_living_world, urban_political, each s42, 5000 t. Summary `death_closes_project_summary.json` sha256 e83078e8. Wall: base arm 1167 s, fix arm 1669 s.
- Bars (definition sha256 df2ba4b5): D1-D7 PASS in all three cells; rpg-designer's own recount matches (WORKS, recorded on #715 as 7187444028).
- Phase 1 item 1 (readers), now measured: base 32 / 30 / 15 dead bodies held a live project at their death (34 / 31 / 15 dead bodies in total), against 0 for fix at every tick. DEATH ends 61 / 68 / 26 (ACTIVE 35 / 33 / 14, SUSPENDED 26 / 35 / 12, so the SUSPENDED branch is exercised in every cell), equal to the extra ended transitions. The living projection (the canonical state with each dead body's `strategic` dropped) and the full world-event stream equal base at every tick; the full state hash differs only through the dead bodies' strategic part, as divergence 2.226 discloses.
- Passive-death lag (limit 1): 0 lag rows in all three cells.
- `capacity_enforcement` writes to a dead-or-dying body holding a live project: base 172 / 170 / 91 rows (including contract rewrites on dead bodies every few ticks), fix 32 / 30 / 15, all on a dying body at its death tick. The base behaviour goes to the cognition backlog (rpg-planner); it is not part of this change.
- `StrategicRedirectionSystem` is never called by the pipeline (logic hoisted into `StrategicIntelligenceSystem`, intelligence.py:518): its death-tick effect is NOT MEASURED. SimQ `project_abandoned` is NOT MEASURED (recording off).
- The `quest_status` candidate follow-up has no measured case: quest projects ended DEATH with the quest still open = 0 in all three cells (note only).
- The mechanism-registry advisory answer above stands.
