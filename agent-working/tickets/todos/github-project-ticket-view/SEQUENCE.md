# Implementation Sequence: github-project-ticket-view

Epic `TCK-20261112-EPIC-GITHUB-PROJECT-TICKET-VIEW`, filed by agent-working-planner-u24 on 2026-11-12. Source: owner #715
6813165811. Designed by agent-working-designer-u24, and lead-planner-u24 OK'd the design. Design: main-checkout
`.claude/handover/drafts/github-project-ticket-view-2026-11-12.md`.

## Order

1. **DONE** TCK-20261112-PROJECT-SYNC-DRY-RUN (P0, standard): `project_sync.py --dry-run` on u24, rpg lanes. Merged in #889
   (c73d76bad). The owner's go was 6813165811.
2. TCK-20261112-PROJECT-SYNC-GUARD-SEAT-AND-STALE (P1a, standard): the guard fix first, then seat mapping (investigated first), `Stale`, the
   entry point and the host name. Dry-run only, covered by go 6813165811 (split by the lead on #715).
3. P1b, not cut: `--init`/`--apply`. Waits for the owner's token result (fine-grained reads tested; writes proven on the first --init;
   fallback classic `project`), the Project, and a fresh go.

## Not cut yet

- **P2:** ubuntu runs the same tool. Needs the token on ubuntu.
- **P3:** all lanes and a per-host timer. Needs the owner's timer decision.
- **P4:** the claim-rule change. Needs the owner's decision after P3.

## Rules

- Every child closes its own ticket, and none of them is a ride-along, because each one is code.
- The ticket files stay the only source. Nothing reads the Project back into tickets.
