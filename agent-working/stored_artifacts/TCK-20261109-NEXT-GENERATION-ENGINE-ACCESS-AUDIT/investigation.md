---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261109-NEXT-GENERATION-ENGINE-ACCESS-AUDIT
artifact_type: investigation
tags: [architecture, engine, determinism]
---

Written retroactively at close (2026-11-11). This records the work as done; it was not a pre-implementation artifact.

# Investigation

Design inputs the work was built from:
- `docs/plans/architecture/next_generation_engine_feasibility_review.md` (section 2 table of step reads and writes; source of 12 of the 43 declarations).
- `src/engine/pipeline.py` `AuthoritativeApplyPipeline.refine`, which dispatches 43 steps through `run_phase`; 26 declarations come from the PhaseDependencyGraph output domains and 5 from the step name alone.
- The ticket `TCK-20261109-NEXT-GENERATION-ENGINE-ACCESS-AUDIT` (conditions 4a to 4e) and the rulings recorded in its Assumptions and Implementation Notes (Q2: no read proxy).

Findings made while building, all recorded in the report: `entity.timeline` is `deque(maxlen=200)` (`src/core/state.py:1018`), which explains why a first fingerprint missed cooperation's append at maxlen; the first sampled timeline check keyed by `id()` reported edits that were id reuse after eviction, so it was rekeyed by a stable event key.
