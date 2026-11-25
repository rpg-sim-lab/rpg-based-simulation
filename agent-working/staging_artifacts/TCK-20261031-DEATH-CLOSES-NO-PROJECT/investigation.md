---
status: active
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
