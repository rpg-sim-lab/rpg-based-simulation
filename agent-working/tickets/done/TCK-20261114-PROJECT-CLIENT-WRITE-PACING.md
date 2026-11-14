---
status: historical
layer: ticket
authority: P1
audience: agent
ticket_id: TCK-20261114-PROJECT-CLIENT-WRITE-PACING
phase: done
date: 2026-11-14
tags: [planning, delivery]
---

# TCK-20261114-PROJECT-CLIENT-WRITE-PACING

## Title
`project_client.py` paces its writes and honours GitHub's rate-limit answers, so the P3 all-lanes first load can run (P3 prerequisite)

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P3

## Request Summary
This is a P3 prerequisite under TCK-20261112-EPIC-GITHUB-PROJECT-TICKET-VIEW, filed at the owner's direction on #715 6874493351 and
dispatched as P3a on #715 6881411615.

The best-practice study (main-checkout `.claude/handover/drafts/github-project-best-practice-2026-11-14.md`, recommendation 7) found
two things:
- GitHub limits mutations through secondary rate limits, about 2,000 points per minute, with each mutation costing more than a query.
- A P3 first load over all lanes is about 2,200 mutations.

The P1b client (#909) sends every mutation back to back with no pacing, and stops at the first failure.

## Scope
1. Pace mutations at no more than about 1 per second (configurable in `registries/session_project.yaml`). Queries are not paced.
2. On a rate-limit answer (HTTP 403/429, a `retry-after` header, or a GraphQL `RATE_LIMITED` error), wait as told, using
   exponential backoff when no wait time is given, up to a bounded number of tries. Then stop the way P1b does, reporting what was
   done and what wasn't.
3. Print progress every N steps.
4. Running again after a stop reconciles, using the existing full-reconcile plan.
5. Tests with an injected clock and runner, no network, no real sleeps: pacing, `retry-after` honoured, backoff bounded, stop after
   the last try.

## Out of Scope
- Every other part of P3: all lanes, Domain as a single-select, and the timer.
- Parallel writes.

## Acceptance Criteria
1. Scope items 1-5 are built, and the scoped tests pass.
2. A live dry run and an `--apply` on Project 1 still behave as in P1b.
3. Staging artifacts exist, and agent-working-designer-u24 reviews plan.md.

## Related Tickets
- TCK-20261112-EPIC-GITHUB-PROJECT-TICKET-VIEW (parent)
- TCK-20261114-PROJECT-SYNC-INIT-AND-APPLY (P1b, #909)
- TCK-20261114-PROJECT-SYNC-LAYER-EPIC-PRIORITY-TAGS (P1c)

## Related Docs
- docs/guidelines/session_roles/project_sync_dry_run.md

## Related Stored Artifacts
- Study (main checkout): `.claude/handover/drafts/github-project-best-practice-2026-11-14.md`

## Related Code Areas
- tools/sessions/project_client.py, tests/tools/test_project_client.py, registries/session_project.yaml

## Assumptions / Open Questions
- **Simpler-fix check (6698958617).** The other option is to split the P3 first load across several runs by hand. That costs nothing
  in code but makes the operator wait between runs, and any timer run (P3) would hit the limit in the same way. Pacing costs about
  60 lines and 5 tests.
- The exact point costs are unconfirmed in the study. Measure the real cost on the first P3 load.

## Implementation Notes
- **Intended deviation from scope item 2:** a GraphQL `RATE_LIMITED` (primary, hourly budget) stops the run at once instead of waiting; an hourly reset does not fit a 15-min timer run. Designer and planner agreed. Secondary limits (429 / 403 with "rate limit") wait max(60 s, backoff) up to `max_tries`.
- `--include` not used (headers would enter the stdout P1b parses); `retry-after` is honoured only when it shows in gh's text, so in practice 60 s per retry.
- A stop inside one item prints `partial: <ticket id>`; its next-run hand-edit lines come from the stop.

## Test Summary
- 12 new no-network tests in `tests/tools/test_project_client.py` with an injected clock, sleep and runner (no real sleeps): pacing, first mutation undelayed, queries unpaced, `retry-after` honoured and capped, backoff at least 60 s and bounded, primary limit stops at once, plain 403 and other errors not retried, stop after the last try with the token redacted, progress every N steps, partial-item naming, rerun does only the rest, config fallbacks.
- Scoped run: `test_project_client` + `test_session_project_sync` + `test_session_project_sync_second_host` + `test_session_status` = 145 passed (planner reproduced it on fb79c4030).
- AC2 live check: a read-only dry run on the branch head against Project 1 (after the P2 apply) shows only the expected finding and "nothing to do". The `--apply` was **skipped**: with nothing to do it would be a no-op and would not exercise pacing, and the permission classifier blocks it for this seat. The first real paced load is P3b's.

## Files Changed
`tools/sessions/project_client.py`, `tools/sessions/project_sync.py`, `registries/session_project.yaml`, `tests/tools/test_project_client.py`, `docs/guidelines/session_roles/project_sync_dry_run.md`, ticket and staging artifacts, monitoring shards.

## Completion Summary
`ProjectClient` now paces mutations (`write_pacing` in `session_project.yaml`, about 1/s; queries unpaced), stops at once on a primary limit (`RATE_LIMITED`; intended deviation from "wait as told"), waits and retries a secondary limit (429, or 403 saying "rate limit") with a 60 s minimum and bounded backoff, then stops as P1b does. `apply_plan` reports progress every N steps and names a partly-written item (`partial: <ticket id>`). Known limits are in the guide: `retry-after` rarely shows in gh's text, so each retry waits 60 s.
