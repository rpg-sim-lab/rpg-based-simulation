---
status: active
layer: core
authority: P1
audience: agent
ticket_id: TCK-20261114-PARITY-LEDGER-TEST-PATH-ERRORS-REMAIN-IN-SEVEN-FILES
phase: open
date: 2026-11-14
tags: [testing]
---

# TCK-20261114-PARITY-LEDGER-TEST-PATH-ERRORS-REMAIN-IN-SEVEN-FILES

## Title
Seven parity-ledger files still carry 2,651 schema errors, most of them P0 entries with no test_path

## Status
OPEN

## Tier
standard

## Type
repair

## Priority
P3

## Request Summary
`TCK-20261010-EPIC-PARITY-LEDGER-PAYDOWN` closed on 2026-11-14 by owner decision (#715
6875225978: close empty epics, recording done versus moved). Only its first ledger file,
`world_dynamics.yaml`, was paid down (#783, #784). This ticket carries the other seven files
forward. CLAUDE.md still requires every P0 entry to have a passing `test_path`, and the CI ratchet
only stops the count from rising.

Counts on origin/main db918c517, from
`python3 -m codebase.gates.parity_ledger_schema check` (2651 errors, matches the committed
baseline). Column A is rule `allOf/0` (a `verified`/`divergent` entry with no test_path). Column B
is rule `allOf/2/else` (a P0 entry that is not `missing`/`unsupported` and has no test_path).
Column C is out-of-enum `proof_type`.

| Ledger file | Owner | A | B | C |
|---|---|---|---|---|
| progression | rpg | 83 | 93 | 0 |
| town_resource | rpg | 129 | 142 | 1 |
| strategic_cognition | rpg | 142 | 197 | 0 |
| infrastructure | testing (owner, 2026-10-10) | 149 | 162 | 19 |
| social_narrative | rpg | 164 | 206 | 0 |
| combat_movement | rpg | 235 | 261 | 4 |
| substrate | rpg | 308 | 355 | 1 |
| **Total** | | 1210 | 1416 | 25 |

Column B checked by a separate count of the YAML: B equals each file's P0 `verified` plus P0
`legacy_verified` entries with no test_path, in all seven files. `faction.yaml` has 0 errors.

## Scope
- Resolve each entry in one of three ways: cite the real test that proves it; change its status to
  what the evidence supports, with the reason; or use an owner-approved exception mechanism, if one
  is ever created (none exists today).
- Work one ledger file at a time, smallest first (the table order). Split a file into several
  tickets when it is too large for one PR (substrate, combat_movement).
- The rules carried from the epic still hold: the schema stays strict; downgrading to
  `legacy_verified` does not clear a P0 error; out-of-enum `proof_type` values are remapped to the
  existing enum entry by entry, never by extending the enum.
- Each PR runs `python3 -m codebase.gates.parity_ledger_schema tighten --yes` and commits
  `codebase/baselines/parity_ledger_schema_baseline.json`.
- Use the method from the world_dynamics children (#784): a draft table of entries reviewed by
  rpg-planner, then writes through `parity_ledger_writer.py`.

## Out of Scope
- Changing the schema rules, the proof_type enum or the ratchet.
- Bulk status changes without per-entry evidence.
- `world_dynamics.yaml` (done) and `faction.yaml` (no errors).

## Acceptance Criteria
1. Each of the seven files reaches 0 errors under all three rules, or carries an owner-recorded
   decision that says why not.
2. Every PR tightens the baseline, and the baseline never rises.
3. Each PR runs a sample of the test_paths it cites and states which ones passed.

## Related Tickets
- `TCK-20261010-EPIC-PARITY-LEDGER-PAYDOWN` (closed; this ticket's source)
- `TCK-20261028-PARITY-PAYDOWN-WORLD-DYNAMICS`, `TCK-20261028-PARITY-PAYDOWN-WORLD-DYNAMICS-STATUS-CHANGES` (method)
- `TCK-20261003-PARITY-LEDGER-SCHEMA-RATCHET` (the gate)

## Related Docs
- `docs/parity_ledger/README.md`, `docs/parity_ledger/schema.json`
- CLAUDE.md "Parity Ledger"

## Related Stored Artifacts
None.

## Related Code Areas
`docs/parity_ledger/*.yaml`, `codebase/gates/parity_ledger_schema.py`,
`codebase/baselines/parity_ledger_schema_baseline.json`

## Assumptions / Open Questions
- Not scheduled. The owner sets when it starts; the architecture re-design is paused as of
  2026-11-14 so in-flight epics finish first.
- `infrastructure.yaml` stays testing's to pay down (owner, 2026-10-10); testing-planner files that
  part.
- Counts move as other work lands. Re-count on current main when work starts.

## Implementation Notes
(Not started.)

## Test Summary
(Not started.)

## Files Changed
(Not started.)

## Completion Summary
(Open.)
