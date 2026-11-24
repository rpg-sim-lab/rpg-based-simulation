---
status: active
layer: performance
authority: P1
audience: agent
ticket_id: TCK-20261120-COMBAT-ENGAGEMENT-COST-GAP-AT-THE-BIRTHS-FINAL-HEAD
phase: open
date: 2026-11-20
tags: [performance]
---

# TCK-20261120-COMBAT-ENGAGEMENT-COST-GAP-AT-THE-BIRTHS-FINAL-HEAD

## Title
combat_engagement costs more per entity-tick at the births final head than on main, in frontier_living_world: confirm the cause and decide the fix

## Status
OPEN

## Tier
standard

## Type
repair

## Priority
P2

## Request Summary
Filed from a finding by rpg-planner-ubuntu. rpg-designer (u24) ruled that a cost flag still present at births' final head "becomes a perf ticket naming births as the cause" (births rulings section 40, `agent-working/stored_artifacts/TCK-20261109-M1-BASIC-WILD-BIRTHS-FOR-EVERY-LIVING-KIND/owner_births_scope_and_rpg_designer_6a_extinction_rulings_2026-11-18.md`, on seat branch `rpg-ubuntu-planner-filings`; I have not read that file). The births PR will carry a limits line naming this ticket id. Perf did not take these measurements; the numbers below are the births seat's, read from its raw file.

## Evidence (births_run cost arms, `frontier_living_world`, seed 42, 5000 ticks, recording OFF, head vs main)
- GO 1 evidence block, head `c1183bb24`: combat_engagement gap +0.371 against a head-vs-head noise of 0.023 (relayed by rpg-planner-ubuntu; not re-read by perf).
- Re-check at the final head `d3401ba43` (main base `ae2f837cb`, #715 GO 7016036832). Read from `/data/vboxuser/births-runs/recheck-d3401ba43/cell/summary.json`, `cost`: combat_engagement gap **0.358** against head-vs-head noise **0.259**. The two head runs' medians are 3.76 ms and 4.73 ms, and the two main runs start at 2.83 ms; so the gap is outside the noise band, but by a small margin (0.358 against 0.259), and the noise band is 11 times wider than in the GO 1 block. Other stages in the same re-check are inside their bands: cooperation 0.167 against 0.212, economy 0.150 against 0.267, governance_ecology 0.196 against 0.261 (relayed).
- Host per the summary: loadavg1 max 2.57 / 4.59 (head runs) and 2.14 / 3.58 (main), MemAvailable min about 3.3 GB, steal 0 jiffies in all four runs, 3G scope on cpus 4-5.

## Likely mechanism (unverified, from rpg-planner-ubuntu)
Newborns and pregnancies add bodies and pairs to the combat_engagement scan; births adds 10 bodies in this cell. Perf has not checked this. Section 10 of `docs/performance/tick_cost_growth.md` shows `combat_engagement` is already 14 to 20 % of the tick on the gate worlds, so a per-body or per-pair cost increase would show here first.

## Scope
1. Decide whether the gap is a real per-entity cost change or the effect of more entities: compare `ms_per_entity_tick` for head and main (the summary has it per run: head 0.135 and 0.159, main 0.126 at the first run; read the rest) and the body count over the run in each arm. If the per-entity cost is flat and the body count rose, the gap is the births population and not a regression.
2. If it is a per-entity rise, py-spy `combat_engagement` at the births final head against main (same command, seed and host conditions, a loaded host with pinned cpus 4-5, steal and swap recorded) and name the callee.
3. Report the finding to rpg-planner-ubuntu and the births seat; the fix, if any, is a `src/` change routed through rpg-planner and is not part of this ticket.

## Out of Scope
Any `src/` change; any claim that births is wrong; reruns of the births evidence block (births owns it).

## Acceptance Criteria
- [ ] The head and main per-entity cost and body counts are tabulated from the births raw file.
- [ ] The gap is classified: population effect, or per-entity cost rise.
- [ ] If a per-entity rise: the py-spy callee is named with shares, and the result is sent to rpg-planner.
- [ ] The births PR limits line cites this ticket id, or the ticket is closed as no regression.

## Related Tickets
- TCK-20261109-M1-BASIC-WILD-BIRTHS-FOR-EVERY-LIVING-KIND
- TCK-20261026-COMBAT-ENGAGEMENT-CONSIDER-PER-PAIR-COST-AFTER-H1 (older, paused)

## Related Docs
- docs/performance/tick_cost_growth.md (sections 10.1, 10.2)

## Related Stored Artifacts
None in this branch. The births rulings file is on `rpg-ubuntu-planner-filings`.

## Related Code Areas
- combat_engagement phase (`src/domains/combat_engagement/`), read-only for this ticket

## Assumptions / Open Questions
- Whether `ms_per_entity_tick` already divides by the changing body count in the head arm (to be read from births' cost script).
- The paused status of timing and src-adjacent perf work: this ticket needs a go per run and, for any `src/` read beyond reading, the owner's lift.

## Implementation Notes
Not started. Waits on a go for any run; step 1 is a read of existing data and needs no run.

## Test Summary

## Files Changed

## Completion Summary

## Durable state, lifecycle and clocks
N/A: measurement and classification only.
