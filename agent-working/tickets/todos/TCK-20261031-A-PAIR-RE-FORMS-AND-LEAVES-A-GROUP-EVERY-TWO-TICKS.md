---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20261031-A-PAIR-RE-FORMS-AND-LEAVES-A-GROUP-EVERY-TWO-TICKS
phase: open
date: 2026-10-31
tags: [cooperation, social]
---

# TCK-20261031-A-PAIR-RE-FORMS-AND-LEAVES-A-GROUP-EVERY-TWO-TICKS

## Title
A pair of entities forms a group and is expelled from it about every 2 ticks. Once group ids stop repeating, each cycle leaves a retained dissolved record, so the group store grows while the churn lasts. Count it first; rpg-designer rules on the rule.

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
Found while verifying TCK-20261031-A-NEW-GROUP-ID-OVERWRITES-A-LIVE-GROUP. rpg-planner agreed this separate ticket, counts first, with rpg-designer to rule (Ruling 2, in that ticket's staging `rpg_designer_ruling_2026-10-31.md`). A retention or bound rule for dissolved records is a lifecycle rule for the designer, not for the group-id PR.

Behaviour finding, on BOTH trees: on lifecycle_full_coverage_world, seed 42, 200t, entities (37,38) form a group and are expelled about every 2 ticks (read in the event lines at t130-140; the implementer reports it from t102). Trees: 6fdfdf555 and branch rpg-ubuntu-group-id-alloc-impl. Data: /data/vboxuser/Work/groups_base/out/tr_{base,branch}.jsonl (scratch; copy what the close needs into staging).

Measured group store on that scenario: at t199, base 20 records (20 dissolved), branch 54 (53 dissolved). Branch 32 records at t158, 54 at t199, about 0.5 per tick while the churn runs. About 950 by 2000t is an extrapolation from one 200t scenario, not a measurement.

Later measurement, s42, 2000t, 3 worlds: formations go from 225 to 571, 185 to 1035 and 96 to 839 (crowded_frontier, frontier_living_world, urban_political), whole tick +5.1%, +35.6%, +14.6%, which holds the group-id PR. So the old id defect may have been suppressing this churn; that reading is untraced. The profiled runs of the group-id ticket test it.

Not known: why the group ends each cycle (the dissolve and expel conditions at `src/systems/world_systems/groups.py` l.90-175 have not been traced for this pair), why it re-forms, and how many pairs and worlds show this.

## Scope
1. Counts, before any fix shape: rpg-designer's counts 1-3, word for word in the group-id ticket's staging `rpg_designer_ruling_2026-10-31.md` (the pool excluded by ghost group_ids on base and whether it explains the gap; re-forming the same membership within 10 or 50 ticks against new memberships; where the time goes). Also per world: how many pairs cycle, cycle length, how long it lasts, store size at t500, t1000 and t2000. Use the group-id PR's 2000t runs where they suffice.
2. Trace one cycle: what ends the group, and what re-forms it. Say whether the contract or recruitment path is involved.
3. Send the counts and the trace to rpg-designer, via rpg-planner-ubuntu and the leads. No fix shape before its ruling.
4. Fix as ruled. It may cover the churn, a retention or bound rule for dissolved records, or both.

Batching (rpg-designer): the group-id fix does not land alone. It lands with this fix, in the same batch, with this fix first or together. Designer's lean: a group that forms should not dissolve without a typed end reason that has changed since it formed; re-forming identical membership on unchanged conditions is the defect.

## Out of Scope
- Group id allocation, which stays with TCK-20261031-A-NEW-GROUP-ID-OVERWRITES-A-LIVE-GROUP.
- Why base keeps an overwritten record one tick longer (rpg-planner: base's store is the corrupted one).

## Acceptance Criteria
1. Counts and the one-cycle trace are in investigation.md, each with the run, seed and commit.
2. rpg-designer's ruling is recorded word for word before implementation.
3. Fix criteria are set from that ruling, including a positive control and any divergence and parity entries.
4. If the group-id PR is held on material cost, this ticket lands the bound that releases it (Ruling 2's test: total tick time up more than 5% in any of the three worlds, or the store passing 2000 records by 2000t).

## Related Tickets
- TCK-20261031-A-NEW-GROUP-ID-OVERWRITES-A-LIVE-GROUP (found here; may be held on this ticket)
- TCK-20260913-GROUP-DISSOLUTION-OUTCOME-NOT-CAPTURED (retains dissolved records)

## Related Docs
- docs/parity_ledger/social_narrative.yaml

## Related Stored Artifacts
None yet.

## Related Code Areas
- src/systems/world_systems/groups.py
- src/engine/pipeline_phases/groups.py
- src/domains/cooperation/phase.py

## Assumptions / Open Questions
- Priority raised to P1 by rpg-planner: this blocks the s42 re-anchor chain. Tier may change with the counts. Not dispatched: the owner go is asked after counts 1-3, with the designer's fix shape.
- Whether churning is ever legitimate behaviour is the designer's question.

## Implementation Notes
## Test Summary
## Files Changed
## Completion Summary
