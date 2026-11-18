---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261118-STATEFUL-PROPERTY-PILOT-FOR-RECORD-LIFECYCLES
phase: open
date: 2026-11-18
tags: [testing, simulation-quality]
---

# TCK-20261118-STATEFUL-PROPERTY-PILOT-FOR-RECORD-LIFECYCLES

## Title
Pilot a Hypothesis stateful-property test for one durable-record lifecycle (testing-planner ask)

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P3

## Request Summary
Owner decision on #715 (2026-11-18, via lead-planner): route a stateful property-test pilot to testing-planner. `docs/testing/test_taxonomy.md` §6 already sanctions the "stateful property" technique ("invariants over action sequences"), and `hypothesis>=6.0.0` is declared in `pyproject.toml`, but no file under `tests/`, `src/` or `tools/` imports it (checked 2026-11-18). Several historical defects survived green tests because tests ran one pass or one transition: the resolve-blocker project re-created every 80 ticks, the suspended project that never exited (#954), the stale `last_failure_reason`, and the `moved_recently` latch. Source: `agent-working/stored_artifacts/TCK-20261118-SIM-ENGINEERING-SKILLS-RESEARCH-PROPOSAL/` (`defect_set.md`, `research.md`, `proposal.md`).

## Scope
1. Pick ONE lifecycle area (suggested: the project record states and slot cap, or blocker inference) with testing-planner and the rule owner; confirm the rule text it asserts, do not invent semantics.
2. Write one `RuleBasedStateMachine` (Hypothesis) with: a rule that applies a pass twice in a row, an invariant that every non-terminal state has a reachable exit, and an assertion on the value after a successful step. Seed handling and determinism: settle it before relying on it (the Hypothesis stateful docs do not cover seeds; check the "replaying failed tests" pages).
3. Show it fails on the pre-fix behaviour: run it against the commit before each of the covered fixes (or a faithful reintroduction on a scratch branch) and record that it finds the defect and prints a short reproducing sequence.
4. Report cost (runtime, flakiness, fixture effort) and a recommendation on spreading the technique.

## Out of Scope
- Metamorphic testing (gated on parked long-run determinism per `test_taxonomy.md` §6).
- Rewriting existing tests, or changing simulation behaviour.
- More than one lifecycle area.

## Acceptance Criteria
- The test is placed per `test_taxonomy.md` §8 with the right markers and runs in the scoped test command CI uses.
- Demonstrated failure on pre-fix behaviour for at least two of the named defects, recorded in the ticket.
- Known Hypothesis limits (invariants cannot read bundles; strategies cannot see machine state except via `runner()`/`data()`) are respected or worked around and noted.
- Runtime within the repo's non-slow budget, or marked with the right marker.

## Related Tickets
- TCK-20261118-SIM-ENGINEERING-SKILLS-RESEARCH-PROPOSAL
- TCK-20261118-ARCH-REVIEWER-LIFECYCLE-TIME-CHECKLIST-EVAL (sibling)

## Related Docs
- docs/testing/test_taxonomy.md §6, §7, §9

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20261118-SIM-ENGINEERING-SKILLS-RESEARCH-PROPOSAL/

## Related Code Areas
- tests/ (placement per taxonomy), the chosen lifecycle's source module

## Assumptions / Open Questions
- Owner: testing-planner (tests/architecture/** routes there; placement may differ). The seat was not running when this was filed.
- Which lifecycle area to pilot is open.

## Implementation Notes
Hypothesis stateful limits and API were read from https://hypothesis.readthedocs.io/en/latest/stateful.html.

## Test Summary
(filled at close)

## Files Changed
(filled at close)

## Completion Summary
(filled at close)
