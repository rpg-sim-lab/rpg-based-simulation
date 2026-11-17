---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261101-PR-RENDER-LEAVES-OUT-A-TICKET-IN-TWO-STATUS-FOLDERS
phase: done
date: 2026-11-01
tags: [delivery]
---

# TCK-20261101-PR-RENDER-LEAVES-OUT-A-TICKET-IN-TWO-STATUS-FOLDERS

## Title
pr_render leaves a ticket out of Closes: when its file is in more than one status folder

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
Found by lead-planner-u24 on PR #820 (rpg), and reproduced and drafted by agent-working-designer-u24 (main checkout
`.claude/handover/drafts/pr-render-ticket-in-two-status-folders-2026-11-01.md`). pr_render's default body listed 17 tickets
as closed that were only open on the branch. Each had an unchanged `done/` file from main and a `todos/` or `inprogress/` copy
the branch added. `discover_tickets` tests "changed" per ticket ID, so the new open copy marks the ID changed. The location
test, though, reads one file: `find_ticket_file` returns `sorted(rglob(...))[0]`, and `done/` sorts first, so
`_not_closed_dir` (TCK-20261002-PR-RENDER-CLOSES-LISTS-FILED-FOLLOWUPS) never fires. Reproduced with main's
`discover_tickets` against #820 head ff5df3c2a (20 listed, 17 open on the branch).

## Scope
- `tools/delivery/pr_render.py::discover_tickets`: leave out, with a warning, a ticket that has files in more than one status
  folder at HEAD. The warning names the folders. The check runs before `_not_closed_dir`, so the sorted-first pick can't hide
  an open copy. The designer's draft section 2 has the shape: a per-ID `_status_dirs` helper next to `find_ticket_file`.
- Add one sentence to the docstring: "So is one with files in two status folders."
- Tests in `tests/tools/test_delivery_pr_render.py`, next to
  `test_a_ticket_filed_under_todos_is_left_out_of_closes_with_a_warning`: (1) done/ plus todos/, the #820 regression, which
  fails on main today; (2) done/ plus inprogress/; (3) done/ only and changed, which is still listed.

## Out of Scope
- `find_ticket_file`'s single return (other callers rely on it), `discover_changed_ticket_ids`, and the exclusion mechanism.
- A repo-state guard: `validate_frontmatter.py::find_closed_ticket_resurrections` plus `TestClosedTicketResurrectionCorpus`
  already flag the tree state in CI.
- #820's duplicate files themselves (rpg-planner, via lead-planner-u24).
- Counting `done/` arrivals not named in commit subjects. Commit-subject discovery is deliberate (TCK-20260927,
  TCK-20261002).

## Acceptance Criteria
1. A ticket with a `done/` file and a `todos/` or `inprogress/` file, whose ID is named in a commit subject and changed by the
   branch, is not in the rendered Closes:. A warning names both folders.
2. A ticket only in `done/` and changed by the branch is still listed.
3. The existing todos/-only, cited-only and exclusion tests pass unchanged.
4. Scoped run: `pytest tests/tools/test_delivery_pr_render.py -q` is green.

## Related Tickets
- TCK-20261002-PR-RENDER-CLOSES-LISTS-FILED-FOLLOWUPS (added `_not_closed_dir`)
- TCK-20261002-PR-RENDER-CITED-ONLY-AND-TICKETLESS-BRANCHES
- TCK-20260928-CLOSED-TICKETS-RESURRECTED-INTO-TODOS (repo-state guard)

## Related Docs
- `docs/guides/delivery_process.md` ("PR Lifecycle"); no change proposed.

## Related Stored Artifacts
- Designer draft (main checkout): `.claude/handover/drafts/pr-render-ticket-in-two-status-folders-2026-11-01.md`

## Related Code Areas
- `tools/delivery/pr_render.py` (agent-working)
- `tests/tools/test_delivery_pr_render.py` (split rpg/agent-working; the new tests sit in agent-working's pr_render section)

## Assumptions / Open Questions
- Reusing `find_closed_ticket_resurrections` instead of a per-ID helper is an implementer choice: it scans the whole tree,
  while pr_render loops per ID.

## Implementation Notes
A per-ID `_status_dirs` helper next to `find_ticket_file`; `discover_tickets` checks it before `_not_closed_dir` and leaves the ticket out with a warning naming both folders. `find_closed_ticket_resurrections` was not reused (it scans the whole tree; pr_render loops per ID).

## Test Summary
`pytest tests/tools/test_delivery_pr_render.py -q`: 84 passed. The two new done/+open-folder cases (todos, inprogress) fail on main without the fix and pass with it; the done/-only control and the existing todos/-only, cited-only and exclusion tests pass unchanged.

## Files Changed
tools/delivery/pr_render.py; tests/tools/test_delivery_pr_render.py.

## Completion Summary
pr_render no longer lists a ticket as closed when its file sits in more than one status folder; it warns and names the folders. #820's duplicate files themselves are rpg-planner's.
