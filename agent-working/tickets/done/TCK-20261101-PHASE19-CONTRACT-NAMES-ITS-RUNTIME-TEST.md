---
status: historical
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20261101-PHASE19-CONTRACT-NAMES-ITS-RUNTIME-TEST
phase: done
date: 2026-11-01
tags: []
---

# TCK-20261101-PHASE19-CONTRACT-NAMES-ITS-RUNTIME-TEST

## Title
The phase19 import contract names its runtime test, drops drifting kernel line numbers, and also guards src.ai.goals

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P3

## Request Summary
Follow-on to `TCK-20261018-PHASE19-OFF-MODE-RUNTIME-CHECK` (#817, 7b4034a14), from testing-planner via the leads. The `c06_hot_path_not_heavy` comments in `codebase/structure/importlinter.toml` still call rpg's OFF-mode condition unenforced, and their `kernel.py` line numbers have drifted. rpg-planner also suggested adding `src.ai.goals` as a source module. Before #803, `src/ai/goals/adventure_scorer.py:10` imported `src.observability.cognition.decision_trace_writer` directly, which loaded the cognition package in an OFF-mode process. The contract's sources did not cover that file.

## Scope
In `codebase/structure/importlinter.toml`, contract `c06_hot_path_not_heavy`:
1. Replace the "UNENFORCED until ..." sentence: the condition is enforced by `tests/architecture/test_phase19_off_mode_imports_none_of_the_four.py`. Keep its stated limit (one tick on one world). Remove the sentence about `test_phase19_observability_boundaries.py` only if it no longer helps a reader.
2. Drop the four `kernel.py:NNN` line references. Name the place instead (`Kernel.__init__`, `Kernel.shutdown`), so they cannot drift again.
3. Add `"src.ai.goals"` to `source_modules`, and update the contract `name` so it stays true (for example `engine, ai.goals and the three hot observability modules do not import the heavy analyzers (phase19)`).

Also on this branch, carried from the planner (`docs/plans/codebase_health/python_code_craft_roadmap.md`): the M7 batch 2 row, plus planner monitoring rows.

## Out of Scope
- Any `src/` change.
- Adding, removing or widening any `ignore_imports` edge. `test_phase19_off_mode_imports_none_of_the_four.py` pins them on purpose.
- Other source modules beyond `src.ai.goals`.
- Historical line numbers in `docs/plans/codebase_health/handoffs/` and the import-linter evaluation: they are dated records.

## Acceptance Criteria
- `make lint-imports` shows the same contract count, 0 broken, with no new ignore and no new stale-ignore warning.
- Positive control in a scratch copy, never the repo: a direct import of `src.observability.cognition.decision_trace_writer` added to `src/ai/goals/adventure_scorer.py` breaks `c06` with the new source and passes without it.
- `tests/architecture/test_phase19_off_mode_imports_none_of_the_four.py` and `tests/codebase/test_import_contracts.py` pass.
- `importlinter.toml` has no `kernel.py:<number>` left in the `c06` block.
- Gates run last, on the exact tree committed.

## Related Tickets
TCK-20261018-PHASE19-OFF-MODE-RUNTIME-CHECK; #803 (adventure scorer fix); #547 (rpg decision (a)); #621.

## Related Docs
docs/plans/codebase_health/python_code_craft_roadmap.md; docs/plans/codebase_health/import_linter_evaluation.md

## Related Stored Artifacts
None.

## Related Code Areas
codebase/structure/importlinter.toml; tests/architecture/test_phase19_off_mode_imports_none_of_the_four.py; tests/codebase/test_import_contracts.py

## Assumptions / Open Questions
With `allow_indirect_imports = true` the new source catches direct imports only, which is the shape of the pre-#803 break. The runtime test stays the check for indirect paths. A grep of origin/main f5ae02e80 finds no direct import of the three forbidden packages under `src/ai/goals`; `make lint-imports` confirms it. rpg-planner proposed the source; this changes no RPG behaviour.

## Implementation Notes
Only the `c06_hot_path_not_heavy` block of `codebase/structure/importlinter.toml` changed. Each comment's location was checked against the current `src/engine/kernel.py`: the artifact repository (line 153), metric recorder, cognition recorder and decision-trace writer (lines 254-272) are all opened in `Kernel.__init__` under `obs_mode != ObservabilityMode.OFF`, and `Kernel.shutdown` closes the writer only `if self._decision_trace_writer`. The "UNENFORCED" sentence now names the runtime test and its limit (one tick on one world). `tests/codebase/test_import_contracts.py` only holds sample lint-imports output, so the renamed contract needed no test edit.

## Test Summary
Run on vCPUs 4-5 under `MemoryMax=1G`, one at a time (lead-planner go). `make lint-imports`: 17 kept, 0 broken, c06 still `KEPT (4 ignored imports)`, no stale-ignore warning. Positive control in a scratch copy on /data (removed afterwards): a direct `from src.observability.cognition import decision_trace_writer` appended to `src/ai/goals/adventure_scorer.py` makes c06 BROKEN with `src.ai.goals` as a source (15 kept, 2 broken) and leaves c06 kept without it (16 kept, 1 broken); the second broken contract in both runs is the registry layer-order contract, which the probe import itself violates. `test_phase19_off_mode_imports_none_of_the_four.py`: 7 passed. `tests/codebase/test_import_contracts.py`: 34 passed.

## Files Changed
`codebase/structure/importlinter.toml` (c06 block). Carried from the planner: the M7 batch 2 roadmap row and monitoring rows; also 5 monitoring tool rows carried from the previous batch.

## Completion Summary
The phase19 contract now names its runtime test, refers to `Kernel.__init__`/`Kernel.shutdown` instead of kernel.py line numbers, and guards `src.ai.goals` too. No `ignore_imports` edge and nothing under `src/` changed.
