---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20261020-A-PURSUING-HOSTILE-WAKES-ITS-TARGET
phase: open
date: 2026-10-20
tags: []
---

# TCK-20261020-A-PURSUING-HOSTILE-WAKES-ITS-TARGET

## Title
A perceived hostile pursuing the subject (INTERCEPT/PURSUE on it) wakes its brain, extending D32's adjacency wake

## Status
BLOCKED

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
OWNER-CONFIRM ITEM: this extends owner decision D32. The designer ruled on 2026-10-20 that it comes after v1, as its own measured step, and will put it to the owner.

Lane A's real-kernel probe on rpg-v3-starvation-threat 70402779d (/mnt/data/scratch-rpg-implementer/v3_close2.py) set this up:
- frontier 42, merchant 37 starving (hp 40/85, hunger 100) with an inn in reach;
- a hostile scout closing from 7 tiles, INTERCEPT from t7 at 1 tile a tick, contact at t12, ATTACK from t15.

The merchant never reacted before contact. The brain runs only at the strategic cadence (10 ticks, staggered by id, cadence.py), and the adjacency wake (scheduler.py:53-55, D32) fires only for a hostile beside the subject. A hunter crosses 6 tiles inside one cadence window. A tactical pass called on those ticks would have pre-empted from distance 6 (PURSUE, then engage). This is disclosed in v1 as row C5 (designer f8913b038).

## Scope
- In the scheduler wake rule: a perceived hostile whose current task is INTERCEPT or PURSUE targeting the subject wakes the subject's brain on that tick.
- Before-numbers, measured before the change:
  - this probe's trace (the hunter crosses 6 tiles unseen);
  - from the paired run, a count of contact attacks where the attacker had been pursuing for 2 or more ticks before contact.
- Measure it as its own step: paired 3 × 42-46, crowded first, with a STOP to the owner. Report the wake rate and its tick cost.
- Finding to record here, not to fix here: during the closing window the merchant's task was a held, empty ENTITY_ACT (action None, payload {}). Find out whether an empty act being held as a task is a defect, and file it if so.

## Out of Scope
- The cadence length. The hunger and threat logic (V3 step (ii)).

## Acceptance Criteria
- The owner confirms the D32 extension before it lands.
- In the probe scenario, the subject reacts before contact. This is pinned by a real-kernel test.
- The paired measurement passes the stop line, or the result goes to the owner.
- The empty-ENTITY_ACT finding is recorded, with a verdict.

## Related Tickets
- the V3 step (ii) ticket on rpg-v3-starvation-threat
- TCK-20261020-HUNGER-AND-RETREAT-ON-ONE-ESCALATION-SCALE

## Related Docs
- docs/plans/systemic_world/owner_decision_memo.md (D32)
- docs/plans/systemic_world/v1_disclosure.md (C5)
- docs/engine/kernel.md (scheduling)

## Related Stored Artifacts
- /mnt/data/scratch-rpg-implementer/v3_close2.py (probe)

## Related Code Areas
- src/engine scheduler.py:53-55 (adjacency wake)
- cadence.py (strategic_intelligence 10)
- tactical.py

## Assumptions / Open Questions
- Is the wake costed per perceived hostile? Bound it the same way the adjacency wake is bounded.

## Implementation Notes
2026-11-03 RULING on order and owner visibility (rpg-designer):
- Whether: a defect to fix, no owner question. A hit not waking its victim contradicts decision 32's intent and row 88's act test.
- When and how measured: owner-visible. The counts below show it moves many deaths, so under one variable per step it is its own measured step, and its place in the order is the owner's (rows 93 and 95).
- Lean: ENG lands first, as already measured, then this fix as the next step, measured on top. ENG's owner row carries one line: "next in the order, unless you'd rather", naming it as the cheaper half of urban's +6.
- Hot-loop: yes. Waking on every hit means more brain decisions under the perf pause (#715 6556861718). Its measurement includes a timing reading if the pause allows; otherwise state "not measured".

2026-11-03 COUNTS on base 65d43dfa9 (lane A's gap probe, pinned, 3 runs, hashes equal to paired; not on ENG's head, which the mechanism doesn't depend on). Hit = a new last_hit_tick with an attacker on a person; next decision = first evaluate_entity_intent at a later tick:
- urban s44: 72 hits; next decision within 2 ticks 3; gap >2 47 (median 7, max 59); died before deciding 22; hp lost in gaps >2 824 (vs 43).
- frontier s42: 192 hits; <=2 18; >2 121 (median 8, max 141); died first 53; hp lost 1878 (vs 173).
- crowded s42: 413 hits; <=2 54; >2 282 (median 8, max 114); died first 77; hp lost 5174 (vs 578).
- Wake ending gaps >2: mostly the cadence slot (35/104/237), adjacency wake alone 3/11/23. Short gaps are made by the adjacency wake.
- So on base, most hits on persons (69 of 72, 174 of 192, 359 of 413) aren't followed by a decision within 2 ticks: the engine's cadence, not ENG. Hp-lost sums over-count where gaps overlap; per-row values are exact.
By kind (gap >2 or died first; urban/frontier/crowded): scout 34/63/62, raider -/29/110, worker 9/12/77, merchant 19/24/24, guard -/27/41, hero 6/-/21, leader -/15/17, blacksmith 1/4/7.
2026-11-03 WIDENED (rpg-designer): the question is now "an act on the subject, row 88's (a) or (b), wakes its brain for a decision on the next tick". A hit is the strongest case. Same idea in one state as divergence 2.154 (the threat wake for a chosen sleeper); say whether one mechanism covers both.
Evidence (lane A's urban s44 re-run on ENG head e844e2845, pinned, hash equal to paired; rows read by lane A, not by rpg-planner): after scout 17's first hit, each victim had NO tactical decision (no evaluate_entity_intent call, task empty) for: victim 2 t3326-3328 (3 ticks), 25 t3501-3505 (5), 1 t3502-3509 (8), 12 t3542-3548 (7), while 17 kept hitting (1 lost 17 hp at t3512, 25 lost 14 at t3511). The act test read True at the next decision, so it isn't the act test. Check whether the gap equals NEED_WAKE_CADENCE (10) by design; e1's 10 ticks suggests re-deciding only on cadence. Code read (lane A, ENG worktree e844, not checked by rpg-planner): an empty task makes the work kind ENTITY_BRAIN (scheduler.py:136-141); unless woken, `_throttled` (scheduler.py:105-114) runs it only on `(tick + id) % cadence == 0` (cadence.py:39-60, default 10, the same value as NEED_WAKE_CADENCE, need_wake.py:8). Two wakes exist: decision 32's adjacency wake (scheduler.py:97-106; an orthogonally adjacent, unengaged perceived hostile, every 2 ticks, only without an action payload) and the need wake (scheduler.py:68-95; only a held move/sleep/INTERACT/WORK under a pressing need, not an empty task). Nothing in the scheduler reads last_hit_tick or last_attacker_id, so there is no wake on being hit. The inversion (rpg-designer): a hostile that names the subject as its target counts as engaged, so decision 32's adjacency wake skips it, which means the hostile acting on you is exactly the one that doesn't wake you. Lean shape, rpg-designer's to rule after the counts: a hit (row 88 (b)) wakes the victim's brain for the next tick, whatever its engagement state. That is consistent with decision 32's intent and the act test, so no owner question unless the counts show a cost. This ticket also settles whether a pursuit (a) wakes too, and how it relates to 2.154 for sleepers. The s44 gaps fit that [I]. Counts wanted before ENG closes, if cheap: hits not followed by a decision within 2 ticks, per run. ENG's owner row names this as the cheaper half of urban's +6: it doesn't change the gate.
After v1. Needs the owner's confirmation.

2026-11-11 PARKED by the owner (#715 6776436829, "Park it (Recommended)"; follows 6767852925 hold-and-narrow). rpg-planner recorded it.
- Built as hit-wake: a hit on t wakes the victim's brain on t+1 (`src/engine/scheduler.py::_is_hit_woken`). The narrowed rule N2 also skips an entity whose task is an ATTACK (rpg-designer's design, main-checkout .claude/handover/drafts/rpg-designer-hitwake-narrowing-design.md).
- Branches, kept LOCAL. Not pushed, not deleted; deleting needs the owner.
  - Lane C's rpg-hit-wake: b46c429e7 is N2 on f25b04d8a; 2162e1f19 is N2 merged with main 993400a52.
  - Both carry divergence 2.159, STRAT-298, the kernel.md wake rule (4) hunk, and this ticket plus TCK-20261107-GROUP-FORMATION-TICK-IS-NEVER-WRITTEN closed in done/.
- Arm 2 (unnarrowed, f25b04d8a vs cefa99b07):
  - 4 Tier 1 trips; Tier 2 FED 10.
  - Owner row: drafts/rpg-designer-hitwake-arm2-owner-row.md.
  - Traces: /mnt/data2/scratch-c3/tier2/.
- N2 (2162e1f19 vs main 993400a52, crowded + urban s42-46 × 5000, pinned):
  - Cells: /mnt/data2/rpg-measure/results/{993400a52995,2162e1f19fd9}-72320cac-5000/. All 10 fix hashes equal b46c429e70cf.
  - Urban deaths 49→60: COMBAT 34→43 and DEFEAT 4→8, both over the bar.
  - Crowded deaths 160→165 (COMBAT 118→128, under the bar).
  - Tier 2: urban s44/s46, scripts ea239a3dec45 / 494d16b706e0, all 4 traces MATCH. Results in /mnt/data2/scratch-c3/tier2_n2main/.
  - Designer's classes: FED 6, NEAR 5, DRIFT 2. Owner row: drafts/rpg-designer-hitwake-n2-owner-row.md.
- Finding: the ATTACK payload clears on the tick the attack lands, so N2 still wakes an attacker on that tick (scout 15, urban s46).
- Revisit after TCK-20261110-A-NON-FLIGHT-MOVE-OFF-ENGAGEMENT-WALKS-INTO-A-KNOWN-LETHAL-FREE-SWING: 4 of the 6 FED die walking off a fight into the free swing. That ticket takes scout 15 s46, scout 17 and worker 4 as evidence.
- A revisit re-measures on the then-current main. The branch results are not reused.

## Test Summary

## Files Changed

## Completion Summary
