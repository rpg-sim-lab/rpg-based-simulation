---
status: historical
layer: ticket
authority: P2
audience: agent
phase: done
ticket_id: TCK-20261112-PROJECT-SYNC-GUARD-SEAT-AND-STALE
artifact_type: test_plan
tags: [planning, delivery]
---

# Test plan
Scoped: `tests/tools/test_session_project_sync.py`, `tests/tools/test_session_status*.py`. No network.
- Guard: one test per spelling (`--method=POST`, `-XPOST`, `-X=POST`, `-fk=v`, `--field=k=v`, `--raw-field=k=v`, `--input=f`) refused; `-XGET`/`--method=GET` allowed.
- Seat: mapped domain -> `rpg-implementer (batch)`; unmapped domain unchanged; leased worktree keeps its role.
- Stale: all branches older than window -> Stale; one fresh branch -> In progress.
- Entry point: running the file as a script (`--help`) exits 0.
- Host: mapped and fallback.

Final (as built): guard 13 refused cases plus 2 allowed; seat 2; Stale 5 (stale, fresh, unknown age; one fresh branch; open PR and Blocked win; filing branch; other-host entry); entry point 1; host 1; registry 1. 77 tests in test_session_project_sync.py + test_session_status*.py.
