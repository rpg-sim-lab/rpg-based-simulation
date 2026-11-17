---
status: active
layer: compliance
authority: P2
audience: agent
ticket_id: TCK-20261116-PARITY-TEST-PATH-BECOMES-A-LIST
phase: open
date: 2026-11-16
tags: [schema, documentation]
---

# TCK-20261116-PARITY-TEST-PATH-BECOMES-A-LIST

## Title
A parity ledger row's test_path is one free-text string (paths joined by `;`, `+` or `,`, with backticks and prose mixed in), so no check can resolve it; make it a list of test node ids with the prose in a separate note field

## Status
OPEN

## Tier
standard

## Type
refactor

## Priority
P3

## Request Summary
This comes from the owner's docs-truth decisions on #715 6911224913. Q3 chose "Parity test_path ratchet" report-only, with test_path becoming a list first. agent-working-planner drafted the work as F3a in the main checkout's `.claude/handover/drafts/docs_truth_fold_in_and_filings.md`, section 2. It is filed here because `docs/parity_ledger/**` routes to rpg (rpg-planner-ubuntu). The report-only ratchet that depends on it, TCK-20261116-PARITY-NEW-ROW-TEST-PATH-RATCHET-REPORT-ONLY, is agent-working's.

Filing only. Dispatch needs an owner go. It also needs rpg-planner (u24)'s yes on the schema change first, because rpg-planner owns parity semantics.

## Scope
1. `docs/parity_ledger/schema.json`: `test_path` changes from `string|null` to an array of strings (an empty list replaces null). Add an optional `test_note` string field for any prose now inside test_path.
2. Migrate every row in the 8 ledger files mechanically:
   - Split on `;`, `+` and `,`, and strip backticks and surrounding whitespace. agent-working-planner measured that about 21 prose fragments get read as missing files otherwise.
   - A fragment that is not a path or a `path::node` goes to `test_note`, verbatim.
   - Use `tools/parity_ledger_writer.py`, which is agent-working's tool. If it can only rewrite a whole file, write a one-off migration that keeps every other byte, and prove it: `git diff --stat` before and after, and a parse-and-compare script showing that every field other than test_path/test_note is identical per row.
3. Update every reader of `test_path`. Find them by grepping the producer and its consumers in tools/, tests/ and src/, not by name-matching. Known ones include tools/parity_ledger_check.py, tools/parity_ledger_scan.py, tools/parity_ledger_writer.py and tests/codebase/test_parity_ledger_schema_gate.py.
4. Update the schema docs: `docs/parity_ledger/README` (if it exists), and CLAUDE.md's parity ledger line through its owner.

## Out of Scope
- The 1,210 verified rows with no test_path. They belong to TCK-20261114-PARITY-LEDGER-TEST-PATH-ERRORS-REMAIN-IN-SEVEN-FILES.
- Any status change, and any automatic downgrade.
- The three rows whose test node is gone. They belong to TCK-20261116-THREE-PARITY-ROWS-CITE-A-TEST-THAT-DOES-NOT-EXIST, and that one lands first so the migration copies correct paths.
- The ratchet check itself (agent-working's ticket).

## Acceptance Criteria
1. The schema validates every migrated row, and `pytest tests/tools/test_parity_ledger_schema.py tests/tools/test_parity_ledger_check.py tests/tools/test_parity_ledger_scan.py tests/tools/test_parity_ledger_writer.py tests/codebase/test_parity_ledger_schema_gate.py` passes, capped.
2. Status counts are unchanged: before and after, per file and per status (all 1,961 verified rows today). Every path a row cites today is still cited, as a list entry. This is shown by a script that compares old fragments to new entries plus test_note.
3. No list entry contains a backtick, `;`, `+` or a space-separated prose word.
4. Every test_path reader works on the list form, with a test per reader for one-entry, many-entry and empty lists.
5. The diff touches only test_path/test_note lines, schema.json and the readers. Show `git diff --stat` and the per-row field-equality check.

## Related Tickets
- TCK-20261116-PARITY-NEW-ROW-TEST-PATH-RATCHET-REPORT-ONLY (depends on this)
- TCK-20261114-PARITY-LEDGER-TEST-PATH-ERRORS-REMAIN-IN-SEVEN-FILES
- TCK-20261116-THREE-PARITY-ROWS-CITE-A-TEST-THAT-DOES-NOT-EXIST (lands first)
- TCK-20261031-EPIC-AI-FIRST-SDLC-EVOLUTION (docs-truth plan)

## Related Docs
- docs/parity_ledger/schema.json and the 8 ledger files
- CLAUDE.md "Parity Ledger" section

## Related Stored Artifacts
None. The draft is the main checkout's untracked `.claude/handover/drafts/docs_truth_fold_in_and_filings.md`, section 2 F3a. Its substance is copied above.

## Related Code Areas
- tools/parity_ledger_writer.py
- tools/parity_ledger_check.py
- tools/parity_ledger_scan.py
- tests/codebase/test_parity_ledger_schema_gate.py

## Assumptions / Open Questions
- Needs rpg-planner (u24)'s yes on the schema change before dispatch. Ask: list form, test_note field, empty list for none.
- Lanes: the ledger rows and schema are rpg's. The writer, check and scan tools and their tests are agent-working's. One implementer can do both, with a review from each lane.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
