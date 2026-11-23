---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261123-STATE-DIGEST-PROBE-SET-PERTURBATION-MUST-CHANGE-THE-SET
phase: open
date: 2026-11-23
tags: [testing]
---

# TCK-20261123-STATE-DIGEST-PROBE-SET-PERTURBATION-MUST-CHANGE-THE-SET

## Title
The state-digest probe changes a set or frozenset field by a union that can equal the original, so a hashed enum-set field reads as unhashed

## Status
OPEN

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
`perturb()` in tests/architecture/state_digest_probe.py grows a set or frozenset with `type(value)(set(value) | {elem})`, where `elem = synthesize(element hint)`. For an enum element `synthesize` returns the first member, and the synthesized record already holds that member, so the union equals the original and the digest cannot move: the field reads "unhashed". Reported by rpg-planner on PR #996: `state.entities[].cognition.memory.navigation.records[].need_services` (FrozenSet[NeedService], hashed through sorted(value)); the same would hit `GiveUpRecord.need_services` that #996 adds. The same shape as TCK-20261122-STATE-DIGEST-PROBE-PERTURBS-FIXED-ARITY-TUPLES-IN-PLACE: a probe artefact, not a digest gap. #996's route is no allowlist row and no type change.

## Scope
1. In the set/frozenset branch of `perturb()`: when the union equals the original, produce a different set by adding a member the set does not hold (for an enum, another member of the enum) and, if there is none, by removing one element. A set whose union already differs (the common case, including an empty set) is unchanged.
2. Keep the second return value (the inserted element, used to probe its own fields) when an element is added, and None when one is removed.
3. Unit tests in tests/architecture/test_state_digest_probe_perturb.py: a FrozenSet[enum] already holding the first member changes; a single-member enum set changes by removal; an empty set grows by one; an ordinary non-colliding set keeps its old behaviour.
4. Run tests/architecture/test_state_digest_covers_every_field.py. Report every row whose verdict changes. An allowlist row that becomes stale is a changed gate expectation: do not edit the allowlist, send it to testing-planner for the owner.

## Out of Scope
- Any src/ change (no type change in #996) and any allowlist row.

## Acceptance Criteria
1. The probe moves the digest for a hashed FrozenSet[enum] field already holding the first enum member.
2. The new probe tests pass, and fail against the old union.
3. The architecture digest test file passes on origin/main plus this change, and on #996's head once this merges.
4. The PR body lists every changed verdict (or says none). It merges before #996.

## Related Tickets
- TCK-20261122-STATE-DIGEST-PROBE-PERTURBS-FIXED-ARITY-TUPLES-IN-PLACE (the earlier probe fix)
- #996 (rpg-stalemate-nav)

## Related Docs
- docs/engine/deterministic_execution.md (the canonical hash)

## Related Stored Artifacts
None.

## Related Code Areas
- tests/architecture/state_digest_probe.py
- tests/architecture/test_state_digest_probe_perturb.py
- tests/architecture/test_state_digest_covers_every_field.py
- tests/architecture/state_digest_allowlist.yaml (read only)

## Assumptions / Open Questions
- A removal changes the digest only if the field is hashed through its elements (sorted(value)); an unhashed set stays unhashed under either change.

## Durable state, lifecycle and clocks
None. Test-only change.

## Implementation Notes
Pytest on taskset -c 0-3, --basetemp on /data, no uv sync, no bare git stash.

## Test Summary
Not run yet.

## Files Changed
None yet.

## Completion Summary
Open.
