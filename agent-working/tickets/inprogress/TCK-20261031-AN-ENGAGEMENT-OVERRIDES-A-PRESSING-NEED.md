---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261031-AN-ENGAGEMENT-OVERRIDES-A-PRESSING-NEED
phase: open
date: 2026-10-31
tags: []
---

# TCK-20261031-AN-ENGAGEMENT-OVERRIDES-A-PRESSING-NEED

## Title
An engagement overrides a pressing need: with hostiles in sight, tactical skips the survival step though no present threat is on the subject (SURV-07)

## Status
INPROGRESS (Phase 1 only: counts first; dispatched by rpg-planner under owner yes #715 6561198771)

## Tier
standard

## Type
bug

## Priority
P1 (the N14 re-measure trips on it; the designer advises it lands before that re-measure)

## Request Summary
From the s44 trace for the N14 STOP (lane B, existing new2 trace of urban_political s44 5000t, pre-#795, classification only). Subject 17 (scout) is fed and rested by 2.153 (one chosen rest t1814-2341, debt 72.7 -> 20, ended by the floor-end wake), leaves on a resolve_blocker project and stands at the inn door (40,24) from t2364 for ~1500 ticks in ATTACK or idle with NO hunger or fatigue project, at hunger 28 -> 100 and debt 20 -> 98; 10 kills at the door; then 17 collapses (t3914-4433) and death at t4434. tactical.py skips the hunger arrival and the in-place survival blocks whenever hostiles are present.

Designer ruling: this breaks SURV-07 ("only a present threat outranks a pressing need"). A hostile merely present, or a fight the subject started itself, is not a present threat TO it. 2.153's rest length and the floor-end wake are KEPT (they did their job); base's subject 17 (pinned starving at (66-67,24), hunger 100 all run) is a base defect, not a target to restore.

RULE (designer): a need past its escalation onset yields only to a present threat to the subject (decision-32 adjacent hostile, or a perceived hostile acting on it: `acting_threat_to`). Otherwise the survival step runs, even with hostiles in sight and even mid-engagement the subject started itself. A present threat still wins, as today.

## Scope
Phase 1 (counts first, read-only probe; no fix shape before rpg-designer reads them), on the 15-run set (3 gate worlds x s42-46, 5000t, base at or after 6fdfdf555):
1. Ticks where a subject has a need past onset (`need_is_pressing`), is in ATTACK, an engage project, or the tactical.py hostiles-present skip, and has NO present threat to it (no decision-32 adjacent hostile, `acting_threat_to` False). Per world, per run; distinct subjects; longest stretch.
2. Collapses and starvation (V3) deaths of those subjects.
3. How often the tactical.py hostiles-present skip fires per run, and on how many of those ticks a present threat exists.
4. Name every tactical.py site that skips the hunger arrival or an in-place survival block on hostile presence (file:line), and which test it uses (presence, engaged, acting).
5. FAMILY TABLE (rpg-designer 2026-10-31): one SURV-07 precedence ruling across ENGAGEMENT-OVERRIDES (this), TCK-20261028-LOW-HP-RETREAT-BRANCH-HOLDS-A-STARVING-SUBJECT-IN-PLACE-BESIDE-A-NON-ACTING-HOSTILE, TCK-20261021-A-SUBJECT-IN-A-FIGHT-IT-CHOSE-NEVER-DISENGAGES-AT-ITS-FLEE-LINE, TCK-20261020-TOWN-RETURN-OUTBIDS-AN-ESCALATED-NEED-UNTIL-ABOUT-95 and TCK-20261029-AN-ESCALATED-NEED-THAT-WINS-SCORING-LOSES-THE-PROJECT-SWITCH. All five are counted in ONE probe on the same 15-run set (preferably lane B's F3 base run), with the same present-threat test (decision-32 adjacent hostile OR `acting_threat_to`) and the same need line (`need_is_pressing`, past escalation onset). Every counted tick carries a tag per ticket it falls under; totals count a tick once; the overlap matrix is reported. One extra tag (designer): CAP_REFUSAL, a tick where the capacity gate (intelligence.py:1768) refuses the subject's best candidate, with the count of SUSPENDED records in its live set (link to TCK-20261020-SUSPENDED-PROJECTS-ARE-NEVER-RESUMED-SLOT-LEAK).
6. FOLLOWERS (designer 2026-10-31, s44 hazard-pack trace, lane B pack_new2_s44.jsonl): 2, 5, 1, 6, 9 each dropped its own need past onset to take subject 13's pursuit target (scout 16, never acting on any of them); count followers individually. List the site that makes a follower adopt a leader's/party's target (party coordination or leadership influence) in item 4. Under the rule a follower keeps its pressing need unless the target is a present threat to the FOLLOWER.
7. Unit test case (Phase 2): built from that trace's state at t1605-1610: subject 13 (hunger 80, past onset) pursues a fleeing scout 16 that never attacks it; under the rule 13 keeps its hunger project.
Phase 2: fix shapes for ALL five only after the table reaches rpg-designer.

## Out of Scope
- A' (sleep vs hunger, TCK SLEEP-WINS): same family, linked; A' is read against this rule after it lands.
- The low-HP retreat branch (TCK-20261028-LOW-HP-RETREAT-BRANCH-HOLDS-A-STARVING-SUBJECT-IN-PLACE-BESIDE-A-NON-ACTING-HOSTILE), the flee line (TCK-20261021-A-SUBJECT-IN-A-FIGHT-IT-CHOSE-NEVER-DISENGAGES-AT-ITS-FLEE-LINE), town return (TCK-20261020-TOWN-RETURN-OUTBIDS-AN-ESCALATED-NEED-UNTIL-ABOUT-95), the project switch (TCK-20261029-AN-ESCALATED-NEED-THAT-WINS-SCORING-LOSES-THE-PROJECT-SWITCH): count overlaps, do not fold in.
- The s44 hazard pack: TCK-20261020-ENGAGE-BRACKETING-MOVES-WALK-A-GROUP-INTO-A-HAZARD-CLUSTER (designer rules after the target-dump re-run).
- N14 (2.153, 2.154): kept; its STOP is not waived by this attribution.

## Acceptance Criteria
(Phase 2, designer to confirm) A subject with a need past onset and no present threat runs its survival step with hostiles in sight; a present threat still wins; the Phase 1 tick count falls to about 0; no rise in deaths by cause; parity row (SURV-07, Enforced); divergence entry if legacy differs.

## Related Tickets
- TCK-20261021-A-CROWDED-SERVICE-DOOR-BLOCKS-A-STARVING-SUBJECT (N14); TCK-20261031-A-SLEEPER-HOLDS-A-DOOR-OR-SERVICE-TILE (F3); A' SLEEP-WINS; the four Out of Scope tickets; TCK-20261023-AN-ACTING-HOSTILE-IS-AN-ACT-NOT-A-STATE (memo row 88).

## Related Docs
- docs/world_rules (SURV-07, AGENCY-07); docs/mechanics/04_strategic_cognition.md; docs/plans/systemic_world/owner_decision_memo.md rows 88, 93

## Related Stored Artifacts
- lane B s44 traces: /mnt/data/scratch-rpg-implementer-2/n14/

## Related Code Areas
- src/ai/tactical.py (hunger arrival ~262-291, in-place survival blocks); src/ai/goals/present_threat.py; src/engine/need_pull.py (need_is_pressing)

## Assumptions / Open Questions
- Phase 1 can share F3 investigation item 1's 15-run base (same set and base) if the probe fields are added to that run (planner proposal to the owner).

## Implementation Notes
- 2026-11-02 PHASE 2 (code, not yet measured; rpg-designer ruling `.claude/handover/drafts/rpg-designer-surv07-phase2-ruling-ACKED.md`). Predicate pair: `need_pull.need_is_pressing` (`entity_need_is_pressing`) and `tactical_threat.need_yields(entity, hostiles, tick)` (`present_threat.acting_threat_to` is the same predicate over perceived hostiles). `tactical.py`: `need_first` branch (pressing, hostiles in sight, none acting) runs before the presence test, role obligation, cohesion and target selection; the objective step moved unchanged into `src/engine/tactical_objective.py` (new, split into small functions). `tactical_rest.py`: `_in_danger` uses `need_yields` in the pressing branch only. Divergence 2.157, parity STRAT-297, Bible 04 paragraph (DRAFT for rpg-designer).
- CHANGED EXPECTATIONS (named for the PR body): (1) `tests/unit/engine/test_rest_in_place.py::test_a_present_threat_means_no_rest` now holds at sleep_debt 50 (below the onset); its pressing rows moved to `tests/unit/tactical/test_surv07_precedence_grid.py` (rpg-planner ruling 2026-11-02). A hostile targeting by payload alone at distance 9 lands on REST under a pressing need (not an act). (2) `tests/unit/tools/test_mechanism_registry_completeness_check.py::test_wider_scope_numbers_pinned` scope_files 351 -> 352 for `src/engine/tactical_objective.py` (pre-approved by rpg-planner; taken from the check's real count at the re-sync onto 65d43dfa9; unbound_files stays 247, see the next note).
- (2026-11-02) src/engine/tactical_objective.py is bound under `tactical_decision` in registries/mechanisms.yaml (rpg-planner ruling), so the unbound_files pin stays 247 and only scope_files moves (351 -> 352).
- 2026-11-02 S2 REMOVED (rpg-designer correction, memo row 88 S1): tactical_rest.py is back on the AGENCY-07 terms (identical to origin/main); `test_rest_in_place.py` is restored to its original expectations (the 'changed expectation (1)' above no longer applies); the grid file's rest and eat-carried rows now assert row 88. HELD AS DRAFTS (rpg-planner): divergence 2.157, parity STRAT-297, the Bible 04 paragraph and the present_threat.py docstring still describe the S2 shape for the in-place rest/eat sites and are stale on that point until the designer re-reads. 3e3a24d10 is the S2 arm.
- Disclosures: a pressing subject whose project is not a need project waits (does not engage) while nothing acts on it; `_suspend_project_for_threat` still suspends non-need projects; the unit grid is the only evidence so far (no paired run yet).
- 2026-11-01 OPEN GRID ROW (designer, from the retention STOP #2): whether a present threat outranks the live project cap is a precedence site. It sits beside CAP_REFUSAL on TCK-20261020-SUSPENDED-PROJECTS-ARE-NEVER-RESUMED-SLOT-LEAK. Before any rule: the causal trace of crowded s46 e14 t366 (displaced record, base behaviour, the chain to the 9 fix-only deaths by attackers 28/30) and e9's t1056 death path. A cap exemption for retreats was tried and dropped (retention afacf1577: 5 death-rise first diffs at cap-exempt adoptions).
- 2026-10-31 HARM PER TAG (designer's ordering input) cannot come from the F3-base outputs, which hold only per-tag totals. It RIDES ON THIS TICKET'S OWN BASE BATCH: one extended probe = fixed skip counter + per-subject tag id sets + per-subject ticks at/past the starvation line + per-subject ticks at fatigue debt >= 98, + per-subject death cause and tick + per-subject collapse count (designer addition), so deaths by cause and collapses join to tags. All five tags (ENGAGEMENT_OVERRIDES, LOW_HP_RETREAT, TOWN_RETURN, ESCALATED_NEED_SWITCH, FLEE_LINE). The designer fixes the site order from that table before this ticket's fix is planned.
- 2026-10-31 DESIGNER RULING (SURV-07 family, from the F3-base family table). THE ONE PRECEDENCE LAW P: at every decision site choosing between a need past its escalation onset and any other goal or act, the need wins unless acting_threat_to(subject) holds (memo row 88: a perceived hostile attacking or pursuing the subject, or one that hit it within the window). No owner row is needed. Whether to flee at all stays on present_threat_to (AGENCY-07); where flight is warranted but the hostile is not acting, a pressing need still wins. ONE shared predicate pair, both reads: need_is_pressing(subject) (need_pull ESCALATION_ONSET line) and need_yields(subject, state) = acting_threat_to. Every site calls them; none re-derives them. ONE PRECEDENCE GRID test: {need pressing y/n} x {no hostile / perceived only / present-not-acting / acting} x site -> winner; each site's ticket adds its rows. Provisional order until harm-per-tag is counted: ENGAGEMENT -> LOW-HP-RETREAT -> TOWN-RETURN -> ESCALATED-SWITCH -> FLEE-LINE.
- THIS SITE: engaging, pursuing or attacking a non-acting hostile loses to a pressing need; self-defence against an acting hostile wins; followers are judged individually. THIS TICKET LANDS THE TWO PREDICATES AND THE GRID TEST; the other four adopt them. Fix the skip counter and measure its own base first.

- 2026-10-31 F3 base (lane B, 15 runs on 6fdfdf555): family table recorded and sent to the designer. ENGAGEMENT_OVERRIDES 5872 ticks / 62 subjects / longest 254 (9 collapsed, 0 starved); LOW_HP_RETREAT 4963/40/270; TOWN_RETURN 3552/20/272; CAP_REFUSAL 9406/233/1; FLEE_LINE 1177/99/50; ESCALATED_NEED_SWITCH 1699/153/1.
- PROBE DEFECT to fix here before this ticket's own base: the tactical hostiles-present skip counter recorded 0 skips over 131785 evaluate calls, so there is no (pressing, present_threat) split. Lane B's untested guess: the wrapper patched the module attribute `_tac.classify_neighbours`, but `evaluate_entity_intent` may reach the classifier through another binding, so the stored hostiles count stays empty. The AC: the fixed counter must be non-zero on a known case (13 pursues 16) before any base is measured.

## Test Summary

## Files Changed

## Completion Summary
