---
status: active
layer: performance
authority: P1
audience: agent
ticket_id: TCK-20261118-CPU-STEAL-AND-SWAP-COUNTERS-IN-EVERY-TIMING-RECORD
phase: open
date: 2026-11-18
tags: [performance]
---

# TCK-20261118-CPU-STEAL-AND-SWAP-COUNTERS-IN-EVERY-TIMING-RECORD

## Title
Record CPU steal time and the swap counters in every timing record, so host stalls can be told apart from guest contention

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
The owner lifted the perf pause only for this (#715 6985064750, logged by lead-planner, dispatch cited from it). It is one of the two pause-lift conditions in TCK-20261116-TIMING-RUNS-SHARE-THEIR-CPUS-WITH-IDLE-SEATS (steal time and swap counters in every timing record). The frontier spread in tick_cost_growth.md section 9 could not be assigned to a cause because steal time was not recorded; the quiet gate already reads swap before and during a pinned run but does not write the numbers into the record.

## Scope
- Under `tools/perf` only, no `src/` change.
- Read the steal field of `/proc/stat` (aggregate and per allowed CPU) at the start and end of each timed run and store the delta (jiffies and percent of the run's wall time) in the timing record. Reuse `read_cpu_jiffies` / `CpuJiffies` in `tools/perf/quiet_gate.py`; add the steal field to the parsed jiffies if it is not parsed yet.
- Store the `pswpin` / `pswpout` deltas (already taken by the in-run check: `swap_delta`) in the same record, also when they are zero.
- Where a record type is a schema (`src/perf` benchmark record or the rerun record), do not change `src/perf` in this ticket: write the new fields into the tools-side record or the sidecar the tools already emit, and note in the PR which file a later schema change would need. If that is impossible, stop and report instead of editing `src/`.
- A steal share above a documented limit is reported as a warning in the record; it does not void the run (the voiding rule is unchanged).
- Unit tests with fake `/proc/stat` and `/proc/vmstat` readers (the module already takes them as arguments): steal delta, zero swap recorded, unreadable steal field handled without failing the run.
- One short paragraph in `docs/performance/perf_baseline_policy.md` section 2.2 naming the new fields.

## Out of Scope
- Any `src/` change, any timing or heavy run (births GO 1, #715 6983630824, holds the slot: unit tests only), the seats-slice fence, the frontier re-run, new gate thresholds, the five backlog fixes (not lifted).

## Acceptance Criteria
- [ ] A timed run's record carries `cpu_steal` (jiffies, percent) and `swap_in_pages` / `swap_out_pages` deltas.
- [ ] Unit tests pass: `pytest tests/unit/perf tests/perf -m "not slow"` scoped to quiet_gate and rerun_baselines tests.
- [ ] No file outside `tools/perf`, `tests/{perf,unit/perf}`, `docs/performance` changed (`git diff --stat origin/main`).
- [ ] mypy gate clean on touched modules.
- [ ] TCK-20261116-TIMING-RUNS... AC3 can be ticked by citing this ticket.

## Related Tickets
- TCK-20261116-TIMING-RUNS-SHARE-THEIR-CPUS-WITH-IDLE-SEATS (stays open for the fence and the frontier re-run)

## Related Docs
- docs/performance/perf_baseline_policy.md (section 2.2)
- docs/performance/tick_cost_growth.md (sections 9, 10.9)

## Related Stored Artifacts
None.

## Related Code Areas
- tools/perf/quiet_gate.py
- tools/perf/rerun_baselines.py (`_gate_reading`)
- tests/unit/perf, tests/perf (test_quiet_gate.py, test_rerun_baselines.py)

## Assumptions / Open Questions
- Where the timing record is written (rerun_baselines vs capacity_run vs profile_tick): the implementer lists every writer first and covers each, or states which is left out and why.

## Implementation Notes
Approval: #715 6985064750.

## Test Summary

## Files Changed

## Completion Summary
