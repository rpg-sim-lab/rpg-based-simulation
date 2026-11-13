---
status: active
layer: systems
authority: P1
audience: agent
ticket_id: TCK-20261113-FIVE-SOCIAL-ACTION-KINDS-MAY-HAVE-NO-ISSUER-IN-PLAY
phase: open
date: 2026-11-13
tags: []
---

# TCK-20261113-FIVE-SOCIAL-ACTION-KINDS-MAY-HAVE-NO-ISSUER-IN-PLAY

## Title
Five social action kinds may have no issuer in play: find which of TEAM_UP, TRADE, TRAIN, PROPOSE_MARRIAGE and JOIN_CLAN/LEAVE_CLAN anything ever emits, and how their contracts are really created and accepted

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
rpg-designer raised this on 2026-11-11 as an after-batch finding (session message). It came out of TCK-20261111-NO-RECRUITMENT-APPRAISAL-RUNS-IN-ANY-CORPUS-WORLD, which landed as #883, docs only. That investigation found that RECRUIT's `execute_recruit` (src/engine/domain/core_actions.py:175/181) has **no issuer**: the action router (src/engine/domain/action_router.py:63-64) dispatches it, but nothing in play emits a RECRUIT action. Real recruitment instead goes through the cooperation path (services.py:283-305 create, phase.py:174-195 accept).

The router has the same shape for TEAM_UP (:66), TRADE (:69), TRAIN (:75), PROPOSE_MARRIAGE (:78), JOIN_CLAN (:81) and LEAVE_CLAN (:84), with their `execute_*` paths in core_actions.py (about :211-584). Bible ch04 §8 (Marriage Proposal Law, SOC-261) and §10 (Clan Lifecycle Law, SOC-264), and ch07's trust appraisal, describe these as verified laws. If any kind has no issuer, it is the same parity gap #883 found for recruitment: law marked verified that play never reaches.

rpg-planner filed this on 2026-11-13. It covers investigation and measurement only, and no fix.

It also carries one further finding (rpg-designer, 2026-11-13, from TCK-20261109-A-COMBAT-RETREAT-PROJECT-WALKS-THE-SUBJECT-AGAINST-THE-HELD-FLIGHT-RULE). In frontier_marches s42, 149 of 400 kept rows had perception failing at distance 1: an orthogonally adjacent hostile that the catalog counts as engagement-hostile, but that `perceived_hostile` was False for. It also had a null-result RETREAT `resolve_move` with no failure_reason (t1953-1959). Scope 4 below.

## Scope
1. **Code read (read-only), on the then-current main.** For each kind (TEAM_UP, TRADE, TRAIN, PROPOSE_MARRIAGE, JOIN_CLAN, LEAVE_CLAN), name with file:line:
   - (a) every site that emits that action string or intent (brain, tactical, strategic, social, cooperation or other), or "none found";
   - (b) the execute path and what it writes;
   - (c) any other path that creates or accepts that kind's contract without the action. Cooperation-style bypasses are the RECRUIT precedent.
   - (d) the appraisal branch in SocialAppraisalSystem for that ContractKind, and whether it is reachable.
2. **Measurement, only for kinds that the read leaves open.** Use one read-only spy, approved by rpg-designer at a sha before it runs. Run it on crowded_frontier, urban_political, frontier_living_world and highland_traverse × s42-46 × 5000 ticks on main, with a plain-twin hash check per world (option A as in S2: one s42 twin per world).
   - Per world and seed, count per kind: action emissions, execute calls, contracts created by site, contracts accepted by path, and appraisals.
   - Cells run under the per-job host bar (MemoryMax=1G, MemAvailable ≥ 1.5 GB), one at a time.
3. rpg-designer rules per kind: DEAD (no issuer and no other path), BYPASS BY DESIGN, BYPASS AS DEFECT, or LIVE. Use the same tests as the recruitment ticket's ruling, fixed before the rows.
4. The perception-at-distance-1 slice: in the code read, find which perception input fails at distance 1 for an adjacent hostile (stealth, signal, the perception gate's own range, or another cause). Also find why a RETREAT resolve_move can return a null result with no failure_reason. Only measure if the read leaves it open. The designer rules whether it's a defect.
5. No fix in this ticket. Any fix, or any docs or ledger correction, is a new ticket, as #883 was.

## Out of Scope
- RECRUIT (settled by #883, divergence 2.205).
- Tuning any acceptance rule (D-09 and similar).
- Fixing anything found.

## Acceptance Criteria
- A per-kind path map (emit → execute → contract create → accept → appraisal) with file:line on main.
- Per-kind counts per world and seed from a designer-approved, hash-matched spy, for the kinds the read left open.
- rpg-designer's per-kind ruling recorded.
- Scope 4 answered: what fails perception at distance 1, and why RETREAT returns a null result with no reason.

## Related Tickets
- TCK-20261111-NO-RECRUITMENT-APPRAISAL-RUNS-IN-ANY-CORPUS-WORLD (#883, the precedent)
- TCK-20261109-A-COMBAT-RETREAT-PROJECT-WALKS-THE-SUBJECT-AGAINST-THE-HELD-FLIGHT-RULE (source of Scope 4)
- TCK-20260902-MARRIAGE-PROPOSAL-CONTRACT, TCK-20260824-AFFECTION-CONTRACT-GATE, TCK-20260904-CLAN-REPUTATION-ASSOCIATION (the builds of these kinds)

## Related Docs
- docs/mechanics/04_strategic_cognition.md §8 (marriage), §10 (clan)
- docs/mechanics/07_social_political_dynamics.md (trust appraisal, contracts)
- docs/parity_ledger/social_narrative.yaml (SOC-261, SOC-264 and the team-up/trade/train entries)
- docs/guidelines/intentional_divergences.md 2.205 (the recruitment precedent)

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20261111-NO-RECRUITMENT-APPRAISAL-RUNS-IN-ANY-CORPUS-WORLD/ (spy and method to reuse)

## Related Code Areas
- src/engine/domain/action_router.py (:63-84)
- src/engine/domain/core_actions.py (execute_* about :175-584)
- src/domains/cooperation/services.py, src/domains/cooperation/phase.py
- src/systems/social_systems/appraisal.py, contracts.py
- src/engine/hostility.py (perceived_hostile), src/engine/legality.py (_is_engagement_hostile), src/systems/movement.py (resolve_move)

## Assumptions / Open Questions
- Line numbers are from main d1c9b3022; re-check them on the then-current main.
- Host: cells queue under the per-job bar.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
