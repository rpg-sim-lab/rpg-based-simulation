---
status: historical
layer: systems
authority: P1
audience: agent
ticket_id: TCK-20261113-FIVE-SOCIAL-ACTION-KINDS-MAY-HAVE-NO-ISSUER-IN-PLAY
phase: done
date: 2026-11-13
tags: []
---

# TCK-20261113-FIVE-SOCIAL-ACTION-KINDS-MAY-HAVE-NO-ISSUER-IN-PLAY

## Title
Five social action kinds may have no issuer in play: find which of TEAM_UP, TRADE, TRAIN, PROPOSE_MARRIAGE and JOIN_CLAN/LEAVE_CLAN anything ever emits, and how their contracts are really created and accepted

## Status
DONE

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
Owner approval: #715 6843004519 and 6843079519; docs-only follow-up per the recruitment precedent (#715 6798982732). rpg-designer's ruling (2026-11-13): the read suffices, no spy. Per kind: BUILT, APPRAISED AND UNREACHABLE IN PLAY with no issuer; JOIN_CLAN doubly dead (no clan exists); LEAVE_CLAN no appraisal and no clan to leave; none has a RECRUIT-style bypass. Scope 4a (perception at distance 1) and 4b (RETREAT null result) are PARKED as findings; the town-regroup point stays with the REGROUP ticket. The exact docs text is the designer's, applied from /mnt/data2/rpg-measure/briefs/five-kinds-docs-ruling.md (sha256 fa98ec10…).

## Test Summary
- No cells were run and no spy was written: the designer ruled that the read suffices.
- The designer's CHECK FIRST (the apply.py:483 clause) was verified against every ClanUpdate producer before SOC-264's text was written: process_leave (clan_lifecycle.py:68) takes the clan_id of an executed LEAVE_CLAN and the phase acts only on outcome SUCCESS, which needs the entity to be a member of an existing clan (core_actions.py:608-613); the join path (pipeline_phases/clan_lifecycle.py:63) takes the payload clan_id but SUCCESS needs `context.clans.get(clan_id)` to exist (core_actions.py:551-557); process_succession (:143) and process_dissolution (:174) use `clan.clan_id` of an entry already in state.clans; groups.py:221 and contracts.py:294 use `find_clan_id_for_entity`, which scans state.clans. No producer can name a new clan_id in play.
- `make parity-ledger-schema-check`: OK, 2651 schema errors, 0 rose, 0 new, 0 fell (unchanged). Frontmatter validators on all six edited docs: OK. `pytest tests/docs -n 1`: 92 passed, 1 skipped, 1 xfailed. `generate_registry.py --check` after the closure regeneration: see Finalize.
- Not run: `make knowledge-index-update` (not run: worktrees use main's index; lead-planner-u24, 2026-11-12).

## Files Changed
- docs/parity_ledger/social_narrative.yaml (SOC-249, 250, 258, 261, 264, 272: support_boundary added; SOC-134 v2_evidence id SOC-268 -> SOC-272), strategic_cognition.yaml (STRAT-266), town_resource.yaml (TOWN-027), world_dynamics.yaml (WORLD-BELIEF-001, appended). All entries stay verified.
- docs/mechanics/07_social_political_dynamics.md (a "Current play" blockquote), 04_strategic_cognition.md (Current play notes in section 8 and 10, the fixture sentence at the reverse-lookup paragraph, SOC-268 -> SOC-272 in 10a), 05_world_evolution.md (one sentence), docs/simulation/social_systems_contract.md (a blockquote), docs/engine/known_limitations.md (one bullet), docs/guidelines/intentional_divergences.md (SOC-268 -> SOC-272 in 2.51).
- agent-working/agent-monitoring shards; tech-stack Inventory seed line in agent-working/lead/stack_seed_review.md (OpenTelemetry, the lead's ride-along, commit d4bf55081).

## Completion Summary
Investigation and docs correction; no src change. None of TEAM_UP, TRADE, TRAIN, PROPOSE_MARRIAGE, JOIN_CLAN or LEAVE_CLAN is issued by anything in play (no ENTITY_ACT payload or ActionIntent creates them; no world, scenario or content file names them; only unit tests call them), so their appraisal branches (_appraise_trade, _appraise_team_up, _appraise_teach, _appraise_marriage, _appraise_clan) run only in unit tests, and no clan exists in play. This follows the SOC-280 pattern: play does nothing, so nothing diverges; every ledger entry stays verified with a support_boundary, and the Bible states the current play. Not changed: the DEV-007 and 2.51 texts (apart from the id fix), world_rules/**, and the SOC-268 mentions in code comments, tests and docs/plans/rpg_design_roadmap/rpg_m5_memory_reputation_epic.md:116 (outside the ruling's three places; for the designer to say). Making any kind reachable is an owner gameplay decision. Parked findings: Scope 4a (the sense gate passes; the cause is the wild-creature clause, decision 47, or intruding being unset; kept frontier_marches s42 rows by subject: scout 83, alpha 17, wild_creature 15, predator_hunter 12, raider 9, shaman 7) and Scope 4b (movement.py:240 step_ready on a costly tile fits t1953-1959 best, an observability finding).
