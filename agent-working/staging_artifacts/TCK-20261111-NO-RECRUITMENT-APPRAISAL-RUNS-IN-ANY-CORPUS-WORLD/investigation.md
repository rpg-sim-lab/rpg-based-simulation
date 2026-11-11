---
status: active
layer: systems
authority: P2
audience: agent
ticket_id: TCK-20261111-NO-RECRUITMENT-APPRAISAL-RUNS-IN-ANY-CORPUS-WORLD
artifact_type: investigation
---

# Investigation (code read on origin/main 70cb24253; read-only)

## Creation sites of a RECRUITMENT ContractState
- C1 cooperation: `CooperationIntentBridge.map_decision` (src/domains/cooperation/services.py ~:260-295) turns posture REQUEST_HELP / HIRE_SUPPORT with a partner into `ContractService.create_recruitment_contract` (src/systems/social_systems/contracts.py:114-134, status OFFERED, `expiry_tick = tick + 10`), stored on the OFFERER's own `strategic.contracts` only (never mirrored to the target). Its only caller (grep): services.py:284.
- C2 the RECRUIT action: `CoreActions.execute_recruit` (src/engine/domain/core_actions.py:137-211). Builds a TEMP contract (:168, id `temp_eval`, OFFERED, never stored), appraises it at :175, and only on ACCEPTED stores an ACTIVE contract on both sides (:181-190). Dispatched by `ActionRouter` on action "RECRUIT" (src/engine/domain/action_router.py:63-64).
- No other `ContractState(kind=RECRUITMENT)` construction in src (grep of `kind=ContractKind.RECRUITMENT`: contracts.py:125, core_actions.py:168 and :181 only).
- Who issues action "RECRUIT"? Nothing. Every `ActionIntent(` in src (combat_engagement/resolver.py:41,52,64; adventure/resolver.py:86 with the kinds REQUEST_CRAFT, MOVE_TO, ACCEPT_QUEST, ATTACK_TARGET, HARVEST_RESOURCE, ASK_INFORMATION, RETURN_TOWN, CHANGE_OCCUPATION; information/resolver.py:52,78; tactical_objective.py:79) uses another kind. The string "RECRUIT" appears only in the router branch, legality.py:167 (a kind list), conservation.py:446 (a transfer source_kind) and rpg_gate_metrics.py:74. src/ai/goals/social_contract_scorer.py:86-88 says the same ("nothing in src issues RECRUIT"). The 2026-09-12 investigation.md:50-52 recorded the same ("zero real construction sites for kind=RECRUIT").

## OFFERED to end state (RECRUITMENT), every path on main
| from | to | where | trigger |
|---|---|---|---|
| OFFERED | ACTIVE | `CooperationPhase.execute` src/domains/cooperation/phase.py:174-196 -> `ContractService.accept_contract` contracts.py:156-181 -> `SocialContractSystem.transition_contract` contracts.py:20-48 (sets expiry = tick + terms.duration) | `find_pending_incoming_offer` services.py:65-93 / `accept_pending_offer` :95-106 selects JOIN_PARTY for the TARGET: offer unexpired, offerer alive+active, target not in a group. No trust check, no rejection path (docstring :73-83; D-09). `build_pending_offer_index` :28-62 |
| (temp OFFERED) | ACTIVE (stored directly) | `execute_recruit` core_actions.py:181-190 | only when `appraise_contract` returns ACCEPTED; never reached (no issuer of RECRUIT) |
| OFFERED | removed from the holder's dict | `ContractService.reap_expired_offers` contracts.py:297-330 (0 < expiry_tick <= tick; sets the `cooperation_offer_retry` cooldown) | expiry |
| OFFERED / COUNTERED | EXPIRED | `ContractLifecycle` expiry pass src/engine/pipeline_phases/contracts.py:~118-136 (`contract_is_due`) | expiry tick reached (event_shapers.py:1572-1580 notes both fire in the same tick) |
| ACTIVE | FULFILLED | pipeline_phases/contracts.py:89-108 -> `resolve_contract_outcome` contracts.py:187-+ with success=True ("success is the only honest disposition") | ACTIVE contract due |
| OFFERED | CANCELLED / COUNTERED | `appraise_contract` return values only (appraisal.py:74,79,88,115,156,185). The one consumer is `execute_recruit`, which on a non-ACCEPTED result stores NO contract (writes `rejection_increment` on the target, core_actions.py:200-210). So no stored RECRUITMENT contract is ever CANCELLED or COUNTERED. | unreached |
Groups: `GroupSystem._gather_formation` src/systems/world_systems/groups.py:338-360 forms a group from ANY live (ACTIVE and not due) contract of the entity, kind-agnostic; the group records `contract_id` and `contract_holder_id` (group_record.py).

## Callers of `_appraise_recruitment`
- Only `SocialAppraisalSystem.appraise_contract` appraisal.py:82-83 (after the trust prelude :36-80 can stop it first with TOTAL_DISTRUST or BETRAYAL_HISTORY).
- `appraise_contract` callers with a RECRUITMENT contract: only `execute_recruit` core_actions.py:175 (on the temp contract). The other `appraise_contract` callers build TEAM_UP/MARRIAGE/CLAN/TEACH/PAID_INFORMATION/etc. contracts (core_actions.py:247,322,434,501,584; paid_information.py:139).
- No code appraises a STORED OFFERED recruitment contract (the cooperation-made kind). `calculate_recruitment_cost` (appraisal.py:508) has no caller.
- Static caller exists (execute_recruit, router); no issuer of the RECRUIT action exists. rpg-designer decides how test (ii) reads that.

## Purity of `appraise_contract` (SHADOW allowed)
appraisal.py:29-115 and :118-185 read `entity`, `contract`, `state`, `trust_score` and return a tuple. grep of appraisal.py for random/rng/cache/lru_cache: no hit. `ClanLifecycleService.find_clan_id_for_entity` (clan_lifecycle.py:41-51) is a sorted read. No write, no draw, no cache. The hash twin is the backing.

## 2026-09-12 investigation (TCK-20260912-PARTY-FORMATION-REACHABILITY-INVESTIGATION), test (iii)
agent-working/stored_artifacts/.../investigation.md:44-62: `accept_contract` had zero callers and zero calls in the instrumented run; the only other path to ACTIVE, `execute_recruit`, had "zero real construction sites for kind=RECRUIT"; JOIN_PARTY was never selected. So before the wiring NO recruitment accept happened, and the appraisal branch was already unreached. The wiring added the first working accept path; it replaced no working path. Lines 166-175: acceptance-criteria richness deferred to D-09.

## Docs and ledger (test (iv))
- Bible ch07 (docs/mechanics/07_social_political_dynamics.md:59-75): "Each routes through the trust pipeline above before kind-specific dispatch"; RECRUITMENT row: "Social fatigue check; party-commitment check; employment cost evaluation". Code has a fatigue check and an employment/pay evaluation in `_appraise_recruitment`; there is no party-commitment check in it (separate finding).
- Parity ledger: SOC-001 (verified, P0): private betrayal history gates recruitment (appraisal.py); SOC-008 (verified, P0): "Recruitment evaluates trust, debt, greed, capability fit, and prior trauma" (cites `calculate_recruitment_cost`, uncalled); a strategic_cognition entry (~:3608) says `SocialContractGoalScorer` is "live-reachable via CoreActions.execute_recruit()", while a later entry (~:4416) says the recruit side "has no production producer". Both are stated as verified law that play does not take on the cooperation path.
- D-09 (docs/plans/deferred_tuning_decisions_register.md:265-): states the shipped minimal condition, "No trust check".

## What the code read points to (not a ruling)
(ii) holds for stored OFFERED contracts; whether it holds as the designer worded it depends on counting the unreached `execute_recruit` caller. (iii) holds. (iv) fails as written (SOC-001/SOC-008 and ch07 state trust gating as verified law). Read as fixed on 2026-11-11, that is BY DESIGN WITH A PARITY GAP if the rows show (i) and (d) = 0; the rows and the designer decide.
