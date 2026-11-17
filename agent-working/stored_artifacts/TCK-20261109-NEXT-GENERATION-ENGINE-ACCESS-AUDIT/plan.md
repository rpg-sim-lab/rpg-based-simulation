---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261109-NEXT-GENERATION-ENGINE-ACCESS-AUDIT
artifact_type: plan
tags: [architecture, engine, determinism]
---

Written retroactively at close (2026-11-11). This records the work as done; it was not a pre-implementation artifact.

# Plan

The approved plan is `docs/plans/architecture/next_generation_engine_access_audit_plan.md` at `origin/architecture-next-generation-engine-epic @ d68b2cd4a` (not yet on main; lands with child 4). The ADR it serves is `docs/architecture/next_generation_engine_adr.md`. This file records how the plan was built, and where it was not followed.

| Plan section | As built |
|---|---|
| 1, what it does | Writes are the diff of the input update against the step's result; hidden mutations are a two-tier state fingerprint; process globals are a fixed watch list read through `sys.modules`. Reads are statically derived (ruling Q2, no read proxy), labelled "statically derived, not observed". |
| 2, files | `observer.py` became `observe.py` + `recorder.py` + `hook.py`; `declarations.py`, `static_reads.py` and `report.py` as planned; one dispatch call in `src/engine/pipeline.py`; flag `ENABLE_ACCESS_AUDIT` (off) in `src/domains/optimization/feature_flags.py`. Tests are under `tests/unit/engine/access_audit/`. |
| 3, the switch | Departure: the recorder is passed through `state.feature_flags["ACCESS_AUDIT_SINK"]` (not hashed, `compare=False`), not held by a kernel-owned auditor; checkpointing is unsupported while it is on. |
| 3a, hidden mutations | Tier 1 content digest of a watch list (depth 3, 400-node cap) and Tier 2 identity and length; deques included after a full-deque append was found invisible; the timeline gets a token plus a sampled content check every 100 ticks. Positive controls are in `test_observer_controls.py`. |
| 4, evidence | Conditions 4a to 4e are in `docs/plans/architecture/next_generation_engine_access_audit_report.md` and the ticket's Test Summary. |
| 6, report | Departure for the in-place input-update table only: tick counts are not recorded (the recorder keeps a per-run set); the table is a lower bound. |

Detail of each ruling and departure: the ticket's Implementation Notes and Completion Summary.
