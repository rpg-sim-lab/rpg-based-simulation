---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20261029-RUN-LEDGER-CANNOT-SHOW-NEED-HARM-SHORT-OF-DEATH
phase: open
date: 2026-10-29
tags: []
---

# TCK-20261029-RUN-LEDGER-CANNOT-SHOW-NEED-HARM-SHORT-OF-DEATH

## Title
The run ledger counts deaths by cause but has no counter for sleep-debt collapses or time spent at the starvation line, so need harm short of death cannot be measured in a paired run

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Finding from rpg-designer (2026-10-29), raised by the :1610 outcome check (TCK-20261027-CAPACITY-GATE-FIRST-RECORD-OF-KIND-IS-DEAD-SO-LIVE-SIBLING-NEVER-RESUMED).
- Paired runs compare deaths by cause only (COMBAT, DEFEAT, HAZARD, STARVATION).
- SURV-07 changes (escalation, wake, capacity, and the new switch ticket) should be judged on harm before death.
- In the :1610 check, sleep-debt collapses and time at or above hunger 95 could not be measured, because nothing counts them.

## Scope
New RunLedger counters, per world-run, keyed the same way as the existing behaviour counters (kind group and person flag; see tests/unit/observability/test_run_ledger_behaviour.py):
1. sleep_debt_collapses: count of collapse events. These are a SLEEP task begun with COLLAPSE_FLAG at debt >= COLLAPSE_LINE (src/engine/sleep_debt.py; Bible 01 Staged Sleep Debt, Bible 04 l.38).
2. ticks_at_starvation_line: entity-ticks with hunger >= STARVING_LINE (src/engine/starvation.py), plus the number of distinct entities that reached it at least once.
3. ticks_at_escalation_onset: entity-ticks with hunger >= the escalation onset (0.6 of the line, as the escalation code defines it; reuse that constant, no new knob). This is the denominator for the switch ticket.
- Add each counter to the paired output (tools/rpg_measure/paired.py) next to deaths by cause.
- Add a line in docs/observability/how_to_run_simulation.md where the paired outputs are listed.

## Out of Scope
- Any decision-path read of these counters.
- Any change to collapse, starvation or escalation behaviour.
- One ledger row per paired invocation: TCK-20261023-PAIRED-WRITES-ONE-RUN-LEDGER-ROW-PER-INVOCATION. Coordinate with it if both are in flight.

## Acceptance Criteria
- The counters are read only from state the apply path already writes. They are ledger only, not canonical state, and the run hash is equal with the ledger on and off (pure observer, like the behaviour counters).
- One unit test per counter: normal, at the threshold, below the threshold, and a distinct-entity count that does not double-count.
- Paired output shows base vs new for all three counters per world.
- The doc line is added. Parity ledger: an infrastructure.yaml entry if the ledger contract is tracked there.

## Related Tickets
- TCK-20261029-AN-ESCALATED-NEED-THAT-WINS-SCORING-LOSES-THE-PROJECT-SWITCH (uses 2 and 3 as its outcome measure; if these land first, its (c)/(d) need no per-tick traces)
- TCK-20261027-CAPACITY-GATE-FIRST-RECORD-OF-KIND-IS-DEAD-SO-LIVE-SIBLING-NEVER-RESUMED
- TCK-20261023-PAIRED-WRITES-ONE-RUN-LEDGER-ROW-PER-INVOCATION
- TCK-20261009-SLEEP-DEBT-WEAKENS-THEN-COLLAPSES-THE-SUBJECT-WHERE-IT-STANDS-NO-HP-LOSS

## Related Docs
- docs/observability/how_to_run_simulation.md
- docs/mechanics/01_entity_anatomy.md (Staged Sleep Debt), 04_strategic_cognition.md (Standing Needs Escalate)
- docs/world_rules/life-body/survival-needs.md (SURV-02, SURV-07)

## Related Stored Artifacts

## Related Code Areas
- src/observability/run_ledger.py (RunLedger)
- src/engine/starvation.py (STARVING_LINE), src/engine/sleep_debt.py (COLLAPSE_LINE, COLLAPSE_FLAG)
- tools/rpg_measure/paired.py

## Assumptions / Open Questions
- Placement (rpg-planner): lane C after #779 and PAIRED-WRITES, or lane A after :1610, whichever is free first. Best before the switch ticket's counts so they can use it. Not dispatched.

## Implementation Notes
## Test Summary
## Files Changed
## Completion Summary
