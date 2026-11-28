---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261031-DEATH-CLOSES-NO-PROJECT
artifact_type: plan
tags: []
---

# Plan: death ends every live project

1. `ProjectEnd.DEATH` (src/core/strategic.py), docstring paired to ABANDONED; pure `end_live_on_death(projects, staged, removed, tick)` over `end_record`.
2. `LifecycleSystem._end_projects_on_death` called in the `if is_dead:` block of `resolve_lifecycle` (sole death authority; covers old age): ends live records, stamps the resolve_blocker blocker (`ended_blocker_stamps`), sets `current_project_id_set=""` and `current_objective_id_set=""`; no update when there is nothing to end and no current project.
3. Tests (written; run when the host allows): tests/unit/strategic/test_death_ends_live_projects.py; the enum-set pin in test_project_end_record.py gains DEATH (a changed existing expectation, reported).
4. Docs: Bible ch04 section, divergence 2.226, parity STRAT-357.
5. Not in this change: quest_status, resolve_blockers (no caller). The measured run was done under the S9 #715 7185997232 (see investigation.md, written at close). No push.
