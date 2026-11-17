---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20261118-QUALITY-SCORES-REWARD-SILENCE-OVER-LATE-ACTIVITY
phase: open
date: 2026-11-18
tags: []
---

# TCK-20261118-QUALITY-SCORES-REWARD-SILENCE-OVER-LATE-ACTIVITY

## Title
Quality pillar scores rate a world that goes silent, or never acts, above one that keeps acting or acts late

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P3

## Request Summary
This is backlog. rpg-designer-ubuntu ruled it a scorer finding on 2026-11-18, during the births corpus trace (TCK-20261109-M1-BASIC-WILD-BIRTHS-FOR-EVERY-LIVING-KIND). It is not part of M1, and births does not change it.

The finding has one root: a pillar is penalised for absence only when a late event finally arrives, and its rate is measured over its own active span. So silence beats late or continued activity. The trace showed it three ways (s42, 1000 ticks, main 3aafdb383 vs the births head):

1. **Denominator.** `quality_report.py:122-124` divides the raw score by `max(current_tick // 4, last_event_tick)`, as documented in docs/simulation_quality/quality_scoring_contract.md §4.4.
   - In urban_political, SOCIAL raw was 20109 on main and 20185 on head (+0.4%).
   - The normalised score fell 36.50 -> 20.19 only because main's last SOCIAL event was at tick 551, while head's ran to tick 1000.
   - A longer active span reads as a lower grade.
2. **Late-first-event dormancy penalties.** `faction.py:57-71` fires `diplomacy_dormant` (-20) on the first `diplomatic_transition` after the `zero_diplomacy_by_tick` gate, when FACTION has no earlier events.
   - A world that never transitions is never penalised (0).
   - A world with one late transition scores -20.
   - Seen in both corpus worlds on head (tick 395 urban_political, tick 860 hero_guild_routing).
   - rpg-designer-ubuntu named the same shape in `calamity_dormant` and `world_static`, and `demographics_dormant` needs a payload flag on a birth event.
3. **Per-tick counting of a persisting state.** `decision_divergence_detected` (event_shapers.py:914-939) is emitted on every tick an entity holds a non-survival project while its top concern is DANGER above 0.7, and COGNITION scores +5 each time.
   - On main hero_guild_routing, one entity (25) made 700 of the 820 events, one per tick from 276 to 975.
   - One stuck entity reads as rich cognition.

## Scope
- (1) Denominator: decide, then implement, a normalisation that doesn't reward a pillar for going silent early. This changes quality_scoring_contract.md §4.4, so the rule comes first: rpg-designer-ubuntu on cause and semantics, and the owner of that contract for the change.
- (2) Dormancy penalties: audit every one-shot rule in src/simulation_quality/scorers/ and classify each one: does it fire on true absence, or only when a late first event arrives?
  - The `_fired` flags on main dca5a8dbb are in agency, cognition (2), combat (2), economy (3), faction (2), information (3), narrative (3), progression (3), social (2) and world_dynamics (5).
  - The rules gated on `pillar_event_counts == 0`, or on a zero window tag, are the first to check: combat.py:59, faction.py:63, information.py:96, social.py:68, and the window-tag gates at agency.py:109, cognition.py:59-60, economy.py:75/89/103, information.py:65, narrative.py:71/93, progression.py:74 and world_dynamics.py:76/103.
  - Fix the ones that fire only on a late event, so that absence is scored at end of run or at the gate tick.
- (3) Per-tick state counting: score `decision_divergence_detected` on entering the state (or once per window), not on every tick it persists. That way one stuck entity can't dominate COGNITION.
  - Second instance, `cooperation_event`, added per rpg-designer-ubuntu's loop read (fc2a5c96). `src/domains/cooperation/phase.py:150-209` re-decides every tick for an entity with a help need and writes `last_cooperation_decision`, and each write emits a `cooperation_event`. On the births head, urban_political s42 1000t has original entities 10 and 28 deciding SOLO on every tick from about 916-919 to tick 1000. That sets SOCIAL's last_event_tick to 1000. The same per-tick shape is normal on main (entity 18: 460 events over ticks 4-495).
  - Check first: does the help need behind a standing SOLO ever resolve? If it never does, split it out as a cooperation behaviour ticket. "Without acting" is unverified, because the payload carries no action field.
- Re-pin the corpus grades the fix moves, under rule (a) (#715 6941107808).

## Out of Scope
- Any M1 or births item.
- Why urban_political main goes SOCIAL-silent after tick 551. That is main's own behaviour, noted but not traced.
- Changing a rule before its ruling.

## Acceptance Criteria
- A pillar's normalised score no longer falls when the same raw activity continues over a longer span. A test pins this.
- Each one-shot dormancy rule fires on true absence, or is documented as intentionally event-triggered. One test per changed rule.
- A persisting decision-divergence state scores once per entry or window. A test pins this.
- quality_scoring_contract.md and docs/guides/simulation_quality.md match the code.

## Related Tickets
- TCK-20261109-M1-BASIC-WILD-BIRTHS-FOR-EVERY-LIVING-KIND
- TCK-20261014-PILLARS-REPORT-NO-DATA-BELOW-A-MINIMUM-EVENT-COUNT
- TCK-20260630-SIMQ-TIMEGATE

## Related Docs
- docs/simulation_quality/quality_scoring_contract.md (§4.4)
- docs/guides/simulation_quality.md (Grade scale)

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20261109-M1-BASIC-WILD-BIRTHS-FOR-EVERY-LIVING-KIND/rpg_designer_ubuntu_births_grade_trace_ruling_2026-11-18.md (Q2, Q3, COGNITION cause)

## Related Code Areas
src/simulation_quality/quality_report.py, src/simulation_quality/pillar_accumulator.py, src/simulation_quality/scorers/, src/observability/event_shapers.py

## Assumptions / Open Questions
- Option offered to lead-planner-u24 (its call): show the raw score and the denominator next to each normalised corpus row value.

## Implementation Notes
None yet.

## Test Summary

## Files Changed

## Completion Summary
