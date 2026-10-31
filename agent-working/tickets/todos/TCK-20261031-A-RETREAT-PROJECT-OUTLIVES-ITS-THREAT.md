---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261031-A-RETREAT-PROJECT-OUTLIVES-ITS-THREAT
phase: open
date: 2026-10-31
tags: []
---

# TCK-20261031-A-RETREAT-PROJECT-OUTLIVES-ITS-THREAT

## Title
A retreat project outlives its threat (entity parked on COMBAT_RETREAT ~950 ticks with no threat, recovered, not moving)

## Status
OPEN. Phase 1 counts DONE (ubuntu, d2ed6c8c2 evidence/retention_trace/). Phase 2 fix shape RULED by rpg-designer 2026-10-31 (completion fact). Not dispatched: standard dispatch needs an owner go.

## Tier
standard

## Type
bug

## Priority
P1 (blocks the #769 SimQ re-anchor of urban_political s42)

## Request Summary
Found by rpg-designer's #769 check (TCK-20261030-SIMQ-ANCHOR-REDS-SINCE-V1-REANCHOR-NEED-A-BISECT, evidence/designer_check/README.md at f0e5a2897 on rpg-ubuntu-simq-anchor-bisect-impl). At d914bace7, urban_political s42 2000t, entity 18 holds proj_combat_retreat_42 over t63-1402: 950 ticks after t452 with no perceived hostile, 742 of them at hp >= 0.5, ~200 at full hp, sitting at about (25,25); retreat_pull changes no score and COMBAT_RETREAT is never the top raw score. Replaced by proj_fatigue_1402 at t1403. Pre-existing retention: #769's src diff is only the scorer and retreat_pull, it only changes who reaches it. #769 itself is CLEARED (designer ruling 2026-10-31).

Designer reading: a retreat moves away from perceived threats (tactical contract section 4, GAP-T03). Recovering while hurt is fine but is RECOVER/REST or no project, never COMBAT_RETREAT; idling at full hp is wrong under any label. A retreat project should end when its threat is gone AND the entity is clear of it; recovery is then an ordinary re-decision. Death should close open projects (count only here).

## Scope
Phase 1 (counts first, read-only probe, ubuntu side). Answers to the designer:
1. Which path keeps proj_combat_retreat_42 each tick t63-1402: (i) a pending COMBAT_RETREAT committed intention re-injected at _COMMITTED_INTENTION_BASE_UTILITY (intelligence.py ~1546; COMBAT_RETREAT is in _COMMITTED_INTENTION_ELIGIBLE_KINDS, :107-111), (ii) the best_candidate filter (intelligence.py ~1586: utility < 20 or no target_id/target_pos skipped; None keeps the current project), or another.
2. What ends it at t1403, and through which path.
3. Width: across 3 worlds x s42-46 at a25619971 and d914bace7, count retreat projects still active N ticks after their last present threat (N = 50, 200, 1000) and distinct entities; is "no living retreat holder" at the parent true across all seeds.
4. Dead entities with an open project (any kind).
Phase 1 answers (rpg-implementer-ubuntu; recounted by rpg-planner-ubuntu from raw logs; rpg-planner checked against code on main 6fdfdf555):
1. Not (i) and not (ii). 1273 of 1340 held ticks have no goal-selection call (scheduler brain cadence, scheduler.py `_throttled`, every 20 ticks; payload and wakes unmeasured). 60 of 67 calls (best RESOLVE_BLOCKER 57, RECOVER 3) return at the capacity gate (intelligence.py:1768 on main, :1771 at d914bace7): 3 live of max 3 (1 ACTIVE, 2 SUSPENDED, unlogged), `escalated_need_wins` False by code for those kinds. 6 calls: best is COMBAT_RETREAT, switch test keeps it.
2. t1402: FATIGUE past onset, `escalated_need_wins` True (escalation.py, HUNGER/FATIGUE only), switch runs: current score 0.0, lock expired t52, candidate 100.47.
3. Width (15 runs per commit, 2000t; lower bound, current project of living entities only): a25619971 10 runs / 26 projects / stale N=50 16 (9 never threatened while held), N=200 3, N=1000 0; d914bace7 14 / 37 / 12 (2) / 4 / 1 (entity 18 only). Predates #769. 26 of 28 N=50 rows end at hp <= 0.47.
4. About 62-67% of dead entities keep a current/ACTIVE project at both commits; split to TCK-20261031-DEATH-CLOSES-NO-PROJECT.

Phase 2 (designer ruling 2026-10-31): a COMBAT_RETREAT project COMPLETES when the threat it answered is no longer present. "Present" is the pull's own test: decision-32 adjacent hostile OR a perceived hostile acting on the entity (`acting_threat_to`). The end is typed (e.g. ended_by THREAT_CLEARED), never a reason string or lock_until_tick. The slot frees and the next selection is an ordinary re-decision (a hurt entity picks RECOVER/REST on its own scores). A returning threat starts a new retreat through the scorer. No hysteresis in v1; flapping (retreat -> complete -> retreat within a few calls) is measured and is the trigger to add one later.
Investigation (before plan): (a) where COMBAT_RETREAT's completion facts are defined today and what they test (destination reached? hp?); entity 18 sat at its destination, so if completion is "reached destination" say why it did not fire; the fix shape depends on missing vs misconditioned. (b) Log the 2 SUSPENDED projects filling entity 18's cap (ids, kinds, age) and count stale SUSPENDED records filling caps generally; that is a :1610 follow-up, reported as counts, not folded in.

WIDENED 2026-10-31 (rpg-designer ruling on the churn; lane C fix-arm a5631c4f3 showed 32 of 52 THREAT_CLEARED ends never threatened and 31 re-adoptions within 60 ticks, 30 at the next selection call):
- THE TEST on both sides is `present_threat_to` (src/ai/goals/present_threat.py; AGENCY-07's full terms: a perceived hostile with wounded, adjacent, targeting/closing or outmatching). This CORRECTS the earlier "decision-32 adjacent OR acting" wording for completion. `acting_threat_to` (memo row 88) is unchanged where it is: it gates retreat_pull's escalation and is the SURV-07 family table's "need yields only to" test.
- R1: CombatRetreatScorer (scorers.py ~235) adopts COMBAT_RETREAT only while present_threat_to holds; low hp, panic or is_fleeing alone do not (2.76's rule carried to the goal scorer; tactical already requires a threat to flee, 2.114). The utility formula is unchanged under the gate.
- R2: completion THREAT_CLEARED when present_threat_to stops holding.
- R3: a hurt subject with no present threat goes to RECOVER/REST on their own scores; verify RecoverScorer yields a candidate passing the selection filter (utility >= 20 and a target). Report ticks with hp < 0.5, no present threat and no RECOVER/REST/FATIGUE project current (about 0; any entity over 200 ticks is a finding).

## Out of Scope
- #769 (cleared). The groups-id fix (TCK-20261031-A-NEW-GROUP-ID-OVERWRITES-A-LIVE-GROUP), sequenced together with this before the s42 re-anchor.
- Closing projects on death: TCK-20261031-DEATH-CLOSES-NO-PROJECT.
- Any change to the capacity gate (intelligence.py:1768) or the :1610 lookup and gate rules (2.143): a 0.0-score project freeing its slot was REJECTED by the designer (it moves every kind). Fix the exit, not the gate.
- Hysteresis on retreat re-entry (only if the counts show flapping).

## Acceptance Criteria
1. Re-run the Phase 1 width count (3 worlds x s42-46, 2000t, same definitions): stale at N=200 and N=1000 is 0 at both a25619971-equivalent and d914bace7-equivalent bases (i.e. the fix on main); N=50 is reported, not gated. Flapping count reported.
2. Unit test: a retreat completes (typed THREAT_CLEARED) when the threat leaves, stays active while it is present, and a new retreat starts when it returns.
3. Main is hash-identical on the gate worlds, or every changed run is attributed to a completed retreat (first diff is a THREAT_CLEARED end).
4. Bible 04 / tactical contract section 4 state "a retreat ends when the threat is gone" as a law; parity ledger row added.
5. Divergence entry, class Enforced, if legacy behaviour differs.
6. No death/combat regression; s42 re-measured (500/1000/2000t) before the re-anchor.

Acceptance additions (widened):
7. Churn: re-adoptions by the same entity within 60 ticks with no present threat = 0; never-threatened adoptions = 0.
8. AC6 replaced: deaths BY CAUSE per world on a cause-logged re-run, both arms (the probe also logs hp, stamina, panic, bravery and the retreat/RECOVER/REST utilities at each retreat adoption). Any per-world rise that first-diff attributes to an ended or unadopted retreat is a STOP, reported to rpg-designer with victim ids; a rise first-diff puts elsewhere (trajectory) is reported, not gated.
9. Unit test from crowded s43: hp < 0.5 and no hostile in view -> RECOVER, not COMBAT_RETREAT; a closing hostile -> COMBAT_RETREAT; the hostile leaves -> completes THREAT_CLEARED.
10. Docs: the law "a retreat begins and ends on the same present-threat test" in tactical contract section 4 and Bible 04; parity row; divergence (Enforced, linked to 2.76) -- 2.156 / STRAT-295 carry it.
Overlap: TCK-20261028-LOW-HP-RETREAT (tactical.py:536-544) is NOT folded in (this ticket gates the goal scorer only); count the moved deaths/ticks also under it with the family-table tag.

## Related Tickets
- TCK-20261031-DEATH-CLOSES-NO-PROJECT (split from Q4); TCK-20261020-SUSPENDED-PROJECTS-ARE-NEVER-RESUMED-SLOT-LEAK and TCK-20261028-CURRENT-PROJECT-CLEARED-WITHOUT-ENDING-LEAVES-ORPHANED-ACTIVE-RECORDS (the stale SUSPENDED / orphan records that fill caps: counts go there, not folded in);
- TCK-20261030-SIMQ-ANCHOR-REDS-SINCE-V1-REANCHOR-NEED-A-BISECT; TCK-20261031-A-NEW-GROUP-ID-OVERWRITES-A-LIVE-GROUP; TCK-20260812-COMMITTED-INTENTION-SEQUENCE; TCK-20261002-COMBAT-OBJECTIVE-TARGETS-ENTITY-VIA-FIXED-POINT-AND-NEVER-TERMINATES (precedent: end a combat objective when its reason is gone)

## Related Docs
- docs/engine/contracts/tactical_contract.md section 4 (GAP-T03); docs/mechanics/04_strategic_cognition.md (goal hierarchy, interruption resistance)

## Related Stored Artifacts
- rpg-ubuntu-simq-anchor-bisect-impl f0e5a2897: evidence/designer_check/README.md

## Related Code Areas
- src/systems/strategic_systems/intelligence.py (capacity gate :1768, switch :1042-ish), project completion facts (location to find), src/ai/goals/present_threat.py, src/engine/scheduler.py (_throttled), src/ai/goals/scorers.py (retreat scorer)

## Assumptions / Open Questions
- Whether other kinds lack an exit test the same way: report, do not fold in.
- The committed-intention pointer (path i) was ruled out by the counts.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
