---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20261029-AN-ESCALATED-NEED-THAT-WINS-SCORING-LOSES-THE-PROJECT-SWITCH
artifact_type: plan
tags: []
---

# Plan v2: an escalated need that wins scoring takes the project switch (K3)

Supersedes plan.md d6b84a72 where they differ; plan.md is kept unedited (approved sha). PLAN ONLY, no src code. Folds in the rulings rpg-designer-k3-plan-rulings.md (972600b6), relayed by rpg-planner as approved. Base e39fe7873.

## 1. Rulings folded in
- Q1 need vs need is EXCLUDED by the CURRENT project's kind identity (`same_kind`; hunger or fatigue), whether or not that need is escalated. Group C (2 rows) is outside the rule, reported.
- Q2 threat test is `present_threat_to` (SURV-07 tier 1); `acting_threat_to` is a reported side count only.
- Q5 the bypass sits before the lock block (lawful: SURV-07's tier-1 test is the law where it differs from the lock's `_threat_resolved`). Report-only guard: list every fire whose released current is combat_retreat or combat_engage, with whether the subject took damage within 50 ticks; any damage is a FINDING to the designer, not a bar.
- Q3 the switch is split into two PURE helpers: `_escalated_need_takes_switch(entity, candidate, current, state) -> bool` (the new rule) and `_ordinary_switch_allows(entity, candidate, current, tick, state) -> bool` (today's lock-plus-margin decision moved out UNCHANGED). `evaluate_project_switch` calls them. The refactor is behaviour-neutral (existing switch tests unchanged; a hash-equal unit check). A small own-job spy (pass-through, hash-neutral) wraps the rule helper; ONLY when it returns True it calls the ordinary helper read-only on the same arguments: FIRES = rule True AND ordinary False (by need and by current kind); TAKEN = rule True. Kit v6 is unchanged and stays the decisive (ii).
- Q4 PHASE 0 FIRST (below), before any src code.

## 2. Phase 0 (read-only, before code)
Kit /mnt/data2/rpg-measure/k3_phase0_kit_v1 (SUMS f48a82a7), commit 443d804c5: one cell urban_political s42 2,400 t, plain then spy, fresh archive of e39fe7873. It records, for every escalated-need decision whose own-kind project is current, the d and d+1 fields fixed by the designer and classes D1 (lawful COMPLETED, need met; leaves K3, baseline 30-n(D1)), D2 (typed end, listed by reason, ruled per reason), D3 (current cleared while ACTIVE; 3+ consecutive at hunger >= 95 = HARD, back to the designer: a lifecycle fix inside K3 or the orphan ticket pulled into M1). The plain hash is the baseline check: it must equal 2a6e74f0 (282b25981's) for the 30 to carry over, else re-count with kit v6 STAGE=neg first. The K kit classes current_project_id == "" as L1; group D is none-current (L2 in substance), reported, no kit change.

## 3. The rule (unchanged in substance, plan.md section 1)
An escalated need candidate (the tree's pressing test) with NO present threat and whose current project is NOT of a need kind takes the switch: the current is suspended (`suspend_record`) and the candidate becomes current in the same update. No new scoring, no setting, no typed field. `detour` keeps its own bypass.

## 4. Own-job counts (fixed by the designer, per cell, fix vs base head e39fe7873)
(i) FIRES and TAKEN by need and current kind. (ii) DECISIVE: kit v6 STAGE=neg on a fresh fix archive, urban s42 2,400 t: K3 losses in groups A and B = 0 (C, D reported); the A/B/C/D split rule is stated in the read file before the read. (iii) TAKEN under a present threat = 0 (the rule helper records present_threat_to at every TAKEN; any True is a FAIL). (iv) in a cell where TAKEN = 0 the final hash EQUALS the base head's, else STOP. (v) report-only: need project time current after a fire; the suspended project's fate (resumed or expired by the N10 TTL); subjects reaching hunger >= 95 and sleep_debt >= 98, fix vs base, with the K2 never-slept cohort caveat; the Q5 guard list.
Cells: the 3 gate worlds x s42 x 5,000 t plus urban s42 2,400 t; plain twin then spy per arm; new fresh archives checked against ls-tree; one process at a time behind rpg_host_gate and the planner's slot.

## 5. Order of work
(1) Phase 0 smoke (done: no-sim real-tree import check) and run after S9; (2) designer reads Phase 0; (3) the two-helper refactor with the neutrality check; (4) the rule + tests; (5) own-job spy kit, controls, S9; (6) docs (Bible ch04 Generalized Bypass and Standing Needs Escalate, a parity row, divergence 2.228), code-health trio, mypy; (7) measurement. No push.
