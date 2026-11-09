---
status: active
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20261109-NEXT-GENERATION-ENGINE-CONTRACT-SPEC
phase: open
date: 2026-11-09
tags: [architecture, engine, determinism]
---

# TCK-20261109-NEXT-GENERATION-ENGINE-CONTRACT-SPEC

## Title
Specify the kernel/logic phase contract and its deterministic merge rules, so the serial kernel can be reproduced exactly behind it.

## Status
INPROGRESS (draft 1 written; draft 2 waits on child 2's report and stage 0)

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Child 4 of `TCK-20261109-EPIC-NEXT-GENERATION-ENGINE`. Blocked on child 0 (`TCK-20261109-NEXT-GENERATION-ENGINE-ADR`) and on the
results of children 1 (the stage 0 re-measure) and 2 (the stage 1 access audit). Owner: architecture. Output is a design doc in
`docs/plans/architecture/`.

## Scope
1. The phase contract: the four layers (feasibility review §5), declarations, the step view, and the typed delta per step kind.
2. Merge rules for every field of `EntityUpdate` and `StateUpdate` (`src/core/updates.py:788-803`), including:
   - splitting the whole-object replace of `cognition_bundle_set` (`:799`) into sub-field deltas;
   - a contention rule for cooperation's JOIN_PARTY contract acceptance (`src/domains/cooperation/phase.py:175-196`);
   - a canonical order for trust/grudge sums, for the combat witness fold, and for clamped faction-sentiment accumulation
     (`apply.py:406-434`);
   - spawn-id allocation (`generator.py:117`);
   - event ids (uuid4, `events.py:56`).
3. State hygiene: caches written onto state (`route_plans`, spatial and movement caches, the cooperation `timeline.append`) move to
   kernel- or phase-owned storage. Process globals are loaded once and fingerprinted.
4. For each rule, how it reproduces today's order exactly (Level A), and the test that proves it.
5. The fit with the distributed-workers experiment's executor seam.
6. The first slice's contract (`fused_strategic_pass`) in full, as the prototype's spec.

**Cost:** one or two doc sessions, no runs. **Leaves out:** code, the parallel executor, Level B changes.

## Out of Scope
- Code. Any semantic change (Level B).

## Acceptance Criteria
1. Every field of `EntityUpdate` and `StateUpdate` has a declared merge rule, with the reason it reproduces today's result.
2. Every hidden mutation and contention point found by child 2 has a rule.
3. The prototype slice's contract is complete enough for rpg-planner to cut stage 3. **Met only by rpg-planner's explicit sign-off**,
   asked for when draft 2 lands (ubuntu review A-n1).

## Related Tickets
- TCK-20261109-EPIC-NEXT-GENERATION-ENGINE (parent)
- TCK-20261109-NEXT-GENERATION-ENGINE-ADR (blocks this)

## Related Docs
- docs/plans/architecture/next_generation_engine_contract_spec.md (the spec, draft 1)
- docs/plans/architecture/next_generation_engine_merge_inventory.md (its field-by-field evidence)
- docs/architecture/next_generation_engine_adr.md (accepted, #715 6742854335)
- docs/plans/architecture/next_generation_engine_feasibility_review.md

## Related Stored Artifacts
- none

## Related Code Areas
- src/core/updates.py
- src/engine/pipeline.py
- src/engine/apply.py
- src/domains/cooperation/phase.py
- src/systems/strategic_systems/intelligence.py

## Assumptions / Open Questions
- Child 2's access audit may find more hidden mutations; the scope follows it.

## Implementation Notes
Filed by architecture-planner-u24. The filing rides a later implementation PR (#715 6697748243).

Draft 1, 2026-11-09, on the owner's dispatch (#715 6743047506):
- every field of `EntityUpdate` (30) and `StateUpdate` (53) has a merge class with its Level A argument (spec §2-§3);
- contention (§4), state hygiene (§5), the prototype slice (§8);
- findings F1-F8 for their owners (§9);
- open items A1-A6 for the audit (§10).
AC 1 is met statically. AC 2 needs child 2's report. AC 3 is drafted for `fused_strategic_pass` and needs rpg-planner's sign-off.
Ubuntu lead-planner review of draft 1 (d315b4194, via lead-planner-u24): good as draft 1; notes A-n1 to A-n4 taken.

## Test Summary
Doc only.

## Files Changed
None yet.

## Completion Summary
Open.
