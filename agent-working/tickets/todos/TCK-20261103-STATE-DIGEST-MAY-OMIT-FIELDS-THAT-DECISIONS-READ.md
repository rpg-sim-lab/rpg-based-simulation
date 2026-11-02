---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20261103-STATE-DIGEST-MAY-OMIT-FIELDS-THAT-DECISIONS-READ
phase: open
date: 2026-11-03
tags: []
---

# TCK-20261103-STATE-DIGEST-MAY-OMIT-FIELDS-THAT-DECISIONS-READ

## Title
The canonical state digest may leave out fields that decisions read: a per-field mechanical test first, counts before any scheme change

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
Raised by rpg-planner-ubuntu from a first text check at 0e7b1030c, relayed by lead-planner-u24 on 2026-11-03. It is not a verified audit, and rpg-planner has not checked the list. The ubuntu lead and rpg-designer both support a ticket, whatever the two wrapper runs on ubuntu find.

Candidates outside `to_canonical_dict`:
- IdentityComponent: cooldowns, traits, craft_target, veterancy_points, latest_intent_results.
- EntityState: stamina, timeline.

Reported decision reads:
- identity.cooldowns: src/engine/tactical.py:704, src/engine/domain/skill_actions.py:48.
- identity.traits: src/systems/social_systems/appraisal.py:146.
- identity.latest_intent_results: src/systems/strategic_systems/work_queue.py:56.
- .stamina: 14 files.
- craft_target and veterancy_points still need a read.

Nested types and aliases are not covered by that check.

Why it matters: every hash-neutral, byte-equal and determinism claim rests on this digest. Earlier gaps were each found by chance and fixed one axis at a time (TCK-20260902-KNOWLEDGE-CANONICAL-HASH-GAP, TCK-20260902-SOCIAL-CANONICAL-HASH-GAP, TCK-20260903-NAVIGATION-CANONICAL-HASH-GAP, TCK-20260907-CAMPAIGN-BRIDGE-FIELDS-STATE-HASH-COVERAGE), which is the case for a mechanical test.

Proposed rule (rpg-designer): a durable field a decision reads must be in the digest or be derivable from what is. Exclusions are listed, each with a reason.

## Scope
Counts first, with no digest change in this step:
1. A mechanical per-field test: change the field, and the digest must move, walking nested types, with an explicit exclusion list. It replaces the text check and catches other names. Its home is testing-planner's call if it belongs under tests/architecture.
2. The list of decision-read fields outside the digest, each with its reader file:line, or marked derivable.
3. Has any probe or fix differed in those fields under an equal hash? For a sample, compare a fuller dump between a plain run and a probed run.
4. State the cost and placing of a widening for the owner: a new scheme (v4) moves every pinned hash and baseline, and old proofs stop comparing, so it probably sits between batches.

## Out of Scope
- Widening the digest (a later step, with an owner decision, after the counts).
- The wrapper or `_run_engine` perturbation question past t2000 (rpg-planner-ubuntu's two runs).
- Per-tick replay digest in paired arms (TCK-20261023-PAIRED-ARMS-RUN-WITHOUT-THE-PER-TICK-REPLAY-DIGEST).
- Re-opening past rulings: none changes on this alone (rpg-designer).

## Acceptance Criteria
- The test runs, reports every field as covered, excluded with a reason, or a gap, and is deterministic. It may be parked as xfail or report-only only with testing-planner's agreement, and no baseline is edited to make it pass.
- Counts 2-3 are reported and rpg-designer rules on the rule and exclusions.
- The owner gets the scheme-change cost before any widening.
- Hot-loop: no for the test. A later widening would be yes (the digest runs on each hashed tick): timing NOT MEASURED under the perf pause (#715 6556861718) and covered by checkpoint (a).

## Related Tickets
- TCK-20260902-KNOWLEDGE-CANONICAL-HASH-GAP, TCK-20260902-SOCIAL-CANONICAL-HASH-GAP, TCK-20260903-NAVIGATION-CANONICAL-HASH-GAP, TCK-20260907-CAMPAIGN-BRIDGE-FIELDS-STATE-HASH-COVERAGE (done)
- TCK-20261023-PAIRED-ARMS-RUN-WITHOUT-THE-PER-TICK-REPLAY-DIGEST
- TCK-20261023-PRESSURE-SIGNALS-SWITCH-FEATURE-FLAGS-OUTSIDE-THE-HASH

## Related Docs
- docs/engine/deterministic_execution.md (the canonical hash, PERF-D5)
- docs/core/state.md

## Related Stored Artifacts
- None yet. The relay is the only source.

## Related Code Areas
- src/core/state.py (`to_canonical_dict` methods), `CanonicalStateHasher`
- src/core/strategic.py, src/core/cognition.py, src/core/self_model.py, src/core/models/

## Assumptions / Open Questions
- Until counted, "hash-neutral" is strong but not complete evidence. rpg-designer's view: a wrapper changing a cooldown would show in hashed state soon after, once it changes an act; that bound is judgment, not measured.
- Dispatch needs an owner yes; its order is rpg-planner's, after the row 88 work.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
