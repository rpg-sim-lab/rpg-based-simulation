---
status: active
layer: performance
authority: P1
audience: agent
ticket_id: TCK-20261116-TIMING-RUNS-SHARE-THEIR-CPUS-WITH-IDLE-SEATS
phase: open
date: 2026-11-16
tags: [performance]
---

# TCK-20261116-TIMING-RUNS-SHARE-THEIR-CPUS-WITH-IDLE-SEATS

## Title
Proposal: keep the Claude seat processes off CPUs 4-5 while timing runs use them on the ubuntu host

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
The owner kept the perf pause and made a cleaner timing host a condition before it lifts: seats kept off CPUs 4-5 (#715 6911604017, relayed by lead-planner on 2026-11-16). This ticket is the proposal for the owner. It is a host setting, so the owner chooses an option; nothing here is applied by perf.

Today timing runs go to CPUs 4-5 (`systemd-run --user --scope ... taskset -c 4-5`), and only `system.slice` is set to CPUs 0-3. The Claude seat processes (planners, implementers, designers) can be scheduled on 4-5, and lead-planner saw them there at about 0.5 to 2 % each. The quiet gate (`perf_baseline_policy.md` §2.2) catches bursts over 10 % before a run starts, but not during it.

## Evidence (stage 0, `TCK-20261115-PER-PHASE-TICK-COST-AFTER-THE-HOSTILITY-AND-COOPERATION-FIXES`, origin/main `db6b4579d`)
- `frontier_living_world`, 6 timed runs, same spec: mean tick 57.55, 34.61, 42.65 ms, then 39.75, 43.92, 37.16 ms. Spread 54 % (runs 1-3), 17 % (runs 4-6), 56 % (all six). INCONCLUSIVE; no run voided.
- `urban_political` and `crowded_frontier` on the same slot: 6.5 % and 7.8 %.
- Swap ruled out for runs 4-6: `pswpout` unchanged, `pswpin` +13, +4, +0 pages, `vmstat` si/so 0/0 before and after each run. Every gate passed with CPUs 4-5 under 10 % busy and swap in+out 0 pages.
- During the same slot, an RPG seat loaded CPU 4 to about 98 % for several minutes (gate failed 3 to 7 times before two runs; the owner's RPG-first rule, #715 6911759453, means perf waits).
- Full readings: `agent-working/staging_artifacts/TCK-20261115-PER-PHASE-TICK-COST-AFTER-THE-HOSTILITY-AND-COOPERATION-FIXES/evidence.md`.

**What the evidence does not show.** It does not prove that seat contention caused the frontier spread: the gate read CPUs 4-5 as quiet before each run, and steal time was not recorded. The fence below removes one known source of noise; it is not a demonstrated fix for this spread.

## Options for the owner
- **A. A seats slice (recommended for the long term).** The seat launcher starts each Claude session in its own user slice with `AllowedCPUs=0-3` (for example `systemd-run --user --slice=seats.slice` with `systemctl --user set-property seats.slice AllowedCPUs=0-3`), and timing scopes keep `taskset -c 4-5`. The fence then holds for every seat and its child processes, including tests a seat starts. Cost: a launcher change (owner of `tools/sessions`), and seats lose two of six CPUs at all times. Setting `user.slice` itself to 0-3 does not work: the timing scopes run under the same user manager and would be fenced off 4-5 too.
- **B. A fence for each timing window only.** Before a slot, lead-planner (or the owner) moves running seat processes to 0-3 (`taskset -a -c -p 0-3 <pid>`), then moves them back afterwards. No config change, reversible; a seat started during the window is not fenced, and it needs a step per slot.
- **C. Time somewhere else.** Run timing on a host or runner of the certification hardware class (`docs/engine/contracts/certification_contract.md` §3), and keep ubuntu for behaviour runs. Cleanest numbers; needs a host.
- **D. No change.** Keep the gate and the spread rule; a world over about 10 % is reported INCONCLUSIVE, as frontier was.

Recommendation: A, with B as a stopgap until A lands. Either way, add steal time (`/proc/stat` steal or `vmstat` st) and the swap counters to every timing run's record (perf, no host change), so host stalls can be told apart from guest contention.

## What this does not fix
- **Swap pressure**: swap held 3.9 of 8 GB. `MemorySwapMax=0` keeps the timed process off swap, but not reclaim by the rest of the guest.
- **Host-side vCPU stalls**: the ubuntu VM has shown idle vCPUs stuck 21 to 163 s in earlier journals. A guest-side CPU fence cannot reach the hypervisor. Candidate cause for the frontier spread, unverified.
- RPG work keeps priority under contention (#715 6911759453), so slots still wait for RPG seats whatever the fence.

## Scope
- The owner picks an option. Then the chosen change is routed by lead-planner to the owner of the launcher or the host. Perf adds steal time and swap counters to timing records (a perf tooling change, which waits for the pause to lift unless the owner releases it).
- After the change: re-run `frontier_living_world`'s 3 timed runs (stage 0 spec) and report whether the spread falls under about 10 %.

## Out of Scope
- Any change to seats, the launcher or the host made by perf.
- Swap sizing and the VM's host-side configuration.

## Acceptance Criteria
- [x] The owner's choice recorded on #715 and cited here (#715 6917238009).
- [x] The chosen fence in place (or option D recorded): option D recorded for now; option A becomes a condition of lifting the pause.
- [ ] Steal time and swap counters in timing records, or a reason they are not. (A lift condition.)
- [ ] Frontier's 3 timed runs re-run after the change, with the spread stated. (After A is in place.)

## Related Tickets
- TCK-20261115-PER-PHASE-TICK-COST-AFTER-THE-HOSTILITY-AND-COOPERATION-FIXES (evidence)
- TCK-20261115-WHAT-A-WORKER-CHUNK-COSTS-TO-ENCODE-AND-SHIP (ran on the same slot)
- TCK-20261101-PERF-BENCH-KNOWN-REDS-PARKED-DURING-THE-PAUSE (where the pause is recorded)

## Related Docs
- docs/performance/perf_baseline_policy.md (§2.2)
- docs/performance/tick_cost_growth.md (§9)
- docs/engine/performance_contract.md

## Related Stored Artifacts
None yet.

## Related Code Areas
- tools/perf/quiet_gate.py
- tools/perf/rerun_baselines.py (`_gate_reading`)

## Assumptions / Open Questions
- Which seat processes the launcher starts, and whether all of them come from one launcher: to be checked by the launcher's owner for option A.
- Whether two CPUs are enough for the seats at peak; RPG work has priority, so option A trades seat speed for timing quality.

## Implementation Notes
- 2026-11-16: **owner decision (#715 6917238009, relayed by lead-planner): "D now, A when the pause lifts".** No host change now: the quiet gate and the spread rule stand, and a world whose spread is over about 10 % is reported INCONCLUSIVE. Two items become conditions of lifting the perf pause, refining the condition in #715 6911604017:
  1. option A, the seats-slice fence (Claude seats limited to CPUs 0-3, timing scopes on 4-5), routed by lead-planner to the launcher's owner when the lift is prepared;
  2. steal time and swap counters in every timing record (perf tooling, done as part of the lift).
  Not chosen: A now, B per window, C another host.
- This ticket stays OPEN as the lift checklist for these two items and the frontier re-run (AC3, AC4). It closes when the pause lifts and those are done, not in the next perf PR.

## Test Summary

## Files Changed

## Completion Summary
