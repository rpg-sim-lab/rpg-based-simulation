---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261109-AN-ADVISORY-GUARD-LISTS-TESTS-WHOSE-SUBJECT-SYSTEM-THE-PIPELINE-NEVER-RUNS
phase: done
date: 2026-11-09
tags: [testing, regression]
---

# TCK-20261109-AN-ADVISORY-GUARD-LISTS-TESTS-WHOSE-SUBJECT-SYSTEM-THE-PIPELINE-NEVER-RUNS

## Title
An advisory guard lists src/systems classes the authoritative pipeline never reaches, and the tests that import them without a stated reason, so a fix's regression test is seen to prove a path that does not run

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Owner go on issue #715, comment 6736269441 (item 2, "(2) advisory unwired-system test guard, riding digest-light"), on proposal 6736224900.

Found case: fused_strategic_pass's pursuit regression test exercises `StrategicRedirectionSystem.enforce`. That class is only re-exported (src/systems/redirection.py) and is not wired in src/engine/pipeline.py, so the test suggests coverage of the live path that it doesn't give.

## Scope
- A tool in tools/test_architecture/ (e.g. unwired_subject_check.py), report only, in the style of marker_check.py. It:
  1. Computes the wired set: systems the authoritative pipeline reaches. Start from what src/engine/pipeline.py's refinement phases call, computed from the code at run time with the same source tools/perf/phase_inventory.py uses, not from docs/performance/phase_inventory.md, whose generated commit can be stale. Then close over static imports and calls from those modules into src/systems/**.
  2. Lists src/systems/** classes and functions outside the wired set, each with how it is referenced (import-only, re-export only, test-only).
  3. Lists tests that import an unwired symbol, unless the test carries `pytest.mark.unwired_subject("<reason>")` (registered in pyproject markers and in docs/testing/test_taxonomy.md if that section governs it).
- A small test in tests/architecture/ that runs the tool on a synthetic package: a wired system, a re-export-only system, and an import-only test with and without the marker. It asserts the report. Plus one run on the real tree, asserting only that the tool completes and that StrategicRedirectionSystem is in the unwired list (the found case).
- Output: a readable text report plus `--json`. Exit code 0 always (advisory).

## Out of Scope
- Any CI block. Making it blocking is a later decision, after a run shows the false-positive rate (indirect calls and registry dispatch will produce some).
- Marking or rewriting existing tests, or deleting unwired systems (that's rpg-planner's call per case).
- Diff coverage (item 3, deferred).

## Acceptance Criteria
- [x] AC1: On the synthetic package, the tool reports exactly the re-export-only system as unwired, and exactly the unmarked importing test.
- [x] AC2: On the real tree, StrategicRedirectionSystem is reported unwired, together with the test(s) that import it. The full real-tree report is attached to the PR, counted (unwired symbols, flagged tests), with a hand-checked sample of 5 entries stating true or false positive.
- [x] AC3: The wired set is derived from pipeline.py at run time. A test proves that adding a call in a synthetic pipeline moves a system into the wired set.
- [x] AC4: Exit code is always 0. No CI job fails on its output.
- [x] AC5: The `unwired_subject` marker is registered, and test_marker_vocabulary.py still passes.

## Related Tickets
- TCK-20261109-FUSED-STRATEGIC-PASS-FAST-PATH-IS-PINNED-BRANCH-BY-BRANCH-AND-AGAINST-THE-SLOW-PATH (C)
- TCK-20261109-THE-FAST-STRATEGIC-PATH-SENDS-AN-ENTITY-TARGET-PURSUER-HOME-WITH-ITS-ITEMS (A: its regression test must go through the wired path)

## Related Docs
- docs/engine/authoritative_pipeline.md
- docs/performance/phase_inventory.md
- docs/testing/test_taxonomy.md

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20261109-AN-ADVISORY-GUARD-LISTS-TESTS-WHOSE-SUBJECT-SYSTEM-THE-PIPELINE-NEVER-RUNS/ (plan, investigation, test_plan, real_tree_report.txt)

## Related Code Areas
- src/engine/pipeline.py, src/systems/**
- tools/test_architecture/, tests/architecture/

## Assumptions / Open Questions
- Rides the digest-light PR as its own ticket (owner 6736269441). Not built until that PR is cued, unless testing-planner says otherwise.
- If the reachability closure turns out unsound for registry-dispatched systems (called by name), list them as "dispatch-reached" rather than wired or unwired, and say so in the report.

## Implementation Notes
Reachability follows names that are used, not imports (a package __init__ would otherwise reach everything); __all__ and unused imports are re-exports. Roots: src/engine/pipeline.py (phase_inventory.inventory_pipeline run on it for the run_phase count); --also-root adds more. Classes: wired, dispatch-reached, unwired (with how referenced). Marker registered in pyproject; one paragraph in docs/testing/test_taxonomy.md (the marker is outside the domain/level vocabulary block, so test_marker_vocabulary is unchanged). Real tree: 63 public src/systems symbols, 29 wired, 15 dispatch-reached, 19 unwired, 26 test files flagged; sample of 5 hand-checked in investigation.md (4 true positives; LoyaltyDriftService has a real caller outside the pipeline). Nothing is marked or rewritten.

## Test Summary
tests/architecture/test_unwired_subject_check.py 8 passed (synthetic, wired-set move, unused import, dispatch-reached, extra root, attribute chain, exit code and JSON, real tree); tests/unit/tools/test_marker_vocabulary.py passed. 11 passed together.

## Files Changed
tools/test_architecture/unwired_subject_check.py (new); tests/architecture/test_unwired_subject_check.py (new); pyproject.toml (marker); docs/testing/test_taxonomy.md; stored artifacts.

## Completion Summary
The advisory exists and finds the case: StrategicRedirectionSystem is re-export only, with 5 importing tests flagged. Exit code is always 0 and no CI job reads it. Making it blocking is a later decision after a false-positive review of the 4 'used only by src module(s) the pipeline does not reach' entries.
