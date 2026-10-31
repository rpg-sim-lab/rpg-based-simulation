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
OPEN (counts first; ruled by rpg-designer 2026-10-31; seated by rpg-planner; not dispatched: needs an owner go, and an order ask is with the owner)

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

## Test Summary

## Files Changed

## Completion Summary
