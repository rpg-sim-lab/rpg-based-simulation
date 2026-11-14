---
status: active
layer: ticket
authority: P2
audience: agent
phase: open
ticket_id: TCK-20261114-PROJECT-SYNC-INIT-AND-APPLY
artifact_type: test_plan
tags: [planning, delivery]
---

# Test plan
Scoped: `tests/tools/test_session_project_sync.py`, `tests/tools/test_session_status*.py`, new `tests/tools/test_project_client.py`. No network: a fake runner returns canned JSON and records every call.

1. init creates the missing fields (text and `Tier` single-select) and leaves present ones alone (second run: nothing created or updated).
2. init sets the built-in Status options to exactly `STATUSES` when they differ, and doesn't when they match.
3. init refuses a same-named wrong-type field: reports it, makes zero mutation calls, non-zero.
4. apply turns creates, updates and archives into the expected mutation sequence; `Sync hash` is the last value set for each item; empty values are skipped on create and cleared on update.
5. apply stops at a failing mutation and reports done vs not done.
6. `project.number: 0` makes `--init` and `--apply` exit 2; `--init` with `--apply`, and `--apply` with `--items`, exit 2.
7. Sentinel token: the value never appears in any recorded argv, in stdout/stderr, or in the text of a raised `ProjectError` (including when the fake gh echoes it in stderr); the call env carries it only for the child.
8. Token file missing, or mode other than 600 -> `ClientRefused` with a plain message and no gh call.
9. `_guard` still refuses `gh api graphql` on the read path; `project_sync.py` source contains no `graphql` call and `project_client.py` contains no delete mutation.
10. Live read paginates (two pages) and maps field values to the dict shape `build_plan` takes; archived items are skipped.
