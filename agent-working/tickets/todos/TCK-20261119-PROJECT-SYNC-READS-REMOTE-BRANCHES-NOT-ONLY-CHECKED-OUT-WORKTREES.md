---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261119-PROJECT-SYNC-READS-REMOTE-BRANCHES-NOT-ONLY-CHECKED-OUT-WORKTREES
phase: open
date: 2026-11-19
tags: [delivery]
---

# TCK-20261119-PROJECT-SYNC-READS-REMOTE-BRANCHES-NOT-ONLY-CHECKED-OUT-WORKTREES

## Title
project_sync reads `origin/*` branches as well as checked-out worktrees, so a ticket worked on a branch nobody has checked out shows on either host

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P3

## Request Summary
The Project view build (TCK-20261119-PROJECT-VIEW-SEAT-COLLABORATORS-LINK-BY-COMMIT-SUBJECT-AND-PARKED) links a branch to a ticket by the ticket ids in its commit subjects, but `project_sync` only reads branches that are checked out in a worktree on the host running it. Its before/after dry run on ubuntu printed `subject-link: ran on 16 branches, linked 0 tickets`, while the implementer's step-1 measurement over 403 local and `origin/*` branches found 5 To-do tickets that the rule would move to In progress (examples: TCK-20261101-DISSOLVED-GROUP-RECORDS-ARE-KEPT-AND-VISITED-EVERY-TICK, TCK-20261109-M1-BASIC-WILD-BIRTHS-FOR-EVERY-LIVING-KIND). Owner accepted the dry run (#715, 2026-11-19) and asked for this follow-up, queued after the Parked ticket. The live Project write waits on a u24 dry run that shows the coin fix, STALEMATE F1 and #965 correctly.

## Scope
1. Re-measure on a named ref and SHA: of the `origin/*` branches ahead of `origin/main`, how many are not checked out in any worktree on either host, how many name a ticket by a leading id plus a code file, and how many of those have an already-merged PR (the squash-merge false-positive class from the Project view review). Report the tickets the rule would move.
2. Design the three open questions with numbers, then implement the chosen answers:
   - **Double counting across hosts.** A remote branch has no host. Decide which host writes its facts (one host, or a host-neutral segment) so two hosts do not both write it and do not disagree; the existing rule is that each host writes only its own facts. Show that two hosts running the sync on the same ref set produce the same value.
   - **Fetch freshness.** The sync reads `origin/main` with no fetch, and `origin/*` is as old as the last fetch. Decide between fetching inside the sync (it is read-only by construction today, so a fetch needs its narrow form added to the allowlist and a stated reason) and reading what is there with its age printed. Either way, the dry run prints the age of the ref set it read.
   - **Cost on 300+ remote branches.** Compare one `git for-each-ref` plus one bounded `git log` over all unmerged refs against one `git log` per branch, with timings on the real repo; the sync runs on a timer.
3. A remote-only branch has no worktree and so no recorded seat: it contributes the branch and a Status, never a Seat or an Involved seat. Say so in the docs.
4. Reuse the cited-vs-worked rule and the merged-PR filter from the Project view build rather than a second rule.
5. Docs: `docs/guidelines/session_roles/project_sync_dry_run.md`.

## Out of Scope
- Writing seats for remote-only branches (no guessing from branch names).
- The Parked marker, the Hotspot field, the seat CLI.
- A live Project write: needs the owner's yes and the before/after dry run to lead-planner.

## Acceptance Criteria
1. Synthetic fixtures: a remote-only branch whose leading-id code commit names a To-do ticket moves it to In progress with no Seat; a merged-PR branch, a cited-only branch and a branch already reachable from `origin/main` do not (must-nots); a remote branch that is also checked out is counted once.
2. Two simulated hosts over the same ref set derive the same value (no double counting); the test fails if both write a segment for the same remote-only branch.
3. Measured timings for the chosen reading strategy on the real repo, and the age of the ref set printed in the dry run.
4. Every new derivation reports ran / skipped / errored.
5. A before/after dry run on a named SHA lists the rows whose Status changes; the 5 expected moves are checked individually.
6. Report-only: the sync's exit code and `--apply` behaviour are unchanged for existing fields.
7. Scoped tests only.

## Related Tickets
- TCK-20261119-PROJECT-VIEW-SEAT-COLLABORATORS-LINK-BY-COMMIT-SUBJECT-AND-PARKED (the build this extends)
- TCK-20261119-PROJECT-VIEW-PARKED-STATE-FROM-A-TICKET-BODY-MARKER-LINE (sequencing: this ticket is dispatched after it)
- TCK-20261112-HAND-ADDED-WORKTREES-ARE-NOT-RECORDED-AGAINST-A-SEAT
- overlap scan: 5 hits, none duplicate (tools/open_ticket_overlap.py on this draft: the two Project view tickets named above, 50.9 and 49.8, are cited; TCK-20261116-PRE-PUSH-ADVISORY-CHECKS-THE-PUSH-TARGET 22.9, TCK-20260913-WAREHOUSE-INGESTION-NEVER-AUTOMATED-SEARCH-API-EMPTY-IN-PRACTICE 22.0 and TCK-20261115-PAIRED-PASS-RECORDS-THE-HOLD-LINE-AND-CHECKS-ITS-BASE 21.7 share only generic words)

## Related Docs
- `docs/guidelines/session_roles/project_sync_dry_run.md`

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261119-PROJECT-VIEW-SEAT-COLLABORATORS-LINK-BY-COMMIT-SUBJECT-AND-PARKED/investigation.md` (step-1 measurement, once the Project view ticket closes)

## Related Code Areas
- `tools/sessions/project_sync.py` (`read_branch_facts`, `subject_links`, `own_segment`)
- `tests/tools/test_session_project_view.py`, `tests/tools/test_session_project_sync_second_host.py`

## Assumptions / Open Questions
- Remote-branch count (300+) is lead-planner's figure; step 1 recounts.
- Whether a remote-only branch should keep a ticket In progress after a long idle time is decided by the existing stale rule; this ticket does not change `stale_branch_days`.
- Sequencing: after the Parked ticket; RPG first for the slot and memory.

## Durable state, lifecycle and clocks
N/A: no src change; the Project items are a generated view rebuilt on each sync, with no new stored state. The only clock is the existing `stale_branch_days`.

## Implementation Notes
Filed by agent-working-planner on lead-planner's relay of an owner request (#715, 2026-11-19).

## Test Summary

## Files Changed

## Completion Summary
