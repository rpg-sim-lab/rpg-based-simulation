---
status: active
layer: ticket
authority: P2
audience: agent
phase: in_progress
ticket_id: TCK-20261114-PROJECT-CLIENT-WRITE-PACING
artifact_type: investigation
tags: [planning, delivery]
---

# Investigation

- `project_client.py` (334 lines): one `graphql()` call path, `_mutate` wraps it for all 8 writes. No retry, no wait; any non-zero rc or `errors` raises `ProjectError` (redacted).
- `apply_plan` already stops at the first `ProjectError` and returns (done, not_done, error); `project_sync.main` prints `applied N step(s); STOPPED, k not done`. Item order puts `Sync hash` last per item, so a stopped run is reconciled by the next plan.
- `project_sync.load_config` only keeps keys present in `DEFAULTS`: the new block must be added there too.
- `gh api graphql --input -` prints no response headers by default; `retry-after` is therefore visible only if gh includes it in an error message. Exponential backoff covers the rest.
- The study (recommendation 7): secondary limits about 2,000 points/min, a P3 first load about 2,200 mutations; 1/s keeps well under it. Point cost unconfirmed; measured on the first P3 load.
- search_docs/graphify: no prior doc or ticket on client pacing (the hits were unrelated backoff work in `src/`).
