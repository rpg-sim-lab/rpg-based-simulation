---
status: active
layer: ticket
authority: P2
audience: agent
phase: inprogress
ticket_id: TCK-20261114-PROJECT-CLIENT-WRITE-PACING
artifact_type: test_plan
tags: [planning, delivery]
---

# Test plan

All in `tests/tools/test_project_client.py`, no network, injected `clock`/`sleep`/runner, no real sleeps.
1. Pacing: 3 mutations back to back sleep `min_interval_s` between them, none before the first; queries (`load_project`, `list_items`) never sleep.
2. `retry-after: N` in the error text is waited exactly N s (capped), then the call succeeds.
3. No wait time given: sleeps follow max(60, base*2^k), bounded by the cap. After a backoff the next mutation's min-interval sleep is computed from the injected clock (0 extra if the interval already passed), not a fixed 1 s.
4. GraphQL `RATE_LIMITED` raises at once (1 call, 0 sleeps) with the 'primary rate limit' message. 429 and 403-with-'rate limit' text are secondary: the first retry waits >= 60 s (max(secondary_min_wait_s, base*2^k), capped), or retry-after when shown. A plain 403 (permission) and a normal GraphQL error raise at once, no retry, no sleep.
5. After `max_tries` rate-limited answers: `ProjectError` (redacted: sentinel token never in the message); through `apply_plan` this gives done/not_done/error as P1b.
6. Progress: callback fires every N steps and not on a stopped run's missing steps.
7. Rerun: stop mid-run; the STOPPED output prints `partial: <ticket id>`; second run does only the unfinished steps; the rerun's only hand-edit lines are for the partial id and the rerun overwrites them.
8. Config: `Pacing` from config with missing/bad values falls back to defaults.
Run: `pytest tests/tools/test_project_client.py tests/tools/test_session_project_sync*.py tests/tools/test_session_status*.py -p no:randomly` (scoped, with `TMPDIR=/mnt/data/Working/tmp-u24 --basetemp`).
