---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261120-SUBJECT-LINK-DOES-NOT-LIFT-A-TICKET-THE-BRANCH-ALSO-EDITS-IN-TODOS
phase: open
date: 2026-11-20
tags: [delivery]
---

# TCK-20261120-SUBJECT-LINK-DOES-NOT-LIFT-A-TICKET-THE-BRANCH-ALSO-EDITS-IN-TODOS

## Title
A ticket worked on a branch that also edits its todos/ file reads To do, because the commit-subject link only lifts tickets the branch does not already carry a copy of

## Status
OPEN

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
Found by lead-planner in ubuntu's first hand apply after #984 (main 0c18f6151, log kept by lead-planner): `update TCK-20261109-M1-BASIC-WILD-BIRTHS-FOR-EVERY-LIVING-KIND To do changed: Status, Seat, Branch, Host facts`, and the sync note said `subject-link: ran on 16 branches, linked 0 tickets`. The births work is live on ubuntu: branch `rpg-ubuntu-wild-births-impl`, checked out in `.claude/worktrees/rpg-ubuntu`, head d3401ba43 and 5fec51fde with subjects that lead with the ticket id and touch `src/` code, no PR. By the #976/#984 rules it should read In progress.
Planner reading (code and git facts only; the dry run is not reproduced yet): `tools/sessions/project_sync.py` line 399, `to_link = worked - {c.id for c in copies}`, drops from linking any ticket for which the branch already has a copy. That branch changes the ticket file itself (`git diff --name-status` against the merge base shows `M agent-working/tickets/todos/TCK-20261109-M1-BASIC-WILD-BIRTHS-FOR-EVERY-LIVING-KIND.md`), so the copy exists, and a `todos/` copy on a branch is filing, never progress, so the ticket stays To do. The worked-by-subject evidence is then never used. This is a different defect from the missing-file case that #976 fixed (a ticket with no file on origin/main).

## Scope
1. Reproduce first, read-only, with a dry run on ubuntu at origin/main 0c18f6151 (the sync reads checked-out worktrees): confirm the reading above or name the real cause. Check the other two causes lead-planner listed (the seat record for that worktree, the merged-PR filter) and rule them in or out from the code and output.
2. If confirmed: when a branch carries a `todos/` copy of a ticket AND has a worked-by-subject commit for it (leading id, a code file outside `agent-working/` and `docs/`), the ticket links as worked and reads In progress, like any other worked ticket. A branch that carries only the filing copy and no worked commit stays To do, as today.
3. Say why Seat and Branch also changed in that row, and whether they were right before or after.

## Out of Scope
- The orphaned in-progress TCK-20261008-SLOW-REGRESSION-SCHEDULE-WATCHDOG finding (testing's, not new).
- The remote-branch reading and the apply-skips behaviour (separate tickets).

## Acceptance Criteria
1. Synthetic fixture shaped like the births case (a branch that edits the ticket's todos/ file and has leading-id code commits) reads In progress with the branch's seat; before the fix the same fixture reads To do (positive control).
2. Must-nots: a branch that edits only the ticket's todos/ file with no code commit stays To do; a docs-only or mid-subject citation stays To do; a Done ticket stays Done; a merged-PR branch is not counted.
3. A dry run before and after on a named SHA shows the births row; whoever runs it names the SHA.
4. Scoped tests only; the whole tools f–z lane locally with the exact command in the push facts.

## Related Tickets
- TCK-20261119-SUBJECT-LINK-FOLLOWS-A-TICKET-FILED-ONLY-ON-AN-UNPUSHED-BRANCH (done; the missing-file case this one complements)
- TCK-20261119-PROJECT-SYNC-APPLY-SKIPS-ITEMS-WITH-A-MISSING-STATUS-OPTION-AND-FLAGS-DOUBTFUL-PARKED-MARKERS (rides the same batch; same file)
- TCK-20261119-PROJECT-SYNC-READS-REMOTE-BRANCHES-NOT-ONLY-CHECKED-OUT-WORKTREES (scored 82.3: same file and the same link rule, but it widens WHICH branches are read, while this ticket fixes a checked-out branch that already carries a copy; not a duplicate, and it must reuse this fix)
- overlap scan: 5 hits, none duplicate (tools/open_ticket_overlap.py on this draft: the remote-branches ticket 82.3 and the apply-skips ticket 37.2 are cited; TCK-20260822-STANDARD-SLOW-REGRESSION-CI-JOB-EXIT-CODE-2 34.2, TCK-20261116-PRE-PUSH-ADVISORY-CHECKS-THE-PUSH-TARGET 29.4 and TCK-20261030-SIMQ-ANCHOR-REDS-SINCE-V1-REANCHOR-NEED-A-BISECT 25.9 share only generic words)

## Related Docs
- `docs/guidelines/session_roles/project_sync_dry_run.md`

## Related Stored Artifacts
- none yet

## Related Code Areas
- `tools/sessions/project_sync.py` (`read_branch_facts`, around line 399; `link_worked`; `subject_links`)
- `tests/tools/test_session_project_view.py`

## Assumptions / Open Questions
- The line-399 reading is the planner's, from code and git facts; step 1 reproduces it.
- Whether the Status was In progress before this tick or To do for longer: the previous item value is in lead-planner's log.

## Durable state, lifecycle and clocks
N/A: no src change; the Project is a generated view rebuilt on each sync.

## Implementation Notes
Filed by agent-working-planner on lead-planner's finding; dispatched with the apply-skips ticket.

## Test Summary

## Files Changed

## Completion Summary
