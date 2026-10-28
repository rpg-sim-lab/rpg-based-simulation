---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261021-A-CROWDED-SERVICE-DOOR-BLOCKS-A-STARVING-SUBJECT
phase: open
date: 2026-10-21
tags: []
---

# TCK-20261021-A-CROWDED-SERVICE-DOOR-BLOCKS-A-STARVING-SUBJECT

## Title
A crowded service door blocks a starving subject 2 tiles away indefinitely (occupancy_violation, falls back to REST)

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
Lane A traced urban_political s44 on step 2 (f9b21b55b, TCK-20261020-A-ESCALATED-NEED-IS-NEVER-REFUSED-FOR-CAPACITY, 2026-10-21; probe tick_log.py, outputs in /mnt/data/scratch-rpg-implementer/paired_en/v3btr/). Merchant 28 dies of STARVATION at t3140, which is a V3.
- proj_hunger_1372 is ACTIVE and current, with the top score (160 at hunger 100), for the whole window t2990-3140. Its objective is hunger_20003, the inn at (39,23). The merchant has 0 gold, so this is a free inn meal.
- The merchant stands at (41-42, 23-24), 2 tiles from the target.
- On 150 of 150 ticks it takes ENTITY_ACT REST (SUCCESS). nav.last_failure_reason is occupancy_violation on every sampled tick.
- Workers 4 and 6, hero 23 and merchants 29, 30 and 12 stand 1-2 tiles away the whole time, so the inn door is crowded. The move toward the inn is refused, and the merchant falls back to REST.
- No threat, stock or money issue.

The designer's ruling (2026-10-21): OUT of family under the user's v1 cutoff (2026-10-21), because the cause is movement and occupancy, not a decision-side cause. It is an owned known red at v1, disclosed as N14, and its rpg_gate_known.yaml entry cites the cutoff.

- CANDIDATE SECOND CASE, not yet confirmed (rpg-designer, 2026-10-29, from the :1610 crowded s46 trace on c32db1a41; /mnt/data/scratch-rpg-implementer/c1610/trace/):
  - crowded_frontier s46, worker 1. Its hunger project is CURRENT for the whole window t3740-4272 at hunger 100 (current in 473 of 533 ticks; fatigue in 60).
  - Ways in reach: INN_MEAL (the free meal on that tree), FORAGE, BUY and WORK_SHIFT.
  - Threat present in 5 of 25 decisions, acting in 1. It never eats and starves at about t4240-4271 (last decision t4239). CORRECTED 2026-10-29: the first report read a nonexistent `alive` attribute and gave t4772.
  - In base it died of COMBAT at about t2000, so a life about 2250 ticks longer exposed this.
  - No :1610 path is involved: the project selection is right.
  - If its execution trace matches this ticket's door shape (an inn in reach, the project current, never served, a refused move or an occupancy fallback), it stays here as a second case. If not, it splits into its own ticket: "a subject whose hunger project is current with a meal in reach starves without eating".
  - First evidence, per tick, new arm only, since base cannot be forced to keep it alive (say so in the report): the action dispatched and its result (move refused or blocked, EAT refused and the reason), position against the inn door, leash, gold, and whether the free meal was offered.
  - Sequenced after lane B's D73 job. Not a :1610 blocker.

## Scope
- Cause first:
  - Is "reach" for a service a single tile or an area? Does an adjacent tile count (divergence 2.78, the walk ending on reach)?
  - Why does a refused move fall back to REST instead of a re-path, a wait-for-gap or another tile?
  - Do the six entities at the door ever clear, and are they queued for the same service?
- The designer rules the shape. Implement, add real-kernel tests (a starving subject at a crowded service door is served within a bound), and measure paired against v1 (seeds 42-46, D76).

## Out of Scope
- Capacity admission (step 2).
- Inn pricing or the free meal (D73, after v1).

## Acceptance Criteria
- The cause is named with evidence.
- No starvation V3 from a service-door occupancy block in the 3 gate worlds × seeds 42-46.
- D76 shows no unexplained drift against v1, and N14 is closed with numbers.

## Related Tickets
- TCK-20261020-A-ESCALATED-NEED-IS-NEVER-REFUSED-FOR-CAPACITY (which surfaced this)
- TCK-20261019-RECORD-BASELINE-V1 (known red, cutoff citation)

## Related Docs
- docs/guidelines/intentional_divergences.md 2.78 (the walk ends on reach) and 2.106 (held move)
- docs/plans/systemic_world/v1_disclosure.md (N14)

## Related Stored Artifacts
- /mnt/data/scratch-rpg-implementer/paired_en/v3btr/ (probe tick_log.py)

## Related Code Areas
- movement and occupancy (MovementCandidateSelector, occupancy checks), service reach

## Assumptions / Open Questions
- Is this specific to inns, or to every service with a single entry tile?

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
