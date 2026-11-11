---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20261110-A-RESTORED-SCENARIO-DROPS-ITS-GOVERNOR-AND-EVENT-RECORDER
phase: open
date: 2026-11-10
tags: []
---

# TCK-20261110-A-RESTORED-SCENARIO-DROPS-ITS-GOVERNOR-AND-EVENT-RECORDER

## Title
A scenario restored from a checkpoint drops the service's governor and its scenario event recorder

## Status
OPEN

## Tier
hotfix

## Type
bug

## Priority
P3

## Request Summary
Found while answering lead-planner-u24's questions for testing-planner's restore-and-continue equivalence ticket (TCK-20261110-A-RUN-RESTORED-FROM-A-CHECKPOINT-EQUALS-THE-UNINTERRUPTED-RUN-TICK-BY-TICK, #715 6757579399). Read on main cf27795cb.

`ScenarioCheckpointer.restore` (src/engine/scenario_checkpoint.py:111-118) builds its Kernel without `governor=` and rebuilds the service as `ScenarioRuntimeService(spec)`. The build path passes `governor=self._governor` (scenario_runtime.py:424), and the service takes `scenario_event_recorder`. So a restored run loses a pinned governor (`zeroes_signals`, the test pin) and the scenario event recorder.

Effect on main: authoritative state is not changed.
- The scheduler sheds no work.
- The executor is sequential (max_worker_count=0 on both paths).
- Replay is off (no_replay).
The restored run's mode telemetry can differ (status.current_mode and the resource_governor events), and scenario objective events after restore go nowhere.

## Scope
1. `restore` accepts `governor` and `scenario_event_recorder`, keyword-only and defaulting to None. It passes them to the Kernel and to the rebuilt service.
2. Update callers that restore a service built with either.
3. Tests: the equivalence ticket's strict-xfail row (pinned governor and recorder survive checkpoint and restore) turns to a pass. Remove its xfail in this ticket.

## Out of Scope
- A concurrent executor on restore. max_worker_count=0 is deliberate on both paths (rpg-planner ruling, 2026-11-10).
- One shared RuntimeProfile builder for both paths. That's an optional refactor; the equivalence ticket pins that the two profiles are equal.
- The checkpoint format version (TCK-20261101-A-CHECKPOINT-HAS-NO-FORMAT-VERSION).

## Acceptance Criteria
- The governor and recorder row passes with no xfail.
- The restore-equivalence state-digest rows still pass.
- No RPG re-measure is needed, because no authoritative state changes. Say so at close.

## Related Tickets
- TCK-20261110-A-RUN-RESTORED-FROM-A-CHECKPOINT-EQUALS-THE-UNINTERRUPTED-RUN-TICK-BY-TICK (testing-planner, the xfail row)
- TCK-20260619-E31C-CHECKPOINT (done)
- TCK-20261101-A-CHECKPOINT-HAS-NO-FORMAT-VERSION

## Related Docs
- docs/engine/scenario_runtime_contract.md (Checkpoint Format)

## Related Stored Artifacts
None.

## Related Code Areas
- src/engine/scenario_checkpoint.py:95-121
- src/engine/scenario_runtime.py:140-160, :405-424

## Assumptions / Open Questions
- Dispatch comes after the RPG batch, in a gap. It's small and has no measurement, so it can pair with the equivalence ticket's run slot.

## Implementation Notes
None yet.

## Test Summary

## Files Changed

## Completion Summary
