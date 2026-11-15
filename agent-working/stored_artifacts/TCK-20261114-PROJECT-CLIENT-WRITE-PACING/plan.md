---
status: historical
layer: ticket
authority: P2
audience: agent
phase: done
ticket_id: TCK-20261114-PROJECT-CLIENT-WRITE-PACING
artifact_type: plan
tags: [planning, delivery]
---

# Plan

Order: (1) config keys; (2) pacing + retry in `ProjectClient`; (3) progress in `apply_plan` and `project_sync`; (4) tests; (5) docs; (6) live check (dry run vs the planner's reference, then `--apply` only after the owner's permission rule is in, after the pending P2 apply).

## Design
**Config** (`registries/session_project.yaml`, new `write_pacing` block; `project_sync.DEFAULTS` gets the same keys so a missing block means the defaults):
`min_interval_s: 1.0`, `progress_every: 25`, `max_tries: 5`, `backoff_base_s: 2.0`, `backoff_cap_s: 120.0`. A `Pacing` frozen dataclass in `project_client.py` holds them; `ProjectClient(..., pacing=Pacing(), clock=time.monotonic, sleep=time.sleep)`. `_client()` in `project_sync.py` builds `Pacing` from config (bad or non-positive values fall back to the default).

**Pacing (item 1).** Only `_mutate` waits: before a mutation, sleep until `min_interval_s` has passed since the previous mutation started. `graphql()` called for queries is never paced. First mutation is not delayed. The wait uses the injected clock/sleep.

**Rate limit (item 2), amended after the designer's review (A).** `graphql()` is split into `_send` (one `gh api graphql` call) and the loop around it. Two kinds:
- *Primary* limit = a GraphQL error with `type: RATE_LIMITED` (hourly points budget). Waiting seconds cannot help: **no retry**, stop at the first one with `ProjectError("primary rate limit: rerun after the hourly reset")`; `apply_plan` turns it into P1b's STOPPED path.
- *Secondary* limit = HTTP 429, or HTTP 403 whose text says "rate limit" / "secondary rate limit". Wait = `retry-after: N` if it shows in gh's error text, else `min(backoff_cap_s, max(secondary_min_wait_s, backoff_base_s * 2**k))` (secondary_min_wait_s 60: GitHub's guidance); a retry-after is also capped at `backoff_cap_s`. After `max_tries` attempts raise `ProjectError("secondary rate limit: gave up after N tries")` (about 7 min worst case at cap 120). A bare 403 (permission) and every other error are not retried: P1b behaviour is unchanged.
- Applies to queries and mutations alike (a rejected mutation was not applied).
- `retry-after` is honoured only when it shows up in gh's error text. `--include` is NOT added (headers would enter the stdout P1b parses; AC2 risk, little gain). Documented in the guide.
New config key: `secondary_min_wait_s: 60.0`.

**Pacing and retry share one clock (C).** The min-interval wait is computed from the injected clock against the previous mutation's start time (updated on every attempt, including retries), never a fixed 1 s: after a backoff sleep the next mutation adds no extra wait and nothing fires early.

**A stop mid-item (B).** `Sync hash` is written last, so an item stopped partway holds new field values with the old hash, and the next run's `hand_edits()` would print false "hand edit" lines for it. Chosen fix (no extra mutations, no change to `build_plan`): the STOPPED output also prints `partial: <ticket id>` for the item the stop fell in (ticket id taken from the failing step's description), and the doc says the next run's hand-edit lines for that id come from the stop, not a person; the rerun overwrites them. (A `build_plan` Source-based suppression was rejected by the designer: Source is written just before the hash, so it would catch only a stop between those two writes.)

**Progress (item 3).** `apply_plan(..., progress=None, every=25)`: after each `every` completed steps call `progress(f"progress: {n}/{total} steps done")`. `project_sync` passes a function printing to stderr (stdout stays the plan + the final "applied N step(s)" line unchanged).

**Rerun (item 4).** No new code: a stopped run leaves its Sync hash for last on each item (existing VALUE_ORDER), so the next dry run replans only what is unfinished. A test proves this against the existing plan builder shape (a Fake that stops mid-run, then a second `apply_plan` over a recomputed plan does only the rest).

**Docs.** `docs/guidelines/session_roles/project_sync_dry_run.md`: one short paragraph (pacing, rate-limit stop, config keys).

## Scope guards
No lanes, Domain, fetch, heartbeat, timer, parallel writes, delete mutation. `_guard` in `project_sync.py` unchanged. Token handling unchanged (`_redact` on every new message).

## AC map
AC1 -> items 1-5 + tests. AC2 -> live dry run (empty diff vs reference) and `--apply` behave as P1b (owner rule needed). AC3 -> this plan reviewed by agent-working-designer-u24 before code.
