---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20261117-A-RESOLVE-BLOCKER-PROJECT-IS-RE-CREATED-EVERY-80-TICKS-AND-STALLS-COOPERATION
phase: done
artifact_type: test_plan
date: 2026-11-18
tags: []
---

# Test plan: churn fix

Unit: tests/unit/strategic/test_blocker_lifecycle.py (merge, quiet bound 199/200, stamps, trim, compose), test_project_end_sites.py (AST scans: ticks passed, end_record caller set, stamp strings), test_project_end_record.py, test_resolve_blocker_completion_is_typed.py, tests/unit/engine/test_checkpoint_fields.py, test_checkpoint_group_fields.py, test_checkpoint_schema.py, mechanism registry completeness.

## Proof Plan
- level: unit plus 4 cells x 5000 ticks with spy and plain twin (cells_fix2b)
- proof kind: B1-B6 = 0, timeout_ends >= 1, twin hash equal, PINNED, logging_errors 0, exceptions {}
- oracle source: designer ruling on own-job shape; spy blocker_spy_v3b.py
- expected effect: fewer builds, only typed ends, no quiet removal inside the bound
- selected commands: scoped pytest -n 1 over the files above and tests/architecture; run_cells_v3.sh; summarize_cells_v3.py; capread_n10.py
