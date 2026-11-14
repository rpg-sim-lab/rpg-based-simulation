# Implementation Sequence: github-project-ticket-view

Epic `TCK-20261112-EPIC-GITHUB-PROJECT-TICKET-VIEW`, filed by agent-working-planner-u24 on 2026-11-12. Source: owner #715
6813165811. Designed by agent-working-designer-u24, and lead-planner-u24 OK'd the design. Design: main-checkout
`.claude/handover/drafts/github-project-ticket-view-2026-11-12.md`.

## Order

1. **DONE** TCK-20261112-PROJECT-SYNC-DRY-RUN (P0, standard): `project_sync.py --dry-run` on u24, rpg lanes. Merged in #889
   (c73d76bad). The owner's go was 6813165811.
2. **DONE** TCK-20261112-PROJECT-SYNC-GUARD-SEAT-AND-STALE (P1a, standard): merged in #893 (f62d240d0). Scope: the guard fix first, then seat mapping (investigated first), `Stale`, the
   entry point and the host name. Dry-run only, covered by go 6813165811 (split by the lead on #715).
3. **DONE** TCK-20261114-PROJECT-SYNC-INIT-AND-APPLY (P1b, standard; merged in #909, 6b8b56eda): `--init`/`--apply` on u24, rpg lanes, run by hand. The owner's
   fresh go is #715 6873359996 (P1b only). It needs the owner's empty org Project under rpg-sim-lab (its number goes into
   session_project.yaml). The first `--init` is the fine-grained token's write proof; if it is refused, stop, because the classic
   `project` fallback is the owner's decision.

4. **DONE** TCK-20261114-PROJECT-SYNC-LAYER-EPIC-PRIORITY-TAGS (P1c, standard; merged in #910, fc62c8557): Layer, Epic, Priority and
   Tags fields, rpg lane. The owner's go was #715 6874493351.
5. **DONE** TCK-20261114-PROJECT-SYNC-SECOND-HOST (P2, standard; merged in #913, 6822509a8): ubuntu writes Project 1 as a second
   host, rpg lane. It settled the two-writer question with host-scoped ownership: a `Host facts` field; Status, Seat and Domain come
   from the union of all hosts, and nothing is archived while another host has facts for the item. The owner's go was #715
   6875225978 item 2. The hold on u24 `--apply` lifts when u24 runs P2 code (its first P2 `--apply`, owner #715 6878981927).
6. **DONE** TCK-20261114-PROJECT-CLIENT-WRITE-PACING (P3a, standard): write pacing and `retry-after`, closed in the PR that files
   P3b and P3c. Dispatched on 2026-11-15 (owner #715 6881411615 item 3). A primary rate limit stops the run; a secondary one waits.
7. **DONE** TCK-20261115-PROJECT-SYNC-ALL-LANES (P3b, standard; closed in the PR that carries this line; first load 2026-11-14, 1608 steps, 183 items): all lanes, Domain as a single-select (the old text field is renamed, not
   deleted), the `attribute()` prefix fix, the Epic (a) fix, `--fetch`, a last-run file, and a heartbeat with the stale-host flag.
   Its first load was run by hand in the lead's terminal (owner #715 6883401913).
8. TCK-20261115-PROJECT-SYNC-HOST-TIMER (P3c, hotfix): systemd user timer templates (hourly; u24 at :00, ubuntu at :30; capped;
   exempt from HOST FREE) and the install doc. The owner installs them, and that install is the owner's standing approval for
   unattended writes (6881411615 item 1). Dispatched after P3b merges.

9. TCK-20261115-PROJECT-SYNC-FILED-DATE-AND-BACKLOG-VIEW (hotfix): a `Filed` date field from the frontmatter date, and the owner's
   Backlog view (To do, grouped by Domain, sorted by Priority and Filed). Owner concern #715 6883358041, go "File + dispatch after
   P3b" (6883401913). It is dispatched after P3b merges, before or alongside P3c.

P3 options and decisions: main-checkout `.claude/handover/drafts/project-sync-p3-timer-options-2026-11-15.md`, decided in #715
6881411615.

## Not cut yet

- **P4:** the claim-rule change. Needs the owner's decision after P3.

## Rules

- Every child closes its own ticket, and none of them is a ride-along, because each one is code.
- The ticket files stay the only source. Nothing reads the Project back into tickets.
