---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261109-NEXT-GENERATION-ENGINE-ACCESS-AUDIT
artifact_type: test_plan
tags: [architecture, engine, determinism]
---

Written retroactively at close (2026-11-11). This records the work as done; it was not a pre-implementation artifact.

# Test plan

- Unit: `tests/unit/engine/access_audit/` (declarations cover every step; observe; flag and on/off equivalence of hash and event count; positive controls including the full-deque append, a blind-spot control, the id-reuse control and the field-diff row; report). 76 tests at `-n 1` at close.
- Evidence (4a): 6 audit-ON cells (crowded_frontier s42 to s46, urban_political s46, 5000 ticks, `PYTHONHASHSEED=0`, approved wrapper) against the main 993400a52 base cells. Cell files are in `/mnt/data2/rpg-measure/evidence/access_audit/out_f19379c43/`.
- Full test.yml set at `-n 1`, mypy_gate and `codebase.health check`: results and the four triaged failures are in the ticket's Test Summary.
- Timing is not measured (4e).
