---
status: active
layer: ticket
authority: P2
audience: agent
ticket_id: TCK-20261112-PROJECT-SYNC-DRY-RUN
artifact_type: investigation
tags: [planning, delivery]
---

# Investigation

Checked against origin/main 5e58ae857 and the u24 host on 2026-11-12. Design: main-checkout draft `github-project-ticket-view-2026-11-12.md` (§1-§5, §8, addendum).

## What status.py gives and does not give
- `collect()` returns a rendered string, not data. The reusable parts are `worktree_entries()` (launch.py, `git worktree list --porcelain`), `inspect_worktree(entry, main, pr_reader, size_reader)`, `seat_infos(roster, state_root)` and `_worktree_for(role, infos, main, state_root)` (private name, one underscore).
- `inspect_worktree` calls `tree_size` on every worktree (57 on u24, expensive). The sync passes `size_reader=lambda p: 0` and a no-op `pr_reader`, so it pays for neither the size walk nor the per-branch `gh pr list`.
- `Role.domain` exists (`rpg-implementer` -> `rpg`), so Domain comes from the roster for a seat-mapped worktree. `_worktree_for` maps a role to its physical worktree; inverting it over all roles gives worktree -> seat.
- Branch names do not name the seat (design §0), so Seat comes from that inversion; failing that `<domain> (unmapped)` from the branch prefix; else `unknown`.
- `status.py` run as a script fails outside `-m` (`No module named tools`); the sync is run as `python3 -m tools.sessions.project_sync`.

## Where the ticket facts are
- Folders on origin/main: `agent-working/tickets/{todos,inprogress,done}`; epic folders nest one level (`todos/<folder>/`). Ticket id = filename stem (`TCK-....md`), the same key `ticket_queue.py` uses.
- Reading content is needed only for tier, title, `## Status` BLOCKED and the pilot-start date. The sync reads names for every ticket (one `git ls-tree -r`) and content (`git show`) only for candidates, so the 3,144 done files are never opened.
- `ticket_queue.py` already uses `gh pr list --json number,title,files --limit 300`; the node-cap note (files over 100 per PR, `--limit 1000` with `commits`) is in the handover. P0 pages the file list with `gh api` GET `repos/.../pulls/<n>/files?per_page=100&page=N` per open PR, because `--json files` stops at 100.

## Rule 4 mechanics (read-only)
- Per worktree with a branch: `git --no-optional-locks merge-base origin/main HEAD`, then `git diff --name-status <base> HEAD -- agent-working/tickets`, plus `git --no-optional-locks status --porcelain --untracked-files=all -- agent-working/tickets`. Added, modified and renamed-to paths count; deleted paths do not.
- A squash-merged branch still looks added against its old merge base; rule 1 (done on main) wins first, so it cannot show In progress.

## Open points
- Pilot-lane rule: a ticket qualifies when found on a worktree whose resolved domain is `rpg`, else whose branch starts `rpg-`; or when already in the `--items` fixture. Main's todos/ carry no domain, so To do from main waits for P3.
- "Done after the pilot start": a Done item is created only for a candidate (branch, PR or fixture) whose ticket frontmatter `date` is on or after `pilot_start`, and archived 14 days after it first reads Done (fixture item carries the first-seen date in `Source`).
- Everything here uses `origin/main` as it stands locally. No fetch; the tool prints the sha and its commit age.
