---
status: active
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20261029-AN-ESCALATED-NEED-THAT-WINS-SCORING-LOSES-THE-PROJECT-SWITCH
artifact_type: plan
tags: []
---

# Plan: an escalated need that wins scoring takes the project switch (K3 fix)

STATUS: PLAN ONLY. No src code until the designer and rpg-planner review it. Standard tier. Branch rpg-k3-escalated-need-switch (worktree /mnt/data2/rpg-wt/k3switch), fast-forwarded onto e39fe7873, the K2 head as pushed to #1015. Baseline: K3 = 30 (urban s42 2,400 ticks) counted on 282b25981; e39fe7873 is hash-equal to it on the three gate worlds (S9 #715 7167758986), so the baseline still holds. A PR is based on main if #1015 has not merged (the lead's rule), rebased then. Law: SURV-07 / Bible ch04 "Standing Needs Escalate". Owner order #715 7159601467 "fix K2 then K3". Designer's option (b) a3833b7d: "an escalated winner with no present threat takes the switch", the smallest SURV-07 rule.

## 1. The rule (one place, no new scoring)
In `evaluate_project_switch`, before the lock block: when the candidate is an ESCALATED NEED project (the tree's own `escalated_need_wins(entity, candidate kind)`, i.e. its pressing test) and there is NO present threat (`present_threat_to(entity, state)`), the lock and the retention margin are bypassed and the switch is taken through the existing update: the current project is SUSPENDED (`suspend_record`) and the candidate becomes current in the same update, as an ordinary win does. Nothing else changes: no new scoring, no new threshold (the escalation onset is the tree's own; no setting is added), and the capacity gate, route_live_record, orphan handling and supersede_on_win are untouched. `detour` keeps its own bypass.

## 2. What the rule does and does not reach, from the measured rows (investigation.md)
Of the 30 losses on the K2 head: groups A (12, town_return current) and B (6, resolve_blocker current) are exactly "an ordinary kind held an escalated need": the rule takes the switch there (18 of 30). Group C (2, fatigue winner against a current HUNGER project) is need against need: the rule as written would let a pressing fatigue displace a pressing hunger project; this plan EXCLUDES it (the rule applies only when the current project is not itself a need project of an escalated need), so C stays as scoring already decided it; ruling needed (Q1). Group D (10 hunger losses with `current_project_id == ""`) is NOT a switch loss: the winner's OWN hunger project was current at d and was cleared in the same apply; no switch rule changes it. D needs its own read of which writer cleared those hunger projects (Phase 0, below); it is reported, not fixed here.

## 3. Phase 0 (before code, read-only, small): who clears the 10 group-D hunger projects
A trace of the 10 rows (urban s42, ticks 1410-1417, 1472-1476, 1932-1936) recording, for the subject's current hunger project at d+1, its status and typed `ended_by` and the writer's phase; a pass-through on apply (the same hash-neutral pattern as the own-job spy) on a fresh archive of e39fe7873. If they are an end the law intends (a finished meal, an arrival), they leave the K3 count (the baseline becomes 20); if not, they become their own ticket. The rule's own-job bars do not depend on it.

## 4. Own-job counts (HARD; proposed for the designer to fix before data)
Per cell, fix arm vs the K2 head:
(i) FIRES: times the rule changed the outcome (the ordinary comparison would have refused, the need's project became current), by need and by the current's kind.
(ii) K3 LOSSES after the fix, kit v6 K3 join: groups A+B must be 0 (the target); C and D reported separately, not a bar.
(iii) FIRES UNDER A PRESENT THREAT = 0 (by construction, the exclusion; measured).
(iv) NEUTRALITY: in a cell where (i) = 0, the final hash EQUALS the K2 head's (e39fe7873 = the references above), else STOP (the rule leaks).
(v) report-only: the need project's time current afterwards and what the SUSPENDED project does (resumed, expired by the 200-tick suspension TTL, N10); subjects reaching sleep_debt >= 98 and hunger >= 95, fix vs K2 head (the collapse lines), as K2's A(ii) did.
How (i) and (iii) are read: kit v6's K3 join records decisions and d+1 outcomes but stores only counts of wins. A fire is a decision whose winner is an escalated need and whose prior current was another LIVE kind and whose d+1 current is the need's project: a small decision-row dump in the same spy (a v7 of the K kit, or own-job style) is needed to count it by row; this is the one new measurement piece and needs the designer's approval; no src counter is added (Q3).

## 5. Measurement (for the S9; proposed)
Decisive: kit v6 STAGE=neg on a FRESH archive of the fix head (urban_political s42 2,400 ticks): K3 groups A+B = 0 (before 18 of 30). Own-job cells: the 3 gate worlds x s42 x 5,000 ticks and urban s42 2,400 ticks, main-side = e39fe7873 and fix side = the K3 head, plain twin then spy per arm, one process at a time behind rpg_host_gate; trees are NEW fresh archives, each file-list checked against `git ls-tree -r`. Reuse an approved kit wherever it fits; the new piece is only the fire-row dump (Q3).

## 6. Tests (written with the code; run in a host gap)
Real kernel (the lodging/strategic harness): (a) an escalated hunger winner with an ordinary kind current (town_return, resolve_blocker) and no threat TAKES the switch: the need project is current and the old one is SUSPENDED in the same update; (b) the same with a present threat (an acting hostile): no switch; (c) a NON-escalated winner (hunger below the onset) does NOT bypass: the ordinary lock and retention still hold; (d) the need against a current need project (fatigue vs hunger) keeps the ordinary comparison (the exclusion); (e) `detour` unchanged; (f) a locked current with utility <= 80 (the 0.8 floor) is released for an escalated need and not for an ordinary one; (g) the suspended project resumes later through the existing path (same_kind_record). Mutants for the review: the pressing test off, the threat test off (b must fail), the need-vs-need exclusion off (d must fail). Typed: no new field (the rule writes only the existing suspend and current writes), so no canonical-dict or checkpoint change. Docs in the same change: Bible ch04 section 2 (Generalized Bypass: the escalated-need exemption written in) and "Standing Needs Escalate", the parity ledger row (new, STRAT-359 or the next free), divergence 2.228 (Bug Fix: the code then does what SURV-07 says; the next free after 2.227), mechanisms.yaml `goal_hierarchy` (planner's).

## 7. Open questions for the designer and rpg-planner (I do not pick)
Q1. Need against need (group C): exclude (as planned: the ordinary comparison between two pressing needs stays) or let the higher escalation win? The rows show 2 cases only.
Q2. Threat exclusion: `present_threat_to` (AGENCY-07 terms, the K kit's main count; the plan's choice) or `acting_threat_to` (the narrower SURV-07 NEED_YIELDS test, also what the scorers already use to drop the pull)? On these rows both give 30.
Q3. The fire-row dump (4 (i), (iii)): a K kit v7 with the decision rows, or accept the inferred count from kit v6 (wins whose d current was another live kind)?
Q4. Phase 0 (group D): run it first and re-baseline K3 to 20 if the ends are lawful, or keep the baseline 30 and report D separately?
Q5. The rule bypasses the lock and the retention margin for an escalated need; should it also bypass the `_threat_resolved` condition for a LOCKED current (it does now: the bypass is before the lock block)?
## 8. Order of work after approval
(1) Phase 0 trace; (2) the rule and its unit tests; (3) real-kernel tests; (4) docs, parity, divergence; (5) targeted pytest and mypy in the lock env, the code-health trio (this gate needs 0 new: write the rule as a small function, not inline in the already long switch); (6) fresh trees and the S9 measurement. No push.
