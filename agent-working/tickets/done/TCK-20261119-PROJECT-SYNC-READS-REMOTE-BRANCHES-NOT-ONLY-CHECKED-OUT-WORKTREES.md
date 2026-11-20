---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261119-PROJECT-SYNC-READS-REMOTE-BRANCHES-NOT-ONLY-CHECKED-OUT-WORKTREES
phase: done
date: 2026-11-19
tags: [delivery]
---

# TCK-20261119-PROJECT-SYNC-READS-REMOTE-BRANCHES-NOT-ONLY-CHECKED-OUT-WORKTREES

## Title
project_sync reads `origin/*` branches as well as checked-out worktrees, so a ticket worked on a branch nobody has checked out shows on either host

## Status
DONE

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

## Disposition
STALE-PREMISE

## Disposition Rationale
Owner decision (#715, 2026-11-20, relayed by lead-planner): close this ticket with a Disposition and build nothing. The premise was that tickets worked on pushed branches nobody has checked out show wrong on the board, and that the implementer's earlier 5 "moves to In progress" showed it. Step 1, measured by agent-working-implementer on origin/main c540a0b17 (taskset -c 0-3, ubuntu's view only; u24's worktrees were not visible), shows that premise was an artefact of treating every old ref as live work:
```
origin/* refs excluding main and HEAD: 222; ahead of origin/main: 220 (squash-merge residue)
checked out in a worktree on ubuntu: 7; remote-only: 213
remote-only refs naming a ticket by a leading id plus a code file: 152
  with an already-merged PR: 57; open PR: 1; no PR: 94
the 95 unmerged refs name 118 tickets: 103 have no live item (Done on main), 5 are To do
the rule would move exactly 5 To-do tickets, and all 5 would read Stale, not In progress:
  branch tips are 67, 31-38, 31-38, 31 and 19-20 days old (stale_branch_days is 14)
  TCK-20261009-RPG-REGRESSION-METRICS-COMPUTED-FROM-TYPED-RECORDS has 44 old refs; its work landed through other PRs
only unmerged ref within 14 days: TCK-20261031-A-PAIR-RE-FORMS-AND-LEAVES-A-GROUP-EVERY-TWO-TICKS (rpg-combined-run-u24-urban)
cost of option (A): about +6 s per tick (merged-PR list of 846 PRs, limit 1000), plus an elected host-neutral `origin` segment;
  a whole dry run is 32.7 s today
```
So: 0 To-do tickets would move to In progress today; each host already sees its own lane worktrees (the births case was fixed by #986's own-copy lift, c540a0b17); and the cost is +6 s a tick plus the one-writer election across hosts. The implementer's read-only measurements were stopped and nothing was built. One fact it read before stopping (the planner did not re-run it): the shared repo already holds all 222 remote heads (`remote.origin.fetch` is the full default refspec, `ls-remote --heads` shows 222 against 223 local origin/* entries including HEAD, none missing), so the widened fetch would not have added objects; the repo is 170 MiB in packs plus 111 MiB loose.

Reopen trigger: pushed-but-unchecked-out branches start hiding real work, meaning a ticket that is actively worked on a branch no worktree has checked out reads To do or Stale on the board while that branch's tip is within the 14-day stale window. If it is reopened, the smallest form is option (A): a remote-only ref counts as working evidence only when its tip is within 14 days, reusing #986's `link_worked` and the merged-PR filter, with the `--fetch` widening to `+refs/heads/*:refs/remotes/origin/*` and `for-each-ref` added to READ_GIT; a simpler two-host derivation than the election was proposed but not measured.

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
none: no code, a Disposition closure.

## Files Changed
none: no code, a Disposition closure (only this ticket's move to done/).

## Completion Summary
Closed 2026-11-20 with Disposition STALE-PREMISE by owner decision (#715, via lead-planner). The step-1 numbers are in `## Disposition Rationale`; nothing was built. Reopen trigger recorded there.
