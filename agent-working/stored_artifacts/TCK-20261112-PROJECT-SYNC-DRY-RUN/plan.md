---
status: historical
layer: ticket
authority: P2
audience: agent
phase: done
ticket_id: TCK-20261112-PROJECT-SYNC-DRY-RUN
artifact_type: plan
tags: [planning, delivery]
---

# Plan

All new code is in `tools/sessions/project_sync.py` (pure functions plus a thin CLI) and `registries/session_project.yaml`. No change to `status.py`; it is reused through its public builders and one private helper (`_worktree_for`), which I propose to import as-is rather than rename (a rename would touch the unchanged status tests).

## Data shapes (frozen dataclasses)
- `Ticket(id, folder, path, tier, title, blocked, date)` read from origin/main.
- `BranchFact(host, branch, worktree, seat, domain, tickets: frozenset[str])`.
- `PrFact(number, url, files: frozenset[str])`.
- `Item(fields: dict)`; `Plan(creates, updates, archives, hand_edits, findings, notes)`.

## Pure functions (no I/O)
1. `derive_status(ticket_id, tickets, prs, branches, folders_seen)` returns `(status, pr, finding)`, first match wins: Done (a file in `done/`) -> In review (open PR whose files include the ticket path) -> Blocked (`## Status` BLOCKED in the branch copy, else main's) -> In progress (a branch fact lists the id) -> To do. A ticket in two folders gets the higher status and a finding; `inprogress/` with no branch is an orphan finding.
2. `derive_fields(...)` builds the design §2 fields: Ticket ID, Status, Domain, Seat, Host, Branch, PR, Tier, Source, Sync hash. `Host` and `Branch` carry `host:branch` entries.
3. `merge_host_entries(current, mine, host)` replaces only entries tagged with `host`, keeps the other host's (design §5). Status rule 4 reads the union.
4. `sync_hash(fields)` = sha256 over the written fields in a fixed order (excludes the hash itself). `detect_hand_edit(item, derived)`: current fields do not hash to the stored `Sync hash` -> `hand edit: <id> <field> '<theirs>' -> '<derived>'`.
5. `build_plan(derived, items, now)`: create / update / archive keyed by Ticket ID; an item with no id or an id with no ticket file -> to-archive; Done items older than 14 days -> archive.

## I/O (thin, injectable)
- `read_origin_tickets(root, ref="origin/main", run=...)` via `git ls-tree` / `git show`, plus `origin_age(root)`.
- `read_branch_facts(root, host, run=...)`: the status.py builders with `size_reader=lambda p: 0` and a no-op `pr_reader`, then the per-worktree diff and porcelain described in the investigation.
- `read_open_prs(run=...)`: `gh pr list --state open --json number,url` then paged `gh api` GET of each PR's files. Only GETs; a failing gh prints a note and treats PRs as unknown (rule 2 skipped, stated in the output).
- `read_items(path)`: the `--items` JSON fixture; empty by default.

## CLI
`python3 -m tools.sessions.project_sync [--dry-run] [--items FILE] [--root DIR]`. `--apply` and `--init` exit 2 with "P1 is not built". Output: origin/main sha and age, host, one line per create/update/archive, hand-edit and orphan findings, a stale-host note. Writes nothing anywhere.

## registries/session_project.yaml
`project: {owner: PLACEHOLDER, number: 0}`, `pilot_lanes: [rpg]`, `pilot_start: 2026-11-12`, `done_window_days: 14`, `stale_host_hours: 24`. No field ids. Loaded with the repo's YAML loader; a missing file or key falls back to those defaults with a note.

## Not doing
`--apply`/`--init`, tokens, ubuntu runs, timers, views, parsing #634 comments, any gh write.

## Amendments (designer review, 2026-11-12: OK with A-E)
- **A. Filing is not progress.** Only a copy in `inprogress/` or `done/` (on the branch, in a porcelain file, or in a PR's file path) counts for rule 4 or rule 2. A `todos/` copy stays To do, with Branch still recorded (the Branch entry gets a `[filing]` suffix, which later runs ignore as rule-4 evidence).
- **B. Branch-only tickets carry their own content.** `BranchFact` holds, per ticket, `(folder, title, tier, blocked, date)`, read with `git show HEAD:<path>` in that worktree for committed files and from disk for porcelain files. The branch copy wins over main's for these fields.
- **C. Done timing from git.** `done_date(path)` = `git log -1 --diff-filter=A --format=%cI origin/main -- <done path>`, run only for candidates. A Done item is created when `done_date >= pilot_start` and archived when it is more than 14 days old. `Source` stays the origin sha plus run time; the hash excludes `Source`, so a new run time alone is never an update.
- **D. PR list limit.** `gh pr list --limit 300` (ticket_queue.PR_LIMIT's value); if the count equals the limit, a note says some PRs may be missing. File lists use `gh api --paginate` (GET).
- **E. Host and detached worktrees.** `--host` defaults to `socket.gethostname()` and is printed. Detached worktrees are skipped and counted; one that changes a ticket file is reported as `unattributed`.
- `_worktree_for` is imported as-is with a comment naming it deliberate reuse.
- A read-only guard wraps every subprocess: git verbs limited to ls-tree, show, merge-base, diff, status, log, rev-parse, worktree; gh limited to `pr list` and GET `api`.
