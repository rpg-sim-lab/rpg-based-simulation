---
status: active
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261109-ONE-MUTATION-RUN-MEASURES-HOW-MANY-INJECTED-FAULTS-THE-FUSED-STRATEGIC-PASS-TESTS-CATCH
phase: open
date: 2026-11-09
tags: [testing]
---

# TCK-20261109-ONE-MUTATION-RUN-MEASURES-HOW-MANY-INJECTED-FAULTS-THE-FUSED-STRATEGIC-PASS-TESTS-CATCH

## Title
One report-only mutmut run measures how many injected faults in fused_strategic_pass its current tests catch, recorded as a mutation baseline under tests/mutation/baselines/

## Status
OPEN

## Tier
hotfix

## Type
chore

## Priority
P2

## Request Summary
Owner go on issue #715, comment 6736269441 (item 2, E): one mutmut run on fused_strategic_pass, in a scratch venv and a git-archive copy, report only. It runs only in a heavy-slot gap named by rpg-planner. The baseline JSON rides the digest-light PR. This is the same method as the two existing mutation baselines (src_core_conservation, src_systems_social_appraisal_v1).

## Scope
- Make a scratch copy with `git archive` of an exact origin/main sha, outside the repo, and a scratch venv with mutmut. mutmut is not added to the project's dependencies.
- Mutate src/systems/strategic_systems/intelligence.py and keep only the mutants inside fused_strategic_pass (its def line through its last line on that sha). Record the line range.
- Test set: the test files that call fused_strategic_pass (12 on main at the time of filing), plus tests/unit/strategic/. List them in the baseline.
- Run single-process, with nothing else heavy on the host.
- Record the result as tests/mutation/baselines/src_systems_strategic_intelligence_fused_v1.json, following the existing baselines' schema (schema_version, kind mutation_baseline, target path, sha256 and lines, run kind/started/finished/runtime/source_sha/source_note, counts, survivors by line). Kill rate = killed / (killed + survived); timeouts and incompetent mutants are counted separately.
- The baseline is a report: survivors are listed, not fixed.

## Out of Scope
- Fixing survivors, adding tests (that is the C ticket), any CI wiring of mutation testing, any src/ change.
- A re-run after C lands. That is optional evidence on C's PR, recorded as a `_v2` file if done, with the same method.

## Acceptance Criteria
- [ ] AC1: The baseline JSON exists, follows the existing baselines' schema, and names the exact source sha, the function line range, the test list, the counts, the runtime, and survivors by line.
- [ ] AC2: The run happened inside the gap rpg-planner named ("HOST FREE for E"). Start and finish were messaged to rpg-planner. The wall time was at most 90 min; if it ran longer, it was stopped and the partial result recorded as `run.kind: partial` with the reason.
- [ ] AC3: No change to pyproject.toml, requirements, or any file outside tests/mutation/baselines/ and this ticket. The scratch copy and venv are removed after the run.

## Related Tickets
- TCK-20261109-FUSED-STRATEGIC-PASS-FAST-PATH-IS-PINNED-BRANCH-BY-BRANCH-AND-AGAINST-THE-SLOW-PATH (C; the tests this measures before and after)

## Related Docs
- docs/plans/test_architecture/ (mutation suite)

## Related Stored Artifacts
- tests/mutation/baselines/src_systems_social_appraisal_v1.json (method and schema reference)

## Related Code Areas
- src/systems/strategic_systems/intelligence.py
- tests/mutation/baselines/

## Assumptions / Open Questions
- The gap: after lane C's 7 hardening runs and before lane A's flight-fix equivalence cell. If the gap closes before the start, the next one is between the flight fix's arm 1 and arm 2 (rpg-planner, 2026-11-09).
- mutmut's version is pinned in the baseline's source_note.

## Implementation Notes
(implementer)

## Test Summary
(implementer)

## Files Changed
(implementer)

## Completion Summary
(implementer)
