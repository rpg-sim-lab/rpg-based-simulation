---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261120-CODE-HEALTH-MOVE-CARRIES-RENAMED-SYMBOLS-AND-PARTIAL-ROW-SETS
phase: open
date: 2026-11-20
tags: [testing]
---

# TCK-20261120-CODE-HEALTH-MOVE-CARRIES-RENAMED-SYMBOLS-AND-PARTIAL-ROW-SETS

## Title
`codebase.health move` re-keys a symbol whose name changed, and moves the rows whose findings moved when only some of a file's rows did

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
The split TCK-20261117-SPLIT-INTELLIGENCE-PY-BELOW-ITS-LINE-CEILINGS (Group 1, u24 lane C) moved `StrategicIntelligenceSystem.infer_blockers` / `resolve_blockers` out of `src/systems/strategic_systems/intelligence.py` as module functions `infer_blockers` / `resolve_blockers` in a new `blocker_lifecycle.py`. `python3 -m codebase.health move` (TCK-20261112-CODE-HEALTH-NAMES-AND-REKEYS-MOVED-ROWS) refused twice. First, the symbol name changed, and `move` re-keys `file` only. Second, only some of intelligence.py's rows moved, and `--symbol` requires every row of a symbol to have moved. Lane C re-keyed the rows by hand through the registry API with a one-off script. codebase-planner OK'd that through lead-planner on 2026-11-20, on conditions: `check` clean at the new keys, a mechanical multiset check for mypy/pyrefly, and the script kept out of codebase/ and tools/. Every future split that also renames, or moves part of a file, would need the same hand path.

## Scope
1. `move OLD_FILE NEW_FILE --symbol S --as NEW_S`: re-keys the rows of `S` in OLD_FILE to `(NEW_FILE, NEW_S)`. `NEW_S` may equal `S`, and NEW_FILE may equal OLD_FILE, for a pure rename in place. Value, ceiling, added_date, reviewed and retiring_ticket are kept byte-identical. Same refusals as today: the moved finding is above its ceiling, the new key already has a row, the old key still has a finding, or the new key has none.
2. Partial row sets: without `--symbol`, `move` re-keys every row of OLD_FILE whose old key has no current finding and whose new key has one, and lists the rows it left in place with the reason ("still found at old key"). It no longer refuses because some rows did not move. With `--symbol`, the current rule stays (every row of that symbol must have moved).
3. The "likely move" pairing in `check` (ratchet.py) also proposes a rename pair when one gone row and one new finding share file-pair, tool and rule and differ only in the symbol's last dotted component or its class prefix. It is marked "rename?" and never picked automatically when ambiguous.
4. Docs: `__main__.py` usage text, and the code-health section of `docs/guidelines/python_code_standard.md`, if it describes `move`.

## Out of Scope
- mypy_baseline.txt and pyrefly_baseline.json re-keys. These stay manual, checked by comparing the (message, code) multisets with path, line and column stripped.
- Any change to what `check` blocks, or to `tighten` / `seed`.
- Re-keying the intelligence rows again: lane C's re-key is the record.

## Acceptance Criteria
- `move --symbol S --as NEW_S` re-keys a renamed symbol's rows with only `file`/`symbol` changed. All other fields are byte-identical, and a test covers it.
- `move` without `--symbol` on a partially moved file re-keys the moved rows, reports the unmoved ones, and exits 0. A test covers it.
- Every existing refusal still refuses (the existing tests stay green), plus a new refusal when `--as` names a symbol with no current finding at NEW_FILE.
- No row's value or ceiling ever goes up, which a property-style test asserts over the refusal matrix.
- tests/codebase/ passes, and `make code-health` is clean.

## Related Tickets
- TCK-20261112-CODE-HEALTH-NAMES-AND-REKEYS-MOVED-ROWS (introduced `move`)
- TCK-20261117-SPLIT-INTELLIGENCE-PY-BELOW-ITS-LINE-CEILINGS (the split that hit both gaps)

## Related Docs
- docs/guidelines/python_code_standard.md
- docs/plans/codebase_health/python_code_craft_roadmap.md

## Related Stored Artifacts
- TCK-20261117-SPLIT-INTELLIGENCE-PY-BELOW-ITS-LINE-CEILINGS stored artifacts: rekey.py (sha 84f0e125cc39a0b0), baseline_row_diff.txt (sha 416b1212d0c94fb8), on u24 until that PR lands

## Related Code Areas
- codebase/health/registry.py (`move_rows`, `_move_problem`)
- codebase/health/ratchet.py (`LikelyMove`, pairing)
- codebase/health/__main__.py
- tests/codebase/

## Assumptions / Open Questions
- Whether rename pairing in `check` (scope 3) earns its complexity: drop it if the heuristic needs more than the two shapes named. `--as` alone still covers the need.

## Durable state, lifecycle and clocks
No simulation state. The only durable file is codebase/baselines/code_health_exceptions.jsonl, written by registry.py alone. This ticket adds no second writer.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
