---
status: historical
layer: ticket
authority: P1
audience: agent
ticket_id: TCK-20261112-PROJECT-SYNC-GUARD-SEAT-AND-STALE
phase: done
date: 2026-11-12
tags: [planning, delivery]
---

# TCK-20261112-PROJECT-SYNC-GUARD-SEAT-AND-STALE

## Title
`project_sync.py` P1a: a write-safe guard, correct Seat mapping, a `Stale` status for old branches, the script entry point and a short host name, all still dry-run (rpg lanes, u24)

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Child P1a of TCK-20261112-EPIC-GITHUB-PROJECT-TICKET-VIEW. P0 (TCK-20261112-PROJECT-SYNC-DRY-RUN) merged in #889 (c73d76bad).
Inputs:
- the #889 review (889#6814148816) guard nit;
- lead-planner-u24's run of the merged dry run on main (2026-11-12), with its 3 findings;
- the designer's AC-2 P1 notes;
- the lead's decision to fold all of it into one P1 ticket, so it lands as one PR.

The lead split P1 (#715, 2026-11-12): **P1a is this ticket.** It's dry-run only, needs no token and no Project, and the owner's go 6813165811 covers it. **P1b** (`--init`/`--apply`) waits for the owner's token result and a fresh go. Design: main-checkout `.claude/handover/drafts/github-project-ticket-view-2026-11-12.md`.

## Scope
1. **Guard first (AC 1, before any write code).** `_guard` matches write flags by prefix as well as by exact token:
   `-X…`/`--method…` other than GET, `-f…`, `-F…`, `--field…`, `--raw-field…`, `--input…`. So `--method=POST`, `-XPOST`,
   `-X=POST`, `-fk=v` and `--field=k=v` are refused. P1b's writes will need one explicit writer path. This ticket adds none.
2. **Seat mapping.** Today every seat prints `rpg (unmapped)`: status.py's roster mapping resolves no worktree to rpg-implementer,
   -2, -3 or rpg-planner. Investigate why. The likely cause is that batch worktrees (nonflight, recruit, rpg, …) aren't any seat's
   bound or default path. Fix it in the smallest place: a mapping in `registries/session_project.yaml`, or a status.py reader of
   the launcher's records. If the fix needs the launcher to record batch worktrees, say so in plan.md, and the ticket narrows.
3. **Stale branches.** A worktree branch whose newest commit and newest working-tree change are both older than
   `stale_branch_days` (session_project.yaml, default 14) shows Status `Stale`, not In progress. It's a new single-select
   option. Example: October's rpg-budget-overrun-telemetry and rpg-kernel-validates-flags-first.
4. **Entry point.** Add a sys.path shim, so `python3 tools/sessions/project_sync.py` works as well as `-m`.
5. **Host name.** The `--host` default comes from a hostname → short-name map in session_project.yaml
   (`u24desktop-Virtual-Machine` → `u24desktop`). It falls back to the hostname.
6. **Tests:**
   - Guard: one per spelling, 5 or more.
   - Seat mapping: 2-3.
   - Stale: 2.
   - Entry point: 1.
   - Host: 1.
   - No network in tests.

## Out of Scope
- `--init`, `--apply`, any GraphQL write and the token: P1b.
- ubuntu (P2), all lanes and the timer (P3), and the claim rule (P4).
- Creating the Project or any token: the owner's actions.
- Views (set by hand in the UI).
- **Any launcher or roster change outside tools/sessions: stop and tell the planner before building it (lead, 2026-11-12).**

## Acceptance Criteria
1. The guard refuses every joined spelling, with tests, before any write path exists in the diff's history order.
2. A real dry run on u24 shows mapped seats for the rpg seats' worktrees, and `Stale` for October's abandoned branches.
3. The real dry-run output goes in the PR body, with the seat and Stale changes against the P0 run.
4. The staging artifacts exist. agent-working-designer-u24 reviews plan.md before code.
5. Scoped tests only. Existing test_session_project_sync.py and test_session_status*.py tests pass.

## Related Tickets
- TCK-20261112-EPIC-GITHUB-PROJECT-TICKET-VIEW (parent)
- TCK-20261112-PROJECT-SYNC-DRY-RUN (P0, #889)

## Related Docs
- none yet; a README section for running the sync comes with this ticket

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20261112-PROJECT-SYNC-DRY-RUN/
- Designer draft (main checkout): `.claude/handover/drafts/github-project-ticket-view-2026-11-12.md`

## Related Code Areas
- tools/sessions/project_sync.py, tools/sessions/status.py, registries/session_project.yaml, tests/tools/test_session_project_sync.py

## Assumptions / Open Questions
- Simpler-fix check (6698958617): fixing quality while still in dry-run is cheaper than fixing it on a live board. Cost: about 140 lines and 13 tests. No measurement runs. Leaves out all writes (P1b).
- Seat mapping is the uncertain part, so plan.md investigates it first.

## Implementation Notes
- Guard: `gh api` is an allowlist (one `repos/...` endpoint, only `--paginate`, `-q/--jq`, `-H/--header`), per the designer's amendment B; `graphql` and every joined or unknown flag are refused.
- Seat: no map. The launcher's recorded seat stays first; the fallback label is `<domain> (seat not recorded)`. The launcher finding: hand-made `git worktree add` worktrees have no record (filed by the planner as TCK-20261112-HAND-ADDED-WORKTREES-ARE-NOT-RECORDED-AGAINST-A-SEAT, riding this PR, not implemented).
- Stale replaces In progress only (amendment C); BranchFact.last_activity from status.py `_activity` (newest of commit and index mtime; approximate).
- sys.path shim, `host_names` map and `stale_branch_days` in registries/session_project.yaml; doc: docs/guidelines/session_roles/project_sync_dry_run.md.

## Test Summary
77 passed: tests/tools/test_session_project_sync.py and tests/tools/test_session_status*.py (-p no:randomly). New: 13 guard refusals and 2 reads, 2 seat, 5 Stale, 1 entry point, 1 host, 1 registry.

## Files Changed
tools/sessions/project_sync.py, registries/session_project.yaml, tests/tools/test_session_project_sync.py, docs/guidelines/session_roles/project_sync_dry_run.md, stored artifacts.

## Completion Summary
P1a built dry-run only: allowlist guard, honest seat label, Stale status, script entry point and host short-name map. Real dry run on u24: 6 Stale rows including October's abandoned branches. Review: planner's PR review comment is recorded afterwards with record_review.py.
