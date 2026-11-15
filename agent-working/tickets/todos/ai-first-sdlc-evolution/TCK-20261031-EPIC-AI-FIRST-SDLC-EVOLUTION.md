---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261031-EPIC-AI-FIRST-SDLC-EVOLUTION
phase: open
date: 2026-10-31
tags: [ai, governance, delivery, planning]
---

# TCK-20261031-EPIC-AI-FIRST-SDLC-EVOLUTION

## Title
Evolve the AI-first SDLC: separate authority, verifiable completion, evidence, simplification, context reliability, and a small evaluation track.

## Status
EPIC_SCOPED

## Tier
epic

## Type
feature

## Priority
P1

## Request Summary
Dispatched by agent-working-designer from the plan (section 72 summary, section 38 dependencies). Owner decisions #715 6529263880: OD-1 yes; OD-2 + OD-10 yes; OD-3 as M1, subject to E6b; OD-14 yes; OD-15 yes; E6b yes. Scope is Phases 0-5 plus research R0-R1. Children are cut only as far as the decisions go; see SEQUENCE.md.

**Rescoped 2026-11-15 by the owner (#715 6889309909, 6889318166).** The owner's words, in full: "I think we can ignore this for now, complete the epic without 'Agents get their own non-admin machine account, and your credentials leave both hosts.'" The words "for now" are why these items are deferred, not dropped.
- **Deferred:** the machine account and credential removal (TCK-20261031-SDLC-MACHINE-USER-AND-OWNER-CREDENTIAL-REMOVAL), E6b (TCK-20261031-SDLC-E6B-THROWAWAY-REPO-GITHUB-BEHAVIOURS), and the M1 merge rule (TCK-20261031-SDLC-RULESET-M1-AND-TAG-PROTECTION). Phase 1's core is out of live scope. OD-2, OD-3 and OD-10 stay decided, but nothing executes them.
- **Kept:** the tag ruleset for the baseline tags, split out as TCK-20261115-SDLC-BASELINE-TAG-RULESET, which the owner applies.
- **Order:** Phase 5 first (TCK-20261031-SDLC-CONTEXT-AND-SESSION-RELIABILITY). Then agent-working-designer brings OD-4, OD-5, OD-6, OD-11, OD-12 and OD-13 to the owner, each with options and a recommendation. Phases 2-4 are cut only after the owner decides them, and their Phase 1 prerequisite is re-read in that pack. R1-R5 stay deferred.
- **Timing:** after the ticket view epic (TCK-20261112-EPIC-GITHUB-PROJECT-TICKET-VIEW: P3c and the backlog view).
- **Stale input:** the repo has been an organization repo (rpg-sim-lab) since 2026-11-12. The plan's GitHub analysis assumes a personal repo, so it is redone for OD-13 and for anything deferred that reopens.

## Scope
Phases 0-5 and R0-R1 of the plan. Children filed now: see SEQUENCE.md.

Not cut yet, with what each is waiting for:
| Work | Waiting for |
|---|---|
| Phase 2, verifiable completion | Phase 1; OD-4, OD-11, OD-12, OD-13 (Phase 2 entry) |
| Phase 3, evidence and attribution | OD-11 (evidence layers); OD-8 only at its exit |
| Phase 4, simplify | Phase 2 in force, Phase 3 landed, R0 tags, OD-5, OD-6 |
| R1, basic evaluation | R0; OD-16, OD-17, OD-18, OD-21; no owner credential reachable by a trial host |

## Out of Scope
- Phase 6 and R2-R5 (conditional or optional in the plan).
- OD-7 and OD-9 as decisions; this epic carries their inputs only.
- `tmp/` content: `AI_WORKING_ISSUE1.md` is the owner's and is not committed unless the owner says so.

## Acceptance Criteria
1. Every Phase 0-5 and R0-R1 item is done, or recorded with a dated owner deferral.
2. ~~An agent identity cannot merge, push to main, or approve its own PR, and no owner credential is usable from either host (Phase 1 acceptance, plan section 39).~~ Deferred by the owner 2026-11-15 (#715 6889318166). It is met by recording that deferral under AC1.
3. Each uncut row above is cut into children only after its decisions are recorded.

## Related Tickets
- none
- Received 2026-11-14 from TCK-20261002-EPIC-SESSION-LAYER-MEASUREMENT-AND-REVIEW (closed, owner #715 6875225978): the session-layer M7 first-month evidence review (harden / keep / retire per advisory rule) and the deferred-item decisions (message inbox, auto-wake, hard message blocking, authority digest pin); and from TCK-20261009-EPIC-SESSION-LEAD-PLANNER: E5's evaluation (does the lead seat lower the manual-action metric). This plan's M7 / OD-9 item is where they land.

## Related Docs
- docs/plans/agent_infrastructure/AI_FIRST_SDLC_ARCHITECTURE_EVOLUTION_PLAN.md
- docs/plans/agent_infrastructure/AI_FIRST_SDLC_DECISION_SUMMARY.md

## Related Stored Artifacts
- none

## Related Code Areas
- See each child

## Assumptions / Open Questions
- Owner condition #715 6528807751: credential details from either host stay out of committed files, tickets and public comments unless a decision needs them; they go to the owner directly.
- No credential or ruleset change is authorised by the epic; each gets its own owner ask, by ticket.
- Undecided, and not to be written as decided: OD-4 to OD-9, OD-11 to OD-13, OD-16 to OD-21.
- u24's credential check came back with the same finding as ubuntu. E6a's inventory covers the two details still unread on u24; its specifics are not for tickets or commits.

## Implementation Notes
(to be filled by the implementer)

## Test Summary
(to be filled by the implementer)

## Files Changed
(to be filled by the implementer)

## Completion Summary
(to be filled by the implementer)
