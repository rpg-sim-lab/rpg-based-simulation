---
status: historical
layer: performance
authority: P1
audience: agent
ticket_id: TCK-20261119-RERUN-OF-R1-R4-AND-MIXED-400-PYSPY-ON-CPUS-4-5
phase: done
date: 2026-11-19
tags: [performance]
---

# TCK-20261119-RERUN-OF-R1-R4-AND-MIXED-400-PYSPY-ON-CPUS-4-5

## Title
Rerun of R1 and R4 and the py-spy before-profiles, pinned to cpus 4-5, recorded in tick_cost_growth.md

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P2

## Request Summary
Section 10.8 of `docs/performance/tick_cost_growth.md` owed a rerun of R1 and R4 and the py-spy runs (the SOLO cooperation ticket's before-profile). Lead released the slot with a per-run go (#715 6989182066, run 2 to 4 goes recorded on #715). Measurement only, no `src/` change.

## Scope
Add sections 10.1b, 10.5b and an updated 10.8 to `tick_cost_growth.md`, and the evidence paragraph to TCK-20261116-TIMING-RUNS-SHARE-THEIR-CPUS-WITH-IDLE-SEATS. Label: loaded host, pinned cpus 4-5, steal/swap recorded.

## Out of Scope
Any `src/` change; any quiet-host claim; a baseline record.

## Acceptance Criteria
- [x] 10.1b and 10.5b carry the rerun numbers with spreads, steal and swap.
- [x] 10.8 records the mixed-400 and gate-world py-spy results and the providers.py:111 cross-reference to the faction-hostility extraction.
- [x] The urban_political swap-touched flag is stated with its unverified cause.
- [x] The TIMING-RUNS ticket has the pinning evidence.

## Related Tickets
- TCK-20261116-TIMING-RUNS-SHARE-THEIR-CPUS-WITH-IDLE-SEATS
- TCK-20261118-PROFILE-MAIN-99A83ADC9-RESOLUTION-OVERHEAD-AND-WALL-CLOCK-PER-1000-TICKS

## Related Docs
- docs/performance/tick_cost_growth.md

## Related Stored Artifacts
None. Raw data: /data/vboxuser/perf_runs/r5, r6, r6b, r7.

## Related Code Areas
None (measurement only).

## Assumptions / Open Questions
None.

## Implementation Notes
Runs: r5 mixed-400 and gate-world py-spy on `c505357b3`; r6, r6b, r7 on `99a83adc9`.

## Test Summary
Not applicable (docs only).

## Files Changed
docs/performance/tick_cost_growth.md; agent-working/tickets/todos/TCK-20261116-TIMING-RUNS-SHARE-THEIR-CPUS-WITH-IDLE-SEATS.md

## Completion Summary
Reran R1 and R4 pinned to cpus 4-5 with steal and swap recorded; recorded the py-spy before-profile for the SOLO ticket.

## Durable state, lifecycle and clocks
N/A: docs-only measurement record; no durable engine state changes.
