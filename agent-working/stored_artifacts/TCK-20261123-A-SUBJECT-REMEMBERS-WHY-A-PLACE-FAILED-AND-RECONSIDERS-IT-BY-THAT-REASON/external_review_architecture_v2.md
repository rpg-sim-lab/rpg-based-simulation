---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261123-A-SUBJECT-REMEMBERS-WHY-A-PLACE-FAILED-AND-RECONSIDERS-IT-BY-THAT-REASON
artifact_type: report
tags: []
---

> Owner-provided external input (#715 7091393459), copied verbatim from tmp/reviews/experience_memory_design_v2_architecture_review.md

## Architecture Review — `experience_memory_design.md` (v2)

**Verdict: The direction is sound. I support this design as the next step for the navigation slice, subject to the validation points below.**

This is an architecture review, not an approval to merge.

### What is strong

1. **Purpose-scoped experience is the right correction to #996's broad suppression.** Binding a failure to `TargetPurpose(project_kind, movement_mode)` prevents a failure in one kind of movement from silently suppressing unrelated actions at the same place.

2. **The producer records evidence instead of inventing a diagnosis.** Mapping legality `ReasonCode` values into `BODIES`, `STATIC`, and `OTHER` keeps memory grounded in observations the movement code actually made.

3. **The read/write boundary is well chosen.** A pure destination gate plus one strategic consume/write site avoids probe side effects and gives durable experience state a single owner.

4. **The due rules are cause-specific.** In particular, no timer for static-only obstruction avoids periodic retries against an unchanged world.

5. **The fresh-cycle rule is essential and correctly specified.** A new give-up replaces the prior cycle's evidence and due fields. Cycle number is history/identity only; it does not affect the delay. This avoids disguising exponential backoff as reassessment.

6. **The design is bounded and deterministic.** The per-subject cap, canonical ordering, tick-based rules, explicit eviction policy, and hash/replay checks are appropriate for persistent simulation state.

### Points to validate before treating the design as complete

**1. `APPROACH_CHANGED` may be triggered by movement that did not create a meaningfully new approach.**

The current rule is positional: Chebyshev distance from `from_position` exceeds the configured radius. A subject can move for an unrelated reason and then retry the same anchor from a position that offers no materially different route.

Keep the current rule for this slice if desired, but make R3 report:

- Retries per (anchor, purpose) following an approach-change review.
- Distance and elapsed time between those retries.
- Repeated failures where the approach changed but no navigation progress was achieved.
- Project endings after repeated give-ups without an intervening meaningful approach change.

This is a measurement concern, not a request to add route-segment identity to slice 1.

**2. STATIC-only has a deliberate blind spot when the world changes but the subject does not move.**

With no time-due rule, removing a blocking building or changing terrain will not reopen the experience until the subject moves beyond the approach radius.

That is a defensible slice-1 tradeoff, and perception-based triggers are explicitly out of scope. Preserve this limitation as an explicit contract; a later topology-change event/invalidation mechanism is the natural extension.

Do not add a polling timer merely to hide the gap.

**3. The project-ending threshold measures repeated navigation give-ups, not necessarily repeated independent opportunities.**

Ending a project at four give-ups can be premature if all four failures came from effectively the same approach and the obstruction has not changed.

R3 should stratify project endings by whether an approach change occurred between cycles. If measurements show premature abandonment, revisit the policy rather than increasing or exponentially backing off the review delay.

**4. `project_kind + movement_mode` is a reasonable slice-1 purpose key, but it is not a complete semantic intent model.**

Different goals can share the same project kind and movement mode while having different success conditions.

I would not expand the key in this PR without evidence, but treat this pair as the current navigation-purpose contract, not as a permanent universal identity for every future experience domain.

Monitor same-anchor record fragmentation and active-record eviction.

**5. Be precise about what “fresh evaluation” means in this slice.**

For navigation, the review opens the destination and the next attempt supplies the new evidence. That is acceptable here.

It is not yet a general pre-action reassessment system. Future capability, vitality, or information causes may need to evaluate whether the old failure condition has changed before spending another action.

Keep that distinction explicit when extending the abstraction beyond navigation.

### Recommendation

Keep the current scope and core architecture. Do not reintroduce ACCESS blockers, generic cooldowns, or exponential backoff for give-ups.

Before closing the design review, ensure the own-job runs exercise approach-change, static-only, repeated-project-give-up, and eviction cases, and report the corresponding R3/R1 distributions.

The known limitations above do not require broadening slice 1; they require keeping its guarantees and blind spots explicit.
