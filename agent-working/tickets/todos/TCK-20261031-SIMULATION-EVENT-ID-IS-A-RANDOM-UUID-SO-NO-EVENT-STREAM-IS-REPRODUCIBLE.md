---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20261031-SIMULATION-EVENT-ID-IS-A-RANDOM-UUID-SO-NO-EVENT-STREAM-IS-REPRODUCIBLE
phase: open
date: 2026-10-31
tags: []
---

# TCK-20261031-SIMULATION-EVENT-ID-IS-A-RANDOM-UUID-SO-NO-EVENT-STREAM-IS-REPRODUCIBLE

## Title
SimulationEvent.event_id is a random uuid4, so no event stream is byte-reproducible and any consumer that orders by it is nondeterministic

## Status
OPEN (seated by rpg-planner 2026-10-31; not dispatched)

## Tier
standard (provisional)

## Type
bug

## Priority
P3

## Request Summary
src/observability/events.py:56: `event_id = Field(default_factory=lambda: uuid.uuid4().hex)`, outside the seeded simulation. Found by rpg-planner-ubuntu during the SimQ anchor bisect (TCK-20261030-SIMQ-ANCHOR-REDS-SINCE-V1-REANCHOR-NEED-A-BISECT), confirmed on u24 main by lead-planner-u24. Simulation state is unaffected (events are non-authoritative), but: (1) event files can never be compared byte-for-byte, so determinism checks over them must exclude event_id; (2) any consumer that ORDERS by event_id inherits randomness.

## Scope
- Audit every consumer of event_id: src/domains/campaigns/behavior_change.py:24 and forbidden.py:24 sort by (tick, event_id) -- determine whether CampaignEvent.event_id derives from SimulationEvent's uuid (if so, same-tick order and so proofs/forbidden detection are nondeterministic); src/simulation_quality/pillar_accumulator.py:39-48 dedups by event_id (order-free, likely fine); cognition recorder trigger_event_id; event_recorder envelope.
- Decide: a deterministic event id (e.g. tick + per-tick sequence, from the seeded run) vs keeping uuid4 and fixing order-dependent consumers to a stable key.

## Out of Scope
- SimQ re-anchor (it compares quality_scores excluding event_id, ruled 2026-10-31).

## Acceptance Criteria
- Two same-seed runs produce identical campaign detector output (proofs, forbidden findings).
- Either event streams are byte-identical across same-seed runs, or the contract (docs/engine/matrices/replay_test_matrix.md / decision_trace_contract) states event_id is excluded from determinism, with a test that every order-dependent consumer uses a stable key.

## Related Tickets
- TCK-20261030-SIMQ-ANCHOR-REDS-SINCE-V1-REANCHOR-NEED-A-BISECT
- TCK-20260619-P0-DETERMINISM

## Related Docs
- docs/engine/matrices/replay_test_matrix.md; docs/observability/decision_trace_contract.md

## Related Stored Artifacts

## Related Code Areas
- src/observability/events.py, src/domains/campaigns/, src/simulation_quality/pillar_accumulator.py

## Assumptions / Open Questions
- Is CampaignEvent.event_id copied from SimulationEvent.event_id?
- rpg-planner-ubuntu (SimQ probes README, ed1d208d5, 2026-10-31): nothing in the simulation core reads event_id; outside observability/simulation_quality the only readers are campaign post-analysis (not run by the single-episode path) and source_event_id fields built from category/region/tick strings. So the exposure is the campaign post-analysis path only.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
