---
status: active
layer: core
authority: P1
audience: agent
ticket_id: TCK-20261115-THREE-VERIFIED-PARITY-ROWS-CITE-A-TEST-FILE-THAT-DOES-NOT-EXIST
phase: open
date: 2026-11-15
tags: []
---

# TCK-20261115-THREE-VERIFIED-PARITY-ROWS-CITE-A-TEST-FILE-THAT-DOES-NOT-EXIST

## Title
Three verified parity rows cite a test file that does not exist (TOWN-019, STRAT-280, COMB-351)

## Status
OPEN

## Tier
hotfix

## Type
repair

## Priority
P2

## Request Summary
lead-planner-u24 asked for this filing on 2026-11-15, with the ubuntu lead's agreement. It came out of rpg-planner's comment on the docs-truth proposal. That comment first claimed 101 such rows. The figure was a parsing error: a multi-path `test_path` was read as one path. It was corrected to lead the same day.

Each path inside each `verified` row's `test_path` was checked on disk at origin/main f94417e6f, after splitting on `;`, `,` and whitespace and stripping `::node`. Directory and `.ts`/`.tsx` paths were checked too, and all of them exist. Exactly 3 rows cite a missing file:

| Row | Priority | Missing path | What happened | Likely fix |
|---|---|---|---|---|
| TOWN-019 (town_resource.yaml) | P0 | `tests/unit/world/test_recovery_class_hall.py::test_class_hall_inn_rest_recovery`, `::test_home_upgrade_blocker` | File deleted in #472 (c826c873d, which also deleted dead inn.py/home.py). The row's first path, `test_building_interaction_contract.py::test_building_interaction_inn_rest_recovery`, exists. | Find whether class-hall and home recovery semantics still have a test. If yes, re-point the row. If not, the row's class-hall/home claim is unproven: narrow the text, or downgrade under its support_boundary. |
| STRAT-280 (strategic_cognition.yaml) | P1 | `tests/unit/ai/test_need_pull.py` | Moved to `tests/unit/engine/test_need_pull.py` in #420 (67592c90c, need_pull moved to engine). | Re-point the row. |
| COMB-351 (combat_movement.yaml) | P1 | `tests/unit/tactical/testflight_weighs_free_swing.py` | Typo. `tests/unit/tactical/test_flight_weighs_free_swing.py` exists. | Re-point the row. |

## Scope
1. Re-point STRAT-280 and COMB-351 to the existing files, and run those tests.
2. TOWN-019: read #472 and the current tests for class-hall and home recovery. Re-point the row if a test exists. Otherwise, rpg-planner decides between narrowing the text and downgrading the row.
3. All ledger edits go through `tools/parity_ledger_writer.py`. Run its `--check`.

## Out of Scope
- The 1210 verified rows with no `test_path` (TCK-20261010-EPIC-PARITY-LEDGER-PAYDOWN).
- The docs-truth CI proposal: required checks, cite resolution, stamps, auto-downgrade.
- Any `src/` change.

## Acceptance Criteria
- No `verified` row cites a non-existent test file. A re-runnable one-shot check confirms this, and its output goes in Test Summary.
- Each re-pointed test passes locally (`-n 1`).
- TOWN-019's resolution is stated with evidence, re-pointed or narrowed/downgraded.

## Related Tickets
- TCK-20261010-EPIC-PARITY-LEDGER-PAYDOWN

## Related Docs
- docs/parity_ledger/town_resource.yaml, strategic_cognition.yaml, combat_movement.yaml; docs/parity_ledger/schema.json

## Related Stored Artifacts
None.

## Related Code Areas
- tools/parity_ledger_writer.py; tests/unit/world/, tests/unit/engine/test_need_pull.py, tests/unit/tactical/test_flight_weighs_free_swing.py

## Assumptions / Open Questions
- Dispatch is a later owner ask. This is filing only, riding rpg-planner's next PR.
- A path-existence check could become a ledger-writer `--check` rule. That belongs to the docs-truth proposal's item 2, not here.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
