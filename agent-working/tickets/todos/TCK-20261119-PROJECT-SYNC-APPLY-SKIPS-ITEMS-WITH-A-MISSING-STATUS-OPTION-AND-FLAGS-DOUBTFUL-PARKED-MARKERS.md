---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261119-PROJECT-SYNC-APPLY-SKIPS-ITEMS-WITH-A-MISSING-STATUS-OPTION-AND-FLAGS-DOUBTFUL-PARKED-MARKERS
phase: open
date: 2026-11-19
tags: [delivery]
---

# TCK-20261119-PROJECT-SYNC-APPLY-SKIPS-ITEMS-WITH-A-MISSING-STATUS-OPTION-AND-FLAGS-DOUBTFUL-PARKED-MARKERS

## Title
One bad Parked marker must not freeze every host's board: `--apply` skips only the items whose Status option is missing, and the sync flags a Parked marker on a ticket that is being worked or that names itself

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P3

## Request Summary
Planner review of PR #984 (comment 7011805637), notes 1 and 2, filed on lead-planner's word (not dispatched; the owner decides whether it ships right after #984).
1. Today `apply_plan` refuses the WHOLE run before the first write when a planned Status value has no option on the Project. Once a ticket reads Parked and the Project has no Parked option, `--apply` exits 2 on both hosts and both hourly timers fail every tick until `--init` runs. The marker hold (no marker written before `--init` appends the option) protects against it, but a single early or stray marker would freeze every host's board. The failure should cost only the item that needs the missing option.
2. Parked sits above In progress, so a planner who resumes work and forgets to remove the marker leaves the board showing Parked while a live branch is working the ticket, and a marker naming the ticket's own id reads Parked for good. Both cases deserve a finding.

## Scope
1. Step 1, read-only, to the planner first: the exact code path where `apply_plan` decides to refuse (which checks run before the first mutation, which of them are about Status options and which about fields), and what the heartbeat or last-run record shows after a refusal.
2. A planned Status value with no option on the Project: leave THAT item at its current Status, print one finding naming the item and the missing option, count it in the run's notes, and carry on with every other item. Exit code: a DISTINCT non-zero code whenever any item was skipped (not the code of a whole-run refusal), recommended by lead-planner and agreed by the planner, because a timer that exits 0 with skipped items hides them; the rest of the run is still written, so a failed unit marks the skip without stopping the next tick. Confirm from the step 1 reading that a non-zero unit exit does not stop the timer from firing again, and say plainly what a timer sees. The skipped count must also reach the last-run record. A missing FIELD (Involved, Blocked by, Hotspot) is a different case and stays a refusal of the whole run, as tested today.
3. Parked marker findings, status unchanged: (a) a valid marker on a ticket that has a non-stale working branch segment: "marker present but a live branch is working it: still waiting?"; (b) a marker whose target ticket id is the ticket's own id: treated as malformed (a finding), so it never reads Parked.
4. Docs: `docs/guidelines/session_roles/project_sync_dry_run.md` (the new apply behaviour and the two findings). Quote the marker form only inline in prose or backticks, never at the start of a line (the hold on `Parked: ` lines until the merge window's `--init`).

## Out of Scope
- Missing fields (still refuse the whole run).
- Changing the precedence of Parked, the 45-day proposal, or how a decision target clears.
- A cycle between two tickets that each wait on the other.
- Any live Project write: the owner's yes and the dry run come first.

## Acceptance Criteria
1. Synthetic items: one item planned for Parked on a Project without the option is left at its old Status with a finding, and every other planned item is written; before the change the same input refuses the whole run (positive control).
2. A run with a missing FIELD still refuses the whole run (must-not for this change).
3. The skipped count appears in the plan notes and in the last-run record the timers write; a test pins it.
4. A marker on a ticket with a live non-stale working branch prints the finding and the Status is still Parked; a marker naming its own id prints the malformed finding and the Status is not Parked; a marker on a ticket with only a stale branch prints no such finding.
5. Scoped tests only; the whole tools f–z lane locally with the exact command in the push facts.

## Related Tickets
- TCK-20261119-PROJECT-VIEW-PARKED-STATE-FROM-A-TICKET-BODY-MARKER-LINE (PR #984, where the reading of the whole-run refusal is tested)
- TCK-20261119-PROJECT-VIEW-SEAT-COLLABORATORS-LINK-BY-COMMIT-SUBJECT-AND-PARKED (the earlier whole-run refusal for missing fields)
- TCK-20261119-PROJECT-SYNC-READS-REMOTE-BRANCHES-NOT-ONLY-CHECKED-OUT-WORKTREES (sibling in the Project view family; touches the same file, so sequence them)
- overlap scan: 5 hits, none duplicate (tools/open_ticket_overlap.py on this draft: the Parked ticket 37.0 and the remote-branches ticket 33.4 are cited above; TCK-20261112-HAND-ADDED-WORKTREES-ARE-NOT-RECORDED-AGAINST-A-SEAT 25.4, TCK-20261006-CAMPAIGN-EPISODE-COMBAT-TEST-RED-BECAUSE-NO-DELIBERATE-ATTACK-ONLY-OPPORTUNITY-ATTACKS 24.7 and TCK-20260914-REGION-DANGER-SEEN-TWO-DEAD-PRECONDITIONS 23.1 share only generic words)

## Related Docs
- `docs/guidelines/session_roles/project_sync_dry_run.md`

## Related Stored Artifacts
- none yet

## Related Code Areas
- `tools/sessions/project_sync.py` (`apply_plan`, `parked_status`, `derive_status`)
- `tools/sessions/project_client.py`
- `tests/tools/test_session_project_parked.py`

## Assumptions / Open Questions
- Whether the heartbeat or last-run record can carry a skipped count without a format change: unmeasured, step 1.
- Whether the owner wants this right after #984 or later, and the exit-code rule: lead-planner asks with the #984 merge ask.

## Durable state, lifecycle and clocks
N/A: no src change; the Project is a generated view rebuilt on each sync. The skipped count is written to the existing last-run record and overwritten by the next run.

## Implementation Notes
Filed by agent-working-planner on lead-planner's word; not dispatched.

## Test Summary

## Files Changed

## Completion Summary
