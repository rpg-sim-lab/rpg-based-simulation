---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20261110-DELIVERY-COST-REF-MODE-READS-NO-BRANCH-SHARDS
phase: done
date: 2026-11-10
tags: [agent-monitoring, delivery, data-quality]
---

# TCK-20261110-DELIVERY-COST-REF-MODE-READS-NO-BRANCH-SHARDS

## Title
`delivery_cost_measurement.py --ref` reads only a week's canonical `tools.jsonl`, so an unclosed week's branch shards count as 0 gh calls

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
Found by lead-planner-u24 on 2026-11-10 while re-checking the DELIVERY-COST watchlist row:
`delivery_cost_measurement.py --ref origin/main --since-week 2026-W44 --through-week 2026-W44` gives 0 gh calls and 0
`gh pr create`; without `--ref` the same window gives 492 and 1. The README tells readers to use `--ref` for any
before/after datapoint, so the pinned reading is the wrong one.

Cause (agent-working-planner-u24, read from origin/main): `--ref` goes through
`tools/agent-monitoring/bash_command_mix.py::load_tools_rows_from_ref`, which keeps only paths ending in
`/<source>.jsonl` at `data/<week>/` depth: the canonical, closed-week file. A week that hasn't been closed holds only
per-branch `<branch>.tools.jsonl` shards (origin/main W44 has many, no `tools.jsonl`), so the ref loader sees nothing. The
working-tree path uses the shared `monitoring_shard_paths.shard_paths()` resolver, which includes branch shards.

## Scope
1. `load_tools_rows_from_ref` also reads `data/<week>/<branch>.<source>.jsonl` shards in the ref's tree, matching what
   `shard_paths()` selects on disk (same naming rule; reuse its pattern if it exposes one).
2. Full-row identity de-dup across a week's canonical and branch files, as the retro and week-close readers do, so a
   row present in both counts once.
3. Tests: a ref tree with only branch shards for a week counts their gh calls; a week with canonical plus an overlapping
   branch shard counts a duplicated row once; a closed week (canonical only) is unchanged.

## Out of Scope
- The PR attribution and subject traceability parts of delivery_cost_measurement.
- Closing weeks W44-W46 (week-close is its own process).
- The README DELIVERY-COST row text (corrected in TCK-20261110-RETRO-READERS-SELECT-TOOL-ROWS-BY-TS's PR).

## Acceptance Criteria
1. `--ref` and working-tree readings of the same unclosed week agree on gh-call count when the ref holds the same shards.
2. The three tests in Scope 3 pass; existing bash_command_mix and delivery-cost tests pass unchanged.
3. Scoped tests only; owner load rule (no pytest -n>1, no broad suites while lane C measures).

## Related Tickets
- TCK-20260924-DELIVERY-COST-MEASUREMENT (done; the tool)
- TCK-20261110-RETRO-READERS-SELECT-TOOL-ROWS-BY-TS (README correction)

## Related Docs
- docs/agent-monitoring/README.md (watchlist, DELIVERY-COST row)

## Related Stored Artifacts
- none

## Related Code Areas
- tools/agent-monitoring/bash_command_mix.py (`load_tools_rows_from_ref`), tools/agent-monitoring/monitoring_shard_paths.py,
  tools/delivery/delivery_cost_measurement.py, tests/tools/

## Assumptions / Open Questions
- Simpler-fix check: widening the ref loader's filename match is the smallest fix; the alternative (closing every week
  before measuring) costs a week-close per reading and leaves open weeks unmeasurable. No measurement runs.
- Other callers of `load_tools_rows_from_ref` (bash-mix reports) gain branch-shard rows too; that is the same fix for them.

## Implementation Notes
bash_command_mix.py: `load_tools_rows_from_ref` now matches the bare `<source>.jsonl` and every `<id>.<source>.jsonl` at data/<week>/ depth (the shard_paths() naming rule). New `dedupe_rows()` (full-row identity) is applied in BOTH `load_tools_rows` and the ref loader, so the working-tree and --ref readings agree. Measured W44 with the fix: working tree 12,778 rows / 489 gh calls / 1 `gh pr create` (raw 12,821 / 492 before de-dup: 43 byte-identical duplicate rows, 3 of them gh calls); `--ref origin/main` (cefa99b07) 12,778 / 489 / 1. Before the fix --ref gave 0 / 0.

## Test Summary
4 new tests in tests/tools/test_bash_command_mix.py (branch shards only; canonical plus overlapping branch shard counts once; closed week unchanged; ref and working tree agree). test_bash_command_mix and test_delivery_cost_measurement: 50 passed, scoped, no -n.

## Files Changed
tools/agent-monitoring/bash_command_mix.py; tests/tools/test_bash_command_mix.py

## Completion Summary