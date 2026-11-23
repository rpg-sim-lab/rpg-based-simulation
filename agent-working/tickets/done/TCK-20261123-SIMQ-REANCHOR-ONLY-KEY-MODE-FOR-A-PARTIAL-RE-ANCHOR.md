---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261123-SIMQ-REANCHOR-ONLY-KEY-MODE-FOR-A-PARTIAL-RE-ANCHOR
phase: done
date: 2026-11-23
tags: [testing]
---

# TCK-20261123-SIMQ-REANCHOR-ONLY-KEY-MODE-FOR-A-PARTIAL-RE-ANCHOR

## Title
simq_reanchor gets an `--only <key>` partial mode so two grade anchors can be re-pinned from their own two audit-mode runs without a measurement of all 81 keys

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
`tools/test_architecture/simq_reanchor.py::reanchor` loops over every run key of the fixture (81 keys, 810 pillar rows) and calls `audit_values` for each, so a re-anchor of two keys exits 2 (REFUSED) at the first unmeasured key; `--exclude` and `--prior-rows` do not fill missing keys. #995's owner-approved re-pin of urban_political s42 1000t SOCIAL and unit_selfmodel_pilot s42 1000t ECONOMY (#715 after 7097520404) needs a sanctioned partial mode. Splicing earlier rows for the other 79 keys was rejected: it mixes shas in one provenance table. Owner yes: #715 7097749295 ("File the --only tool change"); method review by testing-planner (baseline_change_policy.md rule 12) sent to lead-planner on 2026-11-23.

## Scope
1. `--only <run_key>` (repeatable) on `python -m tools.test_architecture.simq_reanchor`. Keys not named are copied from the committed fixture byte-for-byte, need no rows, and appear in no table row.
2. Every named key still needs the full pair: two isolated runs, both audit_mode True and signals_zeroed True, exit 0, identical on every pillar and overall. No override.
3. A named key that is not in the fixture is refused (exit 2, nothing written). A named key with a missing or non-identical pair is refused as today.
4. `--exclude` works inside a named key; an exclusion that names an unnamed key is refused as an unknown exclusion (the key is not part of this run).
5. `--prior-rows`, `--score-overrides` and `--ruling-table` apply to the named keys only; a named key needs its pair in the prior rows when `--prior-rows` is given.
6. The output fixture keeps the layout (`indent=2`, final newline, metadata keys first, run keys and pillars in their existing order); the unnamed keys' bytes are identical to the committed file.
7. The module docstring and docs/plans/test_architecture/reference/baseline_change_policy.md say how a partial re-anchor is recorded (the PR names the sha, that it was measured on a git archive of a branch commit when so, and the moved rows).
8. Unit tests in tests/unit/tools/test_simq_reanchor.py: only the named keys change; an unnamed key is byte-identical; an unknown key is refused; a named key with one run is refused; --exclude inside a named key keeps that row; an exclusion on an unnamed key is refused; default behaviour (no --only) is unchanged.

## Out of Scope
- Running the measurement or the re-pin itself (#995's PR, rpg).
- The other re-anchor tools, and any change to the pair-identity checks.

## Acceptance Criteria
1. Without `--only` every existing test and output is unchanged.
2. With `--only` the two named keys re-anchor and the other 79 keys' bytes in the fixture are identical.
3. The documented command is runnable as: `--rows <rows.jsonl for the named keys> --fixture tests/simulation_quality/fixtures/grade_anchors.json --out new.json --table table.tsv --only urban_political_seed42_1000t --only unit_selfmodel_pilot_seed42_1000t [--prior-rows ...] [--ruling-table ...]`.
4. testing-planner reviews the PR before the owner's push yes; it merges before #995's re-pin.

## Related Tickets
- TCK-20261014-SIMQ-SINGLE-REANCHOR-ON-BASELINE-V1
- TCK-20261014-SIMQ-COMPARE-TOOLS-REFUSE-RUNS-NOT-RECORDED-HOST-INDEPENDENT
- TCK-20261011-SIMQ-GRADE-ANCHORS-RUN-UNDER-AUDIT-MODE

## Related Docs
- docs/plans/test_architecture/reference/baseline_change_policy.md
- docs/testing/regression_policy.md (11b)

## Related Stored Artifacts
None.

## Related Code Areas
- tools/test_architecture/simq_reanchor.py
- tests/unit/tools/test_simq_reanchor.py

## Assumptions / Open Questions
- The anchors are only ever written by this tool (never by hand).

## Durable state, lifecycle and clocks
None. The tool writes a fixture and a table.

## Implementation Notes
Pytest on taskset -c 0-3, --basetemp on /data, no uv sync, no simulation run. No bare git stash.

## Test Summary
tests/unit/tools/test_simq_reanchor.py: 37 passed (taskset -c 0-3), 10 new for items 1-6 and 8 (named-only change, unnamed byte identity, unknown key, one-run named key, full audit-mode pair, exclusion inside and on an unnamed key, prior rows, no --only unchanged, CLI repeatable flag, real fixture). Four mutations (drop the unnamed copy, the unnamed-exclusion refusal, the unknown-key refusal, the meta-key guard) each fail a test. One-off on the real fixture (not committed, synthetic rows for the two keys of AC3's command, no simulation): 81 keys; the other 79 keys' values and their text blocks in the written file are byte-identical, line count 3752 unchanged, table rows only for the two named keys.

## Files Changed
tools/test_architecture/simq_reanchor.py, tests/unit/tools/test_simq_reanchor.py, docs/plans/test_architecture/reference/baseline_change_policy.md (rule 7), this ticket and its stored artifacts.

## Completion Summary
`--only <run_key>` (repeatable) and `reanchor(only=...)` re-pin only the named keys from their own full audit_mode pairs; unnamed keys are copied unchanged with no rows or table lines. The default is unchanged. The partial re-anchor is recorded as docstring and policy rule 7 say. The re-pin itself is #995's.
