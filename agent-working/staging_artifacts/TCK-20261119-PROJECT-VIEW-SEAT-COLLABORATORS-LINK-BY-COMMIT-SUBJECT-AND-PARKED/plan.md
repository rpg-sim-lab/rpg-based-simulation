---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261119-PROJECT-VIEW-SEAT-COLLABORATORS-LINK-BY-COMMIT-SUBJECT-AND-PARKED
artifact_type: plan
tags: [delivery]
---

# plan — TCK-20261119-PROJECT-VIEW-SEAT-COLLABORATORS-LINK-BY-COMMIT-SUBJECT-AND-PARKED

Files: `tools/sessions/project_sync.py` (subject_links, waits_on_ids, derive_hotspots, Segment.involved, hash v5), `tools/sessions/project_client.py` (three text fields), new `tools/sessions/record_seat.py`, `docs/guidelines/session_roles/project_sync_dry_run.md`, tests. Decisions are in the ticket thread (#715) and `investigation.md`. Parked is out of scope (separate ticket). Live `--init` / `--apply` only after the before/after dry run is shown to lead-planner and the planner and the owner's yes is logged. The u24 backfill is run by a u24 seat, not here.
