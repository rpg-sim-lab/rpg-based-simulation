---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261119-SUBJECT-LINK-FOLLOWS-A-TICKET-FILED-ONLY-ON-AN-UNPUSHED-BRANCH
phase: open
date: 2026-11-19
tags: [delivery]
---

# TCK-20261119-SUBJECT-LINK-FOLLOWS-A-TICKET-FILED-ONLY-ON-AN-UNPUSHED-BRANCH

## Title
A ticket filed on an unpushed tickets branch and worked on a lane branch reads To do, because the commit-subject link skips tickets with no file on origin/main

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
lead-planner-u24's u24 dry run of Project view PR #976 at 517ada2ac (git-archive scratch, live read, no write, rc 0; their figures, recorded on #715 and relayed by lead-planner, not re-run by the planner) failed the owner's bar 1: the coin fix (TCK-20261118-A-SERVICE-PAYMENT-WITH-NO-PAYEE-DESTROYS-COIN) still reads To do with Involved = rpg-planner only. Their cause, in `tools/sessions/project_sync.py` around line 363 (`read_branch_facts`): the subject-link counts a ticket as skipped when it has "no ticket file on origin/main". The coin ticket exists only on the unpushed `rpg-planner-tickets-3`, while `rpg-coin-sink` has 9 commits that lead with its id and touch code. Every ticket filed on an unpushed tickets branch and worked on a lane branch reads To do: a class, not one case. In the same run `subject-link` ran on 46 branches, linked 3, skipped 3, merged-PR 0, errored 0. Other bars: F1 moved from Stale to In progress (it is parked: the Parked ticket covers it); #965's seat is unmeasured until the instance-seat ticket lands. The owner's live write waits on bar 1.

## Scope
1. Step 1, read-only: on a named SHA, count the class: tickets named by a leading id plus a code commit on some branch that have no file on origin/main but do have a filing copy on a branch of the same host. List them. Check the u24 run's "skipped 3" individually.
2. The fix, lead-planner-u24's suggestion and the planner's reading of `read_branch_facts`: when origin/main has no copy of the ticket, link to the host's own `[filing]` copy that the sync already derives from `BranchFact` copies, so the ticket reads In progress and the lane branch's seat applies. Keep the rule's other conditions (leading id AND a code file outside `agent-working/` and `docs/`).
3. Must-nots: an id with no file on origin/main and no filing copy anywhere on this host stays skipped and is counted and named in the dry-run notes; a leading-id commit that touches only `agent-working/` or `docs/` still only cites; a ticket Done on origin/main stays Done; a filing copy on a branch only cited (not worked) stays To do.
4. Cross-host: a host without the filing copy must not write a value for that ticket from the subject link alone; two hosts over the same data must not disagree on Status or write each other's facts. Show it with the simulated two-host test already in the second-host suite.
5. Explain, before any `--apply`, why four Done items get Title/Domain/Tier/Layer rewrites in the u24 dry run: TCK-20261115-PROJECT-SYNC-ALL-LANES, TCK-20261115-PROJECT-SYNC-FILED-DATE-AND-BACKLOG-VIEW, TCK-20261115-PROJECT-SYNC-HOST-TIMER and TCK-20261118-A-SECOND-WORLD-BOSS-... (full id to be filled from the run). Name the cause from the data; if the rewrite is unintended, fix it here.
6. Docs: `docs/guidelines/session_roles/project_sync_dry_run.md` (the filing-copy rule and the new skipped line).

## Out of Scope
- The Parked marker, the instance-seat record and the remote-branch reading (separate tickets).
- Creating Project items for ids that have no ticket file anywhere.
- A live Project write: needs the owner's yes and a re-run of the u24 dry run showing bar 1 passes.

## Acceptance Criteria
1. Synthetic fixture shaped like the coin case (ticket file only on an unpushed filing branch; a lane branch with 9 commits leading with its id and touching code) reads In progress and names the lane branch's seat; before the fix the same fixture reads To do (positive control).
2. Each must-not in scope item 3 holds, with a test.
3. Every derivation reports ran / skipped / errored, including how many tickets were linked through a filing copy.
4. The two-host test passes (no double write, no disagreement).
5. The four Done items are explained from data, with the command that shows the cause.
6. A re-run of the u24 dry run on a named SHA (by a u24 seat, scratch state root, no write) shows the coin ticket In progress; that evidence goes to lead-planner and the planner before any live write.
7. Report-only; the exit code and existing fields are unchanged otherwise. Scoped tests only.

## Related Tickets
- TCK-20261119-PROJECT-VIEW-SEAT-COLLABORATORS-LINK-BY-COMMIT-SUBJECT-AND-PARKED (PR #976, the build this fixes)
- TCK-20261119-RECORD-SEAT-ACCEPTS-A-SESSION-INSTANCE-OF-A-MULTI-SESSION-ROLE (touches the same file; sequenced after it)
- TCK-20261119-PROJECT-VIEW-PARKED-STATE-FROM-A-TICKET-BODY-MARKER-LINE (F1)
- TCK-20261118-A-SERVICE-PAYMENT-WITH-NO-PAYEE-DESTROYS-COIN (the case)
- overlap scan: 5 hits, none duplicate (tools/open_ticket_overlap.py on this draft: the tickets named above are cited; the rest share only generic words)

## Related Docs
- `docs/guidelines/session_roles/project_sync_dry_run.md`

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261119-PROJECT-VIEW-SEAT-COLLABORATORS-LINK-BY-COMMIT-SUBJECT-AND-PARKED/investigation.md`

## Related Code Areas
- `tools/sessions/project_sync.py` (`read_branch_facts`, `subject_links`, `own_segment`)
- `tests/tools/test_session_project_view.py`, `tests/tools/test_session_project_sync_second_host.py`

## Assumptions / Open Questions
- The u24 figures and the line-363 cause are lead-planner-u24's; step 1 verifies the cause in code on the named SHA before the fix.
- Whether a filing copy always carries enough fields (Domain, Tier) for the item: to confirm in step 1.

## Durable state, lifecycle and clocks
N/A: no src change; the Project items are a generated view rebuilt on each sync, with no new stored state.

## Implementation Notes
Filed by agent-working-planner on lead-planner's relay of the u24 dry run of #976. Same file as the instance-seat ticket, so sequenced after it.

## Test Summary

## Files Changed

## Completion Summary
