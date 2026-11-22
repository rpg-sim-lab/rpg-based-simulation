---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261121-MEAT-EATERS-IN-FRONTIER-LIVING-WORLD-ATTACK-PEOPLE-FORTY-TIMES-MORE-AFTER-THE-NIGHT-AND-SLOT-FIXES
phase: open
date: 2026-11-21
tags: []
---

# TCK-20261121-MEAT-EATERS-IN-FRONTIER-LIVING-WORLD-ATTACK-PEOPLE-FORTY-TIMES-MORE-AFTER-THE-NIGHT-AND-SLOT-FIXES

## Title
Meat-eaters in frontier_living_world attack people about forty times more often (gate O3 0.6 -> 24.0 per seed) since the night fix (#953) and the suspended-project expiry (#954): trace who attacks, and decide intended vs a loop

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
Owner ruling (via lead-planner-u24, 2026-11-21): attribute the big gate moves before testing re-records the baseline. Gate O3.attacks_on_people, FLW, meat group, per seed s42..s46: baseline v2 (run 43895014837, e72270894) 0,0,0,3,0 -> candidate (run 44906014216, 87792e3e8) 51,5,0,59,5 (floor 3).
The ubuntu lead's split, from saved gate-report JSONs with no reruns (#715 7063400557): #953 (divergence 2.209, night) alone gives +17.6; #954 (2.212, suspended-project expiry) alone gives +19.6; with #958, main a9dc29cdf reaches +36.4; #955 PERC-02a brings it to +23.4; #952 = 0; #983 = 0. SE about 12.3.
rpg-designer ruled it a BUG CANDIDATE until a trace clears it. The rule was pre-set before any data. Neither 2.209 nor 2.212 predicted an attack change, and the two-seed concentration looks like a repeating loop.
This ticket is the TRACE ticket: it owns any gate drift entries or carried rows for the #953/#954-tied rows while the trace runs (rpg-designer: every row tied to #953/#954, alone or combined, and every unplaced row, is held).

## Scope
1. A traced kernel run (own S9; brief at main-checkout .claude/handover/drafts/rpg-planner-o3-trace-brief.md, sha256 cd27e75a, accepted by rpg-designer as the pre-set rule of record): FLW s42 + s45, plus s43 as the REQUIRED quiet control, 5000t, NEW = 87792e3e8 vs BASE = e72270894, each on a fresh git archive tree, with plain twin hash equality.
2. Report (a) O3's unit (hits vs engagements; an engagement = one attacker on one victim with gaps <= 50t), (b) per attacker: kind/species/diet/engagements/hits/victims/day-night, (c) per pair: engagements and outcome, (d) inside the SURV-08 active period or not, (e) per hit: the victim's state (asleep / lodged / awake), its movement mode, and whether its next tactical decision is flight or fight. Also the gate's meat-group membership rule (file:line; inspected 2026-11-21: by diet, so group 'none' cannot be in it). O3 counts HITS (run_ledger._count_attacks), so the trace derives engagements itself.
3. Apply rpg-designer's pre-set rules R1-R7 (in the brief; R6 fight length vs BASE, R7 victim state). R1-R5 and R7 are judged on NEW, with BASE as context. A miss on NEW and BASE is "pre-existing" (still a bug candidate, not attributed to #953/#954); a miss on NEW only is attributed. R6 is NEW vs BASE. NEW's night definition is applied offline to both arms (a measurement label; BASE's agents never used it). Active periods come from a kit-side copy of SURV-08 Q5(a), pinned in the kit. "Not assessable" is NOT a pass: a seed where R5 can't be assessed for attackers carrying >= 10% of engagements reads NOT CLEARED and counts as held. An R5 miss is also tagged "SURV-08 law MISSING in code" (see TCK-20261109-M1-ACTIVITY-PERIOD-AND-HAZARD-TOLERANCE). INTENDED only if all rules hold in every seed where they apply; otherwise a BUG CANDIDATE with the attacker ids, then a fix ticket. A meat group holding a non-meat diet is a metric-grouping finding for testing-planner.
4. If intended: consequence lines in 2.209 and 2.212 plus parity notes (rpg-designer's docs), and the held rows re-record report-only.

## Out of Scope
- Changing the gate, its floors or any baseline row (testing-planner owns the re-record mechanics).
- The TOWN_SERVICE drops as a ruling question (held with the #954 rows; rpg-designer rules them separately if needed).

## Acceptance Criteria
1. The traced run's raw JSONs exist with hashes, the twins match, and rpg-designer recounted them.
2. Each seed (s42, s43, s45) has R1-R7 verdicts recorded, labelled executed, with the pre-existing / attributed / not-assessable labels per the rules in Scope 3, and s43 shows the rules don't fire on a normal seed.
3. The outcome is either a fix ticket filed (bug) or the 2.209/2.212 consequence lines landed (intended), and the held gate rows are released accordingly.

## Related Tickets
- TCK-20261115-THE-NIGHT-CHECK-READS-RAW-WORLD-TIME-SO-EVERY-TICK-AFTER-1800-IS-NIGHT (#953)
- TCK-20261020-SUSPENDED-PROJECTS-ARE-NEVER-RESUMED-SLOT-LEAK (#954)
- TCK-20261117-EACH-BODY-PERCEIVES-BY-ITS-SPECIES-SENSES-AND-SIGNALS-FOLLOW-THE-BODY (#955)
- TCK-20261117-A-SUBJECT-RE-CHOOSES-THE-TARGET-IT-JUST-GAVE-UP-ON (F2; the loop family under R4)

## Related Docs
- docs/guidelines/intentional_divergences.md 2.209, 2.212, 2.210
- docs/world_rules/life-body/survival-needs.md SURV-08
- tools/test_architecture/rpg_gate_known.yaml (drift entries need a TRACE ticket)

## Related Stored Artifacts
None yet. Gate runs 43895014837, 44323101062, 44452967207, 44906014216; #715 7063400557.

## Related Code Areas
- src/observability/rpg_gate_metrics.py (O3 counting, meat grouping)
- src/core/calendar.py, src/systems/strategic_systems/intelligence.py (suspension expiry), src/engine/tactical.py (attack decisions)

## Assumptions / Open Questions
- Whether O3 counts hits or engagements (to be read in the kit).
- Whether the undead (FLW ids 39-44, group 'none') are inside the meat group.

## Durable state, lifecycle and clocks
None expected until the cause is known.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
