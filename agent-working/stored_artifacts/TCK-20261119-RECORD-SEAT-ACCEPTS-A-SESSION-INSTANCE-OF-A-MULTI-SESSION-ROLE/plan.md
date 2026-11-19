---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261119-RECORD-SEAT-ACCEPTS-A-SESSION-INSTANCE-OF-A-MULTI-SESSION-ROLE
artifact_type: plan
tags: [delivery]
---

# plan — TCK-20261119-RECORD-SEAT-ACCEPTS-A-SESSION-INSTANCE-OF-A-MULTI-SESSION-ROLE

record_seat resolves names with `resolve_target` and checks every role and instance for a worktree already recorded; `status.instance_seats` yields explicit instance records; `project_sync.read_branch_facts` adds them to `seat_of` (an instance replaces its own base role on one worktree); `--list` counts records. No `state.py` or `launch.py` change, no new Project field, no init step.
