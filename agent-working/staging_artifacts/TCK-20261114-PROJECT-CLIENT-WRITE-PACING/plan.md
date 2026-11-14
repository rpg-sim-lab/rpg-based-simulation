---
status: active
layer: ticket
authority: P2
audience: agent
phase: in_progress
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

**Rate limit (item 2).** `graphql()` is split into `_send` (one `gh api graphql` call, returns rc/stdout/stderr) and the loop around it. A call is "rate limited" when the combined stdout+stderr+error text shows `HTTP 429`, `HTTP 403` with "rate limit" (a bare 403 permission error is NOT retried), a GraphQL error `type: RATE_LIMITED`, or "secondary rate limit". Wait time: a `retry-after: N` header line if present in the text, else `min(backoff_cap_s, backoff_base_s * 2**attempt)`; always capped at `backoff_cap_s`. After `max_tries` attempts, raise `ProjectError("rate limited: gave up after N tries ...")`, which `apply_plan` already turns into "STOPPED, k not done" exactly as P1b. Applies to queries and mutations alike (a rejected mutation was not applied, so a retry is safe). Other errors are not retried: P1b behaviour is unchanged.
Open point for the designer: `gh api` does not print response headers without `--include`, so `retry-after` is honoured only when it shows in gh's error text; otherwise exponential backoff applies. I do NOT add `--include` (it changes the stdout format that P1b reads). Alternative if you want exact header handling: add `--include` and parse the header block; larger change, more risk to AC2.

**Progress (item 3).** `apply_plan(..., progress=None, every=25)`: after each `every` completed steps call `progress(f"progress: {n}/{total} steps done")`. `project_sync` passes a function printing to stderr (stdout stays the plan + the final "applied N step(s)" line unchanged).

**Rerun (item 4).** No new code: a stopped run leaves its Sync hash for last on each item (existing VALUE_ORDER), so the next dry run replans only what is unfinished. A test proves this against the existing plan builder shape (a Fake that stops mid-run, then a second `apply_plan` over a recomputed plan does only the rest).

**Docs.** `docs/guidelines/session_roles/project_sync_dry_run.md`: one short paragraph (pacing, rate-limit stop, config keys).

## Scope guards
No lanes, Domain, fetch, heartbeat, timer, parallel writes, delete mutation. `_guard` in `project_sync.py` unchanged. Token handling unchanged (`_redact` on every new message).

## AC map
AC1 -> items 1-5 + tests. AC2 -> live dry run (empty diff vs reference) and `--apply` behave as P1b (owner rule needed). AC3 -> this plan reviewed by agent-working-designer-u24 before code.
