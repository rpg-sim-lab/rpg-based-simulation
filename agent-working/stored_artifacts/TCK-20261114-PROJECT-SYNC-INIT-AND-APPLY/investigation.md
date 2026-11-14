---
status: historical
layer: ticket
authority: P2
audience: agent
phase: done
ticket_id: TCK-20261114-PROJECT-SYNC-INIT-AND-APPLY
artifact_type: investigation
tags: [planning, delivery]
---

# Investigation

Owner go: #715 6873359996 (P1b only). Design: main-checkout `.claude/handover/drafts/github-project-ticket-view-2026-11-12.md` §2, §4, §6. P1a artifacts: `agent-working/stored_artifacts/TCK-20261112-PROJECT-SYNC-GUARD-SEAT-AND-STALE/`.

## What exists (read from `tools/sessions/project_sync.py` on origin/main 5c293ac96)
- `_guard` is an allowlist for reads; `gh api graphql` is refused (`_gh_api_is_read` accepts only one `repos/...` endpoint). It stays as is.
- `build_plan(...)` is pure: it takes the current items as a list of dicts keyed by field name (`Title`, `Ticket ID`, `Status`, `Domain`, `Seat`, `Host`, `Branch`, `PR`, `Tier`, `Sync hash`) and returns `Plan(creates, updates, archives, hand_edits, findings, notes)`. Creates carry the derived dict (including `Body`, `Source`, `Sync hash`); updates carry `(derived, changed_fields)`; archives are `(ticket id or title, reason)`.
- `main()` refuses `--apply`/`--init` with exit 2 and takes items only from `--items <file>`.
- `registries/session_project.yaml`: `project.owner: rpg-sim-lab`, `project.number: 0`.

## What P1b needs
1. A GraphQL path with its own token handling. The read guard must not gain a graphql branch, so the client is a separate class that calls `subprocess.run(["gh","api","graphql","--input","-"], input=<json body>, env=<copy + GH_TOKEN>)`. The query and variables go on stdin, the token only in that child's env: nothing secret or large in argv.
2. Live read: `organization(login){projectV2(number){id, fields, items(first:100,after){nodes{id isArchived content{... on DraftIssue{id title}} fieldValues{...}}}}}`, paginated. Items are mapped to the dict shape `build_plan` already takes, plus the private keys `_item_id`, `_draft_id`. Archived items are skipped (the plan reconciles live items).
3. `--init`: read fields; classify each wanted field (missing / right type / wrong type) before any write; wrong type means report and write nothing. Create missing ones (`createProjectV2Field`); set built-in `Status` options with `updateProjectV2Field` only when they differ from `STATUSES`.
4. `--apply`: print the plan, then run mutations in a fixed order: create = `addProjectV2DraftIssue` then field values with `Sync hash` last; update = `updateProjectV2DraftIssue` (when the title changed) then changed fields, `Sync hash` last; archive = `archiveProjectV2Item`. No delete mutation exists in the module (a test greps the module text).

## Risks and open points
- A fine-grained token on an org Project is unconfirmed (design §6, §10). The first `--init` (AC 2b) is the proof; on a refusal we stop and report.
- Replacing the Status options (`updateProjectV2Field`) drops option ids; on a Project with items already set, those items lose their Status value until the next `--apply`. Acceptable here because the Project is new and empty; `--init` only does it when the options differ, and the next `--apply` re-sets them, because a cleared Status reads back as empty, which differs from the derived value.
- Empty derived values (for example `Tier` or `PR` ""): on create they are skipped; on update they use `clearProjectV2ItemFieldValue`.
- Rate limits and partial failure: a failing mutation stops the run and reports; the next run reconciles.
- The token file path `~/.config/rpg-project-sync/token`, mode must be exactly 600; the module never prints it, never puts it in argv, and redacts it from any captured stderr before it is raised.
