---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261116-PARITY-NEW-ROW-TEST-PATH-RATCHET-REPORT-ONLY
phase: open
date: 2026-11-16
tags: [ai, governance, testing]
---

# TCK-20261116-PARITY-NEW-ROW-TEST-PATH-RATCHET-REPORT-ONLY

## Title
A report-only check requires a `verified` parity row added or changed after the cutover to have a test path that resolves to a collected test.

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P3

## Request Summary
Docs-truth track of the SDLC plan (`docs/plans/agent_infrastructure/AI_FIRST_SDLC_ARCHITECTURE_EVOLUTION_PLAN.md`, "Docs-truth track" under Phase 4). Filed by agent-working-planner on 2026-11-16 from agent-working-designer's hand-off. The owner's decisions are on #715: 6911224913 (Q3: all four checks start report-only, none blocking) and 6911534263. The measurements and reasoning are in `agent-working/stored_artifacts/sdlc-decisions/docs_truth_plan.md`. Filing only: dispatch needs a separate owner go. P3, behind RPG work (#715 6911759453). It depends on rpg-planner's ticket that changes `test_path` to a list (F3a in the hand-off). That ticket is filed in rpg's lane, because `docs/parity_ledger/**` routes to rpg-planner.

## Scope
1. After the `test_path`-as-a-list cutover, a report-only check covers each `verified` row added or changed since the cutover. Its `test_path` entries must resolve to a collected test.
   - Rows that rest on slow or integration tests CI does not run may say `verified_offline`.
   - A test node that is gone or no longer collects is reported as such. There are 3 such rows today: TOWN-019, STRAT-280 and COMB-351, which rpg-planner files separately.
2. Split on `;`, `+` and `,`, strip backticks, and accept directories and non-Python tests. Without that, about 21 prose fragments read as missing files (the designer's measurement).

## Out of Scope
- Blocking; downgrading any row; the 1,210 existing verified rows with no `test_path` (TCK-20261114-PARITY-LEDGER-TEST-PATH-ERRORS-REMAIN-IN-SEVEN-FILES).
- Editing `docs/parity_ledger/**` (rpg's).

## Acceptance Criteria
1. Tests with temp ledgers cover a new resolving row, a new non-resolving row, `verified_offline`, and an old untouched untested row (not reported).
2. The check runs report-only in CI. The workflow diff goes to the owner before commit.
3. The parse rules in scope 2 are pinned by a test that uses the prose forms found today.

## Related Tickets
- TCK-20261031-EPIC-AI-FIRST-SDLC-EVOLUTION
- TCK-20261114-PARITY-LEDGER-TEST-PATH-ERRORS-REMAIN-IN-SEVEN-FILES
- rpg-planner's `test_path`-as-a-list ticket (prerequisite; id to add when filed)

## Related Docs
- docs/plans/agent_infrastructure/AI_FIRST_SDLC_ARCHITECTURE_EVOLUTION_PLAN.md (Docs-truth track)
- agent-working/stored_artifacts/sdlc-decisions/docs_truth_plan.md

## Related Stored Artifacts
- agent-working/stored_artifacts/sdlc-decisions/docs_truth_plan.md

## Related Code Areas
- tools/parity_ledger_writer.py (agent-working's)
- tools/gate_checks/ (new check)

## Assumptions / Open Questions
- BLOCKED in practice until the list cutover lands. Do not dispatch before it.

## Implementation Notes
(to be filled by the implementer)

## Test Summary
(to be filled by the implementer)

## Files Changed
(to be filled by the implementer)

## Completion Summary
(to be filled by the implementer)
