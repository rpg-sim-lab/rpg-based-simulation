---
status: active
layer: ai
authority: P2
audience: agent
tags: [ai, process-improvement, governance]
---

# Project sync dry run

`tools/sessions/project_sync.py` derives the GitHub Project items for ticket state from ticket files on `origin/main`, this host's
worktrees and open PRs. It is a dry run: it prints a create / update / archive plan and writes nothing to GitHub or the repo.

Run it from any checkout: `python3 tools/sessions/project_sync.py` (or `python3 -m tools.sessions.project_sync`). `--host` defaults to
`host_names[hostname]` in `registries/session_project.yaml`, else the hostname. `--apply` and `--init` are refused.

Read-only by construction: git goes through a verb allowlist, and `gh` is limited to `pr list` and `gh api repos/...` with only
`--paginate`, `--jq`/`-q` and `--header`/`-H`. `gh api graphql` and every other flag are refused.

Status, first match wins: Done, In review, Blocked, In progress, To do. **Stale** replaces In progress only: every branch working the
ticket is older than `stale_branch_days` (default 14). A branch's age is the newer of its last commit and its index mtime, so it is
approximate: anything that refreshes the index counts as activity. A fresh filing branch does not keep an abandoned working branch In progress.

**Known gap, `<domain> (seat not recorded)`:** the Seat is the one the launcher recorded for the worktree. Worktrees made by hand with
`git worktree add` have no record, so they show the branch-prefix domain and this label. It is a gap in the records, not a sync fault.
Filed as `TCK-20261112-HAND-ADDED-WORKTREES-ARE-NOT-RECORDED-AGAINST-A-SEAT`.
