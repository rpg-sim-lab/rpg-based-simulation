# Implementation Sequence: github-project-ticket-view

Epic `TCK-20261112-EPIC-GITHUB-PROJECT-TICKET-VIEW`, filed by agent-working-planner-u24 on 2026-11-12. Source: owner #715
6813165811. Designed by agent-working-designer-u24, and lead-planner-u24 OK'd the design. Design: main-checkout
`.claude/handover/drafts/github-project-ticket-view-2026-11-12.md`.

## Order

1. TCK-20261112-PROJECT-SYNC-DRY-RUN (P0, standard): `project_sync.py --dry-run` on u24, rpg lanes. No token, no writes.
   The owner's go is 6813165811.

## Not cut yet

- **P1:** `--init` / `--apply` on u24, rpg lanes. Cut it after P0 lands and the owner has created the Project and chosen the
  token (fine-grained tested first, else classic `project`). The lead carries that ask.
- **P2:** ubuntu runs the same tool. Needs the token on ubuntu.
- **P3:** all lanes and a per-host timer. Needs the owner's timer decision.
- **P4:** the claim-rule change. Needs the owner's decision after P3.

## Rules

- Every child closes its own ticket, and none of them is a ride-along, because each one is code.
- The ticket files stay the only source. Nothing reads the Project back into tickets.
