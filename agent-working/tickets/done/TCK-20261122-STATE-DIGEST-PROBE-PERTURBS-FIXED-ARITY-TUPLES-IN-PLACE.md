---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261122-STATE-DIGEST-PROBE-PERTURBS-FIXED-ARITY-TUPLES-IN-PLACE
phase: done
date: 2026-11-22
tags: [testing]
---

# TCK-20261122-STATE-DIGEST-PROBE-PERTURBS-FIXED-ARITY-TUPLES-IN-PLACE

## Title
The state-digest probe changes an element of a fixed-arity tuple field instead of appending one, so an in-type field that is hashed is no longer reported unhashed

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
`perturb()` in tests/architecture/state_digest_probe.py grows every tuple with `value + (elem,)`. For a declared fixed-arity field such as `GiveUpRecord.anchor: Tuple[int, int]` the append is out of type: `to_canonical` writes both declared coordinates, so the hash does not move and the field reads "unhashed". PR #996 is red on `test_every_unhashed_field_is_a_reasoned_row_and_every_row_is_still_unhashed` for `state.entities[].navigation.giveup_records[].anchor`. A run at F2's code confirmed that in-type changes (4,5)->(5,5) and (4,5)->(4,6) move `get_hash`, and (4,5,1) does not. Owner: relaunch testing-implementer for this route, no stopgap allowlist row (#715, via lead-planner). Rule from rpg-designer: the red is a probe artefact, not a src gap.

## Scope
1. In `perturb()`, when the hint is a fixed-arity tuple (`typing.get_args` has no `Ellipsis`), return a copy with one element changed in place, using the element's own hint at that position (reuse `perturb` on the element). Variadic `Tuple[X, ...]` and bare tuples keep the append.
2. A probe unit test: a fixed-arity tuple keeps its length and differs in one element; a variadic tuple grows by one.
3. Run the architecture digest test file. Report every allowlist row it now shows as stale (a fixed-arity field that turns out hashed). Do not edit the allowlist: each such row is a changed gate expectation and goes to the owner through lead-planner.

## Out of Scope
- Any allowlist row (no stopgap row for the anchor).
- src/ (no `to_canonical` change).
- F2's own pin test (tests/unit/strategic/test_giveup_record_digest.py, lands with #996).

## Acceptance Criteria
1. An in-type anchor field no longer reads unhashed; the digest test file passes on origin/main plus this change, and on #996's head once merged.
2. The probe unit test passes and fails against the old append.
3. The PR body lists every row whose verdict changed (or says none).
4. Merges before #996.

## Related Tickets
- #996 (F2, red until this lands)

## Related Docs
- docs/engine/deterministic_execution.md (the canonical hash)

## Related Stored Artifacts
None.

## Related Code Areas
- tests/architecture/state_digest_probe.py
- tests/architecture/test_state_digest_covers_every_field.py
- tests/architecture/state_digest_allowlist.yaml (read only)

## Assumptions / Open Questions
- Which allowlist rows are fixed-arity tuples is not known read-only; the run lists them.

## Durable state, lifecycle and clocks
None. Test-only change.

## Implementation Notes
Pytest on `taskset -c 0-3`, --basetemp on /data, no `uv sync` on the shared .venv.

## Test Summary
New tests/architecture/test_state_digest_probe_perturb.py: 7 pass; against the old append 3 of them fail (fixed-arity length, optional fixed-arity, no-changeable-position). tests/architecture/test_state_digest_covers_every_field.py: 11 passed on origin/main 67c653219 plus this change (taskset -c 0-3). No allowlist row changed verdict: none. #996's anchor field is not on origin/main, so AC1's #996-head half is not checked here.

## Files Changed
tests/architecture/state_digest_probe.py (`_perturb_fixed_arity`, called from `perturb`), tests/architecture/test_state_digest_probe_perturb.py (new), this ticket.

## Completion Summary
`perturb` changes one element in place for a fixed-arity tuple hint (Optional stripped, no Ellipsis, hint length equals value length) using that position's own hint; variadic, bare and mismatched-length tuples keep the append.
