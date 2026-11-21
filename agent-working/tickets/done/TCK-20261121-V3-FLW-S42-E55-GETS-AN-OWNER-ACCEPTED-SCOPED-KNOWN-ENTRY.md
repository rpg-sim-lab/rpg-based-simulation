---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261121-V3-FLW-S42-E55-GETS-AN-OWNER-ACCEPTED-SCOPED-KNOWN-ENTRY
phase: done
date: 2026-11-21
tags: [testing]
---

# TCK-20261121-V3-FLW-S42-E55-GETS-AN-OWNER-ACCEPTED-SCOPED-KNOWN-ENTRY

## Title
Gate V3 on frontier_living_world s42 entity 55 gets an owner-accepted scoped known entry that expires on 2026-12-15

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P1

## Request Summary
testing-planner reported (relayed by lead-planner-u24, #715 7062288026 and correction 7062295489) that rpg_gate_candidate refuses to build the REBASELINE from gate run 44887314422 (main 85770a225). The reason: validity row V3 on frontier_living_world s42 (small_plant_eater 55, t4745, FORAGE untried) has 1 violation and no owner. The refusal is correct. The REBASELINE blocks births on ubuntu. The owner accepted a scoped entry (#715 ask 7062335859, answer 7062341398: "Accept, expires 12-15"). The owning ticket is TCK-20261121-A-SMALL-PLANT-EATER-STARVES-IN-FRONTIER-LIVING-WORLD-WITHOUT-TRYING-TO-FORAGE, which stays open. tools/test_architecture/ belongs to testing, and testing does not edit the known file; per the lead, the entry rides rpg-planner's track.

## Scope
Append one scoped V3 `state: fail` entry to tools/test_architecture/rpg_gate_known.yaml: case frontier_living_world/42 entity 55, ticket TCK-20261121-A-SMALL-PLANT-EATER-STARVES-IN-FRONTIER-LIVING-WORLD-WITHOUT-TRYING-TO-FORAGE, owner rpg-planner, added_on 2026-11-21, expires_on 2026-12-15, and a note.

## Out of Scope
- The cause or fix of e55's death (the owning ticket).
- Building the REBASELINE (testing-planner).
- Any other gate row, the V3 check or the gate's thresholds.

## Acceptance Criteria
1. The entry is in the known file exactly as the owner accepted it, scoped to one (world, seed, entity).
2. known_reds lint reports no problems.
3. The known_reds and rpg_gate tool tests pass.

## Related Tickets
- TCK-20261121-A-SMALL-PLANT-EATER-STARVES-IN-FRONTIER-LIVING-WORLD-WITHOUT-TRYING-TO-FORAGE (owner of the row)
- TCK-20261107-THREE-CROWDED-V3-STARVATIONS-GET-SCOPED-KNOWN-ENTRIES (#839 precedent)
- TCK-20261116-RE-BASELINE-THE-RPG-GATE-REFERENCE-TO-A-MAIN-RUN-AFTER-M1-BASE (#948 removed the earlier V3 entries because they no longer failed)

## Related Docs
- tools/test_architecture/known_reds.py (schema and lint, the module docstring)

## Related Stored Artifacts
None.

## Related Code Areas
- tools/test_architecture/rpg_gate_known.yaml

## Assumptions / Open Questions
- The lineage (likely #955) was relayed and has not been bisected; the owning ticket bisects it.

## Durable state, lifecycle and clocks
The entry expires on 2026-12-15. By then the owning ticket retires it (the row is gone, with evidence) or renews it once, with evidence and a new date.

## Implementation Notes
Entry appended after the V1 entry. It uses a different pattern, so nothing is shadowed.

## Test Summary
Executed on rpg-planner-tickets-4, after merging main 85770a225:
- known_reds.lint_file(rpg_gate_known.yaml, RPG_GATE_SPEC) returned no problems.
- tests/unit/tools/test_known_reds.py: 57 passed.
- test_rpg_gate_candidate, test_rpg_gate_report and test_rpg_gate_baseline: 210 passed.
- tests/static/test_ci_rpg_gate_workflow_shape.py: 12 passed.

## Files Changed
- tools/test_architecture/rpg_gate_known.yaml

## Completion Summary
The scoped V3 entry for frontier_living_world s42 e55 is in the known file, owner-accepted, and expires on 2026-12-15. The owning ticket stays open.
