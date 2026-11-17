---
status: historical
layer: ticket
authority: P2
audience: agent
phase: done
ticket_id: TCK-20261112-PROJECT-SYNC-DRY-RUN
artifact_type: test_plan
tags: [planning, delivery]
---

# Test plan

`tests/tools/test_session_project_sync.py`, fixtures only, no network, no real git (inputs are injected data; the CLI test stubs the three readers).

1. Rule 1: ticket in `done/` on main -> Done.
2. Rule 2: open PR listing the ticket file -> In review, PR set.
3. Rule 3: BLOCKED in a copy that exists only on a branch -> Blocked (the branch copy wins over main's).
4. Rule 4: a branch fact listing the id -> In progress with Seat and `host:branch`.
5. Rule 5: only in `todos/` -> To do; `inprogress/` with no branch -> orphan finding.
6. Ticket in two folders -> higher status and a finding.
7. Squash-merged branch: ticket in done on main and still on the branch -> Done, never In progress.
8. Uncommitted ticket file in a worktree (porcelain-only fact) -> In progress.
9. Unmapped seat -> `<domain> (unmapped)` from the prefix, else `unknown`.
10. Sync hash is stable and field-order independent; a hand-edited item is reported with the exact `hand edit:` line and is then overwritten in the plan.
11. Item with no id, or an id with no ticket file -> to-archive; a Done item whose git done date is older than the window -> archive; a Done ticket whose done date is before pilot_start gets no item.
12. Addendum: ubuntu-tagged branch entry plus an open PR seen from u24 -> In review, both host entries kept.
13. `--apply` and `--init` refused (exit 2, nothing run); no reader is called with a write verb.
14. A branch that adds a `todos/` ticket -> To do, not In progress (Branch recorded with `[filing]`).
15. An open PR that adds a `todos/` ticket -> To do, not In review.
16. Detached worktrees are skipped and counted; one changing a ticket is reported `unattributed`.
17. `gh pr list` returning exactly the limit prints the missing-PRs note.
Plus: the YAML registry loads and carries no field ids. Scoped run: this file and `tests/tools/test_session_status*.py` (unchanged), single process.
