---
status: active
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20261111-A-HOLD-MODE-MOVE-STILL-TAKES-A-STEP
artifact_type: test_plan
tags: []
---

# Test plan

Read-only so far. If the designer rules a defect: a unit test that a subject in mode HOLD with a stored target takes no step (resolve_move returns no new_position and no opportunity attack even at readiness 100 and move_cost 10), and that other modes are unchanged; the existing tests/unit/movement tests (HOLD occupant refuses to yield) stay green; a paired plain-vs-branch crowded_frontier cell only if the rule moves an outcome.

## Proof Plan

- Level: unit (if a fix is ruled) plus a paired measurement only if needed.
- Proof kind: behavioural unit test; for the read, file:line citations and the old-tree trace.
- Oracle source: tactical_contract.md:89 and the code comments (HOLD keeps the tile); the def2 trace.
- Expected effect: a HOLD subject takes no stored-target step.
- Selected commands: pytest tests/unit/movement -n 1 (scoped); parity-ledger schema check if the ledger is touched.
