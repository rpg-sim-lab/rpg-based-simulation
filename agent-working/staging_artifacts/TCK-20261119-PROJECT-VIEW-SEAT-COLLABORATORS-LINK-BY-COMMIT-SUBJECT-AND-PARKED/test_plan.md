---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261119-PROJECT-VIEW-SEAT-COLLABORATORS-LINK-BY-COMMIT-SUBJECT-AND-PARKED
artifact_type: test_plan
tags: [delivery]
---

# test_plan — TCK-20261119-PROJECT-VIEW-SEAT-COLLABORATORS-LINK-BY-COMMIT-SUBJECT-AND-PARKED

Scoped: `tests/tools/test_session_project_view.py`, `tests/tools/test_session_record_seat.py`, the existing `tests/tools/test_session_project_sync*.py`, `tests/tools/test_project_client.py`, `tests/tools/test_session_status.py`, `tests/tools/test_session_launch.py`. Each new derivation has a positive control and a must-not case (cited-only subject; a merged commit; prose "depends on"; a file cited only once; a second worktree for one seat). Live-case checks (coin fix, STALEMATE F1, #965) are done by the u24 side at the before/after dry run, not claimed from ubuntu.
