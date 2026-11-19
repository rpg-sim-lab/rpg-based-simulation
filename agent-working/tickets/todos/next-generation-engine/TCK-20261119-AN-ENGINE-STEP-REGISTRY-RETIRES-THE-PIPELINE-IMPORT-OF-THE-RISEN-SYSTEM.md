---
status: active
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20261119-AN-ENGINE-STEP-REGISTRY-RETIRES-THE-PIPELINE-IMPORT-OF-THE-RISEN-SYSTEM
phase: open
date: 2026-11-19
tags: []
---

# TCK-20261119-AN-ENGINE-STEP-REGISTRY-RETIRES-THE-PIPELINE-IMPORT-OF-THE-RISEN-SYSTEM

## Title
An engine step registry lets world steps (such as rise) register with the pipeline, retiring the import-baseline row `src.engine.pipeline_phases.resources -> src.world.risen`

## Status
OPEN

## Tier
standard

## Type
refactor

## Priority
P2

## Request Summary
This is the retiring ticket the owner required for one import-baseline raise, filed by rpg-planner (the src/engine route) under the next-generation-engine epic. The approval came from the owner on #715 via the ubuntu lead, relayed by lead-planner-u24 on 2026-11-19. It accepts ONE import-baseline row for births (M1, rpg-planner-ubuntu's A2), `src.engine.pipeline_phases.resources -> src.world.risen` (129 -> 130), on codebase-planner's conditions. Condition 2: this retiring ticket is on main BEFORE births merges.

Why the row is needed today (evidence relayed by the lead; inspected by codebase-planner):
- The pipeline is static methods with no hook point.
- A kernel is built in about 20 places, including scenario_checkpoint.py's restore path.
- So a seam wired from above would silently skip rise on some builds, and the direct import is the honest form until a registry exists.

## Scope
1. An engine step registry: world-layer steps (rise first) register with the pipeline phase that runs them. The engine never imports the world module. Every kernel build path, the checkpoint restore included, gets the same registered steps, by construction and with a test.
2. Rise moves to it. The `src.engine.pipeline_phases.resources -> src.world.risen` row is removed from the import baseline, which goes 130 -> 129 or lower, with no other row added.
3. Level A equivalence, per the epic: a content compare, then hash and TICK_END trail, all hash-equal on the gate worlds.

## Out of Scope
- Any behaviour change to rise or births.
- Other engine-to-world imports, unless they move with the same registry and are named here.

## Acceptance Criteria
- The import baseline no longer lists `src.engine.pipeline_phases.resources -> src.world.risen`.
- A test shows that every kernel construction site, the restore path included, runs the registered rise step.
- Hash-equal on the gate worlds (S9).
- This is the exit for the births A2 baseline row.

## Related Tickets
- TCK-20261109-EPIC-NEXT-GENERATION-ENGINE (parent epic)
- TCK-20261109-M1-BASIC-WILD-BIRTHS-FOR-EVERY-LIVING-KIND (births, the row's origin)

## Related Docs
- docs/architecture/next_generation_engine_adr.md; docs/engine/kernel.md; docs/engine/authoritative_pipeline.md

## Related Stored Artifacts
- None.

## Related Code Areas
- src/engine/pipeline_phases/resources.py; src/world/risen.py; the kernel construction sites (scenario_checkpoint.py restore, among about 20)

## Assumptions / Open Questions
- Whether the registry is a stage of the epic's contract spec (TCK-20261109-NEXT-GENERATION-ENGINE-CONTRACT-SPEC) or comes before it is decided by the epic's owner (architecture-planner-u24) when it runs again. The sequence rule holds meanwhile: src/engine stages are sequenced by rpg-planner around M1.

## Durable state, lifecycle and clocks
None. It is a structural move only.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
