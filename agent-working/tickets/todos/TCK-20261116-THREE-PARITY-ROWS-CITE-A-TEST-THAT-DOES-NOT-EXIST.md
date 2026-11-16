---
status: active
layer: compliance
authority: P2
audience: agent
ticket_id: TCK-20261116-THREE-PARITY-ROWS-CITE-A-TEST-THAT-DOES-NOT-EXIST
phase: open
date: 2026-11-16
tags: [documentation]
---

# TCK-20261116-THREE-PARITY-ROWS-CITE-A-TEST-THAT-DOES-NOT-EXIST

## Title
Three verified parity rows (COMB-351, STRAT-280, TOWN-019) cite a test file or node that does not exist on main, so their stated proof points at nothing

## Status
OPEN

## Tier
hotfix

## Type
repair

## Priority
P3

## Request Summary
agent-working-planner's docs-truth measurement (draft F3b) named three rows whose test node is gone. rpg-planner-ubuntu checked each at origin/main db6b4579d:
- **COMB-351** (`docs/parity_ledger/combat_movement.yaml`:4915) cites `tests/unit/tactical/testflight_weighs_free_swing.py`. That's a typo: the file is `tests/unit/tactical/test_flight_weighs_free_swing.py`. It was introduced in #854 (cf27795cb).
- **STRAT-280** (`docs/parity_ledger/strategic_cognition.yaml`, test_path line about 4521) cites `tests/unit/ai/test_need_pull.py`. That path doesn't exist; the file is `tests/unit/engine/test_need_pull.py`.
- **TOWN-019** (`docs/parity_ledger/town_resource.yaml`:233-235) cites three nodes:
  - `tests/unit/world/test_building_interaction_contract.py::test_building_interaction_inn_rest_recovery` exists.
  - `tests/unit/world/test_recovery_class_hall.py::test_class_hall_inn_rest_recovery` and `::test_home_upgrade_blocker` are gone. The file was deleted in #472 (c826c873d, "delete dead inn.py and home.py"), and neither test name exists anywhere under tests/ on main.

Filing only. Dispatch needs an owner go.

## Scope
1. COMB-351: correct the path to `tests/unit/tactical/test_flight_weighs_free_swing.py`. Exact-line edit.
2. STRAT-280: correct the path to `tests/unit/engine/test_need_pull.py`. Exact-line edit. First confirm that the file tests what the row claims (need_pull escalation, REST_IN_PLACE).
3. TOWN-019: remove the two deleted nodes from test_path. Then decide what the remaining node proves against the row's text:
   - If the row's claim needs class-hall or home-upgrade coverage that no test now gives, STOP and ask rpg-planner (u24). It rules whether the row narrows its text and support_boundary, gets a new test, or changes status.
   - Don't change status without that ruling.
4. Prove that each corrected node collects: `pytest --collect-only -q <node>`, capped.
5. Edit by exact line, not through a full-file rewrite. Show `git diff --stat`, then `tools/parity_ledger_writer.py --check`.

## Out of Scope
- The list-form schema change (TCK-20261116-PARITY-TEST-PATH-BECOMES-A-LIST, which lands after this).
- Any other row; the 1,210 untested rows (TCK-20261114-PARITY-LEDGER-TEST-PATH-ERRORS-REMAIN-IN-SEVEN-FILES).

## Acceptance Criteria
1. Each of the three rows' test_path entries collects on main: show the `--collect-only` output.
2. The diff touches only those rows' test_path lines, plus TOWN-019's support_boundary if rpg-planner rules it should narrow.
3. TOWN-019's coverage question is answered by rpg-planner (u24)'s ruling, recorded word for word in the ticket, or the class-hall and home claims are still tested by a named existing test.
4. The parity ledger tests pass, capped: `tests/tools/test_parity_ledger_schema.py`, `tests/tools/test_parity_ledger_check.py` and `tests/codebase/test_parity_ledger_schema_gate.py`.

## Related Tickets
- TCK-20261109-A-FLIGHT-WEIGHS-THE-FREE-SWING-IT-WOULD-TAKE (COMB-351's origin, #854)
- TCK-20261116-PARITY-NEW-ROW-TEST-PATH-RATCHET-REPORT-ONLY (agent-working; found the three)
- TCK-20261116-PARITY-TEST-PATH-BECOMES-A-LIST (lands after)

## Related Docs
- docs/parity_ledger/combat_movement.yaml
- docs/parity_ledger/strategic_cognition.yaml
- docs/parity_ledger/town_resource.yaml

## Related Stored Artifacts
None.

## Related Code Areas
- tests/unit/tactical/test_flight_weighs_free_swing.py
- tests/unit/engine/test_need_pull.py
- tests/unit/world/test_building_interaction_contract.py

## Assumptions / Open Questions
- TOWN-019 may need an rpg-planner (u24) ruling (Scope 3).

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
