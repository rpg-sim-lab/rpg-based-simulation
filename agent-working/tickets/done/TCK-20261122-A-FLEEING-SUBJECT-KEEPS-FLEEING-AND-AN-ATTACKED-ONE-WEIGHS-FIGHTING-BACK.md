---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261122-A-FLEEING-SUBJECT-KEEPS-FLEEING-AND-AN-ATTACKED-ONE-WEIGHS-FIGHTING-BACK
phase: done
date: 2026-11-22
tags: []
---

# TCK-20261122-A-FLEEING-SUBJECT-KEEPS-FLEEING-AND-AN-ATTACKED-ONE-WEIGHS-FIGHTING-BACK

## Title
World rules: a subject that decides to flee keeps fleeing while its threat holds, and a subject under attack weighs fighting back (AGENCY-07 amendment and companion)

## Status
DONE

## Tier
hotfix

## Type
feature

## Priority
P1

## Request Summary
The owner approved 6 points as the expectation the goblin-30 fix is judged against (#715 7076062275, owner account, 07:41:21Z):
1. danger interrupts lower goals, and a resolved goal never blocks;
2. wary, then flee;
3. commit to flight;
4. fight back when cornered or when it judges it can win;
5. varied outcomes;
6. hunts end in reasonable time.

rpg-designer read the catalog at NEW 87792e3e8 (conflict-combat, agency-decision, survival-needs) and ruled on each point:
- Points 1 and 2 are already accepted rules: SURV-07, AGENCY-07, CONFLICT-04, and the CONFLICT-03 amendment of 2026-10-09.
- Points 3 and 4 need new catalog text. AGENCY-07 says when flight starts, but nothing says how long it holds, and nothing says when an attacked subject chooses to fight back. CONFLICT-03 gives only the PERMISSION.
- Points 5 and 6 are judging criteria for the fix (R7 and R6), not rules.

This ticket lands the catalog text for points 3 and 4, plus one optional Bible ch04 clarifying sentence for point 1.

## Scope
1. docs/world_rules/knowledge-agency/agency-decision.md: an AGENCY-07 amendment, "Flight holds once decided" (rpg-designer's proposed wording):
   > A subject that has decided to flee keeps fleeing while the threat that started the flight is still present to it (its pursuer still in reach or still closing), until it is out of the threat's reach or has reached safety. It does not return to an ordinary goal and then flee again within a few moments while the same threat holds. A NEW present threat may change the flight's direction; ending a flight is a decision made when the threat is gone, not a timer.
   Engineering, not this rule: the reach distance, what counts as safety, and any hysteresis band.
2. The same file: an AGENCY-07 companion (or an AGENCY-02 application), "Fighting back is a real option under attack":
   > A subject that is being attacked always weighs fighting back against fleeing. It turns and fights when its flight is failing (it is cornered, it is outpaced, or it is caught again and again) or when it judges, from what it perceives of itself and its attacker (strength, health, arms), that it can win. Neither "always flee" nor "always fight" is the rule; the choice follows the subject's own appraisal, disposition and condition.
   Kind-neutral: decided from properties, never from a kind. Engineering: how "flight is failing" is detected, and the "can win" estimate (the CONFLICT-03 appraisal; KNOW-02's caveat on true stats).
3. Optional, Bible docs/mechanics/04_strategic_cognition.md (goal hierarchy): "A completed or resolved objective carries no pull and never holds a subject against a present threat."
4. Cross-links in the catalog's link sections (CONFLICT-03/04 and AGENCY-02/07).

## Out of Scope
- Any code change. The goblin-30 fix is ruled separately, after the motive stage-2 trace (TCK-20261121-MEAT-EATERS-IN-FRONTIER-LIVING-WORLD-ATTACK-PEOPLE-FORTY-TIMES-MORE-AFTER-THE-NIGHT-AND-SLOT-FIXES).
- Changing R1-R7 or their thresholds.

## Acceptance Criteria
1. The owner approves the WORDING of items 1 and 2, via lead-planner-u24 and recorded on #715, before it lands. The intent is already approved in 7076062275.
2. The catalog text lands as approved, with the engineering lines kept out of the rule text.
3. If the ch04 sentence lands, it is consistent with the goal lifecycle as implemented, or a limits line cites the ticket.
4. make knowledge-index-update, then a REGISTRY regen.

## Related Tickets
- TCK-20261121-MEAT-EATERS-IN-FRONTIER-LIVING-WORLD-ATTACK-PEOPLE-FORTY-TIMES-MORE-AFTER-THE-NIGHT-AND-SLOT-FIXES (the goblin-30 bug candidate)
- TCK-20261109-M1-EACH-MONSTER-KIND-DECLARES-WHY-IT-FIGHTS (decision 62)

## Related Docs
- docs/world_rules/knowledge-agency/agency-decision.md (AGENCY-02, AGENCY-07)
- docs/world_rules/capability-progression/conflict-combat.md (CONFLICT-03 and its amendment, CONFLICT-04)
- docs/world_rules/life-body/survival-needs.md (SURV-07)
- docs/mechanics/04_strategic_cognition.md

## Related Stored Artifacts
None.

## Related Code Areas
None; this ticket is rules text only.

## Assumptions / Open Questions
- Whether "fighting back" lives as an AGENCY-07 companion or an AGENCY-02 application is a placement choice. rpg-designer allows either.

## Durable state, lifecycle and clocks
None.

## Implementation Notes
- Re-tiered from standard at close (2026-11-23, at lead-planner-u24's direction): rules text only, intent self-evident and owner-approved word for word; no code.
- Item 1 "Flight holds once decided" and item 2 "Fighting back is a real option under attack" landed as AGENCY-07 amendments, owner-approved wording (#715 7076062275 intent; the wording via lead-planner-u24): c65073a27.
- The designer's evidence line under the first amendment, and the ch04 sentence (item 3): e17a612bb.
- A third AGENCY-07 amendment, "A first strike when it judges it can win", owner-approved revised text (#715 7078497229 → 7078502579), landed word for word before AGENCY-08: c0b9896e9.
- Cross-links in conflict-combat.md's link section for CONFLICT-03 and CONFLICT-04 (item 4).
- AC3: the ch04 sentence is NOT yet true in code (Step A's A7: two strict xfails on #995). So a limits line in ch04 cites TCK-20261122-A-RESOLVED-OBJECTIVE-PULLS-A-FLEEING-SUBJECT-BACK-TOWARD-IT (added at close).
- Each amendment carries "Repository evidence: NOT YET SUPPORTED", naming Step A or Step B as its implementation.
- Rides in the same PR: the roadmap's systemic_foundation milestone name (42ad7eab5, owner #715 7064089876, under the epic's id), and 14 ticket filings under todos/.

## Test Summary
Docs only; no code and no test changes. No pytest: #995's W run holds u24.
- Checks (executed): yaml/frontmatter validation of the ticket; the docs search; make knowledge-index-update; make docs-registry.

## Files Changed
- docs/world_rules/knowledge-agency/agency-decision.md (three AGENCY-07 amendments)
- docs/world_rules/capability-progression/conflict-combat.md (cross-links)
- docs/mechanics/04_strategic_cognition.md (the resolved-objective sentence and its limits line)
- docs/plans/systemic_world/roadmap.md (milestone name, riding)
- docs/REGISTRY.yaml

## Completion Summary
The AGENCY-07 rules text for owner points 3 and 4, plus the first-strike amendment, landed word for word as approved. The ch04 resolved-objective sentence landed with a limits line, because code doesn't satisfy it yet (Step A). Implementation is Steps A and B, which this PR unblocks.
