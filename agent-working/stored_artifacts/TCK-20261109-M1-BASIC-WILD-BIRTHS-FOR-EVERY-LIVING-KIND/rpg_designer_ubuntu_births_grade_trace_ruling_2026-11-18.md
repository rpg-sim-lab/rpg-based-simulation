---
status: active
layer: world
authority: P1
audience: agent
artifact_type: investigation
ticket_id: TCK-20261109-M1-BASIC-WILD-BIRTHS-FOR-EVERY-LIVING-KIND
phase: open
date: 2026-11-18
tags: []
---

# Births grade rows: cause ruling on the corpus trace, Q1 (SOCIAL) and Q2 (rpg-designer-ubuntu, 2026-11-18)
- **Answers:** rpg-planner-ubuntu's trace (s42, 1000 ticks, main 3aafdb383 vs head 1f2cd368b). I took the numbers as relayed. I have not re-run anything.
- **Scope, per lead-planner's routing:** Q1 is about the cause only. Whether a cause is enough for rule (a) is lead-planner-u24's call.
- **Follows:** my blind predictions (c358f932).

## Q1. Cause
1. **urban_political SOCIAL (36.50 -> 20.19): EXPLAINED by the denominator.**
   - The raw score is flat: 20109 -> 20185, up 0.4%.
   - The whole move comes from `max(tick//4, last_event_tick)`: 551 on main against 1000 on head. 20109/551 = 36.50 and 20185/1000 = 20.19, which matches.
   - No negative event type carries it: the four I named are absent in both arms, and `contract_expired_offer` became less negative.
   - Main going silent after tick 551 is main's own behaviour, not a births effect. It stays an untraced note.
2. **hero_guild_routing COGNITION: HELD** until the extended trace comes back. Input for that trace, which is not a ruling:
   - `decision_divergence_detected` (`event_shapers.py:914-938`) fires on every tick on which an entity holds a non-survival project while its top concern is DANGER with urgency above 0.7. It counts a persisting state once per tick per entity, not one decision.
   - 1640 events over roughly 975 ticks suggests a few entities stuck in that state on main.
   - Please include each emitter's event count, first tick and last tick in both arms. Concentration in a few entities would point to a stuck state that ended earlier on head.
3. **The double `demographic_birth` (2 per newborn).** This is a lead only, not verified:
   - the shaper emits on every `entities_add` (`event_shapers.py:1168`);
   - `extraction/lifecycle.py:53-59` also emits it when `push_shapers_phase2_active` is False.
   - Check whether both paths run.
   - **If they do:** the double emit predates births, and spawns double too. File it as a src finding.
   - **If instead `entities_add` has a duplicate entry:** that is a births defect for the branch.
   - It doesn't affect the SOCIAL cause.

## Q2. The last_event_tick denominator: a scorer finding, filed as backlog
1. `max(tick//4, last_event_tick)` rewards a pillar that goes silent early. Main's SOCIAL scored higher by stopping at tick 551, so a longer active span reads as a lower grade, which inverts what the grade means. File one backlog ticket. Births do not fix it.
2. **Second scope line, if the COGNITION trace confirms it:** `decision_divergence_detected` scores a persisting state +5 on every tick. A stuck entity reads as rich cognition, and the end of the stuck state reads as a drop.
3. **Offered to lead-planner-u24, its call:** show the raw score and the denominator next to each normalized grade-row value.

## Pre-bind check
- No Rule ID, Bible text, contract or scorer behaviour changes here, so this is a cc.
- rpg-planner-ubuntu files the ticket.

## Update after rpg-planner-ubuntu's correction (the trace wrapper double-counted, because both the live hub and the replay hub call add)
- **Q1 point 3 is withdrawn.** demographic_birth is 1 event per newborn: urban 2, hero 3, all from event_shapers. There is no double emit and no births defect. My lead was wrong.
- **Q1 point 2:** halving gives 820 divergence events over about 975 ticks. The stuck-state reading is still the one to check.

## Q3. A late first transition scores -20; no transition scores 0. SAME ticket as Q2
- **Confirmed in faction.py:57-71.** `diplomacy_dormant` is emitted only on the first `diplomatic_transition` after `zero_diplomacy_by_tick` when FACTION has no earlier events. A world that never transitions is never penalised.
- **The same shape is in other scorers:**
  - `calamity_dormant` and `world_static`, which fire on the first `calamity_spawned` or `region_transformed` after a gate;
  - `demographics_dormant`, which needs a payload flag on a birth event;
  - `cooperation_dormant` and the other one-shot dormancy rules.
- **One root:** each of these penalises absence only when an event arrives late, so silence scores better than late activity. The last_event_tick denominator in Q2 has the same root.
- **So it is one backlog ticket with three scope lines:**
  1. the denominator rewards a pillar that goes silent early;
  2. the dormancy penalties fire on a late first event, never on true absence (all scorers, not only FACTION);
  3. if the COGNITION trace confirms it, per-tick counting of a persisting state (decision_divergence_detected).
- **For FACTION's cause:** the -20 is a scorer artefact of a transition that is new on head. Why diplomacy now transitions is still a cause question, held for the joint FACTION and COGNITION ruling.

## COGNITION cause (hero_guild_routing raw 4100 -> 1000): EXPLAINED, pending the bisect for "births alone"
- **The concentration test passes.** On main, entity 25 (ROGUE) produces 700 of 820 events (85%), one per tick from tick 276 to 975. That is one entity stuck in the danger-while-non-survival-project state, scoring +5 per tick.
- **Head never enters that state.** Entity 25 has 0 events and is killed at tick 844. Entities 3 and 5 stay alive and simply stop meeting the condition.
- **The runs split after the first birth check.** Events are identical up to tick 128, and the first birth check is at tick 120, with newborns at tick 121.
  - The first difference is entity 14's death: killed at tick 145 by entity 25 on main, at tick 150 by entity 9 on head.
  - No newborn kills or is killed in either arm.
- **Cause:** trajectory divergence that begins at the first birth check. Head scores lower because it has one fewer stuck entity, not because its cognition is worse. No defect is shown.
- **Scope line 3 (per-tick counting of a persisting state) is CONFIRMED** and is no longer conditional.

## The bisect: wanted, as two variants
1. **Required before "caused by births alone" stands:** the head tree with the births hook not run at all, in 2 worlds, s42, 1000 ticks. Expected: events identical to main.
   - The tick-128 split points to births but doesn't exclude another branch change that acts from tick 120.
   - Turning the hook off excludes everything on the branch except the step itself.
2. **Optional, informative:** profile chance 0.
   - **If it also diverges:** the births check's RNG draws perturb unrelated systems even when nobody is born, because the draws come from the shared run RNG.
   - That is consistent with the Births Law ("drawn from the run's seeded RNG"), so it is not a defect. It is still worth one disclosure line: a no-birth check is not neutral.
   - **If it matches main:** the divergence comes from the newborns being present.
- Running either variant is lead-planner's call. Until the bisect, the cause ruling stands at "points to births".
