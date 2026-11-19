---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261119-PROJECT-VIEW-PARKED-STATE-FROM-A-TICKET-BODY-MARKER-LINE
artifact_type: plan
tags: [delivery]
---

# plan — TCK-20261119-PROJECT-VIEW-PARKED-STATE-FROM-A-TICKET-BODY-MARKER-LINE

Code: marker parser and `parked_status` in tools/sessions/project_sync.py, `Parked` last in STATUSES, YELLOW in STATUS_COLORS, the `parked:` ran/skipped/errored note; docs in project_sync_dry_run.md, delivery_process.md, a pointer in functions/planner.md outside the Card.
MIGRATION ORDER (draft; the scratch-Project result decides whether step 2 can be after the land; proven in the dry run before any live write). Both hosts' hourly timers run `project_sync.py --apply --fetch`: (1) stop `project-sync.timer` on each host (ubuntu: `systemctl --user stop project-sync.timer`; u24's commands are lead-planner-u24's); (2) the token holder runs `python3 tools/sessions/project_sync.py --init` once from the main checkout: it appends the Parked option on the populated Status select (existing options keep their ids; `--replace-status-options` is NEVER used); take a read-only snapshot of every item's Status first (dry run output) so a diff after the first apply shows anything that moved; (3) the owner lands the PR and each host fast-forwards its main checkout; (4) the token holder runs the first `python3 tools/sessions/project_sync.py --apply --fetch` by hand, one host after the other (no marker exists, so no Status changes); (5) start the timers. Old code with the Parked option present is unaffected (it never plans Parked); new code without the option and without any marker is unaffected (`--apply` refuses only when a planned Status has no option). No live write without the owner's logged yes and the scratch evidence.
