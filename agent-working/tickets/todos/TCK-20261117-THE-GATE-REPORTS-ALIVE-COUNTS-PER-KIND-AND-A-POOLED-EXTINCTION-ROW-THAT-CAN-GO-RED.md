---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261117-THE-GATE-REPORTS-ALIVE-COUNTS-PER-KIND-AND-A-POOLED-EXTINCTION-ROW-THAT-CAN-GO-RED
phase: open
date: 2026-11-17
tags: []
---

# TCK-20261117-THE-GATE-REPORTS-ALIVE-COUNTS-PER-KIND-AND-A-POOLED-EXTINCTION-ROW-THAT-CAN-GO-RED

## Title
The rpg gate report gives final alive counts per kind and per occupation, plus a pooled validity row ("alive in ≥3 reference seeds, alive in 0 head seeds") that can go red

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
FILED FOR THE TESTING TRACK by rpg-planner, at the owner's direction (#715 6937306315, follow-up to 6937264378). The owner of the work is testing-planner (tools/test_architecture/), together with src/observability for the per-kind emission. Build it in M1 Phase 2, when other domains get the host back; Phase 3's boundary reads use it.

Why: rpg-designer found that `.github/workflows/rpg-gate-report.yml` can't compute M1's pooled extinction line.
- It pools `O2.seeds_with_survivors` per DIET group (kind_group.py), with every people role in one group.
- It has no "alive in ≥3 base seeds" qualifier.
- It compares against the reference baselines, not the PR's parent.
- An outcome drift never goes red.
- Its uploaded documents carry no per-kind counts, so the line can't be rebuilt from them.
So for M1 Phase 1, extinction and liveness are read on the u24 host at each domain boundary commit (15 plain runs, the kind-level line as M1-base computed it), and the per-PR GitHub run is kept only for its HARD validity rows (V1-V8, determinism, run_errors).

## Scope
1. The gate's per-run output carries the final alive count per kind (species, via species_of()) and per occupation (via occupation_of()), per world and seed.
2. A pooled validity row per world and kind: alive in ≥3 reference seeds AND alive in 0 head seeds → RED (a HARD validity failure, not a drift). The reference and head are inputs, so a boundary read can compare boundary N with boundary N-1.
3. The uploaded documents keep the per-kind counts, so the row can be recomputed offline.
4. Docs: the gate's report docs, plus the M1 epic's Phase 3 plan pointing at the row.

## Out of Scope
- Changing the existing diet-group O2 rows (they stay as report-only drift).
- Any sim behaviour change.
- M1 Phase 1's host boundary reads, which run on today's M1-base line computation.

## Acceptance Criteria
- A gate run on two known refs shows per-kind and per-occupation alive counts.
- A synthetic case (kind alive in 3 reference seeds, 0 head seeds) makes the pooled row RED, and 2 reference seeds does not.
- The row's result equals the M1-base kind-level line on the same inputs (one cross-check world).
- rpg-designer signs off that the row is the pooled line it defined.

## Related Tickets
- TCK-20261109-MILESTONE-1-KINDS-BY-PROPERTIES-EPIC
- TCK-20261115-THE-GATE-REPORTS-WHETHER-EACH-WORLDS-OUTCOMES-STAY-IN-THEIR-BANDS
- TCK-20261115-THE-GATE-METRICS-EMIT-THE-OUTCOME-BAND-ROWS

## Related Docs
- docs/plans/systemic_world/roadmap.md §12.5 (M1 done criteria: the pooled per-world extinction line)
- docs/plans/test_architecture/ (the testing track)

## Related Stored Artifacts
- none

## Related Code Areas
- .github/workflows/rpg-gate-report.yml, tools/test_architecture/ (gate metrics, kind_group.py), src/observability/

## Assumptions / Open Questions
- Should the per-kind counts come from the run's final state (cheapest) or from the event log?
- The occupation counts follow kind=species step 4, once occupation is its own field on main.

## Implementation Notes
- Filed by rpg-planner for testing-planner; no code here. Routed per the session roles: tests/architecture and docs/plans/test_architecture belong to testing-planner.

## Test Summary

## Files Changed

## Completion Summary
