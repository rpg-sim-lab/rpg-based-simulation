---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261031-SDLC-RULESET-M1-AND-TAG-PROTECTION
phase: open
date: 2026-10-31
tags: [ai, governance, security]
---

# TCK-20261031-SDLC-RULESET-M1-AND-TAG-PROTECTION

## Title
The production ruleset is set per OD-3 (M1), and a tag ruleset protects the frozen baselines.

## Status
BLOCKED

## Tier
hotfix

## Type
chore

## Priority
P1

## Request Summary
**Deferred, and split.** Owner decision 2026-11-15 (#715 6889309909, 6889318166): the M1 merge rule is deferred with the machine account and E6b; only the tag ruleset stays. The tag ruleset moved to TCK-20261115-SDLC-BASELINE-TAG-RULESET, which is live. This ticket keeps the M1 part only (scope item 1 and the required-check pins) and stays BLOCKED until the owner reopens it. Its original text follows.

Phase 1 ruleset item. OD-3 is M1 subject to E6b: keep the `update` rule with the owner as sole bypass actor. Section 27a adds a tag ruleset, or OD-15's baselines are not frozen. BLOCKED until E6b holds and the owner gives a yes for this exact change.

## Scope
1. State the before and after against the export; the update rule is expected to be unchanged unless E6b says otherwise.
2. ~~The owner applies the tag ruleset.~~ Moved to TCK-20261115-SDLC-BASELINE-TAG-RULESET on 2026-11-15.
3. Keep the required-check pins.

## Out of Scope
- M2 (needs a new owner decision).
- CODEOWNERS (M2 only).
- The machine user (its own ticket).

## Acceptance Criteria
1. A fresh read of the rulesets matches the agreed after-state.
2. The rollback JSON is named.
3. ~~Tag protection is verified.~~ Moved to TCK-20261115-SDLC-BASELINE-TAG-RULESET.

## Related Tickets
- TCK-20261031-EPIC-AI-FIRST-SDLC-EVOLUTION
- TCK-20261115-SDLC-BASELINE-TAG-RULESET (the tag part, split out 2026-11-15)

## Related Docs
- docs/plans/agent_infrastructure/AI_FIRST_SDLC_ARCHITECTURE_EVOLUTION_PLAN.md
- docs/plans/agent_infrastructure/AI_FIRST_SDLC_DECISION_SUMMARY.md

## Related Stored Artifacts
- none

## Related Code Areas
- GitHub settings (owner-applied)

## Assumptions / Open Questions
- Owner condition #715 6528807751: credential details from either host stay out of committed files, tickets and public comments unless a decision needs them; they go to the owner directly.
- No credential or ruleset change is authorised by the epic; each gets its own owner ask, by ticket.
- Undecided, and not to be written as decided: OD-4 to OD-9, OD-11 to OD-13, OD-16 to OD-21.

## Implementation Notes
(to be filled by the implementer)

## Test Summary
(to be filled by the implementer)

## Files Changed
(to be filled by the implementer)

## Completion Summary
(to be filled by the implementer)
