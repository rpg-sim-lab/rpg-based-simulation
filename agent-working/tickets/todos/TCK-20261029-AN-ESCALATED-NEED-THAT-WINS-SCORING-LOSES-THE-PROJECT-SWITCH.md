---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20261029-AN-ESCALATED-NEED-THAT-WINS-SCORING-LOSES-THE-PROJECT-SWITCH
phase: open
date: 2026-10-29
tags: []
---

# TCK-20261029-AN-ESCALATED-NEED-THAT-WINS-SCORING-LOSES-THE-PROJECT-SWITCH

## Title
An escalated hunger or fatigue goal that has already won scoring still loses evaluate_project_switch to the lock or retention margin of an ordinary current project

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
Found by rpg-implementer's need probe for :1610 (TCK-20261027-CAPACITY-GATE-FIRST-RECORD-OF-KIND-IS-DEAD-SO-LIVE-SIBLING-NEVER-RESUMED) on c32db1a41, frontier_living_world s42-46, 5000t. Data: /mnt/data/scratch-rpg-implementer/c1610/need/ (analyze_need.py).
- Orphan path: escalated need orphans lost the switch, hunger 103 times (14 episodes) and fatigue 307 times (19 episodes). escalated_need_wins was true on every loss. Hunger was 88-100 and sleep_debt about 73-80 in the examples.
- Fresh-candidate path ("no_create_other": no record, no create, gate passes): escalated hunger 97, fatigue 102. evaluate_project_switch returned None.

rpg-designer ruling (2026-10-29): this gap already exists in base d914bace7 (intelligence.py about l.1606-1780) and was not caused by :1610.
- In base, an ACTIVE orphan is not SUSPENDED, so a fresh candidate goes through the same switch with the same score and loses the same way.
- :1610 changes only what follows a win: the orphan becomes current instead of a duplicate being left behind.
- :1610 lands with ruling (b) unchanged, once a base count confirms base lost those switches too.

Defect: Bible 04 "Standing Needs Escalate" (SURV-07) says a pressing need outranks ordinary goals. Here the escalated goal has already won scoring against the current project's live score (with_live_current_score). It is then held by retention_margin and/or the lock in evaluate_project_switch, which is the ordinary-goal hold that SURV-07 says the need overcomes.
- Present threats are handled upstream: below the starvation line a present threat removes the escalation (escalation.py l.40), and the tactical pass pre-empts.
- So the switch is the only place an escalated need loses to a non-threat.

## Scope
Counts first, then numbers to rpg-designer through rpg-planner before any fix shape. Use pure probes, with the state hash equal with and without the probe. Run on frontier_living_world s42-46, on main after :1610 lands. Report the orphan path and the fresh path separately, and hunger and fatigue separately:
- (a) Held by the lock (dual condition: normalized score + margin, plus the 0.8 floor) vs held by the base retention comparison (candidate.score > current.score + retention_margin). Give the score, current score and margin bands.
- (b) The current project's kind when the need loses.
- (c) Parked time: ticks from the first loss until the earliest of need met, switch won, or the consequence line reached.
- (d) Any death or collapse (STARVATION, exhaustion) inside a parked window.

Lean fix shape, for the counts to confirm (rpg-designer's call):
- In evaluate_project_switch, a candidate with escalated_need_wins true bypasses both the lock and retention_margin. It still SUSPENDs the current project in the same update.
- "detour" stays the only unconditional structural bypass for other kinds.
- This is a Bug Fix divergence: the code then does what SURV-07 already says. Bible 04 section 2 (Generalized Bypass) needs the escalated-need exemption written in.
- Paired run 3 worlds x s42-46. It goes to the owner only if the paired run STOPs.

## Out of Scope
- Scoring-stage outbids, where the need loses before the switch: TCK-20261020-TOWN-RETURN-OUTBIDS-AN-ESCALATED-NEED-UNTIL-ABOUT-95.
- Hunger vs retreat on one scale: TCK-20261020-HUNGER-AND-RETREAT-ON-ONE-ESCALATION-SCALE.
- Orphan records: TCK-20261028-CURRENT-PROJECT-CLEARED-WITHOUT-ENDING-LEAVES-ORPHANED-ACTIVE-RECORDS.
- Mapped kinds: TCK-20261028-MAPPED-GOAL-KINDS-NEVER-MATCH-THEIR-OWN-PROJECT-RECORDS.
- Any fix before rpg-designer rules on the counts.

## Acceptance Criteria
- A counts table (a)-(d) per path and per need, sent to rpg-designer through rpg-planner.
- If a fix is ruled: real-kernel tests show that a locked ordinary current project yields to an escalated need, the current project is SUSPENDED in the same update, and a non-escalated candidate is still held. Also: a Bible 04 section 2 edit, a parity ledger entry, a divergence entry (Bug Fix), and a paired run with no unowned STOP.

## Related Tickets
- TCK-20261027-CAPACITY-GATE-FIRST-RECORD-OF-KIND-IS-DEAD-SO-LIVE-SIBLING-NEVER-RESUMED (:1610, lands first)
- TCK-20261020-TOWN-RETURN-OUTBIDS-AN-ESCALATED-NEED-UNTIL-ABOUT-95
- TCK-20261020-HUNGER-AND-RETREAT-ON-ONE-ESCALATION-SCALE
- TCK-20260810-PROJECT-SWITCH-BYPASS-GENERALIZATION, TCK-20260811-INTERRUPTION-BYPASS-RETENTION-MARGIN-SCALE-BUG
- TCK-20261007-PROJECT-SWITCH-COMPARES-A-LIVE-CANDIDATE-SCORE-TO-THE-CURRENT-PROJECTS-CREATION-TIME-SCORE

## Related Docs
- docs/mechanics/04_strategic_cognition.md: section 2 Interruption Resistance (Generalized Bypass, STRAT-236), Standing Needs Escalate (SURV-07)
- docs/guidelines/intentional_divergences.md 2.40, 2.79, 2.143

## Related Stored Artifacts

## Related Code Areas
- src/systems/strategic_systems/intelligence.py (evaluate_project_switch, the project lookup and switch path)
- src/ai/goals/escalation.py (escalated_need_wins)

## Assumptions / Open Questions
- Sequenced after :1610 lands. Independent of the mapped-kinds and orphan tickets. Not dispatched.

## Implementation Notes
## Test Summary
## Files Changed
## Completion Summary
