---
status: historical
layer: ticket
authority: P2
audience: agent
phase: done
ticket_id: TCK-20261112-PROJECT-SYNC-GUARD-SEAT-AND-STALE
artifact_type: plan
tags: [planning, delivery]
---

# Plan

Order (guard first, per AC 1):
1. `_guard`: refuse a `gh api` argument that starts with `-f`, `-F`, `--field`, `--raw-field`, `--input`, or is `-X*`/`--method*` with a value (after `=` or joined) other than GET (case-insensitive). Joined spellings: `--method=POST`, `-XPOST`, `-X=POST`, `-fk=v`, `--field=k=v`, `--raw-field=k=v`, `--input=f`. `-XGET`, `--method=GET` and `-X GET` stay allowed. No write path is added.
2. Seat: `batch_worktree_seat` map in session_project.yaml (`rpg: rpg-implementer`); `attribute()` gets the map; unleased worktree with a mapped domain -> `<seat> (batch)`, else the existing `<domain> (unmapped)`. Launcher recording: reported, not built.
3. Stale: `stale_branch_days: 14` in session_project.yaml; BranchFact.last_activity; derive_status returns `Stale` when every branch fact for the ticket is older than the window (any active branch keeps In progress).
4. Entry point: sys.path shim at the top of project_sync.py (repo root on sys.path when run as a script).
5. Host: `host_names` map in session_project.yaml; `--host` default = map.get(hostname, hostname).
6. README section: how to run the dry run.
Out: any write path, --init/--apply, launcher change.

Seat order (lead 2026-11-12): (a) the launcher's recorded seat via `_worktree_for` (unchanged, already first); (b) only if none, the `batch_worktree_seat` family label `(batch)`; (c) else `<domain> (unmapped)`. A test covers (a) winning over (b).

## Amendments (designer OK 2026-11-12, accepted by the lead; these supersede the text above where they differ)
A. No `batch_worktree_seat` map. The seat stays derived (the launcher's record first); the fallback label is `<domain> (seat not recorded)`, and the gap is named in `docs/guidelines/session_roles/project_sync_dry_run.md`. The hand-made-worktree gap is filed as TCK-20261112-HAND-ADDED-WORKTREES-ARE-NOT-RECORDED-AGAINST-A-SEAT (planner's filing, rides this PR; not implemented).
B. The `gh api` guard is an allowlist: one `repos/...` endpoint (so `graphql` is refused), and only `--paginate`, `-q/--jq` and `-H/--header` with a value. Every joined or unknown spelling is refused.
C. Stale replaces In progress only (Done, In review, Blocked still win); filing branches and a fresh other-host entry keep In progress; unknown age (0) is never stale. README notes the age is approximate (commit or index mtime).
D. README file: `docs/guidelines/session_roles/project_sync_dry_run.md`.
