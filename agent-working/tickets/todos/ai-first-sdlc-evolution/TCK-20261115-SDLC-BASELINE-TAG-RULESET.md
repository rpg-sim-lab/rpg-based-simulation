---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261115-SDLC-BASELINE-TAG-RULESET
phase: open
date: 2026-11-15
tags: [ai, governance, security]
---

# TCK-20261115-SDLC-BASELINE-TAG-RULESET

## Title
A tag ruleset protects the four frozen SDLC baseline tags, applied by the owner.

## Status
OPEN

## Tier
hotfix

## Type
chore

## Priority
P2

## Request Summary
Split from TCK-20261031-SDLC-RULESET-M1-AND-TAG-PROTECTION on 2026-11-15. The owner deferred the machine account, the credential removal, E6b and the M1 merge rule, and kept only this tag ruleset, which the owner applies (#715 6889309909, 6889318166). OD-15 (#715 6529263880) froze the baselines as tags. They are unprotected today (#715 6541773425), so any admin push can move or delete them.

## Scope
1. Read the repository's current rulesets fresh. The 10-31 export (`agent-working/stored_artifacts/sdlc-phase-0/ruleset_14220945_export.jsonl`) predates the 2026-11-12 move to the rpg-sim-lab organization and the owner's bypass restore (#715 6818960465), so it is not the before-state. Record the before-state.
2. Prepare, without running, the command or settings steps for a tag ruleset on `refs/tags/baseline/sdlc-*`:
   - block deletion, update and non-fast-forward;
   - give the owner, or the admin role, bypass so the owner can still act;
   - change nothing on the branch ruleset.
3. The owner applies it, on its own ask through lead-planner, logged on #715.
4. Read the rulesets again and confirm the after-state. Show the four tags still at their recorded SHA.

## Out of Scope
- The M1 merge rule and the branch ruleset (deferred, TCK-20261031-SDLC-RULESET-M1-AND-TAG-PROTECTION).
- The machine account and credential removal (deferred).
- Creating, moving or deleting any tag.

## Acceptance Criteria
1. Before and after ruleset reads are recorded, with no credential detail.
2. A tag ruleset targeting the four `baseline/sdlc-*` tags exists, and the branch ruleset is unchanged.
3. The four tags resolve to the SHA in #715 6541773425 after the change.
4. Whether a non-bypass identity is refused is stated as not verified. No non-admin identity exists to test with, since the machine account is deferred.

## Related Tickets
- TCK-20261031-EPIC-AI-FIRST-SDLC-EVOLUTION
- TCK-20261031-SDLC-RULESET-M1-AND-TAG-PROTECTION (split from)
- TCK-20261031-SDLC-R0-INVENTORY-AND-BASELINE-TAGS (made the tags)

## Related Docs
- docs/plans/agent_infrastructure/SDLC_DECISION_RECORD.md
- docs/plans/agent_infrastructure/AI_FIRST_SDLC_ARCHITECTURE_EVOLUTION_PLAN.md

## Related Stored Artifacts
- agent-working/stored_artifacts/sdlc-phase-0/ruleset_14220945_export.jsonl (old before-state, pre-transfer)

## Related Code Areas
- GitHub repository rulesets (owner-applied)

## Assumptions / Open Questions
- Owner condition #715 6528807751: credential details stay out of committed files, tickets and public comments.
- A seat prepares the steps; only the owner applies a ruleset change.
- The bypass-actor types available to an organization repo differ from those for a personal repo. Read what the API offers; don't assume the plan's personal-repo list.
- Timing: the owner ordered this epic's work after the ticket view epic (P3c and backlog view).

## Implementation Notes
(to be filled by the implementer)

## Test Summary
(to be filled by the implementer)

## Files Changed
(to be filled by the implementer)

## Completion Summary
(to be filled by the implementer)
