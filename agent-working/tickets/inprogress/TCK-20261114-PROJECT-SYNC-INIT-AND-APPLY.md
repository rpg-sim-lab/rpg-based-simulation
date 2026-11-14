---
status: active
layer: ticket
authority: P1
audience: agent
ticket_id: TCK-20261114-PROJECT-SYNC-INIT-AND-APPLY
phase: inprogress
date: 2026-11-14
tags: [planning, delivery]
---

# TCK-20261114-PROJECT-SYNC-INIT-AND-APPLY

## Title
`project_sync.py` P1b: `--init` creates the Project's fields by name and `--apply` writes the plan, through one token-scoped GraphQL path; u24, rpg lanes, run by hand

## Status
INPROGRESS

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Child P1b of TCK-20261112-EPIC-GITHUB-PROJECT-TICKET-VIEW. P0 (#889, c73d76bad) and P1a (#893, f62d240d0) are merged; both are
dry-run only. The owner's fresh go for P1b is on #715 as 6873359996: "we can start GitHub Project ticket view
github-project-ticket-view now". It covers P1b only, not P2, P3 or P4. Design: main-checkout
`.claude/handover/drafts/github-project-ticket-view-2026-11-12.md` §2, §4 and §6.

The owner creates an empty **organization** Project under `rpg-sim-lab` and gives its number N, from the URL
`github.com/orgs/rpg-sim-lab/projects/N`. The settings went to the lead to relay on 2026-11-14. The token is the owner's existing
file `~/.config/rpg-project-sync/token` (mode 600, fine-grained). Whether it can write is proven by the first `--init`.

## Scope
1. **One GraphQL path, separate from the read guard.** `_guard` and `run_command` stay as they are: `gh api graphql` is still refused
   there. Add one `ProjectClient`, a small class that is injectable in tests.
   - It runs `gh api graphql` with `GH_TOKEN` read from the token file and set **only in that subprocess's env**.
   - The token is never in argv, never printed, never logged, never in an exception message and never in the parent env.
   - A missing file, or a file mode other than 600, means a refusal with a plain message.
   - Every GraphQL call (queries and mutations) goes through this client, and nothing else in the module runs `gh api graphql`.
2. **Find the Project.** Use `organization(login: <project.owner>) { projectV2(number: <project.number>) }`. `project.number: 0`,
   or a Project that isn't found, means `--init` and `--apply` refuse with exit 2. Set `number: N` in
   `registries/session_project.yaml` once the owner gives N.
3. **Live item read.** List every item, paginated, with its field values by name. This replaces `--items` as the default input
   when the Project is configured and the token is readable. `--items <file>` stays, for offline runs and tests.
4. **`--init`: idempotent, fields by name** (design §2, plus P1a's `Stale`).
   - Create missing fields: text fields `Ticket ID`, `Domain`, `Seat`, `Host`, `Branch`, `PR`, `Source`, `Sync hash`, and the
     single-select `Tier` (hotfix, standard, epic).
   - Reuse the Project's built-in `Status` single-select, which can't be deleted. Set its options to exactly `STATUSES`:
     To do, In progress, Stale, In review, Blocked, Done.
   - The built-in `Title` is used as is.
   - A field that exists with the right name and type is left alone.
   - A same-named field with the wrong type means: report it, write nothing, exit non-zero. Never delete or rename a field.
   - Print what was created, updated or left alone.
5. **`--apply`.** Compute the same plan the dry run prints, print it, then carry it out.
   - **Create:** `addProjectV2DraftIssue` (title and the one-line `BODY`), then set each field, `Sync hash` last.
   - **Update:** set the changed fields. If the title changed, also update the draft issue's title. Recompute `Sync hash` last.
   - **Archive:** `archiveProjectV2Item`. **Never delete.**
   - Field and option ids are looked up by name on each run. None are stored.
   - A failure partway through stops the run. It reports what was done and what wasn't. Running again reconciles, because the
     plan is a full reconcile.
6. **Default stays dry.** With neither flag, the run prints the plan and writes nothing (live read if configured, else `--items`).
7. **Docs.** Update `docs/guidelines/session_roles/project_sync_dry_run.md` with the `--init`/`--apply` usage, the token rule and
   the never-delete rule. A file rename is not needed.
8. **Tests, no network** (injected client; about 8):
   - init creates missing fields and leaves present ones alone;
   - init sets the built-in Status options;
   - init refuses a wrong-type same-named field;
   - apply turns creates, updates and archives into the expected mutation sequence, with `Sync hash` last;
   - apply stops on a failed mutation and reports what it did;
   - `number: 0` refuses with exit 2;
   - the token value never shows up in argv, stdout, stderr or exception text (use a sentinel token);
   - `_guard` still refuses `gh api graphql` on the read path.

## Out of Scope
- P2 (ubuntu), P3 (all lanes and a timer), P4 (claim rule): each needs its own owner decision.
- Creating the Project, or creating or changing any token: the owner's actions. Never run `gh auth refresh -s project` (design §6).
- Views: the owner sets them by hand in the UI.
- Writing anything back to ticket files or issues (design constraint 1).
- Any change to `tools/sessions/status.py`, the launcher or the roster: stop and tell the planner first.

## Acceptance Criteria
1. Scope items 1-8 are built. The scoped tests pass: `tests/tools/test_session_project_sync.py` and `tests/tools/test_session_status*.py`.
2. **Write proof, run by hand on u24, in this order, each only after the previous step is clean:**
   - (a) Run the live dry run against the owner's Project and send the planner its output.
   - (b) Run `--init`. If GitHub refuses a write (permission or `Resource not accessible`), **stop**. Report the exact error with the
     token redacted. Do not try another token or scope: the classic `project` fallback is the owner's decision, through the lead.
   - (c) Run `--init` a second time. It must report nothing created and nothing updated.
   - (d) The planner reviews the `--apply` plan. Then run `--apply` once.
   - (e) Run the dry run again. It must show no creates, no updates and no hand edits.
3. The PR body carries the redacted output of (a)-(e).
4. The staging artifacts exist. agent-working-designer-u24 reviews plan.md before any code.
5. `grep` of the diff and the captured outputs for the token value finds nothing. The implementer checks this locally and never
   prints the token to do it.

## Related Tickets
- TCK-20261112-EPIC-GITHUB-PROJECT-TICKET-VIEW (parent)
- TCK-20261112-PROJECT-SYNC-DRY-RUN (P0, #889)
- TCK-20261112-PROJECT-SYNC-GUARD-SEAT-AND-STALE (P1a, #893)

## Related Docs
- docs/guidelines/session_roles/project_sync_dry_run.md

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20261112-PROJECT-SYNC-DRY-RUN/
- agent-working/stored_artifacts/TCK-20261112-PROJECT-SYNC-GUARD-SEAT-AND-STALE/
- Designer draft (main checkout): `.claude/handover/drafts/github-project-ticket-view-2026-11-12.md`

## Related Code Areas
- tools/sessions/project_sync.py, registries/session_project.yaml, tests/tools/test_session_project_sync.py

## Assumptions / Open Questions
- **Simpler-fix check (6698958617):**
  - The simplest working shape is one client, `--init` and a full-reconcile `--apply`.
  - Cost: about 150 lines and 8 tests, and no measurement runs.
  - Left out: incremental or partial apply, retries, views, and a second host.
  - A script that only creates (no update or archive) would be smaller, but it would break the full-reconcile design (§4) on the
    first rerun, so it isn't simpler overall.
- **The built-in Status field:** new Projects come with a `Status` single-select (Todo / In Progress / Done). The design names its
  field `Status`, so reusing the built-in one is the only option that keeps that name. If GitHub refuses to edit its options, report
  it and stop. Don't rename the field.
- **Fine-grained token on an org Project:** this is unconfirmed (design §6, §10), and step 2(b) is the proof. It needs the token's
  resource owner to be `rpg-sim-lab`, with the organization permission "Projects: Read and write", and the org must allow
  fine-grained tokens.
- **Project number:** if the owner hasn't given N by the time code is ready, stop at AC 2(a) and wait. Never guess a number, and never
  create a Project.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
