---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261119-PROJECT-VIEW-PARKED-STATE-FROM-A-TICKET-BODY-MARKER-LINE
artifact_type: investigation
tags: [delivery]
---

# investigation — TCK-20261119-PROJECT-VIEW-PARKED-STATE-FROM-A-TICKET-BODY-MARKER-LINE

Measured on origin/main 0b196a142 (224 open tickets): ticket age p50 16, p90 43, max 89 days. Only 1 line-start waits-on line names a ticket id (age 4 days, no date); 6 line-start lines begin with "Parked" (tickets aged 0 to 66 days, p50 46); 1 line in all of them carries a date. 3 of the 6 park on a DECISION (owner decision, owner_decision_memo row 7), not a ticket: hence the decision form of the marker (agent-working-planner, 2026-11-19). The 45-day stale-marker finding is a proposal, not a measurement.
Code path read: `parse_copy` (project_sync.py) reads origin's copy; `derive_status` orders Done, In review, kept status, Blocked, then (new) Parked, then working/Stale/To do. Status options: `init_fields` takes `replace_options` only with `--replace-status-options` or on an empty Project; a populated Project takes `merge_options` (append-only, existing ids kept, `set_select_options` -> `updateProjectV2Field` with `singleSelectOptions`, ids on existing entries). The only paths that clear an item's Status are an option sent without its id or left out (replace, rename). The built-in Status field has NOT been probed on GitHub: scratch-Project test pending the owner's approval (creating a Project is an owner write). Before/after dry run on origin/main 025be2faf: 0 Status rows change (no marker exists), one new `parked:` note line.
Not measured: how GitHub treats an appended option on the built-in Status field of a populated Project (scratch test); the real F1 ticket (u24 planner writes the marker after the code lands).
