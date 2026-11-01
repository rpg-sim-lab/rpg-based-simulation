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
ONE FUNCTION (designer): the adoption gate, the completion rule and tactical.py:209/213's `threats` use one helper; plan.md states what `threats` is built from, and a mismatch is a finding for rpg-designer, not a silent swap. Law cited: 2.114 and Bible ch2 section 7 CONFLICT-04.
BASE: measured on main 6fdfdf555 (pre-F3), stated in the evidence; whichever of this ticket and F3 (TCK-20261031-A-SLEEPER-HOLDS-A-DOOR-OR-SERVICE-TILE) lands second re-measures on top of the other (RECOVER walks to the inn, whose door and bed rule F3 changes).
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
- 2026-11-01 STOP #2 (afacf1577, shape (d) + cap exemption): deaths 344 -> 346; 5 of 6 death-rise first diffs are cap-exempt adoptions (crowded s46 22 -> 31 from e14 t366); retreats 42 -> 120; e18 fixed; e9 had a retreat and still died. DESIGNER RULING: Q1, DROP the cap exemption and land shape (d) alone after its own re-measure (no narrowing; the trace is not blocking). REMOVE the intelligence.py:1768 retreat exemption, the never-suspend clause, their tests and their doc text; 2.156 states no cap behaviour; the owner push ask drops the cap widening. RE-MEASURE (d alone, 15 runs, base 6fdfdf555): STOP on any per-world rise in deaths by cause (victim ids + first diff); e9/e18/e19 by name (e9 cap-refused under a threat is the known base gap, reported, not a STOP); retreat projects, re-adoptions and ends (how much of 42 -> 120 was the exemption); the N=200 stale holds (was present_threat_to true through each hold? if not, a defect); R3 reported only. Exemption follow-up: an open row in law P's grid (ENGAGEMENT-OVERRIDES), with the e14 causal trace (displaced record, base behaviour, the chain to the 9 deaths, e9 t1056) run when a slot is free, not gating. Planner question sent separately: whether the town_center destination walks retreat holders into hostiles (6 of the 9 dead were holding a retreat).
- 2026-11-01 DESIGNER: CAP EXEMPTION GOES INTO THIS TICKET (SCOPE WIDENING; the push ask must present it alongside the earlier widening). SURV-07 ranks a present threat to life above a pressing need, so refusing flight at a full cap while pressing HUNGER/FATIGUE get through inverts the law (law P's mirror; no owner row). Rules: (1) GATE: at intelligence.py:1768, a NEW COMBAT_RETREAT candidate while present_threat_to holds passes the capacity gate exactly as escalated_need_wins does (same mechanism, same choice of what yields the slot, no new eviction rule). (2) NO SUSPENSION: an ACTIVE COMBAT_RETREAT under present_threat_to is never the record that cap pressure suspends; with the threat absent it is an ordinary project and shape (d) governs its end. (3) Scope guard: retreat only. RECOVER gets no exemption (a wound alone is not a threat); COMBAT_ENGAGE belongs to ENGAGEMENT-OVERRIDES. (4) Tests: an e18 test from the trace (cap 3/3 with an adjacent hostile: a retreat is adopted, and a held retreat is not suspended); the precedence-grid rows (cap full x present threat y/n x retreat/need/other). The grid lands with ENGAGEMENT-OVERRIDES, so this ticket writes its rows as a standalone parametrised test that the grid adopts later. Re-measure: shape (d) plus this, reported as before, R3 kept. No re-run for attacker positions; add them to the probe only if re-engagement deaths remain.
- Shape (d) plan rulings (planner): cleared_since on ProjectState (omitted while None), one writer, note_threat_state, through StrategicUpdate; CLEAR_TICKS beside the COMBAT_RETREAT project constants; a SUSPENDED retreat's window does not advance and RESTARTS on resume. e9 (A) facts were sent to the designer: present threat TRUE and acting at t1131, cap 3/3 for ~240 ticks.
- 2026-11-01 BATCH STOP + DESIGNER RULING. Batch on 23e0f9967 (15 runs x both arms, base 6fdfdf555): stale 8/4/1 -> 0/0/0; never-threatened adoptions 767 -> 0; churn 30 -> 0; net deaths 344 -> 339. BUT urban s42 8 -> 16 and frontier s43 21 -> 31, each with its first diff at a THREAT_CLEARED end: e18 / e19 at hp ~0.06 are re-engaged and killed by attacker 17 within 60-110 ticks. Q1: HOLD. The STOP stands and a net -5 does not waive it.
  CAUSE (designer): the completion was built narrower than ruled. The ruling was "the threat it answered is gone AND the entity is clear of it"; the implementation was "no present threat this tick" only.
  SHAPE (d): a COMBAT_RETREAT completes THREAT_CLEARED when present_threat_to is false AND either (1) it has REACHED its retreat destination (town_center), or (2) present_threat_to has been false CONTINUOUSLY for CLEAR_TICKS = 200, a named constant in the retreat table. A returning present threat restarts the window. While no threat is present the retreat keeps walking to its destination ((A) concerns only the tactical flight). Adoption is unchanged (present_threat_to only); never-threatened 0 and churn 0 must still hold. Rejected: (a) an hp line, which brings the stale hold back; (b) attacker memory, more machinery than needed.
  R3 (33 -> 32): a separate base defect, not a precondition. Needs ONE trace (e18 urban s42, e19 frontier s43, THREAT_CLEARED -> death): each selection call with its winner, RECOVER's modified utility, the live set (cap and which SUSPENDED), any gate refusal. A cap refusal files under TCK-20261020-SUSPENDED-PROJECTS-ARE-NEVER-RESUMED-SLOT-LEAK; a score loss is a scorer ticket.
  Q3 (A): e9 does not hold (A) on what we have. Needed: at e9's fatal fight (t1145) was present_threat_to TRUE, and who was the killer? A present threat means trajectory and (A) lands; no flight test firing up to the hit is a finding for the designer. e29 (fl s42, a flight with no perceived hostile) is a separate follow-up row.
  RE-MEASURE: the same 15 runs; deaths by cause per world; the first diff for every run with a death rise; R3; churn. 2.156 and the close stay held until the designer reads it.

## Test Summary

## Files Changed

## Completion Summary

## Landing-order condition (rpg-designer 2026-10-31)
TCK-20261031-A-RETREAT-PROJECT-OUTLIVES-ITS-THREAT is measured on 6fdfdf555 (pre-F3). Whichever of it and TCK-20261031-A-SLEEPER-HOLDS-A-DOOR-OR-SERVICE-TILE lands SECOND repeats, on top of the other, retention's recovery check (ticks with hp < 0.5, no present threat and no RECOVER/REST/FATIGUE project current; any entity over 200 ticks is a finding) and deaths by cause per world.

## Tactical flight gate (rpg-designer ruling (A), 2026-10-31)
Finding (lane C): tactical.py:209/213's `threats` is `perceived_threats` (tactical_threat.py:64-75), perceived hostiles WITHOUT the AGENCY-07 terms; it agrees with present_threat_to whenever hp < 0.7 and differs for an unhurt subject fleeing (dread, grudge) a distant, idle hostile.
Ruling (A), inside this ticket, counts first: tactical's flight gate also calls present_threat_to. It carries 2.76 (retreat from a present threat, not on sight) to the last ungated branch; not a new rule.
- Counts before it lands (probe9, same base): ticks where tactical flees on perceived_threats while present_threat_to is False; distinct entities; hp and the hostile's distance at each; then deaths by cause of those entities on the paired run.
- Land (A) unless first-diff attributes a death to a flight (A) removed; then it goes to rpg-designer with victim ids and (A) waits.
- Docs: the divergence names 2.76 and 2.114 as narrowed (2.114's flight rule now uses the AGENCY-07 terms). Law text: "flight, a retreat project's adoption and its completion use one present-threat test".


- **2026-11-01 landing-order item (from F3):** if this lands after F3, add a test that cleared_since advances while a subject is lodged (F3 suppresses movement intent only; the strategic pass still runs for lodgers).

## Re-measure ruling (rpg-designer, 2026-11-01; fix 5c6001620 vs base 6fdfdf555, 15 runs per arm)
- **Accepted:** no Tier 1. Crowded HAZARD rises in 1 seed only. The crowded s43 first diff (retreat_41 THREAT_CLEARED at t142) is trajectory.
- **Gap to close first:** the mechanism test is widened to cover option A. Within 200t of death, a victim counts if it had a retreat adopted or completed under the new rules, OR a tactical flight decision that option A changed (present_threat_to vs perceived_threats, tactical.py:209/213).
  - Check every flight-relevant tick in the 200t before death for urban s42 e14 and s46 e3 and e13 (PANIC_RETREAT), s45 e16, and the 7 crowded s43 victims.
  - Same answer from both tests is FAIL. A different answer may PASS; the rows go to the designer.
- **e9 (fl s46):** a base gap (byte-identical to base). It goes to TCK-20261031-DEATH-CLOSES-NO-PROJECT, and as a named case in TCK-20261101-A-RETREAT-WALKS-TOWARD-THE-THREAT, with the distance trend over the last 30t and where the town_center walk took it.
- **The destination ticket is now P3.** REGROUP 0->8 hazard entries go to ENGAGE-BRACKETING as H1/N3 evidence. No owner H1 row.
- **Close list:**
  - 2.156 Measured states no cap behaviour and names both changes;
  - disclosures: R3 to the slot-leak ticket; the 2 N=200 holds; destination P3; the REGROUP H1 evidence; e9 as a base gap;
  - F3 lands first, then retention re-measures on F3 (the same 15, the same bar, the recovery check, deaths by cause);
  - the owner push ask names one scope widening (option A, tactical flight).
- **Flight check (lane C probe12, local 335793b2c; designer ACK 2026-11-01):** option A changed no flight decision for any victim. 369 flee ticks, 0 disagreeing. All 11 Tier 2 victims FAIL, so the Tier 2 pairs are divergence.
  - The on-F3 re-measure fills 2.156 Measured and AC9. This set is cited as the pre-F3 reading (c861855da, 335793b2c).
  - On-F3 conditions: any tier-1 cause gets the full Tier 2 trace again (200t, both changes); never-threatened adoptions must stay 0, and a rise is a STOP.
