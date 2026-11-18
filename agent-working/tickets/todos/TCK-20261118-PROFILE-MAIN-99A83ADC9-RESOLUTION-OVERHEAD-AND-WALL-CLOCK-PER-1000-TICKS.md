---
status: active
layer: performance
authority: P1
audience: agent
ticket_id: TCK-20261118-PROFILE-MAIN-99A83ADC9-RESOLUTION-OVERHEAD-AND-WALL-CLOCK-PER-1000-TICKS
phase: open
date: 2026-11-18
tags: [performance]
---

# TCK-20261118-PROFILE-MAIN-99A83ADC9-RESOLUTION-OVERHEAD-AND-WALL-CLOCK-PER-1000-TICKS

## Title
Profile main 99a83adc9: attribute resolution_overhead, re-check H1/H2/H3, measure seconds per 1000 ticks, rank fixes

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
The owner lifted the perf pause for this scope only (#715 6967441209: "Lift: profile now"), because engine speed unblocks development. The owner also ordered a temporal-scale audit that needs wall-clock numbers (#715 6967725212). Measurement only; every fix goes back as its own ticket and any src/ work goes through rpg-planner.

## Scope
- Profile origin/main 99a83adc9 on the corpus worlds and on the synthetic scenarios of `docs/performance/tick_cost_growth.md`.
- Break down `resolution_overhead` (`kernel.py:441`) into named call sites. Start from the existing H5 and section 9 result (`fused_strategic_pass`, `nearest_town_tile`, `evaluate_strategic_intent`) and go one level further: the rest of Resolution that is not the pass.
- Re-check H1 (`is_hostile_compat`), H2 (`cooperation/providers.py get_candidates`) and H3 (`EventRecorder.record`) with sampled shares on the current tree.
- Report seconds per 1000 ticks per world and per entity count (the temporal-scale audit input), with a long-run point so tick-count growth shows.
- Return a ranked fix list with expected savings, each tagged legitimate work or waste and with a counterfactual where one is cheap.
- Say which timings are noisy (TCK-20261116-TIMING-RUNS-SHARE-THEIR-CPUS-WITH-IDLE-SEATS applies).

## Out of Scope
- Any change under src/. Any change to determinism, exact replay or the per-tick commit sort (`kernel.py:593`; lead-planner-u24 measured it well under 1 ms).
- New perf tooling (the pause on it holds). Baseline re-records.

## Acceptance Criteria
- Every figure carries its denominator (tick ms, ticks, warmup, contract, seed, host load, sha).
- Resolution is split so that the unnamed remainder is under 10 % of resolution_overhead, or the ticket says why not.
- H1, H2, H3 each get a verdict (gone, reduced, back) with the share.
- A table of s/1000 ticks by world and entity count, each marked quiet or noisy.
- A ranked list in `docs/performance/tick_cost_growth.md` (new section 10), each item ready to become a ticket.
- Run data cleaned by id.

## Related Tickets
TCK-20261014-PERF-TICK-COST-GROWTH-INVESTIGATION, TCK-20261015-PERF-RESOLUTION-OVERHEAD-ATTRIBUTION (already attributed 87-99 % of resolution_overhead to `fused_strategic_pass`), TCK-20261022-PERF-EVENT-RECORDER-AND-EVENT-CONSTRUCTION-REMEASURE, TCK-20261115-PER-PHASE-TICK-COST-AFTER-THE-HOSTILITY-AND-COOPERATION-FIXES, TCK-20261116-TIMING-RUNS-SHARE-THEIR-CPUS-WITH-IDLE-SEATS.

## Related Docs
docs/performance/tick_cost_growth.md (sections 3, 7, 9), docs/engine/performance_contract.md.

## Related Stored Artifacts
None yet.

## Related Code Areas
tools/perf/profile_tick.py (existing, unchanged), src/engine/kernel.py, src/engine/pipeline.py.

## Assumptions / Open Questions
- Lead's message says resolution_overhead was "left unattributed in TCK-20261014". TCK-20261015 and section 9 already attribute it to `fused_strategic_pass` (19-26 % of the tick). The new work is the finer breakdown and the re-check on 99a83adc9, not a first attribution.
- Only 10 src/ commits separate db6b4579d (section 9) from 99a83adc9, none in the perf-relevant phases, so a delta check is cheap before deciding how many runs repeat.

## Implementation Notes
Run plan sent to lead-planner for a GO per run.

## Test Summary
Not applicable (measurement).

## Files Changed
## Completion Summary
