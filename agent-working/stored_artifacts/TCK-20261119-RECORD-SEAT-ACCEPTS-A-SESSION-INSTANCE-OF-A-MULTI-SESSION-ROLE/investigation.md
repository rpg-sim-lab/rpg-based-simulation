---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261119-RECORD-SEAT-ACCEPTS-A-SESSION-INSTANCE-OF-A-MULTI-SESSION-ROLE
artifact_type: investigation
tags: [delivery]
---

# investigation — TCK-20261119-RECORD-SEAT-ACCEPTS-A-SESSION-INSTANCE-OF-A-MULTI-SESSION-ROLE

Base: 9d308c29d (origin/main ea3d374d0 plus the planner's filings). Keying read: `state.write_bound_worktree(root, instance, path, explicit)` writes `<state root>/<instance>/worktree.json`; `_check_role` accepts any `^[a-z0-9][a-z0-9-]*$`; `launch.resolve_target` accepts `instance_ids(role, max_sessions)` and the launcher writes the bound worktree and the instance record under `target.instance`. So an instance record already exists in the current format. Readers: `status.seat_infos` / `_worktree_for` and `project_sync.read_branch_facts` read by `role.role` only, so instance records were written and never read. max_sessions on this base: rpg-implementer 4, rpg-implementer-ubuntu 4, all others 1. Measured on ubuntu: 1 explicit instance record (`rpg-implementer-ubuntu-2`, live). Before/after dry run on origin/main ea3d374d0: 1 changed row. Not measured: u24's instance records (run `record_seat.py --list` there).
