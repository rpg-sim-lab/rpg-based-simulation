---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261018-PHASE19-OFF-MODE-RUNTIME-CHECK
phase: done
date: 2026-10-18
tags: [testing, architecture, observability]
---

# TCK-20261018-PHASE19-OFF-MODE-RUNTIME-CHECK

## Title
A runtime test that an OFF-mode kernel imports none of the four heavy observability modules the phase19 import-linter ignores rely on

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Filed by codebase per owner decision on #547 (2026-10-18, "Accept gap + follow-up"); owned by testing-planner. The test lives under `tests/architecture/`, which `route.py` shows as split rpg/testing, so it is testing's to implement.

The import-linter contract `engine and the three hot observability modules do not import the heavy analyzers (phase19)` ignores four edges from `src/engine/kernel.py`. rpg-planner allowed them on #547 (decision (a)) on a condition: every edge is a function-local import inside an `obs_mode != ObservabilityMode.OFF` branch, so an OFF-mode kernel imports none of the four modules, and an edge that moves out of the guard becomes a violation. Nothing enforces that condition today: `tests/architecture/test_phase19_observability_boundaries.py` is a static scan that never matches `src.observability...` and has no notion of OFF mode. Until this ticket lands the condition is UNENFORCED (the `importlinter.toml` phase19 comment says so).

## Scope
A runtime test, in a FRESH subprocess interpreter, that:
1. builds a `Kernel` with `ObservabilityMode.OFF` from the compiled `sandbox_world`, runs one `tick_once` and `shutdown`;
2. asserts that none of `src.observability.reporting.artifact_repository`, `src.observability.reporting.metric_recorder`, `src.observability.cognition.recorder` or `src.observability.cognition.decision_trace_writer` is in `sys.modules`.

Parity proof (testing condition 2), two parts:
- an injected unguarded top-level import of one of the four in `kernel.py` (in a scratch copy, never in the repo) makes the test fail;
- a control run with observability ON shows the four modules DO load, so the test can see them.

## Out of Scope
- Adding or widening any `ignore_imports` entry in `codebase/structure/importlinter.toml`.
- Editing `src/`.
- Changing `test_phase19_observability_boundaries.py` beyond what testing decides (it stays as it is unless testing chooses otherwise).

## Acceptance Criteria
- The test exists under `tests/architecture/`, runs in a fresh interpreter, and passes on `main`.
- The injected-import parity run fails the test; the ON-mode control run loads all four modules.
- Codebase follow-on, after the test lands: update the `importlinter.toml` phase19 comment to name the test (codebase-implementer, one small commit).

## Related Tickets
- TCK-20261005-IMPORT-LINTER-FLIP-AND-TEST-RETIREMENT
- TCK-20261004-IMPORT-LINTER-ADOPTION

## Related Docs
- docs/plans/codebase_health/handoffs/handoff_to_testing.md
- docs/plans/codebase_health/handoffs/handoff_to_rpg.md
- codebase/structure/importlinter.toml (phase19 contract)
- #547 (rpg's (a) answer; owner decision 2026-10-18)

## Related Stored Artifacts
None.

## Related Code Areas
- tests/architecture/test_phase19_observability_boundaries.py
- src/engine/kernel.py (function-local imports behind the OFF guard)
- codebase/structure/importlinter.toml

## Assumptions / Open Questions
- Owner: testing-planner (implementer: testing-implementer). Filed by codebase, not by testing.
- Whether the new test replaces the static phase19 hot-path test or sits beside it is testing's call.
- The kernel line numbers in the toml comments drift; the test must not depend on them.

## Implementation Notes
Test: `tests/architecture/test_phase19_off_mode_imports_none_of_the_four.py`. A fresh subprocess builds a Kernel from sandbox_world (seed 42, PROD_SMALL), runs one tick_once and shutdown, reports the kernel's resolved obs mode (asserted equal to the requested mode) and which of the four modules are in sys.modules. First run on main 6fdfdf555 failed for recorder and decision_trace_writer: adventure_scorer.py:10 loaded the cognition package during world compile (a path the linter does not cover). testing-planner held the ticket; rpg-planner fixed src (PR #803, 0bba1ff7d); rerun passed after merging main. Stated limit: one tick on sandbox_world does not cover imports reached only on later ticks or other worlds. The assertion was never narrowed.

## Test Summary
7 passed (OFF none loaded; LIGHT control loads all four; injected unguarded import caught for each of the four; module list equals the four c06 kernel ignore_imports edges).

## Files Changed
tests/architecture/test_phase19_off_mode_imports_none_of_the_four.py (new); this ticket and its stored artifacts.

## Completion Summary
An OFF-mode kernel imports none of the four heavy observability modules, now enforced at runtime in a fresh interpreter, with an ON-mode control and a per-module injected-import parity proof. Gaps stated: one tick on one world; the codebase follow-on (name this test in the importlinter.toml phase19 comment, whose kernel.py line numbers have drifted) is not in this change and stays with testing-planner. Not pushed: pushing and merging need the owner's separate yes.
