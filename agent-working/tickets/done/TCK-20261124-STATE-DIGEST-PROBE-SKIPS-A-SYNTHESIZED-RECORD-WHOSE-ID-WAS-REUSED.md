---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261124-STATE-DIGEST-PROBE-SKIPS-A-SYNTHESIZED-RECORD-WHOSE-ID-WAS-REUSED
phase: done
date: 2026-11-24
tags: [testing]
---

# TCK-20261124-STATE-DIGEST-PROBE-SKIPS-A-SYNTHESIZED-RECORD-WHOSE-ID-WAS-REUSED

## Title
The state-digest probe's visited set holds ids of freed synthesized records, so a new record that reuses an id is skipped and its field paths vanish from one run to the next

## Status
DONE

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
Step 1 (prove first): the new test `test_a_synthesized_record_that_reuses_a_freed_records_id_is_still_probed` fails on origin/main cef537d29: the probe over a holder with two `List[Outer]` fields, where each Outer holds a `List[Rec]`, reports `state.first[].items[].a` but not `state.second[].items[].a` once the freed first Rec's id is handed to the second. The id reuse is modelled, not forced through the allocator: forcing a real address reuse was tried and does not work (the freed block is taken by another allocation before the next record, and 300000 same-type allocations never matched), so the test patches `id` in the probe module with a recycler whose ids are unique among live records and are reissued after a record is freed (the one allocator behaviour the bug needs). With the fix it passes. It proves that an id-keyed `seen` set loses paths on reuse; it does not prove that is what failed run 45140116346, which would need the allocator to reuse an address in that run.
Fix: `visit()` appends each visited object to a `visited` list that lives for the whole probe, beside the id-keyed `seen`. Live state objects are unchanged.
Run on `taskset -c 0-3`: test_state_digest_probe_perturb.py 15 passed (1 new), test_state_digest_covers_every_field.py 11 passed; 26 together. No verdict changed, no allowlist edit.

## Files Changed
tests/architecture/state_digest_probe.py (`visited` list in `probe_state`), tests/architecture/test_state_digest_probe_perturb.py (one test, a recycling-id helper and three small dataclasses), this ticket and its artifacts.

## Completion Summary
The probe keeps every visited object alive for the whole probe, so an id in `seen` cannot be reissued to another record. The failing test is deterministic and fails without the fix. Whether this was the cause of the one flaky CI failure is a hypothesis the test supports but cannot confirm.
