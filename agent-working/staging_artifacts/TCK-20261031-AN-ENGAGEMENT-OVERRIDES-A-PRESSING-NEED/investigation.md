---
status: active
layer: ai
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20261031-AN-ENGAGEMENT-OVERRIDES-A-PRESSING-NEED
tags: []
---

# investigation - TCK-20261031-AN-ENGAGEMENT-OVERRIDES-A-PRESSING-NEED

## Findings so far
- Lane B's skip counter recorded 0 over 131785 evaluate calls. Cause found: `TacticalDecisionSystem.evaluate_entity_intent(state, entity, neighbors=None, region_trauma=None)`; the wrapper in f3h_obs.py read `entity = a[0]`, `state = a[1]` (swapped), so `present_threat(entity, state)` raised inside a bare `except`, before `_SKIP[...] += 1`. Not a binding problem: `classify_neighbours` is imported into tactical's namespace and the patch works.
- Smoke (urban_political s44, 50 ticks, probe `eng_probe.py`): the fixed counter records hostiles-present calls (16 of 131 evaluate calls).
- Skip sites (tactical.py, to be completed with tests in the report): the `if not hostiles:` block at tactical.py:266 (objective pursuit incl. building arrival/hunger arrival, role obligation) is skipped on ANY hostile (presence test: classify_neighbours hostiles); `in_place_survival_update` (tactical_rest.py:135) calls rest_in_place_update / eat_carried_update / eat_at_corpse_in_place_update, the corpse one yields to present_threat_terms (tactical_rest.py:109).

## Phase 1 results (probe eng_probe.py, origin/main 15a8f5893, 15 runs: crowded_frontier / frontier_living_world / urban_political x s42-46, 5000t)
Hot-loop: n/a (probe). Hash neutrality: urban s42 5000t probed == plain == e37b78cfb573fe25460959c6184fc0ec72a7d3ff0ee0dc6654a0dec684c15f61. Counter proof (known-case substitute): eng_synthetic_check.py, 4/4 PASS (pressing + non-adjacent + non-acting hostile in an ATTACK task = ENG; hostile acting = not; adjacent = not; no pressing need = not). DISCLOSURE: lane B's s44 case (subject 13 pursues scout 16) does not reproduce on main (urban s44 1620t: 0 ENG ticks); its trace is pre-#795.

### Family table (ticks / distinct subjects / longest stretch; one tick may carry several tags)
| tag | ticks | subjects | longest |
|---|---|---|---|
| ENGAGEMENT_OVERRIDES | 20029 | 144 | 3385 |
| LOW_HP_RETREAT (PANIC_RETREAT, pressing, no present threat) | 2190 | 46 | 46 |
| LHR_HOLD (AVOID_NO_ROUTE hold under a pressing need) | 0 | 0 | 0 |
| LHR_CARRY_WALK (REGROUP walk, acting hostile, hp<0.5) | 6163 | 227 | 99 |
| TOWN_RETURN (pressing, project town_return) | 6437 | 39 | 387 |
| ESCALATED_NEED_SWITCH | 1569 | 175 | 1 |
| FLEE_LINE (ATTACK while is_fleeing) | 1093 | 99 | 78 |
| CAP_REFUSAL | 16656 | 282 | 1 |
Any-tag ticks (a tick counted once): 51488. Per world ENG ticks: crowded 3205 (69 subjects), frontier 16657 (56), urban 167 (19; only s44).
Overlap (ticks): ENG alone 19345; CAP_REFUSAL alone 15350; TOWN_RETURN alone 5905; LHR_CARRY_WALK alone 5302; LOW_HP_RETREAT alone 1719; ESCALATED alone 966; FLEE+CARRY 730; CAP+ENG 539; CAP+ESCALATED 538; LOW_HP+TOWN_RETURN 355; FLEE alone 317; the rest <=80 each (full matrix in the per-run JSONs / report).
### Harm joins (subjects that carried the ENG tag; deaths are of any cause after or before the tag, not attributed to it)
| world | ENG subj | collapsed | dead (any cause) | starving ticks (hunger>=95) of ENG subjects | debt>=98 ticks | follower ENG ticks / leader / none |
|---|---|---|---|---|---|---|
| crowded | 69 | 15 | 53 (COMBAT 31, DEFEAT 20, HAZARD 2) | 8687 | 1020 | 1399 / 121 / 1685 |
| frontier | 56 | 17 | 11 (COMBAT 6, DEFEAT 5) | 63210 | 10954 | 6463 / 28 / 10166 |
| urban | 19 | 0 | 1 (COMBAT) | 233 | 0 | 103 / 1 / 63 |
No death by STARVATION among recorded subjects in the 15 runs (deaths: COMBAT 181, DEFEAT 107, HAZARD 25 over 526 recorded subjects); 65 subjects collapsed. Followers with ENG ticks: 44 + 40 + 12.
### Tactical hostiles-present skip counter (item 3): 126251 evaluate calls; hostiles present on 8345; split (pressing, adjacent, acting): pressing and neither adjacent nor acting 2942 calls (129 subjects) = the skip site fires with no present threat; pressing+acting 527; pressing+adjacent 1040+407; not pressing 3429.
### REGROUP writers (all 15 runs): intelligence.py:678 66323, :400 113, :406 87 (the town-carry branches, 66523 total), tactical.py:379 1290 (cohesion regroup), movement.py:274 1229, movement.py:315 51, occupancy.py:155 4. The carry share of REGROUP writes is about 95%.
### CAP_REFUSAL: 16656 ticks; live SUSPENDED count at refusal: 0 -> 2243, 1 -> 4217, 2 -> 6535, 3 -> 3177, 4 -> 457, 5 -> 41.
### Item 4 skip sites (tactical.py hostile-presence gates on the survival path)
1. tactical.py:266 `if not hostiles:` skips the whole objective-pursuit block, which holds the hunger arrival and the building arrival (`building_arrival_update`), the other objective kinds, the role obligation (:352 `if group and not hostiles`) and the cohesion REGROUP (:372). Test used: PRESENCE (classify_neighbours hostiles non-empty). Covered by: no unit test of the skip itself found (tests/unit/engine/test_biological_needs.py, test_earn_shift.py, test_lodging.py exercise arrivals without hostiles).
2. tactical.py:262 -> tactical_rest.py:135 in_place_survival_update: rest_in_place_update (tactical_rest.py:66), eat_carried_update (:94), eat_at_corpse_in_place_update (:111) each return None when `present_threat_terms` holds (AGENCY-07 terms: wounded, adjacent, TARGETED, closing, outmatched) = a broader "danger" test than acting_threat_to. Tests: tests/unit/engine/test_rest_in_place.py, test_biological_needs.py.
3. tactical.py:247 safety_retreat_warranted (present_threat_terms, cautious subjects). Test: tests/unit/tactical/ (retreat on sight).
4. tactical.py:213 PANIC branch (emotion.is_fleeing and _panic_holds): fires on perceived threats regardless of need; test: tests/unit/tactical/test_held_panic_falls_through.py.
5. tactical_hold.py:117 AVOID_NO_ROUTE hold (reason to be renamed NO_RETREAT_DESTINATION); presence/avoid verdict.
6. Follower adoption (item 6): the focus-fire target score uses `group.shared_target_id` (tactical.py ~:410-428, `group_bias`), so a follower fights the group's shared target; the hunger skip at :266 then applies because that target counts as a hostile in presence.
### Gaps and disclosures
- LHR_HOLD is gated on a pressing need: 0 in 15 runs. NO_RETREAT_DESTINATION holds WITHOUT a pressing need (e.g. low-hp e23) were not counted; the per-hold region facts (in region, home, boundary and building distances) were therefore not collected. Asked for, not widened.
- LHR_CARRY_WALK is an approximation (REGROUP walk, acting hostile, hp<0.5); the writer split above says how much of REGROUP is the town carry.
- ENG, LOW_HP_RETREAT, TOWN_RETURN and FLEE_LINE are probe-defined (lane B's definitions); harm joins are co-occurrence, not attribution.
