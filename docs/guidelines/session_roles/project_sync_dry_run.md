---
status: active
layer: ai
authority: P2
audience: agent
tags: [ai, process-improvement, governance]
---

# Project sync (dry run, `--init`, `--apply`)

`tools/sessions/project_sync.py` derives the GitHub Project items for ticket state from ticket files on `origin/main`, this host's
worktrees and open PRs. By default it is a dry run: it prints a create / update / archive plan and writes nothing to GitHub or the repo. `--init` and `--apply` (P1b) write to the Project only.

Run it from any checkout: `python3 tools/sessions/project_sync.py` (or `python3 -m tools.sessions.project_sync`). `--host` defaults to
`host_names[hostname]` in `registries/session_project.yaml`, else the hostname. 

Read-only by construction: git goes through a verb allowlist, and `gh` is limited to `pr list` and `gh api repos/...` with only
`--paginate`, `--jq`/`-q` and `--header`/`-H`. `gh api graphql` and every other flag are refused.

Status, first match wins: Done, In review, Blocked, In progress, To do. **Stale** replaces In progress only: every branch working the
ticket is older than `stale_branch_days` (default 14). A branch's age is the newer of its last commit and its index mtime, so it is
approximate: anything that refreshes the index counts as activity. A fresh filing branch does not keep an abandoned working branch In progress.

**Known gap, `<domain> (seat not recorded)`:** the Seat is the one the launcher recorded for the worktree. Worktrees made by hand with
`git worktree add` have no record, so they show the branch-prefix domain and this label. It is a gap in the records, not a sync fault.
Filed as `TCK-20261112-HAND-ADDED-WORKTREES-ARE-NOT-RECORDED-AGAINST-A-SEAT`.

## Writing to the Project (`--init`, `--apply`)

Needs `project.number` in `registries/session_project.yaml` (the org Project `rpg-sim-lab/<number>`; `0` means exit 2) and the token file.

- **Token:** `~/.config/rpg-project-sync/token`, mode exactly 600, read only by `ProjectClient` (`tools/sessions/project_client.py`) and set as
  `GH_TOKEN` in the env of its own `gh api graphql` child process. It is never in argv (the query goes on stdin), never printed or logged, never
  exported, and is redacted from any error text. A missing, empty or looser-than-600 file is refused with a plain message. Never run
  `gh auth refresh -s project`: that widens the login every seat uses.
- **Live read:** when the Project is configured and the token is readable, the current items are read from the Project (paginated, archived
  items skipped). `--items <file>` replaces that for offline runs. A run with neither flag is still a dry run.
- **`python3 tools/sessions/project_sync.py --init`:** creates the missing fields by name (text `Ticket ID`, `Domain`, `Seat`, `Host`, `Branch`,
  `PR`, `Source`, `Sync hash`; single-select `Tier`) and sets the built-in `Status` options to the six statuses. Every check comes before any
  write: a same-named field of the wrong type, or a missing `Status` field, is reported with nothing written (exit 1). Replacing `Status`
  options clears each item's Status, so on a Project that already has items it is refused unless `--replace-status-options` is given.
  A second `--init` reports nothing created or updated.
- **`--apply`** (not with `--init` or `--items`): prints the plan, then carries it out. Create = draft item, then `Ticket ID` first and `Sync hash`
  last; update = changed fields, `Sync hash` last; archive = `archiveProjectV2Item`. A failing step stops the run and prints what was done
  and what was not; the next run reconciles. Items and fields are found by id read on each run; none is stored.
- **Never deleted:** the module has no delete mutation. Items without a `Ticket ID`, duplicates of one `Ticket ID`, and items whose ticket
  file is gone are archived, by their own item id.
