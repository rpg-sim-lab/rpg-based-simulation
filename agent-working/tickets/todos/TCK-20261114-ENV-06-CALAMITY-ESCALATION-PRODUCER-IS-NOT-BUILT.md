---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20261114-ENV-06-CALAMITY-ESCALATION-PRODUCER-IS-NOT-BUILT
phase: open
date: 2026-11-14
tags: [world]
---

# TCK-20261114-ENV-06-CALAMITY-ESCALATION-PRODUCER-IS-NOT-BUILT

## Title
The ENV-06 calamity escalation (owner decision 10) is not built, so `calamity_intensity` is 0.0 in every region in play

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Owner decision 10 / catalog rule ENV-06 (2026-10-05, docs/world_rules/space-environment/environment.md:174-187) says calamity intensity rises only while a region stays above the instability threshold (Bible 05 §2, `trauma_score > 50.0`) for a sustained period, decays slowly once the region calms, and is never raised directly by a single event. Nothing implements it: `CalamityService.apply_calamity_consequences` (src/world/calamity.py:87-107, +0.05 per hero death) has no caller and is NOT the producer to wire, and `CalamityPressurePropagator.propagate_seasonal` only spreads existing intensity (read and closure: TCK-20260914-CALAMITY-INTENSITY-PRODUCER-NEVER-FIRES). Every consumer is inert in play: the 0.3 boss and magical/demonic gate, displacement at 0.6, transformation requirements, and the regional drain scaling.

## Scope
Build the ENV-06 escalation producer: window, rise rate, decay rate and cap are engineering choices to record in Bible 05 and the parity ledger at implementation (ledger edits through tools/parity_ledger_writer.py). Three scenario assertions are owed (a region held above threshold escalates; a single death spike does not; a calmed region decays). World-boss emergence stays deferred (owner decision 14) and is not evidence. Rebind `registries/mechanisms.yaml` `calamity_intensity.implemented_by` when it lands (the planner's file).

## Out of Scope
- Wiring `apply_calamity_consequences`; the boss branch; `CALAMITY_RANDOM_CHANCE` (stays unwired; any probabilistic onset must be conditioned on this escalation, CAUSE-01).

## Acceptance Criteria
- The escalation exists, is deterministic, and is documented in Bible 05 and the ledger.
- The three scenario assertions pass, and a corpus measurement shows what it does to play.

## Related Tickets
- TCK-20260914-CALAMITY-INTENSITY-PRODUCER-NEVER-FIRES (the read and docs-only close)
- TCK-20260914-LAIR-REGION-TRAUMA-NEVER-ACCUMULATES (this ticket is sequenced AFTER it, per owner decision 10: ENV-06 is observable only once trauma accumulates)

## Related Docs
- docs/world_rules/space-environment/environment.md (ENV-06)
- docs/plans/systemic_world/owner_decision_memo.md (row 10)

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20260914-CALAMITY-INTENSITY-PRODUCER-NEVER-FIRES/

## Related Code Areas
- src/world/calamity.py, src/engine/world_dynamics.py, src/world/displacement.py

## Assumptions / Open Questions
- Dispatch is the owner's, after TCK-20260914-LAIR-REGION-TRAUMA-NEVER-ACCUMULATES lands.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
