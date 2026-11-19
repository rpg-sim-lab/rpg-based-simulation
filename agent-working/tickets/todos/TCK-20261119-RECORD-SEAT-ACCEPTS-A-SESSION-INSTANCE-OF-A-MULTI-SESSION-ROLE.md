---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261119-RECORD-SEAT-ACCEPTS-A-SESSION-INSTANCE-OF-A-MULTI-SESSION-ROLE
phase: open
date: 2026-11-19
tags: [delivery]
---

# TCK-20261119-RECORD-SEAT-ACCEPTS-A-SESSION-INSTANCE-OF-A-MULTI-SESSION-ROLE

## Title
record_seat records a session instance (`rpg-implementer-3`) of a multi-session role, so each lane worktree shows its own seat in the Project

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
`tools/sessions/record_seat.py` (Project view PR #976) accepts only roster roles, but the u24 lane seats are session instances of one role: `registries/session_roles.yaml` lines 241-248 give `rpg-implementer` `placement: {worktree: rpg, max_sessions: 4}` (and `rpg-implementer-ubuntu` the same), and rpg-implementer-2/-3/-4 are its instances (found by lead-planner, verified on origin/main; relayed 2026-11-19). Recording a lane under the base role loses most lanes; adding the instances as roster entries would duplicate the role and fight `max_sessions`. Chosen option (c), recommended by lead-planner-u24 and agreed by lead-planner and rpg-planner: record_seat accepts `<role>` or `<role>-<n>` for 2 <= n <= `max_sessions`, stores the role plus the instance, one record per instance. This is on the critical path of the owner's live-write gate: the coin fix (rpg-implementer-3), #965 (rpg-implementer-2) and the lane backfill (m1kind5 = rpg-implementer-2, coinsink = rpg-implementer-3) all need instance seats. Dispatch right after #976 merges.

## Scope
1. Step 1, read-only: how the seat state is keyed today (`state.write_bound_worktree`, `read_bound_worktree`, `_check_role`, `read_instance`, the launcher's own instance records) and where project_sync and status.py turn a worktree into a seat (`_worktree_for`, `attribute`, `seat_of`). Report whether an instance record fits the existing keying without a format change, with the files that must change; stop and tell the planner if it needs more than record_seat, `_worktree_for`/`attribute` and their tests.
2. record_seat: accept `<role>` and `<role>-<n>` with `2 <= n <= placement.max_sessions` of that role from the roster; refuse n above max_sessions, n=0 or 1 as an instance suffix, a non-numeric suffix, a suffix on a role with `max_sessions` 1, and a name that is not a known role or instance. One record per instance, so two instances of the same role can each hold a worktree; the existing refusals (not a live linked worktree, already recorded for another seat) hold per instance.
3. The instance name is stored and displayed exactly as given (for example `rpg-implementer-3`), never collapsed to the role: rpg-planner's lane records cite -2/-3/-4. This is a test, not a comment.
4. project_sync and status.py read an instance record and name that instance as the Seat and in Involved, so the Project shows `rpg-implementer-3`. A worktree with a base-role record keeps showing the base role.
5. Works with the `--state-root` option from #976; the real state root is untouched in tests.
6. Docs: `docs/guidelines/session_roles/project_sync_dry_run.md` (the accepted names, the max_sessions bound, the one-record-per-instance rule, the u24 backfill command for the known lanes).

## Out of Scope
- Adding instances as roster entries or changing `max_sessions`.
- Guessing an instance from a branch name or a path.
- Running the u24 backfill (a u24 seat does, after merge) and the live Project write (owner's yes plus the u24 dry run).
- Changing the launcher's own session-instance records, except to read them.

## Acceptance Criteria
1. `record_seat <wt> rpg-implementer-3` records the instance; status.py shows `writing in` for it; project_sync names `rpg-implementer-3` as the Seat, never `rpg-implementer`. Same for `-2` and `-4`, and for `rpg-implementer-ubuntu-3`.
2. Must-nots, each refused with a plain message and nothing written: `rpg-implementer-5` (above max_sessions 4), `rpg-implementer-1`, `rpg-implementer-x`, `rpg-planner-2` (max_sessions 1), `rpg-implementer-3` on a worktree already recorded for another instance.
3. Two instances of the same role each hold their own worktree at once; recording the second does not move or overwrite the first, and `--replace` moves only the named instance.
4. A base-role record from #976 is read unchanged.
5. The real state root is untouched when `--state-root` is given (before/after compare).
6. Scoped tests only; a before/after project_sync dry run on a named SHA shows the coin-fix and #965 shapes (synthetic fixtures) naming the instance seats.

## Related Tickets
- TCK-20261119-PROJECT-VIEW-SEAT-COLLABORATORS-LINK-BY-COMMIT-SUBJECT-AND-PARKED (PR #976, adds record_seat)
- TCK-20261112-HAND-ADDED-WORKTREES-ARE-NOT-RECORDED-AGAINST-A-SEAT
- overlap scan: 5 hits, none duplicate (tools/open_ticket_overlap.py on this draft: the two tickets named above are cited; the rest share only generic words)

## Related Docs
- `docs/guidelines/session_roles/project_sync_dry_run.md`
- `registries/session_roles.yaml` (placement and max_sessions)

## Related Stored Artifacts
- none yet

## Related Code Areas
- `tools/sessions/record_seat.py`, `tools/sessions/state.py`, `tools/sessions/status.py` (`_worktree_for`), `tools/sessions/project_sync.py` (`attribute`, seat_of)
- `tests/tools/test_session_record_seat.py`, `tests/tools/test_session_project_view.py`

## Assumptions / Open Questions
- Whether the existing bound-worktree record can be keyed by an instance name without a format change: unmeasured, step 1.
- Whether the launcher already writes per-instance records that status.py reads (`read_instance`): to confirm in step 1.
- A code commit to the open PR #976 would need a fresh owner ask; this ticket is the separate PR.

## Durable state, lifecycle and clocks
The seat record is written once per instance at worktree creation by record_seat and cleared when the worktree is removed; one writer (record_seat), no clock. The Project fields are a generated view rebuilt on each sync.

## Implementation Notes
Filed by agent-working-planner on lead-planner's relay (finding by lead-planner, option (c) from lead-planner-u24, rpg-planner's instance-name requirement).

## Test Summary

## Files Changed

## Completion Summary
