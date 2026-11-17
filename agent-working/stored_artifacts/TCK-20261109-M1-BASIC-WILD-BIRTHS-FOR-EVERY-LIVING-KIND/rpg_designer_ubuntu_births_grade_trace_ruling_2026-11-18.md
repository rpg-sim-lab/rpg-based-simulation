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
