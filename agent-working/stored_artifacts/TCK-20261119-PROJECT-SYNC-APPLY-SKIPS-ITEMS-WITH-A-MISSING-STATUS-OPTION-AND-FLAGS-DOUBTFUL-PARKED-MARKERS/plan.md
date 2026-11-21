---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261119-PROJECT-SYNC-APPLY-SKIPS-ITEMS-WITH-A-MISSING-STATUS-OPTION-AND-FLAGS-DOUBTFUL-PARKED-MARKERS
artifact_type: plan
tags: [delivery]
---

# plan — TCK-20261119-PROJECT-SYNC-APPLY-SKIPS-ITEMS-WITH-A-MISSING-STATUS-OPTION-AND-FLAGS-DOUBTFUL-PARKED-MARKERS

`skipped_items` and `apply_plan` skip whole items (creates and updates) whose planned select value has no option and record them on `plan.skipped`; `_main` returns EXIT_SKIPPED (3) when nothing else stopped the run, fills `info["skipped"]` and an honest `error`, prints one finding per item; `main()` writes `skipped` to last-run.json; the live dry run says `apply would skip the item`; `parked_status` adds the live-branch finding and treats a self-naming marker as malformed. A missing field still refuses. No hook edit, no live write.
