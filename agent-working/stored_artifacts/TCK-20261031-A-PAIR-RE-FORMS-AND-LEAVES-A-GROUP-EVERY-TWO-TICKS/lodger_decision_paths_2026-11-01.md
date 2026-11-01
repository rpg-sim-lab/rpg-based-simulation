---
status: active
layer: simulation
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20261031-A-PAIR-RE-FORMS-AND-LEAVES-A-GROUP-EVERY-TWO-TICKS
date: 2026-11-01
tags: []
---

# Paths that can decide or record for a lodged stayer, outside F3's two entries

Input for rpg-planner's new P2 ticket on the F3 seam (suggested TCK-20261101-A-LODGER-OFFERS-AND-ACCEPTS-RECRUIT-CONTRACTS), per rpg-designer's request. It does not gate batch C.

Static read of tree effd2e8fc (arm), `src/` relative paths, nothing run. Made by a read-only survey agent for rpg-planner-ubuntu. "Stayer" = `is_lodged_stayer`. "No" under lodging = the loop and helpers read contain no check, by a grep of the lodging symbols.

Checked by rpg-planner-ubuntu against the code: rows 1 (the `lodged_stayer` uses at intelligence.py:369, 395, 633, 643, and force=True at :618), 6, 7, 16, 19 and 20 (no lodging read), 22, 43, the hunger-only wake in scheduler.py `_is_need_woken`, and no lodging symbol in rows 44, 48, 51. Every other row is the survey's reading, unchecked.

Two findings that change how to read the table:
- The two "suppressed" entries only strip walk targets. Neither suppresses the decision itself (rows 1-3).
- A held stayer runs the brain only on a hunger wake. Pipeline phases run regardless.

## A. The two named entries

| # | Path | Decides or records | Reads lodging? | Reachable for stayer |
|---|---|---|---|---|
| 1 | Strategic intent: systems/strategic_systems/intelligence.py:618, `evaluate_strategic_intent` :1263 (project creation, switch, resume, abandon :1077-1135, :1376-1504, goal choice :1611+) | NEW: project/goal record, current_project_id | Only `lodged_stayer` at :369, used at :395, :633, :643, all walk-target writers. No gate at :618 | yes (on cadence) |
| 2 | Concerns, blockers, leads, bandwidth, same pass: intelligence.py:487-626 (work_queue.py:29 has no filter) | Mixed. Lead check ~:440-470 uses get_neighbor_view, which returns [] for a lodger, so a lodger at the lead's coordinates can record "no_hostiles_found" | Indirect (view.py:27) | yes |
| 3 | Brain: engine/domain/cognition.py:74 InformationNeedDetector, :77-78 tactical | NEW: information-need project, tactical task, action. `suppress_stayer_movement` strips target/mode/path only, and only if the result keeps lodging | Navigation yes; strategic and action output no | yes on a hunger wake |
| 4 | Redirection: intelligence.py:630-683 | NEW walk target | Yes | no |
| 5 | Old StrategicRedirectionSystem, strategic_systems/redirection.py:33 | Redirect | No | not determined (no caller found in engine/ or systems/; rest of src not searched) |

## B. Cooperation, contracts, groups

| # | Path | Decides or records | Reads lodging? | Reachable for stayer |
|---|---|---|---|---|
| 6 | Offer: domains/cooperation/phase.py:105, services.py:280-296 | NEW: recruitment contract, last_cooperation_decision | No | yes (needs a help need) |
| 7 | Accept: phase.py ~:170-192 (`accept_pending_offer`) writes contract ACTIVE on the offerer | NEW: acceptance | No | yes (ungrouped, pending offer) |
| 8 | Timeline, help-need events: phase.py ~:113-120, `_record_decision_events` | Durable timeline record | No | yes |
| 9 | Stayer chosen as partner: providers.py:48, get_candidates | Another's decision naming the stayer | No; index uses position | yes |
| 10 | Party cohesion: phase.py ~:215-260, services.py:374 | Passive: trust/grudge deltas | No | yes |
| 11 | Contract expiry: engine/pipeline_phases/contracts.py:82-130 | Upkeep: FULFILLED/EXPIRED, bonds | No | yes |
| 12 | Reap offers: systems/social_systems/contracts.py:307 | Upkeep | No | yes |
| 13 | SocialContractGoalScorer (ai/goals/social_contract_scorer.py), via row 1 | NEW: project from a contract | No | not determined |
| 14 | Counter-offer: systems/social_systems/appraisal.py:183, :326, from engine/domain/core_actions.py:175, 264, 339, 451, 518, 601 | NEW for the target. Target from `context.entities` when not in the neighbour view, bypassing the spatial exclusion | No in these functions | not determined (action_router.py preconditions unread) |
| 15 | Same actions with a stayer as actor | NEW | n/a | not determined |
| 16 | Formation: systems/world_systems/groups.py:282, `_formation_partner` :324, write ~:310 | NEW: group record, group_id_set; stayer can lead or hold | No; 10-tile test uses position | yes |
| 17 | Group upkeep: groups.py ~:100-240 | Upkeep | No; `get_pos` uses building tile | yes |
| 18 | Directive propagation: groups.py:245-275 | Durable GROUP_OBJECTIVE directive on the member | No | yes |
| 19 | Election: engine/pipeline_phases/groups.py:121, party_lifecycle.py:53 | Stayer can be elected by sociability | No | yes |
| 20 | Defection: pipeline_phases/groups.py:190, party_lifecycle.py:168 | NEW desertion record, notoriety, clan reputation | No | yes |
| 21 | Clan lifecycle: engine/pipeline_phases/clan_lifecycle.py:49, :71 | Upkeep or succession | Not in grep | not determined (body unread) |

## C. Information, social, cognition

| # | Path | Decides or records | Reads lodging? | Reachable for stayer |
|---|---|---|---|---|
| 22 | Paid information: engine/pipeline_phases/paid_information.py:98, writes :159, :186 | NEW: lead and gold transfer, no distance or lodged test | No | yes (active INFORMATION_SEEKING project) |
| 23 | Information router: domains/information/router.py:68 | Source lookup | Source only | no for a lodged source; asker not determined |
| 24 | Information resolver: domains/information/resolver.py:35 | Source lookup | Source only | no for a lodged source; asker not determined |
| 25 | Belief, observation: domains/information/phase.py:45, :70, :171 | Belief record | No | yes |
| 26 | Information intent: pipeline_phases/information_intent_execution.py:48 | Runs `pending_action_intent` | No | not determined |
| 27 | Lead staleness: strategic_systems/belief.py:109 | Passive | No | yes |
| 28 | Lead contradiction: pipeline_phases/lead_contradiction.py:158 | Lead marked failed | No | yes |
| 29 | Memory: domains/memory/phase.py:54 | Passive | No | yes |
| 30 | Self model: cognition/self_model_phase.py:52 | Passive | No | yes |
| 31 | Role model: strategy/role_model_phase.py:41, :49 | Admired target; candidates exclude lodgers, subject not filtered | Candidates only | yes |
| 32 | Rumour: `process_rumor`, belief.py | Lead | No | not determined (no caller found) |
| 33 | Faction sentiment from bonds: domains/faction/sentiment.py:68 | Derived | No | yes when bonds arrive |
| 34 | Grief: core/grief_triggers.py:27, engine/kernel.py:601 | Passive | No | yes |

## D. Combat, world, faction

| # | Path | Decides or records | Reads lodging? | Reachable for stayer |
|---|---|---|---|---|
| 35 | Combat engagement, actor: domains/combat_engagement/phase.py:281, :294, writes :378, :454 | NEW at :454: posture or belief with a target; nearby search from the building tile | Targets (:307); actor no | yes |
| 36 | Witness pass: phase.py:194 | Witness events | Yes | no |
| 37 | Combat, legality, AoE: engine/combat.py:495, legality.py:36, 38, domain/aoe_actions.py:38 | Attack, target | Yes | no |
| 38 | Neighbour and perception indexes: spatial.py:14, spatial_query.py:118, world_index.py:162, candidate_selector.py:106, appraisal.py:48, view.py:27 | Filter | Yes | excluded |
| 39 | Swap, occupancy: pipeline_phases/movement.py:89, 101; occupancy.py:68; occupancy_snapshot.py:28 | Tile conflicts | Yes | no |
| 40 | World emergence: domains/world_emergence/phase.py:105 | Passive; force_route_reevaluation is a re-decision flag | No | yes |
| 41 | Trauma concern: world_emergence/services.py:411, world_dynamics.py:191 | Concern record | No | yes |
| 42 | Hazard, tax: world_dynamics.py:83; town_resolution.py:83; world/regional_sovereignty.py:41 | Passive | No | yes |
| 43 | Reproduction: world/reproduction_humanoid.py:37, world_dynamics.py:306 | NEW: child and bonds; lodged partner excluded by index, initiator not | Partner only | yes as initiator |
| 44 | Displacement: world/displacement.py:52 | home_region write | No | yes |
| 45 | Life stage: lifecycle_systems/lifecycle.py:180 | Role on coming of age | No | yes |
| 46 | Faction decision and diplomacy: engine/faction_decision.py:142 and following | Faction-level | n/a | no entity decision |
| 47 | Military guard index: engine/military_conflict.py:132 | Guards in a region | No | not determined |

## E. Economy, quests, progression, interaction

| # | Path | Decides or records | Reads lodging? | Reachable for stayer |
|---|---|---|---|---|
| 48 | Progression: domains/progression/phase.py:42 | NEW: conversion decision | No | yes |
| 49 | Evolution: engine/evolution.py:26 | Passive | No | yes if an update exists |
| 50 | Blacksmith: engine/blacksmith.py:128 | Recipe, craft; exact tile | No | not determined |
| 51 | Guild visit: pipeline_phases/guild_visit.py:45, :78 | NEW: visit, objective resolved; distance <=1 | No | yes if the guild is within 1 tile |
| 52 | Shop: engine/shop.py:43 | Sanitises transfers | No | no decision |
| 53 | Harvest: world_systems/harvesting.py:15 | Progress | No | not determined |
| 54 | Interaction routing: pipeline_phases/interactions.py:27 | Writes interaction target | No | not determined |
| 55 | Interaction enforcement: engine/interaction.py:52 | Enforces updates | No | only if an update exists |
| 56 | Quests: pipeline_phases/quests.py:22, quest_opportunity_rewards.py:49-59 | Reward resolution | No | not determined |
| 57 | Capacity, hardening: capacity_enforcement.py:34; hardening.py:51 | Upkeep | No | yes (not a decision) |
| 58 | Held action: engine/executor.py ~:153; pipeline_phases/actions.py | The rest itself | No | yes |
| 59 | Bed grant and leave: engine/lodging.py:332, :382 | Lodging lifecycle | Yes | leavers only |

## Not read, or only partly read

- Scorer bodies under src/ai/goals/ (occupation_change_scorer.py:47 and adventure_scorer.py:311 seen as snippets only).
- engine/domain/action_router.py preconditions; core_actions.py beyond execute_recruit's start.
- ActionIntentAdapter, GuildAction.visit, quests internals, QuestResolutionSystem, resources.py, clan_lifecycle bodies.
- world/boss.py:111, 230; world/ecology.py:30; world/threat.py:31; creature_territory.py:44; economy/vacancy.py:40; world/camp.py.
- domains/campaigns/*, treated as between-run carry-forward.
- cooperation/services.py `select_for_own_needs`, and map_decision's FOLLOW_LEADER branch.
- Lines marked ~ are approximate. Bed content data is outside the tree, so which building kinds lodge is unknown.
