---
status: historical
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

## Designer rulings recorded before any rows (via rpg-planner, 2026-11-11)
- Spy approved: recruit_spy.py sha256 84482e13212460c4f1427efaa6020f9e566b8cf60ed0e84a4c023e4af68ccd15, unchanged. Runs on main 70cb24253: 20 spied cells (crowded_frontier, urban_political, frontier_living_world, highland_traverse x s42-46 x 5000) plus 4 PLAIN s42 twins, twins first; each spied cell gets its world's twin hash as argv[5], exit 3 = STOP. A crash in the shadow inputs block is a failed cell, not a gap: fix, send the new sha, wait for re-approval.
- Q1 (test (ii)): an unreachable caller counts as "no live caller" ONLY IF a_execute_recruit_calls = 0 AND b_appraise_contract_recruitment = 0 in all 20 cells, AND the code read cites action_router.py:64 as the only dispatch of execute_recruit with no RECRUIT producer (cited above: router :63-64, no ActionIntent kind RECRUIT in src). Any execute_recruit call makes that world MIXED or DEFECT.
- Q2: if the outcome is BY DESIGN WITH A PARITY GAP, the follow-up (a new ticket, not this one) is pre-named as docs and ledger only: SOC-001 and SOC-008 go to divergent; the two strategic_cognition rows get one consistent wording; ch07 gets a "Current play" note citing D-09 and saying the party-commitment check has no code (the law text is not restated); an intentional_divergences entry, class Bounded. Any code that routes accepts through the appraisal is an owner row, with the shadow verdicts as its cost.
- Reporting rule: status flips on one contract id may be copies in two dicts (holder and target), not transitions. Report them unfiltered.

## Scope 2 closeout (file:line verified on main 70cb24253; read-only; no class)

### (ii) Path map. Every RECRUITMENT OFFERED -> ACTIVE / CANCELLED / FULFILLED route and every appraise caller, with liveness
Liveness is the 24-cell result (2026-11-11, 20 spied cells x 5000 ticks, hashes equal to the 4 plain twins), not a code guess.
| route / caller | where (main 70cb24253) | live in the 20 spied cells? |
|---|---|---|
| OFFERED -> ACTIVE | `CooperationPhase.execute` phase.py:151 (`accept_pending_offer`) and :190 (`ContractService.accept_contract`) -> `transition_contract` contracts.py:178. `accept_pending_offer` services.py:95-106 (also called services.py:122); preconditions in its docstring services.py:70-86: live unexpired OFFERED contract, offerer alive and active, target not in a group; "Richer acceptance criteria ... are explicitly deferred". No call to `appraise_contract` on this path. | YES: c_accept_contract_calls = c_join_party_selections = 14,366 in total (every cell > 0), transitions_to ACTIVE in every cell |
| OFFERED -> ACTIVE (direct) | `execute_recruit` core_actions.py:181 (after `appraise_contract` :175 returns ACCEPTED on a temp contract :168) | NO: a_execute_recruit_calls = 0 in all 20 cells. Only dispatch: action_router.py:63-64 (`action == "RECRUIT"`). No producer of action "RECRUIT" in src: other occurrences are legality.py:167, conservation.py:446, rpg_gate_metrics.py:74; social_contract_scorer.py:86-88 says "nothing in src issues RECRUIT". The routes TEAM_UP, TRADE, TRAIN, PROPOSE_MARRIAGE and JOIN_CLAN have the same shape (router branch, no other string producer found by grep; I did not trace how those action strings are built, so I do not claim they are unissued). |
| OFFERED -> removed (expiry) | `ContractService.reap_expired_offers` contracts.py (called pipeline.py:421, phase "expired_offers") | per-cell c_left_dict counts contracts that left their holder's dict (not summed here); 13,369 contracts were never accepted (flip sequence OFFERED only) |
| OFFERED/COUNTERED -> EXPIRED | pipeline_phases/contracts.py expiry pass (~:118-136) | not separately counted by the spy |
| ACTIVE -> FULFILLED | pipeline_phases/contracts.py:95 -> `ContractService.resolve_contract_outcome` | YES: 14,207 sequences OFFERED>ACTIVE>FULFILLED; 159 stayed ACTIVE at the end |
| OFFERED -> CANCELLED / COUNTERED | return values of `appraise_contract` only (appraisal.py:74,79,88,115,156,185) | NO status CANCELLED or COUNTERED appeared in any flip sequence (unfiltered) |
`appraise_contract` callers on main: core_actions.py:175 (RECRUITMENT temp, `execute_recruit`), :247 (TEAM_UP), :322 (MERCHANT), :434 (TEACH), :501 (MARRIAGE), :584 (CLAN, `execute_join_clan`); paid_information.py:139 (PAID_INFORMATION, in the live pipeline phase pipeline.py:370-371). `_appraise_recruitment`: called only from appraisal.py:83 (`appraise_contract`, RECRUITMENT branch, after the trust prelude :36-80). `calculate_recruitment_cost` appraisal.py:508 has no caller. In the 20 cells: b_appraise_contract_recruitment = 0, b_stopped_before_dispatch = 0, d_appraisals_reached_recruitment_branch = 0 (outside the shadow calls).
Shadow (unwrapped `appraise_contract` at each JOIN_PARTY selection, inputs recorded in the JSONs): ACCEPTED|loyalty_acceptance 8,098; ACCEPTED|fair_compensation 401; CANCELLED|insufficient_incentive 5,866; CANCELLED|betrayal_history 1; total 14,366 = the accepts.

### (iii) Which line shows the appraisal branch was unreached before JOIN_PARTY
No line in TCK-20260912-PARTY-FORMATION-REACHABILITY-INVESTIGATION's stored investigation.md says "the appraisal branch was unreached" in those words (grep for "appraisal" finds no hit). The nearest lines, which show its only caller path was unreached:
- :45-47 "`ContractService.accept_contract()` ... has zero real callers anywhere in `src/` (confirmed by grep) and zero calls in the real 500-tick instrumented run".
- :48-51 "`execute_recruit()` (dispatched from `ActionRouter` on an `ActionIntent(kind="RECRUIT")`), has zero real construction sites for `kind="RECRUIT"` anywhere in `src/`".
- :62 JOIN_PARTY "never chosen, and would no-op if chosen".
- :171-173 acceptance richness (trust, need, faction) "explicitly deferred ... to D-09".
The appraisal being unreached is an inference from :48-51 (its only RECRUITMENT caller is `execute_recruit`), not a stated finding. (Earlier in this file I cited ":44-62" and ":50-52"; the exact lines are above.)

### (iv) What decides recruitment acceptance, quoted with status
- ch07 docs/mechanics/07_social_political_dynamics.md:58-60 "`ContractKind` has 10 real members ... Each routes through the trust pipeline above before kind-specific dispatch"; :65 "| RECRUITMENT | Social fatigue check; party-commitment check; employment cost evaluation |". The chapter's Level: Certified (Authoritative). Code: `_appraise_recruitment` has a fatigue check and a pay evaluation; I find no party-commitment check in it.
- Parity social_narrative.yaml: SOC-001 (:1) "Private betrayal history can override public recruiter reputation." status verified, P0, test_path tests/unit/social/test_betrayal_consequence.py::test_betrayal_trauma_blocks_recruitment, v2_evidence cites `appraise_contract` lines 47-54 as the gate; SOC-008 (:96) "Recruitment evaluates trust, debt, greed, capability fit, and prior trauma." status verified, P0, v2_evidence cites `calculate_recruitment_cost` (no caller), `appraise_contract`/`_appraise_recruitment`, test_path tests/unit/social/test_recruitment.py and the same betrayal test; divergence_note null.
- Parity strategic_cognition.yaml: STRAT-254 (verified, P2) at :3608 "`SocialContractGoalScorer` is confirmed live-reachable via `CoreActions.execute_recruit()` ... which builds ACTIVE RECRUITMENT contracts directly"; STRAT-276 (verified, P2) support_boundary at :4416 "the other holder (the recruit) has no production producer".
- services.py:70-86 `accept_pending_offer` docstring and D-09 (docs/plans/deferred_tuning_decisions_register.md:265-): the shipped acceptance condition has no trust check.
- Facts only. What the cells show against these rows: the weighing in `_appraise_recruitment` did not run on any accept in any of the 20 cells; the shadow call shows what it would have returned (8,499 accepts, 5,867 cancels) on the same inputs. The designer rules on the class.

## Rows (24 cells; main 70cb24253; spy sha256 84482e13...cd15; 5000 ticks; evidence/cells.json holds every cell's counts and hash)
Hash checks first: the spied s42 final_hash equals its plain twin in all four worlds (crowded_frontier d842c20983d7, urban_political 1cd06fd261a2, frontier_living_world 9d4b48476522, highland_traverse b22e1bc6c5bb). Seeds 43-46 have no twin. Every cell rc=0.
| cell | (a) created | exec_recruit calls | (b) appraise RECRUITMENT | (c) accepts | (c) groups (all cooperation_accept) | (d) | shadow acc/loy/canc-incent/canc-betray |
|---|---|---|---|---|---|---|---|
| crowded_frontier_42 | 1259 | 0 | 0 | 719 | 86 | 0 | 2/399/318/0 |
| crowded_frontier_43 | 1284 | 0 | 0 | 845 | 113 | 0 | 51/536/258/0 |
| crowded_frontier_44 | 766 | 0 | 0 | 371 | 79 | 0 | 8/65/298/0 |
| crowded_frontier_45 | 1988 | 0 | 0 | 1041 | 131 | 0 | 3/736/302/0 |
| crowded_frontier_46 | 2960 | 0 | 0 | 1203 | 191 | 0 | 17/699/487/0 |
| urban_political_42 | 1541 | 0 | 0 | 610 | 203 | 0 | 22/230/358/0 |
| urban_political_43 | 1048 | 0 | 0 | 478 | 170 | 0 | 32/207/239/0 |
| urban_political_44 | 1102 | 0 | 0 | 430 | 161 | 0 | 13/155/262/0 |
| urban_political_45 | 477 | 0 | 0 | 217 | 95 | 0 | 17/28/172/0 |
| urban_political_46 | 319 | 0 | 0 | 183 | 25 | 0 | 24/27/132/0 |
| frontier_living_world_42 | 3586 | 0 | 0 | 1975 | 278 | 0 | 95/1137/742/1 |
| frontier_living_world_43 | 2439 | 0 | 0 | 1270 | 190 | 0 | 15/699/556/0 |
| frontier_living_world_44 | 3030 | 0 | 0 | 1824 | 218 | 0 | 67/1403/354/0 |
| frontier_living_world_45 | 3384 | 0 | 0 | 1707 | 339 | 0 | 13/1062/632/0 |
| frontier_living_world_46 | 1577 | 0 | 0 | 661 | 137 | 0 | 19/380/262/0 |
| highland_traverse_42 | 423 | 0 | 0 | 402 | 17 | 0 | 3/307/92/0 |
| highland_traverse_43 | 138 | 0 | 0 | 100 | 15 | 0 | 0/10/90/0 |
| highland_traverse_44 | 114 | 0 | 0 | 90 | 14 | 0 | 0/3/87/0 |
| highland_traverse_45 | 134 | 0 | 0 | 111 | 9 | 0 | 0/10/101/0 |
| highland_traverse_46 | 166 | 0 | 0 | 129 | 14 | 0 | 0/5/124/0 |
| TOTAL (20 cells) | 27735 | 0 | 0 | 14366 | 2485 | 0 | 401/8098/5866/1 |

Totals over the 20 spied cells: 27,735 RECRUITMENT contracts created (all at the cooperation site; unattributed_creations 0); 14,366 accepts; 2,485 groups formed (all by path cooperation_accept); 0 `execute_recruit` calls; 0 appraisals of a RECRUITMENT contract outside the shadow calls; 0 stopped before dispatch. Shadow verdicts: ACCEPTED fair_compensation 401, ACCEPTED loyalty_acceptance 8,098, CANCELLED insufficient_incentive 5,866, CANCELLED betrayal_history 1 (total 14,366 = the accepts). Status flips, unfiltered (may be copies in two dicts): OFFERED only 13,369; OFFERED>ACTIVE>FULFILLED 14,207; OFFERED>ACTIVE 159; no CANCELLED or COUNTERED. Timing NOT MEASURED (perf pause).

## Ruling
rpg-designer, 2026-11-11, session message (relayed by rpg-planner; not #715): **BY DESIGN WITH A PARITY GAP**. The designer checked (ii)-(iv) itself:
- "(ii): the only RECRUITMENT appraise caller is core_actions:175, dispatched only by action_router:64, and nothing issues RECRUIT."
- "(iii): the 09-12 investigation.md, the paragraph 'Confirmed, not assumed...' about :43-62, items 1-2."
- "(iv) FAILS: ch07 :59-67 and SOC-001/008 are verified P0."
(iii) as I found it: no line in the 09-12 investigation.md literally says "appraisal unreached"; it is an inference from :45-51 (zero accept_contract callers, zero RECRUIT construction sites).

## Open item
Owner row pending (lead-planner-u24); docs/ledger fix held until then. This ticket changes no Bible chapter, parity row or divergence entry. The follow-up (a NEW ticket, pre-named by the designer): SOC-001 and SOC-008 to divergent; one wording for the two strategic_cognition rows; a ch07 "Current play" note citing D-09; an intentional_divergences entry, class Bounded. Code that routes accepts through the appraisal is an owner row, with the shadow verdicts above as its cost.

## Also found (unscoped)
- 14,366 accepts formed only 2,485 groups (17%). The rest of the accepted contracts did not form a group in the scan (not investigated here).
- `SocialAppraisalSystem.calculate_recruitment_cost` (appraisal.py:508) has no caller, yet SOC-008 (verified, P0) cites it as evidence.
- Ch07 :65 lists a "party-commitment check" for RECRUITMENT; `_appraise_recruitment` has none.
- No CANCELLED or COUNTERED RECRUITMENT contract exists in play.

## Known gaps
- The producers of the TEAM_UP, TRADE, TRAIN, PROPOSE_MARRIAGE and JOIN_CLAN action strings were not traced, so whether those routes are issued is unknown. This ticket makes no claim about them.
- Timing was not measured. Seeds 43-46 had no plain twin, so purity of the spy there rests on the s42 hash equality.

## Update: the owner answered (docs consequence folded in)
The owner chose (a) docs only (#715 6798982732) and folded the docs fix into this PR (#715 6798995072). It is now in this change: SOC-001 and SOC-008 divergent; STRAT-254 and STRAT-276 reworded (status kept verified); a ch07 "Current play" note; divergence 2.205 (Bounded, D-09). The open item above ("owner row pending ... held") is superseded. Play is unchanged.
