---
status: active
layer: performance
authority: P1
audience: agent
ticket_id: TCK-20261026-COMBAT-ENGAGEMENT-CONSIDER-PER-PAIR-COST-AFTER-H1
phase: open
date: 2026-10-26
tags: [performance]
---

# TCK-20261026-COMBAT-ENGAGEMENT-CONSIDER-PER-PAIR-COST-AFTER-H1

## Title
Profile and name what is left of combat_engagement's per-pair `_consider` cost after H1 (~1.6 s per tick, 70 % of the tick at 1000 entities)

## Status
OPEN

## Tier
standard

## Type
refactor

## Priority
P2

## Request Summary
H1 indexed the relation lookups behind `is_hostile_compat` (TCK-20261006-COMBAT-ENGAGEMENT-HOSTILITY-PROJECTION-COST-STEP). That cut combat_engagement by 12 to 15 %, but the phase is still 70 to 71 % of the tick.
- Setup: `profile_tick.py --scenario movement --entities 1000 --warmup 2 --ticks 6 --contract pinned --sampler none`. combat_engagement goes from about 1.8 s to about 1.6 s per tick, and the tick is about 2.2 to 2.5 s.
- H1's bisect located the step at 132bf09ca, where the phase went from about 0 to 1.8 s. That is the phase starting to evaluate pairs, not a regression of an existing cost. It touched #190 (1e075b807) and #192 (6dd2ccd12), and the single commit was not named.
- #395 added no per-pair cost.

The numbers are in the H1 ticket's Implementation Notes.

## Scope
1. Profile the remaining combat_engagement time at the H1 setup, with a sampler or cProfile on a pinned box, one process at a time. Name the top costs inside `_consider` and its per-pair callees.
2. Optionally, time 1e075b807 and 6dd2ccd12 against their parents, if that helps attribute the cost.
3. Propose fixes that leave the hashes unchanged, for example per-tick memoisation of pair-invariant reads or pruning the candidate pairs. Each fix must be proven by `paired --neutral` IDENTICAL plus before/after timing. A fix that changes behaviour is a separate, owner-gated decision.

## Out of Scope
- Any change to engagement semantics or outcomes.
- The `collection` phase growth (open, separate).
- The digest and replay cost (T3, F1).

## Acceptance Criteria
- A profile names the components of combat_engagement time that are at least 80 % of it.
- Every landed fix shows `paired --neutral` IDENTICAL on 3 worlds × seed 42, plus before/after combat_engagement ms on alternating pairs.
- If no hash-neutral fix exists, the ticket closes as an investigation with the profile recorded.

## Related Tickets
- TCK-20261006-COMBAT-ENGAGEMENT-HOSTILITY-PROJECTION-COST-STEP (H1)
- #593 (tick-cost investigation, owner option ii)

## Related Docs
- docs/engine/performance_contract.md

## Related Stored Artifacts
- the H1 stored artifacts (after merge)

## Related Code Areas
- src/domains/combat_engagement/ (`_consider` and its per-pair callees)
- src/content_semantics/

## Assumptions / Open Questions
- perf-planner may want this under the perf lane rather than rpg. Ask before dispatching.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
