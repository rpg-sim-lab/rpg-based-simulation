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

rpg-designer ruling (2026-11-01): this is a ROW, not a STOP on batch C.
- A lodged stayer makes no NEW social decision: no offer, accept, counter or help request.
- Membership persists through lodging.
- Election skips lodged members while a non-lodged member is eligible.

## Scope
1. Code read first, written into investigation.md: list every decision path a lodged stayer can still reach (cooperation offer/accept/counter/help request, contract acceptance, group formation leader choice, holder binding, election, and any other social or strategic writer), with file:line. Mark which ones F3's suppression already covers.
2. Suppress NEW social decisions by a lodged stayer on each uncovered path: offers, acceptances, counters and help requests, as the source or as the partner.
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

## Acceptance Criteria
- On a re-measure on the same seeds as batch C (frontier s43-s45 and urban s42 at least), lodged contract creations = 0 and lodged contract acceptances = 0.
- Lodged-leader / lodged-holder formations are about 0. Any remaining case is named, with the reason no non-lodged member was eligible.
- A unit test pins that membership persists through lodging.
- Outside follow targets on a lodged leader = 0 (re-measure count), with a unit test of the absent-leader rule.
- A unit test per suppressed path pins that a lodged stayer makes no new offer/accept/counter/help request.
- A run with no lodgers is hash-identical to the base.
- Deaths are paired under the death-STOP bar (Tier 1 / Tier 2 as in the batch C rules). rpg-designer reads any Tier 2 set.
- Mechanics ch.04 (strategic cognition), the parity ledger and intentional_divergences are updated in the same change if behaviour diverges from the Bible.
- Hot-loop: probably no (a lodged-state check on the cooperation decision path, per decision, not per tick per pair). The investigation confirms it. Under the perf pause (#715 6556861718), timing is NOT MEASURED and is covered by checkpoint (a).

## Disclosure
- Batch C's disclosure names this as a known F3 seam (2.155) with this ticket id. F3 (TCK-20261031-A-SLEEPER-HOLDS-A-DOOR-OR-SERVICE-TILE) is already closed and merged (#823, 30307228c), so the seam is recorded here and in batch C, not in F3's close.

## Related Tickets
- TCK-20261031-A-SLEEPER-HOLDS-A-DOOR-OR-SERVICE-TILE (F3; the two suppressed entries)
- TCK-20261031-A-PAIR-RE-FORMS-AND-LEAVES-A-GROUP-EVERY-TWO-TICKS (groups churn; batch C found this; it goes in batch C's disclosure)
- TCK-20261101-DISSOLVED-GROUP-RECORDS-ARE-KEPT-AND-VISITED-EVERY-TICK (groups rider)
- TCK-20261021-A-CROWDED-SERVICE-DOOR-BLOCKS-A-STARVING-SUBJECT (N14; lodging cadence)

## Related Docs
- docs/mechanics/04_strategic_cognition.md
- docs/parity_ledger/social_narrative.yaml, docs/parity_ledger/strategic_cognition.yaml

## Related Stored Artifacts
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

## Assumptions / Open Questions
- Whether the partner side (being offered while lodged) needs the same check as the source. Assumed yes by the ruling ("no offer, accept, counter").
- The code read below answers Scope 1 for cooperation and groups. Other social/strategic writers still need the full listing in investigation.md.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
