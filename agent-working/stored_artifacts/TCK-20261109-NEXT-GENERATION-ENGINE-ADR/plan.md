---
status: active
layer: architecture
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20261109-NEXT-GENERATION-ENGINE-ADR
tags: []
---

# plan - TCK-20261109-NEXT-GENERATION-ENGINE-ADR

Adopt the drafted ADR as a recorded decision. Do not rewrite it.

1. Review the draft at `architecture-next-generation-engine-epic` 9880862c3 against `main` 1fb40ac76 (lead-planner review 1/2,
   R1-R6 and N1-N2, sent via lead-planner-u24).
2. architecture-planner-u24 applies R1-R5 and N1-N2. Recheck the result at 3299c3180.
3. The owner accepts it (#715 6742854335).
4. Adopt it:
   - move the draft to `docs/architecture/next_generation_engine_adr.md` with status Accepted (R6);
   - add the direction paragraph to `docs/architecture/system_overview.md` after "What is deliberately not distributed";
   - add the C-10 evidence-route pointer to `docs/architecture/performance_optimization_decisions.md`.

Out of scope: the distributed-workers ADR amendment, the system_overview "one process" bullet (R1: the companion ADR owns it), and
code.
