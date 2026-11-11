---
status: active
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261109-AN-ADVISORY-GUARD-LISTS-TESTS-WHOSE-SUBJECT-SYSTEM-THE-PIPELINE-NEVER-RUNS
phase: open
date: 2026-11-09
tags: [testing, regression]
---

# TCK-20261109-AN-ADVISORY-GUARD-LISTS-TESTS-WHOSE-SUBJECT-SYSTEM-THE-PIPELINE-NEVER-RUNS

## Title
An advisory guard lists src/systems classes the authoritative pipeline never reaches, and the tests that import them without a stated reason, so a fix's regression test is seen to prove a path that does not run

## Status
OPEN

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
- [ ] AC1: On the synthetic package, the tool reports exactly the re-export-only system as unwired, and exactly the unmarked importing test.
- [ ] AC2: On the real tree, StrategicRedirectionSystem is reported unwired, together with the test(s) that import it. The full real-tree report is attached to the PR, counted (unwired symbols, flagged tests), with a hand-checked sample of 5 entries stating true or false positive.
- [ ] AC3: The wired set is derived from pipeline.py at run time. A test proves that adding a call in a synthetic pipeline moves a system into the wired set.
- [ ] AC4: Exit code is always 0. No CI job fails on its output.
- [ ] AC5: The `unwired_subject` marker is registered, and test_marker_vocabulary.py still passes.

## Related Tickets
- TCK-20261109-FUSED-STRATEGIC-PASS-FAST-PATH-IS-PINNED-BRANCH-BY-BRANCH-AND-AGAINST-THE-SLOW-PATH (C)
- TCK-20261109-THE-FAST-STRATEGIC-PATH-SENDS-AN-ENTITY-TARGET-PURSUER-HOME-WITH-ITS-ITEMS (A: its regression test must go through the wired path)

## Related Docs
- docs/engine/authoritative_pipeline.md
- docs/performance/phase_inventory.md
- docs/testing/test_taxonomy.md

## Related Stored Artifacts
- none

## Related Code Areas
- src/engine/pipeline.py, src/systems/**
- tools/test_architecture/, tests/architecture/

## Assumptions / Open Questions
- Rides the digest-light PR as its own ticket (owner 6736269441). Not built until that PR is cued, unless testing-planner says otherwise.
- If the reachability closure turns out unsound for registry-dispatched systems (called by name), list them as "dispatch-reached" rather than wired or unwired, and say so in the report.

## Implementation Notes
(implementer)

## Test Summary
(implementer)

## Files Changed
(implementer)

## Completion Summary
(implementer)
