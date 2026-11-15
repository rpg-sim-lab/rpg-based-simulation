---
status: active
layer: performance
authority: P1
audience: agent
ticket_id: TCK-20261115-PER-PHASE-TICK-COST-AFTER-THE-HOSTILITY-AND-COOPERATION-FIXES
phase: open
date: 2026-11-15
tags: [performance]
---

# TCK-20261115-PER-PHASE-TICK-COST-AFTER-THE-HOSTILITY-AND-COOPERATION-FIXES

## Title
Re-measure per-phase tick cost on a quiet host after the hostility index (H1) and cooperation candidate (H2) fixes

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
Child 1 (stage 0) of `TCK-20261109-EPIC-NEXT-GENERATION-ENGINE`: "re-measure after H1 (#751) and H2 (#771) on a quiet host; per-phase ms with denominators; Resolution profile incl. `fused_strategic_pass`. Measurement only." The epic left it to be cut by perf-planner.

The owner exempted this item from the perf pause (#715 6556861718), and only this measurement; the pause stays for everything else. Record: #715 6889952914; the owner's words: 6889947724. Relayed by lead-planner on 2026-11-15.

The numbers today are PROVISIONAL and come from a loaded host before both fixes (`docs/performance/tick_cost_growth.md`; feasibility review §3). H1 merged as `35e80fb56` (#751), H2 as `dc059c49e` (#771). The next-generation engine's contract spec (child 4) and its stage choices read these results.

## Scope
- On origin/main at a named sha that contains both fixes: per-phase ms for each kernel phase on the 3 gate worlds (`frontier_living_world`, `urban_political`, `crowded_frontier`; `tools/rpg_measure/paired.py:45`) at seed 42.
- Each figure carries its denominator: the share of the whole tick, plus the tick's own ms, ticks measured, warmup and contract.
- A Resolution profile that names `fused_strategic_pass` (`src/engine/pipeline.py:394`) and its share of Resolution and of the tick.
  - Check first whether the `final_integrity` timer fix of `tick_cost_growth.md` H5 is on main. `pipeline.py` now has a t0..t8 breakdown, which suggests it is. If it is, read the pass from the kernel's own costs. If not, use the process-local wrapper of the H5 attribution (no `src/` edit).
- No new perf tooling in `tools/` and no `src/` edit. The runner question (pinned, #918) is under Open Questions.
- Quiet host under `docs/performance/perf_baseline_policy.md` §2.2 (`tools/perf/quiet_gate.py`), on the heavy slot lead-planner grants, one run at a time, under the 3G cap.
- Write the results into `docs/performance/tick_cost_growth.md` as a dated section with the sha, host and gate readings, and mark the older figures as superseded where these replace them.

## Out of Scope
- Any fix, in `src/` or elsewhere. A finding goes to the code's owner through lead-planner.
- A baseline record or promotion; v0002; the 10k probe; Collection's growth attribution (`TCK-20261026-PERF-COLLECTION-PHASE-GROWTH-ATTRIBUTION`, still paused).
- The world farm (child 3) and the parallel executor (child 5).

## Acceptance Criteria
- [ ] Per-phase ms on all 3 gate worlds at seed 42, each with its denominator, the sha, warmup and measured ticks, contract and the quiet-gate readings.
- [ ] A Resolution profile naming `fused_strategic_pass` with its share of Resolution and of the tick, plus the method used (kernel costs or wrapper).
- [ ] At least 3 timed runs per world, with the spread stated. A result outside the quiet window, or with a spread too wide to read, is marked INCONCLUSIVE, not reported as a figure.
- [ ] `tick_cost_growth.md` updated; the epic's child 1 row can cite this ticket.
- [ ] Run data cleaned by id.

## Related Tickets
- TCK-20261109-EPIC-NEXT-GENERATION-ENGINE (parent, child 1)
- TCK-20261109-NEXT-GENERATION-ENGINE-CONTRACT-SPEC (reads this result)
- TCK-20261026-PERF-COLLECTION-PHASE-GROWTH-ATTRIBUTION (paused; not covered by the exemption)
- TCK-20261101-FUSED-STRATEGIC-PASS-RESTRUCTURE
- TCK-20261101-PERF-BENCH-KNOWN-REDS-PARKED-DURING-THE-PAUSE (where the pause and this exemption are recorded)

## Related Docs
- docs/plans/architecture/next_generation_engine_feasibility_review.md (§3)
- docs/plans/architecture/engine_execution_modes_proposal.md (§2, §3)
- docs/performance/tick_cost_growth.md
- docs/performance/perf_baseline_policy.md (§2.2)
- docs/engine/performance_contract.md

## Related Stored Artifacts
None.

## Related Code Areas
- tools/perf/profile_tick.py
- tools/perf/quiet_gate.py
- src/engine/pipeline.py (read only)

## Assumptions / Open Questions
- **Open (asked of lead-planner 2026-11-15): the runner.** #918 makes measurement evidence come from the pinned runner (`pinned_runner.require_pinned`: pinned governor, `LocalSequentialExecutor`, budget >= 1e9, audit mode, no frame pacing). `tools/perf/profile_tick.py`'s contracts never meet that: its `pinned` contract fixes the governor only, keeps audit mode off, and leaves the executor and budget at the profile's. So "existing tools only" and "pinned" conflict. Proposed: a staging-artifact probe on `rpg_gate_run.build_kernel` that reads the kernel's own per-phase costs, plus one py-spy run over it for the Resolution profile, under the same conditions lead set for the packet-cost probe. The per-phase numbers are then those of the sequential executor, which is what the serial next-gen stages compare against; that caveat is stated with the result.
- Ticks and warmup are fixed in the run spec sent to lead-planner before the slot, not here.
- Host: the ubuntu VM has had host-side vCPU stalls. A quiet-gate pass does not rule them out, so the spread check carries that risk.
- Whether `tick_cost_growth.md`'s older figures stay comparable: measurements from before the 10-25 venv sync are not comparable (handover), so only the post-fix numbers are reported as current.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
