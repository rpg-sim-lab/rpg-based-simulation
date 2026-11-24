---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261124-STATE-DIGEST-PROBE-SKIPS-A-SYNTHESIZED-RECORD-WHOSE-ID-WAS-REUSED
phase: open
date: 2026-11-24
tags: [testing]
---

# TCK-20261124-STATE-DIGEST-PROBE-SKIPS-A-SYNTHESIZED-RECORD-WHOSE-ID-WAS-REUSED

## Title
The state-digest probe's visited set holds ids of freed synthesized records, so a new record that reuses an id is skipped and its field paths vanish from one run to the next

## Status
OPEN

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
`tests.architecture.test_state_digest_covers_every_field::test_every_unhashed_field_is_a_reasoned_row_and_every_row_is_still_unhashed` failed once and passed on a rerun of the same sha (Dependabot #1002, compose.yaml only; run 45140116346, job 137575726100): "state.chests[].items[].properties: stale row (no longer a field path); delete it". "No longer a field path" means the path was absent from the merged results, not that it read covered. In `probe_state`, `visit()` guards with `seen = set()` of `id(o)`. A synthesized record (a chest, then its item) is installed, visited, and freed when `perturb` restores the field; its id stays in `seen`. A later synthesized record can be allocated at the same address, so `id(o) in seen` is true and the record, with every path under it, is skipped. Which address is reused depends on allocator and GC state, so the result is not fixed by the fixed samples. This is a hypothesis from reading the code; the ticket's first step is to prove it with a forced id reuse, not by waiting for a flake.

## Scope
1. A unit test in tests/architecture/test_state_digest_probe_perturb.py (or a sibling) that makes the failure deterministic: a probe over a small dataclass whose synthesized record would reuse a freed id (force it, for example by patching `synthesize` to return an object at a recycled id, or by freeing and re-allocating until ids match), and asserts every path under the second record is reported. It must fail on the current code.
2. Fix `visit()`: keep the visited objects alive for the whole probe (a list beside `seen`) so an id cannot be reused while it is in `seen`, or key `seen` on objects, not ids. Live state objects are unchanged.
3. Run tests/architecture/test_state_digest_covers_every_field.py and test_state_digest_probe_perturb.py. Report every row whose verdict changes. A row that becomes stale or a new unhashed path is a changed gate expectation: do not edit the allowlist, send it to testing-planner for the owner.

## Out of Scope
- Any src/ change and any allowlist edit.
- Changing SAMPLES.

## Acceptance Criteria
1. The new test fails on origin/main and passes with the fix.
2. The two architecture digest test files pass on origin/main plus this change, with no verdict changes, or the changes are listed in the PR body for the owner.
3. If the id-reuse cause is disproved in step 1, the implementer stops and reports to testing-planner with what the failing run's path set lacked, before any fix.

## Related Tickets
- TCK-20261123-STATE-DIGEST-PROBE-SET-PERTURBATION-MUST-CHANGE-THE-SET
- TCK-20261122-STATE-DIGEST-PROBE-PERTURBS-FIXED-ARITY-TUPLES-IN-PLACE

## Related Docs
- docs/engine/deterministic_execution.md (the canonical hash)

## Related Stored Artifacts
None.

## Related Code Areas
- tests/architecture/state_digest_probe.py (`probe_state`, `visit`)
- tests/architecture/test_state_digest_covers_every_field.py
- tests/architecture/state_digest_allowlist.yaml (read only)

## Assumptions / Open Questions
- The flake could have another cause (an unordered iteration choosing `items[:1]`, which is list order and fixed, so unlikely). Id reuse is the lead hypothesis only.
- A full probe run builds 60-tick worlds: no heavy run without lead-planner's GO.

## Durable state, lifecycle and clocks
None. Test-only change.

## Implementation Notes
Pytest on taskset -c 0-3, --basetemp on /data, no uv sync, no bare git stash.

## Test Summary
Not yet run.

## Files Changed
None yet.

## Completion Summary
Open.
