---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261029-KERNEL-IMPORTS-SIMQ-WIRING-INSTEAD-OF-RECEIVING-IT-FROM-ITS-COMPOSITION-ROOT
phase: open
date: 2026-10-29
tags: []
---

# TCK-20261029-KERNEL-IMPORTS-SIMQ-WIRING-INSTEAD-OF-RECEIVING-IT-FROM-ITS-COMPOSITION-ROOT

## Title
Kernel imports src.simulation_quality.wiring (a grandfathered engine -> simulation_quality edge) instead of receiving the quality wiring from its composition root

## Status
OPEN

## Tier
standard

## Type
refactor

## Priority
P3

## Request Summary
Follow-up from PR #779 (TCK-20261028-EVENT-RECORDER-NEVER-GIVEN-THE-RUN-ID-SO-EVENTS-SAY-UNKNOWN-RUN). Moving the SimQ hub construction into src/simulation_quality/wiring.py narrowed the grandfathered engine->simulation_quality import edges from five to one (`src.engine.kernel -> src.simulation_quality.wiring`, kept in codebase/structure/import_layers_baseline.txt with codebase-planner's agreement). The clean shape is to remove that edge: the Kernel receives a quality-wiring factory (or the built feed and hub) from whoever constructs it, so the engine layer never imports simulation_quality.

## Scope
1. List every Kernel construction site (src, tools, tests).
2. Add an optional injected factory, defaulting to no SimQ when absent, and have the composition roots that want SimQ pass build_quality_wiring.
3. Delete the remaining baseline line (codebase-planner agrees on the PR).
4. Show that OFF and ON runs are unchanged: pure-run digest equality on a short run, plus the SimQ score file being identical with SimQ on.

## Out of Scope
SimQ scorer logic; EventRecorder.

## Acceptance Criteria
- No src.engine -> src.simulation_quality import remains, and the import-contract gate passes with the baseline line removed.
- Every construction site that ran SimQ before still does; the digest and the score file are unchanged.

## Related Tickets
TCK-20261028-EVENT-RECORDER-NEVER-GIVEN-THE-RUN-ID-SO-EVENTS-SAY-UNKNOWN-RUN (#779)

## Related Docs
docs/observability/how_to_run_simulation.md

## Related Stored Artifacts
None.

## Related Code Areas
src/engine/kernel.py, src/simulation_quality/wiring.py, codebase/structure/import_layers_baseline.txt

## Assumptions / Open Questions
- How many construction sites rely on the env-driven SimQ default is unmeasured.

## Implementation Notes
Filed on the rpg-planner seat; not dispatched.

## Test Summary

## Files Changed

## Completion Summary
