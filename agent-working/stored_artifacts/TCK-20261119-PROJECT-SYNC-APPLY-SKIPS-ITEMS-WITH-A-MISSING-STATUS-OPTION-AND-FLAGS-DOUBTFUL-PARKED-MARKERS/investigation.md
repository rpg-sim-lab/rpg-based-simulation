---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261119-PROJECT-SYNC-APPLY-SKIPS-ITEMS-WITH-A-MISSING-STATUS-OPTION-AND-FLAGS-DOUBTFUL-PARKED-MARKERS
artifact_type: investigation
tags: [delivery]
---

# investigation — TCK-20261119-PROJECT-SYNC-APPLY-SKIPS-ITEMS-WITH-A-MISSING-STATUS-OPTION-AND-FLAGS-DOUBTFUL-PARKED-MARKERS

Measured on origin/main 0c18f6151. `apply_plan` (project_client.py) ran two checks before its first mutation: every field of VALUE_ORDER plus Source and Sync hash must exist (else `ClientRefused`, run --init first) and every planned value of a select field (Status, Tier, Layer, Priority, Domain) must be an option (else `ClientRefused` naming all of them). `_main` turned a refusal into exit 2; `main()` wrote last-run.json (rc, done, left, error, heartbeat, stale_hosts, failed_streak); no heartbeat on a refusal; the SessionStart hook prints a line at failed_streak >= 2 with the `error` text. The units are Type=oneshot, no Restart=, timer OnCalendar hourly Persistent=true. A throwaway transient timer on this host (a job exiting 3) ran again 7 seconds later: a non-zero exit does not stop the next tick. The existing last-run.json on this host was rc 0 (17:19Z). Decisions by agent-working-planner 2026-11-20: exit 3 counted in failed_streak with the count in a new `skipped` key and the first ids in `error`; all select fields; skip the whole item; both Parked findings. Not measured: the first live behaviour on Project 1 (no live write was made).
