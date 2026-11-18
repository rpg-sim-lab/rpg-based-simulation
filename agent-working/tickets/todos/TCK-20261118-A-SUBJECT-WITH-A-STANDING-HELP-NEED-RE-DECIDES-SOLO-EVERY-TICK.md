---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261118-A-SUBJECT-WITH-A-STANDING-HELP-NEED-RE-DECIDES-SOLO-EVERY-TICK
phase: open
date: 2026-11-18
tags: []
---

# TCK-20261118-A-SUBJECT-WITH-A-STANDING-HELP-NEED-RE-DECIDES-SOLO-EVERY-TICK

## Title
CooperationPhase re-runs the posture choice on every tick for any subject with a help need, so a subject whose need never clears picks SOLO and emits a cooperation_event on every tick, with no memory of its last decision

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Found by rpg-planner-ubuntu on the births head (relayed by the ubuntu lead and lead-planner-u24, 2026-11-18). On urban_political s42 1000t, original adults 10 and 28 emit cooperation_event with decision SOLO on every tick without a break, from 919 and 916 to tick 1000. The births PR does not re-pin that SOCIAL row (owner rule #715 6941107808).

Code read on main dca5a8dbb by rpg-planner (no run):
- `src/domains/cooperation/phase.py::CooperationPhase.execute` loops over every active, alive entity on every tick. It evaluates `HelpNeedEvaluator.evaluate` and, if there is a help need, a group or a pending offer, calls `CooperationDecisionService.select_for_own_needs`. It writes `last_cooperation_decision` into property_updates, and that write is what makes EventExtractor emit cooperation_event.
- `select_for_own_needs` (services.py ~:170-241) picks SOLO when solo_score = max(0, 1 - severity + bravery*0.4) >= 0.5 and no partner scores higher.
- Nothing remembers the last decision or holds it for a period. A help need that persists (for example, one SOLO never acts on) gives one identical decision per tick for as long as it lasts. The posture also lives in free-form `identity.properties["last_cooperation_decision"]`, not in a typed field (CLAUDE.md, Durable State Rule).
- `_record_decision_events` and the help-need events are capped only by `len(entity.timeline) < 150`, not by any decision lifecycle.

SECOND TRIGGER (rpg-planner-ubuntu's cause read, relayed 2026-11-18; rpg-planner confirmed the code on main dca5a8dbb): a group member with NO help need also re-decides every tick. The skip test lets an entity through when `identity.group_id is not None`, and `select_for_own_needs` then returns SOLO with trace reason "No help needs detected." (services.py ~:180-189), and the phase writes last_cooperation_decision again. Births head: entities 10 and 28 are in group 10018 (formed t918, live at t1000), so this trigger, not a standing need, may be the whole cause there. Main: entity 18 emits 460 per-tick events while in groups.

DESIGNER NOTE (rpg-designer side note (a), relayed by lead-planner-u24 on 2026-11-18, report-only): the event side is an event-on-no-change defect at P2. cooperation_event should be emitted only when the decision changes. This is folded into this ticket because it is the same code path as the second trigger. Step 2 still rules the decision side: whether to re-decide, and what a grouped subject with no need holds.

Whether SOLO leads to any action, and why the two subjects' need never clears, is NOT read. That is step 1.

## Scope
1. Evidence, with no behaviour change: on the births head and on main, for urban_political s42 and the 3 standard cells, count per subject the longest run of consecutive same-posture cooperation_events. Split the counts by trigger (a standing help need, or group membership with no need). For entities 10 and 28 (group 10018) and main's entity 18, name which trigger fires and, where there is one, the help need that persists, what SOLO maps to in CooperationIntentBridge.map_decision, and whether any project or task acts on it.
2. rpg-designer rules the class (a decision with no lifecycle, an unmet need, or both) and the fix shape before any code: for example, a typed last decision with a re-decide rule (need changed, or a hold period ended), and what a group member with no need should do (skip the posture choice, or keep a group posture instead of SOLO), and whether the posture moves out of identity.properties.
3. Fix, tests (a standing need gives one decision, not one per tick; a changed need re-decides), Bible text (ch. 07 cooperation), parity and divergence.

4. COST (perf-planner R4, relayed 2026-11-18; owner perf NFR #715 6968328816). The cooperation phase is the growing share of tick cost as population rises: 25%, 31% and 37% of the tick at 100, 200 and 400 synthetic entities, with super-linear total time (66/207/564 s per 1000 ticks). The per-tick re-decision this ticket removes is on that path. The fix reports a before/after profile of CooperationPhase.execute on the 3 standard cells and on a 400-entity synthetic world, under the M1 regression rule.

## Out of Scope
- The births PR's own SOCIAL row (not re-pinned there, as above).
- The resolve_blocker churn (TCK-20261117-A-RESOLVE-BLOCKER-PROJECT-IS-RE-CREATED-EVERY-80-TICKS-AND-STALLS-COOPERATION), though step 1 must say whether the two subjects hold a churning resolve_blocker in the same ticks.
- The DEFER_NO_PARTNER blocker re-creation (TCK-20261101-A-NO-PARTNER-BLOCKER-IS-RE-CREATED-EVERY-TICK).

## Acceptance Criteria
- A group member with no help need doesn't re-emit SOLO every tick. A test pins it.
- cooperation_event is emitted only when a subject's decision changes (rpg-designer). A test pins that an unchanged decision emits nothing.
- No subject emits the same cooperation posture on consecutive ticks unless its inputs changed, or the ruled hold rule allows it. A test pins it.
- The step 1 table is delivered, and the cause is named before the fix.

## Related Tickets
- TCK-20261117-A-RESOLVE-BLOCKER-PROJECT-IS-RE-CREATED-EVERY-80-TICKS-AND-STALLS-COOPERATION (same world and seed, cooperation stall)
- TCK-20261101-A-NO-PARTNER-BLOCKER-IS-RE-CREATED-EVERY-TICK (same per-tick re-decision family)
- TCK-20261010-CAMPAIGN-EPISODE-COOPERATION-SHARE-CROSSES-HALF-ON-MAIN-AFTER-BATCH-2 (per-entity-tick cooperation volume check)
- TCK-20261117-A-DANGER-CONCERN-IS-NEVER-REMOVED-ONCE-ITS-HOSTILE-NO-LONGER-MATTERS (a neighbouring never-exit loop, hero_guild_routing s42 entity 25)

## Related Docs
- docs/mechanics/07_social_political_dynamics.md (party coordination, cooperation posture)

## Related Stored Artifacts
- none (the births-head run belongs to the ubuntu lane)

## Related Code Areas
- src/domains/cooperation/phase.py (CooperationPhase.execute, _record_decision_events), src/domains/cooperation/services.py (select_for_own_needs), CooperationIntentBridge.map_decision, src/observability/event_shapers.py (cooperation_event)

## Assumptions / Open Questions
- Is the never-clearing need itself the defect (SOLO doesn't act on it), or only the per-tick re-decision? Unread; step 1 answers it.
- Is it HARD for births? lead-planner-u24 asked rpg-designer. This ticket doesn't decide that.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
