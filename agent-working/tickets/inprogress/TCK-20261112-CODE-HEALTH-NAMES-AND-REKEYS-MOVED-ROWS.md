---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261112-CODE-HEALTH-NAMES-AND-REKEYS-MOVED-ROWS
phase: open
date: 2026-11-12
tags: [testing]
---

# TCK-20261112-CODE-HEALTH-NAMES-AND-REKEYS-MOVED-ROWS

## Title
The code-health check names a likely move, and one `move` command re-keys the moved rows at unchanged value and ceiling

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
u24 lane C split `src/core/updates.py` into update modules, a pure move with 0 differing definitions by AST. Four complexity rows moved byte-identical to `body.py` and `combat.py`, and `check` failed them as new. The owner allowed a hand re-key for that split (#715 6813365478). The failure is the recorded design: a moved function "surfaces as new", and its old row then shows as gone (`codebase/health/findings.py`, module docstring). More splits are coming (next-gen, update-model refactors), so each one would need a hand re-key and an owner approval.

The owner chose option B (#715 6813393813). `check` still fails a move, but names the likely pairs. A new `move` command re-keys them in one step, never loosening a value or a ceiling. Options A (auto-pair inside `check`) and C (keep re-keying by hand) were not chosen.

## Scope
1. **Pairing (ratchet).** After `compare`, a pure function pairs each gone row with each new finding that has the same `(symbol, tool, rule)`, a symbol that is neither `None` nor ast_grep's `<module>`, a different file, and `value <= row.ceiling`. jscpd is excluded, since its symbol is a file pair, not a definition. A pair is only a label: `RatchetResult.new` and `blocking_failed` are unchanged.
2. **Report.** `format_report` and `format_summary` (CI job summary) show a "likely move" section, `old-file → new-file symbol [tool rule]`, with the exact `move` command to run. When one gone row matches several new findings, or several gone rows match one finding, list every candidate and mark it ambiguous. Never pick one.
3. **`python3 -m codebase.health move OLD_FILE NEW_FILE [--symbol S] [--from DIR]`.**
   - Scans like `check`, using `--from DIR` when given and a full scan otherwise. A skippable tool that is not measured cannot be moved: refuse its rows.
   - Re-keys each row of OLD_FILE (only `S` with `--symbol`) whose old key has no current finding and whose new key has one. It changes `file` only; value, ceiling, added_date, reviewed and retiring_ticket are kept byte-identical.
   - Refuses with exit 2 and writes nothing when:
     - any matched new finding is over the row's ceiling;
     - NEW_FILE already has a row with that key;
     - `--symbol` names a row that cannot be moved;
     - no row would move.
   - Rows of OLD_FILE that still have a current finding stay where they are.
   - Prints each re-key and the final count.
4. **Docs.**
   - Update the `findings.py` docstring sentence about moves.
   - Update the `__main__.py` usage block.
   - Update `docs/plans/codebase_health/python_code_craft_roadmap.md` §6.3, one sentence on the move path.

## Out of Scope
- Any change to `check`'s exit code or to what counts as new or worse (option A, not chosen).
- Renames inside one file, a renamed symbol, or a moved file-level row (`symbol` `None`). These stay new and gone, as today.
- jscpd rows.
- Any `src/` change.
- Changing any existing row in `codebase/baselines/code_health_exceptions.jsonl`.

## Acceptance Criteria
- On a fixture where one function moves unchanged from `a.py` to `b.py`:
  - `check` exits 1, lists the finding under NEW and lists the pair under "likely move".
  - After `move a.py b.py`, `check` exits 0, and the moved row differs from the original only in `file`.
- `move` refuses and writes nothing when the moved finding's value is over the ceiling, when the target key exists, when `--symbol` is not movable, or when nothing moves.
- No pair is labelled for a file-level (`None`) symbol or for jscpd. An ambiguous match lists all candidates.
- `format_summary` shows the same pairs.
- `tests/codebase/` passes, `make code-health` passes, and ruff, mypy and pyrefly add no new finding for `codebase/health/`.
- `codebase/baselines/code_health_exceptions.jsonl` is byte-identical to the base.
- Gates run last, on the exact tree committed.

## Related Tickets
TCK-20261002-CODE-HEALTH-RATCHET-REGISTRY (the ratchet); TCK-20261111-CODE-HEALTH-ROWS-FOR-DELETED-FILES (#872); u24 lane C `src/core/updates.py` split (#715 6813365478).

## Related Docs
docs/plans/codebase_health/python_code_craft_roadmap.md (§6.3); docs/guidelines/python_code_standard.md

## Related Stored Artifacts
agent-working/staging_artifacts/TCK-20261112-CODE-HEALTH-NAMES-AND-REKEYS-MOVED-ROWS/{plan,investigation,test_plan}.md

## Related Code Areas
codebase/health/ratchet.py; codebase/health/registry.py; codebase/health/__main__.py; codebase/health/findings.py; tests/codebase/test_code_health_ratchet_registry.py; tests/codebase/test_code_health_ci_summary.py

## Assumptions / Open Questions
- Keeping the ceiling on a move cannot loosen the gate. The finding still has to sit at or under the ceiling it already had, and the re-key shows in the PR diff of the baseline, where a reviewer can see it.
- A full scan in `move` is slow. `--from DIR` reuses a `check` scan. Any test run past a light scope asks lead-planner for the heavy slot.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
