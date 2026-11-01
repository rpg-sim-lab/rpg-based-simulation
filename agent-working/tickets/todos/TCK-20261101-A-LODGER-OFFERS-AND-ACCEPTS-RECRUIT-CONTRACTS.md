---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261101-A-LODGER-OFFERS-AND-ACCEPTS-RECRUIT-CONTRACTS
phase: open
date: 2026-11-01
tags: []
---

# TCK-20261101-A-LODGER-OFFERS-AND-ACCEPTS-RECRUIT-CONTRACTS

## Title
A lodged stayer still offers and accepts recruit contracts, and a formation can elect it leader and bind it as holder (F3 seam: cooperation is a third decision path)

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
F3 (TCK-20261031-A-SLEEPER-HOLDS-A-DOOR-OR-SERVICE-TILE, merged 30307228c) rules that a lodged stayer emits no intent, and suppresses two entry paths. The groups churn re-measure on F3 (ubuntu groups batch C, TCK-20261031-A-PAIR-RE-FORMS-AND-LEAVES-A-GROUP-EVERY-TWO-TICKS) found a third path. In frontier_living_world s44 (churn arm, probe hash equal to the unprobed arm), 3 formations chose a lodged stayer at building 20003 as leader and bound holder. They are groups 10078, 10080 and 10082, all formed on recruit contracts. No death followed. The lodged-at-group-decision count also rises across seeds (frontier s44 0->738, s45 0->1192; urban s42 455->1454).

Cause (rpg-designer, from the code read): cooperation is a decision path that F3's two-entry suppression missed. `src/domains/cooperation/services.py` maps REQUEST_HELP / HIRE_SUPPORT to `ContractService.create_recruitment_contract` (around :280) with no lodging check on the source or the partner. This is the same on both trees (main and the churn arm), so it is an F3 seam defect. The churn fix only exposes it more often.

rpg-designer ruling (2026-11-01): this is a ROW, not a STOP on batch C, and it does not gate batch C.

## Rule (rpg-designer 2026-11-01; shared with TCK-20261101-A-LODGER-DECISION-PATH-AUDIT; the rule does not split)
(1) A lodged STAYER (lodged and not leaving this tick) takes no new decision of any kind: no project, goal, objective, offer, accept, counter, payment, interaction, reproduction, engagement posture or visit. F3 class (a) was ruled as "SUPPRESS intent emission", so suppressing only the walk writers is the landed code falling short of that ruling, not a new design. Allowed, and nothing else:
- (a) The wake re-decision (rest end, the hunger wake 2.115, and a threat wake where reachable). Its outcomes are limited to:
  - stay;
  - leave (place_leavers; a leaver is no longer a stayer from that tick);
  - an in-building service at its own lodging building (EAT at an inn, F3 Scope 7).
  Anything else it produces is dropped while the subject stays.
- (b) Passive state: time, needs, body, memory, cleared_since, progression conversion. Any choice inside it is the same as it would be outside.
- (c) Standing records keep their lifecycle: membership (rule 2), an existing contract's term, and group end checks applied to it as a member. No defection while lodged: defection is a new decision.
- (d) Absent to others: it cannot be chosen as a partner, offeree, counter-target, reproduction partner, payee or engagement target (appraisal.py:183; this matches appraisal.py:48).
(2)-(4) as in Scope items 3-5 below.

## Scope
Ticket 1 of 2 (rpg-designer accepted the split 2026-11-01): the MEASURED social paths only. The remaining rows of ubuntu's 59-row path list go to TCK-20261101-A-LODGER-DECISION-PATH-AUDIT, which extends this ticket's predicate and test list. No second mechanism is built.
1. Code read first, written into investigation.md: verify each cited social path's file:line at the implementing head (cooperation offer/accept/counter/help request, being chosen as partner, formation, election, holder binding, defection, follow/regroup).
2. Introduce ONE shared predicate, `is_lodged_stayer`, read at each covered decision phase's entity loop (as actor) and in partner/offeree candidate filters (as (d)). No per-site special cases. Suppress NEW social decisions by a lodged stayer: offers, acceptances, counters and help requests, as the source or as the partner, and defection.
2a. An architecture test that lists every phase that writes a decision record and asserts that it reads the predicate. It starts with this ticket's phases; the audit ticket adds its phases to the same list. It lives under tests/architecture/, so testing-planner's OK on placement and shape is needed before implementation.
2b. Parity: check 2.155's text and Bible ch.04 section 1 against the landed code. If the text already says "emits no intent", the ledger has been wrong since #823. Record that and correct it with this fix.
3. Election and leader choice skip lodged members while a non-lodged member is eligible. Holder binding follows the same rule.
4. Existing membership persists through lodging. It is not dissolved or left because the member lodged.
5. Rule (4) (rpg-designer, 2026-11-01): while a leader is lodged it is ABSENT for following and regrouping. Followers outside do not target its building or reach tile; they act on their own. An election picks a non-lodged member. Whether this ships as a behaviour change now, or as a guard with a test only, depends on ubuntu's s45 / urban s42 outside-follower count.
6. The fix reads lodging state, not distance. The distance check passes for co-lodgers and is not the gate.
7. Rule details (rpg-designer verbatim, 2026-11-01, via lead resend):
   - (1) Suppression is the same as F3 class (a): time, needs and wake still run.
   - (3) Formation needs an accepted contract, so lodger-led formations fall to about 0. If every member is lodged, the current leader stays.
   - (4) Reason: without it, followers walk to the inn door to "regroup" with a sleeper. That rebuilds the door jam F3 removed, and it is a REGROUP walk of the kind seen in the hazard entries.
   - The mechanism is the distance-10 finding. Lodgers share the building tile, so formation sees them as side by side.
8. The measurement rows carry the lodging state of BOTH the offerer and the target, at contract creation and at acceptance, plus outside-follower ticks whose follow or REGROUP target is a lodged leader's building tile or reach tile.

## Out of Scope
- The churn fix itself (TCK-20261031-A-PAIR-RE-FORMS-AND-LEAVES-A-GROUP-EVERY-TWO-TICKS).
- The lodging leave/re-claim cadence (N14, TCK-20261021-A-CROWDED-SERVICE-DOOR-BLOCKS-A-STARVING-SUBJECT).
- Target selection and group_bias (TCK-20261020-ENGAGE-BRACKETING-MOVES-WALK-A-GROUP-INTO-A-HAZARD-CLUSTER, H1).
- Any change to what a non-lodged entity decides.
- The remaining lodger decision paths (project/goal records, info-need on wake, paid info, reproduction, engagement posture, progression, guild visits, not-determined rows): TCK-20261101-A-LODGER-DECISION-PATH-AUDIT.
- paid_information.py:98's lead/gold transfer with no distance test, for anyone: TCK-20261101-PAID-INFORMATION-TRANSFERS-WITH-NO-DISTANCE-TEST.
- Lodger-to-lodger interaction in the same building. A possible owner question after the audit ticket; closed for now, for determinism and simplicity.

## Acceptance Criteria
- On a re-measure on the same seeds as batch C (frontier s43-s45 and urban s42 at least): contracts CREATED with a lodged party = 0, and OFFERED->ACTIVE with a lodged party = 0. ACTIVE->FULFILLED is excluded, because term expiry is exception (c) (rpg-designer 2026-11-01).
- Lodged-leader / lodged-holder formations are about 0. Any remaining case is named, with the reason no non-lodged member was eligible.
- A unit test pins that membership persists through lodging.
- Outside follow targets on a lodged leader = 0 (re-measure count, with the objective and reason recorded), with a unit test of the absent-leader rule. rpg-designer ruled rule (4) a GUARD with a test (urban s42: target_id on the leader 0, REGROUP/FOLLOW 0).
- A unit test per suppressed path pins that a lodged stayer makes no new offer/accept/counter/help request/defection, and is never chosen as partner or offeree.
- The architecture test passes for this ticket's phases, and fails if a listed phase drops the predicate.
- A run with no lodgers is hash-identical to the base.
- Deaths are paired under the death-STOP bar (Tier 1 / Tier 2 as in the batch C rules). rpg-designer reads any Tier 2 set.
- Mechanics ch.04 (strategic cognition), the parity ledger and intentional_divergences are updated in the same change if behaviour diverges from the Bible.
- Hot-loop: probably no (a lodged-state lookup on the cooperation/groups decision loops). The investigation confirms it. Under the perf pause (#715 6556861718), timing is NOT MEASURED and is covered by checkpoint (a).

## Disclosure
- Batch C's disclosure names this as a known F3 seam (2.155) with this ticket id. F3 (TCK-20261031-A-SLEEPER-HOLDS-A-DOOR-OR-SERVICE-TILE) is already closed and merged (#823, 30307228c), so the seam is recorded here and in batch C, not in F3's close.

## Related Tickets
- TCK-20261031-A-SLEEPER-HOLDS-A-DOOR-OR-SERVICE-TILE (F3; the two suppressed entries)
- TCK-20261031-A-PAIR-RE-FORMS-AND-LEAVES-A-GROUP-EVERY-TWO-TICKS (groups churn; batch C found this; it goes in batch C's disclosure)
- TCK-20261101-A-LODGER-DECISION-PATH-AUDIT (ticket 2; extends the predicate)
- TCK-20261101-PAID-INFORMATION-TRANSFERS-WITH-NO-DISTANCE-TEST (split out)
- TCK-20261101-DISSOLVED-GROUP-RECORDS-ARE-KEPT-AND-VISITED-EVERY-TICK (groups rider)
- TCK-20261021-A-CROWDED-SERVICE-DOOR-BLOCKS-A-STARVING-SUBJECT (N14; lodging cadence)

## Related Docs
- docs/mechanics/04_strategic_cognition.md
- docs/parity_ledger/social_narrative.yaml, docs/parity_ledger/strategic_cognition.yaml

## Related Stored Artifacts
- Path list: lodger_decision_paths_2026-11-01.md at origin rpg-ubuntu-planner-idle, c721b3316198b4158316194f61fc0deb2acd2141 (59 rows).
- Evidence: ubuntu groups batch C, frontier s44 probe rows (probe hash ebc58e3b8c34; groups 10078/10080/10082, building 20003). Also rpg-designer's own read at src/domains/cooperation/services.py:280. Defect id 2.155 (F3 seam). The pointer is on the churn ticket's evidence folder (origin rpg-ubuntu-group-id-alloc-impl, agent-working/staging_artifacts/TCK-20261031-A-PAIR-RE-FORMS-AND-LEAVES-A-GROUP-EVERY-TWO-TICKS/evidence/).

## Related Code Areas
- src/domains/cooperation/services.py (REQUEST_HELP / HIRE_SUPPORT -> recruitment contract, ~:278-297)
- src/systems/social_systems/contracts.py (ContractService.create_recruitment_contract)
- groups formation, election and holder binding (exact sites from the code read)

## Code read (rpg-planner-ubuntu, 2026-11-01, read-only; seeds investigation.md, re-verify at the implementing head)
- Offer: CooperationPhase loops over active+alive entities (src/domains/cooperation/phase.py:105-106). services.py:280/:284 creates the recruitment contract with no lodged read.
- Accept: phase.py:130/:151 and services.py:48/:80/:95 also have no lodged read.
- Formation: groups.py:282/:325/:338. The leader is the initiator (:300/:391). The distance check passes for co-lodgers.
- Base: reachable by code (phase.py:104-105, groups.py:266/:309). No base probe is needed (rpg-designer).
- Intent: on the rows it is stamps only. The scheduler holds the act, and lodging.py:264 strips moves.
- Open seam, in scope to answer: a follower OUTSIDE with a lodged leader (tactical.py:568 reads the leader's state/position). Does the follower follow a lodged leader to the door, or wait? The investigation answers this before a fix shape.

## Measured on batch C probes (rpg-planner-ubuntu raw read, 2026-11-01; not re-checked)
- Contracts by lodged state (neither / target lodged / both / offerer only):
  - CREATED 419 / 29 / 32 / 0;
  - OFFERED->ACTIVE 230 / 7 / 6 / 0;
  - ACTIVE->FULFILLED 214 / 3 / 9 / 11.
  Offers AND accepts leak. A lodged offerer occurs only with a lodged target (32/32), which fits the distance mechanism.
- Lodged-leader/holder formations: 9 across the probes (0/3/3/3).
- Rule (4), urban s42: 370 ticks of outside members near a lodged leader's building (co-presence: building tile 92, reach tile 63, ring 38); follow target 0. This is not a follow count. target_id on the leader 0; REGROUP/FOLLOW reason 0. That is "needed now" by the tile definition. Caveat: the rows cannot tell following apart from walking to the same inn to rest, and there is no objective column. This ticket measures it with the objective and reason, and rpg-designer then confirms behaviour change vs guard.

## Assumptions / Open Questions
- The partner side is covered by exception (d).
- The architecture test placement needs testing-planner's OK.
- The code read below answers Scope 1 for cooperation and groups. Other social/strategic writers still need the full listing in investigation.md.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary

## 2026-11-01 live example for rule (4) (ubuntu groups batch C)
- e3 with a lodged leader e26: a live case of an outside member whose leader is lodged. Use it as a replay case for the absent-leader guard test. Rows are via ubuntu's batch C evidence.
