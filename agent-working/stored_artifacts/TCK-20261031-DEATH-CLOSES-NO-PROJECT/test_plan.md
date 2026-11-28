---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261031-DEATH-CLOSES-NO-PROJECT
artifact_type: test_plan
tags: []
---

# Test plan

Unit (tests/unit/strategic/test_death_ends_live_projects.py): ACTIVE and SUSPENDED end ABANDONED/DEATH with records kept; current cleared; typed update, prior state untouched; old-age body (alive stays True); already-ended / removed this tick not ended twice; a staged new project ended in the same update; no strategic update for a body with nothing live and no current; blocker stamp; `end_live_on_death` pure; checkpoint round trip and canonical hash; a non-dying body untouched; capacity_enforcement trims nothing on the corpse (ended records are not live); redirection issues no navigation for the dying body.
Existing: tests/unit/strategic/test_project_end_record.py (enum set). Then the lifecycle, strategic and capacity domains' tests and mypy on the touched src, in the lock env, when the host is free.
Run-level (executed under the S9 #715 7185997232 with the own-job kit 18f7b53c7; results in investigation.md, written at close; originally planned as the heavy queue): hash move, extra project events per run, dead-with-live-project count on the gate worlds (target 0), Phase 1 items 2 and 3.
