---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20261028-CURRENT-PROJECT-CLEARED-WITHOUT-ENDING-LEAVES-ORPHANED-ACTIVE-RECORDS
phase: open
date: 2026-10-28
tags: []
---

# TCK-20261028-CURRENT-PROJECT-CLEARED-WITHOUT-ENDING-LEAVES-ORPHANED-ACTIVE-RECORDS

## Title
Five sites clear current_project_id without ending or suspending the project, leaving orphaned ACTIVE records that hold capacity

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
rpg-designer finding (2026-10-28) from the :1610 review (TCK-20261027-CAPACITY-GATE-FIRST-RECORD-OF-KIND-IS-DEAD-SO-LIVE-SIBLING-NEVER-RESUMED, c65794a17). These sites set current_project_id to None and leave the project ACTIVE:
- tactical.py:136
- building_arrival.py:22
- guild_visit.py:88
- intelligence.py:575
- intelligence.py:858

The record stays live (it counts toward max_active_projects) but no one pursues it. :1610 now recovers such a record when a goal of its kind and target wins (make-current arm), but the sites themselves are a lifecycle gap: an orphan whose goal never wins again holds capacity until a trim removes it.

## Scope
Investigation first. No fix shape before rpg-designer sees the numbers.
1. On the corpus gate worlds (3 worlds x s42-46, 5000t; hash-controlled probe, pure-run digest unchanged), count per site: how many times it orphans an ACTIVE record, how long the orphan stays ACTIVE and non-current (median and max ticks), and how it ends (recovered by :1610 make-current, trimmed, completed, still live at the end).
2. Count the ticks on which an orphan makes the capacity gate refuse a new kind.
3. For each site, say what the clear is for (the reason in code or the ticket that added it) and whether ending, suspending or keeping the project current fits that reason.
4. Report to rpg-planner, which forwards to rpg-designer.

## Out of Scope
Any code change. The four mapped kinds (TCK-20261028-MAPPED-GOAL-KINDS-NEVER-MATCH-THEIR-OWN-PROJECT-RECORDS); this can share that ticket's probe run.

## Acceptance Criteria
- Per-site counts and orphan lifetimes on the 15 runs, with the probe's hash equality shown.
- Per-site intent reading with file:line.
- rpg-designer has the numbers.

## Related Tickets
TCK-20261027-CAPACITY-GATE-FIRST-RECORD-OF-KIND-IS-DEAD-SO-LIVE-SIBLING-NEVER-RESUMED (must land first: its make-current arm changes how orphans end)
TCK-20261028-MAPPED-GOAL-KINDS-NEVER-MATCH-THEIR-OWN-PROJECT-RECORDS (sibling investigation)

## Related Docs
docs/mechanics/04_strategic_cognition.md (Project Capacity Counts Live Projects), docs/guidelines/intentional_divergences.md 2.77

## Related Stored Artifacts
None.

## Related Code Areas
src/systems/strategic_systems/intelligence.py, tactical.py, building_arrival.py, guild_visit.py, src/core/strategic.py

## Assumptions / Open Questions
- Exact module paths of the three non-intelligence sites to be confirmed by the investigator (lane A cited the file names).

## Implementation Notes
- EVIDENCE, first concrete cause (rpg-planner, 2026-11-25), from the K3 Phase 0 trace (S9 #715 7168403412; designer read 583d6408…; /mnt/data2/rpg-measure/k3_phase0_out). In 2 rows (class D3: s8 t1472 proj_hunger_1232, s28 t1932 proj_hunger_1312), ONE update carries TWO entries for the same project, COMPLETED and then ACTIVE. The last one wins, which leaves the project ACTIVE with current cleared. That is the orphan shape, from a double write (the arrival's _end_project plus a later entry). Not consecutive, so not HARD (designer).
- NAMES (rename of the measurement kits, owner direction #715 7181423761): the Phase 0 trace kit is now tools/rpg_measure/need_project_cleared_trace_* (was k3_phase0_*); the evidence directory /mnt/data2/rpg-measure/k3_phase0_out keeps its old name.
- MOVED OUT of systemic_foundation (M1) to the cognition-rework backlog, 2026-11-25. Owner ruling #715 7157496515 Q2 (only HARD K1-K5 repairs stay); rpg-designer's classification posted as #715 7157686023 and recorded by the lead as 7157730160. Reason: bounded: a trim removes the orphan, and the orphan path recovers it when its goal wins.
Filed on the rpg-planner seat after :1610; not dispatched.

## Test Summary

## Files Changed

## Completion Summary

## 2026-11-01 counts row from groups batch C (rpg-designer, via rpg-planner)
- crowded s43 v9 (churn-on-F3, ruled NOT FED): ungrouped, on its own COMBAT_ENGAGE walk. Its objective is combat_engage_34 while its task target is 14, a stale or mismatched objective target with an unnamed writer.
- Count it on this ticket's counts step: how often a COMBAT_ENGAGE objective's subject differs from the task target (per run, with durations), and which writer sets each side (file:line). If the mismatch turns out to be a goal-kind/record mapping issue rather than an orphaned record, move the row to TCK-20261028-MAPPED-GOAL-KINDS-NEVER-MATCH-THEIR-OWN-PROJECT-RECORDS.
