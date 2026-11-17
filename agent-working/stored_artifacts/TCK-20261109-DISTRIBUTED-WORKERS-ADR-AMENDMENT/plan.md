---
status: active
layer: architecture
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20261109-DISTRIBUTED-WORKERS-ADR-AMENDMENT
tags: []
---

# plan - TCK-20261109-DISTRIBUTED-WORKERS-ADR-AMENDMENT

Adopt the accepted amendment (owner, #715 6777076537) as a new ADR file in `docs/architecture/`:
1. `git mv` the draft to `docs/architecture/distributed_workers_adr.md`; rewrite the header and Status as accepted; cite 6777076537, 6776551375 and 6776564953.
2. Record the owner's first-build choices as Decision 6; update "Not decided here" and Risks to match the accepted design (f517f1fdf).
3. Apply §5.1 to `system_overview.md` and §5.2 to `devops_plan_amendment_proposal.md`, verbatim with the ADR's quotes.
4. Leave §5.3 (epic child 5) and §5.4 (architecture-planner-u24) unapplied, and say so.
5. Close the ticket, mark SEQUENCE item 1 DONE, run the closure tool and done_checker.
